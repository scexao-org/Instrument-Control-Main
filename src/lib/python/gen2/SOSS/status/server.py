#!/usr/bin/env python
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Apr 15 11:49:17 HST 2009
#]
#
#

# remove once we're certified on python 2.6
from __future__ import with_statement

import sys, re, signal, time
import threading

import Bunch
import Task, Monitor
import SOSS.SOSSrpc as SOSSrpc
import SOSS.status as st
import Derive
import common
import remoteObjects as ro
import logging, ssdlog

version = '20090313.0'


# Regex used to discover/parse statint info
regex_statint = re.compile(r'^mon\.statint\.(\w+)$')


specialValues = {
    # --- FOR IRCS ---
    'FITS.AOS.STATUS' : '-----',
    'AO.STATUS'       : '',

    # --- CONSTANTS ---
    # Following copied from current (2006-08-29) /oss_data/OBS_NFS/OSSL_StatU
    # file on obs1.  I can find no program that writes this file, and the Unix
    # file date is 2005-10-10, so it hasn't changed recently.  Hence, I am
    # assuming these values are contants.
    'FITS.SBR.WEATHER': 'Fine',
    'FITS.SBR.TRANSP' : 1.000,
    'FITS.SBR.TELESCOP': 'Subaru',
    }


class statusServerError(Exception):
    """Class for errors thrown by the status server.
    """
    pass

class StatusServer(object):
    
    def __init__(self, statusObj, logger, monitor, monchannels=['status'],
                 checkptfile='status.cpt'):

        self.logger = logger
        self.monitor = monitor
        self.monchannels = monchannels
        self.statusObj = statusObj
        self.checkptfile = checkptfile

        # We'll share our monitor's thread pool
        self.threadPool = self.monitor.get_threadPool()

        # Needed for starting our own tasks on it
        self.tag = 'status'
        self.shares = ['logger', 'threadPool']

        # This holds the current decoded status values
        self.g2status = Bunch.threadSafeBunch()

        # Lock for mutual exclusion
        self._lock = self.g2status.getlock()

        # For looking up information about tables, aliases, etc.
        # share statusInfo object
        self.statusInfo = self.statusObj.get_statusInfo()

        # For deriving status
        self.derive = Derive.statusDeriver(self, self.logger)

        # Tables to ignore, can be set dynamically
        self.ignoreTables = set([])


    ################################################################
    # Private interfaces
    ################################################################

    def __fetch(self, statusDict, derive=False, allow_none=False):
        """Fetch a group of status values.  (statusDict) is a dictionary
        whose keys are the aliases to fetch.  If (derive)==True, then
        any derived aliases in statusDict are newly recomputed (default
        is False).  If (allow_none)==True, then None values are returned
        as is, otherwise they are converted to STATNONE.

        Returns a dictionary of the result values.
        """
        
        with self._lock:
            for alias in statusDict.keys():
                # Recompute derived aliases if derive==True
                if derive and self.derive.isDerived(alias):
                    val = self.derive.deriveOne(alias)

                else:
                    # Non-derived alias.
                    try:
                        val = self.g2status[alias]

                    except KeyError:
                        #val = common.STATERROR
                        val = common.STATNONE

                # Convert None --> ##NODATA## if allow_none==True
                if (val == None) and (not allow_none):
                    val = common.STATNONE

                statusDict[alias] = val

            return statusDict

    
    def __fetchOne(self, alias, derive=False, allow_none=False):
        """Like fetch(), but just fetch one status alias and return that
        value.
        """
        
        d = self.__fetch({ alias: common.STATNONE },
                         derive=derive, allow_none=allow_none)
        return d[alias]
                              

    def __store(self, statusDict, derive=False):
        """Store a dictionary of status alias/values into the staus system.
        If (derive)==True, then any derived status values that depend on
        these values will be recomputed (default is True).
        """

        with self._lock:
            mon_d = {}
            
            # Store status items
            self.logger.debug("Stored: %s" % str(statusDict))
            self.g2status.update(statusDict)

            if common.mon_transmit:
                mon_d.update(common.ro_sanitize(statusDict, pfx='mon.status.'))

            if derive:
                # Compute derived aliases linked to aliases sent.
                d = self.derive.aliasesToDerivedAliasesDict(statusDict.keys(),
                                                            None)
                if d:
                    self.derive.derive(d)
                    self.logger.debug("Derived: %s" % str(d))
                    self.g2status.update(d)

                    if common.mon_transmit:
                        mon_d.update(common.ro_sanitize(d, pfx='mon.status.'))

            if common.mon_transmit:
                # Update status seen through the monitor
                self.monitor.store(mon_d, ['status'])
            
    ################################################################
    # Public interfaces (over remoteObjects)
    ################################################################

    # Need this because we don't inherit from ro.remoteObjectServer,
    # but are delegated to from it
    def ro_echo(self, arg):
        return arg

            
    def initialize(self):
        """Initialize the status system for use.
        """
        try:
            # Try to restore from last known checkpoint file
            self.restore(self.checkptfile)
            
        except IOError, e:
            # No checkpoint file, so update bare status dict with known
            # special values
            self.g2status.update(specialValues)

        
    def fetchOne(self, alias):
        """Fetch exactly one alias value.
        """

        d = self.__fetch({ alias: common.STATNONE },
                         derive=False, allow_none=False)

        # Sanitize for return trip over remoteObjects, if necessary
        if common.ro_long_fix:
            d = common.ro_sanitize(d)

        val = d[alias]
        
        self.logger.debug("Fetched: %s=%s" % (alias, str(val)))
        return val


    def fetch(self, statusDict):
        """Fetch all aliases specified by the keys of statusDict.
        Returns a dict with all the key/value pairs.
        """

        d = self.__fetch(statusDict,
                         derive=False, allow_none=False)
                              
        # Sanitize for return trip over remoteObjects, if necessary
        if common.ro_long_fix:
            d = common.ro_sanitize(d)

        self.logger.debug("Fetched: %s" % (str(d)))
        return d


    def store(self, statusDict):
        """Store the alias/value pairs in the statusDict into the status
        system.  Derived aliases that depend on any of these will be
        updated.
        """
        # Unsanitize from trip over remoteObjects, if necessary
        if common.ro_long_fix:
            statusDict = common.ro_unsanitize(statusDict)
        
        self.__store(statusDict, derive=True)
        
        return ro.OK


    def dump(self, filepath):
        """Dump the complete set of aliases to a file specified by
        filepath.  Format will be a Python dictionary, with keys in sorted
        order.
        """
        aliases = self.statusInfo.getAliasNames()
        aliases.sort()

        d = {}
        d.fromkeys(aliases, common.STATNONE)

        nd = self.fetch(d)
        with open(filepath, 'w') as out_f:
            out_f.write("#\n# Gen2 status snapshot: %s\n#\n" % (time.ctime()))
            out_f.write("{\n")
            for alias in aliases:
                out_f.write("  '%s': %s,\n" % (alias, repr(nd[alias])))
            out_f.write("}\n")

        return ro.OK
    

    def checkpoint(self, filepath=None):
        """Dump the status snapshot to a file.  Format will be a Python
        dictionary.  Unlike dump(), aliases will not be sorted and the
        output may be difficult to read for a human.  But it should be
        much faster to read and write for python.  Can be used to initialize
        status on a reboot
        """
        if not filepath:
            filepath = self.checkptfile

        self.logger.info("Checkpointing status...")
        with self._lock:
            with open(filepath, 'w') as out_f:
                out_f.write("#\n# Gen2 status snapshot: %s\n#\n" % (time.ctime()))
                out_f.write(str(self.g2status))

        self.logger.info("Done.")
        return ro.OK
    

    def restore(self, filepath):
        """Initialize aliases from a file specified by filepath.
        Format is a Python dictionary.
        """
        try:
            with open(filepath, 'r') as in_f:
                statusDict = eval(in_f.read())
            
            self.store(statusDict)
            return ro.OK

        except IOError, e:
            self.logger.error("Can't open file (%s) for status priming: %s" % (
                filepath, str(e)))
            raise e


    ################################################################
    # Below interfaces are used by Derive.py
    ################################################################

    def fetchList2Dict(self, aliasnames, derive=False):
        """Fetch a list of aliases into a dictionary of key/value pairs.
        If derive==True, then derived status values are freshly
        derived (default is False).

        This interface is primarily called from the Derive.py module.
        """

        statusDict = {}.fromkeys(aliasnames, common.STATNONE)

        self.__fetch(statusDict, derive=derive)
            
        return statusDict


    ################################################################
    # Below interfaces are used by Monitor.py
    ################################################################

    def remote_update(self, valDict, name, channels):
        """Callback function from the monitor when we receive information
        about a status table update in the status interface.
        """
        self.logger.debug("valDict: %s" % str(valDict))

        for path in valDict.keys():
            match = regex_statint.match(path)
            if not match:
                # Skip things that don't match the expected paths
                self.logger.error("No match for path '%s'" % path)
                continue

            tblName = match.group(1)

            # Create and start a task to update these aliases in the store
            t = Task.FuncTask(self.updateAliases,
                              [tblName], {})
            t.init_and_start(self)

        return ro.OK


    def remote_delete(self, valDict, name, channels):
        """Callback function from the monitor when we receive information
        about deleting values.  This should never be called.
        """
        self.logger.debug("valDict: %s" % str(valDict))

        return ro.OK


    def updateAliases(self, tblName):
        """Method that gets called as a task (see remote_update() method),
        invoked when we receive information that a table (tblName) has been
        updated in the status interface.
        """
        with self._lock:
            if tblName in self.ignoreTables:
                return

            try:
                # Currently always fetch the updated status
                self.statusObj.invalidateTable(tblName)

                # Fetch the table data if the data is not stale according to
                # the deltas defined in the statusObj
                if self.statusObj.isTableExpired(tblName):
                    self.statusObj.updateTable(tblName)

                    # Get all status aliases defined by this table
                    aliases = self.statusInfo.tableToAliases(tblName)
                    statusDict = self.statusObj.fetchList(aliases)
                    self.logger.debug("fetched statusDict=%s" % str(statusDict))

                    # Store those locally
                    self.__store(statusDict, derive=True)

            except st.statusError, e:
                self.logger.error("Error updating aliases for table '%s': %s" % (
                    tblName, str(e)))
                #raise e

        # Inform world of updated tables on statupd channel
        tag = ("mon.statupd.%s" % tblName)
        self.monitor.setvals(['statupd'], tag, upd_time=time.time())


    def startIgnoreTable(self, tblName):
        self._lock.acquire()
        try:
            self.ignoreTables.add(tblName)
            
        finally:
            self._lock.release()
        
    def stopIgnoreTable(self, tblName):
        self._lock.acquire()
        try:
            self.ignoreTables.remove(tblName)
            
        finally:
            self._lock.release()
        
################################################################
# Program
################################################################

def main(options, args):

    svcname = options.svcname
    logger = ssdlog.make_logger(svcname, options)

    # TODO: parameterize monitor channels
    monchannels = ['status', 'statupd']

    # Initialize remote objects subsystem.
    try:
        ro.init()

    except ro.remoteObjectError, e:
        logger.error("Error initializing remote objects subsystem: %s" % str(e))
        sys.exit(1)

    cso = None
    status = None
    minimon = None
    mon_started = False
    status_svr = None
    svr_started = False

    # Global termination flag
    ev_quit = threading.Event()
    
    def quit():
        logger.info("Shutting down status service...")
        if status:
            # Attempt to save current state
            status.checkpoint()
        if svr_started:
            status_svr.ro_stop(wait=True)
        if minimon:
            minimon.stop_server(wait=True)
            minimon.stop(wait=True)

    def SigHandler(signum, frame):
        """Signal handler for all unexpected conditions."""
        logger.error('Received signal %d' % signum)
        quit()
        ev_quit.set()

    # Set signal handler for signals
    signal.signal(signal.SIGINT, SigHandler)
    signal.signal(signal.SIGTERM, SigHandler)

    logger.info("Starting status service...")
    try:
        if not options.statint:
            stathost = SOSSrpc.get_myhost(short=True)
        else:
            stathost = options.statint

        #cso = gen2StatusObj(logger, stathost)
        cso = st.cachedStatusObj(stathost)

        # Create mini monitor to reflect to main monitor
        mymonname = ('%s.mon' % svcname)
        minimon = Monitor.Monitor(mymonname, logger, numthreads=15)
        minimon.start()
        minimon.start_server(usethread=True)
        mon_started = True

        if options.monitor:
            # Subscribe main monitor to our updates
            minimon.subscribe(options.monitor, monchannels, {})

            # Subscribe ourselves to the statint feed via main monitor
            minimon.subscribe_remote(options.monitor, ['statint'], {})

        # Configure logger for logging via our monitor
        if options.logmon:
            minimon.logmon(logger, options.logmon, ['logs'])

        # Create status object
        status = StatusServer(cso, logger, minimon, monchannels=monchannels,
                              checkptfile=options.checkptfile)

        # Initialize it
        status.initialize()

        # Register status callbacks to monitor channels
        minimon.subscribe_local(status, ['statint'])

        # Create RO server to handle fetch and store requests
        status_svr = ro.remoteObjectServer(svcname=svcname,
                                           obj=status, logger=logger,
                                           port=options.port,
                                           ev_quit=ev_quit,
                                           usethread=False)
        try:
            print "Press ^C to terminate the server."
            status_svr.ro_start(wait=True)
            svr_started = True

        except KeyboardInterrupt:
            logger.error("Caught keyboard interrupt!")
            
    finally:
        quit()
        
    
if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options] command [args]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("--checkpt", dest="checkptfile", default='status.cpt',
                      metavar="FILE",
                      help="Use FILE as a checkpoint file.")
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-m", "--monitor", dest="monitor", default='monitor',
                      metavar="NAME",
                      help="Subscribe to feeds from monitor service NAME")
    optprs.add_option("--port", dest="port", type="int", default=None,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--statint", dest="statint", metavar="HOST",
                      help="Use HOST for the status interface")
    optprs.add_option("--svcname", dest="svcname", metavar="NAME",
                      default='status',
                      help="Register using NAME as service name")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])


    # Are we debugging this?
    if options.debug:
        import pdb

        pdb.run('main(options, args)')

    # Are we profiling this?
    elif options.profile:
        import profile

        print "%s profile:" % sys.argv[0]
        profile.run('main(options, args)')

    else:
        main(options, args)


# END

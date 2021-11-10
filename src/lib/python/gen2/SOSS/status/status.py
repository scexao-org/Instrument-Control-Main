#!/usr/bin/env python
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Sep  9 13:05:05 HST 2011
#]
#
#

# remove once we're certified on python 2.6
from __future__ import with_statement

import sys, re, signal, time, os
import threading

import Bunch
import Task
import SOSS.SOSSrpc as SOSSrpc
import SOSS.status as st
import interface
import Derive
import common
import remoteObjects as ro
import remoteObjects.Monitor as Monitor
import ssdlog

version = '20090519.0'


# Regex used to discover/parse statint info
regex_statint = re.compile(r'^mon\.statint\.(\w+)$')


specialValues = {
    # --- CONSTANTS ---
    # Following copied from current (2006-08-29) /oss_data/OBS_NFS/OSSL_StatU
    # file on obs1.  I can find no program that writes this file, and the Unix
    # file date is 2005-10-10, so it hasn't changed recently.  Hence, I am
    # assuming these values are contants.
    'FITS.SBR.WEATHER': 'Fine',
    'FITS.SBR.TRANSP' : 1.000,
    'FITS.SBR.TELESCOP': 'Subaru',
    }


class StatusReceiver(interface.StatusReceiver):
    
    def set_server(self, serverObj):
        self.server = serverObj
        
    def notify(self, tblName):
        self.server.updateAliases(tblName)


class statusServerError(Exception):
    """Class for errors thrown by the status server.
    """
    pass

class StatusServer(object):
    
    def __init__(self, statusObj, logger, monitor, threadPool,
                 monchannels=['status'], checkptfile='status.cpt',
                 ut1utcfile=None, ev_quit=None):

        self.logger = logger
        self.monitor = monitor
        self.threadPool = threadPool
        self.monchannels = monchannels
        self.statusObj = statusObj
        self.checkptfile = checkptfile

        # Needed for starting our own tasks on it
        self.tag = 'status'
        self.shares = ['logger', 'threadPool']

        # This holds the current decoded status values
        #self.g2status = Bunch.threadSafeBunch()
        self.g2status = {}

        self.mon_transmit = common.mon_transmit

        # Lock for mutual exclusion
        #self._lock = self.g2status.getlock()
        self._lock = threading.RLock()

        self.monxmit_interval = 1.0
        self.monxmit_lastDict = {}
        self.monxmit_nextDict = {}
        self.ev_quit = ev_quit
        
        # For looking up information about tables, aliases, etc.
        # share statusInfo object
        self.statusInfo = self.statusObj.get_statusInfo()

        # For deriving status
        self.derive = Derive.statusDeriver(self, logger)

        # Initialize UT1-UTC data
        self.ut1utc_file = ut1utcfile

        # Tables to ignore, can be set dynamically
        self.ignoreTables = set([])

        # Aliases to ignore, can be set dynamically
        self.ignoreAliases = set([])


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
#             mon_d = {}
            
            # Store status items
            self.logger.debug("Stored: %s" % str(statusDict))
            self.g2status.update(statusDict)

            if self.mon_transmit:
                self.monxmit_nextDict.update(statusDict)

            if derive:
                # Compute derived aliases linked to aliases sent.
                d = self.derive.aliasesToDerivedAliasesDict(statusDict.keys(),
                                                            None)
                if d:
                    self.derive.derive(d)
                    self.logger.debug("Derived: %s" % str(d))
                    self.g2status.update(d)

                    if self.mon_transmit:
                        self.monxmit_nextDict.update(d)

#             if self.mon_transmit:
#                 # Update status seen through the monitor
#                 self.monitor.update('mon.status', mon_d, ['status'])
            
    def __monxmit_loop(self):

        while not self.ev_quit.isSet():

            cur_time = time.time()
            time_end = cur_time + self.monxmit_interval

            mon_d = {}

            #self.logger.debug("nextDict= %s" % str(self.monxmit_nextDict))
            with self._lock:
                for alias, val in self.monxmit_nextDict.items():
                    try:
                        old_val = self.monxmit_lastDict[alias]

                        # Don't send values that we have already sent that
                        # haven't changed
                        if val == old_val:
                            continue

                    except KeyError:
                        pass

                    self.monxmit_lastDict[alias] = val

                    if isinstance(val, long) and common.ro_long_fix:
                        val = hex(val)
                    # expat (XML-RPC parser) does not like NULs
                    elif isinstance(val, str) and ('\x00' in val):
                        # Just skip these items
                        continue

                    mon_d[alias] = val

                self.monxmit_nextDict = {}

            #self.monxmit(mon_d)
            try:
                # Update status seen through the monitor
                self.logger.debug("Sending status via monitor: %s" % str(mon_d))
                self.monitor.update('mon.status', mon_d, ['status'])

            except Exception, e:
                self.logger.error("Error transmitting status: %s" % str(e))
                
            delta = time_end - cur_time
            if delta > 0:
                self.ev_quit.wait(delta)


    ################################################################
    # Public interfaces (over remoteObjects)
    ################################################################

    def initialize(self):
        """Initialize the status system for use.
        """
        self.update_ut1utc(self.ut1utc_file)
        try:
            # Try to restore from last known checkpoint file
            self.restore(self.checkptfile)
            
        except IOError, e:
            # No checkpoint file, so update bare status dict with known
            # special values
            self.g2status.update(specialValues)

        t = Task.FuncTask(self.__monxmit_loop, [], {})
        t.init_and_start(self)
        
        
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


    def fetchDict(self, aliases):
        """Fetch the list of status aliases in the sequence _aliases_
        and return a dictionary of the results.
        """
        fetchDict = {}.fromkeys(aliases, common.STATNONE)
        return self.fetch(fetchDict)

        
    def fetchList(self, aliases):
        """Fetch the list of status aliases in the sequence _aliases_
        and return a list with the results in the same order as the
        aliases.
        """
        statusDict = self.fetchDict(aliases)
        return [ statusDict[key] for key in aliases ]

        
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


    def update_ut1utc(self, filepath):
        """Update the UT1_UTC data used by the deriver.
        """
        self.logger.info("Updating UT1-UTC data from %s" % filepath)
        with self._lock:
            self.derive.read_UT1_UTC_table(filepath)

        self.logger.info("Done.")
        return ro.OK
    

    def update_statusInfo(self):
        """Reload the status alias information.
        """
        self.logger.info("Reloading status configuration files...")
        with self._lock:
            self.statusInfo.reloadInfo()

        self.logger.info("Done.")
        return ro.OK
    

    def update_monTransmit(self, onOff):
        """Enable/disable monitor status transmission.
        """
        self.logger.info("Setting monitor status transmission to %s" % (
                str(onOff)))
        with self._lock:
            self.mon_transmit = onOff

        self.logger.info("Done.")
        return ro.OK
    

    def update_deriver(self):
        """Reload the status deriver.
        """
        self.logger.info("Reloading status deriver module...")
        with self._lock:
            reload(Derive)
            self.derive = Derive.statusDeriver(self, self.logger)

            self.update_ut1utc(self.ut1utc_file)

        self.logger.info("Done.")
        return ro.OK
    

    ################################################################
    # Below interfaces are used by Derive.py and interface.py
    ################################################################

    def fetchList2Dict(self, aliasnames, derive=False):
        """Fetch a list of aliases into a dictionary of key/value pairs.
        If derive==True, then derived status values are freshly
        derived (default is False).

        This interface is primarily called from the Derive.py and
        interface.py modules.
        """

        statusDict = {}.fromkeys(aliasnames, common.STATNONE)

        self.__fetch(statusDict, derive=derive)
            
        return statusDict


    ################################################################
    # Below interfaces are used by Monitor.py
    ################################################################

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

                    if self.ignoreAliases:
                        aliases = set(aliases).difference(self.ignoreAliases)

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


    def monxmit(self, fetchDict):

        self.__fetch(fetchDict, derive=False, allow_none=False)

        # Get current status set
        mon_d = {}
        with self._lock:
            mon_d.update(common.ro_sanitize(fetchDict, pfx=None))

        try:
            # Update status seen through the monitor
            self.monitor.update('mon.status', mon_d, ['status'])

        except Exception, e:
            self.logger.error("Error transmitting status: %s" % str(e))
            

    ################################################################
    # Debugging/special commands
    ################################################################

    def startIgnoreTable(self, tblName):
        with self._lock:
            self.ignoreTables.add(tblName)
        
    def stopIgnoreTable(self, tblName):
        with self._lock:
            self.ignoreTables.remove(tblName)
        
    def startIgnoreAlias(self, aliasName):
        with self._lock:
            self.ignoreAliases.add(aliasName)

    def stopIgnoreAlias(self, aliasName):
        with self._lock:
            self.ignoreAliases.remove(aliasName)
        
    def additems(self, aliaslist):
        with self._lock:
            for alias in aliaslist:
                self.monxmit_fetchDict[alias] = common.STATNONE
        
    def delitems(self, aliaslist):
        with self._lock:
            for alias in aliaslist:
                del self.monxmit_fetchDict[alias]
        
    def update_monxmit_interval(self, interval):
        self.logger.info("Updating monitor transmit interval (%f)" % (
            interval))
        with self._lock:
            self.monxmit_interval = interval

        self.logger.info("Done.")
        return ro.OK
    

################################################################
# Program
################################################################

def main(options, args):

    svcname = options.svcname

    # Make top-level logger.
    logger = ssdlog.make_logger(svcname, options)

    # TODO: parameterize monitor channels
    monchannels = ['status', 'statupd', 'statint']

    # Initialize remote objects subsystem.
    try:
        ro.init()

    except ro.remoteObjectError, e:
        logger.error("Error initializing remote objects subsystem: %s" % str(e))
        sys.exit(1)

    statusObj = None
    statint = None
    status = None
    minimon = None
    threadPool = None
    mon_started = False
    thrd_started = False
    status_svr = None
    svr_started = False

    # Global termination flag
    ev_quit = threading.Event()
    
    def run():
        logger.info("Starting status service...")

        # Create object in which to store status tables.  This is a passive
        # object; i.e. there are no active threads therein
        statusObj = st.storeStatusObj()

        threadPool = Task.ThreadPool(logger=logger,
                                     ev_quit=ev_quit,
                                     numthreads=options.numthreads)
        
        # Create the status interface object
        statint = StatusReceiver(logger, statusObj, threadPool,
                                 ev_quit=ev_quit,
                                 myhost=options.myhost,
                                 monchannels=monchannels,
                                 loghome=options.loghome)

        # Create mini monitor to reflect to main monitor
        mymonname = ('%s.mon' % svcname)
        minimon = Monitor.Monitor(mymonname, logger, ev_quit=ev_quit,
                                  threadPool=threadPool)
        statint.set_monitor(minimon)

        logger.info("Starting thread pool...")
        threadPool.startall(wait=True)
        thrd_started = True

        logger.info("Starting monitor...")
        minimon.start()
        # Configure logger for logging via our monitor
        if options.logmon:
            minimon.logmon(logger, options.logmon, ['logs'])

        minimon.start_server(usethread=True)
        mon_started = True

        if options.monitor:
            # Publish our updates to the main monitor
            minimon.publish_to(options.monitor, monchannels, {})

        if options.ut1utcfile:
            ut1utc_path = options.ut1utcfile
        else:
            if os.environ.has_key('GEN2COMMON'):
                dir = os.environ['GEN2COMMON'] + '/db'
            else:
                dir = os.path.split(sys.modules[__name__].__file__)[0]

            ut1utc_path = ('%s/UT1_UTC.table' % dir)

        # Create status object
        status = StatusServer(statusObj, logger, minimon, threadPool,
                              monchannels=monchannels,
                              checkptfile=options.checkptfile,
                              ut1utcfile=ut1utc_path,
                              ev_quit=ev_quit)

        # Initialize it
        status.initialize()

        # Connect status interface to server for notifications of new
        # table availability
        statint.set_server(status)

        # Start status interface RPCs
        logger.info("Starting status RPC interfaces...")
        statint.start(wait=True)

        # Create RO server to handle fetch and store requests
        status_svr = ro.remoteObjectServer(svcname=svcname,
                                           obj=status, logger=logger,
                                           port=options.port,
                                           ev_quit=ev_quit,
                                           usethread=False,
                                           threadPool=threadPool)
        try:
            print "Press ^C to terminate the server."
            status_svr.ro_start(wait=True)
            svr_started = True

        except KeyboardInterrupt:
            logger.error("Caught keyboard interrupt!")
            
    def quit():
        logger.info("Shutting down status service...")
        if status:
            # Attempt to save current state
            status.checkpoint()
        if statint:
            statint.stop(wait=True)
        if svr_started:
            status_svr.ro_stop(wait=True)
        if minimon:
            minimon.stop_server(wait=True)
            minimon.stop(wait=True)
        if threadPool:
            threadPool.stopall(wait=True)

    def SigHandler(signum, frame):
        """Signal handler for all unexpected conditions."""
        logger.error('Received signal %d' % signum)
        quit()
        ev_quit.set()

    # Set signal handler for signals
    signal.signal(signal.SIGINT, SigHandler)
    signal.signal(signal.SIGTERM, SigHandler)

    try:
        run()
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
    optprs.add_option("--loghome", dest="loghome", default=None,
                      metavar="DIR",
                      help="Specify DIR for status data logs")
    optprs.add_option("-m", "--monitor", dest="monitor", default='monitor',
                      metavar="NAME",
                      help="Subscribe to feeds from monitor service NAME")
    optprs.add_option("--monunit", dest="monunitnum", type="int",
                      default=3, metavar="NUM",
                      help="Target OSSL_MonitorUnit NUM on OBS")
    optprs.add_option("--myhost", dest="myhost", metavar="NAME",
                      help="Use NAME as my hostname for DAQ communication")
    optprs.add_option("--numthreads", dest="numthreads", type="int",
                      default=100,
                      help="Use NUM threads in thread pool", metavar="NUM")
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
    optprs.add_option("--ut1utc", dest="ut1utcfile", default=None,
                      metavar="FILE",
                      help="Read FILE for UT1-UTC data.")
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

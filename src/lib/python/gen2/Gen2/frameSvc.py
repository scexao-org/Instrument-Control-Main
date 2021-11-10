#!/usr/bin/env python
#
# frameSvc.py -- serve up frame numbers
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Apr  9 13:05:05 HST 2012
#]
#
"""
Usage:
 - To simply query what the current value in the table is:
   ./frameSvc.py SPCAM A
 - To query and increment the current value in the table:
   ./frameSvc.py --bump SPCAM A
 - To set/reset a value in the table:
   ./frameSvc.py --set SPCAM SUPA80000060

 - Additionally, there is a remote method getFrames() which can be used
 to fetch multiple frames at once.

 TODO:
 - I'm not sure this is setting the status variables accurately in the
   case where multiple frames are requested in a single reqest
"""

import sys, re, time
import threading
import datetime

import remoteObjects as ro
import remoteObjects.Monitor as Monitor
import Bunch
import logging, ssdlog
from cfg.INS import INSdata as INSconfig
from SOSS.frame import rpcFrameObj, frameError, OSSS_FRAMEServer
import Gen2.db.frame as framedb

serviceName = "frames"

version = "20120409.0"


class frameSvcError(Exception):
    """Class used for raising exceptions in this module.
    """
    pass

class frameSvc(object):
    """
    Implements a frame number service compatible with the one provided
    by SOSS.
    """

    def __init__(self, svcname, logger, monitor=None, monchannels=[]):
        
        self.logger = logger
        self.monitor = monitor
        self.monchannels = monchannels
        # TODO: parameterize tag template (from svcname?)
        self.tag_template = 'mon.frame.%s.frameSvc'

        self.insconfig = INSconfig()
        
        # For updating status system with session info
        # TODO: parameterize object
        self.status = ro.remoteObjectProxy('status')

        # For mutual exclusion
        self.lock = threading.RLock()
        

    # Need this because we don't inherit from ro.remoteObjectServer,
    # but are delegated to from it
    def ro_echo(self, arg):
        return arg


    def _set_necessary_status(self, insname, frameid, frametype):

        instcode = self.insconfig.getCodeByName(insname)

        statusDict = {}
        if frametype == 'A':
            statusDict['FITS.%s.FRAMEID' % instcode] = frameid
        
        elif frametype == 'Q':
            statusDict['FITS.%s.FRAMEIDQ' % instcode] = frameid

        self.logger.debug("Updating status: %s" % str(statusDict))
        self.status.store(statusDict)


    def getFrameMap(self, insname, frametype):
  
        self.logger.info('getting frame map....')
        with self.lock:
            insname = insname.upper()
            frametype = frametype.upper()
            if len(frametype) > 1:
                prefix = frametype[1]
                frametype = frametype[0]
            else:
                prefix = '0'

            try:
                frameid = framedb.getFrameMap(insname, frametype, 
                                              prefix=prefix)

                return (ro.OK, frameid)

            except Exception, e:
                raise frameError("Error obtaining framemap info: %s" % (str(e)))
            
            
    def getFrames(self, insname, frametype, count):
        """Returns a list of frames (bumps the frame number).
        _count_ is the number of frames to get; e.g.:
           getFrames('SPCAM', 'A', 10)
        """
        self.logger.info('getting frames....')
        with self.lock:
            # If user passed e.g. "A7" then use "7" for the prefix,
            # otherwise default to "0" (prefix==most significant digit)
            insname = insname.upper()
            frametype = frametype.upper()
            if len(frametype) > 1:
                prefix = frametype[1]
                frametype = frametype[0]
            else:
                prefix = '0'

            if count <= 0:
                msg = "Error obtaining frames: count (%d) should be > 0" % (count)
                self.logger.error(msg)
                raise frameError(msg)

            # Try to allocate the frames from the database
            try:
                framelist = framedb.alloc(insname, frametype, count, prefix=prefix)

                for frameid in framelist:
                    # Report frame allocation to monitor
                    # TODO: use getInfo to get db allocation time
                    tag = (self.tag_template % frameid)
                    if self.monitor != None:
                        self.monitor.setvals(self.monchannels, tag,
                                             time_alloc=time.time())

                self._set_necessary_status(insname, frameid, frametype)

                self.logger.info("frames allocated: %s" % str(framelist))
                return (ro.OK, framelist)

            except Exception, e:
                raise frameError("Error obtaining frames: %s" % (str(e)))
            
            
    def set_fno(self, insname, frameid):
        """Resets the frame number to the specified count.
        _insname_ should be one of the valid instrument mnemonics (SPCAM, FLDMON)
        _frameid_ should be something like: SUPA80000060
        """
        self.logger.info('setting info....')
        with self.lock:
            self.logger.debug("Processing set_fno for %s %s" % (insname,
                                                                frameid))
            insname = insname.upper()

            frameid = frameid.upper()
            match = re.match('^(\w{3})([AQ])(\d)(\d{7})$', frameid)
            if not match:
                msg = "Frameid not in recognized format: '%s'" % (frameid)
                self.logger.error(msg)
                return (ro.ERROR, msg)

            (inscode, frametype, prefix, count) = match.groups()
            try:
                count = int(count)
            except ValueError, e:
                msg = "Frameid not in recognized format: '%s': %s" % \
                      (frameid, str(e))
                self.logger.error(msg)
                return (ro.ERROR, msg)

            try:
                framedb.resetCount(insname, frametype, count, prefix=prefix)

                self._set_necessary_status(insname, frameid, frametype)

                msg = "Frameid reset to '%s'" % frameid
                self.logger.debug(msg)
                return (ro.OK, msg) 

            except Exception, e:
                raise frameError("Error resetting frame count: %s" % (str(e)))


def client_get(options, args):

    if (len(args) < 2) or (len(args) > 3):
        print "Usage: %s [options] <insname> A|Q <count>"
        print "Use '%s --help' for options"
        sys.exit(1)

 
    # Initialize remote objects subsystem.
    try:
        ro.init()

    except ro.remoteObjectError, e:
        print "Error initializing remote objects subsystem: %s" % str(e)
        sys.exit(1)

    svc = ro.remoteObjectProxy(options.svcname)

    if len(args) == 3:
        try:
            count = int(args[2])
        
        except ValueError, e:
            print "Count should be an integer: '%s'" % (args[2])
            sys.exit(1)
    else:
        count = 1

    # Call remote method
    if options.bump:
        res = svc.getFrames(args[0], args[1], count)
    else:
        res = svc.getFrameMap(args[0], args[1])

    try:
        (code, result) = res
        if code != ro.OK:
            print "Error calling frame server: %s" % str(result)
            sys.exit(1)

    except ValueError, e:
        print "Internal error calling frame server, unexpected return value of '%s'" % str(res)
        sys.exit(1)
        
    print result


def client_set(options, args):

    if len(args) != 2:
        print "Usage: %s [options] <insname> <frameid>"
        print "Use '%s --help' for options"
        sys.exit(1)

    # Initialize remote objects subsystem.
    try:
        ro.init()

    except ro.remoteObjectError, e:
        print "Error initializing remote objects subsystem: %s" % str(e)
        sys.exit(1)

    svc = ro.remoteObjectProxy(options.svcname)

    # Call remote method
    res = svc.set_fno(args[0], args[1])

    # Interpret result
    try:
        (code, result) = res
        if code != ro.OK:
            print "Error calling frame server: %s" % str(result)
            sys.exit(1)
            
    except ValueError, e:
        print "Internal error calling frame server, unexpected return value of '%s'" % str(res)
        sys.exit(1)

    print result


def server(options, args):

    if len(args) != 0:
        print "Usage: %s [options]"
        print "Use '%s --help' for options"
        sys.exit(1)

    svcname = options.svcname
    # TODO: parameterize monitor channel
    monchannels = ['frames']
        
    # Create top level logger.
    logger = ssdlog.make_logger(svcname, options)

    # Initialize remote objects subsystem.
    try:
        ro.init()

    except ro.remoteObjectError, e:
        logger.error("Error initializing remote objects subsystem: %s" % str(e))
        sys.exit(1)

    svc_started = False
    svr_started = False
    mon_started = False

    # Create mini monitor to reflect to main monitor
    minimon = Monitor.Minimon('%s.mon' % svcname, logger,
                              numthreads=options.numthreads)
    minimon.start()
    mon_started = True

    # publish our information to the specified monitor
    if options.monitor:
        channels = list(monchannels)
        minimon.publish_to(options.monitor, channels, {})

    # Configure logger for logging via our monitor
    if options.logmon:
        minimon.logmon(logger, options.logmon, ['logs'])

    try:
        minimon.start_server(port=options.monport, usethread=True)
        
        fm = frameSvc(svcname, logger, 
                      monitor=minimon, monchannels=monchannels)

        threadPool = minimon.get_threadPool()

        # Superclass constructor
        svc = ro.remoteObjectServer(svcname=svcname,
                                    obj=fm, logger=logger,
                                    port=options.port,
                                    usethread=True,
                                    threadPool=threadPool)

        # Create sun-rpc frame interface
        svr = OSSS_FRAMEServer(logger=logger, frame_func=fm.getFrames)
        
        logger.info("Starting frame service.")
        try:
            svc.ro_start(wait=True)
            svc_started = True

            svr.start(wait=True)
            svr_started = True
            
            while True:
                print "Press ^C to terminate server..."
                sys.stdin.readline()
            
        except KeyboardInterrupt:
            logger.error("Caught keyboard interrupt!")
            
    finally:
        if mon_started:
            minimon.stop(wait=True)
        if svc_started:
            svc.ro_stop(wait=True)
        if svr_started:
            svr.stop(wait=True)
        
    logger.info("Stopping frame service...")


if __name__ == '__main__':
    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("--bump", dest="bump", default=False,
                      action="store_true",
                      help="Bump the frame number after query")
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-m", "--monitor", dest="monitor", default='monitor',
                      metavar="NAME",
                      help="Reflect internal status to monitor service NAME")
    optprs.add_option("--monport", dest="monport", type="int", default=None,
                      help="Register monitor using PORT", metavar="PORT")
    optprs.add_option("--numthreads", dest="numthreads", type="int",
                      default=50,
                      help="Use NUM threads", metavar="NUM")
    optprs.add_option("--port", dest="port", type="int", default=None,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--server", dest="server", default=False,
                      action="store_true",
                      help="Run the server instead of client")
    optprs.add_option("--set", dest="set", default=False,
                      action="store_true",
                      help="Run the set_fno client")
    optprs.add_option("--svcname", dest="svcname", metavar="NAME",
                      default=serviceName,
                      help="Register using NAME as service name")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    # Are we debugging this?
    if options.debug:
        import pdb

        pdb.run('server(options, args)')

    # Are we profiling this?
    elif options.profile:
        import profile

        print "%s profile:" % sys.argv[0]
        profile.run('server(options, args)')

    elif options.server:
        server(options, args)

    elif options.set:
        client_set(options, args)

    else:
        client_get(options, args)
       
    
#END

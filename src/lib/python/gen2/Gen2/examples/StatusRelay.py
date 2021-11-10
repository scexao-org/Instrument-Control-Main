#! /usr/bin/env python
#
# StatusRelay.py -- Provide a status like feed from the summit or another
#     relay.
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Sep  9 13:05:05 HST 2011
#]
import sys, time
import threading

import remoteObjects as ro
import remoteObjects.Monitor as Monitor
import ssdlog

class StatusRelay(object):

    def __init__(self, logger, statsvc, monsvc, monitor, channels):
        self.logger = logger
        # mutex to arbitrate access to status values
        self.lock = threading.RLock()
        # status feed will be stored in here
        self.statusDict = {}

        # status system
        self.statsvc = statsvc
        self.stobj = None

        # monitor system
        self.monsvc = monsvc
        self.monitor = monitor
        self.channels = channels

    # This function will be called at an approximately 1Hz rate with status
    # updates
    def status_cb(self, payload, name, channels):
        try:
            bnch = Monitor.unpack_payload(payload)
            if bnch.path != 'mon.status':
                return

            with self.lock:
                ## print "status updated: %s" % (time.strftime("%H:%M:%S",
                ##                                             time.localtime()))
                self.statusDict.update(bnch.value)
            self.logger.debug("Status updated: %s" % str(bnch.value))

        except Monitor.MonitorError, e:
            print "monitor error: %s" % (str(e))

    def update_statusProxy(self):
        # reset our proxy object to the status system
        self.stobj = ro.remoteObjectProxy(self.statsvc)

    def update_monitorFeed(self):
        # Subscribe our local callback function
        self.monitor.subscribe_cb(self.status_cb, self.channels)
    
        # subscribe our monitor to the publication feed
        self.monitor.subscribe_remote(self.monsvc, self.channels, {})


    def primeStatus(self, aliases):
        # Fetch the keys in _aliases_ from the status system and store
        # them in our status dictionary
        fetchDict = {}.fromkeys(aliases, 0)
        statusDict = {}
        try:
            statusDict = self.stobj.fetch(fetchDict)

        except Exception, e:
            self.logger.error("Error fetching needed status items(%s): %s" % (
                str(aliases), str(e)))
            self.logger.info("Resetting proxy to try again...")
            self.update_statusProxy()
            try:
                statusDict = self.stobj.fetch(fetchDict)

            except Exception, e:
                self.logger.error("2nd try error fetching needed status items (%s): %s" % (
                    str(aliases), str(e)))
                return

        # Update our copy of the status
        with self.lock:
            self.statusDict.update(statusDict)

        
    def fetchDict(self, aliases):
        """Fetch the list of status aliases in the sequence _aliases_
        and return a dictionary of the results.
        """
        fetchDict = {}.fromkeys(aliases, 0)
        return self.fetch(fetchDict)
        
    def fetchList(self, aliases):
        """Fetch the list of status aliases in the sequence _aliases_
        and return a list with the results in the same order as the
        aliases.
        """
        statusDict = self.fetchDict(aliases)
        return [ statusDict[key] for key in aliases ]
        
    def fetch(self, fetchDict):
        """Gen2 status system compatible fetch.
        Fetch the list of status aliases corresponding to the keys in the
        fetchDict, and return a dictionary of the results.
        """
        # Find out which status items are requested that we don't have
        reqkeys = set(fetchDict.keys())
        with self.lock:
            ourkeys = set(self.statusDict.keys())
        missing = reqkeys - ourkeys

        # Fetch the missing items
        if len(missing) > 0:
            self.logger.info("Fetching missing aliases: %s" % str(missing))
            self.primeStatus(missing)

        # Get the items as a transaction
        with self.lock:
            d = self.statusDict
            statusDict = dict((k, d[k]) for k in reqkeys)

        return statusDict

    def fetchOne(self, aliasName):
        """Gen2 status system compatible fetch.
        Fetch the value of a single status alias.
        """
        res = self.fetch({aliasName: 0})
        return res[aliasName]
        
        
def main(options, args):

    ro_hosts = options.gen2host.split(',')
    ro.init(ro_hosts)

    svcname = options.svcname
    monname = svcname + '.mon'
    
    # create a real logger if you want logging
    logger = ssdlog.make_logger(svcname, options)

    ev_quit = threading.Event()
    
    # Create a local subscribe object
    myhost = ro.get_myhost(short=True)
    mymon = Monitor.Monitor(monname, logger)

    channels = options.channels.split(',')
    relay = StatusRelay(logger, options.statsvc, options.monitor,
                        mymon, channels)

    # Startup monitor
    mymon.start(wait=True)
    monport = options.monport
    if not monport:
        monport = options.port + 1
    mymon.start_server(wait=True, port=monport)
    threadPool = mymon.get_threadPool()

    svc = ro.remoteObjectServer(svcname=options.svcname,
                                obj=relay, logger=logger,
                                port=options.port,
                                default_auth=None,
                                ev_quit=ev_quit,
                                usethread=False,
                                threadPool=threadPool)
    try:
        relay.update_statusProxy()
        relay.update_monitorFeed()
    
        try:
            print "Press ^C to terminate the server."
            svc.ro_start(wait=True)
            svr_started = True

        except KeyboardInterrupt:
            logger.error("Caught keyboard interrupt!")
            ev_quit.set()
            
    finally:
        logger.info("Shutting down...")
        mymon.unsubscribe_remote('monitor', channels, {})
        mymon.stop_server()
        mymon.stop()
        
if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%prog'))
    
    optprs.add_option("--channels", dest="channels", metavar="LIST",
                      default="status,errors",
                      help="LIST of channels to subscribe to")
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--gen2host", dest="gen2host", metavar="HOST",
                      default="g2ins1.sum.subaru.nao.ac.jp",
                      help="Connect to Gen2 system using HOST")
    optprs.add_option("-m", "--monitor", dest="monitor", 
                      metavar="NAME", default='monitor',
                      help="Subscribe to status from monitor service NAME")
    optprs.add_option("--monport", dest="monport", type="int", default=None,
                      help="PORT for my monitor", metavar="PORT")
    optprs.add_option("--numthreads", dest="numthreads", type="int",
                      default=50,
                      help="Use NUM threads", metavar="NUM")
    optprs.add_option("-p", "--port", dest="port", type="int", default=9877,
                      help="PORT for my service", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("-s", "--svcname", dest="svcname", metavar="NAME",
                      help="Register using NAME as service name")
    optprs.add_option("--statsvc", dest="statsvc", metavar="NAME",
                      default="status",
                      help="Get status from service NAME")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    if len(args) != 0:
        optprs.error("incorrect number of arguments")

    if not options.svcname:
        optprs.error("Please specify a service name with -s")

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


#! /usr/bin/env python
#
# remoteObjectNameSvc.py -- remote object name service.
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Dec 19 13:25:13 HST 2011
#]
#
# TODO:
# [ ] How to handle authentication for monitor
# [ ] How to handle authentication for name service
#
"""
This is the name service for the remoteObjects middleware.

Each service created by remoteObjectService registers itself here so that
it can be looked up by name instead of (host, port).

Synchronization between name servers is accomplished using the Monitor
service (built on top of PubSub).  The data is stored in the following
hierarchy in the local monitor store:

mon.
    names.
          <svcname>.
                    <host>:<port>.
                                  pingtime
                                  secure

Updates come in on the channel 'names' and these propagate between the
name servers.

"""
# remove once we're certified on python 2.6
from __future__ import with_statement

import sys, os, time
import re
import threading
# optparse imported below (if needed)

import remoteObjects as ro
import Monitor
import ssdlog

# Our version
version = '20100707.0'


#regex_ping = re.compile(r'^mon\.names\.(?P<svcname>.+)\.(?P<host>[^:]+):(?P<port>\d+)$')


# For generating errors from this module
#
class nameServiceError(Exception):
    pass


# TODO:
#  - The registration of names is done via individual monitor updates.
#    This may be too fine grained of a method.  When we want to sync all
#    of our own registrations to another node it would be better to send
#    them all in a single update.
#
class remoteObjectNameService(object):

    def __init__(self, monitor, logger, myhost, purge_delta=30.0):

        self.logger = logger
        self.monitor = monitor
        self.myhost = myhost

        # How long we don't hear from somebody before we drop them
        self.purge_delta = purge_delta

        # self state mutex
        self.lock = threading.RLock()

        # hook for possible future authentication
        self.auth = None

        # For monitor use
        self.tagpfx = 'mon.names'
        self.channels = ['names']


    def _register(self, name, host, port, options, hosttime, replace=True):
        # Create monitor path for this name:
        #   mon.names.<svcname>.<host>:<port>
        # service name and host name have to be escaped for '.'
        tag = '%s.%s.%s:%d' % (self.tagpfx,
                               name.replace('.', '%'),
                               host.replace('.', '%'), port)

        if not self.monitor.has_key(tag):
            self.logger.info("Registering remote object service %s:%d under name '%s'" % (
                host, port, name))

        # TEMP: until we can deprecate former api
        if isinstance(options, bool):
            secure = options
            options = {}
        elif isinstance(options, dict):
            secure = options.get('secure', False)
        else:
            raise nameServiceError("flags argument (%s) should be a dict" % (
                str(flags)))

        keep = options.get('keep', False)
        
        # Notify monitor
        try:
            self.monitor.setvals(self.channels, tag, secure=secure,
                                 pingtime=hosttime, keep=keep)
                        
            return 1

        except Exception, e:
            self.logger.error("Failed to register '%s': %s" % (
                name, str(e)))
            return 0
    

    def register(self, name, host, port, options, replace=True):
        """Register a new name at a certain host and port."""

        hosttime = time.time()
        return self._register(name, host, port, options,
                              hosttime, replace=replace)

    def ping(self, name, host, port, options, hosttime):
        """Get pinged by service.  Register this service if we have never
        heard of it, otherwise just record the time that we heard from it.
        """
        now = time.time()
        self.logger.info("Ping from '%s' (%s:%d) -- %.4f [%.4f]" % (
            name, host, port, hosttime, now-hosttime))

        return self._register(name, host, port, options, hosttime)

        
    def unregister(self, name, host, port):
        """Unregister a new name at a certain host and port."""
        
        # Create monitor path for this name:
        #   mon.names.<svcname>.<host>:<port>
        # service name and host name have to be escaped for '.'
        tag = '%s.%s.%s:%d' % (self.tagpfx,
                               name.replace('.', '%'),
                               host.replace('.', '%'), port)
        
        if self.monitor.has_key(tag):
            self.logger.info("Unregistering remote object service %s:%d under name '%s'" % (
                host, port, name))
            
        # Notify monitor
        try:
            self.monitor.delete(tag, self.channels)
            
            return 1

        except Exception, e:
            self.logger.error("Failed to unregister '%s': %s" % (
                name, str(e)))
            return 0
        

    def clearName(self, name):
        """Clear all registrations associated with _name_."""
        
        # mon.names.<svcname>
        # service name has to be escaped for '.'
        tag = '%s.%s' % (self.tagpfx, name.replace('.', '%'))

        try:
            self.monitor.delete(tag, self.channels)
            
            return 1

        except Exception, e:
            self.logger.error("Failed to unregister '%s': %s" % (
                name, str(e)))
            return 0

        
    def clearAll(self):
        """Clear all name registrations."""

        # Notify monitor
        try:
            self.monitor.delete(self.tagpfx, self.channels)
            
            # TODO: PROBLEM: above call removes 'names' from the local cache
            # which is needed to set a name server in remoteObjects.py
            #self.register('names', self.myhost, options.port, options.secure)
            self.register('names', self.myhost, ro.nameServicePort,
                          ro.default_secure)
            return 1

        except Exception, e:
            self.logger.error("Failed to unregister '%s': %s" % (
                name, str(e)))
            return 0

        
    def getNames(self):
        """Return a list of all registered names."""

        tree = self.monitor.getTree(self.tagpfx)
        if not isinstance(tree, dict):
            return []
        res = []
        for name in tree.keys():
            res.append(name.replace('%', '.'))
        return res

        
    def getNamesSorted(self):
        """Returns a sorted list of all registered names."""

        res = self.getNames()
        res.sort()
        
        return res

        
    def purgeDead(self, name):
        """Purge all registered instances of _name_ that haven't been heard
        from in purge_delta seconds."""
        
        hostlist = self.getHosts(name)
        anyleft = False
        
        for (host, port) in self.getHosts(name):
            tag = '%s.%s.%s:%d' % (self.tagpfx,
                                   name.replace('.', '%'),
                                   host.replace('.', '%'), port)
            vals = self.monitor.getitems_suffixOnly(tag)
            if not vals.has_key('pingtime'):
                # No pingtime?  Give `em the boot!
                self.unregister(name, host, port)

            else:
                # Haven't heard from them in a while?  Ditto!
                delta = time.time() - vals['pingtime']
                if (delta > self.purge_delta) and (not vals['keep']):
                    self.unregister(name, host, port)

                else:
                    anyleft = True

        # if there are no more live hosts left, drop the service name
        # as well
        if not anyleft:
            tag = '%s.%s' % (self.tagpfx, name.replace('.', '%'))
            try:
                self.monitor.delete(tag, self.channels)
            
            except Exception, e:
                self.logger.error("Failed to purge name '%s': %s" % (
                    name, str(e)))
                    

    def purgeAll(self):
        """Iterate over all known registrations and perform a purge
        operation from those we haven't heard from lately."""
        
        for name in self.getNames():
            # TEMP HACK UNTIL WE GET BUMP OUR OWN PING TIME
            if name in ('names',):
                continue
            self.purgeDead(name)

        
    def purgeLoop(self, interval):
        """Loop invoked to periodically purge data from """
        while True:
            time_end = time.time() + interval

            try:
                self.purgeAll()
            except Exception, e:
                self.logger.error("Purge loop error: %s" % (str(e)))

            sleep_time = max(0, time_end - time.time())
            time.sleep(sleep_time)
        
        
    def getHosts(self, name):
        """Return a list of all (host, port) pairs associated with
        a registered name.
        TO BE DEPRECATED--DO NOT USE.  USE getInfo() INSTEAD."""
        
        # mon.names.<svcname>
        # service name has to be escaped for '.'
        tag = '%s.%s' % (self.tagpfx, name.replace('.', '%'))

        tree = self.monitor.getTree(tag)
        if not isinstance(tree, dict):
            return []

        res = []
        for key in tree.keys():
            host, port = key.split(':')
            host = host.replace('%', '.')
            port = int(port)
            res.append((host, port))

        return res

        
    def getInfo(self, name):
        """Return a list of dicts of service info associated with
        a registered name.  This should be used in preference to
        getHosts for most applications."""
        
        # mon.names.<svcname>
        # service name has to be escaped for '.'
        tag = '%s.%s' % (self.tagpfx, name.replace('.', '%'))

        tree = self.monitor.getTree(tag)
        if not isinstance(tree, dict):
            return []

        res = []
        for key in tree.keys():
            host, port = key.split(':')
            host = host.replace('%', '.')
            port = int(port)
            secure = tree[key].get('secure', False)
            pingtime = tree[key].get('pingtime', 0)
            res.append({ 'name': name, 'host': host, 'port': port,
                         'secure': secure, 'pingtime': pingtime })

        return res
        

    def _getInfoPred(self, pred_fn):
        """Return a list of info (dicts) for any services that match
        predicate function _pred_fn_."""
        res = []
        for name in self.getNames():
            infolist = self.getInfo(name)

            for d in infolist:
                if pred_fn(d):
                    res.append(d)

        return res

    def getInfoHost(self, host):
        """Return the info for any services registered on _host_."""
        return self._getInfoPred(lambda d: d['host'] == host)

    def getNamesHost(self, host):
        """Return the names for any services registered on _host_."""
        res = self.getInfoHost(host)
        return map(lambda d: d['name'], res)

    def _syncInfoPred(self, pred_fn):
        """Ping any services that match predicate function _pred_fn_."""
        res = self._getInfoPred(pred_fn)
        for d in res:
            self.ping(d['name'], d['host'], d['port'], d['secure'],
                      d['pingtime'])
    
    def syncInfoSelf(self):
        """Ping any services that registered with us."""
        self._syncInfoPred(lambda d: d['host'] == self.myhost)
        
                    
##     # called if new data becomes available via publish/subscribe
##     #
##     def ps_update(self, payload, name, channels):
##         self.logger.debug("received values '%s'" % str(payload))

##         try:
##             bnch = Monitor.unpack_payload(payload)

##         except Monitor.MonitorError:
##             self.logger.error("malformed packet '%s': %s" % (
##                 str(payload), str(e)))
##             return

##         match = regex_ping.match(bnch.path)
##         if match:
##             # --> path is mon.names.<svcname>.<host>:<port>
##             svcname = match.group('svcname').replace('%', '.')
##             host = match.group('host').replace('%', '.')
##             port = int(match.group('port'))

##             print host, port, bnch.value


    
#------------------------------------------------------------------
# MAIN PROGRAM
#
def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('names', options)

    try:
        myhost = ro.get_myhost()

    except Exception, e:
        raise nameServiceError("Can't get my own hostname: %s" % str(e))

    # Create a local monitor
    myMonName = 'names-%s-%d.mon' % (myhost.replace('.', '_'),
                                     options.monport)
    mymon = Monitor.Monitor(myMonName, logger, numthreads=options.numthreads)
    mymon.add_channels(['names'])
    
    authstr = options.monauth
    if not authstr:
        authstr = "%s:%s" % (myMonName, myMonName)
        monAuthDict = { myMonName: myMonName }
    else:
        l = authstr.split(':')
        monAuthDict = { l[0]: l[1] }

    # Get authorization params, if provided for our name service
    authDict = {}
    if options.auth:
        auth = options.auth.split(':')
        authDict[auth[0]] = auth[1]

    nsobj = remoteObjectNameService(mymon, logger, myhost,
                                    purge_delta=options.purge_delta)
    
    # Hack to use our local object as the name server for our local monitor
    ro.default_ns = nsobj

    threadPool = mymon.get_threadPool()
    
    # Create remote object server for this object.
    # svcname to None temporarily because we get into infinite loop
    # try to register ourselves.
    nssvc = ro.remoteObjectServer(name='names', obj=nsobj, svcname=None,
                                  port=options.port, logger=logger,
                                  usethread=True, threadPool=threadPool,
                                  authDict=authDict,
                                  secure=options.secure,
                                  cert_file=options.cert)
    
    # Subscribe our callback functions to the local monitor
    #mymon.subscribe_cb(nsobj.ps_update, ['names'])

    server_started = False
    
    try:
        try:
            logger.info("Starting monitor...")
            # Startup monitor threadpool
            mymon.start(wait=True)
            # start_server is necessary if we are subscribing, but not if only
            # publishing
            mymon.start_server(port=options.monport,
                               secure=options.secure, cert_file=options.cert,
                               usethread=True,
                               authDict=monAuthDict)
                               #default_auth=None)
            server_started = True

            logger.info("Starting name service..")
            nssvc.ro_start(wait=True)

            # subscribe our monitor to the central monitor hub
            # TODO: how to specify authentication for monitor
            if options.monitor:
                # Ugh!  Find a more elegant way to deal with this:
                # Do not subscribe ourselves to ourself
                monhost = options.monitor.split(':')[0]
                monhost_s = monhost.split('.')[0]
                myhost_s  = myhost.split('.')[0]
                
                if monhost_s != myhost_s:
                    logger.info("Handling monitor subscriptions..")
                    myaddr = myhost + ':' + str(options.monport)
                    logger.info("My address is: %s" % myaddr)
                    try:
                        mymon.subscribe_remote(options.monitor, ['names'],
                                               {'pubauth': options.monauth,
                                                'pubsecure': options.secure,
                                                # TODO: bit of a hack here...can this be
                                                # improved?
                                                'name': myaddr,
                                                'auth': authstr})
                    except Exception, e:
                        logger.error("Error subscribing ourselves to monitor: %s" % (
                            str(e)))
                        # This is ok actually, remote monitor may not yet be up.
                        # Our monitor will try again every few seconds

                    # Subscribe main monitor to our feeds
                    monchannels = ['names']
                    mymon.publish_to(options.monitor, monchannels, {})

            # Register ourself
            logger.info("Registering self..")
            nsobj.register('names', myhost, options.port, options.secure)

        except Exception, e:
            logger.error(str(e))
            raise e
        
        logger.info("Entering main loop..")
        try:
            nsobj.purgeLoop(options.purge_interval)
            
        except KeyboardInterrupt:
            logger.error("Received keyboard interrupt!")

        except Exception, e:
            logger.error(str(e))

    finally:
        logger.info("Stopping remote objects name service...")
        if server_started:
            mymon.stop_server(wait=True)
        mymon.stop(wait=True)
    
    logger.info("Exiting remote objects name service...")
    #ev_quit.set()
    sys.exit(0)

    
if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--numthreads", dest="numthreads", type="int",
                      default=100,
                      help="Use NUM threads", metavar="NUM")
    optprs.add_option("--port", dest="port", type="int",
                      default=ro.nameServicePort,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--purge-interval", dest="purge_interval",
                      type="float", metavar="SECS",
                      default=60.0,
                      help="How often (SECS) to purge dead services")
    optprs.add_option("--purge-delta", dest="purge_delta",
                      type="float", metavar="SECS",
                      default=30.0,
                      help="Delta (SECS) to consider a service dead")
    ssdlog.addlogopts(optprs)
    ro.addlogopts(optprs)
    Monitor.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    if len(args) != 0:
        optprs.error("incorrect number of arguments")


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


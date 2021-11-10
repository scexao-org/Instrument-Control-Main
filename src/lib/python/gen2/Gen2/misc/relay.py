#! /usr/bin/env python
#
# relay.py -- program to relay status between summit and simulator
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Feb  8 15:47:25 HST 2012
#]
# remove once we're certified on python 2.6
from __future__ import with_statement


import sys, re
import time
import threading, Queue
import ssdlog

import SOSS.status.Convert as Convert
import remoteObjects as ro
import remoteObjects.Monitor as Monitor
import remoteObjects.xmlrpclib as xmlrpclib


def get_handle(ns, name):
    l = ns.getHosts(name)
    if len(l) > 0:
        tup = l.pop()
        (host, port) = tup
        return ro.remoteObjectClient(host, port, auth=(name, name))

    return None

class Make_cb(object):

    def __init__(self, **kwdargs):
        self.__dict__.update(kwdargs)
        self.lock = threading.RLock()

    # define callback functions for the monitor

    # this one is called if new data becomes available
    def anon_arr(self, payload, name, channels):
        recvtime = time.time()
            
        self.logger.debug("received values '%s'" % str(payload))

        try:
            bnch = Monitor.unpack_payload(payload)

            if self.monpath and (not bnch.path.startswith(self.monpath)):
                return

        except Monitor.MonitorError:
            return

        #print bnch

        with self.lock:
            if self.monpath:
                tree = bnch.value
                self.queue.put((self.monpath, tree, recvtime))
            else:
                tree = self.monitor.getTree(bnch.path)
                self.queue.put((bnch.path, tree, recvtime))

        
def main(options, args):

    logger = ssdlog.make_logger('relay', options)

    ro.init()

    myhost = ro.get_myhost(short=False)
    myport = options.port
    myself = "%s:%d" % (myhost, myport)
    
    ev_quit = threading.Event()
    queue = Queue.Queue()

    # make a name for our monitor
    myMonName = options.name

    # monitor channels we are interested in
    channels = options.channels.split(',')

    sum_ns = ro.remoteObjectClient(options.gen2host, 7075)
    sum_ns.ro_echo(99)
    
    loc_status = ro.remoteObjectProxy('status')

    # Get a status dict of all aliases
    statusInfo = Convert.statusInfo()
    aliases = statusInfo.getAliasNames()
    # remove troublesome aliases
    for alias in ('CXWS.TSCV.OBE_INR', 'STATL.OBJKIND', 'TSCV.OBJKIND',
                  'TSCV.ZERNIKE_RMS', 'TSCV.ZERNIKE_RMS_WOA20', ):
        aliases.remove(alias)
    sum_status = get_handle(sum_ns, 'status')

    statusDict = dict.fromkeys(aliases, None)
    fetchDict = sum_status.fetch(statusDict)
    #print fetchDict
    loc_status.store(fetchDict)
    
    # Create a local monitor
    mymon = Monitor.Monitor(myMonName, logger, numthreads=20)

    # Make our callback functions
    m = Make_cb(logger=logger, monitor=mymon, queue=queue,
                monpath='mon.status')
   
    # Subscribe our callback functions to the local monitor
    mymon.subscribe_cb(m.anon_arr, channels)

    server_started = False
    try:
        # Startup monitor threadpool
        mymon.start(wait=True)
        # start_server is necessary if we are subscribing, but not if only
        # publishing
        mymon.start_server(wait=True, port=options.port,
                           authDict={myMonName: myMonName})
        server_started = True

        # subscribe our monitor to the summit monitor hub
        
        summit = get_handle(sum_ns, 'monitor')

        summit.subscribe(myself, channels,
                         {'auth': "%s:%s" % (myMonName, myMonName)})
    
        while not ev_quit.isSet():
            try:
                (path, tree, time) = queue.get(block=True, timeout=1.0)

                #print tree
                try:
                    loc_status.store(tree)
                except Exception, e:
                    logger.error("Error relaying status: %s" % (str(e)))
                #printTree(path, tree, time)

            except Queue.Empty:
                continue
        
            except KeyboardInterrupt:
                logger.error("Received keyboard interrupt!")
                ev_quit.set()
            
    finally:
        if server_started:
            mymon.stop_server(wait=True)
        mymon.stop(wait=True)
    
if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options] command [args]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-c", "--channels", dest="channels", default='status',
                      metavar="LIST",
                      help="Subscribe to the comma-separated LIST of channels")
    optprs.add_option("-g", "--gen2host", dest="gen2host", default='g2ins1',
                      help="Summit Gen2 host")
    optprs.add_option("-m", "--monitor", dest="monitor", default='monitor',
                      metavar="NAME",
                      help="Subscribe to feeds from monitor service NAME")
    optprs.add_option("-n", "--name", dest="name", default='relay',
                      metavar="NAME",
                      help="Use NAME as our subscriber name")
    optprs.add_option("-p", "--path", dest="monpath", default=None,
                      metavar="PATH",
                      help="Show values for PATH in monitor")
    optprs.add_option("--port", dest="port", type="int", default=10919,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--sumport", dest="sumport", type="int")
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

#! /usr/bin/env python
#
# example of creating a local monitor and subscribing to info with
# callback functions
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Jul  8 11:14:39 HST 2010
#]
"""
example of creating a local monitor and subscribing to info with
callback functions

examples:
  ./monwatch.py -c statint

  (start 'statussim' service to get some packets flowing)

  ./monwatch.py -c g2task

  (run some command from TaskManager/IntegGUI)
"""
# remove once we're certified on python 2.6
from __future__ import with_statement


import sys, re
import time
import threading, Queue
import ssdlog
import pprint

import remoteObjects as ro
import remoteObjects.Monitor as Monitor

indentFactor = 2

# regex to remove unecessary tag info
regex_path = re.compile("^([\w\-]+)\-\d+\-\d+$")

# matches command execs
regex_exec = re.compile("^(mon\.tasks\.taskmgr\d+\.execTask-TaskManager-\d+-\d+)\..+$")

# Tags that should be converted from Unix time to HST time
times = set(['task_start', 'task_end', 'time_start', 'time_done',
             'cmd_time', 'ack_time', 'end_time', 'est_time'])

def convTime(val):
    ms = int((val - int(val)) * 1000.0)
    s = time.strftime("%H:%M:%S", time.localtime(val))
    return "%s.%03.3d" % (s, ms)
    
def printTree(path, tree, recvtime):

    def pp(tree, level):
        l = tree.items()
        leaves = []
        nodes  = []
        for key, val in l:
            if isinstance(val, dict):
                nodes.append(key)
            else:
                leaves.append(key)

        leaves.sort()
        nodes.sort()

        for key in leaves:
            val = tree[key]
            path = key.split('.')
            key = path[-1]
            match = regex_path.match(key)
            if match:
                key = match.group(1)
            if key in times:
                val = convTime(val)
            sys.stdout.write(' '*(level*indentFactor))
            print "%s: %s" % (key, str(val))

        for key in nodes:
            val = tree[key]
            path = key.split('.')
            key = path[-1]
            match = regex_path.match(key)
            if match:
                key = match.group(1)
            if key in times:
                val = convTime(val)
            sys.stdout.write(' '*(level*indentFactor))
            print "%s" % (key)
            pp(val, level+1)


    print "--- %s ---: %s" % (time.ctime(recvtime), path)
    try:
        pp(tree, 0)
    except:
        print "N/A"
    print
    print "--------------------------------"
    print
        

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
                if not self.history:
                    tree = bnch.value
                else:
                    tree = self.monitor.getTree(self.monpath)
                self.queue.put((self.monpath, tree, recvtime))
            elif self.watch_execs:
                match = regex_exec.match(bnch.path)
                #print match, bnch.path 
                if match:
                    path = match.group(1)
                    tree = self.monitor.getTree(path)
                    self.queue.put((path, tree, recvtime))
            else:
                if not self.history:
                    tree = bnch.value
                else:
                    tree = self.monitor.getTree(bnch.path)
                self.queue.put((bnch.path, tree, recvtime))

        
def main(options, args):

    logger = ssdlog.make_logger('test', options)

    ro.init()
    
    ev_quit = threading.Event()
    queue = Queue.Queue()

    # make a name for our monitor
    myMonName = options.name

    # monitor channels we are interested in
    channels = options.channels.split(',')

    # Create a local monitor
    mymon = Monitor.Monitor(myMonName, logger, numthreads=20)

    # Make our callback functions
    m = Make_cb(logger=logger, monitor=mymon, queue=queue,
                monpath=options.monpath, watch_execs=options.watch_execs,
                history=options.history)
   
    # Subscribe our callback functions to the local monitor
    mymon.subscribe_cb(m.anon_arr, channels)
    
    server_started = False
    try:
        # Startup monitor threadpool
        mymon.start(wait=True)
        # start_server is necessary if we are subscribing, but not if only
        # publishing
        mymon.start_server(wait=True, port=options.port)
        server_started = True

        # subscribe our monitor to the central monitor hub
        mymon.subscribe_remote(options.monitor, channels, ())
    
        while not ev_quit.isSet():
            try:
                (path, tree, time) = queue.get(block=True, timeout=1.0)

                printTree(path, tree, time)

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
    optprs.add_option("-c", "--channels", dest="channels", default='',
                      metavar="LIST",
                      help="Subscribe to the comma-separated LIST of channels")
    optprs.add_option("--history", dest="history", action="store_true",
                      default=False,
                      help="Fetch history on path instead of latest elements")
    optprs.add_option("-m", "--monitor", dest="monitor", default='monitor',
                      metavar="NAME",
                      help="Subscribe to feeds from monitor service NAME")
    optprs.add_option("-n", "--name", dest="name", default='monwatch',
                      metavar="NAME",
                      help="Use NAME as our subscriber name")
    optprs.add_option("-p", "--path", dest="monpath", default=None,
                      metavar="PATH",
                      help="Show values for PATH in monitor")
    optprs.add_option("--port", dest="port", type="int", default=10013,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--we", dest="watch_execs", default=False,
                      action="store_true",
                      help="Watch EXEC events")
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

#! /usr/bin/env python
#
# monlog.py -- syslog-like service to write multiple log files
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Sat Oct 23 12:23:35 HST 2010
#]
# remove once we're certified on python 2.6
from __future__ import with_statement


import sys, re
import os, time
import threading, Queue
import ssdlog

import remoteObjects as ro
import remoteObjects.PubSub as PubSub
import remoteObjects.Monitor as Monitor
import Task

# import some configuration variables
import cfg.monlog as config

# Regex used to discover/parse log info
regex_log = re.compile(r'^mon\.log\.(\w+)$')


class LogWriter(Task.Task):

    def __init__(self, logname, logpath, logger, ev_quit,
                 maxBytes=0, backupCount=0, backupFolder='',
                 timespecs=None, dosync=False,
                 wait_interval=0.1):
        super(LogWriter, self).__init__()

        self.logger = logger
        self.ev_quit = ev_quit
        self.logname = logname
        self.logpath = logpath

        self.wait_interval = wait_interval
        self.backupCount = backupCount
        self.maxBytes = maxBytes

        self.suffix = "%Y-%m-%d_%H-%M-%S"
        self.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$")
        self.backupFolder = backupFolder

        # Set time-based rotation options
        self.timespecs = timespecs
        self.rolloverAt = None
        # value of 60 sec yields a reasonable efficient algorithm
        # for calculating rollover time (see ssdlog.py)
        self.time_inc = 60
        self.time_inc = 5
        if self.timespecs:
            # Calculate earliest rollover time
            times = ssdlog.computeRolloverList(time.time(), self.time_inc,
                                               self.timespecs)
            self.rolloverAt = times[0]

        # queue where buffers are dropped by monitor and read by us
        self.queue = Queue.Queue()
        # the log file stream descriptor
        self.stream = None
        # if dosync==True then flush after every write
        self.dosync = dosync

    def put(self, msgstr):
        self.queue.put(msgstr)

    def shouldRolloverTime(self):
        # Check for time-based rollover
        t = int(time.time())
        if (self.rolloverAt != None) and (t >= self.rolloverAt):
            return True
        return False

    def shouldRolloverSize(self, buffer):
        # check for size-based rollover
        if self.maxBytes > 0:                   # are we rolling over?
            self.stream.seek(0, 2)  #due to non-posix-compliant Windows feature
            if self.stream.tell() + len(buffer) >= self.maxBytes:
                return True
        return False

    def getFilesToDelete(self, dirName, baseName):
        """
        Determine the files to delete when rolling over.

        More specific than the earlier method, which just used glob.glob().
        """
        fileNames = os.listdir(dirName)
        result = []
        prefix = baseName + "."
        plen = len(prefix)
        for fileName in fileNames:
            if fileName[:plen] == prefix:
                suffix = fileName[plen:]
                if self.extMatch.match(suffix):
                    result.append(os.path.join(dirName, fileName))
        result.sort()
        if len(result) < self.backupCount:
            result = []
        else:
            result = result[:len(result) - self.backupCount]
        return result

    def doRollover(self):
        """
        do a rollover; in this case, a date/time stamp is appended to the
        filename when the rollover happens.  If there is a backup count,
        then we have to get a list of matching filenames, sort them and remove
        the one with the oldest suffix.
        """
        self.logger.info("Rolling over log file %s" % self.logpath)
        if self.stream:
            self.stream.close()

        timeTuple = time.localtime(time.time())
        logdir, logfile = os.path.split(self.logpath)

        backupdir = os.path.join(logdir, self.backupFolder)
        rollpath = os.path.join(backupdir,
                                logfile + "." +
                                time.strftime(self.suffix, timeTuple))
        os.rename(self.logpath, rollpath)
        self.logger.debug("Rolled over to %s" % rollpath)

        # Delete some old log files if necessary
        if self.backupCount > 0:
            # find the oldest log file and delete it
            for oldlog in self.getFilesToDelete(backupdir, logfile):
                self.logger.info("Deleting old log file %s" % oldlog)
                try:
                    os.remove(oldlog)
                except OSError, e:
                    self.logger.error("Failed to remove old log file '%s': %s" % (
                        oldlog, str(e)))

        # Open up the log file again
        try:
            self.stream = open(self.logpath, 'w')

        except IOError, e:
            self.logger.error("Failed to open log file '%s': %s" % (
                self.logpath, str(e)))
            self.stream = None

        # Calculate new rollover time
        if self.rolloverAt:
            t = time.time()
            # Calculate earliest rollover time
            times = ssdlog.computeRolloverList(t, self.time_inc,
                                               self.timespecs)
            self.rolloverAt = times[0]
            new_time = time.strftime('%Y-%m-%d %H:%M:%S',
                                     time.localtime(self.rolloverAt))
            self.logger.info("new rollover time (%s) calculated in %.4f secs" % (
                new_time, time.time() - t))
    
    def execute(self):
        # open log
        try:
            self.stream = open(self.logpath, 'a')

        except IOError, e:
            self.logger.error("Failed to open log file '%s': %s" % (
                self.logpath, str(e)))
            return

        # Main loop.
        # Read buffers from queue and write them to the log file.
        while not self.ev_quit.isSet():
            try:
                buffer = self.queue.get(block=True, timeout=self.wait_interval)
                try:
                    # Check for size-based rollover
                    if self.shouldRolloverSize(buffer):
                        self.doRollover()
                        
                    if self.stream:
                        self.stream.write(buffer)
                        # For better performance, do not flush buffer on each
                        # write.  If you need to tail the log, use "monwatch"
                        if self.dosync:
                            self.stream.flush()

                except IOError, e:
                    self.logger.error("Error writing log message: %s" % (
                        str(e)))

            except Queue.Empty:
                pass

            # Check for time-based rollover
            if self.shouldRolloverTime():
                self.doRollover()

        # close log
        try:
            self.stream.close()

        except IOError, e:
            self.logger.error("Failed to close log file '%s': %s" % (
                self.logpath, str(e)))
        
class MsgReceiver(object):

    def __init__(self, threadPool, logger, ev_quit):

        self.logger = logger
        self.ev_quit = ev_quit

        # For task inheritance:
        self.threadPool = threadPool
        self.tag = 'monlog'
        self.shares = ['threadPool']

        self.writerDict = {}
        self.lock = threading.RLock()


    def add_writer(self, logname, logpath, backupCount=4,
                   backupFolder='', timespecs=None, dosync=False):
        writer = LogWriter(logname, logpath, self.logger, self.ev_quit,
                           backupCount=backupCount,
                           backupFolder=backupFolder,
                           timespecs=timespecs, dosync=dosync)
        with self.lock:
            writer.init_and_start(self)

            self.writerDict[logname] = writer
            
    # this one is called if new data becomes available
    def data_arr(self, payload, name, channels):
        try:
            self.logger.debug("received values '%s'" % str(payload))
            bnch = Monitor.unpack_payload(payload)

        except Monitor.MonitorError, e:
            self.logger.error("data receive error: %s" % str(e))
            return

        match = regex_log.match(bnch.path)
        if not match:
            return
        
        logname = match.group(1)
        with self.lock:
            try:
                writer = self.writerDict[logname]

            except KeyError:
                # We're not writing a log for this guy
                pass

        # Drop the packet in this guy's queue
        msgstr = bnch.value['msgstr']
        writer.put(msgstr)

        
def main(options, args):

    logger = ssdlog.make_logger('monlog', options)

    ev_quit = threading.Event()

    # monitor channels we are interested in
    channels = options.channels.split(',')

    # Initialize remote objects subsystem.
    try:
        ro.init()

    except ro.remoteObjectError, e:
        logger.error("Error initializing remote objects subsystem: %s" % str(e))
        sys.exit(1)

    ev_quit = threading.Event()
    usethread = False

    # where to store the logs
    if not options.logdir:
        logdir = config.logdir
    else:
        logdir = options.logdir

    # Create our pubsub
    pubsub = PubSub.PubSub(options.svcname, logger,
                           numthreads=options.numthreads)

    logger.info("Starting monlog...")
    pubsub.start()

    threadPool = pubsub.get_threadPool()

    # Create dictionary of log writers 
    msgReceiver = MsgReceiver(threadPool, logger, ev_quit)

    # Subscribe our local callback functions
    pubsub.subscribe_cb(msgReceiver.data_arr, channels)

    if options.lognames:
        lognames = options.lognames.split(',')
    else:
        lognames = config.logs
        
    # Create and start writers
    for logname in lognames:
        logpath = os.path.join(logdir, logname + '.log')
        msgReceiver.add_writer(logname, logpath,
                               backupFolder=config.backupFolder,
                               backupCount=config.backupCount,
                               timespecs=config.timespecs,
                               dosync=config.syncwrites)
        
    try:
        try:
            pubsub.start_server(port=options.port, wait=True, 
                                 usethread=usethread)
        
        except KeyboardInterrupt:
            logger.error("Caught keyboard interrupt!")

    finally:
        logger.info("Stopping monlog...")
        ev_quit.set()
        if usethread:
            pubsub.stop_server(wait=True)
        pubsub.stop()

    
if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options] command [args]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-c", "--channels", dest="channels", default='logs',
                      metavar="LIST",
                      help="Subscribe to the comma-separated LIST of channels")
    optprs.add_option("--lognames", dest="lognames",
                      metavar="LIST",
                      help="LIST of logs to write")
    optprs.add_option("--numthreads", dest="numthreads", type="int",
                      default=60,
                      help="Use NUM threads", metavar="NUM")
    optprs.add_option("--port", dest="port", type="int", default=7082,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--svcname", dest="svcname", default='monlog',
                      metavar="NAME",
                      help="Use NAME as our service name")
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

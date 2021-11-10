#
# Simple common log format for Python logging module
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Oct 11 23:27:51 HST 2010
#]
#
import sys, os
import re, string
import time
import logging, logging.handlers
import socket
import threading, Queue

if sys.hexversion < 0x02050000:
    STD_FORMAT = '%(asctime)s | %(levelname)1.1s | %(filename)s:%(lineno)d | %(message)s'
else:
    STD_FORMAT = '%(asctime)s | %(levelname)1.1s | %(filename)s:%(lineno)d (%(funcName)s) | %(message)s'

# Can't do this because behind the scenes somewhere it sets some
# characteristics for logging to the terminal--and that causes problems
# for things that are trying to run as daemons
#
#logging.basicConfig(level=logging.DEBUG,
#                    format=STD_FORMAT)

# Max logsize is 200 MB
max_logsize = 200 * 1024 * 1024

# Maximum number of backups
max_backups = 4


# For errors thrown here
class LoggingError(Exception):
    pass

# Special Handlers

class QueueHandler(logging.Handler):
    """Logs to a Queue.Queue object."""

    def __init__(self, queue, level=logging.NOTSET):
        self.queue = queue
        #super(QueueHandler, self).__init__(level=level)
        logging.Handler.__init__(self, level=level)
        
    def emit(self, record):
        self.queue.put(self.format(record))

        
class QueueHandler2(logging.Handler):
    """Logs to a Queue.Queue object."""

    def __init__(self, queue, level=logging.NOTSET):
        self.queue = queue
        #super(QueueHandler, self).__init__(level=level)
        logging.Handler.__init__(self, level=level)
        
    def emit(self, record):
        self.queue.put(record)

    def get(self, block=True, timeout=None):
        record = self.queue.get(block=block, timeout=timeout)
        return self.format(record)

    def process_queue(self, logger, ev_quit, timeout=0.1):
        # Takes another logger and a quit event.  Invokes the logger
        # on records coming through the 
        while not ev_quit.isSet():
            try:
                record = self.queue.get(block=False, timeout=timeout)
                logger.handle(record)
                
            except Queue.Empty:
                pass
    
        
class BroadcastHandler(logging.Handler):
    """Logs to a broadcast or host IP datagram."""

    def __init__(self, addr, port, level=logging.NOTSET,
                 queue=None, buflimit=50000, interval=0.1):
        self.addr = addr
        self.port = port
        # Create socket used for dgram broadcast
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # size of the current buffer
        self.bufsize = 0
        # size limit beyond which buffer is sent out as a datagram
        self.buflimit = buflimit
        # the buffer
        self.buffer = []
        
        # time of the last transmission
        self.lastsend = time.time()
        # time delta (sec) beyond which the buffer is sent regardless
        # of size
        self.interval = interval

        # queue used to double buffer logging requests
        if queue == None:
            queue = Queue.Queue()
        self.queue = queue
        
        # Used to strip out bogus characters from log buffers
        self.deletechars = ''.join(set(string.maketrans('', '')) -
                                   set(string.printable))

        #super(BroadcastHandler, self).__init__(level=level)
        logging.Handler.__init__(self, level=level)

    def emit(self, record):
        msg = self.format(record)
        self.queue.put(msg)

    def _sendbuf(self):
        # Concatenate buffer and send it out over the socket
        buf = '\n'.join(self.buffer)
        self.buffer = []
        self.bufsize = 0
        self.lastsend = time.time()
        self.sock.sendto(buf, (self.addr, self.port))
        
    def start_queue(self, ev_quit=None):
        if not ev_quit:
            ev_quit = threading.Event()
        self.ev_quit = ev_quit
        t = threading.Thread(target=self.process_queue,
                             args=[self.ev_quit])
        t.start()
        return t

    def stop_queue(self):
        self.ev_quit.set()
        
    def process_queue(self, ev_quit):
        """Processes the logs messages that are deposited in the queue by
        the logger.  (ev_quit) is a threading.Event that controls when to
        exit the processing loop.
        """
        while not ev_quit.isSet():
            try:
                msg = self.queue.get(block=False, timeout=self.interval)
                # Strip out bogus characters
                msg = msg.translate(None, self.deletechars)
                msglen = len(msg)

                # Would message size exceed buffer limit?
                if self.bufsize + msglen > self.buflimit:
                    # Yes, send current buffer
                    self._sendbuf()

                self.buffer.append(msg)
                self.bufsize += msglen

            except Queue.Empty:
                pass

            # if there is anything in the buffer, and it has reached
            # the minimum time interval since we last sent a packet, then
            # send the buffer
            if (self.bufsize > 0) and (time.time() - self.lastsend > self.interval):
                self._sendbuf()
            
            
        
class NullHandler(logging.Handler):
    """Logs to a black hole."""

    def emit(self, record):
        pass


class FixedTimeRotatingFileHandler(logging.handlers.BaseRotatingHandler):
    """
    Handler for logging to a file, rotating the log file at certain fixed
    times OR when the size exceeds a certain limit.

    If backupCount is > 0, when rollover is done, no more than backupCount
    files are kept - the oldest ones are deleted.
    """
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0,
                 encoding=None, delay=0, rotateOpts=None, utc=0,
                 time_inc=60):

        if maxBytes > 0:
            mode = 'a' # doesn't make sense otherwise!

        if sys.hexversion <= 0x02060000:
            logging.handlers.BaseRotatingHandler.__init__(self, filename,
                                                          mode, encoding)
        else:
            logging.handlers.BaseRotatingHandler.__init__(self, filename,
                                                          mode, encoding, delay)

        self.maxBytes = maxBytes
        self.backupCount = backupCount
        # TODO: currently this is broken for utc=1
        self.utc = utc
        # value of 60 yields a reasonable efficient algorithm
        self.time_inc = time_inc

        self.suffix = "%Y-%m-%d_%H-%M-%S"
        self.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$")
        #raise ValueError("Invalid rollover interval specified: %s" % self.when)

        # Set time-based rotation options
        self.options = {}
        self.rolloverAt = None
        if rotateOpts:
            self.options.update(rotateOpts)
        
            self.rolloverAt = computeRollover(time.time(), self.time_inc,
                                              **self.options)
        #print "Will rollover at %d, %d seconds from now" % (self.rolloverAt, self.rolloverAt - time.time())

    def shouldRollover(self, record):
        """
        Determine if rollover should occur.

        record is not used, as we are just comparing times, but it is needed so
        the method signatures are the same
        """
        # Check for time-based rollover
        t = int(time.time())
        if (self.rolloverAt != None) and (t >= self.rolloverAt):
            return 1

        # check for size-based rollover
        if self.stream is None:                 # delay was set...
            self.stream = self._open()
        if self.maxBytes > 0:                   # are we rolling over?
            msg = "%s\n" % self.format(record)
            self.stream.seek(0, 2)  #due to non-posix-compliant Windows feature
            if self.stream.tell() + len(msg) >= self.maxBytes:
                return 1
        return 0

    def getFilesToDelete(self):
        """
        Determine the files to delete when rolling over.

        More specific than the earlier method, which just used glob.glob().
        """
        dirName, baseName = os.path.split(self.baseFilename)
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
        if self.stream:
            self.stream.close()
        # get the time that this sequence started at and make it a TimeTuple
        #t = self.rolloverAt
        t = time.time()
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
        dfn = self.baseFilename + "." + time.strftime(self.suffix, timeTuple)
        if os.path.exists(dfn):
            os.remove(dfn)
        os.rename(self.baseFilename, dfn)
        if self.backupCount > 0:
            # find the oldest log file and delete it
            for s in self.getFilesToDelete():
                os.remove(s)
        #print "%s -> %s" % (self.baseFilename, dfn)
        self.mode = 'w'
        self.stream = self._open()

        # Calculate new rollover time
        if self.rolloverAt:
            self.rolloverAt = int(computeRollover(time.time(), self.time_inc,
                                                  **self.options))


# Convenience class for a NullLogger

class NullLogger(logging.Logger):
    """Logs to a black hole."""

    def __init__(self, *args, **kwdargs):
        logging.Logger.__init__(self, *args, **kwdargs)

        self.addHandler(NullHandler())


def get_level(level):
    """Translates a logging level specified as an int or as a string
    into an int.
    """

    if isinstance(level, int):
        return level

    elif isinstance(level, str):
        levels = ['all', 'debug', 'info', 'warn', 'error', 'critical']
        try:
            return levels.index(level.lower()) * 10
        except ValueError:
            try:
                return int(level)
            except ValueError:
                pass

    raise LoggingError("Level must be an int or %s: %s" % (
                str(levels), str(level)))


def get_formatter():
    return logging.Formatter(STD_FORMAT)


def calc_future(time_future, kwdargs):
    """
    Work out the rollover time based on the specified time.
    """
    # Get future time
    (yr, mo, day, hr, min, sec, wday, yday, isdst) = time.localtime(
        time_future)

    # override select values
    d = { 'yr': yr, 'mo': mo, 'day': day, 'hr': hr, 'min': min,
          'sec': sec, 'wday': wday, 'yday': yday, 'isdst': isdst }
    d.update(kwdargs)

    # return future time to run job
    return time.mktime((d['yr'], d['mo'], d['day'], d['hr'], d['min'],
                        d['sec'], -1, -1, -1))


def computeRollover(time_now, time_inc, **kwdargs):
    # Calculate new rollover time
    time_delta = 0
    newRolloverAt = 0
    # TODO: this iteration method seems hideously inefficient
    # What we need is an efficient algorithm that will tell us the least
    # distant time in the future when the kwdargs options are satisfied
    while newRolloverAt < time_now:
        time_delta += time_inc
        newRolloverAt = calc_future(time_now + time_delta, kwdargs)
    return newRolloverAt


def computeRolloverList(time_now, time_inc, rolloverSpecs):
    res = [ computeRollover(time_now, time_inc, **spec) for spec in \
            rolloverSpecs ]
    res.sort()
    return res


def parse_logspec(spec, options):
    if ':' in spec:
        name, level = spec.split(':')
        level = get_level(level)
            
    else:
        name = spec
        level = get_level(options.loglevel)

    if options.logdir:
        if options.logbyhostname:
            myhost = socket.getfqdn().split('.')[0]
            name = os.path.join(options.logdir, myhost, name)
        else:
            name = os.path.join(options.logdir, name)

    rotopts = {}
    if options.logtime:
        opts = options.logtime.split(';')
        for opt in opts:
            try:
                unit, val = opt.split('=')
                unit = unit.lower()
                val = int(val)
                rotopts[unit] = val
            except IndexError, ValueError:
                raise LoggingError("Bad time rotation spec: '%s'" % (options.logtime))
            
    return (name, level, options.logsize, options.logbackups, rotopts)


def make_logger(logname, options, format=STD_FORMAT):

    # Create top level logger.
    logger = logging.Logger(logname)
    #logger = logging.getLogger(logname)
    #logger.setLevel(options.loglevel)
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(format)

    if options.logfile:
        (filename, level, size, backups, rotopts) = parse_logspec(options.logfile, options)
        fileHdlr  = logging.handlers.RotatingFileHandler(filename, maxBytes=size,
                                                         backupCount=backups)
        fileHdlr.setFormatter(fmt)
        fileHdlr.setLevel(level)
        logger.addHandler(fileHdlr)

    #islogging = options.logfile or options.logport or 
    # Add output to stderr, if requested
    if options.logstderr:
        level = get_level(options.loglevel)
        stderrHdlr = logging.StreamHandler()
        stderrHdlr.setLevel(level)
        stderrHdlr.setFormatter(fmt)
        logger.addHandler(stderrHdlr)

    # # TODO: deprecate?
    # if options.logbyqueue:
    #     # In queue-based logging, the real logger is hidden behind a queue
    #     hidden = logger
    #     logger = logging.Logger('queue')
    #     queueHdlr = QueueHandler2(Queue.Queue())
    #     queueHdlr.setLevel(level)
    #     logger.addHandler(queueHdlr)

    if options.logmon:
        from remoteObjects.Monitor import MonitorHandler
        # logging via publish/subscribe.  Application must later call set_monitor()
        monHdlr = MonitorHandler(None,
                                 'mon.log.%s' % logname,
                                 level=get_level(options.loglevel))
        monHdlr.setFormatter(fmt)
        logger.addHandler(monHdlr)

    # if options.logport:
    #     #addr = '255.255.255.255'
    #     sockHdlr = BroadcastHandler(addr, options.logport,
    #                                 level=get_level(options.loglevel))
    #     sockHdlr.setFormatter(fmt)
    #     logger.addHandler(sockHdlr)

    return logger
        

def simple_logger(logname, level=logging.ERROR, format=STD_FORMAT):

    # Create top level logger.
    logger = logging.getLogger(logname)
    logger.setLevel(level)

    fmt = logging.Formatter(format)

    # Add output to stderr
    stderrHdlr = logging.StreamHandler()
    stderrHdlr.setFormatter(fmt)
    logger.addHandler(stderrHdlr)

    return logger
        

def get_handler(logger, klass):

    for hndlr in logger.handlers:
        if isinstance(hndlr, klass):
            return hndlr

    return None
        

def get_handler_formatter(handler):
    return handler.formatter
        
def get_handler_level(handler):
    return handler.level
        

def mklog(logname, queue, level, format=STD_FORMAT):
    logger = logging.getLogger(logname)
    logger.setLevel(level)
    fmt = logging.Formatter(format)
    qHdlr  = QueueHandler(queue, level=level)
    qHdlr.setFormatter(fmt)
    logger.addHandler(qHdlr)
    return logger


def addlogopts(optprs):
    optprs.add_option("--log", dest="logfile", metavar="FILE",
                      help="Write logging output to FILE")
    optprs.add_option("--logport", dest="logport", metavar="PORT",
                      type='int',
                      help="Broadcast logging messages to PORT")
    optprs.add_option("--logdir", dest="logdir", metavar="DIR",
                      help="Write logging output to DIR")
    optprs.add_option("--logbyhostname", dest="logbyhostname", default=False,
                      action="store_true",
                      help="Create log files under host name")
    optprs.add_option("--logbyqueue", dest="logbyqueue", default=False,
                      action="store_true",
                      help="Use a queue to speed logging")
    optprs.add_option("--loglevel", dest="loglevel", metavar="LEVEL",
                      default='info',
                      help="Set logging level to LEVEL")
    optprs.add_option("--logsize", dest="logsize", metavar="NUMBYTES",
                      type="int", default=max_logsize,
                      help="Set maximum logging level to NUMBYTES")
    optprs.add_option("--logbackups", dest="logbackups", metavar="NUM",
                      type="int", default=max_backups,
                      help="Set maximum number of backups to NUM")
    optprs.add_option("--logtime", dest="logtime", metavar="OPTIONS",
                      help="Set log file time-based rotation options")
    optprs.add_option("--stderr", dest="logstderr", default=False,
                      action="store_true",
                      help="Copy logging also to stderr")
    optprs.add_option("--logmon", dest="logmon", metavar="NAME",
                      help="Logging via publish/subscribe using monitor NAME")

# END

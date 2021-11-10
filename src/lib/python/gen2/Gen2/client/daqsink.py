#!/usr/bin/env python
#
# daqsink.py -- transfer Gen2 frames to DAQ.
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Sun Dec 27 23:05:23 HST 2009
#]
#
"""
A program to save FITS frames to DAQ using DAQ fifo control messages.

Usage:
  (To run a server to archive files (run as daqusr@obc1))
  
  ./daqsink.py --daqdir=/mdata/fits -f <keyfile> -p <passfile>

"""

import sys, os, re, time
import logging, socket, signal
import threading, Queue
import hashlib, hmac

import myproc
import Gen2.client.datasink as ds
from SOSS.SOSSfifo import DAQfifoMsg
from cfg.INS import INSdata as INSconfig

version = "20090312.0"

# Chose type of authorization encryption 
digest_algorithm = hashlib.sha1


def getFrameInfoFromPath(fitspath):
    # Extract frame id from file path
    (fitsdir, fitsname) = os.path.split(fitspath)
    (frameid, ext) = os.path.splitext(fitsname)
    
    match = re.match('^(\w{3})([AQ])(\d{8})$', frameid)
    if match:
        (inscode, frametype, frame_no) = match.groups()
        frame_no = int(frame_no)
        
        return (frameid, fitsname, fitsdir, inscode,
                frametype, frame_no)

    return None


class DAQError(Exception):
    pass

class DAQSink(ds.DataSink):

    def __init__(self, logger, fitsdir, daqdir,
                 ev_quit=threading.Event(), timeout=0.1, interval=1.0,
                 fifopath='/app/OBC/dat_local/flowctrl.fifo'):


        self.fitsdir = fitsdir

        super(DAQSink, self).__init__(logger, self.fitsdir,
                                      notify_fn=self.archive_notify,
                                      notify_thread=True)
        
        self.fifopath = fifopath
        self.daqdir = daqdir
        self.timeout = timeout
        # Interval to wait between DAQ submissions
        self.interval = interval
        self.ev_quit = ev_quit

        self.queue = Queue.Queue()

        # Get an instrument configuration object
        self.insconfig = INSconfig()

        # Check FIFO access
        try:
            self.daqfifo_f = open(self.fifopath, 'w')
            #pass
            
        except IOError, e:
            raise DAQError("Can't open '%s' for writing" % self.fifopath)


    def _dropfifo(self, fitspath, kind):

        self.logger.info("Processing %-8.8s: %s" % (kind, fitspath))

        # Convert to absolute file path
        abspath = os.path.abspath(fitspath)
        if not os.path.exists(abspath):
            raise DAQError("Nonexistant FITS file: '%s'" % abspath)

        self.logger.debug("Processing 2")
        # Get frame info from fits path on disk
        info = getFrameInfoFromPath(abspath)
        if not info:
            raise DAQError("Malformed FITS file path: '%s'" % abspath)

        (frameid, fitsname, fitsdir, inscode,
         frametype, frame_no) = info

        self.logger.debug("Processing 3, info=%s" % str(info))
        # Double check instrument is valid
        try:
            insno = self.insconfig.getNumberByCode(inscode)

        except KeyError:
            raise DAQError("Frameid '%s' doesn't match a valid Subaru instrument." % \
                           (frameid))

        self.logger.debug("Processing 4")
        # Sanity check DAQ control word
        kind = kind.upper().strip()
        if not kind in ('FLOWCTRL', 'FLOWSND', 'FLOWSAVE'):
            raise DAQError("DAQ fifo message '%s' doesn't match valid types." % \
                           (kind))

        # Pad field
        kind = ('%-8.8s' % kind)
        
        self.logger.debug("Processing 5")
        # Create appropriate DAQ FIFO message
        msg = DAQfifoMsg()

        # TODO: abstract and enforce checks
        msg.set(kind=kind, frame=frameid, host=insno, manual='  ')
        self.logger.debug(str(msg))

        # Torpedo away!
        self.logger.info("Torpedo away! %-8.8s: %s" % (kind, fitspath))
        self.daqfifo_f.write(str(msg))
        self.daqfifo_f.flush()


    def service_loop(self):

        while not self.ev_quit.isSet():
            try:
                # wait for request from queue, at most self.timeout secs
                (fitspath, kind) = self.queue.get(block=True,
                                                  timeout=self.timeout)
            except Queue.Empty:
                # no request within timeout period, iterate
                continue

            try:
                # have request. calculate time for interval
                endtime = time.time() + self.interval

                # process request
                self._dropfifo(fitspath, kind)

                # if there is any time left to wait in interval, wait
                rest_time = endtime - time.time()
                if rest_time > 0:
                    self.ev_quit.wait(rest_time)

            except Exception, e:
                # Error handling request.  Log it and continue
                self.logger.error("Error with request '%s' for %s: %s" % (
                    kind, fitspath, str(e)))


    def flowctrl(self, fitspath):
        self.logger.debug("Dropping fifo FLOWCTRL message for %s" % fitspath)
        self.queue.put((fitspath, 'FLOWCTRL'))
        return 0

    
    def flowsave(self, fitspath):
        self.logger.debug("Dropping fifo FLOWSAVE message for %s" % fitspath)
        self.queue.put((fitspath, 'FLOWSAVE'))
        return 0

    
    def flowsend(self, fitspath):
        self.logger.debug("Dropping fifo FLOWSEND message for %s" % fitspath)
        self.queue.put((fitspath, 'FLOWSND'))
        return 0


    def store_data(self, filename, filetype, data):

        self.logger.debug("store data: filename=%s filetype=%s" % (
                filename, filetype))

        if filetype == 'fits':
            info = getFrameInfoFromPath(filename)
            if not info:
                raise DAQError("Malformed FITS filename: '%s'" % filename)

        else:
            raise DAQError("Non-FITS file: '%s'" % filename)

        (frameid, fitsname, fitsdir, inscode,
         frametype, frame_no) = info

        insno = self.insconfig.getNumberByCode(inscode)

        # Figure out path to where data files are stored
        if insno != 33:
            daqpath = ('%s/obcp%02d/%s.fits' % (self.daqdir, insno, frameid))
        else:
            # Special case for VGW
            daqpath = ('%s/vgw/%s.fits' % (self.daqdir, frameid))

        self.logger.debug("Storing data into %s" % daqpath)

        if os.path.exists(daqpath):
            raise DAQError("File already exists: %s" % daqpath)

        try:
            out_f = open(daqpath, 'w')

            out_f.write(data)
            out_f.close()

        except IOError, e:
            raise SinkError("Error saving file '%s': %s" % (
                daqpath, str(e)))

        try:
            # DAQ expects files to be stored as -r--r-----
            os.chmod(daqpath, 0440)

        except OSError, e:
            raise DAQError("Error changing permissions on '%s': %s" % (
                daqpath, str(e)))

        return daqpath


    def archive_notify(self, filepath, filetype):
        """This is called when the file is already present from being sent
        by the Gen2 archive service.
        """

        # Finally, drop in fifo
        self.flowctrl(filepath)

        
def server(logger, options, args):

    if options.keyfile:
        keyname, ext = os.path.splitext(options.keyfile)
        try:
            in_f = open(options.keyfile, 'r')
            key = in_f.read().strip()
            in_f.close()

        except IOError, e:
            logger.error("Cannot open key file '%s': %s" % (
                options.keyfile, str(e)))
            sys.exit(1)

    elif options.key:
        key = options.key
        keyname = key.split('-')[0]

    else:
        logger.error("Please specify --keyfile or --key")
        sys.exit(1)

    if options.passfile:
        try:
            in_f = open(options.passfile, 'r')
            passphrase = in_f.read().strip()
            in_f.close()

        except IOError, e:
            logger.error("Cannot open passphrase file '%s': %s" % (
                options.passfile, str(e)))
            sys.exit(1)

    elif options.passphrase != None:
        passphrase = options.passphrase
        
    else:
        logger.error("Please specify --passfile or --pass")
        sys.exit(1)

    # Compute hmac
    hmac_digest = hmac.new(key, passphrase, digest_algorithm).hexdigest()
    
    ev_quit = threading.Event()
    
    sink = DAQSink(logger, options.tmpdir, options.daqdir,
                   interval=options.dropinterval, fifopath=options.fifopath,
                   ev_quit=ev_quit)

    # Start queue processing
    svcloop_t = threading.Thread(target=sink.service_loop, args=[])
    svcloop_t.start()
    
    ds.datasink(options, logger, keyname, hmac_digest, sink)
    ev_quit.set()
    
    logger.info("Exiting program.")
    sys.exit(0)
    

def main(options, args):

    # Create top level logger.
    logger = logging.getLogger('daqsink')
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(ds.LOG_FORMAT)

    if options.logfile:
        fileHdlr  = logging.FileHandler(options.logfile)
        fileHdlr.setFormatter(fmt)
        fileHdlr.setLevel(options.loglevel)
        logger.addHandler(fileHdlr)
    # Add output to stderr, if requested
    if options.logstderr or (not options.logfile):
        stderrHdlr = logging.StreamHandler()
        stderrHdlr.setFormatter(fmt)
        stderrHdlr.setLevel(options.loglevel)
        logger.addHandler(stderrHdlr)

    server(logger, options, args)
    
    logger.info("Exiting program.")
    sys.exit(0)


if __name__ == '__main__':

    # Parse command line options
    from optparse import OptionParser
    
    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%prog'))
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-d", "--tmpdir", dest="tmpdir",
                      metavar="DIR", default='/tmp',
                      help="Specify temporary DIR to receive FITS files")
    optprs.add_option("--daqdir", dest="daqdir",
                      metavar="DIR", default=None,
                      help="Specify DIR to store FITS files for DAQ")
    optprs.add_option("--detach", dest="detach", default=False,
                      action="store_true",
                      help="Detach from terminal and run as a daemon")
    optprs.add_option("-f", "--keyfile", dest="keyfile", metavar="NAME",
                      help="Specify authorization key file NAME")
    optprs.add_option("--fifo", dest="fifopath", metavar="PATH",
                      default='/app/OBC/dat_local/flowctrl.fifo',
                      help="Specify PATH for DAQ fifo")
    optprs.add_option("--host", dest="host", metavar="NAME",
                      default='g2stat.sum.subaru.nao.ac.jp',
                      help="Specify NAME for a Gen2 host")
    optprs.add_option("-i", "--dropinterval", dest="dropinterval", type="float",
                      default=1.0, metavar="SEC",
                      help="Don't prompt, but wait SEC seconds between saves")
    optprs.add_option("--interval", dest="interval", type="int",
                      default=60, metavar="SEC",
                      help="Registration interval in SEC")
    optprs.add_option("-k", "--key", dest="key", metavar="KEY",
                      help="Specify authorization KEY")
    optprs.add_option("--log", dest="logfile", metavar="FILE",
                      help="Write logging output to FILE")
    optprs.add_option("--loglevel", dest="loglevel", metavar="LEVEL",
                      type="int", default=logging.INFO,
                      help="Set logging level to LEVEL")
    optprs.add_option("--pass", dest="passphrase", 
                      help="Specify authorization pass phrase")
    optprs.add_option('-p', "--passfile", dest="passfile", 
                      help="Specify authorization pass phrase file")
    optprs.add_option("--pidfile", dest="pidfile", metavar="FILE",
                      default='/app/OBC/dat/daqsink.pid',
                      help="Write process pid to FILE")
    optprs.add_option("--port", dest="port", type="int", default=15009,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--stderr", dest="logstderr", default=False,
                      action="store_true",
                      help="Copy logging also to stderr")

    (options, args) = optprs.parse_args(sys.argv[1:])

    if not options.daqdir:
        optprs.error("Please specify a --daqdir!")
     
    if options.detach:
        print "Detaching from this process..."
        sys.stdout.flush()
        try:
            child = myproc.myproc(main, args=[options, args],
                                  pidfile=options.pidfile, detach=True)
            child.wait()

            # TODO: check status of process and report error if necessary
        finally:
            sys.exit(0)

    # Are we debugging this?
    elif options.debug:
        import pdb

        pdb.run('main(options, args)')

    # Are we profiling this?
    elif options.profile:
        import profile

        print "%s profile:" % sys.argv[0]
        profile.run('main(options, args)')

    else:
        main(options, args)

#END

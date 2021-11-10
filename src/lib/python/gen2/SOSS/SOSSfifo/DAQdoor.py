#!/usr/bin/env python
#
# DAQdoor.py -- a program to submit FITS frames to DAQ via a "back door".
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Tue Jan 27 17:00:54 HST 2009
#]
#
"""
A program to save FITS frames to DAQ using DAQ fifo control messages.

Usage:
  (To run a server to archive files (run as daqusr@obc1))
  
  ./DAQdoor.py --server --loglevel=0 --fitsdir=/mdata/fits

  (To submit files from another computer to above server (any user))
  ./DAQdoor.py --host=obc FILE1 FILE2 ...

  (To submit a local batch of files, list contained in a text file named
   FILE.txt)
  ./DAQdoor.py --fitsdir=/mdata/fits --framelist=FILE.txt
"""

import sys, os, re, time
import threading, Queue

import remoteObjects as ro
import logging, ssdlog
from SOSS.SOSSfifo import DAQfifoMsg
from cfg.INS import INSdata as INSconfig
from astro.fitsutils import getFrameInfoFromPath


class DAQerror(Exception):
    pass

class DAQdoor(object):

    def __init__(self, logger, ev_quit, timeout=0.1, interval=1.0,
                 fifopath='/app/OBC/dat_local/flowctrl.fifo',
                 fitsdir=''):

        self.fifopath = fifopath
        self.fitsdir = fitsdir
        self.timeout = timeout
        # Interval to wait between DAQ submissions
        self.interval = interval
        self.logger = logger
        self.ev_quit = ev_quit

        self.queue = Queue.Queue()

        # Get an instrument configuration object
        self.insconfig = INSconfig()

        # Check FIFO access
        try:
            self.daqfifo_f = open(self.fifopath, 'w')
            
        except IOError, e:
            print "Can't open '%s' for writing" % self.fifopath
            sys.exit(1)


    def ro_echo(self, arg):
        """For remoteObjects internal use."""
        return arg

    
    def _dropfifo(self, fitspath, kind):

        self.logger.info("Processing %-8.8s: %s" % (kind, fitspath))

        # Convert to absolute file path
        abspath = os.path.abspath(fitspath)
        if not os.path.exists(abspath):
            raise DAQerror("Nonexistant FITS file: '%s'" % abspath)

        # Get frame info from fits path on disk
        info = getFrameInfoFromPath(abspath)
        if not info:
            raise DAQerror("Malformed FITS file path: '%s'" % abspath)

        (frameid, fitsname, fitsdir, inscode,
         frametype, frame_no) = info

        # Double check instrument is valid
        try:
            insno = self.insconfig.getNumberByCode(inscode)

        except KeyError:
            raise DAQerror("Frameid '%s' doesn't match a valid Subaru instrument." % \
                           (frameid))

        # Sanity check DAQ control word
        kind = kind.upper().strip()
        if not kind in ('FLOWCTRL', 'FLOWSND', 'FLOWSAVE'):
            raise DAQerror("DAQ fifo message '%s' doesn't match valid types." % \
                           (kind))

        # Pad field
        kind = ('%-8.8s' % kind)
        
        # Create appropriate DAQ FIFO message
        msg = DAQfifoMsg()

        # TODO: abstract and enforce checks
        msg.set(kind=kind, frame=frameid, host=insno, manual='  ')
        self.logger.debug(str(msg))

        # Torpedo away!
        self.daqfifo_f.write(str(msg))
        self.daqfifo_f.flush()


    def service_loop(self):

        while not self.ev_quit.isSet():
            try:
                # wait for request from queue, at most self.timeout secs
                (fitspath, kind) = self.queue.get(block=True,
                                                  timeout=self.timeout)
                # have request. calculate time for interval
                endtime = time.time() + self.interval

                # process request
                self._dropfifo(fitspath, kind)

                # if there is any time left to wait in interval, wait
                rest_time = endtime - time.time()
                if rest_time > 0:
                    self.ev_quit.wait(rest_time)

            except Queue.Empty:
                # no request within timeout period, iterate
                continue

            except DAQerror, e:
                # Error handling request.  Log it and continue
                self.logger.error("Error with request '%s' for %s: %s" % (
                    kind, fitspath, str(e)))


    def flowctrl(self, fitspath):
        self.queue.put((fitspath, 'FLOWCTRL'))
        return ro.OK

    
    def flowsave(self, fitspath):
        self.queue.put((fitspath, 'FLOWSAVE'))
        return ro.OK

    
    def flowsend(self, fitspath):
        self.queue.put((fitspath, 'FLOWSND'))
        return ro.OK


    def archive_fitsbuf(self, frameid, fitsbuf, modtime):

        info = getFrameInfoFromPath(frameid)
        if not info:
            raise DAQerror("Malformed frameid: '%s'" % frameid)

        (frameid, fitsname, fitsdir, inscode,
         frametype, frame_no) = info

        insno = self.insconfig.getNumberByCode(inscode)
        
        fitspath = ('%s/obcp%02d/%s.fits' % (self.fitsdir, insno, frameid))
        if os.path.exists(fitspath):
            raise DAQerror("File already exists: %s" % fitspath)

        # Decode binary data
        data = ro.binary_decode(fitsbuf)

        try:
            out_f = open(fitspath, 'w')

            out_f.write(data)
            out_f.close()

        except IOError, e:
            raise DAQerror("Error saving file '%s': %s" % (
                fitspath, str(e)))

        try:
            # Set file modification time to desired one
            time_m = time.strftime("%Y%m%d%H%M",
                                   time.localtime(modtime))
            # warning: this may only work on Solaris!
            res = os.system("touch -acm -t %s %s" % (time_m, fitspath))
            if res != 0:
                raise DAQerror("Error changing time on '%s': res=%d" % (
                    fitspath, res))

        except OSError, e:
            raise DAQerror("Error changing time on '%s': %s" % (
                fitspath, str(e)))

        try:
            # DAQ expects files to be stored as -r--r-----
            os.chmod(fitspath, 0440)

        except OSError, e:
            raise DAQerror("Error changing permissions on '%s': %s" % (
                fitspath, str(e)))

        # Finally, drop in fifo
        self.flowctrl(fitspath)
        
        return ro.OK


def client(logger, options, args):

    import pyfits

    if options.host:
        auth = (options.svcname, options.svcname)
        svc = ro.remoteObjectClient(options.host, options.port,
                                    name=options.svcname, auth=auth)
    else:
        svc = ro.remoteObjectProxy(options.svcname)

    if options.framelist:
        # If --framelist=FILE was specified, then read FILE and make a
        # list of fits files from it.
        try:
            in_f = open(options.framelist, 'r')
            buf = in_f.read()
            args = buf.split()

            args = map(lambda fid: options.fitsdir + '/' + fid + '.fits',
                       args)
        except IOError, e:
            raise DAQerror("Failed to open '%s': %s" % (options.framelist,
                                                        str(e)))
    for fitspath in args:
        # open fits file
        try:
            fitsobj = pyfits.open(fitspath, 'readonly')

            hdr = fitsobj[0].header

        except IOError, e:
            raise DAQerror("Error opening fits file '%s': %s" % (
                fitspath, str(e)))

        # get obs date and time
        try:
            date_s = hdr['DATE-OBS'].strip()
            time_s = hdr['HST'].strip()
            frameid = hdr['FRAMEID'].strip()

        except KeyError:
            raise DAQerror("Error getting keyword info for fits file '%s'" % (
                fitspath))

        
        match = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', date_s)
        if not match:
            raise DAQerror("malformed date for fits file '%s' in DATE-OBS (%s)" % (
                fitspath, date_s))

        (yr, mo, da) = map(int, match.groups())

        match = re.match(r'^(\d{2}):(\d{2}):(\d{2})\.\d{3}$', time_s)
        if not match:
            raise DAQerror("malformed time for fits file '%s' in HST (%s)" % (
                fitspath, time_s))

        (hr, min, sec) = map(int, match.groups())

        # make mod time to pass to DAQdoor archive fn
        vec = list(time.localtime(time.time()))
        (vec[0], vec[1], vec[2], vec[3], vec[4], vec[5]) = (
            yr, mo, da, hr, min, sec)

        modtime = time.mktime(vec)

        # read fits buffer
        try:
            fits_f = open(fitspath, 'r')

            fitsbuf = fits_f.read()
            fits_f.close()

        except IOError, e:
            raise DAQerror("Error opening fits file '%s': %s" % (
                fitspath, str(e)))

        # Encode buffer for XMLRPC transport
        fitsbuf = ro.binary_encode(fitsbuf)

        print "Transmitting %s ..." % frameid
        svc.archive_fitsbuf(frameid, fitsbuf, modtime)
        
    
def server(logger, options, args):

    ev_quit = threading.Event()

    daq_obj = DAQdoor(logger, ev_quit, interval=options.interval,
                      fifopath=options.fifopath, fitsdir=options.fitsdir)
    
    svc = ro.remoteObjectServer(svcname=options.svcname,
                                obj=daq_obj, logger=logger,
                                port=options.port,
                                ev_quit=ev_quit,
                                usethread=True)
    
    # Start it
    try:
        logger.info("Starting DAQ door interface service...")
        try:
            svc.ro_start(wait=True)

            daq_obj.service_loop()

        except KeyboardInterrupt:
            logger.error("Caught keyboard interrupt!")

    finally:
        logger.info("DAQ door service shutting down...")
        svc.ro_stop()

    logger.debug("Exiting program.")
    sys.exit(0)
    

def main(options, args):

    svcname = options.svcname
    logger = ssdlog.make_logger(svcname, options)

    # Initialize remoteObjects subsystem
    try:
        ro.init()

    except ro.remoteObjectError, e:
        logger.error("Error initializing remote objects subsystem: %s" % \
                     str(e))
        sys.exit(1)

    if options.server:
        server(logger, options, args)

    client(logger, options, args)


if __name__ == '__main__':

    # Parse command line options
    from optparse import OptionParser
    
    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%prog'))
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-d", "--fitsdir", dest="fitsdir",
                      metavar="DIR", default='/tmp',
                      help="Specify DIR to store FITS files")
    optprs.add_option("--fifo", dest="fifopath", metavar="PATH",
                      default='/app/OBC/dat_local/flowctrl.fifo',
                      help="Specify PATH for DAQ fifo")
    optprs.add_option("-f", "--framelist", dest="framelist",
                      metavar="FILE",
                      help="Specify FILE containing FITS frames")
    optprs.add_option("--host", dest="host", metavar="NAME",
                      default=None,
                      help="Specify NAME for SOSS DAQ host")
    optprs.add_option("-i", "--interval", dest="interval", type="float",
                      default=1.0, metavar="SEC",
                      help="Don't prompt, but wait SEC seconds between saves")
    optprs.add_option("--port", dest="port", type="int", default=9250,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--server", dest="server", default=False,
                      action="store_true",
                      help="Operate as a DAQdoor server")
    optprs.add_option("--svcname", dest="svcname", metavar="NAME",
                      default="DAQdoor",
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

#END

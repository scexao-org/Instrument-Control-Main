#
# SKYMON.py -- SkyMonitor personality for SIMCAM (real instrument!)
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Tue Sep  2 16:28:38 HST 2008
#]
#
"""This file implements the Skymonitor device dependent SKYMON
commands.

Typical use on skymon host:
$ ./simcam.py --cam=SKYMON --obcpnum=13 --paradir=PARA/SKYMON \
    --obshost=obs --stathost=obs --framehost=obs --obchost=obc \
    --loglevel=0 --stderr --log=cams/SKYMON/skymon.log

Typical use for testing:
$ ./simcam.py --cam=SKYMON --obcpnum=13 --paradir=PARA/SKYMON \
    --daqhost=spica --framehost=spica \
    --loglevel=0 --stderr --log=cams/SKYMON/skymon.log

"""

import sys, time, os
import threading, Queue
import glob, math, re

import Task
from SIMCAM import BASECAM
import SIMCAM.cams.common as common
import astro.fitsutils as fitsutils
import Bunch
from cfg.INS import INSdata as INSconfig
import myproc

# For FITS image and header building
import numpy
import pyfits


# Software version (embedded in FITS header)
version = 20071210.00

# proposal id to embed in each FITS file
default_propid  = 'o98017'


class SKYMONError(Exception):
    pass

    
class SKYMON(BASECAM):

    def __init__(self, logger, env, ev_quit=None):

        self.logger = logger
        self.env = env
        # Convoluted but sure way of getting this module's directory
        self.mydir = os.path.split(sys.modules[__name__].__file__)[0]
        # Set ENV vars necessary for sub-processes to inherit
        os.environ['QDASVGWHOME'] = ('%s/src.c' % self.mydir)

        if not ev_quit:
            self.ev_quit = threading.Event()
        else:
            self.ev_quit = ev_quit
        # This is used to cancel long running commands
        self.ev_cancel = threading.Event()

        self.ocs = None
        self.mystatus = None

        self.mode = 'default'
        # dictionary of problem FITS files
        self.problem_files = {}

        # Contains various instrument configuration
        self.insconfig = INSconfig()

        # Thread-safe bunch for storing parameters read/written
        # by threads executing in this object
        self.param = Bunch.threadSafeBunch()
        
        # Interval between images (secs)
        #self.param.snap_interval = 60 * 1
        self.param.snap_interval = 1

        # Interval between status packets (secs)
        self.param.status_interval = 60 * 1

        # Skymonitor configuration parameters
        self.param.incoming_dir = "/data/SKYMON/Incoming"
        self.param.process1_dir = "/data/SKYMON/Process1"
        self.param.process2_dir = "/data/SKYMON/Process2"
        self.param.outgoing_dir = "/data/SKYMON/Outgoing"
        self.param.exptime = 3.33
        
        # Time to enable automatic image sending.
        # (Skymonitor camera shutter opens at 6pm)
        #self.param.autosnap_start = "18:00:00"
        self.param.autosnap_start = "17:00:00"
        
        # Time to disable automatic image sending
        # (Skymonitor camera shutter closes at 6am)
        self.param.autosnap_stop = "06:00:00"
        #elf.param.autosnap_stop = "18:00:00"
        
        # This controls automatic generation of FITS files
        self.ev_auto = threading.Event()
        # Uncomment this to have Skymonitor fire up in AUTOSEND mode
        self.ev_auto.set()
        
        # SKYMON pulls status in sets.  These are the known sets.
        self.statusset = Bunch.Bunch()
        self.statusset.DOME = {'CXWS.TSCV.SHUTTER': 0,
                               }

        self.statusset.START_EXP = {'FITS.SBR.UT1-UTC': 0,
                                    'FITS.SBR.TELESCOP': 0,
                                    'FITS.SBR.MAINOBCP': 0,
                                    'CXWS.TSCV.SHUTTER': 0,
                                    'TSCS.AZ': 0,
                                    
                                    'FITS.SBR.OUT_HUM': 0,
                                    'FITS.SBR.OUT_TMP': 0,
                                    'FITS.SBR.OUT_WND': 0,
                                    'FITS.SBR.OUT_PRS': 0,
                                    
                                    'FITS.SKY.OBSERVER': 0,
                                    'FITS.SKY.OBJECT': 0,
                                    'FITS.SKY.PROP-ID': 0,
                                    }

        self.statusset.PROP_TMPL = ['FITS.%3.3s.PROP-ID',
                                    'FITS.%3.3s.OBJECT',
                                    'FITS.%3.3s.OBSERVER',
                                    ]
        
    #######################################
    # INITIALIZATION
    #######################################

    def initialize(self, ocsint):
        '''Initialize instrument.  
        '''
        # Grab my handle to the OCS interface.
        self.ocs = ocsint

        # Thread pool for autonomous tasks
        self.threadPool = self.ocs.threadPool

        # For task inheritance:
        self.tag = 'skymon'
        self.shares = ['logger', 'ev_quit', 'threadPool']
        
        self.param.fitscount = 0

        # dictionary of problem FITS files
        self.problem_files = {}

        # Used to format status buffer (item lengths must match definitions
        # of status aliases on SOSS side in $OSS_SYSTEM/StatusAlias.pro)
        statfmt = "%(status)-8.8s,%(mode)-8.8s,%(count)8d,%(frame)12.12s;"

        # Register my status.
        self.stblname = 'SKYS0001'
        self.mystatus = self.ocs.addStatusTable(self.stblname,
                                                ['status', 'mode',
                                                 'count', 'frame'],
                                                formatStr=statfmt)
        # Establish initial status values
        self.mystatus.status = 'ALIVE'
        self.mystatus.mode = 'LOCAL'
        self.mystatus.count = self.param.fitscount
        self.mystatus.frame = ''

        # Will be set to periodic status task
        self.status_task = None
        # Will be set to periodic power monitoring task
        self.power_task = None
        self.power_time = None
        # Will be set to periodic fits file generation task
        self.fitsGenTask = None


    def start(self, wait=True):
        super(SKYMON, self).start(wait=wait)

        # Start auto-generation of FITS task
        t = FitsGenTask(self)
        self.fitsGenTask = t
        t.init_and_start(self)

        # Start auto-generation of status task
        t = common.IntervalTask(self.putstatus, 60.0)
        self.status_task = t
        t.init_and_start(self)


    def stop(self, wait=True):
        super(SKYMON, self).stop(wait=wait)
        
        self.ev_cancel.set()
        
        # Stop any tasks, etc.
        # Terminate status generation task
        if self.status_task != None:
            self.status_task.stop()

        self.status_task = None

        if self.fitsGenTask != None:
            self.fitsGenTask.stop()

        self.fitsGenTask = None
        self.logger.info("SKYMON STOPPED.")


    #######################################
    # INTERNAL METHODS
    #######################################

    def statusGenLoop(self):
        """The main status sending loop.
        """
        
        self.logger.info('Starting periodic sending of status')

        while not self.ev_quit.isSet():

            time_end = time.time() + self.param.status_interval

            try:
                self.putstatus()

            except Exception, e:
                self.logger.error("Error sending status: %s" % str(e))

            # Sleep for remainder of desired interval.  We sleep in
            # small increments so we can be responsive to changes to
            # ev_quit
            cur_time = time.time()
            self.logger.debug("Waiting interval, remaining: %f sec" % \
                              (time_end - cur_time))

            while (cur_time < time_end) and (not self.ev_quit.isSet()):
                self.ev_quit.wait(min(0.1, time_end - cur_time))
                cur_time = time.time()

            self.logger.debug("End interval wait")
                
        self.logger.info('Stopping periodic sending of status')


    def discover_files(self):

        # Get the directory listing, and sort, so that earlier
        # frames get processed first.
        dirlist = os.listdir(self.param.process1_dir)
        dirlist.sort()

        for filename in dirlist:

            # Skip non-fits and problem files
            match = re.match('^([-\w\.]+\.fits)$', filename)
            if not match or self.problem_files.has_key(filename):
                continue

            # Try to process the file.
            try:
                self.logger.info("Processing '%s'" % filename)

                # Process the file
                res = self.exp(motor='ON', infile=filename)
                if res != 0:
                    self.logger.error("Processing file '%s' returned error code: %d" % (filename, res))
                    self.problem_files[filename] = True
                    continue

                # If there were no errors then remove the input file
                infits = self.param.process1_dir + '/' + filename
                if os.path.exists(infits):
                    os.remove(infits)

            except Exception, e:
                self.logger.error("Processing file '%s' raised exception: %s" % (filename, str(e)))
                self.problem_files[filename] = True


    def fitsGenLoop(self):
        """The main periodic exposure generation loop.
        """
        
        self.logger.info('Starting periodic generation of FITS files')

        while not self.ev_quit.isSet():

            time_start = time.time()

            if self.ev_auto.isSet() and autoSnapOK(self.param.autosnap_start,
                                                   self.param.autosnap_stop,
                                                   time_start):

                try:
                    #self.logger.debug("autosnap OK; calling discover_files()")

                    self.discover_files()
                    
                except Exception, e:
                    self.logger.error("processing error: %s" % str(e))

                # Sleep for remainder of desired interval.  We sleep in
                # small increments so we can be responsive to changes to
                # parameters to the AUTOSNAP command
                cur_time = time.time()
                time_end = time_start + self.param.snap_interval
                self.logger.debug("Waiting interval, remaining: %f sec" % \
                                  (time_end - cur_time))

                while (cur_time < time_end) and self.ev_auto.isSet() and \
                          (not self.ev_quit.isSet()):
                    self.ev_quit.wait(min(0.1, time_end - cur_time))
                    cur_time = time.time()
                    # snap_interval may have changed
                    time_end = time_start + self.param.snap_interval

                self.logger.debug("End interval wait")
                
            else:
                #self.logger.debug("autosnap NG; sleep...")
                self.ev_quit.wait(0.1)
                
                
        self.logger.info('Stopping periodic generation of FITS files')


    def _update_hdr(self, hdr, statusDict,
                    time_start=0.0, time_end=0.0, frameid='',
                    propid=default_propid):
        """Function to prepare the FITS header.
        _hdr_ is a pyfits header object;
        _statusDict_ is a dictionary full of alias/value combinations
          necessary to synthesize the FITS keywords
        _time_start_ is the starting time of the exposure (in secs)
        _time_end_ is the ending time of the exposure (in secs)
        _frameid_ is the Subaru frame id of the file
        _propid_ is the Subaru proposal id of the file
        """

        hdr.update("BSCALE", 1.0, comment="Real=fits-value*BSCALE+BZERO")
        hdr.update("BZERO", 0.0, comment="Real=fits-value*BSCALE+BZERO")
        hdr.update("BUNIT", "CCD COUNT IN ADU",
                   comment="Unit of original pixel values")
        hdr.update("BLANK", -32767, comment="Value used for NULL pixels")
        hdr.update("TIMESYS", "UTC",
                   comment="Time System used in the header. UTC fix")

        hdr.update("DATE-OBS", fitsutils.calcObsDate(time_start),
                   comment="Observation start date (yyyy-mm-dd)")

        ut1_utc = float(statusDict['FITS.SBR.UT1-UTC'])
        val = fitsutils.calcUT(time_start, ut1_utc=ut1_utc)
        hdr.update("UT", val, comment="HH:MM:SS.S typical(start) UTC at exposure")
##         hdr.update("UT-STR", val,
##                    comment="HH:MM:SS.S UTC at the start of exposure")
##         hdr.update("UT-END", fitsutils.calcUT(time_end),
##                    comment="HH:MM:SS.S UTC at the end of exposure")

        val = fitsutils.calcMJD(time_start, ut1_utc=ut1_utc)
        hdr.update("MJD", val,
                   comment="[d] Mod.Julian Date at typical(start) time")
##         hdr.update("MJD-STR", val,
##                    comment="[d] Mod.Julian Date at the start of exposure")
##         hdr.update("MJD-END", fitsutils.calcMJD(time_end),
##                    comment="[d] Mod.Julian Date at the end of exposure")

        val = fitsutils.calcHST(time_start, ut1_utc=ut1_utc)
        hdr.update("HST", val, comment="HH:MM:SS.S typical(start) HST at exposure")
##         hdr.update("HST-STR", val,
##                    comment="HH:MM:SS.S HST at the start of exposure")
##         hdr.update("HST-END", fitsutils.calcHST(time_end),
##                    comment="HH:MM:SS.S HST at the end of exposure")

        val = fitsutils.calcLST(time_start, ut1_utc=ut1_utc)
        hdr.update("LST", val, comment="HH:MM:SS.S typical(start) LST at exposure")
##         hdr.update("LST-STR", val,
##                    comment="HH:MM:SS.S LST at the start of exposure")
##         hdr.update("LST-END", fitsutils.calcLST(time_end),
##                    comment="HH:MM:SS.S LST at the end of exposure")

        hdr.update("EXPTIME", (time_end - time_start),
                   comment="Total integration time of the frame (sec)")

        hdr.update("PROP-ID", propid, comment="Proposal ID")
        hdr.update("OBSERVAT", "NAOJ", comment="Observatory")
        hdr.update("TELESCOP", "Subaru",
                   comment="Telescope/System which Inst. is attached")

        hdr.update("FRAMEID", frameid,
                   comment="Image sequential number")
        hdr.update("EXP-ID", frameid,
                   comment="ID of the exposure this data was taken")

        hdr.update("INSTRUME", "Skymonitor", comment="Name of instrument")
##         hdr.update("OBJECT", statusDict['FITS.SKY.OBJECT'],
##                    comment="Target Description")
        hdr.update("OBJECT", "Skymonitor",
                   comment="Target Description")
        hdr.update("DATA-TYP", "Skymonitor",
                   comment="Type/Characteristics of this data")
        hdr.update("DETECTOR", "Skymonitor", comment="Name of the detector/CCD")

        hdr.update("GAIN", 1.0, comment="AD conversion factor (electron/ADU)")

        hdr.update("OUT-HUM", statusDict['FITS.SBR.OUT_HUM'],
                   comment="Humidity measured outside of dome (\%)")
        hdr.update("OUT-TMP", statusDict['FITS.SBR.OUT_TMP'],
                   comment="Temperature measured outside of dome (K)")
        hdr.update("OUT-WND", statusDict['FITS.SBR.OUT_WND'],
                   comment="Wind velocity outside of dome (m/s)")
        hdr.update("OUT-PRS", statusDict['FITS.SBR.OUT_PRS'],
                   comment="Atmospheric pressure outside of dome (hpa)")
##         hdr.update("ENVDIR", statusDict['TSCL.WINDD'],
##                    comment="Wind direction outside of dome (deg)")
        hdr.update("E_CIRRUS", -1.0, comment="Cirrus coverage")
        hdr.update("E_CLOUD", -2.0, comment="Cloud coverage")

        hdr.update("VERSION", version, comment="Software version")



    def _process(self, statusDict, infile='in.fits', outfile='out.fits'):
        """Snap an exposure.
        """

        #TODO: make thread safe

        # Check end of processing chain for existing output file with this name
        outfits = self.param.outgoing_dir + '/' + outfile
        if os.path.exists(outfits):
            self.logger.error("FITS file already exists: %s" % outfits)
            return 1

        # SECOND STAGE PROCESSING.
        # Add fits headers corresponding to ocs status items.  At end of
        # this stage, file SkyMonitorPicYYYYMMDDHHMMSS.fits in has resulted
        # in new file SkyMonitorPic-SKYAXXXXXXXX.fits.
        
        # Extract frame id (SKYAXXXXXXXX) from output file name
        match = re.match(r'^([-\w\.]+)\.fits$', outfile)
        if not match:
            self.logger.error("Bad output filename: %s" % outfile)
            return 1

        frameid = match.group(1)
        
        # Decode image date from input file name YYYYMMDDHHMMSS
        match = re.match(r'^SkyMonitorPic(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})\.fits$', infile)
        if not match:
            self.logger.error("Bad input filename: %s" % infile)
            return 1

        # Calculate start and end of exposure
        (yr, mo, da, hr, min, sec) = map(int, match.groups())
        time_start = time.mktime((yr, mo, da, hr, min, sec, 0, 0, 0))
        time_end = time_start + self.param.exptime

        # Construct file paths for second stage processing
        infits  = self.param.process1_dir + '/' + infile
        outfits = self.param.process2_dir + '/SkyMonitorPic-' + outfile
        if os.path.exists(outfits):
            self.logger.error("FITS file already exists: %s" % outfits)
            return 1

        # Open the input fits file
        try:
            #fitsobj = pyfits.open(infits, 'readonly')
            infitsobj = pyfits.open(infits, 'readonly')

        except IOError, e:
            self.logger.error("Error opening FITS file '%s': %s" % (
                              infits, str(e)))
            return 1

	# TEMP
	hdu = pyfits.PrimaryHDU(infitsobj[0].data)
        
        try:
            #prihdr = fitsobj[0].header
            prihdr = hdu.header
            try:
                # Update FITS keywords in primary HDU header
                self._update_hdr(prihdr, statusDict,
                                 time_start=time_start, time_end=time_end,
                                 frameid=frameid)
            except Exception, e:
                self.logger.error('Error building FITS header: %s' % str(e))
                self.logger.error('statusDict=%s' % str(statusDict))
                return 1

            try:
                self.logger.debug('End exposure; writing fits file (%s)' % \
                                  outfits)
                hdu.writeto(outfits)
                hdu.close()

            except OSError, e:
                self.logger.error("Can't write file: %s" % fitsfile)
                return 1
        finally:
            infitsobj.close()

        # If stage2 was successful then remove the input file.
        try:
            os.remove(infits)

        except OSError, e:
            self.logger.error('Failed to remove input file (%s): %s' % (
                infits, str(e)))
            return 1

        # Set up paths for third stage processing
        infits  = outfits
        outfits = self.param.outgoing_dir + '/' + outfile
        if os.path.exists(outfits):
            self.logger.error("FITS file already exists: %s" % outfits)
            return 1

        # THIRD STAGE PROCESSING.
        # Now call Kosugi-san's program to reprocess the FITS file
        # (crops, scales, rotates, annotates).  Needs AZ because camera
        # is mounted on rotating dome; need to rotate image to consistent
        # orientation (North=UP)
        az = statusDict['TSCS.AZ']
        cmdstr = "%s/src.c/QDASvgwSkyFormatFits %f IR %s %s" % (
            self.mydir, az, infits, outfits)

        # Shell out to program
        self.logger.debug("Shell exec: '%s'" % cmdstr)
        proc = myproc.myproc(cmdstr)

        status = proc.wait(timeout=None)
        self.logger.debug("Output: '%s'" % proc.output())
        reason = proc.reason()
        if (status != 'exited') or (reason != 0):
            self.logger.error("QDASvgwSkyFormatFits error: %s" % str(reason))
            return 1
        
        # If stage3 was successful then remove the input file.
        try:
            os.remove(infits)

        except OSError, e:
            self.logger.error('Failed to remove input file (%s): %s' % (
                infits, str(e)))
            return 1

        # Update snap count
        self.param.fitscount += 1
        self.mystatus.count = self.param.fitscount

        return 0


    def _archive(self, frameid, fitsfile):
        """Convenience method for archiving a fits file.
        Try to archive _fitsfile_ as _frameid_ using instrument interface.
        """
        framelist = [(frameid, fitsfile)]
        self.logger.debug("Submitting framelist: %s" % str(framelist))

        res = self.ocs.archive_fits(framelist)
        if res != 0:
            self.logger.error("Archive of '%s' failed." % fitsfile)

        return res


    def _getstatus(self, statusDict):
        """Get status values corresponding to keys in the _statusDict_.
        """

        # Use "fast" status interface
        #self.ocs.getOCSstatus(statusDict)
        self.ocs.requestOCSstatus(statusDict)

        # This request is not logged over DAQ logs
        self.logger.debug("statusDict: %s" % str(statusDict))


    def _calc_obsinfo(self, statusDict):
        """Calculate status values for FITS.SBR.PROP-ID and FITS.SBR.OBJECT
        if they are not already properly defined in _statusDict_.
        """

        if statusDict['FITS.SKY.PROP-ID'].startswith('#'):
            # Observers did NOT allocate Skymonitor.  Instead, look
            # up the main allocated instrument and try to get the values
            # from that
            insname = statusDict['FITS.SBR.MAINOBCP']
            if not insname.startswith('#'):
                # Look up 3-letter code by instrument name
                inscode = self.insconfig.getCodeByName(insname)

                # Add variables FITS.XXX.PROP-ID and FITS.XXX.OBJECT,
                # where XXX is the 3-letter code of the main instrument
                propalias = 'FITS.%3.3s.PROP-ID' % inscode
                objalias = 'FITS.%3.3s.OBJECT' % inscode
                statusDict2 = { propalias: '#', objalias: '#' }

                # Now fetch that status set
                self._getstatus(statusDict2)

                # Substitute these values for the SKY versions
                statusDict['FITS.SKY.PROP-ID'] = statusDict2[propalias]
                statusDict['FITS.SKY.OBJECT']  = statusDict2[objalias]

        # set default object and propid, if not set properly
        if statusDict['FITS.SKY.PROP-ID'].startswith('#'):
            statusDict['FITS.SKY.PROP-ID'] = default_propid
        if statusDict['FITS.SKY.OBJECT'].startswith('#'):
            statusDict['FITS.SKY.OBJECT'] = ''

    

    #######################################
    # INSTRUMENT COMMANDS
    #######################################

    def exp(self, motor='OFF', frameid=None, infile='test.fits'):
        """Same as snap(), except try to archive the resulting FITS file.
        Expects a _frameid_ to be passed; if one is not, then it will attempt
        to allocate one from the OCS.
        """
        if not frameid:
            self.logger.debug('Requesting frame from OCS.')
            framelist = self.ocs.getFrames(1, 'A')
            if (type(framelist) != type(['x'])) or (len(framelist) != 1):
                self.logger.error("Error getting frame id: got '%s'" % \
                                  str(framelist))
                return 1
                
            frameid = framelist[0]
            self.logger.debug("Got frame id '%s'." % frameid)

        # Take the exposure
        outfile = frameid + '.fits'
        res = self.snap(motor=motor, infile=infile, outfile=outfile)
        if res != 0:
            self.logger.error("Snap failed.")
            return res

        # Archive the final product
        fitsfile = self.param.outgoing_dir + '/' + outfile

        res = self._archive(frameid, fitsfile)
        if res != 0:
            self.logger.error("Archive of frame '%s' failed." % frameid)
            return res

        # Update status value
        self.mystatus.frame = frameid

        return 0


    def snap(self, motor='ON', infile='test.fits', outfile='out.fits'):
        """Snap an exposure.
        """

        #TODO: make thread safe

        # Request our status set "START_EXP"
        statusDict = self.statusset.START_EXP
        self._getstatus(statusDict)

        # Check that observer info are properly defined
        #self._calc_obsinfo(statusDict)
        
        res = self._process(statusDict, infile=infile, outfile=outfile)

        return res


    def cancel(self):
        self.logger.debug("CANCEL--setting cancel event")
        self.ev_cancel.set()

        return 0

    
    def reqstatus(self, target="ALL"):
        """Forced import of our status using the normal status interface.
        """
        # Request our status set "START_EXP"
        statusDict = self.statusset.START_EXP
        self.ocs.requestOCSstatus(statusDict)

        return 0


    def getstatus(self, target="ALL"):
        """Forced import of our status using the 'fast' status interface.
        """
        # Request our status set "START_EXP"
        statusDict = self.statusset.START_EXP
        self.ocs.getOCSstatus(statusDict)
        # This request is not logged over DAQ logs
        self.logger.info("statusDict1: %s" % str(statusDict))

        return 0


    def putstatus(self, target="ALL"):
        """Forced export of our status.
        """
        return self.ocs.exportStatus()


    def reqframes(self, num=1, type="A"):
        """Forced frame request.
        """
        framelist = self.ocs.getFrames(num, type)

        # This request is not logged over DAQ logs
        self.logger.info("framelist: %s" % str(framelist))

        return 0


    def autosnap(self, motor="OFF", interval=None):
        """Turn on/off and configure auto generation of FITS files.
        """

        if interval != None:
            self.param.snap_interval = interval
            
        if motor.upper() == 'ON':
            self.ev_auto.set()
            
        elif motor.upper() == 'OFF':
            self.ev_auto.clear()

        else:
            self.logger.error("bad parameter: motor=%s" % str(motor))
            return 1
            
        return 0


    def setcount(self, count=0):
        self.param.fitscount = int(count)
        self.mystatus.count = self.param.fitscount

        self.putstatus()
        return 0

        
    #######################################
    # UTILITY FUNCTIONS
    #######################################

def autoSnapOK(autosnap_start, autosnap_stop, cur_time=None):
    """Checks if _cur_time_ (usually current time in secs) is between
    the _autosnap_start_ and _autosnap_stop_ times (each specified as
    'HH:MM:SS' in 24-hour time).  Returns True if it is, False if not.
    """

    if cur_time == None:
        cur_time = time.time()

    elif type(cur_time) != type(1.0):
        # Assume passed in as "HH:MM:SS"--mostly for testing
        (yr, mo, da, hr, min, sec, wday, yday, isdst) = \
             time.localtime(time.time())

        (cur_hr_str, cur_min_str, cur_sec_str) = cur_time.split(':')
        hr = int(cur_hr_str)
        min = int(cur_min_str)
        sec = int(cur_sec_str)
        # convert back to a float repr
        cur_time = time.mktime((yr, mo, da, hr, min, sec,
                                wday, yday, isdst))

    # Get hr, min, sec of start time
    (start_hr_str, start_min_str, start_sec_str) = \
                   autosnap_start.split(':')
    # Now establish start time (as float) based on current time.
    # If it is earlier than 8am then reckon from the previous day.
    (yr, mo, da, hr, min, sec, wday, yday, isdst) = \
         time.localtime(cur_time)
    if hr < 8:
        (yr, mo, da, hr, min, sec, wday, yday, isdst) = \
             time.localtime(cur_time - (3600 * 8))
        
    # Calculate start time in secs since epoch
    hr = int(start_hr_str)
    min = int(start_min_str)
    sec = int(start_sec_str)
    start_time = time.mktime((yr, mo, da, hr, min, sec, wday, yday, isdst))

    # Get hr, min, sec of end time
    (stop_hr_str, stop_min_str, stop_sec_str) = \
                  autosnap_stop.split(':')

    # Now establish stop time (as float) based on current time.
    # If it is later than 8pm then reckon from the next day.
    (yr, mo, da, hr, min, sec, wday, yday, isdst) = \
         time.localtime(cur_time)
    if hr > 16:
        (yr, mo, da, hr, min, sec, wday, yday, isdst) = \
             time.localtime(cur_time + (3600 * 8))
        
    # Calculate stop time in secs since epoch
    hr = int(stop_hr_str)
    min = int(stop_min_str)
    sec = int(stop_sec_str)
    stop_time = time.mktime((yr, mo, da, hr, min, sec, wday, yday, isdst))

    if (cur_time >= start_time) and (cur_time < stop_time):
        res = True
    else:
        res = False

    return res


    def power_off(self):
        """
        This method is called when the summit begins to run on UPS
        power.  Effect an orderly shutdown once time exceeds a certain
        limit.
        """
        # Record time of initial call of running on UPS
        if not self.power_time:
            self.power_time = time.time()

        # Once power has been off for 60 secs or more, shutdown
        if (time.time() - self.power_time) > 60.0:
            try:
                res = os.system('/usr/sbin/shutdown -h 60')

                self.stop()
            
                self.ocs.shutdown(res)

            except OSError, e:
                self.logger.error("Error issuing shutdown: %s" % str(e))

    def power_on(self):
        """
        This method is called when the summit begins to run on line
        power again.
        """
        self.power_time = None

    
    #######################################
    # Tasks for autonomous threads.
    #######################################

class FitsGenTask(Task.Task):
    """Task that runs the fitsGenLoop() method to automatically snap
    an image periodically.
    """

    def __init__(self, fm):
        self.fm = fm
        super(FitsGenTask, self).__init__()

    def stop(self):
        self.ev_quit.set()
        
    def execute(self):
        self.fm.fitsGenLoop()

        return 0


#END SKYMON.py

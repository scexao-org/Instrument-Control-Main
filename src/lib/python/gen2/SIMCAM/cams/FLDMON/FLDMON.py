#
# FLDMON.py -- FieldMonitor personality for SIMCAM (real instrument!)
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Apr 23 13:40:08 HST 2009
#]
#
"""This file implements the FieldMonitor device dependent FLDMON
commands.

Typical use on fldmon host:
$ ./simcam.py --cam=FLDMON --obcpnum=19 --paradir=PARA \
    --obshost=obs --stathost=obs --framehost=obs --obchost=obc \
    --loglevel=0 --stderr --log=cams/FLDMON/fldmon.log

Typical use for testing:
$ ./simcam.py --cam=FLDMON --obcpnum=19 --paradir=PARA \
    --daqhost=spica --framehost=spica \
    --loglevel=0 --stderr --log=cams/FLDMON/fldmon.log

"""

import sys, time, os
import threading, Queue
import glob, math

import Task
from SIMCAM import BASECAM, CamError, CamCommandError
import SIMCAM.cams.common as common
import astro.fitsutils as fitsutils
import Bunch
from cfg.INS import INSdata as INSconfig

# For FITS image and header building
import numpy
import pyfits
# Does the actual image capture
try:
    import pycap
except ImportError, e:
    print """
    ******************************* 
    Failed to import 'pycap' module.
    NO IMAGE CAPTURE WILL BE POSSIBLE
    *******************************"""


class FLDMONError(Exception):
    pass

    
class FLDMON(BASECAM):

    def __init__(self, logger, env, ev_quit=None):

        self.logger = logger
        # Convoluted but sure way of getting this module's directory
        self.mydir = os.path.split(sys.modules[__name__].__file__)[0]

        if not ev_quit:
            self.ev_quit = threading.Event()
        else:
            self.ev_quit = ev_quit

        # This is used to cancel long running commands
        self.ev_cancel = threading.Event()

        self.ocs = None
        self.mystatus = None

        self.mode = 'default'

        # Contains various instrument configuration
        self.insconfig = INSconfig()

        # Width and height of video image
        self.width  = 320
        self.height = 240

        # Construct numpy used to flip image horizontally
        self.flip_h = numpy.arange(self.width-1, -1, -1)

        # Various measured parameters for Fieldmonitor camera
        # (provided kindly by Takato-san)
        self.pa_offset = 3.87
        self.crpix1 = 164
        self.crpix2 = 64
        self.cdelt1 = 0.1216
        self.cdelt2 = 0.1184
        
        # Thread-safe bunch for storing parameters read/written
        # by threads executing in this object
        self.param = Bunch.threadSafeBunch()
        
        # Camera defaults (taken from original cap.c program)
        self.param.brightness = 60000
        self.param.hue = 32767
        self.param.color = 32767
        self.param.contrast = 64000
        self.param.whitebal = 32767

        # Wait time after starting capture (in usec).
        self.param.waittime = 0

        # Number of subintegrations.
        self.param.subinteg = 1

        # Total integration time
        self.param.integtime = 10.0

        # Number of images stacked
        self.param.stacksize = 7

        # Coadd factor
        self.param.coadd = 1.0

        # Pixel type
        self.param.pxtype = 'Int16'

        # Interval between images (secs)
        self.param.snap_interval = 60

        # Interval between status packets (secs)
        self.param.status_interval = 60 * 1

        # Where to store my locally generated FITS files.
        self.param.fitsdir = "/data/FLDMON/fits"
        
        # Where is my flat-fielding FITS file
        self.param.flatfile = "/data/FLDMON/calib/flat.fits"
        
        # Time to enable automatic image sending.
        # (FieldMonitor camera shutter opens at 6pm)
        self.param.autosnap_start = "18:00:00"
        
        # Time to disable automatic image sending
        # (FieldMonitor camera shutter closes at 6am)
        self.param.autosnap_stop = "06:00:00"
        
        # This controls automatic generation of FITS files
        self.ev_auto = threading.Event()
        # Uncomment this to have FieldMonitor fire up in AUTOSEND mode
        self.ev_auto.set()
        
        # FLDMON pulls status in sets.  These are the known sets.
        self.statusset = Bunch.Bunch()
        self.statusset.DOME = {'CXWS.TSCV.SHUTTER': 0,
                               }

        self.statusset.START_EXP = {'FITS.SBR.UT1-UTC': 0,
                                    'FITS.SBR.TELESCOP': 0,
                                    'FITS.SBR.MAINOBCP': 0,
                                    'TSCS.EL': 0,
                                    'TSCS.AZ': 0,
                                    
                                    'FITS.SBR.AIRMASS': 0,
                                    'FITS.SBR.ALTITUDE': 0,
                                    'FITS.SBR.AZIMUTH': 0,
                                    'FITS.SBR.EQUINOX': 0,
                                    'FITS.SBR.RA': 0,
                                    'FITS.SBR.DEC': 0,
                                    'FITS.SBR.OUT_HUM': 0,
                                    'FITS.SBR.OUT_TMP': 0,
                                    'FITS.SBR.OUT_WND': 0,
                                    'FITS.SBR.OUT_PRS': 0,
                                    'TSCL.WINDD': 0,
                                    
                                    'FITS.FLD.OBSERVER': 0,
                                    'FITS.FLD.OBJECT': 0,
                                    'FITS.FLD.PROP-ID': 0,
                                    }

        self.statusset.END_EXP = {'TSCS.EL': 0,
                                  'FITS.SBR.AIRMASS': 0,
                                  'FITS.SBR.ALTITUDE': 0,
##                                   'FITS.SBR.AZIMUTH': 0,
##                                   'FITS.SBR.EQUINOX': 0,
##                                   'FITS.SBR.RA': 0,
##                                   'FITS.SBR.DEC': 0,
                                  }

        self.statusset.PROP_TMPL = ['FITS.%3.3s.PROP-ID',
                                    'FITS.%3.3s.OBJECT',
                                    'FITS.%3.3s.OBSERVER',
##                                     'FITS.%3.3s.OBS-ALOC',
##                                     'FITS.%3.3s.FOC-POS',
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
        self.tag = 'fldmon'
        self.shares = ['logger', 'ev_quit', 'threadPool']
        
        self.param.fitscount = 0

        # Used to format status buffer (item lengths must match definitions
        # of status aliases on SOSS side in $OSS_SYSTEM/StatusAlias.pro)
        statfmt1 = "%(status)-8.8s,%(mode)-8.8s,%(count)8d,%(frame)12.12s;"

        # Register my status.
        self.stblname = 'FLDS0001'
        self.mystatus = self.ocs.addStatusTable(self.stblname,
                                                ['status', 'mode', 'count',
                                                 'frame'],
                                                formatStr=statfmt1)
        
        # Establish initial status values
        self.mystatus.status = 'ALIVE'
        self.mystatus.mode = 'LOCAL'
        self.mystatus.count = self.param.fitscount
        self.mystatus.frame = ''

        # Will be set to periodic status task
        self.status_task = None
        # Will be set to power monitoring task
        self.power_task = None
        # Will be set to periodic fits file generation task
        self.fitsGenTask = None

        # Initialize the video settings.
        pycap.setup(self.param.brightness, self.param.hue, self.param.color,
                    self.param.contrast, self.param.whitebal)

        self.flatfield = None


    def start(self, wait=True):
        super(FLDMON, self).start(wait=wait)
        
        self.logger.info('***** FLDMON STARTED *****')

        # Start auto-generation of FITS task
        t = FitsGenTask(self)
        self.fitsGenTask = t
        t.init_and_start(self)

        # Start auto-generation of status task
        t = common.IntervalTask(self.putstatus, 60.0)
        self.status_task = t
        t.init_and_start(self)

        # Start task to monitor summit power.  Call self.power_off
        # when we've been running on UPS power for 60 seconds
        #t = common.PowerMonTask(self, self.power_off, upstime=60.0)
        #self.power_task = t
        #t.init_and_start(self)


    def stop(self, wait=True):
        super(FLDMON, self).stop(wait=wait)
        
        self.ev_cancel.set()
        
        # Stop any tasks, etc.
        # Terminate status generation task
        if self.status_task != None:
            self.status_task.stop()

        self.status_task = None

        # Terminate power monitoring task
        if self.power_task != None:
            self.power_task.stop()

        self.power_task = None

        if self.fitsGenTask != None:
            self.fitsGenTask.stop()

        self.fitsGenTask = None
        self.logger.info("FLDMON STOPPED.")


    #######################################
    # INTERNAL METHODS
    #######################################

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
                    # Request our status set "DOME"
                    statusDict = self.statusset.DOME
                    self._getstatus(statusDict)
		    try:
                        shutter = eval('0x' + statusDict['CXWS.TSCV.SHUTTER'])

                    except (ValueError, TypeError), e:
		        shutter = 0

                    if (shutter & 0xF0) == 0xA0:
                        self.logger.debug("Dome closed; not generating file")

                    else:
                        self.logger.debug("autosnap OK; calling exp()")
                        self.exp(motor='ON',
                                 #frameid=('FLDA8%07d' % self.param.fitscount),
                                 stacksize=self.param.stacksize,
                                 waittime=self.param.waittime,
                                 subinteg=self.param.subinteg,
                                 integtime=self.param.integtime,
                                 coadd=self.param.coadd,
                                 pxtype=self.param.pxtype)

                except Exception, e:
                    self.logger.error("exp error: %s" % str(e))

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
                self.ev_quit.wait(0.1)
                
                
        self.logger.info('Stopping periodic generation of FITS files')


    def _update_hdr(self, hdr, statusDict,
                    time_start=0.0, time_end=0.0, frameid=''):
        """Function to prepare the FITS header.
        _hdr_ is a pyfits header object;
        _statusDict_ is a dictionary full of alias/value combinations
          necessary to synthesize the FITS keywords
        _time_start_ is the starting time of the exposure (in secs)
        _time_end_ is the ending time of the exposure (in secs)
        """

        hdr.update("BSCALE", 1.0, comment="Real=fits-value*BSCALE+BZERO")
        hdr.update("BZERO", 0.0, comment="Real=fits-value*BSCALE+BZERO")
        hdr.update("BUNIT", "CCD COUNT IN ADU",
                   comment="Unit of original pixel values")
        hdr.update("BLANK", 0, comment="Value used for NULL pixels")
        hdr.update("TIMESYS", "UTC",
                   comment="Time System used in the header. UTC fix")

        hdr.update("DATE-OBS", fitsutils.calcObsDate(time_start),
                   comment="Observation start date (yyyy-mm-dd)")

        ut1_utc = float(statusDict['FITS.SBR.UT1-UTC'])
        val = fitsutils.calcUT(time_start, ut1_utc=ut1_utc)
        hdr.update("UT", val, comment="HH:MM:SS.S typical(start) UTC at exposure")
        hdr.update("UT-STR", val,
                   comment="HH:MM:SS.S UTC at the start of exposure")
        hdr.update("UT-END", fitsutils.calcUT(time_end),
                   comment="HH:MM:SS.S UTC at the end of exposure")

        val = fitsutils.calcHST(time_start, ut1_utc=ut1_utc)
        hdr.update("HST", val, comment="HH:MM:SS.S typical(start) HST at exposure")
        hdr.update("HST-STR", val,
                   comment="HH:MM:SS.S HST at the start of exposure")
        hdr.update("HST-END", fitsutils.calcHST(time_end),
                   comment="HH:MM:SS.S HST at the end of exposure")

        val = fitsutils.calcLST(time_start, ut1_utc=ut1_utc)
        hdr.update("LST", val, comment="HH:MM:SS.S typical(start) LST at exposure")
        hdr.update("LST-STR", val,
                   comment="HH:MM:SS.S LST at the start of exposure")
        hdr.update("LST-END", fitsutils.calcLST(time_end),
                   comment="HH:MM:SS.S LST at the end of exposure")

        val = fitsutils.calcMJD(time_start, ut1_utc=ut1_utc)
        hdr.update("MJD", val,
                   comment="[d] Mod.Julian Date at typical(start) time")
        hdr.update("MJD-STR", val,
                   comment="[d] Mod.Julian Date at the start of exposure")
        hdr.update("MJD-END", fitsutils.calcMJD(time_end),
                   comment="[d] Mod.Julian Date at the end of exposure")

        zd = 90.0 - statusDict['TSCS.EL']
        hdr.update("ZD-STR", str(zd),
                   comment="[degree] Zenith Distance at the start of exp.")
        hdr.update("ZD-END", str(zd),
                   comment="[degree] Zenith Distance at the end of exp.")
        seczd = 1.0 / math.cos(math.radians(zd))
        hdr.update("SECZ-STR", str(seczd),
                   comment="SEC(Zenith Distance) at the start of exposure")
        hdr.update("SECZ-END", str(statusDict['FITS.SBR.AIRMASS']),
                   comment="SEC(Zenith Distance) at the end of exposure")
        hdr.update("AIRMASS", statusDict['FITS.SBR.AIRMASS'],
                   comment="Average airmass during exposure")
        hdr.update("AZIMUTH", statusDict['FITS.SBR.AZIMUTH'],
                   comment="[degree] Azimuth of tel-pointing. 0:N->90:E")
        hdr.update("ALTITUDE", statusDict['FITS.SBR.ALTITUDE'],
                   comment="[degree] Altitude ang. of telescope pointing")

        hdr.update("GAIN", 1.0, comment="AD conversion factor (electron/ADU)")
        hdr.update("EXPTIME", (time_end - time_start),
                   comment="Total integration time of the frame (sec)")
        hdr.update("PROP-ID", statusDict['FITS.FLD.PROP-ID'],
                   comment="Proposal ID")
        hdr.update("OBSERVER", statusDict['FITS.FLD.OBSERVER'],
                   comment="Observer")
        hdr.update("OBSERVAT", "NAOJ", comment="Observatory")
        hdr.update("TELESCOP", "Subaru",
                   comment="Telescope/System which Inst. is attached")

        hdr.update("FRAMEID", frameid,
                   comment="Image sequential number")
        hdr.update("EXP-ID", frameid,
                   comment="ID of the exposure this data was taken")

        hdr.update("INSTRUME", "Fieldmonitor", comment="Name of instrument")
        hdr.update("OBJECT", statusDict['FITS.FLD.OBJECT'],
                   comment="Target Description")
        hdr.update("DATA-TYP", "Fieldmonitor",
                   comment="Type/Characteristics of this data")
        hdr.update("DETECTOR", "Fieldmonitor", comment="Name of the detector/CCD")

        hdr.update("OUT-HUM", statusDict['FITS.SBR.OUT_HUM'],
                   comment="Humidity measured outside of dome (\%)")
        hdr.update("OUT-TMP", statusDict['FITS.SBR.OUT_TMP'],
                   comment="Temperature measured outside of dome (K)")
        hdr.update("OUT-WND", statusDict['FITS.SBR.OUT_WND'],
                   comment="Wind velocity outside of dome (m/s)")
        hdr.update("OUT-PRS", statusDict['FITS.SBR.OUT_PRS'],
                   comment="Atmospheric pressure outside of dome (hpa)")
        hdr.update("ENVDIR", statusDict['TSCL.WINDD'],
                   comment="Wind direction outside of dome (deg)")
        hdr.update("E_CIRRUS", 0.0, comment="Cirrus coverage")
        hdr.update("E_CLOUD", 0.0, comment="Cloud coverage")

        hdr.update("EQUINOX", 2000.0, comment="Standard FK5 (years)")
        ra = statusDict['FITS.SBR.RA']
        dec = statusDict['FITS.SBR.DEC']
        equinox = float(statusDict['FITS.SBR.EQUINOX'])
        hdr.update("RA", ra, comment="Right ascension of telescope pointing")
        hdr.update("DEC", dec, comment="Declination of telescope pointing")
        ra_deg = fitsutils.hmsToDeg(ra)
        dec_deg = fitsutils.dmsToDeg(dec)
        ra_str, dec_str = fitsutils.getRaDecStrInEq2000(ra_deg, dec_deg, equinox)
        hdr.update("RA2000", ra_str,
                   comment="Right ascension of telescope pointing (J2000)")
        hdr.update("DEC2000", dec_str,
                   comment="Declination of telescope pointing (J2000)")

        hdr.update("CRVAL1", ra_deg,
                   comment="Physical value of the reference X")
        hdr.update("CRVAL2",  dec_deg,
                   comment="Physical value of the reference Y")
        hdr.update("CRPIX1",  self.crpix1,
                   comment="Reference pixel in X (pixel)")
        hdr.update("CRPIX2",  self.crpix2,
                   comment="Reference pixel in Y (pixel)")
        hdr.update("CDELT1", self.cdelt1,
                   comment="X Scale projected on detector (#/pix)")
        hdr.update("CDELT2", self.cdelt2,
                   comment="Y Scale projected on detector (#/pix)")
        hdr.update("CTYPE1", "RA---TAN", comment="Pixel coordinate system")
        hdr.update("CTYPE2", "DEC--TAN", comment="Pixel coordinate system")
        hdr.update("CUNIT1", "degree",
                   comment="Units used in both CRVAL1 and CDELT1")
        hdr.update("CUNIT2", "degree",
                   comment="Units used in both CRVAL2 and CDELT2")

        # Calculate position angle of telescope
        pa = fitsutils.calc_pa(statusDict['TSCS.EL'], statusDict['TSCS.AZ'])

        # Adjust for installation/orientation of camera relative to telescope
        pa += self.pa_offset

        # Calculate rotation matrix
        pc11, pc12, pc21, pc22 = fitsutils.calcPCs(pa, 1.0)
        hdr.update("PC001001", pc11, comment="Pixel Coordinate translation matrix")
        hdr.update("PC001002", pc12, comment="Pixel Coordinate translation matrix")
        hdr.update("PC002001", pc21, comment="Pixel Coordinate translation matrix")
        hdr.update("PC002002", pc22, comment="Pixel Coordinate translation matrix")
        hdr.update("LONGPOLE", 180.0,
                   comment="The North Pole of standard system (deg)")
        hdr.update("WCS-ORIG", "SUBARU Toolkit",
                   comment="The origin of the WCS value")
        hdr.update("RADECSYS", "FK5", comment="The equatorial coordinate system")
        hdr.update("CD1_1", fitsutils.calcCD(pc11, self.cdelt1),
                   comment="Pixel Coordinate translation matrix")
        hdr.update("CD1_2", fitsutils.calcCD(pc12, self.cdelt1),
                   comment="Pixel Coordinate translation matrix")
        hdr.update("CD2_1", fitsutils.calcCD(pc21, self.cdelt2),
                   comment="Pixel Coordinate translation matrix")
        hdr.update("CD2_2", fitsutils.calcCD(pc22, self.cdelt2),
                   comment="Pixel Coordinate translation matrix")


    def _snap(self, statusDict, 
              filename='test.fits', stacksize=6, waittime=10000, subinteg=10,
              integtime=5.0, coadd=1.0, pxtype='Int16'):
        """Snap an exposure.  Parameters:
        _statusDict_: dictionary full of necessary status for FITS header
        _obsDict_: dictionary full of necessary status for FITS header
        _frameid_: the file name (sans extension) that should be used.
        _stacksize_: the number of frames in the stack (- 1).
        _waittime_: the time to wait after starting a capture (in usec)
        _subinteg_: the number of frames to average for 1 exposure (/ 3)
        _integtime_: time to integrate over for each frame
        _coadd_: division factor to raise exposure level
        _pxtype_: data type to use for fits file pixels (Int16 or Float32)
        """

        #TODO: make thread safe

        pxtype = pxtype.capitalize()
        if not pxtype in ('Int16', 'Float32'):
            self.logger.error("Bad pxtype parameter: '%s'" % pxtype)
            return 1

        # Set additive buffer type.  Don't want to overflow.
        buftype = 'Float32'
        if pxtype == 'Int16':
            buftype = 'Int32'
        
        # Try to write out the file to disk
        name, ext = os.path.splitext(filename)
        if ext == '':
            ext = '.fits'

        fitsfile = self.param.fitsdir + '/' + name + ext
        if os.path.exists(fitsfile):
            self.logger.error("FITS file already exists: %s" % fitsfile)
            return 1
        
        self.logger.debug('Making FITS file shell.')
        # Make an array of the appropriate type and size, initialized to 0's
        pridata = numpy.zeros((self.height, self.width), pxtype)
        
        # Make the beginnings of a FITS file
        prihdu = pyfits.PrimaryHDU(pridata)
        hdulist = pyfits.HDUList([prihdu])

        # Start time of overall exposure
        self.logger.debug('Starting exposure.')
        primary_start = time.time()

        pribuf = numpy.zeros((self.height, self.width), buftype)

        # Collect the stack of 1..N-1 images.  The primary HDU will contain
        # the integration of all these frames.
        #
        for i in xrange(stacksize - 1):

            self.logger.debug("Starting exposure: frame %d" % (i+1))

            # C interface buffer is always Int32
            buffer = numpy.zeros((self.height, self.width), 'Int32')

            # Time of this secondary exposure
            numinteg = 0
            time_start = time.time()
            time_end = time_start + integtime

            # Perform high level integrations over the period
            while time.time() < time_end and (not self.ev_cancel.isSet()) \
                      and (not self.ev_quit.isSet()):
                # Capture data into this array.
                # Parameters are array, wait time and number of tight
                # integrations
                pycap.capture(buffer, waittime, subinteg)

                numinteg += 1

                # Seems to be necessary to let other threads run!
                time.sleep(0)

            # End time of this secondary exposure
            time_end = time.time()

            # Check if we've been asked to quit or cancel
            if self.ev_quit.isSet():
                return 1
            if self.ev_cancel.isSet():
                self.logger.error("CANCEL received--aborting exposure")
                self.ev_cancel.clear()
                return 1

            # integration/coadd adjustment
            buffer /= (float(numinteg) / coadd)

            self.logger.debug("Integrations: %d x %d x 3 = %d / %f" % \
                              (numinteg, subinteg, numinteg * subinteg * 3,
                               coadd))

            # Flip image horizontally
            buffer = buffer.take(self.flip_h, axis=1)

            # flat-field image
            if self.flatfield != None:
                # Get mean pixel value of data
                mean_px = buffer.mean()

                # Now divide buffer by flat field image
                buffer = buffer.astype('Float32')
                buffer /= self.flatfield

                # Now scale back to (near) original values
                if pxtype == 'Int16':
                    buffer *= mean_px

            # Coerce back to 16-bit int array
            secdata = buffer.astype(pxtype)

            # Add this data to image as secondary HDU
            hdu = pyfits.ImageHDU(secdata)

            # Update FITS keywords
            try:
                self._update_hdr(hdu.header, statusDict,
                                 time_start=time_start, time_end=time_end,
                                 frameid=filename)
            except Exception, e:
                self.logger.error('Error building FITS header: %s' % str(e))
                self.logger.error('statusDict=%s' % str(statusDict))
                return 1

            hdulist.append(hdu)

            # sum the individual frames into the primary buffer
            pribuf += secdata

        # Divide by stacksize to get the primary HDU data
        pridata += (pribuf / stacksize)

        # Update FITS keywords in primary HDU header
        try:
            self._update_hdr(prihdu.header, statusDict,
                             time_start=primary_start, time_end=time_end,
                             frameid=filename)
        except Exception, e:
            self.logger.error('Error building FITS header: %s' % str(e))
            self.logger.error('statusDict=%s' % str(statusDict))
            return 1

        try:
            self.logger.debug('End exposure; writing fits file (%s)' % \
                              fitsfile)
            hdulist.writeto(fitsfile)

        except OSError, e:
            self.logger.error("Can't write file: %s" % fitsfile)
            return 1

        # Update snap count
        self.param.fitscount += 1
        self.mystatus.count = self.param.fitscount

        return 0


    def _getstatus(self, statusDict):
        """Get status values corresponding to keys in the _statusDict_.
        """

        # Use "fast" status interface
        #self.ocs.getOCSstatus(statusDict)
        self.ocs.requestOCSstatus(statusDict)

        # This request is not logged over DAQ logs
        self.logger.debug("statusDict: %s" % str(statusDict))


    def _calc_obsinfo(self, statusDict):
        """Calculate status values for FITS.SBR.PROP-ID, FITS.SBR.OBSERVER
        and FITS.SBR.OBJECT if they are not already properly defined in
        _statusDict_.
        """

        if statusDict['FITS.FLD.PROP-ID'].startswith('#'):
            # Observers did NOT allocate FieldMonitor.  Instead, look
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
                obsalias = 'FITS.%3.3s.OBSERVER' % inscode
                statusDict2 = { propalias: '#', objalias: '#',
                                obsalias: '#' }

                # Now fetch that status set
                self._getstatus(statusDict2)

                # Substitute these values for the FLD versions
                statusDict['FITS.FLD.PROP-ID'] = statusDict2[propalias]
                statusDict['FITS.FLD.OBJECT']  = statusDict2[objalias]
                statusDict['FITS.FLD.OBSERVER']  = statusDict2[obsalias]

        # set default object and propid, if not set properly
        if statusDict['FITS.FLD.PROP-ID'].startswith('#'):
            statusDict['FITS.FLD.PROP-ID'] = 'o98023'
        if statusDict['FITS.FLD.OBJECT'].startswith('#'):
            statusDict['FITS.FLD.OBJECT'] = ''

    

    #######################################
    # INSTRUMENT COMMANDS
    #######################################

    def exp(self, motor='OFF', frameid=None, stacksize=None, waittime=None,
            subinteg=None, integtime=None, coadd=None, pxtype=None):
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
        res = self.snap(motor=motor, filename=frameid, stacksize=stacksize,
                        waittime=waittime, subinteg=subinteg,
                        integtime=integtime, coadd=coadd, pxtype=pxtype)
        if res != 0:
            self.logger.error("Snap failed.")
            return res

        fitsfile = self.param.fitsdir + '/' + frameid + '.fits'

        (res, errmsg) = self.archive(frameid, fitsfile)
        if res != 0:
            # <= Error message was logged in self.archive()
            return (res, errmsg)

        # Update status value
        self.mystatus.frame = frameid

        return 0


    def snap(self, motor='ON', filename='test.fits', stacksize=6,
             waittime=10000, subinteg=10, integtime=5.0, coadd=1.0,
             pxtype='Int16'):
        """Snap an exposure.  Parameters:
        _filename_: the file name that should be used.
        _stacksize_: the number of frames in the stack (- 1).
        _waittime_: the time to wait after starting a capture (in usec)
        _subinteg_: the number of frames to average for 1 exposure (/ 3)
        _integtime_: total integration time
        _coadd_: division factor to raise exposure level
        _pxtype_: data type to use for fits file pixels (Int16 or Float32)
        """

        #TODO: make thread safe

        # Request our status set "START_EXP"
        statusDict = self.statusset.START_EXP
        self._getstatus(statusDict)

        # Check that observer info are properly defined
        self._calc_obsinfo(statusDict)
        
        res = self._snap(statusDict,
                         filename=filename, stacksize=stacksize,
                         waittime=waittime, subinteg=subinteg,
                         integtime=integtime, coadd=coadd, pxtype=pxtype)

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
        try:
            self.ocs.exportStatus()
            return 0

        except CamError, e:
            return (1, str(e))


    def reqframes(self, num=1, type="A"):
        """Forced frame request.
        """
        framelist = self.ocs.getFrames(num, type)

        # This request is not logged over DAQ logs
        self.logger.info("framelist: %s" % str(framelist))

        return 0


    def autosnap(self, motor="OFF", interval=None, stacksize=None,
                 waittime=None, subinteg=None, integtime=None, coadd=None,
                 pxtype=None):
        """Turn on/off and configure auto generation of FITS files.
        """

        if interval != None:
            self.param.snap_interval = interval
            
        if stacksize != None:
            self.param.stacksize = stacksize
            
        if waittime != None:
            self.param.waittime = waittime
            
        if subinteg != None:
            self.param.subinteg = subinteg
            
        if integtime != None:
            self.param.integtime = integtime
            
        if coadd != None:
            self.param.coadd = coadd
            
        if pxtype != None:
            self.param.pxtype = pxtype
            
        if motor.upper() == 'ON':
            self.ev_auto.set()
            
        elif motor.upper() == 'OFF':
            self.ev_auto.clear()

        else:
            self.logger.error("bad parameter: motor=%s" % str(motor))
            return 1
            
        return 0


    def archive(self, frameid='NOP', fitspath='NOP'):
        """Convenience method for archiving a fits file.
        Try to archive _fitspath_ as _frameid_ using instrument interface.
        """

        self.logger.debug("Archiving frame: %s" % str(fitspath))
        try:
            self.ocs.archive_frame(frameid, fitspath)
            res = 0

        except CamError, e:
            errmsg = "Archive of '%s' failed: %s" % (fitspath, str(e))
            res = 1

        if res != 0:
            self.logger.error(errmsg)
        else:
            errmsg = "Archive of '%s' successful." % (fitspath)
            
        return (res, errmsg)


    def archive_list(self, listpath='NOP'):
        """Convenience method for archiving multiple fits files.
        _listpath_ is a list of frameid and FITS file path pairs.
        """
        self.logger.debug("Reading framelist: %s" % str(listpath))
        try:
            in_f = open(listpath, 'r')
            buf = in_f.read()
            in_f.close()
            
        except IOError, e:
            errmsg = "Can't open file '%s': %s" % (listpath, str(e))
            self.logger.error(errmsg)
            return (1, errmsg)

        lines = buf.strip().split('\n')
        for line in lines:
            try:
                (frameid, fitspath) = line.split(',')
            except IndexError:
                errmsg = "Line doesn't match expected format: '%s'" % (line)
                self.logger.error(errmsg)
                return (1, errmsg)

            frameid = frameid.strip()
            fitspath = fitspath.strip()
            
            (res, msg) = self.archive(frameid, fitspath)
            if res != 0:
                return (1, msg)

        return (res, "All transfers successful")


    def makeflat(self, outfile='flat.fits', indir='/data'):
        """Snap an exposure.  Parameters:
        _outfile_: name of a calibration file to write
        _indir_: directory containing a bunch of FITS images
        """

        self.logger.debug('Making flat-field calibration file.')

        buffer = numpy.zeros((self.height, self.width), 'Int32')

        count = 0

        # For each fits file in this directory:
        #   open it, and add the contents of all images to the buffer
        #   count each buffer
        for fitsfile in glob.glob(indir + '/*.fits'):
            fits_f = pyfits.open(fitsfile, 'readonly')

            for hdu in fits_f:
                buffer += hdu.data
                count += 1

            fits_f.close()

        # Make an array of the appropriate type and size, initialized to 0's
        pridata = numpy.zeros((self.height, self.width), 'Int16')
        pridata += (buffer / count)

        self.flatfield = pridata
        
        # Make the beginnings of a FITS file
        prihdu = pyfits.PrimaryHDU(pridata)
        hdulist = pyfits.HDUList([prihdu])

        # Try to write out the file to disk
        name, ext = os.path.splitext(outfile)
        if ext == '':
            ext = '.fits'

        fitsfile = self.param.fitsdir + '/' + name + ext
        try:
            self.logger.debug('End calibration; writing fits file (%s)' % \
                              fitsfile)
            hdulist.writeto(fitsfile)

        except OSError, e:
            self.logger.error("Can't write file: %s" % fitsfile)
            return 1

        return 0


    def setflat(self, flatfits='flat.fits'):
        # Open flat-fielding file
        try:
            flat_f = pyfits.open(flatfits, 'readonly')
            self.flatfield = flat_f[0].data
            flat_f.close()
            return 0
            
        except IOError, e:
            self.logger.error("Can't open flat file: %s" % flatfits)
            return 1
            

    def clearflat(self, dummy=None):
        self.flatfield = None
        return 0

        
    def setcount(self, count=0):
        self.param.fitscount = int(count)
        self.mystatus.count = self.param.fitscount

        self.putstatus()
        return 0

        
    def power_off(self, upstime=None):
        """
        This method is called when the summit has been running on UPS
        power for a while and power has not been restored.  Effect an
        orderly shutdown.  upstime will be given the floating point time
        of when the power went out.
        """
        res = 1
        try:
            self.logger.info("!!! POWERING DOWN !!!")
            #res = os.system('/usr/sbin/shutdown -h 60')

        except OSError, e:
            self.logger.error("Error issuing shutdown: %s" % str(e))

        self.stop()
            
        self.ocs.shutdown(res)

    
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

    #print "start: %f  cur: %f  stop: %f" % (start_time, cur_time, stop_time)
    return res


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


#END FLDMON.py

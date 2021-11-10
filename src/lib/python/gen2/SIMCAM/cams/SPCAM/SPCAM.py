
#
# SPCAM.py -- Suprime Cam personality for SIMCAM instrument simulator
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Tue Apr 15 12:10:29 HST 2008
#]
# Bruce Bon -- last edit 2007-05-05 10:49
#
"""This file implements a simulator for SOSS device dependent SPCAM
commands.
"""
import sys, time, os
import re, glob
import threading
import types

import Task
from SIMCAM import BASECAM, CamError, CamCommandError
import SIMCAM.cams.common as common
import astro.fitsutils as fitsutils
import Bunch


# Value to return for executing unimplemented command.
# 0: OK, non-zero: error
unimplemented_res = 0
OK_res = 0
BadParm_res = 101
BadMode_res = 202

class SPCAMError(CamError):
    pass

class SPCAM(BASECAM):

    def __init__(self, logger, env, ev_quit=None):

        self.logger = logger
        self.env = env
        # Convoluted but sure way of getting this module's directory
        self.mydir = os.path.split(sys.modules[__name__].__file__)[0]

        if not ev_quit:
            self.ev_quit = threading.Event()
        else:
            self.ev_quit = ev_quit

        self.ocs = None
        self.mystatus = None

        # Thread-safe bunch for storing parameters read/written
        # by threads executing in this object
        self.param = Bunch.threadSafeBunch()
        
        # Interval between status packets (secs)
        self.param.status_interval = 60

        # Mode instrument is in: 'obc' or 'suka' (local)
        self.mode = 'suka'

        # Possible set of filters
        self.filters = {
            }

        # Assign other instrument state variables to their defaults
        self.stateCcdInit         = False
        self.stateFilterInit      = False
        self.stateFilterInitPos   = False
        self.stateInit            = False
        self.stateMessiaInit      = False
        self.stateShutterInit     = False
        self.stateChosenFilter    = None    # Filter that is in place (not on stack)
        # Following set to defaults for SHUTTER DD command
        self.stateShutterMotor    = 'ON'
        self.stateShutterSelect   = None
        self.stateShutterDuration = None
        self.stateShutterTimer    = 'OFF'
        self.stateShutterOpenClose = 'CLOSE'

        # SPCAM pulls status in sets.  These are the known sets.
        self.statusset = Bunch.Bunch()
        self.statusset.PROPID = {'FITS.SBR.UT1-UTC': 0,
                                 'FITS.SUP.PROP-ID': 0,
                                 'FITS.SBR.TELESCOP': 0,
                                 'FITS.SUP.FOC-POS': 0,
                                 'FITS.SBR.ADC-TYPE': 0,
                                 'FITS.SUP.OBSERVER': 0,
                                 'FITS.SUP.OBS-ALOC': 0,
                                 'FITS.SBR.TELFOCUS': 0,
                                 }
        self.statusset.OBJECT = {'FITS.SBR.FOC-VAL': 0,
                                 'FITS.SUP.OBJECT': 0,
                                 'FITS.SBR.ALTITUDE': 0,
                                 'FITS.SBR.INST-PA': 0,
                                 'FITS.SBR.RA': 0,
                                 'FITS.SBR.DEC': 0,
                                 'FITS.SBR.DOM-WND': 0,
                                 'FITS.SBR.OUT-WND': 0,
                                 'FITS.SBR.DOM-TMP': 0,
                                 'FITS.SBR.OUT-TMP': 0,
                                 'FITS.SBR.DOM-HUM': 0,
                                 'FITS.SBR.OUT-HUM': 0,
                                 'FITS.SBR.DOM-PRS': 0,
                                 'FITS.SBR.OUT-PRS': 0,
                                 'FITS.SBR.WEATHER': 0,
                                 'FITS.SBR.SEEING': 0,
                                 'FITS.SBR.ZD': 0,
                                 'FITS.SBR.SECZ': 0,
                                 'FITS.SBR.AIRMASS': 0,
                                 'FITS.SBR.INSROT': 0,
                                 'FITS.SBR.ADC': 0,
                                 'FITS.SBR.EQUINOX': 0,
                                 'FITS.SUP.DATASET': 0,
                                 'FITS.SBR.AZIMUTH': 0,
                                 'FITS.SUP.OBS-MOD': 0,
                                 'FITS.SBR.M2-POS1': 0,
                                 'FITS.SBR.M2-POS2': 0,
                                 'FITS.SBR.M2-POS3': 0,
                                 'FITS.SBR.M2-ANG1': 0,
                                 'FITS.SBR.M2-ANG2': 0,
                                 'FITS.SBR.M2-ANG3': 0,
                                 'FITS.PFU.OFFSET-X': 0,
                                 'FITS.PFU.OFFSET-Y': 0,
                                 'FITS.PFU.OFFSET-Z': 0,
                                 'FITS.SBR.AG-PRBX': 0,
                                 'FITS.SBR.AG-PRBY': 0,
                                 }
        self.statusset.AIRMASS = {'FITS.SBR.ZD': 0,
                                  'FITS.SBR.SECZ': 0,
                                  'FITS.SBR.AIRMASS': 0,
                                  'FITS.SBR.INSROT': 0,
                                  'FITS.SBR.ADC': 0,
                                  'FITS.SBR.AUTOGUID': 0,
                                  }
        
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
        self.tag = 'SPCAM'
        self.shares = ['logger', 'ev_quit', 'threadPool']
        
        # Used to format status buffer (item lengths must match definitions
        # of status aliases on SOSS side in $OSS_SYSTEM/StatusAlias.pro)
        statfmt = "(status)2.2s%(time)-13.13s"

        # Register my status.
        self.mystatus = self.ocs.addStatusTable('SUPS0001',
                                                ['status', 'time'],
                                                formatStr=statfmt)
        
        # Establish initial status values
        self.mystatus.status = 'OK'
        self.mystatus.time = '000000'

        # Will be set to periodic status task
        self.statusTask = None


    def start(self, wait=True):
        super(SPCAM, self).start(wait=wait)
        
        self.logger.info("SPCAM STARTED.")
        # Start auto-generation of status task
        t = common.IntervalTask(self.status, 60.0)
        self.status_task = t
        t.init_and_start(self)


    def stop(self, wait=True):
        super(SPCAM, self).start(wait=wait)
        
        # Terminate status generation task
        if self.status_task != None:
            self.status_task.stop()

        self.status_task = None
        self.logger.info("SPCAM STOPPED.")

    #######################################
    # INTERNAL METHODS
    #######################################

    def change_mode(self, mode):
        if (mode != 'obc') and (mode != 'suka'):
            self.logger.error("Bad mode: '%s'" % mode)
            return BadMode_res
        else:
            self.mode = mode
            if mode == 'obc':
                # Request our status set "PROPID"
                statusDict = self.statusset.PROPID
                self.ocs.requestOCSstatus(statusDict)

                # Request our status set "OBJECT"
                statusDict = self.statusset.OBJECT
                self.ocs.requestOCSstatus(statusDict)
            return OK_res
                    
    #######################################
    # INSTRUMENT COMMANDS
    #######################################

    def abort(self, target=None):
        """Abort a command?
        """
        self.logger.info(
            "*** SPCAM:  command 'abort' not yet implemented, target=%s ***" % \
            `target`)
        res = unimplemented_res
        return res

    def alloc(self, dummy="DUMMY"):
        """Allocate the instrument for use.
        """
        self.logger.debug("*** SPCAM: changing to 'obc' mode ***")
        res = self.change_mode('obc')
        self.logger.info("*** SPCAM has been allocated ***")
        return res

    def archive(self, frame=None, name=None):
        self.logger.error("command 'archive' not yet implemented")
        res = unimplemented_res
        return res

    def archiveall(self, dummy=None):
        self.logger.info(
            "*** SPCAM:  command 'archiveall' not yet implemented ***")
        res = unimplemented_res
        return res

    def archivesome(self, nsend=None):
        self.logger.info(
       "*** SPCAM:  command 'archivesome' not yet implemented, nsend=%s ***" % \
            `nsend` )
        res = unimplemented_res
        return res

    def autosend(self, mode=None):
        self.logger.error("command 'autosend' not yet implemented")
        res = unimplemented_res
        return res

    def auxfilter(self, direction=None, motor=None, select=None):
        self.logger.error("command 'auxfilter' not yet implemented")
        res = unimplemented_res
        return res

    def bias(self, name=None, ow=None, object=None, bin=None,
             frame0=None, frame1=None, frame2=None, frame3=None, frame4=None,
             frame5=None, frame6=None, frame7=None, frame8=None, frame9=None):
        """Take a bias frame.
        """
        self.logger.info("*** SPCAM:  command 'bias' not yet implemented ***")
        self.logger.debug("   name=%s, ow=%s, object=%s, bin=%s" % \
            (`name`, `ow`, `object`, `bin`) ) 
        self.logger.debug("   frame0=%s, frame1=%s, frame2=%s, frame3=%s" % \
            (`frame0`, `frame1`, `frame2`, `frame3`) ) 
        #res = unimplemented_res
        #return res

        frameidlist = [frame0, frame1, frame2, frame3, frame4,
                       frame5, frame6, frame7, frame8, frame9]
        testfiles = ['bias000_test_si001s.fits',
                     'bias000_test_w4c5.fits',
                     'bias000_test_w93c2.fits',
                     'bias000_test_si002s.fits',
                     'bias000_test_w67c1.fits',
                     'bias000_test_w9c2.fits',
                     'bias000_test_si005s.fits',
                     'bias000_test_w6c1.fits',
                     'bias000_test_si006s.fits',
                     'bias000_test_w7c3.fits']

        framelist = []
        for frame_cnt in xrange(10):
            frameid = frameidlist[frame_cnt]
            testfile = testfiles[frame_cnt]

            fitspath = os.path.abspath('%s/spcam_data/%s' % (self.mydir, testfile))

            # Add it to framelist
            framelist.append((frameid, fitspath))

        self.logger.debug("done exposing...")
        
        # Add a task to delay and then archive_fits
        self.logger.info("Adding delay task with '%s'" % \
                         str(framelist))
        t = common.DelayedSendTask(self.ocs, 10.0, framelist)
        t.initialize(self)
        self.threadPool.addTask(t)
        return 0

    def callamp(self, filter=None, motor=None, select=None):
        self.logger.error("command 'callamp' not yet implemented")
        res = unimplemented_res
        return res

    def camera(self, binmode=None, exposure=None, frame=None, gain=None, mode=None, partmode=None):
        self.logger.error("command 'camera' not yet implemented")
        res = unimplemented_res
        return res

    def ccd(self, add=None, area1=None, area2=None, binning=None, chip=None, frame=None, header=None, mode=None, motor=None):
        self.logger.error("command 'ccd' not yet implemented")
        res = unimplemented_res
        return res

    def ccdinit(self, dummy=None):
        self.stateCcdInit = True
        self.logger.info("*** SPCAM:  CCD has been initialized ***")
        res = OK_res
        return res

    def ccdstage(self, motor=None, x=None, y=None, z=None):
        self.logger.info("*** SPCAM:  command 'ccdstage' not yet implemented ***")
        res = unimplemented_res
        return res

    def ccdtemp(self, ctemp=None, motor=None):
        self.logger.error("command 'ccdtemp' not yet implemented")
        res = unimplemented_res
        return res

    def dark(self, name=None, exp=None, ow=None, object=None, bin=None, 
             frame0=None, frame1=None, frame2=None, frame3=None, frame4=None,
             frame5=None, frame6=None, frame7=None, frame8=None, frame9=None):
        self.logger.info("*** SPCAM:  command 'dark' not yet implemented ***")
        self.logger.debug("   name=%s, exp=%s, ow=%s, object=%s, bin=%s" % \
            (`name`, `exp`, `ow`, `object`, `bin`) ) 
        self.logger.debug("   frame0=%s, frame1=%s, frame2=%s, frame3=%s" % \
            (`frame0`, `frame1`, `frame2`, `frame3`) ) 
        res = unimplemented_res
        return res


    def exp( self, name=None, exp=None, ow=None, object=None, typ=None, bin=None, 
             frame0=None, frame1=None, frame2=None, frame3=None, frame4=None,
             frame5=None, frame6=None, frame7=None, frame8=None, frame9=None):
        self.logger.info("*** SPCAM:  command 'exp' not yet implemented ***")
        self.logger.debug("   name=%s, exp=%s, ow=%s, object=%s, typ=%s, bin=%s" % \
            (`name`, `exp`, `ow`, `object`, `typ`, `bin`) ) 
        self.logger.debug("   frame0=%s, frame1=%s, frame2=%s, frame3=%s" % \
            (`frame0`, `frame1`, `frame2`, `frame3`) ) 
        res = unimplemented_res
        return res

        frameidlist = [frame0, frame1, frame2, frame3, frame4,
                       frame5, frame6, frame7, frame8, frame9]
        testfiles = ['bias000_test_si001s.fits',
                     'bias000_test_w4c5.fits',
                     'bias000_test_w93c2.fits',
                     'bias000_test_si002s.fits',
                     'bias000_test_w67c1.fits',
                     'bias000_test_w9c2.fits',
                     'bias000_test_si005s.fits',
                     'bias000_test_w6c1.fits',
                     'bias000_test_si006s.fits',
                     'bias000_test_w7c3.fits']

        framelist = []
        for frame_cnt in xrange(10):
            frameid = frameidlist[frame_cnt]
            testfile = testfiles[frame_cnt]

            fitspath = os.path.abspath('/home/gen2/Svn/lib/python/SOSS/SIMCAM/spcam_data/' + testfile)

            # Add it to framelist
            framelist.append((frameid, fitspath))

        self.logger.debug("done exposing...")
        
        # Add a task to delay and then archive_fits
        self.logger.info("Adding delay task with '%s'" % \
                         str(framelist))
        t = common.DelayedSendTask(self.ocs, 10.0, framelist)
        t.initialize(self)
        self.threadPool.addTask(t)
        return 0

    def hscexp(self, frame_spec=None, groupsof=5):

        testfiles = glob.glob('/%s/HSCsim/uncompressed/*.fits' % (os.environ['DATAHOME']))
        testfiles.sort()

        match = re.match(r'^(\w{3})(\w)(\d{8}):(\d{4})$', frame_spec)
        if not match:
            raise SPCAMError("Bad frame specification: '%s'" % str(frame_spec))

        inscode, frame_typ, frame_start, num_frames = match.groups()
        frame_start = int(frame_start)
        #num_frames  = int(num_frames)
        num_frames = 112

        framelist = []
        count = 0
        while count < num_frames:
            frameid = '%s%s%08d' % (inscode, frame_typ, frame_start+count)
            fitspath = testfiles[count]

            # Add it to framelist
            framelist.append((frameid, fitspath))
            count += 1

        self.logger.debug("Sending files in groups of %d..." % groupsof)
        count = 0
        start_time = time.time()
        while count < num_frames:
            if len(framelist) >= groupsof:
                sublist = framelist[:groupsof]
                framelist = framelist[groupsof:]
            else:
                sublist = framelist
                framelist = []
            count += len(sublist)
        
            try:
                self.ocs.archive_framelist(sublist)
            except Exception, e:
                raise CamCommandError("Got exception sending files: %s" % str(e))

        elapsed_time = time.time() - start_time
        self.logger.info("Elapsed send time: %.3f sec" % elapsed_time)
        return 0

    def filter1(self, direction=None, motor=None, select=None, tilt=None):
        self.logger.error("command 'filter1' not yet implemented")
        res = unimplemented_res
        return res

    def filter2(self, direction=None, motor=None, select=None):
        self.logger.error("command 'filter2' not yet implemented")
        res = unimplemented_res
        return res

    def filtercheck(self, filter="W-C-RC", cond="TRUE"):
        """Check that a filter is in place or not.
        """
        self.logger.info("*** SPCAM:  FilterCheck command received ***")
        self.logger.debug("   filter=%s, cond=%s" % (`filter`, `cond`) ) 
        # TEMP ?????
        return 0
    
        if not self.stateChosenFilter:
            # No filter in place, COND=FALSE
            if cond == "FALSE":
                return 0
            # No filter in place, COND=TRUE
            return 1
        
        if self.stateChosenFilter != filter:
            # Different filter in place, COND=FALSE
            if cond == "FALSE":
                return 0
            return 1

        # Current filter in place, COND=FALSE
        if cond == "FALSE":
            return 1
        return 0

    def filterinit(self, dummy=None):
        self.stateFilterInit = True
        self.logger.info("*** SPCAM:  Filter has been initialized ***")
        res = OK_res
        return res

    def filterinitpos(self, dummy=None):
        self.stateFilterInitPos  = True
        self.logger.info("*** SPCAM:  Filter position has been initialized ***")
        res = OK_res
        return res

    def filterrestore(self, filter="W-C-RC"):
        """Return a filter to the stack.
        """

        self.logger.info("*** SPCAM:  FilterRestore command received ***")
        self.logger.debug("   filter=%s" % `filter` ) 
        # TEMP ????
        return 0
    
        if not self.stateChosenFilter:
            self.logger.error("No filter in place!")
            return 1
        
        if self.stateChosenFilter != filter:
            self.logger.error("Filter '%s' is not in place!" % \
                              filter)
            return 1
        
        self.stateChosenFilter = None
        return 0

    def filterset(self, filter="W-C-RC"):
        """Set a filter from the stack into place.
        """

        self.logger.info("*** SPCAM:  FilterSet command received ***")
        self.logger.debug("   filter=%s" % `filter` ) 
        # TEMP ?????
        return 0
    
        if self.stateChosenFilter:
            self.logger.error("Already a filter in place: '%s'" % \
                              self.stateChosenFilter)
            return 1
        
        self.stateChosenFilter = filter
        return 0

    def fits_file(self, frame_no=None, motor=None):
        self.logger.error("command 'fits_file' not yet implemented")
        res = unimplemented_res

        time.sleep(15.0)
        return res

    def forcefiltername(self, filter=None):
        self.logger.error("command 'forcefiltername' not yet implemented")
        res = unimplemented_res
        return res

    def free(self, dummy="DUMMY"):
        """Deallocate the instrument and return to local control.
        """
        self.logger.debug("*** SPCAM: changing to 'suka' mode ***")
        res = self.change_mode('suka')
        self.logger.info("*** SPCAM has been freed ***")
        return res

    def grism(self, direction=None, motor=None, select=None):
        self.logger.error("command 'grism' not yet implemented")
        res = unimplemented_res
        return res

    def init(self, dummy=None):
        self.stateInit = True
        self.logger.info("*** SPCAM has been initialized ***")
        res = OK_res
        return res

    def master(self, dummy=None):
        self.logger.error("command 'master' not yet implemented")
        res = unimplemented_res
        return res

    def messiainit(self, dummy=None):
        self.stateMessiaInit = True
        self.logger.info("*** SPCAM:  Messia has been initialized ***")
        res = OK_res
        return res

    def mos(self, motor=None, position=None, select=None, tz=None):
        self.logger.error("command 'mos' not yet implemented")
        res = unimplemented_res
        return res

    def obcp_mode(self, mode=None, motor=None):
        self.logger.error("command 'obcp_mode' not yet implemented")
        res = unimplemented_res
        return res

    def observe_mode(self, command_permission=None, motor=None):
        self.logger.error("command 'observe_mode' not yet implemented")
        res = unimplemented_res
        return res

    def open(self, exp=None):
        self.logger.error("command 'open' not yet implemented")
        res = unimplemented_res
        return res

    def polarizer(self, angle=None, motor=None, select=None):
        self.logger.error("command 'polarizer' not yet implemented")
        res = unimplemented_res
        return res

    def read(self, name=None, ow=None, object=None, typ=None, bin=None, 
             frame0=None, frame1=None, frame2=None, frame3=None, frame4=None, 
             frame5=None, frame6=None, frame7=None, frame8=None, frame9=None):
        self.logger.info("*** SPCAM:  command 'read' not yet implemented ***")
        self.logger.info(
            "            name=%s, ow=%s, object=%s, typ=%s, bin=%s" % \
            (`name`, `ow`, `object`, `typ`, `bin`) )
        self.logger.info(
            "            frame0=%s, frame1=%s, frame2=%s, frame3=%s" % \
            (`frame0`, `frame1`, `frame2`, `frame3`) )
        res = unimplemented_res
        return res

    def readpartial(self, name=None, ow=None, object=None, typ=None, bin=None, 
            pos1=None, pos2=None, 
            frame0=None, frame1=None, frame2=None, frame3=None, frame4=None, 
            frame5=None, frame6=None, frame7=None, frame8=None, frame9=None):
        self.logger.error("command 'readpartial' not yet implemented")

        self.logger.info("*** SPCAM:  command 'readpartial' not yet implemented ***")
        self.logger.info(
            "            name=%s, ow=%s, object=%s, typ=%s, bin=%s" % \
            (`name`, `ow`, `object`, `typ`, `bin`) )
        self.logger.info(
            "            pos1=%s, pos2=%s" %  (`pos1`, `pos2`) )
        self.logger.info(
            "            frame0=%s, frame1=%s, frame2=%s, frame3=%s" % \
            (`frame0`, `frame1`, `frame2`, `frame3`) )
        res = unimplemented_res
        return res

    def schedulermode(self, frame=None, mode=None, motor=None):
        self.logger.error("command 'schedulermode' not yet implemented")
        res = unimplemented_res
        return res

    def shutter(self, duration=None, motor=None, select=None, timer=None):
        res = OK_res
        motorUpper = motor.upper()
        if  motorUpper == 'ON' or motorUpper == 'OFF':
            self.stateShutterMotor = motorUpper
        else: 
            self.logger.error("shutter: illegal value (%s) for motor" % \
                              motor )
            return BadParm_res

        selectUpper = select.upper()
        if  selectUpper == 'OPEN' or selectUpper == 'CLOSE':
            self.stateShutterSelect = selectUpper
        else: 
            self.logger.error("shutter: illegal value (%s) for select" % \
                              select )
            return BadParm_res

        timerUpper = timer.upper()
        if  timerUpper == 'ON' or timerUpper == 'OFF':
            self.stateShutterTimer = timerUpper
        else: 
            self.logger.error("shutter: illegal value (%s) for timer" % \
                              timer )
            return BadParm_res

        if  type(duration) != types.FloatType:
            self.logger.error("shutter: illegal type (%s) for duration" % \
                              type(duration) )
            return BadParm_res
        self.stateShutterDuration = duration

        self.logger.info("*** SPCAM:  Shutter parms have been set ***")
        self.logger.info(
            "            duration=%s, motor=%s, select=%s, timer=%s" %
            (`duration`, `motor`, `select`, `timer`) )
        res = OK_res
        return res

    def shutterclose(self, dummy=None):
        self.stateShutterOpenClose = 'CLOSE'
        self.logger.info("*** SPCAM:  Shutter has been closed ***")
        res = OK_res
        return res

    def shutterinit(self, dummy=None):
        self.stateShutterInit = True
        self.logger.info("*** SPCAM:  Shutter has been initialized ***")
        res = OK_res
        return res

    def shutteropen(self, dummy=None):
        self.stateShutterOpenClose = 'OPEN'
        self.logger.info("*** SPCAM:  Shutter has been opened ***")
        res = OK_res
        return res

    def shutter_open(self, dec=None, height=None, motor=None, ra=None,
                     width=None):
        self.logger.error("command 'shutter_open' not yet implemented")
        res = unimplemented_res
        return res

    def sleep(self, sleep_time=1):
        time.sleep(sleep_time)
        return OK_res

    def slit(self, motor=None, select=None):
        self.logger.info(
            "*** SPCAM:  slit commanded with motor=%s, select=%s ***" % \
            (`motor`, `select`) )
        self.logger.error("command 'slit' not yet implemented")
        res = unimplemented_res
        return res

    def status(self, target="ALL"):
        """Forced export of our status.
        """
        # self.logger.info(
        #     "*** SPCAM:  Forced status export command with target = %s ***" % \
        #     target )
        return self.ocs.exportStatus()

    def t1(self, binmode=None, exposure=None, gain=None, mode=None,
           partmode=None):
        self.logger.error("command 't1' not yet implemented")
        res = unimplemented_res
        return res

    def take(self, exp=None):
        """Take an image?
        """
        self.logger.info("*** SPCAM:  command 'take' not yet implemented, called with exp = %s ***" % `exp`)
        # Fake exposure time by sleeping.
        time.sleep(exp)
        res = OK_res
        return res

    def tcheck(self, dummy=None):
        self.logger.error("command 'tcheck' not yet implemented")
        res = unimplemented_res
        return res

    def test(self, lets=None):
        self.logger.error("command 'test' not yet implemented")
        res = unimplemented_res
        return res

    def vcheck(self, dummy=None):
        self.logger.error("command 'vcheck' not yet implemented")
        res = unimplemented_res
        return res

    def wait(self, exp=None):
        self.logger.info("*** SPCAM:  command 'wait' not yet implemented, called with exp = %s ***" % `exp`)
        res = unimplemented_res
        return res

    def waitreadout(self, dummy=None):
        """Wait til the CCD is done reading out.
        """
        self.logger.info("*** SPCAM:  command 'waitreadout' sleeps 5 seconds ***")
        time.sleep(5.0)
        res = OK_res
        return res

    def wipe(self, dummy=None):
        """Wipe the CCD.
        """
        self.logger.info("*** SPCAM:  command 'wipe' not yet implemented ***")
        res = unimplemented_res
        return res

    def wiper(self, mode=None):
        self.logger.error("command 'wiper' not yet implemented")
        res = unimplemented_res
        return res


#END SPCAM.py

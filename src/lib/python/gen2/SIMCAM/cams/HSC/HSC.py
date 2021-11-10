#
# HSC.py -- native HSC personality for SIMCAM instrument interface
#
#
"""This file implements the OCS interface for Hyper Suprime-Cam.
"""
import sys, os, time
import re
import threading

import Bunch
from SIMCAM import BASECAM, CamError, CamCommandError
import SIMCAM.cams.common as common


class HSCError(CamCommandError):
    pass

class HSC(BASECAM):

    def __init__(self, logger, env, ev_quit=None):

        super(HSC, self).__init__()
        
        self.logger = logger
        self.env = env
        # Convoluted but sure way of getting this module's directory
        self.mydir = os.path.split(sys.modules[__name__].__file__)[0]

        if not ev_quit:
            self.ev_quit = threading.Event()
        else:
            self.ev_quit = ev_quit

        # Holds our link to OCS delegate object
        self.ocs = None

        # We define our own modes that we report through status
        # to the OCS
        self.mode = 'default'

        # Thread-safe bunch for storing parameters read/written
        # by threads executing in this object
        self.param = Bunch.threadSafeBunch()
        
        # Interval between status packets (secs)
        self.param.status_interval = 10.0


    #######################################
    # INITIALIZATION
    #######################################

    def initialize(self, ocsint):
        '''Initialize instrument.  
        '''
        super(HSC, self).initialize(ocsint)
        self.logger.info('***** INITIALIZE CALLED *****')
        # Grab my handle to the OCS interface.
        self.ocs = ocsint

        # Get instrument configuration info
        self.obcpnum = self.ocs.get_obcpnum()
        self.insconfig = self.ocs.get_INSconfig()

        # Thread pool for autonomous tasks
        self.threadPool = self.ocs.threadPool

        # For task inheritance:
        self.tag = 'HSC'
        self.shares = ['logger', 'ev_quit', 'threadPool']
        
        # Used to format status buffer (item lengths must match definitions
        # of status aliases on Gen2 side in StatusAlias.pro)
        statfmt1 = "%(status)-8.8s,%(mode)-8.8s,%(count)8d;%(time)-15.15s"

        # Define other status formats here if you have more than one table...

        # Get our 3 letter instrument code and full instrument name
        self.inscode = self.insconfig.getCodeByNumber(self.obcpnum)
        self.insname = self.insconfig.getNameByNumber(self.obcpnum)

        # Figure out our status table name.
        tblName1 = ('%3.3sS%04.4d' % (self.inscode, 1))

        self.stattbl1 = self.ocs.addStatusTable(tblName1,
                                                ['status', 'mode', 'count',
                                                 'time'],
                                                formatStr=statfmt1)

        # Add other tables here if you have more than one table...
        
        # Establish initial status values
        self.stattbl1.setvals(status='ALIVE', mode='LOCAL', count=0)

        # Handles to periodic tasks
        self.status_task = None
        self.power_task = None

        # Lock for handling mutual exclusion
        self.lock = threading.RLock()


    def start(self, wait=True):
        super(HSC, self).start(wait=wait)
        
        self.logger.info('HSC STARTED.')

        # Start auto-generation of status task
        t = common.IntervalTask(self.putstatus,
                                self.param.status_interval)
        self.status_task = t
        t.init_and_start(self)

        # Start task to monitor summit power.  Call self.power_off
        # when we've been running on UPS power for 60 seconds
        t = common.PowerMonTask(self, self.power_off, upstime=60.0)
        #self.power_task = t
        #t.init_and_start(self)


    def stop(self, wait=True):
        super(HSC, self).stop(wait=wait)
        
        # Terminate status generation task
        if self.status_task != None:
            self.status_task.stop()

        self.status_task = None

        # Terminate power check task
        if self.power_task != None:
            self.power_task.stop()

        self.power_task = None

        self.logger.info("HSC STOPPED.")


    #######################################
    # INTERNAL METHODS
    #######################################

    def dispatchCommand(self, tag, cmdName, args, kwdargs):
        self.logger.debug("tag=%s cmdName=%s args=%s kwdargs=%s" % (
            tag, cmdName, str(args), str(kwdargs)))
        try:
            # Try to look up the named method
            method = getattr(self, cmdName)

        except AttributeError, e:
            result = "ERROR: No such method in subsystem: %s" % (cmdName)
            self.logger.error(result)
            raise CamCommandError(result)

        params = {}
        params.update(kwdargs)
        params['tag'] = tag

        return method(*args, **params)

    #######################################
    # INSTRUMENT COMMANDS
    #######################################


    def abort(self, target=None, tag=None):
        raise HSCError("command 'abort' not yet implemented")

    def alloc(self, dummy=None, tag=None):
        raise HSCError("command 'alloc' not yet implemented")

    def archive(self, frame=None, fpath=None, tag=None):
	"""Archive an existing file.  _frame_ is the frameid and 
        _fpath_ is the path to the frame on the OBCP (may be NOP).
        """

        self.logger.info("Archive called for '%s' at %s" % (
                frame, fpath))

	if not frame:
	    raise HSCError("No frame specified!")

	if not fpath:
            # Set this to your data area
	    fpath = os.path.join(self.env.INST_PATH, frame + '.fits')
            fpath = os.path.abspath(fpath)

        framelist = [(frame.upper(), fpath)]
        self.logger.info("Submitting framelist '%s'" % str(framelist))
        self.ocs.archive_framelist(framelist)

    def archiveall(self, dummy=None, tag=None):
        raise HSCError("command 'archiveall' not yet implemented")

    def archivesome(self, nsend=None, tag=None):
        raise HSCError("command 'archivesome' not yet implemented")

    def autosend(self, mode=None, tag=None):
        raise HSCError("command 'autosend' not yet implemented")

    def auxfilter(self, motor=None, select=None, direction=None, tag=None):
        raise HSCError("command 'auxfilter' not yet implemented")

    def bias(self, name=None, ow=None, object=None, bin=None, frame=None, tag=None):
        raise HSCError("command 'bias' not yet implemented")

    def callamp(self, motor=None, select=None, filter=None, tag=None):
        raise HSCError("command 'callamp' not yet implemented")

    def ccdinit(self, dummy=None, tag=None):
        raise HSCError("command 'ccdinit' not yet implemented")

    def ccdstage(self, motor=None, x=None, y=None, z=None, tag=None):
        raise HSCError("command 'ccdstage' not yet implemented")

    def ccdtemp(self, motor=None, ctemp=None, tag=None):
        raise HSCError("command 'ccdtemp' not yet implemented")

    def dark(self, name=None, exp=None, ow=None, object=None, bin=None, frame=None, tag=None):
        raise HSCError("command 'dark' not yet implemented")

    def exp(self, name=None, exp=None, ow=None, object=None, typ=None, bin=None, frame=None, tag=None):
        raise HSCError("command 'exp' not yet implemented")

    def filter2(self, motor=None, select=None, direction=None, tag=None):
        raise HSCError("command 'filter2' not yet implemented")

    def filtercheck(self, filter=None, cond=None, tag=None):
        raise HSCError("command 'filtercheck' not yet implemented")

    def filterinit(self, dummy=None, tag=None):
        raise HSCError("command 'filterinit' not yet implemented")

    def filterinitpos(self, dummy=None, tag=None):
        raise HSCError("command 'filterinitpos' not yet implemented")

    def filterrestore(self, filter=None, tag=None):
        raise HSCError("command 'filterrestore' not yet implemented")

    def filterset(self, filter=None, tag=None):
        raise HSCError("command 'filterset' not yet implemented")

    def fits_file(self, motor=None, frame_no=None, tag=None):
        raise HSCError("command 'fits_file' not yet implemented")

    def forcefiltername(self, filter=None, tag=None):
        raise HSCError("command 'forcefiltername' not yet implemented")

    def free(self, dummy=None, tag=None):
        raise HSCError("command 'free' not yet implemented")

    def getstatus(self, target="ALL", tag=None):
        """Forced import of our status using the normal status interface.
        """
	ra, dec = self.ocs.requestOCSstatusList2List(['STATS.RA',
                                                      'STATS.DEC'])

        self.logger.info("Status returned: ra=%s dec=%s" % (ra, dec))

    def grism(self, motor=None, select=None, direction=None, tag=None):
        raise HSCError("command 'grism' not yet implemented")

    def init(self, dummy=None, tag=None):
        raise HSCError("command 'init' not yet implemented")

    def master(self, dummy=None, tag=None):
        raise HSCError("command 'master' not yet implemented")

    def messiainit(self, dummy=None, tag=None):
        raise HSCError("command 'messiainit' not yet implemented")

    def mos(self, position=None, motor=None, select=None, tz=None, tag=None):
        raise HSCError("command 'mos' not yet implemented")

    def obcp_mode(self, motor=None, mode=None, tag=None):
        raise HSCError("command 'obcp_mode' not yet implemented")

    def observe_mode(self, motor=None, command_permission=None, tag=None):
        raise HSCError("command 'observe_mode' not yet implemented")

    def open(self, exp=None, tag=None):
        raise HSCError("command 'open' not yet implemented")

    def polarizer(self, motor=None, select=None, angle=None, tag=None):
        raise HSCError("command 'polarizer' not yet implemented")

    def power_off(self, upstime=None, tag=None):
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

    def putstatus(self, target="ALL", tag=None):
        """Forced export of our status.
        """
	# Bump our status send count and time
	self.stattbl1.count += 1
	self.stattbl1.time = time.strftime("%4Y%2m%2d %2H%2M%2S",
                                           time.localtime())

        self.ocs.exportStatus()

    def read(self, name=None, ow=None, object=None, typ=None, bin=None, frame=None, tag=None):
        raise HSCError("command 'read' not yet implemented")

    def readpartial(self, name=None, ow=None, object=None, typ=None, bin=None, pos1=None, pos2=None, frame=None, tag=None):
        raise HSCError("command 'readpartial' not yet implemented")

    def schedulermode(self, motor=None, mode=None, frame=None, tag=None):
        raise HSCError("command 'schedulermode' not yet implemented")

    def shutter(self, motor=None, select=None, duration=None, timer=None, tag=None):
        raise HSCError("command 'shutter' not yet implemented")

    def shutterclose(self, dummy=None, tag=None):
        raise HSCError("command 'shutterclose' not yet implemented")

    def shutterinit(self, dummy=None, tag=None):
        raise HSCError("command 'shutterinit' not yet implemented")

    def shutteropen(self, dummy=None, tag=None):
        raise HSCError("command 'shutteropen' not yet implemented")

    def shutter_open(self, motor=None, ra=None, dec=None, width=None, height=None, tag=None):
        raise HSCError("command 'shutter_open' not yet implemented")

    def sleep(self, sleep_time=0, tag=None):

        itime = float(sleep_time)

        # extend the tag to make a subtag
        subtag = '%s.1' % tag
        
        # Set up the association of the subtag in relation to the tag
        # This is used by integgui to set up the subcommand tracking
        # Use the subtag after this--DO NOT REPORT ON THE ORIGINAL TAG!
        self.ocs.setvals(tag, subpath=subtag)

        # Report on a subcommand.  Interesting tags are:
        # * Having the value of float (e.g. time.time()):
        #     task_start, task_end
        #     cmd_time, ack_time, end_time (for communicating systems)
        # * Having the value of str:
        #     cmd_str, task_error
        
        self.ocs.setvals(subtag, task_start=time.time(),
                         cmd_str='Sleep %f ...' % itime)
        
        self.logger.info("\nSleeping for %f sec..." % itime)
        while int(itime) > 0:
            self.ocs.setvals(subtag, cmd_str='Sleep %f ...' % itime)
            sleep_time = min(1.0, itime)
            time.sleep(sleep_time)
            itime -= 1.0

        self.ocs.setvals(subtag, cmd_str='Awake!')
        self.logger.info("Woke up refreshed!")
        self.ocs.setvals(subtag, task_end=time.time())


    def slit(self, select=None, motor=None, tag=None):
        raise HSCError("command 'slit' not yet implemented")

    def status(self, target=None, tag=None):
        raise HSCError("command 'status' not yet implemented")

    def t1(self, mode=None, binmode=None, partmode=None, gain=None, exposure=None, tag=None):
        raise HSCError("command 't1' not yet implemented")

    def take(self, exp=None, tag=None):
        raise HSCError("command 'take' not yet implemented")

    def tcheck(self, dummy=None, tag=None):
        raise HSCError("command 'tcheck' not yet implemented")

    def test(self, lets=None, tag=None):
        raise HSCError("command 'test' not yet implemented")

    def vcheck(self, dummy=None, tag=None):
        raise HSCError("command 'vcheck' not yet implemented")

    def wait(self, exp=None, tag=None):
        raise HSCError("command 'wait' not yet implemented")

    def waitreadout(self, dummy=None, tag=None):
        raise HSCError("command 'waitreadout' not yet implemented")

    def wipe(self, dummy=None, tag=None):
        raise HSCError("command 'wipe' not yet implemented")

    def wiper(self, mode=None, tag=None):
        raise HSCError("command 'wiper' not yet implemented")

    
#END HSC.py

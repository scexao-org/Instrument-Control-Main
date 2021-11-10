#
# GENERIC.py -- native GENERIC personality for SIMCAM instrument simulator
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Mar 30 09:30:31 HST 2011
#]
#
"""This file implements a simulator for a simulated instrument (GENERIC).
"""
import sys, os, time
import re
import threading

import pyfits

import Bunch
import Task
import astro.fitsutils as fitsutils
from SIMCAM import BASECAM, CamError, CamCommandError
import SIMCAM.cams.common as common


# Value to return for executing unimplemented command.
# 0: OK, non-zero: error
unimplemented_res = 0


class GENERICError(CamCommandError):
    pass

class GENERIC(BASECAM):

    def __init__(self, logger, env, ev_quit=None):

        super(GENERIC, self).__init__()
        
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
        super(GENERIC, self).initialize(ocsint)
        self.logger.info('***** INITIALIZE CALLED *****')
        # Grab my handle to the OCS interface.
        self.ocs = ocsint

        # Get instrument configuration info
        self.obcpnum = self.ocs.get_obcpnum()
        self.insconfig = self.ocs.get_INSconfig()

        # Thread pool for autonomous tasks
        self.threadPool = self.ocs.threadPool

        # For task inheritance:
        self.tag = 'simcam'
        self.shares = ['logger', 'ev_quit', 'threadPool']
        
        # Used to format status buffer (item lengths must match definitions
        # of status aliases on SOSS side in $OSS_SYSTEM/StatusAlias.pro)
        statfmt1 = "%(status)-8.8s,%(mode)-8.8s,%(count)8d;%(time)-15.15s"

        # Define other status formats here if you have more than one table...

        # Get our 3 letter instrument code and full instrument name
        self.inscode = self.insconfig.getCodeByNumber(self.obcpnum)
        self.insname = self.insconfig.getNameByNumber(self.obcpnum)

        # Figure out our status table name.
        if self.obcpnum == 9:
            # Special case for SUKA.  Grrrrr!
            tblName1 = 'OBCPD'
        else:
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
        super(GENERIC, self).start(wait=wait)
        
        self.logger.info('GENERIC STARTED.')

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
        super(GENERIC, self).stop(wait=wait)
        
        # Terminate status generation task
        if self.status_task != None:
            self.status_task.stop()

        self.status_task = None

        # Terminate power check task
        if self.power_task != None:
            self.power_task.stop()

        self.power_task = None

        self.logger.info("GENERIC STOPPED.")


    #######################################
    # INTERNAL METHODS
    #######################################

    def dispatchCommand(self, tag, cmdName, args, kwdargs):
        self.logger.debug("tag=%s cmdName=%s args=%s kwdargs=%s" % (
            tag, cmdName, str(args), str(kwdargs)))

        params = {}
        params.update(kwdargs)
        params['tag'] = tag
        
        try:
            # Try to look up the named method
            method = getattr(self, cmdName)

        except AttributeError, e:
            result = "ERROR: No such method in subsystem: %s" % (cmdName)
            self.logger.error(result)
            raise CamCommandError(result)

        return method(*args, **params)

    #######################################
    # INSTRUMENT COMMANDS
    #######################################

    def sleep(self, tag=None, sleep_time=0):

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


    def obcp_mode(self, motor='OFF', mode=None, tag=None):
	"""One of the commands that are in the SOSSALL.cd
        """
        self.mode = mode


    def get_dss(self, frame_no=None, ra=None, dec=None,
                width=10, height=10, tag=None):

        statusDict = {
            'FITS.SBR.RA': 0,
            'FITS.SBR.DEC': 0,
            'FITS.SUK.PROP-ID': 0,
            'FITS.SUK.OBSERVER': 0,
            #'FITS.SUK.OBJECT': 0,
            }
        try:
            res = self.ocs.requestOCSstatus(statusDict)
            self.logger.debug("Status returned: %s" % (str(statusDict)))

        except GENERICError, e:
            return (1, "Failed to fetch status: %s" % (str(e)))
        
        #cgi_str = "http://dbs1:30000/dss1_subaru?ra=%(ra)s&dec=%(dec)s&mime-type=application/x-fits&x=%(x)s&y=%(y)s"
        cgi_str = "http://archive.eso.org/dss/dss?ra=%(ra)s&dec=%(dec)s&x=%(x)s&y=%(y)s&mime-type=application/x-fits"

        if not ra:
            ra = statusDict['FITS.SBR.RA']
        if not dec:
            dec = statusDict['FITS.SBR.DEC']

        params = { 'ra': ra, 'dec': dec, 'x': str(width), 'y': str(height) }

        req_str = cgi_str % params

        filename = '/tmp/%s.fits' % frame_no

        cmd_str = "wget --tries=5 -T 60 -O %s '%s'" % (filename, req_str)

        self.logger.info("request is: %s" % req_str)
        res = os.system(cmd_str)

        if res != 0:
            return (1, "Failed to fetch DSS file: res=%d" % (
                res))

        try:
            py_f = pyfits.open(filename, 'update')
            #py_f = pyfits.open(filename)

            self.logger.info("verifying pass #1")
            hdulist = py_f[0:]
            #hdulist.verify()

            hdu = py_f[0]
            updDict = {'FRAMEID': frame_no,
                       'EXP-ID': frame_no,
                       'PROP-ID': statusDict['FITS.SUK.PROP-ID'],
                       'OBSERVER': statusDict['FITS.SUK.OBSERVER'],
                       #'OBJECT': statusDict['FITS.SUK.OBJECT'],
                       'OBSERVAT': 'NAOJ',
                       'TELESCOP': 'Subaru',
                       'INSTRUME': 'SUKA',
                       }

            self.logger.info("updating header")
            for key, val in updDict.items():
                hdu.header.update(key, val)

            self.logger.info("verifying pass #2")
            hdulist = py_f[0:]
            #hdulist.verify()
            self.logger.info("flushing")
            py_f.flush(output_verify='ignore')
            self.logger.info("closing")
            py_f.close(output_verify='ignore')
        
        except Exception, e:
            return (1, "Failed to open/update returned DSS file: %s" % (
                str(e)))

        try:
            self.logger.debug("archiving")
            self.ocs.archive_frame(frame_no, filename, 
                                   transfermethod='scp')

        except Exception as e:
            raise GENERICError("Failed to transfer file '%s': %s" % (
                filename, str(e)))
            

    def fits_file(self, motor='OFF', frame_no=None, template=None, delay=0,
                  tag=None):
	"""One of the commands that are in the SOSSALL.cd.
        """

        self.logger.info("fits_file called...")

	if not frame_no:
	    return 1

        # TODO: make this return multiple fits files
	if ':' in frame_no:
	    (frame_no, num_frames) = frame_no.split(':')
	    num_frames = int(num_frames)
        else:
            num_frames = 1

        # Check frame_no
        match = re.match('^(\w{3})(\w)(\d{8})$', frame_no)
        if not match:
            raise GENERICError("Error in frame_no: '%s'" % frame_no)

	inst_code = match.group(1)
	frame_type = match.group(2)
        # Convert number to an integer
        try:
            frame_cnt = int(match.group(3))
        except ValueError, e:
            raise GENERICError("Error in frame_no: '%s'" % frame_no)

        statusDict = {
            'FITS.SUK.PROP-ID': 'None',
            'FITS.SUK.OBSERVER': 'None',
            'FITS.SUK.OBJECT': 'None',
            }
        try:
            res = self.ocs.requestOCSstatus(statusDict)
            self.logger.debug("Status returned: %s" % (str(statusDict)))

        except GENERICError, e:
            return (1, "Failed to fetch status: %s" % (str(e)))
        
        # Iterate over number of frames, creating fits files
        frame_end = frame_cnt + num_frames
        framelist = []
        
        while frame_cnt < frame_end:
            # Construct frame_no and fits file
            frame_no = '%3.3s%1.1s%08.8d' % (inst_code, frame_type, frame_cnt)
            templfile = os.path.abspath(template)
            if not os.path.exists(templfile):
                raise GENERICError("File does not exist: %s" % (fitsfile))

            fits_f = pyfits.open(templfile)
            
            hdu = fits_f[0]
            updDict = {'FRAMEID': frame_no,
                       'EXP-ID': frame_no,
                       'PROP-ID': statusDict['FITS.SUK.PROP-ID'],
                       'OBSERVER': statusDict['FITS.SUK.OBSERVER'],
                       'OBJECT': statusDict['FITS.SUK.OBJECT'],
                       'OBSERVAT': 'NAOJ',
                       'TELESCOP': 'Subaru',
                       'INSTRUME': 'SUKA',
                       }

            self.logger.info("updating header")
            for key, val in updDict.items():
                hdu.header.update(key, val)

            fitsfile = '/tmp/%s.fits' % frame_no
            try:
                os.remove(fitsfile)
            except OSError:
                pass
            fits_f.writeto(fitsfile, output_verify='ignore')
            fits_f.close()

            # Add it to framelist
            framelist.append((frame_no, fitsfile))

            frame_cnt += 1

        # self.logger.debug("done exposing...")
        
        # If there was a non-negligible delay specified, then queue up
        # a task for later archiving of the file and terminate this command.
        if delay:
            if type(delay) == type(""):
                delay = float(delay)
            if delay > 0.1:
                # Add a task to delay and then archive_framelist
                self.logger.info("Adding delay task with '%s'" % \
                                 str(framelist))
                t = common.DelayedSendTask(self.ocs, delay, framelist)
                t.initialize(self)
                self.threadPool.addTask(t)
                return 0

        # If no delay specified, then just try to archive the file
        # before terminating the command.
        self.logger.info("Submitting framelist '%s'" % str(framelist))
        self.ocs.archive_framelist(framelist)


#     def copy_file(self, motor='OFF', frame_no=None):
# 	"""One of the commands that are in the SOSSALL.cd.
#         """

#         self.logger.info("fits_file called...")

# 	if not frame_no:
#             raise GENERICError("No frame_no specified!")

#         # TODO: make this return multiple fits files
# 	if ':' in frame_no:
# 	    (frame_no, num_frames) = frame_no.split(':')
# 	    num_frames = int(num_frames)
#         else:
#             num_frames = 1

#         # Check frame_no
#         match = re.match('^(\w{3})(\w)(\d{8})$', frame_no)
#         if not match:
#             raise GENERICError("Error in frame_no: '%s'" % frame_no)

# 	inst_code = match.group(1)
# 	frame_type = match.group(2)
#         # Convert number to an integer
#         try:
#             frame_cnt = int(match.group(3))
#         except ValueError, e:
#             raise GENERICError("Error in frame_no: '%s'" % frame_no)

#         # Iterate over number of frames, creating fits files
#         frame_end = frame_cnt + num_frames
#         framelist = []
        
#         while frame_cnt < frame_end:
#             # Construct frame_no and fits file
#             frame_no = '%3.3s%1.1s%08.8d' % (inst_code, frame_type, frame_cnt)
#             #fitsfile = '%s/%s.fits' % (self.env.INST_PATH, frame_no)
#             fitsfile = '%s/%s.fits' % ("/tmp", frame_no)

#             # take exposure
#             hdrkwds = { #'prop-id': self.env.proposal,
#                 'frameid': frame_no,
#                 'obcpmode': self.mode,
#                 }
# 	    try:
# 		os.system('cp %s/data/SUKA-4M.fits %s' % (self.mydir,
#                                                           fitsfile))
# 	    except OSError, e:
# 		raise GENERICError("Error making FITS file: %s" % str(e))

#             # Add it to framelist
#             framelist.append((frame_no, fitsfile))

#             frame_cnt += 1

#         self.logger.debug("done exposing...")
        
#         # If there was a non-negligible delay specified, then queue up
#         # a task for later archiving of the file and terminate this command.
#         if delay:
#             if type(delay) == type(""):
#                 delay = float(delay)
#             if delay > 0.1:
#                 # Add a task to delay and then archive_framelist
#                 self.logger.info("Adding delay task with '%s'" % \
#                                  str(framelist))
#                 t = common.DelayedSendTask(self.ocs, delay, framelist)
#                 t.initialize(self)
#                 self.threadPool.addTask(t)
#                 return (0, "OK")

#         # If no delay specified, then just try to archive the file
#         # before terminating the command.
#         self.logger.info("Submitting framelist '%s'" % str(framelist))
#         self.ocs.archive_framelist(framelist)


    def putstatus(self, target="ALL"):
        """Forced export of our status.
        """
	# Bump our status send count and time
	self.stattbl1.count += 1
	self.stattbl1.time = time.strftime("%4Y%2m%2d %2H%2M%2S",
                                           time.localtime())

        self.ocs.exportStatus()


    def schedulermode(self, motor='OFF', mode='OBCP', frame='NOP',
                      qframe='NOP'):
        """This is called by SOSS when through mode is initiated.
        """
        pass


    def getstatus(self, target="ALL"):
        """Forced import of our status using the normal status interface.
        """
	ra, dec, focusinfo, focusinfo2 = self.ocs.requestOCSstatusList2List(['STATS.RA',
                                                      'STATS.DEC',
                                                      'TSCV.FOCUSINFO',
                                                      'TSCV.FOCUSINFO2'])

        self.logger.info("Status returned: ra=%s dec=%s focusinfo=%s focusinfo2=%s" % (ra, dec, focusinfo, focusinfo2))


    def getstatus2(self, target="ALL"):
        """Forced import of our status using the 'fast' status interface.
        """
	ra, dec = self.ocs.getOCSstatusList2List(['STATS.RA',
                                                  'STATS.DEC'])

        self.logger.info("Status returned: ra=%s dec=%s" % (ra, dec))


    def reqframes(self, num=1, type="A"):
        """Forced frame request.
        """
        framelist = self.ocs.getFrames(num, type)

        # This request is not logged over DAQ logs
        self.logger.info("framelist: %s" % str(framelist))


    def kablooie(self, motor='OFF'):
	"""Generate an exception no matter what.
        """
        raise GENERICError("KA-BLOOIE!!!")


    def defaultCommand(self, *args, **kwdargs):
        """This method is called if there is no matching method for the
        command defined.
        """

        # If defaultCommand is called, the cmdName is pushed back on the
        # argument tuple as the first arg
        cmdName = args[0]
        self.logger.info("Called with command '%s', params=%s" % (cmdName,
                                                                  str(kwdargs)))

        res = unimplemented_res
        self.logger.info("Result is %d\n" % res)

	return res


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

    
#END GENERIC.py

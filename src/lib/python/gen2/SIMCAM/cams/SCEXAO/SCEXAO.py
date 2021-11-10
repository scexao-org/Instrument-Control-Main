#
# SCEXAO.py -- native SCEXAO personality for SIMCAM instrument interface
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Dec 29 17:31:45 HST 2010
#]
#
"""This file implements the OCS interface for (SCEXAO).
"""
import sys, os, time
import threading

import Bunch
import Task
from SIMCAM import BASECAM, CamError, CamCommandError
import SIMCAM.cams.common as common


# Value to return for executing unimplemented command.
# 0: OK, non-zero: error
unimplemented_res = 1

dummyTag = 'foo.1'

class SCEXAOError(CamCommandError):
    pass

class SCEXAO(BASECAM):

    def __init__(self, logger, env, ev_quit=None):

        super(SCEXAO, self).__init__()
        
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

        # Interval between status fetches (secs)
        self.param.pointing_fetch_interval = 60.0


    #######################################
    # INITIALIZATION
    #######################################

    def initialize(self, ocsint):
        '''Initialize instrument.  
        '''
        super(SCEXAO, self).initialize(ocsint)
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
        self.fetching_task = None

        # Lock for handling mutual exclusion
        self.lock = threading.RLock()


    def start(self, wait=True):
        super(SCEXAO, self).start(wait=wait)
        
        self.logger.info('SCEXAO STARTED.')

        # Start auto-generation of status task
        t = common.IntervalTask(self.putstatus,
                                self.param.status_interval)
        self.status_task = t
        t.init_and_start(self)

        # Start task to fetching pointing at intervals
        t = common.IntervalTask(self.getstatus,
                                self.param.pointing_fetch_interval)
        self.fetching_task = t
        t.init_and_start(self)



    def stop(self, wait=True):
        super(SCEXAO, self).stop(wait=wait)
        
        # Terminate status generation task
        if self.status_task != None:
            self.status_task.stop()
        if self.fetching_task != None:
            self.fetching_task.stop()

        self.status_task = None
        self.fetching_task = None

        self.logger.info("SCEXAO STOPPED.")


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

        except Exception, e:
            result = "ERROR invoking command '%s': %s" % (cmdName, str(e))
            self.logger.error(result)
            raise CamCommandError(result)

        params = {}
        params.update(kwdargs)
        params['tag'] = tag

        return method(*args, **params)

    #######################################
    # INSTRUMENT COMMANDS
    #######################################

    def sleep(self, sleep_time=0, tag=dummyTag):

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


    def putstatus(self, target="ALL", tag=dummyTag):
        """Forced export of our status.
        """
	# Bump our status send count and time
	self.stattbl1.count += 1
	self.stattbl1.time = time.strftime("%4Y%2m%2d %2H%2M%2S",
                                           time.localtime())

        self.ocs.exportStatus()


    def getstatus(self, target="ALL", tag=dummyTag):
        """Forced import of our status using the normal status interface.
        """
        statusDict = {
            'FITS.SBR.RA': 0,
            'FITS.SBR.DEC': 0,
            #'FITS.XAO.PROP-ID': 0,
            #'FITS.XAO.OBSERVER': 0,
            #'FITS.XAO.OBJECT': 0,
            'STATS.RA': 0,
            'STATS.DEC': 0,
            }

        try:
            res = self.ocs.requestOCSstatus(statusDict)
            self.logger.debug("Status returned: %s" % (str(statusDict)))

        except SCEXAOError, e:
            return (1, "Failed to fetch status: %s" % (str(e)))
        
        self.logger.info("Status returned: %s" % (str(statusDict)))


#END SCEXAO.py

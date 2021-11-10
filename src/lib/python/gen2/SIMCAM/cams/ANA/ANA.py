#
# ANA.py -- implements SOSS ANA device dependant commands
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Tue Apr 15 12:10:29 HST 2008
#]
#
"""This file implements SOSS ANA device dependant commands (ANA).

Example:

./simcam.py --cam=ANA --loglevel=0 --stderr --paradir=PARA/ANA --obcpnum=99 \
  --interfaces=cmd,sdst --daqhost=mobs --monunit=2
"""
import sys, os, time
import threading

import Bunch
import Task
from SIMCAM import BASECAM
import SIMCAM.cams.common as common


class ANAError(Exception):
    pass

class ANA(BASECAM):

    def __init__(self, logger, env, ev_quit=None):

        super(ANA, self).__init__()
        
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
        self.param.status_interval = 10


    #######################################
    # INITIALIZATION
    #######################################

    def initialize(self, ocsint):
        '''Initialize instrument.  
        '''
        super(ANA, self).initialize(ocsint)

        self.logger.info('***** INITIALIZE CALLED *****')
        # Grab my handle to the OCS interface.
        self.ocs = ocsint

        # Thread pool for autonomous tasks
        self.threadPool = self.ocs.threadPool
        
        # For task inheritance:
        self.tag = 'ana'
        self.shares = ['logger', 'ev_quit', 'threadPool']
        
        # Used to format status buffer (item lengths must match definitions
        # of status aliases on SOSS side in $OSS_SYSTEM/StatusAlias.pro)
        statfmt = "%(status)-8.8s,%(queuelen)8d,%(command)-64.64s;%(padding)s"

        # Register my status.
        self.mystatus = self.ocs.addStatusTable('ANAD',
                                                ['status', 'queuelen',
						 'command', 'padding'],
                                                formatStr=statfmt)
        
        # Establish initial status values
        self.mystatus.status = 'ALIVE'
        self.mystatus.queuelen = 0
        self.mystatus.command = ''
        self.mystatus.padding = (' '*164)

        # Will be set to periodic status task
        self.status_task = None


    def start(self, wait=True):
        super(ANA, self).start(wait=wait)
        
        self.logger.info('***** START CALLED *****')
        # Start auto-generation of status task
        t = common.IntervalTask(self.putstatus, 60.0)
        self.status_task = t
        t.init_and_start(self)


    def stop(self, wait=True):
        super(ANA, self).stop(wait=wait)
        
        # Terminate status generation task
        if self.status_task != None:
            self.status_task.stop()

        self.status_task = None

        self.logger.info("ANA STOPPED.")


    #######################################
    # INTERNAL METHODS
    #######################################

    #######################################
    # INSTRUMENT COMMANDS
    #######################################

    def confirmation(self, instrument_name=None, title=None, dialog=None):
	return 0


    def execute_program(self, command=None, parameter=None):

        self.mystatus.command = 'EXECUTE_PROGRAM'
        self.putstatus()

        # run command and return exit code
        #res = os.system("%s %s" % (command, parameter))
        res = 0
        
        self.mystatus.command = ''
        self.putstatus()

	return res


    def userinput(self, instrument_name=None, title=None,
                  item1=None, item2=None, item3=None, item4=None, item5=None,
                  item6=None, item7=None, item8=None, item9=None,
                  default_item1=None, default_item2=None, default_item3=None,
                  default_item4=None, default_item5=None, default_item6=None,
                  default_item7=None, default_item8=None, default_item9=None):

        self.mystatus.command = 'USERINPUT'
        self.putstatus()

        # TODO: do user input
        
        self.mystatus.command = ''
        self.putstatus()

	return 0


    def putstatus(self, target="ALL"):
        """Forced export of our status.
        """
        res = self.ocs.exportStatus()

	return res


    def getstatus2(self, target="ALL"):
        """Forced import of our status using the 'fast' status interface.
        """
	statusDict = {'STATS.RA': None, 'STATS.DEC': None}

        self.ocs.getOCSstatus(statusDict)
        # This request is not logged over DAQ logs
        self.logger.info("statusDict1: %s" % str(statusDict))

        return 0


#END ANA.py

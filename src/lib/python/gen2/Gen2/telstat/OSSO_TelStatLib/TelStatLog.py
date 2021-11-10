# TelStatLog.py -- Bruce Bon -- 2008-08-26

# Log messages to a file

######################################################################
################   import needed modules   ###########################
######################################################################

import os
import time
import logging 
from logging import handlers

import StatusDictionary
import TelStat_cfg

######################################################################
################   declare logging function   ########################
######################################################################
telStatLog_firstTime = True
telStatLog_logger = None
telStatLog_dict = {}

def TelStatLog( ID, message, alwaysOutput = False ):
    """Open log file, append message to it, then close it."""
    global telStatLog_firstTime, telStatLog_logger, telStatLog_dict

    # Get current time for from the status dictionary message tagging 
    #       and log message suppression
    curTime = StatusDictionary.StatusDictionary['TELSTAT.UNIXTIME']
    t = curTime.value()             # may be None
    if  t == None:          # no time available in StatusDictionary
        t = time.time()

    # Make sure I haven't printed this same message in the last 10 minutes
    if  not alwaysOutput and telStatLog_dict.has_key( ID ):
        if  telStatLog_dict[ ID ] + 600.0 > t:
            return      # don't repeat message for 600 seconds
    telStatLog_dict[ ID ] = t

    # If the first time, set up a logger to manage the log files
    if  telStatLog_firstTime:
        telStatLog_firstTime = False

        # Set umask for log, and save old one for restore later
        umaskSave = os.umask( 022 )

        # "loggers are never instantiated directly but
        #  always through getlogger
        telStatLog_logger = logging.getLogger("TelStatLog")

        # Set logger threshold
        telStatLog_logger.setLevel(0)

        # Setup rotating logfile handler, rfh
        rfh = handlers.RotatingFileHandler(
            TelStat_cfg.TELSTAT_LOG_PATH, 'a', 20480, 9)

        # Add handler, rfh to our logger
        telStatLog_logger.addHandler(rfh)

        # Restore umask
        os.umask( umaskSave )

    # Write to the log file and return
    timeTuple  = time.localtime(t)
    timeString = time.strftime( '%Y-%m-%d %H:%M:%S', timeTuple )
    telStatLog_logger.warning("%s: %s", timeString, message)

    return


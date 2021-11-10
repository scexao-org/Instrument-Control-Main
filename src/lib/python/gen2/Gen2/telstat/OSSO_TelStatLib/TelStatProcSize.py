# TelStatProcSize.py -- Bruce Bon -- 2008-04-01
# Display process size

######################################################################
################   import needed modules   ###########################
######################################################################

import os
import re

import StatusDictionary
import TelStatLog
import TelStat_cfg
import OSSC_screenPrintConversions

######################################################################
################   assign needed globals   ###########################
######################################################################

MyPID      = os.getpid()
MyUname    = os.uname()[0]
MyProcInfo = '/proc/' + `MyPID` + '/statm'

prevPsSize = 0
curPsSize  = 0
prevTime   = 0
iterCount  = 0

FirstAtomPattern = re.compile( '(.+?) ' )
#? PsSzAtomPattern  = re.compile( '.{41}\s+(.+?) ' )

TelStatProcessSizeMessage      = TelStat_cfg.TSPSInfoBase
TelStatProcessSizeWarnMessage1 = TelStat_cfg.TSPSWarnBase
TelStatProcessSizeWarnMessage2 = TelStat_cfg.TSPSWarnBase+1

######################################################################
################   declare function(s)   #############################
######################################################################

def procSize( label, minPeriod=0, diffMin=0 ):
    """Log a message with the current process size.  If minPeriod > 0, 
       then don't log until minPeriod passes since last log.
       If the size difference is less than diffMin, then don't log."""
    global prevPsSize, curPsSize, prevTime

    t = StatusDictionary.StatusDictionary['TELSTAT.UNIXTIME'].value() # sec
    if  t == None:
        t = 0
    #? print 't = %s, prevTime = %s, minPeriod = %s' % (`t`, `prevTime`, `minPeriod`)
    #? return
    if  (minPeriod > 0) and (prevTime + minPeriod > t):
        return

    if  MyUname == 'Linux':
        fd = open( MyProcInfo, 'r' )
        inLine = fd.readline()
        fd.close
        atm = FirstAtomPattern.match( inLine ).group(1)
        curPsSize = long( atm )
    elif  MyUname == 'SunOS':
        psCmd = 'ps -lp ' + `MyPID`
        # print 'psCmd = "%s"' % psCmd
        try:
            pfd = os.popen( psCmd )
            inLine = pfd.readline()     # first line is header
            inLine = pfd.readline()
            pfd.close
            atm = inLine.split()[9]
        except Exception, value:
            curPsSize = prevPsSize
            msg = "(%s): At update cycle %4d, error getting TelStat process size: %s" %\
                (label, OSSC_screenPrintConversions.OSPC_IterCnt, `value`)
            TelStatLog.TelStatLog( TelStatProcessSizeWarnMessage1, msg, False )
            return
        try:
            curPsSize = long( atm )
        except:
            curPsSize = prevPsSize
            msg = "(%s): At update cycle %4d, unknown TelStat process size (%s)" %\
                (label, OSSC_screenPrintConversions.OSPC_IterCnt, atm)
            TelStatLog.TelStatLog( TelStatProcessSizeWarnMessage2, msg, False )
        #? atm = PsSzAtomPattern.match( inLine ).group(1)
        #? # print 'atm = "%s"' % atm
        #? curPsSize = long( atm )
    else:       # MyUname == ??
        return

    diff = curPsSize - prevPsSize
    #? print 'diff = %s, diffMin = %s' % (`diff`, `diffMin`)
    if  diff <= -diffMin or diff >= diffMin:
        msg = "(%s): At update cycle %4d, TelStat process size = %d KB" %\
            (label, OSSC_screenPrintConversions.OSPC_IterCnt, curPsSize)
        TelStatLog.TelStatLog( TelStatProcessSizeMessage, msg, True )
        prevTime   = t
        prevPsSize = curPsSize


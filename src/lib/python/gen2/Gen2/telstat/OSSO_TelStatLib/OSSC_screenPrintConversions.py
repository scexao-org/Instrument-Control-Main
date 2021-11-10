# OSSC_screenPrintConversions.py -- Bruce Bon -- 2008-08-26
#
# The purpose of this module is to provide a wrapper that calls 
# OSSC_screenPrint and converts its output.  The goal is to isolate
# peculiarities of OSSC_screenPrint and hard-coded conversions from
# StatIO.py.  The StatusDictionary dictionary, herein, must
# have the same keys as the aliasDict dictionary in OSSC_screenPrint.
#

##############################################################################
################   import needed modules   ###################################
##############################################################################

import os, os.path
import time
import sys
import types
import re
import socket
import getpass
from types import *
from math  import *

from OSSC_screenPrintData import *
import StatIO
import TelStatLog
import StatusDictionary as SD
import TelStat_cfg
import DispType

##############################################################################
################   Gen2-specific global variables   ##########################
##############################################################################

# NOTE: gen2src should be a symbolic link in the 
#       .../product/OSSO/OSSO_TelStat.d directory, pointing at 
#       .../gen2/trunk/src and gen2lib should be a symbolic link 
#       pointing at .../lib/trunk/python
gen2FirstTime = True

#gen2libpath = './gen2lib'
##thisDir = os.path.split(sys.modules[__name__].__file__)[0]
##gen2libpath = '%s/../gen2lib' % thisDir
#print "gen2libpath is %s" % gen2libpath

#print "LOOKING FOR GEN2 at %s" % (gen2libpath)
##if  os.path.exists( gen2libpath ):
##    sys.path.append( gen2libpath )
from SOSS.status import STATNONE, STATERROR, g2StatusObj, cachedStatusObj
import remoteObjects as ro
import remoteObjects.Monitor as Monitor

statServerAvailable = False     # may be reset if in Gen2 mode
g2Stat = None                   # will be the 'status' server ro proxy


newvaldict={}
keynum=0

class Gen2Error( Exception ):
    """No new functionality, just the name."""
    pass

##############################################################################
################   global variables   ########################################
##############################################################################

aliasDictNdx    = 0
aliasDictOffset = 0
OSPC_IterCnt    = 0

exitCB = None

ScrPrntLogOpenMessage  = TelStat_cfg.ScrPrntInfoBase
ScrPrntSimNdxMessage   = TelStat_cfg.ScrPrntInfoBase+1

ScrPrntWarnReplayCnvrt = TelStat_cfg.ScrPrntWarnBase
ScrPrntWarnReplayNoKey = TelStat_cfg.ScrPrntWarnBase+1
ScrPrntWarnUndefMax    = TelStat_cfg.ScrPrntWarnBase+2

ScrPrntUndefErr       = TelStat_cfg.ScrPrntErrBase
ScrPrntErrConversion  = TelStat_cfg.ScrPrntErrBase+1
ScrPrntErrReplayOpen  = TelStat_cfg.ScrPrntErrBase+2
ScrPrntErrReplayRead  = TelStat_cfg.ScrPrntErrBase+3
ScrPrntErrAppNotFound = TelStat_cfg.ScrPrntErrBase+4
ScrPrntErrBadSymName  = TelStat_cfg.ScrPrntErrBase+5
ScrPrntErrCalHctAmp   = TelStat_cfg.ScrPrntErrBase+6
ScrPrntSrvConnect1Err = TelStat_cfg.ScrPrntErrBase+7
ScrPrntSrvConnect2Err = TelStat_cfg.ScrPrntErrBase+8
ScrPrntSrvConnect3Err = TelStat_cfg.ScrPrntErrBase+9
ScrPrntSrvConnect4Err = TelStat_cfg.ScrPrntErrBase+10
ScrPrntUnknownErr     = TelStat_cfg.ScrPrntErrBase+11
ScrPrntErrRemObjError = TelStat_cfg.ScrPrntErrBase+12

G2ErrConversion       = TelStat_cfg.ScrPrntErrBase+12

# Replay-related variables
replayFile      = None
__replayLineBuf = '\n'
__replayEOF     = False

##############################################################################
################   Functions intended for local use only   ###################
##############################################################################

def __OSPC_aliasListStr( statKeys ):
    """Convert Python list, statKeys, into a comma-delimited string list."""
    outStr = ""
    for  key in statKeys:
        if  key[0:8] == 'TELSTAT.':
            continue    # any TELSTAT alias is for internal use only!
        if  outStr == '':
            outStr = key
        else:
            outStr += ' ' + key
    #? print "__OSPC_aliasListStr: statKeys = ", statKeys
    #? print "__OSPC_aliasListStr: outStr = "
    #? print "   `%s'" % outStr
    return outStr

__entryLineCnt = 0
def __OSPC_writeAliasToLog( key, valueStr ):
    global __entryLineCnt
    valueStr = valueStr.strip()
    if  valueStr == "" or valueStr[0] == "#" or valueStr == None:
        return          # don't write out None's
        #? # convert null, comment, None into "None"
        #? valueStr = "None"
    TelStat_cfg.telStatDataLog_fd.write( '%s %s; ' % (key,valueStr) )
    __entryLineCnt += 1
    if  __entryLineCnt >= 3:
        __entryLineCnt = 0
        TelStat_cfg.telStatDataLog_fd.write( '\n' )


##############################################################################
################   Module-global functions   #################################
##############################################################################

OSPCspNotFoundErrorPattern = re.compile('.*OSSC_screenPrin.* not found')

OSPCundefSymErrorPattern   = re.compile('Error :.*\[(.*)\]=ERROR')
OSPCundefSymCALHCTErrorPattern = \
    re.compile('Error :.*\[TSCL\.CAL_HCT(.)_AMP(.*)\]=ERROR')

OSPCcannotConnectServer1ErrorPattern = re.compile(\
       'cannot connect to server. \( not running.*\[srv=(.*),prop=(.*?)\].*')
OSPCcannotConnectServer2ErrorPattern = \
    re.compile('Error : Exit=-1 arg1=\[(.*)\] arg2=\[OSSC_screenPrint.*')
OSPCcannotConnectServer3ErrorPattern = \
    re.compile('socket connection hangup !!  cannot continue .*')
OSPCcannotConnectServer4ErrorPattern = \
    re.compile('recv\(\) error\. cannot read header.*')

OSPCmaxUndefinedSymbolMessages = 100
OSPCalwaysPrint = True
OSPCspUnknownScreenPrintErr = ""
OSPCspUnknownScreenPrintErrCnt = 0

def OSPC_getValues_CommonProlog():
    """Perform prolog actions common to both OSPC_getValues_ScreenPrint
    and OSPC_getValues_Gen2."""

    global __entryLineCnt
    global OSPC_IterCnt

    OSPC_IterCnt += 1           # for debugging
    __entryLineCnt = 0          # reset this to make all records in phase

    # If the first time, open data log file to write
    if  TelStat_cfg.telStatDataLogging and      \
        TelStat_cfg.telStatDataLog_fd == None:
        # Open the data log -- this is the only place that it is opened
        if  TelStat_cfg.telStatDataLoggingFirstTime:
            # First time, just use the path from TelStat_cfg
            OSPCtelStatDataLog_path = TelStat_cfg.TELSTAT_DATALOG_PATH
            TelStat_cfg.telStatDataLoggingFirstTime = False
        else:
            # After first time, find current time tag and construct file name
            timeTuple  = time.localtime()
            timeString = '%d_%02d_%02d_%02d%02d%02d' % \
                         ( timeTuple[0], timeTuple[1], timeTuple[2],
                           timeTuple[3], timeTuple[4], timeTuple[5] )
            OSPCtelStatDataLog_path =   \
                TelStat_cfg.TELSTAT_LOG_ROOT_DIR + '/TelStat_ReplayData_' + \
                getpass.getuser() + '_' + timeString + '.log'
        TelStat_cfg.telStatDataLog_fd = open( OSPCtelStatDataLog_path, 'a' )
        os.chmod( OSPCtelStatDataLog_path, 0644 )
        TelStat_cfg.telStatDataLog_fd.write( 
              '# TelStat Version ' + 
               TelStat_cfg.TELSTAT_VERSION + ' ' + TelStat_cfg.TELSTAT_DATE +
              ', ' + TelStat_cfg.telstatMode + ' mode, on ' +
              socket.gethostname() + '\n#\n' )
        TelStatLog.TelStatLog( ScrPrntLogOpenMessage, 
            '(OSSC_screenPrintConversions:OSPC_getValues_ScreenPrint): ' +
            'Started data logging to %s' % OSPCtelStatDataLog_path, True )

    # Get time for this cycle
    epochTime = time.time()

    # Write time tag to data log file
    if  TelStat_cfg.telStatDataLogging:
        timeTuple  = time.localtime(epochTime)
        timeString = '%d-%d-%02d %02d:%02d:%02d' % \
                        ( timeTuple[0], timeTuple[1], timeTuple[2],
                          timeTuple[3], timeTuple[4], timeTuple[5] )
        TelStat_cfg.telStatDataLog_fd.write( 
                        '%s  %s\n' % (timeString, TelStat_cfg.OSS_OBS_HOST) )

    # Get list of StatusDictionary keys and remove inactive keys from the list
    statusKeys     = SD.StatusDictionary.keys()
    statusKeysIter = SD.StatusDictionary.keys()
    #? statusKeysIter.sort()    # good for debugging, but not needed otherwise
    for  key in statusKeysIter:
        if  not SD.StatusDictionary[key].getActive():
            statusKeys.remove( key )

    # Sort statusKeys (optional, might be deleted to save time)
    #statusKeys.sort()

    return epochTime, statusKeys


class Make_cb(object):
   
    def __init__(self, **kwdargs):
        self.__dict__.update(kwdargs)

    def anon_arr(self, payload, name, channels):
                   
        try:
            bnch = Monitor.unpack_payload(payload)
            
            if self.monpath and (not bnch.path.startswith(self.monpath)):
                return
        except Monitor.MonitorError:
            return

        try:
            with StatIO.lock:
                #self.logger.debug('bnch val  %s' %bnch.value) 
                newvaldict.update((k,bnch.value[k]) for k in newvaldict.keys() if k in bnch.value)
                #self.logger.debug('update newvaldict ...  %s' %newvaldict) 
        except Exception, e:
            self.logger.error('status updating error %s' %e)
            return 


def OSPC_getValues_Gen2(logger, fromGen2=True):
    """Get updated values for the SD.StatusDictionary from
     the Gen2 status server, using conversions specified therein."""
 
    global __entryLineCnt
    global gen2FirstTime, statServerAvailable, g2Stat
    global newvaldict,keynum

    # First time -- check for status server presence, get remote proxy
    if  gen2FirstTime:
        gen2FirstTime = False
        if fromGen2:
            g2Stat = g2StatusObj(svcname='status')
        else:
            g2Stat = cachedStatusObj('obs1.sum.subaru.nao.ac.jp')
        statServerAvailable = True

    # Set __entryLineCnt, OSPC_IterCnt; open data log (first time only); 
    #   get epochTime and statusKeys
    epochTime, statusKeys = OSPC_getValues_CommonProlog()

    # Separate statusKeys into fetchKeys and telstatKeys
    fetchKeys   = []
    for  key in statusKeys:
        if not  key.startswith( 'TELSTAT.'):
            fetchKeys.append( key )
   
    current_keynum=len(fetchKeys)

    try:
        logger.debug('keynum=%d   cur_keynum=%d' %(keynum, current_keynum) )
        if not keynum ==  current_keynum:
            keynum=current_keynum
            newvaldict = dict.fromkeys( fetchKeys, STATNONE )
            newvaldict = g2Stat.fetch( newvaldict )
            logger.debug('fetching from status server...')
        else:
            logger.debug('fetching from mon ...')

        #print "result = ",newvaldict
    except  Exception, value:
        keynum=0
        # set TELSTAT.UNIXTIME
        SD.StatusDictionary['TELSTAT.UNIXTIME'].setValue(hrsec=epochTime)
        # log error
        logger.error("ERROR (OSSC_screenPrintConversions:OSPC_getValues_Gen2):  cannot access remote status object: %s" %str(value))
        # set all other variables to None
        for  key in statusKeys:
            if  key != 'TELSTAT.UNIXTIME':
                SD.StatusDictionary[key].setValue( None )
        # if logging is turned on, write TELSTAT.NODATA, to data log
        if  TelStat_cfg.telStatDataLogging:
            __OSPC_writeAliasToLog( 'TELSTAT.NODATA', 'No Data' )
            TelStat_cfg.telStatDataLog_fd.write( '\n' )
            TelStat_cfg.telStatDataLog_fd.write( '\n' )
        # end of processing for this cycle -- return
        return
    #? printDict( 'newvaldict', newvaldict )

    # Start data log entry 
    key = 'TELSTAT.UNIXTIME'
    SD.StatusDictionary[key].setValue( hrsec=epochTime )

    # if data logging turned on, write TELSTAT.UNIXTIME to file
    if  TelStat_cfg.telStatDataLogging:
        __OSPC_writeAliasToLog( key, SD.StatusDictionary[key].format_forLog() )

    #with lock:
    # Process newvaldict values
    for  key,g2val in newvaldict.items():
        try:
            SD.StatusDictionary[key].fromGen2(g2val)
        except  DispType.ConversionError, value:
            # Log conversion error message
            logger.error("key = %s, G2 status value = %s"  %( key, str(g2val)) )
            SD.StatusDictionary[key].setValue( None )
        else:
            #? print '%d: %s' % (__entryLineCnt,key)
            # if data logging turned on, write status alias to file
            if  TelStat_cfg.telStatDataLogging:
                __OSPC_writeAliasToLog( key, 
                                        SD.StatusDictionary[key].formatForLog())

    if  TelStat_cfg.telStatDataLogging:
        TelStat_cfg.telStatDataLog_fd.write( '\n' )
        if  __entryLineCnt != 0:
            TelStat_cfg.telStatDataLog_fd.write( '\n' )

    #? raise Gen2Error, 'Gen2 test, stop after first fetch!'


def printDict( name, valdict ):
    print name,':'
    keys = valdict.keys()
    keys.sort()
    for  key in keys:
        print '    %-20s   %s' % (key, `valdict[ key ]`)
    print

def OSPC_getValues_Replay():
    """Get values for the SD.StatusDictionary from a ReplayData
    log file, using conversions specified in StatusDictionary."""
    global statusKeys, replayFile, __replayLineBuf, __replayEOF
    global replayNdx, OSPC_IterCnt

    OSPC_IterCnt += 1           # for debugging

    # If replay file has finished, return without modifying dictionary!
    # This leaves the dictionary values at the last ones read from the file.
    if  replayFile != None:
        if   replayFile.closed:
            return

    # Get list of StatusDictionary keys and remove inactive keys from the list
    statusKeys     = SD.StatusDictionary.keys()
    statusKeysIter = SD.StatusDictionary.keys()
    #? statusKeysIter.sort()    # good for debugging, but not needed otherwise
    for  key in statusKeysIter:
        try:
            if  not SD.StatusDictionary[key].getActive():
                statusKeys.remove( key )
        except:
            print 'Exception on status with key', key
            print SD.StatusDictionary[key]
            msg = \
               ("ERROR (OSSC_screenPrintConversions:OSPC_getValues_Replay): "+ \
                "Exception on status with key '%s'" % key )
            print msg
            TelStatLog.TelStatLog( ScrPrntErrConversion, msg, True )
            exitCB()

    # If file is not already open, open it and skip replayInitSkip records
    #  NOTE: this logic will skip replayInitSkip records each time the
    #   file is re-opened, e.g. by selecting Options/Restart Data Replay
    if  replayFile == None:
        try:
            replayFile = open( TelStat_cfg.replayFileSpec, 'r' )
            for  i in range(0, TelStat_cfg.replayInitSkip):
                __replaySkipRecord()
        except:
            msg = \
               ("ERROR (OSSC_screenPrintConversions:OSPC_getValues_Replay): "+ \
                "replay file '%s' open failed.") % TelStat_cfg.replayFileSpec
            print msg
            TelStatLog.TelStatLog( ScrPrntErrReplayOpen, msg, True )
            exitCB()
        __replayLineBuf = '\n'
        __replayEOF = False   # initialize to no EOF

    # First try to read date/time line, to detect end of file
    __replayReadLine()          # date/time

    # If replay file has finished, return without modifying dictionary!
    # This leaves the dictionary values at the last ones read from the file.
    if   replayFile.closed:
        return

    # Initialize all variables except TELSTAT.UNIXTIME to None
    for  key in statusKeys:
        if  key != 'TELSTAT.UNIXTIME':
            SD.StatusDictionary[key].setValue( None )

    # Read a record and process all its alias assignments
    __replayReadLine()          # first record with data
    while __replayLineBuf != '\n' and __replayLineBuf != '':
        while  __replayGetAliasVal() == True:
            pass
        __replayReadLine()      # read next record line (blank for EOR)

    # Skip records as needed for replaySamplePeriod
    if  TelStat_cfg.replaySamplePeriod > 1:
        for  i in range(0, TelStat_cfg.replaySamplePeriod):
            __replaySkipRecord()


def __replayReadLine():
    """Read a single line of a replay log file."""
    global replayFile, __replayLineBuf, __replayEOF
    # Are we already at end-of-file?  If so, do nothing.
    if  __replayEOF:
        return
    # Read a line of record, ignoring comment lines beginning with "#"
    __replayLineBuf = '#'                       # force first read
    while __replayLineBuf != '' and __replayLineBuf[0] == '#':
        try:
            __replayLineBuf = replayFile.readline()
        except:
            TelStatLog.TelStatLog( ScrPrntErrReplayRead,
               ("ERROR (OSSC_screenPrintConversions:OSPC_getValues_Replay): " +
                "replay file '%s' read failed.") % TelStat_cfg.replayFileSpec,
                True )
            exitCB()
    # If read nothing, we're at end of file, so close it
    if  __replayLineBuf == '':  # end of file
        replayFile.close()
        __replayEOF = True

def __replaySkipRecord():
    """Skip a record in a replay log file."""
    global replayFile, __replayLineBuf, __replayEOF
    __replayReadLine()          # date/time
    __replayReadLine()          # first record with data
    while __replayLineBuf != '\n' and not __replayEOF:
        __replayReadLine()
    # If we're at end of file, close it
    if  __replayLineBuf == '':  # end of file
        replayFile.close()
        __replayEOF = True

OSPCaliasAssignPattern   = re.compile('(^\S+?)(\s+?)(.*?);')

def __replayGetAliasVal():
    """Get all alias values from a single line of a replay record."""
    global statusKeys, replayFile, __replayLineBuf
    global OSPCaliasAssignPattern
    i = __replayLineBuf.find(';')
    if  i < 0:          # not found indicates no more aliases on this line
        return False
    #print "__replayGetAliasVal: __replayLineBuf = `%s', i = %d" % \
    #   (__replayLineBuf[:-1], i)
    mo = OSPCaliasAssignPattern.match( __replayLineBuf )
    if  mo:
        key = mo.group(1)
        outStr = mo.group(3)
        # test for empty record!!
        if  key == 'TELSTAT.NODATA':
            # return False to end processing of this line, and this should
            # be the last line in the record
            return False
        #? print "__replayGetAliasVal: key = %s, outStr = `%s'" % (key, outStr)
        if  not SD.StatusDictionary.has_key( key ):
            TelStatLog.TelStatLog( ScrPrntWarnReplayNoKey,
               ("WARNING (OSSC_screenPrintConversions:OSPC_getValues_Replay): "+
                "key `%s' is not in StatusDictionary.") % key,
                False )
        elif  outStr == "None":
            SD.StatusDictionary[key].setValue( None )
        else:
            try:
                SD.StatusDictionary[key].fromLogFmt(outStr)
            except  DispType.ConversionError, value:
                # Log conversion error message
                TelStatLog.TelStatLog( ScrPrntErrConversion,
                 ("ERROR (OSSC_screenPrintConversions:OSPC_getValues_Replay):"+
                    " conversion failure: key = %s, value-string = `%s'") % \
                    (key, outStr), False )
                SD.StatusDictionary[key].setValue( None )
    else:
        TelStatLog.TelStatLog( ScrPrntWarnReplayCnvrt,
           ("WARNING (OSSC_screenPrintConversions:OSPC_getValues_Replay): " +
            "replay pattern match failure, LineBuf = `%s'.") % __replayLineBuf,
            False )
    __replayLineBuf = __replayLineBuf[i+2:]

    return True

# StatIO.py -- Bruce Bon -- 2006-12-05 16:08

##############################################################################
################   import needed modules   ###################################
##############################################################################

import os
import sys
from math import *
import threading

import TelStatLog
from DispType import *
import OSSC_screenPrintConversions
import StatusDictionary as SD
import TelStat_cfg
import TelStatProcSize

##############################################################################
################   global constants   ########################################
##############################################################################

# source codes
StatIO_ScreenPrint    = 0       # "OSSC_screenPrint"
StatIO_ScreenPrintSim = 1       # "OSSC_screenPrint simulation"
StatIO_Gen2           = 2       # pull data from Gen2 status server
StatIO_Replay         = 3       # replay a log file
StatIO_SossCache      = 4       # get status from Soss cache object

##############################################################################
################   global variables   ########################################
##############################################################################

# List of registered panes
StatIO_RegisteredPanes = []

# Data source in current use
StatIO_DataSource = StatIO_ScreenPrintSim

##############################################################################
################   Private functions   #######################################
##############################################################################

def _typeStr( x ):
    """Return the type string corresponding to x, without the extras
    around it.  I.e. if "print type(x)" prints out "<type 'float'>",
    then typeStr(x) will return "float"."""
    tStr = `type(x)`
    i1 = tStr.find( "'" )
    if  i1 < 0:
        return tStr
    i2 = tStr.find( "'", i1+1 )
    if  i2 < 0:
        return tStr
    tStr = tStr[i1+1:i2]
    if  tStr == 'NoneType':
        tStr = 'None'
    return tStr

##############################################################################
################   Module-global functions   #################################
##############################################################################

def StatIO_initialize( source, logger ):
    """Function that initializes the global dictionary, log file, etc."""
    global StatIO_DataSource
    #  Set module variable(s) to select and facilitate access to data source
    StatIO_DataSource = source

    #? TelStatLog.TelStatLog( TelStat_cfg.StatioInfoBase, 
    #?  'StatIO_initialize, data source = %s, OSSC_screenPrintPath = %s' % 
    #?  (source, TelStat_cfg.OSSC_screenPrintPath), True )

    # ??? Initialize any necessary data structures, e.g. in global dictionary
    # ??? Close log file if any is open at this time

    # ??? Open a log file and output initial data, e.g. dictionary keys
    StatIO_service(logger)

def StatIO_close():
    """Function that closes the log file."""
    # ??? Close log file if any is open at this time
    pass

def StatIO_printDict( logfile ):
    """Function to print essential data from global dictionary."""
    logfile.write( "\nStatus Alias Dictionary Values\n" )
    keys = SD.StatusDictionary.keys()
    keys.sort()
    for  key in keys:
        try:
            if  SD.StatusDictionary[key].myDDT() == DDT_int:
                logfile.write( "    %-22s (%-5s): %14s = %s\n" % \
                               (key, _typeStr(SD.StatusDictionary[key].value()),
                                     SD.StatusDictionary[key].format(),
                                     SD.StatusDictionary[key].formatHex()) )
            else:
                logfile.write( "    %-22s (%-5s):   %s\n" % \
                               (key, _typeStr(SD.StatusDictionary[key].value()),
                                     SD.StatusDictionary[key].format()) )
        except Exception, e:
            logfile.write( "    %-22s: bad dict entry: %s {%s} \n" % \
                           (key, `SD.StatusDictionary[key]`, e) )
        logfile.flush()
    logfile.write( "\n" )
    #? for  key in SD.StatusDictionary.keys():
    #?  TelStatLog.TelStatLog( TelStat_cfg.StatioInfoBase, "  %-20s   %s" % \
    #?          (key, SD.StatusDictionary[key].format()), True)
    #? TelStatLog.TelStatLog( TelStat_cfg.StatioInfoBase, "", True )
        
def StatIO_registerPane( pane ):
    """Function to register a GUI pane with StatIO, adding its
    set of status keys to the global dictionary."""
    statusKeys = pane.statKeys()
    #? TelStatLog.TelStatLog( TelStat_cfg.StatioInfoBase,
    #?     "    StatIO_registerPane called for pane `%s'." % pane.myName, True )
    #? TelStatLog.TelStatLog( TelStat_cfg.StatioInfoBase,
    #?     "      status keys = %s" % `statusKeys`, True )
    # Add status keys to global dictionary
    for  key in pane.statKeys():
        if  not (SD.StatusDictionary.has_key( key )):
            #print "--==--> whoa, not adding bad dict for %s" % (key)
            # fixme: sammy doesn't understand why this object gets wrapped in a dict that breaks the code...
            #SD.StatusDictionary[ key ] = (StrDDT(key), SD.OSPC_ConvrtStr, True)
            SD.StatusDictionary[ key ] = StrDDT(key)
            # ??? Look up status data in StatusAlias.def ???
    #? print "    StatIO_registerPane: all keys = ", SD.StatusDictionary.keys()
    #? print
    # Add pane to pane list for refresh
    StatIO_RegisteredPanes.append( pane )

lock=threading.RLock()

def StatIO_service(logger):
    """Main service function that retrieves status values to update
    the global dictionary.  Should be called 1/second."""

    with lock:
        
        OSSC_screenPrintConversions.OSPC_getValues_Gen2(logger)

        # Call refresh methods of all registed panes
        for  pane in StatIO_RegisteredPanes:
            pane.refresh( SD.StatusDictionary )


##############################################################################
################   declare Pane base class   #################################
##############################################################################

# Display pane base class -- declare required attributes and methods, and
#       provide minimal versions of them
class StatPaneBase:
    def __init__(self, statusKeys, myName="Unspecified"):
        """Constructor for status display pane base."""
        self.statusKeys = statusKeys
        self.myName = myName
    #?  TelStatLog.TelStatLog( TelStat_cfg.StatioInfoBase,
    #?          "  StatPaneBase constructor for pane `%s':" % self.myName, True)
        StatIO_registerPane( self )

    def refresh(self, dict):
        """Refresh pane with updated values from dict."""
    #?  TelStatLog.TelStatLog( TelStat_cfg.StatioInfoBase,
    #?          "    Pane ", self.myName, " received refresh call:", True )
        # ??? Do whatever is necessary to refresh the pane!
        # ??? This method should be overridden by the child pane class.
        for  key in self.statusKeys:
            TelStatLog.TelStatLog( TelStat_cfg.StatioInfoBase,
                "      %-20s   %s" % \
                (key, SD.StatusDictionary[key].format()), True)

    def statKeys(self):
        """Return list of status keys of interest to this pane."""
        return self.statusKeys

    def printGeom( self ):
        """Print this pane's current geometry."""
        self.update_idletasks() # must be done to assure that geometry is up to date
        print self.myName + "\t",
        if  len(self.myName) < 8:
            print "\t",
        print "Pane geometry = ", self.winfo_geometry()

##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
# 
# Phase 0: as above implemented:
#   - Master allocates individual panes, which in turn register themselves
#     with StatIO (see StatPaneBase.__init__ above) by calling 
#     StatIO_registerPane( self ).
#   - StatIO_registerPane( pane ) calls pane.statKeys() to get a list of status 
#     keys that are used by this pane, and adds any to the global dictionary
#     that aren't already there.  It also adds pane to a list of panes whose
#     refresh methods will be called by StatIO_service().
#   - Master calls StatIO_initialize() before any use of global dictionary,
#     to specify the data source and do any necessary data initialization.
#   - Master (or "after" or a thread Timer) calls StatIO_service() periodically
#     to update the dictionary; StatIO_initialize() will call StatIO_service()
#     as part of initialization.
#   - StatIO_service() performs whatever operations are necessary to acquire
#     data values with which to update the global dictionary, then calls the
#     refresh methods of all registered panes, providing the pane with a
#     reference to the global dictionary.
#   - Each pane accesses the global dictionary directly to get needed objects.
#     May call the format() method of each object to get a formatted string
#     representation of the value, and then set a StringVar variable which will
#     then automatically update a widget's display.  May also call the value() 
#     method to get a numeric value.
#
##############################################################################
# 
# Phase 1:
#  - Decipher RPC protocol used for getting status values from OBS alias server.
#  - Develop an RPC alias server simulator module with which to test this 
#    version.
#  - Replace calls to OSSC_screenPrint in StatIO_initialize() with conditional
#    code, which makes some sort of local IPC call if the client and server 
#    hosts are the same, and which makes RPC calls if they are different.
#    (Or always make RPC calls.)
# 
#  Estimated time to add:  several days to 2 weeks
#

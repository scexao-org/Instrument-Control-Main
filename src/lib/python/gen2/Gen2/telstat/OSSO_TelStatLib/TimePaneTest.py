#!/usr/local/bin/python
# TimePaneTest.py -- Arne Grimstrup -- 2003-10-01
# copied shameless from PointingPaneTest.py -- Bruce Bon -- 2003-09-29 12:05

# Test program for TimePane.py

######################################################################
################   import needed modules   ###########################
######################################################################

import os
import sys
import signal
import time

import Tkinter
from Tkconstants import *
import Pmw

from TimePane import *

######################################################################
################   assign needed globals   ###########################
######################################################################

EXITCODE   = 0

dbgcnt = 10

######################################################################
################   root function definitions   #######################
######################################################################

def SigHandler(signum, frame):
    """Signal handler for all unexpected conditions."""
    global EXITCODE		# necessary, else assignment would be local!
    print "TimePaneTest.SigHandler() called, signum = ",	\
	    signum,".\n"
    EXITCODE = signum
    EndProc()

def EndProc():
    """Exit function."""
    print "TimePaneTest.EndProc() called, EXITCODE = ",	\
	    EXITCODE,".\n"
    root.destroy()
    sys.exit( EXITCODE )

def RootRefresh():
    global dbgcnt
    print "TimePaneTest.RootRefresh() called, time = %.6f" % time.time()
    StatIO_service()
    root.after( 1000, RootRefresh )
#?    dbgcnt -= 1
#?    if  dbgcnt > 0:
#?	root.after( 1000, RootRefresh )

######################################################################
################   root operations   #################################
######################################################################

StatIOsource = StatIO_ScreenPrintSim
TelStat_cfg.OSSC_screenPrintPath = OSSC_SCREENPRINTSIMPATH

# Instantiate a Pmw/Tk object and set its tk_strictMotif attribute for strict
#	Motif compliance
root = Tkinter.Tk()
Pmw.initialise(root)
root.tk_strictMotif(1)
root["bg"] = "black"
root.iconname( 'TimePaneTest' )
root.title( 'TimePaneTest' )
root.protocol( 'WM_DELETE_WINDOW', EndProc )

# Set signal handler for various signals
signal.signal( signal.SIGINT, SigHandler )
signal.signal( signal.SIGTERM, SigHandler )
signal.signal( signal.SIGUSR1, SigHandler )
signal.signal( signal.SIGUSR2, SigHandler )


# Create pane
tpPane = TimePane(root, pbgcolor="lightblue")
tpPane.rePack()

# Get status data -- this should be called periodically!!
RootRefresh()

# Go
root.mainloop()

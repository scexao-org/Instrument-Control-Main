#! /usr/local/bin/python

#  Arne Grimstrup
#  2003-09-29
#  Modified 2006-12-04 16:28 Bruce Bon

#  This module implements the Dome Flat Field status display pane.

from Tkinter import *      # UI widgets and event loop infrastructure
from StatIO import *       # Status I/O functions
from DispType import *     # Status display data types
from TelStat_cfg import *  # Display configuration

import TelStatLog          # Diagnostic logging
import Pmw                 # Additional UI widgets 
import IndicatorLamp       # Light widget

DomeErrUndefDomeFF_A   = DomeErrBase+1
DomeErrNoDataDomeFF_A  = DomeErrBase+2
DomeErrUndefDomeFF_1B  = DomeErrBase+3
DomeErrNoDataDomeFF_1B = DomeErrBase+4
DomeErrUndefDomeFF_2B  = DomeErrBase+5
DomeErrNoDataDomeFF_2B = DomeErrBase+6
DomeErrUndefDomeFF_3B  = DomeErrBase+7
DomeErrNoDataDomeFF_3B = DomeErrBase+8
DomeErrUndefDomeFF_4B  = DomeErrBase+9
DomeErrNoDataDomeFF_4B = DomeErrBase+10

class DomePane(Frame, StatPaneBase):
    """Create an instance of the Dome Flat Field display pane."""
    def __init__(self, parent, pfgcolor=DOMEPANEFOREGROUND, pbgcolor=DOMEPANEBACKGROUND,
                 pfont=DOMEPANELABELFONT, lcolor=DOMEPANELIGHTCOLOR):
        # Initialize base classes and register status symbols to be delivered
        # to this pane
        Frame.__init__(self, parent)
        StatPaneBase.__init__(self, ('TSCV.DomeFF_A','TSCV.DomeFF_1B','TSCV.DomeFF_2B',
                                     'TSCV.DomeFF_3B','TSCV.DomeFF_4B'), 'DomePane')

        # Single button press forces the pane to report its geometry.  Used for
        # debugging purposes only.
        self.configure(bg=pbgcolor)
        self.bind("<ButtonRelease-1>", self.geomCB)

        # Store the configuration for the lights.  Note that all lights will have
        # the same on/off colour.  To change this, we'll need to move duplicate
        # this tuple and move it to the configuration file.
        self.lightconfig = (50, 30, pbgcolor, pfgcolor, lcolor[0], 
                            [DOMEPANEOFFFOREGROUND, DOMEPANEONFOREGROUND, 
                             DOMEPANEONFOREGROUND, DOMEPANEONFOREGROUND])

        # The pane consists of a title label, two lights, and a field to report the
        # amperage of the light.  The amperage label is blank since there is no
        # status symbol currently defined that reports the value.
        self.TLabel = Label(self, text="DomeFF ", font=pfont, bg=pbgcolor, fg=pfgcolor)
        self.TLabel.grid(row=0,column=0)

        self.Light10W = IndicatorLamp.IndicatorLamp(self, "10W", self.lightconfig)
        self.Light10W.grid(row=0,column=1)

        self.Light600W = IndicatorLamp.IndicatorLamp(self, "600W", self.lightconfig)
        self.Light600W.grid(row=0,column=2)

        self.ALabel = Label(self, text=" ", font=pfont, bg=pbgcolor, fg=pfgcolor)
        self.ALabel.grid(row=0,column=3)

        self.badFfaCount  = 0
        self.badFf1bCount = 0
        self.badFf2bCount = 0
        self.badFf3bCount = 0
        self.badFf4bCount = 0

    def refresh(self, dict):
        """Refresh the pane display."""
        self.update(dict)


    def update(self, dict):
        """Update the light displays with the most recent status."""

        # Get the raw data and extract 5 2-bit single-lamp status values
        ff1bN = ff2bN = ff4bN = None
        ffa  = ffaN = dict['TSCV.DomeFF_A'].value()
        ff1b = dict['TSCV.DomeFF_1B'].value()
        if  ff1b != None:
            ff1bN = ff1b >> 2
        ff2b = dict['TSCV.DomeFF_2B'].value()
        if  ff2b != None:
            ff2bN = ff2b >> 4
        ff3bN = ff3b = dict['TSCV.DomeFF_3B'].value()
        ff4b  = dict['TSCV.DomeFF_4B'].value()
        if  ff4b != None:
            ff4bN = ff4b >> 2

        # Count number of lamps ON
        numberOn = 0
        if  ffaN == 0x01:
            numberOn += 1
        if  ff1bN == 0x01:
            numberOn += 1
        if  ff2bN == 0x01:
            numberOn += 1
        if  ff3bN == 0x01:
            numberOn += 1
        if  ff4bN == 0x01:
            numberOn += 1

        if  ffa == None:
            if  self.badFfaCount > 0:
                TelStatLog.TelStatLog( DomeErrNoDataDomeFF_A, 
                    "ERROR (DomePane:update):  " +
                    "No data available for 10 W Lamp Status (TSCV.DomeFF_A)" )
            self.badFfaCount += 1
            badLabel = "No Data"
        elif  ffaN != 0x01 and ffaN != 0x02:
            if  self.badFfaCount > 0:
                TelStatLog.TelStatLog( DomeErrUndefDomeFF_A, 
                    "ERROR (DomePane:update):  " +
                    "Undefined 10 W Lamp Status (TSCV.DomeFF_A) = %x" % ffa )
            self.badFfaCount += 1
            badLabel = "%02x" % ffa
        else:
            self.badFfaCount = 0

        if  self.badFfaCount > 1:
            self.Light10W.update(3, badLabel)         # Alarm
        elif  self.badFfaCount == 0:
            if ffa == 0x01:
                if  numberOn > 1:
                    self.Light10W.update(2, "10W")    # Warning
                else:
                    self.Light10W.update(1, "10W")    # On
            elif ffa == 0x02:
                self.Light10W.update(0)               # Off
        # else self.badFfaCount == 1 : do nothing

        # There is only one light but it is driven by these 4 symbols.
        if  ff1b == None:
            if  self.badFf1bCount > 0:
                TelStatLog.TelStatLog( DomeErrNoDataDomeFF_1B,
                   "ERROR (DomePane:update):  " +
                   "No data available for 600 W Lamp 1 Status (TSCV.DomeFF_1B)")
            self.badFf1bCount += 1
            badLabel = "No Data"
        elif  ff1bN != 0x01 and ff1bN != 0x02:
            if  self.badFf1bCount > 0:
                TelStatLog.TelStatLog( DomeErrUndefDomeFF_1B, 
                   "ERROR (DomePane:update):  " +
                   "Undefined 600 W Lamp 1 Status (TSCV.DomeFF_1B) = %x" % ff1b)
            self.badFf1bCount += 1
            badLabel = "%02x" % ff1b
        else:
            self.badFf1bCount = 0

        if  ff2b == None:
            if  self.badFf2bCount > 0:
                TelStatLog.TelStatLog( DomeErrNoDataDomeFF_2B,
                   "ERROR (DomePane:update):  " +
                   "No data available for 600 W Lamp 2 Status (TSCV.DomeFF_2B)")
            self.badFf2bCount += 1
            badLabel = "No Data"
        elif  ff2bN != 0x01 and ff2bN != 0x02:
            if  self.badFf2bCount > 0:
                TelStatLog.TelStatLog( DomeErrUndefDomeFF_2B, 
                   "ERROR (DomePane:update):  " +
                   "Undefined 600 W Lamp 2 Status (TSCV.DomeFF_2B) = %x" % ff2b)
            self.badFf2bCount += 1
            badLabel = "%02x" % ff2b
        else:
            self.badFf2bCount = 0

        if  ff3b == None:
            if  self.badFf3bCount > 0:
                TelStatLog.TelStatLog( DomeErrNoDataDomeFF_3B,
                   "ERROR (DomePane:update):  " +
                   "No data available for 600 W Lamp 3 Status (TSCV.DomeFF_3B)")
            self.badFf3bCount += 1
            badLabel = "No Data"
        elif  ff3bN != 0x01 and ff3bN != 0x02:
            if  self.badFf2bCount > 0:
                TelStatLog.TelStatLog( DomeErrUndefDomeFF_3B, 
                   "ERROR (DomePane:update):  " +
                   "Undefined 600 W Lamp 3 Status (TSCV.DomeFF_3B) = %x" % ff3b)
            self.badFf3bCount += 1
            badLabel = "%02x" % ff3b
        else:
            self.badFf3bCount = 0

        if  ff4b == None:
            if  self.badFf4bCount > 0:
                TelStatLog.TelStatLog( DomeErrNoDataDomeFF_4B,
                   "ERROR (DomePane:update):  " +
                   "No data available for 600 W Lamp 4 Status (TSCV.DomeFF_4B)")
            self.badFf4bCount += 1
            badLabel = "No Data"
        elif  ff4bN != 0x01 and ff4bN != 0x02:
            if  self.badFf4bCount > 0:
                TelStatLog.TelStatLog( DomeErrUndefDomeFF_4B, 
                   "ERROR (DomePane:update):  " +
                   "Undefined 600 W Lamp 4 Status (TSCV.DomeFF_4B) = %x" % ff4b)
            self.badFf4bCount += 1
            badLabel = "%02x" % ff4b
        else:
            self.badFf4bCount = 0

        if  self.badFf1bCount > 1 or self.badFf2bCount > 1 or \
            self.badFf3bCount > 1 or self.badFf4bCount > 1:
            self.Light600W.update(3, badLabel)        # Alarm
        elif  self.badFf1bCount == 0 and self.badFf2bCount == 0 and \
              self.badFf3bCount == 0 and self.badFf4bCount == 0:
            if  ff1bN != 0x02 or ff2bN != 0x02 or ff3bN != 0x02 or ff4bN != 0x02:
                if  numberOn > 1:
                    self.Light600W.update(2, "600W")  # Warning
                else:
                    self.Light600W.update(1, "600W")  # On
            else:   # if we get here, all data sources indicate off
                self.Light600W.update(0)              # Off
        # else self.badFf*bCount == 1 : do nothing


    def resize(self, paneWidth):
        """Change the pane to fit the new geometry."""
        
        # Update the window so that the correct geometry is reported
        # must be done to assure that geometry != 1x1+0+0
        self.update_idletasks()

        # Internally, the pane uses a grid to control the placement of
        # the component widgets.  Since we want to keep the lights
        # together, most of the resize is applied to the labels on
        # either side.
        colMinWidth     = int((paneWidth - self.Light10W.winfo_width() - \
                                self.Light600W.winfo_width()) / 2.0)
        rowMinHeight    = self.winfo_height()

        self.rowconfigure( 0, minsize=self.winfo_height() )
        self.columnconfigure( 0, minsize=colMinWidth )
        self.columnconfigure( 3, minsize=colMinWidth )

        # After the grid is resized, we can resize the pane itself
        self.configure( width=paneWidth, height=rowMinHeight )


    def rePack(self):
        """First resize, then repack this pane."""
        self.pack(anchor=NW)


    def geomCB(self, event):
        """Callback for to print geometry."""
        print "Dome pane:       ", self.winfo_geometry()


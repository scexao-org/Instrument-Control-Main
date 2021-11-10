#! /usr/local/bin/python

#  Arne Grimstrup
#  2003-09-29
#  Modified 2008-08-26 Bruce Bon

#  This module implements the Calibration Light status display pane.

from Tkinter import *      # UI widgets and event loop infrastructure
from StatIO import *       # Status I/O functions
from DispType import *     # Status display data types
from TelStat_cfg import *  # Display configuration

import TelStatLog          # Diagnostic logging
import Pmw                 # Additional UI widgets 
import IndicatorLamp       # Light widget

CalErrUndefDataHctLamp1 = CalErrBase+1
CalErrNoDataHctLamp1    = CalErrBase+2
CalErrUndefDataHctLamp2 = CalErrBase+3
CalErrNoDataHctLamp2    = CalErrBase+4
CalErrUndefDataHalLamp1 = CalErrBase+5
CalErrNoDataHalLamp1    = CalErrBase+6
CalErrUndefDataHalLamp2 = CalErrBase+7
CalErrNoDataHalLamp2    = CalErrBase+8
CalErrUndefDataRglLamp1 = CalErrBase+9
CalErrNoDataRglLamp1    = CalErrBase+10
CalErrUndefDataRglLamp2 = CalErrBase+11
CalErrNoDataRglLamp2    = CalErrBase+12

class CalPane(Frame, StatPaneBase):
    """Create an instance of the Calibration light display pane."""
    def __init__(self, parent, pfgcolor=CALPANEFOREGROUND, pbgcolor=CALPANEBACKGROUND,
                 plfont=CALPANELABELFONT, pafont=CALPANEAMPFONT, lcolor=CALPANELIGHTCOLOR):

        # Initialize the base classes and register the status symbols that are to be
        # received by this frame.
        Frame.__init__(self, parent)
        StatPaneBase.__init__(self, ('TSCL.CAL_POS','TSCL.CAL_HCT1_AMP',
                                     'TSCL.CAL_HCT2_AMP', 'TSCL.CAL_HAL1_AMP',
                                     'TSCL.CAL_HAL2_AMP', 'TSCV.CAL_HCT_LAMP1',
                                     'TSCV.CAL_HCT_LAMP2','TSCV.CAL_HAL_LAMP1',
                                     'TSCV.CAL_HAL_LAMP2', 'TSCV.CAL_RGL_LAMP1',
                                     'TSCV.CAL_RGL_LAMP2'), 'CalPane')

        # Single button press forces the pane to report its geometry.  Used for
        # debugging purposes only.
        self.configure(bg=pbgcolor)
        self.bind("<ButtonRelease-1>", self.geomCB)

        # Store the configuration for the lights.  Note that all lights will have
        # the same on/off colour.  To change this, we'll need to move duplicate
        # this tuple and move it to the configuration file.
        self.lightconfig = (50, 30, pbgcolor, pfgcolor, lcolor[0], 
                            [CALPANEOFFFOREGROUND, CALPANEONFOREGROUND, 
                             CALPANEONFOREGROUND, CALPANEONFOREGROUND])


        # The pane consists of a title label, a cluster of six lights, a field to
        # report the amperage of the active light, and a field to report the postion
        # of the calibration probe.
        self.TLabel = Label(self, text="CAL", font=plfont, bg=pbgcolor, fg=pfgcolor, width=5)
        self.TLabel.grid(row=0,column=0, rowspan=2)

        self.LightHCT1 = IndicatorLamp.IndicatorLamp(self, CALPANEHCT1LABEL, self.lightconfig)
        self.LightHCT1.grid(row=0,column=1)

        self.LightHCT2 = IndicatorLamp.IndicatorLamp(self, CALPANEHCT2LABEL, self.lightconfig)
        self.LightHCT2.grid(row=0,column=2)

        self.LightHAL1 = IndicatorLamp.IndicatorLamp(self, CALPANEHAL1LABEL, self.lightconfig)
        self.LightHAL1.grid(row=0,column=3)

        self.LightHAL2 = IndicatorLamp.IndicatorLamp(self, CALPANEHAL2LABEL, self.lightconfig)
        self.LightHAL2.grid(row=1,column=3)

        self.LightRGL1 = IndicatorLamp.IndicatorLamp(self, CALPANERGL1LABEL, self.lightconfig)
        self.LightRGL1.grid(row=1,column=1)

        self.LightRGL2 = IndicatorLamp.IndicatorLamp(self, CALPANERGL2LABEL, self.lightconfig)
        self.LightRGL2.grid(row=1,column=2)

        self.ALabelTxt = StringVar()
        self.ALabelTxt.set("        ")
        self.ALabel = Label(self, textvariable=self.ALabelTxt, font=pafont,
                            bg=pbgcolor, fg=pfgcolor )
        self.ALabel.grid(row=0,column=4,rowspan=2)

        self.PLabelTxt = StringVar()
        self.PLabelTxt.set("CAL Probe          mm")
        self.PLabel = Label(self, textvariable=self.PLabelTxt, bg=pbgcolor, fg=pfgcolor )
        self.PLabel.grid(row=2,column=0,columnspan=5)

        # Initialize all lamps to OFF and amperage to null
        self.LightHCT1.update(0)
        self.LightHCT2.update(0)
        self.LightHAL1.update(0)
        self.LightHAL2.update(0)
        self.LightRGL1.update(0)
        self.LightRGL2.update(0)
        self.ALabelTxt.set("         ")
        self.badHct1Count = 0
        self.badHct2Count = 0
        self.badHal1Count = 0
        self.badHal2Count = 0
        self.badRgl1Count = 0
        self.badRgl2Count = 0

    def refresh(self, dict):
        """Refresh the pane display."""
        self.update(dict)


    def update(self, dict):
        """Update the lights and display values."""
        # Update the probe position
        pos = dict['TSCL.CAL_POS'].value()
        if  pos == None:
            self.PLabelTxt.set("CAL Probe <No Data>")
        else:
            self.PLabelTxt.set("CAL Probe %+3.3f mm" % (pos))

        # Get the raw data and extract 16 2-bit single-lamp status values
        hct_lamp1 = dict['TSCV.CAL_HCT_LAMP1'].value()
        hct_lamp2 = dict['TSCV.CAL_HCT_LAMP2'].value()
        hal_lamp1 = dict['TSCV.CAL_HAL_LAMP1'].value()
        hal_lamp2 = dict['TSCV.CAL_HAL_LAMP2'].value()
        rgl_lamp1 = dict['TSCV.CAL_RGL_LAMP1'].value()
        rgl_lamp2 = dict['TSCV.CAL_RGL_LAMP2'].value()
        if  hct_lamp1 == None:
            hct1Cs    = None
            hct1NsOpt = None
            hct1P1    = None
            hct1P2    = None
        else:
            hct1Cs    =  hct_lamp1 & 0x03
            hct1NsOpt = (hct_lamp1 & 0x0c) >> 2  
            hct1P1    = (hct_lamp1 & 0x30) >> 4  
            hct1P2    = (hct_lamp1 & 0xc0) >> 6  
        if  hct_lamp2 == None:
            hct2Cs    = None
            hct2NsOpt = None
        else:
            hct2Cs    =  hct_lamp2 & 0x03
            hct2NsOpt = (hct_lamp2 & 0x0c) >> 2  
        if  hal_lamp1 == None:
            hal1Cs    = None
            hal1NsOpt = None
            hal1NsIr  = None
        else:
            hal1Cs    =  hal_lamp1 & 0x03
            hal1NsOpt = (hal_lamp1 & 0x0c) >> 2  
            hal1NsIr  = (hal_lamp1 & 0x30) >> 4  
        if  hal_lamp2 == None:
            hal2Cs    = None
            hal2NsOpt = None
            hal2NsIr  = None
        else:
            hal2Cs    =  hal_lamp2 & 0x03
            hal2NsOpt = (hal_lamp2 & 0x0c) >> 2  
            hal2NsIr  = (hal_lamp2 & 0x30) >> 4  
        if  rgl_lamp1 == None:
            rgl1Cs    = None
            rgl1NsIr  = None
        else:
            rgl1Cs    =  rgl_lamp1 & 0x03
            rgl1NsIr  = (rgl_lamp1 & 0x30) >> 4  
        if  rgl_lamp2 == None:
            rgl2Cs    = None
            rgl2NsIr  = None
        else:
            rgl2Cs    =  rgl_lamp2 & 0x03
            rgl2NsIr  = (rgl_lamp2 & 0x30) >> 4  
        lampArray = (hct1Cs, hct1NsOpt, hct1P1, hct1P2, hct2Cs, hct2NsOpt, 
                     hal1Cs, hal1NsOpt, hal1NsIr, hal2Cs, hal2NsOpt, hal2NsIr, 
                     rgl1Cs, rgl1NsIr, rgl2Cs, rgl2NsIr)

        # Count the number of lamps that are ON
        numberOn = 0
        for  i in range(0, 16):
            if  lampArray[i] == 0x01:     # ON
                numberOn += 1

        # Process Fe-Ar status (CAL_HCT_LAMP1)
        if  hct_lamp1 == None:
            TelStatLog.TelStatLog( CalErrNoDataHctLamp1,
                "ERROR (CalPane:update):  " +
                "No data available for %s Lamp Status (TSCV.CAL_HCT_LAMP1)" % CALPANEHCT1LABEL)
            self.badHct1Count += 1
            if  self.badHct1Count > 1:
                self.LightHCT1.update(3, "No Data")
            # else no update on this lamp
            if  self.badHct1Count == 2:
              TelStatLog.TelStatLog( CalErrNoDataHctLamp1,
                "ERROR (CalPane:update):  " +
                "No data available for %s Lamp Status (TSCV.CAL_HCT_LAMP1)" % CALPANEHCT1LABEL)
        elif  hct1Cs    == 0x03 or hct1Cs    == 0x00 or     \
              hct1NsOpt == 0x03 or hct1NsOpt == 0x00 or     \
              hct1P1    == 0x03 or hct1P1    == 0x00 or     \
              hct1P2    == 0x03 or hct1P2    == 0x00:       # Invalid values
            self.badHct1Count += 1
            if  self.badHct1Count > 1:
                self.LightHCT1.update(3, "%02x" % hct_lamp1 )
            # else no update on this lamp
            TelStatLog.TelStatLog( CalErrUndefDataHctLamp1,
                "ERROR (CalPane:update):  " +
                "Undefined %s Lamp Status (TSCV.CAL_HCT_LAMP1) = %02x" % (CALPANEHCT1LABEL, hct_lamp1))
        elif  hct1Cs == 0x01 or hct1NsOpt == 0x01 or     \
              hct1P1 == 0x01 or hct1P2    == 0x01:          # ON
            self.badHct1Count = 0     # reset
            if  numberOn > 1:
                self.LightHCT1.update(2)                    # ON yellow
            else:
                self.LightHCT1.update(1)                    # ON green
            amp = dict['TSCL.CAL_HCT1_AMP'].value()
            if  amp != None:
                self.ALabelTxt.set("%+5.3fmA" % (amp))
            else:
                self.ALabelTxt.set("<No Data>")
        else:                                               # OFF
            self.badHct1Count = 0     # reset
            self.LightHCT1.update(0)

        # Process Th-Ar status (CAL_HCT_LAMP2)
        if  hct_lamp2 == None:
            self.badHct2Count += 1
            if  self.badHct2Count > 1:
                self.LightHCT2.update(3, "No Data")
            # else no update on this lamp
            if  self.badHct2Count == 2:
              TelStatLog.TelStatLog( CalErrNoDataHctLamp2,
                "ERROR (CalPane:update):  " +
                "No data available for %s Lamp Status (TSCV.CAL_HCT_LAMP2)" % CALPANEHCT2LABEL)
        elif  hct2Cs    == 0x03 or hct2Cs    == 0x00 or     \
              hct2NsOpt == 0x03 or hct2NsOpt == 0x00:       # Invalid values
            TelStatLog.TelStatLog( CalErrUndefDataHctLamp2,
                "ERROR (CalPane:update):  " +
                "Undefined %s Lamp Status (TSCV.CAL_HCT_LAMP2) = %02x" % (CALPANEHCT2LABEL, hct_lamp2))
            self.badHct2Count += 1
            if  self.badHct2Count > 1:
                self.LightHCT2.update(3, "%02x" % hct_lamp2 )
            # else no update on this lamp
        elif  hct2Cs == 0x01 or hct2NsOpt == 0x01:          # ON
            self.badHct2Count = 0     # reset
            if  numberOn > 1:
                self.LightHCT2.update(2)                    # ON yellow
            else:
                self.LightHCT2.update(1)                    # ON green
            amp = dict['TSCL.CAL_HCT2_AMP'].value()
            if  amp != None:
                self.ALabelTxt.set("%+5.3fmA" % (amp))
            else:
                self.ALabelTxt.set("<No Data>")
        else:                                               # OFF
            self.badHct2Count = 0     # reset
            self.LightHCT2.update(0)

        # Process Hal1 status (CAL_HAL_LAMP1)
        if  hal_lamp1 == None:
            self.badHal1Count += 1
            if  self.badHal1Count > 1:
                self.LightHAL1.update(3, "No Data")
            # else no update on this lamp
            if  self.badHal1Count == 2:
              TelStatLog.TelStatLog( CalErrNoDataHalLamp1,
                "ERROR (CalPane:update):  " +
                "No data available for %s Lamp Status (TSCV.CAL_HAL_LAMP1)" % CALPANEHAL1LABEL)
        elif  hal1Cs    == 0x03 or hal1Cs    == 0x00 or     \
              hal1NsOpt == 0x03 or hal1NsOpt == 0x00 or     \
              hal1NsIr  == 0x03 or hal1NsIr  == 0x00:       # Invalid values
            TelStatLog.TelStatLog( CalErrUndefDataHalLamp1,
                "ERROR (CalPane:update):  " +
                "Undefined %s Lamp Status (TSCV.CAL_HAL_LAMP1) = %02x" % (CALPANEHAL1LABEL, hal_lamp1))
            self.badHal1Count += 1
            if  self.badHal1Count > 1:
                self.LightHAL1.update(3, "%02x" % hal_lamp1 )
            # else no update on this lamp
        elif  hal1Cs == 0x01 or hal1NsOpt == 0x01 or hal1NsIr == 0x01:   # ON
            self.badHal1Count = 0     # reset
            if  numberOn > 1:
                self.LightHAL1.update(2)                    # ON yellow
            else:
                self.LightHAL1.update(1)                    # ON green
            amp = dict['TSCL.CAL_HAL1_AMP'].value()
            if  amp != None:
                self.ALabelTxt.set("%+5.3fmA" % (amp))
            else:
                self.ALabelTxt.set("<No Data>")
        else:                                               # OFF
            self.badHal1Count = 0     # reset
            self.LightHAL1.update(0)

        # Process Hal2 status (CAL_HAL_LAMP2)
        if  hal_lamp2 == None:
            self.badHal2Count += 1
            if  self.badHal2Count > 1:
                self.LightHAL2.update(3, "No Data")
            # else no update on this lamp
            if  self.badHal2Count == 2:
              TelStatLog.TelStatLog( CalErrNoDataHalLamp2,
                "ERROR (CalPane:update):  " +
                "No data available for %s Lamp Status (TSCV.CAL_HAL_LAMP2)" % CALPANEHAL2LABEL)
        elif  hal2Cs    == 0x03 or hal2Cs    == 0x00 or     \
              hal2NsOpt == 0x03 or hal2NsOpt == 0x00 or     \
              hal2NsIr  == 0x03 or hal2NsIr  == 0x00:       # Invalid values
            TelStatLog.TelStatLog( CalErrUndefDataHalLamp2,
                "ERROR (CalPane:update):  " +
                "Undefined %s Lamp Status (TSCV.CAL_HAL_LAMP2) = %02x" % (CALPANEHAL2LABEL, hal_lamp2))
            self.badHal2Count += 1
            if  self.badHal2Count > 1:
                self.LightHAL2.update(3, "%02x" % hal_lamp2 )
            # else no update on this lamp
        elif  hal2Cs == 0x01 or hal2NsOpt == 0x01 or hal2NsIr == 0x01:   # ON
            self.badHal2Count = 0     # reset
            if  numberOn > 1:
                self.LightHAL2.update(2)                    # ON yellow
            else:
                self.LightHAL2.update(1)                    # ON green
            amp = dict['TSCL.CAL_HAL2_AMP'].value()
            if  amp != None:
                self.ALabelTxt.set("%+5.3fmA" % (amp))
            else:
                self.ALabelTxt.set("<No Data>")
        else:                                               # OFF
            self.badHal2Count = 0     # reset
            self.LightHAL2.update(0)

        # Process Rgl1 status (CAL_RGL_LAMP1)
        if  rgl_lamp1 == None:
            self.badRgl1Count += 1
            if  self.badRgl1Count > 1:
                self.LightRGL1.update(3, "No Data")
            # else no update on this lamp
            if  self.badRgl1Count == 2:
              TelStatLog.TelStatLog( CalErrNoDataRglLamp1,
                "ERROR (CalPane:update):  " +
                "No data available for %s Lamp Status (TSCV.CAL_RGL_LAMP1)" % CALPANERGL1LABEL)
        elif  rgl1Cs    == 0x03 or rgl1Cs    == 0x00 or     \
              rgl1NsIr  == 0x03 or rgl1NsIr  == 0x00:       # Invalid values
            TelStatLog.TelStatLog( CalErrUndefDataRglLamp1,
                "ERROR (CalPane:update):  " +
                "Undefined %s Lamp Status (TSCV.CAL_RGL_LAMP1) = %02x" % (CALPANERGL1LABEL, rgl_lamp1))
            self.badRgl1Count += 1
            if  self.badRgl1Count > 1:
                self.LightRGL1.update(3, "%02x" % rgl_lamp1 )
            # else no update on this lamp
        elif  rgl1Cs == 0x01 or rgl1NsIr == 0x01:           # ON
            self.badRgl1Count = 0     # reset
            if  numberOn > 1:
                self.LightRGL1.update(2)                    # ON yellow
            else:
                self.LightRGL1.update(1)                    # ON green
            self.ALabelTxt.set("          ")
        else:                                               # OFF
            self.badRgl1Count = 0     # reset
            self.LightRGL1.update(0)

        # Process Rgl2 status (CAL_RGL_LAMP2)
        if  rgl_lamp2 == None:
            self.badRgl2Count += 1
            if  self.badRgl2Count > 1:
                self.LightRGL2.update(3, "No Data")
            # else no update on this lamp
            if  self.badRgl2Count == 2:
              TelStatLog.TelStatLog( CalErrNoDataRglLamp2,
                "ERROR (CalPane:update):  " +
                "No data available for %s Lamp Status (TSCV.CAL_RGL_LAMP2)" % CALPANERGL2LABEL)
        elif  rgl2Cs    == 0x03 or rgl2Cs    == 0x00 or     \
              rgl2NsIr  == 0x03 or rgl2NsIr  == 0x00:       # Invalid values
            TelStatLog.TelStatLog( CalErrUndefDataRglLamp2,
                "ERROR (CalPane:update):  " +
                "Undefined %s Lamp Status (TSCV.CAL_RGL_LAMP2) = %02x" % (CALPANERGL2LABEL, rgl_lamp2))
            self.badRgl2Count += 1
            if  self.badRgl2Count > 1:
                self.LightRGL2.update(3, "%02x" % rgl_lamp2 )
            # else no update on this lamp
        elif  rgl2Cs == 0x01 or rgl2NsIr == 0x01:           # ON
            self.badRgl2Count = 0     # reset
            if  numberOn > 1:
                self.LightRGL2.update(2)                    # ON yellow
            else:
                self.LightRGL2.update(1)                    # ON green
            self.ALabelTxt.set("          ")
        else:                                               # OFF
            self.badRgl2Count = 0     # reset
            self.LightRGL2.update(0)

    
    def resize(self, paneWidth):
        """Change the pane to fit the new geometry."""

        # Update the window so that the correct geometry is reported
        # must be done to assure that geometry != 1x1+0+0
        self.update_idletasks()

        # Internally, the pane uses a grid to control the placement of
        # the component widgets.  Since we want to keep the lights
        # together, most of the resize is applied to the labels on
        # either side.
        colMinWidth     = int((paneWidth - self.LightHCT1.winfo_width() - \
                                self.LightHCT2.winfo_width() - \
                                self.LightHAL1.winfo_width()) / 2.0)

        self.columnconfigure( 0, minsize=colMinWidth )
        self.columnconfigure( 4, minsize=colMinWidth )

        # After the grid is resized, we can resize the pane itself
        self.configure( width=paneWidth )


    def rePack(self):
        """First resize, then re-place this pane.
           This should ONLY be called if this pane is used in a top-level
              geometry pane, NOT if it is a page in a Notebook."""
        self.pack(anchor=NW)


    def geomCB(self, event):
        """Callback for to print geometry."""
        print "Cal pane:        ", self.winfo_geometry()


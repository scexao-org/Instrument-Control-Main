#! /usr/local/bin/python
# PointingPane.py -- Bruce Bon -- 2005-12-05 16:02
# Display pane for Telescope Pointing Status

######################################################################
################   import needed modules   ###########################
######################################################################

import os
import sys

import Tkinter
from Tkconstants import *
import Pmw
import string

from TelStat_cfg import *
from StatIO import *
from DispType import *

######################################################################
################   assign needed globals   ###########################
######################################################################

statusKeys = ( 'STATS.EQUINOX', 'TSCS.ALPHA','TSCS.DELTA','TSCS.AZ','TSCS.EL', 
                'TSCS.ALPHA_C','TSCS.DELTA_C','TSCS.AZ_CMD','TSCS.EL_CMD',
                'TELSTAT.ROT_POS', 'TELSTAT.ROT_CMD' )

######################################################################
################   declare class for the pane   ######################
######################################################################

# Telescope Pointing Status Pane class
class PointingPane(Tkinter.Frame,StatPaneBase):
    MWin = 0

    def __init__(self,parent):
        """Telescope Pointing Status Pane constructor."""
        Tkinter.Frame.__init__(self, parent, class_="PointingPane", \
            borderwidth=paneBorderWidth, relief=paneBorderRelief)
        StatPaneBase.__init__(self, statusKeys, 'PointingPane' )
        self.MWin = parent
        self["bg"] = POINTPANEBACKGROUND
        self.createWidgets()
        self.equinox = 'Unknown Equinox'
#?      print "\n", self, " options:\n", self.config()  # debug


    def resize( self, paneWidth, paneHeight ):
        """Resize this pane."""
        row0height = int( paneHeight * 0.25 ) - 1
        row1height = int( paneHeight * 0.5 ) - 2
        row2height = int( paneHeight * 0.25 ) - 1
        col0width  = int( paneWidth * 0.08 ) - 1
        col12width = int( paneWidth * 0.24 ) - 1
        col35width = int( paneWidth * 0.14 ) - 1
        self.rowconfigure(    0, minsize=row0height )
        self.rowconfigure(    1, minsize=row1height )
        self.rowconfigure(    2, minsize=row2height )
        self.columnconfigure( 0, minsize=col0width )
        self.columnconfigure( 1, minsize=col12width )
        self.columnconfigure( 2, minsize=col12width )
        self.columnconfigure( 3, minsize=col35width )
        self.columnconfigure( 4, minsize=col35width )
        self.columnconfigure( 5, minsize=col35width )

    def rePack(self):
        """First resize, then re-place this pane.
           This should ONLY be called if this pane is used in a top-level
              geometry pane, NOT if it is a page in a Notebook."""
        widWidth  = root.winfo_width()
        widHeight = root.winfo_height()
        self.resize( widWidth, widHeight )
        self.pack( anchor=NW)

# Map of widgets onto grid:
#       0           1           2           3           4            5
# 0                 raLabel     decLabel    azLabel     elLabel     rotLabel
# 1     curLabel    raValue     decValue    azValue     elValue     rotValue
# 2     cmdLabel    raCmdVal    decCmdVal   azCmdVal    elCmdVal    rotCmdVal
#
    def createWidgets(self):
        """Create widgets for PointingPane."""

        self.raLabel = Tkinter.Label(self, text="RA(Unknown Equinox)", 
                bg = self["bg"], width = 1, height = 1,   # minimize text size
                fg = POINTPANEFOREGROUND, font=POINTPANETITLESFONT)
        self.raLabel.grid(row=0,column=1,sticky=N+E+S+W)

        self.decLabel = Tkinter.Label(self,text="DEC(Unknown Equinox)",
                bg = self["bg"], width = 1, height = 1,   # minimize text size
                fg = POINTPANEFOREGROUND, font=POINTPANETITLESFONT)
        self.decLabel.grid(row=0,column=2,sticky=N+E+S+W)

        self.azLabel = Tkinter.Label(self,text="      Az(deg:S=0,W=90)",
                bg = self["bg"], width = 1, height = 1,   # minimize text size
                fg = POINTPANEFOREGROUND, font=POINTPANETITLESFONT)
        self.azLabel.grid(row=0,column=3,sticky=N+E+S+W)

        self.elLabel = Tkinter.Label(self,text="    El(deg)", bg = self["bg"],
                width = 1, height = 1,          # minimize text size
                fg = POINTPANEFOREGROUND, font=POINTPANETITLESFONT)
        self.elLabel.grid(row=0,column=4,sticky=N+E+S+W)

        self.rotLabel = Tkinter.Label(self,text="    Rot(deg)", bg = self["bg"],
                width = 1, height = 1,          # minimize text size
                fg = POINTPANEFOREGROUND, font=POINTPANETITLESFONT)
        self.rotLabel.grid(row=0,column=5,sticky=N+E+S+W)

        self.curLabel = Tkinter.Label(self,text="Current", bg = self["bg"],
                width = 1, height = 1,          # minimize text size
                fg = POINTPANEFOREGROUND, font=POINTPANETITLESFONT)
        self.curLabel.grid(row=1,column=0,sticky=N+E+S+W)

        self.cmdLabel = Tkinter.Label(self,text="Commanded", bg = self["bg"],
                width = 1, height = 1,          # minimize text size
                fg = POINTPANEFOREGROUND, font=POINTPANETITLESFONT)
        self.cmdLabel.grid(row=2,column=0,sticky=N+E+S+W)


        self.raValue = Tkinter.Label(self, bg = self["bg"],
                width = 1, height = 1,          # minimize text size
                fg = POINTPANEFOREGROUND, font=POINTPANECURFONT)
        self.raValue.grid(row=1,column=1, sticky=N+E+S+W)

        self.decValue = Tkinter.Label(self, bg = self["bg"],
                width = 1, height = 1,          # minimize text size
                fg = POINTPANEFOREGROUND, font=POINTPANECURFONT)
        self.decValue.grid(row=1,column=2, sticky=N+E+S+W)

        self.azValue = Tkinter.Label(self, bg = self["bg"],
                width = 1, height = 1,          # minimize text size
                fg = POINTPANEFOREGROUND, font=POINTPANECURFONT)
        self.azValue.grid(row=1,column=3, sticky=N+E+S+W)

        self.elValue = Tkinter.Label(self, bg = self["bg"],
                width = 1, height = 1,          # minimize text size
                fg = POINTPANEFOREGROUND, font=POINTPANECURFONT)
        self.elValue.grid(row=1,column=4, sticky=N+E+S+W)

        self.rotValue = Tkinter.Label(self, bg = self["bg"],
                width = 1, height = 1,          # minimize text size
                fg = POINTPANEFOREGROUND, font=POINTPANECURFONT)
        self.rotValue.grid(row=1,column=5, sticky=N+E+S+W)


        self.raCmdVal = Tkinter.Label(self, bg = self["bg"],
                width = 1, height = 1,          # minimize text size
                fg = POINTPANEFOREGROUND, font=POINTPANECMDFONT)
        self.raCmdVal.grid(row=2,column=1, sticky=N+E+S+W)

        self.decCmdVal = Tkinter.Label(self, bg = self["bg"],
                width = 1, height = 1,          # minimize text size
                fg = POINTPANEFOREGROUND, font=POINTPANECMDFONT)
        self.decCmdVal.grid(row=2,column=2, sticky=N+E+S+W)

        self.azCmdVal = Tkinter.Label(self, bg = self["bg"],
                width = 1, height = 1,          # minimize text size
                fg = POINTPANEFOREGROUND, font=POINTPANECMDFONT)
        self.azCmdVal.grid(row=2,column=3, sticky=N+E+S+W)

        self.elCmdVal = Tkinter.Label(self, bg = self["bg"],
                width = 1, height = 1,          # minimize text size
                fg = POINTPANEFOREGROUND, font=POINTPANECMDFONT)
        self.elCmdVal.grid(row=2,column=4, sticky=N+E+S+W)

        self.rotCmdVal = Tkinter.Label(self, bg = self["bg"],
                width = 1, height = 1,          # minimize text size
                fg = POINTPANEFOREGROUND, font=POINTPANECMDFONT)
        self.rotCmdVal.grid(row=2,column=5, sticky=N+E+S+W)



    def refresh(self, dict):
        """Refresh pane with updated values from dict."""
#?      print "    Pane ", self.myName, " received refresh call:",
        # Debugging printout
        #? for  key in self.statusKeys:
        #?     print "      %-20s   %s" % \
        #?      (key, StatusDictionary.StatusDictionary[key][0].format())
#?      print " %s   %s" % \
#?   ('TSCS.ALPHA', StatusDictionary.StatusDictionary['TSCS.ALPHA'][0].format())

        # Do whatever is necessary to refresh the pane!
        eqn = dict['STATS.EQUINOX'].value()
        if  eqn == None or eqn == 'None':
            equinox = 'Unknown Equinox'
        else:
            #equinox = string.strip( str(eqn) )   # old
            equinox = '%.1f' % eqn                # as of version 2.1.1, float
        if  equinox != self.equinox:
            self.raLabel.config(  text="RA(%s)" % equinox )
            self.decLabel.config( text="DEC(%s)" % equinox )
            self.equinox = equinox

        self.raValue.config( text=dict['TSCS.ALPHA'].format_HrMinSec(3, False) )
        self.decValue.config( text=dict['TSCS.DELTA'].format_DegMinSec(2) )
        self.azValue.config( text=dict['TSCS.AZ'].format_Deg() )
        self.elValue.config( text=dict['TSCS.EL'].format_Deg() )

        self.raCmdVal.config( text=dict['TSCS.ALPHA_C'].format_HrMinSec(3, False) )
        self.decCmdVal.config( text=dict['TSCS.DELTA_C'].format_DegMinSec(2))
        self.azCmdVal.config( text=dict['TSCS.AZ_CMD'].format_Deg() )
        self.elCmdVal.config( text=dict['TSCS.EL_CMD'].format_Deg() )

        self.rotValue.config(  text=dict['TELSTAT.ROT_POS'].format_Deg() )
        self.rotCmdVal.config( text=dict['TELSTAT.ROT_CMD'].format_Deg() )

######################################################################
################   test application   ################################
######################################################################

#?  Following for debugging only ############
import time
curtime         = time.time()
prevtime        = time.time()
statRefresh     = True
def refresh():
    global curtime, prevtime, statRefresh
    curtime = time.time()
    deltatime = curtime - prevtime
    print "LimitsPane.refresh() called, time = %.6f, delta = %.6f" % \
                                                        (curtime, deltatime)
    StatIO_service()
    prevtime = curtime
    testPointingPane.refresh( StatusDictionary.StatusDictionary )
    if  statRefresh:
        root.after( 15000, refresh )    # avoids possible frame overflow

if __name__ == '__main__':

    from StatIO import *
    StatIOsource = StatIO_ScreenPrintSim
    TelStat_cfg.OSSC_screenPrintPath = OSSC_SCREENPRINTSIMPATH

    # Create the base frame for the widgets
    root = Tkinter.Tk()
    Pmw.initialise(root)
    root.title("Pointing Pane Test")
    root.geometry("1280x115-0+0")

    # Create an instance 
    testPointingPane = PointingPane( root )
    testPointingPane.grid( row=0, column=0 )

    # Define event handler for resizing
    def mouseEnter(event):
        widWidth = root.winfo_width()
        widHeight = root.winfo_height()
        print "\n***** mouseEnter is resizing to %d x %d *****" % \
                ( widWidth, widHeight )
        testPointingPane.resize( widWidth, widHeight )

    # Bind mouseEnter to mouse entry into the window    
    root.bind("<Enter>", mouseEnter)

    # Print root geometry
    root.update_idletasks()  # must be done to assure that geometry != 1x1+0+0
    print "root :                       ", root.geometry()
    print "testPointingPane :   ", testPointingPane.winfo_geometry(), "\n"
    testPointingPane.resize( 1265, 110 )
    root.update_idletasks() # must be done to assure that geometry is up to date
    print "root :                       ", root.geometry()
    print "testPointingPane :   ", testPointingPane.winfo_geometry(), "\n"

    refresh()
    root.mainloop()


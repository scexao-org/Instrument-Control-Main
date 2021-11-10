#! /usr/local/bin/python
# LimitsPane.py -- Bruce Bon -- 2006-12-04  16:29

# Display pane for telescope limits scales

######################################################################
################   import needed modules   ###########################
######################################################################

import os
import sys

import Tkinter
from Tkconstants import *
import Pmw

from TelStat_cfg import *
from StatIO import *
from DispType import *
from Alert import *
#from AudioPlayer import *
import LimitsWidget

######################################################################
################   assign needed globals   ###########################
######################################################################

StatusKeys = (  'TELSTAT.FOCUS', 'TSCS.AZ', 'TSCS.AZ_CMD',
                'TELSTAT.ROT_POS', 'TELSTAT.ROT_CMD',
                'TSCL.LIMIT_FLAG',  'TSCL.LIMIT_AZ', 'TSCL.LIMIT_ROT', 
                'TSCV.AGTheta',      'STATL.AG_THETA_CMD',
                'TELSTAT.M1_CLOSED', 'TELSTAT.DOME_CLOSED', 
                'TELSTAT.EL_STOWED', 'TELSTAT.SLEWING' )

AzLimits = (-269.5, -260.0, 260.0, 269.5)

RotatorLimitsDict = \
      { FOCUS_PF_OPT:
                (ROT_PF_LOWALARM,    ROT_PF_LOWWARNING,
                 ROT_PF_HIGHWARNING, ROT_PF_HIGHALARM),
        FOCUS_PF_IR:
                (ROT_PF_IR_LOWALARM,    ROT_PF_IR_LOWWARNING,
                 ROT_PF_IR_HIGHWARNING, ROT_PF_IR_HIGHALARM),
        FOCUS_PF_OPT2:
                (ROT_PF_OPT2_LOWALARM,    ROT_PF_OPT2_LOWWARNING,
                 ROT_PF_OPT2_HIGHWARNING, ROT_PF_OPT2_HIGHALARM),
        FOCUS_NS_OPT:
                (ROT_NS_LOWALARM,    ROT_NS_LOWWARNING,
                 ROT_NS_HIGHWARNING, ROT_NS_HIGHALARM),
        FOCUS_NS_IR:
                (ROT_NS_LOWALARM,    ROT_NS_LOWWARNING,
                 ROT_NS_HIGHWARNING, ROT_NS_HIGHALARM),
        FOCUS_CS_OPT:
                (ROT_CS_LOWALARM,    ROT_CS_LOWWARNING,
                 ROT_CS_HIGHWARNING, ROT_CS_HIGHALARM),
        FOCUS_CS_IR:
                (ROT_CS_LOWALARM,    ROT_CS_LOWWARNING,
                 ROT_CS_HIGHWARNING, ROT_CS_HIGHALARM),
        None:
                (ROT_CS_LOWALARM,    ROT_CS_LOWWARNING,
                 ROT_CS_HIGHWARNING, ROT_CS_HIGHALARM)  #default values
      }

AGLimitsDict = \
      { FOCUS_NS_OPT:   (-269.5, -260, 260, 269.5),
        FOCUS_NS_IR:    (-269.5, -260, 260, 269.5),
        FOCUS_CS_OPT:   (-184.5, -175, 175, 184.5),
        FOCUS_CS_IR:    (-184.5, -175, 175, 184.5),
        None:           (-270, -250, 250, 270)          #default values
      }

# TSCL.LIMIT_FLAG values:
LIM_FLAG_AZ      = 0x04
LIM_FLAG_ROT     = 0x08
LIM_FLAG_BIGROT  = 0x10

######################################################################
################   declare class for the pane   ######################
######################################################################

# Telescope Limit Scales Pane class
class LimitsPane(Tkinter.Frame,StatPaneBase):

    def __init__(self,parent):
        """Telescope Limit Scales Pane constructor."""
        Tkinter.Frame.__init__(self, parent, class_="LimitsPane", \
            borderwidth=paneBorderWidth, relief=paneBorderRelief)
        StatPaneBase.__init__(self, StatusKeys, 'LimitsPane' )
        self.MWin = 0
        self.azWidget = 0
        self.rotWidget = 0
        self.agProbeWidget = 0
        self.AGvisible  = False
        self.RotVisible = True
        self.Focus = None
        self.widWidth  = 100     # defaults, not likely to be used
        self.widHeight =  40
        self.MWin = parent
        self["bg"] = LIMPANEBACKGROUND
        #? self["bg"] = "red"   # debugging
        self.createWidgets()
#?      print "\n", self, " options:\n", self.config()  # debug


    def resize( self, widWidth=-1, widHeight=-1 ):
        """Resize this pane."""
        # resize methods may NOT access winfo functions to get their own
        # widths/heights, because such cannot be forced to be correct size
        #? print "\nLimitsPane.resize: widWidth x widHeight = %d x %d" % \
        #?      ( widWidth, widHeight )

        # Get values from arguments or saved values
        if  widWidth < 0:
            widWidth = self.widWidth
        else:
            self.widWidth = widWidth
        if  widHeight < 0:
            widHeight = self.widHeight
        else:
            self.widHeight = widHeight

        # Adjust for borders and minimum size
        widWidth  -= paneBorderWidth*3
        if  widHeight < 0:
            widHeight = 40              # less is unreasonable!
        #widHeight -= paneBorderWidth*4
        if  widWidth < 100:
            widWidth = 100              # less is unreasonable!
        if  widHeight < 40:
            widHeight = 40              # less is unreasonable!

        # Compute column width and row height
        colMinWidth     = widWidth
        n = 3.0
#?      if  self.AGvisible:
#?          n = 3.0
#?      else:
#?          n = 2.0
        rowMinHeight    = int( widHeight / n )
        #? print "LimitsPane width x height        = %d x %d" % \
        #?      ( self.winfo_width(), self.winfo_height() )
        #? print "     widWidth x widHeight = %d x %d" % \
        #?      ( widWidth, widHeight )
        #? print "           Resizing to %d x %d cells" % \
        #?      ( colMinWidth, rowMinHeight )

        # Do the actual resize
        self.rowconfigure(    0, minsize=rowMinHeight )
        self.rowconfigure(    1, minsize=rowMinHeight )
        self.columnconfigure( 0, minsize=colMinWidth )
        #? print "           Resizing azWidget:"
        self.azWidget.resize( colMinWidth, rowMinHeight )
        #? print "           Resizing rotWidget:"
        if  self.RotVisible:    # Frame has no resize method, so can't call it
            self.rotWidget.resize( colMinWidth, rowMinHeight )
        self.rowconfigure( 2, minsize=rowMinHeight )
        if  self.AGvisible:     # Frame has no resize method, so can't call it
            #? print "           Resizing agProbeWidget:"
            self.agProbeWidget.resize( colMinWidth, rowMinHeight )

    def rePack(self):
        """First resize, then repack this pane."""
        self.resize()
        self.pack( anchor=NW)

# Map of widgets onto grid:
#       0           
# 0     azWidget            
# 1     rotWidget
# 2     agProbeWidget
#
    def createWidgets(self):
        """Create widgets for LimitsPane."""

        # Initialize alert suppression flags to False
        self.suppressAlrts    = False
        self.azSuppWarnAlrts  = False
        self.rotSuppAllAlrts  = False
        self.rotSuppWarnAlrts = False

        # Create azimuth audio alert and widget
        self.azLimAlert  = AudioAlert( 
                        warnAudio=AU_WARN_AZ_LIMIT, warnMinInterval=180, 
                        alarmAudio=AU_ALARM_AZ_LIMIT, alarmMinInterval=60 )
        self.azWidget = \
           LimitsWidget.LimitsWidget( self, 'azWidget', 'Az', self.azLimAlert )
        self.azWidget.grid( row=0, column=0 )
        self.azWidget.setLimits( AzLimits )

        # Create rotator widget
        self.rotLimAlert = AudioAlert( 
                        warnAudio=AU_WARN_ROT_LIMIT, warnMinInterval=180, 
                        alarmAudio=AU_ALARM_ROT_LIMIT,alarmMinInterval=60 )
        self.rotWidget = LimitsWidget.LimitsWidget( self, 'rotWidget', \
                'Rotator Prime Optical', self.rotLimAlert )
        self.rotWidget.grid( row=1, column=0 )

        # Create AG probe widget
        self.agLimAlert  = AudioAlert( 
                        warnAudio=AU_WARN_AG_LIMIT, warnMinInterval=180, 
                        alarmAudio=AU_ALARM_AG_LIMIT, alarmMinInterval=60 )
        self.agProbeWidget = Tkinter.Frame( self )
        self.agProbeWidget["bg"] = LIMPANEBACKGROUND
        self.agProbeWidget["width"]  = 420
        self.agProbeWidget["height"] = 60
        self.agProbeWidget.grid( row=2, column=0 )


    def refresh(self, dict):
        """Refresh pane with updated values from dict."""
#?      print " %s   %s" % \
#?   ('TSCS.ALPHA', StatusDictionary.StatusDictionary['TSCS.ALPHA'][0].format())
        # get all data needed for update
        Focus           = dict['TELSTAT.FOCUS'].value()
        AZ              = dict['TSCS.AZ'].value_ArcDeg()
        AZ_CMD          = dict['TSCS.AZ_CMD'].value_ArcDeg()
        INSROTPOS       = dict['TELSTAT.ROT_POS'].value_ArcDeg()
        INSROTCMD       = dict['TELSTAT.ROT_CMD'].value_ArcDeg()
        AGTheta         = dict['TSCV.AGTheta'].value_ArcDeg()
        AG_THETA_CMD    = dict['STATL.AG_THETA_CMD'].value_ArcDeg()
        Slewing         = dict['TELSTAT.SLEWING'].value()

        # Find time-to-limit values to use
        LimitFlags      = dict['TSCL.LIMIT_FLAG'].value()
        if  LimitFlags == None:
            bigrot      = None
        else:
            bigrot      = LimitFlags & LIM_FLAG_BIGROT  # means rot time > 720
        LimitAZ         = dict['TSCL.LIMIT_AZ'].value_Min()
        LimitRot        = dict['TSCL.LIMIT_ROT'].value_Min()
        # Force AZ value to be 721 if LimitFlags says AZ value is infinite
        if  (LimitFlags != None) and not (LimitFlags & LIM_FLAG_AZ):
            LimitAZ     = 721
        # Force values to be 721 if bigrot or LimitFlags says value is infinite
        if  bigrot or \
            ((LimitFlags != None)  and not (LimitFlags & LIM_FLAG_ROT)):
            LimitRot    = 721

        #? print "LimitAZ = %f, LimitRot = %f" % (LimitAZ, dict['TSCL.LIMIT_ROT'].value_Min() )
        #? print "LimitElLow = %f, LimitElHigh = %f" % (dict['TSCL.LIMIT_EL_LOW'].value_Min(), dict['TSCL.LIMIT_EL_HIGH'].value_Min())

        # Determine whether to sound audio alert when approaching limits.
        # The conditions used here are computed by the GlobalStates.py module.
        # They are taken to mean that the telescope is currently inactive and 
        # that any limit alert condition may be a consequence of data that is 
        # not meaningful when the telescope is inactive.
        suppressAlrts = False
        if  dict['TELSTAT.M1_CLOSED'].value() or     \
            dict['TELSTAT.DOME_CLOSED'].value() or   \
            dict['TELSTAT.EL_STOWED'].value():
            suppressAlrts = True

        #? suppressAlrts = False   # for testing only ????????

        # If the Limit AZ value is defined and > 30 minutes, 
        # then suppress any AZ limits warning alert
        azSuppWarnAlrts = suppressAlrts
        if  LimitAZ != None and LimitAZ > 30.0:
            azSuppWarnAlrts = True
        #? print "0 suppressAlrts = %s, azSuppWarnAlrts = %s" % (`suppressAlrts`, `azSuppWarnAlrts`)
        if  azSuppWarnAlrts != self.azSuppWarnAlrts:     # reset if changed
            self.azWidget.suppressAlerts( azSuppWarnAlrts, level=WARNING )
            self.azSuppWarnAlrts = azSuppWarnAlrts

        # Call azWidget.refresh()
        if  suppressAlrts != self.suppressAlrts:        # reset if changed
            self.azWidget.suppressAlerts( suppressAlrts, level=ALARM )
        self.azWidget.refresh( AZ, AZ_CMD )

        # Determine focus, set AGvisible, set RotVisible, set Rotator label
        if  Focus == FOCUS_PF_OPT:
            FocusLabel  = 'Prime Optical'
            AGvisible  = False
            RotVisible = True
        elif  Focus == FOCUS_PF_IR:
            FocusLabel  = 'Prime IR'
            AGvisible  = False
            RotVisible = True
        elif  Focus == FOCUS_PF_OPT2:
            FocusLabel  = 'Prime Optical 2'
            AGvisible  = False
            RotVisible = True
        elif  Focus == FOCUS_CS_OPT or Focus == FOCUS_CS_IR:
            FocusLabel  = 'Cassegrain'
            AGvisible  = True
            RotVisible = True
        elif  Focus == FOCUS_NS_OPT:
            FocusLabel  = 'Nasmyth Optical'
            AGvisible  = True
            RotVisible = True
        elif  Focus == FOCUS_NS_IR:
            FocusLabel  = 'Nasmyth IR'
            AGvisible  = True
            RotVisible = True
        else:   # None
            FocusLabel  = '<No Data>'
            AGvisible  = False
            RotVisible = False

        # Create/destroy Rotator widget if visibility or focus has changed
        if  self.RotVisible != RotVisible or self.Focus != Focus:
            self.RotVisible = RotVisible
            if  RotVisible:
                self.rotWidget.grid_remove()
                self.rotWidget.destroy()
                self.rotWidget = LimitsWidget.LimitsWidget( 
                        self, 'rotWidget', 'AGProbe', self.rotLimAlert )
                self.rotWidget.grid( row=1, column=0 )
                self.rotWidget.setLabel( 'Rotator ' + FocusLabel )
                #? print "Setting limits to ", RotatorLimitsDict[Focus]
                self.rotWidget.setLimits( RotatorLimitsDict[Focus] )
            else:
                self.rotWidget.grid_remove()
                self.rotWidget.destroy()
                self.rotWidget = Tkinter.Frame( self )
                self.rotWidget["bg"] = LIMPANEBACKGROUND
                self.rotWidget.grid( row=1, column=0 )
            self.resize()

        # If Rotator visible, compute suppression and call rotWidget.refresh()
        if  RotVisible:
            # Suppress all Rot alerts if suppressAlrts or Slewing.
            rotSuppAllAlrts = suppressAlrts or Slewing
            if  rotSuppAllAlrts != self.rotSuppAllAlrts:    # reset if changed
                self.rotWidget.suppressAlerts( rotSuppAllAlrts, level=ALARM   )
                self.rotSuppAllAlrts = rotSuppAllAlrts
                #? print '1 *rotSuppAllAlrts = ', self.rotSuppAllAlrts
            rotSuppWarnAlrts = rotSuppAllAlrts
            # Suppress warning Rot alerts Limit Rot value > 30 minutes
            if  not rotSuppAllAlrts:        # alarms NOT suppressed
                if  LimitRot != None and LimitRot > 30.0:
                    rotSuppWarnAlrts = True
            #? print '2 *rotSuppAllAlrts = %s, rotSuppWarnAlrts = %s' % (`rotSuppAllAlrts`, `rotSuppWarnAlrts`)
            if  rotSuppWarnAlrts != self.rotSuppWarnAlrts:   # reset if changed
                self.rotWidget.suppressAlerts( rotSuppWarnAlrts, level=WARNING )
                self.rotSuppWarnAlrts = rotSuppWarnAlrts
                #? print '3 *rotSuppAllAlrts = ', self.rotSuppAllAlrts
            # Call rotWidget.refresh()
            #? print '4 self.rotSuppAllAlrts = ', self.rotSuppAllAlrts
            self.rotWidget.refresh( INSROTPOS, INSROTCMD )


        # Get data and call agProbeWidget.refresh()
        if  self.AGvisible != AGvisible or self.Focus != Focus:
            #? print "Focus changed to %0d" % Focus
            self.AGvisible = AGvisible
            if  AGvisible:
                self.agProbeWidget.grid_remove()
                self.agProbeWidget.destroy()
                self.agProbeWidget = LimitsWidget.LimitsWidget( 
                        self, 'agProbeWidget', 'AGProbe', self.agLimAlert )
                self.agProbeWidget.grid( row=2, column=0 )
                self.agProbeWidget.setLabel( 'AGProbe ' + FocusLabel )
                #? print "Setting limits to ", AGLimitsDict[Focus]
                self.agProbeWidget.setLimits( AGLimitsDict[Focus] )
                self.agProbeWidget.suppressAlerts( suppressAlrts, level=WARNING)
                self.agProbeWidget.suppressAlerts( suppressAlrts, level=ALARM  )
            else:
                self.agProbeWidget.grid_remove()
                self.agProbeWidget.destroy()
                self.agProbeWidget = Tkinter.Frame( self )
                self.agProbeWidget["bg"] = LIMPANEBACKGROUND
                self.agProbeWidget.grid( row=2, column=0 )
            self.resize()
        if  AGvisible:
            if  suppressAlrts != self.suppressAlrts:    # reset if changed
                self.agProbeWidget.suppressAlerts( suppressAlrts, level=WARNING)
                self.agProbeWidget.suppressAlerts( suppressAlrts, level=ALARM  )
            self.agProbeWidget.refresh( AGTheta, AG_THETA_CMD )

        self.suppressAlrts = suppressAlrts
        self.Focus = Focus

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
    testLimPane.refresh( StatusDictionary.StatusDictionary )
    if  statRefresh:
        root.after( 100, refresh )      # avoids possible frame overflow

if __name__ == '__main__':

    from StatIO import *
    StatIOsource = StatIO_ScreenPrintSim
    TelStat_cfg.OSSC_screenPrintPath = OSSC_SCREENPRINTSIMPATH

    # Create the base frame for the widgets
    root = Tkinter.Tk()
    Pmw.initialise(root)
    root.title("Limits Pane Test")
    root.geometry("-0+0")

    # Create an instance 
    testLimPane = LimitsPane( root )
    testLimPane.grid( row=0, column=0 )

    # Define event handler for resizing
    def mouseEnter(event):
        widWidth = root.winfo_width()
        widHeight = root.winfo_height()
        print "\n***** mouseEnter is resizing *****"
        testLimPane.resize( widWidth, widHeight )

    # Bind mouseEnter to mouse entry into the window    
    root.bind("<Enter>", mouseEnter)

    # Print root geometry
    root.update_idletasks()  # must be done to assure that geometry != 1x1+0+0
    print "root :       ", root.geometry(), "\n"

    refresh()
    root.mainloop()


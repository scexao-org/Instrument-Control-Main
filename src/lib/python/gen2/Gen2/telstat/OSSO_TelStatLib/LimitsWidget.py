#! /usr/local/bin/python
# LimitsWidget.py -- Bruce Bon -- 2005-12-14  10:42

# Widget to display a value on a limit scale

######################################################################
################   import needed modules   ###########################
######################################################################

import Tkinter
from Tkconstants import *
import Pmw

from TelStat_cfg import *
from Alert import *
import TelStatLog

######################################################################
################   declare class for the pane   ######################
######################################################################

LimWarnThreshExceeded   = LimWarnBase
LimErrLimitExceeded     = LimErrBase

# Limits widget class
class LimitsWidget(Tkinter.Canvas):
    

    def __init__( self, parent, name, varName, alertObj, 
                  widWidth=420, widHeight=60):
        """Limits Widget constructor."""
        Tkinter.Canvas.__init__(self, parent, name=name,
                width=widWidth, height=widHeight )
        self.dataAcquired = False        # a first-time flag
        self.lowAlarm     = -270.0
        self.lowWarning   = -240.0
        self.highWarning  =  240.0
        self.highAlarm    =  270.0
        self.curValue     = -260.0
        self.cmdValue     = -200.0
        self.curValueStr  = '-260.0'
        self.cmdValueStr  = '-200.0'
        self.prevValue    = self.curValue
        self.prevCmdValue = self.cmdValue
        self.varName      =  'xx'
        self.widWidth     =  100
        self.widHeight    =   40
        self.suppressAlrtsWarn  = False     # warning audio alerts turned on
        self.suppressAlrtsAlarm = False     # alarm   audio alerts turned on
        self.parent     = parent
        self["bg"]      = LIMPANEBACKGROUND
        self.varName    = varName
        self.alertObj   = alertObj
        self.allowCurAlert = True       # turn to False if value == None
        self.allowCmdAlert = True       # turn to False if value == None
        self.resize( widWidth, widHeight )
        self.bind("<ButtonRelease-1>", self.geomCB)
#?      print "\n", self, " options:\n", self.config()  # debug

    def setLimits( self, limits ):
        """Reset limit and alarm values."""
        self.lowAlarm    = limits[0]
        self.lowWarning  = limits[1]
        self.highWarning = limits[2]
        self.highAlarm   = limits[3]
        #? print "\nLimitsWidget %s setLimits:" % self.varName
        #? print "      alarms = %f, %f, %f, %f" % \
        #?      (self.lowAlarm, self.highAlarm, self.lowWarning, self.highWarning ) 
        #? print "      widWidth = %.1f, widHeight = %.1f"%\
        #?      (self.widWidth, self.widHeight)
        self.resize( self.widWidth, self.widHeight )

    def setLabel( self, varName ):
        self.varName    = varName
        self.itemconfigure( self.textID, text = varName, fill=LIMPANELABEL )

    def suppressAlerts( self, suppress = True, level=WARNING ):
        """Set flag to suppress audio alerts, or to re-enable them (False)."""
        if  level == WARNING:
            self.suppressAlrtsWarn  = suppress
        elif  level == ALARM:
            self.suppressAlrtsAlarm = suppress

    def resize( self, widWidth, widHeight ):
        """Recompute any size-dependent positions, and redisplay all."""
        self.valueRange = self.highAlarm - self.lowAlarm
        self.widWidth   = widWidth
        self.widHeight  = widHeight
        self.varNameX   = 0.004 * widWidth
        self.varNameY   = 0.01  * widHeight
        self.scaleY     = 0.5   * widHeight
        self.scaleMinX  = 0.1   * widWidth
        self.scaleMaxX  = 0.9   * widWidth
        self.scaleRange = self.scaleMaxX - self.scaleMinX
        self.minMaxLabelY = 0.5 * widHeight + 12
        scaleValueRatio = self.scaleRange / self.valueRange
        self.alarmMinX  = self.scaleMinX + scaleValueRatio * \
                        (self.lowWarning - self.lowAlarm)
        self.alarmMaxX  = self.scaleMinX + scaleValueRatio * \
                        (self.highWarning - self.lowAlarm)
        self.scaleZeroX = self.scaleMinX + scaleValueRatio * (-self.lowAlarm)
        self.minLabelX  = self.scaleMinX - 15
        self.maxLabelX  = self.scaleMaxX + 10
        #? cur = self.curArrowLen = 0.25*widHeight
        #? cmd = self.cmdArrowLen = 0.15*widHeight
        cur = self.curArrowLen = 15
        cmd = self.cmdArrowLen = 10
        self.curArrowShape = (cur, cur, 0.5*cur)
        self.cmdArrowShape = (cmd, cmd, 0.5*cmd)
        self.curLabelOffsets = ( 0.7*cur, cur )
        self.cmdLabelOffsets = ( 0.7*cmd, cmd )
        self.configure( width=widWidth, height=widHeight )
        #? print "LimitsWidget %s resize:" % self.varName ,
        #? print "      widWidth = %.1f, widHeight = %.1f, valueRange = %.1f"%\
        #?      (widWidth, widHeight, self.valueRange )
        #? print "      %.1f, %.1f, %.1f, %.1f, %.1f"%\
        #?   (self.scaleY, self.scaleMinX, self.scaleMaxX, self.scaleZeroX, \
        #?    self.scaleRange)
        #? print "      %.1f, %.1f, %.1f, %.1f, %.1f, %.1f"%\
        #?   (self.minMaxLabelY, self.alarmMinX, self.alarmMaxX,\
        #?    self.scaleZeroX, self.minLabelX, self.maxLabelX)

        self.redrawBg()
        if  self.dataAcquired:
            self.redrawFg()
            self.prevValue    = self.curValue
            self.prevCmdValue = self.cmdValue

    def redrawBg( self ):
        """Redraw background, i.e. constant objects."""
        self.delete( ('B',) )
        self.textID = self.create_text( self.varNameX, self.varNameY,
            text=self.varName, anchor=NW, fill=LIMPANELABEL, tags=('B',) )
        # main scale bar
        self.create_rectangle(                  # center piece
            self.alarmMinX, self.scaleY-1, self.alarmMaxX, self.scaleY+1, 
            fill=LIMPANESCALE, outline=LIMPANESCALE,tags=('B',) )
        self.create_rectangle(                  # left piece
            self.scaleMinX, self.scaleY-1, self.alarmMinX, self.scaleY+1, 
            fill=LIMPANEALARM, outline=LIMPANEALARM,tags=('B',) )
        self.create_rectangle(                  # right piece
            self.alarmMaxX, self.scaleY-1, self.scaleMaxX, self.scaleY+1, 
            fill=LIMPANEALARM, outline=LIMPANEALARM,tags=('B',) )
        self.create_rectangle(                  # vertical at low end
            self.scaleMinX, self.scaleY-10, self.scaleMinX+1, self.scaleY+10, 
            fill=LIMPANEALARM, outline=LIMPANEALARM,tags=('B',) )
        self.create_rectangle(                  # vertical at 0 point
            self.scaleZeroX, self.scaleY-8, self.scaleZeroX,self.scaleY+8, 
            fill=LIMPANESCALE, outline=LIMPANESCALE,tags=('B',) )
        self.create_rectangle(                  # vertical at high end
            self.scaleMaxX, self.scaleY-10, self.scaleMaxX-1, self.scaleY+10, 
            fill=LIMPANEALARM, outline=LIMPANEALARM,tags=('B',) )
        minStr = '%.0f' % self.lowAlarm
        maxStr = '%.0f' % self.highAlarm
        self.create_text( self.minLabelX, self.minMaxLabelY,
            text=minStr, anchor=NW, fill=LIMPANELABEL, tags=('B',) )
        self.create_text( self.maxLabelX, self.minMaxLabelY,
            text=maxStr, anchor=NE, fill=LIMPANELABEL, tags=('B',) )

    def __pointerColor( self, val, noneAllow ):
        if  val <= self.lowAlarm or val >= self.highAlarm:
            if  noneAllow and (not self.suppressAlrtsAlarm):
                self.alertObj.alert( level=ALARM )
#?          TelStatLog.TelStatLog( LimErrLimitExceeded,
#?                      "ERROR (LimitsWidget:" + self.varName +
#?                      ":__pointerColor):  " +
#?                      "value limit exceeded = %.3f" % val )
            return LIMPANEPOINTERALARM          # alarm color
        if  val < self.lowWarning or val > self.highWarning:
            if  noneAllow and (not self.suppressAlrtsWarn):
                self.alertObj.alert()
#?          TelStatLog.TelStatLog( LimWarnThreshExceeded,
#?                      "WARNING (LimitsWidget:" + self.varName +
#?                      ":__pointerColor):  " +
#?                      "value threshold exceeded = %.3f" % val )
            return LIMPANEPOINTERWARN           # warning color
        else:
            return LIMPANEPOINTER

    def redrawFg( self ):
        """Redraw foreground objects, i.e. pointers."""
        self.delete( ('F',) )
        self.prevValue    = self.curValue
        self.prevCmdValue = self.cmdValue

        self.curX = self.scaleMinX + self.scaleRange * \
                        (self.curValue - self.lowAlarm) / self.valueRange
        aColor = self.__pointerColor( self.curValue, self.allowCurAlert )
        self.curPtr = self.create_line( 
            self.curX, self.scaleY-1, self.curX, self.scaleY-self.curArrowLen,
            arrow=FIRST, arrowshape=self.curArrowShape, fill=aColor,
            tags=('F',) )
        if  self.curValue < -1:
            self.curLabel = self.create_text( 
                self.curX+self.curLabelOffsets[0], 
                self.scaleY-1-self.curLabelOffsets[1], 
                text=self.curValueStr, anchor=W, fill=aColor, tags=('F',) )
        else:
            self.curLabel = self.create_text( 
                self.curX-self.curLabelOffsets[0], 
                self.scaleY-1-self.curLabelOffsets[1], 
                text=self.curValueStr, anchor=E, fill=aColor, tags=('F',) )

        self.cmdX = self.scaleMinX + self.scaleRange * \
                        (self.cmdValue - self.lowAlarm) / self.valueRange
        aColor = self.__pointerColor( self.cmdValue, self.allowCmdAlert )
        self.cmdPtr = self.create_line( 
            self.cmdX, self.scaleY+1, self.cmdX, self.scaleY+self.cmdArrowLen,
            arrow=FIRST, arrowshape=self.cmdArrowShape, fill=aColor,
            tags=('F',) )
        if  self.cmdValue < -1:
            self.cmdLabel = self.create_text( 
                self.cmdX+self.cmdLabelOffsets[0], 
                self.scaleY+1+self.cmdLabelOffsets[1], 
                text=self.cmdValueStr, anchor=W, fill=aColor, tags=('F',) )
        else:
            self.cmdLabel = self.create_text( 
                self.cmdX-self.cmdLabelOffsets[0], 
                self.scaleY+1+self.cmdLabelOffsets[1], 
                text=self.cmdValueStr, anchor=E, fill=aColor, tags=('F',) )

    def moveFg( self ):
        """Move foreground objects, i.e. pointers."""
        # If either sign has changed, do a redraw
        if  (self.prevValue * self.curValue < 0) or     \
            (self.prevCmdValue * self.cmdValue < 0):
            self.redrawFg()     # to handle changes in positions of labels
            return
        self.prevValue    = self.curValue
        self.prevCmdValue = self.cmdValue
        self.itemconfigure( self.curLabel, text = self.curValueStr )
        self.itemconfigure( self.cmdLabel, text = self.cmdValueStr )
        x = self.scaleMinX + self.scaleRange * \
                        (self.curValue - self.lowAlarm) / self.valueRange
        deltaX = x - self.curX
        aColor = self.__pointerColor( self.curValue, self.allowCurAlert )
        self.curX = x
        self.move( self.curPtr, deltaX, 0 )
        self.move( self.curLabel, deltaX, 0 )
        self.itemconfigure( self.curPtr, fill = aColor )
        self.itemconfigure( self.curLabel, fill = aColor )

        x = self.scaleMinX + self.scaleRange * \
                        (self.cmdValue - self.lowAlarm) / self.valueRange
        deltaX = x - self.cmdX
        aColor = self.__pointerColor( self.cmdValue, self.allowCmdAlert )
        self.cmdX = x
        self.move( self.cmdPtr, deltaX, 0 )
        self.move( self.cmdLabel, deltaX, 0 )
        self.itemconfigure( self.cmdPtr, fill = aColor )
        self.itemconfigure( self.cmdLabel, fill = aColor )

    def refresh( self, newCurValue=None, newCmdValue=None ):
        """Recompute pointer positions and move the pointers there."""

        if  newCurValue == None:
            self.curValue      = self.lowAlarm
            self.curValueStr   = 'CURRENT <No Data>'
            self.allowCurAlert = False
        else:
            self.curValue      = newCurValue
            self.curValueStr   = 'CURRENT (%.1f)' % newCurValue
        if  newCmdValue == None:
            self.cmdValue      = self.lowAlarm
            self.cmdValueStr   = 'commanded <No Data>'
            self.allowCmdAlert = False
        else:
            self.cmdValue      = newCmdValue
            self.cmdValueStr   = 'commanded (%.1f)' % newCmdValue
        #? print "LimitsWidget: curValue = %s, cmdValue = %s" % \
        #?      (`self.curValue`, `self.cmdValue`)

        if  self.dataAcquired:
            self.moveFg()
        else:
            self.dataAcquired = True
            self.redrawFg()
        # Reset for next time
        self.allowCurAlert = True
        self.allowCmdAlert = True

    def geomCB(self, event):
        """Callback for to print geometry."""
        print self.varName, ":  ", self.winfo_geometry()

######################################################################
################   test application   ################################
######################################################################

#?  Following for debugging only ############
#?def refresh():
#?    newCurValue = testLimWidget.curValue + 3.0
#?    newCmdValue = testLimWidget.cmdValue + 2.0
#?    if  newCurValue >= testLimWidget.highAlarm:
#?      newCurValue = -269
#?    if  newCmdValue >= testLimWidget.highAlarm:
#?      newCmdValue = -268
#?    testLimWidget.refresh( newCurValue, newCmdValue )
#?    root.after( 50, refresh )
#?
#?if __name__ == '__main__':
#?    # Create the base frame for the widgets
#?    root = Tkinter.Tk()
#?    Pmw.initialise(root)
#?    root.title("Limits Widget Test")
#?
#?    # Create an instance 
#?    testLimWidget = LimitsWidget( root, 'testLimWidget', 'Azimuth' )
#?    testLimWidget.grid( row=0, column=0 )
#?
#?    refresh()
#?    root.mainloop()
#?

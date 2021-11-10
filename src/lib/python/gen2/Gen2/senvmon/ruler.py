#!/usr/bin/env python

# timeRuler.py 20090504 sam streeper created

#This code is a work in progress, not all features fleshed out.


from __future__ import division
import sys
import math
#from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from bisect import bisect

import time

class Ruler(QWidget):
    # A ruler's beam is perpendicular to its length, & specified in pixels
    # Naive default, can remove if I always calculate what beam should be
    Beam = 16
    # number of pixels for the variable part of a full length tick-mark
    FullTick = 4
    # The pixels of a base tick will be added to all tick marks
    BaseTick = 0
    DPI = 83
    # position: enum
    LEFT, RIGHT, TOP, BOTTOM = range(4)
    # ruler orientation: enum to indicate ruler ticks off in QT coords or reversed
    NORMAL, REVERSED = range(2)
    # ruler text orientation
    TEXTNORMAL, UP, DOWN = range(3)

    def __init__(self, graphWidget, parent=None):
        super(Ruler,self).__init__(parent)

        self.graph = graphWidget
        self.font = QFont()
        self.font.setPointSize(6)  #7
        # maxWidthString will be used to set the beam of a vertical ruler;
        #  you should change it based on the format of the widest value you will display
        self.maxWidthString = "000.00"
        self.textOrientation = Ruler.TEXTNORMAL
        self.initializeDefaults(Ruler.BOTTOM)

    def _verticalRulerBeam(self):
        extraSpace = 4
        #extraSpace=30
        return (self.stringWidth + self.fullTick + self.baseTick + 
                self.tickExtraSpace + self.textOffset + extraSpace)

    def _horizontalRulerBeam(self):
        extraSpace = -1
        #extraSpace = 5 # this is for vnc setting; on vnc, timer ruler is cut and hard to see
        stringHeight = self.fontMetrics.height()
        return (stringHeight + self.fullTick + self.baseTick + 
                self.tickExtraSpace + self.textOffset + extraSpace)

    # invoke this after setting ruler values that affect the beam; result is that self.beam is correct
    def calcBeam(self):
        if (self.position in (Ruler.BOTTOM, Ruler.TOP)) or self.textOrientation != Ruler.TEXTNORMAL:
            self.beam = self._horizontalRulerBeam()
            # width as big as possible, height fixed to beam
            self.setSizePolicy(QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed))
        else:
            self.beam = self._verticalRulerBeam()
            # width fixed to beam, height as big as possible
            self.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Ignored))

    def initializeDefaults(self,position):
        self.fontMetrics = QFontMetrics(self.font)
        self.stringWidth = self.fontMetrics.width(self.maxWidthString)
        self.position = position
        # for an inch ruler the pixels/unit is dpi
        # for other ruler scales, you will set this to mark your chosen unit with a full tick
        self.pixelsPerUnit = Ruler.DPI
        self.marksPerUnit = 4
        
        # how much does the ruler display increment per full tick
        self.valueIncrement = 1
        # ruler's starting value
        self.startValue = 0
        # direction doesn't work yet, since that obfuscates the drawing loop
        # instead I'll just try swapping the start/end values and invert the value increment
        #self.direction = Ruler.NORMAL
        self.fullTick = Ruler.FullTick
        self.baseTick = Ruler.BaseTick
        self.tickExtraSpace = 1
        if self.position == Ruler.LEFT:
            self.tickExtraSpace = 3
            # text offset for vertical rulers
            self.textOffset = 3
        elif self.position == Ruler.BOTTOM:
            # tighten it up
            self.textOffset = -1
        self.filled = True
        self.drawBorder = True
        self.calcBeam()

    def minimumSizeHint(self):
        # depending on orientation, one of these will be ignored, this will only constrain 
        # the dimension of the actual beam
        return QSize(self.beam, self.beam)
    
    def rulerRect(self):
        '''
        The ruler rect fits within this widget's rect() and has a suitable margin
        based on the graph's dataviewMargin
        '''
        rect = self.rect()
        if self.position in (Ruler.TOP, Ruler.BOTTOM):
            margin = self.graph.dataviewMargin.width()
            return QRect(margin, 0, rect.width() - (2*margin), rect.height())
        else:
            margin = self.graph.dataviewMargin.height()
            return QRect(0, margin, rect.width(), rect.height() - (2*margin))

    def _paintBackground(self, painter):
        rulerRect = self.rulerRect()
        if self.filled:
            painter.setBrush(QColor('#dcdad8'))
            #-----------------------------------------
            if self.position in (Ruler.TOP, Ruler.BOTTOM):
                gradient = QLinearGradient(0,rulerRect.top(), 0,rulerRect.bottom())
            else:
                gradient = QLinearGradient(rulerRect.left(), 0,rulerRect.right(), 0)

            gradient.setColorAt(0, QColor('#dcdad8'))
            gradient.setColorAt(0.5, Qt.white)
            gradient.setColorAt(1, QColor('#dcdad8'))
            painter.fillRect(rulerRect, QBrush(gradient))

            #-----------------------------------------
        else:
            painter.setBrush(Qt.NoBrush)

        if self.drawBorder:
            painter.setPen(QPen(Qt.black, 0, Qt.SolidLine))
        else:
            painter.setPen(QPen(Qt.black, 0, Qt.NoPen))

        #if self.filled or self.drawBorder:
        if self.drawBorder:
            painter.drawRect(rulerRect)
        #else:
        if not self.drawBorder:
            # just draw a single ruler line
            painter.setPen(QPen(Qt.black, 0, Qt.SolidLine))
            if self.position == Ruler.BOTTOM:
                painter.drawLine(rulerRect.topLeft(),rulerRect.topRight())
            elif self.position == Ruler.LEFT:
                painter.drawLine(rulerRect.topRight(),rulerRect.bottomRight())

    def _paintTicks(self, painter, returnGrid=False):
        '''
        Before _paintTicks is invoked, ensure the following variables are ok:
            self.drawPosition (0=ruler start, neg ok) : Where the first full tick value is aligned
            self.startValue : The first full tick value, won't be visible if drawPos is negative
            self.valueIncrement : delta between consecutive full tick values
            self.pixelsPerUnit : pixels between full tick values
        '''
        
        rulerRect = self.rulerRect()
        if returnGrid:
            grid = []
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(Qt.black, 0, Qt.SolidLine))

        # self.drawPosition marks where a tick will be drawn
        # drawEnd is the point where ticks will no longer be drawn
        if self.position == Ruler.BOTTOM:
            drawBeginning = rulerRect.left()
            drawEnd = rulerRect.right()
        elif self.position == Ruler.LEFT:
            #self.drawPosition = self.boundingRect().top()
            drawBeginning = rulerRect.top()
            drawEnd = rulerRect.bottom()
        
        drawInterval = self.pixelsPerUnit / self.marksPerUnit

        # drawCounter is how many ticks I have drawn, so it represents position in the tickLength cycle
        drawCounter = 0
        value = self.startValue
        tickTextBoundary = self.fullTick + self.baseTick + self.tickExtraSpace
        painter.setFont(self.font)
        painter.setPen(Qt.black)
        while self.drawPosition <= drawEnd:
            tickLength = self.fullTick
            divisor = self.marksPerUnit
            drawValue = 1
            # calculate the tick length; it's full length when the drawCounter align on marksPerUnit
            # and the tick lengths will be halved until we know what tickLength boundary we're drawing
            while divisor > 1:
                modResult = drawCounter % divisor
                if modResult == 0:
                    break
                tickLength /= 2
                divisor /= 2
                # once we have divided the tick, we know we're not on a big boundary where a value is drawn
                drawValue = 0

            if self.drawPosition >= drawBeginning:
                # draw the tick
                if self.position == Ruler.BOTTOM:
                    painter.drawLine(self.drawPosition, 0, self.drawPosition, tickLength + self.baseTick)
                elif self.position == Ruler.LEFT:
                    painter.drawLine(self.beam - (tickLength + self.baseTick), self.drawPosition, self.beam, self.drawPosition)
                    
                # draw the value if on a full boundary
                if drawValue:
                    if self.position == Ruler.BOTTOM:
                        painter.drawText(self.drawPosition-(0.95 * drawInterval),
                                         tickTextBoundary + self.textOffset,
                                         2 * drawInterval,
                                         self.beam - tickTextBoundary,
                                         Qt.AlignHCenter,
                                         self.valueString(value))
                    elif self.position == Ruler.LEFT:
                        painter.drawText(self.textOffset,
                                         self.drawPosition-(0.95 * drawInterval),
                                         self.beam - tickTextBoundary - self.textOffset,
                                         2 * drawInterval,
                                         Qt.AlignVCenter | Qt.AlignHCenter,
                                         self.valueString(value))

                    if returnGrid:
                        grid.append(self.drawPosition)

                    value += self.valueIncrement
            elif drawValue:
                # I missed the first valueIncrement because it wasn't drawn
                # fixme: !!! this is ok when the first tick is a half, but wrong otherwise !!!
                value += self.valueIncrement

            # advance to the next tick drawing position
            self.drawPosition += drawInterval
            # advance the counter for the tick length calculation
            drawCounter += 1

        if returnGrid:
            return grid


    def paintEvent(self, event):
        painter = QPainter(self)
        self._paintBackground(painter)
        # drawPosition isn't going to be right here, fix in subclass
        self.drawPosition = 0
        self._paintTicks(painter)

    def valueString(self, value):
        return str(value)


class TimeRuler(Ruler):
    # Ruler values will be set based on the parameters from the TIMESCALES array (& friends)
    # values are in seconds
    # there is one more TICKS_PER_UNIT than TIMESCALES which is the number of ticks per unit for 
    # the biggest timescales once the time is > 15 minutes we will just divide the units with 
    # half ticks.  I DO need 2 values at the end with 2 ticks per unit, so that the ticks are 
    # right when I run off the end of the timescales
    TIMESCALES =     (1, 5, 15, 30, 60, 2*60, 3*60, 5*60, 10*60, 15*60, 30*60)
    TICKS_PER_UNIT = (1, 1,  3,  2,  2,    2,    3,    1,     2,     3,     2, 2)

    # I will try to display DESIRED_VALUES (ticks with values)
    DESIRED_VALUES = 3.5

    def __init__(self, graphWidget, parent=None):
        super(TimeRuler, self).__init__(graphWidget, parent)
        #self.filled = False
        self.drawBorder = False
        self.marksPerUnit = 2
        self._timeRangeInitialized = False
        self.timeRange = 0
        #arrowBoxWidth = self.beam * 1.5
        #self.timeAnchorRect = QRectF(self.rect().width() - arrowBoxWidth,-1,arrowBoxWidth,self.beam)
        self.dragging = False
        


    def paintEvent(self, event):
        painter = QPainter(self)
        #painter.setClipRect(self.rect())

        self._paintBackground(painter)
        if self._timeRangeInitialized:
            self.drawPosition = self.myDrawPosition
            Ruler._paintTicks(self, painter)
            if not self.graph.timeIsAnchored():
                # if time isn't anchored, draw a conspicuous widget to return to anchored mode
                painter.setPen(QPen(QColor('#c10000'), 1, Qt.SolidLine))
                painter.setBrush(QColor('#ff3030'))
                painter.drawRect(self.timeAnchorRect)

                painter.setPen(QPen(Qt.white, 1, Qt.SolidLine))
                painter.setBrush(Qt.black)
                arrowLeft = self.timeAnchorRect.left() + 4
                arrow = [arrowLeft, 2,
                         self.timeAnchorRect.right()-4, self.timeAnchorRect.center().y(),
                         arrowLeft, self.timeAnchorRect.bottom()-2]
                painter.drawPolygon(QPolygon(arrow))


    # called when display scaling is changed
    def calcTimeRangeParameters(self, timeRange):
        '''
        i = 0
        for timescale in TimeRuler.TIMESCALES:
            if (timescale * TimeRuler.DESIRED_VALUES) > timeRange:
                self.secondsPerUnit = TimeRuler.TIMESCALES[i]
                break
            i += 1
        self.marksPerUnit = TimeRuler.TICKS_PER_UNIT[i]
        '''
        i = bisect(TimeRuler.TIMESCALES, (timeRange / TimeRuler.DESIRED_VALUES))
        #self.secondsPerUnit = TimeRuler.TIMESCALES[i]
        self.marksPerUnit = TimeRuler.TICKS_PER_UNIT[i]

        # if we got to the end of timescales, we don't know the number of seconds per unit yet
        # fixme: these control structures feel inelegant or retarded
        #if (TimeRuler.TIMESCALES[-1] * TimeRuler.DESIRED_VALUES) < timeRange:
        if i < len(TimeRuler.TIMESCALES):
            self.secondsPerUnit = TimeRuler.TIMESCALES[i]
        else:
            self.secondsPerUnit = TimeRuler.TIMESCALES[-1]
            i = 0
            # don't loop (doubling time scale) forever, should never happen tho
            while i < 2000:
                nextTry = self.secondsPerUnit * 2
                if (nextTry * TimeRuler.DESIRED_VALUES) > timeRange:
                    break
                self.secondsPerUnit = nextTry
                i += 1

        if timeRange < (2 * 60):
            self.timeFormat = "%H:%M:%S"
        elif timeRange < (1.4 * 24 * 60 * 60):
            self.timeFormat = "%H:%M"
        else:
            self.timeFormat = "%a %H:%M"
            
        #print "calcTimeRangeParams - minutes per unit: %d" % (self.secondsPerUnit / 60)
        pixelsPerSecond = self.rulerRect().width() / timeRange
        self.pixelsPerUnit = pixelsPerSecond * self.secondsPerUnit
        self.valueIncrement = self.secondsPerUnit
    
    def setTimeRange(self, startTime, endTime):
        self._timeRangeInitialized = True
        newTimeRange = endTime - startTime
        if self.timeRange != newTimeRange:
            self.timeRange = newTimeRange
            self.calcTimeRangeParameters(newTimeRange)

        iStartTime = int(startTime)
        iOffsetTime = 0
        # fixme! In Hawaii local time, the time since epoch aligns on an incorrect 4 hour boundary;
        # I'll align it by starting to draw ticks 2 hours earlier once the time scale reaches 4 hours/tick
        if self.secondsPerUnit > (2 * 60 * 60):
            # fixme: this will offset to the ruler start drawPosition to correct for Hawaii local time!!!
            #print "offsetting ruler start time, was %s" % (self.valueString(iStartTime))
            # offset time must be negative; we intend to start drawing full ticks earlier
            iOffsetTime = (-2 * 60 * 60)
            #print "    new ruler start time: %s thats: %s" % (self.valueString(iStartTime), \
            #           self.valueString(iStartTime - ((iStartTime + iOffsetTime) % self.secondsPerUnit)))
            
        self.startValue = iStartTime - ((iStartTime + iOffsetTime) % self.secondsPerUnit)
        # the drawPosition is set to the first full tick, which will be before the ruler's drawBeginning
        scale = (endTime - self.startValue) / self.timeRange
        rulerRect = self.rulerRect()
        self.myDrawPosition = rulerRect.right() - (rulerRect.width() * scale)

    def valueString(self, value):
        return time.strftime(self.timeFormat, time.localtime(value))

    def mousePressEvent(self,event):
        if not event.button() == Qt.LeftButton:
            return
        if not self.graph.timeIsAnchored():
            if self.timeAnchorRect.contains(event.pos()):
                self.graph.coordinator.timeAnchored = True
                self.graph.coordinator.timerEvent(None)
                return
        self.dragging = True
        # fixme: the TVcoordinator should respect that the timescale is being dragged and not send
        # spurious movements (although time will continue to accrete)
        if self.graph.timeIsAnchored():
            width = self.rulerRect().width()
            x = min(event.pos().x() - self.graph.dataviewMargin.width(), width-1)
            scale = (width - x) / width
            self.timeUnderCursor = self.graph.dataView.endTime - (self.timeRange * scale)
            #print " XXXX --> %s" % (self.valueString(self.timeUnderCursor))
        else:
            width = self.rulerRect().width()
            scale = (width - (event.pos().x() - self.graph.dataviewMargin.width())) / width
            self.timeUnderCursor = self.graph.dataView.endTime - (self.timeRange * scale)
        self.graph.refreshDisplay()

    def mouseMoveEvent(self,event):
        if not ((event.buttons() & Qt.LeftButton) and self.dragging):
            #print "ignoring mouse move event"
            return
        if self.graph.timeIsAnchored():
            width = self.rulerRect().width()
            endTime = self.graph.dataView.endTime
            x = min(event.pos().x() - self.graph.dataviewMargin.width(), width-1)
            scale = (width - x) / width
            #print "Mouse move scale: %f" % (scale)
            startTime = endTime - ((endTime - self.timeUnderCursor) / scale)
            if endTime - startTime > self.graph.coordinator.maxTimeRange:
                startTime = endTime - self.graph.coordinator.maxTimeRange
            elif endTime - startTime < self.graph.coordinator.minTimeRange:
                startTime = endTime - self.graph.coordinator.minTimeRange
            self.graph.coordinator.setTimeRange(startTime, endTime, calcTimeRange=True)
        else:
            scale = (event.pos().x() - self.graph.dataviewMargin.width()) / self.rulerRect().width()
            startTime = self.timeUnderCursor - (scale * self.timeRange)
            self.graph.coordinator.setTimeRange(startTime, startTime+self.timeRange)

    def mouseReleaseEvent(self,event):
        if not (event.button() == Qt.LeftButton and self.dragging):
            return
        self.dragging = False

    def resizeEvent(self, event):
        # since the graph machinery will never use an empty valueRange, this will force
        # an update based on the new size
        #self.timeRange = 0
        if self._timeRangeInitialized:
            self.calcTimeRangeParameters(self.timeRange)
        arrowBoxWidth = self.beam * 1.5
        self.timeAnchorRect = QRect(self.rect().width() - arrowBoxWidth,-1,arrowBoxWidth,self.beam)
            
def convertToScientific(nr):
    coefficient = float(nr)
    exponent = 0
    while abs(coefficient) >= 10:
        exponent += 1
        coefficient = coefficient / 10
    while abs(coefficient) < 1:
        exponent -= 1
        coefficient = coefficient * 10
    return (coefficient, exponent)

def sign(x):
        return cmp(x,0)

class ValueRuler(Ruler):
    # VALUESCALES = (1, 2, 3, 4, 5, 6,   7, 8, 9,10)
    MARKSFORRANGE = (4, 4, 3, 4, 5, 3, 3.5, 4, 3, 4)
    
    def __init__(self, graphWidget, parent=None):
        super(ValueRuler, self).__init__(graphWidget, parent)
        self.initializeDefaults(Ruler.LEFT)
        #self.filled = False
        self.drawBorder = False
        self.pixelsPerUnit = 20
        self.marksPerUnit = 2
        self._valueRangeInitialized = False
        self.fullTick = 6
        self.baseTick = 1
        self.valueRange = 0
        self.hardValueIncrement = None

    def paintEvent(self, event):
        painter = QPainter(self)
        self._paintBackground(painter)
        if self._valueRangeInitialized:
            self.drawPosition = self.myDrawPosition
            if self.graph.drawValueGrid:
                grid = Ruler._paintTicks(self, painter, returnGrid=True)
                self.graph.valueGrid = grid
            else:
                Ruler._paintTicks(self, painter)


    def calcValueRangeParameters(self, valueRange):
        if self.hardValueIncrement != None:
            self.valueIncrement = -self.hardValueIncrement
            self.pixelsPerUnit = self.rulerRect().height() / (valueRange / self.hardValueIncrement)
            return
        (vCoefficient, vExponent) = convertToScientific(valueRange)
        # normalizedRangeDigit will be in range(1,9) as the first digit in
        # scientific notation
        normalizedRangeDigit = int(vCoefficient)

        # The valueIncrement will be a bit small when the scientific notation nears rounding
        # values (ie 1.9e+1, 1.6e+22); the effect is most pronounced for small normalizedRangeDigit
        roundingTestDigit = (int(vCoefficient * 10)) % 10
        if ((normalizedRangeDigit < 9) and (roundingTestDigit >= 5)):
            normalizedRangeDigit += 1

        numFullTicks = ValueRuler.MARKSFORRANGE[normalizedRangeDigit - 1]
        positiveValueIncrement = normalizedRangeDigit * (10**vExponent) / numFullTicks
        self.valueIncrement = -positiveValueIncrement
        tickRange = numFullTicks * positiveValueIncrement
        #print "  normRngDig=%d   vInc: %f    represented Range:%0.3f" % \
        #    (normalizedRangeDigit, positiveValueIncrement, tickRange)
        self.pixelsPerUnit = (self.rulerRect().height() * (tickRange / valueRange)) / numFullTicks
    
    def updateValueRange(self, minval, maxval):
        if minval == None or maxval == None:
            self._valueRangeInitialized = False
            return
        newValueRange = maxval - minval
        if self.valueRange != newValueRange:
            self.valueRange = newValueRange
            #print "\ngraph:%s  valueRange:%f  maxval:%f" % (self.graph.title, newValueRange, maxval)
            self.calcValueRangeParameters(newValueRange)
        
        # we draw from top (0 in drawing coordinates) to bottom
        # self.valueIncrement is negative since we count down from the maxval at the top
        maxvalSign = sign(maxval)
        # intervalCount is the number of times the ruler's fullTick interval goes into maxval
        # we now must find the first full tick drawn at or before the start of the ruler
        intervalCount = abs(int(maxval / -self.valueIncrement))
        if ((intervalCount * -self.valueIncrement) < abs(maxval) and (maxvalSign > 0)):
            intervalCount += 1
        self.startValue = (intervalCount * -self.valueIncrement) * maxvalSign
        
        scale = (self.startValue - minval) / self.valueRange
        #print "    scale = %f" % (scale)
        rulerRect = self.rulerRect()
        self.myDrawPosition = rulerRect.bottom() - (rulerRect.height() * scale)
        self._valueRangeInitialized = True


    def valueString(self, value):
        iValue = int(value)
        if iValue == value:
            return str(iValue)
        if self.valueRange <= 1.1:
            return "%0.2f" % (float(value))
        return "%0.1f" % (float(value))

    
    def mousePressEvent(self,event):
        self.graph.drawValueGrid = not self.graph.drawValueGrid
        #self.graph.updateValueRange(self.graph.dataView.startTime, self.graph.dataView.endTime)
        self.graph.refreshDisplay()

    def resizeEvent(self, event):
        # since the graph machinery will never use an empty valueRange, this will force
        # an update based on the new size
        self.valueRange = 0
        # I'd like to update the valueRange parameters based on the new size right now rather
        # than wait for the next timed display update (where it will be triggered by the
        # current invalid valueRange) but (fixme) the following is a grody invasive way to force this
        self.graph.updateValueRange(self.graph.dataView.startTime, self.graph.dataView.endTime)


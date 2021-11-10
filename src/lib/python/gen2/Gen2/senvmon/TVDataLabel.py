#!/usr/bin/env python

# 2009 Sam Streeper
# 20091120
#
# DataLabels show the value of data on the graph and let you disable the display of individual
# data feeds.  They are wrapped in a LableContainer which is the information area at the
# top of a timeValue graph

from __future__ import division
import sys
import math

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from timeValueGraph import *

from TVFlowlayout import FlowLayout

# fixme: where should this common function be?
def averageColor(color1, color2, weight1=1, weight2=1):
    divisor = weight1 + weight2
    averageR = (weight1*color1.red() + weight2*color2.red())/divisor
    averageG = (weight1*color1.green() + weight2*color2.green())/divisor
    averageB = (weight1*color1.blue() + weight2*color2.blue())/divisor
    return QColor(averageR, averageG, averageB)

class LabelContainer(QWidget):
    def __init__(self, graphWidget, parent=None):
        super(LabelContainer, self).__init__(parent)
        # width is as big as possible, any height but prefer (small) sizehint (grown to contents)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred))
        self.graph = graphWidget
        flowLayout = FlowLayout(spacing=0) #2
        # ack pfft
        flowLayout._verticalSpacing = 0
        self.setLayout(flowLayout)
        # was: painter.drawText(4, 11, " %s " % (self.graph.title))
        title = TightLabel(self.graph, self.graph.title)
        title.font().setPointSize(0) #10
        title.font().setBold(False)
        #title.setPen(Qt.black)
        #title.setBackgroundMode(Qt.TransparentMode)
        flowLayout.addWidget(title)
        #self.setAttribute(Qt.WA_OpaquePaintEvent)

    def paintEvent(self, event):
        painter = QPainter(self)
        darkPanelColor = QColor('#a0a0a0')
        bgColor = QColor(self.graph.backgroundColor())

        darkAverageColor = averageColor(darkPanelColor, bgColor, weight2=5)
        painter.setBrush(darkAverageColor)
        painter.setPen(QPen(Qt.black, 0, Qt.NoPen))
        #painter.drawRect(QRectF(2,0,self.rect().width()-4,self.rect().height()))
        painter.drawRect(2,0,self.rect().width()-4,self.rect().height())
        
    def minimumSizeHint(self):
        return QSize(100,20)

# a TightLabel is a graph label that has a tight bounding box, so it gets laid out with
# minimum border space.  I'm trying to get the most information on the least pixels.
# I use the TightLabel directly for a graph title, and I subclass for formatted data displays
class TightLabel(QWidget):
    def __init__(self, graphWidget, formatString, parent=None):
        super(TightLabel, self).__init__(parent)
        self.graph = graphWidget
        self.formatString = formatString
        self.font().setPointSize(1) #9
        self.textBorders = QSize(22, -1)
        self.calculateSize()
        # TightLabels won't change size so won't change layout regardless of label contents
        self.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))

    def formattedString(self):
        return "%s  " % (self.formatString,)
    
    def longestExpectedString(self):
        return self.formattedString()
    
    def calculateSize(self):
        fontMetrics = QFontMetrics(self.font())
        boundingRect = fontMetrics.boundingRect(self.longestExpectedString())
        self._width = math.ceil(boundingRect.width()) + (2 * self.textBorders.width())
        self._height = math.ceil(boundingRect.height()) + (2 * self.textBorders.height())
        self._fontYOffset = boundingRect.height() - fontMetrics.descent() + self.textBorders.height() -1
        
    def minimumSizeHint(self):
        return QSize(self._width, self._height)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.font().setBold(True)
        myString = self.formattedString()
        painter.setPen(self.graph.colorFor(self))
        painter.drawText(self.textBorders.width(), self._fontYOffset, myString)

class DataLabel(TightLabel):
    def __init__(self, graphWidget, formatString, parent=None):
        self.value = None
        self.hidden = False
        super(DataLabel, self).__init__(graphWidget, formatString, parent)

    def stringForValue(self, value):
        if value == None:
            try:
                i = self.formatString.index('%')
                return self.formatString[:i] + '???'
            except:
                return '???'
        return self.formatString % (value)
    
    def labelString(self):
        value = self.graph.currentValueForDataLabel(self)
        return self.stringForValue(value)
    
    def longestExpectedString(self):
        return self.stringForValue(float(self.graph.longestStringForDataLabel(self)))
         
    def paintEvent(self, event):
        painter = QPainter(self)

        myString = self.labelString()

        if self.hidden:
            disabledBackgroundColor = averageColor(self.graph.backgroundColor(),QColor('#404040'),3)
            painter.setPen(QPen(Qt.black, 0, Qt.NoPen))
            painter.setBrush(disabledBackgroundColor)

            BOTTOM = self._height - 2
            RIGHT = self._width - 1
            painter.drawRect(0,0, RIGHT, BOTTOM)
            #--------------
            painter.setBrush(Qt.NoBrush)
    
            painter.setPen(QPen(Qt.black, 0, Qt.SolidLine))
            painter.drawLine(0, 0, 0, BOTTOM)
            painter.drawLine(0, 0, RIGHT, 0)
    
            painter.setPen(QPen(Qt.white, 0, Qt.SolidLine))
            painter.drawLine(0, BOTTOM, RIGHT, BOTTOM)
            painter.drawLine(RIGHT, 0, RIGHT, BOTTOM)

        painter.setPen(self.graph.colorFor(self))
        painter.drawText(self.textBorders.width(), self._fontYOffset, " %s " % (myString,))

    def mousePressEvent(self,event):
        self.hidden = not self.hidden
        index = self.graph.indexForDataLabel(self)
        if self.hidden:
            self.graph.displayOrder.remove(index)
        else:
            self.graph.displayOrder.append(index)
        #print "display order: %s" % (str(self.graph.displayOrder),)
        self.graph.updateValueRange(self.graph.dataView.startTime, self.graph.dataView.endTime)
        self.graph.refreshDisplay()


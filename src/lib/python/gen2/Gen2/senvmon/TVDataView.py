#!/usr/bin/env python

# 2009 Sam Streeper
# 20091201

from __future__ import division

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from bisect import bisect, bisect_left

import time
from TVData import *
from RuntimeDecisionEngine import *

# fixme: where should this common function be?
def averageColor(color1, color2, weight1=1, weight2=1):
    divisor = weight1 + weight2
    averageR = (weight1*color1.red() + weight2*color2.red())/divisor
    averageG = (weight1*color1.green() + weight2*color2.green())/divisor
    averageB = (weight1*color1.blue() + weight2*color2.blue())/divisor
    return QColor(averageR, averageG, averageB)

# A TVDataView is instantiated by a TimeValueGraph
# Consider (or fixme?): Graph keeps a reference to dataview and dataview keeps
# reference to graph.  Also dataview isn't really independent, but queries a lot
# into its graph without formal interfaces.  What to do?
class TVDataView(QWidget, Decider):
    def __init__(self, graphWidget, parent=None, size=QSize(30,30)):
        super(TVDataView,self).__init__(parent)
        self.graph = graphWidget
        self.startTime = self.endTime = None
        self.minval = self.maxval = None
        self.drawBorder = False
        #self.drawBorder = True
        # size parameter is minimum, but dataview should be as big as possible
        self.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        self._minSize = size
        self.setMouseTracking(True)

    def minimumSizeHint(self):
        return self._minSize


    def dataviewRect(self):
        '''
        The dataviewRect fits within this widget's rect() and has a suitable margin
        based on the graph's dataviewMargin
        '''
        rect = self.rect()
        margin = self.graph.dataviewMargin
        return QRect(margin.width(), margin.height(), rect.width() - (2*margin.width()), \
                     rect.height() - (2*margin.height()))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, self.graph._antialiased)
        
        dataviewRect = self.dataviewRect()

        if self.drawBorder:
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(Qt.darkGray, 0, Qt.SolidLine))
            painter.drawRect(dataviewRect)

        if None in (self.startTime, self.endTime, self.minval, self.maxval):
            return

        width = dataviewRect.width()
        timeInterval = self.endTime - self.startTime
        widthPerTime = width / timeInterval
        height = dataviewRect.height()
        valueInterval = self.maxval - self.minval
        heightPerValue = height / valueInterval

        painter.setClipRect(dataviewRect.x(),0, dataviewRect.width(), self.rect().height())

        if self.graph.coordinator.timeSelected:
            if self.graph.coordinator.selectionTime0 <= self.graph.coordinator.selectionTime1:
                time0 = self.graph.coordinator.selectionTime0
                time1 = self.graph.coordinator.selectionTime1
            else:
                time0 = self.graph.coordinator.selectionTime1
                time1 = self.graph.coordinator.selectionTime0
            if not ((time0 < self.startTime and time1 < self.startTime) or
                (time0 > self.endTime and time1 > self.endTime)):
                time0 = max(time0, self.startTime)
                time1 = min(time1, self.endTime)
                # fixme: get a sane selection color from the current theme
                selectionColor = QColor('#fcd6a0')
                painter.setBrush(selectionColor)
                painter.setPen(QPen(Qt.black, 0, Qt.NoPen))
                x0 = ((time0 - self.startTime) * widthPerTime) + dataviewRect.x()
                x1 = (time1 - self.startTime) * widthPerTime + dataviewRect.x()
    
                painter.drawRect(QRectF(x0, dataviewRect.y(), max(x1-x0, 1), dataviewRect.height()))

        
        # This is a bit odd: Ruler is maybe too integrated since it draws and handles interface
        # and it alone has the knowlege about how it will pick and mark its rules for a range.
        # (ie more clever than good design).  Be that as it may, the rules are dynamic but the
        # ruler leaves a handy list of its chosen rule marks in the graph's valueGrid attribute (yikes)
        # so the dataView can lay a grid to match the ruler's full tick marks.
        if self.graph.drawValueGrid and self.graph.valueGrid:
            # fixme: set the grid color from the current theme
            painter.setPen(QPen(QColor(240,240,240), 0, Qt.SolidLine))
            for y in self.graph.valueGrid:
                #yval = dataviewRect.y() + y
                #painter.drawLine(dataviewRect.x()+1, yval, dataviewRect.width()-2, yval)
                painter.drawLine(dataviewRect.x()+1, y, dataviewRect.width()-2, y)
        
        #for dataStore in self.graph.dataStores:
        # fixme: current color fetching scheme sucks
        #for i, dataStore in enumerate(self.graph.dataStores):
        for i in self.graph.displayOrder:
            dataStore = self.graph.dataStores[i]
            color = self.graph.DATACOLORS[i]

            # initiate the generator for my timeValue data
            beginIndex, endIndex = dataStore.indiceesForTimeRange(self.startTime, self.endTime)

            # fixme: If the time step is large compared to the display window, I'll backstep to try & start from a data 
            # point before the beginning time (with drawing clipped); this should be tuned for variable sampling intervals
            # fixme 2: with new features I added, I sometimes want to draw to the point after the endTime
            #if ((self.endTime - self.startTime) < (3*60)):
            if beginIndex > 0:
                beginIndex -= 1
            if endIndex < len(dataStore)-1:
                endIndex += 1

            maxDelta = None
            if hasattr(self.graph, "maxDeltas") and self.graph.maxDeltas != None:
                maxDelta = self.graph.maxDeltas[i]

            if (endIndex - beginIndex) < (2 * width):
                self.drawGraphFromData(painter, color, dataStore, beginIndex, endIndex, widthPerTime, heightPerValue, maxDelta)
            else:
                # We have way more data points than pixels, draw the 50,000 foot view from the cache
                # There's an assumption here that the data has somewhat regular spacing
                '''
                if self.decide("display", "drawRects", Decider.ACT):
                    self.drawRectsFromCache(painter, color, dataStore, self.startTime, self.endTime, width, widthPerTime, heightPerValue, maxDelta)
                else:
                    self.drawPolygonsFromCache(painter, color, dataStore, self.startTime, self.endTime, width, widthPerTime, heightPerValue, maxDelta)
                '''
                self.drawPolygonsFromCache(painter, color, dataStore, self.startTime, self.endTime, width, widthPerTime, heightPerValue, maxDelta)

        try:
            if ((not self.graph.timeIsAnchored()) and 
                    #(self.graph.coordinator.mouseEventGraph == self.graph) and
                    (self.graph.coordinator.timeUnderCursor != None)):
                for i in self.graph.displayOrder:
                    try:
                        # fixme: the following comment describes an allegedly depricated 
                        # mechanism and might  be somewhat inaccurate (or not):
                        # dataLabel is my unique key for the values under the cursor that
                        # were (yuck) grabbed during the graph's mouseMoveEvent.  The following 
                        # drawing was probably triggered by that event
                        dataLabel = self.graph.dataLabels[i]
                        timeValue = self.graph.TVAfterCursor[dataLabel]
                        color = self.graph.DATACOLORS[i]
                        self.highlightTimeValue(timeValue, painter, color, widthPerTime, heightPerValue)
                    except KeyError, e:
                        # The coordinator has no timeValue for this (datalabel & datastore)
                        # Not a problem, cursor is probably out of bounds
                        #print "stepping through highlighted values raised: %s" % (str(e),)
                        pass
        except AttributeError, ae:
            # the coordinator might not have a mouseEventGraph yet, not a problem
            #print "XXX attribute error: %s" % (str(ae),)
            pass

    def highlightTimeValue(self, timeValue, painter, color, widthPerTime, heightPerValue):
        RECTWIDTH = 6
        dataviewRect = self.dataviewRect()
        try:
            x = ((timeValue[0] - self.startTime) * widthPerTime) - (RECTWIDTH/2) + dataviewRect.x()
            y = ((self.maxval - timeValue[1]) * heightPerValue) - (RECTWIDTH/2) + dataviewRect.y()
            
            borderBlendColor = QColor('#ffffff')
            borderColor = averageColor(color, borderBlendColor, weight2=3)
            painter.setBrush(color)
            painter.setPen(QPen(borderColor, 1.5, Qt.SolidLine))
            painter.drawRect(QRectF(x,y, RECTWIDTH, RECTWIDTH))
        except TypeError, e:
            # probably tried to do calc y component from legal None value
            pass

    
    def drawGraphFromData(self, painter, color, dataStore, beginIndex, endIndex, widthPerTime, \
                          heightPerValue, maxDelta, drawAllData=True):
        if self.graph.isAntialiased():
            lineWidth = 1
        else:
            lineWidth = 2
        painter.setPen(QPen(color, lineWidth, Qt.SolidLine))
        timeValueList = dataStore.tvDataForIndicees(beginIndex, endIndex)
        lastY = None
        lastTime = None
        lastVal = None
        y = None
        dataviewRect = self.dataviewRect()
        for timeValue in timeValueList:
            didDrawLine = False
            try:
                #print "    got time:%s  value:%s" % (str(timeValue[0]),str(timeValue[1]))
                x = (timeValue[0] - self.startTime) * widthPerTime + dataviewRect.x()
                y = (self.maxval - timeValue[1]) * heightPerValue + dataviewRect.y()
                # force discontinuity if difference in values greater than graph's maxDeltas
                if maxDelta and lastVal != None and (abs(lastVal - timeValue[1]) > maxDelta):
                    lastY = None
                # force discontinuity if great time gap between datum
                if timeValue[0] - self.graph.dataExpiry() > lastTime:
                    lastY = None
            except TypeError, e:
                #print "        whoa, type error"
                y = None
                lastY = None
            # if lastY != None, then I will have also set lastX != None
            if lastY != None:
                # drawAllData draws a line vertex for all datum; 
                # Otherwise this won't draw until the new vertex has moved a pixel
                if drawAllData or ((abs(x-lastX) >= 1) or (abs(y-lastY) >=1)):
                    try:
                        #print "drawing %s,%s - %s,%s" % (str(lastX), str(lastY), str(x), str(y))
                        painter.drawLine(lastX, lastY, x, y)
                        didDrawLine = True
                    except:
                        # TypeError ?
                        # failed to draw line, this data sucks so scaling math screwed up
                        pass
            if ((lastY == None) or didDrawLine):
                lastX = x
                lastY = y
            lastTime = timeValue[0]
            lastVal = timeValue[1]

            
    def drawRectsFromCache(self, painter, color, dataStore, startTime, endTime, width, widthPerTime, \
                           heightPerValue, maxDelta):
        maxInterval = 3 / widthPerTime
        minMaxRegionList = dataStore.minMaxRegionsForTimeRange(startTime, endTime, width, maxInterval)

        y1 = None
        fillBlendColor = QColor('#ffffff')
        averageR = (fillBlendColor.red() + color.red())/2
        averageG = (fillBlendColor.green() + color.green())/2
        averageB = (fillBlendColor.blue() + color.blue())/2
        lightFillColor = QColor(averageR, averageG, averageB)
        painter.setBrush(lightFillColor)
        painter.setPen(QPen(color, 0, Qt.SolidLine))
        dataviewRect = self.dataviewRect()

        for mmRegion in minMaxRegionList:
            (minval1, maxval1, containsNone, time1, time2) = mmRegion

            shouldDraw = True
            try:
                x1 = (time1 - self.startTime) * widthPerTime + dataviewRect.x()
                w1 = (time2 - time1) * widthPerTime
                y1 = (self.maxval - maxval1) * heightPerValue + dataviewRect.y()
                h1 = (maxval1 - minval1) * heightPerValue
                # force discontinuity if difference in values greater than graph's maxDeltas
                if maxDelta and (abs(maxval1 - minval1) > maxDelta):
                    shouldDraw = False
                # force discontinuity if great time gap between datum
                if time2 - (1.2 * maxInterval) > time1:
                    shouldDraw = False
            except TypeError, e:
                shouldDraw = False
            if shouldDraw:
                try:
                    #print "%s drawing Rect: %0.2f %0.2f  %0.2f %0.2f" % (self.graph.key, x1, y1, w1, h1)
                    painter.drawRect(QRectF(x1,y1, w1,h1))
                except:
                    # TypeError ?
                    print "draw from cache failed to draw, something wonky"
                    pass


    def drawPolygonsFromCache(self, painter, color, dataStore, startTime, endTime, width, widthPerTime, \
                           heightPerValue, maxDelta):
        maxInterval = 3 / widthPerTime
        minMaxRegionList = dataStore.minMaxRegionsForTimeRange(startTime, endTime, width, maxInterval)

        fillBlendColor = QColor('#ffffff')
        lightFillColor = averageColor(fillBlendColor, color)

        painter.setBrush(lightFillColor)
        painter.setPen(QPen(color, 1, Qt.SolidLine))
        
        maxList = []
        minList = []
        lastRect = None
        dataviewRect = self.dataviewRect()

        for mmRegion in minMaxRegionList:
            (minval1, maxval1, containsNone, time1, time2) = mmRegion

            shouldDraw = True
            try:
                x1 = (time1 - self.startTime) * widthPerTime + dataviewRect.x()
                w1 = (time2 - time1) * widthPerTime
                y1 = (self.maxval - maxval1) * heightPerValue + dataviewRect.y()
                h1 = (maxval1 - minval1) * heightPerValue
                # force discontinuity if difference in values greater than graph's maxDeltas
                if maxDelta and (abs(maxval1 - minval1) > maxDelta):
                    shouldDraw = False
                # force discontinuity if great time gap between datum
                if time2 - (1.2 * maxInterval) > time1:
                    shouldDraw = False
                if containsNone:
                    shouldDraw = False
            except TypeError, e:
                shouldDraw = False
            if shouldDraw:
                if len(maxList) == 0:
                    lastRect = QRectF(x1,y1, w1,h1)
                else:
                    lastRect = None
                x = x1 + (w1 / 2)
                maxList += [x,y1]
                # make sure region is 1 pixel high
                h1 = max(h1, 1)
                # minList is gonna be reversed
                minList += [y1+h1, x]
            else:
                # bad region so I won't continue the old plot, just emit it now
                try:
                    if lastRect:
                        painter.drawRect(lastRect)
                    elif len(maxList) > 0:
                        # draws the top of the maxes, then return to origin by drawing mins in reverse
                        painter.drawPolygon(QPolygon(maxList + minList[::-1]))
                except:
                    # TypeError ?
                    print "draw from cache failed to draw, something wonky"
                finally:
                    maxList = []
                    minList = []
                    lastRect = None
        # Now emit the last thing to be drawn
        try:
            if lastRect:
                painter.drawRect(lastRect)
            elif len(maxList) > 0:
                # draws the top of the maxes, then return to origin by drawing mins in reverse
                painter.drawPolygon(QPolygon(maxList + minList[::-1]))
        except:
            # TypeError ?
            print "draw from cache failed to draw, something wonky"
        

            
    def setTimeRange(self, startTime, endTime):
        self.startTime = startTime
        self.endTime = endTime

    def updateValueRange(self, minval, maxval):
        self.minval = minval
        self.maxval = maxval


    def mousePressEvent(self,event):
        if not event.button() == Qt.LeftButton:
            return
        self.dragging = True

        self.graph.coordinator.timeAnchored = False
        dataviewRect = self.dataviewRect()

        scale = (event.pos().x() - dataviewRect.x()) / dataviewRect.width()
        clickTime = self.startTime + (self.graph.coordinator.timeRange * scale)
        
        # extend the existing selection if shift-click or ctl-click
        if (self.graph.coordinator.timeSelected and
                (event.modifiers() & (Qt.ShiftModifier | Qt.ControlModifier))):
            if self.graph.coordinator.selectionTime1 < self.graph.coordinator.selectionTime0:
                # time-order the selection endpoints for testing sanity
                tmp = self.graph.coordinator.selectionTime0
                self.graph.coordinator.selectionTime0 = self.graph.coordinator.selectionTime1
                self.graph.coordinator.selectionTime1 = tmp
                
            # if clickTime closer to selection start, set the original click to selection end
            if (abs(clickTime - self.graph.coordinator.selectionTime0) <
                abs(clickTime - self.graph.coordinator.selectionTime1)):
                self.graph.coordinator.selectionTime0 = self.graph.coordinator.selectionTime1

            self.graph.coordinator.selectionTime1 = clickTime
            self.graph.refreshDisplay()

        else:
            self.graph.coordinator.timeSelected = False
            self.graph.coordinator.selectionTime0 = clickTime
            self.graph.coordinator.selectionTime1 = None
    
            # fixme: it's a bit unfortunate to have to draw everything now just to get 
            # everything drawn in the new state but what to do?
            self.graph.coordinator.setTimeRange(self.startTime,self.endTime)


    def mouseMoveEvent(self,event):
        #X------------------------------------------
        # This event will leave some state in the coordinator.  There may or may not be
        # applicable event information in the coordinator when each graph's dataview draws, so the 
        # code that draws mouse position related data is protected from the expected exceptions
        # This design is ugly and needs a rethink but it saves me lots of full redisplays which are expensive
        # (fixme: the full redraws should not be necessary once implemented with sane qt code)
        dataviewRect = self.dataviewRect()
        if not self.graph.timeIsAnchored():
            # first note the x position of the event and the time at that position
            x = event.pos().x() - dataviewRect.x()
            # I'm going to note the values at (after) the cursor for informative display
            eventPositionRatio = x / dataviewRect.width()
            self.graph.coordinator.timeUnderCursor = self.startTime + \
                (eventPositionRatio * self.graph.coordinator.timeRange)
            try:
                if self.graph.coordinator.mouseEventGraph != self.graph:
                    oldGraph = self.graph.coordinator.mouseEventGraph
                    # eliminate the old displayed timeValues
                    oldGraph.TVAfterCursor = {}
                    oldGraph.refreshDisplay()
            except AttributeError, e:
                pass
            self.graph.coordinator.mouseEventGraph = self.graph
            # clear previous data
            self.graph.TVAfterCursor = {}

            # fixme: I now feel there's no reason that I need to fetch the datapoints under the
            # cursor at the mouseMoveEvent time; I should just look up the points at the coordinator's 
            # timeUnderCursor at display time (paintEvent) so I could display all the coordinator's
            # graph's dataValues, assuming I had a way to do that with acceptable performance
            for i in self.graph.displayOrder:
                dataStore = self.graph.dataStores[i]
                index = dataStore.leftIndexForTime(self.graph.coordinator.timeUnderCursor)
                if index < len(dataStore):
                    # store the timeValue after the cursor for this displayed datastore
                    # (yes the hash key is goofy but unique and hashable anyway)
                    # The value here will be used for both dataLabel & dataView displays
                    self.graph.TVAfterCursor[self.graph.dataLabels[i]] = dataStore[index]

        #X------------------------------------------

        if ((event.buttons() & Qt.LeftButton) and self.dragging):
            if self.graph.coordinator.selectionTime1 == None:
                self.graph.coordinator.timeSelected = True
            # FIXME fixme: if event isn't within view, autoscroll all graphs
            scale = (event.pos().x() - dataviewRect.x()) / dataviewRect.width()
            self.graph.coordinator.selectionTime1 = self.startTime + (self.graph.coordinator.timeRange * scale)
        if (event.buttons() & Qt.LeftButton) or not self.graph.timeIsAnchored():
            # Should be like this, but performance is unacceptable, I need to revisit how to display
            # the points under the cursor without redrawing the static displays
            #self.graph.coordinator.refreshDisplays()
            self.graph.refreshDisplay()


    def mouseReleaseEvent(self,event):
        if not (event.button() == Qt.LeftButton and self.dragging):
            return
        self.dragging = False
        dataviewRect = self.dataviewRect()

        if self.graph.coordinator.selectionTime1 == None:
            self.graph.coordinator.timeSelected = False
        else:
            # FIXME fixme: if event isn't within view, autoscroll all graphs
            scale = (event.pos().x() - dataviewRect.x()) / dataviewRect.width()
            self.graph.coordinator.selectionTime1 = self.startTime + (self.graph.coordinator.timeRange * scale)
        self.graph.coordinator.setTimeRange(self.startTime,self.endTime)
    def wheelEvent(self, event):
        if self.graph.coordinator:
            zoomValue = (event.delta() / 120.0) * 1.25
            if zoomValue < 0:
                zoomValue = 1.0 / abs(zoomValue)
            if self.graph.coordinator.timeAnchored:
                self.graph.coordinator.zoom(zoomValue)
                # fire a fake event to update the children
                self.graph.coordinator.timerEvent(None)
            else:
                dataviewRect = self.dataviewRect()
                # first note the x position of the event and the time at that position
                x = event.pos().x() - dataviewRect.x()
                # sanity checking, should not be necessary...
                x = max(x, 0.001)
                x = min(x, dataviewRect.width())
                eventPositionRatio = x / dataviewRect.width()
                eventTime = self.graph.dataView.startTime + (eventPositionRatio * self.graph.coordinator.timeRange)

                self.graph.coordinator.zoom(zoomValue)
                # then have the coordinator zoom such that the time stays in the same position with the new coordinator.timeRange
                startTime = eventTime - (eventPositionRatio * self.graph.coordinator.timeRange)
                self.graph.coordinator.setTimeRange(startTime, startTime + self.graph.coordinator.timeRange)

#!/usr/bin/env python

# 2009 Sam Streeper
# 20091112
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Apr 27 08:24:50 HST 2012
#]
#
# TimeValueGraph is a PyQT4 widget that displays a simple clear graph of data values over time.
# The intention is to display and monitor real time data feeds.  Multiple graphs are linked
# to display a synchronized view of all data.  Run this file for an example:
#    $ ./timeValueGraph.py &
# You can subclass to provide your data and custom behaviour

from __future__ import division
import sys
import os
import math
import threading

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import time
import cPickle
import shelve
import datetime

from ruler import *
from TVDataView import *
from propertyDecorator import *
from TVDataLabel import *

version = '20090430.0'

TVG_DEFAULTSIZE = (430,135)

# fixme: sammy consider the double buffering from
#http://www.commandprompt.com/community/pyqt/x2765

class TimeValueGraph(QWidget):
    #DEFAULTSIZE = (430,135)
    # fixme: hide datacolors array and access via method, let classes init color range
    DATACOLORS = (QColor('#7f0084'),QColor('#107800'),QColor('#10227f'), 
                  QColor('#564900'),QColor('#bb1000'),QColor('#1082cf'),
                  QColor('#e12080'),QColor('#05bb60'),QColor('#40aa10'))

    def __init__(self, parent=None, size=TVG_DEFAULTSIZE, displayTime=True, key=None, \
                 datastoreCount=0, dataLabelFormats=None, title=None):

        super(TimeValueGraph, self).__init__(parent)

        # a unique identifier the data could be persisted under
        self.key = key
        
        #self.setStyleSheet("border: none")
        
        self.warningColor = QColor(255,255,180)
        self.errorColor = QColor(255,220,220)
        self.selectionBackgroundColor = QColor(255,240,232)
        self.initBackgroundColor(QColor(Qt.white))
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        
        self.title = title
        self._antialiased = False
        
        self.minDisplayVal = self.maxDisplayVal = None
        self.softMinDisplayVal = self.softMaxDisplayVal = None
        self.hardMinDisplayVal = self.hardMaxDisplayVal = None

        self.dataColors = TimeValueGraph.DATACOLORS
        self.colorDict = {}

        self.setLayout(QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setMargin(0)

        self.labelContainer = LabelContainer(self)
        self.layout().addWidget(self.labelContainer)

        sideMargins = QWidget(self)
        # policy: width as big as possible, height as big as possible but start with sizehint
        sideMargins.setSizePolicy(QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding))
        self.layout().addWidget(sideMargins)
        # 3 pixels at bottom
        self.layout().addSpacing(3) 

        sideMarginsLayout = QHBoxLayout()
        sideMargins.setLayout(sideMarginsLayout)
        sideMarginsLayout.setSpacing(0)
        sideMarginsLayout.setMargin(0)
        # 3 pixels on the left
        sideMarginsLayout.addSpacing(3) 

        # gridWidget contains timeValueDataView & ruler(s)
        gridWidget = self.gridWidget = QWidget(sideMargins)
        sideMarginsLayout.addWidget(gridWidget)
        # 3 pixels on the right
        sideMarginsLayout.addSpacing(3) 

        gridWidget.setLayout(QGridLayout())
        gridLayout = gridWidget.layout()
        gridLayout.setSpacing(0)
        gridLayout.setMargin(0)
        #gridLayout.setColumnStretch(0,0)
        #gridLayout.setColumnStretch(1,1)
        
        # for the purpose of layout, the dataview has no margin so it gets the max
        # area to draw without clipping.  But in fact it's nice to have a soft margin
        # that I can draw beyond, while still separating rulers & dataview
        self.dataviewMargin = QSize(0,1) #2,5

        self.valueRuler = ValueRuler(self, parent=gridWidget)
        gridLayout.addWidget(self.valueRuler,0,0)
        self.drawValueGrid = False
        self.valueGrid = None

        if displayTime:
            self.timeRuler = TimeRuler(self, parent=gridWidget)
            gridLayout.addWidget(self.timeRuler,1,1)
        else:
            self.timeRuler = None

        self.dataStores = self.createDatastores(_datastoreCount=datastoreCount)
        #print 'DATASTORES:%s' %self.dataStores
        self.displayOrder = list(range(len(self.dataStores)))
        self.dataView = self.createDataViewForGraph(self)
        self.idealSize = size    # a tupe
        #self.dataView.setMinimumSize(size[0], size[1])
        gridLayout.addWidget(self.dataView,0,1)
        
        if dataLabelFormats:
            self.dataLabels = []
            # fixme: the following dataLabelsToDataStores dict doesn't gain appreciable performance
            # but makes maintenance a pain.  If an indexed lookup is beneficial (not clear...) I think 
            # this attribute ought to be implemented as a function that builds the indexed answer on the fly
            self.dataLabelsToDataStores = {}
            
            for i in range(len(dataLabelFormats)):
                dataLabel = DataLabel(self,dataLabelFormats[i])
                # fixme: the following line means subclassing responsibility, rewrite to
                # know the association on the fly
                self.dataLabelsToDataStores[dataLabel] = self.dataStores[i]
                self.colorDict[dataLabel] = TimeValueGraph.DATACOLORS[i]
                self.dataLabels.append(dataLabel)
                self.labelContainer.layout().addWidget(dataLabel)

        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding,
                                       QSizePolicy.Expanding))
        self.setCoordinator(None)
        
        
    def createDataViewForGraph(self, graphWidget):
        return TVDataView(graphWidget)

    def backgroundColor(self):
        if self.timeIsAnchored():
            return self._backgroundColor
        return self.selectionBackgroundColor
    
    def initBackgroundColor(self, color):
        self.normalColor = self._backgroundColor = color

    def setBackgroundColor(self, color):
        self._backgroundColor = color

        
    def setAntialiased(self, val):
        self._antialiased = val
        #self.setRenderHint(QPainter.Antialiasing, self._antialiased)
    
    def isAntialiased(self):
        return self._antialiased

    def sizeHint(self):
        return QSize(self.idealSize[0], self.idealSize[1])

    """
    # I thought I'd turn antialiasing on/off on the fly, but you can't do this inside paint
    # (ie after rendering parameters are set & individual widgets are redrawing)
    def disableAntialiasing(self):
        # Turns off antialiasing but doesn't change the global graph setting 
        self.setRenderHint(QPainter.Antialiasing, False)

    def restoreAntialiasSetting(self):
        self.setRenderHint(QPainter.Antialiasing, self._antialiased)
    """

    # Subclasses will override this to return a list of persisted data to be graphed
    def createDatastores(self, _datastoreCount=0):
        return map(lambda placeholder: CTVData(), range(_datastoreCount))
    
    # Subclasses should override
    # Data will be gathered & added to the dataview's datastore
    # I could timestamp the data with the time passed in here, but it might be cooler if
    # old data were stamped with its true collection time (?)
    #
    # When you have written the code to create the suitable # of datastores (createDatastores())
    # and fetch the data to be displayed (fetchData()),
    # fetchData() should call storeData() to perform housekeeping and ready the updated data for the TVDataView
    def fetchData(self, now, stat_vals):
        pass

    # Sometimes my datasource burps and returns a non-numeric type that fails in math operations for scaling
    # so I'm only going to add numeric values to my timeValue datastore
    def valueIsOK(self, val):
        if val == None:
            return True
        try:
            test = val - 1.0
        except TypeError:
            return False
        return True

    def storeDatum(self, time, value, datastoreIndex):
        dataStore = self.dataStores[datastoreIndex]
        # fixme: this should be asserted by the datastore instead of here
        try:
            assert time >= dataStore[-1][0]
        except IndexError, e:
            # No worries on IndexError, happens when there is no last time (new datastore)
            pass
        dataStore.cullDataOlderThan(self.coordinator.maxTimeRange)
        if self.valueIsOK(value):
            dataStore.append((time, value))
    
    # In my use case, I tend to poll for all values at once, and then save them together.
    # However, as long as each datastore is simply appended with sequential data, there is
    # no need for any synchronicity amongst the datastores.  You can store data coming at
    # different rates OK.
    def storeData(self, time, values):
        for i, value in enumerate(values):
            self.storeDatum(time, value, i)

    # called when the current time changes or the zoom range changes
    # === This is the important driving method for display updates ====
    def setTimeRange(self, startTime, endTime):
        # I turn on antialiasing for small time ranges for a better look
        # and turn it off on large range for better performance
        # fixme: This should be tunable/settable, but what metric will decide?
        # (for now I've tuned it for my particular datarate and CPU power...)
        if ((endTime - startTime) < (2.5 * 60 * 60)):
            self.setAntialiased(True)
        else:
            self.setAntialiased(False)
            
        self.dataView.setTimeRange(startTime, endTime)
        if self.timeRuler:
            self.timeRuler.setTimeRange(startTime, endTime)
        self.updateValueRange(startTime, endTime)
        self.refreshDisplay()

    def sign(self, x):
        return cmp(x,0)
    
    def updateValueRange(self, startTime, endTime):
        if self.hardMinDisplayVal != None:
            minval = self.hardMinDisplayVal
        elif self.softMinDisplayVal != None:
            minval = self.softMinDisplayVal
        else:
            minval = None

        if self.hardMaxDisplayVal != None:
            maxval = self.hardMaxDisplayVal
        elif self.softMaxDisplayVal != None:
            maxval = self.softMaxDisplayVal
        else:
            maxval = None

        if self.hardMinDisplayVal == None or self.hardMaxDisplayVal == None:
            # need to get min & max from data
            #for i in range(len(self.dataStores)):
            for i in self.displayOrder:
                small, big = self.dataStores[i].minMaxForTimeRange(startTime, endTime)

                if ((self.hardMinDisplayVal == None) and (minval == None or small < minval)
                    and (small != None)):
                    minval = small
                if ((self.hardMaxDisplayVal == None) and (maxval == None or big > maxval)
                    and (big != None)):
                    maxval = big

        if minval == maxval and minval != None:
            if minval == 0:
                minval = -1
                maxval = 1
            else:
                if self.sign(minval) == -1:
                    minval = minval * 1.1
                    maxval = maxval * 0.9
                else:
                    minval = minval * 0.9
                    maxval = maxval * 1.1

        self.dataView.updateValueRange(minval, maxval)
        self.valueRuler.updateValueRange(minval, maxval)
    
    def setCoordinator(self, coordinator):
        self.coordinator = coordinator
        

    
    def refreshDisplay(self):
        self.update()

    def colorFor(self, object):
        try:
            return self.colorDict[object]
        except (TypeError, KeyError), e:
            pass
        # we got an object that doesn't have a color, something wasn't set up correctly
        return Qt.black

    def dataExpiry(self):
        """Returns number of seconds after which data is not current or consecutive datum aren't connected."""
        return 30

    def currentValueForDataLabel(self, dataLabel):
        if not self.timeIsAnchored():
            try:
                if (self.coordinator.mouseEventGraph != self) or (self.coordinator.timeUnderCursor == None):
                    return None
                return self.TVAfterCursor[dataLabel][1]
            except:
                return None
            return None
        try:
            # get the last time-value pair from the appropriate datastore
            timeAndValue = self.dataLabelsToDataStores[dataLabel][-1]
            # if the data is expired, don't return a 'current' value
            if (timeAndValue[0] + self.dataExpiry()) < time.time():
                return None
            # return the current value
            return timeAndValue[1]
        except:
            return None
        return None

    def indexForDataLabel(self, dataLabel):
        for i in range(len(self.dataLabels)):
            if dataLabel == self.dataLabels[i]:
                return i
        # fixme: error should raise
        return None
    
    # I don't want to resize the dataLabels when I fetch new data, so I'll size them before
    # I lay out the graph.  You might want to override some of the following methods to
    # provide space for the longest data strings you expect to see.  You can set a global
    # default 'long string' length, or set a longest string length per datastore.
    # For the calculation of fontMetrics, the following string will be converted to a float
    # so you should start and end it with significant (non-zero) digits
    def _longestDataValueString(self):
        return "-800.08"
    
    def longestStringForDataIndex(self, index):
        return self._longestDataValueString()
    
    def longestStringForDataLabel(self, dataLabel):
        return self.longestStringForDataIndex(self.indexForDataLabel(dataLabel))

    def timeIsAnchored(self):
        return self.coordinator.timeAnchored

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(self.backgroundColor())
        painter.fillRect(QRectF(0,0,self.geometry().width(),self.geometry().height()), QBrush(self.backgroundColor()))

        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(Qt.darkGray, 0, Qt.SolidLine))
        BOTTOM = self.geometry().height()-2
        RIGHT = self.geometry().width()-2
        painter.drawLine(1, 0, 1, BOTTOM)
        painter.drawLine(1, BOTTOM, RIGHT, BOTTOM)
        painter.drawLine(RIGHT, 0, RIGHT, BOTTOM)

# timeValueGraphs (subclasses, really) will be added added to a TVCoordinator
# via addGraph()
# time value graph coordinator will layout its children, zoom them together,
# keep a timer and broadcast a time signal for synchronous data fetching and display updates
class TVCoordinator(object):
    # default display is 4 hours, value is a float in seconds
    DefaultTimeRange = 4 * (60 * 60)
    MaxTimeRange = 10 * 24 * (60 * 60)
    MinTimeRange = 30
    
    def __init__(self, stat_dict, minute, envi_file, key, logger, parent=None):
        self.graphs = []
        self.timerId = 0
        self.timeRange = TVCoordinator.DefaultTimeRange
        self.maxTimeRange = TVCoordinator.MaxTimeRange
        self.minTimeRange = TVCoordinator.MinTimeRange
        self._timeAnchored = True
        self._timeSelected = False
        
        self.envi_file=envi_file
        self.key=key
        #self.pickle=pickleName
        self.logger=logger
        self.__stat_dict=stat_dict
        self.minute=minute
        self.timer_save_data = QTimer()
        self.timer_save_data.connect(self.timer_save_data, SIGNAL("timeout()"),
                                     self.save_data_interval)
        self.timer_save_data.start(60000*minute) #60000=1min
        self.timer = QTimer()
        self.timer.timeout.connect(self.timerEvent)
        
        self.statuslock=threading.RLock()
   
        self.savelock=threading.RLock()
  
    @prop
    def timeAnchored():
        def _setAnchored(self, anchoredValue):
            if anchoredValue:
                self._timeSelected = False
            self._timeAnchored = anchoredValue

        return {'fset': _setAnchored }

    @prop
    def timeSelected():
        pass

    @property
    def stat_dict(self):
        with self.statuslock:
            self.logger.debug('getting stat_dict....')
            return self.__stat_dict

    @stat_dict.setter
    def stat_dict(self, value):
        with self.statuslock:
            self.logger.debug('setting stat_dict....')
            self.__stat_dict=value

    def addGraph(self, tvGraph):
        self.graphs.append(tvGraph)
        tvGraph.setCoordinator(self)

    def save_data_interval(self):
        self.logger.info('saving data %d min....' %(self.minute))

        #tmp_key='%s' %datetime.date.today()
        #self.logger.info('key=%s  tmp_key=%s' %(self.key_str, tmp_key))
        #if not tmp_key in self.key_str:
        #    self.key_str=tmp_key
        
        with self.savelock:
            self.logger.info('saving stat_dict....')
            self.saveDatastoresShelve()
#        if not self.timerId:
#            self.logger.info('saving data interval <%d min>' %(minute))
#            self.timerEvent(None)
#            self.timerId = self.timer.start(1000 * 60 * minute)

        
    def runAtInterval(self, interval):
        if not self.timerId:
            # fire a fake event now before I start the timer
            self.timerEvent(None)
            # invoke timer event every 5 seconds
            self.logger.debug('setting interval <%d sec>' %(interval))
            self.timer.setInterval(1000 * interval)
            self.timerId = True
            self.timer.start()

#    def init_time_anchored(self):
#        now = time.time()
#        if self.timeAnchored:
#            try:
#                self.setTimeRange(now - self.timeRange, now)
#            except Exception,e:
#                pass

#    def update_status(self, stat_val):
#        self.logger.debug('stat_val %s' %stat_val)
        
#        with self.lock:
#            now = time.time()
#            [graph.fetchData(now, self.stat_val) for graph in self.graphs]
                
#        if self.timeAnchored:
#            try:
#                self.setTimeRange(now - self.timeRange, now)
#            except Exception,e:
#                pass

#    def run(self):
#        # default is 5 sec
#        self.runAtInterval(interval=5)

    def stop(self):
        if not self.timerId:
            self.killTimer(self.timerId)
        self.timerId = 0

    def setTimeRange(self, startTime, endTime, calcTimeRange=False):
        if calcTimeRange:
            self.timeRange = endTime - startTime
        for graph in self.graphs:
            try:
                graph.setTimeRange(startTime, endTime)
            except Exception,e:
                pass  

#    def timerEvent(self, event):
#        now = time.time()
        # this method also catches an event such as zooming in/out. then adjust time range.  
#        if self.timeAnchored:
#            try:
#                self.setTimeRange(now - self.timeRange, now)
#            except Exception,e:
#                pass

    def timerEvent(self, event):
        now = time.time()
        # On 'real' timer events, fetch data & update the timeline
        # but don't fetch data on 'fake' events that are fired to update the display (like zoom)
        if event:  
            stat_val=self.stat_dict

            with self.savelock:
                [graph.fetchData(now, stat_val) for graph in self.graphs]
 
            #stat_vals= self.status.fetch(self.stat_dict)
            #for graph in self.graphs:
            #    graph.fetchData(now, stat_vals)
        if self.timeAnchored:
            try:
                self.setTimeRange(now - self.timeRange, now)
            except Exception,e:
                pass

    # The performance of this is unacceptable for interactive stuff
    def refreshDisplays(self):
        for graph in self.graphs:
            graph.setTimeRange(graph.dataView.startTime, graph.dataView.endTime)

    def zoom(self, zoomAmount):
        newTimeRange = self.timeRange * zoomAmount
        #print "zoom amount:%f newRange:%f" % (zoomAmount, newTimeRange)
        if (newTimeRange >= self.minTimeRange) and (newTimeRange <= self.maxTimeRange):
            self.timeRange = newTimeRange

    def saveDatastoresShelve(self):
        ''' save all the datastores to a pickle file in the current directory '''

        #st=time.time()

        self.logger.debug('saving shelve...')
 
        myPersistentData = {}
        
        badWrite = False
        output = None
        try:
            #output = open(self.pickle, 'wb')
            output = shelve.open(self.envi_file)
            self.logger.debug('opening envi file...')
            for tvGraph in self.graphs:
                try:
                    for dataStore in tvGraph.dataStores:
                        dataStore.flushCache()
                    if tvGraph.key != None:
                        myPersistentData[tvGraph.key] = tvGraph.dataStores
                except Exception,e:
                    continue  
            output[self.key]=myPersistentData
            #cPickle.dump(myPersistentData, output)
            self.logger.debug('saving shelve done')
            #print "done saving pickle"
        except Exception, e:
            self.logger.error("shelve save exception: %s" % str(e))
            badWrite = True
        finally:
            #print "closing pickle"
            if output:
                output.close()
            # fixme: if badWrite, erase the file
            #if badWrite:
            #    self.logger.debug("removing bad pickleFile: %s" % (pickleName))
            #    try:
            #        os.remove(pickleName)
            #    except OSError, e:
            #       pass    
        #et=time.time()-st
        #self.logger.info('time to save %f sec' %et ) 

class Global:
    """Generic container for shared variables."""
    #Fixme: I don't like my current persistence design that requires this Global hack;
    #At startup, I read an archive into a global dictionary, and then as objects are
    #initialized, they look for their key in the persisted data dict.
    pass

#################################################################
### =================  main() starts here =======================
#################################################################
def main(options, args):
    import random
    
    class PersistentGraph(TimeValueGraph):
        def createDatastores(self, _datastoreCount):
            if Global.persistentData and (self.key in Global.persistentData):
                dataList = Global.persistentData[self.key]
                return dataList
            return map(lambda placeholder: CTVData(), range(_datastoreCount))
    
    class SineOfTimes(PersistentGraph):
        def fetchData(self, now):
            # create values here
            halfTime = now/20
            longCycle = now/1000
            z = 3 * math.sin(longCycle)
            a = math.sin(halfTime)
            b = math.sin(3 * halfTime)/3
            c = math.sin(5 * halfTime)/5
            d = math.sin(7 * halfTime)/7
            self.storeData(now, (z+a, z+b, z+c, z+d, z+a+b+c+d))


    class SeeSaw(PersistentGraph):
        def fetchData(self, now):
            # create values here
            halfTime = now/28
            longCycle = now/2500
            mediumCycle = now/200
            z = 2.5 * math.sin(longCycle)
            wobble = 0.3 * math.sin(mediumCycle)
            a = math.sin(halfTime)
            try:
                self.gammaRayGlitchCountdown -= 1
                if self.gammaRayGlitchCountdown <= 0:
                    self.gammaRayGlitchCountdown = random.randrange(3000,15000)
                    # introduce an order of magnitude glitch to elucidate cache errors
                    # Give me occasional noise for my signal
                    a += random.uniform(-10, 10)
            except AttributeError, e:
                self.gammaRayGlitchCountdown = random.randrange(2000,10200)
            b = -math.sin(2 * halfTime)/2
            c = math.sin(3 * halfTime)/3
            d = -math.sin(4 * halfTime)/4
            e = math.sin(5 * halfTime)/5
            sawSum = z + a + b + c + d + e
            self.storeData(now, (z,a+wobble, b+wobble, c+wobble, d+wobble, e+wobble, sawSum+wobble))

    class SecondSteps(PersistentGraph):
        def fetchData(self, now):
            hours = int(time.strftime("%H", time.localtime(now)))
            minutes = int(time.strftime("%M", time.localtime(now)))
            seconds = int(time.strftime("%S", time.localtime(now)))

            # list of last values from (hours, minutes, seconds) datastores
            lastValues = []
            for datastore in self.dataStores:
                try:
                    # get the value from the datastore's last timeValue
                    lastValue = datastore[-1][1]
                    # test it for sanity
                    testMathOperations = lastValue - 1
                except (IndexError, TypeError), e:
                    # default former value, all values will be advanced from this lastValue
                    lastValue = -1
                lastValues.append(lastValue)
                    
            if minutes < lastValues[1]:
                # insert a null to break continuity when minutes wrap
                # It might be simpler to just supply a maxDelta value for the minutes datastore,
                # but I wanted to show that you can signal the renderer by inserting a null value.
                # (The renderers may have different responses to nulls in the data stream, though)
                #self.dataStores[1].append((now, None))
                # The unanchored data displays are saner if the discontinuity is placed at the last time
                self.dataStores[1].append((self.dataStores[1][-1][0], None))
            if seconds < lastValues[2]:
                #self.dataStores[2].append((now, None))
                self.dataStores[2].append((self.dataStores[2][-1][0], None))

            # the 'time components' I'm graphing here have a low change rate, but the data is fetched
            # rather frequently on the coordinator's poll, so I'm going to reduce the storage rate
            # Just store (unchanging) data more frequently than the dataExpiry
            COUNTDOWN = 11
            try:
                for i, count in enumerate(self.countdown):
                    self.countdown[i] = count - 1
            except AttributeError, e:
                # first time initialization, counters for hours & minutes data rate reduction
                self.countdown = [COUNTDOWN] * 2
                
            if hours != lastValues[0] or self.countdown[0] <= 0:
                self.storeDatum(now, hours, 0)
                self.countdown[0] = COUNTDOWN
            if minutes != lastValues[1] or self.countdown[1] <= 0:
                self.storeDatum(now, minutes, 1)
                self.countdown[1] = COUNTDOWN
            self.storeDatum(now, seconds, 2)
                
            self.checkSecondsState(seconds)

        def checkSecondsState(self, seconds):
            alarm = (seconds >= 55)
            warning = (seconds >= 50)
            if (alarm):
                if not (self.alarmState == 2):
                    self.alarmState = 2
                    self.setBackgroundColor(self.errorColor)
            elif warning:
                if not (self.alarmState == 1):
                    self.alarmState = 1
                    self.setBackgroundColor(self.warningColor)
            elif self.alarmState:
                self.alarmState = 0
                self.setBackgroundColor(self.normalColor)
                

    pickleName = 'time_value_data.pickle'
    try:
        dataPickle = None
        dataPickle = open(pickleName, 'rb')
        Global.persistentData = cPickle.load(dataPickle)
    except:
        Global.persistentData = {}
    finally:
        if dataPickle:
            dataPickle.close()
        
    app = QApplication(sys.argv)

    coordinator = TVCoordinator()
    coordinator.setWindowTitle(coordinator.tr("Time-Value Graphs"))
    coordinator.minTimeRange = 15
    coordinator.maxTimeRange = 2 * 24 * 60 * 60

    widget = SineOfTimes(size=(500,200), displayTime=False, key='SineOfTimes', datastoreCount=5,
                         title = "Sine of Times",
                    dataLabelFormats=("Fundamental: %0.2f ", "  3x: %0.2f   ",
                                      "5x: %0.2f ", "7x: %0.2f ", "Sum: %0.2f "))
    widget.initBackgroundColor(QColor(210,230,255))
    coordinator.addGraph(widget)


    widget = SeeSaw(size=(500,175), displayTime=False, key='SeeSaw', datastoreCount=7,
                    title = "See Saw",
                    dataLabelFormats=("Long Wave: %0.2f ", "Fundamental: %0.2f ", "  2x: %0.2f   ",
                                      "3x: %0.2f ", "4x: %0.2f ", "5x: %0.2f ", "Sum: %0.2f "))
    widget.initBackgroundColor(QColor(240,240,230))
    coordinator.addGraph(widget)

    
    widget = SecondSteps(size=(500,150), key='SecondSteps', datastoreCount=3, 
                         title = "Second Steps",
                         dataLabelFormats=("Hours:%d ","Minutes:%d ","Seconds:%d "))
    widget.initBackgroundColor(QColor(240,255,245))
    # graph can render discontinuities when changes between consecutive values are too great
    widget.maxDeltas = (23, None, None)
    # don't crop/scale the clock ruler values to the (hour,min,sec) data
    widget.hardMinDisplayVal = -0.1
    widget.hardMaxDisplayVal = 61
    widget.valueRuler.marksPerUnit = 3
    widget.valueRuler.hardValueIncrement = 15
    widget.alarmState = 0
    coordinator.addGraph(widget)

    # Free initialization data
    Global.persistentData = None
    

    coordinator.resize(coordinator.layout().closestAcceptableSize(coordinator, QSize(400,525)))
    #coordinator.setMinimumSize(coordinator.size())

    coordinator.runAtInterval(2)
    coordinator.show()

    appExecReturn = app.exec_()
    coordinator.saveDatastoresPickle(pickleName)
    sys.exit(appExecReturn)

if __name__ == '__main__':

    # a dictionary of persisted objects, my old timeValue datastores
    Global.persistentData = None
    
    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options] command [args]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    
    (options, args) = optprs.parse_args()

    if len(args) != 0:
        optprs.error("incorrect number of arguments")

    # Are we debugging this?
    if options.debug:
        import pdb

        pdb.run('main(options, args)')

    # Are we profiling this?
    elif options.profile:
        import profile

        print "%s profile:" % sys.argv[0]
        profile.run('main(options, args)')

    else:
        main(options, args)

#! /usr/local/bin/python

# Sam Streeper
# 2008-12-04

# StatusGraph is a subclass of LineGraph that graphs status values

from Tkinter import *  # UI widgets and event loop infrastructure
import Tkinter
import Pmw             # Additional UI widgets
import time            # Time functions
import LineGraph
import SOSS.status

DEFAULTGRAPH = ("Label", "black", "white", None, 1, 0, 1)
# used like: gconfig=("Humidity(%)", "black", "white", None, 0, 0, 1, "Humidity: %d%%")

#  DEFAULTLINE contains a list of configurations for the lines that
#  are plotted in the graph.  For each line, there must be a tuple
#  containing the following information:
#  0) Line name
#  1) Line colour
#  2) Line style
#  3) Line width
#  4) Point symbol
#  5) Label format
#  6) Label font
DEFAULTLINE = [('A', '#7f0084',   0, 2, '', "A: %d", "Helvetica 12 bold"),
               ('B', '#107800', 0, 2, '', "B: %d", "Helvetica 12 bold")]

DEFAULTSIZE = (102,430)

#  DEFAULTWINDOW gives the maximum capacity that the data vectors can store.
#  In this case, we can store a maximum of one hour of data sampled at 1 Hz.
DEFAULTWINDOW = 14400

#  DEFAULTSCALE indicates the size (in seconds) of the display window.
#  in the graph at each level.  DEFAULTSSCALE gives the initial display window
#  size to be used.
DEFAULTSSCALE = 5
DEFAULTSCALES = (300, 900, 1800, 3600, 7200, 14400)

#  DEFAULTFONTS gives the fonts for the X and Y scale respectively.
DEFAULTFONTS = ("Helvetica 9", "Helvetica 10")


class StatusGraph(LineGraph.LineGraph):
    def __init__(self, parent, size=DEFAULTSIZE,
                 gconfig=DEFAULTGRAPH, lconfig=None,
                 pwindow=DEFAULTWINDOW, iscale=DEFAULTSSCALE, pscales=DEFAULTSCALES, 
                 ptickfont=DEFAULTFONTS, 
                 statusKeys=(), statusFormats=None,
                 alarmValues=None,
                 maxDeltas=None,
                 title="", displayTime=False, background=None,
                 statusObj=None):
        """Create a new instance of a telescope status graph with the given configuration."""
        
        if not lconfig:
            lconfig=map(list,DEFAULTLINE[:len(statusKeys)])
        else:
            # user 'probably' passed in list of tuples, change to list of writable lists
            tmp_lconfig=map(list,lconfig[:len(statusKeys)])
            lconfig=tmp_lconfig
        config=list(gconfig)
        self.statusKeys = statusKeys
        # if formatting strings not provided, substitute just the raw number if there's one status
        # and default to formatting strings for Dome & Outside if there are 2 status keys to be graphed
        if (not statusFormats):
            if (len(statusKeys) == 1):
                statusFormats=("%d",)
            elif (len(statusKeys) ==2):
                statusFormats=("Outside: %d", "Dome: %d")
        for c in range(len(statusKeys)):
            # copy the line config formats from the status formats list
            lconfig[c][5] = statusFormats[c]
            # a lineconfig's zeroth element will be printed if there's no status data
            # so make that element the status key if there's no descriptive status format
            # but if the status format is something like "name:%format" then use the name
            index = statusFormats[c].find(':')
            if (index == -1):
                lconfig[c][0] = statusKeys[c]
            else:
                lconfig[c][0] = statusFormats[c][:index]
            #print "-=- format = ", lconfig[c][0]
        self.title = config[0] = title
        if (displayTime):
            config[4] = 0
        self.displayTime = displayTime
        if (background):
            config[2] = background
        self.background = config[2]
        self.cachedStatus = statusObj
        LineGraph.LineGraph.__init__(self, parent, size=size, gconfig=config, lconfig=lconfig,
                 pwindow=pwindow, iscale=iscale, pscales=pscales, ptickfont=ptickfont)
        self.alarmValues = alarmValues
        self.alarmState = False
        # if the change of a value from the previous iteration exceeds maxDelta,
        # force a discontinuity in the graph by replacing the current value with None
        # Used when wind direction wraps across North so I don't plot a line where it 
        # switched over the 0->360 discontinuity
        self.maxDeltas = maxDeltas
        if self.maxDeltas:
            self.previousStatusAliasValues = [None] * len(statusKeys)

    def rescale(self):
        """Update the time scale."""
        if (self.currscale == DEFAULTSSCALE) : hide = not self.displayTime
        else: hide = False
        
        self.chart.xaxis_configure(hide=hide,
                                   min=self.lastx-self.scales[self.currscale]+1,
                                   max=self.lastx, stepsize=self.scales[self.currscale]*0.4)

    def valueExceedsMax(self, valueList, maxList):
        for c in range(len(valueList)):
            if valueList[c] > maxList[c] : return True
        return False

    def checkAlarm(self, statusAliasValues):
        if not self.alarmValues : return
        alarm = self.valueExceedsMax(statusAliasValues,self.alarmValues)
        
        if (alarm and not self.alarmState):
            self.alarmState = True
            self.newbackground("#ffdddd")
        elif ((not alarm) and self.alarmState):
            self.alarmState = False
            self.newbackground(self.background)
            
    def maxDeltasExceeded(self, currentVals, prevVals, maxDeltas):
        for c in range(len(currentVals)):
            #print "cur:%r prev:%r maxD:%r" % (currentVals[c], prevVals[c], maxDeltas[c])
            try:
                if abs(currentVals[c] - prevVals[c]) > maxDeltas[c]:
                    return True
            except TypeError, e:
                #print "--> %r" % (e)
                pass
        return False
        
    def mungedStatusAliasValues(self, currentVals, prevVals, maxDeltas):
        newValues = list()
        for c in range(len(currentVals)):
            try:
                if abs(currentVals[c] - prevVals[c]) > maxDeltas[c]:
                    currentValue = None
                else:
                    currentValue = currentVals[c]
            except TypeError, e:
                #print "==>", e
                currentValue = currentVals[c]
            newValues.append(currentValue)
        return newValues
    
    def tick(self):
        try:
            statusAliasValues = map(lambda alias:self.cachedStatus[alias],self.statusKeys)
            graphedStatusAliasValues = statusAliasValues
            
            # if we're looking for discontinuities, we may need to mung the graphed values
            # & store the previous values for comparison
            if self.maxDeltas:
                if self.maxDeltasExceeded(statusAliasValues, self.previousStatusAliasValues, self.maxDeltas):
                    graphedStatusAliasValues = self.mungedStatusAliasValues(
                            statusAliasValues, self.previousStatusAliasValues, self.maxDeltas)
                self.previousStatusAliasValues = statusAliasValues
                
            self.update(time.time(),graphedStatusAliasValues)
            self.checkAlarm(statusAliasValues)
        except:
            pass
        self.after(5000, self.tick)

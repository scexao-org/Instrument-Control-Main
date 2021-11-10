#!/usr/bin/env python

from __future__ import division
import sys
import math
from PyQt4.QtGui import *
import SOSS.status as st
#import ssdlog
import time
import cPickle
import os

from timeValueGraph import *
from TVData import *

version = '20090430.0'

SG_DEFAULTSIZE = (430,102)

class StatusGraph(TimeValueGraph):
    def __init__(self, parent=None, size=SG_DEFAULTSIZE,
                 statusKeys=(), key=None, statusFormats=None,
                 warningValues=None,
                 alarmValues=None,
                 maxDeltas=None,
                 title=None, displayTime=False, backgroundColor=None,
                 logger=None):

        self.logger=logger  
  
        """Create a new instance of a telescope status graph with the given configuration."""
        
        self.statusKeys = statusKeys
        # if formatting strings not provided, substitute just the raw number if there's one status
        # and default to formatting strings for Outside & Dome if there are 2 status keys to be graphed
        if (not statusFormats):
            if (len(statusKeys) == 1):
                statusFormats=("%.1f",)
            elif (len(statusKeys) ==2):
                statusFormats=("Outside: %.1f", "Dome: %.1f")
        self.statusFormats = statusFormats

        #self.cachedStatus = statusObj
        
        TimeValueGraph.__init__(self, parent, size=size, displayTime=displayTime, key=key, title=title)

        if backgroundColor:
            self.initBackgroundColor(backgroundColor)

        self.warningValues = warningValues
        self.alarmValues = alarmValues
        self.alarmState = 0
        
        # if the change of a value from the previous iteration exceeds maxDelta,
        # force a discontinuity in the graph
        # Used when wind direction wraps across North so I don't plot a line where it 
        # switched over the 0->360 discontinuity
        self.maxDeltas = maxDeltas

        self.dataLabels = []
        # fixme: this dict should be removed here & in superclass
        self.dataLabelsToDataStores = {}
        
        for i in range(len(statusKeys)):
            dataLabel = DataLabel(self,statusFormats[i])
            self.dataLabelsToDataStores[dataLabel] = self.dataStores[i]
            self.colorDict[dataLabel] = TimeValueGraph.DATACOLORS[i]
            self.dataLabels.append(dataLabel)
            self.labelContainer.layout().addWidget(dataLabel)

    def createDatastores(self, _datastoreCount=0):
        ''' returns a list of the time-value datastores to be used for this graph; fill em with persistent data if you got it. '''
        # I'm ignoring _datastoreCount in this implementation
        if Global.persistentData and (self.key in Global.persistentData):
            dataList = Global.persistentData[self.key]
            # fixme: probably should sanity check the data; ie it's sorted and all times prior to now
            # (so it will remain sorted when I add data (clock better be sane)
            return dataList
        # return a list with a datastore for every statusKey
        return map(lambda placeholder: CTVData(), self.statusKeys)

    def fetchData(self, now, stat_vals):

        self.logger.debug('stat_vals passed <%s>' %(stat_vals))
   
        try:
            statusAliasValues=[stat_vals[sk] for sk in self.statusKeys]
            #statusAliasValues = map(lambda alias:self.cachedStatus[alias], self.statusKeys)
            self.logger.debug('key<%s> data<%s>' %(self.statusKeys, statusAliasValues))
            
            self.storeData(now, statusAliasValues)
            self.checkAlarm(statusAliasValues)
        except Exception, e:
            self.logger.error('fetchData error <%s>' %e)
            #print "fetchData raised"
            pass

    def valueExceedsMax(self, valueList, maxList):
        for c in range(len(valueList)):
            if valueList[c] > maxList[c] : return True
        return False

    def checkAlarm(self, statusAliasValues):
        if not self.alarmValues and not self.warningValues: return
        warning = alarm = False
        if self.alarmValues:
            alarm = self.valueExceedsMax(statusAliasValues,self.alarmValues)
        if self.warningValues:
            warning = self.valueExceedsMax(statusAliasValues,self.warningValues)

        if alarm:
            if not self.alarmState == 2:
                self.alarmState = 2
                self.setBackgroundColor(self.errorColor)
        elif warning:
            if not self.alarmState == 1:
                self.alarmState = 1
                self.setBackgroundColor(self.warningColor)
        elif self.alarmState != 0:
            self.alarmState = 0
            self.setBackgroundColor(self.normalColor)

    





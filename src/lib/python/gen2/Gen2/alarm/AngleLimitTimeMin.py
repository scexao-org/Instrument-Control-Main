#!/usr/bin/env python

#
# AngleLimitTimeMin.py - methods for determining which of the angular
#                        limit time status variables has the minimum
#                        value.
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Wed Jun 20 15:43:40 HST 2012
#]
#
# The AngleLimitTimeMin class implements the logic to determine which
# of the angular limit time status variables has the minimum value.
#

import remoteObjects as ro

class AngleLimitTimeMin(object):
    def __init__(self, logger = ro.nullLogger()):
        self.logger = logger
        self.statusVar = {
            'limitTimeAz':     {'ID': 'Melco_00A13D3', 'value': None},
            'limitTimeElLow':  {'ID': 'Melco_00A13D1', 'value': None},
            'limitTimeElHigh': {'ID': 'Melco_00A13D2', 'value': None},
            'limitTimeRot':    {'ID': 'Melco_00A13D4', 'value': None}
            }

        # This is a "long time", i.e., longer than any expected limit
        # time value from the TSC.
        self.longTime = 721 # minutes

        # These are the attributes that express the minimum limit time
        # and the name of the angular quantity with the minimum value.
        self.limitTimeMin = self.longTime
        self.limitTimeName = None

    def update(self, svConfig, statusFromGen2):

        # Update the TelState status variables
        telState = svConfig.configID['TelState'].importedObject
        telState.update(svConfig, statusFromGen2)

        # Update our status variables
        for key in self.statusVar:
            ID = self.statusVar[key]['ID']
            svConfigItem = svConfig.configID[ID]
            if svConfigItem.Gen2Alias in statusFromGen2:
                self.statusVar[key]['value'] = svConfigItem.MelcoValue(statusFromGen2[svConfigItem.Gen2Alias])

        # Determine which angular quantity has the minimum limit time
        self.limitTimeMin = self.longTime
        self.limitTimeName = None
        if telState.limitFlagElLow():
            if self.limitTimeElLow() < self.limitTimeMin:
                self.limitTimeMin = self.limitTimeElLow()
                self.limitTimeName = 'limitTimeElLow'
        if telState.limitFlagElHigh():
            if self.limitTimeElHigh() < self.limitTimeMin:
                self.limitTimeMin = self.limitTimeElHigh()
                self.limitTimeName = 'limitTimeElHigh'
        if telState.limitFlagAz():
            if self.limitTimeAz() < self.limitTimeMin:
                self.limitTimeMin = self.limitTimeAz()
                self.limitTimeName = 'limitTimeAz'
        if not telState.limitFlagBigRot() and telState.limitFlagRot():
            if self.limitTimeRot() < self.limitTimeMin:
                self.limitTimeMin = self.limitTimeRot()
                self.limitTimeName = 'limitTimeRot'

    def limitTimeAz(self):
        return self.statusVar['limitTimeAz']['value']
    def limitTimeElLow(self):
        return self.statusVar['limitTimeElLow']['value']
    def limitTimeElHigh(self):
        return self.statusVar['limitTimeElHigh']['value']
    def limitTimeRot(self):
        return self.statusVar['limitTimeRot']['value']

#!/usr/bin/env python

#
# AngleLimitTime.py - methods for determining if the telescope
#                     azimuth, elevation, or instrument rotator are
#                     near a limit.
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Thu Jun 21 09:47:03 HST 2012
#]
#

import re
import remoteObjects as ro
import Derived

class AngleLimitTime(Derived.Derived):

    def __init__(self, logger = ro.nullLogger()):
        super(AngleLimitTime, self).__init__(logger)

        self.statusVar = {
            'limitTimeAz':     {'ID': 'Melco_00A13D3', 'value': None},
            'limitTimeElLow':  {'ID': 'Melco_00A13D1', 'value': None},
            'limitTimeElHigh': {'ID': 'Melco_00A13D2', 'value': None},
            'limitTimeRot':    {'ID': 'Melco_00A13D4', 'value': None}
            }
        self.compositeAlarms = ('TimeLimitAz', 'TimeLimitELLow', 'TimeLimitELUp', 'TimeLimitInRImRProbe')

        # We will store DomeShutter, MirrorCover, TelState, and
        # FocalStation objects here. We need these because we want to
        # mute the alarms when the dome is closed and telescope is
        # "inactive".
        self.domeShutter = None
        self.mirrorCover = None
        self.telState = None

    def update(self, svConfig, statusFromGen2):
        super(AngleLimitTime, self).update(svConfig, statusFromGen2)

        # Get references to the DomeShutter, MirrorCover, and TelState
        # objects.
        if self.domeShutter == None:
            self.domeShutter = svConfig.configID['DomeShutter'].importedObject
        if self.mirrorCover == None:
            self.mirrorCover = svConfig.configID['MirrorCover'].importedObject
        if self.telState == None:
            self.telState = svConfig.configID['TelState'].importedObject

       # Update the dome shutter, mirror cover, and telescope state
        # status variables.
        self.domeShutter.update(svConfig, statusFromGen2)
        self.mirrorCover.update(svConfig, statusFromGen2)
        self.telState.update(svConfig, statusFromGen2)

        # Mute our alarms if the telescope is "inactive", i.e., if the
        # mirror covers are closed or the dome shutter is closed or
        # the telescope is in the stowed position. We also mute the
        # alarms if the telescope is slewing or if it is "pointing".
        if self.mirrorCover.m1Closed() or \
                self.domeShutter.shutterClosed() or \
                self.telState.elStowed() or \
                self.telState.isSlewing() or \
                self.telState.isPointing(): 
            self.setAllMuteState(True)
        else:
            self.setAllMuteState(False)

        # Update the AngleLimitTimeMin status variables so that they
        # will be available when we need them.
        self.angleLimitTimeMin = svConfig.configID['AngleLimitTimeMin'].importedObject
        self.angleLimitTimeMin.update(svConfig, statusFromGen2)

        # Set the alarms to "Ignore" that don't have a valid limit
        # flag.
        self.setIgnoreState()

    def setIgnoreState(self):
        for key in self.statusVar:
            flagName = re.sub('Time', 'Flag', key)
            ignore = not self.telState.getLimitFlag(flagName)
            ID = self.statusVar[key]['ID']
            svConfigItem = self.svConfig.configID[ID]
            if svConfigItem.Alarm:
                for severity in svConfigItem.Alarm:
                    if ignore:
                        self.svConfig.startIgnoreAlarm(ID, severity)
                    else:
                        self.svConfig.stopIgnoreAlarm(ID, severity)

    def limitThreshold(self, name, severity):
        svConfigItem = self.svConfig.configID[self.statusVar[name]['ID']]
        return svConfigItem.Alarm[severity].Threshold

    def limitTimeAlarmState(self, limitTimeName, severity):
        threshold = self.limitThreshold(limitTimeName, severity)
        if self.angleLimitTimeMin.limitTimeName == limitTimeName:
            return self.angleLimitTimeMin.limitTimeMin <= threshold
        else:
            return False

    def limitTimeAlarmHandler(self, statusVarName, compName, severity):
        alarmState = self.limitTimeAlarmState(statusVarName, severity)
        if alarmState and 'Warning' in severity:
            # For "Warning" alarms, set MinNotifyInterval so that
            # there are three announcements in the time until the
            # limit is reached
            notifyInterval = self.angleLimitTimeMin.limitTimeMin * 60 / 3
            svConfigItem = self.svConfig.configID[self.statusVar[statusVarName]['ID']]
            svConfigItem.Alarm[severity].MinNotifyInterval = notifyInterval
            svConfigItem = self.svConfig.configID[compName]
            svConfigItem.Alarm[severity].MinNotifyInterval = notifyInterval
        return alarmState
    
    def azLimitTimeWarningLo(self):
        return self.limitTimeAlarmHandler('limitTimeAz', 'TimeLimitAz', 'WarningLo')
    def azLimitTimeCriticalLo(self):
        return self.limitTimeAlarmHandler('limitTimeAz', 'TimeLimitAz', 'CriticalLo')

    def elLowLimitTimeWarningLo(self):
        return self.limitTimeAlarmHandler('limitTimeElLow', 'TimeLimitELLow', 'WarningLo')
    def elLowLimitTimeCriticalLo(self):
        return self.limitTimeAlarmHandler('limitTimeElLow', 'TimeLimitELLow', 'CriticalLo')

    def elHighLimitTimeWarningLo(self):
        return self.limitTimeAlarmHandler('limitTimeElHigh', 'TimeLimitELUp', 'WarningLo')
    def elHighLimitTimeCriticalLo(self):
        return self.limitTimeAlarmHandler('limitTimeElHigh', 'TimeLimitELUp', 'CriticalLo')

    def rotLimitTimeWarningLo(self):
        return self.limitTimeAlarmHandler('limitTimeRot', 'TimeLimitInRImRProbe', 'WarningLo')
    def rotLimitTimeCriticalLo(self):
        return self.limitTimeAlarmHandler('limitTimeRot', 'TimeLimitInRImRProbe', 'CriticalLo')

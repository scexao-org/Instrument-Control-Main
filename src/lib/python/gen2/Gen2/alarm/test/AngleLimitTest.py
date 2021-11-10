#!/usr/bin/env python

#
# AngleLimitTest.py - The AngleLimitTest class is the base class for
#                     the AzAngleLimitTest, RotAngleLimitTest, and
#                     AGProbeAngleLimitTest modules.
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Mon May  7 09:37:52 HST 2012
#]
#

import unittest
import AlarmTest
import Gen2.alarm.AngleLimitTime as AngleLimitTime

class AngleLimitTest(AlarmTest.AlarmTest):
    def setUp(self):
        super(AngleLimitTest, self).setUp()
        # We will need AngleLimitTime so create it here
        self.angleLimitTime = AngleLimitTime.AngleLimitTime()
        if hasattr(self, 'angleLimit'):
            for name in self.angleLimit.statusVar:
                if 'Cmd' in name:
                    self.cmdName = name
                else:
                    self.actName = name
                    
            self.severityList = []
            for name in self.angleLimit.compositeAlarms:
                self.compositeName = name
                ID = name
                svConfigItem = self.svConfig.configID[ID]
                for severity in svConfigItem.Alarm:
                    self.severityList.append(severity)

            self.alarmStates = {}
            for name in self.angleLimit.statusVar:
                self.alarmStates[name] = {}
                ID = self.angleLimit.statusVar[name]['ID']
                svConfigItem = self.svConfig.configID[ID]
                for severity in svConfigItem.Alarm:
                    self.alarmStates[name][severity] = False
            for name in self.angleLimit.compositeAlarms:
                self.alarmStates[name] = {}
                ID = name
                svConfigItem = self.svConfig.configID[ID]
                for severity in svConfigItem.Alarm:
                    self.alarmStates[name][severity] = False

            self.muteStates = {}
            for severity in self.severityList:
                self.muteStates[severity] = False

    def clearAlarmStates(self):
        for name in self.alarmStates:
            for severity in self.alarmStates[name]:
                self.alarmStates[name][severity] = False

    def setAlarmStates(self, severityDict):
        for name in severityDict:
            severity = severityDict[name]
            if name == 'Cmd':
                svName = self.cmdName
            elif name == 'Act':
                svName = self.actName
            if 'Ok' not in severity:
                self.alarmStates[svName][severity] = True
                self.alarmStates[self.compositeName][severity] = True
            if 'Critical' in severity:
                warn_severity = severity.replace('Critical', 'Warning')
                self.alarmStates[svName][warn_severity] = True
                self.alarmStates[self.compositeName][warn_severity] = True

    def getAngle(self, name, severity):
        if 'Ok' in severity:
            return 0
        else:
            # Return an angle that is just past the threshold
            svConfigItem = self.svConfig.configID[self.getID(name)]
            return svConfigItem.Alarm[severity].Threshold * 1.02

    def getLimitTime(self):
        # Return a "time to limit" that is less than the threshold
        ID = self.angleLimitTime.statusVar['limitTimeAz']['ID']
        svConfigItem = self.svConfig.configID[ID]
        return svConfigItem.Alarm['WarningLo'].Threshold * 0.5

    def getID(self, name):
        # Return the status variable ID
        return self.angleLimit.statusVar[name]['ID']

    def setAngle(self, name, angle):
        # Set the Gen2 status alias for the azimuth command or actual
        # angle to the specified value
        Gen2Alias = self.svConfig.configID[self.getID(name)].Gen2Alias
        self.statusFromGen2[Gen2Alias] = angle

    def setMuteStates(self, severity, state):
        for s in self.muteStates:
            if severity in s:
                self.muteStates[s] = state

    def checkSVItemAlarmState(self, name, ID):
        svConfigItem = self.svConfig.configID[ID]
        if svConfigItem.Alarm:
            for severity in svConfigItem.Alarm:
                if 'OK' not in severity:
                    if svConfigItem.importedObject:
                    
                        alarmState = self.alarmFuncs[name][severity]()
                    else:
                        alarmState = svConfigItem.isAlarm(severity, self.angleLimit.statusVar[name]['value'])
                        if self.alarmStates[name][severity]:
                            self.assertTrue(alarmState)
                        else:
                            self.assertFalse(alarmState)

    def checkAlarmStates(self):
        for name in self.angleLimit.statusVar:
            self.checkSVItemAlarmState(name, self.getID(name))
        for name in self.angleLimit.compositeAlarms:
            self.checkSVItemAlarmState(name, name)

    def checkMuteStates(self, allMuteOn):
        for severity in self.severityList:
            for alarmName in self.angleLimit.compositeAlarms:
                ID = alarmName
                if allMuteOn:
                    self.assertTrue(self.svConfig.getMuteOnState(severity, ID))
                else:
                    if self.muteStates[severity]:
                        self.assertTrue(self.svConfig.getMuteOnState(severity, ID))
                    else:
                        self.assertFalse(self.svConfig.getMuteOnState(severity, ID))

    def checkAngleLimit(self, severity):
        self.setOpState(True)
        self.setTelLimitFlag(azValid = True)
        self.setTelDrive('Tracking')
        if severity['Cmd'] == 'Ok' and severity['Act'] == 'Ok':
            self.setAngleLimitTime(shortTime = False)
        else:
            self.setAngleLimitTime(shortTime = True)
        self.setAngle(self.cmdName, self.getAngle(self.cmdName, severity['Cmd']))
        self.setAngle(self.actName, self.getAngle(self.actName, severity['Act']))
        self.angleLimit.update(self.svConfig, self.statusFromGen2)
        self.checkAlarmStates()

    def checkMuteWarningsBigLimitTime(self, severity):
        # Set "time to limit" to a large number and check to see that
        # Warning alarms are muted.
        self.setOpState(True)
        self.setTelLimitFlag(azValid = True)
        self.setTelDrive('Tracking')
        # This sets the "time to limit" to a large number, i.e.,
        # greater than the threshold.
        self.setAngleLimitTime(shortTime = False)
        self.setAngle(self.cmdName, self.getAngle(self.cmdName, severity['Cmd']))
        self.setAngle(self.actName, self.getAngle(self.actName, severity['Act']))
        self.angleLimit.update(self.svConfig, self.statusFromGen2)
        # The Warning alarms should be muted because the "time to
        # limit" is large.
        self.setMuteStates('Warning', True)
        self.checkMuteStates(False)

    def checkMuteWarningsNoLimitFlag(self, severity):
        # Set all "time to limit" flags to 0 and check to see that
        # Warning alarms are muted.
        self.setOpState(True)
        self.setTelLimitFlag()
        self.setTelDrive('Tracking')
        self.setAngle(self.cmdName, self.getAngle(self.cmdName, severity['Cmd']))
        self.setAngle(self.actName, self.getAngle(self.actName, severity['Act']))
        self.angleLimit.update(self.svConfig, self.statusFromGen2)
        # The Warning alarms should be muted because all the "time to
        # limit" flags are 0.
        self.setMuteStates('Warning', True)
        self.checkMuteStates(False)

    def checkMuteDomeClosed(self, severity):
        # Set dome to closed and make sure all alarms are muted
        self.setDomeShutter(False, False)
        self.setMirrorCover(False)
        self.setTelStowed(False)
        self.setTelLimitFlag(azValid = True)
        self.setTelDrive('Tracking')
        self.setAngle(self.cmdName, self.getAngle(self.cmdName, severity['Cmd']))
        self.setAngle(self.actName, self.getAngle(self.actName, severity['Act']))
        self.angleLimit.update(self.svConfig, self.statusFromGen2)
        self.checkAlarmStates()
        # checkMuteStates(True) says that *all* alarms should indicate
        # that they are muted.
        self.checkMuteStates(True)

    def checkMuteMirrorClosed(self, severity):
        # Set mirror covers to closed and make sure all alarms are muted
        self.setDomeShutter(True, True)
        self.setMirrorCover(True)
        self.setTelStowed(False)
        self.setTelLimitFlag(azValid = True)
        self.setTelDrive('Tracking')
        self.setAngle(self.cmdName, self.getAngle(self.cmdName, severity['Cmd']))
        self.setAngle(self.actName, self.getAngle(self.actName, severity['Act']))
        self.angleLimit.update(self.svConfig, self.statusFromGen2)
        self.checkAlarmStates()
        # checkMuteStates(True) says that *all* alarms should indicate
        # that they are muted.
        self.checkMuteStates(True)

    def checkMuteTelStowed(self, severity):
        # Set telescope position to stowed and make sure all alarms
        # are muted
        self.setDomeShutter(True, True)
        self.setMirrorCover(False)
        self.setTelStowed(True)
        self.setTelLimitFlag(azValid = True)
        self.setTelDrive('Tracking')
        self.setAngle(self.cmdName, self.getAngle(self.cmdName, severity['Cmd']))
        self.setAngle(self.actName, self.getAngle(self.actName, severity['Act']))
        self.angleLimit.update(self.svConfig, self.statusFromGen2)
        self.checkAlarmStates()
        # checkMuteStates(True) says that *all* alarms should indicate
        # that they are muted.
        self.checkMuteStates(True)

    def checkMuteOpState(self, severity):
        # Set dome, mirror covers, and telescope position to
        # non-operational and make sure all alarms are muted.
        self.setOpState(False)
        self.setTelLimitFlag(azValid = True)
        self.setTelDrive('Tracking')
        self.setAngle(self.cmdName, self.getAngle(self.cmdName, severity['Cmd']))
        self.setAngle(self.actName, self.getAngle(self.actName, severity['Act']))
        self.angleLimit.update(self.svConfig, self.statusFromGen2)
        self.checkAlarmStates()
        # checkMuteStates(True) says that *all* alarms should indicate
        # that they are muted.
        self.checkMuteStates(True)

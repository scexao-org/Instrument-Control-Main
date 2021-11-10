#!/usr/bin/env python

#
# AngleLimitTimeTest.py - Test the AngleLimitTime class to make sure it:
#                           - accurately reports alarm states
#                           - ignores alarm warnings when dome is closed
#                             or telescope is slewing or pointing
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Wed Apr 25 15:13:54 HST 2012
#]
#

import unittest
import AlarmTest
import Gen2.alarm.AngleLimitTime as AngleLimitTime
import Gen2.alarm.AngleLimitTimeMin as AngleLimitTimeMin

class AngleLimitTimeTest(AlarmTest.AlarmTest):
    def setUp(self):
        # We will need an AngleLimitTime object, so create one here
        self.angleLimitTime = AngleLimitTime.AngleLimitTime()
        # Also, AngleLimitTimeMin
        self.angleLimitTimeMin = AngleLimitTimeMin.AngleLimitTimeMin()
        # Now, call our parent's setUp method.
        super(AngleLimitTimeTest, self).setUp()
        self.alarmStates =  {
            'limitTimeAz':
                {
                'WarningLo':  False,
                'CriticalLo': False,
                },
            'limitTimeElLow':
                {
                'WarningLo':  False,
                'CriticalLo': False,
                },
            'limitTimeElHigh':
                {
                'WarningLo':  False,
                'CriticalLo': False,
                },
            'limitTimeRot':
                {
                'WarningLo':  False,
                'CriticalLo': False,
                }
            }

        self.alarmFuncs = {
            'limitTimeAz':     {'WarningLo':  self.angleLimitTime.azLimitTimeWarningLo, 'CriticalLo': self.angleLimitTime.azLimitTimeCriticalLo},
            'limitTimeElLow':  {'WarningLo':  self.angleLimitTime.elLowLimitTimeWarningLo, 'CriticalLo': self.angleLimitTime.elLowLimitTimeCriticalLo},
            'limitTimeElHigh': {'WarningLo':  self.angleLimitTime.elHighLimitTimeWarningLo, 'CriticalLo': self.angleLimitTime.elHighLimitTimeCriticalLo},
            'limitTimeRot':    {'WarningLo':  self.angleLimitTime.rotLimitTimeWarningLo, 'CriticalLo': self.angleLimitTime.rotLimitTimeCriticalLo},
            }

    def getID(self, name):
        # Return the status variable ID
        return self.angleLimitTimeMin.statusVar[name]['ID']

    def setLimitTime(self, name, severity):
        svConfigItem = self.svConfig.configID[self.getID(name)]
        if 'Ok' in severity:
            value = svConfigItem.Alarm['WarningLo'].Threshold * 1.02
        else:
            value = svConfigItem.Alarm[severity].Threshold * 0.5
        Gen2Alias = self.svConfig.configID[self.getID(name)].Gen2Alias
        self.statusFromGen2[Gen2Alias] = value

    def checkAlarmStates(self):
        for t in self.alarmFuncs:
            for severity in self.alarmFuncs[t]:
#                print t,severity,self.alarmStates[t][severity],self.alarmFuncs[t][severity]()
                if self.alarmStates[t][severity]:
                    self.assertTrue(self.alarmFuncs[t][severity]())
                else:
                    self.assertFalse(self.alarmFuncs[t][severity]())

    def setAndUpdate(self, name, severity, elLowValid = None, elHighValid = None, azValid = None, rotValid = None, bigRotValid = None):
        self.setTelLimitFlag(elLowValid, elHighValid, azValid, rotValid, bigRotValid)
        self.setLimitTime(name, severity)
        self.angleLimitTimeMin.update(self.svConfig, self.statusFromGen2)
        self.angleLimitTime.update(self.svConfig, self.statusFromGen2)
        if 'Critical' in severity:
            self.alarmStates[name]['WarningLo'] = True
        if 'Ok' in severity:
            self.alarmStates[name][severity] = False
        else:
            self.alarmStates[name][severity] = True

    def checkLimitTime(self, name, severity, elLowValid = None, elHighValid = None, azValid = None, rotValid = None, bigRotValid = None):
        self.setOpState(True)
        self.setTelDrive('Tracking')
        self.setAndUpdate(name, severity, elLowValid, elHighValid, azValid, rotValid, bigRotValid)
        self.checkAlarmStates()
        self.checkMuteStates(False)

    def checkMuteStates(self, muteOn):
        for name in self.angleLimitTime.compositeAlarms:
            ID = name
            svConfigItem = self.svConfig.configID[ID]
            if svConfigItem.Alarm:
                for severity in svConfigItem.Alarm:
                    muteOnState = self.svConfig.getMuteOnState(severity, ID)
                    if muteOn:
                        self.assertTrue(muteOnState)
                    else:
                        self.assertFalse(muteOnState)

    def checkMuteDomeClosed(self, name, severity, elLowValid = None, elHighValid = None, azValid = None, rotValid = None, bigRotValid = None):
        # Set dome to closed and make sure all alarms are muted
        self.setDomeShutter(False, False)
        self.setMirrorCover(False)
        self.setTelStowed(False)
        self.setTelDrive('Tracking')
        self.setAndUpdate(name, severity, elLowValid, elHighValid, azValid, rotValid, bigRotValid)
        self.checkAlarmStates()
        self.checkMuteStates(True)

    def checkMuteMirrorClosed(self, name, severity, elLowValid = None, elHighValid = None, azValid = None, rotValid = None, bigRotValid = None):
        # Set dome to closed and make sure all alarms are muted
        self.setDomeShutter(True, True)
        self.setMirrorCover(True)
        self.setTelStowed(False)
        self.setTelDrive('Tracking')
        self.setAndUpdate(name, severity, elLowValid, elHighValid, azValid, rotValid, bigRotValid)
        self.checkAlarmStates()
        self.checkMuteStates(True)

    def checkMuteTelStowed(self, name, severity, elLowValid = None, elHighValid = None, azValid = None, rotValid = None, bigRotValid = None):
        # Set dome to closed and make sure all alarms are muted
        self.setDomeShutter(True, True)
        self.setMirrorCover(False)
        self.setTelStowed(True)
        self.setTelDrive('Tracking')
        self.setAndUpdate(name, severity, elLowValid, elHighValid, azValid, rotValid, bigRotValid)
        self.checkAlarmStates()
        self.checkMuteStates(True)

    def checkMuteOpState(self, name, severity, elLowValid = None, elHighValid = None, azValid = None, rotValid = None, bigRotValid = None):
        # Set dome to closed and make sure all alarms are muted
        self.setOpState(False)
        self.setTelDrive('Tracking')
        self.setAndUpdate(name, severity, elLowValid, elHighValid, azValid, rotValid, bigRotValid)
        self.checkAlarmStates()
        self.checkMuteStates(True)

    def checkMuteTelDrive(self, name, severity, telDrive, elLowValid = None, elHighValid = None, azValid = None, rotValid = None, bigRotValid = None):
        # Set dome to closed and make sure all alarms are muted
        self.setOpState(True)
        self.setTelDrive(telDrive)
        self.setAndUpdate(name, severity, elLowValid, elHighValid, azValid, rotValid, bigRotValid)
        self.checkAlarmStates()
        self.checkMuteStates(True)

    def testAngleLimitTimeAllOk(self):
        self.checkLimitTime('limitTimeAz', 'Ok', azValid = True)

    def testAzLimitTimeWarningLo(self):
        self.checkLimitTime('limitTimeAz', 'WarningLo', azValid = True)

    def testAzLimitTimeCriticalLo(self):
        self.checkLimitTime('limitTimeAz', 'CriticalLo', azValid = True)

    def testElLowLimitTimeWarningLo(self):
        self.checkLimitTime('limitTimeElLow', 'WarningLo', elLowValid = True)

    def testElLowLimitTimeCriticalLo(self):
        self.checkLimitTime('limitTimeElLow', 'CriticalLo', elLowValid = True)

    def testElHighLimitTimeWarningLo(self):
        self.checkLimitTime('limitTimeElHigh', 'WarningLo', elHighValid = True)

    def testElHighLimitTimeCriticalLo(self):
        self.checkLimitTime('limitTimeElHigh', 'CriticalLo', elHighValid = True)

    def testRotLimitTimeWarningLo(self):
        self.checkLimitTime('limitTimeRot', 'WarningLo', rotValid = True)

    def testRotLimitTimeCriticalLo(self):
        self.checkLimitTime('limitTimeRot', 'CriticalLo', rotValid = True)

    def testAzLimitTimeMuteDomeClosedCriticalLo(self):
        self.checkMuteDomeClosed('limitTimeAz', 'CriticalLo', azValid = True)

    def testAzLimitTimeMuteMirrorClosedCriticalLo(self):
        self.checkMuteMirrorClosed('limitTimeAz', 'CriticalLo', azValid = True)

    def testAzLimitTimeMuteTelStowedCriticalLo(self):
        self.checkMuteTelStowed('limitTimeAz', 'CriticalLo', azValid = True)

    def testAzLimitTimeMuteOpStateCriticalLo(self):
        self.checkMuteOpState('limitTimeAz', 'CriticalLo', azValid = True)

    def testAzLimitTimeMuteTelDriveCriticalLo(self):
        self.checkMuteTelDrive('limitTimeAz', 'CriticalLo', 'Slewing', azValid = True)

    def testAzLimitTimeMuteTelDriveCriticalLo(self):
        self.checkMuteTelDrive('limitTimeAz', 'CriticalLo', 'Pointing', azValid = True)

if __name__ == '__main__':
    unittest.main()

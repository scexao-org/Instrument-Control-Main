#!/usr/bin/env python

#
# WindscreenTest.py - Test the Windscreen class to make sure it:
#                       - accurately reports alarm states
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Fri May  4 11:50:58 HST 2012
#]
#

import unittest
import AlarmTest
import Gen2.alarm.Windscreen as Windscreen

class WindscreenTest(AlarmTest.AlarmTest):
    def setUp(self):
        super(WindscreenTest, self).setUp()
        # We will need a Windscreen object, so create one here
        self.windscreen = Windscreen.Windscreen()
        self.alarmFuncs = {
            'driveOffAndPosHigh': {'Critical':  self.windscreen.driveOffAndPosHigh},
            'modeFreeAndDriveOn': {'Critical':  self.windscreen.modeFreeAndDriveOn},
            'obstructWarn':       {'Warning':  self.windscreen.obstructWarn, 'Critical':  self.windscreen.obstructCrit}
            }

    def getID(self, name):
        # Return the status variable ID
        return self.windscreen.statusVar[name]['ID']

    def setDrive(self, driveOn):
        Gen2Alias = self.svConfig.configID[self.getID('driveOn')].Gen2Alias
        if driveOn:
            self.statusFromGen2[Gen2Alias] = 0x04
        else:
            self.statusFromGen2[Gen2Alias] = 0x08

    def setPositionValue(self, name, value):
        Gen2Alias = self.svConfig.configID[self.getID(name)].Gen2Alias
        self.statusFromGen2[Gen2Alias] = value

    def setPosition(self, position):
        if 'Low' in position:
            self.setPositionValue('realPos', 0)
        elif 'High' in position:
            self.setPositionValue('realPos', self.windscreen.highPosThreshold * 1.02)

    def setPositionOffset(self, severity):
        if 'Ok' in severity:
            self.setPositionValue('cmdPos', 0)
            self.setPositionValue('realPos', 0)
        elif 'Warning' in severity:
            self.setPositionValue('cmdPos', self.windscreen.obstructThreshold * 1.02)
            self.setPositionValue('realPos', 0)
        elif 'Critical' in severity:
            self.setPositionValue('cmdPos', -self.windscreen.obstructThreshold * 1.02)
            self.setPositionValue('realPos', 0)

    def setSyncMode(self, syncMode):
        Gen2Alias = self.svConfig.configID[self.getID('syncMode')].Gen2Alias
        if syncMode:
            self.statusFromGen2[Gen2Alias] = 0x01
        else:
            self.statusFromGen2[Gen2Alias] = 0x02

    def checkMuteStates(self, allMuteOn):
        for alarmName in self.windscreen.compositeAlarms:
            ID = alarmName
            svConfigItem = self.svConfig.configID[alarmName]
            if svConfigItem.Alarm:
                for severity in svConfigItem.Alarm:
                    if allMuteOn:
                        self.assertTrue(self.svConfig.getMuteOnState(severity, ID))
                    else:
                        self.assertFalse(self.svConfig.getMuteOnState(severity, ID))

    def testWindscreenAllOk(self):
        self.setOpState(True)
        self.setTelDrive('Tracking')
        self.setDrive(False)
        self.setPosition('Low')
        self.setPositionOffset('Ok')
        self.setSyncMode(True)
        self.windscreen.update(self.svConfig, self.statusFromGen2)
        self.assertFalse(self.alarmFuncs['driveOffAndPosHigh']['Critical']())
        self.checkMuteStates(False)

    def testDriveOffAndPosHigh(self):
        self.setOpState(True)
        self.setTelDrive('Tracking')
        self.setDrive(False)
        self.setPosition('Low')
        self.windscreen.update(self.svConfig, self.statusFromGen2)
        self.assertFalse(self.alarmFuncs['driveOffAndPosHigh']['Critical']())
        self.checkMuteStates(False)

        self.setDrive(True)
        self.setPosition('High')
        self.windscreen.update(self.svConfig, self.statusFromGen2)
        self.assertFalse(self.alarmFuncs['driveOffAndPosHigh']['Critical']())
        self.checkMuteStates(False)

        self.setDrive(True)
        self.setPosition('Low')
        self.windscreen.update(self.svConfig, self.statusFromGen2)
        self.assertFalse(self.alarmFuncs['driveOffAndPosHigh']['Critical']())
        self.checkMuteStates(False)

        self.setDrive(False)
        self.setPosition('High')
        self.windscreen.update(self.svConfig, self.statusFromGen2)
        self.assertTrue(self.alarmFuncs['driveOffAndPosHigh']['Critical']())
        self.checkMuteStates(False)

    def testModeFreeAndDriveOn(self):
        self.setOpState(True)
        self.setTelDrive('Tracking')
        self.setSyncMode(True)
        self.setDrive(True)
        self.windscreen.update(self.svConfig, self.statusFromGen2)
        self.assertFalse(self.alarmFuncs['modeFreeAndDriveOn']['Critical']())
        self.checkMuteStates(False)

        self.setSyncMode(False)
        self.setDrive(False)
        self.windscreen.update(self.svConfig, self.statusFromGen2)
        self.assertFalse(self.alarmFuncs['modeFreeAndDriveOn']['Critical']())
        self.checkMuteStates(False)

        self.setSyncMode(True)
        self.setDrive(False)
        self.windscreen.update(self.svConfig, self.statusFromGen2)
        self.assertFalse(self.alarmFuncs['modeFreeAndDriveOn']['Critical']())
        self.checkMuteStates(False)

        self.setSyncMode(False)
        self.setDrive(True)
        self.windscreen.update(self.svConfig, self.statusFromGen2)
        self.assertTrue(self.alarmFuncs['modeFreeAndDriveOn']['Critical']())
        self.checkMuteStates(False)

    def testObstructWarn(self):
        self.setOpState(True)
        self.setTelDrive('Tracking')
        self.setDrive(True)
        self.setSyncMode(True)
        self.setPositionOffset('Ok')
        self.windscreen.update(self.svConfig, self.statusFromGen2)
        self.assertFalse(self.alarmFuncs['obstructWarn']['Warning']())
        self.assertFalse(self.alarmFuncs['obstructWarn']['Critical']())
        self.checkMuteStates(False)

        self.setDrive(False)
        self.setSyncMode(False)
        self.setPositionOffset('Warning')
        self.windscreen.update(self.svConfig, self.statusFromGen2)
        self.assertFalse(self.alarmFuncs['obstructWarn']['Warning']())
        self.assertFalse(self.alarmFuncs['obstructWarn']['Critical']())
        self.checkMuteStates(False)

        self.setDrive(False)
        self.setSyncMode(False)
        self.setPositionOffset('Critical')
        self.windscreen.update(self.svConfig, self.statusFromGen2)
        self.assertFalse(self.alarmFuncs['obstructWarn']['Warning']())
        self.assertFalse(self.alarmFuncs['obstructWarn']['Critical']())
        self.checkMuteStates(False)

        self.setDrive(True)
        self.setSyncMode(True)
        self.setPositionOffset('Warning')
        self.windscreen.update(self.svConfig, self.statusFromGen2)
        self.assertTrue(self.alarmFuncs['obstructWarn']['Warning']())
        self.setPositionOffset('Critical')
        self.windscreen.update(self.svConfig, self.statusFromGen2)
        self.assertTrue(self.alarmFuncs['obstructWarn']['Critical']())
        self.checkMuteStates(False)

    def testWindscreenMuteDomeClosed(self):
        self.setDomeShutter(False, False)
        self.setMirrorCover(False)
        self.setTelStowed(False)
        self.setTelDrive('Pointing')
        self.setDrive(False)
        self.setPosition('High')
        self.windscreen.update(self.svConfig, self.statusFromGen2)
        self.assertTrue(self.alarmFuncs['driveOffAndPosHigh']['Critical']())
        self.checkMuteStates(True)

    def testWindscreenMuteMirrorClosed(self):
        self.setDomeShutter(True, True)
        self.setMirrorCover(True)
        self.setTelStowed(False)
        self.setTelDrive('Pointing')
        self.setDrive(False)
        self.setPosition('High')
        self.windscreen.update(self.svConfig, self.statusFromGen2)
        self.assertTrue(self.alarmFuncs['driveOffAndPosHigh']['Critical']())
        self.checkMuteStates(True)

    def testWindscreenMuteTelStowed(self):
        self.setDomeShutter(True, True)
        self.setMirrorCover(False)
        self.setTelStowed(True)
        self.setTelDrive('Pointing')
        self.setDrive(False)
        self.setPosition('High')
        self.windscreen.update(self.svConfig, self.statusFromGen2)
        self.assertTrue(self.alarmFuncs['driveOffAndPosHigh']['Critical']())
        self.checkMuteStates(True)

    def testWindscreenMuteTelSlewing(self):
        self.setDomeShutter(True, True)
        self.setMirrorCover(False)
        self.setTelStowed(False)
        self.setTelDrive('Slewing')
        self.setDrive(False)
        self.setPosition('High')
        self.windscreen.update(self.svConfig, self.statusFromGen2)
        self.assertTrue(self.alarmFuncs['driveOffAndPosHigh']['Critical']())
        self.checkMuteStates(True)

    def testWindscreenMuteOpState(self):
        self.setOpState(False)
        self.setTelDrive('Tracking')
        self.setDrive(False)
        self.setPosition('High')
        self.windscreen.update(self.svConfig, self.statusFromGen2)
        self.assertTrue(self.alarmFuncs['driveOffAndPosHigh']['Critical']())
        self.checkMuteStates(True)

    def driveOffPosHighTest(self):
        self.setOpState(True)
        self.setTelDrive('Tracking')
        self.setDrive(False)
        self.setPosition('High')
        self.windscreen.update(self.svConfig, self.statusFromGen2)

    def modeFreeAndDriveOnTest(self):
        self.setOpState(True)
        self.setTelDrive('Tracking')
        self.setSyncMode(False)
        self.setDrive(True)
        self.windscreen.update(self.svConfig, self.statusFromGen2)

    def obstructWarnTest(self):
        self.setOpState(True)
        self.setTelDrive('Tracking')
        self.setDrive(True)
        self.setSyncMode(True)
        self.setPositionOffset('Warning')
        self.windscreen.update(self.svConfig, self.statusFromGen2)
       
    def obstructCritTest(self):
        self.setOpState(True)
        self.setTelDrive('Tracking')
        self.setDrive(True)
        self.setSyncMode(True)
        self.setPositionOffset('Critical')
        self.windscreen.update(self.svConfig, self.statusFromGen2)

if __name__ == '__main__':
    unittest.main()

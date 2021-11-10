#!/usr/bin/env python

# TipTiltTest.py - Test the TipTilt class to make sure it:
#                    - accurately reports alarm states
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Wed Apr 25 16:14:09 HST 2012
#]
#

import unittest
import AlarmTest
import FocusInfo
import Gen2.alarm.FocalStation as FocalStation
import Gen2.alarm.TipTilt as TipTilt

class TipTiltTest(AlarmTest.AlarmTest):
    def setUp(self):
        super(TipTiltTest, self).setUp()
        # We will need a TipTilt object, so create one here
        self.tiptilt = TipTilt.TipTilt()
        # Will also need a FocusInfo object.
        self.focusInfo = FocusInfo.FocusInfo()
        self.alarmFuncs = {
            'warnTipTiltDriveOff': {'Warning':  self.tiptilt.warnTipTiltDriveOff}
            }

    def getID(self, name):
        # Return the status variable ID
        return self.tiptilt.statusVar[name]['ID']

    def setDrive(self, driveOn):
        Gen2Alias = self.svConfig.configID[self.getID('tipTiltDriveOn')].Gen2Alias
        if driveOn:
            self.statusFromGen2[Gen2Alias] = 0x01
        else:
            self.statusFromGen2[Gen2Alias] = 0x02

    def setTipTiltMode(self, mode):
        Gen2Alias = self.svConfig.configID[self.getID('tipTiltChopping')].Gen2Alias
        if 'Chopping' in mode:
            self.statusFromGen2[Gen2Alias] = 0x01
        elif 'TipTilt' in mode:
            self.statusFromGen2[Gen2Alias] = 0x02
        elif 'Position' in mode:
            self.statusFromGen2[Gen2Alias] = 0x04
        elif 'MAINT' in mode:
            self.statusFromGen2[Gen2Alias] = 0x80

    def setChopStatus(self, status):
        Gen2Alias = self.svConfig.configID[self.getID('choppingStart')].Gen2Alias
        if 'StartRdy' in status:
            self.statusFromGen2[Gen2Alias] = 0x04
        elif 'Start' in status:
            self.statusFromGen2[Gen2Alias] = 0x01
        elif 'Stop' in status:
            self.statusFromGen2[Gen2Alias] = 0x02

    def setDataAvailable(self, state):
        Gen2Alias = self.svConfig.configID[self.getID('tipTiltDataAvailable')].Gen2Alias
        if state:
            self.statusFromGen2[Gen2Alias] = 0x01
        else:
            self.statusFromGen2[Gen2Alias] = 0x00

    def testWarnTipTiltDriveOff(self):
        # The "warn tip-tilt drive off" alarm depends on the focus
        # settings, so iterate through all of them.
        for f in self.focusInfo.focusInfoIterator():
            self.setFocStation(f)
            # Iterate through all of the modes and statuses
            for mode in ('Chopping', 'TipTilt', 'Position', 'MAINT'):
                for status in ('StartRdy', 'Start', 'Stop'):
                    if 'MAINT' in mode:
                        # Iterate through the "drive" states. The
                        # Tip-Tilt alarm should always be "off" here
                        # since the tip-tilt mode is 'MAINT'.
                        for drive in (True, False):
                            self.setDrive(drive)
                            self.setTipTiltMode(mode)
                            self.setChopStatus(status)
                            self.tiptilt.update(self.svConfig, self.statusFromGen2)
                            self.assertFalse(self.alarmFuncs['warnTipTiltDriveOff']['Warning']())
                    else:
                        # The Tip-Tilt alarm is only active when M2 is "IR"
                        if f['M2'] == 'IR':
                            # First, turn on the drive and set the mode to
                            # Chopping and status to Start so that the
                            # Tip-Tilt state will be "True". The alarm should
                            # be "off" at this point.
                            self.setDrive(True)
                            self.setTipTiltMode(mode)
                            self.setChopStatus(status)
                            self.setDataAvailable(True)
                            self.tiptilt.update(self.svConfig, self.statusFromGen2)
                            self.assertFalse(self.alarmFuncs['warnTipTiltDriveOff']['Warning']())
                            # Now, turn off the drive. Since we
                            # transitioned from "drive on" to "drive
                            # off", the alarm should now be "on".
                            self.setDrive(False)
                            self.tiptilt.update(self.svConfig, self.statusFromGen2)
                            self.assertTrue(self.alarmFuncs['warnTipTiltDriveOff']['Warning']())
                            # If we do another update, the alarm should still
                            # be "on"
                            self.tiptilt.update(self.svConfig, self.statusFromGen2)
                            self.assertTrue(self.alarmFuncs['warnTipTiltDriveOff']['Warning']())
                            # If we turn the drive back on, the alarm should
                            # change to "off"
                            self.setDrive(True)
                            self.tiptilt.update(self.svConfig, self.statusFromGen2)
                            self.assertFalse(self.alarmFuncs['warnTipTiltDriveOff']['Warning']())
                        else:
                            # Iterate through the "drive" states. The
                            # Tip-Tilt alarm should always be "off"
                            # here since M2 is not "IR"
                            for drive in (True, False):
                                self.setDrive(drive)
                                self.setTipTiltMode(mode)
                                self.setChopStatus(status)
                                self.setDataAvailable(True)
                                self.tiptilt.update(self.svConfig, self.statusFromGen2)
                                self.assertFalse(self.alarmFuncs['warnTipTiltDriveOff']['Warning']())

    def warnTipTiltDriveOffTest(self):
        for f in self.focusInfo.focusInfoIterator():
            self.focalStationName = f['FOCAL_STATION']
            self.setFocStation(f)
            focalStation = FocalStation.FocalStation()
            focalStation.update(self.svConfig, self.statusFromGen2)
            if focalStation.m2IsIR():
                self.setTipTiltMode('Chopping')
                self.setChopStatus('Start')
                self.setDataAvailable(True)
                self.setDrive(False)
                self.tiptilt.update(self.svConfig, self.statusFromGen2)
                break

    def warnTipTiltDriveOffAllOkTest(self):
        self.setDrive(True)
        self.setTipTiltMode('Chopping')
        self.setChopStatus('Start')
        self.setDataAvailable(True)
        self.tiptilt.update(self.svConfig, self.statusFromGen2)

if __name__ == '__main__':
    unittest.main()

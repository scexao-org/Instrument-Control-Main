#!/usr/bin/env python

#
# PACmdTest.py - Test the PACmd class to make sure it:
#                  - accurately reports alarm states
#                  - ignores alarm warnings when dome is
#                    closed or telescope is slewing
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Wed Apr 25 15:18:43 HST 2012
#]
#

import unittest
import time
import AlarmTest
import ADCFreeTest
import FocusInfo
import Gen2.alarm.PACmd as PACmd
import Gen2.alarm.FocalStation as FocalStation

class PACmdTest(AlarmTest.AlarmTest):
    def setUp(self):
        super(PACmdTest, self).setUp()
        # Will also need a FocusInfo object.
        self.focusInfo = FocusInfo.FocusInfo()

    def getAngle(self):
        # Return an angle that is just past the threshold
        return self.pacmd.errorThreshold * 1.02

    def getID(self, name):
        # Return the status variable ID
        return self.pacmd.statusVar[name]['ID']

    def setAngles(self, angles):
        for name in angles:
            self.setAngle(name, angles[name])

    def setAngle(self, name, angle):
        # Set the Gen2 status alias for the PA command or actual
        # angle to the specified value
        Gen2Alias = self.svConfig.configID[self.getID(name)].Gen2Alias
        self.statusFromGen2[Gen2Alias] = angle
        Gen2Alias = self.Gen2Alias[name]
        self.statusFromGen2[Gen2Alias] = angle

    def checkPACmd(self, f):
        self.setAngles({'rot': 0, 'rotCmd': self.getAngle()})
        self.setFocStation(f)
        self.pacmd.update(self.svConfig, self.statusFromGen2)
        if self.pacmd.focalStation.rotIsOut():
            self.checkIgnoreFocalStation(True)
        else:
            self.assertFalse(self.alarmFuncs['paCmdWarning']['Warning']())
            self.assertTrue(self.pacmd.paCmdStartTime > 0)
            now = time.time()
            self.pacmd.paCmdStartTime = now - self.pacmd.paStartupInterval * 1.02
            self.assertTrue(self.alarmFuncs['paCmdWarning']['Warning']())
            self.checkIgnoreFocalStation(False)
        self.setAngles({'rot': 0, 'rotCmd': 0})
        self.pacmd.update(self.svConfig, self.statusFromGen2)

    def checkIgnoreFocalStation(self, ignore):
        for name in self.pacmd.compositeAlarms:
            ID = name
            svConfigItem = self.svConfig.configID[ID]
            if svConfigItem.Alarm:
                for severity in svConfigItem.Alarm:
                    if ignore:
                        self.assertTrue(svConfigItem.Alarm[severity].Ignore)
                    else:
                        self.assertFalse(svConfigItem.Alarm[severity].Ignore)

    def checkIgnoreAllFocalStations(self, ignore, focalStation=''):
        for f in self.focusInfo.focusInfoIterator(focalStation):
            self.setAngles({'rot': 0, 'rotCmd': self.getAngle()})
            self.setFocStation(f)
            self.pacmd.update(self.svConfig, self.statusFromGen2)
            now = time.time()
            self.pacmd.paCmdStartTime = now - self.pacmd.paStartupInterval * 1.02
            self.checkIgnoreFocalStation(ignore)
            self.setAngles({'rot': 0, 'rotCmd': 0})
            self.pacmd.update(self.svConfig, self.statusFromGen2)

    def checkIgnoreOpState(self, focalStation):
        # Set dome, mirror covers, and telescope position to
        # non-operational and make sure all alarms are ignored.
        self.setOpState(False)
        self.setTelDrive('Tracking')
        self.checkIgnoreAllFocalStations(True, focalStation)

    def checkIgnoreSlewing(self, focalStation):
        self.setOpState(True)
        self.setTelDrive('Slewing')
        self.checkIgnoreAllFocalStations(True, focalStation)

    def paCmdTest(self, focalStation = None):
        self.setOpState(True)
        self.setTelDrive('Tracking')
        for f in self.focusInfo.focusInfoIterator(focalStation):
            self.setFocStation(f)
            focalStation = FocalStation.FocalStation()
            focalStation.update(self.svConfig, self.statusFromGen2)
            adcFreeTest = ADCFreeTest.ADCFreePFTest()
            adcFreeTest.setUp()
            if focalStation.adcIsIn():
                adcFreeTest.setADCInDriveOnSync()
            else:
                adcFreeTest.setADCOut()
            self.statusFromGen2.update(adcFreeTest.statusFromGen2)
            if focalStation.rotIsIn():
                self.setAngle('rot', 0)
                self.setAngle('rotCmd', self.getAngle())
                self.pacmd.update(self.svConfig, self.statusFromGen2)
                break

    def paCmdAllOkTest(self):
        self.setAngle('rot', 0)
        self.setAngle('rotCmd', 0)

class PACmdPFTest(PACmdTest):
    def setUp(self):
        # Call our parent's setUp method.
        super(PACmdPFTest, self).setUp()
        # We will need a PACmdPF object, so create one here
        self.pacmd = PACmd.PACmdPF()
        self.alarmFuncs = {
            'paCmdWarning': {'Warning':  self.pacmd.paCmdWarning}
            }
        self.Gen2Alias = {'rotCmd': 'TSCS.INSROTCMD_PF', 'rot': 'TSCS.INSROTPOS_PF'}

    def testPACmd(self):
        self.setOpState(True)
        self.setTelDrive('Tracking')
        # The "PACmd" alarm depends on the focus settings, so iterate
        # through all of them. For this test we only care about the P
        # focal stations.
        for f in self.focusInfo.focusInfoIterator('^P_'):
            self.checkPACmd(f)

    def testIgnoreOpState(self):
        self.checkIgnoreOpState('^P_')

    def testIgnoreSlewing(self):
        self.checkIgnoreSlewing('^P_')

    def paCmdPFTest(self, focalStation = 'P_OPT'):
        super(PACmdPFTest, self).paCmdTest(focalStation)

    def paCmdPFAllOkTest(self):
        super(PACmdPFTest, self).paCmdAllOkTest()

class PACmdNsTest(PACmdTest):
    def setUp(self):
        # Call our parent's setUp method.
        super(PACmdNsTest, self).setUp()
        # We will need a PACmdNsCs object, so create one here
        self.pacmd = PACmd.PACmdNs()
        self.alarmFuncs = {
            'paCmdWarning': {'Warning':  self.pacmd.paCmdWarning}
            }
        self.Gen2Alias = {'rotCmd': 'TSCS.IMGROTCMD', 'rot': 'TSCS.ImgRotPos'}

    def testPACmd(self):
        self.setOpState(True)
        self.setTelDrive('Tracking')
        # The "PACmd" alarm depends on the focus settings, so iterate
        # through all of them. For this test we only care about the P
        # focal stations.
        for f in self.focusInfo.focusInfoIterator('^NS_'):
            self.checkPACmd(f)

    def testIgnoreOpState(self):
        self.checkIgnoreOpState('^NS_')

    def testIgnoreSlewing(self):
        self.checkIgnoreSlewing('^NS_')

    def paCmdNsTest(self, focalStation = 'NS_OPT'):
        super(PACmdNsTest, self).paCmdTest(focalStation)

    def paCmdNsAllOkTest(self):
        super(PACmdNsTest, self).paCmdAllOkTest()

class PACmdCsTest(PACmdTest):
    def setUp(self):
        # Call our parent's setUp method.
        super(PACmdCsTest, self).setUp()
        # We will need a PACmdNsCs object, so create one here
        self.pacmd = PACmd.PACmdCs()
        self.alarmFuncs = {
            'paCmdWarning': {'Warning':  self.pacmd.paCmdWarning}
            }
        self.Gen2Alias = {'rotCmd': 'TSCS.INSROTCMD', 'rot': 'TSCS.INSROTPOS'}

    def testPACmd(self):
        self.setOpState(True)
        self.setTelDrive('Tracking')
        # The "PACmd" alarm depends on the focus settings, so iterate
        # through all of them. For this test we only care about the P
        # focal stations.
        for f in self.focusInfo.focusInfoIterator('^CS_'):
            self.checkPACmd(f)

    def testIgnoreOpState(self):
        self.checkIgnoreOpState('^CS_')

    def testIgnoreSlewing(self):
        self.checkIgnoreSlewing('^CS_')

    def paCmdCsTest(self, focalStation = 'CS_OPT'):
        super(PACmdCsTest, self).paCmdTest(focalStation)

    def paCmdCsAllOkTest(self):
        super(PACmdCsTest, self).paCmdAllOkTest()

if __name__ == '__main__':
    unittest.main()

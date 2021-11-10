#!/usr/bin/env python

#
# ADCFree.py - Test the ADCFree class to make sure it:
#                - accurately reports alarm states
#                - ignores alarm warnings when dome
#                  is closed or telescope isslewing
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Thu Apr 26 16:55:08 HST 2012
#]
#

import unittest
import AlarmTest
import FocusInfo
import Gen2.alarm.ADCFree as ADCFree
import Gen2.alarm.FocalStation as FocalStation

class ADCFreeTest(AlarmTest.AlarmTest):
    def setUp(self):
        super(ADCFreeTest, self).setUp()
        # Will need a FocusInfo object.
        self.focusInfo = FocusInfo.FocusInfo()

    def getID(self, name):
        # Return the status variable ID
        return self.adcfree.statusVar[name]['ID']

    def setIn(self, adcIn):
        Gen2Alias = self.svConfig.configID[self.getID('ADC_In')].Gen2Alias
        if adcIn:
            self.statusFromGen2[Gen2Alias] = 0x08
        else:
            self.statusFromGen2[Gen2Alias] = 0x10

    def setDrive(self, driveOn):
        Gen2Alias = self.svConfig.configID[self.getID('ADC_DriveOn')].Gen2Alias
        if driveOn:
            self.statusFromGen2[Gen2Alias] = 0x01
        else:
            self.statusFromGen2[Gen2Alias] = 0x02

    def setADCInDriveOffSync(self):
        self.setIn(True)
        self.setDrive(False)
        self.setSyncMode(True)

    def setADCInDriveOnASync(self):
        self.setIn(True)
        self.setDrive(True)
        self.setSyncMode(False)

    def setADCInDriveOnSync(self):
        self.setIn(True)
        self.setDrive(True)
        self.setSyncMode(True)

    def setADCOut(self):
        self.setIn(False)
        self.setDrive(False)
        self.setSyncMode(False)

    def checkADCFree(self, f):
        self.setFocStation(f)
        if 'IN' in f['ADC']:
            self.setADCInDriveOffSync()
            self.adcfree.update(self.svConfig, self.statusFromGen2)
            self.assertTrue(self.alarmFuncs['adcFree']['Warning']())
            self.checkIgnoreFocalStation(False)

            self.setADCInDriveOnASync()
            self.adcfree.update(self.svConfig, self.statusFromGen2)
            self.assertTrue(self.alarmFuncs['adcFree']['Warning']())
            self.checkIgnoreFocalStation(False)

            self.setADCInDriveOnSync()
            self.adcfree.update(self.svConfig, self.statusFromGen2)
            self.assertFalse(self.alarmFuncs['adcFree']['Warning']())
            self.checkIgnoreFocalStation(False)
        else:
            self.setADCOut()
            self.adcfree.update(self.svConfig, self.statusFromGen2)
            self.assertFalse(self.alarmFuncs['adcFree']['Warning']())
            self.checkIgnoreFocalStation(False)

    def checkIgnoreFocalStation(self, ignore):
        for name in self.adcfree.compositeAlarms:
            ID = name
            svConfigItem = self.svConfig.configID[ID]
            if svConfigItem.Alarm:
                for severity in svConfigItem.Alarm:
                    if ignore:
                        self.assertTrue(svConfigItem.Alarm[severity].Ignore)
                    else:
                        self.assertFalse(svConfigItem.Alarm[severity].Ignore)

    def checkIgnoreAllFocalStations(self, ignore):
        for f in self.focusInfo.focusInfoIterator(''):
            self.setFocStation(f)
            self.adcfree.update(self.svConfig, self.statusFromGen2)
            self.checkIgnoreFocalStation(ignore)

    def checkIgnoreOpState(self):
        # Set dome, mirror covers, and telescope position to
        # non-operational and make sure all alarms are ignored.
        self.setOpState(False)
        self.setTelDrive('Tracking')
        self.checkIgnoreAllFocalStations(True)

    def checkIgnoreSlewing(self):
        self.setOpState(True)
        self.setTelDrive('Slewing')
        self.checkIgnoreAllFocalStations(True)

    def adcFreeDriveOnTest(self, focalStation = None):
        self.setOpState(True)
        self.setTelDrive('Tracking')        
        for f in self.focusInfo.focusInfoIterator(focalStation):
            self.focalStationName = f['FOCAL_STATION']
            self.setFocStation(f)
            focalStation = FocalStation.FocalStation()
            focalStation.update(self.svConfig, self.statusFromGen2)
            if focalStation.adcIsIn():
                self.setADCInDriveOnASync()
                self.adcfree.update(self.svConfig, self.statusFromGen2)
                break

    def adcFreeDriveOffTest(self, focalStation = None):
        self.setOpState(True)
        self.setTelDrive('Tracking')        
        for f in self.focusInfo.focusInfoIterator(focalStation):
            self.focalStationName = f['FOCAL_STATION']
            self.setFocStation(f)
            focalStation = FocalStation.FocalStation()
            focalStation.update(self.svConfig, self.statusFromGen2)
            if focalStation.adcIsIn():
                self.setADCInDriveOffSync()
                self.adcfree.update(self.svConfig, self.statusFromGen2)
                break

    def adcFreeAllOkTest(self, focalStation = None):
        self.setOpState(True)
        self.setTelDrive('Tracking')        
        for f in self.focusInfo.focusInfoIterator(focalStation):
            self.focalStationName = f['FOCAL_STATION']
            self.setFocStation(f)
            focalStation = FocalStation.FocalStation()
            focalStation.update(self.svConfig, self.statusFromGen2)
            if focalStation.adcIsIn():
                self.setADCInDriveOnSync()
                self.adcfree.update(self.svConfig, self.statusFromGen2)
                break

class ADCFreePFTest(ADCFreeTest):
    def setUp(self):
        # Now, call our parent's setUp method.
        super(ADCFreePFTest, self).setUp()
        # We will need an ADCFreePF object, so create one here
        self.adcfree = ADCFree.ADCFreePF()
        self.alarmFuncs = {
            'adcFree': {'Warning':  self.adcfree.adcFree}
            }

    def setSyncMode(self, syncMode):
        Gen2Alias = self.svConfig.configID[self.getID('ADC_SyncMode')].Gen2Alias
        if syncMode:
            self.statusFromGen2[Gen2Alias] = 0x40
        else:
            self.statusFromGen2[Gen2Alias] = 0x80

    def testADCFree(self):
        self.setOpState(True)
        self.setTelDrive('Tracking')
        # The "adcFree" alarm depends on the focus settings, so
        # iterate through all of them. For this test, we only care
        # about P focal stations
        for f in self.focusInfo.focusInfoIterator('P_'):
            self.checkADCFree(f)

    def testIgnoreOpState(self):
        self.checkIgnoreOpState()

    def testIgnoreSlewing(self):
        self.checkIgnoreSlewing()

    def adcFreePFAllOkTest(self, focalStation = 'P_OPT'):
        super(ADCFreePFTest, self).adcFreeAllOkTest(focalStation)

    def adcFreePFDriveOnTest(self, focalStation = 'P_OPT'):
        super(ADCFreePFTest, self).adcFreeDriveOnTest(focalStation)

    def adcFreePFDriveOffTest(self, focalStation = 'P_OPT'):
        super(ADCFreePFTest, self).adcFreeDriveOffTest(focalStation)

class ADCFreeNsCsTest(ADCFreeTest):
    def setUp(self):
        # Call our parent's setUp method.
        super(ADCFreeNsCsTest, self).setUp()
        # We will need an ADCFreeNsCs object, so create one here
        self.adcfree = ADCFree.ADCFreeNsCs()
        self.alarmFuncs = {
            'adcFree': {'Warning':  self.adcfree.adcFree}
            }

    def setSyncMode(self, syncMode):
        Gen2Alias = self.svConfig.configID[self.getID('ADC_SyncMode')].Gen2Alias
        if syncMode:
            self.statusFromGen2[Gen2Alias] = 0x04
        else:
            self.statusFromGen2[Gen2Alias] = 0x08

    def testADCFree(self):
        self.setOpState(True)
        self.setTelDrive('Tracking')
        # The "adcFree" alarm depends on the focus settings, so
        # iterate through all of them. For this test, we only care
        # about Ns and Cs focal stations.
        for f in self.focusInfo.focusInfoIterator('NS_|CS_'):
            self.checkADCFree(f)

    def testIgnoreOpState(self):
        self.checkIgnoreOpState()

    def testIgnoreSlewing(self):
        self.checkIgnoreSlewing()

    def adcFreeNsAllOkTest(self, focalStation = 'NS_OPT'):
        super(ADCFreeNsCsTest, self).adcFreeAllOkTest(focalStation)

    def adcFreeNsDriveOnTest(self, focalStation = 'NS_OPT'):
        super(ADCFreeNsCsTest, self).adcFreeDriveOnTest(focalStation)

    def adcFreeNsDriveOffTest(self, focalStation = 'NS_OPT'):
        super(ADCFreeNsCsTest, self).adcFreeDriveOffTest(focalStation)

    def adcFreeCsAllOkTest(self, focalStation = 'CS_OPT'):
        super(ADCFreeNsCsTest, self).adcFreeAllOkTest(focalStation)

    def adcFreeCsDriveOnTest(self, focalStation = 'CS_OPT'):
        super(ADCFreeNsCsTest, self).adcFreeDriveOnTest(focalStation)

    def adcFreeCsDriveOffTest(self, focalStation = 'CS_OPT'):
        super(ADCFreeNsCsTest, self).adcFreeDriveOffTest(focalStation)

if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python

#
# AG_PosnErrorTest.py - Test the AG_PosnError class to make sure it:
#                         - accurately reports alarm states
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Fri Apr 27 10:29:01 HST 2012
#]
#

import math
import unittest
import AlarmTest
import ADCFreeTest
import FocusInfo
import GuideStarTest
import Gen2.alarm.AG_PosnError as AG_PosnError
import Gen2.alarm.FocalStation as FocalStation

class AG_PosnErrorTest(AlarmTest.AutoguiderTest):
    def setUp(self):
        super(AG_PosnErrorTest, self).setUp()
        # We will need a AG_PosnError object, so create one here
        self.agPosnError = AG_PosnError.AG_PosnError()
        self.focusInfo = FocusInfo.FocusInfo()
        self.alarmFuncs = {
            'AG_Error': {'WarningHi': self.agPosnError.agPosnErrorWarn, 'CriticalHi':  self.agPosnError.agPosnErrorCrit},
            'SV_Error': {'WarningHi': self.agPosnError.svAGPosnErrorWarn, 'CriticalHi':  self.agPosnError.svAGPosnErrorCrit}
            }

    def checkAGPosnError(self, gmode, name, severity):
        self.setPosnError(gmode, name, severity)
        self.agPosnError.update(self.svConfig, self.statusFromGen2)
        if 'Ok' in severity:
            for s in self.alarmFuncs[name]:
                self.assertFalse(self.alarmFuncs[name][s]())
                self.assertFalse(self.alarmFuncs[name][s]())
        else:
            self.assertTrue(self.alarmFuncs[name][severity]())

    def testAGPosnErrorOk(self):
        for gmode in self.telState.telDriveModes['Guiding']:
            self.setTelDrive(gmode)
            if 'SV' in gmode:
                self.checkAGPosnError(gmode, 'SV_Error', 'Ok')
            else:
                self.checkAGPosnError(gmode, 'AG_Error', 'Ok')

    def testAGPosnErrorWarning(self):
        for gmode in self.telState.telDriveModes['Guiding']:
            self.setTelDrive(gmode)
            if 'SV' in gmode:
                self.checkAGPosnError(gmode, 'SV_Error', 'WarningHi')
            else:
                self.checkAGPosnError(gmode, 'AG_Error', 'WarningHi')

    def testAGPosnErrorCritical(self):
        for gmode in self.telState.telDriveModes['Guiding']:
            self.setTelDrive(gmode)
            if 'SV' in gmode:
                self.checkAGPosnError(gmode, 'SV_Error', 'CriticalHi')
            else:
                self.checkAGPosnError(gmode, 'AG_Error', 'CriticalHi')     

    def agPosnErrorTest(self, gmode, severity):
        self.setTelDrive(gmode)
        if 'SV' in gmode:
            name = 'SV_Error'
        else:
            name = 'AG_Error'
        if 'PIR' in gmode or 'FMOS' in gmode:
            focalStation = 'P_IR'
            if 'PIR' in gmode:
                self.statusFromGen2['TSCV.AGPIRCCalc'] = 0x04
            elif 'FMOS' in gmode:
                self.statusFromGen2['TSCV.AGFMOSCCalc'] = 0x04
        else:
            focalStation = 'NS_OPT'
        for f in self.focusInfo.focusInfoIterator(focalStation):
            self.focalStationName = f['FOCAL_STATION']
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
            self.setPosnError(gmode, name, severity)
            self.agPosnError.update(self.svConfig, self.statusFromGen2)
            break

    def agPosnErrorAG1WarningHiTest(self, severity = 'WarningHi'):
        self.agPosnErrorTest('Guiding(AG1)', severity)

    def agPosnErrorAG1CriticalHiTest(self, severity = 'CriticalHi'):
        self.agPosnErrorTest('Guiding(AG1)', severity)

    def agPosnErrorAGPIRWarningHiTest(self, severity = 'WarningHi'):
        self.agPosnErrorTest('Guiding(AGPIR)', severity)

    def agPosnErrorAGPIRCriticalHiTest(self, severity = 'CriticalHi'):
        self.agPosnErrorTest('Guiding(AGPIR)', severity)

    def agPosnErrorAGFMOSWarningHiTest(self, severity = 'WarningHi'):
        self.agPosnErrorTest('Guiding(AGFMOS)', severity)

    def agPosnErrorAGFMOSCriticalHiTest(self, severity = 'CriticalHi'):
        self.agPosnErrorTest('Guiding(AGFMOS)', severity)

    def agPosnErrorSV1WarningHiTest(self, severity = 'WarningHi'):
        self.agPosnErrorTest('Guiding(SV1)', severity)

    def agPosnErrorSV1CriticalHiTest(self, severity = 'CriticalHi'):
        self.agPosnErrorTest('Guiding(SV1)', severity)

    def agPosnErrorAllOkTest(self):
        for f in self.focusInfo.focusInfoIterator('NS_OPT'):
            self.focalStationName = f['FOCAL_STATION']
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
            break

        self.setPosnErrorAllOk()
        self.setIntensityAllOk()
        self.agPosnError.update(self.svConfig, self.statusFromGen2)

if __name__ == '__main__':
    unittest.main()

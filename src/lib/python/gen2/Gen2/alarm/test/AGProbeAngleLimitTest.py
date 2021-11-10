#!/usr/bin/env python

# Test the AGProbeRotAngleLimitNsCs classes to make sure it:
#  - accurately reports alarm states

import unittest
import AlarmTest
import AngleLimitTest
import ADCFreeTest
import FocusInfo
import Gen2.alarm.AngleLimit as AngleLimit
import Gen2.alarm.FocalStation as FocalStation

class AGProbeAngleLimitTest(AngleLimitTest.AngleLimitTest):
    def setUp(self):
        super(AGProbeAngleLimitTest, self).setUp()
        self.focusInfo = FocusInfo.FocusInfo()
        if hasattr(self, 'angleLimit'):
            self.alarmFuncs = {
                'AGProbeAngleLimit':
                {
                'WarningLo': self.angleLimit.agProbeAngleLimitWarningLo,
                'WarningHi': self.angleLimit.agProbeAngleLimitWarningHi,
                'CriticalLo': self.angleLimit.agProbeAngleLimitCriticalLo,
                'CriticalHi': self.angleLimit.agProbeAngleLimitCriticalHi
                }
                }
        self.Gen2Alias = {'ag': 'TSCV.AGTheta'}

    def setAngle(self, name, angle):
        super(AGProbeAngleLimitTest, self).setAngle(name, angle)
        if name in self.Gen2Alias:
            Gen2Alias = self.Gen2Alias[name]
            self.statusFromGen2[Gen2Alias] = angle

    def setAngleLimitTime(self, shortTime = True):
        super(AGProbeAngleLimitTest, self).setAngleLimitTime()

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

    def checkAllFocalStations(self, checkFunc, severity):
        for f in self.focusInfo.focusInfoIterator(self.focalStations):
            self.focalStationName = f['FOCAL_STATION']
            self.setFocStation(f)
            self.clearAlarmStates()
            self.setAlarmStates(severity)
            checkFunc(severity)

    def checkAGProbeAngleLimitAllOk(self):
        self.checkAllFocalStations(self.checkAngleLimit, {'Cmd': 'Ok', 'Act': 'Ok'})

    def checkAGProbeCmdLimitWarningLo(self):
        self.checkAllFocalStations(self.checkAngleLimit, {'Cmd': 'WarningLo', 'Act': 'Ok'})

    def checkAGProbeCmdLimitWarningHi(self):
        self.checkAllFocalStations(self.checkAngleLimit, {'Cmd': 'WarningHi', 'Act': 'Ok'})

    def checkAGProbeCmdLimitCriticalLo(self):
        self.checkAllFocalStations(self.checkAngleLimit, {'Cmd': 'CriticalLo', 'Act': 'Ok'})

    def checkAGProbeCmdLimitCriticalHi(self):
        self.checkAllFocalStations(self.checkAngleLimit, {'Cmd': 'CriticalHi', 'Act': 'Ok'})

    def checkAGProbeAngleLimitWarningLo(self):
        self.checkAllFocalStations(self.checkAngleLimit, {'Cmd': 'Ok', 'Act': 'WarningLo'})

    def checkAGProbeAngleLimitWarningHi(self):
        self.checkAllFocalStations(self.checkAngleLimit, {'Cmd': 'Ok', 'Act': 'WarningHi'})

    def checkAGProbeAngleLimitCriticalLo(self):
        self.checkAllFocalStations(self.checkAngleLimit, {'Cmd': 'Ok', 'Act': 'CriticalLo'})

    def checkAGProbeAngleLimitCriticalHi(self):
        self.checkAllFocalStations(self.checkAngleLimit, {'Cmd': 'Ok', 'Act': 'CriticalHi'})

    def agProbeAngleLimitTest(self, severity, focalStation = None):
        self.setOpState(True)
        self.setTelLimitFlag()
        self.setTelDrive('Tracking')
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
            self.setAngle(self.cmdName, self.getAngle(self.cmdName, severity['Cmd']))
            self.setAngle(self.actName, self.getAngle(self.actName, severity['Act']))
            self.angleLimit.update(self.svConfig, self.statusFromGen2)

    def agProbeAngleLimitAllOkTest(self):
        self.setAngleLimitTime(shortTime = False)
        self.setAngle(self.cmdName, 0)
        self.setAngle(self.actName, 0)

class AGProbeAngleLimitNsTest(AGProbeAngleLimitTest):
    def setUp(self):
        # We will need a AGProbeAngleLimitNs object, so create one here
        self.angleLimit = AngleLimit.AGProbeAngleLimitNs()
        # Call our parent's setUp method.
        super(AGProbeAngleLimitNsTest, self).setUp()

        self.focalStations = '^NS_'

        self.alarmFuncs['AGProbeAngleLimit_NS'] = {}
        for severity in self.alarmFuncs['AGProbeAngleLimit']:
            self.alarmFuncs['AGProbeAngleLimit_NS'][severity] = self.alarmFuncs['AGProbeAngleLimit'][severity]

    def testAGProbeAngleLimitAllOk(self):
        self.checkAGProbeAngleLimitAllOk()

    def testAGProbeCmdLimitWarningLo(self):
        self.checkAGProbeCmdLimitWarningLo()

    def testAGProbeCmdLimitWarningHi(self):
        self.checkAGProbeCmdLimitWarningHi()

    def testAGProbeCmdLimitCriticalLo(self):
        self.checkAGProbeCmdLimitCriticalLo()

    def testAGProbeCmdLimitCriticalHi(self):
        self.checkAGProbeCmdLimitCriticalHi()

    def testAGProbeAngleLimitWarningLo(self):
        self.checkAGProbeAngleLimitWarningLo()

    def testAGProbeAngleLimitWarningHi(self):
        self.checkAGProbeAngleLimitWarningHi()

    def testAGProbeAngleLimitCriticalLo(self):
        self.checkAGProbeAngleLimitCriticalLo()

    def testAGProbeAngleLimitCriticalHi(self):
        self.checkAGProbeAngleLimitCriticalHi()

    def agProbeAngleLimitNsTest(self, focalStation = 'NS_OPT', severity = 'WarningHi'):
        super(AGProbeAngleLimitNsTest, self).agProbeAngleLimitTest({'Cmd': severity, 'Act': severity}, focalStation)

    def agProbeAngleLimitNsAllOkTest(self):
        super(AGProbeAngleLimitNsTest, self).agProbeAngleLimitAllOkTest()

class AGProbeAngleLimitCsTest(AGProbeAngleLimitTest):
    def setUp(self):
        # We will need a AGProbeAngleLimitCs object, so create one here
        self.angleLimit = AngleLimit.AGProbeAngleLimitCs()
        # Call our parent's setUp method.
        super(AGProbeAngleLimitCsTest, self).setUp()
        self.focalStations = '^CS_'

        self.alarmFuncs['AGProbeAngleLimit_CS'] = {}
        for severity in self.alarmFuncs['AGProbeAngleLimit']:
            self.alarmFuncs['AGProbeAngleLimit_CS'][severity] = self.alarmFuncs['AGProbeAngleLimit'][severity]

    def testAGProbeAngleLimitAllOk(self):
        self.checkAGProbeAngleLimitAllOk()

    def testAGProbeCmdLimitWarningLo(self):
        self.checkAGProbeCmdLimitWarningLo()

    def testAGProbeCmdLimitWarningHi(self):
        self.checkAGProbeCmdLimitWarningHi()

    def testAGProbeCmdLimitCriticalLo(self):
        self.checkAGProbeCmdLimitCriticalLo()

    def testAGProbeCmdLimitCriticalHi(self):
        self.checkAGProbeCmdLimitCriticalHi()

    def testAGProbeAngleLimitWarningLo(self):
        self.checkAGProbeAngleLimitWarningLo()

    def testAGProbeAngleLimitWarningHi(self):
        self.checkAGProbeAngleLimitWarningHi()

    def testAGProbeAngleLimitCriticalLo(self):
        self.checkAGProbeAngleLimitCriticalLo()

    def testAGProbeAngleLimitCriticalHi(self):
        self.checkAGProbeAngleLimitCriticalHi()

    def agProbeAngleLimitCsTest(self, focalStation = 'CS_OPT', severity = 'WarningHi'):
        super(AGProbeAngleLimitCsTest, self).agProbeAngleLimitTest({'Cmd': severity, 'Act': severity}, focalStation)

    def agProbeAngleLimitCsAllOkTest(self):
        super(AGProbeAngleLimitCsTest, self).agProbeAngleLimitAllOkTest()

if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python

#
# RotAngleLimitTest.py - Test the RotAngleLimit* classes to make sure they:
#                          - accurately report alarm states
#                          - mute alarm warnings when telescope is
#                            non-operational, etc.
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Mon May  7 10:44:20 HST 2012
#]
#

import unittest
import AlarmTest
import AngleLimitTest 
import ADCFreeTest 
import FocusInfo
import Gen2.alarm.FocalStation as FocalStation
import Gen2.alarm.AngleLimit as AngleLimit

class RotAngleLimitTest(AngleLimitTest.AngleLimitTest):
    def setUp(self):
        super(RotAngleLimitTest, self).setUp()
        self.focusInfo = FocusInfo.FocusInfo()
        self.setTelDrive('Pointing')

        if hasattr(self, 'angleLimit'):
            self.alarmFuncs = {
                'RotAngleLimit':
                {
                'WarningLo': self.angleLimit.rotAngleLimitWarningLo,
                'WarningHi': self.angleLimit.rotAngleLimitWarningHi,
                'CriticalLo': self.angleLimit.rotAngleLimitCriticalLo,
                'CriticalHi': self.angleLimit.rotAngleLimitCriticalHi
                }
                }

    def setAngleLimitTime(self, shortTime = True):
        if shortTime:
            limitTime = self.getLimitTime()
            self.setTelLimitFlag(rotValid = True)
        else:
            limitTime = 100
        super(RotAngleLimitTest, self).setAngleLimitTime(limitTimeRot = limitTime)

    def fsSeverity(self, severity):
        return '_'.join([self.focalStationName, severity])

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
            if severity:
                self.setAlarmStates(severity)
            checkFunc(severity)

    def checkMuteWarningTelIsSlewing(self, severity):
        # Set telescope drive to 'slewing' and make sure alarms are
        # muted.
        self.setOpState(True)
        self.setTelLimitFlag(azValid = True)
        self.setTelDrive('Slewing')
        self.setAngleLimitTime(shortTime = True)
        self.setAngle(self.cmdName, 0)
        self.setAngle(self.actName, self.getAngle(self.actName, severity['Act']))
        self.angleLimit.update(self.svConfig, self.statusFromGen2)
        self.setAlarmStates(severity)
        self.checkAlarmStates()
        self.checkMuteStates(True)

    def checkMuteWarningsLimitTime(self, severity):
        self.setAngleLimitTime(shortTime = True)
        self.angleLimit.update(self.svConfig, self.statusFromGen2)
        self.muteStates['WarningHi'] = False
        self.muteStates['WarningLo'] = False
        self.checkMuteStates(False)

    def checkRotAngleLimitAllOk(self):
        self.checkAllFocalStations(self.checkAngleLimit, {'Cmd': 'Ok', 'Act': 'Ok'})

    def checkRotCmdLimitWarningLo(self):
        self.checkAllFocalStations(self.checkAngleLimit, {'Cmd': 'WarningLo', 'Act': 'Ok'})

    def checkRotCmdLimitWarningHi(self):
        self.checkAllFocalStations(self.checkAngleLimit, {'Cmd': 'WarningHi', 'Act': 'Ok'})

    def checkRotCmdLimitCriticalLo(self):
        self.checkAllFocalStations(self.checkAngleLimit, {'Cmd': 'CriticalLo', 'Act': 'Ok'})

    def checkRotCmdLimitCriticalHi(self):
        self.checkAllFocalStations(self.checkAngleLimit, {'Cmd': 'CriticalHi', 'Act': 'Ok'})

    def checkRotAngleLimitWarningLo(self):
        self.checkAllFocalStations(self.checkAngleLimit, {'Cmd': 'Ok', 'Act': 'WarningLo'})

    def checkRotAngleLimitWarningHi(self):
        self.checkAllFocalStations(self.checkAngleLimit, {'Cmd': 'Ok', 'Act': 'WarningHi'})

    def checkRotAngleLimitCriticalLo(self):
        self.checkAllFocalStations(self.checkAngleLimit, {'Cmd': 'Ok', 'Act': 'CriticalLo'})

    def checkRotAngleLimitCriticalHi(self):
        self.checkAllFocalStations(self.checkAngleLimit, {'Cmd': 'Ok', 'Act': 'CriticalHi'})

    def checkRotAngleLimitMuteWarnings(self):
        self.checkAllFocalStations(self.checkMuteWarningsBigLimitTime, {'Cmd': 'Ok', 'Act': 'CriticalHi'})
        self.checkAllFocalStations(self.checkMuteWarningsNoLimitFlag, {'Cmd': 'Ok', 'Act': 'CriticalHi'})
        self.checkAllFocalStations(self.checkMuteWarningsLimitTime, None)

    def checkRotAngleLimitMuteDomeClosed(self):
        self.setAngleLimitTime(shortTime = True)
        self.checkAllFocalStations(self.checkMuteDomeClosed, {'Cmd': 'Ok', 'Act': 'CriticalHi'})

    def checkRotAngleLimitMuteMirrorClosed(self):
        self.setAngleLimitTime(shortTime = True)
        self.checkAllFocalStations(self.checkMuteMirrorClosed, {'Cmd': 'Ok', 'Act': 'CriticalHi'})

    def checkRotAngleLimitMuteTelStowed(self):
        self.setAngleLimitTime(shortTime = True)
        self.checkAllFocalStations(self.checkMuteTelStowed, {'Cmd': 'Ok', 'Act': 'CriticalHi'})

    def checkRotAngleLimitMuteOpState(self):
        self.setAngleLimitTime(shortTime = True)
        self.checkAllFocalStations(self.checkMuteOpState, {'Cmd': 'Ok', 'Act': 'CriticalHi'})

    def checkRotAngleLimitMuteTelIsSlewing(self):
        self.setAngleLimitTime(shortTime = True)
        self.checkAllFocalStations(self.checkMuteWarningTelIsSlewing, {'Cmd': 'Ok', 'Act': 'CriticalHi'})

    def rotAngleLimitTest(self, severity, focalStation = None):
        self.setOpState(True)
        self.setTelLimitFlag(azValid = True)
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
            if focalStation.rotIsIn():
                if severity['Cmd'] == 'Ok' and severity['Act'] == 'Ok':
                    self.setAngleLimitTime(shortTime = False)
                else:
                    self.setAngleLimitTime(shortTime = True)
                self.setAngle(self.cmdName, self.getAngle(self.cmdName, severity['Cmd']))
                self.setAngle(self.actName, self.getAngle(self.actName, severity['Act']))
                self.angleLimit.update(self.svConfig, self.statusFromGen2)
                break

    def rotAngleLimitMuteWarningsBigLimitTimeTest(self, severity, focalStation = None):
        self.setOpState(True)
        self.setTelLimitFlag(azValid = True)
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
            if focalStation.rotIsIn():
                self.setAngleLimitTime(shortTime = False)
                self.setAngle(self.cmdName, self.getAngle(self.cmdName, severity['Cmd']))
                self.setAngle(self.actName, self.getAngle(self.actName, severity['Act']))
                self.angleLimit.update(self.svConfig, self.statusFromGen2)
                break

    def rotAngleLimitMuteWarningsNoLimitFlagTest(self, severity, focalStation = None):
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
            if focalStation.rotIsIn():
                self.setAngle(self.cmdName, self.getAngle(self.cmdName, severity['Cmd']))
                self.setAngle(self.actName, self.getAngle(self.actName, severity['Act']))
                self.angleLimit.update(self.svConfig, self.statusFromGen2)
                break

    def rotAngleLimitAllOkTest(self):
        self.setAngleLimitTime(shortTime = False)
        self.setAngle(self.cmdName, 0)
        self.setAngle(self.actName, 0)

class RotAngleLimitP_IRTest(RotAngleLimitTest):
    def setUp(self):
        # We will need a RotAngleLimitP_IR object, so create one here
        self.angleLimit = AngleLimit.RotAngleLimitP_IR()
        # Call our parent's setUp method.
        super(RotAngleLimitP_IRTest, self).setUp()
        self.focalStations = 'P_IR'

        self.alarmFuncs['RotAngleLimit_P_IR'] = {}
        for severity in self.alarmFuncs['RotAngleLimit']:
            self.alarmFuncs['RotAngleLimit_P_IR'][severity] = self.alarmFuncs['RotAngleLimit'][severity]

    def testRotAngleLimitAllOk(self):
        self.checkRotAngleLimitAllOk()

    def testRotCmdLimitWarningLo(self):
        self.checkRotCmdLimitWarningLo()

    def testRotCmdLimitWarningHi(self):
        self.checkRotCmdLimitWarningHi()

    def testRotCmdLimitCriticalLo(self):
        self.checkRotCmdLimitCriticalLo()

    def testRotCmdLimitCriticalHi(self):
        self.checkRotCmdLimitCriticalHi()

    def testRotAngleLimitWarningLo(self):
        self.checkRotAngleLimitWarningLo()

    def testRotAngleLimitWarningHi(self):
        self.checkRotAngleLimitWarningHi()

    def testRotAngleLimitCriticalLo(self):
        self.checkRotAngleLimitCriticalLo()

    def testRotAngleLimitCriticalHi(self):
        self.checkRotAngleLimitCriticalHi()

    def testRotAngleLimitMuteWarnings(self):
        self.checkRotAngleLimitMuteWarnings()

    def testRotAngleLimitMuteDomeClosed(self):
        self.checkRotAngleLimitMuteDomeClosed()

    def testRotAngleLimitMuteMirrorClosed(self):
        self.checkRotAngleLimitMuteMirrorClosed()

    def testRotAngleLimitMuteTelStowed(self):
        self.checkRotAngleLimitMuteTelStowed()

    def testRotAngleLimitMuteOpState(self):
        self.checkRotAngleLimitMuteOpState()

    def testRotAngleLimitMuteTelIsSlewing(self):
        self.checkRotAngleLimitMuteTelIsSlewing()

    def rotAngleLimitP_IRTest(self, focalStation = 'P_IR', severity = 'WarningHi'):
        super(RotAngleLimitP_IRTest, self).rotAngleLimitTest({'Cmd': severity, 'Act': severity}, focalStation)

    def rotAngleLimitP_IRBigLimitTimeTest(self, focalStation = 'P_IR', severity = 'WarningHi'):
        super(RotAngleLimitP_IRTest, self).rotAngleLimitMuteWarningsBigLimitTimeTest({'Cmd': severity, 'Act': severity}, focalStation)

    def rotAngleLimitP_IRNoLimitFlagTest(self, focalStation = 'P_IR', severity = 'WarningHi'):
        super(RotAngleLimitP_IRTest, self).rotAngleLimitMuteWarningsNoLimitFlagTest({'Cmd': severity, 'Act': severity}, focalStation)

    def rotAngleLimitP_IRAllOkTest(self):
        super(RotAngleLimitP_IRTest, self).rotAngleLimitAllOkTest()

class RotAngleLimitP_OPTTest(RotAngleLimitTest):
    def setUp(self):
        # We will need a RotAngleLimitP_OPT object, so create one here
        self.angleLimit = AngleLimit.RotAngleLimitP_OPT()
        # Call our parent's setUp method.
        super(RotAngleLimitP_OPTTest, self).setUp()
        self.focalStations = 'P_OPT'

        self.alarmFuncs['RotAngleLimit_P_OPT'] = {}
        for severity in self.alarmFuncs['RotAngleLimit']:
            self.alarmFuncs['RotAngleLimit_P_OPT'][severity] = self.alarmFuncs['RotAngleLimit'][severity]

    def testRotAngleLimitAllOk(self):
        self.checkRotAngleLimitAllOk()

    def testRotCmdLimitWarningLo(self):
        self.checkRotCmdLimitWarningLo()

    def testRotCmdLimitWarningHi(self):
        self.checkRotCmdLimitWarningHi()

    def testRotCmdLimitCriticalLo(self):
        self.checkRotCmdLimitCriticalLo()

    def testRotCmdLimitCriticalHi(self):
        self.checkRotCmdLimitCriticalHi()

    def testRotAngleLimitWarningLo(self):
        self.checkRotAngleLimitWarningLo()

    def testRotAngleLimitWarningHi(self):
        self.checkRotAngleLimitWarningHi()

    def testRotAngleLimitCriticalLo(self):
        self.checkRotAngleLimitCriticalLo()

    def testRotAngleLimitCriticalHi(self):
        self.checkRotAngleLimitCriticalHi()

    def testRotAngleLimitMuteWarnings(self):
        self.checkRotAngleLimitMuteWarnings()

    def testRotAngleLimitMuteDomeClosed(self):
        self.checkRotAngleLimitMuteDomeClosed()

    def testRotAngleLimitMuteMirrorClosed(self):
        self.checkRotAngleLimitMuteMirrorClosed()

    def testRotAngleLimitMuteTelStowed(self):
        self.checkRotAngleLimitMuteTelStowed()

    def testRotAngleLimitMuteOpState(self):
        self.checkRotAngleLimitMuteOpState()

    def testRotAngleLimitMuteTelIsSlewing(self):
        self.checkRotAngleLimitMuteTelIsSlewing()

    def rotAngleLimitP_OPTTest(self, focalStation = 'P_OPT', severity = 'WarningHi'):
        super(RotAngleLimitP_OPTTest, self).rotAngleLimitTest({'Cmd': severity, 'Act': severity}, focalStation)

    def rotAngleLimitP_OPTAllOkTest(self):
        super(RotAngleLimitP_OPTTest, self).rotAngleLimitAllOkTest()

class RotAngleLimitNsTest(RotAngleLimitTest):
    def setUp(self):
        # We will need a RotAngleLimitNs object, so create one here
        self.angleLimit = AngleLimit.RotAngleLimitNs()
        # Call our parent's setUp method.
        super(RotAngleLimitNsTest, self).setUp()

        self.focalStations = '^NS_'

        self.alarmFuncs['RotAngleLimit_NS'] = {}
        for severity in self.alarmFuncs['RotAngleLimit']:
            self.alarmFuncs['RotAngleLimit_NS'][severity] = self.alarmFuncs['RotAngleLimit'][severity]

    def testRotAngleLimitAllOk(self):
        self.checkRotAngleLimitAllOk()

    def testRotCmdLimitWarningLo(self):
        self.checkRotCmdLimitWarningLo()

    def testRotCmdLimitWarningHi(self):
        self.checkRotCmdLimitWarningHi()

    def testRotCmdLimitCriticalLo(self):
        self.checkRotCmdLimitCriticalLo()

    def testRotCmdLimitCriticalHi(self):
        self.checkRotCmdLimitCriticalHi()

    def testRotAngleLimitWarningLo(self):
        self.checkRotAngleLimitWarningLo()

    def testRotAngleLimitWarningHi(self):
        self.checkRotAngleLimitWarningHi()

    def testRotAngleLimitCriticalLo(self):
        self.checkRotAngleLimitCriticalLo()

    def testRotAngleLimitCriticalHi(self):
        self.checkRotAngleLimitCriticalHi()

    def testRotAngleLimitMuteWarnings(self):
        self.checkRotAngleLimitMuteWarnings()

    def testRotAngleLimitMuteDomeClosed(self):
        self.checkRotAngleLimitMuteDomeClosed()

    def testRotAngleLimitMuteMirrorClosed(self):
        self.checkRotAngleLimitMuteMirrorClosed()

    def testRotAngleLimitMuteTelStowed(self):
        self.checkRotAngleLimitMuteTelStowed()

    def testRotAngleLimitMuteOpState(self):
        self.checkRotAngleLimitMuteOpState()

    def testRotAngleLimitMuteTelIsSlewing(self):
        self.checkRotAngleLimitMuteTelIsSlewing()

    def rotAngleLimitNsTest(self, focalStation = 'NS_OPT', severity = 'WarningHi'):
        super(RotAngleLimitNsTest, self).rotAngleLimitTest({'Cmd': severity, 'Act': severity}, focalStation)

    def rotAngleLimitNsAllOkTest(self):
        super(RotAngleLimitNsTest, self).rotAngleLimitAllOkTest()

class RotAngleLimitCsTest(RotAngleLimitTest):
    def setUp(self):
        # We will need a RotAngleLimitCs object, so create one here
        self.angleLimit = AngleLimit.RotAngleLimitCs()
        # Call our parent's setUp method.
        super(RotAngleLimitCsTest, self).setUp()

        self.focalStations = '^CS_'

        self.alarmFuncs['RotAngleLimit_CS'] = {}
        for severity in self.alarmFuncs['RotAngleLimit']:
            self.alarmFuncs['RotAngleLimit_CS'][severity] = self.alarmFuncs['RotAngleLimit'][severity]

    def testRotAngleLimitAllOk(self):
        self.checkRotAngleLimitAllOk()

    def testRotCmdLimitWarningLo(self):
        self.checkRotCmdLimitWarningLo()

    def testRotCmdLimitWarningHi(self):
        self.checkRotCmdLimitWarningHi()

    def testRotCmdLimitCriticalLo(self):
        self.checkRotCmdLimitCriticalLo()

    def testRotCmdLimitCriticalHi(self):
        self.checkRotCmdLimitCriticalHi()

    def testRotAngleLimitWarningLo(self):
        self.checkRotAngleLimitWarningLo()

    def testRotAngleLimitWarningHi(self):
        self.checkRotAngleLimitWarningHi()

    def testRotAngleLimitCriticalLo(self):
        self.checkRotAngleLimitCriticalLo()

    def testRotAngleLimitCriticalHi(self):
        self.checkRotAngleLimitCriticalHi()

    def testRotAngleLimitMuteWarnings(self):
        self.checkRotAngleLimitMuteWarnings()

    def testRotAngleLimitMuteDomeClosed(self):
        self.checkRotAngleLimitMuteDomeClosed()

    def testRotAngleLimitMuteMirrorClosed(self):
        self.checkRotAngleLimitMuteMirrorClosed()

    def testRotAngleLimitMuteTelStowed(self):
        self.checkRotAngleLimitMuteTelStowed()

    def testRotAngleLimitMuteOpState(self):
        self.checkRotAngleLimitMuteOpState()

    def testRotAngleLimitMuteTelIsSlewing(self):
        self.checkRotAngleLimitMuteTelIsSlewing()

    def rotAngleLimitCsTest(self, focalStation = 'CS_OPT', severity = 'WarningHi'):
        super(RotAngleLimitCsTest, self).rotAngleLimitTest({'Cmd': severity, 'Act': severity}, focalStation)

    def rotAngleLimitCsAllOkTest(self):
        super(RotAngleLimitCsTest, self).rotAngleLimitAllOkTest()

if __name__ == '__main__':
    unittest.main()

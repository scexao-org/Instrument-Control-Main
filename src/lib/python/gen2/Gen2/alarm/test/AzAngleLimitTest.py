#!/usr/bin/env python

#
# AzAngleLimitTest.py - Test the AzAngleLimit class to make sure it:
#                         - accurately reports alarm states
#                         - mutes alarm warnings when telescope is
#                           non-operational, etc.
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Mon May  7 10:59:45 HST 2012
#]
#

import unittest
import AlarmTest
import AngleLimitTest
import Gen2.alarm.AngleLimit as AngleLimit

class AzAngleLimitTest(AngleLimitTest.AngleLimitTest):
    def setUp(self):
        # We will need an AzAngleLimit object, so create one here
        self.angleLimit = AngleLimit.AzAngleLimit()
        super(AzAngleLimitTest, self).setUp()

        self.alarmFuncs = {
            'AzAngleLimit':
            {
            'WarningLo':  self.angleLimit.azAngleLimitWarningLo,
            'CriticalLo': self.angleLimit.azAngleLimitCriticalLo,
            'WarningHi':  self.angleLimit.azAngleLimitWarningHi,
            'CriticalHi': self.angleLimit.azAngleLimitCriticalHi
            }
            }

    def setAngleLimitTime(self, shortTime = True):
        if shortTime:
            limitTime = self.getLimitTime()
            self.setTelLimitFlag(azValid = True)
        else:
            limitTime = 100
        super(AzAngleLimitTest, self).setAngleLimitTime(limitTimeAz = limitTime)

    def testAzAngleLimitAllOk(self):
        self.checkAngleLimit({'Cmd': 'Ok', 'Act': 'Ok'})

    def testAzCmdLimitWarningLo(self):
        severity = {'Cmd': 'WarningLo', 'Act': 'Ok'}
        self.setAlarmStates(severity)
        self.checkAngleLimit(severity)

    def testAzCmdLimitWarningHi(self):
        severity = {'Cmd': 'WarningHi', 'Act': 'Ok'}
        self.setAlarmStates(severity)
        self.checkAngleLimit(severity)

    def testAzCmdLimitCriticalLo(self):
        severity = {'Cmd': 'CriticalLo', 'Act': 'Ok'}
        self.setAlarmStates(severity)
        self.checkAngleLimit(severity)

    def testAzCmdLimitCriticalHi(self):
        severity = {'Cmd': 'CriticalHi', 'Act': 'Ok'}
        self.setAlarmStates(severity)
        self.checkAngleLimit(severity)

    def testAzLimitWarningLo(self):
        severity = {'Cmd': 'Ok', 'Act': 'WarningLo'}
        self.setAlarmStates(severity)
        self.checkAngleLimit(severity)

    def testAzLimitWarningHi(self):
        severity = {'Cmd': 'Ok', 'Act': 'WarningHi'}
        self.setAlarmStates(severity)
        self.checkAngleLimit(severity)

    def testAzLimitCriticalLo(self):
        severity = {'Cmd': 'Ok', 'Act': 'CriticalLo'}
        self.setAlarmStates(severity)
        self.checkAngleLimit(severity)

    def testAzLimitCriticalHi(self):
        severity = {'Cmd': 'Ok', 'Act': 'CriticalHi'}
        self.setAlarmStates(severity)
        self.checkAngleLimit(severity)

    def testAzAngleLimitWarningLo(self):
        severity = {'Cmd': 'WarningLo', 'Act': 'WarningLo'}
        self.setAlarmStates(severity)
        self.checkAngleLimit(severity)

    def testAzAngleLimitWarningHi(self):
        severity = {'Cmd': 'WarningHi', 'Act': 'WarningHi'}
        self.setAlarmStates(severity)
        self.checkAngleLimit(severity)

    def testAzAngleLimitCriticalLo(self):
        severity = {'Cmd': 'CriticalLo', 'Act': 'CriticalLo'}
        self.setAlarmStates(severity)
        self.checkAngleLimit(severity)

    def testAzAngleLimitCriticalHi(self):
        severity = {'Cmd': 'CriticalHi', 'Act': 'CriticalHi'}
        self.setAlarmStates(severity)
        self.checkAngleLimit(severity)

    def testAzAngleLimitMuteWarnings(self):
        # For these two calls, warnings will be muted because
        # checkMuteWarningsBigLimitTime sets the "time to limit" to a
        # large number, i.e., greater than the threshold. These calls
        # check that warning alarms are muted for angles in both
        # warning and critical states.
        self.checkMuteWarningsBigLimitTime({'Cmd': 'WarningHi',  'Act': 'WarningHi'})
        self.checkMuteWarningsBigLimitTime({'Cmd': 'CriticalHi', 'Act': 'CriticalHi'})

        # For these two calls, warnings will be muted because
        # checkMuteWarningsNoLimitFlag sets the "time to limit" flag
        # to 0, which basically means that the "time to limit" is
        # infinite. These calls check that warning alarms are muted
        # for angles in both warning and critical states.
        self.checkMuteWarningsNoLimitFlag({'Cmd': 'WarningHi',  'Act': 'WarningHi'})
        self.checkMuteWarningsNoLimitFlag({'Cmd': 'CriticalHi', 'Act': 'CriticalHi'})

        # Now set the "time to limit" to a number less than the
        # threshold. Check to make sure that the warning alarms are
        # *not* muted.
        self.setAngleLimitTime(shortTime = True)
        self.angleLimit.update(self.svConfig, self.statusFromGen2)
        self.setMuteStates('Warning', False)
        self.checkMuteStates(False)

    def testAzAngleLimitMuteDomeClosed(self):
        # This test sets the dome to "closed" and then checks to make
        # sure that *all* alarms indicate that they are muted.
        severity = {'Cmd': 'Ok', 'Act': 'WarningHi'}
        self.setAlarmStates(severity)
        # Set the "time to limit" to below the threshold so that the
        # Warning alarms aren't muted by the "time to limit" criterion.
        self.setAngleLimitTime(shortTime = True)
        self.checkMuteDomeClosed(severity)

    def testAzAngleLimitMuteMirrorClosed(self):
        # This test sets the mirror covers to "closed" and then checks
        # to make sure that *all* alarms indicate that they are muted.
        severity = {'Cmd': 'Ok', 'Act': 'CriticalHi'}
        self.setAlarmStates(severity)
        # Set the "time to limit" to below the threshold so that the
        # Warning alarms aren't muted by the "time to limit" criterion.
        self.setAngleLimitTime(shortTime = True)
        self.checkMuteMirrorClosed(severity)

    def testAzAngleLimitMuteTelStowed(self):
        # This test sets the telescope to "stowed" and then checks
        # to make sure that *all* alarms indicate that they are muted.
        severity = {'Cmd': 'Ok', 'Act': 'CriticalHi'}
        self.setAlarmStates(severity)
        # Set the "time to limit" to below the threshold so that the
        # Warning alarms aren't muted by the "time to limit" criterion.
        self.setAngleLimitTime(shortTime = True)
        self.checkMuteTelStowed(severity)

    def testAzAngleLimitMuteOpState(self):
        # This test sets the dome/telescope/mirror covers to
        # "non-operational" and then checks to make sure that *all*
        # alarms indicate that they are muted.
        severity = {'Cmd': 'Ok', 'Act': 'CriticalHi'}
        self.setAlarmStates(severity)
        # Set the "time to limit" to below the threshold so that the
        # Warning alarms aren't muted by the "time to limit" criterion.
        self.setAngleLimitTime(shortTime = True)
        self.checkMuteOpState(severity)

    def azAngleLimitMuteWarningsBigLimitTimeTest(self):
        # Warnings will be muted because checkMuteWarningsBigLimitTime
        # sets the "time to limit" to a large number, i.e., greater
        # than the threshold.
        self.checkMuteWarningsBigLimitTime({'Cmd': 'WarningHi',  'Act': 'WarningHi'})

    def azAngleLimitMuteWarningsNoLimitFlagTest(self):
        # Warnings will be muted because checkMuteWarningsNoLimitFlag
        # sets the limit flags to 0, which basically means that the
        # "time to limit" is infinite.
        self.checkMuteWarningsNoLimitFlag({'Cmd': 'WarningHi',  'Act': 'WarningHi'})

if __name__ == '__main__':
    unittest.main()

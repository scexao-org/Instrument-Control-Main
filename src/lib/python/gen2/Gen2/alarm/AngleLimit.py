#!/usr/bin/env python

#
# AngleLimit.py - methods for determining if the telescope azimuth or
#                 instrument rotator are near a limit.
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Mon May  7 09:08:13 HST 2012
#]
#
# AngleLimit.py supplies methods to check the following conditions for
# alarm states:
#
# 1. Telescope azimuth commanded or actual angles are near the rotation limit
# 2. Rotator commanded or actual angles are near the rotation limit
# 3. AG Probe commanded or actual angles are near the rotation limit
#
# AngleLimit is the base class. Also in this file are the subclasses
# AzAngleLimit, RotAngleLimit, and AGProbeAngleLimit, which implement
# the alarms for their respective hardware.
#

import re
import remoteObjects as ro
import Derived
import AngleLimitTime

class AngleLimit(Derived.Derived):
    def __init__(self, logger = ro.nullLogger()):
        super(AngleLimit, self).__init__(logger)

        # We will need an AngleLimitTime object, so create one here.
        #        self.angleLimitTime = AngleLimitTime.AngleLimitTime()
        self.angleLimitTime = None
        # We will store DomeShutter, MirrorCover, TelState, and
        # FocalStation objects here. We need these because we want to
        # mute the alarms when the dome is closed and telescope is
        # "inactive".
        self.domeShutter = None
        self.mirrorCover = None
        self.telState = None

    # Update our status variable values based on the current status as
    # supplied to us via the Gen2 status aliases.
    def update(self, svConfig, statusFromGen2):
        super(AngleLimit, self).update(svConfig, statusFromGen2)
        
        # Get references to the DomeShutter, MirrorCover, and TelState
        # objects.
        if self.domeShutter == None:
            self.domeShutter = svConfig.configID['DomeShutter'].importedObject
        if self.mirrorCover == None:
            self.mirrorCover = svConfig.configID['MirrorCover'].importedObject
        if self.telState == None:
            self.telState = svConfig.configID['TelState'].importedObject

        # Update the dome shutter, mirror cover, and telescope state
        # status variables.
        self.domeShutter.update(svConfig, statusFromGen2)
        self.mirrorCover.update(svConfig, statusFromGen2)
        self.telState.update(svConfig, statusFromGen2)

        if self.angleLimitTime == None:
            self.angleLimitTime = svConfig.configID['AngleLimitTime'].importedObject
        self.angleLimitTime.update(svConfig, statusFromGen2)
        
    # This section has some logic to mute the alarms based on the
    # current telescope status. There are two conditions under
    # which we want to mute the alarms.
    #
    # 1. Mute all alarms if the telescope is "inactive", i.e., if
    #    the mirror covers are closed or the dome shutter is closed
    #    or the telescope is in the stowed position.
    #
    # 2. Mute the "warning" alarms if the computed time to the
    #    limit is greater than the warning threshold.
    #
    def getMuteAllAlarms(self):

        muteAllAlarms = False
        if self.mirrorCover.m1Closed() or \
                self.domeShutter.shutterClosed() or \
                self.telState.elStowed():
            muteAllAlarms = True
        else:
            muteAllAlarms = False
        return muteAllAlarms

    def getMuteWarningAlarms(self, limitFlag, limitName, limitTime):
        muteWarningAlarms = False
        if limitFlag == 0 or \
               (limitFlag and \
                limitTime > self.angleLimitTime.limitThreshold(limitName, 'WarningLo')):
            muteWarningAlarms = True
        else:
            muteWarningAlarms = False
        return muteWarningAlarms

    def doMuteAlarms(self, muteAllAlarms, muteWarningAlarms):
        # Un-mute all alarms and then mute any that need to be muted
        # based on the results of the above logic.
        self.setAllMuteState(False)
        if muteAllAlarms:
            self.setAllMuteState(True)
        elif muteWarningAlarms:
            self.setAllWarningMuteState(True)

    def limitThreshold(self, name, severity):
        svConfigItem = self.svConfig.configID[self.statusVar[name]['ID']]
        return svConfigItem.Alarm[severity].Threshold

    def limitAlarmState(self, name, limitThreshold, severity):
        ID = self.statusVar[name]['ID']
        svConfigItem = self.svConfig.configID[ID]
        FocalStation = svConfigItem.FocalStation
        if FocalStation == None or \
               FocalStation and (FocalStation in self.focalStation()):
            if 'Lo' in severity:
                if self.statusVar[name]['value'] <= limitThreshold:
                    return True
                else:
                    return False
            elif 'Hi' in severity:
                if self.statusVar[name]['value'] >= limitThreshold:
                    return True
                else:
                    return False
        else:
            return False

class AzAngleLimit(AngleLimit):
    def __init__(self, logger = ro.nullLogger()):
        super(AzAngleLimit, self).__init__(logger)
        self.statusVar = {
            'azCmd': {'ID': 'Melco_0002003', 'value': None},
            'az':    {'ID': 'Melco_00A11BF', 'value': None}
            }
        self.compositeAlarms = ('AzAngleLimit', )
        self.angleLimitTimeMin = None

    def update(self, svConfig, statusFromGen2):
        super(AzAngleLimit, self).update(svConfig, statusFromGen2)
        muteAllAlarms = self.getMuteAllAlarms()
        if self.angleLimitTimeMin == None:
            self.angleLimitTimeMin = svConfig.configID['AngleLimitTimeMin'].importedObject

        self.angleLimitTimeMin.update(svConfig, statusFromGen2)
        muteWarningAlarms = self.getMuteWarningAlarms(self.telState.limitFlagAz(), 'limitTimeAz', self.angleLimitTimeMin.limitTimeAz())
        self.doMuteAlarms(muteAllAlarms, muteWarningAlarms)

    def azCmdLimitWarningLo(self):
        name = 'azCmd'
        severity = 'WarningLo'
        threshold = self.limitThreshold(name, severity)
        return self.limitAlarmState(name, threshold, severity)
    def azCmdLimitCriticalLo(self):
        name = 'azCmd'
        severity = 'CriticalLo'
        threshold = self.limitThreshold(name, severity)
        return self.limitAlarmState(name, threshold, severity)

    def azCmdLimitWarningHi(self):
        name = 'azCmd'
        severity = 'WarningHi'
        threshold = self.limitThreshold(name, severity)
        return self.limitAlarmState(name, threshold, severity)
    def azCmdLimitCriticalHi(self):
        name = 'azCmd'
        severity = 'CriticalHi'
        threshold = self.limitThreshold(name, severity)
        return self.limitAlarmState(name, threshold, severity)

    def azLimitWarningLo(self):
        name = 'az'
        severity = 'WarningLo'
        threshold = self.limitThreshold(name, severity)
        return self.limitAlarmState(name, threshold, severity)
    def azLimitCriticalLo(self):
        name = 'az'
        severity = 'CriticalLo'
        threshold = self.limitThreshold(name, severity)
        return self.limitAlarmState(name, threshold, severity)

    def azLimitWarningHi(self):
        name = 'az'
        severity = 'WarningHi'
        threshold = self.limitThreshold(name, severity)
        return self.limitAlarmState(name, threshold, severity)
    def azLimitCriticalHi(self):
        name = 'az'
        severity = 'CriticalHi'
        threshold = self.limitThreshold(name, severity)
        return self.limitAlarmState(name, threshold, severity)

    def azAngleLimitWarningLo(self):
        return self.azCmdLimitWarningLo() or self.azLimitWarningLo()
    def azAngleLimitCriticalLo(self):
        return self.azCmdLimitCriticalLo() or self.azLimitCriticalLo()
    def azAngleLimitWarningHi(self):
        return self.azCmdLimitWarningHi() or self.azLimitWarningHi()
    def azAngleLimitCriticalHi(self):
        return self.azCmdLimitCriticalHi() or self.azLimitCriticalHi()

class RotAngleLimit(AngleLimit):

    def update(self, svConfig, statusFromGen2):
        super(RotAngleLimit, self).update(svConfig, statusFromGen2)
        self.FocalStation = svConfig.configID['FocalStation'].importedObject
        self.FocalStation.update(svConfig, statusFromGen2)

        muteAllAlarms = self.getMuteAllAlarms()
        telState = svConfig.configID['TelState'].importedObject
        muteAllAlarms = muteAllAlarms or telState.isSlewing()

        angleLimitTimeMin = svConfig.configID['AngleLimitTimeMin'].importedObject
        angleLimitTimeMin.update(svConfig, statusFromGen2)

        muteWarningAlarms = self.getMuteWarningAlarms(angleLimitTimeMin.limitTimeRot(), 'limitTimeRot', angleLimitTimeMin.limitTimeRot())
        self.doMuteAlarms(muteAllAlarms, muteWarningAlarms)

        # Set our alarms' Ignore state based on whether or not the
        # current focal station matches the focal station associated
        # with our alarms.
#        self.setAllIgnoreState()

    def focalStation(self):
        return self.FocalStation.focalStation()

    def rotCmdLimitWarningLo(self):
        name = 'rotCmd'
        severity = 'WarningLo'
        threshold = self.limitThreshold(name, severity)
        return self.limitAlarmState(name, threshold, severity)

    def rotCmdLimitCriticalLo(self):
        name = 'rotCmd'
        severity = 'CriticalLo'
        threshold = self.limitThreshold(name, severity)
        return self.limitAlarmState(name, threshold, severity)

    def rotCmdLimitWarningHi(self):
        name = 'rotCmd'
        severity = 'WarningHi'
        threshold = self.limitThreshold(name, severity)
        return self.limitAlarmState(name, threshold, severity)

    def rotCmdLimitCriticalHi(self):
        name = 'rotCmd'
        severity = 'CriticalHi'
        threshold = self.limitThreshold(name, severity)
        return self.limitAlarmState(name, threshold, severity)

    def rotLimitWarningLo(self):
        name = 'rot'
        severity = 'WarningLo'
        threshold = self.limitThreshold(name, severity)
        return self.limitAlarmState(name, threshold, severity)

    def rotLimitCriticalLo(self):
        name = 'rot'
        severity = 'CriticalLo'
        threshold = self.limitThreshold(name, severity)
        return self.limitAlarmState(name, threshold, severity)

    def rotLimitWarningHi(self):
        name = 'rot'
        severity = 'WarningHi'
        threshold = self.limitThreshold(name, severity)
        return self.limitAlarmState(name, threshold, severity)

    def rotLimitCriticalHi(self):
        name = 'rot'
        severity = 'CriticalHi'
        threshold = self.limitThreshold(name, severity)
        return self.limitAlarmState(name, threshold, severity)

    def rotAngleLimitWarningLo(self):
        return self.rotCmdLimitWarningLo() or self.rotLimitWarningLo()
    def rotAngleLimitCriticalLo(self):
        return self.rotCmdLimitCriticalLo() or self.rotLimitCriticalLo()
    def rotAngleLimitWarningHi(self):
        return self.rotCmdLimitWarningHi() or self.rotLimitWarningHi()
    def rotAngleLimitCriticalHi(self):
        return self.rotCmdLimitCriticalHi() or self.rotLimitCriticalHi()

class RotAngleLimitP_IR(RotAngleLimit):
    def __init__(self, logger = ro.nullLogger()):
        super(RotAngleLimitP_IR, self).__init__(logger)
        self.statusVar = {
            'rotCmd': {'ID': 'Melco_0036002_P_IR', 'value': None},
            'rot':    {'ID': 'Melco_0036001_P_IR', 'value': None}
            }
        self.compositeAlarms = ('RotAngleLimit_P_IR', )

class RotAngleLimitP_OPT(RotAngleLimit):
    def __init__(self, logger = ro.nullLogger()):
        super(RotAngleLimitP_OPT, self).__init__(logger)
        self.statusVar = {
            'rotCmd': {'ID': 'Melco_0036002_P_OPT', 'value': None},
            'rot':    {'ID': 'Melco_0036001_P_OPT', 'value': None}
            }
        self.compositeAlarms = ('RotAngleLimit_P_OPT', )

class RotAngleLimitNs(RotAngleLimit):
    def __init__(self, logger = ro.nullLogger()):
        super(RotAngleLimit, self).__init__(logger)
        self.statusVar = {
            'rotCmd':   {'ID': 'Melco_0004002_NS', 'value': None},
            'rot':      {'ID': 'Melco_0004001_NS', 'value': None},
            }
        self.compositeAlarms = ('RotAngleLimit_NS', )

class RotAngleLimitCs(RotAngleLimit):
    def __init__(self, logger = ro.nullLogger()):
        super(RotAngleLimit, self).__init__(logger)
        self.statusVar = {
            'rotCmd':   {'ID': 'Melco_0004002_CS', 'value': None},
            'rot':      {'ID': 'Melco_0004001_CS', 'value': None},
            }
        self.compositeAlarms = ('RotAngleLimit_CS', )

class AGProbeAngleLimit(AngleLimit):

    def update(self, svConfig, statusFromGen2):
        super(AGProbeAngleLimit, self).update(svConfig, statusFromGen2)
        self.FocalStation = svConfig.configID['FocalStation'].importedObject
        self.FocalStation.update(svConfig, statusFromGen2)
        
        # Set our alarms' Ignore state based on whether or not the
        # current focal station matches the focal station associated
        # with our alarms.
#        self.setAllIgnoreState()

    def focalStation(self):
        return self.FocalStation.focalStation()

    def agCmdLimitWarningLo(self):      
        name = 'agCmd'
        severity = 'WarningLo'
        threshold = self.limitThreshold(name, severity)
        return self.limitAlarmState(name, threshold, severity)
    def agCmdLimitCriticalLo(self):
        name = 'agCmd'
        severity = 'CriticalLo'
        threshold = self.limitThreshold(name, severity)
        return self.limitAlarmState(name, threshold, severity)
    def agCmdLimitWarningHi(self):
        name = 'agCmd'
        severity = 'WarningHi'
        threshold = self.limitThreshold(name, severity)
        return self.limitAlarmState(name, threshold, severity)
    def agCmdLimitCriticalHi(self):
        name = 'agCmd'
        severity = 'CriticalHi'
        threshold = self.limitThreshold(name, severity)
        return self.limitAlarmState(name, threshold, severity)

    def agLimitWarningLo(self):
        name = 'ag'
        severity = 'WarningLo'
        threshold = self.limitThreshold(name, severity)
        return self.limitAlarmState(name, threshold, severity)
    def agLimitCriticalLo(self):
        name = 'ag'
        severity = 'CriticalLo'
        threshold = self.limitThreshold(name, severity)
        return self.limitAlarmState(name, threshold, severity)
    def agLimitWarningHi(self):
        name = 'ag'
        severity = 'WarningHi'
        threshold = self.limitThreshold(name, severity)
        return self.limitAlarmState(name, threshold, severity)
    def agLimitCriticalHi(self):
        name = 'ag'
        severity = 'CriticalHi'
        threshold = self.limitThreshold(name, severity)
        return self.limitAlarmState(name, threshold, severity)

    def agProbeAngleLimitWarningLo(self):
        return self.agCmdLimitWarningLo() or self.agLimitWarningLo()
    def agProbeAngleLimitCriticalLo(self):
        return self.agCmdLimitCriticalLo() or self.agLimitCriticalLo()
    def agProbeAngleLimitWarningHi(self):
        return self.agCmdLimitWarningHi() or self.agLimitWarningHi()
    def agProbeAngleLimitCriticalHi(self):
        return self.agCmdLimitCriticalHi() or self.agLimitCriticalHi()

class AGProbeAngleLimitNs(AGProbeAngleLimit):
    def __init__(self, logger = ro.nullLogger()):
        super(AGProbeAngleLimitNs, self).__init__(logger)
        self.statusVar = {
            'agCmd': {'ID': 'Melco_000D004_NS', 'value': None},
            'ag':    {'ID': 'Melco_000D002_NS', 'value': None}
            }
        self.compositeAlarms = ('AGProbeAngleLimit_NS', )

class AGProbeAngleLimitCs(AGProbeAngleLimit):
    def __init__(self, logger = ro.nullLogger()):
        super(AGProbeAngleLimitCs, self).__init__(logger)
        self.statusVar = {
            'agCmd': {'ID': 'Melco_000D004_CS', 'value': None},
            'ag':    {'ID': 'Melco_000D002_CS', 'value': None}
            }
        self.compositeAlarms = ('AGProbeAngleLimit_CS', )

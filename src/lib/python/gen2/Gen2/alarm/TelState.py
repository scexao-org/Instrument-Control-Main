#!/usr/bin/env python

#
# TelState.py - methods for determining the state of the telescope
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Fri Apr 20 13:48:11 HST 2012
#]
#
# Knowledge of the following telescope states are accessible via this
# class:
# 1. If the telescope is stowed or not
# 2. If the elevation, azimuth, rotator, or "big rotation" flags are
#    set or not
# 3. If the telescope is slewing, pointing, guiding, or guiding via
#    the slit-viewer.
#

import remoteObjects as ro

class TelState(object):
    def __init__(self, logger = ro.nullLogger()):
        self.logger = logger
        self.statusVar = {
            'EL':        {'ID': 'Melco_00A11C0', 'value': None},
            'LimitFlag': {'ID': 'Melco_00A13D6', 'value': None},
            'TelDrive':  {'ID': 'TelDrive',      'value': None}
            }

        # This is the "inactive elevation angle threshold". If the
        # telescope elevation angle is greater than the threshold,
        # then the telescope is considered to be "stowed", i.e.,
        # inactive.
        self.inactiveElevationThreshold = 89.5

        # These are the bit-masks for looking at the TSCL.LIMIT_FLAG
        # value and determining which of the angle limit calculations
        # are valid.
        self.limitFlagElLowMask  = 0x01
        self.limitFlagElHighMask = 0x02
        self.limitFlagAzMask     = 0x04
        self.limitFlagRotMask    = 0x08
        self.limitFlagBigRotMask = 0x10

        # These are the strings that identify the telescope drive as
        # being in slewing or pointing or guiding.
        self.slewing =  'slewing'
        self.pointing = 'pointing'
        self.guiding =  'guiding'

        # These are the different guiding and drive modes that the
        # STATL.TELDRIVE status alias can have.
        self.telDriveModes = {
            'Guiding': ('Guiding(AG1)', 'Guiding(AG2)', 'Guiding(SV1)', 'Guiding(SV2)', 'Guiding(AGPIR)', 'Guiding(AGFMOS)'),
            'Slewing': ('Slewing'),
            'Tracking': ('Tracking', 'Tracking(Non-Sidereal)'),
            'Pointing': ('Pointing')
            }

    def update(self, svConfig, statusFromGen2):
        # Update our statusVar dictionary based on the status values
        # received from Gen2.
        for key in self.statusVar:
            ID = self.statusVar[key]['ID']
            svConfigItem = svConfig.configID[ID]
            if svConfigItem.Gen2Alias in statusFromGen2:
                self.statusVar[key]['value'] = svConfigItem.MelcoValue(statusFromGen2[svConfigItem.Gen2Alias])

    def elStowed(self):
        return self.statusVar['EL']['value'] >= self.inactiveElevationThreshold

    def limitFlagElLow(self):
        return self.statusVar['LimitFlag']['value'] & self.limitFlagElLowMask

    def limitFlagElHigh(self):
        return self.statusVar['LimitFlag']['value'] & self.limitFlagElHighMask

    def limitFlagAz(self):
        return self.statusVar['LimitFlag']['value'] & self.limitFlagAzMask

    def limitFlagRot(self):
        return self.statusVar['LimitFlag']['value'] & self.limitFlagRotMask

    def limitFlagBigRot(self):
        return self.statusVar['LimitFlag']['value'] & self.limitFlagBigRotMask

    def getLimitFlag(self, name):
        if name == 'limitFlagElLow':
            return self.limitFlagElLow()
        elif name == 'limitFlagElHigh':
            return self.limitFlagElHigh()
        elif name == 'limitFlagAz':
            return self.limitFlagAz()
        elif name == 'limitFlagRot':
            return self.limitFlagRot()
        elif name == 'limitFlagBigRot':
            return self.limitFlagBigRot()

    def isSlewing(self):
        return self.slewing in self.statusVar['TelDrive']['value'].lower()

    def isPointing(self):
        return self.pointing in self.statusVar['TelDrive']['value'].lower()

    def isGuiding(self):
        return self.guiding in self.statusVar['TelDrive']['value'].lower()

    def isGuidingSV(self):
        return self.isGuiding() and 'sv' in self.statusVar['TelDrive']['value'].lower()

    def telDrive(self):
        return self.statusVar['TelDrive']['value']

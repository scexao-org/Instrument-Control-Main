#!/usr/bin/env python

# GuideStar.py - methods for determining if the guide star has been
#                lost
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Thu Jun 21 12:32:20 HST 2012
#]
#
# GuideStar.py supplies methods to check the the guide signal
# intensity to determine if any of the following alarm conditions
# exist:
# 1. Guide star lost
#

import remoteObjects as ro
import Derived

class GuideStar(Derived.Derived):
    def __init__(self, logger = ro.nullLogger()):
        super(GuideStar, self).__init__(logger)

        # These status variables are defined in the alarm
        # configuration file. Each one of these status variables is
        # related to a single MELCO value supplied to Gen2 via the TSC
        # status packets.
        self.statusVar = {
            'PIR AG for SH Star Detect Start':   {'ID': 'Melco_003B004', 'value': None},
            'PIR Fibre AG Star Detect Start':    {'ID': 'Melco_003B020', 'value': None},
            'HSC AG for SC Star Detect Start':   {'ID': 'Melco_003D013', 'value': None},
            'HSC AG for SH Star Detect Start':   {'ID': 'Melco_003E013', 'value': None},
            'PIR AG for SH Star Posn Intensity': {'ID': 'Melco_003B01A', 'value': None},
            'PIR Fibre AG Star Posn Intensity':  {'ID': 'Melco_003B038', 'value': None},
            'HSC AG for SC Star Posn Intensity': {'ID': 'Melco_003D01D', 'value': None},
            'HSC AG for SH Star Posn Intensity': {'ID': 'Melco_003E01C', 'value': None},
            'AG Star Position1 Intensity on AG': {'ID': 'Melco_0006028', 'value': None},
            'SV Star Position1 Intensity on SV': {'ID': 'Melco_0007128', 'value': None},
           }

        # We will store a TelState object here. We need this because
        # TelState tells us if we are guiding or not and if we are
        # guiding via the SV or the regular AG.
        self.telState = None

        # We will store a FocalStation object here. We need this
        # because the alarm depends on knowing the focal station
        # value. The focal station determines which status variable
        # contains the guide star intensity.
        self.focalStation = None

    # Update our status variable values based on the current status as
    # supplied to us via the Gen2 status aliases.
    def update(self, svConfig, statusFromGen2):
        super(GuideStar, self).update(svConfig, statusFromGen2)

        # Get references to the TelState and FocalStation objects.
        if self.telState == None:
            self.telState = svConfig.configID['TelState'].importedObject
        if self.focalStation == None:
            self.focalStation = svConfig.configID['FocalStation'].importedObject

        # Update the telescope state and focal station status
        # variables.
        self.telState.update(svConfig, statusFromGen2)
        self.focalStation.update(svConfig, statusFromGen2)

        # Initially, ignore all of the individual alarms
        self.setIndIgnoreState(True)
        # Then, if we are guiding, enable only the alarm corresponding
        # to the current guiding mode.
        starDetect = False
        if self.telState.isGuiding():
            starDetect = True
            if self.telState.isGuidingSV():
                name = 'SV Star Position1 Intensity on SV'
            else:
                if self.focalStation.focalStation() == 'P_IR':
                    if self.statusVar['PIR AG for SH Star Detect Start']['value']:
                        name = 'PIR AG for SH Star Posn Intensity'
                    elif self.statusVar['PIR Fibre AG Star Detect Start']['value']:
                        name = 'PIR Fibre AG Star Posn Intensity'
                    else:
                        starDetect = False
                elif self.focalStation.focalStation() == 'P_OPT2':
                    if self.statusVar['HSC AG for SC Star Detect Start']['value']:
                        name = 'HSC AG for SC Star Posn Intensity'
                    elif self.statusVar['HSC AG for SH Star Detect Start']['value']:
                        name = 'HSC AG for SH Star Posn Intensity'
                    else:
                        starDetect = False
                else:
                    name = 'AG Star Position1 Intensity on AG'
            if starDetect:
                self.setIndIgnoreState(False, name)

    # guideStarLost returns True if the guide star intensity is below
    # the threshold value. Otherwise, it returns False. False is also
    # returned if we are not guiding, as reported by the telState
    # object.
    def guideStarLost(self):
        # Determine if we are guiding.
        starDetect = False
        if self.telState.isGuiding():
            starDetect = True
            # Determine if we are guiding via the SV or the regular AG.
            if self.telState.isGuidingSV():
                name = 'SV Star Position1 Intensity on SV'
            else:
                # If the focal station is P, location of guiding
                # intensity value depends on whether focal station is
                # P_IR or P_OPT.
                if self.focalStation.focalStation() == 'P_IR':
                    if self.statusVar['PIR AG for SH Star Detect Start']['value']:
                        name = 'PIR AG for SH Star Posn Intensity'
                    elif self.statusVar['PIR Fibre AG Star Detect Start']['value']:
                        name = 'PIR Fibre AG Star Posn Intensity'
                    else:
                        starDetect = False
                elif self.focalStation.focalStation() == 'P_OPT2':
                    if self.statusVar['HSC AG for SC Star Detect Start']['value']:
                        name = 'HSC AG for SC Star Posn Intensity'
                    elif self.statusVar['HSC AG for SH Star Detect Start']['value']:
                        name = 'HSC AG for SH Star Posn Intensity'
                    else:
                        starDetect = False
                else:
                    name = 'AG Star Position1 Intensity on AG'
            # Get the intenisity value from our status variable data
            # structure and compare it to the threshold. If the
            # intensity is below the threshold, return True to trigger
            # an alarm condition. Otherwide, False will be returned.
            if starDetect:
                intensity = self.statusVar[name]['value']
                svConfigItem = self.svConfig.configID[self.statusVar[name]['ID']]
                threshold = svConfigItem.Alarm['CriticalLo'].Threshold
                return intensity < threshold
            else:
                # No star detected, so no intensity, so return False
                return False
        else:
            # Not guiding, so return False.
            return False

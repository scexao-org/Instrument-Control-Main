#!/usr/bin/env python

# Windspeed.py - methods for determining if the windspeed exceeds the
#                specified threshold
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Fri Feb 22 09:17:25 HST 2013
#]
#
# Windspeed.py supplies methods to check the following environmental
# conditions for alarm states:
#
# 1. Top ring wind speed
# 2. Center section (i.e., elevation bearing) wind speed
#
# The update method in the Windspeed class modifies the alarms
# attributes in svConfig so as to mute the alarm's audio announcements
# if the telescope is pointing or slewing. Note that an alarm
# condition will still be recorded if the telescope is pointing or
# slewing and a quantity exceeds the threshold, but the alarm will not
# be announced.

import remoteObjects as ro
import Derived
import SOSS.status.common as common

class Windspeed(Derived.Derived):
    def __init__(self, logger = ro.nullLogger()):
        super(Windspeed, self).__init__(logger)

        # These status variables are defined in the alarm
        # configuration file.
        self.statusVar = {
            'topRingRear':   {'ID': 'Melco_002C174', 'value': common.STATNONE},
            'topRingFront':  {'ID': 'Melco_002C180', 'value': common.STATNONE},
            'csctFrontX':    {'ID': 'Melco_002C1A4', 'value': common.STATNONE},
            'csctFrontY':    {'ID': 'Melco_002C1B0', 'value': common.STATNONE},
            'csctFrontZ':    {'ID': 'Melco_002C1BC', 'value': common.STATNONE},
            'csctRearX':     {'ID': 'Melco_002C1C8', 'value': common.STATNONE},
            'csctRearY':     {'ID': 'Melco_002C1D4', 'value': common.STATNONE},
            'csctRearZ':     {'ID': 'Melco_002C1E0', 'value': common.STATNONE},
            }

        self.compositeAlarms = ('HighWindspeedTopRing', 'HighWindspeedCSCT')

        # We will store a TelState object here. We need this because
        # TelState tells us if we are pointing or slewing.
        self.telState = None

    # Update our status variable values based on the current status as
    # supplied to us via the Gen2 status aliases.
    def update(self, svConfig, statusFromGen2):
        super(Windspeed, self).update(svConfig, statusFromGen2)

        # Get a reference to the TelState object.
        if self.telState == None:
            self.telState = svConfig.configID['TelState'].importedObject

        # Update the telescope state status so that we can determine
        # if we need to mute the alarms due to the telescope being in
        # the slewing or pointing state.
        self.telState.update(svConfig, statusFromGen2)

        # If the telescope is slewing or pointing, mute the audio
        # announcements.
        self.setAllMuteState(self.telState.isPointing() or self.telState.isSlewing())

    # warnWindspeed is used to raise an alarm if any of the subsidiary
    # status items are in an alarm state.
    def warnWindspeed(self, names):
        isAlarm = False
        for name in names:
            svConfigItem = self.svConfig.configID[self.statusVar[name]['ID']]
            #print 'name',name
            #print 'alarmState',svConfigItem.alarmState(self.statusVar[name]['value'])
            if 'Warning' in svConfigItem.alarmState(self.statusVar[name]['value']):
                isAlarm = True
        return isAlarm

    def warnWindspeedTopRing(self):
        # The top ring windspeed warning depends on the alarm state of
        # the two top ring windspeed sensors.
        return self.warnWindspeed(('topRingRear', 'topRingFront'))

    def warnWindspeedCenterSection(self):
        # The center section windspeed warning depends on the alarm
        # state of the six center section windspeed sensors.
        return self.warnWindspeed(('csctFrontX', 'csctFrontY', 'csctFrontZ', 'csctRearX', 'csctRearY', 'csctRearZ'))

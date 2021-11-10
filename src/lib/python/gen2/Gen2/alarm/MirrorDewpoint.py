#!/usr/bin/env python

# MirrorDewpoint.py - methods for determining if the outside dewpoint
#                     temperature is close to the mirror temperature
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Tue Feb 12 13:24:37 HST 2013
#]
#
# MirrorDewpoint.py supplies methods to check the following environmental
# conditions for alarm states:
#
# 1. outside dewpoint is close to mirror temperature
#
# The threshold value is contained in this module.
#
# The update method in the MirrorDewpoint class modifies the alarms
# attributes in svConfig so as to mute the alarm's audio announcements
# if the dome is in a "closed" state, i.e., both the IR and Optical
# shutters are closed. Note that an alarm condition will still be
# recorded if the dome is closed and a quantity exceeds the threshold,
# but the alarm will not be announced.

import remoteObjects as ro
import Derived
import SOSS.status.common as common

class MirrorDewpoint(Derived.Derived):
    def __init__(self, logger = ro.nullLogger()):
        super(MirrorDewpoint, self).__init__(logger)

        # These status variables are defined in the alarm
        # configuration file. The mirror temperature is related to a
        # single MELCO value supplied to Gen2 via the TSC status
        # packets. The external dewpoint is a Gen2 derived quantity,
        # based on the external temperature and humidity.
        self.statusVar = {
            'mirrorTemp':   {'ID': 'Melco_00A1171', 'value': None},
            'extDewpoint':  {'ID': 'ExternalDewpoint', 'value': None},
            }

        # This "composite" alarm is defined in the alarm
        # configuration file.
        self.compositeAlarms = ('MirrorDewpoint',)

        # Threshold temperature to trigger warning alarm - if dewpoint
        # is within 2 deg C of mirror temperature, raise a warning
        # alarm.
        self.warnThreshold = 2.0

    # Update our status variable values based on the current status as
    # supplied to us via the Gen2 status aliases.
    def update(self, svConfig, statusFromGen2):
        super(MirrorDewpoint, self).update(svConfig, statusFromGen2)

        # Update the dome shutter status so that we can determine if
        # we need to mute the alarms due to the dome being closed.
        domeShutter = svConfig.configID['DomeShutter'].importedObject
        domeShutter.update(svConfig, statusFromGen2)

        # If the dome shutter is closed, modify the status variable
        # configuration to mute all of the audio announcements. If the
        # shutter is open, un-mute the audio.
        closed = domeShutter.shutterClosed()
        self.setAllMuteState(closed)

    # warnTemperature is used to raise an alarm if the dewpoint
    # temperature is within the threshold value of the mirror
    # temperature.
    def warnTemperature(self):
        # First, make sure that both the dewpoint and mirror
        # temperatures are valid values. If either is ##NODATA## or
        # ##ERROR##, return False.
        try:
            common.assertValidStatusValue('STATL.DEW_POINT_O', self.extDewpoint())
            common.assertValidStatusValue('TSCL.M1_TEMP', self.mirrorTemp())
        except common.statusError:
            return False
        # Return True if the dewpoint temperature is within the
        # threshold value of the mirror temperature. Otherwise, return
        # False.
        if self.extDewpoint() >= self.mirrorTemp() - self.warnThreshold:
            return True
        else:
            return False

    # Return the current value of the mirror temperature
    def mirrorTemp(self):
        return self.statusVar['mirrorTemp']['value']

    # Return the current value of the external dewpoint temperature
    def extDewpoint(self):
        return self.statusVar['extDewpoint']['value']

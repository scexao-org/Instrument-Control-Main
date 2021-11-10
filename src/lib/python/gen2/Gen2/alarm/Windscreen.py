#!/usr/bin/env python

#
# Windscreen.py - methods for determining if the windscreen
#                 settings/position are in an alarm state
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Fri May  4 12:22:40 HST 2012
#]
#
# Windscreen.py supplies methods to check the following windscreen
# conditions for alarm states:
#
# 1. Windscreen drive off and position "high"
# 2. Windscreen mode "free" (i.e., not synched to telescope elevation)
#    and drive on
# 3. Windscreen drive on and synched to telescope elevation, but
#    command and actual position values differ by more than threshold
#

import remoteObjects as ro
import Derived

class Windscreen(Derived.Derived):
    def __init__(self, logger = ro.nullLogger()):
        super(Windscreen, self).__init__(logger)

        # These status variables are defined in the alarm
        # configuration file. Each one of these status variables is
        # related to a single MELCO value supplied to Gen2 via the TSC
        # status packets.
        self.statusVar = {'driveOn':   {'ID': 'Melco_0030046', 'value': None},
                          'driveOff':  {'ID': 'Melco_0030047', 'value': None},
                          'cmdPos':    {'ID': 'Melco_00A1349', 'value': None},
                          'realPos':   {'ID': 'Melco_0030001', 'value': None},
                          'syncMode':  {'ID': 'Melco_00A1167', 'value': None},
                          'aSyncMode': {'ID': 'Melco_00A1168', 'value': None}}
        self.compositeAlarms = ('WSDriveOffPosHigh', 'WSModeFreeDriveOn', 'WSObstruct')

        # This is the windscreen "high position" threshold. When the
        # drive is off and the reported position is greater than
        # highPosThreshold, an alarm status will be returned from the
        # driveOffAndPosHigh method.
        self.highPosThreshold = 5.0

        # This is the threshold for determining whether the windscreen
        # may obstruct the telescope. When the drives are on and the
        # windscreen and telescope elevation are synched, if the
        # commanded windscreen position differs from the actual
        # position by more than the threshold, an alarm status will be
        # returned.
        self.obstructThreshold = 1.0

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
        super(Windscreen, self).update(svConfig, statusFromGen2)

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

        # Mute all alarms if the telescope is "inactive", i.e., if the
        # mirror covers are closed or the dome shutter is closed or
        # the telescope is in the stowed position. Furthermore, mute
        # all alarms if the telescope is slewing. Otherwise, un-mute
        # the alarms.
        if self.mirrorCover.m1Closed() or \
               self.domeShutter.shutterClosed() or \
               self.telState.elStowed() or \
               self.telState.isSlewing():
            self.setAllMuteState(True)
        else:
            self.setAllMuteState(False)

    # driveOffAndPosHigh implements the "Windscreen drives
    # off/position high" alarm. Returns True if the windscreen drive
    # is off and the actual windscreen position is greater than the
    # threshold value. Otherwise, return False.
    def driveOffAndPosHigh(self):
        if (self.driveOff() == 1) and (self.realPos() > self.highPosThreshold):
            return True
        else:
            return False

    # modeFreeAndDriveOn implements the "Windscreen mode free/drives
    # on" alarm. Returns True if the windscreen mode is "free" (i.e.,
    # not synched to telescope elevation) and the windscreen drives
    # are on. Otherwise, return False.
    def modeFreeAndDriveOn(self):
        if (self.driveOn() == 1) and (self.aSyncMode() == 1):
            return True
        else:
            return False

    # obstructWarn implements the "Windscreen may obstruct telescope"
    # warning alarm. Returns True if the windscreen drives are on and
    # the windscreen is synched to the telescope elevation but the
    # command and actual windscreen position values differ by more
    # than the threshold. Otherwise, return False.
    def obstructWarn(self):
        if (self.driveOn() == 1) and (self.syncMode() == 1):
            if self.cmdPos() - self.realPos() > self.obstructThreshold:
                return True
            else:
                return False
        else:
            return False

    # obstructCrit implements the "Windscreen may obstruct telescope"
    # critical alarm. Returns True if the windscreen drives are on and
    # the windscreen is synched to the telescope elevation but the
    # command and actual windscreen position values differ by more
    # than the threshold. Otherwise, return False.
    def obstructCrit(self):
        if (self.driveOn() == 1) and (self.syncMode() == 1):
            if self.cmdPos() - self.realPos() < -self.obstructThreshold:
                return True
            else:
                return False
        else:
            return False

    # Return the current value of the driveOff flag
    def driveOff(self):
        return self.statusVar['driveOff']['value']

    # Return the current value of the driveOn flag
    def driveOn(self):
        return self.statusVar['driveOn']['value']

    # Return the current value of the commanded windscreen position
    def cmdPos(self):
        return self.statusVar['cmdPos']['value']

    # Return the current value of the actual windscreen position
    def realPos(self):
        return self.statusVar['realPos']['value']

    # Return the current value of the synch flag
    def syncMode(self):
        return self.statusVar['syncMode']['value']

    # Return the current value of the asynch flag
    def aSyncMode(self):
        return self.statusVar['aSyncMode']['value']


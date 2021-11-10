#!/usr/bin/env python

#
# PACmd.py - methods for determining if there is a large difference
#            between the rotator commanded and actual position
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Tue Jun 26 10:13:10 HST 2012
#]
#
# PACmd.py supplies methods to check the rotator for the following
# alarm states:
#
# 1. The difference between the commanded and actual position angle
#    exceeds the threshold value
#
# Note that the above alarm takes into account the time required for
# the hardware to start moving and catch-up to the commanded angle.
#
# The alarm is set to the "ignore" state if any of the following are true:
# 1. Mirror covers are closed
# 2. Dome shutter is closed
# 3. Telescope is stowed
# 4. Rotator is "out"
# 5. Telescope is slewing
#
# PACmd is the base class. Also in this file are PACmdPF and
# PACmdNsCs, which implement the alarms for their respective focal
# station rotators.
#

import time
import remoteObjects as ro
import Derived

class PACmd(Derived.Derived):
    def __init__(self, logger = ro.nullLogger()):
        super(PACmd, self).__init__(logger)

        self.errorThreshold = 0.1 # degree
        self.delaySecondsPerDegree = 0.6667 # seconds/degree
        self.paCmdStartTime = None
        self.paDelayIntervalMin = 6.0 # seconds
        self.paDelayInterval = None

        self.svConfig = None
        self.domeShutter = None
        self.mirrorCover = None
        self.telState = None
        self.focalStation = None

    def update(self, svConfig, statusFromGen2):
        super(PACmd, self).update(svConfig, statusFromGen2)
        
        if self.domeShutter == None:
            self.domeShutter = svConfig.configID['DomeShutter'].importedObject
        if self.mirrorCover == None:
            self.mirrorCover = svConfig.configID['MirrorCover'].importedObject
        if self.telState == None:
            self.telState = svConfig.configID['TelState'].importedObject
        if self.focalStation == None:
            self.focalStation = svConfig.configID['FocalStation'].importedObject

        # Update the dome shutter, mirror cover, and telescope state
        # status variables.
        self.domeShutter.update(svConfig, statusFromGen2)
        self.mirrorCover.update(svConfig, statusFromGen2)
        self.telState.update(svConfig, statusFromGen2)
        self.focalStation.update(svConfig, statusFromGen2)

    def getIgnoreState(self):
        # Ignore alarms if mirror covers are closed or dome shutter is
        # closed, etc.
        if self.mirrorCover.m1Closed() or \
                self.domeShutter.shutterClosed() or \
                self.telState.elStowed() or \
                self.focalStation.rotIsOut() or \
                self.telState.isSlewing():
            return True
        else:
            return False

    def setPACmdIgnoreState(self):
        # Set the "Ignore" state based on whether or not mirror covers
        # are closed or dome shutter is closed, telescope is slewing,
        # etc.
        if self.getIgnoreState():
            self.setAllIgnoreState(True)
            # If we are ignoring the alarms, also set paCmdStartTime
            # to None. This means that, when the "ignore alarm" state
            # completes, we re-calculate paCmdStartTime instead of
            # using a value that might have been calculated before the
            # "ignore alarm" period started.
            self.paCmdStartTime = None
        else:
            # If we aren't ignoring the alarms, check the
            # command-actual position difference.
            self.checkCmdPosDiff()

    def checkCmdPosDiff(self):
        paCmdDiff = self.paCmdDiff()
        if paCmdDiff >= self.errorThreshold:
            if self.paCmdStartTime == None:
                self.paCmdStartTime = time.time()
                self.paStartupInterval = self.paDelayIntervalMin + self.delaySecondsPerDegree * paCmdDiff
        else:
            self.paCmdStartTime = None

    def paCmdWarning(self):
        if self.paCmdStartTime == None:
            return False
        else:
            return (time.time() - self.paCmdStartTime) > self.paStartupInterval

    def paCmdDiff(self):
        return abs(self.rotCmd() - self.rotPos())

    def focalStation(self):
        self.focalStation = self.svConfig.configID['FocalStation'].importedObject
        return focalStation.focalStation()

    def rotCmd(self):
        return self.statusVar['rotCmd']['value']

    def rotPos(self):
        return self.statusVar['rot']['value']

class PACmdPF(PACmd):
    def __init__(self, logger = ro.nullLogger()):
        super(PACmdPF, self).__init__(logger)
        self.statusVar = {
            'rotCmd': {'ID': 'Melco_0036002_P_IR', 'value': None},
            'rot':    {'ID': 'Melco_0036001_P_IR', 'value': None}
            }
        self.compositeAlarms = ('PA_Cmd_Timeout_PF', )

    def update(self, svConfig, statusFromGen2):
        super(PACmdPF, self).update(svConfig, statusFromGen2)
       
        # This class is for the prime-focus rotator. Enable alarms if
        # focal station is prime-focus. Otherwise, ignore alarms.
        if self.focalStation.focalStationIsPrimeFocus():
            self.setAllIgnoreState(False)
        else:
            self.setAllIgnoreState(True)

        # Set the "Ignore" state based on whether or not mirror covers
        # are closed or dome shutter is closed, telescope is slewing,
        # etc.
        self.setPACmdIgnoreState()

class PACmdNs(PACmd):
    def __init__(self, logger = ro.nullLogger()):
        super(PACmdNs, self).__init__(logger)
        self.statusVar = {
            'rotCmd':   {'ID': 'Melco_0004002_PACmd', 'value': None},
            'rot':      {'ID': 'Melco_0004001_PACmd', 'value': None}
            }
        self.compositeAlarms = ('PA_Cmd_Timeout_NS', )

    def update(self, svConfig, statusFromGen2):
        super(PACmdNs, self).update(svConfig, statusFromGen2)

        # This class is for the Ns rotators. Enable alarms if focal
        # station is Nasmyth. Otherwise, ignore alarms.
        if self.focalStation.focalStationIsNasmyth():
            self.setAllIgnoreState(False)
        else:
            self.setAllIgnoreState(True)

        # Set the "Ignore" state based on whether or not mirror covers
        # are closed or dome shutter is closed, telescope is slewing,
        # etc.
        self.setPACmdIgnoreState()

class PACmdCs(PACmd):
    def __init__(self, logger = ro.nullLogger()):
        super(PACmdCs, self).__init__(logger)
        self.statusVar = {
            'rotCmd':   {'ID': 'Melco_0004002_PACmd', 'value': None},
            'rot':      {'ID': 'Melco_0004001_PACmd', 'value': None}
            }
        self.compositeAlarms = ('PA_Cmd_Timeout_CS', )

    def update(self, svConfig, statusFromGen2):
        super(PACmdCs, self).update(svConfig, statusFromGen2)

        # This class is for the Cs rotator. Enable alarms if focal
        # station is Cassegrain. Otherwise, ignore alarms.
        if self.focalStation.focalStationIsCassegrain():
            self.setAllIgnoreState(False)
        else:
            self.setAllIgnoreState(True)

        # Set the "Ignore" state based on whether or not mirror covers
        # are closed or dome shutter is closed, telescope is slewing,
        # etc.
        self.setPACmdIgnoreState()

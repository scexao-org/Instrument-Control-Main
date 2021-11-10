#!/usr/bin/env python

#
# TipTilt.py - methods for determining if the tip-tilt drive is in an
#              alarm state
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Mon Apr 23 13:28:27 HST 2012
#]
#
# TipTilt.py supplies methods to check the following tip-tilt
# conditions for alarm states:
#
# 1. the tip-tilt drive was turned off, after having been on
#

import remoteObjects as ro
import Derived

class TipTilt(Derived.Derived):
    def __init__(self, logger = ro.nullLogger()):
        super(TipTilt, self).__init__(logger)

        # These status variables are defined in the alarm
        # configuration file. Each one of these status variables is
        # related to a single MELCO value supplied to Gen2 via the TSC
        # status packets.
        self.statusVar = {
            'tipTiltChopping':         {'ID': 'Melco_002800B', 'value': None},
            'tipTiltTipTilt':          {'ID': 'Melco_002800C', 'value': None},
            'tipTiltPosition':         {'ID': 'Melco_0028029', 'value': None},
            'tipTiltMaint':            {'ID': 'Melco_002800D', 'value': None},
            'tipTiltDriveOn':          {'ID': 'Melco_0028007', 'value': None},
            'tipTiltDriveOff':         {'ID': 'Melco_0028008', 'value': None},
            'tipTiltDriveOnRdy':       {'ID': 'Melco_002802A', 'value': None},
            'choppingStart':           {'ID': 'Melco_0028066', 'value': None},
            'choppingStop':            {'ID': 'Melco_0028067', 'value': None},
            'tipTiltChoppingStartRdy': {'ID': 'Melco_0028026', 'value': None},
            'tipTiltDataAvailable':    {'ID': 'Melco_0028045', 'value': None}
            }

        # We need these attributes to determine if the tip-tilt state
        # has changed from the previous time.
        self.previousTipTiltAndDriveState = None
        self.currentTipTiltAndDriveState = None
        self.savedAlarmState = None

        # We will store a FocalStation object here. We need this
        # because the alarm depends on knowing if the M2 value is
        # "IR".
        self.focalStation = None

    def update(self, svConfig, statusFromGen2):
        super(TipTilt, self).update(svConfig, statusFromGen2)

        # Get the FocalStation object from the status variable data
        # structure and update the FocalStation attributes with the
        # current values supplied by the status process.
        if self.focalStation == None:
            self.focalStation = svConfig.configID['FocalStation'].importedObject
        self.focalStation.update(svConfig, statusFromGen2)

        # Save the currentTipTiltAndDriveState for use the next time around
        self.previousTipTiltAndDriveState = self.currentTipTiltAndDriveState
        # Compute the current tip-tilt/drive state and save it.
        self.currentTipTiltAndDriveState = self.tipTiltState() and self.tipTiltDriveOn()

    # warnTipTiltDriveOff returns True if the tip-tilt state changes
    # from False to True or if the saved alarm state is
    # True. Otherwise, it returns False.
    def warnTipTiltDriveOff(self):
        if self.tipTiltState():
            # If tipTiltState is True, we need to check the
            # currentTipTiltAndDriveState. If that is True, that means
            # the drive is on, so there is no alarm. Set the alarm
            # state to False.
            if self.currentTipTiltAndDriveState:
                self.savedAlarmState = False
            elif self.savedAlarmState or ((not self.currentTipTiltAndDriveState) and self.previousTipTiltAndDriveState):
                # The tip-tilt state is True and the drive state has
                # changed from on to off, so set the alarm state to
                # True.
                self.savedAlarmState = True
        else:
            # If tipTiltState is False, set alarm state to False
            self.savedAlarmState = False

        return self.savedAlarmState

    # Compute the current tip-tilt state. The tip-tilt state is True
    # if all of the following are True:
    # 1. The current focal station M2 value is IR
    # 2. Either the Tip-Tilt Chopping, Tip-Tilt, or Position mode flag
    # is set. The other Tip-Tilt mode is MAINT.
    # 3. The tipTiltChopStatus value is True
    # 3. The tipTiltDataAvailableStatus value is True
    #
    # Note that the tipTiltState is independent of the drive state.
    def tipTiltState(self):
        return self.focalStation.m2IsIR() and \
            (self.tipTiltChopping() or self.tipTiltTipTilt() or self.tipTiltPosition()) and \
            self.tipTiltChopStatus() and \
            self.tipTiltDataAvailableStatus()

    # Return the current value of the Tip-Tilt Chopping Mode flag
    def tipTiltChopping(self):
        return self.statusVar['tipTiltChopping']['value']

    # Return the current value of the Tip-Tilt Tip-Tilt Mode flag
    def tipTiltTipTilt(self):
        return self.statusVar['tipTiltTipTilt']['value']

    # Return the current value of the Tip-Tilt Position Mode flag
    def tipTiltPosition(self):
        return self.statusVar['tipTiltPosition']['value']

    # Return the current value of the Tip-Tilt MAINT Mode flag
    def tipTiltMaint(self):
        return self.statusVar['tipTiltChopping']['value']

    # Return the current value of the Tip-Tilt Drive On flag
    def tipTiltDriveOn(self):
        return self.statusVar['tipTiltDriveOn']['value']

    # Return the current value of the Tip-Tilt Drive Off flag
    def tipTiltDriveOff(self):
        return self.statusVar['tipTiltDriveOff']['value']

    # Return the current value of the Tip-Tilt Drive On RDY flag
    def tipTiltDriveOnRdy(self):
        return self.statusVar['tipTiltDriveOnRdy']['value']

    # Return the current value of the Chopping Start flag
    def choppingStart(self):
        return self.statusVar['choppingStart']['value']

    # Return the current value of the Chopping Stop flag
    def choppingStop(self):
        return self.statusVar['choppingStop']['value']

    # Return the current value of the Chopping StartReady flag
    def tipTiltChoppingStartRdy(self):
        return self.statusVar['tipTiltChoppingStartRdy']['value']

    # Return the current value of the Data Available flag
    def tipTiltDataAvailable(self):
        return self.statusVar['tipTiltDataAvailable']['value']

    # Return True if chopping flags have values, i.e. not ##NODATA##
    def tipTiltChopStatus(self):
        return (self.choppingStart() == 1 or self.choppingStart() == 0) and \
            (self.choppingStop() == 1 or self.choppingStop() == 0) and \
            (self.tipTiltChoppingStartRdy() == 1 or self.tipTiltChoppingStartRdy() == 0)

    # Return True if data available flag has a value, i.e. not ##NODATA##
    def tipTiltDataAvailableStatus(self):
        return (self.tipTiltDataAvailable() == 1 or self.tipTiltDataAvailable() == 0)

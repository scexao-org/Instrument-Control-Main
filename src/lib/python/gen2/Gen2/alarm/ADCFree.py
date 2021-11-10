#!/usr/bin/env python

#
# ADCFree.py - methods for determining if any of the ADC drive/synch
#              conditions are in an alarm state
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Mon Apr 23 13:17:56 HST 2012
#]
#
# ADCFree.py supplies methods to check the following ADC conditions
# for alarm states:
#
# 1. ADC is "in" and the drive is off or the drive is on and the ADC
#    is in "asynch" mode.
#
# Note that the drive and synch status variables depend on the current
# focal station. The base class is ADCFree and all of the classes in
# this module inherit from that class. This module supplies the
# ADCFreePF class for the prime focus ADCFreeNs for the Nasmyth focus,
# and ADCFreeCs for the Cassegrain focus. Each class uses the status
# variables appropriate for the respective focal station.
#

import remoteObjects as ro
import Derived

class ADCFree(Derived.Derived):
    def __init__(self, logger = ro.nullLogger()):
        super(ADCFree, self).__init__(logger)
        
        # These status variables are defined in the alarm
        # configuration file. Each one of these status variables is
        # related to a single MELCO value supplied to Gen2 via the TSC
        # status packets. The ADC In/Out status variables do not
        # depend on the focal station.
        self.statusVar = {
            'ADC_In':   {'ID': 'Melco_0004122', 'value': None},
            'ADC_Out':  {'ID': 'Melco_0004123', 'value': None}
            }

        # Note that the base class doesn't have any composite alarms,
        # but the sub-classes do.

        # We will store DomeShutter, MirrorCover, TelState, and
        # FocalStation objects here. We need these because we want to
        # ignore the "ADC Free" alarms when the dome is closed and
        # telescope is "inactive". We need the FocalStation object
        # because the drive and synch status variables depend on the
        # focal station.
        self.domeShutter = None
        self.mirrorCover = None
        self.telState = None
        self.focalStation = None

    def update(self, svConfig, statusFromGen2):
        super(ADCFree, self).update(svConfig, statusFromGen2)

        # Get references to the DomeShutter, MirrorCover, TelState,
        # and FocalStation objects.
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

    # Ignore alarms if mirror covers are closed or dome shutter is
    # closed, or the telescope is stowed or slewing.
    def setIgnoreWhenClosed(self):
        if self.mirrorCover.m1Closed() or \
                self.domeShutter.shutterClosed() or \
                self.telState.elStowed() or \
                self.telState.isSlewing():
            self.setAllIgnoreState(True)

    # focalStation returns the current focal station as a string
    def focalStation(self):
        if self.focalStation == None:
            self.focalStation = self.svConfig.configID['FocalStation'].importedObject
        return focalStation.focalStation()

    # adcFree implements the "ADC in free mode" alarm. It first checks
    # to see if the ADC is "In". If so, it checks to see if either:
    # the drive is off or the drive is on and the ADC is not in
    # synchronous mode. If so, returns True. If the ADC is not "In" or
    # the drive is on and in synchronous mode, returns False.
    def adcFree(self):
        if self.adcIn() and \
                (not self.driveOn() and self.driveOff()) or \
                ((self.driveOn() and not self.driveOff()) and \
                     self.aSyncMode() and not self.syncMode()):
            return True
        else:
            return False

    # Return the current value of the ADC_In flag
    def adcIn(self):
        return self.statusVar['ADC_In']['value']

    # Return the current value of the ADC_Out flag
    def adcOut(self):
        return self.statusVar['ADC_Out']['value']

    # Return the current value of the ADC_DriveOn flag
    def driveOn(self):
        return self.statusVar['ADC_DriveOn']['value']

    # Return the current value of the ADC_DriveOff flag
    def driveOff(self):
        return self.statusVar['ADC_DriveOff']['value']

    # Return the current value of the ADC_SyncMode flag
    def syncMode(self):
        return self.statusVar['ADC_SyncMode']['value']

    # Return the current value of the ADC_aSyncMode flag
    def aSyncMode(self):
        return self.statusVar['ADC_aSyncMode']['value']

class ADCFreePF(ADCFree):
    # ADCFreePF is a subclass of ADCFree, specifically for the
    # prime-focus ADC.
    def __init__(self):
        super(ADCFreePF, self).__init__()
        # These status variables are defined in the alarm
        # configuration file. Each one of these status variables is
        # related to a single MELCO value supplied to Gen2 via the TSC
        # status packets.
        self.statusVar['ADC_DriveOn']   = {'ID': 'Melco_003610B', 'value': None}
        self.statusVar['ADC_DriveOff']  = {'ID': 'Melco_003610C', 'value': None}
        self.statusVar['ADC_SyncMode']  = {'ID': 'Melco_00A1244', 'value': None}
        self.statusVar['ADC_aSyncMode'] = {'ID': 'Melco_00A1245', 'value': None}

        # This is the status variable for the prime-focus "ADC in free
        # mode" alarm.
        self.compositeAlarms = ('PrimeADCFreeMode', )
        
    # Update our status variable values based on the current status as
    # supplied to us via the Gen2 status aliases.
    def update(self, svConfig, statusFromGen2):
        super(ADCFreePF, self).update(svConfig, statusFromGen2)
       
        # This class is for the prime-focus ADC. Enable alarms if
        # focal station is prime-focus. Otherwise, ignore alarms.
        if self.focalStation.focalStationIsPrimeFocus():
            self.setAllIgnoreState(False)
        else:
            self.setAllIgnoreState(True)

        # Ignore alarm when mirror covers or dome are closed or if the
        # telescope is stowed or slewing.
        self.setIgnoreWhenClosed()

class ADCFreeNsCs(ADCFree):
    # ADCFreeNsCs is a subclass of ADCFree, specifically for the
    # Nasmyth or Cassegrain ADC.
    def __init__(self):
        super(ADCFreeNsCs, self).__init__()
        # These status variables are defined in the alarm
        # configuration file. Each one of these status variables is
        # related to a single MELCO value supplied to Gen2 via the TSC
        # status packets.
        self.statusVar['ADC_DriveOn']   = {'ID': 'Melco_000410B', 'value': None}
        self.statusVar['ADC_DriveOff']  = {'ID': 'Melco_000410C', 'value': None}
        self.statusVar['ADC_SyncMode']  = {'ID': 'Melco_00A102E', 'value': None}
        self.statusVar['ADC_aSyncMode'] = {'ID': 'Melco_00A102F', 'value': None}

class ADCFreeNs(ADCFreeNsCs):
    # ADCFreeNs is a subclass of ADCFreeNsCs, specifically for the
    # Nasmyth ADC.
    def __init__(self):
        super(ADCFreeNs, self).__init__()
        # This is the status variable for the Nasmyth "ADC in free
        # mode" alarm.
        self.compositeAlarms = ('NsADCFreeMode', )

    # Update our status variable values based on the current status as
    # supplied to us via the Gen2 status aliases.
    def update(self, svConfig, statusFromGen2):
        super(ADCFreeNs, self).update(svConfig, statusFromGen2)

        # This class is for the Ns ADC. Enable alarms if focal
        # station is Nasmyth Optical. Otherwise, ignore alarms.
        if self.focalStation.focalStationIsNasmythOpt():
            self.setAllIgnoreState(False)
        else:
            self.setAllIgnoreState(True)

        # Ignore alarm when mirror covers or dome are closed or if the
        # telescope is stowed or slewing.
        self.setIgnoreWhenClosed()

class ADCFreeCs(ADCFreeNsCs):
    def __init__(self):
        super(ADCFreeCs, self).__init__()
        self.compositeAlarms = ('CsADCFreeMode', )

    def update(self, svConfig, statusFromGen2):
        super(ADCFreeNsCs, self).update(svConfig, statusFromGen2)

        # This class is for the Cs ADC. Enable alarms if focal
        # station is CS. Otherwise, ignore alarms.
        if self.focalStation.focalStationIsCassegrain():
            self.setAllIgnoreState(False)
        else:
            self.setAllIgnoreState(True)

        # Ignore alarm when mirror covers or dome are closed or if the
        # telescope is stowed or slewing.
        self.setIgnoreWhenClosed()

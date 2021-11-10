#!/usr/bin/env python

#
# AG_PosnError.py - methods for determining if the autoguider error is
#                   in an alarm state
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Wed Apr 25 09:52:50 HST 2012
#]
#
# AG_PosnError.py supplies methods to check the following autoguider
# conditions for alarm states:
#
# 1. Autoguider position error exceeds threshold.
#

import remoteObjects as ro
import Derived

class AG_PosnError(Derived.Derived):
    def __init__(self, logger = ro.nullLogger()):
        super(AG_PosnError, self).__init__(logger)
        
        # These status variables are defined in the alarm
        # configuration file. Each one of these status variables is
        # related to a single Gen2 status alias derived from data
        # supplied to Gen2 via the TSC status packets.
        self.statusVar = {
            'AG_Error': {'ID': 'AG_PosnError',  'value': None},
            'SV_Error': {'ID': 'SV_PosnError',  'value': None}
           }

        # We will store a TelState object here. We need a TelState
        # object because it tells us if the telescope is guiding and,
        # if so, whether it is guiding via the regular autoguider or
        # via the slit-viewer.
        self.telState = None

    # Update our status variable values based on the current status as
    # supplied to us via the Gen2 status aliases.
    def update(self, svConfig, statusFromGen2):
        super(AG_PosnError, self).update(svConfig, statusFromGen2)

        # Get a reference to the TelState object
        if self.telState == None:
            self.telState = svConfig.configID['TelState'].importedObject

        # Update the telescope state status variables.
        self.telState.update(svConfig, statusFromGen2)

        # Initially, ignore all of the individual alarms
        self.setIndIgnoreState(True)
        # Then, if we are guiding, enable only the alarm corresponding
        # to the current guiding mode.
        if self.telState.isGuiding():
            if self.telState.isGuidingSV():
                self.setIndIgnoreState(False, 'SV_Error')
            else:
                self.setIndIgnoreState(False, 'AG_Error')

    # Determine if the autoguider position error is in an alarm state.
    def posnErrorState(self, name, severity):
        # Get the threshold value for this quantity
        svConfigItem = self.svConfig.configID[self.statusVar[name]['ID']]
        threshold = svConfigItem.Alarm[severity].Threshold
        # Get the current value of the position error
        value = self.statusVar[name]['value']
        # First, check to see if we are guiding
        if self.telState.isGuiding():
            # We need to see if the supplied name matches the guiding
            # mode, e.g., if the name is SV_Error and we are guiding
            # via the slit-viewer, then we need to check the current
            # value against the threshold. Otherwise, we just return
            # False.
            if (self.telState.isGuidingSV() and 'SV' in name) or \
                   (not self.telState.isGuidingSV() and 'AG' in name):
                if 'Warning' in severity:
                    if value >= threshold and value < svConfigItem.Alarm['CriticalHi'].Threshold:
                        return True
                    else:
                        return False
                else:
                     if value >= threshold:
                         return True
                     else:
                         return False
            else:
                return False
        else:
            return False

    # agPosnErrorWarn returns True if the autoguider position error is
    # in a warning state.
    def agPosnErrorWarn(self):
        return self.posnErrorState('AG_Error', 'WarningHi')

    # agPosnErrorCrit returns True if the autoguider position error is
    # in a critical state.
    def agPosnErrorCrit(self):
        return self.posnErrorState('AG_Error', 'CriticalHi')

    # svAGPosnErrorWarn returns True if the slit-viewer position error is
    # in a warning state.
    def svAGPosnErrorWarn(self):
        return self.posnErrorState('SV_Error', 'WarningHi')
        
    # svAGPosnErrorCrit returns True if the slit-viewer position error is
    # in a critical state.
    def svAGPosnErrorCrit(self):
        return self.posnErrorState('SV_Error', 'CriticalHi')

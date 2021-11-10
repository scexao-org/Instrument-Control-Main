#!/usr/bin/env python

#
# Derived.py - methods used by the classes that implement the DerivedAlarms
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Wed Apr 25 09:47:34 HST 2012
#]
#

import re
import remoteObjects as ro

class Derived(object):
    def __init__(self, logger = ro.nullLogger()):
        self.logger = logger
        self.statusVar = {}
        self.compositeAlarms = {}
        self.svConfig = None

    # Update any of our status variables that have been supplied with
    # new values by Gen2 status aliases.
    def update(self, svConfig, statusFromGen2):
        self.svConfig = svConfig

        for key in self.statusVar:
            ID = self.statusVar[key]['ID']
            svConfigItem = self.svConfig.configID[ID]
            if svConfigItem.Gen2Alias in statusFromGen2:
                self.statusVar[key]['value'] = svConfigItem.MelcoValue(statusFromGen2[svConfigItem.Gen2Alias])

    def setIndMuteState(self, severity, muteOn):
        # Iterate through all of the regular status alarms
        for key in self.statusVar:
            ID = self.statusVar[key]['ID']
            svConfigItem = self.svConfig.configID[ID]
            if svConfigItem.Alarm:
                for sev in svConfigItem.Alarm:
                    if re.search(severity, sev):
                        if muteOn:
                            self.svConfig.muteOn(ID, sev, 'Config')
                        else:
                            self.svConfig.muteOff(ID, sev, 'Config')

    def setCompMuteState(self, severity, muteOn):
        # Iterate through all of the "composite" status alarms
        for name in self.compositeAlarms:
            svConfigItem = self.svConfig.configID[name]
            ID = svConfigItem.ID
            # Iterate through all of the alarms for this status
            # variable and set the mute state appropriately.
            if svConfigItem.Alarm:
                for sev in svConfigItem.Alarm:
                    if re.search(severity, sev):
                        if muteOn:
                            self.svConfig.muteOn(ID, sev, 'Config')
                        else:
                            self.svConfig.muteOff(ID, sev, 'Config')

    # Set the mute state for all of our alarms
    def setAllMuteState(self, muteOn):
        self.setIndMuteState('.*', muteOn)
        self.setCompMuteState('.*', muteOn)

     # Set the mute state for all of our 'Warning' alarms
    def setAllWarningMuteState(self, muteOn):
        self.setIndMuteState('Warning', muteOn)
        self.setCompMuteState('Warning', muteOn)

    def setIgnoreState(self, ignore, ID, svConfigItem):
        # Iterate through all of the alarms for this status variable
        # and set the ignore state appropriately.
        if svConfigItem.Alarm:
            for severity in svConfigItem.Alarm:
                if ignore:
                    self.svConfig.startIgnoreAlarm(ID, severity)
                else:
                    self.svConfig.stopIgnoreAlarm(ID, severity)
                        
    def setIndIgnoreState(self, ignore, name = None):
        if name == None:
            # Iterate through all of the regular status alarms
            for key in self.statusVar:
                ID = self.statusVar[key]['ID']
                svConfigItem = self.svConfig.configID[ID]
                self.setIgnoreState(ignore, ID, svConfigItem)
        else:
            # set the ignore state for the named status variable's
            # alarms
            ID = self.statusVar[name]['ID']
            svConfigItem = self.svConfig.configID[ID]
            self.setIgnoreState(ignore, ID, svConfigItem)

    def setCompIgnoreState(self, ignore, name = None):
        if name == None:
            # Iterate through all of the "composite" status alarms
            for compName in self.compositeAlarms:
                svConfigItem = self.svConfig.configID[compName]
                ID = svConfigItem.ID
                self.setIgnoreState(ignore, ID, svConfigItem)
        else:
            # set the ignore state for the named composite alarms
            svConfigItem = self.svConfig.configID[name]
            ID = svConfigItem.ID
            self.setIgnoreState(ignore, ID, svConfigItem)
        
    def setAllIgnoreState(self, ignore):
        self.setIndIgnoreState(ignore)
        self.setCompIgnoreState(ignore)

    # Note: setMuteState was experimental is not currently used.

    # Set mute state based on individual alarms, considering both
    # 'Config' and 'User' muteOn states. If any of the individual
    # alarms are muted, set other corresponding individual and
    # composite alarms to the same muteOn state.
    def setMuteState(self, statusVarNames, compositeID):
        muteOn = {}
        # First, iterate through all the individual status variables
        # and determine the muteOn state for each alarm, taking into
        # consideration the mute state in the status variable
        # configuration as well as the mute state set by the user.
        i = 0
        for name in statusVarNames:
            ID = self.statusVar[name]['ID']
            svConfigItem = self.svConfig.configID[ID]
            if svConfigItem.Alarm:
                for severity in svConfigItem.Alarm:
                    configMute = self.svConfig.getMuteOnState(severity, ID, 'Config')
                    userMute = self.svConfig.getMuteOnState(severity, ID, 'User')
                    thisMuteResult = configMute or userMute
                    if i == 0:
                        muteOn[severity] = thisMuteResult
                    else:
                        muteOn[severity] = muteOn[severity] or thisMuteResult
            i += 1

        print 'statusVarNames',statusVarNames
        print 'compositeID',compositeID
        print 'muteOn',muteOn
        # Now that we have the mute state for each alarm, set the mute
        # state for each alarm in the individual status variables.
        for name in statusVarNames:
            ID = self.statusVar[name]['ID']
            svConfigItem = self.svConfig.configID[ID]
            if svConfigItem.Alarm:
                for severity in svConfigItem.Alarm:
                    self.svConfig.setMuteOnState(ID, severity, muteOn[severity], 'User')

        # Set the mute state for the alarms in the composite status
        # variable to the same value as for the individual alarms.
        svConfigItem = self.svConfig.configID[compositeID]
        if svConfigItem.Alarm:
            for severity in svConfigItem.Alarm:
                self.svConfig.setMuteOnState(compositeID, severity, muteOn[severity], 'User')      


#!/usr/bin/env python

# Enviro.py - methods for determining if any of the environmental
#             conditions are in an alarm state
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Fri Jul  6 11:12:58 HST 2012
#]
#
# Enviro.py supplies methods to check the following environmental
# conditions for alarm states:
#
# 1. external and/or internal humidity above threshold value
# 2. external and/or internal windspeed above threshold value
#
# The threshold values are supplied in the svConfig structure, having
# been read from the alarm configuration file
# (cfg/alarm/environment_alarm_cfg.yml). There are typically both
# warning and critical threshold values supplied.
#
# Note that there are environmental sensors both inside and outside of
# the dome. If either or both sensors for a particular quantity are in
# an alarm state, we want to make only a single
# announcement. Therefore, the alarm configuration file specifies
# alarms for the individual sensors, but it also specifies "composite"
# alarms that are dependent on multiple sensors. The alarms on the
# individual sensors don't have any associated audio announcements but
# the "composite" alarms do have audio annoucements. That is how the
# "single announcement" scheme is implemented.
#
# In addition to the above alarms, additional methods are provided to
# determine if environmental conditions have been in the acceptable
# range (i.e., not exceeding the critical threshold value) for a
# specified time period, typically 15 or 30 minutes. The time period
# is specified in the alarm configuration file via the
# MinNotifyInterval and NotifyTimeout attributes.
#
# Finally, the update method in the Enviro class modifies the alarms'
# attributes in svConfig so as to mute the alarm's audio announcements
# if the dome is in a "closed" state, i.e., both the IR and Optical
# shutters are closed. Note that an alarm condition will still be
# recorded if the dome is closed and a quantity exceeds the threshold,
# but the alarm will not be announced.

import time
import remoteObjects as ro
import Derived

class Enviro(Derived.Derived):
    def __init__(self, logger = ro.nullLogger()):
        super(Enviro, self).__init__(logger)

        # These status variables are defined in the alarm
        # configuration file. Each one of these status variables is
        # related to a single MELCO value supplied to Gen2 via the TSC
        # status packets.
        self.statusVar = {
            'extTemp':      {'ID': 'Melco_000C005', 'value': None},
            'extHumidity':  {'ID': 'Melco_000C006', 'value': None},
            'extWindspeed': {'ID': 'Melco_000C002', 'value': None},
            'intHumidity':  {'ID': 'Melco_002A0CC', 'value': None},
            'intWindspeed': {'ID': 'Melco_002A0F0', 'value': None}
            }

        # These "composite" alarms are defined in the alarm
        # configuration file. Each of these alarms is related to
        # multiple MELCO values, e.g., highHumidity is an alarm that
        # will be triggered if either the external or internal
        # humidity exceeds the threshold. The following alarms also
        # implement the "environmental conditions have been in range"
        # alarms.
        self.compositeAlarms = (
            'HighHumidity',
            'HighWindspeed',
            'HumidityInRange15Min',
            'WindspeedInRange15Min',
            'EnviroInRange30Min'
            )

        # The clearPending flag is used to implement the
        # "environmental conditions have been in range" alarms.
        self.clearPending = {'Humidity': False, 'Windspeed': False}

    # Update our status variable values based on the current status as
    # supplied to us via the Gen2 status aliases.
    def update(self, svConfig, statusFromGen2):
        super(Enviro, self).update(svConfig, statusFromGen2)

        # Update the dome shutter status so that we can determine if
        # we need to mute the alarms due to the dome being closed.
        domeShutter = svConfig.configID['DomeShutter'].importedObject
        domeShutter.update(svConfig, statusFromGen2)

        # If the dome shutter is closed, modify the status variable
        # configuration to mute all of the audio announcements. If the
        # shutter is open, un-mute the audio.
        closed = domeShutter.shutterClosed()
        self.setAllMuteState(closed)

        # We actually want the "environmental conditions have been in
        # range" alarms to be un-muted at all times, so un-mute them
        # here.
        for name in ('HumidityInRange15Min', 'WindspeedInRange15Min', 'EnviroInRange30Min'):
            svConfigItem = self.svConfig.configID[name]
            ID = svConfigItem.ID
            if svConfigItem.Alarm:
                for sev in svConfigItem.Alarm:
                    self.svConfig.muteOff(ID, sev, 'Config')

        # If the humidity is in the "Ok" range, reset the
        # firstNotifyTimestamp attribute for the humidity alarms.
        if not self.warnHumidity() and not self.critHumidity():
            self.svConfig.configID['HighHumidity'].resetFirstNotifyTime()

        # If the windspeed is in the "Ok" range, reset the
        # firstNotifyTimestamp attribute for the windspeed alarms.
        if not self.warnWindspeed() and not self.critWindspeed():
            self.svConfig.configID['HighWindspeed'].resetFirstNotifyTime()

    # warnHi is used for the humidity and windspeed composite
    # alarms. Returns True if either the external or internal values
    # are above the warning threshold but below the critical
    # threshold. Otherwise, returns False.
    def warnHi(self, name, extValue, intValue):
        extKey = 'ext' + name
        intKey = 'int' + name
        svConfigItem = self.svConfig.configID[self.statusVar[extKey]['ID']]
        warnThresholdExt = svConfigItem.Alarm['WarningHi'].Threshold
        critThresholdExt = svConfigItem.Alarm['CriticalHi'].Threshold
        svConfigItem = self.svConfig.configID[self.statusVar[intKey]['ID']]
        warnThresholdInt = svConfigItem.Alarm['WarningHi'].Threshold
        critThresholdInt = svConfigItem.Alarm['CriticalHi'].Threshold
        if (extValue >= warnThresholdExt and extValue < critThresholdExt) or \
                (intValue >= warnThresholdInt and intValue < critThresholdInt):
            return True
        else:
            return False

    # critHi is used for the humidity and windspeed composite
    # alarms. Returns True if either the external or internal values
    # are above the critical threshold. Otherwise, returns False. Note
    # that, if the critical threshold is exceeded, the method also
    # sets the clearPending flag to True. The clearPending flag is
    # part of the implementation of the "environmental conditions have
    # been in range" alarms.
    def critHi(self, name, extValue, intValue):
        extKey = 'ext' + name
        intKey = 'int' + name
        svConfigItem = self.svConfig.configID[self.statusVar[extKey]['ID']]
        critThresholdExt = svConfigItem.Alarm['CriticalHi'].Threshold
        svConfigItem = self.svConfig.configID[self.statusVar[intKey]['ID']]
        critThresholdInt = svConfigItem.Alarm['CriticalHi'].Threshold
        if extValue >= critThresholdExt or intValue >= critThresholdInt:
            self.clearPending[name] = True
            return True
        else:
            return False

    # warnHumidity is a wrapper method around the warnHi method,
    # specifically for humidity
    def warnHumidity(self):
        return self.warnHi('Humidity', self.extHumid(), self.intHumid())

    # critHumidity is a wrapper method around the critHi method,
    # specifically for humidity
    def critHumidity(self):
        return self.critHi('Humidity', self.extHumid(), self.intHumid())

    # warnWindspeed is a wrapper method around the warnHi method,
    # specifically for windspeed
    def warnWindspeed(self):
        return self.warnHi('Windspeed', self.extWindspeed(), self.intWindspeed())

    # Wrapper method around the critHi method, specifically for
    # windspeed
    def critWindspeed(self):
        return self.critHi('Windspeed', self.extWindspeed(), self.intWindspeed())

    # Determine if the specified environmental condition has been in
    # the acceptable range for the specified amount of time, after
    # previously having been in the critical range. If so, return
    # True. Otherwise, return False.
    def envCondInRange(self, key1, key2, severity, currentState):
        # Get the current time
        now = time.time()
        # Get the time at which the condition was last in the critical range
        svConfigItem = self.svConfig.configID[key1]
        critAlarm = svConfigItem.Alarm[severity]
        lastAlarmTimestamp = critAlarm.lastAlarmTimestamp
        # The okAlarm configuration tells us the time interval over
        # which the value has to be in the non-critical range.
        okAlarm = self.svConfig.configID[key2].Alarm['OK']
        # Check to see if we should trigger the "environmental
        # conditions have been in range" alarm, based on the following
        # tests:
        # 1. Not currently in critical range
        # 2. Condition was in critical range at some point
        # 3. MinNotifyInterval seconds have elapsed since condition was last in critical range
        # 4. # The "Ok" alarm hasn't timed-out
        if (not currentState) and \
                (not lastAlarmTimestamp == None) and \
                now > lastAlarmTimestamp + okAlarm.MinNotifyInterval and \
                now < lastAlarmTimestamp + okAlarm.NotifyTimeout:
            return True
        else:
            return False

    # humidityInRange15 is a wrapper method around the envCondInRange
    # method, specifically for humidity.
    def humidityInRange15(self):
        return self.envCondInRange('HighHumidity', 'HumidityInRange15Min', 'CriticalHi', self.critHumidity())

    # humidityInRange15 is a wrapper method around the envCondInRange
    # method, specifically for windspeed.
    def windspeedInRange15(self):
        return self.envCondInRange('HighWindspeed', 'WindspeedInRange15Min', 'CriticalHi', self.critWindspeed())

    # enviroInRange30 determines whether both the humidity and windspeed
    # have been in range for the specified time. It makes use of the
    # envCondInRange method as well as our clearPending attribute.
    def enviroInRange30(self):
        # Determine if the humidity and windspeed have been in the
        # non-critical range for the specified amount of time.
        inRange30 = {}
        inRange30['Humidity'] = self.envCondInRange('HighHumidity', 'EnviroInRange30Min', 'CriticalHi', self.critHumidity())
        inRange30['Windspeed'] = self.envCondInRange('HighWindspeed', 'EnviroInRange30Min', 'CriticalHi', self.critWindspeed())

        # We need to check to see if either humidity or windspeed, or
        # both, have a clearPending and, if so, if they have been in
        # the non-critical range for the specified amount of time.
        if self.clearPending['Humidity'] and self.clearPending['Windspeed']:
            # Both humidity and windspeed have clearPending set, which
            # means they were both in the critcial range at some
            # point.
            if inRange30['Humidity'] and inRange30['Windspeed']:
                # Both humidity and windspeed have been in the
                # non-critical range for the specified amount of time,
                # so reset the clearPending flags and return True to
                # indicate that the "Ok" alarm should be triggered.
                self.clearPending['Humidity'] = False
                self.clearPending['Windspeed'] = False
                return True
            else:
                # One or the other of humidity or windspeed has been
                # in the non-critical range for the specified time, so
                # reset that one's clearPending flag. Return False
                # because they both haven't been in range for long
                # enough.
                for name in inRange30:
                    if inRange30[name]:
                        self.clearPending[name] = False
                return False
        else:
            # Either humidity or windspeed might have clearPending
            # set. If the one that has clearPending set has also been
            # in the non-critical range for the specified time, then
            # reset clearPending and return True to indicate that the
            # "Ok" alarm should be triggered.
            for name in inRange30:
                if self.clearPending[name] and inRange30[name]:
                    self.clearPending[name] = False
                    return True
            # If we get here, either there were no clearPending flags
            # set or the one that was set wasn't in the non-critical
            # range for long enough. Either way, we don't want to
            # trigger the "Ok" alarm, so return False.
            return False           

    # Return the current value of the external temperature
    def extTemp(self):
        return self.statusVar['extTemp']['value']

    # Return the current value of the external humidity
    def extHumid(self):
        return self.statusVar['extHumidity']['value']

    # Return the current value of the internal humidity
    def intHumid(self):
        return self.statusVar['intHumidity']['value']

    # Return the current value of the external windspeed
    def extWindspeed(self):
        return self.statusVar['extWindspeed']['value']

    # Return the current value of the internal windspeed
    def intWindspeed(self):
        return self.statusVar['intWindspeed']['value']

#!/usr/bin/env python
#
# StatusValHistory.py - Status Value and Alarm classes for Gen2
#                       alarm_handler.py application
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Fri Feb 22 11:56:31 HST 2013
#]
#
import os, getopt, sys
import time
import shelve, anydbm
import threading
import StatusVar

class StatusVal(object):
    def __init__(self, ID, timestamp = None, value = None, alarmState = None, muteOn = None):
        self.ID = ID
        self.timestamp = timestamp
        self.value = value
        self.alarmState = alarmState
        self.muteOn = muteOn

    def setStatus(self, timestamp, value, alarmState, muteOn):
        self.timestamp = timestamp
        self.value = value
        self.alarmState = alarmState
        self.muteOn = muteOn

    def getStatus(self):
        status = {'ID':         self.ID,
                  'timestamp':  self.timestamp,
                  'value':      self.value,
                  'alarmState': self.alarmState,
                  'muteOn':     self.muteOn}
        return status

    def __repr__(self):
        return "ID=%s timestamp=%f, value=%s, alarmState=%s, muteOn=%s" % (self.ID, self.timestamp, str(self.value), self.alarmState, self.muteOn)

class StatusAlarm(object):
    def __init__(self, ID, Name, timestamp, value, alarmState, varType, units, audioFilename, muteOn, visible):
        self.ID = ID
        self.Name = Name
        self.timestamp = timestamp
        self.value = value
        self.alarmState = alarmState
        self.varType = varType
        self.units = units
        self.audioFilename = audioFilename
        self.muteOn = muteOn
        self.visible = visible
        self.acknowledged = False

    def getAlarm(self):
        alarm = {'ID':            self.ID,
                 'Name':          self.Name,
                 'timestamp':     self.timestamp,
                 'value':         self.value,
                 'alarmState':    self.alarmState,
                 'varType':       self.varType,
                 'units':         self.units,
                 'audioFilename': self.audioFilename,
                 'muteOn':        self.muteOn,
                 'visible':       self.visible,
                 'acknowledged':  self.acknowledged
                  }
        return alarm

    def __repr__(self):
        retString = '%s, ID=%s, Name=%s, value=%s, ' % (time.asctime(time.localtime(self.timestamp)), self.ID, self.Name, self.value)
        if self.varType == 'Analog':
            retString += 'units=%s, ' % self.units
        retString += 'alarmState=%s, audioFile=%s, muteOn=%s, visible=%s, acknowledged=%s' % (self.alarmState, self.audioFilename, self.muteOn, self.visible, self.acknowledged)
        return retString

class StatusValHistory(object):
    def __init__(self, persistDatafileLock, logger):
        self.history = {}
        self.initialAlarmList = []
        self.alarmList = {}
        self.changedAlarmList = {}
        self.reportAlarmList = []
        self.logger = logger
        self.lock = threading.RLock()
        self.persistHistoryDataKey = 'history'
        self.persistDatafileLock = persistDatafileLock
        # Note that a lower value implies a higher priority for the
        # audio files. The Critical alarms have the highest priority.
        self.audioPriority = {
            'Critical': {'current': None, 'max':   0, 'min':  99},
            'Warning':  {'current': None, 'max': 100, 'min': 199},
            'OK':       {'current': None, 'max': 200, 'min': 299}
            }
        for severity in self.audioPriority:
            self.audioPriority[severity]['current'] = self.audioPriority[severity]['max']
        # Create a dictionary to gather the names of the audio files
        # that need to get played for the active alarms. We want to
        # organize the list so that all Critical alarms get played
        # first, Warning alarms next, etc. Note that we will make use
        # of the SoundSink's priority argument so that the sounds get
        # played sequentially rather than all on top of each other.
        self.alarmAudioFilenames = {}

    def loadHistory(self, filename, svConfig):
        with self.persistDatafileLock:
            try:
                self.logger.info('Opening alarm_handler history for loading %s...' % filename)
                persistData = shelve.open(filename)
            except anydbm.error,e:
                message = 'Error creating or opening %s %s' % (filename,str(e))
                self.logger.error(message)
                raise Exception(message)

            try:
                self.history = persistData[self.persistHistoryDataKey]
                for ID in self.history:
                    if ID not in svConfig.configID:
                        del self.history[ID]
                persistData[self.persistHistoryDataKey] = self.history
            except KeyError, e:
                self.logger.warn('Warning %s key not found in filename %s' % (str(e), filename))
            finally:
                self.logger.info('Closing alarm_handler history after loading')
                persistData.close()

    def saveHistory(self, filename):
        with self.persistDatafileLock:
            try:
                self.logger.info('Opening alarm_handler history for saving %s...' % filename)   
                persistData = shelve.open(filename)
            except anydbm.error,e:
                message = 'Error creating or opening %s %s' % (filename,str(e))
                self.logger.error(message)
                raise Exception(message)

            with self.lock:
                try:
                    persistData[self.persistHistoryDataKey] = self.history
                finally:
                    self.logger.info('Closing alarm_handler history after saving')
                    persistData.close()

        return 0

    def reportOne(self, ID):
        try:
            history = self.history[ID]
        except:
            raise Exception('ID %s does not exist in StatusValHistory.history' % ID)
        for statusValue in history:
            self.logger.info('%s %s %s %s %s' % (
                    statusValue.ID, 
                    time.asctime(time.localtime(statusValue.timestamp)),
                    str(statusValue.value),
                    statusValue.alarmState,
                    statusValue.muteOn))

    def report(self, ID = None):
        try:
            if ID:
                self.reportOne(ID)
            else:
                for ID in self.history:
                    self.reportOne(ID)
            return 0
        except Exception, e:
            return str(e)

    def initialValue(self, svConfig, statusFromGen2):
        self.initalAlarmList = []
        timestamp = time.time()

        for ID in svConfig.configID:
            svConfigItem = svConfig.configID[ID]
            if svConfigItem.Gen2Alias:
                Gen2Alias = svConfigItem.Gen2Alias
                gen2Value = statusFromGen2[Gen2Alias]
                gen2AliasInfo = svConfig.configGen2[Gen2Alias]
                if svConfigItem.Alarm:
                    ID = svConfigItem.ID
                    MelcoValue = svConfigItem.MelcoValue(gen2Value)
                    alarmState = svConfigItem.alarmState(gen2Value)
                    muteOn = svConfig.getMuteOnState(alarmState, ID)
                    statusVal = StatusVal(ID, timestamp, MelcoValue, alarmState, muteOn)
                    with self.lock:
                        if ID in self.history:
                            if self.checkCurrentSameAsPrevious(statusVal):
                                self._update_currentSameAsPrevious(statusVal)
                            else:
                                self.history[ID].append(statusVal)
                        else:
                            self.history[ID] = [statusVal]
                    Name = svConfigItem.Name
                    varType = svConfigItem.Type
                    if varType == 'Analog':
                        units = svConfigItem.Units
                    else:
                        units = None
                    audioFilename = svConfig.getAlarmAudio(alarmState, ID)
                    visible = svConfig.getVisibleState(alarmState, ID)
                    self.initialAlarmList.append(StatusAlarm(ID,
                                                             Name,
                                                             timestamp,
                                                             MelcoValue,
                                                             alarmState,
                                                             varType,
                                                             units,
                                                             audioFilename,
                                                             muteOn,
                                                             visible))
            elif svConfigItem.importedObject:                
                svConfigItem.importedObject.update(svConfig, statusFromGen2)
                if svConfigItem.Alarm:
                    alarmState = svConfigItem.alarmState(None)
                    muteOn = svConfig.getMuteOnState(alarmState, ID)
                    statusVal = StatusVal(ID, timestamp, None, alarmState, muteOn)
                    with self.lock:
                        if ID in self.history:
                            if self.checkCurrentSameAsPrevious(statusVal):
                                self._update_currentSameAsPrevious(statusVal)
                            else:
                                self.history[ID].append(statusVal)
                        else:
                            self.history[ID] = [statusVal]
                    Name = svConfigItem.Name
                    audioFilename = svConfig.getAlarmAudio(alarmState, ID)
                    visible = svConfig.getVisibleState(alarmState, ID)
                    self.initialAlarmList.append(StatusAlarm(ID,
                                                             Name,
                                                             timestamp,
                                                             None,
                                                             alarmState,
                                                             None,
                                                             None,
                                                             audioFilename,
                                                             muteOn,
                                                             visible))

    def checkCurrentSameAsPrevious(self, currentUpdate):
        ID = currentUpdate.ID
        history = self.history[ID]
        previousUpdate = history[-1]
        previousMelcoValue = previousUpdate.value
        previousAlarmState = previousUpdate.alarmState
        previousMuteOn = previousUpdate.muteOn

        currentMelcoValue = currentUpdate.value
        currentAlarmState = currentUpdate.alarmState
        currentMuteOn = currentUpdate.muteOn

        if currentMelcoValue == previousMelcoValue and \
               currentAlarmState == previousAlarmState and \
               currentMuteOn == previousMuteOn:
            return True
        else:
            return False

    def _update_currentSameAsPrevious(self, currentUpdate):
        ID = currentUpdate.ID
        history = self.history[ID]
        previousUpdate = history[-1]
        previousMelcoValue = previousUpdate.value
        previousAlarmState = previousUpdate.alarmState
        previousMuteOn = previousUpdate.muteOn

        # We found that the value, alarm state, and muteOn haven't
        # changed since the previous time. Before we decide what to do
        # with the current value, examine the value/state/muteOn from two
        # steps back, if we have that much history.
        if len(history) > 1:
            secondPreviousUpdate = history[-2]
            secondPreviousValue = secondPreviousUpdate.value
            secondPreviousAlarmState = secondPreviousUpdate.alarmState
            secondPreviousMuteOn = secondPreviousUpdate.muteOn
            if previousMelcoValue == secondPreviousValue and \
                   previousAlarmState == secondPreviousAlarmState and \
                   previousMuteOn == secondPreviousMuteOn:
                # Current value/alarm state/muteOn is same as previous
                # value/state/muteOn and the same as the one before
                # that, so just update the timestamp on the previous
                # update to reflect the current timestamp.
                previousUpdate.setStatus(currentUpdate.timestamp, currentUpdate.value, currentUpdate.alarmState, currentUpdate.muteOn)
            else:
                # Previous value/alarm state/muteOn differ from the
                # 2nd previous one, so we don't want to alter previous
                # values. Append current value/alarm state/muteOn onto
                # history.
                with self.lock:
                    history.append(currentUpdate)
        else:
            # Our history has only one previous value, so we don't
            # want to alter it. Append current value/alarm
            # state/muteOn onto history.
            with self.lock:
                history.append(currentUpdate)

    def update(self, svConfig, statusFromGen2):
        timestamp = time.time()
        # Loop through all the Gen2 status aliases that we got from
        # the status task
        for Gen2Alias in statusFromGen2:
            # We only care about Gen2 status aliases that are in our
            # status variable configuration.
            if Gen2Alias in svConfig.configGen2:
                # Get the value of the status variable. This was sent
                # to us by the Gen2 status task.
                gen2Value = statusFromGen2[Gen2Alias]
                # Get the status variable configuration information
                # for this Gen2 status alias.
                gen2AliasInfo = svConfig.configGen2[Gen2Alias]
                # Loop through all the Gen2AliasModifiers for this
                # Gen2 status alias in our status variable
                # configuration. We usually have multiple
                # Gen2AliasModifiers for status aliases that are a
                # combination of bits from the Melco status words.
                for Gen2AliasModifier in gen2AliasInfo:
                    # Get the configuration information for this
                    # status alias/modifier. This information includes
                    # the Melco identifier, alarm definitions, etc.
                    svConfigItem = gen2AliasInfo[Gen2AliasModifier]
                    # We only care about this
                    # Gen2Alias/Gen2AliasModifier combination if there
                    # is an Alarm defined for it
                    if svConfigItem.Alarm:
                        ID = svConfigItem.ID
                        # Send the current value that we got from Gen2
                        # to the MelcoValue method so that we can get
                        # the value of the status parameter as it
                        # exists in the TSC/Melco system. Sometimes,
                        # this involves applying a bit mask to the
                        # Gen2 value.
                        currentMelcoValue = svConfigItem.MelcoValue(gen2Value)
                        # Based on the current Gen2 value, determine
                        # if the status parameter is in an alarm
                        # condition. Note that the alarmState method
                        # internally uses the MelcoValue method to
                        # convert the Gen2 value into a Melco value.
                        currentAlarmState = svConfigItem.alarmState(gen2Value)
                        # We also want to store the current muteOn
                        # state in the history, so get that here
                        currentMuteOn = svConfig.getMuteOnState(currentAlarmState, ID)

                        # Before we append to the history log, examine
                        # the current and previous values to see if
                        # they are the same. The idea is that we don't
                        # want to store repeated values that don't
                        # change. We really only want to store
                        # transitions from one value to a different
                        # value. This will save disk space and make it
                        # less tedious to look through the history
                        # log.
                        history = self.history[ID]
                        previousUpdate = history[-1]
                        previousMelcoValue = previousUpdate.value
                        previousAlarmState = previousUpdate.alarmState
                        previousMuteOn = previousUpdate.muteOn

                        currentUpdate = StatusVal(ID, timestamp, currentMelcoValue, currentAlarmState, currentMuteOn)

                        if currentMelcoValue == previousMelcoValue and \
                               currentAlarmState == previousAlarmState and \
                               currentMuteOn == previousMuteOn:
                            # Current value is same as previous - call
                            # a helper function that will append to
                            # the history if necessary.
                            self._update_currentSameAsPrevious(currentUpdate)
                        else:
                            # Current value and/or alarm state has
                            # changed from previous. Append to history
                            # log.
                            with self.lock:
                                history.append(currentUpdate)   

        # The above section added alarms for each Status Variable
        # whose value comes directly from a single Gen2 status
        # alias. The next section adds alarms for the Status Variables
        # that depend on multiple Gen2 status aliases.
        for ID in svConfig.configID:
            svConfigItem = svConfig.configID[ID]
            if svConfigItem.importedObject:
                svConfigItem.importedObject.update(svConfig,statusFromGen2)
                if svConfigItem.Alarm:
                    currentAlarmState = svConfigItem.alarmState(None)
                    currentMuteOn = svConfig.getMuteOnState(currentAlarmState, ID)
                    history = self.history[ID]
                    previousUpdate = history[-1]
                    previousAlarmState = previousUpdate.alarmState
                    previousMuteOn = previousUpdate.muteOn
                    currentUpdate = StatusVal(ID, timestamp, None, currentAlarmState, currentMuteOn)
                    if currentAlarmState == previousAlarmState and currentMuteOn == previousMuteOn:
                        self._update_currentSameAsPrevious(currentUpdate)
                    else:
                        with self.lock:
                            history.append(currentUpdate)

    def alarms(self, svConfig):
        """Build a list of alarms for the most recent entry in the history data structure"""
        self.alarmList = []
        self.changedAlarmList = []
        # Loop through all the ID's in the history data
        # structure
        for ID in self.history:
            history = self.history[ID]
            length = len(history)
            # Get some information about this ID from the status
            # variable confguration
            Name = svConfig.configID[ID].Name
            varType = svConfig.configID[ID].Type
            if varType == 'Analog':
                units = svConfig.configID[ID].Units
            else:
                units = None
            # Special case if the length of the history for this ID is
            # 1. In that case, we basically look to see if the
            # alarmState is anything besides Ok and, if so, set a flag
            # so that we can create a StatusAlarm object and add it to
            # our alarm list.
            createAlarm = False
            createChangedAlarm = False
            if length == 1:
                currentAlarmState = history[0].alarmState
                if currentAlarmState != 'Ok':
                    createAlarm = True
                createChangedAlarm = True
            elif length > 1:
                # If the history length is greater than 1, we look to
                # see if the current alarm state is something besides
                # Ok and if the current alarm state has changed from
                # the previous one in the history log. If so, set a
                # flag so that we can create a StatusAlarm object and
                # add it to our alarm list.
                currentAlarmState = history[-1].alarmState
                previousAlarmState = history[-2].alarmState
                if currentAlarmState != 'Ok' or (currentAlarmState == 'Ok' and currentAlarmState != previousAlarmState):
                    createAlarm = True
                if currentAlarmState != previousAlarmState:
                    createChangedAlarm = True

            # If the flag is true, create a StatusAlarm object and add
            # it to the alarmList
            if createAlarm or createChangedAlarm:
                audioFilename = svConfig.getAlarmAudio(currentAlarmState, ID)
                muteOn = svConfig.getMuteOnState(currentAlarmState, ID)
                visible = svConfig.getVisibleState(currentAlarmState, ID)
                alarm = StatusAlarm(ID,
                                    Name,
                                    history[-1].timestamp,
                                    history[-1].value,
                                    currentAlarmState,
                                    varType,
                                    units,
                                    audioFilename,
                                    muteOn,
                                    visible)
               
                if createAlarm:
                    self.alarmList.append(alarm)
                if createChangedAlarm:
                    self.logger.info('%s -changed alarm' % alarm)
                    self.changedAlarmList.append(alarm)

    def reportAlarms(self, svConfig, soundsink):
        self.reportAlarmList = []
        # Create the list of alarms based on the current values in the
        # history data structure.
        self.alarms(svConfig)
        # Clear out the alarmAudioFilenames data structure.
        for severity in self.audioPriority:
            self.alarmAudioFilenames[severity] = []
        # Loop through all the alarms in the list. It is possible that
        # there are no alarms. That is ok.
        for alarm in self.alarmList:
            # We use the ID in the alarm as an index to get the status
            # variable configuration information for this alarm
            ID = alarm.ID
            svConfigItem = svConfig.configID[ID]
            alarmState = alarm.alarmState
            if alarmState == 'Ok':
                print alarm
                self.reportAlarmList.append(alarm)
                self.logger.info('%s - reported alarm' % alarm)
            elif alarmState == 'N/A':
                pass
            else:
                # Get the alarm configuration for this ID and the
                # alarm state in which the variable is currently in.
                svConfigAlarm = svConfigItem.Alarm[alarmState]
                muteOn = svConfig.getMuteOnState(alarmState, ID)
                acknowledged = svConfigAlarm.acknowledged
                lastNotifyTimestamp = svConfigAlarm.lastNotifyTimestamp
                minNotifyInterval = svConfigAlarm.MinNotifyInterval
                notifyTimeout = svConfigAlarm.NotifyTimeout
                now = time.time()

                svConfigAlarm.lastAlarmTimestamp = now
                firstNotifyTimestamp = svConfigAlarm.firstNotifyTimestamp

                # We need to check to see if we should
                # print/report/announce this alarm. Here are the
                # criteria we use:
                # 1. If the next three items are all True, we
                #    print/report/announce the alarm
                #    a. lastNotifyTimestamp is defined and
                #       minNotifyInterval seconds has elapsed since the
                #       last notification                
                #    b. firstNotifyTimestamp is defined and the
                #       elapsed time since the first notification has not
                #       exceeded the timeout
                #    c. the alarm has not been acknowledged
                # 2. If the muteOn state of the alarm has changed, we
                #    print/report the alarm. If muteOn is False, we also
                #    announce the alarm.
                if ((lastNotifyTimestamp == None or now > lastNotifyTimestamp + minNotifyInterval) and \
                    (firstNotifyTimestamp == None or now < firstNotifyTimestamp + notifyTimeout) and \
                    not acknowledged) or \
                    self.muteOnChanged(ID):
                    print alarm
                    self.reportAlarmList.append(alarm)
                    self.logger.info('%s - reported alarm' % alarm)
                    # If the alarm isn't muted and we have a soundsink
                    # object on which to play the audio alarm, add the
                    # alarm audio to the alarmAudioFilenames data
                    # structure.
                    if soundsink and alarm.audioFilename and (not muteOn):
                        self.addAudio(alarmState, alarm.audioFilename)
                    if firstNotifyTimestamp == None:
                        svConfigAlarm.firstNotifyTimestamp = now

                        # Save the current time so that we can know
                        # when this alarm was last printed/announced.
                    svConfigItem.Alarm[alarmState].lastNotifyTimestamp = now

        # If we have a soundsink object on which to play audio alarms,
        # play all the alarms in the alarmAudioFilenames data
        # structure now.
        if soundsink:
            self.playAudio(soundsink)

    def addAudio(self, alarmState, audioFilename):
        for severity in self.audioPriority:
            priority = self.audioPriority[severity]
            if severity in alarmState:
                self.logger.info('Adding audio file %s to %s list' % (audioFilename, severity))
                self.alarmAudioFilenames[severity].append((audioFilename, priority['current']))
                if priority['current'] < priority['min']:
                    priority['current'] += 1
                else:
                    priority['current'] = priority['max']
        
    def playAudio(self, soundsink):
        for severity in ('Critical', 'Warning', 'OK'):
            for alarmAudioFilename, audioPriority in self.alarmAudioFilenames[severity]:
                self.logger.info('Playing audio file %s with priority %d' % (alarmAudioFilename, audioPriority))
                soundsink.playFile(alarmAudioFilename, priority=audioPriority)

    def muteOnChanged(self, ID):
        history = self.history[ID]
        current = history[-1]
        if len(history) > 1:
            previous = history[-2]
            if previous.muteOn != current.muteOn:
                return True
            else:
                return False
        else:
            return False

    def purgeOne(self, ID, age = 86400):
        try:
            history = self.history[ID]
        except:
            raise Exception('ID %s does not exist in StatusValHistory.history' % ID)
        now = time.time()
        oldest = now - age
        self.logger.info('Purging all data for ID %s prior to %s' % (ID, time.asctime(time.localtime(oldest))))
        self.logger.debug('Length of ID %s prior to purge is %d earliest time is %s' % (ID, len(history), time.asctime(time.localtime(history[0].timestamp))))
        i = -1
        with self.lock:
            for statusValue in history:
                if statusValue.timestamp < oldest:
                    i += 1
                else:
                    break
            if i >= 0:
                del history[0:i+1]
        self.logger.debug('Length of ID %s after purge is %d earliest time is %s' % (ID, len(self.history[ID]), time.asctime(time.localtime(self.history[ID][0].timestamp))))
        return 0

    def purge(self, age = 86400, maxLength = None, ID = None):
        try:
            if ID:
                self.purgeOne(ID, age)
            else:
                if maxLength:
                    maxHistoryLength = -1
                    maxhistoryLengthID = None
                    i = 0
                    for ID in self.history:
                        i += 1
                        thisLength = len(self.history[ID])
                        if i == 1 or thisLength > maxHistoryLength:
                            maxHistoryLength = thisLength
                            maxhistoryLengthID = ID
                    if maxhistoryLengthID:
                        self.logger.debug('ID with longest history is %s length is %d maxLength is %d' % (maxhistoryLengthID, maxHistoryLength, maxLength))
                        if maxHistoryLength > maxLength:
                            age = time.time() - self.history[maxhistoryLengthID][maxHistoryLength-maxLength-1].timestamp
                for ID in self.history:
                    self.purgeOne(ID, age)
            return 0
        except Exception, e:
            return str(e)

def main(options, args):
    pass

def usage():
    print 'Usage: StatusVal [-h|--help]'

if __name__=='__main__':

    # Process command-line options
    try:
        options, args = getopt.getopt(sys.argv[1:], 'h', ['help'])
    except getopt.GetoptError as e:
        print e
        usage()
        exit(1)

    for o, a in options:
        if o in ('-h', '--help'):
            usage()
            exit(0)
        else:
            print 'Unexpected option:',o

    main(options, args)

#! /usr/local/bin/python
# Alert.py -- Bruce Bon -- 2006-12-04 16:38

# Alert classes, to sound audio files and manage repeat intervals

# AudioAlert objects must be instantiated for each pair of 
# alarm/warning audio files are to be used.  An AudioAlert
# object may have its minimum interval times customized to whatever
# values are desired.  It will play its alert sound when the alert()
# method is called, unless it has already played the sound within
# min interval seconds of the current call.  The min interval will
# never be less thanTelStat_cfg.AudioMinInterval (currently 5 seconds), 
# to make sure that messages are not sent faster than the audio can be 
# played.
#
# Clear messages are played only if there was a preceding alarm
# message (NOT just a warning), and then only after the min interval
# since the last time the alert was called with level==ALARM.
# If an alert has a clear message but no alarm message, the alert() 
# method must still be called with ALARM in order for the 
# time-of-last-alarm to be set; otherwise, no clear message will ever 
# be issued.
#
# Arguments/parameters:
#    warnAudio          file spec of warning audio clip
#    warnMinInterval    min interval in seconds between warning sounds
#    warnTimeOut        max period in seconds during which warnings will
#                       be sounded, before warnTimeOut is reset
#    alarmAudio         file spec of alarm audio clip
#    alarmMinInterval   min interval in seconds between alarm sounds
#    alarmTimeOut       max period in seconds during which alarms will
#                       be sounded, before alarmTimeOut reset
#    clearAudio         file spec of clear audio clip
#    clearMinInterval   min interval in seconds before issuing clear audio
#                       and between repeated clear audio messages
#    clearTimeOut       max period in seconds during which clear messages
#                       will be sounded, before clearTimeOut reset

######################################################################
################   import needed modules   ###########################
######################################################################

# import signal
import time

import TelStat_cfg
import AudioPlayer
import StatusDictionary         # for time

######################################################################
################   assign needed globals   ###########################
######################################################################

CLEAR   = 0
WARNING = 1
ALARM   = 2
ERROR   = 2     # deprecated

# Following constants must be numbers because they are used in expressions
_NO_TIME_OUT = 60*60*24*365         # no time-out
_FIRST_TIME = _NO_TIME_OUT * 100    # indicates first audio for this alert 
                                    #   since it was cleared


######################################################################
################   declare classes for alerts   ######################
######################################################################

class AudioAlert:
    '''An object which will play sound alerts for a single condition, 
        housekeeping to avoid too frequent sound-offs, etc.'''

    def __init__( self,
                  warnAudio=None,
                  warnMinInterval=TelStat_cfg.AudioMinInterval,
                  warnTimeOut=None,
                  alarmAudio=None,
                  alarmMinInterval=TelStat_cfg.AudioMinInterval,
                  alarmTimeOut=None,
                  clearAudio=None,
                  clearMinInterval=TelStat_cfg.AudioMinInterval,
                  clearTimeOut=None):
        """Constructor."""
        self.warnAudio          = warnAudio
        self.warnMinInterval    = warnMinInterval
        if  warnTimeOut == None:
            self.warnTimeOut    = _NO_TIME_OUT
        else:
            self.warnTimeOut    = warnTimeOut

        self.alarmAudio         = alarmAudio
        self.alarmMinInterval   = alarmMinInterval
        if  alarmTimeOut == None:
            self.alarmTimeOut   = _NO_TIME_OUT
        else:
            self.alarmTimeOut   = alarmTimeOut

        self.clearAudio         = clearAudio
        self.clearMinInterval  = clearMinInterval
        if  clearTimeOut == None:
            self.clearTimeOut   = _NO_TIME_OUT
        else:
            self.clearTimeOut   = clearTimeOut

        self.mute               = False
        self.warnAudioLastTime  = 0
        self.alarmAudioLastTime = 0
        self.clearAudioLastTime = 0
        self.warnFirstTime      = _FIRST_TIME
        self.alarmFirstTime     = _FIRST_TIME
        self.clearFirstTime     = _FIRST_TIME
        self.alarmLastTime      = 0
        self.clearPending       = False
        if  not TelStat_cfg.audioPlayer:
            TelStat_cfg.audioPlayer = AudioPlayer.AudioPlayer()
            TelStat_cfg.audioPlayer.setMuteState(TelStat_cfg.DEFAULT_AUDIO_MUTE_ON)


    def alert( self, level=WARNING ):
        '''Sound an alert for this cycle.  
           Call this method during refresh() service from wherever an alert 
           condition is detected.  For any instance, this method should
           be called no more than once during a refresh cycle.'''
        t = StatusDictionary.StatusDictionary['TELSTAT.UNIXTIME'].value()

        # do audio warning if needed
        if  level == WARNING:
            if  self.warnAudio != None and not self.mute and \
                t > self.warnAudioLastTime + self.warnMinInterval and \
                t < self.warnFirstTime + self.warnTimeOut:
                self.warnAudioLastTime  = t
                TelStat_cfg.audioPlayer.playAudio( self.warnAudio )
                if  self.warnFirstTime == _FIRST_TIME:
                    self.warnFirstTime = t
                #? if  self.warnTimeOut == 28:
                #?     print "t = %s, FirstTime = %s, Timeout = %s" % \
                #?         (t, self.warnFirstTime, self.warnTimeOut)
            # signal exit from alarm state, if any
            self.alarmAudioLastTime = 0
            self.alarmFirstTime = _FIRST_TIME

        # do audio alarm if needed
        elif  level == ALARM:
            if  self.alarmAudio != None and not self.mute and \
                t > self.alarmAudioLastTime + self.alarmMinInterval and \
                t < self.alarmFirstTime + self.alarmTimeOut:
                self.alarmAudioLastTime = t
                TelStat_cfg.audioPlayer.playAudio( self.alarmAudio )
                if  self.alarmFirstTime == _FIRST_TIME:
                    self.alarmFirstTime = t
            self.alarmLastTime = t      # last alarm call, with or without audio
            # signal exit from warning state
            self.warnAudioLastTime = 0
            self.warnFirstTime = _FIRST_TIME
            self.clearPending = True

        # take clear actions if needed
        elif  level == CLEAR:
            # signal exit from alarm and/or warning states
            self.warnFirstTime  = _FIRST_TIME
            self.alarmFirstTime = _FIRST_TIME

        # do audio clear if needed -- either WARNING or CLEAR level
        if  self.clearAudio != None and level != ALARM and \
            t > self.alarmLastTime + self.clearMinInterval and \
            t > self.clearAudioLastTime + self.clearMinInterval and \
            t < self.alarmLastTime + self.clearTimeOut and \
            self.clearPending:
            self.clearAudioLastTime = t
            TelStat_cfg.audioPlayer.playAudio( self.clearAudio )
            if  self.clearFirstTime == _FIRST_TIME:
                self.clearFirstTime = t
            # repeat clear message until time-out or cleared by alarm
            if  t > self.alarmLastTime + self.clearTimeOut:
                self.clearPending = False


    def setMinIntervals( self, warnMinInterval=None, alarmMinInterval=None,
                         clearMinInterval=None ):
        '''Set min interval\'s to new values.'''
        if  warnMinInterval != None and warnMinInterval > 0:
            self.warnMinInterval = warnMinInterval
        if  alarmMinInterval != None and alarmMinInterval > 0:
            self.alarmMinInterval = alarmMinInterval
        if  clearMinInterval != None and clearMinInterval > 0:
            self.clearMinInterval = clearMinInterval

    def setMute( self ):
        '''Turn sound off -- makes an alert to this object a no-op.'''
        self.mute = True

    def clearMute( self ):
        '''Turn sound back on.'''
        self.mute = False

    def resetFirstTime( self, level=WARNING ):
        '''Reset to be as though alert() never called for specified level.'''
        if  level == WARNING:
            self.warnFirstTime      = _FIRST_TIME
        elif  level == ALARM:
            self.alarmFirstTime     = _FIRST_TIME
        elif  level == CLEAR:
            self.clearFirstTime     = _FIRST_TIME

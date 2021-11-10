# AudioPlayer.py -- Bruce Bon -- 2006-12-04 16:39

# This module defines a class which will create a separate thread to
# play sound files without holding up GUI event service.  An AudioPlayer
# object maintain the background thread, which will stay alive until
# signaled to shut down.  The play method of the AudioPlayer object will
# queue sounds to be played by the background thread.  When the background
# thread has no sounds to play, it will poll at 1 Hz and sleep in between.

##############################################################################
################   import needed modules   ###################################
##############################################################################

import os
import os.path
import time
import threading
import TelStat_cfg
import TelStatLog
import StatusDictionary         # for time

##############################################################################
################   global variable and constant   ############################
##############################################################################

terminateFlag = False   # global so that setting True terminates ALL
                        # AudioPlayer threads, should there be more than one

AudioInfoDebug          = TelStat_cfg.AudioInfoBase
AudioErrDeviceFailure   = TelStat_cfg.AudioErrBase
AudioErrNoAudFiles      = TelStat_cfg.AudioErrBase + 1
AudioErrNoAudFile       = TelStat_cfg.AudioErrBase + 2
AudioErrNoDevice        = TelStat_cfg.AudioErrBase + 3

######################################################################
################   declare class for AudioPlayer   ###################
######################################################################

class AudioPlayer:

    def __init__( self ):
        '''Constructor.'''
        self.muteAllSounds = False
        self.soundQueue = []
        self.messageDict = {}
        self.dataLock = threading.RLock()
        #? TelStatLog.TelStatLog( TelStat_cfg.AudioInfoBase,
        #?      'INFO (AudioPlayer:__init__):  starting playerThread...', True )
        self.playerThread = threading.Thread( target=self.__playerThread )
        self.playerThread.start()
        if  not os.path.exists( TelStat_cfg.AU_DEV_PATH ):
            # no audio device, so can do nothing!
            TelStatLog.TelStatLog( AudioErrNoDevice,
                ("ERROR (AudioPlayer:__init__):  %s" % TelStat_cfg.AU_DEV_PATH)+
                " does not exist -- no audio will be played.")
            return
        if  TelStat_cfg.TELSTAT_AUDIO_DIRECTORY == None:
            # no audio files, so can do nothing!
            TelStatLog.TelStatLog( AudioErrNoAudFiles,
                "ERROR (AudioPlayer:__init__):  can't find audio files -- " +
                "no audio will be played.")

    def setMuteState(self, muteOn):
        self.muteAllSounds = muteOn

    def getMuteState(self):
        return self.muteAllSounds

    def playAudio( self, audio ):
        if  audio == None or audio == 'None':
            return
        if  not os.path.exists( audio ):
            # this audio file doesn't exist, so can do nothing!
            TelStatLog.TelStatLog( AudioErrNoAudFiles,
                "ERROR (AudioPlayer:playAudio):  can't find audio file `" +
                audio + "' -- no audio will be played.")
            return
        t = StatusDictionary.StatusDictionary['TELSTAT.UNIXTIME'].value()
        # make sure t is valid, if not make it a very large number
        if  t == None or t == 'None':
            t = 9999999999999.0         # greater than any actual time
        # test to see if it enough time passed since this message last played
        if  self.messageDict.has_key( audio ):
            playAudio = (t > self.messageDict[ audio ])
        else:
            playAudio = True
        # queue it and set minimum time for next play
        if (not self.muteAllSounds) and playAudio:
            # Following is for debugging, and should be disabled later
            TelStatLog.TelStatLog( AudioInfoDebug,
                "AudioPlayer.playAudio():  playing alert %s" % audio, True )
            if  t != 9999999999999.0:
                self.messageDict[ audio ] = t + TelStat_cfg.AudioMinInterval
            if  not self.playerThread.isAlive():   # make sure thread is alive
                self.playerThread.start()
            self.dataLock.acquire()
            self.soundQueue.append( audio )        # put to end of list
            self.dataLock.release()
        elif self.muteAllSounds:
            TelStatLog.TelStatLog( AudioInfoDebug,
                "AudioPlayer.playAudio(): Muted - NOT playing alert %s" % audio, True )
            

    def terminate( self ):
        global terminateFlag
        terminateFlag = True
        self.playerThread.join()

    def __playerThread( self ):
        '''Function to be executed in background thread, to play sounds.'''
        while not terminateFlag:    
            # Check terminateFlag and soundQueue
            audio = None
            self.dataLock.acquire()
            l = len(self.soundQueue)
            if  l > 0:
                audio = self.soundQueue.pop(0)  # get from beginning of list
            self.dataLock.release()

            if  audio == None:
                time.sleep( 1.0 )               # poll queue 1/second
            else:
                #if  not os.path.exists( TelStat_cfg.AU_DEV_PATH ) or \
                #    TelStat_cfg.TELSTAT_AUDIO_DIRECTORY == None:
                if  TelStat_cfg.TELSTAT_AUDIO_DIRECTORY == None:
                    continue    # no audio device or files, so do nothing!
                if  os.path.exists( TelStat_cfg.SOSS_AUDIO_PLAYER ):
                    cmd = TelStat_cfg.SOSS_AUDIO_PLAYER + " -exec %d %s %s" % \
                                   ( TelStat_cfg.SOSS_AUDIO_VOLUME, 
                                     TelStat_cfg.SOSS_AUDIO_CHANNELS, audio )
                elif  os.path.exists( TelStat_cfg.AU_SOX_PATH ):
                    # check the operating system and change the
                    # output file type
                    if os.uname()[0] == 'SunOS':
                        deviceFileType = "sunau"
                    elif os.uname()[0] == "Linux":
                        deviceFileType = "ossdsp"
                    cmd = '%s %s -t %s %s' % \
                     ( TelStat_cfg.AU_SOX_PATH, audio, deviceFileType, TelStat_cfg.AU_DEV_PATH )
                else:
                    cmd = 'cat %s > %s' % ( audio, TelStat_cfg.AU_DEV_PATH )
                #print "cmd is '%s'" % cmd
                os.system(cmd)
                continue
                # The above lines substituted because what follows interrupts
                # GUI service!!  Need to fix this, if we can!

                # Read the .au file
                auReadObj = open( audio, 'r' )
                audioString = auReadObj.read()
                auReadObj.close()

                # Open the audio device and play the sound
                try:
                    audioObj = sunaudiodev.open('w')
                except sunaudiodev.error:
                    TelStatLog.TelStatLog( AudioErrDeviceFailure,
                                "ERROR (AudioPlayer:__playerThread):  " +
                                "Failed to open Sun audio device.")
                else:
                    audioObj.write( audioString )
                    audioObj.close()

        #? TelStatLog.TelStatLog( TelStat_cfg.AudioInfoBase,
        #?     'INFO (AudioPlayer:terminate):  terminating playerThread...', True )
        return

######################################################################
################   test application   ################################
######################################################################

#?  Following for debugging only ############
if __name__ == '__main__':
    player = AudioPlayer()
    #time.sleep( 2.0 )

    player.playAudio( TelStat_cfg.E_WARNAZ )
    #print '.'; time.sleep( 0.5 ); print '.'; time.sleep( 0.5 ); print '.'; time.sleep( 0.5 ); print '.'; time.sleep( 0.5 ); print '_'; time.sleep( 0.5 )
    player.playAudio( TelStat_cfg.E_WARNROT )
    #print '.'; time.sleep( 0.5 ); print '.'; time.sleep( 0.5 ); print '.'; time.sleep( 0.5 ); print '.'; time.sleep( 0.5 ); print '_'; time.sleep( 0.5 )
    player.playAudio( TelStat_cfg.E_AGSTAR )
    #print '.'; time.sleep( 0.5 ); print '.'; time.sleep( 0.5 ); print '.'; time.sleep( 0.5 ); print '.'; time.sleep( 0.5 ); print '_'; time.sleep( 0.5 )
    player.playAudio( TelStat_cfg.E_TELMOVE )
    #print '.'; time.sleep( 0.5 ); print '.'; time.sleep( 0.5 ); print '.'; time.sleep( 0.5 ); print '.'; time.sleep( 0.5 ); print '_'; time.sleep( 0.5 )
    player.playAudio( TelStat_cfg.E_WARNHEL )
    #print '.'; time.sleep( 0.5 ); print '.'; time.sleep( 0.5 ); print '.'; time.sleep( 0.5 ); print '.'; time.sleep( 0.5 ); print '_'; time.sleep( 0.5 )
    player.playAudio( TelStat_cfg.E_CANCEL )
    #print '.'; time.sleep( 0.5 ); print '.'; time.sleep( 0.5 ); print '.'; time.sleep( 0.5 ); print '.'; time.sleep( 0.5 ); print '_'; time.sleep( 0.5 )
    player.playAudio( TelStat_cfg.E_ERRDBS )
    #print '.'; time.sleep( 0.5 ); print '.'; time.sleep( 0.5 ); print '.'; time.sleep( 0.5 ); print '.'; time.sleep( 0.5 ); print '_'; time.sleep( 0.5 )
    player.playAudio( TelStat_cfg.E_WARNWIND )
    time.sleep( 20.0 )
    player.terminate()

# MenuPane.py -- Bruce Bon -- 2008-08-26

# Display pane for Telescope Status pull-down menus

######################################################################
################   import needed modules   ###########################
######################################################################

import os
import sys
import time
import getpass

import Tkinter
from Tkconstants import *
import Pmw
import webbrowser

import TelStat_cfg
import TelStatLog
from DispType import *
import StatIO
import OSSC_screenPrintConversions

######################################################################
################   assign needed globals   ###########################
######################################################################

#print 'TELSTAT_MANUAL_URL = \n "' + TELSTAT_MANUAL_URL + '"'

MenuLogCloseMessage = TelStat_cfg.MenuInfoBase
MenuSwtchSrcMessage = TelStat_cfg.MenuInfoBase + 1
MenuStatLogMessage  = TelStat_cfg.MenuInfoBase + 2
MenuMuteAllSoundsMessage  = TelStat_cfg.MenuInfoBase + 3

######################################################################
################   declare classes for the panes   ###################
######################################################################

# Telescope Status Menu Bar Pane class
class MenuPane(Tkinter.Frame):
    parent = 0

    def resize( self ):
        """Resize this pane."""
        pass    # for now

    def rePack( self ):
        """First resize, then re-place this pane.
           This should ONLY be called if this pane is used in a top-level
              geometry pane, NOT if it is a page in a Notebook."""
        self.resize()
        self.pack( anchor=NW)

    def __init__( self, parent, 
                  toggleRefreshCB, stepCB, setDelayCB, sizesCB, terminateCB,
                  myName="" ):
        """Telescope Pointing Status Pane constructor."""
        Tkinter.Frame.__init__(self, parent, class_="MenuPane", \
            borderwidth=TelStat_cfg.paneBorderWidth, 
            relief=TelStat_cfg.paneBorderRelief)
        self.parent             = parent
        self.myName             = myName
        self.toggleRefreshCB    = toggleRefreshCB
        self.stepCB             = stepCB
        self.setDelayCB         = setDelayCB
        self.sizesCB            = sizesCB
        self.terminateCB        = terminateCB
        self["bg"]              = "CadetBlue"
        self.createWidgets()
#?      print "\n", self, " options:\n", self.config()  # debug


    def toggleTelRay( self ):
        if  TelStat_cfg.TelPaneRayDisplay:
            TelStat_cfg.TelPaneRayDisplay = False
            self.optionsMenu.delete( self.optTelRayNdx )
            self.optionsMenu.insert_command( self.optTelRayNdx,
               label='Turn Prototype Light Path On', 
               command=self.toggleTelRay )
        else:
            TelStat_cfg.TelPaneRayDisplay = True
            self.optionsMenu.delete( self.optTelRayNdx )
            self.optionsMenu.insert_command( self.optTelRayNdx,
               label='Turn Prototype Light Path Off', 
               command=self.toggleTelRay )

    def setRefreshDelay10( self ):
        self.setDelayCB( 10 )

    def setRefreshDelay400( self ):
        self.setDelayCB( 400 )

    def setRefreshDelay1000( self ):
        self.setDelayCB( 1000 )

    def setRefreshDelay2000( self ):
        self.setDelayCB( 2000 )

    def setRefreshDelay5000( self ):
        self.setDelayCB( 5000 )

    def setRefreshDelay10000( self ):
        self.setDelayCB( 10000 )

    def setRefreshDelay20000( self ):
        self.setDelayCB( 20000 )

    def toggleDataLogging( self ):
        if  TelStat_cfg.telStatDataLogging:
            # Turn data logging off
            TelStat_cfg.telStatDataLogging = False
            if  TelStat_cfg.telStatDataLog_fd != None:
                TelStat_cfg.telStatDataLog_fd.close()
                TelStat_cfg.telStatDataLog_fd = None
                TelStatLog.TelStatLog( MenuLogCloseMessage, 
                    '(MenuPane:toggleDataLogging): ' +
                    'Turned data logging off and closed log file', True )
            self.optionsMenu.delete( self.optDataLogNdx )
            self.optionsMenu.insert_command( self.optDataLogNdx,
                label='Turn Data Logging On', 
                command=self.toggleDataLogging )
        else:
            # Turn data logging on
            TelStat_cfg.telStatDataLogging = True
            self.optionsMenu.delete( self.optDataLogNdx )
            self.optionsMenu.insert_command( self.optDataLogNdx,
                label='Turn Data Logging Off', 
                command=self.toggleDataLogging )

    def testSound( self ):
        """Play several of our alerts in a row, ending with an OK alert."""
        if  not TelStat_cfg.audioPlayer:
            TelStat_cfg.audioPlayer = AudioPlayer.AudioPlayer()
        TelStat_cfg.audioPlayer.playAudio( TelStat_cfg.AU_WARN_LOW_TEMP )
        TelStat_cfg.audioPlayer.playAudio( TelStat_cfg.AU_ALARM_HIGH_HUMID )
        TelStat_cfg.audioPlayer.playAudio( TelStat_cfg.AU_ALARM_HIGH_WIND )
        TelStat_cfg.audioPlayer.playAudio( TelStat_cfg.AU_ALERT_ENV_OK )
        TelStat_cfg.audioPlayer.playAudio( TelStat_cfg.AU_ALERT_ENV_OK30 )

    def muteAllSounds( self ):
        TelStatLog.TelStatLog( MenuMuteAllSoundsMessage, 
                               'muteAllSounds called %d'%self.muteAllSoundsValue.get(), True )
        if TelStat_cfg.audioPlayer:
            if self.muteAllSoundsValue.get() == 0:
                TelStatLog.TelStatLog( MenuMuteAllSoundsMessage, 
                                       'muteAllSounds setting mute to False', True )
                TelStat_cfg.audioPlayer.setMuteState(False)
            elif self.muteAllSoundsValue.get() == 1:
                TelStatLog.TelStatLog( MenuMuteAllSoundsMessage, 
                                       'muteAllSounds setting mute to True', True )
                TelStat_cfg.audioPlayer.setMuteState(True)

    def restartReplay( self ):
        if  OSSC_screenPrintConversions.replayFile != None:
            if   not OSSC_screenPrintConversions.replayFile.closed:
                OSSC_screenPrintConversions.replayFile.close()
            OSSC_screenPrintConversions.replayFile = None

    def alarmcondition ( self ):        
        Test = Pmw.MessageDialog( self.parent,
                title = 'Test',
                buttons = ('Close',),  defaultbutton = 0, message_text = 
                'Test (Alarm Condition Dialog).' )
        result = Test.show()

    def debugToggleRefresh( self ):
        self.toggleRefreshCB()

    def debugStep( self ):
        self.stepCB()

    def debugSizes( self ):
        self.sizesCB()

    def logDict( self ):
        # Find time tag and use for file name construction
        timeTuple  = time.localtime()
        timeString = '%d_%02d_%02d_%02d%02d%02d' % \
                     ( timeTuple[0], timeTuple[1], timeTuple[2],
                       timeTuple[3], timeTuple[4], timeTuple[5] )
        dictFileName = TelStat_cfg.TELSTAT_LOG_ROOT_DIR + '/TelStatDict_' + \
                            getpass.getuser() + '_' + timeString + '.log'
        TelStatLog.TelStatLog( MenuStatLogMessage, 
          '(MenuPane:logDict): Logging StatusDictionary to '+dictFileName, True)
        print '(MenuPane:logDict): Logging StatusDictionary to '+ dictFileName
        fp = open( dictFileName, 'w' )
        os.chmod( dictFileName, 0644 )
        fp.write( "TelStat Dictionary Dump, %s, %s mode\n" % \
                  (timeString,TelStat_cfg.telstatMode) )
        StatIO.StatIO_printDict( fp )
        fp.close()

    def debugReplaySamplePeriod( self ):
        self.debugReplayDialog = Pmw.PromptDialog( self.parent,
                title      = 'Set Replay Sample Period',
                label_text = 'Replay Sample Period (records)',
                entryfield_labelpos = 'n',
                defaultbutton = 0,
                command    = self.debugReplaySamplePeriodCB )
        self.RSPentry = self.debugReplayDialog.component( 'entryfield' )
        # initialize entry to contain current value
        self.RSPentry.insert( 0, `TelStat_cfg.replaySamplePeriod` )
        # allow only integer entries of 1 or greater
        self.RSPentry['validate'] = {'validator':'numeric','min':1}
        self.debugReplayDialog.show()


    def debugReplaySamplePeriodCB( self, result ):
        result = self.debugReplayDialog.get()
        if  result != "":
            TelStat_cfg.replaySamplePeriod = int( result )
        self.debugReplayDialog.destroy()
        #TelStat_cfg.replaySamplePeriod

    def terminateWindow( self ):
        self.terminateCB()

        
    def helpManual( self ):
        manHelp = Pmw.TextDialog( self.parent,
             scrolledtext_labelpos = 'n',
             title = 'TelStat Manual', 
             label_text = 'TelStat version ' + \
                          TelStat_cfg.TELSTAT_VERSION + ', On-line Manual',
             buttons = ('Close',),  defaultbutton = 0 )
        #manHelp.scrolledtext_text.height = 45  # doesn't work!!
        f = open( TelStat_cfg.TELSTAT_MANUAL_HLP, 'r' )
        l = f.readline()
        while l:
            manHelp.insert( 'end', l )
            l = f.readline()
        f.close()
        manHelp.configure( text_state = 'disabled' )
        result = manHelp.show()
#?1     manHelp = Pmw.MessageDialog( self.parent,
#?1             title = 'Manual Help',
#?1             buttons = ('Close',),  message_text = 
#?1             'The On-line Manual is not yet available.' )
#?1     result = manHelp.show()
#?0     webbrowser.open( TELSTAT_MANUAL_URL, autoraise=True )

        
    def helpAlerts( self ):
        alertsHelp = Pmw.TextDialog( self.parent,
             scrolledtext_labelpos = 'n',
             title = 'TelStat Alerts Reference',
             label_text = 'TelStat version ' + TelStat_cfg.TELSTAT_VERSION + \
                          ', Alerts Reference',
             buttons = ('Close',),  defaultbutton = 0 )
        #alertsHelp.scrolledtext_text.height = 45       # doesn't work!!
        f = open( TelStat_cfg.TELSTAT_ALERTS_HLP, 'r' )
        l = f.readline()
        while l:
            alertsHelp.insert( 'end', l )
            l = f.readline()
        f.close()
        alertsHelp.configure( text_state = 'disabled' )
        result = alertsHelp.show()

    def helpClose( self ):
        closeHelp = Pmw.MessageDialog( self.parent,
                title = 'Options Help',
                buttons = ('Close',),  defaultbutton = 0, message_text = 
                'The Close menu allows termination of this window.' )
        result = closeHelp.show()

    def helpOptions( self ):
        optionsHelp = Pmw.TextDialog( self.parent,
             scrolledtext_labelpos = 'n',
             title = 'TelStat Options Help',
             label_text = 'TelStat version ' + TelStat_cfg.TELSTAT_VERSION + \
                          ', Options Help',
             buttons = ('Close',),  defaultbutton = 0 )
        #optionsHelp.scrolledtext_text.height = 45      # doesn't work!!
        f = open( TelStat_cfg.TELSTAT_OPTIONS_HLP, 'r' )
        l = f.readline()
        while l:
            optionsHelp.insert( 'end', l )
            l = f.readline()
        f.close()
        optionsHelp.configure( text_state = 'disabled' )
        result = optionsHelp.show()

    def helpDebug( self ):
        debugHelp = Pmw.TextDialog( self.parent,
             scrolledtext_labelpos = 'n',
             title = 'TelStat Debug Help',
             label_text = \
              'TelStat version ' + TelStat_cfg.TELSTAT_VERSION + ', Debug Help',
             buttons = ('Close',),  defaultbutton = 0 )
        #debugHelp.scrolledtext_text.height = 45        # doesn't work!!
        f = open( TelStat_cfg.TELSTAT_DEBUG_HLP, 'r' )
        l = f.readline()
        while l:
            debugHelp.insert( 'end', l )
            l = f.readline()
        f.close()
        debugHelp.configure( text_state = 'disabled' )
        result = debugHelp.show()

    def helpLightPath( self ):
        lightpathHelp = Pmw.TextDialog( self.parent,
             scrolledtext_labelpos = 'n',
             title = 'TelStat Lightpath Help',
             label_text = 'TelStat version ' + TelStat_cfg.TELSTAT_VERSION + \
                          ', Lightpath Help',
             buttons = ('Close',),  defaultbutton = 0 )
        #lightpathHelp.scrolledtext_text.height = 45    # doesn't work!!
        f = open( TelStat_cfg.TELSTAT_LIGHTPATH_HLP, 'r' )
        l = f.readline()
        while l:
            lightpathHelp.insert( 'end', l )
            l = f.readline()
        f.close()
        lightpathHelp.configure( text_state = 'disabled' )
        result = lightpathHelp.show()


    def helpScaleChange( self ):
        scaleHelp = Pmw.MessageDialog( self.parent,
                title = 'Scale Change Help',
                buttons = ('Close',),  defaultbutton = 0, message_text = 
                'The horizontal scale of any of the graphs may be changed by ' +
                '\nmoving the mouse pointer over the graph and double-clicking.' +
                '\n\nTo expand the scale, double-click the left ' +
                'mouse button.\nTo shrink the scale, double-click ' +
                'the middle mouse button.' )
        result = scaleHelp.show()

    def helpAbout( self ):
        Pmw.aboutversion( 
         TelStat_cfg.TELSTAT_VERSION + '   ' + TelStat_cfg.TELSTAT_DATE + '\n' )
        Pmw.aboutcontact( 
                'Brought to you by the Subaru Software Development Group\n' +
                'Bruce Bon, Arne Grimstrup, Takeshi Inagaki\n' +
                'National Astronomical Observatory of Japan\n' +
                'Subaru Telescope\nHilo, Hawaii\n\n' +
                'Alerts spoken by Heidi Van der Veer' )
        about = Pmw.AboutDialog( self.parent, 
                applicationname = 'Subaru Telescope Status Window' )

    def helpReleaseNotes( self ):
        manRelNotes = Pmw.TextDialog( self.parent,
             scrolledtext_labelpos = 'n',
             title = 'TelStat Release Notes', 
             label_text = 'TelStat version ' + \
                          TelStat_cfg.TELSTAT_VERSION + ', Release Notes',
             buttons = ('Close',),  defaultbutton = 0 )
        #manRelNotes.scrolledtext_text.height = 45      # doesn't work!!
        f = open( TelStat_cfg.TELSTAT_RELEASENOTES_HLP, 'r' )
        l = f.readline()
        while l:
            manRelNotes.insert( 'end', l )
            l = f.readline()
        f.close()
        manRelNotes.configure( text_state = 'disabled' )
        result = manRelNotes.show()

    def createWidgets( self ):
        """Create widgets for MenuPane."""

        self.menuBar    = Tkinter.Menu(self.parent)

        # Create Close menu
        self.closeMenu = Tkinter.Menu(self.menuBar, tearoff=0)
        self.closeMenu.add_command(label="Close", command=self.terminateWindow)

        # Create Options menu
        self.optionsMenu = Tkinter.Menu(self.menuBar, tearoff=0)
        optNdx = 0
        # Telescope ray option
        if  TelStat_cfg.TelPaneRayDisplay:
            self.optionsMenu.add_command(               \
               label='Turn Prototype Light Path Off', 
               command=self.toggleTelRay )
        else:
            self.optionsMenu.add_command(               \
               label='Turn Prototype Light Path On', 
               command=self.toggleTelRay )
        self.optTelRayNdx       = optNdx                # index
        optNdx += 1
        
        self.optionsMenu.add_command(
            label='Set refresh delay = 1.0 sec', 
            command=self.setRefreshDelay1000 )
        self.optRef1Ndx     = optNdx                # index
        optNdx += 1
        self.optionsMenu.add_command(
            label='Set refresh delay = 2.0 sec', 
            command=self.setRefreshDelay2000 )
        self.optRef2Ndx     = optNdx                # index
        optNdx += 1
        self.optionsMenu.add_command(
            label='Set refresh delay = 5.0 sec', 
            command=self.setRefreshDelay5000 )
        self.optRef5Ndx = optNdx                        # index
        optNdx += 1
        self.optionsMenu.add_command(
            label='Set refresh delay = 10.0 sec', 
            command=self.setRefreshDelay10000 )
        self.optRef10Ndx = optNdx                       # index
        optNdx += 1
        self.optionsMenu.add_command(
            label='Set refresh delay = 20.0 sec', 
            command=self.setRefreshDelay20000 )
        self.optRef20Ndx = optNdx                       # index
        optNdx += 1

        if  not TelStat_cfg.replayFlag:
            # Data logging option, a toggle
            if  TelStat_cfg.telStatDataLogging:
                # Data logging initially off
                self.optionsMenu.add_command(         \
                   label='Turn Data Logging Off', 
                   command=self.toggleDataLogging )
            else:
                # Data logging initially on
                self.optionsMenu.add_command(         \
                   label='Turn Data Logging On', 
                   command=self.toggleDataLogging )
            self.optDataLogNdx = optNdx                 # index
            optNdx += 1

        self.optionsMenu.add_command(
            label='Test sound', 
            command=self.testSound )
        self.optTestSndNdx = optNdx                     # index
        optNdx += 1

        self.muteAllSoundsValue = Tkinter.IntVar()
        if TelStat_cfg.audioPlayer:
            TelStatLog.TelStatLog( MenuMuteAllSoundsMessage, 
                                   'audioPlayer exists', True )
            if TelStat_cfg.audioPlayer.getMuteState():
                self.muteAllSoundsValue.set(1)
            else:
                self.muteAllSoundsValue.set(0)
        else:
            TelStatLog.TelStatLog( MenuMuteAllSoundsMessage, 
                                   'audioPlayer does not exist', True )
        self.optionsMenu.add_checkbutton(
            label='Mute all sounds', 
            command=self.muteAllSounds, variable = self.muteAllSoundsValue )
        self.optMuteAllSoundsNdx = optNdx                     # index
        optNdx += 1

        # Create Debug menu -- only if debugging turned on
        if  TelStat_cfg.debugFlag or TelStat_cfg.replayFlag:
            self.debugMenu = Tkinter.Menu(self.menuBar, 
                title = 'Debug Menu', tearoff=1)
            dbgNdx = 1          # because of tearoff?
            self.debugMenu.add_command(
                label='Toggle refresh', command=self.debugToggleRefresh )
            self.dbgTogRfrshNdx = dbgNdx                # index
            dbgNdx += 1
            self.debugMenu.add_command(
                label='Single step', command=self.debugStep )
            self.dbgSnglStepNdx = dbgNdx                # index
            dbgNdx += 1
            self.debugMenu.add_command(
                label='Set refresh delay = 0.01 sec', 
                command=self.setRefreshDelay10 )
            self.dbgRefp01Ndx   = dbgNdx                # index
            dbgNdx += 1
            self.debugMenu.add_command(
                label='Set refresh delay = 0.4 sec', 
                command=self.setRefreshDelay400 )
            self.dbgRefp4Ndx    = dbgNdx                # index
            dbgNdx += 1

            if  TelStat_cfg.replayFlag:
                self.debugMenu.add_command(
                    label='Set replay sample period', 
                    command=self.debugReplaySamplePeriod )
                self.dbgReplayPerNdx = dbgNdx           # index
                dbgNdx += 1
            self.debugMenu.add_command(
                label='Log dictionary', command=self.logDict )
            self.dbgLogDictNdx        = dbgNdx          # index
            dbgNdx += 1
            self.debugMenu.add_command(
                label='Print geometry', command=self.debugSizes )
            self.dbgPrintGeomNdx        = dbgNdx        # index
            dbgNdx += 1
            self.debugMenu.add_command( 
               label="Alarm Condition Dialog", command=self.alarmcondition )
            self.dbgAlarmDialogNdx      = dbgNdx        # index
            dbgNdx += 1


        # Create Help menu
        self.helpMenu = Tkinter.Menu( self.menuBar, tearoff=0, name='help' )
        self.helpMenu.add_command( label="Manual", command=self.helpManual )
        self.helpMenu.add_command( label="Alerts", command=self.helpAlerts )
        self.helpMenu.add_separator()
        self.helpMenu.add_command( label="Close help", command=self.helpClose )
        self.helpMenu.add_command(
            label="Options help", command=self.helpOptions)
        if  TelStat_cfg.debugFlag or TelStat_cfg.replayFlag:
            self.helpMenu.add_command( 
                label="Debug help", command=self.helpDebug )
        self.helpMenu.add_command( 
                label="Lightpath Help", command=self.helpLightPath )
        self.helpMenu.add_command(
                label="Scale-change help", command=self.helpScaleChange )
        self.helpMenu.add_separator()
        self.helpMenu.add_command( label="About", command=self.helpAbout )
        self.helpMenu.add_command( label="Release Notes", 
                                   command=self.helpReleaseNotes)

        self.menuBar.add_cascade(label='Close', menu=self.closeMenu)
        self.menuBar.add_cascade(label='Options', menu=self.optionsMenu)
        if  TelStat_cfg.debugFlag or TelStat_cfg.replayFlag:
            self.menuBar.add_cascade(label='Debug', menu=self.debugMenu )
        self.menuBar.add_cascade(label='Help', menu=self.helpMenu)

        self.parent.config(menu=self.menuBar)


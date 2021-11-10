#! /usr/local/bin/python
#  TrackingPane.py
#  Arne Grimstrup
#  2003-09-29
#  Modified 2007-12-28 Bruce Bon

#  This module implements the tracking status display pane.

from Tkinter import *      # UI widgets and event loop infrastructure
from StatIO import *       # Status I/O functions
from DispType import *     # Status display data types
from TelStat_cfg import *  # Display configuration
from TelStatLog import *   # Log infrastructure
from Alert import *        # Alert infrastructure

import StatusDictionary as SD

import types               # for type names
import time                # System time functions

import Pmw                 # Additional UI widgets 
import LineGraph           # Strip chart widgets
import ErrorWidget         # Scatter plot widget
import StateWidget         # State display widget

TrackErrInvalidAgBrightness    = TrackErrBase+1
TrackErrUnknownTrackStatus     = TrackErrBase+2
TrackErrInvalidSvBrightness    = TrackErrBase+3
TrackErrInvalidAgSeeing        = TrackErrBase+4
TrackErrInvalidSvSeeing        = TrackErrBase+5
TrackErrInvalidExposure        = TrackErrBase+6
TrackErrInvalidAgProbe         = TrackErrBase+7
TrackErrUndefAgValue           = TrackErrBase+8
TrackErrUndefSvValue           = TrackErrBase+9

#  Text and color pairs for each autoguiding state.
TrackingStates = [('Unknown',    PANECOLORREDALARMBACKGROUND),
                  ('Pointing',   PANECOLORMEDGREENBACKGROUND),
                  ('Slewing',    PANECOLORYELLOWWARNBACKGROUND),
                  ('Tracking',   PANECOLORMEDGREENBACKGROUND),
                  ('AG Guiding', PANECOLORMEDGREENBACKGROUND),
                  ('AG Guiding', PANECOLORYELLOWWARNBACKGROUND),
                  ('AG Guiding', PANECOLORREDALARMBACKGROUND),
                  ('SV Guiding', PANECOLORMEDGREENBACKGROUND),
                  ('SV Guiding', PANECOLORYELLOWWARNBACKGROUND),
                  ('SV Guiding', PANECOLORREDALARMBACKGROUND),
                  ('NS Guiding', PANECOLORMEDGREENBACKGROUND),
                  ('NS Guiding', PANECOLORYELLOWWARNBACKGROUND),
                  ('NS Guiding', PANECOLORREDALARMBACKGROUND)]

# Exposure time value is reported for both the autoguider and the slit viewer
EXPNUMFORMAT  = "%9d"
EXPFORMAT     = "Exptime (AG): %s ms\t(SV): %s ms"

# AG probe radius and angle is reported to indicate current and intended position
AGFORMAT = " AG Probe %8.1f mm / %8s deg\n(Command) %8.1f mm / %8s deg"
AGFORMAT_PF = " AG Probe %8.1f mm / %8.1f mm\n(Command) %8.1f mm / %8.1f mm"
AGFORMAT_PIR = " AG Probe %8.1f mm\n(Command) %8.1f mm"

# Detector threshold is reported as upper and lower bounds
THRESFORMAT = "Threshold  %5d / %5d"

class TrackingPane(Frame, StatPaneBase):
    def __init__(self, parent, logger, pfgcolor=TRACKPANEFOREGROUND, pbgcolor=TRACKPANEBACKGROUND, pfont=TRACKPANETEXTFONT):
  
        self.logger=logger
        """Create an instance of the tracking status display pane."""

        # Configure the base frame to default values
        Frame.__init__(self, parent)

        # The tracking status pane consists of a tracking status banner, a scatter plot of autoguider error
        # plots, strip charts for guide star brightness and seeing conditions, and displays of guide camera
        # exposure times, positions of the guide probe, and detector thresholds.
        # Register the status symbols we need to plot the values
        StatPaneBase.__init__(self, 
            ('TELSTAT.FOCUS', 'TSCL.AG1dX', 'TSCL.AG1dY', 'TSCL.AG1Intensity', 
             'TSCS.EL', 'TSCV.AGPIRCCalc', 'TSCV.AGFMOSCCalc', 
             'TSCL.AGPIRIntensity', 'TSCL.AGFMOSIntensity',
             'TSCL.AGPIRStarSize', 'TSCL.AGFMOSStarSize',
             'TSCL.AGPIRdX', 'TSCL.AGPIRdY', 'TSCV.AGPIRExpTime',
             'TSCL.AGFMOSdAZ', 'TSCL.AGFMOSdEL', 'TSCV.AGFMOSExpTime',
             'TSCV.HSC.SCAG.CCalc', 'TSCL.HSC.SCAG.Intensity',
             'TSCL.HSC.SCAG.StarSize', 'TSCL.HSC.SCAG.DX', 'TSCL.HSC.SCAG.DY',
             'TSCV.HSC.SCAG.ExpTime', 'TSCL.HSC.SCAG.dAZ', 'TSCL.HSC.SCAG.dEL',
             'TSCV.HSC.SHAG.CCalc', 'TSCL.HSC.SHAG.Intensity',
             'TSCL.HSC.SHAG.StarSize', 'TSCL.HSC.SHAG.DX', 'TSCL.HSC.SHAG.DY',
             'TSCV.HSC.SHAG.ExpTime', 'TSCL.HSC.SHAG.dAZ', 'TSCL.HSC.SHAG.dEL',
             'VGWD.FWHM.AG', 'VGWD.FWHM.SV', 'TSCV.AGExpTime', 'TSCV.SVExpTime',
             'TSCV.AGR','TSCV.AGTheta', 'STATL.AG_R_CMD', 'STATL.AG_THETA_CMD', 
             'TSCL.AGPF_X', 'TSCL.AGPF_Y', 'TSCL.AGPF_X_CMD', 'TSCL.AGPF_Y_CMD',
             'STATL.AG1_I_BOTTOM', 'STATL.AG1_I_CEIL', 'STATL.SV_CALC_MODE', 
             'STATL.SV1_I_BOTTOM', 'STATL.SV1_I_CEIL', 'STATL.AGRERR', 
             'TELSTAT.UNIXTIME', 'TSCL.SV1Intensity', 'STATL.SVRERR', 
             'STATL.TELDRIVE', 'TELSTAT.TELDRIVE', 'TELSTAT.SLEWING',
             'AON.TT.TTX', 'AON.TT.TTY', 'AON.TT.WTTC1', 'AON.TT.WTTC2', 'FITS.AON.OBS_ALOC', 'FITS.IRC.OBS_ALOC', 'FITS.HIC.OBS_ALOC', 'FITS.K3D.OBS_ALOC' ), 
            'TrackingPane')

        # Establish the main background color
        self.configure(bg=pbgcolor)

        # Create the status banner and "lost guide star" alert
        self.state = StateWidget.StateWidget(self, 'Unknown', PANECOLORREDALARMBACKGROUND, TRACKPANESTATUSSIZE, TRACKPANESTATUSFONT_GEN2)

        self.state.grid(row=0,column=0)
        self.guideStarLostAlert  = AudioAlert( warnAudio=None,
                        alarmAudio=AU_ALARM_GUIDE_STAR_LOST, alarmMinInterval=30 )

  
        self.ins_obs='Observation'
        # Create the scatter plot
        try:
            self.ao=SD.StatusDictionary['FITS.AON.OBS_ALOC'].format()
            self.ircs=SD.StatusDictionary['FITS.IRC.OBS_ALOC'].format()
            self.hiciao=SD.StatusDictionary['FITS.HIC.OBS_ALOC'].format()
            self.k3d=SD.StatusDictionary['FITS.K3D.OBS_ALOC'].format()
        except Exception:
            self.ao=self.ircs=self.hiciao=self.k3d=None           

        if self.ao==self.ins_obs and (self.ircs==self.ins_obs or self.hiciao==self.ins_obs or self.k3d==self.ins_obs):
            self.error = ErrorWidget.ErrorWidgetAO(self, psize=TRACKPANEERRORPLOTSIZE, pscale=TRACKPANEPLOTSCALE,  pgrid=TRACKPANEPLOTSHOWGRID, pbcolor=TRACKPANEPLOTCOLOR, pointcfg=TRACKPANEPLOTTGT,linger=TRACKPANEERRORLINGER, logger=logger)
        else:
            self.error = ErrorWidget.ErrorWidget(self, psize=TRACKPANEERRORPLOTSIZE,
                                            pscale=TRACKPANEPLOTSCALE,
                                            pgrid=TRACKPANEPLOTSHOWGRID,
                                            pbcolor=TRACKPANEPLOTCOLOR,
                                            pointcfg=TRACKPANEPLOTTGT,
                                            linger=TRACKPANEERRORLINGER,
                                            logger=logger)        


        self.error.grid(row=1,column=0)

        self.laststate = 0
        self.lasterrplot = 0
        
        # Create the brightness graph
        self.bright = LineGraph.LineGraph(self, size=(120,TRACKPANELINEPLOTSIZE), gconfig=TRACKPANEBRIGHTGRAPH,
                                          lconfig=TRACKPANEBRIGHTLINES)
        self.bright.grid(row=2,column=0)

        # Create the seeing graph
        self.seeing = LineGraph.LineGraph(self, size=(120,TRACKPANELINEPLOTSIZE), gconfig=TRACKPANESEEGRAPH,
                                          lconfig=TRACKPANESEELINES)
        self.seeing.grid(row=3,column=0)
        self.seeerr = 0

        # Create the exposure time displays
        self.ExpLabelText = StringVar()
        self.ExpLabelText.set(EXPFORMAT % (0,0))
        self.ExpLabel = Label(self, font=pfont, textvariable=self.ExpLabelText, fg=pfgcolor, bg=pbgcolor)
        self.ExpLabel.grid(row=4,column=0)
        self.exptimeerr = 0

        # Create the probe position displays
        self.AGProbeLabelText = StringVar()
        self.AGProbeLabelText.set(AGFORMAT % (0.0,0.0,0.0,0.0))
        self.AGProbeLabel = Label(self, font=pfont, textvariable=self.AGProbeLabelText, fg=pfgcolor, bg=pbgcolor)
        self.AGProbeLabel.grid(row=5,column=0)
        self.agprobeerr = 0

        # Create the detector threshold displays
        self.ThresLabelText = StringVar()
        self.ThresLabelText.set(THRESFORMAT % (0,0))
        self.ThresLabel = Label(self, font=pfont, textvariable=self.ThresLabelText, fg=pfgcolor, bg=pbgcolor)
        self.ThresLabel.grid(row=6,column=0)
        self.thresholderr = 0

    def get_alloc_observation(self):

        timeout=20
        cur_time = time.time()
        end_time = cur_time + timeout

        found=False
        vals=[]
        # monitoring threads
        while cur_time < end_time and not found:
            try:
                ao=SD.StatusDictionary['FITS.AON.OBS_ALOC'].format()
                ircs=SD.StatusDictionary['FITS.IRC.OBS_ALOC'].format()
                hiciao=SD.StatusDictionary['FITS.HIC.OBS_ALOC'].format()
                found=True
                vals.extend([ao, ircs, hiciao]) 
            except Exception as e:
                print 'not yet found'

            time.sleep(0.2)
            cur_time = time.time()
         
        return vals        


    def checkBrightValue(self, bright):
        """Determine the brightness graph's state from the given value."""
        if bright < 0 or bright > 999999:
            self.bright.newbackground(PANECOLORREDALERTFOREGROUND)
            return 0
        else:
            if bright == 0 and self.bright.nowbackground() != PANECOLORYELLOWALERTFOREGROUND:
                self.bright.newbackground(PANECOLORYELLOWALERTFOREGROUND)
            elif bright > 0 and self.bright.nowbackground() != ENVPANEBACKGROUND:
                self.bright.newbackground(ENVPANEBACKGROUND)
            return 1

    def checkSeeingValue(self, see):
        """Determine the brightness graph's state from the given value."""
        if see >= 0.0:
            if self.seeing.nowbackground() != TRACKPANEBACKGROUND:
                self.seeing.newbackground(TRACKPANEBACKGROUND)
            return 1
        else:
            self.seeing.newbackground(PANECOLORREDALERTFOREGROUND)
            return 0

    def refresh(self, dict):
        """Update the plot with new values."""

        # Record the timestamp for the strip charts
        t = dict['TELSTAT.UNIXTIME'].value()

        ag = sv = agfmos = agpir = agHscSc = agHscSh =False
        
        # Determine the autoguider status values
        valCosEl       = 1.0
        valFocus       = dict['TELSTAT.FOCUS'].value()
        valTeldrive    = dict['TELSTAT.TELDRIVE'].value()
        valTeldrStr    = dict['STATL.TELDRIVE'].value()
        valAgIntensity = valSvIntensity = None
        valExpTimeAG   = valExpTimeSV   = None
        valBottom    = None
        valCeiling   = None
        if  valFocus == FOCUS_PF_IR:
            valCosEl    = dict['TSCS.EL'].cos()
            if  dict['TSCV.AGPIRCCalc'].value() == 0x04:
                valAG = 1
                valAgIntensity = dict['TSCL.AGPIRIntensity'].value()
                valExpTimeAG   = dict['TSCV.AGPIRExpTime'].value()
                valBottom      = dict['TSCV.AGPIR_I_BOTTOM'].value()
                valCeiling     = dict['TSCV.AGPIR_I_CEIL'].value()
                agpir = True
            elif  dict['TSCV.AGFMOSCCalc'].value() == 0x04:
                valAG = 2
                valAgIntensity = dict['TSCL.AGFMOSIntensity'].value()
                valExpTimeAG   = dict['TSCV.AGFMOSExpTime'].value()
                agfmos = True
                # valBottom = valCeiling = None
            else:
                # if neither above applies, we have an undefined state!
                valAG = UNDEF
                valAgIntensity = UNDEF
                valExpTimeAG   = UNDEF
        elif  valFocus == FOCUS_PF_OPT2:
            valCosEl    = dict['TSCS.EL'].cos()
            if  dict['TSCV.HSC.SHAG.CCalc'].value() == 0x04:
                valAG = 4
                valAgIntensity = dict['TSCL.HSC.SHAG.Intensity'].value()
                valExpTimeAG   = dict['TSCV.HSC.SHAG.ExpTime'].value()
                valBottom      = dict['TSCV.HSC.SHAG.I_BOTTOM'].value()
                valCeiling     = dict['TSCV.HSC.SHAG.I_CEIL'].value()
                agHscSh = True
            elif  dict['TSCV.HSC.SCAG.CCalc'].value() == 0x04:
                valAG = 3
                valAgIntensity = dict['TSCL.HSC.SCAG.Intensity'].value()
                valExpTimeAG   = dict['TSCV.HSC.SCAG.ExpTime'].value()
                # valBottom = valCeiling = None
                agHscSc = True
            else:
                # if neither above applies, we have an undefined state!
                valAG = UNDEF
                valAgIntensity = UNDEF
                valExpTimeAG   = UNDEF
        else:
            valAG = None
            valAgIntensity = dict['TSCL.AG1Intensity'].value()
            valExpTimeAG   = dict['TSCV.AGExpTime'].value()
            if  valTeldrive == TELDRIVE_GUIDE_AG or \
                valTeldrive == TELDRIVE_GUIDE_AG1 or \
                valTeldrive == TELDRIVE_GUIDE_AG2:
                valBottom  = dict['STATL.AG1_I_BOTTOM'].value()
                valCeiling = dict['STATL.AG1_I_CEIL'].value()
            elif  valTeldrive > TELDRIVE_GUIDE_AG2:
                valBottom  = dict['STATL.SV1_I_BOTTOM'].value()
                valCeiling = dict['STATL.SV1_I_CEIL'].value()
        valSvIntensity = dict['TSCL.SV1Intensity'].value()
        valExpTimeSV   = dict['TSCV.SVExpTime'].value()
        valSlew        = dict['TELSTAT.SLEWING'].value()
        valSvCalc      = dict['STATL.SV_CALC_MODE'].value()

        # If it is defined and a string and we're in an SV mode,
        #   append valSvCalc to valTeldrStr
        if  (type(valSvCalc) == types.StringType) and \
            (valTeldrive >= TelStat_cfg.TELDRIVE_GUIDE_SV):
            valTeldrStr = '%s (%s)' % (valTeldrStr, valSvCalc)

        nowstate = 0
        warnAlarm = True
        if valTeldrive == None or valTeldrive == UNDEF:
            # Unknown value
            self.state.updateText( 'Unknown' )
            self.state.updateColor( PANECOLORREDALARMBACKGROUND )
            #? TelStatLog( TrackErrUnknownTrackStatus, 
            #?     "ERROR (TrackingPane:state label) Unknown Tracking Status value = " + `valTeldrive` )
        else:
            nowstate = valTeldrive
            # Update autoguider status label box
            self.state.updateText( valTeldrStr )
            if  valTeldrive == TELDRIVE_POINT or \
                valTeldrive == TELDRIVE_TRACK or valTeldrive == TELDRIVE_TRACK_NS:
                self.state.updateColor( PANECOLORMEDGREENBACKGROUND )
                warnAlarm = False
            elif  valSlew: 
                self.state.updateColor( PANECOLORYELLOWWARNBACKGROUND )
            else:
                # if we reach here, we're doing some sort of guiding
                if  valTeldrive < TELDRIVE_GUIDE_SV:
                    # Autoguider is engaged -- find intensity and error values
                    ag = True
                    valIntensity = valAgIntensity
                    valErr = dict['STATL.AGRERR'].value()

                    # Adjust display and issue alert if needed
                    if  valIntensity == UNDEF or valIntensity == None or \
                        valErr == None:
                        # Unknown value
                        self.state.updateColor( PANECOLORREDALARMBACKGROUND )
                        TelStatLog( TrackErrUndefAgValue, 
                            "ERROR (TrackingPane:status label) Unknown AG brightness or error value" )
                    elif  valIntensity < 1.0:
                        # Guide star isn't bright enough to hold lock - show alarm
                        self.state.updateColor( PANECOLORREDALARMBACKGROUND )
                        self.guideStarLostAlert.alert( level=ALARM )
                    elif valErr >= 1000.0:
                        # Autoguider is seriously losing track of guide star - show alarm
                        self.state.updateColor( PANECOLORREDALARMBACKGROUND )
                    elif valErr >= 500.0:
                        # Autoguider is losing track of guide star - show warning
                        self.state.updateColor( PANECOLORYELLOWWARNBACKGROUND )
                    else:
                        # Autoguider guiding ok
                        warnAlarm = False
                        self.state.updateColor( PANECOLORMEDGREENBACKGROUND )
                else:
                    # Slit viewer is providing tracking
                    sv = True
                    valIntensity = valSvIntensity
                    valErr = dict['STATL.SVRERR'].value()
                    # Adjust display and issue alert if needed
                    if  valIntensity == None or valErr == None:
                        # Unknown value
                        self.state.updateColor( PANECOLORREDALARMBACKGROUND )
                        TelStatLog( TrackErrUndefSvValue, 
                            "ERROR (TrackingPane:status label) Unknown SV brightness or error value" )
                    elif  valIntensity < 1.0:
                        # Guide star isn't bright enough to hold lock - show alarm
                        self.state.updateColor( PANECOLORREDALARMBACKGROUND )
                        self.guideStarLostAlert.alert( level=ALARM )
                    elif valErr >= 1000.0:
                        # Slit viewer is seriously losing track of guide star - show alarm
                        self.state.updateColor( PANECOLORREDALARMBACKGROUND )
                    elif valErr >= 500.0:
                        # Slit viewer is losing track of guide star - show warning
                        self.state.updateColor( PANECOLORYELLOWWARNBACKGROUND )
                    else:
                        # Slit viewer guiding ok
                        warnAlarm = False
                        self.state.updateColor( PANECOLORMEDGREENBACKGROUND )

        # Plot the new error values -- x and y are in units of milliarcsec
        #? if nowstate >= TELDRIVE_GUIDE_AG and nowstate <= TELDRIVE_GUIDE_AG2:

#        print 'ao alloc=%s  ircs alloc=%s hiciao alloc=%s' %(str( dict['FITS.AON.OBS_ALOC'].value()), str(dict['FITS.IRC.OBS_ALOC'].value()), str(dict['FITS.HIC.OBS_ALOC'].value()))
        ins_obs='Observation'
        if  self.ao==self.ins_obs and (self.ircs==self.ins_obs or self.hiciao==self.ins_obs or self.k3d==self.ins_obs):
            x = dict['AON.TT.TTX'].value()
            y = dict['AON.TT.TTY'].value()
            c1 = dict['AON.TT.WTTC1'].value()
            c2 = dict['AON.TT.WTTC2'].value()

#            print 'ttx=%s  tty=%s' %(str(x),str(y))
#            print 'wttc1=%s  wttc2=%s' %(str(x),str(y)) 
            if c1 != None and c2 != None:     # if either == None, do nothing
                self.error.update2(c1, c2)

            valExpTime = 0                   
        elif  nowstate == TELDRIVE_GUIDE_AG or \
            nowstate == TELDRIVE_GUIDE_AG1 or nowstate == TELDRIVE_GUIDE_AG2:
            x = dict['TSCL.AG1dX'].value()
            y = dict['TSCL.AG1dY'].value()
            valExpTime = valExpTimeAG
        elif  nowstate == TELDRIVE_GUIDE_AGFMOS or \
              nowstate == TELDRIVE_GUIDE_AGPIR:
            if  valAG == 1:
                x = dict['TSCL.AGPIRdX'].value()
                y = dict['TSCL.AGPIRdY'].value()
            elif  valAG == 2:
                x = 1000.0 * valCosEl * dict['TSCL.AGFMOSdAZ'].value()
                y = 1000.0 * dict['TSCL.AGFMOSdEL'].value()
            else:
                x = None
                y = None
                if  nowstate != self.laststate: # only clear once per transition
                    self.error.clear()
            valExpTime = valExpTimeAG
        elif  nowstate == TELDRIVE_GUIDE_HSCSCAG or \
              nowstate == TELDRIVE_GUIDE_HSCSHAG:
            if valAG == 3:
                x = dict['TSCL.HSC.SCAG.DX'].value()
                y = dict['TSCL.HSC.SCAG.DY'].value()
            elif valAG == 4:
                x = dict['TSCL.HSC.SHAG.DX'].value()
                y = dict['TSCL.HSC.SHAG.DY'].value()
            else:
                x = None
                y = None
                if  nowstate != self.laststate: # only clear once per transition
                    self.error.clear()
            valExpTime = valExpTimeAG
        elif nowstate >= TELDRIVE_GUIDE_SV and nowstate <= TELDRIVE_GUIDE_SV2:
            x = dict['TSCL.SV1DX'].value()
            y = dict['TSCL.SV1DY'].value()
            valExpTime = valExpTimeSV
        else:
            x = None
            y = None
            valExpTime = 0
            if  nowstate != self.laststate: # only clear once per transition
                self.error.clear()
        if x != None and y != None:     # if either == None, do nothing
            if self.lasterrplot < t - (valExpTime/1000):
                # raw units are milliarcsec
#                print 'updating x=%s  y=%s' %(str(x),str(y)) 
                self.error.update(x, y)
                self.lasterrplot = t

        # Plot the current brightness.  Change the background to warning color if
        # brightness goes below threshold
        if  ag:
            agbright = valAgIntensity
            svbright = None
        elif  sv:
            svbright = valSvIntensity
            agbright = None
        else:
            agbright = None
            svbright = None
        if  agbright == UNDEF:
            agbright = None
        if  svbright == UNDEF:
            svbright = None

        if  agbright != None and self.checkBrightValue(agbright) == 0:
            TelStatLog( TrackErrInvalidAgBrightness, 
                        "ERROR (TrackingPane:brightness plot) Invalid AG Brightness value = %d" % agbright )
            agbright = None
        if  svbright != None and self.checkBrightValue(svbright) == 0:
            TelStatLog( TrackErrInvalidSvBrightness, 
                        "ERROR (TrackingPane:brightness plot) Invalid SV Brightness value = %d" % svbright )
            svbright = None
        self.bright.update(t,(agbright,svbright))
            

        # Plot the current seeing value
        if  ag:
            if agfmos:
                agsee = dict['TSCL.AGFMOSStarSize'].value() 
                svsee = None
            elif agpir:
                agsee = dict['TSCL.AGPIRStarSize'].value() 
                svsee = None
            elif agHscSc:
                agsee = dict['TSCL.HSC.SCAG.StarSize'].value() 
                svsee = None
            elif agHscSh:
                agsee = dict['TSCL.HSC.SHAG.StarSize'].value() 
                svsee = None
            else:
                agsee = dict['VGWD.FWHM.AG'].value() 
                svsee = None
        elif  sv:
            agsee = None
            svsee = dict['VGWD.FWHM.SV'].value() 
        else:
            agsee = None
            svsee = None
        if  agsee == UNDEF:
            agsee = None
        if  svsee == UNDEF:
            svsee = None

        if agsee != None and self.checkSeeingValue(agsee) == 0:
            TelStatLog( TrackErrInvalidAgSeeing, 
                        "ERROR (TrackingPane:seeing plot) Invalid AG Seeing value = %d" % agsee )
            agsee = None
        if svsee != None and self.checkSeeingValue(svsee) == 0:
            TelStatLog( TrackErrInvalidSvSeeing, 
                        "ERROR (TrackingPane:seeing plot) Invalid SV Seeing value = %d" % svsee )
            svsee = None
        self.seeing.update(t,(agsee,svsee))

        # Update the current exposure times
        if  nowstate < TELDRIVE_GUIDE_AG:   # i.e. not currently guiding
            self.ExpLabelText.set( '' )
        else:
            err = False
            if valExpTimeAG == None:
                expTimeAgStr = '         '
            elif valExpTimeAG == UNDEF:
                expTimeAgStr = 'Undefined'
            elif  valExpTimeAG < 0:
                err = True
            else:
                expTimeAgStr = EXPNUMFORMAT % valExpTimeAG
            if valExpTimeSV == None:
                expTimeSvStr = '         '
            elif valExpTimeSV == UNDEF:
                expTimeSvStr = 'Undefined'
            elif  valExpTimeSV < 0:
                err = True
            else:
                expTimeSvStr = EXPNUMFORMAT % valExpTimeSV
            if valExpTimeAG == None and valExpTimeSV == None:
                self.ExpLabel.configure(bg=PANECOLORREDALERTFOREGROUND)
                self.exptimeerr = 1
                self.ExpLabelText.set( 'ExpTime: <No Data>' )
            elif  err:
                # Indicate invalid data received
                self.ExpLabel.configure(bg=PANECOLORREDALERTFOREGROUND)
                self.exptimeerr = 1
                TelStatLog( TrackErrInvalidExposure, 
       "ERROR (TrackingPane:exposure time) Invalid exposure time values = %s %s"
                            % (`valExpTimeAG`, `valExpTimeSV`) )
            else:
                if self.exptimeerr == 1:
                    # Clear invalid data indicator
                    self.ExpLabel.configure(bg=TRACKPANEBACKGROUND)
                    self.exptimeerr = 0
                self.ExpLabelText.set(EXPFORMAT % (expTimeAgStr, expTimeSvStr))

        # Update the probe position
        valFocus = dict['TELSTAT.FOCUS'].value()
        if  valFocus == FOCUS_PF_OPT or valFocus == FOCUS_PF_OPT2:
            agx  = dict['TSCL.AGPF_X'].value()
            cagx = dict['TSCL.AGPF_X_CMD'].value()
            agy  = dict['TSCL.AGPF_Y'].value()
            cagy = dict['TSCL.AGPF_Y_CMD'].value()
            if agx == None or agy == None or cagx == None or cagy == None:
                self.AGProbeLabel.configure(bg=PANECOLORREDALERTFOREGROUND)
                self.agprobeerr = 1
                self.AGProbeLabelText.set("AG Probe: <No Data>\n(Command) <No Data>")
            elif agx < -0.1 or agx > 170.0 or agy < -20.0 or agy > 20.0 or \
                     cagx < -0.1 or cagx > 170.0 or cagy < -20.0 or cagy > 20.0:
                # Indicate invalid data received
                self.AGProbeLabel.configure(bg=PANECOLORREDALERTFOREGROUND)
                self.agprobeerr = 1
                TelStatLog( TrackErrInvalidAgProbe, 
                            "ERROR (TrackingPane:AG probe) Invalid AG probe values = %f %f %f %f"
                            % (agx, agy, cagx, cagy))
            else:
                if abs(agx-cagx) > 1.0 or abs(agy-cagy) > 1.0:  # AG Probe is moving
                    self.AGProbeLabel.configure(fg=TRACKPANEAGPROBEMOVECOLOR)
                else:
                    self.AGProbeLabel.configure(fg=TRACKPANEFOREGROUND)
                if self.agprobeerr == 1:
                    # Clear invalid data indicator
                    self.AGProbeLabel.configure(bg=TRACKPANEBACKGROUND)
                    self.agprobeerr = 0
                self.AGProbeLabelText.set(AGFORMAT_PF % (agx, agy, cagx, cagy ) )

        elif  valFocus == FOCUS_PF_IR:
            if  valAG == 1:
                agx  = dict['TSCL.AGPIR_X'].value()
                cagx = dict['TSCL.AGPIR_X_CMD'].value()
                if agx == None or cagx == None:
                    self.AGProbeLabel.configure(bg=PANECOLORREDALERTFOREGROUND)
                    self.agprobeerr = 1
                    self.AGProbeLabelText.set("AG Probe: <No Data>\n(Command) <No Data>")
                # Following test almost certainly wrong!  Replace with good values.
                elif  agx < -1000.0 or agx > 1000.0 or \
                      cagx < -1000.0 or cagx > 1000.0:
                    # Indicate invalid data received
                    self.AGProbeLabel.configure(bg=PANECOLORREDALERTFOREGROUND)
                    self.agprobeerr = 1
                    TelStatLog( TrackErrInvalidAgProbe, 
                                "ERROR (TrackingPane:AG probe) Invalid FMOS AG1 probe values = %f %f"
                                % (agx, cagx))
                else:
                    if abs(agx-cagx) > 1.0:  # AG Probe is moving
                        self.AGProbeLabel.configure(fg=TRACKPANEAGPROBEMOVECOLOR)
                    else:
                        self.AGProbeLabel.configure(fg=TRACKPANEFOREGROUND)
                    if self.agprobeerr == 1:
                        # Clear invalid data indicator
                        self.AGProbeLabel.configure(bg=TRACKPANEBACKGROUND)
                        self.agprobeerr = 0
                    self.AGProbeLabelText.set(AGFORMAT_PIR % (agx, cagx ) )
            elif  valAG == 2:
                # AG2 has no probe position status values
                self.AGProbeLabelText.set('')

        elif  valFocus != None and valFocus != UNDEF:
            # This case covers non-PF AG probe locations, which use radius/theta
            agr  = dict['TSCV.AGR'].value()
            cagr = dict['STATL.AG_R_CMD'].value()
            agtheta  = dict['TSCV.AGTheta'].value_ArcDeg()
            cagtheta = dict['STATL.AG_THETA_CMD'].value_ArcDeg()
            if agr == None or agtheta == None or cagr == None or cagtheta == None:
                self.AGProbeLabel.configure(bg=PANECOLORREDALERTFOREGROUND)
                self.agprobeerr = 1
                self.AGProbeLabelText.set("AG Probe: <No Data>\n(Command) <No Data>")
            elif agr < -999.999 or agr > 999.999 or agtheta < -277.777 or agtheta > 277.777 or \
                     cagr < -999.999 or cagr > 999.999 or cagtheta < -277.777 or cagtheta > 277.777:
                # Indicate invalid data received
                self.AGProbeLabel.configure(bg=PANECOLORREDALERTFOREGROUND)
                self.agprobeerr = 1
                TelStatLog( TrackErrInvalidAgProbe, 
                            "ERROR (TrackingPane:AG probe) Invalid AG probe values = %f %s %f %s"
                            % (agr, dict['TSCV.AGTheta'].format_Deg(1),
                               cagr, dict['STATL.AG_THETA_CMD'].format_Deg(1)))
            else:
                if abs(agr-cagr) > 1.0 or abs(agtheta-cagtheta) > 1.0:  # AG Probe is moving
                    self.AGProbeLabel.configure(fg=TRACKPANEAGPROBEMOVECOLOR)
                else:
                    self.AGProbeLabel.configure(fg=TRACKPANEFOREGROUND)
                if self.agprobeerr == 1:
                    # Clear invalid data indicator
                    self.AGProbeLabel.configure(bg=TRACKPANEBACKGROUND)
                    self.agprobeerr = 0
                self.AGProbeLabelText.set(AGFORMAT % (agr, dict['TSCV.AGTheta'].format_Deg(1),
                                                      cagr, dict['STATL.AG_THETA_CMD'].format_Deg(1)))
        else:
            self.AGProbeLabel.configure(bg=TRACKPANEBACKGROUND)
            self.agprobeerr = 1
            self.AGProbeLabelText.set("AG Probe: <Unknown Focus>")

        # Update the threshold values
        if  valTeldrive < TELDRIVE_GUIDE_AG:    # not guiding
            self.ThresLabel.configure(bg=TRACKPANEBACKGROUND)
            self.ThresLabelText.set("")
        else:
            if  valFocus == FOCUS_PF_IR and valAG == 2:
                self.ThresLabelText.set("")
                self.ThresLabel.configure(bg=TRACKPANEBACKGROUND)
                self.thresholderr = 0
            elif  valBottom == None or valCeiling == None:
                self.ThresLabel.configure(bg=PANECOLORREDALERTFOREGROUND)
                self.thresholderr = 1
                self.ThresLabelText.set("Threshold: <No Data>")
            elif  valBottom >= 0 and valCeiling >= 0:
                if  self.thresholderr == 1:
                    # Clear invalid data indicator
                    self.ThresLabel.configure(bg=TRACKPANEBACKGROUND)
                    self.thresholderr = 0
                self.ThresLabelText.set(THRESFORMAT % (valBottom,valCeiling))
            else:
                # Indicate invalid data received
                self.ThresLabel.configure(bg=PANECOLORREDALERTFOREGROUND)
                self.thresholderr = 1
                TelStatLog( TrackErrInvalidExposure, 
                            "ERROR (TrackingPane:exposure time) Invalid exposure time values = %d %d"
                            % (valBottom, valCeiling) )

    def resize(self):
        """Redraw the pane to fit the new width."""
        pass

    def rePack(self):
        """First resize, then re-place this pane.
           This should ONLY be called if this pane is used in a top-level
              geometry pane, NOT if it is a page in a Notebook."""
        self.resize()
        self.pack(anchor=NW)


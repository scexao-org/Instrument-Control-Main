#! /usr/local/bin/python
# GlobalStates.py -- Bruce Bon -- 2008-08-26
#    Knowledge expert for assigning global states
#    Each of the derived boolean global states (beginning with "TELSTAT")
#    computed by this module may have any of 4 values:  True, False, None
#    or UNDEF (== -1).  None is used to signify that the raw value(s) from 
#    which the boolean is computed is/are unavailable.  UNDEF is used to
#    signify that the raw value(s) from which the boolean is computed 
#    is/are erroneous or has/have undefined value(s).
#    In most cases, the True value indicates a condition in which
#    it may be desirable to suppress audio alerts.
#
#    TELSTAT.FOCUS is a simple integer that may be None, if the source
#    alias (TSCV.Focus) is undefined, else one of the integer constants
#    defined in TelStat_cfg.py:  FOCUS_PF_OPT, FOCUS_PF_IR, FOCUS_NS_OPT,
#    FOCUS_NS_IR, FOCUS_CS_OPT, FOCUS_CS_IR.
#
#    TELSTAT.ROT_POS and TELSTAT.ROT_CMD are simply copies of existing
#    alias values, selected by the focus.

######################################################################
################   import needed modules   ###########################
######################################################################

import os
import sys

from DispType import *
import StatIO
import TelStatLog
import StatusDictionary
import TelStat_cfg

######################################################################
################   assign needed globals   ###########################
######################################################################

statusKeys = ( 
        # raw data
        'TSCS.EL', 'STATS.AZDIF', 'STATS.ELDIF',
        'TSCV.M1Cover', 'TSCV.M1CoverOnway', 'TSCV.DomeShutter',
        'TSCV.FOCUSINFO', 'TSCV.FOCUSINFO2', 'TSCV.FOCUSALARM', 'TSCV.ADCInOut',
        'TSCS.INSROTPOS_PF', 'TSCS.INSROTCMD_PF', 
        'TSCS.INSROTPOS',    'TSCS.INSROTCMD', 
        'TSCS.ImgRotPos',    'TSCS.IMGROTCMD', 'TSCV.ImgRotType',
        'STATL.TELDRIVE',
        'TSCV.TT_Mode', 'TSCV.TT_Drive', 
        'TSCV.TT_DataAvail', 'TSCV.TT_ChopStat',
        # derived data, to be assigned by this object
        'TELSTAT.TELDRIVE',
        'TELSTAT.SLEWING', 'TELSTAT.M1_CLOSED', 'TELSTAT.DOME_CLOSED', 
        'TELSTAT.EL_STOWED', 'TELSTAT.FOCUS', 'TELSTAT.M2', 'TELSTAT.AO', 
        'TELSTAT.ROTATOR', 'TELSTAT.ADC',
        'TELSTAT.ROT_POS', 'TELSTAT.ROT_CMD')

# Constants for logging
GSInfoStartStopSlew = TelStat_cfg.GSinfoBase

GSErrUndefTelDrive   = TelStat_cfg.GSerrBase
GSErrUndefFocus      = TelStat_cfg.GSerrBase+1
GSErrUndefM2Drive    = TelStat_cfg.GSerrBase+2
GSErrUndefFOCUSINFO  = TelStat_cfg.GSerrBase+3
GSErrSetActive       = TelStat_cfg.GSerrBase+4
GSErrUndefADCInOut   = TelStat_cfg.GSerrBase+5
GSErrInconsistentADC    = TelStat_cfg.GSerrBase+6
GSErrInconsistentRotADC = TelStat_cfg.GSerrBase+7
GSErrMissingFOCUSALARM  = TelStat_cfg.GSerrBase+8

GSWarnChangingFocus  = TelStat_cfg.GSwarnBase

######################################################################
################   declare class for the object   ####################
######################################################################

# Global States knowledge expert class
class GlobalStates(StatIO.StatPaneBase):
    MWin = 0

    def __init__(self):
        """Global States knowledge expert constructor."""
        StatIO.StatPaneBase.__init__(self, statusKeys, 'GlobalStates' )
        self.prevSLEWING = None        # Persistent value for slewing
        self.prevFOCUS   = None        # Persistent value for Focus
        self.prevM2      = None        # Persistent value for M2 selection

    def __setActiveFlags(self, dict, foc):
        """Turn on values for the new focus (foc) and turn off others."""
        if  foc == None or foc == TelStat_cfg.UNDEF or \
            foc == TelStat_cfg.FOCUS_CHANGING:
            # turn them all off!
                # Prime Focus
            dict['TSCS.INSROTPOS_PF'].setActive( False )
            dict['TSCS.INSROTCMD_PF'].setActive( False )
            dict['TSCL.AGPF_X'].setActive( False )
            dict['TSCL.AGPF_Y'].setActive( False )
            dict['TSCL.AGPF_X_CMD'].setActive( False )
            dict['TSCL.AGPF_Y_CMD'].setActive( False )
            dict['TSCV.ADCONOFF_PF'].setActive( False )
            dict['TSCV.ADCMODE_PF'].setActive( False )
            dict['TSCV.INSROTMODE_PF'].setActive( False )
            dict['TSCL.INSROTPA_PF'].setActive( False )
            dict['STATS.ROTDIF_PF'].setActive( False )

                # Cassegrain and Nasmyth
            dict['TSCV.ADCInOut'].setActive( False )
            dict['TSCV.ADCOnOff'].setActive( False )
            dict['TSCV.ADCMode'].setActive( False )
            dict['TSCV.AGR'].setActive( False )
            dict['TSCV.AGTheta'].setActive( False )
            dict['STATL.AG_R_CMD'].setActive( False )
            dict['STATL.AG_THETA_CMD'].setActive( False )
            dict['STATS.ROTDIF'].setActive( False )

                # Cassegrain-only
            dict['TSCS.INSROTPOS'].setActive( False )
            dict['TSCS.INSROTCMD'].setActive( False )
            dict['TSCL.InsRotPA'].setActive( False )
            dict['TSCV.InsRotMode'].setActive( False )

                # Nasmyth-only
            dict['TSCS.ImgRotPos'].setActive( False )
            dict['TSCS.IMGROTCMD'].setActive( False )
            dict['TSCL.ImgRotPA'].setActive( False )
            dict['TSCV.ImgRotMode'].setActive( False )
            dict['TSCV.ImgRotType'].setActive( False )

                # Prime and Cassegrain
            dict['TSCV.InsRotRotation'].setActive( False )

        else:   # focus is defined and known

            if  foc == TelStat_cfg.FOCUS_PF_OPT or  \
                foc == TelStat_cfg.FOCUS_PF_IR or   \
                foc == TelStat_cfg.FOCUS_PF_OPT2 or \
                foc == TelStat_cfg.FOCUS_CS_OPT or  \
                foc == TelStat_cfg.FOCUS_CS_IR:
                # turn prime focus, Cassegrain on
                dict['TSCV.InsRotRotation'].setActive( True )

            if  foc == TelStat_cfg.FOCUS_PF_OPT or  \
                foc == TelStat_cfg.FOCUS_PF_IR  or  \
                foc == TelStat_cfg.FOCUS_PF_OPT2:
                # turn prime focus on, Cassegrain and Nasmyth off
                dict['TSCS.INSROTPOS_PF'].setActive( True )
                dict['TSCS.INSROTCMD_PF'].setActive( True )
                dict['TSCL.INSROTPA_PF'].setActive( True )
                dict['TSCV.INSROTROTATION_PF'].setActive( True )
                dict['TSCV.INSROTMODE_PF'].setActive( True )
                dict['STATS.ROTDIF_PF'].setActive( True )

                if  foc == TelStat_cfg.FOCUS_PF_OPT or \
                    foc == TelStat_cfg.FOCUS_PF_IR:
                    dict['TSCL.AGPF_X'].setActive( True )
                    dict['TSCL.AGPF_Y'].setActive( True )
                    dict['TSCL.AGPF_X_CMD'].setActive( True )
                    dict['TSCL.AGPF_Y_CMD'].setActive( True )

                if  foc == TelStat_cfg.FOCUS_PF_OPT or \
                    foc == TelStat_cfg.FOCUS_PF_OPT2:
                        # Turn on optical-only and turn off PF_IR
                    dict['TSCV.ADCONOFF_PF'].setActive( True )
                    dict['TSCV.ADCMODE_PF'].setActive( True )
                    dict['TSCL.AGFMOSIntensity'].setActive( False )
                    dict['TSCL.AGPIRIntensity'].setActive( False )
                    dict['TSCL.AGFMOSStarSize'].setActive( False )
                    dict['TSCL.AGPIRStarSize'].setActive( False )
                    dict['TSCL.AGFMOSdAZ'].setActive( False )
                    dict['TSCL.AGFMOSdEL'].setActive( False )
                    dict['TSCL.AGPIRdX'].setActive( False )
                    dict['TSCL.AGPIRdY'].setActive( False )
                    dict['TSCL.AGPIR_X'].setActive( False )
                    dict['TSCL.AGPIR_X_CMD'].setActive( False )
                    dict['TSCV.AGFMOSCCalc'].setActive( False )
                    dict['TSCV.AGFMOSExpTime'].setActive( False )
                    dict['TSCV.AGPIRCCalc'].setActive( False )
                    dict['TSCV.AGPIRExpTime'].setActive( False )
                    dict['TSCV.AGPIR_I_BOTTOM'].setActive( False )
                    dict['TSCV.AGPIR_I_CEIL'].setActive( False )
                    if foc == TelStat_cfg.FOCUS_PF_OPT2:
                        # Turn on P_OPT2 items
                        dict['TSCL.HSC.SCAG.Intensity'].setActive( True )
                        dict['TSCL.HSC.SCAG.StarSize'].setActive( True )
                        dict['TSCL.HSC.SCAG.dAZ'].setActive( True )
                        dict['TSCL.HSC.SCAG.dEL'].setActive( True )
                        dict['TSCL.HSC.SCAG.DX'].setActive( True )
                        dict['TSCL.HSC.SCAG.DY'].setActive( True )
                        dict['TSCV.HSC.SCAG.CCalc'].setActive( True )
                        dict['TSCV.HSC.SCAG.ExpTime'].setActive( True )
                        dict['TSCL.HSC.SHAG.Intensity'].setActive( True )
                        dict['TSCL.HSC.SHAG.StarSize'].setActive( True )
                        dict['TSCL.HSC.SHAG.dAZ'].setActive( True )
                        dict['TSCL.HSC.SHAG.dEL'].setActive( True )
                        dict['TSCL.HSC.SHAG.DX'].setActive( True )
                        dict['TSCL.HSC.SHAG.DY'].setActive( True )
                        dict['TSCV.HSC.SHAG.CCalc'].setActive( True )
                        dict['TSCV.HSC.SHAG.ExpTime'].setActive( True )
                        dict['TSCV.HSC.SHAG.I_BOTTOM'].setActive( True )
                        dict['TSCV.HSC.SHAG.I_CEIL'].setActive( True )
                else:   # foc == TelStat_cfg.FOCUS_PF_IR:
                        # Turn off optical-only and turn on PF_IR
                    dict['TSCV.ADCONOFF_PF'].setActive( False )
                    dict['TSCV.ADCMODE_PF'].setActive( False )
                    dict['TSCL.AGFMOSIntensity'].setActive( True )
                    dict['TSCL.AGPIRIntensity'].setActive( True )
                    dict['TSCL.AGFMOSStarSize'].setActive( True )
                    dict['TSCL.AGPIRStarSize'].setActive( True )
                    dict['TSCL.AGFMOSdAZ'].setActive( True )
                    dict['TSCL.AGFMOSdEL'].setActive( True )
                    dict['TSCL.AGPIRdX'].setActive( True )
                    dict['TSCL.AGPIRdY'].setActive( True )
                    dict['TSCL.AGPIR_X'].setActive( True )
                    dict['TSCL.AGPIR_X_CMD'].setActive( True )
                    dict['TSCV.AGFMOSCCalc'].setActive( True )
                    dict['TSCV.AGFMOSExpTime'].setActive( True )
                    dict['TSCV.AGPIRCCalc'].setActive( True )
                    dict['TSCV.AGPIRExpTime'].setActive( True )
                    dict['TSCV.AGPIR_I_BOTTOM'].setActive( True )
                    dict['TSCV.AGPIR_I_CEIL'].setActive( True )

                if foc == TelStat_cfg.FOCUS_PF_OPT2:
                    # Turn on ADCInOut for P_OPT2
                    dict['TSCV.ADCInOut'].setActive( True )
                else:
                    # Cassegrain and Nasmyth
                    dict['TSCV.ADCInOut'].setActive( False )

                    # Cassegrain and Nasmyth
                dict['TSCV.ADCOnOff'].setActive( False )
                dict['TSCV.ADCMode'].setActive( False )
                dict['TSCV.AGR'].setActive( False )
                dict['TSCV.AGTheta'].setActive( False )
                dict['TSCV.InsRotRotation'].setActive( False )
                dict['TSCV.InsRotMode'].setActive( False )
                dict['TSCV.ImgRotRotation'].setActive( False )
                dict['TSCV.ImgRotMode'].setActive( False )
                dict['TSCV.ImgRotType'].setActive( False )
                dict['STATL.AG_R_CMD'].setActive( False )
                dict['STATL.AG_THETA_CMD'].setActive( False )
                dict['STATS.ROTDIF'].setActive( False )

                    # Cassegrain-only
                dict['TSCS.INSROTPOS'].setActive( False )
                dict['TSCS.INSROTCMD'].setActive( False )
                dict['TSCL.InsRotPA'].setActive( False )
                dict['TSCV.InsRotMode'].setActive( False )

                    # Nasmyth-only
                dict['TSCS.ImgRotPos'].setActive( False )
                dict['TSCS.IMGROTCMD'].setActive( False )
                dict['TSCL.ImgRotPA'].setActive( False )
                dict['TSCV.ImgRotMode'].setActive( False )
                dict['TSCV.ImgRotType'].setActive( False )

            else: # FOCUS_NS_OPT, FOCUS_NS_IR, FOCUS_CS_OPT or FOCUS_CS_IR
                # turn prime focus off, Cassegrain and Nasmyth on
                dict['TSCS.INSROTPOS_PF'].setActive( False )
                dict['TSCS.INSROTCMD_PF'].setActive( False )
                dict['TSCL.AGPF_X'].setActive( False )
                dict['TSCL.AGPF_Y'].setActive( False )
                dict['TSCL.AGPF_X_CMD'].setActive( False )
                dict['TSCL.AGPF_Y_CMD'].setActive( False )
                dict['TSCV.ADCONOFF_PF'].setActive( False )
                dict['TSCV.ADCMODE_PF'].setActive( False )
                dict['TSCV.INSROTROTATION_PF'].setActive( False )
                dict['TSCV.INSROTMODE_PF'].setActive( False )
                dict['TSCL.INSROTPA_PF'].setActive( False )
                dict['STATS.ROTDIF_PF'].setActive( False )

                    # Cassegrain and Nasmyth
                dict['TSCV.ADCMode'].setActive( True )
                dict['TSCV.AGR'].setActive( True )
                dict['TSCV.AGTheta'].setActive( True )
                dict['STATL.AG_R_CMD'].setActive( True )
                dict['STATL.AG_THETA_CMD'].setActive( True )
                dict['STATS.ROTDIF'].setActive( True )

                if  foc == TelStat_cfg.FOCUS_NS_OPT:
                        # Cassegrain-only
                    dict['TSCS.INSROTPOS'].setActive( False )
                    dict['TSCS.INSROTCMD'].setActive( False )
                    dict['TSCL.InsRotPA'].setActive( False )
                    dict['TSCV.InsRotMode'].setActive( False )
                        # Nasmyth-only
                    dict['TSCS.ImgRotPos'].setActive( True )
                    dict['TSCS.IMGROTCMD'].setActive( True )
                    dict['TSCL.ImgRotPA'].setActive( True )
                    dict['TSCV.ImgRotRotation'].setActive( True )
                    dict['TSCV.ImgRotMode'].setActive( True )
                        # Turn on optical-only
                    dict['TSCV.ADCInOut'].setActive( True )
                    dict['TSCV.ADCOnOff'].setActive( True )
                    dict['TSCV.ImgRotType'].setActive( True )

                elif  foc == TelStat_cfg.FOCUS_NS_IR:
                        # Cassegrain-only
                    dict['TSCS.INSROTPOS'].setActive( False )
                    dict['TSCS.INSROTCMD'].setActive( False )
                    dict['TSCL.InsRotPA'].setActive( False )
                    dict['TSCV.InsRotMode'].setActive( False )
                        # Nasmyth-only
                    dict['TSCS.ImgRotPos'].setActive( True )
                    dict['TSCS.IMGROTCMD'].setActive( True )
                    dict['TSCL.ImgRotPA'].setActive( True )
                    dict['TSCV.ImgRotRotation'].setActive( True )
                    dict['TSCV.ImgRotMode'].setActive( True )
                        # Turn off optical-only
                    dict['TSCV.ADCInOut'].setActive( False )
                    dict['TSCV.ADCOnOff'].setActive( False )
                    dict['TSCV.ImgRotType'].setActive( False )

                else: # FOCUS_CS_*
                        # Cassegrain-only
                    dict['TSCS.INSROTPOS'].setActive( True )
                    dict['TSCS.INSROTCMD'].setActive( True )
                    dict['TSCL.InsRotPA'].setActive( True )
                    dict['TSCV.InsRotMode'].setActive( True )
                        # Turn on optical-only
                    dict['TSCV.ADCInOut'].setActive( True )
                    dict['TSCV.ADCOnOff'].setActive( True )
                        # Nasmyth-only
                    dict['TSCS.ImgRotPos'].setActive( False )
                    dict['TSCS.IMGROTCMD'].setActive( False )
                    dict['TSCL.ImgRotPA'].setActive( False )
                    dict['TSCV.ImgRotMode'].setActive( False )
                    dict['TSCV.ImgRotType'].setActive( False )


    def __setADC(self, dict, FocusInfo, FocusIn):
        """Given that TSCV.FOCUSINFO is valid and FocusIn specifies ADC in/out,
        set TELSTAT.ADC based on TSCV.ADCInOut. """
        InOut = dict['TSCV.ADCInOut'].value();
        if  InOut == None:
            dict['TELSTAT.ADC'].setValue(None)
        elif  InOut != 0x08 and InOut != 0x10:      # invalid
            dict['TELSTAT.ADC'].setValue(TelStat_cfg.UNDEF)
            TelStatLog.TelStatLog( GSErrUndefADCInOut,
                'ERROR (GlobalStates:refresh):  Undefined value ' +
                'of TSCV.ADCInOut (0x%02x)' %  InOut )
        elif  InOut == 0x08:    # in
            if  FocusIn:
                dict['TELSTAT.ADC'].setValue(TelStat_cfg.ADC_IN)
            else:   # !FocusIn
                dict['TELSTAT.ADC'].setValue(TelStat_cfg.UNDEF)
                TelStatLog.TelStatLog( GSErrInconsistentADC,
                    ('ERROR (GlobalStates:refresh):  TSCV.FOCUSINFO ' +
                    '(0x%08x) indicates ADC out, but TSCV.ADCInOut (0x%02x) ' +
                    'indicates ADC in') %  (FocusInfo,InOut) )
        elif  InOut == 0x10:    # out
            if  FocusIn:
                dict['TELSTAT.ADC'].setValue(TelStat_cfg.UNDEF)
                TelStatLog.TelStatLog( GSErrInconsistentADC,
                    ('ERROR (GlobalStates:refresh):  TSCV.FOCUSINFO ' +
                    '(0x%08x) indicates ADC in, but TSCV.ADCInOut (0x%02x) ' +
                    'indicates ADC out') %  (FocusInfo,InOut) )
            else:   # !FocusIn
                dict['TELSTAT.ADC'].setValue(TelStat_cfg.ADC_OUT)

    def refresh(self, dict):
        """Refresh global states with updated values from dict."""

        # Determine TELSTAT.TELDRIVE
        std = dict['STATL.TELDRIVE'].value()
        if  std == None:
            dict['TELSTAT.TELDRIVE'].setValue(None)
            TelStatLog.TelStatLog( GSErrUndefTelDrive,
                    'ERROR (GlobalStates:refresh):  STATL.TELDRIVE is None')
        else:
            try:
                std = std.upper()
            except:
                TelStatLog.TelStatLog( GSErrUndefTelDrive,
                        'ERROR (GlobalStates:refresh):  exception converting' +
                        ' STATL.TELDRIVE value (%s) to upper' % `std` )
                std = 'UNKNOWN'
            try:
                if  std.find( 'UNKNOWN' ) >= 0:
                    dict['TELSTAT.TELDRIVE'].setValue(TelStat_cfg.UNDEF)
                elif  std.find( 'POINT' ) >= 0:
                    dict['TELSTAT.TELDRIVE'].setValue(
                                        TelStat_cfg.TELDRIVE_POINT)
                elif  std.find( 'TRACKING(NON-SIDEREAL)' ) >= 0:
                    dict['TELSTAT.TELDRIVE'].setValue(
                                        TelStat_cfg.TELDRIVE_TRACK_NS)
                elif  std.find( 'TRACK' ) >= 0:
                    dict['TELSTAT.TELDRIVE'].setValue(
                                        TelStat_cfg.TELDRIVE_TRACK)
                elif  std.find( 'SLEW' ) >= 0:
                    dict['TELSTAT.TELDRIVE'].setValue(
                                        TelStat_cfg.TELDRIVE_SLEW)
                elif  std.find( 'GUIDING(AGPIR)' ) >= 0:
                    dict['TELSTAT.TELDRIVE'].setValue(
                                        TelStat_cfg.TELDRIVE_GUIDE_AGPIR)
                elif  std.find( 'GUIDING(AGFMOS)' ) >= 0:
                    dict['TELSTAT.TELDRIVE'].setValue(
                                        TelStat_cfg.TELDRIVE_GUIDE_AGFMOS)
                elif  std.find( 'GUIDING(HSCSCAG)' ) >= 0:
                    dict['TELSTAT.TELDRIVE'].setValue(
                                        TelStat_cfg.TELDRIVE_GUIDE_HSCSCAG)
                elif  std.find( 'GUIDING(HSCSHAG)' ) >= 0:
                    dict['TELSTAT.TELDRIVE'].setValue(
                                        TelStat_cfg.TELDRIVE_GUIDE_HSCSHAG)
                elif  std.find( 'GUIDING(AG1)' ) >= 0:
                    dict['TELSTAT.TELDRIVE'].setValue(
                                        TelStat_cfg.TELDRIVE_GUIDE_AG1)
                elif  std.find( 'GUIDING(AG2)' ) >= 0:
                    dict['TELSTAT.TELDRIVE'].setValue(
                                        TelStat_cfg.TELDRIVE_GUIDE_AG2)
                elif  std.find( 'GUIDING(AG)' ) >= 0:
                    dict['TELSTAT.TELDRIVE'].setValue(
                                        TelStat_cfg.TELDRIVE_GUIDE_AG)
                elif  std.find( 'GUIDING(SV1)' ) >= 0:
                    dict['TELSTAT.TELDRIVE'].setValue(
                                        TelStat_cfg.TELDRIVE_GUIDE_SV1)
                elif  std.find( 'GUIDING(SV2)' ) >= 0:
                    dict['TELSTAT.TELDRIVE'].setValue(
                                        TelStat_cfg.TELDRIVE_GUIDE_SV2)
                elif  std.find( 'GUIDING(SV)' ) >= 0:
                    dict['TELSTAT.TELDRIVE'].setValue(
                                        TelStat_cfg.TELDRIVE_GUIDE_SV)
                else:
                    dict['TELSTAT.TELDRIVE'].setValue(
                                        TelStat_cfg.UNDEF)
                    TelStatLog.TelStatLog( GSErrUndefTelDrive,
                        'ERROR (GlobalStates:refresh):  Undefined' +
                        ' STATL.TELDRIVE = "%s"' %  std )
            except:
                TelStatLog.TelStatLog( GSErrUndefTelDrive,
                    'ERROR (GlobalStates:refresh):  exception converting' +
                    ' STATL.TELDRIVE value (%s) to TELSTAT.TELDRIVE' % `std` )
                dict['TELSTAT.TELDRIVE'].setValue(TelStat_cfg.UNDEF)

        # Determine if the telescope is slewing
        td = dict['TELSTAT.TELDRIVE'].value()
        if  td == None or td == TelStat_cfg.UNDEF:
            dict['TELSTAT.SLEWING'].setValue(None)
            self.prevSLEWING = None
        elif  td == TelStat_cfg.TELDRIVE_SLEW:
            if  self.prevSLEWING == False:
                TelStatLog.TelStatLog( GSInfoStartStopSlew,
                    "GlobalStates:refresh():  Starting telescope slew", 
                    alwaysOutput = True )
            dict['TELSTAT.SLEWING'].setValue(True)
            self.prevSLEWING = True
        else:
            if  self.prevSLEWING == True:
                TelStatLog.TelStatLog( GSInfoStartStopSlew,
                    "GlobalStates:refresh():  Finished telescope slew",
                    alwaysOutput = True )
            dict['TELSTAT.SLEWING'].setValue(False)
            self.prevSLEWING = False

        # Determine if the telescope is inactive according to elevation
        el = dict['TSCS.EL'].value_ArcDeg()
        if  el == None:
            dict['TELSTAT.EL_STOWED'].setValue(None)
        else:
            if  el >= TelStat_cfg.GS_INACTIVEELEVATION:
                dict['TELSTAT.EL_STOWED'].setValue(True)
            else:
                dict['TELSTAT.EL_STOWED'].setValue(False)

        # Determine if the dome shutter is closed
        DomeShutter     = dict['TSCV.DomeShutter'].value();
        if  DomeShutter == None:
            dict['TELSTAT.DOME_CLOSED'].setValue(None)
        else:
            if  DomeShutter &(0x50) == 0:
                dict['TELSTAT.DOME_CLOSED'].setValue(True)
            else:
                dict['TELSTAT.DOME_CLOSED'].setValue(False)

        # Determine if the M1 cover is closed
        M1CoverOnway    = dict['TSCV.M1CoverOnway'].value();
        M1Cover         = dict['TSCV.M1Cover'].value();
        if  M1CoverOnway == None or M1Cover == None:
            dict['TELSTAT.M1_CLOSED'].setValue(None)
        else:
            if  M1CoverOnway != 0x01 and M1CoverOnway != 0x02 and \
                M1Cover &(0x5555555555555555555555) == 0x4444444444444444444444:
                dict['TELSTAT.M1_CLOSED'].setValue(True)
            else:
                dict['TELSTAT.M1_CLOSED'].setValue(False)

        # Compute TELSTAT.FOCUS, TELSTAT.M2, TELSTAT.ROTATOR, TELSTAT.ADC
        Focus   = dict['TSCV.FOCUSINFO'].value();
        Focus2  = dict['TSCV.FOCUSINFO2'].value();
        dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.ROT_OUT)
        dict['TELSTAT.ADC'].setValue(TelStat_cfg.ADC_OUT)
        # For recording purposes, leave all these aliases always active
        # dict['TSCV.FOCUSINFO'].setActive( True )
        # dict['TSCV.Focus'].setActive( False )
        # dict['TSCV.M2Drive'].setActive( False )

        badFocus = False
        dict['TELSTAT.AO'].setValue(TelStat_cfg.AO_OUT)
        if  Focus == None or Focus2 == None:
            foc = None
            dict['TELSTAT.M2'].setValue(None)
            dict['TELSTAT.ROTATOR'].setValue(None)
            dict['TELSTAT.ADC'].setValue(None)
            dict['TELSTAT.AO'].setValue(None)
        elif  Focus == 0x01000000:
            foc = TelStat_cfg.FOCUS_PF_OPT
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_PF_OPT)
            dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.ROT_INSR)
            dict['TELSTAT.ADC'].setValue(TelStat_cfg.ADC_IN)
        elif  Focus == 0x02000000:
            foc = TelStat_cfg.FOCUS_PF_IR
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_PF_IR)
            dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.ROT_INSR)
        elif  Focus == 0x04000000:
            foc = TelStat_cfg.FOCUS_CS_OPT
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_CS_OPT)
            dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.ROT_INSR)
            self.__setADC(dict, Focus, False)
        elif  Focus == 0x08000000:
            foc = TelStat_cfg.FOCUS_CS_OPT
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_CS_OPT)
            dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.ROT_INSR)
            self.__setADC(dict, Focus, True)
        elif  Focus == 0x10000000:
            foc = TelStat_cfg.FOCUS_NS_OPT
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_CS_OPT)
            self.__setADC(dict, Focus, False)
        elif  Focus == 0x20000000:
            foc = TelStat_cfg.FOCUS_NS_OPT
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_CS_OPT)
            self.__setADC(dict, Focus, True)
        elif  Focus == 0x40000000:
            foc = TelStat_cfg.FOCUS_NS_OPT
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_CS_OPT)
            dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.ROT_IMRB)
            self.__setADC(dict, Focus, False)
        elif  Focus == 0x80000000L:
            foc = TelStat_cfg.FOCUS_NS_OPT
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_CS_OPT)
            dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.ROT_IMRB)
            self.__setADC(dict, Focus, True)
        elif  Focus == 0x00010000:
            foc = TelStat_cfg.FOCUS_NS_OPT
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_CS_OPT)
            dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.ROT_IMRR)
            self.__setADC(dict, Focus, False)
        elif  Focus == 0x00020000:
            foc = TelStat_cfg.FOCUS_NS_OPT
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_CS_OPT)
            dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.ROT_IMRR)
            self.__setADC(dict, Focus, True)
        elif  Focus == 0x00040000:
            foc = TelStat_cfg.FOCUS_NS_IR
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_CS_OPT)
        elif  Focus == 0x00080000:
            foc = TelStat_cfg.FOCUS_NS_IR
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_CS_OPT)
            dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.ROT_IMR)
        elif  Focus == 0x00100000:
            foc = TelStat_cfg.FOCUS_NS_OPT
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_NS_OPT)
            self.__setADC(dict, Focus, False)
        elif  Focus == 0x00200000:
            foc = TelStat_cfg.FOCUS_NS_OPT
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_NS_OPT)
            self.__setADC(dict, Focus, True)
        elif  Focus == 0x00400000:
            foc = TelStat_cfg.FOCUS_NS_OPT
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_NS_OPT)
            dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.ROT_IMRB)
            self.__setADC(dict, Focus, False)
        elif  Focus == 0x00800000:
            foc = TelStat_cfg.FOCUS_NS_OPT
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_NS_OPT)
            dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.ROT_IMRB)
            self.__setADC(dict, Focus, True)
        elif  Focus == 0x00000100:
            foc = TelStat_cfg.FOCUS_NS_OPT
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_NS_OPT)
            dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.ROT_IMRR)
            self.__setADC(dict, Focus, False)
        elif  Focus == 0x00000200:
            foc = TelStat_cfg.FOCUS_NS_OPT
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_NS_OPT)
            dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.ROT_IMRR)
            self.__setADC(dict, Focus, True)
        elif  Focus == 0x00000400:
            foc = TelStat_cfg.FOCUS_NS_IR
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_NS_OPT)
        elif  Focus == 0x00000800:
            foc = TelStat_cfg.FOCUS_NS_IR
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_NS_OPT)
            dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.ROT_IMR)
        elif  Focus == 0x00001000:
            foc = TelStat_cfg.FOCUS_CS_IR
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_IR)
            dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.ROT_INSR)
        elif  Focus == 0x00002000:
            foc = TelStat_cfg.FOCUS_NS_OPT
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_IR)
        elif  Focus == 0x00004000:
            foc = TelStat_cfg.FOCUS_NS_OPT
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_IR)
            self.__setADC(dict, Focus, True)
        elif  Focus == 0x00008000:
            foc = TelStat_cfg.FOCUS_NS_OPT
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_IR)
            dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.ROT_IMRB)
        elif  Focus == 0x00000001:
            foc = TelStat_cfg.FOCUS_NS_OPT
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_IR)
            dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.ROT_IMRB)
            self.__setADC(dict, Focus, True)
        elif  Focus == 0x00000002:
            foc = TelStat_cfg.FOCUS_NS_OPT
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_IR)
            dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.ROT_IMRR)
        elif  Focus == 0x00000004:
            foc = TelStat_cfg.FOCUS_NS_OPT
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_IR)
            dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.ROT_IMRR)
            self.__setADC(dict, Focus, True)
        elif  Focus == 0x00000008:
            foc = TelStat_cfg.FOCUS_NS_IR
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_IR)
        elif  Focus == 0x00000010:
            foc = TelStat_cfg.FOCUS_NS_IR
            dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_IR)
            dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.ROT_IMR)
        elif  Focus == 0x00000000:
            if  Focus2 == 0x01:
                foc = TelStat_cfg.FOCUS_NS_IR
                dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_IR)
                dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.ROT_OUT)
                dict['TELSTAT.AO'].setValue(TelStat_cfg.AO_IN)
            elif  Focus2 == 0x02:
                foc = TelStat_cfg.FOCUS_NS_IR
                dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_CS_OPT)
                dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.ROT_OUT)
                dict['TELSTAT.AO'].setValue(TelStat_cfg.AO_IN)
            elif  Focus2 == 0x04:
                foc = TelStat_cfg.FOCUS_NS_IR
                dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_NS_OPT)
                dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.ROT_OUT)
                dict['TELSTAT.AO'].setValue(TelStat_cfg.AO_IN)
            elif  Focus2 == 0x08:
                foc = TelStat_cfg.FOCUS_PF_OPT2
                dict['TELSTAT.M2'].setValue(TelStat_cfg.M2_PF_OPT2)
                dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.ROT_INSR)
                self.__setADC(dict, Focus2, False)
            else:
                badFocus = True
        else:
            badFocus = True

        if  badFocus:
            foc = TelStat_cfg.UNDEF
            dict['TELSTAT.M2'].setValue(TelStat_cfg.UNDEF)
            dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.UNDEF)
            dict['TELSTAT.ADC'].setValue(TelStat_cfg.UNDEF)
            dict['TELSTAT.AO'].setValue(TelStat_cfg.UNDEF)
            TelStatLog.TelStatLog( GSErrUndefFOCUSINFO,
                "ERROR (GlobalStates:refresh):  Undefined TSCV.FOCUSINFO = %x" %  Focus )

        # Process TSCV.FOCUSALARM conditions
        Alarm     = dict['TSCV.FOCUSALARM'].value();
        if  Alarm == None:
            dict['TELSTAT.M2'].setValue(TelStat_cfg.UNDEF)
            dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.UNDEF)
            dict['TELSTAT.ADC'].setValue(TelStat_cfg.UNDEF)
            TelStatLog.TelStatLog( GSErrMissingFOCUSALARM,
                'ERROR (GlobalStates:refresh):  no TSCV.FOCUSALARM ' +
                'data is available' )
        else:
            if  Alarm &(0x40):
                # TSC Focus Pattern Alarm - Focus is in transition
                foc = TelStat_cfg.FOCUS_CHANGING
                dict['TELSTAT.M2'].setValue(TelStat_cfg.UNDEF)
                dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.UNDEF)
                dict['TELSTAT.ADC'].setValue(TelStat_cfg.UNDEF)
                TelStatLog.TelStatLog( GSWarnChangingFocus,
                    'ERROR (GlobalStates:refresh):  TSCV.FOCUSALARM ' +
                    '(0x%02x) indicates changing FOCUS' %  Alarm )
            if  Alarm &(0x80):
                # TSC Rotator ADC Selected Alarm - Focus in conflict with Rot or ADC
                dict['TELSTAT.M2'].setValue(TelStat_cfg.UNDEF)
                dict['TELSTAT.ROTATOR'].setValue(TelStat_cfg.UNDEF)
                dict['TELSTAT.ADC'].setValue(TelStat_cfg.UNDEF)
                TelStatLog.TelStatLog( GSErrInconsistentRotADC,
                    'ERROR (GlobalStates:refresh):  TSCV.FOCUSALARM ' +
                    '(0x%02x) indicates inconsistent ADC/Rot selection' %  Alarm )

        dict['TELSTAT.FOCUS'].setValue(foc)
        # foc == dict['TELSTAT.FOCUS'].value()

        # Copy values into TELSTAT.ROT_POS and TELSTAT.ROT_CMD
        if foc == None:
            dict['TELSTAT.ROT_POS'].setValue(None)
            dict['TELSTAT.ROT_CMD'].setValue(None)
        elif foc == TelStat_cfg.FOCUS_PF_OPT or foc == TelStat_cfg.FOCUS_PF_IR or foc == TelStat_cfg.FOCUS_PF_OPT2:
            dict['TELSTAT.ROT_POS'].setValue(
                                dict['TSCS.INSROTPOS_PF'].value() )
            dict['TELSTAT.ROT_CMD'].setValue(
                                dict['TSCS.INSROTCMD_PF'].value() )
        elif foc == TelStat_cfg.FOCUS_NS_OPT or foc == TelStat_cfg.FOCUS_NS_IR:
            dict['TELSTAT.ROT_POS'].setValue(
                                dict['TSCS.ImgRotPos'].value() )
            dict['TELSTAT.ROT_CMD'].setValue(
                                dict['TSCS.IMGROTCMD'].value() )
        else: # FOCUS_CS_OPT or FOCUS_CS_IR
            dict['TELSTAT.ROT_POS'].setValue(
                                dict['TSCS.INSROTPOS'].value() )
            dict['TELSTAT.ROT_CMD'].setValue(
                                dict['TSCS.INSROTCMD'].value() )

        # If focus has changed, set active flags to control which status
        #   alias values are pulled by OSSC_screenPrint.  All aliases which
        #   were turned OFF under the previous focus will be None for 1 cycle
        #   when the focus changes.
        if  foc != self.prevFOCUS:
            self.__setActiveFlags(dict, foc)
            self.prevFOCUS = foc
        # Set flags that are dependent on TELSTAT.M2
        m2 = dict['TELSTAT.M2'].value()
        if  m2 != self.prevM2:
            if  m2 != TelStat_cfg.M2_IR:
                # Turn all TT aliases off
                dict['TSCV.TT_Mode'].setActive( False )
                dict['TSCV.TT_Drive'].setActive( False )
                dict['TSCV.TT_DataAvail'].setActive( False )
                dict['TSCV.TT_ChopStat'].setActive( False )
            else:
                # Turn all TT aliases on
                dict['TSCV.TT_Mode'].setActive( True )
                dict['TSCV.TT_Drive'].setActive( True )
                dict['TSCV.TT_DataAvail'].setActive( True )
                dict['TSCV.TT_ChopStat'].setActive( True )
            self.prevM2 = m2

#        print 'STATL.TELDRIVE = %s, TELSTAT.TELDRIVE = %s' %    \
#            ( `dict['STATL.TELDRIVE'].value()`,                \
#              self._fmt_( '%d', dict['TELSTAT.TELDRIVE'].value()) ),
#        print 'TSCV.FOCUSINFO = %s, TSCV.FOCUSALARM = %s, TELSTAT.FOCUS = %s' %    \
#            ( self._fmt_( '0x%08x', dict['TSCV.FOCUSINFO'].value()),    \
#              self._fmt_( '0x%08x', dict['TSCV.FOCUSALARM'].value()),    \
#              self._fmt_( '%d', dict['TELSTAT.FOCUS'].value()) )
#        print 'TELSTAT.M2 = %s, TELSTAT.ROTATOR = %s, TELSTAT.ADC = %s' %    \
#            ( self._fmt_( '%d', dict['TELSTAT.M2'].value()),              \
#              self._fmt_( '%d', dict['TELSTAT.ROTATOR'].value()),
#              `dict['TELSTAT.ADC'].value()` )
#        print 'TSCV.INSROTMODE_PF = %s, TSCV.InsRotMode = %s, TSCV.ImgRotMode = %s' %    \
#            ( self._fmt_( '0x%x', dict['TSCV.INSROTMODE_PF'].value()),    \
#              self._fmt_( '0x%x', dict['TSCV.InsRotMode'].value()),       \
#              self._fmt_( '0x%x', dict['TSCV.ImgRotMode'].value()) )
#        print ('TSCV.FOCUSALARM = %s, TELSTAT.ROT_POS = %s, ' + \
#                'TELSTAT.ROT_CMD = %s, TSCV.ImgRotType = %s') %    \
#            ( self._fmt_( '0x%x',  Alarm), \
#              self._fmt_( '%8.3f', dict['TELSTAT.ROT_POS'].value_ArcDeg()), \
#              self._fmt_( '%8.3f', dict['TELSTAT.ROT_CMD'].value_ArcDeg()), \
#              self._fmt_( '0x%x',  dict['TSCV.ImgRotType'].value()) )
#        print 'TSCV.M1Cover = %s, TSCV.M1CoverOnway = %s' %    \
#            ( self._fmt_( '0x%x', dict['TSCV.M1Cover'].value()), \
#              self._fmt_( '0x%x', dict['TSCV.M1CoverOnway'].value()) )

    def printGeom( self):
        """Dummy to override StatPaneBase's"""
        print "GlobalStates has no geometry!"

    def _fmt_(self, fmt, var):
        """Format any variable into a string using format fmt."""
        if  var==None:
            return 'None'
        try:
            return fmt % var
        except:
            return '<' + `var` + '>'

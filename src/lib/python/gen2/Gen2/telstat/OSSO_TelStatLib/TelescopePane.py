#! /usr/local/bin/python
# TelescopePane.py -- Bruce Bon -- 2008-08-27

# Display pane for telescope state data

######################################################################
################   import needed modules   ###########################
######################################################################

import os
import sys

import Tkinter
from Tkconstants import *
import Pmw

import TelStat_cfg
from TelStat_cfg import *
import TelStatLog
from StatIO import *
from DispType import *
from Alert import *

######################################################################
################   assign needed globals   ###########################
######################################################################

StatusKeys = ('TSCV.DomeShutter', 
              'TSCV.TopScreen', 'TSCL.TSFPOS', 'TSCL.TSRPOS',
              'TSCV.WindScreen', 'TSCV.WINDSDRV', 
              'TSCL.WINDSPOS', 'TSCL.WINDSCMD',
              'TSCS.EL', 'STATS.AZDIF', 'STATS.ELDIF', 
              'TELSTAT.FOCUS', 'TELSTAT.M2', 'TELSTAT.ROTATOR', 'TELSTAT.ADC',
              'TELSTAT.M1_CLOSED', 'TELSTAT.DOME_CLOSED', 
              'TELSTAT.EL_STOWED', 'TELSTAT.SLEWING',
              'TSCL.Z',
              'TSCV.ADCONOFF_PF', 'TSCV.ADCMODE_PF',
              'TSCV.ADCInOut', 'TSCV.ADCOnOff', 'TSCV.ADCMode', 
              'TSCV.FOCUSINFO',
              'TSCV.M1Cover', 'TSCV.M1CoverOnway',
              'TELSTAT.ROT_POS', 'TELSTAT.ROT_CMD',
              'TSCV.INSROTROTATION_PF', 'TSCV.INSROTMODE_PF',
              'TSCV.InsRotRotation', 'TSCV.InsRotMode',
              'TSCV.ImgRotRotation', 'TSCV.ImgRotMode', 'TSCV.ImgRotType',
              'TELSTAT.AO',
              'TSCV.CellCover', 'TSCV.TT_Mode', 
              'TSCV.TT_Drive', 'TSCV.TT_DataAvail', 'TSCV.TT_ChopStat',
              'WAV.STG1_PS', 'WAV.STG2_PS', 'WAV.STG3_PS')

LocationPrime   = 0
LocationCs      = 1
LocationNsOpt   = 2
LocationNsIR    = 3
LocationUndefined = 4

ConditionGreen  = 10
ConditionYellow = 20    # must be greater than ConditionGreen
ConditionRed    = 30    # must be greater than ConditionYellow

M1Closed        = 0
M1Open          = 2
M1Other         = 4

TeleErrUndefTopScreen     = TeleErrBase+1
TeleErrUndefWSDrive       = TeleErrBase+2
TeleErrUndefWSMode        = TeleErrBase+3
TeleErrUndefADCMODE_PF    = TeleErrBase+7
TeleErrUndefADCONOFF_PF   = TeleErrBase+8
TeleErrUndefADCMode       = TeleErrBase+9
TeleErrUndefADCOnOff      = TeleErrBase+10
TeleErrUndefADCInOut      = TeleErrBase+11
TeleErrUndefCellCover     = TeleErrBase+12
TeleErrUndefInsRot_PF     = TeleErrBase+13
TeleErrUndefInsRot_Cs     = TeleErrBase+14
TeleErrUndefInsRot_Ns     = TeleErrBase+16
TeleErrUndefImgRotType    = TeleErrBase+17
TeleErrUndefWindScreen    = TeleErrBase+18
TeleErrInconsistentImgRotType = TeleErrBase+19
TeleErrInconsistentAdcInOut   = TeleErrBase+20

TeleWarnPartialM1Cover  = TeleWarnBase

#############################
# Conventions used for coordinates and object specifications:
#
#   - Real geometry is expressed in a coordinate frame whose origin is
#       at the elevation axis and whose units are meters;
#       x increases to the right, y increases down; variable names with
#       a "Meters" suffix are in this coordinate frame
#   - A "normalized" coordinate frame, whose x and y coordinates range from
#       0.0 to 100.0, corresponds to the limits of the TelescopePane window;
#       the origin of this frame is in the upper left of the window, and
#       variable names with a "Norm" suffix are in this coordinate frame;
#       the translation between the Meters and Norm coordinate frames is
#       constant
#   - The display coordinate frame, whose units are pixels, has the same
#       origin as the Norm coordinate frame, but its values change whenever
#       the pane is resized
#   - A point or location in any of these frames is represented by a 
#       2-tuple of following form:  (x,y)
#   - A rectangle or a line is represented by a 2-tuple of point 2-tuples, of
#       the following form:  ( (xmin,ymin), (xmax,ymax) )
# "Base" 4-tuples represent lines nearest the origin that are the basis
# of the rest of the object geometry



# Real coordinates:
DSBaseMeters            = ( (-18.0, -15.5),  ( 18.0, -15.5) )

TSBaseMeters            = ( (-17.0, -14.0),  ( 17.0, -14.0) )
TSRearCoverLen          = 12.5          # meters
TSpanelLen              = 5.0
#TSzeroXMeters           = 5.0
TSzeroXMeters           = 7.2   # fudged to not obstruct 90 deg telescope ray

WSLenMeters             = 14.9+6.0
WSBottomCoverLenMeters  =  6.0
WSMaxYMeters            =  7.5
WSBaseXMeters           =  -17.0
WSBaseMeters            = \
    ( (WSBaseXMeters, WSMaxYMeters-WSLenMeters), (WSBaseXMeters, WSMaxYMeters) )

# vertical positions of on-axis objects
FocusNumPosYMeters      = -12.5
RotPfPosYMeters         = -11.0
M2PosYMeters            =  -9.5
AdcPfPosYMeters         =  -8.0
FocusIdPosYMeters       =  -6.5
M1CoverPosYMeters       =   3.1
M1PosYMeters            =   4.4
CellCoverPosYMeters     =   5.6
AdcCsPosYMeters         =   6.9
RotCsPosYMeters         =   8.2
AoPolarizerPosYMeters   =   9.5

# horizontal offset from axis of innermost Nasmyth objects
NsBaseXOffsetMeters     =  12.5

# radius of mirror, and lower corners of light beam
MirrorRadiusMeters      =  4.0
TelRayLeft0Meters       = (-13.5, MirrorRadiusMeters)
        # 1.5 is a little kludge to reduce apparent distortion from the
        # fact that the y-scale > x-scale (see MetersToNormX,Y below)
TelRayRight0Meters      = (-12.0, -MirrorRadiusMeters)

# Following scale factors translate "real" units (meters) into units in
#    the 100 x 100 normalized Telescope Pane coordinate frame.
MetersToNormX           = 2.35
MetersToNormY           = 3.5
#MetersToNormY          = 2.35



# Following sets the "real" coordinate origin to a location within the
#    100 x 100 "normalized" coordinate frame.  Changing these numbers
#    will offset the entire display within the pane.
ElAxisXNorm             = 50.0
ElAxisYNorm             = 60.0
ElAxisNorm              = (ElAxisXNorm, ElAxisYNorm)


def xLateRealToNorm( realCoords ):
    """Translate real into normalized coordinates."""
    rval = []
    for a in realCoords:
        rval.append( (ElAxisXNorm + a[0]*MetersToNormX, 
                      ElAxisYNorm + a[1]*MetersToNormY) )
    return tuple( rval )

def rotate( coords, s, c ):
    """Rotate left-handed coordinates coords (a 2-tuple of x and y) through 
        an angle represented by s and c, the sin and cos of the elevation."""
    return ((coords[0]*c - coords[1]*s),(coords[1]*c + coords[0]*s),)

# Following are coordinates normalized to 0-100 in both x and y

    # Dome Shutter and Top Screen
DSBaseNorm      = xLateRealToNorm( DSBaseMeters )
DSOutlineNorm   = ( (DSBaseNorm[0][0], DSBaseNorm[0][1]-2.2), 
                    DSBaseNorm[1] )
x0 = DSOutlineNorm[0][0]
w = DSOutlineNorm[1][0] - x0
xl = x0 + 0.05 * w
xh = x0 + 0.95 * w
DSOutlineOpenLeftNorm = ( (x0, DSOutlineNorm[0][1]),
                               (xl, DSOutlineNorm[1][1]) )
DSOutlineOpenRightNorm = ( (xh, DSOutlineNorm[0][1]),
                               (DSOutlineNorm[1][0], DSOutlineNorm[1][1]) )
xl = x0 + 0.2 * w
xh = x0 + 0.8 * w
DSOutlinePartLeftNorm = ( (x0, DSOutlineNorm[0][1]),
                               (xl, DSOutlineNorm[1][1]) )
DSOutlinePartRightNorm = ( (xh, DSOutlineNorm[0][1]),
                               (DSOutlineNorm[1][0], DSOutlineNorm[1][1]) )
DSOutlineTextNorm = ( (xl+xh)/2.0, DSOutlineNorm[1][1]-0.2 )


TSBaseNorm              = xLateRealToNorm( TSBaseMeters )
TSzeroXNorm             = ElAxisXNorm + MetersToNormX * TSzeroXMeters
TSYbaseNorm             = TSBaseNorm[0][1]
TSpanelLenNorm          = MetersToNormX * TSpanelLen
TSRearCoverLenNorm      = MetersToNormX * TSRearCoverLen
TSRearCoverNorm         = ( (TSBaseNorm[1][0]-TSRearCoverLenNorm,TSYbaseNorm-1),
                            (TSBaseNorm[1][0], TSYbaseNorm) )

    # Wind Screen
WSBaseNorm              = xLateRealToNorm( WSBaseMeters )
WSXbaseNorm             = WSBaseNorm[0][0]
WSYminNorm              = WSBaseNorm[0][1]
WSYmaxNorm              = WSBaseNorm[1][1]
WSzeroYNorm             = ElAxisYNorm + \
                         MetersToNormY * (WSMaxYMeters - WSBottomCoverLenMeters)
WSOutlineNorm           = ( (WSXbaseNorm-2,   WSYminNorm), 
                            (WSXbaseNorm,     WSzeroYNorm)  )
WSBottomCoverNorm       = ( (WSXbaseNorm - 2, WSzeroYNorm),
                            (WSXbaseNorm,     WSYmaxNorm)  )

    # Telescope ray
TelRayOriginXNorm       = ElAxisXNorm
TelRayOriginYNorm       = ElAxisYNorm
TelRayOriginNorm        = (TelRayOriginXNorm, TelRayOriginYNorm)

    # On-axis objects -- mostly text boxes
FocusNumNorm            = xLateRealToNorm( 
                ((-8.0, FocusNumPosYMeters),  ( 8.0, FocusNumPosYMeters+1.0)) )

RotPfNorm               = xLateRealToNorm( 
                ((-11.0, RotPfPosYMeters),  ( 11.0, RotPfPosYMeters+1.0)) )

M2Norm                  = xLateRealToNorm(
                ((-9.0, M2PosYMeters),  ( 9.0, M2PosYMeters+1.0)) )

AdcPfNorm               = xLateRealToNorm(
                ((-9.0, AdcPfPosYMeters),  ( 9.0, AdcPfPosYMeters+1.0)) )

FocusIdNorm             = xLateRealToNorm(
                ((-13.0, FocusIdPosYMeters),  ( 13.0, FocusIdPosYMeters+2.0)) )

M1CoverBaseNorm         = xLateRealToNorm(
                ((-11.5, M1CoverPosYMeters), (11.5, M1CoverPosYMeters)) )
M1CoverNorm     = ( (M1CoverBaseNorm[0][0], M1CoverBaseNorm[0][1]-2.2), 
                    M1CoverBaseNorm[1] )
w = M1CoverNorm[1][0] - M1CoverNorm[0][0]
xl = M1CoverNorm[0][0] + 0.05 * w
xh = M1CoverNorm[0][0] + 0.95 * w
M1CoverOpenLeftNorm = ( (M1CoverNorm[0][0], M1CoverNorm[0][1]),
                               (xl, M1CoverNorm[1][1]) )
M1CoverOpenRightNorm = ( (xh, M1CoverNorm[0][1]),
                               (M1CoverNorm[1][0], M1CoverNorm[1][1]) )
xl = M1CoverNorm[0][0] + 0.1 * w
xh = M1CoverNorm[0][0] + 0.9 * w
M1CoverPartLeftNorm = ( (M1CoverNorm[0][0], M1CoverNorm[0][1]),
                               (xl, M1CoverNorm[1][1]) )
M1CoverPartRightNorm = ( (xh, M1CoverNorm[0][1]),
                               (M1CoverNorm[1][0], M1CoverNorm[1][1]) )
M1CoverTextNorm = ( (xl+xh)/2.0, M1CoverNorm[1][1]-0.05 )


M1CoordRadius           = 100.0
M1PosNorm       = (ElAxisXNorm, ElAxisYNorm + M1PosYMeters * MetersToNormY)
M1CoordNorm = ( (M1PosNorm[0]-M1CoordRadius, M1PosNorm[1]-2.0*M1CoordRadius),
                (M1PosNorm[0]+M1CoordRadius, M1PosNorm[1]) )
M1LabelCoordNorm        = ( M1PosNorm[0], M1PosNorm[1] - 1.0 )

M1Extents               = (-88.0, 10.0, -102.0, 10.0)   # degrees


CellCoverBaseNorm               = xLateRealToNorm(
                ((-6.0, CellCoverPosYMeters), (6.0, CellCoverPosYMeters)) )
CellCoverNorm   = ( (CellCoverBaseNorm[0][0], CellCoverBaseNorm[0][1]-2.0), 
                    CellCoverBaseNorm[1] )
w = CellCoverNorm[1][0] - CellCoverNorm[0][0]
xl = CellCoverNorm[0][0] + 0.05 * w
xh = CellCoverNorm[0][0] + 0.95 * w
CellCoverOpenLeftNorm = ( (CellCoverNorm[0][0], CellCoverNorm[0][1]),
                               (xl, CellCoverNorm[1][1]) )
CellCoverOpenRightNorm = ( (xh, CellCoverNorm[0][1]),
                               (CellCoverNorm[1][0], CellCoverNorm[1][1]) )
xl = CellCoverNorm[0][0] + 0.1 * w
xh = CellCoverNorm[0][0] + 0.9 * w
CellCoverPartLeftNorm = ( (CellCoverNorm[0][0], CellCoverNorm[0][1]),
                               (xl, CellCoverNorm[1][1]) )
CellCoverPartRightNorm = ( (xh, CellCoverNorm[0][1]),
                               (CellCoverNorm[1][0], CellCoverNorm[1][1]) )
CellCoverTextNorm = ( (xl+xh)/2.0, CellCoverNorm[1][1]-0.2 )

RotCsNorm       = xLateRealToNorm(
                ((-11.0, RotCsPosYMeters),  ( 11.0, RotCsPosYMeters+1.0)) )

AdcCsNorm       = xLateRealToNorm(
                ((-10.0, AdcCsPosYMeters),  ( 10.0, AdcCsPosYMeters+1.0)) )

AoPolarizerNorm = xLateRealToNorm(
                ((-9.0, AoPolarizerPosYMeters),  ( 9.0, AoPolarizerPosYMeters+1.0)) )


    # Nasmyth IR objects -- text boxes
RotNsIRNorm     = xLateRealToNorm(
           ((-NsBaseXOffsetMeters-1.0, -3.0),  ( -NsBaseXOffsetMeters, 3.0)) )

    # Nasmyth Optical objects -- text boxes
RotNsOptNorm    = xLateRealToNorm(
           ((NsBaseXOffsetMeters, -3.0),  ( NsBaseXOffsetMeters+1.0, 3.0)) )
AdcNsOptNorm    = xLateRealToNorm(
           ((NsBaseXOffsetMeters+1.5, -2.5),  ( NsBaseXOffsetMeters+2.5, 2.5)) )

    # Waveplate objects -- text boxes
WPPolarizerNorm = ((WSXbaseNorm+1,M1CoverNorm[1][1]+1),(CellCoverBaseNorm[0][0]-3,M1CoverNorm[1][1]+5))
WPHalfStageNorm = ((WSXbaseNorm+1,M1CoverNorm[1][1]+5.5),(CellCoverBaseNorm[0][0]-3,M1CoverNorm[1][1]+9.5))
WPQuarterStageNorm = ((WSXbaseNorm+1,M1CoverNorm[1][1]+10),(CellCoverBaseNorm[0][0]-3,M1CoverNorm[1][1]+14))

######################################################################
################   declare class for the pane   ######################
######################################################################

# Telescope State Pane class
class TelescopePane(Tkinter.Canvas,StatPaneBase):

    dataAcquired        = False

    DomeShutter         = 0
    TopScreen           = 0
    TopScreenStr        = ''
    TSFPOS              = 0
    TSRPOS              = 0
    WindScreen          = 0
    WINDSDRV            = 0
    WINDSPOS            = 0
    WINDSCMD            = 0
    EL                  = AngleDDT(0)
    FOCUS               = 0
    FocusStr            = ''
    Z                   = 0
    M2                  = 0
    M2Str               = ''
    ADCONOFF_PF         = 0
    ADCMODE_PF          = 0
    ADCInOut            = 0
    ADCOnOff            = 0
    ADCMode             = 0
    M1Cover             = 0
    M1CoverOnway        = 0
    ROTATOR             = 0
    ROT_POS             = 0
    ROT_CMD             = 0
    INSROTMODE_PF       = 0
    InsRotMode          = 0
    ImgRotMode          = 0
    ImgRotType          = 0
    CellCover           = 0

    rotType = 'P_Opt_InsRot'

    # Audio alert objects which will be used when needed
    wsDrvOffPosHighAlert = AudioAlert(
                          warnAudio=None, alarmAudio=AU_ALARM_WS_HIGH, 
                          alarmMinInterval=60,  # 1 per minute
                          alarmTimeOut=600)     # 10 minutes
    wsDrvOnFreeAlert = AudioAlert(
                          warnAudio=None, alarmAudio=AU_ALARM_WS_FREE, 
                          alarmMinInterval=60,  # 1 per minute
                          alarmTimeOut=600)     # 10 minutes
    wsObstructAlert = AudioAlert(
                          warnAudio=None, alarmAudio=AU_ALARM_WS_OBSTRUCT,
                          alarmMinInterval=60,  # 1 per minute
                          alarmTimeOut=600)     # 10 minutes

    primeADCalert = AudioAlert(
                          warnAudio=AU_WARN_ADC_PF_FREE, alarmAudio=None, 
                          warnMinInterval=600 ) # 1 per 10 minutes
    cassegrainADCalert = AudioAlert(
                          warnAudio=AU_WARN_ADC_CS_FREE, alarmAudio=None, 
                          warnMinInterval=600 ) # 1 per 10 minutes
    nasmythADCalert = AudioAlert(
                          warnAudio=AU_WARN_ADC_NS_FREE, alarmAudio=None, 
                          warnMinInterval=600 ) # 1 per 10 minutes

    tiptiltOffAlert = AudioAlert(
                          warnAudio=AU_WARN_TIPTILT_OFF, alarmAudio=None, 
                          warnMinInterval=10,   # 1 per 10 seconds
                          warnTimeOut=48 )      # total of 5 warnings
    tiptiltOnPrev = False
    tiptiltSoundWarning = False

    def __init__( self, parent, widWidth=300, widHeight=300):
        """Telescope State Pane constructor."""
        Tkinter.Canvas.__init__(self, parent, name='telescope pane',
            width=widWidth, height=widHeight,
            borderwidth=paneBorderWidth, relief=paneBorderRelief)
        StatPaneBase.__init__(self, StatusKeys, 'TelescopePane' )
        self.parent     = parent
        self["bg"] = TELPANEBACKGROUND
        self.widWidth   = widWidth
        self.widHeight  = widHeight
        self.resize( widWidth, widHeight )
        self.bind("<ButtonRelease-1>", self.geomCB)
#?      TelStatLog.TelStatLog( TeleInfoBase, `self, " options:\n", self.config()` )
#?      print "\n", self, " options:\n", self.config()  # debug
        self.ndx = 0


    #######################################################################
    ### resize method, called only by constructor and when pane is resized
    #######################################################################

    def resize( self, widWidth, widHeight ):
        """Recompute any size-dependent positions, and redisplay all."""
        # resize methods may NOT access winfo functions to get their own
        # widths/heights, because such cannot be forced to be correct size
        widWidth  -= paneBorderWidth*3
        widHeight -= paneBorderWidth*3
        if  widWidth < 100:
            widWidth = 100              # less is unreasonable!
        if  widHeight < 100:
            widHeight = 100             # less is unreasonable!
        #? print "self.geom:    %d x %d" % (self.winfo_width(),self.winfo_height())
        #? print "resize to:    %d x %d\n" % (widWidth, widHeight)
        #? print '**>> Scales: MetersToNormX = %f, MetersToNormY = %f' % \
        #?      (MetersToNormX, WSMetersToNormY)
        Tkinter.Canvas.configure(self, width=widWidth, height=widHeight )
        self.xScale = widWidth / 100.0
        self.yScale = widHeight / 100.0
        self.redrawBg()
        if  self.dataAcquired:
            self.redrawFg()

    #####################################################################
    ### refresh method, called during StatIO update
    #####################################################################

    def refresh(self, dict):
        """Refresh pane with updated values from dict."""
        #? print "    Telescope Pane received refresh call:"
        # Debugging printout
        #? for  key in StatusKeys:
        #?     print "      %-20s   %s" % \
        #?          (key, StatusDictionary.StatusDictionary[key][0].format())

        if  not self.dataAcquired:
            self.dataAcquired = True

        #print "EXTRACTING DATA"
        # Get all data needed for update
        self.FOCUS       = dict['TELSTAT.FOCUS'].value()
        self.M2          = dict['TELSTAT.M2'].value()
        self.ROTATOR     = dict['TELSTAT.ROTATOR'].value()
        self.M1_CLOSED   = dict['TELSTAT.M1_CLOSED'].value()
        self.ADC         = dict['TELSTAT.ADC'].value()
        self.DOME_CLOSED = dict['TELSTAT.DOME_CLOSED'].value()
        self.EL_STOWED   = dict['TELSTAT.EL_STOWED'].value()
        self.SLEWING     = dict['TELSTAT.SLEWING'].value()
        self.ROT_POS     = dict['TELSTAT.ROT_POS'].value_ArcDeg()
        self.ROT_CMD     = dict['TELSTAT.ROT_CMD'].value_ArcDeg()
        self.DomeShutter = dict['TSCV.DomeShutter'].value()
        self.TopScreen   = dict['TSCV.TopScreen'].value()
        self.TSFPOS      = dict['TSCL.TSFPOS'].value()
        self.TSRPOS      = dict['TSCL.TSRPOS'].value()
        self.WindScreen  = dict['TSCV.WindScreen'].value()
        self.WINDSDRV    = dict['TSCV.WINDSDRV'].value()
        self.WINDSPOS    = dict['TSCL.WINDSPOS'].value()
        self.WINDSCMD    = dict['TSCL.WINDSCMD'].value()
        self.EL          = dict['TSCS.EL']
        self.AZDIF       = dict['STATS.AZDIF']
        self.ELDIF       = dict['STATS.ELDIF']
        self.Z           = dict['TSCL.Z'].value()
        self.ADCONOFF_PF = dict['TSCV.ADCONOFF_PF'].value()
        self.ADCMODE_PF  = dict['TSCV.ADCMODE_PF'].value()
        self.ADCInOut    = dict['TSCV.ADCInOut'].value()
        self.ADCOnOff    = dict['TSCV.ADCOnOff'].value()
        self.ADCMode     = dict['TSCV.ADCMode'].value()
        self.FOCUSINFO   = dict['TSCV.FOCUSINFO'].value()
        self.M1Cover     = dict['TSCV.M1Cover'].value()
        self.M1CoverOnway = dict['TSCV.M1CoverOnway'].value()
        self.INSROTROTATION_PF = dict['TSCV.INSROTROTATION_PF'].value()
        self.INSROTMODE_PF  = dict['TSCV.INSROTMODE_PF'].value()
        self.InsRotRotation = dict['TSCV.InsRotRotation'].value()
        self.InsRotMode     = dict['TSCV.InsRotMode'].value()
        self.ImgRotRotation = dict['TSCV.ImgRotRotation'].value()
        self.ImgRotMode     = dict['TSCV.ImgRotMode'].value()
        self.ImgRotType     = dict['TSCV.ImgRotType'].value()
        self.AO             = dict['TELSTAT.AO'].value()
        self.CellCover      = dict['TSCV.CellCover'].value()
        self.TT_Mode        = dict['TSCV.TT_Mode'].value()
        self.TT_Drive       = dict['TSCV.TT_Drive'].value()
        self.TT_DataAvail   = dict['TSCV.TT_DataAvail'].value()
        self.TT_ChopStat    = dict['TSCV.TT_ChopStat'].value()
        self.Waveplate1     = dict['WAV.STG1_PS'].value()
        self.Waveplate2     = dict['WAV.STG2_PS'].value()
        self.Waveplate3     = dict['WAV.STG3_PS'].value()


        # Redraw foreground
        #print "REDRAWING"
        self.redrawFg()
        #print "REDRAWED"

    #####################################################################
    ### primitive methods for drawing in normalized (0-100) coordinates
    #####################################################################

    def drawText( self, text, normCoords, anchor=SW, font=fontTiny,
                  textColor=TELPANEFOREGROUND, textFillColor=TRANSPARENT, 
                  tags=('F',)):
        """Draw text at normCoords, anchored as specified."""
        x = self.xScale * normCoords[0]
        y = self.yScale * normCoords[1]
        if  textFillColor==TRANSPARENT or textFillColor == TELPANEBACKGROUND:
            self.create_text( x, y, text=text, font=font, anchor=anchor, 
                                justify=CENTER, fill=textColor, tags=tags )
        else:
            self.create_window(x, y, anchor=anchor, tags=tags,
                                   window=Tkinter.Label(self,text=text,
                                      bd=0,relief=SOLID,
                                      bg=textFillColor,fg=textColor,font=font) )


    def drawLine( self, normCoords, fillColor=TELPANEFOREGROUND, tags=('F',) ):
        """Draw a line (or n lines) at normCoords with the given color and tags."""
        coords = [ normCoords[0][0]*self.xScale,        \
                   normCoords[0][1]*self.yScale,        \
                   normCoords[1][0]*self.xScale,        \
                   normCoords[1][1]*self.yScale          ]
        self.create_line( coords, fill=fillColor, tags=tags )


    def drawRect( self, normCoords, 
                  outlineColor=TELPANEFOREGROUND, fillColor=TRANSPARENT, 
                  textColor=TELPANEFOREGROUND, textFillColor=TRANSPARENT,
                  font=fontTiny, anchor=CENTER, label='',tags=('F',) ):
        """Draw a rectangle at normCoords with the given colors and tags."""
        #? print 'drawRect: normCoords  =', normCoords
        xMin = self.xScale * normCoords[0][0]
        yMin = self.yScale * normCoords[0][1]
        xMax = self.xScale * normCoords[1][0]
        yMax = self.yScale * normCoords[1][1]
        self.create_rectangle( xMin, yMin, xMax, yMax,
            fill=fillColor, outline=outlineColor,tags=tags )
        if  len(label) > 0:
            xText = xMin+2      # good for W, NW, SW
            yText = yMin+2      # good for N, NW, NE
            if  anchor == CENTER:
                xText = (xMin+xMax)/2
                yText = (yMin+yMax)/2
            elif  anchor.find(E) >= 0:
                xText = xMax-2  # good for E, NE, SE
            elif  anchor.find(S) >= 0:
                yText = yMax-2  # good for S, SW, SE
            if  textFillColor==TRANSPARENT or textFillColor==TELPANEBACKGROUND:
                self.create_text( xText, yText, text=label, fill=textColor,
                                  font=font, anchor=anchor, tags=tags )
            else:
                self.create_window(xText, yText, anchor=anchor, tags=tags,
                                   window=Tkinter.Label(self,text=label,
                                      bd=0,relief=SOLID,
                                      bg=textFillColor,fg=textColor,font=font) )

    def drawOval( self, normCoords, outlineColor, fillColor, font=fontTiny,
                  anchor=CENTER, label='',tags=('F',) ):
        """Draw an oval at normCoords with the given colors and tags."""
        xMin = self.xScale * normCoords[0][0]
        yMin = self.yScale * normCoords[0][1]
        xMax = self.xScale * normCoords[1][0]
        yMax = self.yScale * normCoords[1][1]
        self.create_oval( xMin, yMin, xMax, yMax,
            fill=fillColor, outline=outlineColor,tags=tags )
        if  len(label) > 0:
            xText = xMin        # good for W, NW, SW
            yText = yMin        # good for N, NW, NE
            if  anchor == CENTER:
                xText = (xMin+xMax)/2
                yText = (yMin+yMax)/2
            elif  anchor.find(E) >= 0:
                xText = xMax    # good for E, NE, SE
            elif  anchor.find(S) >= 0:
                yText = yMax    # good for S, SW, SE
            self.create_text( xText, yText, text=label,
                                font=font, anchor=anchor, tags=tags )

    def drawArc( self, normCoords, start, extent, style=ARC, 
                  outlineColor=TELPANEFOREGROUND, tags=('F',) ):
        """Draw an arc specified by normCoords, start, extent and style,
                with the given colors and tags."""
        xMin = self.xScale * normCoords[0][0]
        yMin = self.yScale * normCoords[0][1]
        xMax = self.xScale * normCoords[1][0]
        yMax = self.yScale * normCoords[1][1]
        self.create_arc( xMin, yMin, xMax, yMax, start=start, extent=extent, 
            style=style, outline=outlineColor, tags=tags )

    def drawPoly( self, normCoords, outlineColor=TELPANEOUTLINE, 
                  fillColor=TRANSPARENT, tags=('F',) ):
        """Draw a polygon at normCoords with the given colors and tags."""
        #? print 'drawNorm: normCoords:'
        pixCoords = []
        for a in normCoords:
            #? print '  ', a
            pixCoords.append( (a[0] * self.xScale, 
                               a[1] * self.yScale) )
        #self.create_polygon( tuple( pixCoords ),
        #    fill=fillColor, stipple=TELSTAT_LIGHTPATH_BIT, outline=outlineColor,tags=tags )
        self.create_polygon( tuple( pixCoords ),
            fill=fillColor, stipple="gray12", outline=outlineColor,tags=tags )

    #####################################################################
    ### methods for drawing components of display
    #####################################################################

    def drawDomeShutter( self ):
        """Draw dome shutter."""
        if  self.DomeShutter == None:
            self.drawRect( DSOutlinePartLeftNorm, 
                                TELPANEFOREGROUND, TELPANECLOSED )
            self.drawRect( DSOutlinePartRightNorm, 
                                TELPANEFOREGROUND, TELPANECLOSED )
            self.drawText( 'No Dome Shutter Data', DSOutlineTextNorm,
                            font=fontTinyBold, anchor=S, tags=('F',) )
        else:
            ds = self.DomeShutter & 0x50
            if  ds == 0x50:             # OPEN
                self.drawText( 'Dome Shutter Open', DSOutlineTextNorm,
                    font=fontTinyBold, anchor=S, tags=('F',) )
                self.drawRect( DSOutlineOpenLeftNorm, 
                                    TELPANEFOREGROUND, TELPANEBACKGROUND )
                self.drawRect( DSOutlineOpenRightNorm, 
                                    TELPANEFOREGROUND, TELPANEBACKGROUND )
            elif  ds == 0x00:   # NOT OPEN
                self.drawRect( DSOutlineNorm, 
                        outlineColor=TELPANEFOREGROUND, fillColor=TELPANECLOSED,
                        textColor=TELPANEFOREGROUND, textFillColor=TRANSPARENT,
                        font=fontTinyBold, label=' Dome Shutter Not Open' )
            else:                       # partially open
                self.drawRect( DSOutlinePartLeftNorm, 
                                    TELPANEFOREGROUND, TELPANECLOSED )
                self.drawRect( DSOutlinePartRightNorm, 
                                    TELPANEFOREGROUND, TELPANECLOSED )
                self.drawText( ' Dome Shutter Partial (%x)' % ds, 
                                DSOutlineTextNorm,
                                font=fontTinyBold, anchor=S, tags=('F',) )

    def drawTopScreen( self ):
        """Draw top screen."""
        fillColor = TELPANEBACKGROUND
        TopScreenStr = ''
        if  self.TopScreen == None:
            fillColor = TELPANEALARMFOREGROUND
            TopScreenStr = 'No Data'
        else:
            if  self.TopScreen & 0x10:
                TopScreenStr += 'Free Mode'
            elif  self.TopScreen & 0x0C:
                TopScreenStr += 'Link Mode'
            if  len(TopScreenStr) == 0:
                fillColor = TELPANEALARMFOREGROUND
                TopScreenStr = 'Mode Undefined (%x)' % self.TopScreen
                TelStatLog.TelStatLog( TeleErrUndefTopScreen, 
                            ("ERROR (TelescopePane:drawTopScreen):  " +
                            "Undefined TopScreen Mode = %x") % \
                            self.TopScreen )

        if  self.TSFPOS == None or self.TSRPOS == None:
            fillColor = TELPANEALARMFOREGROUND
            self.drawText( "Top Screen %s, No Data" % TopScreenStr, 
                ( (TSBaseNorm[0][0]+TSBaseNorm[1][0])/2.0, 
                                                TSBaseNorm[0][1]+0.5 ),
                textFillColor=fillColor, font=fontSmallBold, anchor=N, 
                tags=('F',) )
            return

        fNx = TSzeroXNorm - MetersToNormX*self.TSFPOS
        
        fNxCoord = ( (fNx, TSYbaseNorm-1), (fNx+TSpanelLenNorm, TSYbaseNorm-2))
        self.drawRect( fNxCoord, TELPANEFOREGROUND, TELPANECLOSED )
        rNx0 = TSzeroXNorm - MetersToNormX*self.TSRPOS
        if  self.TSRPOS <= 5.0:
            rNx1 = rNx0
        elif  self.TSRPOS <= 10.0:
            rNx1 = rNx0 + (self.TSRPOS-5.0) * TSpanelLenNorm / 5.0
        else:
            rNx1 = rNx0 + TSpanelLenNorm

        TSR0nCoord = ( (rNx0, TSYbaseNorm-2), 
                       (rNx0+TSpanelLenNorm, TSYbaseNorm-3) )
        TSR1nCoord = ( (rNx1, TSYbaseNorm-3), 
                       (rNx1+TSpanelLenNorm, TSYbaseNorm-4) )
        self.drawRect( TSR0nCoord, TELPANEFOREGROUND, TELPANECLOSED )
        self.drawRect( TSR1nCoord, TELPANEFOREGROUND, TELPANECLOSED )
        self.drawText( "Top Screen %s" % TopScreenStr, 
                ( (TSBaseNorm[0][0]+TSBaseNorm[1][0])/2.0, 
                                                TSBaseNorm[0][1]+0.5 ),
                textFillColor=fillColor, font=fontSmallBold, anchor=N, 
                tags=('F',) )

    def drawWindScreen( self ):
        """Draw wind screen."""
        # Precompute alert suppression boolean
        SoundWsAlert =          \
             not self.SLEWING and not self.M1_CLOSED and \
             not self.DOME_CLOSED and not self.EL_STOWED
        #? self.ndx += 1
        #? print "WS %d: SoundWsAlert = %s" % (self.ndx, `SoundWsAlert`)
        #? print "WS: ws = %s, drv = %s, pos = %s, cmd = %s, dif = %f" %        \
        #?   (`self.WindScreen`, `self.WINDSDRV`, `self.WINDSPOS`, `self.WINDSCMD`,
        #?      self.WINDSCMD-self.WINDSPOS )
        xOffset = 2
        textFillColor = TRANSPARENT
        fillColor = TELPANECLOSED       # green
        # Precompute local state
        if  self.WINDSDRV == None:
            wsDrv = False       # treat like off
        elif  self.WINDSDRV == 0x08:
            wsDrv = False       # == off
        elif  self.WINDSDRV == 0x04:
            wsDrv = True        # == on
        else:
            wsDrv = False       # treat like off, but log an error
            TelStatLog.TelStatLog( TeleErrUndefWSDrive,
                                   ("ERROR (TelescopePane:drawWindScreen):  " +
                                   "Undefined WindScreen Drive = %x") % \
                                   self.WINDSDRV )
        if  wsDrv == None:      # should never get this, unless we change above
            wsStr = 'No WS\nDrv Data'
            xOffset = 0
        else:
            if  self.WindScreen == None:
                wsStr = 'No Mode Data'
            elif  self.WindScreen == 0x01:
                wsStr = 'WindScreen\nLink'
            elif  self.WindScreen == 0x02:
                wsStr = 'WindScreen\nFree'
            else:
                textFillColor = fillColor = TELPANEALARMFOREGROUND
                wsStr = 'WindScreen\nMode Undefined (%x)' % self.WindScreen
                TelStatLog.TelStatLog( TeleErrUndefWindScreen,
                                ("ERROR (TelescopePane:drawWindScreen):  " +
                                "Undefined WindScreen Mode = %x") % \
                                self.WindScreen )
                xOffset = max( xOffset, 6 )
        # Compute foreground colors and send audio alerts, if any
        if  self.WINDSPOS == None:
            textFillColor = fillColor = TELPANEALARMFOREGROUND
            wsStr += '\nNo Pos Data'
        elif  self.WINDSCMD == None:
            textFillColor = fillColor = TELPANEALARMFOREGROUND
            wsStr += '\nNo Cmd Data'
        elif  wsDrv == False and self.WINDSPOS <= 5.0:
            pass        # GREEN, no alerts
        elif  wsDrv == False and self.WINDSPOS > 5.0:   # drive off and ws high
            fillColor = textFillColor = TELPANEALARMFOREGROUND
            wsStr += '\nDrvOff/PosHigh'
            xOffset = max( xOffset, 5 )
            if  SoundWsAlert:
                self.wsDrvOffPosHighAlert.alert(level=ALARM)
        elif  wsDrv and self.WindScreen == 0x02:        # drive on and Free
            fillColor = textFillColor = TELPANEALARMFOREGROUND
            wsStr += '\nDriveOn'
            #xOffset = max( xOffset, 6 )
            if  SoundWsAlert:
                self.wsDrvOnFreeAlert.alert(level=ALARM)
        elif  wsDrv and self.WindScreen == 0x01 and             \
                fabs(self.WINDSCMD-self.WINDSPOS) <= 1.0:
            pass        # GREEN, no alerts
        elif  wsDrv and self.WindScreen == 0x01 and             \
                self.WINDSCMD-self.WINDSPOS > 1.0:
            if  fillColor != TELPANEALARMFOREGROUND:
                textFillColor = fillColor = TELPANEWARNFOREGROUND
            wsStr += '\nPos!=Cmd'
            #xOffset = max( xOffset, 9 )
        elif  wsDrv and self.WindScreen == 0x01:# self.WINDSCMD-self.WINDSPOS<-1
                                                # WS may obstruct telescope
            fillColor = textFillColor = TELPANEALARMFOREGROUND
            wsStr += '\nWS OBSTRUCT'
            xOffset = max( xOffset, 4 )
            if  SoundWsAlert:
                self.wsObstructAlert.alert(level=ALARM)
        else:   # WindScreen undefined
            textFillColor = fillColor = TELPANEWARNFOREGROUND
        # compute graphic coordinates for drawing and draw box
        if  self.WINDSPOS != None:
            wsCoord = ( (WSXbaseNorm,WSzeroYNorm - MetersToNormY*self.WINDSPOS),
                        (WSXbaseNorm-2, WSzeroYNorm) )
            #? print 'drawWindScreen: wsCoord  =', wsCoord, \
            #?                  ', WINDSPOS = ', self.WINDSPOS
            self.drawRect( wsCoord, fillColor=fillColor )
        # draw text
        self.drawText( wsStr, (WSXbaseNorm+xOffset,WSYmaxNorm+0.4), 
                        textFillColor=textFillColor, anchor=N, font=fontSmallBold )


    def drawTelescopeRay( self ):
        """Draw telescope ray indicating elevation."""
        if  self.EL.value() == None:
            return
        s = self.EL.sin()
        c = self.EL.cos()
        rayMeters = rotate( (-100.0,0.0), s, c )
        rayLeftMeters  = rotate( TelRayLeft0Meters, s, c )
        rayRightMeters = rotate( TelRayRight0Meters, s, c )
        rayNorm = (rayMeters[0] * MetersToNormX, rayMeters[1] * MetersToNormY )
        rayLeftNorm  = xLateRealToNorm( (rayLeftMeters, ) )[0]
        rayRightNorm = xLateRealToNorm( (rayRightMeters,) )[0]
        rayLeftInfNorm  = \
                  ( rayLeftNorm[0]  + rayNorm[0], rayLeftNorm[1]  + rayNorm[1] )
        rayRightInfNorm  = \
                  ( rayRightNorm[0] + rayNorm[0], rayRightNorm[1] + rayNorm[1] )
#       normCoords = ( TelRayOriginNorm, rayLeftNorm, 
        normCoords = ( rayLeftNorm, 
                        rayLeftInfNorm, rayRightInfNorm, rayRightNorm )
        self.drawPoly(
                normCoords,outlineColor=TELPANERAYOUTLINE, fillColor=TELPANERAY)
        self.drawLine( 
           ( TelRayOriginNorm, 
             (TelRayOriginNorm[0]+rayNorm[0], TelRayOriginNorm[1]+rayNorm[1]) ),
           fillColor=TELPANERAYOUTLINE, tags=('F',) )
        
    def drawFocus( self ):
        """Draw focus Z box."""
        fillColor = TELPANEBACKGROUND
        if  self.Z == None:
            fillColor = TELPANEALARMFOREGROUND
            label = 'Focus = No Data'
        else:
            label = 'Focus = %.4f mm' % self.Z
        self.drawRect( FocusNumNorm, TELPANEFOREGROUND, fillColor,
                        font=fontSmallBold, label=label )
        
    def drawM2( self ):
        """Draw M2 box -- either 'M2' or 'SPCAM'."""
        fillColor = TELPANEBACKGROUND
        addSuffix = False
        tiptiltOn = False
        # Find primary label
        if  self.M2 == None:
            fillColor = TELPANEALARMFOREGROUND
            M2Str = 'M2 No Data'
        elif  self.M2 == M2_IR:
            M2Str = 'IR M2'
            addSuffix = True        # ONLY add suffix if IR M2
        elif  self.M2 == M2_CS_OPT:
            M2Str = 'Cs Opt M2'
        elif  self.M2 == M2_NS_OPT:
            M2Str = 'Ns Opt M2'
        elif  self.M2 == M2_PF_OPT:
            M2Str = 'SPCAM at M2'
        elif  self.M2 == M2_PF_IR:
            M2Str = 'FMOS at M2'
        elif  self.M2 == M2_PF_OPT2:
            M2Str = 'HSC at M2'
        else:   # self.M2 == UNDEF
            fillColor = TELPANEALARMFOREGROUND
            M2Str = 'M2 Undefined'
        # No label suffix unless all of following conditions are met:
        if  addSuffix and    \
            self.TT_Mode != None and self.TT_Drive != None and  \
            self.TT_DataAvail != None and self.TT_ChopStat != None and  \
            self.TT_Mode&0x07 and  \
            self.TT_Drive&0x01 and \
            not (self.TT_Drive&0x02):
            # if we get here, we know:
            #     IR M2
            #     TT_Mode indicates either tip/tilt, chopping or position modes
            #     TT_Drive indicates Drive On and NOT Drive Off
            tiptiltOn = True
            # Find label suffix
            if  self.TT_Mode&0x47 == 0x04:
                # Position mode -- mode is OK, but no display
                pass
            elif  self.TT_Mode&0x47 == 0x02:
                # Tip-Tilt mode
                M2Str += " (Tip/Tilt)"
                if  not self.TT_DataAvail&0x01:
                    # not Data Available
                    fillColor = TELPANEWARNFOREGROUND
            elif  self.TT_Mode&0x47 == 0x01:
                # Chopping mode
                M2Str += " (Chopping)"
                if  self.TT_ChopStat&0x02 or (self.TT_ChopStat&0x05 != 0x05):
                    # Chopping Stop OR not chopping start OR not ch start ready
                    fillColor = TELPANEWARNFOREGROUND
            else:
                # Bad mode
                M2Str += " (UndefMode)"
                fillColor = TELPANEWARNFOREGROUND
        # Draw it!
        self.drawRect( M2Norm, TELPANEFOREGROUND, fillColor,
                        font=fontBold, label=M2Str )

        #? print 'tiptiltOn = ', tiptiltOn
        # Test for Tip/Tilt transitions between on and off
        #   When no transition, don't change self.tiptiltSoundWarning
        if  self.tiptiltOnPrev:
            if  not tiptiltOn:  # on-to-off transition -- sound warning
                self.tiptiltSoundWarning = True
        else:           # not tiptiltOnPrev
            if  tiptiltOn:      # off-to-on transition -- turn warning off
                self.tiptiltSoundWarning = False
                self.tiptiltOffAlert.resetFirstTime()

        # Save tiptiltOn for next refresh and and sound alert if needed
        self.tiptiltOnPrev = tiptiltOn
        if  self.tiptiltSoundWarning:
            self.tiptiltOffAlert.alert()


    def drawAdc( self ):
        """Draw ADC box at appropriate focus location."""
        # Determine whether to sound audio alert for ADC in Free mode
        # The conditions used here are computed by the GlobalStates.py module.
        # They are taken to mean that the telescope is currently inactive or
        # slewing, so that the ADC mode is unimportant.
        if self.M1_CLOSED or self.DOME_CLOSED or self.EL_STOWED or self.SLEWING:
            SoundAdcAlert = False
        else:
            SoundAdcAlert = True
        # Now interpret the ADC values
        fillColor = TELPANEBACKGROUND
        textFillColor = TRANSPARENT
        if  self.FOCUS == None or self.FOCUS == UNDEF:
            return  # display nothing if focus is unknown

        elif  self.FOCUS == FOCUS_PF_OPT or self.FOCUS == FOCUS_PF_OPT2:
            if  self.ADC == None:
                # Should NEVER get here!
                fillColor = TELPANEALARMFOREGROUND
                adcStr = 'ADC No Data'
            elif  self.ADC == UNDEF:
                # Should NEVER get here!
                adcStr = 'ADC Undefined'
                fillColor = TELPANEALARMFOREGROUND
            elif  self.ADC == ADC_OUT:
                # Should NEVER get here for FOCUS_PF_OPT, but ok
                # for FOCUS_PF_OPT2, which might have ADC Out
                if self.FOCUS == FOCUS_PF_OPT:
                    adcStr   = 'No ADC'
                else:
                    adcStr   = 'ADC Out'
            elif  self.ADC == ADC_IN:
                if  self.ADCONOFF_PF == None:
                    fillColor = TELPANEALARMFOREGROUND
                    adcStr   = 'No ADC On/Off Data'
                elif  self.ADCONOFF_PF == 0x02:                 # Power Off
                    fillColor = TELPANEALARMFOREGROUND
                    if  SoundAdcAlert:
                        self.primeADCalert.alert()
                    adcStr   = 'ADC Free'
                elif  self.ADCONOFF_PF == 0x01:                 # Power On
                    if  self.ADCMODE_PF == None:
                        fillColor = TELPANEALARMFOREGROUND
                        adcStr   = 'No ADC Mode Data'
                    elif  self.ADCMODE_PF == 0x40:
                        adcStr   = 'ADC Link'
                    elif  self.ADCMODE_PF == 0x80:
                        fillColor = TELPANEALARMFOREGROUND
                        if  SoundAdcAlert:
                            self.primeADCalert.alert()
                        adcStr   = 'ADC Free'
                    else:
                        fillColor = TELPANEALARMFOREGROUND
                        adcStr   = 'ADC Undefined (%s,%s)' % \
                                        (self._fmt_( '%x', self.ADCONOFF_PF), \
                                         self._fmt_( '%x', self.ADCMODE_PF))
                        TelStatLog.TelStatLog( TeleErrUndefADCMODE_PF,
                            ("ERROR (TelescopePane:drawAdc 1):  Undefined " +
                             "ADC: ADCONOFF_PF = %s, ADCMODE_PF = %s") % \
                                      (self._fmt_( '0x%x', self.ADCONOFF_PF), \
                                       self._fmt_( '0x%x', self.ADCMODE_PF)) )
                else:
                    fillColor = TELPANEALARMFOREGROUND
                    adcStr   = 'ADC Undefined (%s,%s)' % \
                                        (self._fmt_( '%x', self.ADCONOFF_PF), \
                                         self._fmt_( '%x', self.ADCMODE_PF))
                    TelStatLog.TelStatLog( TeleErrUndefADCONOFF_PF,
                           ("ERROR (TelescopePane:drawAdc 2):  Undefined " +
                            "ADC: ADCONOFF_PF = %s, ADCMODE_PF = %s") %  \
                                      (self._fmt_( '0x%x', self.ADCONOFF_PF), \
                                       self._fmt_( '0x%x', self.ADCMODE_PF)) )
            else:
                # Should NEVER get here!
                fillColor = textFillColor = TELPANEALARMFOREGROUND
                adcStr   = 'ADC Undefined (%s,%s,%s)' % \
                            (`self.ADC`, `self.ADCONOFF_PF`, `self.ADCMODE_PF`)
                TelStatLog.TelStatLog( TeleErrUndefADCInOut,
                           ("ERROR (TelescopePane:drawAdc 3):  " +
                            "Undefined TELSTAT.ADC = %s") % `self.ADC` )
            self.drawRect( AdcPfNorm, fillColor=fillColor, 
                               font=fontSmallBold, label=adcStr )
            # endif  self.FOCUS == FOCUS_PF_OPT or self.FOCUS == FOCUS_PF_OPT2

        elif  self.FOCUS == FOCUS_CS_OPT:
#            print 'self.ADC = %s, self.ADCOnOff = %s, self.ADCMode = %s' %    \
#                    ( `self.ADC`,  self._fmt_( '0x%08x', self.ADCOnOff),    \
#                      self._fmt_( '0x%08x', self.ADCMode) )
            if  self.ADC == None:
                fillColor = TELPANEALARMFOREGROUND
                adcStr = 'ADC No Data'
            elif  self.ADC == UNDEF:
                adcStr = 'ADC Undefined'
                fillColor = TELPANEALARMFOREGROUND
            elif  self.ADC == ADC_OUT:
                adcStr   = 'No ADC'
            elif  self.ADC == ADC_IN:
                if  self.ADCOnOff == None:
                    fillColor = TELPANEALARMFOREGROUND
                    adcStr   = 'No ADC On/Off Data'
                elif  self.ADCOnOff == 0x02:                    # Power Off
                    fillColor = TELPANEALARMFOREGROUND
                    if  SoundAdcAlert:
                        self.cassegrainADCalert.alert()
                    adcStr   = 'ADC Free'
                elif  self.ADCOnOff == 0x01:                    # Power On
                    if  self.ADCMode == None:
                        fillColor = TELPANEALARMFOREGROUND
                        adcStr   = 'No ADC Mode Data'
                    elif  self.ADCMode == 0x04:     # Link
                        adcStr   = 'ADC Link'
                    elif  self.ADCMode == 0x08:     # Free
                        fillColor = TELPANEALARMFOREGROUND
                        if  SoundAdcAlert:
                            self.cassegrainADCalert.alert()
                        adcStr   = 'ADC Free'
                    else:
                        fillColor = TELPANEALARMFOREGROUND
                        adcStr   = 'ADC Undefined (%s,%s)' % \
                                        (self._fmt_( '%x', self.ADCOnOff), \
                                         self._fmt_( '%x', self.ADCMode))
                        TelStatLog.TelStatLog( TeleErrUndefADCMode,
                                   ("ERROR (TelescopePane:drawAdc 4):  " +
                                    "Undefined ADC: ADCOnOff = %s, " +
                                    "ADCMode = %s") % \
                                     (self._fmt_( '0x%x', self.ADCOnOff), \
                                      self._fmt_( '0x%x', self.ADCMode)) )
                else:
                    fillColor = TELPANEALARMFOREGROUND
                    adcStr   = 'ADC Undefined (%s,%s)' % \
                                        (self._fmt_( '%x', self.ADCOnOff), \
                                         self._fmt_( '%x', self.ADCMode))
                    TelStatLog.TelStatLog( TeleErrUndefADCOnOff,
                                ("ERROR (TelescopePane:drawAdc 5):  " +
                                 "Undefined ADC: ADCOnOff = %s, " +
                                 "ADCMode = %s") % \
                                  (self._fmt_( '0x%x', self.ADCOnOff), \
                                   self._fmt_( '0x%x', self.ADCMode)) )
            else:
                # Should NEVER get here!
                fillColor = textFillColor = TELPANEALARMFOREGROUND
                adcStr   = 'ADC Undefined (%s,%s,%s)' % \
                            (`self.ADC`, `self.ADCOnOff`, `self.ADCMode`)
                TelStatLog.TelStatLog( TeleErrUndefADCInOut,
                           ("ERROR (TelescopePane:drawAdc 6):  " +
                            "Undefined TELSTAT.ADC = %s") % `self.ADC` )
            self.drawRect( AdcCsNorm, fillColor=fillColor, 
                           font=fontBold, label=adcStr )

        elif  self.FOCUS  == FOCUS_NS_OPT:
            if  self.ADC == None:
                fillColor = TELPANEALARMFOREGROUND
                adcStr = 'ADC\nNo Data'
            elif  self.ADC == UNDEF:
                adcStr = 'ADC\nUndefined'
                fillColor = TELPANEALARMFOREGROUND
            elif  self.ADC == ADC_OUT:
                adcStr   = 'No\nADC'
            elif  self.ADC == ADC_IN:
                if  self.ADCOnOff == None:
                    fillColor = TELPANEALARMFOREGROUND
                    adcStr   = 'No ADC\nOn/Off Data'
                elif  self.ADCOnOff == 0x02:                    # Power Off
                    fillColor = textFillColor = TELPANEALARMFOREGROUND
                    if  SoundAdcAlert:
                        self.nasmythADCalert.alert()
                    adcStr   = 'ADC\nFree'
                elif  self.ADCOnOff == 0x01:                    # Power On
                    if  self.ADCMode == None:
                        fillColor = TELPANEALARMFOREGROUND
                        adcStr   = 'No ADC\nMode Data'
                    elif  self.ADCMode == 0x04:     # Link
                        adcStr   = 'ADC\nLink'
                    elif  self.ADCMode == 0x08:     # Free
                        fillColor = textFillColor = TELPANEALARMFOREGROUND
                        if  SoundAdcAlert:
                            self.nasmythADCalert.alert()
                        adcStr   = 'ADC\nFree'
                    else:
                        fillColor = textFillColor = TELPANEALARMFOREGROUND
                        adcStr   = 'ADC\nUndefined\n(%s,%s)' % \
                                        (self._fmt_( '%x', self.ADCOnOff), \
                                         self._fmt_( '%x', self.ADCMode))
                        TelStatLog.TelStatLog( TeleErrUndefADCMode,
                              ("ERROR (TelescopePane:drawAdc 7):  " +
                               "Undefined ADC: ADCOnOff = %s, ADCMode = %s") % \
                                (self._fmt_( '0x%x', self.ADCOnOff), \
                                 self._fmt_( '0x%x', self.ADCMode)) )
                else:
                    fillColor = textFillColor = TELPANEALARMFOREGROUND
                    adcStr   = 'ADC\nUndefined\n(%s,%s)' % \
                                        (self._fmt_( '%x', self.ADCOnOff), \
                                         self._fmt_( '%x', self.ADCMode))
                    TelStatLog.TelStatLog( TeleErrUndefADCOnOff,
                         ("ERROR (TelescopePane:drawAdc 8):  Undefined ADC: " +
                          "ADCOnOff = %s, ADCMode = %s") % \
                           (self._fmt_( '0x%x', self.ADCOnOff), \
                            self._fmt_( '0x%x', self.ADCMode)) )
            else:
                # Should NEVER get here!
                fillColor = textFillColor = TELPANEALARMFOREGROUND
                adcStr   = 'ADC\nUndefined\n(%s,%s,%s)' % \
                            (`self.ADC`, `self.ADCOnOff`, `self.ADCMode`)
                TelStatLog.TelStatLog( TeleErrUndefADCInOut,
                           ("ERROR (TelescopePane:drawAdc 9):  " +
                            "Undefined TELSTAT.ADC = %s") % `self.ADC` )
            self.drawRect( AdcNsOptNorm, anchor=NW, 
                           fillColor=fillColor, textFillColor=textFillColor, 
                           font=fontBold, label=adcStr )

        # else don't display anything!  (for P_IR, Ns_IR, Cs_IR)


    def drawFocusId( self ):
        """Draw focus select box."""
        fillColor = TELPANEBACKGROUND
        if  self.FOCUS == FOCUS_PF_OPT:
            self.FocusStr = 'Prime Optical'
        elif  self.FOCUS == FOCUS_PF_IR:
            self.FocusStr = 'Prime IR'
        elif  self.FOCUS == FOCUS_PF_OPT2:
            self.FocusStr = 'Prime Optical 2'
        elif  self.FOCUS == FOCUS_CS_OPT:
            self.FocusStr = 'Cassegrain Optical'
        elif  self.FOCUS == FOCUS_CS_IR:
            self.FocusStr = 'Cassegrain IR'
        elif  self.FOCUS == FOCUS_NS_OPT:
            self.FocusStr = 'Nasmyth Optical'
        elif  self.FOCUS == FOCUS_NS_IR:
            self.FocusStr = 'Nasmyth IR'
        elif  self.FOCUS == UNDEF:
            self.FocusStr = 'Focus Undefined'
            fillColor=TELPANEALARMFOREGROUND
        elif  self.FOCUS == FOCUS_CHANGING:
            self.FocusStr = 'Focus Changing'
            fillColor=TELPANEALARMFOREGROUND
        else:  # self.FOCUS == None:
            self.FocusStr = 'No Focus ID Data'
            fillColor=TELPANEALARMFOREGROUND
        self.drawRect( FocusIdNorm, fillColor=fillColor,
                       font=fontBigBold, label=self.FocusStr )
        
    def drawM1cover( self ):
        """Draw M1 cover box."""
        textFillColor = TRANSPARENT
        M1state = M1Other
        anchor = S      # for text
        if  self.M1Cover == None:
            textFillColor = TELPANEALARMFOREGROUND
            M1Str = 'No M1Cover Data'
        elif  self.M1CoverOnway == None:
            textFillColor = TELPANEALARMFOREGROUND
            M1Str = 'No M1CoverOnway Data'
        else:
            if  self.M1CoverOnway == 0x01:
                M1Str = 'M1 Cover OnWay-Open'
            elif  self.M1CoverOnway == 0x02:
                M1Str = 'M1 Cover OnWay-Closed'
            elif  self.M1Cover & 0x5555555555555555555555 == 0x1111111111111111111111:
                M1state = M1Open
            elif  self.M1Cover & 0x5555555555555555555555 == 0x4444444444444444444444:
                M1state = M1Closed
            else:
                M1Str = 'M1 Cover Partial\n(%x)' % self.M1Cover
                anchor = CENTER
                TelStatLog.TelStatLog( TeleWarnPartialM1Cover,
                           ("WARNING (TelescopePane:drawM1Cover):  " +
                            "Partial M1Cover = %x, M1CoverOnway = %x") % \
                           (self.M1Cover,self.M1CoverOnway) )

        if  M1state == M1Open:
            fillColor = TELPANEBACKGROUND
            self.drawText( 'M1 Cover Open', M1CoverTextNorm,
                font=fontTinyBold, anchor=S, tags=('F',) )
            self.drawRect( M1CoverOpenRightNorm, 
                                TELPANEFOREGROUND, fillColor )
            self.drawRect( M1CoverOpenLeftNorm, 
                                TELPANEFOREGROUND, fillColor )
        elif  M1state == M1Closed:
            fillColor = TELPANECLOSED
            self.drawRect( M1CoverNorm, TELPANEFOREGROUND, fillColor,
                TELPANEFOREGROUND, font=fontTinyBold, label='M1 Cover Closed' )
        else:                           # partially open
            fillColor = TELPANECLOSED
            self.drawRect( M1CoverPartLeftNorm, 
                                TELPANEFOREGROUND, fillColor )
            self.drawRect( M1CoverPartRightNorm, 
                                TELPANEFOREGROUND, fillColor )
            self.drawText( M1Str, M1CoverTextNorm, textFillColor=textFillColor, 
                           font=fontTinyBold, anchor=anchor, tags=('F',) )

    def drawM1( self ):
        """Draw M1 mirror."""
        self.drawArc( M1CoordNorm, M1Extents[0], M1Extents[1], tags=('B',) )
        self.drawArc( M1CoordNorm, M1Extents[2], M1Extents[3], tags=('B',) )
        self.drawText( 'M1', M1LabelCoordNorm, anchor=CENTER, 
                        font=fontBold, tags=('B',) )


    def drawCellCover( self ):
        """Draw Cell cover box."""
        fillColor = TELPANEBACKGROUND
        textFillColor = TRANSPARENT
        if  self.CellCover == None:
            fillColor = TELPANECLOSED
            textFillColor = TELPANEALARMFOREGROUND
            CellStr = 'No Cell Cover Data'
        else:
            if  self.CellCover == 0x01:
                self.drawText( 'Cell Cover Open', CellCoverTextNorm,
                    textFillColor=textFillColor,
                    font=fontTinyBold, anchor=S, tags=('F',) )
                self.drawRect( CellCoverOpenLeftNorm, 
                                outlineColor=TELPANEFOREGROUND, 
                                fillColor=fillColor, 
                                textFillColor=textFillColor )
                self.drawRect( CellCoverOpenRightNorm, 
                                outlineColor=TELPANEFOREGROUND, 
                                fillColor=fillColor, 
                                textFillColor=textFillColor )
                return
            elif  self.CellCover == 0x04:
                fillColor = TELPANECLOSED
                self.drawRect( CellCoverNorm, 
                                outlineColor=TELPANEFOREGROUND, 
                                fillColor=fillColor, 
                                textFillColor=textFillColor,
                                font=fontTinyBold, 
                                label='Cell Cover Closed')
                return
            elif  self.CellCover == 0x00:
                fillColor = TELPANECLOSED
                CellStr = 'Cell Cover OnWay'
            else:
                fillColor = TELPANECLOSED
                textFillColor = TELPANEALARMFOREGROUND
                CellStr = 'Cell Cover State Undefined (%x)' % self.CellCover
                TelStatLog.TelStatLog( TeleErrUndefCellCover,
                           ("ERROR (TelescopePane:drawCellCover):  " +
                            "Undefined CellCover = %x") % self.CellCover )

        # Fell through -- either OnWay or undefined or No Data
        self.drawRect( CellCoverPartLeftNorm, 
                        outlineColor=TELPANEFOREGROUND, 
                        fillColor=fillColor)
        self.drawRect( CellCoverPartRightNorm, 
                        outlineColor=TELPANEFOREGROUND, 
                        fillColor=fillColor)
        if  self.CellCover != None and textFillColor == TELPANEALARMFOREGROUND:
            posN = ( CellCoverTextNorm[0], CellCoverTextNorm[1]+0.4 )
        else:
            posN = CellCoverTextNorm
        self.drawText( CellStr, posN, textFillColor=textFillColor, 
                       font=fontTinyBold, anchor=S, tags=('F',) )


    def drawRotator( self ):
        """Draw rotator box at appropriate focus location."""
        #? print "ROT_POS = %s, ROT_CMD = %s deg, ROT_MODE = %s\n" % \
        #?    ( `self.ROT_POS`, `self.ROT_CMD`, `self.InsRotMode` )

        # Find location, thresholds and mode based on focus, and
        #    label text based on mode and focus
        condition = ConditionGreen
        displayRedBlueAchvd = False  # don't display red/blue or achieved status
        if  self.FOCUS == FOCUS_PF_OPT or self.FOCUS == FOCUS_PF_IR or self.FOCUS == FOCUS_PF_OPT2:
            location = LocationPrime
            warnThresh  = ROT_PF_HIGHWARNING
            alarmThresh = ROT_PF_HIGHALARM
            if  self.ROTATOR == None or self.INSROTMODE_PF == None:
                label = 'No Rot Data'
                condition = ConditionRed
            elif  self.ROTATOR == UNDEF:
                label = 'Rotator Undefined'
                condition = ConditionRed
            elif  self.ROT_POS == None or self.ROT_CMD == None:
                label = 'No Rot Pos Data'
                condition = ConditionRed
            elif  self.ROTATOR == ROT_OUT:
                # Should NEVER get here!  No OUT condition at PF
                label = 'InsRot Out'            # OK, so far -- ConditionGreen
                displayRedBlueAchvd = True
            # if we get this far, ROTATOR==ROT_INSR
            elif  self.INSROTROTATION_PF == 0x02 or self.INSROTMODE_PF == 0x20:
                label = 'InsRot Free'
                condition = ConditionYellow
                displayRedBlueAchvd = True
            elif  self.INSROTROTATION_PF == 0x01 and self.INSROTMODE_PF == 0x10:
                label = 'InsRot Link'           # OK, so far -- ConditionGreen
                displayRedBlueAchvd = True
            else:
                label     = 'InsRot Undefined (%s,%s)' % \
                                (self._fmt_( '%x', self.INSROTROTATION_PF), \
                                 self._fmt_( '%x', self.INSROTMODE_PF))
                condition = ConditionRed
                TelStatLog.TelStatLog( TeleErrUndefInsRot_PF,
                         ("ERROR (TelescopePane:drawRotator) 1:  " +
                          "Undefined PF InsRot: INSROTROTATION_PF = %s, " +
                          "INSROTMODE_PF = %s") % \
                           (self._fmt_( '0x%x', self.INSROTROTATION_PF), \
                            self._fmt_( '0x%x', self.INSROTMODE_PF)) )

        elif  self.FOCUS == FOCUS_CS_OPT or self.FOCUS == FOCUS_CS_IR:
            location = LocationCs
            warnThresh  = ROT_CS_HIGHWARNING
            alarmThresh = ROT_CS_HIGHALARM
            if  self.ROTATOR == None or self.InsRotMode == None:
                label = 'No Rot Data'
                condition = ConditionRed
            elif  self.ROTATOR == UNDEF:
                label = 'Rotator Undefined'
                condition = ConditionRed
            elif  self.ROT_POS == None or self.ROT_CMD == None:
                label = 'No Rot Pos Data'
                condition = ConditionRed
            elif  self.ROTATOR == ROT_OUT:
                # Should NEVER get here!  No OUT condition at Cs
                label = 'InsRot Out'            # OK, so far -- ConditionGreen
                displayRedBlueAchvd = True
            # if we get this far, ROTATOR==ROT_INSR
            elif  self.InsRotRotation == 0x02 or self.InsRotMode == 0x02:
                label = 'InsRot Free'
                condition = ConditionYellow
                displayRedBlueAchvd = True
            elif  self.InsRotRotation == 0x01 and self.InsRotMode == 0x01:
                label = 'InsRot Link'           # OK, so far -- ConditionGreen
                displayRedBlueAchvd = True
            else:
                label     = 'InsRot Undefined (%s,%s)' % \
                                (self._fmt_( '%x', self.InsRotRotation), \
                                 self._fmt_( '%x', self.InsRotMode))
                condition = ConditionRed
                TelStatLog.TelStatLog( TeleErrUndefInsRot_Cs,
                         ("ERROR (TelescopePane:drawRotator) 2:  " +
                          "Undefined Cs InsRot: InsRotRotation = %s, " +
                          "InsRotMode = %s") % \
                           (self._fmt_( '0x%x', self.InsRotRotation), \
                            self._fmt_( '0x%x', self.InsRotMode)) )

        elif  self.FOCUS == FOCUS_NS_OPT or self.FOCUS == FOCUS_NS_IR:
            location = LocationNsOpt
            warnThresh  = ROT_NS_HIGHWARNING
            alarmThresh = ROT_NS_HIGHALARM
            if  self.ROTATOR == None or self.ImgRotMode == None:
                label = 'No Rot or\n AO Data'   # means FOCUSINFO unavailable
                condition = ConditionRed
            elif  self.ROTATOR == UNDEF:
                label = 'Rotator\nUndefined'
                condition = ConditionRed
            elif  self.ROT_POS == None or self.ROT_CMD == None:
                label = 'No Rot\nPos Data'
                condition = ConditionRed
            elif  self.ROTATOR == ROT_OUT:
                label = 'ImgRot\n  Out'      # OK, so far -- ConditionGreen
                displayRedBlueAchvd = True
                # Append AO status -- only applicable if ROT_OUT
                if  self.AO == AO_IN:
                    label += '\nAO In'
                elif  self.AO == AO_OUT:
                    label += '\nAO Out'
                # else do nothing for AO, because FOCUSINFO must be bad
            # if we get this far, ROTATOR is ROT_IMR, ROT_IMRB or ROT_IMRR
            elif  self.ImgRotRotation == 0x02 or self.ImgRotMode == 0x02:
                label = 'ImgRot\nFree'
                condition = ConditionYellow
                displayRedBlueAchvd = True
            elif  self.ImgRotRotation == 0x01 and self.ImgRotMode == 0x01:
                label = 'ImgRot\nLink'       # OK, so far -- ConditionGreen
                displayRedBlueAchvd = True
            elif  self.ImgRotRotation == 0x01 and self.ImgRotMode == 0x40:
                label = 'ImgRot\nZenith'     # OK, so far -- ConditionGreen
                displayRedBlueAchvd = True
            else:
                label     = 'ImgRot\nUndefined\n(%s,%s)' % \
                                (self._fmt_( '%x', self.ImgRotRotation), \
                                 self._fmt_( '%x', self.ImgRotMode))
                condition = ConditionRed
                TelStatLog.TelStatLog( TeleErrUndefInsRot_Ns,
                           ("ERROR (TelescopePane:drawRotator) 3:  " +
                            "Undefined Ns ImgRot: ImgRotRotation = %s, " +
                            "ImgRotMode = %s") % \
                           (self._fmt_( '0x%x', self.ImgRotRotation), \
                            self._fmt_( '0x%x', self.ImgRotMode)) )
            # Append type label (Red, OnWay-Red, Blue, OnWay-Blue)
            if  displayRedBlueAchvd and \
                condition != ConditionRed and \
                self.FOCUS == FOCUS_NS_OPT:
                if  self.ImgRotType == None:
                    label += '\n(No ImgRot\nType Data)'
                elif  self.ImgRotType == 0x12:    # Blue
                    if  self.ROTATOR == ROT_IMRB:
                        label += '\n(Blue)'
                    else:
                        label += '\n(Blue?)'
                        condition = ConditionYellow
                        TelStatLog.TelStatLog( TeleErrInconsistentImgRotType,
                            ("ERROR (TelescopePane:drawRotator) 4:  " +
                             "Inconsistent FOCUSINFO (%s) and " +
                             "ImgRotType (%s)") % \
                             (self._fmt_( '0x%x', self.FOCUSINFO), \
                              self._fmt_( '0x%x', self.ImgRotType) )  )
                elif  self.ImgRotType == 0x10:  # OnWayBlue
                    label += '\n(OnWay-Blue)'   # doesn't have to be consistent
                elif  self.ImgRotType == 0x0C:  # Red
                    if  self.ROTATOR == ROT_IMRR:
                        label += '\n(Red)'
                    else:
                        label += '\n(Red?)'
                        condition = ConditionYellow
                        TelStatLog.TelStatLog( TeleErrInconsistentImgRotType,
                            ("ERROR (TelescopePane:drawRotator) 5:  " +
                             "Inconsistent FOCUSINFO (%s) and " +
                             "ImgRotType (%s)") % \
                             (self._fmt_( '0x%x', self.FOCUSINFO), \
                              self._fmt_( '0x%x', self.ImgRotType) )  )
                elif  self.ImgRotType == 0x04:  # OnWayRed
                    label += '\n(OnWay-Red)'    # doesn't have to be consistent
                elif  self.ImgRotType == 0x14:  # none
                    label += '\n(none type)'
                else:
                    label += ',\nImgRot\n Type\nUndefined (%s)' % \
                             self._fmt_( '%x', self.ImgRotType )
                    condition = ConditionYellow
                    TelStatLog.TelStatLog( TeleErrUndefImgRotType,
                            ("ERROR (TelescopePane:drawRotator) 6:  " +
                             "Undefined ImgRotType = %s") % \
                             self._fmt_( '0x%x', self.ImgRotType) )

        else:
            return      # focus unknown, don't draw a rotator!

        # Find condition based on thresholds
        if  displayRedBlueAchvd and \
            condition != ConditionRed and self.ROTATOR >= ROT_IMR:
                            # else POS or CMD may be None
            absPos = fabs(self.ROT_POS)
            # test current position against thresholds
            if  absPos > alarmThresh:
                condition = ConditionRed
            elif  absPos > warnThresh:
                condition = ConditionYellow
            # else <= warnThresh, still ConditionGreen
            # test cmd - pos against 0.1 degrees
            absDif = fabs( self.ROT_CMD - self.ROT_POS )
            if  absDif >= 0.1:
                condition = ConditionRed
                if  self.FOCUS == FOCUS_NS_OPT or self.FOCUS == FOCUS_NS_IR:
                    label += '\ncmd not achvd'
                else:
                    label += ' cmd not achvd'

        # Set fillColor
        fillColor = TELPANEBACKGROUND
        textFillColor = TRANSPARENT
        if  condition == ConditionYellow:
            fillColor     = TELPANEWARNFOREGROUND       # yellow
            textFillColor = TELPANEWARNFOREGROUND
        elif  condition == ConditionRed:
            fillColor     = TELPANEALARMFOREGROUND      # red
            textFillColor = TELPANEALARMFOREGROUND
        # else   condition == ConditionGreen

        # Draw the rotator
        if  self.FOCUS == FOCUS_PF_OPT or self.FOCUS == FOCUS_PF_IR or self.FOCUS == FOCUS_PF_OPT2:
            self.drawRect( RotPfNorm, 
                           fillColor=fillColor, textFillColor=TRANSPARENT,
                           font=fontSmallBold, label=label )
        elif  self.FOCUS == FOCUS_CS_OPT or self.FOCUS == FOCUS_CS_IR:
            self.drawRect( RotCsNorm, 
                           fillColor=fillColor, textFillColor=TRANSPARENT,
                           font=fontSmallBold, label=label )
        elif  self.FOCUS == FOCUS_NS_OPT:
            self.drawRect( RotNsOptNorm, 
                           fillColor=fillColor, textFillColor=fillColor,
                           anchor=NE, font=fontSmallBold, label=label )
        else:  # self.FOCUS == FOCUS_NS_IR
            self.drawRect( RotNsIRNorm, 
                           fillColor=fillColor, textFillColor=fillColor,
                           anchor=NW, font=fontSmallBold, label=label )


    def drawWaveplate( self ):
        """Draw Waveplate stages."""
        # only drawn if focus is NSIR
        if  self.FOCUS != FOCUS_NS_IR:
            return

        # It's slightly wasteful to repeatedly create these data structures in this method
        # but they contain instance vars and make the implementation more readable
        # (status value, rect, label)
        STATUSVAL, RECT, LABEL = range(3)
        WPDisplayData = (
            (self.Waveplate1, WPPolarizerNorm,    'Polarizer %s'),
            (self.Waveplate2, WPHalfStageNorm,    '1/2 WP %s'),
            (self.Waveplate3, WPQuarterStageNorm, '1/4 WP %s')
                      )

        for WPData in WPDisplayData:
            statusValue = WPData[STATUSVAL]
            try:
                floatStatusVal = float(statusValue)
            except:
                floatStatusVal = -1.0
            if floatStatusVal == 0.0:
                fillColor = TELPANEBACKGROUND
                stageStatus = 'Out'
            elif floatStatusVal == 55.0:
                fillColor = TELPANECLOSED
                stageStatus = 'In'
            else:
                fillColor = TELPANEWARNFOREGROUND
                stageStatus = '???'
        
            self.drawRect( WPData[RECT],
                           fillColor=fillColor, textFillColor=fillColor,
                           font=fontNormal, label=WPData[LABEL] % (stageStatus) )


    def drawAoPolarizer( self ):
        """Draw AO/Polarizer box."""
        fillColor = TELPANEBACKGROUND
        self.drawRect( AoPolarizerNorm, TELPANEFOREGROUND, fillColor, 
                        font=fontNormal, label='AO/Polarizer' )


    #####################################################################
    ### methods for redrawing background and foreground
    #####################################################################

    def redrawBg( self ):
        """Redraw background, i.e. constant objects. Calls primitives."""
        self.delete( ('B',) )
        self.drawLine( DSBaseNorm, TELPANEFOREGROUND, tags=('B',) )
        self.drawRect( TSRearCoverNorm, TELPANEFOREGROUND, TELPANESOLID,
                        tags=('B',) )
        self.drawLine( TSBaseNorm, TELPANEFOREGROUND, tags=('B',) )
        self.drawRect( WSOutlineNorm, TELPANEFOREGROUND, TELPANEBACKGROUND,
                        tags=('B',) )
        self.drawRect( WSBottomCoverNorm, TELPANEFOREGROUND, TELPANESOLID,
                        tags=('B',) )

        self.drawM1()
        #? debugBox = ( (5,5), (95, 95) )
        #? self.drawRect( debugBox, TELPANEFOREGROUND, TRANSPARENT,tags=('B',) )
        self.drawLine( M1CoverBaseNorm, TELPANEFOREGROUND, tags=('B',) )
        self.drawLine( CellCoverBaseNorm, TELPANEFOREGROUND, tags=('B',) )

    def redrawFg( self ):
        """Redraw foreground objects, i.e. pointers."""
        self.delete( ('F',) )
        if  TelStat_cfg.TelPaneRayDisplay:
            self.create_oval( self.xScale*(TelRayOriginXNorm-0.5), 
                              self.yScale*(TelRayOriginYNorm-0.5), 
                              self.xScale*(TelRayOriginXNorm+0.5), 
                              self.yScale*(TelRayOriginYNorm+0.5), 
                              fill=TELPANERAY, outline=TELPANERAY, tags=('F',))
            self.drawTelescopeRay()
        self.drawDomeShutter()
        self.drawTopScreen()
        self.drawWindScreen()
        self.drawFocus()
        self.drawRotator()
        self.drawM2()
        self.drawAdc()
        self.drawFocusId()
        self.drawM1cover()
        self.drawCellCover()
        self.drawWaveplate()
#?      self.drawAoPolarizer()

    def rePack(self):
        """First resize, then repack this pane."""
        self.resize()
        self.pack( anchor=NW)

    #####################################################################
    ### miscellaneous methods
    #####################################################################

    def geomCB(self, event):
        """Callback for to print geometry."""
        TelStatLog.TelStatLog( TeleInfoBase,
                    "Telescope Pane:    %s" % self.winfo_geometry(), True )

    def _fmt_(self, fmt, var):
        """Format any variable into a string using format fmt."""
        if  var==None:
            return 'None'
        try:
            return fmt % var
        except:
            return '<' + `var` + '>'

######################################################################
################   test application   ################################
######################################################################

#?  Following for debugging only ############
import time
curtime         = time.time()
prevtime        = time.time()
statRefresh     = True
def refresh():
    global curtime, prevtime, statRefresh
    curtime = time.time()
    deltatime = curtime - prevtime
    print "TelescopePane.refresh() called, time = %.6f, delta = %.6f" % \
                                                        (curtime, deltatime)
    StatIO_service()
    prevtime = curtime
    if  statRefresh:
        root.after( 200, refresh )      # avoids possible frame overflow

if __name__ == '__main__':

    from StatIO import *
    #StatIOsource = StatIO_ScreenPrintSim
    #TelStat_cfg.OSSC_screenPrintPath = OSSC_SCREENPRINTSIMPATH

    # Create the base frame for the widgets
    root = Tkinter.Tk()
    Pmw.initialise(root)
    root.title("Telescope Pane Test")
    root.geometry("-0+0")
    

    # Create an instance
    testTelPane = TelescopePane( root, 'testTelPane' )
    #testTelPane.grid( row=0, column=0 )
    #testTelPane.grid( row=0, column=0, sticky=W+E+N+S )

    # Define event handler for resizing
    def mouseEnter(event):
        widWidth = root.winfo_width()
        widHeight = root.winfo_height()
        testTelPane.resize( widWidth, widHeight )

    # Define event handler for freezing refresh
    def mouseRight(event):
        global statRefresh
        if  statRefresh:
            statRefresh = False
        else:
            statRefresh = True
            refresh()

    # Define event handler for toggling telescope ray display
    def mouseLeft(event):
        if  TelStat_cfg.TelPaneRayDisplay:
            TelStat_cfg.TelPaneRayDisplay = False
            print 'TelPane:  TelPaneRayDisplay = ', TelStat_cfg.TelPaneRayDisplay
        else:
            TelStat_cfg.TelPaneRayDisplay = True
            print 'TelPane:  TelPaneRayDisplay = ', TelStat_cfg.TelPaneRayDisplay

    # Bind mouseEnter to mouse entry into the window    
    root.bind("<Enter>", mouseEnter)

    # Bind mouseRight to mouse button 1 into the window 
    root.bind("<Button-1>", mouseLeft)

    # Bind mouseLeft to mouse button 3 into the window  
    root.bind("<Button-3>", mouseRight)

    # Print root geometry
    root.update_idletasks()  # must be done to assure that geometry != 1x1+0+0
    print "root :       ", root.geometry(), "\n"

    refresh()
    root.mainloop()


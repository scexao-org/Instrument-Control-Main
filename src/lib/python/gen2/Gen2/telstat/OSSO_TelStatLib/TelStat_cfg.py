# TelStat_cfg.py -- Bruce Bon -- 2008-09-18

# Constants used by multiple modules in the Telescope Status window

import os
import re
import time
import getpass
import Tkinter
from Tkconstants import *
import Pmw

######################################################################
################   TelStat date and version   ########################
######################################################################

TELSTAT_DATE    = '2008-09-18'
TELSTAT_VERSION = '2.1.13'

######################################################################
################   file and URL paths   ##############################
######################################################################


# Find time tag for file name construction
timeTuple  = time.localtime()
timeString = '%d_%02d_%02d_%02d%02d%02d' % \
             ( timeTuple[0], timeTuple[1], timeTuple[2],
               timeTuple[3], timeTuple[4], timeTuple[5] )

# Find path to OSSC_screenPrint
OSSC_SCREENPRINTREALPATH = 'OSSC_screenPrint'   # must be in PATH
OSSC_SCREENPRINTSIMPATH  = './OSSC_screenPrint_sim'
OSSC_screenPrintPath     = OSSC_SCREENPRINTREALPATH

# Log file paths and file descriptors
try:
    TELSTAT_LOG_ROOT_DIR = os.environ['LOGHOME']
except KeyError:
    TELSTAT_LOG_ROOT_DIR = '/gen2/logs'


TELSTAT_LOG_PATH = \
        TELSTAT_LOG_ROOT_DIR + '/TelStat_' + timeString + '.log'
TELSTAT_DATALOG_PATH = \
        TELSTAT_LOG_ROOT_DIR + '/TelStat_ReplayData_' + timeString + '.log'
telStatDataLoggingFirstTime = True   # only use TELSTAT_DATALOG_PATH first time
telStatDataLogging   = False
telStatDataLog_fd    = None
telstatMode = 'SOSS'


# Menu Pane Configuration -- find paths to help files
try:
    TELSTAT_MANPATH = os.environ['TELSTAT_MANPATH']
except KeyError:
    TELSTAT_MANPATH = os.getcwd()
TELSTAT_MANUAL_URL      = 'file://' + TELSTAT_MANPATH + '/TelStatManual.html'
TELSTAT_MANUAL_HLP      = TELSTAT_MANPATH + '/TelStatManual.hlp'
TELSTAT_ALERTS_HLP      = TELSTAT_MANPATH + '/TelStatAlerts.hlp'
TELSTAT_OPTIONS_HLP     = TELSTAT_MANPATH + '/TelStatOptions.hlp'
TELSTAT_DEBUG_HLP       = TELSTAT_MANPATH + '/TelStatDebug.hlp'
TELSTAT_LIGHTPATH_HLP   = TELSTAT_MANPATH + '/TelStatLightPath.hlp'
TELSTAT_RELEASENOTES_HLP = TELSTAT_MANPATH + '/TelStatReleaseNotes.hlp'

# Telescope Pane Bitmaps
try:
    GEN2CONF = os.environ['CONFHOME']
except KeyError:
    GEN2CONF = '/gen2/conf'
TELSTAT_LIGHTPATH_BIT = '@' + GEN2CONF + 'product/file/gray6.xbm'

######################################################################
################   OBCP Names   ######################################
######################################################################

OBCPSYM = { 
    "IRCS"   :"IRC",        # OBCP01
    "AO"     :"AOS",        # OBCP02
    "CIAO"   :"CIA",        # OBCP03
    "OHS"    :"OHS",        # OBCP04
    "FOCAS"  :"FCS",        # OBCP05
    "HDS"    :"HDS",        # OBCP06
    "COMICS" :"COM",        # OBCP07
    "SPCAM"  :"SUP",        # OBCP08
    "SUKA"   :"SUK",        # OBCP09
    "MIRTOS" :"MIR",        # OBCP10
    "VTOS"   :"VTO",        # OBCP11
    "CAC"    :"CAC",        # OBCP12
    "SKYMON" :"SKY",        # OBCP13
    "PI1"    :"PI1",        # OBCP14
    "K3D"    :"K3D",        # OBCP15
    "OTHER16":"O16",        # OBCP16
    "MOIRCS" :"MCS",        # OBCP17
    "FMOS"   :"FMS",        # OBCP18
    "FLDMON" :"FLD",        # OBCP19
    "AO188"  :"AON",        # OBCP20
    "HICIAO" :"HIC",        # OBCP21
    "WAVEPLAT":"WAV",        # OBCP22
    "LGS"    :"LGS",        # OBCP23
    "HSC"    :"HSC",        # OBCP24
    "OTHER25":"O25",        # OBCP25
    "OTHER26":"O26",        # OBCP26
    "OTHER27":"O27",        # OBCP27
    "OTHER28":"O28",        # OBCP28
    "OTHER29":"O29",        # OBCP29
    "OTHER30":"O30",        # OBCP30
    "OTHER31":"O31",        # OBCP31
    "OTHER32":"O32",        # OBCP32
    "VGW"    :"VGW" }       # OBCP33

######################################################################
################   miscellaneous   ###################################
######################################################################

debugFlag       = False

replayFlag      = False
replayFileSpec  = 'No Replay File Specified'
replayInitSkip          = 0     # during replay, skip this many initial records
replaySamplePeriod      = 1     # replay every replaySamplePeriod'th record

paneBorderWidth=2
paneBorderRelief=Tkinter.RAISED

PIXELS_PER_BUTTON_WIDTH_UNIT  = 10
PIXELS_PER_BUTTON_HEIGHT_UNIT = 21

DOUBLE_BORDER_FUDGE_PIXELS = 35

######################################################################
################   fonts   ###########################################
######################################################################

# Fonts
# fontTiny       = Pmw.logicalfont( 'Helvetica',-4 )
# fontTinyBold   = Pmw.logicalfont( 'Helvetica',-4, weight='bold' )
# fontSmall      = Pmw.logicalfont( 'Helvetica',-2 )
# fontSmallBold  = Pmw.logicalfont( 'Helvetica',-2, weight='bold' )
# fontNormal     = Pmw.logicalfont( 'Helvetica',2 )
# fontBold       = Pmw.logicalfont( 'Helvetica',2, weight='bold' )
# fontBig        = Pmw.logicalfont( 'Helvetica',5 )
# fontBigBold    = Pmw.logicalfont( 'Helvetica',5, weight='bold' )
# fontBigger     = Pmw.logicalfont( 'Helvetica',12 )
# fontBiggerBold = Pmw.logicalfont( 'Helvetica',12, weight='bold' )
# fontHuge       = Pmw.logicalfont( 'Helvetica',18 )
# fontHugeBold   = Pmw.logicalfont( 'Helvetica',18, weight='bold' )
# fontMoreHuge     = Pmw.logicalfont( 'Helvetica',28 )
# fontMoreHugeBold = Pmw.logicalfont( 'Helvetica',28, weight='bold' )
# fontMostHuge     = Pmw.logicalfont( 'Helvetica',40 )
# fontMostHugeBold = Pmw.logicalfont( 'Helvetica',40, weight='bold' )


fontTiny       = Pmw.logicalfont( 'Helvetica',-6 )
fontTinyBold   = Pmw.logicalfont( 'Helvetica',-6, weight='bold' )
fontXSmall      = Pmw.logicalfont( 'Helvetica',-4 )
fontXSmallBold  = Pmw.logicalfont( 'Helvetica',-4, weight='bold' )
fontSmall      = Pmw.logicalfont( 'Helvetica',-2 )
fontSmallBold  = Pmw.logicalfont( 'Helvetica',-2, weight='bold' )
fontNormal     = Pmw.logicalfont( 'Helvetica',0 )
fontBold       = Pmw.logicalfont( 'Helvetica',0, weight='bold' )
fontBig        = Pmw.logicalfont( 'Helvetica',2 )
fontBigBold    = Pmw.logicalfont( 'Helvetica',2, weight='bold' )
fontBigger     = Pmw.logicalfont( 'Helvetica',10 )
fontBiggerBold = Pmw.logicalfont( 'Helvetica',10, weight='bold' )
fontHuge       = Pmw.logicalfont( 'Helvetica',16 )
fontHugeBold   = Pmw.logicalfont( 'Helvetica',16, weight='bold' )
fontMoreHuge     = Pmw.logicalfont( 'Helvetica',26 )
fontMoreHugeBold = Pmw.logicalfont( 'Helvetica',26, weight='bold' )
fontMostHuge     = Pmw.logicalfont( 'Helvetica',38 )
fontMostHugeBold = Pmw.logicalfont( 'Helvetica',38, weight='bold' )



######################################################################
################   sounds   ##########################################
######################################################################

audioPlayer             = None          # to be replaced
AudioMinInterval        = 5.0           # seconds

# Find paths to audio players and the Sun audio device, set player parameters
try:
    SOSS_AUDIO_PLAYER = os.environ['OSS_LOAD_MODULE'] + '/OSST_audioplay'
except KeyError:
    SOSS_AUDIO_PLAYER = \
      '/sg1/ocs/SRC_20031216/product/OSST/OSST_audioplay.d/OSST_audioplay'
SOSS_AUDIO_VOLUME   = 255
SOSS_AUDIO_CHANNELS = "SHL"
#SOSS_AUDIO_CHANNELS = "HL"     # for debugging, no speaker

AU_SOX_PATH = '/usr/bin/sox'
AU_DEV_PATH = '/dev/audio'

# Find audio directory for old SOSS sound clips
try:
    SOSS_AUDIO_DIRECTORY = os.environ['OSS_SOUND'] + '/'
except KeyError:
    SOSS_AUDIO_DIRECTORY = '/sg1/ocs/SRC_20031216/product/remote/file/'

# Following are heritage sounds, i.e. recorded for SOSS:
E_AGSTAR        = SOSS_AUDIO_DIRECTORY + 'E_AGSTAR.au'
E_CANCEL        = SOSS_AUDIO_DIRECTORY + 'E_CANCEL.au'
E_ERRALLOC      = SOSS_AUDIO_DIRECTORY + 'E_ERRALLOC.au'
E_ERRDBS        = SOSS_AUDIO_DIRECTORY + 'E_ERRDBS.au'
E_ERRDECODE     = SOSS_AUDIO_DIRECTORY + 'E_ERRDECODE.au'
E_ERROBC        = SOSS_AUDIO_DIRECTORY + 'E_ERROBC.au'
E_ERROBS        = SOSS_AUDIO_DIRECTORY + 'E_ERROBS.au'
E_ERRTSC        = SOSS_AUDIO_DIRECTORY + 'E_ERRTSC.au'
E_ERRVGW        = SOSS_AUDIO_DIRECTORY + 'E_ERRVGW.au'
E_EXPDONE       = SOSS_AUDIO_DIRECTORY + 'E_EXPDONE.au'
E_EXPSTART      = SOSS_AUDIO_DIRECTORY + 'E_EXPSTART.au'
E_FILTCHG       = SOSS_AUDIO_DIRECTORY + 'E_FILTCHG.au'
E_FILTDONE      = SOSS_AUDIO_DIRECTORY + 'E_FILTDONE.au'
E_FOCDETECT     = SOSS_AUDIO_DIRECTORY + 'E_FOCDETECT.au'
E_FOCFAIL       = SOSS_AUDIO_DIRECTORY + 'E_FOCFAIL.au'
E_INPUT         = SOSS_AUDIO_DIRECTORY + 'E_INPUT.au'
E_MANCALC       = SOSS_AUDIO_DIRECTORY + 'E_MANCALC.au'
E_MANREADOUT    = SOSS_AUDIO_DIRECTORY + 'E_MANREADOUT.au'
E_TELMOVE       = SOSS_AUDIO_DIRECTORY + 'E_TELMOVE.au'
E_ERRTSC        = SOSS_AUDIO_DIRECTORY + 'E_ERRTSC.au'
E_WARNAZ        = SOSS_AUDIO_DIRECTORY + 'E_WARNAZ.au'
E_WARNHEL       = SOSS_AUDIO_DIRECTORY + 'E_WARNHEL.au'
E_WARNHUM       = SOSS_AUDIO_DIRECTORY + 'E_WARNHUM.au'
E_WARNLEL       = SOSS_AUDIO_DIRECTORY + 'E_WARNLEL.au'
E_WARNROT       = SOSS_AUDIO_DIRECTORY + 'E_WARNROT.au'
E_WARNWIND      = SOSS_AUDIO_DIRECTORY + 'E_WARNWIND.au'

# Find audio directory for TelStat sound clips
try:
    TELSTAT_AUDIO_DIRECTORY = os.environ['OSS_SOUND'] + '/'
except KeyError:
    TELSTAT_AUDIO_DIRECTORY = './'
# Make sure that sound clips are there!
if not os.path.exists(TELSTAT_AUDIO_DIRECTORY + 'AlarmGuideStarLostH100Vf.au'):
    TELSTAT_AUDIO_DIRECTORY = './'
if not os.path.exists(TELSTAT_AUDIO_DIRECTORY + 'AlarmGuideStarLostH100Vf.au'):
    TELSTAT_AUDIO_DIRECTORY = None

# Default audio mute state
DEFAULT_AUDIO_MUTE_ON = True

# Following are new sounds, recorded for TelStat:
        # Tracking Pane
AU_ALARM_GUIDE_STAR_LOST = TELSTAT_AUDIO_DIRECTORY + 'AlarmGuideStarLostH100Vf.au'
        # Telescope Pane
AU_ALARM_WS_FREE        = TELSTAT_AUDIO_DIRECTORY + 'AlarmWindscreenFreeH75Vf.au'
AU_ALARM_WS_HIGH        = TELSTAT_AUDIO_DIRECTORY + 'AlarmWindscreenHighH50Vf.au'
AU_ALARM_WS_OBSTRUCT    = TELSTAT_AUDIO_DIRECTORY + 'AlarmWindscreenObstructH50Vf.au'
AU_WARN_ADC_PF_FREE     = TELSTAT_AUDIO_DIRECTORY + 'WarnAdcPfFreeH50Vf.au'
AU_WARN_ADC_CS_FREE     = TELSTAT_AUDIO_DIRECTORY + 'WarnAdcCsFreeH50Vf.au'
AU_WARN_ADC_NS_FREE     = TELSTAT_AUDIO_DIRECTORY + 'WarnAdcNsFreeH50Vf.au'
AU_WARN_TIPTILT_OFF     = TELSTAT_AUDIO_DIRECTORY + 'WarnTipTiltOffLauren2.au'
        # Limits Pane
AU_WARN_AZ_LIMIT        = TELSTAT_AUDIO_DIRECTORY + 'WarnAzLimitH50Vf.au'
AU_ALARM_AZ_LIMIT       = TELSTAT_AUDIO_DIRECTORY + 'AlarmAzLimitH50Vf.au'
AU_WARN_ROT_LIMIT       = TELSTAT_AUDIO_DIRECTORY + 'WarnRotLimitH50Vf.au'
AU_ALARM_ROT_LIMIT      = TELSTAT_AUDIO_DIRECTORY + 'AlarmRotLimitH50Vf.au'
AU_WARN_AG_LIMIT        = TELSTAT_AUDIO_DIRECTORY + 'WarnAgLimitH50Vf.au'
AU_ALARM_AG_LIMIT       = TELSTAT_AUDIO_DIRECTORY + 'AlarmAgLimitH50Vf.au'
        # Target Pane
AU_WARN_AZ_LIMIT_TIME   = TELSTAT_AUDIO_DIRECTORY + 'WarnAzLimitTimeH50Vf.au'
AU_ALARM_AZ_LIMIT_TIME  = TELSTAT_AUDIO_DIRECTORY + 'AlarmAzLimitTimeH250Vf.au'
AU_WARN_EL_LIMIT_TIME   = TELSTAT_AUDIO_DIRECTORY + 'WarnElLimitTimeH50Vf.au'
AU_ALARM_EL_LIMIT_TIME  = TELSTAT_AUDIO_DIRECTORY + 'AlarmElLimitTimeH50Vf.au'
AU_WARN_ROT_LIMIT_TIME  = TELSTAT_AUDIO_DIRECTORY + 'WarnRotLimitTimeH50Vf.au'
AU_ALARM_ROT_LIMIT_TIME = TELSTAT_AUDIO_DIRECTORY + 'AlarmRotLimitTimeH50Vf.au'
AU_WARN_PA_CMDFAIL      = TELSTAT_AUDIO_DIRECTORY + 'WarnPAcmdFailH50Vf.au'
        # Environment Pane
AU_WARN_LOW_TEMP        = TELSTAT_AUDIO_DIRECTORY + 'WarnLowTempH50Vf.au'
AU_WARN_HIGH_HUMID      = TELSTAT_AUDIO_DIRECTORY + 'WarnHighHumidH50Vf.au'
AU_ALARM_HIGH_HUMID     = TELSTAT_AUDIO_DIRECTORY + 'AlarmHighHumidH50Vf.au'
AU_WARN_HIGH_WIND       = TELSTAT_AUDIO_DIRECTORY + 'WarnHighWindH50Vf.au'
AU_ALARM_HIGH_WIND      = TELSTAT_AUDIO_DIRECTORY + 'AlarmHighWindH50Vf.au'
AU_ALERT_ENV_OK         = TELSTAT_AUDIO_DIRECTORY + 'AlertEnvOKH250Vf.au'
AU_ALERT_ENV_OK30       = TELSTAT_AUDIO_DIRECTORY + 'AlertEnvOK30H2100Vf.au'


######################################################################
################   global state constants   ##########################
######################################################################

GS_SLEWTHRESHOLD     = 0.25     # degrees
GS_INACTIVEELEVATION = 89.5     # degrees

ROT_PF_LOWALARM         = -249.5
ROT_PF_LOWWARNING       = -240.0
ROT_PF_HIGHWARNING      =  240.0
ROT_PF_HIGHALARM        =  249.5

ROT_PF_IR_LOWALARM      = -179.5
ROT_PF_IR_LOWWARNING    = -175.0
ROT_PF_IR_HIGHWARNING   =  175.0
ROT_PF_IR_HIGHALARM     =  179.5

ROT_PF_OPT2_LOWALARM     = -269.5
ROT_PF_OPT2_LOWWARNING   = -260.5
ROT_PF_OPT2_HIGHWARNING  =  260.5
ROT_PF_OPT2_HIGHALARM    =  269.5

ROT_NS_LOWALARM         = -179.5
ROT_NS_LOWWARNING       = -175.0
ROT_NS_HIGHWARNING      =  175.0
ROT_NS_HIGHALARM        =  179.5

ROT_CS_LOWALARM         = -269.5
ROT_CS_LOWWARNING       = -260.0
ROT_CS_HIGHWARNING      =  260.0
ROT_CS_HIGHALARM        =  269.5

UNDEF = -1

FOCUS_CHANGING = 11
FOCUS_PF_OPT   = 12
FOCUS_PF_IR    = 13
FOCUS_PF_OPT2  = 14
FOCUS_NS_OPT   = 15
FOCUS_NS_IR    = 16
FOCUS_CS_OPT   = 17
FOCUS_CS_IR    = 18

M2_PF_OPT = 21
M2_PF_IR  = 22
M2_PF_OPT2= 23
M2_CS_OPT = 24
M2_NS_OPT = 25
M2_IR     = 26

ROT_OUT   = 31
ROT_INSR  = 32
ROT_IMR   = 33
ROT_IMRB  = 34
ROT_IMRR  = 35

ADC_OUT   = 41
ADC_IN    = 42

AO_OUT    = 51
AO_IN     = 52

TELDRIVE_POINT        = 51
TELDRIVE_TRACK        = 52
TELDRIVE_TRACK_NS     = 53
TELDRIVE_SLEW         = 54
TELDRIVE_GUIDE_AG     = 55
TELDRIVE_GUIDE_AGPIR  = 56
TELDRIVE_GUIDE_AGFMOS = 57
TELDRIVE_GUIDE_HSCSCAG= 58
TELDRIVE_GUIDE_HSCSHAG= 59
TELDRIVE_GUIDE_AG1    = 60
TELDRIVE_GUIDE_AG2    = 61
TELDRIVE_GUIDE_SV     = 62
TELDRIVE_GUIDE_SV1    = 63
TELDRIVE_GUIDE_SV2    = 64

######################################################################
################   colors   ##########################################
######################################################################

PANECOLORBLUEBACKGROUND         = '#cae1ff'     # pale blue
PANECOLORGREENBACKGROUND        = '#c1ffc1'     # pale green
PANECOLORYELLOWBACKGROUND       = '#fafad2'     # cream
PANECOLORWHITEBACKGROUND        = 'whitesmoke'
PANECOLORMEDGREENBACKGROUND     = 'green'

PANECOLORYELLOWWARNBACKGROUND   = '#ffff00'
PANECOLORREDALARMBACKGROUND     = '#ff0000'

PANECOLORFOREGROUND             = '#000000'     # black
PANECOLORYELLOWFOREGROUND       = '#ffff00'     # bright yellow
PANECOLORGREENFOREGROUND        = '#007000'
PANECOLORBRIGHTGREENFOREGROUND  = '#00ff00'
PANECOLORYELLOWWARNFOREGROUND   = '#ffff00'
PANECOLORREDALARMFOREGROUND     = '#ff0000'
PANECOLORPURPLEFOREGROUND       = '#7f007f'
PANECOLORBROWNFOREGROUND        = '#600000'
PANECOLORORANGEFOREGROUND       = '#ff7700'

PANECOLORYELLOWALERTFOREGROUND  = '#ffff00'
PANECOLORREDALERTFOREGROUND     = '#ff0000'

TRANSPARENT             = ''


######################################################################
################   pane configuration data   #########################
######################################################################

# Help Popup Configuration
HELPPOPUPBACKGROUND     = PANECOLORWHITEBACKGROUND
HELPPOPUPFOREGROUND     = PANECOLORFOREGROUND


# Pointing Pane Configuration
POINTPANEBACKGROUND     = PANECOLORBLUEBACKGROUND
POINTPANEFOREGROUND     = PANECOLORFOREGROUND
#POINTPANETITLESFONT     = fontNormal
#POINTPANECURFONT        = fontMoreHugeBold
#POINTPANECMDFONT        = fontBig

POINTPANETITLESFONT     = fontXSmall
POINTPANECURFONT        = fontHugeBold
POINTPANECMDFONT        = fontBig



# Telescope Pane Configuration
TelPaneRayDisplay       = True
TELPANEBACKGROUND       = PANECOLORYELLOWBACKGROUND
TELPANEFOREGROUND       = PANECOLORFOREGROUND
TELPANEOUTLINE          = PANECOLORGREENFOREGROUND
TELPANENORMFOREGROUND   = PANECOLORFOREGROUND
TELPANEWARNFOREGROUND   = PANECOLORYELLOWWARNFOREGROUND
TELPANEALARMFOREGROUND  = PANECOLORREDALARMFOREGROUND
TELPANECLOSED           = PANECOLORBRIGHTGREENFOREGROUND
TELPANESOLID            = PANECOLORBROWNFOREGROUND
TELPANELABEL            = PANECOLORGREENFOREGROUND
TELPANERAYOUTLINE       = PANECOLORBRIGHTGREENFOREGROUND
TELPANERAY              = PANECOLORBRIGHTGREENFOREGROUND


# Limits Pane Configuration
LIMPANEBACKGROUND       = PANECOLORYELLOWBACKGROUND
LIMPANELABEL            = PANECOLORFOREGROUND
LIMPANESCALE            = PANECOLORGREENFOREGROUND
LIMPANEALARM            = PANECOLORORANGEFOREGROUND
LIMPANEPOINTER          = PANECOLORGREENFOREGROUND
LIMPANEPOINTERALARM     = PANECOLORREDALARMFOREGROUND
LIMPANEPOINTERWARN      = PANECOLORREDALARMFOREGROUND


# Target Pane Configuration

# TARGETPANEFOREGROUND specifies colors in the pane
TARGETPANEFOREGROUND = \
        ( PANECOLORFOREGROUND, PANECOLORFOREGROUND, PANECOLORFOREGROUND )

# TARGETPANEBACKGROUND specifies the background colors for the pane and
TARGETPANEBACKGROUND = \
        ( PANECOLORBLUEBACKGROUND,     PANECOLORYELLOWWARNBACKGROUND, 
          PANECOLORREDALARMBACKGROUND, PANECOLORBRIGHTGREENFOREGROUND )

# Seconds per degree for suppression of "Position angle not achieved" messages
TARGETPANESECPERDEG_PF = 0.6667
TARGETPANESECPERDEG_CS = 0.6667
TARGETPANESECPERDEG_NS = 0.6667

# TARGETPANEPROPID holds the proposal id for the session
#? from commands import getoutput
#? try:
#?     TARGETPANEPROPFILE = os.environ['OSSO_TMP'] + '/Login.info'
#?     TARGETPANEPROPID = getoutput('head -2 ' + TARGETPANEPROPFILE + ' | tail -1')
#?     if len(TARGETPANEPROPID) > 9:
#?         TARGETPANEPROPID = getoutput('/usr/xpg4/bin/id -gn')
#? except KeyError:
#?     TARGETPANEPROPID = getoutput('/usr/xpg4/bin/id -gn')

# Time Pane Configuration
# The order for individual widget configurations is:
# ( UTC clock, HST clock, LST clock, HA clock )

# TIMEPANEFOREGROUND specifies colors for the 4 time clocks in the pane.
#TIMEPANEFOREGROUND = ('green', 'lightblue', 'yellow', 'lightgray')
TIMEPANEFOREGROUND = \
        (PANECOLORFOREGROUND, PANECOLORFOREGROUND, \
         PANECOLORFOREGROUND, PANECOLORFOREGROUND)

# TIMEPANEBACKGROUND specifies the background color for the pane and
# all of the clock widgets.
TIMEPANEBACKGROUND = PANECOLORBLUEBACKGROUND

# TIMEPANEFONT specifies the text font for the clocks.
#TIMEPANEFONT   = ( 'Helvetica 24 bold', 'Helvetica 24 bold', \
#                  'Helvetica 24 bold','Helvetica 24 bold')
#TIMEPANEFONT   = ( fontHugeBold, fontHugeBold, \
#                   fontHugeBold,fontHugeBold)

TIMEPANEFONT   = ( fontBiggerBold, fontBiggerBold, \
                   fontBiggerBold, fontBiggerBold)


# TIMEPANEFORMAT specifies what information each clock displays.
# See the time.strftime() description for a list of valid format codes.
TIMEPANEFORMAT = ( 'UT: %H:%M:%S (%b/%d)', '%Z: %H:%M:%S (%b/%d)', 
                   'LST: %H:%M:%S', None)


# Environment Pane Configuration

# Temperature limit 
TEMPERATURELOWER  = -10.0

# Humidity limit 
HUMIDITYUPPER     =  80.0
HUMIDITYLOWER     =  70.0

# Windspeed limit
WINDSPEEDUPPER    =  20.0
WINDSPEEDLOWER    =  15.0

# ENVPANEBACKGROUND specifies the background color for the pane only
ENVPANEBACKGROUND = PANECOLORGREENBACKGROUND

# Graph configuration order is:
# ( title, foreground color, background color, yscale (min, max), 
#   hidexscale, hideyscale, hidelegend )

# ENVPANETEMPGRAPH specifies the configuration for the Temperature chart
ENVPANETEMPGRAPH = \
        ('Temperature', PANECOLORFOREGROUND, PANECOLORGREENBACKGROUND, None, 0, 0, 1)

# ENVPANEHUMGRAPH specifies the configuration for the Temperature chart
ENVPANEHUMGRAPH = \
        ('Humidity', PANECOLORFOREGROUND, PANECOLORGREENBACKGROUND, None, 0, 0, 1)

# ENVPANEWSGRAPH specifies the configuration for the Temperature chart
ENVPANEWSGRAPH = \
        ('Wind Speed', PANECOLORFOREGROUND, PANECOLORGREENBACKGROUND, None, 0, 0, 1)

# Line configuration order is:
# ( name, color, dashes, line width, symbol )
# The number of tuples gives the number of lines expected

#ENVPANETEMPLINES specifies the configuration for the Temperature chart lines
#ENVPANETEMPLINES = \
#        [('Outside', PANECOLORPURPLEFOREGROUND, 0, 2, '', 'Outside: %+4.1f C', "Helvetica 12 bold"),
#         ('Dome', PANECOLORGREENFOREGROUND, 0, 2, '', 'Dome: %+4.1f C', "Helvetica 12 bold")]

ENVPANETEMPLINES = \
        [('Outside', PANECOLORPURPLEFOREGROUND, 0, 2, '', 'Outside: %+4.1f C', fontXSmallBold),
         ('Dome', PANECOLORGREENFOREGROUND, 0, 2, '', 'Dome: %+4.1f C', fontXSmallBold)]


#ENVPANEHUMLINES specifies the configuration for the Temperature chart lines
#ENVPANEHUMLINES = \
#        [('Outside', PANECOLORPURPLEFOREGROUND, 0, 1, '', 'Outside: %4.1f %%', "Helvetica 12 bold"),
#         ('Dome', PANECOLORGREENFOREGROUND, 0, 1, '', 'Dome: %4.1f %%', "Helvetica 12 bold")]

ENVPANEHUMLINES = \
        [('Outside', PANECOLORPURPLEFOREGROUND, 0, 1, '', 'Outside: %4.1f %%', fontXSmallBold),
         ('Dome', PANECOLORGREENFOREGROUND, 0, 1, '', 'Dome: %4.1f %%', fontXSmallBold)]


#ENVPANEWSLINES specifies the configuration for the Temperature chart lines
#ENVPANEWSLINES = \
#        [('Outside', PANECOLORPURPLEFOREGROUND, 0, 2, '', 'Outside: %4.1f m/s', "Helvetica 12 bold"),
#         ('Dome', PANECOLORGREENFOREGROUND, 0, 2, '', 'Dome: %4.1f m/s', "Helvetica 12 bold")]

ENVPANEWSLINES = \
        [('Outside', PANECOLORPURPLEFOREGROUND, 0, 2, '', 'Outside: %4.1f m/s', fontXSmallBold ),
         ('Dome', PANECOLORGREENFOREGROUND, 0, 2, '', 'Dome: %4.1f m/s', fontXSmallBold)]


# Tracking Pane Configuration

# TRACKPANEBACKGROUND specifies the background color for the pane only
TRACKPANEBACKGROUND = PANECOLORGREENBACKGROUND

# TRACKPANEFOREGROUND specifies the foreground color for the pane only
TRACKPANEFOREGROUND = PANECOLORFOREGROUND

# TRACKPANETEXTFONT specifies the font for the text portion of the display
#TRACKPANETEXTFONT = fontBig
TRACKPANETEXTFONT = fontNormal


# TRACKPANESTATUSSIZE specifies the size for the status display
TRACKPANESTATUSSIZE = (75,400)

# TRACKPANESTATUSFONT specifies the font for the status text
# Notes from trials 2007-04-16:
#   - On a Sun X server, e.g. mows1, fontMostHuge (Helvetica 40) is
#     way too big for the widest labels.  fontHuge (Helvetica 28) is
#     smaller, and is a bit too small.  
#     Helvetica 30 barely fits the widest label, so is just right.
#   - On a Linux X server, e.g. ssd19, anything larger than Helvetica 35
#     displays the same and appears a little smaller than Helvetica 30
#     on the Sun.  Widest label takes up ~90% of the label width.
# Decided to assume that Gen2 is on Linux and use Helvetical 40, else 30.
TRACKPANESTATUSFONT = 'Helvetica 30'
#TRACKPANESTATUSFONT_GEN2 = 'Helvetica 40'

TRACKPANESTATUSFONT_GEN2 = fontHuge



# TRACKPANEERRORPLOTSIZE specifies the initial size of the scatter plot.
TRACKPANEERRORPLOTSIZE = 300

# TRACKPANELINEPLOTSIZE specifies the initial size of the strip charts.
TRACKPANELINEPLOTSIZE = 400

# TRACKPANEPLOTCOLOR specifies the color configuration of the scatter plot
# The ordering of values is ( foreground, background, grid)
TRACKPANEPLOTCOLOR = \
        (PANECOLORFOREGROUND, PANECOLORGREENBACKGROUND, PANECOLORGREENFOREGROUND)

# TRACKPANEPLOTSCALE specifies the unit length of the first circle
# The ordering of values is ( minimum, maximum, increment, initial)
# TRACKPANEPLOTSCALE = (0.5, 8.0, 0.5, 2.0) # milli arcsec
# TRACKPANEPLOTSCALE = (0.0005, 0.00801, 0.0005, 0.002) # arcsec
TRACKPANEPLOTSCALE = (0.125, 1.001, 0.125, 0.25) # arcsec

# TRACKPANEPLOTSHOWGRID specifies whether the scale grid should be shown.
TRACKPANEPLOTSHOWGRID = 1

# TRACKPANEPLOTTGT specifies the configuration for the plot symbols used in the
# scatter plot pane.  Configuration order is ( dot radius, color, error color ).
TRACKPANEPLOTTGT = ( 1, PANECOLORFOREGROUND, PANECOLORREDALARMFOREGROUND)

# TRACKPANEERRORLINGER specifies the number of AG error targets displayed on
# the plot at a time.
TRACKPANEERRORLINGER = 256

# See Environment Pane Configuration for graph configuration ordering

# TRACKPANEBRIGHTGRAPH specifies the configuration for the Brightness chart
TRACKPANEBRIGHTGRAPH = ( 'Brightness', PANECOLORFOREGROUND, 
        PANECOLORGREENBACKGROUND, None, 0, 0, 1)

# TRACKPANESEEGRAPH specifies the configuration for the Seeing chart
TRACKPANESEEGRAPH = ('Seeing', PANECOLORFOREGROUND, PANECOLORGREENBACKGROUND, 
        None, 0, 0, 1)

# See Environment Pane Configuration for graph line configuration ordering

#TRACKPANEBRIGHTLINES specifies the config for the Temperature chart lines
#TRACKPANEBRIGHTLINES = [('AG', PANECOLORGREENFOREGROUND, 0, 2, '', 'AG: %9d ADU', "Helvetica 12 bold"),
#                        ('SV', PANECOLORPURPLEFOREGROUND, 0, 2, '', 'SV: %9d ADU', "Helvetica 12 bold")]

TRACKPANEBRIGHTLINES = [('AG', PANECOLORGREENFOREGROUND, 0, 2, '', 'AG: %9d ADU', fontXSmallBold),
                        ('SV', PANECOLORPURPLEFOREGROUND, 0, 2, '', 'SV: %9d ADU', fontXSmallBold)]

#ENVPANEHUMLINES specifies the configuration for the Temperature chart lines
#TRACKPANESEELINES = [('AG', PANECOLORGREENFOREGROUND, 0, 2, '', 'AG: %3.1f arcsec', "Helvetica 12 bold"),
#                     ('SV', PANECOLORPURPLEFOREGROUND, 0, 2, '', 'SV: %3.1f arcsec', "Helvetica 12 bold")]

TRACKPANESEELINES = [('AG', PANECOLORGREENFOREGROUND, 0, 2, '', 'AG: %3.1f arcsec', fontXSmallBold),
                     ('SV', PANECOLORPURPLEFOREGROUND, 0, 2, '', 'SV: %3.1f arcsec', fontXSmallBold)]


#TRACKPANEAGPROBEMOVECOLOR specifies the AG Probe text color during motion
TRACKPANEAGPROBEMOVECOLOR = PANECOLORPURPLEFOREGROUND

# Dome Flat Field Pane Configuration

# DOMEPANELABELFONT specifies the font used for the "DomeFF" label.
#DOMEPANELABELFONT = 'Helvetica 16 bold'
DOMEPANELABELFONT = fontBold

# DOMEPANEFOREGROUND specifies the foreground color used in the pane.
DOMEPANEFOREGROUND = PANECOLORFOREGROUND

# DOMEPANEOFF/ONFOREGROUND specify the font colors used in the indicators.
DOMEPANEOFFFOREGROUND = PANECOLORFOREGROUND
DOMEPANEONFOREGROUND  = PANECOLORFOREGROUND

# DOMEPANEBACKGROUND specifies the foreground color used in the pane.
DOMEPANEBACKGROUND = PANECOLORYELLOWBACKGROUND

# DOMEPANELIGHTCOLOR specifies the background/foreground/warning/alarm colors 
# used for each light.  Ordering is [ (10W light config), (600W light config) ]
DOMEPANELIGHTCOLOR = \
    [(DOMEPANEBACKGROUND, PANECOLORBRIGHTGREENFOREGROUND, 
      PANECOLORYELLOWWARNBACKGROUND, PANECOLORREDALARMBACKGROUND),
     (DOMEPANEBACKGROUND, PANECOLORBRIGHTGREENFOREGROUND, 
      PANECOLORYELLOWWARNBACKGROUND, PANECOLORREDALARMBACKGROUND)]


# Calibration Pane Configuration

# Calibration lamp labels
CALPANEHCT1LABEL = 'Th-Ar1'
CALPANEHCT2LABEL = 'Th-Ar2'
CALPANEHAL1LABEL = 'Hal1'
CALPANEHAL2LABEL = 'Hal2'
CALPANERGL1LABEL = 'Ne'
CALPANERGL2LABEL = 'Ar'

# CALPANELABELFONT specifies the font used for the "CAL" label.
#CALPANELABELFONT = 'Helvetica 16 bold'
CALPANELABELFONT = fontBold



# CALPANELABELFONT specifies the font used for the Amperage label.
#CALPANEAMPFONT = 'Helvetica 8'
CALPANEAMPFONT = fontXSmall


# CALPANEFOREGROUND specifies the foreground color used in the pane.
CALPANEFOREGROUND = PANECOLORFOREGROUND

# CALPANEOFF/ONFOREGROUND specify the font colors used in the indicators.
CALPANEOFFFOREGROUND = PANECOLORFOREGROUND
CALPANEONFOREGROUND  = PANECOLORFOREGROUND

# CALPANEBACKGROUND specifies the foreground color used in the pane.
CALPANEBACKGROUND = PANECOLORYELLOWBACKGROUND

# CALPANELIGHTCOLOR specifies the (background,foreground) color used for 
# each light.  Ordering is:
# [ (HCT1 light config), (HCT2 light config), (HAL1 light config), 
#   (HAL2 light config), (RGL1 light config), (RGL2 light config) ] 
CALPANELIGHTCOLOR = [ (CALPANEBACKGROUND, PANECOLORBRIGHTGREENFOREGROUND,
                       PANECOLORYELLOWWARNBACKGROUND, PANECOLORREDALARMBACKGROUND),
                      (CALPANEBACKGROUND, PANECOLORBRIGHTGREENFOREGROUND,
                       PANECOLORYELLOWWARNBACKGROUND, PANECOLORREDALARMBACKGROUND),
                      (CALPANEBACKGROUND, PANECOLORBRIGHTGREENFOREGROUND,
                       PANECOLORYELLOWWARNBACKGROUND, PANECOLORREDALARMBACKGROUND),
                      (CALPANEBACKGROUND, PANECOLORBRIGHTGREENFOREGROUND,
                       PANECOLORYELLOWWARNBACKGROUND, PANECOLORREDALARMBACKGROUND),
                      (CALPANEBACKGROUND, PANECOLORBRIGHTGREENFOREGROUND,
                       PANECOLORYELLOWWARNBACKGROUND, PANECOLORREDALARMBACKGROUND),
                      (CALPANEBACKGROUND, PANECOLORBRIGHTGREENFOREGROUND,
                       PANECOLORYELLOWWARNBACKGROUND, PANECOLORREDALARMBACKGROUND)]

######################################################################
################   message and alert base ID's   #####################
######################################################################

# TelStat
TSinfoBase      = 100
TSwarnBase      = 200
TSerrBase       = 300

# Global States
GSinfoBase      = 1100
GSwarnBase      = 1200
GSerrBase       = 1300

# Pointing Pane
TSinfoBase      = 2100
TSwarnBase      = 2200
TSerrBase       = 2300

# Menu Pane
MenuInfoBase    = 3100
MenuWarnBase    = 3200
MenuErrBase     = 3300

# Help Popups
HelpInfoBase    = 4100
HelpWarnBase    = 4200
HelpErrBase     = 4300

# TelescopePane
TeleInfoBase    = 5100
TeleWarnBase    = 5200
TeleErrBase     = 5300

# Limits Pane
LimInfoBase     = 6100
LimWarnBase     = 6200
LimErrBase      = 6300

# Target Pane
TargInfoBase    = 7100
TargWarnBase    = 7200
TargErrBase     = 7300

# Time Pane
TimeInfoBase    = 8100
TimeWarnBase    = 8200
TimeErrBase     = 8300

# Environment Pane
EnvInfoBase     = 9100
EnvWarnBase     = 9200
EnvErrBase      = 9300

# Tracking Pane
TrackInfoBase   = 10100
TrackWarnBase   = 10200
TrackErrBase    = 10300

# Dome Pane
DomeInfoBase    = 11100
DomeWarnBase    = 11200
DomeErrBase     = 11300

# Calibration Pane
CalInfoBase     = 12100
CalWarnBase     = 12200
CalErrBase      = 12300

# Dummy Pane
DummyInfoBase   = 14100
DummyWarnBase   = 14200
DummyErrBase    = 14300


# StatIO
StatioInfoBase  = 20100
StatioWarnBase  = 20200
StatioErrBase   = 20300

# AudioPlayer
AudioInfoBase   = 21100
AudioWarnBase   = 21200
AudioErrBase    = 21300

# DispType
DispTypeInfoBase = 22100
DispTypeWarnBase = 22200
DispTypeErrBase  = 22400

# OSSC_screenPrintConversions, etc.
ScrPrntInfoBase = 23100
ScrPrntWarnBase = 23200
ScrPrntErrBase  = 23400

# TelStatProcSize
TSPSInfoBase    = 24100
TSPSWarnBase    = 24200
TSPSErrBase     = 24400


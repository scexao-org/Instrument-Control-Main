# DispType.py -- Sam Streeper -- 2008-10-03

##############################################################################
################   import needed modules   ###################################
##############################################################################

import os
import sys
import types
import time
from math import *

import Util
import TelStatLog
import StatusDictionary as SD
import TelStat_cfg

gen2libpath = './gen2lib'
if  os.path.exists( gen2libpath ):
    sys.path.append( gen2libpath )
    from SOSS.status import STATNONE, STATERROR
else:
    STATNONE=STATERROR=None

##############################################################################
################   global constants   ########################################
##############################################################################

# type codes
DDT_null        = 0
DDT_bool        = 1
DDT_int         = 2
DDT_float       = 3
DDT_string      = 4
DDT_angle       = 5
DDT_time        = 6
DDT_unixTime    = 7

ArcSecToRad     = pi / (180.0 * 60 * 60)
ArcDegToRad     = pi / 180.0

# UNDEF must be the same as in TelStat_cfg.py
UNDEF = -1

DispTypeInfoBase      = TelStat_cfg.DispTypeInfoBase

DispTypeWarnBadStrVal = TelStat_cfg.DispTypeWarnBase

DispTypeErrBase       = TelStat_cfg.DispTypeErrBase
DispTypeConvErr       = TelStat_cfg.DispTypeErrBase

##############################################################################
################   exception definition   ####################################
##############################################################################

class ConversionError( Exception ):
    """Exception class to be raised if any error occurs in conversion."""
    def __init__( self, value ):
        self.value = value
    def __str__( self ):
        return `self.value`

##############################################################################
################   conversion functions   ####################################
##############################################################################

def OSPC_convert( str, convertCode ):
    """Convert a string obtained from OSSC_screenPrint or a compatible 
    simulation program, to the fundamental type needed by StatIO.py."""
    #? print "  __OSPC_convert:  str = `%s', convertCode = %d" % ( str, convertCode )
    if  str == '' or str == 'None':
        return None

    elif  convertCode == SD.OSPC_ConvrtBool:
        try:
            if  str.startswith("T") or str.startswith("t"):
                return True
            else:
                return False
        except Exception, value:
            raise  ConversionError, "boolean conversion error"

    elif  convertCode == SD.OSPC_ConvrtInt:
        try:
            if  str.startswith("0x") or str.startswith("0X"):
                return long(str[2:],16)
            else:
                return long(round(float(str)))
        except Exception, value:
            raise  ConversionError, "integer conversion error"

    elif  convertCode == SD.OSPC_ConvrtHex:
        try:
            return long(str,16)
        except Exception, value:
            raise  ConversionError, "hexadecimal conversion error"

    elif  convertCode == SD.OSPC_ConvrtFloat:
        try:
            return float(str)
        except Exception, value:
            raise  ConversionError, "float conversion error"

    elif  convertCode == SD.OSPC_ConvrtDegAng:      # DD.dddddddd
        try:
            deg  = float( str )
            return deg * 3600.0         # setValue units are arcsec
        except Exception, value:
            raise  ConversionError, "DegAng conversion error"

    elif  convertCode == SD.OSPC_ConvrtFmosAsec:      # Ssssss (Asec & 100ths of milliAsec)
        try:
            a  = int( str )
            return a * 0.00001         # setValue units are arcsec
        except Exception, value:
            raise  ConversionError, "Fmos Asec conversion error"

    elif  convertCode == SD.OSPC_ConvrtRA:          # HHMMSSssss
        try:
            hr   = int( str[0:2] )
            m  = int( str[2:4] )
            sec  = int( str[4:6] )
            secf = int( str[6:10] )
            return (hr * 3600 + m * 60 + sec + secf * 0.0001) * 15.0
        except Exception, value:
            raise  ConversionError, "RA conversion error"

    elif  convertCode == SD.OSPC_ConvrtDec:         # DDMMSSssss
        try:
            if  str[0] == '8':
                sign = -1
            else:
                sign = +1
            deg  = int( str[1:4] )
            min  = int( str[4:6] )
            sec  = int( str[6:8] )
            secf = int( str[8:10] )
            return sign * (deg * 3600 + min * 60 + sec + secf * 0.01)
        except Exception, value:
            raise  ConversionError, "Declination conversion error"

    elif  convertCode == SD.OSPC_ConvrtMinTime:     # MMM
        # this used for conversion of TSCL.LIMIT_*
        try:
            min  = float( str )
            return min * 60     # return hrsec
        except Exception, value:
            raise  ConversionError, "Minutes time conversion error"

    elif  convertCode == SD.OSPC_ConvrtYrTime:      # YYYYMMDDhhmmss.sss
        try:
            yr   = int( str[0:4] )
            mnth = int( str[4:6] )
            day  = int( str[6:8] )
            hr   = int( str[8:10] )
            min  = int( str[10:12] )
            sec  = int( str[12:14] )
            secf = int( str[14:17] )
            return "%4d-%02d-%02d %02d:%02d:%02d.%03d" % \
                                                (yr,mnth,day, hr,min,sec,secf)
        except Exception, value:
            raise  ConversionError, "Date/Time conversion error"

    elif  convertCode == SD.OSPC_ConvrtUnixTime:
        try:
            if  str[0:4] == "None":     # convert string 'None' into None
                return None
            else:
                return float(str)
        except Exception, value:
            raise  ConversionError, "Unix time (since epoch) conversion error"

    else:  # convertCode == SD.OSPC_ConvrtStr or undefined
        if  str[0] == "#": # convert null or comment into None
            return None
        else:
            return str.strip()  # no conversion

def OSPC_G2convert( val, convertCode ):
    """Convert a value obtained from the Gen 2 status server to the fundamental 
    type needed by StatIO.py."""
    #? print "  __OSPC_G2convert:  val = %s, convertCode = %d" % ( `val`, convertCode )
    if  val == STATNONE:
        return None

    elif  convertCode == SD.OSPC_ConvrtInt or convertCode == SD.OSPC_ConvrtHex:
        try:
##             if  type(val) == types.StringType and val.startswith("B0x"):
##                 #? print '*** long int value = 0x%x' % long(val[3:],16)
##                 return long(val[3:],16)
            if  type(val) == types.IntType or type(val) == types.LongType:
                return val
            elif  type(val) == types.FloatType or type(val) == types.StringType:
                return long(val)
            else:
                #? print "    integer conversion type error on %s" % `val`
                raise  ConversionError, "integer conversion type error on %s"%\
                                                                          `val`
        except Exception, value:
            #? print "    integer conversion error on %s, %s" % (`val`, value)
            raise  ConversionError, "integer conversion error %s on %s" % \
                                                                (`value`,`val`)

    elif  convertCode == SD.OSPC_ConvrtDegAng:      # float degrees
        try:
            if  type(val) == types.StringType:
                val = float( val )
            return val * 3600.0         # setValue units are arcsec
        except Exception, value:
            raise  ConversionError, "DegAng conversion error on %s on %s" % \
                                                                (`value`,`val`)

    elif  convertCode == SD.OSPC_ConvrtRA:          # HHMMSSssss
        try:
            val = ('%010x' % val)
            hr   = int( val[0:2] )
            m  = int( val[2:4] )
            sec  = int( val[4:6] )
            secf = int( val[6:9] )
            return (hr * 3600 + m * 60 + sec + secf * 0.001) * 15.0
        except Exception, value:
            raise  ConversionError, "RA conversion error on %s on %s" % \
                                                                (`value`,`val`)

    elif  convertCode == SD.OSPC_ConvrtDec:         # DDMMSSssss
        try:
            val = ('%010x' % val)
            #print "***", val
            if  val[0] == '8':
                sign = -1
            else:
                sign = +1
            val = val[2:]
            deg  = int( val[0:2] )
            m  = int( val[2:4] )
            sec  = int( val[4:6] )
            secf = int( val[6:8] )
            return sign * (deg * 3600 + m * 60 + sec + secf * 0.01)
        except Exception, value:
            raise  ConversionError, "Declination conversion error on %s on %s"%\
                                                                (`value`,`val`)

    elif  convertCode == SD.OSPC_ConvrtMinTime:     # minutes
        # this used for conversion of TSCL.LIMIT_*
        try:
            return val * 60     # return hrsec
        except Exception, value:
            raise ConversionError, "Minutes time conversion error on %s on %s"%\
                                                                (`value`,`val`)

#?    elif  convertCode == SD.OSPC_ConvrtStr and type(val) != types.StringType:
#?        # this used for conversion of STATS.EQUINOX
#?        return str(val)

    else:
        return val          # for everything else, no conversion

#?tmpOfInterest = ('TSCL.AG1Intensity','TSCL.SV1Intensity','TSCV.AGExpTime',
#?    'TSCV.CAL_HAL_LAMP1','TSCV.CAL_HAL_LAMP2','TSCV.CellCover','TSCV.DomeFF_1B',
#?    'TSCV.DomeShutter','TSCV.FOCUSINFO','TSCV.M1Cover')
#? tmpOfInterest = ('TSCV.AGTheta','VGWD.FWHM.AG')
tmpOfInterest = ()
##############################################################################
################   declare display-data-type classes   #######################
##############################################################################

# Display data type base class -- may not really be needed
class DisplayDataType:
    '''Base class for all display data-types, identifying required methods.'''

    def __init__(self,value=None,key='??',OSPCcode=None, active=True):
        """Constructor for root display data type; do generic initialization."""
        self.key      = key
        self.ospcCode = OSPCcode
        self.ddt = DDT_null
        self.active = active
    def setActive(self,active=True):   # set this object as active or not
        self.active = active
    def getActive(self):        # get this object's active flag
        return self.active
    def setValue(self,value):   # set value
        self.setValue(value)
    def fromOSP(self,strVal):   # set value from an OSSC_screenPrint string
        self.setValue(OSPC_convert( strVal, self.ospcCode ))
    def fromGen2(self,g2Val):   # set value from a Gen2 value from status.py
        if  self.key in tmpOfInterest:
            print '%s: ospcCode = %d, g2Val = ' % (self.key, self.ospcCode),g2Val, ', g2 type = ', type(g2Val)
        self.setValue(OSPC_G2convert( g2Val, self.ospcCode ))
        if  self.key in tmpOfInterest:
            if  self.ddt == DDT_int:
                print '   value = ', self.value(), ', formatHex() = ', self.formatHex()
            else:
                print '   value = ', self.value()
    def fromLogFmt(self,strVal):
        """Set value from a data log string value."""
        self.setValue(strVal)   # Good only for string format!!
    def formatForLog(self):
        """Return a data-log-formatted string."""
        return `self.myValue`   # NOT GOOD, MUST BE OVERRIDEN
    def value(self):            # return value
        return self.myValue     # NOT GOOD, MUST BE OVERRIDEN
    def format(self):           # return default-formatted string
        return `self.myValue`
    def myDDT(self):            # return my display data type code
        return self.ddt

class BoolDDT(DisplayDataType):
    '''Boolean display data-type.'''

    def __init__(self,value=None,key='??',OSPCcode=None, active=True):
        """Constructor for boolean display data type."""
        DisplayDataType.__init__(self,key=key,OSPCcode=OSPCcode, active=active)
        self.boolValue = value
        self.ddt = DDT_bool

    def setValue(self, value=None):
        """Set boolean value."""
        self.boolValue = value

    def toggleValue(self):
        """Invert boolean value."""
        if  self.boolValue != None:     # can't invert None
            self.boolValue = not self.boolValue

    def value(self):
        """Return boolean value."""
        return self.boolValue

    def format(self,width=5):
        """Return formatted string for boolean value."""
        if  self.boolValue == None:
            return '<No Data>'
        elif  self.boolValue == UNDEF:
            return '<Undefined>'
        else:
            if  self.boolValue:
                if  width < 5:
                    return 'T    '[0:width]
                else:
                    return 'True      '[0:width]
            else:
                if  width < 5:
                    return 'F    '[0:width]
                else:
                    return 'False     '[0:width]

    def fromLogFmt(self,strVal):
        """Set value from a data log string value."""
        if  strVal == 'True':
            self.boolValue = True
        elif  strVal == 'False':
            self.boolValue = False
        elif  strVal == 'None':
            self.boolValue = None
        else:
            self.boolValue = UNDEF

    def formatForLog(self):
        """Return a data-log-formatted string."""
        #? print ' BoolDDT.formatForLog, boolValue(%s) = ' % self.key, self.boolValue
        if  self.boolValue == None:
            return 'None'
        elif  self.boolValue == UNDEF:
            return 'UNDEF'
        elif  self.boolValue:
            return 'True'
        else:
            return 'False'

class IntDDT(DisplayDataType):
    '''Integer display data-type, including longs.'''

    def __init__(self,value=None,key='??',OSPCcode=None, active=True):
        """Constructor for integer display data type."""
        DisplayDataType.__init__(self,key=key,OSPCcode=OSPCcode, active=active)
        self.intValue = value
        self.ddt = DDT_int

    def setValue(self, value=None):
        """Set integer value."""
        self.intValue = value

    def incrementValue(self):
        """Increment integer value."""
        if  self.intValue != None:
            self.intValue = self.intValue + 1

    def value(self):
        """Return integer value."""
        return self.intValue

    def format(self,width=2):
        """Return formatted string for integer value."""
        format = '%' + str(3+width) + 'd'
        if  self.intValue == None:
            return '<No Data>'
        elif  self.intValue == UNDEF:
            return '<Undefined>'
        else:
            return  ( format % self.intValue )

    def formatHex(self,width=2):
        """Return hex-formatted string for integer value."""
        format = '0x%0' + str(3+width) + 'x'
        if  self.intValue == None:
            return '<No Data>'
        elif  self.intValue == UNDEF:
            return '<Undefined>'
        else:
            return  ( format % self.intValue )

    def fromLogFmt(self,strVal): 
        """Set value from a data log string value."""
        if  strVal == 'None':
            self.intValue = None
        elif  strVal == 'UNDEF':
            self.intValue = UNDEF
        else:
            try:
                if  strVal[0:2] == '0x':
                    self.intValue = long( strVal, 16 )
                else:
                    self.intValue = long( strVal )
            except Exception, value:
                self.intValue = None
                exceptMsg = \
                   "Bad integer format (%s) for alias %s, exception msg %s" % \
                                                      (strVal,self.key,`value`)
                TelStatLog.TelStatLog( DispTypeConvErr, 
                            'ERROR (DispTypes:IntDDT): ' + exceptMsg, True )
                raise  ConversionError, exceptMsg

    def formatForLog(self):
        """Return a data-log-formatted string."""
        #? print '  IntDDT.formatForLog, intValue(%s) = ' % self.key, self.intValue
        if  self.intValue == None:
            return 'None'
        elif  self.intValue == UNDEF:
            return 'UNDEF'
        else:
            return '%d' % self.intValue


class FloatDDT(DisplayDataType):
    '''Float display data-type.'''

    def __init__(self,value=None,key='??',OSPCcode=None, active=True):
        """Constructor for floating point display data type."""
        DisplayDataType.__init__(self,key=key,OSPCcode=OSPCcode,active=active)
        self.floatValue = value
        self.ddt = DDT_float

    def setValue(self, value=None):
        """Set floating point value."""
        if  value == None:
            self.floatValue = None
        else:
            try:
                self.floatValue = float(value)
            except Exception, excValue:
                self.floatValue = None
                exceptMsg = "setValue: Bad floating point format " + \
                                      "(%s) for alias %s, exception msg %s" % \
                                                     (value,self.key,`excValue`)
                TelStatLog.TelStatLog( DispTypeConvErr, 
                             'ERROR (DispTypes:FloatDDT): ' + exceptMsg, False )
                raise  ConversionError, exceptMsg

    def incrementValue(self):
        """Increment floating point value."""
        if  self.floatValue != None:
            self.floatValue = self.floatValue + 1.0

    def value(self):
        """Return floating point value."""
        return self.floatValue

    def format(self,width=6,decimalPlaces=2):
        """Return formatted string for floating point value."""
        #? print '%s = %s   ' % (self.key,`self.floatValue`), type(self.floatValue)
        if  self.floatValue == None:
            return '<No Data>'
        elif  self.floatValue == UNDEF:
            return '<Undefined>'
        else:
            format = '%' + str(width) + '.' + str(decimalPlaces) + 'f'
            return  ( format % self.floatValue )

    def fromLogFmt(self,strVal): 
        """Set value from a data log string value."""
        if  strVal == 'None':
            self.floatValue = None
        elif  strVal == 'UNDEF':
            self.floatValue = UNDEF
        else:
            try:
                self.floatValue = float( strVal )
            except Exception, value:
                self.floatValue = None
                exceptMsg = "fromLogFmt: Bad floating point format " + \
                                      "(%s) for alias %s, exception msg %s" % \
                                                      (strVal,self.key,`value`)
                TelStatLog.TelStatLog( DispTypeConvErr, 
                             'ERROR (DispTypes:FloatDDT): ' + exceptMsg, True )
                raise  ConversionError, exceptMsg

    def formatForLog(self):
        """Return a data-log-formatted string."""
        #? print 'FloatDDT.formatForLog, floatValue(%s) = ' % self.key, self.floatValue
        if  self.floatValue == None:
            return 'None'
        elif  self.floatValue == UNDEF:
            return 'UNDEF'
        else:
            return '%.6f' % self.floatValue


class StrDDT(DisplayDataType):
    '''String display data-type.'''

    def __init__(self,value=None,key='??',OSPCcode=None, active=True):
        """Constructor for string display data type."""
        DisplayDataType.__init__(self,key=key,OSPCcode=OSPCcode,active=active)
        self.setValue( value )
        self.ddt = DDT_string

    def setValue(self, value=None):
        """Set string value."""
        if  value != None and type(value) != types.StringType:
            TelStatLog.TelStatLog( DispTypeWarnBadStrVal,
                    'WARNING (DispType:StrDDT): non-string input type ' + \
                    '(%s), key = %s, value = %s' % \
                    ( type(value), self.key, `value` ) )
            self.strValue = None
            return
        if  value == None or value[0:1] == "#":
            self.strValue = None
        else:
            self.strValue = value

    def value(self):
        """Return string value."""
        return self.strValue

    def format(self,width=None):
        """Return formatted string for string value."""
        if  width == None:
            format = '%s'
        else:
            format = '%' + str(width) + 's'
        if  self.strValue == None:
            return '<No Data>'
        elif  self.strValue == UNDEF:
            return '<Undefined>'
        return  ( format % self.strValue )

    def fromLogFmt(self,strVal): 
        """Set value from a data log string value."""
        if  strVal == 'None':
            self.strValue = None
        elif  strVal == 'UNDEF':
            self.strValue = UNDEF
        else:
            self.strValue = strVal

    def formatForLog(self):
        """Return a data-log-formatted string."""
        #? print '  StrDDT.formatForLog, strValue(%s) = ' % self.key, self.strValue
        if  self.strValue == None:
            return 'None'
        elif  self.strValue == UNDEF:
            return 'UNDEF'
        else:
            return self.strValue


class AngleDDT(DisplayDataType):
    """Data-type to hold an angle, whether it be specified in units of arc
        (deg, min, arcsec) or time (hour, min, hrsec)"""

    SetTypeArc = 0
    SetTypeHr  = 1

    def __init__(self, arcsec=None, deg=None, hrsec=None, key='??',
                       OSPCcode=None, active=True):
        """Constructor for angle display data type; used for RA, DEC, EL, AZ."""
        DisplayDataType.__init__(self,key=key,OSPCcode=OSPCcode,active=active)
        self.ddt = DDT_angle
        if  arcsec != None:
            self.arcsec = arcsec
            self.hrsec  = arcsec / 15.0
            self.settype = self.SetTypeArc
        elif  deg != None:
            self.arcsec = deg * 3600.0
            self.hrsec  = self.arcsec / 15.0
            self.settype = self.SetTypeArc
        elif  hrsec != None:
            self.hrsec  = hrsec
            self.arcsec = hrsec * 15.0
            self.settype = self.SetTypeHr
        else:
            self.arcsec = None
            self.hrsec  = None
            self.settype = self.SetTypeArc
        #? print 'arcsec = ', self.arcsec, ', hrsec = ', self.hrsec


    def setValue(self, arcsec=None, deg=None, hrsec=None):
        """Set value in specified units."""
        #? print 'setValue: arcsec = ', arcsec, ', hrsec = ', hrsec, ', deg = ', deg
        if  arcsec != None:
            self.arcsec = arcsec
            self.hrsec  = arcsec / 15.0
            self.settype = self.SetTypeArc
        elif  deg != None:
            self.arcsec = deg * 3600.0
            self.hrsec  = arcsec / 15.0
            self.settype = self.SetTypeArc
        elif  hrsec != None:
            self.hrsec  = hrsec
            self.arcsec = hrsec * 15.0
            self.settype = self.SetTypeHr
        else:
            self.arcsec = None
            self.hrsec  = None
            self.settype = self.SetTypeArc


    def incrementValue(self):
        """Increment angle value in specified units."""
        if  self.arcsec == None:
            return      # no-op
        if  self.settype == self.SetTypeArc:
            self.arcsec = self.arcsec + 1.0
            self.hrsec  = self.arcsec / 15.0
        else:  # self.settype == self.SetTypeHr
            self.hrsec  = self.hrsec + 1.0
            self.arcsec = self.hrsec * 15.0


    def value(self):
        """Return value in default units, i.e. arcsec."""
        return self.arcsec

    def value_ArcSec(self):
        """Return value in arcsec."""
        return self.arcsec

    def value_ArcMin(self):
        """Return value in arcmin."""
        if  self.arcsec == None:
            return None
        elif  self.arcsec == UNDEF:
            return UNDEF
        return self.arcsec / 60.0

    def value_ArcDeg(self):
        """Return value in arc degrees."""
        if  self.arcsec == None:
            return None
        elif  self.arcsec == UNDEF:
            return UNDEF
        return self.arcsec / 3600.0

    def value_Rad(self):
        """Return value in radians."""
        if  self.arcsec == None:
            return None
        elif  self.arcsec == UNDEF:
            return UNDEF
        return self.arcsec  * ArcSecToRad

    def value_HrSec(self):
        """Return value in hr sec."""
        if  self.arcsec == None:
            return None
        elif  self.arcsec == UNDEF:
            return UNDEF
        return self.hrsec

    def value_HrMin(self):
        """Return value in hr min."""
        if  self.arcsec == None:
            return None
        elif  self.arcsec == UNDEF:
            return UNDEF
        return self.hrsec / 60.0

    def value_Hr(self):
        """Return value in hours."""
        if  self.arcsec == None:
            return None
        elif  self.arcsec == UNDEF:
            return UNDEF
        return self.hrsec / 3600.0

    def tan(self):
        """Return tangent of value."""
        if  self.arcsec == None:
            return None
        elif  self.arcsec == UNDEF:
            return UNDEF
        return tan( self.arcsec  * ArcSecToRad )

    def sin(self):
        """Return sin of value."""
        if  self.arcsec == None:
            return None
        elif  self.arcsec == UNDEF:
            return UNDEF
        return sin( self.arcsec  * ArcSecToRad )

    def cos(self):
        """Return cos of value."""
        if  self.arcsec == None:
            return None
        elif  self.arcsec == UNDEF:
            return UNDEF
        return cos( self.arcsec  * ArcSecToRad )


    def format(self,decimalPlaces=2):
        """Return default-formatted string, conversion depends on settype."""
        if  self.arcsec == None:
            return '<No Data>'
        elif  self.arcsec == UNDEF:
            return '<Undefined>'
        if  self.settype == self.SetTypeArc:
            return self.format_DegMinSec(decimalPlaces)
        else:   # self.settype == self.SetTypeHr
            return self.format_HrMinSec(decimalPlaces)

    def format_Deg(self,decimalPlaces=2):
        """Return Deg-formatted string."""
        if  self.arcsec == None:
            return '<No Data>'
        elif  self.arcsec == UNDEF:
            return '<Undefined>'
        if  self.arcsec > 0.0:
            signChar = " +"
        elif  self.arcsec < 0.0:
            signChar = " "
        else:
            signChar = "  "
        format = '%s%.' + str(decimalPlaces) + 'f'
        deg = self.arcsec/3600
        return  ( format % (signChar, deg) )

    def format_DegMinSec(self,decimalPlaces=2):
        """Return DegMinSec-formatted string."""
        if  self.arcsec == None:
            return '<No Data>'
        elif  self.arcsec == UNDEF:
            return '<Undefined>'
        if  self.arcsec > 0.0:
            signChar = "+"
            aSec = self.arcsec
        elif  self.arcsec < 0.0:
            signChar = "-"
            aSec = -self.arcsec
        else:
            signChar = " "
            aSec = 0.0
        format = '%s%02d:%02d:%0' + str(3+decimalPlaces) + '.' + str(decimalPlaces) + 'f'
        deg = floor( aSec/3600 )
        min = floor( (aSec - deg * 3600) / 60 )
        sec = aSec - deg * 3600 - min * 60
        # NOTE: this will be correct to decimalPlaces, but if sec is
        # almost 60 (e.g. 59.9999999), the formatted value may appear
        # incorrect (e.g. +3:05:60.00)
        return  ( format % (signChar,deg,min,sec) )

    def format_HrMinSec(self, decimalPlaces=2, useSign=True):
        """Return HrMinSec-formatted string."""
        if  self.arcsec == None:
            return '<No Data>'
        elif  self.arcsec == UNDEF:
            return '<Undefined>'
        if  self.arcsec > 0.0:
            if useSign == True:
                signChar = "+"
            else:
                signChar = " " 
            hSec = self.hrsec
        elif  self.hrsec < 0.0:
            signChar = "-"              # MUST use sign if it is negative!!
            hSec = -self.hrsec
        else:
            signChar = " "
            hSec = 0.0
        format = '%s%02d:%02d:%0' + str(3+decimalPlaces) + '.' + \
                 str(decimalPlaces) + 'f'
        hr  =  hSec//3600
        m =  (hSec - hr  * 3600) // 60 
        sec = hSec - (hr  * 3600) - (m * 60)
        # NOTE: this will be correct to decimalPlaces, but if sec is
        # almost 60 (e.g. 59.9999999), the formatted value may appear
        # incorrect (e.g. +3:05:60.00)
        return  ( format % (signChar,hr,m,sec) )

    def fromLogFmt(self,strVal): 
        """Set value from a data log string value."""
        if  strVal == 'None':
            self.arcsec = None
            self.hrsec  = None
        elif  strVal == 'UNDEF':
            self.arcsec = UNDEF
            self.hrsec  = UNDEF
        else:
            try:
                self.arcsec = float( strVal )
                self.hrsec  = self.arcsec / 15.0
            except Exception, value:
                self.arcsec = None
                self.hrsec  = None
                exceptMsg = "Bad arcsec floating point format " + \
                                      "(%s) for alias %s, exception msg %s" % \
                                                      (strVal,self.key,`value`)
                TelStatLog.TelStatLog( DispTypeConvErr, 
                            'ERROR (DispTypes:AngleDDT): ' + exceptMsg, True )
                raise  ConversionError, exceptMsg

    def formatForLog(self):
        """Return a data-log-formatted string."""
        #? print 'AngleDDT.formatForLog, arcsec(%s) = ' % self.key, self.arcsec
        if  self.arcsec == None:
            return 'None'
        elif  self.arcsec == UNDEF:
            return 'UNDEF'
        else:
            return '%.2f' % self.arcsec


class TimeDDT(DisplayDataType):
    '''Time display data-type.'''

    def __init__(self,hrsec=None,hr=None,key='??',OSPCcode=None,active=True):
        """Constructor for time display data type."""
        DisplayDataType.__init__(self,key=key,OSPCcode=OSPCcode,active=active)
        self.ddt = DDT_time
        if  hrsec != None:
            self.hrsec  = hrsec
        elif  hr != None:
            self.hrsec  = hr * 3600
        else:
            self.hrsec  = None
        #? print 'hrsec = ', self.hrsec


    def setValue(self, hrsec=None, hrmin=None, hr=None):
        """Set value in specified units."""
        if  (hrmin==None and hrsec==None and hr==None):
            self.hrsec  = None
            return
        if  hr != None:
            self.hrsec  = hr * 3600
        else:
            self.hrsec  = 0
        if  hrmin != None:
            self.hrsec  += hrmin * 60
        if  hrsec != None:
            self.hrsec  += hrsec


    def incrementValue(self):
        """Increment seconds of value."""
        if  self.hrsec == None:
            return      # no-op
        self.hrsec = self.hrsec + 1.0


    def value(self):
        """Return value in default units, i.e. seconds."""
        return self.hrsec

    def value_Sec(self):
        """Return value in seconds."""
        return self.hrsec

    def value_Min(self):
        """Return value in minutes"""
        if  self.hrsec == None:
            return None
        elif  self.hrsec == UNDEF:
            return UNDEF
        return self.hrsec / 60.0

    def value_Hr(self):
        """Return value in hours."""
        if  self.hrsec == None:
            return None
        elif  self.hrsec == UNDEF:
            return UNDEF
        return self.hrsec / 3600.0


    def format(self,decimalPlaces=2):
        """Return default-formatted string."""
        if  self.hrsec == None:
            return '<No Data>'
        elif  self.hrsec == UNDEF:
            return '<Undefined>'
        return self.format_HrMinSec(decimalPlaces)

    def format_HrMinSec(self,decimalPlaces=2):
        """Return HrMinSec-formatted string."""
        if  self.hrsec == None:
            return '<No Data>'
        elif  self.hrsec == UNDEF:
            return '<Undefined>'
        format = '%02d:%02d:%0' + str(3+decimalPlaces) + '.' + \
                                                        str(decimalPlaces) + 'f'
        hr  = floor( self.hrsec/3600 )
        m = floor( (self.hrsec - hr  * 3600) / 60 )
        sec = self.hrsec - hr  * 3600 - m * 60
        return  ( format % (hr ,m, sec) )

    def format_HrMin(self,decimalPlaces=2):
        """Return HrMin-formatted string -- 23 hr 59 min."""
        if  self.hrsec == None:
            return '<No Data>'
        elif  self.hrsec == UNDEF:
            return '<Undefined>'
        if  decimalPlaces > 0:
            format = '%02d hr %0' + str(3+decimalPlaces) + '.' + \
                                                        str(decimalPlaces) + 'f min'
        else:
            format = '%02d hr %3d min'
        hr = floor( self.hrsec/3600 )
        min = (self.hrsec - hr * 3600) / 60.0
        return  ( format % (hr,min) )

    def format_HM(self,decimalPlaces=2):
        """Return HM-formatted string -- 23h 59m."""
        if  self.hrsec == None:
            return '<No Data>'
        elif  self.hrsec == UNDEF:
            return '<Undefined>'
        if  decimalPlaces > 0:
            format = '%dh %0' + '.' + str(decimalPlaces) + 'fm'
        else:
            format = '%dh %dm'
        hr = floor( self.hrsec/3600 )
        min = (self.hrsec - hr * 3600) / 60.0
        return  ( format % (hr,min) )

    def format_Hr(self,decimalPlaces=2):
        """Return Hr-formatted string."""
        if  self.hrsec == None:
            return '<No Data>'
        elif  self.hrsec == UNDEF:
            return '<Undefined>'
        format = '%0' + str(3+decimalPlaces) + '.' + str(decimalPlaces) + 'f'
        hr = self.hrsec/3600
        return  ( format % hr)

    def fromLogFmt(self,strVal): 
        """Set value from a data log string value."""
        if  strVal == 'None':
            self.hrsec  = None
        elif  strVal == 'UNDEF':
            self.hrsec = UNDEF
        else:
            try:
                self.hrsec  = float( strVal )
            except Exception, value:
                self.hrsec  = None
                exceptMsg = "Bad hrsec floating point format " + \
                                     "(%s) for alias %s, exception msg %s" % \
                                                     (strVal,self.key,`value`)
                TelStatLog.TelStatLog( DispTypeConvErr, 
                              'ERROR (DispTypes:TimeDDT): ' + exceptMsg, True )
                raise  ConversionError, exceptMsg

    def formatForLog(self):
        """Return a data-log-formatted string."""
        #? print ' TimeDDT.formatForLog, hrsec(%s) = ' % self.key, self.hrsec
        if  self.hrsec == None:
            return 'None'
        elif  self.hrsec == UNDEF:
            return 'UNDEF'
        else:
            return '%.4f' % self.hrsec


# Location constant for Subaru Telescope
DEFAULTLONGITUDE = -155.60222  # Degrees W of Prime Meridian

class UnixTimeDDT(DisplayDataType):
    '''UnixTime display data-type; inherent value is in 
    seconds since Epoch (1970 for Unix).'''

    def __init__(self, hrsec=None, logStr='None', pyHSTtuple=None,
                 key='??', OSPCcode=None, active=True):
        """Constructor for date/time display data type."""
        DisplayDataType.__init__(self,key=key,OSPCcode=OSPCcode,active=active)
        self.ddt = DDT_unixTime
        #? print '__init__: hrsec = ', hrsec, ', logStr = ', logStr, ', pyHSTtuple = ', pyHSTtuple
        self.setValue( hrsec, logStr, pyHSTtuple )

    def setValue(self, hrsec=None, logStr='None', pyHSTtuple=None):
        """Set value."""
        #? print 'setValue: hrsec = ', hrsec, ', logStr = ', logStr, ', pyHSTtuple = ', pyHSTtuple
        if  hrsec != None:
            self.hrsec  = hrsec
            # pyHSTtuple is HST (not UT)
            self.pyHSTtuple  = time.localtime( hrsec )
        elif  logStr != 'None' and logStr != None:
            self.pyHSTtuple[0] = int( logStr[0:4] )
            self.pyHSTtuple[1] = int( logStr[4:6] ) 
            self.pyHSTtuple[2] = int( logStr[6:8] )
            self.pyHSTtuple[3] = int( logStr[8:10] )
            self.pyHSTtuple[4] = int( logStr[10:12] )
            self.pyHSTtuple[5] = int( logStr[12:14] )
            self.pyHSTtuple[6] = int( logStr[14:15] )
            self.pyHSTtuple[7] = int( logStr[15:18] )
            self.pyHSTtuple[8] = -1
        elif  pyHSTtuple != None:
            self.pyHSTtuple  = pyHSTtuple
            # only valid if pyHSTtuple is actually local time (HST)
            self.hrsec  = time.mktime( pyHSTtuple )
        else:
            self.pyHSTtuple  = None
            self.hrsec    = None
        #? print 'pyHSTtuple = ', self.pyHSTtuple

    def setValueHSTtuple(self, pyHSTtuple=None):
        """Set value."""
        self.pyHSTtuple  = pyHSTtuple
        self.hrsec  = time.mktime( pyHSTtuple )
        #? print 'pyHSTtuple = ', self.pyHSTtuple

    def value(self):
        """Return value is seconds since epoch."""
        return self.hrsec

    def value_unixTime(self):
        """Return value is integer seconds since epoch."""
        if  self.hrsec == None:
            return None
        elif  self.hrsec == UNDEF:
            return UNDEF
        return int( self.hrsec )

    def value_HSTtuple(self):
        """Return value is a Python localtime tuple."""
        if  self.hrsec == None:
            return None
        elif  self.hrsec == UNDEF:
            return UNDEF
        return self.pyHSTtuple

    def value_UTtuple(self):
        """Return value is a Python gmtime tuple."""
        if  self.hrsec == None:
            return None
        elif  self.hrsec == UNDEF:
            return UNDEF
        return time.gmtime( self.hrsec )

    def value_LSTtuple(self):
        """Return value is a Python gmtime tuple representing local 
        sidereal time."""
        if  self.hrsec == None:
            return None
        elif  self.hrsec == UNDEF:
            return UNDEF
        return time.gmtime( self.value_LSTsec() )

    def value_LSTsec(self):
        if  self.hrsec == None:
            return None
        elif  self.hrsec == UNDEF:
            return UNDEF
        # Calculate LST from gmtime, etc.
        now = time.gmtime( self.hrsec )
        ut = now[3] * 3600.0 + now[4] * 60.0 + now[5]
        dd = now[2] + (ut / 86400.0)
        jd = Util.calcJulianDays(now[0], now[1], dd)
        tu = (jd - 2451545.0) / 36525.0
        gst = Util.calcGST(tu, ut)
        lst = gst - 37315.3333; # (155 28' 50" ):(155*3600+28*60+50)/15
        if lst < 0.0:
            lst = lst + 86400.0;
        return lst

    def format(self):
        """Return default-formatted string."""
        if  self.hrsec == None:
            return '<No Data>'
        elif  self.hrsec == UNDEF:
            return '<Undefined>'
        format = '%H:%M:%S (%b %d)'
        return time.strftime( format, self.pyHSTtuple )

    def format_DateTimeTag(self):
        """Return date/time formatted string."""
        if  self.hrsec == None:
            return '<No Data>'
        elif  self.hrsec == UNDEF:
            return '<Undefined>'
        format = '%Y-%m-%d %H:%M:%S'
        return time.strftime( format, self.pyHSTtuple )

    def format_HST(self):
        """Return HST as default-formatted string."""
        if  self.hrsec == None:
            return '<No Data>'
        elif  self.hrsec == UNDEF:
            return '<Undefined>'
        format = '%H:%M:%S (%b/%d)'
        return time.strftime( format, self.pyHSTtuple )

    def format_UT(self):
        """Return UT as default-formatted string."""
        if  self.hrsec == None:
            return '<No Data>'
        elif  self.hrsec == UNDEF:
            return '<Undefined>'
        format = '%H:%M:%S (%b/%d)'
        return time.strftime( format, time.gmtime( self.hrsec ) )

    def format_LST(self):
        """Return LST as default-formatted string."""
        if  self.hrsec == None:
            return '<No Data>'
        elif  self.hrsec == UNDEF:
            return '<Undefined>'
        format = '%H:%M:%S'
        return time.strftime( format, time.gmtime( self.value_LSTsec() ) )

    def format_HSTstrftime(self,format):
        """Return HST string formatted with time.strftime."""
        if  self.hrsec == None:
            return '<No Data>'
        elif  self.hrsec == UNDEF:
            return '<Undefined>'
        return time.strftime( format, self.pyHSTtuple )

    def format_UTstrftime(self,format):
        """Return UT string formatted with time.strftime."""
        if  self.hrsec == None:
            return '<No Data>'
        elif  self.hrsec == UNDEF:
            return '<Undefined>'
        return time.strftime( format, time.gmtime( self.hrsec ) )

    def format_LSTstrftime(self,format):
        """Return LST string formatted with time.strftime."""
        if  self.hrsec == None:
            return '<No Data>'
        elif  self.hrsec == UNDEF:
            return '<Undefined>'
        return time.strftime( format, time.gmtime( self.value_LSTsec() ) )

    def format_forLog(self):
        """Return string formatted for data logging."""
        if  self.hrsec == None:
            return '<No Data>'
        elif  self.hrsec == UNDEF:
            return 'UNDEF'
        # This is simply seconds since epoch as a formatted float
        return '%.2f' % self.hrsec

    def fromLogFmt(self,strVal): 
        """Set value from a data log string value."""
        if  strVal == 'None':
            self.hrsec  = None
        elif  strVal == 'UNDEF':
            self.hrsec = UNDEF
        else:
            try:
                self.hrsec  = float( strVal )
                self.pyHSTtuple  = time.localtime( self.hrsec )
            except Exception, value:
                self.hrsec  = None
                self.pyHSTtuple  = None
                exceptMsg = "Bad hrsec floating point format " + \
                                     "(%s) for alias %s, exception msg %s" % \
                                                     (strVal,self.key,`value`)
                TelStatLog.TelStatLog( DispTypeConvErr, 
                         'ERROR (DispTypes:UnixTimeDDT): ' + exceptMsg, True )
                raise  ConversionError, exceptMsg

    def formatForLog(self):
        """Return a data-log-formatted string."""
        #? print 'UnixTimeDDT.formatForLog, hrsec(%s) = ' % self.key, self.hrsec
        if  self.hrsec == None:
            return 'None'
        elif  self.hrsec == UNDEF:
            return 'UNDEF'
        else:
            return '%.4f' % self.hrsec


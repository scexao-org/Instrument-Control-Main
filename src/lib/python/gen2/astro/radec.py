# radec.py
#
# Takeshi Inagaki -- 2007-05
# Bruce Bon -- last edit 2007-09-18
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Apr 23 15:45:53 HST 2012
#]
#
# Algorithms for functions below taken from, among others:
#    /soss/SRC/product/OSST/OSST_Calc_ProbeOffset.d/OSST_Calc_ProbeOffset.c
#    /soss/SRC/product/OSST/OSST_calc_probe.d/OSST_calc_probe.c


import math
import types
import time

import subaru

degPerHMSHour = 15.0      #360/24
degPerHMSMin  = 0.25      #360.0/24/60
degPerHMSSec  = 1.0/240.0 #360.0/24/60/60

degPerDmsMin  = 1.0/60.0
degPerDmsSec  = 1.0/3600.0

HMSHourPerDeg = 1.0/15.0
HMSMinPerDeg  = 4.0
HMSSecPerDeg  = 240.0

class AstroError(Exception):
    pass

class AstroCalcError(Exception):
    pass

class AzElError(AstroCalcError):
    """Exception thrown when checking potential telescope movement if the
    azimuth or elevation exceeds the limits."""
    pass

def calSinCos(pa):
    """Parm pa is a number in units of degrees; return value is a tuple
       whose elements are the sin and cosine of pa."""
    
    s=c=math.radians(pa)
    # IS THIS ENOUGH PRECISION ??
    s='%.8f' % ( math.sin(s) )
    c='%.8f' % ( math.cos(c) )

    return (s,c)


def convertToFloat(ra, dec):
    """Parms ra and dec are lists or tuples, the elements of which are numbers.
       The ra elements are sign (+1 or -1), hours, minutes and seconds of right 
       ascension, and the dec elements are sign (+1 or -1), degrees, minutes 
       and seconds of declination.  The return value is a pair of floats that 
       encode seconds as units, minutes as hundreds and degrees/hours as 
       ten-thousands (herein known as 'funky SOSS format').  The declination 
       return value is signed by multiplying it by the input sign element."""
    
    fra  = ra[0]  * (ra[1]  * 10000.0 + ra[2]  * 100.0 + ra[3])
    fdec = dec[0] * (dec[1] * 10000.0 + dec[2] * 100.0 + dec[3])
            
    return (fra, fdec)


def deltaStars(az1, el1, az2, el2):
    """Parms are the azimuths and elevations of 2 stars in radians;
       result is the distance between the stars in arcseconds."""
    
    del1=math.pi/2.0 -el1
    del2=math.pi/2.0 -el2
    daz = az2-az1
    
    delta_radian = math.acos(math.cos(del1)*math.cos(del2) + \
                             math.sin(del1)*math.sin(del2)*math.cos(daz))
      
    # convert rad to deg then arcsec       
    return math.degrees(delta_radian)*3600.00

def offsetDegToHms(ra_off):
    """Used for relative RA values, such as probe offsets."""
    if ra_off < 0.0:
        sign = -1.0
    else:
        sign = 1.0
    ra = math.fabs(ra_off)
    rah   = ra/degPerHMSHour
    ramin = (ra % degPerHMSHour) * HMSMinPerDeg
    rasec = (ra % degPerHMSMin)  * HMSSecPerDeg
    return  (sign, int(rah), int(ramin), rasec)

def degToHms(ra):
    '''
    converts the ra (in degrees) to HMS three tuple.
    H and M are in integer and the S part is in float.
    '''
    assert (ra >= 0.0), AstroCalcError("RA (%f) is negative" % (ra))
    assert ra < 360.0, AstroCalcError("RA (%f) > 360.0" % (ra))
    rah   = ra/degPerHMSHour
    ramin = (ra % degPerHMSHour) * HMSMinPerDeg
    rasec = (ra % degPerHMSMin)  * HMSSecPerDeg
    return  (int(rah), int(ramin), rasec)

def raHmsToString(rah, ramin, rasec, format='%02d%02d%02d'):
    """Format RA hours, minutes, seconds into a string HHMMSS."""
    return  format % (rah, ramin, rasec)

def degToDmsForQdas(dec):

    """Convert the dec, in degrees, to an (sign,D,M,S) tuple.
       D and M are integer, and sign and S are float.

       this function is used by qdas_pixradec command only. 
       if degToDms is used to convert deg to dms, there is a case that a output value does not match with a expected value.  
    """

    assert dec <= 90, AstroCalcError("DEC (%f) > 90.0" % (dec))
    assert dec >= -90, AstroCalcError("DEC (%f) < -90.0" % (dec))

    if dec < 0.0:
        sign = -1.0
    else:
        sign = 1.0
    dec = math.fabs(dec)

    dec *= 360000.0
    ideg = int(round(dec))
  
    d = ideg / 360000
    m = (ideg % 360000) / 6000
    s = (ideg % 6000) / 100.0


    return (int(sign), int(d), int(m), s)

def raDegToString(ra_deg, format='%02d%02d%06.3f'):
    if ra_deg > 360.0:
        ra_deg = math.fmod(ra_deg, 360.0)
        
    ra_hour, ra_min, ra_sec = degToHms(ra_deg)
    return raHmsToString(ra_hour, ra_min, ra_sec, format=format)
    
def offsetRaDegToString(ra_deg, format='%s%02d%02d%06.3f'):
    if ra_deg > 360.0:
        ra_deg = math.fmod(ra_deg, 360.0)
        
    sign, ra_hour, ra_min, ra_sec = offsetDegToHms(ra_deg)
    if sign > 0:
        sign_sym = '+'
    else:
        sign_sym = '-'
    return format % (sign_sym, int(ra_hour), int(ra_min), ra_sec)
    
def degToDms(dec):
    """Convert the dec, in degrees, to an (sign,D,M,S) tuple.
       D and M are integer, and sign and S are float."""
   
    assert dec <= 90, AstroCalcError("DEC (%f) > 90.0" % (dec))
    assert dec >= -90, AstroCalcError("DEC (%f) < -90.0" % (dec))

    if dec < 0.0:
        sign = -1.0
    else:
        sign = 1.0
    dec = dec * sign

    # bug fixed    
    mnt, sec = divmod(dec*3600, 60)
    deg, mnt = divmod(mnt, 60)
    # this calculation with return values produces conversion problem.
    # e.g. dec +311600.00 -> 31.2666666667 degree  deg=31 min=15 sec=60 instead deg=31 min=16 sec=0.0
  
    #mnt = (dec % 1.0) * 60.0
    #sec = (dec % (1.0/60.0)) * 3600.0

    return (int(sign), int(deg), int(mnt), sec)

def decDmsToString(sign, decd, decmin, decsec, format='%s%02d%02d%02d'):
    """Format dec sign, degrees, minutes, seconds into a string +DDMMSS."""
    if sign > 0:
        sign_sym = '+'
    else:
        sign_sym = '-'
    return format % (sign_sym, int(decd), int(decmin), decsec)

def decDegToString(dec_deg, format='%s%02d%02d%05.2f'):
    dec_sign, dec_degree, dec_min, dec_sec = degToDms(dec_deg)
    return decDmsToString(dec_sign, dec_degree, dec_min, dec_sec,
                          format=format)
    
# ra hms as string to ra degree
def hmsStrToDeg(ra):
    """Convert a string representation of RA into a float in degrees."""
    hour, min, sec = ra.split(':')
    ra_deg = hmsToDeg(int(hour), int(min), float(sec))
    return ra_deg
    
# dec dms to dec degree
def dmsStrToDeg(dec):
    """Convert a string representation of DEC into a float in degrees."""
    sign_deg, min, sec = dec.split(':')
    sign = sign_deg[0:1]
    deg = sign_deg[1:] 
    dec_deg = decTimeToDeg(sign, int(deg), int(min), float(sec))
    return dec_deg

def hmsToHour(s, h, m, sec):
    """Convert signed RA/HA hours, minutes, seconds to floating point hours."""
    return s * (h + m/60.0 + sec/3600.0)

def hmsToDeg(h, m, s):
    """Convert RA hours, minutes, seconds into an angle in degrees."""
    return h * degPerHMSHour + m * degPerHMSMin + s * degPerHMSSec

def dmsToDeg(sign, deg, min, sec):
    """Convert dec sign, degrees, minutes, seconds into a signed angle in degrees."""
    return sign * (deg + min * degPerDmsMin + sec * degPerDmsSec)

def hmsToRad(h,m,s):
    """Convert RA hours, minutes, seconds into an angle in radians."""
    ra_deg = hmsToDeg(h, m, s)
    return math.radians(ra_deg)

def dmsToRad(sign_sym, deg, min, sec):
    """Convert dec sign, degrees, minutes, seconds into a signed angle in radians.
       sign_sym may represent negative as either '-' or numeric -1."""
    dec_deg = decTimeToDeg(sign_sym, deg, min, sec)
    return math.radians(dec_deg)

def decTimeToDeg(sign_sym, deg, min, sec):
    """Convert dec sign, degrees, minutes, seconds into a signed angle in degrees.
       sign_sym may represent negative as either '-' or numeric -1."""
    if sign_sym == -1 or sign_sym == '-':
        sign = -1
    else:
        sign = 1
    return dmsToDeg(sign, deg, min, sec)

def funkyHMStoHours(HMS):
    """Convert funky HMS format, possibly signed, into hours.
       Both input (HMS) and return values are floating point."""
    s,h,m,sec = parseDMS(HMS)
    return hmsToHour(s, h, m, sec) 

def funkyHMStoDeg(HMS):
    (hrs, min, sec) = parseHMS(HMS)
    return hmsToDeg(hrs, min, sec)

def funkyDMStoDeg(DMS):
    """Convert funky DMS format, possibly signed, into degrees.
       Both input (DMS) and return values are floating point."""
    s,h,m,sec = parseDMS(DMS)
    return hmsToHour(s, h, m, sec) 

def arcsecToDeg(arcsec):
    """Convert numeric arcseconds (aka DMS seconds) to degrees of arc."""
    return arcsec * degPerDmsSec

def ra_max_min(ra_center, dec_center, ra_range):
    """Parms are a location in RA and dec, and an RA delta, all in units 
       of radians; the RA delta is an angular distance, which must be adjusted
       to account for the fact that a given difference is RA is a smaller
       angular distance at a higher declination (i.e. distance from equator). 
       Return is a pair of RA values in radians corresponding to the minimum
       and maximum RA in the desired range."""
    ra_range = ra_range/math.cos(math.radians(dec_center))
    return (ra_center - ra_range, ra_center + ra_range)

def dec_max_min(dec_center, dec_range):
    """Parms are a location in dec, and a dec delta, all in units of radians. 
       Return is a pair of dec values in radians corresponding to the minimum
       and maximum dec in the desired range."""
    return (dec_center - dec_range, dec_center + dec_range)    

# Returns tuple of tuples of ra_min and ra_max
def get_ra_range(ra_min, ra_max):
    """Parms are a minimum and a maximum value of RA, in units of degrees.
       Result is a tuple of tuples that might be used for searching a star
       catalog for stars between ra_min and ra_max.  Each inner tuple is
       an ra_min,ra_max pair, where both are between 0 and 360 degrees,
       ra_min<ra_max in each pair, and ranges that include 0/360 degrees
       are covered by 2 separate tuples."""
    # First convert RA (degree) to positive between 0 and 360
    ra_min = ra_min % 360.0
    ra_max = ra_max % 360.0
    if ra_min == ra_max:
        return ((0.0, 360.0),)
    elif ra_min > ra_max:
        return ((ra_min, 360.0), (0.0, ra_max),)
    else:
        return ((ra_min, ra_max),)

def get_dec_range(dec_min,
                  dec_max):
    """Parms are a minimum and a maximum value of declination, in degrees.
       Result is a tuple that might be used for searching a star catalog 
       for stars between dec_min and dec_max.  The result is a dec_min,dec_max 
       pair, where both are between -90 and +90 degrees, and dec_min<dec_max."""
    # not a good logic but we need to be compatible with the old software
    if dec_max > 89.8:
       return (min(dec_min, 180.0 - dec_max), 90.0)

    if dec_min < -89.8:
       return (-90.0, max(dec_max, -(180.0 + dec_min)))

    return (dec_min, dec_max)

def get_ra_dec_range(ra_min,  ra_max,
                     dec_min, dec_max):
    """Combine get_ra_range() and get_dec_range() -- return a 2-tuple,
       the first element of which is the tuple of tuples returned by
       get_ra_range(), and the second element of which is the tuple
       returned by get_dec_range()."""
    if dec_max > 89.8 or dec_min < -89.8:
        ra = ((0, 360.0),)
    else:
        ra = get_ra_range(ra_min, ra_max)

    dec = get_dec_range(dec_min, dec_max)
    return (ra, dec)

# Another method to find RA range using 
# Spherical Trigonometry
def get_ra_dec_range2(ra_center,  delta_ra,
                      dec_center, delta_dec):
    """A more sophisticated combination of get_ra_range() and get_dec_range().
       Parms are a location in RA and dec, and delta's in RA and dec, in 
       units of radians.  Parm delta_ra is the FOV in the ra direction, and 
       delta_ra is the FOV in the dec direction.  Returns a tuple in the 
       same format as that returned by get_ra_dec_range()."""
    (dec_min, dec_max) = get_dec_range(dec_center - delta_dec, 
                                       dec_center + delta_dec)
    if abs(dec_max) < abs(dec_min):
        dec =  dec_min
    else:
        dec = dec_max

    cos_dec_square = math.cos(math.radians(dec))**2.0
    cos_delta_ra   = math.cos(math.radians(delta_ra))
    # modified shperical trig. formula to minimize 
    # rounding error.
    cos_real_delta_ra = cos_delta_ra/cos_dec_square - 1.0/cos_dec_square + 1.0
    # if the result is more than 1.0, truncate the result to 1.0.
    if abs(cos_real_delta_ra) > 1:
        cos_real_delta_ra = cos_real_delta_ra/abs(cos_real_delta_ra)
    real_ra_delta = math.degrees(math.acos(cos_real_delta_ra))
    real_ra_range = get_ra_range(ra_center - real_ra_delta, 
                                 ra_center + real_ra_delta)
    return (real_ra_range, (dec_min, dec_max))

def getRaAngle(dec, apparent_ra):
    '''
    returns ra angle at dec for an apparent
    angle along the ra direction. 
    units for this function is all in degrees.
    '''
    #if abs(dec) - 90.0 < 0.00001:
    #    return 0.0
    return apparent_ra/math.cos(math.radians(dec))

def getApprentRaAngle(dec, ra_angle):
    '''
    returns apparent angle along the ra direction
    from the ra angle distance and dec 
    units for this function is all in degrees.
    '''
    return ra_angle * math.cos(math.radians(dec))

def convertToHmsDms(ra, dec, logger=None):
    """Encode angular arcsecond values (see convertToFloat()),
       and return a pair of floats in 'funky SOSS format'."""

    # make sure that the input values are numeric
    if logger is not None:
        logger.debug('convertHmsDms ra<%f>' %(ra)) 
    ra  = float(ra)/15.0
    dec = float(dec)

    if logger is not None:
        logger.debug('convertHmsDms ra<%f> = float(ra) / 15.0 ' %(ra)) 
    # compute RA components
    if  ra < 0.0:
        rsign = -1.0
        ra   *= -1.0
    else:
        rsign = +1.0
    rh = ra // 3600
    if logger is not None:
        logger.debug('convertHmsDms rh<%f> = ra<%f> // 3600 ' %(rh, ra)) 
    ra = ra - rh*3600.0
    if logger is not None:
        logger.debug('convertHmsDms ra<%f> = ra - rh<%f>*3600.0 ' %(ra, rh)) 
        
    
    rm = ra // 60
    if logger is not None:
        logger.debug('convertHmsDms rm<%f> = ra<%f> // 60 ' %(rm, ra)) 
    
    
    rs = ra - rm*60.0
    if logger is not None:
        logger.debug('convertHmsDms rs<%f> = ra<%f>  - rm<%f>*60.0 ' %(rs, ra, rm)) 

    # compute Dec components
    if  dec < 0.0:
        dsign = -1.0
        dec  *= -1.0
    else:
        dsign = +1.0
    dh  = dec // 3600
    dec = dec - dh*3600.0
    dm  = dec // 60
    ds  = dec - dm*60.0

    return convertToFloat( (rsign, rh,rm,rs), (dsign,dh,dm,ds) )

def parseHMS(ra_in):
    """   input HHMMSS.sss '''
       Decode an absolute RA value in 'funky SOSS format' (see convertToFloat()),
       and return a tuple containing hours, minutes and 
       seconds of RA."""
    # make sure that the (offset_)dec/(offset_)ra is numeric
    ra_in = float(ra_in)
    # then convert it into the formatted string
    input_str  = '%010.3f' % (ra_in)

    # break down the parts 
    return (int  (input_str[0:2]),
            int  (input_str[2:4]),                                                
            float(input_str[4:]))                                                

def parseDMS(dec_in):
    """Decode an angular value in 'funky SOSS format' (see convertToFloat()),
       and return a tuple containing sign (+1 or -1), degrees, minutes and 
       seconds of arc."""

    # make sure that the input value is numeric
    dec_in = float(dec_in)
    
    # then convert it into the formatted string
    input_str  = '%+011.3f' % (dec_in)

    # break down the parts 
    if input_str[0] == '-':
        input_sign = -1
    else:
        input_sign = 1

    return (input_sign,
            int  (input_str[1:3]),
            int  (input_str[3:5]),                                                
            float(input_str[5:]))                                                
    
def relHMStoArcsec(input):
    """   input +-HHMMSS.sss
       Decode a signed RA value in 'funky SOSS format' (see convertToFloat()),
       and return seconds of arc as a float."""
    sign, h, m, s=parseRelHMS(input)
    #? print ">>>>> s,h,m,s = ", (sign,h,m,s)
    return sign * (h*3600.0 + m*60.0 + s) * 15.0

def HMStoArcsec(input):
    """   input HHMMSS.sss
       Decode an RA value in 'funky SOSS format' (see convertToFloat()),
       and return seconds of arc as a float."""
    h, m, s=parseHMS(input)
    return(h*3600.0 + m*60.0 + s) * 15.0
    
def DMStoArcsec(input):
    """   input +-DDMMSS.sss
       Decode an angular value in 'funky SOSS format' (see convertToFloat()),
       and return seconds of arc as a float."""
    sign, d, m, s=parseDMS(input)
    return sign * (d*3600.0 + m*60.0 + s)
    
def parseRelHMS(input):
    """   input +-HHMMSS.sss '''
       Decode an RA value in 'funky SOSS format' (see convertToFloat()),
       and return a tuple containing sign (+1 or -1), hours, minutes and 
       seconds of arc.  This is called 'relative RA' or 'RelHMS' because 
       it is signed; the encoding is the same as for angles."""
    return parseDMS(input)

def calc_ra_dec_with_offset(ra, 
                            dec, 
                            offset_ra, 
                            offset_dec):
    ra  = parseHMS(ra)
    dec = parseDMS(dec)

    offset_ra_deg  = arcsecToDeg(offset_ra)
    offset_dec_deg = arcsecToDeg(offset_dec)
    
    dec_deg = dmsToDeg(dec[0],
                       dec[1],
                       dec[2],                                                
                       dec[3])                                                
    ra_deg = hmsToDeg( ra[0],
                       ra[1],
                       ra[2])
    target_ra_deg  = ra_deg + getRaAngle(dec_deg, offset_ra_deg)
    # normalize the ra angle
    target_ra_deg  = target_ra_deg % 360.0

    
    target_dec_deg = offset_dec_deg + dec_deg
    # normalize the dec angle
    if target_dec_deg > 90.0 or target_dec_deg < -90.0:
        if target_dec_deg > 90.0:
            ref_deg = 90.0
        elif target_dec_deg < -90.0:
            ref_deg = -90.0

        diff_deg = target_dec_deg - ref_deg 
        target_dec_deg = ref_deg - diff_deg
    
    # finally convert to the hms and dms notation.  
    target_ra  = degToHms(target_ra_deg)
    target_dec = degToDms(target_dec_deg)

    return (target_ra,  target_dec)

def calc_apparent_angle_distance(dec, real_ra_distance):
    result_t = parseDMS(real_ra_distance)
    result = result_t[0] * (result_t[1] * 10000.0 + result_t[2] * 100.0 + result_t[3])
    return math.cos(dec) * result * 3600.0



_stMapping = {
    'cs'          : 0,
    'cs_opt'      : 0,
    'cs_ir'       : 1,
    'ns_opt'      : 2,
    'ns_ir'       : 4,
    'ns_ir_optm2' : 7,
    'p_opt'       : 6,
    'p_ir'        : 6
    }

def _focusCaseId( f_select, imgrot_flag ):
    """Derive integer case ID, to be used in SOSS-compatible functions,
       calc_ProbeOffSet and Ag_Getoffset."""
    if  type(f_select) != types.StringType or \
        f_select.lower() not in _stMapping.keys():
        # ERROR -- can't determine focus!
        return '_focusCaseId: illegal f_select value %s' % `f_select`
    st = _stMapping[ f_select.lower() ]
    if  st == 2 or st == 4 or st == 7:
        if  imgrot_flag != 0 and imgrot_flag != 1:
            # ERROR -- can't determine rotator in or out
            return '_focusCaseId: illegal imgrot_flag value %s' % `imgrot_flag`
        elif  imgrot_flag == 1:
            st += 1
    return st

#***********************************************
#* Offset on the guider (gdofst.c)             *
#* Copy-right reserved by Wataru Tanaka (1998) *
#***********************************************
def _gdofst( st, p, th, da, dd, a0, h0, sv=False, logger=None):
    """This function is copied almost directly from the gdofst function 
       in OSST_Calc_ProbeOffset.c or OSST_AG_GetOffset.c -- gdofst is
       identical in both programs.  The input arguments have the same names 
       and interpretations.
       Input arguments:
          st: focal position flag;  
              st=0:Cas(opt),        st=1:Cas(IR)
              st=2:Nas(opt,non-ImR),st=3:Nas(opt,ImR)
              st=4:Nas(IR, non-ImR),st=5:Nas(IR, ImR)
              st=6:prime (now unusable ??)
              st=7:Nas(IR, with NsOpt M2, non-ImR)
              st=8:Nas(IR, with NsOpt M2, ImR)
          p : position angle of the rotator (deg)
          th: position angle of the guider (deg)
          da: offset angle distance toward the right ascension (arcsec)
          dd: offset angle distance toward the declination (arcsec)
          a0: azimuth of the telescope (deg)
          h0: altitude of the telescope (deg)
          
          added arg 'guide' to distinguish between 'AG' guide or 'SV' guide offset.
                default is None that also imply the 'AG'. 
       Output is a 2-tuple (x,y) where:
          x is offset x on the CCD (pix)
          y is offset y on the CCD (pix)
    """

    #? print "_gdofst ( st, p, th, da, dd, a0, h0) = ",( st, p, th, da, dd, a0, h0)
    #rad=math.pi/180.0
    
    

    #pl=19.8285; pl=pl*rad;          # latitude
    pl = math.radians(19.8285) # latitude radians
    #p=p*rad; h0=h0*rad; a0=a0*rad;
    p = math.radians(p); h0 = math.radians(h0); a0 = math.radians(a0)
    
    pa = math.atan2( math.cos(pl)*math.sin(a0),
                     math.sin(pl)*math.cos(h0) + \
                        math.cos(pl)*math.sin(h0)*math.cos(a0))

    if logger is not None:
        logger.debug("radec.py def _gdofst p<%f> h0<%f> a0<%f> pa<%f> da<%f> dd<%f> " %(p,h0, a0, pa, da, dd))

    if  st == 0:
        # Cs_Opt
        fl=100029.16            # focal length 2000/05/23
        ep=95.492               # rotation angle of the CCD
        
        if sv:
            sf=0.015/0.2475
            sg=-1.0  #sg 1.0 -> -1.0 2003/07/02 Refer case 3 */
        else:
            sf=0.015/0.3355         # scale factor 0.3355 Calc 2000/05/25
            sg=1.0        
        
                                # ep 98.08 -> 95.492 2000/02/05
        
        #pa=p-pa+(th+ep)*rad 
        pa = p-pa+math.radians(th+ep)
        if logger is not None:
            logger.debug("radec.py def _gdofst  case is CS_OPT pa<%f>" %pa)
        

    elif  st==1:
        # Cs_IR
        fl=100022.75            # focal length 2000/05/23
        sf=0.015/0.3355         # scale factor 0.3355 Calc 2000/05/25 >
        ep=95.492               # rotation angle of the CCD
                                # ep 98.08 -> 95.492 2000/02/05
        sg=1.0
        
        pa = p-pa+math.radians(th+ep)
        if logger is not None:
            logger.debug("radec.py def _gdofst  case is CS_IR pa<%f>" %pa)
         
    elif  st==2:

        # Ns_Opt w/o ImgRot
        fl=102264.94            # focas length 2000/05/23
        
        if sv:
            sf=0.015/0.2375
            ep=122.88 
            sg=1.0
        else:
            sf=0.015/0.335          # scale factor 2000/05/23
            ep=-5.75                # rotation angle of the CCD
                                    # ep 5.50 -> -5.50 2001/01/16
                                    # ep -5.50-> -5.75 2001/01/29
            sg=-1.0 
 
        pa = -pa+h0-math.radians(-th+ep)
        if logger is not None:
            logger.debug("radec.py def _gdofst  case is Ns_Opt w/o ImgRot pa<%f>" %pa)
        
                                
    elif  st==3:
        # Ns_Opt w ImgRot
        fl=104227.61            # focas length 2000/05/23
        
        if sv:
            sf=0.015/0.2375
            ep=122.83  #        /* Calculated on 2003/07/02 */
            sg=-1.0     #    /* sg 1.0 -> -1.0 2003/07/02 */
        else:
            sf=0.015/0.335          # scale factor 2000/05/23
            ep=-5.75                # rotation angle of the CCD
                                # ep 5.50 -> -5.50 2000/07/01
                                # ep -5.50-> -5.75 2001/01/29
            sg=1.0 
        #pa=2.0*p-pa-h0+(-th+ep)*rad  # th -> -th 2000/07/01
        
        pa = 2.0*p-pa-h0+math.radians(-th+ep)
        if logger is not None:
            logger.debug("radec.py def _gdofst  case is Ns_Opt w ImgRot pa<%f>" %pa)
            

    elif  st==4:
        # Ns_IR w/o ImgRot
        fl=108536.05            # focas length 2000/05/23
        sf=0.015/0.334          # scale factor 2000/05/23
        ep=-5.50                # rotation angle of the CCD
                                # ep 5.50 -> -5.50 2001/01/16
        sg=-1.0 
        #pa=-pa-h0-(-th+ep)*rad  # Org: p-pa-h0+(th+ep)*rad
                                # 2001/01/29 not tested yet
        #pa = -pa-h0-math.radians(-th+ep)
        pa = -pa-h0-math.radians(-th+ep)
        if logger is not None:
            logger.debug("radec.py def _gdofst  case is Ns_IR w/o ImgRot pa<%f>" %pa)
            
                               

# 2001/07/29 added by George Kosugi
    elif  st==7:
        # Ns_IR with Ns_Opt M2 w/o ImgRot
        fl=102264.94            # Ns_Opt focas length 2000/05/23
        sf=0.015/0.334          # scale factor 2000/05/23
        ep=-5.50                # rotation angle of the CCD
                                # ep 5.50 -> -5.50 2001/01/16
        sg=-1.0 
        #pa=-pa-h0-(-th+ep)*rad  # Org: p-pa-h0+(th+ep)*rad
                                # 2001/01/29 not tested yet
        pa = -pa-h0-math.radians(-th+ep)
        if logger is not None:
            logger.debug("radec.py def _gdofst  case is Ns_IR with Ns_Opt M2 w/o ImgRot pa<%f>" %pa)
                               

    elif  st==5:
        # Ns_IR w ImgRot
        fl=110629.08            # focas length 2000/05/23
        sf=0.015/0.334          # scale factor 2000/05/23
        ep=-5.50                # rotation angle of the CCD
                                # ep 5.50 -> -5.50 2000/12/18
        sg=1.0 
        #pa=2.0*p-pa+h0+(-th+ep)*rad  # -2.0*h0 ->  h0 2000/05/25
                                     #      th -> -th 2000/05/25
        pa = 2.0*p-pa+h0+math.radians(-th+ep)                            
        if logger is not None:
            logger.debug("radec.py def _gdofst  case is Ns_IR with ImgRot pa<%f>" %pa)

# 2001/07/29 added by George Kosugi
    elif  st==8:
        # Ns_IR with Ns_Opt M2 w ImgRot
        fl=104227.61            # Ns_Opt focas length 2000/05/23
        sf=0.015/0.334          # scale factor 2000/05/23
        ep=-5.50                # rotation angle of the CCD
                                # ep 5.50 -> -5.50 2000/12/18
        sg=1.0 
        #pa=2.0*p-pa+h0+(-th+ep)*rad  # -2.0*h0 ->  h0 2000/05/25
                                     #      th -> -th 2000/05/25
        pa = 2.0*p-pa+h0+math.radians(-th+ep)
        if logger is not None:
            logger.debug("radec.py def _gdofst  case is Ns_IR with Ns_Opt M2 w ImgRot pa<%f>" %pa)                            

    elif  st==6:
        # PrimeFocus
        fl=15320.21             # focas length 2000/05/23
        sf=0.015/2.15           # scale factor 2000/05/23
        ep=95.50                # rotation angle of the CCD
                                # ep 5.50 -> 95.50 2002/11/28
        sg=1.0                  # sg -1.0 -> 1.0 2002/11/28
        #pa=p-pa+(th+ep)*rad     # tested on 2002/11/28
        pa = p-pa+math.radians(-th+ep)
        if logger is not None:
            logger.debug("radec.py def _gdofst  case is PrimeFocus pa<%f>" %pa)
 

    # Modified +dd -> -dd
    x = ( sg * math.radians(fl) * (-da*math.cos(pa) - dd*math.sin(pa)) ) / (sf * 3600.0)
    y = ( math.radians(-fl) * ( da*math.sin(pa) - dd*math.cos(pa) ) ) /  (sf * 3600.0)
    
    if logger is not None:
        logger.debug("radec.py def _gdofst  x<%f> y<%f>" %(x,y))
    
    #? print "_gdofst (x,y) = ",(x,y)
    return (x,y)

# Constants needed by _AGGO_CheckInt and calc_AgGetoffset
CCD_X_MIN = 0
CCD_Y_MIN = 0
CCD_X_MAX = 511
CCD_Y_MAX = 511

def _AGGO_CheckInt(ccd_range):
    """Check to make sure provided coordinates are within CCD ranges."""
    ret = 0

    #? print "n_x1, n_y1, n_x2, n_y2 = ",(n_x1, n_y1, n_x2, n_y2)
    # x1
    if  CCD_X_MIN > ccd_range[0]:
        ccd_range[0]  = CCD_X_MIN
        ret = 1
    elif  CCD_X_MAX < ccd_range[0]:
        ccd_range[0]  = CCD_X_MAX
        ret = 1
    
    # x2    
    if  CCD_X_MIN > ccd_range[2]:
        ccd_range[2]  = CCD_X_MIN
        ret = 1
    elif  CCD_X_MAX < ccd_range[2]:
        ccd_range[2]  = CCD_X_MAX
        ret = 1
    
    # y1   
    if  CCD_Y_MIN > ccd_range[1]:
        ccd_range[1]  = CCD_Y_MIN
        ret = 1
    elif  CCD_Y_MAX < ccd_range[1]:
        ccd_range[1]  = CCD_Y_MAX
        ret = 1
    
    # y2
    if  CCD_Y_MIN > ccd_range[3]:
        ccd_range[3]  = CCD_Y_MIN
        ret = 1
    elif  CCD_Y_MAX < ccd_range[3]:
        ccd_range[3]  = CCD_Y_MAX
        ret = 1
       
    return ret


def calc_test(test):
    print test


def calc_Getoffset( f_select, az, el, ra_rel, dec_rel, origin_x1, origin_y1,
                      centroid_x1, centroid_y1, centroid_x2, centroid_y2,
                      readout_x1,  readout_y1, readout_x2,  readout_y2,
                      imgrot_flag, rotator, probet, sv=False, logger=None ):
    """This function is copied almost directly from the main body in
       OSST_AG_GetOffset.c and OSST_SV_GetOffset.c
       Outputs are as needed for SOSS AG/SV_GETOFFSET command."""

    if logger is not None:
        logger.debug('radec.py def calc_AgGetoffset called')

    # Derive st, for use with _gdofst()
    st = _focusCaseId( f_select, imgrot_flag )
    
    if logger is not None:
        logger.debug('radec.py def calc_AgGetoffset focousid<%s>' %(str(st)) )
        
    if  type(st) == types.StringType:
        return "calc_AgGetoffset:"+st, None, None, None, None, None, None, None, None, None

    # Compute x,y needed for offset transformation
    #             st, p,       th,     da,  dd,  a0, h0
    x,y = _gdofst(st, rotator, probet, ra_rel, dec_rel, az, el, sv, logger)
    
    if logger is not None:
        logger.debug('radec.py def calc_AgGetoffset  _gdofst x<%f> y<%f>' %(x,y) )

    # Compute the outputs, and check for errors
    err = 0
    norigin_x1 = origin_x1 + x
    norigin_y1 = origin_y1 + y
    if  (CCD_X_MIN>norigin_x1) or (CCD_X_MAX<norigin_x1) or \
        (CCD_Y_MIN>norigin_y1) or (CCD_Y_MAX<norigin_y1):
        err += 1
    if logger is not None:
        logger.debug('radec.py def calc_AgGetoffset  noorigin err<%d> x1<%s> y1<%s> ' %(err, str(norigin_x1), str(norigin_y1) ) ) 
        
        
    ncentroid_x1 = centroid_x1 + int(x)
    ncentroid_y1 = centroid_y1 + int(y)
    ncentroid_x2 = centroid_x2 + int(x)
    ncentroid_y2 = centroid_y2 + int(y)
    
    new_centroid=[ncentroid_x1, ncentroid_y1, ncentroid_x2, ncentroid_y2]
    err += _AGGO_CheckInt(new_centroid)
    ncentroid_x1=new_centroid[0]; ncentroid_y1=new_centroid[1]; ncentroid_x2=new_centroid[2]; ncentroid_y2=new_centroid[3];
    if logger is not None:
        logger.debug('radec.py def calc_AgGetoffset centroid err<%d> x1<%s> y1<%s> x2<%s> y2<%s>' %(err, str(ncentroid_x1), str(ncentroid_y1), str(ncentroid_x2), str(ncentroid_y2) ) )

    nreadout_x1 = readout_x1 + int(x)
    nreadout_y1 = readout_y1 + int(y)
    nreadout_x2 = readout_x2 + int(x)
    nreadout_y2 = readout_y2 + int(y)
    
    new_readout=[nreadout_x1, nreadout_y1, nreadout_x2, nreadout_y2]
    err += _AGGO_CheckInt(new_readout)
    nreadout_x1=new_readout[0]; nreadout_y1=new_readout[1]; nreadout_x2=new_readout[2]; nreadout_y2=new_readout[3];
    if logger is not None:
        logger.debug('radec.py def calc_AgGetoffset readout err<%d>, x1<%s> y1<%s> x2<%s> y2<%s>' %(err, str(nreadout_x1), str(nreadout_y1), str(nreadout_x2), str(nreadout_y2) ) )

    if  err == 3:
        err = "calc_AgGetoffset: Area exceeded the CCD area"
        if logger is not None:
            logger.error('radec.py def  Area exceeded the CCD area' %err)
        return err, None, None, None, None, None, None, None, None, None

    if logger is not None:
        logger.debug('radec.py def calc_AgGetoffset x new_origin<%f> y new_origin<%f>' %(norigin_x1, norigin_y1) )
        logger.debug('radec.py def calc_AgGetoffset x1 new_centroid<%f>  y1 new_centroid<%f>  x2 new_centroid<%f>  y2 new_centroid<%f>' %(ncentroid_x1, ncentroid_y1, ncentroid_x2, ncentroid_y2) )
        logger.debug('radec.py def calc_AgGetoffset x1 new_readout<%f>  y1 new_readout<%f>  x2 new_readout<%f>  y2 new_readout<%f>' %(nreadout_x1, nreadout_y1, nreadout_x2,nreadout_y2) )


    return norigin_x1,   norigin_y1, \
           ncentroid_x1, ncentroid_y1, ncentroid_x2, ncentroid_y2, \
           nreadout_x1,  nreadout_y1,  nreadout_x2,  nreadout_y2


def calc_ConvSecRaDec(rasec, decsec, rarel, decrel, rabase, decbase, logger=None):
    """All inputs must be arc seconds (not seconds of RA or HA).
       Outputs are as needed for SOSS CONVSECRADEC command:
        rasecout, decsecout are in arc seconds
        rarelout, decrelout are in funky SOSS numeric format
            (see parseHMS, parseDMS, etc.)    """

    # calculate decbase in rad and its cosine
     
    decbase_rad =math.radians( decbase/3600.0 )
    cosdecbase  =math.cos( decbase_rad )
    if logger is not None:
         logger.debug("radec.py def calc_ConvSecRaDec decbaserad<%f>  rad( decbase<%f> / 3600.0 )> " %(decbase_rad, decbase))
   
  
  
    if logger is not None:
        logger.debug("radec.py def calc_ConvSecRaDec  rarelout = rasec<%f> / cosdecbase<%f> " %(rasec, cosdecbase))
   
  
    # compute outputs, all still in arcsec
    rasecout  = rarel * cosdecbase
    decsecout = decrel
    rarelout  = rasec / cosdecbase
    decrelout = decsec            
    
    if logger is not None:
        logger.debug("radec.py def calc_ConvSecRaDec  rarelout<%f> decrelout<%f>" %(rarelout,  decrelout))
    #print rasecout, decsecout, rarelout, decrelout

    # convert rarelout, decrelout to funky SOSS format
    rarelout, decrelout = convertToHmsDms( rarelout, decrelout, logger=logger )
     
    if logger is not None:
        logger.debug("radec.py def calc_ConvSecRaDec  rasec<%f> decsec<%f> rarel<%s> decrel<%s>" %(rasecout, decsecout, str(rarelout), str(decrelout)))
    return (rasecout, decsecout, rarelout, decrelout)


def julianDate(gmtime=None):
    """Compute and return Julian Date in days (and fractions).
    If gmtime is furnished, use it; else compute JD from time.gmtime().
    See http://scienceworld.wolfram.com/astronomy/JulianDate.html,
        http://en.wikipedia.org/wiki/Julian_day
    """
    if  gmtime:
        tm = gmtime
    else:
        tm = time.gmtime()

    # UT as a fraction of a day
    utd = (tm.tm_hour*3600.0 + tm.tm_min*60.0 + tm.tm_sec)/86400.0
    yy = tm.tm_year
    mm = tm.tm_mon
    dd = tm.tm_mday
    t1 = 7 * (yy + ((mm+9) // 12)) // 4
    t2 = 275 * mm // 9
    jd = 367 * yy - t1 + t2 + dd + 1721013.5 + utd
    return jd


#****************************************
#* Precession                           *
#* Copy-right reserved by Wataru Tanaka *
#****************************************
def prcsn1(oe,ne,ra,de):
    """Copied from OSST_calc_probe.c .
       Compute precession(?):
          oe=old, ne=new epoch in JD
          Output ra, dec units : radians"""

    srad=math.pi/(180.0*3600.0);
    if  oe<=ne:
        p1=oe; p2=ne; sg=1
    else:
        p2=oe; p1=ne; sg=-1
    t0=(p1-2451545.0)/36525.0; t1=(p2-p1)/36525.0; t2=t1*t1; t3=t1*t2;
    x=(2306.2181+1.39656*t0-.000139*t0*t0)*t1+(.30188-.000344*t0)*t2+.017998*t3;
    z=x+(.7928+.00041*t0)*t2+.00205*t3;
    o=(2004.3109-.8533*t0-.000217*t0*t0)*t1-(.42665+.000217*t0)*t2-.041833*t3;
    x=sg*x*srad; z=sg*z*srad; o=sg*o*srad;
    so=math.sin(o); co=math.cos(o); sr=math.sin(ra+x); cr=math.cos(ra+x); 
    sd=math.sin(de); cd=math.cos(de);
    xx=co*cd*cr-so*sd; yy=cd*sr; zz=so*cd*cr+co*sd;
    pra=math.atan2(yy,xx)+z; pde=math.atan2(zz,math.sqrt(xx*xx+yy*yy))
    return pra, pde


#**********************************************************
#* Coordinates of the guider - equatorial to r,theta      *
#* Copy-right reserved by Wataru Tanaka (1998) (gdeqrt.c) *
#**********************************************************
def _gdeqrt(st,jd,eo,es,pr,r0,d0,rs,ds,cx,cy):
    """This function is copied almost directly from the gdofst function 
       in OSST_calc_probe.c .  The input arguments have the same names 
       and interpretations.
       Input arguments:
          st: focal position flag;
              st=0:Cas(opt),        st=1:Cas(IR)
              st=2:Nas(opt,non-ImR),st=3:Nas(opt,ImR)
              st=4:Nas(IR, non-ImR),st=5:Nas(IR, ImR)
              st=6:prime
              st=7:Nas(IR, with NsOpt M2, non-ImR)
              st=8:Nas(IR, with NsOpt M2, ImR)
          jd: Jurian date
          eo: equinox of the object (year)
          es: equinox of the guide star (year)
          pr: offset angle of the rotator (deg)
              offset angle of the image (deg)
                            in the cases of st=3 and 5
              pr=0.0 in the cases of st=2 and 4
          r0: right ascension of the object (hour)
          d0: declination of the object (deg)
          rs: right ascension of the guide star (hour)
          ds: declination of the guide star (deg)
          cx: offset x on the CCD (pix)
          cy: offset y on the CCD (pix)
          rd: radial position of the guider (mm)
              x position in the case of the prime (mm)
          th: position angle of the guider (deg)
              offset angle of the guider (deg)
                            in the cases of st=2 and 4
              y position in the case of the prime (mm)
       Output is a 2-tuple (rd,th) where:
          rd,th is probe x,y for prime focus
          rd,th is probe radius and theta for other foci
    """
    rad=math.pi/180.0;

    r0=r0*rad*15.0; d0=d0*rad; rs=rs*rad*15.0; ds=ds*rad;
    jo=(eo-2000.0)*365.25+2451545.0; js=(es-2000.0)*365.25+2451545.0;

    r0, d0 = prcsn1(jo,jd,r0,d0)
    rs, ds = prcsn1(js,jd,rs,ds)
    sts=math.sin(r0-rs); cts=math.cos(r0-rs)
    sdo=math.sin(d0); cdo=math.cos(d0); sds=math.sin(ds); cds=math.cos(ds)

    x=cds*sts; y=cdo*sds-sdo*cds*cts
    ps=math.atan2(x,y)/rad; 
    z=sdo*sds+cdo*cds*cts

    # focal length, scale factor, and rotation angle of CCD
    if  st == 0:
        # Cs_Opt
        fl=100029.16;           # focal length 2000/05/23
        sg=0.015/0.3355;        # scale factor 0.3355 Calc 2000/05/25
        ep=95.492;              # rotation angle of the CCD 2000/02/05
        r=fl*math.atan2(math.sqrt(x*x+y*y),z);
        x=sg*(cx*math.cos(ep*rad)+cy*math.sin(ep*rad))
        y=sg*(-cx*math.sin(ep*rad)+cy*math.cos(ep*rad));
        z=math.sqrt(r*r-x*x); rd=z+y; th=math.atan2(x,z)/rad-90.0;
        th=th-pr+ps;
    elif  st == 1:
        # Cs_IR
        fl=100022.75;           # focal length 2000/05/23
        sg=0.015/0.3355;        # scale factor 0.3355 Calc 2000/05/25
        ep=95.492;              # rotation angle of the CCD 2000/02/05
        r=fl*math.atan2(math.sqrt(x*x+y*y),z);
        x=sg*(cx*math.cos(ep*rad)+cy*math.sin(ep*rad)); 
        y=sg*(-cx*math.sin(ep*rad)+cy*math.cos(ep*rad));
        z=math.sqrt(r*r-x*x); rd=z+y; th=math.atan2(x,z)/rad-90.0;
        th=th-pr+ps;
    elif  st == 2:
        # Ns_Opt w/o ImgRot
        fl=102264.94;           # focal length 2000/05/23
        sg=0.015/0.335;         # scale factor 2000/05/23
        ep=-5.75;               # rotation angle of the CCD 2001/01/29
        r=fl*math.atan2(math.sqrt(x*x+y*y),z);
        x=sg*(cx*math.cos(ep*rad)+cy*math.sin(ep*rad));
        y=sg*(-cx*math.sin(ep*rad)+cy*math.cos(ep*rad));
        z=math.sqrt(r*r-x*x); rd=z+y; th=math.atan2(x,z)/rad-90.0;
        th=ps-th;               # 2001/04/11 by Geo  th=th-ps -> th=ps-th
    elif  st == 3:
        # Ns_Opt w ImgRot
        fl=104227.61;           # focal length 2000/05/23
        sg=0.015/0.335;         # scale factor 2000/05/23
        ep=-5.75;               # rotation angle of the CCD 2001/01/29
        r=fl*math.atan2(math.sqrt(x*x+y*y),z);
        x=sg*(cx*math.cos(ep*rad)+cy*math.sin(ep*rad))
        y=sg*(-cx*math.sin(ep*rad)+cy*math.cos(ep*rad));
        z=math.sqrt(r*r-x*x); rd=z+y; th=math.atan2(x,z)/rad-90.0;
        th=th+pr-ps;            # 2000/07/01 by Geo  th=th+pr+ps -> th=th+pr-ps
    elif  st == 4:
        # Ns_IR w/o ImgRot
        fl=108536.05;           # focal length 2000/05/23
        sg=0.015/0.334;         # scale factor 2000/05/23
        ep=5.5;                 # rotation angle of the CCD
        r=fl*math.atan2(math.sqrt(x*x+y*y),z);
        x=sg*(cx*math.cos(ep*rad)+cy*math.sin(ep*rad))
        y=sg*(-cx*math.sin(ep*rad)+cy*math.cos(ep*rad));
        z=math.sqrt(r*r-x*x); rd=z+y; th=math.atan2(x,z)/rad-90.0;
        th=th-ps;               # not tested yet as of 2001/07/31
    elif  st == 5:
        # Ns_IR w ImgRot
        fl=110629.08;           # focal length 2000/05/23
        sg=0.015/0.334;         # scale factor 2000/05/23
        ep=5.5;                 # rotation angle of the CCD
        r=fl*math.atan2(math.sqrt(x*x+y*y),z);
        x=sg*(cx*math.cos(ep*rad)+cy*math.sin(ep*rad))
        y=sg*(-cx*math.sin(ep*rad)+cy*math.cos(ep*rad));
        z=math.sqrt(r*r-x*x); rd=z+y; th=math.atan2(x,z)/rad-90.0;
        th=th+2.0*pr-ps;        # 2001/04/03 by Geo  th=th+pr+ps -> th=th+2.0*pr-ps
    elif  st == 7:
        # Ns_IR with Ns_Opt M2 w/o ImgRot
        fl=102264.94;           # focal length 2000/05/23
        sg=0.015/0.334;         # scale factor 2000/05/23
        ep=5.5;                 # rotation angle of the CCD
        r=fl*math.atan2(math.sqrt(x*x+y*y),z);
        x=sg*(cx*math.cos(ep*rad)+cy*math.sin(ep*rad))
        y=sg*(-cx*math.sin(ep*rad)+cy*math.cos(ep*rad));
        z=math.sqrt(r*r-x*x); rd=z+y; th=math.atan2(x,z)/rad-90.0;
        th=th-ps;               # not tested yet as of 2001/07/31
    elif  st == 8:
        # Ns_IR with Ns_Opt M2 w ImgRot
        fl=104227.61;           # focal length 2000/05/23
        sg=0.015/0.334;         # scale factor 2000/05/23
        ep=5.5;                 # rotation angle of the CCD
        r=fl*math.atan2(sqrt(x*x+y*y),z);
        x=sg*(cx*math.cos(ep*rad)+cy*math.sin(ep*rad)); 
        y=sg*(-cx*math.sin(ep*rad)+cy*math.cos(ep*rad));
        z=math.sqrt(r*r-x*x); rd=z+y; th=math.atan2(x,z)/rad-90.0;
        th=th+2.0*pr-ps;        # 2001/07/29 by Geo  th=th+pr+ps -> th=th+2.0*pr-ps
    elif  st == 6:
        # PrimeFocus
        fl=15320.21;            # focal length 2000/05/23
        sg=2.128;               # scale factor 2000/05/23
        ep=0.0;                 # rotation angle of the CCD
        r=fl*math.atan2(math.sqrt(x*x+y*y),z);
#        r=r-0.00000436049*r*r+0.0000023908295*r*r*r-0.000000004527512*r*r*r*r;*/
        r=r+1.8478e-6*math.pow(r,3.0)+3.25e-11*math.pow(r,5.0)-4.06e-15*math.pow(r,7.0)
        x=sg*(cx*math.cos(ep*rad)+cy*math.sin(ep*rad))
        y=sg*(-cx*math.sin(ep*rad)+cy*math.cos(ep*rad));
        th=(-pr+ps-90.0)*rad;
        rd=-r*math.cos(th)+y;   # 2000/08/04 by Geo  rd=r*cos(th)-y -> rd=-r*cos(th)+y
        th=-r*math.sin(th)-x;
    else:
        return "_gdeqrt: illegal value for st",None

    if  st!=6 and r*r<x*x:
        return "_gdeqrt: not PF and r*r<x*x",None
    if  st!=6:
        th=math.fmod(th,360.0)
    if  th>180.0:
        th=th-360.0
    if  th<-180.0:
        th=th+360.0

    return rd, th


CCD_CENTER_OFFSET_X = 0.0
CCD_CENTER_OFFSET_Y = 0.0
def calc_Calc_Probe( f_select, tel_ra, tel_dec, tel_equinox,
                     probe_ra, probe_dec, probe_equinox,
                     ag_pa, imgrot_flag ):
    """This function is copied almost directly from the main body in
       OSST_calc_probe.c .
       Outputs are as needed for the SOSS CALC_PROBE command:
            STATOBS.AGPF_X, STATOBS.AGPF_Y or STATOBS.AG_R, STATOBS.AG_THETA."""

    # Derive st, for use with _gdofst()
    st = _focusCaseId( f_select, imgrot_flag )
    if  type(st) == types.StringType:
        return "calc_Calc_Probe:"+st, None

    # Convert funky SOSS format into arc seconds
    rt = funkyHMStoHours(tel_ra)
    dt = funkyDMStoDeg(tel_dec)
    rs = funkyHMStoHours(probe_ra)
    ds = funkyDMStoDeg(probe_dec)
    cx = CCD_CENTER_OFFSET_X
    cy = CCD_CENTER_OFFSET_Y

    # Calculate JD, then LST (Local Sidereal Time)
    jd = julianDate()
    #??? I don't know if this is sufficient -- much complexity exists in the
    #??? calculation of jd by OSST_calc_probe.c -- seems to include LST

    rd,th = _gdeqrt(st, jd, tel_equinox, probe_equinox, 
                    ag_pa, rt, dt, rs, ds, cx, cy)
    if  type(rd) == types.StringType:
        return "calc_Calc_Probe:"+rd, None

    return rd,th


def calc_ProbeOffSet( az, el, src_x, src_y, dest_x, dest_y,
                      f_select, imgrot_flag, probet, rotator, logger=None ):
    """This function is copied almost directly from the main body in
       OSST_Calc_ProbeOffset.c .
       Outputs are as needed for SOSS CALC_PROBEOFFSET command:
          RASEC, DECSEC are both floating point values in arc seconds. """

    # Derive st, for use with _gdofst()
   
    st = _focusCaseId( f_select, imgrot_flag )
    
    if logger is not None:
        logger.debug('radec.py def calc_ProbeOffSet foucusid<%s>' %(str(st)))
    
    if  type(st) == types.StringType:
        if logger is not None:
            logger.error('radec.py def calc_ProbeOffSet foucusid<%s>' %(str(st)))
        return "calc_ProbeOffSet:"+st, None

    # Compute matrix elements for offset transformation
    #               st, p,       th,     da,  dd,  a0, h0
    x1,y1 = _gdofst(st, rotator, probet, 1.0, 0.0, az, el, sv=False, logger=logger)
    x2,y2 = _gdofst(st, rotator, probet, 0.0, 1.0, az, el, sv=False, logger=logger)
        
    if logger is not None:
        logger.debug('radec.py def calc_ProbeOffSet _gdofset x1<%f> y1<%f>' % (x1, y1)  )
        logger.debug('radec.py def calc_ProbeOffSet _gdofset x2<%f> y2<%f>' % (x2, y2)  )    
        logger.debug('radec.py def calc_ProbeOffSet x1*y2 - x2*y1 = <%f>' % (x1*y2 - x2*y1)  )
    
    if  (x1*y2 - x2*y1) == 0.0:
        da = 'calc_ProbeOffSet: matric inversion error (%f, %f, %f, %f)' % \
                (x1, y1, x2, y2)
        if logger is not None:
            logger.error('radec.py def calc_ProbeOffSet x1*y2 - x2*y1 == 0.0')       
        return da,None

    # Compute dest-src deltas and transform them to image plane (?)
    sdx = dest_x - src_x
    sdy = dest_y - src_y
    da = ( y2*sdx - x2*sdy)/(x1*y2 - x2*y1)
    dd = (-y1*sdx + x1*sdy)/(x1*y2 - x2*y1)
    if logger is not None:
        logger.debug('radec.py def calc_ProbeOffSet da<%f> dd<%f>' % (da, dd)  )

    return da,dd


def calc_RaDec(mode, rabase, decbase, raoffset, decoffset, logger=None, format_ra='%02d%02d%06.3f', format_dec='%s%02d%02d%05.2f' ):
    
    # convert ra(hms.sss) to ra(degree) 
    (ra_hour,ra_min,ra_sec)=parseHMS(rabase)
    ra_deg=hmsToDeg(ra_hour, ra_min, ra_sec)
    
    (ra_rel_sign, ra_rel_hour, ra_rel_min, ra_rel_sec)=parseRelHMS(raoffset)
    ra_rel_deg= ra_rel_sign *hmsToDeg(ra_rel_hour, ra_rel_min, ra_rel_sec)
    
    # convert dec(dms.ss) to dec(degree)
    (dec_sign, dec_degree, dec_min, dec_sec)=parseDMS(decbase)
    if logger is not None:
        logger.debug("def cacl_RaDec convert dec to deg  sign<%s> dec_degree<%s> min<%s> sec<%s>" %(str(dec_sign), str(dec_degree), str(dec_min), str(dec_sec)))

    dec_deg=dmsToDeg(dec_sign, dec_degree, dec_min, dec_sec)
       
    dec_rel_sign, dec_rel_degree, dec_rel_min, dec_rel_sec=parseDMS(decoffset)
    dec_rel_deg=dmsToDeg(dec_rel_sign, dec_rel_degree, dec_rel_min, dec_rel_sec)
  
    if logger is not None:
        logger.debug("def cacl_RaDec basera<%s> relra<%s> basedec<%s> reldec<%s>" %(str(ra_deg), str(ra_rel_deg), str(dec_deg), str(dec_rel_deg)))
  
  
    ra=( ra_deg + mode*ra_rel_deg )
    dec=dec_deg + (mode*dec_rel_deg)
    
    logger.debug("def cacl_RaDec ra<%s> dec<%s> " %(str(ra), str(dec)))
    
    if ra < 0.0:
        ra = 360 + math.fmod(ra, 360)
    else: # ra might be greater than 360. instead of having if comparison, just operate fmod for all ra
        ra = math.fmod(ra, 360.0)    
         
    if dec > 90.0:
        dec = 90 - math.fmod(dec, 90.0)
        ra = math.fmod( ra+ 180.0, 360.0)
    elif dec < -90:
        dec = -90 - math.fmod(dec, 90.0)
        ra = math.fmod( ra+ 180.0, 360.0)
    
    if logger is not None:
        logger.debug("def cacl_RaDec after adjustment ra<%s> dec<%s> " %(str(ra), str(dec)))
#    
    ra_hour, ra_min, ra_sec=degToHms(ra)
    dec_sign, dec_degree, dec_min, dec_sec=degToDms(dec)

    if dec_sign > 0: sign='+'
    else:            sign='-' 

    if logger is not None:
        logger.debug("def cacl_RaDec dec deg to dms sign<%s> deg<%d> min<%d> sec<%f>" %(sign, dec_degree, dec_min,dec_sec ))

        
    ra_output=format_ra %(ra_hour, ra_min, ra_sec)
    dec_output=format_dec %(sign, dec_degree, dec_min, dec_sec)
    
    if logger is not None:
        logger.debug("def cacl_RaDec ra(hms)<%s> dec(dms)<%s> " %(str(ra_output), str(dec_output)))
#    
    return (ra_output, dec_output )
#    


''' 
   distance on the sphere between two points in radias
   from ( az1, el1, az2, el2 )
   or two instances of same coordinate system 
   
   Copyright:: Copyright (C) 2004 Daigo Tomono <dtomono at freeshell.org>
   License::   GPL
   
   (unit rad)
'''
def delta_stars(ra0, dec0, ra1, dec1):
         
    dra, ddec0,ddec1=delta_ra_dec(ra0, dec0, ra1, dec1)
    
    #print 'dra%f  ddec0:%f  ddec1%f' %(dra, ddec0, ddec1)
     
    delta = math.acos(\
                  math.cos( ddec0 )*math.cos( ddec1 ) + \
                  math.sin( ddec0 )*math.sin( ddec1 )*math.cos( dra ) )  # distance
    
    #print 'd:%f' %(d)
    
    #if delta==0: return 'SAME_STAR'
    #else:    return d

    return delta
    

''' 
   calculate the delta ra/dec
   (unit rad)
'''
def delta_ra_dec(ra0, dec0, ra1, dec1):
    
    ddec0 = math.pi/2.0 - dec0
    ddec1 = math.pi/2.0 - dec1
    dra = ra1 - ra0

    return (dra, ddec0, ddec1)


''' 
   position angle (angle from north/zenith to east/right)
   of point1 seen from point0 in radius
   from ( az0, el0, az1, el1 )
   or two instances of same coordiante system 
   
   Copyright:: Copyright (C) 2004 Daigo Tomono <dtomono at freeshell.org>
   License::   GPL
 
   (unit rad)
'''
def pa_stars(ra0, dec0, ra1, dec1, delta=None ):
    
    # if star is the same postion as the zenith
    if math.fabs(dec0) == math.pi/2.0:
        ra0=ra1,ra1=ra0; 
        dec0=dec1,dec1=dec0;
        swap=1
    else: swap=0
    
    # if stars' delta is not figued out yet    
    if delta == None:
        delta=delta_stars(ra0, dec0, ra1, dec1)
        #print 'delta_stars called  d:%f' %(d)

    if delta==0:
        #? print 'pa stars d==0'     
        return  delta

   
    # find out ra/dec delta 
    dra, ddec0,ddec1=delta_ra_dec(ra0, dec0, ra1, dec1)
    #print 'dra, ddec0, ddec1', dra, ddec0, ddec1
    
    y=math.sin(ddec1)*math.sin(dra)/math.sin(delta)
    x=(math.cos(ddec1) - math.cos(ddec0)*math.cos(delta))/(math.sin(ddec0)*math.sin(delta))
    
    #print 'x:%f  y:%f' %(x, y) 
    pa = math.atan2( y, x )
    
    # turn around 180 degree
    if swap:
        #print 'swap'
        if pa < 0.0: pa+=math.pi    
        else:            pa-=math.pi
    
    #print 'pa %10.20f' %(pa)    
    return pa

    
def altaz2(th_rad, pl_rad, ra_rad, dec_rad, units='radians'):
    """
    Alt-azimuth
    Copyright:: Copyright reserved by Wataru Tanaka
    
    th_rad: local sidereal time, pl_rad: latitude
    ra_rad: right ascension, dec_rad: declination
    returns (altitude, azimuth) in radians 

    Translated from SOSS source code product/liboss_cal/OSScal_lockRADEC.c
    """
    th_rad = th_rad - ra_rad;
    sth = math.sin(th_rad)
    cth = math.cos(th_rad)
    sdc = math.sin(dec_rad)
    cdc = math.cos(dec_rad)
    spl = math.sin(pl_rad)
    cpl = math.cos(pl_rad)
    zz = spl * sdc + cpl * cdc * cth
    pha = math.atan2(zz, math.sqrt(1.0 - zz * zz))
    paz = math.atan2(cdc * sth, -cpl * sdc + spl * cdc * cth)
    if units == 'degrees':
        return (math.degrees(pha), math.degrees(paz))

    return (pha, paz)


def gst(tu, ut, fg, logger=None):
    """
    Greenwich Sidereal Time
    Copyright:: Copyright reserved by Wataru Tanaka

    tu: JC from 2000.0(UT1), ut: sec,
    fg=0:mean, fg=1:without short term, fg=2:with short term

    Translated from SOSS source code product/liboss_cal/OSScal_lockRADEC.c
    """
    rad = math.pi / 180.0;
    pgs = ( 24110.54841 + 8640184.812866 * tu +
            0.093104 * tu * tu - 0.0000062 * tu * tu * tu + ut )
    if logger:
        logger.debug("0. pgs=%f" % (pgs))
    if fg !=0:
        ps = ( -(17.200 + 0.017 * tu) * math.sin((125.045 - 1934.136 * tu) * rad) -
               1.319 * math.sin((200.93 + 72001.54 * tu) * rad) +
               0.206 * math.sin((250.1 - 3868.3 * tu) * rad) )
        if logger:
            logger.debug("1. ps=%f" % (ps))
        ps = ( ps + 0.143 * math.sin((357.5 + 35999.1 * tu) * rad) -
               0.052 * math.sin((198.5 + 108000.6 * tu) * rad) +
               0.022 * math.sin((203.4 + 36002.5 * tu) * rad) +
               0.013 * math.sin((75.9 + 73935.7 * tu) * rad) )
        if logger:
            logger.debug("2. ps=%f" % (ps))

        if fg == 2:
            ps = ( ps - 0.227 * math.sin((76.6 + 962535.8 * tu) * rad) +
                   0.071 * math.sin((135.0 + 477198.9 * tu) * rad) - 
                   0.039 * math.sin((311.6 + 964469.9 * tu) * rad) - 
                   0.030 * math.sin((211.6 + 1439734.6 * tu) * rad) - 
                   0.016 * math.sin((259.3 - 413335.4 * tu) * rad) +
                   0.012 * math.sin((301.7 + 485336.9 * tu) * rad) )
            if logger:
                logger.debug("3. ps=%f" % (ps))

        pgs = pgs + ps * math.cos((23.439 - 0.013 * tu) * rad)/15.0
        if logger:
            logger.debug("4. pgs=%f" % (pgs))

    pgs = pgs - 86400.0 * int(pgs / 86400.0)
    if logger:
        logger.debug("5. pgs=%f" % (pgs))
    if pgs < 0.0:
        pgs = pgs + 86400.0
    if logger:
        logger.debug("6. pgs=%f" % (pgs))

    return pgs


def odtjdt(yy, mm, dd, logger=None):
    """
    Convert from the date to Julian date
    Copyright:: Copyright reserved by Wataru Tanaka

    yy:year, mm:month dd:day with the fraction

    NOTE: use function julianDate() if possible instead of this....EJ

    Translated from SOSS source code product/liboss_cal/OSScal_lockRADEC.c
    """
    if logger:
        logger.debug("yy=%d mm=%d dd=%f" % (yy, mm, dd))
    mo = -((14 - mm) // 12)
    if logger:
        logger.debug("mo=%d" % (mo))
    pp = (1461 * (yy + 4800 + mo)) // 4 + (367 * (mm - 2 - mo * 12))//12
    if logger:
        logger.debug("pp=%d" % (pp))
    pjd = pp - (3 * ((yy + 4900 + mo) // 100)) // 4 - 32075.5 + dd
    return pjd


def radec_deg_abs_to_azel_deg(ra_deg, dec_deg, localtime_t=None,
                              ra_off_deg=None, dec_off_deg=None,
                              units='degrees', logger=None):
    """Convert 'funky' SOSS format RA/DEC to an (AZ, EL) tuple (in degrees).
    ra_deg: RA in 'funky' SOSS format (float, NOT char)
    dec_deg: DEC in 'funky' SOSS format (float, NOT char)
    localtime_t: seconds since the epoch in local time; if None
       use the current time

    Derived from SOSS source code product/liboss_cal/OSScal_lockRADEC.c
    """
    if not localtime_t:
        localtime_t = time.time()
    long_rad = math.radians(subaru.SUBARU_LONGITUDE_DEG)
    lat_rad = math.radians(subaru.SUBARU_LATITUDE_DEG)

    # Date to JD
    loctime = time.localtime(localtime_t)
    # partial seconds
    subsec = localtime_t - time.mktime(loctime)
    jd = odtjdt(loctime.tm_year, loctime.tm_mon, float(loctime.tm_mday))
    if logger:
        logger.debug("0. jd=%f" % (jd))

    ut = 3600.0*(loctime.tm_hour + 10) + 60.0*loctime.tm_min + loctime.tm_sec + subsec
    jd = jd + ut/86400.0
    tu = (jd - 2451545.0) / 36525.0
    if (ut >= 86400.0):
        ut -= 86400.0

    # calculate LST
    fg = 2
    gs = gst(tu, ut, fg)
    if logger:
        logger.debug("jd=%f ut=%f tu=%f gs=%f" % (jd, ut, tu, gs))
    #th_rad=rad*gs/240.0+long_rad
    th_rad = math.radians(gs)/240.0 + long_rad

    # Convert RA/DEC degrees to radians
    ra_rad = math.radians(ra_deg) * 15.0
    dec_rad = math.radians(dec_deg)

    # Apply RA/DEC offsets, if provided
    if ra_off_deg:
        ra_off_rad = math.radians(ra_off_deg) * 15.0
        ra_rad += ra_off_rad
    if dec_off_deg:
        dec_off_rad = math.radians(dec_off_deg)
        dec_rad += dec_off_rad
        
    if logger:
        logger.debug("th=%f lat=%f ra=%f dec=%f" % (th_rad, lat_rad, ra_rad, dec_rad))
    
    el, az = altaz2(th_rad, lat_rad, ra_rad, dec_rad, units=units)
    if logger:
        logger.debug("az=%f el=%f" % (az, el))

    return (az, el)


def calcAzEl(ra, dec, localtime_t=None, ra_off=None, dec_off=None,
              logger=None):
    """
    Convert RA/DEC in 'funky SOSS' degree format to degrees AZ/EL.
    localtime_t specifies the local time (in sec since the epoch).
    A tuple of (az, el) is returned.
    """

    ra_deg = funkyHMStoHours(ra)
    dec_deg = funkyDMStoDeg(dec)

    # Calculate offsets, if supplied
    if ra_off:
        ra_off = funkyHMStoHours(ra_off)
    if dec_off:
        dec_off = funkyDMStoDeg(dec_off)

    if logger:
        logger.debug("ra=%f dec=%f ra_off=%s dec_off=%s" % (
            ra_deg, dec_deg, ra_off, dec_off))
        
    return radec_deg_abs_to_azel_deg(ra_deg, dec_deg,
                                     localtime_t=localtime_t,
                                     ra_off_deg=ra_off,
                                     dec_off_deg=dec_off,
                                     logger=logger)

def checkAzEl(az, el, azmin=None, azmax=None, elmin=None, elmax=None):
    """Check the az/el against the maximum and minimum values.
    """
    if not azmin:
        azmin = subaru.CMD_TEL_MINAZ
    if not azmax:
        azmax = subaru.CMD_TEL_MAXAZ
    if not elmin:
        elmin = subaru.CMD_TEL_MINEL
    if not elmax:
        elmax = subaru.CMD_TEL_MAXEL

    assert el >= elmin, \
           AzElError("Target elevation is below threshold (%.2f < %.2f)" % (
        el, elmin))
    assert el <= elmax, \
           AzElError("Target elevation is above threshold (%.2f > %.2f)" % (
        el, elmax))
    assert az >= azmin, \
           AzElError("Target azimuth is below threshold (%.2f < %.2f)" % (
        az, azmin))
    assert az <= azmax, \
           AzElError("Target azimuth is above threshold (%.2f > %.2f)" % (
        az, azmax))


def SV_mm2RaDec(f_select, rotator, imgrot_flag, tel_ra, tel_dec,
                tel_equinox, svprobe_mm, logger=None):
    """
    SV_mm2RaDec

    George KOSUGI       Created  1998/12/16
                        Modified 2000/06/22
                        Modified 2000/06/23 Commented out prcsn
    Eric Jeschke        Modified 2011/04/11 Converted to python

    Input:
           f_select:       CS|CS_OPT / CS_IR / NS_IR / NS_OPT / P_IR / P_OPT
           rotator:        Rotation angle of Instrument/Image Rotator
                                  (degree:absolute? need checkup)
           imgrot_flag:    Image Rotator is Used: 1, not used: 0
	   tel_ra:         RA of the Telescope Pointing (HHMMSS.SSS)
	   tel_dec:        DEC of the Telescope Pointing (+DDMMSS.SS)
	   tel_equinox:    Equinox of the Telescope Pointing
           svprobe_mm:     Target Probe Position for SV (mm)

    Output:
	   center_ra:      RA Center of the SV CCD (HHMMSS.SSS)
	   center_dec:     DEC Center of the SV CCD (+DDMMSS.SS)
	   center_equinox: Equinox

    Errors:
           Normal: no exception
           Error:  raises a form of AstroError
    """

    rt = funkyHMStoHours(tel_ra)
    dt = funkyDMStoDeg(tel_dec)
    cx = subaru.ccd_center_offset_x
    cy = subaru.ccd_center_offset_y

    tel_equinox = float(tel_equinox)
    center_equinox = tel_equinox
    f_select = f_select.upper()

    # focus select
    if f_select in ('CS', 'CS_OPT'):
        st = 0
        minmm = subaru.probe_min_range_cs
        maxmm = subaru.probe_max_range_cs

    elif f_select in ('CS_IR',):
        st = 1
        minmm = subaru.probe_min_range_cs
        maxmm = subaru.probe_max_range_cs

    elif f_select in ('NS_OPT',):
        if imgrot_flag == 0:
            st = 2
	else:
            st = 3
        minmm = subaru.probe_min_range_ns
        maxmm = subaru.probe_max_range_ns

    else:
        raise AstroCalcError("Bad foci specified for calculation: '%s'" % (
            f_select))
	
    if (svprobe_mm < minmm) or (svprobe_mm > maxmm):
        raise AstroError("Probe position exceeds limits: probe_mm=%f" % (
            svprobe_mm))

    # Calc JD 
    jd = julianDate()

    if logger:
        logger.debug("svxequ(%d, %f, %f, %f, %f, %f, %f, %f, %f)" % (
            st, jd, tel_equinox, rotator, rt, dt, svprobe_mm, cx, cy))

    dcr, dcd = svxequ(st, jd, tel_equinox, rotator, rt, dt, svprobe_mm, cx, cy)

    if logger:
        logger.debug("Result: Center_RA(Hour)=%f  Center_DEC(Deg)=%f" % (
            dcr, dcd))

    # Hour -> RA, Deg -> DEC
    center_ra = raDegToString(dcr*15.0, format='%02d:%02d:%06.3f')
    center_dec = decDegToString(dcd, format='%s%02d:%02d:%05.2f')
    if logger:
        logger.debug("Result: Center_RA=%s  Center_DEC=%s  Center_Equinox=%f" % (
        center_ra, center_dec, center_equinox))
	
    return (center_ra, center_dec, center_equinox)


def SV_RaDec2mm(f_select, rotator, imgrot_flag, tel_ra, tel_dec,
                tel_equinox, target_ra, target_dec, target_equinox,
                logger=None):
    """
    SV_RaDec2mm

    George KOSUGI       Created  1998/12/16
                        Modified 2000/06/22
                        Modified 2000/06/23 Commented out prcsn
    Eric Jeschke        Modified 2011/04/11 Converted to python

    Input:
           f_select:       CS|CS_OPT / CS_IR / NS_IR / NS_OPT / P_IR / P_OPT
           rotator:        Rotation angle of Instrument/Image Rotator
                                    (degree:absolute? need to check on this)
           imgrot_flag:    Image Rotator is Used: 1, not used: 0
	   tel_ra:         RA of the Telescope Pointing (HHMMSS.SSS)
	   tel_dec:        DEC of the Telescope Pointing (+DDMMSS.SS)
	   tel_equinox:    Equinox of the Telescope Pointing
	   target_ra:      RA of the Target Object (HHMMSS.SSS)
	   target_dec:     DEC of the Target Object (+DDMMSS.SS)
	   target_equinox: Equinox of the Target Object

    Output:
           svprobe_mm:       Target Probe Position for SV (mm)
           ccd_y:            Y-Position on CCD

    Errors:
           Normal: no exception
           Error:  raises a form of AstroError
    """
    # RA, DEC: character to double RA(Hour) DEC(deg)
    rt = funkyHMStoHours(tel_ra)
    dt = funkyDMStoDeg(tel_dec)

    rs = funkyHMStoHours(target_ra)
    ds = funkyDMStoDeg(target_dec)

    cx = subaru.ccd_center_offset_x

    # FOCUS Select */
    # focus select
    if f_select in ('CS', 'CS_OPT'):
        st = 0
        minmm = subaru.probe_min_range_cs
        maxmm = subaru.probe_max_range_cs

    elif f_select in ('CS_IR',):
        st = 1
        minmm = subaru.probe_min_range_cs
        maxmm = subaru.probe_max_range_cs

    elif f_select in ('NS_OPT',):
        if imgrot_flag == 0:
            st = 2
	else:
            st = 3
        minmm = subaru.probe_min_range_ns
        maxmm = subaru.probe_max_range_ns

    else:
        raise AstroCalcError("Bad foci specified for calculation: '%s'" % (
            f_select))
	
    # Calc JD 
    jd = julianDate()

    if logger:
        logger.debug("svequx(%d, %f, %f, %f, %f, %f, %f, %f, %f, %f)" % (
            st, jd, tel_equinox, target_equinox, rotator, rt, dt, rs,
            ds, cx))

    mm, cy = svequx(st, jd, tel_equinox, target_equinox, rotator, rt, dt,
                    rs, ds, cx);

    if logger:
        logger.debug("Result: mm=%f  cy=%f" % (mm, cy))

    if math.fabs(cy) > subaru.ccd_max_width_y/2.0:
        raise AstroError("Target Position is out of range: CCD_Y=>%f" % (
            cy))

    if (mm < minmm) or (mm > maxmm):
        raise AstroError("Target Position is out of range: Probe_MM=>%f" % (
            mm))

    return (mm, cy)


def svxequ(st, jd, eo, pr, r0, d0, xx, cx, cy):
    """
    Coordinates of the slit viewer - x to equatorial
    Copyright reserved by Wataru Tanaka (1998)
    Modified by George Kosugi (2000-06-23)
    Converted to python and Modified by Eric Jeschke (2011-04-11)
    Parameters:
      int st: focal position flag;
      st=0:Cas(opt), st=1:Cas(IR), st=2:Nas(opt,non-ImR),st=3:Nas(opt,ImR)
      double jd: Jurian date
      double eo: equinox of the coordinates (year)
      double pr: offset angle of the rotator (deg)
      double r0: right ascension of the telescope (hour)
      double d0: declination of the telescope (deg)
      double xx: probe position (mm)
      double cx: offset x on the CCD (pix)
      double cy: offset y on the CCD (pix)
    Returns:
      double rs: right ascension of the guide star (hour)
      double ds: declination of the guide star (deg)
    """

    rad = math.pi / 180.0;

    # focal length, scale factor, and rotation angle
    # Modified by George 2000/06/23
    ## if st == 0:
    ##     fl = 100029.20; sf = 3.97
    ## elif st == 1:
    ##     fl = 100027.31; sf = 3.97
    ## elif st == 2:
    ##     fl = 102271.44; sf = 4.16; pr = 30.6932-pr; cy = -cy
    ## elif st == 3:
    ##     fl = 104234.24; sf = 4.16; pr = 30.6932-2.0*pr
    pr = -pr;
    if st == 0:
	fl = 100029.20; sf=3.97
    elif st == 1:
	fl = 100027.31; sf=3.97
    elif st == 2:
	fl = 102271.44; sf = 4.16; cy=-cy
    elif st == 3:
	fl = 104234.24; sf = 4.16

    sf = sf*0.015; cx = sf*cx+xx; cy = sf*cy
    r0 = math.radians(15.0*r0); d0=math.radians(d0)
    r = math.sqrt(cx*cx+cy*cy)/fl
    #th = math.atan2(cy, cx)+pr*rad
    th = math.atan2(cy, cx) + math.radians(pr)
    x = math.sin(r)*math.sin(th)
    y = math.cos(d0)*math.cos(r) - math.sin(d0)*math.sin(r)*math.cos(th)
    rt = r0 - math.atan2(x,y)
    z = math.sin(d0)*math.cos(r) + math.cos(d0)*math.sin(r)*math.cos(th)
    dt = math.atan2(z, math.sqrt(x*x+y*y))
    # TODO: assign symbolic constants....EJ
    jo = (eo-2000.0)*365.25 + 2451545.0
    # Comment out by George 2000/06/23
    # prcsn1(jd,jo,rt,dt,rs,ds);

    rs = rt; ds = dt
    #rs = rs /(15.0*rad)
    rs = rs / math.radians(15.0)
    ds = ds / rad
    if rs < 0.0:
        rs = rs + 24.0

    return (rs, ds)

def svequx(st, jd, eo, es, pr, r0, d0, rs, ds, cx):
    """
    Coordinates of the slit viewer - equatorial to x
    Copyright reserved by Wataru Tanaka (1998)
    Modified by George Kosugi (2000-06-23)
    Converted to python and Modified by Eric Jeschke (2011-04-11)
    Parameters:
      int st: focal position flag:
          st=0:Cas(opt), st=1:Cas(IR), st=2:Nas(opt,non-imR), st=3:Nas(opt,imR)
      double jd: Julian date
      double eo: equinox of the object (year)
      double es: equinox of the guide star (year)
      double pr: offset angle of the rotator (deg)
      double r0: right ascension of the object (hour)
      double d0: declination of the object (deg)
      double rs: right ascension of the guide star (hour)
      double ds: declination of the guide star (deg)
      double cx: offset x on the CCD (pix)
    Returns:
      double xx: position of the slit viewer (mm)
      double cy: offset y on the CCD (pix)
    """

    rad = math.pi / 180.0;

    r0 = math.radians(15.0*r0); d0 = math.radians(d0)
    rs = math.radians(15.0*rs); ds = math.radians(ds);
    pr = math.radians(pr)
    # TODO: assign symbolic constants....EJ
    jo = (eo-2000.0)*365.25 + 2451545.0
    js = (es-2000.0)*365.25 + 2451545.0
    # Comment out by George  2000/06/23
    # prcsn1(jo,jd,r0,d0,&r0,&d0); prcsn1(js,jd,rs,ds,&rs,&ds);

    sts = math.sin(r0-rs); cts = math.cos(r0-rs)
    sdo = math.sin(d0); cdo = math.cos(d0)
    sds = math.sin(ds); cds = math.cos(ds)
    x = cds*sts; y = cdo*sds-sdo*cds*cts; th = math.atan2(x,y)
    z = sdo*sds+cdo*cds*cts; r = math.atan2(math.sqrt(x*x+y*y),z)

    # focal length, scale factor, and rotation angle 
    # Modified by George 2000/06/23
    ## if st == 0:
    ##     fl = 100029.20; sf = 3.97; th=-pr+th
    ## elif st == 1:
    ##     fl = 100027.31; sf = 3.97; th=-pr+th
    ## elif st == 2:
    ##     fl = 102271.44; sf = 4.16; th=pr-th-math.radians(30.6932)
    ## elif st == 3:
    ##     fl = 104234.24; sf = 4.16; th=2.0*pr+th-math.radians(30.6932)
    if st == 0:
	fl = 100029.20; sf = 3.97; th+=pr
    elif st == 1:
	fl = 100027.31; sf = 3.97; th+=pr
    elif st == 2:
	fl = 102271.44; sf = 4.16; th+=pr
    elif st == 3:
	fl = 104234.24; sf = 4.16; th+=pr

    sf = sf*0.015
    xx = r*math.cos(th)*fl-cx*sf
    cy = r*math.sin(th)*fl/sf

    return (xx, cy)


#END

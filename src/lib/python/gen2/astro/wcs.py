#
# wcs.py -- module for calculating WCS info
#
#[ Takeshi Inagaki (tinagaki@naoj.org) --
#]
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Apr 23 16:28:09 HST 2012
#]
#
# TODO: CHECK OVERLAP OF TIME FUNCTIONS IN radec.py !!
#
#  References
#
#  [Kit95]  Kitchin C.R., Telescopes and Techniques: An Introduction to
#              Practical Astronomy, Springer-Verlag London, 1995.
#

import time
import math
from SOSS.status.common import STATNONE, STATERROR

import radec
import subaru

class FitsHeaderError(Exception):
    pass
class WCSError(FitsHeaderError):
    pass

# this function is provided by MOKA2 Development Team (1996.xx.xx)
#   and used in SOSS system
def trans_coeff (eq, x, y, z):
       
    tt = (eq - 2000.0) / 100.0
    
    zeta=2306.2181*tt+0.30188*tt*tt+0.017998*tt*tt*tt
    zetto=2306.2181*tt+1.09468*tt*tt+0.018203*tt*tt*tt
    theta=2004.3109*tt-0.42665*tt*tt-0.041833*tt*tt*tt
    
    zeta = math.radians(zeta) / 3600.0
    zetto = math.radians(zetto) / 3600.0
    theta = math.radians(theta) / 3600.0
    
    
    p11=math.cos(zeta)*math.cos(theta)*math.cos(zetto)-math.sin(zeta)*math.sin(zetto)
    p12=-math.sin(zeta)*math.cos(theta)*math.cos(zetto)-math.cos(zeta)*math.sin(zetto)
    p13=-math.sin(theta)*math.cos(zetto)
    p21=math.cos(zeta)*math.cos(theta)*math.sin(zetto)+math.sin(zeta)*math.cos(zetto)
    p22=-math.sin(zeta)*math.cos(theta)*math.sin(zetto)+math.cos(zeta)*math.cos(zetto)
    p23=-math.sin(theta)*math.sin(zetto)
    p31=math.cos(zeta)*math.sin(theta)
    p32=-math.sin(zeta)*math.sin(theta)
    p33=math.cos(theta)
    
    return (p11,p12,p13, p21, p22, p23, p31,p32, p33)

# this function is provided by MOKA2 Development Team (1996.xx.xx)
#   and used in SOSS system
# changed a little
# ra/dec degree and equinox are passed
# ra/dec degree based on equinox 2000 will be returned   
def eq2000(ra_deg, dec_deg, eq):

    args = (ra_deg, dec_deg, eq)
    if (None in args) or (STATNONE in args) or (STATERROR in args):
        raise FitsHeaderError("Invalid value in RA, DEC or EQUINOX")
                
    ra_deg, dec_deg = eqToEq2000(ra_deg, dec_deg, eq)

    rah, ramin, rasec = radec.degToHms(ra_deg)

    ra = radec.raHmsToString(rah, ramin, rasec, format='%02d:%02d:%06.3f')

    sign, decd, decmin, decsec = radec.degToDms(dec_deg)

    dec = radec.decDmsToString(sign, decd, decmin, decsec,
                               format='%s%02d:%02d:%05.2f')

    return (ra, dec)
       
def eqToEq2000(ra_deg, dec_deg, eq):
           
    ra_rad = math.radians(ra_deg)
    dec_rad = math.radians(dec_deg)
    
    x=math.cos(dec_rad) * math.cos(ra_rad) 
    y=math.cos(dec_rad) * math.sin(ra_rad)
    z=math.sin(dec_rad) 
    
    p11, p12, p13, p21, p22, p23, p31, p32, p33= trans_coeff (eq, x, y, z)
    
    x0 = p11*x + p21*y + p31*z
    y0 = p12*x + p22*y + p32*z
    z0 = p13*x + p23*y + p33*z
    
    new_dec = math.asin(z0)
    if( x0 == 0.0 ):
        new_ra = math.pi / 2.0
    else:
        new_ra = math.atan( y0/x0 )
        
    if( (y0*math.cos(new_dec) > 0.0 and x0*math.cos(new_dec)<=0.0)  or  
        (y0*math.cos(new_dec) <=0.0 and x0*math.cos(new_dec)< 0.0) ):
            new_ra += math.pi
            
    elif ( new_ra < 0.0 ):
        new_ra += 2.0*math.pi
        
    #new_ra = new_ra * 12.0 * 3600.0 / math.pi
    new_ra_deg = new_ra * 12.0 / math.pi * 15.0
   
    #new_dec = new_dec * 180.0 * 3600.0 / math.pi
    new_dec_deg = new_dec * 180.0 / math.pi
 
    return (new_ra_deg, new_dec_deg)


def calcPC(irot_tel, imgrot_flag, insrotpa, altitude, azimuth, imgrot):
    args = (irot_tel, imgrot_flag, insrotpa, altitude, azimuth, imgrot)
    if (None in args) or (STATNONE in args) or (STATERROR in args):
        raise WCSError("Invalid value in arguments")
             
    # imgrot is sync to telescope
    if irot_tel == 'LINK':
        sg = 1.0
        if imgrot_flag == '08':   # Red
            pa = (73.59 - float(insrotpa)) * 2.0
            pc11, pc12, pc21, pc22 = setPCs(pa, sg)
        elif imgrot_flag =='02': # Blue 
            # have not measured yet. Therefore, use same calculation as Red
            pa = (73.59 - float(insrotpa)) * 2.0
            pc11, pc12, pc21, pc22 = setPCs(pa,sg)
        else:                    # None 
            sg = -1.0
            pa = calcPA(irot_tel, imgrot_flag, float(insrotpa), altitude, azimuth, imgrot)
            pc11, pc12, pc21, pc22 = setPCs(pa,sg)
    elif irot_tel == 'FREE':
        if imgrot_flag =='08':   # Red
            sg=1.0
            pa=calcPA(irot_tel, imgrot_flag, float(insrotpa), altitude, azimuth, imgrot)
            pc11, pc12, pc21, pc22 = setPCs(pa,sg)
        elif imgrot_flag =='02': # Blue
            sg=1.0
            pa=calcPA(irot_tel, imgrot_flag, float(insrotpa), altitude, azimuth, imgrot)
            pc11, pc12, pc21, pc22 = setPCs(pa,sg)  
        else:
            sg=-1.0
            pa=calcPA(irot_tel, imgrot_flag, float(insrotpa), altitude, azimuth, imgrot)
            pc11, pc12, pc21, pc22 = setPCs(pa,sg)       
        
    return (pc11, pc12, pc21, pc22)   

 
def calcPA(irot_tel, imgrot_flag, insrotpa, altitude, azimuth, imgrot):
    subaru_lati_rad=math.radians(subaru.SUBARU_LATITUDE_DEG)
    alti_rad= math.radians(altitude)
    azim_rad= math.radians( (azimuth-180.0) )
    p=math.atan2(  math.cos(subaru_lati_rad) * math.sin(azim_rad),  
                   math.sin(subaru_lati_rad) * math.cos(alti_rad) +  math.cos(subaru_lati_rad) * math.sin(alti_rad) * math.cos( azim_rad)  )
       
    # imgrot is async and img is eihter red or blue
    if irot_tel is 'FREE' and (imgrot_flag is '08' or imgrot_flag is '02'):
        pa = 57.18 + altitude + math.degrees(p) - 2.0 * imgrot
    else:
        pa = 180.0 + 58.4 + altitude - math.degrees(p)
        
    return pa

def setPCs(pa, sg):
    
    pc11=math.cos( math.radians(pa) )
    pc12=math.sin( math.radians(pa) )
    pc21=-math.sin( math.radians(pa) ) * sg
    pc22=math.cos( math.radians(pa) ) * sg
    
    return (pc11, pc12, pc21, pc22)

# calc CD1_1 = PC001001 * CDELT1  | CD1_2 = PC001002 * CDELT1
#      CD2_1 = PC002001 * CDELT2  | CD2_2 = PC002002 * CDELT2
def calcCD(pc, cd):
    return pc * cd        
         
# calc fit keyword 'CDELT1/2'
def calcCDELT(cdelt, bin):
    return cdelt * bin

# calculate crpix 1/2  ccd center(X/Y) - (exposure X/Y pixel / bin)
def calcCRPIX(ccd, exp, bin):
    return ccd - ( exp / bin )

# msec to sec
def calcExpTime(exptime):
    return exptime / 1000.0

# ra hms to ra degree
def hmsToDeg (ra):
    hour, min, sec = ra.split(':')
    ra_deg = radec.hmsToDeg(int(hour), int(min), float(sec))
    return ra_deg
    
# dec dms to dec degree
def dmsToDeg (dec):
    sign_deg, min, sec = dec.split(':')
    sign=sign_deg[0:1]; deg =sign_deg[1:] 
    dec_deg=radec.decTimeToDeg(sign, int(deg), int(min), float(sec) )
    return dec_deg     

#  ag ccd degree/pixel
####  all SH values are dummy and it is ok with fake values #####
####  not figure them out yet #####

# calculate observation date   (YYYY-MM-DD)
def calcObsDate(sec, format='%04d-%02d-%02d'):
    gmt = adjustTime(sec, 0)
    return format % (gmt[0], gmt[1], gmt[2]) 
        
# calculate GMT   (HH:MM:SS.sss)        
def calcUT(sec, format='%02d:%02d:%06.3f'):
    gmt = adjustTime(sec, 0)
    return format % (gmt[3], gmt[4], gmt[5])
    
# calculate HST   (HH:MM:SS.sss)    
def calcHST (sec, format='%02d:%02d:%06.3f'):
    hst = adjustTime(sec, 0, timefunc=time.localtime)
    return format % (hst[3], hst[4], hst[5])
    
#
#
#def calcJulianDays(yyyy, mm, dd):
#    """Pythonized version of SOSS Julian Day calculation function.
#       SOSS original function is liboss_cal/OSScal_LST.c:getJD()."""
#    # Python rounded the value of mo down instead of truncating the value
#    mo = -((14 - mm) / 12)
#    pp = (1461 * (yyyy + 4800 + mo)) / 4 + (367 * (mm - 2 - mo * 12)) / 12
#    pjd = pp - (3 * ((yyyy + 4900 + mo) / 100)) / 4 - 32075.5 + dd
#    return pjd
#
#
def calcGST(tu, ut):
    """Pythonized version of SOSS Global Sidereal Time calculation function,
    but only for Mean case (removed the with and without 'short term' cases).
    """

    tu2 = tu * tu
    tu3 = tu2 * tu
    
    pgs = 24110.54841 + (8640184.812866 * tu) + (0.093104 * tu2) - \
          (0.0000062 * tu3) + ut
    #print "   calcGST1:  pgs = %12.3f" % pgs
    pgs = pgs - 86400.0 * int(pgs / 86400.0)
    
    if pgs < 0.0:
        pgs = pgs + 86400.0

    return pgs


def sidereal(year, month, day, hour, minute, second, offset=None):
    """Pythonized version of SOSS Local Sidereal Time calculation function.
    Modified to use passed date.
    """
   
    jd = calcJD(year, month, day, hour, minute, second)
    ut = (hour * 3600.0) + (minute * 60.0) + second
    tu = (jd - 2451545.0) / 36525.0
    gst = calcGST(tu, ut)

    if offset == None:
        #off = 37315.26  # (-155 28' 48.900" ):(155*3600+28*60+48.9)/15   SUBARU's LONGITUDE
        offset = math.fabs(subaru.SUBARU_LONGITUDE_DEG)*3600.0/15.0
    lst = gst - offset
    
    if lst < 0.0:
        lst = lst + 86400.0
    
    return lst


def calcLST_sec(sec, ut1):
    
    year, month, day, hour, min, sec = adjustTime(sec, ut1)
               
    # year/month/day/hour/min/sec 
    lst_sec = sidereal(year, month, day, hour, min, sec)
    return lst_sec

def calcLST(sec, ut1, format='%02d:%02d:%06.3f'):
    
    if not ( (ut1 == None) or (ut1 == STATNONE) or (ut1 == STATERROR) ):
                     
        lst_sec = calcLST_sec(sec, ut1)
        lst = adjustTime(lst_sec, 0)
        return format % (lst[3], lst[4], lst[5])
    
    else:
        return None

def calcJD(year, month, day, hour, minute, second):
    ut = hour * 3600.0 + minute * 60.0 + second
    dd = day + ( ut / 86400.0)
    
    mo = -((14 - month) / 12)
    pp = (1461 * (year + 4800 + mo)) / 4 + (367 * (month - 2 - mo * 12)) / 12
    pjd = pp - (3 * ((year + 4900 + mo) / 100)) / 4 - 32075.5 + dd
    
    #return calcJulianDays(year, month, dd)
    return pjd
    
   
def calcMJD(sec, ut1):   
    
    if not ( (ut1 == None) or (ut1 == STATNONE) or (ut1 == STATERROR) ):
        year, month, day, hour, minute, second = adjustTime(sec, ut1)
        
        jd = calcJD(year, month, day, hour, minute, second)
          
        return jd-2400000.5    
    else:
        return None
     

def adjustTime(sec, corr, timefunc=time.gmtime):
    
    mepoch = float(sec) + float(corr)
    utc = timefunc(mepoch)
      
    sec, usec = str(mepoch).split('.')
    sec = float('%s.%s' % (utc[5], usec))
    
    # year/month/day/hour/min/sec
    return (utc[0], utc[1], utc[2], utc[3], utc[4], sec)


def calcHA_sec(lst_sec, ra_deg):
        # According to Kitchin[Kit95], the relationship between local sidereal
        # time, right ascension and hour angle can be expressed in the
        # following formula
        #
        #       LST = RA + HA
        #
        # or alternatively
        #
        #       HA = LST - RA
        #
        # The LST is the passed parameter and the telescope supplies
        # the RA for the designated target.
        #ra_sec = ra_deg / 240.0
        ra_hour, ra_min, ra_sec = radec.degToHms(ra_deg)
        ra_sec = (ra_hour * 3600.0) + (ra_min * 60.0) + ra_sec
        delta_sec = lst_sec - ra_sec

        # normalize the expression. The hour value must be
        # between -12 < HA < 12. If it is +13, it must be -11
        delta_hrs = abs(int(delta_sec / 3600.0))
        if delta_hrs > 12:
            if delta_sec > 0:
                delta_sec -= 86400
            elif delta_sec < 0:
                delta_sec += 86400

        return delta_sec
    
        ## delta = Util.timediff(lst[3:6],self.ra)

        ## # normalize the expression. The hour value must be
        ## # between -12 < HA < 12. If it is +13, it must be -11
        ## if  (delta[0] == '+' and delta[1][0] > 12 ):
        ##     delta = Util.timediff(delta[1], [24, 0, 0])
        ## elif  (delta[0] == '-' and delta[1][0] > 12 ):
        ##     delta = Util.timediff(delta[1], [24, 0, 0])
        ##     delta[0] = '+'

        ## # Calculation is performed using H:M:S but need only be reported
        ## # as H:M.  We may want to support display of H:M:S in the future.
        ## self.nowStr.set("HA:%c%2.2dh%2.2dm" %
        ##                 (delta[0], delta[1][0], delta[1][1]))

# END

#! /usr/local/bin/python

#  Arne Grimstrup
#  2003-09-30
#  Modified 2005-02-22 14:49 Bruce Bon

#  This module implements a variety of support functions.
import time            # Time and time-specific formatting functions
import math            # Math functions

# Location constants for Subaru Telescope
DEFAULTLONG = -155.60222  # Degrees W of Prime Meridian
DEFAULTLAT = 19.935       # Degrees N of Equator
DEFAULTELV = 4163         # Metres above Sea Level

def calcAirMass(el):
    """Pythonized version of SOSS Air Mass calculation function."""
    if  el < 1.0 or el > 179.0:
        return None
    else:
        zd = 90.0 - el;
        sz = 1.0 / math.cos(zd / 180.0 * math.pi);
        sz1 = sz - 1.0;
        am = sz - 0.0018167 * sz1 - 0.002875 * sz1 * sz1 - 0.0008083 * sz1 * sz1 * sz1;
        return am


def calcJulianDays(yyyy, mm, dd):
    """Pythonized version of SOSS Julian Day calculation function.
       SOSS original function is liboss_cal/OSScal_LST.c:getJD()."""
    # Python rounded the value of mo down instead of truncating the value
    mo = -((14 - mm) / 12)
    pp = (1461 * (yyyy + 4800 + mo)) / 4 + (367 * (mm - 2 - mo * 12)) / 12
    pjd = pp - (3 * ((yyyy + 4900 + mo) / 100)) / 4 - 32075.5 + dd
    return pjd

def calcGST(tu, ut):
    """Pythonized version of SOSS Global Sidereal Time calculation function, but
       only for Mean case (removed the with and without 'short term' cases)."""

    tu2 = tu * tu
    tu3 = tu2 * tu
    rad = math.radians(1)

    pgs = 24110.54841 + 8640184.812866*tu + 0.093104*tu2 - 0.0000062*tu3 + ut
    #print "   calcGST1:  pgs = %12.3f" % pgs
    pgs = pgs - 86400.0 * int(pgs / 86400.0);
    #print "   calcGST2:  pgs = %12.3f" % pgs
    if pgs < 0.0:
        pgs = pgs + 86400.0;

    return pgs

def sidereal(long=DEFAULTLONG):
    """Pythonized version of SOSS Local Sidereal Time calculation function."""

    now = time.gmtime()

    ut = now[3] * 3600.0 + now[4] * 60.0 + now[5]
    dd = now[2] + (ut / 86400.0)
    jd = calcJulianDays(now[0], now[1], dd)

    tu = (jd - 2451545.0) / 36525.0
    gst = calcGST(tu, ut)

    lst = gst - 37315.3333; # (155 28' 50" ):(155*3600+28*60+50)/15
    if lst < 0.0:
        lst = lst + 86400.0;

    return time.gmtime(lst)
    

def timediff(a,b):
    """Compute the signed difference, a-b, between two unsigned H:M:S lists."""

    if a >= b:
        sign = '+'
        delta = [a[0]-b[0], a[1]-b[1], a[2]-b[2]]

        # Occasionally we need to borrow from the next most significant field
        if delta[2] < 0 and (delta[1] > 0 or delta[0] > 0):
            delta[1] -= 1
            delta[2] += 60
        if delta[1] < 0 and delta[0] > 0:
            delta[0] -= 1
            delta[1] += 60
    else:
        sign = '-'
        delta = [b[0]-a[0], b[1]-a[1], b[2]-a[2]]
        if delta[2] < 0 and (delta[1] > 0 or delta[0] > 0):
            delta[1] -= 1
            delta[2] += 60
            
        if delta[1] > 0 and delta[0] < 0:
            delta[0] += 1
            delta[1] -= 60
        elif delta[1] < 0 and delta[0] > 0:
            delta[0] -= 1
            delta[1] += 60
        
    return [sign,delta]


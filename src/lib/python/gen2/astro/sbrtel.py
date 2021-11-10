import sys
import time
import calendar
import re

import subaru
import radec

import ephem

## File format for TSC non-sidereal tracking files
## e.g.
## #1 Ceres on July 26 HST
## +00.0000 +00.0000 ON% +0.000
## UTC Geocentric Equatorial Mean Polar Geocentric
## ABS
## TSC
## 7
## 20010727000000.000 185406.057 -303521.41   1.953782861 2000.0000
## 20010727003000.000 185405.055 -303524.50   1.953904593 2000.0000
## 20010727010000.000 185404.053 -303527.59   1.954026432 2000.0000
## 20010727013000.000 185403.051 -303530.67   1.954148379 2000.0000
## 20010727020000.000 185402.050 -303533.75   1.954270432 2000.0000
## 20010727023000.000 185401.049 -303536.82   1.954392592 2000.0000
## 20010727030000.000 185400.049 -303539.90   1.954514860 2000.0000
##
## An explanation of the various terms is given below. It is strongly
## recommended that you use the underlined parameters. 
## Line # 	Options 	Description
## 1 	  	Comment for the file (starting with #)
## 2 	(+/-)ss.ssss 	RA proper motion (arcsec/yr)
## (+/-)ss.ssss 	Dec proper motion (arcsec/yr)
## ON%/OFF 	E-term
## (+/-)0.sss 	Annual parallax (arcsec)
## 3 	UTC/TDT 	
## Geocentric/Heliocentric/Barycentric 	
## Equatorial/Ecliptic 	
## Mean/Apparent 	
## XYZ/Polar 	
## Geocentric/Heliocentric 	
## 4 	ABS/REL	
## 5 	+/-/TSC 	Flag for Az drive direction
## 6 	  	Number of lines following this one
## 7+
## (max 6000) 	YYYYMMDDhhmmss.sss 	Date and time
## hhmmss.sss 	Right ascension (J2000.0)
## (+/-)ddmmss.ss 	Declination (J2000.0)
## rrr.rrrrrrrrr 	Geocentric distance (AU)
## yyyy.yyyy 	Equinox

class SubaruEphemeris(object):

    def __init__(self):
        # Set up observer for Subaru Telescope
        self.sbrtel = self.getObserver()
        self.curtime = time.time()

    def set_date_timetup(self, timetup):
        date_s = time.strftime("%Y/%m/%d %H:%M:%S", timetup)
        #print "setting date to %s" % (date_s)
        self.sbrtel.date = date_s

    def set_date(self, time_f):
        self.curtime = time_f
        # Observer() class in pyephem seems to require date to be
        # specified in UT
        #self.set_date_timetup(time.localtime(time_f))
        self.set_date_timetup(time.gmtime(time_f))

    def set_current_date(self):
        self.set_date(time.time())

    def set_date_localtime(self, year, month, day, hour, minute, second):
        timetup = (year, month, day, hour, minute, second, -1, -1, -1)
        time_f = time.mktime(timetup)
        self.set_date(time_f)

    def set_date_gmtime(self, year, month, day, hour, minute, second):
        timetup = (year, month, day, hour, minute, second, -1, -1, -1)
        time_f = calendar.timegm(timetup)
        self.set_date(time_f)

    def incr_date(self, delta_sec):
        self.set_date(self.curtime + delta_sec)

    def getObserver(self, time_f=None):
        sbrtel = ephem.Observer()
        sbrtel.lon = subaru.SUBARU_LONGITUDE
        sbrtel.lat = subaru.SUBARU_LATITUDE
        ## sbrtel.lon = str(subaru.SUBARU_LONGITUDE_DEG)
        ## sbrtel.lat = str(subaru.SUBARU_LATITUDE_DEG)
        sbrtel.elevation = subaru.SUBARU_ALTITUDE_METERS
        sbrtel.epoch = '2000.0'
        if time_f == None:
            time_f = time.time()
        sbrtel.date = time.strftime("%Y/%m/%d %H:%M:%S",
                                    time.gmtime(time_f))
        return sbrtel
        
    def TSCTracking(self, obj, start_f, end_f, stepsec=60.0):
        # tai_utc is the delta between UTC and TAI (atomic) time

        #time_f = start_f + tai_utc
        time_f = start_f

        tups = []
        while time_f <= end_f:
            self.set_date(time_f)
            obj.compute(self.sbrtel)

            (yr, mo, da, hr, mn, sc, x, y, z) = time.gmtime(time_f)

            time_tsc = "%04d%02d%02d%02d%02d%02d.000" % (
                yr, mo, da, hr, mn, sc)
            ra_deg = radec.hmsStrToDeg(str(obj.ra))
            ra_tsc = radec.raDegToString(ra_deg)
            dec_deg = radec.dmsStrToDeg(str(obj.dec))
            dec_tsc = radec.decDegToString(dec_deg)
            dst_tsc = "%.9f" % obj.earth_distance
            eqx_tsc = "2000.0000"
            tups.append((time_tsc, ra_tsc, dec_tsc, dst_tsc, eqx_tsc))

            time_f += stepsec

        return tups
            
## $ ssh u09XXX@obs.sum.subaru.nao.ac.jp
## Password: Password for the u-account
## Last login: ...
## Sun Microsystems Inc.   SunOS 5.10      Generic January 2005
## obs1[1]> cd ../wtanaka/planet
## /home/wtanaka/planet
## obs1[2]> jplsbrut
## Object  0:sun      1:Mercury  2:Venus    3:moon     4:Mars
##         5:Jupiter  6:Saturn   7:Uranus   8:Neptune  9:Pluto
## Object No. = 5

## Date and time shall be described in the TDT (~UT).
##  Start date (yyyymmdd) = 20091111
##        time   (hhmm)   = 0400
##  End   date (yyyymmdd) = 20091111
##        time   (hhmm)   = 0600
##  Step         (min)    = 30
##  TAI-UTC      (sec)    = 34

## Output file name   : /home/u09XXX/jupiter.dat
## Comment (<=35char.): Jupiter on 2009-11-11
## 20091111040000.000 212437.498 -161615.14   4.923599799 2000.0000
## 20091111043000.000 212437.953 -161612.86   4.923924226 2000.0000
## 20091111050000.000 212438.409 -161610.57   4.924248653 2000.0000
## 20091111053000.000 212438.864 -161608.28   4.924573081 2000.0000
## 20091111060000.000 212439.320 -161606.00   4.924897509 2000.0000

def jplsbrut():
    lst = [ephem.Sun(), ephem.Mercury(), ephem.Venus(), ephem.Moon(),
           ephem.Mars(), ephem.Jupiter(), ephem.Saturn(), ephem.Uranus(),
           ephem.Neptune(), ephem.Pluto()]

    sys.stdout.write("""Object  0:sun      1:Mercury  2:Venus    3:moon     4:Mars
        5:Jupiter  6:Saturn   7:Uranus   8:Neptune  9:Pluto
Object No. = """)
    sys.stdout.flush()
    index = int(sys.stdin.readline().strip())
    obj = lst[index]

    print "Date and time shall be described in HST."
    sys.stdout.write(" Start date (YYYY-MM-DD HH:MM:SS) = ")
    start_date = sys.stdin.readline().strip()
    sys.stdout.write(" End   date (YYYY-MM-DD HH:MM:SS) = ")
    end_date = sys.stdin.readline().strip()
    sys.stdout.write(" Step         (min)    = ")
    step = sys.stdin.readline().strip()
    print ""
    sys.stdout.write("Output file name   : ")
    outfile = sys.stdin.readline().strip()
    sys.stdout.write("Comment (<=35char.): ")
    comment = sys.stdin.readline().strip()[:35]

    match = re.match(r'^(\d{4})\-(\d{2})\-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})$',
                     start_date)
    vals = map(int, match.groups())
    vals.extend([-1, -1, -1])
    start_f = time.mktime(vals)
    
    match = re.match(r'^(\d{4})\-(\d{2})\-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})$',
                     end_date)
    vals = map(int, match.groups())
    vals.extend([-1, -1, -1])
    end_f = time.mktime(vals)

    stepsec = float(step) * 60.0

    sbrtel = SubaruEphemeris()
    tups = sbrtel.TSCTracking(obj, start_f, end_f, stepsec)

    length = len(tups)

    with open(outfile, 'w') as out_f:
        out_f.write('#%s\n' % (comment))
        out_f.write('+00.0000 +00.0000 ON% +0.000\n')
        out_f.write('UTC Geocentric Equatorial Mean Polar Geocentric\n')
        out_f.write('ABS\n')
        out_f.write('TSC\n')
        out_f.write('%d\n' % length)

        for tup in tups:
            out_f.write("%s %s %s %s %s\n" % tup)

def test_comet():
    obj = ephem.EllipticalBody()
    obj._epoch = '2000'
    obj._epoch_p = '2000'
    obj._inc = 18.7527
    obj._Om = 5.9635
    obj._om = 160.8131
    obj._e = 0.135067

    sbrtel = SubaruEphemeris()
    start_f = calendar.timegm((1999, 05, 24, 05, 00, 00, -1, -1, -1))
    end_f = calendar.timegm((1999, 05, 24, 10, 00, 00, -1, -1, -1))
    tups = sbrtel.TSCTracking(obj, start_f, end_f, 60.0)

    for tup in tups:
        print "%s %s %s %s %s\n" % tup
    
def test_planet():
    obj = ephem.Jupiter()

    sbrtel = SubaruEphemeris()
    start_f = calendar.timegm((2009, 11, 11, 04, 00, 00, -1, -1, -1))
    end_f = calendar.timegm((2009, 11, 11, 06, 00, 00, -1, -1, -1))
    tups = sbrtel.TSCTracking(obj, start_f, end_f, 30*60)

    for tup in tups:
        print "%s %s %s %s %s" % tup

def test_comet2():
    obj = ephem.readdb("C/1995 O1 (Hale-Bopp),e,89.4397,282.3793,130.5313,178.9199,0.0004118,0.99493492,0.0000,03/31.2852/1997,2000,g -2.0,4.0")
    sbrtel = SubaruEphemeris()
    start_f = calendar.timegm((2009, 11, 11, 04, 00, 00, -1, -1, -1))
    end_f = calendar.timegm((2009, 11, 11, 06, 00, 00, -1, -1, -1))
    tups = sbrtel.TSCTracking(obj, start_f, end_f, 30*60)

    for tup in tups:
        print "%s %s %s %s %s" % tup
    
    
# END

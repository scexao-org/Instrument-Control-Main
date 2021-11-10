#!/usr/bin/env python
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Aug 22 11:08:58 HST 2011
#]
# Daigo Tomono
#

import sys, os, time
import logging
import urllib
import shelve
import pprint
import socket
import smtplib
from email.mime.text import MIMEText


version = '20110822.0'

################################################
# Configuration variables, any of which can be 
# overridden with command line options
################################################

# URL to fetch to get weather data
weather_url = 'http://kiloaoloa.soest.hawaii.edu/forecast/mko/stats/text/latest_fcst.txt'

# sample file, archived at http://kiloaoloa.soest.hawaii.edu/forecast/mko/stats/text/2009111310.txt
test_data = \
"""2009111314,2009111320,2009111402,2009111414,2009111420,2009111502,2009111514,2009111520,2009111602,2009111614,2009111702,2009111714,2009111802
90,90,90,90,80,70,80,70,50,50,10,30,10
,,,,,,,,,,,,
100,100,100,100,90,75,75,75,60,50,25,20,10
90,90,90,75,60,50,50,25,10,10,0,0,0
8,8,8,8,6,6,6,6,6,4.5,3.5,4,2.5
2,0,0,2,0,0,3,1,1,4,1,5,1
22.5,20,20,15,10,10,10,10,10,10,10,10,10
120,120,120,90,90,60,210,315,315,0,45,45,120
NaN,1.5,1.5,NaN,1.3,1.2,NaN,1.1,1.0,NaN,0.8,NaN,0.8
"""

pfx = os.path.join(os.environ['HOME'], 'get2am')

# File to write data file that will be FTP-ed by TSC
tscfile = '%s/tomorrow-2am' % pfx

# Path to historical weather data
dbfile = '%s/tomorrow_2am.db' % pfx

# Logfile to write our log to
logfile = '%s/tomorrow-2am.log' % pfx


class WeatherError(Exception):
    """Generic exception thrown during weather processing cycle.
    """
    pass


def get_data(options):
    """Fetch the data from the MKWC using a URL.  Returns the data as a
    large string.
    """
    try:
        in_f = urllib.urlopen(options.url)
        try:
            return in_f.read()

        finally:
            in_f.close()

    except IOError, e:
        raise WeatherError("Cannot open weather URL (%s):\n%s" % (options.url,
                                                         str(e)))
        

# Current file format as of Nov 13, 2009
# guessed with comparing http://kiloaoloa.soest.hawaii.edu/forecast/mko/archive/index.cgi?selectedfcst=20091113.am.html
# and http://kiloaoloa.soest.hawaii.edu/forecast/mko/stats/text/2009111310.txt
# by Daigo Tomono <tomono at subaru.naoj.org>
# 1  time
# 2  mean cloud coverage (%)
# 3  <empty>
# 4  chance of fog (%)
# 5  chance of precipiation (%)
# 6  mean precipitable water (mm)
# 7  summit temperature (deg-C)
# 8  mean wind speed (mph)
# 9  wind direction (deg, N:0 E:90)
# 10 mean seeing (arcsec)
weather_keys = ('not_used', 'mean_cloud_coverage_%', 'empty', 'chance_of_fog_%',
                'chance_of_precipitation_%', 'mean_precipitable_water',
                'summit_temperature', 'mean_wind_speed', 'wind_direction')
# V3 new file format nov 20,2003  by Ryan Lyman
# 1  time,time,time,,,,
# 2  mean cloud coverage %
# 3  chance of fog %
# 4  chance of precipiation %
# 5  mean precipitable water
# 6  summit temperature
# 7  mean wind speed
# 8  wind direction
#
# V2 new file format feb 26, 2003
# yyyy,mm,dd,hh,{nine values for precip}
# yyyy,mm,dd,hh,{nine values for temperature}
# yyyy,mm,dd,hh,{nine values for windspeed}
# yyyy,mm,dd,hh,{nine values for winddir}
# when hh=10, nie values for 2pm,8pm,2am,,,
# when hh=17, nie values for 8pm,2am,8am,,,
# sometimes, {} are missing !!!
#
def parse_data(data):
    """Parse the data (a string) according to the format shown above.
    Data is stored into a dictionary by keys that are tuples:
    (date, attrib) where date is of the form "YYYYMMDDHH" and attrib
    is one of the weather_keys above.  The dictionary is returned.
    """

    res = {}
    
    # See comments above for format
    lines = data.split('\n')

    # First line is YYYYMMDDHH for each column of data
    line = lines.pop(0)
    dates = line.split(',')

    # There will be one line for each weather_key
    for i in xrange(1, len(weather_keys)):

        # Datums are comma separated
        key = weather_keys[i]
        line = lines.pop(0)
        data = line.split(',')

        # fog data has been missing for a while
        if 'empty' == key:
            continue 

        # Number of values should match number of dates
        if len(data) != len(dates):
            raise WeatherError("Weather data is corrupted!")
        
        # For each data value, store it into the dictionary according
        # to (date, attrib).  The data is all numerical.  We try to decode
        # as a float first, and then integer.
        for j in xrange(len(dates)):
            date = dates[j]

            try:
                value = float(data[j])

            except ValueError:
                try:
                    value = int(data[j])

                except ValueError, e:
                    raise WeatherError("Weather datum is neither int nor float: %s" % data[i])
                    
            res[(date, key)] = value
            
    return res
            

def write_tscfile(options, weather):
    """Write the one-line file that TSC wants to FTP from us.  Format was
    determined by studying Ogasawara-san's file.
    """

    # Time now, rounded to the last whole second
    now = int(time.time())

    # Whenever you run this, tomorrow is 24hrs ahead
    hr24_secs = 24 * 60 * 60
    then = now + hr24_secs

    # Cut back to tomorrow 2am
    (yr, mo, da, hh, mm, ss, wda, yda, isdst) = time.localtime(then)
    (hh, mm, ss, wda, yda) = (2, 0, 0, 0, 0)
    then = int(time.mktime((yr, mo, da, hh, mm, ss, wda, yda, isdst)))
    
    # Generate the key
    key = ('%04d%02d%02d%02d' % (yr, mo, da, hh))

    # python 2.3 has an issue with strftime precision
    #now = time.strftime('%4Y%2m%2d%2H', time.localtime(now))
    now = time.strftime('%Y%m%d%H', time.localtime(now))

    # For some reason, then is still printed as sec since epoch in 
    # Ogasawara-san's format
    then = int(then)

    # Don't ask my why this has the format it does, especially the part
    # about now=then--I'm just following the format of Ogasawara-san's script
    try:
        assert(weather.has_key((key, 'summit_temperature')))
        assert(weather.has_key((key, 'mean_wind_speed')))
        assert(weather.has_key((key, 'mean_precipitable_water')))

        res = "%5.1f # W=%5.1f mph Pc=%5.1f mm for %s 2am  at %s=%s" % (
            weather[(key, 'summit_temperature')],
            weather[(key, 'mean_wind_speed')],
            weather[(key, 'mean_precipitable_water')],
            key[0:8], now, then)

	out_f = open(options.tscfile, 'w')
        out_f.write("%s\n" % res)
        out_f.close()

        return res

    except (AssertionError, KeyError), e:
        raise WeatherError("Tomorrow's data seems to be missing!: %s" % str(e))


def check_send_email(options, weather):
    """Send email to the daycrews mailing list if the 3-night average 2am
    summit temperature differs from the forecasted termperature by more
    than 3 degrees.  The email is a reminder to check the temperature.
    """
    # Add/update current weather forecast to DBM database
    db = shelve.open(options.dbfile, writeback=False)
    d = {}
    # *^&@$%!!  DBM databases can only have string keys.  Convert
    # keys to strings
    for key in weather.keys():
	d[str(key)] = weather[key]
    db.update(d)

    # TODO: delete old entries no longer needed
    db.sync()

    # Whenever you run this, tomorrow is 24hrs ahead.  Make keys for
    # tomorrow, today, yesterday and the day before
    hr24_secs = 24 * 60 * 60
    today = time.time()
    tomorrow = today + hr24_secs
    ytrday = today - hr24_secs
    dbytrday = ytrday - hr24_secs

    # Cut back to 2am 
    (yr, mo, da, hh, mm, ss, wda, yda, isdst) = time.localtime(tomorrow)
    key1 = ('%04d%02d%02d02' % (yr, mo, da))
    (yr, mo, da, hh, mm, ss, wda, yda, isdst) = time.localtime(today)
    key2 = ('%04d%02d%02d02' % (yr, mo, da))
    (yr, mo, da, hh, mm, ss, wda, yda, isdst) = time.localtime(ytrday)
    key3 = ('%04d%02d%02d02' % (yr, mo, da))
    (yr, mo, da, hh, mm, ss, wda, yda, isdst) = time.localtime(dbytrday)
    key4 = ('%04d%02d%02d02' % (yr, mo, da))
    
    try:
        try:
            assert(db.has_key(str((key1, 'summit_temperature'))))
            assert(db.has_key(str((key2, 'summit_temperature'))))
            assert(db.has_key(str((key3, 'summit_temperature'))))
            assert(db.has_key(str((key4, 'summit_temperature'))))

            tonights_temp = db[str((key1, 'summit_temperature'))]

            ave_temp_last3nights = (db[str((key2, 'summit_temperature'))] +
                               	    db[str((key3, 'summit_temperature'))] + 
                                    db[str((key4, 'summit_temperature'))]) / 3.0

            tempdiff = tonights_temp - ave_temp_last3nights
            if abs(tempdiff) > 3.0:
                send_email(options, tempdiff)

        except (AssertionError, KeyError), e:
            raise WeatherError("Historical weather data seems to be missing!: %s" % str(e))
    finally:
        db.close()


def send_email(options, tempdiff):
    """Actually does the work of sending an email to daycrews.
    """
    if not options.email:
        return

    #raise WeatherError("TODO: send email to daycrews")

    # python 2.3 has an issue with strftime precision
    #now = time.strftime('%4Y/%2m/%2d/%2H:%2M', time.localtime(now))
    now = time.strftime('%Y/%m/%d/%H:%M', time.localtime(now))

    subj = "TempDiff_" + now
    body = "      # TempDiff= %6.2f (today-average(last 3days))" % tempdiff
    
    #mailto('daycrew', subj, body)
    mailto(options.email, subj, body)


def mailto(addr, subj, body):

    try:
        msg = MIMEText(body)
        me = os.environ['LOGNAME'] + '@' + socket.getfqdn()

        # me == the sender's email address
        # addr == the recipient's email address
        msg['Subject'] = subj
        msg['From'] = me
        msg['To'] = addr

        # Send the message via our own SMTP server, but don't include the
        # envelope header.
        s = smtplib.SMTP('smtp.subaru.nao.ac.jp')
        s.sendmail(me, [addr], msg.as_string())
        s.quit()

    except Exception, e:
        raise WeatherError("Error sending email: %s" % str(e))


def main(options, args):

    # Configure the logger.
    logger = logging.getLogger('get2am')
    logger.setLevel(options.loglevel)
    if options.logfile:
        fileHdlr = logging.FileHandler(options.logfile, 'a')
        fileHdlr.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(module)s:%(lineno)d %(message)s'))
        logger.addHandler(fileHdlr)
    # Add output to stderr, if requested
    if (not options.logfile) or (options.logstderr):
        stderrHdlr = logging.StreamHandler()
        stderrHdlr.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(module)s:%(lineno)d %(message)s'))
        logger.addHandler(stderrHdlr)

    try:
        # Get current forecast data
        data = get_data(options)
        logger.debug("raw data is: %s" % (pprint.pformat(data)))
        #data = test_data

        # Parse data
        weather = parse_data(data)
        logger.debug("parsed data is: %s" % (pprint.pformat(weather)))

        # Write TSC file
        res = write_tscfile(options, weather)
        logger.info(res)

        # Check if we should send email to daycrews
        check_send_email(options, weather)

    except Exception, e:
        # If there is an error, print a message to the log file and send
        # an email message to OCS
        errmsg = str(e)
        logger.error(errmsg)
        mailto('ssdsys@naoj.org', '[get2am] problem', errmsg)
        sys.exit(1)
   
    sys.exit(0)
    

if __name__ == '__main__':
    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage, version=('%%prog %s' % version))

    parser.add_option("--dbfile", dest="dbfile", default=dbfile,
                      help="Path to the file for storing weather data")
    parser.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    parser.add_option("--email", dest="email", default=None,
                      help="Email address to send warning notices")
    parser.add_option("--log", dest="logfile", metavar="FILE",
                      default=logfile,
                      help="Write logging output to FILE")
    parser.add_option("--loglevel", dest="loglevel", metavar="LEVEL",
                      type="int", default=logging.INFO,
                      help="Set logging level to LEVEL")
    parser.add_option("--tscfile", dest="tscfile", metavar="FILE",
                      default=tscfile,
                      help="Write text output to FILE")
    parser.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    parser.add_option("--stderr", dest="logstderr", default=False,
                      action="store_true",
                      help="Copy logging also to stderr")
    parser.add_option("--url", dest="url", metavar="URL",
                      default=weather_url,
                      help="Use URL to get weather data")

    (options, args) = parser.parse_args(sys.argv[1:])

    if len(args) != 0:
        parser.error("incorrect number of arguments")

    # Are we debugging this?
    if options.debug:
        import pdb

        pdb.run('main(options, args)')

    # Are we profiling this?
    elif options.profile:
        import profile

        print "%s profile:" % sys.argv[0]
        profile.run('main(options, args)')

    else:
        main(options, args)
       

#END

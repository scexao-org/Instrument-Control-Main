#
# dates.py -- routines for manipulating dates/times
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon May 10 10:50:51 HST 2010
#]
import datetime

def str2date(date_s):
    try:
        date = datetime.datetime.strptime(date_s, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        date = datetime.datetime.strptime(date_s, '%Y-%m-%d')

    return date

def tomorrow(year, month, day):
    """Simple routine for getting tomorrow's date.  Takes a year, month, day
    and returns a tuple of the same, but for tomorrow."""

    nowdate = datetime.datetime(year, month, day, 9, 0, 0)
    tomorrow = nowdate + datetime.timedelta(hours=24)

    (yr, mo, da, hr, min, sec, x, y, z) = tomorrow.timetuple()

    return (yr, mo, da)

#END

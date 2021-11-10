#!/usr/bin/env python
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Mar 11 13:23:55 HST 2010
#]
#
#
# remove once we're certified on python 2.6
from __future__ import with_statement

import sys, os.path, re
import time, datetime

import dates

# See functions night_cut and day_cut
begin_obs = '17:00:00'
end_obs   = '08:00:00'

ig_regex1 = re.compile(r'^(?P<time>[\d\.]+)\s*:\s*(\w+)\s*:\s*\d+\sbyte\s*:\s*\[(?P<rpcstr>.+)\]\s*$')
ig_regex2 = re.compile(r'^\s*(?P<size>\d+),(?P<time>[\d\.]+),SUBARUV1,\s*(?P<seqnum>\d+),(?P<from>\w+)\s*,\s*(?P<pid>\d+),\s*(?P<uid>\d*),\s*(?P<gid>\d*),(?P<to>\w+)\s*,(?P<pkttype>\w\w),(?P<pktsubtype>\w\w),\s*(?P<paylen>\d+),(?P<payload>.+)$')

sch_regex1 = re.compile(r'^(?P<time1>[\d\.]+)\s*:\s*(?P<subsys>[\w_]+)\s*:\s*(?P<wtf>\w\w)\s*:\s*TYPE\s*(?P<type>[\d\-]+)\s*:\s*HEADER\s*:\s*(?P<time2>[\d\.]+)\s*(?P<from>[\w_]+)\s*\-\>\s*(?P<to>[\w_]+)\s*size=\d+\s*ret=0x\w+\s*:\s*DATA\s*:\s*\[(?P<data>.+)\]$')

gen2_regex1 = re.compile(r'^(?P<time>\d{4}\-\d{2}\-\d{2}\s\d{2}:\d{2}:\d{2},\d{3})\s')

def gen2time_to_sec(s):
    """This function takes a timestamp such as found in a Gen2 log and converts it to
    seconds (a float).  e.g. '2010-03-10 13:43:52,793' -> 1268264632.793
    """
    (yr, mo, da, hh, mm, ss, wda, yda, isdst) = time.localtime(time.time())
    match = re.match(r'^(\d{4})\-(\d{2})\-(\d{2})\s+(\d{2}):(\d{2}):(\d{2}),(\d{3})$', s)
    if not match:
        raise Exception("Bad time format: %s" % (s))
    
    (yr, mo, da, hh, mm, ss, msec) = map(int, match.groups())
    t = time.mktime((yr, mo, da, hh, mm, ss, wda, yda, isdst))
    return t + float(msec)/1000.0

def sosstime_to_sec(s):
    """This function takes a timestamp such as found in a SOSS log and converts it to
    seconds (a float).  e.g. '20100310134352.793' -> 1268264632.793
    """
    (yr, mo, da, hh, mm, ss, wda, yda, isdst) = time.localtime(time.time())
    match = re.match(r'^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})\.(\d{3})$', s)
    if not match:
        raise Exception("Bad time format: %s" % (s))
    
    (yr, mo, da, hh, mm, ss, msec) = map(int, match.groups())
    t = time.mktime((yr, mo, da, hh, mm, ss, wda, yda, isdst))
    return t + float(msec)/1000.0


def cut_log(in_f, out_f, fromdate, todate, slacklines=5000):

    from_s = fromdate.strftime('%Y-%m-%d %H:%M:%S,%f')
    to_s = todate.strftime('%Y-%m-%d %H:%M:%S,%f')
    slackcount = 0
    withintime = False

    for line in in_f:
        match = gen2_regex1.match(line)

        try:
            time_s = match.group(1)
        except Exception as e:
            pass
        else:
            if time_s < from_s:
                withintime = False
                continue

            if time_s > to_s:
                withintime = False
                slackcount += 1
                if slackcount > slacklines:
                    return
            else:
                withintime = True
        finally:
            if withintime:
                out_f.write(line)

def cut_log_s(in_f, out_f, fromdate_s, todate_s, slacklines=5000):
    fromdate = dates.str2date(fromdate_s)
    todate = dates.str2date(todate_s)

    return cut_log(in_f, out_f, fromdate, todate, slacklines=slacklines)
    

def cut_log_f(inpath, outpath, fromdate_s, todate_s, slacklines=5000):

    with open(inpath, 'r') as in_f:
        with open(outpath, 'w') as out_f:
            return cut_log_s(in_f, out_f, fromdate_s, todate_s, slacklines=slacklines)
    

def cut(inargs, outpath, fromdate_s, todate_s):
    """Cut lines from a Gen2 log file."""
    
    # Try to open all the input files and make a list of the descriptors
    in_f_lst = []
    for inpath in inargs:
        if inpath == '-':
            in_f = sys.stdin
        else:
            in_f = open(inpath, 'r')
        in_f_lst.append((inpath, in_f))

    # Open the output file
    if outpath == '-':
        out_f = sys.stdout
    else:
        if os.path.exists(outpath):
            raise IOError("Path %s exists!" % outpath)

        out_f = open(outpath, 'w')

    for inpath, in_f in in_f_lst:
        res = cut_log_s(in_f, out_f, fromdate_s, todate_s)

        if inpath != '-':
            in_f.close()

    if outpath != '-':
        out_f.close()


def get_output(inargs, outpath, date_s, suffix):
    if os.path.isdir(outpath):
        inpath = inargs[0]
        if inpath == '-':
            pfx, ext = 'stdin', 'log'
        else:
            dirpath, filename = os.path.split(inpath)
            pfx, ext = os.path.splitext(filename)
            # is this a backup (rollover) file?
            # if so, strip the digits
            if (len(ext) > 0) and (ext[1:]).isdigit():
                pfx, ext = os.path.splitext(pfx)
                
        outpath = os.path.join(outpath, '%s-%s-%s%s' % (pfx, date_s, suffix, ext))
    return outpath

def night_cut(inargs, outpath, fromdate_s, todate_s=None):

    date = dates.str2date(fromdate_s)
    date_s = date.strftime('%Y%m%d')
    fromdate_s = date.strftime('%Y-%m-%d' + ' ' + begin_obs)

    outpath = get_output(inargs, outpath, date_s, 'obs')

    if not todate_s:
        (yr, mo, da, hr, min, sec, x, y, z) = date.timetuple()
        yr, mo, da = dates.tomorrow(yr, mo, da)
        todate_s = ('%04d-%02d-%02d' % (yr, mo, da)) + ' ' + end_obs

    cut(inargs, outpath, fromdate_s, todate_s)

    
def day_cut(inargs, outpath, fromdate_s, todate_s=None):

    date = dates.str2date(fromdate_s)
    date_s = date.strftime('%Y%m%d')
    fromdate_s = date.strftime('%Y-%m-%d') + ' ' + end_obs

    outpath = get_output(inargs, outpath, date_s, 'day')

    if not todate_s:
        todate_s = date.strftime('%Y-%m-%d') + ' ' + begin_obs

    cut(inargs, outpath, fromdate_s, todate_s)

    
def other_cut(inargs, outpath, fromdate_s, todate_s=None):

    if not todate_s:
        date = dates.str2date(fromdate_s)
        todate_s = date.strftime('%Y-%m-%d') + ' ' + end_obs

    outpath = get_output(inargs, outpath, fromdate_s, todate_s)

    cut(inargs, outpath, fromdate_s, todate_s)

    
def main(options, args):

    def get_output():
        if options.outpath:
            return options.outpath
        if options.outdir:
            return options.outdir
        return '-'

    action = options.action.lower()

    if action == 'cut':
        cut(args, get_output(), options.fromdate, options.todate)

    elif action == 'nightcut':
        night_cut(args, get_output(), options.fromdate, options.todate)
    elif action == 'daycut':
        day_cut(args, get_output(), options.fromdate, options.todate)

    elif action == 'time':
        try:
            fn = {'soss': sosstime_to_sec,
                  'gen2': gen2time_to_sec,}[options.timetype.lower()]
        except KeyError:
            print "Please specify a -t of 'gen2' or 'soss'!"
            sys.exit(1)

        if len(args) >= 1:
            t1 = fn(args[0])

        if len(args) >= 2:
            t2 = fn(args[1])

        if len(args) == 1:
            print "time = % 10.3f secs" % (t1)

        elif len(args) == 2:
            print "diff = % 10.3f secs" % (t2 - t1)
        
    else:
        print "I don't know how to perform action '%s'" % action


if __name__ == '__main__':
    from optparse import OptionParser

    usage = "usage: %prog -t soss|gen2 time1 time2"
    optprs = OptionParser(usage=usage, version=('%%prog'))

    optprs.add_option("-a", "--action", dest="action", 
                      help="Specify action to take")
    optprs.add_option("--from", dest="fromdate", metavar="DATE",
                      help="Specify from DATE as YYYY-MM-DD HH:MM:SS")
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-o", "--out", dest="outpath", metavar="PATH", 
                      help="Specify output PATH")
    optprs.add_option("-d", "--outdir", dest="outdir", metavar="DIR", 
                      help="Specify output PATH")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--to", dest="todate", metavar="DATE",
                      help="Specify to DATE as YYYY-MM-DD HH:MM:SS")
    optprs.add_option("-t", "--type", dest="timetype", metavar="TYPE",
                      help="Please choose soss|gen2 for the time type")

    (options, args) = optprs.parse_args(sys.argv[1:])

    if not options.action:
        optprs.error("Please specify an --action")

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

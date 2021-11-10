#!/usr/bin/env python
#
# checkstat.py -- utility to check last received times of status tables
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Sat Oct 30 13:50:01 HST 2010
#]
"""
USAGE:
    ./checkstat.py [ -t ]
"""

import sys, time

import remoteObjects as ro
from cfg.INS import INSdata

def _timecmp(x, y):
    if not isinstance(x[1], float):
        if not isinstance(y[1], float):
            return 0
        return -1
    if not isinstance(y[1], float):
        return 1
    if x[1] < y[1]:
        return -1
    if x[1] > y[1]:
        return 1
    return 0
    
def main(options, args):

    #logger = ssdlog.make_logger('checkstat', options)

    ro.init()

    st = ro.remoteObjectProxy(options.statussvc)

    insdata = INSdata()
    statusDict = {}
    lookupDict = {}

    # Get all the names of the 'ALIVE' status tables for the instruments
    for insname in insdata.getNames():
        if insname == 'VGW':
            continue
        inscode = insdata.getCodeByName(insname)
        tblname = '%3.3sS0001' % inscode

        alias = 'GEN2.STATUS.TBLTIME.%s' % tblname
        statusDict[alias] = 0
        lookupDict[alias] = insname

    # Additional tables to check
    for tblname in ('TSCS', 'TSCL', 'TSCV', 'VGWD', 'VGWQ'):
        alias = 'GEN2.STATUS.TBLTIME.%s' % tblname
        statusDict[alias] = 0
        lookupDict[alias] = tblname

    fetchDict = st.fetch(statusDict)
        
    if options.sorttime:
        times = fetchDict.items()
        times.sort(_timecmp)
        keys = [(alias, lookupDict[alias]) for alias in \
                map(lambda x: x[0], times)]
    else:
        keys = lookupDict.items()
        keys.sort(lambda x, y: cmp(x[1], y[1]))
    #print keys

    for alias, name in keys:
        timeval = fetchDict[alias]
        if timeval == '##NODATA##':
            time_s = 'No record'
        elif isinstance(timeval, float):
            time_s = time.strftime('%Y-%m-%d %H:%M:%S',
                                   time.localtime(timeval))
        else:
            time_s = 'ERROR: %s' % str(timeval)
        
        print "%-8.8s  %s" % (name, time_s)

        
if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [-t]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--statussvc", dest="statussvc", default='status',
                      metavar="NAME",
                      help="Use service NAME for obtaining status")
    optprs.add_option("-t", "--sorttime", dest="sorttime", default=False,
                      action="store_true",
                      help="Sort results by time instead of alphabetically")
    #ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    if len(args) != 0:
        optprs.error("incorrect number of arguments")

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


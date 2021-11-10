#!/usr/bin/env python
#
"""
STARSquery.py -- program for querying STARS frame info

Typical use (command line):
# check multiple independent frames
./STARSquery.py SUPA01217250 SUPA01217251 SUPA01217252 ...

# check a range of frames
./STARSquery.py SUPA01217250-SUPA01217319
"""

import sys, os
import re
import threading

import remoteObjects as ro
import logging, ssdlog
from SOSS.STARSint import STARSdb


def checkFrameList(starsdb, framelist):
    for frameid in framelist:
        #print frame
        if starsdb.is_in_stars(frameid[:12]):
            print " is in stars: %s" % frameid
        else:
            print "NOT in stars: %s" % frameid


def checkLogList(starsdb, loglist):
    for logid in loglist:
        if starsdb.is_log_stars(logid):
            print " is in stars: %s" % logid
        else:
            print "NOT in stars: %s" % logid


def checkFrameDict(starsdb, framedict):
    for frameid in framedict.keys():
        if starsdb.is_in_stars(frameid[:12]):
            framedict[frameid] = True
        else:
            framedict[frameid] = 'N'


def checkLogDict(starsdb, logdict):
    for logid in logdict.keys():
        if starsdb.is_log_stars(logid):
            logdict[logid] = True
        else:
            logdict[logid] = 'N'


def get_frameSpec(frameid):
    match = re.match('^(\w{3})([AQ])(\d)(\d{7})$', frameid)
    if not match:
        raise Exception("Bad frameid '%s'" % frameid)

    (inscode, frtype, prefix, number) = match.groups()
    return (inscode.upper(), frtype.upper(), int(prefix), int(number))

def getFrameList(framespec):
    if '-' in framespec:
        first, second = framespec.split('-')
        #print first, second

        (inscode1, frtype1, prefix1, number1) = get_frameSpec(first)
        (inscode2, frtype2, prefix2, number2) = get_frameSpec(second)
        #print inscode1, frtype1, prefix1, number1, number2

        framelist = [ '%3.3s%1.1s%1.1d%07d' % (
                           inscode1, frtype1, prefix1, num) \
                      for num in xrange(number1, number2+1) ]

    else:
        framelist = [ framespec ]

    return framelist



def server(options, args):
    svcname = options.svcname
    logger = ssdlog.make_logger(svcname, options)
       
    starsdb = STARSdb(logger)
    # Initialize remote objects subsystem.
    try:
        ro.init()

    except ro.remoteObjectError, e:
        logger.error("Error initializing remote objects subsystem: %s" % str(e))
        sys.exit(1)

        
    class QueryServer(object):
        def ro_echo(self, val):
            return val
        
        # List is assumed to be a list of frameid's to check
        def checkFrames(self, framelist):
            logger.debug("STARS query: %s" % str(framelist))
            d = {}
            for frameid in framelist:
                d[frameid] = 'N'

            checkFrameDict(starsdb, d)
            logger.debug("STARS result: %s" % str(d))
            return d

    svc = QueryServer()
    svr = ro.remoteObjectServer(svcname=svcname, port=options.port,
                                usethread=False, obj=svc)
    logger.info("STARS query starting up.")
    try:
        try:
            svr.ro_start()

        except KeyboardInterrupt:
            logger.error("Caught keyboard interrupt!")

    finally:
        logger.info("STARS query shutting down.")
        svr.ro_stop()


def main(options, args):

    if options.svcname:
        server(options, args)

    else:
        logger = ssdlog.make_logger('STARSquery', options)
        if options.framelist != None:
            with open(options.framelist, 'r') as in_f:
                buf = in_f.read()
                framelist = buf.split('\n')
                if len(framelist[-1]) == 0:
                    framelist = framelist[:-1]

        elif len(args) == 1:
            if options.filetype == 'fits':
                framelist = getFrameList(args[0])
            else:
                framelist = args

        else:
            # Args is assumed to be a list of frameid's to check
            framelist = args

        starsdb = STARSdb(logger)
        
        if options.filetype == 'fits':
            checkFrameList(starsdb, framelist)
        else:
            checkLogList(starsdb, framelist)
    

if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-f", "--framelist", dest="framelist", metavar="FILE",
                      help="Use FILE containing a list of frame ids")
    optprs.add_option("--port", dest="port", type="int", default=9901,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--svcname", dest="svcname", metavar="NAME",
                      default=None,
                      help="Register using NAME as service name")
    optprs.add_option("-t", "--type", dest="filetype", metavar="TYPE",
                      default='fits',
                      help="Specify file TYPE (fits|log)")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

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
       
# END

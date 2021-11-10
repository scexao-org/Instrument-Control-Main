#!/usr/bin/env python
#
# getSOSSstatus.py -- example Python program to get SOSS status
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Jan 30 10:08:45 HST 2008
#]
#
"""
Sample program to fetch SOSS status.  Invoke with SOSS status aliases on
the command line, e.g.

$ ./getSOSSstatus.py STATS.RA STATS.DEC

If the -i or --interval option is used, the program will wait that many
seconds and then fetch again, e.g.

$ ./getSOSSstatus.py -i 10 STATS.RA STATS.DEC

"""
import sys, time
from optparse import OptionParser

from SOSS.status import cachedStatusObj, statusError

usage = """
usage: %prog [options] <ALIAS> [...]
"""

def getAliases(statusObj, aliases):

    for aliasname in aliases:
        try:
            value = statusObj[aliasname]
            print "%24.24s = %s" % (aliasname, str(value))

        except statusError, e:
            print "%24.24s = %s" % (aliasname, '** ERROR **')
            print str(e)


def main(options, args):

    # Create a SOSS status object
    statusObj = cachedStatusObj(host=options.statushost)

    try:
        # One shot or..continuous?
        if options.interval == None:
            getAliases(statusObj, args)

        else:
            while True:
                getAliases(statusObj, args)
                print "---------------------------------"

                time.sleep(options.interval)

    except KeyboardInterrupt:
        print "Received keyboard interrupt!"
        


if __name__ == '__main__':

    # Parse command line options
    parser = OptionParser(usage=usage, version=('%prog'))
    
    parser.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    parser.add_option("-i", "--interval", dest="interval",
                      default=None, type=float,
                      help="Loop in intervals of NUM seconds",
                      metavar="NUM")
    parser.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    parser.add_option("--statushost", dest="statushost",
                      default='obs.sum.naoj.org',
                      help="Use HOST for obtaining SOSS status", metavar="HOST")

    (options, args) = parser.parse_args(sys.argv[1:])

    if len(args) == 0:
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

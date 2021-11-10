#!/usr/bin/env python
#
# screenPrint.py -- Python equivalent version of OSSC_screenPrint
#
import sys
import re
from optparse import OptionParser

from SOSS.status import cachedStatusObj, g2StatusObj, statusError, statusInfo

usage = """
usage: %prog [options] <ALIAS> [...]

Examples:

  Fetch SOSS status:
  ./screenPrint.py --statushost=obs --soss STATS.RA STATS.DEC STATL.TSC_F_SELECT
  
  Fetch Gen2 status:
  ./screenPrint.py --statushost=g2s4 STATS.RA STATS.DEC STATL.TSC_F_SELECT
  
"""

def main(options, args):

    # create a handle to the status system whether gen2 or soss
    if options.soss:
        sc = cachedStatusObj(host=options.statushost)

    else:
        sc = g2StatusObj(host=options.statushost, svcname=options.statussvc)

    if options.regex:
        info = statusInfo()
        regexes = map(re.compile, args)
        args = []
        for alias in info.getAliasNames():
            for regex in regexes:
                if regex.match(alias):
                    args.append(alias)
        args.sort()
            
    # fetch the list of status items (returns a dict)
    res = sc.get_statusValuesList(args)

    # print the key/values out, interpreting as necessary
    idx = 1
    for aliasname in args:
        try:
            aliasdef = sc.info.get_aliasDef(aliasname)

        except statusError, e:
            # this means that StatusAlias.pro does not contain this name
            aliasdef = None

        val = res.pop(0)
        
        if (aliasdef != None) and (aliasdef.stype == 'B'):
            if options.raw:
                print "%0x" % val
            else:
                print "% 3d : [%s]=[%0x]" % (idx, aliasname, val)
        else:
            if options.raw:
                print "%s" % str(val)
            else:
                print "% 3d : [%s]=[%s]" % (idx, aliasname, str(val))
        idx += 1


if __name__ == '__main__':

    # Parse command line options
    parser = OptionParser(usage=usage, version=('%prog'))
    
    parser.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    parser.add_option("--g2", dest="gen2", default=False, action="store_true",
                      help="Fetch status from Gen2")
    parser.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    parser.add_option("-R", "--raw", dest="raw", action="store_true",
                      default=False,
                      help="No extraneous output")
    parser.add_option("-r", "--regex", dest="regex", default=False, action="store_true",
                      help="Arguments are regular expressions for aliases")
    parser.add_option("--soss", dest="soss", default=False, action="store_true",
                      help="Fetch status from SOSS")
    parser.add_option("--statushost", dest="statushost",
                      default='localhost', metavar="HOST",
                      help="Use HOST for obtaining status")
    parser.add_option("--statussvc", dest="statussvc",
                      default='status', metavar="HOST",
                      help="Use NAME for obtaining Gen2 status")

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

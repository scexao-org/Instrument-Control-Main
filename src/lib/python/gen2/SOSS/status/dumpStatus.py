#!/usr/bin/env python
#
# dumpStatus.py -- grab status and dump it in dictionary format to stdout
#
import sys, time
import pprint
from optparse import OptionParser

from SOSS.status import cachedStatusObj, statusError

usage = """
usage: %prog [options] <ALIAS> [...]
       %prog [options] ALL
"""

badToken = '## N/A ##'


def captureAliases(sc, aliases):
    """Take a status object _sc_ and a list of status aliases _aliases_.
    Fetch all aliases and form a dictionary of the results.  Returns the
    dictionary and an error lookup table containing entries of the form:
    (aliasname, error string)
    """

    # Fill up an empty dictionary with all keys
    d = {}
    errorlist = []
    for aliasname in aliases:
        try:
            d[aliasname] = sc.get_statusValue(aliasname)
            
        except (KeyError, statusError), e:
            d[aliasname] = badToken
            errorlist.append((aliasname, str(e)))

    return (d, errorlist)


def captureAliasesGen2(sc, aliases):
    """Take a status object _sc_ and a list of status aliases _aliases_.
    Fetch all aliases and form a dictionary of the results.  Returns the
    dictionary and an error lookup table containing entries of the form:
    (aliasname, error string)
    """

    # Fill up an empty dictionary with all keys
    d = {}
    for aliasname in aliases:
        d[aliasname] = 0

    nd = sc.fetch(d)
    # TODO!
    errorlist = []
            
    return (nd, errorlist)


def g2PrimeAliases(sc, statusDict):

    # Ugly hack for non XML-RPC compliant data
    for aliasname in statusDict.keys():
        try:
            val = None
            aliasDef = sc.status.get_aliasDef(aliasname)

            if (aliasDef.stype == 'B') and (aliasDef.length > 4):
                val = statusDict[aliasname]
                newval = (('B0x' + ('%%0%dx' % (2*aliasDef.length))) % val)
                statusDict[aliasname] = newval

        except Exception, e:
            sys.stderr.write("Exception raised during long int conversion for '%s'=(%s):\n%s\n" % (
                aliasname, val, str(e)))
            statusDict[aliasname] = '##ERROR##'

            
def main(options, args):

    # Create status object
    sc = cachedStatusObj(host=options.statushost)

    # If "ALL" given as command line arg, then grab it, otherwise it is a
    # list of aliases
    if (len(args) == 1) and (args[0].upper() == "ALL"):
        if options.tables:
            args = sc.getTableNames()
        else:
            args = sc.getAliasNames()

    if options.statussvc:
        import remoteObjects as ro
        ro.init()
        
        sc = ro.remoteObjectProxy(options.statussvc)
        
        (d, errorlist) = captureAliasesGen2(sc, args)

    else:
        (d, errorlist) = captureAliases(sc, args)

    if options.g2prime:
        g2PrimeAliases(sc, d)
        
    # Dump Python readable repn to stdout
    #print repr(d)
    print "#\n# SOSS status snapshot: %s\n#\n" % (time.ctime())
    pprint.pprint(d)

    if len(errorlist) > 0:
        sys.stderr.write("ERRORS fetching:\n")
        for (aliasname, errstr) in errorlist:
            sys.stderr.write("%16s: %s\n" % (aliasname, errstr))
    
        

if __name__ == '__main__':

    # Parse command line options
    parser = OptionParser(usage=usage, version=('%prog'))
    
    parser.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    parser.add_option("--g2prime", dest="g2prime", action="store_true",
                      default=False,
                      help="Massage data for Gen2 status")
    parser.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    parser.add_option("--statushost", dest="statushost",
                      default='obs1.sum.subaru.nao.ac.jp',
                      help="Use HOST for obtaining SOSS status", metavar="HOST")
    parser.add_option("--statussvc", dest="statussvc", metavar="NAME",
                      help="Use NAME service for obtaining Gen2 status")
    parser.add_option("--tables", dest="tables", default=False, action="store_true",
                      help="Arguments are table names, not alias names")

    (options, args) = parser.parse_args(sys.argv[1:])


    #if len(args) == 0:
    #    parser.error("incorrect number of arguments")

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

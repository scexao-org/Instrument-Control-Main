#!/usr/bin/env python
#
# check_ope.py -- utility to check legacy OPE (observation) files
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed May  4 10:21:58 HST 2011
#]
#
# remove once we're certified on python 2.6
from __future__ import with_statement

import sys, os

import SOSS.parse.ope as ope


def get_similar(varref, vardict, choppct=0.85):
    length = int(len(varref) * choppct)
    varref = varref[:length]
    varlist = filter(lambda k: k.startswith(varref), vardict.keys())
    varlist.sort()
    return varlist

def remove_ignores(varref_list, ignorelist):
    return filter(lambda k: k.upper() not in ignorelist, varref_list)

def main(options, args):

    # Set up list of paths of include directories for PRM files, etc.
    if options.prmpath != None:
        # 1st priority--user specified on command line
        include_dirs = options.prmpath.split(':')

    elif os.environ.has_key('PRMPATH'):
        # 2nd priority--user has defined an environment variable
        include_dirs = os.environ['PRMPATH'].split(':')

    else:
        # 3rd priority--construct a default set:
        #  $HOME/Procedure:$HOME/Procedure/COMMON:$HOME/Procedure/<insname>
        home = os.path.join(os.environ['HOME'], 'Procedure')
        include_dirs = [
            home,
            os.path.join(home, 'COMMON'),
            ]
        if options.instrument:
            insname = options.instrument.upper()
            include_dirs.append(os.path.join(home, insname))
        

    # Iterate through the arguments, which are expected to be OPE
    # files and check them
    status = 0
    ignorelist = map(lambda s: s.upper(), options.ignore.split(','))
    
    for opefile in args:
        print "===================================================="
        print " OPE file: %s" % opefile
        print ""

        with open(opefile, 'r') as in_f:
            buf = in_f.read()

        try:
            res = ope.check_ope(buf, include_dirs=include_dirs)

            if len(res.badcoords) > 0:
                for bnch in res.badcoords:
                    print "Line %4d: warning: %s" % (
                        bnch.lineno, bnch.errstr)
                    print "  --> %s" % (bnch.text)
                status = 1
                
            bads = remove_ignores(res.badset, ignorelist)
            if len(bads) > 0:
                
                print "Undefined variable references in OPE file: %s" % (
                    ', '.join(bads))
                for bnch in res.badlist:
                    if bnch.varref.upper() not in bads:
                        continue
                    print "Line %4d: $%s" % (bnch.lineno, bnch.varref)
                    print "  --> %s" % (bnch.text)
                    similar = get_similar(bnch.varref, res.vardict,
                                          choppct=options.choppct)
                    print "Similar vars: %s" % (similar)

                status = 1

            if status == 0:
                print "Congratulations, the file looks good."
                    
        except Exception, e:
            print "Error trying to parse OPE file: %s" % str(e)
            print ""
            print "Please check the OPE structure:"
            print "see http://wiki.subaru.nao.ac.jp/wiki/OPE_File_Format"
            print "for details."
            status = 1

    sys.exit(status)
        
    
if __name__ == '__main__':

    # Parse command line options
    from optparse import OptionParser

    optprs = OptionParser(version=('%prog'))
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--chop", dest="choppct", metavar="PCT",
                      type="float", default=0.85,
                      help="Specify PCT for similar variable comparisons")
    optprs.add_option("-p", "--prmpath", dest="prmpath", metavar="PATH",
                      help="Specify colon-separated PATH for PRM lookups")
    optprs.add_option("-i", "--inst", dest="instrument", metavar="NAME",
                      help="Specify instrument NAME for PRM lookups")
    optprs.add_option("--ignore", dest="ignore", metavar="VARLIST",
                      default='',
                      help="Comma-separated list of bad variables to ignore")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")

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

#!/usr/bin/env python
#
# set_ltcs.py -- Laser Traffic Control System remote control interface
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Jun 19 12:34:42 HST 2008
#]
#
# Usage:
#  ./set_ltcs.py --laser_impacted=NO  ('NO', 'YES' or 'CALC')
# 
#  Sets the LASER_IMPACTED flag in LTCS
#
#  ./set_ltcs.py --laser_state=ON     ('OFF', 'ON' or 'ON-SKY')
# 
#  Sets the LASER_STATE flag in LTCS
# 
# Both options can be used together.
#
import sys, os

import remoteObjects as ro

# -- APPLICATION CONFIGURATION --

version = "20090121.0"

default_host = 'fldmon.sum.subaru.nao.ac.jp:8212'

###################################################
# PROGRAM
###################################################

def main(options, args):

    ro.init()

    auth = None
    if options.auth:
        auth = options.auth.split(':')
    elif os.environ.has_key('LTCSAUTH'):
        auth = os.environ['LTCSAUTH'].split(':')

    if options.rohost:
        (rohost, roport) = options.rohost.split(':')
        roport = int(roport)
        ro_svc = ro.remoteObjectClient(rohost, roport, auth=auth)
        #ro_svc = ro.remoteObjectClient(rohost, roport, auth=auth,
        #                               secure=True)

    if options.laserimpacted:
        val = options.laserimpacted.upper()
        if not val in ('NO', 'YES', 'CALC'):
            raise Exception("Valid values for --laser_impacted are NO|YES|CALC")

        ro_svc.set('laserimpacted', val)

    if options.laserstate:
        val = options.laserstate.upper()
        if not val in ('OFF', 'ON', 'ON-SKY'):
            raise Exception("Valid values for --laser_state are OFF|ON|ON-SKY")

        ro_svc.set('laserstate', val)

    sys.exit(0)


if __name__ == '__main__':
    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options] start|stop|status"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))

    optprs.add_option("--auth", dest="auth",
                      help="Use authorization; arg should be user:passwd")
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--laser_impacted", dest="laserimpacted",
                      help="Set LASER_IMPACTED flag (NO|YES|CALC)")
    optprs.add_option("--laser_state", dest="laserstate",
                      help="Set LASER_STATE flag (OFF|ON|ON-SKY)")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--secure", dest="secure", action="store_true",
                      default=False,
                      help="Use SSL encryption")
    optprs.add_option("--rohost", dest="rohost",
                      default=default_host,
                      help="Connect to host:port")

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

#!/usr/bin/env python
#
# getFrame.py -- Python equivalent version of OSST_GetFrame
#

import sys
from SOSS.frame import rpcFrameObj, frameError


version = '20080131.0'


def main(options, args):

    if not options.framehost:
        print "Need to specify a frame server host with --host"
        sys.exit(1)
        
    frameSvc = rpcFrameObj(options.framehost)

    inst = args.pop(0)
    frametype = args.pop(0)
    num = 0
    if options.setflag or (len(args) > 0):
        num = int(args.pop(0))

    if not options.setflag:
        res = frameSvc.get_frame(inst, frametype, num=num)

    else:
        res = frameSvc.set_frame(inst, frametype, num)
    
    print res


###################################################################
# MAIN PROGRAM
#
if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    parser.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    parser.add_option("--host", dest="framehost", 
                      help="Use HOST as the frame server host", metavar="HOST")
    parser.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    parser.add_option("--set", dest="setflag", default=False,
                      action="store_true",
                      help="Reset the counter.")

    (options, args) = parser.parse_args(sys.argv[1:])

    if (len(args) < 2) or (len(args) > 3):
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
       
# END

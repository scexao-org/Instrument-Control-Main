#! /usr/bin/env python
#
# g2login.py -- script to start a dual VNC client session for Gen2 SOSS
#   compatibility mode.
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Feb  4 15:36:33 HST 2009
#]

import sys, os
import logging
import myproc
from SimpleXMLRPCServer import SimpleXMLRPCServer
import binascii

port = 15051


LOG_FORMAT = '%(asctime)s | %(levelname)1.1s | %(filename)s:%(lineno)d | %(message)s'

class ClientControl(object):

    def __init__(self, logger):
        self.procs = {}
        self.logger = logger

    def ro_echo(self, arg):
        return arg

    def viewerOn(self, localdisp, localgeom, remotedisp, passwd, viewonly):

        passwd = binascii.a2b_base64(passwd)

        passwd_file = '/tmp/v__%d' % os.getpid()
        out_f = open(passwd_file, 'w')
        out_f.write(passwd)
        out_f.close()

        # VNC window
        cmdstr = "vncviewer -display %s -geometry %s %s -passwd %s" % (
            localdisp, localgeom, remotedisp, passwd_file)
        if viewonly:
            cmdstr += " -viewonly"
        self.logger.info(cmdstr)

        key = localdisp + localgeom
        try:
            self.procs[key].killpg()
        except:
            pass
        self.procs[key] = myproc.myproc(cmdstr, usepg=True)
        #os.remove(passwd_file)
        return 0

    def viewerOff(self, localdisp, localgeom):
        self.logger.info("viewer off %s" % (localdisp))
        try:
            key = localdisp + localgeom
            self.procs[key].killpg()
            del self.procs[key]
        except OSError, e:
            self.logger.error("viewer off error: %s" % (str(e)))
        return 0


def main(options, args):

    # Create top level logger.
    logger = logging.getLogger('viewercontrol')
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(LOG_FORMAT)

    if options.logfile:
        fileHdlr  = logging.FileHandler(options.logfile)
        fileHdlr.setFormatter(fmt)
        fileHdlr.setLevel(options.loglevel)
        logger.addHandler(fileHdlr)
    # Add output to stderr, if requested
    if options.logstderr or (not options.logfile):
        stderrHdlr = logging.StreamHandler()
        stderrHdlr.setFormatter(fmt)
        stderrHdlr.setLevel(options.loglevel)
        logger.addHandler(stderrHdlr)

    ctrl = ClientControl(logger)

    # Create server
    server = SimpleXMLRPCServer(('', options.port))
    server.register_function(ctrl.ro_echo)
    server.register_function(ctrl.viewerOn)
    server.register_function(ctrl.viewerOff)

    try:
        logger.info("Starting viewer control service...")
        try:
            server.serve_forever()
            
        except KeyboardInterrupt:
            logger.error("Caught keyboard interrupt!")

    finally:
        logger.info("Viewer control service shutting down...")
    
    sys.exit(0)

    
if __name__ == '__main__':
    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--log", dest="logfile", metavar="FILE",
                      help="Write logging output to FILE")
    optprs.add_option("--loglevel", dest="loglevel", metavar="LEVEL",
                      type="int", default=logging.INFO,
                      help="Set logging level to LEVEL")
    optprs.add_option("--stderr", dest="logstderr", default=False,
                      action="store_true",
                      help="Copy logging also to stderr")
    optprs.add_option("--port", dest="port", type="int", default=port,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")

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
       
    
# END

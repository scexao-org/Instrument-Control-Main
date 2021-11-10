#!/usr/bin/env python
#
# hskymon.py -- wrapper to start up the hskymon viewer under Gen2
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Tue Dec 27 15:25:40 HST 2011
#]
#
"""
USAGE:
Under normal operation, this program starts up the viewer as a subprocess,
registers with the remote objects name service as 'skyview' and processes
view requests.  e.g.

    $ ./hskymon.py --log=$LOGHOME/hskymon.log 

"""

import sys, os
from optparse import OptionParser
import fcntl, signal

import myproc
import ssdlog
import cfg.g2soss as g2soss

version = "20111227.0"


class HskymonViewerError(Exception):
    """Class for exceptions raised in this module.
    """
    pass


def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('hskymon', options)

    ### Start the legacy viewer ###

    # Flags that record what has been started, to effect an orderly
    # shutdown--see quit().  We declare variables here so that quit
    # is closed in their lexical scope.
    viewproc = None

    # This function is called if we receive a signal, terminate the app,
    # etc.
    def quit(exitcode):
        if viewproc:
            logger.info("Stopping hskymon viewer.")
            try:
                viewproc.killpg()
                
            except Exception, e:
                # If user used a normal exit mechanism from GUI then
                # trying to kill it here raises an error.
                if str(e) != "[Errno 3] No such process":
                    logger.error("Error stopping subprocesses: %s" % str(e))
                    exitcode = 1

        # logger.close() ??
        sys.exit(exitcode)

    def SigHandler(signum, frame):
        """Signal handler for all unexpected conditions."""
        logger.error('Received signal %d !' % signum)
        quit(1)

    # Set signal handler for signals
    signal.signal(signal.SIGHUP, SigHandler)
    signal.signal(signal.SIGTERM, SigHandler)

    logger.info("Starting hskymon...")
    try:
        # Start the SOSS Hskymon viewer
        cmdstr = "hskymon -l %s" % (os.path.join(os.environ['LOGHOME'],
                                                 'hskymon.log'))

        env = g2soss.make_env('SKYMON', options=options)
            
        logger.debug("Starting hskymon viewer.")
        viewproc = myproc.myproc(cmdstr, close_fds=True,
                                 env=env, addenv=True,
                                 usepg=(not options.nopg), 
                                 stderr=sys.stderr)

        # Set process' stdout and stderr to non-blocking
        #rv = fcntl.fcntl(viewproc.stdout, fcntl.F_SETFL, os.O_NDELAY)
        #rv = fcntl.fcntl(viewproc.stderr, fcntl.F_SETFL, os.O_NDELAY)

        viewproc.waitpg()
        logger.info("Viewer seems to have died--terminating")

    except KeyboardInterrupt:
        logger.error("Caught keyboard interrupt!")
        quit(0)

    except Exception, e:
        # TODO: log the traceback
        logger.error("Caught exception: %s" % str(e))

    quit(1)


if __name__ == '__main__':

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--display", dest="display", metavar="HOST:N",
                      help="Use X display on HOST:N")
    optprs.add_option("--nopg", dest="nopg", default=False,
                      action="store_true",
                      help="Do not form a process group")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    ssdlog.addlogopts(optprs)

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
       
# END hskymon.py

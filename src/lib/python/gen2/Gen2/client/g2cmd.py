#! /usr/bin/env python
#
# g2cmd.py -- issue a command in Gen2 from the command line
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Tue Mar  9 11:53:42 HST 2010
#]
#
"""
g2cmd.py is an interface to the Gen2 TaskManager function.  It allows
many aspects of the TaskManager to be controlled from the Unix command
line.  It's typical purpose is to execute a command, although it can
also set allocations, load task modules, load PARA interface files, or
reset the task manager.

Typical use:

    # Execute a command via the Task Manager
    $ g2cmd.py --cmd="EXEC TSC ..." 
    $ g2cmd.py --cmd="EXEC TSC ..." --timeout=10.0
    $ g2cmd.py "EXEC TSC ..." 10.0

    # Reset the Task Manager
    $ g2cmd.py --reset

    # Set allocations, load a task module and load a para directory
    $ g2cmd.py --allocs=taskmgr,TSC,status --load=TCSdd --para=TSC

    # Initialize the Task Manager from a session
    $ g2cmd.py --session=main
    
"""

import sys, os, time

import remoteObjects as ro
import ssdlog


def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('g2cmd', options)

    # Initialize remote objects subsystem.
    try:
        ro.init(options.rohosts.split(','))

    except ro.remoteObjectError, e:
        logger.error("Error initializing remote objects subsystem: %s" % str(e))
        sys.exit(1)

    # Global variable environment for tasks.  Empty is usually OK.
    envstr = ""

    # Set up authorization if specified
    auth = None
    if options.auth:
        auth = options.auth.split(':')
        
    res = 1
    try:
        try:
            # Get a handle to the Task Manager
            tm = ro.remoteObjectProxy(options.svcname,
                                      logger=logger, auth=auth)

            # Figure out what we are going to do.  Several options
            # can be combined.  Command issuing is always the last
            # thing done.  If no special options were given and no
            # command, then complain about it.
            nocomplain = False
            
            if options.reset:
                res = tm.reset(options.queuename)
                nocomplain = True

            if options.session:
                res = tm.initializeFromSession(options.session)
                nocomplain = True

            if options.allocs:
                res = tm.setAllocs(options.allocs.split(','))
                nocomplain = True

            if options.alloc:
                res = tm.addAllocs(options.alloc.split(','))
                nocomplain = True

            if options.load:
                res = tm.loadModules(options.load.split(','))
                nocomplain = True

            if options.para:
                res = tm.loadParaBase(options.para.split(','))
                nocomplain = True

            # If we are to issue a command, check that we have one
            cmdstr = options.cmdstr
            timeout = options.timeout

            # If a first argument was provided, it overrides any --cmd
            if len(args) >= 1:
                cmdstr = args[0]
                # Timeout is optional second argument
                if len(args) == 2:
                    timeout = float(args[1])

            if not cmdstr:
                if not nocomplain:
                    logger.error("No command specified!")

            else:
                logger.debug("Issuing command: %s" % (cmdstr))
                start_t = time.time()
                
                res = tm.execTaskTimeout(options.queuename,
                                         cmdstr, envstr,
                                         timeout)
                end_t = time.time()
                elapsed_t = end_t - start_t
                
                if res == 2:
                    logger.error("Command timed out (%.3f sec)" % (
                        elapsed_t))

                elif res != 0:
                    logger.error("Command error: %s" % (cmdstr))

                else:
                    logger.debug("Command terminated normally (%.3f sec)" % (
                        elapsed_t))

        except KeyboardInterrupt:
            logger.warn("Caught keyboard interrupt!")

        except Exception, e:
            logger.error("Caught exception: %s" % (str(e)))
            
        except Exception, e:
            logger.error("Caught exception: %s" % (str(e)))
            
    finally:
        pass

    sys.exit(res)


if __name__ == '__main__':

    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options] [cmdstr] [timeout]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--allocs", dest="allocs",
                      help="Specify a list of allocations to SET")
    optprs.add_option("--alloc", dest="alloc",
                      help="Specify a list of allocations to ADD")
    optprs.add_option("--auth", dest="auth",
                      help="TaskManager authorization; arg should be user:passwd")
    optprs.add_option("--cmd", dest="cmdstr",
                      help="Command string to execute in TaskManager")
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--load", dest="load",
                      help="Specify a list of task modules to load")
    optprs.add_option("--para", dest="para",
                      help="Specify a list of PARA directories to load")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--queuename", dest="queuename",
                      default="executer",
                      metavar="NAME", 
                      help="Use queue NAME for task submission")
    optprs.add_option("--reset", dest="reset", action="store_true",
                      default=False,
                      help="Reset the Task Manager")
    optprs.add_option("--rohosts", dest="rohosts", default='localhost',
                      help="Gen2 hosts")
    optprs.add_option("--session", dest="session", metavar="NAME",
                      help="Specify a session NAME to configure from")
    optprs.add_option("--svcname", dest="svcname", default="taskmgr0",
                      metavar="NAME", 
                      help="Connect to task manager at service NAME")
    optprs.add_option("--timeout", dest="timeout", type="float",
                      help="Timeout for command; default is no timeout")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])


    if len(args) > 2:
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

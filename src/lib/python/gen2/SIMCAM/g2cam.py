#!/usr/bin/env python
#
# g2cam.py -- Simulated or real instrument using OCS Gen2 interface
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Nov 30 16:15:31 HST 2011
#]
#
import sys, os
import signal
import threading
# profile imported below (if needed)
# pdb imported below (if needed)
# optparse imported below (if needed)

import Task
import remoteObjects as ro
import remoteObjects.Monitor as Monitor
import Gen2.soundsink as SoundSink
from g2Instrument import Instrument
import logging, ssdlog

version = "20110923.0"

# Convoluted but sure way of getting this module's directory
# TODO: is this still needed?
mydir = os.path.split(sys.modules[__name__].__file__)[0]
sys.path.insert(0, "%s/cams/SIMCAM" % mydir)

def main(options, args):

    # Several cameras can be specified with the --cam option
    # "main" camera is the last one on the list
    cams = options.cam.split(',')
    maincam = cams[-1]
    if '=' in maincam:
        (alias, maincam) = maincam.split('=')
    maincam = maincam.upper()

    # Create top level logger.
    logger = ssdlog.make_logger(maincam, options)

    ev_quit = threading.Event()

    # Determine the personalities.  User can specify several cams to be
    # loaded on the command line.  Also, cams can be given aliases.
    camlist = []
    main_alias = 'SIMCAM'
    if options.cam:
        for cam in cams:
            alias = cam
            if '=' in cam:
                (alias, cam) = cam.split('=')
            camlist.append((alias, cam))

        main_alias = camlist[0][0]

    svcname = main_alias

    # Create Gen2 interfaces
    try:
        ro.init([options.gen2host])

    except ro.remoteObjectError, e:
        logger.error("Cannot initialize remote objects: %s" % str(e))
        sys.exit(1)
    
    frameint = ro.remoteObjectProxy(options.framesvc)
    statusint = ro.remoteObjectProxy(options.statussvc)
    archiveint = ro.remoteObjectProxy(options.archivesvc)

    # Create process-wide thread pool for autonomous tasks
    threadPool = Task.ThreadPool(logger=logger, ev_quit=ev_quit,
                                 numthreads=options.numthreads)

    # Create monitor for PubSub style feedback
    monitor = Monitor.Monitor('%s.mon' % svcname, logger,
                              ev_quit=ev_quit, threadPool=threadPool)
    cmdchannel = 'INSint%d' % options.obcpnum
    
    sndsink = SoundSink.SoundSource(monitor=monitor, logger=logger,
                                   channels=['sound'])

    # Create the instrument object
    simcam = Instrument(logger, threadPool, monitor,
                        [cmdchannel], ev_quit=ev_quit, 
                        archiveint=archiveint, frameint=frameint,
                        statusint=statusint, obcpnum=options.obcpnum,
                        soundsink=sndsink)

    # Load the personalities.  User can specify several cams to be loaded
    # on the command line.  Also, cams can be given aliases.
    for (alias, cam) in camlist:
        simcam.loadPersonality(cam, alias=alias)

    channels = [cmdchannel, 'frames', 'sound']
    if options.monitor:
        # Publish our channels to the specified monitor
        monitor.publish_to(options.monitor, channels, {})

        # and subscribe to information about tasks
        taskch = [options.taskmgr, 'g2task']
        monitor.subscribe_cb(simcam.arr_taskinfo, taskch)
        monitor.subscribe_remote(options.monitor, taskch, {})

    try:
        try:
            logger.debug("Starting threadPool ...")
            threadPool.startall(wait=True)
            
            logger.debug("Starting monitor ...")
            monitor.start(wait=True)
            monitor.start_server(wait=True)

            logger.info("Starting instrument %s ..." % maincam)
            simcam.start()
            
            # Run off and do my UI here...
            simcam.ui(main_alias, options, args, ev_quit)

        except KeyboardInterrupt:
            logger.error("Keyboard interrupt!")

        except Exception, e:
            logger.error("Exception starting instrument: %s" % str(e))

    finally:
        if options.seppuku:
            logger.info("%s ... seppuku!" % maincam)
            os.kill(os.getpid(), signal.SIGKILL)

        logger.info("Stopping instrument %s ..." % maincam)
        simcam.stop()

        logger.debug("Stopping monitor ...")
        monitor.stop_server(wait=True)
        monitor.start(wait=True)

        logger.debug("Stopping threadPool ...")
        threadPool.stopall(wait=True)
            

if __name__ == '__main__':

    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("--archivesvc", dest="archivesvc", metavar="NAME",
                      default='archiver',
                      help="Lookup archive service by NAME")
    optprs.add_option("--cam", dest="cam", default="SIMCAM",
                      help="Use CAM as the instrument", metavar="CAM")
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--display", dest="display", metavar="HOST:N",
                      help="Use X display on HOST:N")
    optprs.add_option("--gen2host", dest="gen2host", metavar="HOST",
                      default='localhost',
                      help="Use HOST to dynamically locate services")
    optprs.add_option("--framesvc", dest="framesvc", metavar="NAME",
                      default='frames',
                      help="Lookup frame service by NAME")
    optprs.add_option("--monitorsvc", dest="monitor", metavar="NAME",
                      default='monitor',
                      help="Publish events to external monitor NAME")
    optprs.add_option("-n", "--obcpnum", dest="obcpnum", type="int",
                      default=9,
                      help="Use NUM as the OBCP number", metavar="NUM")
    optprs.add_option("--numthreads", dest="numthreads", type="int",
                      default=50,
                      help="Use NUM threads in thread pool", metavar="NUM")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--seppuku", dest="seppuku", action="store_true",
                      default=False,
                      help="Terminate the program forcefully on ^C")
    optprs.add_option("--statussvc", dest="statussvc", metavar="NAME",
                      default='status',
                      help="Lookup status service by NAME")
    optprs.add_option("--taskmgr", dest="taskmgr", metavar="NAME",
                      default='taskmgr0',
                      help="Connect to TaskManager with name NAME")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    if options.display:
        os.environ['DISPLAY'] = options.display

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

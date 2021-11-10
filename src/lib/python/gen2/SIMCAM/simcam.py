#!/usr/bin/env python
#
# simcam.py -- Simulated or real instrument using python OCS interface
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Tue Apr 12 10:09:33 HST 2011
#]
#
import sys, os
import threading
import signal
# profile imported below (if needed)
# pdb imported below (if needed)
# optparse imported below (if needed)
import logging

import Bunch
import Task
from Instrument import Instrument
from SOSS.DAQtk import OCSintError, ocsInt
from SOSS.frame import rpcFrameObj, frameError
from SOSS.status import cachedStatusObj, statusError
import ssdlog
# remoteObjects imported below (if needed)

version = "20100331.0"

# Convoluted but sure way of getting this module's directory
# TODO: is this still needed?
mydir = os.path.split(sys.modules[__name__].__file__)[0]
sys.path.insert(0, "%s/cams/SIMCAM" % mydir)


def get_hosts(insname, nshost):
    import xmlrpclib
    try:
        # Query the name server on the Gen2 host for the service
        # names of the instrument and the status subsystems
        proxy = xmlrpclib.ServerProxy('http://%s:7075/' % nshost)

        insint_hosts = proxy.getHosts(insname)
        if len(insint_hosts) == 0:
            raise OCSintError("No instrument interface found")

        status_hosts = proxy.getHosts('status')
        if len(status_hosts) == 0:
            raise OCSintError("No status interface found")

        # Strip off FQDN to short name
        cmds = insint_hosts[0][0].split('.')[0]
        sdst = status_hosts[0][0].split('.')[0]

        d = Bunch.Bunch(obshost=cmds, gethost=cmds, obchost=cmds,
                        stathost=sdst)
        return d
    
    except Exception, e:
        raise OCSintError("Couldn't configure interfaces: %s" % str(e))


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
    paradirs = []
    camlist = []
    main_alias = 'SIMCAM'
    if options.cam:
        for cam in cams:
            alias = cam
            if '=' in cam:
                (alias, cam) = cam.split('=')
            camlist.append((alias, cam))

            # Assume paradir is named after camera alias
            if options.paradir:
                paradir = ('%s/%s' % (options.paradir, alias))
                paradirs.append(paradir)

        main_alias = camlist[0][0]

    # If --gen2host option given, then we can dynamically look up
    # our legacy interfaces
    if options.gen2host:
        logger.info("Gen2 system--dynamically configuring legacy interfaces")
        hosts = get_hosts(main_alias, options.gen2host)
        
        obchost = hosts.obchost
        obshost = hosts.obshost
        gethost = hosts.gethost
        thruhost = hosts.obshost
        stathost = hosts.stathost

    # If --daqhost option is given, then it's a shortcut way to say ALL
    # interfaces are at this host
    elif options.daqhost:
        obchost = options.daqhost
        obshost = options.daqhost
        gethost = options.daqhost
        thruhost = options.daqhost
        stathost = options.daqhost

    else:
        # Otherwise the hosts are broken out into separate options:
        obchost = options.obchost
        obshost = options.obshost
        thruhost = options.thruhost
        stathost = options.stathost
        if options.gethost:
            gethost = options.gethost
        else:
            gethost = stathost

    # Create process-wide thread pool for autonomous tasks
    threadPool = Task.ThreadPool(logger=logger,
                                 ev_quit=ev_quit,
                                 numthreads=options.numthreads)
    
    # Create an OCS interface object (from DAQtk.py)
    daqtk = ocsInt(options.obcpnum, obshost=obshost,
                   thruhost=thruhost, stathost=stathost,
                   gethost=gethost, obchost=obchost,
                   obsif=options.obsif, obcif=options.obcif,
                   getif=options.getif, statif=options.statif,
                   ev_quit=ev_quit,
                   interfaces=options.interfaces,
                   monunitnum=options.monunitnum,
                   logger=logger, threadPool=threadPool)

    # Specified a frame id server for the instrument to use to fetch
    # frameids asynchronously
    if options.framehost:
        try:
            frameint = rpcFrameObj(options.framehost)

        except rpc.PortMapError, e:
            logger.error("Can't connect to portmapper on framehost (%s)" % \
                         options.framehost)
            sys.exit(1)
    else:
        frameint = None

    # Specified a status server for the instrument to use to fetch
    # status (not via the DAQtk status mechanism)
    if options.statushost:
        statusObj = cachedStatusObj(options.statushost)

    else:
        statusObj = None

    # Create the instrument object
    simcam = Instrument(logger, ev_quit=ev_quit, 
                        ocsint=daqtk, frameint=frameint,
                        statusObj=statusObj, obcpnum=options.obcpnum,
                        threadPool=threadPool,
                        allowNoPara=options.noparaok)

    # Load the personalities.  User can specify several cams to be loaded
    # on the command line.  Also, cams can be given aliases.
    for (alias, cam) in camlist:
        simcam.loadPersonality(cam, alias=alias)

    # Load the paradirs
    if len(paradirs) > 0:
        simcam.loadParaDirs(paradirs)
        
    try:
        try:
            logger.debug("Starting threadPool ...")
            threadPool.startall(wait=True)
            
            logger.info("Starting instrument %s ..." % maincam)
            simcam.start()
            
            # Subscribe our mini-monitor to the main monitor, if one was specified
            if options.monitor:
                import remoteObjects as ro
                ro.init()

                minimon = daqtk.get_monitor()
                minimon.subscribe(options.monitor, daqtk.monchannels, None)

            # Run off and do my GUI here...
            simcam.ui(main_alias, options, args, ev_quit)

        except KeyboardInterrupt:
            logger.error("Keyboard interrupt!")

    finally:
        if options.seppuku:
            logger.info("%s ... seppuku!" % maincam)
            os.kill(os.getpid(), signal.SIGKILL)

        logger.info("Stopping instrument %s ..." % maincam)
        simcam.stop()

        logger.debug("Stopping threadPool ...")
        threadPool.stopall(wait=True)

            

if __name__ == '__main__':

    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("--cam", dest="cam", default="SIMCAM",
                      help="Use CAM as the instrument", metavar="CAM")
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--daqhost", dest="daqhost",
                      help="Use HOST for all DAQ hosts", metavar="HOST")
    optprs.add_option("--display", dest="display", metavar="HOST:N",
                      help="Use X display on HOST:N")
    optprs.add_option("--framehost", dest="framehost", metavar="HOST",
                      help="Use HOST for the frame server host")
    optprs.add_option("--gen2host", dest="gen2host", metavar="HOST",
                      help="Use Gen2 HOST to dynamically locate interfaces")
    optprs.add_option("--gethost", dest="gethost",
                      help="Use HOST as the status request host",
                      metavar="HOST")
    optprs.add_option("--getif", dest="getif",
                      help="Use IF as the status request send IF",
                      metavar="IF")
    optprs.add_option("--interfaces", dest="interfaces",
                      default="cmd,file,sreq,sdst",
                      help="List of interfaces to activate")
    optprs.add_option("--seppuku", dest="seppuku", action="store_true",
                      default=False,
                      help="Terminate the program forcefully on ^C")
    optprs.add_option("--monitor", dest="monitor", metavar="NAME",
                      help="Publish events to external monitor NAME")
    optprs.add_option("--monunit", dest="monunitnum", type="int",
                      default=3, metavar="NUM",
                      help="Target OSSL_MonitorUnit NUM on OBS")
    optprs.add_option("-n", "--obcpnum", dest="obcpnum", type="int",
                      default=9,
                      help="Use NUM as the OBCP number", metavar="NUM")
    optprs.add_option("--noparaok", dest="noparaok", default=False,
                      action="store_true",
                      help="Allow missing PARA files")
    optprs.add_option("--numthreads", dest="numthreads", type="int",
                      default=20,
                      help="Use NUM threads in thread pool", metavar="NUM")
    optprs.add_option("--obchost", dest="obchost", metavar="HOST",
                      help="Use HOST as the DAQtk file host")
    optprs.add_option("--obcif", dest="obcif",
                      help="Use IF as the DAQtk file send IF", metavar="IF")
    optprs.add_option("--obshost", dest="obshost",
                      help="Use HOST as the DAQ command host", metavar="HOST")
    optprs.add_option("--obsif", dest="obsif",
                      help="Use IF as the DAQ command send IF", metavar="IF")
    optprs.add_option("--paradir", dest="paradir", metavar="DIR",
                      help="Use DIR for retrieving instrument PARA files")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--stathost", dest="stathost",
                      help="Use HOST as the DAQ status host", metavar="HOST")
    optprs.add_option("--statif", dest="statif",
                      help="Use IF as the DAQ status IF", metavar="IF")
    optprs.add_option("--statushost", dest="statushost", metavar="HOST",
                      help="Use HOST for the status server host")
    optprs.add_option("--thruhost", dest="thruhost",
                      help="Use HOST as the DAQ through host", metavar="HOST")
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

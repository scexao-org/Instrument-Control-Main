#! /usr/bin/env python
# 
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Jan 11 19:24:44 HST 2012
#]

# Standard library imports
import sys, os
import threading

# SSD/Gen2 imports
import remoteObjects as ro
import remoteObjects.Monitor as Monitor
import Bunch
import ssdlog
import Gen2.soundsink as SoundSink

# Local integgui2 imports
import fits
import controller as igctrl
import view.IntegView as igview
import view.common
import CommandQueue

def main(options, args):
    
    global controller, gui

    # Create top level logger.
    logger = ssdlog.make_logger('integgui2', options)

    ro.init()

    ev_quit = threading.Event()

    # make a name for our monitor
    if options.monname:
        myMonName = options.monname
    else:
        myMonName = 'integgui2-%s-%d.mon' % (
            ro.get_myhost(short=True), options.monport)

    # monitor channels we are interested in
    sub_channels = []
    pub_channels = ['g2task']

    # Create a local monitor
    mymon = Monitor.Monitor(myMonName, logger, numthreads=options.numthreads)
    #mymon = Monitor.Minimon(myMonName, logger, numthreads=options.numthreads)

    threadPool = mymon.get_threadPool()
        
    # command queues
    queues = Bunch.Bunch(default=CommandQueue.CommandQueue('default',
                                                            logger), )
    if options.logmon:
        logtype = 'monlog'
    else:
        logtype = 'normal'
        
    # Create view
    gui = igview.IntegView(logger, ev_quit, queues, logtype=logtype)

    # Create network callable object for notifications
    notify_obj = fits.IntegGUINotify(gui, options.fitsdir)
    notify_obj.update_framelist()

    # For playing sounds
    soundsink = SoundSink.SoundSource(monitor=mymon, logger=logger,
                                      channels=['sound'])
    pub_channels.append('sound')

    # Create controller
    controller = igctrl.IntegController(logger, ev_quit, mymon,
                                        gui, queues, notify_obj,
                                        soundsink, options,
                                        logtype=logtype)

    view.common.set_view(gui)
    view.common.set_controller(controller)

    # Configure for currently allocated instrument
    if options.instrument:
        insname = options.instrument
        controller.set_instrument(insname)
    else:
        try:
            insname = controller.get_alloc_instrument()
            controller.set_instrument(insname)
        except Exception, e:
            # TODO: error popup?
            pass

    if options.geometry:
        gui.setPos(options.geometry)
    #gui.logupdate()

    # Subscribe our callback functions to the local monitor
    # Task info
    # TODO: g2task should not be fixed
    taskch = [options.taskmgr, 'g2task']
    mymon.subscribe_cb(controller.arr_taskinfo, taskch)
    sub_channels.extend(taskch)
    
    # Obsinfo
    ig_ch = options.taskmgr + '-ig'
    mymon.subscribe_cb(controller.arr_obsinfo, [ig_ch])
    sub_channels.append(ig_ch)

    # Log info
    mymon.subscribe_cb(controller.arr_loginfo, ['logs'])
    #sub_channels.append('logs')

    # Fits info
    mymon.subscribe_cb(controller.arr_fitsinfo, ['frames'])
    sub_channels.append('frames')

    # Session info
    #mymon.subscribe_cb(controller.arr_sessinfo, ['sessions'])
    #sub_channels.append('sessions')

    # Configure from session, if requested
    if options.session:
        try:
            controller.config_from_session(options.session)
        except Exception, e:
            logger.error("Failed to initialize from session '%s': %s" % (
                options.session, str(e)))

    # Start up a remote object server for certain services provided by
    # integgui2
    svc = ro.remoteObjectServer(svcname=options.svcname,
                                obj=controller, logger=logger,
                                method_list=['get_ope_paths',
                                             'obs_play_sound_file',
                                             'obs_timer',
                                             'obs_confirmation',
                                             'obs_userinput',
                                             'obs_combobox',
                                             'load_page'],
                                port=options.port,
                                ev_quit=ev_quit,
                                usethread=True, threadPool=threadPool)
    
    # Load any files specified on the command line
    for opefile in args:
        gui.load_ope(opefile)

    server_started = False
    ro_server_started = False
    try:
        # Startup monitor threadpool
        mymon.start(wait=True)
        # start_server is necessary if we are subscribing, but not if only
        # publishing
        mymon.start_server(wait=True, port=options.monport)
        server_started = True

        # subscribe our monitor to the central monitor hub
        if sub_channels:
            mymon.subscribe_remote(options.monitor, sub_channels, {})
        # publish to central monitor hub
        if pub_channels:
            mymon.publish_to(options.monitor, pub_channels, {})

        if options.logmon:
            mymon.subscribe_remote(options.logmon, ['logs'], {})
            #mymon.subscribe(options.logmon, ['logs'], {})
            mymon.logmon(logger, options.logmon, ['logs'])

        svc.ro_start(wait=True)
        ro_server_started = True

        try:
            gui.mainloop(timeout=0.001)

        except KeyboardInterrupt:
            logger.error("Received keyboard interrupt!")

    finally:
        if ro_server_started:
            svc.ro_stop(wait=True)
        if server_started:
            mymon.stop_server(wait=True)
        mymon.stop(wait=True)
    
    logger.info("Exiting Gen2/SCM IntegGUI II...")
    #gui.quit()
    sys.exit(0)
    

# Create demo in root window for testing.
if __name__ == '__main__':
  
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
##     optprs.add_option("-c", "--channels", dest="channels", default='g2task',
##                       metavar="LIST",
##                       help="Subscribe to the comma-separated LIST of channels")
    optprs.add_option("--display", dest="display", metavar="HOST:N",
                      help="Use X display on HOST:N")
    optprs.add_option("--fitsdir", dest="fitsdir",
                      metavar="DIR",
                      help="Specify DIR to look for FITS files")
    optprs.add_option("-g", "--geometry", dest="geometry",
                      metavar="GEOM", default="1860x1100+57+0",
                      help="X geometry for initial size and placement")
    optprs.add_option("-i", "--inst", dest="instrument",
                      help="Specify instrument(s) to use for integgui")
    optprs.add_option("-m", "--monitor", dest="monitor", default='monitor',
                      metavar="NAME",
                      help="Subscribe to feeds from monitor service NAME")
    optprs.add_option("--monname", dest="monname", metavar="NAME",
                      help="Use NAME as our monitor subscriber name")
    optprs.add_option("-p", "--path", dest="monpath", default='mon.sktask',
                      metavar="PATH",
                      help="Show values for PATH in monitor")
    optprs.add_option("--monport", dest="monport", type="int", default=10017,
                      help="Register monitor using PORT", metavar="PORT")
    optprs.add_option("--numthreads", dest="numthreads", type="int",
                      default=50,
                      help="Start NUM threads in thread pool", metavar="NUM")
    optprs.add_option("--port", dest="port", type="int", default=12050,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--session", dest="session", metavar="NAME",
                      help="Configure from session NAME")
    optprs.add_option("--svcname", dest="svcname", metavar="NAME",
                      default="integgui0",
                      help="Register using NAME as service name")
    optprs.add_option("--taskmgr", dest="taskmgr", metavar="NAME",
                      default='taskmgr0',
                      help="Connect to TaskManager with name NAME")
    ssdlog.addlogopts(optprs)


    (options, args) = optprs.parse_args(sys.argv[1:])

##     if len(args) != 0:
##         optprs.error("incorrect number of arguments")

    if options.display:
        os.environ['DISPLAY'] = options.display

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


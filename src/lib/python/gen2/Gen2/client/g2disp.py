#!/usr/bin/env python
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Jan 11 23:20:33 HST 2012
#]
#
"""
"""
# remove once we're certified on python 2.6
from __future__ import with_statement

import sys, time, os
import threading
import binascii

import ssdlog
import myproc
import remoteObjects as ro
#import remoteObjects.PubSub as PubSub
import remoteObjects.Monitor as Monitor
import SOSS.SOSSrpc as SOSSrpc
import Gen2.soundsink as SoundSink
import Task

# Default ports
default_svc_port = 19051
default_mon_port = 19052

# Sound device to use for audio
default_sound_dev = "/dev/audio"


# TODO: put this in a utilities module
def error(msg, exitcode=0):
    """Called for an error.  Print _msg_ to stderr and exit program
    with code _exitcode_ if _exitcode_ is set to non-zero.
    """
    sys.stderr.write(msg + '\n')
    if exitcode != 0:
        sys.exit(exitcode)


class g2Disp(object):

    def __init__(self, **kwdargs):
        self.__dict__.update(kwdargs)
        self.lock = threading.RLock()
        self.procs = {}

        # Needed for starting our own tasks
        self.tag = 'g2disp'
        self.shares = ['logger', 'threadPool']

    def ro_echo(self, arg):
        return arg
    
    def start_server(self, rohosts, options):
        # Initialize remoteObjects subsystem
        try:
            ro.init(rohosts)

        except ro.remoteObjectError, e:
            self.logger.error("Error initializing remote objects subsystem: %s" % \
                         str(e))
            return

        # channels we are interested in
        channels = ['sound']

        self.ev_quit = threading.Event()
        self.server_exited = threading.Event()

        # Create a local pub sub instance
        # mymon = PubSub.PubSub('%s.mon' % self.basename, self.logger,
        #                       numthreads=30)
        monname = '%s.mon' % self.basename
        mymon = Monitor.Monitor(monname, self.logger, numthreads=30)
        self.monitor = mymon

        self.soundsink = SoundSink.SoundSink(monitor=mymon,
                                             logger=self.logger,
                                             ev_quit=self.ev_quit)
        self.soundsource = SoundSink.SoundSource(monitor=mymon,
                                                 logger=self.logger,
                                                 channels=['sound'])

        # Subscribe our callback functions to the local monitor
        mymon.subscribe_cb(self.soundsink.anon_arr, channels)

        self.mon_server_started = False
        self.ro_server_started = False

        # Startup monitor threadpool
        mymon.start(wait=True)
        mymon.start_server(wait=True, port=options.monport)
        self.mon_server_started = True

        self.threadPool = self.monitor.get_threadPool()

        # subscribe our monitor to the central monitor hub
        mymon.subscribe_remote(options.monitor, channels, ())

        # publish to central monitor hub
        #mymon.subscribe(options.monitor, channels, ())
        mymon.publish_to(options.monitor, ['sound'], {})

        self.svc = ro.remoteObjectServer(svcname=self.basename,
                                         obj=self, logger=self.logger,
                                         port=options.port,
                                         ev_quit=self.ev_quit,
                                         threadPool=self.threadPool,
                                         #auth=None,
                                         usethread=True)
        self.svc.ro_start(wait=True)
        self.ro_server_started = True

    def stop_server(self):
        self.logger.info("%s exiting..." % self.basename)
        if self.mon_server_started:
            self.monitor.stop_server(wait=True)
        if self.ro_server_started:
            self.svc.ro_stop(wait=True)
        self.monitor.stop(wait=True)


    def viewerOn(self, localdisp, localgeom, remotedisp, passwd, viewonly):
        self.muteOff()
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
        self.logger.info("viewer ON (-display %s -geometry %s %s)" % (
                localdisp, localgeom, remotedisp))

        key = localdisp + localgeom
        try:
            self.procs[key].killpg()
        except Exception, e:
            pass
        try:
            self.procs[key] = myproc.myproc(cmdstr, usepg=True)
        except Exception, e:
            self.logger.error("viewer on error: %s" % (str(e)))
        #os.remove(passwd_file)
        return 0

    def viewerOff(self, localdisp, localgeom):
        self.muteOn()
        self.logger.info("viewer OFF (%s)" % (localdisp))
        try:
            key = localdisp + localgeom
            self.procs[key].killpg()
            del self.procs[key]
        except (myproc.myprocError, OSError), e:
            self.logger.error("viewer off error: %s" % (str(e)))
        return 0

    def allViewersOff(self):
        self.logger.info("All viewers OFF")
        for key in self.procs.keys():
            try:
                self.procs[key].killpg()
                del self.procs[key]
            except (myproc.myprocError, OSError), e:
                self.logger.warn("viewer off error: %s" % (str(e)))
        return 0

    def muteOn(self):
        self.soundsink.muteOn()
        return 0

    def muteOff(self):
        self.soundsink.muteOff()
        return 0


def main(options, args, ui):

    myhost = SOSSrpc.get_myhost(short=False)

    basename = 'g2disp-%s' % (myhost.replace('.', '_'))
    logger = ssdlog.make_logger(basename, options)

    # Make our callback object
    mobj = g2Disp(logger=logger, basename=basename)

    ui.ui(mobj)
        

class CmdLineUI(object):
    def __init__(self, options):
        self.options = options

    def ui(self, obj):
        obj.start_server(self.options.rohosts.split(','),
                         self.options)

        try:
            try:
                while True:
                    print "Type ^C to exit the server"
                    sys.stdin.readline()

            except KeyboardInterrupt:
                print "Keyboard interrupt!"
                
        finally:
            obj.allViewersOff()
            obj.stop_server()


def add_options(optprs):
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-c", "--channels", dest="channels", default='sound',
                      metavar="LIST",
                      help="Subscribe to the comma-separated LIST of channels")
    optprs.add_option("-m", "--monitor", dest="monitor", default='monitor',
                      metavar="NAME",
                      help="Subscribe to feeds from monitor service NAME")
    optprs.add_option("--monport", dest="monport", type="int",
                      default=default_mon_port, metavar="PORT",
                      help="Use PORT for our monitor")
    optprs.add_option("--port", dest="port", type="int",
                      default=default_svc_port, metavar="PORT",
                      help="Use PORT for our monitor")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--rohosts", dest="rohosts", default='g2s1,g2s3,g2s4',
                      metavar="HOSTLIST",
                      help="Hosts to use for remote objects connection")
    optprs.add_option("--svcname", dest="svcname", default=None,
                      metavar="NAME",
                      help="Act as a sound distribution service with NAME")
    ssdlog.addlogopts(optprs)


if __name__ == '__main__':

    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    add_options(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    # Are we debugging this?
    if options.debug:
        import pdb

        pdb.run('main(options, args, no_gui)')

    # Are we profiling this?
    elif options.profile:
        import profile

        print "%s profile:" % sys.argv[0]
        profile.run('main(options, args, no_gui)')

    else:
        cmd_ui = CmdLineUI(options)

        main(options, args, cmd_ui)

#END

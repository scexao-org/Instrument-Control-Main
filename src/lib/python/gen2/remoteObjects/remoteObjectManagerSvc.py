#! /usr/bin/env python
#
# remoteObjectManagerSvc.py -- start/stop/monitor remote object services.
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Dec  9 16:27:58 HST 2010
#]
#
# Description:
#   Implements a service for handing graceful startup, shutdown and
#   monitoring/failover of remote object services.
#
''' Basic idea:
The names of the "top-level" services along with the startup commands are
registered in a configuration file.  This service starts those processes.
'''
# remove once we're certified on python 2.6
from __future__ import with_statement

import sys, socket, os
import threading
import time, signal

import Bunch
import remoteObjects as ro
import myproc
import ssdlog

# Our version
version = '20080524.0'


class managerSvcError(Exception):
    pass


def getLoadAvg(bnch):
    """Get the load average of the machine and store into the passed bunch
    object.
    """
    tup = os.getloadavg()
    bnch.la1min = tup[0]
    bnch.la5min = tup[1]
    bnch.la15min = tup[2]
    
    
def getProcInfo(pid):
    """Utility function to read information about a process from the /proc
    directory.  TODO: does this work on Solaris 10?
    """
    in_f = open('/proc/%d/status' % pid, 'r')
    data = in_f.read()
    in_f.close()

    lines = data.split('\n')
    res = {}
    for line in lines:
        line = line.strip()
        if ':' in line:
            try:
                (key, val) = line.split(':')

                key = key.strip().lower()
                val = val.strip()

                # Replace tabs in values
                if '\t' in val:
                    val = val.replace('\t', ' ')
                    
                res[key] = val
                
            except ValueError:
                continue

    return res

            
class processObj(object):

    def __init__(self, name, start_cmd, stop_cmd=None, logger=None,
                 stdout=None, stderr=None,
                 autorestart=False,
                 restart_threshold=10, restart_interval=1.0):
        self.name = name
        self.start_cmd = start_cmd
        self.stop_cmd = stop_cmd
        self.proc = None
        self.timestart = time.time()
        self.timecheck = self.timestart
        self.startcount = 0
        self.stopcount = 0
        self.autorestart = autorestart
        self.restart_threshold = restart_threshold
        self.restart_interval_init = restart_interval
        self.restart_interval = restart_interval
        self.lock = threading.RLock()
        # Seconds to wait after sending SIGTERM before trying SIGKILL
        self.killwait = 2.0

        # If no logger is passed in, create a simple one to stderr
        if not logger:
            self.logger = ro.nullLogger()
        else:
            self.logger = logger

        # Stdout/stderr messages
        if stdout:
            self.stdout = stdout
        else:
            #self.stdout = open("/dev/null", "w")
            self.stdout = sys.stdout
        if stderr:
            self.stderr = stderr
        else:
            #self.stderr = open("/dev/null", "w")
            self.stderr = sys.stderr


    def start(self):
        with self.lock:
            self.logger.info("Starting process associated with '%s'..." % \
                             self.name)
            if self.proc and self.proc.status() == 'running':
                # Should we raise an error here?
                #raise managerSvcError("process already running: '%s'" % self.name)
                return ro.OK

            self.startcount += 1

            self.logger.info(self.start_cmd)
            self.proc = myproc.myproc(self.start_cmd, stdout=self.stdout,
                                      stderr=self.stderr,
                                      usepg=True)
            self.timestart = time.time()

            if self.proc.status() != 'running':
                return ro.ERROR

            return ro.OK


    def stop(self):
        with self.lock:
            self.logger.info("Stopping process associated with '%s'..." % \
                             self.name)
            #if self.proc and self.proc.status() == 'running':
            if self.proc:
                self.stopcount += 1

                if self.stop_cmd:
                    self.logger.info("Attempting stop command associated with '%s'..." % \
                           self.name)
                    try:
                        self.logger.info(self.stop_cmd)
                        stop_proc = myproc.myproc(self.stop_cmd,
                                                  stdout=self.stdout,
                                                  stderr=self.stderr)

                        # Wait a bit
                        time.sleep(self.killwait)

                        stop_proc.kill()

                    except myproc.myprocError, e:
                        pass

                self.logger.info("Sending SIGTERM to top process associated with '%s'..." % \
                           self.name)
                try:
                    # Try to terminate gracefully by sending a SIGTERM to
                    # the top-level process
                    self.proc.signal(signal.SIGTERM)

                    # Wait a bit
                    status = self.proc.waitpg(timeout=self.killwait)
                    # if status == 'exited':
                    #     self.proc = None
                    #     return ro.OK

                except myproc.myprocError, e:
                    self.logger.error("Error sending SIGTERM to process: %s" % str(e))

                # Just to be sure we've cleaned up any mess, send SIGKILL
                # to the entire process group...
                try:
                    self.logger.info("Killing process group for '%s'." % \
                                     self.name)
                    self.proc.killpg()

                    # Wait some more
                    status = self.proc.waitpg(timeout=2.0)
                    if status == 'exited':
                        self.proc = None
                        return ro.OK

                except myproc.myprocError, e:
                    pass

                # Last sanity check
                if self.proc.statuspg() == 'exited':
                    self.proc = None
                    return ro.OK
                
                self.logger.info("Sorry, could not terminate '%s'." % \
                         self.name)
                return ro.ERROR


    def restart(self):
        try:
            self.stop()
        except Exception, e:
            pass

        # Manual restarts reset the stopcount
        self.reset_stopcount()
        
        self.start()
            

    def reset_stopcount(self):
        """Resets the stopcount=startcount so that automatic restarts get
        a fresh number of failure tries before supressing autorestart.
        """
        
        with self.lock:
            self.logger.info("Resetting stopcount associated with '%s'..." % \
                             self.name)
            self.stopcount = self.startcount
            self.restart_interval = self.restart_interval_init
            
        
    def getpid(self):
        """Returns the pid associated with this process object.  If the
        process is not running, -1 is returned.
        """
        with self.lock:
            if self.proc and self.proc.status() == 'running':
                return self.proc.getpid()
            else:
                return -1


    def getProcInfo(self):
        """Returns the status information associated with this process
        object, as gleaned from /proc.  If the process is not running,
        -1 is returned.
        """
        with self.lock:
            if self.proc and self.proc.status() == 'running':
                pid = self.proc.getpid()

                return getProcInfo(pid)
            
            else:
                return -1
            

    def update(self, cmdDict):
        """Setter for the command data.
        """
        with self.lock:
            self.start_cmd = cmdDict['start']
            self.stop_cmd = cmdDict.get('stop', None)
            

    def setRestartParams(self, autorestart, restart_threshold,
                         restart_interval):
        self.autorestart = autorestart
        self.restart_threshold = restart_threshold
        self.restart_interval = restart_interval
        
        
    def get_runningtime(self):
        """Returns the running time associated with this process object.
        If the process is not running, 0 is returned.
        """
        with self.lock:
            if not self.proc:
                # No process started
                self.logger.debug("No process handle for %s" % (self.name))
                return 0.0

            status = self.proc.statuspg()
            if status != 'running':
                self.logger.debug("Process group status = %s" % (status))
                return 0.0

            return time.time() - self.timestart
            

    def check(self):
        with self.lock:
            self.logger.debug("checking '%s'..." % self.name)
            self.timecheck = time.time()
        
            if not self.proc:
                # No process started
                self.logger.debug("No process attached to '%s'" % self.name)
                return

            status = self.proc.status()
            self.logger.debug("status of '%s' is %s" % (self.name, status))

            if status != 'running' and self.autorestart:
                # Was this stopped intentionally?
                if self.stopcount >= self.startcount:
                    self.logger.warn("Intentional stop (stopcount=%d, startcount=%d); not restarting" % \
                                       (self.stopcount, self.startcount))
                    return
                
                # Check to see if the process has had to be auto-restarted
                # excessively.  If so, don't restart unless our threshold
                # has passed.
                if ((self.startcount - self.stopcount) > self.restart_threshold):
                    self.logger.warn("Excessive auto-restarts associated with '%s'; not restarting" % \
                                       self.name)
                    return

                # If we are beneath our restart interval then silently
                # ignore the restart.
                self.logger.warn("timecheck: %f timestart:%f int: %f" % \
                                   (self.timecheck, self.timestart,
                                    self.restart_interval))
                if ((self.timecheck - self.timestart) < self.restart_interval):
                    return
                
                self.logger.warn("'%s' process seems to have died; attempting restart" % \
                                   self.name)

                # Exponential backoff on restarts
                self.restart_interval *= 2
                
                self.start()
                
            else:
                # Reset exponential backoff
                self.restart_interval = self.restart_interval_init
        
        
class remoteObjectManagerService(ro.remoteObjectServer):

    def __init__(self, name='', host=None, port=None, usethread=False,
                 logger=None, stdout=None, ev_quit=None, authDict=None,
                 secure=ro.default_secure, cert_file=ro.default_cert,
                 threadPool=None):

        # Logger for logging debug/error messages
        if not logger:
            self.logger = ro.nullLogger()
        else:
            self.logger = logger

        try:
            if stdout:
                self.logger.info("Using '%s' for default output" % stdout)
                self.stdout = open(stdout, "a")
            else:
                #self.stdout = open("/dev/null", "a")
                self.logger.info("Using STDOUT for default output")
                self.stdout = sys.stdout

        except IOError, e:
            self.logger.info("Using /dev/null for default output")
            self.stdout = open("/dev/null", "a")
            
        if not ev_quit:
            self.ev_quit = threading.Event()
        else:
            self.ev_quit = ev_quit

        # will set self.name, etc.
        ro.remoteObjectServer.__init__(self, name=name, host=host, port=port,
                                       logger=self.logger,
                                       usethread=usethread,
                                       ev_quit=self.ev_quit,
                                       authDict=authDict,
                                       secure=secure, cert_file=cert_file,
                                       threadPool=threadPool)

        self.map = {}
        self.lock = threading.RLock()
        # maximum seconds to sleep, is subdivided by a count of processes monitored
        self.sleepquantum = 1.0
        self.count = 0

        # Table of current load average info
        self.myldavg = Bunch.threadSafeBunch()
        self.starttime = time.time()


    def __get_po(self, name):
        with self.lock:
            try:
                return self.map[name]
            except KeyError, e:
                raise managerSvcError("there is no process associated with '%s'" % name)
                

    def add_with_output(self, name, cmdDict):

        self.logger.info("Trying to register '%s'" % (name))

        start_cmd = cmdDict['start']
        stop_cmd = cmdDict.get('stop', None)
        stdout = cmdDict.get('stdout', self.stdout)
        stderr = cmdDict.get('stderr', self.stdout)

        with self.lock:
            # If there is an existing process object with this name, then
            # just reset its command line
            if self.map.has_key(name):
                self.logger.info("reloading info for '%s'" % name)
                self.map[name].update(cmdDict)

            # Otherwise make a new process object
            else:
                po = processObj(name, start_cmd, stop_cmd=stop_cmd,
                                logger=self.logger,
                                stdout=stdout, stderr=stderr)
                self.map[name] = po
                self.count += 1

            return ro.OK

        
    def add(self, name, cmd):
        """Old method to be deprecated--use add_with_output instead"""
        d = {}
        d['start'] = cmd
        
        return self.add_with_output(name, d)

        
    def set_restart(self, name, autorestart, restart_threshold,
                    restart_interval):
        po = self.__get_po(name)

        self.logger.info("[managerSvc] setting restart params associated with '%s'" % name)
        po.setRestartParams(autorestart, restart_threshold, restart_interval)
        return ro.OK


    def remove(self, name):

        self.logger.info("Trying to unregister '%s'" % (name))
        try:
            self.stop(name)

        except Exception, e:
            self.logger.warn("Error stopping process associated with '%s': %s" % \
                               (name, str(e)))
        
        with self.lock:
            del self.map[name]

            self.count -= 1
            return ro.OK

        
    def getpid(self, name):
        # Special case for self
        if name == self.name:
            return os.getpid()

        po = self.__get_po(name)

        return po.getpid()


    def getNames(self):
        with self.lock:
            return self.map.keys()

        
    def start(self, name):
        po = self.__get_po(name)

        self.logger.info("[managerSvc] starting process associated with '%s'" % name)
        return po.start()


    def stop(self, name):
        po = self.__get_po(name)

        self.logger.info("[managerSvc] stopping process associated with '%s'" % name)
        po.stop()
        return ro.OK


    def restart(self, name):
        po = self.__get_po(name)

        self.logger.info("[managerSvc] restarting process associated with '%s'" % name)
        po.stop()
        return po.start()


    def stopall(self):
        """Stop all processes being monitored.
        """
        for name in self.getNames():
            self.stop(name)
        return ro.OK


    def startall(self):
        """Start all programs that are registered.
        """
        for name in self.getNames():
            self.start(name)
        return ro.OK

        
    def restartall(self):
        """Restart all processes being monitored.
        """
        self.stopall()
        return self.startall()

        
    def shutdown(self):
        """Shutdown all processes and terminate the remoteObjectManagerSvc.
        """
        self.stopall()

        self.quit()
        return ro.OK


    def quit(self):
        self.ev_quit.set()
        
        return ro.OK


    def clear(self):
        for name in self.getNames():
            self.remove(name)
        return ro.OK


    def gettime(self, name):
        # Special case for self
        if name == self.name:
            return time.time() - self.starttime

        po = self.__get_po(name)

        rt = po.get_runningtime()
        return rt


    def getProcInfo(self, name):
        # Special case for self
        if name == self.name:
            return getProcInfo(os.getpid())

        po = self.__get_po(name)

        return po.getProcInfo()


    def getLoadAvg(self):

        getLoadAvg(self.myldavg)
        d = {}
        d.update(self.myldavg)

        return d


    def bootup_slaves(self, hosts):
        hosts = hosts.split(',')
        cmd = os.path.abspath(sys.argv[0])
        #print "cmd is '%s'" % cmd
        for host in hosts:
            self.add("mgrsvc(%s)" % (host), "ssh %s %s" % (host, cmd))
        self.startall()


    def shutdown_slaves(self, hosts):
        hosts = hosts.split(',')
        hostports = [(host, ro.managerServicePort) \
                     for host in hosts]
        sp = ro.remoteObjectSPAll('mgrsvc', hostports=hostports)
        results = sp.shutdown()
        

    # This gets called when a service has stopped responding (however that is
    # defined) and the appropriate action should be taken (e.g. restart, etc.)
    #
    def failure(self, name):

        # TODO: more elaborate logic
        return self.restart(name)


    def ro_manager_loop(self):

        self.logger.info("Starting remote object manager loop...")
        getLoadAvg(self.myldavg)

        while not self.ev_quit.isSet():
            for name in self.getNames():
                po = self.__get_po(name)
                if not po:
                    continue

                po.check()

            # Update the current load averages
            #getLoadAvg(self.myldavg)
            #self.logger.debug("Averages: %f %f %f" % (
            #   self.myldavg.la1min, self.myldavg.la5min, self.myldavg.la15min))
            
            # Race condition here with self.count, but it's not critical (!?)
            #time.sleep(self.sleepquantum / max(1, self.count))
            # NOTE: this sleep value needs to be carefully tuned--
            # if < 1.0 seems to cause CPU usage to skyrocket...
            time.sleep(1.0)

        self.logger.info("Stopping remote object manager loop...")


#------------------------------------------------------------------
# MAIN PROGRAM
#
def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('mgrsvc', options)

    # Get the names of the nodes in this cluster and remove our name.  The
    # result is the list of hosts running name servers that we need to
    # synchronize with. 
    try:
        myhost = ro.get_myhost(short=True)

    except Exception, e:
        raise managerSvcError("Can't get my own hostname: %s" % str(e))

    authDict = {}
    if options.auth:
        auth = options.auth.split(':')
        authDict[auth[0]] = auth[1]

    stdout = None
    if options.stdout:
        if options.logdir:
            if options.logbyhostname:
                stdout = os.path.join(options.logdir, myhost, options.stdout)
            else:
                stdout = os.path.join(options.logdir, options.stdout)
        else:
            stdout = options.stdout
            
    # Start the manager service
    ms = remoteObjectManagerService(name='mgrsvc', port=options.port,
                                    usethread=True, logger=logger,
                                    stdout=stdout,
                                    authDict=authDict,
                                    secure=options.secure,
                                    cert_file=options.cert)

    # Simple signal handler to shutdown the world when we receive a signal
    def handler(signum, frame):
        logger.error('Signal handler called with signal', signum)
        ms.shutdown()

    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGHUP, handler)

    try:
        try:
            ms.ro_start()

            # Slave mode starts up slaves on other hosts
            #if options.ro_hosts:
            #    ms.bootup_slaves(options.ro_hosts)

            # Register ourselves
            #ms.register('mgrsvc', host, port)

            ms.ro_manager_loop()

        except KeyboardInterrupt:
            logger.error("Caught keyboard interrupt!")

    finally:
        logger.info("Remote object manager service stopping ...")

        # Shut down slaves
        #if options.ro_hosts:
        #    ms.shutdown_slaves(options.ro_hosts)

        # When we stop, everything we control stops!
        ms.shutdown()
        #ms.ro_stop()
        

    
if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("--auth", dest="auth",
                      help="Use authorization; arg should be user:passwd")
    optprs.add_option("--cert", dest="cert",
                      help="Path to key/certificate file")
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--detach", dest="detach", default=False,
                      action="store_true",
                      help="Detach from terminal and run as a daemon")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--hosts", dest="ro_hosts",
                      help="Use HOSTS for remote objects", metavar="HOSTS")
    optprs.add_option("--output", dest="stdout", metavar="FILE",
                      help="Direct subprocess stdout/stderr to FILE")
    optprs.add_option("--pidfile", dest="pidfile", metavar="FILE",
                      help="Write process pid to FILE")
    optprs.add_option("--port", dest="port", type="int",
                      default=ro.managerServicePort,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--secure", dest="secure", action="store_true",
                      default=False,
                      help="Use SSL encryption")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    if len(args) != 0:
        optprs.error("incorrect number of arguments")


    if options.detach:
        print "Detaching from this process..."
        sys.stdout.flush()
        try:
            child = myproc.myproc(main, args=[options, args],
                                  pidfile=options.pidfile, detach=True)
            child.wait()

            # TODO: check status of process and report error if necessary
        finally:
            sys.exit(0)

    # Are we debugging this?
    elif options.debug:
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

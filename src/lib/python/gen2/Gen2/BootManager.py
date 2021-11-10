#!/usr/bin/env python
#
# Gen 2 boot up script for distributed services.
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Apr 19 15:15:18 HST 2013
#]
#
#
"""BootManager -- bootstrapping facility for running Gen2 distributed over
a cluster of hosts.

Typical use:

STARTUP
=======
# show configurations
./BootManager.py --showconfigs

# start boot manager
./BootManager.py --config=solo

# Boot the remoteObjectsManager service on all cluster nodes.
bootmgr> boot()

# starts stage 1 (other remoteObjects infrastructure)
bootmgr> start(1)

# starts stage 2 (core services: status, Monitor, TaskManager)
bootmgr> start(2)

# starts stage 3 (interfaces and non-core services)
bootmgr> start(3)


SHUTDOWN
========
bootmgr> shutdown()

# Alternative: stop everything except manager service
bootmgr> stopall()


OTHER USEFUL COMMANDS
=====================

# Restart a specific service
bootmgr> restart('status')

# Stop a stage
bootmgr> stop(3)

# Restart a stage
bootmgr> restart(2)

# Clear the map on all hosts

bootmgr> clearall()

# Reload the config file
bootmgr> reloadConfig()

# loads the map defined by --config into all cluster hosts
bootmgr> setup()

# show all running services
bootmgr> sl()
"""
# remove once we're certified on python 2.6
from __future__ import with_statement

import sys, os
import signal
import socket, time
import threading
import random, re
# for command line interface:
import atexit, readline

import myproc
import remoteObjects as ro
import remoteObjects.Monitor as Monitor
import logging, ssdlog
import Bunch
    
# Version/release number
version = "20100317.0"


def makecmd(basedir, svcinfo, nodeinfo):
    """Form a command line to run from the _svcinfo_ dictionary.
    """

    if svcinfo.has_key('rundir'):
        rundir = svcinfo['rundir']
        # If running directory configured as absolute path then don't
        # prepend base directory to it
        if rundir.startswith('/') or rundir.startswith('$'):
            wrapper = '(cd %s; %%s)' % (rundir)
        else:
            wrapper = '(cd %s/%s; %%s)' % (basedir, rundir)
    else:
        wrapper = '(cd %s; %%s)' % (basedir)
        
    if svcinfo.has_key('cmddir'):
        cmddir = svcinfo['cmddir']
        cmd = '/'.join((cmddir, (svcinfo['start'] % svcinfo)))
    else:
        cmd = (svcinfo['start'] % svcinfo)

    return wrapper % cmd


def my_import(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


class BootError(Exception):
    """Class for errors thrown by boot manager.
    """
    pass

class BootErrorNoCmd(BootError):
    pass


class BootManager(object):
    """The BootManager class is used to manage a set of processes on a
    cluster of hosts via the remoteObjectManager service.  It provides
    methods for loading a configuration 'map' which describes the commands
    used to start processes and on which nodes they are allowed to run.
    BootManager reads this map and makes the appropriate calls to the
    remoteObjectManager running on each node to register the commands and
    start the processes.
    """
    
    def __init__(self, logger, mgrport=None, monsvc='monitor',
                 confpfx='cfg.bm.'):

        self.logger = logger
        self.confmodule = None
        self.confname = None
        self.confpfx = confpfx
        if not mgrport:
            mgrport = ro.managerServicePort
        self.mgrport = mgrport
        self.monsvc = monsvc
        self.get_disp = None
        
        self.dct = {
            'start': self.start,
            'stop': self.stop,
            'stage': self.stage,
            'tostage': self.tostage,
            'clearall': self.clearall,
            'stopall': self.stopall,
            }

        # Time to sleep between re-trying ro_echo calls when determining
        # if a service is up or down
        self.time_incr = 0.1

        # Current stage that we are at
        self.cur_level = -1

        # Periodic jobs table
        self.periodic = []
        # Interval to check for periodic jobs (in sec)
        self.check_interval = 5.0
        self.mon_update_interval = 10.0

        # for mutex
        self.lock = threading.RLock()


    # Need this because we don't inherit from ro.remoteObjectServer,
    # but are delegated to from it
    def ro_echo(self, arg):
        return arg


    def load(self, config):

        def populate(hostbnch):
            return ro.populate_host(hostbnch, def_user=os.environ['LOGNAME'],
                                    def_port=ro.managerServicePort)

        with self.lock:
            #self.hosts = map(fn, config.hosts)
            self.hosts = map(populate, config.managers.values())
            self.config = config
            try:
                dispfn = getattr(self.confmodule, 'get_disp')
                self.get_disp = dispfn(config)

            except Exception, e:
                self.logger.error("Error loading get_disp() function")
                self.get_disp = None

            # Make a bunch of handles to the ro manager service on all hosts.
            # The service may already be running or not.
            hostports = [(host.fqdn, host.port) for host in self.hosts]
            self.msb = ro.make_robunch('mgrsvc', hostports=hostports)

            # Get a handle to the NS, if one is up
            self.resetns()

            # Get list of periodic services and calculate starting times
            self.periodic = self.getSvcs(lambda info: info.has_key('periodic'))
            for svcname in self.periodic:
                svcinfo = self.get_svcinfo(svcname)
                self.calc_next_period(svcname, svcinfo)

            #print "ldconfig: %s" % str(self.config.svconfig.keys())
            return ro.OK


    def loadModule(self, moduleName):
        with self.lock:
            try:
                #self.confmodule = __import__(moduleName)
                self.confmodule = my_import(self.confpfx + moduleName)

            except ImportError:
                raise BootError("Can't load module '%s'" % moduleName)
        
            
    def loadConfig(self, configName):
        with self.lock:
            try:
                self.loadModule(configName)
                
                config = self.confmodule.config
                self.confname = configName

            except KeyError:
                raise BootError("No such named configuration '%s'" % configName)

            return self.load(config)
            
            
    def reloadConfig(self):
        with self.lock:
            reload(self.confmodule)
            config = self.confmodule.config

            return self.load(config)
            
            
    def getConfigs(self):
        if not self.confmodule:
            raise BootError("No module loaded")
        if not hasattr(self.confmodule, 'configs'):
            raise BootError("Module has no attribute 'configs'")

        raise BootError("This function has been deprecated")
        #return self.confmodule.configs.keys()

        
    def execute(self, cmd, args):
        try:
            cmd = cmd.strip().lower()
            func = self.dct[cmd]
        
        except KeyError, e:
            raise BootErrorNoCmd("Not a valid command: '%s'" % cmd)

        return func(*args)


    def clearall(self):
        """Clear all service names in all ro managers.
        """
        self.msb.all.clear()

        return ro.OK

        
    def stopall(self):
        """Stop any services that are already running.
        """
        return self.msb.all.stopall()


    def resetns(self):
        """Reset our handle to the ns.
        """
        # Get a generic handle to the nameserver(s)
        hosts = ro.unique_hosts(self.hosts)
        with self.lock:
            self.ns = ro.getns(hosts)

        return ro.OK

        
    def _boot(self, svcname):
        """Start local process (used mainly for remoteObjectManagerSvc).
        """

        hosts = self.getHosts(svcname)
        svcinfo = self.get_svcinfo(svcname)

        for hostbnch in hosts:
            #hostbnch = ro.split_host(host, def_user=os.environ['LOGNAME'])
            
            mgrcmd = makecmd(self.config.basedir, svcinfo, hostbnch)
            # escape $ for shell replacement
            #mgrcmd = mgrcmd.replace('$', '\\$')
        
            # Start manager service on each host
            cmdstr = "ssh %s@%s '%s'" % (
                hostbnch.user, hostbnch.fqdn, mgrcmd)
            self.logger.debug("Bootstrap command is '%s'" % (cmdstr))
            proc = myproc.myproc(cmdstr)
            #args = [ 'ssh', ('%s@%s' % (hostbnch.user, hostbnch.fqdn)),
            #         mgrcmd ]
            #self.logger.debug("Bootstrap command is '%s'" % (str(args)))
            #proc = myproc.myproc(args)
            res = proc.wait()

        # wait for mgrsvc to become available
        self.check_level_up_deadline(0, time.time() + 5.0)
        
        # Load configuration map into all nodes
        return self.setup()


    def boot(self):
        return self._boot('mgrsvc')

        
    def shutdown(self):
        """Shutdown all ro managers.
        """
        try:
            self.stopall()

        finally:
            return self.msb.all.shutdown()

        
    def start_host(self, hostkey, svcname):
        if not ':' in hostkey:
            hostkey = '%s:%d' % (socket.getfqdn(hostkey), ro.managerServicePort)
            
        self.msb[hostkey].start(svcname)
        runtime = self.msb[hostkey].gettime(svcname)
        count = 0
        while runtime <= 0 and count < 10:
            time.sleep(0.1)
            runtime = self.msb[hostkey].gettime(svcname)
            count += 1
        if count > 0:
            self.logger.info('BootManager waited %d times for %s runup on %s' % (count, svcname, hostkey))
        if not (runtime > 0):
            raise BootError("Service '%s' startup failed on host '%s' %f %f!" % (
                svcname, hostkey, runtime, self.msb[hostkey].gettime(svcname)))

    def _start_hostbunch(self, hostbnch, svcname):
        return self.start_host(hostbnch.key, svcname)
    
    def stop_host(self, hostkey, svcname):
        if not ':' in hostkey:
            hostkey = '%s:%d' % (socket.getfqdn(hostkey), ro.managerServicePort)
            
        self.msb[hostkey].stop(svcname)
        if (self.msb[hostkey].gettime(svcname) > 0):
            raise BootError("Service '%s' sthutdown failed on host '%s'!" % (
                svcname, hostkey))

    def _stop_hostbunch(self, hostbnch, svcname):
        return self.stop_host(hostbnch.key, svcname)

    def restart_host(self, hostkey, svcname):
        self.stop_host(hostkey, svcname)
        self.start_host(hostkey, svcname)


    def start(self, svcname):
        """Start service(s) associated with _svcname_.
        """

        # If argument is an int, then they are trying to start a stage,
        # not a specific process
        if type(svcname) in (int, long, float):
            return self.stage(svcname, 'start')
            
        svcinfo = self.get_svcinfo(svcname)
        # Level 0 is special
        if svcinfo['level'] == 0:
            return self._boot(svcname)

        start_flags = svcinfo.get('flags', [])

        hosts = self.getHosts(svcname)

        if 'random' in start_flags:
            # Start the service on random hosts
            count = svcinfo['count']
            while count > 0:
                idx = random.randint(0, len(hosts)-1)
                random_hostbnch = hosts[idx]
                host = random_hostbnch.key

                self.start_host(host, svcname)
                count -= 1

        else:
            # If no special flags then start a copy of the service
            # on each host until count is reached
            count = svcinfo['count']
            idx = 0
            while (count > 0) and (idx < len(hosts)):
                hostbnch = hosts[idx]
                host = hostbnch.key
                idx += 1
                try:
                    self.start_host(host, svcname)
                    count -= 1
                    
                except BootError, e:
                    self.logger.warn("Failed to start service '%s' on preferred host %s: %s" % (
                        svcname, host, str(e)))
                                         
            if count > 0:
                raise BootError("Service '%s' startup failed, count=%d" % (
                    (svcname, count)))

        return ro.OK


    def stop(self, svcname):
        """Stop service(s) associated with _svcname_.
        """
        # If argument is an int, then they are trying to start a stage,
        # not a specific process
        if type(svcname) in (int, long, float):
            return self.stage(svcname, 'stop')
            
        svcinfo = self.get_svcinfo(svcname)
        if svcinfo['level'] == 0:
            # TODO: allow level 0 to be shutdown individually
            return self.shutdown()

        else:
            # TODO: log/signal errors shutting down!!
            for hostbnch in self.getHosts(svcname):
                host = hostbnch.key
                self.stop_host(host, svcname)

        return ro.OK

        
    def restart(self, svcname):
        """Restart service(s) associated with _svcname_.
        """
        # If argument is an int, then they are trying to start a stage,
        # not a specific process
        if type(svcname) in (int, long, float):
            return self.stage(svcname, 'restart')
            
        self.stop(svcname)
        self.start(svcname)

        return ro.OK
        
        
    def get_svcinfo(self, svcname):
        try:
            return self.config.svconfig[svcname]

        except KeyError:
            raise BootError("No such service found: '%s'" % svcname)
        
        
    def getSvcs(self, info_cmp):
        """Return all the service names that match a given criteria.
        """
        svconfig = self.config.svconfig
        res = []

        # Iterate over service configuration data
        for svcname in svconfig.keys():
            info = svconfig[svcname]

            if info_cmp(info):
                res.append(svcname)

        return res

        
    def get_levels(self):
        """Gets the list of levels in the current configuration."""
        res = []
        for (key, svcinfo) in self.config.svconfig.items():
            if svcinfo['level'] not in res:
                res.append(svcinfo['level'])
        res.sort()

        return res

        
    def getHosts(self, svcname):
        """Get all the keys for each remoteObjectManagerSvc instance
        that this service runs under.
        """
##         def fn(host):
##             # returns a Bunch of attributes about the host:
##             # *.{ host, fqdn, port, user, key, etc. }
##             return ro.split_host(host, def_user=os.environ['LOGNAME'],
##                                  def_port=ro.managerServicePort)

        svcinfo = self.get_svcinfo(svcname)

        # Makes a list of bunches
        bnchs = [ self.config.managers[key] for key in svcinfo['hosts'] ]
        return bnchs
    
        
    def check_ns(self, svcname):
        """Returns the instances of _svcname_ registered with the
        name servers.  Raises a BootError if we cannot communicate with the
        name server. 
        """
        try:
            res = self.ns.getHosts(svcname)
            return res
        
        except ro.remoteObjectError, e:
            raise BootError("Name service unavailable")
                    

    def check_ns_registered(self, svcname):
        """Returns the number of instances of _svcname_ registered with the
        name server.  Raises a BootError if we cannot communicate with the
        name server. 
        """
        try:
            res = self.check_ns(svcname)
            return len(res)
        
        except ro.remoteObjectError, e:
            raise BootError("Name service unavailable")
                    

    def check_ns_registered_deadline(self, svcname, deadline, count=1):
        """Like check_ns_registered(), but keeps checking until the
        specified count is reached or the time == _deadline_.
        """
        num = 0
        while (num < count) and (time.time() < deadline):
            try:
                num = self.check_ns_registered(svcname)
                if num < count:
                    # Sleep a teeny bit and try again
                    time.sleep(self.time_incr)

            except BootError, e:
                # Name service may be coming up, wait a bit and try again
                time.sleep(self.time_incr)
                
        return num


    def get_spall(self, svcname):
        # Special case: ro manager service
        if svcname == 'mgrsvc':
            return self.msb.all

        hostports = self.ns.getHosts(svcname)
        if len(hostports) == 0:
            raise BootError("Service %s not registered anywhere" % svcname)

        return ro.remoteObjectSPAll(svcname, hostports=hostports)

        
    def check_svc(self, sp):
        echoval = 99
        count = 0

        results = sp.ro_echo(echoval)
        for ((host, port), (res, val)) in results.items():
            if res == 0:
                count += 1

        #print "check_svc: %d, %s" % (count, str(results))
        return count


    def check_svc_up_deadline(self, svcname, deadline):
        svcinfo = self.get_svcinfo(svcname)
        if svcinfo['level'] > 0:
            count = self.check_ns_registered_deadline(svcname, deadline,
                                                      count=svcinfo['count'])
            if count < svcinfo['count']:
                raise BootError("Service (%s) unavailable by deadline" % \
                                    (svcname))
        
        sp = self.get_spall(svcname)
        timestart = time.time()
        done = False
        while not done and (time.time() < deadline):
            try:
                if self.check_svc(sp) >= svcinfo['count']:
                    done = True
                    continue

            except ro.remoteObjectError, e:
                pass

            # Sleep a teeny bit and try again
            time.sleep(self.time_incr)

        if not done:
            raise BootError("Service (%s) unavailable by deadline" % \
                            (svcname))

        return ro.OK
        

    def check_svcs_up_deadline(self, svcnames, deadline):

        # Check remoteObjects service response
        for svcname in svcnames:
            svcinfo = self.get_svcinfo(svcname)
            if 'nosvccheck' in svcinfo['flags']:
                continue
            
            self.check_svc_up_deadline(svcname, deadline)

            
    def check_svc_down_deadline(self, svcname, deadline):
        svcinfo = self.get_svcinfo(svcname)

        # NOTE [2]: there is a race condition here with the name service
        # which may drop the name (since it has been killed) before
        # we can get a handle to the (now) non-existent services
        sp = self.get_spall(svcname)
        timestart = time.time()
        done = False
        while not done and (time.time() < deadline):
            try:
                if self.check_svc(sp) == 0:
                    done = True
                    continue

            except ro.remoteObjectError, e:
                pass

            # Sleep a teeny bit and try again
            time.sleep(self.time_incr)

        if not done:
            raise BootError("Service (%s) still available by deadline" % \
                            (svcname))

        # Currently, service names take a little while to drop
        # out of the name servers
##         if svcinfo['level'] > 0:
##             count = self.check_ns_registered_deadline(svcname, deadline,
##                                                       count=svcinfo['count'])
##             if count > 0:
##                 raise BootError("Service (%s) still available by deadline" % \
##                                 (svcname))
        
        return ro.OK
        

    def check_svcs_down_deadline(self, svcnames, deadline):
        # Check remoteObjects service response
        for svcname in svcnames:
            svcinfo = self.get_svcinfo(svcname)
            if 'nosvccheck' in svcinfo['flags']:
                continue

            # Will raise exception if don't meet deadline
            self.check_svc_down_deadline(svcname, deadline)

        return ro.OK

            
    def check_procs_up_deadline(self, svcnames, deadline):
        done = False
        while not done and (time.time() < deadline):
            try:
                uptimes = self.uptime(svcnames)

                for svcname in svcnames:
                    d = uptimes[svcname]

                    svcinfo = self.get_svcinfo(svcname)

                    # Check count of reported processes
                    count = len(d.keys())
                    if count != svcinfo['count']:
                        raise BootError("Process counts don't match for service '%s': %d (actual) != %d (config)" % (
                            svcname, count, svcinfo['count']))

                    # Check individual uptimes
                    for (host, uptime) in d.items():
                        if not (uptime > 0):
                            raise BootError("Uptime=%.2f for service '%s', host %s" % (
                            uptime, svcname, host))

                # Made it through all service names/hosts!
                done = True

            except BootError, e:
                pass

            # Sleep a teeny bit and try again
            time.sleep(self.time_incr)

        if not done:
            # TODO: Could stand some better error reporting here
            raise BootError("Processes for (%s) not up by deadline" % \
                            (str(svcnames)))

        return ro.OK
        

    def check_procs_down_deadline(self, svcnames, deadline):
        done = False
        while not done and (time.time() < deadline):
            try:
                uptimes = self.uptime(svcnames)

                for svcname in svcnames:
                    d = uptimes[svcname]

                    svcinfo = self.get_svcinfo(svcname)

                    # Check count of reported processes
                    count = len(d.keys())
                    if count != svcinfo['count']:
                        raise BootError("Process counts don't match for service '%s': %d (actual) != %d (config)" % (
                            svcname, count, svcinfo['count']))

                    # Check individual uptimes
                    for (host, uptime) in d.items():
                        if not (uptime == 0):
                            raise BootError("Uptime=%.2f for service '%s', host %s" % (
                            uptime, svcname, host))

                # Made it through all service names/hosts!
                done = True

            except BootError, e:
                pass

            # Sleep a teeny bit and try again
            time.sleep(self.time_incr)

        if not done:
            # TODO: Could stand some better error reporting here
            raise BootError("Processes for (%s) not down by deadline" % \
                            (str(svcnames)))

        return ro.OK
        

    def check_level_up_deadline(self, level, deadline):
        
        # Iterate over service configuration data
        svcnames = self.getSvcs(lambda info: info['level'] == level)

        # Check processes
        # Manager service runs in level 0 and check_procs_up_deadline
        # uses the manager service
        if level > 0:
            self.check_procs_up_deadline(svcnames, deadline)

        self.check_svcs_up_deadline(svcnames, deadline)

        return ro.OK
        

    def check_level_down_deadline(self, level, deadline):
        
        # Iterate over service configuration data
        svcnames = self.getSvcs(lambda info: info['level'] == level)

        # Name service is level 1, and check_svcs_down_deadline
        # uses the name service
        # See NOTE [2] ABOVE
        #if level > 1:
        #    self.check_svcs_down_deadline(svcnames, deadline)

        # Check processes
        # Manager service runs in level 0 and check_procs_down_deadline
        # uses the manager service
        if level > 0:
            self.check_procs_down_deadline(svcnames, deadline)

        return ro.OK
        

    def which_stage(self):
        """Determine the highest level stage that has all stages
        below it completely up."""

        levels = self.get_levels()
        self.logger.debug("Determining current stage for levels: %s" % (
            str(levels)))
        
        last_good = -1

        try:
            for level in levels:
                self.logger.debug("Checking level %d..." % level)
                deadline = time.time() + 1.0
                self.check_level_up_deadline(level, deadline)

                last_good = level

        except BootError, e:
            pass
            
        self.logger.debug("Current stage is %d" % last_good)
        return last_good

    
    def stage(self, level, action):
        services = self.getSvcs(lambda info: info['level'] == level)
        self.logger.debug("Stage %d services affected: %s" % (
            level, str(services)))
        
        # Iterate over service configuration data
        for svcname in services:

            if action == 'start':
                self.start(svcname)

            elif action == 'stop':
                self.stop(svcname)
                
            elif action == 'restart':
                self.stop(svcname)
                self.start(svcname)
                
            else:
                raise BootError("Don't understand action '%s'" % action)

        return ro.OK
                

    def down2stage(self, stage):
        """Stop all stages above (stage)."""
        levels = self.get_levels()
        levels.reverse()

        self.logger.debug("Stopping all stages above %d" % stage)
        for level in levels:
            if level > stage:
                self.stage(level, 'stop')
                
                deadline = time.time() + 10.0
                self.check_level_down_deadline(level, deadline)

        return ro.OK

        
    # THIS BREAKS WITH NON-INTEGER LEVELS
    # TODO: FIX!!
    def tostage(self, stage, delta=20.0):
        if self.cur_level < stage:
            # Current stage is less than desired stage
            level = self.cur_level + 1
            while level <= stage:
                self.stage(level, 'start')

                # Check for all services up by deadline
                # (will raise an exception if not)
                deadline = time.time() + delta
                self.check_level_up_deadline(level, deadline)

                # Advance notion of current stage
                self.cur_level = level
                level += 1

        elif self.cur_level > stage:
            # Current stage is greater than desired stage
            level = self.cur_level
            while level > stage:
                self.stage(level, 'stop')
                
                deadline = time.time() + delta
                self.check_level_down_deadline(level, deadline)

                level -= 1
                self.cur_level = level

        else:
            self.warn("Methinks I'm already at stage %d" % stage)
            self.warn("If not, maybe a reset() would help")

        return ro.OK

        
    def reset(self):
        """Reset our idea of the current valid stage."""

        # Find out highest valid stage
        self.cur_level = self.which_stage()

        # Take down everything above it.
        self.down2stage(self.cur_level)

        return self.which_stage()

        
    def setup(self):
        # Load up all the programs we need to start into the respective
        # ro managers
        svconfig = self.config.svconfig
        basedir  = self.config.basedir
        
        for svcname in svconfig.keys():
            #print '*** %s ***' % svcname.upper()
            svcinfo = svconfig[svcname]

            hosts = self.getHosts(svcname)
            #self.logger.debug("hosts for '%s' are %s" % (
            #                   svcname, str(hosts)))
                
            # Contact each host that this service is configured to run on
            # and add the info
            for hostbnch in hosts:

                # Form command line to be executed
                start_cmd = makecmd(basedir, svcinfo, hostbnch)
                cmdDict = {}
                cmdDict['start'] = start_cmd

                # TODO: stop_cmd should have the same wrapping semantics
                copyDict(cmdDict, svcinfo, ('stop', 'stdout', 'stderr'))

                # If user specified stdout but not stderr, then share
                if cmdDict.has_key('stdout') and (not cmdDict.has_key('stderr')):
                    cmdDict['stderr'] = cmdDict['stdout']

                self.logger.debug("Pushing out service info for '%s' to %s" % (
                    svcname, hostbnch.key))
                self.logger.debug("cmdDict=%s" % (cmdDict))

                # TODO: need to try--catch here
                try:
                    self.msb[hostbnch.key].add_with_output(svcname, cmdDict)
                except Exception as e:
                    self.logger.error("Error pushing out to %s: %s" % (
                            hostbnch.key, str(e)))

        return ro.OK
            
            
    def uptime(self, svcnames):
        """Show the uptime for each service on each host.  _svcnames_ is
        either a single service name or a list of service names.
        If _svcnames_==[] then show all services.
        """
        svconfig = self.config.svconfig

        if type(svcnames) == type(""):
            svcnames = [svcnames]
        if len(svcnames) == 0:
            svcnames = svconfig.keys()

        res = {}
        for svcname in svcnames:
            hosts = self.getHosts(svcname)

            d = {}
            res[svcname] = d
            for hostbnch in hosts:
                try:
                    d[hostbnch.key] = self.msb[hostbnch.key].gettime(svcname)
#                     self.logger.debug("results for %s/%s: %f" % (hostbnch.key,
#                                                                  svcname,
#                                                                  d[hostbnch.key]))

                except ro.remoteObjectError, e:
#                     self.logger.warn("ERROR for host %s/%s: %s" % (hostbnch.key,
#                                                                    svcname,
#                                                                    str(e)))
                    d[hostbnch.key] = 'ERROR'

        return res
        #return ro.OK
            
            
    def procinfo(self, svcname):
        """Returns process information for service name _svcname_, culled
        from the /proc filesystem by the manager service.
        """
        svcnames = [svcname]
        res = {}
        for svcname in svcnames:
            hosts = self.getHosts(svcname)

            d = {}
            res[svcname] = d
            for hostbnch in hosts:
                try:
                    d[hostbnch.key] = self.msb[hostbnch.key].getProcInfo(svcname)
#                     self.logger.debug("results for %s/%s: %s" % (hostbnch.key,
#                                                                  svcname,
#                                                                  str(d[hostbnch.key])))

                except ro.remoteObjectError, e:
#                     self.logger.warn("PROCINFO: ERROR for host %s/%s: %s" % (hostbnch.key,
#                                                                              svcname,
#                                                                              str(e)))
                    d[hostbnch.key] = 'ERROR'

        return res


    def ldavg(self):
        """Returns the load averages of all the hosts in the cluster.
        """
        ans = self.msb.all.getLoadAvg()

        result = {}
        for key in ans.keys():
            (host, port) = key

            (res, d) = ans[key]
            result[host] = (d['la1min'], d['la5min'], d['la15min'])

        return result

    
    def sl_info(self):

        svconfig = self.config.svconfig
        
        svcs = self.uptime([])
        res = []
        keys = svcs.keys()
        keys.sort()
        for svcname in keys:
            svc_d = svcs[svcname]
            hosts = svc_d.keys()
            hosts.sort()
            for host in hosts:
                match = re.match(r'^([-_\w]+)\..+$', host)
                if match:
                    hostname = match.group(1)
                else:
                    hostname = host

                uptime = svc_d[host]
                level  = svconfig[svcname]['level']

                # Return a list of dicts of the results
                d = {'svcname': svcname,
                     'level': level,
                     'hostname': hostname,
                     'uptime': uptime,
                     }
                res.append(d)

        return res
            
            
    def sl(self, sortkey='level'):
        """Like uptime, but doesn't take any arguments.  Returns a long
        formatted string showing the uptime for various services.
        """

        fmt_svc = "%16.16s  %6.2f %12.12s   %s"

        if not sortkey in ('level', 'uptime', 'svcname', 'hostname'):
            raise BootError("Illegal sort key: '%s'" % sortkey)
        
        data = self.sl_info()

        # Sort the data according to the selected column
        data.sort(lambda x, y: cmp(x[sortkey], y[sortkey]))

        res = []
        for d in data:
            # Interpret data more user-friendly than just seconds up
            uptime = d['uptime']
            if not isinstance(uptime, float):
                d['uptime_r'] = 'N/A'

            elif uptime <= 0:
                d['uptime_r'] = 'NOT RUNNING'

            elif uptime < 60.0:
                d['uptime_r'] = '%.2f secs' % uptime

            elif uptime < 3600.0:
                d['uptime_r'] = '%.2f mins' % (uptime/60.0)

            elif uptime < 86400.0:
                d['uptime_r'] = '%.2f hours' % (uptime/3600.0)

            elif uptime < 604800.0:
                d['uptime_r'] = '%.2f days' % (uptime/86400.0)

            elif uptime < 31449600.0:
                d['uptime_r'] = '%.2f weeks' % (uptime/604800.0)

            else:
                d['uptime_r'] = '%.2f years' % (uptime / 31449600.0)
                
            res.append(fmt_svc % (d['svcname'], d['level'],
                                  d['hostname'], d['uptime_r']))

        return '\n'.join(res)
            

    def calc_next_period(self, svcname, svcinfo):
        time_fn = svcinfo['periodic']
        try:
            time_fn(self, svcinfo)
            if svcinfo.has_key('time_next'):
                next_time = svcinfo['time_next']
                if not isinstance(next_time, float):
                    self.logger.error("Periodic service time calculation for '%s' did not return a float: %s" % (
                        svcname, str(next_time)))
                else:
                    self.logger.info("Next run of '%s' will be %s" % (
                        svcname, time.ctime(next_time)))
        except Exception, e:
            self.logger.error("Periodic service time calculation for '%s' raised exception: %s" % (
                    svcname, str(e)))


    def update_monitor_loop(self, logger):
        """Updates the monitor periodically with data about processes.
        """

        # TODO: move this somewhere else, and pass in.
        ev_quit = threading.Event()
        channels = ['bootmgr']
        self.mon = Monitor.Monitor('bootmgr.mon', logger, numthreads=20)
        self.mon.publish_to(self.monsvc, ['bootmgr', 'logs'], {})
        
        self.mon.start(wait=True)
        tag = 'mon.bootmgr.uptime'

        try:
            while not ev_quit.isSet():
                start_time = time.time()
                deadline = start_time + self.check_interval

                # Check for periodic services to run
                for svcname in self.periodic:
                    svcinfo = self.get_svcinfo(svcname)
                    try:
                        next_time = svcinfo['time_next']
                    except KeyError:
                        self.calc_next_period(svcname, svcinfo)
                        if not svcinfo.has_key('time_next'):
                            self.logger.debug("No element 'time_next' in periodic service '%s'" % (
                                    svcname))
                            continue
                        next_time = svcinfo['time_next']

                    if time.time() < next_time:
                        # too early to run this job
                        continue

                    del svcinfo['time_next']
                    # Calculate next time to run this job
                    self.calc_next_period(svcname, svcinfo)

                    # Try to run the job
                    try:
                        self.start(svcname)
                            
                    except Exception, e:
                        self.logger.error("Error starting periodic task '%s': %s" % (
                            svcname, str(e)))

                # Update monitor with uptime information
                if int(start_time % self.mon_update_interval) == 0:
                    #self.logger.info("updating monitor!")
                    svcs = self.uptime([])
                    self.mon.update(tag, svcs, channels)

                # Wait until next interval
                wait_time = deadline - time.time()
                if wait_time > 0:
                    ev_quit.wait(wait_time)
                else:
                    self.logger.warn("Missed deadline (%s) by %.3f sec" % (
                            time.asctime(time.localtime(deadline)), abs(wait_time)))
        finally:
            self.mon.stop(wait=True)
            
            
def cmdline(options, bm):
    
    histfile = os.path.join(os.environ['HOME'], '.bmhist')
    try:
        # load the history file
        readline.read_history_file(histfile)
        
    except IOError:
        pass
    # Write out history file when the program terminates
    atexit.register(readline.write_history_file, histfile)

    try:
        while True:
            cmd = raw_input('bootmgr> ')
            if len(cmd) == 0:
                continue
            try:
                print eval("bm." + cmd)
                
            except (EOFError, KeyboardInterrupt), e:
                raise e

            except Exception, e:
                print str(e)
                continue

    except (EOFError, KeyboardInterrupt):
        print ""
        pass


def service(options, bootmgr, logger):

    # Initialize remote objects subsystem.
    try:
        ro.init()

    except ro.remoteObjectError, e:
        logger.error("Error initializing remote objects subsystem: %s" % str(e))
        sys.exit(1)

    # Encapsulate our remote object interface as a simple class
    # 
    class roInterface(ro.remoteObjectServer):

        def __init__(self, svcname, usethread=False):
            self.ev_quit = threading.Event()

            self.bm = bootmgr

            # Superclass constructor
            ro.remoteObjectServer.__init__(self, svcname=svcname,
                                           obj=self.bm, logger=logger,
                                           port=options.port,
                                           ev_quit=self.ev_quit,
                                           usethread=usethread)

            #self.bm.start()


    # Create our remote service object
    svc = roInterface(options.svcname, usethread=True)

    # Start it
    try:
        logger.info("Starting Boot Manager service...")
        try:
            svc.ro_start()

            bootmgr.update_monitor_loop(logger)

        except KeyboardInterrupt:
            logger.error("Caught keyboard interrupt!")

    finally:
        logger.info("Boot Manager service shutting down...")
        svc.ro_stop()


def copyDict(dst_dct, src_dct, keys):
    for key in keys:
        if src_dct.has_key(key):
            dst_dct[key] = src_dct[key]


def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('bootmgr', options)

    # Create the boot manager
    bootmgr = BootManager(logger, mgrport=options.mgrport,
                          monsvc=options.monitor,
                          confpfx=options.confpfx)

    # Show possible configurations
    # NOTE: this won't work unless a module is loaded
    if options.showconfigs:
        print "Available configurations: %s" % str(bootmgr.getConfigs())
        sys.exit(0)

    if options.configname:
        # Try to load the specified config
        try:
            bootmgr.loadConfig(options.configname)

        except BootError, e:
            print str(e)
            print "Available configurations: %s" % str(bootmgr.getConfigs())
            sys.exit(1)
        
        # Overriding set of hosts.  This is probably not a good idea in the
        # general case (and will only work if we have a config loaded)
##         if options.hosts:
##             rohosts = options.hosts.split(',')
##             bootmgr.config.hosts = rohosts
##             bootmgr.load(bootmgr.config)

    # If we are asked to run as a service, do so
    if options.svcname:
        service(options, bootmgr, logger)
        
    # If there are command line arguments (after stripping options)
    # then treat them as a command and try to execute it.  Otherwise
    # enter an interactive command line shell.
    elif len(args) > 0:
        try:
            print "Executing %s" % args[0]
            bootmgr.execute(args[0], args[1:])

        except BootErrorNoCmd, e:
            print "'%s' isn't a command I understand." % args[0]
            sys.exit(1)

    else:
        cmdline(options, bootmgr)
        
    sys.exit(0)

    
if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options] command [args]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("--config", dest="configname", default=None,
                      metavar="NAME",
                      help="Use configuration with name=NAME for setup")
    optprs.add_option("--confpfx", dest="confpfx", default='cfg.bm.',
                      metavar="PACKAGE",
                      help="Use python package PACKAGE for loading configs")
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--hosts", dest="hosts",
                      help="Override hosts configuration (careful)",
                      metavar="HOSTS")
    optprs.add_option("--mgrport", dest="mgrport", type="int", default=None,
                      help="Use manager service on port NUM", metavar="NUM")
    optprs.add_option("-m", "--monitor", dest="monitor", default='monitor',
                      metavar="NAME",
                      help="Supply feed to monitor service NAME")
    optprs.add_option("--port", dest="port", type="int", default=None,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("-s", "--showconfigs", dest="showconfigs", default=False,
                      action="store_true",
                      help="Show available configurations")
    optprs.add_option("--svcname", dest="svcname", metavar="NAME",
                      help="Register using NAME as service name")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])


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

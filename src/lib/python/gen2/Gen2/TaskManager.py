#!/usr/bin/env python
#
# TaskManager.py -- implements the OCS Gen2 Task Manager.
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Jan  4 17:18:45 HST 2013
#]
#
 
import sys, os

# --- TEMP, until we figure out configuration issues ---
# TODO: parameterize!
obshome = os.environ['OBSHOME']

# Add personal Tasks directory
personalHome = '%s/Tasks' % (os.environ['HOME'])
sys.path.insert(1, personalHome)
# ------------------------------------------------------


import re, signal
import threading
# for command line interface:
import os, atexit, readline
#optparse imported below (if needed)
import glob, time
import imp

import Task
# so we can import g2Task and skTask
sys.path.insert(1, '%s/COMMON/task' % (obshome))
import g2Task, skTask

import SOSS.DotParaFiles.ParaValidator as ParaValidator
import SOSS.parse.sk_interp as sk_interp
#import SOSS.parse.CommandParser as CommandParser
#import Session
from cfg.INS import INSdata as INSconfig

import remoteObjects as ro
import remoteObjects.Monitor as Monitor
import Bunch
import ssdlog, logging

serviceName = 'taskmgr0'

# Version/release number
version = "20100319.0"


# CODE NOTES
# ==========
# [1] Items marked with this note probably should be in a critical section,
# if the remote object server ever supports more than one thread, since they
# involve modifying the task manager's state.  In the current implementation
# of remoteObjects, only one thread handles calls to a remoteObjectServer's
# methods, so this is not an issue.
#

# Prefix used in monitor reporting for tasks.
# TODO: get this from the session/environment
tm_mon_pfx = "mon.tasks"


class TagGenerator(object):
    """Generates tags for tasks running under the TaskManager.
    """

    def get_tag(self, taskobj):
        """Get a unique tag (seq num) for a task.  The task counter is bumped
        and the value interpolated into a template.
        """

        # Obtain a new tag (event unique id)
        num = time.time()

        num_s = ('%.7f' % num).replace('.', '-')
        #num_s = ('%d' % num)

        # Generate task tag.  Try to render something readable by extracting
        # the class name of the task.  If we fail, just make the tag the
        # sequence number of the task.
        try:
            if hasattr(taskobj, 'name'):
                tag = taskobj.name + '-' + num_s
                
            else:
                name = repr(taskobj.__class__)
                match = re.match("^<class '([^']+)'>$", name)
                if not match:
                    tag = num_s
                else:
                    className = match.group(1)
                    tag = className.split('.')[-1] + '-' + num_s
            
        except:
            tag = num_s
        return tag


class TaskManagerError(Exception):
    """Class of exceptions raised for errors generated in the task manager.
    """
    pass


class TaskManager(object):
    """This is the TaskManager.
    """

    def __init__(self, logger=None, ev_quit=None, dbpath='taskmgr-db',
                 threadPool=None, numthreads=50, internal_allocs=None,
                 identity=serviceName, monitor='monitor'):

        self.myname = identity
        self.myMonName = ('%s.mon' % self.myname)
        self.mainMonName = monitor

        # For instrument information
        self.insconfig = INSconfig()
        
        # Handles for subsystems.  Is set/reset by setAllocs() method.
        self.alloc = Bunch.threadSafeBunch()
        #self.alloc = {}

        # Dictionary-compat object of 'internal' allocations (local objects to
        # the TaskManager process)
        if internal_allocs:
            self.internal_allocs = internal_allocs
        else:
            self.internal_allocs = {}

        self.internal_allocs['taskmgr'] = self

        # If no logger is passed in, create a simple one to stderr
        if not logger:
            logger = logging.getLogger(self.myname)
            logger.setLevel(logging.ERROR)
            fmt = logging.Formatter(ssdlog.STD_FORMAT)
            stderrHdlr = logging.StreamHandler()
            stderrHdlr.setFormatter(fmt)
            logger.addHandler(stderrHdlr)
        self.logger = logger

        if not ev_quit:
            ev_quit = threading.Event()
        self.ev_quit = ev_quit

        self.numthreads = numthreads

        # If we were passed in a thread pool, then use it.  If not,
        # make one.  Record whether we made our own or not.
        if threadPool != None:
            self.threadPool = threadPool
            self.mythreadpool = False

        else:
            self.threadPool = Task.ThreadPool(logger=self.logger,
                                              ev_quit=self.ev_quit,
                                              numthreads=self.numthreads)
            self.mythreadpool = True
        
        # If we were handed a monitor then use it, otherwise create a
        # minimon (will be synced to by external monitor)
        if self.internal_allocs.has_key('monitor'):
            self.monitor = self.internal_allocs['monitor']
            self.mymonitor = False
        else:
            self.monitor = Monitor.Minimon(self.myMonName, self.logger,
                                           useSync=False,
                                           threadPool=self.threadPool)
            self.mymonitor = True
            self.internal_allocs['monitor'] = self.monitor

        # Our list of loaded modules
        self.modules = Bunch.threadSafeBunch()
        # Our directory mapping subsystems and task class names
        self.taskdir = Bunch.threadSafeBunch(caseless=True)
        self.taskdir[''] = Bunch.threadSafeBunch(caseless=True)

        # Generates tags for tasks
        self.tagger = TagGenerator()

        # Used for validating subsystem commands
        self.validator = ParaValidator.ParaValidator(self.logger)

        # For loading skeleton files
        self.sk_bank = sk_interp.skBank(obshome)

        # TODO: this value should be parameterized
        self.channels = [self.myname]

        # Default variables we will share with child tasks
        self.shares = ['logger', 'threadPool', 'alloc', 'shares', 'tagger',
                       'monitor', 'validator', 'channels', 'insconfig',]

        # Top level tag that all my tasks will appear underneath in the monitor
        self.tag = ('mon.tasks.%s' % self.myname)
        self.qtask = {}

        self.topTags = []

    def getName(self):
        return self.myname
    
    def start(self, wait=True):
        """Start the task manager.
        This method creates a fresh thread pool and starts it, and creates
        a single compound task that executes tasks concurrently from a
        queue.
        """
        # Start our thread pool (if we created it)
        if self.mythreadpool:
            self.threadPool.startall(wait=True)

        # Start monitor (if we created it)
        if self.mymonitor:
            self.monitor.start(wait=True)
            self.monitor.start_server(wait=True, usethread=True)

            ro.init()
            
            # Subscribe to g2task from main monitor feed
            self.monitor.subscribe_remote('monitor', ['g2task'], {})

            # Publish our feeds to the main monitor
            monchannels = [self.myname]
            self.monitor.publish_to('monitor', monchannels, {})

        self.start_sktask_environment()
        
        self.logger.debug("start completed")
        
        
    def stop(self, timeout=10.0, wait=True):
        """Stop the task manager.
        This method attempts to stop the top-level task and then stops the
        thread pool.
        """
        self.reset()
        
        self.logger.debug("Stopping top level task.")
        self.qtask['top'].stop()
        self.logger.debug("Waiting for top level task.")
        try:
            self.qtask['top'].wait(timeout=timeout)

        except Task.TaskTimeout, e:
            self.logger.error("Timed out waiting for top level task.")
        
        except Exception, e:
            self.logger.error("Top level task died with exception: %s" % \
                              str(e))
        
        # Stop monitor (if we created it)
        if self.mymonitor:
            self.monitor.stop(wait=wait)

        # Stop thread pool (if we created it)
        if self.mythreadpool:
            self.threadPool.stopall(wait=wait)

        self.logger.debug("stop completed")


    def restart(self):
        """Restart the task manager.
        """
        self.stop()

        self.start()

        
    def get_threadPool(self):
        return self.threadPool
    
    def get_monitor(self):
        return self.monitor
    

    def start_sktask_environment(self):
        # Create one queue and cancel/pause mechanism for the
        # "regular" dispatcher .  This also has a shared sklock mutex
        # for handling overlapping commands (preprocessing and
        # postprocessing sections)
        queue = Task.PriorityQueue()
        ev_cancel = threading.Event()
        ev_pause = threading.Event()
        sklock = threading.Lock()

        # Create two executor tasks in this environment
        t1 = skTask.skExecutorTask(queue, ev_quit=self.ev_quit,
                                   ev_cancel=ev_cancel, ev_pause=ev_pause,
                                   sklock=sklock, waitflag=True)
        t2 = skTask.skExecutorTask(queue, ev_quit=self.ev_quit,
                                   ev_cancel=ev_cancel, ev_pause=ev_pause,
                                   sklock=sklock, waitflag=True)

        # Separate queue, pause and cancel for the "interactive"
        # dispatcher
        queue = Task.PriorityQueue()
        ev_cancel = threading.Event()
        ev_pause = threading.Event()

        # Create one task for this (but it doesn't wait on the tasks)
        t3 = skTask.skExecutorTask(queue, ev_quit=self.ev_quit,
                                   ev_cancel=ev_cancel, ev_pause=ev_pause,
                                   sklock=None, waitflag=False)

        self.qtask['executer'] = t1
        #self.qtask['executer2'] = t2
        self.qtask['launcher'] = t3
        # Create a concurrent task to "drive" all the dispatchers
        self.qtask['top'] = Task.ConcurrentAndTaskset([t1, t2, t3])

        self.qtask['top'].init_and_start(self)


    def release(self, tag):
        """Release all tasks waiting on _tag_ in the monitor.
        """
        self.logger.info("Releasing all tasks waiting on '%s'" % tag)
        self.monitor.release(tag)

        
    def releaseAll(self):
        """Release all tasks waiting on the monitor.
        """
        self.logger.info("Releasing all tasks waiting on monitor.")
        self.monitor.releaseAll()

        
    def reset(self, queueName='executer'):
        """Flushes any pending tasks and releases any tasks waiting in
        the monitor.
        """
        self.logger.info("Flushing task queues")
        if self.qtask[queueName]:
            self.qtask[queueName].flush()
        # TODO: kill concurrent top level tasks!
            
        self.monitor.releaseAll()

        
    def cancel(self, queueName):
        self.logger.info("Trying to cancel tasks in queue '%s'" % (
            queueName))
        try:
            qt = self.qtask[queueName]
        except KeyError:
            raise TaskManagerError("No such queue: '%s'" % (queueName))

        qt.cancel()

        #self.reset()

        # Release any paused tasks to discover the cancel...
        qt.resume()
        
    def pause(self, queueName):
        self.logger.info("Trying to pause tasks in queue '%s'" % (
            queueName))
        try:
            qt = self.qtask[queueName]
        except KeyError:
            raise TaskManagerError("No such queue: '%s'" % (queueName))
        qt.pause()
        
    def resume(self, queueName):
        self.logger.info("Trying to resume tasks in queue '%s'" % (
            queueName))
        try:
            qt = self.qtask[queueName]
        except KeyError:
            raise TaskManagerError("No such queue: '%s'" % (queueName))
        qt.resume()
        
        
    def _indexModule(self, moduleName, module, subsys):
        """Internal method used to index the module.
        """

        self.logger.debug("Indexing module '%s'" % (moduleName))

        if self.modules.has_key(moduleName):
            moduleInfo = self.modules[moduleName]
            
        else:
            # See Note [1]
            moduleInfo = Bunch.Bunch()
            self.modules[moduleName] = moduleInfo

        moduleInfo.module = module

        if subsys == None:
            try:
                subsys = getattr(module, 'SUBSYS')

            except AttributeError:
                #subsys = moduleName
                subsys = ''

        # Atomically create case-insensitive task index (a caseless,
        # threadSafeBunch) under the index _subsys_ (e.g. 'TSC')
        tdir = self.taskdir.getsetitem(subsys, Bunch.threadSafeBunch,
                                       kwdargs={'caseless': True})

        # Populate this index with the task classes and their names.
        # Note this will overwrite any other modules classes with the
        # same names in this subsystem
        for name in dir(module):
            attr = getattr(module, name)
            # Only save things that are g2Task and subclasses
            if isinstance(attr, type) and issubclass(attr, g2Task.g2Task):
                self.logger.debug("Indexed task '%s'" % (name))
                tdir[name] = Bunch.Bunch(name=name, klass=attr)
        
        self.logger.info("Loaded module '%s' into subsystem %s" % \
                         (moduleName, subsys))


    def loadModule(self, moduleName, subsys=None, path=None):
        """Loads the named module into the task manager, so that it can
        then instantiate task-derived classes in that module.
        We raise a TaskManagerError if the given module cannot be loaded.
        """
        if self.modules.has_key(moduleName):
            moduleInfo = self.modules[moduleName]
            
            self.logger.info("Reloading module '%s'" % moduleName)
            try:
                module = moduleInfo.module
                reload(module)

            except ImportError, e:
                errmsg = "Error reloading module: %s" % str(e)
                self.logger.error(errmsg)
                raise TaskManagerError(errmsg)

        else:
            self.logger.debug("Importing module '%s'" % moduleName)
            try:
                if path == None:
                    module = __import__(moduleName)
                else:
                    module = imp.load_source(moduleName, path)

            except ImportError, e:
                errmsg = "Error loading module: %s" % str(e)
                self.logger.error(errmsg)
                raise TaskManagerError(errmsg)

        return self._indexModule(moduleName, module, subsys)
    

    def loadModules(self, moduleList, subsys=None):
        """Loads a list of modules.
        """
        for modname in moduleList:
            self.loadModule(modname, subsys=subsys)
            
            
    def loadAbsCmds(self, obe_id, obe_mode):
        """Loads a set of abstract commands as a module.
        """

        if obe_mode.upper() == 'ALL':
            modes = []
            for path in glob.glob('%s/%s/sk/*' % (obshome, obe_id)):
                (pfx, obe_mode) = os.path.split(path)
                modes.append(obe_mode)

            modes.sort()
            for obe_mode in modes:
                self.loadAbsCmds(obe_id, obe_mode)

            return

        elif not os.path.isdir('%s/%s/sk/%s' % (obshome, obe_id, obe_mode)):
            raise TaskManagerError("No such OBE/MODE: '%s/%s'" % (
                obe_id, obe_mode))
        
        # Create module for this obe_id and obe_mode
        # (should this be in a try/except clause?)
        self.logger.debug("Building module from skeleton files '%s/%s'" % (
            obe_id, obe_mode))
        module = skTask.build_abscmd_module(obshome, obe_id, obe_mode,
                                            self.sk_bank)

        modname = module.__name__
        subsys = sk_interp.get_subsys(obe_id, obe_mode)

        # Uncomment if module should be importable by other modules?
        #sys.modules[modname] = module
        
        # Index the module.
        return self._indexModule(modname, module, subsys)
            
            
    def loadParaDirs(self, paraDirList):
        """Loads the validator from a list of para file directories.
        """
        self.validator.loadParaDirs(paraDirList)
        self.logger.info("Loaded para files from %s" % (str(paraDirList)))
            
            
    def loadParaDir(self, paraDir, subsys=None):
        """Loads the validator from a directory of para files.
        """
        self.validator.loadParaDir(paraDir, subsys=subsys)
        self.logger.info("Loaded para files from %s" % paraDir)
            
            
    def loadParaBase(self, paraList, paraDirBase=obshome):
        """Loads the validator from a list of para directories
        relative to a base directory.
        """
        paraDirList = [ os.path.join(paraDirBase, paraDir) \
                        for paraDir in paraList ]
        self.loadParaDirs(paraDirList)
            

    def getModules(self):
        """Shows the list of loaded modules.
        """
        # See Note [1]
        res = self.modules.keys()
        return res
            
            
    def setAllocs(self, allocNames):
        """Set the list of allocations for the task manager.  Given a list
        of remote object service names, allocate proxies (handles) to all of
        the remote objects and put them in the allocs list.
        """
        allocs = {}
        try:
            for svcname in allocNames:
                # Aliasing service under a different name?
                if '=' in svcname:
                    (alias, svcname) = svcname.split('=')
                else:
                    alias = svcname

                if self.internal_allocs.has_key(svcname):
                    proxy = self.internal_allocs[svcname]
                else:
                    proxy = ro.remoteObjectProxy(svcname)

                allocs[alias] = proxy

        except ro.remoteObjectError, e:
            errmsg = "Error allocating subsystem: %s" % svcname
            self.logger.error(errmsg)
            raise TaskManagerError(errmsg)

        # See Note [1]
        self.alloc.clear()
        self.alloc.update(allocs)
        
        self.logger.info("Allocations set to: %s" % str(allocNames))


    def getAllocs(self):
        # See Note [1]
        res = self.alloc.keys()
        return res

    
    def addAllocs(self, allocNames):
        self.logger.info("Adding allocations: %s" % str(allocNames))

        # Get current set of allocs and add these
        allocs = set(self.getAllocs())
        allocs = allocs.union(set(allocNames))
        self.setAllocs(allocs)
        
        
    def initializeFromSession(self, sessionSvc, sessionName):
        # Reads module level variable 'obshome'

        self.sk_bank = sk_interp.skBank(obshome)

        # Check that we have a handle to the session service
        if not self.alloc.has_key(sessionSvc):
            errmsg = "No subsystem: '%s'" % sessionSvc
            self.logger.error(errmsg)
            raise TaskManagerError(errmsg)

        # Get the list of allocations to this session
        try:
            svcnames = self.alloc[sessionSvc].getSessionAllocations(sessionName)
            self.setAllocs(svcnames)
            
        except ro.remoteObjectError, e:
            errmsg = "Error getting allocation info: %s" % str(e)
            self.logger.error(errmsg)
            raise TaskManagerError(errmsg)

        # Get the list of active instrument codes (IRC, SUP, etc.)
        inst_list = self.insconfig.getNames()

        # Iterate over the svc names of the allocations.  Services names
        # for instruments and legacy systems are expected to match; i.e.
        # VGW --> VGW, MOIRCS --> MOIRCS, TSC --> TSC, etc.
        for name in self.getAllocs():

            # Load tasks, if there is a task file with this prefix
            if name != 'TSC':
                if name in inst_list:
                    # Because Bruce preferred 'SUPdd.py' over 'SPCAM.py'
                    inst_code = self.insconfig.getCodeByName(name)
                    taskfile = ('%s/%s/task/%sdd.py' % (
                        obshome, name, inst_code))
                    modname = ('%sdd' % (inst_code))
                else:
                    taskfile = ('%s/%s/task/%sdd.py' % (
                        obshome, name, name))
                    modname = ('%sdd' % (name))
            else:
                # Because Mark preferred 'TCS' over 'TSC'
                taskfile = ('%s/TSC/task/TCSdd.py' % (obshome))
                modname = 'TCSdd'

            if os.path.exists(taskfile):
                self.logger.info("Loading tasks for '%s'..." % name)
                self.loadModule(modname, path=taskfile)
            else:
                self.logger.debug("No tasks to load for '%s'..." % name)
            
            # Load para files, if there is a para dir with this prefix
            paraDir = os.path.join(obshome, name, 'para')
            if os.path.isdir(paraDir):
                self.loadParaDir(paraDir, subsys=name)
            else:
                self.logger.debug("No PARAs to load for '%s'..." % name)

        # For looking up abs commands
        taskfile = ('%s/COMMON/task/skTask.py' % (obshome))
        self.loadModule('skTask', path=taskfile)

        # Load up abstract command modules
        modelist = skTask.getModesList(obshome, svcnames)
        modelist.extend(skTask.getModes(obshome, 'COMMON'))

        for (obe_id, obe_mode) in modelist:
            self.loadAbsCmds(obe_id, obe_mode)


    def getFactory(self, className, subsys=None):
        """Lookup the class for a given class name.  This will raise an
        AttributeError if the given class does not exist in the module.
        """
        if subsys == None:
            subsys= ''
            
        try:
            mdir = self.taskdir[subsys]

        except KeyError:
            errmsg = "No such subsystem '%s'" % subsys
            self.logger.error(errmsg)
            raise TaskManagerError(errmsg)

        try:
            return mdir[className]

        except KeyError:
            errmsg = "Cannot find a class corresponding to name '%s'" % \
                     className
            self.logger.error(errmsg)
            raise TaskManagerError(errmsg)


    def getTasks(self, subsys):
        try:
            mdir = self.taskdir[subsys]

        except KeyError:
            errmsg = "No such subsystem '%s'" % subsys
            self.logger.error(errmsg)
            raise TaskManagerError(errmsg)

        res = Bunch.Bunch(caseless=True)
        for key in mdir.keys():
            res[key] = mdir[key].klass

        return res


    def submit(self, task, queueName='executer'):
        # Get the task queue that this should go on
        try:
            qt = self.qtask[queueName]

        except KeyError:
            errmsg = "Error creating task: no such task queue '%s'" % (
                queueName)
            self.logger.error(errmsg)
            raise TaskManagerError(errmsg)

        # Get a task id
        className = task.__class__.__name__
        tag = ("%s.%s-%s" % (self.tag, className, self.tagger.get_tag(self)))

        # Forcibly set the tag.  This will prevent the task from trying
        # to create one later in its initialize() method
        task.tag = tag

        # Remind ourselves to vaccuum this later
        self.topTags.append(tag)
        
        # Put the task on the appropriate task queue
        self.logger.debug("Queueing task '%s' on queue %s" % (
            str(task), queueName))
        qt.addTask(task)


    def addTask(self, className, args, kwdargs, subsys=None,
                queueName='executer'):
        """Create a task and add it to a task queue.
        _className_ is the class name of a Task-derived class to
        instantiate.
        _args_ (a sequence) and _kwdargs_ (a dict) are
        passed to the constructor for initializing the task.
        _subsys_ (if specified) names a particular subsystem under which
        this task is filed.
        _queueName_ (if specified) names a particular queue on which
        the task should be enqueued.
        We raise a TaskManagerError if the task cannot be created.
        """

        # Get the task factory that makes this kind of task
        self.logger.debug("Creating task: class=%s subsys=%s args=%s kwdargs=%s" % \
                          (className, str(subsys), str(args), str(kwdargs)))

        classInfo = self.getFactory(className, subsys=subsys)

        # Get a task id
#        tag = ("%s.%s-%s" % (self.tag, classInfo.name, self.tagger.get_tag(self)))

        try:
            # Create an instance of this task
            task = classInfo.klass(*args, **kwdargs)

        except (Exception), e:
            # TODO: catch traceback and log it
            errmsg = "Error creating task: %s" % str(e)
            self.logger.error(errmsg)
            raise TaskManagerError(errmsg)

        # Forcibly set the tag.  This will prevent the task from trying
        # to create one later in its initialize() method
#        task.tag = tag

        self.submit(task, queueName=queueName)

        return task


    def awaitTask(self, task, timeout=None):
        return self.awaitTaskByTag(task.tag)
    
    def awaitTaskByTag(self, tag, timeout=None):
        # If task submission was successful, then watch the monitor for
        # the result.
        try:
            d = self.monitor.getitem_any(['%s.task_end' % tag],
                                         timeout=timeout)

        except Monitor.TimeoutError, e:
            self.logger.error(str(e))
            return 2
        
        # Task terminated.  Get all items currently associated with this
        # transaction.
        vals = self.monitor.getitems_suffixOnly(tag)
        if type(vals) != dict:
            self.logger.error("Could not get task transaction info")
            return ro.ERROR

        # This produces voluminous output for large sk files and is not helpful
        #self.logger.debug("task transaction info: %s" % str(vals))

        # Interpret task results:
        #   task_code == 0 --> OK   task_code != 0 --> ERROR
        #res = vals.get('task_code', 1)
        if vals.has_key('task_code'):
            res = vals['task_code']
        else:
            logger.error("Task has no task result code; assuming error")
            res = ro.ERROR

        if not isinstance(res, int):
            logger.error("Task result code (%s) not int; assuming error" % (
                res))
            res = ro.ERROR

        try:
            totaltime = vals['task_end'] - vals['task_start']
            time_s = ('%.3f sec' % totaltime)
        except Exception as e:
            time_s = 'N/A: %s' % (str(e))

        if res == 0:
            self.logger.info("task terminated successfully (%s)" % (time_s))
            return ro.OK
        else:
            # Check for a diagnostic message
            msg = vals.get('task_error',
                           "[No diagnostic message available]")
            # This is reported elsewhere?
            self.logger.error("task terminated with error: %s" % msg)
            return res
            
        
    def execTask(self, queueName, cmdstr, envstr):
        """Interface to execute a SOSS-formatted command.
        [This is the interface used by, e.g. IntegGUI]
        """

        task = self.addTask('execTask', [cmdstr, envstr, self.sk_bank],
                            {}, queueName=queueName)
        return self.awaitTask(task)
        

    def execTaskNoWait(self, queueName, cmdstr):
        """Interface to execute a SOSS-formatted command.
        [This is the interface used by, e.g. integgui2]
        """

        envstr = ''
        task = self.addTask('execTask', [cmdstr, envstr, self.sk_bank],
                            {}, queueName=queueName)
        return task.tag
        

    def execTaskTimeout(self, queueName, cmdstr, envstr, timeout):
        task = self.addTask('execTask', [cmdstr, envstr, self.sk_bank],
                            {}, queueName=queueName)
        return self.awaitTask(task, timeout=timeout)
    

    def runTask(self, subsys, className, args, kwdargs, timeout):

        task = self.addTask(className, args, kwdargs, subsys=subsys)

        return self.awaitTask(task, timeout=timeout)


    def end_dd(self, tag, retcode, msg):
        """Reply to an end_dd call
        """
        self.monitor.setvals(self.channels, tag,
                             msg=msg, time_done=time.time(),
                             result=retcode, done=True)
        return ro.OK
        

    def vaccuum(self, older_than_sec=600):
        """Remove old task transactions from the monitor.  <older_than_sec>
        gives a time interval (in seconds); completed tasks older than that
        are removed from the monitor.
        """
        self.logger.info("Vaccuuming tasks older than %.2f sec ..." % (
            older_than_sec))
        time_start = time.time()
        for tag in self.topTags:
            
            vals = self.monitor.getitems_suffixOnly(tag)
            if type(vals) != dict:
                self.logger.error("Could not get task transaction info for tag (%s)" % (
                    tag))
                self.topTags.remove(tag)
                continue

            if not vals.has_key('task_end'):
                # If we cannot determine that the task has finished, carry on
                continue

            # If the task end time is older than the limit, cull the task info
            end_time = vals['task_end']
            if (time.time() - end_time) > older_than_sec:
                self.logger.debug("Deleting tag %s" % (tag))
                # note 'local' channel: do not propagate delete
                self.monitor.delete(tag, self.channels)
                self.topTags.remove(tag)

        time_elapsed = time.time() - time_start
        self.logger.info("Finished vaccuuming (%.2f sec)." % (
            time_elapsed))
        return ro.OK
    
        
def cmdline(options):
    
    histfile = os.path.join(os.environ['HOME'], '.tmhist')
    try:
        # load the history file
        readline.read_history_file(histfile)
        
    except IOError:
        pass
    # Write out history file when the program terminates
    atexit.register(readline.write_history_file, histfile)

    try:
        while True:
            cmd = raw_input('tm>>> ')
            if len(cmd) == 0:
                continue
            try:
                print eval("tm." + cmd)
                
            except (EOFError, KeyboardInterrupt), e:
                raise e

            except Exception, e:
                print str(e)
                continue

    except (EOFError, KeyboardInterrupt):
        print ""
        pass


def main(options, args):

    svcname = options.svcname
        
    # Create top level logger.
    logger = ssdlog.make_logger(svcname, options)

    # Initialize remote objects subsystem.
    try:
        ro.init()

    except ro.remoteObjectError, e:
        logger.error("Error initializing remote objects subsystem: %s" % str(e))
        sys.exit(1)

    taskmgr = None
    minimon = None
    tm_svr = None
    tm_started = False
    mon_started = False

    # Global termination flag
    ev_quit = threading.Event()
    
    def quit():
        logger.info("Shutting down Task Manager service...")
        if taskmgr:
            taskmgr.stop(wait=True)
        if mon_started:
            minimon.releaseAll()
            minimon.stop_server(wait=True)
            minimon.stop(wait=True)
        if tm_started:
            tm_svr.ro_stop(wait=False)

    def SigHandler(signum, frame):
        """Signal handler for all unexpected conditions."""
        logger.error('Received signal %d' % signum)
        quit()
        ev_quit.set()

    # Set signal handler for signals
    #signal.signal(signal.SIGINT, SigHandler)
    signal.signal(signal.SIGTERM, SigHandler)

    logger.info("Starting Task Manager service...")
    try:
        try:
            # Create and start a task manager
            taskmgr = TaskManager(logger=logger, ev_quit=ev_quit,
                                  numthreads=options.numthreads,
                                  identity=svcname)
            taskmgr.start(wait=True)

            minimon = taskmgr.get_monitor()
            minimon.start_server(wait=True, usethread=True)
            minimon.start(wait=True)
            mon_started = True

            threadPool = taskmgr.get_threadPool()

            # channel we send out information for integgui
            mychannel = '%s-ig' % svcname

            # If one was specified, subscribe our mini-monitor to the
            # main monitor g2task feed
            if options.monitor:
                minimon.subscribe_remote(options.monitor, ['g2task'], {})

                # Publish our feeds to the specified monitor
                monchannels = [svcname, 'frames', mychannel]
                minimon.publish_to(options.monitor, monchannels, {})

            # Configure logger for logging via our monitor
            if options.logmon:
                minimon.logmon(logger, options.logmon, ['logs'])

            # Set up authorization credentials?
            # e.g. --auth='joe:pw1,bob:pw2,...
            authDict = None
            if options.auth:
                authDict = dict(map(lambda s: s.split(':'),
                                    options.auth.split(',')))
        
            # Start remoteObjects server in the taskmgr
            tm_svr = ro.remoteObjectServer(svcname=svcname,
                                           obj=taskmgr, logger=logger,
                                           ev_quit=ev_quit,
                                           port=options.port,
                                           authDict=authDict,
                                           usethread=False,
                                           threadPool=threadPool)

            # Set allocations if specified
            if options.allocs:
                taskmgr.setAllocs(options.allocs.split(','))

            # Load modules/tasks if specified
            if options.load:
                res = taskmgr.loadModules(options.load.split(','))
                nocomplain = True

            # Initialize load of PARA files if specified
            if options.para:
                res = taskmgr.loadParaBase(options.para.split(','),
                                           options.parabase)
                nocomplain = True

            # Initialize from session if specified
            if options.session:
                tup = options.session.split(':')
                if len(tup) == 1:
                    sess_svc = 'sessions'
                    sess_name = tup[0]
                else:
                    sess_svc = tup[0]
                    sess_name = tup[1]

                try:
                    taskmgr.initializeFromSession(sess_svc, sess_name)

                    minimon.setvals([mychannel], 'mon.taskmgr.%s' % svcname,
                                    ready=time.time())
                except Exception, e:
                    logger.error("ERROR: failed to initialize from session '%s'" % (
                            sess_name))
                
            # Because usethread=False above, our thread will enter here
            # and not return.
            tm_started = True
            tm_svr.ro_start(wait=True)

        except KeyboardInterrupt:
            logger.warn("Caught keyboard interrupt!")

        except Exception, e:
            logger.error("Caught exception: %s" % str(e))
            
    finally:
        logger.warn("Trying to terminate...")
        quit()


if __name__ == '__main__':
    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("--allocs", dest="allocs", metavar="LIST",
                      default='sessions',
                      help="Specify initial set of allocations")
    optprs.add_option("--auth", dest="auth",
                      help="TaskManager authorization; arg should be user:passwd")
    optprs.add_option("--db", dest="dbpath", metavar="FILE",
                      default='taskmgr-db',
                      help="Use FILE for the task manager database")
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--load", dest="load",
                      help="Specify a list of task modules to load")
    optprs.add_option("--monitor", dest="monitor", metavar="NAME",
                      default='monitor',
                      help="Synchronize with Monitor named NAME")
    optprs.add_option("--numthreads", dest="numthreads", type="int",
                      default=30,
                      help="Use NUM threads", metavar="NUM")
    optprs.add_option("--para", dest="para",
                      help="Specify a list of PARA directories to load")
    optprs.add_option("--parabase", dest="parabase", default=obshome,
                      help="Specify the base directory for PARA files")
    optprs.add_option("--port", dest="port", type="int", default=None,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--session", dest="session", metavar="NAME",
                      default=None,
                      help="Initialize from session NAME")
##     optprs.add_option("--skdir", dest="skdir", default='.',
##                          help="Base directory of the skeleton files")
    optprs.add_option("--sm", dest="sessionmgr", metavar="NAME",
                      default='sessions',
                      help="Use Session Manager with service NAME")
    optprs.add_option("--svcname", dest="svcname", metavar="NAME",
                      default=serviceName,
                      help="Register using NAME as service name")
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
       
    
# END

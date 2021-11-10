# 
# Eric Jeschke (eric@naoj.org)
#

import re
import os, time
import threading
import string

import view.common as common
import CommandQueue

# SSD/Gen2 imports
import Task
import remoteObjects as ro
import remoteObjects.Monitor as Monitor
import Bunch
from cfg.INS import INSdata
import cfg.g2soss as g2soss

# Regex used to discover/parse frame info
regex_frame = re.compile(r'^mon\.frame\.(\w+)\.(\w+)$')
regex_frameid = re.compile('^(\w{3})([AQ])(\d{8})$')

# Regex used to discover/parse log info
regex_log = re.compile(r'^mon\.log\.(\w+)$')

# These are the status variables pulled from the status system. "%s" is
# replaced by the 3-letter instrument mnemonic of the currently allocated
# primary instrument in IntegGUI.
#
statvars_t = [(1, 'STATOBS.%s.OBSINFO1'), (2, 'STATOBS.%s.OBSINFO2'),
              (3, 'STATOBS.%s.OBSINFO3'), (4, 'STATOBS.%s.OBSINFO4'),
              (5, 'STATOBS.%s.OBSINFO5'), # 6 is error log string
              (7, 'STATOBS.%s.TIMER_SEC'), (8, 'FITS.%s.PROP-ID'),
              ]

opefile_host = 'ana.sum.subaru.nao.ac.jp'


valid_monlogs = set(['taskmgr0', 'TSC', 'status', 
                     'sessions', 'frames',
                     'STARS', 'archiver', 'gen2base',
                     'integgui2', 'fitsview', 'fitsview1',
                     ])
# add active instrument names
valid_monlogs.update(INSdata().getNames())

typical_monlogs = set(['taskmgr0', 'TSC', 'status', 'integgui2',
                       'archiver'
                       ])
typical_monlogs.update(INSdata().getNames())


class ControllerError(Exception):
    pass

class IntegController(object):
    """
    IMPORTANT NOTE: The GUI thread makes calls into this object, but these
    SHOULD NOT BLOCK or the GUI becomes unresponsive!  ALL CALLS IN should
    create and start a task to do the work (which will be done on another
    thread).
    """
    
    def __init__(self, logger, ev_quit, monitor, view, queues, fits,
                 soundsink, options, logtype='normal'):

        self.logger = logger
        self.ev_quit = ev_quit
        self.monitor = monitor
        self.gui = view
        self.queue = queues
        self.fits = fits
        # mutex on this instance
        self.lock = threading.RLock()
        self.soundsink = soundsink
        self.options = options
        self.logtype = logtype
        self.histidx = 0

        # TODO: improve this
        self.valid_monlogs = valid_monlogs

        self.executingP = threading.Event()

        # For task inheritance:
        self.threadPool = monitor.get_threadPool()
        self.tag = 'IntegGUI'
        self.shares = ['logger', 'ev_quit', 'threadPool']

        # Used for looking up instrument codes, etc.
        self.insconfig = INSdata()
        self.insname = 'SUKA'
        self.inscodes = []
        self.propid = None

        # Used to strip out bogus characters from log buffers
        self.deletechars = ''.join(set(string.maketrans('', '')) -
                                   set(string.printable))
        self.reset_conn()


    def reset_conn(self):
        self.tm = ro.remoteObjectProxy(self.options.taskmgr)
        self.tm2 = ro.remoteObjectProxy(self.options.taskmgr)
        self.status = ro.remoteObjectProxy('status')
        self.sm = ro.remoteObjectProxy('sessions')
        self.bm = ro.remoteObjectProxy('bootmgr')

        ## self.transdict = {}

#############
###  GUI interface to the controller
            
    def clearQueue(self, queueName):
        queue = self.queue[queueName]
        queue.flush()

    def execQueue(self, queueName, tm_queueName='executer'):
        """This method is called when the GUI has commands for the
        controller.
        """
        try:
            queueObj = self.queue[queueName]

            # ?? TODO: should have a different executingP flag for each queue?
            t = Task.FuncTask2(self.exec_queue, queueObj, tm_queueName,
                               self.executingP,
                               common.sound.success_executer,
                               common.sound.failure_executer)
        
            # now the task is spun off into another thread
            # for the task manager interaction
            t.init_and_start(self)

        except Exception, e:
            # TODO: popup error here?
            self.gui.gui_do(self.gui.popup_error, str(e))

    def execOne(self, cmdObj, tm_queueName):
        if tm_queueName == 'launcher':
            sound_success, sound_failure = (common.sound.success_launcher,
                                            common.sound.failure_launcher)
        else:
            sound_success, sound_failure = (common.sound.success_executer,
                                            common.sound.failure_executer)

        try:
            t = Task.FuncTask2(self.exec_one, cmdObj, tm_queueName,
                               sound_success, sound_failure)
        
            # now the task is spun off into another thread
            # for the task manager interaction
            t.init_and_start(self)

        except Exception, e:
            # TODO: popup error here?
            self.gui.gui_do(self.gui.popup_error, str(e))

    def editOne(self, cmdObj):
        try:
            t = Task.FuncTask2(self.edit_one, cmdObj)
            t.init_and_start(self)

        except Exception, e:
            # TODO: popup error here?
            self.gui.gui_do(self.gui.popup_error, str(e))


    def get_all_queued_tags(self):
        # TODO: may need a lock?
        tags = set([])
        for queueObj in self.queue.values():
            tags.update(queueObj.get_tags())

        return tags
        

    def remove_by_tags(self, tags):
        # TODO: may need a lock?
        cmdObjs = set([])
        for queueObj in self.queue.values():
            deleted = queueObj.removeFilter(lambda x: not (str(x) in tags))
            cmdObjs.update(deleted)
        return cmdObjs


    def ctl_do(self, func, *args, **kwdargs):
        try:
            t = Task.FuncTask(func, args, kwdargs)
            t.init_and_start(self)

        except Exception, e:
            raise ControllerError(e)
        
#############

    def tm_cancel(self, queueName):
        self.playSound(common.sound.tm_cancel, priority=16)
        def cancel():
            self.tm2.cancel(queueName)

        #self.tm2.cancel(queueName)
        t = Task.FuncTask2(cancel)
        t.init_and_start(self)

    def tm_pause(self, queueName):
        def pause():
            self.tm2.pause(queueName)

        t = Task.FuncTask2(pause)
        t.init_and_start(self)

    def tm_resume(self, queueName):
        def resume():
            self.tm2.resume(queueName)
            #self.gui.gui_do(self.gui.reset_pause)
            
        t = Task.FuncTask2(resume)
        t.init_and_start(self)

    def tm_restart(self):
        def kill():
            self.playSound(common.sound.tm_kill, priority=16)

            # ask Boot Manager to restart the Task Manager
            self.bm.restart(self.options.taskmgr)

            self.gui.update_statusMsg("Restarting TaskManager.  Please wait...")
            
            # reset visually all command executors
            self.gui.gui_do(self.gui.reset_pause)

            ## # Release all pending transactions
            ## self.release_all_transactions()

        t = Task.FuncTask2(kill)
        t.init_and_start(self)

    def addQueue(self, queueName, logger):
        if self.queue.has_key(queueName):
            raise ControllerError("Queue already exists: '%s'" % queueName)
        
        queue = CommandQueue.CommandQueue(queueName, logger)
        self.queue[queueName] = queue
        return queue

    def set_instrument(self, insname):
        """Called when we notice a change of instrument.
        """
        try:
            inscode = self.insconfig.getCodeByName(insname)
        except KeyError:
            # If no instrument allocated, then just look up a non-existent
            # instrument status messages
            inscode = "NOP"
    
        # Set up default fetch list and dictionary.
        # _statDict_: dictionary whose keys are status variables we need
        # _statvars_: list of (index, key) pairs (index is used by IntegGUI)
        statvars = []
        for (idx_t, key_t) in statvars_t:
            if key_t:
                keyCmn = key_t % "CMN"
                key = key_t % inscode
            statvars.append((idx_t, keyCmn))
            statvars.append((idx_t, key))

        with self.lock:
            self.statvars = statvars
            self.insname = insname
            

    def get_instrument(self):
        return self.insname

    def get_alloc_instrument(self):
        insname = self.status.fetchOne('FITS.SBR.MAINOBCP')
        return insname
    
    def config_alloc_instrument(self):
        insname = self.get_alloc_instrument()
        self.set_instrument(insname)

    def config_from_session(self, sessionName):
        self.sessionName = sessionName
        try:
            info = self.sm.getSessionInfo(self.sessionName)

        except ro.remoteObjectError, e:
            self.logger.error("Error getting session info for session '%s': %s" % (
                    self.sessionName, str(e)))

        self._session_config(info)

    def load_frames(self, framelist):
        # TODO: this should maybe be in IntegView

        for frameid in framelist:
            fitspath = self.insconfig.getFileByFrameId(frameid)
            self.gui.gui_do(self.gui.load_fits, fitspath)


    def _session_config(self, info):
        self.logger.debug("info=%s" % str(info))

        # Get propid info
        propid = info.get('propid', 'xxxxx')
        observers = info.get('observers', 'N/A')
        inst = info.get('mainInst', 'N/A')
        inst = inst.upper()
        self.gui.update_obsinfo({'PROP-ID':
                                                      ('%s - %s - %s' % (propid,
                                                                         inst,
                                                                         observers))
                                 })

        self.set_instrument(inst)

        # Get allocs
        allocs = info.get('allocs', [])
        allocs_lst = []
    
        for name in self.insconfig.getNames(active=True):
            if name in allocs:
                allocs_lst.append(name)

        # List of inst codes we should pay attention to
        self.inscodes = map(self.insconfig.getCodeByName, allocs_lst)
        self.propid = propid
        
        # Load up appropriate launchers and handsets
        #self.gui.close_launchers()

        launchers = []
        handsets = []

        for name in ['TELESCOPE']:
            launchers.extend(self.gui.get_launcher_paths('COMMON', name))
        # uncomment once Az/El handset is ready
        #for name in ['STANDARD', 'TELESCOPE']:
        for name in ['STANDARD']:
            handsets.extend(self.gui.get_handset_paths('COMMON', name))

        for name in allocs_lst:
            launchers.extend(self.gui.get_launcher_paths(name, name))
            handsets.extend(self.gui.get_handset_paths(name, name))

        self.logger.debug("launchers=%s handsets=%s" % (
            launchers, handsets))
        for filepath in launchers:
            # TODO: remove references to gui instance vars
            self.gui.gui_do(self.gui.load_launcher, self.gui.lws, filepath)
        for filepath in handsets:
            # TODO: remove references to gui instance vars
            self.gui.gui_do(self.gui.load_handset, self.gui.handsets, filepath)

        # Load up appropriate log files
        #self.gui.close_logs()

        names = set(allocs)
        # Remove some that aren't particularly useful--they can be
        # added manually if desired
        logs = list(names.intersection(typical_monlogs))
        logs.sort()

        for name in logs:
            if self.logtype == 'monlog':
                self.gui.gui_do(self.gui.load_monlog, self.gui.logpage,
                                name)
            else:
                logpath = os.path.join(g2soss.loghome, name + '.log')
                self.gui.gui_do(self.gui.load_log, self.gui.logpage,
                                logpath)


        # Set appropriate areas for loading OPE files
        procdir = os.path.join(os.environ['HOME'], 'Procedure')
        propiddir = os.path.join(procdir, 'ANA', propid, 'Procedure')
        if os.path.isdir(propiddir):
            self.gui.set_procdir(propiddir, inst)
        else:
            self.gui.set_procdir(procdir, inst)
            

    def getvals(self, path):
        return self.monitor.getitems_suffixOnly(path)

    ## def awaitTask(self, tag, timeout=None):

    ##     # If task submission was successful, then watch the monitor for
    ##     # the result.
    ##     try:
    ##         d = self.monitor.getitem_any(['%s.task_end' % tag],
    ##                                      timeout=timeout)

    ##     except Monitor.TimeoutError, e:
    ##         self.logger.error(str(e))
    ##         return 2
        
    ##     # Task terminated.  Get all items currently associated with this
    ##     # transaction.
    ##     vals = self.monitor.getitems_suffixOnly(tag)
    ##     if type(vals) != dict:
    ##         self.logger.error("Could not get task transaction info")
    ##         return ro.ERROR

    ##     # This produces voluminous output for large sk files and is not helpful
    ##     #self.logger.debug("task transaction info: %s" % str(vals))

    ##     # Interpret task results:
    ##     #   task_code == 0 --> OK   task_code != 0 --> ERROR
    ##     #res = vals.get('task_code', 1)
    ##     if vals.has_key('task_code'):
    ##         res = vals['task_code']
    ##     else:
    ##         logger.error("Task has no task result code; assuming error")
    ##         res = ro.ERROR

    ##     if not isinstance(res, int):
    ##         logger.error("Task result code (%s) not int; assuming error" % (
    ##             res))
    ##         res = ro.ERROR

    ##     if res == 0:
    ##         self.logger.info("task terminated successfully")
    ##         return ro.OK
    ##     else:
    ##         # Check for a diagnostic message
    ##         msg = vals.get('task_error',
    ##                        "[No diagnostic message available]")
    ##         # This is reported elsewhere?
    ##         self.logger.info("task terminated with error: %s" % msg)
    ##         return res

    def update_integgui(self, statusDict):
        d = {}
        for (idx, key) in self.statvars:
            val = statusDict.get(key, '##')
            if not val.startswith('##'):
                slot = key.split('.')[-1]
                d[slot] = str(val)

        self.gui.update_obsinfo(d)


    # this one is called if new data becomes available about tasks
    def arr_taskinfo(self, payload, name, channels):
        self.logger.debug("received values '%s'" % str(payload))
        try:
            bnch = Monitor.unpack_payload(payload)

        except Monitor.MonitorError:
            self.logger.error("malformed packet '%s': %s" % (
                str(payload), str(e)))
            return

        if not bnch.has_key('value'):
            # delete (vaccuum) packet
            return
        vals = bnch.value

        if vals.has_key('ast_id'):
            # SkMonitorPage update on some abstract or device dependent command
            self.gui.process_ast(vals['ast_id'], vals)

        elif vals.has_key('subpath'):
            # SkMonitorPage update on some subcommand
            self.gui.process_subcommand(bnch.path,
                                        vals['subpath'], vals)

        # possible SkMonitorPage update on some command status change
        else:
            self.gui.process_task(bnch.path, vals)
        
        if vals.has_key('task_code'):
            res = vals['task_code']
            # Interpret task results:
            #   task_code == 0 --> OK   task_code != 0 --> ERROR
            if res == 0:
##                 self.gui.gui_do(self.gui.feedback_ok,
##                                 tmtrans.queueName, tmtrans, res)
                pass
            else:
                # If there was a problem, let the gui know about it
##                 self.gui.gui_do(self.gui.feedback_error,
##                                 tmtrans.queueName, tmtrans, str(res))
                if res == 3:
                    self.logger.info("Task cancelled (%s)" % bnch.path)
                    self.gui.cancel_dialog(bnch.path)

    # this one is called if new data becomes available for integgui
    def arr_obsinfo(self, payload, name, channels):
        self.logger.debug("received values '%s'" % str(payload))

        try:
            bnch = Monitor.unpack_payload(payload)

        except Monitor.MonitorError:
            self.logger.error("malformed packet '%s': %s" % (
                str(payload), str(e)))
            return

        vals = bnch.value
        if vals.has_key('obsinfo'):
            statusDict = bnch.value['obsinfo']
            self.update_integgui(statusDict)

        elif vals.has_key('ready'):
            self.gui.update_statusMsg("TaskManager is ready.")

            self.playSound(common.sound.tm_ready, priority=22)
            
        
    # this one is called if new log data becomes available
    def arr_loginfo(self, payload, name, channels):
        self.logger.debug("received values '%s'" % str(payload))
        try:
            bnch = Monitor.unpack_payload(payload)

        except Monitor.MonitorError:
            self.logger.error("malformed packet '%s': %s" % (
                str(payload), str(e)))
            return

        # Find out the log for this information by examining the path
        match = regex_log.match(bnch.path)
        if match:
            logname = match.group(1)
            # Remove any non-ascii characters that won't go into
            # a standard text buffer
            # this is now handled at the sending end....EJ
            #buf = bnch.value['msgstr']
            #bnch.value['msgstr'] = buf.translate(None, self.deletechars)
            self.gui.update_loginfo(logname, bnch.value)
            
        
    # this one is called if new data becomes available about frames
    def arr_fitsinfo(self, payload, name, channels):
        self.logger.debug("received values '%s'" % str(payload))

        try:
            bnch = Monitor.unpack_payload(payload)

        except Monitor.MonitorError:
            self.logger.error("malformed packet '%s': %s" % (
                str(payload), str(e)))
            return

        # Find out the source of this information by examining the path
        match = regex_frame.match(bnch.path)
        if match:
            (frameid, subsys) = match.groups()

            try:
                # See if there is method to handle this information
                # in the 'fits' object
                method = getattr(self.fits, '%s_hdlr' % subsys)

            except AttributeError:
                self.logger.debug("No handler for '%s' subsystem" % subsys)
                return

            # check if this is a frame from an instrument that is
            # allocated
            match = regex_frameid.match(frameid)
            if match:
                inscode = match.group(1).upper()
                if not (inscode in self.inscodes):
                    return

            try:
                # Get all the saved items under this path to report to
                # the handler
                vals = self.monitor.getitems_suffixOnly(bnch.path)
                
                method(frameid, vals)
                return

            except Exception, e:
                self.logger.error("Error processing '%s': %s" % (
                    str(bnch.path), str(e)))
            return

        # Skip things that don't match the expected paths
        self.logger.error("No match for path '%s'" % bnch.path)
        return

                
    # this one is called if new data becomes available about the session
    def arr_sessinfo(self, payload, name, channels):
        self.logger.debug("received values '%s'" % str(payload))

        try:
            bnch = Monitor.unpack_payload(payload)

        except Monitor.MonitorError:
            self.logger.error("malformed packet '%s': %s" % (
                str(payload), str(e)))
            return

        if bnch.path == ('mon.session.%s' % self.sessionName):
            
            info = bnch.value
            #self._session_config(info)
                

    def audible_warn(self, cmd_str, vals):
        """Called when we get a failed command and should/could issue an audible
        error.  cmd_str, if not None, is the device dependent command that caused
        the error.
        """
        self.logger.debug("Audible warning: %s" % cmd_str)
        if not cmd_str:
            return

        if not self.gui.audible_errors:
            return

        cmd_str = cmd_str.lower().strip()
        match = re.match(r'^exec\s+(\w+)\s+.*', cmd_str)
        if not match:
            subsys = 'general'
        else:
            subsys = match.group(1)

        soundfile = 'ogg/en/%s_error.ogg' % subsys
        #soundfile = 'E_ERR%s.au' % subsys.upper()
        self.playSound(soundfile, priority=20)


    def playSound(self, soundfile, priority=20):
        soundpath = os.path.join(g2soss.producthome,
                                 'file/Sounds', soundfile)
        if os.path.exists(soundpath):
            self.soundsink.playFile(soundpath, priority=priority)
            
        else:
            self.logger.error("No such audio file: %s" % soundpath)

#############
#
    def feedback_ok(self, tm_queueName, cmdstr, cmdObj, res, soundfile,
                    time_start, time_end):
        self.logger.info("Ok [%s] %s" % (tm_queueName, cmdstr))
        self.log_history(cmdstr, time_start, time_end, tm_queueName, 'OK')

        # Mark success graphically appropriate to the source
        cmdObj.mark_status('done')

        if soundfile:
            self.playSound(soundfile, priority=18)

    def feedback_error(self, tm_queueName, cmdstr, cmdObj, res,
                       e, soundfile, time_start, time_end):
        self.logger.error("Error [%s] %s\n:%s" % (tm_queueName,
                                                  cmdstr, str(e)))
        if res == 3:
            # Command was cancelled
            status = 'CN'
        else:
            # Command had error
            status = 'NG'
        self.log_history(cmdstr, time_start, time_end, tm_queueName, status)

        # Mark an error graphically appropriate to the source
        cmdObj.mark_status('error')

        if soundfile:
            self.playSound(soundfile, priority=18)
            
    def feedback_break(self):
        self.logger.info("-- Break --")
        soundfile = common.sound.break_executer
        self.playSound(soundfile, priority=22)


    def log_history(self, cmdstr, time_start, time_end, tm_queueName,
                    result):
        elapsed = time_end - time_start
        d = {'cmdstr': cmdstr,
             't_start': time.strftime('%H:%M:%S', time.localtime(time_start)),
             't_end': time.strftime('%H:%M:%S', time.localtime(time_end)),
             't_elapsed': "%.3f" % elapsed,
             'queue': tm_queueName.capitalize(),
             'result': result,
             }
        if result == 'OK':
            #d['icon'] = "face-cool.svg"
            d['icon'] = "ok.svg"
        elif result == 'CN':
            #d['icon'] = "face-raspberry.svg"
            d['icon'] = "warning.svg"
        elif result == 'NG':
            #d['icon'] = "face-angry.svg"
            d['icon'] = "error.svg"
        
        self.histidx += 1
        self.gui.update_history(self.histidx, d)
        

    def get_sound_failure(self, res, cmdstr, sound_failure):
        if res == 3:
            self.gui.update_statusMsg("Task cancelled!")
            return common.sound.cancel_executer
        return sound_failure
            
    def exec_queue(self, queueObj, tm_queueName, executingP,
                   sound_success, sound_failure):
        
        while len(queueObj) > 0:
            try:
                # pull an item off the front of the queue
                cmdObj = queueObj.get()
                cmdObj.mark_status('normal')
            
            except Exception, e:
                self.gui.gui_do(self.gui.popup_error, str(e))
                return

            try:
                # Get the command string associated with this kind of page.
                cmdstr = cmdObj.get_cmdstr()

                if cmdstr == '== BREAK ==':
                    self.feedback_break()
                    return
                elif cmdstr == '== NOP ==':
                    # comment or other non-command item
                    continue
                
            except Exception, e:
                # Put object back on the front of the queue
                queueObj.prepend(cmdObj)
                self.gui.gui_do(self.gui.popup_error, str(e))
                return

            try:
                res = 1
                cmdObj.mark_status('executing')

                # Try to execute the command in the TaskManager
                self.logger.debug("Invoking to task manager (%s): '%s'" % (
                    tm_queueName, cmdstr))

                self.gui.update_statusMsg("TaskManager is executing...")
                executingP.set()
                time_start = time.time()

                res = self.tm.execTask(tm_queueName, cmdstr, '')
                ## tag = self.tm.execTaskNoWait(tm_queueName, cmdstr)
                ## self.logger.debug("Task submitted tag=%s" % tag)
                ## res = self.awaitTask(tag)

                time_end = time.time()
                executingP.clear()
                self.gui.update_statusMsg("")

                if res != 0:
                    raise Exception('Command terminated with res=%d' % res)

            except Exception, e:
                time_end = time.time()
                executingP.clear()
                self.gui.update_statusMsg("")

                # Put object back on the front of the queue
                queueObj.prepend(cmdObj)

                # Interpret failure sonically
                sound_failure = self.get_sound_failure(res, cmdstr,
                                                       sound_failure)
                
                self.feedback_error(tm_queueName, cmdstr, cmdObj, res,
                                    str(e), sound_failure, time_start,
                                    time_end)
                return

            self.feedback_ok(tm_queueName, cmdstr, cmdObj, res, None,
                             time_start, time_end)

        # When queue is empty and no errors then play success sound
        self.playSound(sound_success, priority=22)


    def exec_one(self, cmdObj, tm_queueName, sound_success, sound_failure):
        try:
            res = 1
            cmdstr = cmdObj.get_cmdstr()
        
            cmdObj.mark_status('executing')

            # Try to execute the command in the TaskManager
            self.logger.debug("Invoking to task manager (%s): '%s'" % (
                tm_queueName, cmdstr))

            # fix!
            if tm_queueName == 'executer':
                self.gui.update_statusMsg("TaskManager is executing...")
                self.executingP.set()
            time_start = time.time()

            res = common.controller.tm.execTask(tm_queueName,
                                                cmdstr, '')
            time_end = time.time()
            # fix!
            if tm_queueName == 'executer':
                self.executingP.clear()
                self.gui.update_statusMsg("")
            if res == 0:
                self.feedback_ok(tm_queueName, cmdstr, cmdObj,
                                 res, sound_success, time_start, time_end)
            else:
                raise Exception('Command terminated with res=%d' % res)

        except Exception, e:
            time_end = time.time()
            # fix!
            if tm_queueName == 'executer':
                self.executingP.clear()
                self.gui.update_statusMsg("")

            # Interpret failure sonically
            sound_failure = self.get_sound_failure(res, cmdstr,
                                                   sound_failure)
            
            self.feedback_error(tm_queueName, cmdstr, cmdObj, res,
                                str(e), sound_failure, time_start, time_end)


    def edit_one(self, cmdObj):
        try:
            cmdstr = cmdObj.get_cmdstr()
        
        except Exception, e:
            common.view.popup_error("Error editing command: %s" % (
                    str(e)))
            return
                
        self.gui.gui_do(self.gui.edit_command, cmdstr)


    def _soundfn(self, filename):
        return lambda : self.playSound(filename)

    def obs_timer(self, tag, title, iconfile, soundfile, time_sec):
        def callback(*args):
            pass
        
        soundfn = self._soundfn(soundfile)
        try:
            self.gui.obs_timer(tag, title, iconfile, soundfn, time_sec,
                               callback)

            self.monitor.setvals(['g2task'], tag, complete=time.time(),
                                 status=0)
            return ro.OK
    
        except Exception, e:
            raise Exception("failed to start timer: %s" % (str(e)))
            
    
    def obs_confirmation(self, tag, title, iconfile, soundfile, btnlist):
        def callback(idx, vallist):
            if idx == None:
                self.monitor.setvals(['g2task'], tag, status=-1,
                                     complete=time.time(),
                                     msg="User cancelled dialog!")
            else:
                self.monitor.setvals(['g2task'], tag, status=idx+1,
                                     msg="OK",
                                     complete=time.time())

        soundfn = self._soundfn(soundfile)
        try:
            self.gui.obs_confirmation(tag, title, iconfile, soundfn, btnlist,
                                      callback)
            return ro.OK
    
        except Exception, e:
            raise Exception("failed to start confirmation dialog: %s" % (str(e)))
    
    def obs_userinput(self, tag, title, iconfile, soundfile, itemlist):
        def callback(idx, vallist, resDict):
            if idx == None:
                self.monitor.setvals(['g2task'], tag, status=-1,
                                     msg="User cancelled dialog!",
                                     complete=time.time())
            else:
                self.monitor.setvals(['g2task'], tag, status=idx+1,
                                     msg="OK", values=resDict,
                                     complete=time.time())

        soundfn = self._soundfn(soundfile)
        try:
            self.gui.obs_userinput(tag, title, iconfile, soundfn, itemlist,
                                   callback)

            return ro.OK
    
        except Exception, e:
            raise Exception("failed to start userinput dialog: %s" % (str(e)))
    

    def obs_combobox(self, tag, title, iconfile, soundfile, itemlist):
        def callback(idx, vallist, resDict):
            if idx == None:
                self.monitor.setvals(['g2task'], tag, status=-1,
                                     msg="User cancelled dialog!",
                                     complete=time.time())
            else:
                self.monitor.setvals(['g2task'], tag, status=idx+1,
                                     msg="OK", values=resDict,
                                     complete=time.time())

        soundfn = self._soundfn(soundfile)
        try:
            self.gui.obs_combobox(tag, title, iconfile, soundfn, itemlist,
                                  callback)

            return ro.OK
    
        except Exception, e:
            raise Exception("failed to start combobox dialog: %s" % (str(e)))

    def obs_play_sound_file(self, tag, soundfile):
        try:
            self.playSound(soundfile)
            return ro.OK
    
        except Exception, e:
            raise Exception("failed to play sound file '%s': %s" % (
                soundfile, str(e)))
    
    def get_ope_paths(self, dummy):
        # dummy argument for Tajitsu-san's C code
        return self.gui.get_ope_paths()

    def load_page(self, filename):
        self.logger.info('filename to load is %s' % filename)
        self.gui.load_file(filename)
        return 0
#END

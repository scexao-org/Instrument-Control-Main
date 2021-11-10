#
# g2Instrument.py -- generic base class for an instrument (BASECAM) and
#   a framework for interfacing with the OCS (Instrument)
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Sun Feb  5 19:28:17 HST 2012
#]
import sys, os
import time
import traceback
import threading

import Task
from Bunch import Bunch, threadSafeBunch
import remoteObjects as ro
import remoteObjects.Monitor as Monitor
from cfg.INS import INSdata as INSconfig


class CamError(Exception):
    pass

class CamInterfaceError(CamError):
    pass

class CamCommandError(CamError):
    pass

class BASECAM(object):
    """For future use, common instrument base class.
    """

    def __init__(self):
        pass
        
    def initialize(self, ocsint):
        """Initialize the instrument such that it can be started with
        start().  Parameter _ocsint_ is the object through which we can
        communicate with the OCS via certain methods.
        """
        self._ocsint = ocsint
        

    def start(self, wait=True):
        """Start the instrument.  Starts any threads, etc.
        """
        pass

    def stop(self, wait=True):
        """Stop the instrument.  Stops any threads, etc.
        """
        pass

    def ui(self, options, args, ev_quit, logger=None):
        # Placeholder for cam-supplied user interface
        print "Press ^C to terminate instrument..."
        while not ev_quit.isSet():
            ev_quit.wait(0.01)
    

class Instrument(object):

    def __init__(self, logger, threadPool, monitor, monchannels,
                 ev_quit=None, timeout=0.1,
                 archiveint=None, frameint=None, statusint=None,
                 env=None, obcpnum=9, numthreads=50,
                 soundsink=None):

        self.monitor = monitor
        self.monchannels = monchannels
        self.threadPool = threadPool
        self.soundsink = soundsink

        if not ev_quit:
            self.ev_quit = threading.Event()
        else:
            self.ev_quit = ev_quit
        self.logger = logger
        self.numthreads = numthreads
        self.timeout = timeout

        self.lock = threading.RLock()

        # For reading various instrument configuration values
        self.insconfig = INSconfig()
        self.obcpnum = obcpnum

        # Holds various client-settable parameters
        # Install reasonable defaults for timeouts:
        #  o 15.0 sec for a status request
        #  o 120.0 sec for a file transfer request
        self.params = threadSafeBunch(timeout_status=15.0,
                                      timeout_thrucmd=None,
                                      timeout_filexfr=120.0)
        
        # For task inheritance:
        self.tag = 'Instrument'
        self.shares = ['logger', 'threadPool', 'monitor', 'params']

        # For our status values
        self._mystatus = {}

        # For OCS status values
        # This could also use a SOSS.status object
        #self._ocsstatus = threadSafeBunch()

        # Set up linkage between ourself and frame interface
        self.frameint = frameint

        # Set up linkage between ourself and status interface
        self.statusint = statusint

        # Set up linkage between ourself and archive interface
        self.archiveint = archiveint

        # Create the "environment" (see loadPersonality())
        if env:
            self.env = env
        else:
            self.env = Bunch(INST_PATH='.')

        # Holds info about loaded camera modules
        self.cams = threadSafeBunch()

        # Holds information about running commands
        self.cmdHist = {}


    def loadPersonality(self, camName, alias=None, moduleDir=None):

        # TODO: if reloading, need to call stop() on currently
        # executing cam
        camName = camName.upper()

        # Make sure cam module dir is in our import path
        if not moduleDir:
            thisDir = os.path.split(sys.modules[__name__].__file__)[0]
            moduleDir = '%s/cams/%s' % (thisDir, camName)
        if not moduleDir in sys.path:
            sys.path.append(moduleDir)

        # Instrument will be referred to by this alias
        if not alias:
            alias = camName
        alias = alias.upper()
            
        try:
            if self.cams.has_key(alias):
                camInfo = self.cams[alias]
            
                self.logger.info("Reloading instrument personality '%s'" % \
                                 camName)
                module = camInfo.module
                reload(module)

            else:
                self.logger.debug("Loading instrument personality '%s'" % \
                                  camName)
                #moduleName = ("SOSS.cams.%s" % camName)
                moduleName = camName
                module = __import__(moduleName)

                camInfo = Bunch(module=module)
                self.cams[alias] = camInfo

        except ImportError, e:
            self.logger.error("Error loading instrument personality '%s': %s" % \
                              (camName, str(e)))
            self.logger.error("sys.path is '%s'" % ':'.join(sys.path))
            self.logger.error("Instrument personality not loaded!")
            return
        
        try:
            # Get the class constructor for this instrument personality
            classObj = getattr(module, camName)

        except AttributeError, e:
            # Not in this module, keep looking...
            self.logger.error("Cannot find a class corresponding to name '%s'" % \
                              camName)
            self.logger.error("Instrument personality not loaded!")
            return
        
        # Create the instrument personality
        cam = classObj(self.logger, self.env, ev_quit=self.ev_quit)
        camInfo.cam = cam
        cam._camName = alias

        # Check for special methods
        try:
            camInfo.dispatch = cam.dispatchCommand
        except AttributeError:
            camInfo.dispatch = None
        try:
            camInfo.cancel = cam.cancelCommand
        except AttributeError:
            camInfo.cancel = None

        # Register instrument interface <--> cam
        cam.initialize(self)

    def _reload_and_restart(self, camName):
        # This is only as good as the cam's stop() method
        self.logger.info("Trying to stop camera %s..." % (camName))
        self.stopCam(camName)

        self.logger.info("Reloading camera module %s..." % (camName))
        self.loadPersonality(camName)
        
        self.logger.info("Trying to start camera %s..." % (camName))
        self.startCam(camName)
        
    def reload_and_restart(self, camName):
        # Start another task so that cam's thread (if called from cam)
        # can go back and be terminated properly
        t = Task.FuncTask2(self._reload_and_restart, camName)
        t.init_and_start(self)
        

    def get_INSconfig(self):
        return self.insconfig
    
    def get_obcpnum(self):
        return self.obcpnum
    
        
    def startCam(self, camName, wait=True):
        if not self.cams.has_key(camName):
            self.logger.warn("No instrument personality '%s' to start" % \
                             camName)
        else:
            camInfo = self.cams[camName]
            # Do any initialization of the module
            camInfo.cam.start()
            
    def stopCam(self, camName, wait=True):
        if not self.cams.has_key(camName):
            self.logger.warn("No instrument personality '%s' to stop" % \
                             camName)
        else:
            camInfo = self.cams[camName]

            
    def shutdown(self, res):
        """
        Called by the instrument to let us know to shutdown the interface.
        """
        # TODO: record result?
        #self.ev_quit = True
        pass

    
    def start(self, wait=True):

        # Start the instrument(s)
        for cam in self.cams.keys():
            self.startCam(cam, wait=wait)
            
        # start the command servers
        self.ro_svc = {}
        for cam in self.cams.keys():
            self.ro_svc[cam] = ro.remoteObjectServer(cam,
                                                     obj=self,
                                                     logger=self.logger,
                                                     method_list=['executeCmd',
                                                                  'reload_module'],
                                                     usethread=True,
                                                     threadPool=self.threadPool)
            self.ro_svc[cam].ro_start(wait=True)
    
    def stop(self, wait=True):

        # Stop the instrument(s)
        for cam in self.cams.keys():
            self.ro_svc[cam].ro_stop(wait=True)

            self.stopCam(cam, wait=wait)

        # Last ditch effort
        self.ev_quit.set()
        self.logger.info("INSTRUMENT STOPPED.")


    def ui(self, camName, options, args, ev_quit, logger=None):
        """Lookup the user interface function in the cam and run it.
        """
        try:
            camInfo = self.cams[camName]
        
        except KeyError:
            result = "ERROR: No personality loaded for '%s'!" % (camName)
            self.logger.error(result)
            raise CamError(result)

        if not logger:
            logger = self.logger

        # This method will default to the one in BASECAM if not overridden
        return camInfo.cam.ui(options, args, ev_quit, logger=logger)

    def reload_module(self, moduleName):
        reload(sys.modules[moduleName])
        
    #####################################
    # COMMAND FUNCTIONS
    #####################################

    def executeCmd(self, camName, tag, cmdName, args, kwdargs):
        """Called to execute a generic instrument command.  Interprets
        cmdName (a string) and calls the appropriate method with args
        and keyword args (kwdargs)."""

        self.logger.debug("Command received: subsys=%s cmdName=%s args=%s tag=%s" % (
                camName, cmdName, str(kwdargs), tag))
        
        try:
            camInfo = self.cams[camName]
        
        except KeyError:
            result = "ERROR: No personality loaded for '%s'!" % (camName)
            self.logger.error(result)
            raise CamError(result)

        if camInfo.dispatch:
            method = camInfo.dispatch
            # Cam has a special dispatch method.
            args = (tag, cmdName, args, kwdargs)
            kwdargs = {}

        else:
            try:
                # Try to look up the named method
                method = getattr(camInfo.cam, cmdName)

            except AttributeError, e:
                # Push command name back on argument list as first arg
                args.insert(0, cmdName)
                try: 
                    method = getattr(camInfo.cam, 'defaultCommand')
                except AttributeError, e:
                    result = "ERROR: No such method in subsystem: %s" % (cmdName)
                    self.logger.error(result)
                    raise CamError(result)

        self.cmdHist[tag] = Bunch(camInfo=camInfo)
        try:
            task = Task.FuncTask(self.doExecute,
                                 [tag, method, args, kwdargs],
                                 {},
                                 logger=self.logger)
            task.init_and_start(self)
        
        except Exception, e:
            result = "Error invoking task: %s" % (e)
            self.logger.error(result)
            #del self.cmdHist[tag]
            raise CamError(result)

        return ro.OK


    def doExecute(self, tag, method, args, kwdargs):
        self.cmdHist[tag].time_start = time.time()
        res = (0, 'OK')
        try:
            # call method and collect result
            res = method(*args, **kwdargs)

            # If a cam raises an exception, the command is recorded as
            # a failure.  If the cam returns a value, it is considered
            # a success, EXCEPT in the case where it is an int or tuple
            # For backward-compatibility with SIMCAM cams we check the
            # return value if it is one of these
            self.logger.debug("Return value is %s" % str(res))
            if res == None:
                res = (0, 'OK')

            if isinstance(res, tuple) and (len(res) == 2):
                (status, result) = res
                if not isinstance(status, int):
                    self.logger.error("Bad status return (%s)--should be type int" % (str(status)))
                    status = 1
                if not isinstance(result, str):
                    self.logger.error("Bad message return (%s)--should be type str" % (str(result)))
                    result = "ERROR: %s" % (str(result))
                res = (status, result)

            elif isinstance(res, int):
                if res == 0:
                    res = (0, 'OK')
                else:
                    res = (res, 'ERROR')

            else:
                res = (0, 'OK')

        except CamCommandError, e:
            # This is the Pythonic way for the instrument to cleanly
            # signal an error
            msg = str(e)
            self.logger.error(msg)
            res = (1, msg)
                    
        except Exception, e:
            msg = "ERROR: Command terminated with exception: %s" % \
                  (str(e))
            try:
                (extype, value, tb) = sys.exc_info()
                self.logger.error("Traceback:\n%s" % \
                                  "".join(traceback.format_tb(tb)))

                # NOTE: to avoid creating a cycle that might cause
                # problems for GC--see Python library doc for sys module
                tb = None

            except Exception, e:
                self.logger.error("Traceback information unavailable.")
                
            res = (1, msg)

        end_time = time.time()
        self.cmdHist[tag].time_end = end_time
        #del self.cmdHist[tag]
        self.monitor.setvals(self.monchannels, tag, end_time=end_time,
                             end_result=res[0], end_payload=res[1],
                             msg=res[1], time_done=end_time, result=res[0],
                             done=True)

    def setvals(self, tag, **kwdargs):
        return self.monitor.setvals(self.monchannels, tag, **kwdargs)

    def get_monitor(self):
        return self.monitor

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

        if vals.has_key('task_code'):
            res = vals['task_code']
            # Interpret task results:
            #   task_code == 0 --> OK   task_code != 0 --> ERROR
            if res == 3:
                self.logger.info("Task cancelled (%s)" % bnch.path)
                self.cancel_commands(bnch.path)


    def cancel_commands(self, tagpfx):
        """Find all commands that are tagged with this command prefix and
        call the cancel method (if available) with this tag.
        """
        for tag in self.cmdHist.keys():
            if not tag.startswith(tagpfx):
                continue

            bnch = self.cmdHist[tag]
            camInfo = bnch.camInfo
            if camInfo.cancel:
                camInfo.cancel(tag)

    
    #####################################
    # "THROUGH" COMMANDS (EXPERIMENTAL)
    #####################################
    
    def execOCScommand(self, cmdstr, timeout=None):

        raise CamInterfaceError("This feature is not yet implemented!")

    #####################################
    # STATUS FUNCTIONS
    #####################################
    
    def exportStatusTable(self, tableName):
        """
        Send one table of status data to OCS.  tableName should be
        a valid table that exists on the OCS side, and has been added
        with addStatusTable().
        """
        if not self._mystatus.has_key(tableName):
            errmsg = "No such table defined -- name=%s" % tableName
            #self.logger.error(errmsg)
            raise CamError("Error exporting status: %s" % errmsg)

        statusDict = {}

        # If there is a mapping between the instrument aliases and
        # the OCS aliases, then transform the keys
        tblInfo = self._mystatus[tableName]
        if tblInfo.mapping != None:
            for ocsAlias, insAlias in tblInfo.mapping.items():
                statusDict[ocsAlias] = tblInfo.table[insAlias]
        else:
            statusDict.update(tblInfo.table)

        print "STATUS IS", statusDict
        self.logger.debug("statusDict = %s" % str(statusDict))
        try:
            self.statusint.store(statusDict)

        except ro.remoteObjectError, e:
            raise CamInterfaceError(e)
            
        self.logger.debug("Sending status finished.")
        return 0


    def exportStatus(self):
        """
        Send all my defined tables of status data to OCS.
        """
        for tableName in self._mystatus.keys():
            self.exportStatusTable(tableName)

        return 0

        
    def addStatusTable(self, tableName, keyOrder, formatStr=None,
                       mapping=None):
        """
        Add a new status table to the set of status tables.  This MUST be
        also defined on the SOSS side.
        """

        table = threadSafeBunch()

        # Construct a format string if user did not supply one.
        # TODO (maybe): use StatusAlias.def to construct format string?
        if not formatStr:
            formatStr = ''.join(map(lambda var: '%%(%s)s' % var, keyOrder))

        # If no mapping is passed in, construct a default one
        if mapping == None:
            inscode = self.insconfig.getCodeByNumber(self.obcpnum)

            mapping = {}
            for key in keyOrder:
                mapping['%s.%s' % (inscode, key.upper())] = key
                
        newtbl = threadSafeBunch(name=tableName, table=table,
                                 keyOrder=keyOrder, formatStr=formatStr,
                                 mapping=mapping)

        self._mystatus[tableName] = newtbl
        return table

        
    def getInternalStatusInfo(self, tableName):
        try:
            tableBunch = self._mystatus[tableName]
            
        except KeyError, e:
            raise CamError("No such table defined: '%s'" % (tableName))
                
        return tableBunch


    def getStatusTable(self, tableName):
        """
        Return a local status table object that was created with
        addStatusTable()
        """
        tableBunch = self.getInternalStatusInfo(tableName)
        return tableBunch.table
        

    def getStatusValue(self, tableName, key):
        """
        Return a local status value for key from table tableName.
        """
        table = self.getStatusTable(tableName)
            
        # May raise KeyError, that's OK
        return table[key]


    def getStatusDict(self, tableName, statusDict):
        table = self.getStatusTable(tableName)
            
        # May raise KeyError, that's OK
        table.fetchDict(statusDict)
        return statusDict


    def getStatusList(self, tableName, keySeq):
        table = self.getStatusTable(tableName)
            
        # May raise KeyError, that's OK
        return table.fetchList(keySeq)


    def setStatusValue(self, tableName, key, value):
        """
        Set a local status value for key in table tableName.
        """
        table = self.getStatusTable(tableName)
                
        table[key] = value


    def setStatusDict(self, tableName, statusDict):
        table = self.getStatusTable(tableName)
                
        table.update(statusDict)


    def setStatus(self, tableName, **kwdargs):
        self.setStatusDict(tableName, kwdargs)


    def requestOCSstatus(self, statusDict, timeout=None):
        """
        Request OCS status using the standard instrument protocol.
        statusDict is a dict whose keys are the status aliases you want
        to fetch.  The dictionary is filled in with the values.
        """

        if timeout == None:
            timeout = self.params.timeout_status

        # TODO: timeout not yet supported!
        try:
            self.logger.debug("request=%s" % (str(statusDict)))

            resDict = self.statusint.fetch(statusDict)
            
            statusDict.update(resDict)
            self.logger.debug("result=%s" % (str(statusDict)))
            
        except ro.remoteObjectError, e:
            raise CamInterfaceError(e)

        return 0


    def validateStatus(self, statusDict):
        """
        Sanity check on the items in statusDict.  If any are bad status
        values, return the keys in a list.
        """
        res = []
        for (alias, value) in statusDict.items():
            strval = str(value)
            # TODO: this is a very rough approximation of error.
            if strval.startswith('#') or (strval == 'UNDEF'):
                res.append(alias)
                
        return res


    def requestOCSstatusList2Dict(self, aliasList, timeout=None):
        """
        Takes a list of status aliases and returns a dict of OCS status
        values.
        """

        self.logger.debug("aliasList=%s" % (str(aliasList)))

        # Turn the list of aliases into a dict of keys
        #statusDict = {}.fromkeys(aliasList, None)
        statusDict = {}.fromkeys(aliasList, '##ERROR##')

        # Get the status
        self.requestOCSstatus(statusDict, timeout=timeout)

        return statusDict

        
    def requestOCSstatusList2List(self, aliasList, timeout=None):
        """
        Takes a list of status aliases and returns a list of OCS status
        values in the same order.
        """

        statusDict = self.requestOCSstatusList2Dict(aliasList,
                                                    timeout=timeout)

        # Upack back into list
        res = []
        for key in aliasList:
            res.append(statusDict[key])

        return res

        
    def getOCSstatus(self, statusDict):
        """
        In Gen2, there is no difference between requestOCSstatus and
        getOCSstatus, except for the return value.
        """
        self.requestOCSstatus(statusDict)

        return 0

        
    def getOCSstatusList2Dict(self, aliasList):
        """
        In Gen2, there is no difference between getOCSstatusList2Dict and
        requestOCSstatusList2Dict.
        """
        return self.requestOCSstatusList2Dict(aliasList)

        
    def getOCSstatusList2List(self, aliasList):
        """
        In Gen2, there is no difference between getOCSstatusList2List and
        requestOCSstatusList2List.
        """
        return self.requestOCSstatusList2List(aliasList)

        
    #####################################
    # FITS TRANSFER FUNCTIONS
    #####################################

    def get_filesize(self, fitspath):
        # Stat the FITS file to get the size.
        try:
            statbuf = os.stat(fitspath)

        except OSError, e:
            raise CamInterfaceError("Cannot stat file '%s': %s" % \
                                    (fitspath, str(e)))

        return statbuf.st_size

    def archive_framelist(self, framelist, timeout=None,
                          host='lookup', transfermethod='lookup'):
        """
        Archive a list of frames.  'framelist' should be a list of tuples,
        where each tuple is of the one of the following forms:
           (frameid, fitspath)
           (frameid, fitspath, size)
           (frameid, fitspath, size, md5sum)
        frameid is the Subaru frame id of the file (e.g. 'SUKA00047325')
        and fitspath is the path to the FITS file to be archived.
        size is the size of the file in bytes and md5sum is the MD5
        checksum of the file.
        """

        if timeout == None:
            timeout = self.params.timeout_filexfr

        self.logger.debug("archiving %s" % (str(framelist)))

        # TODO: timeout is not yet supported!
        try:
            self.archiveint.archive_framelist(host, transfermethod, 
                                              framelist)
            
        except ro.remoteObjectError, e:
            raise CamInterfaceError(e)
        
        return 0
    
        
    def archive_fits(self, framelist):
        self.logger.error("***DEPRECATED FUNCTION--PLEASE USE FUNCTION 'archive_framelist' INSTEAD ***")
        return self.archive_framelist(framelist)

        
    def archive_frame_md5(self, frameid, fitspath, md5sum, timeout=None,
                          host='lookup', transfermethod='lookup'):
        """
        Archive a single FITS frame.  frameid is the Subaru frame id that
        has already been allocated (either passed to the instrument in the
        command, or fetched using getFrame()) and fitspath is the path
        to the fits file.  The file does not need to have the same name
        as the frame id.
        """

        size = self.get_filesize(fitspath)
        framelist = [ (frameid, fitspath, size, md5sum) ]
        
        return self.archive_framelist(framelist, timeout=timeout,
                                      host=host, transfermethod=transfermethod)

        
    def archive_frame(self, frameid, fitspath, timeout=None,
                      host='lookup', transfermethod='lookup'):
        """
        Archive a single FITS frame.  frameid is the Subaru frame id that
        has already been allocated (either passed to the instrument in the
        command, or fetched using getFrame()) and fitspath is the path
        to the fits file.  The file does not need to have the same name
        as the frame id.
        """

        size = self.get_filesize(fitspath)
        framelist = [ (frameid, fitspath, size) ]
        
        return self.archive_framelist(framelist, timeout=timeout,
                                      host=host, transfermethod=transfermethod)

        
    def archive(self, filepath, filetype='fits', timeout=None, frtype='A',
                host='lookup', transfermethod='lookup'):
        """
        Archive a single file, obtaining a frame id automatically for the
        purpose.  Currently only filetype=='fits' is supported.
        """

        if timeout == None:
            timeout = self.params.timeout_status
            
        if filetype.lower() != 'fits':
            raise CamError("Currently I can only archive FITS files!")
        
        # Get a frame of the appropriate type
        frameid = self.getFrame(frtype)

        return self.archive_frame(frameid, filepath, timeout=timeout,
                                  host=host, transfermethod=transfermethod)

        
    #####################################
    # FRAME ID FUNCTIONS
    #####################################
    
    def getFrames(self, num, frtype):
        """
        Obtain 'num' frame ids of type 'frtype'.  Returns a list of 'num'
        frames.  'frtype' should be 'A' or 'Q'.
        """
        if self.frameint == None:
            errmsg = "No frame interface found!"
            #self.logger.error(errmsg)
            raise CamInterfaceError(errmsg)

        obcpnum = self.get_obcpnum()
        insname = self.insconfig.getNameByNumber(obcpnum)
        
        if not frtype in ('A', 'Q'):
            raise CamError("Frame type (%s) must be 'A' or 'Q'" % str(type))

        try:
            (status, framelist) = self.frameint.getFrames(insname, frtype, num)

            assert(status == ro.OK), \
                CamInterfaceError("getFrames() unexpected status return: '%s'" % (
                                     str(status)))

            assert(isinstance(framelist, list)), \
                CamInterfaceError("getFrames() unexpected return: '%s'" % (
                                     str(framelist)))
                
            assert(len(framelist) == num), \
                CamInterfaceError("getFrames() frame list length != %d" % (
                num))

            return framelist
        
        except ro.remoteObjectError, e:
            raise CamInterfaceError(e)

        
    def getFrame(self, frtype):
        """
        Obtain a single Subaru frame id.  'frtype' should be 'A' or 'Q'.
        """
        framelist = self.getFrames(1, frtype)
        return framelist[0]
        
        
    #####################################
    # SOUND FUNCTIONS
    #####################################
    
    def playLocalSoundFile(self, filepath, format=None):
        if self.soundsink != None:
            self.soundsink.playFile(filepath, format=format)
        else:
            raise CamInterfaceError("This cam was not configured with a SoundSink")
        
    def playSoundBuffer(self, buffer, format='ogg'):
        if self.soundsink != None:
            self.soundsink.playSound(buffer, format=format)
        else:
            raise CamInterfaceError("This cam was not configured with a SoundSink")

        
    #####################################
    # MISC FUNCTIONS
    #####################################
    
        
# END

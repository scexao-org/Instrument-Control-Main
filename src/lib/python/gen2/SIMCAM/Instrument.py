#
# Instrument.py -- generic base class for an instrument (BASECAM) and
#   a framework for interfacing with the OCS (Instrument)
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Apr 25 20:26:30 HST 2011
#]
import sys, os
import re
import threading
import traceback

import Task
from Bunch import Bunch, threadSafeBunch

import SOSS.DotParaFiles.ParaValidator as ParaValidator
from SOSS.parse.para_parser import NOP
from cfg.INS import INSdata as INSconfig
from SOSS.DAQtk import OCSintError
from SOSS.frame import frameError
from SOSS.status import statusError


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

    def __init__(self, logger, ev_quit=None, timeout=0.1,
                 ocsint=None, frameint=None, statusObj=None,
                 allowNoPara=False, env=None, obcpnum=9,
                 threadPool=None, numthreads=20):

        self.lock = threading.RLock()
        if not ev_quit:
            self.ev_quit = threading.Event()
        else:
            self.ev_quit = ev_quit
        self.logger = logger
        self.numthreads = numthreads
        self.timeout = timeout
        self.allowNoPara = allowNoPara

        # For reading various instrument configuration values
        self.insconfig = INSconfig()
        self.obcpnum = obcpnum

        # Holds various client-settable parameters
        # Install reasonable defaults for timeouts:
        #  o 15.0 sec for a status request
        #  o 240.0 sec for a file transfer request
        self.params = threadSafeBunch(timeout_status=15.0,
                                      timeout_thrucmd=None,
                                      timeout_filexfr=240.0)
        
        # Thread pool for autonomous tasks
        if threadPool:
            self.threadPool = threadPool
            self.own_threadPool = False
        else:
            self.threadPool = Task.ThreadPool(logger=self.logger,
                                              ev_quit=self.ev_quit,
                                              numthreads=self.numthreads)
            self.own_threadPool = True
        # For task inheritance:
        self.tag = 'Instrument'
        self.shares = ['logger', 'threadPool', 'params']

        # For our status values
        self._mystatus = {}

        # For OCS status values
        # This could also use a SOSS.status object
        #self._ocsstatus = threadSafeBunch()

        # Set up linkage between ourself and frame interface (SOSS.frame)
        self.frameint = frameint

        # Set up linkage between ourself and status interface (SOSS.status)
        self.statusObj = statusObj

        # Create the "environment" (see loadPersonality())
        if env:
            self.env = env
        else:
            self.env = Bunch(INST_PATH='.')

        # Set up linkage between ourself and OCS interface (SOSS.DAQtk)
        self.ocsint = ocsint
        if self.ocsint:
            self.ocsint.initialize(self)

        # Holds info about loaded camera modules
        self.cams = threadSafeBunch()

        # Holds para file definitions and parameter validators for
        # commands
        self.validator = ParaValidator.ParaValidator(self.logger)


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
        
    def executeCmd(self, cmdstr):
        """Called to execute a generic instrument command.  Interprets
        cmdstr (a string) and calls the appropriate method."""
        
        self.logger.info("Command received: '%s'" % cmdstr)

        # Convert a SOSS device dependent command string into a Python
        # method invocation.
        # Expected arg structure is "EXEC <SUBSYS> <CMD> <PARAM1>=<ARG1> ..."
        #
        status = 1
        result = 'ERROR'
        tbstr = ''
        try:
            # Process command and validate parameters
            self.logger.debug("validating: %s" % (cmdstr))
            (subsys, cmdName, args, kwdargs, res) = \
                     self.validator.processCmd(cmdstr, noparaok=True)
            if res != 0:
                errmsg = "no validation done--missing para file?"
                # If user specified --noparaok, then issue a warning and
                # proceed, otherwise log as an error and bail out
                if not self.allowNoPara:
                    self.logger.error(errmsg)
                    return (status, "ERROR: cmd '%s': %s" % \
                            (cmdstr, errmsg))

                self.logger.warn(errmsg)
                
            else:
                # Remove keyword args that are NOPs so that they get
                # default values in Python method
                for key, val in kwdargs.items():
                    if val == NOP:
                        self.logger.debug("removing kwd arg=%s" % (key))
                        del kwdargs[key]

            # If there is a SUBSYS=YYYY parameter, then use it
            # to select the camera to invoke the command in;
            # otherwise use the default one from "EXEC <SUBSYS> <CMD> ..."
            camName = kwdargs.get('subsys', subsys)

            # Now invoke method in instrument personality
            self.logger.debug("calling: subsys=%s method=%s args=%s" % \
                              (camName, cmdName, str(kwdargs)))
            if not self.cams.has_key(camName):
                result = "ERROR: No personality loaded for '%s'!" % camName
                self.logger.error(result)
                return (status, result)

            # Lookup the method
            try:
                method = getattr(self.cams[camName].cam, cmdName)

            # If there is no method by that name, try to invoke the
            # method with the name "defaultCommand"
            except AttributeError, ne:
                # Push command name back on argument list as first arg
                args.insert(0, cmdName)
                try: 
                    method = getattr(self.cams[camName].cam, 'defaultCommand')
                except AttributeError, e:
                    result = "ERROR: %s" % str(ne)
                    return (status, result)

            # Call the method in the instrument
            status = method(*args, **kwdargs)

            self.logger.debug("Return value is %s" % str(status))

            # Acceptable return types to DAQtk interface are int or
            # (int, str).
            if (type(status) == int) or (type(status) == type((0, ""))):
                return status

            # Assume Pythonic approach--method would have raised an
            # exception if there was a problem.
            return (0, 'COMPLETE')

        except ParaValidator.ParaValidatorError, e:
            result = "ERROR: Parameter validation error: %s" % \
                     (str(e))
                    
        except CamCommandError, e:
            # This is the Pythonic way for the instrument to cleanly
            # signal an error
            result = str(e)
                    
        except Exception, e:
            result = "ERROR: Command '%s' terminated with exception: %s" % \
                     (cmdstr, str(e))
            try:
                (extype, value, tb) = sys.exc_info()
                tbstr = "".join(traceback.format_tb(tb))
                self.logger.error("Traceback:\n%s" % (tbstr))

                # NOTE: to avoid creating a cycle that might cause
                # problems for GC--see Python library doc for sys module
                tb = None

            except Exception, e:
                self.logger.error("Traceback information unavailable.")
                tbstr = ''

        self.logger.error(result)

        # Callback into the CAM for error results
        try: 
            method = getattr(self.cams[camName].cam, 'exceptionResult')
            
        except AttributeError, e:
            return (status, result)

        try:
            tmp = method(camName, cmdName, str(kwdargs), result, tbstr)

            if isinstance(tmp, basestring):
                result = tmp
                
        except Exception, e:
            pass
        
        return (status, result)


    def get_INSconfig(self):
        return self.insconfig
    
    def get_obcpnum(self):
        return self.obcpnum
    
        
    def startCam(self, camName, wait=True):
        if not self.cams.has_key(camName):
            self.logger.warn("No instrument personality '%s' to start" % \
                             camName)
        else:
            self.cams[camName].cam.start()
            
    def stopCam(self, camName, wait=True):
        if not self.cams.has_key(camName):
            self.logger.warn("No instrument personality '%s' to stop" % \
                             camName)
        else:
            self.cams[camName].cam.stop()

            
    def shutdown(self, res):
        """
        Called by the instrument to let us know to shutdown the interface.
        """
        # TODO: record result?
        #self.ev_quit = True
        pass

    
    def start(self, wait=True):

        # Start any threads, etc.
        if self.own_threadPool:
            self.threadPool.startall(wait=True)

        # Start the legacy ocs (DAQtk) interface
        if not self.ocsint:
            self.logger.warn("No DAQtk interface to start")
        else:
            self.ocsint.start(wait=wait)
        
        # Start the instrument(s)
        for cam in self.cams.keys():
            self.startCam(cam, wait=wait)
        
    
    def stop(self, wait=True):

        # Stop the instrument(s)
        for cam in self.cams.keys():
            self.stopCam(cam, wait=wait)

        # Stop the legacy ocs (DAQtk) interface
        if not self.ocsint:
            self.logger.warn("No DAQtk interface to stop")
        else:
            self.logger.info("Stopping DAQtk interface.")
            self.ocsint.stop(wait=wait)
        
        # Stop our threads, etc.
        if self.own_threadPool:
            self.threadPool.stopall(wait=wait)

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
        

    def loadParaBuf(self, parakey, paraBuf):
        """Load a buffer with a PARA definition into the validator.
        """
        self.validator.loadParaBuf(parakey, paraBuf)
        

    def loadParaDir(self, paraDir):
        """Loads directory full of PARA files into the validator.
        """
        self.validator.loadParaDir(paraDir)
        

    def loadParaDirs(self, paraDirs):
        """Loads multiple directories of PARA files into the validator.
        """
        self.validator.loadParaDirs(paraDirs)
        

    def __check_interface(self):
        """Check whether we really have a valid OCS interface.
        """
        if not self.ocsint:
            raise CamInterfaceError("No OCS interface found!")


    def __check_result(self, res):
        """Interpret low level protocol codes returned from the OCS
        interface.
        """

        self.logger.debug("res=%s" % str(res))
        try:
            pkt_type, res_code, msgstr = res

        except IndexError:
            errmsg = "OCS interface returned unexpected format: '%s'" % (
                str(res))
            #self.logger.error(errmsg)
            raise CamInterfaceError(errmsg)
            
        if (pkt_type != 'end') or (res_code != 0):
            errmsg = "pkt_type=%s res_code=%d msgstr=%s" % (
                pkt_type, res_code, msgstr)
            #self.logger.error(errmsg)
            raise CamInterfaceError("OCS interface low-level protocol error: %s" % (
                errmsg))

    # This is here for compatibility with g2cam
    def setvals(self, tag, **kwdargs):
        pass
        
    #####################################
    # "THROUGH" COMMANDS (EXPERIMENTAL)
    #####################################
    
    def execOCScommand(self, cmdstr, timeout=None):

        self.__check_interface()

        if timeout == None:
            timeout = self.params.timeout_status
            
        try:
            res = self.ocsint.execCommand(cmdstr, timeout=timeout)
            self.__check_result(res)

        except OCSintError, e:
            raise CamInterfaceError(e)

        return res

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
        
        self.__check_interface()

        tableBunch = self._mystatus[tableName]

        self.logger.debug("Formatting table for %s" % tableName)
        try:
            statusdata = (tableBunch.formatStr % tableBunch.table)
            print "STATUS DATA len=%d" % len(statusdata)
            print statusdata

        except Exception, e:
            errmsg = "Exception raised formatting status buffer: %s" % str(e)
            #self.logger.error(errmsg)
            raise CamError(errmsg)
        
        self.logger.debug("Sending buffer for %s" % tableName)
        try:
            self.ocsint.sendStatus(tableBunch.name, statusdata)

        except OCSintError, e:
            raise CamInterfaceError(e)
            
        self.logger.debug("Sending status finished.")
        return 0


    def exportStatus(self):
        """
        Send all my defined tables of status data to OCS.
        """
        self.__check_interface()

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
        return table.fetchList(KeySeq)


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

        self.__check_interface()

        if timeout == None:
            timeout = self.params.timeout_status
            
        try:
            res = self.ocsint.requestStatus(statusDict, timeout=timeout)
            self.__check_result(res)
            
        except OCSintError, e:
            raise CamInterfaceError(e)

        return res

    def validateStatus(self, statusDict):
        """
        Sanity check on the items in statusDict.  If any are bad status
        values, return the keys in a list.
        """
        res = []
        for (alias, value) in statusDict.items():
            strval = str(value)
            # TODO: this is a very rough approximation of error.  What does
            # DAQtk.py return?
            if strval.startswith('#') or (strval == 'UNDEF'):
                res.append(alias)
                
        return res

    def requestOCSstatusList2Dict(self, aliasList, timeout=None):
        """
        Takes a list of status aliases and returns a dict of OCS status
        values.
        """

        # Turn the list of aliases into a dict of keys
        statusDict = {}.fromkeys(aliasList, None)

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
        Get status using the more efficient status protocol.
        statusDict is a dict whose keys are the status aliases you want
        to fetch.  The dictionary is filled in with the values.
        """
        if self.statusObj == None:
            errmsg = "No OCS status 2 interface found!"
            #self.logger.error(errmsg)
            raise CamInterfaceError(errmsg)

        try:
            self.statusObj.get_statusValuesDict(statusDict)

        except statusError, e:
            raise CamInterfaceError(e)

        return 0

        
    def getOCSstatusList2Dict(self, aliasList):
        """
        Takes a list of status aliases and returns a dict of OCS status
        values.
        """

        # Turn the list of aliases into a dict of keys
        statusDict = {}
        statusDict.fromkeys(aliasList, None)

        # Get the status
        self.getOCSstatus(statusDict)

        return statusDict

        
    def getOCSstatusList2List(self, aliasList):
        """
        Takes a list of status aliases and returns a list of OCS status
        values in the same order.
        """

        statusDict = self.getOCSstatusList2Dict(aliasList)

        # Upack back into list
        res = []
        for key in aliasList:
            res.append(statusDict[key])

        return res

        
    #####################################
    # FITS TRANSFER FUNCTIONS
    #####################################
    
    def archive_framelist(self, framelist, timeout=None):
        """
        Archive a list of frames.  'framelist' should be a list of tuples,
        where each tuple is of the form (frameid, fitspath).  frameid is
        the Subaru frame id of the file (e.g. 'SUKA00047325' and fitspath is
        the path to the FITS file to be archived.
        """

        self.__check_interface()

        if timeout == None:
            timeout = self.params.timeout_filexfr
            
        try:
            res = self.ocsint.archive_framelist(framelist,
                                                timeout=timeout)
            # TODO: need to check multiple frame return codes
            self.__check_result(res)
            
        except OCSintError, e:
            raise CamInterfaceError(e)
        
        return res
        

    def archive_fits(self, framelist):
        self.logger.error("***DEPRECATED FUNCTION--PLEASE USE FUNCTION 'archive_framelist' INSTEAD ***")
        return self.archive_framelist(framelist)

        
    def archive_frame(self, frameid, fitspath, timeout=None):
        """
        Archive a single FITS frame.  frameid is the Subaru frame id that
        has already been allocated (either passed to the instrument in the
        command, or fetched using getFrame()) and fitspath is the path
        to the fits file.  The file does not need to have the same name
        as the frame id.
        """

        framelist = ((frameid, fitspath),)
        
        return self.archive_framelist(framelist, timeout=timeout)

        
    def archive(self, filepath, filetype='fits', timeout=None, frtype='A'):
        """
        Archive a single file, obtaining a frame id automatically for the
        purpose.  Currently only filetype=='fits' is supported.
        """

        self.__check_interface()

        if timeout == None:
            timeout = self.params.timeout_status
            
        if filetype.lower() != 'fits':
            raise CamError("Currently I can only archive FITS files!")
        
        # Get an 'A' frame
        frameid = self.getFrame(frtype)
        try:
            framelist = ((frameid, filepath),)
            res = self.ocsint.archive_framelist(framelist,
                                                timeout=timeout)
            self.__check_result(res)
            
        except OCSintError, e:
            raise CamInterfaceError(e)
        
        return res
        
    #####################################
    # FRAME ID FUNCTIONS
    #####################################
    
    def getFrame(self, frtype):
        """
        Obtain a single Subaru frame id.  'frtype' should be 'A' or 'Q'.
        """
        if self.frameint == None:
            errmsg = "No frame interface found!"
            #self.logger.error(errmsg)
            raise CamInterfaceError(errmsg)

        obcpnum = self.ocsint.obcpnum
        insname = self.insconfig.getNameByNumber(obcpnum)
        
        if not frtype in ('A', 'Q'):
            raise CamError("Frame type (%s) must be 'A' or 'Q'" % str(type))
        
        try:
            frameid = self.frameint.get_frame(insname, frtype, num=1)
            frameid = frameid.split(':')[0]

        except frameError, e:
            raise CamInterfaceError(e)

        return frameid
        
        
    def getFrames(self, num, frtype):
        """
        Obtain 'num' frame ids of type 'frtype'.  Returns a list of 'num'
        frames.  'frtype' should be 'A' or 'Q'.
        """
        if self.frameint == None:
            errmsg = "No frame interface found!"
            #self.logger.error(errmsg)
            raise CamInterfaceError(errmsg)

        obcpnum = self.ocsint.obcpnum
        insname = self.insconfig.getNameByNumber(obcpnum)
        
        if not frtype in ('A', 'Q'):
            raise CamError("Frame type (%s) must be 'A' or 'Q'" % str(type))
        
        if num < 1:
            raise CamError("Number of frames (%d) must be >= 1" % num)
        
        try:
            res = self.frameint.get_frame(insname, frtype, num=num)

            match = re.match(r'^(\w{3})(\w{1})(\d{1})(\d{7}):(\d{4})$', res)
            if not match:
                raise CamError("OCS frame number does not match expected format: '%s'" % (
                    res))

            (inscode, frame_type, frame_pfx, frame_cnt, numframes) = match.groups()
            if not (int(numframes) == num):
                raise CamError("OCS frame number does not match expected format: '%s'" % (
                        res))

            frame_cnt = int(frame_cnt)

            framelist = []
            for i in xrange(num):
                frameid = '%3.3s%1.1s%1.1s%07d' % (inscode, frame_type, frame_pfx, frame_cnt+i)
                framelist.append(frameid)

            return framelist

        except frameError, e:
            raise CamInterfaceError(e)
        
        
    #####################################
    # MISC FUNCTIONS
    #####################################
    
        
# END

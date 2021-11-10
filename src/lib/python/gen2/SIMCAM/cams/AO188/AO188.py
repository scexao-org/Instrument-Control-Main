#
# SIMCAM.py -- native SIMCAM personality for SIMCAM instrument simulator
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Sun Sep 14 18:53:30 HST 2008
#  Modified by Yosuke Minowa for AO188
#  Last edit: Feb 15 23:29 HST 2011  
#]
#
"""This file implements a simulator for a simulated instrument (SIMCAM).
"""
import sys, os, time
import re
import threading

import Bunch
import Task
import astro.fitsutils as fitsutils
from SIMCAM import BASECAM, CamError, CamCommandError
import SIMCAM.cams.common as common
import socket
import subprocess
from AO188_Misc import isfloat

import string
import re
import astro.radec as radec

# Value to return for executing unimplemented command.
# 0: OK, non-zero: error
unimplemented_res = 0


class AO188Error(CamCommandError):
    pass

class AO188(BASECAM):

    def __init__(self, logger, env, ev_quit=None):

        super(AO188, self).__init__()
        
        self.logger = logger
        self.env = env
        # Convoluted but sure way of getting this module's directory
        self.mydir = os.path.split(sys.modules[__name__].__file__)[0]

        if not ev_quit:
            self.ev_quit = threading.Event()
        else:
            self.ev_quit = ev_quit

        self.ocs = None
        self.mystatus1 = None
        self.mystatus2 = None
        self.mode = 'default'

        # Thread-safe bunch for storing parameters read/written
        # by threads executing in this object
        self.param = Bunch.threadSafeBunch()
        
        # Interval between status packets (secs)
        self.param.status_interval = 60


    #######################################
    # INITIALIZATION
    #######################################

    def initialize(self, ocsint):
        '''Initialize instrument.  
        '''
        super(AO188, self).initialize(ocsint)
        self.logger.info('***** INITIALIZE CALLED *****')
        # Grab my handle to the OCS interface.
        self.ocs = ocsint

        # Get instrument configuration info
        self.obcpnum = self.ocs.get_obcpnum()
        self.insconfig = self.ocs.get_INSconfig()

        # Thread pool for autonomous tasks
        self.threadPool = self.ocs.threadPool

        # For task inheritance:
        self.tag = 'simcam'
        self.shares = ['logger', 'ev_quit', 'threadPool']

        # dictionary for server host name and port number
        self.server = {'howfs':{'host':'10.0.0.3','port':18816},\
                       'lowfs':{'host':'10.0.0.3','port':18818},\
                       'calsci':{'host':'10.0.0.3','port':18815},\
                       'rtscom':{'host':'10.0.0.3','port':25010},\
                       'au':{'host':'10.0.0.3','port':18087},\
                       'envmon':{'host':'10.0.0.3','port':25011},\
                       'imrsrv':{'host':'10.0.0.6','port':25430}}
        
        # Used to format status buffer (item lengths must match definitions
        # of status aliases on SOSS side in $OSS_SYSTEM/StatusAlias.pro)

        ##### Status for slow update (statfmt1) #####
        # SIMCAM status 
        statfmt1 = "%(status)-8.8s,"
        # AO bench 
        statfmt1 = statfmt1 + "%(bench)-8.8s,"
        # ENTSHUT 
        statfmt1 = statfmt1 + "%(enshut)-12.12s,%(eshutp)9.5f,%(eshutm)8d,"
        # CALXZ 
        statfmt1 = statfmt1 + "%(calx)-12.12s,%(calxp)9.3f,%(calxm)8d,"
        statfmt1 = statfmt1 + "%(calz)-12.12s,%(calzp)9.3f,%(calzm)8d,"
        # CALLD 
        statfmt1 = statfmt1 + "%(calld1)-8.8s,%(calld1i)8.3f,%(calld1p)8.3f,"
        statfmt1 = statfmt1 + "%(calld2)-8.8s,%(calld2i)8.3f,%(calld2p)8.3f,"
        statfmt1 = statfmt1 + "%(calld3)-8.8s,%(calld3i)8.3f,%(calld3p)8.3f,"
        # CALM 
        statfmt1 = statfmt1 + "%(calmngsf)-12.12s,%(calmngsfp)9.5f,%(calmngsfm)8d,"
        statfmt1 = statfmt1 + "%(calmlgsf)-12.12s,%(calmlgsfp)9.5f,%(calmlgsfm)8d,"
        statfmt1 = statfmt1 + "%(calmtp1)-12.12s,%(calmtp1p)9.4f,%(calmtp1m)8d,"
        statfmt1 = statfmt1 + "%(calmtp1r)-12.12s,%(calmtp1rv)9.3f,%(calmtp1rp)9.3f,%(calmtp1rm)8d,"
        statfmt1 = statfmt1 + "%(calmtp2)-12.12s,%(calmtp2p)9.4f,%(calmtp2m)8d,"
        statfmt1 = statfmt1 + "%(calmtp2r)-12.12s,%(calmtp2rv)9.3f,%(calmtp2rp)9.3f,%(calmtp2rm)8d,"
        statfmt1 = statfmt1 + "%(calmm3tx)-12.12s,%(calmm3txp)9.4f,%(calmm3txm)8d,"
        statfmt1 = statfmt1 + "%(calmm3ty)-12.12s,%(calmm3typ)9.4f,%(calmm3tym)8d,"
        # BS1/2
        statfmt1 = statfmt1 + "%(bs1)-12.12s,%(bs1p)9.5f,%(bs1m)10d,"
        statfmt1 = statfmt1 + "%(bs2)-12.12s,%(bs2p)9.5f,%(bs2m)10d,"
        # F-conversion
        statfmt1 = statfmt1 + "%(fconv)-12.12s,%(fconvp)9.5f,"
        # HOWFS mechanism
        statfmt1 = statfmt1 + "%(hwnap)-12.12s,%(hwnapp)9.5f,%(hwnapm)10d,"
        statfmt1 = statfmt1 + "%(hwlap)-12.12s,%(hwlapp)9.5f,%(hwlapm)10d,"
        statfmt1 = statfmt1 + "%(hwadc)-12.12s,%(hwadcp)9.5f,%(hwadcm)10d,"
        statfmt1 = statfmt1 + "%(hwabs)-12.12s,%(hwabsp)9.5f,%(hwabsm)10d,"
        statfmt1 = statfmt1 + "%(hwaf1)-12.12s,%(hwaf1p)9.5f,%(hwaf1m)10d,"
        statfmt1 = statfmt1 + "%(hwaf2)-12.12s,%(hwaf2p)9.5f,%(hwaf2m)10d,"
        statfmt1 = statfmt1 + "%(hwhbs)-12.12s,%(hwhbsp)9.5f,%(hwhbsm)10d,"
        statfmt1 = statfmt1 + "%(hwpbs)-12.12s,%(hwpbsp)9.5f,%(hwpbsm)10d,"
        statfmt1 = statfmt1 + "%(hwlaz)-12.12s,%(hwlazp)9.5f,%(hwlazm)10d,"
        statfmt1 = statfmt1 + "%(hwlaf)-12.12s,%(hwlafp)9.5f,%(hwlafm)10d,"
        statfmt1 = statfmt1 + "%(hwlash)-8.8s,"
        # LOWFS mechanism
        statfmt1 = statfmt1 + "%(lwap1)-12.12s,%(lwap1p)9.5f,%(lwap1m)10d,"
        statfmt1 = statfmt1 + "%(lwadc)-12.12s,%(lwadcp)9.5f,%(lwadcm)10d,"
        statfmt1 = statfmt1 + "%(lwabs)-12.12s,%(lwabsp)9.5f,%(lwabsm)10d,"
        statfmt1 = statfmt1 + "%(lwaf1)-12.12s,%(lwaf1p)9.5f,%(lwaf1m)10d,"
        statfmt1 = statfmt1 + "%(lwaf2)-12.12s,%(lwaf2p)9.5f,%(lwaf2m)10d,"
        statfmt1 = statfmt1 + "%(lwap2)-12.12s,%(lwap2p)9.5f,%(lwap2m)10d,"
        statfmt1 = statfmt1 + "%(lwpbs)-12.12s,%(lwpbsp)9.5f,%(lwpbsm)10d,"
        statfmt1 = statfmt1 + "%(lwlaz)-12.12s,%(lwlazp)9.5f,%(lwlazm)10d,"
        statfmt1 = statfmt1 + "%(lwlaf)-12.12s,%(lwlafp)9.5f,%(lwlafm)10d,"
        statfmt1 = statfmt1 + "%(lwlash)-8.8s,"
        # VM aperture
        statfmt1 = statfmt1 + "%(vmirs)-12.12s,%(vmirsp)9.4f,%(vmirsm)10d,"
        # Environment
        statfmt1 = statfmt1 + "%(apdti)6.2f,%(apdto)6.2f,"
        statfmt1 = statfmt1 + "%(bncti)6.2f,%(bncto)6.2f,"
        statfmt1 = statfmt1 + "%(bnchi)6.2f,%(bncho)6.2f"

        ##### Status for fast update (statfmt2) #####

        # LOOP mode 
        statfmt2 = "%(loopmode)-8.8s,"
        # IMR 
        statfmt2 = statfmt2 + "%(imrstat)-12.12s,%(imrmod)-12.12s,%(imrang)9.3f,%(imrpad)9.3f,%(imrpap)9.3f,"
        statfmt2 = statfmt2 + "%(imrra)-16.16s,%(imrdec)-16.16s,"
        # Science path ADC
        statfmt2 = statfmt2 + "%(sadc)-12.12s,%(sadcp)9.5f,%(sadcm)10d,"
        statfmt2 = statfmt2 + "%(sadcstat)-12.12s,"
        statfmt2 = statfmt2 + "%(sadcmode)-12.12s,"
        statfmt2 = statfmt2 + "%(sadcfc)9.3f,"
        statfmt2 = statfmt2 + "%(sadcra)-16.16s,%(sadcdec)-16.16s,%(sadcpa)9.3f,"
        statfmt2 = statfmt2 + "%(sadca1)9.5f,%(sadca1m)10d,"
        statfmt2 = statfmt2 + "%(sadca2)9.5f,%(sadca2m)10d,"
        # AU1 
        statfmt2 = statfmt2 + "%(au1x)9.5f,%(au1y)9.5f,"
        statfmt2 = statfmt2 + "%(au1xa)9.5f,%(au1ya)9.5f,"
        statfmt2 = statfmt2 + "%(au1foc)9.5f,"
        statfmt2 = statfmt2 + "%(au1tx)9.5f,%(au1ty)9.5f,"
        statfmt2 = statfmt2 + "%(au1m1x)9.5f,%(au1m1y)9.5f,%(au1m1z)9.5f,"
        statfmt2 = statfmt2 + "%(au1m2x)9.5f,%(au1m2y)9.5f,"
        statfmt2 = statfmt2 + "%(au1gsx)9.3f,%(au1gsy)9.3f,"
        # AU2 
        statfmt2 = statfmt2 + "%(au2x)9.5f,%(au2y)9.5f,"
        statfmt2 = statfmt2 + "%(au2xa)9.5f,%(au2ya)9.5f,"
        statfmt2 = statfmt2 + "%(au2foc)9.5f,"
        statfmt2 = statfmt2 + "%(au2tx)9.5f,%(au2ty)9.5f,"
        statfmt2 = statfmt2 + "%(au2m1x)9.5f,%(au2m1y)9.5f,%(au2m1z)9.5f,"
        statfmt2 = statfmt2 + "%(au2m2x)9.5f,%(au2m2y)9.5f,"
        statfmt2 = statfmt2 + "%(au2gsx)9.3f,%(au2gsy)9.3f,"
        # VM 
        statfmt2 = statfmt2 + "%(vm)-8.8s,%(vmvolt)6.2f,%(vmfreq)6.1f,%(vmphas)6.1f,"
        # HOWFS-ADC tracking
        statfmt2 = statfmt2 + "%(hwadcstat)-12.12s,%(hwadcmode)-12.12s,"
        statfmt2 = statfmt2 + "%(hwadcfc)9.3f,"
        statfmt2 = statfmt2 + "%(hwadcra)-16.16s,%(hwadcdec)-16.16s,%(hwadcpa)9.3f,"
        statfmt2 = statfmt2 + "%(hwadca1)9.3f,%(hwadca1m)10d,"
        statfmt2 = statfmt2 + "%(hwadca2)9.3f,%(hwadca2m)10d,"
        # LOWFS-ADC tracking
        statfmt2 = statfmt2 + "%(lwadcstat)-12.12s,%(lwadcmode)-12.12s,"
        statfmt2 = statfmt2 + "%(lwadcfc)9.3f,"
        statfmt2 = statfmt2 + "%(lwadcra)-16.16s,%(lwadcdec)-16.16s,%(lwadcpa)9.3f,"
        statfmt2 = statfmt2 + "%(lwadca1)9.3f,%(lwadca1m)10d,"
        statfmt2 = statfmt2 + "%(lwadca2)9.3f,%(lwadca2m)10d,"
        # HOWFS-APD
        statfmt2 = statfmt2 + "%(hwapda)8.3f,"
        # LOWFS-APD
        statfmt2 = statfmt2 + "%(lwapda)8.3f,"
        # CNTMON 
        statfmt2 = statfmt2 + "%(loop)-8.8s,"
        statfmt2 = statfmt2 + "%(dmgain)7.3f,%(ttgain)7.3f,%(psubg)7.3f,"
        statfmt2 = statfmt2 + "%(wttgain)7.3f,"
        statfmt2 = statfmt2 + "%(lttgain)7.3f,%(ldfgain)7.3f,"
        statfmt2 = statfmt2 + "%(httgain)7.3f,%(hdfgain)7.3f,"
        statfmt2 = statfmt2 + "%(adfgain)7.3f,"
        statfmt2 = statfmt2 + "%(sttgain)7.3f,"
        statfmt2 = statfmt2 + "%(ttx)8.3f,%(tty)8.3f,"
        statfmt2 = statfmt2 + "%(wtt1)8.3f,%(wtt2)8.3f,"
        statfmt2 = statfmt2 + "%(ctt1)8.3f,%(ctt2)8.3f,"
        statfmt2 = statfmt2 + "%(dmcmtx)-16.16s,%(ttcmtx)-16.16s"

        # Get our 3 letter instrument code and full instrument name
        self.inscode = self.insconfig.getCodeByNumber(self.obcpnum)
        self.insname = self.insconfig.getNameByNumber(self.obcpnum)
        
        
        # table name
        tblName1 = 'AONS0001' # for slow status  
        tblName2 = 'AONS0002' # for fast status

        self.mystatus1 = self.ocs.addStatusTable(tblName1,
                                                ['status',
                                                 'bench',
                                                 'enshut','eshutp','eshutm',
                                                 'calx','calxp','calxm',
                                                 'calz','calzp','calzm',
                                                 'calld1','calld1i','calld1p',
                                                 'calld2','calld2i','calld2p',
                                                 'calld3','calld3i','calld3p',
                                                 'calmngsf','calmngsfp','calmngsfm',
                                                 'calmlgsf','calmlgsfp','calmlgsfm',
                                                 'calmtp1','calmtp1p','calmtp1m',
                                                 'calmtp1r','calmtp1rv','calmtp1rp','calmtp1rm',
                                                 'calmtp2','calmtp2p','calmtp2m',
                                                 'calmtp2r','calmtp2rv','calmtp2rp','calmtp2rm',
                                                 'calmm3tx','calmm3txp','calmm3txm',
                                                 'calmm3ty','calmm3typ','calmm3tym',
                                                 'bs1','bs1p','bs1m',
                                                 'bs2','bs2p','bs2m',
                                                 'fconv','fconvp',
                                                 'hwnap','hwnapp','hwnapm',
                                                 'hwlap','hwlapp','hwlapm',
                                                 'hwadc','hwadcp','hwadcm',
                                                 'hwabs','hwabsp','hwabsm',
                                                 'hwaf1','hwaf1p','hwaf1m',
                                                 'hwaf2','hwaf2p','hwaf2m',
                                                 'hwhbs','hwhbsp','hwhbsm',
                                                 'hwpbs','hwpbsp','hwpbsm',
                                                 'hwlaz','hwlazp','hwlazm',
                                                 'hwlaf','hwlafp','hwlafm',
                                                 'hwlash',
                                                 'lwap1','lwap1p','lwap1m',
                                                 'lwadc','lwadcp','lwadcm',
                                                 'lwabs','lwabsp','lwabsm',
                                                 'lwaf1','lwaf1p','lwaf1m',
                                                 'lwaf2','lwaf2p','lwaf2m',
                                                 'lwap2','lwap2p','lwap2m',
                                                 'lwpbs','lwpbsp','lwpbsm',
                                                 'lwlaz','lwlazp','lwlazm',
                                                 'lwlaf','lwlafp','lwlafm',
                                                 'lwlash',
                                                 'vmirs','vmirsp','vmirsm',
                                                 'apdti','apdto',
                                                 'bncti','bncto',
                                                 'bnchi','bncho'
                                                 ],
                                                formatStr=statfmt1)


        self.mystatus2 = self.ocs.addStatusTable(tblName2,
                                                ['loopmode',
                                                 'imrstat','imrmod','imrang','imrpad','imrpap',
                                                 'imrra','imrdec',
                                                 'sadc','sadcp','sadcm',
                                                 'sadcstat','sadcmode',
                                                 'sadcfc',
                                                 'sadcra','sadcdec','sadcpa',
                                                 'sadca1','sadca1m',
                                                 'sadca2','sadca2m',
                                                 'au1x','au1y',
                                                 'au1xa','au1ya',
                                                 'au1foc',
                                                 'au1tx','au1ty',
                                                 'au1m1x','au1m1y','au1m1z',
                                                 'au1m2x','au1m2y',
                                                 'au1gsx','au1gsy',
                                                 'au2x','au2y',
                                                 'au2xa','au2ya',
                                                 'au2foc',
                                                 'au2tx','au2ty',
                                                 'au2m1x','au2m1y','au2m1z',
                                                 'au2m2x','au2m2y',
                                                 'au2gsx','au2gsy',
                                                 'vm','vmvolt','vmfreq','vmphas',
                                                 'hwadcstat','hwadcmode',
                                                 'hwadcfc',
                                                 'hwadcra','hwadcdec','hwadcpa',
                                                 'hwadca1','hwadca1m',
                                                 'hwadca2','hwadca2m',
                                                 'lwadcstat','lwadcmode',
                                                 'lwadcfc',
                                                 'lwadcra','lwadcdec','lwadcpa',
                                                 'lwadca1','lwadca1m',
                                                 'lwadca2','lwadca2m',
                                                 'hwapda',
                                                 'lwapda',
                                                 'loop',
                                                 'dmgain','ttgain','psubg',
                                                 'wttgain',
                                                 'lttgain','ldfgain',
                                                 'httgain','hdfgain',
                                                 'adfgain',
                                                 'sttgain',
                                                 'ttx','tty',
                                                 'wtt1','wtt2',
                                                 'ctt1','ctt2',
                                                 'dmcmtx','ttcmtx'
                                                 ],
                                                formatStr=statfmt2)

        
        # special counter for getaobenchstat
        # status polling interval for getaobench is "self.aobench_poll_interval"
        # times higher than others
        self.aobench_poll_count = 0 
        self.aobench_poll_interval = 60
        
        # Establish initial status values
        self.mystatus1.setvals(status='ALIVE')
        self.getaobenchstat()
        self.getcalstat()
        self.getenshutstat()
        self.getimrstat()
        self.getsadcstat()
        self.getbsstat()
        self.getfconvstat()
        self.getcntmonstat(1)
        self.getau1stat()
        self.getau2stat()
        self.gethowfsstat()
        self.gethwadcstat()
        self.getvmstat()
        self.getlowfsstat()
        self.getlwadcstat()
        self.getenvstat()
        self.getloopmode() # this line should be placed after getau1stat()
        
        # Handles to periodic tasks
        self.status_task = None
        self.power_task = None

        # Lock for handling mutual exclusion
        self.lock = threading.RLock()


    def start(self, wait=True):
        super(AO188, self).start(wait=wait)
        
        self.logger.info('AO188 STARTED.')

        # Start auto-generation of status task
        t1 = common.IntervalTask(self.put_slow_status, 10.0)
        self.status_task = t1
        t1.init_and_start(self)

        t2 = common.IntervalTask(self.put_fast_status, 1.0)
        self.status_task = t2
        t2.init_and_start(self)

        # Start task to monitor summit power.  Call self.power_off
        # when we've been running on UPS power for 60 seconds
        t = common.PowerMonTask(self, self.power_off, upstime=60.0)
        self.power_task = t
        # power monitor is not implemented (YM)
        #t.init_and_start(self) 


    def stop(self, wait=True):
        super(AO188, self).stop(wait=wait)
        
        # Terminate status generation task
        if self.status_task != None:
            self.status_task.stop()

        self.status_task = None

        # Terminate power check task
        if self.power_task != None:
            self.power_task.stop()

        self.power_task = None

        self.logger.info("AO188 STOPPED.")


    ####################
    # INTERNAL METHODS #
    ####################

    ### Send command to ao188 servers ###
    def AO188SendCmd (self, server, cmd):

        # convert string to lower case
        server = server.lower()
        cmd = cmd.lower()

        # get server host and port
        if self.server.has_key(server):
            host = self.server[server]['host']
            port = self.server[server]['port']
        else:
            raise AO188Error("Error: unknown server name %s" % server)
        
        #Open socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(120)
        except socket.error, msg:
            sock.close()
            raise AO188Error(msg[1])
        
        try:
            sock.connect ((host, port))
        except socket.error, msg:
            sock.close()
            raise AO188Error(msg[1])
          
        # Send command to server
        sock.send(cmd)
            
        # Receive response from server
        retstr = ""
        while 1:
            data = sock.recv(1024)
            retstr = retstr + data
            if len(data) == 0 or data.find("\r") != -1:
                break
        
        # close socket
        sock.close()

        # send error message to SOSS if any
        if(retstr != "\0" and retstr != "\r"):
            raise AO188Error(retstr[:-2])

    ### Send command to ao188 servers and receive return string ###
    def AO188SendCmdRecv (self, server, cmd):

        # convert string to lower case
        server = server.lower()
        #cmd = cmd.lower()

        # get server host and port
        if self.server.has_key(server):
            host = self.server[server]['host']
            port = self.server[server]['port']
        else:
            self.logger.warn("Unknown server name : %s" % str(server))
            return "FALSE"
                           
                            
        #Open socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(120)
        except socket.error, msg:
            sock.close()
            self.logger.warn("Failed to define socket for command : %s" % (str(cmd)))
            return "FALSE"
        
        try:
            sock.connect ((host, port))
        except socket.error, msg:
            sock.close()
            self.logger.warn("Failed to connect server (%s) for command : %s" % (str(server),str(cmd)))
            return "FALSE"

        # Send command to server
        sock.send(cmd)
            
        # Receive response from server
        retstr = ""
        while 1:
            data = sock.recv(1024)
            retstr = retstr + data
            if len(data) == 0 or data.find("\r") != -1:
                break
        
        #close socket
        sock.close()

        # delete '\r' from received string
        retstr = retstr[:-1]
        
        # return received string
        return retstr


    ### Execute command in AO188 ###
    def AO188ExecCmd (self, cmd):

        # convert string to lower case
        cmd = cmd.lower()

        # execute command
        proc = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
        ret = proc.stdout.read()
        if ret != "" :
            raise AO188Error("Error: %s" % str(ret))
        
        
    ### Execute command in AO188 and receive return string ###
    def AO188ExecCmdRecv (self, cmd):

        # convert string to lower case
        if cmd.find("imr") < 0:
            cmd = cmd.lower()

        # execute command
        proc = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        err = proc.stderr.read()
        if err != "" :
            raise AO188Error("Error: %s" % str(err))

        ret = proc.stdout.read()
        
        return ret

    ####################################
    ###  Commands for getting status ###
    ####################################


    ### Get AO bench status ###
    def getaobenchstat(self):
        ### check AO bench status via TSCV.FOCUSINFO2 ###
        ### This funtion is not used until AO bench position
        ### mechanical sensor will available.

        #if self.aobench_poll_count == 0:
        #    # initialize status dictionary
        #    statusDict = {'TSCV.FOCUSINFO2': -1}
        #                
        #    # get telescope focus information
        #    focus = -1
        #    try:
        #        self.ocs.requestOCSstatus(statusDict)
        #        focus = int(statusDict['TSCV.FOCUSINFO2'])
        #    except Exception, e:
        #        focus = -1
        #    
        #    # initialize status
        #    bench = "UNKNOWN"
        #
        #    # assign bench status from telescope focus information
        #    if focus == 0:
        #        bench = "OUT"
        #    elif focus > 0:
        #        bench = "IN"
        #            
        #    # register status value
        #    self.mystatus1['bench'] = bench
        #
        #    # count up 
        #    self.aobench_poll_count += 1
        #        
        #else:
        #    # count up
        #    self.aobench_poll_count += 1
        #    if self.aobench_poll_count > self.aobench_poll_interval :
        #        self.aobench_poll_count = 0
        self.mystatus1['bench'] = "UNKNOWN"
        
    ### Get Loop mode (NGS/LGS) ###
    def getloopmode(self):

        # initialize status
        loopmode = "UNKNOWN"

        # if au1 focus is larger than 50mm,
        # loop mode should be "LGS".
        if float(self.mystatus2['au1foc']) > 50.0 :
            loopmode = "LGS"
        else :
            loopmode = "NGS" 
            
        # for LGSwoNGS mode, lowfs status are necessary
        
        # register status value
        self.mystatus2['loopmode'] = loopmode
                
    ### Get Entrance shutter status ###
    def getenshutstat(self):
        ### get entrance shutter status ###
        ret = self.AO188SendCmdRecv("calsci", "entshut st\r")

        # split status line into array
        r = re.compile('[\s:\[\]\(\)]+')
        param = r.split(ret)

        # initialize status values
        enshut = "UNKNOWN"
        eshutm = -99
        eshutp = -99.9

        # parse status array
        if len(param) > 4:
            enshut = param[1]
            if isfloat(param[2]):
                eshutp = float(param[2])
            if isfloat(param[4]):
                eshutm = int(param[4])

        # register status values 
        self.mystatus1['enshut'] = enshut
        self.mystatus1['eshutp'] = eshutp
        self.mystatus1['eshutm'] = eshutm

    ### Get calibration unit status ###
    def getcalstat(self):
        # get calxz stage status
        ret = self.AO188SendCmdRecv("calsci", "calxz st\r")

        # split status line into array
        r = re.compile('[\s:,\[\]\(\)\n]+')
        param = r.split(ret)

        # Initialize status 
        calx = calz = "UNKNOWN"
        calxp = calzp = -99.9
        calxm = calzm = -99

        # parse status array 
        for item in range(len(param)):
            if param[item] == "X-Axis":
                calx = param[item+1]
                if isfloat(param[item+2]):
                    calxp = float(param[item+2])
                if isfloat(param[item+4]):
                    calxm = int(param[item+4])
            elif param[item] == "Z-Axis":
                calz = param[item+1]
                if isfloat(param[item+2]):
                    calzp = float(param[item+2])
                if isfloat(param[item+4]):
                    calzm = int(param[item+4])
        
        # register status values 
        self.mystatus1['calx'] = calx
        self.mystatus1['calxp'] = calxp
        self.mystatus1['calxm'] = calxm
        self.mystatus1['calz'] = calz
        self.mystatus1['calzp'] = calzp
        self.mystatus1['calzm'] = calzm


        # get cal LD status 
        ret = self.AO188SendCmdRecv("calsci", "calld st\r")

        # split status line into array 
        r = re.compile('[\s:]+')
        param = r.split(ret)

        # initialize status values 
        calld1 = calld2 = calld3 = "UNKNOWN"
        calld1i = calld2i = calld3i = -99.9
        calld1p = calld2p = calld3p = -99.9

        # parse status array 
        for item in range(len(param)):
            if param[item] == "655" and param[item+1] == "nm":
                calld1 = param[item+3]
                if isfloat(param[item+5]):
                    calld1i = float(param[item+5])
                if isfloat(param[item+7]):
                    calld1p = float(param[item+7])
            elif param[item] == "1550" and param[item+1] == "nm":
                calld2 = param[item+3]
                if isfloat(param[item+5]):
                    calld2i = float(param[item+5])
                if isfloat(param[item+7]):
                    calld2p = float(param[item+7])
            elif param[item] == "589" and param[item+1] == "nm":
                calld3 = param[item+3]
                if isfloat(param[item+5]):
                    calld3i = float(param[item+5])
                if isfloat(param[item+7]):
                    calld3p = float(param[item+7])

        # register status values 
        self.mystatus1['calld1'] = calld1
        self.mystatus1['calld1i'] = calld1i
        self.mystatus1['calld1p'] = calld1p
        self.mystatus1['calld2'] = calld2
        self.mystatus1['calld2i'] = calld2i
        self.mystatus1['calld2p'] = calld2p
        self.mystatus1['calld3'] = calld3
        self.mystatus1['calld3i'] = calld3i
        self.mystatus1['calld3p'] = calld3p

        # get cal motor status
        ret = self.AO188SendCmdRecv("calsci", "calm st\r")

        # split status line into array 
        r = re.compile('[\s:,\[\]\(\)\n]+')
        param = r.split(ret)

        # Initialize status 
        calmngsf = calmlgsf = "UNKNOWN"
        calmngsfp = calmlgsfp = -99.9
        calmngsfm = calmlgsfm = -99
        calmtp1 = calmtp2 = "UNKNOWN"
        calmtp1p = calmtp2p = -99.9
        calmtp1m = calmtp2m = -99
        calmtp1r = calmtp2r = "UNKNOWN"
        calmtp1rp = calmtp2rp = -99.9
        calmtp1rm = calmtp2rm = -99
        calmtp1rv = calmtp2rv = -99.9
        calmm3tx = calmm3ty = "UNKNOWN"
        calmm3txp = calmm3typ = -99.9
        calmm3txm = calmm3tym = -99
        
        # parse status array 
        for item in range(len(param)):
            if param[item] == "NGS" and param[item+1] == "Focus":
                calmngsf = param[item+2]
                if isfloat(param[item+3]):
                    calmngsfp = float(param[item+3])
                if isfloat(param[item+5]):
                    calmngsfm = int(param[item+5])
            elif param[item] == "LGS" and param[item+1] == "Focus":
                calmlgsf = param[item+2]
                if isfloat(param[item+3]):
                    calmlgsfp = float(param[item+3])
                if isfloat(param[item+5]):
                    calmlgsfm = int(param[item+5])
            elif param[item] == "TP1" and param[item+1] == "In/Out":
                calmtp1 = param[item+2]
                if isfloat(param[item+3]):
                    calmtp1p = float(param[item+3])
                if isfloat(param[item+5]):
                    calmtp1m = int(param[item+5])
            elif param[item] == "TP1" and param[item+1] == "Rotation":
                calmtp1r = param[item+2]
                if isfloat(param[item+3]):
                    calmtp1rp = float(param[item+3])
                if isfloat(param[item+5]):
                    calmtp1rm = int(param[item+5])
                if calmtp1r == "Moving...":
                    if isfloat(param[item+7]):
                        calmtp1rv = float(param[item+7])
                else :
                    calmtp1rv = 0.0
            elif param[item] == "TP2" and param[item+1] == "In/Out":
                calmtp2 = param[item+2]
                if isfloat(param[item+3]):
                    calmtp2p = float(param[item+3])
                if isfloat(param[item+5]):
                    calmtp2m = int(param[item+5])
            elif param[item] == "TP2" and param[item+1] == "Rotation":
                calmtp2r = param[item+2]
                if isfloat(param[item+3]):
                    calmtp2rp = float(param[item+3])
                if isfloat(param[item+5]):
                    calmtp2rm = int(param[item+5])
                if calmtp2r == "Moving...":
                    if isfloat(param[item+7]):
                        calmtp2rv = float(param[item+7])
                else :
                    calmtp2rv = 0.0
            elif param[item] == "M3" and param[item+1] == "Tilt-X":
                calmm3tx = param[item+2]
                if isfloat(param[item+3]):
                    calmm3txp = float(param[item+3])
                if isfloat(param[item+5]):
                    calmm3txm = int(param[item+5])
            elif param[item] == "M3" and param[item+1] == "Tilt-Y":
                calmm3ty = param[item+2]
                if isfloat(param[item+3]):
                    calmm3typ = float(param[item+3])
                if isfloat(param[item+5]):
                    calmm3tym = int(param[item+5])

        # register status values 
        self.mystatus1['calmngsf'] = calmngsf
        self.mystatus1['calmngsfp'] = calmngsfp
        self.mystatus1['calmngsfm'] = calmngsfm
        self.mystatus1['calmlgsf'] = calmlgsf
        self.mystatus1['calmlgsfp'] = calmlgsfp
        self.mystatus1['calmlgsfm'] = calmlgsfm
        self.mystatus1['calmtp1'] = calmtp1
        self.mystatus1['calmtp1p'] = calmtp1p
        self.mystatus1['calmtp1m'] = calmtp1m
        self.mystatus1['calmtp1r'] = calmtp1r
        self.mystatus1['calmtp1rp'] = calmtp1rp  
        self.mystatus1['calmtp1rm'] = calmtp1rm
        self.mystatus1['calmtp1rv'] = calmtp1rv
        self.mystatus1['calmtp2'] = calmtp2
        self.mystatus1['calmtp2p'] = calmtp2p
        self.mystatus1['calmtp2m'] = calmtp2m
        self.mystatus1['calmtp2r'] = calmtp2r
        self.mystatus1['calmtp2rp'] = calmtp2rp  
        self.mystatus1['calmtp2rm'] = calmtp2rm
        self.mystatus1['calmtp2rv'] = calmtp2rv
        self.mystatus1['calmm3tx'] = calmm3tx
        self.mystatus1['calmm3txp'] = calmm3txp
        self.mystatus1['calmm3txm'] = calmm3txm
        self.mystatus1['calmm3ty'] = calmm3ty
        self.mystatus1['calmm3typ'] = calmm3typ
        self.mystatus1['calmm3tym'] = calmm3tym


    ### Get IMR status ###
    def getimrstat(self):

        # chnage shell script file.
        #imr_proc = subprocess.Popen(["/home/ao/golota/bin/sh_imrcli_stat_soss"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ret = self.AO188ExecCmdRecv("/home/ao/ao188/bin/imr_client IMR STAT SOSS")

        if ret == "" :
            raise AO188Error("Error: %s" % "IMR status is not available")

        r = re.compile('[\s:,\[\]]+')
        param = r.split(ret)

        imrstat = "UNKNOWN"
        imrmod = "UNKNOWN"
        imrpa  = -999.9
        imrpad = -999.9
        imrpap = -999.9
        imrang = -999.9
        imrra="UNKNOWN"
        imrdec="UNKNOWN"
        imrgeofile="UNKNOWN"

        for item in range(len(param)):
            #print "   Debug: getimrsrvstat: param[%s]= %s" % (item, param[item])
            if param[item] == "MODE":
                if param[item+1] == "SID":
                    imrmod = "SID"
                elif param[item+1] == "NON-SID":
                    imrmod = "NON-SID"
                elif param[item+1] == "ADI":
                    imrmod = "ADI"
                else:
                    imrmod = "NA"
            elif param[item] == "STAT":
                if param[item+1] == "STANDBY":
                    imrstat = "STAND-BY"
                elif param[item+1] == "TRACK":
                    imrstat = "TRACK"
                elif param[item+1] == "SLEW":
                    imrstat = "SLEW"
                elif param[item+1] == "GEN":
                    imrstat = "GEN"
                else:
                    imrstat = "STOP"
            elif param[item] == "PA":
                if isfloat(param[item+1]):
                    imrpa = float(param[item+1])
            elif param[item] == "PAD":
                if isfloat(param[item+1]):
                    imrpad = float(param[item+1])
            elif param[item] == "PAP":
                if isfloat(param[item+1]):
                    imrpap = float(param[item+1])
            elif param[item] == "ANG":
                if isfloat(param[item+1]):
                    imrang = float(param[item+1])
            elif param[item] == "RA2000":
                if param[item+1] != "DEC2000" and param[item+2] != "DEC2000" and param[item+3] != "DEC2000":
                    imrra = param[item+1] +':'+param[item+2]+':'+ param[item+3]
                else:
                    imrra = ""
            elif param[item] == "DEC2000":
                if param[item+1] != "RA" and param[item+2] != "RA" and param[item+3] != "RA":
                    imrdec = param[item+1] +':'+param[item+2]+':'+ param[item+3]
                else:
                    imrdec = ""
            
    
                    
        # register status values
        self.mystatus2['imrstat'] = imrstat
        self.mystatus2['imrmod'] = imrmod
        self.mystatus2['imrang'] = imrang
        self.mystatus2['imrpad'] = imrpad
        self.mystatus2['imrpap'] = imrpap
        self.mystatus2['imrra'] = imrra
        self.mystatus2['imrdec'] = imrdec

    ### get Science path ADC status (not implemented) ###
    def getsadcstat(self):
        
        ret = self.AO188ExecCmdRecv("/home/ao/ao188/bin/sadct st")

        if ret == "" :
            raise AO188Error("Error: %s" % "SciPath ADC status is not available")
  
        # split status line into array
        r = re.compile('[\s:,\[\]\(\)\n]+')
        param = r.split(ret)

        # Initialize status
        sadc = "UNKNOWN"
        sadcp = -99.9
        sadcm = -99
        sadcstat = sadcmode = "UNKNOWN"
        sadcra = sadcdec = "UNKNOWN"
        sadcpa = -999.9
        sadcfc = -99.9
        sadca1 = sadca2 = -999.9
        sadca1m = sadc2m = -999

        # parse status array
        for item in range(len(param)):
            if param[item] == "ADC" and param[item+1] == "Status":
                sadcstat = param[item+2]
            elif param[item] == "Mode": 
                sadcmode = param[item+1]
            elif param[item] == "FC": 
                if isfloat(param[item+1]):
                    sadcfc = float(param[item+1])
            elif param[item] == "RA":
                if isfloat(param[item+1]) and isfloat(param[item+2]) and isfloat(param[item+3]):
                    sadcra = param[item+1]+":"+param[item+2]+":"+param[item+3]
            elif param[item] == "Dec":
                if isfloat(param[item+1]) and isfloat(param[item+2]) and isfloat(param[item+3]):
                    sadcdec = param[item+1]+":"+param[item+2]+":"+param[item+3]
            elif param[item] == "PA":
                if isfloat(param[item+1]):
                    sadcpa = float(param[item+1])
            elif param[item] == "ADC" and param[item+1] == "In/Out":
                sadc = param[item+2]
                if isfloat(param[item+3]):
                    sadcp = float(param[item+3])
                if isfloat(param[item+5]):
                    sadcm = int(param[item+5])
            elif param[item] == "ADC" and param[item+1] == "P1" and param[item+2] == "Rotation":
                if isfloat(param[item+4]):
                    sadca1 = float(param[item+4])
                if isfloat(param[item+6]):
                    sadca1m = float(param[item+6])
            elif param[item] == "ADC" and param[item+1] == "P2" and param[item+2] == "Rotation":
                if isfloat(param[item+4]):
                    sadca2 = float(param[item+4])
                if isfloat(param[item+6]):
                    sadca2m = float(param[item+6])

        # register status values
        self.mystatus2['sadcstat'] = sadcstat
        self.mystatus2['sadcmode'] = sadcmode
        self.mystatus2['sadcfc'] = sadcfc
        self.mystatus2['sadcra'] = sadcra
        self.mystatus2['sadcdec'] = sadcdec
        self.mystatus2['sadcpa'] = sadcpa    
        self.mystatus2['sadc'] = sadc
        self.mystatus2['sadcp'] = sadcp
        self.mystatus2['sadcm'] = sadcm
        self.mystatus2['sadca1'] = sadca1
        self.mystatus2['sadca1m'] = sadca1m
        self.mystatus2['sadca2'] = sadca2
        self.mystatus2['sadca2m'] = sadca2m

    ### get BS status ###
    def getbsstat(self):

        # BS1 status 
        ret = self.AO188SendCmdRecv("calsci", "bs1 st\r")

        # split status line into array
        r = re.compile('[\s:\[\]\(\)]+')
        param = r.split(ret)

        # initialize status values
        bs1 = "UNKNOWN"
        bs1m = -99
        bs1p = -99.9

        # parse status array
        if len(param) > 4:
            bs1 = param[1]
            if isfloat(param[2]):
                bs1p = float(param[2])
            if isfloat(param[4]):
                bs1m = int(param[4])

        # register status values
        self.mystatus1['bs1'] = bs1
        self.mystatus1['bs1p'] = bs1p
        self.mystatus1['bs1m'] = bs1m
        
        # BS2 status
        ret = self.AO188SendCmdRecv("calsci", "bs2 st\r")

        # split status line into array
        r = re.compile('[\s:\[\]\(\)]+')
        param = r.split(ret)

        # initialize status values
        bs2 = "UNKNOWN"
        bs2m = -99
        bs2p = -99.9

        # parse status array
        if len(param) > 4:
            bs2 = param[1]
            if isfloat(param[2]):
                bs2p = float(param[2])
            if isfloat(param[4]):
                bs2m = int(param[4])

        # register status values
        self.mystatus1['bs2'] = bs2
        self.mystatus1['bs2p'] = bs2p
        self.mystatus1['bs2m'] = bs2m

    ### get f-conversion optics status ###
    def getfconvstat(self):
        ret = self.AO188SendCmdRecv("au", "fconv st\r")

        # split status line into array
        r = re.compile('[\s:,\[\]]+')
        param = r.split(ret)
        
        fconv = "UNKNOWN"
        fconvp = -99.9
        
        for item in range(len(param)):
            if param[item] == "Optics":
                fconv = param[item+1]
                if isfloat(param[item+2]):
                    fconvp = float(param[item+2])
                    
        self.mystatus1['fconv'] = fconv
        self.mystatus1['fconvp'] = fconvp

    ### get Count monitor status ###
    def getcntmonstat(self, cached):
        # get CNTMON status (update) 
        # cached = 0 : update status
        # cached = 1 : cache status
        if cached == 0:
            ret = self.AO188SendCmdRecv("rtscom", "cntmon stu\r")
        else :
            ret = self.AO188SendCmdRecv("rtscom", "cntmon st\r")

        # split status line into array
        r = re.compile('[\s,=\(\)\n]+')
        param = r.split(ret)

        # Initialize status
        dmgain = -99.9 
        ttgain = psubg = -9.9
        wttgain = lttgain = ldfgain = httgain = hdfgain = adfgain = sttgain = -99.9
        hwapda = lwapda = -99.9
        dmcmtx = ttcmtx = "UNKNOWN"
        ttx = tty = -99.9
        wtt1 = wtt2 = -99.9
        ctt1 = ctt2 = -99.9
        loop = "UNKNOWN"

        # parse status array
        stat_line = ""
        for item in range(len(param)):
             # Change status line
            if param[item] == "LOOP" and param[item+1] == ":":
                stat_line = "loop"
            elif param[item] == "GAIN" and param[item+1] == ":":
                stat_line = "gain"
            elif param[item] == "VM" and param[item+1] == ":":
                stat_line = "vm"
            elif param[item] == "TT" and param[item+1] == ":":
                stat_line = "tt"
            elif param[item] == "APD" and param[item+1] == ":":
                stat_line = "apd"
            elif param[item] == "FILE" and param[item+1] == ":":
                stat_line = "file"
            else :
                # Loop status
                if stat_line == "loop":
                    if param[item] == "State":
                        loop = param[item+1]
                        
                # Gain status 
                if stat_line == "gain":
                    if param[item] == "DMG":
                        if isfloat(param[item+1]):
                            dmgain = float(param[item+1])
                    elif param[item] == "TTG":
                        if isfloat(param[item+1]):
                            ttgain = float(param[item+1])
                    elif param[item] == "PSUB":
                        if isfloat(param[item+1]):
                            psubg = float(param[item+1])
                    elif param[item] == "STT":
                        if isfloat(param[item+1]):
                            sttgain = float(param[item+1])
                    elif param[item] == "LTT":
                        if isfloat(param[item+1]):
                            lttgain = float(param[item+1])
                    elif param[item] == "LDF":
                        if isfloat(param[item+1]):
                            ldfgain = float(param[item+1])
                    elif param[item] == "WTT":
                        if isfloat(param[item+1]):
                            wttgain = float(param[item+1])
                    elif param[item] == "ADF":
                        if isfloat(param[item+1]):
                            adfgain = float(param[item+1])
                    
                # TT status
                if stat_line == "tt":
                    if param[item] == "TT_tip":
                        if isfloat(param[item+1]):
                            ttx = float(param[item+1])
                    elif param[item] == "TT_tilt":
                        if isfloat(param[item+1]):
                            tty = float(param[item+1])
                    elif param[item] == "WTT_CH1":
                        if isfloat(param[item+1]):
                            wtt1 = float(param[item+1])
                    elif param[item] == "WTT_CH2":
                        if isfloat(param[item+1]):
                            wtt2 = float(param[item+1])
                    elif param[item] == "CTT_CH1":
                        if isfloat(param[item+1]):
                            ctt1 = float(param[item+1])
                    elif param[item] == "CTT_CH2":
                        if isfloat(param[item+1]):
                            ctt2 = float(param[item+1])
                            
                # APD status
                if stat_line == "apd":
                    if param[item] == "HOWFS-Ave.":
                        if isfloat(param[item+1]):
                            hwapda = float(param[item+1])
                        elif param[item+1] == "nan":
                            hwapda = 0.0
                    elif param[item] == "LOWFS-Ave.":
                        if isfloat(param[item+1]):
                            lwapda = float(param[item+1])
                        elif param[item+1] == "nan":
                            lwapda = 0.0
                        
                # FILE status
                if stat_line == "file":
                    if param[item] == "DMCMTX":
                        dmcmtx_param = param[item+1].split('/')
                        if len(dmcmtx_param) > 0:
                            dmcmtx = dmcmtx_param[len(dmcmtx_param)-1]
                        else:
                            dmcmtx = dmcmtx_param[0]
                        
                    elif param[item] == "TTCMTX":
                        ttcmtx_param = param[item+1].split('/')
                        if len(ttcmtx_param) > 0:
                            ttcmtx = ttcmtx_param[len(ttcmtx_param)-1]
                        else:
                            ttcmtx = ttcmtx_param[0]

        # register status values
        self.mystatus2['loop'] = loop
        self.mystatus2['dmgain'] = dmgain
        self.mystatus2['ttgain'] = ttgain
        self.mystatus2['psubg'] = psubg
        self.mystatus2['wttgain'] = wttgain
        self.mystatus2['lttgain'] = lttgain
        self.mystatus2['ldfgain'] = ldfgain
        self.mystatus2['httgain'] = httgain
        self.mystatus2['hdfgain'] = hdfgain
        self.mystatus2['adfgain'] = adfgain
        self.mystatus2['sttgain'] = sttgain
        self.mystatus2['ttx'] = ttx
        self.mystatus2['tty'] = tty
        self.mystatus2['wtt1'] = wtt1
        self.mystatus2['wtt2'] = wtt2
        self.mystatus2['ctt1'] = ctt1
        self.mystatus2['ctt2'] = ctt2
        self.mystatus2['hwapda'] = hwapda        
        self.mystatus2['lwapda'] = lwapda        
        self.mystatus2['dmcmtx'] = dmcmtx
        self.mystatus2['ttcmtx'] = ttcmtx
 
    ### Get AU1 status ###
    def getau1stat(self):
        ### get AU1 status ###
        ret = self.AO188SendCmdRecv("au", "au1 st\r")

        # split status line into array
        r = re.compile('[\s=:\(\)\n\[\],]+')
        param = r.split(ret)

        # Initialize status
        au1x = au1y = au1xa = au1ya = au1foc = au1tx = au1ty = -99.9
        au1m1x = au1m1y = au1m1z = au1m2x = au1m2y = -99.9
        au1gsx = au1gsy = 0.0

        # parse status array
        for item in range(len(param)):
            if param[item] == "Offset":
                if param[item+1] == "X":
                    if isfloat(param[item+2]):
                        au1x = float(param[item+2])
                    if isfloat(param[item+4]):
                        au1xa = float(param[item+4])
                elif param[item+1] == "Y":
                    if isfloat(param[item+2]):
                        au1y = float(param[item+2])
                    if isfloat(param[item+4]):    
                        au1ya = float(param[item+4])
            elif param[item] == "Focus":
                if isfloat(param[item+1]):
                    au1foc = float(param[item+1])
            elif param[item] == "Axis" and param[item+1] == "Tilt":
                if param[item+2] == "X":
                    if isfloat(param[item+3]):
                        au1tx = float(param[item+3])
                elif param[item+2] == "Y":
                    if isfloat(param[item+3]):
                        au1ty = float(param[item+3])
            elif param[item] == "M1":
                if param[item+1] == "Z":
                    if isfloat(param[item+2]):
                        au1m1z = float(param[item+2])
                elif param[item+1] == "TX":
                    if isfloat(param[item+2]):
                        au1m1x = float(param[item+2])
                elif param[item+1] == "TY":
                    if isfloat(param[item+2]):
                        au1m1y = float(param[item+2])
            elif param[item] == "M2":
                if param[item+1] == "TX":
                    if isfloat(param[item+2]):
                        au1m2x = float(param[item+2])
                elif param[item+1] == "TY":
                    if isfloat(param[item+2]):
                        au1m2y = float(param[item+2])
            elif param[item] == "GS":
                if param[item+1] == "coords":
                    if isfloat(param[item+2]):
                        au1gsx = float(param[item+2])
                    if isfloat(param[item+3]):
                        au1gsy = float(param[item+3])

        # register status values
        self.mystatus2['au1x'] = au1x
        self.mystatus2['au1xa'] = au1xa
        self.mystatus2['au1y'] = au1y
        self.mystatus2['au1ya'] = au1ya
        self.mystatus2['au1foc'] = au1foc
        self.mystatus2['au1tx'] = au1tx
        self.mystatus2['au1ty'] = au1ty
        self.mystatus2['au1m1x'] = au1m1x
        self.mystatus2['au1m1y'] = au1m1y
        self.mystatus2['au1m1z'] = au1m1z
        self.mystatus2['au1m2x'] = au1m2x
        self.mystatus2['au1m2y'] = au1m2y
        self.mystatus2['au1gsx'] = au1gsx
        self.mystatus2['au1gsy'] = au1gsy


    ### Get AU1 status ###
    def getau2stat(self):
        ### get AU1 status ###
        ret = self.AO188SendCmdRecv("au", "au2 st\r")

        # split status line into array
        r = re.compile('[\s=:\(\)\n\[\],]+')
        param = r.split(ret)

        # Initialize status
        au2x = au2y = au2xa = au2ya = au2foc = au2tx = au2ty = -99.9
        au2m1x = au2m1y = au2m1z = au2m2x = au2m2y = -99.9
        au2gsx = au2gsy = 0.0

        # parse status array
        for item in range(len(param)):
            if param[item] == "Offset":
                if param[item+1] == "X":
                    if isfloat(param[item+2]):
                        au2x = float(param[item+2])
                    if isfloat(param[item+4]):
                        au2xa = float(param[item+4])
                elif param[item+1] == "Y":
                    if isfloat(param[item+2]):
                        au2y = float(param[item+2])
                    if isfloat(param[item+4]):    
                        au2ya = float(param[item+4])
            elif param[item] == "Focus":
                if isfloat(param[item+1]):
                    au2foc = float(param[item+1])
            elif param[item] == "Axis" and param[item+1] == "Tilt":
                if param[item+2] == "X":
                    if isfloat(param[item+3]):
                        au2tx = float(param[item+3])
                elif param[item+2] == "Y":
                    if isfloat(param[item+3]):
                        au2ty = float(param[item+3])
            elif param[item] == "M1":
                if param[item+1] == "Z":
                    if isfloat(param[item+2]):
                        au2m1z = float(param[item+2])
                elif param[item+1] == "TX":
                    if isfloat(param[item+2]):
                        au2m1x = float(param[item+2])
                elif param[item+1] == "TY":
                    if isfloat(param[item+2]):
                        au2m1y = float(param[item+2])
            elif param[item] == "M2":
                if param[item+1] == "TX":
                    if isfloat(param[item+2]):
                        au2m2x = float(param[item+2])
                elif param[item+1] == "TY":
                    if isfloat(param[item+2]):
                        au2m2y = float(param[item+2])
            elif param[item] == "GS":
                if param[item+1] == "coords":
                    if isfloat(param[item+2]):
                        au2gsx = float(param[item+2])
                    if isfloat(param[item+3]):
                        au2gsy = float(param[item+3])

        # register status values
        self.mystatus2['au2x'] = au2x
        self.mystatus2['au2xa'] = au2xa
        self.mystatus2['au2y'] = au2y
        self.mystatus2['au2ya'] = au2ya
        self.mystatus2['au2foc'] = au2foc
        self.mystatus2['au2tx'] = au2tx
        self.mystatus2['au2ty'] = au2ty
        self.mystatus2['au2m1x'] = au2m1x
        self.mystatus2['au2m1y'] = au2m1y
        self.mystatus2['au2m1z'] = au2m1z
        self.mystatus2['au2m2x'] = au2m2x
        self.mystatus2['au2m2y'] = au2m2y
        self.mystatus2['au2gsx'] = au2gsx
        self.mystatus2['au2gsy'] = au2gsy

    
    ### Get HOWFS status ###
    def gethowfsstat(self):
        
        ret = self.AO188SendCmdRecv("howfs", "howfs st\r")

        # split status line into array
        r = re.compile('[\s:,\[\]\(\)\n]+')
        param = r.split(ret)

        # Initialize status
        hwnap = hwlap = "UNKNOWN"
        hwnapp = hwlapp = -99.9
        hwnapm = hwlapm = -99
        hwadc = "UNKNOWN"
        hwadcp = -99.9
        hwadcm = 99
        hwabs = hwhbs = hwpbs = "UNKNOWN"
        hwabsp = hwhbsp = hwpbsp = -99.9
        hwabsm = hwhbsm = hwpbsm = -99
        hwaf1 = hwaf2 = "UNKNOWN"
        hwaf1p = hwaf2p = -99.9
        hwaf1m = hwaf2m = -99
        hwlaz = hwlaf = "UNKNOWN"
        hwlazp = hwlafp = -99.9
        hwlazm = hwlafm = -99
        hwlash = "UNKNOWN"
        vmirs = "UNKNOWN"
        vmirsp = -99.9
        vmirsm = -99

        # parse status array
        for item in range(len(param)):
            if param[item] == "NGS" and param[item+1] == "Aperture":
                hwnap = param[item+2]
                if isfloat(param[item+3]):
                    hwnapp = float(param[item+3])
                if isfloat(param[item+5]):
                    hwnapm = int(param[item+5])
            elif param[item] == "LGS" and param[item+1] == "Aperture":
                hwlap = param[item+2]
                if isfloat(param[item+3]):
                    hwlapp = float(param[item+3])
                if isfloat(param[item+5]):
                    hwlapm = int(param[item+5])
            elif param[item] == "ADC" and param[item+1] == "In/Out":
                hwadc = param[item+2]
                if isfloat(param[item+3]):
                    hwadcp = float(param[item+3])
                if isfloat(param[item+5]):
                    hwadcm = int(param[item+5])
            elif param[item] == "Acq." and param[item+1] == "Camera" and param[item+2] == "BS":
                hwabs = param[item+3]
                if isfloat(param[item+4]):
                    hwabsp = float(param[item+4])
                if isfloat(param[item+6]):
                    hwabsm = int(param[item+6])
            elif param[item] == "Hires" and param[item+1] == "Camera" and param[item+2] == "BS":
                hwhbs = param[item+3]
                if isfloat(param[item+4]):
                    hwhbsp = float(param[item+4])
                if isfloat(param[item+6]):
                    hwhbsm = int(param[item+6])
            elif param[item] == "Pupil" and param[item+1] == "Camera" and param[item+2] == "BS":
                hwpbs = param[item+3]
                if isfloat(param[item+4]):
                    hwpbsp = float(param[item+4])
                if isfloat(param[item+6]):
                    hwpbsm = int(param[item+6])
            elif param[item] == "Acq." and param[item+1] == "Camera" and param[item+2] == "FW1":
                hwaf1 = param[item+3]
                if isfloat(param[item+4]):
                    hwaf1p = float(param[item+4])
                if isfloat(param[item+6]):
                    hwaf1m = int(param[item+6])
            elif param[item] == "Acq." and param[item+1] == "Camera" and param[item+2] == "FW2":
                hwaf2 = param[item+3]
                if isfloat(param[item+4]):
                    hwaf2p = float(param[item+4])
                if isfloat(param[item+6]):
                    hwaf2m = int(param[item+6])
            elif param[item] == "LA" and param[item+1] == "Stage":
                hwlaz = param[item+2]
                if isfloat(param[item+3]):
                    hwlazp = float(param[item+3])
                if isfloat(param[item+5]):
                    hwlazm = int(param[item+5])
            elif param[item] == "LA" and param[item+1] == "FW":
                hwlaf = param[item+2]
                if isfloat(param[item+3]):
                    hwlafp = float(param[item+3])
                if isfloat(param[item+5]):
                    hwlafm = int(param[item+5])
            elif param[item] == "LA" and param[item+1] == "Shutter":
                hwlash = param[item+2]
            elif param[item] == "VM" and param[item+1] == "Iris":
                vmirs = param[item+2]
                if isfloat(param[item+3]):
                    vmirsp = float(param[item+3])
                if isfloat(param[item+5]):
                    vmirsm = int(param[item+5])

        # register status values
        self.mystatus1['hwnap'] = hwnap
        self.mystatus1['hwnapp'] = hwnapp
        self.mystatus1['hwnapm'] = hwnapm
        self.mystatus1['hwlap'] = hwlap
        self.mystatus1['hwlapp'] = hwlapp
        self.mystatus1['hwlapm'] = hwlapm
        self.mystatus1['hwadc'] = hwadc
        self.mystatus1['hwadcp'] = hwadcp
        self.mystatus1['hwadcm'] = hwadcm
        self.mystatus1['hwabs'] = hwabs
        self.mystatus1['hwabsp'] = hwabsp
        self.mystatus1['hwabsm'] = hwabsm
        self.mystatus1['hwaf1'] = hwaf1
        self.mystatus1['hwaf1p'] = hwaf1p
        self.mystatus1['hwaf1m'] = hwaf1m
        self.mystatus1['hwaf2'] = hwaf2
        self.mystatus1['hwaf2p'] = hwaf2p
        self.mystatus1['hwaf2m'] = hwaf2m
        self.mystatus1['hwpbs'] = hwpbs
        self.mystatus1['hwpbsp'] = hwpbsp
        self.mystatus1['hwpbsm'] = hwpbsm
        self.mystatus1['hwhbs'] = hwhbs
        self.mystatus1['hwhbsp'] = hwhbsp
        self.mystatus1['hwhbsm'] = hwhbsm
        self.mystatus1['hwlaz'] = hwlaz
        self.mystatus1['hwlazp'] = hwlazp
        self.mystatus1['hwlazm'] = hwlazm
        self.mystatus1['hwlaf'] = hwlaf
        self.mystatus1['hwlafp'] = hwlafp
        self.mystatus1['hwlafm'] = hwlafm
        self.mystatus1['hwlash'] = hwlash
        self.mystatus1['vmirs'] = vmirs
        self.mystatus1['vmirsp'] = vmirsp
        self.mystatus1['vmirsm'] = vmirsm

    ### Get HOWFS ADC status ###
    def gethwadcstat(self):
        
        ret = self.AO188ExecCmdRecv("/home/ao/ao188/bin/howfs_adc st")

        if ret == "" :
            raise AO188Error("Error: %s" % "HOWFS ADC status is not available")
  
        # split status line into array
        r = re.compile('[\s:,\[\]\(\)\n]+')
        param = r.split(ret)

        # Initialize status
        hwadcstat = hwadcmode = "UNKNOWN"
        hwadcra = hwadcdec = "UNKNOWN"
        hwadcpa = -999.9
        hwadcfc = -99.9
        hwadca1 = hwadca2 = -999.9
        hwadca1m = hwadc2m = -999

        # parse status array
        for item in range(len(param)):
            if param[item] == "ADC" and param[item+1] == "Status":
                hwadcstat = param[item+2]
            elif param[item] == "Mode": 
                hwadcmode = param[item+1]
            elif param[item] == "FC": 
                if isfloat(param[item+1]):
                    hwadcfc = float(param[item+1])
            elif param[item] == "RA":
                if isfloat(param[item+1]) and isfloat(param[item+2]) and isfloat(param[item+3]):
                    hwadcra = param[item+1]+":"+param[item+2]+":"+param[item+3]
            elif param[item] == "Dec":
                if isfloat(param[item+1]) and isfloat(param[item+2]) and isfloat(param[item+3]):
                    hwadcdec = param[item+1]+":"+param[item+2]+":"+param[item+3]
            elif param[item] == "PA":
                if isfloat(param[item+1]):
                    hwadcpa = float(param[item+1])
            elif param[item] == "ADC" and param[item+1] == "P1" and param[item+2] == "Rotation":
                if isfloat(param[item+4]):
                    hwadca1 = float(param[item+4])
                if isfloat(param[item+6]):
                    hwadca1m = float(param[item+6])
            elif param[item] == "ADC" and param[item+1] == "P2" and param[item+2] == "Rotation":
                if isfloat(param[item+4]):
                    hwadca2 = float(param[item+4])
                if isfloat(param[item+6]):
                    hwadca2m = float(param[item+6])

        # register status values
        self.mystatus2['hwadcstat'] = hwadcstat
        self.mystatus2['hwadcmode'] = hwadcmode
        self.mystatus2['hwadcfc'] = hwadcfc
        self.mystatus2['hwadcra'] = hwadcra
        self.mystatus2['hwadcdec'] = hwadcdec
        self.mystatus2['hwadcpa'] = hwadcpa
        self.mystatus2['hwadca1'] = hwadca1
        self.mystatus2['hwadca1m'] = hwadca1m
        self.mystatus2['hwadca2'] = hwadca2
        self.mystatus2['hwadca2m'] = hwadca2m

    ### get VM status ###
    def getvmstat(self):

        ret = self.AO188SendCmdRecv("howfs", "vm st\r")

        # split status line into array
        r = re.compile('[\s:,]+')
        param = r.split(ret)

        # initialize status values
        vm = "UNKNOWN"
        vmfreq = -99.9
        vmvolt = -99.9
        vmphas = -99.9

        # parse status array
        for item in range(len(param)):
            if param[item] == "Drive":
                vm = param[item+1]
            elif param[item] == "Freq":
                if isfloat(param[item+1]):
                    vmfreq = float(param[item+1])
            elif param[item] == "Volt":
                if isfloat(param[item+1]):
                    vmvolt = float(param[item+1])
            elif param[item] == "Phase":
                if isfloat(param[item+1]):
                    vmphas = float(param[item+1])

        # register status values
        self.mystatus2['vm'] = vm
        self.mystatus2['vmfreq'] = vmfreq
        self.mystatus2['vmvolt'] = vmvolt
        self.mystatus2['vmphas'] = vmphas

    ### Get LOWFS status ###
    def getlowfsstat(self):
        
        ret = self.AO188SendCmdRecv("lowfs", "lowfs st\r")

        # split status line into array
        r = re.compile('[\s:,\[\]\(\)\n]+')
        param = r.split(ret)

        # Initialize status
        lwap1 = lwap2 = "UNKNOWN"
        lwap1p = lwap2p = -99.9
        lwap1m = lwap2m = -99
        lwadc = "UNKNOWN"
        lwadcp = -99.9
        lwadcm = 99
        lwabs = lwpbs = "UNKNOWN"
        lwabsp = lwpbsp = -99.9
        lwabsm = lwpbsm = -99
        lwaf1 = lwaf2 = "UNKNOWN"
        lwaf1p = lwaf2p = -99.9
        lwaf1m = lwaf2m = -99
        lwlaz = lwlaf = "UNKNOWN"
        lwlazp = lwlafp = -99.9
        lwlazm = lwlafm = -99
        lwlash = "UNKNOWN"
 
        # parse status array
        for item in range(len(param)):
            if param[item] == "Aperture" and param[item+1] == "1":
                lwap1 = param[item+2]
                if isfloat(param[item+3]):
                    lwap1p = float(param[item+3])
                if isfloat(param[item+5]):
                    lwap1m = int(param[item+5])
            elif param[item] == "Aperture" and param[item+1] == "2":
                lwap2 = param[item+2]
                if isfloat(param[item+3]):
                    lwap2p = float(param[item+3])
                if isfloat(param[item+5]):
                    lwap2m = int(param[item+5])
            elif param[item] == "ADC" and param[item+1] == "In/Out":
                lwadc = param[item+2]
                if isfloat(param[item+3]):
                    lwadcp = float(param[item+3])
                if isfloat(param[item+5]):
                    lwadcm = int(param[item+5])
            elif param[item] == "Acq." and param[item+1] == "Camera" and param[item+2] == "BS":
                lwabs = param[item+3]
                if isfloat(param[item+4]):
                    lwabsp = float(param[item+4])
                if isfloat(param[item+6]):
                    lwabsm = int(param[item+6])
            elif param[item] == "Pupil" and param[item+1] == "Camera" and param[item+2] == "BS":
                lwpbs = param[item+3]
                if isfloat(param[item+4]):
                    lwpbsp = float(param[item+4])
                if isfloat(param[item+6]):
                    lwpbsm = int(param[item+6])
            elif param[item] == "Acq." and param[item+1] == "Camera" and param[item+2] == "FW1":
                lwaf1 = param[item+3]
                if isfloat(param[item+4]):
                    lwaf1p = float(param[item+4])
                if isfloat(param[item+6]):
                    lwaf1m = int(param[item+6])
            elif param[item] == "Acq." and param[item+1] == "Camera" and param[item+2] == "FW2":
                lwaf2 = param[item+3]
                if isfloat(param[item+4]):
                    lwaf2p = float(param[item+4])
                if isfloat(param[item+6]):
                    lwaf2m = int(param[item+6])
            elif param[item] == "LA" and param[item+1] == "Stage":
                lwlaz = param[item+2]
                if isfloat(param[item+3]):
                    lwlazp = float(param[item+3])
                if isfloat(param[item+5]):
                    lwlazm = int(param[item+5])
            elif param[item] == "LA" and param[item+1] == "FW":
                lwlaf = param[item+2]
                if isfloat(param[item+3]):
                    lwlafp = float(param[item+3])
                if isfloat(param[item+5]):
                    lwlafm = int(param[item+5])
            elif param[item] == "LA" and param[item+1] == "Shutter":
                lwlash = param[item+2]

        # register status values
        self.mystatus1['lwap1'] = lwap1
        self.mystatus1['lwap1p'] = lwap1p
        self.mystatus1['lwap1m'] = lwap1m
        self.mystatus1['lwap2'] = lwap2
        self.mystatus1['lwap2p'] = lwap2p
        self.mystatus1['lwap2m'] = lwap2m
        self.mystatus1['lwadc'] = lwadc
        self.mystatus1['lwadcp'] = lwadcp
        self.mystatus1['lwadcm'] = lwadcm
        self.mystatus1['lwabs'] = lwabs
        self.mystatus1['lwabsp'] = lwabsp
        self.mystatus1['lwabsm'] = lwabsm
        self.mystatus1['lwaf1'] = lwaf1
        self.mystatus1['lwaf1p'] = lwaf1p
        self.mystatus1['lwaf1m'] = lwaf1m
        self.mystatus1['lwaf2'] = lwaf2
        self.mystatus1['lwaf2p'] = lwaf2p
        self.mystatus1['lwaf2m'] = lwaf2m
        self.mystatus1['lwpbs'] = lwpbs
        self.mystatus1['lwpbsp'] = lwpbsp
        self.mystatus1['lwpbsm'] = lwpbsm
        self.mystatus1['lwlaz'] = lwlaz
        self.mystatus1['lwlazp'] = lwlazp
        self.mystatus1['lwlazm'] = lwlazm
        self.mystatus1['lwlaf'] = lwlaf
        self.mystatus1['lwlafp'] = lwlafp
        self.mystatus1['lwlafm'] = lwlafm
        self.mystatus1['lwlash'] = lwlash

    ### Get LOWFS ADC status ###
    def getlwadcstat(self):
        
        ret = self.AO188ExecCmdRecv("/home/ao/ao188/bin/howfs_adc st")
       
        if ret == "" :
            raise AO188Error("Error: %s" % "LOWFS ADC status is not available")
  
        # split status line into array
        r = re.compile('[\s:,\[\]\(\)\n]+')
        param = r.split(ret)

        # Initialize status
        lwadcstat = lwadcmode = "UNKNOWN"
        lwadcra = lwadcdec = "UNKNOWN"
        lwadcpa = -999.9
        lwadcfc = -99.9
        lwadca1 = lwadca2 = -999.9
        lwadca1m = lwadc2m = -999

        # parse status array
        for item in range(len(param)):
            if param[item] == "ADC" and param[item+1] == "Status":
                lwadcstat = param[item+2]
            elif param[item] == "Mode": 
                lwadcmode = param[item+1]
            elif param[item] == "FC": 
                if isfloat(param[item+1]):
                    lwadcfc = float(param[item+1])
            elif param[item] == "RA":
                if isfloat(param[item+1]) and isfloat(param[item+2]) and isfloat(param[item+3]):
                    lwadcra = param[item+1]+":"+param[item+2]+":"+param[item+3]
            elif param[item] == "Dec":
                if isfloat(param[item+1]) and isfloat(param[item+2]) and isfloat(param[item+3]):
                    lwadcdec = param[item+1]+":"+param[item+2]+":"+param[item+3]
            elif param[item] == "PA":
                if isfloat(param[item+1]):
                    lwadcpa = float(param[item+1])
            elif param[item] == "ADC" and param[item+1] == "P1" and param[item+2] == "Rotation":
                if isfloat(param[item+4]):
                    lwadca1 = float(param[item+4])
                if isfloat(param[item+6]):
                    lwadca1m = float(param[item+6])
            elif param[item] == "ADC" and param[item+1] == "P2" and param[item+2] == "Rotation":
                if isfloat(param[item+4]):
                    lwadca2 = float(param[item+4])
                if isfloat(param[item+6]):
                    lwadca2m = float(param[item+6])

        # register status values
        self.mystatus2['lwadcstat'] = lwadcstat
        self.mystatus2['lwadcmode'] = lwadcmode
        self.mystatus2['lwadcfc'] = lwadcfc
        self.mystatus2['lwadcra'] = lwadcra
        self.mystatus2['lwadcdec'] = lwadcdec
        self.mystatus2['lwadcpa'] = lwadcpa
        self.mystatus2['lwadca1'] = lwadca1
        self.mystatus2['lwadca1m'] = lwadca1m
        self.mystatus2['lwadca2'] = lwadca2
        self.mystatus2['lwadca2m'] = lwadca2m

    ### get environment status ###
    def getenvstat(self):

        ret = self.AO188SendCmdRecv("envmon", "envmon st\r")

        # split status line into array 
        r = re.compile('[\s:,\[\]\(\)=]+')
        param = r.split(ret)

        # initialize status values 
        apdti = apdto = -99.9
        bncti = bncto = -99.9
        bnchi = bncho = -99.9

        # parse status array 
        for item in range(len(param)):
            if param[item] == "Inlet" and param[item+1] == "coolant":
                if isfloat(param[item+2]):
                    apdti = float(param[item+2])
            elif param[item] == "Outlet" and param[item+1] == "coolant":
                if isfloat(param[item+2]):
                    apdto = float(param[item+2])
            elif param[item] == "Bench" and param[item+1] == "inside":
                if isfloat(param[item+3]):
                    bncti = float(param[item+3])
                if isfloat(param[item+6]):
                    bnchi = float(param[item+6])
            elif param[item] == "Bench" and param[item+1] == "outside":
                if isfloat(param[item+3]):
                    bncto = float(param[item+3])
                if isfloat(param[item+6]):
                    bncho = float(param[item+6])        

        # register status values 
        self.mystatus1['apdti'] = apdti
        self.mystatus1['apdto'] = apdto
        self.mystatus1['bncti'] = bncti
        self.mystatus1['bncto'] = bncto
        self.mystatus1['bnchi'] = bnchi
        self.mystatus1['bncho'] = bncho

    #######################
    # INSTRUMENT COMMANDS #
    #######################

    ### Entrance shutter ###
    def ent_shut(self,  cmd='NOP', val='NOP', server='NOP'):
        
        # check command
        if cmd == None or val == None :
            raise AO188Error("Error: no command selected for entshut")
        
        # make command string
        cmdstr = "entshut %s\r" % (str(val.lower()))
        
        # send command to server
        self.AO188SendCmd(server, cmdstr)
        
        # update status
        self.put_status(target="ENSHT")


    ### CAL XZ-stage ###
    def calxz(self,  cmd='NOP', val_x='NOP', val_z='NOP', pos='NOP', server='NOP'):
        # make command string and send command
        if cmd.lower() == 'set' :
            if pos.lower() == 'out' or pos.lower() == 'center':
                cmdstr = "calxz all %s\r" % (str(pos.lower()))
                self.AO188SendCmd(server, cmdstr)
            elif  pos.lower() == 'gascell': # special case for gas cell
                cmdstr = "calxz all gas_cell\r"
                self.AO188SendCmd(server, cmdstr)
        elif cmd.lower() == 'movrel' or cmd.lower() == 'movabs':
            # change command to mactch calxz syntax
            if cmd.lower() == 'movabs':
                cmd = 'ma'
            else :
                cmd = 'mr'

            # check value and execute command
            if isfloat(val_x) and  isfloat(val_z) :
                # moving cal xz-stage to commanded position
                cmdstr = "calxz x %s %.3f\r" % (str(cmd), float(val_x))
                self.AO188SendCmd(server, cmdstr)
                cmdstr = "calxz z %s %.3f\r" % (str(cmd), float(val_z))
                self.AO188SendCmd(server, cmdstr)
            else :
                raise AO188Error("Error: invalid values (%s , %s) for calxz %s" % (str(val_x), str(val_z), str(cmd)))
            
        else :
            raise AO188Error("Error: unknown command (calxz %s)" % (str(cmd.lower())))

        # update status
        self.put_status(target="CAL")
        
    ### CAL LD ###
    def calld(self,  id='NOP', cmd='NOP', val='NOP', pwr='NOP', server='NOP'):
        if cmd.lower() == 'ild':
            # set current value in Iconst mode
            cmdstr = "calld %d ild %.3f\r" % (int(id), float(val))
            # send command to server
            self.AO188SendCmd(server, cmdstr)
        elif cmd.lower() == 'power':
            if int(id) == 4:
                if str(pwr.lower()) == 'off':
                    # turn off alignment laser
                    self.AO188ExecCmd('/home/ao/ao188/bin/pwrsw 10.0.0.28 off 1')
                else :
                    # cannot turn on alignment laser
                    raise AO188Error("Error: cannot turn on the alignment laser from Gen2")
            else :
                # LD power turn on/off
                cmdstr = "calld %d %s\r" % (int(id), str(pwr))
                # send command to server
                self.AO188SendCmd(server, cmdstr)
        else :
            raise AO188Error("Error: unknown command (calld %s)" % (str(cmd.lower())))

        # Update status
        self.put_status(target="CAL")

    ### CALM ###
    def calm(self, dev='NOP', cmd='NOP', server='NOP'):
        # check device
        if dev == None:
            raise AO188Error("Error: no device selected")
        # check command
        if cmd == None:
            raise AO188Error("Error: no command selected")

        # make command string
        cmdstr = "calm %s %s\r" % (str(dev.lower()), str(cmd.lower()))
        # send command to server
        self.AO188SendCmd(server, cmdstr)
        # Update status
        self.put_status(target="CAL")

    #### IMR ###
    def imgrot(self, move='LINK', coord='ABS', ra='NOP', dec='NOP', equinox=2000.0, position=0.0, imrangle=0.0, target='NOP', tmode='NOP', server='NOP'):

        # get current IMR status
        self.getimrstat()

        imr_sts = ""
        ret_str = ""
        
        if move.lower() == 'stop' or move.lower() == 'free':
            if self.mystatus2['imrstat'].lower() != "stand-by":
                cmdstr = "IMR %s\r" % (str(move).upper())
                self.logger.info("Command sent to imrsrv: %s" % str(cmdstr))
                ret_str = self.AO188SendCmdRecv(server, cmdstr)
        elif move.lower() == 'slew':
            cmdstr = "IMR SLEW IMRANGLE=%.3f\r" % (float(imrangle))
            self.logger.info("Command sent to imrsrv: %s" % str(cmdstr))
            ret_str = self.AO188SendCmdRecv(server, cmdstr)

        elif move.lower() == 'link':
            if ra == None or dec == None:
                                
                # get current coordinates
                try:
                    # initialize status dictionary
                    statusDict = {'STATS.RA': 'NOP', 'STATS.DEC': 'NOP'}
                    self.ocs.requestOCSstatus(statusDict)
                    ra = statusDict['STATS.RA']
                    dec = statusDict['STATS.DEC']
                    self.logger.info("RA = %s , Dec = %s" % (str(ra), str(dec)))
                except Exception, e:
                        raise AO188Error("Error getting OCS status: %s" % str(e))

            (rah,ramin,rasec)=radec.parseHMS(ra)
            (sign, decd, decmin, decsec)=radec.parseDMS(dec)

            ra_imr = radec.raHmsToString(rah, ramin, rasec, format='%02d:%02d:%06.3f')
            dec_imr = radec.decDmsToString(sign, decd, decmin, decsec, format='%s%02d:%02d:%05.2f')

            if coord.lower() == 'file':

                # check target file name
                param = target.split(" ")
                if len(param) == 1:
                    target = param[0]
                elif len(param) == 2:
                    target = param[1]
                else :
                    raise AO188Error("Error in TARGET: %s is not correct format" % str(target)) 
                
                
                cmdstr = "IMR LINK RA=%s DEC=%s EQUINOX=%.1f PA=%f TMODE=%s TARGET=%s\r"\
                         % (str(ra_imr), str(dec_imr), float(equinox), float(position), str(tmode), str(target))
                self.logger.info("Command sent to imrsrv: %s" % str(cmdstr))
                ret_str = self.AO188SendCmdRecv(server, cmdstr)

            else :
                cmdstr = "IMR LINK RA=%s DEC=%s EQUINOX=%.1f PA=%f TMODE=%s\r"\
                         %(str(ra_imr), str(dec_imr), float(equinox), float(position), str(tmode))
                self.logger.info("Command sent to imrsrv: %s" % str(cmdstr))
                ret_str = self.AO188SendCmdRecv(server, cmdstr)
                
        else:
            raise AO188Error("Error in MOVE: %s" % move)

        
        self.logger.info("Received string from imrsrv: %s" % ret_str)
        
        imr_str = ret_str
        # remove stoplist 
        stoplist=["ERROR:\r","\r"]
        #stoplist=["ERROR:\n\r","\n\r"]
        #stoplist=["ERROR:\n\r","DONE:\n\r"]
        stoppattern='|'.join(map(re.escape, stoplist))
        imr_str = re.sub(stoppattern,'',ret_str)
        
        #print "   imgrot: len= %d imr_str= %s" % (len(imr_str), str(imr_str))
        # truncate, do not remove 
        imr_str = imr_str[:24]
        #print "   imgrot: len= %d imr_str= %s" % (len(imr_str), str(imr_str))

        if ret_str.find("ERROR:") != -1:
            raise AO188Error ("Error: %s" % str(imr_str))
        elif imr_str.find("DONE:") != -1:
            pass
        else:
            pass

        # TODO: Uncomment 
        self.put_status(target="IMR")

    ### SciPath ADC ###
    def sadc(self, move='NOP', coord='NOP', ra='NOP', dec='NOP', equinox=2000.0, pa=0.0, ang1=0.0, ang2=0.0, fc=1.0, target='NOP', mode='NOP', server='NOP'):
        # get SADC status 
        self.getsadcstat()
        
        if move.lower() == 'free':
            self.AO188ExecCmd("/home/ao/ao188/bin/sadct async")
        elif move.lower() == 'link':
            if equinox != 2000.0:
                raise AO188Error ("Error: equinox %f is not supported" % float(equinox))
            
            if ra == None or dec == None:
                                
                # get current coordinates
                try:
                    # initialize status dictionary
                    statusDict = {'STATS.RA': 'NOP', 'STATS.DEC': 'NOP'}
                    self.ocs.requestOCSstatus(statusDict)
                    ra = statusDict['STATS.RA']
                    dec = statusDict['STATS.DEC']
                    self.logger.info("RA = %s , Dec = %s" % (str(ra), str(dec)))
                except Exception, e:
                        raise AO188Error("Error getting OCS status: %s" % str(e))

            (rah,ramin,rasec)=radec.parseHMS(ra)
            (sign, decd, decmin, decsec)=radec.parseDMS(dec)

            ra_adc = radec.raHmsToString(rah, ramin, rasec, format='%02d:%02d:%06.3f')
            dec_adc = radec.decDmsToString(sign, decd, decmin, decsec, format='%s%02d:%02d:%05.2f')

            if coord == 'ABS':
                self.AO188ExecCmd('/home/ao/ao188/bin/sadct async')
                self.AO188ExecCmd('/home/ao/ao188/bin/sadct pa %f' % float(pa))
                self.AO188ExecCmd('/home/ao/ao188/bin/sadct mode %s' % str(mode.lower()))
                self.AO188ExecCmd('/home/ao/ao188/bin/sadct fc %f' % float(fc))
                self.AO188ExecCmd('/home/ao/ao188/bin/sadct radec %s %s' % (str(ra_adc),str(dec_adc)))
                self.AO188ExecCmd('/home/ao/ao188/bin/sadct sync')
            else :
                raise AO188Error ("Error: Non-sidereal tracking is not implemented")
        elif move.lower() == 'stop':
            self.AO188ExecCmd("/home/ao/ao188/bin/sadc all stop")
            if self.mystatus2['sadcstat'].lower() != "async":
                raise AO188Error("Error: cannot stop rotation stages while synchronizing")
        elif move.lower() == 'slew':
            if self.mystatus2['sadcstat'].lower() != "async":
                raise AO188Error("Error: cannot slew rotation stages while synchronizing")
            else:
                self.AO188ExecCmd("/home/ao/ao188/bin/sadc adcp1r ma %f" % float(ang1))
                self.AO188ExecCmd("/home/ao/ao188/bin/sadc adcp2r ma %f" % float(ang2))
        elif move.lower() == 'base':
            if self.mystatus2['sadcstat'].lower() != "async":
                raise AO188Error("Error: cannot slew rotation stages while synchronizing")
            else:
                self.AO188ExecCmd("/home/ao/ao188/bin/sadct base")
        elif move.lower() == 'in':
            self.AO188ExecCmd("/home/ao/ao188/bin/sadct in")
        elif move.lower() == 'out':
            self.AO188ExecCmd("/home/ao/ao188/bin/sadct out")

        # update status
        self.put_status(target="SADC")

    ### HOWFS ADC ###
    def hwadc(self, move='NOP', coord='NOP', ra='NOP', dec='NOP', equinox=2000.0, pa=0.0, ang1=0.0, ang2=0.0, fc=1.0, target='NOP', mode='NOP', server='NOP'):
        # get SADC status 
        self.gethwadcstat()
        
        if move.lower() == 'free':
            self.AO188ExecCmd("/home/ao/ao188/bin/howfs_adc async")
        elif move.lower() == 'link':
            if equinox != 2000.0:
                raise AO188Error ("Error: equinox %f is not supported" % float(equinox))
            
            if ra == None or dec == None:
                                
                # get current coordinates
                try:
                    # initialize status dictionary
                    statusDict = {'STATS.RA': 'NOP', 'STATS.DEC': 'NOP'}
                    self.ocs.requestOCSstatus(statusDict)
                    ra = statusDict['STATS.RA']
                    dec = statusDict['STATS.DEC']
                    self.logger.info("RA = %s , Dec = %s" % (str(ra), str(dec)))
                except Exception, e:
                        raise AO188Error("Error getting OCS status: %s" % str(e))

            (rah,ramin,rasec)=radec.parseHMS(ra)
            (sign, decd, decmin, decsec)=radec.parseDMS(dec)

            ra_adc = radec.raHmsToString(rah, ramin, rasec, format='%02d:%02d:%06.3f')
            dec_adc = radec.decDmsToString(sign, decd, decmin, decsec, format='%s%02d:%02d:%05.2f')

            if coord == 'ABS':
                self.AO188ExecCmd('/home/ao/ao188/bin/howfs_adc async')
                self.AO188ExecCmd('/home/ao/ao188/bin/howfs_adc pa %f' % float(pa))
                self.AO188ExecCmd('/home/ao/ao188/bin/howfs_adc mode %s' % str(mode.lower()))
                self.AO188ExecCmd('/home/ao/ao188/bin/howfs_adc fc %f' % float(fc))
                self.AO188ExecCmd('/home/ao/ao188/bin/howfs_adc radec %s %s' % (str(ra_adc),str(dec_adc)))
                self.AO188ExecCmd('/home/ao/ao188/bin/howfs_adc sync')
            else :
                raise AO188Error ("Error: Non-sidereal tracking is not implemented" % float(equinox))
        elif move.lower() == 'stop':
            self.AO188ExecCmd("/home/ao/ao188/bin/howfs adcp1r stop")
            self.AO188ExecCmd("/home/ao/ao188/bin/howfs adcp2r stop")
            if self.mystatus2['hwadcstat'].lower() != "async":
                raise AO188Error("Error: cannot stop rotation stages while synchronizing")
        elif move.lower() == 'slew':
            if self.mystatus2['hwadcstat'].lower() != "async":
                raise AO188Error("Error: cannot slew rotation stages while synchronizing")
            else:
                self.AO188ExecCmd("/home/ao/ao188/bin/howfs adcp1r ma %f" % float(ang1))
                self.AO188ExecCmd("/home/ao/ao188/bin/howfs adcp2r ma %f" % float(ang2))
        elif move.lower() == 'base':
            if self.mystatus2['hwadcstat'].lower() != "async":
                raise AO188Error("Error: cannot slew rotation stages while synchronizing")
            else:
                self.AO188ExecCmd("/home/ao/ao188/bin/howfs_adc base")

        # update status
        self.put_status(target="HWADC")

    ### LOWFS ADC ###
    def lwadc(self, move='NOP', coord='NOP', ra='NOP', dec='NOP', equinox=2000.0, pa=0.0, ang1=0.0, ang2=0.0, fc=1.0, target='NOP', mode='NOP', server='NOP'):
        # get SADC status 
        self.getlwadcstat()
        
        if move.lower() == 'free':
            self.AO188ExecCmd("/home/ao/ao188/bin/lowfs_adc async")
        elif move.lower() == 'link':
            if equinox != 2000.0:
                raise AO188Error ("Error: equinox %f is not supported" % float(equinox))
            
            if ra == None or dec == None:
                                
                # get current coordinates
                try:
                    # initialize status dictionary
                    statusDict = {'STATS.RA': 'NOP', 'STATS.DEC': 'NOP'}
                    self.ocs.requestOCSstatus(statusDict)
                    ra = statusDict['STATS.RA']
                    dec = statusDict['STATS.DEC']
                    self.logger.info("RA = %s , Dec = %s" % (str(ra), str(dec)))
                except Exception, e:
                        raise AO188Error("Error getting OCS status: %s" % str(e))

            (rah,ramin,rasec)=radec.parseHMS(ra)
            (sign, decd, decmin, decsec)=radec.parseDMS(dec)

            ra_adc = radec.raHmsToString(rah, ramin, rasec, format='%02d:%02d:%06.3f')
            dec_adc = radec.decDmsToString(sign, decd, decmin, decsec, format='%s%02d:%02d:%05.2f')

            if coord == 'ABS':
                self.AO188ExecCmd('/home/ao/ao188/bin/lowfs_adc async')
                self.AO188ExecCmd('/home/ao/ao188/bin/lowfs_adc pa %f' % float(pa))
                self.AO188ExecCmd('/home/ao/ao188/bin/lowfs_adc mode %s' % str(mode.lower()))
                self.AO188ExecCmd('/home/ao/ao188/bin/lowfs_adc fc %f' % float(fc))
                self.AO188ExecCmd('/home/ao/ao188/bin/lowfs_adc radec %s %s' % (str(ra_adc),str(dec_adc)))
                self.AO188ExecCmd('/home/ao/ao188/bin/lowfs_adc sync')
            else :
                raise AO188Error ("Error: Non-sidereal tracking is not implemented" % float(equinox))
        elif move.lower() == 'stop':
            self.AO188ExecCmd("/home/ao/ao188/bin/lowfs adcp1r stop")
            self.AO188ExecCmd("/home/ao/ao188/bin/lowfs adcp2r stop")
            if self.mystatus2['lwadcstat'].lower() != "async":
                raise AO188Error("Error: cannot stop rotation stages while synchronizing")
        elif move.lower() == 'slew':
            if self.mystatus2['lwadcstat'].lower() != "async":
                raise AO188Error("Error: cannot slew rotation stages while synchronizing")
            else:
                self.AO188ExecCmd("/home/ao/ao188/bin/lowfs adcp1r ma %f" % float(ang1))
                self.AO188ExecCmd("/home/ao/ao188/bin/lowfs adcp2r ma %f" % float(ang2))
        elif move.lower() == 'base':
            if self.mystatus2['lwadcstat'].lower() != "async":
                raise AO188Error("Error: cannot slew rotation stages while synchronizing")
            else:
                self.AO188ExecCmd("/home/ao/ao188/bin/lowfs_adc base")

        # update status
        self.put_status(target="LWADC")

    ###  CNTMON ###
    def cntmon(self, cmd='NOP', arg='NOP', val1=0.0, val2=0.0, mtx='NOP', server='NOP'):
        
        if cmd.lower() == 'loop':
            # check argument and values
            if arg.lower() == 'on' or arg.lower() == 'pause' or arg.lower() == 'resume' or arg.lower() == 'reset':
                cmdstr = 'cntmon %s %s\r' % (str(cmd.lower()), str(arg.lower()))
            
            elif arg.lower() == 'stop':
                cmdstr = 'cntmon %s off 0\r' % (str(cmd.lower()))
            
            elif arg.lower() == 'gain' or arg.lower() == 'gaintt' or arg.lower() == 'psub' or arg.lower() == 'gainstt':
                if isfloat(val1) :
                    cmdstr = 'cntmon %s %s %f\r' % (str(cmd.lower()), str(arg.lower()), float(val1))
                else :
                    raise AO188Error("Error: invalid value (%s) for command (cntmon %s %s)" % (str(val1), str(cmd.lower()), str(arg.lower())))
            
            elif arg.lower() == 'off'  or arg.lower() == 'step':
                if(isfloat(val1)):
                    cmdstr = 'cntmon %s %s %d\r' % (str(cmd.lower()), str(arg.lower()), int(val1))
                else :
                    raise AO188Error("Error: invalid value (%s) for command (cntmon %s %s)" % (str(val1), str(cmd.lower()), str(arg.lower())))
            
            else:
                raise AO188Error("Error: unknown command (cntmon %s %s)" % (str(cmd.lower()), str(arg.lower())))
            
            # send command to server
            self.AO188SendCmd(server, cmdstr)

        elif cmd.lower() == 'dm':
            # check argument and values
            if arg.lower() == 'zero' or arg.lower() == 'flat' or arg.lower() == 'refresh':
                cmdstr = 'cntmon %s %s\r' % (str(cmd.lower()), str(arg.lower()))
                self.AO188SendCmd(server, cmdstr)
            elif arg.lower() == 'saveflat':
                cmdstr = 'cntmon %s %s\r' % (str(cmd.lower()), str(arg.lower()))
                ret_str = self.AO188SendCmdRecv(server, cmdstr)
            else:
                raise AO188Error("Error: unknown command (cntmon %s %s)" % (str(cmd.lower()), str(arg.lower())))

        elif cmd.lower() == 'tt' or cmd.lower() == 'stt' or cmd.lower() == 'wtt':
            if arg.lower() == 'zero' or arg.lower() == 'flat' :
                 cmdstr = 'cntmon %s %s\r' % (str(cmd.lower()), str(arg.lower()))
                 self.AO188SendCmd(server, cmdstr)
            elif arg.lower() == 'movabs': 
                if isfloat(val1) and isfloat(val2) :
                    cmdstr = "cntmon %s tip %.3f\r" %  (str(cmd.lower()), float(val1))
                    self.AO188SendCmd(server, cmdstr)
                    cmdstr = "cntmon %s tilt %.3f\r" % (str(cmd.lower()), float(val2))
                    self.AO188SendCmd(server, cmdstr)
                else :
                    raise AO188Error("Error: invalid values (%s , %s) for tip/tilt" % (str(val1), str(val2)))
            elif arg.lower() == 'movrel': 
                if isfloat(val1) and isfloat(val2) :
                    cmdstr = "cntmon %s tip %.3f r\r" % (str(cmd.lower()), float(val1))
                    ret_str = self.AO188SendCmdRecv(server, cmdstr)
                    cmdstr = "cntmon %s tilt %.3f r\r" % (str(cmd.lower()), float(val2))
                    ret_str = self.AO188SendCmdRecv(server, cmdstr)
                else :
                    raise AO188Error("Error: invalid values (%s , %s) for %s" % (str(val1), str(val2)), str(cmd))
            elif arg.lower() == 'saveflat':
                cmdstr = 'cntmon %s %s\r' % (str(cmd.lower()), str(arg.lower()))
                ret_str = self.AO188SendCmdRecv(server, cmdstr)
            else:
                raise AO188Error("Error: unknown command (cntmon %s %s)" % (str(cmd.lower()), str(arg.lower())))

        elif cmd.lower() == 'gain':
            if arg.lower() == 'clear':
                cmdstr = "cntmon send %s %s\r" % (str(cmd.lower()), str(arg.lower()))
            elif arg.lower() == 'wtt' or arg.lower() == 'ltt' or arg.lower() == 'ldf' or arg.lower() == 'htt' \
                    or arg.lower() == 'hdf' or arg.lower() == 'dmg' or arg.lower() == 'ttg' or arg.lower() == 'pss':
                cmdstr = "cntmon send %s %s %f\r" % (str(cmd.lower()), str(arg.lower()), float(val1))
            else :
                raise AO188Error("Error: unknown command (cntmon %s %s)" % (str(cmd.lower()), str(arg.lower())))
            ret_str =  self.AO188SendCmdRecv(server, cmdstr)

        elif cmd.lower() == 'cmtx':
            if arg.lower() == 'load':
                if mtx.lower() == 'ngs':
                    cmdstr = "cntmon send cmtx load config/ao188cmtx.oct\r"
                    ret_str =  self.AO188SendCmdRecv(server, cmdstr)
                elif mtx.lower() == 'lgs':
                    cmdstr = "cntmon send cmtx load config/ao188cmtx_lgs.oct\r"
                    ret_str =  self.AO188SendCmdRecv(server, cmdstr)
                elif mtx.lower() == 'auto':
                    raise AO188Error("Error: cmtx load auto is not implemented")
                else :
                    raise AO188Error("Error: unknown control matrix (%s)" % str(val1))
            else :
                raise AO188Error("Error: unknown command (cntmon %s %s)" % (str(cmd.lower()), str(arg.lower())))

        # update status 
        self.put_status(target="LOOP")
        self.put_status(target="TT")

        
    ### command for changing loop parameters --- replaced by CNTMON soon ### 
    def loop(self, cmd='NOP', time='NOP', server='NOP'):
        self.cntmon('LOOP', cmd, int(time), 0.0, 'NOP', server)

    ### command for changing Tip/Tilt mount parameters -- replaced by CNTMON soon ### 
    def dm(self, cmd='NOP', val='NOP', server='NOP'):
        if cmd.lower() == 'setgain':
            self.cntmon('LOOP', 'GAIN',float(val), 0.0, 'NOP', server)
        elif cmd.lower() == "setvolt":
            self.cntmon('DM', val, 0.0, 0.0, 'NOP', server)


    ### command for changing Tip/Tilt mount parameters -- replaced by CNTMON soon  ### 
    def tt(self, cmd='NOP', val='NOP', ttx='NOP', tty='NOP', server='NOP'):
        if cmd.lower() =='setgain':
            self.cntmon('LOOP', 'GAINTT',float(val), 0.0, 'NOP', server)
        elif cmd.lower() == 'setvolt':
            self.cntmon('TT', val, float(ttx), float(tty), 'NOP', server)
            
    #### command for changing Secondary Tip/Tilt parameters from count monitor -- replaced by CNTMON soon ### 
    def stt(self, cmd='NOP', val='NOP', ttx='NOP', tty='NOP', server='NOP'):
        if cmd.lower() =='setgain':
            self.cntmon('LOOP', 'GAINSTT', float(val), 0.0, 'NOP', server)
        elif cmd.lower() == 'setvolt':
            self.cntmon('STT', val, float(ttx), float(tty), 'NOP', server)
 
    # command for changing Secondary Tip/Tilt parameters from irm2 client
    # made by Oya-san
    def irm2tt(self, proc='NOP', gain='NOP', server='NOP'):

        # IP address for VME computer
        vme_ip = "10.0.0.88"

        # irm2tt client command
        com = "/home/ao/bin/irm2ttComCli"
        
        # make SOSS command string
        if proc == None:
            soss_cmd = "EXEC AO188 IRM2TT GAIN=%f" % float(gain)
        else:
            soss_cmd = "EXEC AO188 IRM2TT PROC=%s" % str(proc)

        # command string
        cmdstr = com + " " + vme_ip + " " + "\""+ soss_cmd + "\""

        # execute command  
        irm2tt_proc = subprocess.Popen([cmdstr], shell=True, stdout=subprocess.PIPE)
        ret_str = irm2tt_proc.stdout.read()
        if ret_str[:-1] != "OK" :
            raise AO188Error("Error in IRM2TT: %s" % ret_str[:-1])
        
    ### BS ###
    def bs(self, dev='NOP', cmd='NOP', server='NOP'):
        # make command string
        cmdstr = "%s %s\r" % (str(dev.lower()), str(cmd.lower()))
        # send command to server
        self.AO188SendCmd(server, cmdstr)
        # update status
        self.put_status(target="BS")
        

    ### AU ###
    def au(self,dev='NOP', cmd='NOP', val1=0.0, val2=0.0, ins='NOP', pixscale='NOP', mode='NOP', server='NOP'):

        if dev == None:
            raise AO188Error("Error: no device selected")
        
         # chcek command and move AU
        if cmd.lower() == "aoff" or cmd.lower() == "roff" or cmd.lower() == "asoff" or cmd.lower() == "rsoff"\
                or cmd.lower() == "atilt" or cmd.lower() == "rtilt" or cmd.lower() == "ttzero"\
                or cmd.lower() == "wacq" or cmd.lower() == "hacq" or cmd.lower() == "pacq"\
                or cmd.lower() == "rwoff" or cmd.lower() == "rhoff" or cmd.lower() == "rpoff":
            if isfloat(val1) and isfloat(val2) :
                cmdstr = "%s %s %.5f %.5f\r" % (str(dev.lower()),str(cmd.lower()), float(val1), float(val2))
                self.AO188SendCmd(server, cmdstr)
            else:
                raise AO188Error("Error: invalid values (%s , %s) for %s %s command"\
                                         % (str(val1), str(val2), str(dev.lower()), str(cmd.lower())))
                
        elif cmd.lower() == "afocus" or cmd.lower() == "rfocus":
            if isfloat(val1):
                cmdstr = "%s %s %.5f\r" % (str(dev.lower()),str(cmd.lower()), float(val1))
                self.AO188SendCmd(server, cmdstr)
            else:
                raise AO188Error("Error: invalid value (%s) for %s %s command"\
                                     % (str(val1), str(dev.lower()), str(cmd.lower())))

        elif cmd.lower() == "mode" :
            if mode != None :
                cmdstr = "%s %s %s\r" % (str(dev.lower()),str(cmd.lower()), str(mode.lower()))
                self.AO188SendCmd(server, cmdstr)
            else:
                raise AO188Error("Error: no value selected for %s %s command"\
                                     % (str(dev.lower()), str(cmd.lower())))
            
        elif cmd.lower() == "base" :
            if ins != None :
                cmdstr = "%s instbase %s\r" % (str(dev.lower()), str(ins.lower()))
                self.AO188SendCmd(server, cmdstr)
                cmdstr = "%s %s\r" % (str(dev.lower()),str(cmd.lower()))
                self.AO188SendCmd(server, cmdstr)
            else:
                raise AO188Error("Error: no value selected for %s %s command"\
                                     % (str(dev.lower()), str(cmd.lower())))

        elif cmd.lower() == "scicam" :
            if ins != None and pixscale != None:
                scicamid = str(ins.lower()) + str(pixscale.lower())
                
                # set instrument base 
                cmdstr = "%s instbase %s\r" % (str(dev.lower()),str(ins.lower()))
                self.AO188SendCmd(server, cmdstr)

                # set science camera
                cmdstr = "%s scicam %s\r" % (str(dev.lower()),str(scicamid))
                self.AO188SendCmd(server, cmdstr)

            else:
                raise AO188Error("Error: no value selected for %s %s command"\
                                     % (str(dev.lower()), str(cmd.lower())))

        elif cmd.lower() == "stop":
            cmdstr = "%s %s\r" % (str(dev.lower()),str(cmd.lower()))
            self.AO188SendCmd(server, cmdstr)
            
        else :
            raise AO188Error("Error: unknown command (%s)" % str(cmd.lower()))
        
        
        # update status
        if dev.lower() == "au1":
            self.put_status(target="AU1")
        else:
            self.put_status(target="AU2")
        self.put_status(target="TT")

    ### ADF ###
    def adf(self,cmd='NOP', arg='NOP', gain=0.0, time=0, server='NOP'):

        # chcek command
        if cmd.lower() == "loop":
            if arg.lower() == "on" or arg.lower() == "off":
                cmdstr = "adf loop %s\r" % (str(arg.lower()))
            else:
                raise AO188Error("Error: invalid command (adf loop %s)" % (str(arg.lower())))
                
        elif cmd.lower() == "gain":
            if isfloat(gain):
                cmdstr = "adf gain %.5f\r" % (float(gain))
            else:
                raise AO188Error("Error: invalid command (adf gain %s)" % (str(gain)))

        elif cmd.lower() == "interval" :
            if isfloat(interval):
                cmdstr = "adf interval %d\r" % (int(time))
            else:
                raise AO188Error("Error: invalid command (adf gain %s)" % (str(time)))
        else :
            raise AO188Error("Error: unknown command (%s)" % str(cmd.lower()))
        
        # send command string
        self.AO188SendCmd(server, cmdstr)
        
        # update status
        self.put_status(target="AU1")
        
   
    ### Command for AO tip/tilt dithering  ###
    def dith(self, x_pix=0, y_pix=0, ins='NOP', pixscale='NOP', dev='NOP', server='NOP'):

        # make camera ID string
        scicamid = str(ins.lower()) + str(pixscale.lower())

        # make command str
        cmdstr = "%s scicamroff %s %.3f %.3f\r" % (str(dev.lower()), str(scicamid), float(x_pix), float(y_pix))

        # send command to server
        self.AO188SendCmd(server, cmdstr)

        # update status
        if dev.lower() == "au1":
            self.put_status(target="AU1")
        else :
            self.put_status(target="AU2")
        self.put_status(target="TT")

    ### command for AU1 star acquision on science camera ###
    def setaop(self, x_pix=0, y_pix=0, ins='NOP', pixscale='NOP', dev='NOP', server='NOP'):

        # make camera ID string
        scicamid = str(ins.lower()) + str(pixscale.lower())

        # make command string
        cmdstr = "%s scicamacq %s %.2f %.2f\r" % (str(dev.lower()),str(scicamid), float(x_pix), float(y_pix))
        
        # send command to server
        self.AO188SendCmd(server, cmdstr)
        
        # update status
        if dev.lower() == "au1":
            self.put_status(target="AU1")
        else :
            self.put_status(target="AU2")
        self.put_status(target="TT")

    #### command for storing AO GS acquisition point on science camera ###
    def setscicam(self, ins='NOP', pixscale='NOP', dev='NOP', server='NOP'):
        self.au(dev, "scicam", 0.0, 0.0, ins, pixscale, 'NOP', server)

        
    ### command for offloading AO188 Tip/Tilt by moving AU1  -- replaced by au soon  ###
    def au1_move(self,cmd='NOP', val1='NOP', val2='NOP', server='NOP'):
        self.au("AU1", cmd, val1, val2, 'NOP', 'NOP', 'NOP', server)
        

    ### VM ###
    def vm(self, cmd='NOP', val=0.0, pwr='NOP', server='NOP'):

        # make command string
        if cmd.lower() =='power':
            if pwr.lower() == 'on':
                cmdstr = "vm on\r"
            elif pwr.lower() == 'off':
                cmdstr = "vm off\r"
            else :
                raise AO188Error("Error in pwr: %s" % pwr)
        elif cmd.lower() == 'volt':
            if val != None:
                cmdstr = "vm volt %lf\r" % float(val)
            else :
                raise AO188Error("Error in val: %s" % val)                
        elif cmd.lower() == 'freq':
            if val != None:
                cmdstr = "vm freq %lf\r" % float(val)
            else :
                raise AO188Error("Error in val: %s" % val)                
        elif cmd.lower() == 'phase':
            if val != None:
                cmdstr = "vm phase %lf\r" % float(val)
            else :
                raise AO188Error("Error in val: %s" % val)                
        else :
            raise AO188Error("Error in CMD: %s" % ins)

        # send command to server
        self.AO188SendCmd(server, cmdstr)

        # update status
        self.put_status(target="VM")
        self.put_status(target="APDAV")

        
    ### function for opening LA filter wheel  (no para file) ###
    def lafw(self, wfs, cmd, val):
        
        # check wfs
        if wfs.lower() == "howfs":
            self.gethowfsstat()
            lafw_key = 'hwlaf'
            lash_key = 'hwlash'
            apda_key = 'hwapda'
            apd_upper_limit = 350.0 # (R~8.8)
            nave = 3 # average cycle
        elif wfs == "lowfs":
            self.getlowfsstat()
            lafw_key = 'lwlaf'
            lash_key = 'lwlash'
            apda_key = 'lwapda'
            apd_upper_limit = 350.0 # temporary value
            nave = 3 


        if wfs.lower() == 'lowfs' and cmd.lower() == 'go' and val.lower() == 'auto':
            raise AO188Error("Error: auto is not implemented for %s" % (str(wfs)))
        
        # array for storing fw alias names 
        fw_apd_stat = ['close','nd0.01','nd0.03','nd0.1','nd0.3','nd1','nd3','nd10','nd30','none']
        
        if cmd.lower() == 'move':

            fw_apd_id = -1
            for item in range(len(fw_apd_stat)) :
                if self.mystatus1[lafw_key].lower() == fw_apd_stat[item] :
                    fw_apd_id = item
                    
            if fw_apd_id < 0 :
                raise AO188Error("Error: unknown lafw status %s" % param[4])

            if val.lower() == 'step10+' :
                fw_apd_id += 2
            elif val.lower() == 'step3+':
                fw_apd_id += 1
            elif val.lower() == 'step3-':
                fw_apd_id -= 1
            elif val.lower() == 'step10-':
                fw_apd_id -= 2

            if fw_apd_id > len(fw_apd_stat) - 1 :
                fw_apd_id = len(fw_apd_stat) - 1
            elif fw_apd_id < 0 :
                fw_apd_id = 0

            cmdstr = "%s lafw %s\r" % (str(wfs), str(fw_apd_stat[fw_apd_id]))
            self.AO188SendCmd(wfs, cmdstr)
                
        elif cmd.lower() == 'go':
            if val.lower() == "auto":
                
                if self.mystatus1[lash_key].lower() != "open":
                    raise AO188Error("Error: la shutter is not open")

                if self.mystatus1[lafw_key].lower() == "close":
                    cmdstr = "%s lafw nd0.01\r" % (str(wfs))
                    self.AO188SendCmd(wfs, cmdstr)
                    
                for i in range(len(fw_apd_stat)):
                    if wfs == "howfs":
                        self.gethowfsstat()
                    else :
                        self.getlowfsstat()
                        
                    if self.mystatus1[lash_key].lower() != "open":
                        raise AO188Error("Error: la shutter is not open")

                    fw_apd_id = -1
                    for item in range(len(fw_apd_stat)) :
                        if self.mystatus1[lafw_key].lower() == fw_apd_stat[item] :
                            fw_apd_id = item
                            
                    if fw_apd_id < 0 :
                        raise AO188Error("Error: unknown lafw status %s" % self.mystatus1[lafw_key])

                  
                    # get average apd count
                    apd_ave = 0

                    for j in range(nave):
                        self.getcntmonstat(0)
                        apd_ave += float(self.mystatus2[apda_key])

                    apd_ave = apd_ave / float(nave)

                    # check APD power is on
                    if apd_ave <= 0 :
                        raise AO188Error("Error: failed to get APD count")
                        
                    # calculate next fw position
                    p = float(apd_upper_limit) / float(apd_ave)
                    if p > 10.0:
                        fw_apd_id += 2
                    elif p <= 10.0 and p > 3.0:
                        fw_apd_id += 1
                    else :
                        break

                    # check fw_apd_id value and send command to server
                    if fw_apd_id >= len(fw_apd_stat) - 1:
                        fw_apd_id = len(fw_apd_stat) -1
                        cmdstr = "%s lafw %s\r" % (str(wfs), str(fw_apd_stat[fw_apd_id]))
                        self.AO188SendCmd(wfs, cmdstr)
                        break
                    else :
                        cmdstr = "%s lafw %s\r" % (str(wfs), str(fw_apd_stat[fw_apd_id]))
                        self.AO188SendCmd(wfs, cmdstr)
            
            else :
                # make command string
                cmdstr = "%s lafw %s\r" % (str(wfs), str(val.lower()))
                self.AO188SendCmd(wfs, cmdstr)

        elif cmd.lower() == 'stop':
            cmdstr = "%s lafw stop \r" % (str(wfs))
            self.AO188SendCmd(wfs, cmdstr)

    ### function for opening LA filter wheel  (no para file) ###
    def laz(self, wfs, cmd):
        
        # check wfs
        if wfs.lower() == 'howfs':
            self.gethowfsstat()
        elif wfs.lower() == 'lowfs':
            self.getlowfsstat()
        else:
            raise AO188Error("Error: unknown WFS (%s)" % (str(wfs)))

        if cmd.lower() == 'auto':
            if wfs.lower() == 'howfs' :
                laz = ""

                # check ADC/WTT 
                if self.mystatus1['hwnap'].lower() == "mirror":
                    laz = laz + "lgs"
                else:
                    if self.mystatus1['hwadc'].lower() == "in": 
                        laz = laz + "adc"
                
                # NOBS 
                if self.mystatus1['hwabs'].lower() == "none" and self.mystatus1['hwhbs'].lower() == "none" and self.mystatus1['hwpbs'].lower() == "none":
                    if laz == "":
                        laz = "nobs"

                # ALLBS
                elif self.mystatus1['hwabs'].lower() != "none" and self.mystatus1['hwhbs'].lower() != "none" and self.mystatus1['hwpbs'].lower() != "none":
                    if laz == "":
                        laz = "allbs"
                    else :
                        laz = laz + "+allbs"

                # ABS
                elif self.mystatus1['hwabs'].lower() != "none" and self.mystatus1['hwhbs'].lower() == "none" and self.mystatus1['hwpbs'].lower() == "none":
                    if laz == "":
                        laz = "abs"
                    else :
                        laz = laz + "+abs"

                # HBS
                elif self.mystatus1['hwabs'].lower() == "none" and self.mystatus1['hwhbs'].lower() != "none" and self.mystatus1['hwpbs'].lower() == "none":
                    if laz == "":
                        laz = "hbs"
                    else :
                        laz = laz + "+hbs"

                # PBS
                elif self.mystatus1['hwabs'].lower() == "none" and self.mystatus1['hwhbs'].lower() == "none" and self.mystatus1['hwpbs'].lower() != "none":
                    if laz == "":
                        laz = "pbs"
                    else :
                        laz = laz + "+pbs"

                # ABS+HBS
                elif self.mystatus1['hwabs'].lower() != "none" and self.mystatus1['hwhbs'].lower() != "none" and self.mystatus1['hwpbs'].lower() == "none":
                    if laz == "":
                        laz = "abs+hbs"
                    else :
                        laz = laz + "+abs+hbs"

                # ABS+PBS
                elif self.mystatus1['hwabs'].lower() != "none" and self.mystatus1['hwhbs'].lower() == "none" and self.mystatus1['hwpbs'].lower() != "none":
                    if laz == "":
                        laz = "abs+pbs"
                    else :
                        laz = laz + "+abs+pbs"

                # HBS+PBS
                elif self.mystatus1['hwabs'].lower() == "none" and self.mystatus1['hwhbs'].lower() != "none" and self.mystatus1['hwpbs'].lower() != "none":
                    if laz == "":
                        laz = "hbs+pbs"
                    else :
                        laz = laz + "+hbs+pbs"

            elif wfs.lower() == 'lowfs' :

                laz = ""
               
                # check ADC 
                if self.mystatus1['lwadc'].lower() == "in": 
                    laz = laz + "adc"
                
                # NOBS 
                if self.mystatus1['lwabs'].lower() == "none" and self.mystatus1['lwpbs'].lower() == "none":
                    if laz == "":
                        laz = "nobs"

                # ALLBS
                elif self.mystatus1['lwabs'].lower() != "none" and self.mystatus1['lwpbs'].lower() != "none":
                    if laz == "":
                        laz = "allbs"
                    else :
                        laz = laz + "+allbs"

                # ABS
                elif self.mystatus1['lwabs'].lower() != "none" and self.mystatus1['lwpbs'].lower() == "none":
                    if laz == "":
                        laz = "abs"
                    else :
                        laz = laz + "+abs"

                # PBS
                elif self.mystatus1['lwabs'].lower() == "none" and self.mystatus1['lwpbs'].lower() != "none":
                    if laz == "":
                        laz = "pbs"
                    else :
                        laz = laz + "+pbs"


            cmdstr = "%s laz %s\r" % (str(wfs.lower()),str(laz))
            self.AO188SendCmd(wfs, cmdstr)

        else :
            cmdstr = "%s laz %s\r" % (str(wfs.lower()),str(cmd.lower()))
            self.AO188SendCmd(wfs, cmdstr)

    ### WFS ### 
    def wfs(self, wfs='NOP', dev='NOP', cmd='NOP', val=0.0, pos='NOP', server='NOP'):
        
        # check WFS
        if wfs.lower() != "ho" and wfs.lower() != "lo":
            raise AO188Error("Error: unknown wfs (%s)" % (str(wfs.lower())))
        else :
            wfs = wfs.lower()+"wfs"
            
        # check deviceand execute command 
        if dev == None:
            raise AO188Error("Error: no device selected")
        elif dev.lower() == "lash":
            cmdstr = "%s %s %s\r" % (str(wfs), str(dev.lower()), str(cmd.lower()))
            # send twice until HOWFS lashutter problem is fixed
            self.AO188SendCmd(server, cmdstr)
            self.AO188SendCmd(server, cmdstr)
        elif dev.lower() == "vmap" or dev.lower() == "ap2":
            # check command 
            if cmd.lower() == 'full':
                cmdstr = "%s %s %s\r" % (str(wfs), str(dev.lower()), str(cmd.lower()))
            elif cmd.lower() =='movrel':
                if isfloat(val):
                    cmdstr = "%s %s mr %.4f\r" % (str(wfs), str(dev.lower()), float(val))
                else :
                    raise AO188Error("Error: invalid value (%s) for %s %s %s command" % (str(val), str(wfs), str(dev.lower()), str(cmd.lower())))
            elif cmd.lower() == 'movabs':
                if isfloat(val):
                    cmdstr = "%s %s ma %.4f\r" % (str(wfs), str(dev.lower()), float(val))
                else :
                    raise AO188Error("Error: invalid value (%s) for %s %s %s command" % (str(val), str(wfs), str(dev.lower()), str(cmd.lower())))
            else :
                raise AO188Error("Error: unknown command (%s)" % (str(cmd.lower())))
            self.AO188SendCmd(server, cmdstr)
        elif dev.lower() == "lafw":
            self.lafw(wfs, cmd.lower(), pos.lower())
        elif dev.lower() == "laz":
            self.laz(wfs, cmd.lower())
        else :
            cmdstr = "%s %s %s\r" % (str(wfs), str(dev.lower()), str(cmd.lower()))
            self.AO188SendCmd(server, cmdstr)

        # update status    
        if wfs.lower() == 'howfs':
            self.put_status(target="HOWFS")
        else:
            self.put_status(target="LOWFS")
        self.put_status(target="APDAV")


    ### LA shutter ###
    def apd_shut(self, cmd='NOP', val='NOP', dev='NOP'):
        if dev.lower() == 'howfs' :
            self.wfs("HO", "LASH", val, 0.0, "NOP", "HOWFS")
        elif dev.lower() == 'lowfs' :
            self.wfs("LO", "LASH", val, 0.0, "NOP", "LOWFS")
        else :
            raise AO188Error("Error: unknown device (%s)" % str(dev.lowere()))

    ### LAFW ###
    def fw_apd(self, cmd='NOP', val='NOP', dev='NOP'):
        if dev.lower() == 'howfs' :
            self.wfs("HO", "LAFW", cmd, 0.0, val, "HOWFS")
        elif dev.lower() == 'lowfs' :
            self.wfs("LO", "LAFW", cmd, 0.0, val, "LOWFS")
        else :
            raise AO188Error("Error: unknown device (%s)" % str(dev.lowere()))

    ### APD ###
    def apd(self, cmd='NOP', shelf=0, server='NOP'):
        if cmd.lower() == 'on':
            if int(shelf) >= 1 and int(shelf) <= 12:
                cmdstr = '/home/ao/ao188/bin/asc_ctl.py %d /a3ffff > /dev/null' % (int(shelf))
                self.AO188ExecCmd(cmdstr)
            else :
                raise AO188Error("Error: invalid shelf number  (%s)" % (int(shelf)))
        elif cmd.lower() == 'off':
            if int(shelf) >= 1 and int(shelf) <= 12:
                cmdstr = '/home/ao/ao188/bin/asc_ctl.py %d /a00000 > /dev/null' % (int(shelf))
                self.AO188ExecCmd(cmdstr)
            else :
                raise AO188Error("Error: invalid shelf number  (%s)" % (int(shelf)))
        else :
            raise AO188Error("Error: unknown command (%s)" % str(cmd.lower()))

    ### F-conversion optics ###
    def fconv(self,  cmd='NOP', val='NOP', server='NOP'):
        if val.lower() == 'in':
            cmdstr = "fconv in\r"
        elif val.lower() == 'out':
            cmdstr = "fconv out\r"
        else :
            raise AO188Error("Error: unknwon command (%s)" % str(val))

        self.AO188SendCmd(server, cmdstr)            
        self.put_status(target="FCONV")


    ### Audio ###
    def audio(self, cmd='NOP', server='NOP'):
        if cmd.lower() == 'start':
            self.AO188ExecCmd('/home/ao/ao188/bin/start_audio > /dev/null')
        elif cmd.lower() == 'stop':
            self.AO188ExecCmd('/home/ao/ao188/bin/stop_audio > /dev/null')
        else :
            raise AO188Error("Error: unknown command (%s)" % str(cmd.lower()))

    ### Sleep ###
    def sleep(self, sleep_time=0):

        itime = float(sleep_time)
        
        self.logger.info("\nSleeping for %f sec..." % itime)
        time.sleep(itime)
        self.logger.info("Woke up refreshed!")

    # Distributing AO188 status to SOSS
    # Update all status
    def put_status(self, target="ALL"):

        self.mystatus1.setvals(status='ALIVE')
  	# Bump our status
        if target == "ALL" or target == "ENSHT":
            self.getenshutstat()
        if target == "ALL" or target == "IMR":
            self.getimrstat()
        if target == "ALL" or target == "SADC":
            self.getsadcstat()
        if target == "ALL" or target == "BS":
            self.getbsstat()
        if target == "ALL" or target == "FCONV":
            self.getfconvstat()
        if target == "ALL" or target == "LOOP":
            self.getcntmonstat(1)
        if target == "ALL" or target == "APDAV" or target == "TT":
            self.getcntmonstat(1)
        if target == "ALL" or target == "AU1":
            self.getau1stat()
        if target == "ALL" or target == "AU2":
            self.getau2stat()
        if target == "ALL" or target == "HOWFS":
            self.gethowfsstat()
        if target == "ALL" or target == "HWADC":
            self.gethwadcstat()
        if target == "ALL" or target == "LOWFS":
            self.getlowfsstat()
        if target == "ALL" or target == "LWADC":
            self.getlwadcstat()
        if target == "ALL" or target == "VM":
            self.getvmstat()
        if target == "ALL" or target == "CAL":
            self.getcalstat()
        if target == "ALL" or target == "ENV":
            self.getenvstat()
        if target == "ALL" or target == "BENCH":
            self.getaobenchstat()
        if target == "ALL" or target == "LOOPMODE":
            self.getloopmode()

        """Forced export of our status.
        """
        try:
            self.ocs.exportStatus()
        except CamError, e:
            raise AO188Error("Error putting status %s" % str(e))


    # Distributing slow AO188 status
    def put_slow_status(self):

        self.mystatus1.setvals(status='ALIVE')
        self.getenshutstat()
        self.getbsstat()
        self.getfconvstat()
        self.gethowfsstat()
        self.getlowfsstat()
        self.getcalstat()
        self.getenvstat()
        self.getaobenchstat()
 
        """Forced export of our status.
        """
        try:
            self.ocs.exportStatusTable('AONS0001')
        except CamError, e:
            raise AO188Error("Error putting status %s" % str(e))

    # Distributing fast AO188 status
    def put_fast_status(self):
        
        self.getimrstat()
        self.getsadcstat()
        self.getau1stat()
        self.getau2stat()
        self.gethwadcstat()
        self.getlwadcstat()
        self.getcntmonstat(1)
        self.getvmstat()
        self.getloopmode()

        """Forced export of our status.
        """
        try:
            self.ocs.exportStatusTable('AONS0002')
        except CamError, e:
            raise AO188Error("Error putting status %s" % str(e))
                
    def getstatus(self, target="ALL"):
        """Forced import of our status using the normal status interface.
        """
        try:
            ra, dec = self.ocs.requestOCSstatusList2List(['STATS.RA', 'STATS.DEC'])
            #ra, dec = self.ocs.requestOCSstatusList2List(['STATS.RA', 'STATS.DEC'])
        #except CamError, e:
        except Exception, e:
            raise AO188Error("Error getting status: %s" % str(e))
        
            
        self.logger.info("Status returned: ra=%s dec=%s" % (ra, dec))
        
#    def getstatus2(self, target="ALL"):
#        """Forced import of our status using the 'fast' status interface.
#        """
#	ra, dec = self.ocs.getOCSstatusList2List(['STATS.RA', 'STATS.DEC'])
#
#        self.logger.info("Status returned: ra=%s dec=%s" % (ra, dec))


    def fits_file(self, motor='OFF', frame_no=None, delay=None):
	"""One of the commands that are in the SOSSALL.cd.
        """

        self.logger.info("fits_file called...")

	if not frame_no:
	    return 1

        # TODO: make this return multiple fits files
	if ':' in frame_no:
	    (frame_no, num_frames) = frame_no.split(':')
	    num_frames = int(num_frames)
        else:
            num_frames = 1

        # Check frame_no
        match = re.match('^(\w{3})(\w)(\d{8})$', frame_no)
        if not match:
            raise AO188Error("Error in frame_no: '%s'" % frame_no)

	inst_code = match.group(1)
	frame_type = match.group(2)
        # Convert number to an integer
        try:
            frame_cnt = int(match.group(3))
        except ValueError, e:
            raise AO188Error("Error in frame_no: '%s'" % frame_no)

        # Iterate over number of frames, creating fits files
        frame_end = frame_cnt + num_frames
        framelist = []
        
        while frame_cnt < frame_end:
            # Construct frame_no and fits file
            frame_no = '%3.3s%1.1s%08.8d' % (inst_code, frame_type, frame_cnt)
            fitsfile = '%s/%s.fits' % (self.env.INST_PATH, frame_no)

            # take exposure
            hdrkwds = { #'prop-id': self.env.proposal,
                'frameid': frame_no,
                'obcpmode': self.mode,
                }
            fitsutils.make_fakefits(fitsfile, hdrkwds, 10, 5)

            # Add it to framelist
            framelist.append((frame_no, fitsfile))

            frame_cnt += 1

        self.logger.debug("done exposing...")
        
        # If there was a non-negligible delay specified, then queue up
        # a task for later archiving of the file and terminate this command.
        if delay:
            if type(delay) == type(""):
                delay = float(delay)
            if delay > 0.1:
                # Add a task to delay and then archive_framelist
                self.logger.info("Adding delay task with '%s'" % \
                                 str(framelist))
                t = common.DelayedSendTask(self.ocs, delay, framelist)
                t.initialize(self)
                self.threadPool.addTask(t)
                return 0

        # If no delay specified, then just try to archive the file
        # before terminating the command.
        self.logger.info("Submitting framelist '%s'" % str(framelist))
        try:
            self.ocs.archive_framelist(framelist)
        #except CamError, e:
        except Exception, e:
            raise AO188Error("Error archiving file: %s" % str(e))
        
            
    # Command for SOSS acceptance test --- OK 
    def obcp_mode(self, motor='OFF', mode=None):
	"""One of the commands that are in the SOSSALL.cd
        """
        self.mode = mode

#    def schedulermode(self, motor='OFF', mode='OBCP', frame='NOP',
#                      qframe='NOP'):
#        """This is called by SOSS when through mode is initiated.
#        """
#        pass


#    def reqframes(self, num=1, type="A"):
#        """Forced frame request.
#        """
#        framelist = self.ocs.getFrames(num, type)
#
#        # This request is not logged over DAQ logs
#        self.logger.info("framelist: %s" % str(framelist))


    def defaultCommand(self, *args, **kwdargs):
        """This method is called if there is no matching method for the
        command defined.
        """

        # If defaultCommand is called, the cmdName is pushed back on the
        # argument tuple as the first arg
        cmdName = args[0]
        self.logger.info("Called with command '%s', params=%s" % (cmdName,str(kwdargs)))

        res = unimplemented_res
        self.logger.info("Result is %d\n" % res)

	return res


    def power_off(self, upstime=None):
        """
        This method is called when the summit has been running on UPS
        power for a while and power has not been restored.  Effect an
        orderly shutdown.  upstime will be given the floating point time
        of when the power went out.
        """
        res = 1
        try:
            self.logger.info("!!! POWERING DOWN !!!")
            #res = os.system('/usr/sbin/shutdown -h 60')

        except OSError, e:
            self.logger.error("Error issuing shutdown: %s" % str(e))

        self.stop()
            
        self.ocs.shutdown(res)

    
#END AO188.py

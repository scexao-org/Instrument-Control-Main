#
# SIMCAM.py -- native SIMCAM personality for SIMCAM instrument simulator
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Sun Sep 14 18:53:30 HST 2008
#  Modified by Yosuke Minowa for LGS
#  Last edit: Apr 1 02:17 HST 2011  
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
import math

# Value to return for executing unimplemented command.
# 0: OK, non-zero: error
unimplemented_res = 0


class LGSError(CamCommandError):
    pass

class LGS(BASECAM):

    def __init__(self, logger, env, ev_quit=None):

        super(LGS, self).__init__()
        
        self.logger = logger
        self.env = env
        # Convoluted but sure way of getting this module's directory
        self.mydir = os.path.split(sys.modules[__name__].__file__)[0]

        if not ev_quit:
            self.ev_quit = threading.Event()
        else:
            self.ev_quit = ev_quit

        self.ocs = None
        self.mystatus = None
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
        super(LGS, self).initialize(ocsint)
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
        self.server = {'llt':{'host':'10.0.0.3','port':18824},\
                       'rtscom':{'host':'10.0.0.3','port':25010}}

        # Used to format status buffer (item lengths must match definitions
        # of status aliases on SOSS side in $OSS_SYSTEM/StatusAlias.pro)

        ##### Status for slow update (statfmt1) #####
        # SIMCAM status 
        statfmt = "%(status)-8.8s,"
        # 589 laser
        statfmt = statfmt + "%(laser_state)-12.12s,"
        statfmt = statfmt + "%(laser_1064_chl)-12.12s,%(laser_1319_chl)-12.12s,"
        statfmt = statfmt + "%(laser_1064_rfp)-12.12s,%(laser_1319_rfp)-12.12s,"
        statfmt = statfmt + "%(laser_1064_ldc)6.2f,%(laser_1064_ldpws)-12.12s,"
        statfmt = statfmt + "%(laser_1319_ldc)6.2f,%(laser_1319_ldpws)-12.12s,"
        statfmt = statfmt + "%(laser_1064_shutter)-12.12s,%(laser_1319_shutter)-12.12s,"
        statfmt = statfmt + "%(laser_589_shutter)-12.12s,"
        statfmt = statfmt + "%(laser_sfgcstl_tctl)-12.12s,"
        statfmt = statfmt + "%(laser_sfgcstl_stmp)6.2f,%(laser_sfgcstl_tmp)6.2f,"
        statfmt = statfmt + "%(laser_1064_etl_tctl)-12.12s,"
        statfmt = statfmt + "%(laser_1064_etl_stmp)6.2f,%(laser_1064_etl_tmp)6.2f,"
        statfmt = statfmt + "%(laser_1319_etl_tctl)-12.12s,"
        statfmt = statfmt + "%(laser_1319_etl_stmp)6.2f,%(laser_1319_etl_tmp)6.2f,"
        statfmt = statfmt + "%(laser_lhead_tmp)6.2f,"
        statfmt = statfmt + "%(laser_lencl_tmp1)6.2f,%(laser_lencl_tmp2)6.2f,%(laser_lencl_tmp3)6.2f,"
        statfmt = statfmt + "%(laser_1064_pwr)6.2f,%(laser_1319_pwr)6.2f,%(laser_589_pwr)6.2f,"
        statfmt = statfmt + "%(laser_ml_drv_freq)8.4f,%(laser_ml_drv_phase)6.2f,%(laser_rep_rate)8.4f,"
        statfmt = statfmt + "%(laser_pcu_stat)-16.16s,%(laser_rcu_stat)-16.16s,"
        # Diagnostic system
        statfmt = statfmt + "%(lds_hwp1_pos)6.1f,%(lds_hwp1_step)8d,"
        statfmt = statfmt + "%(lds_hwp2_pos)6.1f,%(lds_hwp2_step)8d,"
        statfmt = statfmt + "%(lds_hwp3_pos)6.1f,%(lds_hwp3_step)8d,"
        statfmt = statfmt + "%(lds_qwp_pos)6.1f,%(lds_qwp_step)8d,"
        statfmt = statfmt + "%(lds_sodcell)6.3f,%(lds_sodcell_pmtg)6.3f,%(lds_sodcell_tmp)6.1f,"
        # Fiber coupling
        statfmt = statfmt + "%(fiber_id)8d,"
        statfmt = statfmt + "%(fiber_cplens_pos_x)9.2f,%(fiber_cplens_pos_y)9.2f,%(fiber_cplens_pos_z)9.2f,"
        statfmt = statfmt + "%(fiber_fibhold_pos_x)9.2f,%(fiber_fibhold_pos_y)9.2f,%(fiber_fibhold_pos_z)9.2f,"
        statfmt = statfmt + "%(fiber_retpwr)6.2f,%(fiber_retpwr_range)4d,"
        statfmt = statfmt + "%(fiber_throughput)6.2f,"
        # Laser room
        statfmt = statfmt + "%(lsroom_state)-12.12s,"
        statfmt = statfmt + "%(lsroom_stmp)6.2f,"
        statfmt = statfmt + "%(lsroom_1064_hefan)-12.12s,%(lsroom_1319_hefan)-12.12s,%(lsroom_roof_hefan)-12.12s,"
        statfmt = statfmt + "%(lsroom_valv_stat_h)-12.12s,%(lsroom_valv_stat_l)-12.12s,"
        statfmt = statfmt + "%(lsroom_col_flwrate)6.2f,"
        statfmt = statfmt + "%(lsroom_lcr_hum)6.2f,"
        statfmt = statfmt + "%(lsroom_lcr_tmp1)6.2f,%(lsroom_lcr_tmp2)6.2f,%(lsroom_lcr_tmp3)6.2f,"
        statfmt = statfmt + "%(lsroom_lcr_tmp4)6.2f,%(lsroom_lcr_tmp5)6.2f,"
        statfmt = statfmt + "%(lsroom_ctr_tmp1)6.2f,%(lsroom_ctr_tmp2)6.2f,%(lsroom_ctr_tmp3)6.2f,"
        statfmt = statfmt + "%(lsroom_ctr_tmp4)6.2f,%(lsroom_ctr_tmp5)6.2f,"
        # LLT
        statfmt = statfmt + "%(llt_launch_state)-12.12s,"
        statfmt = statfmt + "%(llt_collens_x_pos)10.3f,%(llt_collens_x_step)8d,"
        statfmt = statfmt + "%(llt_collens_y_pos)10.3f,%(llt_collens_y_step)8d,"
        statfmt = statfmt + "%(llt_collens_z_pos)10.3f,%(llt_collens_z_step)8d,"
        statfmt = statfmt + "%(llt_m3_x_pos)10.3f,%(llt_m3_x_step)8d,"
        statfmt = statfmt + "%(llt_m3_z_pos)10.3f,%(llt_m3_z_step)8d,"
        statfmt = statfmt + "%(llt_laser_pwr)6.2f,"
        statfmt = statfmt + "%(llt_tmp_opt)6.2f,%(llt_tmp_ir)6.2f,"
        statfmt = statfmt + "%(llt_tmp_front)6.2f,%(llt_tmp_rear)6.2f,"
        statfmt = statfmt + "%(llt_shut)-12.12s,%(llt_cover)-12.12s,"
        # Safety
        statfmt = statfmt + "%(emgshut_stat_e)-12.12s,%(emgshut_stat_w)-12.12s,%(emgshut_stat_c)-12.12s,"
        # LTCS
        statfmt = statfmt + "%(ltcs_policy)-12.12s,%(ltcs_shut_stat)-12.12s,"
        statfmt = statfmt + "%(ltcs_laser_stat)-12.12s,%(ltcs_telcol_stat)-12.12s,%(ltcs_satcol_stat)-12.12s,"
        statfmt = statfmt + "%(ltcs_telcol_twin)8d,%(ltcs_satcol_twin)8d"
        
        # Get our 3 letter instrument code and full instrument name
        self.inscode = self.insconfig.getCodeByNumber(self.obcpnum)
        self.insname = self.insconfig.getNameByNumber(self.obcpnum)
        
        # table name
        tblName = 'LGSS0001' 

        self.mystatus = self.ocs.addStatusTable(tblName,
                                                ['status',
                                                 'laser_state',
                                                 'laser_1064_chl','laser_1319_chl',
                                                 'laser_1064_rfp','laser_1319_rfp',
                                                 'laser_1064_ldc','laser_1064_ldpws',
                                                 'laser_1319_ldc','laser_1319_ldpws',
                                                 'laser_1064_shutter','laser_1319_shutter',
                                                 'laser_589_shutter',
                                                 'laser_sfgcstl_tctl',
                                                 'laser_sfgcstl_stmp','laser_sfgcstl_tmp',
                                                 'laser_1064_etl_tctl',
                                                 'laser_1064_etl_stmp','laser_1064_etl_tmp',
                                                 'laser_1319_etl_tctl',
                                                 'laser_1319_etl_stmp','laser_1319_etl_tmp',
                                                 'laser_lhead_tmp',
                                                 'laser_lencl_tmp1','laser_lencl_tmp2','laser_lencl_tmp3',
                                                 'laser_1064_pwr','laser_1319_pwr','laser_589_pwr',
                                                 'laser_ml_drv_freq','laser_ml_drv_phase','laser_rep_rate',
                                                 'laser_pcu_stat','laser_rcu_stat',
                                                 'lds_hwp1_pos','lds_hwp1_step',
                                                 'lds_hwp2_pos','lds_hwp2_step',
                                                 'lds_hwp3_pos','lds_hwp3_step',
                                                 'lds_qwp_pos','lds_qwp_step',
                                                 'lds_sodcell','lds_sodcell_pmtg','lds_sodcell_tmp',
                                                 'fiber_id',
                                                 'fiber_cplens_pos_x','fiber_cplens_pos_y','fiber_cplens_pos_z',
                                                 'fiber_fibhold_pos_x','fiber_fibhold_pos_y','fiber_fibhold_pos_z',
                                                 'fiber_retpwr','fiber_retpwr_range',
                                                 'fiber_throughput',
                                                 'lsroom_state',
                                                 'lsroom_stmp',
                                                 'lsroom_1064_hefan','lsroom_1319_hefan','lsroom_roof_hefan',
                                                 'lsroom_valv_stat_h','lsroom_valv_stat_l',
                                                 'lsroom_col_flwrate',
                                                 'lsroom_lcr_hum',
                                                 'lsroom_lcr_tmp1','lsroom_lcr_tmp2','lsroom_lcr_tmp3',
                                                 'lsroom_lcr_tmp4','lsroom_lcr_tmp5',
                                                 'lsroom_ctr_tmp1','lsroom_ctr_tmp2','lsroom_ctr_tmp3',
                                                 'lsroom_ctr_tmp4','lsroom_ctr_tmp5',
                                                 'llt_launch_state',
                                                 'llt_collens_x_pos','llt_collens_x_step',
                                                 'llt_collens_y_pos','llt_collens_y_step',
                                                 'llt_collens_z_pos','llt_collens_z_step',
                                                 'llt_m3_x_pos','llt_m3_x_step',
                                                 'llt_m3_z_pos','llt_m3_z_step',
                                                 'llt_laser_pwr',
                                                 'llt_tmp_opt','llt_tmp_ir',
                                                 'llt_tmp_front','llt_tmp_rear',
                                                 'llt_shut','llt_cover',
                                                 'emgshut_stat_e','emgshut_stat_w','emgshut_stat_c',
                                                 'ltcs_policy','ltcs_shut_stat',
                                                 'ltcs_laser_stat','ltcs_telcol_stat','ltcs_satcol_stat',
                                                 'ltcs_telcol_twin','ltcs_satcol_twin'
                                                 ],
                                                formatStr=statfmt)
        
        # Establish initial status values
        self.mystatus.setvals(status='ALIVE')
        self.get_589laser_stat()
        self.get_diag_stat()
        self.get_fiber_coupling_stat()
        self.get_laser_room_stat()
        self.get_llt_stat()
        self.get_emgshut_stat()
        self.get_ltcs_stat()
        
        # Handles to periodic tasks
        self.status_task = None
        self.power_task = None

        # Lock for handling mutual exclusion
        self.lock = threading.RLock()


    def start(self, wait=True):
        super(LGS, self).start(wait=wait)
        
        self.logger.info('LGS STARTED.')

        # Start auto-generation of status task
        t1 = common.IntervalTask(self.put_status, 10.0)
        self.status_task = t1
        t1.init_and_start(self)

        # Start task to monitor summit power.  Call self.power_off
        # when we've been running on UPS power for 60 seconds
        t = common.PowerMonTask(self, self.power_off, upstime=60.0)
        self.power_task = t
        # power monitor is not implemented (YM)
        #t.init_and_start(self) 


    def stop(self, wait=True):
        super(LGS, self).stop(wait=wait)
        
        # Terminate status generation task
        if self.status_task != None:
            self.status_task.stop()

        self.status_task = None

        # Terminate power check task
        if self.power_task != None:
            self.power_task.stop()

        self.power_task = None

        self.logger.info("LGS STOPPED.")


    ####################
    # INTERNAL METHODS #
    ####################

    ### Send command to ao188 servers ###
    def LGSSendCmd (self, server, cmd):

        # convert string to lower case
        server = server.lower()
        cmd = cmd.lower()

        # get server host and port
        if self.server.has_key(server):
            host = self.server[server]['host']
            port = self.server[server]['port']
        else:
            raise LGSError("Error: unknown server name %s" % server)
        
        #Open socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(120)
        except socket.error, msg:
            sock.close()
            raise LGSError(msg[1])
        
        try:
            sock.connect ((host, port))
        except socket.error, msg:
            sock.close()
            raise LGSError(msg[1])
          
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
            raise LGSError(retstr[:-2])

    ### Send command to ao188 servers and receive return string ###
    def LGSSendCmdRecv (self, server, cmd):

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


    ### Execute command in LGS ###
    def LGSExecCmd (self, cmd):

        # convert string to lower case
        cmd = cmd.lower()

        # execute command
        proc = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
        ret = proc.stdout.read()
        if ret != "" :
            raise LGSError("Error: %s" % str(ret))
        
        
    ### Execute command in LGS and receive return string ###
    def LGSExecCmdRecv (self, cmd):

        # convert string to lower case
        if cmd.find("imr") < 0:
            cmd = cmd.lower()

        # execute command
        proc = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        err = proc.stderr.read()
        if err != "" :
            raise LGSError("Error: %s" % str(err))

        ret = proc.stdout.read()
        
        return ret

    ####################################
    ###  Commands for getting status ###
    ####################################

    ### 589 laser status ###
    def get_589laser_stat(self):

        # initialize status
        laser_state = 'UNKNOWN'         # Laser generation status (EMIT/SHUTTERED/OFF)
        laser_1064_chl = 'UNKNOWN'      # Power status of chiller for YAG1064
        laser_1319_chl = 'UNKNOWN'      # Power status of chiller for YAG1319
        laser_1064_rfp = 'UNKNOWN'      # Power status of RF mode-locker for YAG1064
        laser_1319_rfp = 'UNKNOWN'      # Power status of RF mode-locker for YAG1319
        laser_1064_ldc = -99.99         # LD Current setting for YAG1064 (A)
        laser_1064_ldpws = 'UNKNOWN'    # Status of LD power supply for YAG1064 (ON/OFF)
        laser_1319_ldc = -99.99         # LD Current setting for YAG1319 (A)
        laser_1319_ldpws = 'UNKNOWN'    # Status of LD power supply for YAG1319 (ON/OFF)
        laser_1064_shutter = 'UNKNOWN'  # Shutter status of YAG1064 (OPEN/CLOSE)
        laser_1319_shutter = 'UNKNOWN'  # Shutter status of YAG1319 (OPEN/CLOSE)
        laser_589_shutter = 'UNKNOWN'   # Shutter status of SFG589 (OPEN/CLOSE)
        laser_sfgcstl_tctl = 'UNKNOWN'  # Control status of SFG crystal temperature (ON/OFF)
        laser_sfgcstl_stmp = -99.99     # Temperature setting of SFG crystal (degC)
        laser_sfgcstl_tmp = -99.99      # Temperature of SFG crystal (degC)
        laser_1064_etl_tctl = 'UNKNOWN' # Control status of YAG1064 etalon temperature (ON/OFF)
        laser_1064_etl_stmp = -99.99    # Temperature setting of YAG1064 etalon (degC)
        laser_1064_etl_tmp = -99.99     # Temperature of YAG1064 etalon (degC)
        laser_1319_etl_tctl = 'UNKNOWN' # Control status of YAG1319 etalon temperature (ON/OFF)
        laser_1319_etl_stmp = -99.99    # Temperature setting of YAG1319 etalon (degC)
        laser_1319_etl_tmp = -99.99     # Temperature of YAG1319 etalon (degC)
        laser_lhead_tmp	= -99.99        # Temperature of SFG Laser head (degC)
        laser_lencl_tmp1 = -99.99      # Temperature of SFG Laser enclosure #1 (degC)
        laser_lencl_tmp2 = -99.99      # Temperature of SFG Laser enclosure #2 (degC)
        laser_lencl_tmp3 = -99.99      # Temperature of SFG Laser enclosure #3 (degC)
        laser_1064_pwr = -99.99       # Output power of YAG1064 (W)
        laser_1319_pwr = -99.99       # Output power of YAG1319 (W)
        laser_589_pwr	= -99.99        # Output power of SFG589 (W) 
        laser_ml_drv_freq = -9.9999     # Frequency of Mode-lock driver (MHz)
        laser_ml_drv_phase = -99.99     # Differential phase of Mode-lock driver (deg)
        laser_rep_rate = -9.9999        # Repetition rate of SFG589 laser (MHz)
        laser_pcu_stat = 'UNKNOWN'    # Status of power control unit
        laser_rcu_stat = 'UNKNOWN'    # Status of remote control unit

        # check laser status
        if laser_1064_ldpws.lower() == 'off' and laser_1319_ldpws.lower() == 'off':
            laser_state = 'OFF'
        elif laser_1064_ldpws.lower() == 'unknown' or laser_1319_ldpws.lower() == 'unknown' :
            if laser_1064_shutter.lower() == 'close' and laser_1319_shutter.lower() == 'close' :
                laser_state = 'SHUTTERED'
            else :
                if laser_589_shutter.lower() == 'close':
                    laser_state = 'SHUTTERED'
                else :
                    laser_state = 'UNKNOWN'
        else :
            if laser_1064_shutter.lower() == 'close' and laser_1319_shutter.lower() == 'close' :
                laser_state = 'SHUTTERED'
            elif laser_1064_shutter.lower() == 'unknown' or laser_1319_shutter.lower() == 'unknown' :
                if laser_589_shutter.lower() == 'close' :
                    laser_state = 'SHUTTERED'
                else :
                    laser_state = 'UNKNOWN'
            else :
                if laser_589_shutter.lower() == 'close' :
                    laser_state = 'SHUTTERED'
                elif laser_589_shutter.lower() == 'open' :
                    laser_state = 'EMIT'
                else:
                    laser_state = 'UNKNOWN'


        # check power control unit status
        if laser_pcu_stat == '0000':
            laser_pcu_stat = 'NORMAL'
        else :
            #laser_pcu_stat = 'ERROR(%s)' % (str(laser_pcu_stat))
            laser_pcu_stat = 'UNKNOWN'

        # check remote control unit status
        if laser_rcu_stat == '0000':
            laser_rcu_stat = 'NORMAL'
        else :
            #laser_rcu_stat = 'ERROR(%s)' % (str(laser_pcu_stat))
            laser_rcu_stat = 'UNKNOWN'

        # register status values
        self.mystatus['laser_state'] = laser_state
        self.mystatus['laser_1064_chl'] = laser_1064_chl
        self.mystatus['laser_1319_chl'] = laser_1319_chl
        self.mystatus['laser_1064_rfp'] = laser_1064_rfp
        self.mystatus['laser_1319_rfp'] = laser_1319_rfp
        self.mystatus['laser_1064_ldc'] = laser_1064_ldc
        self.mystatus['laser_1064_ldpws'] = laser_1064_ldpws
        self.mystatus['laser_1319_ldc'] = laser_1319_ldc
        self.mystatus['laser_1319_ldpws'] = laser_1319_ldpws
        self.mystatus['laser_1064_shutter'] = laser_1064_shutter
        self.mystatus['laser_1319_shutter'] = laser_1319_shutter
        self.mystatus['laser_589_shutter'] = laser_589_shutter
        self.mystatus['laser_sfgcstl_tctl'] = laser_sfgcstl_tctl
        self.mystatus['laser_sfgcstl_stmp'] = laser_sfgcstl_stmp
        self.mystatus['laser_sfgcstl_tmp'] = laser_sfgcstl_tmp
        self.mystatus['laser_1064_etl_tctl'] = laser_1064_etl_tctl
        self.mystatus['laser_1064_etl_stmp'] = laser_1064_etl_stmp
        self.mystatus['laser_1064_etl_tmp'] = laser_1064_etl_tmp
        self.mystatus['laser_1319_etl_tctl'] = laser_1319_etl_tctl
        self.mystatus['laser_1319_etl_stmp'] = laser_1319_etl_stmp
        self.mystatus['laser_1319_etl_tmp'] = laser_1319_etl_tmp
        self.mystatus['laser_lhead_tmp'] = laser_lhead_tmp
        self.mystatus['laser_lencl_tmp1'] = laser_lencl_tmp1
        self.mystatus['laser_lencl_tmp2'] = laser_lencl_tmp2
        self.mystatus['laser_lencl_tmp3'] = laser_lencl_tmp3
        self.mystatus['laser_1064_pwr'] = laser_1064_pwr
        self.mystatus['laser_1319_pwr'] = laser_1319_pwr
        self.mystatus['laser_589_pwr'] = laser_589_pwr
        self.mystatus['laser_ml_drv_freq'] = laser_ml_drv_freq
        self.mystatus['laser_ml_drv_phase'] = laser_ml_drv_phase
        self.mystatus['laser_rep_rate'] = laser_rep_rate
        self.mystatus['laser_pcu_stat'] = laser_pcu_stat
        self.mystatus['laser_rcu_stat'] = laser_rcu_stat
        
        
    ### Get laser diagnostic system status ###
    def get_diag_stat(self):

        # initialize status
        lds_hwp1_pos = -99.9	  # Stage position of 1/2 waveplate #1 (deg)
        lds_hwp1_step = -99999    # Stage position of 1/2 waveplate #1 (microstep)
        lds_hwp2_pos = -99.9	  # Stage position of 1/2 waveplate #2 (deg)
        lds_hwp2_step = -99999    # Stage position of 1/2 waveplate #2 (microstep)
        lds_hwp3_pos = -99.9	  # Stage position of 1/2 waveplate #3 (deg)
        lds_hwp3_step = -99999    # Stage position of 1/2 waveplate #3 (microstep)
        lds_qwp_pos = -99.9	  # Stage position of 1/4 waveplate (deg)
        lds_qwp_step = -99999	  # Stage position of 1/4 waveplate (microstep)
        lds_sodcell = -9.999      # Brightness of Sodium gas cell
        lds_sodcell_pmtg = -9.999 # Gain of PMT for Sodium gas cell
        lds_sodcell_tmp = -99.9  # Temperature of Sodium gas cell

        # register status values
        self.mystatus['lds_hwp1_pos'] = lds_hwp1_pos
        self.mystatus['lds_hwp1_step'] = lds_hwp1_step
        self.mystatus['lds_hwp2_pos'] = lds_hwp2_pos
        self.mystatus['lds_hwp2_step'] = lds_hwp2_step
        self.mystatus['lds_hwp3_pos'] = lds_hwp3_pos
        self.mystatus['lds_hwp3_step'] = lds_hwp3_step
        self.mystatus['lds_qwp_pos'] = lds_qwp_pos
        self.mystatus['lds_qwp_step'] = lds_qwp_step
        self.mystatus['lds_sodcell'] = lds_sodcell
        self.mystatus['lds_sodcell_pmtg'] = lds_sodcell_pmtg
        self.mystatus['lds_sodcell_tmp'] = lds_sodcell_tmp
         
    ### Get Fiber coupling status ###
    def get_fiber_coupling_stat(self):

        # initialize status
        fiber_id = -99999  # ID of Laser Fiber
        fiber_cplens_pos_x = -9999.99   # Stage position of coupling lens in X (um)
        fiber_cplens_pos_y = -9999.99   # Stage position of coupling lens in Y (um)
        fiber_cplens_pos_z = -9999.99   # Stage position of coupling lens in Z (um)
        fiber_fibhold_pos_x = -9999.99  # Stage position of fiber holder in X (um)
        fiber_fibhold_pos_y = -9999.99  # Stage position of fiber holder in Y (um)
        fiber_fibhold_pos_z = -9999.99  # Stage position of fiber holder in Z (um)
        fiber_retpwr = -9.99         # Power returned from LLT throught relay fiber
        fiber_retpwr_range = -99     # Gain range of returned power
        fiber_throughput = -9.99        # Overall throughput of relay fiber (%)

        # register status values 
        self.mystatus['fiber_id'] = fiber_id
        self.mystatus['fiber_cplens_pos_x'] = fiber_cplens_pos_x
        self.mystatus['fiber_cplens_pos_y'] = fiber_cplens_pos_y
        self.mystatus['fiber_cplens_pos_z'] = fiber_cplens_pos_z
        self.mystatus['fiber_fibhold_pos_x'] = fiber_fibhold_pos_x
        self.mystatus['fiber_fibhold_pos_y'] = fiber_fibhold_pos_y
        self.mystatus['fiber_fibhold_pos_z'] = fiber_fibhold_pos_z
        self.mystatus['fiber_retpwr'] = fiber_retpwr
        self.mystatus['fiber_retpwr_range'] = fiber_retpwr_range
        self.mystatus['fiber_throughput'] = fiber_throughput

    ### Get laser room status ###
    def get_laser_room_stat(self):

        # initial parameter
        lsroom_state = 'UNKNOWN'         # Laser room status (NORMAL/ABNORMAL)
        lsroom_stmp = -99.99             # Temperature setting for laser room (degC)
        lsroom_1064_hefan = 'UNKNOWN'    # Status of heat exchanger fan for YAG1064 chiller (ON/OFF)
        lsroom_1319_hefan = 'UNKNOWN'    # Status of heat exchanger fan for YAG1319 chiller (ON/OFF)
        lsroom_roof_hefan = 'UNKNOWN'    # Status of heat exchanger fan at the roof of laser room (ON/OFF)
        lsroom_valv_stat_h = 'UNKNOWN'   # Status of solenoid valve for high flow rate (ON/OFF)
        lsroom_valv_stat_l = 'UNKNOWN'   # Status of solenoid valve for low flow rate (ON/OFF)
        lsroom_col_flwrate = -99.99      # Flow rate of coolant of telescope chiller (l/min)
        lsroom_lcr_hum = -99.99          # Humidity in laser clearn room (%)
        lsroom_lcr_tmp1 = -99.99         # Temperature in laser clean room #1 (degC)
        lsroom_lcr_tmp2 = -99.99         # Temperature in laser clean room #2 (degC)
        lsroom_lcr_tmp3 = -99.99         # Temperature in laser clean room #3 (degC)
        lsroom_lcr_tmp4 = -99.99         # Temperature in laser clean room #4 (degC)
        lsroom_lcr_tmp5 = -99.99         # Temperature in laser clean room #5 (degC)
        lsroom_ctr_tmp1 = -99.99         # Temperature in laser control room #1 (degC)
        lsroom_ctr_tmp2 = -99.99         # Temperature in laser control room #2 (degC)
        lsroom_ctr_tmp3 = -99.99         # Temperature in laser control room #3 (degC)
        lsroom_ctr_tmp4 = -99.99         # Temperature in laser control room #4 (degC)
        lsroom_ctr_tmp5 = -99.99         # Temperature in laser control room #5 (degC) <-- LD drive cable

        
        #if lsroom_1064_hefan.lower() == 'on' and lsroom_1319_hefan.lower() == 'on' and \
        #   lsroom_roof_hefan.lower() == 'on' and lsroom_valv_stat_h.lower() == 'on' and \
        #   lsroom_valv_stat_l.lower() == 'on':
        #    # check temperateure range
        #    # (normal range: 5<T<65 for LD drive cable, 5 < T <30 for others)
        #    lsroom_state = 'NORMAL'
        #else :
        #    lsroom_state = 'ABNORMAL'
        
        
        # register status values 
        self.mystatus['lsroom_state'] = lsroom_state
        self.mystatus['lsroom_stmp'] = lsroom_stmp
        self.mystatus['lsroom_1064_hefan'] = lsroom_1064_hefan
        self.mystatus['lsroom_1319_hefan'] = lsroom_1319_hefan
        self.mystatus['lsroom_roof_hefan'] = lsroom_roof_hefan
        self.mystatus['lsroom_valv_stat_h'] = lsroom_valv_stat_h
        self.mystatus['lsroom_valv_stat_l'] = lsroom_valv_stat_l
        self.mystatus['lsroom_col_flwrate'] = lsroom_col_flwrate
        self.mystatus['lsroom_lcr_hum'] = lsroom_lcr_hum
        self.mystatus['lsroom_lcr_tmp1'] = lsroom_lcr_tmp1
        self.mystatus['lsroom_lcr_tmp2'] = lsroom_lcr_tmp2
        self.mystatus['lsroom_lcr_tmp3'] = lsroom_lcr_tmp3
        self.mystatus['lsroom_lcr_tmp4'] = lsroom_lcr_tmp4
        self.mystatus['lsroom_lcr_tmp5'] = lsroom_lcr_tmp5
        self.mystatus['lsroom_ctr_tmp1'] = lsroom_ctr_tmp1
        self.mystatus['lsroom_ctr_tmp2'] = lsroom_ctr_tmp2
        self.mystatus['lsroom_ctr_tmp3'] = lsroom_ctr_tmp3
        self.mystatus['lsroom_ctr_tmp4'] = lsroom_ctr_tmp4
        self.mystatus['lsroom_ctr_tmp5'] = lsroom_ctr_tmp5
        
    ### Get LLT status ###
    def get_llt_stat(self):

        # initialize parameters
        llt_launch_state = 'UNKNOWN'  # Laser launching status (ON/OFF)
        llt_collens_x_pos = -999.999 # Stage position of collimator lens in X (um) 
        llt_collens_x_step = -999999 # Stage position of collimator lens in X (microstep)
        llt_collens_y_pos = -999.999 # Stage position of collimator lens in Y (um) 
        llt_collens_y_step = -999999 # Stage position of collimator lens in Y (microstep) 
        llt_collens_z_pos = -999.999 # Stage position of collimator lens in Z (um)
        llt_collens_z_step = -999999 # Stage position of collimator lens in Z (microstep) 
        llt_m3_x_pos = -999.999       # Stage position of M3 in X (um)
        llt_m3_x_step = -999999       # Stage position of M3 in X (microstep)
        llt_m3_z_pos = -999.999       # Stage position of M3 in Z (um)
        llt_m3_z_step = -999999       # Stage position of M3 in Z (microstep)
        llt_laser_pwr = -99.99        # Laser power at LLT (Watt)
        llt_tmp_opt = -99.99          # Temperature at OPT side (degC)
        llt_tmp_ir = -99.99           # Temperature at IR side (degC)
        llt_tmp_front = -99.99        # Temperature at FRONT side (degC)
        llt_tmp_rear = -99.99         # Temperature at REAR side (degC)
        llt_shut = 'UNKNOWN'          # Shutter status (OPEN/CLOSE)
        llt_cover = 'UNKNOWN'         # Cover status (OPEN/CLOSE)

        # get llt stage status
        ret = self.LGSSendCmdRecv("llt", "llt st\r")

        # split status line into array
        r = re.compile('[\s=:\(\)\n\[\],]+')
        param = r.split(ret)

        # parse status array
        for item in range(len(param)):
            if param[item] == "L1":
                if param[item+1] == "X-stage":
                    if isfloat(param[item+3]):
                        llt_collens_x_pos = float(param[item+3])
                    if isfloat(param[item+5]):
                        llt_collens_x_step = int(param[item+5])
                elif param[item+1] == "Y-stage":
                    if isfloat(param[item+3]):
                        llt_collens_y_pos = float(param[item+3])
                    if isfloat(param[item+5]):
                        llt_collens_y_step = int(param[item+5])
                elif param[item+1] == "Z-stage":
                    if isfloat(param[item+3]):
                        llt_collens_z_pos = float(param[item+3])
                    if isfloat(param[item+5]):
                        llt_collens_z_step = int(param[item+5])
            elif param[item] == "M3":
                if param[item+1] == "X-stage":
                    if isfloat(param[item+3]):
                        llt_m3_x_pos = float(param[item+3])
                    if isfloat(param[item+5]):
                        llt_m3_x_step = int(param[item+5])
                elif param[item+1] == "Y-stage": # this should be Z-stage (server status is wrong?)
                    if isfloat(param[item+3]):
                        llt_m3_z_pos = float(param[item+3])
                    if isfloat(param[item+5]):
                        llt_m3_z_step = int(param[item+5])
        
        # get llt power status (for LLT shutter)
        ret = self.LGSSendCmdRecv("llt", "llt_nps st\r")
        
        # split status line into array
        r = re.compile('[\s=:\(\)\n\[\],]+')
        param = r.split(ret)

        for item in range(len(param)):
            if param[item] == "2":
                if param[item+1] == "Shutter":
                    if param[item+2] == "OFF":
                        llt_shut = "CLOSE"
                    elif param[item+2] == "ON":
                        llt_shut = "OPEN"
                    else :
                        llt_shut = "UNKNOWN"

        # register status values
        self.mystatus['llt_launch_state'] = llt_launch_state
        self.mystatus['llt_collens_x_pos'] = llt_collens_x_pos
        self.mystatus['llt_collens_x_step'] = llt_collens_x_step
        self.mystatus['llt_collens_y_pos'] = llt_collens_y_pos
        self.mystatus['llt_collens_y_step'] = llt_collens_y_step
        self.mystatus['llt_collens_z_pos'] = llt_collens_z_pos
        self.mystatus['llt_collens_z_step'] = llt_collens_z_step
        self.mystatus['llt_m3_x_pos'] = llt_m3_x_pos
        self.mystatus['llt_m3_x_step'] = llt_m3_x_step
        self.mystatus['llt_m3_z_pos'] = llt_m3_z_pos
        self.mystatus['llt_m3_z_step'] = llt_m3_z_step
        self.mystatus['llt_laser_pwr'] = llt_laser_pwr
        self.mystatus['llt_tmp_opt'] = llt_tmp_opt
        self.mystatus['llt_tmp_ir'] = llt_tmp_ir
        self.mystatus['llt_tmp_front'] = llt_tmp_front
        self.mystatus['llt_tmp_rear'] = llt_tmp_rear
        self.mystatus['llt_shut'] = llt_shut
        self.mystatus['llt_cover'] = llt_cover
        

    def get_emgshut_stat(self):

        # initialize parameters 
        emgshut_stat_e = 'UNKNOWN'   # Status of emergency shutter at East side (ON/OFF)
        emgshut_stat_w = 'UNKNOWN'   # Status of emergency shutter at West side (ON/OFF)
        emgshut_stat_c = 'UNKNOWN'   # Status of emergency shutter in telescope control room (ON/OFF)

        # register status values 
        self.mystatus['emgshut_stat_e'] = emgshut_stat_e
        self.mystatus['emgshut_stat_w'] = emgshut_stat_w
        self.mystatus['emgshut_stat_c'] = emgshut_stat_c
             

    def get_ltcs_stat(self):

        # initialize parameters
        ltcs_policy =  'UNKNOWN'     # Policy of laser traffic control system (FirstON/Classical)
        ltcs_shut_stat = 'UNKNOWN'   # Status of shuttering (OPEN/CLOSE)
        ltcs_laser_stat = 'UNKNOWN'  # Status of laser propagation (ONSKY/ON/OFF)
        ltcs_telcol_stat = 'UNKNOWN' # LTCS Status of collision with telescopes
        ltcs_satcol_stat = 'UNKNOWN' # Status of collision with satellite
        ltcs_telcol_twin = -999999   # Remaining open time window until telescope collision (sec)
        ltcs_satcol_twin = -999999   # Remaining open time window until satellite collision (sec)

        # register status values
        self.mystatus['ltcs_policy'] = ltcs_policy
        self.mystatus['ltcs_shut_stat'] = ltcs_shut_stat
        self.mystatus['ltcs_laser_stat'] = ltcs_laser_stat
        self.mystatus['ltcs_telcol_stat'] = ltcs_telcol_stat
        self.mystatus['ltcs_satcol_stat'] = ltcs_satcol_stat
        self.mystatus['ltcs_telcol_twin'] = ltcs_telcol_twin
        self.mystatus['ltcs_satcol_twin'] = ltcs_satcol_twin


    #######################
    # INSTRUMENT COMMANDS #
    #######################

    # moving LLT stage and shutter
    def llt(self,dev='NOP', cmd='NOP', val=0.0, server='NOP'):

        # check device and execute command
        if dev == None:
            # get current Az/EL
            try:
                statusDict = {'TSCS.AZ': 'NOP', 'TSCS.EL': 'NOP'}
                self.ocs.requestOCSstatus(statusDict)
                az = statusDict['TSCS.AZ']
                el = statusDict['TSCS.EL']
                self.logger.info("AZ = %s , EL = %s" % (str(az), str(el)))
            except Exception, e:
                raise LGSError("Error getting Az/EL status: %s" % str(e))

            # check Az/El values
            if isfloat(az) == False or isfloat(el) == False:
                raise LGSrror("Error in Az/El values: (%s,%s)" % (str(az),str(el)))

            # make command string
            if cmd.lower() == "steering":
                cmdstr = "llt steering %f %f\r" % (float(az), float(el))
            elif cmd.lower() == "udbase":
                # get current L1x/L1y position
                self.put_status(target="LLT")
                l1x = self.mystatus['llt_collens_x_step']
                l1y = self.mystatus['llt_collens_y_step']
                cmdstr = "llt udbase %d %d %f %f\r" % (int(l1x), int(l1y), float(az), float(el))
            else :
                raise LGSError("Error: no device selected")
        elif dev.lower() == "l1x" or dev.lower() == "l1y" or dev.lower() == "l1z"\
             or dev.lower() == "m3x" or dev.lower() == "m3z":

            # exception for l1z and m3z command 
            if dev.lower() == "l1z":
                dev = "coll"

            if dev.lower() == "m3z":
                dev = "m3y"

            # make command string 
            if cmd.lower() == "ma":
                if isfloat(val):
                    cmdstr = "llt %s ma %f\r" % (str(dev.lower()),float(val))                
            elif cmd.lower() == "mr":
                if isfloat(val):
                    cmdstr = "llt %s mr %f\r" % (str(dev.lower()),float(val))
            elif cmd.lower() == "mas":
                if isfloat(val):
                    cmdstr = "llt %s mas %d\r" % (str(dev.lower()),int(val))
            elif cmd.lower() == "mrs":
                if isfloat(val):
                    cmdstr = "llt %s mrs %d\r" % (str(dev.lower()),int(val))
            else :
                raise LGSError("Error: unknwon command (%s)" % str(cmd.lower()))
            
        elif dev.lower() == "shutter":
            # make command string
            if cmd.lower() == "open":
                cmdstr = "llt_nps on 2\r"
            elif cmd.lower() == "close":
                cmdstr = "llt_nps off 2\r"

        else :
            raise LGSError("Error: unknown device (%s)" % str(dev.lower()))

        # send command
        self.LGSSendCmd(server, cmdstr)

        # change ltcs status in case for sending shutter close command 
        if dev.lower() == "shutter" and cmd.lower() == "close":
            self.LGSExecCmd("/home/ao/ao188/bin/set_ltcs.py --laser_impacted=NO --laser_state=ON --auth=joe:bob2bob")
        
        # update status
        self.put_status(target="LLT")

    def calc_beam_angle(self, thresh):
        # get rayleigh scattered beam angle
        if float(thresh) > 0:
            ret = self.LGSSendCmdRecv("rtscom", "cntmon rayleigh %f\r" % float(thresh))
        else:
            ret = self.LGSSendCmdRecv("rtscom", "cntmon rayleigh\r")

        # split status line into array
        r = re.compile('[\s,=\(\)\n]+')
        param = r.split(ret)

        angle = -100.0
        nring = -1
        # parse status array
        for item in range(len(param)):
            if param[item] == "ANGLE":
                if isfloat(param[item+1]):
                    angle = float(param[item+1])
            elif param[item] == "Nring":
                if isfloat(param[item+1]):
                    nring = float(param[item+1])

        # store the calculated values into array 
        result = []
        result.append(angle)
        result.append(nring)

        return tuple(result)

    # LGS beam alignment 
    def beam_align(self, thresh=5.0, step=200, nstep_max=10):
        # update status
        self.put_status(target="LLT")
        #self.put_status_ao188(target="IMR")
        
        # store original position
        l1x_step_org = int(self.mystatus['llt_collens_x_step'])
        l1y_step_org = int(self.mystatus['llt_collens_y_step'])
        self.logger.info("L1X.STEP0 = %d , L1Y.STEP0 = %d" % (l1x_step_org, l1y_step_org))
        
        # get current EL and IMR angle from Status alias
        try:
            statusDict = {'TSCS.EL': 'NOP', 'AON.IMR.ANGLE': 'NOP'}
            self.ocs.requestOCSstatus(statusDict)
            el = statusDict['TSCS.EL']
            imr_ang = statusDict['AON.IMR.ANGLE']
            self.logger.info("EL = %s , IMR_ANGLE= %s" % (str(el), str(imr_ang)))
        except Exception, e:
            raise LGSError("Error getting EL and IMR angle: %s" % str(e))

        # check values
        if isfloat(el) == False or isfloat(imr_ang) == False:
            raise LGSError("Error in EL or IMR angle values: (%s,%s)" % (str(el),str(imr_ang)))

        # calculate offset angle due to EL and IMR rotation
        offset = (90.0 - float(el)) + ((2.0 * (float(imr_ang) - 90.0)) % 360.0)

        # Get initial angle of the laser beam
        angle,nring = self.calc_beam_angle(thresh)
        if angle < -99.0 or nring < 0 :
            raise LGSError("Error: failed to get beam angle")

        # assign step size for X-direction depending on the initial beam angle
        if angle == -99.0:
            dx = step
        else :
            angle0 = (angle - offset) % 360.0
            if angle0 >= 0 and angle0 < 180.0:
                dx = -1.0 * step
            else:
                dx = step

        # move L1X stage by step=dx until laser beam is detected at outer than 5th ring
        # or the number of iteration is more than nstep_max
        dx_total = 0
        nstep = 0
        while nring < 5 :
            self.llt("L1X", "MRS", dx, "LLT")
            dx_total += dx

            angle,nring = self.calc_beam_angle(thresh)
            if angle < -99.0 or nring < 0 :
                self.llt("L1X", "MAS", l1x_step_org, "LLT")
                raise LGSError("Error: failed to get beam angle")
            
            nstep += 1
            if nstep == nstep_max:
                break

        # calculate the angle correnspods to the case when EL=90deg and IMR=90deg
        if angle == -99.0 or nring < 5 :
            self.llt("L1X", "MAS", l1x_step_org, "LLT")
            raise LGSError("Error: failed to detect laser beam angle1")
        else :
            angle1 = (angle - offset) % 360.0
            self.logger.info("Angle1 = %.2f , Nring = %.1f" % (float(angle1), float(nring)))
            l1x_step1 = int(self.mystatus['llt_collens_x_step'])
            l1y_step1 = int(self.mystatus['llt_collens_y_step'])
            self.logger.info("L1X.STEP1 = %d , L1Y.STEP1 = %d" % (l1x_step1, l1y_step1))

        # assign step size, target angle, and range of overshooted angle
        # for Y-direction depending on the beam angle (angle1).
        if angle1 >= 0.0 and angle1 < 90.0 :
            dy = -1.0 * step
            target_angle = 90.0
            angle_min = 90.0
            angle_max = 180.0
        elif angle1 >= 90.0 and angle1 < 180.0 :
            dy = step
            target_angle = 90.0
            angle_min = 0.0
            angle_max = 90.0
        elif angle1 >= 180.0 and angle1 < 270.0 :
            dy = step
            target_angle = 270.0
            angle_min = 270.0
            angle_max = 360.0
        elif angle1 >= 270.0 and angle1 < 360.0 :
            dy = -1.0 * step
            target_angle = 270.0
            angle_min = 180.0
            angle_max = 270.0

        # move L1y stage until the beam angle reach in the range assigned above 
        # and the laser beam is detected outer than 5th ring. 
        # stop iteration when the number of iteration exceed more than nstep_max
        angle2 = angle1
        nstep = 0
        dy_total = 0
        while angle2 < angle_min or angle2 >= angle_max or nring < 5 :
            self.llt("L1Y", "MRS", dy, "LLT")
            dy_total += dy

            angle,nring = self.calc_beam_angle(thresh)
            if angle < -99.0 or nring < 0 :
                self.llt("L1X", "MAS", l1x_step_org, "LLT")
                self.llt("L1Y", "MAS", l1y_step_org, "LLT")
                raise LGSError("Error: failed to get beam angle")
            elif angle == -99.0 :
                angle2 = angle
            else :
                angle2 = (angle - offset) % 360.0
            
            nstep += 1
            if nstep == nstep_max:
                break

        if angle2 >= angle_min and angle2 < angle_max :
            self.logger.info("Angle2 = %.2f , Nring = %.1f" % (float(angle2), float(nring)))
            l1x_step2 = int(self.mystatus['llt_collens_x_step'])
            l1y_step2 = int(self.mystatus['llt_collens_y_step'])
            self.logger.info("L1X.STEP2 = %d , L1Y.STEP2 = %d" % (l1x_step2, l1y_step2))
        else :
            self.llt("L1X", "MAS", l1x_step_org, "LLT")
            self.llt("L1Y", "MAS", l1y_step_org, "LLT")
            raise LGSError("Error: failed to detect laser beam angle2")

        # calculate the L1y step corresponds to the target_angle 
        if(angle2 != angle1):
            if angle1 >= 0.0 and angle1 < 90.0 :
                y1 = 0
                y2 = l1y_step1 - l1y_step2
                t1 = angle1*math.pi/180.0
                t2 = (180.0-angle2)*math.pi/180.0
                y = (y1*math.tan(t1)+y2*math.tan(t2)) / (math.tan(t1)+math.tan(t2))
                l1y_step_align = l1y_step1 - y
            elif angle1 >= 90.0 and angle1 < 180.0 :
                y1 = 0
                y2 = l1y_step2 - l1y_step1
                t1 = angle2*math.pi/180.0
                t2 = (180.0-angle1)*math.pi/180.0
                y = (y1*math.tan(t1)+y2*math.tan(t2)) / (math.tan(t1)+math.tan(t2))
                l1y_step_align = l1y_step2 - y
            elif angle1 >= 180.0 and angle1 < 270.0 :
                y1 = 0
                y2 = l1y_step2 - l1y_step1
                t1 = (angle1-180.0)*math.pi/180.0
                t2 = (360.0-angle2)*math.pi/180.0
                y = (y1*math.tan(t1)+y2*math.tan(t2)) / (math.tan(t1)+math.tan(t2))
                l1y_step_align = l1y_step1 + y
            elif angle1 >= 270.0 and angle1 < 360.0 :
                y1 = 0
                y2 = l1y_step1 - l1y_step2
                t1 = (angle2-180.0)*math.pi/180.0
                t2 = (360.0-angle1)*math.pi/180.0
                y = (y1*math.tan(t1)+y2*math.tan(t2)) / (math.tan(t1)+math.tan(t2))
                l1y_step_align = l1y_step2 + y

            # record aligned position 
            self.logger.info("L1Y.ALIGN = %d" % (l1y_step_align))
        else:
            self.llt("L1X", "MAS", l1x_step_org, "LLT")
            self.llt("L1Y", "MAS", l1y_step_org, "LLT")
            raise LGSError("Error: failed to detect laser beam angle (angled did not change beween step 1 and 2)")

        # move l1y stage by -1000 step from the aligned position and calculate the beam angle
        self.llt("L1X", "MAS", l1x_step_org, "LLT")
        self.llt("L1Y", "MAS", l1y_step_align - 1000, "LLT")
        angle,nring = self.calc_beam_angle(thresh)
        if angle < -99.0 or nring < 0 :
            self.llt("L1X", "MAS", l1x_step_org, "LLT")
            self.llt("L1Y", "MAS", l1y_step_org, "LLT")
            raise LGSError("Error: failed to get beam angle")

        # move L1Y stage by -1.0*step until laser beam is detected at outer than 5th ring
        # or the number of iteration exceeds more than nstep_max
        nstep = 0
        dy = -1.0 * step
        while nring < 5 :
            self.llt("L1Y", "MRS", dy, "LLT")
 
            angle,nring = self.calc_beam_angle(thresh)
            if angle < -99.0 or nring < 0 :
                self.llt("L1X", "MAS", l1x_step_org, "LLT")
                self.llt("L1Y", "MAS", l1y_step_org, "LLT")
                raise LGSError("Error: failed to get beam angle")
            
            nstep += 1
            if nstep == nstep_max:
                break

        # calculate angle correspods to EL=90deg, IMR=90deg
        if angle == -99.0 or nring < 5:
            self.llt("L1X", "MAS", l1x_step_org, "LLT")
            self.llt("L1Y", "MAS", l1y_step_org, "LLT")
            raise LGSError("Error: failed to detect laser beam angle3")
        else :
            angle3 = (angle - offset) % 360.0
            self.logger.info("Angle3 = %.2f , Nring = %.1f" % (float(angle3), float(nring)))
            l1x_step3 = int(self.mystatus['llt_collens_x_step'])
            l1y_step3 = int(self.mystatus['llt_collens_y_step'])
            self.logger.info("L1X.STEP3 = %d , L1Y.STEP3 = %d" % (l1x_step3, l1y_step3))
            
        # assign step size, target angle, and range of overshooted angle
        # for X-direction depending on the beam angle (angle3).
        if angle3 >= 90.0 and angle3 < 180.0 :
            dx = step
            target_angle = 180.0
            angle_min = 180.0
            angle_max = 270.0
        elif angle3 >= 180.0 and angle3 < 270.0 :
            dx = -1.0 * step
            target_angle = 180.0
            angle_min = 90.0
            angle_max = 180.0
        else :
            self.llt("L1X", "MAS", l1x_step_org, "LLT")
            self.llt("L1Y", "MAS", l1y_step_org, "LLT")
            raise LGSError("Error: unexpected angle (%lf) at this step" % (float(angle3)))
        
        # move L1x stage until the beam angle reach in the range assigned above 
        # and the laser beam is detected outer than 5th ring. 
        # stop iteration when the number of iteration exceed more than nstep_max
        angle4 = angle3
        nstep = 0
        while angle4 < angle_min or angle4 >= angle_max or nring < 5:
            self.llt("L1X", "MRS", dx, "LLT")

            angle,nring = self.calc_beam_angle(thresh)
            if angle < -99.0 or nring < 0 :
                self.llt("L1X", "MAS", l1x_step_org, "LLT")
                self.llt("L1Y", "MAS", l1y_step_org, "LLT")
                raise LGSError("Error: failed to get beam angle")
            elif angle == -99.0 :
                angle4 = angle
            else :
                angle4 = (angle - offset) % 360.0
            
            nstep += 1
            if nstep == nstep_max:
                break
            
        if angle4 >= angle_min and angle4 < angle_max :
            self.logger.info("Angle4 = %.2f , Nring = %.1f" % (float(angle4), float(nring)))
            l1x_step4 = int(self.mystatus['llt_collens_x_step'])
            l1y_step4 = int(self.mystatus['llt_collens_y_step'])
            self.logger.info("L1X.STEP4 = %d , L1Y.STEP4 = %d" % (l1x_step4, l1y_step4))
        else :
            self.llt("L1X", "MAS", l1x_step_org, "LLT")
            self.llt("L1Y", "MAS", l1y_step_org, "LLT")
            raise LGSError("Error: failed to detect laser beam angle4")

        # calculate the L1x step corresponds to the target_angle 
        if(angle4 != angle3):
            if angle3 >= 90.0 and angle3 < 180.0 :
                x1 = 0
                x2 = l1x_step4 - l1x_step3
                t1 = (angle3-90.0)*math.pi/180.0
                t2 = (270.0-angle4)*math.pi/180.0
                x = (x1*math.tan(t1)+x2*math.tan(t2)) / (math.tan(t1)+math.tan(t2))
                l1x_step_align = l1x_step3 + x
            elif angle3 >= 180.0 and angle3 < 270.0 :
                x1 = 0
                x2 = l1x_step3 - l1x_step4
                t1 = (angle4-90.0)*math.pi/180.0
                t2 = (270.0-angle3)*math.pi/180.0
                x = (x1*math.tan(t1)+x2*math.tan(t2)) / (math.tan(t1)+math.tan(t2))
                l1x_step_align = l1x_step4 + x
 
            self.logger.info("L1X.ALIGN = %d" % (l1x_step_align))
        else:
            self.llt("L1X", "MAS", l1x_step_org, "LLT")
            self.llt("L1Y", "MAS", l1y_step_org, "LLT")
            raise LGSError("Error: failed to detect laser beam angle (angle did not change between step 3 and 4)")

        # move l1x, l1y to the aligned position
        self.llt("L1X", "MAS", l1x_step_align, "LLT")
        self.llt("L1Y", "MAS", l1y_step_align, "LLT")

    ### Sleep ###
    def sleep(self, sleep_time=0):

        itime = float(sleep_time)
        
        self.logger.info("\nSleeping for %f sec..." % itime)
        time.sleep(itime)
        self.logger.info("Woke up refreshed!")

    # Distributing LGS status to SOSS
    # Update all status
    def put_status(self, target="ALL"):

        self.mystatus.setvals(status='ALIVE')
  	# Bump our status
        if target.lower() == "all" or target.lower() == "laser":
            self.get_589laser_stat()
        if target.lower() == "all" or target.lower() == "diag":
            self.get_diag_stat()
        if target.lower() == "all" or target.lower() == "fiber":
            self.get_fiber_coupling_stat()
        if target.lower() == "all" or target.lower() == "lsroom":
            self.get_laser_room_stat()
        if target.lower() == "all" or target.lower() == "llt":
            self.get_llt_stat()
        if target.lower() == "all" or target.lower() == "safety":
            self.get_emgshut_stat()
        if target.lower() == "all" or target.lower() == "ltcs":
            self.get_ltcs_stat()

        """Forced export of our status.
        """
        try:
            self.ocs.exportStatus()
        except CamError, e:
            raise LGSError("Error putting status %s" % str(e))


    # get status -- just for testing
    def getstatus(self, target="ALL"):
        """Forced import of our status using the normal status interface.
        """
        try:
            ra, dec = self.ocs.requestOCSstatusList2List(['STATS.RA', 'STATS.DEC'])
            #ra, dec = self.ocs.requestOCSstatusList2List(['STATS.RA', 'STATS.DEC'])
        #except CamError, e:
        except Exception, e:
            raise LGSError("Error getting status: %s" % str(e))
        
            
        self.logger.info("Status returned: ra=%s dec=%s" % (ra, dec))
        

    # Command for SOSS acceptance test --- OK 
    def obcp_mode(self, motor='OFF', mode=None):
	"""One of the commands that are in the SOSSALL.cd
        """
        self.mode = mode


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

    
#END LGS.py

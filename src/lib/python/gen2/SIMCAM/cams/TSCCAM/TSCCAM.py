#
# TSCCAM.py -- TSC personality for SIMCAM instrument simulator
#   (Effectively a SOSS TSC command simulator.)
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Mar 18 22:47:06 HST 2009
#]
# Bruce Bon -- last edit 2007-05-05 20:51
#
"""This file implements a simulator for SOSS device dependent telescope
commands.
"""
import sys, time, os
import string, re

import Bunch
import Task
import astro.fitsutils as fitsutils

from SIMCAM import BASECAM
import SIMCAM.cams.common as common
import remoteObjects as ro


# Value to return for executing unimplemented command.
# 1: OK, 0: error
OK_res = (0, 'OK')
BadParm_res_code = 101
BadMode_res_code = 202

unimplemented_res = OK_res


class TSCCAMError(Exception):
    pass

class TSCCAM(BASECAM):

    def __init__(self, logger, env, ev_quit=None):

        super(TSCCAM, self).__init__()
        
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
        

    #######################################
    # INITIALIZATION
    #######################################
    def initialize(self, ocsint):
        '''Initialize instrument.  
        '''
        super(TSCCAM, self).initialize(ocsint)
        
        # Grab my handle to the OCS interface.
        self.ocs = ocsint

        # Thread pool for autonomous tasks
        self.threadPool = self.ocs.threadPool
        # For task inheritance:
        self.tag = 'TSCCAM'
        self.shares = ['logger', 'ev_quit', 'threadPool']
        
        # Used to format status buffer (item lengths must match definitions
        # of status aliases on SOSS side in $OSS_SYSTEM/StatusAlias.pro)
        statfmt = "%(status)-8.8s,%(mode)-8.8s,%(count)8d;"

        # Register my status.
        self.mystatus = self.ocs.addStatusTable('TSCC0001',
                                                ['status', 'mode', 'count'],
                                                formatStr=statfmt)
        
        # Establish initial status values
        self.mystatus.status = 'ALIVE'
        self.mystatus.mode = 'LOCAL'
        self.mystatus.count = 0

        # Will be set to periodic status task
        self.status_task = None

        # Thread-safe bunch for storing parameters read/written
        # by threads executing in this object
        self.param = Bunch.threadSafeBunch()
        
        # Interval between status packets (secs)
        self.param.status_interval = 60

        ro.init()
        self.g2status = ro.remoteObjectProxy('status')
        self.bootmgr = ro.remoteObjectProxy('bootmgr')

        # Simulation variables
        self.el = 89.5
        self.az = -90.0


    def start(self, wait=True):
        super(TSCCAM, self).start(wait=wait)
        self.logger.info("TSCCAM STARTED.")
        
        # Start auto-generation of status task
        t = common.IntervalTask(self.putstatus, 60.0)
        self.status_task = t
        t.init_and_start(self)


    def stop(self, wait=True):
        super(TSCCAM, self).stop(wait=wait)
        
        # Terminate status generation task
        if self.status_task != None:
            self.status_task.stop()

        self.status_task = None
        self.logger.info("TSCCAM STOPPED.")


    #######################################
    # INTERNAL METHODS
    #######################################

    def putstatus(self, target="ALL"):
        """Forced export of our status.
        """
        return self.ocs.exportStatus()

    def statusGenLoop(self):
        """The main status sending loop.
        """
        self.logger.info('Starting periodic sending of status')

        while not self.ev_quit.isSet():

            time_end = time.time() + self.param.status_interval

            try:
                self.putstatus()

            except Exception, e:
                self.logger.error("Error sending status: %s" % str(e))

            # Sleep for remainder of desired interval.  We sleep in
            # small increments so we can be responsive to changes to
            # ev_quit
            cur_time = time.time()
            self.logger.debug("Waiting interval, remaining: %f sec" % \
                              (time_end - cur_time))

            while (cur_time < time_end) and (not self.ev_quit.isSet()):
                self.ev_quit.wait(min(0.1, time_end - cur_time))
                cur_time = time.time()

            self.logger.debug("End interval wait")
                
        self.logger.info('Stopping periodic sending of status')


    #######################################
    # SOSS TSC DEVICE-DEPENDENT COMMANDS
    #######################################

    def adc(self, coord=None, f_select=None, mode=None, motor=None, position=None, telescope=None, wavelen=None):
        self.logger.error("command 'adc' not yet implemented")
        res = unimplemented_res
        return res

    def adc_pf(self, coord=None, f_select=None, motor=None, position=None, telescope=None, wavelen=None):
        self.logger.error("command 'adc_pf' not yet implemented")
        res = unimplemented_res
        return res

    def ag(self, readout=None, f_select=None, d_type=None, exposure=None, binning=None, 
                 cal_dark=None, cal_flat=None, cal_sky=None, x1=None, y1=None, 
                 x2=None, y2=None, cal_loop=None):
        self.logger.error("command 'ag' not yet implemented")
        res = unimplemented_res
        return res

        self.logger.info("*** TSC: AG command called ***")
        self.logger.debug(
            "            readout=%s, f_select=%s, d_type=%s, exposure=%s, " %
            (`readout`, `f_select`, `d_type`, `exposure`) )
        self.logger.debug(
            "            binning=%s, cal_dark=%s, cal_flat=%s, cal_sky=%s, " %
            (`binning`, `cal_dark`, `cal_flat`, `cal_sky`) )
        self.logger.debug(
            "            x1=%s, y1=%s, x2=%s, y2=%s, cal_loop=%s, " %
            (`x1`, `y1`, `x2`, `y2`, `cal_loop`) )
        readout = readout.upper()
        if readout == 'ON':
            self.logger.info("Turning ON ag camera send")
            res = self.bootmgr.start('ag_sim')

        elif readout == 'OFF':
            self.logger.info("Turning OFF ag camera send")
            res = self.bootmgr.stop('ag_sim')
            
        return res

    def ag_centroid(self, readout=None, f_select=None, calc_mode=None, x1=None, y1=None, 
                          x2=None, y2=None, calc_region=None, i_ceil=None, i_bottom=None ):
        self.logger.info("*** TSC:  command 'ag_centroid' not yet implemented ***")
        self.logger.debug(
            "            readout=%s, f_select=%s, calc_mode=%s, " %
            (`readout`, `f_select`, `calc_mode`) )
        self.logger.debug(
            "            x1=%s, y1=%s, x2=%s, y2=%s, " %
            (`x1`, `y1`, `x2`, `y2`) )
        self.logger.debug(
            "            calc_region=%s, i_ceil=%s, i_bottom=%s" %
            (`calc_region`, `i_ceil`, `i_bottom`) )
        res = unimplemented_res
        return res

    def ag_centroid_tt(self, calc_mode=None, i_bottom=None, i_ceil=None, readout=None, x1=None, x2=None, y1=None, y2=None):
        self.logger.error("command 'ag_centroid_tt' not yet implemented")
        res = unimplemented_res
        return res

    def ag_change_exptime(self, binning=None, exposure=None, f_select=None, readout=None, x1=None, x2=None, y1=None, y2=None):
        self.logger.error("command 'ag_change_exptime' not yet implemented")
        res = unimplemented_res
        return res

    def ag_change_skylvl(self, calc_region=None, f_select=None, i_bottom=None, i_ceil=None, readout=None):
        self.logger.error("command 'ag_change_skylvl' not yet implemented")
        res = unimplemented_res
        return res

    def ag_origin(self, motor=None, f_select=None, mode=None, calc_region=None, x=None, y=None):
        self.logger.info("*** TSC:  command 'ag_origin' not yet implemented ***")
        self.logger.debug(
            "            motor=%s, f_select=%s, mode=%s, calc_region=%s, " %
            (`motor`, `f_select`, `mode`, `calc_region`) )
        self.logger.debug( "            x=%s, y=%s" % (`x`, `y`) )
        res = unimplemented_res
        return res

    def ag_parts(self, f_select=None, motor=None, shutter=None):
        self.logger.error("command 'ag_parts' not yet implemented")
        res = unimplemented_res
        return res

    def ag_threshold(self, motor=None):
        self.logger.error("command 'ag_threshold' not yet implemented")
        res = unimplemented_res
        return res

    def ag_tracking(self, motor=None, f_select=None, calc_region=None):
        self.logger.info("*** TSC:  command 'ag_tracking' not yet implemented ***")
        self.logger.debug(
            "            motor=%s, f_select=%s, calc_region=%s" %
            (`motor`, `f_select`, `calc_region`) )
        res = unimplemented_res
        return res

    def ag_tt(self, binning=None, cal_dark=None, cal_flat=None, cal_loop=None, cal_sky=None, d_type=None, exposure=None, readout=None, x1=None, x2=None, y1=None, y2=None):
        self.logger.error("command 'ag_tt' not yet implemented")
        res = unimplemented_res
        return res

    def agsh_probe(self, anab=None, coord=None, dec=None, e=None, equinox=None, f_select=None, motor=None, pmdec=None, pmra=None, ra=None, telescope=None):
        self.logger.error("command 'agsh_probe' not yet implemented")
        res = unimplemented_res
        return res

    def agsh_probe_local(self, coord=None, f_select=None, motor=None, r=None, telescope=None, theta=None):
        self.logger.error("command 'agsh_probe_local' not yet implemented")
        res = unimplemented_res
        return res

    def agsh_probe_local_pf(self, motor=None, f_select=None, coord=None, 
                                  x=None, y=None, z=None, z_drive=None):
        self.logger.info("*** TSC:  command 'agsh_probe_local_pf' not yet implemented ***")
        self.logger.debug(
            "            motor=%s, f_select=%s, coord=%s, " %
            (`motor`, `f_select`, `coord`) )
        self.logger.debug( "            x=%s, y=%s, z=%s, z_drive=%s" % (`x`, `y`, `z`, `z_drive`))
        res = unimplemented_res
        return res

    def agsh_probe_pf(self, motor=None, f_select=None, coord=None, ra=None, dec=None, 
                            equinox=None, pmra=None, pmdec=None, e=None, anab=None, z_drive=None):
        self.logger.info("*** TSC:  command 'agsh_probe_pf' not yet implemented ***")
        self.logger.debug(
            "            motor=%s, f_select=%s, coord=%s, ra=%s, dec=%s, " %
            (`motor`, `f_select`, `coord`, `ra`, `dec`) )
        self.logger.debug(
            "            equinox=%s, pmra=%s, pmdec=%s, e=%s, " %
            (`equinox`, `pmra`, `pmdec`, `e`) )
        self.logger.debug( "            anab=%s, z_drive=%s" % (`anab`, `z_drive`) )
        res = unimplemented_res
        return res

    def azeldrive(self, motor=None, coord=None, az=None, el=None, 
                  az_speed=None, el_speed=None):

        self.logger.debug("*** TSC:  command 'azeldrive' starting ***")
        self.logger.debug(
            "            motor=%s, coord=%s, az=%s, el=%s, az_speed=%s, el_speed=%s" %
            (str(motor), str(coord), str(az), str(el), str(az_speed),
             str(el_speed)) )

        if  abs(el_speed) == 0.0:
            msg = "AzElDrive: EL_SPEED must be > 0"
            self.logger.error(msg)
            res = (BadParm_res_code, msg)
            return res
        commanded_el = string.atof(el)
        el_speed = string.atof(el_speed)
#        start_el = float(self.g2status.fetchOne('TSCS.EL'))
        start_el = self.el
        if commanded_el > self.el:
            dir = abs(el_speed)
        else:
            dir = - abs(el_speed)
        self.g2status.store({'TSCS.EL_CMD': commanded_el})
        while int(self.el) != int(commanded_el):
            end_time = time.time() + 1.0/abs(el_speed)

            self.g2status.store({'TSCS.EL': self.el})
            self.el += dir

            cur_time = time.time()
            if cur_time < end_time:
                time.sleep(end_time - cur_time)

        self.el = commanded_el
        self.g2status.store({'TSCS.EL': self.el})
        res = 0
        self.logger.info("*** TSC:  command 'azeldrive' completed ***")
        return res

    def cal_parts(self, f_select=None, fan=None, filter_a=None, filter_b=None, filter_c=None, filter_d=None, mode=None, motor=None, shutter=None):
        self.logger.error("command 'cal_parts' not yet implemented")
        res = unimplemented_res
        return res

    def cal_probe(self, coord=None, f_select=None, motor=None, position=None):
        self.logger.error("command 'cal_probe' not yet implemented")
        res = unimplemented_res
        return res

    def cal_source(self, amp=None, f_select=None, lamp=None, motor=None):
        self.logger.error("command 'cal_source' not yet implemented")
        res = unimplemented_res
        return res

    def cellcover(self, motor=None, position=None):
        self.logger.error("command 'cellcover' not yet implemented")
        res = unimplemented_res
        return res

    def domedrive(self, mode=None, motor=None, position=None):
        self.logger.error("command 'domedrive' not yet implemented")
        res = unimplemented_res
        return res

    def domeff(self, motor=None, mode=None, lamp=None, amp=None, volt=None):
        self.logger.info("*** TSC:  command 'domeff' not yet implemented ***")
        self.logger.debug(
            "            motor=%s, mode=%s, lamp=%s, amp=%s, volt=%s" %
            (`motor`, `mode`, `lamp`, `amp`, `volt`) )
        res = unimplemented_res
        return res

    def domelight(self, lamp=None, motor=None):
        self.logger.error("command 'domelight' not yet implemented")
        res = unimplemented_res
        return res

    def domeshutter(self, motor=None, position=None, topscreen=None):
        self.logger.error("command 'domeshutter' not yet implemented")
        res = unimplemented_res
        return res

    def imgrot(self, coord=None, motor=None, position=None, telescope=None, type=None):
        self.logger.error("command 'imgrot' not yet implemented")
        res = unimplemented_res
        return res

    def insrot(self, coord=None, motor=None, position=None, telescope=None):
        self.logger.error("command 'insrot' not yet implemented")
        res = unimplemented_res
        return res

    def insrot_pf(self, motor=None, telescope=None, coord=None, position=None):
        self.logger.info("*** TSC:  command 'insrot_pf' not yet implemented ***")
        self.logger.debug(
            "            motor=%s, telescope=%s, coord=%s, position=%s, " %
            (`motor`, `telescope`, `coord`, `position`) )
        res = unimplemented_res
        return res

    def irm2(self, amp=None, direction_mode=None, fq=None, mode=None, motor=None, offset_mode=None, pattern=None, position=None, signal=None, tx=None, ty=None, z=None, zero_bias=None):
        self.logger.error("command 'irm2' not yet implemented")
        res = unimplemented_res
        return res

    def m1cover(self, motor=None, position=None):
        self.logger.error("command 'm1cover' not yet implemented")
        res = unimplemented_res
        return res

    def m1_iec(self, motor=None):
        self.logger.error("command 'm1_iec' not yet implemented")
        res = unimplemented_res
        return res

    def m3drive(self, motor=None, position=None, select=None):
        self.logger.error("command 'm3drive' not yet implemented")
        res = unimplemented_res
        return res

    def ma_correction(self, motor=None):
        self.logger.error("command 'ma_correction' not yet implemented")
        res = unimplemented_res
        return res

    def native(self, cmd=None):
        self.logger.error("command 'native' not yet implemented")
        res = unimplemented_res
        return res

    def obe_param(self, agm2_offset=None, motor=None):
        self.logger.error("command 'obe_param' not yet implemented")
        res = unimplemented_res
        return res

    def operequest(self, message=None):
        self.logger.error("command 'operequest' not yet implemented")
        res = unimplemented_res
        return res

    def primode(self, mode=None, motor=None):
        self.logger.error("command 'primode' not yet implemented")
        res = unimplemented_res
        return res

    def sh(self, binning=None, cal_dark=None, cal_loop=None, cal_sky=None, d_type=None, exposure=None, readout=None):
        self.logger.error("command 'sh' not yet implemented")
        res = unimplemented_res
        return res

    def sh_change_exptime(self, exposure=None, readout=None):
        self.logger.error("command 'sh_change_exptime' not yet implemented")
        res = unimplemented_res
        return res

    def sh_change_skylvl(self, i_bottom=None, i_ceil=None, readout=None):
        self.logger.error("command 'sh_change_skylvl' not yet implemented")
        res = unimplemented_res
        return res

    def sh_measurement(self, i_bottom=None, i_ceil=None, loop=None, readout=None):
        self.logger.error("command 'sh_measurement' not yet implemented")
        res = unimplemented_res
        return res

    def sh_parts(self, motor=None, shutter=None):
        self.logger.error("command 'sh_parts' not yet implemented")
        res = unimplemented_res
        return res

    def sv(self, binning=None, cal_loop=None, d_type=None, exposure=None, readout=None, x1=None, x2=None, y1=None, y2=None):
        self.logger.error("command 'sv' not yet implemented")
        res = unimplemented_res
        return res

    def sv_centroid(self, calc_mode=None, calc_region=None, i_bottom=None, i_ceil=None, readout=None, x1=None, x2=None, y1=None, y2=None):
        self.logger.error("command 'sv_centroid' not yet implemented")
        res = unimplemented_res
        return res

    def sv_change_exptime(self, exposure=None, readout=None):
        self.logger.error("command 'sv_change_exptime' not yet implemented")
        res = unimplemented_res
        return res

    def sv_change_skylvl(self, calc_region=None, i_bottom=None, i_ceil=None, readout=None):
        self.logger.error("command 'sv_change_skylvl' not yet implemented")
        res = unimplemented_res
        return res

    def sv_origin(self, calc_region=None, mode=None, motor=None, x=None, y=None):
        self.logger.error("command 'sv_origin' not yet implemented")
        res = unimplemented_res
        return res

    def sv_parts(self, filter=None, motor=None, shutter=None):
        self.logger.error("command 'sv_parts' not yet implemented")
        res = unimplemented_res
        return res

    def sv_probe(self, coord=None, f_select=None, motor=None, position=None):
        self.logger.error("command 'sv_probe' not yet implemented")
        res = unimplemented_res
        return res

    def sv_threshold(self, motor=None):
        self.logger.error("command 'sv_threshold' not yet implemented")
        res = unimplemented_res
        return res

    def sv_tracking(self, calc_region=None, motor=None):
        self.logger.error("command 'sv_tracking' not yet implemented")
        res = unimplemented_res
        return res

    def teldrive(self, motor=None, coord=None, ra=None, dec=None, equinox=None, pmra=None, 
                       pmdec=None, e=None, anab=None, direction=None, target=None):
        self.logger.info("*** TSC:  command 'teldrive' not yet implemented ***")
        self.logger.debug(
            "            motor=%s, coord=%s, ra=%s, dec=%s" %
            (`motor`, `coord`, `ra`, `dec`) )
        self.logger.debug(
            "            equinox=%s, pmra=%s, pmdec=%s, e=%s, " %
            (`equinox`, `pmra`, `pmdec`, `e`) )
        self.logger.debug(
            "            anab=%s, direction=%s, target=%s" %
            (`anab`, `direction`, `target`) )
        res = unimplemented_res
        return res

    def teldrive_offset(self, motor=None, coord=None, ra=None, dec=None):
        self.logger.info("*** TSC:  command 'teldrive_offset' not yet implemented ***")
        self.logger.debug("            motor=%s, coord=%s ra=%s dec=%s" % (`motor`, `coord`, `ra`, `dec`) )
        res = unimplemented_res
        return res

    def telfocus(self, motor=None, coord=None, f_select=None, z=None):
        self.logger.info("*** TSC:  command 'telfocus' not yet implemented ***")
        self.logger.debug(
            "            motor=%s, coord=%s, f_select=%s, z=%s" %
            (`motor`, `coord`, `f_select`, `z`) )
        res = unimplemented_res
        return res

    def topscreen(self, coord=None, motor=None, p_select=None, position=None):
        self.logger.error("command 'topscreen' not yet implemented")
        res = unimplemented_res
        return res

    def windscreen(self, coord=None, motor=None, position=None):
        self.logger.error("command 'windscreen' not yet implemented")
        res = unimplemented_res
        return res

#        self.logger.debug(
#            "            motor=%s, motor=%s, motor=%s, motor=%s, " %
#            (`motor`, `motor`, `motor`, `motor`) )
#END TSCCAM.py

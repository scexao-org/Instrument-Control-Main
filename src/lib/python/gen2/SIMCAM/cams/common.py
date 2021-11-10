#
# common.py -- Common functions for instrument simulators
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Tue Apr 15 16:30:04 HST 2008
#]
#
import time
import Task
from SIMCAM import CamError, CamCommandError

    #######################################
    # Tasks for autonomous threads.
    #######################################

class DelayedSendTask(Task.Task):

    def __init__(self, ocs, waittime, framelist):
        self.ocs = ocs
        self.waittime = float(waittime)
        self.framelist = framelist

        super(DelayedSendTask, self).__init__()

    def execute(self):
        self.logger.info("DelayedSendTask: %f, %s" % (self.waittime,
                                                      str(self.framelist)))

        # Wait the right amount of time
        time.sleep(self.waittime)

        self.logger.info("Submitting framelist: %s" % str(self.framelist))
        res = self.ocs.archive_fits(self.framelist)

        return res
    

class IntervalTask(Task.Task):
    """Task that runs a function at a given interval, passing it args
    and kwdargs.
    """

    def __init__(self, fn, interval, args=None, kwdargs=None):
        self.fn = fn
        self.interval = interval
        if not args:
            args = []
        self.args = args
        if not kwdargs:
            kwdargs = {}
        self.kwdargs = kwdargs
        super(IntervalTask, self).__init__()

    def stop(self):
        self.ev_quit.set()
        
    def execute(self):
        self.logger.info('Starting periodic interval task')

        while not self.ev_quit.isSet():

            time_end = time.time() + self.interval

            try:
                self.fn(*self.args, **self.kwdargs)

            except Exception, e:
                self.logger.error("Error invoking fn: %s" % str(e))

            # Sleep for remainder of desired interval.  We sleep in
            # small increments so we can be responsive to changes to
            # ev_quit
            cur_time = time.time()
            self.logger.debug("Waiting interval, remaining: %f sec" % \
                              (time_end - cur_time))

            while (cur_time < time_end) and (not self.ev_quit.isSet()):
                time.sleep(0)
                self.ev_quit.wait(min(0.1, time_end - cur_time))
                cur_time = time.time()

            self.logger.debug("End interval wait")
                
        self.logger.info('Stopping periodic interval task')

      
class PowerMonTask(IntervalTask):
    """
    A periodic task to check for a power outage and notify the OBCP if there
    is a problem.
    Shows an example of subclassing IntervalTask for a specific purpose.

    """

    def __init__(self, cam, fnOff, upstime=60.0,
                 fnDn=None, fnUp=None, check_interval=10.0):
        self.cam = cam
        self.fnOff = fnOff
        self.upstime = upstime
        self.fnDn = fnDn
        self.fnUp = fnUp
        self.interval = check_interval
        self.statusDict = {'TSCV.DOMEUPS': 0}
        self.on_ups_start_time = None
        
        super(PowerMonTask, self).__init__(self._check_power,
                                           self.interval)

    def _power_dn(self):
        # Record the time of the power outage, if we have not already
        if not self.on_ups_start_time:
            self.on_ups_start_time = time.time()

        # If we've been on UPS power for more than self.upstime seconds
        # then call the function we were configured with to shut down
        delta_down = time.time() - self.on_ups_start_time
        if delta_down >= self.upstime:
            self.fnOff(upstime=self.on_ups_start_time)

        elif self.fnDn:
            # If we haven't hit the shutdown interval, but the user
            # specified a function to call warning of impending shutdown,
            # call it.
            self.fnDn(upstime=self.on_ups_start_time)

        else:
            # If nothing else, log a warning message
            self.logger.warn('WARNING: running on UPS power!')

        
    def _power_up(self):
        # Cancel any pending call to self.fnOff
        if self.on_ups_start_time:
            self.on_ups_start_time = None

            # If the user specified a function to call when the power
            # returned (before the deadline), then call it.
            if self.fnUp:
                self.fnUp(upstime=time.time())

            else:
                # If nothing else, log a message
                self.logger.warn('Power restored.')
        
        
    def _check_power(self):
        self.logger.debug('Checking power via TSCV.DOMEUPS')
        try:
            # TODO: get the interface, rather than relying on cam
            # assigning it to 'ocs'
            self.cam.ocs.requestOCSstatus(self.statusDict)
            #self.cam.ocs.getOCSstatus(self.statusDict)

            # Validate the status result
            results = self.cam.ocs.validateStatus(self.statusDict)
            if len(results) > 0:
                self.logger.warn("Values are invalid for: %s" % str(results))

            else:
                # interpret value
                value = int(self.statusDict['TSCV.DOMEUPS'])
                self.logger.debug("DOMEUPS=%d" % value)
                if value != 0:
                    self._power_dn()
                else:
                    self._power_up()

        except (ValueError, CamError), e:
            self.logger.error("Error checking power status: %s" % str(e))


class FuncTask(Task.FuncTask):
    """Task that runs a method or function.
    """

    def __init__(self, func, args, **kwdargs):
        """
        func: any callable.
        args: tuple or list of positional arguments
        kwdargs: any keyword arguments 
        """
        super(FuncTask, self).__init__(func, args, kwdargs)

      
#END

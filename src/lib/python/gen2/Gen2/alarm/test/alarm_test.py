#!/usr/bin/env python
#
# alarm_test.py -- Test alarm_handler and verify that alarms are
#                  getting triggered
#
# Typical runup command:
#    alarm_test.py --log alarm_test.log
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Wed Apr 25 16:16:19 HST 2012
#]
#

import os, sys
import time
import re
import threading
import remoteObjects as ro
import remoteObjects.Monitor as Monitor
import ssdlog
import AlarmTest
import ADCFreeTest
import AngleLimitTimeTest
import AzAngleLimitTest
import RotAngleLimitTest
import AGProbeAngleLimitTest
import AG_PosnErrorTest
import EnviroTest
import GuideStarTest
import PACmdTest
import TipTiltTest
import WindscreenTest

# Default ports
default_alarm_test_port = 18031
default_mon_port = 18032

# Default set of channels to subscribe to
sub_channels = ['status']

# mutex to arbitrate access to status values
lock = threading.RLock()
# status feed from Gen2 will be stored in here
statusFromGen2 = {}

SLEEP = 3

def status_cb(payload, logger, statusProxy):
    global statusFromGen2, lock
    try:
        bnch = Monitor.unpack_payload(payload)
        if bnch.path != 'mon.status':
            return

        with lock:
            logger.debug('status updated: %s' % (
                    time.strftime("%H:%M:%S", time.localtime())))
            statusFromGen2.update(bnch.value)

    except Monitor.MonitorError, e:
        logger.error('monitor error: %s' % (str(e)))

    except Exception, e:
        logger.error('Exception in status_cb: %s' % (str(e)))

class AlarmTestService:
    def __init__(self, statusProxy, ev_quit):
        self.statusProxy = statusProxy
        self.ev_quit = ev_quit
        self.alarmTest = AlarmTest.AlarmTest()
        self.alarmTest.setUp()
        self.testPattern = '^test|Test$'
        self.Objects = {}
        self.Objects['ADCFreePFTest'] = ADCFreeTest.ADCFreePFTest()
        self.Objects['ADCFreeNsCsTest'] = ADCFreeTest.ADCFreeNsCsTest()
        self.Objects['AngleLimitTimeTest'] = AngleLimitTimeTest.AngleLimitTimeTest()
        self.Objects['AzAngleLimitTest'] = AzAngleLimitTest.AzAngleLimitTest()
        self.Objects['RotAngleLimitP_IRTest'] = RotAngleLimitTest.RotAngleLimitP_IRTest()
        self.Objects['RotAngleLimitP_OPTTest'] = RotAngleLimitTest.RotAngleLimitP_OPTTest()
        self.Objects['RotAngleLimitNsTest'] = RotAngleLimitTest.RotAngleLimitNsTest()
        self.Objects['RotAngleLimitCsTest'] = RotAngleLimitTest.RotAngleLimitCsTest()
        self.Objects['AGProbeAngleLimitNsTest'] = AGProbeAngleLimitTest.AGProbeAngleLimitNsTest()
        self.Objects['AGProbeAngleLimitCsTest'] = AGProbeAngleLimitTest.AGProbeAngleLimitCsTest()
        self.Objects['AG_PosnErrorTest'] = AG_PosnErrorTest.AG_PosnErrorTest()
        self.Objects['EnviroTest'] = EnviroTest.EnviroTest()
        self.Objects['GuideStarTest'] = GuideStarTest.GuideStarTest()
        self.Objects['PACmdPFTest'] = PACmdTest.PACmdPFTest()
        self.Objects['PACmdNsTest'] = PACmdTest.PACmdNsTest()
        self.Objects['PACmdCsTest'] = PACmdTest.PACmdCsTest()
        self.Objects['TipTiltTest'] = TipTiltTest.TipTiltTest()
        self.Objects['WindscreenTest'] = WindscreenTest.WindscreenTest()

    def changeFocus(self):
        self.alarmTest.setFocusChanging(True)
        self.statusProxy.store(self.alarmTest.statusFromGen2)
        return 0
        
    def doMethod(self, Method, focalStation=None, severity=None, Module=None, Class=None):
        found = False
        if Module == None and Class == None:
            for Class in self.Objects:
                Object = self.Objects[Class]
                if hasattr(Object, Method):
                    found = True
                    break
        else:
            try:
                Object = eval('%s.%s()' % (Module, Class))
            except NameError as e:
                return str(e)
            except AttributeError as e:
                return str(e)
            found = True
        if found:
            eval('Object.setUp()')
            methodCall = 'Object.%s(' % Method
            if focalStation:
                methodCall += "focalStation='%s'" % focalStation
                if severity:
                    methodCall += ','
            if severity:
                methodCall += "severity='%s'" % severity
            methodCall += ')'
            eval(methodCall)
            print Object.statusFromGen2
            if 'TSCV.FOCUSINFO' in Object.statusFromGen2 or 'TSCV.FOCUSINFO2' in Object.statusFromGen2:
                changingFocus = True
                self.changeFocus()
                time.sleep(SLEEP)
            else:
                changingFocus = False
            self.statusProxy.store(Object.statusFromGen2)
            if changingFocus:
                self.alarmTest.setFocusChanging(False)
                self.statusProxy.store(self.alarmTest.statusFromGen2)
            return '.'.join([Class, Method]) + ' complete'
        else:
            return found

    def doAllMethods(self, Class, Module = None):
        if Module == None:
            Module = Class
        self.doMethod('testAllOk', Module, Class)
        for attr in dir(self.Objects[Class]):
            if re.search(self.testPattern, attr):
                method = self.doMethod(attr, Module, Class)
                print method
                time.sleep(SLEEP)
        self.doMethod('testAllOk', Module, Class)
        return 0

    def listClasses(self):
        return self.Objects.keys()

    def listAllTests(self):
        tests = {}
        for Class in self.Objects:
            tests[Class] = []
            for attr in dir(self.Objects[Class]):
                if re.search(self.testPattern, attr):
                    tests[Class].append(attr)
        return tests

    def listTests(self, Class):
        tests = []
        for attr in dir(self.Objects[Class]):
            if re.search(self.testPattern, attr):
                tests.append(attr)
        return tests

    def testEnviro(self):
        self.doAllMethods('EnviroTest')
        return 0

def main(options, args):
    global statusFromGen2, lock

    # Create top level logger.
    logger = ssdlog.make_logger('alarm_test', options)

    statusFromGen2 = {}

    logger.debug("Initializing remote objects")
    if options.rohosts:
        ro.init(options.rohosts.split(','))
    else:
        ro.init()

    # Connect to the status service via a proxy object and fetch
    # initial status items that we need
    statusProxy = ro.remoteObjectProxy('status')
    logger.info("Fetching initial status values")
    statusFromGen2 = statusProxy.fetch(statusFromGen2)
    logger.info('initial status %s' % statusFromGen2)

    # make a name for our monitor
    if options.monname:
        myMonName = options.monname
    else:
        myMonName = 'alarm_test.mon'

    # Create a local monitor
    mymon = Monitor.Monitor(myMonName, logger, numthreads=options.numthreads)

    # Subscribe our local callback function
    fn = lambda payload, name, channels: status_cb(payload, logger, statusProxy)
    mymon.subscribe_cb(fn, sub_channels)

    # Startup monitor
    mymon.start(wait=True)
    mymon.start_server(wait=True, port=options.monport)

    # subscribe our monitor to the publication feed
    mymon.subscribe_remote(options.monitor, sub_channels, {})

    ev_quit = threading.Event()

    testMethods = [
        'changeFocus',
        'doMethod',
        'doAllMethods',
        'listClasses',
        'listAllTests',
        'listTests',
        'testEnviro'
        ]

    alarmTestService = AlarmTestService(statusProxy, ev_quit)
    alarm_test_svc = ro.remoteObjectServer(svcname='alarm_test',
                                           obj=alarmTestService, logger=logger,
                                           method_list=testMethods,
                                           port=options.alarm_test_port,
                                           ev_quit=ev_quit,
                                           #auth=None,
                                           usethread=True)
    alarm_test_svc.ro_start(wait=True)


    logger.info('Starting up main program...')
    try:
        try:
            print "Type ^C to exit the server"
            while True:
                sys.stdin.readline()

        except KeyboardInterrupt:
            logger.info('Received keyboard interrupt--"shutting down...')
    finally:
        logger.info("shutting down...")
        mymon.stop_server(wait=True)
        alarm_test_svc.ro_stop(wait=True)
        mymon.stop(wait=True)

if __name__ == '__main__':

    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))

    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-m", "--monitor", dest="monitor", default='monitor',
                      metavar="NAME",
                      help="Subscribe to feeds from monitor service NAME")
    optprs.add_option("--monname", dest="monname", metavar="NAME",
                      help="Use NAME as our monitor subscriber name")
    optprs.add_option("--monport", dest="monport", type="int",
                      default=default_mon_port,
                      help="Register monitor using PORT", metavar="PORT")
    optprs.add_option("--alarm_test_port", dest="alarm_test_port", type="int",
                      default=default_alarm_test_port, metavar="PORT",
                      help="Use PORT for our alarm test service")
    optprs.add_option("--numthreads", dest="numthreads", type="int",
                      default=50,
                      help="Start NUM threads in thread pool", metavar="NUM")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--rohosts", dest="rohosts",
                      metavar="HOSTLIST",
                      help="Hosts to use for remote objects connection")

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

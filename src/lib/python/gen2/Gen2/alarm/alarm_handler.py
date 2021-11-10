#!/usr/bin/env python
#
# alarm_handler.py -- Monitor Gen2 status aliases and report alarms
#
# Typical runup command:
#    alarm_handler.py --log alarm_handler.log
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Fri Aug 10 13:23:49 HST 2012
#]
#

import os, sys
import time
import threading
import remoteObjects as ro
import remoteObjects.Monitor as Monitor
import Task
import ssdlog
import Gen2.soundsink as SoundSink
import Gen2.alarm.StatusValHistory as StatusValHistory
import Gen2.alarm.StatusVar as StatusVar

# Default ports
default_alh_port = 18011
default_mon_port = 18012

default_purge_max_age_days = 31
default_purge_max_length = 100
default_purge_interval = 600

default_persist_data_filename = 'alarm_handler.shelve'
default_persist_data_save_interval = 300

# Default alarm configuration file
try:
    pyhome = os.environ['PYHOME']
    cfgDir = os.path.join(pyhome, 'cfg', 'alarm')
except:
    cfgDir = '.'
default_alarm_cfg_file = os.path.join(cfgDir, '*.yml')

# Default persistent data file
try:
    pyhome = os.environ['GEN2COMMON']
    persist_data_dir = os.path.join(pyhome, 'db')
except:
    persist_data_dir =  os.path.join('/gen2/share/db')
default_persist_data_file = os.path.join(persist_data_dir, default_persist_data_filename)

persistDatafileLock = threading.RLock()

# Default set of channels to subscribe to
sub_channels = ['status']

# Default set of channels to publish to
pub_channels = ['sound']

# mutex to arbitrate access to status values
lock = threading.RLock()
# status feed from Gen2 will be stored in here
statusFromGen2 = {}

def status_cb(payload, logger, statusProxy, svConfig, statusValHistory, soundsink):
    global statusFromGen2, lock
    try:
        bnch = Monitor.unpack_payload(payload)
        if bnch.path != 'mon.status':
            return

        with lock:
            logger.debug('status updated: %s' % (
                    time.strftime("%H:%M:%S", time.localtime())))
            statusFromGen2.update(bnch.value)

        statusValHistory.update(svConfig, statusFromGen2)
#        statusValHistory.report()
        statusValHistory.reportAlarms(svConfig, soundsink)
        updateStatusForGUI(statusProxy, statusValHistory, logger)
        updateStatusForSTS(statusProxy, svConfig, statusValHistory, logger)
   
    except Monitor.MonitorError, e:
        logger.error('monitor error: %s' % (str(e)))

    except Exception, e:
        logger.error('Exception in status_cb: %s' % (str(e)))

def initialStatusForGUI(statusProxy, statusValHistory, logger):
    alarmStatus = {}

    for alarm in statusValHistory.initialAlarmList:
        ID = alarm.ID
        if alarm.visible:
            alarmStatus['ALARM_' + ID] = alarm.getAlarm()

    # Send the initial status to the status proxy
    logger.info('initialStatusForGUI sending %s' % alarmStatus)
    statusProxy.store(alarmStatus)

def initialStatusForSTS(statusProxy, svConfig, statusValHistory, logger):
    statusForSTS = {}

    # Insert the current time into the status dictionary
    statusForSTS['STS.TIME1'] = time.time()

    # Loop through all the ID's in the status variable
    # configuration
    for ID in svConfig.configID:
        if ID in statusValHistory.history:
            # Get the time history for this ID
            history = statusValHistory.history[ID]
            # Get the status variable configuration for this ID to see
            # if it has an STSAlias attribute.
            svConfigItem = svConfig.configID[ID]
            STSAlias = svConfigItem.STSAlias
            # If this ID has an STSAlias attribute, then look at the
            # most recent value in the time-history and set the STS
            # status corresponding to the alarm state.
            if STSAlias:
                if history[-1].alarmState == 'Ok':
                    statusForSTS[STSAlias] = 0
                else:
                    statusForSTS[STSAlias] = 1

    # Send the initial status to the status proxy
    logger.info('initialStatusForSTS sending %s' % statusForSTS)
    statusProxy.store(statusForSTS)

def updateStatusForGUI(statusProxy, statusValHistory, logger):
    alarmStatus = {}

    # Loop through all the alarms in the "changed" list
    for alarm in statusValHistory.changedAlarmList:
        # We use the ID in the alarm as an index to get the
        # status variable configuration information for this alarm
        ID = alarm.ID
        if alarm.visible:
            alarmStatus['ALARM_' + ID] = alarm.getAlarm()

    # Now loop through all the alarms in the "reported" list
    for alarm in statusValHistory.reportAlarmList:
        ID = alarm.ID
        if alarm.visible:
            alarmStatus['ALARM_' + ID] = alarm.getAlarm()

    # Send the updated status to the status proxy
    logger.debug('updateStatusForGUI sending %s' % alarmStatus)
    statusProxy.store(alarmStatus)

def updateStatusForSTS(statusProxy, svConfig, statusValHistory, logger):
    statusForSTS = {}

    # We always want to update the clock
    statusForSTS['STS.TIME1'] = time.time()

    # Loop through all the alarms that have changed state and set the
    # corresponding values in statusForSTS.
    for alarm in statusValHistory.changedAlarmList:
        # We use the MelcoId in the alarm as an index to get the
        # status variable configuration information for this alarm
        ID = alarm.ID
        svConfigItem = svConfig.configID[ID]
        # If this ID has an STSAlias attribute, then set the STS
        # status corresponding to the alarm state.
        STSAlias = svConfigItem.STSAlias
        if STSAlias:
            if alarm.alarmState == 'Ok':
                statusForSTS[STSAlias] = 0
            else:
                statusForSTS[STSAlias] = 1

    # Send the updated status to the status proxy
    logger.debug('updateStatusForSTS sending %s' % statusForSTS)
    statusProxy.store(statusForSTS)

class AlarmHandlerService:
    def __init__(self, soundsink, svConfig, svHistory, persistDataFile, ev_quit):
        self.soundsink = soundsink
        self.svConfig = svConfig
        self.svHistory = svHistory
        self.persistDataFile = persistDataFile
        self.ev_quit = ev_quit
        self.periodicTaskNames = ('periodicPurge', 'periodicSave')
        self.timer = {}
        self.ev_timerComplete = {}
        for name in self.periodicTaskNames:
            self.ev_timerComplete[name] = threading.Event()

    def masterMuteOff(self):
        self.soundsink.muteOff()
        return 0

    def masterMuteOn(self):
        self.soundsink.muteOn()
        return 0

    def playFile(self):
        self.soundsink.playFile()
        return 0

    def muteOff(self, ID, severity):
        retVal = self.svConfig.muteOff(ID, severity, 'User')
        if retVal == 0:
            self.saveConfig()
        return retVal

    def muteOn(self, ID, severity):
        retVal = self.svConfig.muteOn(ID, severity, 'User')
        if retVal == 0:
            self.saveConfig()
        return retVal

    def startIgnoreAlarm(self, ID, severity):
        retVal = self.svConfig.startIgnoreAlarm(ID, severity)
        if retVal == 0:
            self.saveConfig()
        return retVal

    def stopIgnoreAlarm(self, ID, severity):
        retVal = self.svConfig.stopIgnoreAlarm(ID, severity)
        if retVal == 0:
            self.saveConfig()
        return retVal

    def dumpSvConfigItem(self, ID):
        return self.svConfig.dumpSvConfigItem(ID)

    def loadSvConfig(self, filename):
        return self.svConfig.loadSvConfig(filename)

    def reportHistory(self, ID = None):
        return self.svHistory.report(ID)

    def purgeHistory(self, age = 86400, ID = None):
        return self.svHistory.purge(age, ID=ID)

    def purgeHistoryLength(self, maxAgeDays = 31, maxLength = 100, ID = None):
        return self.svHistory.purge(86400*maxAgeDays, maxLength, ID)

    def saveHistory(self):
        return self.svHistory.saveHistory(self.persistDataFile)        

    def saveConfig(self):
        return self.svConfig.saveConfig(self.persistDataFile)        

    def timerCompletePeriodicPurge(self):
        self.ev_timerComplete['periodicPurge'].set()

    def timerCompletePeriodicSave(self):
        self.ev_timerComplete['periodicSave'].set()

    def _createTimer(self, name, interval, callback):
        self.timer[name] = threading.Timer(interval, callback)
        # tell the thread to terminate when the main process ends
        self.timer[name].daemon = True

    def periodicPurge(self, maxAgeDays, maxLength, interval):
        while not self.ev_quit.isSet():
            self.ev_timerComplete['periodicPurge'].clear()
            self._createTimer('periodicPurge', interval, self.timerCompletePeriodicPurge)
            self.timer['periodicPurge'].start()
            self.ev_timerComplete['periodicPurge'].wait(interval + 10)
            self.purgeHistoryLength(maxAgeDays, maxLength)

    def periodicSave(self, interval):
        while not self.ev_quit.isSet():
            self.ev_timerComplete['periodicSave'].clear()
            self._createTimer('periodicSave', interval, self.timerCompletePeriodicSave)
            self.timer['periodicSave'].start()
            self.ev_timerComplete['periodicSave'].wait(interval + 10)
            self.saveHistory()

    def stopTimer(self):
        for name in self.periodicTaskNames:
            if self.timer[name]:
                self.timer[name].cancel()
            self.ev_timerComplete[name].set()

def main(options, args):
    global statusFromGen2, lock

    # Create top level logger.
    logger = ssdlog.make_logger('alarm_handler', options)

    # Load the status variable configuration
    try:
        svConfig = StatusVar.StatusVarConfig(options.configfile, persistDatafileLock, logger)
        ## svConfig.loadSavedConfig(options.persistDataFile)
        ## svConfig.saveConfig(options.persistDataFile)
    except Exception, e:
        logger.error('Error opening configuration file(s): %s' % str(e))
        return

    # Use the Gen2 status aliases in the svConfig to create a dict
    # with those alias names as the keys in the dict.
    statusFromGen2 = {}.fromkeys(svConfig.configGen2)

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

    statusValHistory = StatusValHistory.StatusValHistory(persistDatafileLock, logger)
    ## statusValHistory.loadHistory(options.persistDataFile, svConfig)
    statusValHistory.purge(86400*options.purgeMaxAgeDays, options.purgeMaxLength)
    ## statusValHistory.saveHistory(options.persistDataFile)
    statusValHistory.initialValue(svConfig, statusFromGen2)

    logger.debug('initial history')
    statusValHistory.report()

    # make a name for our monitor
    if options.monname:
        myMonName = options.monname
    else:
        myMonName = 'alarm_handler.mon'

    # Create a local monitor
    mymon = Monitor.Monitor(myMonName, logger, numthreads=options.numthreads)

    # Create a SoundSource object so that we can send audio when an
    # alarm occurs
    soundsink = SoundSink.SoundSource(monitor=mymon, logger=logger, channels=pub_channels)

    # Tell the local monitor that we will be publishing to the sounds
    # channel
    mymon.publish_to(options.monitor, pub_channels, {})

    # Subscribe our local callback function
    fn = lambda payload, name, channels: status_cb(payload, logger, statusProxy, svConfig, statusValHistory, soundsink)
    mymon.subscribe_cb(fn, sub_channels)

    # Startup monitor
    mymon.start(wait=True)
    mymon.start_server(wait=True, port=options.monport)

    # subscribe our monitor to the publication feed
    mymon.subscribe_remote(options.monitor, sub_channels, {})

    ev_quit = threading.Event()

    # Create an AlarmHandlerService object and connect it to a remote
    # object server so that we can control the playing of the audio
    alarmHandlerService = AlarmHandlerService(soundsink, svConfig, statusValHistory, options.persistDataFile, ev_quit)
    alh_svc = ro.remoteObjectServer(svcname='alarm_handler',
                                    obj=alarmHandlerService, logger=logger,
                                    method_list=['masterMuteOff',
                                                 'masterMuteOn',
                                                 'playFile',
                                                 'muteOff',
                                                 'muteOn',
                                                 'startIgnoreAlarm',
                                                 'stopIgnoreAlarm',
                                                 'dumpSvConfigItem',
                                                 'loadSvConfig',
                                                 'reportHistory',
                                                 'purgeHistory',
                                                 'purgeHistoryLength',
                                                 'saveHistory',
                                                 'saveConfig'],
                                      port=options.alh_port,
                                      ev_quit=ev_quit,
                                      #auth=None,
                                      usethread=True)
    alh_svc.ro_start(wait=True)

    purgeTask = Task.FuncTask2(alarmHandlerService.periodicPurge, options.purgeMaxAgeDays, options.purgeMaxLength, options.purgeInterval)
    purgeTask.initialize(mymon)
    mymon.get_threadPool().addTask(purgeTask)

    ## persistDataSaveTask = Task.FuncTask2(alarmHandlerService.periodicSave, options.persistDataSaveInterval)
    ## persistDataSaveTask.initialize(mymon)
    ## mymon.get_threadPool().addTask(persistDataSaveTask)    

    statusValHistory.reportAlarms(svConfig, soundsink)
    initialStatusForGUI(statusProxy, statusValHistory, logger)
    initialStatusForSTS(statusProxy, svConfig, statusValHistory, logger)

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
        alarmHandlerService.stopTimer()
        mymon.stop_server(wait=True)
        alh_svc.ro_stop(wait=True)
        mymon.stop(wait=True)

if __name__ == '__main__':

    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))

    optprs.add_option("-f", "--configfile", dest="configfile", default=default_alarm_cfg_file,
                      help="Specify configuration file")
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
    optprs.add_option("--alh_port", dest="alh_port", type="int",
                      default=default_alh_port, metavar="PORT",
                      help="Use PORT for our sound service")
    optprs.add_option("--numthreads", dest="numthreads", type="int",
                      default=50,
                      help="Start NUM threads in thread pool", metavar="NUM")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--rohosts", dest="rohosts",
                      metavar="HOSTLIST",
                      help="Hosts to use for remote objects connection")

    optprs.add_option("--purgeMaxAgeDays", dest="purgeMaxAgeDays", type="int",
                      metavar="PURGEMAXAGEDAYS", default=default_purge_max_age_days,
                      help="Max age (days) of status variable history")
    optprs.add_option("--purgeMaxLength", dest="purgeMaxLength", type="int",
                      metavar="PURGEMAXLENGTH", default=default_purge_max_length,
                      help="Max length of status variable history")
    optprs.add_option("--purgeInterval", dest="purgeInterval", type="int",
                      metavar="PURGEINTERVAL", default=default_purge_interval,
                      help="Status value history purge interval (sec)")

    optprs.add_option("--persistDataFile", dest="persistDataFile",
                      default=default_persist_data_file,
                      help="Persistent data file")
    optprs.add_option("--persistDataSaveInterval", dest="persistDataSaveInterval", type="int",
                      default=default_persist_data_save_interval,
                      help="Persistent data save interval (sec)")

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

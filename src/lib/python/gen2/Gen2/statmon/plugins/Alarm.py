#
# Alarm.py -- Alarm plugin for statmon
#
# Uses the MainWindow class from alarm_gui.py to create an Alarm GUI
# that can be "plugged in" to statmon.
# 
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Tue Jun 19 08:25:40 HST 2012
#]
#
import os
import threading
from PyQt4 import QtGui, QtCore
import remoteObjects as ro
import Gen2.alarm.alarm_gui as AlarmGui
import Gen2.alarm.StatusVar as StatusVar
import Gen2.alarm.StatusValHistory as StatusValHistory
import PlBase

class Alarm(PlBase.Plugin):

    def build_gui(self, container):
        self.firstTime = True
        self.root = container
        self.aliases = []
        self.previousStatusDict = None

        # Set up a connection to the alarm_handler so that the GUI can
        # send messages to it
        self.alhProxy = ro.remoteObjectProxy('alarm_handler')

        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        container.setLayout(layout)

        # Create the GUI from the MainWindow class in alarm_gui.py
        self.mw = AlarmGui.MainWindow('', self.alhProxy, self.logger, container)
        layout.addWidget(self.mw, stretch=1)

    def start(self):
        persistDatafileLock = threading.RLock()

        # The configuration files tell us which Gen2 aliases we want
        # to monitor. The configuration files are normally in
        # $PYHOME/cfg/alarm. If $PYHOME is not defined, use the
        # current working directory.
        try:
            pyhome = os.environ['PYHOME']
            cfgDir = os.path.join(pyhome, 'cfg', 'alarm')
        except:
            cfgDir = '.'
        alarm_cfg_file = os.path.join(cfgDir, '*.yml')

        # StatusVarConfig reads in the configuration files
        try:
            self.svConfig = StatusVar.StatusVarConfig(alarm_cfg_file, persistDatafileLock, self.logger)
        except Exception, e:
            self.logger.error('Error opening configuration file(s): %s' % str(e))

        # Create a list of all the Gen2 aliases we want to monitor
        self.aliases = []
        for ID in self.svConfig.configID:
            if self.svConfig.configID[ID].Alarm:
                self.aliases.append('ALARM_' + ID)
        self.aliases.append('STS.TIME1')

        # Default persistent data file
        default_persist_data_filename = 'alarm_handler.shelve'
        try:
            pyhome = os.environ['GEN2COMMON']
            persist_data_dir = os.path.join(pyhome, 'db')
        except:
            persist_data_dir =  os.path.join('/gen2/share/db')
        default_persist_data_file = os.path.join(persist_data_dir, default_persist_data_filename)

        # Load the status value history
        self.statusValHistory = StatusValHistory.StatusValHistory(persistDatafileLock, self.logger)
        self.statusValHistory.loadHistory(default_persist_data_file, self.svConfig)

        # Register the update callback function and tell the
        # controller the names of the Gen2 aliases we want to monitor.
        self.controller.register_select('alarm', self.update, self.aliases)

    # changedStatus copies from statusDict only the status values that
    # have changed since the last time we got the update.
    def changedStatus(self, statusDict):
        changedStatusDict = {}
        # Iterate through all the Gen2 status aliases that we are
        # monitoring
        for name in self.aliases:
            # If this status alias is an "ALARM" alias, look at its
            # contents to see if anything has changed since the last
            # time we got the update. If so, add the alarm to the list
            # of changed status values.
            if 'ALARM_' in name:
                currentAlarmItem = statusDict[name]
                previousAlarmItem = self.previousStatusDict[name]
                changed = False
                for attribute in currentAlarmItem:
                    if currentAlarmItem[attribute] != previousAlarmItem[attribute]:
                        changed = True
                        break
                if changed:
                    changedStatusDict[name] = currentAlarmItem
            elif name == 'STS.TIME1':
                # STS.TIME1 is a scalar quantity, so just check to see
                # if it has been updated. If so, add it to the list of
                # changed status values.
                if statusDict[name] != self.previousStatusDict[name]:
                    changedStatusDict[name] = statusDict[name]

        # Return the list of changed values
        return changedStatusDict

    def update(self, statusDict):
        # The first time we get called, we have to call the
        # initializeAlarmWindow method. On subsequent calls, we need
        # to determine which status values have changed and then call
        # updateAlarmWindow.
        if self.firstTime:
            self.logger.debug(statusDict)
            AlarmGui.initializeAlarmWindow(self.mw, self.svConfig, self.statusValHistory, statusDict)
            self.firstTime = False
        else:
            try:
                changedStatusDict = self.changedStatus(statusDict)
            except TypeError as e:
                self.logger.error('Exception %s' % e)
                self.logger.debug('previousStatusDict %s' % self.previousStatusDict)
                self.logger.debug('current statusDict %s' % statusDict)
                changedStatusDict = {}
            self.logger.debug(changedStatusDict)
            AlarmGui.updateAlarmWindow(self.mw, self.svConfig, changedStatusDict)

        # Save the current statusDict information so that we can
        # determine if there are any changes the next time around.
        self.previousStatusDict = statusDict

    def __str__(self):
        return 'alarm'

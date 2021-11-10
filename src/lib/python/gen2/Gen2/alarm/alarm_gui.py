#!/usr/bin/env python
#
# alarm_gui.py -- GUI to monitor alarm-related Gen2 status aliases and
#                 display alarms
#
# Typical runup command:
#    alarm_gui.py --log alarm_gui.log
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Thu May 31 15:23:00 HST 2012
#]
#

import os, sys, operator
import time
import threading
from PyQt4 import QtCore, QtGui
import remoteObjects as ro
import remoteObjects.Monitor as Monitor
import ssdlog
import StatusVar
import StatusValHistory

# Default ports
default_mon_port = 18022

# Default alarm configuration file
try:
    pyhome = os.environ['PYHOME']
    cfgDir = os.path.join(pyhome, 'cfg', 'alarm')
except:
    cfgDir = '.'
default_alarm_cfg_file = os.path.join(cfgDir, '*.yml')

# Default persistent data file
default_persist_data_filename = 'alarm_handler.shelve'

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

class MyTableModel(QtCore.QAbstractTableModel): 
    def __init__(self, datain, headerdata, parent=None, *args): 
        """ datain: a list of lists
            headerdata: a list of strings
        """
        QtCore.QAbstractTableModel.__init__(self, parent, *args) 
        self.arraydata = datain
        self.headerdata = headerdata
        self.sortColumn = None
        self.sortOrder = None

    def insertRow(self, row, index=QtCore.QModelIndex()):
        self.beginInsertRows(index, row, row)
        if len(self.headerdata) == 4:
            self.arraydata.append([0,'NoId','NoName','NoSeverity'])
        else:
            self.arraydata.append([0,'NoId','NoName','NoSeverity',False])
        self.endInsertRows()
        return True
 
    def removeRow(self, row, index=QtCore.QModelIndex()):
        self.beginRemoveRows(index, row, row)
        self.arraydata = self.arraydata[:row] + self.arraydata[row+1:]
        self.endRemoveRows()
        return True
 
    def rowCount(self, parent): 
        return len(self.arraydata) 
 
    def columnCount(self, parent): 
        return len(self.headerdata)
 
    def data(self, index, role):
        if not index.isValid(): 
            return QtCore.QVariant() 
        elif role == QtCore.Qt.DisplayRole: 
            dataItem = self.arraydata[index.row()][index.column()]
            if index.column() == 0:
                timestr = time.strftime('%Y-%b-%d %H:%M:%S',time.localtime(dataItem))
                return QtCore.QVariant(timestr)
            elif index.column() == 4:
                return QtCore.QVariant()
            else:
                return QtCore.QVariant(dataItem) 
        elif role == QtCore.Qt.BackgroundRole:
            severity = self.arraydata[index.row()][3]
            if severity.lower() == 'ok':
                return QtCore.QVariant(QtGui.QColor(QtCore.Qt.green))
            elif 'Warning' in severity:
                return QtCore.QVariant(QtGui.QColor(QtCore.Qt.yellow))
            elif 'Critical' in severity:
                return QtCore.QVariant(QtGui.QColor(QtCore.Qt.red))
            else:
                return QtCore.QVariant(QtGui.QColor(QtCore.Qt.white))
        elif role == QtCore.Qt.ForegroundRole:
            severity = self.arraydata[index.row()][3]
            if severity.lower() == 'ok':
                return QtCore.QVariant(QtGui.QColor(QtCore.Qt.black))
            elif severity == 'Warning':
                return QtCore.QVariant(QtGui.QColor(QtCore.Qt.black))
            elif severity == 'Critical':
                return QtCore.QVariant(QtGui.QColor(QtCore.Qt.white))
            else:
                return QtCore.QVariant(QtGui.QColor(QtCore.Qt.black))
        elif role == QtCore.Qt.TextAlignmentRole:
            if index.column() == 1 or index.column() == 3:
                return QtCore.QVariant(QtCore.Qt.AlignCenter)
        elif role == QtCore.Qt.CheckStateRole:
            if index.column() == 4:
                if self.arraydata[index.row()][4]:
                    return QtCore.Qt.Checked
                else:
                    return QtCore.Qt.Unchecked
            else:
                return QtCore.QVariant()
        else:
#            print 'data method called with row,column,role',index.row(),index.column(),role
            return QtCore.QVariant()

    def setData(self, index, value, role = QtCore.Qt.EditRole):
        if role == QtCore.Qt.CheckStateRole and index.column() == 4:
            self.arraydata[index.row()][index.column()] = value.toBool()
            self.emit(QtCore.SIGNAL('dataChanged()'))
            ID = self.arraydata[index.row()][1]
            severity = self.arraydata[index.row()][3]
            self.emit(QtCore.SIGNAL('checkboxChanged'), ID, severity, value.toBool())
            return True
        else:
            return False

    def flags(self, index):
        if index.column() == 4:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable
        else:
            return QtCore.Qt.NoItemFlags

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant(self.headerdata[col])
        return QtCore.QVariant()

    def sort(self, Ncol, order):
        """Sort table by given column number.
        """
        self.emit(QtCore.SIGNAL('layoutAboutToBeChanged()'))
        self.arraydata = sorted(self.arraydata, key=operator.itemgetter(Ncol))
        self.sortColumn = Ncol
        self.sortOrder = order
        if order == QtCore.Qt.DescendingOrder:
            self.arraydata.reverse()
        self.emit(QtCore.SIGNAL('layoutChanged()'))

    def myAddData(self, alarm):
        self.insertRow(1)
        i = 0
        for item in alarm:
            self.arraydata[-1][i] = item
            i += 1
        if self.sortColumn != None:
            self.sort(self.sortColumn, self.sortOrder)

    def myUpdateData(self, alarm):
        timestamp = alarm[0]
        ID = alarm[1]
        Name = alarm[2]
        severity = alarm[3]
        muteOn = alarm[4]
        found = False
        if severity == 'Ok':
            i = 0
            for row in self.arraydata:
                if row[1] == ID:
                    found = True
                    break
                i += 1
            if found:
                self.removeRow(i)
        else:
            for row in self.arraydata:
                if row[1] == ID:
                    self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
                    row[0] = timestamp
                    row[2] = Name
                    row[3] = severity
                    row[4] = muteOn
                    self.emit(QtCore.SIGNAL("layoutChanged()"))
                    found = True
            if not found:
                self.myAddData(alarm)

    def myRemoveData(self, alarm):
        ID = alarm[1]
        Name = alarm[2]
        severity = alarm[3]
        found = False
        i = 0
        for row in self.arraydata:
            if row[1] == ID and row[2] == Name and row[3] == severity:
                found = True
                break
            i += 1
        if found:
            self.removeRow(i)

    def checkData(self, timestamp):
        # If there is more than one row in the table, remove the 'No
        # Active Alarms' row
        if len(self.arraydata) > 1:
            self.myRemoveData([0, 'N/A', 'No Active Alarms', 'OK', True])
        # If the table is empty, add a 'No Active Alarms' row
        elif len(self.arraydata) == 0:
            self.myAddData([timestamp, 'N/A', 'No Active Alarms', 'OK', True])

class MainWindow(QtGui.QWidget):
    def __init__(self, geometry, alhProxy, logger, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.currentData = []
        self.historyData = []
        self.currentModel = None
        self.historyModel = None
        self.alhProxy = alhProxy
        self.lastTimeUpdate = None
        self.logger = logger

        font = QtGui.QFont('DejaVu Sans', 9)
        self.setFont(font)

        # Compute column widths based on text in each column
        fm = self.fontMetrics()
        pad = 10
        timeWidth = fm.width(time.strftime('%Y-%b-%d %H:%M:%S',time.localtime(time.time()))) + pad
        IDWidth = fm.width('MELCO_0000000') + pad
        nameWidth = IDWidth
        severityWidth = fm.width('Severity') + pad
        muteWidth = fm.width('Mute') + pad
        self.columnWidths = {'Time': timeWidth, 'ID': IDWidth, 'Name': nameWidth, 'Severity': severityWidth, 'Mute': muteWidth}

        # Compute window width based on column widths
        windowWidth = 0
        for name in self.columnWidths:
            windowWidth += self.columnWidths[name]

        # Make the window a little wider than the sum of the columns
        windowWidthPad = 70
        windowWidth += windowWidthPad

        windowHeight = 400
        if len(geometry) > 0:
            [size, x, y] = geometry.split('+')
            if len(size) > 0:
                [windowWidth, windowHeight] = size.split('x')
            self.setGeometry(int(x), int(y), int(windowWidth), int(windowHeight))
        self.setWindowTitle('Alarm Monitor')

        self.layout = QtGui.QVBoxLayout(self)
 
        self.timeLabel = QtGui.QLabel('<font color="red">No time signal!</font>', self)
 
        if parent == None:
            self.qbtn = QtGui.QPushButton('Quit', self)
            self.qbtn.clicked.connect(QtCore.QCoreApplication.instance().quit)

        self.layout.addWidget(self.timeLabel)
        self.tabWidget = QtGui.QTabWidget()

        self.createCurrentTable()

        self.currentWidget = QtGui.QWidget()
        self.currentLayout = QtGui.QVBoxLayout()
        self.currentLayout.addWidget(self.currentTV)
        self.currentWidget.setLayout(self.currentLayout)
        self.tabWidget.addTab(self.currentWidget, 'Active')

        self.createHistoryTable()

        self.historyWidget = QtGui.QWidget()
        self.historyLayout = QtGui.QVBoxLayout()
        self.historyLayout.addWidget(self.historyTV)
        self.historyWidget.setLayout(self.historyLayout)
        self.tabWidget.addTab(self.historyWidget, 'History')

        self.layout.addWidget(self.tabWidget) 
        if parent == None:
            self.layout.addWidget(self.qbtn)

        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.connect(self.timer, QtCore.SIGNAL('timeout()'), self.myTimeout)
        self.timer.start(5000)

        self.connect(self, QtCore.SIGNAL('timeUpdate'), self.updateTimeLabel)
        self.connect(self, QtCore.SIGNAL('gen2AlarmUpdate'), self.addTheAlarm)
        self.connect(self, QtCore.SIGNAL('gen2CurrentAlarmUpdate'), self.updateTheAlarm)
        self.connect(self, QtCore.SIGNAL('CheckActiveAlarms'), self.checkTheActiveAlarms)
        self.connect(self.currentModel, QtCore.SIGNAL('checkboxChanged'), self.checkboxChanged)

    def myTimeout(self):
        #print 'timeout at ',time.strftime('%Y-%b-%d %H:%M:%S',time.localtime(time.time()))
        if self.lastTimeUpdate:
            text = '<font color="red">%s</font>' % self.lastTimeUpdate
            self.timeLabel.setText(text)
        self.addAlarm(time.time(), 'N/A', 'Alarm handler conn. lost', 'Warning', False, True)

    def createCurrentTable(self):
        # create the view
        self.currentTV = QtGui.QTableView()

        # set the table model
        header = ['Time', 'ID', 'Name', 'Severity', 'Mute']
        self.currentModel = MyTableModel(self.currentData, header, self) 

        self.currentTV.setModel(self.currentModel)

        # hide vertical header
        vh = self.currentTV.verticalHeader()
        vh.setVisible(False)

        # set horizontal header properties
        hh = self.currentTV.horizontalHeader()
        hh.setStretchLastSection(True)

        # set column width to fixed values
        self.setColumnWidths(self.currentModel, self.currentTV)

        # enable sorting
        self.currentTV.setSortingEnabled(True)

    def createHistoryTable(self):
        # create the view
        self.historyTV = QtGui.QTableView()

        # set the table model
        header = ['Time', 'ID', 'Name', 'Severity']
        self.historyModel = MyTableModel(self.historyData, header, self) 

        self.historyTV.setModel(self.historyModel)

        # set the minimum size
#        tv.setMinimumSize(400, 300)

        # hide grid
#        tv.setShowGrid(False)

        # set the font
#        font = QtGui.QFont("Courier New", 8)
#        tv.setFont(font)

        # hide vertical header
        vh = self.historyTV.verticalHeader()
        vh.setVisible(False)

        # set horizontal header properties
        hh = self.historyTV.horizontalHeader()
        hh.setStretchLastSection(True)

        # set column width to fixed values
        self.setColumnWidths(self.historyModel, self.historyTV)

        # enable sorting
        self.historyTV.setSortingEnabled(True)

    def updateTime(self, text):
#        print 'updateTime called',text
        self.emit( QtCore.SIGNAL('timeUpdate'), text )       

    def updateTimeLabel(self, text):
        """ Add item to list widget """
#        print "updateTimeLabel: " + text
        self.lastTimeUpdate = text
        text = '<font color="green">%s</font>' % text
        self.timeLabel.setText(text)
        self.currentModel.myRemoveData([0, 'N/A', 'Alarm handler conn. lost', 'Warning', False])
        self.timer.stop()
        self.timer.start()

    def addAlarm(self, timestamp, ID, Name, alarmState, muteOn, acknowledged):
#        print 'addAlarm called',ID, Name, timestamp, alarmState
        alarm = [timestamp, ID, Name, alarmState]
        if ID != 'N/A' or alarmState.lower() != 'ok':
            self.emit( QtCore.SIGNAL('gen2AlarmUpdate'), alarm )

        alarm = [timestamp, ID, Name, alarmState, muteOn]
        self.emit( QtCore.SIGNAL('gen2CurrentAlarmUpdate'), alarm )       

    def checkActiveAlarms(self, timestamp):
        self.emit( QtCore.SIGNAL('CheckActiveAlarms'), timestamp )       

    def addTheAlarm(self, alarm):
        """ Add alarm to tableData """
#        print "AddTheAlarm: ", alarm
        self.historyModel.myAddData(alarm)

    def updateTheAlarm(self, alarm):
        """ Update alarm in tableData """
#        print "updateTheAlarm: ", alarm
        self.currentModel.myUpdateData(alarm)

    def checkTheActiveAlarms(self, timestamp):
        self.currentModel.checkData(timestamp)

    def checkboxChanged(self, ID, severity, value):
        if value:
            r = self.alhProxy.muteOn(ID,severity)
        else:
            r = self.alhProxy.muteOff(ID,severity)

    def setColumnWidths(self, dataModel, tv):
        i = 0
        for name in dataModel.headerdata:
            tv.setColumnWidth(i, self.columnWidths[name])
            i += 1

def initializeAlarmWindow(mainWindow, svConfig, statusValHistory, statusFromGen2):
    history = {}
    for ID in statusValHistory.history:
        historyID = statusValHistory.history[ID]
        if len(historyID) > 1:
            i = 0
            for statusVal in historyID:
                timestamp = statusVal.timestamp
                if i == 0:
                    if statusVal.alarmState != 'Ok':
                        if timestamp not in history:
                            history[timestamp] = {}
                        history[timestamp][ID] = statusVal
                else:
                    if statusVal.alarmState != 'Ok' or \
                       (statusVal.alarmState == 'Ok' and historyID[i - 1].alarmState != 'Ok'):
                        if timestamp not in history:
                            history[timestamp] = {}
                        history[statusVal.timestamp][ID] = statusVal
                i += 1
        else:
            statusVal = historyID[0]
            timestamp = statusVal.timestamp
            if statusVal.alarmState != 'Ok':
                if timestamp not in history:
                    history[timestamp] = {}
                history[timestamp][ID] = statusVal

    for timestamp in sorted(history):
        for ID in history[timestamp]:
            historyItem = history[timestamp][ID]
            alarmItem = {'Name': None,
                         'timestamp': timestamp,
                         'value': historyItem.value,
                         'alarmState': historyItem.alarmState,
                         'varType': None,
                         'units': None,
                         'audioFilename': None,
                         'muteOn': historyItem.muteOn,
                         'visible': None,
                         'acknowledged': False}
            if ID in svConfig.configID:
                svConfigItem = svConfig.configID[ID]
                alarmItem['Name'] = svConfigItem.Name
                alarmItem['varType'] = svConfigItem.Type
                if alarmItem['varType'] == 'Analog':
                    alarmItem['units'] = svConfigItem.Units
                if historyItem.alarmState in svConfigItem.Alarm:
                    alarmItem['audioFilename'] = svConfigItem.Alarm[historyItem.alarmState].Audio
                    alarmItem['visible'] = svConfigItem.Alarm[historyItem.alarmState].Visible
            alarm = StatusValHistory.StatusAlarm(ID,
                                                 alarmItem['Name'],
                                                 alarmItem['timestamp'],
                                                 alarmItem['value'],
                                                 alarmItem['alarmState'],
                                                 alarmItem['varType'],
                                                 alarmItem['units'],
                                                 alarmItem['audioFilename'],
                                                 alarmItem['muteOn'],
                                                 alarmItem['visible'])
            mainWindow.addAlarm(alarm.timestamp, alarm.ID, alarm.Name, alarm.alarmState, alarm.muteOn, alarmItem['acknowledged'])
    
    alarmCount = 0
    for ID in svConfig.configID:
        alias = 'ALARM_' + ID
        if alias in statusFromGen2:
            if isinstance(statusFromGen2[alias], dict):
                alarmItem = statusFromGen2[alias]
#                print 'alarmItem is',alarmItem
                if alarmItem['alarmState'] != 'Ok':
                    alarmCount += 1
                    alarm = StatusValHistory.StatusAlarm(ID,
                                                         alarmItem['Name'],
                                                         alarmItem['timestamp'],
                                                         alarmItem['value'],
                                                         alarmItem['alarmState'],
                                                         alarmItem['varType'],
                                                         alarmItem['units'],
                                                         alarmItem['audioFilename'],
                                                         alarmItem['muteOn'],
                                                         alarmItem['visible'])
                    mainWindow.addAlarm(alarm.timestamp, alarm.ID, alarm.Name, alarm.alarmState, alarm.muteOn, alarmItem['acknowledged'])
            else:
                print 'alias found in statusDict but it is not a dict',alias

    mainWindow.checkActiveAlarms(time.time())

def updateAlarmWindow(mainWindow, svConfig, statusFromGen2):
    alarmCount = 0
    for ID in svConfig.configID:
        alias = 'ALARM_' + ID
        if alias in statusFromGen2:
            if isinstance(statusFromGen2[alias], dict):
                alarmCount += 1
                alarmItem = statusFromGen2[alias]
                alarm = StatusValHistory.StatusAlarm(ID,
                                                     alarmItem['Name'],
                                                     alarmItem['timestamp'],
                                                     alarmItem['value'],
                                                     alarmItem['alarmState'],
                                                     alarmItem['varType'],
                                                     alarmItem['units'],
                                                     alarmItem['audioFilename'],
                                                     alarmItem['muteOn'],
                                                     alarmItem['visible'])
                mainWindow.addAlarm(alarm.timestamp, alarm.ID, alarm.Name, alarm.alarmState, alarm.muteOn, alarmItem['acknowledged'])
            else:
                print 'alias found in statusDict but it is not a dict',alias
    if 'STS.TIME1' in statusFromGen2:
        timeStr = time.asctime(time.localtime(statusFromGen2['STS.TIME1']))
        mainWindow.updateTime(timeStr)

    mainWindow.checkActiveAlarms(time.time())

def status_cb(payload, logger, mainWindow, svConfig):
    global statusFromGen2, lock
    try:
        bnch = Monitor.unpack_payload(payload)
        if bnch.path != 'mon.status':
            return

        with lock:
            logger.debug('status updated: %s' % (
                    time.strftime("%H:%M:%S", time.localtime())))
            statusDict = bnch.value
            statusFromGen2.update(statusDict)
            logger.debug("status updated: %d items time:%s" % (
                len(statusDict),
                time.strftime("%H:%M:%S", time.localtime())))

        if mainWindow:
            updateAlarmWindow(mainWindow, svConfig, statusDict)

    except Monitor.MonitorError, e:
        logger.error('monitor error: %s' % (str(e)))

    except Exception, e:
        logger.error('Exception in status_cb: %s' % (str(e)))

def main(options, args):
    global statusFromGen2, lock

    # Create top level logger.
    logger = ssdlog.make_logger('alarm_monitor', options)

    # Load the status variable configuration
    try:
        svConfig = StatusVar.StatusVarConfig(options.configfile, persistDatafileLock, logger)
    except Exception, e:
        logger.error('Error opening configuration file(s): %s' % str(e))
        return

    # Use the STS status aliases in the svConfig to create a dict
    # with those alias names as the keys in the dict.
#    statusFromGen2 = {}.fromkeys(svConfig.configGen2)
#    statusFromGen2['STS.TIME1'] = 0
    for ID in svConfig.configID:
        if svConfig.configID[ID].Alarm:
            statusFromGen2['ALARM_' + ID] = 0
    statusFromGen2['STS.Tel.NsOpt.Rot.1stLimPos'] = 0
    statusFromGen2['STS.Tel.NsOpt.Rot.2ndLimPos'] = 0
#    statusFromGen2['STS.Tel.NsOpt.Rot.2ndLimPos'] = 0

    logger.debug("Initializing remote objects")
    if options.rohosts:
        ro.init(options.rohosts.split(','))
    else:
        ro.init()

    # Tell alarm_handler process to save its status value history so
    # that we can get the up-date status values from the persistent
    # data file.
    try:
        alarmHandlerProxy = ro.remoteObjectProxy('alarm_handler')
        alarmHandlerProxy.saveHistory()
    except ro.remoteObjects.remoteObjectError, e:
        logger.warn('Warning: unable to connect to alarm_handler to save history: %s' % str(e))
    except Exception, e:
        logger.error('Error while telling alarm_handler to save history: %s' % str(e))

    # Load the status value history
    statusValHistory = StatusValHistory.StatusValHistory(persistDatafileLock, logger)
    statusValHistory.loadHistory(options.persistDataFile, svConfig)

    # Connect to the status service via a proxy object and fetch
    # initial status items that we need
    statusProxy = ro.remoteObjectProxy('status')
    logger.info("Fetching initial status values")
    statusFromGen2 = statusProxy.fetch(statusFromGen2)
    logger.info('initial status %s' % statusFromGen2)

    alhProxy = ro.remoteObjectProxy('alarm_handler')

    # make a name for our monitor
    if options.monname:
        myMonName = options.monname
    else:
        myMonName = 'alarm_monitor-%s.mon' % (ro.get_myhost(short=True))

    # Create a local monitor
    mymon = Monitor.Monitor(myMonName, logger, numthreads=options.numthreads)

    mainWindow = None

    # Subscribe our local callback function
    fn = lambda payload, name, channels: status_cb(payload, logger, mainWindow, svConfig)
    mymon.subscribe_cb(fn, sub_channels)

    # Startup monitor
    mymon.start(wait=True)
    mymon.start_server(wait=True, port=options.monport)

    # subscribe our monitor to the publication feed
    mymon.subscribe_remote(options.monitor, sub_channels, {})

    logger.info('Starting up main program...')
    try:
        QtGui.QApplication.setGraphicsSystem('raster')
        app = QtGui.QApplication(sys.argv)
        mainWindow = MainWindow(options.geometry, alhProxy, logger)
        initializeAlarmWindow(mainWindow, svConfig, statusValHistory, statusFromGen2)
        mainWindow.show()
        app.exec_()
    finally:
        logger.info("shutting down...")
        mymon.unsubscribe_remote(options.monitor, sub_channels, {})
        mymon.stop_server(wait=True)
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
    optprs.add_option("-g", "--geometry", dest="geometry",
                      metavar="GEOM", default="+1290+127",
                      help="X geometry for initial size and placement")
    optprs.add_option("--display", dest="display", metavar="HOST:N",
                      help="Use X display on HOST:N")
    optprs.add_option("-m", "--monitor", dest="monitor", default='monitor',
                      metavar="NAME",
                      help="Subscribe to feeds from monitor service NAME")
    optprs.add_option("--monname", dest="monname", metavar="NAME",
                      help="Use NAME as our monitor subscriber name")
    optprs.add_option("--monport", dest="monport", type="int",
                      default=default_mon_port,
                      help="Register monitor using PORT", metavar="PORT")
    optprs.add_option("--numthreads", dest="numthreads", type="int",
                      default=50,
                      help="Start NUM threads in thread pool", metavar="NUM")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--rohosts", dest="rohosts",
                      metavar="HOSTLIST",
                      help="Hosts to use for remote objects connection")
    optprs.add_option("--persistDataFile", dest="persistDataFile",
                      default=default_persist_data_file,
                      help="Persistent data file")

    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    if options.display:
        os.environ['DISPLAY'] = options.display

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

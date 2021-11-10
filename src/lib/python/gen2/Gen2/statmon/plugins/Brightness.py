#
# EnvMon.py -- Environment plugin for StatMon
# 
# Takeshi Inagaki (tinagaki@naoj.org)
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Apr 15 17:12:48 HST 2013
#]
#
import time
import math
import os
import shelve

import PlBase
import Bunch
# TODO: I think eventually most of these should be migrated over to
# statmon, or else redone....EJ
import Gen2.senvmon.statusGraph as StatusGraph
import Gen2.senvmon.timeValueGraph as timeValueGraph
# Needed for unpickling...ugh
from Gen2.senvmon.timeValueGraph import Global
import Gen2.senvmon.TVData as TVData
# Hack required by timeValueGraph
timeValueGraph.Global.persistentData = {}
import Gen2.senvmon.resourceMon as rmon
import Gen2.senvmon.direction as dr

from PyQt4 import QtGui, QtCore
from ginga.qtw import QtHelp

al_ag_bright = 'TSCL.AG1Intensity'
al_sv_bright = 'TSCL.SV1Intensity'

class Brightness(PlBase.Plugin):

    def build_gui(self, container):
        self.root = container
        #self.root.setStyleSheet("QWidget { background: lightblue }")

        self.statusDict = {}

        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        container.setLayout(layout)

        split = QtGui.QSplitter()
        split.setOrientation(QtCore.Qt.Vertical)
        ## split.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Ignored,
        ##                                       QtGui.QSizePolicy.Ignored))
        
        #self.w = Bunch.Bunch()

        envi_file = os.path.join(os.environ['GEN2COMMON'], 'db', 'test.shelve')  
        key='brightness'

        try:
            load_data(envi_file, key, 3600, self.logger)
        except Exception, e:
            self.logger.error("Error loading persistent data: %s" % (str(e)))

        self.sc = timeValueGraph.TVCoordinator(self.statusDict, 10, envi_file,
                                               key, self.logger)
        coordinator = self.sc

        vbox = QtHelp.VBox()

        # Brightness
        b = StatusGraph.StatusGraph(title="Brightness",
                                    key="brightness",
                                    size=(350, 150),
                                    statusKeys=(al_ag_bright, al_sv_bright),
                                    statusFormats=("AG: %0.0f", "SV: %0.0f"),
                                    alarmValues = (0, 999999),
                                    warningValues = (0,0),
                                    displayTime=True,
                                    backgroundColor=QtGui.QColor(245,255,252),
                                    logger=self.logger)

        coordinator.addGraph(b)
        vbox.addWidget(b, stretch=1)
        split.addWidget(vbox)

        #layout.addWidget(split, stretch=1, alignment=QtCore.Qt.AlignTop)
        layout.addWidget(split, stretch=1)
        

    def start(self):
        aliases = [ al_ag_bright, al_sv_bright]

        self.controller.register_select('brightness', self.update, aliases)
        now = time.time()
        self.sc.setTimeRange(now - (3600*4), now, calcTimeRange=True)
        self.sc.timerEvent(False)

    def update(self, statusDict):
        self.logger.debug('brightness. %s' %str(statusDict))
        self.statusDict.update(statusDict)
        try:
            self.sc.timerEvent(True)
        except Exception, e:
            self.logger.error("Error updating status: %s" % (str(e)))
            
    def __str__(self):
        return 'brightness'


def __set_data(envi_data, key, logger):

    try:
        Global.persistentData=envi_data[key]
        #print 'GETDATA:%d' % len(Global.persistentData['temperature'][0])
        #print 'GETDATA:%s' % Global.persistentData 
        logger.debug('getting data for key %s' %key)
        #print envi_data[key_str]
    except KeyError,e:
        Global.persistentData = {}
        logger.debug('getting data for no key')


def __restore_data(envi_data, key, logger):
    try:
        envi_data[key]=Global.persistentData
    except Exception,e:
        logger.warn('no key found...  %s' %e)


def load_data(envi_file,  key, datapoint, logger):
    ''' loading data '''

    # open/load shelve file 
    try:
        logger.debug('opening env data...')   
        envi_data = shelve.open(envi_file)

        __set_data(envi_data, key, logger)  

        __remove_old_data(datapoint, logger)

        __restore_data(envi_data, key,logger)
 
        envi_data.close()
  
    except IOError,e:
        logger.warn('warn  opening envi_data %s' %str(e))
        Global.persistentData = {}
        #envi_data.close()

def __remove_old_data(datapoint, logger):
 
    for k in Global.persistentData.keys():
         logger.debug('removing key=%s' %k)
         for val in range(len(Global.persistentData[k])):
              num_points=len(Global.persistentData[k][val])

              logger.debug('length of datapoint=%d' %num_points )
              if num_points  >  datapoint:
                  del Global.persistentData[k][val][:num_points-datapoint]     
                  #logger.debug('after  deleting datapoint=%s' % Global.persistentData[k][val])
                  logger.debug('length of datapoint=%d' %len(Global.persistentData[k][val]) )

    
#END

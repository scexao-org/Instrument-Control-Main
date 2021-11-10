import PlBase
import Calprobe
from PyQt4 import QtGui, QtCore

class CalprobePlugin(PlBase.Plugin):
    """ Cal Source Probe Plugin """
    aliases=['TSCL.CAL_POS']
  
    def build_gui(self, container):
        self.root = container

        qtwidget = QtGui.QWidget()

        self.calprobe = Calprobe.CalProbeDisplay(qtwidget, logger=self.logger)
       
        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.calprobe, stretch=1)
        container.setLayout(layout)
 
    def start(self):
        self.controller.register_select('calprobe', self.update, \
                                         CalprobePlugin.aliases)

    def update(self, statusDict):
        self.logger.debug('status=%s' %str(statusDict))
        try:
            probe = statusDict.get(CalprobePlugin.aliases[0])

            self.calprobe.update_calprobe(probe=probe)
        except Exception as e:
            self.logger.error('error: updating status. %s' %str(e))
            

import PlBase
import EnvMon
from PyQt4 import QtGui, QtCore

class EnvMonPlugin(PlBase.Plugin):
    """ EnvMon """
    aliases = ['TSCL.WINDD', 'STATS.AZ_ADJ', 'TSCL.WINDS_O',  'TSCL.WINDS_I', \
               'TSCL.TEMP_O',  'TSCL.TEMP_I', 'TSCL.HUMI_O', 'TSCL.HUMI_I', \
               "STATL.DEW_POINT_O", 'TSCL.M1_TEMP', \
               'TSCL.TOPRING_WINDS_F', 'TSCL.TOPRING_WINDS_R']

    def build_gui(self, container):
        self.root = container

        qtwidget = QtGui.QWidget()

        self.em = EnvMon.EnvMon(qtwidget, logger=self.logger)
       
        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.em, stretch=1)
        container.setLayout(layout)
 
    def start(self):
        self.controller.register_select('envmon', self.update, EnvMonPlugin.aliases)
        self.em.start()

    def update(self, statusDict):
        self.logger.debug('status=%s' %str(statusDict))
        self.em.update_envmon(status_dict=statusDict)


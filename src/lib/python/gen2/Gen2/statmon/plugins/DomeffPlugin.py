import PlBase
import Domeff
from PyQt4 import QtGui, QtCore

class DomeffPlugin(PlBase.Plugin):
    """ Domeff """
    aliases=['TSCV.DomeFF_A', 'TSCV.DomeFF_1B', 'TSCV.DomeFF_2B', \
             'TSCV.DomeFF_3B', 'TSCV.DomeFF_4B']
  
    def build_gui(self, container):
        self.root = container

        qtwidget = QtGui.QWidget()

        self.domeff=Domeff.DomeffDisplay(qtwidget, logger=self.logger)
       
        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.domeff,stretch=1)
        container.setLayout(layout)
 
    def start(self):
        self.controller.register_select('domeff', self.update, \
                                         DomeffPlugin.aliases)

    def update(self, statusDict):
        self.logger.debug('status=%s' %str(statusDict))
        try:
            ff_a = statusDict.get(DomeffPlugin.aliases[0])
            ff_1b = statusDict.get(DomeffPlugin.aliases[1])
            ff_2b = statusDict.get(DomeffPlugin.aliases[2])
            ff_3b = statusDict.get(DomeffPlugin.aliases[3])
            ff_4b = statusDict.get(DomeffPlugin.aliases[4])

            self.domeff.update_domeff(ff_a=ff_a, ff_1b=ff_1b, ff_2b=ff_2b,\
                                      ff_3b=ff_3b, ff_4b=ff_4b) 
        except Exception as e:
            self.logger.error('error: updating status. %s' %str(e))
            


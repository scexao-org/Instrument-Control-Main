import PlBase
import Resource
from PyQt4 import QtGui, QtCore

class ResourcePlugin(PlBase.Plugin):
    """ Resource water, oil """
    aliases=['TSCV.WATER', 'TSCV.OIL']
  
    def build_gui(self, container):
        self.root = container

        qtwidget = QtGui.QWidget()

        self.resource = Resource.ResourceDisplay(qtwidget, logger=self.logger)
       
        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.resource, stretch=1)
        container.setLayout(layout)
 
    def start(self):
        self.controller.register_select('resource', self.update, \
                                         ResourcePlugin.aliases)

    def update(self, statusDict):
        self.logger.debug('status=%s' %str(statusDict))
        water = statusDict.get(ResourcePlugin.aliases[0])
        oil = statusDict.get(ResourcePlugin.aliases[1])

        try:
            self.resource.update_resource(water=water, oil=oil) 
        except Exception as e:
            self.logger.error('error: updating status. %s' %str(e))
            


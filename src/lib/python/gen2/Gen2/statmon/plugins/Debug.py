#
# Debug.py -- Debugging plugin for StatMon
# 
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Apr  5 14:18:45 HST 2012
#]
#
import PlBase

from PyQt4 import QtGui, QtCore

class Debug(PlBase.Plugin):

    def build_gui(self, container):
        self.root = container

        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        container.setLayout(layout)
        
        self.msgFont = QtGui.QFont("Fixed", 14)
        tw = QtGui.QTextEdit()
        tw.setReadOnly(True)
        tw.setCurrentFont(self.msgFont)
        self.tw = tw
        self.history = []
        self.histmax = 10
         
        sw = QtGui.QScrollArea()
        sw.setWidgetResizable(True)
        sw.setWidget(self.tw)

        layout.addWidget(sw, stretch=1)
        sw.show()

        self.entry = QtGui.QLineEdit()
        layout.addWidget(self.entry, stretch=0)
        self.entry.returnPressed.connect(lambda: self.command_cb(self.entry))

    def start(self):
        pass

    def closePlugin(self, plname):
        self.view.close_plugin(plname)
        return True    

    def reloadPlugin(self, plname):
        #self.view.close_plugin(plname)
        self.view.reload_plugin(plname)
        return True
            
    def reloadModule(self, name):
        self.controller.mm.loadModule(name)
        return True

    def command(self, cmdstr):
        self.logger.debug("Command is '%s'" % (cmdstr))
        # Evaluate command
        try:
            result = eval(cmdstr)

        except Exception, e:
            result = str(e)
            # TODO: add traceback

        # Append command to history
        self.history.append('>>> ' + cmdstr + '\n' + str(result))

        # Remove all history past history size
        self.history = self.history[-self.histmax:]
        # Update text widget
        self.tw.setText('\n'.join(self.history))
        
    def command_cb(self, w):
        # TODO: implement a readline/history type function
        cmdstr = str(w.text()).strip()
        self.command(cmdstr)
        w.setText("")
        
    def __str__(self):
        return 'debug'
    
#END

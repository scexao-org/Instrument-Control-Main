#
# Viewer.py -- Qt display handler for StatMon.
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Apr 15 17:12:49 HST 2013
#]
#
# stdlib imports
import sys, os
import Queue
import traceback

# GUI imports
from ginga.qtw import QtHelp
from PyQt4 import QtGui, QtCore
from ginga.misc import Bunch

moduleHome = os.path.split(sys.modules[__name__].__file__)[0]
icon_path = os.path.abspath(os.path.join(moduleHome, '..', 'icons'))
rc_file = os.path.join(moduleHome, "qt_rc")


class ViewError(Exception):
    """Exception raised for errors in this module."""
    pass

class Viewer(object):
     
    def __init__(self):
        # Create the top level Qt app
        QtGui.QApplication.setGraphicsSystem('raster')
        app = QtGui.QApplication([])
        app.connect(app, QtCore.SIGNAL('lastWindowClosed()'),
                    self.quit)
        self.app = app
        # read in any module-level style sheet
        if os.path.exists(rc_file):
            self.app.setStyleSheet(rc_file)
        
        # Get screen size
        desktop = app.desktop()
        #rect = desktop.screenGeometry()
        rect = desktop.availableGeometry()
        size = rect.size()
        self.screen_wd = size.width()
        self.screen_ht = size.height()

        # defaults for height and width
        self.default_height = min(900, self.screen_ht - 100)
        self.default_width  = min(1600, self.screen_wd)

        # This is where all the widgets get stored
        self.w = Bunch.Bunch()
        self.iconpath = icon_path

        # Default fonts for our all
        self.font = Bunch.Bunch(mono12=QtGui.QFont('Monospace', 12),
                                mono11=QtGui.QFont('Monospace', 11))

        QtGui.QToolTip.setFont(self.font.mono11)

        # For now...
        self.controller = self

        # dictionary of plugins
        self.plugins = {}
        

    def build_toplevel(self, layout):
        # Create root window and add delete/destroy callbacks
        root = QtGui.QWidget()
        root.connect(root, QtCore.SIGNAL('closed()'), 
                     self.quit)
        root.resize(self.default_width, self.default_height)
        
        self.w.root = root

        # access main frame
        vbox = QtGui.QVBoxLayout()
        vbox.setContentsMargins(2, 2, 2, 2)
        vbox.setSpacing(2)
        root.setLayout(vbox)
        self.w.mframe = vbox

        # Add menubar and menus, if desired
        self.add_menus()

        # Dynamically create the desktop layout
        self.ds = QtHelp.Desktop()
        self.w.mvbox = self.ds.make_desktop(layout, widgetDict=self.w)
        self.w.mframe.addWidget(self.w.mvbox, stretch=1)

        # Add popup dialogs
        self.add_dialogs()

        # Add status bar, if desired
        self.add_statusbar()

        return root
    
        
    def add_menus(self):
        """Subclass should override this to create a custom menu bar
        or to omit a menu bar.
        """
        pass

    def add_dialogs(self):
        """Subclass should override this to create their own necessary
        dialogs.
        """
        pass

    def add_statusbar(self):
        """Subclass should override this to create their own status bar
        or to omit a status bar.
        """
        self.w.status = QtGui.QStatusBar()
        self.w.mframe.addWidget(self.w.status)

    def set_titlebar(self, text):
        """Sets the title of the top level window.
        """
        self.w.root.setWindowTitle(text)
        
    def load_plugin(self, pluginName, moduleName, className, wsName, tabName):

        widget = QtGui.QWidget()

        # Record plugin info
        canonicalName = pluginName.lower()
        bnch = Bunch.Bunch(caseless=True,
                           name=canonicalName, officialname=pluginName,
                           modulename=moduleName, classname=className,
                           wsname=wsName, tabname=tabName, widget=widget)
        
        self.plugins[pluginName] = bnch
        
        try:
            module = self.mm.loadModule(moduleName)

            # Look up the module and class
            module = self.mm.getModule(moduleName)
            klass = getattr(module, className)

            # instantiate the class
            pluginObj = klass(self.model, self, self.controller,
                              self.logger)

            # Save a reference to the plugin object so we can use it
            # later
            self.plugins[pluginName].setvals(obj=pluginObj)

            # Build the plugin GUI
            pluginObj.build_gui(widget)

            # Add the widget to a workspace and save the tab name in
            # case we need to delete the widget later on.
            dsTabName = self.ds.add_page(wsName, widget, 2, tabName)
            self.plugins[pluginName].setvals(wsTabName=dsTabName)

            # Start the plugin
            pluginObj.start()

        except Exception, e:
            errstr = "Plugin '%s' failed to initialize: %s" % (
                className, str(e))
            self.logger.error(errstr)
            try:
                (type, value, tb) = sys.exc_info()
                tb_str = "\n".join(traceback.format_tb(tb))
                self.logger.error("Traceback:\n%s" % (tb_str))
                
            except Exception, e:
                tb_str = "Traceback information unavailable."
                self.logger.error(tb_str)
                
            vbox = QtGui.QVBoxLayout()
            vbox.setContentsMargins(4, 4, 4, 4)
            vbox.setSpacing(0)
            widget.setLayout(vbox)
            
            textw = QtGui.QTextEdit()
            textw.append(str(e) + '\n')
            textw.append(tb_str)
            textw.setReadOnly(True)
            vbox.addWidget(textw, stretch=1)
                
            self.ds.add_page(wsName, widget, 2, tabName)

    def close_plugin(self, pluginName):
        bnch = self.plugins[pluginName]
        self.logger.info('calling stop() for plugin %s' % (pluginName))
        bnch.obj.stop()
        self.logger.info('calling remove_tab() for plugin %s' % (pluginName))
        self.ds.remove_tab(bnch.wsTabName)
        return True
     
    def close_all_plugins(self):
        for pluginName in self.plugins:
            try:
                self.close_plugin(pluginName)
            except Exception as e:
                self.logger.error('Exception while calling stop for plugin %s: %s' % (pluginName, e))
        return True
    
    def reload_plugin(self, pluginName):
        pInfo = self.plugins[pluginName]
        try:
            self.close_plugin(pluginName)
        except:
            pass
        
        return self.load_plugin(pInfo.officialname, pInfo.modulename,
                                pInfo.classname, pInfo.wsname,
                                pInfo.tabname)
        
    def statusMsg(self, msg, duration=None, iserror=False):
        """Send a message to the status bar.  If (duration) is specified
        then the message will disappear after that many seconds.
        """
        # TODO: turn background of bar red for duration if iserror==True
        if duration:
            self.w.status.showMessage(msg, duration*1000)
        else:
            self.w.status.showMessage(msg)

    def error(self, text, duration=None):
        """Convenience function to log an error to the error log and also
        display it in the status bar as an error.
        """
        self.logger.error(text)
        self.statusMsg(text, duration=duration, iserror=True)

    def setPos(self, x, y):
        """Set the position of the root window."""
        self.w.root.move(x, y)

    def setSize(self, w, h):
        """Set the size of the root window."""
        self.w.root.resize(w, h)

    def setGeometry(self, geometry):
        """Set the geometry of the root window.  (geometry) is expected to
        be an X-style geometry string; e.g. 1000x900+100+200
        """
        # Painful translation of X window geometry specification
        # into correct calls to Qt
        coords = geometry.replace('+', ' +')
        coords = coords.replace('-', ' -')
        coords = coords.split()
        if 'x' in coords[0]:
            # spec includes dimensions
            dim = coords[0]
            coords = coords[1:]
        else:
            # spec is position only
            dim = None

        if dim != None:
            # user specified dimensions
            dim = map(int, dim.split('x'))
            self.setSize(*dim)

        if len(coords) > 0:
            # user specified position
            coords = map(int, coords)
            self.setPos(*coords)

    def update_pending(self, timeout=0.0):
        """Routine to process pending Qt events."""
        try:
            self.app.processEvents()
        except Exception, e:
            self.logger.error(str(e))
            # TODO: traceback!
        
        done = False
        while not done:
            #print "PROCESSING IN-BAND"
            # Process "in-band" Qt events
            try:
                future = self.gui_queue.get(block=True, 
                                            timeout=timeout)

                # Execute the GUI method
                try:
                    try:
                        res = future.thaw(suppress_exception=False)

                    except Exception, e:
                        future.resolve(e)

                        self.logger.error("gui error: %s" % str(e))
                        try:
                            (type, value, tb) = sys.exc_info()
                            tb_str = "".join(traceback.format_tb(tb))
                            self.logger.error("Traceback:\n%s" % (tb_str))

                        except Exception, e:
                            self.logger.error("Traceback information unavailable.")

                finally:
                    pass

                    
            except Queue.Empty:
                done = True
                
            except Exception, e:
                self.logger.error("Main GUI loop error: %s" % str(e))
                #pass
                
        # Process "out-of-band" events
        #print "PROCESSING OUT-BAND"
        try:
            self.app.processEvents()
        except Exception, e:
            self.logger.error(str(e))
            # TODO: traceback!


    ####################################################
    # CALLBACKS
    ####################################################
    
    def quit(self, *args):
        """Quit the application.
        """
        self.stop()
        return True


# END

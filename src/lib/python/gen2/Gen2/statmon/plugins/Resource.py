#!/usr/bin/env python

import sys
import os

from CanvasLabel import Canvas, QtCore, QtGui, Qt, ERROR

import ssdlog

progname = os.path.basename(sys.argv[0])

    
class Resource(Canvas):
    ''' Water/Oil Storage'''
    def __init__(self, parent=None, logger=None):
        super( Resource, self).__init__(parent=parent, fs=10, width=275,\
                                     height=25, align='vcenter', \
                                     weight='bold', logger=logger)
 
    def update_resource(self,  resource):
        ''' resource= TSCV.WATER | TSCV.OIL  '''
                  
        self.logger.debug('resource=%s' %(str(resource)))

        color=self.normal

        if resource == 0:
            text = 'Normal'
        elif resource >= 1.0:
            text = 'HIGH ALARM'
            color = self.alarm
        elif resource <= -1.0:
            text = 'LOW ALARM'
            color = self.alarm
        else:
            text = 'Undefined'
            color = self.alarm

        # #self.setText('CalProbe: ')
        self.setText(text)
        self.setStyleSheet("QLabel {color :%s ; background-color:%s }" \
                           %(color, self.bg))


class WaterStorageDisplay(QtGui.QWidget):
    ''' WaterStorage  '''
    def __init__(self, parent=None, logger=None):
        super(WaterStorageDisplay, self).__init__(parent)
   
        self.water_label = Canvas(parent=parent, fs=10, width=175,\
                                height=25, align='vcenter', weight='bold', \
                                logger=logger)

        self.water_label.setText('Water Storage')
        self.water_label.setIndent(15)

        self.water =  Resource(parent=parent, logger=logger)
        self.__set_layout() 

    def __set_layout(self):
        objlayout = QtGui.QHBoxLayout()
        objlayout.setSpacing(0) 
        objlayout.setMargin(0)
        objlayout.addWidget(self.water_label)
        objlayout.addWidget(self.water)
        self.setLayout(objlayout)

    def update_water(self, water):
        self.water.update_resource(resource=water)    

    def tick(self):
        ''' testing solo mode '''
        import random  
        random.seed()

        water = random.randrange(-2, 2)
        self.update_water(water)


class OilStorageDisplay(QtGui.QWidget):
    def __init__(self, parent=None, logger=None):
        super(OilStorageDisplay, self).__init__(parent)
   
        self.oil_label = Canvas(parent=parent, fs=10, width=175,\
                                height=25, align='vcenter', weight='bold', \
                                logger=logger)

        self.oil_label.setText('Oil Storage')
        self.oil_label.setIndent(15)

        self.oil = Resource(parent=parent, logger=logger)
        self.__set_layout() 

    def __set_layout(self):
        objlayout = QtGui.QHBoxLayout()
        objlayout.setSpacing(0) 
        objlayout.setMargin(0)
        objlayout.addWidget(self.oil_label)
        objlayout.addWidget(self.oil)
        self.setLayout(objlayout)

    def update_oil(self, oil):
        self.oil.update_resource(resource=oil)    

    def tick(self):
        ''' testing solo mode '''
        import random  
        random.seed()

        oil = random.randrange(-2, 2)
        self.update_oil(oil)


class ResourceDisplay(QtGui.QWidget):
    def __init__(self, parent=None, logger=None):
        super(ResourceDisplay, self).__init__(parent)
   
        self.water =  WaterStorageDisplay(parent=parent, logger=logger)
        self.oil = OilStorageDisplay(parent=parent, logger=logger)

        self.__set_layout() 

    def __set_layout(self):
        objlayout = QtGui.QVBoxLayout()
        objlayout.setSpacing(1) 
        objlayout.setMargin(0)
        objlayout.addWidget(self.water)
        objlayout.addWidget(self.oil)
        self.setLayout(objlayout)

    def update_resource(self, water, oil):
        self.water.update_water(water=water) 
        self.oil.update_oil(oil=oil)    

    def tick(self):
        ''' testing solo mode '''
        import random  
        random.seed()

        water = oil = random.randrange(-2, 2)
        self.update_resource(water, oil)




def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('resource', options)
 
    class AppWindow(QtGui.QMainWindow):
        def __init__(self):
            super(AppWindow, self).__init__()
            self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.w=450; self.h=25;
            self.init_ui()

        def init_ui(self):
            self.resize(self.w, self.h)

            self.main_widget = QtGui.QWidget()
            l = QtGui.QVBoxLayout(self.main_widget)
            l.setMargin(0) 
            l.setSpacing(0)
 
            if options.mode == 'water':
                r = WaterStorageDisplay(parent=self.main_widget, logger=logger)
            elif options.mode == 'oil':
                r = OilStorageDisplay(parent=self.main_widget, logger=logger)
            else:
                r = ResourceDisplay(parent=self.main_widget, logger=logger)

            l.addWidget(r)

            timer = QtCore.QTimer(self)
            QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"), r.tick)
            timer.start(options.interval)

            self.main_widget.setFocus()
            self.setCentralWidget(self.main_widget) 
            self.statusBar().showMessage("%s starting..." %options.mode, options.interval)

        def closeEvent(self, ce):
            self.close()

    try:
        qApp = QtGui.QApplication(sys.argv)
        aw = AppWindow()
        print 'state'
        #state = State(logger=logger)  
        aw.setWindowTitle("%s" % progname)
        aw.show()
        #state.show()
        print 'show'
        sys.exit(qApp.exec_())

    except KeyboardInterrupt, e:
        logger.warn('keyboard interruption....')
        sys.exit(0)



if __name__ == '__main__':
    # Create the base frame for the widgets

    from optparse import OptionParser
 
    usage = "usage: %prog [options] command [args]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--display", dest="display", metavar="HOST:N",
                      help="Use X display on HOST:N")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--interval", dest="interval", type='int',
                      default=1000,
                      help="Inverval for plotting(milli sec).")
    # note: there are sv/pir plotting, but mode ag uses the same code.  
    optprs.add_option("--mode", dest="mode",
                      default='resource',
                      help="Specify a resource mode [water| oil | resource ]")

    ssdlog.addlogopts(optprs)
    
    (options, args) = optprs.parse_args()

    if len(args) != 0:
        optprs.error("incorrect number of arguments")

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


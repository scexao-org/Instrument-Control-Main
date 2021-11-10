#!/usr/bin/env python

import sys
import os
import math

from CanvasLabel import Canvas, QtCore, QtGui, Qt, ERROR

import ssdlog

progname = os.path.basename(sys.argv[0])

    
class Airmass(Canvas):
    ''' Air mass   '''
    def __init__(self, parent=None, logger=None):
        super(Airmass, self).__init__(parent=parent, fs=10, width=275,\
                                     height=25, align='vcenter', \
                                     weight='bold', logger=logger)
 
        self.setAlignment(QtCore.Qt.AlignVCenter)

    def get_airmass(self, el):
        
        try:
            assert 1.0 <= el <=179.0
        except AssertionError as e:
            self.logger.debug('error: airmass el range. %s' %(str(e)))
            am = None
        else:
            zd = 90.0 - el
            rad = math.radians(zd)
            sz = 1.0 / math.cos(rad)
            sz1 = sz - 1.0
            am = sz - 0.0018167 * sz1 - 0.002875 * sz1**2 - 0.0008083 * sz1**3
        finally:
            return am

    def update_airmass(self, el):
        ''' el = TSCS.EL '''
                  
        self.logger.debug('airmass el=%s' %(str(el)))

        color=self.normal
        airmass = self.get_airmass(el)
     
        if not airmass in ERROR:
            text = '{0:.2f}'.format(airmass)
        else:
            text = '{0}'.format('Undefined')
            color = self.alarm
            self.logger.error('error: airmass=%s' %(str(airmass)))

        #self.setText('CalProbe: ')
        self.setText(text)
        self.setStyleSheet("QLabel {color :%s ; background-color:%s }" \
                           %(color, self.bg))


class AirmassDisplay(QtGui.QWidget):
    def __init__(self, parent=None, logger=None):
        super(AirmassDisplay, self).__init__(parent)
   
        self.airmass_label = Canvas(parent=parent, fs=10, width=175,\
                                height=25, align='vcenter', weight='bold', \
                                logger=logger)

        self.airmass_label.setText('AirMass')
        self.airmass_label.setIndent(15)

        self.airmass = Airmass(parent=parent, logger=logger)
        self.__set_layout() 

    def __set_layout(self):
        layout = QtGui.QHBoxLayout()
        layout.setSpacing(0) 
        layout.setMargin(0)
        layout.addWidget(self.airmass_label)
        layout.addWidget(self.airmass)
        self.setLayout(layout)

    def update_airmass(self, el):
        self.airmass.update_airmass(el)

    def tick(self):
        ''' testing solo mode '''
        import random  

        el = random.uniform(-20.0, 200)
        if el < -10 or el > 190:
            el = '##STATNONE##'    

        self.update_airmass(el)


def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('state', options)
 
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
            p = AirmassDisplay(parent=self.main_widget, logger=logger)
            l.addWidget(p)

            timer = QtCore.QTimer(self)
            QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"), p.tick)
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
                      default='ag',
                      help="Specify a plotting mode [ag | sv | pir | fmos]")

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


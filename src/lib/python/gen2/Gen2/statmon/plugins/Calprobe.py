#!/usr/bin/env python

import sys
import os

from CanvasLabel import Canvas, QtCore, QtGui, Qt, ERROR

import ssdlog

progname = os.path.basename(sys.argv[0])
    
class CalProbe(Canvas):
    ''' Cal Source Probe  '''
    def __init__(self, parent=None, logger=None):
        super(CalProbe, self).__init__(parent=parent, fs=10, width=200,\
                                       height=25, align='vcenter', \
                                       weight='bold', logger=logger)

    def update_calprobe(self, probe):
        ''' probe = TSCL.CAL_POS '''

        self.logger.debug('probe=%s' %(str(probe)))

        color=self.normal
        try:
            text = '{0:+3.3f} mm'.format(probe)
        except Exception:
            text = 'Undefined'
            color = self.alarm
            self.logger.error('error: calprobe undef. probe=%s' %(str(probe)))

        #self.setText('CalProbe: ')
        self.setText(text)
        self.setStyleSheet("QLabel {color :%s ; background-color:%s }" \
                           %(color, self.bg))

class CalProbeDisplay(QtGui.QWidget):
    def __init__(self, parent=None, logger=None):
        super(CalProbeDisplay, self).__init__(parent)
   
        self.calprobe_label = Canvas(parent=parent, fs=10, width=175,\
                                height=25, align='vcenter', \
                                weight='bold', logger=logger)

        self.calprobe_label.setText('CalProbe')
        self.calprobe_label.setIndent(15)

        self.calprobe = CalProbe(parent=parent, logger=logger)
        self.__set_layout() 

    def __set_layout(self):
        layout = QtGui.QHBoxLayout()
        layout.setSpacing(0) 
        layout.setMargin(0)
        layout.addWidget(self.calprobe_label)
        layout.addWidget(self.calprobe)
        self.setLayout(layout)

    def update_calprobe(self, probe):
        self.calprobe.update_calprobe(probe)

    def tick(self):
        ''' testing solo mode '''
        import random  
        random.seed()

        indx = random.randrange(0, 35)
        indx2 = random.randrange(0, 5) 

        foci = [0x01000000, 0x02000000, 0x04000000, 0x08000000,
                0x10000000, 0x20000000, 0x40000000, 0x80000000L,
                0x00010000, 0x00020000, 0x00040000, 0x00080000,
                0x00100000, 0x00200000, 0x00400000, 0x00800000,
                0x00000100, 0x00000200, 0x00000400, 0x00000800,
                0x00001000, 0x00002000, 0x00004000, 0x00008000,
                0x00000001, 0x00000002, 0x00000004, 0x00000008, 
                0x00000010, 0x00000000, 
                "Unknown", None, '##STATNONE##', '##NODATA##', '##ERROR##']
 
        foci2 = [0x01, 0x02, 0x04, "Unknown", None, '##STATNONE##', \
                 '##NODATA##', 0x08, '##ERROR##']
        try:
            focus = foci[indx]
            focus2 = foci2[indx2]
        except Exception as e:
            focus = None
            focus2 = None
            print e
        probe = random.random()*random.randrange(-20, 20)
        self.update_calprobe(probe)


def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('state', options)
 
    class AppWindow(QtGui.QMainWindow):
        def __init__(self):
            super(AppWindow, self).__init__()
            self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.w=275; self.h=25;
            self.init_ui()

        def init_ui(self):
            self.resize(self.w, self.h)

            self.main_widget = QtGui.QWidget()
            l = QtGui.QVBoxLayout(self.main_widget)
            l.setMargin(0) 
            l.setSpacing(0)
            m2 = CalProbeDisplay(parent=self.main_widget, logger=logger)
            l.addWidget(m2)

            timer = QtCore.QTimer(self)
            QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"), m2.tick)
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


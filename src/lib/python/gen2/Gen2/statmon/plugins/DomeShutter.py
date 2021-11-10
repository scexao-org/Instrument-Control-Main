#!/usr/bin/env python

import sys
import os
import ssdlog
from CanvasLabel import Canvas, QtCore, QtGui, Qt, ERROR


progname = os.path.basename(sys.argv[0])


class DomeShutter(Canvas):

    ''' state of the DomeShutter  '''
    def __init__(self, parent=None, logger=None):
        super(DomeShutter, self).__init__(parent=parent, fs=10, width=500, \
                                          height=15, fg='white', bg='black', \
                                          weight='bold', logger=logger )

    def update_dome(self, dome):
        ''' dome=TSCV.DomeShutter '''
        self.logger.debug('dome=%s' %(str(dome)))

        if dome in ERROR:
            self.logger.error('error: dome=%s' %(str(dome)))   
            text='Dome Shutter Undefiend'
            bg=self.alarm
            fg=self.fg
        elif dome == 0x50: # dome shutter open
            self.logger.debug('open dome=%s' %(str(dome)))
            text='Dome Shutter Open'
            bg=self.fg  
            fg=self.normal
        elif dome == 0x00: # dome shuuter close
            self.logger.debug('close dome=%s' %(str(dome)))
            text='Dome Shutter Closed'
            bg=self.bg
            fg=self.fg
        else: # dome shutter  partial
            self.logger.debug('partial dome=%s' %(str(dome)))
            text='Dome Shuter Partial'
            bg=self.warn
            fg=self.fg

        self.logger.debug('text=%s fg=%s bg=%s' %(text, fg, bg))      

        self.setStyleSheet("QLabel {color: %s; background-color: %s}" %(fg, bg))
        self.setText(text)


    def tick(self):
        ''' testing solo mode '''
        self.logger.debug('ticking...')
        import random  
        random.seed()

        indx=random.randrange(0,12)
        dome=['##NODATA##', 0x50, 0xA0, None,  0x20, 'Unkonw', \
              0x80, 0x90, '##STATNONE##', 0x00, 0x10, '##ERROR##']

        try:
            dome=dome[indx]
            self.update_dome(dome)
        except Exception as e:
            self.logger.error('error: %s' %e)
            pass

def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('state', options)
 
    class AppWindow(QtGui.QMainWindow):
        def __init__(self):
            super(AppWindow, self).__init__()
            self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.w=500; self.h=15;
            self.init_ui()

        def init_ui(self):
            self.resize(self.w, self.h)

            self.main_widget = QtGui.QWidget()
            l = QtGui.QVBoxLayout(self.main_widget)
            l.setMargin(0) 
            l.setSpacing(0)
            dome = DomeShutter(parent=self.main_widget, logger=logger)
            l.addWidget(dome)

            timer = QtCore.QTimer(self)
            QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"), dome.tick)
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


#!/usr/bin/env python

import sys
import os
import math

from CanvasLabel import Canvas, QtCore, QtGui, Qt, ERROR

import ssdlog

progname = os.path.basename(sys.argv[0])

    
class Pa(Canvas):
    ''' Position Angle   '''
    def __init__(self, parent=None, logger=None):
        super(Pa, self).__init__(parent=parent, fs=10, width=200,\
                                     height=25, align='vcenter', \
                                     weight='bold', logger=logger)
 
    def convert_to_float(self, cmd_diff):
   
        try:
            cmd_diff = math.fabs(float(cmd_diff)) 
        except Exception as e:
            cmd_diff = None
            self.logger.debug('error: cmd_diff to float. %s' %(str(e)))
        finally:
            return cmd_diff

    def get_calc_pa(self, pa):
        
        try:
            pa = ((pa + 540.0) % 360.0) - 180.0
        except Exception as e:
            self.logger.debug('error: pa calc. %s' %(str(e)))
            pa = None
        finally:
            return pa

    def update_pa(self, pa, cmd_diff):
        ''' pa = TSCL.INSROTPA_PF # POPT
            pa = TSCL.InsRotPA  # CS
            pa = TSCL.ImgRotPA  # NS
            cmd_diff = STATS.ROTDIF_PF # POPT
            cmd_diff = STATS.ROTDIF # CS/NS
        '''
                  
        self.logger.debug('position angle pa=%s cmd_diff=%s' %(str(pa), str(cmd_diff)))

        color=self.normal
        pa = self.get_calc_pa(pa)
        cmd_diff = self.convert_to_float(cmd_diff)     

        diff = 0.1
        if not (pa in ERROR or cmd_diff in ERROR):
            text = '{0:.2f} deg'.format(pa)
            if cmd_diff >= diff:
                color = self.warn
                #text = '{0:.2f} deg.  cmd_diff={1:.2f}>={2}'.format(pa, cmd_diff, diff)
                text = '{0:.2f} deg  Diff:{1:.2f}'.format(pa, cmd_diff)     
        else:
            text = '{0}'.format('Undefined')
            color = self.alarm
            self.logger.error('error: pa=%s cmd_diff=%s' %(str(pa), str(cmd_diff)))

        #self.setText('CalProbe: ')
        self.setText(text)
        self.setStyleSheet("QLabel {color :%s ; background-color:%s }" \
                           %(color, self.bg))


class PaDisplay(QtGui.QWidget):
    def __init__(self, parent=None, logger=None):
        super(PaDisplay, self).__init__(parent)
   
        self.pa_label = Canvas(parent=parent, fs=10, width=175,\
                                height=25, align='vcenter', \
                                weight='bold', logger=logger)

        self.pa_label.setText('Position Angle')
        self.pa_label.setIndent(15)

        self.pa = Pa(parent=parent, logger=logger)
        self.__set_layout() 

    def __set_layout(self):
        layout = QtGui.QHBoxLayout()
        layout.setSpacing(0) 
        layout.setMargin(0)
        layout.addWidget(self.pa_label)
        layout.addWidget(self.pa)
        self.setLayout(layout)

    def update_pa(self, pa, cmd_diff):
        self.pa.update_pa(pa, cmd_diff)

    def tick(self):
        ''' testing solo mode '''
        import random  

        pa = random.uniform(-100.0, 150)
        cmd_diff = random.uniform(-0.5, 0.5)
        if pa > 100:
            pa = '##STATNONE##'    
        if cmd_diff < -0.3:
            cmd_diff = 'Unknown'
        self.update_pa(pa, cmd_diff)


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
            p = PaDisplay(parent=self.main_widget, logger=logger)
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


#!/usr/bin/env python

import sys
import os

from CanvasLabel import Canvas, QtCore, QtGui, Qt, ERROR

import ssdlog

progname = os.path.basename(sys.argv[0])

    
class Threshold(Canvas):
    ''' Threshold(guiding image)  '''
    def __init__(self, parent=None, logger=None):
        super(Threshold, self).__init__(parent=parent, fs=10, width=85,\
                                     height=25, align='vcenter', \
                                     logger=logger)
 
        self.setIndent(10)
    def update_threshold(self, bottom, ceil):
        ''' bottom = TSCV.AG1_I_BOTTOM | TSCV.SV1_I_BOTTOM
            ceil = TSCV.AG1_I_CEIL | TSCV.SV1_I_CEIL
        '''
                  
        self.logger.debug('bottom=%s ceil=%s' %(str(bottom), str(ceil)))

        color=self.normal

        try:
            text = 'Th: {0:.0f} / {1:.0f}'.format(bottom, ceil)
        except Exception as e:
            text = 'Threshold: {0}'.format('Undefiend') 
            color = self.alarm

        self.setText(text)
        self.setStyleSheet("QLabel {color :%s ; background-color:%s }" \
                           %(color, self.bg))


# class ThresholdDisplay(QtGui.QWidget):
#     def __init__(self, parent=None, logger=None):
#         super(ThresholdDisplay, self).__init__(parent)
   
#         self.exptime_label = Canvas(parent=parent, fs=10, width=10,\
#                                 height=25, align='vcenter', \
#                                 logger=logger)

#         self.threshold_label.setText('Threshold:')
#         self.threshold_label.setIndent(5)
#         #self.propid_label.setAlignment(QtCore.Qt.AlignVCenter) 

#         self.threshold = Threshold(parent=parent, logger=logger)
#         self.__set_layout() 

#     def __set_layout(self):
#         layout = QtGui.QHBoxLayout()
#         layout.setSpacing(1) 
#         layout.setMargin(0)
#         layout.addWidget(self.threshold_label)
#         layout.addWidget(self.threshold)
#         self.setLayout(layout)

#     def update_threshold(self, bottom, ceil):
#         self.threshold.update_threshold(bottom, ceil)

    def tick(self):
        ''' testing solo mode '''
        import random  

        bottom = random.randrange(0, 30000)
        ceil = random.randrange(30000, 70000)
        self.update_threshold(bottom, ceil)

def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('state', options)
 
    class AppWindow(QtGui.QMainWindow):
        def __init__(self):
            super(AppWindow, self).__init__()
            self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.w=170; self.h=25;
            self.init_ui()

        def init_ui(self):
            self.resize(self.w, self.h)

            self.main_widget = QtGui.QWidget()
            l = QtGui.QVBoxLayout(self.main_widget)
            l.setMargin(0) 
            l.setSpacing(0)
            t = Threshold(parent=self.main_widget, logger=logger)
            l.addWidget(t)

            timer = QtCore.QTimer(self)
            QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"), t.tick)
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


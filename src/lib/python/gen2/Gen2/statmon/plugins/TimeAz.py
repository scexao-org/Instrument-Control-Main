#!/usr/bin/env python

import sys
import os

from CanvasLabel import Canvas, QtCore, QtGui, Qt, ERROR

import ssdlog
from TimeEl import to_hour_min 

progname = os.path.basename(sys.argv[0])


class TimeAzLimit(Canvas):
    ''' Time to Azimuth Limit   '''
    def __init__(self, parent=None, logger=None):
        super(TimeAzLimit, self).__init__(parent=parent, fs=10, width=200,\
                                     height=25, align='vcenter', \
                                     weight='bold', logger=logger)
 
    def update_azlimit(self, flag, az):
        ''' flag = TSCL.LIMIT_FLAG 
            az = TSCL.LIMIT_AZ 
        '''

        self.logger.debug('flag=%s az=%s' %(str(flag), str(az)))
        limit_flag = 0x04

        limit = 721 # in minute
        color=self.normal
        #az_txt = ''
 
        if flag in ERROR or az in ERROR:
            text = 'Undifined'
            color = self.alarm
        else:
            if flag & limit_flag:
                if az < limit:
                    #az_txt = "(Limit Az)"
                    limit = az

            if limit > 720.0: # plenty of time. 12 hours
                text = '--h --m' 
            elif limit <= 1: # 0 to 1 minute left
                color = self.alarm
                hm  = to_hour_min(limit)
                text = '%s <= 1m' %(hm) 
            elif limit > 30: # 30 to 720 min left
                hm = to_hour_min(limit)
                text = '%s' %(hm)  
            else: # 1 to 30 min left
                color = self.warn
                hm = to_hour_min(limit)
                text = '%s <= 30m' %(hm)

        self.setText(text)
        self.setStyleSheet("QLabel {color :%s ; background-color:%s }" \
                            %(color, self.bg))

class TimeAzLimitDisplay(QtGui.QWidget):
    def __init__(self, parent=None, logger=None):
        super(TimeAzLimitDisplay, self).__init__(parent)
   
        self.timelimit_label = Canvas(parent=parent, fs=10, width=175,\
                                height=25, align='vcenter', \
                                weight='bold', logger=logger)

        self.timelimit_label.setText('Time to AZ Limit')
        self.timelimit_label.setIndent(15)

        self.azlimit = TimeAzLimit(parent=parent, logger=logger)
        self.__set_layout() 

    def __set_layout(self):
        azlayout = QtGui.QHBoxLayout()
        azlayout.setSpacing(0) 
        azlayout.setMargin(0)
        azlayout.addWidget(self.timelimit_label)
        azlayout.addWidget(self.azlimit)
        self.setLayout(azlayout)

    def update_azlimit(self, flag, az):
        self.azlimit.update_azlimit(flag, az)

    def tick(self):
        ''' testing solo mode '''
        import random  
        
        indx = random.randrange(0,3)
        flag = [0, 4, 4, 'Unknown']
        flag = flag[indx]

        az = random.uniform(0, 760)
        if az > 750.0:
            az = '##NODATA##'
        self.update_azlimit(flag, az)

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
            t = TimeAzLimitDisplay(parent=self.main_widget, logger=logger)
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


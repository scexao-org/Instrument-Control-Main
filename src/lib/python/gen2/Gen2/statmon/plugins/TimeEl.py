#!/usr/bin/env python

import sys
import os

from CanvasLabel import Canvas, QtCore, QtGui, Qt, ERROR

import ssdlog

progname = os.path.basename(sys.argv[0])


def to_hour_min(limit):
    ''' convert to hour-min'''
    try:
        h = limit // 60
        m = limit % 60
    except Exception as e:
        self.logger.error('error: to hour min.  %s' %e)
        hm = '--h --m calc error'
    else:
        hm = '%dh %dm' %(h,m)           
    finally:
        return hm 

class TimeElLimit(Canvas):
    ''' Time to Elevation Limit   '''
    def __init__(self, parent=None, logger=None):
        super(TimeElLimit, self).__init__(parent=parent, fs=10, width=200,\
                                          height=25, align='vcenter', \
                                          weight='bold', logger=logger)
 
    def update_ellimit(self, flag, low, high):
        ''' flag = TSCL.LIMIT_FLAG 
            low = TSCL.LIMIT_EL_LOW 
            high = TSCL.LIMIT_EL_HIGH '''

        self.logger.debug('flag=%s low=%s high=%s' %(str(flag), str(low), str(high)))
        low_limit = 1
        high_limit = 2
        high_limit2 = 3 
        limit = 721 # in minute
        color=self.normal
        el_txt = ''
 
        if flag in ERROR or low in ERROR or high in ERROR:
            text = 'Undifined'
            color = self.alarm
        else:
            if flag is low_limit:
                if low < limit:
                    el_txt = "(Low)"
                    limit = low
            elif flag is high_limit or flag is high_limit2: 
                # high limit seems to be either flag=2 or flag=3
                # need to confirm it. 
                if high < limit:
                    el_txt = "(High)"
                    limit = high

            if limit > 720.0: # plenty of time. 12 hours
                text = '--h --m' 
            elif limit <= 1: # 0 to 1 minute left
                color = self.alarm
                hm  = to_hour_min(limit)
                text = '%s <= 1m %s' %(hm, el_txt) 
            elif limit > 30: # 30 to 720 min left
                hm = to_hour_min(limit)
                text = '%s %s' %(hm, el_txt)  
            else: # 1 to 30 min left
                color = self.warn
                hm = to_hour_min(limit)
                text = '%s <= 30m %s' %(hm, el_txt)

        self.setText(text)
        self.setStyleSheet("QLabel {color :%s ; background-color:%s }" \
                            %(color, self.bg))

class TimeElLimitDisplay(QtGui.QWidget):
    def __init__(self, parent=None, logger=None):
        super(TimeElLimitDisplay, self).__init__(parent)
   
        self.timelimit_label = Canvas(parent=parent, fs=10, width=175,\
                                height=25, align='vcenter', \
                                weight='bold', logger=logger)

        self.timelimit_label.setText('Time to EL Limit')
        self.timelimit_label.setIndent(15)

        self.ellimit = TimeElLimit(parent=parent, logger=logger)
        self.__set_layout() 

    def __set_layout(self):
        ellayout = QtGui.QHBoxLayout()
        ellayout.setSpacing(0) 
        ellayout.setMargin(0)
        ellayout.addWidget(self.timelimit_label)
        ellayout.addWidget(self.ellimit)
        self.setLayout(ellayout)

    def update_ellimit(self, flag, low, high):
        self.ellimit.update_ellimit(flag, low, high)

    def tick(self):
        ''' testing solo mode '''
        import random  
        
        indx = random.randrange(0,3)
        flag = [0, 1, 2, 'Unknown']
        flag = flag[indx]

        low = random.uniform(0, 760)
        high = random.uniform(0, 760)

        if low > 750.0:
            low = '##NODATA##'
        if high > 750.0:
            high = '##STATNONE##'
        self.update_ellimit(flag, low, high)

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
            t = TimeElLimitDisplay(parent=self.main_widget, logger=logger)
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
        #timer.stop()
        aw.close()
        sys.exit()


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


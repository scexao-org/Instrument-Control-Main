#!/usr/bin/env python

import sys
import os

from CanvasLabel import Canvas, QtCore, QtGui, Qt, ERROR

import ssdlog
from TimeEl import to_hour_min 

progname = os.path.basename(sys.argv[0])


class TimeRotLimit(Canvas):
    ''' Time to Rotator Limit   '''
    def __init__(self, parent=None, logger=None):
        super(TimeRotLimit, self).__init__(parent=parent, fs=10, width=200,\
                                           height=25, align='vcenter', \
                                           weight='bold', logger=logger)
 
    def update_rotlimit(self, flag, rot, link, focus, focus2):
        ''' flag = TSCL.LIMIT_FLAG 
            rot = TSCL.LIMIT_ROT 
            link = TSCV.PROBE_LINK
            focus = TSCV.FOCUSINFO 
            focus2 = TSCV.FOCUSINFO2
        '''

        pf = (0x01000000, 0x02000000, (0x00000000, 0x08))
        self.logger.debug('flag=%s rot=%s link=%s focus=0x%x focus2=0x%x'  %(str(flag), str(rot), str(link), focus, focus2))
        limit_flag_rot = 0x08
        limit_flag_bigrot = 0x10
        link_flag = 0x01

        limit = 721 # in minute
        color=self.normal
        rot_txt = ''
 
        if flag in ERROR or rot in ERROR or link in ERROR:
            text = 'Undifined'
            color = self.alarm
        else:
            if not (flag & limit_flag_bigrot) \
               and (flag & limit_flag_rot):
                if rot < limit:
                     limit = rot

            prime_focus = focus in pf or (focus,focus2) in pf
            if (link & link_flag) == link_flag and not prime_focus:
                rot_txt = '(Probe)'
            else: 
                rot_txt = '(Rotator)'

            if limit > 720.0: # plenty of time. 12 hours
                text = '--h --m' 
            elif limit <= 1: # 0 to 1 minute left
                color = self.alarm
                hm  = to_hour_min(limit)
                text = '%s <= 1m %s' %(hm, rot_txt) 
            elif limit > 30: # 30 to 720 min left
                hm = to_hour_min(limit)
                text = '%s %s' %(hm, rot_txt)  
            else: # 1 to 30 min left
                color = self.warn
                hm = to_hour_min(limit)
                text = '%s <= 30m %s' %(hm, rot_txt)

        self.setText(text)
        self.setStyleSheet("QLabel {color :%s ; background-color:%s }" \
                            %(color, self.bg))

class TimeRotLimitDisplay(QtGui.QWidget):
    def __init__(self, parent=None, logger=None):
        super(TimeRotLimitDisplay, self).__init__(parent)
   
        self.timelimit_label = Canvas(parent=parent, fs=10, width=175,\
                                      height=25, align='vcenter', \
                                      weight='bold', logger=logger)

        self.timelimit_label.setText('Time to Rot Limit')
        self.timelimit_label.setIndent(15)

        self.rotlimit = TimeRotLimit(parent=parent, logger=logger)
        self.__set_layout() 

    def __set_layout(self):
        rotlayout = QtGui.QHBoxLayout()
        rotlayout.setSpacing(0) 
        rotlayout.setMargin(0)
        rotlayout.addWidget(self.timelimit_label)
        rotlayout.addWidget(self.rotlimit)
        self.setLayout(rotlayout)

    def update_rotlimit(self, flag, rot, link, focus, focus2):
        self.rotlimit.update_rotlimit(flag, rot, link, focus, focus2)

    def tick(self):
        ''' testing solo mode '''
        import random  
        
        indx = random.randrange(0,3)
        indx2 = random.randrange(0,5)
        flag = [0, 8, 10, 'Unknown']
        flag = flag[indx]

        rot = random.uniform(0, 760)
        if rot > 750.0:
            rot = '##NODATA##'
        link = random.randrange(0,4)
        # popt/pir/popt2/cs/ns/ns 
        focus = [0x01000000, 0x02000000, 0x00000000, 0x08000000, 0x00010000, 0x00040000][indx2]
        # ns/ns/ns/popt2
        focus2 = [0x01, 0x02,0x04, 0x08][indx]
        self.update_rotlimit(flag, rot, link, focus, focus2)

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
            t = TimeRotLimitDisplay(parent=self.main_widget, logger=logger)
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
        aw.close()
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


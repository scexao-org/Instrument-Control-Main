#!/usr/bin/env python

import sys
import os


# This is only needed for Python v2 but is harmless for Python v3.
#import sip
#sip.setapi('QVariant', 2)
from CanvasLabel import Canvas, QtCore, QtGui, Qt, ERROR
import ssdlog

progname = os.path.basename(sys.argv[0])

    
class Focus(Canvas):
    ''' telescope focus  '''

    def __init__(self, parent=None, logger=None):
        super(Focus, self).__init__(parent=parent, fs=22, width=250, height=35, frame=True, linewidth=1,  logger=logger )

    # to do 0x11111111 is a tentative for popt2. need to figure it out. 
    foci = {0x01000000: 'Prime Optical',
            0x02000000: 'Prime IR', 0x00001000: 'Cassegrain IR',
            0x04000000: 'Cassegrain Optical', 0x08000000: 'Cassegrain Optical', 
            0x10000000: 'Nasmyth Optical', 0x20000000: 'Nasmyth Optical' , 
            0x40000000: 'Nasmyth Optical', 0x80000000L: 'Nasmyth Optical',
            0x00010000: 'Nasmyth Optical', 0x00020000: 'Nasmyth Optical', 
            0x00100000: 'Nasmyth Optical', 0x00200000: 'Nasmyth Optical',
            0x00400000: 'Nasmyth Optical', 0x00800000: 'Nasmyth Optical', 
            0x00000100: 'Nasmyth Optical', 0x00000200: 'Nasmyth Optical',
            0x00002000: 'Nasmyth Optical', 0x00004000: 'Nasmyth Optical', 
            0x00008000: 'Nasmyth Optical', 0x00000001: 'Nasmyth Optical',
            0x00000002: 'Nasmyth Optical', 0x00000004: 'Nasmyth Optical', 
            0x00040000: 'Nasmyth IR', 0x00080000: 'Nasmyth IR', 
            0x00000400: 'Nasmyth IR', 0x00000800: 'Nasmyth IR',
            0x00000800: 'Nasmyth IR', 0x00000008: 'Nasmyth IR', 
            0x00000010: 'Nasmyth IR', 
            (0x00000000, 0x01): 'Nasmyth IR',
            (0x00000000, 0x02): 'Nasmyth IR',
            (0x00000000, 0x04): 'Nasmyth IR', 
            (0x00000000, 0x08): 'Prime Optical2'}

    def update_focus(self,focus, focus2, alarm):
        ''' focus = TSCV.FOCUSINFO 
            focus2 = TSCV.FOCUSINFO2
            alarm = TSCV.FOCUSALARM '''

        self.logger.debug('focus=%s focus2=%s alarm=%s' %(str(focus), str(focus2), str(alarm)))

        color=self.normal
        try:
            text = Focus.foci[focus]
        except KeyError:
            try:
                text = Focus.foci[(focus,focus2)]
            except KeyError:
                text='Focus Undefined'
                color=self.alarm
                self.logger.error('error: focus undef. focusinfo=%s focusinfo2=%s focusalarm=%s' %(str(focus), str(focus2), str(alarm)))

        try:
            if alarm & 0x40:        
                text='Focus Changing'
                color=self.alarm
            if alarm & 0x80:
                text='Focus Conflict'
                color=self.alarm
                self.logger.error('error: focus in conflict with rot/adc')
        except TypeError:
            text = 'Focus Undefined'
            color=self.alarm
            self.logger.error('error: focusalarm undef. focusinfo=%s focusinfo2=%s focusalarm=%s' %(str(focus), str(focus2), str(alarm)))


        self.setStyleSheet("QLabel {color :%s; background-color:%s}" \
                           %(color, self.bg) )
        self.setText(text)

    def tick(self):
        ''' testing solo mode '''
        import random  
        random.seed()

        findx=random.randrange(0, 35)

        foci=[0x01000000, 0x02000000, 0x04000000, 0x08000000,
              0x10000000, 0x20000000, 0x40000000, 0x80000000L,
              0x00010000, 0x00020000, 0x00040000, 0x00080000,
              0x00100000, 0x00200000, 0x00400000, 0x00800000,
              0x00000100, 0x00000200, 0x00000400, 0x00000800,
              0x00001000, 0x00002000, 0x00004000, 0x00008000,
              0x00000001, 0x00000002, 0x00000004, 0x00000008, 
              0x00000010, 0x00000000, 
              "Unknown", None, '##STATNONE##', '##NODATA##', '##ERROR##']
  
        
        aindx=random.randrange(0, 6)
        alarm=[0x40,  None, 0x00, 0x80, '##NODATA##', 0x00 ]
        try:
            focus=foci[findx]
            alarm=alarm[aindx]
        except Exception as e:
            focus=None
            alarm=0x40
            print e
        #focus=0x04000000
        focus2=0x08
        self.update_focus(focus, focus2, alarm)


def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('state', options)
 
    class AppWindow(QtGui.QMainWindow):
        def __init__(self):
            super(AppWindow, self).__init__()
            self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.w=250; self.h=25;
            self.init_ui()

        def init_ui(self):
            self.resize(self.w, self.h)

            self.main_widget = QtGui.QWidget()
            l = QtGui.QVBoxLayout(self.main_widget)
            l.setMargin(0) 
            l.setSpacing(0)
            f = Focus(parent=self.main_widget, logger=logger)
            l.addWidget(f)

            timer = QtCore.QTimer(self)
            QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"), f.tick)
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


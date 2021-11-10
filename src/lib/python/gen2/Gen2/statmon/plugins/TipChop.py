#!/usr/bin/env python

import sys
import os

from CanvasLabel import Canvas, QtCore, QtGui, Qt, ERROR

import ssdlog

progname = os.path.basename(sys.argv[0])


class TipChop(Canvas):
    ''' telescope 2nd mirror   '''
    def __init__(self, parent=None, logger=None):
        super(TipChop, self).__init__(parent=parent, fs=16, width=125, \
                                      height=35, logger=logger )

    # m2ir=[0x00001000, 0x00002000, 0x00004000, 0x00008000, 
    #       0x00000001, 0x00000002, 0x00000004, 0x00000008, 0x00000010]

    def update_tipchop(self, mode, drive, data, state, focus=None, focus2=None):
    #def update_tipchop(self, focus, focus2):
        ''' 
           mode=TSCV.TT_Mode
           drive=TSCV.TT_Drive
           data=TSCV.TT_DataAvail
           chop_state=TSCV.TT_ChopStat 
           focus=
           focus2=
        '''
       
        self.logger.debug('mode=%s drive=%s  data=%s state=%s' %(str(mode), str(drive), str(data), str(state)))
        self.logger.debug('focus=%s focus2=%s' %(str(focus), str(focus2)))

        color=self.normal
        # if  not (focus in TipChop.m2ir or \
        #         (focus==0x00000000 and focus2==0x01)):
        #     text=''
        if mode in ERROR or drive in ERROR or \
             data in ERROR or state in ERROR:
            text=''
        elif not drive&0x01 and drive&0x02: # not drive on
            text=''
        elif mode&0x47 == 0x04:  # positon mode is ok
            text=''
        elif mode&0x47 == 0x02: # tip-tilt mode
            text='Tip-Tilt'
            if not data&0x01: # data not available
                color=self.warn
        elif mode&0x47 == 0x01: # chopping mode
            text='Chopping'
            # choppig stop/not chopping start/not chopping start ready
            if state&0x02 or (not state&0x05 == 0x05): 
                color = self.warn
        else:   
            text='Tip/Chop Undefined'
            color=self.alarm
 
        self.setText(text)
        self.setStyleSheet("QLabel {color :%s ; background-color:%s }" \
                           %(color, self.bg))

    def tick(self):
        ''' testing solo mode '''
        import random  
        random.seed()

        findx=random.randrange(0, 11)
        f2indx=random.randrange(0, 6) 
      
        mindx=random.randrange(0, 4) 
        dindx=random.randrange(0, 2) 
        daindx=random.randrange(0, 2) 
        sindx=random.randrange(0,3) 
       
        print findx, f2indx, mindx, dindx, daindx, sindx
 
        mode=[0x04, 0x02, 0x01, None]
        drive=[0x02, 0x01]
        data=[0x02, 0x01]
        state=[0x02, 0x05, 0x00]

        foci=[0x00001000, 0x00002000, 0x00004000, '##STATNONE##', \
              0x00008000, 0x00000001, 0x00000002, 0x00000004, \
              0x00000008, 0x00000010, 0x00000000]
 
        foci2=[0x01, 0x02, 0x04, "Unknown", 0x01, 0x01]
        try:
            mode=mode[mindx]
            drive=drive[dindx]
            data=data[daindx]
            state=state[sindx]
            focus=foci[findx]
            focus2=foci2[f2indx]
        except Exception as e:
            focus= 0x00000000
            focus2=0x01
            mode=0x01
            drive=0x01
            data=0x02
            state=0x02
            print e
        self.update_tipchop(mode, drive, data, state, focus, focus2)


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
            tc = TipChop(parent=self.main_widget, logger=logger)
            l.addWidget(tc)

            timer = QtCore.QTimer(self)
            QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"), tc.tick)
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


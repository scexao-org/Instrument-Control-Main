#!/usr/bin/env python

import sys
import os

# This is only needed for Python v2 but is harmless for Python v3.
#import sip
#sip.setapi('QVariant', 2)

from CanvasLabel import Canvas, QtCore, QtGui, Qt, ERROR

import ssdlog


progname = os.path.basename(sys.argv[0])

   
# class InsRot(QtGui.QLabel):
#     ''' state of the telescope in pointing/slewing/tracking/guiding  '''
#     def __init__(self, parent=None, logger=None):
#         super(InsRot, self).__init__(parent)

#         self.bg='white'
#         self.alarm='red'
#         self.normal='green'
#         self.warn='orange'
#         self.w=125
#         self.h=20

#         self.logger=logger
       
#         self.__init_label()

#     def __init_label(self):
#         self.font = QtGui.QFont('UnDotum', 11.5) 
#         self.setText('Initializing')
#         self.setAlignment(QtCore.Qt.AlignCenter)
#         self.setFont(self.font)

#         self.setStyleSheet("QLabel {color :%s ; background-color:%s}" %(self.normal, self.bg))

#     def minimumSizeHint(self):
#         return QtCore.QSize(self.w, self.h)

#     def sizeHint(self):
#         return QtCore.QSize(self.w, self.h)


class InsRot(Canvas):
    ''' instrument rotator   '''
    def __init__(self, parent=None, logger=None):
        super(InsRot, self).__init__(parent=parent, fs=11.5, width=125, \
                                     height=35, logger=logger )

    def update_insrot(self, insrot, mode):
        self.logger.debug('rot=%s mode=%s' %(str(insrot), str(mode)))

        if insrot == self.insrot_free or mode == self.mode_free:
            text = 'InsRot Free'
            color=self.warn
        elif insrot == self.insrot_link and mode == self.mode_link:
            text = 'InsRot Link'
            color=self.normal
        else:
            text='InsRot Undefined'
            color=self.alarm

        self.setText(text)
        self.setStyleSheet("QLabel {color :%s ; background-color:%s }" \
                           %(color, self.bg))


class InsRotPf(InsRot):
    ''' prime focus rotator  '''
    def __init__(self, parent=None, logger=None):

        self.insrot_free=0x02
        self.insrot_link=0x01
        self.mode_free=0x20
        self.mode_link=0x10
        super(InsRotPf, self).__init__(parent, logger)

    def update_insrot(self, insrot, mode):
        ''' insrot=TSCV.INSROTROTATION_PF
            mode=TSCV.INSROTMODE_PF 
        ''' 
        super(InsRotPf, self).update_insrot(insrot, mode)


    def tick(self):
        ''' testing solo mode '''
        import random  
        random.seed()

        rindx=random.randrange(0, 6)
        mindx=random.randrange(0, 6)

        insrot=[0x01, 0x02, 0x02, 0x01,  '##NODATA##', '##ERROR##']
 
        mode=[0x10, 0x20, None, '##STATNONE##', 0x10, 0x20]
        try:
            insrot=insrot[rindx]
            mode=mode[mindx]
        except Exception as e:
            insrot=0x01
            mode=0x10
            print e
        self.update_insrot(insrot, mode)


class InsRotCs(InsRot):
    ''' cassegrain rotator  '''
    def __init__(self, parent=None, logger=None):

        self.insrot_free=0x02
        self.insrot_link=0x01
        self.mode_free=0x02
        self.mode_link=0x01
        super(InsRotCs, self).__init__(parent, logger)

    def update_insrot(self, insrot, mode):
        ''' insrot=TSCV.InsRotRotation
            mode=TSCV.InsRotMode
        '''
        super(InsRotCs, self).update_insrot(insrot, mode)

    def tick(self):
        ''' testing solo mode '''
        import random  
        random.seed()

        rindx=random.randrange(0, 6)
        mindx=random.randrange(0, 6)

        insrot=[0x01, 0x02, None, 0x02, '##NODATA##', 0x01]
 
        mode=[0x01, 0x02, 0x02, '##STATNONE##', 0x01, '##ERROR##']
        try:
            insrot=insrot[rindx]
            mode=mode[mindx]
        except Exception as e:
            insrot=0x01
            mode=0x10
            print e
        self.update_insrot(insrot, mode)


def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('insrot', options)
 
    class AppWindow(QtGui.QMainWindow):
        def __init__(self):
            super(AppWindow, self).__init__()
            self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.w=125; self.h=25;
            self.init_ui()

        def init_ui(self):
            self.resize(self.w, self.h)

            self.main_widget = QtGui.QWidget()
            l = QtGui.QVBoxLayout(self.main_widget)
            l.setMargin(0) 
            l.setSpacing(0)

            if options.mode=='pf':
                ins = InsRotPf(parent=self.main_widget, logger=logger)
            elif options.mode=='cs':
                ins = InsRotCs(parent=self.main_widget, logger=logger)
            l.addWidget(ins)

            timer = QtCore.QTimer(self)
            QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"), ins.tick)
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
                      default='pf',
                      help="Specify a plotting mode [pf|cs]")

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


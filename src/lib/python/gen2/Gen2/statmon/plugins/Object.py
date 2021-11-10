#!/usr/bin/env python

import sys
import os

from CanvasLabel import Canvas, QtCore, QtGui, Qt, ERROR

import ssdlog

progname = os.path.basename(sys.argv[0])


class Object(Canvas):
    ''' Object  '''
    def __init__(self, parent=None, logger=None):
        super(Object, self).__init__(parent=parent, fs=10, width=200,\
                                     height=25, align='vcenter', \
                                     weight='bold', logger=logger)

    def update_object(self, obj):
        ''' object = FITS.XXX.OBJECT '''

        self.logger.debug('obj=%s' %(str(obj)))

        color=self.normal

        if not obj in ERROR:
            #text = '%s %s' %(label.ljust(15), obj.rjust(20))            
            text = '{0}'.format(obj)
        else:
            #text = '%s %s' %(label.ljust(15), 'Undefined'.rjust(20))
            text = '{0}'.format('Undefiend')
            color = self.alarm
            self.logger.error('error: object undef. object=%s' %(str(obj)))

        #self.setText('CalProbe: ')
        self.setText(text)
        self.setStyleSheet("QLabel {color :%s ; background-color:%s }" \
                           %(color, self.bg))

class ObjectDisplay(QtGui.QWidget):
    def __init__(self, parent=None, logger=None):
        super(ObjectDisplay, self).__init__(parent)
   
        self.obj_label = Canvas(parent=parent, fs=10, width=175,\
                                height=25, align='vcenter', \
                                weight='bold', logger=logger)

        self.obj_label.setText('Object')
        self.obj_label.setIndent(15)
        #self.obj_label.setAlignment(QtCore.Qt.AlignVCenter) 

        self.obj = Object(parent=parent, logger=logger)
        self.__set_layout() 

    def __set_layout(self):
        objlayout = QtGui.QHBoxLayout()
        objlayout.setSpacing(0) 
        objlayout.setMargin(0)
        objlayout.addWidget(self.obj_label)
        objlayout.addWidget(self.obj)
        self.setLayout(objlayout)

    def update_object(self, obj):
        self.obj.update_object(obj)

    def tick(self):
        ''' testing solo mode '''
        import random  
        random.seed()

        indx = random.randrange(0, 9)

        obj = ['FOFOSS', None, 'NAOJ1212', 'M78asfaf', "Unknown", \
               '##STATNONE##', '##NODATA##', 'GINZA', '##ERROR##']
 
        try:
            obj = obj[indx]
        except Exception as e:
            obj = 'SUBARU'
            print e
        self.update_object(obj)


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
            obj = ObjectDisplay(parent=self.main_widget, logger=logger)
            l.addWidget(obj)

            timer = QtCore.QTimer(self)
            QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"), obj.tick)
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


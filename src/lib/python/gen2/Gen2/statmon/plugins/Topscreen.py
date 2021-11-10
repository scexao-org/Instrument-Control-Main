#!/usr/bin/env python

import os
import sys
import math
import numpy as np

from PyQt4 import QtGui, QtCore

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.figure import SubplotParams
from matplotlib.lines import Line2D
import matplotlib.patches as mpatches

from error import ERROR
import ssdlog
import PlBase

progname = os.path.basename(sys.argv[0])
progversion = "0.1"

 
class TopscreenCanvas(FigureCanvas):
    """ Topscreen """
    def __init__(self, parent=None, width=1, height=1,  logger=None):

        sub=SubplotParams(left=0.0, bottom=0, right=1, \
                          top=1, wspace=0, hspace=0)
        self.fig = Figure(figsize=(width, height), facecolor='white', \
                          subplotpars=sub)
        self.axes = self.fig.add_subplot(111)
        # We want the axes cleared every time plot() is called
        #self.axes.hold(False)
        #self.axes.grid(True)

        # y axis values. these are fixed values. 
        self.y_axis=[-1, 0, 1]
        self.center_y=0.0

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QtGui.QSizePolicy.Expanding, \
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        # width/hight of widget
        self.w=500
        self.h=50
        
        self.logger=logger
   
        self.init_figure()

    def minimumSizeHint(self):
        return QtCore.QSize(self.w, self.h)

    def sizeHint(self):
         return QtCore.QSize(self.w, self.h)
  
    def init_figure(self):
        ''' initial drawing '''

        limit=[30.3, 0] # there is a case of tscl.tsfpos=24.28, so limit is at least 24.28 + 6 = 30.28 
        front_init=16
        self.rear1_pos=rear1_init=4
        rear2_init=10
       
        # top screen front/rear length/width
        self.screen_len=6 # 6 meter
        screen_width=0.2

        self.screen_color='green'
        self.normal_color='black'
        self.alarm_color='red'

        # front/rear top screen
        ts_kwargs=dict(alpha=0.8, fc=self.screen_color, \
                       ec=self.screen_color, lw=1, ) 
        self.front=mpatches.Rectangle((front_init, screen_width - screen_width), \
                                      self.screen_len, screen_width, **ts_kwargs)

        self.rear1=mpatches.Rectangle((rear1_init, screen_width*2), \
                                      self.screen_len, screen_width, \
                                      **ts_kwargs)
        self.rear2=mpatches.Rectangle((rear2_init, screen_width), \
                                      self.screen_len, screen_width, \
                                      **ts_kwargs)

        self.axes.add_patch(self.front)
        self.axes.add_patch(self.rear1)
        self.axes.add_patch(self.rear2)

        # draw x-axis line
        line_kwargs=dict(alpha=0.7, ls='-', lw=0.7 , color=self.screen_color, 
                         marker='.', ms=10.0, mew=1, markevery=(0,1)) 

        middle=[max(limit), min(limit)] 
        line=Line2D(middle, [self.center_y]*len(middle), **line_kwargs)
        self.axes.add_line(line)

        # draw text
        self.text=self.axes.text(0.5, 0.2, 'Initializing', \
                                 va='baseline', ha='center', \
                                 transform = self.axes.transAxes, \
                                             color=self.normal_color, \
                                             fontsize=13)

        # set x,y limit values  
        self.axes.set_xlim(max(limit), min(limit))
        self.axes.set_ylim(min(self.y_axis), max(self.y_axis))
        # # disable default x/y axis drawing 
        #self.axes.set_xlabel(False)
        #self.axes.apply_aspect()
        self.axes.set_axis_off()
       
        #self.axes.set_xscale(10)
        self.axes.axison=False
        self.draw()


class Topscreen(TopscreenCanvas):
    
    """A canvas that updates itself every second with a new plot."""
    def __init__(self,*args, **kwargs):
 
        TopscreenCanvas.__init__(self, *args, **kwargs)
        #super(TopscreenCanvas, self).__init__(*args, **kwargs)
   
    def update_topscreen(self, mode, front , rear):
        ''' mode = TSCV.TopScreen
            front = TSCL.TSFPOS
            rear = TSCL.TSRPOS
        '''
        free=0x10
        link=0x0C
        color=self.normal_color   
        
        self.logger.debug('mode=%s' %(mode))  

        if mode in ERROR: 
            mode='Top Screen Undefined'     
            color=self.alarm_color
        elif mode & free:
            mode='Top Screen Free'
        elif mode & link:
            mode='Top Screen Link'
        else: 
            mode='Top Screen Mode Undef'
            color=self.alarm_color

        self.text.set_text(mode)
        self.text.set_color(color)  

        self.logger.debug('updating pre_rear1=%s' %(self.rear1_pos))  

        try:
            if rear < self.rear1_pos:
                self.rear1_pos=rear
            elif ((self.rear1_pos+self.screen_len) < rear): 
                self.rear1_pos=rear-self.screen_len
            self.logger.debug('updating front=%s rear1=%s rear2=%s' \
                              %(front, self.rear1_pos, rear))  

            self.front.set_x(front)
            self.rear1.set_x(self.rear1_pos)
            self.rear2.set_x(rear)

        except Exception as e:
            self.logger.error('error: front=%s rear=%s. %s' \
                              %(str(front), str(rear), e))

        self.draw()

    def tick(self):
        ''' testing  mode solo '''
        import random  
        random.seed()
 
        mode=[32, "Unknown", 31,  None, 11, '##STATNONE##', 12, '##NODATA##', 30, '##ERROR##']
        #  range is limit+-100, 
        indx=random.randrange(0, 10)
        try:
            mode=mode[indx]
        except Exception:
            mode=30
        front=random.randrange(0, 24)
        rear=random.randrange(0, 14)

        self.update_topscreen(mode, front, rear)


def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('plot', options)
 
    class AppWindow(QtGui.QMainWindow):
        def __init__(self):
            QtGui.QMainWindow.__init__(self)
            self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.w=500; self.h=40;
            self.setup()

        def setup(self):
            self.resize(self.w, self.h)
            self.main_widget = QtGui.QWidget(self)

            l = QtGui.QVBoxLayout(self.main_widget)
            topscreen = Topscreen(self.main_widget, logger=logger)
            l.addWidget(topscreen)

            timer = QtCore.QTimer(self)
            QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"), topscreen.tick)
            timer.start(options.interval)

            self.main_widget.setFocus()
            self.setCentralWidget(self.main_widget)

            self.statusBar().showMessage("topscreen starting..."  ,5000)
            #print options

        def closeEvent(self, ce):
            self.close()

    try:
        qApp = QtGui.QApplication(sys.argv)
        aw = AppWindow()
        aw.setWindowTitle("%s" % progname)
        aw.show()
        sys.exit(qApp.exec_())

    except KeyboardInterrupt as  e:
        print 'key...board'
        logger.info('keyboard interruption....')
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

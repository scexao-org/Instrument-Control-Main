#!/usr/bin/env python

import os
import sys
import math
import numpy as np

from PyQt4 import QtGui, QtCore

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib.patches as mpatches
from matplotlib.figure import SubplotParams
from matplotlib.artist import Artist

import ssdlog
import PlBase
from error import *

progname = os.path.basename(sys.argv[0])
progversion = "0.1"

 
class ElCanvas(FigureCanvas):
    """ Windscreen """
    def __init__(self, parent=None, width=1, height=1,  dpi=None, logger=None):
      
        sub=SubplotParams(left=0.0, bottom=0, right=0.999, \
                          top=1, wspace=0, hspace=0)
        self.fig = Figure(figsize=(width, height), \
                          facecolor='white', subplotpars=sub)
 
        #self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='white')
        #self.fig = Figure(facecolor='white')
        self.axes = self.fig.add_subplot(111)
        # We want the axes cleared every time plot() is called
        #self.axes.hold(False)
        #self.axes.grid(True)

        self.limit_low=0.0
        self.limit_high=90.0;

        self.alarm_high=89.5
        self.alarm_low=10.0

        self.warn_high=89.0
        self.warn_low=15.0


        self.normal_color='green'
        self.warn_color='orange'
        self.alarm_color='red'

        # y axis values. these are fixed values. 
        #self.x_scale=[-0.007, 1.0]
        #self.y_scale=[-0.002,  1.011]

        self.x_scale=[-0.001, 1.0]
        self.y_scale=[0.0,  1.0055]

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        #FigureCanvas.setSizePolicy(self, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        #FigureCanvas.updateGeometry(self)

        # width/hight of widget
        self.w=250
        self.h=250
        #FigureCanvas.resize(self, self.w, self.h)

        self.logger=logger
   
        self.init_figure()
  
    def init_figure(self):
        ''' initial drawing '''

        # draw el frame
        el_kwargs=dict(alpha=0.6, fc='white', ec='black', lw=1.5) 
        el = mpatches.Wedge((1,0), 1, 90, 180, **el_kwargs) 
        self.axes.add_patch(el)

        # draw el angle
        el_kwargs=dict(alpha=0.5, fc=self.normal_color, \
                       ec=self.normal_color, lw=8) 
        self.el = mpatches.Wedge((1,0), 0.99, 90, 180, **el_kwargs) 
        self.axes.add_patch(self.el)

        self.axes.set_ylim(min(self.y_scale), max(self.y_scale))
        self.axes.set_xlim(min(self.x_scale), max(self.x_scale))
        # # disable default x/y axis drawing 
        #self.axes.set_xlabel(False)
        #self.axes.apply_aspect()
        self.axes.set_axis_off()
       
        #self.axes.set_xscale(10)
        #self.axes.axison=False
        self.draw()

    def minimumSizeHint(self):
        return QtCore.QSize(self.w, self.h)

    def sizeHint(self):
         return QtCore.QSize(self.w, self.h)


class El(ElCanvas):
    
    """A canvas that updates itself every second with a new plot."""
    def __init__(self,*args, **kwargs):
 
        #super(AGPlot, self).__init__(*args, **kwargs)
        ElCanvas.__init__(self, *args, **kwargs)


     
    def __get_val_state(self, el, state):

        color=self.normal_color
        if state=="Pointing":
            return (el, color)

        if el > self.limit_high:
            color=self.alarm_color 
            el=self.limit_high
        elif el < self.limit_low:
            color=self.alarm_color 
            el=self.limit_low
        elif (el >= self.alarm_high or el <= self.alarm_low):  
            color=self.alarm_color 
        elif (el >= self.warn_high or el <= self.warn_low):  
            color=self.warn_color

        return (el, color)


    def update_el(self, el, state):
        ''' el = TSCS.EL 
            state = STATL.TELDRIVE '''

        self.logger.debug('updating el=%s state=%s'  %(str(el), state)) 

        val, color=self.__get_val_state(el, state)

        try:
            Artist.remove(self.el)
            el_kwargs=dict(alpha=0.5, fc=color, ec=color, lw=8) 
            self.el = mpatches.Wedge((1,0), 0.99, 180-val, 180, **el_kwargs) 
            self.axes.add_patch(self.el)
            self.draw()
        except Exception as e:
            self.logger.error('error: updating. %s' %str(e))
            pass

    def tick(self):
        ''' testing solo mode '''
        import random  
        random.seed()
        state=["Guiding(AG1)", "Guiding(AG2)", "Unknown", "##NODATA##",
               "##ERROR##", "Guiding(SV1)","Guiding(SV2)", "Guiding(AGPIR)",
               "Guiding(AGFMOS)", "Tracking", "Tracking(Non-Sidereal)", 
               "Slewing", "Pointing", "Guiding(HSCSCAG)", "Guiding(HSCSHAG)"]

        # el limit is between 0 and 90, 
        el=random.random()*random.randrange(0,150)
        indx=random.randrange(0,15)
        try:
            state=state[indx]
        except Exception:
            state='Pointing' 
        self.update_el(el, state)



def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('el', options)
 
    class AppWindow(QtGui.QMainWindow):
        def __init__(self):
            QtGui.QMainWindow.__init__(self)
            self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.w=250; self.h=250;
            self.setup()

        def setup(self):
            self.resize(self.w, self.h)
            self.main_widget = QtGui.QWidget(self)

            l = QtGui.QVBoxLayout(self.main_widget)
            el = El(self.main_widget, logger=logger)
            l.addWidget(el)

            timer = QtCore.QTimer(self)
            QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"), el.tick)
            timer.start(options.interval)

            self.main_widget.setFocus()
            self.setCentralWidget(self.main_widget)

            self.statusBar().showMessage("windscreen starting..."  ,5000)
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

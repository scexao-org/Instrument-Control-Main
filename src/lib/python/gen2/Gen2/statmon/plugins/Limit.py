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

import ssdlog
import PlBase

progname = os.path.basename(sys.argv[0])
progversion = "0.1"

 
class LimitCanvas(FigureCanvas):
    """  Canvas to draw a limit """
    def __init__(self, parent=None, title='Limit', width=5, height=5,
                 alarm=[0,0], warn=[0,0], limit=[0,0], marker=0.0, marker_txt='',logger=None):

        sub=SubplotParams(left=0.05,  right=0.95, wspace=0, hspace=0)
        self.fig = Figure(figsize=(width, height),  facecolor='white', subplotpars=sub )
        self.axes = self.fig.add_subplot(111)
        # We want the axes cleared every time plot() is called
        #self.axes.hold(False)
        #self.axes.grid(True)

        self.title=title
        self.limit_low=min(limit); self.limit_high=max(limit);
        self.alarm_low=min(alarm); self.alarm_high=max(alarm);
        self.warn_low=min(warn); self.warn_high=max(warn);
        self.marker=marker; self.marker_txt=marker_txt;

        self.cur_color='green'
        self.cmd_color='blue'
        self.warn_color='orange'
        self.alarm_color='red'

        # y axis values. these are fixed values. 
        self.y_axis=[-1, 0.0,  1]
        self.center_y=0.0
        self.init_x=0.0  # initial value of x

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        # width/hight of widget
        self.w=350
        self.h=80
        self.logger=logger
   
        self.init_figure()
  
    def init_figure(self):
        ''' initial drawing '''

        # position of current/cmd display
        self.y_curoffset=0.35
        self.y_cmdoffset=-0.65

        # current,commanded text
        self.bbox=dict(boxstyle="round, pad=0.15",facecolor=self.cur_color, ec="none",  alpha=0.75,)
#        center_x='%.1f' %self.center_x
        self.cur_anno=self.axes.annotate(self.init_x,  fontsize=13, weight='bold', 
                                         xy=(self.init_x, self.center_y), 
                                         xytext=(self.init_x, self.y_curoffset),
                                         bbox=self.bbox, color='w',
                                         #rotation=-90,
                                         arrowprops=dict(arrowstyle="-|>", relpos=(0.5, -0.2)),
                                         transform=self.axes, horizontalalignment='center')

        self.cmd_anno=self.axes.annotate(self.init_x,  fontsize=12, weight='bold', 
                                         xy=(self.init_x, self.center_y), 
                                         xytext=(self.init_x, self.y_cmdoffset),
                                         bbox=dict(boxstyle="round,pad=0.15", facecolor=self.cmd_color, 
                                                   ec="none",  alpha=0.05, ),
                                         color=self.cmd_color,
                                         arrowprops=dict(arrowstyle="-|>", relpos=(0.5, 0)),
                                         transform=self.axes, horizontalalignment='center')


        # draw x-axis
        line_kwargs=dict(alpha=0.7, ls='-', lw=1.5 , color=self.cur_color, 
                         marker='|', ms=8.0, mew=1.5, markevery=(1,10)) 

        line_edge_kwargs=dict(alpha=0.9, ls='-', lw=2 , color=self.warn_color, 
                              marker='|', ms=20.0, mew=3, markevery=(1,1), mec=self.alarm_color) 

        middle=[self.warn_low,  self.marker, self.warn_high] 
        line_middle=Line2D(middle, [self.center_y]*len(middle), **line_kwargs)

        right=[self.warn_high, self.limit_high]
        line_right=Line2D(right, [self.center_y]*len(right), **line_edge_kwargs)

        left=[self.warn_low, self.limit_low] 
        line_left=Line2D(left, [self.center_y]*len(left), **line_edge_kwargs)

        self.axes.add_line(line_right)
        self.axes.add_line(line_left)
        self.axes.add_line(line_middle)

        # draw text
        self.axes.text(0, 0.9, self.title,  color=self.cmd_color,  va='baseline', ha='left', 
                       transform=self.axes.transAxes, fontsize=11)
        self.axes.text(0.5, 0.95, 'current',   va='baseline', ha='center', 
                       transform=self.axes.transAxes, fontsize=11)
        self.axes.text(0.5, 0.1, 'commanded',  va='top', ha='center', 
                       transform=self.axes.transAxes, fontsize=10)
 
        # draw labels of x-axis
        x_axis=[self.limit_low, self.marker, self.limit_high]
        x_label=[self.limit_low, self.marker_txt, self.limit_high]

        for (x, label) in zip(x_axis, x_label) :
            self.axes.text(x, -0.8,  '%s'%label, fontsize=11,  va='center', ha='center', alpha=0.7)
        # set x,y scale.   note: added +-0.00001 in order to display a value that exceeds possitive/negative limit, otherwise, a value will disappear only when this widget is plugged into telstat   
        self.axes.set_xlim(self.limit_low-0.00001, self.limit_high+0.00001)
        self.axes.set_ylim(min(self.y_axis), max(self.y_axis))
        # # disable default x/y axis drawing 
        #self.axes.set_xlabel(False)
        #self.axes.set_ylabel(False)
        self.axes.axison=False
        self.draw()

    def minimumSizeHint(self):
        return QtCore.QSize(self.w, self.h)

    def sizeHint(self):
         return QtCore.QSize(self.w, self.h)


class Limit(LimitCanvas):
    """ AZ/EL/Rotator/Probe Limit  """
    def __init__(self,*args, **kwargs):
 
        #super(AGPlot, self).__init__(*args, **kwargs)
        LimitCanvas.__init__(self, *args, **kwargs)

    def get_val_state(self,val, state=None):
    
        color=self.cur_color
        try:
            text='%.1f' %val
        except Exception as e:
            self.logger.error('error: value not number=%s %s' %(str(val), str(e)))
            text='No Data'
            color=self.alarm_color
            val=0
        else:
            if val > self.limit_high:
                color=self.alarm_color 
                val=self.limit_high
            elif val < self.limit_low:
                color=self.alarm_color 
                val=self.limit_low
            elif (val >= self.alarm_high or val <= self.alarm_low):  
                color=self.alarm_color 
            elif (val >= self.warn_high or val <= self.warn_low):  
                color=self.warn_color

        return (text, val, color)

    def update_limit(self, current , cmd, state=None):

        self.logger.debug('updating cur=%s cmd=%s state=%s' %(current, cmd, state))  

        text,val,color=self.get_val_state(current, state)

        # ignore alarm/warning if el in pointing  
        if state and state.strip()=='Pointing':
            color=self.cur_color

        try:
            self.cur_anno.set_text(text)
            self.cur_anno.xy=(val, self.center_y)
            self.cur_anno.xytext=(val, self.y_curoffset)
            self.bbox['facecolor']=color
            self.cur_anno.set_bbox(self.bbox)
        except Exception as e:
            self.logger.error('error: setting current value. %s' %e)
            pass

        text, val,color=self.get_val_state(cmd)
        try:
            self.cmd_anno.xytext=(val, self.y_cmdoffset)
            self.cmd_anno.set_text(text)
            self.cmd_anno.xy=(val, self.center_y)
        except Exception as e:
            self.logger.error('error: setting cmd value. %s' %e)
            pass
 
        self.draw()

    def tick(self):
        ''' testing  mode solo '''
        import random  
        random.seed()
 
        #  range is limit+-100, 
        current=random.random()*random.randrange(self.limit_low-200, self.limit_high+100)
        cmd=random.random()*random.randrange(self.limit_low-100, self.limit_high+100)

        self.update_limit(current, cmd)



class ElLimit(Limit):
    ''' EL Limit for testing '''
    def __init__(self,*args, **kwargs):
        super(ElLimit, self).__init__(*args, **kwargs)

    def tick(self):
        ''' testing solo mode '''
        import random  
        random.seed()
        state=["Guiding(AG1)", "Guiding(AG2)", "Unknown", "##NODATA##",
               "##ERROR##", "Guiding(SV1)","Guiding(SV2)", "Guiding(AGPIR)",
               "Guiding(AGFMOS)", "Tracking", "Tracking(Non-Sidereal)", 
               "Slewing", "Pointing"]

        # el limit is between 0 and 90, 
        current=random.random()*random.randrange(0,self.limit_high+50)
        cmd=random.random()*random.randrange(0, self.limit_high+50)
        indx=random.randrange(0,13)
        try:
            state=state[indx]
        except Exception:
            state='Pointing' 
        self.update_limit(current, cmd, state)

def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('plot', options)
 
    class AppWindow(QtGui.QMainWindow):
        def __init__(self):
            QtGui.QMainWindow.__init__(self)
            self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.setup()

        def setup(self):

            self.main_widget = QtGui.QWidget(self)

            l = QtGui.QVBoxLayout(self.main_widget)

            if options.mode=='az':
                title='AZ'
                alarm=[-269.5, 269.5]
                warn=[-260.0, 260.0 ]
                limit=[-270.0, 270.0]
                limit =  Limit(self.main_widget, title=title, alarm=alarm, warn=warn, limit=limit, logger=logger)
            if options.mode=='el':
                title='EL'
                marker=15.0
                marker_txt=15.0
                warn=[15.0, 89.0]
                alarm=[10.0,89.5] 
                limit=[0.0, 90.0]                
                limit =  ElLimit(self.main_widget, title=title, alarm=alarm, warn=warn, limit=limit, marker=marker, marker_txt=marker_txt,logger=logger)

            elif options.mode=='popt':
                title='Rotator Popt'
                alarm=[-249.5, 249.5]
                warn=[-240.0, 240.0 ]
                limit=[-250.0, 250.0]
                limit = Limit(self.main_widget, title=title, alarm=alarm, warn=warn, limit=limit,logger=logger)
            elif options.mode=='popt2' or options.mode=='cs':
                if options.mode=='popt2':
                    title='Rotator Popt2'
                else:
                    title='Rotator Cs'
                warn=[-260.0, 260.0]
                alarm=[-269.5, 269.5]
                limit=[-270.0, 270.0]
                limit = Limit(self.main_widget, title=title, alarm=alarm, warn=warn, limit=limit, logger=logger)
            elif options.mode=='pir':
                title='Rotator Pir'
                warn=[-175.0,175.0]
                alarm=[-179.5,179.5]
                limit=[-180.0, 180.0]
                limit =  Limit(self.main_widget, title=title, alarm=alarm, warn=warn, limit=limit, logger=logger)
            elif options.mode=='nsir' or  options.mode=='nsopt':
                if options.mode=='nsir':
                    title='Rotator Ns Ir'
                else:
                    title='Rotator Ns Opt'
                warn=[-175.0,175.0]
                alarm=[-179.5,179.5]
                limit=[-180.0, 180.0]
                limit = Limit(self.main_widget, title=title, alarm=alarm, warn=warn, limit=limit, logger=logger)

            elif options.mode=='nsirag' or options.mode=='nsoptag':
                if options.mode=='nsirag':
                    title='AgProbe Ns Ir'
                else:
                    title='AgProbe Ns Opt'
                warn=[-270.0, 270.0]
                alarm=[-270.0, 270.0]
                limit=[-270.0, 270.0]
                limit = Limit(self.main_widget, title=title, alarm=alarm, warn=warn, limit=limit, logger=logger)

            elif options.mode=='csag':
                title='AgProbe Cs'
                warn=[-185.0, 185.0]
                alarm=[-185.0, 185.0]
                limit=[-185.0, 185.0]
                limit = Limit(self.main_widget, title=title, alarm=alarm, warn=warn, limit=limit, logger=logger)

            l.addWidget(limit)

            timer = QtCore.QTimer(self)
            QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"), limit.tick)
            timer.start(options.interval)

            self.main_widget.setFocus()
            self.setCentralWidget(self.main_widget)

            self.statusBar().showMessage("%s starting..." %options.mode, 5000)
            #print options

        def closeEvent(self, ce):
            self.close()

    try:
        qApp = QtGui.QApplication(sys.argv)
        aw = AppWindow()
        aw.setWindowTitle("%s" % progname)
        aw.show()
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
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--interval", dest="interval", type='int',
                      default=1000,
                      help="Inverval for plotting(milli sec).")
    # note: there are sv/pir plotting, but mode ag uses the same code.  
    optprs.add_option("--mode", dest="mode",
                      default='az',
                      help="Specify a plotting mode [az|el|popt|popt2|pir|cs|nsir|nsopt|nsirag|nsoptag|csag]")

    ssdlog.addlogopts(optprs)
    
    (options, args) = optprs.parse_args()

    if len(args) != 0:
        optprs.error("incorrect number of arguments")

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

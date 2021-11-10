#!/usr/bin/env python

import sys, os
import math
import threading

from PyQt4 import QtGui, QtCore
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from matplotlib.axes import Axes

#from pylab import *
from matplotlib.patches import Circle
#from matplotlib.patches import Rectangle
from matplotlib.artist import Artist
from matplotlib.lines import Line2D

from matplotlib.widgets import Button
#import matplotlib.patches as mpatches

#import matplotlib.lines as lines
from matplotlib.figure import SubplotParams

import Bunch
import ssdlog
from Exptime import Exptime
from Threshold import Threshold
from Dummy import Dummy
progname = os.path.basename(sys.argv[0])
progversion = "0.1"

 
class PlotCanvas(FigureCanvas):
    """ AG/SV/FMOS/AO188 Plotting """
    def __init__(self, parent=None, center_x=0, center_y=0, logger=None):
        #sub=SubplotParams(bottom=0)
        self.fig = Figure(figsize=(5, 5), dpi=None, facecolor='white')
        #plt.subplots_adjust(bottom=0.3) 
        self.axes = self.fig.add_subplot(111)
        # We want the axes cleared every time plot() is called
        #self.axes.hold(False)
        #self.axes.grid(True)
       
            
        self.center_x=center_x  # center of canvas
        self.center_y=center_y    
        self.w=350
        self.h=350
      
        self.plot_color='blue'
        self.record_color='black'
        self.alarm_color='red'
        self.warn_color='orange'

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.logger=logger

        #self.fig.canvas.mpl_connect('button_press_event', self.test)
        #self.fig.canvas.mpl_connect('pick_event', self.onpick)

        self.init_figure()

    def zoomin(self):
        self.logger.debug('zooming in')
        self.scale_index-=1 
        self.reconfigure()

    def zoomout(self):
        self.logger.debug('zooming out')
        self.scale_index+=1 
        self.reconfigure()

    def refresh(self):
        self.logger.debug('refresh')
        self.clear()

    def get_min_max_scale(self):
        ''' get min/max scale values '''  
        scale=self.scale[self.scale_index]
        #scale=self.circle[self.scale_index]
        min_val= min(scale)
        max_val= max(scale)
        return (min_val, max_val) 

    def get_scales(self):
        ''' get scales of circle/x,y axis/y label'''
        circle=self.circle[self.scale_index]
        y_axis=self.y_axis[self.scale_index]  
        x_axis=self.x_axis[self.scale_index]  
        y_label=self.y_label[self.scale_index]
      
        return (circle, x_axis, y_axis, y_label)

    def init_figure(self):
        ''' initial drawing '''

        try:
            (circle, x_axis, y_axis, y_label)=self.get_scales()
            (scale_min, scale_max)=self.get_min_max_scale()
        except Exception as e:
            self.logger.error('error: getting scales. %s' %e)
            return

        # the arrow from previous plotting to current plotting 
        self.arrow=self.axes.annotate('', xy=(self.center_x, self.center_y), 
                                      xytext=(self.center_x, self.center_y),
                                      size=5, color='b',
                                      arrowprops=dict(arrowstyle="wedge,tail_width=2.0", \
                                                      facecolor='grey', ec="none", \
                                                      alpha=0.5, patchA=None, \
                                                      relpos=(0.5, -0.09)),
                                      horizontalalignment='center')

        #kwargs=dict(boxstyle='square', alpha=0.1, ec='grey', fc='white' )


        kwargs=dict(alpha=0.4, ec='grey', fc='white' ) 
        #self.axes.text(0.057, 1.02, '[                       ]', color='w', ha='left', va='baseline',
        #               bbox=kwargs,
        #               fontsize=27,
        #               transform=self.axes.transAxes) 
        self.title_x=self.axes.text(0.30, 1.03, 'X:%02.2f' %(self.center_x), \
                                    color='green', ha='left', va='baseline', \
                                    #bbox=kwargs, \
                                    fontsize=14, \
                                    transform=self.axes.transAxes)

        self.title_y=self.axes.text(0.54, 1.03, 'Y:%02.2f' %(self.center_y), \
                                    color='green', ha='left', va='baseline', \
                                    #bbox=kwargs, \
                                    fontsize=14, \
                                    transform=self.axes.transAxes)

        #t=Rectangle((0.05, 0.05), 0.9, 0.9, alpha=0.1, color='lightgreen', ec='None',  transform=self.axes.transAxes)
        #self.axes.add_patch(t)  

        # draw inner/outer circles 
        self.inner_c = Circle((self.center_x, self.center_y), min(circle), \
                               fc="None", ec="g", lw=0.5, ls='solid')
        self.axes.add_patch(self.inner_c)
        self.outer_c = Circle((self.center_x, self.center_y), max(circle), \
                               fc="None", ec="g", lw=1.5, ls='solid')
        self.axes.add_patch(self.outer_c)

        # draw x-axis
        self.h_line=Line2D(x_axis, [self.center_x]*len(x_axis), alpha=0.75, \
                           ls='None', lw=0.7, color='g', marker='+', ms=35.0, \
                           mew=1.5, markevery=(2,10))

        self.axes.add_line(self.h_line)

        # draw y-axis
        self.v_line=Line2D([min(x_axis)]*len(y_axis), y_axis, alpha=1, ls=':', \
                           lw=3, marker=0, color='g', ms=15.0, mew=1, markevery=None)
        self.axes.add_line(self.v_line)

        # draw labels of y-axis
        self.label=[]
        for (y, label) in zip(y_axis, y_label) :
            self.label.append(self.axes.text(min(x_axis)-0.03-(0.03*self.scale_index), y, '%s' \
                              %label, verticalalignment='center', horizontalalignment='right'))

        # set x,y limit values  
        self.axes.set_xlim(scale_min, scale_max)
        self.axes.set_ylim(scale_min, scale_max)
        # disable default x/y axis drawing 
        self.axes.axison=False

        #a = self.fig.axes([-0.5, -.5, 0.1, 0.075])
        #b = Button(a, 'Next')

        self.draw()

    def reconfigure(self):
        ''' reconfigure canvas '''
        self.logger.debug('reconfiguring...')

        def set_scale_index():
            num_scale=len(self.scale)-1
            if self.scale_index > num_scale:
                self.scale_index=num_scale
            elif self.scale_index < 0:
                self.scale_index=0

        set_scale_index()

        try:
            (circle, x_axis, y_axis, y_label)=self.get_scales()
            (min_val, max_val)=self.get_min_max_scale()
        except Exception as e:
            self.logger.error('error: getting scales. %s' %e)
            return 

        # re-set x/y-axis 
        #self.h_line.set_data(x_axis, [0]*len(x_axis))
        self.h_line.set_data(x_axis, [self.center_x]*len(x_axis))
        self.v_line.set_data([min(x_axis)]*len(y_axis), y_axis)
        
        # re-set circles  
        #self.inner_c.set_axes([self.center_x, self.center_y])
        self.inner_c.set_radius(min(circle))
        self.outer_c.set_radius(max(circle))

        # re-draw labels of y-axis
        for (text, label) in zip(self.label, y_label):
            text.set_text('%s'%label)
         
        # re-set values of y-axis
        for (text, y) in zip(self.label, y_axis):
            text.set_y(y)
        
        # re-set  values of x-axis  
        for text in self.label:
            # 0.03 is a value to adjust lables position of y-axis
            text.set_x(min(x_axis)-self.label_offset-(0.029*self.scale_index))

        self.axes.set_xlim(min_val, max_val)
        self.axes.set_ylim(min_val, max_val)

        self.draw()

    # def mousePressEvent(self, event):
    #     if event.button() == QtCore.Qt.LeftButton:
    #         print 'LEFT...'
    #         self.scale_index+=1
    #     elif event.button() == QtCore.Qt.RightButton:
    #         print 'Right...'
    #         self.scale_index-=1 
    #     else:
    #         return 
    #     self.reconfigure()

    def minimumSizeHint(self):
        return QtCore.QSize(self.w, self.h)

    def sizeHint(self):
         return QtCore.QSize(self.w, self.h)


class Plot(PlotCanvas):
    
    """A canvas that updates itself every second with a new plot."""
    def __init__(self, parent=None, center_x=0, center_y=0, logger=None):
 
        #super(AGPlot, self).__init__(*args, **kwargs)

        self.c=0
        self.plot_record=[]

        self.max_record=500   # max number of record to draw on canvas

        self.label_offset=0.03    # offset potision of label of y-axis 
        self.record_radius=0.005  # the radius of a circle of record

        self.scale_index=1  # default scale

        # those values are measured not to waggle redrawn circles when a widget is reconfigured
        self.scale=([-0.28, 0.28], [-0.56, 0.56], \
                    [-0.84, 0.84], [-1.12, 1.12], \
                    [-1.40, 1.40], [-1.68, 1.68], \
                    [-1.96, 1.96], [-2.24, 2.24])

        # the radius of inner/outer circle
        self.circle=([0.125, 0.25], [0.25, 0.5], \
                     [0.375, 0.75], [0.5, 1.0],  \
                     [0.625, 1.25], [0.75, 1.5], \
                     [0.875, 1.75], [1.0, 2.0])
        # y axis values
        self.y_axis=([-0.25, -0.125, 0.0, 0.125,  0.25], \
                     [-0.5, -0.25, 0.0, 0.25, 0.5],  \
                     [-0.75, -0.375, 0.0, 0.375, 0.75], \
                     [-1.0, -0.5, 0.0, 0.5, 1.0],  \
                     [-1.25, -0.625, 0.0, 0.625, 1.25], \
                     [-1.5, -0.75, 0.0, 0.75, 1.5],  \
                     [-1.75, -0.875, 0.0, 0.875, 1.75], \
                     [-2.0, -1.0, 0.0, 1.0, 2.0])
        # x axis values
        self.x_axis=([-0.25, -0.125, 0.0, 0.125,  0.25], \
                     [-0.5, -0.25, 0.0, 0.25, 0.5], \
                     [-0.75, -0.375, 0.0, 0.375, 0.75], \
                     [-1.0, -0.5,  0.0, 0.5, 1.0], \
                     [-1.25, -0.625, 0.0, 0.625, 1.25], \
                     [-1.5, -0.75, 0.0, 0.75, 1.5], \
                     [-1.75, -0.875, 0.0, 0.875, 1.75], \
                     [-2.0, -1.0, 0.0, 1.0, 2.0])
        # y axis labels
        self.y_label=([-0.25, -0.125, 'arcsec', 0.125, 0.25], \
                      [-0.5, -0.25, 'arcsec', 0.25, 0.5], \
                      [-0.75, -0.375, 'arcsec', 0.375, 0.75], \
                      [-1.0, -0.5, 'arcsec', 0.5, 1.0], \
                      [-1.25, -0.625, 'arcsec', 0.625, 1.25], \
                      [-1.5, -0.75, 'arcsec', 0.75, 1.5], \
                      [-1.75, -0.875, 'arcsec', 0.875, 1.75], \
                      [-2.0, -1.0,  'arcsec', 1.0, 2.0])

        PlotCanvas.__init__(self, parent=parent, center_x=center_x, \
                            center_y=center_y, logger=logger)

        self.rlock = threading.RLock()


    def tick(self):
        ''' testing solo mode '''
        import random  
        random.seed()

        x=random.random()*random.randrange(-800,800)
        y=random.random()*random.randrange(-800,800)
        self.update_plot(x,y)



    # def in_range(self, x, y, limit):
    #     ''' is ploting in range '''
    #     res=True
    #     if (x > limit or x < -limit) or (y > limit or y < -limit):
    #         res=False
    #     return res

    #def draw_path(self, cur, pre):
    def draw_path(self):
        ''' draw a path to a current plotting from previous one ''' 
        with self.rlock:
            try:
                cur=self.plot_record[-1]
                pre=self.plot_record[-2]
                self.arrow.xy=(cur.x, cur.y)
                self.arrow.xytext=(pre.x, pre.y) 
            except Exception as e:
                self.logger.warn('warn: drawing path. %s' %e)
                pass

    def redraw_point(self):
        ''' re-draw a previous plotting to a smaller circle  ''' 
        with self.rlock:
            try:
                # somehow self.plot_record[-1:] is not retrieving data, added extra[0]
                pre = self.plot_record[-1] # extract the lastest record 
                pre.point.set_radius(self.record_radius)
                pre.point.set_facecolor(pre.color)
                pre.point.set_edgecolor(pre.color)
                pre.point.set_alpha(0.75)
            #  extracting the lastest record fails if a plotting is the first time. but it's ok  
            except Exception as e:
                pre=None
                self.logger.warn('warn: %s' %str(e))
                pass
        #return pre
#        plot_path()

    def clear(self):
        ''' clear all plottings '''   
        with self.rlock: 
            for num in xrange(len(self.plot_record)):
                self.delete_oldest_record()
            self.arrow.xy=(0, 0)
            self.arrow.xytext=(0, 0) 
        self.draw() 
    
    def delete_oldest_record(self):
        ''' delete the oldest plotting '''
        try:   
            p=self.plot_record.pop(0)
            Artist.remove(p.point)
        except Exception as e:
            print e
            pass            


    def update_plot(self, x , y):
        ''' update plotting '''
        self.logger.debug('x=%s y=%s' %(x,y)) 
        
        try:
            x *= 0.001
            y *= 0.001
        except Exception as e:
            self.logger.warn('warn: x, y are not digits. %s' %e)
            return 

        #pre=self.redraw_point()
        self.redraw_point()
    
        #plot=self.plot_point(x,y)
        self.plot_point(x,y) 

        self.draw_path()
        #self.draw_path(plot, pre)

        with self.rlock:
            plot_points = len(self.plot_record) 
            if plot_points > self.max_record:
                self.delete_oldest_record()

        self.title_x.set_text('X:%02.2f' %(x))
        self.title_y.set_text('Y:%02.2f' %(y))
        #self.axes.set_title('x=%0.2f, y=%0.2f' %(x,y))
 
        self.draw()

    def plot_point(self, x , y, ):
        ''' plotting '''

        self.c+=1

        alarm = max(self.circle[self.scale_index])
 
#        in_range=self.in_range(x,y, limit=alarm)       
        
        circle = Circle(xy=(x,y), radius=0.0125*(self.scale_index+1), \
                      ec="none", fill=True, alpha=1)
        if (x > alarm or x < -alarm) or (y > alarm or y < -alarm):
            circle.set_facecolor(self.alarm_color) 
            color = self.alarm_color
        else:
            circle.set_facecolor(self.plot_color)
            color = self.record_color
        
        self.axes.add_patch(circle)  

        print self.c
 
        plot=Bunch.Bunch(point=circle, x=x, y=y, color=color)

        #print 'PLOT=%s' %plot         
        with self.rlock:
            self.plot_record.append(plot)
        
        #print self.plot_record
        #return plot


class Ao1Plot(Plot):
    def __init__(self, parent=None, logger=None):
        #super(AOPlot1, self).__init__(parent, logger)
        Plot.__init__(self, parent=parent, logger=logger)

        self.scale_index=0
        self.label_offset = 1.033

        self.plot_radius = 0.45
        self.record_radius = 0.1 
        self.max_record=100

        self.alarm=9.0
        self.warn=6.0

        self.record_color = 'grey'

        # those values are measured not to waggle redrawn circles when a widget is reconfigured
        #self.scale=([-11.2, 11.2],)
        self.scale = ([-10.072, 10.072],)
        # the radius of inner/outer circle
        #self.circle=([5.0, 10.0],)
        self.circle = ([6.0, 9.0],)
        # y axis values
        #self.y_axis=([-10.0, -5.0, 0.0, 5.0,  10.0],)
        self.y_axis = ([-9.0, -6.0, 0.0, 6.0,  9.0],)
        # x axis values
        #self.x_axis=([-10.0, -5.0, 0.0, 5.0,  10.0],)
        self.x_axis = ([-9.0, -6.0, 0.0, 6.0,  9.0],)
        # y axis labels
        #self.y_label=([-10.0, -5.0, 'voltage', 5.0,  10.0],)
        self.y_label = ([-9.0, -6.0, '0.0(V)', 6.0,  9.0],)
  
        self.reconfigure()

    def plot_point(self, x, y):
        self.logger.debug('ao1 plotting')
         
        if (x >= self.alarm or x <= -self.alarm) or \
           (y >= self.alarm or y <= -self.alarm):
            circle=Circle(xy=(x,y), radius=self.plot_radius, \
                              fc=self.alarm_color, ec='none', fill=True, alpha=1)
            color=self.alarm_color
        elif (self.warn <= x or x <= -self.warn) or \
             (self.warn <= y  or y <= -self.warn):
            circle=Circle(xy=(x,y), radius=self.plot_radius, \
                          fc=self.warn_color, ec='none', fill=True, alpha=1)
            color=self.warn_color
        else:
            circle=Circle(xy=(x,y), radius=self.plot_radius, \
                          fc=self.plot_color, ec='none', fill=True, alpha=1)
            color=self.record_color
        
        self.axes.add_patch(circle)  
 
        plot=Bunch.Bunch(point=circle, x=x, y=y, color=color)

        with self.rlock:
            self.plot_record.append(plot)

        return plot


class Ao2Plot(Plot):
    def __init__(self, parent=None, logger=None):

        Plot.__init__(self, parent=parent, center_x=5, center_y=5, logger=logger)

        self.scale_index=0
        self.label_offset=0.553

        self.plot_radius=0.25
        self.record_radius=0.06 

        self.alarm_low=2.0
        self.alarm_high=8.0

        self.max_record=100
        self.record_color='grey'
        #self.alarm=self.warn=3.0 # no warning. so set warn as alarm

        #self.warn_color='red' 

        # those values are measured not to waggle redrawn circles when a widget is reconfigured
        #self.scale=([-5.6, 5.6],)
        self.scale=([-0.6, 10.6],)
        # the radius of inner/outer circle
        self.circle=([3.0, 5.0],)
        # y axis values
        #self.y_axis=([-5.0, -3.0, 0.0, 3.0,  5.0],)
        self.y_axis=([0, 2.0, 5.0, 8.0,  10.0],)
        # x axis values
        self.x_axis=([0, 2.0, 5.0, 8.0,  10.0],)
        #self.x_axis=([-5.0, -3.0, 0.0, 3.0,  5.0],)
        # y axis labels
        #self.y_label=([-5.0, -3.0, 'VL', 3.0,  5.0],)
        self.y_label=([0.0, 2.0, '5.0(V)', 8.0,  10.0],)
        self.reconfigure()


    def plot_point(self, x, y):
        if (x >= self.alarm_high or x <= self.alarm_low) or \
           (y >= self.alarm_high or y <= self.alarm_low):
            circle=Circle(xy=(x,y), radius=self.plot_radius, \
            fc=self.alarm_color, ec="none", fill=True, alpha=1)
            color=self.alarm_color
        else:
            circle=Circle(xy=(x,y), radius=self.plot_radius, \
            fc=self.plot_color, ec="none", fill=True, alpha=1)
            color=self.record_color
        
        self.axes.add_patch(circle)  
 
        plot=Bunch.Bunch(point=circle, x=x, y=y, color=color)

        with self.rlock:
            self.plot_record.append(plot)

        return plot


    # def update_plot(self, x , y):
    #     self.logger.debug('updating ao2 x=%s y=%s' %(x,y))
    #     # make sure that x/y are digits not string 
    #     try:
    #         x*=1000.0
    #         y*=1000.0
    #     except Exception:
    #         pass 
    #     else:
    #         Plot.update_plot(self, x , y)
      
    # def tick(self):
    #     ''' testing solo mode '''
    #     import random  
    #     random.seed()

    #     x=random.random()*random.randrange(0, 15)
    #     y=random.random()*random.randrange(0,15)
    #     self.update_plot(x,y)


class Buttons(QtGui.QWidget):
    def __init__(self, parent=None, plot=None, logger=None):
        super(Buttons, self).__init__(parent)
        self.plot=plot
        self.logger=logger

    @property
    def ao_layout(self):
        buttonlayout = QtGui.QHBoxLayout()
        buttonlayout.setSpacing(0)
        buttonlayout.setMargin(0)
        spacer = QtGui.QWidget()
        spacer.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding) 
        refresh = QtGui.QPushButton(QtGui.QIcon.fromTheme('view-refresh'), 'Clear')
        refresh.clicked.connect(self.plot.refresh) 
        buttonlayout.addWidget(spacer)
        buttonlayout.addWidget(refresh)
 
        return buttonlayout

    @property
    def layout(self):
        buttonlayout = QtGui.QHBoxLayout()
        buttonlayout.setSpacing(0)
        buttonlayout.setMargin(0)
        zoomin = QtGui.QPushButton(QtGui.QIcon.fromTheme('zoom-in'), 'Zoom In')
        zoomin.clicked.connect(self.plot.zoomin)
        #zoomin.setStyleSheet('QPushButton {color: white;  background-color: lightgrey }')
        zoomout = QtGui.QPushButton(QtGui.QIcon.fromTheme('zoom-out'), 'Zoom Out')
        zoomout.clicked.connect(self.plot.zoomout)
        spacer = QtGui.QWidget()
        spacer.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding) 
        refresh = QtGui.QPushButton(QtGui.QIcon.fromTheme('view-refresh'), 'Clear')
        refresh.clicked.connect(self.plot.refresh) 
        buttonlayout.addWidget(zoomin)
        buttonlayout.addWidget(zoomout) 
        buttonlayout.addWidget(spacer)
        buttonlayout.addWidget(refresh)
 
        return buttonlayout
      
  
class FmosPlot(QtGui.QWidget):
    ''' Fmos Guiding '''
    def __init__(self, parent=None, logger=None):
        super(FmosPlot, self).__init__(parent)
        
        self.plot = Plot(parent=parent, logger=logger) 
        self.buttons = Buttons(parent=parent, plot=self.plot, logger=logger)
        
        self.logger=logger
        self.set_gui()

    def tick(self):

        import random  
        random.seed()

        x = random.random()*random.randrange(-2, 2)
        y = random.random()*random.randrange(-2,2)
        el = random.randrange(15,90) 

        state = ["Guiding(AGFMOS)", "Guiding(AGFMOS)", "Slewing", "Guiding(AGFMOS)",]
 
        sindx = random.randrange(0,4)
        state = state[sindx]

        self.update_plot(state, x, y, el)

    def set_gui(self):

        layout = QtGui.QVBoxLayout()        
        layout.setSpacing(0) 
        layout.setMargin(0)
        layout.addWidget(self.plot)


        layout.addLayout(self.buttons.layout)
        self.setLayout(layout)

    def update_plot(self, state, x, y, el):
        self.logger.debug('state=%s x=%s y=%s el=%s' %(state, x, y, el))
        fmos_guiding="Guiding(AGFMOS)"

        try:
            x = 1000.0 *  math.cos(math.radians(el)) * x 
            y *= 1000.0 
        except Exception as e:
            self.logger.error('error: x,y,el %s' %e)
        else: 
            if state == fmos_guiding:
                self.logger.debug('fmos guiding...')
                self.plot.update_plot(x, y)
            else:
                self.logger.debug('no guiding...')
                self.plot.clear()              


class NsIrPlot(QtGui.QWidget):
    '''  NsIr AO188 Plotting  '''
    def __init__(self, parent=None, logger=None):
        super(NsIrPlot, self).__init__(parent)
        
        self.ao1 = Ao1Plot(parent=parent, logger=logger) 
        self.buttons1 = Buttons(parent=parent, plot=self.ao1, logger=logger)

        self.ao2 = Ao2Plot(parent=parent, logger=logger) 
        self.buttons2 = Buttons(parent=parent, plot=self.ao2, logger=logger)

  
        self.logger=logger
        self.set_gui()

    def tick(self):

        import random  
        random.seed()

        x1 = random.random()*random.randrange(-11,11)
        y1 = random.random()*random.randrange(-11,11)
 
        x2 = random.random()*random.randrange(0, 15)
        y2 = random.random()*random.randrange(0,15)

        self.update_plot(x1, y1, x2, y2)

    def set_gui(self):

        layout = QtGui.QVBoxLayout()        
        layout.setSpacing(0)
        layout.setMargin(0)
        layout.addWidget(self.ao1)
        layout.addLayout(self.buttons1.ao_layout)
        layout.addWidget(self.ao2)
        layout.addLayout(self.buttons2.ao_layout)
        self.setLayout(layout)

    def update_plot(self, ao1x, ao1y, ao2x, ao2y):

        self.logger.debug('ao1x=%s ao1y=%s ao2x=%s ao2y=%s' %(ao1x, ao1y, ao2x, ao2y))

        try:
            ao1x*=1000.0
            ao1y*=1000.0
        except Exception:
            self.logger.debug('error: ao1 calc ')
            pass 
        else:
            self.ao1.update_plot(ao1x , ao1y)

        try:
            ao2x*=1000.0
            ao2y*=1000.0
        except Exception:
            pass 
        else:
            self.ao2.update_plot(ao2x , ao2y)
 

class AgPlot(QtGui.QWidget):
    '''  Ag Guiding  '''
    def __init__(self, parent=None, logger=None):
        super(AgPlot, self).__init__(parent)
        
        self.plot = Plot(parent=parent, logger=logger) 
        self.buttons = Buttons(parent=parent, plot=self.plot, logger=logger)  
        self.exptime = Exptime(parent=parent, logger=logger) 
        self.threshold = Threshold(parent=parent, logger=logger) 
        #self.empty = Dummy(width=60, height=25,  logger=logger)
        #self.empty1 = Dummy(width=1, height=25,  logger=logger)
        self.logger = logger
        self.set_gui()

    def tick(self):

        import random  

        state = ["Guiding(AG)", "Guiding(AG1)", "Guiding(AG2)",  "Slewing"]
        sindx = random.randrange(0,4)
        state = state[sindx]
        x = random.random()*random.randrange(-800,800)
        y = random.random()*random.randrange(-800,800)
        exptime = random.random()*random.randrange(0, 40000)
        bottom = random.randrange(0, 30000)
        ceil = random.randrange(30000, 70000)
        self.update_plot(state, x, y, exptime, bottom, ceil)

    def set_gui(self):

        layout = QtGui.QVBoxLayout()        
        layout.setSpacing(1) 
        layout.setMargin(0)
        layout.addWidget(self.plot)

        hlayout = QtGui.QHBoxLayout()   
        hlayout.setSpacing(2)
        hlayout.addWidget(self.exptime)
        hlayout.addWidget(self.threshold)
        layout.addLayout(hlayout)

        layout.addLayout(self.buttons.layout)
        self.setLayout(layout)

    def update_plot(self, state, x, y, exptime, bottom, ceil):
        self.logger.debug('state=%s x=%s y=%s' %(state, x, y))
        ag_guiding=("Guiding(AG)",  "Guiding(AG1)", "Guiding(AG2)", "Guiding(HSCSHAG)",
                    "Guiding(HSCSCAG)")

        if state in ag_guiding:
            self.logger.debug('ag guiding...')
            self.plot.update_plot(x, y)
            self.exptime.update_exptime(exptime)
            self.threshold.update_threshold(bottom, ceil)
        else:
            self.logger.debug('no guiding...')
            self.plot.clear()  
            self.exptime.clear() 
            self.threshold.clear()           


class TwoGuidingPlot(QtGui.QWidget):
    ''' Ns-Opt AG/SV, HSCSC/SHAG Guiding  '''
    def __init__(self, parent=None, logger=None):
        super(TwoGuidingPlot, self).__init__(parent)
        
        self.plot = Plot(parent=parent, logger=logger)
        self.exptime = Exptime(parent=parent, logger=logger) 
        self.threshold = Threshold(parent=parent, logger=logger) 
        self.buttons = Buttons(parent=parent, plot=self.plot, logger=logger)  
        self.logger = logger
        self.set_gui()

    def set_gui(self):

        layout = QtGui.QVBoxLayout()        
        layout.setSpacing(1) 
        layout.setMargin(0)
        layout.addWidget(self.plot)

        hlayout = QtGui.QHBoxLayout()   
        hlayout.setSpacing(2)
        hlayout.addWidget(self.exptime)
        hlayout.addWidget(self.threshold)
        layout.addLayout(hlayout)

        layout.addLayout(self.buttons.layout)
        self.setLayout(layout)

    def update_plot(self, state, \
                    guiding1_x, guiding1_y, \
                    guiding2_x, guiding2_y, \
                    guiding1_exp, guiding2_exp, \
                    guiding1_bottom, guiding1_ceil, \
                    guiding2_bottom, guiding2_ceil):
        
        self.logger.debug("state=%s g1x=%s g1y=%s g2x=%s g2y=%s g1exp=%s g2exp=%s g1bottom=%s  g1ceil=%s g2bottom=%s g2ceil=%s" %(state, guiding1_x, guiding1_y, guiding2_x, guiding2_y, guiding1_exp, guiding2_exp, guiding1_bottom, guiding1_ceil, guiding2_bottom, guiding2_ceil))

        guiding1 = ("Guiding(AG1)", "Guiding(AG2)", "Guiding(HSCSCAG)")
        guiding2 = ("Guiding(SV1)", "Guiding(SV2)", "Guiding(HSCSHAG)")  

        if state in guiding1:
            self.logger.debug('state=%s guiding1...' %state)
            self.plot.update_plot(guiding1_x, guiding1_y)
            self.exptime.update_exptime(exptime=guiding1_exp)
            self.threshold.update_threshold(bottom=guiding1_bottom, ceil=guiding1_ceil)
        elif state in guiding2:
            self.logger.debug('state=%s guiding2...' %state)
            self.plot.update_plot(guiding2_x, guiding2_y)
            self.exptime.update_exptime(exptime=guiding2_exp)
            self.threshold.update_threshold(bottom=guiding2_bottom, ceil=guiding2_ceil)
        else:
            self.logger.debug('state=%s no guiding...' %state)
            self.plot.clear()              
            self.exptime.clear()
            self.threshold.clear()

    def tick(self):

        import random  
        random.seed()

        state = ["Guiding(AG1)", "Guiding(AG2)", \
                 "Guiding(SV1)","Guiding(SV2)",  \
                 "Guiding(HSCSCAG)", "Guiding(HSCSHAG)", \
                 "Slewing"]
 
        sindx = random.randrange(0,7)
        state = state[sindx]
        guiding1_x = guiding2_x = random.random()*random.randrange(-800,800)
        guiding1_y = guiding2_y = random.random()*random.randrange(-800,800)
        guiding1_exp = guiding2_exp = random.random()*random.randrange(0, 40000)
        guiding1_bottom = guiding2_bottom = random.randrange(0, 30000)
        guiding1_ceil = guiding2_ceil = random.randrange(30000, 70000)

        self.update_plot(state, \
                    guiding1_x, guiding1_y, \
                    guiding2_x, guiding2_y, \
                    guiding1_exp, guiding2_exp, \
                    guiding1_bottom, guiding1_ceil, \
                    guiding2_bottom, guiding2_ceil)


# class NsOptPlot(QtGui.QWidget):
#     ''' Ns Opt AG/SV Guiding  '''
#     def __init__(self, parent=None, logger=None):
#         super(NsOptPlot, self).__init__(parent)
        
#         self.plot = Plot(parent=parent, logger=logger)
#         self.exptime = Exptime(parent=parent, logger=logger) 
#         self.threshold = Threshold(parent=parent, logger=logger) 
#         self.buttons = Buttons(parent=parent, plot=self.plot, logger=logger)  
#         self.logger = logger
#         self.set_gui()

#     def tick(self):

#         import random  
#         random.seed()

#         state = ["Guiding(AG)", "Guiding(AG1)", "Guiding(AG2)",  
#                  "Guiding(SV)", "Guiding(SV1)","Guiding(SV2)",  "Slewing"]
 
#         sindx = random.randrange(0,7)
#         state = state[sindx]
#         x = random.random()*random.randrange(-800,800)
#         y = random.random()*random.randrange(-800,800)
#         exp = random.random()*random.randrange(0, 40000)
#         bottom = random.randrange(0, 30000)
#         ceil = random.randrange(30000, 70000)
#         self.update_plot(state=state, ag_x=x, ag_y=y, sv_x=x, sv_y=y, \
#                          ag_exp=exp, sv_exp=exp, ag_bottom=bottom, \
#                          ag_ceil=ceil, sv_bottom=bottom, sv_ceil=ceil)

#     def set_gui(self):

#         layout = QtGui.QVBoxLayout()        
#         layout.setSpacing(1) 
#         layout.setMargin(0)
#         layout.addWidget(self.plot)

#         hlayout = QtGui.QHBoxLayout()   
#         hlayout.setSpacing(2)
#         hlayout.addWidget(self.exptime)
#         hlayout.addWidget(self.threshold)
#         layout.addLayout(hlayout)

#         layout.addLayout(self.buttons.layout)
#         self.setLayout(layout)

#     def update_plot(self, state, ag_x, ag_y, sv_x, sv_y, \
#                     ag_exp, sv_exp, ag_bottom, ag_ceil, sv_bottom, sv_ceil):
#         self.logger.debug('state=%s x=%s y=%s bottom=%s ceil=%s ' \
#                           %(state, ag_x, ag_y, ag_bottom, ag_ceil))
#         ag_guiding = ("Guiding(AG)",  "Guiding(AG1)", "Guiding(AG2)")
#         sv_guiding = ("Guiding(SV)", "Guiding(SV1)","Guiding(SV2)")  

#         if state in ag_guiding:
#             self.logger.debug('ag guiding...')
#             self.plot.update_plot(ag_x, ag_y)
#             self.exptime.update_exptime(exptime=ag_exp)
#             self.threshold.update_threshold(bottom=ag_bottom, ceil=ag_ceil)
#         elif state in sv_guiding:
#             self.logger.debug('sv guiding...')
#             self.plot.update_plot(sv_x, sv_y)
#             self.exptime.update_exptime(exptime=sv_exp)
#             self.threshold.update_threshold(bottom=sv_bottom, ceil=sv_ceil)
#         else:
#             self.logger.debug('no guiding...')
#             self.plot.clear()              
#             self.exptime.clear()
#             self.threshold.clear()


def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('plot', options)
 
    class AppWindow(QtGui.QMainWindow):
        def __init__(self):
            QtGui.QMainWindow.__init__(self)
            self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

            self.resize(350, 350)

            self.main_widget = QtGui.QWidget()
            l = QtGui.QVBoxLayout(self.main_widget)
            l.setMargin(0) 
            l.setSpacing(0)
            
            #sc = MyStaticMplCanvas(self.main_widget, width=5, height=5, dpi=None)
           
            if options.mode == 'ag':
                plot = AgPlot(self.main_widget, logger=logger)
                #aplot=AOPlot1(self.main_widget, logger=logger)
            elif options.mode == 'fmos':
                plot=FmosPlot(self.main_widget, logger=logger)
            elif options.mode == 'nsopt' or options.mode == 'hsc':   
                plot = TwoGuidingPlot(self.main_widget, logger=logger)
            elif options.mode == 'nsir':   
                plot = NsIrPlot(self.main_widget, logger=logger)
            else:
                logger.error('error: mode=%s' %options.mode)
                sys.exit(1)
            #l.addWidget(sc)
            #zoomin = QtGui.QPushButton(QtGui.QIcon.fromTheme('zoom-in'), 'Zoom In')
            l.addWidget(plot)
            ##l.addWidget(aplot)
            ##l.addWidget(zoomin)
            timer = QtCore.QTimer(self)
            QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"), plot.tick)
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
                      help="Specify a plotting mode [ag | nsopt | nsir | fmos]")

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


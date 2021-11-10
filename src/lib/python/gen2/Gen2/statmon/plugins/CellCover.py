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

import ssdlog
import PlBase
from error import ERROR

progname = os.path.basename(sys.argv[0])
progversion = "0.1"

 
class CellCanvas(FigureCanvas):
    """ AG/SV/FMOS/AO188 Plotting """
    def __init__(self, parent=None, width=3, height=3,  logger=None):

        sub=SubplotParams(left=0.0, right=1, bottom=0, top=1, wspace=0, hspace=0)
        self.fig = Figure(figsize=(width, height), facecolor='white', subplotpars=sub )
        self.axes = self.fig.add_subplot(111)
        # We want the axes cleared every time plot() is called
        #self.axes.hold(False)
        #self.axes.grid(True)
        
        self.closed_color='black'
        self.open_color='white'
        self.onway_color='orange'
        self.alarm_color='red'

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QtGui.QSizePolicy.Expanding, \
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        # width/hight of widget
        self.w=250
        self.h=30
        self.logger=logger
   
        self.init_figure()
  
    def init_figure(self):
        ''' initial drawing '''

        # draw cell cover
        cell_kwargs=dict(alpha=0.7, fc=self.closed_color, ec='grey', lw=1.5) 
        self.cell= mpatches.Rectangle((0.25, 0.75), 0.5, 0.2, **cell_kwargs)
        self.axes.add_patch(self.cell)

        # draw text
        self.text=self.axes.text(0.5, 0.5, 'Initializing', \
                                 va='top', ha='center', \
                                 transform=self.axes.transAxes, fontsize=11)

        self.axes.axison=False
        self.draw()

    def minimumSizeHint(self):
        return QtCore.QSize(self.w, self.h)

    def sizeHint(self):
         return QtCore.QSize(self.w, self.h)


class CellCover(CellCanvas):
    
    """A canvas that updates itself every second with a new plot."""
    def __init__(self,*args, **kwargs):
 
        #super(AGPlot, self).__init__(*args, **kwargs)
        CellCanvas.__init__(self, *args, **kwargs)

    def update_cell(self, cell):
        ''' cell = 'TSCV.CellCover'  '''
        self.logger.debug('updating cell=%s' %(cell))  

        if cell == 0x01: # cell cover open
            self.text.set_text('Cell Cover Open')
            self.cell.set_facecolor(self.open_color)
        elif cell == 0x04: # cell cover close
            self.text.set_text('Cell Cover Closed')
            self.cell.set_facecolor(self.closed_color)
        elif cell == 0x00: # cell cover on-way
            self.text.set_text('Cell Cover OnWay')
            self.cell.set_facecolor(self.onway_color)
        else:  # # cell cover unknown status
            self.text.set_text('Cell Cover Undef')
            self.cell.set_facecolor(self.alarm_color)

        self.draw()

    def tick(self):
        ''' testing  mode solo '''
        import random  
        random.seed()

        indx=random.randrange(0, 8)
        cell=[0x01, 'Unknown', None, '##STATNONE##', 0x00, '##NODATA##', '##ERROR##', 0x04]
        try:
            cell=cell[indx]
        except Exception:
            cell=None
    
        self.update_cell(cell)


def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('plot', options)
 
    class AppWindow(QtGui.QMainWindow):
        def __init__(self):
            QtGui.QMainWindow.__init__(self)
            self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.w=250
            self.h=20
            self.setup()

        def setup(self):
            self.resize(self.w, self.h)
            self.main_widget = QtGui.QWidget(self)

            l = QtGui.QVBoxLayout(self.main_widget)
            cell =  CellCover(self.main_widget, logger=logger)

            l.addWidget(cell)

            timer = QtCore.QTimer(self)
            QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"), cell.tick)
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
                      default='az',
                      help="Specify a plotting mode [az | rot | ag ]")

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

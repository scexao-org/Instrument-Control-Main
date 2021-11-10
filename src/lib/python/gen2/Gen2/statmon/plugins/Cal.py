#!/usr/bin/env python

import os
import sys

from PyQt4 import QtGui, QtCore
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib.patches as mpatches
from matplotlib.figure import SubplotParams
from matplotlib.artist import Artist

from CanvasLabel import Canvas, QtCore, QtGui, Qt, ERROR
import ssdlog
from Bunch import Bunch
import PlBase
from error import *


progname = os.path.basename(sys.argv[0])
progversion = "0.1"


class CalCanvas(FigureCanvas):
    """ Cal Source Canvas """
    def __init__(self, parent=None, width=1, height=1,  dpi=None, logger=None):
      
        sub=SubplotParams(left=0.0, bottom=0, right=1, \
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

 
        self.normal = 'green'
        self.warn = 'orange'
        self.alarm = 'red'
        self.bg = 'white'

        self.x_scale=[0, 1]
        self.y_scale=[0,  2]

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        #FigureCanvas.setSizePolicy(self, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        #FigureCanvas.updateGeometry(self)

        # width/hight of widget
        self.w=200
        self.h=40
        #FigureCanvas.resize(self, self.w, self.h)

        self.logger=logger
   
        self.init_figure()
  
    def init_figure(self):
        ''' initial drawing '''

        common_keys = dict(va='baseline', ha="center", color=self.normal, size=11)       
        w = 0.11
        h = 0.6 
   
        kargs = dict(fc=self.bg, ec=self.normal, lw=1.5) 
        # Th-Ar1 Label
        self.axes.text(0.11, 1.2, "Th-Ar1", common_keys)

        # Th-Ar1 frame
        bs = mpatches.BoxStyle("Round4", pad=0.05) 
        self.th_ar1 = mpatches.FancyBboxPatch((0.05, 1.1), w, h, \
                                          boxstyle=bs, **kargs)
        self.axes.add_patch(self.th_ar1)

        # Th-Ar2 Label
        self.axes.text(0.11, 0.25, "Th-Ar2", common_keys)

        # Th-Ar2 frame
        self.th_ar2 = mpatches.FancyBboxPatch((0.05, 0.2), w, h, \
                                          boxstyle=bs, **kargs)
        self.axes.add_patch(self.th_ar2)

        # Ne Label
        self.axes.text(0.36, 1.2, "Ne", common_keys)

        # Ne frame
        self.ne = mpatches.FancyBboxPatch((0.3, 1.1), w, h, \
                                          boxstyle=bs, **kargs)
        self.axes.add_patch(self.ne)

        # Ar Label
        self.axes.text(0.36, 0.25, "Ar", common_keys)

        # ar frame
        self.ar = mpatches.FancyBboxPatch((0.3, 0.2), w, h, \
                                          boxstyle=bs, **kargs)
        self.axes.add_patch(self.ar)

        # hal1 Label
        self.axes.text(0.6, 1.2, "Hal1", common_keys)

        # hal1 frame
        self.hal1 = mpatches.FancyBboxPatch((0.55, 1.1), w, h, \
                                          boxstyle=bs, **kargs)
        self.axes.add_patch(self.hal1)

        # hal2 Label
        self.axes.text(0.6, 0.25, "Hal2", common_keys)

        # hal2 frame
        self.hal2 = mpatches.FancyBboxPatch((0.55, 0.2), w, h, \
                                          boxstyle=bs, **kargs)
        self.axes.add_patch(self.hal2)

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


class Cal(CalCanvas):
    """ Cal Source """
    def __init__(self,*args, **kwargs):
 
        #super(AGPlot, self).__init__(*args, **kwargs)
        CalCanvas.__init__(self, *args, **kwargs)

        # display milliampere(mA)
        self.ma = Canvas(parent=kwargs['parent'], fs=8, width=175,\
                             height=25, align='vcenter', \
                             logger=kwargs['logger'])

        self.ma.setText('')
        self.ma.setIndent(15)
        self.on = 1
        self.off =2

    def __num_of_undef_vals(self, val_set):
        ''' find out the number of undefined values'''

        for val in [self.on, self.off]:
            try:
                val_set.remove(val)
            except KeyError:
                pass 
        return len(val_set)

    def __mask_value(self, val, focus):

        mask = {'CS': 0x03, 'NSIR': 0x30, 'NSOPT': 0x0c, \
                'PF1': 0x30, 'PF2': 0xc0}
        try:
            #val = int('%s' %val, 16)
            val = val & mask[focus]
        except Exception:
            val = None
        finally:
            return val 

    def __shift_value(self, val, focus):
        ''' right shift '''
        shift = {'CS': 0, 'NSIR': 4, 'NSOPT': 2, \
                 'PF1': 4, 'PF2': 6}
 
        masked = self.__mask_value(val, focus)       
 
        try:
            val = masked >> shift[focus]
        except Exception:
            val = None
        finally:
            return val  

    def __update(self, lamps, num_on):
   
        for lamp, val in  lamps.items():  
            vals = set(val.lamp)
            num_undef = self.__num_of_undef_vals(val_set=vals)       
             
            self.logger.debug('lamps  %s'%vals)
            self.logger.debug('num undef %s' %str(num_undef))
 
            if num_undef:
                lamp.set_fc(self.alarm)
                lamp.set_alpha(1)
            else:
                self.logger.debug('val lamp %s' %str(val.lamp))
                self.logger.debug('val amp %s' %str(val.amp)) 
                ma = ''
                if self.on in val.lamp:
                    lamp.set_fc(self.normal)
                    lamp.set_alpha(0.5)
                    self.logger.debug('on')

                    self.logger.debug('val amp=%s' %val.amp) 
                    
                    if num_on > self.on: # at least 2 lamps are on
                        lamp.set_fc(self.warn)
                        lamp.set_alpha(1)
                    else: # 1 lamp is on
                        if not val.amp in ERROR:
                            ma = '%+5.3fmA' %val.amp
                        self.ma.setText(ma)
                        self.logger.debug('amp=%s' %str(ma))
                else:
                    self.logger.debug('off')
                    #if not ma:
                    #    self.ma.setText(ma) 
                    lamp.set_fc(self.bg)
                    lamp.set_alpha(1)

    def update_cal(self, hct1, hct2, hal1, hal2, rgl1, rgl2, \
                   hct1_amp, hct2_amp, hal1_amp, hal2_amp, \
                   rgl1_amp=None, rgl2_amp=None):
        ''' hct1 = TSCV.CAL_HCT_LAMP1
            hct2 = TSCV.CAL_HCT_LAMP2
            hal1 = TSCV.CAL_HAL_LAMP1
            hal2 = TSCV.CAL_HAL_LAMP2
            rgl1 = TSCV.CAL_RGL_LAMP1
            rgl2 = TSCV.CAL_RGL_LAMP2

            hal1_amp = TSCL.CAL_HAL1_AMP
            hal2_amp = TSCL.CAL_HAL2_AMP
            hct1_amp = TSCL.CAL_HCT1_AMP
            hct2_amp = TSCL.CAL_HCT2_AMP
        '''
        # hct1 = (hct1_cs, hct1_nsopt, hct1_pf1, hct1_pf2)
        # hct2 = (hct2_cs, hct2_nsopt)
        # hal1 = (hal1_cs, hal1_nsopt, hal1_nsir)
        # hal2 = (hal2_cs, hal2_nsopt, hal2_nsir)
        # rgl1 = (rgl1_cs, rgl1_nsir)
        # rgl2 = (rgl2_cs, rgl2_nsir)

        self.logger.debug('updating hct1=%s hct2=%s hal1=%s hal2=%s rgl1=%s rgl2=%s' %(hct1, hct2, hal1, hal2, rgl1, rgl2)) 

        hct1_cs = self.__shift_value(hct1, focus='CS')
        hct1_nsopt = self.__shift_value(hct1, focus='NSOPT')
        hct1_pf1 = self.__shift_value(hct1, focus='PF1')
        hct1_pf2 = self.__shift_value(hct1, focus='PF2')

        hct2_cs = self.__shift_value(hct2, focus='CS')
        hct2_nsopt = self.__shift_value(hct2, focus='NSOPT')

        hal1_cs = self.__shift_value(hal1, focus='CS')
        hal1_nsopt = self.__shift_value(hal1, focus='NSOPT')
        hal1_nsir = self.__shift_value(hal1, focus='NSIR')

        hal2_cs = self.__shift_value(hal2, focus='CS')
        hal2_nsopt = self.__shift_value(hal2, focus='NSOPT')
        hal2_nsir = self.__shift_value(hal2, focus='NSIR')

        rgl1_cs = self.__shift_value(rgl1, focus='CS')
        rgl1_nsir = self.__shift_value(rgl1, focus='NSIR')

        rgl2_cs = self.__shift_value(rgl2, focus='CS')
        rgl2_nsir = self.__shift_value(rgl2, focus='NSIR')


        bhct1 = Bunch(lamp=(hct1_cs, hct1_nsopt, hct1_pf1, hct1_pf2), amp=hct1_amp)
        bhct2 = Bunch(lamp=(hct2_cs, hct2_nsopt), amp=hct2_amp)
        bhal1 = Bunch(lamp= (hal1_cs, hal1_nsopt, hal1_nsir), amp=hal1_amp)
        bhal2 = Bunch(lamp=(hal2_cs, hal2_nsopt, hal2_nsir), amp=hal2_amp)
        brgl1 = Bunch(lamp=(rgl1_cs, rgl1_nsir), amp=rgl1_amp)
        brgl2 = Bunch(lamp=(rgl2_cs, rgl2_nsir), amp=rgl2_amp)
        blamps = {self.th_ar1: bhct1, self.th_ar2: bhct2, \
                  self.hal1: bhal1, self.hal2: bhal2, \
                  self.ne: brgl1, self.ar: brgl2}

        self.logger.debug('shifted hct1cs=%s htc1nsopt=%s hct1pf1=%s hct1pf2=%s'  %(str(hct1_cs), str(hct1_nsopt), str(hct1_pf1), str(hct1_pf2))) 

        lamps = [hct1_cs, hct1_nsopt, hct1_pf1, hct1_pf2, hct2_cs, hct2_nsopt, \
                 hal1_cs, hal1_nsopt, hal1_nsir, hal2_cs, hal2_nsopt, hal2_nsir, \
                 rgl1_cs, rgl1_nsir, rgl2_cs, rgl2_nsir]

        num_on = lamps.count(self.on)   

        self.__update(blamps, num_on)

        self.draw()


class CalDisplay(QtGui.QWidget):
    def __init__(self, parent=None, logger=None):
        super(CalDisplay, self).__init__(parent)
   
        self.cal_label = Canvas(parent=parent, fs=10, width=175,\
                                height=25, align='vcenter', weight='bold', \
                                logger=logger)

        self.cal_label.setText('Cal')
        self.cal_label.setIndent(15)

        self.cal = Cal(parent=parent, logger=logger)
        self.__set_layout() 

    def __set_layout(self):
 
        hlayout = QtGui.QHBoxLayout()
        hlayout.setSpacing(0) 
        hlayout.setMargin(0)  

        vlayout = QtGui.QVBoxLayout()
        vlayout.setSpacing(0) 
        vlayout.setMargin(0)
        vlayout.addWidget(self.cal_label)
        vlayout.addWidget(self.cal.ma)
       
        hlayout.addLayout(vlayout)

        hlayout.addWidget(self.cal)
        self.setLayout(hlayout)

    def update_cal(self, hct1, hct2, hal1, hal2, rgl1, rgl2, \
                   hct1_amp, hct2_amp, hal1_amp, hal2_amp):

        self.cal.update_cal(hct1, hct2, hal1, hal2, rgl1, rgl2, \
                            hct1_amp, hct2_amp, hal1_amp, hal2_amp)

    def tick(self):
        ''' testing solo mode '''
        import random  

        # off  
        hct1= 'aa'; hct2= 'a'
        hal1 = hal2 = '2a'
        rgl1 = rgl2 = '22'

        #hal1 = '1a'
        #hal2 = '2a'

        # on
        hct1= 'a9'; hct2 = '9' 

        # test
        hct1= '6a'; hct2 = 'a' 
        #hct1= 'aa'; hct2 = 'a' 


        hct1_amp = hct2_amp = 14.86
        hal1_amp = hal2_amp = 54.321
        self.update_cal(hct1, hct2, hal1, hal2, rgl1, rgl2, \
                        hct1_amp, hct2_amp, hal1_amp, hal2_amp)



def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('el', options)
 
    class AppWindow(QtGui.QMainWindow):
        def __init__(self):
            QtGui.QMainWindow.__init__(self)
            self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.w=275; self.h=40;
            self.setup()

        def setup(self):
            self.resize(self.w, self.h)
            self.main_widget = QtGui.QWidget(self)

            l = QtGui.QVBoxLayout(self.main_widget)
            cal = CalDisplay(self.main_widget, logger=logger)
            l.addWidget(cal)

            timer = QtCore.QTimer(self)
            QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"), cal.tick)
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

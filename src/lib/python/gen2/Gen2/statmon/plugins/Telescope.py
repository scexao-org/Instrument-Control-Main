#!/usr/bin/env python

# This is only needed for Python v2 but is harmless for Python v3.
#import sip
#sip.setapi('QVariant', 2)
import os
import sys

from PyQt4 import QtCore, QtGui

import ssdlog
from DomeShutter import DomeShutter
from Topscreen import Topscreen
from Windscreen import Windscreen
from FocusZ import FocusZ
from Focus import Focus
#from El import El
from AzEl import AzEl
from M2 import M2
from M1Cover import M1Cover
from CellCover import CellCover
import InsRot
import ImgRot
import Adc
from TipChop import TipChop
from Waveplate import Waveplate
from Dummy import Dummy

progname = os.path.basename(sys.argv[0])

class TelescopeGui(QtGui.QWidget):
    def __init__(self, parent=None, obcp=None, logger=None):
        super(TelescopeGui, self).__init__(parent) 
        
        self.obcp = obcp
        self.logger = logger
        self.dome_shutter = DomeShutter(logger=logger)
        self.topscreen = Topscreen(logger=logger)
        self.windscreen = Windscreen(logger=logger)
        self.z = FocusZ(logger=logger) 
        self.focus = Focus(logger=logger)  
        #self.el=El(logger=logger)
        self.azel = AzEl(logger=logger) 
        self.m2 = M2(logger=logger)   
        self.m1 = M1Cover(logger=logger) 
        self.cell = CellCover(logger=logger)   
        self.resize(500, 500)
        self.set_layout()

    def set_layout(self):
   
        mainlayout = QtGui.QVBoxLayout()        
        mainlayout.setSpacing(0) 
        mainlayout.setMargin(0)
        
        # dome part of telescope
        toplayout = QtGui.QVBoxLayout()
        toplayout.setSpacing(0) 
        toplayout.addWidget(self.dome_shutter)
        toplayout.addWidget(self.topscreen)

        # middle part of telescope
        middlelayout = QtGui.QVBoxLayout()

        # focusing part of telescope
        telfocuslayout=QtGui.QVBoxLayout()
        telfocuslayout.addWidget(self.z)
        telfocuslayout.addWidget(self.m2)
        telfocuslayout.addWidget(self.focus)

        # telesocpe body 
        telbodylayout=QtGui.QVBoxLayout()
        telbodylayout.setSpacing(0) 
        #telbodylayout.addWidget(self.el)
        telbodylayout.addWidget(self.azel)
        telbodylayout.addWidget(self.m1)
        telbodylayout.addWidget(self.cell)
      
        middlelayout.addLayout(telfocuslayout)
        middlelayout.addLayout(telbodylayout)

        # right layout will be combination of following components: 
        # ins/img-rot, adc, tiptilt, wavepalte  
        rightlayout=QtGui.QVBoxLayout()
        self.set_focus_layout(rlayout=rightlayout)

        # combine right, middle, left layout
        telhlayout=QtGui.QHBoxLayout()
        telhlayout.setSpacing(0)  
        telhlayout.addWidget(self.windscreen)
        telhlayout.addLayout(middlelayout)
        telhlayout.addLayout(rightlayout)

        mainlayout.addLayout(toplayout)
        mainlayout.addLayout(telhlayout)
        self.setLayout(mainlayout)

    def popt_layout(self, rlayout):
        ''' prime focus optical'''
        r1layout=QtGui.QVBoxLayout()
        #r1layout.addWidget(self.d1)
        empty_shell=Dummy(height=95, logger=self.logger) 
        r1layout.addWidget(empty_shell)

        r2layout=QtGui.QVBoxLayout()
        r2layout.setSpacing(1)
        empty_shell=Dummy(height=1, logger=self.logger)    
        r2layout.addWidget(empty_shell)
        self.insrot=InsRot.InsRotPf(logger=self.logger)   
        r2layout.addWidget(self.insrot) 
        self.adc = Adc.AdcPf(logger=self.logger) 
        r2layout.addWidget(self.adc) 
        empty_shell=Dummy(height=285, logger=self.logger)
        r2layout.addWidget(empty_shell)

        rlayout.addLayout(r1layout)
        rlayout.addLayout(r2layout)
   
    def pir_layout(self, rlayout): 
        ''' prime focus infrared'''
        r1layout=QtGui.QVBoxLayout()
        #r1layout.addWidget(self.d1)
        empty_shell=Dummy(height=95, logger=self.logger) 
        r1layout.addWidget(empty_shell)

        r2layout=QtGui.QVBoxLayout()
        r2layout.setSpacing(1)

        empty_shell=Dummy(height=1, logger=self.logger)    
        r2layout.addWidget(empty_shell)

        self.insrot=InsRot.InsRotPf(logger=self.logger)   
        r2layout.addWidget(self.insrot) 

        empty_shell=Dummy(height=320, logger=self.logger)
        r2layout.addWidget(empty_shell)

        rlayout.addLayout(r1layout)
        rlayout.addLayout(r2layout)

    def nsopt_layout(self, rlayout):
        ''' nasmyth focus optical'''
        r1layout=QtGui.QVBoxLayout()
        #r1layout.addWidget(self.d1)
        empty_shell=Dummy(height=95, logger=self.logger) 
        r1layout.addWidget(empty_shell)

        r2layout=QtGui.QVBoxLayout()
        r2layout.setSpacing(1)
        empty_shell=Dummy(height=1, logger=self.logger)    
        r2layout.addWidget(empty_shell)
        self.imgrot=ImgRot.ImgRotNsOpt(logger=self.logger)   
        r2layout.addWidget(self.imgrot) 
        self.adc = Adc.Adc(logger=self.logger) 
        r2layout.addWidget(self.adc) 
        empty_shell=Dummy(height=277, logger=self.logger)
        r2layout.addWidget(empty_shell)

        rlayout.addLayout(r1layout)
        rlayout.addLayout(r2layout)

    def nsir_layout(self, rlayout):
        ''' nasmyth focus infrared'''

        r1layout=QtGui.QVBoxLayout()
        #r1layout.addWidget(self.d1)
        empty_shell=Dummy(height=95, logger=self.logger) 
        r1layout.addWidget(empty_shell)

        r2layout=QtGui.QVBoxLayout()
        r2layout.setSpacing(1)
        empty_shell=Dummy(height=1, logger=self.logger)    
        r2layout.addWidget(empty_shell)
        self.imgrot=ImgRot.ImgRotNsIr(logger=self.logger)   
        r2layout.addWidget(self.imgrot) 
        self.waveplate=Waveplate(logger=self.logger)   
        r2layout.addWidget(self.waveplate) 
        empty_shell=Dummy(height=250, logger=self.logger)
        r2layout.addWidget(empty_shell)

        rlayout.addLayout(r1layout)
        rlayout.addLayout(r2layout)

    def cs_layout(self, rlayout):
        ''' cassegrain focus ''' 
        r1layout = QtGui.QVBoxLayout()
        #r1layout.addWidget(self.d1)
        empty_shell = Dummy(height=95, logger=self.logger) 
        r1layout.addWidget(empty_shell)

        r2layout = QtGui.QVBoxLayout()
        r2layout.setSpacing(1)
        empty_shell = Dummy(height=1, logger=self.logger)    
        r2layout.addWidget(empty_shell)

        self.insrot = InsRot.InsRotCs(logger=self.logger)   
        r2layout.addWidget(self.insrot)
 
        empty_shell = Dummy(height=320, logger=self.logger)
        r2layout.addWidget(empty_shell)

        rlayout.addLayout(r1layout)
        rlayout.addLayout(r2layout)

    def csir_layout(self, rlayout):
        ''' cassegrain focus infrared '''

        r1layout = QtGui.QVBoxLayout()
        #r1layout.addWidget(self.d1)
        empty_shell = Dummy(height=25, logger=self.logger) 
        r1layout.addWidget(empty_shell)

        self.tipchop = TipChop(logger=self.logger)
        r1layout.addWidget(self.tipchop)

        empty_shell = Dummy(height=35, logger=self.logger) 
        r1layout.addWidget(empty_shell)

        r2layout = QtGui.QVBoxLayout()
        r2layout.setSpacing(1)

        empty_shell = Dummy(height=1, logger=self.logger)    
        r2layout.addWidget(empty_shell)

        self.insrot = InsRot.InsRotCs(logger=self.logger)   
        r2layout.addWidget(self.insrot) 

        empty_shell = Dummy(height=320, logger=self.logger)
        r2layout.addWidget(empty_shell)

        rlayout.addLayout(r1layout)
        rlayout.addLayout(r2layout)

    def csopt_layout(self, rlayout):
        ''' cassegrain focus optical '''

        r1layout=QtGui.QVBoxLayout()
        #r1layout.addWidget(self.d1)
        empty_shell = Dummy(height=95, logger=self.logger) 
        r1layout.addWidget(empty_shell)

        r2layout = QtGui.QVBoxLayout()
        r2layout.setSpacing(1)
        empty_shell = Dummy(height=1, logger=self.logger)    
        r2layout.addWidget(empty_shell)

        self.insrot = InsRot.InsRotCs(logger=self.logger)   
        r2layout.addWidget(self.insrot)
 
        self.adc = Adc.Adc(logger=self.logger) 
        r2layout.addWidget(self.adc) 
        empty_shell=Dummy(height=285, logger=self.logger)
        r2layout.addWidget(empty_shell)

        rlayout.addLayout(r1layout)
        rlayout.addLayout(r2layout)

    def set_focus_layout(self, rlayout):
        ''' spcam/hsc: insrot,adc 
            fmos: insrot
            hds:  imgrot,adc
            ircs/hiciao/k3d: imgrot,waveplate
            comics: insrot,tipchop
            focas: insrot,adc
            moircs insrot 
        ''' 
        focus = {'HDS': self.nsopt_layout, 'SPCAM': self.popt_layout, \
                 'HICIAO': self.nsir_layout, 'IRCS': self.nsir_layout, \
                 'FMOS': self.pir_layout, 'HSC': self.popt_layout, \
                 'K3D': self.nsir_layout, 'MOIRCS': self.cs_layout, \
                 'FOCAS': self.csopt_layout, 'COMICS': self.csir_layout, \
                 'SUKA': self.cs_layout}

        self.logger.debug('telescope focuslayout ins=%s' %self.obcp) 

        try:
            focus[self.obcp](rlayout)
        except Exception as e:
            self.logger.error('error: setting focus layout. %s' %str(e))
            pass

class Telescope(TelescopeGui):
    def __init__(self, parent=None, obcp=None, logger=None):
        super(Telescope, self).__init__(parent=parent, obcp=obcp, logger=logger) 

    def update_nsir(self, **kargs):
        self.imgrot.update_imgrot(imgrot=kargs.get('TSCV.ImgRotRotation'), \
                                  mode=kargs.get('TSCV.ImgRotMode'), \
                                  focus=kargs.get('TSCV.FOCUSINFO'), \
                                  itype=kargs.get('TSCV.ImgRotType'))

        self.waveplate.update_waveplate(stage1=kargs.get('WAV.STG1_PS'), \
                                        stage2=kargs.get('WAV.STG2_PS'), \
                                        stage3=kargs.get('WAV.STG3_PS'),)

    def update_csir(self, **kargs):
        self.tipchop.update_tipchop(mode=kargs.get('TSCV.TT_Mode'), \
                                    drive=kargs.get('TSCV.TT_Drive'), \
                                    data=kargs.get('TSCV.TT_DataAvail'), \
                                    state=kargs.get('TSCV.TT_ChopStat'))

        self.insrot.update_insrot(insrot=kargs.get('TSCV.InsRotRotation'), \
                                  mode=kargs.get('TSCV.InsRotMode'))

    def update_csopt(self, **kargs):

        self.insrot.update_insrot(insrot=kargs.get('TSCV.InsRotRotation'), \
                                  mode=kargs.get('TSCV.InsRotMode'))
        
        self.adc.update_adc(on_off=kargs.get('TSCV.ADCOnOff'), \
                            mode=kargs.get('TSCV.ADCMode'), \
                            in_out=kargs.get('TSCV.ADCInOut'))

    def update_cs(self, **kargs):
        self.insrot.update_insrot(insrot=kargs.get('TSCV.InsRotRotation'), \
                                  mode=kargs.get('TSCV.InsRotMode'))

    def update_pir(self, **kargs):

        self.insrot.update_insrot(insrot=kargs.get('TSCV.INSROTROTATION_PF'), \
                                  mode=kargs.get('TSCV.INSROTMODE_PF'))

    def update_popt(self, **kargs):

        self.insrot.update_insrot(insrot=kargs.get('TSCV.INSROTROTATION_PF'), \
                                  mode=kargs.get('TSCV.INSROTMODE_PF'))
        
        # self.adc.update_adc(on_off=kargs.get('TSCV.ADCONOFF_PF'), \
        #                     mode=kargs.get('TSCV.ADCMODE_PF'), \
        #                     in_out=kargs.get('TSCV.ADCInOut'))

        self.adc.update_adc(on_off=kargs.get('TSCV.ADCONOFF_PF'), \
                            mode=kargs.get('TSCV.ADCMODE_PF'))


    def update_nsopt(self, **kargs):

        self.imgrot.update_imgrot(imgrot=kargs.get('TSCV.ImgRotRotation'), \
                                  mode=kargs.get('TSCV.ImgRotMode'), \
                                  focus=kargs.get('TSCV.FOCUSINFO'), \
                                  itype=kargs.get('TSCV.ImgRotType'))
        
        self.adc.update_adc(on_off=kargs.get('TSCV.ADCOnOff'), \
                            mode=kargs.get('TSCV.ADCMode'), \
                            in_out=kargs.get('TSCV.ADCInOut'))

    def update_focus(self, **kargs):
        
        focus = {'HDS': self.update_nsopt, 'SPCAM': self.update_popt, \
                 'HICIAO': self.update_nsir, 'IRCS': self.update_nsir, \
                 'FMOS': self.update_pir, 'HSC': self.update_popt, \
                 'K3D': self.update_nsir, 'MOIRCS': self.update_cs, \
                 'FOCAS': self.update_csopt, 'COMICS': self.update_csir, \
                 'SUKA': self.update_cs}

        try:
            focus[self.obcp](**kargs) 
        except Exception as e:
            self.logger.error('error: updating focus.  %s' %str(e)) 

    def update_telescope(self, **kargs):

        self.logger.debug('updating telescope. %s' %str(kargs)) 

        self.dome_shutter.update_dome(dome=kargs.get('TSCV.DomeShutter')) 
        self.topscreen.update_topscreen(mode=kargs.get('TSCV.TopScreen'), \
                                        front=kargs.get('TSCL.TSFPOS'), \
                                        rear=kargs.get('TSCL.TSRPOS'))

        self.windscreen.update_windscreen(drv=kargs.get('TSCV.WINDSDRV'), \
                                          windscreen=kargs.get('TSCV.WindScreen'), \
                                          cmd=kargs.get('TSCL.WINDSCMD'), \
                                          pos=kargs.get('TSCL.WINDSPOS'), \
                                          el=kargs.get('TSCS.EL'))

        self.z.update_z(z=kargs.get('TSCL.Z'))

        self.m2.update_m2(focus=kargs.get('TSCV.FOCUSINFO'), \
                          focus2=kargs.get('TSCV.FOCUSINFO2'),)

        self.focus.update_focus(focus=kargs.get('TSCV.FOCUSINFO'), \
                                focus2=kargs.get('TSCV.FOCUSINFO2'), \
                                alarm=kargs.get('TSCV.FOCUSALARM'))

        #self.el.update_el(el=kargs.get('TSCS.EL'), \
        #                  state=kargs.get('STATL.TELDRIVE'))

        # self.azel.update_azel(az=kargs.get('TSCS.AZ'),\
        #                       el=kargs.get('TSCS.EL'), \
        #                       wind=kargs.get('TSCL.WINDD'), \
        #                       state=kargs.get('STATL.TELDRIVE'))

        self.azel.update_azel(az=kargs.get('TSCS.AZ'),\
                              el=kargs.get('TSCS.EL'), \
                              winddir=kargs.get('TSCL.WINDD'), \
                              windspeed=kargs.get('TSCL.WINDS_O'), \
                              state=kargs.get('STATL.TELDRIVE'))


        self.m1.update_m1cover(m1cover=kargs.get('TSCV.M1Cover'), \
                               m1cover_onway=kargs.get('TSCV.M1CoverOnway'))

        self.cell.update_cell(cell=kargs.get('TSCV.CellCover'))

        self.update_focus(**kargs)

    def tick(self):

        import random
        self.dome_shutter.tick()
        self.topscreen.tick()
        self.z.tick()
        self.focus.tick()
        #self.el.tick()

        el = random.random()*random.randrange(0,100)
        #el=27.1
        self.azel.tick(el=el)
        self.windscreen.tick(el=el)
        
        #self.azel.tick()
        #self.windscreen.tick()
  
        self.m2.tick()
        self.m1.tick()
        self.cell.tick()

        if self.obcp in ('MOIRCS', 'FOCAS', 'SPCAM', 'HSC', 'COMICS', 'FMOS', 'SUKA'):
            self.insrot.tick()
        if self.obcp in ('HDS', 'HICIAO', 'IRCS', 'K3D'):
            self.imgrot.tick()
        if self.obcp in ('HICIAO', 'IRCS', 'K3D'):
            self.waveplate.tick()
        if self.obcp in ('HDS', 'FOCAS', 'SPCAM', 'HSC'): 
            self.adc.tick()
        if self.obcp == 'COMICS':
            self.tipchop.tick()

def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('telescope', options)


    try:
        
        qApp = QtGui.QApplication(sys.argv)
        tel = Telescope(obcp=options.ins, logger=logger)  
        timer = QtCore.QTimer()
        QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"), tel.tick)
        timer.start(options.interval)
        tel.setWindowTitle("%s" % progname)
        tel.show()
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

    optprs.add_option("--ins", dest="ins",
                      default='HDS',
                      help="Specify an instrument name. e.g., HDS")


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


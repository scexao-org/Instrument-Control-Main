#!/usr/bin/env python

import os
import sys
import time
import subprocess, shlex
import ssdlog
from PyQt4.QtCore import *
from PyQt4.QtGui import *


class GuiderForm(QDialog):

    def __init__(self, parent=None):
        super(GuiderForm, self).__init__(parent)   

    def setup_ui(self):
        #GuiderSim.setObjectName()

        # guider type
        gbox_type=QGroupBox('Type')

        vbox_type=QVBoxLayout()
        hbox_type=QHBoxLayout()    
        self.ag_cb = QCheckBox("&AG")
        self.sv_cb = QCheckBox("S&V")
        self.sh_cb = QCheckBox("S&H")
        self.fmos_cb = QCheckBox("&FMOS")

        hbox_type2=QHBoxLayout()   

        self.hscscag_cb = QCheckBox("&HSCSCAG")
        self.hscshag_cb = QCheckBox("&HSCSHAG")
        self.hscsh_cb = QCheckBox("&HSCSH")

        self.ag_cb.setChecked(True)

        hbox_type.addWidget(self.ag_cb)
        hbox_type.addWidget(self.sv_cb)
        hbox_type.addWidget(self.sh_cb) 
        hbox_type.addWidget(self.fmos_cb) 

        hbox_type2.addWidget(self.hscscag_cb)
        hbox_type2.addWidget(self.hscshag_cb) 
        hbox_type2.addWidget(self.hscsh_cb) 

        vbox_type.addLayout(hbox_type)
        vbox_type.addLayout(hbox_type2)

        gbox_type.setLayout(vbox_type)  

       # guider kind
        gbox_kind=QGroupBox("Kind")
        #gbox_kind.setFlat(True)
        #gbox_kind.setStyleSheet("QGroupBox { background-color: rgb(255, 255,\
        #255); border:1px solid rgb(255, 170, 255); }")
        hbox_kind=QHBoxLayout()    
        self.obj_rb = QRadioButton("&Obj")
        self.dark_rb = QRadioButton("&Dark")
        self.flat_rb = QRadioButton("F&lat")
        self.sky_rb = QRadioButton("S&ky")
        self.obj_rb.setChecked(True)
        hbox_kind.addWidget(self.obj_rb)
        hbox_kind.addWidget(self.dark_rb)
        hbox_kind.addWidget(self.flat_rb) 
        hbox_kind.addWidget(self.sky_rb) 
        gbox_kind.setLayout(hbox_kind)  


        # guider binning
        gbox_binning=QGroupBox('Binning')
        hbox_binning=QHBoxLayout()   
        self.one_rb=QRadioButton("&1x1")
        self.two_rb = QRadioButton("&2x2")
        self.four_rb = QRadioButton("&4x4")
        self.eight_rb = QRadioButton("&8x8")
        self.one_rb.setChecked(True)
        hbox_binning.addWidget(self.one_rb)
        hbox_binning.addWidget(self.two_rb)
        hbox_binning.addWidget(self.four_rb) 
        hbox_binning.addWidget(self.eight_rb) 
        gbox_binning.setLayout(hbox_binning)  

        # guider target-host
        gbox_host=QGroupBox('Target Host')
        hbox_host=QHBoxLayout()    
        self.localhost_rb = QRadioButton('localhost')
        self.g2s4_rb = QRadioButton("&g2s4")
        self.g2b3_rb = QRadioButton("g2&b3")
        self.g2s1_rb = QRadioButton("g2s1")
        self.g2s3_rb = QRadioButton("g2s&3")
        #g2b1_rb = QRadioButton("g2b1")
        self.localhost_rb.setChecked(True)
        #self.g2s4_rb.setChecked(True)
        hbox_host.addWidget(self.localhost_rb)
        hbox_host.addWidget(self.g2s4_rb)
        hbox_host.addWidget(self.g2b3_rb)
        hbox_host.addWidget(self.g2s1_rb) 
        hbox_host.addWidget(self.g2s3_rb) 
        #hbox_host.addWidget(g2b1_rb) 
        gbox_host.setLayout(hbox_host)  

        # guider interval
        hbox_interval=QHBoxLayout()    

        interval_lb = QLabel("Interval(sec): ")
        self.interval_sb = QSpinBox()
        self.interval_sb.setRange(1,60)
        interval_lb.setBuddy(self.interval_sb)
       
        hbox_interval.addWidget(interval_lb)
        hbox_interval.addWidget(self.interval_sb)
        

        # number of frames 
        hbox_num=QHBoxLayout()    
        num_lb = QLabel("Num of Frames: ")
        self.num_sb = QSpinBox()
        self.num_sb.setRange(0,10000000)
        num_lb.setBuddy(self.num_sb)
        self.num_sb.setValue(1)  # default is 1        

        hbox_num.addWidget(num_lb)
        hbox_num.addWidget(self.num_sb)

        # line separator 
        line = QFrame()
        line.setFrameStyle(QFrame.HLine|QFrame.Sunken)

   
        # start button
        start_bt = QPushButton('Start') 

        # stop button
        stop_bt = QPushButton('Stop') 

        # space
        spacer = QSpacerItem(15,10,QSizePolicy.Minimum, QSizePolicy.Expanding) 

        # close button
        close_bt = QPushButton('&Quit') 

        # top layout
        topLayout = QVBoxLayout()
        topLayout.addWidget(gbox_type)
        topLayout.addWidget(gbox_kind)
        topLayout.addWidget(gbox_binning)
        topLayout.addWidget(gbox_host)
        topLayout.addLayout(hbox_interval)
        topLayout.addLayout(hbox_num)
 
        # button layout
        buttonLayout = QHBoxLayout()
        #buttonLayout.setSpacing(20)
        buttonLayout.addWidget(start_bt)
        buttonLayout.addWidget(stop_bt)
        buttonLayout.addItem(spacer)
        buttonLayout.addWidget(close_bt)
        #buttonLayout.addStretch()

        # main layout
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(topLayout)
        mainLayout.setMargin(10)
        mainLayout.addWidget(line)
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)


        self.connect(start_bt, SIGNAL("clicked()"), self.start )
        self.connect(stop_bt, SIGNAL("clicked()"), self.stop )
        self.connect(close_bt, SIGNAL("clicked()"), self.close_guidersim )

        self.timer = QTimer()
        self.connect(self.timer, SIGNAL("timeout()"), self.start_guidersim)

        self.setWindowTitle("Guider Simulator")

class GuiderSim(GuiderForm):

    def __init__(self,logger, parent=None):
        super(GuiderSim, self).__init__()

        self.logger=logger
        self.setup_ui()
        self.count=0
        self.setWindowTitle("Guider Simulator")

    @property
    def types(self):
       
        cmd=[]     
        type_dict={'ag':'AgSim_ag','sv':'AgSim_sv', 'sh':'AgSim_sh', 'fmos':'AgSim_fmos', 'hscscag':'AgSim_hscscag', 'hscshag':'AgSim_hscshag', 'hscsh':'AgSim_hscsh' }
  
        if self.ag_cb.isChecked():
            cmd.append(type_dict['ag'])
        if self.sv_cb.isChecked():
            cmd.append(type_dict['sv'])
        if self.sh_cb.isChecked():
            cmd.append(type_dict['sh'])
        if self.fmos_cb.isChecked():
            cmd.append(type_dict['fmos'])
        if self.hscscag_cb.isChecked():
            cmd.append(type_dict['hscscag'])
        if self.hscshag_cb.isChecked():
            cmd.append(type_dict['hscshag'])
        if self.hscsh_cb.isChecked():
            cmd.append(type_dict['hscsh'])

        return cmd

    @property
    def kind(self):
        
        kind={'obj':'1','dark':'2','flat':'3','sky':'4'}
        if self.obj_rb.isChecked():
            return kind['obj']
        elif self.dark_rb.isChecked():
            return kind['dark']    
        elif self.flat_rb.isChecked():
            return kind['flat']
        elif self.sky_rb.isChecked():
            return kind['sky']
   
    @property
    def binning(self):
        
        binning={'1x1':'1', '2x2':'2', '4x4':'4', '8x8':'8'}
        if self.one_rb.isChecked():
            return binning['1x1']
        elif self.two_rb.isChecked():
            return binning['2x2']   
        elif self.four_rb.isChecked():
            return binning['4x4']
        elif self.eight_rb.isChecked():
            return binning['8x8']

    @property
    def host(self):
        
        host={'localhost':'localhost','g2s4':'g2s4','g2b3':'g2b3','g2s1':'g2s1','g2s3':'g2s3'}

        if self.localhost_rb.isChecked():
            return host['localhost']
        elif self.g2s4_rb.isChecked():
            return host['g2s4']
        elif self.g2b3_rb.isChecked():
            return host['g2b3']    
        elif self.g2s1_rb.isChecked():
            return host['g2s1']
        elif self.g2s3_rb.isChecked():
            return host['g2s3']

    def start(self):
        self.logger.debug('sending an image...')
        #self.event.set()

        interval=self.interval_sb.value()
        self.count=self.num_sb.value()

        try:
            interval*=1000
        except Exception as e:
            interval=1000  # set interval to 1 sec if something is wrong

        self.timer.start(interval)

    def start_guidersim(self):

        if not self.count:
            self.stop()          
            return 

        fits_dict={'AgSim_ag':'AG.fits', 'AgSim_sv':'SV.fits', 
                   'AgSim_sh':'SH.fits', 'AgSim_fmos':'FMOS.fits', 
                   'AgSim_hscscag':'HSCSCAG.fits', 'AgSim_hscshag':'HSCSHAG.fits', 
                   'AgSim_hscsh':'HSCSH.fits'}

        for cmd in self.types:
            try:
                fits_path=os.path.join(os.environ['DATAHOME'], 'agsim', fits_dict[cmd])
                cmd=os.path.join(os.environ['ARCHHOME'], 'bin', cmd)
                cmd="%s %s %s  %s 1 1 %s" %(cmd, self.kind, self.binning, self.host, fits_path)
                self.logger.debug('cmd=%s' %cmd) 
                args=shlex.split(cmd)
                subprocess.Popen(args)
            except Exception as e:
                self.logger.error("error: executing sim. %s" %e)
         
        self.count-=1 
        self.num_sb.setValue(self.count)      

    def stop(self):
        self.logger.debug('stop sending ...')
        self.timer.stop()

    def close_guidersim(self):
        self.logger.debug('closing guider sim....')
        self.stop()
        self.close()     


def main(options,args):

    logname = 'agsim'
    logger = ssdlog.make_logger(logname, options)

    logger.info('guider sim starting ...')


    app = QApplication(sys.argv)
    gsim = GuiderSim(logger)
    gsim.show()
    app.exec_()


if __name__ == "__main__":
 

    from optparse import OptionParser

    usage = "usage: %prog [options] [file] ..."
    optprs = OptionParser(usage=usage, version=('%prog'))

    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")

    optprs.add_option("--display", dest="display", metavar="HOST:N",
                      help="Use X display on HOST:N")

    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")

    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])


    if options.display:
        os.environ['DISPLAY'] = options.display

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



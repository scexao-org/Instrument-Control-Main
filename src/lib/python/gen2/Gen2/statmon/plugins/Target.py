#!/usr/bin/env python

# This is only needed for Python v2 but is harmless for Python v3.
#import sip
#sip.setapi('QVariant', 2)
import os
import sys

from PyQt4 import QtCore, QtGui

import ssdlog
from Propid import PropIdDisplay
from Object import ObjectDisplay
from Airmass import AirmassDisplay
from Pa import PaDisplay
from TimeAz import TimeAzLimitDisplay
from TimeEl import TimeElLimitDisplay
from TimeRot import TimeRotLimitDisplay

progname = os.path.basename(sys.argv[0])

class TargetGui(QtGui.QWidget):
    def __init__(self, parent=None, obcp=None, logger=None):
        super(TargetGui, self).__init__(parent) 
        
        self.obcp = obcp  # instrument 3 letter code
        self.logger = logger
        self.propid = PropIdDisplay(logger=logger)
        self.object = ObjectDisplay(logger=logger)
        #self.airmass = AirmassDisplay(logger=logger)
        self.pa = PaDisplay(logger=logger) 
        self.time_az = TimeAzLimitDisplay(logger=logger)  
        self.time_el = TimeElLimitDisplay(logger=logger)
        self.time_rot = TimeRotLimitDisplay(logger=logger)   
        self.set_layout()

    def set_layout(self):
   
        mainlayout = QtGui.QVBoxLayout()        
        mainlayout.setSpacing(1) 
        mainlayout.setMargin(0)

        mainlayout.addWidget(self.propid)        
        mainlayout.addWidget(self.object)        
        #mainlayout.addWidget(self.airmass)        
        mainlayout.addWidget(self.pa)        
        mainlayout.addWidget(self.time_az)        
        mainlayout.addWidget(self.time_el)        
        mainlayout.addWidget(self.time_rot)        
        self.setLayout(mainlayout)


class Target(TargetGui):
    def __init__(self, parent=None, obcp=None, logger=None):
        super(Target, self).__init__(parent=parent, obcp=obcp, logger=logger) 

    def get_pa_status(self):

        try:
            pa, cmd_diff = {'SUP': ('TSCL.INSROTPA_PF', 'STATS.ROTDIF_PF'), \
                'FMS': ('TSCL.INSROTPA_PF', 'STATS.ROTDIF_PF'), \
                'HSC': ('TSCL.INSROTPA_PF', 'STATS.ROTDIF_PF'), \
                'HDS': ('TSCL.ImgRotPA', 'STATS.ROTDIF'), \
                'HIC': ('TSCL.ImgRotPA', 'STATS.ROTDIF'), \
                'IRC': ('TSCL.ImgRotPA', 'STATS.ROTDIF'), \
                'K3D': ('TSCL.ImgRotPA', 'STATS.ROTDIF'), \
                'MCS': ('TSCL.InsRotPA', 'STATS.ROTDIF'), \
                'FCS': ('TSCL.InsRotPA', 'STATS.ROTDIF'), \
                'SUK': ('TSCL.InsRotPA', 'STATS.ROTDIF'), \
                'COM': ('TSCL.InsRotPA', 'STATS.ROTDIF')}[self.obcp]
        except Exception:
            pa = cmd_diff = None 
        finally:   
            return (pa, cmd_diff)    
 
    def update_target(self, **kargs):

        self.logger.debug('updating telescope. %s' %str(kargs)) 

        try:
            propid = 'FITS.{0}.PROP_ID'.format(self.obcp)
            self.propid.update_propid(propid=kargs.get(propid)) 

            obj = 'FITS.{0}.OBJECT'.format(self.obcp) 
            self.object.update_object(obj=kargs.get(obj))

            #self.airmass.update_airmass(el=kargs.get('TSCS.EL'))

            # pa = TSCL.INSROTPA_PF | TSCL.InsRotPA | TSCL.ImgRotPA
            # cmd_diff = STATS.ROTDIF_PF | STATS.ROTDIF
            pa, cmd_diff = self.get_pa_status()
            self.pa.update_pa(pa=kargs.get(pa), \
                              cmd_diff=kargs.get(cmd_diff))

            self.time_az.update_azlimit(flag=kargs.get('TSCL.LIMIT_FLAG'), \
                                        az=kargs.get('TSCL.LIMIT_AZ'),)

            self.time_el.update_ellimit(flag=kargs.get('TSCL.LIMIT_FLAG'), \
                                        low=kargs.get('TSCL.LIMIT_EL_LOW'), \
                                        high=kargs.get('TSCL.LIMIT_EL_HIGH'))

            self.time_rot.update_rotlimit(flag=kargs.get('TSCL.LIMIT_FLAG'), \
                                          rot=kargs.get('TSCL.LIMIT_ROT'), \
                                          link=kargs.get('TSCV.PROBE_LINK'), \
                                          focus=kargs.get('TSCV.FOCUSINFO'), \
                                          focus2=kargs.get('TSCV.FOCUSINFO2'))
        except Exception as e:
            self.logger.error('error: target update. %s' %str(e))  

    def tick(self):

        self.propid.tick()
        self.object.tick()
        #self.airmass.tick()
        self.pa.tick()
        self.time_az.tick()
        self.time_el.tick()
        self.time_rot.tick()

def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('telescope', options)


    try:
        qApp = QtGui.QApplication(sys.argv)
        tel = Target(obcp=options.ins, logger=logger)  
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
                      help="Specify 3 character code of an instrument. e.g., HDS")


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


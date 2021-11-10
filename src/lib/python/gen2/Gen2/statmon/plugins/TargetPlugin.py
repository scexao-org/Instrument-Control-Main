import sip
from PyQt4 import QtGui, QtCore

import PlBase
import Target
import  cfg.INS as INS


class TargetPlugin(PlBase.Plugin):
    """ Target """

    def __set_aliases(self, ins_code):

        self.aliases = ['FITS.{0}.PROP_ID'.format(ins_code), \
                        'FITS.{0}.OBJECT'.format(ins_code), \
                        'TSCL.INSROTPA_PF', 'STATS.ROTDIF_PF', \
                        'TSCL.ImgRotPA', 'STATS.ROTDIF', \
                        'TSCL.InsRotPA', 'TSCL.LIMIT_FLAG', \
                        'TSCL.LIMIT_AZ', 'TSCL.LIMIT_EL_LOW', \
                        'TSCL.LIMIT_EL_HIGH', 'TSCL.LIMIT_ROT', \
                        'TSCV.PROBE_LINK', 'TSCV.FOCUSINFO', \
                        'TSCV.FOCUSINFO2', 'TSCS.EL']
        self.logger.debug('setting aliases=%s' %self.aliases)

    def set_layout(self, obcp):

        ins = INS.INSdata()

        ins_code = ins.getCodeByName(obcp)
        self.__set_aliases(ins_code)

        qtwidget = QtGui.QWidget()
        self.target = Target.Target(qtwidget, obcp=ins_code, \
                                  logger=self.logger)
       
        self.vlayout = QtGui.QVBoxLayout()
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.vlayout.setSpacing(0)
        self.vlayout.addWidget(self.target,stretch=1)
        self.root.setLayout(self.vlayout)

    def change_config(self, controller, d):

        obcp = d['inst']
        if obcp.startswith('#'):
            self.logger.debug('obcp is not assigned. %s' %obcp)
            return 


        self.logger.debug('target changing config dict=%s ins=%s' %(d, d['inst']))  
        try:
            sip.delete(self.target)
            sip.delete(self.vlayout)
             
        except Exception as e:
            self.logger.error('error: configuring layout. %s' %e)  
        else:
            self.set_layout(obcp=obcp) 
            controller.register_select('target', self.update, \
                                         self.aliases)

    def build_gui(self, container):
        self.root = container

        try:
            obcp = self.controller.proxystatus.fetchOne('FITS.SBR.MAINOBCP')
            self.set_layout(obcp=obcp)
        except Exception as e:
            self.logger.error('error: building layout. %s' %e)

    def start(self):
        self.controller.register_select('target', self.update, \
                                         self.aliases)
        self.controller.add_callback('change-config', self.change_config)

    def update(self, statusDict):
        self.logger.debug('status=%s' %str(statusDict))
        self.target.update_target(**statusDict) 

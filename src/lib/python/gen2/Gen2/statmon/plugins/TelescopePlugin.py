from PyQt4 import QtGui, QtCore
import sip

import PlBase
import Telescope


class TelescopePlugin(PlBase.Plugin):
    """ Telescope Plugin"""

    aliases=['TSCV.DomeShutter', 'TSCV.TopScreen', 'TSCL.TSFPOS', \
             'TSCL.TSRPOS', 'TSCV.WINDSDRV', 'TSCV.WindScreen', \
             'TSCL.WINDSPOS', 'TSCL.WINDSCMD', 'TSCL.WINDD', 'TSCL.Z', \
             'TSCV.FOCUSINFO', 'TSCV.FOCUSINFO2', 'TSCV.FOCUSALARM', \
             'TSCS.AZ', 'STATL.TELDRIVE', 'TSCS.EL', \
             'TSCV.M1Cover', 'TSCV.M1CoverOnway', 'TSCV.CellCover', \
             'TSCV.ADCONOFF_PF', 'TSCV.ADCMODE_PF', \
             'TSCV.ADCOnOff', 'TSCV.ADCMode', 'TSCV.ADCInOut', \
             'TSCV.ImgRotRotation', 'TSCV.ImgRotMode', 'TSCV.ImgRotType', \
             'TSCV.INSROTROTATION_PF', 'TSCV.INSROTMODE_PF', \
             'TSCV.InsRotRotation', 'TSCV.InsRotMode', \
             'WAV.STG1_PS', 'WAV.STG2_PS', 'WAV.STG3_PS', \
             'TSCV.TT_Mode', 'TSCV.TT_Drive', 'TSCV.TT_DataAvail', \
             'TSCV.TT_ChopStat', 'TSCL.WINDS_O']

    def set_layout(self, obcp):

        self.logger.debug('telescope setlayout ins=%s' %(obcp))
        qtwidget = QtGui.QWidget()

        self.telescope = Telescope.Telescope(qtwidget, obcp=obcp, \
                                           logger=self.logger)

        self.vlayout = QtGui.QVBoxLayout()
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.vlayout.setSpacing(0)
        self.vlayout.addWidget(self.telescope, stretch=1)
        self.root.setLayout(self.vlayout)

    def change_config(self, controller, d):

        self.logger.debug('telescope change config dict=%s ins=%s' %(d, d['inst']))  
        obcp = d['inst']
        if obcp.startswith('#'):
            self.logger.debug('obcp is not assigned. %s' %obcp)
            return 
       
        try:
            sip.delete(self.telescope)
            sip.delete(self.vlayout)
            self.set_layout(obcp=obcp) 
        except Exception as e:
            self.logger.error('error: configuring layout. %s' %e)  

    def build_gui(self, container):

        self.root = container

        try:
            obcp = self.controller.proxystatus.fetchOne('FITS.SBR.MAINOBCP')
            self.set_layout(obcp)
        except Exception as e:
            self.logger.error('error: building layout. %s' %e)

    def start(self):
        self.controller.register_select('telescope', self.update, \
                                         TelescopePlugin.aliases)
        self.controller.add_callback('change-config', self.change_config)

    def update(self, statusDict):
        self.logger.debug('status=%s' %str(statusDict))
        self.telescope.update_telescope(**statusDict) 

import PlBase
import Cal
from PyQt4 import QtGui, QtCore

class CalPlugin(PlBase.Plugin):
    """ Cal Source Plugin """

    aliases=['TSCV.CAL_HCT_LAMP1', 'TSCV.CAL_HCT_LAMP2', \
             'TSCV.CAL_HAL_LAMP1', 'TSCV.CAL_HAL_LAMP2', \
             'TSCV.CAL_RGL_LAMP1', 'TSCV.CAL_RGL_LAMP2', \
             'TSCL.CAL_HCT1_AMP', 'TSCL.CAL_HCT2_AMP', \
             'TSCL.CAL_HAL1_AMP', 'TSCL.CAL_HAL2_AMP' ]

    def build_gui(self, container):
        self.root = container

        qtwidget = QtGui.QWidget()

        self.cal=Cal.CalDisplay(qtwidget, logger=self.logger)
       
        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.cal, stretch=1)
        container.setLayout(layout)
 
    def start(self):
        self.controller.register_select('cal', self.update, \
                                         CalPlugin.aliases)

    def update(self, statusDict):
        self.logger.debug('status=%s' %str(statusDict))
        try:
            hct1 = statusDict.get(CalPlugin.aliases[0])
            hct2 = statusDict.get(CalPlugin.aliases[1])
            hal1 = statusDict.get(CalPlugin.aliases[2])
            hal2 = statusDict.get(CalPlugin.aliases[3])
            rgl1 = statusDict.get(CalPlugin.aliases[4])
            rgl2 = statusDict.get(CalPlugin.aliases[5])
            hct1_amp = statusDict.get(CalPlugin.aliases[6])
            hct2_amp = statusDict.get(CalPlugin.aliases[7])
            hal1_amp = statusDict.get(CalPlugin.aliases[8])
            hal2_amp = statusDict.get(CalPlugin.aliases[9])

            self.cal.update_cal(hct1=hct1, hct2=hct2, \
                                hal1=hal1, hal2=hal2, \
                                rgl1=rgl1, rgl2=rgl2, \
                                hct1_amp=hct1_amp, hct2_amp=hct2_amp, \
                                hal1_amp=hal1_amp, hal2_amp=hal2_amp)
        except Exception as e:
            self.logger.error('error: updating status. %s' %str(e))
            


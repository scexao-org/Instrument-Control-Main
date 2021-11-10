#
# Takeshi Inagaki
# Eric Jeschke (eric@naoj.org)
#
from PyQt4 import QtGui, QtCore
import sip

import PlBase
import Plot


class PlotPlugin(PlBase.Plugin):

    def __set_aliases(self, obcp):

        if obcp in self.ag:
            self.update = self.update_ag
            self.aliases = ['STATL.TELDRIVE', 'TSCL.AG1dX', 'TSCL.AG1dY', 
                            'TSCV.AGExpTime', 'TSCV.AG1_I_BOTTOM', 'TSCV.AG1_I_CEIL']
        elif obcp in self.ao:
            self.update = self.update_ao
            self.aliases = ['AON.TT.TTX','AON.TT.TTY', 'AON.TT.WTTC1','AON.TT.WTTC2']   
        elif obcp ==  self.agsv:
            self.update = self.update_twoguiding
            self.aliases = ['STATL.TELDRIVE', \
                            'TSCL.AG1dX', 'TSCL.AG1dY', \
                            'TSCL.SV1DX', 'TSCL.SV1DY', \
                            'TSCV.AGExpTime', 'TSCV.SVExpTime',\
                            'TSCV.AG1_I_BOTTOM', 'TSCV.AG1_I_CEIL', \
                            'TSCV.SV1_I_BOTTOM', 'TSCV.SV1_I_CEIL']

        elif obcp == self.fmosag:
            self.update = self.update_fmosag
            self.aliases = ['STATL.TELDRIVE', 'TSCL.AGFMOSdAZ', 'TSCL.AGFMOSdEL', 'TSCS.EL']
        elif obcp == self.hscag:
            self.update = self.update_twoguiding
            self.aliases = ['STATL.TELDRIVE', \
                            'TSCL.HSC.SCAG.DX', 'TSCL.HSC.SCAG.DY', \
                            'TSCL.HSC.SHAG.DX', 'TSCL.HSC.SHAG.DY', \
                            'TSCV.HSC.SCAG.ExpTime', 'TSCV.HSC.SHAG.ExpTime', \
                            'TSCV.HSC.SCAG.I_BOTTOM', 'TSCV.HSC.SCAG.I_CEIL', \
                            'TSCV.HSC.SHAG.I_BOTTOM', 'TSCV.HSC.SHAG.I_CEIL']
 
    def update_ao(self, statusDict):
        self.logger.debug('status=%s' %str(statusDict))
        ao1x = statusDict.get(self.aliases[0])
        ao1y = statusDict.get(self.aliases[1])
        ao2x = statusDict.get(self.aliases[2])
        ao2y = statusDict.get(self.aliases[3])
        self.plot.update_plot(ao1x, ao1y, ao2x, ao2y)


    def update_fmosag(self, statusDict):
        self.logger.debug('status=%s' %str(statusDict))
        state = statusDict.get(self.aliases[0])
        x = statusDict.get(self.aliases[1])
        y = statusDict.get(self.aliases[2])
        el = statusDict.get(self.aliases[3])
        self.plot.update_plot(state, x, y, el)
            
    def update_ag(self, statusDict):
        self.logger.debug('status=%s' %str(statusDict))
        state = statusDict.get(self.aliases[0])
        x = statusDict.get(self.aliases[1])
        y = statusDict.get(self.aliases[2])
        exp = statusDict.get(self.aliases[3])
        bottom = statusDict.get(self.aliases[4])
        ceil = statusDict.get(self.aliases[5]) 
        self.plot.update_plot(state=state, x=x, y=y, \
                            exptime=exp, bottom=bottom, ceil=ceil)


    def update_twoguiding(self, statusDict):
        self.logger.debug('status=%s' %str(statusDict))
        state = statusDict.get(self.aliases[0])
        guiding1_x = statusDict.get(self.aliases[1])
        guiding1_y = statusDict.get(self.aliases[2])
        guiding2_x = statusDict.get(self.aliases[3])
        guiding2_y = statusDict.get(self.aliases[4])
        guiding1_exp = statusDict.get(self.aliases[5])
        guiding2_exp = statusDict.get(self.aliases[6])
        guiding1_bottom = statusDict.get(self.aliases[7])
        guiding1_ceil = statusDict.get(self.aliases[8])
        guiding2_bottom = statusDict.get(self.aliases[9])
        guiding2_ceil = statusDict.get(self.aliases[10])

        self.plot.update_plot(state, guiding1_x, guiding1_y, guiding2_x, guiding2_y, \
                               guiding1_exp, guiding2_exp, \
                               guiding1_bottom, guiding1_ceil, \
                               guiding2_bottom, guiding2_ceil)



    def change_config(self, controller, d):

        obcp = d['inst']
        if obcp.startswith('#'):
            self.logger.debug('obcp is not assigned. %s' %obcp)
            return 


        self.logger.debug('plot changing config dict=%s ins=%s' %(d, d['inst']))  
        try:
            sip.delete(self.plot)
            sip.delete(self.vlayout)
        except Exception as e:
            self.logger.error('error: plot configuring layout. %s' %e)  
        else:
            self.set_layout(obcp=obcp) 
            controller.register_select('plot', self.update, self.aliases)


    def set_layout(self, obcp):

        self.logger.debug('plot setlayout. obcp=%s' %obcp) 
        self.__set_aliases(obcp)
        self.logger.debug('plot update=%s  aliases=%s' %(self.update, self.aliases)) 
    
        qtwidget = QtGui.QWidget()

        if obcp in self.ag:
            self.plot = Plot.AgPlot(qtwidget, logger=self.logger)
        elif obcp in self.ao:
            self.plot = Plot.NsIrPlot(qtwidget, logger=self.logger)
        elif obcp == self.agsv or obcp == self.hscag:
            self.plot = Plot.TwoGuidingPlot(qtwidget, logger=self.logger)    
        elif obcp == self.fmosag:
            self.plot = Plot.FmosPlot(qtwidget, logger=self.logger)

        self.vlayout = QtGui.QVBoxLayout()
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.vlayout.setSpacing(0)
        self.vlayout.addWidget(self.plot, stretch=1)
        self.root.setLayout(self.vlayout)

    def build_gui(self, container):
        self.root = container
        self.hscag = 'HSC'  
        self.fmosag = 'FMOS'
        self.ag = ('MOIRCS', 'FOCAS', 'COMICS', 'SPCAM', 'SUKA')
        self.ao = ('IRCS', 'HICIAO', 'K3D', )
        self.agsv = 'HDS'

        try:
            obcp = self.controller.proxystatus.fetchOne('FITS.SBR.MAINOBCP')
            self.set_layout(obcp=obcp)
        except Exception as e:
            self.logger.error('error: building layout. %s' %e)

    def start(self):
        self.logger.debug('starting plot-updating...') 
        self.controller.register_select('plot', self.update, self.aliases)
        self.controller.add_callback('change-config', self.change_config)

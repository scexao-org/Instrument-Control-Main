from PyQt4 import QtGui, QtCore
import sip

import PlBase
import State


class StatePlugin(PlBase.Plugin):

    def __set_aliases(self, obcp):
 
        other = ('SPCAM', 'IRCS', 'HICIAO', 'K3D', 'MOIRCS', 'FOCAS', 'COMICS')
        ns_opt = ('HDS',)
        p_opt2 = ('HSC',)
        p_ir = ('FMOS',)

        if obcp in other:
            self.aliases = ['STATL.TELDRIVE', \
                            'TSCL.AG1Intensity', 'STATL.AGRERR']
        elif obcp in ns_opt:
            self.aliases = ['STATL.TELDRIVE', \
                            'TSCL.AG1Intensity', 'STATL.AGRERR', \
                            'TSCL.SV1Intensity', 'STATL.SVRERR', \
                            'STATL.SV_CALC_MODE']
        elif obcp in p_opt2:
            self.aliases = ['STATL.TELDRIVE', \
                            'TSCL.HSC.SCAG.Intensity', 'STATL.AGRERR', \
                            'TSCL.HSC.SHAG.Intensity', 'STATL.AGRERR']
        elif obcp in p_ir:
            self.aliases = ['STATL.TELDRIVE', \
                            'TSCL.AGFMOSIntensity', 'STATL.AGRERR']


    def change_config(self, controller, d):

        self.logger.info('changing config dict=%s ins=%s' %(d, d['inst']))  

        obcp = d['inst']
        if obcp.startswith('#'):
            self.logger.debug('obcp is not assigned. %s' %obcp)
            return 

        try:
            sip.delete(self.state)
            sip.delete(self.vlayout)
        except Exception as e:
            self.logger.error('error: deleting current layout. %s' %e)  
        else:
            self.set_layout(obcp=obcp)  
            controller.register_select('state', self.update, self.aliases)

    def set_layout(self, obcp):

        self.__set_aliases(obcp)

        qtwidget = QtGui.QWidget()
        self.state = State.State(parent=qtwidget, logger=self.logger)
       
        self.vlayout = QtGui.QVBoxLayout()
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.vlayout.setSpacing(0)
        self.vlayout.addWidget(self.state,stretch=1)
        self.root.setLayout(self.vlayout)

    def build_gui(self, container):
        self.root = container

        try:
            obcp = self.controller.proxystatus.fetchOne('FITS.SBR.MAINOBCP')
            self.set_layout(obcp)
        except Exception as e:
            self.logger.error('error: building layout. %s' %e)

    def start(self):
        self.controller.register_select('state', self.update, self.aliases)
        self.controller.add_callback('change-config', self.change_config)

    def update(self, statusDict):
        self.logger.debug('status=%s' %str(statusDict))

        state = statusDict.get(self.aliases[0])

        guiding1 = ["Guiding(AG1)", "Guiding(AG2)", "Guiding(AGFMOS)", \
                    "Guiding(AGPIR)", "Guiding(HSCSCAG)"]
        sv = ["Guiding(SV1)", "Guiding(SV2)"]
        guiding2 = sv + ["Guiding(HSCSHAG)"]

   
        if state in guiding1:
            intensity = statusDict.get(self.aliases[1])
            valerr = statusDict.get(self.aliases[2])
        elif state in guiding2:
            intensity = statusDict.get(self.aliases[3])
            valerr = statusDict.get(self.aliases[4])
        else:  # if not guiding, intensity and valerr don't matter. 
            intensity = valerr = None              
         
        if state in sv:
            calc_mode = statusDict.get(self.aliases[5])
        else:
            calc_mode = None

        self.state.update_state(state=state, intensity=intensity, valerr=valerr, calc_mode=calc_mode)

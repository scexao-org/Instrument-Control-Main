from PyQt4 import QtGui, QtCore
import sip

import PlBase
import GuidingImage

class GuidingImagePlugin(PlBase.Plugin):
    """ Guiding Image Brightness/Seeing  """

    def __set_aliases(self, obcp):

        if obcp in self.ag:
            self.aliases = ['TSCL.AG1Intensity', 'VGWD.FWHM.AG']
        elif obcp ==  self.agsv:
            self.aliases = ['TSCL.AG1Intensity', 'TSCL.SV1Intensity', \
                            'VGWD.FWHM.AG', 'VGWD.FWHM.SV']
        elif obcp == self.fmosag:
            self.aliases = ['TSCL.AGFMOSIntensity', 'TSCL.AGFMOSStarSize']
        elif obcp == self.hscag:
            self.aliases = ['TSCL.HSC.SCAG.Intensity', 'TSCL.HSC.SCAG.StarSize', \
                            'TSCL.HSC.SHAG.Intensity', 'TSCL.HSC.SHAG.StarSize']

    def set_layout(self, obcp):

        self.__set_aliases(obcp)
        self.logger.debug('guidingimage obcp=%s  aliases=%s' %(obcp, self.aliases)) 

        qtwidget = QtGui.QWidget()

        self.gi = GuidingImage.GuidingImage(qtwidget, obcp=obcp, logger=self.logger)
       
        self.vlayout = QtGui.QVBoxLayout()
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.vlayout.setSpacing(0)
        self.vlayout.addWidget(self.gi, stretch=1)
        self.root.setLayout(self.vlayout)

    def change_config(self, controller, d):

        obcp = d['inst']
        if obcp.startswith('#'):
            self.logger.debug('guidingimage obcp is not assigned. %s' %obcp)
            return 

        self.logger.debug('guidingimage changing config dict=%s ins=%s' %(d, d['inst']))  

        try:
            if not self.obcp in self.ao:
                sip.delete(self.gi)
                sip.delete(self.vlayout)
        except Exception as e:
            self.logger.error('error: configuring layout. %s' %e)  
        else:
            if not obcp in self.ao:
                self.set_layout(obcp=obcp) 
                controller.register_select('guidingimage', self.update, \
                                         self.aliases)
                self.gi.start()
        finally:
            self.obcp = obcp

    def build_gui(self, container):

        self.hscag = 'HSC'  
        self.fmosag = 'FMOS'
        self.ag = ('MOIRCS', 'FOCAS', 'COMICS', 'SPCAM', 'SUKA')
        self.agsv = 'HDS'
        self.ao = ('IRCS', 'HICIAO', 'K3D', )

        self.root = container

        try:
            self.obcp = self.controller.proxystatus.fetchOne('FITS.SBR.MAINOBCP')
            self.logger.debug('guidingimage building gui. obcp=%s' %self.obcp)
            if not self.obcp in self.ao: 
                self.set_layout(obcp=self.obcp)
        except Exception as e:
            self.logger.error('error: building layout. %s' %e)
 
    def start(self):
#        self.logger.debug('start aliases=%s' %AgPlotPlugin.aliases)
        if not self.obcp in self.ao:
            self.controller.register_select('guidingimage', self.update, self.aliases)
            self.gi.start()

        self.controller.add_callback('change-config', self.change_config)


    def update(self, statusDict):
        self.logger.debug('guidingimage status=%s' %str(statusDict))
        self.gi.update_guidingimage(status_dict=statusDict)


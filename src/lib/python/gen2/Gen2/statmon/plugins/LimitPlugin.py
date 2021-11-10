from PyQt4 import QtGui, QtCore
import sip

import PlBase
import Limit


class AzLimitPlugin(PlBase.Plugin):
    """ Az Limit """
    aliases = ['TSCS.AZ', 'TSCS.AZ_CMD']
  
    def build_gui(self, container):
        self.root = container

        qtwidget = QtGui.QWidget()
        title = 'AZ'
        alarm = [-269.5, 269.5]
        warn = [-260.0, 260.0 ]
        limit = [-270.0, 270.0]
        self.limit = Limit.Limit(parent=qtwidget, title=title, alarm=alarm, warn=warn, limit=limit, logger=self.logger)
        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.limit, stretch=1)
        container.setLayout(layout)
 
    def start(self):
        self.controller.register_select('azlimit', self.update, AzLimitPlugin.aliases)

    def update(self, statusDict):
        self.logger.debug('status=%s' %str(statusDict))
        cur = statusDict.get(AzLimitPlugin.aliases[0])
        cmd = statusDict.get(AzLimitPlugin.aliases[1])
        self.limit.update_limit(current=cur, cmd=cmd)


class ElLimitPlugin(PlBase.Plugin):
    """ El Limit """
    aliases=['TSCS.EL', 'TSCS.EL_CMD', 'STATL.TELDRIVE']
  
    def build_gui(self, container):
        self.root = container

        qtwidget = QtGui.QWidget()
        title = 'EL'
        marker = 15.0
        marker_txt = 15.0
        warn = [15.0, 89.0]
        alarm = [10.0,89.5] 
        limit = [10.0, 90.0]   

        self.limit = Limit.Limit(parent=qtwidget, title=title, alarm=alarm, warn=warn, limit=limit, marker=marker, marker_txt=marker_txt, logger=self.logger)
        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.limit,stretch=1)
        container.setLayout(layout)
 
    def start(self):
        self.controller.register_select('ellimit', self.update, ElLimitPlugin.aliases)

    def update(self, statusDict):
        self.logger.debug('status=%s' %str(statusDict))
        cur = statusDict.get(ElLimitPlugin.aliases[0])
        cmd = statusDict.get(ElLimitPlugin.aliases[1])
        state=statusDict.get(ElLimitPlugin.aliases[2])
        self.limit.update_limit(current=cur, cmd=cmd, state=state)



class RotLimitPlugin(PlBase.Plugin):
    """ Rotator Limit """

    def __set_aliases(self, obcp):
 
        # instrument on prime/cs/ns focus
        pf = ('SPCAM', 'HSC', 'FMOS')  
        cs = ('MOIRCS', 'FOCAS', 'COMICS')
        ns = ('IRCS', 'HDS', 'HICIAO', 'K3D')

        if obcp in pf:
            self.aliases = ['TSCS.INSROTPOS_PF', 'TSCS.INSROTCMD_PF']
        elif obcp in cs:
            self.aliases = ['TSCS.INSROTPOS', 'TSCS.INSROTCMD']          
        elif obcp in ns:
            self.aliases = ['TSCS.ImgRotPos', 'TSCS.IMGROTCMD']
        else:
            self.aliases = [None, None]

    def __set_limit(self, obcp):

        # instrument name: title, warn, alarm,  limit
        limit = {'SPCAM': ('Rotator Popt', (-240.0, 240.0), (-249.5, 249.5), (-250.0, 250.0)), 
                 'HSC': ('Rotator Popt2',  (-260.0, 260.0), (-269.5, 269.5), (-270.0, 270.0)),
                 'FMOS': ('Rotator Pir', (-175.0, 175.0), (-179.5, 179.5), (-180.0, 180.0)),
                 'HDS': ('Rotator Ns Opt', (-175.0, 175.0), (-179.5, 179.5), (-180.0, 180.0)), 
                 'IRCS': ('Rotator Ns Ir', (-175.0, 175.0), (-179.5, 179.5), (-180.0, 180.0)), 
                 'HICIAO': ('Rotator Ns Ir', (-175.0, 175.0), (-179.5, 179.5), (-180.0, 180.0)), 
                 'K3D': ('Rotator Ns Ir', (-175.0, 175.0), (-179.5, 179.5), (-180.0, 180.0)), 
                 'COMICS': ('Rotator Cs',  (-260.0, 260.0), (-269.5, 269.5), (-270.0, 270.0)),
                 'MOIRCS': ('Rotator Cs',  (-260.0, 260.0), (-269.5, 269.5), (-270.0, 270.0)),
                 'FOCAS': ('Rotator Cs',  (-260.0, 260.0), (-269.5, 269.5), (-270.0, 270.0)),
                 'SUKA': ('Rotator Cs',  (-260.0, 260.0), (-269.5, 269.5), (-270.0, 270.0)),}

        try:
            self.title, self.warn, self.alarm, self.limit = limit[obcp]
        except Exception as e:
            self.logger.error('error: seting limit. %s' %e)
            self.title, self.warn, self.alarm, self.limit = None

    def set_layout(self, obcp):
  
        self.__set_aliases(obcp)
        self.__set_limit(obcp)

        self.logger.debug('rotator-limit setlayout. obcp=%s aliases=%s  title=%s' %(obcp, self.aliases, self.title)) 

        qtwidget = QtGui.QWidget()

        self.limit_rot = Limit.Limit(parent=qtwidget, title=self.title, alarm=self.alarm, \
                                 warn=self.warn, limit=self.limit, logger=self.logger)
        
        self.vlayout = QtGui.QVBoxLayout()
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.vlayout.setSpacing(0)
        self.vlayout.addWidget(self.limit_rot, stretch=1)
        self.root.setLayout(self.vlayout)

    def change_config(self, controller, d):

        self.logger.debug('rotator-limit changing config dict=%s ins=%s' %(d, d['inst']))  

        obcp = d['inst']
        if obcp.startswith('#'):
            self.logger.debug('obcp is not assigned. %s' %obcp)
            return 

        try:
            sip.delete(self.limit_rot)
            sip.delete(self.vlayout)
        except Exception as e:
            self.logger.error('error: deleting current layout. %s' %e)  
        else:
            self.set_layout(obcp=obcp)  
            controller.register_select('rotlimit', self.update, self.aliases)

    def build_gui(self, container):

        self.root = container

        try:
            obcp = self.controller.proxystatus.fetchOne('FITS.SBR.MAINOBCP')
            self.set_layout(obcp)
        except Exception as e:
            self.logger.error('error: building layout. %s' %e)

    def start(self):
        self.controller.register_select('rotlimit', self.update, self.aliases)
        self.controller.add_callback('change-config', self.change_config)


    def update(self, statusDict):
        self.logger.debug('status=%s' %str(statusDict))
        
        cur = statusDict.get(self.aliases[0])
        cmd = statusDict.get(self.aliases[1])
        self.limit_rot.update_limit(current=cur, cmd=cmd)


class ProbeLimitPlugin(PlBase.Plugin):
    """ Probe Limit  """

    def set_layout(self, obcp):
  
        self.set_aliases(obcp)
        self.set_limit(obcp)

        self.logger.debug('probe-limit obcp=%s aliases=%s title=%s' %(obcp, self.aliases, self.title)) 

        qtwidget = QtGui.QWidget()

        width = 350
        self.limit_probe = Limit.Limit(parent=qtwidget, title=self.title, \
                                        alarm=self.alarm, warn=self.warn, \
                                        limit=self.limit, width=width, logger=self.logger)
        
        self.vlayout = QtGui.QVBoxLayout()
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.vlayout.setSpacing(0)
        self.vlayout.addWidget(self.limit_probe, stretch=1)
        self.root.setLayout(self.vlayout)

    def change_config(self, controller, d):

        self.logger.debug('probe-limit changing config dict=%s ins=%s' %(d, d['inst']))  

        obcp = d['inst']
        if obcp.startswith('#'):
            self.logger.debug('obcp is not assigned. %s' %obcp)
            return 

        try:
            if not (self.obcp in self.ao or self.obcp == self.popt2):
                sip.delete(self.limit_probe)
                sip.delete(self.vlayout)
        except Exception as e:
            self.logger.error('error: deleting current layout. %s' %e)  
        else:
            if not (obcp in self.ao or obcp == self.popt2):
                self.set_layout(obcp=obcp)  
                controller.register_select(self.register_name, self.update, self.aliases)
        finally:
            self.obcp = obcp


    def build_gui(self, container):

        self.popt = 'SPCAM'  
        self.pir = 'FMOS'
        self.ag = ('MOIRCS', 'FOCAS', 'COMICS', 'HDS', 'SUKA')
        self.ao = ('IRCS', 'HICIAO', 'K3D', )
        self.popt2 = 'HSC'
 
        self.root = container

        try:
            self.obcp = self.controller.proxystatus.fetchOne('FITS.SBR.MAINOBCP')
            self.set_layout(obcp=self.obcp)
        except Exception as e:
            self.logger.error('error: building layout. %s' %e)

    def update(self, statusDict):
        self.logger.debug('status=%s' %str(statusDict))
        
        cur = statusDict.get(self.aliases[0])
        cmd = statusDict.get(self.aliases[1])
        self.limit_probe.update_limit(current=cur, cmd=cmd)


class Probe1LimitPlugin(ProbeLimitPlugin):
    """ AG Probe R/X Limit  """

    def set_aliases(self, obcp):

        if obcp in self.ag:
            self.aliases = ['TSCV.AGR', 'TSCL.AG_R_CMD']     
        elif obcp == self.popt:
            self.aliases = ['TSCL.AGPF_Y', 'TSCL.AGPF_Y_CMD']
        elif obcp == self.pir:
            self.aliases = ['TSCL.AGPIR_Y', 'TSCL.AGPIR_Y_CMD']
        else:
            self.aliases = [None, None]

    def set_limit(self, obcp):

        # instrument name: title, warn, alarm,  limit
        limit = {'SPCAM': ('Ag-X Popt', (0.0, 170.0), (0.0, 170.0), (0.0, 170.0)), 
                 'FMOS': ('Ag-X Pir', (-9.0, 239.0), (-10.0, 240.0), (-10.0, 240.0)),
                 'HDS': ('Ag_R Ns Opt', (0.0, 140.0), (0.0, 140.0), (-5.0, 145.0)), 
                 'COMICS': ('Ag-R Cs', (0.0, 140.0), (0.0, 140.0), (-5.0, 145.0)),
                 'MOIRCS': ('Ag-R Cs', (0.0, 140.0), (0.0, 140.0), (-5.0, 145.0)),
                 'FOCAS': ('Ag-R Cs', (0.0, 140.0), (0.0, 140.0), (-5.0, 145.0)),
                 'SUKA': ('Ag-R Cs', (0.0, 140.0), (0.0, 140.0), (-5.0, 145.0)),}

        try:
            self.title, self.warn, self.alarm, self.limit = limit[obcp]
        except Exception as e:
            self.logger.error('error: seting limit. %s' %e)
            self.title, self.warn, self.alarm, self.limit = None

    def start(self):
        self.register_name = 'probe1limit'
        self.controller.register_select(self.register_name, self.update, self.aliases)
        self.controller.add_callback('change-config', self.change_config)


class Probe2LimitPlugin(ProbeLimitPlugin):
    """ AG Probe Theta/Y Limit  """

    def set_aliases(self, obcp):

        if obcp in self.ag:
            self.aliases = ['TSCV.AGTheta', 'TSCL.AG_THETA_CMD']    
        elif obcp == self.popt:
            self.aliases = ['TSCL.AGPF_Y', 'TSCL.AGPF_Y_CMD']
        elif obcp == self.pir:
            self.aliases = ['TSCL.AGPIR_Y', 'TSCL.AGPIR_Y_CMD']
        else:
            self.aliases = [None, None]
 
    def set_limit(self, obcp):

        # instrument name: title, warn, alarm,  limit
        limit = {'SPCAM': ('Ag-Y Popt', (-20.0, 20.0), (-20.0, 20.0), (-20.0, 20.0)), 
                 'FMOS': ('Ag-Y Pir', (-40.0, 40.0), (-40.0, 40.0), (-40.0, 40.0)),
                 'HDS': ('Ag_Theta Ns Opt', (-270.0, 270.0), (-270.0, 270.0), (-270.0, 270.0)), 
                 'COMICS': ('Ag-Theta Cs', (-185.0, 185.0), (-185.0, 185.0), (-185.0, 185.0)),
                 'MOIRCS': ('Ag-Theta Cs', (-185.0, 185.0), (-185.0, 185.0), (-185.0, 185.0)),
                 'FOCAS': ('Ag-Theta Cs', (-185.0, 185.0), (-185.0, 185.0), (-185.0, 185.0)),
                 'SUKA': ('Ag-Theta Cs', (-185.0, 185.0), (-185.0, 185.0), (-185.0, 185.0)),}

        try:
            self.title, self.warn, self.alarm, self.limit = limit[obcp]
        except Exception as e:
            self.logger.error('error: seting limit. %s' %e)
            self.title, self.warn, self.alarm, self.limit = None

    def start(self):
        self.register_name = 'probe2limit'
        self.controller.register_select(self.register_name, self.update, self.aliases)
        self.controller.add_callback('change-config', self.change_config)





# class Probe1LimitPlugin(PlBase.Plugin):
#     """ AG Probe R/X Limit  """

#     def __set_aliases(self, obcp):

#         if obcp in self.ag_r:
#             self.aliases = ['TSCV.AGR', 'TSCL.AG_R_CMD']     
#         elif obcp == self.popt_x:
#             self.aliases = ['TSCL.AGPF_Y', 'TSCL.AGPF_Y_CMD']
#         elif obcp == self.pir_x:
#             self.aliases = ['TSCL.AGPIR_Y', 'TSCL.AGPIR_Y_CMD']
#         else:
#             self.aliases = [None, None]

#     def __set_limit(self, obcp):

#         # instrument name: title, warn, alarm,  limit
#         limit = {'SPCAM': ('Ag-X Popt', (0.0, 170.0), (0.0, 170.0), (0.0, 170.0)), 
#                  'FMOS': ('Ag-X Pir', (-9.0, 239.0), (-10.0, 240.0), (-10.0, 240.0)),
#                  'HDS': ('Ag_R Ns Opt', (0.0, 140.0), (0.0, 140.0), (-5.0, 145.0)), 
#                  'COMICS': ('Ag-R Cs', (0.0, 140.0), (0.0, 140.0), (-5.0, 145.0)),
#                  'MOIRCS': ('Ag-R Cs', (0.0, 140.0), (0.0, 140.0), (-5.0, 145.0)),
#                  'FOCAS': ('Ag-R Cs', (0.0, 140.0), (0.0, 140.0), (-5.0, 145.0)),}

#         try:
#             self.title, self.warn, self.alarm, self.limit = limit[obcp]
#         except Exception as e:
#             self.logger.error('error: seting limit. %s' %e)
#             self.title, self.warn, self.alarm, self.limit = None

#     def set_layout(self, obcp):
  
#         self.__set_aliases(obcp)
#         self.__set_limit(obcp)

#         self.logger.debug('probe-limit r/x. obcp=%s aliases=%s  title=%s' %(obcp, self.aliases, self.title)) 

#         qtwidget = QtGui.QWidget()

#         width = 350
#         self.limit_probe1 = Limit.Limit(parent=qtwidget, title=self.title, \
#                                         alarm=self.alarm, warn=self.warn, \
#                                         limit=self.limit, width=width, logger=self.logger)
        
#         self.vlayout = QtGui.QVBoxLayout()
#         self.vlayout.setContentsMargins(0, 0, 0, 0)
#         self.vlayout.setSpacing(0)
#         self.vlayout.addWidget(self.limit_probe1, stretch=1)
#         self.root.setLayout(self.vlayout)

#     def change_config(self, controller, d):

#         self.logger.debug('probe-limit r/x changing config dict=%s ins=%s' %(d, d['inst']))  

#         obcp = d['inst']
#         if obcp.startswith('#'):
#             self.logger.debug('obcp is not assigned. %s' %obcp)
#             return 

#         try:
#             if not (self.obcp in self.ao or self.obcp == self.hsc):
#                 sip.delete(self.limit_probe1)
#                 sip.delete(self.vlayout)
#         except Exception as e:
#             self.logger.error('error: deleting current layout. %s' %e)  
#         else:
#             if not (obcp in self.ao or obcp == self.hsc):
#                 self.set_layout(obcp=obcp)  
#                 controller.register_select('probe1limit', self.update, self.aliases)
#         finally:
#             self.obcp = obcp

#     def build_gui(self, container):

#         self.popt_x = 'SPCAM'  
#         self.pir_x = 'FMOS'
#         self.ag_r = ('MOIRCS', 'FOCAS', 'COMICS', 'HDS',)
#         self.ao = ('IRCS', 'HICIAO', 'K3D', )
#         self.hsc = 'HSC'
 
#         self.root = container

#         try:
#             self.obcp = self.controller.proxystatus.fetchOne('FITS.SBR.MAINOBCP')
#             self.set_layout(obcp=self.obcp)
#         except Exception as e:
#             self.logger.error('error: building layout. %s' %e)

#     def start(self):
#         if not (self.obcp in self.ao or self.obcp == self.hsc):
#             self.controller.register_select('probe1limit', self.update, self.aliases)
#         self.controller.add_callback('change-config', self.change_config)

#     def update(self, statusDict):
#         self.logger.debug('status=%s' %str(statusDict))
        
#         cur = statusDict.get(self.aliases[0])
#         cmd = statusDict.get(self.aliases[1])
#         self.limit_probe1.update_limit(current=cur, cmd=cmd)


# class Probe2LimitPlugin(PlBase.Plugin):
#     """ AG Probe Theta/Y Limit  """

#     def __set_aliases(self, obcp):

#         if obcp in self.ag_theta:
#             self.aliases = ['TSCV.AGTheta', 'TSCL.AG_THETA_CMD']    
#         elif obcp == self.popt_y:
#             self.aliases = ['TSCL.AGPF_Y', 'TSCL.AGPF_Y_CMD']
#         elif obcp == self.pir_y:
#             self.aliases = ['TSCL.AGPIR_Y', 'TSCL.AGPIR_Y_CMD']
#         else:
#             self.aliases = [None, None]
 
#     def __set_limit(self, obcp):

#         # instrument name: title, warn, alarm,  limit
#         limit = {'SPCAM': ('Ag-Y Popt', (-20.0, 20.0), (-20.0, 20.0), (-20.0, 20.0)), 
#                  'FMOS': ('Ag-Y Pir', (-40.0, 40.0), (-40.0, 40.0), (-40.0, 40.0)),
#                  'HDS': ('Ag_Theta Ns Opt', (-270.0, 270.0), (-270.0, 270.0), (-270.0, 270.0)), 
#                  'COMICS': ('Ag-Theta Cs', (-185.0, 185.0), (-185.0, 185.0), (-185.0, 185.0)),
#                  'MOIRCS': ('Ag-Theta Cs', (-185.0, 185.0), (-185.0, 185.0), (-185.0, 185.0)),
#                  'FOCAS': ('Ag-Theta Cs', (-185.0, 185.0), (-185.0, 185.0), (-185.0, 185.0)),}

#         try:
#             self.title, self.warn, self.alarm, self.limit = limit[obcp]
#         except Exception as e:
#             self.logger.error('error: seting limit. %s' %e)
#             self.title, self.warn, self.alarm, self.limit = None

#     def set_layout(self, obcp):
  
#         self.__set_aliases(obcp)
#         self.__set_limit(obcp)

#         self.logger.debug('probe-limit theta/y. obcp=%s aliases=%s  title=%s' %(obcp, self.aliases, self.title)) 

#         qtwidget = QtGui.QWidget()

#         width = 350
#         self.limit_probe2 = Limit.Limit(parent=qtwidget, title=self.title, \
#                                         alarm=self.alarm, warn=self.warn, \
#                                         limit=self.limit, width=width, logger=self.logger)
        
#         self.vlayout = QtGui.QVBoxLayout()
#         self.vlayout.setContentsMargins(0, 0, 0, 0)
#         self.vlayout.setSpacing(0)
#         self.vlayout.addWidget(self.limit_probe2, stretch=1)
#         self.root.setLayout(self.vlayout)

#     def change_config(self, controller, d):

#         self.logger.debug('probe-limit theta/y changing config dict=%s ins=%s' %(d, d['inst']))  

#         obcp = d['inst']
#         if obcp.startswith('#'):
#             self.logger.debug('obcp is not assigned. %s' %obcp)
#             return 

#         try:
#             if not (self.obcp in self.ao or self.obcp == self.hsc):
#                 self.logger.debug('probe-limit deleteing %s' %obcp)
#                 sip.delete(self.limit_probe2)
#                 sip.delete(self.vlayout)
#         except Exception as e:
#             self.logger.error('error: deleting current layout. %s' %e)  
#         else:
#             if not (obcp in self.ao or obcp == self.hsc):
#                 self.set_layout(obcp=obcp)  
#                 controller.register_select('probe2limit', self.update, self.aliases)
#         finally:
#             self.obcp = obcp

#     def build_gui(self, container):

#         self.popt_y = 'SPCAM'  
#         self.pir_y = 'FMOS'
#         self.ag_theta = ('MOIRCS', 'FOCAS', 'COMICS', 'HDS',)
#         self.ao = ('IRCS', 'HICIAO', 'K3D', )
#         self.hsc = 'HSC'

#         self.root = container

#         try:
#             self.obcp = self.controller.proxystatus.fetchOne('FITS.SBR.MAINOBCP')
#             self.set_layout(obcp=self.obcp)
#         except Exception as e:
#             self.logger.error('error: building layout. %s' %e)

#     def start(self):
#         if not (self.obcp in self.ao or self.obcp == self.hsc):
#             self.controller.register_select('probe2limit', self.update, self.aliases)
#         self.controller.add_callback('change-config', self.change_config)

#     def update(self, statusDict):
#         self.logger.debug('status=%s' %str(statusDict))
        
#         cur = statusDict.get(self.aliases[0])
#         cmd = statusDict.get(self.aliases[1])
#         self.limit_probe2.update_limit(current=cur, cmd=cmd)


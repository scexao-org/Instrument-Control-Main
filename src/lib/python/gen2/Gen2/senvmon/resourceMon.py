#!/usr/bin/env python
#
# Takeshi Inagaki (tinagaki@naoj.org)
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Apr 30 13:15:29 HST 2012
#]
#

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class ResourceMonitor(QWidget):

    def __init__(self, statusKeys=("TSCV.WATER", "TSCV.OIL"), logger=None):
        super(ResourceMonitor, self).__init__()

        self.logger=logger
        self.statusKeys = statusKeys
        
        self.vl=QVBoxLayout()
        self.setLayout(self.vl)
        self.vl.setSpacing(3)
        self.vl.setMargin(3)

        # water label layout
        self.labelLayout1 = QHBoxLayout()
        
        # water label
        self.water=QLabel()
        self.water.setText("Water Storage: ")
        self.water.font().setBold(True)
        self.water_status=QLabel("<font color=darkblue>Normal</font>")
        self.labelLayout1.addWidget(self.water)
        self.labelLayout1.addWidget(self.water_status)
        self.labelLayout1.addStretch()
       
        # oil label layout
        self.labelLayout2 = QHBoxLayout()

        # oil label
        self.oil=QLabel()
        self.oil.setText('Oil Storage:')
        self.oil.font().setBold(True)
        self.oil_status=QLabel("<font color=darkblue>Normal</font>")
        self.labelLayout2.addWidget(self.oil)
        self.labelLayout2.addWidget(self.oil_status)
        self.labelLayout2.addStretch()

        self.vl.addLayout(self.labelLayout1, stretch=0)
        self.vl.addLayout(self.labelLayout2, stretch=0)  

    def fetchData(self, now, stat_vals):   
        """ fetch data corresponging to status aliases """
                
        try:
            waterVal, oilVal = [stat_vals[sk] for sk in self.statusKeys]
            self.logger.debug('water=%s oil=%s' %(str(waterVal), str(oilVal)))
            self.update_water_status(waterVal)
            self.update_oil_status(oilVal)

        except Exception, e:
            self.logger.error('fetchData error <%s>' %e)
            pass     
   
    def update_water_status(self, waterVal):
        """ update water storage status """
        self.logger.debug('updating water val... %s' %str(waterVal)) 
        
        if waterVal != 0:            
            if waterVal <= -1.0:
                self.water_status.setText("<font color=red>LOW ALARM</font>")                
            elif waterVal >= 1.0:
                self.water_status.setText("<font color=red>HIGH ALARM</font>")                
            else:
                self.water_status.setText("<font color=yellow>Undefined</font>")
                
        else:
            self.water_status.setText("<font color=darkblue>Normal</font>")
       

    def update_oil_status(self, oilVal):
        """ update oil storage status """
        self.logger.debug('updating oil val... %s' %str(oilVal)) 
                
        if oilVal  != 0:            
            if oilVal <= -1.0:
                self.oil_status.setText("<font color=red>LOW ALARM</font>")                 
            elif oilVal >= 1.0:
                self.oil_status.setText("<font color=red>HIGH ALARM</font>")
            else:
                self.oil_status.setText("<font color=yellow>Undefined</font>")                
        else:
            self.oil_status.setText("<font color=darkblue>Normal</font>")


#END






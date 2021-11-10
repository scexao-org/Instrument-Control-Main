#!/usr/bin/env python

from __future__ import division
import sys
import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from timeValueGraph import *

import SOSS.status as st
import remoteObjects as ro
import ssdlog

import random
import types

DIRN_DEFAULTSIZE = (250, 250)

class Ui_Directions(QWidget):
    
    def setupUi(self,Directions, size):
        
        super(Ui_Directions,self).__init__()
        
        self.setWindowTitle("Wind Direction & Dome AZ")
        # allow expansion
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding,
                                       QSizePolicy.Expanding))
        print size
        self.pref_width = size[0]
        self.pref_height = size[1]
        #self.resize(self.pref_width, self.pref_height)
        
        # wind-speed indicator
        self.wind_point=-77
        self.wind_speed_vertex=QPoint(0, self.wind_point)
        
        # wind direction pointer & wind speed indicator
        # defaul shape is an equilateral triangle, 
        # pointing to the center from 0 degree on the compass 
        self.windpointer=QPolygon([
            QPoint(8, -91),
            QPoint(-8, -91),
            self.wind_speed_vertex
        ])
        
        # the shape of subaru telescope   
        self.subaru = QRectF(-21, -25, 42, 50)
        # the pointer to a direction where subaru faces 
        self.subarupointer=QPolygon([
            QPoint(-15, -15),
            QPoint(15, -15),
            QPoint(0, 25)
        ])
        
    def sizeHint(self):
        return QSize(self.pref_width, self.pref_height)

#class Directions(Ui_Directions,TimeValueGraph):
class Directions(Ui_Directions):    
    def __init__(self, interval=None, statusKeys=("TSCS.AZ", "TSCL.WINDD", "TSCL.WINDS_O"), size=DIRN_DEFAULTSIZE, mode=None, logger=None, parent=None):
        
        super(Directions, self).__init__(parent)
        self.setupUi(self, size=size)
        
        self.wind_direction=0
        self.subaru_az=0
        self.wind_speed=0
        self.logger=logger
        self.statusKeys = statusKeys   
        
        if mode=='test':
            interval=1000*interval # milli sec
            self.logger.debug('setting interval %d' %interval )
            timer_d = QTimer(self)
            self.connect(timer_d, SIGNAL("timeout()"), self.fetch_fake_data)
            self.logger.debug('timer connected to fetchData' )
            timer_d.start(interval)
          
        elif mode == 'solo':
            ro.init()
            #st.g2StatusObj('status')
            self.status = ro.remoteObjectProxy('status') 
            interval=1000*interval # milli sec
            self.logger.debug('setting interval %d' %interval )
            timer_d = QTimer(self)
            self.connect(timer_d, SIGNAL("timeout()"), self.fetch_solo_data)
            self.logger.debug('timer connected to fetchData' )
            timer_d.start(interval)  

    
    def paintEvent(self,event=None):
        ''' paint canvas '''

        LogicalSize = 200.0
        side = min(self.width(), self.height())
        self.painter = QPainter()
        self.painter.begin(self)
        self.painter.fillRect(event.rect(), QBrush(Qt.white))
        
        self.painter.setRenderHint(QPainter.Antialiasing)
        self.painter.setRenderHint(QPainter.SmoothPixmapTransform)
          
        self.painter.translate(self.width() / 2, self.height() / 2)
        self.painter.scale(side / LogicalSize, side / LogicalSize)
        
        # draw a line in every 30 degree
        p=QPen(Qt.darkBlue, 2)
        self.painter.setPen(p)
        #self.painter.setPen(Qt.darkBlue)
        for i in range(0, 12):
            if i%3==0:
                self.painter.drawLine(88, 0, 96, 0)
            else:
                self.painter.drawLine(80, 0, 96, 0)
            self.painter.rotate(30.0)
      
        # draw the pointer of a wind direction and  its speed
        # default: pointing north to the center  
        self.painter.save()
        self.painter.setPen(Qt.NoPen)
        self.painter.setBrush(QBrush(QColor('orange')))
        self.painter.rotate(self.wind_direction)
        self.painter.drawConvexPolygon(self.windpointer)
        self.painter.restore() 

       
        # some adjustment (0,0) is the center of the compass
        # the compass of wind directions 
        f=QFont("Helvetica", 10, QFont.Bold)
        self.painter.setFont(f)
        #text0=QRect(-15, -73 , 25,25)
        #self.painter.drawText(text0, Qt.AlignCenter,  "0") # North
        self.painter.drawText(-3, -73,   "0") # North
        self.painter.drawText(-12, 81, "180") # South
        self.painter.drawText(68, 4, "90")    # East
        self.painter.drawText(-80, 4, "270")  # West 

        # some adjustment (0,0) is the center of the compass
        # the comapss of the telescope
        self.painter.drawText(-4, -30, "N") # North:180 deg
        self.painter.drawText(-4, 39, "S") # South (for subaru, the south is 0 degree) 
        self.painter.drawText(31, 4, "E")    # East:-90 deg
        self.painter.drawText(-41, 4, "W")  # West:90 deg

        # draw a lines in 5 deg around the compass
        pen=QPen(Qt.darkCyan, 1.5)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        self.painter.setPen(pen)
        #self.painter.setPen(QPen(Qt.darkCyan, 2, Qt.RoundCap, Qt.RoundJoin))
    

        for j in range(0, 72):
            if (j % 6) != 0: 
                self.painter.drawLine(92, 0, 96, 0)
            self.painter.rotate(5.0)

        # draw the subaru telescope and its pointing 
        # default: pointing to the south, which is 0 degree in subaru's way
        self.painter.save()
        self.painter.setPen(Qt.NoPen)
        #self.painter.setPen(QPen(Qt.gray))
        self.painter.rotate(self.subaru_az)
        self.painter.setBrush(QBrush(Qt.lightGray))
        self.painter.drawEllipse(self.subaru)
        self.painter.setBrush(QBrush(Qt.darkBlue))
        self.painter.drawConvexPolygon(self.subarupointer) 
        self.painter.restore()

        self.painter.end()
  
    
    def set_windspeed(self):
        ''' set the shape of wind-speed '''
        self.wind_speed_vertex=QPoint(0, self.wind_speed)
        
        self.windpointer=QPolygon([
            QPoint(8, -91),
            QPoint(-8, -91),
            self.wind_speed_vertex
        ])
        
    
    def _is_float(self, az, wind_d, wind_s):
        ''' check if fetched data are float or not '''
        if type(az) is float:
            self.subaru_az=az
        if type(wind_d) is float:
            self.wind_direction=wind_d
        if type(wind_s) is float:
            self.wind_speed=self.wind_point+wind_s

    def fetch_fake_data(self):
        ''' this is for testing purpose '''
        az=float(random.randrange(0.0,360.0))
        wind_d=float(random.randrange(0.0,360.0))
        wind_s=float(random.randrange(0.0,50.0))
        
        self.logger.debug('fetching fake data az=%s wind_d=%s wind_speed=%s' %(str(az), str(wind_d), str(wind_s)))  
        stat_val={"TSCS.AZ":az, "TSCL.WINDD":wind_d, "TSCL.WINDS_O":wind_s}
 
        self.fetchData(stat_val=stat_val)

    def fetch_solo_data(self):
        ''' this is for solo mode(ruuning wind-direction itself)'''
        stat_dict={"TSCS.AZ":None, "TSCL.WINDD":None, "TSCL.WINDS_O":None}
        try:
            stat_val=self.status.fetch(stat_dict)
            self.fetchData(stat_val=stat_val)
        except ro.remoteObjectError, e:
            self.logger.error('fetchData error <%s>' %e)
            pass    

    def fetchData(self, now=None, stat_val=None):
        ''' update status values  '''   
        self.logger.debug('fetchdata stat_vals<%s>' %(stat_val))
        try:
            az, wind_d, wind_s=[stat_val[sk] for sk in self.statusKeys]
            self.logger.debug('fetching values domeAz=%s wind-direction=%s wind_speed=%s' %(str(az), str(wind_d), str(wind_s)))
            self._is_float(az,wind_d,wind_s)  
        except Exception,e:
            self.logger.error('fetchData error <%s>' %e)
            pass    
        
        self.set_windspeed()
        self.update()

    def setCoordinator(self, coordinator):
        pass

def main(options, args):

    import signal
    # catch keyboard interruption
    signal.signal(signal.SIGINT, signal.SIG_DFL)
  
    logger = ssdlog.make_logger('Wind Direction', options)

    #global_font=QFont("lucida", 10, QFont.Bold)   

    logger.debug('Wind direction starting...')
    
    try:
        app = QApplication(sys.argv)
        ds=Directions(interval=options.interval, mode=options.mode, logger=logger)
        ds.show()
        app.exec_()
    except KeyboardInterrupt:
        print 'keyboard interrupting...'
        app.shutdown() 
    #print 'shutting down'
    #sys.exit(app.exec_())


if __name__ == "__main__":
    
    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options] command [args]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--mode", dest="mode", metavar='MODE', 
                      default="obs",
                      help="Speficy the mode to run this program [solo|test]")
    optprs.add_option("--interval", dest="interval", type='int', metavar="INTERVAL",                      
                      default=3,
                      help="Time to update Wind Direction")
    ssdlog.addlogopts(optprs)
    (options, args) = optprs.parse_args()

    if len(args) != 0:
        optprs.error("incorrect number of arguments")

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
    
    


#! /usr/bin/env python
#
# Takeshi Inagaki
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Tue Sep  2 17:10:54 HST 2008
#]
#

import os, sys
import numpy
import pyfits
import time
import threading, Queue

import remoteObjects as ro
from StatusBundle import Bunch

try:
    from pylab import *
    from matplotlib import *    
    from qt import *
   
    QApplication.setColorSpec(QApplication.NormalColor)
    app = QApplication(sys.argv)
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure

except ImportError:
    print "You need to install matplot, qt, etc",
    #sys.exit(1)


# This seems to be what PyQt expects, according to the examples shipped in
# its distribution.
TRUE  = 1
FALSE = 0

progname = os.path.basename(sys.argv[0])
progversion = "0.1"

DISPLAY_QUEUE = Queue.Queue(50)

I_CUT_QUEUE = Queue.Queue(50)

IMAGE=None
PIXELX=PIXELY=None

version='0.1'

class remoteGuiderDisplay(ro.remoteObjectServer):
    def __init__(self, svcname, debug, port, usethread=False):
       
        # Superclass constructor
        #self.guider=GuiderSaveFrame(debug=False, monitor=monitor, svcname=svcname)
        ro.remoteObjectServer.__init__(self, svcname=svcname, port=port, usethread=usethread)
                                      
        self.debug=debug      
        #self.monitor=monitor
        self.image=None       

        self.status=ro.remoteObjectProxy('status')
        
#        if self.monitor:
#            self.db = StatusBundle.nestedStatusBundle()
#            m = ro.remoteObjectProxy(self.monitor)
#            self.db.register_sync(svcname, m)
        
    ######################################
    # Methods provided by remote object interface
    ######################################

    # guider display command
    # image, x, y are passed    
    def guider_display(self, data, pixelX, pixelY):
        
        try:
            DISPLAY_QUEUE.put_nowait( (data, pixelX, pixelY) )
            I_CUT_QUEUE.put_nowait( (data, pixelX, pixelY) )
            self.region_selection_data=data
            self.data_x=pixelX
            self.data_y=pixelY
            if options.debug:
                print 'def guider_display: put image into display Q'
            return ro.OK
        except Queue.Full():
            print 'display Q put failed'
            return ro.ERROR
     
    def region_selection(self):

        print 'region_selection called'

        if options.debug:
            print 'def region_selection called'
                
        # Decode binary data
        decode_image = ro.binary_decode(self.region_selection_data)

        # string to numpy    
        decode_image = numpy.fromstring(decode_image, numpy.float32, shape=(self.data_x, self.data_y)) 

        
        #numpy.reshape(self.image.data, (self.pixDeltaX,self.pixDeltaY)).astype('Float32'),
        
        try:
            os.remove('/tmp/VGW.fits')
        except:
            print 'No tmp/VGW.fits file'
            pass

        try:    
            hdu=pyfits.PrimaryHDU(decode_image)
            hdu.writeto( '/tmp/VGW.fits' )
        except IOError,e:
            print 'region selection write error %s' %(str(e)) 
        
        print 'enter x1 x2 y1 y2:'  
        line=sys.stdin.readline()
        line=line.strip()
        line=line.split()
        x1=line[0]; x2=line[1]; y1=line[2]; y2=line[3]
        print 'x1:[%s] x2:[%s] y1:[%s] y2:[%s]' %(x1, x2, y1, y2) 
      
        
        cordinate={'VGWQ.AGE.X1':int(x1), 'VGWQ.AGE.X2':int(x2), 'VGWQ.AGE.Y1':int(y1), 'VGWQ.AGE.Y2':int(y2)}

        print 'x y cordinate ', cordinate
    
        #self.status.store(cordinate)

        return ro.OK
            

class MplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    def __init__(self, parent=None, width=5, height=5, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        # We want the axes cleared every time plot() is called
        self.axes.hold(False)

        #self.compute_initial_figure()
        
        FigureCanvas.__init__(self, self.fig)
        self.reparent(parent, QPoint(0, 0))

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def sizeHint(self):
        w, h = self.get_width_height()
        return QSize(w, h)

    def minimumSizeHint(self):
        return QSize(10, 10)


class GuiderDisplayIcutMplCanvas(MplCanvas):

    def __init__(self, *args, **kwargs):
                
        MplCanvas.__init__(self, *args, **kwargs)
        timer = QTimer(self, "canvas update timer")
        QObject.connect(timer, SIGNAL("timeout()"), self.update_i_cut_figure)
        timer.start(1000, FALSE)
        self.i_cut_image=self.decode_image=self.X=self.Y=None
        

    def update_i_cut_figure(self):

        try:
            #self.diplay_image=DISPLAY_QUEUE.get(block=True, timeout=0.2)
            self.decode_image, self.X, self.Y=I_CUT_QUEUE.get(block=True, timeout=0.1)
                                  
            if options.debug:
                print 'def update_i_cut_figure: get image from display Q  X:%s  Y:%s' %(self.X, self.Y)
                
            # Decode binary data
            self.decode_image = ro.binary_decode(self.decode_image)

            # string to numpy    
            self.decode_image = numpy.fromstring(self.decode_image, numpy.uint32, shape=(self.X, self.Y)) 
            
            self.i_cut_image=self.decode_image-self.decode_image.mean()
                          
            self.axes.imshow(where(less(self.i_cut_image, 0), 0, self.i_cut_image), origin='lower', cmap=cm.gray) 
                           
            #self.axes.imshow(where(less(self.i_cut_image-self.i_cut_image.mean(), 0), 0, self.i_cut_image-self.i_cut_image.mean()), origin='lower', cmap=cm.gray)
            self.draw()          
             
        except:
            pass
        
#        try:
#            self.i_cut_image=I_CUT_QUEUE.get(block=True, timeout=0.2)            
#            self.axes.imshow(where(less(self.i_cut_image-self.i_cut_image.mean(), 0), 0, self.i_cut_image-self.i_cut_image.mean()), origin='lower', cmap=cm.gray)
#            self.draw()
#        except:
#            pass 
      

class GuiderDisplayMplCanvas(MplCanvas):
    """A canvas that updates itself every second with a new plot."""
    def __init__(self, *args, **kwargs):
                
        MplCanvas.__init__(self, *args, **kwargs)
        timer = QTimer(self, "canvas update timer")
        QObject.connect(timer, SIGNAL("timeout()"), self.update_figure)
        timer.start(1000, FALSE)
        
        self.diplay_image=self.X=self.Y=None       
  
    def update_figure(self): 
                  
        try:
            #self.diplay_image=DISPLAY_QUEUE.get(block=True, timeout=0.2)
            self.diplay_image, self.X, self.Y=DISPLAY_QUEUE.get(block=True, timeout=0.1)
                                  
            if options.debug:
                print 'def update_figure: get image from display Q  X:%s  Y:%s' %(self.X, self.Y)
                
            # Decode binary data
            self.diplay_image = ro.binary_decode(self.diplay_image)

            # string to numpy    
            self.diplay_image = numpy.fromstring(self.diplay_image, numpy.uint32, shape=(self.X, self.Y)) 
                      
            self.axes.imshow(self.diplay_image, origin='lower', cmap=cm.gray)
            self.draw()  
        except:
            pass
#     

class ApplicationWindow(QMainWindow):
    def __init__(self, svc):
        self.svc = svc
        
        QMainWindow.__init__(self, None,
                             "application main window",
                             Qt.WType_TopLevel | Qt.WDestructiveClose)

        self.file_menu = QPopupMenu(self)
        self.file_menu.insertItem('&Quit', self.fileQuit, Qt.CTRL + Qt.Key_Q)
        self.menuBar().insertItem('&File', self.file_menu)

        self.help_menu = QPopupMenu(self)
        self.menuBar().insertSeparator()
        self.menuBar().insertItem('&Help', self.help_menu)

        self.help_menu.insertItem('&About', self.about)

        self.main_widget = QWidget(self, "Main widget")

        l = QVBoxLayout(self.main_widget)
        gd = GuiderDisplayMplCanvas(self.main_widget, width=4, height=4, dpi=100)
        gdi = GuiderDisplayIcutMplCanvas(self.main_widget, width=4, height=4, dpi=100)
        
        l.addWidget(gdi)
        l.addWidget(gd)

        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

        self.statusBar().message("QT matplot", 8000)
 
 
    def fileQuit(self):
        self.svc.ro_stop()
        qApp.exit(0)

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QMessageBox.about(self, "About %s" % progname,
u"""%(prog)s version %(version)s
Copyright \N{COPYRIGHT SIGN} 2005 Florent Rougon

display test"""
                          % {"prog": progname, "version": progversion})


def main_display(svc):
       
    aw = ApplicationWindow(svc)
    aw.setCaption("%s" % progname)
    qApp.setMainWidget(aw)
    aw.show()
    sys.exit(qApp.exec_loop())
      
if __name__ == "__main__":
    
        # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage, version=('%%prog %s' % version))
    parser.add_option("--debug", dest="debug", default=False, action="store_true",
                     help="Enter the pdb debugger on main()")
    parser.add_option("--profile", dest="profile", action="store_true",
                     default=False,
                     help="Run the profiler on main()")
    parser.add_option("--log", dest="logfile", metavar="FILE",
                     default="TaskManager.log",
                     help="Write logging output to FILE")
    parser.add_option("--svcname", dest="svcname", metavar="NAME",
                      help="Register using NAME as service name")
    parser.add_option("-m", "--monitor", dest="monitor", default=False,
                      metavar="NAME",
                      help="Reflect internal status to monitor service NAME")
    parser.add_option("--port", dest="port", type="int",
                      default=None,
                      help="Register using PORT", metavar="PORT")                      
                      

    (options, args) = parser.parse_args(sys.argv[1:])

    if len(args) != 0:
       parser.error("incorrect number of arguments")          
    
    # assign svcname 
    if options.svcname:   svcname = options.svcname
    else:                 svcname = 'guiderdisplay'    
   
    # debug option   
    if options.debug:     debug=True
    else:                 debug=False
     
        
    # set up port   
    if options.port:      port = options.port 
    else:                 port = None
            
     
    # Remote objects initializion
    ro.init()

    # If we are handed a service name, use it.  Otherwise construct a
    # default one.
    svc = remoteGuiderDisplay(svcname, debug, port, usethread=True)

    # start image displaying server
    try:
        svc.ro_start()
        print "guiderdisplay: svc started"
    except:
        print "guiderdisplay: failed to start svc"
 
    # start gui 
    # main_display(svc)

    #try:
    #    sys.stdin.readline()
    #except KeyboardInterrupt:
    #    pass

    # stop all threads
    #svc.ro_stop()
    #print "guiderint: svc stopped"
    
    
      
    #sys.exit(1)
    
    
    
    

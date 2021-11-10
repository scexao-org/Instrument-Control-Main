#!/usr/bin/env python


import os
import sys
import glob
import subprocess,shlex
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import ssdlog


class GuiderListWidget(QListWidget):
    """ list widget """
    def __init__(self, parent=None):
        super(GuiderListWidget, self).__init__(parent)
        #self.setAcceptDrops(True)
        self.setDragEnabled(True)
        

    def dragEnterEvent(self, event):
        
        if event.mimeData().hasFormat("application/x-icon-and-text"):
            event.accept()
        else:
            event.ignore()


    def dragMoveEvent(self, event):
        
        if event.mimeData().hasFormat("application/x-icon-and-text"):
            event.setDropAction(Qt.MoveAction)
            event.accept()
        else:
            event.ignore()


#    def dropEvent(self, event):
#        print 'drop event...'
#        if event.mimeData().hasFormat("application/x-icon-and-text"):
#            data = event.mimeData().data("application/x-icon-and-text")
#            stream = QDataStream(data, QIODevice.ReadOnly)
#            text = QString()
#            icon = QIcon()
#            stream >> text >> icon
#            item = QListWidgetItem(text, self)
#            item.setIcon(icon)
#            event.setDropAction(Qt.MoveAction)
#            event.accept()
#        else:
#            event.ignore()


    def startDrag(self, dropActions):
        
        item = self.currentItem()
        icon = item.icon()
        data = QByteArray()
        stream = QDataStream(data, QIODevice.WriteOnly)
        stream << item.text() << icon
        mimeData = QMimeData()
        mimeData.setData("application/x-icon-and-text", data)
        drag = QDrag(self)
        drag.setMimeData(mimeData)
        pixmap = icon.pixmap(24, 24)
        drag.setHotSpot(QPoint(12, 12))
        drag.setPixmap(pixmap)
        if drag.start(Qt.MoveAction) == Qt.MoveAction:
            self.takeItem(self.row(item))


class GuiderWidget(QWidget):
    
    def __init__(self, text, icon=QIcon(), parent=None):
        super(GuiderWidget, self).__init__(parent)
        self.setAcceptDrops(True)
        self.text = QString(text)
        self.icon = icon
        self.dragged = QColor(Qt.white)
        self.drag = QColor(Qt.yellow).light()
        #self.error = QColor(Qt.red) 
        #self.status={'init':True, 'normal':False, 'error':False}
        

    def minimumSizeHint(self):
        fm = QFontMetricsF(self.font())
        if self.icon.isNull():
            return QSize(fm.width(self.text), fm.height() * 1.5)
        return QSize(34 + fm.width(self.text),
                     max(34, fm.height() * 1.5))


    def paintEvent(self, event):
        #print 'print event... %s ' %(str(self.name))
        height = QFontMetricsF(self.font()).height()
        painter = QPainter(self)
        
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        

        if self.icon.isNull():
            #painter.clear()
            painter.fillRect(self.rect(), self.drag)
            painter.drawText(10, height, self.text)
        else:
            painter.fillRect(self.rect(), self.dragged)
            pixmap = self.icon.pixmap(24, 24) 
            painter.drawPixmap(10, 5, pixmap)
            painter.drawText(40, height, self.text )


    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-icon-and-text"):
            event.accept()
        else:
            event.ignore()


#    def dragMoveEvent(self, event):
#        if event.mimeData().hasFormat("application/x-icon-and-text"):
#            event.setDropAction(Qt.CopyAction)
#            event.accept()
#        else:
#            event.ignore()

    def is_right_location(self,text):
        print 'is right location', text
        
        typegroup=['AG','SV','SH','FMOS']
        bingroup=['1x1','2x2','4x4','8x8']
        kindgroup=['Dark','Flat','Obj','Sky']
        hostgroup=['g2b1','g2b3','g2s1','g2s3','g2s4']

        groups=[typegroup,bingroup,kindgroup,hostgroup]
        params={'AG Type':typegroup, 'AG Binning':bingroup, 
                'AG Kind':kindgroup, 'Target Host':hostgroup}
       
        try:
            print 'trying <%s>' %self.text
            k='%s' %self.text
            vals=params[k

]
            print vals
            if text in vals:
                return True
            else:
                return False
        except KeyError,e:
            print 'except'
            for g in groups:
                print g
                if text in g and self.text in g:
                    return True
            return False
 

    def dropEvent(self, event):
         
        if event.mimeData().hasFormat("application/x-icon-and-text"):
            data = event.mimeData().data("application/x-icon-and-text")
            stream = QDataStream(data, QIODevice.ReadOnly)
            text = QString()
            icon = QIcon()
            stream >> text >> icon          

            if self.is_right_location(text):
                self.text=text
                self.icon=icon
                self.drag=QColor(Qt.white)
                event.setDropAction(Qt.CopyAction)
                event.accept()
                self.updateGeometry()
                self.update()
            else:
                event.ignore()
        else:
            event.ignore()


 #   def mouseMoveEvent(self, event):
 #       self.startDrag()
 #       QWidget.mouseMoveEvent(self, event)


 #   def startDrag(self):
 #       icon = self.icon
 #       if icon.isNull():
 #           return
 #       data = QByteArray()
 #       stream = QDataStream(data, QIODevice.WriteOnly)
 #       stream << self.text << icon
 #       mimeData = QMimeData()
 #       mimeData.setData("application/x-icon-and-text", data)
 #       drag = QDrag(self)
 #       drag.setMimeData(mimeData)
 #       pixmap = icon.pixmap(24, 24)
 #       drag.setHotSpot(QPoint(12, 12))
 #       drag.setPixmap(pixmap)
 #       drag.start(Qt.CopyAction)



  


class Form(QDialog):
    """ Guider Sim Gui """

    def _add_items(self, listwidget, subdir):
        path = os.path.dirname(__file__)

        path=os.path.join(path,subdir)
        for image in sorted(glob.glob('%s/*.png' %path)):
            image=os.path.basename(image)
            item = QListWidgetItem(os.path.basename(image.split(".")[0]))
            item.setIcon(QIcon(os.path.join(path, image) ))
            listwidget.addItem(item)
  

    def __init__(self, logger, parent=None):
        super(Form, self).__init__(parent)
        self.logger=logger

        self.logger.debug('setting up form..')
       
        self.resize(580,350)


        # guider type 
        images='images/type'
        guiderTypeWidget=GuiderListWidget()
        guiderTypeWidget.setViewMode(QListView.IconMode)
        #guiderTypeWidget.setFlow(QListView.LeftToRight)
        guiderTypeWidget.setSpacing(10)
        #guiderTypeWidget.setGeometry(QRect(30,30,200,50))

        #guiderTypeWidget.updateGeometries()
        self._add_items(guiderTypeWidget,images)
        #guiderTypeWidget.width(200)

        # guider binning 
        images='images/binning'
        guiderBinningWidget=GuiderListWidget()
        guiderBinningWidget.setViewMode(QListWidget.IconMode)
        guiderBinningWidget.setSpacing(10)
        
        self._add_items(guiderBinningWidget,images)

        # guider kind
        images='images/kind'
        guiderKindWidget=GuiderListWidget()
        guiderKindWidget.setViewMode(QListWidget.IconMode)
        guiderKindWidget.setSpacing(10)
        self._add_items(guiderKindWidget, images)

        # guider target host
        images='images/host'
        guiderHostWidget=GuiderListWidget()
        guiderHostWidget.setViewMode(QListWidget.IconMode)
        guiderHostWidget.setSpacing(10)
        self._add_items(guiderHostWidget,images)

        # 
        self.typeWidget = GuiderWidget("AG Type")
        self.kindWidget = GuiderWidget("AG Kind")
        self.binningWidget = GuiderWidget("AG Binning")
        self.hostWidget = GuiderWidget("Target Host")


        glayout = QGridLayout()

        ivlabel=QLabel('interval(sec)')
        numlabel=QLabel('num data')
        self.ivspinBox = QSpinBox()
        self.ivspinBox.setRange(1,100)
        self.numspinBox = QSpinBox()
        self.numspinBox.setRange(1,10000)

        glayout.addWidget(self.typeWidget, 0, 0,1, -1)
        glayout.addWidget(self.binningWidget, 1, 0 ,1, -1)
        glayout.addWidget(self.kindWidget, 2, 0, 1, -1)
        glayout.addWidget(self.hostWidget, 3, 0, 1, -1)

        glayout.addWidget(ivlabel, 4, 0)
        glayout.addWidget(self.ivspinBox, 4, 1)
        glayout.addWidget(numlabel, 5, 0)
        glayout.addWidget(self.numspinBox, 5, 1)


        line = QFrame()
        #self.line.setGeometry(QtCore.QRect(540,30,20,391))
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)


        vboxlayout = QVBoxLayout()
        vboxlayout.setMargin(0)
        vboxlayout.setSpacing(10)

        startButton = QPushButton('Start')
        stopButton = QPushButton('Stop')
      
        spacer = QSpacerItem(20,16,QSizePolicy.Minimum, QSizePolicy.Expanding)
        
        closeButton = QPushButton('Close')

        vboxlayout.addWidget(startButton)
        vboxlayout.addWidget(stopButton)
        vboxlayout.addItem(spacer)
        vboxlayout.addWidget(closeButton)
        
        # buttons connection
        QObject.connect(startButton, SIGNAL("clicked()"), self.start_guidersim)
        QObject.connect(stopButton, SIGNAL("clicked()"), self.stop_guidersim)
        QObject.connect(closeButton, SIGNAL("clicked()"), self.reject)



        vlayout = QVBoxLayout() 
        vlayout.setSpacing(5)

        #splitter = QSplitter(Qt.Vertical)
        #splitter.addWidget(guiderTypeWidget) 
        #splitter.addWidget(guiderBinningWidget) 
        #splitter.addWidget(guiderKindWidget) 
        vlayout.addWidget(guiderTypeWidget) 
        vlayout.addWidget(guiderBinningWidget) 
        vlayout.addWidget(guiderKindWidget) 
        vlayout.addWidget(guiderHostWidget)


        layout = QHBoxLayout()

        layout.addLayout(vlayout)
        layout.addLayout(glayout)
        layout.addWidget(line)
        layout.addLayout(vboxlayout) 
        self.setLayout(layout)

        self.setWindowTitle("Guiding Simulator")



class GuiderSim(Form):
    """ Guider Simulator """

    def __init__(self, logger):
        super(GuiderSim, self).__init__(logger)

        self.logger=logger
        self.pid=None
 
    def get_binning(self,bin):
             
        binning={'1x1':1,'2x2':2,'4x4':4,'8x8':8}
      
        try:
            return binning[bin]
        except KeyError,e:
            self.logger.debug('faile to get binning<%s>' %e)
            return None


    def get_kind(self,kind):

        kinds={'Dark':2,'Sky':4,'Flat':3,'Obj':1}

        try:
            return kinds[kind]
        except KeyError,e:
            self.logger.debug('faile to get kind<%s>' %e)
            return None


    def __get_param(self, obj, params, key):
        

        if not obj.icon.isNull():
            params[key]=str(obj.text)
            self.logger.debug('get param<%s>' %str(params[key]))
        else:
            params[key]=None
            obj.drag=QColor(Qt.red)
            obj.update() 


    def get_params(self):

        params={'type':None, 'binning':None, 'kind':None, 'interval':None, 'num':None, 'tgthost':None}

        # get ag type
        self.__get_param(self.typeWidget, params, key='type')  
           
        # get binning
        self.__get_param(self.binningWidget, params, key='binning') 
        params['binning']=self.get_binning(params['binning'])     

        # get kind
        self.__get_param(self.kindWidget, params, key='kind')
        params['kind']=self.get_kind(params['kind']) 
 
        # get target host
        self.__get_param(self.hostWidget, params, key='tgthost')      
        
        # get interval 
        params['interval']=self.ivspinBox.value()

        # get num of frames to send
        params['num']=self.numspinBox.value()

        self.logger.debug('params<%s>' %params)

        return  params


    def exec_guider_sim(self, params):
        ''' execute AgSim.py '''

        try:
            #cmd=os.path.join(os.environ['PYHOME'],'SOSS/GuiderInt', 'AgSim.py' )
            #args= "-a %(type)s  -b  %(binning)d -k %(kind)d --tgthost %(tgthost)s --interval %(interval)f --num %(num)d --loglevel=0"  %params
        # -a type, -b binning  --kind, --tgthost --interval --num
          
            #self.logger.debug('cmd<%s> args<%s>' %(cmd,args))
            #self.pid=subprocess.Popen([cmd, '%s' %args]).pid

            cmd=os.path.join(os.environ['SOSSHOME'],'bin', 'AgSim_ag' )
            #args= " %(kind)d  %(binning)d %(tgthost)s  %(num)d  %(interval)d "  %params
            args=" %(kind)s  %(binning)s  %(tgthost)s  %(num)s  %(interval)s \n" %(params)
            
            cmd_line=cmd+args
            args=cmd_line.split()
            self.logger.debug('args<%s>' %(args))

            #self.pid=subprocess.Popen([cmd, '1', '1', 'g2s4', '10', '1'])

            self.pid=subprocess.Popen([cmd, str(params['kind']), str(params['binning']),params['tgthost'], str(params['num']), str(params['interval']) ] )
        except OSError,e:
            self.logger.error('cmd exec error <%s>' %e)

    def stop_guidersim(self):
 
        try:
            self.pid.terminate()
        except OSError,e:
            self.logger.error('terminating cmd error <%s>' %e)


    def start_guidersim(self):
        self.logger.debug('start sending frames')
        
        params=self.get_params()
       
        if not None in params.values():
            self.exec_guider_sim(params)



def main(options, args):

    import signal

    # catch keyboard interruption
    signal.signal(signal.SIGINT, signal.SIG_DFL)


    logname = 'guider_sim'
    logger = ssdlog.make_logger(logname, options)

    logger.info('guider sim starting ...')


    try:
        app = QApplication(sys.argv)
        gs = GuiderSim(logger)
        gs.show()
        app.exec_()
    except KeyboardInterrupt:
        print 'keyboard interrupting ...'
        app.shutdown()

if __name__=="__main__":

    
    from optparse import OptionParser

    usage = "usage: %prog [options] [file] ..."
    optprs = OptionParser(usage=usage, version=('%prog'))

    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
      
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    #if len(args) > 0:
    #    optprs.error("incorrect number of arguments")
       
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
    



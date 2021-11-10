#!/usr/bin/env python

from __future__ import division
import sys
import math

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from TVFlowlayout import FlowLayout

import time

version = '20091105.0'
TVG_DEFAULTSIZE = (430,135)

def averageColor(color1, color2, weight1=1, weight2=1):
    divisor = weight1 + weight2
    averageR = (weight1*color1.red() + weight2*color2.red())/divisor
    averageG = (weight1*color1.green() + weight2*color2.green())/divisor
    averageB = (weight1*color1.blue() + weight2*color2.blue())/divisor
    return QColor(averageR, averageG, averageB)

class CoolBox(QWidget):
    def __init__(self, parent=None, size=TVG_DEFAULTSIZE):
        super(CoolBox,self).__init__(parent)
        self.backgroundColor = QColor(1,2,3)

        self.setLayout(QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setMargin(0)

        self.info = CoolInfo(self)
        self.layout().addWidget(self.info)

        sideMargins = QWidget(self)
        sideMargins.setSizePolicy(QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding))
        self.layout().addWidget(sideMargins)
        # 3 pixels at bottom
        self.layout().addSpacing(3)

        sideMarginsLayout = QHBoxLayout()
        sideMargins.setLayout(sideMarginsLayout)
        sideMarginsLayout.setSpacing(0)
        sideMarginsLayout.setMargin(0)
        # 3 pixels on the left
        sideMarginsLayout.addSpacing(3)
        
        # gridWidget contains timeValueGraph & ruler(s)
        gridWidget = self.gridWidget = QWidget(sideMargins)
        sideMarginsLayout.addWidget(gridWidget)
        # 3 pixels on the right
        sideMarginsLayout.addSpacing(3)
        
        gridWidget.setLayout(QGridLayout())
        gridLayout = gridWidget.layout()
        gridLayout.setSpacing(0)
        gridLayout.setMargin(0)
        #gridWidget.setColumnStretch(0,0)
        #gridWidget.setColumnStretch(1,1)
        gridLayout.addWidget(CoolRule(gridWidget, orientation=1),0,0)
        gridLayout.addWidget(CoolRule(gridWidget),1,1)
        
        gridLayout.addWidget(DataView(gridWidget, size=QSize(size[0], size[1])), 0,1)


    def paintEvent(self, event):
        painter = QPainter(self)
        #painter.begin(self)

        painter.setPen(self.backgroundColor)
        painter.setBrush(self.backgroundColor)
        painter.drawRect(QRectF(0,0,self.size().width(), self.size().height()))
        
        geometry = self.geometry()
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(Qt.darkGray, 0, Qt.SolidLine))
        
        BOTTOM = geometry.height()-2
        RIGHT = geometry.width()-2
        painter.drawLine(1, 0, 1, BOTTOM)
        painter.drawLine(1, BOTTOM, RIGHT, BOTTOM)
        painter.drawLine(RIGHT, 0, RIGHT, BOTTOM)

        #painter.end()
        
class CoolInfo(QWidget):
    def __init__(self, parent=None):
        super(CoolInfo,self).__init__(parent)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred))

        flowLayout = FlowLayout(spacing=3)
        flowLayout.addWidget(QPushButton(self.tr("Wind Direction (Something)")))
        flowLayout.addWidget(QPushButton(self.tr("Short:1000.05")))
        flowLayout.addWidget(QPushButton(self.tr("Longer: 12347.0")))
        flowLayout.addWidget(QPushButton(self.tr("Different text: 99.75")))
        flowLayout.addWidget(QPushButton(self.tr("More text: 733.74")))
        flowLayout.addWidget(QPushButton(self.tr("Even longer button text: 123.456")))
        self.setLayout(flowLayout)

        
    def minimumSizeHint(self):
        return QSize(30,26)

    def paintEvent(self, event):
        painter = QPainter(self)
        #painter.begin(self)

        darkPanelColor = QColor('#a0a0a0')
        bgColor = self.parentWidget().backgroundColor

        darkAverageColor = averageColor(darkPanelColor, bgColor, weight2=5)
        painter.setBrush(darkAverageColor)
        painter.setPen(QPen(Qt.black, 0, Qt.NoPen))
        painter.drawRect(QRectF(2,0,self.geometry().width()-4,self.geometry().height()))

        #painter.end()

class CoolRule(QWidget):
    def __init__(self, parent=None, orientation=0):
        super(CoolRule,self).__init__(parent)
        if orientation == 0:
            # horizontal rule fixme this is not clear
            self.setSizePolicy(QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed))
        else:
            self.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Ignored))
        
    def minimumSizeHint(self):
        return QSize(44,24)

    def paintEvent(self, event):
        painter = QPainter(self)
        #painter.begin(self)

        ruleColor = QColor('#a0a0a0')

        painter.setBrush(ruleColor)
        painter.setPen(Qt.black)
        #painter.setPen(QPen(Qt.black, 1, Qt.NoPen))
        painter.drawRect(QRectF(0,0,self.geometry().width()-1,self.geometry().height()-1))

        #painter.end()

        
class DataView(QWidget):
    def __init__(self, parent=None, size=QSize(30,30)):
        super(DataView,self).__init__(parent)
        self.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        self._minSize = size
        
    def minimumSizeHint(self):
        return self._minSize

    def paintEvent(self, event):
        painter = QPainter(self)
        color = QColor('#70b070')
        painter.setBrush(color)
        painter.setPen(Qt.black)
        painter.drawRect(QRectF(0,0,self.rect().width()-1,self.rect().height()-1))

#################################################################
### =================  main() starts here =======================
#################################################################
def main(options, args):

    app = QApplication(sys.argv)

    topWidget = QWidget()
    topWidget.setLayout(QVBoxLayout())
    topWidget.layout().setSpacing(0)
    topWidget.layout().setMargin(0)


    #widget = CoolBox(size=(350,100))
    widget = CoolBox()
    widget.backgroundColor = QColor(210,230,255)
    topWidget.layout().addWidget(widget)

    #widget = CoolBox(size=(350,75))
    widget = CoolBox()
    widget.backgroundColor = QColor(252,210,200)
    topWidget.layout().addWidget(widget)

    topWidget.resize(topWidget.layout().closestAcceptableSize(topWidget, QSize(370,800)))
    topWidget.setMinimumSize(topWidget.size())
    
    topWidget.setWindowTitle('CoolBox test')
    topWidget.show()
    
    appExecReturn = app.exec_()
    sys.exit(appExecReturn)

if __name__ == '__main__':
    
    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options] command [args]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    
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

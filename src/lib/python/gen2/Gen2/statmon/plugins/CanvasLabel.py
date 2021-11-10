from PyQt4 import QtCore, QtGui, Qt
from error import ERROR
    
class Canvas(QtGui.QLabel):
    ''' draw a label on a canvas  '''
    def __init__(self, parent=None, font='UnDotum', fs=27, weight='normal', \
                 frame=False, linewidth=1, midlinewidth=2, \
                 width=350, height=75, fg='green', bg='white', \
                 align='center', logger=None):
        super(Canvas, self).__init__(parent)

        self.warn='orange'
        self.alarm='red'
        self.normal='green'
        self.fg=fg
        self.bg=bg
        self.width=width
        self.height=height
        self.logger=logger

        self.font = QtGui.QFont(font, fs) 
        fontweight={'normal': QtGui.QFont.Normal, 'bold':QtGui.QFont.Bold}
        self.font.setWeight(fontweight[weight])
        self.setText('Initializing')
        align = {'center': QtCore.Qt.AlignCenter, \
                 'left': QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, \
                 'right': QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter, 
                 'vcenter': QtCore.Qt.AlignVCenter}[align]
        self.setAlignment(align)
        self.setFont(self.font)

        if frame:
            #self.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Raised)
            self.setFrameStyle(QtGui.QFrame.Box | QtGui.QFrame.Raised) 
            self.setLineWidth(linewidth)
            self.setMidLineWidth(midlinewidth)
        self.setStyleSheet("QLabel {color :%s; background-color:%s }" %(self.fg, self.bg))

    def minimumSizeHint(self):
        return QtCore.QSize(self.width, self.height)

    def sizeHint(self):
        return QtCore.QSize(self.width, self.height)


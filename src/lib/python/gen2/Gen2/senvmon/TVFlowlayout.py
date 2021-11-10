#!/usr/bin/env python

"""was PyQt4 port of the layouts/flowlayout example from Qt v4.x"""
# but inelegantly munged for sammy's labelContainer layout needs

import sys
from PyQt4 import QtCore, QtGui


class Window(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        flowLayout = FlowLayout(spacing=3)
        flowLayout.addWidget(QtGui.QPushButton(self.tr("Short")))
        flowLayout.addWidget(QtGui.QPushButton(self.tr("Longer")))
        flowLayout.addWidget(QtGui.QPushButton(self.tr("Different text")))
        flowLayout.addWidget(QtGui.QPushButton(self.tr("More text")))
        flowLayout.addWidget(QtGui.QPushButton(self.tr("Even longer button text")))
        self.setLayout(flowLayout)

        self.setWindowTitle(self.tr("Flow Layout2"))


class FlowLayout(QtGui.QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        QtGui.QLayout.__init__(self, parent)

        if parent is not None:
            self.setMargin(margin)
        self.setSpacing(spacing)

        self.itemList = []

    def setSpacing(self, spacing):
        self._horizontalSpacing = spacing
        self._verticalSpacing = spacing
        
    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]

    def takeAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)

    def expandingDirections(self):
        return QtCore.Qt.Orientations(QtCore.Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.doLayout(QtCore.QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        QtGui.QLayout.setGeometry(self, rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()

        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        size += QtCore.QSize(2 * self.margin(), 2 * self.margin())
        return size

    # This feels inelegant but my elegant code brain is out to lunch today
    def _layOutLine(self, x, y, width, lineNumber, lineItems):
        if len(lineItems) == 0:
            return
        startIndex = 0
        # The 'title' lable on the first line gets special handling
        if lineNumber == 0:
            item = lineItems[0]
            item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))

            increment = item.sizeHint().width() + self._horizontalSpacing
            x += increment
            width -= increment
            startIndex = 1

        count = len(lineItems)
        for index in range(startIndex, count):
            width -= lineItems[index].sizeHint().width()
        divisor = count - startIndex + 1
        itemSpacing = width / divisor
        for index in range(startIndex, count):
            x += itemSpacing
            item = lineItems[index]
            item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))
            x += item.sizeHint().width()
    
    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0
        lineItems = []
        lineNumber = 0

        for item in self.itemList:
            nextX = x + item.sizeHint().width() + self._horizontalSpacing
            if nextX - self._horizontalSpacing > rect.right() and lineHeight > 0:
                # item will go onto the next line
                if not testOnly:
                    # Since the current line is complete, let's nicely space the items
                    self._layOutLine(rect.x(), y, rect.width(), lineNumber, lineItems)
                        
                lineItems = []
                lineNumber += 1
                x = rect.x()
                y += lineHeight + self._verticalSpacing
                nextX = x + item.sizeHint().width() + self._horizontalSpacing
                lineHeight = 0

            lineItems.append(item)

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        if not testOnly:
            self._layOutLine(rect.x(), y, rect.width(), lineNumber, lineItems)

        return y + lineHeight - rect.y()


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    mainWin = Window()
    mainWin.show()
    sys.exit(app.exec_())

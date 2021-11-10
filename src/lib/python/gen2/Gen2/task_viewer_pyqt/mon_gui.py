# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mon.ui'
#
# Created: Wed Apr 15 09:51:14 2009
#      by: PyQt4 UI code generator 4.3.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(QtCore.QSize(QtCore.QRect(0,0,702,549).size()).expandedTo(Form.minimumSizeHint()))

        self.treeWidget = QtGui.QTreeWidget(Form)
        self.treeWidget.setGeometry(QtCore.QRect(40,20,611,451))

        font = QtGui.QFont()
        font.setPointSize(9)
        self.treeWidget.setFont(font)
        self.treeWidget.setFrameShape(QtGui.QFrame.VLine)
        self.treeWidget.setObjectName("treeWidget")

        self.pushButtonClose = QtGui.QPushButton(Form)
        self.pushButtonClose.setGeometry(QtCore.QRect(570,500,80,28))
        self.pushButtonClose.setObjectName("pushButtonClose")

        self.pushButtonClear = QtGui.QPushButton(Form)
        self.pushButtonClear.setGeometry(QtCore.QRect(450,500,80,28))
        self.pushButtonClear.setObjectName("pushButtonClear")

        self.retranslateUi(Form)
        QtCore.QObject.connect(self.pushButtonClose,QtCore.SIGNAL("clicked()"),Form.close)
        QtCore.QObject.connect(self.pushButtonClear,QtCore.SIGNAL("clicked()"),self.treeWidget.clear)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtGui.QApplication.translate("Form", "Task Monitor", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(0,QtGui.QApplication.translate("Form", "task", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(1,QtGui.QApplication.translate("Form", "status", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(2,QtGui.QApplication.translate("Form", "start time", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(3,QtGui.QApplication.translate("Form", "end time", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButtonClose.setText(QtGui.QApplication.translate("Form", "close", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButtonClear.setText(QtGui.QApplication.translate("Form", "clear all", None, QtGui.QApplication.UnicodeUTF8))


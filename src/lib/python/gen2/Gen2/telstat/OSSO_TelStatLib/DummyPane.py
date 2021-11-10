# DummyPane.py -- Bruce Bon -- 2003-12-02 16:47

# Dummy pane to be used for any panes that are TBD

######################################################################
################   import needed modules   ###########################
######################################################################

import Tkinter
from Tkconstants import *

from TelStat_cfg import *
from StatIO import *

######################################################################
################   declare classes for the panes   ###################
######################################################################

# Dummy Pane class
class DummyPane(Tkinter.Button,StatPaneBase):
    parent = 0

    def geomCB(self):
	"""Callback for to print geometry."""
	#? TelStatLog( DummyInfoBase, 
	#? 	    `self["text"], " :	", self.winfo_geometry()`, True )
	#? TelStatLog( DummyInfoBase, 
	#? 	    "Parent :	%s" % self.parent.geometry(), True)

    def __init__(self,parent,labelStr,width=-1,height=-1):
	"""Dummy Pane constructor."""
	Tkinter.Button.__init__(self, parent,		\
	    borderwidth=paneBorderWidth, relief=paneBorderRelief)
	StatPaneBase.__init__(self, (), 'DummyPane' )
	self.parent = parent
	self["command"] = self.geomCB
	self["bg"] = "CadetBlue"
	self["font"] = fontBigBold
	self["text"] = labelStr
	if  width > 10:
	    self["width"] = width
	if  height > 10:
	    self["height"] = height
#?	print "\n", self, " options:\n", self.config()	# debug

    def resize( self, paneWidth=0, paneHeight=0 ):
	"""Resize this pane."""
	if  paneWidth > 10:
	    self["width"] = paneWidth
	if  paneHeight > 10:
	    self["height"] = paneHeight
	self.printGeom()

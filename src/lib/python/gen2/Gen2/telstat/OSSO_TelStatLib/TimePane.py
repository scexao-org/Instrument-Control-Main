#! /usr/local/bin/python

from Tkinter import *
from StatIO import *
from DispType import *
from TelStat_cfg import *
import Pmw
import TimeLabel
import HALabel
import Util
import time
import os

class TimePane(Frame, StatPaneBase):
    def __init__(self, parent, pfgcolor=TIMEPANEFOREGROUND, pbgcolor=TIMEPANEBACKGROUND,
                 pformat=TIMEPANEFORMAT, pfont=TIMEPANEFONT):
        Frame.__init__(self, parent,
                       borderwidth=paneBorderWidth, relief=paneBorderRelief)
        StatPaneBase.__init__(self, ('TSCS.ALPHA','TELSTAT.UNIXTIME'), 'TimePane')
        self.configure(bg=pbgcolor)

        parent.update_idletasks()  # must be done to assure that geometry != 1x1+0+0
        colminwidth =(int(parent.winfo_width()/4) - 1)
        self.columnconfigure(0,minsize=colminwidth+60)
        self.columnconfigure(1,minsize=colminwidth+60)
        self.columnconfigure(2,minsize=colminwidth-60)
        self.columnconfigure(3,minsize=colminwidth-60)

        self.format = pformat
        
        self.UTLabel = TimeLabel.TimeLabel(self, ifgcolor=pfgcolor[0], ibgcolor=pbgcolor, ifont=pfont[0])
        self.UTLabel.grid(row=0,column=0, sticky=N+E+S+W)

        os.environ['TZ'] = "US/Hawaii"
        time.tzset()
        self.HTLabel = TimeLabel.TimeLabel(self, ifgcolor=pfgcolor[1], ibgcolor=pbgcolor, ifont=pfont[1])
        self.HTLabel.grid(row=0,column=1, sticky=N+E+S+W)

        self.LSTLabel = TimeLabel.TimeLabel(self, ifgcolor=pfgcolor[2], ibgcolor=pbgcolor, ifont=pfont[2])
        self.LSTLabel.grid(row=0,column=2, sticky=N+E+S+W)

        self.HALabel = HALabel.HALabel(self, ifgcolor=pfgcolor[3], ibgcolor=pbgcolor, ifont=pfont[3])
        self.HALabel.setTarget(Util.sidereal()[3:6])
        self.HALabel.grid(row=0,column=3, sticky=N+E+S+W)

    def update(self, dict):

        t = dict['TELSTAT.UNIXTIME']
        if  t.value() == None:
            self.UTLabel.update('<No Data>')
            self.HTLabel.update('<No Data>')
            self.LSTLabel.update('<No Data>')
            # self.HALabel.update('<No Data>')  # leave HA alone!
        else:
            self.UTLabel.update(t.format_UTstrftime(self.format[0]))
            self.HTLabel.update(t.format_HSTstrftime(self.format[1]))
            self.LSTLabel.update(t.format_LSTstrftime(self.format[2]))
            self.HALabel.update(t.value_LSTtuple())
            
    def refresh(self, dict):
        alpha = dict['TSCS.ALPHA'].value_HrSec()
        if  alpha != None:      # else leave at previous value
            self.HALabel.setTarget(time.gmtime(alpha)[3:6])
        self.update(dict)

    def resize(self):
        pass

    def rePack(self):
        """First resize, then re-place this pane.
           This should ONLY be called if this pane is used in a top-level
              geometry pane, NOT if it is a page in a Notebook."""
        self.resize()
        self.pack( anchor=NW)

    def tick(self):
        self.update()
        self.after(1000, self.tick)



#!/usr/bin/env python

import sys
import matplotlib
import numpy as np
import pyfits as pf
import threading
import time
import pdb
import os, sys, socket, time, numpy, commands, binascii, datetime, math
import errno
import commands
import re
import pickle
from lockfile import FileLock
import gtk
import pygtk
pygtk.require('2.0')
import pango
import mmap
import struct
import glob
import matplotlib.pyplot as plt

matplotlib.use('GTK')

from matplotlib.backends.backend_gtk import FigureCanvasGTK
from matplotlib.backends.backend_gtkagg \
import NavigationToolbar2GTKAgg as NavigationToolbar

from matplotlib.figure import Figure 
from matplotlib.axes import Subplot 
from matplotlib.patches import Circle
import matplotlib.cm as cm
import array
from math import *

from scipy.signal import medfilt2d as medfilt
from scipy.misc import imsave
from random import choice

gtk.gdk.threads_init() # needed to allow multi-threads

import GtkMain         # Eric's object to make the GUI thread safe.


(plt.rcParams)['image.origin'] = 'lower'      # plot origin in lower left corner
(plt.rcParams)['image.cmap']   = 'gray'       # just like good old IDL (image display)
plt.ion() 

# ------------------------------------------------------------------
# ------------------------------------------------------------------

# The current lowfs frame in the Shared Memory

fname1 = "/tmp/aol1_DMmode_cmd1.im.shm"  # residuals
fname2 = "/tmp/aol1_DMmode_cmd.im.shm"   # to be applied

fd1 = os.open(fname1, os.O_RDONLY)
buf1 = mmap.mmap(fd1, 0, mmap.MAP_SHARED, mmap.PROT_READ)

fd2 = os.open(fname2, os.O_RDONLY)
buf2 = mmap.mmap(fd2, 0, mmap.MAP_SHARED, mmap.PROT_READ)

(xsize, ysize, z) = struct.unpack('lll', buf1[88:112])

class myGUI:
    # ------------------------------
    nbv = 100 # number of values to be plotted
    sig_x = np.empty(0)
    sig_y = np.empty(0) # instant values read from shared memory
    sig_f = np.empty(0)
    sig_a1= np.empty(0)
    sig_a2= np.empty(0)
    ave_x = np.empty(0)#zeros(nbv)
    ave_y = np.empty(0)#zeros(nbv) # averaged values
    ave_f = np.empty(0)
    ave_a1= np.empty(0)
    ave_a2= np.empty(0)

    live_plot = False

    # -------------------------------
    def pgquit(self, widget):
        self.live_plot = False
        print("The program has ended normally.")
        mygtk.gui_quit()

    # -------------------------------
    def __init__(self,):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("destroy", self.pgquit)
        self.window.set_title("Plot window")
        self.window.set_border_width(5)
        self.window.set_default_size(800,600)

        self.table = gtk.Table(10,4, True)
        self.window.add(self.table)
        self.table.show()

        # ==========================================
        self.figure = Figure(figsize=(6,4), dpi=72)
        self.axis   = self.figure.add_subplot(111)
        self.axis.set_title('tip-tilt log plotter for LLOWFS')
        self.axis.set_xlabel('Iteration')
        self.axis.set_ylabel('Tip-Tilt residual (micron)')
        self.axis.set_ylim([-80.0, 80.0])
        self.axis.set_ylim([-0.35, 0.35])
        self.axis.grid(True)
        x = np.arange(100)
        self.axis.plot(x)
        self.axis.plot(x)
        self.canvas = FigureCanvasGTK(self.figure)
        self.canvas.show()
        self.table.attach(self.canvas, 0, 4, 0,9)
        # ==========================================


        butt = gtk.Button("START")
        butt.connect("clicked", self.b_clicked1)
        self.table.attach(butt, 0, 1, 9, 10)
        butt.show()

        self.butt = gtk.Button("STOP")
        self.butt.connect("clicked", self.b_clicked2)        
        self.table.attach(self.butt, 1, 2, 9, 10)
        self.butt.show()

        #self.lbl = gtk.Label("ExpTime:")
        #self.butt.connect("clicked", self.b_clicked3)        
        #self.table.attach(self.lbl, 2, 3, 9, 10)
        #self.lbl.show()

       # self.lbl_tint = gtk.Label("")
       # self.table.attach(self.lbl_tint, 3, 4, 9, 10)
       # self.lbl_tint.show()

        # ----------------
        self.window.show()

    def b_clicked1(self, widget):
        self.live_plot = True
        #plot_loop(self)
        t = threading.Thread(target=plot_loop, args=(self,))
        t.start()
       
    def b_clicked2(self, widget):
        self.live_plot = False
    
    

# ------------------------------------------------------------------
# ------------------------------------------------------------------



def plot_loop(GUI):
 
    bins = 10 # bin size for running average
    rate = 10 # plot refreshes every xx times
    loop_delay = 0.01 # delay to ease CPU
    
    cnt =0
     
    xx = 0
    while GUI.live_plot:

        xx += 0.1

        # tip-tilt residuals at lowfs
        myarr = np.fromstring(buf1[200:200+4*xsize],dtype=np.float32) 

        tip   = myarr[0]
        tilt  = myarr[1]
        foc   = myarr[2]

        #print myarr[0]
       # tip_low, = struct.unpack('d', buf[800:808])
       # tilt_low, = struct.unpack('d', buf[808:816])
    
        # sin wave generator with random noise

       # GUI.sig_x = np.append(GUI.sig_x, 2*np.cos(xx) + 0.5*np.random.randn())
       # GUI.sig_y = np.append(GUI.sig_y, 3*np.sin(xx) + 0.5*np.random.randn())
        
        GUI.sig_x = np.append(GUI.sig_x, tip)
        GUI.sig_y = np.append(GUI.sig_y, tilt)
        GUI.sig_f = np.append(GUI.sig_f, foc)

     
        # keep the log plot < nbv values
        if np.size(GUI.sig_x) > GUI.nbv:
            GUI.sig_x = np.delete(GUI.sig_x, 0)
            GUI.sig_y = np.delete(GUI.sig_y, 0)
            GUI.sig_f = np.delete(GUI.sig_f, 0)


        # build up the average plot
        #GUI.ave_x = np.append(GUI.ave_x, np.mean(GUI.sig_x[-bins:]))
        #GUI.ave_y = np.append(GUI.ave_y, np.mean(GUI.sig_y[-bins:]))
        
        GUI.ave_x = np.append(GUI.ave_x, np.mean(GUI.sig_x[-bins:]))
        GUI.ave_y = np.append(GUI.ave_y, np.mean(GUI.sig_y[-bins:]))
        GUI.ave_f = np.append(GUI.ave_f, np.mean(GUI.sig_f[-bins:]))
         
        if np.size(GUI.ave_x) > GUI.nbv:
            GUI.ave_x = np.delete(GUI.ave_x, 0)
            GUI.ave_y = np.delete(GUI.ave_y, 0)
            GUI.ave_f = np.delete(GUI.ave_f, 0)
 

        cnt += 1
        if cnt > rate:
            cnt = 0
            mygtk.gui_call(updt_plot, GUI)
   
        time.sleep(loop_delay)
    exit(0)

def updt_plot(GUI):
    GUI.axis.lines.pop(0)
    GUI.axis.lines.pop(0)

    #GUI.axis.lines.pop(0)
    #GUI.axis.lines.pop(0)
    #GUI.axis.lines.pop(0)
    GUI.axis.plot(GUI.ave_x, 'b',label='tip')
    GUI.axis.plot(GUI.ave_y, 'r', label='tilt')
    GUI.axis.legend(loc=0)

    #GUI.axis.plot(GUI.ave_f, 'o', label='focus')
    #GUI.axis.lines.pop(0)

    #GUI.axis.plot(GUI.ave_a1, 'g', label='45a')
    #GUI.axis.plot(GUI.ave_a2, 'y', label='90a')
    
    GUI.canvas = FigureCanvasGTK(GUI.figure)
    GUI.canvas.show()
    GUI.table.attach(GUI.canvas, 0, 4, 0, 9)


# ------------------------------------------------------------------
# ------------------------------------------------------------------

# ------------------------------------------------------------------
if __name__ == "__main__":
    ev_quit = threading.Event()
    mygtk = GtkMain.GtkMain(ev_quit=ev_quit)

    GUI = myGUI()

    try:
        mygtk.mainloop()
    except KeyboardInterrupt:
        mygtk.gui_quit()



#-----------------------------------------------------------------------------
# Tip Tilt residual real time telemetry for LLOWFS
# Created: 6 May 2014
# Author : Frantz + Garima




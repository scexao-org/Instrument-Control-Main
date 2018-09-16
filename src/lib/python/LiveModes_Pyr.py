#!/usr/bin/env python

import pygame, sys
from pygame.locals import *
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import pdb
import mmap
import struct
import os, select
import array
import Image
import time
import datetime
import pyfits as pf
import threading
import readline
import numpy.fft as nfft

home = os.getenv('HOME')
sys.path.append(home+'/src/lib/python/')
from spkl_tools   import *
from img_tools    import *
from scexao_shm   import shm

plt.ion()



utcnow = datetime.datetime.utcnow

# ------------------------------------------------------------------
#                       global variables
# ------------------------------------------------------------------



# ------------------------------------------------------------------
#                access to shared memory structures
# ------------------------------------------------------------------
res = shm('/tmp/aol2_DMmode_cmd1.im.shm', False) # read mode residuals
com = shm('/tmp/aol2_DMmode_cmd.im.shm', False)  # read mode commands


class myGUI:
    # --------------------------------------------------------------

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
        self.axis   = self.figure.add_subplot(311)
        self.axis.set_title('tip-tilt log plotter for LLOWFS')
        self.axis.set_xlabel('Iteration')
        self.axis.set_ylabel('Tip-Tilt residual (micron)')
        # self.axis.set_ylim([-0.35, 0.35])
        self.axis.grid(True)
        # x = np.arange(100)
        # self.axis.plot(x)
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
        # ----------------
        self.window.show()

    def b_clicked1(self, widget):
        self.live_plot = True
        t = threading.Thread(target=plot_loop, args=(self,))
        t.start()
       
    def b_clicked2(self, widget):
        self.live_plot = False
    
# ------------------------------------------------------------------
# ------------------------------------------------------------------

    def plot_loop(GUI):
        
        bins = 1024 # bin size for the buffer
        rate = 10 # period of refreshment [s]
        loop_delay = 0.01 # delay to ease CPU
        
        n_modes = 5
        n_start = 0
        meta_res = res.read_meta_data(False)
        dim_res = meta_res.size
        n_modes_t = dim_res[0]
        if n_modes > n_modes_t:
            n_modes = n_modes_t
            n_start = 0

        modes = [[None for x in range(n_modes)] for y in range(bins)]

        cnt = 0
        
        xx = 0
        while GUI.live_plot:

            xx += 0.1
            
            for x in xrange(1, bins):# tip-tilt residuals at lowfs
                modes_temp = res.get_data(False, True)
                modes[::x] = modes_temp[::1]
            
            
                
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
# Mode residual telemetry for PyWFS
# Created: 3 Oct 2014
# Author : Julien

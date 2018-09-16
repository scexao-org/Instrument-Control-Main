
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
from numpy.linalg import solve


home = os.getenv('HOME')
sys.path.append(home+'/src/lib/python/')
from spkl_tools   import *
from img_tools    import *
from camera_tools import cam_cmd
from scexao_shm   import shm
import drive_piezo


plt.ion()

dev  = "/dev/serial/by-id/"
dev += "usb-FTDI_FT232R_USB_UART_AH01JW35-if00-port0"

Piezo_volt=drive_piezo.PIEZO(dev)      # connecting to Piezo actuators

utcnow = datetime.datetime.utcnow

# ------------------------------------------------------------------
#                       global variables
# ------------------------------------------------------------------

xc = 72.4
yc = 72.7

ampl=""   
tint=""
nbstep=""
phase =0.0
choice =0


# Subclass the the threading.Thread class so that we can run the
# add_DM_circ function in its own thread.

class myThread (threading.Thread):
    def __init__(self, ev_quit, ampl, tint, nbstep):
        threading.Thread.__init__(self)
        self.ev_quit = ev_quit
        self.ampl = ampl
        self.tint = tint
        self.nbstep = nbstep
    def run(self):
        # Stay in loop until ev_quit is set
        while not self.ev_quit.isSet():
            # ------Function that writes back to shared memory-------
            with lock:
                ampl = self.ampl
                tint = self.tint
                nbstep = self.nbstep
            Dichroic_circ(ampl,tint,nbstep)
 
        clear_voltage() 
        print("Dichroic circle ended normally.")

def menu():
        print("\n Main Menu")
        print("==========\n")
        print("Key a: Change amplitude")
        print("Key t: Change integration time")
        print("Key n: Change number of points")
        print("Key q: Turn off the DM circle and put channel 7 to zero")

def shutdown(thread):
    thread.ev_quit.set()


#--------------Functions that read the shared memory array, modify the array 
# ---as per user input and writes it back to the shared memory

def Dichroic_circ(ampl, tint, nbstep):
    ''' ----------------------------------------
    calculate tip tilt phaseramp DM displacement map:
    - ampl    :  amplitude in um
    - tint   :  time interval in us
    - NBstep :  set number of points in a circle
    ---------------------------------------- '''
    global phase
    global loop_end

    phase = phase + 2*np.pi / nbstep
    if phase > (2*np.pi):
        phase = phase - 2*np.pi
    ampx = ampl * np.cos(phase) * xc 
    ampy = ampl * np.sin(phase) * yc
    Piezo_volt.write_piezox(ampx)
    Piezo_volt.write_piezoy(ampy)

    return()

def clear_voltage():
    Piezo_volt.write_piezox(72.4)
    #time.sleep(delay)
    Piezo_volt.write_piezoy(72.7)
    #time.sleep(delay)
    exit()

#------------------------------------------------------------------------------


# User interaction via Command prompt------------------

print("\nNOTE : This is a program to apply a circle of tip tilt to the dichroic\n")
#chn = raw_input("Enter DM channel number (Channel 5, 6 and 7 are available) : ")
#chn = np.float(chn)
#print (" chn :", chn) 
print("\nMain Menu\n")
print("==========\n")
print("Key a: Change amplitude")
print("Key t: Change integration time")
print("Key n: Change number of points")
print("Key q: Turn off the circle and move dichroic to the nominal position")
print("\n")


# Enter initial values of variables which modify the current array from shared memory 

ampl = raw_input("Enter amplitude (in um) : ")
ampl = np.float(ampl)
print " ampl :", ampl

tint = raw_input("Enter Integration time (in us) : ")
tint = np.float(tint)
print "tint :", tint

nbstep = raw_input("Enter number of steps : ")
nbstep = np.float(nbstep)
print "NBstep :", nbstep

print("\nStatus:")
print("---------\n")
print "Amplitude (um): ", ampl
print "NB step: ", nbstep 
print "tint: ", tint 
print "Requested uptdate frequ KHz: ", 0.001/(1.0e-6*tint)
print "Requested circle frequ Hz: ", 1.0/nbstep/(1.0e-6*tint)

# Create an Event, RLock, and Thread objects for use in running the
# add_DM_circ in a thread. ev_quit is used to send a signal to exit
# the loop that is running add_DM_circ. lock is used to synchronize
# access to the ampl, tint, and nbstep values.

ev_quit = threading.Event()
lock = threading.RLock()
thread1 = myThread(ev_quit, ampl, tint, nbstep)

# Start the thread
thread1.start()

# Loop to prompt user for input. The user can exit the loop by entering "q" or
# ctrl-C.
try:
    while True:
        menu()
        cmd = raw_input('? ')

        if cmd == 'a':
            ampl_input = raw_input("Enter amplitude (in um):")
            with lock:
                thread1.ampl = np.float(ampl_input)
                print " ampl :", thread1.ampl

        elif cmd == 't':
            tint_input = raw_input("Enter Integration time (in us):")
            with lock:
                thread1.tint = np.float(tint_input)
                print " tint :", thread1.tint
                print("\nStatus:")
                print("------------\n")
                print "Amplitude (um): ", ampl
                print "NB step: ", nbstep
                print "tint: ", thread1.tint 
                print "Requested uptdate frequ KHz: ", 0.001/(1.0e-6*thread1.tint)
                print "Requested circle frequ Hz: ", 1.0/nbstep/(1.0e-6*thread1.tint)

        elif cmd == 'n':
            nbstep_input = raw_input("Enter number of steps::")
            with lock:
                thread1.nbstep = np.float(nbstep_input)
                print" NBstep :", thread1.nbstep
                print("\nStatus:")
                print("------------\n")
                print "Amplitude (um): ", ampl
                print "NB step: ", thread1.nbstep
                print "tint: ", tint 
                print "Requested uptdate frequ KHz: ", 0.001/(1.0e-6*tint)
                print "Requested circle frequ Hz: ", 1.0/thread1.nbstep/(1.0e-6*tint)

        elif cmd == 'q':
            clear_voltage() 
            shutdown(thread1)
            print("Dichroic circle ended normally.")
            break

except KeyboardInterrupt:
    shutdown(thread1)

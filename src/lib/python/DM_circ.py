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

home = os.getenv('HOME')
sys.path.append(home+'/src/lib/python/')
from spkl_tools   import *
from img_tools    import *
from camera_tools import cam_cmd
from scexao_shm   import shm
import wheel

from numpy.linalg import solve

plt.ion()



utcnow = datetime.datetime.utcnow

# ------------------------------------------------------------------
#                       global variables
# ------------------------------------------------------------------
nch      = 8               # number of channels
dms      = 50              # dm diameter (in actuator)

#xc,yc    = np.meshgrid(np.arange(dms)-dms/2, # dm coordinates 
                      # np.arange(dms)-dms/2) # 

xc,yc    = np.meshgrid((np.arange(dms)-dms/2.0)/dms/2.0, # dm coordinates 
                       (np.arange(dms)-dms/2.0)/dms/2.0) #
ampl=""   
tint=""
nbstep=""
phase =0.0
choice =0

'''
xc=np.zeros(dms*dms, dtype=float)
yc=np.zeros(dms*dms, dtype=float)

for i in range(int(dms)):
    for j in range(int(dms)):
        x = 1.0*i-24.5;
	y = 1.0*j-24.5;
	x /= 25.0;
	y /= 25.0;
	xc[j*50+i] = x;
	yc[j*50+i] = y;
      
'''

# Subclass the the threading.Thread class so that we can run the
# add_DM_circ function in its own thread.

class myThread (threading.Thread):
    def __init__(self, ev_quit, ampl, tint, nbstep, chn, disp7, disp, volt):
        threading.Thread.__init__(self)
        self.ev_quit = ev_quit
        self.ampl = ampl
        self.tint = tint
        self.nbstep = nbstep
        self.chn = chn
        self.disp7 = disp7
        self.disp = disp
        self.volt = volt
    def run(self):
        # Stay in loop until ev_quit is set
        while not self.ev_quit.isSet():
            # ------Function that writes back to shared memory-------
            with lock:
                ampl = self.ampl
                tint = self.tint
                nbstep = self.nbstep
                chn = self.chn
            add_DM_circ(ampl,tint,nbstep,chn)
 
        clear_channel(chn) 
        exec "disp%d.close()" % (self.chn,)
        self.disp.close()
        self.volt.close()  
        print("DM circle ended normally.")

def menu():
        print("\n Main Menu")
        print("==========\n")
        print("Key a: Change amplitude")
        print("Key t: Change integration time")
        print("Key n: Change number of points")
        print("Key q: Turn off the DM circle and put channel 7 to zero")

def shutdown(thread):
    thread.ev_quit.set()

# ------------------------------------------------------------------
#                access to shared memory structures
# ------------------------------------------------------------------

disp7  = shm('/tmp/dmdisp7.im.shm', False)  # read channel 7
disp   = shm('/tmp/dmdisp.im.shm', False)
volt   = shm('/tmp/dmvolt.im.shm', False)

#--------------Functions that read the shared memory array, modify the array 
# ---as per user input and writes it back to the shared memory

def DM_circ(ampl, tint, nbstep):
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
    circ = ampl * np.cos(phase) * xc +  ampl * np.sin(phase) * yc
    return(circ)
    
def add_DM_circ(ampl,tint,nbstep, chn):
    ''' -----------------------------------------
    adds a circle to the DM channel "chn"
    ----------------------------------------- '''
    dispm = DM_circ(ampl,tint, nbstep)
    add_DM_disp(dispm, chn)

def add_DM_disp(dispm, chn):
    ''' -----------------------------------------
    adds a displ map to the DM channel "chn"
    ----------------------------------------- '''
    map0 = get_DM_disp(chn)
    disp_2_DM(dispm+map0, chn)

def get_DM_disp(chn):
    exec "map0 = disp%d.get_data(False, True)" % (chn,)
    return(map0)

def disp_2_DM(dispm, chn):
    exec "disp%d.set_data0(dispm)" % (chn,)

def init_DM_channel(chn):
    exec "disp%d.set_data0(np.zeros((dms,dms)))" % (chn,)
    return(True)

def clear_channel(chn):
    init_DM_channel(chn)
    exit(0)

#------------------------------------------------------------------------------


# User interaction via Command prompt------------------

print("\nNOTE : This is a program to apply a circle of phaseramps on DM\n")
chn = raw_input("Enter DM channel number (Channel 5, 6 and 7 are available) : ")
chn = np.float(chn)
print (" chn :", chn) 
print("\nMain Menu\n")
print("==========\n")
print("Key a: Change amplitude")
print("Key t: Change integration time")
print("Key n: Change number of points")
print("Key q: Turn off the DM circle and put channel 7 to zero")
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
thread1 = myThread(ev_quit, ampl, tint, nbstep, chn, disp7, disp, volt)

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
            shutdown(thread1)
            clear_channel(chn) 
            self.disp.close()
            self.volt.close()
            print("DM circle ended normally.")
            break

except KeyboardInterrupt:
    shutdown(thread1)

## while True:


##     #----- Exit the program--------------------

##     os.system('cls' if os.name == 'nt' else 'clear')
##     print "Press Enter to stop DM circle!"
##     if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
##         line = raw_input()
##         exec "disp%d.close()" % (chn,)
##         disp7.close()
##         disp.close()
##         volt.close()    
##         exec "disp%d.set_data(np.zeros((dms,dms)))" % (chn,)
##         print("DM circle ended normally.")
##         break
##         sys.exit()

##     # ----- things I was trying to change the variable values while 'the while              loop' is running

##     if choice == 1:
##         ampl = raw_input("Enter amplitude (in um):")
##         ampl = np.float(ampl)
##         print (" ampl :", ampl) 

##     elif choice == 2:
##         tint = raw_input("Enter Integration time (in us):")
##         tint = np.float(tint)
##         print ("tint is :", tint)
        
##         print("\nStatus:")
##         print("***********\n")
##         print("Requested uptdate frequ KHz", 0.001/(1.0e-6*tint))
##         print("Requested circle frequ Hz", 1.0/nbstep/(1.0e-6*tint))
   

##     elif choice == 3:

##         nbstep = raw_input("Enter number of steps:")
##         nbstep = np.float(nbstep)
##         print ("NBstep :", nbstep)

##         print("\nStatus:")
##         print("***********\n")
##         print("Requested uptdate frequ KHz", 0.001/(1.0e-6*tint))
##         print("Requested circle frequ Hz", 1.0/nbstep/(1.0e-6*tint))

##     elif choice == 4:
##         # close shared memory access

##         exec "disp%d.close()" % (chn,)
##         disp.close()
##         volt.close()    
##         exec "disp%d.set_data(np.zeros((dms,dms)))" % (chn,)
##         print("DM circle ended normally.")
##         sys.exit()





#while True:

#t1=thread.start_new(add_DM_circ,(ampl,tint,nbstep,chn))




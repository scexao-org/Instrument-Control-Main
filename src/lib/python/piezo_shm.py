#!/usr/bin/python
import sys
import numpy as np
import array
import Image
import time
import datetime
import pyfits as pf
import threading
import readline
import pygame
from pygame.locals import *
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import pdb
import mmap
import struct
import os, select

import drive_piezo

home = os.getenv('HOME')
sys.path.append(home+"/src/lib/python/")
from scexao_shm import shm

plt.ion()

dev  = "/dev/serial/by-id/"
dev += "usb-FTDI_FT232R_USB_UART_AH01JW35-if00-port0"

Piezo_volt=drive_piezo.PIEZO(dev)      # connecting to Piezo actuators
shm_volt = shm("/tmp/ppiezo.im.shm")   # create shared memory file for Piezo

fd  = os.open("/tmp/ppiezo.im.shm", os.O_RDWR)   # reading Piezo shared memory  
buf = mmap.mmap(fd, 0, mmap.MAP_SHARED)

delay = 0.004

# Reading and writing Piezo actuators
#-----------------------------------------

def read_piezo():
    
    x = Piezo_volt.read_piezox()
    y = Piezo_volt.read_piezoy()

    # splitting the string 

    #x = np.float(x[34:39])
    x = np.float(x[8:12])
    y = np.float(y[8:12])
    #z = np.float(z[8:12])

    volts = (np.array(([[x,y]]), dtype=np.float32)).reshape(2,1)
    return (volts)

def read_piezoxy():

    [x, y] = Piezo_volt.read_piezoxy()
    #x = np.float(x[8:12])
    #y = np.float(y[8:12])

    return (x,y)


def write_piezoxy(x,y):

    Piezo_volt.write_piezoxy(x,y)
    return (x,y)


def write_piezo(x, y):

    Piezo_volt.write_piezox(x)
    time.sleep(delay)
    Piezo_volt.write_piezoy(y)
    time.sleep(delay)

    xvolt = Piezo_volt.read_piezox()
    time.sleep(delay)
    yvolt = Piezo_volt.read_piezoy()
    time.sleep(delay)

    [xvolt,yvolt] = Piezo_volt.read_piezoxy()
    time.sleep(delay)


    # splitting the string 
    xvolt = xvolt[8:12]
    yvolt = yvolt[8:12]
    #zvolt = zvolt[8:12]

    #volts = (np.array(([[xvolt,yvolt,zvolt]]), dtype=np.float32)).reshape(3,1)
    return (xvolt, yvolt)


# Reading and writing Shared memory DS
#---------------------------------------

def read_shm():
    x = shm_volt.get_data()[0,0]
    y = shm_volt.get_data()[0,1]
    #z = shm_volt.get_data()[0,2]

    volts = (np.array(([[x,y]]), dtype=np.float32)).reshape(2,1)
    return (x, y)

def write_shm(x,y):

    exec "shm_volt.set_data(x,y)"
    return(True)

def get_write():

    write,  = struct.unpack('i',   buf[168:172])     # flag
    return write

cnt  = 0

while True:

    cnt0   = shm_volt.get_counter()
    #print "\n SHM cnt0: ", cnt0
    
    if(cnt <= cnt0):
        cnt = cnt0
        time.sleep(0.001)
        print "\n SHM cnt0: ", cnt
         
        write = get_write()
        print "\n  SHM write value",get_write()

        if write == 0:
   
            [x,y] = read_shm()
            time.sleep(delay)
            print "\n piezo x & y read from SHM (volts):", x , y
        
           # [xvolt, yvolt] = write_piezoxy(x,y)
           # time.sleep(delay)
            Piezo_volt.write_piezox(72.4+x)
            time.sleep(delay)
            Piezo_volt.write_piezoy(72.7+y)
            time.sleep(delay)

            #print "\n Voltages sent to piezo x & y (volts):", xvolt, yvolt

            x = Piezo_volt.read_piezox()
            y = Piezo_volt.read_piezoy()

            #x = np.float(x[8:12])
            #y = np.float(y[8:12])

            #[xvolt, yvolt] = read_piezoxy()
            time.sleep(delay)
            print "\n Voltages read from piezo x (volts):", x
            print "\n Voltages read from piezo y (volts):", y
            
        cnt = cnt + 1

        #buf[176:184] = struct.pack('l', cnt)     # update counter
        #print "\nNew SHM counter value",shm_volt.get_counter()
  
        #exit(0)

        









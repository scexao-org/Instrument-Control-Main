#!/usr/bin/env python
import os
import commands
import numpy as np
import time

from lockfile import FileLock
import array

import mmap
import struct
import pdb

import matplotlib.pyplot as plt
import matplotlib.animation as ani


delay=0.05  #Delay between reading data in

fname='/tmp/irim1.bin'    #path and file to be read in

fd = os.open(fname, os.O_RDONLY)
buf = mmap.mmap(fd, 0, mmap.MAP_SHARED, mmap.PROT_READ)   #Creates a string structure of the data in shared memory

i=0       #initializing some values
x=list()
y=list()

fig=plt.figure()         #Initializing a figure
ax=plt.axes(xlim=(0,200), ylim=(1540000,1600000))   #Formats the plot
line, = ax.plot([], [], lw=2)

def init():
    line.set_data([], [])
    return line,

def animate(i):
    fi, = struct.unpack('l', buf[8:16])
    print("frame # %d" % (fi))
    x.append(i)
    y.append(fi)
    line.set_data(x,y)
    return line,

anim=ani.FuncAnimation(fig,animate,init_func=init,
                       frames=5000, interval=0.1, blit=True)  
#Calls a module called animation to make the movie. Cant get the screen to 
#keep going once it reaches the other end atm.
plt.show()   #Plots the data

##Alternative way using a while loop. Needs real time disp code.
#i=0
#while i<1000:
#    fi, = struct.unpack('l', buf[8:16])
#    print("frame # %d" % (fi))
#    x.append(i)
#    y.append(fi)
#    i+=1

os.close(fd)


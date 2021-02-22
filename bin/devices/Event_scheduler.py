#!/usr/bin/env python3

import pygame
import time
import numpy as np
import matplotlib.pyplot as plt 

import analog_output
import serial
import os
import time
import binascii
import sys
import pdb

home = os.getenv('HOME')
sys.path.append(home+'/bin/devices/')

from scexao_shm import shm

delay=0.5
relative=False
aoname="/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AH01JW35-if00-port0"

pygame.init()
TIMER_EVENT = pygame.USEREVENT+1

pygame.time.set_timer(TIMER_EVENT, 10)

timer_count = 0
MAX_TIMER_COUNT = 1000
time_step=np.zeros((1000,1))

shm_NominalVolt = shm("/tmp/pyrTT.im.shm")   # create shared memory file for Piezo
def read_NominalVolts():

    x0 = shm_NominalVolt.get_data()[0,0]
    y0 = shm_NominalVolt.get_data()[0,1]
    #x0 = -5.2
    #y0 = -5.7
    return (x0, y0)

def on_timer_event():
    global last_time
    global timer_count
    
    new_time = time.time()
    [x0,y0] = read_NominalVolts()

    print new_time - last_time
    time_step[timer_count-1] = new_time - last_time
    last_time = new_time

    if timer_count % 2 == 0:
        voltx=x0
        volty=y0
        ao.voltage('C',voltx)
        time.sleep(0.02)
        ao.voltage('D',volty)
    else:
        voltx=x0-1.
        volty=y0-1.
        ao.voltage('C',voltx)
        time.sleep(0.02)
        ao.voltage('D',volty)

    timer_count += 1
    time.sleep(0.02)
             

    if timer_count > MAX_TIMER_COUNT:
        print last_time - initial_time
        pygame.event.post(pygame.event.Event(pygame.QUIT, {}))

initial_time = time.time()
last_time = initial_time
ao = analog_output.aoutput(aoname)
while True:
    event = pygame.event.wait()
    if event.type == TIMER_EVENT:
        on_timer_event()

    elif event.type == pygame.QUIT:
        break

plt.figure()
plt.plot(time_step)
ave=np.average(time_step)
print ave
ao.close()

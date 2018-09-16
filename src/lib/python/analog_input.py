#!/usr/bin/env python
#waeE7124Nf
# ----------------------------------------------------------- #
#    _               _               _                   _    #
#   /_\  _ __   __ _| | ___   __ _  (_)_ __  _ __  _   _| |_  #
#  //_\\| '_ \ / _` | |/ _ \ / _` | | | '_ \| '_ \| | | | __| #
# /  _  \ | | | (_| | | (_) | (_| | | | | | | |_) | |_| | |_  #
# \_/ \_/_| |_|\__,_|_|\___/ \__, | |_|_| |_| .__/ \__,_|\__| #
#                           2|___/          |_|                #
# ----------------------------------------------------------- #

import serial
import os
import time
import binascii
import numpy as np

#devname  = "/dev/serial/by-path/"
#devname += "pci-0000:00:1a.0-usb-0:1.4.3.1.1:1.0-port0"

brate = 9600 # baud rate for Weeder AI board
tout  = 0.1  # time out for serial connection (in sec)
delay = 0.05  # safety delay between send - receive 

class ainput(object):
    def __init__(self,devname):
        self.s=serial.Serial(devname,brate,timeout=tout)

    def dec(self):
        self.s.write("ADA0\r\n") #changes position of decimal

    def mode(self):
        self.s.write("AMA1\r\n")

    def read(self,ptave):
        count=0
        output=np.zeros((ptave))
        while count < ptave:
            self.s.write("ARA\r\n")
            time.sleep(delay)
            result=(self.s.readlines()[0])
            output[count]=(int(''.join([i for i in result if i.isdigit()])))/1000.
            count=count+1
        return np.mean(output)
    
    def close(self):
        self.s.close()



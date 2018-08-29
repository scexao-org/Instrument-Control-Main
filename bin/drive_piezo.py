#!/usr/bin/env python
import serial
import os
import time
import binascii
import time
import sys

home = os.getenv('HOME')
sdir = home+'/conf/scexao_status/' # status directory

brate = 115200 # baud rate for EZ-stepper circuits
tout  = 0.2    # time out for serial connection (in sec)
delay = 0.1    # safety delay between send - receive

dev  = "/dev/serial/by-id/"
dev += "usb-FTDI_FT232R_USB_UART_AH01JW35-if00-port0"

# -----------------------------------------------
#  this is for the SCExAO status monitor program
# -----------------------------------------------

if not os.path.exists(sdir):
    os.mkdir(sdir)
    print("status directory was created")


class PIEZO:

    def __init__(self, dev):
        if os.path.islink(dev):
            dummy = os.path.split(dev)
            self.id = dummy[1]
            ddir = dummy[0]
            link = os.readlink(dev)
            self.dev = os.path.join(ddir, link)
        else:
            self.dev = dev
            self.id  = os.path.split(dev)[1]
        try:
            self.ser = serial.Serial(self.dev, brate, timeout=tout)
        except:
            self.ser = None
            print("Device %s either not connected or not powered" % \
                      (self.dev,))
            return(None)


    def write_piezox(self,Xvolt):
        cmdx="XV%f\r" % (Xvolt,)
        #self.s=serial.Serial(dev,brate, timeout=0.01)
        self.ser.write(cmdx)
        #self.s.close()
        return(None)

    def write_piezoy(self,Yvolt):
        cmdy="YV%f\r" % (Yvolt,)
        #self.s=serial.Serial(dev,brate, timeout=0.01)
        self.ser.write(cmdy)
        #self.s.close()
        return(None)

    def write_piezoxy(self,Xvolt, Yvolt):
        cmdx="XV%f\r" % (Xvolt,)
        cmdy="YV%f\r" % (Yvolt,)
        self.ser.write(cmdx)
        self.ser.write(cmdy)
        return(None)

    def write_piezoz(self,Zvolt):
        cmdz="ZV%f\r" % (Zvolt,)
        #self.s=serial.Serial(dev,brate, timeout=0.01)
        self.ser.write(cmdz)
        #self.s.close()
        return(None)

    def read_piezox(self):
        #self.s=serial.Serial(dev, brate, timeout=0.1)
        self.ser.write("XR?\r")
        infox=self.ser.readline()
        #self.s.close()
        return infox

    def read_piezoxy(self):
        self.ser.write("XR?\r")
        self.ser.write("YR?\r")
        infox=self.ser.readline()
        infoy=self.ser.readline()
        return infox, infoy

    def read_piezoy(self):
        #self.s=serial.Serial(dev, brate, timeout=0.1)
        self.ser.write("YR?\r")
        infoy=self.ser.readline()
        #self.s.close()
        return infoy

    def read_piezoz(self):
        #self.s=serial.Serial(dev, brate, timeout=0.1)
        self.ser.write("ZR?\r")
        infoz=self.ser.readline()
        #self.s.close()
        return infoz

    def close(self):
        if self.ser != None:
            self.ser.close()





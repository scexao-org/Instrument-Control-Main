#!/usr/bin/env python
import serial
import os
import time
import binascii
import time

home = os.getenv('HOME')
sdir = home+'/conf/scexao_status/' # status directory

brate = 9600 # baud rate for Weeder DIO board
tout  = 0.1  # time out for serial connection (in sec)
delay = 0.1  # safety delay between send - receive

# -----------------------------------------------
#  this is for the SCExAO status monitor program
# -----------------------------------------------

if not os.path.exists(sdir):
    os.mkdir(sdir)
    print("status directory was created")

# -------------------------------------------
#  this is EZ stepper chain class definition
# -------------------------------------------

class dio:
    def __init__(self, dev="/dev/null"):
        if dev != "/dev/null":
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

            self.ser.write('A00\r')
            time.sleep(delay)
            msg = self.ser.readline()
            
            if "A?" in msg:
                #print("DIO card found.")
                tmp = ""

            else:
                print("Device %s is not recognized as a DIO card" % \
                          (self.dev,))
                print("The chain may simply not be powered up.")
                self.ser.close()
                return(None)

        else:
            self.id = "null"
            self.dev = dev

    def flip(self, chn):
        self.ser.write("AL%s\r\n" % (chn))
        time.sleep(delay)
        dummy = self.ser.readline()
        #print dummy
        
        self.ser.write("AH%s\r\n" % (chn))
        time.sleep(delay)
        dummy = self.ser.readline()
        #print dummy

        self.ser.write("AL%s\r\n" % (chn))
        time.sleep(delay)
        dummy = self.ser.readline()
        #print dummy

    def turn_on(self, chn):
        self.ser.write("AH%s\r\n" % (chn))
        time.sleep(delay)
        dummy = self.ser.readline()
        print dummy

    def turn_off(self, chn):
        self.ser.write("AL%s\r\n" % (chn))
        time.sleep(delay)
        dummy = self.ser.readline()
        print dummy

    def init(self):
        ''' ------------------------------------------------------
        This is the sequence to set the flip mounts connected
        to the DIO board in the proper state.
        ------------------------------------------------------ '''
        
    def close(self):
        if self.ser != None:
            self.ser.close()

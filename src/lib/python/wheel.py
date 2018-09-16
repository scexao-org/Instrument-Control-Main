#!/usr/bin/env python
import serial
import os
import time

home = os.getenv('HOME')
sdir = home+'/conf/scexao_status/' # status directory

brate = 115200 # baud rate for Thorlabs FW102C
tout = 0.1     # time out for serial connection (in sec)

# -----------------------------------------------
#  this is for the SCExAO status monitor program
# -----------------------------------------------

if not os.path.exists(sdir):
    os.mkdir(sdir)
    print("status directory was created")

def touch(fname, times=None):
    with file(fname, 'a'):
        os.utime(fname, times)

# --------------------------------
#  this is wheel class definition
# --------------------------------

class wheel:
    def __init__(self, dev="/dev/null", config=None):

        ''' ---------------------------------------------------------
        dev:    device name in /dev/serial/by-id/...
        config: configuration file that stores the wheel content
        --------------------------------------------------------- '''

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

            self.ser.write('\r')
            dummy = self.ser.readline()
        else:
            self.id = "null"
            self.dev = dev

        current = sdir + self.id + '.txt'
        if os.path.exists(current):
            pos = open(current, 'r').readline()[0] # read single character
            self.goto(pos)

    def reset(self):
        current = sdir + self.id + '.txt'
        if ((os.path.exists(current)) and (self.id != "null")):
            pos = open(current, 'r').readline()[0] # read single character
            self.goto(pos)
        
    def goto(self, slot):
        if ((0 < int(slot) < 7) and (self.id != "null")):
            # -- rotate the filter wheel --
            self.ser.write("pos=%c\r" % (slot,))
            dummy = self.ser.readline()
            # -- update the config file --
            current = sdir + self.id + '.txt'
            open(current, 'w').write(slot+'\n')
            touch(sdir+'updt')
        else:
            print("can't do that")

    def what_slot(self):
        dummy = self.ser.readlines() # flush
        self.ser.write("pos?\r")
        time.sleep(0.1)
        dummy = self.ser.readline()
        return(dummy[5])

    def saved(self):
        current = sdir + self.id + '.txt'
        if (os.path.exists(current)):
            pos = open(current, 'r').readline()[0] # read single character)
        else:
            pos = "NOT DEFINED YET!"
        return(pos)

    def close(self):
        if self.ser != None:
            self.ser.close()

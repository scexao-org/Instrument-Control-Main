#!/usr/bin/env python
import serial
import os
import time
import subprocess

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
        '''
        current = sdir + self.id + '.txt'
        if os.path.exists(current):
            pos = open(current, 'r').readline()[0] # read single character
            self.goto(pos)
        '''
        '''
        filename = "/home/scexao/bin/devices/conf/conf_"+wheelname+".txt"

        slots = [line.rstrip('\n') for line in open(filename)]
        self.nslots = len(slots)
        nparam = len(slots[0].split(';'))
        for i in range(nparam):
            exec "self.param%d = []" % (i,)
            
        for j in range(self.nslots):
            sparam = slots[j].split(';')
            for i in range(nparam):
                exec "self.param%d.append(sparam[i])" % (i)
        '''
    def reset(self):
        current = sdir + self.id + '.txt'
        if ((os.path.exists(current)) and (self.id != "null")):
            pos = open(current, 'r').readline()[0] # read single character
            self.goto(pos)
        
    def goto(self, slot, wheelname):
        if ((0 < int(slot) < 7) and (self.id != "null")):
            # -- rotate the filter wheel --
            self.ser.write("pos=%c\r" % (slot,))
            dummy = self.ser.readline()
            # -- update the config file --
            current = sdir + self.id + '.txt'
            open(current, 'w').write(slot+'\n')
            touch(sdir+'updt')
            subprocess.call(["scexaostatus","set", str(wheelname), str(slot)])
        else:
            print("can't do that")

    def status(self, wheelname):
        dummy = self.ser.readlines() # flush
        self.ser.write("pos?\r")
        time.sleep(0.1)
        dummy = self.ser.readline()
        subprocess.call(["scexaostatus","set", str(wheelname), str(dummy[5])])
        print "Wheel is in position "+str(dummy[5])
        return(dummy[5])

    def saved(self):
        current = sdir + self.id + '.txt'
        if (os.path.exists(current)):
            pos = open(current, 'r').readline()[0] # read single character)
            print "Zaber is in position "+str(pos)
        else:
            pos = "NOT DEFINED YET!"
        return(pos)

    def close(self):
        if self.ser != None:
            self.ser.close()

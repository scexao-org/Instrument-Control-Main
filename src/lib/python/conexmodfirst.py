#!/usr/bin/env python
import serial
import os
import time
import binascii
import sys
import pdb

delay=0.5

class conex(object):
    def __init__(self):
        self.s=None

    def open(self,WN, byid=False):
        if byid == False:
            devname = "/dev/ttyCONEX%d" % (WN,)
            print("device: %s" % (devname,))
            self.s=serial.Serial(devname,921600,timeout=0.5)
        else:
            self.s=serial.Serial(byid,921600,timeout=0.5)
        #self.s.open()

    def home(self):
        self.s.write("1RS\r\n")
        time.sleep(delay)
        self.s.write("1OR\r\n")
    
    def move(self,POS):
        self.s.write("1PA"+str(POS)+"\r\n")
        time.sleep(delay)

    def pos(self):
        self.s.write("1TP\r\n")
        time.sleep(delay)
        pos=self.s.readlines()
        print(pos[0][3:-2])  
        pos=round(float(pos),2)
        return(pos)#print pos

    def getvel(self):
        self.s.write("1SU?\r\n")
        time.sleep(delay)
        vel=self.s.readlines()
        print(vel)  


    def setconfigon(self):
        self.s.write("1PW1\r\n")
        time.sleep(delay)
        print(self.s.readlines())

    def setconfigoff(self):
        self.s.write("1PW0\r\n")
        time.sleep(delay)
        print(self.s.readlines())
    
    def getconfig(self):
        self.s.write("1PW?\r\n")
        time.sleep(delay)
        print(self.s.readlines())
    
    def setstate(self,STATE):
        self.s.write("1MM"+str(STATE)+"\r\n")
        time.sleep(delay)
        print(self.s.readlines())

    def sendCMD(self,cmdv):
        self.s.write("1"+str(cmdv)+"\r\n")
        time.sleep(delay)
        print(self.s.readlines())

    def getstate(self):
        self.s.write("1MM?\r\n")
        time.sleep(delay)
        print(self.s.readlines())

    def setvel(self, VEL):
        self.s.write("1SU"+str(VEL)+"\r\n")
        time.sleep(delay)
        print(self.s.readlines())
    
    def reset(self):
        self.s.write("1RS\r\n")
        time.sleep(delay)
        print(self.s.readlines())

    def homealone(self):
        self.s.write("1OR\r\n")
        time.sleep(delay)
        print(self.s.readlines())

    def status(self):
        self.s.write("1TP\r\n")
        time.sleep(delay)
        pos=self.s.readlines()
        pos=pos[0]
        pos=pos[3:]
        pos=pos[:-2]
        pos=round(float(pos),1)
        if pos == 0.0:
            print "Wheel is in slot 1/home position"
        elif pos == 45.0:
            print "Wheel is in slot 2"
        elif pos == 90.0:
            print "Wheel is in slot 3"
        elif pos == 135.0:
            print "Wheel is in slot 4"
        elif pos ==180.0:
            print "Wheel is in slot 5"
        elif pos == 225:
            print "Wheel is in slot 6"
        elif pos == 270.0:
            print "Wheel is in slot 7"
        elif pos == 315.0:
            print "Wheel is in slot 8"
        else:
            print "Wheel is not on a slot. Try homing."

    def Lyot_status(self):
        self.s.write("1TP\r\n")
        time.sleep(delay)
        pos=self.s.readlines()
        pos=pos[0]
        pos=pos[3:]
        pos=pos[:-2]
        pos=round(float(pos),1)
        if pos == 0.0:
            print "Wheel is in slot 1/home position"
        elif pos == 28.5:
            print "Wheel is in slot 2"
        elif pos == 76.0:
            print "Wheel is in slot 3"
        elif pos == 135.0:
            print "Wheel is in slot 4"
        elif pos ==163.0:
            print "Wheel is in slot 5"
        else:
            print "Wheel is not on a slot. Try homing."

    def strbowl_status(self):
        self.s.write("1TP\r\n")
        time.sleep(delay)
        pos=self.s.readlines()
        pos=pos[0]
        pos=pos[3:]
        pos=pos[:-2]
        pos=round(float(pos),2)
        if pos == 1.20:
            print "Wheel is in slot 1/home position"
        elif pos == 46.10:
            print "Wheel is in slot 2"
        elif pos == 91.14:
            print "Wheel is in slot 3"
        elif pos == 136.59:
            print "Wheel is in slot 4"
        elif pos ==182.085:
            print "Wheel is in slot 5"
        elif pos == 221.20:
            print "Wheel is in slot 6"
        elif pos == 271.20:
            print "Wheel is in slot 7"
        elif pos == 319.09:
            print "Wheel is in slot 8"
        else:
            print "Wheel is not on a slot. Try homing."

    def pywfs_pickoff_status(self):
        self.s.write("1TP\r\n")
        time.sleep(delay)
        pos=self.s.readlines()
        pos=pos[0]
        pos=pos[3:]
        pos=pos[:-2]
        pos=round(float(pos),2)
        if pos == 0.0:
            print "Wheel is in slot 1/home position"
        elif pos == 30.0:
            print "Wheel is in slot 2"
        elif pos == 60.0:
            print "Wheel is in slot 3"
        elif pos == 90.0:
            print "Wheel is in slot 4"
        elif pos ==120.0:
            print "Wheel is in slot 5"
        elif pos == 150.0:
            print "Wheel is in slot 6"
        elif pos == 180.0:
            print "Wheel is in slot 7"
        elif pos == 210.0:
            print "Wheel is in slot 8"
        elif pos == 240.0:
            print "Wheel is in slot 9"
        elif pos == 270.0:
            print "Wheel is in slot 10"
        elif pos == 300.0:
            print "Wheel is in slot 11"
        elif pos == 330.0:
            print "Wheel is in slot 12"
        else:
            print "Wheel is not on a slot. Try homing."

    def vampfirst_status(self):
        self.s.write("1TP\r\n")
        time.sleep(delay)
        pos=self.s.readlines()
        pos=pos[0]
        pos=pos[3:]
        pos=pos[:-2]
        pos=round(float(pos),2)
        if pos == 0.0:
            print "Wheel is in slot 1/home position"
        elif pos == 36.0:
            print "Wheel is in slot 2"
        elif pos == 72.0:
            print "Wheel is in slot 3"
        elif pos == 108.0:
            print "Wheel is in slot 4"
        elif pos ==144.0:
            print "Wheel is in slot 5"
        elif pos == 180.0:
            print "Wheel is in slot 6"
        elif pos == 216.0:
            print "Wheel is in slot 7"
        elif pos == 252.0:
            print "Wheel is in slot 8"
        elif pos == 288.0:
            print "Wheel is in slot 9"
        elif pos == 324.0:
            print "Wheel is in slot 10"
        else:
            print "Wheel is not on a slot. Try homing."

    def status_calsrc(self):
        self.s.write("1TP\r\n")
        time.sleep(delay)
        pos=self.s.readlines()
        pos=pos[0]
        pos=pos[3:]
        pos=pos[:-2]
        pos=round(float(pos),1)
        print "Position "+str(pos)+"mm"
        
    def close(self):
        self.s.close()

  
   

#move()
#s.close()

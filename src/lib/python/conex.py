#!/usr/bin/env python
import serial
import os
import time
import binascii
import sys
import pdb
import subprocess

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
        self.s.write("1TP\n")
        time.sleep(delay)
        pos=self.s.readlines()
        print pos
        pos=pos[0]
        pos=pos[3:]
        pos=pos[:-2]
        pos=round(float(pos),2)
        return(pos)#print pos

    def status(self,wheel=""):
        self.s.write("1TP\r\n")
        time.sleep(delay)
        pos=self.s.readlines()
        print pos
        pos=pos[0]
        pos=pos[3:]
        pos=pos[:-2]
        pos=round(float(pos),1)
        if pos == 0.0:
            print "Wheel is in slot 1/home position"
            if wheel != "":
                subprocess.call(["scexaostatus","set", str(wheel), "1"])
        elif pos == 45.0:
            print "Wheel is in slot 2"
            if wheel != "":
                subprocess.call(["scexaostatus","set", str(wheel), "2"])
        elif pos == 90.0:
            print "Wheel is in slot 3"
            if wheel != "":
                subprocess.call(["scexaostatus","set", str(wheel), "3"])
        elif pos == 135.0:
            print "Wheel is in slot 4"
            if wheel != "":
                subprocess.call(["scexaostatus","set", str(wheel), "4"])
        elif pos ==180.0:
            print "Wheel is in slot 5"
            if wheel != "":
                subprocess.call(["scexaostatus","set", str(wheel), "5"])
        elif pos == 225:
            print "Wheel is in slot 6"
            if wheel != "":
                subprocess.call(["scexaostatus","set", str(wheel), "6"])
        elif pos == 270.0:
            print "Wheel is in slot 7"
            if wheel != "":
                subprocess.call(["scexaostatus","set", str(wheel), "7"])
        elif pos == 315.0:
            print "Wheel is in slot 8"
            if wheel != "":
                subprocess.call(["scexaostatus","set", str(wheel), "8"])
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
            subprocess.call(["scexaostatus","set", "lyotpos", "1"])
        elif pos == 28.5:
            print "Wheel is in slot 2"
            subprocess.call(["scexaostatus","set", "lyotpos", "2"])
        elif pos == 76.0:
            print "Wheel is in slot 3"
            subprocess.call(["scexaostatus","set", "lyotpos", "3"])
        elif pos == 135.0:
            print "Wheel is in slot 4"
            subprocess.call(["scexaostatus","set", "lyotpos", "4"])
        elif pos ==163.0:
            print "Wheel is in slot 5"
            subprocess.call(["scexaostatus","set", "lyotpos", "5"])
        else:
            print "Wheel is not on a slot. Try homing."

    def chariswhl_status(self):
        self.s.write("1TP\r\n")
        time.sleep(delay)
        pos=self.s.readlines()
        pos=pos[0]
        pos=pos[3:]
        pos=pos[:-2]
        pos=round(float(pos),2)
        if pos == 0.00:
            print "Wheel is in slot 1/home position"
            subprocess.call(["scexaostatus","set", "scibspos", "1"])
        elif pos == 45.15:
            print "Wheel is in slot 2"
            subprocess.call(["scexaostatus","set", "scibspos", "2"])
        elif pos == 90.00:
            print "Wheel is in slot 3"
            subprocess.call(["scexaostatus","set", "scibspos", "3"])
        elif pos == 135.00:
            print "Wheel is in slot 4"
            subprocess.call(["scexaostatus","set", "scibspos", "4"])
        elif pos == 180.00:
            print "Wheel is in slot 5"
            subprocess.call(["scexaostatus","set", "scibspos", "5"])
        elif pos == 225.00:
            print "Wheel is in slot 6"
            subprocess.call(["scexaostatus","set", "scibspos", "6"])
        elif pos == 270.00:
            print "Wheel is in slot 7"
            subprocess.call(["scexaostatus","set", "scibspos", "7"])
        elif pos == 315.00:
            print "Wheel is in slot 8"
            subprocess.call(["scexaostatus","set", "scibspos", "8"])
        else:
            print "Wheel is not on a slot. Try homing."

    def mkidswhl_status(self):
        self.s.write("1TP\r\n")
        time.sleep(delay)
        pos=self.s.readlines()
        pos=pos[0]
        pos=pos[3:]
        pos=pos[:-2]
        pos=round(float(pos),2)
        if pos == 0.00:
            print "Wheel is in slot 1/home position"
            subprocess.call(["scexaostatus","set", "sci2bspos", "1"])
        elif pos == 44.11:
            print "Wheel is in slot 2"
            subprocess.call(["scexaostatus","set", "sci2bspos", "2"])
        elif pos == 90.00:
            print "Wheel is in slot 3"
            subprocess.call(["scexaostatus","set", "sci2bspos", "3"])
        elif pos == 135.00:
            print "Wheel is in slot 4"
            subprocess.call(["scexaostatus","set", "sci2bspos", "4"])
        elif pos == 180.00:
            print "Wheel is in slot 5"
            subprocess.call(["scexaostatus","set", "sci2bspos", "5"])
        elif pos == 225.00:
            print "Wheel is in slot 6"
            subprocess.call(["scexaostatus","set", "sci2bspos", "6"])
        elif pos == 270.00:
            print "Wheel is in slot 7"
            subprocess.call(["scexaostatus","set", "sci2bspos", "7"])
        elif pos == 315.00:
            print "Wheel is in slot 8"
            subprocess.call(["scexaostatus","set", "sci2bspos", "8"])
        else:
            print "Wheel is not on a slot. Try homing."

    def fwheel_status(self):
        self.s.write("1TP\r\n")
        time.sleep(delay)
        pos=self.s.readlines()
        pos=pos[0]
        pos=pos[3:]
        pos=pos[:-2]
        pos=round(float(pos),2)
        if pos == 0.00:
            print "Wheel is in slot 1/home position"
            subprocess.call(["scexaostatus","set", "IRfwpos", "1"])
        elif pos == 45.00:
            print "Wheel is in slot 2"
            subprocess.call(["scexaostatus","set", "IRfwpos", "2"])
        elif pos == 90.00:
            print "Wheel is in slot 3"
            subprocess.call(["scexaostatus","set", "IRfwpos", "3"])
        elif pos == 135.00:
            print "Wheel is in slot 4"
            subprocess.call(["scexaostatus","set", "IRfwpos", "4"])
        elif pos == 180.00:
            print "Wheel is in slot 5"
            subprocess.call(["scexaostatus","set", "IRfwpos", "5"])
        elif pos == 225.00:
            print "Wheel is in slot 6"
            subprocess.call(["scexaostatus","set", "IRfwpos", "6"])
        elif pos == 270.00:
            print "Wheel is in slot 7"
            subprocess.call(["scexaostatus","set", "IRfwpos", "7"])
        elif pos == 315.00:
            print "Wheel is in slot 8"
            subprocess.call(["scexaostatus","set", "IRfwpos", "8"])
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
            subprocess.call(["scexaostatus","set", "pywfsbspos", "1"])
        elif pos == 30.0:
            print "Wheel is in slot 2"
            subprocess.call(["scexaostatus","set", "pywfsbspos", "2"])
        elif pos == 60.0:
            print "Wheel is in slot 3"
            subprocess.call(["scexaostatus","set", "pywfsbspos", "3"])
        elif pos == 90.0:
            print "Wheel is in slot 4"
            subprocess.call(["scexaostatus","set", "pywfsbspos", "4"])
        elif pos ==120.0:
            print "Wheel is in slot 5"
            subprocess.call(["scexaostatus","set", "pywfsbspos", "5"])
        elif pos == 150.0:
            print "Wheel is in slot 6"
            subprocess.call(["scexaostatus","set", "pywfsbspos", "6"])
        elif pos == 180.0:
            print "Wheel is in slot 7"
            subprocess.call(["scexaostatus","set", "pywfsbspos", "7"])
        elif pos == 210.0:
            print "Wheel is in slot 8"
            subprocess.call(["scexaostatus","set", "pywfsbspos", "8"])
        elif pos == 240.0:
            print "Wheel is in slot 9"
            subprocess.call(["scexaostatus","set", "pywfsbspos", "9"])
        elif pos == 270.0:
            print "Wheel is in slot 10"
            subprocess.call(["scexaostatus","set", "pywfsbspos", "10"])
        elif pos == 300.0:
            print "Wheel is in slot 11"
            subprocess.call(["scexaostatus","set", "pywfsbspos", "11"])
        elif pos == 330.0:
            print "Wheel is in slot 12"
            subprocess.call(["scexaostatus","set", "pywfsbspos", "12"])
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
            subprocess.call(["scexaostatus","set", "vampfirstbspos", "1"])
        elif pos == 36.0:
            print "Wheel is in slot 2"
            subprocess.call(["scexaostatus","set", "vampfirstbspos", "2"])
        elif pos == 72.0:
            print "Wheel is in slot 3"
            subprocess.call(["scexaostatus","set", "vampfirstbspos", "3"])
        elif pos == 108.0:
            print "Wheel is in slot 4"
            subprocess.call(["scexaostatus","set", "vampfirstbspos", "4"])
        elif pos ==144.0:
            print "Wheel is in slot 5"
            subprocess.call(["scexaostatus","set", "vampfirstbspos", "5"])
        elif pos == 180.0:
            print "Wheel is in slot 6"
            subprocess.call(["scexaostatus","set", "vampfirstbspos", "6"])
        elif pos == 216.0:
            print "Wheel is in slot 7"
            subprocess.call(["scexaostatus","set", "vampfirstbspos", "7"])
        elif pos == 252.0:
            print "Wheel is in slot 8"
            subprocess.call(["scexaostatus","set", "vampfirstbspos", "8"])
        elif pos == 288.0:
            print "Wheel is in slot 9"
            subprocess.call(["scexaostatus","set", "vampfirstbspos", "9"])
        elif pos == 324.0:
            print "Wheel is in slot 10"
            subprocess.call(["scexaostatus","set", "vampfirstbspos", "10"])
        else:
            print "Wheel is not on a slot. Try homing."

    def status_calsrc(self):
        self.s.write("1TP\r\n")
        time.sleep(delay)
        pos=self.s.readlines()
        pos=pos[0][3:-2]
        pos=round(float(pos),1)
        print pos
        print "Position "+str(pos)+"mm"
        if pos == 0.0:
            subprocess.call(["scexaostatus","set", "cal_src", "2"])
        if pos == 21.5:
            subprocess.call(["scexaostatus","set", "cal_src", "1"])
            

    def src_status(self):
        self.s.write("1TP\r\n")
        time.sleep(delay)
        pos=self.s.readlines()
        pos=pos[0]
        pos=pos[3:]
        pos=pos[:-2]
        pos=round(float(pos),1)
        if pos == 20.3:
            print "Tunable superK is in"
            subprocess.call(["scexaostatus","set", "supKsrc", "1"])
        elif pos == 32.7:
            print "1523 nm HeNe is in"
            subprocess.call(["scexaostatus","set", "supKsrc", "2"])
        elif pos == 43.0:
            print "Broadband SuperK is in"
            subprocess.call(["scexaostatus","set", "supKsrc", "3"])
        elif pos == 43.12:
            print "Broadband SuperK faint is in"
            subprocess.call(["scexaostatus","set", "supKsrc", "4"])
        elif pos == 52.5:
            print "Halogen lamp is in"
            subprocess.call(["scexaostatus","set", "supKsrc", "5"])
        else:
            print "Unsure, try homing."
        
    def close(self):
        self.s.close()

  
   

#move()
#s.close()

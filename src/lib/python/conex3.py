#!/usr/bin/env python
import serial
import os
import time
import sys
import subprocess
home = os.getenv('HOME')
sys.path.append(home+'/src/lib/python/')
import logit #Custom logging library

delay = 0.5

class conex(object):
    def __init__(self):
        self.s = None

    def open(self, devid):
        self.s = serial.Serial(devid, 921600, timeout=0.5)
        dummy = self.s.readlines() # flush the port

    def home(self, devname):
        self.s.write("1RS\r\n")
        time.sleep(delay)
        self.s.write("1OR\r\n")
        logit.logit(devname,'Homed')
    
    def move(self, pos, devname, log=True):
        self.s.write("1PA"+str(pos)+"\r\n")
        time.sleep(delay)
        if log:
            logit.logit(devname,'moved_to_'+str(pos))

    def status(self, devname):
        self.s.write("1TP\r\n")
        time.sleep(delay)
        pos = self.s.readlines()
        try:
            pos = pos[0]
            pos = pos[3:]
            pos = pos[:-2]
            pos = round(float(pos), 3)
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", devname, str(pos)])
        except:
            print pos
            print "NO STATUS SENT"
        return pos
        
    def close(self):
        self.s.close()

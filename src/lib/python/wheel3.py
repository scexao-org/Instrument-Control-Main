#!/usr/bin/env python
import serial
import os
import time
import sys
import subprocess
home = os.getenv('HOME')
sys.path.append(home+'/src/lib/python/')
import logit #Custom logging library

class wheel(object):
    def __init__(self):
        self.s = None
        
    def open(self, devid):
        try:
            self.s = serial.Serial(devid, 115200, timeout=0.5)
            self.s.write('\r'.encode())
            dummy = self.s.readline() # flush the port
        except:
            print("Thorlabs wheel %s not connected" %devid)
            sys.exit()
            
    def move(self, slot, devname):
        self.s.write(str.encode("pos=%c\r" % (slot,)))
        dummy = self.s.readline()
        logit.logit(devname,'moved_to_slot_'+str(slot))

    def status(self):
        dummy = self.s.readlines() # flush
        self.s.write("pos?\r".encode())
        time.sleep(0.1)
        dummy = self.s.readline().decode()
        slot = dummy[5]
        return int(slot)

    def close(self):
        self.s.close()

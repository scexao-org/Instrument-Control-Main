#!/usr/bin/env python
import serial
import os
import time
import sys
import subprocess

delay=0.5

class conex(object):
    def __init__(self):
        self.s=None

    def open(self, byid, conexname):
        self.s=serial.Serial(byid,921600,timeout=0.5)
        filename = "/home/scexao/bin/devices/conf/conf_"+conexname+".txt"
        
        slots = [line.rstrip('\n') for line in open(filename)]
        self.nslots = len(slots)
        nparam = len(slots[0].split(';'))
        for i in range(nparam):
            exec "self.param%d = []" % (i,)
        
        for j in range(self.nslots):
            sparam = slots[j].split(';')
            for i in range(nparam):
                exec "self.param%d.append(sparam[i])" % (i)

    def home(self, conexname):
        self.s.write("1RS\r\n")
        time.sleep(delay)
        self.s.write("1OR\r\n")
        subprocess.call(["scexaostatus","set", str(conexname), "-1"])
    
    def move(self,POS, conexname):
        self.s.write("1PA"+str(POS)+"\r\n")
        time.sleep(delay)
        subprocess.call(["scexaostatus","set", str(conexname), str(POS)])

    def status(self, conexname, col=2):
        self.s.write("1TP\r\n")
        time.sleep(delay)
        pos=self.s.readlines()
        pos=pos[0]
        pos=pos[3:]
        pos=pos[:-2]
        pos=round(float(pos),2)
        subprocess.call(["scexaostatus","set", str(conexname), str(pos)])
        if pos == 0:
            print "Conex is home."
        exec "paramf = map(float, self.param%d)" %(col,)
        if pos in paramf:
            for i in range(self.nslots):
                if pos == paramf[i]:
                    print "Conex is in position "+self.param0[i]+", "+self.param1[i]+"."
        else:
            print "Position = "+str(pos)+", Conex is not in a defined position. Try homing."
        return pos
        
    def close(self):
        self.s.close()

  
   

#move()
#s.close()

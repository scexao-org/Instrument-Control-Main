#!/usr/bin/env python
import serial
import os
import time
import sys
import subprocess
home = os.getenv('HOME')
sys.path.append(home+'/src/lib/python/')
import logit #Custom logging library

delay = 0.1 

def step2zaberByte(nstep):
    step = nstep        # local version of the variable
    zbytes = [0,0,0,0]  # series of four bytes for Zaber
    if step < 0: step += 256**4
    for i in range(3,-1,-1):
        zbytes[i] = step / 256**i
        step     -= zbytes[i] * 256**i
    return zbytes
                                                     
def zaberByte2step(zb):
    nstep = zb[3]*256**3 + zb[2]*256**2 + zb[1]*256 + zb[0]
    if zb[3] > 127: nstep -= 256**4
    return nstep

def zab_cmd(cmd):
    nl = []
    instr = map(int, cmd.split(' '))

    for c in instr:
        if c == 255: nl.extend([c,c])
        else:        nl.append(c)

    buf = ''.join(map(chr, nl))
    return buf

def zab_response(data):
   r = map(ord, data)
   foo = r
   r = []
   flag = 0
   for c in foo:
      if flag == 0: 
          r.append(c)
          if c == 255: flag = 1
      else: flag = 0
   buf = string.join(map(str,r[-6:])).strip()
   return buf

class zaber:
    def __init__(self):
        self.s = None

    def open(self, zaberchain):
        filename = "/home/scexao/bin/devices/conf/path_zabchain_"+zaberchain+".txt"
        filep = open(filename, 'r')
        self.dev  = "/dev/serial/"
        self.dev += filep.read().rstrip('\n')
        self.s = serial.Serial(self.dev, 9600, timeout=0.5)
        dummy = self.s.readlines() # flush the port

    def home(self, idn, devname):
        self.command(idn, 1, 0)
        logit.logit(devname,'Homed')

    def move(self, idn, pos, devname, log=True):
        self.command(idn, 20, pos)
        time.sleep(delay)
        if log:
            logit.logit(devname,'moved_to_'+str(pos))
        
    def status(self, idn, devname):
        pos = self.command(idn, 60, 0)
        subprocess.call(["/home/scexao/bin/scexaostatus", "set", devname, str(pos)])
        return pos

    def command(self, idn, cmd, arg, quiet=True):
        args = ' '.join(map(str, step2zaberByte(int(arg))))
        full_cmd = '%s %d %s' % (idn, cmd, args)
        if not quiet:
            print full_cmd
        self.s.write(zab_cmd(full_cmd))
        dummy = []
        while dummy == []:
            dummy = map(ord, self.s.readline())
            time.sleep(0.1)
        reply = zaberByte2step(dummy[2:])
        if not quiet:
            print("zaber %d = %d" % (int(idn), reply))
        return(reply)

    def close(self):
        self.s.close()

#!/usr/bin/env python
import serial
import os
import time
import numpy as np

home = os.getenv('HOME')
sdir = home+'/conf/scexao_status/' # status directory

brate = 9600 # baud rate for Zaber actuators
tout  = 0.1  # time out for serial connection (in sec)
delay = 0.1  # safety delay between send - receive

# -----------------------------------------------
#  this is for the SCExAO status monitor program
# -----------------------------------------------

if not os.path.exists(sdir):
    os.mkdir(sdir)
    print("status directory was created")

# ---------------------------------------------------
#      utility to signal the status monitor
# ---------------------------------------------------

def touch(fname, times=None):
    with file(fname, 'a'):
        os.utime(fname, times)

# ---------------------------------------------------
# convert a number of steps into the series of bytes 
# expected by the Zaber actuator                     
# ---------------------------------------------------

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

# ---------------------------------------------------
# conversion between low-level serial port command 
# format and representation in the program
# ---------------------------------------------------

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

# -----------------------------------------------
#  this is for the SCExAO status monitor program
# -----------------------------------------------

if not os.path.exists(sdir):
    os.mkdir(sdir)
    print("status directory was created")

# --------------------------------------
#  this is zaber chain class definition
# --------------------------------------

class zaber_chain:
    def __init__(self, dev="/dev/null", quiet=False):
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

            dummy = self.ser.readlines() # flush the port

            initz = False
            tmpf = '/tmp/' + self.id + '.tmp'

            if not os.path.exists(tmpf):
                initz = True
                touch(tmpf)

                # --- initial position query ---
                self.ser.write(zab_cmd('0 60 0 0 0 0'))
                time.sleep(delay)
                dummy = map(ord, self.ser.readline())
                sz = dummy.__len__()

                if (sz < 1):
                    print("Device %s either not connected or not powered" % \
                              (self.dev,))
                    self.ser.close()
                    self.ser = None
                    return(None)

                if not quiet:
                    print dummy
                if ((sz >= 6) and (dummy[1] == 60)):
                    self.nz = sz / 6
                    print("Device %s connected to %d Zabers" % \
                              (self.dev, self.nz,))
                    self.idns = np.zeros(self.nz)
                    for i in range(self.nz):
                        self.idns[i] = int(dummy[6*i]) # stores connected dev ids

                    # --
                    for i in range(self.nz):
                        cmd = "%d 60 0 0 0 0" % (self.idns[i],)
                        self.ser.write(zab_cmd(cmd))
                        time.sleep(delay)
                        dummy = map(ord, self.ser.readline())
                        if not quiet:
                            print("ID %d = %d" % \
                                      (self.idns[i], zaberByte2step(dummy[2:])))
        else:
            self.id = "null"
            self.dev = dev

        # refresh the zaber memory with last saved positions
        current = sdir + self.id + '.txt'
        if os.path.exists(current):
            if initz:
                lines = open(current, 'r+w').readlines() # read multiple lines
                nl = lines.__len__()                     # number of lines

                for i in range(nl):
                    data = lines[i].split() # read #actu & position
                    if data != []:
                        args = ' '.join(map(str, step2zaberByte(int(data[1]))))
                        self.command(data[0], 45, data[1], quiet=quiet)

        else:
            # create a file with 0 positions
            f = open(current, 'w')
            for i in range(self.nz):
                f.write("%d %d\n" % (self.idns[i], 0))
            f.close()

    def home(self, idn=None):
        current = sdir + self.id + '.txt'

        if idn == None: # global home
            f = open(current, 'w')
            for i in range(self.nz):
                f.write("%d 0\n" % (self.idns[i],))
            f.close()
            touch(sdir+'updt')

            for i in range(self.nz):
                self.command(self.idns[i], 1, 0)
        else:
            self.command(idn, 1, 0)
            f = open(current, 'r+')
            lines = f.readlines()
            f.close()

            for i in range(lines.__len__()):
                data = lines[i].split()
                if data != []:
                    if int(data[0]) == int(idn):
                        lines[i] = data[0] + ' ' + str(0) + '\n'
                open(current, 'w').writelines(lines)
            touch(sdir+'updt')
    
    def status(self, idn=None, quiet=False):
        pos = self.command(idn, 60, 0, quiet=quiet)
        if pos == 0:
            print "Zaber is home."
        print "Zaber is in position "+str(pos)
        return pos

    def command(self, idn, cmd, arg, force=False, quiet=False):
        current = sdir + self.id + '.txt'
        if ((not os.path.exists(current)) and (not force)):
            print("Config file does not exist. Home device first!")
            return(None)
        if force:
            print("Command forced. Should home device.")

        args = ' '.join(map(str, step2zaberByte(int(arg))))
        full_cmd = '%s %d %s' % (idn, cmd, args)
        if not quiet:
            print full_cmd
        self.ser.write(zab_cmd(full_cmd))
        dummy = []
        while dummy == []:
            dummy = map(ord, self.ser.readline())
            time.sleep(0.1)
        reply = zaberByte2step(dummy[2:])
        if not quiet:
            print("zaber %d = %d" % (int(idn), reply))
        return(reply)

    def move(self, idn, pos, force=False, relative=False, quiet=False):
        cmd = 20
        if relative:
            cmd = 21
        self.command(idn, cmd, pos, force, quiet)
        # -- update the config file --
        current = sdir + self.id + '.txt'
        f = open(current, 'r+')
        lines = f.readlines()
        f.close()

        for i in range(lines.__len__()):
            data = lines[i].split()
            if data != []:
                if int(data[0]) == int(idn):
                    lines[i] = data[0] + ' ' + str(pos) + '\n'
                open(current, 'w').writelines(lines)
                touch(sdir+'updt')
    
        
    def close(self):
        if self.ser != None:
            self.ser.close()

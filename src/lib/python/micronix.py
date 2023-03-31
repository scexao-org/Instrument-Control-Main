#!/usr/bin/env python3

# ========================================================================== #
#    ___                     _                      _         __             #
#   / _ \___ _ __   ___ _ __(_) ___    ___ ___   __| | ___   / _| ___  _ __  #
#  / /_\/ _ \ '_ \ / _ \ '__| |/ __|  / __/ _ \ / _` |/ _ \ | |_ / _ \| '__| #
# / /_\\  __/ | | |  __/ |  | | (__  | (_| (_) | (_| |  __/ |  _| (_) | |    #
# \____/\___|_| |_|\___|_|  |_|\___|  \___\___/ \__,_|\___| |_|  \___/|_|    #
#                                                                            #
#   __ _ _                                     _                             #
#  / _| (_)_ __    _ __ ___   ___  _   _ _ __ | |_ ___                       #
# | |_| | | '_ \  | '_ ` _ \ / _ \| | | | '_ \| __/ __|                      #
# |  _| | | |_) | | | | | | | (_) | |_| | | | | |_\__ \                      #
# |_| |_|_| .__/  |_| |_| |_|\___/ \__,_|_| |_|\__|___/                      #
#         |_|                                                                #
#                                                                            #
# ========================================================================== #

import time
import os
import sys
import serial
import subprocess
import numpy as np
home = os.getenv('HOME')
sys.path.append(home+'/src/lib/python/')

# =====================================================================
# =====================================================================

def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False
 
class micronix(object):
    def __init__(self, micname, micid, axesids, axesnames, args=[], description="no description", defpos=[], color_st=False):

        self.micname = micname
        self.description = description
        self.micid = "/dev/serial/by-id/"+micid
        self.axesids = axesids
        self.axesnames = axesnames
        naxes = len(self.axesnames)
        self.args = args
        self.defpos = defpos
        self.color_st = color_st
        
        filename = home+"/bin/devices/conf/conf_"+micname+".txt"
        slots = [line.rstrip('\n') for line in open(filename)]
        self.nslots = len(slots)
        nparam = len(slots[0].split(';'))
        self.nend = nparam-1
        for i in range(nparam):
            exec("self.param%d = []" % (i,), globals(), locals())
            
        for j in range(self.nslots):
            sparam = slots[j].split(';')
            for i in range(nparam):
                exec("self.param%d.append(sparam[i])" % (i,), globals(), locals())

        if args == []:
            self.usage()
            
        else:
            if "--help1" in args[0].lower():
                self.quickhelp()
                sys.exit()

            elif args[0].lower() in axesnames:
                axisname = args[0].lower()
                axisid = axesids[axesnames.index(axisname)]
                
                if "home" in args[1].lower():   #Home command
                    opened = self.open(self.micid)
                    if opened:
                        self.home(axisid)
                        time.sleep(1)
                        pos0 = -1000.
                        pos = self.status(axisid,axisname)
                        subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.micname+'_st', 'UNKNOWN', '3'])
                        while pos0 != pos:
                            pos0 = pos
                            pos = self.status(axisid,axisname)
                            time.sleep(0.2)
                            try:
                                subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.micname+"_"+axisname, str(pos)])
                            except:
                                print("waiting for value")
                        
                        self.s.write("%iZRO\r\n".encode() %axisid)
                        time.sleep(0.2)
                        self.close()
                
                elif "status" in args[1].lower():
                    opened = self.open(self.micid)
                    if opened:
                        pos = self.status(axisid, axisname)
                        time.sleep(0.2)
                        self.close()
                        d = locals()
                        exec("paramf = list(map(float, self.param%d))" %(axisid+1), globals(), d)
                        paramf = d['paramf']
                        if pos in paramf:
                            for i in range(self.nslots):
                                if pos == paramf[i]:
                                    print("Position = "+str(pos)+", Micronix is in position "+self.param0[i]+", "+self.param1[i])
                        else:
                            print("Position = "+str(pos)+", Micronix is not in a defined position. Try homing.")
                    
                elif "goto" in args[1].lower():  #Goto commands
                    if isfloat(args[2]):
                        opened = self.open(self.micid)
                        if opened:
                            self.goto(axisid,float(args[2]))
                            time.sleep(1)
                            pos0 = -1000.
                            pos = self.status(axisid,axisname)
                            subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.micname+'_st', 'UNKNOWN', '3'])
                            while pos0 != pos:
                                pos0 = pos
                                pos = self.status(axisid,axisname)
                                time.sleep(0.2)
                                try:
                                    subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.micname+"_"+axisname, str(pos)])
                                except:
                                    print("waiting for value")
                            self.close()
                    else:
                        self.usage()
                        
                elif args[1].isdigit():
                    slot = int(args[1])
                    opened = self.open(self.micid)
                    if opened:
                        #self.goto_slot(slot, conu)
                        self.close()

            elif args[0].lower() in defpos:
                inddef = defpos.index(args[0].lower())
                if (0 <= inddef < self.nslots):
                    for i in range(naxes):
                        opened = self.open(self.micid)
                        if not opened:
                            subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.micname+'_st', 'NOT CONNECTED', '0'])
                            sys.exit()
                        else:
                            d = locals()
                            exec("pos = float(self.param%d[inddef])" %(i+2,), globals(), d)
                            pos = d['pos']
                            self.goto(axesids[i],float(pos))
                            time.sleep(0.2)
                            pos0 = self.status(axesids[i],axesnames[i])
                            subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.micname+'_st', 'UNKNOWN', '3'])
                            it = 0
                            while pos0 != pos or it == 10:
                                pos0 = self.status(axesids[i],axesnames[i])
                                it += 1
                                time.sleep(0.2)
                                try:
                                    subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.micname+"_"+self.axesnames[i], str(pos0)])
                                except:
                                    print("waiting for value")
                            if self.color_st:
                                exec("subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.micname+'_st', self.param1[inddef][:16], self.param%d[inddef]])" % (self.nend,), globals(), locals())
                            else:
                                subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.micname+"_st", self.param1[inddef][:16]])
                        
                    self.close()

            elif "status" in args[0].lower():
                pos = np.zeros(naxes)
                paramf = np.zeros(naxes)
                found = False
                for i in range(naxes):
                    opened = self.open(self.micid)
                    if not opened:
                        subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.micname+'_st', 'NOT CONNECTED', '0'])
                        sys.exit()
                    pos[i] = self.status(axesids[i], axesnames[i])
                    time.sleep(0.2)
                    self.close()
                for i in range(self.nslots):
                    for j in range(naxes):
                        exec("paramf[j] = float(self.param%d[i])" %(j+2,), globals(), locals())
                    if (np.sum(paramf[1:]) > 0 and np.all(pos == paramf)) or (np.sum(paramf[1:]) == 0 and pos[0] == paramf[0]):
                        print("Device is in position "+self.param0[i]+", "+self.param1[i])
                        if self.color_st:
                            exec("subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.micname+'_st', self.param1[i][:16], self.param%d[i]])" % (self.nend,), globals(), locals())
                        else:
                            subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.micname+"_st", self.param1[i][:16]])
                        found = True
                if not found:
                    print("Device is not in a defined position. Try homing.")
                    subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.micname+'_st', 'UNKNOWN', '3'])

            elif "com" in args[0].lower():
                opened = self.open(self.micid)
                if not opened:
                    subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.micname+'_st', 'NOT CONNECTED', '0'])
                    sys.exit()
                self.s.write(("%s\r\n"%args[1]).encode())
                time.sleep(0.2)
                status = self.s.readlines()
                print(status)
                time.sleep(1)
                self.close()


            else:
                self.usage()
        
    # =====================================================================

    def open(self, micid):
        try:
            self.s = serial.Serial(micid, baudrate=38400, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, rtscts=True, timeout=0.1)
            dummy = self.s.readlines() # flush the port
            opened = True
            time.sleep(0.2)
        except:
            print("DISCONNECTED")
            subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.micname+'_st', 'NOT CONNECTED', '0'])
            opened = False
        return opened

    def home(self, axisid):
        try:
            self.s.write("%iFBK3\r\n".encode() %axisid)
            time.sleep(1)
            self.s.write("%iHOM\r\n".encode() %axisid)
            time.sleep(1)
        except:
            print("CANNOT HOME AXIS")
    
    def status(self, axisid, axisname):
        self.s.write("%iPOS?\r\n".encode() %axisid)
        time.sleep(0.2)
        status = self.s.readlines()
        if status == []:
            self.s.write("%iPOS?\r\n".encode() %axisid)
            time.sleep(0.2)
            status = self.s.readlines()
        pos = 0
        try:
            pos = status[0].decode()
            pos = pos[1:9]
            pos = round(float(pos), 3)
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", "%s_%s" %(self.micname,axisname), str(pos)])
        except:
            print("STATUS UNKNOWN")
            subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.micname+'_st', 'UNKNOWN', '3'])
        return pos
            
    def goto(self, axisid, pos):
        try:
            self.s.write("%iMVA%f\r\n".encode() %(axisid,pos))
            time.sleep(0.2)
            self.s.write("%iMVA%f\r\n".encode() %(axisid,pos))
            time.sleep(0.2)
        except:
            print("CANNOT MOVE AXIS")
    
    def close(self):
        time.sleep(0.2)
        self.s.close()
        
    # =====================================================================
    
    def usage(self):
        print("""---------------------------------------
Usage: %s <dev> <command> <arg>
---------------------------------------""" %self.micname)
        print("DEV:")
        for i in range(len(self.axesnames)):
            print("    %-6s  move %s axis" % (self.axesnames[i], self.axesnames[i]))
        print("    status  status of the full device")
        print("""COMMAND:)
    status  displays status
      home  sends home
      goto  moves to absolute position: numerical value
     1 - %d defined positions""" % (self.nslots,))
        if self.defpos != []:
            for i in range(len(self.defpos)):
                print("    %-6s  move stage to %s position" % (self.defpos[i], self.defpos[i]))
        print("""ARG:
    numerical value for position
CONTENT:""")
        for i in range(self.nslots):
            print("   ", self.param0[i], self.param1[i])
                        
        print("--------------------------------------- ")

    # -----------------------------------------------------------------
    def quickhelp(self):
        print("%20s       %s" % (self.micname,self.description))

    # -----------------------------------------------------------------

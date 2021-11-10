#!/usr/bin/env python

# ========================================================= #
#    ___                     _                      _       #
#   / _ \___ _ __   ___ _ __(_) ___    ___ ___   __| | ___  #
#  / /_\/ _ \ '_ \ / _ \ '__| |/ __|  / __/ _ \ / _` |/ _ \ #
# / /_\\  __/ | | |  __/ |  | | (__  | (_| (_) | (_| |  __/ #
# \____/\___|_| |_|\___|_|  |_|\___|  \___\___/ \__,_|\___| #
#                                                           #
#   __                  _            _                      #
#  / _| ___  _ __    __| | _____   _(_) ___ ___  ___        #
# | |_ / _ \| '__|  / _` |/ _ \ \ / / |/ __/ _ \/ __|       #
# |  _| (_) | |    | (_| |  __/\ V /| | (_|  __/\__ \       #
# |_|  \___/|_|     \__,_|\___| \_/ |_|\___\___||___/       #
#                                                           #
# ========================================================= #

import os
import sys
import subprocess
import numpy as np
import time
home = os.getenv('HOME')
sys.path.append(home+'/src/lib/python/')
import logit #Custom logging library
import conex_tt

# =====================================================================
# =====================================================================

def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False
        
class steering_tt:
    
    def __init__(self, devname, conexid="http://133.40.163.196:50001", conexnames=[], args=[], description="no description", defpos=[]):
        
        self.devname = devname
        self.description = description
        
        if args != [] and "--help1" in args[0].lower():
            self.quickhelp()
            sys.exit()
          
        self.conexid = conexid
        self.conexnames = conexnames
        self.args = args
        self.defpos = defpos
        self.nbdev = 2
        
        if args != []:
            self.devnamec = devname+'_'+args[0]
        
        filename = "/home/scexao/bin/devices/conf/conf_"+devname+".txt"
        
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
                
        if args != []:
            try:
                self.col = conexnames.index(args[0])+2
            except:
                self.col = 2
              
        na = args.__len__()  # number of arguments
        
        if args == []:
            self.usage()
            
        elif (args[0].lower() in conexnames) and args[0].lower() not in defpos:
            if na > 1:
                self.axis = args[0].lower()
                if "goto" in args[1].lower():  #Goto commands
                    if (na > 2) and isfloat(args[2]):
                        self.conex_goto(float(args[2]))
                    else:
                        self.usage()
                        
                elif args[1].isdigit():
                    slot = int(args[1])
                    self.conex_goto_slot(slot)
                    
                else:
                    self.usage()
                  
            else:
                self.usage()
                
        elif args[0].lower() in defpos:
            inddef = defpos.index(args[0].lower())
            self.col = 2
            self.conex_goto_slot(inddef+1)
            exec("subprocess.call(['/home/scexao/bin/scexaostatus', 'set', devname+'_st', self.param1[inddef], self.param%d[inddef]])" % (self.nend,), globals(), locals())

        elif "home" in args[0].lower():   #Home command
            self.conex_home()
            
        elif "status" in args[0].lower():
            self.conex_status()
            
        else:
            self.usage()

    # =====================================================================
    
    def usage(self):
        print("""---------------------------------------
Usage: %s <dev> <command> <arg>
---------------------------------------""" % (self.devname))
        print("DEV:")
        if self.conexnames != []:
            for i in range(len(self.conexnames)):
                print("    %-6s  move %s stage" % (self.conexnames[i], self.conexnames[i]))
        print("    status  status of the full device")
        print("""COMMAND:
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
        print("%20s       %s" % (self.devname,self.description))

    # -----------------------------------------------------------------
    def conex_home(self):
        conex_tt.move(0., 0., self.devname, self.conexid)
        pos0 = (-1000.,-1000.)
        pos = conex_tt.status(self.devname, self.conexid)
        subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devname+'_st', 'UNKNOWN', '3'])
        while pos0 != pos:
            pos0 = pos
            pos = conex_tt.status(self.devname, self.conexid)
            time.sleep(0.2)
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.devname+"_theta", str(pos[1])])
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.devname+"_phi", str(pos[0])])
            subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devname+'_st', 'UNKNOWN', '3'])
        
    # -----------------------------------------------------------------
    def conex_status(self):
        pos = conex_tt.status(self.devname, self.conexid)
        if pos == (0.,0.):
            print("Conex is home.")
        paramf1 = list(map(float, self.param2))
        paramf2 = list(map(float, self.param3))
        if pos[1] in paramf1 and pos[0] in paramf2:
            for i in range(self.nslots):
                if pos[1] == paramf1[i] and pos[0] == paramf2[i]:
                    print("Position = "+str(pos[::-1])+", Conex is in position "+self.param0[i]+", "+self.param1[i])
                    exec("subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devnamec+'_st', self.param1[i][:16], self.param%d[i]])" % (self.nend,), globals(), locals())
        else:
            print("Position = "+str(pos[::-1])+", Conex is not in a defined position. Try homing.")
            subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devname+'_st', 'UNKNOWN', '3'])
              
    # -----------------------------------------------------------------
    def conex_goto(self, pos):
        posc = conex_tt.status(self.devname, self.conexid)
        if self.axis == "theta":
            if self.devname == "steering":
                conex_tt.move(posc[0], pos, self.devname, self.conexid)
            else:
                conex_tt.move(pos, posc[0], self.devname, self.conexid)
            paramf = list(map(float, self.param2))
        elif self.axis == "phi":
            if self.devname == "steering":
                conex_tt.move(pos, posc[1], self.devname, self.conexid)
            else:
                conex_tt.move(posc[1], pos, self.devname, self.conexid)
            paramf = list(map(float, self.param3))
        pos0 = (-1000,-1000.)
        paramf1 = list(map(float, self.param2))
        paramf2 = list(map(float, self.param3))
        subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devname+'_st', 'UNKNOWN', '3'])
        while pos0 != posc:
            pos0 = posc
            posc = conex_tt.status(self.devname, self.conexid)
            time.sleep(0.1)           
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.devname+"_theta", str(posc[1])])
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.devname+"_phi", str(posc[0])])
        
    # -----------------------------------------------------------------
    def conex_goto_slot(self, slot):
        if (1 <= slot <= self.nslots):
            d = locals()
            exec("pos1 = self.param%d[slot-1]" %(self.col,), globals(), d)
            pos1 = d['pos1']
            d = locals()
            exec("pos2 = self.param%d[slot-1]" %(self.col+1,), globals(), d)
            pos2 = d['pos2']
            if self.devname == "steering":
                conex_tt.move(pos2, pos1, self.devname, self.conexid)
            else:
                conex_tt.move(pos1, pos2, self.devname, self.conexid)
            pos0 = (-1000.,-1000.)
            pos = conex_tt.status(self.devname, self.conexid)
            subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devname+'_st', 'UNKNOWN', '3'])
            while pos0 != pos:
                pos0 = pos
                pos = conex_tt.status(self.devname, self.conexid)
                time.sleep(0.2)
                subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.devname+"_theta", str(pos[1])])
                subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.devname+"_phi", str(pos[0])])
                    
            logit.logit(self.devname,'moved_to_slot_'+str(slot))
        else:
            print("Conex only has "+str(self.nslots)+" positions")

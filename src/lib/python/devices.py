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

# =====================================================================
# =====================================================================

def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False
        
class devices:
    
    def __init__(self, devname, conexids=[], conexnames=[], zaberchain="", zaberids=[], zabernames=[], args=[], description="no description", defpos=[], color_st=False):
        
        self.devname = devname
        self.description = description
        
        if args != [] and "--help1" in args[0].lower():
            self.quickhelp()
            sys.exit()
          
        self.conexids = conexids
        self.conexnames = conexnames
        self.zaberchain = zaberchain
        self.zaberids = zaberids
        self.zabernames = zabernames
        self.args = args
        self.defpos = defpos
        self.color_st = color_st
        self.nbdev = len(conexnames)+len(zabernames)
        
        if conexnames != []:
            import conex3 as conex
            self.con = conex.conex()
            if self.nbdev == 1:
                self.devnamec = devname
                conu = 0
                zabu = 1
            else:
                if args != []:
                    self.devnamec = devname+'_'+args[0]
                conu = 1
                zabu = 1
            
        if zabernames != []:
            import zaber_chain3 as zaber
            self.zab = zaber.zaber()
            if self.nbdev == 1:
                self.devnamez = devname
                zabu = 0
                conu = 1
            else:
                if args != []:
                    self.devnamez = devname+'_'+args[0]
                zabu = 1
                conu = 1
                
        filename = "/home/scexao/bin/devices/conf/conf_"+devname+".txt"
        
        slots = [line.rstrip('\n') for line in open(filename)]
        self.nslots = len(slots)
        nparam = len(slots[0].split(';'))
        self.nend = nparam-1
        for i in range(nparam):
            exec "self.param%d = []" % (i,)
            
        for j in range(self.nslots):
            sparam = slots[j].split(';')
            for i in range(nparam):
                exec "self.param%d.append(sparam[i])" % (i,)
                
        if self.nbdev == 1:
            self.col = 2
        else:
            if args != []:
                try:
                    self.col = (conexnames+zabernames).index(args[0])+2
                except:
                    self.col = 2
              
        na = args.__len__()  # number of arguments
        
        if args == []:
            self.usage()
            
        elif (args[0].lower() in conexnames) or (conu == 0) and args[0].lower() not in defpos:
            if na > conu:
                if conu == 0:
                    self.conexid = "/dev/serial/by-id/"+conexids[0]
                else:
                    cindex = conexnames.index(args[0].lower())
                    self.conexid = "/dev/serial/by-id/"+conexids[cindex]
                if "home" in args[conu].lower():   #Home command
                    self.conex_home(conu)

                elif "status" in args[conu].lower():
                    self.conex_status(conu)
                    
                elif "goto" in args[conu].lower():  #Goto commands
                    if (na > conu+1) and isfloat(args[conu+1]):
                        self.conex_goto(float(args[conu+1]), conu)
                    else:
                        self.usage()
                        
                elif args[conu].isdigit():
                    slot = int(args[conu])
                    self.conex_goto_slot(slot, conu)
                    
                else:
                    self.usage()
                  
            else:
                self.usage()
                
        elif ((args[0].lower() in zabernames) or (zabu == 0)) and (zaberchain != "") and args[0].lower() not in defpos:
            if na > zabu:
                if zabu == 0:
                    self.zaberid = zaberids[0]
                else:
                    zindex = zabernames.index(args[0].lower())
                    self.zaberid = zaberids[zindex]
                if "home" in args[zabu].lower():   #Home command
                    self.zaber_home(zabu)
                    
                elif "status" in args[zabu].lower():
                    self.zaber_status(zabu)
                    
                elif "goto" in args[zabu].lower():  #Goto commands
                    if (na > zabu+1) and (args[zabu+1].isdigit()):
                        self.zaber_goto(int(args[zabu+1]), zabu)
                    else:
                        self.usage()
                        
                elif args[zabu].isdigit():
                    slot = int(args[zabu])
                    self.zaber_goto_slot(slot, zabu)
                    
                else:
                    self.usage()
                  
            else:
                self.usage()
              
        elif args[0].lower() in defpos:
            inddef = defpos.index(args[0].lower())
            self.col = 2
            if conexnames != []:
                for i in range(len(conexnames)):
                    if self.nbdev != 1:
                        self.devnamec = devname+'_'+conexnames[i]
                    self.conexid = "/dev/serial/by-id/"+conexids[i]
                    self.conex_goto_slot(inddef+1, 1)
                    self.col += 1
            if zabernames != []:
                for i in range(len(zabernames)):
                    if self.nbdev != 1:
                        self.devnamez = devname+'_'+zabernames[i]
                    self.zaberid = zaberids[i]
                    self.zaber_goto_slot(inddef+1, 1)
                    self.col += 1
            if self.color_st:
                exec "subprocess.call(['/home/scexao/bin/scexaostatus', 'set', devname+'_st', self.param1[inddef], self.param%d[inddef]])" % (self.nend,)
            else:
                subprocess.call(["/home/scexao/bin/scexaostatus", "set", devname+"_st", self.param1[inddef]])

                    
        elif ("status" in args[0].lower() and conu*zabu == 1):
            self.col = 2
            pos = np.zeros(self.nbdev)
            paramf = np.zeros(self.nbdev)
            found = False
            if conexnames != []:
                for i in range(len(conexnames)):
                    self.devnamec = devname+'_'+conexnames[i]
                    self.conexid = "/dev/serial/by-id/"+conexids[i]
                    self.con.open(self.conexid)
                    pos[self.col-2] = self.con.status(self.devnamec)
                    self.col += 1
                    self.con.close()
            if zabernames != []:
                for i in range(len(zabernames)):
                    self.devnamez = devname+'_'+zabernames[i]
                    self.zaberid = zaberids[i]
                    self.zab.open(self.zaberchain)
                    pos[self.col-2] = self.zab.status(self.zaberid, self.devnamez)
                    self.col += 1
                    self.zab.close()
            for i in range(self.nslots):
                for j in range(self.nbdev):
                    exec "paramf[j] = float(self.param%d[i])" %(j+2,)
                if (np.sum(paramf[1:]) > 0 and np.all(pos == paramf)) or (np.sum(paramf[1:]) == 0 and pos[0] == paramf[0]):
                    print "Device is in position "+self.param0[i]+", "+self.param1[i]
                    if self.color_st:
                        exec "subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devname+'_st', self.param1[i][:16], self.param%d[i]])" % (self.nend,)
                    else:
                        subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.devname+"_st", self.param1[i][:16]])
                    found = True
            if not found:
                print "Device is not in a defined position. Try homing."
                subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devname+'_st', 'UNKNOWN', '3'])
        
        else:
            self.usage()

    # =====================================================================
    
    def usage(self):
        if self.nbdev > 1:
            dev = "<dev> "
        else:
            dev = ""
        print """---------------------------------------
Usage: %s %s <command> <arg>
---------------------------------------""" % (self.devname,dev)
        if self.nbdev > 1:
            print "DEV:"
            if self.conexnames != []:
                for i in range(len(self.conexnames)):
                    print "    %-6s  move %s stage" % (self.conexnames[i], self.conexnames[i])
            if self.zabernames != []:
                for i in range(len(self.zabernames)):
                    print "    %-6s  move %s stage" % (self.zabernames[i], self.zabernames[i])
        print "    status  status of the full device"
        print """COMMAND:
    status  displays status
      home  sends home
      goto  moves to absolute position: numerical value
     1 - %d defined positions""" % (self.nslots,)
        if self.defpos != []:
            for i in range(len(self.defpos)):
                print "    %-6s  move stage to %s position" % (self.defpos[i], self.defpos[i])
        print """ARG:
    numerical value for position
CONTENT:"""
        for i in range(self.nslots):
            print "   ", self.param0[i], self.param1[i]
                        
        print "--------------------------------------- "

    # -----------------------------------------------------------------
    def quickhelp(self):
        print "%20s       %s" % (self.devname,self.description)

    # -----------------------------------------------------------------
    def conex_home(self, conu):
        self.con.open(self.conexid)
        self.con.home(self.devnamec)
        pos0 = -1000.
        exec "paramf = map(float, self.param%d)" %(self.col,)
        pos = self.con.status(self.devnamec)
        subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devname+'_st', 'UNKNOWN', '3'])
        while pos0 != pos:
            pos0 = pos
            pos = self.con.status(self.devnamec)
            time.sleep(0.2)
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.devnamec, str(pos)])
            if conu == 0:
                if pos in paramf:
                    for i in range(self.nslots):
                        if pos == paramf[i]:
                            if self.color_st:
                                exec "subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devnamec+'_st', self.param1[i][:16], self.param%d[i]])" % (self.nend,)
                            else:
                                subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.devnamec+"_st", self.param1[i][:16]])
                else:
                    subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devnamec+'_st', 'UNKNOWN', '3'])
        self.con.close()
        
    # -----------------------------------------------------------------
    def conex_status(self, conu):
        self.con.open(self.conexid)
        pos = self.con.status(self.devnamec)
        self.con.close()
        if pos == 0:
            print "Conex is home."
        exec "paramf = map(float, self.param%d)" %(self.col,)
        if pos in paramf:
            for i in range(self.nslots):
                if pos == paramf[i]:
                    print "Position = "+str(pos)+", Conex is in position "+self.param0[i]+", "+self.param1[i]
                    if conu == 0:
                        if self.color_st:
                            exec "subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devnamec+'_st', self.param1[i][:16], self.param%d[i]])" % (self.nend,)
                        else:
                            subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.devnamec+"_st", self.param1[i][:16]])
        else:
            print "Position = "+str(pos)+", Conex is not in a defined position. Try homing."
            if conu == 0:
                subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devnamec+'_st', 'UNKNOWN', '3'])
              
    # -----------------------------------------------------------------
    def conex_goto(self, pos, conu):
        self.con.open(self.conexid)
        self.con.move(pos, self.devnamec)
        pos0 = -1000.
        exec "paramf = map(float, self.param%d)" %(self.col,)
        pos = self.con.status(self.devnamec)
        subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devnamec+'_st', 'UNKNOWN', '3'])
        while pos0 != pos:
            pos0 = pos
            pos = self.con.status(self.devnamec)
            time.sleep(0.1)
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.devnamec, str(pos)])
            if conu == 0:
                if pos in paramf:
                    for i in range(self.nslots):
                        if pos == paramf[i]:
                            if self.color_st:
                                exec "subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devnamec+'_st', self.param1[i][:16], self.param%d[i]])" % (self.nend,)
                            else:
                                subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.devnamec+"_st", self.param1[i][:16]])
                else:
                    subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devnamec+'_st', 'UNKNOWN', '3'])
        self.con.close()
        
    # -----------------------------------------------------------------
    def conex_goto_slot(self, slot, conu):
        if (1 <= slot <= self.nslots):
            self.con.open(self.conexid)
            exec "pos = self.param%d[slot-1]" %(self.col,)
            self.con.move(float(pos), self.devnamec, log=False)
            pos0 = -1000.
            exec "paramf = map(float, self.param%d)" %(self.col,)
            pos = self.con.status(self.devnamec)
            subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devname+'_st', 'UNKNOWN', '3'])
            while pos0 != pos:
                pos0 = pos
                pos = self.con.status(self.devnamec)
                time.sleep(0.2)
                subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.devnamec, str(pos)])
                if conu == 0:
                    if pos in paramf:
                        for i in range(self.nslots):
                            if pos == paramf[i]:
                                if self.color_st:
                                    exec "subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devnamec+'_st', self.param1[i][:16], self.param%d[i]])" % (self.nend,)
                                else:
                                    subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.devnamec+"_st", self.param1[i][:16]])
                    else:
                        subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devnamec+'_st', 'UNKNOWN', '3'])
            self.con.close()
            logit.logit(self.devnamec,'moved_to_slot_'+str(slot))
        else:
            print("Conex only has "+str(self.nslots)+" positions")
            
    # -----------------------------------------------------------------
    def zaber_home(self, zabu):
        self.zab.open(self.zaberchain)
        self.zab.home(self.zaberid, self.devnamez)
        pos0 = -1.5
        exec "paramf = map(float, self.param%d)" %(self.col,)
        pos = self.zab.status(self.zaberid, self.devnamez)
        subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devname+'_st', 'UNKNOWN', '3'])
        while pos0 != pos:
            pos0 = pos
            pos = self.zab.status(self.zaberid, self.devnamez)
            time.sleep(0.2)
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.devnamez, str(pos)])
            if zabu == 0:
                if pos in paramf:
                    for i in range(self.nslots):
                        if pos == paramf[i]:
                            if self.color_st:
                                exec "subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devnamez+'_st', self.param1[i][:16], self.param%d[i]])" % (self.nend,)
                            else:
                                subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.devnamez+"_st", self.param1[i][:16]])
                else:
                    subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devnamez+'_st', 'UNKNOWN', '3'])
        self.zab.close()
        
    # -----------------------------------------------------------------
    def zaber_status(self, zabu):
        self.zab.open(self.zaberchain)
        pos = self.zab.status(self.zaberid, self.devnamez)
        self.zab.close()
        if pos == 0:
            print "Zaber is home."
        exec "paramf = map(int, self.param%d)" %(self.col,)
        if pos in paramf:
            for i in range(self.nslots):
                if pos == paramf[i]:
                    print "Position = "+str(pos)+", Zaber is in position "+self.param0[i]+", "+self.param1[i]
                    if zabu == 0:
                        if self.color_st:
                            exec "subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devnamez+'_st', self.param1[i][:16], self.param%d[i]])" % (self.nend,)
                        else:
                            subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.devnamez+"_st", self.param1[i][:16]])
        else:
            print "Position = "+str(pos)+", Zaber is not in a defined position. Try homing."
            if zabu == 0:
                subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devnamez+'_st', 'UNKNOWN', '3'])
              
    # -----------------------------------------------------------------
    def zaber_goto(self, pos, zabu):
        self.zab.open(self.zaberchain)
        self.zab.move(self.zaberid, pos, self.devnamez)
        pos0 = -1.5
        exec "paramf = map(float, self.param%d)" %(self.col,)
        pos = self.zab.status(self.zaberid, self.devnamez)
        subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devname+'_st', 'UNKNOWN', '3'])
        while pos0 != pos:
            pos0 = pos
            pos = self.zab.status(self.zaberid, self.devnamez)
            time.sleep(0.2)
            subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.devnamez, str(pos)])
            if zabu == 0:
                if pos in paramf:
                    for i in range(self.nslots):
                        if pos == paramf[i]:
                            if self.color_st:
                                exec "subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devnamez+'_st', self.param1[i][:16], self.param%d[i]])" % (self.nend,)
                            else:
                                subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.devnamez+"_st", self.param1[i][:16]])
                else:
                    subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devnamez+'_st', 'UNKNOWN', '3'])
        self.zab.close()
        
    # -----------------------------------------------------------------
    def zaber_goto_slot(self, slot, zabu):
        if (1 <= slot <= self.nslots):
            self.zab.open(self.zaberchain)
            exec "pos = self.param%d[slot-1]" %(self.col,)
            if int(pos) > 0:
                self.zab.move(self.zaberid, int(pos), self.devnamez, log=False)
                pos0 = -1.5
                exec "paramf = map(float, self.param%d)" %(self.col,)
                pos = self.zab.status(self.zaberid, self.devnamez)
                subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devname+'_st', 'UNKNOWN', '3'])
                while pos0 != pos:
                    pos0 = pos
                    pos = self.zab.status(self.zaberid, self.devnamez)
                    time.sleep(0.2)
                    subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.devnamez, str(pos)])
                    if zabu == 0:
                        if pos in paramf:
                            for i in range(self.nslots):
                                if pos == paramf[i]:
                                    if self.color_st:
                                        exec "subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devnamez+'_st', self.param1[i][:16], self.param%d[i]])" % (self.nend,)
                                    else:
                                        subprocess.call(["/home/scexao/bin/scexaostatus", "set", self.devnamez+"_st", self.param1[i][:16]])
                        else:
                            subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devnamez+'_st', 'UNKNOWN', '3'])
                self.zab.close()
                logit.logit(self.devnamez,'moved_to_slot_'+str(slot))
        else:
            print("Zaber only has "+str(self.nslots)+" positions")
            

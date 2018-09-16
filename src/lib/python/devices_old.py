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
    
    def __init__(self, devname, conexids=[], conexnames=[], zaberchain="", zaberids=[], zabernames=[], args=[], description="no description", defpos=[]):
        
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
                    self.conex_home()

                elif "status" in args[conu].lower():
                    self.conex_status()
                    
                elif "goto" in args[conu].lower():  #Goto commands
                    if (na > conu+1) and isfloat(args[conu+1]):
                        self.conex_goto(float(args[conu+1]))
                    else:
                        self.usage()
                        
                elif args[conu].isdigit():
                    slot = int(args[conu])
                    self.conex_goto_slot(slot)
                    
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
                    self.zaber_home()
                    
                elif "status" in args[zabu].lower():
                    self.zaber_status()
                    
                elif "goto" in args[zabu].lower():  #Goto commands
                    if (na > zabu+1) and (args[zabu+1].isdigit()):
                        self.zaber_goto(int(args[zabu+1]))
                    else:
                        self.usage()
                        
                elif args[zabu].isdigit():
                    slot = int(args[zabu])
                    self.zaber_goto_slot(slot)
                    
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
                    self.conex_goto_slot(inddef+1)
                    self.col += 1
            if zabernames != []:
                for i in range(len(zabernames)):
                    if self.nbdev != 1:
                        self.devnamez = devname+'_'+zabernames[i]
                    self.zaberid = zaberids[i]
                    self.zaber_goto_slot(inddef+1)
                    self.col += 1
                                    
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
    def conex_home(self):
        self.con.open(self.conexid)
        self.con.home(self.devnamec)
        self.con.close()
        
    # -----------------------------------------------------------------
    def conex_status(self):
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
        else:
            print "Position = "+str(pos)+", Conex is not in a defined position. Try homing."
              
    # -----------------------------------------------------------------
    def conex_goto(self, pos):
        self.con.open(self.conexid)
        self.con.move(pos, self.devnamec)
        self.con.close()
        
    # -----------------------------------------------------------------
    def conex_goto_slot(self, slot):
        if (1 <= slot <= self.nslots):
            self.con.open(self.conexid)
            exec "pos = self.param%d[slot-1]" %(self.col,)
            self.con.move(float(pos), self.devnamec, log=False)
            self.con.close()
            logit.logit(self.devnamec,'moved_to_slot_'+str(slot))
        else:
            print("Conex only has "+str(self.nslots)+" positions")
            
    # -----------------------------------------------------------------
    def zaber_home(self):
        self.zab.open(self.zaberchain)
        self.zab.home(self.zaberid, self.devnamez)
        self.zab.close()
        
    # -----------------------------------------------------------------
    def zaber_status(self):
        self.zab.open(self.zaberchain)
        pos = self.zab.status(self.zaberid, self.devnamez)
        self.zab.close()
        if pos == 0:
            print "Zaber is home."
        exec "paramf = map(int, self.param%d)" %(self.col,)
        if pos in paramf:
            for i in range(self.nslots):
                if pos == paramf[i]:
                    print "Position = "+str(pos)+", Zaber is in position "+self.param0[i]+", "+self.param1[i]+"."
        else:
            print "Position = "+str(pos)+", Zaber is not in a defined position. Try homing."
              
    # -----------------------------------------------------------------
    def zaber_goto(self, pos):
        self.zab.open(self.zaberchain)
        self.zab.move(self.zaberid, pos, self.devnamez)
        self.zab.close()
        
    # -----------------------------------------------------------------
    def zaber_goto_slot(self, slot):
        if (1 <= slot <= self.nslots):
            self.zab.open(self.zaberchain)
            exec "pos = self.param%d[slot-1]" %(self.col,)
            self.zab.move(self.zaberid, int(pos), self.devnamez, log=False)
            self.zab.close()
            logit.logit(self.devnamez,'moved_to_slot_'+str(slot))
        else:
            print("Zaber only has "+str(self.nslots)+" positions")
            

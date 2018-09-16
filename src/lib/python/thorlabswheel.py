#!/usr/bin/env python

# =========================================================================== #
#    ___                     _                      _         __              #
#   / _ \___ _ __   ___ _ __(_) ___    ___ ___   __| | ___   / _| ___  _ __   #
#  / /_\/ _ \ '_ \ / _ \ '__| |/ __|  / __/ _ \ / _` |/ _ \ | |_ / _ \| '__|  #
# / /_\\  __/ | | |  __/ |  | | (__  | (_| (_) | (_| |  __/ |  _| (_) | |     #
# \____/\___|_| |_|\___|_|  |_|\___|  \___\___/ \__,_|\___| |_|  \___/|_|     #
#                                                                             #
#  _____ _                _       _                    _               _      #
# /__   \ |__   ___  _ __| | __ _| |__  ___  __      _| |__   ___  ___| |___  #
#   / /\/ '_ \ / _ \| '__| |/ _` | '_ \/ __| \ \ /\ / / '_ \ / _ \/ _ \ / __| #
#  / /  | | | | (_) | |  | | (_| | |_) \__ \  \ V  V /| | | |  __/  __/ \__ \ #
#  \/   |_| |_|\___/|_|  |_|\__,_|_.__/|___/   \_/\_/ |_| |_|\___|\___|_|___/ #
#                                                                             #
# =========================================================================== #

import os
import sys
import subprocess
home = os.getenv('HOME')
sys.path.append(home+'/src/lib/python/')
import wheel3 as wheel

# =====================================================================
# =====================================================================

class thorlabswheel:

    def __init__(self, devname, whids=[], whnames=[], args=[], description="no description", color_st=False):

        self.devname = devname
        self.description = description

        if args != [] and "--help1" in args[0].lower():
            self.quickhelp()
            sys.exit()
          
        self.whids = whids
        self.whnames = whnames
        self.args = args
        self.color_st = color_st
        self.wh = wheel.wheel()

        if whnames == []:
            self.devnamew = devname
            whu = 0
        else:
            if args != []:
                self.devnamew = devname+'_'+args[0]
                whu = 1
            
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
                
        na = args.__len__()  # number of arguments
        
        if args == []:
            self.usage()

        elif (args[0].lower() in whnames) or (whu == 0):
            if na > whu:
                if whu == 0:
                    self.windex = 0
                    self.whid = "/dev/serial/by-id/"+whids[0]
                else:
                    self.windex = whnames.index(args[0].lower())
                    self.whid = "/dev/serial/by-id/"+whids[self.windex]
                if "status" in args[whu].lower():
                    self.wheel_status()
                    
                elif args[whu].isdigit():
                    slot = args[whu]
                    self.wheel_goto_slot(slot)
                            
                else:
                    self.usage()
                        
            else:
                self.usage()
                
        else:
            self.usage()

    # =====================================================================
    
    def usage(self):
        if self.whnames != []:
            dev = "<dev> "
        else:
            dev = ""
        print """---------------------------------------
Usage: %s %s <command>
---------------------------------------""" % (self.devname,dev)
        if self.whnames != []:
            print "DEV:"
            for i in range(len(self.whnames)):
                    print "    %-6s  move %s stage" % (self.whnames[i], self.whnames[i])
        print """COMMAND:
    status  displays status
     1 - 6 defined positions"""
        print """ARG:
    numerical value for position
CONTENT:"""
        if self.whnames == []:
            for i in range(6):
                print "   ", self.param0[i], self.param1[i]
        else:
            for j in range(len(self.whnames)):
                print "   ", self.whnames[j]
                for i in range(6):
                    exec "print '   ', self.param0[i], self.param%d[i]" % (j+1,)
                        
        print "--------------------------------------- "

    # -----------------------------------------------------------------
    def quickhelp(self):
        print "%20s       %s" % (self.devname,self.description)
        
    # -----------------------------------------------------------------
    def wheel_status(self):
        self.wh.open(self.whid)
        slot = self.wh.status()
        self.wh.close()
        exec "params = self.param%d[slot-1]" % (self.windex+1,)
        print "Position = "+str(slot)+", Conex is in position "+self.param0[slot-1]+", "+params
        if self.color_st:
            exec "subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devnamew, params, self.param%d[slot-1]])" % (self.nend,)
        else:
            subprocess.call(["/home/scexao/bin/scexaostatus","set", self.devnamew, params])
            
        
    # -----------------------------------------------------------------
    def wheel_goto_slot(self, slot):
        if (1 <= int(slot) <= 6):
            self.wh.open(self.whid)
            self.wh.move(slot, self.devnamew)
            self.wh.close()
            exec "params = self.param%d[int(slot)-1]" % (self.windex+1,)
            if self.color_st:
                exec "subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.devnamew, params, self.param%d[int(slot)-1]])" % (self.nend,)
            else:
                subprocess.call(["/home/scexao/bin/scexaostatus","set", self.devnamew, params])

        else:
            print("Conex only has 6 positions")

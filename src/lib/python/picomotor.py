#!/usr/bin/env python

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

import sys
import os
import numpy as np
import subprocess
import asyncio
from newfocus8742.tcp import NewFocus8742TCP as TCP

home = os.getenv('HOME')
sys.path.append(home+'/src/lib/python/')
import logit #Custom logging library

#from scxkw.config import REDIS_DB_HOST, REDIS_DB_PORT
#from scxkw.redisutil.typed_db import Redis

#rdb = Redis(host=REDIS_DB_HOST, port=REDIS_DB_PORT)
#LEGACY_EXEC = '/home/scexao/bin/scexaostatus'

# =====================================================================
# =====================================================================

class picomotor:

    def __init__(self, picobench, piconame, picoids, axesnames, args=[], description="no description"):
        
        filename = home+"/bin/devices/conf/conf_"+piconame+".txt"
        filename2 = home+"/bin/devices/conf/path_pico_"+picobench+".txt"
        self.piconame = piconame
        filep = open(filename2, 'r')
        self.picopath = filep.read().rstrip('\n')
        self.description = description

        if args != [] and "--help1" in args[0]:
            self.quickhelp()
            sys.exit()

        loop = asyncio.get_event_loop()
        loop.set_debug(False)
        self.picoids = picoids
        self.axesnames = axesnames
        
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
            self.piconamep = piconame+'_'+args[0]

        self.col = axesnames.index(args[0])+2

        na = args.__len__()

        if args == []:
            self.usage()

        elif args[0].lower() in axesnames:
            if na > 1:
                pindex = axesnames.index(args[0].lower())
                self.picoid = picoids[pindex]

                if "status" in args[1].lower():
                    loop.run_until_complete(self.status())
                    """
                elif "goto" in args[1].lower():
                    if (na > 2) and (args[2].lstrip('+-').isdigit()):
                        loop.run_until_complete(self.goto(int(args[2])))
                else:
                        self.usage()
                    """
                elif "push" in args[1].lower():
                    if (na > 2) and (args[2].lstrip('+-').isdigit()):
                        loop.run_until_complete(self.push(int(args[2])))
                    else:
                        self.usage()

                elif args[2].isdigit():
                    slot = int(args[2])
                    loop.run_until_complete(self.goto_slot(slot))

            else:
                self.usage()

        """
        elif args[0].lower() in defpos:
            inddef = defpos.index(args[0].lower())
            self.col = 2
            for i in range(len(axesnames)):
                self.piconamep = piconame+'_'+axesnames[i]
                self.goto_slot(inddef+1)
                self.col += 1

        elif ("status" in args[0].lower() and conu*zabu == 1):
            self.col = 2
            pos = np.zeros(self.nbdev)
            paramf = np.zeros(self.nbdev)
            found = False
            for i in range(len(axesnames)):
                self.piconamep = piconame+'_'+axesnames[i]
                pos[self.col-2] = self.con.status(self.devnamec)
                    self.col += 1
                    self.con.close()
            for i in range(self.nslots):
                for j in range(self.nbdev):
                    exec("paramf[j] = float(self.param%d[i])" %(j+2,), globals(), locals())
                if (np.sum(paramf[1:]) > 0 and np.all(pos == paramf)) or (np.sum(paramf[1:]) == 0 and pos[0] == paramf[0]):
                    print("Device is in position "+self.param0[i]+", "+self.param1[i])
                    #if self.color_st:
                    #    exec("subprocess.call([home+'/bin/scexaostatus', 'set', self.devname+'_st', self.param1[i][:16], self.param%d[i]])" % (self.nend,), globals(), locals())
                    #else:
                    #    subprocess.call([home+"/bin/scexaostatus", "set", self.devname+"_st", self.param1[i][:16]])
                    found = True
            if not found:
                print("Device is not in a defined position. Try homing.")
                #subprocess.call([home+'/bin/scexaostatus', 'set', self.devname+'_st', 'UNKNOWN', '3'])
        """
        #else:
        #    self.usage()
        
# =====================================================================

    def usage(self):
        print("""---------------------------------------
Usage: %s <dev> <command> <arg>
---------------------------------------""" % (self.piconame,))
        print("DEV:")
        for i in range(len(self.axesnames)):
            print("    %-6s  move %s axis" % (self.axesnames[i], self.axesnames[i]))
        print("    status  status of the full device")
        print("""COMMAND:)
    status  displays status
      goto  moves to absolute position: numerical value
      push  moves to relative position: numerical value
     1 - %d defined positions""" % (self.nslots,))
        #if self.defpos != []:
        #    for i in range(len(self.defpos)):
        #        print("    %-6s  move stage to %s position" % (self.defpos[i], self.defpos[i]))
        print("""ARG:
    numerical value for position
CONTENT:""")
        for i in range(self.nslots):
            print("   ", self.param0[i], self.param1[i])
                        
        print("--------------------------------------- ")
    
    # -----------------------------------------------------------------
    def quickhelp(self):
        print("%20s       %s" % (self.piconame,self.description))
    
    # -----------------------------------------------------------------
    async def status(self):
        dev = await TCP.connect(self.picopath)
        print(dev)
        pos = await dev.get_position(self.picoid)
        print(pos)
        await dev.finish(self.picoid)

    """
    async def goto(self,pos):
        dev = await TCP.connect(self.picopath)
        dev.set_position(self.picoid,pos)
        pos = await dev.get_position(self.picoid)
        print(pos)
        await dev.finish(self.picoid)
    """

    async def push(self,motion):
        dev = await TCP.connect(self.picopath)
        dev.set_relative(self.picoid,motion)
        pos = await dev.get_position(self.picoid)
        print(pos)
        await dev.finish(self.picoid)

    async def goto_slot(self,slot):
        if (1 <= slot <= self.nslots):
            d = locals()
            exec("pos = self.param%d[slot-1]" %(self.col,), globals(), d)
            pos = d['pos']
            dev = await TCP.connect(self.picopath)
            dev.set_position(self.picoid,int(pos))
            pos = await dev.get_position(self.picoid)
            print(pos)
            await dev.finish(self.picoid)
            logit.logit(self.piconamep,'moved_to_slot_'+str(slot))
        else:
            print("Picomotor only has "+str(self.nslots)+" positions")

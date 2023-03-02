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
                        self.close()
                
                elif "status" in args[1].lower():
                    opened = self.open(self.micid)
                    if opened:
                        self.status(axisid)
                        self.close()
                    
                elif "goto" in args[1].lower():  #Goto commands
                    if isfloat(args[2]):
                        opened = self.open(self.micid)
                        if opened:
                            self.goto(axisid,float(args[2]))
                            self.close()
                    else:
                        self.usage()
                        
                elif args[1].isdigit():
                    slot = int(args[1])
                    opened = self.open(self.micid)
                    if opened:
                        self.goto_slot(slot, conu)
                        self.close()

            elif args[0].lower() in defpos:
                print("WORK IN PROGRESS")

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
            opened = False
        return opened

    def home(self, axisid):
        try:
            self.s.write("%iFBK3\r\n".encode() %axisid)
            time.sleep(1)
            self.s.write("%iHOM\r\n".encode() %axisid)
            time.sleep(1)
            self.s.write("%iZRO\r\n".encode() %axisid)
            time.sleep(0.2)
        except:
            print("CANNOT HOME AXIS")
    
    def status(self, axisid):
        self.s.write("%iPOS?\r\n".encode() %axisid)
        time.sleep(0.2)
        status = self.s.readlines()
        print(status)
        #except:
        #    print("STATUS UNKNOWN")
            
    def goto(self, axisid, pos):
        try:
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

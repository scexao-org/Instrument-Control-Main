#!/usr/bin/python

# ========================================================= #
#    ___                     _                      _       #
#   / _ \___ _ __   ___ _ __(_) ___    ___ ___   __| | ___  #
#  / /_\/ _ \ '_ \ / _ \ '__| |/ __|  / __/ _ \ / _` |/ _ \ #
# / /_\\  __/ | | |  __/ |  | | (__  | (_| (_) | (_| |  __/ #
# \____/\___|_| |_|\___|_|  |_|\___|  \___\___/ \__,_|\___| #
#                                                           #
#   __                  __  ___  __                         #
#  / _| ___  _ __    /\ \ \/ _ \/ _\                        #
# | |_ / _ \| '__|  /  \/ / /_)/\ \                         #
# |  _| (_) | |    / /\  / ___/ _\ \                        #
# |_|  \___/|_|    \_\ \/\/     \__/                        #
#                                                           #
# ========================================================= #
                                     
import socket
import random
import time
import sys
import string
import os
import subprocess

SCEXAO_NPS_IP = {1: "133.40.162.194",
                 2: "133.40.162.195",
                 3: "133.40.162.198"}

# =====================================================================
# =====================================================================

class nps:

    def __init__(self, npsname, npsid, portid, args=[], description="no description"):
        
        self.npsname = npsname
        self.description = description
        
        if args != [] and "--help1" in args[0]:
            self.quickhelp()
            sys.exit()

        self.npsid = npsid
        self.portid = portid
        
        na = args.__len__()
        
        if args == []:
            self.usage()
        
        elif "on" in args[0]:
            self.npson()
            
        elif "off" in args[0]:
            self.npsoff()

        elif "status" in args[0]:
            self.status()
            
        else:
            self.usage()

# =====================================================================

    def usage(self):
        print("""---------------------------------------
Usage: %s <command>
---------------------------------------
COMMAND:
    on      turns on
    off     turns off
    status  displays status
        ---------------------------------------""" % (self.npsname,))
    
    # -----------------------------------------------------------------
    def quickhelp(self):
        print("%20s       %s" % (self.npsname,self.description))

    # -----------------------------------------------------------------
    def npson(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((SCEXAO_NPS_IP[self.npsid], 23))
            sock.send("@@@@\r\n".encode())
            time.sleep(0.1)
            temp = sock.recv(1024)
            time.sleep(0.1)
            
            cmd = str.encode("N0%i\r\n" % (self.portid,))
            sock.send(cmd)
            time.sleep(1)
            temp = sock.recv(1024)
            subprocess.call(["scxkw-setter", "set", "nps%d_%d" %(self.npsid,self.portid), 'ON', '1'])
            time.sleep(0.1)
            sock.close()
            time.sleep(0.1)
            print(self.npsname+" is ON")
        except:
            print("""-------------------------------------------------------
nps_on could not connect to NPS.
check that environment variable NPS_IP is correctly set
-------------------------------------------------------""")

    # -----------------------------------------------------------------
    def npsoff(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((SCEXAO_NPS_IP[self.npsid], 23))
            sock.send("@@@@\r\n".encode())
            time.sleep(0.1)
            temp = sock.recv(1024)
            time.sleep(0.1)
            
            cmd = str.encode("F0%i\r\n" % (self.portid,))
            sock.send(cmd)
            time.sleep(1)
            temp = sock.recv(1024)
            subprocess.call(["scxkw-setter", "set", "nps%d_%d" %(self.npsid,self.portid), 'OFF', '0'])
            time.sleep(0.1)
            sock.close()
            time.sleep(0.1)
            print(self.npsname+" is OFF")
        except:
            print("""-------------------------------------------------------
nps_on could not connect to NPS.
check that environment variable NPS_IP is correctly set
-------------------------------------------------------""")

    # -----------------------------------------------------------------
    def status(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((SCEXAO_NPS_IP[self.npsid], 23))
            sock.send("@@@@\r\n".encode())
            time.sleep(0.1)
            temp = sock.recv(1024)
            time.sleep(0.1)
            
            cmd = "DN0\r\n".encode()
            sock.send(cmd)
            time.sleep(1)
            npsstatus = sock.recv(1024)
            npsstatus2 = npsstatus[npsstatus.find("OUTLET %i" % (self.portid,))+9:]
            npsstatus3 = npsstatus2[:npsstatus2.find("(")-1]
            if npsstatus3 == 'ON':
                col = '1'
            elif npsstatus3 == 'OFF':
                col = '0'
            else:
                col = '3'
            subprocess.call(["scxkw-setter", "set", "nps%d_%d" %(self.npsid,self.portid), npsstatus3, col])
            time.sleep(0.1)
            sock.close()
            time.sleep(0.1)
            print(self.npsname+" is "+npsstatus3)
            
        except:
            print("""-------------------------------------------------------
nps_on could not connect to NPS.
check that environment variable NPS_IP is correctly set
-------------------------------------------------------""")


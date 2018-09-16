#!/usr/bin/env python
import serial
import os
import time
import binascii
import sys
import pdb

delay=0.5
#45 degrees ~ 45-46 units

s=serial.Serial("/dev/ttyCONEX2",921600,timeout=0.5)

def usage():
    print """-------------------------------------
Usage: conex <dev> <command> <arg>
-------------------------------
dev:\n---
    wheel         manipulate conex wheel
command:\n-------
    home          sends the wheel to home
    goto          moves wheel to slot: numerical value
    status or ?   reports current position of wheel
arg:\n---
    numerical value (slot number)
    1-8 (wheel slot position)\n
examples:\n--------
    conex wheel home
    conex wheel goto 1 (change wheel slot)
    conex wheel status  
    conex wheel ?
-------------------------------"""
    sys.exit()


def move():
    args = sys.argv[1:]  # list of read arguments
    na = args.__len__()  # number of arguments
             
    if args == []: usage() 
   
    if "wheel" in args[0].lower():
        if "goto" in args[1].lower():
            if "1" in args[2].lower(): #PIAA_Bin
                s.write("1PA0.0\r\n")
                time.sleep(delay)
            elif "2" in args[2].lower(): #PIAA
                s.write("1PA45.0\r\n")
                time.sleep(delay)
            elif "3" in args[2].lower(): #PIAACMC
                s.write("1PA90.0\r\n")
                time.sleep(delay)
            elif "4" in args[2].lower(): #Open
                s.write("1PA135.0\r\n")
                time.sleep(delay)
            elif "5" in args[2].lower(): #Vortex
                s.write("1PA180.0\r\n")
                time.sleep(delay)
            elif "6" in args[2].lower(): #8OPM
                s.write("1PA225.0\r\n")
                time.sleep(delay)
            elif "7" in args[2].lower(): #4QPM
                s.write("1PA271.0\r\n")
                time.sleep(delay)
            elif "8" in args[2].lower(): 
                s.write("1PA315.0\r\n")
                time.sleep(delay)
            else:
                print("Wheel only has 8 positions")
            sys.exit()
        elif "home" in args[1].lower():
            s.write("1RS\r\n")
            time.sleep(delay)
            s.write("1OR\r\n")
        elif "status" in args[1].lower() or "?" in args[1].lower():
            s.write("1TP\r\n")
            time.sleep(delay)
            pos=s.readlines()
            pos=pos[0]
            pos=pos[3:]
            pos=pos[:-2]
            pos=round(float(pos),1)
            if pos == 0.0:
                print "Wheel is in slot 1"
            elif pos == 45.0:
                print "Wheel is in slot 2"
            elif pos == 90.0:
                print "Wheel is in slot 3"
            elif pos == 135.0:
                print "Wheel is in slot 4"
            elif pos ==180.0:
                print "Wheel is in slot 5"
            elif pos == 225:
                print "Wheel is in slot 6"
            elif pos == 270.0:
                print "Wheel is in slot 7"
            elif pos == 0.0:
                print "Wheel is in the home position"
            else:
                print "Wheel is not on a slot"
        else:
            usage()
    else:
        usage()

move()


s.close()

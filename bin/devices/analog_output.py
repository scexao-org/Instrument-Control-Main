#!/usr/bin/env python3
#waeE7124Nf
# ------------------------------------------------------------------- #
#    _               _                 ___       _               _    #
#   /_\  _ __   __ _| | ___   __ _    /___\_   _| |_ _ __  _   _| |_  #
#  //_\\| '_ \ / _` | |/ _ \ / _` |  //  // | | | __| '_ \| | | | __| #
# /  _  \ | | | (_| | | (_) | (_| | / \_//| |_| | |_| |_) | |_| | |_  #
# \_/ \_/_| |_|\__,_|_|\___/ \__, | \___/  \__,_|\__| .__/ \__,_|\__| #
#                            |___/                  |_|               #
# ------------------------------------------------------------------- #

import serial
import os
import time
import binascii
import sys
import numpy as np

home = os.getenv('HOME')
sys.path.append(home+'/src/lib/python/')
import logit #Custom logging library

aoname = "/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AH01JW35-if00-port0"
dcname = "/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A100L84Y-if00-port0"

brate = 9600 # baud rate for Weeder AI board
tout  = 0.1  # time out for serial connection (in sec)
delay = 0.05  # safety delay between send - receive 

class aoutput(object):
    def __init__(self, devname):
        self.s=serial.Serial(devname,brate,timeout=tout)
    
    def voltage(self,channel,voltage):
        #if "A"!=channel:
        if ("C"==channel) or ("D"==channel):
            if (float(voltage)>-9.0) and (float(voltage)<-1):
                volts=int(float(voltage)*100)
                text="AV"+str(channel)+str(volts)+"\r\n"
                self.s.write(text.encode())
            else:
                print("DC offsets must be between -1.0 and -9.0 V")
        else:
            volts=int(float(voltage)*100)
            text="AV"+str(channel)+str(volts)+"\r\n"
            self.s.write(text.encode())
            #if (float(volts>-1000)) and (float(volts<1000)):
            #else:
            #    print("Please enter a value between -10 and 10 V")
        #else:
        #    volts=float(voltage)
        #    text=':CHAN2:VOLT '+str(volts)+'; \r\n'
        #    self.s.write(text)
            
    
    def close(self):
        self.s.close()


def usage():
    print("""---------------------------------------
Usage: analog_out <command> <arg>
---------------------------------------
command:\n-------
    voltage  allows the voltage of a
             channel to be changed \n
arg 1:\n-----
    channel #  (A-D) 

arg 2:\n-----
    voltage    (-10 and 10)
    
examples:\n--------
    analog_out voltage A 0.8
    analog_out voltage C -5 \n

channel usage:\n-------------
    A - LVDS power supply (3.3 V)
    B - comparator voltage (0-1V)
    C - DC offset for tip (~-5V)
    D - DC offset for tilt (~-5V)
--------------------------------------- """)
    sys.exit()

def main():
    args = sys.argv[1:]  # list of read arguments
    na = args.__len__()  # number of arguments

    if args == []: usage()

    if "voltage" in args[0].lower():
        if na < 2:
            usage()
        elif (args[1]=="A") or (args[1]=="B") or (args[1]=="C") or (args[1]=="D"):
            if isinstance(float(args[2]),float):
                if (float(args[2])>-10) and (float(args[2])<10):
                    ao = aoutput(aoname)
                    ao.voltage(args[1],args[2])
                    ao.close()
                    #if args[1]!="A":
                    #else:
                    #    dc = aoutput(dcname)
                    #    dc.voltage(args[1],args[2])
                    #    dc.close()
                    logit.logit('Analog_output','Channel:'+str(args[1])+' Amplitude: '+str(args[2]))
                else:
                    print("Please enter a voltage between -10 and 10")
            else:
                print("Please enter a number between -10 and 10")
        else:
            print("Please enter a channel between A and D")

    else:
        usage()
    
if __name__ == "__main__":
    main()

#!/usr/bin/env python3

# ================================================= #
#                   _       _       _               #
#   /\/\   ___   __| |_   _| | __ _| |_ ___  _ __   #
#  /    \ / _ \ / _` | | | | |/ _` | __/ _ \| '__|  #
# / /\/\ \ (_) | (_| | |_| | | (_| | || (_) | |     #
# \/    \/\___/ \__,_|\__,_|_|\__,_|\__\___/|_|     #
#                                                   #
# ================================================= #

import serial
import os
import time
import binascii
import sys
import pdb
import numpy as np



home = os.getenv('HOME')
sys.path.append(home+'/bin/devices/')
import analog_output
sys.path.append(home+'/src/lib/python/')
import logit #Custom logging library

delay=0.5
relative=False
aoname="/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AH01JW35-if00-port0"
modname='/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A600KPDY-if00-port0'

class mod(object):
    def __init__(self,modname):
        self.s=serial.Serial(modname, 19200, timeout=0.5)
        
    def frequency(self,channel,freq):
        self.s.write(str.encode('F'+str(channel)+" "+str(freq)+'\r\n')) 

    def amplitude(self,channel,amp):
        if (float(amp)>=0) and (float(amp)<=1.0):
            amp=int(amp*1023)
            #print(amp)
            self.s.write(str.encode('V'+str(channel)+" "+str(amp)+'\r\n'))
        else:
            print("Enter a value between 0 and 1 V")

    def phase(self,channel,phas):
        phas=int(phas*16383/360)
        self.s.write(str.encode('P'+str(channel)+" "+str(phas)+'\r\n'))

    def status(self):
        self.s.readlines()
        self.s.write('QUE \r\n'.encode())
        output=self.s.readlines().decode()
        return(output)

    def save(self):
        self.s.write('s\r\n'.encode())

    def reset(self):
        self.s.write('r\r\n'.encode())

    def close(self):
        self.s.close()


def usage():
    print("""---------------------------------------
Usage: modulator <command> <arg>
---------------------------------------
command:\n-------
    status     displays waveform status
    frequency  allows the frequncy to 
               be changed: numerical 
               value 
    amplitude  allows the amplitude to
               be changed: numerical 
               value 
    phase      allows the phase to be 
               changed: numerical 
               value\n
arg:\n---
    numerical value in Hz (100-3500) 
    or V (0 and 1)
    or P (0 - 360 deg)
    
examples:\n--------
    modulator status
    modulator frquency 0.1 \n
--------------------------------------- """)
    sys.exit()


def main():
    args = sys.argv[1:]  # list of read arguments
    na = args.__len__()  # number of arguments

    if args == []: usage()

    if "status" in args[0].lower(): 
        modulate = mod(modname)
        stat=modulate.status()
        #print(stat)
        freq1 = int(stat[3][0:8],16)//10
        print("Channel 1 frequency: "+str(freq1)+" Hz")
        freq2 = int(stat[4][0:8],16)//10
        print("Channel 2 frequency: "+str(freq2)+" Hz")
        Amp1  = round(int(stat[3][14:18],16)/1023.,1)
        print("Channel 1 Amplitude: +/-"+str(Amp1)+" V pk-pk")
        Amp2  = round(int(stat[4][14:18],16)/1023.,1)
        print("Channel 2 Amplitude: +/-"+str(Amp2)+" V pk-pk")
        Phase1= round(int(stat[3][9:13],16)*360/16384.,1)
        print("Channel 1 Phase: "+str(Phase1)+" degrees")
        Phase2= round(int(stat[4][9:13],16)*360/16384.,1)
        print("Channel 2 Phase: "+str(Phase2)+" degrees")
        modulate.close()
        
    elif "frequency" in args[0].lower():
        if na < 2:
            usage()
        else:
            if isinstance(float(args[1]),float):
                if (float(args[1])>99) and (float(args[1])<3501):
                    modulate = mod(modname)
                    stat=modulate.status()
                    #print(stat)
                    Amp1 = round(int(stat[3][14:18],16)/1023.,1)
                    if int(args[1])==500:
                        ao = analog_output.aoutput(aoname)
                        volts = -1.0*Amp1
                        ao.voltage('A',volts)
                        ao.close()
                    elif int(args[1])==1000:
                        ao = analog_output.aoutput(aoname)
                        volts = -0.9*Amp1
                        ao.voltage('A',volts)
                        ao.close()
                    elif int(args[1])==1500:
                        ao = analog_output.aoutput(aoname)
                        volts = -0.8*Amp1
                        ao.voltage('A',volts)
                        ao.close()
                    elif int(args[1])==2000:
                        ao = analog_output.aoutput(aoname)
                        volts = -0.6*Amp1
                        ao.voltage('A',volts)
                        ao.close()
                    elif int(args[1])==2500:
                        ao = analog_output.aoutput(aoname)
                        volts = -0.35*Amp1
                        ao.voltage('A',volts)
                        ao.close()
                    elif int(args[1])==3000:
                        ao = analog_output.aoutput(aoname)
                        volts = -0.3*Amp1
                        ao.voltage('A',volts)
                        ao.close()
                    elif int(args[1])==3500:
                        ao = analog_output.aoutput(aoname)
                        volts = -0.3*Amp1
                        ao.voltage('A',volts)
                        ao.close()

                    freq=float(args[1])/1000000
                    modulate.frequency(2,freq)
                    modulate.frequency(3,freq)
                    modulate.save()
                    time.sleep(delay)
                    modulate.reset()
                    stat=modulate.status()
                    freq1 = int(stat[3][0:8],16)//10
                    print("Channel 1 frequency: "+str(freq1)+" Hz")
                    freq2 = int(stat[4][0:8],16)//10
                    print("Channel 2 frequency: "+str(freq2)+" Hz")
                    Amp1  = round(int(stat[3][14:18],16)/1023.,1)
                    print("Channel 1 Amplitude: +/-"+str(Amp1)+" V pk-pk")
                    Amp2  = round(int(stat[4][14:18],16)/1023.,1)
                    print("Channel 2 Amplitude: +/-"+str(Amp2)+" V pk-pk")
                    Phase1= round(int(stat[3][9:13],16)*360/16384.,1)
                    print("Channel 1 Phase: "+str(Phase1)+" degrees")
                    Phase2= round(int(stat[4][9:13],16)*360/16384.,1)
                    print("Channel 2 Phase: "+str(Phase2)+" degrees")
                    modulate.close()
                    logit.logit('Modulator','Frequency_changed_to_'+str(args[1])+'(MHz)')
                else:
                    print("Enter a frequency between 100 and 3500 Hz")
            else:
                print("Please enter a number between 100 and 3500 Hz")

    elif "amplitude" in args[0].lower():
        if na < 2:
            usage()
        else:
            modulate = mod(modname)
            stat=modulate.status()
            freq1 = int(stat[3][0:8],16)/10
            if freq1 == 500:
                ao = analog_output.aoutput(aoname)
                volts = -1.0*float(args[1])
                ao.voltage('A',volts)
                ao.close()
            elif freq1 == 1000:
                ao = analog_output.aoutput(aoname)
                volts = -0.9*float(args[1])
                ao.voltage('A',volts)
                ao.close()
            elif freq1 == 1500:
                ao = analog_output.aoutput(aoname)
                volts = -0.8*float(args[1])
                ao.voltage('A',volts)
                ao.close()
            elif freq1 == 2000:
                ao = analog_output.aoutput(aoname)
                volts = -0.6*float(args[1])
                ao.voltage('A',volts)
                ao.close()
            elif freq1 == 2500:
                ao = analog_output.aoutput(aoname)
                volts = -0.35*float(args[1])
                ao.voltage('A',volts)
                ao.close()
            elif freq1 == 3000:
                ao = analog_output.aoutput(aoname)
                volts = -0.3*float(args[1])
                ao.voltage('A',volts)
                ao.close()

            modulate.amplitude(2,float(args[1]))
            modulate.amplitude(3,float(args[1]))
            modulate.save()
            time.sleep(delay)
            #stat=mod.status()
            #print(stat)
            modulate.close()
            logit.logit('Modulator','Amplitude_changed_to_'+str(args[1])+'(V)')
    elif "phase" in args[0].lower():
        if na < 2:
            usage()
        else:
            modulate = mod(modname)
            modulate.phase(3,int(args[1]))
            modulate.save()
            time.sleep(delay)
            modulate.close()
            logit.logit('Modulator','Phase_changed_to_'+str(args[1])+'(P)')
            
    else:
        usage()
    
if __name__ == "__main__":
    main()





#500   -0.924
#1000  -0.707
#1500  -0.382
#2000  -0.03
#2500  -0.03
#3000  -0.03
#3500  -0.03

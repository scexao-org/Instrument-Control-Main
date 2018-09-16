#!/usr/bin/env python

import os, sys, socket, time, numpy, commands, binascii, datetime, math
import pyfits
import  sys
import numpy as np
import pyinotify as pn
import os
import array
import numpy as np
from math import *
import array
import matplotlib.pyplot as plt
import Image
import mmap
#from threading import Thread
import thread
import struct
import pytz

wder = "/media/scexao/data/20141106/Pyramid/Pyramid_"

index_cube = 0

s=""
if len(sys.argv)==2:
    s+="_"+sys.argv[1]
    

#----------Reading residuals-----------


b1 = shm('/tmp/aol2_DMmode_cmd1.im.shm', False)  # residuals
b2 = shm('/tmp/aol2_DMmode_cmd.im.shm', False)   # to be applied

b3 = shm('/tmp/aol2_DMmode_AVE.im.shm', False)
b4 = shm('/tmp/aol2_DMmode_LIMIT.im.shm', False)
b5 = shm('/tmp/aol2_DMmode_RMS.im.shm', False)
b6 = shm('/tmp/aol2_DMmode_GAIN.im.shm', False)

(xs, ys, zs) = struct.unpack('lll', b1[88:112])
(xsg, ysg, zsg) = struct.unpack('lll', b6[88:112])


#--- Lowfs COMMUNICATION SHARED MEMORY-----------------------

camid = 2 # camera identifier (1: LOWFS camera)
fd1  = os.open("/tmp/ircam%d.im.shm" % (camid,), os.O_RDWR)
buf1 = mmap.mmap(fd1, 0, mmap.MAP_SHARED)

(frm,) = struct.unpack('l', buf1[176:184])
(xsize, ysize, z) = struct.unpack('lll', buf1[88:112])

nel = xsize * ysize

#print "xs=%d,ys=%d -> nel = %d" % (xsize, ysize, nel)


# Reading Keywords
#---------------------
'''
# ON
x0 = 164040
print("Keywords\n--------")
print(str(buf1[x0:x0+16]).strip('\x00'))
print(str(buf1[x0+16]).strip('\x00'))
val, = struct.unpack('d', buf1[x0+17:x0+25])
print("value = %f" % (val,))
cmt = str(buf1[x0+25:x0+25+80]).strip('\x00')
print("comment: %s" % (cmt,))

# XOFFSET
x0 = 164145
print("Keywords\n--------")
print(str(buf1[x0:x0+20]).strip('\x00'))
print(str(buf1[x0+30:x0+50]).strip('\x00'))
val, = struct.unpack('d', buf1[x0+21:x0+29])
print("value = %f" % (val,))
cmt = str(buf1[x0+50:x0+50+80]).strip('\x00')
print("comment: %s" % (cmt,))

# YOFFSET
x0 = 164254
print("Keywords\n--------")
print(str(buf1[x0:x0+30]).strip('\x00'))
print(str(buf1[x0+40:x0+60]).strip('\x00'))
val, = struct.unpack('d', buf1[x0+31:x0+39])
print("value = %f" % (val,))
cmt = str(buf1[x0+60:x0+60+80]).strip('\x00')
print("comment: %s" % (cmt,))

x0 = 164363

# EXPOSURE TIME
#print("Keywords\n--------")
#print(str(buf1[x0:x0+50]).strip('\x00'))
#print(str(buf1[x0+50:x0+60]).strip('\x00'))
val, = struct.unpack('d', buf1[x0+61:x0+69])
#print("value = %f" % (val,))
cmt = str(buf1[x0+60:x0+60+80]).strip('\x00')
#print("comment: %s" % (cmt,))
'''
      


etimes = np.array([1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0, 500.0, 
                   1000.0, 2000.0, 5000.0, 10000.0, 20000.0, 50000.0,
                   100000.0, 200000.0, 500000.0]) # in microseconds

x0 = 164363
'''
def get_NB_frames():
    
    frames =0
    while True:       
        val, = struct.unpack('d', buf1[x0+61:x0+69])
        if val<= 1000.0:
            frames = 10000
            yield frames
        else:
            frames = 1000
            yield frames

frames_no = get_NB_frames()

for i in frames_no:
    NB_frames = i 
    print (NB_frames)

'''

NB_frames=5000

buffer_is_full=[0,0]
image_cube=[np.empty((NB_frames, ysize, xsize), dtype='uint32') , np.empty((NB_frames, ysize, xsize), dtype='uint32') ]
time_text=["",""]

#---  global double buffer and index
buffer_channel=0
loop_end = 0            
final_index_cube = 0

#--- Threads

def get_image():
    global buffer_channel
    global index_cube
    global buf1
    global loop_end
    global final_index_cube
    global NB_frames
    #cntro, = struct.unpack('l', buf1[8:16])
    cntro  = -1

    #cntro = struct.unpack('q', buf1[40032:40040])
    missed_cnt=0    

    while 1:

        cntr, = struct.unpack('l', buf1[176:184])
        wrt, = struct.unpack('i', buf1[168:172])
        val, = struct.unpack('d', buf1[x0+61:x0+69])

        myres   = np.fromstring(b1[200:200+4*xs],dtype=np.float32) 
        myresdm = np.fromstring(b2[200:200+4*xs],dtype=np.float32) 
        
        resX   = myres[0]
        resY   = myres[1]
        resZ   = myres[2]

        dmX   = myresdm[0]
        dmY   = myresdm[1]
        dmZ   = myresdm[2]

        Ave   = np.fromstring(b3[200:200+4*xs],dtype=np.float32) 

        AveX   = Ave[0]
        AveY   = Ave[1]
        AveZ   = Ave[2]

        Lim   = np.fromstring(b4[200:200+4*xs],dtype=np.float32) 

        LimX   = Lim[0]
        LimY   = Lim[1]
        LimZ   = Lim[2]


        rms   = np.fromstring(b5[200:200+4*xs],dtype=np.float32) 

        rmsX   = rms[0]
        rmsY   = rms[1]
        rmsZ   = rms[2]

        Gain = np.fromstring(b6[200:200+4*xsg*ysg],dtype=np.float32).reshape(ysg, xsg)
        
        GX   = Gain[0][0]
        GY   = Gain[0][1]
        GZ   = Gain[0][2]
       
         
        TGX   = Gain[1][0]
        TGY   = Gain[1][1]
        TGZ   = Gain[1][2]
       


       #print 'cntr=',cntr,'cntro=',cntro,'wrt=',wrt
    
        if wrt==0 and cntr!=cntro:
            image_cube[buffer_channel][index_cube] = get_lowfs_img() 
            #print "OK"
            cntr_end, = struct.unpack('l', buf1[176:184]) 
            img_tvsec   =  np.fromstring(buf1[144:152],dtype=np.uint64)
            img_tv_nsec =  np.fromstring(buf1[152:160],dtype=np.uint64)
       
            t      =  datetime.datetime.fromtimestamp(img_tvsec,tz=pytz.utc)
           # img_date="%02d-%02d-%02d-%06d"%(t.hour,t.minute,t.second,img_tv_nsec/1000)
            img_date="%04d/%02d/%02d %02d:%02d:%02d.%06d"%(t.year,t.month,t.day,t.hour,t.minute,t.second,img_tv_nsec/1000)

            #print 'cntr_end=',cntr_end,img_date
            if cntr ==cntr_end:
                #print "OK"
                index_cube=index_cube+1
                cntro=cntr          
                time_text[buffer_channel] += img_date+'     '+str(val)+'             '+str(cntr)+'        '+str(resX)+'       '+str(resY)+'     '+str(resZ)+'    '+str(dmX)+'     '+ str(dmY)+ '     '+str(dmZ)+'         ' +str(AveX)+'    '+str(AveY)+'    ' +str(AveZ)+ '   '  +str(LimX)+'     ' +str(LimY)+ '  ' +str(LimZ)+ '     ' +str(rmsX)+  '     '+str(rmsY)+ '      '+str(rmsZ)+ '      '+ str(GX)+ '    '+ str(GY)+ '    '+ str(GZ)+'    '+str(TGX)+'    '+str(TGY)+'    '+str(TGZ)+ '    '+"\n"

                print "%1d %8d%s" %(buffer_channel,index_cube,'\b'*11),
                print "%1d %8d %26s%s" %(buffer_channel,index_cube,img_date,'\b'*(11+26+1)),
                (xsize2, ysize2, z2) = struct.unpack('lll', buf1[88:112])
                if xsize != xsize2 or ysize !=ysize2:
                    loop_end=1
     
                if index_cube == NB_frames or loop_end==1:
                    final_index_cube = index_cube
                    index_cube = 0
                    if buffer_channel ==0:
                        buffer_channel =1
                        buffer_is_full[0]= 1
                    else:
                        buffer_channel =0
                        buffer_is_full[1]= 1
                    if loop_end==1:
                        time.sleep(1)  #wait save_data() to finish
                        sys.exit()
                else:
                    cntro=cntr              
                    missed_cnt=missed_cnt+1 
        else:
            missed_cnt=missed_cnt+1
   
        #print missed_cnt

def save_data():
    global buffer_channel
    global loop_end
    global final_index_cube 

    while 1:
        time.sleep(0.1)
        if buffer_is_full[0]==1 or buffer_is_full[1]==1 :
            buffer_channel_full = 1 - buffer_channel  # opposite to the current
            now=datetime.datetime.now(None)
            now=datetime.datetime.now(tz=pytz.utc)
            val, = struct.unpack('d', buf1[x0+61:x0+69])
            la_date=str(now.hour)+"_"+str(now.minute)+"_"+str(now.second)+"_"+str(now.microsecond)
            la_date="%02d:%02d:%02d.%06d"%(now.hour,now.minute,now.second,now.microsecond)
            #print " "*12 + "%15s"%la_date +" "*(26+1)+ "\b"*(27+26+1)
            print " "*12 + "saved as %s" %la_date +"\b"*(12+9+len(la_date)+1),
        
            ##### test
          
            pyfits.writeto(wder+str(la_date)+'_'+str(val)+"us"+s+".fits",image_cube[buffer_channel_full][0:final_index_cube], clobber=True)
        
            f=open(wder+str(la_date)+'_'+str(val)+"us"+s+".txt",'w')              
            f.write("Date...........UT..........Exposure Time......Frame number.....resX(um).......resY..........resZ......dmX......dmY....dmZ............AveX..........AveY..........AveZ............LimX........LimY.............LimZ...........ResX..............ResY.........ResY....... GX .......GY.......GZ........TGX......TGY.....TGZ \n")         
            f.write(time_text[buffer_channel_full])
            f.close()
            image_cube[buffer_channel_full] = np.empty((NB_frames, ysize, xsize), dtype='uint16')  
            buffer_is_full[buffer_channel_full] = 0
            time_text[buffer_channel_full] =""
            if loop_end==1:
                loop_end=2
                sys.exit()
    
 

def get_lowfs_img():
 
    myarr = np.fromstring(buf1[200:200+2*nel],dtype=np.ushort).reshape(ysize, xsize)

    return(myarr)


os.chdir('/home/scexao/src/lowfs/')

#---- main


#t=thread.start_new(get_NB_frames,())
t1=thread.start_new(get_image,())
t2=thread.start_new(save_data,())

while 1:
    ans = raw_input("finish? (y/n) [ENT]\n")

    if ans == "y":
        loop_end=1
        print "\ncube waiting to be filled\n"
        while 1:
            time.sleep(0.1)
            if loop_end==2:
                sys.exit()



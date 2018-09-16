#!/usr/bin/env python
import os
import commands
import numpy as np
import time

from lockfile import FileLock
import array

import mmap
import struct
import pdb

# ========================================================
#       CONNECTION WITH THE SCExAO INTERNAL CAMERAS
# ========================================================

home = os.getenv('HOME')
root_dir = home + '/src/OWLcam/'
fifocam_in = root_dir + 'fifo_in'
fifocam_ut = root_dir + 'fifo_out'

def cam_cmd(cmd, reply=False):
    os.system('echo "%s" > %s' % (cmd, fifocam_in,))
    res = None
    if reply:
        time.sleep(0.1)
        res = commands.getoutput('cat %s' % (fifocam_ut,))
    return(res)

def getfitsdata(imname):
    ''' quick interface to read current img from the temp dir '''
    with FileLock(imname):
        try:
            im = pf.getdata(imname)
        except:
            im = None
    return(im)

def getbindata(fname, xs=320, ys=256):
    ''' -------------------------------------------------
    Get binary data. Default assumed size is 320x256
    ------------------------------------------------- '''
    with FileLock(fname):
        try:
            a = array.array('H')
            a.fromfile(open(fname), xs*ys)
            im = np.array(np.split(np.array(a), ys))
        except:
            im = None
            print("Problem!")
    return(im)

# ------------------------------------------------------------------
#            acces to shared memory camera data
# ------------------------------------------------------------------
def getSMdata(fname, xs=320, ys=256):
    fd = os.open(fname, os.O_RDONLY)
    buf = mmap.mmap(fd, 0, mmap.MAP_SHARED, mmap.PROT_READ)

    on, = struct.unpack('i', buf[:4])
    fi, = struct.unpack('l', buf[8:16])
    st, = struct.unpack('i', buf[16:20])
    (xs,ys) = struct.unpack('ii', buf[20:28])
    (x0,y0) = struct.unpack('ii', buf[28:36])
    v0, = struct.unpack('H', buf[36:38])

    nel = xs*ys

    print("buffer length = %d" % (len(buf)))
    a = array.array('H')
    a.fromstring(buf[36:36+2*nel])
    im = np.array(np.split(np.array(a), ys))
            
    print("Camera is %d, frame # %d, status = %d" % (on, fi, st))
    print("Size = (%d, %d)" % (xs, ys))
    print("Orgn = (%d, %d)" % (x0, y0))

    print("First value: %d (of %d elements)" % (v0,nel))

    buf.close()
    os.close(fd)

    return(im)

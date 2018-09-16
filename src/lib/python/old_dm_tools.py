# ====================================================================
#            wrapper to select ramdisk or Shared Memory
# ====================================================================
def disp_2_DM(disp, channel=3):
    return (disp_2_DM_SM(disp, channel=channel))

def get_DM_disp(channel=3):
    return (get_DM_disp_SM(channel=channel))

# ====================================================================
#                       ramdisk file access
# ====================================================================

def disp_2_DM_RAM(disp, channel=3):
    ''' ------------------------------------------------------------
    sends a dms x dms disp map to the DM, using the provided 
    channel. For speckle control, the default channel is #3
    ------------------------------------------------------------ '''
    dmap = "/mnt/ramdisk/dmdisp%d.bin" % (channel,)
    try:
        with FileLock(dmap):
            f = open(dmap, 'w')
            f.write(np.hstack(disp.astype('f')))
            f.close()
    except:
        print("Could not access %s" %(dmap,))
        return None
    return True

def get_DM_disp_RAM(channel=3):
    ''' ------------------------------------------------------
    reads the provided channel number displacement map
    For speckle control, the default channel is #3
    Returns a 2d array.
    ------------------------------------------------------ '''
    dmap = "/mnt/ramdisk/dmdisp%d.bin" % (channel,)
    a = array.array('f')
    try:
        with FileLock(dmap):
            f = open(dmap, 'ro')
            a.fromfile(f, dms*dms)
            f.close()
    except:
        print("Could not access %s" %(dmap,))
        return None
    return(np.array(a).reshape(dms,dms))

# ====================================================================
#                      shared memory file access
# ====================================================================

def disp_2_DM_SM(disp, channel=3):
    ''' ------------------------------------------------------------
    sends a dms x dms disp map to the DM shared memory data structure,
    using the provided channel. 
    For speckle control, the default channel is #3
    ------------------------------------------------------------ '''
    sz = 4*dms*dms
    dmap = "/tmp/dmdisp%d-sm.bin" % (channel,)
    fd = os.open(dmap, os.O_RDWR)
    buf = mmap.mmap(fd, 0, mmap.MAP_SHARED)

    aa = array.array('f', (np.hstack(disp.astype('f'))).tolist())

    cnt, = struct.unpack('q', buf[sz+8:sz+16]) # get current counter value
    buf[sz:sz+8]    = struct.pack('q', 1)      # set write flag to 1
    buf[0:sz]       = aa.tostring()            # write the disp array
    buf[sz+8:sz+16] = struct.pack('q', cnt+1)  # update counter
    buf[sz:sz+8]    = struct.pack('q', 0)      # set write flag to 0

    buf.close()
    os.close(fd)
    return True

def get_DM_disp_SM(channel=3):
    ''' ------------------------------------------------------
    reads the provided channel number displacement map
    from the shared memory structure defined by OG in 
    "/src/DMcontrol/dm_dispcomb/dm_dispcomb.h".

    For speckle control, the default channel is #3
    Returns a 2d array.
    ------------------------------------------------------ '''
    sz = 4*dms*dms
    dmap = "/tmp/dmdisp%d-sm.bin" % (channel,)
    fd = os.open(dmap, os.O_RDONLY)
    buf = mmap.mmap(fd, 0, mmap.MAP_SHARED, mmap.PROT_READ)

    a = array.array('f')
    a.fromstring(buf[0:sz])
    
    #print struct.unpack('qq', buf[sz:sz+16])

    buf.close()
    os.close(fd)

    return(np.array(a).reshape(dms,dms))

def get_channel_counter_SM(channel):
    sz = 4*dms*dms
    dmap = "/tmp/dmdisp%d-sm.bin" % (channel,)
    fd = os.open(dmap, os.O_RDONLY)
    buf = mmap.mmap(fd, 0, mmap.MAP_SHARED, mmap.PROT_READ)
    cnt, = struct.unpack('q', buf[sz+8:sz+16]) # get current counter value
    buf.close()
    os.close(fd)
    return(cnt)

def current_DM_counter_SM():
    sz = 4*dms*dms
    dmap = "/tmp/dmdisp-sm.bin"
    fd = os.open(dmap, os.O_RDONLY)
    buf = mmap.mmap(fd, 0, mmap.MAP_SHARED, mmap.PROT_READ)

    cnt, = struct.unpack('q', buf[sz+8:sz+16]) # get current counter value

    buf.close()
    os.close(fd)
    return(cnt)
    




def add_DM_sine(amp, kx, ky, phi=0.0, chn=3):
    ''' -----------------------------------------
    plays a sine wave on the surface of the DM:
    - amp: speckle amplitude in um
    - kx:  x-spatial frequency
    - ky:  y-spatial frequency
    - phi: phase offset of the sine wave
    - chn: DM channel to process
    ----------------------------------------- '''
    sz = dms # 2k-DM diameter (in actuators)
    x,y = np.meshgrid(np.arange(sz)-sz/2, np.arange(sz)-sz/2)
    phase = 2*np.pi*(kx*x+ky*y) + phi
    depl = amp * np.sin(phase)

    fname = '/mnt/ramdisk/dmdisp%d.bin' % (chn,)
    disp = get_DM_disp(chn)+depl
    disp_2_DM(disp, chn)

def init_DM_channel(chn=3):
    OK = False
    while not OK:
        OK = disp_2_DM(np.zeros((dms, dms)), chn)
    return(True)

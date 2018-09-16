import os
import mmap
import struct
import ctypes
import numpy as np
import time
import array

class shm:
    ''' -------------------------------------------------------------
    Shared memory data structure for images and volt maps for SCExAO
    Definition is available in ~/src/Cfits/src/CLIcore.h
    ------------------------------------------------------------- '''

    # ==========================
    def __init__(self, fname=None, data=None, verbose=True):
        if fname == None:
            print("No shared memory file name provided")
            return(None)

        if ((not os.path.exists(fname))):
            print("Shared mem structure %s will be created" % (fname,))
            self.create(fname, data)
        else:
            self.fd = os.open(fname, os.O_RDWR)
            fname2 = os.path.basename(fname)
            fname3 = os.path.splitext(fname2)[0]
            fname4 = os.path.splitext(fname3)[0]
            self.fname = fname4
            self.buf = mmap.mmap(self.fd, 0, mmap.MAP_SHARED)
            self.read_meta_data(verbose=verbose)
            self.get_data()

    # ==========================
    def create(self, fname, data=None):

        kws = 200 # for later: keyword section size...

        conv = {'str'    : 1, # conversion table: ndtype -> shm-code
                'int32'  : 2,
                'float32': 3,
                'float64': 4,
                'uint16' : 7}

        if data == None:
            print("No data (ndarray) provided!")
            return(False)
        else:
            # anticipate shm data structure size
            # ----------------------------------
            self.ddtype = data.dtype    # data-type in numpy format
            self.elt_sz = data.itemsize # size of array element in bytes
            self.nel    = data.size     # number of array elements
            self.fname = fname

            self.naxis  = np.size(data.shape)
            temp = [0,0,0]
            temp[:self.naxis] = data.shape
            self.size = tuple(temp)
            xs, ys, zs = self.size
            self.idtype = conv[data.dtype.name]
            # create the file
            # ---------------
            fsz = 200+self.nel*self.elt_sz + kws
            npg = fsz / mmap.PAGESIZE + 1 # number of PAGES 2 be allocated

            self.fd = os.open(fname, os.O_CREAT | os.O_TRUNC | os.O_RDWR)
            os.write(self.fd, '\x00' * npg * mmap.PAGESIZE)
            self.buf = mmap.mmap(self.fd, npg * mmap.PAGESIZE, 
                                 mmap.MAP_SHARED, mmap.PROT_WRITE)

            self.buf[80:88]   = struct.pack('l', self.naxis)
            self.buf[88:112]  = struct.pack('lll',  xs, ys, zs)
            self.buf[112:120] = struct.pack('l', self.nel)
            self.buf[120:128] = struct.pack('l', self.idtype)
            self.buf[128:136] = struct.pack('d', 0.0) # creation    time
            self.buf[136:144] = struct.pack('d', 0.0) # last access time

            self.buf[164:168] = struct.pack('i', 0) # share  flag
            self.buf[168:172] = struct.pack('i', 0) # write  flag
            self.buf[172:176] = struct.pack('i', 0) # status flag

            #self.buf[176:184] = struct.pack('',)
            #self.buf[184:192] = struct.pack('',)
            #self.buf[192:200] = struct.pack('',)

            self.set_data(data)
            return(True)

    # ==========================
    def close(self,):
        self.buf.close()
        os.close(self.fd)

    # ==========================
    def read_meta_data(self, verbose=True):
        buf = self.buf
        self.imname  = str(buf[0:80]).strip('\x00')       # image name
        self.naxis,  = struct.unpack('l',   buf[80:88])   # array dimension
        self.size    = struct.unpack('lll', buf[88:112])  # array size
        self.nel,    = struct.unpack('l',   buf[112:120]) # nb. elements
        self.idtype, = struct.unpack('l',   buf[120:128]) # image dtype
        self.crtime, = struct.unpack('d',   buf[128:136]) # creation time
        self.latime, = struct.unpack('d',   buf[136:144]) # last access time

        self.shared, = struct.unpack('i',   buf[164:168]) # flag
        self.write,  = struct.unpack('i',   buf[168:172]) # flag

        self.status, = struct.unpack('i',   buf[172:176])   
        self.cnt0,   = struct.unpack('l',   buf[176:184]) # counter
        self.cnt1,   = struct.unpack('l',   buf[184:192]) # counter
        self.nbkw    = struct.unpack('l',   buf[192:200]) # nb of keywords

        self.elt_sz = 2
        self.ddtype = np.int32

        if self.idtype == 1: # C-char
            self.elt_sz = 1
            self.ddtype = np.str

        if self.idtype == 2: # C-long
            self.elt_sz = 4
            self.ddtype = np.int32
                
        if self.idtype == 3: # C-float
            self.elt_sz = 4 
            self.ddtype = np.float32

        if self.idtype == 4: # C-double
            self.elt_sz= 8
            self.ddtype = np.float64

        if self.idtype == 7: # C-ushort
            self.elt_sz= 2
            self.ddtype = np.ushort

        if verbose:
            print("imname = %s"             % (self.imname,))
            print("naxis = %d"              % (self.naxis,))
            print("xs, ys, zs = %d, %d, %d" %  self.size)
            print("image data type %d"      % (self.idtype,))
            print("image counter = %d"      % (self.cnt0,))
            print("SHARED %d"               % (self.shared,))

    # ==========================
    def get_data(self,check=False,reform=True, sleepT=0.001, timeout=5):
        if check:
            time0 = time.time()
            timen = time.time()
            cnt, = struct.unpack('l',   self.buf[176:184]) # current counter val
            while (cnt <= self.cnt0) and (timen-time0 < timeout):
                time.sleep(sleepT)
                cnt, = struct.unpack('l',   self.buf[176:184])
                timen = time.time()
            self.cnt0 = cnt
            
        data = np.fromstring(
            self.buf[200:200+self.nel*self.elt_sz], dtype=self.ddtype)

        if reform:
            data = data.reshape(self.size[:self.naxis][::-1])

        return(data)

    # ==========================
    def get_counter(self):
        self.cnt0,   = struct.unpack('l',   self.buf[176:184]) # counter
        return self.cnt0

    # ==========================
    def set_data(self, data):
        conv = {'str'    : 'c', # conversion table: ndtype -> shm-code
                'int32'  : 'i',
                'float32': 'f',
                'float64': 'd',
                'uint16' : 'h'}

        dt = conv[data.dtype.name]

        aa = array.array(dt, (np.hstack(data.astype(dt))).tolist())
        try:
            self.buf[200:200+self.nel*self.elt_sz] = aa.tostring()
            counter, = struct.unpack('l', self.buf[176:184])
            counter += 1
            self.buf[176:184] = struct.pack('l', counter)
            if  ((("dm" in self.fname) and ("disp" in self.fname)) or ("blobcam" in self.fname)):
                os.system("imsempost %s"%(self.fname,))
            status = True
        except:
            print("Failed to write buffer to shared mem structure")
            status = False
        return(status)

    # ==========================
    def set_data0(self, data):
        aa = array.array('f', (np.hstack(data.astype('f'))).tolist())
        try:
            self.buf[200:200+self.nel*self.elt_sz] = aa.tostring()
            counter, = struct.unpack('l',   self.buf[176:184])
            counter += 1
            self.buf[176:184] = struct.pack('l', counter)
            if  ((("dm" in self.fname) and ("disp" in self.fname)) or ("blobcam" in self.fname)):
                os.system("imsempost %s"%(self.fname,))
        except:
            print("Failed to write buffer to shared mem structure")
        return(True)

    # ==========================
    def save_as_fits(self, fitsname):
        '''Rudimentary fits file export

        Should eventually include keywords information.
        '''
        pf.writeto(fitsname, self.get_data(), clobber=True)

    # ==========================
    def get_expt(self):
        x0 = 164363
        self.expt, = struct.unpack('d', self.buf[x0+61:x0+69])
        return self.expt
    
    # ==========================
    def set_expt(self, expt):
        try:
            x0 = 164363
            self.buf[x0+61:x0+69] = struct.pack('d', expt)
        except:
            print("failed to write exposure time")
        return(True)

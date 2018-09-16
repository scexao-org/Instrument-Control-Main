import os
import mmap
import struct
import ctypes
import numpy as np
import time
import array

class StructStatus(ctype.Structure):
     _fields_ = [('src_fib_st',c_char*16),
                 ('int src_fib_co',c_int),
                 ('src_fib',c_float),
                 ('oap1_st',c_char*16),
                 ('oap1_co',c_int),
                 ('oap1_theta',c_float),
                 ('oap1_phi',c_float),
                 ('oap1_f',c_int),
                 ('dichroic_st',c_char*16),
                 ('dichroic_co',c_int),
                 ('dichroic',c_float),
                 ('pupil_st',c_char*16),
                 ('pupil_co',c_int),
                 ('pupil_wheel',c_float),
                 ('pupil_x',c_int),
                 ('pupil_y',c_int),
                 ('piaa1_st',c_char*16),
                 ('piaa1_co',c_int),
                 ('piaa1_wheel',c_float),
                 ('piaa1_x',c_int),
                 ('piaa1_y',c_int),
                 ('piaa2_st',c_char*16),
                 ('piaa2_co',c_int),
                 ('piaa2_wheel',c_float),
                 ('piaa2_x',c_int),
                 ('piaa2_y',c_int),
                 ('piaa2_f',c_int),
                 ('nuller_pickoff_st',c_char*16),
                 ('nuller_pickoff_co',c_int),
                 ('nuller_pickoff',c_float),
                 ('PG1_pickoff',c_char*16),
                 ('PG1_pickoff_co',c_int),
                 ('fpm_st',c_char*16),
                 ('fpm_co',c_int),
                 ('fpm_wheel',c_float),
                 ('fpm_x',c_int),
                 ('fpm_y',c_int),
                 ('fpm_f',c_int),
                 ('lyot_st',c_char*16),
                 ('lyot_co',c_int),
                 ('lyot_wheel',c_float),
                 ('lyot_x',c_int),
                 ('lyot_y',c_int),
                 ('invpiaa_st',c_char*16),
                 ('invpiaa_co',c_int),
                 ('invpiaa_x',c_float),
                 ('invpiaa_y',c_float),
                 ('invpiaa_theta',c_int),
                 ('invpiaa_phi',c_int),
                 ('intsphere',c_char*16),
                 ('intsphere_co',c_int),
                 ('charis_pickoff_st',c_char*16),
                 ('charis_pickoff_co',c_int),
                 ('charis_pickoff',c_float),
                 ('mkids_pickoff_st',c_char*16),
                 ('mkids_pickoff_co',c_int),
                 ('mkids_pickoff',c_float),
                 ('ircam_filter',c_char*16),
                 ('ircam_filter_co',c_int),
                 ('ircam_block',c_char*16),
                 ('ircam_block_co',c_int),
                 ('pcfi_pickoff_st',c_char*16),
                 ('pcfi_pickoff_co',c_int),
                 ('pcfi_pickoff',c_float),
                 ('ircam_fcs_st',c_char*16),
                 ('ircam_fcs_co',c_int),
                 ('ircam_fcs',c_int),
                 ('saphira_pickoff_st',c_char*16),
                 ('saphira_pickoff_co',c_int),
                 ('saphira_pickoff',c_float),
                 ('chuck_pup',c_char*16),
                 ('chuck_pup_co',c_int),
                 ('fibinj_pickoff_st',c_char*16),
                 ('fibinj_pickoff_co',c_int),
                 ('fibinj_pickoff',c_float),
                 ('fibinj_fib_st',c_char*16),
                 ('fibinj_fib_co',c_int),
                 ('fibinj_fib_x',c_int),
                 ('fibinj_fib_y',c_int),
                 ('fibinj_fib_f',c_int),
                 ('fibinj_car',c_int),
                 ('PG2_pickoff',c_char*16),
                 ('PG2_pickoff_co',c_int),
                 ('lowfs_block',c_char*16),
                 ('lowfs_block_co',c_int),
                 ('lowfs_fcs',c_int),
                 ('pcfi_len_st',c_char*16),
                 ('pcfi_len_co',c_int),
                 ('pcfi_len',c_float),
                 ('pcfi_fib_st',c_char*16),
                 ('pcfi_fib_co',c_int),
                 ('pcfi_fib_x',c_float),
                 ('pcfi_fib_y',c_float),
                 ('pcfi_fib_f',c_float),
                 ('polarizer_st',c_char*16),
                 ('polarizer_co',c_int),
                 ('polarizer',c_float),
                 ('pywfs_pickoff_st',c_char*16),
                 ('pywfs_pickoff_co',c_int),
                 ('pywfs_pickoff',c_float),
                 ('pywfs_filter',c_char*16),
                 ('pywfs_filter_co',c_int),
                 ('pywfs_col',c_int),
                 ('pywfs_fcs',c_int),
                 ('pywfs_pup_x',c_int),
                 ('pywfs_pup_y',c_int),
                 ('first_pickoff_st',c_char*16),
                 ('first_pickoff_co',c_int),
                 ('first_pickoff',c_float),
                 ('rhea_pickoff_st',c_char*16),
                 ('rhea_pickoff_co',c_int),
                 ('rhea_pickoff',c_float),
                 ('first_photometry_x1_st',c_char*16),
                 ('first_photometry_x1_co',c_int),
                 ('first_photometry_x1',c_float),
                 ('first_photometry_x2_st',c_char*16),
                 ('first_photometry_x2_co',c_int),
                 ('first_photometry_x2',c_float),
                 ('src_select_st',c_char*16),
                 ('src_select_co',c_int),
                 ('src_select',c_float),
                 ('src_flux_irnd',c_char*16),
                 ('src_flux_optnd',c_char*16),
                 ('src_flux_filter',c_char*16),
                 ('logchuck',c_char*16),
                 ('logchuck_co',c_int),
                 ('darkchuck',c_char*16),
                 ('darkchuck_co',c_int),
                 ('hotspot',c_char*16),
                 ('hotspot_co',c_int)]


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
            self.ddtype = np.short

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
    

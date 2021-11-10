#
# Ag.py -- AG client module
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Jun 14 17:08:17 HST 2012
#]
#
#
import sys, os, time
import socket
import threading, Queue

import rpc
import pyfits, numpy
import Bunch
import SOSS.SOSSrpc as SOSSrpc

import ag_vgwpacker
import ag_vgwtypes
import ag_vgwconstants


# Version
version = "20110421.0"

# Id codes that appear in the header string of the RPC message
# Source        Dest   Program Number             Header
# ---------------------------------------------------------
# HSC AG for SC VGW    HSCSCAG_VGW_PRG=0x20000032 AGSC,003D
# HSC AG for SC TWS1/2 HSCSCAG_VGW_PRG=0x20000033 AGSC,003D
# HSC AG for SH VGW    HSCSHAG_VGW_PRG=0x20000034 SHAG,003E
# HSC AG for SH TWS1/2 HSCSHAG_VGW_PRG=0x20000035 SHAG,003E
# HSC SH        VGW    HSCSH_VGW_PRG=0x20000036   SH%%,003F
# HSC SH        TWS1/2 HSCSH_VGW_PRG=0x20000037   SH%%,003F
# 
# I don't know about the header. For AG, SH, SV, and FMOS, they are
# AG%%,0006, SH%%,0009, SV%%,0007, and OBCP,003B, respectively.

ag_info = {
    'AG': dict(id='AG%%', code='0006',
               foci={'PFVS': dict(ccdx=512, ccdy=512,
                                  degx=0.000026093, degy=0.000026093),
                     'PIR%': dict(ccdx=512, ccdy=512,
                                  degx=0.000026093, degy=0.000026093),
                     'CASS': dict(ccdx=512, ccdy=512,
                                  degx=0.000026044, degy=0.000026044),
                     'NSIR': dict(ccdx=512, ccdy=512,
                                  degx=0.000023825, degy=0.000023823),
                     'NSOP': dict(ccdx=512, ccdy=512,
                                  degx=0.000025252, degy=0.000025252),
                     }),
    'SV': dict(id='SV%%', code='0007',
               foci={'CASS': dict(ccdx=512, ccdy=512,
                                  degx=0.000034722, degy=0.000034722),
                     'NSOP': dict(ccdx=512, ccdy=512,
                                  degx=0.000034722, degy=0.000034722),
                     }),
    'SH': dict(id='SH%%', code='0009',
               foci={'PFVS': dict(ccdx=512, ccdy=512,
                                  degx=0.000056106, degy=0.000056106),
                     'PIR%': dict(ccdx=512, ccdy=512,
                                  degx=0.000056106, degy=0.000056106),
                     'CASS': dict(ccdx=512, ccdy=512,
                                  degx=0.000026044, degy=0.000026044),
                     'NSIR': dict(ccdx=512, ccdy=512,
                                  degx=0.000023825, degy=0.000023825),
                     'NSOP': dict(ccdx=512, ccdy=512,
                                  degx=0.000025252, degy=0.000025252),
                     }),
    'FMOS': dict(id='OBCP', code='003B',
                 foci={'FMOS': dict(ccdx=640, ccdy=480,
                                    degx=0.0000, degy=0.0000),
                       }),
    'HSCSCAG': dict(id='AGSC', code='003D',
                    #foci={'PVFS': dict(ccdx=1024, ccdy=1024,
                    foci={'PVFS': dict(ccdx=512, ccdy=512,
                                       degx=0.1600, degy=0.1600),
                          }),
    'HSCSHAG': dict(id='SHAG', code='003E',
                    foci={'PVFS': dict(ccdx=640, ccdy=480,
                                       degx=0.0000, degy=0.0000),
                          }),
    'HSCSH': dict(id='SH%%', code='003F',
                  foci={'PVFS': dict(ccdx=1024, ccdy=1024,
                                     degx=0.0000, degy=0.0000),
                        }),
    }

# Allowable AG types
ag_types = ag_info.keys()

# Make a reverse lookup map from the unique code
ag_map = {}
for key in ag_types:
    ag_map[ ag_info[key]['code'] ] = (key, ag_info[key])

# AG -> AGFILTER
# SH -> SHFILTER
# SV (0.0/1.0/2.0/3.0) ->  NoFilter/Filter1/Filter2/NDFilter
ag_filter = { 'AG': "AGFILTER",
              'SH': "SHFILTER",
              0.0: "NoFilter",
              1.0: "Filter1",
              2.0: "Filter2",
              3.0: "NDFilter",
              }

# adu conversion factor (electron/ADU)    
ag_gain = { 'AG': 1.0, 'SV': 1.0, 'SH': 1.0 }

# foci full name
ag_foci = { 'CASS': 'Cassegrain',
            'NSOP': 'Nasmyth-Opt',
            'NSIR': 'Nasmyth-IR',
            'PFVS': 'Prime',
            'PIR%': 'Prime',
            'COUD': 'Coude',
            }

# Template string for AG header.  Copied from DAQvgwAgClnt.c, et. al.
ag_head_templ = "%(insCode)4.4s%(insName)4.4s%(foci)4.4s%(binX)1.1sx%(binY)1.1s%%%(expRangeX)04d%(expRangeY)04d%(expRangeDX)04d%(expRangeDY)04d%(expTime)08du%%16%(dataKind)02d%(numPixX)04d%(numPixY)04d      "

header_conversions = {
    # e.g,  0006 AG%% CASS  1x1%  0195  0161  0151  0151  00000560 u%    16    01    0151  0151   RESERVED
    #       0-4  4-8  8-12  12-16 16-20 20-24 24-28 28-32 32-40    40-42 42-44 44-46 46-50 50-54  54-60                       
    'insCode'   : ((0, 4), str),         # guider camera code (unique)
    'insName'   : ((4, 6), str),         # guider camera name (not unique)
    'foci'      : ((8, 12), str),        # foci of camera
    'binX'      : ((12, 13), int),       # binning in X (1, 2, 4, 8)
    'binY'      : ((14, 15), int),       # binning in Y (1, 2, 4, 8)
    'expRangeX' : ((16, 20), int),       # exposure range X
    'expRangeY' : ((20, 24), int),       # exposure range Y
    'expRangeDX': ((24, 28), int),       # exposure range delta X
    'expRangeDY': ((28, 32), int),       # exposure range delta Y
    'expTime'   : ((32, 40), int),       # exposure time in msec
    'dataType'  : ((40, 42), str),       # data type i%|u%|f%|d%)
    'pixBit'    : ((42, 44), int),       # bits per pixel (e.g. 16)
    'dataKind'  : ((44, 46), str),       # data kind 01|02|03|04|05
    'numPixX'   : ((46, 50), int),       # image width (number of pixels in X)
    'numPixY'   : ((50, 54), int),       # image height (number of pixels in Y)
    'reserve'   : ((54, 60), str),
    }

# NOTES:
# Looking at SOSS VGW code, the following values are set in their "header"
# (these are all ints)
#  iBin <- 1, 2, 4, 8 
#  iX <- exposure range X (gen2: expRangeX)
#  iY <- exposure range Y (gen2: expRangeY)
# iDX <- exposure range delta X (gen2: expRangeDX)
# iDY <- exposure range delta X (gen2: expRangeDY)
# iPixDX <- image number of pixels wide (X axis) (gen2: numPixX)
# iPixDY <- image number of pixels high (Y axis) (gen2: numPixY)
# iDataSize <- iPixDX * iPixDY  (total number of datums)
# iExpTime <- exposure time (msec) (gen2: expTime)
# iFlg <- On/Off flag which indicates reception of valid data
#
# Not in the structure but referenced:
# iHost <- 0=AG, 1=SV 2=SH  (AG is reused for FMOS)
# iKind <- the data kind  
#
# [a] Binning gets reduced to a single number (1, 2, 4, or 8), depending
#     on whether the value is 1x1, 2x2, 4x4 or 8x8).  Supposedly SH binning
#     should never be 4 or 8.
# [ ] VGW expects that:
#      iPixDX == floor(iDX / iBin)
#      iPixDY == floor(iDY / iBin)
#      iDX % iBin == 0
#      iDY % iBin == 0
#      iDX / iBin == iPixDX
#      iDY / iBin == iPixDY
# [ ] VGW never expects any other data type than '%u' (16 bit unsigned int)
# [ ] VGW never expects any other size of pixBit except '16'
# [ ] Data kinds are '01' (normal), '02' (dark), '03' (flat), '04' (sky),
#     '05' (bias).  VGW changes these to ordinal values indexed from 0;
#     i.e. 0=normal (aka 'object'), 1=dark, 2=flat, 3=sky, 4=bias
#     However, for SV, data "kind" is looked up in a stored VGW variable
#     (sent previously by an a priori "EXEC VGW SV_DATA_TYPE" command).
# Time values sent from the telescope are discarded and the times passed
#   to VGW subsystems are calculated as the time the data was received
        
def getHeaderValue(headerStr, key):
    try:
        range    = header_conversions[key][0]
        convfunc = header_conversions[key][1]
        return convfunc(headerStr[range[0]:range[1]])
    except:
        return None

def getHeaderBunch(headerStr):
    """Return a Bunch containing all the AG header items."""
    res = Bunch.Bunch()
    for key in header_conversions.keys():
        res[key] = getHeaderValue(headerStr, key)

    return res

class AgError(Exception):
    pass
    
class AgClientError(AgError):
    pass
    
class AgServerError(AgError):
    pass
    
# Base class for making RPC calls to the VGW AG RPC services.
#
class AgClientBase(object):

    def __init__(self):
        pass

    # Add the packers and unpackers for AgClient calls.  This is somehow
    # invoked from the rpc.py package.
    #
    def addpackers(self):
        self.packer = ag_vgwpacker.AG_VGWPacker()
        self.unpacker = ag_vgwpacker.AG_VGWUnpacker('')

    #
    # RPC procedures
    #
    def unpack_void(self):
        """NOP stub function for unpacking void return type.
        """
        return None

    # This implements the client call to the AG RPC server.
    #
    def agproc_vgw_cmd(self, head, tv_sec, tv_usec, data):

        # Head will be packed as farray, packer seems to require sequence
        # of ints
        head_as_arr = map(ord, head)

        args = ag_vgwtypes.tgVform(head_as_arr, tv_sec, tv_usec, data)
        res = self.make_call(ag_vgwconstants.AGPROC_VGW_CMD, args,
                             self.packer.pack_tgVform,
                             #self.unpacker.unpack_bool)
                             self.unpack_void)

        return res


class UDP_AgClient(AgClientBase, rpc.UDPClient):
    """Subclass implementing specific UDP RPC interface to AG image receiver.
    """
    def __init__(self, host, prognum,
                 version=ag_vgwconstants.AGPROC_VGW_VERS,
                 uid=os.getuid(), gid=os.getgid(),
                 sec=(rpc.AUTH_UNIX, None)):
        rpc.UDPClient.__init__(self, host, prognum, version, sec)
        AgClientBase.__init__(self)
        self.uid = uid
        self.gid = gid


class TCP_AgClient(AgClientBase, rpc.TCPClient):
    """Subclass implementing specific TCP RPC interface to AG image receiver.
    """
    def __init__(self, host, prognum,
                 version=ag_vgwconstants.AGPROC_VGW_VERS,
                 uid=os.getuid(), gid=os.getgid(),
                 sec=(rpc.AUTH_UNIX, None)):
        rpc.TCPClient.__init__(self, host, prognum, version, sec)
        AgClientBase.__init__(self)
        self.uid = uid
        self.gid = gid


class AgClient(object):
    def __init__(self, tgthost, agtype, logger, transport='auto'):

        # Record RPC preferences for later lazy client creation
        self.tgthost = tgthost
        self.agtype = agtype
        self.transport = transport
        self.rpcclient = None
        self.logger = logger

        # Look up RPC parameters
        try:
            key = ("%stoVGW" % self.agtype)
            prgnums = SOSSrpc.lookup_rpcsvc(key)

        except KeyError, e:
            raise AgServerError("Error looking up rpc parameters")

        self.prognum = prgnums.server_receive_prgnum
        self.version = ag_vgwconstants.AGPROC_VGW_VERS
        

    # Make the RPC client 
    def _mk_client(self):

        self.logger.info("Making client on demand to host %s" % self.tgthost)
        try:
            # Create the rpc client
            if self.transport == "auto":
                # Try TCP first, then UDP, according to RFC2224
                try:
                    cl = TCP_AgClient(self.tgthost, self.prognum,
                                      version=self.version)
                except socket.error:
                    self.logger.debug("TCP Connection refused, trying UDP")
                    cl = UDP_AgClient(self.tgthost, self.prognum,
                                      version=self.version)
            elif self.transport == "tcp":
                cl = TCP_AgClient(self.tgthost, self.prognum,
                                      version=self.version)
            elif self.transport == "udp":
                cl = UDP_AgClient(self.tgthost, self.prognum,
                                      version=self.version)
            else:
                raise RuntimeError, "Invalid protocol"

            self.rpcclient = cl
            #cl.voidrtn = True
            return

        except (rpc.PortMapError, socket.error), e:
            self.rpcclient = None
            msg = "Cannot create RPC client: %s'" % (str(e))
            self.logger.error(msg)
            raise AgClientError(msg)
            

    def format_head(self, agType, agFocus, numPixX, numPixY,
                    iBinning=1, iKind=1, expRangeX=None, expRangeY=None,
                    expRangeDX=None, expRangeDY=None, expTime=1000):
        """Formats the header of an AG packet.
        """
        agid = ag_info[agType]['id']
        agcode = ag_info[agType]['code']
        agwd = ag_info[agType]['foci'][agFocus]['ccdx']
        aght = ag_info[agType]['foci'][agFocus]['ccdy']

        if expRangeX == None:
            expRangeX = 0
        if expRangeY == None:
            expRangeY = 0
        if expRangeDX == None:
            expRangeDX = agwd
        if expRangeDY == None:
            expRangeDY = aght
            
        d = {'insCode': agcode,
             'insName': agid,
             'foci'   : agFocus,
             'binX'   : iBinning,
             'binY'   : iBinning,
             'expRangeX': expRangeX,
             'expRangeY': expRangeY,
             'expRangeDX': expRangeDX,
             'expRangeDY': expRangeDY,
             'expTime': expTime,
             'dataKind':  iKind,
             'numPixX': numPixX,
             'numPixY': numPixY,
             }
        hdr = ag_head_templ % d
        print "|%s|" % hdr
        assert len(hdr) == 60, AgClientError("AG Header does not meet required size (%d != 60)" % len(hdr))
        
        return hdr


    def send_ag(self, header, tv_sec, tv_usec, data):
        """Sends a packet of AG data.  _header_ is the TSC-formatted AG packet
        header, _tv_sec_ and _tv_usec_ encode the time of the data image
        capture, and _data_ is a 16-bit int array of pixel data.

        Generally clients should call 
        """

        # Lazy client creation, prevents problems if server is not up
        # before client
        if not self.rpcclient:
            self._mk_client()

        self.logger.debug("calling host '%s'" % (self.tgthost))
        try:
            res = self.rpcclient.agproc_vgw_cmd(header, tv_sec, tv_usec, data)

        except Exception, e:
            # Possibly stale RPC client, try resetting it...
            # this may raise a AgClientError
            self.logger.error("Error calling RPC: %s" % str(e))
            self.logger.info("possibly stale client, resetting...")
            self._mk_client()

            # Now try again, one more time...
            try:
                res = self.rpcclient.agproc_vgw_cmd(header, tv_sec, tv_usec,
                                                    data)

            except Exception, e:
                self.rpcclient = None
                raise AgClientError("RPC call to send data failed: %s" % str(e))
            
        self.logger.debug("host returned '%s'" % (str(res)))
        return res


    def sendAgData(self, agType, agFocus, datatime, data_np,
                    iBinning=1, iKind=1, expRangeX=None, expRangeY=None,
                    expRangeDX=None, expRangeDY=None, expTime=1000):
        """Send an AG image.
        _agType_   = { AG | SV | SH | FMOS | HSCSCAG | HSCSHAG | HSCSH }
        _agFocus_  = { PFVS | PIR% | FMOS| CASS | NSOP | NSIR }
        _iBinning_  = AG binning to BINNING (1:1x1, 2:2x2, 4:4x4, 8:8x8)
        _iKind_     = AG data kind to KIND (1:Obj, 2:Dark, 3:Flat, 4:Sky, 5: Bias)
        _datatime_ = time of the exposure as a float
        _data_np_  = array of pixel data as a numpy
        """

        # Get dim of data size for calculating header
        (height, width) = data_np.shape

        # Sanity check on type
        if not (agType in ag_types):
            raise AgClientError("agType (%s) must be in %s" % (
                agType, str(ag_types)))

        aginfo = ag_info[agType]
        
        # Sanity check on foci
        if not (agFocus in aginfo['foci']):
            raise AgClientError("agFocus (%s) must be in %s" % (
                agFocus, str(aginfo['foci'])))
        
        # Sanity check on binning
        if not (iBinning in (1, 2, 3, 4)):
            raise AgClientError("binning (--bin) must be in range 1-4")
        
        # Sanity check on kind
        if not (iKind in (1, 2, 3, 4)):
            raise AgClientError("data kind (--kind) must be in range 1-4")
        
        # Make TSC-compatible AG header
        agheader = self.format_head(agType, agFocus, width, height,
                                    iBinning=iBinning, iKind=iKind,
                                    expRangeX=expRangeX, expRangeY=expRangeY,
                                    expRangeDX=expRangeDX,
                                    expRangeDY=expRangeDY,
                                    expTime=expTime)

        # Get time as two integers: sec and usec (required in this format
        # by the RPC call)
        (sec_str, usec_str) = str(datatime).split('.')
        sec  = int(sec_str)
        usec = int(usec_str)

        # Massage data into RPC-compatible format (flat)
        # NOTE: this is done already in the packer
        #data_np = data_np.astype('UInt16').flatten()

        # Send image to target
        return self.send_ag(agheader, sec, usec, data_np)

        
    def sendAgFITS(self, agType, agFocus, fitsobj, datatime=None,
                   iBinning=1, iKind=1, expRangeX=None, expRangeY=None,
                   expRangeDX=None, expRangeDY=None, expTime=1000):

        hdu = fitsobj[0]

        if not datatime:
            datatime = time.time()
        
        return self.sendAgData(agType, agFocus, datatime, hdu.data,
                               iBinning=iBinning, iKind=iKind,
                               expRangeX=expRangeX, expRangeY=expRangeY,
                               expRangeDX=expRangeDX,
                               expRangeDY=expRangeDY,
                               expTime=expTime)


    def sendAgFile(self, agType, agFocus, fitspath, datatime=None,
                   iBinning=1, iKind=1, expRangeX=None, expRangeY=None,
                   expRangeDX=None, expRangeDY=None, expTime=1000):

        try:
            fitsobj = pyfits.open(fitspath, 'readonly')

        except IOError, e:
            raise AgClientError("Cannot open FITS file '%s'" % (fitspath))

        try:
            return self.sendAgFITS(agType, agFocus, fitsobj, datatime=datatime,
                                   iBinning=iBinning, iKind=iKind,
                                   expRangeX=expRangeX, expRangeY=expRangeY,
                                   expRangeDX=expRangeDX,
                                   expRangeDY=expRangeDY,
                                   expTime=expTime)

        finally:
            fitsobj.close()


class AgReceiver(SOSSrpc.TCP_rpcServer):
    
    def __init__(self, prognum, progver=1, host='', port=None, ev_quit=None,
                 logger=None, queue=None):

        super(AgReceiver, self).__init__(prognum, progver=progver,
                                         host=host, port=port, ev_quit=ev_quit,
                                         logger=logger, queue=queue)
                
    def addpackers(self):
        self.packer = ag_vgwpacker.AG_VGWPacker()
        self.unpacker = ag_vgwpacker.AG_VGWUnpacker(False)


    def handle_1(self):

        # unpack data
        cur_time = time.time()

        try:
            agpkt = self.unpacker.unpack_tgVform()

            self.logger.debug("unpack time: %8.4f" % (
                time.time() - cur_time))

            self.rpcqueue.put(agpkt)

        except Exception, e:
            self.logger.error("Error unpacking RPC parameters: %s" % str(e))
               
        try:
            self.turn_around()
            
        except rpc.RPCUnextractedData:
            self.logger.error("*** Unextracted Data in request!")

        # this RPC returns void
        return rpc.VOID_RTN
    

class AgServer(object):
    
    def __init__(self, logger, host='', port=None, ev_quit=None, queue=None,
                 timeout=0.1, delta=1.0, agtype='AG'): 
              
        # Look up RPC parameters
        try:
            key = ("%stoVGW" % agtype)
            prgnums = SOSSrpc.lookup_rpcsvc(key)

        except KeyError, e:
            raise AgServerError("Error looking up rpc parameters")

        self.prognum = prgnums.server_receive_prgnum
        self.version = ag_vgwconstants.AGPROC_VGW_VERS
        self.host = host
        self.port = port

        self.params = Bunch.threadSafeBunch()
        # If new image is received in less than delta seconds, it is
        # dropped.
        self.params.delta = delta
        self.last_time = 0.0
        self.lock = threading.RLock()
        
        self.agtype = agtype
        self.rpcserver = None

        self.logger = logger
        if not ev_quit:
            self.ev_quit = threading.Event()
        else:
            self.ev_quit = ev_quit
        if not queue:
            self.queue = Queue.Queue()
        else:
            self.queue = queue
        self.timeout = timeout

        self.reset_server()

        super(AgServer, self).__init__()


    def reset_server(self):
        # Create RPC server
        self.rpcserver = AgReceiver(self.prognum, progver=self.version,
                                    host=self.host, port=self.port,
                                    ev_quit=self.ev_quit, logger=self.logger,
                                    queue=self.queue)

    def start(self):
        self.rpcserver.start()
        
    def stop(self, wait=True):
        self.rpcserver.stop(wait=wait)

    def restart(self):
        self.stop(wait=True)
        self.reset_server()
        self.start()
        
    def set_delta(self, delta):
        self.params.delta = delta
       
    def mainloop(self):

        self.logger.info("Starting processing of AG packets")

        while not self.ev_quit.isSet():

            try:
                agpkt = self.queue.get(block=True, timeout=self.timeout)

                start_time = time.time()
                
                # continue processing if at least delta seconds
                # has elapsed since last packet
                delta = self.params.delta
                if (start_time - self.last_time) < delta:
                    self.logger.debug("dropping packet received under delta %-.4f" % (
                        delta))
                    continue

                self.last_time = start_time
            
                # extract ag header (it is in an array format)
                agheader_str = ''.join(map(chr, agpkt.head))

                # hack to remove trailing nulls in the string
                i = agheader_str.find('\0')
                if i > 0:
                    agheader_str = agheader_str[:i]

                # convert it into a record of typed values
                aghdr = getHeaderBunch(agheader_str)

                # Extract size of image data from header
                width  = aghdr.numPixX
                height = aghdr.numPixY
                reported_data_size = width * height
                data_len = len(agpkt.data)

                # check that header and actual data size match
                if reported_data_size != data_len:
                    raise AgServerError("data size mismatch: hdr=%d data=%d" % (
                        reported_data_size, data_len))
                  
                # Convert time back to a float (ugh!)
                datatime = float('%d.%d' % (agpkt.tv_sec, agpkt.tv_usec))

                # Reshape AG data to 2-dim array
                # TODO: should this be done in the unpacker?
                data_np = numpy.reshape(agpkt.data, (height, width))

                split_time = time.time()
                
                # Process the data
                # IDEA: make a "fits object" out of the data here
                # to encapsulate AG interface detail in the header
                self.process(aghdr, datatime, data_np)

                end_time = time.time()
                elapsed_time = end_time - start_time
                self.logger.debug("time: setup=%-.4f process=%-.4f total=%-.4f" % (
                    (split_time - start_time),
                    (end_time - split_time), elapsed_time) )

                if elapsed_time > self.params.delta:
                    self.logger.warn("elapsed time exceeded delta by: %-.4f sec" % (
                        elapsed_time - self.params.delta))

            except Queue.Empty:
                continue
            
            except KeyboardInterrupt, e:
                raise e
            
            except Exception, e:
                self.logger.error("Exception raised processing data: %s" % (
                    str(e)))

        self.logger.info("Stopping processing of AG packets")


    def process(self, agheader, datatime, data_np):
        """Process AG data packet.
        _agheader_ is a bunch corresponding to the AG header data.
        _datatime_ is the data time (as float) of the data.
        _data_np_ is a numpy 2-dim array of the pixel data.

        Subclass should override this to customize their own processing.
        """
        self.logger.debug("time: %8.4f  header: %s" % (datatime, str(agheader)))

 
# END


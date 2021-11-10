#! /usr/bin/env python
#
# SOSS_frame -- Retrieve frame ids from SOSS via RPC
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Sep 23 16:14:40 HST 2009
#]
#
#
# remove once we're certified on python 2.6
from __future__ import with_statement

import sys, os, socket
import threading

import rpc
import SOSS.SOSSrpc as SOSSrpc
from cfg.INS import INSdata as INSconfig
import logging, ssdlog

from OSSS_Frameconstants import *
from OSSS_Frametypes import *
import OSSS_Framepacker


class frameError(Exception):
    """ Class for all exceptions thrown by methods in the SOSS frame module
    """
    pass


    ################################################
    #    OSSS_FrameSvc RPC INTERFACE STUFF
    ################################################


# Base class for making RPC calls to the SOSS OSSS_Frame service.
#
class OSSS_FRAMEClient(object):

    def __init__(self):
##         super(OSSS_FRAMEClient, self).__init__(prognum, logger=logger,
##                                                ev_quit=ev_quit)
        pass

    def addpackers(self):
        """Add the packers and unpackers for OSSS_Frame calls.  This is
        invoked from the rpc.py package.
        """
        self.packer = OSSS_Framepacker.OSSS_FRAMEPacker()
        self.unpacker = OSSS_Framepacker.OSSS_FRAMEUnpacker('')

    #
    # RPC procedures
    # These implement the client calls to the OSSS_Frame RPC server.
    #

    #   unit : 'SUKA', 'FLDMON', etc.
    #   type : 'A' or 'Q'
    #   dno  : dispatcher number  : 0,1,2-6 (can be '0')
    #   num  : number (can be '0')
    #
    def OSSs_GET_FNO(self, unit, type, dno, num):
        args = GetFnoArgs(unit, type, dno, num)
        res = self.make_call(OSSs_GET_FNO, args, \
                             self.packer.pack_GetFnoArgs, \
                             self.unpacker.unpack_string)

        return res


    #   str  : frame id to reset the frame counter
    #
    def OSSs_SET_FNO(self, str):
        res = self.make_call(OSSs_SET_FNO, str, \
                             self.packer.pack_string, \
                             self.unpacker.unpack_string)

        return res


class rpcFrameObj(object):
    """ Implements a Python interface to the SOSS frame id server.

    Example usage:
    ...
    import SOSS.frame
    ...
    frameSvc = SOSS.frame.rpcFrameObj('obs')

    frameid = frameSvc.get_frame('FLDMON', 'A')
    """

    def __init__(self, host, transport='auto'):

        # Record RPC preferences for later lazy client creation
        self.transport = transport
        self.framehost = host
        self.rpcclient = None


    # Make the RPC client 
    def _mk_client(self):

        try:
            # Create the rpc client
            if self.transport == "auto":
                # Try TCP first, then UDP, according to RFC2224
                try:
                    cl = TCP_OSSS_FRAMEClient(self.framehost)
                except socket.error:
                    # print "TCP Connection refused, trying UDP"
                    cl = UDP_OSSS_FRAMEClient(self.framehost)
            elif transport == "tcp":
                cl = TCP_OSSS_FRAMEClient(self.framehost)
            elif transport == "udp":
                cl = UDP_OSSS_FRAMEClient(self.framehost)
            else:
                raise RuntimeError, "Invalid protocol"

            self.rpcclient = cl
            return

        except (rpc.PortMapError, socket.error), e:
            self.rpcclient = None
            raise frameError('Cannot create RPC client: %s' % (str(e)))
            
        
    # Make an rpc call to get a frame id for the given instrument and type.
    #
    def get_frame(self, inst, frametype, num=1):

        # Lazy client creation, prevents problems if server is not up
        # before client
        if not self.rpcclient:
            self._mk_client()

        num_str = '%d' % num
        try:
            res = self.rpcclient.OSSs_GET_FNO(inst, frametype, '0', num_str)

        except Exception, e:
            # Possibly stale RPC client, try resetting it...
            # this may raise a frameError
            self._mk_client()

            # Now try again, one more time...
            try:
                res = self.rpcclient.OSSs_GET_FNO(inst, frametype, '0', num_str)

            except Exception, e:
                self.rpcclient = None
                raise frameError("RPC call to get frame failed: %s" % str(e))
            
        return res


    def set_frame(self, inst, frametype, num):
        raise frameError("Operation not yet implemented")
    

class TCP_OSSS_FRAMEClient(OSSS_FRAMEClient, rpc.TCPClient):
    """Subclass implementing specific TCP RPC interface to OSSS_Frame
    """
    def __init__(self, host, uid=os.getuid(), gid=os.getgid(),
                 #sec=(rpc.AUTH_UNIX, None)
                 sec=(rpc.AUTH_NULL, None)
                 ):
        rpc.TCPClient.__init__(self, host, OSSS_Frame, \
                               OSSS_FrameVersion, sec)
        OSSS_FRAMEClient.__init__(self)
        self.uid = uid
        self.gid = gid


class UDP_OSSS_FRAMEClient(OSSS_FRAMEClient, rpc.UDPClient):
    """Subclass implementing specific UDP RPC interface to OSSS_Frame
    """
    def __init__(self, host, uid=os.getuid(), gid=os.getgid(),
                 #sec=(rpc.AUTH_UNIX, None)
                 sec=(rpc.AUTH_NULL, None)
                 ):
        rpc.UDPClient.__init__(self, host, OSSS_Frame, \
                               OSSS_FrameVersion, sec)
        OSSS_FRAMEClient.__init__(self)
        self.uid = uid
        self.gid = gid


    
class OSSS_FRAMEServer(SOSSrpc.TCP_rpcServer):

    def __init__(self, prognum=OSSS_Frame, logger=None, ev_quit=None,
                 frame_func=None):
        super(OSSS_FRAMEServer, self).__init__(prognum, logger=logger,
                                               ev_quit=ev_quit)

        if not frame_func:
            frame_func = self.getFrames
        self.frame_func = frame_func
        self.lock = threading.RLock()
        # used if we need to implement our own frame server
        self.counts = {}
        self.insconfig = INSconfig()

    def setCounts(self, counts):
	self.counts = counts


    def addpackers(self):
        """Add the packers and unpackers for OSSS_Frame calls.  This is
        invoked from the rpc.py package.
        """
        self.packer = OSSS_Framepacker.OSSS_FRAMEPacker()
        self.unpacker = OSSS_Framepacker.OSSS_FRAMEUnpacker('')

    #
    # RPC procedures
    # These implement the server functions of the OSSS_Frame RPC server.
    #

    def handle_1(self):
        """Handles the call GET_FNO(unit, type, dno, num) (see OSSS_Frame.x)
        """
        data = self.unpacker.unpack_GetFnoArgs()

        if self.logger:
            self.logger.info(str(data))       
        try:
            self.turn_around()
            
        except rpc.RPCUnextractedData:
            self.logger.error("*** Unextracted Data in request!")

        # Get parameters
        insname = data.unit
        frametype = data.type.upper()
        # interestingly, specified as a string in OSSS_Frame.x
        count = int(data.num)

        single = False
        if count == 0:
            count = 1
            single = True

        # Get the frames
        try:
            (res_code, framelist) = self.frame_func(insname, frametype, count)

        except Exception, e:
            self.logger.error("Error getting frames: %s" % (str(e)))
            framelist = []

        if res_code != 0:
            self.logger.error("Error getting frames: res=%d" % (res_code))
            framelist = []

        # Check that desired count was achieved
        if len(framelist) != count:
            self.logger.error("Counts don't match: %d != %d",
                              (count, len(framelist)))
            res = "ERROR"
        
        elif single:
            res = framelist[0]

        else:
            res = ('%s:%04d' % (framelist[0], count))
        
        # Return result
        self.packer.pack_string(res)


    def getFrames(self, insname, frametype, count):
        """Simple frame function to use if we are not given something
        more sophisticated in the constructor.
        """

        with self.lock:
            error = False

            # Convert instrument name to code (i.e. 'SPCAM' --> 'SUP'
            try:
                inscode = self.insconfig.getCodeByName(insname)

            except KeyError:
                self.logger.error("Invalid instrument name: %s" % insname)
                error = True

            # Check requested frame type is valid
            if frametype not in ('A', 'Q'):
                self.logger.error("Invalid frame type: %s" % frametype)
                error = True

            if error:
                return (1, [])

            fr_num = self.counts[inscode]
            self.counts[inscode] += count
            res = []

            for i in xrange(count):
                res.append('%3.3s%1.1s%08d' % (inscode, frametype, fr_num+i))

            return (0, res)
    

def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('frames', options)

    ev_quit = threading.Event()

    svr = OSSS_FRAMEServer(OSSS_Frame, logger, ev_quit=ev_quit)

    if options.counts:
	xxx = options.counts.split(',')
	counts = {}
	for yyy in xxx:
	    (inscode, count) = yyy.split(':')
            counts[inscode.upper()] = int(count)
        svr.setCounts(counts)

    try:
        try:
            logger.info("Starting frame server.")
            svr.start()

            while True:
                print "Press ^C to terminate server..."
                sys.stdin.readline()
            
        except KeyboardInterrupt:
            logger.error("Caught keyboard interrupt!")

        except Exception, e:
            logger.error("Frame server raised exception: %s" % str(e))

    finally:
        logger.info("Stopping frame server.")
        svr.stop(wait=True)

        logger.info("Program end.")
        
        
if __name__ == '__main__':

    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%prog'))
    
    optprs.add_option("--counts", dest="counts", default=None,
                      help="Initial frame counts")
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-n", "--obcpnum", dest="obcpnum", type="int",
                      default=9,
                      help="Use NUM as the OBCP number", metavar="NUM")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    if len(args) != 0:
        optprs.error("incorrect number of arguments")


    # Are we debugging this?
    if options.debug:
        import pdb

        pdb.run('main(options, args)')

    # Are we profiling this?
    elif options.profile:
        import profile

        print "%s profile:" % sys.argv[0]
        profile.run('main(options, args)')

    else:
        main(options, args)


# END SOSS_frame.py

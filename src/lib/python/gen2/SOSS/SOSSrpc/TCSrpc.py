#
# TCSrpc.py -- (aks "TSC") rpc interface base class
#
# Bruce Bon (Bruce.Bon@SubaruTelescope.org)  2006-11-21
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Feb 11 16:50:22 HST 2008
#]
#
"""This module provides classes describing the formats of Subaru Telescope
Control System RPC messages, and convenience methods for packing and unpacking
them.
"""
import types
import os, time
import common
from common import rpcMsgError


class TCScmdRpcMsgError(common.rpcMsgError):
    pass

class TCSstatRpcMsgError(common.rpcMsgError):
    pass


TCS_STATUS_HOST = "TSC%"


def time2timestamp(sectime=None):
    """Converts a Python time float in UT into a TCS-style RPC UT timestamp 
       (a string in the form YYYYMMDDhhmmsss, where sss is in deciseconds)."""

    if not sectime:
        sectime = time.time()   # UT
    # A little wierdness here because TCS uses no decimal points, i.e.
    # represents seconds as an integer in units of 0.1 sec
    dsec = ('%.1f' % sectime)[-1]
    # Currently the field width and precision are not supported under Solaris Python 2.3
    # return time.strftime(t2tsStrFmt, time.gmtime(sectime)) + dsec
    return time.strftime("%Y%m%d%H%M%S", time.gmtime(sectime)) + dsec


def timestamp2time(timestamp_str):
    """Converts a TCS-style UT timestamp (a string in the form 
    YYYYMMDDhhmmsss, where sss is in deciseconds) into a Python UT
    time float."""
    ts2tStrFmt = "%Y%m%d%H%M%S"
    
    head = timestamp_str[0:14]
    tail = timestamp_str[14:15] 
    tup = time.strptime(head, ts2tStrFmt)
    # mktime treats its argument as a localtime(), i.e. HST, so we
    # must subtract 10 hours (36000.0 seconds)
    return time.mktime(tup) + float('0.'+tail) - 36000.0


def time2HSTtimestamp(sectime=None):
    """Converts a Python time float in UT into an HST timestamp string,
    in the form YYYY-MM-DD hh:mm:ss.s ."""

    #t2HtsStrFmt = "%4Y-%2m-%2d %2H:%2M:%2S"
    t2HtsStrFmt = "%Y-%m-%d %H:%M:%S"
    
    if not sectime:
        sectime = time.time()   # UT
    # Get deci-seconds with decimal point
    dsec = ('%.1f' % sectime)[-2:]
    return time.strftime(t2HtsStrFmt, time.gmtime(sectime))+dsec  # HST


######################################################################
################   declare rpcHeader class   #########################
######################################################################

class TCSstatRpcHeader(object):
    """TCS RPC Header Class.  This is a container for RPC header
    parameters.
    """
   
    def __init__(self, rpcmsg=None):
        """Constructor.  Calls load(rpcmsg) to extract header parameters if
           an RPC message is provided; else calls sethdr() to set default
           header parameters."""

        self.len_hdr = 33

        if rpcmsg:
            self.load( rpcmsg )     # must be a packed RPC message type
        else:
            self.sethdr()

    def load(self, rpcmsg):
        """Extract RPC parameters from message header in rpcmsg into rpcHeader
           variables.  Use this method to parse a message that was received.

           NOTE: for TCSL and TCSS interfaces (see STATint), rpcmsg is
           an object that has the actual message imbedded in a "contents" 
           attribute;  therefore, the header and payload fields must be
           extracted from rpcmsg.contents.  For all other TCS interfaces,
           the header and payload fields must be extracted from rpcmsg.  

           If a ValueError or IndexError is detected, raises rpcMsgError."""

        # Mark time received 
        self.timerecd = time2timestamp()

        # Extract string message if necessary
        if  type(rpcmsg) != types.StringType:
            rpcmsg = rpcmsg.contents

        # Parse fields of header
        #? print 'rpcmsg = ',rpcmsg
        try:
            self.msg_type        = rpcmsg[0:2]
            self.rcvr_host       = rpcmsg[2:6]
            self.send_host       = rpcmsg[6:10]
            self.proc_id_str     = rpcmsg[10:14]
            self.proc_id         = int( self.proc_id_str )
            self.msg_time_str    = rpcmsg[14:29]
            self.msg_time        = timestamp2time( self.msg_time_str )
            self.len_payload_str = rpcmsg[29:33]
            self.len_payload     = int( self.len_payload_str )
            self.len_total       = self.len_hdr + self.len_payload
            self.payload   = rpcmsg[self.len_hdr:self.len_hdr+self.len_payload]

        except ValueError, e:
            raise rpcMsgError("malformed TCS rpc message: '%s'" % rpcmsg)
        except IndexError, e:
            raise rpcMsgError("malformed TCS rpc message: '%s'" % rpcmsg)

    def str(self):
        """Format header into a string for printing, logging, etc."""
        return 'TSC rpc msg: typ %s, rcvr %s, sndr %s, pid %s, time %s' % \
               ( self.msg_type, self.rcvr_host, self.send_host,
                 self.proc_id_str, self.msg_time_str )

    def sethdr( self, rcvr_host=TCS_STATUS_HOST, msg_type='CD', payload='' ):
        """Set RPC header parameters into rpcHeader variables.
           Use this method to initialize a message that is to be sent."""
        self.msg_type        = msg_type
        if  len(rcvr_host) >= 4:
            self.rcvr_host   = rcvr_host[0:4]           # truncate
        else:   # < 4
            self.rcvr_host   = (rcvr_host+'%%%')[0:4]   # pad with %
        myhost               = common.get_myhost(short=True)
        if  len(myhost) >= 4:
            self.send_host   = myhost[0:4]              # truncate
        else:   # < 4
            self.send_host   = (myhost+'%%%')[0:4]      # pad with %
        self.send_host       = '%4s' % myhost
        self.proc_id         = os.getpid()
        self.proc_id_str     = '%4d' % self.proc_id
        self.msg_time_str    = time2timestamp()
        self.msg_time        = timestamp2time( self.msg_time_str )
        self.len_payload     = len(payload)
        self.len_payload_str = "%d" % self.len_payload
        self.payload         = payload
        self.len_total       = self.len_hdr + self.len_payload

######################################################################
################   declare rpcMsg class   ############################
######################################################################

class TCSstatRpcMsg(TCSstatRpcHeader):
    """TCS RPC Message Class.  Inherits from rpcHeader.  Includes methods for
       setting the message data payload and formatting a complete packet,
       including RPC header and data payload.  Set functions for the
       data payload are customized for the various TCS message types."""

    def __init__(self, rpcmsg=None, **kwdargs):
        """Constructor.  Initializes RPC header from rpcmsg, then
           sets overrides from kwdargs."""

        TCSstatRpcHeader.__init__(self, rpcmsg)

        # overrides
        self.set(**kwdargs)

    #
    # Public methods
    #

    def packet2str(self):
        """Build an TCS RPC packet string, including header parameters and
           the data payload."""

        # Sets self.payload -- does nothing unless method overridden by subclass
        self.pack_payload()

        pkt = self.msg_type + self.rcvr_host + self.send_host + \
              self.proc_id_str + self.msg_time_str + self.len_payload_str + \
              self.payload
        
        return pkt

    def set(self, **kwdargs):
        """Convenience function for setting message header values.  Set 
           arbitrary rpcMsg variables from keyword arguments provided by 
           the caller."""
        self.__dict__.update(kwdargs)

    def pack_payload(self):
        """Does nothing.  May be overridden by a subclass to pack its 
           own payload on a packet2str."""
        pass

    def __str__(self):
        return self.packet2str()

#END

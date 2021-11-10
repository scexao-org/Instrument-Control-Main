#
# rpc.py - RFC1057/RFC1831
#
# Copyright (C) 2005-2009 Subaru Telescope, NAOJ (http://subarutelescope.org/)
# All rights reserved.
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri May  6 16:04:51 HST 2011
#]
# 
# Copyright (C) 2001 Cendio Systems AB (http://www.cendio.se)
# All rights reserved.
# 
# Copyright (c) 2001 Python Software Foundation.
# All rights reserved.
# 
# Copyright (c) 2000 BeOpen.com.
# All rights reserved.
# 
# Copyright (c) 1995-2001 Corporation for National Research Initiatives.
# All rights reserved.
# 
# Copyright (c) 1991-1995 Stichting Mathematisch Centrum.
# All rights reserved.
# 
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License. 
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

# XXX The UDP version of the protocol resends requests when it does
# XXX not receive a timely reply -- use only for idempotent calls!

# XXX There is no provision for call timeout on TCP connections

__pychecker__ = 'no-callinit'

import xdrlib
import socket
import select
import os
import time
import random
import warnings
import logging
import threading
import exceptions
from errno import *
import struct
try:
    import gssapi
except ImportError:
    pass


def verify_gssapi_module():
    try:
        gssapi
    except NameError:
        raise RuntimeError("gssapi module not compiled")
    
try:
    import select
except ImportError:
    warnings.warn("This system does not have poll!")
    import selectpoll as select

#Attempt to make xid's as random as possible to avoid repetition.
G_lastxid = random.randint(0,2**30 - 1)

RPCVERSION = 2

RPCSEC_GSS_VERS_1 = 1

MAXSEQ = 0x80000000L  # Maximum gss sequence number value

#enum rpc_gss_proc_t
RPCSEC_GSS_DATA          = 0
RPCSEC_GSS_INIT          = 1
RPCSEC_GSS_CONTINUE_INIT = 2
RPCSEC_GSS_DESTROY       = 3

#enum rpc_gss_service_t
rpc_gss_svc_none      = 1
rpc_gss_svc_integrity = 2
rpc_gss_svc_privacy   = 3

# enum msg_type
CALL = 0
REPLY = 1

# enum auth_flavor
AUTH_NULL = 0
AUTH_UNIX = 1
AUTH_SHORT = 2
AUTH_DES = 3
RPCSEC_GSS = 6

# enum reply_stat
MSG_ACCEPTED = 0
MSG_DENIED = 1

# enum accept_stat
SUCCESS = 0                             # RPC executed successfully
PROG_UNAVAIL  = 1                       # remote hasn't exported program
PROG_MISMATCH = 2                       # remote can't support version #
PROC_UNAVAIL  = 3                       # program can't support procedure
GARBAGE_ARGS  = 4                       # procedure can't decode params
SYSTEM_ERR    = 5                       # errors like mem alloc failuere

# enum reject_stat
RPC_MISMATCH = 0                        # RPC version number != 2
AUTH_ERROR = 1                          # remote can't authenticate caller

# enum auth_stat
AUTH_OK           = 0                   # success
AUTH_BADCRED      = 1                   # bad credentials (seal broken)
AUTH_REJECTEDCRED = 2                   # client must begin new session
AUTH_BADVERF      = 3                   # bad verifier (seal broken)
AUTH_REJECTEDVERF = 4                   # verifier expired or replayed
AUTH_TOOWEAK      = 5                   # rejected for security reasons
AUTH_INVALIDRESP  = 6                   # bogus response verifier
AUTH_FAILED       = 7                   # reason unknown
RPCSEC_GSS_CREDPROBLEM = 13
RPCSEC_GSS_CTXPROBLEM  = 14

# special return value for void returns
VOID_RTN = '--void--'

# Dictionary of supported security types
supported = {'sys' : (AUTH_UNIX, None),
             'unix' : (AUTH_UNIX, None),
             'null' : (AUTH_NULL, None),
             'none' : (AUTH_NULL, None),
             'krb5' : (RPCSEC_GSS, rpc_gss_svc_none),
             'krb5i' : (RPCSEC_GSS, rpc_gss_svc_integrity),
             'krb5p' : (RPCSEC_GSS, rpc_gss_svc_privacy)}

# All RPC errors are subclasses of RPCException
class RPCException(Exception):
    def __str__(self):
        # name of the object's class, which may be a descendant class
        return self.__class__.__name__
        #return "RPCException"

class RPCSecurity(RPCException):
    def __init__(self, msg=""):
        self.msg = msg

    def __str__(self):
        if self.msg:
            return "%s" % self.msg
        else:
            return "RPC security error"

class BadRPCVerifier(RPCSecurity):
    def __str__(self):
        return "Bad verifier in RPC reply"

class BadRPCFlavor(RPCSecurity):
    def __init__(self, flavor):
        self.flavor = flavor
    def __str_(self):
        return "Unknown or unsupported security flavor %i" % self.flavor

class BadRPCMsgType(RPCException):
    def __init__(self, msg_type):
        self.msg_type = msg_type

    def __str__(self):
        return "BadRPCMsgType %d" % self.msg_type

class BadRPCVersion(RPCException):
    def __init__(self, version):
        self.version = version

    def __str__(self):
        return "BadRPCVersion %d" % self.version

class RPCMsgDenied(RPCException):
    # MSG_DENIED
    def __init__(self, stat):
        self.stat = stat

    def __str__(self):
        return "RPCMsgDenied %d" % self.stat

class RPCMisMatch(RPCException):
    # MSG_DENIED: RPC_MISMATCH
    def __init__(self, low, high):
        self.low = low
        self.high = high

    def __str__(self):
        return "RPCMisMatch %d,%d" % (self.low, self.high)

class RPCAuthError(RPCException):
    # MSG_DENIED: AUTH_ERROR
    def __init__(self, stat):
        self.stat = stat

    def __str__(self):
        return "RPCAuthError %d" % self.stat

class BadRPCReplyType(RPCException):
    # Neither MSG_DENIED nor MSG_ACCEPTED
    def __init__(self, msg_type):
        self.msg_type = msg_type

    def __str__(self):
        return "BadRPCReplyType %d" % self.msg_type

class RPCProgUnavail(RPCException):
    # PROG_UNAVAIL
    def __str__(self):
        return "RPCProgUnavail"

class RPCProgMismatch(RPCException):
    # PROG_MISMATCH
    def __init__(self, low, high):
        self.low = low
        self.high = high

    def __str__(self):
        return "RPCProgMismatch %d,%d" % (self.low, self.high)

class RPCProcUnavail(RPCException):
    # PROC_UNAVAIL
    def __str__(self):
        return "RPCProcUnavail"

class RPCNoHeader(RPCException):
    # PROC_UNAVAIL
    def __str__(self):
        return "RPCNoHeader"

class RPCGarbageArgs(RPCException):
    # GARBAGE_ARGS
    def __str__(self):
        return "RPCGarbageArgs"

class RPCUnextractedData(RPCException):
    # xdrlib raised exception because unextracted data remained
    def __str__(self):
        return "RPCUnextractedData"

class RPCBadAcceptStats(RPCException):
    # Unknown accept_stat
    def __init__(self, stat):
        self.stat = stat

    def __str__(self):
        return "RPCBadAcceptStats %d" % self.stat

class XidMismatch(RPCException):
    # Got wrong XID in reply, got "xid" instead of "expected"
    def __init__(self, xid, expected):
        self.xid = xid
        self.expected = expected

    def __str__(self):
        return "XidMismatch %d,%d" % (self.xid, self.expected)

class TimeoutError(RPCException):
    pass

class PortMapError(RPCException):
    def __init__(self, msg=""):
        self.msg = msg

    def __str__(self):
        if self.msg:
            return "%s" % self.msg
        else:
            return "PortMapError"



class Packer(xdrlib.Packer):

    def pack_auth(self, auth):
        """ Takes as input a tuple of (flavor, body) """
        flavor, body = auth
        if len(body) > 400:
            raise xdrlib.XDRError, "Authenticator body too long: %i"%len(body)
        self.pack_enum(flavor)
        self.pack_opaque(body)

    def pack_auth_unix(self, stamp, machinename, uid, gid, gids):
        self.pack_uint(stamp)
        self.pack_string(machinename)
        self.pack_uint(uid)
        self.pack_uint(gid)
        self.pack_uint(len(gids))
        for i in gids:
            self.pack_uint(i)

    def pack_cred_gss(self, gss_proc, seq_num, service, handle):
        self.pack_uint(RPCSEC_GSS_VERS_1)
        self.pack_uint(gss_proc)
        self.pack_uint(seq_num)
        self.pack_uint(service)
        self.pack_opaque(handle)

    # This does not pack the verifier at end, since some security
    # protocols require knowledge of what has been packed so far before
    # verifier can be created.  So follow this with pack_callverf()
    def pack_callheader(self, xid, prog, vers, proc, cred):
        self.pack_uint(xid)
        self.pack_enum(CALL)
        self.pack_uint(RPCVERSION)
        self.pack_uint(prog)
        self.pack_uint(vers)
        self.pack_uint(proc)
        self.pack_auth(cred)

    def pack_callverf(self, verf):
        self.pack_auth(verf)
        # Caller must add procedure-specific part of call

    def pack_replyheader(self, xid, verf):
        self.pack_uint(xid)
        self.pack_enum(REPLY)
        self.pack_uint(MSG_ACCEPTED)
        self.pack_auth(verf)
        self.pack_enum(SUCCESS)
        # Caller must add procedure-specific part of reply


class Unpacker(xdrlib.Unpacker):

    def get_remaining(self):
        return self.get_buffer()[self.get_position():]

    def unpack_auth(self):
        flavor = self.unpack_enum()
        body = self.unpack_opaque()
        if flavor == AUTH_UNIX:
            p = Unpacker(body)
            body = p.unpack_auth_unix()
        if flavor == RPCSEC_GSS:
            # body equals checksum from getMIC
            pass
        return (flavor, body)

    def unpack_gss_init(self):
        handle = self.unpack_opaque()
        major  = self.unpack_uint()
        minor  = self.unpack_uint()
        window = self.unpack_uint()
        token  = self.unpack_opaque()
        return major, minor, handle, window, token

    def unpack_auth_unix(self):
        stamp=self.unpack_uint()
        machinename=self.unpack_string()
        uid=self.unpack_uint()
        gid=self.unpack_uint()
        n_gids=self.unpack_uint()
        gids = []
        for i in range(n_gids):
            gids.append(self.unpack_uint())
        return stamp, machinename, uid, gid, gids

    def unpack_callheader(self):
        xid = self.unpack_uint()
        msg_type = self.unpack_enum()
        if msg_type != CALL:
            raise BadRPCMsgType(msg_type)
        rpcvers = self.unpack_uint()
        if rpcvers != RPCVERSION:
            raise BadRPCVersion(rpcvers)
        prog = self.unpack_uint()
        vers = self.unpack_uint()
        proc = self.unpack_uint()
        cred = self.unpack_auth()
        verf = self.unpack_auth()
        return xid, prog, vers, proc, cred, verf
        # Caller must add procedure-specific part of call

    def unpack_replyheader(self):
        xid = self.unpack_uint()
        msg_type = self.unpack_enum()
        if msg_type != REPLY:
            raise BadRPCMsgType(msg_type)
        stat = self.unpack_enum()
        if stat == MSG_DENIED:
            stat = self.unpack_enum()
            if stat == RPC_MISMATCH:
                low = self.unpack_uint()
                high = self.unpack_uint()
                raise RPCMisMatch(low, high)
            if stat == AUTH_ERROR:
                stat = self.unpack_uint()
                raise RPCAuthError(stat)
            raise RPCMsgDenied(stat)
        if stat != MSG_ACCEPTED:
            raise BadRPCReplyType(stat)
        verf = self.unpack_auth()
        stat = self.unpack_enum()
        if stat == PROG_UNAVAIL:
            raise RPCProgUnavail()
        if stat == PROG_MISMATCH:
            low = self.unpack_uint()
            high = self.unpack_uint()
            raise RPCProgMismatch(low, high)
        if stat == PROC_UNAVAIL:
            raise RPCProcUnavail()
        if stat == GARBAGE_ARGS:
            raise RPCGarbageArgs()
        if stat != SUCCESS:
            raise RPCBadAcceptStats(stat)
        return xid, verf
        # Caller must get procedure-specific part of reply


# Subroutines to create opaque authentication objects

def make_auth_null():
    return ''

def make_auth_unix(seed, host, uid, gid, groups):
    p = Packer()
    p.pack_auth_unix(seed, host, uid, gid, groups)
    return p.get_buffer()

def make_cred_gss(seq_num, handle, service=rpc_gss_svc_none,
                  gss_proc=RPCSEC_GSS_DATA):
    p = Packer()
    p.pack_cred_gss(gss_proc, seq_num, service, handle)
    return p.get_buffer()

def make_auth_unix_default():
    try:
        uid = os.getuid()
        gid = os.getgid()
    except AttributeError:
        uid = gid = 0
    return make_auth_unix(int(time.time()-unix_epoch()), \
              socket.gethostname(), uid, gid, [])

_unix_epoch = -1
def unix_epoch():
    """Very painful calculation of when the Unix Epoch is.

    This is defined as the return value of time.time() on Jan 1st,
    1970, 00:00:00 GMT.

    On a Unix system, this should always return 0.0.  On a Mac, the
    calculations are needed -- and hard because of integer overflow
    and other limitations.

    """
    global _unix_epoch
    if _unix_epoch >= 0: return _unix_epoch
    now = time.time()
    localt = time.localtime(now)        # (y, m, d, hh, mm, ss, ..., ..., ...)
    gmt = time.gmtime(now)
    offset = time.mktime(localt) - time.mktime(gmt)
    y, m, d, hh, mm, ss = 1970, 1, 1, 0, 0, 0
    offset, ss = divmod(ss + offset, 60)
    offset, mm = divmod(mm + offset, 60)
    offset, hh = divmod(hh + offset, 24)
    d = d + offset
    _unix_epoch = time.mktime((y, m, d, hh, mm, ss, 0, 0, 0))
    print "Unix epoch:", time.ctime(_unix_epoch)
    return _unix_epoch


# Common base class for clients

class Client:
    def __init__(self, host, prog, vers, port, sec = (AUTH_NULL, None),
                 logger=None):
        self.host = host
        self.prog = prog
        self.vers = vers
        self.port = port
        self.sec  = sec  # A pair containing (flavor, extra_info)
        if not logger:
            logger = logging.getLogger("rpc")
        self.logger = logger
        # for mutual exclusion
        self.lock = threading.RLock()
        # for termination
        self.quit = threading.Event()
        # for select() timeout
        self.timeout = 1.0
        self.voidrtn = False

        self.sock = None
        self.addpackers()
#now replaced by G_lastxid to make xid more global, and therefore not repeat-
#       self.lastxid = 0 # XXX should be more random?
        self.lastxid = 0 # now used to keep a per-client last xid to know what to expect.
        self.__connect(sec)

    def __connect(self, sec):
        self.makesocket() # Assigns to self.sock
        self.bindsocket()
        self.connsocket()
        self.sec_init(sec)

    def reconnect(self, sec):
        self.__connect(sec)

    def sec_init(self, sec):
        """Run any necessary initialization needed by security flavor

        sec is a pair containing (flavor, extra_info)
        """
        self.cred = None
        self.verf = None
        self.sec = sec
        flavor = sec[0]
        if flavor in [AUTH_NULL, AUTH_UNIX]:
            # These flavors do not need any initialization
            pass
        
        elif flavor == RPCSEC_GSS:
            verify_gssapi_module()
            self.gss_seq_num = 0

            service = "nfs@%s" % self.host
            major, x, name = gssapi.importName(service)
            if major != gssapi.GSS_S_COMPLETE:
                raise RPCSecurity, "Bad return value from importName: %i"%major

            # We need to send NULLPROCs with token from initSecContext
            good_major = [gssapi.GSS_S_COMPLETE, gssapi.GSS_S_CONTINUE_NEEDED]
            init = 1
            reply_token = ''
            reply_major = ''
            context = gssapi.Buffer()
            while True:
                major, x, token, context, x, x, x = \
                       gssapi.initSecContext(name, reply_token, context)
                if major not in good_major:
                    raise RPCSecurity, \
                          "Bad return value from initSecContext: %i" % major
                if (major == gssapi.GSS_S_CONTINUE_NEEDED) and \
                   (reply_major == gssapi.GSS_S_COMPLETE):
                    raise RPCSecurity, "Unexpected COMPLETE from server"
                if token and (reply_major != gssapi.GSS_S_COMPLETE):
                    reply_major, x, handle, x, reply_token = \
                                 self.make_call(0, token.pulldata(),
                                                self.packer.pack_opaque,
                                                self.unpacker.unpack_gss_init,
                                                init)
                    if reply_major not in good_major:
                        raise RPCSecurity, \
                              "Bad return value from server: %i" % reply_major
                    init = 2
                if major == gssapi.GSS_S_COMPLETE:
                    if reply_major != gssapi.GSS_S_COMPLETE:
                        raise RPCSecurity, "Unexpected COMPLETE from client"
                    break
            self.gss_context = context
            self.gss_handle = handle
            
        else:
            raise BadRPCFlavor, flavor

    def change_sec(self, name):
        """Changes security to name from supported dictionary.  It assumes
        any appropriate sec_init calls have already been run"""
        try: self.sec = supported[name]
        except KeyError:
            self.logger.warn("Unsupported security flavor %s, security unchanged" % name)
            return
        self.verf = None
        self.cred = None

    def secure_data(self, data, init=0):
        # Apply any manipulations to call data required by security method
        flavor = self.sec[0]
        if flavor in [AUTH_NULL, AUTH_UNIX]:
            pass
        elif flavor == RPCSEC_GSS:
            verify_gssapi_module()
            service = self.sec[1]
            if service == rpc_gss_svc_none or init:
                pass
            elif service == rpc_gss_svc_integrity:
                # data = opaque[gss_seq_num+data] + opaque[checksum]
                p = Packer()
                p.pack_uint(self.gss_seq_num)
                data = p.get_buffer() + data
                major, minor, checksum = gssapi.getMIC(self.gss_context, data)
                if major != gssapi.GSS_S_COMPLETE:
                    raise RPCSecurity, "Bad gssapi.getMIC return %i" % major
                p.reset()
                p.pack_opaque(data)
                p.pack_opaque(checksum)
                data = p.get_buffer()
            elif service == rpc_gss_svc_privacy:
                # data = opaque[wrap([gss_seq_num+data])]
                # FRED - this is untested
                p = Packer()
                p.pack_uint(self.gss_seq_num)
                data = p.get_buffer() + data
                major, x, data, x = gssapi.wrap(self.gss_context, data)
                if major != gssapi.GSS_S_COMPLETE:
                    raise RPCSecurity, "Bad gssapi.wrap return %i" % major
                p.reset()
                p.pack_opaque(data)
                data = p.get_buffer()
            else:
                raise RPCSecurity, "Unknown service %i for RPCSEC_GSS"%service
        else:
            raise BadRPCFlavor, flavor
        
        return data
        
    def unsecure_data(self, data, init=0):
        # Apply any manipulations to reply data required by security method
        flavor = self.sec[0]
        if flavor in [AUTH_NULL, AUTH_UNIX]:
            pass
        elif flavor == RPCSEC_GSS:
            verify_gssapi_module()
            service = self.sec[1]
            if service == rpc_gss_svc_none or init:
                pass
            elif service == rpc_gss_svc_integrity:
                # data = opaque[gss_seq_num+data] + opaque[checksum]
                p = Unpacker(data)
                data = p.unpack_opaque()
                checksum = p.unpack_opaque()
                p.done()
                major = gssapi.verifyMIC(self.gss_context, data, checksum)[0]
                if major != gssapi.GSS_S_COMPLETE:
                    raise RPCSecurity, "Bad gssapi.verifyMIC return %i" % major
                p.reset(data)
                seqnum = p.unpack_uint()
                if seqnum != self.gss_seq_num:
                    raise RPCSecurity, "Mismatched seqnums in reply"
                data = p.get_remaining()
            elif service == rpc_gss_svc_privacy:
                # data = opaque[wrap([gss_seq_num+data])]
                # FRED - this is untested
                p = Unpacker(data)
                data = p.unpack_opaque()
                p.done()
                major,x,data,x,x = gssapi.unwrap(self.gss_context, data)
                if major != gssapi.GSS_S_COMPLETE:
                    raise RPCSecurity, "Bad gssapi.unwrap return %i" % major
                p.reset(data)
                seqnum = p.unpack_uint()
                if seqnum != self.gss_seq_num:
                    raise RPCSecurity, "Mismatched seqnums in reply"
                data = p.get_remaining()
            else:
                raise RPCSecurity, "Unknown service %i for RPCSEC_GSS"%service
        else:
            raise BadRPCFlavor, flavor
        
        return data
        
    def close(self):
        #? print '>>>>rpc.Client.close: self  =', self
        self.sock.close()

    def makesocket(self):
        # This MUST be overridden
        raise RuntimeError("makesocket not defined")

    def connsocket(self):
        # Override this if you don't want/need a connection
        self.sock.connect((self.host, self.port))

    def bindsocket(self, sock=853):
        # Override this to bind to a different port (e.g. reserved)
    # This is necessary because otherwise will default to an insecure
    # port, which the server will reject unless it has the 'insecure'
    # option set
        if self.prog < 0x200000:
                try:
                    self.sock.bind(('', sock))
                except socket.error, why:
                    if why[0] == EADDRINUSE:
                        self.bindsocket(sock+1)
                    else:
                        self.sock.bind(('', 0))
        else:
            self.sock.bind(('', 0))

    def addpackers(self):
        # Override this to use derived classes from Packer/Unpacker
        self.packer = Packer()
        self.unpacker = Unpacker('')

    def make_call(self, proc, args, pack_func, unpack_func, init=0):
        # Don't normally override this (but see Broadcast)
        if pack_func is None and args is not None:
            raise TypeError("non-null args with null pack_func")
        self.start_call(proc, init)
        p = self.packer
        header = p.get_buffer()
        p.reset()
        if pack_func:
            pack_func(args)
        data = p.get_buffer()
        data = self.secure_data(data, init)
        # do_call() strips RPC header from reply and returns verifier, and
        # self.unpacker is set to beginning of the procedure results
        verf = self.do_call(header, data)
        output = self.unsecure_data(self.unpacker.get_remaining(), init)
        
        self.unpacker.reset(output)
        if unpack_func:
            result = unpack_func()
        else:
            result = None
        try:
            self.unpacker.done()
        except xdrlib.Error:
            raise RPCUnextractedData()

        if verf is not None or \
           result is None:
            self.check_verf(result, verf, init)
        return result

    def check_verf(self, result, verf, init=0, flavor=None):
        """Checks that result and verf from a server reply are consistent.

        Raises an exception if they are not.
        """
        if flavor is None: flavor = self.sec[0]
        if flavor in [AUTH_NULL, AUTH_UNIX]:
            # These flavors do not use verification
            pass
        elif flavor == RPCSEC_GSS:
            verify_gssapi_module()
            # verifier is checksum of either window (during init) or seq_num
            if init: msg = result[3]
            else:    msg = self.gss_seq_num
            
            if init:
                if result[0] != gssapi.GSS_S_COMPLETE:
                    if verf != (AUTH_NULL, make_auth_null()):
                        raise BadRPCVerifier
            else:
                # body = checksum of gss_seq_num (network order) in
                # corresponding request
                major = gssapi.verifyMIC(self.gss_context,
                                         struct.pack(">L", msg),
                                         verf[1])[0]
                if (major!=gssapi.GSS_S_COMPLETE) or (verf[0]!=RPCSEC_GSS):
                    raise BadRPCVerifier
            return
        else:
            raise BadRPCFlavor, flavor
        
    def start_call(self, proc, init=0):
        """ Pack the call header """
        # Don't override this
        global G_lastxid
        self.lastxid = G_lastxid = xid = G_lastxid + 1
        # self.lastxid = xid = G_lastxid + 1
        cred = self.mkcred(init)
        p = self.packer
        p.reset()
        p.pack_callheader(xid, self.prog, self.vers, proc, cred)
        verf = self.mkverf(init, p.get_buffer())
        p.pack_callverf(verf)

    def do_call(header, data):
        # This MUST be overridden
        # It should send to the server the message in header + data.
        # Then strip the RPC header from reply and return verifier, and
        # set self.unpacker to beginning of the procedure results.
        raise RuntimeError("do_call not defined")

    def mkcred(self, init=0):
        """Make credentials for RPC header

        outputs a tuple of (flavor, body)
        """
        flavor = self.sec[0]
        if flavor == AUTH_NULL:
            if self.cred == None:
                self.cred = (AUTH_NULL, make_auth_null())
        elif flavor == AUTH_UNIX:
            if self.cred == None:
                hostname = socket.gethostname()
                groups = os.getgroups()
                self.logger.debug("making CRED uid=%d gid=%d" % (
                        self.uid, self.gid))
                self.cred = (AUTH_UNIX,
                             make_auth_unix(1, hostname, self.uid, self.gid, groups))
        elif flavor == RPCSEC_GSS:
            service = self.sec[1]
            if init == 1:
                self.cred = (RPCSEC_GSS, make_cred_gss(0, '', rpc_gss_svc_none,
                                                       RPCSEC_GSS_INIT))
            elif init > 1:
                self.cred = (RPCSEC_GSS, make_cred_gss(0, '', rpc_gss_svc_none,
                                                       RPCSEC_GSS_CONTINUE_INIT))
            else:
                self.gss_seq_num += 1 # FRED - check for overflow
                self.cred = (RPCSEC_GSS,
                             make_cred_gss(self.gss_seq_num, self.gss_handle,
                                           service))
        else:
            raise BadRPCFlavor, flavor
        return self.cred

    def mkverf(self, init = 0, buf=None):
        """Make verifier for RPC header

        outputs a tuple of (flavor, body)
        """
        flavor = self.sec[0]
        if flavor in [AUTH_NULL, AUTH_UNIX]:
            if self.verf == None:
                self.verf = (AUTH_NULL, make_auth_null())
        elif flavor == RPCSEC_GSS:
            verify_gssapi_module()
            if init:
                self.verf = (AUTH_NULL, make_auth_null())
            else:
                major, minor, checksum = gssapi.getMIC(self.gss_context, buf)
                if major != gssapi.GSS_S_COMPLETE:
                    raise RPCSecurity, "Bad gssapi.getMIC return %i" % major
                self.verf = (RPCSEC_GSS, checksum)
        else:
            raise BadRPCFlavor, flavor
        return self.verf
    
    def call_0(self):           # Procedure 0 is always like this
        return self.make_call(0, None, None, None)


# Record-Marking standard support

def sendfrag(sock, last, frag):
    x = len(frag)
    # Boo! By the standard, the length need to be 
    # multiple of 4 and if x % 4 !=0, we need to pad the frag!!
    if last: x = x | 0x80000000L
    header = struct.pack("!L", x)
    #header = (chr(int(x>>24 & 0xff)) + chr(int(x>>16 & 0xff)) + \
    #         chr(int(x>>8 & 0xff)) + chr(int(x & 0xff)))
    sock.send(header + frag)

def sendrecord(sock, record):
    # Boo! this does not check the MAX fragment size!!!
    sendfrag(sock, 1, record)

def recvfrag(sock):
    header = sock.recv(4)
    if len(header) < 4:
        if len(header)==0:
            raise RPCNoHeader
        else:
            raise EOFError
    x = struct.unpack('!L', header)[0]
    last = ((x & 0x80000000L) != 0)
    n = int(x & 0x7fffffff)
    ## frag = ''
    frag = []
    # Boo! it blocks here!!! (yasu)
    while n > 0:
      buf = sock.recv(n)
      if not buf: raise EOFError
      n = n - len(buf)
      ## frag = frag + buf
      frag.append(buf)
    ## return last, frag
    return last, ''.join(frag)

def recvrecord(sock):
    ## record = ''
    record = []
    last = 0
    while not last:
      last, frag = recvfrag(sock)
      ## record = record + frag
      record.append(frag)
    ## return record
    return ''.join(record)  


# Try to bind to a reserved port (must be root)

last_resv_port_tried = None
def bindresvport(sock, host):
    global last_resv_port_tried
    FIRST, LAST = 600, 1024 # Range of ports to try
    if last_resv_port_tried == None:
        last_resv_port_tried = FIRST + os.getpid() % (LAST-FIRST)
    for i in range(last_resv_port_tried, LAST) + \
              range(FIRST, last_resv_port_tried):
        last_resv_port_tried = i
        try:
            sock.bind((host, i))
            return last_resv_port_tried
        except socket.error, ( msg):
            if errno != 114:
                raise socket.error( msg)
    raise RuntimeError("can't assign reserved port")


# Client using TCP to a specific port

class RawTCPClient(Client):

    def makesocket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def do_call(self, header, data):
        call = header + data
        sendrecord(self.sock, call)
        try:
            if self.voidrtn:
                return None
            reply = recvrecord(self.sock)
        except RPCNoHeader:
            # This means we received a TCP reply without an RPC payload,
            # most likely a reset
            self.logger.warn("Trying to reconnect...")
            self.close()
            self.reconnect(self.sec)
            self.logger.warn("Reconnected")
            # Try again, if it fails again, we just pass back the error
            sendrecord(self.sock, call)
            reply = recvrecord(self.sock)
        u = self.unpacker
        u.reset(reply)
        xid, verf = u.unpack_replyheader()
        if xid != self.lastxid:
            # Can't really happen since this is TCP...
            raise XidMismatch(xid, self.lastxid)
        return verf

# Client using UDP to a specific port

class RawUDPClient(Client):
    def __init__(self, host, prog, vers, port, sec = (AUTH_NULL, None),
                 logger=None):
        Client.__init__(self, host, prog, vers, port, sec, logger=logger)
        #self.timeout      = 1
        self.retry        = 5
        self.max_interval = 25

    def makesocket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def do_call(self, header, data):
        call = header + data
        self.sock.send(call)
        
        try:
            from select import select
        except ImportError:
            self.logger.warn('WARNING: select not found, RPC may hang')
            select = None
        BUFSIZE = 8192 # Max UDP buffer size
        timeout = self.timeout
        count   = self.retry
        while not self.quit.isSet():
            r, w, x = [self.sock], [], []
            if select:
                r, w, x = select(r, w, x, timeout)
            if self.sock not in r:
                count = count - 1
                if count < 0: 
                        raise TimeoutError() 
                if timeout < self.max_interval:
                    # exponential backoff
                    timeout = timeout * 2
                    self.logger.debug('RESEND %s %s' % (str(timeout),
                                                        str(count)))
                self.sock.send(call)
                continue
            reply = self.sock.recv(BUFSIZE)
            u = self.unpacker
            u.reset(reply)
            xid, verf = u.unpack_replyheader()
            if xid != self.lastxid:
##              self.logger.warn('BAD xid: %s' % str(xid))
                continue
            break
        return verf

# Client using UDP broadcast to a specific port

class RawBroadcastUDPClient(RawUDPClient):

    def __init__(self, bcastaddr, prog, vers, port, logger=None):
        RawUDPClient.__init__(self, bcastaddr, prog, vers, port, logger=logger)
        self.reply_handler = None
        self.timeout = 30

    def connsocket(self):
        # Don't connect -- use sendto
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def set_reply_handler(self, reply_handler):
        self.reply_handler = reply_handler

    def set_timeout(self, timeout):
        self.timeout = timeout # Use None for infinite timeout

    def make_call(self, proc, args, pack_func, unpack_func):
        if pack_func is None and args is not None:
            raise TypeError("non-null args with null pack_func")
        self.start_call(proc)
        if pack_func:
            pack_func(args)
        call = self.packer.get_buffer()
        self.sock.sendto(call, (self.host, self.port))
        try:
            from select import select
        except ImportError:
            self.logger.warn('WARNING: select not found, broadcast will hang')
            select = None
        BUFSIZE = 8192 # Max UDP buffer size (for reply)
        replies = []
        if unpack_func is None:
            def dummy(): pass
            unpack_func = dummy
        while 1:
            r, w, x = [self.sock], [], []
            if select:
                if self.timeout is None:
                    r, w, x = select(r, w, x)
                else:
                    r, w, x = select(r, w, x, self.timeout)
            if self.sock not in r:
                break
            reply, fromaddr = self.sock.recvfrom(BUFSIZE)
            u = self.unpacker
            u.reset(reply)
            xid, verf = u.unpack_replyheader()
            if xid != self.lastxid:
##                self.logger.warn('BAD xid: %s' % str(xid))
                continue
            reply = unpack_func()
            try:
                self.unpacker.done()
            except xdrlib.Error:
                raise RPCUnextractedData()
            replies.append((reply, fromaddr))
            if self.reply_handler:
                self.reply_handler(reply, fromaddr)
        return replies


# Port mapper interface

# Program number, version and (fixed!) port number
PMAP_PROG = 100000
PMAP_VERS = 2
PMAP_PORT = 111

# Procedure numbers
PMAPPROC_NULL = 0                       # (void) -> void
PMAPPROC_SET = 1                        # (mapping) -> bool
PMAPPROC_UNSET = 2                      # (mapping) -> bool
PMAPPROC_GETPORT = 3                    # (mapping) -> unsigned int
PMAPPROC_DUMP = 4                       # (void) -> pmaplist
PMAPPROC_CALLIT = 5                     # (call_args) -> call_result

# A mapping is (prog, vers, prot, port) and prot is one of:

IPPROTO_TCP = 6
IPPROTO_UDP = 17

# A pmaplist is a variable-length list of mappings, as follows:
# either (1, mapping, pmaplist) or (0).

# A call_args is (prog, vers, proc, args) where args is opaque;
# a call_result is (port, res) where res is opaque.


class PortMapperPacker(Packer):

    def pack_mapping(self, mapping):
        prog, vers, prot, port = mapping
        self.pack_uint(prog)
        self.pack_uint(vers)
        self.pack_uint(prot)
        self.pack_uint(port)

    def pack_pmaplist(self, list):
        self.pack_list(list, self.pack_mapping)

    def pack_call_args(self, ca):
        prog, vers, proc, args = ca
        self.pack_uint(prog)
        self.pack_uint(vers)
        self.pack_uint(proc)
        self.pack_opaque(args)


class PortMapperUnpacker(Unpacker):

    def unpack_mapping(self):
        prog = self.unpack_uint()
        vers = self.unpack_uint()
        prot = self.unpack_uint()
        port = self.unpack_uint()
        return prog, vers, prot, port

    def unpack_pmaplist(self):
        return self.unpack_list(self.unpack_mapping)

    def unpack_call_result(self):
        port = self.unpack_uint()
        res = self.unpack_opaque()
        return port, res


class PartialPortMapperClient:
    __pychecker__ = 'no-classattr'
    def addpackers(self):
        self.packer = PortMapperPacker()
        self.unpacker = PortMapperUnpacker('')

    def Set(self, mapping):
        return self.make_call(PMAPPROC_SET, mapping, \
                self.packer.pack_mapping, \
                self.unpacker.unpack_uint)

    def Unset(self, mapping):
        return self.make_call(PMAPPROC_UNSET, mapping, \
                self.packer.pack_mapping, \
                self.unpacker.unpack_uint)

    def Getport(self, mapping):
        return self.make_call(PMAPPROC_GETPORT, mapping, \
                self.packer.pack_mapping, \
                self.unpacker.unpack_uint)

    def Dump(self):
        return self.make_call(PMAPPROC_DUMP, None, \
                None, \
                self.unpacker.unpack_pmaplist)

    def Callit(self, ca):
        return self.make_call(PMAPPROC_CALLIT, ca, \
                self.packer.pack_call_args, \
                self.unpacker.unpack_call_result)


class TCPPortMapperClient(PartialPortMapperClient, RawTCPClient):

    def __init__(self, host, logger=None):
        RawTCPClient.__init__(self, 
                host, PMAP_PROG, PMAP_VERS, PMAP_PORT, logger=logger)


class UDPPortMapperClient(PartialPortMapperClient, RawUDPClient):

    def __init__(self, host, logger=None):
        RawUDPClient.__init__(self, \
                host, PMAP_PROG, PMAP_VERS, PMAP_PORT, logger=logger)


class BroadcastUDPPortMapperClient(PartialPortMapperClient, \
                                   RawBroadcastUDPClient):

    def __init__(self, bcastaddr, logger=None):
        RawBroadcastUDPClient.__init__(self, \
                bcastaddr, PMAP_PROG, PMAP_VERS, PMAP_PORT, logger=logger)


# Generic clients that find their server through the Port mapper

class TCPClient(RawTCPClient):

    def __init__(self, host, prog, vers, sec = AUTH_NULL, logger=None):
        pmap = TCPPortMapperClient(host, logger=logger)
        if logger:
            logger.debug("TCPClient connection to %s %d/%x %s %s" % (
                    host, prog, prog, str(vers), str(pmap)))
        port = pmap.Getport((prog, vers, IPPROTO_TCP, 0))
        pmap.close()
        if port == 0:
            raise PortMapError("program %d not registered at %s" % (prog,host))
        RawTCPClient.__init__(self, host, prog, vers, port, sec, logger=logger)


class UDPClient(RawUDPClient):

    def __init__(self, host, prog, vers, sec = AUTH_NULL, logger=None):
        pmap = UDPPortMapperClient(host, logger=logger)
        port = pmap.Getport((prog, vers, IPPROTO_UDP, 0))
        pmap.close()
        if port == 0:
            raise PortMapError("program %d not registered at %s" % (prog,host))
        RawUDPClient.__init__(self, host, prog, vers, port, sec, logger=logger)


class BroadcastUDPClient(Client):

    def __init__(self, bcastaddr, prog, vers, logger=None):
        self.pmap = BroadcastUDPPortMapperClient(bcastaddr, logger=logger)
        self.pmap.set_reply_handler(self.my_reply_handler)
        self.prog = prog
        self.vers = vers
        self.user_reply_handler = None
        self.addpackers()

    def close(self):
        self.pmap.close()

    def set_reply_handler(self, reply_handler):
        self.user_reply_handler = reply_handler

    def set_timeout(self, timeout):
        self.pmap.set_timeout(timeout)

    def my_reply_handler(self, reply, fromaddr):
        port, res = reply
        self.unpacker.reset(res)
        result = self.unpack_func()
        try:
            self.unpacker.done()
        except xdrlib.Error:
            raise RPCUnextractedData()
        self.replies.append((result, fromaddr))
        if self.user_reply_handler is not None:
            self.user_reply_handler(result, fromaddr)

    def make_call(self, proc, args, pack_func, unpack_func):
        self.packer.reset()
        if pack_func:
            pack_func(args)
        if unpack_func is None:
            def dummy(): pass
            self.unpack_func = dummy
        else:
            self.unpack_func = unpack_func
        self.replies = []
        packed_args = self.packer.get_buffer()
        dummy_replies = self.pmap.Callit( \
                (self.prog, self.vers, proc, packed_args))
        return self.replies


# Server classes

# These are not symmetric to the Client classes
# XXX No attempt is made to provide authorization hooks yet

class Server:
    def __init__(self, host, prog, vers, port, logger=None):
        self.host = host # Should normally be '' for default interface
        self.prog = prog
        self.vers = vers
        self.port = port # Should normally be 0 for random port
        if not logger:
            logger = logging.getLogger("rpc")
        self.logger = logger
        self.sock = None
        self.prot = None
        # for mutual exclusion
        self.lock = threading.RLock()
        # for termination
        self.quit = threading.Event()
        # for select() timeout
        self.timeout = 1.0
        
        self.makesocket() # Assigns to self.sock and self.prot
        self.bindsocket()
        self.host, self.port = self.sock.getsockname()
        self.addpackers()
        self.addpackerclasses()

    def quit_loop(self):
        self.quit.set()
        
    def register(self):
        mapping = self.prog, self.vers, self.prot, self.port
        p = UDPPortMapperClient(self.host, logger=self.logger)
        if not p.Set(mapping):
            raise PortMapError("register failed")

    def unregister(self):
        mapping = self.prog, self.vers, self.prot, self.port
        p = UDPPortMapperClient(self.host, logger=self.logger)
        if not p.Unset(mapping):
            raise PortMapError("unregister failed")

    def handle_threaded(self, call, packer, unpacker):
        # Don't use unpack_header but parse the header piecewise
        # XXX I have no idea if I am using the right error responses!
        unpacker.reset(call)
        packer.reset()
        xid = unpacker.unpack_uint()
        packer.pack_uint(xid)
        temp = unpacker.unpack_enum()
        if temp != CALL:
            return None # Not worthy of a reply
        packer.pack_uint(REPLY)
        temp = unpacker.unpack_uint()
        if temp != RPCVERSION:
            packer.pack_uint(MSG_DENIED)
            packer.pack_uint(RPC_MISMATCH)
            packer.pack_uint(RPCVERSION)
            packer.pack_uint(RPCVERSION)
            return packer.get_buffer()
        packer.pack_uint(MSG_ACCEPTED)
        packer.pack_auth((AUTH_NULL, make_auth_null()))
        prog = unpacker.unpack_uint()
        if prog != self.prog:
            packer.pack_uint(PROG_UNAVAIL)
            return packer.get_buffer()
        vers = unpacker.unpack_uint()
        if vers != self.vers:
            packer.pack_uint(PROG_MISMATCH)
            packer.pack_uint(self.vers)
            packer.pack_uint(self.vers)
            return packer.get_buffer()
        proc = unpacker.unpack_uint()

        # Look up handling method
        methname = 'handle_threaded_' + `proc`
        try:
            meth = getattr(self, methname)

        except AttributeError:
            packer.pack_uint(PROC_UNAVAIL)
            return packer.get_buffer()

        # Ack--state munge!
        # These don't seem to be used anywhere, so I don't think it matters
        # that they are overwritten, still....
        self.recv_cred = unpacker.unpack_auth()
        self.recv_verf = unpacker.unpack_auth()

        # Call handling method
        try:
            # Unpack args, call turn_around(), pack reply
            meth(packer, unpacker)

        except (EOFError, RPCGarbageArgs):
            # Too few or too many arguments
            packer.reset()
            packer.pack_uint(xid)
            packer.pack_uint(REPLY)
            packer.pack_uint(MSG_ACCEPTED)
            packer.pack_auth((AUTH_NULL, make_auth_null()))
            packer.pack_uint(GARBAGE_ARGS)

        return packer.get_buffer()

    def handle(self, call):
        # Don't use unpack_header but parse the header piecewise
        # XXX I have no idea if I am using the right error responses!
        self.unpacker.reset(call)
        self.packer.reset()
        xid = self.unpacker.unpack_uint()
        self.packer.pack_uint(xid)
        temp = self.unpacker.unpack_enum()
        if temp != CALL:
            return None # Not worthy of a reply
        self.packer.pack_uint(REPLY)
        temp = self.unpacker.unpack_uint()
        if temp != RPCVERSION:
            self.packer.pack_uint(MSG_DENIED)
            self.packer.pack_uint(RPC_MISMATCH)
            self.packer.pack_uint(RPCVERSION)
            self.packer.pack_uint(RPCVERSION)
            return self.packer.get_buffer()
        self.packer.pack_uint(MSG_ACCEPTED)
        self.packer.pack_auth((AUTH_NULL, make_auth_null()))
        prog = self.unpacker.unpack_uint()
        if prog != self.prog:
            self.packer.pack_uint(PROG_UNAVAIL)
            return self.packer.get_buffer()
        vers = self.unpacker.unpack_uint()
        if vers != self.vers:
            self.packer.pack_uint(PROG_MISMATCH)
            self.packer.pack_uint(self.vers)
            self.packer.pack_uint(self.vers)
            return self.packer.get_buffer()
        proc = self.unpacker.unpack_uint()
        methname = 'handle_' + `proc`
        try:
            meth = getattr(self, methname)
        except AttributeError:
            self.packer.pack_uint(PROC_UNAVAIL)
            return self.packer.get_buffer()
        self.recv_cred = self.unpacker.unpack_auth()
        self.recv_verf = self.unpacker.unpack_auth()
        self.logger.debug("recv_cred=%s recv_verf=%s" % (str(self.recv_cred),
                                                         str(self.recv_verf)))
        try:
            res = meth() # Unpack args, call turn_around(), pack reply
            if res == VOID_RTN:
                # Special Sun extension to RPC (void return type) ?
                return None
        except (EOFError, RPCGarbageArgs):
            # Too few or too many arguments
            self.packer.reset()
            self.packer.pack_uint(xid)
            self.packer.pack_uint(REPLY)
            self.packer.pack_uint(MSG_ACCEPTED)
            self.packer.pack_auth((AUTH_NULL, make_auth_null()))
            self.packer.pack_uint(GARBAGE_ARGS)
        return self.packer.get_buffer()

    def turn_around_threaded(self, packer, unpacker):
        try:
            unpacker.done()
        except xdrlib.Error:
            raise RPCUnextractedData()
        
        packer.pack_uint(SUCCESS)

    def turn_around(self):
        try:
            self.unpacker.done()
        except xdrlib.Error:
            raise RPCUnextractedData()
        
        self.packer.pack_uint(SUCCESS)

    def handle_threaded_0(self, packer, unpacker): # Handle NULL message
        self.turn_around_threaded(packer, unpacker)

    def handle_0(self): # Handle NULL message
        self.turn_around()

    def makesocket(self):
        # This MUST be overridden
        raise RuntimeError("makesocket not defined")

    def bindsocket(self):
        # Override this to bind to a different port (e.g. reserved)
        self.sock.bind((self.host, self.port))

    def addpackers(self):
        # Override this to use derived classes from Packer/Unpacker
        self.packer = Packer()
        self.unpacker = Unpacker('')

    def addpackerclasses(self):
        # Override this to use derived classes from Packer/Unpacker
        self.packerClass = Packer
        self.unpackerClass = Unpacker

    def session(self, *args):
        # Override this to choose which style of handling you want:
        # standard, threaded or forking
        return self.standard_session(*args)


class TCPServer(Server):

    def makesocket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.prot = IPPROTO_TCP

    def loop(self):
        self.sock.listen(0)
        while not self.quit.isSet():
            self.session(self.sock.accept())

    def standard_session(self, connection):
        sock, (host, port) = connection
        while not self.quit.isSet():
            try:
                call = recvrecord(sock)

            except EOFError:
                break

            except socket.error, msg:
                self.logger.error('socket error: %s' % msg)
                break

            reply = self.handle(call)
            if reply is not None:
                sendrecord(sock, reply)

    def threaded_session(self, connection):
        t = threading.Thread(target=self.session_in_thread,
                             args=[connection])
        t.start()

    def session_in_thread(self, connection):
        sock, (host, port) = connection
        while not self.quit.isSet():
            try:
                call = recvrecord(sock)

            except EOFError:
                break

            except socket.error, msg:
                self.logger.error('socket error: %s' % msg)
                break

            # make per-thread packer and unpacker
            packer = self.packerClass()
            unpacker = self.unpackerClass('')
            
            reply = self.handle_threaded(call, packer, unpacker)
            if reply is not None:
                sendrecord(sock, reply)

##     def forkingloop(self):
##         # Like loop but uses forksession()
##         self.sock.listen(0)
##         while not self.quit.isSet():
##             self.forksession(self.sock.accept())

    def forking_session(self, connection):
        # Like session but forks off a subprocess
        # Wait for deceased children
        try:
            while not self.quit.isSet():
                pid, sts = os.waitpid(0, 1)
        except os.error:
            pass
        pid = None
        try:
            pid = os.fork()
            if pid: # Parent
                connection[0].close()
                return
            # Child
            self.session(connection)
        finally:
            # Make sure we don't fall through in the parent
            if pid == 0:
                os._exit(0)

class MultipleTCPServer(Server):
    def makesocket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.setsockopt(socket.SOCK_STREAM, socket.SO_REUSEADDR, 1)
        except:
            self.logger.warn("unable to set SO_REUSEADDR on port.")
        self.prot = IPPROTO_TCP
        self.active = []
        self.info = {}
        
    def loop(self):
        self.sock.listen(0)
        while not self.quit.isSet():
            input = [ self.sock ] + self.active
            try:
                (sin, sout, sexp) = select.select(input, [], [], self.timeout)
            except KeyboardInterrupt:
                return
            for i in sin:
                if i == self.sock:
                    self.newsession(self.sock.accept())
                else: 
                    self.session(i)
                    
    def newsession(self, sock):
        sock, (host, port) = sock
        self.logger.debug("new connection from %s:%d" % (host, port))
        self.active.append(sock)
        self.info[sock] = (host,port)
        
    def standard_session(self, sock):
        try:
            if self.info.has_key(sock):
                self.sender_port = self.info[sock];
            else:
                self.sender_port = ( "", 0)
            call = recvrecord(sock)
            reply = self.handle(call)
            if reply is not None:
                sendrecord(sock, reply)
        except (EOFError, RPCNoHeader):
            try:
                self.logger.debug("closing connection from %s:%d" % sock.getpeername())
                pass
            except socket.error, e:
                self.logger.error("socket error--closing connection: %s" % (
                    str(e)))
            sock.close()
            del self.info[sock]
            self.active.remove(sock)
        except socket.error, msg:
            self.logger.debug("socket error--closing connection: %s" % (
                    str(msg)))
            sock.close()
            del self.info[sock]
            self.active.remove(sock)

    def threaded_session(self, sock):
        t = threading.Thread(target=self.session_in_thread,
                             args=[sock])
        t.start()

    def session_in_thread(self, sock):
        try:
            self.lock.acquire()
            try:
                if self.info.has_key(sock):
                    self.sender_port = self.info[sock];
                else:
                    self.sender_port = ( "", 0)
            finally:
                self.lock.release()
                
            call = recvrecord(sock)

            # make per-thread packer and unpacker
            packer = self.packerClass()
            unpacker = self.unpackerClass('')
            
            reply = self.handle_threaded(call, packer, unpacker)
            if reply is not None:
                sendrecord(sock, reply)
                
        except (EOFError, RPCNoHeader):
            try:
                self.logger.debug("closing connection from %s:%d" % sock.getpeername())
                pass
            except socket.error, e:
                self.logger.error("socket error--closing connection: %s" % (
                    str(e)))
            sock.close()

            self.lock.acquire()
            try:
                try:
                    del self.info[sock]
                except KeyError:
                    pass
                try:
                    self.active.remove(sock)
                except ValueError:
                    pass
            finally:
                self.lock.release()

        except socket.error, msg:
            self.logger.debug("socket error--closing connection: %s" % (
                    str(msg)))
            sock.close()

            self.lock.acquire()
            try:
                try:
                    del self.info[sock]
                except KeyError:
                    pass
                try:
                    self.active.remove(sock)
                except ValueError:
                    pass
            finally:
                self.lock.release()

class AsyncTCPServer(Server):
    def makesocket(self, delay = 1000):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(0)
        try:
            self.sock.setsockopt(socket.SOCK_STREAM, socket.SO_REUSEADDR, 1)
        except:
            self.logger.warn("unable to set SO_REUSEADDR on port.")
        self.prot = IPPROTO_TCP
        self.polling_object = select.poll()
        self.polling_object.register(self.sock, select.POLLIN)
        self.delay = delay
        self.info = {}
        self.socks = {}
        self.read_buffers = {}
        self.write_buffers = {}
        self.client_connections = []
        self.server_connections = []
 
    def beatheart(self):
        pass

    def newsession(self, sock):
        sock, (host, port) = sock
        self.logger.debug("ASYNCRPC new conn from %s:%d" % (host, port))
        sock.setblocking(0)
        self.socks[sock.fileno()] = sock
        self.info[sock] = (host, port)
        self.read_buffers[sock] = ""
        self.write_buffers[sock] = ""
        self.client_callbacks = {}
        self.client_unpack = {}
        self.polling_object.register(sock, select.POLLIN)
        self.server_connections.append(sock)

    def closesession(self, sock):
        self.logger.debug("ASYNCRPC shutting down %s:%d" % self.info[sock])
        self.polling_object.unregister(sock)
        del self.socks[sock.fileno()]
        del self.info[sock]
        del self.read_buffers[sock]
        del self.write_buffers[sock]
        self.server_connections.remove(sock)
        sock.close()

    def mkcred(self):
        # Override this to use more powerful credentials
        if self.cred == None:
            self.cred = (AUTH_NULL, make_auth_null())
        return self.cred

    def mkverf(self):
        # Override this to use a more powerful verifier
        if self.verf == None:
            self.verf = (AUTH_NULL, make_auth_null())
        return self.verf


    def makecall(self, proc, args, pack_func, unpack_func, callback):
        global G_lastxid
        cred = self.mkcred()
        verf = self.mkverf()
        xid = G_lastxid 
        G_lastxid += 1
        p = self.packer
        p.reset()
        
        
    def loop(self):
        self.sock.listen(1)
        self.heartbeat = time.time()
        while not self.quit.isSet():
            # following few lines from asyncore.py included with python2.3
            # Copyright 1996, Sam Rushing <rushing@nightmare.com>
            try:
                timewait = (self.heartbeat-time.time())*1000
                if timewait <=1:
                    timewait = 1
                events = self.polling_object.poll(timewait)
            except select.error, err:
                if err[0] != EINTR:
                    # raise WHAT??
                    raise
                else:
                    events = []
            for iter in events:
                fd, event = iter
                if fd == self.sock.fileno():
                    self.newsession(self.sock.accept())
                else:
                    if event & select.POLLIN:
                        self.asyncread(self.socks[fd])
                    elif event & select.POLLOUT:
                        self.asyncwrite(self.socks[fd])
                    elif event & select.POLLHUP:
                        self.closesession(fd)
                    elif event & select.POLLERR:
                        # raise WHAT??
                        raise
                    elif event & select.POLLNVAL:
                        #print ??
                        pass
            if time.time() > self.heartbeat:
                self.beatheart()
                self.heartbeat = time.time() + (self.delay/1000)

    def asyncread(self, sock):
        try:
            data = sock.recv(32768)
        except socket.error, why:
            if why[0] in (ENOTCONN, ECONNRESET, ESHUTDOWN):
                self.logger.error("ASYNCRPC: ABNORMAL SHUTDOWN OF CONNECTION %s:%d" % self.info[sock])
                self.closesession(sock)
                return
            raise socket.error, why 
        if len(data) == 0:
            self.closesession(sock)
            return
        self.read_buffers[sock] += data
        if len(self.read_buffers[sock]) > 4:
            offset = 0
            last = 0
            while not last and offset+4 < len(self.read_buffers[sock]):
                x = struct.unpack(">L", self.read_buffers[sock][offset:offset+4])[0]
                offset += 4
                last = (( x & 0x80000000L) != 0)
                length = int(x & 0x7fffffff)
                if length > ( len(self.read_buffers[sock]) - offset):
                    return
                offset += length
            record = ""
            offset = 0
            last = 0
            while not last:
                x = struct.unpack(">L", self.read_buffers[sock][offset:offset+4])[0]
                offset += 4
                last = (( x & 0x80000000L) != 0)
                length = int(x & 0x7fffffff)
                record += self.read_buffers[sock][offset:offset+length]
                offset += length
            self.read_buffers[sock] = ""
            self.sender_port = self.info[sock]
            reply = self.handle(record)
            self.write_buffers[sock] = struct.pack(">L", 0x80000000L | len(reply)) + reply 
            self.polling_object.register(sock, select.POLLOUT )
            
    def asyncwrite(self, sock):
        datasent = sock.send(self.write_buffers[sock])
        self.write_buffers[sock] = self.write_buffers[sock][datasent:]
        if len(self.write_buffers[sock]) == 0:
            self.polling_object.register(sock, select.POLLIN)


class UDPServer(Server):

    def makesocket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.prot = IPPROTO_UDP

    def loop(self):
##         try:
##             while not self.quit.isSet():
##                 self.session()
##         finally:
##             self.sock.close()

        try:
            while not self.quit.isSet():
                input = [ self.sock ]
                try:
                    (sin, sout, sexp) = select.select(input, [], [],
                                                      self.timeout)

                except KeyboardInterrupt:
                    return

                if sin != []:
                    self.session()

        finally:
            self.sock.close()

    def session(self):
        call, host_port = self.sock.recvfrom(8192)

        self.sender_port = host_port
        reply = self.handle(call)
        if reply != None:
            self.sock.sendto(reply, host_port)


# Simple test program -- dump local portmapper status

def test():
    pmap = UDPPortMapperClient('')
    list = pmap.Dump()
    list.sort()
    for prog, vers, prot, port in list:
        print prog, vers,
        if prot == IPPROTO_TCP: print 'tcp',
        elif prot == IPPROTO_UDP: print 'udp',
        else: print prot,
        print port


# Test program for broadcast operation -- dump everybody's portmapper status

def testbcast():
    import sys
    if sys.argv[1:]:
        bcastaddr = sys.argv[1]
    else:
        bcastaddr = '<broadcast>'
    def rh(reply, fromaddr):
        host, port = fromaddr
        print host + '\t' + `reply`
    pmap = BroadcastUDPPortMapperClient(bcastaddr)
    pmap.set_reply_handler(rh)
    pmap.set_timeout(5)
    unused_replies = pmap.Getport((100002, 1, IPPROTO_UDP, 0))


# Test program for server, with corresponding client
# On machine A: python -c 'import rpc; rpc.testsvr()'
# On machine B: python -c 'import rpc; rpc.testclt()' A
# (A may be == B)

def testsvr():
    # Simple test class -- proc 1 doubles its string argument as reply
    class S(UDPServer):
        def handle_1(self):
            arg = self.unpacker.unpack_string()
            self.turn_around()
            print 'RPC function 1 called, arg', `arg`
            self.packer.pack_string(arg + arg)
    #
    s = S('', 0x20000000, 1, 0)
    try:
        s.unregister()
    except PortMapError, e:
        print 'RuntimeError:', e.args, '(ignored)'
    s.register()
    print 'Service started...'
    try:
        s.loop()
    finally:
        s.unregister()
        print 'Service interrupted.'


def testclt():
    import sys
    if sys.argv[1:]: host = sys.argv[1]
    else: host = ''
    # Client for above server
    class C(UDPClient):
        def call_1(self, arg):
            return self.make_call(1, arg, \
                    self.packer.pack_string, \
                    self.unpacker.unpack_string)
    c = C(host, 0x20000000, 1)
    print 'making call...'
    reply = c.call_1('hello, world, ')
    print 'call returned', `reply`


# Local variables:
# py-indent-offset: 4
# tab-width: 8
# End:

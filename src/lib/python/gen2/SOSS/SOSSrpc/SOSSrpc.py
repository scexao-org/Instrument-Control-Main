#
# SOSSrpc.py -- SOSS RPC messages class definitions
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Feb  6 12:34:22 HST 2008
#]
# Bruce Bon (Bruce.Bon@SubaruTelescope.org)  2006-11-21
#
#
"""This module provides classes describing the formats of Subaru Telescope
SOSS Observation Control System RPC messages, and convenience methods for
packing and unpacking them.
"""
import os
from Bunch import Bunch
import common
from common import rpcMsgError


class SOSScmdRpcMsgError(common.rpcMsgError):
    pass


class SOSScmdRpcHeader(object):
    """SOSS RPC Header Class.  This is a container for RPC header
    parameters.
    """
   
    def __init__(self, rpcmsg=None):
        """Constructor.  Calls load(rpcmsg) to extract header parameters if
           an RPC message is provided; else calls sethdr() to set default
           header parameters."""

        self.len_hdr = 128

        if rpcmsg:
            self.load(rpcmsg)
        else:
            self.sethdr()


    def load(self, rpcmsg):
        """Extract RPC parameters from message header in rpcmsg into rpcHeader
           variables.  
           If a ValueError or IndexError is detected, raises rpcMsgError."""

        # Mark time received 
        self.timerecd = common.time2timestamp()

        # Split data into fields and parse it
        data = rpcmsg.split(',')

        try:
            self.len_total = int(data[0])
            self.timesent = data[1].strip()
            # mktime treats its argument as a localtime(), i.e. HST, so we
            # must subtract 10 hours (36000.0 seconds):
            self.msg_time = common.timestamp2time( self.timesent ) - 36000.0
            self.protocol_ver = data[2].strip()
            self.seq_num = int(data[3])
            self.sender = data[4].strip()
            self.process_code = int(data[5])
            # uid and gid can be blank, according to SOSS rpc spec, and often
            # are, so we maintain them as strings, not ints.
            self.uid = data[6].strip()
            self.gid = data[7].strip()
            self.receiver = data[8].strip()
            self.pkt_type = data[9].strip()
            self.msg_type = data[10].strip()
            self.len_payload = int(data[11])
            self.reserved = '%27s' % ''
            self.payload = rpcmsg[self.len_hdr:]

        except ValueError, e:
            raise rpcMsgError("malformed SOSS rpc message: '%s'" % rpcmsg)
        except IndexError, e:
            raise rpcMsgError("malformed SOSS rpc message: '%s'" % rpcmsg)


    def sethdr(self, seq_num=1, receiver='', sender=None, pkt_type='', \
               msg_type='', payload='', uid='', gid=''):
        """Extract RPC header parameters into rpcHeader variables."""

        self.len_payload = len(payload)
        self.len_total = self.len_hdr + self.len_payload
        self.protocol_ver = 'SUBARUV1'
        self.seq_num = seq_num
        if not sender:
            self.sender = common.get_myhost(short=True)
        else:
            self.sender = sender
        # TODO: I know this is not really supposed to be the PID,
        # but it will do for now.
        self.process_code = os.getpid()
        self.uid = uid
        self.gid = gid
        self.receiver = receiver
        self.pkt_type = pkt_type
        self.msg_type = msg_type
        self.reserved = '%27s' % ''
        self.payload = payload
        self.timesent = common.time2timestamp()
        self.timerecd = self.timesent
        

class SOSScmdRpcMsg(SOSScmdRpcHeader):
    """RPC Message Class.  Inherits from SOSSrpcHeader.  Includes methods for
    setting the message data payload and formatting a complete packet,
    including RPC header and data payload.  Set functions for the
    data payload are customized for the various SOSS message types.
    """

    def __init__(self, rpcmsg=None, **kwdargs):
        """Constructor.  Initializes RPC header from rpcmsg, then
           sets overrides from kwdargs."""

        SOSScmdRpcHeader.__init__(self, rpcmsg)

        # overrides
        self.set(**kwdargs)

    #
    # Public methods
    #

    def packet2str(self):
        """Build an SOSS RPC packet string, including header parameters and
           the data payload."""

        # Sets self.payload -- does nothing unless method overridden by subclass
        self.pack_payload()

        # TODO: field widths don't seem to truncate fields if they are larger
        pkt = "%010d,%18.18s,%8.8s,%08d,%-8.8s,%5d,%5s,%5.5s,%-8.8s,%2.2s,%2.2s,%010d,%27.27s%s" % (
            self.len_hdr + len(self.payload),
            self.timesent,
            self.protocol_ver,
            self.seq_num,
            self.sender,
            self.process_code,
            self.uid,
            self.gid,
            self.receiver,
            self.pkt_type,
            self.msg_type,
            len(self.payload),
            self.reserved,
            self.payload )
        
        return pkt

    def __str__(self):
        return self.packet2str()


    def set(self, **kwdargs):
        """Convenience function for setting message header values.  Set 
           arbitrary rpcMsg variables from keyword arguments provided by 
           the caller."""
        self.__dict__.update(kwdargs)


    def new_packet(self, **kwdargs):
        """Same as "set", but updates the timesent and seq_num."""

        self.timesent = common.time2timestamp()
        self.seq_num += 1

        self.set(**kwdargs)
        
    
    def make_packet(self, **kwdargs):
        """Like new_packet, but returns the packed packet contents."""

        self.new_packet(**kwdargs)

        return self.packet2str()


    def pack_payload(self):
        """Does nothing.  May be overridden by a subclass to pack its 
           own payload on a packet2str."""
        pass

    
    # "AB" call--acknowledgement call for the rpc-based SOSS handshake
    # After receiving a cmd message, we respond with an "AB" message
    # indicating message received and command commencing.
    # THIS IS COMMON TO 'CT', 'DT' and 'FT' packet formats
    #
    def pack_ab(self, ref_seq_num, result, **kwdargs):
        """Set self.payload to be the data payload for an AB message."""

        # AB args are sequence number and result code
        payload = "%08d,%4d" % (ref_seq_num, result)

        self.new_packet(msg_type='AB', payload=payload, **kwdargs)

    def unpack_ab(self):
        """Unpack self.payload from an AB message."""
        try:
            (seq_num, result) = self.payload.split(',')
            seq_num = int(seq_num)
            result = int(result)

        except (ValueError, TypeError), e:
            raise rpcMsgError("SOSS RPC AB payload format error: %s" % str(e))

        return Bunch(seq_num=seq_num, result=result)


    # "CD" call--initial call for the rpc-based SOSS handshake
    # Takes a frame id and a file path and sends a CD message to the obcp
    # requesting it to execute a command.
    #
    def pack_cd(self, cmd, **kwdargs):
        """Set self.payload to be the data payload for a CD message."""

        # DS args are file path, size and frame number
        payload = cmd

        self.new_packet(pkt_type='CT', msg_type='CD', payload=payload, \
                        **kwdargs)

    def unpack_cd(self):
        """Unpack self.payload from a CD message."""
        cmdstr = self.payload.strip()
        
        return Bunch(cmdstr=cmdstr)

        
    # "EN" call--completion notification call for the rpc-based
    # SOSS handshake.
    #
    def pack_en(self, ref_seq_num, status, result, **kwdargs):
        """Set self.payload to be the data payload for an EN message."""

        # EN args are sequence number, status and result 
        payload = "%08d,%4d,%s" % (ref_seq_num, status, result)

        self.new_packet(pkt_type='CT', msg_type='EN', payload=payload, \
                        **kwdargs)

    def unpack_en(self):
        """Unpack self.payload from a EN message."""
        try:
            payload = self.payload.split(',')
            seq_num = int(payload[0])
            result = int(payload[1])
            # 'application-level' payload
            payload = ','.join(payload[2:])

        except (ValueError, IndexError, TypeError), e:
            raise rpcMsgError("SOSS RPC CT,EN payload format error: %s" % str(e))

        return Bunch(seq_num=seq_num, result=result, payload=payload)


    # "DS" call--initial call for the rpc-based SOSS handshake
    # Takes a frame id and a file path and sends a DS message to the server
    # requesting it to transfer the file.
    #
    def pack_ds(self, framelist, **kwdargs):
        """Set self.payload to be the data payload for a DS message."""

        l = []
        for frameinfo in framelist:
            # DS args are file path, size and frame number, in some multiple
            # i.e. (filepath, size, frame) == frameinfo
            l.append("%s,%d,%s" % frameinfo)

        payload = ','.join(l)
        self.new_packet(pkt_type='DT', msg_type='DS', payload=payload, \
                        **kwdargs)

    def unpack_ds(self):
        """Unpack self.payload from a DS message."""

        try:
            # Unpack payload.  At the end, _framelist_ will contain a list of
            # tuples of the form (path, size, frameid)--one for each file to
            # be transferred.
            framelist = []
            contents = self.payload.split(',')
            while len(contents) > 0:
                path = contents.pop(0).strip()
                size = int(contents.pop(0))
                frameid = contents.pop(0).strip().upper()
                framelist.append((path, size, frameid))

        except (ValueError, TypeError), e:
            raise rpcMsgError("SOSS RPC DT,DS payload format error: %s" % str(e))

        return Bunch(path=path, size=size, frameid=frameid, framelist=framelist)


    # "DE" call--completion notification call for the rpc-based
    # SOSS handshake
    #
    def pack_de(self, ref_seq_num, result, statuslist, **kwdargs):
        """Set self.payload to be the data payload for a DE message."""

        # DE args are sequence number, result and status codes for each
        # transferred frame.
        cmdres = ["%08d" % ref_seq_num, "%4d" % result]
        
        for status in statuslist:
            cmdres.append("%4d" % status) 
            
        payload = ",".join(cmdres)

        self.new_packet(pkt_type='DT', msg_type='DE', payload=payload, \
                        **kwdargs)


    def unpack_de(self):
        """Unpack self.payload from a DE message."""
        try:
            statuslist = self.payload.split(',')
            seq_num = statuslist.pop(0)
            seq_num = int(seq_num)
            statuslist = map(int, statuslist)
            result = statuslist.pop(0)

        except (ValueError, TypeError), e:
            raise rpcMsgError("SOSS RPC DT,DE payload format error: %s" % str(e))

        return Bunch(seq_num=seq_num, result=result, statuslist=statuslist)


    # "FS" call--STARS command call for the rpc-based SOSS handshake.
    #
    def pack_fs(self, fitspath, fitssize, frameid, propid, dsthost, channel, \
                indexpath, indexsize, **kwdargs):
        """Set self.payload to be the data payload for an FS message."""

        payload = "%s,%d,%s,%s,%s,%s,%s,%s" % \
                  (fitspath, fitssize, frameid, propid, dsthost, channel, \
                   indexpath, indexsize)

        self.new_packet(pkt_type='FT', msg_type='FS', payload=payload, \
                        **kwdargs)

    def unpack_fs(self):
        """Unpack self.payload from a FS message."""
        try:
            data = self.payload.split(',')
            (fitspath, fitssize, frameid, propid, starsdir, version,
             indexpath, indexsize) = data
            fitssize = int(fitssize)
            indexsize = int(indexsize)

        except ValueError, e:
            raise rpcMsgError("SOSS RPC FT,FS payload error: %s" % str(e))

        return Bunch(fitspath=fitspath, fitssize=fitssize, frameid=frameid,
                     propid=propid, starsdir=starsdir, version=version,
                     indexpath=indexpath, indexsize=indexsize)

        
    # "FE" call--completion notification call for the rpc-based
    # SOSS handshake.
    #
    def pack_fe(self, ref_seq_num, result, status1, status2, **kwdargs):
        """Set self.payload to be the data payload for an FE message."""

        # FE args are sequence number, overall result, and individual status codes
        # for main fits file and index file.
        payload = "%08d,%4d,%4d,%4d" % (ref_seq_num, result, status1, status2)

        self.new_packet(pkt_type='FT', msg_type='FE', payload=payload, \
                        **kwdargs)

    def unpack_fe(self):
        """Unpack self.payload from a FE message."""
        try:
            (seq_num, status1, status2, result) = self.payload.split(',')
            seq_num = int(seq_num)
            status1 = int(status1)
            status2 = int(status2)
            result = int(result)

        except ValueError, e:
            raise rpcMsgError("SOSS RPC FT,FE payload format error: %s" % str(e))

        return Bunch(seq_num=seq_num, status1=status1, status2=status2, result=result)
    
        
    # "SD" call--status transmission call for the rpc-based SOSS handshake.
    #
    # (see examples in obc1:/app/OBC/log/obsstat.log)
    #
    def pack_sd(self, tblname, statusdata, **kwdargs):
        """Set self.payload to be the data payload for an SD message."""

        # SD args are destination status table name + status data
        # NOTE: do some instruments use a space instead of a comma between the table name
        # and the data?
        payload = "%-8.8s,%s" % (tblname, statusdata)

        self.new_packet(pkt_type='ST', msg_type='SD', payload=payload, 
                        **kwdargs)

    def unpack_sd(self):
        """Unpack self.payload from a FE message."""
        try:
            tablename  = self.payload[0:8]
            statusdata = self.payload[9:]

        except IndexError, e:
            raise rpcMsgError("SOSS RPC SD payload format error: %s" % str(e))

        return Bunch(tablename=tablename, statusdata=statusdata)

#END

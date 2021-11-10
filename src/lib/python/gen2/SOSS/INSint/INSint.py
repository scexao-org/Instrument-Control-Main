#!/usr/bin/env python
#
# INSint.py -- Interface with DAQtk-based Subaru Observatory instruments.
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Tue May 22 10:19:00 HST 2012
#]
#[ Bruce Bon (bon@naoj.org) --
#  Last edit: Mon Nov 15 13:19 HST 2006
#]
#
import sys, re, time, os
import threading, Queue
import datetime
# profile imported below (if needed)
# pdb imported below (if needed)
# optparse imported below (if needed)

import rpc
import SOSS.SOSSrpc as SOSSrpc
from Bunch import Bunch, threadSafeBunch
import Task
import remoteObjects as ro
import remoteObjects.Monitor as Monitor
# SOSS.status imported below (if needed)
import logging, ssdlog
import BaseInterface
import Gen2.db.frame as framedb

from cfg.INS import INSdata
from DAQtkDatSndMemtypes import *
import DAQtkDatSndMempacker

# Version/release number
version = "20120410.0"

# Service name prefix for directory of remote objects
serviceName_pfx = 'INSint'

# Default number of files to transfer in parallel
groups_of = 10

class INSintError(Exception):
    """Instrument Interface Error Exception.  Inherits from Exception and
       adds no functionality, but distinct name allows distinct catch
       clauses."""
    pass


# HELPER CLASSES/FUNCTIONS

class FetchStatusWrapper_SOSS(object):
    """Wraps a simple class around a dictionary interface of status data.
    This makes an interface compatible with the SOSS status system.
    """
    def __init__(self, statusDict):
        self.statusDict = statusDict

    def fetch(self, fetchDict, fetchList):
        for alias in fetchList:
            try:
                fetchDict[alias] = self.statusDict[alias]
            except Exception, e:
                # TODO: put error value in fetchDict?
                raise e
                pass

class FetchStatusWrapper_Gen2(object):
    """Wraps a simple class around a Gen2 (remote) status interface.
    This makes an interface compatible with the Gen2 status system.
    """
    def __init__(self, remoteStatusObj):
        self.statusObj = remoteStatusObj

    def fetch(self, fetchDict, fetchList):
        # Create a dictionary whose keys are aliases
        argDict = {}
        for alias in fetchList:
            argDict[alias] = 0

        try:
            resDict = self.statusObj.fetch(argDict)
            #fetchDict.update(resDict)
            # SOSS status has a feature where it inserts double quotes
            # around any status value that is a string and has embedded
            # spaces.  The Gen2 status system does not have this feature
            # so we need to convert them here so that values with whitespace
            # can cross the instrument interface.
            # TODO: this is fairly inefficient; try to improve it
            for key, val in resDict.items():
                if isinstance(val, str) and (not val.startswith('"')) \
                   and (len(val.split()) > 1):
                    fetchDict[key] = ('"%s"' % val)
                else:
                    fetchDict[key] = val
                
        except Exception, e:
            raise e
            #pass

                
class DDCommandChannel(BaseInterface.BaseInterface):
    """Instrument Command Interface Class.  An object of this class executes 
    Device Dependent (DD) commands using RPC transactions with an OBCP.  
    It contains an RPC client to send DD commands to the OBCP, and an RPC 
    server to receive corresponding Ack (AB) and Completion (EN) messages 
    from the OBCP.
    """
    def __init__(self, obcpnum, obcphost, ev_quit, logger, db, taskqueue,
                 myhost=None, myport=None, seq_num=None, monchannels=[]):
        """Class constructor.

        See BaseInterface for common parameters to all interfaces.

        Unique parameters:
          obcpnum: the number of the OBCP we are going to communicate with.
          Used to look up the correct RPC parameters.

          obcphost: the host name of the OBCP.

          monchannels: a list of monitor channels to use for announcing
          events on our local monitor.  Any other Monitor subscribing to
          these channels will receive our updates.
        """

        # Initialize common attributes
        super(DDCommandChannel, self).__init__(ev_quit, logger, db,
                                               taskqueue,
                                               myhost=myhost, myport=myport,
                                               seq_num=seq_num)
        
        self.obcphost = obcphost
        self.obcpnum = obcpnum
        self.monchannels = monchannels
        self.key_template = 'cmd.%d'
        self.sendTasker = Task.make_tasker(self.cmd_send)
        self.recvTasker = Task.make_tasker(self.cmd_recv)
        
        # Look up obcp command RPC parameters
        try:
            rpckey = ('OBStoOBCP%d(cmd)' % obcpnum)

            self.rpcconn = SOSSrpc.clientServerPair(rpckey, initiator=True,
                                                    logger=self.logger,
                                                    #ev_quit=self.ev_quit,
                                                    #myhost=self.myhost,
                                                    recvqueue=self.taskqueue,
                                                    func=self.recvTasker)

        except SOSSrpc.rpcError, e:
            raise INSintError("Error creating rpc client-server pair: %s" % \
                              str(e))

        # Restore sequence number from db in case of a restart
        key = 'cmd.%d.seq_num' % (self.obcpnum)
        if self.db.has_key(key):
            self.seq_num.reset(self.db[key])


    def _get_key(self, seq_num):
        return self.key_template % seq_num
    
    def put_trans(self, seq_num, tag):
        key = self._get_key(seq_num)

        # Is there a cmdb bundle for this seq_num?
        if self.db.has_key(key):
            raise INSintError("Tag exists matching sequence number %d" % \
                              (seq_num))

        else:
            self.db[key] = tag

    def get_trans(self, seq_num):
        key = self._get_key(seq_num)

        # Is there a bundle for this seq_num?
        if self.db.has_key(key):
            return self.db[key]

        else:
            raise INSintError("No tag matching sequence number %d" % \
                              (seq_num))

    def del_trans(self, seq_num, tag):
        """This is called to delete a transaction from the pending transaction
        table (self.db).  The transaction tag is deleted under (key) IFF the
        transaction contains all three RPC components: cmd, ack, end
        """
        key = self._get_key(seq_num)

        # Raises an exception if tag not found?
        if not self.db.has_key(key):
            self.logger.warn("No command data found for tag '%s'" % tag)
            return

        cmdb = self.db.get_node(tag)
        cmdb.enter()
        try:
            if cmdb.has_key('cmd') and cmdb.has_key('ack') and \
                   cmdb.has_key('end'):
                try:
                    del self.db[key]
                except KeyError:
                    pass

        finally:
            cmdb.leave()


    def cmd_send(self, tag):
        """Look up the command information registered under _tag_,
        and send the string command to the instrument.
        """

        seq_num = -1
        try:
            # Raises an exception if tag not found?
            if not self.db.has_key(tag):
                raise INSintError("No command data found for tag '%s'" % tag)

            cmdb = self.db.get_node(tag)

            # Create RPC message
            rpcbuf = SOSSrpc.SOSScmdRpcMsg(sender=self.myhost,
                                           receiver=self.obcphost,
                                           pkt_type='CT')

            # Get new sequence number for this transaction
            seq_num = self.seq_num.bump()

            # Pack rpc buffer with command
            rpcbuf.pack_cd(cmdb.cmd_str, seq_num=seq_num)

            # Inform monitor of impending event
            self.db.setvals(self.monchannels, tag, seq_num=seq_num,
                            cmd_time=time.time())
            # Associate this tag with this seq_num
            self.put_trans(seq_num, tag)

            # Make the rpc client call
            try:
                res = self.rpcconn.callrpc(rpcbuf)

            except SOSSrpc.rpcClientError, e:
                raise INSintError("rpc error sending CD command: %s" % str(e))

        except INSintError, e:
            self.cmd_error(e, seq_num, tag)
        
        except Exception, e:
            self.cmd_error(e, seq_num, tag)
            raise e
        

    def send_cmd(self, tag):
        self.logger.debug("Adding task to task queue for tag '%s'" % tag)
        self.taskqueue.put(self.sendTasker(tag))
        
            
    def validate_ack(self, tag, result):
        """Validate the contents of the ack message received from
        the instrument.
        """

        cmdb = self.db.get_node(tag)
        
        # Is there an AB record for this seq_num?
        if cmdb.has_key('ack_time'):
            raise INSintError("Error ack reply: duplicate ack record matching sequence number (%d)" % \
                                (cmdb.seq_num))

        # Record AB record for this seq_num
        self.db.setvals(self.monchannels, tag, ack_time=time.time(),
                        ack_result=result)

        # Is there a command record for this seq_num?  Should be.
        if not cmdb.has_key('cmd_time'):
            raise INSintError("Error in ack reply: no command record matching sequence number (%d)" % \
                                (cmdb.seq_num))

        # Is there an CE record for this seq_num?  Should not be.
        # This should be a warning...depending on network delays CE could
        # arrive before AB
        if cmdb.has_key('end_time'):
            errmsg = "ack reply: end record exists matching sequence number (%d)" % (cmdb.seq_num)
            #raise INSintError(errmsg)
            self.logger.warn(errmsg)

        # Error in AB result code?
        if result != 0:
            raise INSintError("Error ack reply: result=%d" % result)
        

    def validate_end(self, tag, result, payload):
        """Validate the contents of the end command message received from
        the instrument.
        """

        cmdb = self.db.get_node(tag)
        
        # Is there an CE record for this seq_num?
        if cmdb.has_key('end_time'):
            raise INSintError("Error end reply: duplicate end record matching sequence number (%d)" % \
                                (cmdb.seq_num))

        # Record CE record for this seq_num
        self.db.setvals(self.monchannels, tag, end_time=time.time(),
                        end_result=result, end_payload=payload)

        # Is there a command record for this seq_num?  Should be.
        if not cmdb.has_key('cmd_time'):
            raise INSintError("Error in ack reply: no command record matching sequence number (%d)" % \
                                (cmdb.seq_num))

        # Is there an AB record for this seq_num? Should be.
        if not cmdb.has_key('ack_time'):
            # Depending on network delays CE could arrive before AB...
            errmsg = "end reply: no ack record matching sequence number (%d)" % \
                     (cmdb.seq_num)
            ##raise INSintError(errmsg)
            self.logger.warn(errmsg)

        if result != 0:
            raise INSintError("Error end reply: result=%d, payload=%s" % \
                                (result, payload))
        

    def cmd_recv(self, rpcmsg):
        """Process packets sent by the intrument on the command channel in response
        to a command sent.  Normally there will be two types of packets sent: an ACK
        and an END.
        """

        # Until we have seq_num in payload we don't know which
        # command this is associated with
        tag = None
        seq_num = -1
        try:
            # Call handler for appropriate rpc msg type
            if rpcmsg.msg_type == 'AB':
                try:
                    data = rpcmsg.unpack_ab()

                except SOSSrpc.rpcMsgError, e:
                    raise INSintError("SOSS RPC payload format error: %s" % str(e))

                # Look up the transaction matching this seq_num
                seq_num = data.seq_num
                tag = self.get_trans(seq_num)

                # Validate packet and record result
                self.validate_ack(tag, data.result)

            elif rpcmsg.msg_type == 'EN':
                try:
                    data = rpcmsg.unpack_en()
                    
                except SOSSrpc.rpcMsgError, e:
                    raise INSintError("SOSS RPC payload format error: %s" % str(e))
                
                # Look up the transaction matching this seq_num
                seq_num = data.seq_num
                tag = self.get_trans(seq_num)

                self.validate_end(tag, data.result, data.payload)

                # End command validated
                self.db.setvals(self.monchannels, tag,
                                msg='cmd transaction with OBCP complete',
                                time_done=time.time(), result=0,
                                done=True)

            else:
                raise INSintError("Different reply than AB or EN!")

            # Delete our reference to the transaction so as not to leak memory
            if tag:
                self.del_trans(seq_num, tag)

        except INSintError, e:
            self.cmd_error(e, seq_num, tag)

        except Exception, e:
            self.cmd_error(e, seq_num, tag)
            raise e
                    

    # This is called when we have an error anywhere in the process of
    # sending a command to the instrument.
    #
    def cmd_error(self, e, seq_num, tag):
        # Log the exception that led to us being called
        msg = str(e)
        self.logger.error(msg)

        # Signal to any waiters on this command that we are done
        if tag:
            self.db.setvals(self.monchannels, tag, msg=msg,
                            time_done=time.time(), result=-1,
                            done=True)

            # Delete our reference to the cmdb so as not to leak memory
            self.del_trans(seq_num, tag)


class ThroughCommand(BaseInterface.BaseInterface):
    """Instrument Command Through Command Interface Class.  An object of
       this class receives and services requests for device-dependent
       command execution from an OBCP.  It contains an RPC server to
       receive request messages (CD), and an RPC client to 
       send Ack (AB) and Completion (EN) messages back to the OBCP."""

    def __init__(self, ev_quit, logger, db, taskqueue, 
                 myhost=None, myport=None, seq_num=None):
        """Class constructor.

        See BaseInterface for common parameters to all interfaces.

        Unique parameters:
          None
        """

        # Initialize common attributes
        super(ThroughCommand, self).__init__(ev_quit, logger, db,
                                             taskqueue,
                                             myhost=myhost, myport=myport,
                                             seq_num=seq_num)
        
        self.recvTasker = Task.make_tasker(self.thru_recv)

        # Look up 
        try:
            key = 'OBCPtoOBS(thru)'

            self.rpcconn = SOSSrpc.clientServerPair(key, initiator=False,
                                                    logger=self.logger,
                                                    #ev_quit=self.ev_quit,
                                                    #myhost=self.myhost,
                                                    recvqueue=self.taskqueue,
                                                    func=self.recvTasker)

        except SOSSrpc.rpcError, e:
            raise INSintError("Error creating rpc client-server pair: %s" % \
                              str(e))


    def thru_recv(self, rpcmsg):

        if rpcmsg.msg_type != 'CD':
            raise INSintError("rpc msg is not a SOSS CD request")

        sender = rpcmsg.sender.lower()

        try:
            data = rpcmsg.unpack_cd()
            dd_cmd = data.cmdstr

        except SOSSrpc.rpcMsgError, e:
            raise INSintError("SOSS RPC payload format error: %s" % str(e))
            
        self.logger.info("DD through command: '%s'" % dd_cmd)

        status = 0
        # TODO: check for syntax?
            
        # Create buffer for RPC message
        rpcbuf = SOSSrpc.SOSScmdRpcMsg(sender=self.myhost, pkt_type='CT')
        
        # Send AB message
        rpcbuf.pack_ab(rpcmsg.seq_num, status, receiver=rpcmsg.sender,
                       seq_num=self.seq_num.bump())
        try:
            res = self.rpcconn.callrpc(rpcbuf)

        except SOSSrpc.rpcClientError, e:
            raise INSintError("rpc error sending AB reply: %s" % str(e))
        
        status = 1
        result = 'ERROR,through commands not supported'
            
        # Send EN message
        rpcbuf.pack_en(rpcmsg.seq_num, status, result,
                       seq_num=self.seq_num.bump())
        try:
            res = self.rpcconn.callrpc(rpcbuf)

        except SOSSrpc.rpcClientError, e:
            raise INSintError("rpc error sending EN reply: %s" % str(e))

        self.logger.debug("Processed through command successfully!")


class StatusRequest(BaseInterface.BaseInterface):
    """Instrument Status Request Interface Class.  An object of this class 
       receives and services requests for status from an OBCP.  It contains 
       an RPC server to receive request messages (CD), and an RPC client to 
       send Ack (AB) and Completion (EN) messages back to the OBCP."""

    def __init__(self, ev_quit, logger, db, taskqueue, statusObj,
                 myhost=None, myport=None, seq_num=None,
                 hostfilterDict=None):
        """Class constructor.

        See BaseInterface for common parameters to all interfaces.

        Unique parameters:
          statusObj: a FetchStatusWrapper_Gen2 or FetchStatusWrapper_SOSS
          object to interface to the status system of the OCS.  Used to
          obtain status for resolving status requests.

          hostfilterDict: a dictionary of hosts from which we will accept
          status requests.  If the host name ('sender' field as pulled
          from the RPC packet) is in the dictionary, we accept the request,
          otherwise we drop it.  If None, then requests from all hosts
          are accepted.
        """

        # Initialize common attributes
        super(StatusRequest, self).__init__(ev_quit, logger, db,
                                            taskqueue,
                                            myhost=myhost, myport=myport,
                                            seq_num=seq_num)
        
        self.statusObj = statusObj
        self.hostfilter = hostfilterDict
        self.clients = {}
        self.client_lock = threading.RLock()
        self.recvTasker = Task.make_tasker(self.sreq_recv)

        # Look up 
        try:
            key = 'OBCPtoOBS(sreq)'

            self.rpcconn = SOSSrpc.clientServerPair(key, initiator=False,
                                                    logger=self.logger,
                                                    #ev_quit=self.ev_quit,
                                                    #myhost=self.myhost,
                                                    recvqueue=self.taskqueue,
                                                    func=self.recvTasker)

        except SOSSrpc.rpcError, e:
            raise INSintError("Error creating rpc client-server pair: %s" % \
                              str(e))


    def get_client(self, host):

        host = host.lower()

        self.client_lock.acquire()
        try:

            if self.clients.has_key(host):
                # Cached lazy client for this host; use it
                return self.clients[host]

            # Else look up prognum and create a new lazy client
            # for this host and cache it
            try:
                key = 'OBCPtoOBS(sreq)'
                bnch = SOSSrpc.lookup_rpcsvc(key)

            except KeyError:
                raise statusReceiveError("Error creating rpc client: no such key '%s'" % \
                                  key)

            prognum = bnch.server_send_prgnum
            
            self.clients[host] = SOSSrpc.lazyClient(host=host,
                                                    prognum=prognum,
                                                    logger=self.logger)
            return self.clients[host]

        finally:
            self.client_lock.release()
        
            
    def sreq_recv(self, rpcmsg):

        if rpcmsg.msg_type != 'CD':
            raise INSintError("rpc msg is not a SOSS CD request")

        # Optional host filtering--drop the packet if it comes from a
        # host that we haven't explicitly allowed
        sender = rpcmsg.sender.lower()
        if (self.hostfilter != None) and (not self.hostfilter.has_key(sender)):
            self.logger.warn("Host '%s' not in filter list--dropping packet" % \
                sender)
            return

        try:
            data = rpcmsg.unpack_cd()

        except SOSSrpc.rpcMsgError, e:
            raise INSintError("SOSS RPC payload format error: %s" % str(e))

        # Format of command should be STATUS,ALIAS,ALIAS,...
        try:
            (cmd, aliases) = data.cmdstr.split(',')
            if cmd != 'STATUS':
                raise INSintError("Status request command format error: '%s'" % rpcmsg.payload)
            
        except (ValueError, TypeError), e:
            raise INSintError("Status request command format error: '%s'" % rpcmsg.payload)
            
        # TODO: check for validity of all status variables

        # Create buffer for RPC message
        rpcbuf = SOSSrpc.SOSScmdRpcMsg(sender=self.myhost, pkt_type='CT')
        
        # Send AB message
        rpcbuf.pack_ab(rpcmsg.seq_num, 0, receiver=rpcmsg.sender,
                       seq_num=self.seq_num.bump())

        # Get client handle back to requestor
        rpcconn = self.get_client(sender)
        
        try:
            res = rpcconn.callrpc(rpcbuf)

        except SOSSrpc.rpcClientError, e:
            raise INSintError("rpc error sending AB reply: %s" % str(e))
        
        # Get the requested status from the statusObj interface
        aliases = aliases.replace('$', '').split()

        # Actually fetch the status values from status system
        status = 0
        result = 'COMPLETE'
        try:
            # This fetches the data from the status server
            # TODO: reuse same dictionary?
            fetchDict = {}
            self.statusObj.fetch(fetchDict, aliases)
                
            # Now pack data up for return trip
            data = []
            for alias in aliases:
                try:
                    #data.append(str(self.fetchDict[alias]))
                    data.append('%-64.64s' % str(fetchDict[alias]))

                except Exception, e:
                    self.logger.error("error getting status for '%s': %s" % (alias, str(e)))

                    # We should return UNDEF for individual status aliases that
                    # that we cannot retrieve
                    #data.append('UNDEF')
                    data.append('%-64.64s' % 'UNDEF')

            # Result of command is whitespace-joined data with "COMPLETE,"
            # at beginning
            data = ' '.join(data)
            result = result + ',' + data

        except Exception, e:
            self.logger.error("error getting status: %s" % str(e))

            status = 1
            result = 'ERROR,'
            
        # Send EN message
        rpcbuf.pack_en(rpcmsg.seq_num, status, result,
                       seq_num=self.seq_num.bump())
        try:
            res = rpcconn.callrpc(rpcbuf)

        except SOSSrpc.rpcClientError, e:
            raise INSintError("rpc error sending EN reply: %s" % str(e))

        self.logger.debug("Processed status request successfully!")


class StatusReceiver(BaseInterface.BaseInterface):
    """Instrument Status Receiver class. An object of this class receives 
       status data messages (SD) from an OBCP.  It contains an RPC server 
       to receive SD messages."""

    def __init__(self, monunitnum, ev_quit, logger, db, taskqueue,
                 statusObj=None, myhost=None, myport=None, seq_num=None):
        """Class constructor.

        See BaseInterface for common parameters to all interfaces.

        Unique parameters:
          monunitnum: the 'SOSS monitor unit number' (0-6) on which to
          listen for incoming status packets.  This has nothing to do
          with the Gen2 monitor.  Basically, used to look up the correct
          RPC configuration.
        """

        # Initialize common attributes
        super(StatusReceiver, self).__init__(ev_quit, logger, db,
                                             taskqueue,
                                             myhost=myhost, myport=myport,
                                             seq_num=seq_num)
        
        self.monunitnum = monunitnum
        # Delegate object to send our status tables to
        self.statusObj = statusObj
        self.recvTasker = Task.make_tasker(self.sdst_recv)

        # Look up 
        try:
            key = ('toOBS%d(sdst)' % monunitnum)

            self.rpcconn = SOSSrpc.clientServerPair(key, initiator=False,
                                                    logger=self.logger,
                                                    #ev_quit=self.ev_quit,
                                                    #myhost=self.myhost,
                                                    recvqueue=self.taskqueue,
                                                    func=self.recvTasker)

        except SOSSrpc.rpcError, e:
            raise INSintError("Error creating rpc client-server pair: %s" % \
                              str(e))


    def sdst_recv(self, rpcmsg):
        """Check input queue for a message from the RPC server.  If time-out,
           then return None; if got a message, log it and return it.
           Called from the status processing loop method."""

        # Validate packet format
        if rpcmsg.msg_type != 'SD':
            raise INSintError("rpc msg is not a SOSS SD packet")

        try:
            data = rpcmsg.unpack_sd()

        except SOSSrpc.rpcMsgError, e:
            raise INSintError("SOSS RPC payload format error: %s" % str(e))
        
        # Send status table to status system
        tablename  = data.tablename
        statusdata = data.statusdata

        self.logger.info("Got table [%s]" % (tablename))
        if self.statusObj:
            self.statusObj.put_table(tablename, statusdata)


class FITS_recvServer(SOSSrpc.TCP_rpcServer):
    """Instrument FITS File RPC Receiver Class.  Inherits from 
       SOSSrpc.TCP_rpcServer.  This class contains an RPC function/method 
       (handle_1) that receives an RPC message and adds it to a queue of 
       received messages (rpcqueue).  Used by ArchiveRequest."""

    def addpackers(self):
        self.packer = DAQtkDatSndMempacker.DAQTKDATSNDMEMPacker()
        self.unpacker = DAQtkDatSndMempacker.DAQTKDATSNDMEMUnpacker('')

    def handle_1(self):
        """RPC method called by external host."""
        if self.logger:
            self.logger.debug("received RPC FITS packet")

        rpcmsg = self.unpacker.unpack_DAQtkRpcFits()
        #if self.logger:
        #    self.logger.debug("cframe.len=%d" % len(rpcmsg.cframe))
        #l = map(chr, rpcmsg.cframe)
        #i = l.find('\0')
        #if i > 0:
        #    l = l[:i]
        #rpcmsg.cframe = ''.join(l)
        #if self.logger:
        #    self.logger.debug("RPC fits xfr: '%s'" % str(rpcmsg))
        
        # Add message to queue of received messages
        self.rpcqueue.put(rpcmsg)

        try:
            self.turn_around()
            
        except rpc.RPCUnextractedData:
            if self.logger:
                self.logger.error("Unextracted data in request!")

        # Return confirmation result
        res = True
        self.packer.pack_bool(res)


class ArchiveRequest(BaseInterface.BaseInterface):
    """Instrument FITS File Receiver Class."""

    def __init__(self, obcpnum, raidpath, ev_quit, logger, db, taskqueue,
                 hostfilterDict=None,
                 username=None, transfermethod='scp',
                 myhost=None, myport=None, seq_num=None,
                 fitsport=None, monchannels=[]):
        """Class constructor.

        See BaseInterface for common parameters to all interfaces.

        Unique parameters:
          obcpnum: the number of the OBCP we are going to communicate with.
          Used to look up the correct RPC parameters.

          raidpath: a path to a directory in which to store incoming FITS
          files.

          hostfilterDict: a dictionary of hosts from which we will accept
          transfer requests.  If the host name ('sender' field as pulled
          from the RPC packet) is in the dictionary, we accept the request,
          otherwise we drop it.  If None, then requests from all hosts
          are accepted.

          username: if using FTP or SCP transfer, the username to log into
          the OBCP with.

          transfermethod: One of FTP|SCP|RPC.  Only IRCS uses RPC for the
          actual file transfer (as opposed to the 'request' for the file
          transfer).  Please don't use it--it is a bad custom protocol that
          should never have been used.

          fitsport: If using transfermethod==RPC (don't!), the port to use
          for the RPC server.  Default of None will select a random, unused
          port.
          
          monchannels: a list of monitor channels to use for announcing
          events on our local monitor.  Any other Monitor subscribing to
          these channels will receive our updates.
        """

        # Initialize common attributes
        super(ArchiveRequest, self).__init__(ev_quit, logger, db,
                                             taskqueue,
                                             myhost=myhost, myport=myport,
                                             seq_num=seq_num)
        
        self.hostfilter = hostfilterDict
        self.monchannels = monchannels
        # TODO: parameterize tag template
        self.tag_template = 'mon.frame.%s.INSint'
        self.recvTasker = Task.make_tasker(self.file_recv)

        # Look up 
        try:
            key = ('OBCP%dtoOBC(file)' % obcpnum)

            self.rpcconn = SOSSrpc.clientServerPair(key, initiator=False,
                                                    logger=self.logger,
                                                    #ev_quit=self.ev_quit,
                                                    #myhost=self.myhost,
                                                    recvqueue=self.taskqueue,
                                                    func=self.recvTasker)
        except SOSSrpc.rpcError, e:
            raise INSintError("Error creating rpc client-server pair: %s" % \
                              str(e))

        # TODO: check write access to this directory
        self.raidpath = os.path.abspath(raidpath)
        # Get the current username as the login for transfers if one was not
        # provided.
        if not username:
            #username = getpass.getuser()
            username = os.environ['LOGNAME']  #was os.getlogin()
        self.username = username
        self.transfermethod = transfermethod.lower()
            
        # If this is an instrument that sends FITS files via RPC calls,
        # then we need to enable this server.
        if self.transfermethod == 'rpc':
            try:
                key = ('OBCP%dtoOBC(rpc)' % obcpnum)
                svc = SOSSrpc.lookup_rpcsvc(key)

            except KeyError, e:
                raise INSintError("Can't find rpc program numbers (key=%s)" % key)

            # Create a FITS receive RPC server, if necessary
            self.fitsrecv = FITS_recvServer(host='', port=fitsport,
                                            prognum=svc.server_receive_prgnum,
                                            #ev_quit=self.ev_quit,
                                            logger=self.logger)
        else:
            self.fitsrecv = None

        self.data_timeout = 240.0
        # Number of files to transfer in parallel
        self.max_group_size = groups_of

    def file_recv(self, rpcmsg):

        if rpcmsg.msg_type != 'DS':
            raise INSintError("rpc msg is not a SOSS DS request")

        sender = rpcmsg.sender.lower()
        if (self.hostfilter != None) and (not self.hostfilter.has_key(sender)):
            self.logger.warn("Host '%s' not in filter list--dropping packet" % \
                sender)
            return

        result = 0
        msg = '[N/A]'
        try:
            data = rpcmsg.unpack_ds()

            cmd_time = time.time()
        
        except SOSSrpc.rpcMsgError, e:
            result = 1
            msg = "SOSS RPC payload format error: %s" % str(e)
            # don't raise exception--log error and send ACK with error status
            self.logger.error(msg)

        # Create buffer for RPC message
        rpcbuf = SOSSrpc.SOSScmdRpcMsg(sender=self.myhost, pkt_type='DT')

        ack_time = time.time()
        # Send AB (ack) message
        rpcbuf.pack_ab(rpcmsg.seq_num, result, receiver=rpcmsg.sender,
                       seq_num=self.seq_num.bump())
        try:
            res = self.rpcconn.callrpc(rpcbuf)

        except SOSSrpc.rpcClientError, e:
            msg = "rpc error sending AB reply: %s" % str(e)
            raise INSintError(msg)

        # Stop here if there was a problem unpacking the request,
        # otherwise proceed to try and transfer the file.
        if result != 0:
            return

        # Record results to monitor for each frameid
        framelist  = data.framelist
        total_bytes = 0
        for (path, size, frameid) in framelist:
            
            total_bytes += size

            tag = (self.tag_template % frameid)
            self.db.setvals(self.monchannels, tag, cmd_time=cmd_time,
                            ack_time=ack_time,
                            seq_num=rpcmsg.seq_num, 
                            payload=rpcmsg.payload)

        # For each frame on the frame list, attempt to transfer the file
        # and record in the monitor what happened.
        total_frames = len(framelist)
        if total_frames == 0:
            self.logger.info("Empty frame list, finishing up")
            return

        # Figure out group size
        group_size = min(self.max_group_size, total_frames)

        group_num = total_frames // group_size
        extra_num = total_frames % group_size
        self.logger.info("%d rounds of %d, extra round of %d" % (group_num, group_size, extra_num))

        rounds = group_num
        if extra_num > 0:
            rounds += 1
        resultlist = []

        # Begin transferring groups
        time_xfer = time.time()

        # For each group, create a concurrent task containing individual tasks
        # to transfer the files
        for k in xrange(group_num):
            self.logger.info("Round %d/%d (group of %d)" % (k+1, rounds, group_num))
            tasklist = []
            resDict = threadSafeBunch()
            index = 0

            for j in xrange(group_size):
                args = [index, resDict]
                args.extend(framelist.pop(0))
                args.append(rpcmsg.sender)

                t = Task.FuncTask(self.save_fits, args, {})
                tasklist.append(t)
                index += 1

            # Create a concurrent task to manage all the parallel transfers
            t = Task.ConcurrentAndTaskset(tasklist)

            # Preinitialize results to errors
            for i in xrange(index):
                resDict[i] = 1
            
            # Start the task and await the results
            result = 1
            self.taskqueue.put(t)
            try:
                # What is a reasonable timeout value?
                result = t.wait(timeout=self.data_timeout)
                self.logger.debug("result is %s" % (str(result)))

                # Check result (although task SHOULD raise an exception
                # if there is a problem with any of the subtasks
                if result in (None, 0):
                    result = 0
                else:
                    result = 1

            except Task.TaskError, e:
                pass

            statuslist = [ resDict[i] for i in xrange(index) ]

            resultlist.extend(statuslist)

        if extra_num > 0:
            tasklist = []
            resDict = threadSafeBunch()
            index = 0

            self.logger.info("Round %d/%d (group of %d)" % (rounds, rounds, extra_num))
            for j in xrange(extra_num):
                args = [index, resDict]
                args.extend(framelist.pop(0))
                args.append(rpcmsg.sender)

                t = Task.FuncTask(self.save_fits, args, {})
                tasklist.append(t)
                index += 1

            # Create a concurrent task to manage all the parallel transfers
            t = Task.ConcurrentAndTaskset(tasklist)

            # Preinitialize results to errors
            for i in xrange(index):
                resDict[i] = 1
            
            # Start the task and await the results
            result = 1
            self.taskqueue.put(t)
            try:
                # What is a reasonable timeout value?
                result = t.wait(timeout=self.data_timeout)
                self.logger.debug("result is %s" % (str(result)))

                # Check result (although task SHOULD raise an exception
                # if there is a problem with any of the subtasks
                if result in (None, 0):
                    result = 0
                else:
                    result = 1

            except Task.TaskError, e:
                pass

            statuslist = [ resDict[i] for i in xrange(index) ]

            resultlist.extend(statuslist)

        time_end = time.time()

        # sanity check on individual results
        if sum(resultlist) != 0:
            result = 1
                
        # Send END message
        rpcbuf.pack_de(rpcmsg.seq_num, result, resultlist,
                       seq_num=self.seq_num.bump())
        try:
            res = self.rpcconn.callrpc(rpcbuf)

        except SOSSrpc.rpcClientError, e:
            msg = "rpc error sending DE reply: %s" % str(e)
            raise INSintError(msg)

        # log any additional info?  statuslist?
        if result != 0:
            raise INSintError("File transfer request failed!")
            
        transfer_time = time_end - time_xfer
        rate = float(total_bytes) / (1024 * 1024) / transfer_time
        self.logger.info("Total transfer time %.3f sec (%.2f MB/s)" % (
                transfer_time, rate))
            
    def check_rename(self, newpath):
        if os.path.exists(newpath):
            renamepath = newpath + time.strftime(".%Y%m%d-%H%M%S",
                                                 time.localtime())
            self.logger.warn("File '%s' exists; renaming to '%s'" % (
                newpath, renamepath))
            os.rename(newpath, renamepath)
            return True
        return False
        
    def save_fits(self, index, resDict, path, size, frameid, sender):

        tag = (self.tag_template % frameid)

        # Calculate new path on our side
        newname = frameid + '.fits'
        newpath = os.path.join(self.raidpath, newname)
            
        # Record start of transfer for this frame
        self.db.setvals(self.monchannels, tag, time_start=time.time(),
                        filepath=newpath, srcpath=path)

        # check for file exists already; if so, rename it and allow the
        # transfer to continue
        self.check_rename(newpath)
            
        # Copy the file
        status = 1
        xferDict = dict(xfer_type='inst->gen2')
        try:
            if path == 'MEMORY-DATA':
                self.save_fits_via_rpc(size, frameid, 25.0, sender, newpath,
                                       result=xferDict)
            else:
                self.save_fits_via_ftp(path, size, frameid, sender, newpath,
                                       result=xferDict)

            # TEMP: FITS files are stored as -r--r-----
            os.chmod(newpath, 0440)

            # Stat the FITS file to get the size.
            try:
                statbuf = os.stat(newpath)

            except OSError, e:
                raise INSintError("Cannot stat file '%s': %s" % (
                    newpath, str(e)))

            if statbuf.st_size != size:
                raise INSintError("File size (%d) does not match request size (%d)" % (statbuf.st_size, size))

            msg = ("Received fits file %s.fits successfully!" % frameid)
            xferDict.update(dict(res_str=msg, res_code=0))
            self.logger.info(msg)
            status = 0

        except Exception, e:
            msg = ("FITS reception error for file %s.fits: %s" % \
                   (frameid, str(e)))
            xferDict.update(dict(res_str=msg, res_code=-1))
            self.logger.error(msg)
            # TODO: what is the proper error return value(s)?
            # All we know is 0=OK, non-zero is error

        # Record transfer in Gen2 db transfer table
        framedb.addTransfer(frameid, **xferDict)

        # Record end of transfer for this frame
        self.db.setvals(self.monchannels, tag, time_done=time.time(),
                        filesize=size, status=status, msg=msg, done=True)

        # Store the result of this transfer into our "slot" in the results
        # dictionary
        resDict[index] = status
        return status


    # This function handles saving a fits file via RPC transfer.
    #
    def save_fits_via_rpc(self, size, frameid, timeout, sender, newpath,
                          result={}):

        def pad(buf, fillch):
            # Size of a FITS header unit
            size_fits_hdu = 2880
            
            padnum = size_fits_hdu - len(buf)
            if padnum == 0:
                return buf

            # If fill char is a space, we can use string interpolation
            # which should be efficient.
##             if fillch == ' ':
##                 return '% -*.*s' % (padnum, padnum, buf)

            # Fill char is not a space.
            # TODO: figure out a more efficient way to do this
            # (For some reason you cannot use [buf].extend(...)   why?)
            l = [buf]
            l.extend([fillch for i in xrange(padnum)])
            return ''.join(l)

        self.logger.info("Request to transfer FITS data via RPC")
        result.update(dict(time_start=datetime.datetime.now(),
                           src_host=sender, src_path='RPCDATA',
                           dst_host=self.myhost, dst_path=newpath,
                           xfer_method='rpc'))

        done = False
        while not done:
            done = True
            try:
                # rpcmsg has format of DAQtkDatSndMemtypes.DAQtkRpcFits
                # TODO: what is the correct timeout value here (if any?)
                rpcmsg = self.fitsrecv.rpcqueue.get(block=True,
                                                    timeout=timeout)
                cframe = rpcmsg.cframe[0:12].strip().upper()
                self.logger.info("Received FITS RPC packet (cframe=%s)" % rpcmsg.cframe)
                #self.logger.info("Received FITS RPC packet")

                if cframe == 'END':
                    done = True
                    continue
                    
                if cframe != frameid:
                    self.logger.warn("cframe (%s) does not match expected frameid (%s)" % \
                                         (cframe, frameid))
                
                # Open a file and write the FITS content.
                try:
                    out_f = open(newpath, 'w')

                    out_f.write(rpcmsg.ph)
                    out_f.write(rpcmsg.pd)
#                     out_f.write(pad(rpcmsg.ph, ' '))
#                     out_f.write(pad(rpcmsg.pd, '\0'))
#                     out_f.write(pad(rpcmsg.ah1, ' '))
#                     out_f.write(pad(rpcmsg.ad1, '\0'))
#                     out_f.write(pad(rpcmsg.ah2, ' '))
#                     out_f.write(pad(rpcmsg.ad2, '\0'))
#                     out_f.write(pad(rpcmsg.ah3, ' '))
#                     out_f.write(pad(rpcmsg.ad3, '\0'))

                    out_f.flush()
                    out_f.close()
                    
                    result.update(dict(time_done=datetime.datetime.now(),
                                       res_code=0))

                except IOError, e:
                    errmsg = "Can't open file for writing: %s" % (str(e))
                    result.update(dict(time_done=datetime.datetime.now(),
                                       res_str=errmsg))
                    raise INSintError(errmsg)
                    

            except Queue.Empty, e:
                errmsg = "Timed out waiting for fits file rpc msg!"
                result.update(dict(time_done=datetime.datetime.now(),
                                   res_str=errmsg))
                raise INSintError(errmsg)
            

    # This function handles saving a fits file via FTP or SCP transfer.
    #
    def save_fits_via_ftp(self, path, size, frameid, ftphost, newpath,
                          result={}):

        self.transfer_file(path, ftphost, newpath,
                           transfermethod=self.transfermethod,
                           username=self.username, result=result)

    def transfer_file(self, filepath, host, newpath,
                      transfermethod='ftp', username=None,
                      password=None, port=None, result={}):

        """Modified subset of the version found in datasink.
        """
        self.logger.info("transfer file (%s): %s <-- %s" % (
            transfermethod, newpath, filepath))
        (directory, filename) = os.path.split(filepath)

        result.update(dict(time_start=datetime.datetime.now(),
                           src_host=host, src_path=filepath,
                           dst_host=self.myhost, dst_path=newpath,
                           xfer_method=transfermethod))
        
        if not username:
            try:
                username = os.environ['LOGNAME']
            except KeyError:
                username = 'anonymous'
            
        if transfermethod == 'scp':
            # passwordless scp is assumed to be setup
            cmd = ("scp %s@%s:%s %s" % (username, host, filepath, newpath))

        ## elif transfermethod == 'ftp':
        ##     cmd = ("wget --tries=5 --waitretry=1 -O %s -a FTP.log --user=%s ftp://%s/%s" % (
        ##         newpath, username, host, filepath))
            
        else:
            # <== Set up to do an lftp transfer (ftp/sftp/ftps/http/https)

            if password:
                login = '"%s","%s"' % (username, password)
            else:
                # password to be looked up in .netrc
                login = '"%s"' % (username)

            setup = "set xfer:log yes; set net:max-retries 1; set net:reconnect-interval-max 2; set net:reconnect-interval-base 2; set xfer:disk-full-fatal true;"

            # Special args for specific protocols
            if transfermethod == 'ftp':
                setup = "%s set ftp:use-feat no; set ftp:use-mdtm no;" % (setup)

            elif transfermethod == 'ftps':
                setup = "%s set ftp:use-feat no; set ftp:use-mdtm no; set ftp:ssl-force yes;" % (
                    setup)

            elif transfermethod == 'sftp':
                setup = "%s set ftp:use-feat no; set ftp:use-mdtm no; set ftp:ssl-force yes;" % (
                    setup)
                
            else:
                raise INSintError("Request to transfer file '%s': don't understand '%s' as a transfermethod" % (
                    filename, transfermethod))

            if port:
                cmd = ("""lftp -e '%s get %s -o %s; exit' -u %s %s://%s:%d""" % (
                    setup, filepath, newpath, login, transfermethod, host, port))
            else:
                cmd = ("""lftp -e '%s get %s -o %s; exit' -u %s %s://%s""" % (
                    setup, filepath, newpath, login, transfermethod, host))


        try:
            result.update(dict(xfer_cmd=cmd))

            self.logger.debug(cmd)
            res = os.system(cmd)

            result.update(dict(time_done=datetime.datetime.now(),
                               xfer_code=res))

        except Exception, e:
            self.logger.error("Command was: %s" % (cmd))
            errmsg = "Failed to transfer fits file '%s': %s" % (
                filename, str(e))
            result.update(dict(time_done=datetime.datetime.now(),
                               res_str=errmsg, xfer_code=-1))
            raise INSintError(errmsg)

        if res != 0:
            self.logger.error("Command was: %s" % (cmd))
            errmsg = "Failed to transfer fits file '%s': exit err=%d" % (
                filename, res)
            result.update(dict(res_str=errmsg))
            raise INSintError(errmsg)


    def start(self, usethread=True, wait=True, timeout=None):
        # If we have a special FITS receiver RPC server (IRCS only...Grrrr!)
        # then start it up
        if self.fitsrecv:
            self.logger.info("Starting RPC FITS receiver service")
            #self.fitsrecv.start(usethread=True, wait=wait, timeout=timeout)
            t = Task.FuncTask(self.fitsrecv.start, [],
                              {'usethread': False})
            self.taskqueue.put(t)
            if wait:
                self.fitsrecv.wait_start(timeout=timeout)

        # Our other RPC server normal startup
        super(ArchiveRequest, self).start(usethread=usethread, wait=wait,
                                       timeout=timeout)
        

class ocsInsInt(object):
    """Instrument Interface Container Class.  An object of this class 
       instantiates objects of the various interface classes above
       as members.  It also provides a start method to start all threads
       and RPC servers, and a stop method to terminate everything."""

    def __init__(self, obcpnum, obcphost, raidpath, statusObj,
                 interfaces=('cmd', 'thru', 'sreq', 'sdst', 'file'),
                 #interfaces=('cmd', 'sreq', 'sdst', 'file'),
                 hostfilterDict=None, monunitnum=3, myhost=None,
                 transfermethod='scp', username=None, 
                 logger=None, ev_quit=None, db=None, seq_num=None,
                 threadPool=None, numthreads=None):

        for name in interfaces:
            if not name in ('cmd', 'thru', 'file', 'sdst', 'sreq'):
                raise INSintError("Interfaces must be any combination of: cmd, thru, sdst, sreq, file--'%s'" % interfaces)

        self.myhost = myhost
        
        if logger:
            self.logger = logger
        else:
            self.logger = ssdlog.NullLogger('ocsInsInt')

        if not ev_quit:
            self.ev_quit = threading.Event()
        else:
            self.ev_quit = ev_quit

        svcname = '%s%d' % (serviceName_pfx, obcpnum)
        self.monchannels = [svcname]
        
        if numthreads:
            self.numthreads = numthreads
        else:
            # Estimate number of threads needed to handle traffic
            # 1 for each possible RPC server + worker threads
            self.numthreads = 20 + (len(interfaces) * 6)
            
        # Thread pool for autonomous tasks
        # If we were passed in a thread pool, then use it.  If not,
        # make one.  Record whether we made our own or not.  This
        # threadPool is shared by all interfaces.
        if threadPool != None:
            self.threadPool = threadPool
            self.mythreadpool = False

        else:
            self.threadPool = Task.ThreadPool(logger=self.logger,
                                              ev_quit=self.ev_quit,
                                              numthreads=self.numthreads)
            self.mythreadpool = True

        # Make/load the local monitor
        if db:
            self.db = db
            self.mymonitor = False
        else:
            self.db = Monitor.Monitor('%s.mon' % svcname, self.logger,
                                      threadPool=self.threadPool)
            self.mymonitor = True

        if seq_num:
            self.seq_num = seq_num
        else:
            # Share a sequence number between interfaces, or let each
            # interface generate it's own sequence numbers
            #self.seq_num = SOSSrpc.rpcSequenceNumber()
            self.seq_num = None
        
        # Master queue for distributing work to threadpool
        self.taskqueue = Queue.Queue()
        self.timeout = 0.1
        self.qtask = None
        
        # For task inheritance:
        self.tag = 'INSint'
        self.shares = ['logger', 'ev_quit', 'timeout', 'threadPool']

        # Get list of channels to communicate with instrument host.
        self.iface_names = interfaces
        self.monunitnum = monunitnum

        # Build up desired set of interfaces.
        self.iface = Bunch()
        
        for name in self.iface_names:
            # Make a logger to use
            if not logger:
                queue = Queue.Queue()
                log = ssdlog.mklog(name, queue, logging.DEBUG)
            else:
                log = logger
                queue = None
                
            if name == 'cmd':
                #log = gui_log(Queue.Queue(),None)
                iface = DDCommandChannel(obcpnum, obcphost, ev_quit, log,
                                         self.db, self.taskqueue,
                                         seq_num=self.seq_num,
                                         myhost=self.myhost,
                                         monchannels=self.monchannels)
                self.iface[name] = Bunch(log=log, logqueue=queue, iface=iface)
                continue
            
            if name == 'thru':
                #log = gui_log(Queue.Queue(),None)
                iface = ThroughCommand(ev_quit, log, self.db, self.taskqueue,
                                       myhost=self.myhost,
                                       seq_num=self.seq_num)
                self.iface[name] = Bunch(log=log, logqueue=queue, iface=iface)
                continue
            
            if name == 'sreq':
                #log = gui_log(Queue.Queue(),None)
                iface = StatusRequest(ev_quit, log, self.db, self.taskqueue,
                                      statusObj, seq_num=self.seq_num,
                                      myhost=self.myhost,
                                      hostfilterDict=hostfilterDict)
                self.iface[name] = Bunch(log=log, logqueue=queue, iface=iface)
                continue
            
            if name == 'sdst':
                #log = gui_log(Queue.Queue(),None)
                iface = StatusReceiver(self.monunitnum, ev_quit, log, self.db,
                                       self.taskqueue,
                                       myhost=self.myhost,
                                       seq_num=self.seq_num)
                self.iface[name] = Bunch(log=log, logqueue=queue, iface=iface)
                continue

            if name == 'file':
                #log = gui_log(Queue.Queue(),None)
                iface = ArchiveRequest(obcpnum, raidpath, ev_quit, log, self.db,
                                       self.taskqueue, seq_num=self.seq_num,
                                       myhost=self.myhost,
                                       fitsport=8991,
                                       hostfilterDict=hostfilterDict,
                                       username=username, 
                                       transfermethod=transfermethod,
                                       monchannels=['frames'])
                self.iface[name] = Bunch(log=log, logqueue=queue, iface=iface)
                continue

            raise INSintError("Unknown interface type: '%s'" % name)
        
        
    def get_threadPool(self):
        return self.threadPool
    
    def get_monitor(self):
        return self.db

    
    def start_ifaces(self, ifaces=None, wait=True):
        """Start instrument interfaces.
        """
        if not ifaces:
            ifaces = self.iface_names

        for name in ifaces:
            self.iface[name].iface.start(usethread=True, wait=wait)


    def start(self, ifaces=None, wait=True):
        """Start instrument interfaces.
        """

        self.ev_quit.clear()

        # Start our thread pool (if we created it)
        if self.mythreadpool:
            self.threadPool.startall(wait=True)

        # Start our monitor (if we created it)
        if self.mymonitor:
            self.db.start(wait=True)
        
        # Initialize the task queue processing task.
        t = Task.QueueTaskset(self.taskqueue, waitflag=False)
        self.qtask = t
        t.init_and_start(self)
        
        self.start_ifaces(ifaces, wait=wait)


    def stop_ifaces(self, ifaces=None, wait=True):
        """Stop instrument interfaces.
        """
        if not ifaces:
            ifaces = self.iface_names

        for name in ifaces:
            self.iface[name].iface.stop(wait=wait)

       
    def stop(self, ifaces=None, wait=True):
        """Stop instrument interfaces.
        """
        # Stop our monitor (if we created it)
        if self.mymonitor:
            #self.db.releaseAll()        # Release all waiters
            self.db.stop(wait=True)
        
        self.stop_ifaces(ifaces, wait=wait)

        if self.qtask:
            self.qtask.stop()
        
        # Stop our thread pool (if we created it)
        if self.mythreadpool:
            self.threadPool.stopall(wait=wait)

        self.logger.info("INSTRUMENT INTERFACE STOPPED.")
        self.ev_quit.set()

       
    def send_cmd(self, tag, cmd_str):
        """Send a string command to the instrument.  _tag_ is a task manager
        generated id for keeping track of this command.
        """

        self.logger.debug("tag=%s cmd='%s'" % (tag, cmd_str))
        try:
            if not self.iface.has_key('cmd'):
                raise INSintError("No command interface available")

            if self.db.has_val(tag, 'time_start'):
                raise INSintError("A command already exists with this tag")

            # Remove any trailing ';'
            if ';' in cmd_str:
                cmd_str = cmd_str.split(';')[0]

            # Remove any extraneous whitespace
            cmd_str = cmd_str.strip()
            
            self.db.setvals(self.monchannels, tag, time_start=time.time(),
                            cmd_str=cmd_str)

            # Add send_cmd job to work queue
            self.iface['cmd'].iface.send_cmd(tag)
            
        except INSintError, e:
            msg = "Error invoking send_cmd: %s" % str(e)
            self.logger.error(msg)

            # Signal to any waiters on this command that we are done
            self.db.setvals(self.monchannels, tag, msg=msg, time_done=time.time(),
                            done=True)



# Encapsulate our remote object interface as a simple class
# 
class roINS(ro.remoteObjectServer):

    def __init__(self, svcname, ins, logger, port=None, usethread=False,
                 threadPool=None):

        self.ins = ins
        self.ev_quit = threading.Event()
        self.logger = logger

        # Superclass constructor
        ro.remoteObjectServer.__init__(self, svcname=svcname,
                                       port=port,
                                       ev_quit=self.ev_quit,
                                       logger=self.logger,
                                       usethread=usethread,
                                       threadPool=threadPool)



    ######################################
    # Methods provided by remote object interface
    ######################################

    def send_cmd(self, tag, cmd_str):
        """Send a command string to an instrument.
        """
        try:
            self.ins.send_cmd(tag, cmd_str)
            return ro.OK

        except Exception, e:
            self.logger.error("Exception raised: %s" % str(e))
            return ro.ERROR

    def send_native_cmd(self, tag, cmd_str):
        """Used by SIMCAM TSC simulator (TSCCAM)"""
        return self.send_cmd(tag, 'EXEC TSC NATIVE CMD="%s"' % cmd_str)

    def set_group_size(self, n):
        self.ins.iface['file'].iface.max_group_size = n
        return ro.OK


def main(options, args):

    channel_cmds = '%s%d' % (serviceName_pfx, options.obcpnum)
    channel_file = 'frames'

    # If we are handed a service name, use it.  Otherwise construct a
    # default one.
    if options.svcname:
        svcname = options.svcname
    else:
        svcname = channel_cmds

    # Create top level logger.
    logger = ssdlog.make_logger(svcname, options)

    cfg = {}
    if options.inscfg:
        try:
            insconfig = INSdata(info=options.inscfg)
            cfg = insconfig.getOBCPInfoByNumber(options.obcpnum)
            
        except IOError, e:
            logger.error("Error opening instrument configuration '%s': %s" % (
                    options.inscfg, str(e)))
            sys.exit(1)

   
    # Initialize remote objects subsystem.
    try:
        ro.init()

    except ro.remoteObjectError, e:
        logger.error("Error initializing remote objects subsystem: %s" % str(e))
        sys.exit(1)

    # Get hostname of OBCP host.  If None, assume we are running on
    # local host.
    obcphost = options.obcphost
    if not obcphost:
        obcphost = SOSSrpc.get_myhost(short=True)
        obcphost = cfg.get('obcphost', obcphost)

    # Get file transfer method
    transfermethod = options.transfermethod
    if not transfermethod:
        transfermethod = cfg.get('transfermethod', 'scp')

    # Get username for FTP/SCP transfers
    username = options.username
    if not username:
        username = cfg.get('username', os.environ['LOGNAME'])

    interfaces = options.interfaces.split(',')

    # Did user specify a list of hosts allowed to request status?
    if options.hostfilter:
        hostfilterDict = {}
        for host in options.hostfilter.split(','):
            hostfilterDict[host] = True
    else:
        hostfilterDict = None
        
    if options.statussvc:
        ro_status = ro.remoteObjectProxy(options.statussvc)
        statusObj = FetchStatusWrapper_Gen2(ro_status)
        
    elif options.statushost:
        from SOSS.status import cachedStatusObj

        statusDict = cachedStatusObj(options.statushost)
        statusObj = FetchStatusWrapper_SOSS(statusDict)
        
    else:
        statusDict = {}
        statusObj = FetchStatusWrapper_SOSS(statusDict)

    # Create instrument interface and start it
    try:
        ins = ocsInsInt(options.obcpnum, obcphost,
                        options.fitsdir, statusObj,
                        interfaces=interfaces,
                        hostfilterDict=hostfilterDict,
                        transfermethod=transfermethod,
                        username=username,
                        myhost=options.myhost,
                        ev_quit=None, logger=logger,
                        monunitnum=options.monunitnum,
                        db=None, numthreads=options.numthreads)

        logger.info("Instrument interface coming up.")
        ins.start(wait=True)

    except INSintError, e:
        logger.error("Couldn't create/start instrument interface: %s" % str(e))
        sys.exit(1)

    # Start remote objects interface
    svc = None
    try:
        minimon = ins.get_monitor()
        threadPool = ins.get_threadPool()

        # Publish our results to the specified monitor
        if options.monitor:
            minimon.publish_to(options.monitor, [channel_cmds, channel_file],
                              {})
            
        # Configure logger for logging via our monitor
        if options.logmon:
            minimon.logmon(logger, options.logmon, ['logs'])

        try:
            # Create our remote service object
            svc = roINS(svcname, ins, logger, port=options.port, usethread=False,
                        threadPool=threadPool)
            svc.ro_start(wait=True)

        except KeyboardInterrupt:
            logger.error("Caught keyboard interrupt!")

        except Exception, e:
            logger.error("Uncaught exception: %s" % str(e))
            # TODO: log complete stack dump

    finally:
        logger.info("Instrument interface shutting down.")
        ins.stop(wait=True)
        # Only if usethread=True
        # if svc:
        #     svc.ro_stop(wait=True)


if __name__ == '__main__':

    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("-C", "--clear", dest="clear", default=False,
                      action="store_true",
                      help="Clear the rpc transaction database on startup")
    optprs.add_option("--db", dest="dbpath", metavar="FILE",
                      help="Use FILE as the rpc transaction database")
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-d", "--fitsdir", dest="fitsdir", metavar="DIR",
                      default=".",
                      help="Use DIR for storing instrument FITS files")
    optprs.add_option("--fitsport", dest="fitsport", type="int", default=None,
                      help="Register using PORT for FITS rpc transfer", metavar="PORT")
    optprs.add_option("--hostfilter", dest="hostfilter", metavar="HOSTS",
                      help="Specify a list of HOSTS that can request status")
    optprs.add_option("-i", "--interfaces", dest="interfaces",
                      default="cmd,file,sreq,sdst",
                      help="List of interfaces to activate")
    optprs.add_option("--inscfg", dest="inscfg", metavar="FILE",
                      help="Read instrument configuration data from FILE")
    optprs.add_option("-m", "--monitor", dest="monitor", default=False,
                      metavar="NAME",
                      help="Reflect internal status to monitor service NAME")
    optprs.add_option("--monunit", dest="monunitnum", type="int",
                      default=3, metavar="NUM",
                      help="Target OSSL_MonitorUnit NUM on OBS")
    optprs.add_option("--myhost", dest="myhost", metavar="NAME",
                      help="Use NAME as my hostname for communication")
    optprs.add_option("--numthreads", dest="numthreads", type="int",
                      default=50,
                      help="Use NUM threads in thread pool", metavar="NUM")
    optprs.add_option("--obcphost", dest="obcphost", 
                      help="Use HOST as the OBCP host", metavar="HOST")
    optprs.add_option("-n", "--obcpnum", dest="obcpnum", type="int",
                      default=9,
                      help="Use NUM as the OBCP number", metavar="NUM")
    optprs.add_option("--port", dest="port", type="int", default=None,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--statushost", dest="statushost",
                      help="Use HOST for obtaining SOSS status", metavar="HOST")
    optprs.add_option("--statussvc", dest="statussvc",
                      help="Use SVCNAME for obtaining Gen2 status",
                      metavar="SVCNAME")
    optprs.add_option("-t", "--transfermethod", dest="transfermethod",
                      help="Use METHOD (ftp|rpc|scp) for transferring FITS files (OBCP must support method)")
    optprs.add_option("--svcname", dest="svcname", metavar="NAME",
                      help="Register using NAME as service name")
    optprs.add_option("-u", "--username", dest="username", metavar="USERNAME",
                      help="Login as USERNAME@obcp for ftp/scp transfers")
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
       
# END INSint.py

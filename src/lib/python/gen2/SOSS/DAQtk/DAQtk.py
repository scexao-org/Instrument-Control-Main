#!/usr/bin/env python
#
# DAQtk.py -- Interact with SOSS as a Subaru Observatory instrument.
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Apr 22 13:32:36 HST 2011
#]
#
#
import sys, re, os, time
import threading, Queue

from Bunch import Bunch
import Task
import SOSS.SOSSrpc as SOSSrpc
from SOSS.INSint import BaseInterface
from SOSS.parse.CommandParser import CommandParser
import logging, ssdlog
from SOSS import status
import remoteObjects.Monitor as Monitor

# Service name prefix for directory of remote objects
serviceName_pfx = 'OCSint'


class OCSintError(Exception):
    pass


# HELPER CLASSES/FUNCTIONS

class DAQtkInterface(BaseInterface):
    """Methods shared by any interface initiating a connection to the OCS.
    """

    def _get_key(self, seq_num):
        return self.key_template % seq_num
    
    def put_trans(self, seq_num, tag):
        key = self._get_key(seq_num)

        # Is there a cmdb bundle for this seq_num?
        if self.db.has_key(key):
            raise OCSintError("Tag exists matching sequence number %d" % \
                              (seq_num))

        else:
            self.db[key] = tag

    def get_trans(self, seq_num):
        key = self._get_key(seq_num)

        # Is there a bundle for this seq_num?
        if self.db.has_key(key):
            return self.db[key]

        else:
            raise OCSintError("No tag matching sequence number %d" % \
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

    # This is called when we have an error anywhere in the process of
    # sending a through command to the OCS.
    #
    def cmd_error(self, e, seq_num, tag):
        # Log the exception that led to us being called
        errmsg = str(e)
        self.logger.error(errmsg)

        # Signal to any waiters on this command that we are done
        if tag:
            self.db.setvals(self.monchannels, tag, msg=errmsg,
                            time_done=time.time(), result=-1,
                            done=True)

            # Delete our reference to the cmdb so as not to leak memory
            self.del_trans(seq_num, tag)

    def submit_request(self, tag):
        self.logger.debug("Adding task to task queue for tag '%s'" % tag)
        self.taskqueue.put(self.sendTasker(tag))
        


class CommandReceiverInterface(BaseInterface):
    """Instrument Command Receiver class. An object of this class receives 
       command messages (CD) from OCS.  It contains an RPC server 
       to receive CD messages."""

    def __init__(self, obcpnum, ev_quit, logger, db, taskqueue,
                 monchannels=[], myhost=None, myport=None, seq_num=None):

        # Initialize common attributes
        super(CommandReceiverInterface, self).__init__(ev_quit, logger, db,
                                                       taskqueue,
                                                       myhost=myhost, myport=myport,
                                                       seq_num=seq_num)

        self.recvTasker = Task.make_tasker(self.cmd_recv)
        self.has_instrument = threading.Event()
        self.instrument = None
        self.monchannels = monchannels

        # Look up 
        try:
            rpckey = ('OBStoOBCP%d(cmd)' % obcpnum)

            self.rpcconn = SOSSrpc.clientServerPair(rpckey, initiator=False,
                                                    logger=self.logger,
                                                    ev_quit=self.ev_quit,
                                                    #myhost=self.myhost,
                                                    recvqueue=self.taskqueue,
                                                    func=self.recvTasker)

        except SOSSrpc.rpcError, e:
            raise OCSintError("Error creating rpc client-server pair: %s" % \
                              str(e))


    def cmd_recv(self, rpcmsg):

        if rpcmsg.msg_type != 'CD':
            raise OCSintError("rpc msg is not a SOSS CD request")

        # check for validity of command 
        status = 0

        try:
            data = rpcmsg.unpack_cd()
            cmd = data.cmdstr

        except SOSSrpc.rpcMsgError, e:
            raise OCSintError("SOSS RPC payload format error: %s" % str(e))
            
        self.logger.info("DD command received: '%s'" % cmd)
        if cmd == '':
            self.logger.error("null command received")
            status = 1

        tag = Task.get_tag(None)

        # Inform monitor of command received
        self.db.setvals(self.monchannels, tag, cmd_time=time.time(),
                        cmd_str=cmd, seq_num=rpcmsg.seq_num)
        
        # Create buffer for RPC message
        rpcbuf = SOSSrpc.SOSScmdRpcMsg(sender=self.myhost, pkt_type='CT')

        # Send AB message
        rpcbuf.pack_ab(rpcmsg.seq_num, status, receiver=rpcmsg.sender,
                       seq_num=self.seq_num.bump())

        self.db.setvals(self.monchannels, tag, ack_time=time.time(),
                        ack_result=status)
        
        try:
            res = self.rpcconn.callrpc(rpcbuf)

        except SOSSrpc.rpcClientError, e:
            raise OCSintError("rpc error sending AB response: %s" % str(e))

        # Invoke the command to the instrument and get the result
        if not self.has_instrument.isSet():
            status = 1
            self.logger.error("No instrument delegate set!")
        else:
            try:
                # Call into the delegate instrument object
                status = self.instrument.executeCmd(cmd)

            except Exception, e:
                status = (1, str(e))

        # Possible result codes:
        # 0,COMPLETE
        # N,CONTEXT_SPECIFIC_ERROR_MESSAGE

        # Possible returns are (status, result) or just status.
        # If just status code, then figure out a generic result msg
        if (type(status) == type((0,""))) and (len(status) == 2):
            (status, result) = status
            if (type(status) != int) or (type(result) != str):
                status = 1
                result = "ERROR: BAD RETURN TYPE TO DAQtk"

        elif type(status) == int:
            if status == 0:
                result = 'COMPLETE'
            else:
                result = 'ERROR'

        else:
            status = 1
            result = "ERROR: BAD RETURN TYPE TO DAQtk"
        
        # Send EN message
        rpcbuf.pack_en(rpcmsg.seq_num, status, result,
                       seq_num=self.seq_num.bump())

        self.db.setvals(self.monchannels, tag, end_time=time.time(),
                        end_result=status, msg=result)
        
        try:
            res = self.rpcconn.callrpc(rpcbuf)

        except SOSSrpc.rpcClientError, e:
            raise OCSintError("rpc error sending EN response: %s" % str(e))

        self.logger.debug("Completed command request.")
        self.db.setvals(self.monchannels, tag,
                        time_done=time.time(), result=status,
                        done=True)


    def initialize(self, ins):
        self.instrument = ins
        self.has_instrument.set()


class ThroughCommandInterface(DAQtkInterface):
    """Instrument Through Command Interface Class.  An object of this class
       sends commands for OCS execution using RPC transactions with the
       OCS.  It contains an RPC client to send commands to the OCS,
       and an RPC server to receive corresponding Ack (AB) and Completion (EN)
       messages from the OCS."""

    def __init__(self, obcpnum, thruhost, ev_quit, logger, db, taskqueue,
                 monchannels=[], myhost=None, myport=None, seq_num=None):

        # Initialize common attributes
        super(ThroughCommandInterface, self).__init__(ev_quit, logger, db,
                                                      taskqueue,
                                                      myhost=myhost, myport=myport,
                                                      seq_num=seq_num)

        self.obcpnum = obcpnum
        self.thruhost = thruhost
        self.monchannels = monchannels
        self.key_template = 'thru.%d'
        self.sendTasker = Task.make_tasker(self.thru_cmd)
        self.recvTasker = Task.make_tasker(self.thru_recv)

        # Look up 
        try:
            key = ('OBCPtoOBS(thru)')

            self.rpcconn = SOSSrpc.clientServerPair(key, initiator=True,
                                                    logger=self.logger,
                                                    ev_quit=self.ev_quit,
                                                    #myhost=self.myhost,
                                                    recvqueue=self.taskqueue,
                                                    func=self.recvTasker)

        except SOSSrpc.rpcError, e:
            raise OCSintError("Error creating rpc client-server pair: %s" % \
                              str(e))

##         key = 'thru.%d.seq_num' % (self.obcpnum)
##         if self.db.has_key(key):
##             self.seq_num.reset(self.db[key])


    def thru_cmd(self, tag):
        """Look up the command information registered under _tag_,
        and send the string command to the OCS.
        """

        seq_num = -1
        try:
            if not self.db.has_key(tag):
                raise OCSintError("No command data found for tag '%s'" % tag)

            cmdb = self.db.get_node(tag)

            # Create buffer for RPC message
            rpcbuf = SOSSrpc.SOSScmdRpcMsg(sender=self.myhost,
                                           receiver=self.thruhost,
                                           pkt_type='CT')

            # Get new sequence number for this transaction
            seq_num = self.seq_num.bump()

            # Send initial message as client
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
                raise OCSintError("rpc error sending CD command: %s" % str(e))

        except OCSintError, e:
            self.cmd_error(e, cmdb)

        except Exception, e:
            self.cmd_error(e, cmdb)
            raise e


    def validate_ack(self, tag, result):

        cmdb = self.db.get_node(tag)
        
        # Is there an AB record for this seq_num?
        if cmdb.has_key('ack_time'):
            raise OCSintError("Error ack reply: duplicate ack record matching sequence number (%d)" % \
                                (cmdb.seq_num))

        # Record AB record for this seq_num
        self.db.setvals(self.monchannels, tag, ack_time=time.time(),
                        ack_result=result)

        # Is there a command record for this seq_num?  Should be.
        if not cmdb.has_key('cmd_time'):
            raise OCSintError("Error in ack reply: no command record matching sequence number (%d)" % \
                                (cmdb.seq_num))

        # Is there an CE record for this seq_num?  Should not be.
        if cmdb.has_key('end_time'):
            errmsg = "ack reply: end record exists matching sequence number (%d)" % (cmdb.seq_num)
            #raise OCSintError(errmsg)
            # depending on network delays CE could arrive before AB...
            self.logger.warn(errmsg)
        
        # Error in AB result code?
        if result != 0:
            raise OCSintError("Error ack reply: result=%d" % result)


    def validate_end(self, cmdb, result, payload):

        cmdb = self.db.get_node(tag)
        
        # Is there an CE record for this seq_num?
        if cmdb.has_key('end_time'):
            raise OCSintError("Error end reply: duplicate end record matching sequence number (%d)" % \
                                (cmdb.seq_num))

        # Record CE record for this seq_num
        self.db.setvals(self.monchannels, tag, end_time=time.time(),
                        end_result=result, end_payload=payload)

        # Is there a command record for this seq_num?  Should be.
        if not cmdb.has_key('cmd_time'):
            raise OCSintError("Error in ack reply: no command record matching sequence number (%d)" % \
                                (cmdb.seq_num))

        # Is there an AB record for this seq_num? Should be.
        if not cmdb.has_key('ack_time'):
            errmsg = "end reply: no ack record matching sequence number (%d)" %  (cmdb.seq_num)
            #raise OCSintError(errmsg)
            # depending on network delays CE could arrive before AB...
            self.logger.warn(errmsg)

        if result != 0:
            raise OCSintError("Error end reply: result=%d, payload=%s" % \
                                (result, payload))
        
        # Success!
        

    def thru_recv(self, rpcmsg):
        tag = None
        seq_num = -1
        try:
            # Call handler for appropriate rpc msg type
            if rpcmsg.msg_type == 'AB':
                try:
                    data = rpcmsg.unpack_ab()

                except SOSSrpc.rpcMsgError, e:
                    raise OCSintError("SOSS RPC payload format error: %s" % str(e))

                # Look up the transaction matching this seq_num
                seq_num = data.seq_num
                tag = self.get_trans(seq_num)

                self.validate_ack(tag, data.result)

            elif rpcmsg.msg_type == 'EN':
                try:
                    data = rpcmsg.unpack_en()

                except SOSSrpc.rpcMsgError, e:
                    raise OCSintError("SOSS RPC payload format error: %s" % str(e))

                # Look up the transaction matching this seq_num
                seq_num = data.seq_num
                tag = self.get_trans(seq_num)

                self.validate_end(tag, data.result, data.payload)

                # End command validated--notify waiters
                self.db.setvals(self.monchannels, tag,
                                msg='through command processed successfully by OCS',
                                time_done=time.time(), result=0,
                                done=True)

            else:
                raise OCSintError("Different reply than AB or EN!")

            # Delete our reference to the transaction so as not to leak memory
            if tag:
                self.del_trans(seq_num, tag)

        except OCSintError, e:
            self.cmd_error(e, seq_num, tag)

        except Exception, e:
            self.cmd_error(e, seq_num, tag)
            raise e


class StatusRequestInterface(DAQtkInterface):
    """Instrument Status Request Interface Class.  An object of this class
       sends requests for OCS status values using RPC transactions with the
       OCS.  It contains an RPC client to send request commands to the OCS,
       and an RPC server to receive corresponding Ack (AB) and Completion (EN)
       messages from the OCS."""

    def __init__(self, obcpnum, stathost, ev_quit, logger, db, taskqueue,
                 monchannels=[], myhost=None, myport=None, seq_num=None):

        # Initialize common attributes
        super(StatusRequestInterface, self).__init__(ev_quit, logger, db,
                                                     taskqueue,
                                                     myhost=myhost, myport=myport,
                                                     seq_num=seq_num)

        self.obcpnum = obcpnum
        self.stathost = stathost
        self.monchannels = monchannels
        self.key_template = 'sreq.%d'
        # holds all kinds of data about SOSS status aliases 
        self.status = status.statusInfo()
        self.sendTasker = Task.make_tasker(self.sreq_cmd)
        self.recvTasker = Task.make_tasker(self.sreq_recv)

        # Look up 
        try:
            key = ('OBCPtoOBS(sreq)')

            self.rpcconn = SOSSrpc.clientServerPair(key, initiator=True,
                                                    logger=self.logger,
                                                    ev_quit=self.ev_quit,
                                                    #myhost=self.myhost,
                                                    recvqueue=self.taskqueue,
                                                    func=self.recvTasker)

        except SOSSrpc.rpcError, e:
            raise OCSintError("Error creating rpc client-server pair: %s" % \
                              str(e))


    def sreq_cmd(self, tag):

        seq_num = -1
        try:
            # Raises an exception if tag not found?
            if not self.db.has_key(tag):
                raise OCSintError("No status request data found for tag '%s'" % tag)

            cmdb = self.db.get_node(tag)

            statusDict = cmdb.statusDict
            keylist = statusDict.keys()
            # Record order that we requested aliases
            cmdb.keylist = keylist

            # Create status request command from all desired status aliases
            statuskeys = [('$%s' % key) for key in keylist]
            cmd = ('STATUS,%s' % (' '.join(statuskeys)))

            # Create buffer for RPC message
            rpcbuf = SOSSrpc.SOSScmdRpcMsg(sender=self.myhost,
                                           receiver=self.stathost,
                                           pkt_type='CT')

            # Get new sequence number for this transaction
            seq_num = self.seq_num.bump()

            # Send initial message as client
            rpcbuf.pack_cd(cmd, seq_num=seq_num)

            # Inform monitor of impending event
            self.db.setvals(self.monchannels, tag, seq_num=seq_num,
                            cmd_time=time.time())
            # Associate this tag with this seq_num
            self.put_trans(seq_num, tag)

            # Make the rpc client call
            try:
                res = self.rpcconn.callrpc(rpcbuf)

            except SOSSrpc.rpcClientError, e:
                raise OCSintError("rpc error sending CD command: %s" % str(e))

        except OCSintError, e:
            self.cmd_error(e, seq_num, tag)

        except Exception, e:
            self.cmd_error(e, seq_num, tag)
            raise e


    def convert(self, aliasName, valueStr):
        """Given a alias value and the corresponding alias, return the
        value converted to a convenient Python data type.
        """

        # Try to convert it according to the correct type
        try:
            aliasdef = self.status.get_aliasDef(aliasName)

        except status.statusError, e:
            raise OCSintError("Error getting alias def for '%s': %s" % (
	                         aliasName, str(e)))

        # Do we have an override of the type from our StatusAlias
        # supplementary data?
        try:
            stype = aliasdef.supp_data['type']

        except KeyError, e:
            stype = aliasdef.stype

        # Apply the necessary conversion.
        try:
            if stype in ('C', 'R'):
                return valueStr
            
            if stype in ('D', 'F', 'L', 'S'):
                return float(valueStr)
            
            if stype in ('B', 'I'):
                return int(valueStr)

            raise OCSintError("Don't know how to convert %s (%s)" % \
                              (aliasName, valueStr))

        except ValueError, e:
            #raise OCSintError(str(e))
            # If there is an error, just silently default to NOT converting
            # from a string...
            return valueStr
        
    
    def validate_ack(self, tag, result):

        cmdb = self.db.get_node(tag)
        
        # Is there an AB record for this seq_num?
        if cmdb.has_key('ack_time'):
            raise OCSintError("Error ack reply: duplicate ack record matching sequence number (%d)" % \
                                (cmdb.seq_num))

        # Record AB record for this seq_num
        self.db.setvals(self.monchannels, tag, ack_time=time.time(),
                        ack_result=result)

        # Is there a command record for this seq_num?  Should be.
        if not cmdb.has_key('cmd_time'):
            raise OCSintError("Error in ack reply: no command record matching sequence number (%d)" % \
                                (cmdb.seq_num))

        # Is there an CE record for this seq_num?  Should not be.
        if cmdb.has_key('end_time'):
            errmsg = "ack reply: end record exists matching sequence number (%d)" % (cmdb.seq_num)
            #raise OCSintError(errmsg)
            # depending on network delays CE could arrive before AB...
            self.logger.warn(errmsg)
        
        # Error in AB result code?
        if result != 0:
            raise OCSintError("Error ack reply: result=%d" % result)
        

    def validate_end(self, tag, result, payload):

        cmdb = self.db.get_node(tag)
        
        # Is there an CE record for this seq_num?
        if cmdb.has_key('end_time'):
            raise OCSintError("Error end reply: duplicate end record matching sequence number (%d)" % \
                                (cmdb.seq_num))

        # Record CE record for this seq_num
        self.db.setvals(self.monchannels, tag, end_time=time.time(),
                        end_result=result, end_payload=payload)

        # Is there a command record for this seq_num?  Should be.
        if not cmdb.has_key('cmd_time'):
            raise OCSintError("Error in ack reply: no command record matching sequence number (%d)" % \
                                (cmdb.seq_num))

        # Is there an AB record for this seq_num? Should be.
        if not cmdb.has_key('ack_time'):
            errmsg = "end reply: no ack record matching sequence number (%d)" %  (cmdb.seq_num)
            #raise OCSintError(errmsg)
            # depending on network delays CE could arrive before AB...
            self.logger.warn(errmsg)

        if result != 0:
            raise OCSintError("Error end reply: result=%d, payload=%s" % \
                                (result, payload))

        if not payload.startswith('COMPLETE,'):
            raise OCSintError("status values incomplete: %s" % payload)
            
        # Success!  Unpack the data into the statusDict
        # TODO: is there something better/faster/as reliable as CommandParser
        parser = CommandParser()
        try:
            values = parser.tokenize(payload[9:])

        except CommandParser.CommandParserError, e:
            raise OCSintError("Error end reply: error parsing payload: %s" % \
                              payload)

        self.logger.debug("Before statusDict packing; values are: %s" % str(values))
        statusDict = cmdb.statusDict
        try:
            for aliasName in cmdb.keylist:
                # Pop value off of payload
                valueStr = values.pop(0).strip()

                # Try to convert it according to the correct type
                statusDict[aliasName] = self.convert(aliasName, valueStr)

        except IndexError, e:
            raise OCSintError("Error EN reply: payload is too short; alias=%s" % \
                                (aliasName))
        self.logger.debug("After statusDict packing; statusDict: %s" % str(statusDict))
        

    def sreq_recv(self, rpcmsg):
        tag = None
        seq_num = -1
        try:
            # Call handler for appropriate rpc msg type
            if rpcmsg.msg_type == 'AB':
                try:
                    data = rpcmsg.unpack_ab()

                except SOSSrpc.rpcMsgError, e:
                    raise OCSintError("SOSS RPC payload format error: %s" % str(e))

                # Look up the transaction matching this seq_num
                seq_num = data.seq_num
                tag = self.get_trans(seq_num)

                self.validate_ack(tag, data.result)

            elif rpcmsg.msg_type == 'EN':
                try:
                    data = rpcmsg.unpack_en()

                except SOSSrpc.rpcMsgError, e:
                    raise OCSintError("SOSS RPC payload format error: %s" % str(e))

                # Look up the transaction matching this seq_num
                seq_num = data.seq_num
                tag = self.get_trans(seq_num)

                self.validate_end(tag, data.result, data.payload)

                # End command validated--notify waiters
                self.db.setvals(self.monchannels, tag,
                                msg='status request processed successfully by OCS', 
                                time_done=time.time(), result=0,
                                done=True)

            else:
                raise OCSintError("Different reply than AB or EN!")

            # Delete our reference to the cmdb so as not to leak memory
            if tag:
                self.del_trans(seq_num, tag)

        except OCSintError, e:
            self.cmd_error(e, seq_num, tag)

        except Exception, e:
            self.cmd_error(e, seq_num, tag)
            raise e


class StatusDistributorInterface(BaseInterface):
    """Instrument Status Distributor class. An object of this class sends 
       status data messages (SD) to the OCS system.  It contains an RPC
       client to send these messages."""

    def __init__(self, monunitnum, stathost, ev_quit, logger, db,
                 taskqueue, monchannels=[],
                 myhost=None, myport=None, seq_num=None):
        """Look up the RPC program number corresponding to monunitnum;
           set object variables for myhost, stop event, logger, timeout, etc.;
           create queue self.statqueue for receiving status to be sent."""

        # Initialize common attributes
        super(StatusDistributorInterface, self).__init__(ev_quit, logger, db,
                                                         taskqueue,
                                                         myhost=myhost, myport=myport,
                                                         seq_num=seq_num)

        self.stathost = stathost
        self.monchannels = monchannels
        self.sendTasker = Task.make_tasker(self.sdst_send)

        # Look up 
        try:
            key = ('toOBS%d(sdst)' % monunitnum)

            self.rpcconn = SOSSrpc.clientServerPair(key, initiator=True,
                                                    logger=self.logger,
                                                    #myhost=self.myhost,
                                                    ev_quit=self.ev_quit)

        except SOSSrpc.rpcError, e:
            raise OCSintError("Error creating rpc client-server pair: %s" % \
                              str(e))


    def sdst_send(self, tablename, statusdata):
        """Send status to the OCS system.  Arguments are the tablename and
        a buffer of status data.
        """

        rpcbuf = SOSSrpc.SOSScmdRpcMsg(sender=self.myhost,
                                       receiver=self.stathost,
                                       pkt_type='ST')

        # Send message as client
        rpcbuf.pack_sd(tablename, statusdata, seq_num=self.seq_num.bump())
        try:
            res = self.rpcconn.callrpc(rpcbuf)

        except SOSSrpc.rpcClientError, e:
            raise OCSintError("rpc error sending SD command: %s" % str(e))


    def start(self, usethread=True, wait=True, timeout=None):
        # We don't operate a server, actually--only use client part
        pass

    def stop(self, wait=True, timeout=None):
        # We don't operate a server, actually--only use client part
        #self.rpcconn.stop(wait=wait)
        self.logger.info("Status distribution interface stopped.")

    def sendStatus(self, tablename, statusdata, async=False):
        """API method to send statusdata for tablename."""
        if async:
            self.taskqueue.put(self.sendTasker(tablename, statusdata))
        else:
            self.sdst_send(tablename, statusdata)


class ArchiverInterface(DAQtkInterface):
    """DAQtk FITS Archiver Class.  An object of this class executes
       transfer requests for FITS files to be sent from an OBCP to DAQ.
       It contains an RPC client to send transfer requests in DT messages 
       to DAQ, and an RPC server to receive corresponding Ack (AB) and 
       Transfer Completion (DE) messages from DAQ."""

    def __init__(self, obcpnum, obchost, ev_quit, logger, db, taskqueue,
                 monchannels=[], myhost=None, myport=None, seq_num=None):
        """Constructor.  This method looks up the key information for 
           communicating with OBC, creates and starts an RPC server
           to receive Ack and Completion messages, and creates an RPC
           client (to be started when needed) for sending transfer request
           messages."""

        # Initialize common attributes
        super(ArchiverInterface, self).__init__(ev_quit, logger, db,
                                                taskqueue,
                                                myhost=myhost, myport=myport,
                                                seq_num=seq_num)

        self.obchost = obchost
        self.obcpnum = obcpnum
        self.monchannels = monchannels
        self.key_template = 'file.%d'
        self.sendTasker = Task.make_tasker(self.file_cmd)
        self.recvTasker = Task.make_tasker(self.file_recv)

        # Look up OBC server key -> destination for a transfer request
        try:
            key = ('OBCP%dtoOBC(file)' % obcpnum)

            self.rpcconn = SOSSrpc.clientServerPair(key, initiator=True,
                                                    logger=self.logger,
                                                    ev_quit=self.ev_quit,
                                                    #myhost=self.myhost,
                                                    recvqueue=taskqueue,
                                                    func=self.recvTasker)

        except SOSSrpc.rpcError, e:
            raise OCSintError("Error creating rpc client-server pair: %s" % \
                              str(e))


    def file_cmd(self, tag):
        """This method is called to execute a transfer request for the
           files specified in 'cmdb.pathlist'.  It performs the 3-message
           protocol of a transfer request transaction (DT/AB/DE)."""

        seq_num = -1
        try:
            if not self.db.has_key(tag):
                raise OCSintError("No command data found for tag '%s'" % tag)

            cmdb = self.db.get_node(tag)

            framelist = []
            # TODO: check that cmdb.framelist is a list and check structure of
            # list
            self.logger.debug("framelist is %s" % str(cmdb.framelist))

            for pair in cmdb.framelist:
                (frame, path) = pair

                # Get absolute path of file (for FTP process on other side)
                # Apparently this does not raise an exception for a bad path
                path = os.path.abspath(path)

                if not os.path.isfile(path):
                    raise OCSintError("Not a regular file: %s" % path)

                try:
                    st = os.stat(path)

                except OSError, e:
                    raise OCSintError("Cannot stat file: %s" % str(e))

                # Extract frame id from file path
                (dir, fn) = os.path.split(path)
                match = re.match(r'^(\w+)(\.fits)*$', fn)
                if not match:
                    raise OCSintError("Bad filename: %s" % fn)

                framelist.append((path, st.st_size, frame))

            # Get new sequence number for this transaction
            seq_num = self.seq_num.bump()

            # Create buffer for RPC message
            rpcbuf = SOSSrpc.SOSScmdRpcMsg(sender=self.myhost,
                                           receiver=self.obchost,
                                           pkt_type='DT')

            # Send initial message as client
            rpcbuf.pack_ds(framelist, seq_num=seq_num)

            # Inform monitor of impending event
            self.db.setvals(self.monchannels, tag, seq_num=seq_num,
                            cmd_time=time.time())
            # Associate this tag with this seq_num
            self.put_trans(seq_num, tag)

            # Make the client RPC call
            try:
                res = self.rpcconn.callrpc(rpcbuf)

            except SOSSrpc.rpcClientError, e:
                raise OCSintError("rpc error sending DS command: %s" % str(e))

        except OCSintError, e:
            self.cmd_error(e, seq_num, tag)

        except Exception, e:
            self.cmd_error(e, seq_num, tag)
            raise e


    def validate_ack(self, tag, result):

        cmdb = self.db.get_node(tag)
        
        # Is there an AB record for this seq_num?
        if cmdb.has_key('ack_time'):
            raise OCSintError("Error ack reply: duplicate ack record matching sequence number (%d)" % \
                                (cmdb.seq_num))

        # Record AB record for this seq_num
        self.db.setvals(self.monchannels, tag, ack_time=time.time(),
                        ack_result=result)

        # Is there a command record for this seq_num?  Should be.
        if not cmdb.has_key('cmd_time'):
            raise OCSintError("Error in ack reply: no command record matching sequence number (%d)" % \
                                (cmdb.seq_num))

        # Is there an DE record for this seq_num?  Should not be.
        if cmdb.has_key('end_time'):
            errmsg = "ack reply: end record exists matching sequence number (%d)" % (cmdb.seq_num)
            # depending on network delays DE could arrive before AB...
            #raise OCSintError(errmsg)
            self.logger.warn(errmsg)

        # Error in AB result code?
        if result != 0:
            raise OCSintError("Error ack reply: result=%d" % (result))
        

    def validate_end(self, tag, result, statuslist):

        cmdb = self.db.get_node(tag)
        
        # Is there an DE record for this seq_num?
        if cmdb.has_key('end_time'):
            raise OCSintError("Error end reply: duplicate end record matching sequence number (%d)" % \
                                (cmdb.seq_num))

        # Record DE record for this seq_num
        self.db.setvals(self.monchannels, tag, end_time=time.time(),
                        end_result=result, end_status=statuslist)

        # Is there a command record for this seq_num?  Should be.
        if not cmdb.has_key('cmd_time'):
            raise OCSintError("Error in ack reply: no command record matching sequence number (%d)" % \
                                (cmdb.seq_num))

        # Is there an AB record for this seq_num? Should be.
        if not cmdb.has_key('ack_time'):
            errmsg = "end reply: no ack record matching sequence number (%d)" %  (cmdb.seq_num)
            #raise OCSintError(errmsg)
            # depending on network delays DE could arrive before AB...
            self.logger.warn(errmsg)

        # TODO: check statuslist?
        if result != 0:
            raise OCSintError("Error end reply: result=%d status=%s" % \
                                (result, str(statuslist)))
        

    def file_recv(self, rpcmsg):

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
                    raise OCSintError("SOSS RPC payload format error: %s" % str(e))

                # Look up the transaction matching this seq_num
                seq_num = data.seq_num
                tag = self.get_trans(seq_num)

                self.validate_ack(tag, data.result)

            elif rpcmsg.msg_type == 'DE':
                try:
                    data = rpcmsg.unpack_de()

                except SOSSrpc.rpcMsgError, e:
                    raise OCSintError("SOSS RPC payload format error: %s" % str(e))

                # Look up the transaction matching this seq_num
                seq_num = data.seq_num
                tag = self.get_trans(seq_num)

                self.validate_end(tag, data.result, data.statuslist)

                # End command validated--notify waiters
                self.db.setvals(self.monchannels, tag,
                                msg='file transfer request processed successfully by OCS',
                                time_done=time.time(), result=0,
                                done=True)

            else:
                raise OCSintError("Different reply than AB or DE!")
                    
            # Delete our reference to the cmdb so as not to leak memory
            if tag:
                self.del_trans(seq_num, tag)

        except OCSintError, e:
            self.cmd_error(e, seq_num, tag)

        except Exception, e:
            self.cmd_error(e, seq_num, tag)
            raise e


class ocsInt(object):
    """OCS Interface Container Class.  An object of this class 
       instantiates objects of the various interface classes above
       as members.  It also provides a start method to start all threads
       and RPC servers, and a stop method to terminate everything."""

    def __init__(self, obcpnum, obshost=None, stathost=None, obchost=None,
                 thruhost=None, gethost=None,
                 obsif=None, statif=None, obcif=None, getif=None,
                 interfaces='cmd,thru,sreq,sdst,file', db=None,
                 logger=None, ev_quit=None, monunitnum=3, seq_num=None,
                 threadPool=None, numthreads=None):

        self.obcpnum = obcpnum
        self.timeout = 0.1
        self.qtask = None
            
        # Get list of channels to communicate with SOSS hosts.
        self.iface_names = interfaces.split(',')
        
        for name in self.iface_names:
            if not name in ('cmd', 'thru', 'sdst', 'sreq', 'file'):
                raise OCSintError("Interfaces must be any combination of: cmd, thru, sdst, sreq, file--'%s'" % interfaces)

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

        # Get hostname of our host.
        myhost = SOSSrpc.get_myhost(short=True)

        # Assume local host if no hosts given for connections of various
        # subsystems.
        if not obsif:
            obsif = myhost
        if not obshost:
            obshost = myhost
        if not thruhost:
            thruhost = myhost
        if not obcif:
            obcif = myhost
        if not obchost:
            obchost = myhost
        if not statif:
            statif = myhost
        if not stathost:
            stathost = myhost
        if not getif:
            getif = myhost
        if not gethost:
            gethost = myhost

        if numthreads:
            self.numthreads = numthreads
        else:
            # Estimate number of threads needed to handle traffic
            self.numthreads = 6 + (len(interfaces) * 2) + 10
            
        # Thread pool for autonomous tasks
        if threadPool:
            self.threadPool = threadPool
            self.mythreadpool = False
        else:
            self.threadPool = Task.ThreadPool(logger=self.logger,
                                              ev_quit=self.ev_quit,
                                              numthreads=self.numthreads)
            self.mythreadpool = True
            
        # Make/load the local monitor for tracking transactions
        self.db = Monitor.Minimon('%s.mon' % svcname, self.logger,
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

        # For task inheritance:
        self.tag = 'DAQtk'
        self.shares = ['logger', 'ev_quit', 'timeout', 'threadPool']

        # Build up desired set of interfaces.
        self.iface = {}
        
        for name in self.iface_names:
            # Create a log for logging results
            if not logger:
                queue = Queue.Queue()
                log = ssdlog.mklog(name, queue, logging.DEBUG)
            else:
                log = logger
                queue = None

            if name == 'cmd':
                iface = CommandReceiverInterface(obcpnum, ev_quit, log, self.db,
                                                 self.taskqueue, myhost=obsif,
                                                 seq_num=self.seq_num,
                                                 monchannels=self.monchannels)
                self.iface[name] = Bunch(log=log, logqueue=queue, iface=iface)
                continue
            
            if name == 'thru':
                iface = ThroughCommandInterface(obcpnum, thruhost, ev_quit,
                                                log, self.db,
                                                self.taskqueue, myhost=obsif,
                                                seq_num=self.seq_num,
                                                monchannels=self.monchannels)
                self.iface[name] = Bunch(log=log, logqueue=queue, iface=iface)
                continue
            
            if name == 'sreq':
                iface = StatusRequestInterface(obcpnum, gethost, ev_quit,
                                               log, self.db,
                                               self.taskqueue, myhost=getif,
                                               seq_num=self.seq_num,
                                               monchannels=self.monchannels)
                self.iface[name] = Bunch(log=log, logqueue=queue, iface=iface)
                continue
            
            if name == 'sdst':
                iface = StatusDistributorInterface(monunitnum, stathost,
                                                   ev_quit, log, self.db,
                                                   self.taskqueue, myhost=statif,
                                                   seq_num=self.seq_num,
                                                   monchannels=self.monchannels)
                self.iface[name] = Bunch(log=log, logqueue=queue, iface=iface)
                continue

            if name == 'file':
                iface = ArchiverInterface(obcpnum, obchost, ev_quit, log,
                                          self.db, self.taskqueue,
                                          myhost=obcif, seq_num=self.seq_num,
                                          monchannels=self.monchannels)
                self.iface[name] = Bunch(log=log, logqueue=queue, iface=iface)
                continue

            raise OCSintError("Unknown interface type: '%s'" % name)


    def get_threadPool(self):
        return self.threadPool
    
    def get_monitor(self):
        return self.db

    ##########################################################
    # METHODS FOR INSTRUMENTS
    ##########################################################

    def start_ifaces(self, ifaces=None, wait=True):
        """Start DAQtk interfaces.
        """
        if not ifaces:
            ifaces = self.iface_names

        for name in ifaces:
            self.iface[name].iface.start(usethread=True, wait=wait)


    def start(self, wait=True):
        """Start the interfaces."""
        
        self.ev_quit.clear()

        # Start our thread pool (if we created it)
        if self.mythreadpool:
            self.threadPool.startall(wait=True)

        # Start our monitor (if we created it)
        if self.mymonitor:
            self.db.start(wait=True)
        
        # Initialize the task queue processing task
        t = Task.QueueTaskset(self.taskqueue, waitflag=False)
        self.qtask = t
        t.initialize(self)
        t.start()
        
        self.start_ifaces(wait=wait)


    def stop_ifaces(self, ifaces=None, wait=True):
        """Stop instrument interfaces.
        """
        if not ifaces:
            ifaces = self.iface_names

        for name in ifaces:
            self.iface[name].iface.stop(wait=wait)

       
    def stop(self, wait=True):
        """Stop the interfaces."""

        # Stop our monitor (if we created it)
        if self.mymonitor:
            #self.db.releaseAll()        # Release all waiters
            self.db.stop(wait=True)
        
        self.stop_ifaces(wait=wait)
        
        if self.qtask:
            self.qtask.stop()
        
        # Stop our thread pool (if we created it)
        if self.mythreadpool:
            self.threadPool.stopall(wait=wait)

        self.ev_quit.set()
        self.logger.info("DAQtk INTERFACE STOPPED.")


    def initialize(self, ins):
        """Set the Instrument (or subclass thereof) object (_ins_) with which
        this OCS interface will communicate.  This should be done before you
        start() this object."""

        if not self.iface.has_key('cmd'):
            raise OCSintError("No command channel defined for this OCS interface")
        
        self.iface['cmd'].iface.initialize(ins)


    def awaitTransaction(self, tag, block=True, timeout=None):

        if not block:
            return ('noblock', 0, 'non-blocking call')

        # If task submission was successful, then watch the monitor for
        # the result.
        try:
            d = self.db.getitem_any(['%s.done' % tag], timeout=timeout)

        except Monitor.TimeoutError, e:
            self.logger.error(str(e))
            return ('err', 1, 'Transaction timed out for tag=%s' % tag)
        
        # Task terminated.  Get all items currently associated with this
        # transaction.
        vals = self.db.getitems_suffixOnly(tag)
        if type(vals) != dict:
            self.logger.error("Could not get transaction info for tag=%s" % (
                tag))
            return ('err', 1, 'N/A')

        self.logger.debug("%s transaction info: %s" % (tag, str(vals)))

        # Interpret transaction results:
        if vals.has_key('time_done') and vals.has_key('time_start'):
            self.logger.debug("%s OCS transaction time: %.3f sec" % (
                tag, vals['time_done'] - vals['time_start']))

        # Interpret transaction results:
        if vals.has_key('end_time'):
            return ('end', vals.get('end_result', 1), vals.get('msg', 'N/A'))

        if vals.has_key('ack_time'):
            return ('ack', vals.get('ack_result', 1), vals.get('msg', 'N/A'))

        if vals.has_key('cmd_time'):
            return ('cmd', 1, vals.get('msg', 'N/A'))

        return ('err', 1, vals.get('msg', 'N/A'))


    def requestStatus(self, statusDict, block=True, timeout=None):
        """Request status from the OCS.  statusDict is a dictionary containing
        the keys for status that are requested.  Upon return the values for
        for these keys will be set in the dictionary.  A return value of zero
        indicates that all values were retrieved successfully.  If non-zero,
        then some values may have not been successfully retrieved."""

        if not self.iface.has_key('sreq'):
            raise OCSintError("No status request channel defined for this OCS interface")
        
        # Get a tag for this command
        tag = Task.get_tag(None)
        self.logger.debug("tag=%s statusDict=%s" % (tag, statusDict))

        try:
            self.db.setvals(self.monchannels, tag, time_start=time.time(),
                            statusDict=statusDict)

            self.iface['sreq'].iface.submit_request(tag)

        except Exception, e:
            errmsg = "Error invoking submit_statusRequest: %s" % str(e)
            self.logger.error(errmsg)

            # Signal to any waiters on this command that we are done
            self.db.setvals(self.monchannels, tag, msg=errmsg,
                            time_done=time.time(), result=-1, done=True)
            
        return self.awaitTransaction(tag, block=block, timeout=timeout)


    def execCommand(self, cmdstr, block=True, timeout=None):
        """Send a through command to the OCS.  cmdstr is a device-dependant
        command.  A return value of zero indicates success.  If non-zero,
        then some error occurred."""

        if not self.iface.has_key('thru'):
            raise OCSintError("No through command channel defined for this OCS interface")

        # Get a tag for this command
        tag = Task.get_tag(None)
        self.logger.debug("tag=%s cmd='%s'" % (tag, cmd_str))

        try:
            # Remove any extraneous whitespace
            cmd_str = cmd_str.strip()
            
            self.db.setvals(self.monchannels, tag, time_start=time.time(),
                            cmd_str=cmd_str)

            # send job to work queue
            self.iface['thru'].iface.submit_request(tag)

        except Exception, e:
            errmsg = "Error invoking submit_command: %s" % str(e)
            self.logger.error(errmsg)

            # Signal to any waiters on this command that we are done
            self.db.setvals(self.monchannels, tag, msg=errmsg,
                            time_done=time.time(), result=-1, done=True)
            
        return self.awaitTransaction(tag, block=block, timeout=timeout)


    def sendStatus(self, tablename, statusdata):
        """Send status to the OCS.  statusdata is a buffer of status data
        to send.  A return value of zero indicates that the status values
        were successfully sent to OCS.""" 
    
        if not self.iface.has_key('sdst'):
            raise OCSintError("No status send channel defined for this OCS interface")

        try:
            return self.iface['sdst'].iface.sendStatus(tablename, statusdata)

        except SOSSrpc.rpcClientError, e:
            raise OCSintError("Error sending status: %s" % str(e))

    
    def archive_framelist(self, framelist, block=True, timeout=None):
        """Submit a FITS image data file to the OCS for archiving.
        A return value of zero indicates that the file was successfully
        transferred."""
        
        if not self.iface.has_key('file'):
            raise OCSintError("No archive channel defined for this OCS interface")
        
        # Get a tag for this command
        tag = Task.get_tag(None)
        self.logger.debug("tag=%s framelist=%s" % (tag, str(framelist)))

        try:
            self.db.setvals(self.monchannels, tag, time_start=time.time(),
                            framelist=framelist)

            self.iface['file'].iface.submit_request(tag)

        except Exception, e:
            errmsg = "Error invoking submit_fits: %s" % str(e)
            self.logger.error(errmsg)

            # Signal to any waiters on this command that we are done
            self.db.setvals(self.monchannels, tag, msg=errmsg,
                            time_done=time.time(), result=-1, done=True)
            
        return self.awaitTransaction(tag, block=block, timeout=timeout)



# END DAQtk.py

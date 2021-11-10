#!/usr/bin/env python
#
# TCSint2.py -- 2nd telescope control system interface
#
# The TCS interface for the Gen2 SOSS system.
#
# Yasuhiko Sakakibara <yasu@subaru.naoj.org>
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed May  8 15:43:55 HST 2013
#]
#
import sys, time, os
import signal
# for simulator
import datetime
import logging, ssdlog
import threading
# profile imported below (if needed)
# pdb imported below (if needed)
# optparse imported below (if needed)

import rpc
import SOSS.SOSSrpc as SOSSrpc
import Task
import remoteObjects as ro
import remoteObjects.Monitor as Monitor

import Packet as pkt
import TowardTSCpacker
import telcmds

UID = 3
GID = 8

    
def makeTimestamp():
    return datetime.datetime.now(pkt.TZ_LOCAL)


class TCSintError(Exception):
    pass


class PartialTCSClient(object):
    '''
    "Business Logic" part of the RPC client.
    '''
    def __init__(self):
        self._lock = threading.RLock()

    def addpackers(self):
        self.packer   = TowardTSCpacker.TOWARDTSCPacker()
        self.unpacker = TowardTSCpacker.TOWARDTSCUnpacker('')
    
    def null(self):
        return self.make_call(0, None, None, None)

    def call(self, pkt_str, uid, gid):
        with self._lock:
            # TODO: figure out something more elegant here, probably by
            # modifying make_call in rpc.py
            self.uid = uid
            self.gid = gid
            self.cred = None

            self.logger.info('%s (uid=%d, gid=%d)' % (pkt_str, self.uid, self.gid))

            res = self.make_call(1, pkt_str, self.packer.pack_string,
                                 self.unpacker.unpack_bool)
            self.logger.debug('RES<=%s' % str(res))

        return res

    def send(self, seq_num, commandString, uid=UID, gid=GID, sender='OCS'):

        commandId    = commandString[0:6]
        commandParam = commandString[6:]
        payload = pkt.CommandRequestPayload(seqNum=seq_num, 
                                            commandId=commandId, 
                                            commandParam=commandParam)
        payload_str = payload.format()
        header = pkt.TSCHeader(messageType='CD',
                               #sender     ='OCS',
                               sender     = sender,
                               receiver   = 'TSC',
                               pid        = 0,
                               timeSent   = makeTimestamp(),

                               lenPayload = len(payload_str))
         
        pkt_str = header.format() + payload_str
        return self.call(pkt_str, uid, gid)

    def ack(self, seq_num, commandId, receiptNum, projectedCompletionTime,
            uid=UID, gid=GID):

        payload = pkt.CommandAckPayload(seqNum=seq_num, 
                                        commandId=commandId, 
                                        receiptNum=receiptNum,
                                        projectedCompletionTime=projectedCompletionTime)
        payload_str = payload.format()
        header = pkt.TSCHeader(messageType='CA',
                 #receiver  ='OBS',
                 receiver   ='OCS',
                 sender     ='TSC',
                 pid        = 0,
                 timeSent   = makeTimestamp(),

                 lenPayload = len(payload_str))
         
        pkt_str = header.format() + payload_str
        return self.call(pkt_str, uid, gid)

    def nack(self, seq_num, commandId, errorCode,
             uid=UID, gid=GID):

        payload = pkt.CommandNackPayload(seqNum=seq_num, 
                                         commandId=commandId, 
                                         errorCode=errorCode)
        payload_str = payload.format()
        header = pkt.TSCHeader(messageType='CA',
                 #receiver  ='OBS',
                 receiver   ='OCS',
                 sender     ='TSC',
                 pid        = 0,
                 timeSent   = makeTimestamp(),

                 lenPayload = len(payload_str))
         
        pkt_str = header.format() + payload_str
        return self.call(pkt_str, uid, gid)

    def complete(self, seq_num, commandId, receiptNum, resultCode, resultInfo,
                 uid=UID, gid=GID):

        payload = pkt.CommandCompletionPayload(seqNum=seq_num, 
                                               commandId=commandId, 
                                               receiptNum=receiptNum,
                                               resultCode=resultCode,
                                               resultInfo=resultInfo)
        payload_str = payload.format()
        header = pkt.TSCHeader(messageType='CE',
                 #receiver  ='OBS',
                 receiver   ='OCS',
                 sender     ='TSC',
                 pid        = 0,
                 timeSent   = makeTimestamp(),

                 lenPayload = len(payload_str))
         
        pkt_str = header.format() + payload_str
        return self.call(pkt_str, uid, gid)

   
class TCSClient(PartialTCSClient, rpc.TCPClient):
    def __init__(self, host, prognum, vers=1, sec=(rpc.AUTH_UNIX, None),
                 logger=None):
        rpc.TCPClient.__init__(self, host, prognum, vers, sec=sec,
                               logger=logger)
        PartialTCSClient.__init__(self)
        # These are needed by the rpc.py package
        self.uid = UID
        self.gid = GID


class TCS_rpcServer(SOSSrpc.TCP_rpcServer):

    #
    # fully realized methods for abstract methods in rpcServer
    #
    def addpackers(self):
        """Set data payload packer and unpacker to OSSC_ComCD versions.
        This will be called from rpc.py
        """
        self.packer   = TowardTSCpacker.TOWARDTSCPacker()
        self.unpacker = TowardTSCpacker.TOWARDTSCUnpacker('')


    def handle_1(self):
        data = self.unpacker.unpack_opaque()

        #self.logger.info("RPC<=%s" % data)
        self.logger.info(data)

        res = False
        try:
            self.turn_around()

            self.func(data)

            res = True
        
        except rpc.RPCUnextractedData:
            self.logger.error("*** Unextracted Data in request!")

        except Exception, e:
            self.logger.error("Error processing packet: %s" % str(e))

        # Return confirmation result
        self.packer.pack_bool(res)


class TCSint(object):

    def __init__(self, tcshost, 
                 ev_quit, logger, minimon, threadPool,
                 prog_send=0x20000011, prog_recv=0x20000012,
                 myhost=None, myport=None, seq_num=None,
                 telcmdDict=None, telackDict=None):
        self.tcshost = tcshost
        self.ev_quit = ev_quit
        self.logger = logger
        self.minimon = minimon
        self.threadPool = threadPool

        self.prog_send = prog_send
        self.prog_recv = prog_recv

        self.wait_ack = False
        self.use_subtracking = False
        # timeout (secs) to wait for an ACK in multi-command commands
        self.ack_timeout = 10.0

        # Set interface for RPC server
        if myhost:
            self.myhost = myhost
        else:
            self.myhost = SOSSrpc.get_myhost(short=True)
            # None binds to all available interfaces
            #self.myhost = None
        # If None, will choose random, open port
        self.myport = myport
        if seq_num:
            self.seq_num = seq_num
        else:
            self.seq_num = SOSSrpc.rpcSequenceNumber()

        if not telcmdDict:
            telcmdDict = {}
        self.telcmds = telcmdDict
        if not telackDict:
            telackDict = {}
        self.telacks = telackDict
        
        self.client = None
        self.server = None

        # Result parsers
        self.packetParser = pkt.PacketParser()
        self.packetParser.setHeaderParser(pkt.TSCHeaderParser())
        self.packetParser.addPayloadParser(pkt.CommandRequestPayloadParser())
        self.packetParser.addPayloadParser(pkt.CommandAckPayloadParser())
        self.packetParser.addPayloadParser(pkt.CommandCompletionPayloadParser())
        self.packetParser.addPayloadParser(pkt.AsyncMessagePayloadParser())

        self.key_template = 'cmd.%d'
        self.monchannels  = ['TCSint0']
        self.lock = threading.RLock()

        # Safety lock that must be OFF before commands can be executed
        self.safetyLock = threading.Event()
        # set()?  what should be the default
        self.safetyLockOff()

        # Needed for starting and intializing tasks
        self.shares = ['logger', 'threadPool']
        self.tag = 'TCSint2'
        

    def start(self, wait=True):
        """Start telescope command rpc interface.
        """
        self.client = None

        self.server = TCS_rpcServer(self.prog_recv, logger=self.logger,
                                    ev_quit=self.ev_quit, func=self.recv_reply)
        self.server.start(wait=wait)

    def stop(self, wait=True):
        """Stop telescope command rpc interface.
        """
        self.client = None

        if self.server:
            self.server.stop(wait=wait)


    def safetyLockOn(self):
        self.safetyLock.set()
        self.logger.info("Safety lock is now turned ON")
        
    def safetyLockOff(self):
        self.safetyLock.clear()
        self.logger.info("Safety lock is now turned OFF")
        
    def safetyLockSetP(self):
        return self.safetyLock.isSet()
        
    def setWaitAck(self, bool):
        self.wait_ack = bool
        
    def setSubTrack(self, bool):
        self.use_subtracking = bool
        
    def _get_key(self, seq_num):
        return self.key_template % seq_num
    
    def put_trans(self, seq_num, tag):
        key = self._get_key(seq_num)

        # Is there a cmdb bundle for this seq_num?
        if self.minimon.has_key(key):
            raise TCSintError("Tag exists matching sequence number %d" % \
                              (seq_num))

        else:
            self.minimon[key] = tag

    def get_trans(self, seq_num):
        key = self._get_key(seq_num)

        # Is there a bundle for this seq_num?
        if self.minimon.has_key(key):
            return self.minimon[key]

        else:
            raise TCSintError("No tag matching sequence number %d" % \
                              (seq_num))

    def del_trans(self, seq_num, tag):
        """This is called to delete a transaction from the pending transaction
        table (self.minimon).  The transaction tag is deleted under (key) IFF the
        transaction contains all three RPC components: cmd, ack, end
        """
        key = self._get_key(seq_num)

        # Raises an exception if tag not found?
        if not self.minimon.has_key(key):
            self.logger.warn("No command data found for tag '%s'" % tag)
            return

        cmdb = self.minimon.get_node(tag)
        cmdb.enter()
        try:
            if cmdb.has_key('cmd') and cmdb.has_key('ack') and \
                   cmdb.has_key('end'):
                try:
                    del self.minimon[key]
                except KeyError:
                    pass

        finally:
            cmdb.leave()


    def sleep(self, secs):
        self.ev_quit.wait(secs)

        
    def send_cmd(self, tag, cmd_str, uid=UID, gid=GID, sender='OCS'):
        """Send a string command to the telescope.  _tag_ is a task manager
        generated id for keeping track of this command.
        """

        self.logger.debug("tag=%s cmd='%s'" % (tag, cmd_str))
        try:
            if self.minimon.has_val(tag, 'time_start'):
                raise TCSintError("A command already exists with this tag")

            telcmd = cmd_str[0:6]
            try:
                d = self.telcmds[telcmd]
                #self.logger.info('d = %s' % str(d))
                descr = d['title']

            except KeyError, IndexError:
                descr = "(no description available)"

            cmd_repn = "%s %s" % (telcmd, descr) 
                
            self.minimon.setvals(self.monchannels, tag, time_start=time.time(),
                                 cmd_str=cmd_str, cmd_desc=descr,
                                 cmd_repn=cmd_repn,
                                 uid=uid, gid=gid, sender=sender)

            self.send_native_cmd(tag)
            
        except Exception, e:
            msg = "Error invoking send_cmd: %s" % str(e)
            self.logger.error(msg)

            # Signal to any waiters on this command that we are done
            self.minimon.setvals(self.monchannels, tag, msg=msg,
                                 time_done=time.time(),
                                 done=True)

    def start_cmd(self, tag, cmd_str, uid=UID, gid=GID, sender='OCS'):
        # Give send_cmd job to worker
        task = Task.FuncTask(self.send_cmd, [tag, cmd_str],
                             {'uid': uid, 'gid': gid, 'sender': sender},
                             logger=self.logger)
        task.init_and_start(self)
        
    def wait_for_termination(self, taglist):
        # *** WARNING *** WARNING *** WARNING ***
        # timeout=None means this interface will hangup at times!!
        res = self.minimon.getitem_all(taglist, timeout=None)

        for tag, val in res.items():
            if val != 0:
                raise TCSintError("Error result from TSC for tag %s" % (
                    tag))
        
    def send_cmds(self, tag, cmd_str, cmd_list, uid=UID, gid=GID, sender='OCS'):
        """Send a list of string commands to the telescope.
        _tag_ is a task manager generated id for keeping track of this transaction.
        """

        try:
            if self.minimon.has_val(tag, 'time_seq'):
                raise TCSintError("A command already exists with this tag")
            
            res = -1
            try:
                ## self.minimon.setvals(self.monchannels, tag, cmd_str=cmd_str,
                ##                      time_start=time.time())
                self.minimon.setvals([], tag, time_seq=time.time())

                taglist = []
                count = 0
                for cmd_str in cmd_list:
                    self.logger.debug("cmd_str=%s" % (cmd_str))
                    subtag = '%s.%d' % (tag, count)

                    if cmd_str.startswith('SLEEP'):
                        # "built in" sleep specified; delay for the specified duration
                        duration = float(cmd_str.split()[1]) / 1000.0
                        self.sleep(duration)
                        res = 0

                    elif cmd_str.startswith('WAIT'):
                        # "built in" wait specified; wait for all pending tasks
                        self.wait_for_termination(taglist)
                        taglist = []

                    else:
                        # Associate subtag for subcommand tracking
                        if self.use_subtracking:
                            self.minimon.setvals(self.monchannels, tag,
                                                 subpath=subtag)

                        ack_tag = '%s.ack_result' % (subtag)
                        end_tag = '%s.end_result' % (subtag)
                        taglist.append(end_tag)

                        # Issue this individual command
                        self.send_cmd(subtag, cmd_str, uid=uid, gid=gid,
                                      sender=sender)

                        if self.wait_ack:
                            # Wait to iterate until we see an ACK or END from this
                            # command in our monitor
                            res = self.minimon.getitem_any([ack_tag, end_tag],
                                                           timeout=self.ack_timeout)
                            if res.has_key(ack_tag) and (res[ack_tag] != 0):
                                # If result contains a NACK, then raise an error
                                raise TCSintError("Command '%s': NACK result from TSC" % (
                                    cmd_str))

                            if res.has_key(end_tag) and (res[end_tag] != 0):
                                # If command is finished, check result
                                raise TCSintError("Command '%s': error result from TSC" % (
                                    cmd_str))

                    count += 1

                ## # If there are any more tags left to wait on, wait on them now
                ## if len(taglist) > 0:
                ##     self.wait_for_termination(taglist)

                msg = "All commands sent successfully"
                res = 0

            except Exception, e:
                msg = "Error invoking send_cmds: %s" % str(e)
                self.logger.error(msg)

        finally:
            # Signal to any waiters on this command that we are done
            #self.minimon.setvals(self.monchannels, tag, msg=msg,
            #                     time_done=time.time(), result=res, done=True)
            pass


    def start_cmds(self, tag, cmd_str, cmd_list, uid=UID, gid=GID, sender='OCS'):
        # Give send_cmd job to worker
        task = Task.FuncTask(self.send_cmds, [tag, cmd_str, cmd_list],
                             {'uid': uid, 'gid': gid, 'sender': sender},
                             logger=self.logger)
        task.init_and_start(self)
        

    def make_client(self, tcshost):
        with self.lock:
            self.client = None
            try:
                self.client = TCSClient(tcshost, self.prog_send, vers=1,
                                        logger=self.logger)
            except Exception, e:
                raise TCSintError("Couldn't create RPC client: %s" % str(e))


    def send_native_cmd(self, tag):

        seq_num = -1
        try:
            # Raises an exception if tag not found?
            if not self.minimon.has_key(tag):
                raise TCSintError("No command data found for tag '%s'" % tag)

            cmdb = self.minimon.get_node(tag)

            # Final check--check safety lock
            if self.safetyLock.isSet():
                raise TCSintError("Safety lock is ON")

            # Get new sequence number for this transaction
            seq_num = self.seq_num.bump()

            # Inform monitor of impending event
            self.minimon.setvals(self.monchannels, tag, seq_num=seq_num,
                                 cmd_time=time.time())
            
            # Associate this tag with this seq_num
            self.put_trans(seq_num, tag)

            # Make the rpc client call
            with self.lock:
                if not self.client:
                    self.make_client(self.tcshost)

                try:
                    res = self.client.send(seq_num, cmdb.cmd_str,
                                           uid=cmdb.uid, gid=cmdb.gid,
                                           sender=cmdb.sender)

                except Exception, e:
                    self.logger.warn("Client call error (possible stale client), resetting client...")
                    self.make_client(self.tcshost)

                    # Try one more time...best effort
                    try:
                        res = self.client.send(seq_num, cmdb.cmd_str,
                                               uid=cmdb.uid, gid=cmdb.gid,
                                               sender=cmdb.sender)

                    except Exception, e:
                        self.client = None
                        raise TCSintError("rpc error sending CD command: %s" % str(e))
                
                #return ro.OK

        except Exception, e:
            message = 'Command failed with error %s' % str(e)
            self.logger.error(message)
            self.minimon.setvals(self.monchannels, tag,
                                 done=True, time_done=time.time(),
                                 end_result=1, msg=message)

            #return ro.ERROR


    def validate_ack(self, tag, result, infoDict):
        """Validate the contents of the ack message received from the telescope.
        """

        cmdb = self.minimon.get_node(tag)
        
        # Is there an AB record for this seq_num?
        if cmdb.has_key('ack_time'):
            raise TCSintError("Error ack reply: duplicate ack record matching sequence number (%d)" % (
                    cmdb.seq_num))

        if infoDict.has_key('est_time'):
            dt = infoDict['est_time']
            # Sometimes we get a None estimate!!
            if dt != None:
                # convert datetime() format to time.time() format
                t = time.mktime(dt.timetuple())
            else:
                # TODO: what should this be?
                t = time.time()
            infoDict['est_time'] = t
            #infoDict['est_time_human'] = time.ctime(t)

        if self.telacks.has_key(str(result)):
            d = self.telacks[str(result)]
            title, descr = d['title'], d['descr']
        else:
            title, descr = "N/A", "N/A"

        # Record AB record for this seq_num
        self.minimon.setvals(self.monchannels, tag, ack_time=time.time(),
                             ack_result=result, ack_title=title,
                             ack_descr=descr, **infoDict)

        # Is there a command record for this seq_num?  Should be.
        if not cmdb.has_key('cmd_time'):
            raise TCSintError("Error in ack reply: no command record matching sequence number (%d)" % \
                                (cmdb.seq_num))

        # Is there an CE record for this seq_num?  Should not be.
        # This should be a warning...depending on network delays CE could
        # arrive before AB
        if cmdb.has_key('end_time'):
            errmsg = "ack reply: end record exists matching sequence number (%d)" % (cmdb.seq_num)
            #raise TCSintError(errmsg)
            self.logger.warn(errmsg)

        # Error in AB result code?
        if result != 0:
            ## raise TCSintError("Error ack reply: result=%s" % str(result))
            raise TCSintError("Command '%s' (%s): Error ACK from TSC: %s" % (
                cmdb.cmd_str, cmdb.cmd_desc, str(result)))
        

    def validate_end(self, tag, result, infoDict):
        """Validate the contents of the end command message received from the telescope.
        """

        cmdb = self.minimon.get_node(tag)
        
        # Is there an CE record for this seq_num?
        if cmdb.has_key('end_time'):
            raise TCSintError("Error end reply: duplicate end record matching sequence number (%d)" % \
                                (cmdb.seq_num))

        # Record CE record for this seq_num
        self.minimon.setvals(self.monchannels, tag, end_time=time.time(),
                             end_result=result, **infoDict)

        # Is there a command record for this seq_num?  Should be.
        if not cmdb.has_key('cmd_time'):
            raise TCSintError("Error in ack reply: no command record matching sequence number (%d)" % \
                                (cmdb.seq_num))

        # Is there an AB record for this seq_num? Should be.
        if not cmdb.has_key('ack_time'):
            # Depending on network delays CE could arrive before AB...
            errmsg = "end reply: no ack record matching sequence number (%d)" % \
                     (cmdb.seq_num)
            ##raise TCSintError(errmsg)
            self.logger.warn(errmsg)

        if result != 0:
            ## raise TCSintError("Error end reply: result=%s, infoDict=%s" % \
            ##                     (str(result), str(infoDict)))
            raise TCSintError("Command '%s' (%s): Error END from TSC: result=%s infoDict=%s" % (
                cmdb.cmd_str, cmdb.cmd_desc, str(result), str(infoDict)))
        

    def recv_reply(self, data):

        try:
            # Add send_native_cmd job to work queue
            task = Task.FuncTask(self.process_reply, [data], {},
                                 logger=self.logger)
            task.init_and_start(self)
            
        except Exception, e:
            msg = "Error invoking recv_reply: %s" % str(e)
            self.logger.error(msg)


    def process_reply(self, data):

        h, p = self.packetParser.parse(data)
        self.logger.debug(h.format())
        self.logger.debug(p.format())

        # Get sequence number and look up transaction
        seq_num = 0

        tag = None
        try:
            if h.messageType == 'CA':
                seq_num = p.seqNum
                # Get pending transaction matching seq_num in ack
                tag = self.get_trans(seq_num)

                if isinstance(p, pkt.CommandAckPayload):
                    # COMMAND ACKNOWLEDGED (ACK)
                    self.validate_ack(tag, 0, 
                                      { 'est_time': p.projectedCompletionTime,
                                        'receiptNum': p.receiptNum,
                                        })

                elif isinstance(p, pkt.CommandNackPayload):
                    # COMMAND ACKNOWLEDGE FAILED (NACK)
                    self.validate_ack(tag, p.errorCode, {})
                    
                else:
                    raise TCSintError("Error ack reply: error parsing packet: %s" % str(p))
                
            elif h.messageType == 'CE':
                seq_num = p.seqNum
                # Get pending transaction matching seq_num in end
                tag = self.get_trans(seq_num)

                if isinstance(p, pkt.CommandCompletionPayload):
                    if p.resultCode == 'COMPLETE':
                        # COMMAND COMPLETED
                        self.validate_end(tag, 0, {})

                    else:
                        # COMMAND COMPLETION FAILED
                        self.validate_end(tag, p.resultCode,
                                          {'resultInfo': p.resultInfo,
                                           })
                        
                    # End command validated
                    self.minimon.setvals(self.monchannels, tag,
                                         msg='cmd tranaction with TCS complete',
                                         time_done=time.time(), result=0,
                                         done=True)

                else:
                    raise TCSintError("Error end reply: error parsing packet: %s" % str(p))
                
            elif h.messageType == 'CM':

                self.logger.error("Asynchronous message from TSC: %d:%s" % (
                        p.msgCode, p.msgText))

                time_err = time.time()
                # Asynchronous error message from TSC
                tag = 'mon.error.2.TCSint.%s' % (
                    str(time_err).replace('.', '-'))
                self.minimon.setvals(['errors'], tag,
                                     code=p.msgCode, msg=p.msgText,
                                     time_error=time_err)

            else:
                raise TCSintError("Different reply than CA or CE!")

        except Exception, e:
            self.cmd_error(e, seq_num, tag)
            #raise e

    # This is called when we have an error anywhere in the process of
    # sending a command to the telescope.
    #
    def cmd_error(self, e, seq_num, tag):
        # Log the exception that led to us being called
        msg = str(e)
        self.logger.error(msg)

        # Signal to any waiters on this command that we are done
        if tag:
            self.minimon.setvals(self.monchannels, tag, msg=msg,
                                 time_done=time.time(), result=-1,
                                 done=True)

            # Delete our reference to the cmdb so as not to leak memory
            self.del_trans(seq_num, tag)


class TCSsim(TCSint):

    def __init__(self, tcshost, 
                 ev_quit, logger, minimon, threadPool,
                 prog_send=0x20000011, prog_recv=0x20000012,
                 myhost=None, myport=None, seq_num=None,
                 telcmdDict=None, telackDict=None):
        super(TCSsim, self).__init__(tcshost, ev_quit, logger, minimon,
                                     threadPool,
                                     prog_send=prog_recv, prog_recv=prog_send,
                                     myhost=myhost, myport=myport,
                                     seq_num=seq_num, telcmdDict=telcmdDict,
                                     telackDict=telackDict)


    def recv_reply(self, data):
        # call back with CA then CE
        try:
            h, p = self.packetParser.parse(data)
            self.logger.debug(h.format())
            self.logger.debug(p.format())

            # Get new receipt number for this transaction
            receiptNum = self.seq_num.bump()

            timeEstimateSec = 10.0
            timeFuture = time.time() + timeEstimateSec

            #projectedCompletionTime = datetime.datetime.utcnow()
            projectedCompletionTime = datetime.datetime.fromtimestamp(
                timeFuture)

            # Make the ACK call
            with self.lock:
                if not self.client:
                    self.make_client(self.tcshost)

                try:
                    res = self.client.ack(p.seqNum, p.commandId,
                                          receiptNum, projectedCompletionTime)

                except Exception, e:
                    self.logger.warn("Client call error (possible stale client), resetting client...")
                    self.make_client(self.tcshost)

                    # Try one more time...best effort
                    try:
                        res = self.client.ack(p.seqNum, p.commandId,
                                              receiptNum, projectedCompletionTime)
                    except Exception, e:
                        self.client = None
                        raise TCSintError("rpc error sending CD command: %s" % str(e))
                
            
            task = Task.FuncTask(self.recv_complete,
                                 [p, receiptNum, timeEstimateSec], {})
            task.init_and_start(self)

            return ro.OK

        except Exception, e:
            message = 'Command failed with error %s' % str(e)
            self.logger.error(message)

                
    def recv_complete(self, p, receiptNum, timeEstimateSec):
        try:
            # success return code
            resultCode = 'COMPLETE'
            # ?? binary data
            resultInfo = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

            #time.sleep(timeEstimateSec)

            # Make the END call
            with self.lock:
                if not self.client:
                    self.make_client(self.tcshost)

                try:
                    res = self.client.complete(p.seqNum, p.commandId,
                                               receiptNum, resultCode,
                                               resultInfo)

                except Exception, e:
                    self.logger.warn("Client call error (possible stale client), resetting client...")
                    self.make_client(self.tcshost)

                    # Try one more time...best effort
                    try:
                        res = self.client.complete(p.seqNum, p.commandId,
                                                   receiptNum, resultCode,
                                                   resultInfo)
                    except Exception, e:
                        self.client = None
                        raise TCSintError("rpc error sending CD command: %s" % str(e))
                
                return ro.OK

        except Exception, e:
            message = 'Command failed with error %s' % str(e)
            self.logger.error(message)

        
class RemoteTCSint(ro.remoteObjectServer):
    '''
    Wrapper to the TCSint class to provide remote interface.
    '''
    def __init__(self, 
                 mySvcName, tcsint, logger=None, port=None,
                 usethread=False, uid=UID, gid=GID, sender='OCS',
                 threadPool=None):

        self.tcsint = tcsint

        # For generating unique tags
        self.seq_num = SOSSrpc.rpcSequenceNumber(0)

        # Can also be "OBS", "CIAX", "CXWS"
        self.sender = sender

        self.uid = uid
        self.gid = gid
        
        ro.remoteObjectServer.__init__(self, 
                                       svcname=mySvcName,
                                       usethread=usethread,
                                       port=port,
                                       logger=logger,
                                       threadPool=threadPool)

    def safetyLockOn(self):
        self.tcsint.safetyLockOn()
        return ro.OK
        
    def safetyLockOff(self):
        self.tcsint.safetyLockOff()
        return ro.OK
        
    def safetyLockSetP(self):
        return self.tcsint.safetyLockSetP()
        
    def setWaitAck(self, bool):
        self.tcsint.setWaitAck(bool)
        return ro.OK
        
    def setSubTrack(self, bool):
        self.tcsint.setSubTrack(bool)
        return ro.OK
        
    def setSender(self, who):
        self.sender = who.upper()
        return ro.OK
        

    def send_native_cmd(self, tag, command):
        try:
            self.tcsint.start_cmd(tag, command, sender=self.sender,
                                 uid=self.uid, gid=self.gid)

        except Exception, e:
            self.logger.error('Error in the sendNativeCommand() method')
            self.logger.error(e)
            # TODO set error message to self.minimon
            return ro.ERROR

        return ro.OK

    def sendNativeCommandAs(self, tag, command, uid, gid, sender):
        try:
            self.tcsint.start_cmd(tag, command, uid=uid, gid=gid, sender=sender)

        except Exception, e:
            self.logger.error('Error in the sendNativeCommandAs() method')
            self.logger.error(e)
            # TODO set error message to self.minimon
            return ro.ERROR

        return ro.OK

    def send_cmds(self, tag, cmd_str, cmd_list):
        try:
            self.tcsint.start_cmds(tag, cmd_str, cmd_list,
                                   uid=self.uid, gid=self.gid,
                                   sender=self.sender)

        except Exception, e:
            self.logger.error('Error in the start_cmds() method')
            self.logger.error(e)
            # TODO set error message to self.minimon
            return ro.ERROR

        return ro.OK

    def login(self, tag):
        #cmd_str = '1A1901naoj NAOJ dummyUnit dummyMenu dummyMessage'
        cmd_str = '1A1901pleiades Alcy/One dummyUnit dummyMenu dummyMessage'

        return self.sendNativeCommandAs(tag, cmd_str, 0, 0, self.sender)

    def login_OBS(self, tag):
        #cmd_str = '1A1901naoj NAOJ dummyUnit dummyMenu dummyMessage'
        cmd_str = '1A1901pleiades Alcy/One dummyUnit dummyMenu dummyMessage'

        return self.sendNativeCommandAs(tag, cmd_str, 0, 0, 'OBS')

    def login_naoj(self, tag):
        cmd_str = '1A1901naoj NAOJ dummyUnit dummyMenu dummyMessage'

        return self.sendNativeCommandAs(tag, cmd_str, 0, 0, self.sender)

    def logout(self, tag):
        cmd_str = '1A1902'

        return self.sendNativeCommandAs(tag, cmd_str, UID, GID, self.sender)

    def logout_00(self, tag):
        cmd_str = '1A1902'

        return self.sendNativeCommandAs(tag, cmd_str, 0, 0, self.sender)

    def logout_OBS(self, tag):
        cmd_str = '1A1902'

        return self.sendNativeCommandAs(tag, cmd_str, UID, GID, 'OBS')

    def OBSpri(self, tag):
        cmd_str = '1A1008OBSPRI%%'

        return self.sendNativeCommandAs(tag, cmd_str, UID, GID, self.sender)

    def OBSpri_OBS(self, tag):
        cmd_str = '1A1008OBSPRI%%'

        return self.sendNativeCommandAs(tag, cmd_str, UID, GID, 'OBS')

    def TSCpri(self, tag):
        cmd_str = '1A1008TSCPRI%%'

        return self.sendNativeCommandAs(tag, cmd_str, UID, GID, self.sender)

    def statusOn(self, tag):
        cmd_str = '1A1011'

        return self.sendNativeCommandAs(tag, cmd_str, 0, 0, self.sender)

    def tsc_login(self):
        """This is an all-in-one login/send status command.
        """
        tag = 'login_%d' % self.seq_num.bump()
        res = self.login(tag)
        if res != ro.OK:
            return res

        time.sleep(1.0)

        tag = 'statusOn_%d' % self.seq_num.bump()
        res = self.statusOn(tag)

        return res

    def tsc_logout(self):
        """This is an all-in-one logout command.
        """
        tag = 'logout_%d' % self.seq_num.bump()
        res = self.logout(tag)

        return res

    def tsc_obspri(self):
        tag = 'obspri_%d' % self.seq_num.bump()
        res = self.OBSpri(tag)

        return res

    def tsc_tscpri(self):
        tag = 'tscpri_%d' % self.seq_num.bump()
        res = self.TSCpri(tag)

        return res

    def tsc_statusOn(self):
        tag = 'statusOn_%d' % self.seq_num.bump()
        res = self.statusOn(tag)

        return res



def main(options, args):

    svcname = options.svcname
    monchannels = ['TCSint0']
    
    # Configure top level logger.
    logger = ssdlog.make_logger(svcname, options)

    # Initialize remote objects subsystem.
    try:
        ro.init()

    except ro.remoteObjectError, e:
        logger.error("Error initializing remote objects subsystem: %s" % str(e))
        sys.exit(1)

    ev_quit = threading.Event()

    threadPool = None
    minimon = None
    tcsint = None
    ro_int = None

    def quit():
        logger.info("Shutting down telescope interface...")
        if ro_int:
            ro_int.ro_stop(wait=True)
        if tcsint:
            tcsint.stop(wait=True)
        if minimon:
            #minimon.releaseAll()
            minimon.stop(wait=True)
        if threadPool:
            threadPool.stopall(wait=True)

    def SigHandler(signum, frame):
        """Signal handler for all unexpected conditions."""
        logger.error('Received signal %d' % signum)
        quit()
        ev_quit.set()

    # Set signal handler for signals
    #signal.signal(signal.SIGINT, SigHandler)
    signal.signal(signal.SIGTERM, SigHandler)

    threadPool = Task.ThreadPool(logger=logger,
                                 ev_quit=ev_quit,
                                 numthreads=options.numthreads)
    # TCSint monitor interface
    minimon = Monitor.Minimon('%s.mon' % options.svcname, logger,
                              threadPool=threadPool)

    # publish our results to the specified monitor
    if options.monitor:
        minimon.publish_to(options.monitor, ['TCSint0', 'errors'], {})

    # Configure logger for logging via our monitor
    if options.logmon:
        minimon.logmon(logger, options.logmon, ['logs'])

    klass = TCSint
    if options.simulate:
        klass = TCSsim
    tcsint = klass(options.tcshost, ev_quit, logger, minimon,
                   threadPool, telcmdDict=telcmds.telcmds,
                   telackDict=telcmds.telacks)

    remote_int = RemoteTCSint(svcname, tcsint, port=options.port,
                              logger=logger, sender=options.sender,
                              uid=options.uid, gid=options.gid,
                              threadPool=threadPool)

    logger.info("Starting telescope interface...")
    try:
        threadPool.startall(wait=True)

        minimon.start(wait=True)

        tcsint.start(wait=True)

        try:
            remote_int.ro_start(wait=True)

        except KeyboardInterrupt:
            logger.error("Caught keyboard interrupt!")
            remote_int = None

    finally:
        quit()

    logger.info("Program should terminate")


if __name__ == '__main__':

    from optparse import OptionParser
    import sys
    optprs = OptionParser()

    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--gid", dest="gid", type="int",
                      default=8,
                      help="Use GID in RPC packets", metavar="GID")
    optprs.add_option("-m", "--monitor", dest="monitor", 
                      default="monitor", metavar="NAME",
                      help="Reflect internal status to monitor service NAME")
    optprs.add_option("--numthreads", dest="numthreads", type="int",
                      default=100,
                      help="Use NUM threads", metavar="NUM")
    optprs.add_option("--obsprognum", dest="obsprognum", metavar="NUM",
                      type="int", default=0x20000012,
                      help="Use ProgNum as the OBS RPC program number")
    optprs.add_option("--port", dest="port", type="int",
                      default=None,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--sim", dest="simulate", action="store_true",
                      default=False,
                      help="Run as a simulator")
    optprs.add_option("--sender", dest="sender", default='OCS',
                      help="Use SENDER in RPC packets", metavar="SENDER")
    optprs.add_option("--svcname", dest="svcname", metavar="NAME",
                      default = "TCSint0", 
                      help="Register using NAME as service name")
    optprs.add_option("--tcshost", dest="tcshost", metavar="HOST",
                      default = 'localhost',
                      help="Use HOST as the TCS host")
    optprs.add_option("--tcsprognum", dest="tcsprognum", metavar="NUM",
                      type="int", default=0x20000011,
                      help="Use ProgNum as the TCS RPC program number")
    optprs.add_option("--uid", dest="uid", type="int",
                      default=3,
                      help="Use UID in RPC packets", metavar="UID")
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
       

# END TCSint2.py

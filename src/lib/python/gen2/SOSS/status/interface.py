#!/usr/bin/env python
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Mar 16 14:34:10 HST 2012
#]
# Bruce Bon (bruce.bon@subarutelescope.org)
#
#
# remove once we're certified on python 2.6
from __future__ import with_statement

import sys, re, time, os
import signal
import threading, Queue
# profile imported below (if needed)
# pdb imported below (if needed)
# optparse imported below (if needed)

from Bunch import Bunch
import Task
import remoteObjects as ro
import remoteObjects.Monitor as Monitor
import SOSS.SOSSrpc as SOSSrpc
import SOSS_status
import common, Convert
import logging, ssdlog
import Task

# For Receiving TCS status
#    constants file not necessary and causes FutureWarning
#from TCSLconstants import *
#from TCSSconstants import *
#from TCSVconstants import *

from TCSLtypes import *
from TCSStypes import *
from TCSVtypes import *

import TCSLpacker
import TCSSpacker
import TCSVpacker

# For responding to ScreenGet requests
#import OSSC_ScreenGetconstants
import OSSC_ScreenGetpacker
import OSSC_ScreenGettypes


# Version/release number
version = "20120316.0"

tblsize = 1292
# subtable table: offset
TSCLsubTables = { 'L1': 0 * tblsize,
                  'L2': 1 * tblsize,
                  'L3': 2 * tblsize,
                  'L4': 3 * tblsize,
                  'L5': 4 * tblsize,
                  'L6': 5 * tblsize,
                  'L7': 6 * tblsize,
                  }

tableIntervals = {
    'TSCS': { 'rate': 0.1 },
    'TSCL': { 'rate': 1.0 },
    'TSCV': { 'rate': 1.0 },
    'DAQgetRpc': { 'rate': 0.1 },
    }


class statusReceiveError(common.statusError):
    pass

class statusRequestError(common.statusError):
    pass


class TSCSstatusRpcServer(SOSSrpc.UDP_rpcServer):
    
    def addpackers(self):
        self.packer   = TCSSpacker.TCSSPacker()
        self.unpacker = TCSSpacker.TCSSUnpacker('')

    def handle_1(self):

        try:
            #rpcstr = self.unpacker.get_buffer()
            data = self.unpacker.unpack_broadcastForm()
            rpcmsg = SOSSrpc.TCSstatRpcMsg(rpcmsg=data)

            # Process rpc message
            #self.func((rpcmsg, data))
            self.func((rpcmsg, data.contents))

            self.turn_around()
            
        except rpc.RPCUnextractedData:
            self.logger.error("*** Unextracted Data in request!")

        except Exception, e:
            self.logger.error("Error processing RPC packet: %s" % (
                    str(e)))


class TSCLstatusRpcServer(SOSSrpc.UDP_rpcServer):
    
    def addpackers(self):
        self.packer   = TCSLpacker.TCSLPacker()
        self.unpacker = TCSLpacker.TCSLUnpacker('')

    def handle_1(self):

        try:
            #rpcstr = self.unpacker.get_buffer()
            data = self.unpacker.unpack_broadcastForm()
            rpcmsg = SOSSrpc.TCSstatRpcMsg(rpcmsg=data)

            # Process rpc message
            #self.func((rpcmsg, data))
            self.func((rpcmsg, data.contents))

            self.turn_around()
            
        except rpc.RPCUnextractedData:
            self.logger.error("*** Unextracted Data in request!")

        except Exception, e:
            self.logger.error("Error processing RPC packet: %s" % (
                    str(e)))


class TSCVstatusRpcServer(SOSSrpc.TCP_rpcServer):
    
    def addpackers(self):
        self.packer   = TCSVpacker.TCSVPacker()
        self.unpacker = TCSVpacker.TCSVUnpacker('')

    def handle_1(self):

        # Process rpc message
        res = False
        try:
            data = self.unpacker.unpack_FM_NetForm()
            rpcmsg = SOSSrpc.TCSstatRpcMsg(rpcmsg=data)

            self.func((rpcmsg, data))

            self.turn_around()
            
            res = True
            
        except rpc.RPCUnextractedData:
            self.logger.error("*** Unextracted Data in request!")

        except Exception, e:
            self.logger.error("Exception raised processing RPC packet: %s" % (
                str(e)))

        # Return confirmation result
        self.packer.pack_bool(res)


class SOSSstatusRpcServer(SOSSrpc.SOSS_rpcServer):

    def handle_1(self):

        # Process rpc message
        res = False
        try:
            data = self.unpacker.unpack_ComCDarg()
            rpcmsg = SOSSrpc.SOSScmdRpcMsg(rpcmsg=data)

            if self.logger:
                self.logger.info(data)
        
            self.func((rpcmsg, data))

            self.turn_around()
            
            res = True
            
        except rpc.RPCUnextractedData:
            self.logger.error("*** Unextracted Data in request!")

        except Exception, e:
            self.logger.error("Exception raised processing RPC packet: %s" % (
                str(e)))

        # Return confirmation result
        self.packer.pack_bool(res)


class ScreenGetRpcServer(SOSSrpc.TCP_rpcServer):

    def set_statusObj(self, statusObj):
        self.statusObj = statusObj
        
    def addpackers(self):
        self.packer   = OSSC_ScreenGetpacker.OSSC_SCREENGETPacker()
        self.unpacker = OSSC_ScreenGetpacker.OSSC_SCREENGETUnpacker('')

    def handle_1(self):

        try:
            data = self.unpacker.unpack_ScreenGetArgs()

            tabledef = data.tabledef
            offset = int(data.start)
            length = int(data.size)

            self.turn_around()
            
        except rpc.RPCUnextractedData:
            self.logger.error("*** Unextracted Data in request!")

        except Exception, e:
            self.logger.error("Exception raised processing RPC packet: %s" % (
                str(e)))
            return

        parts = tabledef.split(',')
        try:
            tablename = parts[2].strip().upper()
            self.logger.debug("Received request: table=%s offset=%d length=%d" % (
                tablename, offset, length))

            res = self.statusObj.get_subTable(tablename, offset, length)
            
        except (IndexError, ValueError), e:
            self.logger.error("Bad tabledef (%s) resulted in error: %s" % (
                tabledef, str(e)))
            res = ('#ERROR: %s #' % str(e))

        except (common.statusError), e:
            self.logger.error("Status error: %s" % (str(e)))
            res = ('#ERROR: %s #' % str(e))

        # Return result
        self.packer.pack_string(res)


class DAQGetRpcServer(SOSSrpc.SOSS_rpcServer):

    def handle_1(self):

        # Process rpc message
        res = False
        try:
            data = self.unpacker.unpack_ComCDarg()
            rpcmsg = SOSSrpc.SOSScmdRpcMsg(rpcmsg=data)

            if self.logger:
                self.logger.info(data)
        
            self.func((rpcmsg, data))

            self.turn_around()
            
            res = True
            
        except rpc.RPCUnextractedData:
            self.logger.error("*** Unextracted Data in request!")

        except Exception, e:
            self.logger.error("Exception raised processing RPC packet: %s" % (
                str(e)))

        # Return confirmation result
        self.packer.pack_bool(res)


class StatusReceiver(object):

    def __init__(self, logger, statusObj, threadPool, ev_quit=None,
                 myhost=None, monchannels=[], loghome=None):
        self.recvTSCTasker = self.processRpcMsgTasker(self.processTCSstatRpcMsg)
        self.recvSOSSTasker = self.processRpcMsgTasker(self.processSOSSstatRpcMsg)
        self.recvDAQTasker = self.processRpcMsgTasker(self.processDAQgetRpcMsg)

        self.statusObj = statusObj
        self.num_SOSSmonunits = 5
        self.num_TSCmonunits  = 1
        self.TSCmonunit = {}
        self.SOSSmonunit = {}
        self.ScreenGet = {}
        self.statusInfo = Convert.statusInfo(version=2)

        # For TSC status logging
        self.loghome = loghome
        self.tsclog = {}
        self.tsclog_lock = threading.RLock()
        self.tsclog_hr = 0

        self.logger = logger
        self.monitor = None
        self.threadPool = threadPool
        self.monchannels = monchannels
        if ev_quit:
            self.ev_quit = ev_quit
        else:
            self.ev_quit = threading.Event()
        self.timeout = 0.1
        self.qtask = None
        self.taskqueue = Queue.Queue()

        # For handling updates to the monitor
        self.monUpdateInterval = 1.0
        self.monUpdateSet = set([])
        self.monUpdateLock = threading.RLock()

        # For DAQ status request handing
        self.hostfilter = None
        self.hostfilter_lock = threading.RLock()
        if not myhost:
            myhost = SOSSrpc.get_myhost(short=True)
        self.myhost = myhost
        self.seq_num = SOSSrpc.rpcSequenceNumber()
        self.clients = {}
        self.client_lock = threading.RLock()

        # For task inheritance:
        self.tag = 'StatusReceiver'
        self.shares = ['logger', 'ev_quit', 'timeout', 'threadPool',
                       'monitor']


    def set_monitor(self, monitor):
        self.monitor = monitor
        
    def set_server(self, server):
        self.server = server
        
    def get_threadPool(self):
        return self.threadPool
        
    def start(self, wait=True, timeout=None, usethread=False):

        # Start thread pool
        self.threadPool.startall(wait=True)
        
        # Initialize the task queue processing task.
        t = Task.QueueTaskset(self.taskqueue, waitflag=False)
        self.qtask = t
        t.init_and_start(self)

        self.cycleTSCstatusLogs()

        # Start TSC receivers
        for stype in ('TSCS', 'TSCL', 'TSCV'):
            for i in xrange(self.num_TSCmonunits):
                server = self.make_TSCmonunit(stype, i)
                self.TSCmonunit[(stype,i)] = server
                t = Task.FuncTask(server.start, [],
                                  {'usethread': False})
                self.taskqueue.put(t)
                server.wait_start(timeout=timeout)

        # Start SOSS receivers
        for i in xrange(1, self.num_SOSSmonunits):
            server = self.make_SOSSmonunit(i)
            self.TSCmonunit[i] = server
            t = Task.FuncTask(server.start, [],
                              {'usethread': False})
            self.taskqueue.put(t)
            if wait:
                server.wait_start(timeout=timeout)

        # Start DAQ GetRpc service
        server = self.make_DAQGetRpc()
        self.DAQgetRpc = server
        t = Task.FuncTask(server.start, [],
                          {'usethread': False})
        self.taskqueue.put(t)
        if wait:
            server.wait_start(timeout=timeout)
        
        # Start ScreenGet service
        server = self.make_ScreenGet(0)
        server.set_statusObj(self.statusObj)
        self.ScreenGet[0] = server
        t = Task.FuncTask(server.start, [],
                          {'usethread': False})
        self.taskqueue.put(t)
        if wait:
            server.wait_start(timeout=timeout)

        # Start monitor notifier
        t = Task.FuncTask(self.monloop, [], {})
        self.taskqueue.put(t)

    def stop(self, wait=True):

        # Stop ScreenGets
        for key in self.ScreenGet.keys():
            self.ScreenGet[key].stop(wait=True)

        # Stop TSC receivers
        for key in self.TSCmonunit.keys():
            self.TSCmonunit[key].stop(wait=True)

        # Close TSC status logs
        for pkttype in ('S', 'L', 'V'):
            self.tsclog[pkttype].fd.close()

        # Stop SOSS receivers
        for key in self.SOSSmonunit.keys():
            self.SOSSmonunit[key].stop(wait=True)

        # Stop DAQ GetRpc service
        self.DAQgetRpc.stop(wait=True)
        
        # Stop queue task
        self.qtask.stop()

        # Stop thread pool
        self.threadPool.stopall(wait=wait)
        

    def make_TSCmonunit(self, stype, unitnum):
        try:
            key = ('%s%d->' % (stype, unitnum))
            bnch = SOSSrpc.lookup_rpcsvc(key)

            rpcKlassDict = {'TSCS': TSCSstatusRpcServer,
                            'TSCL': TSCLstatusRpcServer,
                            'TSCV': TSCVstatusRpcServer,
                            }
            klass = rpcKlassDict[stype]
            
        except KeyError:
            raise statusReceiveError("Error creating rpc server: no such key '%s'" % \
                              key)
        
        prognum = bnch.server_receive_prgnum

        server = klass(prognum, ev_quit=self.ev_quit,
                       logger=self.logger,
                       queue=self.taskqueue,
                       func=self.recvTSCTasker)
        return server
        

    def make_SOSSmonunit(self, unitnum):
        try:
            key = ('toOBS%d(sdst)' % (unitnum))
            bnch = SOSSrpc.lookup_rpcsvc(key)

        except KeyError:
            raise statusReceiveError("Error creating rpc server: no such key '%s'" % \
                              key)
        
        prognum = bnch.server_receive_prgnum
        
        server = SOSSstatusRpcServer(prognum, ev_quit=self.ev_quit,
                                     logger=self.logger,
                                     queue=self.taskqueue,
                                     func=self.recvSOSSTasker)
        return server
        

    def make_DAQGetRpc(self):
        try:
            key = 'OBCPtoOBS(sreq)'
            bnch = SOSSrpc.lookup_rpcsvc(key)

        except KeyError:
            raise statusReceiveError("Error creating rpc server: no such key '%s'" % \
                              key)
        
        prognum = bnch.server_receive_prgnum
        
        server = DAQGetRpcServer(prognum, ev_quit=self.ev_quit,
                                 logger=self.logger,
                                 queue=self.taskqueue,
                                 func=self.recvDAQTasker)
        return server
        

    def make_ScreenGet(self, unitnum):
        try:
            #key = ('ScreenGetOBS' % (unitnum))
            # Unitnum ignored for now
            key = ('ScreenGetOBS')
            bnch = SOSSrpc.lookup_rpcsvc(key)

        except KeyError:
            raise statusReceiveError("Error creating rpc server: no such key '%s'" % \
                              key)
        
        prognum = bnch.server_receive_prgnum
        
        server = ScreenGetRpcServer(prognum, ev_quit=self.ev_quit,
                                    logger=self.logger,
                                    queue=self.taskqueue,
                                    func=self.recvSOSSTasker)
        return server
        

    def lookup_TSCLoffset(self, subTabId):

        return TSCLsubTables[subTabId]
    

    def lookup_TSCVoffset(self, subTabId):

        self.logger.debug("Looking up TSCV offset using key '%s'" % subTabId)
        tscvdef = self.statusInfo.get_TSCVDef(subTabId)

        return (tscvdef.offset, tscvdef.length)


    def cycleTSCstatusLogs(self):

        if not self.loghome:
            return

        with self.tsclog_lock:
            # Get current time
            cur_time = time.time()
            (yr, mo, da, hr, min, sec, wday, yday, isdst) = time.localtime(cur_time)
            # yuck--hard-coded reset hour to 8 or 17
            if (hr >= 8) and (hr < 17):
                hr = 8
            else:
                # If after midnight, reset to the day before
                if hr < 8:
                    cur_time -= 86400
                    (yr, mo, da, hr, min, sec, wday, yday, isdst) = time.localtime(cur_time)
                hr = 17

            logspec = ('%s/cuts/TSC%%s-%4.4d%02.2d%02.2d-%02.2d.pkt' % (self.loghome, yr, mo, da, hr))
            self.tsclog_hr = hr

            # For writing TSC status logs
            for pkttype in ('S', 'L', 'V'):
                try:
                    self.tsclog[pkttype].fd.close()

                except KeyError:
                    # first time
                    self.tsclog[pkttype] = Bunch(lock=threading.Lock())

                except Exception, e:
                    self.logger.error("Error closing previous log file for TSC%s: %s" % (
                            pkttype, str(e)))
                
                self.tsclog[pkttype].fd = open(logspec % (pkttype), 'a')


    def logTSCstatus(self, pkttype, data, recsize):

        if not self.loghome:
            return

        # Pad data (with nulls) to length of desired record size
        # (feature requested by Daigo Tomono)
        length = len(data)
        if length < recsize:
            data = data + ('\x00' * (recsize - length))

        with self.tsclog_lock:
            # Get current time
            (yr, mo, da, hr, min, sec, wday, yday, isdst) = time.localtime()
            if hr in (8, 17) and (self.tsclog_hr != hr):
                self.cycleTSCstatusLogs()

        with self.tsclog[pkttype].lock:
            self.tsclog[pkttype].fd.write(data)
            #self.tsclog[pkttype].fd.flush()
        

    def processTCSstatRpcMsg(self, rpcpair):

        (rpcmsg, rpcstr) = rpcpair
        
        data = rpcmsg.payload
        lenData = rpcmsg.len_payload
        
        if rpcmsg.msg_type != 'MO':
            raise statusReceiveError("Unknown TCS status packet type: '%s'" % (
                subTabId))

        updtime = time.time()
        
        if data[0] == 'S':
            # TSCS packet data can be put straight in
            self.logger.debug("Putting to status table (S)")
            tblData = rpcstr
            tblName = 'TSCS'
            self.statusObj.put_table(tblName, tblData)

            # log status packet for TSC dumps and analysis
            self.logTSCstatus('S', rpcstr, tblsize)

        elif data[0] == 'L':
            # log status packet for TSC dumps and analysis
            self.logTSCstatus('L', rpcstr, tblsize)

            # TSCL packet data is put in as a subrange
            subTabId = data[0:2]
            try:
                offset = self.lookup_TSCLoffset(subTabId)

                self.logger.debug("Putting to status table (L(%d))" % offset)
                tblData = rpcstr
                tblName = 'TSCL'
                self.statusObj.put_subTable(tblName, tblData, offset)

            except KeyError:
                raise statusReceiveError("Unknown TCSL packet subtype: '%s'" % subTabId)

        elif data[0] == 'E':
            # log status packet for TSC dumps and analysis
            self.logTSCstatus('V', rpcstr, 8192)

            tblName = 'TSCV'
            # First insert RPC header into root of table; this is needed by programs
            # that dump the status logs
            tblData = rpcstr[:rpcmsg.len_hdr+1]
            self.statusObj.put_subTable(tblName, tblData, 0)

            # TSCV packet data is put in as a subrange
            sdsNdx = 1
            #while (sdsNdx + 20) < lenData:
            while sdsNdx < lenData:
                devId     = data[sdsNdx:sdsNdx+4]
                devIdTime = data[sdsNdx+4:sdsNdx+19]
                self.logger.debug("SDS devId=%s devIdTime=%s" % (devId,
                                                                 devIdTime))
                subTabId = 'TSCV%s' % devId
                try:
                    (offset, sdsLen) = self.lookup_TSCVoffset(subTabId)

                    tblData = data[sdsNdx: sdsNdx+sdsLen]
                    
                    self.logger.debug("Putting to status table (V)")
                    self.statusObj.put_subTable(tblName, tblData, offset)
                    
                except Convert.statusInfoError:
                    #raise statusReceiveError("Unknown TCSV device id: '%s'" % devId)
                    self.logger.error("Unknown TCSV device id: '%s' -- stopping packet processing" % devId)
                    break

                sdsNdx += sdsLen

        else:
            raise statusReceiveError("Unknown TCS status payload type: '%s'" % (
                data[0]))

        # Record the time we received this table
        self.server.store({'GEN2.STATUS.TBLTIME.%s' % tblName: updtime})
        
        return tblName
        

    def get_client(self, host):

        host = host.lower()
        
        with self.client_lock:

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
        
            
    def processSOSSstatRpcMsg(self, rpcpair):

        (rpcmsg, rpcstr) = rpcpair
        
        # Validate packet format
        if rpcmsg.msg_type != 'SD':
            raise statusReceiveError("rpc msg is not a SOSS SD packet")

        try:
            data = rpcmsg.unpack_sd()

        except SOSSrpc.rpcMsgError, e:
            raise statusReceiveError("SOSS RPC payload format error: %s" % str(e))

        updtime = time.time()
        
        # Send status table to status system
        tblName  = data.tablename.strip()
        #statusdata = data.statusdata

        self.logger.info("Putting to status table (%s)" % (
            tblName))
        self.statusObj.put_table(tblName, rpcstr)

        # Record the time we received this table
        self.server.store({'GEN2.STATUS.TBLTIME.%s' % tblName: updtime})
        
        return tblName


    def processDAQgetRpcMsg(self, rpcpair):

        (rpcmsg, rpcstr) = rpcpair
        
        if rpcmsg.msg_type != 'CD':
            raise statusRequestError("rpc msg is not a SOSS CD request")

        # Optional host filtering--drop the packet if it comes from a
        # host that we haven't explicitly allowed
        sender = rpcmsg.sender.lower()
        with self.hostfilter_lock:
            if (self.hostfilter != None) and (not self.hostfilter.has_key(sender)):
                self.logger.warn("Host '%s' not in filter list--dropping packet" % \
                                 sender)
                return

        try:
            data = rpcmsg.unpack_cd()

        except SOSSrpc.rpcMsgError, e:
            raise statusRequestError("SOSS RPC payload format error: %s" % str(e))

        # Format of command should be STATUS,ALIAS,ALIAS,...
        try:
            (cmd, aliases) = data.cmdstr.split(',')
            if cmd != 'STATUS':
                raise statusRequestError("Status request command format error: '%s'" % rpcmsg.payload)
            
        except (ValueError, TypeError), e:
            raise statusRequestError("Status request command format error: '%s'" % rpcmsg.payload)
            
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
            raise statusRequestError("rpc error sending AB reply: %s" % str(e))
        
        # Get the requested status from the status server
        aliases = aliases.replace('$', '').split()

        # Actually fetch the status values from status system
        status = 0
        result = 'COMPLETE'
        try:
            # Get requested values from the statusObj
            fetchDict = self.server.fetchList2Dict(aliases)

            # Log request
            self.logger.info("request from %s: %s" % (sender, str(fetchDict)))
                
            # Now pack data up for return trip
            data = []
            for alias in aliases:
                try:
                    val = fetchDict[alias]
                    if isinstance(val, float):
                        # "G" form of conversion forces upper case "E"
                        # in scientific notation--required for STARS and
                        # most instruments just stuff status value directly
                        # into the FITS header
                        val = '%G' % val
                    else:
                        val = str(val).strip()

                    # Check if value needs to be quoted
                    # cases: blank, or contains spaces or commas
                    if ((' ' in val) or (',' in val) or (len(val) == 0)) \
                            and not val.startswith('"'):
                        val = '"' + val + '"'

                    # The DAQ interface spec says that values in the return
                    # packet are whitespace separated, but some older 
                    # instruments seem to rely on fixed width items
                    # TODO: double-check this and remove if possible
                    #data.append(val)
                    data.append('%-64.64s' % val)

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
        # Q: seq number here may be >1 above the previous one...will
        # DAQtk complain about that at the other end?
        rpcbuf.pack_en(rpcmsg.seq_num, status, result,
                       seq_num=self.seq_num.bump())
        try:
            res = rpcconn.callrpc(rpcbuf)

        except SOSSrpc.rpcClientError, e:
            raise statusRequestError("rpc error sending EN reply: %s" % str(e))

        self.logger.debug("Processed status request successfully!")

        return 'DAQgetRpc'


    def processRpcMsg(self, fn, rpcpair):

        try:
            start_time = time.time()
            
            tblName = fn(rpcpair)

            if tblName != 'DAQgetRpc':
                # Notify interested parties via monitor
                self.notify(tblName)
            
            stop_time = time.time()
            delta = stop_time - start_time
            
            self.logger.debug("%s packet processing time was %5.3f sec" % (
                tblName, delta))

            return tblName

        except Exception, e:
            self.logger.error("Error processing RPC packet: %s" % str(e))


    def processRpcMsgTasker(self, fn):

        def tasker(rpcpair):
            start_time = time.time()
            
            #self.taskqueue.put(Task.FuncTask(self.processRpcMsg,
            #                                 (fn, rpcpair), {}))
            tblName = self.processRpcMsg(fn, rpcpair)
            
            stop_time = time.time()
            delta = stop_time - start_time

            self.logger.debug("%s packet turnaround time was %5.3f sec" % (
                tblName, delta))

            # Check turnaround time against maximum limits
            try:
                maxtime = tableIntervals[tblName]['rate']
            except KeyError:
                maxtime = 1.0

            if delta > maxtime:
                self.logger.warn("%s packet turnaround time of %5.3f sec exceeds maximum (%5.3f) for this table" % (
                    tblName, delta, maxtime))

        return tasker


    def notify(self, tblName):
        self.monUpdateLock.acquire()
        try:
            self.monUpdateSet.add(tblName)

        finally:
            self.monUpdateLock.release()


    def add_hostfilter(self, hostname):
        with self.hostfilter_lock:
            if self.hostfilter == None:
                self.hostfilter = {}

            self.hostfilter[hostname] = None
            
    def del_hostfilter(self, hostname):
        with self.hostfilter_lock:
            if self.hostfilter == None:
                return
            try:
                del self.hostfilter[hostname]
            except KeyError:
                pass
            
    def monloop(self):
        while not self.ev_quit.isSet():
            self.monUpdateLock.acquire()
            try:
                tables = list(self.monUpdateSet)
                self.monUpdateSet = set([])

            finally:
                self.monUpdateLock.release()

            for tblName in tables:
                tag = ("mon.statint.%s" % tblName)
                # TODO: race condition for self.monitor?
                if self.monitor:
                    self.monitor.setvals(self.monchannels, tag,
                                         upd_time=time.time())

            self.ev_quit.wait(self.monUpdateInterval)

            
def main(options, args):

    svcname = options.svcname
    logger = ssdlog.make_logger(svcname, options)
    monchannels = ['statint', 'logs']
        
    # Initialize remote objects subsystem.
    try:
        ro.init()

    except ro.remoteObjectError, e:
        logger.error("Error initializing remote objects subsystem: %s" % str(e))
        sys.exit(1)

    # Global termination flag
    ev_quit = threading.Event()
    
    statint = None
    minimon = None
    threadPool = None
    mon_started = False

    def quit():
        logger.info("Shutting down status interface...")
        if statint:
            statint.stop(wait=True)
        if minimon:
            minimon.stop(wait=True)
        if mon_started:
            minimon.stop_server(wait=True)
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

    # Create object in which to store status tables.  This is a passive
    # object; i.e. there are no active threads therein
    statusObj = SOSS_status.storeStatusObj()

    # Create thread pool
    threadPool = Task.ThreadPool(logger=logger,
                                 ev_quit=ev_quit,
                                 numthreads=options.numthreads)
        
    # Create the status interface object
    logger.info("Starting status monitor units...")
    statint = StatusReceiver(logger, statusObj, threadPool,
                             ev_quit=ev_quit,
                             myhost=options.myhost,
                             monchannels=monchannels,
                             loghome=options.loghome)

    # Create our monitor interface
    monSvcName = 'statint.mon'
    minimon = Monitor.Monitor(monSvcName, logger, #ev_quit=ev_quit,
                              threadPool=threadPool)
    statint.set_monitor(minimon)

    try:
        threadPool.startall(wait=True)
        
        minimon.start(wait=True)

        if options.monitor:
            # Subscribe main monitor to our feeds
            minimon.subscribe(options.monitor, monchannels, ())

        logger.info("Press ^C to terminate...")
        try:
            statint.start(wait=True)
            minimon.start_server(wait=True, usethread=False)
            mon_started = True

        except KeyboardInterrupt:
            logger.error("Keyboard interrupt received!")

    finally:
        quit()
        

if __name__ == '__main__':

    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--loghome", dest="loghome", default=None,
                      metavar="DIR",
                      help="Specify DIR for status data logs")
    optprs.add_option("-m", "--monitor", dest="monitor", default=False,
                      metavar="NAME",
                      help="Reflect internal status to monitor service NAME")
    optprs.add_option("--monunit", dest="monunitnum", type="int",
                      default=3, metavar="NUM",
                      help="Target OSSL_MonitorUnit NUM on OBS")
    optprs.add_option("--myhost", dest="myhost", metavar="NAME",
                      help="Use NAME as my hostname for DAQ communication")
    optprs.add_option("--numthreads", dest="numthreads", type="int",
                      default=30,
                      help="Use NUM threads in thread pool", metavar="NUM")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--svcname", dest="svcname",
                      default='statint',
                      help="Use SVCNAME for supplying Gen2 status",
                      metavar="SVCNAME")
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
       
#END

#!/usr/bin/env python
#
# SOSS rpc interface base class
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Jun 14 17:08:17 HST 2012
#]
# Bruce Bon (Bruce.Bon@SubaruTelescope.org)  2006-11-21
#
# The charter of this module is to provide common code and data to support
# SOSS RPC transactions.  The RPC program numbers are gathered here in
# the dictionary, ProgramNumbers.  Utility functions provide program
# number lookup and time <-> timestamp conversions.  Class definitions
# for RPC headers and messages provide containers for message parameters
# and packing/unpacking of the parts of a message, following the format
# developed by Fujitsu for SOSS.  RPC client and server classes provide
# data and methods commonly needed by SOSS interfaces.
# 
# NOTE: see http://ssdweb.naoj.org/info/reference/NetCommTerms.html for
# definition of terms if any of the description below is confusing.
# A "SOSS client" is the host/system that initiates a SOSS transaction 
# by executing an RPC call to a "SOSS server."
#
# The SOSS client SEND RPC program number (ProgNo) is the one used to send 
# the first packet of information to the SOSS server, which receives the 
# packet using the same ProgNo; therefore, the SOSS client SEND ProgNo is
# the same as the SOSS server RCV ProgNo.
#
# The SOSS server SEND ProgNo is the one used to send reply packets 
# (Ack, Completion, etc.), if any, to the SOSS client, which receives them 
# using the same ProgNo; therefore, the SOSS server SEND ProgNo is the same 
# as the SOSS client RCV ProgNo.
#
# Comments at the beginning of the list of ProgramNumbers identify that the
# first column of numbers (ProgramNumbers[key][0]) contains the SOSS client
# SEND ProgNo's; the second column of numbers (ProgramNumbers[key][1]) 
# contains the SOSS client RCV ProgNo's.
#
# Examples:
#    Command transaction from SOSS to OBCP*:
#           SOSS client = OBS, SOSS server = OBCP*
#    Status packets from OBCP* to SOSS:
#           SOSS client = OBCP*, SOSS server = OBS
#    FITS transfer request from OBCP* to SOSS
#           SOSS client = OBCP*, SOSS server = OBS
#    FITS transfer request from SOSS to STARS
#           SOSS client = OBC, SOSS server = STARS*
#
# The source module containing a list of the ProgNo's in the obsolete SOSS 
# code is .../product/OSSC/OSSC_monClnt.d/OSSC_monClnt.c .
#
import os, socket, select, time
import threading, Queue
import random

# Local imports
import rpc
from Bunch import Bunch

# RPC interface includes
# constants file not necessary and causes FutureWarning
#from OSSC_ComCDconstants import *
from OSSC_ComCDtypes import *
import OSSC_ComCDpacker

# RPC program numbers for send/receive messages with external hosts.
ProgramNumbers = {
#                      SEND        RCV  (perspective of SOSS client)
#                      RCV         SEND (perspective of SOSS server)
    'OBStoOSSA0': (0x21010001, 0x21020001),  
    'OBStoOSSA1': (0x21010101, 0x21020101),  
    'OBStoOSSA2': (0x21010201, 0x21020201),  
    'OBStoOSSA3': (0x21010301, 0x21020301),  
    'OBStoOSSA4': (0x21010401, 0x21020401),  
    'OBStoOSSA5': (0x21010501, 0x21020501),  
    'OBStoOSSA6': (0x21010601, 0x21020601),  
    'OBStoOSSA7': (0x21010701, 0x21020701),  
    'OBStoOSSA8': (0x21010801, 0x21020801),  
    'OBStoOSSA9': (0x21010901, 0x21020901),  
    'OBStoOSSB0': (0x21010002, 0x21020002),  
    'OBStoOSSB1': (0x21010102, 0x21020102),  
    'OBStoOSSB2': (0x21010202, 0x21020202),  
    'OBStoOSSB3': (0x21010302, 0x21020302),  
    'OBStoOSSB4': (0x21010402, 0x21020402),  
    'OBStoOSSB5': (0x21010502, 0x21020502),  
    'OBStoOSSB6': (0x21010602, 0x21020602),  
    'OBStoOSSB7': (0x21010702, 0x21020702),  
    'OBStoOSSB8': (0x21010802, 0x21020802),  
    'OBStoOSSB9': (0x21010902, 0x21020902),  

    # StatusMonitor units
    'toOBS1(sdst)': (0x21030021, None),  
    'toOBS2(sdst)': (0x21030022, None),
    # (Most obcps send status to monitor unit 3):
    'toOBS3(sdst)': (0x21030023, None),  
    'toOBS4(sdst)': (0x21030024, None),  
    'toOBS5(sdst)': (0x21030025, None),  

    'ScreenGetOBS': (0x21040034, None),
    
#OWS,OBC,VGW,OBCP to OBS
    #
    # "through mode" (not used?)
    'OBCPtoOBS(thru)': (0x21010011, 0x21020011),
    # status request via DAQtk
    'OBCPtoOBS(sreq)': (0x21010012, 0x21020012),  

    # OBS <--> OBCP Command Interface
    'OBStoOBCP1(cmd)': (0x21010103, 0x21020103),  
    'OBStoOBCP2(cmd)': (0x21010203, 0x21020203),  
    'OBStoOBCP3(cmd)': (0x21010303, 0x21020303),  
    'OBStoOBCP4(cmd)': (0x21010403, 0x21020403),  
    'OBStoOBCP5(cmd)': (0x21010503, 0x21020503),  
    'OBStoOBCP6(cmd)': (0x21010603, 0x21020603),  
    'OBStoOBCP7(cmd)': (0x21010703, 0x21020703),  
    'OBStoOBCP8(cmd)': (0x21010803, 0x21020803),  
    'OBStoOBCP9(cmd)': (0x21010903, 0x21020903),  
    'OBStoOBCP10(cmd)': (0x21010a03, 0x21020a03),  
    'OBStoOBCP11(cmd)': (0x21010b03, 0x21020b03),  
    'OBStoOBCP12(cmd)': (0x21010c03, 0x21020c03),  
    'OBStoOBCP13(cmd)': (0x21010d03, 0x21020d03),  
    'OBStoOBCP14(cmd)': (0x21010e03, 0x21020e03),  
    'OBStoOBCP15(cmd)': (0x21010f03, 0x21020f03),  
    'OBStoOBCP16(cmd)': (0x21011003, 0x21021003),  
    'OBStoOBCP17(cmd)': (0x21011103, 0x21021103),  
    'OBStoOBCP18(cmd)': (0x21011203, 0x21021203),  
    'OBStoOBCP19(cmd)': (0x21011303, 0x21021303),  
    'OBStoOBCP20(cmd)': (0x21011403, 0x21021403),  
    'OBStoOBCP21(cmd)': (0x21011503, 0x21021503),  
    'OBStoOBCP22(cmd)': (0x21011603, 0x21021603),  
    'OBStoOBCP23(cmd)': (0x21011703, 0x21021703),  
    'OBStoOBCP24(cmd)': (0x21011803, 0x21021803),  
    'OBStoOBCP25(cmd)': (0x21011903, 0x21021903),  
    'OBStoOBCP26(cmd)': (0x21011a03, 0x21021a03),  
    'OBStoOBCP27(cmd)': (0x21011b03, 0x21021b03),  
    'OBStoOBCP28(cmd)': (0x21011c03, 0x21021c03),  
    'OBStoOBCP29(cmd)': (0x21011d03, 0x21021d03),  
    'OBStoOBCP30(cmd)': (0x21011e03, 0x21021e03),  
    'OBStoOBCP31(cmd)': (0x21011f03, 0x21021f03),  
    'OBStoOBCP32(cmd)': (0x21012003, 0x21022003),  
    'OBStoOBCP33(cmd)': (0x21010002, 0x21020002),  # VGW

    # Special hack for TSC simulator
    'OBStoOBCP89(cmd)': (0x21015903, 0x21025903),  
    # Special hack for ANA interface
    'OBStoOBCP99(cmd)': (0x21010102, 0x21020102),  

    # OBC <--> OBCP (FITS transfer coordination)
    'OBCP1toOBC(file)': (0x21010141, 0x21020141),  
    'OBCP2toOBC(file)': (0x21010241, 0x21020241),  
    'OBCP3toOBC(file)': (0x21010341, 0x21020341),  
    'OBCP4toOBC(file)': (0x21010441, 0x21020441),  
    'OBCP5toOBC(file)': (0x21010541, 0x21020541),  
    'OBCP6toOBC(file)': (0x21010641, 0x21020641),  
    'OBCP7toOBC(file)': (0x21010741, 0x21020741),  
    'OBCP8toOBC(file)': (0x21010841, 0x21020841),  
    'OBCP9toOBC(file)': (0x21010941, 0x21020941),  
    'OBCP10toOBC(file)': (0x21010a41, 0x21020a41),  
    'OBCP11toOBC(file)': (0x21010b41, 0x21020b41),  
    'OBCP12toOBC(file)': (0x21010c41, 0x21020c41),  
    'OBCP13toOBC(file)': (0x21010d41, 0x21020d41),  
    'OBCP14toOBC(file)': (0x21010e41, 0x21020e41),  
    'OBCP15toOBC(file)': (0x21010f41, 0x21020f41),  
    'OBCP16toOBC(file)': (0x21011041, 0x21021041),  
    'OBCP17toOBC(file)': (0x21011141, 0x21021141),  
    'OBCP18toOBC(file)': (0x21011241, 0x21021241),  
    'OBCP19toOBC(file)': (0x21011341, 0x21021341),  
    'OBCP20toOBC(file)': (0x21011441, 0x21021441),  
    'OBCP21toOBC(file)': (0x21011541, 0x21021541),  
    'OBCP22toOBC(file)': (0x21011641, 0x21021641),  
    'OBCP23toOBC(file)': (0x21011741, 0x21021741),  
    'OBCP24toOBC(file)': (0x21011841, 0x21021841),  
    'OBCP25toOBC(file)': (0x21011941, 0x21021941),  
    'OBCP26toOBC(file)': (0x21011a41, 0x21021a41),  
    'OBCP27toOBC(file)': (0x21011b41, 0x21021b41),  
    'OBCP28toOBC(file)': (0x21011c41, 0x21021c41),  
    'OBCP29toOBC(file)': (0x21011d41, 0x21021d41),  
    'OBCP30toOBC(file)': (0x21011e41, 0x21021e41),  
    'OBCP31toOBC(file)': (0x21011f41, 0x21021f41),  
    'OBCP32toOBC(file)': (0x21012041, 0x21022041),  
    'OBCP33toOBC(file)': (0x21010042, 0x21020042),  # VGW
 
    # OBC <--> OBCP (RPC FITS transfer)
    'OBCP1toOBC(rpc)': (0x21010151, 0x21020151),  
    'OBCP2toOBC(rpc)': (0x21010251, 0x21020251),  
    'OBCP3toOBC(rpc)': (0x21010351, 0x21020351),  
    'OBCP4toOBC(rpc)': (0x21010451, 0x21020451),  
    'OBCP5toOBC(rpc)': (0x21010551, 0x21020551),  
    'OBCP6toOBC(rpc)': (0x21010651, 0x21020651),  
    'OBCP7toOBC(rpc)': (0x21010751, 0x21020751),  
    'OBCP8toOBC(rpc)': (0x21010851, 0x21020851),  
    'OBCP9toOBC(rpc)': (0x21010951, 0x21020951),  
    'OBCP10toOBC(rpc)': (0x21010a51, 0x21020a51),  
    'OBCP11toOBC(rpc)': (0x21010b51, 0x21020b51),  
    'OBCP12toOBC(rpc)': (0x21010c51, 0x21020c51),  
    'OBCP13toOBC(rpc)': (0x21010d51, 0x21020d51),  
    'OBCP14toOBC(rpc)': (0x21010e51, 0x21020e51),  
    'OBCP15toOBC(rpc)': (0x21010f51, 0x21020f51),  
    'OBCP16toOBC(rpc)': (0x21011051, 0x21021051),  
    'OBCP17toOBC(rpc)': (0x21011151, 0x21021151),  
    'OBCP18toOBC(rpc)': (0x21011251, 0x21021251),  
    'OBCP19toOBC(rpc)': (0x21011351, 0x21021351),  
    'OBCP20toOBC(rpc)': (0x21011451, 0x21021451),  
    'OBCP21toOBC(rpc)': (0x21011551, 0x21021551),  
    'OBCP22toOBC(rpc)': (0x21011651, 0x21021651),  
    'OBCP23toOBC(rpc)': (0x21011751, 0x21021751),  
    'OBCP24toOBC(rpc)': (0x21011851, 0x21021851),  
    'OBCP25toOBC(rpc)': (0x21011951, 0x21021951),  
    'OBCP26toOBC(rpc)': (0x21011a51, 0x21021a51),  
    'OBCP27toOBC(rpc)': (0x21011b51, 0x21021b51),  
    'OBCP28toOBC(rpc)': (0x21011c51, 0x21021c51),  
    'OBCP29toOBC(rpc)': (0x21011d51, 0x21021d51),  
    'OBCP30toOBC(rpc)': (0x21011e51, 0x21021e51),  
    'OBCP31toOBC(rpc)': (0x21011f51, 0x21021f51),  
    'OBCP32toOBC(rpc)': (0x21012051, 0x21022051),  
    'OBCP33toOBC(rpc)': (0x21012052, 0x21022052),  # VGW

    # OBC <--> STARS (file transfer)
    'OBCtoSTARS1': (0x22000101, 0x22000102),  # Summit
    'OBCtoSTARS2': (0x22000201, 0x22000202),  # Summit
    'OBCtoSTARS3': (0x22000301, 0x22000302),  # Not used
    'OBCtoSTARS4': (0x22000401, 0x22000402),  # Not used
    'OBCtoSTARS5': (0x22000501, 0x22000502),  # Simulator
    'OBCtoSTARS6': (0x22000601, 0x22000602),  # Simulator
    'OBCtoSTARS7': (0x22000701, 0x22000702),  # Not used
    'OBCtoSTARS8': (0x22000801, 0x22000802),  # Not used

    # AG image (tcp)
    'AGtoVGW': (0x20000021, 0x20000021),
    'SVtoVGW': (0x20000027, 0x20000027),
    'SHtoVGW': (0x20000024, 0x20000024),
    'FMOStoVGW': (0x20000030, 0x20000030),
    'HSCSCAGtoVGW': (0x20000032, 0x20000032),
    'HSCSHAGtoVGW': (0x20000034, 0x20000034),
    'HSCSHtoVGW': (0x20000036, 0x20000036),

    # ?? Some ANA functions (ANA also uses OBStoOSSB1)
    'ANAxxx1': (0x21040030, 0x21040030),
    'ANAxxx2': (0x21040031, 0x21040031),
    'ANAxxx3': (0x21040035, 0x21040035),
    'ANAxxx4': (0x21040036, 0x21040036),
    'OBCtoANA(img)': (0x23000101, 0x23000101),

    # Status TSCS (UDP)
    'TSCS0->': (0x20000013, None),
    'TSCS1->': (0x21030126, None),
    'TSCS2->': (0x21030226, None),
    'TSCS3->': (0x21030326, None),
    'TSCS4->': (0x21030426, None),
    'TSCS5->': (0x21030526, None),

    # Status TSCL (UDP)
    'TSCL0->': (0x20000014, None),
    'TSCL1->': (0x21030127, None),
    'TSCL2->': (0x21030227, None),
    'TSCL3->': (0x21030327, None),
    'TSCL4->': (0x21030427, None),
    'TSCL5->': (0x21030527, None),

    # Status TSCV (TCP)
    'TSCV0->': (0x20000015, None),
    'TSCV1->': (0x21030128, None),
    'TSCV2->': (0x21030228, None),
    'TSCV3->': (0x21030328, None),
    'TSCV4->': (0x21030428, None),
    'TSCV5->': (0x21030528, None),

    # OBS <--> TSC Command Interface
    #    The TowardTSC.x interface is used when sending a command from 
    #    OBS to TSC (entry[0]) and the FromTSC.x interface is used when 
    #    sending an Ack or Completion from TSC to OBS (entry[1]).
    #  TowardTSC.x:
    'OBS->TSC0': (0x20000011, 0x20000012),
    'OBS->TSC1': (0x21010104, 0x21020104),
    'OBS->TSC2': (0x21010204, 0x21020204),
    'OBS->TSC3': (0x21010304, 0x21020304),
    'OBS->TSC4': (0x21010404, 0x21020404),
    'OBS->TSC5': (0x21010504, 0x21020504),

    #  FromTSC.x:
    'TSC0->OBS': (0x20000012, 0x20000011),
    'TSC1->OBS': (0x21020104, 0x21010104),
    'TSC2->OBS': (0x21020204, 0x21010204),
    'TSC3->OBS': (0x21020304, 0x21010304),
    'TSC4->OBS': (0x21020404, 0x21010404),
    'TSC5->OBS': (0x21020504, 0x21010504)
    }

def lookup_rpcsvc(key):
    """Get the send and receive program numbers for a service
       looked up by a service string.  May raise a KeyError."""
    recv, send = ProgramNumbers[key]
    return Bunch(server_send_prgnum=send, server_receive_prgnum=recv,
                 client_send_prgnum=recv, client_receive_prgnum=send)

def get_rpcsvc_keys():
    """Returns all the possible service keys for SOSS RPC services."""
    return ProgramNumbers.keys()


def unregister(keys):
    """Tries to unregister all the servers associated with _keys_.
    Returns a dictionary of True/False entries for all services that were
    successfully unregistered.
    """
    res = {}
    for key in keys:
        prgnums = lookup_rpcsvc(key)

        # Mapping is taken from rpc.py: (prognum, version, protocol, port)
        mapping_tcp = prgnums.server_receive_prgnum, 1, rpc.IPPROTO_TCP, 0
        mapping_udp = prgnums.server_receive_prgnum, 1, rpc.IPPROTO_UDP, 0

        # Create client to portmapper and try to unregister this mapping
        p = rpc.UDPPortMapperClient('')
        if p.Unset(mapping_tcp):
            res[key] = True

        if p.Unset(mapping_udp):
            res[key] = True

        if not res.has_key(key):
            res[key] = False

    return res


def unregister_all():
    return unregister(get_rpcsvc_keys())

    
def time2timestamp(sectime=None):
    """Converts a Python time float into a SOSS-style RPC timestamp (a string)."""

    strfmt = "%Y%m%d%H%M%S"
    
    if not sectime:
        sectime = time.time()

    # A little wierdness is needed here to calculate msec (required by the SOSS rpc spec)
    msec = ('%.3f' % sectime).split('.')[1]
    # Currently the field width and precision are not supported under Solaris Python 2.3
    # timestamp = time.strftime("%4Y%2m%2d%2H%2M%2S", time.localtime(curtime)) + "." + msec
    timestamp = time.strftime("%Y%m%d%H%M%S", time.localtime(sectime)) + "." + msec
    return timestamp


def timestamp2time(timestamp_str):
    """Converts a SOSS-style timestamp into a Python time float."""
    strfmt = "%Y%m%d%H%M%S"
    
    head, tail = timestamp_str.split('.')
    tup = time.strptime(head, strfmt)
    sectime = time.mktime(tup) + float('0.'+tail)
        
    return sectime


def get_myhost(short=False):
    '''Get the name of the local host.  If short=True, return only the
    unqualified hostname'''
    
    myhost = socket.getfqdn()

    if not short:
        return myhost
    else:
        return myhost.split('.')[0]
    

def strip_host(host):
    '''Strip FQDN --> name.'''
    
    return host.split('.')[0]
    

def get_randomport(first=20000, last=30000):
    '''Get a random port number between _first_ and _last_.'''

    port = random.randint(first, last)

    return port


class rpcError(Exception):
    """RPC Message Error Exception.  Inherits from Exception and
       adds no functionality, but distinct name allows distinct catch
       clauses."""
    pass

class rpcMsgError(rpcError):
    """RPC Message Error Exception.  Inherits from Exception and
       adds no functionality, but distinct name allows distinct catch
       clauses."""
    pass


class rpcSequenceNumber(object):
    """RPC Sequence Number Class.  This implements a simple class for
    atomically incrementing an RPC sequence number.  A service will typically
    create one of these objects and share it among all the threads operating
    in that object."""

   
    def __init__(self, seq_num=0):
        """Constructor."""

        self.seq_num = seq_num
        self.lock = threading.RLock()


    def reset(self, seq_num):
        """Reset number to a known value."""

        self.lock.acquire()
        try:
            self.seq_num = seq_num

        finally:
            self.lock.release()


    def bump(self):
        """Return current number and increment, in one atomic operation."""

        self.lock.acquire()
        try:
            seq_num = self.seq_num
            self.seq_num += 1

            return seq_num

        finally:
            self.lock.release()


#END

#!/usr/bin/env python
# test_SOSS_rpc.py
#
# Bruce Bon (Bruce.Bon@SubaruTelescope.org)  2007-03-07
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Oct 15 12:34:15 HST 2008
#]
#

import unittest
import os
import re

import common
import SOSSrpc

# ========================================================================

class TestFunctions(unittest.TestCase):
    """Test module functions class."""

#    def setUp(self):
#        # put any setup here
#    def tearDown(self):
#        # put any teardown here

    def testLookup_rpcsvc(self):
        """Test lookup_rpcsvc function."""
        keys = common.ProgramNumbers.keys()
        for  key in keys:
            entry = common.ProgramNumbers[ key ]
            bunch = common.lookup_rpcsvc(key)
            self.assertEquals( entry[0], bunch.server_receive_prgnum )
            self.assertEquals( entry[0], bunch.client_send_prgnum )
            self.assertEquals( entry[1], bunch.server_send_prgnum )
            self.assertEquals( entry[1], bunch.client_receive_prgnum )

    def testGet_rpcsvc_keys(self):
        """Test get_rpcsvc_keys function."""
        #print 'Testing common module functions'
        keysDirect = common.ProgramNumbers.keys()
        keysFromFn = common.get_rpcsvc_keys()
        self.assertEquals( keysDirect, keysFromFn )

    def testTime2timestamp(self):
        """Test time2timestamp and timestamp2time functions."""
        # Test 10 hours (GMT-HST) + 1 second
        sectime = 36001.0
        timestamp = common.time2timestamp(sectime)
        self.assertEquals( '19700101000001.000', timestamp )
        sectime = common.timestamp2time(timestamp)
        self.assertAlmostEquals( 36001.0, sectime, 3 )
        # Test round trip
        timestampIn = '20060125161614.769'
        sectime = common.timestamp2time(timestampIn)
        self.assertAlmostEquals( 1138241774.769, sectime, 3 )
        timestampOut = common.time2timestamp(sectime)
        self.assertEquals( timestampIn, timestampOut )

    def testGetMyhost(self):
        """Test get_myhost function."""
        shortHostnamePattern = re.compile('^.*?\.')
        try:
            fi = os.popen( 'hostname --fqdn' )    # stdin
            #fi = os.popen( 'hostname' )    # stdin
            hostStr = fi.readline()
            fi.close()
            longHostname = hostStr[:-1]
            mo = shortHostnamePattern.match( hostStr )
            if  mo:
                shortHostname = (mo.group(0))[:-1]
            else:
                shortHostname = hostStr[:-1]
        except KeyError:
            longHostname  = None         # Unknown
            shortHostname = None         # Unknown
        self.assertEquals( longHostname,  common.get_myhost() )
        self.assertEquals( longHostname,  common.get_myhost(False) )
        self.assertEquals( shortHostname, common.get_myhost(True) )

    def testGetRandomPort(self):
        """Test get_randomport function."""
        port = common.get_randomport()
        self.assert_( port >= 20000 )
        self.assert_( port <= 30000 )
        port = common.get_randomport()
        self.assert_( port >= 20000 )
        self.assert_( port <= 30000 )
        port = common.get_randomport(10,12)
        self.assert_( port >= 10 )
        self.assert_( port <= 12 )
        port = common.get_randomport(10,12)
        self.assert_( port >= 10 )
        self.assert_( port <= 12 )
        port = common.get_randomport(10,12)
        self.assert_( port >= 10 )
        self.assert_( port <= 12 )


class TestRpcSequenceNumber(unittest.TestCase):
    """Test rpcSequenceNumber class."""

    def testAll(self):
        """Test all methods."""
        rsn = common.rpcSequenceNumber()
        self.assertEquals( 0, rsn.seq_num )
        rsn.bump()
        self.assertEquals( 1, rsn.seq_num )
        rsn = common.rpcSequenceNumber(692784)
        self.assertEquals( 692784, rsn.seq_num )
        rsn.bump()
        self.assertEquals( 692785, rsn.seq_num )
        rsn.reset(473923)
        self.assertEquals( 473923, rsn.seq_num )
        rsn.bump()
        self.assertEquals( 473924, rsn.seq_num )


class TestRpcHeader(unittest.TestCase):
    """Test rpcHeader class."""

    def testInit(self):
        """Test constructor method."""
        #print '\nTesting rpcHeader class'
        # Test null header
        rh = SOSSrpc.SOSScmdRpcHeader()
        self.assertEquals( 128, rh.len_total )
        # Test 2 sample headers
        testHdr1 = '       132,20060125161614.769,SUBARUV1,      37,    host, 0123,  bon,05123, rcvr1  ,CT,AB,         4,                            123'
        rh = SOSSrpc.SOSScmdRpcHeader( testHdr1 )
        self.assertEquals( 132, rh.len_total )
        self.assertEquals( 'AB', rh.msg_type )
        self.assertEquals( ' 123', rh.payload )
        testHdr2 = '       240,20060124222147.661,SUBARUV1,   65275,obc1-a1 ,10002,     ,     ,s01-a1  ,FT,FS,       112,                           /mdata/fits/obcp13/SKYA00584047.fits,1005120,SKYA00584047,o98017,sdata01,S01,/mdata/index/SKYA00584047.index,400'
        rh = SOSSrpc.SOSScmdRpcHeader( testHdr2 )
        self.assertEquals( 240, rh.len_total )
        self.assertEquals( 'FS', rh.msg_type )
        self.assertEquals( '/mdata/fits/obcp13/SKYA00584047.fits,1005120,SKYA00584047,o98017,sdata01,S01,/mdata/index/SKYA00584047.index,400', rh.payload )

    def testLoad(self):
        """Test load method."""
        rh = SOSSrpc.SOSScmdRpcHeader()
        # Test sample header
        testHdr1 = '       132,20060125161614.769,SUBARUV1,      37,    host, 0123,  bon,05123, rcvr1  ,CT,AB,         4,                            123'
        rh.load( testHdr1 )
        self.assertEquals( 132,    rh.len_total )
        self.assertEquals( 'AB',   rh.msg_type )
        self.assertEquals( ' 123', rh.payload )

    def testSetHdr(self):
        """Test sethdr method."""
        pass

class TestRpcMsg(unittest.TestCase):
    """Test rpcMsg class."""

    def testInit(self):
        """Test constructor method."""
        #print '\nTesting rpcMsg class'
        pass

    def testMakePacket(self):
        """Test make_packet method."""
        pass

    def testPackAb(self):
        """Test pack_ab method."""
        pass


# ========================================================================

if __name__ == "__main__":
    unittest.main()


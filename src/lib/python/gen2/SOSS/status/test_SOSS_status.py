#!/usr/bin/env python

import unittest
import logging
import SOSS_status as SOSS_status
import struct

logger = logging.getLogger('SOSS_statusTest')

class statusConverterTestCase(unittest.TestCase):
    def setUp(self):
        self.converter = SOSS_status.statusConverter()
        self.alias = SOSS_status.statusAlias(mask=None, multiplier=None)
        
    def testConv_B_1(self):
        src = '\x80\x00\x00\x00\x00\x00'
        self.alias.mask = 0x01
        result = self.converter.conv_B(src, self.alias)
        self.assertEqual(0, result)
        
    def testConv_B_2(self):
        src = '\x80\x00'
        self.alias.mask = 0xffffffffL
        result = self.converter.conv_B(src, self.alias)
        self.assertEqual(32768, result)
        
    def testConv_B_3(self):
        src = '\xC0\x00'
        self.alias.mask = 0x8000
        result = self.converter.conv_B(src, self.alias)
        self.assertEqual(32768, result)
        
    def testConv_B_4(self):
        src = '\x80\x00\x00\x00\x00\x01'
        self.alias.mask = 0xf00000000000
        result = self.converter.conv_B(src, self.alias)
        self.assertEqual(2**(6*8 - 1), result)

    def testConv_D_1(self):
        src = '\x80\x00\x10'
        result = self.converter.conv_D(src, self.alias)
        self.assertEqual(-0.1, result)
        
    def testConv_D_2(self):
        src = '\x80\x00\x10'
        self.alias.mask = 0xffff00
        result = self.converter.conv_D(src, self.alias)
        self.assertEqual(0.0, result)
        
    def testConv_D_3(self):
        src = '\x80\x00\x10\x00\x00\x01'
        result = self.converter.conv_D(src, self.alias)
        self.assertEqual(-0.10000001, result)
        
    def testconv_S_32bit_1(self):
        # signed binary number
        src = '\x80\x00\x00\x00'
        self.alias.multiplier = 2.0
        result = self.converter.conv_S(src, self.alias)
        self.assertEqual(-2147483648.0 * 2.0, result)
        
    def testconv_S_32bit_2(self):
        # signed binary number
        src = '\x80\x00\x00\x00'
        self.alias.multiplier = 1
        result = self.converter.conv_S(src, self.alias)
        self.assertEqual(-2147483648.0, result)
        
    def testconv_S_16bit_1(self):
        # signed binary number
        src = '\x80\x00'
        self.alias.multiplier = 2.0
        result = self.converter.conv_S(src, self.alias)
        self.assertEqual(-32768.0 * 2.0, result)
        
    def testconv_S_16bit_2(self):
        # signed binary number
        src = '\x80\x00'
        self.alias.multiplier = 1
        result = self.converter.conv_S(src, self.alias)
        self.assertEqual(-32768, result)
        
        
    def testconv_L_32bit_1(self):
        # signed binary number
        src = '\x80\x00\x00\x00'
        self.alias.multiplier = 2
        result = self.converter.conv_L(src, self.alias)
        self.assertEqual(2147483648 * 2, result)
        
    def testconv_L_32bit_2(self):
        # signed binary number
        src = '\x80\x00\x00\x00'
        self.alias.multiplier = 1
        result = self.converter.conv_L(src, self.alias)
        self.assertEqual(2147483648, result)
        
    def testconv_L_16bit_1(self):
        # signed binary number
        src = '\x80\x00'
        self.alias.multiplier = 2
        result = self.converter.conv_L(src, self.alias)
        self.assertEqual(32768.0 * 2.0, result)
        
    def testconv_D_16bit_1(self):
        # signed binary number
        src = '\x80\x00'
        self.alias.multiplier = 1
        result = self.converter.conv_L(src, self.alias)
        self.assertEqual(32768.0, result)
        
        # signed binary number
        src = '\x81\x00'
         
        result = self.converter.conv_D(src, self.alias)
        self.assertEqual(-100.0, result)
        
if __name__ == '__main__':
    rootLogger = logging.getLogger()
    rootLogger.addHandler(logging.StreamHandler())
    rootLogger.setLevel(logging.DEBUG)
    
    unittest.main()

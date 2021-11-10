#!/usr/bin/env python
#
# Test cases for FLDMON.py
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Dec 18 12:39:31 HST 2008
#]
#
import unittest

import FLDMON
import environment
import logging, ssdlog

# Create top level logger.
logger = logging.getLogger('test_FLDMON')
logger.setLevel(logging.ERROR)

fmt = logging.Formatter(ssdlog.STD_FORMAT)

stderrHdlr = logging.StreamHandler()
stderrHdlr.setFormatter(fmt)
logger.addHandler(stderrHdlr)


class Test_Utilties(unittest.TestCase):
    """Test the utility functions of FLDMON.
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_autoSnapOK_2000(self):
        res = FLDMON.autoSnapOK("18:00:00", "06:00:00", "20:00:00")
        self.assertEquals(True, res)

    def test_autoSnapOK_0000(self):
        res = FLDMON.autoSnapOK("18:00:00", "06:00:00", "00:00:00")
        self.assertEquals(True, res)

    def test_autoSnapOK_0200(self):
        res = FLDMON.autoSnapOK("18:00:00", "06:00:00", "02:00:00")
        self.assertEquals(True, res)

    def test_autoSnapOK_0600(self):
        res = FLDMON.autoSnapOK("18:00:00", "06:00:00", "06:00:00")
        self.assertEquals(False, res)

    def test_autoSnapOK_0605(self):
        res = FLDMON.autoSnapOK("18:00:00", "06:00:00", "06:05:00")
        self.assertEquals(False, res)

    def test_autoSnapOK_1755(self):
        res = FLDMON.autoSnapOK("18:00:00", "06:00:00", "17:55:00")
        self.assertEquals(False, res)

    def test_autoSnapOK_1800(self):
        res = FLDMON.autoSnapOK("18:00:00", "06:00:00", "18:00:00")
        self.assertEquals(True, res)

    def test_autoSnapOK_1000(self):
        res = FLDMON.autoSnapOK("18:00:00", "06:00:00", "10:00:00")
        self.assertEquals(False, res)

    def test_autoSnapOK_1200(self):
        res = FLDMON.autoSnapOK("18:00:00", "06:00:00", "12:00:00")
        self.assertEquals(False, res)

    def test_autoSnapOK_1400(self):
        res = FLDMON.autoSnapOK("18:00:00", "06:00:00", "14:00:00")
        self.assertEquals(False, res)

    def test_autoSnapOK_1600(self):
        res = FLDMON.autoSnapOK("18:00:00", "06:00:00", "16:00:00")
        self.assertEquals(False, res)

    def test_autoSnapOK_daytime_1500(self):
        res = FLDMON.autoSnapOK("14:00:00", "18:00:00", "15:00:00")
        self.assertEquals(True, res)

        
if __name__ == '__main__':

    unittest.main()

#END

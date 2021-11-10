#!/usr/bin/env python
#
# Unit Tests for the fitsutils class
#
# Eric Jeschke  (eric@naoj.org) 2006.07.19
#

import unittest
import os
import fitsutils
import pyfits


class Test_fitsutils(unittest.TestCase):

    def setUp(self):
        self.propid = 'o98001'
        self.frameid = 'SIMA00000001'
        self.testfile = '%s.fits' % self.frameid
        self.hdrkwds = {
            'prop-id': self.propid,
            'frameid': self.frameid,
            }
        self.width = 5
        self.height = 10

    def tearDown(self):
        if os.path.exists(self.testfile):
            os.remove(self.testfile)


    def test_make_fakefits(self):
        # Make a fake fits file
        fitsutils.make_fakefits(self.testfile, self.hdrkwds, self.width, self.height)
        self.assert_(os.path.exists(self.testfile))
        
        fits = pyfits.open(self.testfile)
        hdr = fits[0].header
        for (key, val) in self.hdrkwds.items():
            self.assert_(hdr.has_key(key))
            self.assertEquals(val, hdr[key])
        fits.close()


if __name__ == '__main__':

    unittest.main()


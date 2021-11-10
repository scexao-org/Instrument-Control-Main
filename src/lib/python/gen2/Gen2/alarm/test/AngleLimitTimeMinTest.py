#!/usr/bin/env python

#
# AngleLimitTimeMinTest.py - Test the AngleLimitTimeMin class
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Wed Apr 25 15:10:19 HST 2012
#]
#

import unittest
import AlarmTest
import Gen2.alarm.AngleLimitTimeMin as AngleLimitTimeMin

class AngleLimitTimeMinTest(AlarmTest.AlarmTest):
    def setUp(self):
        super(AngleLimitTimeMinTest, self).setUp()
        # We will need AngleLimitTime so create it here
        self.angleLimitTimeMin = AngleLimitTimeMin.AngleLimitTimeMin()

    def testLimitTimeNone(self):
        self.setTelLimitFlag()
        self.setAngleLimitTime()
        self.angleLimitTimeMin.update(self.svConfig, self.statusFromGen2)
        self.assertTrue(self.angleLimitTimeMin.limitTimeName == None)

    def testLimitTimeAz(self):
        self.setTelLimitFlag(azValid = True)
        self.setAngleLimitTime(limitTimeAz = 10)
        self.angleLimitTimeMin.update(self.svConfig, self.statusFromGen2)
        self.assertTrue(self.angleLimitTimeMin.limitTimeName == 'limitTimeAz')

    def testLimitTimeElLow(self):
        self.setTelLimitFlag(elLowValid = True)
        self.setAngleLimitTime(limitTimeElLow = 10)
        self.angleLimitTimeMin.update(self.svConfig, self.statusFromGen2)
        self.assertTrue(self.angleLimitTimeMin.limitTimeName == 'limitTimeElLow')

    def testLimitTimeElHigh(self):
        self.setTelLimitFlag(elHighValid = True)
        self.setAngleLimitTime(limitTimeElHigh = 10)
        self.angleLimitTimeMin.update(self.svConfig, self.statusFromGen2)
        self.assertTrue(self.angleLimitTimeMin.limitTimeName == 'limitTimeElHigh')

    def testLimitTimeRot(self):
        self.setTelLimitFlag(rotValid = True)
        self.setAngleLimitTime(limitTimeRot = 10)
        self.angleLimitTimeMin.update(self.svConfig, self.statusFromGen2)
        self.assertTrue(self.angleLimitTimeMin.limitTimeName == 'limitTimeRot')

if __name__ == '__main__':
    unittest.main()

#!/usr/local/bin/python

import Util
import unittest
import re

class PosTimeDiffTest(unittest.TestCase):

    def testSame(self):
        c = Util.timediff([0,0,0],[0,0,0])
        self.assertEqual(c,['+',[0,0,0]])

    def testPosSec(self):
        c = Util.timediff([0,0,1],[0,0,0])
        self.assertEqual(c,['+',[0,0,1]])

    def testPosMin(self):
        c = Util.timediff([0,1,0],[0,0,0])
        self.assertEqual(c,['+',[0,1,0]])

    def testPosHr(self):
        c = Util.timediff([1,0,0],[0,0,0])
        self.assertEqual(c,['+',[1,0,0]])

    def testPosMinSec(self):
        c = Util.timediff([0,1,1],[0,0,0])
        self.assertEqual(c,['+',[0,1,1]])

    def testPosHrSec(self):
        c = Util.timediff([1,0,1],[0,0,0])
        self.assertEqual(c,['+',[1,0,1]])

    def testPosHrMin(self):
        c = Util.timediff([1,1,0],[0,0,0])
        self.assertEqual(c,['+',[1,1,0]])

    def testPosHrMinSec(self):
        c = Util.timediff([1,1,1],[0,0,0])
        self.assertEqual(c,['+',[1,1,1]])


class NegTimeDiffTest(unittest.TestCase):

    def testNegSec(self):
        c = Util.timediff([0,0,0],[0,0,1])
        self.assertEqual(c,['-',[0,0,1]])

    def testNegMin(self):
        c = Util.timediff([0,0,0],[0,1,0])
        self.assertEqual(c,['-',[0,1,0]])

    def testNegHr(self):
        c = Util.timediff([0,0,0],[1,0,0])
        self.assertEqual(c,['-',[1,0,0]])

    def testNegMinSec(self):
        c = Util.timediff([0,0,0],[0,1,1])
        self.assertEqual(c,['-',[0,1,1]])

    def testNegHrSec(self):
        c = Util.timediff([0,0,0],[1,0,1])
        self.assertEqual(c,['-',[1,0,1]])

    def testNegHrMin(self):
        c = Util.timediff([0,0,0],[1,1,0])
        self.assertEqual(c,['-',[1,1,0]])

    def testNegHrMinSec(self):
        c = Util.timediff([0,0,0],[1,1,1])
        self.assertEqual(c,['-',[1,1,1]])


class MixTimeDiffTest(unittest.TestCase):

    def testPosMinNegSec(self):
        c = Util.timediff([0,1,0],[0,0,1])
        self.assertEqual(c,['+',[0,0,59]])

    def testNegMinPosSec(self):
        c = Util.timediff([0,0,1],[0,1,0])
        self.assertEqual(c,['-',[0,0,59]])

    def testPosHrNegSec(self):
        c = Util.timediff([1,0,0],[0,0,1])
        self.assertEqual(c,['+',[0,59,59]])

    def testNegHrPosSec(self):
        c = Util.timediff([0,0,1],[1,0,0])
        self.assertEqual(c,['-',[0,59,59]])

    def testPosHrNegMin(self):
        c = Util.timediff([1,0,0],[0,1,0])
        self.assertEqual(c,['+',[0,59,0]])

    def testNegHrPosMin(self):
        c = Util.timediff([0,1,0],[1,0,0])
        self.assertEqual(c,['-',[0,59,0]])

    def testPosHrSecNegMin(self):
        c = Util.timediff([1,0,1],[0,1,0])
        self.assertEqual(c,['+',[0,59,1]])

    def testPosHrMinNegSec(self):
        c = Util.timediff([1,1,0],[0,0,1])
        self.assertEqual(c,['+',[1,0,59]])

    def testPosHrNegMinSec(self):
        c = Util.timediff([1,0,0],[0,1,1])
        self.assertEqual(c,['+',[0,58,59]])

    def testNegHrPosMinSec(self):
        c = Util.timediff([0,1,1],[1,0,0])
        self.assertEqual(c,['-',[0,58,59]])

    def testNegHrSecPosMin(self):
        c = Util.timediff([0,1,0],[1,0,1])
        self.assertEqual(c,['-',[0,59,1]])

    def testNegHrMinPosSec(self):
        c = Util.timediff([0,0,1],[1,1,0])
        self.assertEqual(c,['-',[1,0,59]])

class JDTest(unittest.TestCase):
    def testKnownJD(self):
        c = Util.calcJulianDays(2003,10,10)
        self.assertEqual(c,2452922.500000)

    def testEpoch2000(self):
        c = Util.calcJulianDays(2000,1,1.5)
        self.assertEqual(c,2451545.0)

    def testGST(self):
        tu = (Util.calcJulianDays(2003,10,10.5) - 2451545.0) / 36525.0;
        c = Util.calcGST(tu, 43200)
        self.assertAlmostEqual(c, 47683.8455207, 5)

##     def testLST(self):
##         c = Util.newsidereal()
##         d = Util.sidereal()
##         self.assertEqual(c, d)

class AirMassTest(unittest.TestCase):
    
    def testAirMassLessOne(self):
        c = Util.calcAirMass(-15.0)
        self.assertEqual(c, None)
        
    def testAirMass1(self):
        c = Util.calcAirMass(1.0)
        self.assertAlmostEqual(c, -96.15, 2)
        
    def testAirMassGreater179(self):
        c = Util.calcAirMass(181.0)
        self.assertEqual(c, None)
        
    def testAirMass179(self):
        c = Util.calcAirMass(179.0)
        self.assertAlmostEqual(c, -96.15, 2)
        
    def testAirMass45(self):
        c = Util.calcAirMass(45.0)
        self.assertAlmostEqual(c, 1.41, 2)
        
    def testAirMass135(self):
        c = Util.calcAirMass(135.0)
        self.assertAlmostEqual(c, 1.41, 2)
        
    def testAirMass90(self):
        c = Util.calcAirMass(90.0)
        self.assertAlmostEqual(c, 1.00, 2)

def LoadTests(s, c):
    testFilter = re.compile("^test")
    t = filter(testFilter.search, dir(c))
    for m in t:
        s.addTest(c(m))

def PosTimeDiffTests():
    suite = unittest.TestSuite()
    LoadTests(suite, PosTimeDiffTest)
    return suite

def NegTimeDiffTests():
    suite = unittest.TestSuite()
    LoadTests(suite, NegTimeDiffTest)
    return suite

def MixTimeDiffTests():
    suite = unittest.TestSuite()
    LoadTests(suite, MixTimeDiffTest)
    return suite

def AllTimeDiffTests():
    suite = unittest.TestSuite((PosTimeDiffTests(), NegTimeDiffTests(), MixTimeDiffTests()))
    return suite

def JDTests():
    suite = unittest.TestSuite()
    LoadTests(suite, JDTest)
    return suite

def AMTests():
    suite = unittest.TestSuite()
    LoadTests(suite, AirMassTest)
    return suite

def AllTests():
    suite = unittest.TestSuite((AllTimeDiffTests(), JDTests(), AMTests()))
    return suite

if __name__ == "__main__":
        unittest.main()

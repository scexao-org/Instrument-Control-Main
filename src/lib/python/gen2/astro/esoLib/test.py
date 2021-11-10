import pyfits
import sys
import unittest

testPath = sys.modules['__main__'].__file__
data = pyfits.open('pix.fits')[0].data[15:45, 305:335].flat
sys.path.append('./lib/python%d.%d/site-packages'%(sys.version_info[0], sys.version_info[1]))
import iqe

class IQEFuncTestCase(unittest.TestCase):
    def testIqeFunction(self):
        ((x,        sdiv_x),
         (fwhm_x,   sdiv_fwhm_x),
         (y,        sdiv_y),
         (fwhm_y,   sdiv_fwhm_y),
         (maj_axis, sdiv_maj_axis),
         (peak,     sdiv_peak),
         (bg,       sdiv_bg)
        ) = iqe.iqe(data, 30, 30)
        self.assertAlmostEqual( 14.0751361847, x,           5)
        self.assertAlmostEqual(  0.0014929270, sdiv_x,      9)
        self.assertAlmostEqual(  2.5210909843, fwhm_x,      6)
        self.assertAlmostEqual(  0.0035314439, sdiv_fwhm_x, 9)
           
        self.assertAlmostEqual( 16.8185482025, y,           5)
        self.assertAlmostEqual(  0.0015319359, sdiv_y,      9)
        self.assertAlmostEqual(  2.3958778381, fwhm_y,      6)
        self.assertAlmostEqual(  0.0033525992, sdiv_fwhm_y, 9)

        # According to Arne, the difference between ia32 and sparc 
        # is due to the wrong floating point implementation on ia32.
        # It appears we only get 6 digit effective precision on 
        # ia32 of the platform for major axis std div.
        self.assertAlmostEqual(119.5355072021, maj_axis,      4)
        self.assertAlmostEqual(  1.1137487888, sdiv_maj_axis, 5)
        
        self.assertAlmostEqual(528.3922729492, peak,          4)
        self.assertAlmostEqual(  0.7953894734, sdiv_peak,     7)
        
        self.assertAlmostEqual( 75.0885086060, bg,            5)
        self.assertAlmostEqual( 12.9850578308, sdiv_bg,       5)
        
    def testIqebgvFunction(self):
        iqe.iqebgv(data, 30, 30)
    
    def testIqeFunctionFailure(self):
        self.assertRaises(TypeError, iqe.iqe, 1.2, "hoge", "hoge")
 
    def testIqeFunctionFailure2(self):
        self.assertRaises(ValueError, iqe.iqe, 1.2, 5, 5)

if __name__ == '__main__':
    m = sys.modules['__main__']
    # print str(m.__file__)
    unittest.main()

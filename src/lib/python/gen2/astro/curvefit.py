#
# curvefit.py -- FITS curve fitting using wrapped iqe function
#
# Yasuhiko Sakakibara
# Takeshi Inagaki
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Mar 17 03:33:38 HST 2011
#]

import numpy
import pyfits
import math
import os
import iqe

import Bunch

#########################################################################
#  Curve fitting
#########################################################################    

class LeastSquareFits(object):

    def __init__(self, logger):
        super(LeastSquareFits, self).__init__()
        
        self.logger = logger
                          
    def _gauss_jordan(self, m, epsilon = 10.0 ** -10):
        """
        Puts given matrix (2D array) into the Reduced Row Echelon Form.
        Returns True if successful, False if 'm' is singular.
        """
        (h, w) = (len(m), len(m[0]))

        # Elimination
        for y in range(0,h):

            maxrow = y

            # Find pivot
            for y2 in range(y+1, h):
                if abs(m[y2][y]) > abs(m[maxrow][y]):
                    maxrow = y2

            (m[y], m[maxrow]) = (m[maxrow], m[y])

            # Singular matrix check
            if abs(m[y][y]) <= epsilon:     
                return False

            # Eliminate column y
            for y2 in range(y+1, h):    
                c = m[y2][y] / m[y][y]

                for x in range(y, w):
                    m[y2][x] -= m[y][x] * c

        # Back substitute
        for y in range(h-1, 0-1, -1): 
            c = m[y][y]

            for y2 in range(0,y):
                for x in range(w-1, y-1, -1):
                    m[y2][x] -=  m[y][x] * m[y2][y] / c

            m[y][y] /= c

            # Normalize row y
            for x in range(h, w):
                m[y][x] /= c

        return True


    def _least_sq_parabola(self, l):
        """
        Given a series of (z, fwhm) pairs, builds an augmented matrix
        for the system of linear equations which solutions, a, b, c are
        the coefficients of the quadratic function
            fwhm(z) = a*z**2 + b*z + c
        """
        sum_1    = float(len(l))
        sum_x    = 0
        sum_x2   = 0
        sum_x3   = 0
        sum_x4   = 0
        sum_y    = 0
        sum_x_y  = 0
        sum_x2_y = 0

        for aPair in l:
            x = aPair[0]
            y = aPair[1]

            sum_x    += x
            sum_x2   += x ** 2.0
            sum_x3   += x ** 3.0
            sum_x4   += x ** 4.0
            sum_y    += y
            sum_x_y  += (x * y)
            sum_x2_y += (y * (x ** 2.0))
   
        return [
                 [sum_x4, sum_x3, sum_x2, sum_x2_y],
                 [sum_x3, sum_x2, sum_x,  sum_x_y],
                 [sum_x2,  sum_x, sum_1,  sum_y]
               ]

    def _cutout_data(self, data, x1, y1, x2, y2):
        ''' cut out data area for iqe calculation 
            data area(x1,y1,x2,y2) should be specified by obc frame region cmd  before focus fitting '''
        
        self.logger.debug("x1<%d> y1<%d> x2<%d> y2<%d> x2-x1<%d> y2-y1<%d>" %(x1, y1, x2, y2, x2-x1, y2-y1) )
        
        try:
            data = numpy.transpose(data[y1:y2])
            return numpy.transpose(data[x1:x2])
        #except KeyError, e:
        #    self.logger.error("index slicing  key  error<%s>" %(e) )
        except Exception,e:     
            self.logger.error("index slicing error<%s>" %(e) )
  
    def _get_keyword_val(self, header, keyword):
        ''' get a fit keyword vlaue'''
        try:
            return header[keyword]
        except KeyError,e:
            self.logger.error("failed to get fits keyword value<%s>" %(e))
            #raise KeyError, "_get_keyword_val failed<%s>" %(keyword)
    
    def _extract_data(self, hdulist,x1, y1, x2, y2):
        ''' if one of coordinate is None, pass full size image to calculate fwhm
            otherwise, slice image based on x1/x2 y1/y2  values 
            note: currently iqe funciton does calculate float 32 image only,  convert an image to float 32 all the time '''  
        if None in [x1, y1, x2, y2]:
            #x_delta = self._get_keyword_val(hdulist[0].header, 'NAXIS1')
            #y_delta = self._get_keyword_val(hdulist[0].header, 'NAXIS2')

            data = hdulist[0].data
            #(row, col)=data.shape
                       
            data = data.astype('float32')
            self.logger.debug("LeastSquareFits  build_data_points region none len data len(data[0])<%d> len(data)<%d>" %( int(len(data[0])), int(len(data) ) ) ) 
            #data =  numarray.array ( data,  type=numarray.Float32)
        else:                  
                              
            data_type = hdulist[0].data.dtype.name
            #x_delta = x2-x1
            #y_delta = y2-y1
           
            self.logger.debug("data type<%s>" %(data_type) )
            data=self._cutout_data(hdulist[0].data, int(x1), int(y1), int(x2), int(y2))
            #(row, col) = data.shape
            try:
                data =  numpy.array( data, 'float32')
            except Exception,e:
                self.logger.error("converting data to float32 error<%s>" %e)
        return  data
    
    def _write_cutout_image(self, data, path):
        """ write a fits file based on sliced region """
        try:
            hdu=pyfits.PrimaryHDU(data)
            hdu.writeto(path)
        except IOError, e:
            self.logger.error("failed to write cut image<%s>" %e)


    def buildDataPoints(self, file_list, x1=None, y1=None, x2=None, y2=None, cutout=None):
       
        res = []
      
        for aFileName in file_list:
            dirname, filename = os.path.split(aFileName)
            
            try:
                self.logger.debug("opening fits file<%s>" %(aFileName) )
                hdulist = pyfits.open(aFileName)
            except IOError, e:
                self.logger.error("failed to open fits file '%s': <%s>" %(
                        filename, str(e)))
                continue
            
            data =self._extract_data(hdulist,x1, y1, x2, y2)

            (row, col) = data.shape
            self.logger.debug("data row<%d> col<%d>" %(int(row), int(col) ) )
                    

            if cutout is not None:
                path = "%s/%sx%s_%s" % (cutout, str(row), str(col), aFileName ) 
                self._write_cutout_image(data, path)
           
            try:
                iqe_res = iqe.iqe(data.flat, int(row), int(col))
                self.logger.debug('iqe res<%s>' %(str(iqe_res)))
                z_value = self._get_keyword_val(hdulist[0].header, 'FOC-VAL')
                cdelta1 = self._get_keyword_val(hdulist[0].header, 'CDELT1')
                cdelta2 = self._get_keyword_val(hdulist[0].header, 'CDELT2')
                # account for left-handed coordinate system
                cdelta1 = math.fabs(cdelta1)
                cdelta2 = math.fabs(cdelta2)
                fwhm = (iqe_res[1][0] * cdelta1 + iqe_res[3][0] * cdelta2) /2.0
                fwhm = fwhm * 3600.0
                res.append((z_value, fwhm))
                self.logger.debug("%s: z<%f> fwhm<%f>" % (
                        filename, z_value, fwhm))
                
            except Exception,e:
                self.logger.error("%s: failed to calc iqe: <%s>" % (
                        filename, str(e)))
            finally:
                hdulist.close()
            
        # sort result by z_value
        res.sort(lambda x, y: cmp(x[0], y[0]))
    
        return res


    def plotQuadratic(self, t, a, b, c):
        return a * t**2.0 + b * t + c    

    def findMinZ(self, a, b):
        ''' derivative of ax**2 + bx + c =0 -> 2ax + b = 0 -> x = -b / 2a 
            to find out the minimum value of x '''
        return -1.0 * b/(2.0 * a)


    def getMinXY(self, ls, a,b,c):
        minX = self.findMinZ(a, b)
        minY = a * minX**2.0 + b * minX + c
     
        return (minX, minY)

    def calc_coefficient(self, data_points):
        self.logger.debug("data_points <%s>" %(data_points) )
    
        augMat = self._least_sq_parabola(data_points)

        resFlag = self._gauss_jordan(augMat)
        if not resFlag:
            return False
        
        return augMat

    def fitCurve(self, data_points):

        # Set up a struct to be returned with the results
        res = Bunch.Bunch(a=None, b=None, c=None, minX=None, minY=None,
                          code='empty', msg='No message')
        
        if not len(data_points):
            # all fwhm calculations failed; no data points found
            self.logger.error('no data points!')
            res.msg = 'No data available: FWHM all failed'
            return res

        dpX  = [aDataPoint[0] for aDataPoint in data_points]
        dpY  = [aDataPoint[1] for aDataPoint in data_points]
        self.logger.debug("setGraph datapoints<%s> dpX<%s> dpY<%s>>" %(str(data_points), str(dpX),str(dpY) ))

        augMat = self.calc_coefficient(data_points)
        
        if not augMat:
            res.msg = "Result matrix is singular: curve fitting failed"
            res.code = 'singular'
            self.logger.error(res.msg)
            return res
       
        res.a = a = augMat[0][3]
        res.b = b = augMat[1][3]
        res.c = c = augMat[2][3]
        self.logger.debug("a[%s] b[%s] c[%s]" %(str(a),str(b), str(c) ))

        if a <= 0:
            self.logger.error("Error: coefficient 'a' must be positive<%f>: curve fitting failed" %(a) )
            res.msg="fitting curve calc failed\n a*x**2 + b*x + c \n a[%.3f] must be positive"  %(a)
            res.code = 'positive'
            return res
 
        res.minX = minX = self.findMinZ(a, b)
        res.minY = minY = a * minX**2.0 + b * minX + c
       
        self.logger.debug("minX=%s minY=%s" % (minX, minY))
        res.code = 'maybeok'
        res.msg = "Curve fitting succeeded"
        return res


    def make_file_list(self, data_dir, framelist):
    #def focusFitFrames(self, data_dir, framelist,  x1=None, y1=None, x2=None, y2=None, cutout=None):
        file_list = [ os.path.join(data_dir, '%s.fits' % frameid) \
                      for frameid in framelist ] 
         
        return file_list
        #return self.calc_coefficient(file_list, x1, y1, x2, y2, cutout)
    

#END

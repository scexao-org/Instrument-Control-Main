#
# astro/fitsdata.py -- operations on FITS data via numpy/pyfits
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Jul 15 16:30:32 HST 2011
#]
#

import math
import pyfits
import numpy
import time

import Bunch
import iqe as iqemod
import qualsize as qualmod

class FitsDataError(Exception):
    """Base exception for raising errors in this module."""
    pass


def get_bitdepth(data_na):
    """Get the bit-depth of the FITS data in _data_na_.
    """
    return data_na.itemsize()


def cut_levels(data_na, top_px=255.0):
    """Perform a 'cut levels' operation on the FITS image stored in numpy
    _data_na_.  Destructively changes data_na.
    """

    # Find max and min values in the data.
    max_px = numpy.nanmax(data_na)
    min_px = numpy.nanmin(data_na)

    # Determine scaling factor to use for data.
    if max_px == min_px:
        scale = 0.0
    else:
        scale = top_px / float(max_px - min_px)

    # Subtract minimum pixel value from all pixels, to drop black point to 0.
    data_na -= min_px
    # Scale all pixels by scale factor, to raise white point to max.
    data_na *= scale

    
## def flip_vertically(data_na):
##     """Flip a FITS image stored in _data_na_ vertically.
##     Returns the NEW flipped COPY.
##     """
##     (height, width) = data_na.shape

##     #tmp_na = numpy.take(data_na, (numpy.arange(height-1, -1, -1))).view()
##     tmp_na = numpy.take(data_na, (numpy.arange(height-1, -1, -1)))
##     return tmp_na

    
def flip_vertically(data_na):
    """Flip a FITS image stored in _data_na_ vertically.
    Returns the NEW flipped COPY.
    """
    (height, width) = data_na.shape

    tmp_na = data_na.take(numpy.arange(height-1, -1, -1), axis=0)
    return tmp_na


def flip_horizontally(data_na):
    """Flip a FITS image stored in _data_na_ horizontally.
    Returns the NEW flipped COPY.
    """
    (height, width) = data_na.shape

    tmp_na = data_na.take(numpy.arange(width-1, -1, -1), axis=1)
    return tmp_na


def fits_to_rgbdata(data_na):
    """Converts a FITS numpy data to an 8-bit, cut-leveled RGB image
    stored in a packed buffer string suitable for loading into a Gtk pixbuf.
    """

    # Get some information about the image
    (height, width) = data_na.shape
    #ntype = data_na.type()

    # 1. CONVERT TO 8-BIT DATA
    print "Converting to 8-bit RGB..."
    start = time.time()
    cut_levels(data_na)
    tmp_na = data_na.astype(numpy.uint8)
    end = time.time()
    print "time = %f s" % (end - start)

    # 2. REFLECT IMAGE FROM FITS COORDINATE SYSTEM TO STANDARD RGB COORD SYSTEM
    # (i.e. a vertical flip)
    # TODO: is there a more efficient way to do this with numpy?
    print "Flipping..."
    start = time.time()
    tmp_na = flip_vertically(tmp_na)
    end = time.time()
    print "time = %f s" % (end - start)

    # 3. CONVERT TO STRING BUFFER
    # TODO: this is the slow part.  Figure out a more efficient mechanism
    # to get numpy data into a Pixbuf
##     def fitspix2rgbpix(val):
##         return chr(val) + chr(val) + chr(val)
    
    # Resize to single dimension (i.e. buffer)
    # TODO: is there an easier/faster way to do this using numpy?
    print "Creating buffer..."
    start = time.time()
##     tmp_na = numpy.reshape(tmp_na, height * width)
    tmp_na = tmp_na.flatten()
    tmp_na = tmp_na.repeat(3)
    data = tmp_na.tostring()
##     data = ''.join(map(fitspix2rgbpix, tmp_na))
    end = time.time()
    print "time = %f s" % (end - start)

    return data

def cutout_data(data, x1, y1, x2, y2, astype=None):
    """cut out data area for e.g. iqe calculation. 
    """
    data = numpy.transpose(data[y1:y2])
    data = numpy.transpose(data[x1:x2])
    if astype:
        data = data.astype(astype)
    return data
  
def iqe(data):
    # NOTE: iqe function currently only operates on floats
    data = numpy.array(data, 'float32')
    (row, col) = data.shape
                    
    return iqemod.iqe(data.flat, row, col)

def iqe2(data):
    # parm[0] = mean X position within array, first pixel = 0
    # parm[1] = FWHM in X
    # parm[2] = mean Y position within array, first pixel = 0
    # parm[3] = FWHM in Y
    # parm[4] = angle of major axis, degrees, along X = 0
    # parm[5] = peak value of object above background
    # parm[6] = mean background level
    tup = iqe(data)
    bnch = Bunch.Bunch(objx=tup[0][0], objy=tup[2][0], fwhm_x=tup[1][0],
                       fwhm_y=tup[3][0], ang_x=tup[4][0],
                       brightness=tup[5][0], skylevel=tup[6][0],
                       x=float(int(tup[0][0])), y=float(int(tup[2][0])))
    return bnch

def starsize(fwhm_x, deg_pix_x, fwhm_y, deg_pix_y):
    cdelta1 = math.fabs(deg_pix_x)
    cdelta2 = math.fabs(deg_pix_y)
    fwhm = (fwhm_x * cdelta1 + fwhm_y * cdelta2) / 2.0
    fwhm = fwhm * 3600.0
    return fwhm
    
def qualsize(data):
    (x, y, fwhm, brightness, skylevel, objx, objy) = qualmod.qualsize(data)

    return Bunch.Bunch(x=x, y=y, fwhm=fwhm, brightness=brightness,
                       skylevel=skylevel, objx=objx, objy=objy)

def fwhm(data, deg_pix_x, deg_pix_y):
    # Calculate image quality function
    iqe_res = iqe(data)
    return starsize(iqe_res[1][0], deg_pix_x,
                    iqe_res[3][0], deg_pix_y)


def scale(data_np, new_width, new_height, conserve=False):
    """Scale an image to a new width and height.
    """
    print "target size is %dx%d" % (new_width, new_height)
    #width, height = data_np.shape
    height, width = data_np.shape
    
    w_factor = float(new_width) / float(width)
    h_factor = float(new_height) / float(height)
    factor = min(w_factor, h_factor)
    print "factor is %f" % (factor)

    if factor < 1.0:
        factor = - (1.0/factor)
    if factor != 1.0:
        bindata = rebin(data_np, factor, conserve=conserve)
    else:
        bindata = data_np
    ## bindata = congrid(data, (self.width, self.height),
    ##                   method='linear')

    return bindata


def rebin(thedata, factor, conserve=None):
    """
Rebins an array into an array with the same aspect ratio, but with
dimensions that are larger or smaller by a factor of 'factor'. Increase
or decrease of dimensions is determined by the sign of 'factor'.

If the conserve keyword is set, flux is conserved, and the total of
the output array will be equal (barring rounding errors) to the total 
of the input array.

Works for 2D arrays; would require more smarts to make it work for 
higher dimensions. 
    """
    assert abs(factor) != 1.0, "Rebinning at the same scale wastes cpu!"

    if factor < 0: # make the array smaller
        oldshape = thedata.shape
        factor = abs(factor)
        work = numpy.zeros(oldshape, thedata.dtype)
        
        for i in range(0, oldshape[0], factor):
            for j in range(0, oldshape[1], factor):
                if not conserve:
                    work[i, j] = thedata[i:i+factor, j:j+factor].mean(dtype=numpy.float64)
                else:
                    work[i, j] = thedata[i:i+factor, j:j+factor].sum(dtype=numpy.float64)
        return work[::factor, ::factor]

    elif (factor > 0): # make the array bigger
        work = numpy.repeat( numpy.repeat(thedata, factor, axis=0),
                             factor, axis=1)
        if not conserve:
            return work
        else:
            return work/(factor*factor)

def congrid(a, newdims, method='neighbor', centre=False, minusone=False):
    '''Arbitrary resampling of source array to new dimension sizes.
    Currently only supports maintaining the same number of dimensions.
    To use 1-D arrays, first promote them to shape (x,1).
    
    Uses the same parameters and creates the same co-ordinate lookup points
    as IDL''s congrid routine, which apparently originally came from a VAX/VMS
    routine of the same name.

    method:
    neighbor - closest value from original data
    nearest and linear - uses n x 1-D interpolations using
                         scipy.interpolate.interp1d
    (see Numerical Recipes for validity of use of n 1-D interpolations)
    spline - uses ndimage.map_coordinates

    centre:
    True - interpolation points are at the centres of the bins
    False - points are at the front edge of the bin

    minusone:
    For example- inarray.shape = (i,j) & new dimensions = (x,y)
    False - inarray is resampled by factors of (i/x) * (j/y)
    True - inarray is resampled by(i-1)/(x-1) * (j-1)/(y-1)
    This prevents extrapolation one element beyond bounds of input array.
    '''
    if not a.dtype in [numpy.float64, numpy.float32]:
        a = numpy.cast[float](a)

    m1 = numpy.cast[int](minusone)
    ofs = numpy.cast[int](centre) * 0.5
    old = numpy.array( a.shape )
    ndims = len( a.shape )
    if len( newdims ) != ndims:
        print "[congrid] dimensions error. " \
              "This routine currently only support " \
              "rebinning to the same number of dimensions."
        return None
    newdims = numpy.asarray( newdims, dtype=float )
    dimlist = []

    if method == 'neighbor':
        for i in range( ndims ):
            base = numpy.indices(newdims)[i]
            dimlist.append( (old[i] - m1) / (newdims[i] - m1) \
                            * (base + ofs) - ofs )
        cd = numpy.array( dimlist ).round().astype(int)
        newa = a[list( cd )]
        return newa

    elif method in ['nearest','linear']:
        # calculate new dims
        for i in range( ndims ):
            base = numpy.arange( newdims[i] )
            dimlist.append( (old[i] - m1) / (newdims[i] - m1) \
                            * (base + ofs) - ofs )
        # specify old dims
        olddims = [numpy.arange(i, dtype = numpy.float) for i in list( a.shape )]

        # first interpolation - for ndims = any
        mint = scipy.interpolate.interp1d( olddims[-1], a, kind=method )
        newa = mint( dimlist[-1] )

        trorder = [ndims - 1] + range( ndims - 1 )
        for i in range( ndims - 2, -1, -1 ):
            newa = newa.transpose( trorder )

            mint = scipy.interpolate.interp1d( olddims[i], newa, kind=method )
            newa = mint( dimlist[i] )

        if ndims > 1:
            # need one more transpose to return to original dimensions
            newa = newa.transpose( trorder )

        return newa
    elif method in ['spline']:
        oslices = [ slice(0,j) for j in old ]
        oldcoords = numpy.ogrid[oslices]
        nslices = [ slice(0,j) for j in list(newdims) ]
        newcoords = numpy.mgrid[nslices]

        newcoords_dims = range(numpy.rank(newcoords))
        #make first index last
        newcoords_dims.append(newcoords_dims.pop(0))
        newcoords_tr = newcoords.transpose(newcoords_dims)
        # makes a view that affects newcoords

        newcoords_tr += ofs

        deltas = (numpy.asarray(old) - m1) / (newdims - m1)
        newcoords_tr *= deltas

        newcoords_tr -= ofs

        newa = scipy.ndimage.map_coordinates(a, newcoords)
        return newa
    else:
        print "Congrid error: Unrecognized interpolation type.\n", \
              "Currently only \'neighbor\', \'nearest\',\'linear\',", \
              "and \'spline\' are supported."
        return None


#END

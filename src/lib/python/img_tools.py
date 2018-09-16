import numpy as np
import pyfits as pf
from scipy.signal import medfilt2d as medfilt
from scipy import ndimage
import pdb
import matplotlib.pyplot as plt


''' ---------------------------------------------------------------------
A lot of algorithms and diagnostic tools end up relying on a small
number of apparently simple but actually tricky tools to find centroids, 
mask regions of images, locate features, subtract background, ...

these little tools are assembled here into a single "library" that 
should be included by all programs requiring them.

Frantz.
--------------------------------------------------------------------- '''

def mkdisk((xs, ys), (x0, y0), r0):
    ''' ------------------------------------------------------
    Create a circular mask centered on (x0,y0) in an array of
    size (xs, ys) with radius r0.
    Useful for centroid algorithms.
    ------------------------------------------------------ '''
    x,y = np.meshgrid(np.arange(xs)-x0, np.arange(ys)-y0)
    dist = np.hypot(y,x)
    mask = dist <= r0
    return mask

def mkbox((xs, ys), (x0, y0), (dx, dy)):
    ''' ------------------------------------------------------
    Create a box mask of lower corner (x0,y0) in an array of
    size (xs, ys), of dimensions (dx, dy).
    ------------------------------------------------------ '''
    x,y = np.meshgrid(np.arange(xs), np.arange(ys))
    mask = (x >= x0) * (x < x0+dx) * (y >= y0) * (y < y0+dy)
    return mask

def find_disk_center(img, diam=100):
    ''' ------------------------------------------------------
    Locate the center of a disk of given radius in img
    This algorithm minimizes the flux outside the disk
    ------------------------------------------------------ '''
    (ys, xs) = img.shape # size of "image"
    bmask = mkdisk((xs, ys), (xs/2, ys/2), diam/2)
    mydisk = np.zeros_like(img)
    mydisk[bmask] = 1.0
    mydisk = 1 - np.roll(np.roll(mydisk, ys/2, 0), xs/2, 1)
    
    temp = medfilt(img.copy() - np.median(img))
    temp -= temp.min()
    bval = np.sum(temp)

    thr = np.percentile(temp, 92) # pupil covers 8% of img surface
    temp[temp < thr] = 0.0
    temp[temp > thr] = 1.0

    x0, y0, x1, y1 = 0, 0, xs, ys # first iteration search area
    xcb, ycb = 0, 0

    stp = np.float(diam)

    while (stp > 0.5):
        xc = np.arange(x0, x1, stp, dtype=int)
        yc = np.arange(y0, y1, stp, dtype=int)
        for i in xrange(xc.size):
            for j in xrange(yc.size):
                mydisk = np.roll(np.roll(mydisk, xc[i], 0), yc[j], 1)
                tot_out = np.sum((mydisk) * temp)
                val = tot_out
                mydisk = np.roll(np.roll(mydisk, -xc[i], 0), -yc[j], 1)
                if (val < bval):
                    bval = val
                    xcb, ycb = xc[i], yc[j]
        x0, x1 = 0.5 * (x0 + xcb), 0.5 * (x1 + xcb)
        y0, y1 = 0.5 * (y0 + ycb), 0.5 * (y1 + ycb)
        stp *= 0.5

    mydisk = 1.0 - np.roll(np.roll(mydisk, xcb, 0), ycb, 1)

    return((xcb, ycb))


def find_psf_center(img, verbose=True, nbit=10):
    ''' -------------------------------------
    Locate the center of a psf-type image img
    ------------------------------------- '''
    temp = img.astype('float')
    bckg = np.median(temp)   # background level
    temp -= bckg
    mfilt = medfilt(temp, 3) # median filtered, kernel size = 3
    (sy, sx) = mfilt.shape   # size of "image"
    sxy = np.max([sx, sy])

    xc, yc = sx/2, sy/2      # first estimate for psf center

    signal = np.zeros_like(img)
    #signal[mfilt > bckg] = 1.0
    signal[mfilt > 0] = 1.0

    for it in xrange(nbit):
        #sz = sx/2/(1.0+(0.1*sx/2*it/(4*nbit)))
        sz = sxy/2/(1.0+(0.1*sxy/2*it/(4*nbit)))
        x0 = np.max([int(0.5 + xc - sz), 0])
        y0 = np.max([int(0.5 + yc - sz), 0])
        x1 = np.min([int(0.5 + xc + sz), sx])
        y1 = np.min([int(0.5 + yc + sz), sy])

        mask = np.zeros_like(img)
        mask[y0:y1, x0:x1] = 1.0

        profx = (mfilt*mask*signal).sum(axis=0)
        profy = (mfilt*mask*signal).sum(axis=1)
        
        xc = (profx*np.arange(sx)).sum() / profx.sum()
        yc = (profy*np.arange(sy)).sum() / profy.sum()

        if verbose:
            print("it #%2d center = (%.2f, %.2f)" % (it+1, xc, yc))

    return (xc, yc)

def locate_speckles(img, nspk=1, xr=5.0, nbit=20):
    ''' --------------------------------
    Returns two lists of x,y coordinates 
    of speckles in the image.
    parameters:
    - img  : the image to be searched
    - nspk : # of speckles to profile
    - xr   : exclusion radius
    -------------------------------- '''
    temp = img.copy()        # to make sure we don't damage image
    mfilt = medfilt(temp, 3) # median filtered, kernel size = 3
    (ys, xs) = mfilt.shape   # size of "image"
    spkx, spky = [], []      # speckle coordinates
    ni = 0                   # number of identified speckles
    
    while (ni < nspk):
        # locate maximum in image
        x1 = mfilt.argmax() %  xs
        y1 = mfilt.argmax() // xs
        # fine-tune coordinates
        m1 = mkdisk((xs, ys), (x1, y1), xr)
        if nbit == 0:
            (x11, y11) = (x1, y1)
            mfilt *= (1.0-m1)
        else:
            (x11, y11) = find_psf_center((m1) * mfilt, False, nbit)
            mfilt *= (1.0 - mkdisk((xs, ys), (x11, y11), xr))

        # increment counter of speckles
        spkx.append(x11)
        spky.append(y11)
        ni += 1

    return (spkx, spky)

def locate_speckles0(img, nspk=1, xr=5.0, nbit=20):
    mfilt = medfilt(img, 3)
    #pf.writeto('test.fits', mfilt, clobber=True)
    vmax = np.percentile(mfilt, 99.95)
    labeled, nobj = ndimage.label(mfilt > 0.99*vmax)
    if nobj > 1:
        mass = ndimage.center_of_mass(img, labeled, range(1,nspk+1))
    else:
        mass = []
        #mass = ndimage.center_of_mass(img, labeled)
    temp = np.array(mass)
    return((temp[:,1], temp[:,0]))


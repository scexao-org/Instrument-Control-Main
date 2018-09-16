import numpy as np, matplotlib.pyplot as plt, pyfits as pf
from scipy.misc import factorial as fac
from scipy import *
import pdb

import pupil

shift = np.fft.fftshift

# ----------------------------------------
#   equivalent of the IDL dist function
# ----------------------------------------
def dist((n,m)):
    x,y = np.meshgrid(np.arange(n)-n/2, np.arange(m)-m/2)
    return(np.hypot(y,x))

# ---------------------------------------------------------
# Returns the azimuth in radians of points in an array of 
# size (n, m) with respect to the center of the array.
# ---------------------------------------------------------
def azim((n, m)):
    xx,yy = np.meshgrid(np.arange(n)-n/2, np.arange(m)-m/2)
    return np.arctan2(xx,yy)



def sector((n,m), radius, sector=1):
    ''' ---------------------------------------------------------
    returns an array that draws the pupil of the Subaru Telescope
    at the center of an array of size (n,m) with radius "radius".

    Symbols and values used for the description come from the
    document sent to Axsys for the fabrication of the SCExAO
    PIAA lenses, circa 2009.
    --------------------------------------------------------- '''
    dtor = np.pi / 180.0

    # Subaru pupil description
    # ------------------------
    pdiam, odiam = 7.92, 2.3  # tel. and obst. diameters (meters)
    thick  = 0.45             # adopted spider thickness (meters)
    offset = 1.278            # spider intersection offset (meters)
    beta   = 51.75*dtor       # spider angle beta
    ro     = odiam/pdiam      # fraction of aperture obsctructed
    
    xx,yy  = np.meshgrid(np.arange(n)-n/2, np.arange(m)-m/2)
    mydist = np.hypot(yy,xx)

    thick  *= radius/pdiam
    offset *= radius/pdiam
    epsi   = thick/(2*np.sin(beta))

    a = ((xx > offset + epsi) * (abs(np.arctan(yy/(xx-offset-epsi))) < beta))
    b = ((xx < -offset - epsi) * (abs(np.arctan(yy/(xx+offset+epsi))) < beta))
    # quadrants 2-3
    c = ((yy > 0.0) * ((abs(np.arctan(yy/(xx-offset+epsi))) > beta) +
                       (abs(np.arctan(yy/(xx+offset-epsi))) > beta)))
    d = ((yy < 0.0) * ((abs(np.arctan(yy/(xx-offset+epsi))) > beta) +
                       (abs(np.arctan(yy/(xx+offset-epsi))) > beta)))
    # pupil outer and inner edge
    e = (mydist < radius) * (mydist > ro*radius)

    if sector == 1:        
        temp = (0.3*a-0.1*(b+c+d))*e
    elif sector == 2:
        temp = (0.3*b-0.1*(a+c+d))*e
    elif sector == 3:
        temp = (0.3*c-0.1*(a+b+d))*e
    else:
        temp = (0.3*d-0.1*(a+b+c))*e
        
    return(temp/temp.std())


def mksector_vector(ii, xymask):
    '''------------------------------------------
    returns a 1D vector of size xymask.shape(0),
    containing the n,m Zernike polynomial
   ------------------------------------------ '''
    res = np.zeros(xymask.shape[0])
    rho = np.sqrt(xymask[:,0]**2+xymask[:,1]**2)

    toto = sector((50,50), 25, sector=ii)

    xx = np.cast['int'](np.round(xymask[:,0]*25+25))
    yy = np.cast['int'](np.round(xymask[:,1]*25+25))

    res = toto[xx, yy]

    rms0 = np.std(res)
    res /= rms0
    return res

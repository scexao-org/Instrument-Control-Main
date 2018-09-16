import numpy as np, matplotlib.pyplot as plt, pyfits as pf
from scipy.misc import factorial as fac
from scipy import *
import pdb

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

# ------------------------------------------------
# Returns the Zernike coefficients and exponents 
# for a given mode (n,m)
# ------------------------------------------------
def zer_coeff(n,m):
    coeffs, pows = [], []

    for s in range((n-m)/2+1):
        coeffs.append((-1.0)**s * fac(n-s) / \
                          (fac(s) * fac((n+m)/2.0 - s) * fac((n-m)/2.0 - s))) 
        pows.append(n-2.0*s)
    return coeffs, pows

def noll_2_zern(j):
    '''------------------------------------------
    Noll index converted to Zernike indices 

    j: Noll index
    n: radial Zernike index
    m: azimuthal Zernike index
   ------------------------------------------ '''
    if (j == 0):
        raise ValueError("Noll indices start at 1")

    n = 0
    j1 = j-1
    while (j1 > n):
        n += 1
        j1 -= n

    m = (-1)**j * ((n % 2) + 2 * int((j1+((n+1)%2)) / 2.0 ))
    return (n, m)

# corresponding to a given Zernike polynomial (n,m).
# optional proj = "cos" or "sin".
# optional nolim = 1 (wf extends beyond the disk limit)
# ------------------------------------------------------
def mkzer(n, m, size, rad, limit=False):
    '''------------------------------------------
    returns a 2D array of size sz,
    containing the n,m Zernike polynomial
    within a disk of radius rad
   ------------------------------------------ '''
    res = np.zeros((size, size))
    (coeffs, pows) = zer_coeff(n,np.abs(m))

    rho = dist((size, size))/float(rad)
    outp = np.where(rho >  1.0)
    inp  = np.where(rho <= 1.0)

    for i in range(np.size(coeffs)):
        res += coeffs[i] * (rho)**pows[i]

    if (limit != False): 
        res[outp] = 0.0

    azi = azim((size, size))

    if m > 0:
        res *= np.cos(m * azi)
    if m < 0:
        res *= np.sin(-m * azi)

    # normalization
    rms0 = np.std(res[inp])
    res /= rms0
    return res

def mkzer1(j, sz, rad, limit=False):
    '''------------------------------------------
    returns a 2D array of size sz,
    containing the j^th Zernike polynomial
    within a disk of radius rad
   ------------------------------------------ '''
    (n,m) = noll_2_zern(j)
    return (mkzer(n,m, sz, rad, limit))

def mkzer_vector(n, m, xymask):
    '''------------------------------------------
    returns a 1D vector of size xymask.shape(0),
    containing the n,m Zernike polynomial
   ------------------------------------------ '''
    (coeffs, pows) = zer_coeff(n,np.abs(m))
    res = np.zeros(xymask.shape[0])
    rho = np.sqrt(xymask[:,0]**2+xymask[:,1]**2)

    for i in range(np.size(coeffs)):
        res += coeffs[i] * (rho)**pows[i]

    azi = np.arctan2(xymask[:,0], xymask[:,1])

    if m > 0:
        res *= np.cos(m * azi)
    if m < 0:
        res *= np.sin(-m * azi)

    # normalization
    rms0 = np.std(res)
    res /= rms0
    return res

def mkzer1_vector(j, xymask):
    '''------------------------------------------
    returns a 1D vector of size xymask.shape(0),
    containing the j^th Zernike polynomial
   ------------------------------------------ '''
    (n,m) = noll_2_zern(j)
    return(mkzer_vector(n, m, xymask))

# --------------------------------------------------------
#                     main program
# --------------------------------------------------------
if __name__ == "__main__":

    size=512
    vmax = 150.0

    zer = mkzer(3,3, 32,32, "cos",0)

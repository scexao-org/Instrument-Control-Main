import os
import sys
import numpy as np

import pickle
from numpy.linalg   import solve
from scipy.optimize import fmin
from scipy.optimize import leastsq
#from scipy.signal   import medfilt

home = os.getenv('HOME')
sys.path.append(home+'/src/lib/python/')
from img_tools import *

auxdir = home+"/conf/speckle_aux/"

def medfilt (x, k=3):
    """Apply a length-k median filter to a 1D array x.
    Boundaries are extended by repeating endpoints.
    """
    assert k % 2 == 1, "Median filter length must be odd."
    assert x.ndim == 1, "Input must be one-dimensional."
    k2 = (k - 1) // 2
    y = np.zeros ((len (x), k), dtype=x.dtype)
    y[:,k2] = x
    for i in range (k2):
        j = k2 - i
        y[j:,i] = x[:-j]
        y[:j,i] = x[0]
        y[:-j,-(i+1)] = x[j:]
        y[-j:,-(i+1)] = x[-1]
    return np.median (y, axis=1)

# ====================================================================
# ====================================================================

class Config():
    nk, na = 20.0, 10.0
    a2b_amps   = 0.1  + 0.2 * np.arange(na) / na
    a2b_kxs    = 0.01 + 0.5 * np.arange(nk) / nk
    #a2b        = pf.getdata(auxdir+'a2b.fits')

    I0 = 6511.3
    c0 = 0.025
    a0 = 0.04

    def read_conf_file(self, fname='config.pick'):
        #global stat_sz
        # --- or load default parameters ---

        self.SPF2PIX      = np.array([[166.89, -0.13],
                                      [0.39, 165.03]])
        
        self.PIX2SPF      = np.array(np.matrix(self.SPF2PIX).I)
        self.prbamp       = 0.01  # probe default amplitude
        self.lpgain       = 0.2
        self.nphi         = 10
        self.nspk_2_track = 1
        self.nfrm_2_anlys = 1
        self.orient       = "LFT"
        self.stat_sz      = 50
        self.ROI_xr       = 20
        self.orix         = 160
        self.oriy         = 128
        
        try:
            # --- upload configuration from pickle file ---
            fd = open(auxdir+fname, 'r')
            data = pickle.load(fd)
            fd.close()
            self.orix         = data["orix"]
            self.oriy         = data["oriy"]
            self.PIX2SPF      = data["pix2spf"]
            self.SPF2PIX      = data["spf2pix"]
            self.lpgain       = data["lpgain"]
            self.nphi         = data["nphi"]
            self.nspk_2_track = data["nspkl"]
            self.nfrm_2_anlys = data["nfrm"]
            self.prbamp       = data["prbamp"]
            self.orient       = data["orient"]
            self.stat_sz      = data["stat_sz"]

        except:
            print("File %s incomplete?" % (fname,))
            print("Some parameters may be missing")
            self.nspk_2_track = 10
        stat_sz = self.stat_sz

        self.spxs = np.zeros(50) # max number of speckles
        self.spys = np.zeros(50) # max number of speckles

        return None

    def save_conf_file(self, fname='config.pick'):
        data = {"nspkl"   : int(self.nspk_2_track),
                "nfrm"    : int(self.nfrm_2_anlys),
                "orix"    : self.orix,
                "oriy"    : self.oriy,
                "pix2spf" : self.PIX2SPF,
                "spf2pix" : self.SPF2PIX,
                "prbamp"  : self.prbamp,
                "nphi"    : self.nphi,
                "orient"  : self.orient,
                "ROI_xr"  : self.ROI_xr,
                "stat_sz" : self.stat_sz,
                "lpgain"  : self.lpgain,
                "nphi"    : self.nphi}

        fd = open(auxdir+fname, 'w')
        pickle.dump(data, fd)
        fd.close()
        return None

    def summary(self):
        print("Config. summary:\n--------------------------")
        if self.orix != None:
            print("Field origin coordinates:")
            print("(x0, y0) = (%6.2f,%6.2f)" % (self.orix,self.oriy,))
        if self.SPF2PIX != None:
            np.set_printoptions(suppress=True)
            print("\nSPF2PIX matrix:")
            print(np.round(self.SPF2PIX, 3))
        print("--------------------------")

# ====================================================================
# ====================================================================

def mk_sat_mask((xs, ys), satx, saty, xr=15):
    imask = mkdisk((xs, ys), (satx[0], saty[0]), xr)
    for i in range(3):
        imask += mkdisk((xs, ys), (satx[i+1], saty[i+1]), xr)
    return(imask)

# ====================================================================
# ====================================================================

def mkROI((xs, ys), (x0, y0), ori="LFT", xr=10):
    ''' ----------------------------------------
    Defines the Region of Interest, centered on
    (x0, y0), for the requested fov position.
    ---------------------------------------- '''
    #bx, by = 80, 80 # eyeballed from images
    bx, by = 72, 72 # eyeballed from images
    nw = 10 # notch width

    notch = mkbox((xs, ys),  (x0-nw, y0), (2*nw, by))

    if ori == "RGT": 
        x1, y1, dx, dy = x0, y0-by, bx, 2*by
        notch = mkbox((xs, ys),  (x0, y0), (nw, by))
    elif ori == "DWN":
        x1, y1, dx, dy = x0-bx, y0, 2*bx, by
        notch = mkbox((xs, ys),  (x0, y0), (bx, nw))
    elif ori == "UP":
        x1, y1, dx, dy = x0-bx, y0-by, 2*bx, by
        notch = mkbox((xs, ys),  (x0-bx, y0-nw), (bx, nw))
    elif ori == "LFT":
        x1, y1, dx, dy = x0-bx, y0-by, bx, 2*by
        notch = mkbox((xs, ys),  (x0-nw, y0-by), (nw, by))

    wbox  = mkbox((xs, ys),  (x1, y1), (dx, dy))
    #obox  = mkdisk((xs, ys), (x0, y0), bx) # outer disk
    obox  = mkbox((xs, ys),  (x0-bx, y0-by), (2*bx, 2*by)) # outer box
    imask = mkdisk((xs, ys), (x0, y0), xr) # inner disk excluded
    return wbox * obox * (1 - imask) * (1 - notch)
    #return wbox * obox * (1 - imask) * (1 - notch)

# ======================================================================
# ======================================================================

def mkROI_0((xs, ys), (x0, y0), ori="LFT", xr=10):
    ''' ----------------------------------------
    Defines the Region of Interest, centered on
    (x0, y0), for the requested fov position.
    ---------------------------------------- '''
    bx, by = 84, 84 # eyeballed from images

    if ori == "RGT": 
        x1, y1, dx, dy = x0, y0-by, bx, 2*by
    elif ori == "UP":
        x1, y1, dx, dy = x0-bx, y0, 2*bx, by
    elif ori == "DWN":
        x1, y1, dx, dy = x0-bx, y0-by, 2*bx, by
    else:
        x1, y1, dx, dy = x0-bx, y0-by, bx, 2*by
    
    wbox  = mkbox((xs, ys), (x1, y1), (dx, dy))
    imask = mkdisk((xs, ys), (x0, y0), xr)
    return wbox * (1 - imask)

# ======================================================================
# ======================================================================

def residuals(p, y, phi):
    k, a, th = p
    err = y - k*(a0**2 + 2*a*a0*np.cos(th-phi))
    return err

def peval(phi, p):
    return p[0] * (a0**2 + 2*p[1]*a0*np.cos(p[2]-phi))

# ======================================================================
# ======================================================================

def CAsolver(ii, Iarr, a0, verbose=False): # quick CA solver!!

    cur_file = home+"/conf/speckle_aux/current_%02d" % (ii,)

    phi    =  2*np.pi * np.arange(Iarr.size-1) / float(Iarr.size-1)
    temp   = medfilt(Iarr[1:])
    phi0   = phi[temp == np.max(temp)][0]   # initial guess for phase

    test   = np.cos(phi) + 1j * np.sin(phi)
    crit   = np.dot(Iarr[1:], test)

    ph1    = np.angle(crit)
    AA     = 2.0 * np.abs(crit) / 30
    offset = np.mean(Iarr[1:])# - Iarr[0] !!!! TO BE TESTED !!!
    gamma  = AA / offset

    a11 = a0 * (1 + np.sqrt(1-gamma**2)) / gamma
    a12 = a0 * (1 - np.sqrt(1-gamma**2)) / gamma
    a1 = np.min([a11, a12])

    if np.isnan(a1):
        a1 = 0.0
    soluce = [a1, ph1, offset]

    koeff = AA / (2 * a0 * a1)

    print("c=%.3f, a0=%.3f, a1=%.3f, AA = %.3f, ph1 = %.3f, offset = %.3f" % 
          (koeff, a0, a1, AA, ph1, offset))
    np.save(cur_file, (Iarr, a0, phi, soluce))#[a0, Iarr, phi, plsq[0]])
    return soluce

# ======================================================================
# ======================================================================

def CAsolver1(Iarr, a0, verbose=False):
    ''' ---------------------------------------------
    Solver for the complex amplitude of a speckle.
    Relies on scipy's "leastsq" procedure.
    --------------------------------------------- '''

    cur_file = home+"/conf/speckle_aux/current"

    phi =  2*np.pi * np.arange(Iarr.size-1) / float(Iarr.size-1)
    temp = medfilt(Iarr[1:])
    phi0  = phi[temp == np.max(temp)][0]   # initial guess for phase
    koeff = np.abs(Iarr[1:].mean()-Iarr[0])/a0**2    # initial guess for coeff

    p0 = [koeff, a0, phi0, 0.0]

    # model and cost function for least square
    feval = lambda p, phase: p[0] * (a0**2 + 2*p[1]*a0*np.cos(p[2]-phase)) + p[3]
    resid = lambda p, phase, inten: inten - feval(p, phase)

    trial, nmax = 0, 1000
    klook = True
    while klook:
        plsq = leastsq(resid, p0, args=(phi, Iarr[1:]))
        soluce = np.array([np.abs(plsq[0][1]), plsq[0][2], 
                           np.abs(plsq[0][0]), plsq[0][3]])

        #print a0
        #print Iarr
        #print '------'

        if soluce[0] < 0.0: p0[1] += 0.01#np.pi/2
        else: klook = False
        trial+=1
        if trial == nmax:
            print "Stopped trying after %d times" % (nmax,)
            return np.array([0.0, 0.0, 0.0])

    np.save(cur_file, (Iarr, a0, phi, plsq[0]))#[a0, Iarr, phi, plsq[0]])
    return soluce

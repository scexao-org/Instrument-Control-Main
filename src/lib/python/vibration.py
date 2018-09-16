#!/usr/bin/env python

import numpy as np
import numpy as np
import numpy.fft as nfft
import math as m
import sys

# ======= MAKE RAMP =====================================================
# =======================================================================

def make_ramp(*args):
    # make_ramp - Creates a n points ramp between a and b.
    # PURPOSE:
    # This function computes and returns a n point ramp between a and b, b can
    # be excluded or included, with a linear or logarithmic step.
    # INPUTS:
    #    a: left limit, included
    #    b: right limit, excluded or included
    #    n: numer of points in the ramp
    #  leq: OPTIONAL boolean to include b, default is b is excluded
    # loga: OPTIONAL boolean to use a log frequency axis, default is linear.
    # OUPUTS:
    # ramp: ramp
    
    ni = len(args)
    
    a = args[0]
    b = args[1]
    n = args[2]
    if ni == 3:
        leq = 0
        loga = 0
    elif ni == 4:
        leq = args[3]
        loga = 0
    else:
        leq = args[3]
        loga = args[4]
        if leq == []:
            leq = 0
    
    if leq == 1:
        n2 = n-1
    else:
        n2 = n
    
    if loga == 1:
        ramptemp = np.array(map(float, range(n)))*(m.log10(b)-m.log10(a))/n2+m.log10(a)
        ramp = np.power(10,ramptemp)
    else:
        ramp = np.array(map(float, range(n)))*(b-a)/n2+a
    
    return ramp

# ====== CALCULATE PSD ==================================================
# =======================================================================
class Returnpsd(object):
    def __init__(self, freq, psd, cumint):
        self.freq = freq
        self.psd = psd
        self.cumint = cumint

def calc_psd(x, fsamp):
    # calc_psd - calculate the PSD and the cumulative integral of a set of data.
    # PURPOSE:
    # This function computes the PSD of a set of data.
    # INPUTS:
    #        x: Time sequence to analyze.
    # OUTPUTS:
    #      psd: PSD of the time sequence.
    #   cumint: cumulative integral of the time sequence.
    
    s = np.shape(x)
    npoints = s[0]
    if len(s) == 2:
        ndim = s[1]
    else:
        x = np.reshape(x, [npoints, 1])
        ndim = 1
    
    freq = make_ramp(fsamp/npoints, fsamp/2., npoints//2, [], 0)
    
    psd = np.zeros([npoints//2, ndim])
    cumint = np.zeros([npoints//2, ndim])
    #window = np.hanning(npoints)
    #window /= np.mean(window)
    for i in range(ndim):
        fftxx = nfft.fft(np.squeeze(x[:, i]))/npoints#*window)/npoints
        psdxx = abs(fftxx)**2
        psd[:, i] = psdxx[0:npoints//2]
        cumint[1:npoints//2, i] = 2*np.cumsum(np.squeeze(psd[1:npoints//2, i]))
    
    psd = np.squeeze(psd)
    cumint = np.squeeze(cumint)
    
    return Returnpsd(freq, psd, cumint)

# ========== PSD2D ===============================================
# ================================================================
class Returnpsd2d(object):
    def __init__(self, X, Y, psd_2d, cumint_2d):
        self.X = X
        self.Y = Y
        self.psd_2d = psd_2d
        self.cumint_2d = cumint_2d

def psd2d(signal, npoints, nshift, fsamp):
    ntot = len(signal)
    npsd = (ntot-npoints)//nshift+1
    
    window = np.hanning(npoints)
    window /= np.mean(window)

    psd_2d = np.zeros((npsd, npoints/2))
    cumint_2d = np.zeros((npsd, npoints/2))
    for i in range(npsd):
        sig2 = signal[i*nshift:i*nshift+npoints]*window
        res_psd = calc_psd(sig2, fsamp)
        psd_2d[i,:] = res_psd.psd
        cumint_2d[i,:] = res_psd.cumint
    
    freq = res_psd.freq
    time = make_ramp(0, npsd*nshift/fsamp, npsd)
    X,Y = np.meshgrid(freq, time)
    
    return Returnpsd2d(X, Y, psd_2d, cumint_2d)


# ========== PSDrad ===============================================
# ================================================================
class Returnpsdrad(object):
    def __init__(self, X, Y, psd_rad, cumint_rad):
        self.X = X
        self.Y = Y
        self.psd_rad = psd_rad
        self.cumint_rad = cumint_rad

def psdrad(signal, npoints, nshift, nangle, fsamp):
    
    s = np.shape(signal)
    if len(s) != 2:
        print "wrong dimensions"
        sys.exit()
    else:
        ndim = s[1]
        if ndim != 2:
            print "wrong dimensions"
            sys.exit()
        ntot = s[0]
    
    freq = make_ramp(fsamp/npoints, fsamp/2., npoints//2)
    
    psd_rad = np.zeros([nangle, npoints//2])
    cumint_rad = np.zeros([nangle, npoints//2])
    window = np.hanning(npoints)
    window /= np.mean(window)
    nbfft = (ntot-npoints)//nshift+1
    ffttemp = np.zeros((npoints, nbfft, 2), dtype=np.complex64)
    for k in range(nbfft):
        for i in range(2):
            ffttemp[:,k,i] = nfft.fft(np.squeeze(signal[k*nshift:k*nshift+npoints, i])*window)/npoints
    #fftxx = np.mean(ffttemp[:,:,0], axis=1)
    #fftyy = np.mean(ffttemp[:,:,1], axis=1)
    angles = make_ramp(0, 180, nangle)
    for k in range(nangle):
        angle = angles[k]/180.*m.pi
        fftangle = ffttemp[:,:,0]*m.cos(angle)+ffttemp[:,:,1]*m.sin(angle)
        psdangle = abs(fftangle)**2
        psd_rad[k,:] = np.mean(psdangle, axis=1)[0:npoints//2]
        cumint_rad[k,1:npoints//2] = 2*np.cumsum(np.squeeze(psd_rad[k,1:npoints//2]))

    X,Y = np.meshgrid(freq, angles)
    
    return Returnpsdrad(X, Y, psd_rad, cumint_rad)


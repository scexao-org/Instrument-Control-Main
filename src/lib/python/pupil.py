import numpy as np
import pdb

shift = np.fft.fftshift
fft   = np.fft.fft2
ifft  = np.fft.ifft2

dtor = np.pi / 180.0 # convert degrees to radians

# ==================================================================
def get_prad(fsz=512, ldim=8.0, wl=1.6e-6, pscale=10.0):
    ''' ----------------------------------------------------------
    returns the pixel size that, in a Fourier simulation,
    would result in the requested sampling requirements:

    - fsz    : size of the square Fourier array (default: 512x512)
    - ldim   : linear dimension in meters (default: 8.0)
    - wl     : wavelength in meters (default: 1.6e-6)
    - pscale : plate scale in mas / pixel (default: 10.0)
    ---------------------------------------------------------- '''
    ld = wl/ldim * 648e6 / np.pi / pscale # l/D in pixels
    return(fsz/ld/2)

# ==================================================================4
def spectral_sampling(wl1, wl2, nl, wavenum=False):
    ''' ----------------------------------------------------------
    Returns an array of regularly sampled wavelength between 
    wl1 and wl2, optionally equally spaced in wave numbers.
    - wl1: shorter wavelength (in meters)
    - wl2: longer wavelength (in meters)
    - nl: number of spectral bins
    - wavenum: True if sampling equally spaced in wave numbers
    ---------------------------------------------------------- '''
    if (not wavenum):
        return (wl1 + (wl2-wl1) * np.arange(nl) / (nl-1))
    else:
        k1, k2 = 1./wl1, 1./wl2
        kk = k1 + (k2-k1) * np.arange(nl) / (nl-1)
        return (1./kk)

# ==================================================================
def hex_pup_coords(srad, nr):
    ''' ----------------------------------------------------------
    produces a list of x,y coordinates for a hex grid made of
    nr concentric rings, with a step srad
    ---------------------------------------------------------- '''
    rmax   = np.round(nr * srad)
    xs, ys = np.array(()), np.array(())

    for i in range(1-nr, nr, 1):
        for j in xrange(1-nr, nr, 1):
            x = srad * (i + 0.5 * j)
            y = j * np.sqrt(3)/2.*srad
            if (abs(i+j) < nr):
                xs = np.append(xs, x)
                ys = np.append(ys, y)

    xx, yy = xs.copy(), ys.copy()
    xs, ys = np.array(()), np.array(())

    for i in range(xx.size): 
        if (0.5*srad <= np.sqrt(xx[i]**2 + yy[i]**2) < rmax*0.97*np.sqrt(3)/2.):
            xs = np.append(xs, xx[i])
            ys = np.append(ys, yy[i])
    return(xs, ys)

# ==================================================================4
def subaru((n,m), radius, spiders=True):
    ''' ---------------------------------------------------------
    returns an array that draws the pupil of the Subaru Telescope
    at the center of an array of size (n,m) with radius "radius".

    Symbols and values used for the description come from the
    document sent to Axsys for the fabrication of the SCExAO
    PIAA lenses, circa 2009.
    --------------------------------------------------------- '''

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

    if spiders:
        return((a+b+c+d)*e)
    else:
        return(e)

# ==================================================================4
def subaru_asym((xs, ys), radius, spiders=True, PA=0.0):
    ''' -------------------------------------------------------------
    Returns a pupil mask with an asymmetric arm that mostly follows
    the geometry of the original APF-WFS.
    ------------------------------------------------------------- '''

    # pupil description
    ro     = 0.3
    thick  = 0.5       # arm thickness (% of central)
    th = PA * dtor     # convert PA into radians
    th0 = np.mod(th, np.pi)
    xx,yy  = np.meshgrid(np.arange(xs)-xs/2, np.arange(ys)-ys/2)
    #mydist = np.hypot(yy,xx)

    h = thick*ro*radius/np.cos(th0)

    pup = subaru((xs,ys), radius, spiders)    

    a = (yy > xx*np.tan(th0) - h)
    b = (yy < xx*np.tan(th0) + h)

    #pdb.set_trace()

    if th < np.pi:
        pup = pup * (1 - (a * b * (xx > 0)))
    else:
        pup = pup *( 1 - (a * b * (xx < 0)))
    return pup

# ======================================================================
def HST((xs,ys), radius, spiders=True):
    '''Draws the HST telescope pupil of given radius in a nxm image.
    
    Returns an array of booleans, telling what is in and what is out of
    the Subaru pupil, placed at the center of an array of size (xs, ys).

    '''
    # pupil description
    pdiam, odiam = 2.4, 0.792 # tel. and obst. diameters (meters)
    thick  = 0.20             # adopted spider thickness (meters)
    beta   = 45.0*np.pi/180.  # spider angle beta
    ro     = odiam/pdiam      # fraction of aperture obsctructed

    xx,yy  = np.meshgrid(np.arange(xs)-xs/2, np.arange(ys)-ys/2)
    mydist = np.hypot(yy,xx)

    thick  *= radius/pdiam
    epsi    = thick/(2*np.sin(beta))

    a = ((xx > epsi) * (abs(np.arctan(yy/(xx-epsi))) < beta))
    b = ((xx < - epsi) * (abs(np.arctan(yy/(xx+epsi))) < beta))
    # quadrants 2-3
    c = ((yy > 0) * ((abs(np.arctan((yy-epsi)/(xx))) > beta)))
    d = ((yy < 0) * ((abs(np.arctan((yy+epsi)/(xx))) > beta)))
    # pupil outer and inner edge
    e = (((mydist) < radius) * ((mydist) > ro*radius))
    if spiders: pup = (a+b+c+d)*e
    else:       pup = e
    return pup

# ======================================================================
def segmented(sz, prad, srad, gap=False):
    '''Returns a segmented pupil image, and a list of coordinates
    for each segment.
    '''
    nr   = 50 # number of rings within the pupil

    xs = np.array(())
    ys = np.array(())

    for i in range(1-nr, nr, 1):
        for j in xrange(1-nr, nr, 1):
            x = srad * (i + 0.5 * j)
            y = j * np.sqrt(3)/2.*srad
            if (abs(i+j) < nr):
                xs = np.append(xs, x)
                ys = np.append(ys, y)
    
    print ("%d" % (xs.size))
    xx, yy = xs.copy(), ys.copy()        # temporary copies
    xs, ys = np.array(()), np.array(())  # start from scratch again
    
    for i in xrange(xx.size):
        thisrad = np.sqrt(xx[i]**2 + yy[i]**2)
        #print(thisrad)
        if (thisrad < prad):
            xs = np.append(xs, xx[i]+sz/2)
            ys = np.append(ys, yy[i]+sz/2)

    pup = np.zeros((sz,sz))
    for i in xrange(xs.size):
        pup[xs[i], ys[i]] = 1.0

    print ("%d" % (xs.size))
    return(pup)

# ======================================================================
def hex_grid(sz, prad, srad, gap=False):
    '''Returns a segmented pupil image, and a list of coordinates
    for each segment.
    '''
    nr   = 50 # number of rings within the pupil

    xs = np.array(())
    ys = np.array(())

    for i in range(1-nr, nr, 1):
        for j in xrange(1-nr, nr, 1):
            x = srad * (i + 0.5 * j)
            y = j * np.sqrt(3)/2.*srad
            if (abs(i+j) < nr):
                xs = np.append(xs, x)
                ys = np.append(ys, y)
    
    print ("%d" % (xs.size))
    xx, yy = xs.copy(), ys.copy()        # temporary copies
    xs, ys = np.array(()), np.array(())  # start from scratch again
    
    for i in xrange(xx.size):
        thisrad = np.sqrt(xx[i]**2 + yy[i]**2)
        #print(thisrad)
        if (thisrad < prad):
            xs = np.append(xs, xx[i]+sz/2)
            ys = np.append(ys, yy[i]+sz/2)

    pup = np.zeros((sz,sz))
    for i in xrange(xs.size):
        pup[xs[i], ys[i]] = 1.0

    print ("%d" % (xs.size))
    return(pup)

# ======================================================================
def kolmo(rnd1, rnd2, fc, ld0, correc=1e0, rms=0.1):
    '''Does a Kolmogorov wavefront simulation with partial AO correction.
    
    Wavefront simulation of total size "size", following Kolmogorov statistics
    with a Fried parameter "r0", with partial AO correction up to a cutoff 
    frequency "fc". Parameters are:
    
    - rnd1, rnd2 : arrays of normally distributed numbers
    - fc         : cutoff frequency (in lambda/D)
    - ld0        : lambda/D (in pixels)
    - correc     : correction of wavefront amplitude (factor 10, 100, ...)
    - std        : rms

    Note1: after applying the pupil mask, the Strehl is going to vary a bit
    Note2: one provides rnd1 and rn2 from outside so that the same experiment
           can be repeated with the same random numbers.
    '''

    ys,xs = rnd1.shape
    xx,yy  = np.meshgrid(np.arange(xs)-xs/2, np.arange(ys)-ys/2)
    myarr = shift(np.hypot(yy,xx))
    temp = np.zeros(rnd1.shape, dtype=complex)
    temp.real = rnd1
    temp.imag = rnd2

    in_fc = (myarr < (fc*ld0))
    out_fc = True - in_fc

    myarr[0,0] = 1.0 # trick to avoid div by 0!
    myarr = myarr**(-11./6.)
    myarr[in_fc] /= correc
    
    test = (ifft(myarr * temp)).real
    
    test -= np.mean(test)
    test *= rms/np.std(test)

    return test

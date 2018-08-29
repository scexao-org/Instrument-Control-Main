import pyfits as pf
import pyinotify as pn
import datetime
import numpy as np
import sys
import time
import pickle
from lockfile import FileLock
import matplotlib.pyplot as plt
from numpy.linalg import solve
import array

from scipy.optimize import leastsq
from scipy.optimize import fmin
from scipy.signal import medfilt2d as medfilt

sys.path.append('/home/scexao/lib/python/')
from scexao import *
import pdb

utcnow = datetime.datetime.utcnow

# --------------------------------
# useful variables and config bits
# --------------------------------
dms = 32 # 32 act MEMS size
plt.rcParams['image.origin']='lower'
plt.rcParams['image.cmap']='gray'
cmax = 10000.0 # camera saturation level 

# ----------------------------------------------------------------
# necessary bit to access images in continuous acquisition mode!
# ----------------------------------------------------------------
class EventHandler(pn.ProcessEvent):
    img = None

    def process_IN_CLOSE_WRITE(self, event):
        if "irdisp0.fits" in event.pathname:
            with FileLock("/tmp/irdisp0.fits"):
                try:
                    self.img = pf.getdata("/tmp/irdisp0.fits")
                except:
                    self.img = None

wm = pn.WatchManager()   # Watch Manager
mask = pn.IN_CLOSE_WRITE # watched events

handler = EventHandler()
notifier = pn.ThreadedNotifier(wm, handler)
notifier.start()
wdd = wm.add_watch('/tmp', mask, rec=True)

def get_xenics_img():
    while handler.img == None:
        time.sleep(0.01)
    img = handler.img.copy()
    handler.img = None
    return img

# ----------------------------------------------------------------

# ===========================================================================
# ===========================================================================
# ===========================================================================


def probe_field(probes, verbose=True, ncd=1):
    ''' -------------------------------------------------------
    probe the image with the provided probes (2D disp maps)
    returns #probes + 1 (ref) images
    ------------------------------------------------------- '''
    time.sleep(0.05)
    res   = []                     # empty list
    res.append(get_xenics_img())   # reference image
    k     = 3                      # disp map used (default = 3)
    npb   = np.shape(probes)[0]    # number of probes
    disp0 = get_DM_disp(k)         # original disp map

    for i in xrange(npb):
        # --- apply probe to DM ---
        if disp_2_DM(probes[i], k) == None:
            return None
        # --- get image by camera ---
        time.sleep(0.01)
        im = get_xenics_img()
        for j in range(ncd-1):
            im += get_xenics_img()
        im /= float(ncd)
        res.append(im)
        tt = utcnow()
        if verbose:
            sys.stdout.write("img %2d, %s\n" % (i,tt.isoformat(),))
            sys.stdout.flush()

    disp_2_DM(disp0, k) # restore the DM shape
    return res
        



def classic_nulling(ROI=None, ns=1, nphi=10, a0=0.05, gain=0.1, amin=0.01, 
                    nit=10, ncd=10):
    ''' -----------------------------------------------------------
    speckle nulling level 0: go after the ns brightest speckles
    ns:  number of speckles to go after
    ncd: number of coadds for detection step
    ----------------------------------------------------------- '''
    im = get_xenics_img() # initial image

    if ROI == None:
        ROI = mkROI(im.shape, (conf.fovy,conf.fovx), "left")

    for i in range(ncd-1):
        im += get_xenics_img()

    im /= float(ncd)

    (spy, spx) = spkl_finder(im*ROI, ns, 5.0)

    spl = [] # empty list of speckles properties (kx, ky, a0)

    for ii in xrange(ns):
        [kx, ky] = np.dot(conf.pix2spf, 
                          [conf.fovx-spx[ii], conf.fovy-spy[ii]])
        spl.append((kx, ky))
        print("probing for (kx,ky)=(%.2f,%.2f)" %(kx, ky,))

    gains = gain * np.ones(ns)
    # first empty round (gain=0) to eyeball amplitudes
    amps = static_iteration(spl, a0, 0.0, nphi, ROI)

    for i in range(nit):
        amps = static_iteration(spl, amps, gains, nphi, ROI)
        for ii in xrange(ns):
            if amps[ii] < amin:
                gains[ii] = 0.0
                amps[ii] = 0.0
        print np.round(amps, 3)
        print np.round(gains,3)

        if ((gains == 0.0).sum() == ns):
            break

def static_iteration(spks, a0, gain, nphi=10, ROI=None):
    ''' ------------------------------------------------------------
    new take on the speckle nulling problem. 

    Instead of running after speckles, this iteration scans for
    a predefinite list of speckle coordinates. In addition to
    applying corrections, the function returns what it believes
    to be better probe amplitudes for subsequent iterations.

    params:
    - nphi: number of modulated phases
    - spks: list of spatial frequencies (kx, ky)
    - a0:   list of amplitude probes for this iteration
    - gain: list of gains for the close-loop
    ------------------------------------------------------------ '''
    phitest = 2*np.pi * np.arange(nphi) / float(nphi)
    func = lambda (amp, phi, off, k): off + k* (
        amp**2 + a0**2 + 2*amp*a0*np.cos(phi-phitest))
    
    im = get_xenics_img() # initial image
    if ROI == None:
        ROI = mkROI(im.shape, (conf.fovy,conf.fovx), "left")

    moy  = np.mean(im[ROI > 0])
    devi = np.std(im[ROI > 0])
    maxi = im[ROI > 0].max()
    mini = im[ROI > 0].min()
    medi = np.median(im[ROI > 0])

    f = open('spk.log', 'a')
    line = "ROI (mean, med, min, max, std) = ("
    line += "%.1f, %.1f, %.1f, %.1f, %.2f\n" % \
        (moy, medi, mini, maxi, devi)
    f.write(line)
    f.close()

    ns = np.shape(spks)[0] # number of speckles in the list

    # --- ensure consistency of paramaters ---
    if np.size(gain) != ns:
        gains = np.zeros(ns)
        gains[:] = gain
    else:
        gains = np.copy(gain)

    if np.size(a0) != ns:
        a0s = np.zeros(ns)
        a0s[:] = a0
    else:
        a0s = np.copy(a0)

    a0s   = np.append(a0s,   0.0)
    gains = np.append(gains, 0.0)

    spk_props = [] # empty list of speckles properties (kx, ky, a0)

    for ii in xrange(ns):
        spk_props.append((spks[ii][0], spks[ii][1], a0s[ii]))

    data = probe_speckles(spk_props, nphi, verbose=False)
    
    # --- MODEL THE SPECKLES ---
    model = [] # empty list of speckle models
    for ii in xrange(ns):
        model.append(CAsolver(data[ii], a0s[ii]))
        model[ii][1] = model[ii][1] % (2*np.pi)
        print("Speckle properties: (amp, phi, coeff) = (%.3f, %.2f, %.1f)" % \
                  (model[ii][0],model[ii][1],model[ii][2]))
        if (model[ii][0] > 5*a0s[ii]):
            model[ii][0] = 0.0

        crit = model[ii][0]/a0s[ii] - 1.0

    # --- APPLY CORRECTIONS ---
    x,y = np.meshgrid(np.arange(dms)-dms/2, np.arange(dms)-dms/2)
    disp = np.zeros_like(get_DM_disp(3))
    for ii in xrange(ns):
        phase = 2.0*np.pi*(x*spk_props[ii][0] + y*spk_props[ii][1])+\
            model[ii][1]
        disp = gains[ii] * model[ii][0]*np.sin(phase+np.pi)
        saturation = (data[ii] > cmax).sum()

        if (saturation == 0):
            DM_add_disp(disp)
        else:
            print("SATURATION! Correction not applied!")

    return (((np.array(model))[:,0]))



def CAsolver(Iarr, a_test):
    ''' ---------------------------------------------
    Solver for the complex amplitude of a speckle.
    Relies on scipy's "fmin" procedure.
    --------------------------------------------- '''

    phi =  2*np.pi * np.arange(Iarr.size-1) / float(Iarr.size-1)
    phi0  = phi[Iarr[1:] == np.max(Iarr[1:])][0]   # initial guess for phase
    off   = Iarr[1:].mean()                        # initial guess for offset
    koeff = (Iarr[1:].mean()-Iarr[0])/a_test**2    # initial guess for coeff
    p0 = np.array([a_test, phi0, off, abs(koeff)]) # initial guess vector

    data = np.append(Iarr, a_test) # merge into one single data array
    
    modl0 = lambda p, phase: p[3] * (
        a_test**2 + 2*p[0]*a_test*np.cos(p[1]-phase))
    err0 = lambda p, phase, intens: (np.abs(modl0(p, phase)-intens)).sum()

    trial,nmax = 0, 1000
    klook = True
    while klook:
        soluce = fmin(err0, p0, args=(phi, Iarr[1:]-Iarr[0]),
                      maxiter=100000, disp=0)
 
        if soluce[0] > 1.0: p0[0] /= 2.0 # 
        if soluce[0] < 0.0: p0[1] += np.pi/2
        else: klook = False
        trial+=1
        if trial == nmax:
            print "Stopped trying after %d times" % (nmax,)
            return np.array([0.0, 0.0, 0.0])
    soluce[1] = soluce[1] % (2*np.pi)

    debug = False#True#

    if debug ==True:
        print("amp = %.2f, phase = %.2f, coeff = %.2f" % \
                  (soluce[0], soluce[1], soluce[2]))
        plt.plot(Iarr[1:]-Iarr[0])
        plt.plot(Iarr[1:]-Iarr[0], 'bo')
        plt.plot(modl0(soluce,phi), 'r')
        #pdb.set_trace()
    return soluce

def probe_speckles(spks, nmod=4, verbose=True):
    ''' ------------------------------------------------------------
    Probe given list of speckles properties.

    Each speckle is a 3-element tuple :
    - (kx, ky, amplitude)

    Optional arguments:
    - nmod: number of phase modulation steps (between 0 and 2pi)
            default is 4 (0, pi/2, pi, 3pi/2)

    Returns: a list of arrays with interferences

    Example:
    
    probe_speckles([(kx1, ky1, ap], (kx2, ky2)])
    ------------------------------------------------------------ '''
    nspk = np.size(spks)

    # --- create the DM probes ---
    prbs = [] # empty list of DM probes
    for i in xrange(nmod):
        phi = 2.0* np.pi / float(nmod) * i
        spp = [] # empty list of SpkProbe objects
        for ii, spk in enumerate(spks):
            spp.append(SpkProbe(spk[0], spk[1], spk[2], phi))
        prbs.append(mk_probe(spp))

    # --- get the data ---
    a = probe_field(prbs, verbose)
    xs,ys = a[0].shape[1], a[0].shape[0]

    # --- extract the speckle intensity functions ---
    res = [] # empty list of results
    irad = 3.0
    for ii, spk in enumerate(spks):
        [px, py] = [conf.fovx, conf.fovy] - \
            np.dot(conf.spf2pix, [spk[0], spk[1]])
        spmask = cmask(ys, xs, py, px, irad)
        spf = np.zeros((nmod+1))

        # note for later: the simple mean can most certainly
        # be replaced by a quantity more robust to noise....

        for i in range(nmod+1):
            spf[i] = np.mean((a[i][spmask>0])) # speckle intef. flux
        res.append(spf)
    return res

# ================================================================
#                       DEBUG and TESTS
# ================================================================
#DM_flat()

if __name__ == "__main__":
    conf = Config()
    conf.read_conf_file()
    
    myROI = mkROI((256,320), "left")
    amp0 = 0.05

    pdb.set_trace()

    for i in range(20):
        classic_nulling(myROI, nphi=30, ns=10, a0=0.03, gain=0.5, amin=0.01, 
                        nit=5, ncd=10)

    print("STOP!")
    pdb.set_trace()

    amp = static_iteration([(-0.3, 0.3)], amp0, gain, nphi=10, ROI=myROI)

    for i in range(5):
        amp = static_iteration([(-0.3, 0.3)], amp, 0.3, nphi=10, ROI=myROI)
        if amp < 0.01:
            break

        print("INTERATION %d, amp = %.3f" % (i, amp))

        #print("--- > a0 = %.2f" % (amp0,))

''' =================================================================
Notes for later: 
- check for saturation / low SNR in ROI
- measure the speckle contrast as a function of (kx,ky, amplitude)
  for a flat wavefront, and check that it is the same with an
  aberrated wavefront.
- kill da spekal!
================================================================= '''

# just re-wrote these this morning.... (July 15, 2013)
# they replicate something already well written last year...

# --------------------------------------------------------------
#          low-level access to the DM disp files
# --------------------------------------------------------------
def get_dm_shape(fname):
    with FileLock(fname):
        try:
            a = array.array('f')
            a.fromfile(open(fname), 50*50)
            disp = np.array(np.split(np.array(a), 50))
        except:
            disp = None
            print("Problem!")
    return(disp)

def set_dm_shape(fname, disp):
    temp = disp.flatten().tolist()
    a = array.array('f')
    a.fromlist(temp)
    with FileLock(fname):
        try:
            a.tofile(open(fname, 'w'))
        except:
            print('Could not set %s' % (fname,))
            return(False)
    return(True)

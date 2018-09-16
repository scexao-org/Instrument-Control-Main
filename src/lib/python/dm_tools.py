import os
import mmap
import struct
import pdb
import numpy as np
import pyfits as pf
from scipy.signal import medfilt2d as medfilt
from lockfile import FileLock
import array
import binascii

dms = 50 # 2k-DM diameter (in actuators)

class SpkProbe():
    '''--------------------------------------------------
    Speckle probe abstraction, for speckle nulling.

    Follows the convention established by OG and FM:
    kx, ky: (x,y) spatial frequencies on the DM
    amp   : amplitude in microns
    phi   : phase 
    -------------------------------------------------- '''
    def __init__(self,kx,ky,amp,phi):
        self.kx = kx
        self.ky = ky
        self.amp = amp
        self.phi = phi

# ====================================================================
# ====================================================================

def mk_probe(spks):
    ''' --------------------------------------------------
    create a 2d disp map from a list of speckle probes
    -------------------------------------------------- '''
    x,y = np.meshgrid(np.arange(dms)-dms/2, np.arange(dms)-dms/2)

    res = get_DM_disp(3)
    for i in range(np.size(spks)):
        phase = 2.0*np.pi*(x*spks[i].kx + y*spks[i].ky)+spks[i].phi
        res += spks[i].amp*np.sin(phase)
    return res

def DM_add_disp(disp, channel=3):
    ''' ---------------------------------------------------------------
    Adds a displacement map disp to the one current on the provided 
    channel of the DM. Default channel is #3.
    This function is useful for applying actual corrections to the
    DM shape.
    --------------------------------------------------------------- '''
    disp0 = get_DM_disp(channel)
    disp_2_DM(disp0 + disp)
    return 0

def DM_add_poke((x0,y0), a0, channel=3):
    ''' ------------------------------------------------------------
    Pokes one single actuator at the coordinate (x0, y0)
    with an amplitude a0 in microns
    ------------------------------------------------------------ '''
    disp0 = get_DM_disp(channel)
    disp = np.zeros_like(disp0)
    disp[int(x0),int(y0)] = a0
    disp_2_DM(disp0 + disp)
    return 0


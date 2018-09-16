#!/usr/bin/env python

import pyfits as pf
import numpy as np
import time

import matplotlib.pyplot as plt

import os
import sys
home = os.getenv('HOME')
sys.path.append(home+'/src/lib/python')
from scexao_shm import shm


plt.ion()
plt.show()

# ---------------------------------------------------------
camid = 2

etimes = np.array([1, 2, 5, 10, 20, 50, 100, 200, 500, 
                   1000, 2000, 5000, 10000, 20000, 50000])

ys, xs = 256, 320

imc = np.zeros((15, ys, xs))
drk = np.zeros((15, ys, xs))

for i, etime in enumerate(etimes):
    drk[i] = pf.getdata("darks_%06d.fits" % (etime,)).astype('float')
    imname = "null_rigt_%06d.fits" % (etime,)
    try:
        imc[i]  = pf.getdata(imname).astype('float') - drk[i]
    except:
        print 'missing frames?'

v1 = 100
v2 = 10000
hdim = np.zeros((ys, xs))
hdim = imc[0]
hdim[imc[0] < v1] = 0.0

for i in xrange(11):
    test1 = (v1 < imc[i]) * (imc[i] < v2) 
    test2 = (v1 < imc[i+1]) * (imc[i+1] < v2) 
    test = test1 * test2

    coeff = (imc[i+1]/imc[i])[test].mean()
    hdim *= coeff
    hdim += imc[i+1]
    hdim /= 2.0
    hdim[imc[i+1] < v1] = 0.0


pf.writeto("hd_null_right.fits", hdim/hdim.max(), clobber=True)


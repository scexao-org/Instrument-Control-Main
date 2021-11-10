#!/usr/bin/env python

import os, sys, time
from astropy.io import fits as pf
import numpy as np
import math as m
import array
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.ticker import LogFormatterMathtext
import numpy.fft as nfft
import scipy.signal as signal
import re
import glob
from scipy.fftpack import fftfreq
from scipy.fftpack import fftshift
from scipy.signal import medfilt2d
from scipy.ndimage import rotate
from scipy.signal import tukey
from scipy.signal import correlate2d
from scipy.interpolate import griddata
from scipy.interpolate import interp2d
from skimage import color, data, restoration
from skimage.morphology import watershed
from skimage.feature import peak_local_max
from scipy import ndimage as ndi
from skimage.segmentation import random_walker
from skimage import measure
from astropy.modeling import models, fitting
from astropy.modeling.models import custom_model
import copy
from scipy.ndimage import shift
from scipy.ndimage import median_filter
home = os.getenv('HOME')
sys.path.append(home+'/src/lib/python/')
import vibration as vib
import image_processing as impro
import img_tools as imtools
from hcipy import * 
from tqdm import tqdm

plt.ion()

def meanim(image_list, i0, ni):
    for i in range(ni):
        imagec = pf.getdata(image_list[i0+i])
        if i == 0:
            imagem = np.mean(imagec*(imagec!=65535), axis=0)
        else:
            imagem += np.mean(imagec*(imagec!=65535), axis=0)
    imagem /= float(ni)
    return(imagem)

path = '/media/data/20210929/kcamlog/' 
image_list = glob.glob(path+'kcam_*.fits') 
image_list.sort() 
ipin = 8                                                                                                  
npin = 1                                                                                                  
idark = 9                                                                                                 
ndark = 1                                                                                                 
rm = 7 

dark = meanim(image_list, idark, ndark)
pin = meanim(image_list, ipin, npin)
pin -= dark
posst,xoff,yoff,strehlv,dia_ring,distco,angleco,contrastco = impro.binary_processing(pin, saveplot=False, retroinj=True, strehlcalc = False, verbose=False, camera = "Buffycam",rm=rm,nst=1)

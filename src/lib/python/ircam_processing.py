#!/usr/bin/env python

import os, sys, time, glob
from astropy.io import fits as pf
import numpy as np
import math as m
import array
import re
import copy
from matplotlib.animation import ArtistAnimation
import matplotlib.pyplot as plt
home = os.getenv('HOME')
sys.path.append(home+'/src/lib/python/')
import colormaps as cmaps


# ========= EXTRACT SERIES OF IMAGES ====================
#========================================================
class Returncube(object):
    def __init__(self, cube, expT):
        self.cube = cube
        self.expT = expT

def extract_cube(date, hh, mm, ss, nim):
    
    path = '/media/data/%s/ircam1log/'% (date,)
    image_list = glob.glob(path+'ircam1*.fits')
    
    image_list.sort()
    
    ncubes = len(image_list)
    times = np.zeros((ncubes,3))
    
    for i in range(ncubes):
        p, imagesf = os.path.split(image_list[i])
        name_split = imagesf.split(':')
        times[i,0] = int(name_split[0][7:])
        times[i,1] = int(name_split[1])
        times[i,2] = float(name_split[2][:12])
    
    times2 = times[:,0]*3600+times[:,1]*60+times[:,2]
    indexes = np.where(times2 <= hh*3600+mm*60+ss)[0]
    
    im_index = indexes[-1]
    

    f = open(image_list[im_index].replace('fits', 'txt'))
    timestamps = f.readlines()

    nimages = len(timestamps)
    times = np.zeros((nimages,3))
    
    for i in range(nimages):
        name_split = timestamps[i].split()[0].split(':')
        times[i,0] = int(name_split[0])
        times[i,1] = int(name_split[1])
        times[i,2] = float(name_split[2])
    
    times2 = times[:,0]*3600+times[:,1]*60+times[:,2]
    indexes = np.where(times2 >= hh*3600+mm*60+ss)[0]
    
    start_index = indexes[0]
    
    images = pf.getdata(image_list[im_index])
    cubesize = np.array(images.shape)
    cubesize[0] = nim
    cube = np.zeros(cubesize)
    expT = np.zeros(nim)
    imin = 0
    k = 0
    
    while imin < nim:
        if k != 0:
            images = pf.getdata(image_list[im_index+k])
            nimages = images.shape[0]
        expTtmp = np.loadtxt(image_list[im_index+k].replace('fits', 'txt'),usecols=(4,))
        ntmp = min(nim-imin, nimages-start_index)
        cube[imin:imin+ntmp,:,:] = images[start_index:start_index+ntmp,:,:]
        expT[imin:imin+ntmp] = expTtmp[start_index:start_index+ntmp]
        start_index = 0
        k += 1
        imin += ntmp
        
    return Returncube(cube, expT)


# ========= EXTRACT SPECIFIC CUBE =======================
#========================================================
class Returncube(object):
    def __init__(self, cube, expT):
        self.cube = cube
        self.expT = expT

def extract_cube_path(date, cube_name):
    
    path = '/media/data/%s/ircam1log/%s'% (date,cube_name)
    
    cube = pf.getdata(path)
    
    expT = np.loadtxt(path.replace('fits', 'txt'),usecols=(4,))
        
    return Returncube(cube, expT)

# ========= EXTRACT SPECIFIC CUBES FROM LIST ============
#========================================================
class Returncube(object):
    def __init__(self, cube, expT):
        self.cube = cube
        self.expT = expT

def extract_cube_path(date, cube_list):

    n_cubes = len(cube_list)
    
    for i in range(n_cubes):
        path = '/media/data/%s/ircam1log/%s'% (date,cube_list[i])
    
        if i == 0:
            cube = pf.getdata(path)
            
            expT = np.loadtxt(path.replace('fits', 'txt'),usecols=(4,))
        else:
            cube = np.concatenate((cube, pf.getdata(path)), axis = 0)
            
            expT = np.concatenate((expT, np.loadtxt(path.replace('fits', 'txt'),usecols=(4,))), axis=0)        

    return Returncube(cube, expT)


# ====== DARK SUBTRACT CUBE ======================================
# ================================================================

def dark_subtract_cube(date, time, struct):
    
    pathd = '/media/data/%s/ircam1log/darks/%s/'% (date, time)
    dark_list = glob.glob(pathd+'dark_*fits')
    
    dark_list.sort()
    
    ndark = len(dark_list)
    print ndark
    expT_darks = np.zeros(ndark)
    
    for i in range(ndark):
        p, darkf = os.path.split(dark_list[i])
        expT_darks[i] = re.search(r'\d+', darkf).group(0)
        darks = pf.getdata(dark_list[i])
        if i == 0:
            dark_m = np.zeros((ndark, darks.shape[0], darks.shape[1]))
        dark_m[i,:,:] = darks

    cube_ds = np.zeros_like(struct.cube)
    nim = cube_ds.shape[0]
    for k in range(nim):
        ind = np.where(expT_darks == struct.expT[k])
        cube_ds[k,:,:] = struct.cube[k,:,:]-dark_m[ind,:,:]

    return cube_ds

# ====== SAVE DARK SUBTRACTED CUBE ===============================
# ================================================================

def save_ds_cube(date, hh, mm, ss, nim, dated, timed, path):
    
    struct = extract_cube(date, hh, mm, ss, nim)
    
    cube_ds = dark_subtract_cube(dated, timed, struct)
    
    pf.writeto(path, cube_ds, clobber=True)

    return None

# ====== SAVE DARK SUBTRACTED CUBE FROM LIST =====================
# ================================================================

def save_ds_cube_path(date, cube_list, dated, timed, path):
    
    struct = extract_cube_path(date, cube_list)
    
    cube_ds = dark_subtract_cube(dated, timed, struct)
    
    pf.writeto(path, cube_ds, clobber=True)

    return None

# ====== SAVE DARK SUBTRACTED AVERAGED IMAGE =====================
# ================================================================

def save_dsa_image(date, hh, mm, ss, nim, dated, timed, path):
    
    struct = extract_cube(date, hh, mm, ss, nim)
    
    cube_ds = dark_subtract_cube(dated, timed, struct)
    
    image = np.mean(cube_ds, axis=0)
    pf.writeto(path, image, clobber=True)

    return None


# ====== SAVE VIDEO FROM LIST ====================================
# ================================================================

def save_ds_video_path(date, cube_list, dated, timed, path):
    
    #plt.ion()
    f1 = plt.figure(figsize=(3,3))
    ax = f1.add_subplot(111)

    struct = extract_cube_path(date, cube_list)
    
    cube_ds = dark_subtract_cube(dated, timed, struct)
    
    cube_ds = cube_ds[400:,:,:]
    images = []
    texts = ["AO188 off, SCExAO off", "AO188 on, SCExAO off", "AO188 on, SCExAO on"]
    
    for i in xrange(cube_ds.shape[0]):
        print i
        imtemp = cube_ds[i,68:188,100:220]
        imtemp = np.log10(imtemp)
        imtemp = np.nan_to_num(imtemp)
        im = ax.imshow(imtemp, cmap = cmaps.inferno, clim=(0.0, 4.0), interpolation="bicubic")
        if i < 759:
            j = 0
        elif (i >758) and (i < 1600):
            j = 1
        else:
            j = 2
        ax.annotate(texts[j], xy=(10,110), xytext=(10,110), color='white')

        images.append((im,))
        
    anim = ArtistAnimation(f1, images, interval=25, blit=False)
    anim.save(path,dpi=150)

    return None



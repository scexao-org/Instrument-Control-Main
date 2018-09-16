#!/usr/bin/env python

#This script can be used to prepare images to make videos from raw images.
import os, sys, time, glob
import pyfits as pf
import numpy as np
from matplotlib import *
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from scipy.misc import imsave
import pdb

home = os.getenv('HOME')
sys.path.append(home+'/src/lib/python/')
import ircam_processing as improc
import hot_pixels as hp

#------- Importing data at a given UT -----------#
datain=improc.extract_cube(20151031, 11, 22, 15, 10)
#date - UT date e.g. 20151031
#hh   - hour 2 digits
#mm   - minutes 2 digits
#ss   - seconds can be floating point number
#nim  - number of images to look at
#Returns the data and a list of corresponding exposure times


#------ Subtracting a dark from each frame ------#
dataout=improc.dark_subtract_cube(20151031, 121818, datain)
#date  - UT date of the darks
#time  - UT time of the darks closest to the data
#struct - the data from the previous function is an input
zsize, ysize, xsize = np.shape(dataout)



#------ Hot pixel removal from each frame -------#
cleanim=np.zeros_like(dataout)
for i in range(zsize):
    useless,cleanim[i]=hp.find_outlier_pixels(dataout[i])


#------ Plot an image to inspect it -------------#
#mycmap = cm.viridis
plt.figure()
plt.imshow(cleanim[0])


#------ Saving data cube of images --------------#
#filename = 'Cleaned_cube'
#pf.writeto('/home/scexao/Documents/Nems_data/Chuck_videos/20151031/'+filename+'.fits', cleanim, clobber=True)



#--- Saving images to png with appropriate color scale ---#
index = 0
mycmap = cm.jet # cm.gray # cm.hot

'''
for j in xrange(zsize):
    snap = cleanim[j]
    snap -= np.median(snap)
    snap[snap < 0.0] = 0.0
    snap /= snap.max()
    #plt.figure()
    #plt.imshow(snap**0.5)
    #imsave('/home/scexao/Documents/Nems_data/Chuck_videos/20151031/im%06d.png' % (index,), mycmap(snap**0.5))
    index+=1
'''

#------------ Converting to an mp4 ------------#
#Once the pngs have been created use the following command in the terminal
#avconv -r 200 -i im%06d.png -b:v 1000k -c:v libx264 myAwesomeMovie.mp4
#framerate can be changed with the number 200


#Takes a fits file and saves a video from it

import pyfits
import matplotlib.pyplot as plt
import numpy as np
import pdb
#from scipy.stats import mode
import os
#import time

dir = 'images/'
filename = 'saphira_14:10:04.159651175_cleaned.fits'
print "Reading image..."
img = pyfits.getdata(dir+filename)#[2000:3000]
print "Image read. Size is ", np.shape(img)

mymin = np.sort(img[0].flatten())[np.size(img[0])*.01]
mymax = np.sort(img[0].flatten())[np.size(img[0])*.999]
for z in range(np.shape(img)[0]):
    plt.imshow(img[z], interpolation='none', vmin=mymin, vmax=mymax)
    plt.savefig('imagestovid/img%03d.png' % (z,))
    plt.clf()

os.system('avconv -r 30 -i imagestovid/img%03d.png -b:v 1000k -c:v libx264 myAwesomeMovie.mp4') #30 fps. %03d means 3 digit numerical extension of filenames

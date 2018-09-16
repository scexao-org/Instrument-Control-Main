#!/usr/bin/env python

''' 
OBJECTIVE: 
---------

1) Creating Subaru Pupil
2) Creating Lyot mask compatible with Four Quadrant Phase Mask

INPUTS:
--------

n, m         : dimensions of the array in pixels
prad         : radius of the subaru telescope in pixels
pdiam, odiam : subaru telescope pupil's actual outer and obscuration diameter (in meters) respectively
thick        : actual thickness of the spider arms (in meters)
offset       : actual offset of the spider arms from the center of the obscuration (in meters)
beta         : actual angle of the spider arms (in degree) 

OUTPUTS:
--------

pup  : subaru telescope pupil
lyot : lyot mask compatible with four quadrant phase mask


AUTHOR:
-------

Garima Singh  :  Version 0.1 of 11 January 2013

--------------------------------------------------------------------------------------------------'''

#--------------------------------------------------------------
# importing necessary in-built Python's libraries and packages 
#--------------------------------------------------------------

import numpy as np
from numpy.fft import fftshift as shift
import pyfits as pf
import matplotlib.pyplot as plt


#------------------------------------------------------------------------
# dist() functions is the Hacked up adaptation of the IDL dist() command
#------------------------------------------------------------------------

def dist((n,m)):

    '''Hacked up adaptation of the IDL dist command
    '''
    x2=np.roll((np.arange(n, dtype=float)-n/2)**2, n/2)
    y2=np.roll((np.arange(m, dtype=float)-m/2)**2, m/2)
    a=np.empty((n,m))
    for i in np.arange(m):
        a[:,i]=x2
    for i in np.arange(n):
        a[i,:]+=y2
    return np.sqrt(a)


#--------------------------------------------------------------
# Subaru_pupil function returns the Subaru Telescope Pupil 
#--------------------------------------------------------------

def Subaru_pupil((nn,mm), prad):
    '''Returns an array describing the pupil of the Subaru Telescope

    parameters:
    ----------
    - (nn, mm): dimensions of the array in pixels
    - prad: radius of the pupil in pixels    '''

#-------------------
# pupil description
#-------------------

    pdiam, odiam = 7.92, 2.5 #2.3         # tel. and obst. diameters (meters)
    thick  = 0.23                         # adopted spider thickness (meters)
    offset = 1.278                        # spider intersection offset (meters)
    beta   = 51.75*np.pi/180              # spider angle beta

    ro  = odiam/pdiam                     # fraction of aperture obsctructed
 
    xx     =   np.outer(np.ones(nn), np.arange(mm)) - mm/2
    yy     =   np.outer(np.arange(nn), np.ones(mm)) - nn/2

    mydist = dist((nn, mm))

#--------------------------------------------------
# scaled values of the pupil's parameters in pixels
#---------------------------------------------------

    thick  *= prad/pdiam
    offset *= prad/pdiam
    epsi    = thick/(2*np.sin(beta))

#--------------------------------------
# Spider arms definition: quadrants 1-4
#--------------------------------------

    a = ((xx > offset + epsi) * (abs(np.arctan(yy/(xx-offset-epsi))) < beta))
    b = ((xx < -offset - epsi) * (abs(np.arctan(yy/(xx+offset+epsi))) < beta))

#---------------
# quadrants 2-3
#---------------

    c = ((yy > 0.0) * ((abs(np.arctan(yy/(xx-offset+epsi))) > beta) +
                       (abs(np.arctan(yy/(xx+offset-epsi))) > beta)))
    d = ((yy < 0.0) * ((abs(np.arctan(yy/(xx-offset+epsi))) > beta) +
                       (abs(np.arctan(yy/(xx+offset-epsi))) > beta)))

#----------------------------
# pupil outer and inner edge
#----------------------------

    e   = ((shift(mydist) < prad) * (shift(mydist) > ro*prad))
    pup = (a+b+c+d)*e

#    pf.writeto("/Users/Keha/Documents/Python_programming/phase_coronagraphy/fits_images/pupil.fits", pup* np.ones([1024,1024]), clobber=True)

    return pup

#-------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------


#----------------------------------------------------------------------
# Square_Lyot function returns the lyot mask for Subaru Telescope Pupil 
#----------------------------------------------------------------------


def Square_Lyot((nn,mm), prad):

    '''Returns an array describing the square lyot for the Subaru Telescope pupil 

    parameters:
    ----------
    - (nn, mm): dimensions of the array in pixels
    - prad: radius of the pupil in pixels    '''
    
    #-------------------
    # pupil description
    #-------------------

    pdiam, odiam = 7.92, 2.3     # tel. and obst. diameters (meters)
    thick  = 0.23                # spider thickness (meters), oversize by 2%
    offset = 1.278               # spider intersection offset (meters)
    beta   = 51.75*np.pi/180     # spider angle beta

    ro  = odiam/pdiam            # fraction of aperture obsctructed
  
    xx     =   np.outer(np.ones(nn), np.arange(mm)) - mm/2
    yy     =   np.outer(np.arange(nn), np.ones(mm)) - nn/2

    mydist = dist((nn, mm))

    #--------------------------------------------------
    # scaled values of the pupil's parameters in pixels
    #---------------------------------------------------

    thick   = thick* 1.5 * (prad/pdiam) 
    offset *= prad/pdiam
    epsi    = thick/(2*np.sin(beta))
    

    #---------------------------------------------------
    # oversized spider arms for lyot mask: quadrants 1-4
    #----------------------------------------------------
    
    a = ((xx > offset + epsi) * (abs(np.arctan(yy/(xx-offset-epsi))) < beta))
    b = ((xx < -offset - epsi) * (abs(np.arctan(yy/(xx+offset+epsi))) < beta))

    #--------------
    # quadrants 2-3
    # --------------

    c = (((yy > 0.0) * ((abs(np.arctan(yy/(xx-offset+epsi))) > beta) +
                       (abs(np.arctan(yy/(xx+offset-epsi))) > beta))))
    d = (((yy < 0.0) * ((abs(np.arctan(yy/(xx-offset+epsi))) > beta) +
                       (abs(np.arctan(yy/(xx+offset-epsi))) > beta))))
    
    #-------------------------------------------------------------------
    # sides of the square obscuration for lyot oversized by 12 %
    #-------------------------------------------------------------------

    sq = ro*prad*1.12           

    #---------------------
    # Lyot mask outer edge
    #---------------------

    e  = ((shift(mydist) < prad * 0.95))  
         
    lyot = (a+b+c+d)* e

    #---------------------
    # Lyot mask inner edge
    #---------------------

    no,mo=np.shape(lyot)
    Xo=no/2
    Yo=mo/2
    sq=int(np.ceil(sq))

    for io in range ((Xo-sq),(Xo+sq)):
        for jo in range ((Yo-sq),(Yo+sq)):
            lyot[io,jo]=0
         

    return lyot

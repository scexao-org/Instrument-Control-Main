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
import pyfits as pf
import matplotlib.pyplot as plt


#------------------------------------------------------------------------
# dist() functions is the Hacked up adaptation of the IDL dist() command
#------------------------------------------------------------------------

def dist((n,m),(offsetn,offsetm)=(0,0)):

    '''Hacked up adaptation of the IDL dist command
    '''
    x2=(np.arange(n, dtype=float)-n/2+offsetn)**2
    y2=(np.arange(m, dtype=float)-m/2+offsetm)**2
    a=np.empty((n,m))
    for i in np.arange(m):
        a[:,i]=x2
    for i in np.arange(n):
        a[i,:]+=y2
    return np.sqrt(a)


#--------------------------------------------------------------
# Subaru_pupil function returns the Subaru Telescope Pupil 
#--------------------------------------------------------------

def Subaru_pupil((nn,mm), prad, badactuator=False, spider2=False):
    '''Returns an array describing the pupil of the Subaru Telescope

    parameters:
    ----------
    - (nn, mm): dimensions of the array in pixels
    - prad: radius of the pupil in pixels    
    - badactuator: (boolean) add the 2 bad actuators in the pupil
    - spider2: (boolean) add the secondary spider arm masking the bad actuator'''

#-------------------
# pupil description
#-------------------

    pdiam, odiam = 7.92, 2.4              # tel. and obst. diameters (meters)
    thick  = 0.35                         # adopted spider thickness (meters)
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

    e   = (mydist < prad) * (mydist > ro*prad)
    pup = (a+b+c+d)*e

    if badactuator:
        rb = 0.08
        db1 = 0.46
        xb1 = offset+db1*prad*np.cos(beta)
        yb1 = db1*prad*np.sin(beta)
        bdist1 = dist((nn, mm),(-yb1,-xb1))
        f = bdist1 > rb*prad
        db2 = 0.75
        offset2 = 0.34
        xb2 = (offset2-db2*np.cos(beta))*prad
        yb2 = -db2*np.sin(beta)*prad
        bdist2 = dist((nn, mm),(-yb2,-xb2))
        g = bdist2 > rb*prad
        pup *= f*g
    
        if spider2:
            thick2 = 0.18
            thick2 *= prad/pdiam
            offset2 *= prad
            epsi2 = thick2/(2*np.sin(beta))
            h = (np.arctan(yy/(xx-offset2+epsi2))<beta)*(yy<=-ro*prad/2)*(xx<=offset2)+(yy>-ro*prad/2)+(xx>offset2)+(np.arctan(yy/(xx-offset2-epsi2))>beta)
            pup *= h

    return pup

#-------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------

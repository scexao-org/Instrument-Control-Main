#
# fitsutils.py -- Miscellaneous FITS/numpy utility functions
#
# Takeshi Inagaki  (tinagaki@naoj.org)
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Dec 29 11:25:52 HST 2010
#]
#
"""
This module provides various utility functions for manipulating FITS
files.
"""

import sys, os, time
import time
import re
import math
from types import *

import numpy
import pyfits

import radec
from SOSS.status import STATNONE, STATERROR
# TODO: This should be in a centralized configuration file!
from subaru import SUBARU_LATITUDE_DEG


class ParameterError(Exception):
    pass
    

def validateArgs(*args):
    """Check that there are no erroneous values in the arguments.
    Raise an ParameterError if there are.
    """
    
    if ((None in args)  or (STATNONE in args) or (STATERROR in args)):
        raise ParameterError("Invalid parameter values: %s" % str(args))




#########################################
#   DSS  WCS calculation
#########################################

def get_keyword_values(hdr, wcs):
    ''' fetch indispensable fits-keyword values from dss fits  for wcs calculation '''
                
    for key in wcs.keys():
        try:
            wcs[key]=hdr[key]
        except:
            #print 'not in fits', key    
            pass


def update_dss_fits(wcs_add, hdr, logger=None):
    ''' update fit keywords '''
    
    update_list=['CTYPE1','CTYPE2','RADESYS','CRPIX1','CRPIX2','CRVAL1','CRVAL2','CDELT1',
              'CDELT2','CROTA1', 'CROTA2','CD1_1','CD1_2','CD2_1','CD2_2',
              'PC001001','PC001002','PC002001','PC002002','LONPOLE','EQUINOX']

    
    for w in update_list:
        #print wcs_add[w], wcs_add[w]['val'], wcs_add[w]['comment']
        try:
            if logger:
                logger.debug('key<%s> val<%s> cmt<%s>' %(w, wcs_add[w]['val'], wcs_add[w]['comment']))
            hdr.update(w, wcs_add[w]['val'], wcs_add[w]['comment'])
        except:
            if logger:
                logger.debug('key<%s> default_val<%s> cmt<%s>' %(w, wcs_add[w]['val'], wcs_add[w]['comment']))
            pass
    
    hdr.add_comment("WCS keywords are appended by python function 'append_WCS'") 
    hdr.add_comment('written by OCS Team(Subaru Telescope)') 
    hdr.add_comment("'append_WCS' is implemented based on WCSTools coded by Doug Mink(SAO)") 

def append_wcs(file_name, logger=None):    
    
    wcs={'NAXIS1':0, 'NAXIS2':0, 'PLTRAH':0, 'PLTRAM':0,'PLTRAS':0,
         "PLTDECSN":'', "PLTDECD":0, "PLTDECM":0, "PLTDECS":0,
         'EQUINOX':0, 'PLTSCALE':0,'CNPIX1':0,'CNPIX2':0,
         "XPIXELSZ":0, "YPIXELSZ":0, "PPO3":0, "PPO6":0,
         "AMDX1":0, "AMDX2":0, "AMDX3":0, "AMDX4":0,
         "AMDX5":0, "AMDX6":0,"AMDX7":0, "AMDX8":0,
         "AMDX9":0, "AMDX10":0, "AMDX11":0, "AMDX12":0, "AMDX13":0,
         "AMDY1":0, "AMDY2":0, "AMDY3":0, "AMDY4":0,
         "AMDY5":0, "AMDY6":0,"AMDY7":0, "AMDY8":0,
         "AMDY9":0, "AMDY10":0, "AMDY11":0,"AMDY12":0, "AMDY13":0, 
         
         'XINC':0, 
         'CRPIX1':0, 'CRPIX2':0, "CRVAL1":0, "CRVAL2":0,}
    

    wcs_add={'CTYPE1': {'val':'RA---TAN', 'comment': "Projection type of 1st axis"}, #0
             'CTYPE2': {'val':'DEC--TAN', 'comment': "Projection type of 2nd axis"}, #1
             'RADESYS': {'val':'FK5', 'comment': "Coordinate System"},               #2
             'CRPIX1': {'val':0, 'comment':"1st Reference Pixel Coordinate"},        #3
             'CRPIX2': {'val':0, 'comment':"2nd Reference Pixel Coordinate"},        #4
             'CRVAL1': {'val':0, 'comment': "1st Reference Pixel Value"},            #5
             'CRVAL2': {'val':0, 'comment': "2nd Reference Pixel Value"},            #6
             'CDELT1': {'val':0, 'comment': "Increment for 1st axis"},               #7
             'CDELT2': {'val':0, 'comment': "Increment for 2nd axis"},               #8
             'CROTA1': {'val':0, 'comment': "Rotation angle of 1st axis"},           #9
             'CROTA2': {'val':0, 'comment': "Rotation angle of 2nd axis"},           #10 
             'CD1_1': {'val':0, 'comment': "CD Matrix"},                             #11
             'CD1_2': {'val':0, 'comment': "CD Matrix"},                             #12
             'CD2_1': {'val':0, 'comment': "CD Matrix"},                             #13
             'CD2_2': {'val':0, 'comment': "CD Matrix"},                             #14
             'PC001001': {'val':0, 'comment': "PC Matrix"},                          #15
             'PC001002': {'val':0, 'comment': "PC Matrix"},                          #16
             'PC002001': {'val':0, 'comment': "PC Matrix"},                          #17
             'PC002002': {'val':0, 'comment': "PC Matrix"},                          #18
             'LONPOLE': {'val':180.0, 'comment': "Rotation of Longitude Pole"},
             'EQUINOX':{ 'val':2000.0, 'comment': "EQUINOX for this coordinate description"}}
    
    errmsg=[]
   
    try:
        hdulist=pyfits.open(file_name, mode='update')
    except IOError,e:
        errmsg.append("<P><B>ERROR:</B> %s.\n" %(e))
        if logger:
            logger.debug('fits open error<%s>' %e)        
        #print errmsg
        return errmsg
    hdr=hdulist[0].header
    get_keyword_values(hdr, wcs)
    
    
    wcs_add['CRPIX1']['val']= 0.5 * wcs["NAXIS1"]
    wcs_add['CRPIX2']['val']= 0.5 * wcs["NAXIS2"]
    
    wcs['CRPIX1']=wcs_add['CRPIX1']['val']
    wcs['CRPIX2']=wcs_add['CRPIX2']['val']
    
    if wcs['EQUINOX'] == 1950.0:
        #print 'EQUINOX FK4' , wcs['EQUINOX']
        wcs_add['RADESYS']['val']='FK4'
    else:
        #print 'EQUINOX FK5' , wcs['EQUINOX']
        wcs_add['RADESYS']['val']='FK5'
    
    ra0, dec0=dsspos(wcs_add['CRPIX1']['val'], wcs_add['CRPIX2']['val'], wcs, logger)
   
    wcs_add['CRVAL1']['val']=ra0
    wcs_add['CRVAL2']['val']=dec0
    wcs['CRVAL1']=ra0
    wcs['CRVAL2']=dec0
   
    #ra1, dec1= dsspos(wcs_add['CRPIX1']['val'], wcs_add['CRPIX2']['val']+1.0, wcs)
    #yinc=dec1-dec0
    #wcs['YINC']=dec1-dec0
    ra1, dec1= dsspos(wcs_add['CRPIX1']['val']+1.0, wcs_add['CRPIX2']['val'], wcs, logger) 
    wcs['XINC']=ra1-ra0
   
   
    rot=wcsrotset(ra0, dec0, wcs, logger)
     
    if type(rot) is StringType:
        hdulist.close()
        return errmsg.append(rot)
   
    
    wcs_add['CROTA1']['val']=wcs_add['CROTA2']['val']=rot
    #wcs_add['CROTA2']['val']=rot
    
    rot_rad=math.radians(rot)
    crot=math.cos(rot_rad)
    srot=math.sin(rot_rad)
    
    ra1, dec1=dsspos(wcs_add['CRPIX1']['val']+crot, wcs_add['CRPIX2']['val']+srot, wcs, logger)
    wcs_add['CDELT1']['val']=-wcsdist(ra0, dec0, ra1, dec1,logger)

    ra1, dec1=dsspos(wcs_add['CRPIX1']['val']+srot, wcs_add['CRPIX2']['val']+crot, wcs, logger)
    wcs_add['CDELT2']['val']=wcsdist(ra0, dec0, ra1, dec1, logger)
    
    #print 'CDELT', wcs_add['CDELT1']['val'], wcs_add['CDELT2']['val']
    
    s = wcs_add['CDELT2']['val'] / wcs_add['CDELT1']['val']
    
    wcs_add['PC001001']['val']=crot
    wcs_add['PC001002']['val']=-srot * s
    wcs_add['PC002001']['val']=srot / s
    wcs_add['PC002002']['val']=crot

    #print wcs_add['PC001001']['val'], wcs_add['PC001002']['val'], wcs_add['PC002001']['val'], wcs_add['PC002002']['val']

    if (wcs_add['CDELT1']['val'] *  wcs_add['CDELT2']['val'] > 0):
        srot = math.sin(-rot_rad)
    else:
        srot = math.sin(rot_rad)
        
    # Set CD matrix */
    wcs_add['CD1_1']['val'] = wcs_add['CDELT1']['val'] * crot
    
    if (wcs_add['CDELT1']['val'] < 0):
        wcs_add['CD1_2']['val'] = -math.fabs(wcs_add['CDELT2']['val']) * srot
    else:
        wcs_add['CD1_2']['val'] = math.fabs(wcs_add['CDELT2']['val']) * srot

    if( wcs_add['CDELT2']['val'] < 0):
        wcs_add['CD2_1']['val'] = math.fabs(wcs_add['CDELT1']['val']) * srot
    else:
        wcs_add['CD2_1']['val'] = -math.fabs(wcs_add['CDELT1']['val']) * srot
    
    wcs_add['CD2_2']['val'] = wcs_add['CDELT2']['val'] * crot
  
    #print wcs_add['CD1_1']['val'], wcs_add['CD1_2']['val'], wcs_add['CD2_1']['val'], wcs_add['CD2_2']['val']
    
    
    update_dss_fits(wcs_add, hdr, logger)
    
    hdulist.flush()      
    #hdulist.close()
    
    return errmsg

def wcsdist(x1,y1,x2,y2, logger=None):
    
    pos1=[]
    pos2=[]
    # Convert two vectors to direction cosines */
    xr1 = math.radians(x1)
    yr1 = math.radians(y1)
    cosb = math.cos(yr1)
    pos1.append(math.cos(xr1) * cosb)
    pos1.append(math.sin(xr1) * cosb)
    pos1.append(math.sin(yr1))
  
   
    xr2 = math.radians(x2)
    yr2 = math.radians(y2)
    cosb = math.cos(yr2)
    pos2.append(math.cos(xr2) * cosb)
    pos2.append(math.sin(xr2) * cosb)
    pos2.append(math.sin(yr2))
  

    #  Modulus squared of half the difference vector */
    w = 0.0
    for i in xrange(3):
        w += (pos1[i] - pos2[i]) * (pos1[i] - pos2[i])
    
    w = w / 4.0
    if (w > 1.0):
        w = 1.0
    # Angle beween the vectors */
    diff = 2.0 * math.atan2 (math.sqrt (w), math.sqrt (1.0 - w))
    diff = math.degrees(diff)
    if logger:
        logger.debug('diff<%f>' %diff)
    return (diff)

def wcsrotset(cra, cdec, wcs, logger=None):
    '''  compute image rotation '''
   
    xinc = math.fabs (wcs['XINC'])
    #yinc = math.fabs (wcs['YINC'])
    
    #* Compute position angles of North and East in image */
    xc = wcs['CRPIX1']  # wcs['CRPIX1'] == wcs->xrefpix;
    yc = wcs['CRPIX2']  # wcs['CRPIX2']wcs->yrefpix;

    #print "xinc=%f xc=%f yc=%f " %(xinc,xc,yc)

    #cra, cdec = dsspos(xc,yc,wcs)
    #print "dsspos cra<%f> cdec<%f> " %(cra, cdec)
 
    #print "calling dsspix xinc<%f> " %xinc
    #print "calling dsspix cra+xinc<%f> cdec<%f>" %((cra+xinc, cdec))

    xe,ye=dsspix (cra+xinc, cdec, wcs, logger)
    #xn,yn=dsspix (cra, cdec+yinc, wcs)
    if xe == None:
        return ye

    pa_east = math.degrees(math.atan2 (ye-yc, xe-xc))
    if (pa_east < -90.0):
        pa_east += 360.0 
#    
    if (pa_east > 90.0 and pa_east < 270.0):
        #print 'pa_east > 90 pa_east > 270.0'
        pa_east -= 180.0
    
    if logger:
        logger.debug('wcs_rot<%f>' % pa_east)
    return  pa_east


def dsspix (xpos, ypos, wcs, logger=None):
    ''' compute pixel coordinates for sky position 
        return (x-pixel, y-pixel) if successful. 
        otherwise, return (None, 'Error message')  
    '''
    
    conr2s = 206264.8062470964
    tolerance = 0.0000005
    max_iterations = 50
    
    # Convert RA and Dec in radians to standard coordinates on a plate 
    xr = math.radians(xpos)
    yr = math.radians(ypos)
    
    sypos = math.sin(yr)
    cypos = math.cos(yr)
    
    
    
    dec_rad= radec.dmsToRad( wcs['PLTDECSN'].strip(),  wcs['PLTDECD'], wcs['PLTDECM'] , wcs['PLTDECS'])
    
    if (dec_rad == 0.0):
        dec_rad = wcs["CRVAL2"]
        
    syplate = math.sin(dec_rad)
    cyplate = math.cos(dec_rad)
    
    #print "syplate=%f cyplate=%f" %( syplate,cyplate)
    
    ra_rad= radec.hmsToRad(wcs["PLTRAH"], wcs["PLTRAM"], wcs["PLTRAS"])
    if (ra_rad == 0.0):
        ra_rad = wcs["CRVAL2"]
    #print "xr=%f ra_rad=%f" %( xr, ra_rad) 
    sxdiff = math.sin(xr - ra_rad)
    cxdiff = math.cos(xr - ra_rad)
    #print "sxdiff=%f cxdiff=%f"  %( sxdiff, cxdiff)
    
    div = (sypos * syplate) + (cypos * cyplate * cxdiff)
    
    try:
        xi = cypos * sxdiff * conr2s / div
        eta = ((sypos * cyplate) - (cypos * syplate * cxdiff)) * conr2s / div
    except ZeroDivisionError,e:
        if logger:
            logger.debug('zero division<%s>' %(e))
        #print 'log ', e
        return (None, '<P><B>ERROR:</B> Problem  dsspix <%s>  div<%s>\n' %(e, str(div)))
    
    #print "xi=%f eta=%f" %( xi, eta)   
    # Set initial value for x,y 

    try:
        xmm = xi / wcs["PLTSCALE"]
        ymm = eta / wcs["PLTSCALE"]
    except ZeroDivisionError,e:
        if logger:
            logger.debug('zero division<%s>' %(e))
        #print 'log ', e
        return (None, '<P><B>ERROR:</B> Problem  dsspix <%s>  platscale<%s>\n' %(e, str(wcs["PLTSCALE"])))
        #return (None,'dsspix zero division error  wcs[pltscale]<%s>' %(str(wcs["PLTSCALE"])))
    
    #print "xmm=%f ymm=%f" %(xmm, ymm)
    
    # Iterate by Newton's method */
    for i in xrange(max_iterations):
        # X plate model */
        xy = xmm * ymm
        x2 = xmm * xmm
        y2 = ymm * ymm
        x2y = x2 * ymm
        y2x = y2 * xmm
        x2y2 = x2 + y2 
        cjunk = x2y2 * x2y2
        x3 = x2 * xmm
        y3 = y2 * ymm
        x4 = x2 * x2
        y4 = y2 * y2
        
        f1=wcs["AMDX1"]*xmm
        f2=wcs["AMDX2"]*ymm
        f3=wcs["AMDX3"]
        f4=wcs["AMDX4"]*x2
        f5=wcs["AMDX5"]*xy
        f6=wcs["AMDX6"]*y2
        f7=wcs["AMDX7"]*x2y2 
        f8=wcs["AMDX8"]*x3
        f9=wcs["AMDX9"]*x2y
        f10=wcs["AMDX10"]*y2x
        f11=wcs["AMDX11"]*y3
        f12=wcs["AMDX12"]*xmm*x2y2
        f13=wcs["AMDX13"]*xmm*cjunk
        
        f=f1+f2+f3+f4+f5+f6+f7+f8+f9+f10+f11+f12+f13
     
#        f = wcs->x_coeff[0]*xmm      + wcs->x_coeff[1]*ymm +
#            wcs->x_coeff[2]          + wcs->x_coeff[3]*x2 +
#            wcs->x_coeff[4]*xy       + wcs->x_coeff[5]*y2 +
#            wcs->x_coeff[6]*x2y2     + wcs->x_coeff[7]*x3 +
#            wcs->x_coeff[8]*x2y      + wcs->x_coeff[9]*y2x +
#            wcs->x_coeff[10]*y3      + wcs->x_coeff[11]*xmm*x2y2 +
#            wcs->x_coeff[12]*xmm*cjunk;

        #  Derivative of X model wrt x
        fx1=wcs["AMDX1"]
        fx4=wcs["AMDX4"]*2.0*xmm
        fx5=wcs["AMDX5"]*ymm
        fx7=wcs["AMDX7"]*2.0*xmm
        fx8=wcs["AMDX8"]*3.0*x2
        fx9=wcs["AMDX9"]*2.0*xy
        fx10=wcs["AMDX10"]*y2
        fx12=wcs["AMDX12"]*(3.0*x2+y2)
        fx13=wcs["AMDX13"]*(5.0*x4 +6.0*x2*y2+y4)     
        
        fx=fx1+fx4+fx5+fx7+fx8+fx9+fx10+fx12+fx13
        
#        fx = wcs->x_coeff[0]           + wcs->x_coeff[3]*2.0*xmm +
#         wcs->x_coeff[4]*ymm       + wcs->x_coeff[6]*2.0*xmm +
#         wcs->x_coeff[7]*3.0*x2    + wcs->x_coeff[8]*2.0*xy +
#         wcs->x_coeff[9]*y2        + wcs->x_coeff[11]*(3.0*x2+y2) +
#         wcs->x_coeff[12]*(5.0*x4 +6.0*x2*y2+y4);
# 
        # Derivative of X model wrt y
        fy2=wcs["AMDX2"]
        fy5=wcs["AMDX5"]*xmm
        fy6=wcs["AMDX6"]*2.0*ymm
        fy7=wcs["AMDX7"]*2.0*ymm
        fy9=wcs["AMDX9"]*x2
        fy10=wcs["AMDX10"]*2.0*xy
        fy11=wcs["AMDX11"]*3.0*y2
        fy12=wcs["AMDX12"]*2.0*xy
        fy13=wcs["AMDX13"]*4.0*xy*x2y2
        
        fy=fy2+fy5+fy6+fy7+fy9+fy10+fy11+fy12+fy13
        
#        fy = wcs->x_coeff[1]           + wcs->x_coeff[4]*xmm +
#         wcs->x_coeff[5]*2.0*ymm   + wcs->x_coeff[6]*2.0*ymm +
#         wcs->x_coeff[8]*x2        + wcs->x_coeff[9]*2.0*xy +
#         wcs->x_coeff[10]*3.0*y2   + wcs->x_coeff[11]*2.0*xy +
#         wcs->x_coeff[12]*4.0*xy*x2y2;


        # Y plate model */

        g1=wcs["AMDY1"]*ymm
        g2=wcs["AMDY2"]*xmm
        g3=wcs["AMDY3"]
        g4=wcs["AMDY4"]*y2
        g5=wcs["AMDY5"]*xy
        g6=wcs["AMDY6"]*x2
        g7=wcs["AMDY7"]*x2y2 
        g8=wcs["AMDY8"]*y3
        g9=wcs["AMDY9"]*y2x
        g10=wcs["AMDY10"]*x2y
        g11=wcs["AMDY11"]*x3
        g12=wcs["AMDY12"]*ymm*x2y2
        g13=wcs["AMDY13"]*ymm*cjunk
        
        g=g1+g2+g3+g4+g5+g6+g7+g8+g9+g10+g11+g12+g13 
#
#    /* Y plate model */
#    g = wcs->y_coeff[0]*ymm       + wcs->y_coeff[1]*xmm +
#       wcs->y_coeff[2]            + wcs->y_coeff[3]*y2 +
#       wcs->y_coeff[4]*xy         + wcs->y_coeff[5]*x2 +
#       wcs->y_coeff[6]*x2y2       + wcs->y_coeff[7]*y3 +
#       wcs->y_coeff[8]*y2x        + wcs->y_coeff[9]*y2x +
#       wcs->y_coeff[10]*x3        + wcs->y_coeff[11]*ymm*x2y2 +
#       wcs->y_coeff[12]*ymm*cjunk;
 
 
        # Derivative of Y model wrt x */
        gx2=wcs["AMDY2"]
        gx5=wcs["AMDY5"]*ymm
        gx6=wcs["AMDY6"]*2.0*xmm
        gx7=wcs["AMDY7"]*2.0*xmm
        gx9=wcs["AMDY9"]*y2
        gx10=wcs["AMDY10"]*2.0*xy
        gx11=wcs["AMDY11"]*3.0*x2
        gx12=wcs["AMDY12"]*2.0*xy
        gx13=wcs["AMDY13"]*4.0*xy*x2y2
        
        gx=gx2+gx5+gx6+gx7+gx9+gx10+gx11+gx12+gx13
 
#        /* Derivative of Y model wrt x */
#        gx = wcs->y_coeff[1]           + wcs->y_coeff[4]*ymm +
#        wcs->y_coeff[5]*2.0*xmm   + wcs->y_coeff[6]*2.0*xmm +
#        wcs->y_coeff[8]*y2       + wcs->y_coeff[9]*2.0*xy +
#        wcs->y_coeff[10]*3.0*x2  + wcs->y_coeff[11]*2.0*xy +
#        wcs->y_coeff[12]*4.0*xy*x2y2;
 
        # Derivative of Y model wrt y */
        gy1=wcs["AMDY1"]
        gy4=wcs["AMDY4"]*2.0*ymm
        gy5=wcs["AMDY5"]*xmm
        gy7=wcs["AMDY7"]*2.0*ymm
        gy8=wcs["AMDY8"]*3.0*y2
        gy9=wcs["AMDY9"]*2.0*xy
        gy10=wcs["AMDY10"]*x2
        gy12=wcs["AMDY12"]*(x2+3.0*y2) 
        gy13=wcs["AMDY13"]*(5.0*y4 + 6.0*x2*y2 + x4)
        gy=gy1+gy4+gy5+gy7+gy8+gy9+gy10+gy12+gy13
        
#        Derivative of Y model wrt y */
#    gy = wcs->y_coeff[0]            + wcs->y_coeff[3]*2.0*ymm +
#         wcs->y_coeff[4]*xmm        + wcs->y_coeff[6]*2.0*ymm +
#         wcs->y_coeff[7]*3.0*y2     + wcs->y_coeff[8]*2.0*xy +
#         wcs->y_coeff[9]*x2         + wcs->y_coeff[11]*(x2+3.0*y2) +
#         wcs->y_coeff[12]*(5.0*y4 + 6.0*x2*y2 + x4);
       
        #print "f=%f fx=%f fy=%f g=%f gx=%f gy=%f" %(f, fx, fy, g, gx,gy)
       
        f -= xi
        g -= eta
        dx = ((-f * gy) + (g * fy)) / ((fx * gy) - (fy * gx))
        dy = ((-g * fx) + (f * gx)) / ((fx * gy) - (fy * gx))
        xmm += dx
        ymm += dy
        
        if logger:
            logger.debug("dx<%f> dy<%f>"  %( math.fabs(dx),math.fabs(dy) ))
        
        if (( math.fabs(dx) < tolerance) and (math.fabs(dy) < tolerance)):
            break
   
    # Convert mm from plate center to plate pixels 
    try:
        x = (wcs['PPO3'] - xmm*1000.0) / wcs['XPIXELSZ']
        y = (wcs['PPO6'] + ymm*1000.0) / wcs['YPIXELSZ']
    except ZeroDivisionError,e:
        if logger:
            logger.debug('zero division<%s>' %(e))
        #print 'log ', e
        return (None, '<P><B>ERROR:</B> Problem  dsspix <%s>  x/ypiexlsz<%s %s>\n' %(e, str(wcs['XPIXELSZ']), str(wcs['YPIXELSZ']) ))
        #return (None,'dsspix zero division error  xpix<%s> xpix<%s>' %(str(wcs['XPIXELSZ']), str(wcs['YPIXELSZ'])))

    # Convert from plate pixels to image pixels 
    xpix = x - wcs['CNPIX1'] + 1.0 - 0.5
    ypix = y - wcs['CNPIX2'] + 1.0 - 0.5
     
    
    # If position is off of the image, return offscale code 
    try:
        assert 0.5 <= xpix < wcs['NAXIS1']+0.5
        assert 0.5 <= ypix < wcs['NAXIS2']+0.5
    except AssertionError,e:
        if logger:
            logger.debug('out of range<%s>' %e)    
        return (None, '<P><B>ERROR:</B> Problem  out of rang x/ypix<%s %s>\n' %(e, str(xpix), str(ypix) ))
        
        #return (None,'dsspix out of range xpix<%s> ypix<%s>' %(str(xpix), str(ypix)))
   
    if logger:
        logger.debug("xpix<%f> ypix<%f>" %(xpix, ypix)) 
    return (xpix, ypix)


def dsspos(xpix, ypix, wcs, logger=None):
    """ compute accurate position for pixel coordinates. 
        return (x-pos, y-pos) if successful. 
        otherwise, return (None, 'Error message')   
    """
    
    cond2r = 0.01745329252
    cons2r = 206264.8062470964
    twopi = 6.28318530717959
  
    # Convert from image pixels to plate pixels 
    x = xpix + wcs['CNPIX1'] - 0.5
    y = ypix + wcs['CNPIX2'] - 0.5
    
    #print "x=%f y=%f" %(x,y)
    # Convert from pixels to millimeters */
    xmm = (wcs['PPO3'] - (x * wcs['XPIXELSZ'])) / 1000.0
    ymm = ((y * wcs['YPIXELSZ']) - wcs['PPO6']) / 1000.0
    xmm2 = xmm**2
    ymm2 = ymm**2
    xmm3 = xmm * xmm2
    ymm3 = ymm * ymm2
    x2y2 = xmm2 + ymm2
    
    if logger:
        logger.debug("xmm=%f ymm=%f xmm2=%f ymm2=%f xmm3=%f ymm3=%f x2y2=%f" %( xmm,ymm,xmm2,ymm2,xmm3,ymm3,x2y2))
    # Compute coordinates from x,y and plate model 
    
    ''' note: 
              if you implement caluculation like "wcs["AMDX1"]*xmm  + wcs["AMDX2"]*ymm ...", 
              it will produce an inaccurate result as compared with SOSS C wirtten code. 
    '''
    x1 = wcs["AMDX1"] * xmm
    x2 = wcs["AMDX2"] * ymm
    x3 = wcs["AMDX3"]
    x4 = wcs["AMDX4"] * xmm2
    x5 = wcs["AMDX5"] * xmm * ymm
    x6 = wcs["AMDX6"] * ymm2
    x7 = wcs["AMDX7"] * x2y2
    x8 = wcs["AMDX8"] * xmm3
    x9 = wcs["AMDX9"] * xmm2 * ymm
    x10 = wcs["AMDX10"] * xmm * ymm2
    x11 = wcs["AMDX11"] * ymm3
    x12 = wcs["AMDX12"] * xmm * x2y2
    x13 = wcs["AMDX13"] * xmm * x2y2**2
    
    if logger:
        logger.debug('x1=%f x2=%f x3=%f x4=%f x5=%f x6=%f x7=%f x8=%f x9=%f x10=%f x11=%f x12=%f x13=%f' %(x1,x2,x3,x4,x5,x6,x7,x8,x9,x10,x11,x12,x13))
    
    xi= x1 + x2 + x3 + x4 + x5 + x6 + x7 + x8 + x9 + x10 + x11 + x12 + x13
#    xi=0.0
#    xi = wcs["AMDX1"]*xmm 
#    + wcs["AMDX2"]*ymm 
#    + wcs["AMDX3"] 
#    + wcs["AMDX4"]*xmm2 
#    + wcs["AMDX5"]*xmm*ymm 
#    + wcs["AMDX6"]*ymm2 
#    + wcs["AMDX7"]*x2y2 
#    + wcs["AMDX8"]*xmm3 
#    + wcs["AMDX9"]*xmm2*ymm 
#    + wcs["AMDX10"]*xmm*ymm2 
#    + wcs["AMDX11"]*ymm3 
#    + wcs["AMDX12"]*xmm*(x2y2)
#    + wcs["AMDX13"]*xmm*x2y2*x2y2
      
    eta1 = wcs["AMDY1"]*ymm 
    eta2 = wcs["AMDY2"]*xmm
    eta3 = wcs["AMDY3"]
    eta4 = wcs["AMDY4"]*ymm2 
    eta5 = wcs["AMDY5"]*xmm*ymm
    eta6 = wcs["AMDY6"]*xmm2
    eta7 = wcs["AMDY7"]*x2y2
    eta8 = wcs["AMDY8"]*ymm3
    eta9 = wcs["AMDY9"]*ymm2*xmm
    eta10 = wcs["AMDY10"]*ymm*xmm2
    eta11 = wcs["AMDY11"]*xmm3 
    eta12 = wcs["AMDY12"]*ymm*x2y2
    eta13 = wcs["AMDY13"]*ymm*x2y2**2
    
    if logger:
        logger.debug('x1=%f x2=%f x3=%f x4=%f x5=%f x6=%f x7=%f x8=%f x9=%f x10=%f x11=%f x12=%f x13=%f' %(x1,x2,x3,x4,x5,x6,x7,x8,x9,x10,x11,x12,x13))
    eta= eta1 + eta2 + eta3 + eta4 + eta5 + eta6 + eta7 + eta8 + eta9 + eta10 + eta11 + eta12 + eta13
    
#    eta = wcs["AMDY1"]*ymm 
#    + wcs["AMDY2"]*xmm
#    + wcs["AMDY3"] + wcs["AMDY4"]*ymm2 
#    + wcs["AMDY5"]*xmm*ymm + wcs["AMDY6"]*xmm2 
#    + wcs["AMDY7"]*(x2y2) + wcs["AMDY8"]*ymm3 
#    + wcs["AMDY9"]*ymm2*xmm + wcs["AMDY10"]*ymm*xmm2 
#    + wcs["AMDY11"]*xmm3 + wcs["AMDY12"]*ymm*(x2y2)
#    + wcs["AMDY13"]*ymm*x2y2*x2y2
    
    #print 'xi=%f eta=%f' %(xi, eta)      
    # Convert to radians 
    xir = xi / cons2r
    etar = eta / cons2r
    
    #print 'xir=%f etar=%f' %(xir, etar)
  
    # Convert to RA and Dec 
    #dec_rad= _calc_dec_rad(wcs)
    #print "DEC_RAD<%s>" %(str(dec_rad))
    
    dec_rad=radec.dmsToRad( wcs['PLTDECSN'].strip(),  wcs['PLTDECD'], wcs['PLTDECM'] , wcs['PLTDECS'])
    #print "DEC_RAD<%s>" %(str(dec_rad))
    
    ctan = math.tan(dec_rad)
    ccos = math.cos(dec_rad)
    #print 'dec_rad=%f ctan=%f ccos=%f' %(dec_rad, ctan, ccos)
    
    raoff = math.atan2( (xir/ccos), (1.0 - (etar*ctan) ))
    #ra = raoff + _calc_ra_rad(wcs)
    #print 'ra raoff' , ra, raoff
    
    ra = raoff + radec.hmsToRad(wcs["PLTRAH"], wcs["PLTRAM"], wcs["PLTRAS"])
    #print 'ra raoff' , ra, raoff
    
    if (ra < 0.0):
        ra += twopi
    xpos = ra / cond2r
    
    exc=etar*ctan
    epc=etar+ctan
    cos_ra=math.cos(raoff)
    tmp=(epc/(1.0-exc))
    atan_ra=cos_ra * tmp
    dec=0.0    
    dec = math.atan( atan_ra )
    
    #print "dec exc epc cos_ra tmp atan_ra" , dec, exc, epc, cos_ra,tmp, atan_ra
     
    ypos = dec*1.0/cond2r
    
    #return (xpos, ypos)
    if logger:
        logger.debug('xpos[%f] ypos[%f]' %(xpos, ypos))
    return (xpos, ypos)



#########################################
#   Position/rotation calculations
#########################################

# this function is provided by MOKA2 Development Team (1996.xx.xx)  &
# used in SOSS
#
def trans_coeff (equinox, x, y, z):
       
    tt = (equinox - 2000.0) / 100.0
    
    zeta = math.radians((2306.2181 * tt) + (0.30188 * (tt ** 2)) + \
                        (0.017998 * (tt ** 3))) / 3600.0
    zetto= math.radians((2306.2181 * tt) + (1.09468 * (tt ** 2)) + \
                        (0.018203 * (tt ** 3))) / 3600.0
    theta= math.radians((2004.3109 * tt) - (0.42665 * (tt ** 2)) - \
                        (0.041833 * (tt ** 3))) / 3600.0
    
    p11 = math.cos(zeta) * math.cos(theta) * math.cos(zetto) - \
          math.sin(zeta) * math.sin(zetto)
    p12 = -math.sin(zeta) * math.cos(theta) * math.cos(zetto) - \
          math.cos(zeta) * math.sin(zetto)
    p13 = -math.sin(theta) * math.cos(zetto)
    p21 = math.cos(zeta) * math.cos(theta) * math.sin(zetto) + \
          math.sin(zeta) * math.cos(zetto)
    p22 = -math.sin(zeta) * math.cos(theta) * math.sin(zetto) + \
          math.cos(zeta) * math.cos(zetto)
    p23 = -math.sin(theta) * math.sin(zetto)
    p31 = math.cos(zeta) * math.sin(theta)
    p32 = -math.sin(zeta) * math.sin(theta)
    p33 = math.cos(theta)
    
    return (p11, p12, p13, p21, p22, p23, p31, p32, p33)


# this function is provided by MOKA2 Development Team (1996.xx.xx)  &
# used in SOSS system
# changed a little
# ra/dec degree and equinox are passed
# ra/dec degree based on equinox 2000 will be returned   

def getRaDecStrInEq2000(ra_deg, dec_deg, equinox):
    """
    Coverts RA and DEC in degrees to equivalents in equinox 2000, and
    then formats them as strings in HMS format.
    Parameters:
      ra_deg: RA in degrees
      dec_deg: DEC in degrees
      equinox: equinox used
    Result:
      (ra_str, dec_str), where these are ra and dec expressed as HMS strings
      or (None, None) if the inputs cannot be converted.
    """
       
    # Convert ra/dec to equivalent in equinox 2000 if a different
    # equinox was used.
    ra_deg, dec_deg = eqToEq2000(ra_deg, dec_deg, equinox)

    # Convert degrees back to HMS and produce strings
    rah, ramin, rasec = radec.degToHms(ra_deg)

    ra_str = radec.raHmsToString(rah, ramin, rasec,
                                             format='%02d:%02d:%06.3f')

    sign, decd, decmin, decsec = radec.degToDms(dec_deg)

    dec_str = radec.decDmsToString(sign, decd, decmin, decsec,
                                               format='%s%02d:%02d:%05.2f')

    return (ra_str, dec_str)


def eqToEq2000(ra_deg, dec_deg, equinox):
    """Convert RA (in degrees) and DEC (in degreees) to their equivalents
    in equinox 2000.
    Parameters:
      ra_deg: RA in degrees
      dec_deg: DEC in degrees
      equinox: equinox used
    Result:
      (ra_deg, dec_deg), converted as described.
    """
           
    if equinox == 2000.0:
        return (ra_deg, dec_deg)
        
    ra_rad = math.radians(ra_deg)
    dec_rad = math.radians(dec_deg)
    
    x = math.cos(dec_rad) * math.cos(ra_rad) 
    y = math.cos(dec_rad) * math.sin(ra_rad)
    z = math.sin(dec_rad) 
    
    p11, p12, p13, p21, p22, p23, p31, p32, p33 = trans_coeff(equinox, x, y, z)
    
    x0 = (p11 * x) + (p21 * y) + (p31 * z)
    y0 = (p12 * x) + (p22 * y) + (p32 * z)
    z0 = (p13 * x) + (p23 * y) + (p33 * z)
    
    new_dec = math.asin(z0)
    if x0 == 0.0:
        new_ra = math.pi / 2.0
    else:
        new_ra = math.atan( y0/x0 )
        
    if( (y0 * math.cos(new_dec) > 0.0 and x0 * math.cos(new_dec) <= 0.0) or
        (y0 * math.cos(new_dec) <=0.0 and x0 * math.cos(new_dec) < 0.0) ):
        new_ra += math.pi
            
    elif new_ra < 0.0:
        new_ra += 2.0 * math.pi
        
    #new_ra = new_ra * 12.0 * 3600.0 / math.pi
    new_ra_deg = new_ra * 12.0 / math.pi * 15.0
   
    #new_dec = new_dec * 180.0 * 3600.0 / math.pi
    new_dec_deg = new_dec * 180.0 / math.pi
 
    return (new_ra_deg, new_dec_deg)


def calc_pc( irot_tel, imgrot_flag, insrotpa, altitude, azimuth, imgrot):
    """Calculate the PC001001, PC001002, PC002001 and PC002002 FITS keyword
    values.
    Parameters:
      irot_tel:
      imgrot_flg:
      insrotpa:
      altitude:
      azimuth:
      imgrot:
    """
    # imgrot is sync to telescope
    if irot_tel == 'LINK':
        sg = 1.0
        if imgrot_flag =='08':   # Red
            pa = (73.59-insrotpa) * 2.0
            pc11, pc12, pc21, pc22 = setPCs(pa,sg)

        elif imgrot_flag =='02': # Blue
            # Blue have not measured yet. Therefore, use same calculation
            # as Red
            pa = (73.59-insrotpa) * 2.0
            pc11, pc12, pc21, pc22 = setPCs(pa,sg)

        else:                    # None 
            sg = -1.0
            pa=calcPA(irot_tel, imgrot_flag, insrotpa, altitude, azimuth, imgrot)
            pc11, pc12, pc21, pc22 = setPCs(pa,sg)

    elif irot_tel == 'FREE':
        if imgrot_flag =='08':   # Red
            sg=1.0
            pa=calcPA(irot_tel, imgrot_flag,insrotpa, altitude, azimuth, imgrot)
            pc11, pc12, pc21, pc22 = setPCs(pa,sg)

        elif imgrot_flag =='02': # Blue
            sg=1.0
            pa=calcPA(irot_tel, imgrot_flag,insrotpa, altitude, azimuth, imgrot)
            pc11, pc12, pc21, pc22 = setPCs(pa,sg)  

        else:
            sg=-1.0
            pa=calcPA(irot_tel, imgrot_flag,insrotpa, altitude, azimuth, imgrot)
            pc11, pc12, pc21, pc22 = setPCs(pa,sg)       
        
    return (pc11, pc12, pc21, pc22)   

 
def calcPC(*args):
    """Calculate the PC001001, PC001002, PC002001 and PC002002 FITS keyword
    values.
    Parameters:
      irot_tel:
      imgrot_flg:
      insrotpa:
      altitude:
      azimuth:
      imgrot:
    """
    validateArgs(*args)
    try:
        return calc_pc(*args)
        
    except IndexError:
        raise ParameterError("Incorrect number of parameters: %s" % str(args))


def calc_pa(altitude, azimuth, latitude_deg=SUBARU_LATITUDE_DEG):
    """Generic calculation of position angle based on telescope pointing.
    Parameters:
      altitude: elevation of the telescope
      azimuth: azimuth of the telescope 
      latitude_deg: latitude of the telescope
    """
    subaru_lati_rad = math.radians(latitude_deg)
    alti_rad = math.radians(altitude)
    azim_rad = math.radians( (azimuth-180.0) )
    pa = math.atan2( math.cos(subaru_lati_rad) * math.sin(azim_rad),  
                     math.sin(subaru_lati_rad) * math.cos(alti_rad) + \
                     math.cos(subaru_lati_rad) * math.sin(alti_rad) * \
                     math.cos(azim_rad) )
       
    return pa


def calcPA(irot_tel, imgrot_flag, insrotpa, altitude, azimuth, imgrot,
           latitude_deg=SUBARU_LATITUDE_DEG):
    """Calculate Position Angle.
    Parameters:
      irot_tel:
      imgrot_flg:
      insrotpa:
      altitude: elevation of the telescope
      azimuth: azimuth of the telescope 
      imgrot:
      latitude_deg: latitude of the telescope
    """
    p = calc_pa(altitude, azimuth, latitude_deg)
       
    # imgrot is async and img is eihter red or blue
    if irot_tel is 'FREE' and (imgrot_flag is '08' or imgrot_flag is '02'):
        pa = 57.18 + altitude - math.degrees(p) - 2.0 * imgrot

    else:
        pa = 180.0 + 58.4 + altitude - math.degrees(p)
        
    return pa


def calcPCs(pa, sg):
    
    pc11 = math.cos( math.radians(pa) )
    pc12 = math.sin( math.radians(pa) )
    pc21 = -math.sin( math.radians(pa) ) * sg
    pc22 = math.cos( math.radians(pa) ) * sg
    
    return (pc11, pc12, pc21, pc22)


#CD1_1 = PC001001 * CDELT1  | CD1_2 = PC001002 * CDELT1
#CD2_1 = PC002001 * CDELT2  | CD2_2 = PC002002 * CDELT2
def calcCD(pc, cd):
    """Calculate the CD1_1, CD1_2, CD2_1 and CD2_2 FITS keyword values.
    """
    validateArgs(pc, cd)

    return pc * cd

         
def calcCDELT(cdelt, binning):
    """calc fit keyword 'CDELT1/2'
    """

    validateArgs(cdelt, binning)

    return cdelt * binning


def calcCRPIX(ccd_center_px, exp_wd, binning):
    """calculate crpix 1/2  ccd center(X/Y) -
    (exposure width X/Y pixel / binning)
    """

    validateArgs(ccd_center_px, exp_wd, binning)

    return ccd_center_px - ( exp_wd / binning )


def calcExpTime(exptime):
    """msec to sec
    """

    validateArgs(exptime)

    return exptime / 1000.0


def hmsToDeg (ra_str):
    """Converts an RA expressed in HH:MM:SS.sss to degrees (float).
    """

    validateArgs(ra_str)

    try:
        hour, min, sec = ra_str.split(':')
    except IndexError:
        raise ParameterError("Bad format for parameter: %s" % str(ra_str))

    return radec.hmsToDeg(int(hour), int(min), float(sec))

    
def dmsToDeg (dec_str):
    """Converts a DEC expressed in DD:MM:SS.sss to degrees (float).
    """

    validateArgs(dec_str)

    try:
        deg, min, sec = dec_str.split(':')
    except IndexError:
        raise ParameterError("Bad format for parameter: %s" % str(dec_str))

    sign = deg[0:1]
    deg = deg[1:] 
    return radec.decTimeToDeg(sign, int(deg), int(min),
                                          float(sec))


#  ag ccd degree/pixel
####  all SH values are dummy and it is ok with fake values #####
####  not figure them out yet #####


#########################################
#   Date calculations
#########################################

def calcDATE_OBS(secs_epoch, ut1_utc=0.0, format='%04d-%02d-%02d'):
    """Calculate observation date in format for FITS keyword 'DATE-OBS'
    """
    (yr, mo, da, hr, min, sec) = adjustTime(secs_epoch, ut1_utc=ut1_utc)

    # format UTCD
    return format % (yr, mo, da) 



def calcObsDate(secs_epoch, ut1_utc=0.0, format='%04d-%02d-%02d'):
    """Calculate observation date in format for FITS keyword 'DATE-OBS'
    """
    (yr, mo, da, hr, min, sec) = adjustTime(secs_epoch, ut1_utc=ut1_utc)

    # format UTCD
    return format % (yr, mo, da) 

        
def calcUT(secs_epoch, ut1_utc=0.0, format='%02d:%02d:%06.3f'):
    """Calculate time in format for FITS keyword 'UT', 'UT-STR' and 'UT-END'.
    Default format is (HH:MM:SS.sss)
    """
         
    (yr, mo, da, hr, min, sec) = adjustTime(secs_epoch, ut1_utc=ut1_utc)

    return format % (hr, min, sec)

    
def calcUT2(sec, usec, ut1_utc=0.0, format='%02d:%02d:%06.3f'):
    """Same as calcUT, but passing secs and fractional secs separately.
    """
    validateArgs(sec, usec, ut1_utc)
    
    return calcUT(float('%d.%d' % (sec, usec)), ut1_utc=ut1_utc, format=format)
         

def calcHST(secs_epoch, ut1_utc=0.0, format='%02d:%02d:%06.3f'):
    """Calculate time in format for FITS keyword 'HST', 'HST-STR' and
    'HST-END'.  Default format is (HH:MM:SS.sss)
    """
         
    (yr, mo, da, hr, min, sec) = adjustTime(secs_epoch, ut1_utc=ut1_utc,
                                            timefn=time.localtime)

    return format % (hr, min, sec)

    
def calcHST2(sec, usec, ut1_utc=0.0, format='%02d:%02d:%06.3f'):
    """Same as calcHST, but passing secs and fractional secs separately.
    """
    validateArgs(sec, usec, ut1_utc)
    
    return calcHST(float('%d.%d' % (sec, usec)), ut1_utc=ut1_utc,
                   format=format)

#
#
#def calcJulianDays(yyyy, mm, dd):
#    """Pythonized version of SOSS Julian Day calculation function.
#       SOSS original function is liboss_cal/OSScal_LST.c:getJD()."""
#    # Python rounded the value of mo down instead of truncating the value
#    mo = -((14 - mm) / 12)
#    pp = (1461 * (yyyy + 4800 + mo)) / 4 + (367 * (mm - 2 - mo * 12)) / 12
#    pjd = pp - (3 * ((yyyy + 4900 + mo) / 100)) / 4 - 32075.5 + dd
#    return pjd
#
#
def calcGST(tu, ut):
    """Pythonized version of SOSS Global Sidereal Time calculation function,
    but only for Mean case (removed the with and without 'short term' cases).
    """

    tu2 = tu * tu
    tu3 = tu2 * tu
    
    pgs = 24110.54841 + 8640184.812866*tu + 0.093104*tu2 - 0.0000062*tu3 + ut
    #print "   calcGST1:  pgs = %12.3f" % pgs
    pgs = pgs - 86400.0 * int(pgs / 86400.0)
    
    if pgs < 0.0:
        pgs = pgs + 86400.0;

    return pgs


def sidereal(yr, mo, da, hr, min, sec):
    """Pythonized version of SOSS Local Sidereal Time calculation function."""
    """modified to use passed date"""
   
    jd = calcJD(yr, mo, da, hr, min, sec)
    ut = hr * 3600.0 + min * 60.0 + sec
    tu = (jd - 2451545.0) / 36525.0

    gst = calcGST(tu, ut)
     
    lst = gst - 37315.26  # (-155 28' 48.900" ):(155*3600+28*60+48.9)/15   SUBARU's LONGITUDE
    
    #lst = gst - 37315.3333; # (155 28' 50" ):(155*3600+28*60+50)/15
    if lst < 0.0:
        lst = lst + 86400.0
    
    return lst


def calcLST(secs_epoch, ut1_utc=0.0, format='%02d:%02d:%06.3f'):
    """Calculate time in format for FITS keyword 'LST', 'LST-STR' and
    'LST-END'.  Default format is (HH:MM:SS.sss)
    """
    
    yr, mo, da, hr, min, sec = adjustTime(secs_epoch, ut1_utc)
               
    # Calculate LST
    lst_secs = sidereal(yr, mo, da, hr, min, sec)

    # Now get GMT of that, broken down
    (yr, mo, da, hr, min, sec) = adjustTime(lst_secs)

    # Return string formatted for FITS header
    return format % (hr, min, sec) 


def calcLST2(sec, usec, ut1_utc=0.0, format='%02d:%02d:%06.3f'):
    """Same as calcLST, but passing secs and fractional secs separately.
    """
    
    validateArgs(sec, usec, ut1_utc)
    
    return calcLST(float('%d.%d' % (sec, usec)), ut1_utc=ut1_utc,
                   format=format)


def calcJD(year, month, day, hour, minute, second):

    ut = hour * 3600.0 + minute * 60.0 + second
    dd = day + ( ut / 86400.0)
    
    mo = -((14 - month) / 12)
    pp = (1461 * (year + 4800 + mo)) / 4 + (367 * (month - 2 - mo * 12)) / 12
    pjd = pp - (3 * ((year + 4900 + mo) / 100)) / 4 - 32075.5 + dd
    
    #return calcJulianDays(year, month, dd)
    return pjd
    

def calcMJD(secs_epoch, ut1_utc=0.0):   
    """Calculate time in format for FITS keyword 'MJD', 'MJD-STR' and
    'MJD-END'.  Default format is (HH:MM:SS.sss)
    """
    
    yr, mo, da, hr, min, sec = adjustTime(secs_epoch, ut1_utc=ut1_utc)
        
    jd = calcJD(yr, mo, da, hr, min, sec)

    # ??? 2400000.5
    return jd - 2400000.5
     

def calcMJD2(sec, usec, ut1_utc=0.0):   
    """Same as calcMJD, but passing secs and fractional secs separately.
    """
    
    validateArgs(sec, usec, ut1_utc)

    return calcMJD(float('%d.%d' % (sec, usec)), ut1_utc=ut1_utc)
     

def adjustTime(secs_epoch, ut1_utc=0.0, timefn=time.gmtime):

    # Add UT1_UTC correction factor
    nsecs = secs_epoch + ut1_utc

    # Now get time of that, broken down
    (yr, mo, da, hr, min, sec, wday, yday, isdst) = timefn(nsecs)

    # Add back in the fractional seconds
    frac_sec = nsecs - int(nsecs)
    sec = float(sec) + frac_sec

    # Return broken down time
    return (yr, mo, da, hr, min, sec)


## class FITSBuilder(object):

##     def __init__(self, buildlist):
##         self.bl = buildlist
    
##     def update(self, hdr):
##         for rec in self.bl:
##             comment = rec.get('comment', None)
##             if rec.has_key('value'):
##                 val = rec['value']
                
##             elif rec.has_key('calc'):
##                 args = rec.get('args', [])
##                 args = rec.get('kwdargs', {})

##                 fn = rec['calc']
##                 if callable(fn):
##                     val = fn(*args, **kwdargs)

##             else:
##                 # No reasonable value found
##                 val = 'ERROR'
                    
##             hdr.update(rec['kwd'], val, comment=comment)


#########################################
#   FITS file manipulations
#########################################

def make_fits(filepath, hdrdct, data):
    """Convenience function for making a FITS file.
    """
    fitsobj = pyfits.HDUList()
    hdu = pyfits.PrimaryHDU()
    for (kwd, val) in hdrdct.items():
        hdu.header.update(kwd, val)
    hdu.data = data
    fitsobj.append(hdu)
    fitsobj.writeto(filepath)
    fitsobj.close()


def make_fakefits(filepath, hdrdct, width, height):
    """ Make a little fake FITS file.
    _width_ and _height_ are dimensions, 
    """
    #data = numpy.zeros((width, height), type=numpy.float32)
    # how to force floats?
    data = numpy.zeros((width, height))
    make_fits(filepath, hdrdct, data)


def checkFrameId(ins, frameid):
    match = re.match('^%3s[AQ]\d{8}$' % ins, frameid)
    return match


def getFrameInfoFromPath(fitspath):
    # Extract frame id from file path
    (fitsdir, fitsname) = os.path.split(fitspath)
    (frameid, ext) = os.path.splitext(fitsname)
    
    match = re.match('^(\w{3})([AQ])(\d{8})$', frameid)
    if match:
        (inscode, frametype, frame_no) = match.groups()
        frame_no = int(frame_no)

        inscode = inscode.upper()
        frameid = frameid.upper()
        frametype = frametype.upper()

        return (frameid, fitsname, fitsdir, inscode, frametype, frame_no)

    return None


def grep_fits(fitspaths, kwddict, re_flags=0):
    """Convenience function for searching headers of a FITS file(s).
    Takes a list (or indexable object) of fits file paths (fitspaths)
    and a dict of keyword/regexp pairs (kwddict).  For each fits file
    all the fits HDU headers are examined for each keyword in _kwddict_.
    If the keyword exists in the header, its associated value is matched
    against the regexp specified by _kwddict_.

    What is returned is a dict of dicts, where the keywords of the top
    level dict are the fits file paths and the items are dicts of all
    matching FITS keywords and values.  Example:

    >>> fitsutils.grep_fits(['MCSA00054635.fits', 'MCSA00054636.fits'],
            {'HST': '.*'})
    {'MCSA00054635.fits': {'HST': '14:59:40.608'},
     'MCSA00054636.fits': {'HST': '14:59:40.020'}}
    """

    res = {}
    for fitspath in fitspaths:
        fitsobj = pyfits.open(fitspath, 'readonly')
        d2 = {}
        try:
            for hdu in fitsobj:
                for (kwd, regexp) in kwddict.items():
                    if hdu.header.has_key(kwd):
                        val = hdu.header[kwd]
                        match = re.match(regexp, val, re_flags)
                        if match:
                            d2[kwd] = val
        finally:
            fitsobj.close()
            if len(d2) > 0:
                res[fitspath] = d2
        
    return res


def update_fits(fitspath, newpath, datadict):
    """Convenience function for updating a FITS file.
    Takes a fits path, an (optional) new path, and a data dictionary of
    keyword/value pairs.  The FITS file is opened, each header is updated
    with the items from the datadict and then the file is written out and
    closed.
    """

    if (newpath == None) or (newpath == fitspath):
        mode = 'update'
    else:
        mode = 'readonly'
        
    fitsobj = pyfits.open(fitspath, mode)
    try:

        for hdu in fitsobj:
            for (kwd, val) in datadict.items():
                hdu.header.update(kwd, val)

        if mode == 'readonly':
            fitsobj.writeto(newpath)
            
    finally:
        fitsobj.close()
        

def change_frameid(fitspath, newframeid):
    """Convenience function for updating a FITS file to have a new Subaru
    frame id.
    """

    #checkFrameId()

    fitspath = os.path.abspath(fitspath)
    (fitsdir, fitsname) = os.path.split(fitspath)

    newpath = fitsdir + "/" + newframeid + ".fits"
    if os.path.exists(newpath):
        raise ParameterError("File already exists: %s" % newpath)
    
    update_fits(fitspath, newpath, {'FRAMEID': newframeid,
                                    'EXP-ID': newframeid})

    
def change_propid(fitspath, newpropid):
    """Convenience function for updating a FITS file to have a new Subaru
    prop-id.
    """

    update_fits(fitspath, None, {'PROP-ID': newpropid})

#END


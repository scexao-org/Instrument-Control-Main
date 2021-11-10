#!/usr/bin/env python

import sys, os, re
import unittest
import pyfits, numpy
import guiderint
import guidersave
import guiderfits
import guiderfitsheader
import environment
import astro.wcs as wcs
import Queue
from SOSS.STATint.StatusConstants import *
import logging, ssdlog

# Create top level logger
logger = logging.getLogger('testfunc_guiderint')
logger.setLevel(logging.ERROR)

fmt = logging.Formatter(ssdlog.STD_FORMAT)

stderrHdlr = logging.StreamHandler()
stderrHdlr.setFormatter(fmt)
logger.addHandler(stderrHdlr)

NUM=re.compile(r'([-|+]?[0-9]+(\.[0-9]+)?(e[-][0-9]+)?)$')  

class TestPyfitsData(unittest.TestCase):
    
    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)
        
        self.env = environment.MockEnvironment()
        self.dirpath= self.env.INST_PATH
        
        self.createfits=guiderfits.GuiderCreateFits(logger, monitor=None,
                                                    debug=False,
                                                    dummyval=False,
                                                    usethread=True)
        
        self.aliasVal=guiderfitsheader.getAlias()                            # status alias values
        self.keyVal=guiderfitsheader.getKeyVal()
                

    def setUp(self):
        #self.env = environment.MockEnvironment()
        #self.env.removeTestDirs()  # just in case, remove dir
        #self.env.makeDirs()    
        #self.path= self.env.INST_PATH
        self.frameid='VGWA0000001'
        self.framelist=['VGWA0000002', 'VGWA0000003', 'VGWA0000004', 'VGWA0000005']
        self.fits_row = 3
        self.fits_col = 3
        self.fits_type=-32
        self.fits_dimension=2
            
        self.dummy_image = numpy.zeros((self.fits_row,self.fits_col)).astype('Float32')
        
        self.header_info={'DATA-TYP': 'OBJECT', 'FRAMEID': 'VGWA0000001', 'BIN-FCT1': 1, 'EXPTIME': 0.56}
        self.sec=1000; self.usec=111111
      
        
    
    def testGetHeaderValue(self):
        header="0006AG%%CASS1x1%009701880151015100000560u%160101510151      "
        val='0006'; key='insCode'
        self.assertHeader(header, val, key)
        
        val='AG'; key='insName'
        self.assertHeader(header, val, key)
        
        val='CASS'; key='foci'
        self.assertHeader( header, val, key)
               
        val=1; key='binX'
        self.assertHeader( header, val, key)
        
        val=1; key='binX'
        self.assertHeader( header, val, key)
        
        val=97; key='expRangeX'
        self.assertHeader(header, val, key)
        
        val=188; key='expRangeY'
        self.assertHeader( header, val, key)
        
        val=151; key='expRangeDX'
        self.assertHeader( header, val, key)
        
        val=151; key='expRangeDY'
        self.assertHeader( header, val, key)
        
        val=560; key='expTime'
        self.assertHeader(header, val, key)
        
        val='u%'; key='dataType'
        self.assertHeader(header, val, key)        
        
        val=16; key='pixBit'
        self.assertHeader(header, val, key) 
        
        val='01'; key='data'
        self.assertHeader(header, val, key) 
               
        val=151; key='numPixX'
        self.assertHeader(header, val, key)         
        
        val=151; key='numPixY'
        self.assertHeader(header, val, key)  
        
        val='      '; key='reserve'
        self.assertHeader(header, val, key)
        
        val=None; key='test'
        self.assertHeader(header, val, key)
                
        
    def assertHeader(self, header, val, key):
        res=guiderfitsheader.getHeaderValue(header, key)
        self.assertEqual(val, res)   
    
    def testValidateStatusVal(self):
        aliasVal='test'
        val='test'
        res=guiderfitsheader.validateStatusVal(aliasVal)
        self.assertEqual(val, res)
    
        aliasVal=3.0
        val=3.0
        res=guiderfitsheader.validateStatusVal(aliasVal)
        self.assertEqual(val, res)
        
        aliasVal=None
        val=None
        res=guiderfitsheader.validateStatusVal(aliasVal)
        self.assertEqual(val, res)
        
        aliasVal = STATNONE
        val=None
        res=guiderfitsheader.validateStatusVal(aliasVal)
        self.assertEqual(val, res)        
                
        aliasVal == STATERROR
        val=None
        res=guiderfitsheader.validateStatusVal(aliasVal)
        self.assertEqual(val, res)       
    
    def testCalcLST(self):
        sec=1156606274
        usec=636666  
        ut1=0.01
        val = '03:28:17.629'
        res= wcs.calcLST(sec, usec, ut1, format='%02d:%02d:%02d.%s')
        self.assertEqual(val, res)
##        
#    
    def testSidereal(self):
        year=2006; month=8; day=26; hour=15; min=31; sec=14.65 
        val=12497.6295148
        res=wcs.sidereal(year, month, day, hour, min, sec)
        print 'test sidereal ', val, res
        self.assertAlmostEqual(val, res, 6)
    
    def testCalcGST(self):
        ut =55874.65
        tu =0.0665064120465
        
        val=49812.8901445
        
        res=wcs.calcGST(tu, ut)
        print val, res
        self.assertAlmostEqual(val, res, 6)
    
    def testCalcJD(self):
        year=2006; month=8; day=26; hour=15; min=31; sec=14.65 
        val=2453974.1467
        res=wcs.calcJD(year, month, day, hour, min, sec)
        self.assertAlmostEqual(val, res, 4)
    
    def testAdjustTime(self):
        
        sec=1156606274
        usec=636666  
        ut1=0.01
        val=(2006, 8, 26, 15, 31, 14.65)
        year, month, day, hour, min, sec= wcs.adjustTime(sec, usec, ut1)
        self.assertEquals(val, (year, month, day, hour, min, sec))
         
    def testCalcMJD(self):
        sec=1156606274
        usec=636666  
        ut1=0.01
        val=53973.646697337739
        res=wcs.calcMJD(sec, usec, ut1) 
        self.assertAlmostEqual(val, res, 6) 
        
        ut1=None
        val=None
        res=wcs.calcMJD(sec, usec, ut1) 
        self.assertEqual(val, res) 
        
        ut1=STATNONE
        res=wcs.calcMJD(sec, usec, ut1) 
        self.assertEqual(val, res) 
        
        
        ut1=STATERROR
        res=wcs.calcMJD(sec, usec, ut1) 
        self.assertEqual(val, res)
      
    def testCalcHST (self):
        sec=1163551632
        usec=675184        
        val='14:47:12.675'
        res=wcs.calcHST(sec, usec, format='%02d:%02d:%02d.%d') 
        self.assertEqual(val, res)
                     
    def testCalcUT(self):
               
        sec=1163551632
        usec=675184
        val='00:47:12.675'
        res=wcs.calcUT(sec, usec, format='%02d:%02d:%02d.%d') 
        self.assertEqual(val, res)
        
    def testCalcObsDate(self):
        sec=1163548510.801403
        val='2006-11-14'
        res=wcs.calcObsDate(sec, format='%04d-%02d-%02d')   
        self.assertEqual(val,res)
        
    def testHmsToDeg (self):    
        
        ra='02:14:17.914'
        val=33.574641667
        res=wcs.hmsToDeg (ra)
        self.assertAlmostEqual(val, res, 7)
        
        
    def testDmsToDeg (self):
        dec='+31:49:30.45'
        val=31.825125
        res=wcs.dmsToDeg(dec)
        self.assertAlmostEqual(val, res, 7)    
        
    def testCalcExpTime(self):
        exptime=88
        val=0.088
        res=wcs.calcExpTime(exptime)    
        self.assertEqual(val, res)
        
        exptime=None
        val=None
        res=wcs.calcExpTime(exptime)    
        self.assertEqual(val, res)
        
        
    def testCalcCRPIX(self):
        ccd=512; exp=12; bin=1
        val = 500
        res= wcs.calcCRPIX(ccd, exp, bin)
        self.assertEqual(val, res)
        
        ccd=512; exp=12; bin=None
        val = None
        res= wcs.calcCRPIX(ccd, exp, bin)
        self.assertEqual(val, res)
        
        ccd=512; exp=None; bin=1
        val = None
        res= wcs.calcCRPIX(ccd, exp, bin)
        self.assertEqual(val, res)
        
        ccd=None; exp=12; bin=1
        val = None
        res= wcs.calcCRPIX(ccd, exp, bin)
        self.assertEqual(val, res)
   
    def testCalcCDELT(self):
        cdelt=1.0; bin=3.0
        val=3.0
        res=wcs.calcCDELT(cdelt, bin)
        self.assertEqual(val, res)
        
        cdelt=None; bin=3.0
        val=None
        res=wcs.calcCDELT(cdelt, bin)
        self.assertEqual(val, res)
        
        cdelt=1.0; bin=None
        val=None
        res=wcs.calcCDELT(cdelt, bin)
        self.assertEqual(val, res)
       
    def testCalcCD(self):
        pc = 1.0; cd =2.0
        val=2.0    
        res=wcs.calcCD(pc, cd)    
        self.assertEqual(val, res)
    
        pc = None; cd =2.0
        val=None    
        res=wcs.calcCD(pc, cd)    
        self.assertEqual(val, res)    
    
        pc = 1.0; cd =None
        val=None    
        res=wcs.calcCD(pc, cd)    
        self.assertEqual(val, res)  
    
    def testPC(self):
        
        # link flag=08
        irot_tel='LINK'; imgrot_flag='08'; insrotpa=90.0; altitude=90; azimuth=-90; imgrot=45.0
        
        # expected values
        ep11=0.84037746045218853; ep12=-0.54200159037029616; ep21=0.54200159037029616; ep22=0.84037746045218853
         
        p11, p12, p21, p22= wcs.calcPC(irot_tel, imgrot_flag, insrotpa, altitude, azimuth, imgrot)
    
        self.assertEquals((ep11, ep12, ep21, ep22),(p11, p12, p21, p22))
        
        # link flag=02
        irot_tel='LINK'; imgrot_flag='02'; insrotpa=90.0; altitude=90; azimuth=-90; imgrot=45.0
        ep11=0.84037746045218853; ep12=-0.54200159037029616; ep21=0.54200159037029616; ep22=0.84037746045218853
        p11, p12, p21, p22= wcs.calcPC(irot_tel, imgrot_flag, insrotpa, altitude, azimuth, imgrot)
        self.assertEquals((ep11, ep12, ep21, ep22),(p11, p12, p21, p22))
       
        # link flag=none   
        irot_tel='LINK'; imgrot_flag='None'; insrotpa=90.0; altitude=90; azimuth=-90; imgrot=45.0
        ep11=-0.52398590597007955;  ep12=-0.85172693414304734; ep21=-0.85172693414304734; ep22=0.52398590597007955
        p11,p12,p21,p22= wcs.calcPC(irot_tel, imgrot_flag, insrotpa, altitude, azimuth, imgrot)
        self.assertEquals((ep11, ep12, ep21, ep22),(p11, p12, p21, p22))

        # free flag=08
        irot_tel='FREE'; imgrot_flag='08'; insrotpa=90.0; altitude=90; azimuth=-90; imgrot=45.0 
        ep11=0.84037746045218842; ep12=-0.54200159037029638; ep21=0.54200159037029638; ep22=0.84037746045218842
        p11, p12,p21,p22= wcs.calcPC(irot_tel, imgrot_flag, insrotpa, altitude, azimuth, imgrot)
        self.assertEquals((ep11, ep12, ep21, ep22),(p11, p12, p21, p22))

        # free flag=02
        irot_tel='FREE'; imgrot_flag='02'; insrotpa=90.0; altitude=90; azimuth=-90; imgrot=45.0 
        ep11=0.84037746045218842; ep12=-0.54200159037029638; ep21=0.54200159037029638; ep22=0.84037746045218842
        p11, p12,p21,p22= wcs.calcPC(irot_tel, imgrot_flag, insrotpa, altitude, azimuth, imgrot)
        self.assertEquals((ep11, ep12, ep21, ep22),(p11, p12, p21, p22))

        # free flag=none 
        irot_tel='FREE'; imgrot_flag='None'; insrotpa=90.0; altitude=90; azimuth=-90; imgrot=45.0 
        ep11=-0.52398590597007955;  ep12=-0.85172693414304734; ep21=-0.85172693414304734; ep22=0.52398590597007955
        p11, p12,p21,p22= wcs.calcPC(irot_tel, imgrot_flag, insrotpa, altitude, azimuth, imgrot)
        self.assertEquals((ep11, ep12, ep21, ep22),(p11, p12, p21, p22))

        # error case 
        irot_tel=None; imgrot_flag='None'; insrotpa=90.0; altitude=90; azimuth=-90; imgrot=45.0 
        ep11=None;  ep12=None; ep21=None; ep22=None
        p11, p12,p21,p22= wcs.calcPC(irot_tel, imgrot_flag, insrotpa, altitude, azimuth, imgrot)
        self.assertEquals((ep11, ep12, ep21, ep22),(p11, p12, p21, p22))

        # error case 
        irot_tel='FREE'; imgrot_flag='None'; insrotpa=STATNONE; altitude=90; azimuth=-90; imgrot=45.0 
        ep11=None;  ep12=None; ep21=None; ep22=None
        p11, p12,p21,p22= wcs.calcPC(irot_tel, imgrot_flag, insrotpa, altitude, azimuth, imgrot)
        self.assertEquals((ep11, ep12, ep21, ep22),(p11, p12, p21, p22))

        # error case 
        irot_tel='FREE'; imgrot_flag='None'; insrotpa=90.0; altitude=STATERROR; azimuth=-90; imgrot=45.0 
        ep11=None;  ep12=None; ep21=None; ep22=None
        p11, p12,p21,p22= wcs.calcPC(irot_tel, imgrot_flag, insrotpa, altitude, azimuth, imgrot)
        self.assertEquals((ep11, ep12, ep21, ep22),(p11, p12, p21, p22))

       
    def testEq200(self):

        ra_deg=321.24749756
        dec_deg=-37.26398849
        
        ra, dec= wcs.eq2000(ra_deg, dec_deg, 2000)  
        
        eRA='21:24:59.399'
        eDEC='-37:15:50.36'
        
        self.assertEquals((eRA, eDEC),(ra, dec))
        
        ra_deg=48.78401184
        dec_deg=14.89663601
        
        ra, dec= wcs.eq2000(ra_deg, dec_deg, 2000)
       
        eRA='03:15:08.163'
        eDEC='+14:53:47.89'
      
        self.assertEquals((eRA, eDEC),(ra, dec))
      
        
        ra_deg=3.58530426
        dec_deg=-1.18520558
        
        ra, dec= wcs.eq2000(ra_deg, dec_deg, 2000)  
        
        eRA='00:14:20.473'
        eDEC='-01:11:06.74'
        
        self.assertEquals((eRA, eDEC),(ra, dec))
   
        ra, dec= wcs.eq2000(ra_deg, None, 2000)
        self.assertEquals((None, None),(ra, dec))
        
        ra, dec= wcs.eq2000(ra_deg, dec_deg, STATNONE)
        self.assertEquals((None, None),(ra, dec))  
        
        ra, dec= wcs.eq2000(STATERROR, dec_deg, 2000)
        self.assertEquals((None, None),(ra, dec))  
        
        

    ###### AG CASS #####    
    def testAgCassGuiderKeyword(self):
               
        usec=tv_usec=636996     # time sec
        sec=tv_sec=1156606274   # time milisec
        
        header="0006AG%%CASS1x1%009701880151015100000560u%160101510151      "    # header
             
        vals=self.keyVal
        
        aliasVal=self.aliasVal
        keyVal=self.keyVal
                
        vals['CRPIX1']=159.0;vals['CRPIX2']=68.0; vals['CRVAL1']=33.574641667; vals['CRVAL2']=31.82512474; 
        vals['BIN-FCT1']=vals['BIN-FCT2']=1;vals['PRD-MIN1']=97;  vals['PRD-MIN2']=188 
        vals['PRD-RNG1']=151; vals['PRD-RNG2']=151
        vals['RA']='02:14:17.914'; vals['DEC']='+31:49:30.45'; vals['EQUINOX']=2000.0
        vals['RA2000']='02:14:17.914'; vals['DEC2000']='+31:49:30.45';
        vals['CDELT1']=vals['CDELT2']=vals['CD1_1']=vals['CD2_2']=0.000026044
        vals['ALTITUDE']=89.0; vals['AZIMUTH']=-90.0;
        vals['DATE-OBS']='2006-08-26'; vals['UT']='15:31:14.636'; vals['MJD']=53973.6466972;vals['HST']='05:31:14.636'; vals['LST']='03:28:17.619' 
        vals['EXPTIME']=0.56; 
        vals['AIRMASS']=9.99999; vals['ZD']=9.999; vals['DOM-PRS']=9.99
        vals['OBSERVER']='OCS, SS, TEL'; vals['PROP-ID']='o98003'; vals['TELESCOP']='Subaru'
        vals['TELFOCUS'] = vals['FOC-POS'] = 'Cassegrain';vals['FOC-VAL'] = 7.5
        vals['M2-POS1']=1.0; vals['M2-POS2']=1.1; vals['M2-ANG1']=1.2; vals['M2-ANG2']=1.3
        vals['AG-PRB1']=140.0; vals['AG-PRB2']=90.0 ; vals['INSROT']=90.0
        vals['FRAMEID'] = vals['EXP-ID']= self.frameid;  vals['OBS-ALOC'] = 'Observation'
        vals['INSTRUME']='AG';  vals['DATA-TYP']='OBJECT'; vals['DETECTOR']='AG'; vals['GAIN']=1.0; vals['DET-TMP']=-40.0;  vals['FILTER01']='AGFILTER'
        
        aliasVal['FITS.SBR.RA']='02:14:17.914'; aliasVal['FITS.SBR.DEC']='+31:49:30.45'; aliasVal['FITS.SBR.EQUINOX']=2000.0;
        aliasVal['FITS.SBR.ALTITUDE']=89.0; aliasVal['FITS.SBR.AZIMUTH']=-90.0; aliasVal['FITS.SBR.UT1-UTC']=0.0;  
        aliasVal['FITS.SBR.AIRMASS']=9.99999; aliasVal['FITS.SBR.ZD']=9.999; aliasVal['FITS.SBR.DOM-PRS']=9.99;
        aliasVal['FITS.VGW.OBSERVER']='OCS, SS, TEL'; aliasVal['FITS.VGW.PROP-ID']='o98003'; aliasVal['FITS.SBR.TELESCOP']='Subaru';
        aliasVal['FITS.SBR.TELFOCUS']='Cassegrain'; aliasVal['FITS.SBR.FOC-VAL']=7.5; 
        aliasVal['FITS.SBR.M2-POS1']=1.0; aliasVal['FITS.SBR.M2-POS2']=1.1; aliasVal['FITS.SBR.M2-ANG1']=1.2; aliasVal['FITS.SBR.M2-ANG2']=1.3;
        aliasVal['FITS.SBR.AG-PRBR']=140.0; aliasVal['FITS.SBR.AG-PRBT']=90.0;aliasVal['FITS.SBR.INSROT']=90.0;
        #aliasVal['FITS.SBR.AG-PRBX']=10.0; aliasVal['FITS.SBR.AG-PRBY']=20.0; aliasVal['FITS.SBR.SV-PRB']=100.0; 
        #aliasVal['FITS.SBR.IMGROT']=45.0; aliasVal['FITS.SBR.IMR-TYPE']='RED'; 
        aliasVal['FITS.SBR.ADC-TYPE']='NULL'; aliasVal['FITS.SBR.ADC']=999.999;
        aliasVal['FITS.VGW.OBS-ALOC']='Observation';  
        aliasVal['FITS.SBR.DET-TMPAG']=-40.0; 
        #aliasVal['FITS.SBR.DET-TMPSV']=-41.0;aliasVal['FITS.SBR.DET-TMPSH']=-42.0;
        #aliasVal['FITS.VGW.IROT_TELESCOPE']='LINK'; aliasVal['FITS.VGW.IMGROT_FLG']='08';  aliasVal['FITS.VGW.INSROTPA']=90.0;
                    
        self.assertFitskeyword(self.frameid, header, sec, usec, keyVal,  aliasVal, vals)


    ###### AG NSOP #####
    def testAgNsopGuiderKeyword(self):
        
        usec=tv_usec=636996     # time sec
        sec=tv_sec=1156606274   # time milisec
        
        header="0006AG%%NSOP1x1%009701880151015100000560u%160101510151      "    # header

        vals=self.keyVal 
        aliasVal=self.aliasVal
        keyVal=self.keyVal
        
        vals['CRPIX1']=159.0;vals['CRPIX2']=68.0; vals['CRVAL1']=33.574641667; vals['CRVAL2']=31.82512474; 
        vals['BIN-FCT1']=vals['BIN-FCT2']=1;vals['PRD-MIN1']=97;  vals['PRD-MIN2']=188 
        vals['PRD-RNG1']=151; vals['PRD-RNG2']=151
        vals['RA']='02:14:17.914'; vals['DEC']='+31:49:30.45'; vals['EQUINOX']=2000.0
        vals['RA2000']='02:14:17.914'; vals['DEC2000']='+31:49:30.45';
        vals['CDELT1']=vals['CDELT2']=vals['CD1_1']=vals['CD2_2']=0.000025252
        vals['ALTITUDE']=89.0; vals['AZIMUTH']=-90.0;
        vals['DATE-OBS']='2006-08-26'; vals['UT']='15:31:14.636'; vals['MJD']=53973.6466972;vals['HST']='05:31:14.636'; vals['LST']='03:28:17.619' 
        vals['EXPTIME']=0.56; 
        vals['AIRMASS']=9.99999; vals['ZD']=9.999; vals['DOM-PRS']=9.99
        vals['OBSERVER']='OCS, SS, TEL'; vals['PROP-ID']='o98003'; vals['TELESCOP']='Subaru'
        vals['TELFOCUS'] = vals['FOC-POS'] = 'Nasmyth-Opt'
        vals['FOC-VAL'] = 7.5
        vals['M2-POS1']=1.0; vals['M2-POS2']=1.1; vals['M2-ANG1']=1.2; vals['M2-ANG2']=1.3
        vals['AG-PRB1']=140.0; vals['AG-PRB2']=90.0 
        #vals['INSROT']=90.0
        vals['IMGROT']=45.0; vals['IMR-TYPE']='RED' 
        vals['ADC-TYPE']='NULL';  vals['ADC']=999.999
        vals['FRAMEID'] = vals['EXP-ID']= self.frameid;  vals['OBS-ALOC'] = 'Observation'
        vals['INSTRUME']='AG';  vals['DATA-TYP']='OBJECT'; vals['DETECTOR']='AG'; vals['GAIN']=1.0; vals['DET-TMP']=-40.0;  vals['FILTER01']='AGFILTER'        
        
        aliasVal['FITS.SBR.RA']='02:14:17.914'; aliasVal['FITS.SBR.DEC']='+31:49:30.45'; aliasVal['FITS.SBR.EQUINOX']=2000.0;
        aliasVal['FITS.SBR.ALTITUDE']=89.0; aliasVal['FITS.SBR.AZIMUTH']=-90.0; aliasVal['FITS.SBR.UT1-UTC']=0.0;  
        aliasVal['FITS.SBR.AIRMASS']=9.99999; aliasVal['FITS.SBR.ZD']=9.999; aliasVal['FITS.SBR.DOM-PRS']=9.99;
        aliasVal['FITS.VGW.OBSERVER']='OCS, SS, TEL'; aliasVal['FITS.VGW.PROP-ID']='o98003'; aliasVal['FITS.SBR.TELESCOP']='Subaru';
        aliasVal['FITS.SBR.TELFOCUS']='Nasmyth-Opt'
        aliasVal['FITS.SBR.FOC-VAL']=7.5; 
        aliasVal['FITS.SBR.M2-POS1']=1.0; aliasVal['FITS.SBR.M2-POS2']=1.1; aliasVal['FITS.SBR.M2-ANG1']=1.2; aliasVal['FITS.SBR.M2-ANG2']=1.3;
        aliasVal['FITS.SBR.AG-PRBR']=140.0; aliasVal['FITS.SBR.AG-PRBT']=90.0
        #aliasVal['FITS.SBR.INSROT']=90.0
        #aliasVal['FITS.SBR.AG-PRBX']=10.0; aliasVal['FITS.SBR.AG-PRBY']=20.0; aliasVal['FITS.SBR.SV-PRB']=100.0; 
        aliasVal['FITS.SBR.IMGROT']=45.0; aliasVal['FITS.SBR.IMR-TYPE']='RED'; 
        aliasVal['FITS.SBR.ADC-TYPE']='NULL'
        aliasVal['FITS.SBR.ADC']=999.999;
        aliasVal['FITS.VGW.OBS-ALOC']='Observation';  
        aliasVal['FITS.SBR.DET-TMPAG']=-40.0; 
        #aliasVal['FITS.SBR.DET-TMPSV']=-41.0;aliasVal['FITS.SBR.DET-TMPSH']=-42.0;
        #aliasVal['FITS.VGW.IROT_TELESCOPE']='LINK'; aliasVal['FITS.VGW.IMGROT_FLG']='08';  aliasVal['FITS.VGW.INSROTPA']=90.0;
      
        self.assertFitskeyword(self.frameid, header, sec, usec, keyVal,  aliasVal, vals)


    ###### AG NSIR #####
    def testAgNsirGuiderKeyword(self):
        
        usec=tv_usec=636996     # time sec
        sec=tv_sec=1156606274   # time milisec
        
        header="0006AG%%NSIR1x1%009701880151015100000560u%160101510151      "    # header
        aliasVal=self.aliasVal                            # status alias values
        keyVal=self.keyVal    
        vals=self.keyVal
        
        vals['CRPIX1']=159.0;vals['CRPIX2']=68.0; vals['CRVAL1']=33.574641667; vals['CRVAL2']=31.82512474; 
        vals['BIN-FCT1']=vals['BIN-FCT2']=1;vals['PRD-MIN1']=97;  vals['PRD-MIN2']=188 
        vals['PRD-RNG1']=151; vals['PRD-RNG2']=151
        vals['RA']='02:14:17.914'; vals['DEC']='+31:49:30.45'; vals['EQUINOX']=2000.0
        vals['RA2000']='02:14:17.914'; vals['DEC2000']='+31:49:30.45';
        vals['CDELT1']=vals['CD1_1']=0.000023825
        vals['CDELT2']=vals['CD2_2']=0.000023823
        vals['ALTITUDE']=89.0; vals['AZIMUTH']=-90.0;
        vals['DATE-OBS']='2006-08-26'; vals['UT']='15:31:14.636'; vals['MJD']=53973.6466972;vals['HST']='05:31:14.636'; vals['LST']='03:28:17.619' 
        vals['EXPTIME']=0.56; 
        vals['AIRMASS']=9.99999; vals['ZD']=9.999; vals['DOM-PRS']=9.99
        vals['OBSERVER']='OCS, SS, TEL'; vals['PROP-ID']='o98003'; vals['TELESCOP']='Subaru'
        vals['TELFOCUS'] = vals['FOC-POS'] = 'Nasmyth-IR'
        vals['FOC-VAL'] = 7.5
        vals['M2-POS1']=1.0; vals['M2-POS2']=1.1; vals['M2-ANG1']=1.2; vals['M2-ANG2']=1.3
        vals['AG-PRB1']=140.0; vals['AG-PRB2']=90.0 
        # vals['INSROT']=90.0
        vals['IMGROT']=46.0; vals['IMR-TYPE']='BLUE' 
        vals['ADC-TYPE']='NULL';  vals['ADC']=999.999
        vals['FRAMEID'] = vals['EXP-ID']= self.frameid;  vals['OBS-ALOC'] = 'Observation'
        vals['INSTRUME']='AG';  vals['DATA-TYP']='OBJECT'; vals['DETECTOR']='AG'; vals['GAIN']=1.0; vals['DET-TMP']=-40.0;  vals['FILTER01']='AGFILTER'        
           
        aliasVal['FITS.SBR.RA']='02:14:17.914'; aliasVal['FITS.SBR.DEC']='+31:49:30.45'; aliasVal['FITS.SBR.EQUINOX']=2000.0;
        aliasVal['FITS.SBR.ALTITUDE']=89.0; aliasVal['FITS.SBR.AZIMUTH']=-90.0; aliasVal['FITS.SBR.UT1-UTC']=0.0;  
        aliasVal['FITS.SBR.AIRMASS']=9.99999; aliasVal['FITS.SBR.ZD']=9.999; aliasVal['FITS.SBR.DOM-PRS']=9.99;
        aliasVal['FITS.VGW.OBSERVER']='OCS, SS, TEL'; aliasVal['FITS.VGW.PROP-ID']='o98003'; aliasVal['FITS.SBR.TELESCOP']='Subaru';
        aliasVal['FITS.SBR.TELFOCUS']='Nasmyth-IR'
        aliasVal['FITS.SBR.FOC-VAL']=7.5; 
        aliasVal['FITS.SBR.M2-POS1']=1.0; aliasVal['FITS.SBR.M2-POS2']=1.1; aliasVal['FITS.SBR.M2-ANG1']=1.2; aliasVal['FITS.SBR.M2-ANG2']=1.3;
        aliasVal['FITS.SBR.AG-PRBR']=140.0; aliasVal['FITS.SBR.AG-PRBT']=90.0;aliasVal['FITS.SBR.INSROT']=90.0;
        #aliasVal['FITS.SBR.AG-PRBX']=10.0; aliasVal['FITS.SBR.AG-PRBY']=20.0; aliasVal['FITS.SBR.SV-PRB']=100.0; 
        aliasVal['FITS.SBR.IMGROT']=46.0;  aliasVal['FITS.SBR.IMR-TYPE']='BLUE'; 
        aliasVal['FITS.SBR.ADC-TYPE']='NULL'; aliasVal['FITS.SBR.ADC']=999.999;
        aliasVal['FITS.VGW.OBS-ALOC']='Observation';  
        aliasVal['FITS.SBR.DET-TMPAG']=-40.0; 
        #aliasVal['FITS.SBR.DET-TMPSV']=-41.0;aliasVal['FITS.SBR.DET-TMPSH']=-42.0;
        #aliasVal['FITS.VGW.IROT_TELESCOPE']='LINK'; aliasVal['FITS.VGW.IMGROT_FLG']='08';  aliasVal['FITS.VGW.INSROTPA']=90.0;
        self.assertFitskeyword(self.frameid, header, sec, usec, keyVal,  aliasVal, vals)
        
    
    ###### AG PFVS #####   
    def testAgPfvsGuiderKeyword(self):        
        
        usec=tv_usec=636996     # time sec
        sec=tv_sec=1156606274   # time milisec
        
        header="0006AG%%PFVS1x1%009701880151015100000560u%160101510151      "    # header
        aliasVal=self.aliasVal                            # status alias values
        keyVal=self.keyVal    
        vals=self.keyVal
       
        vals['CRPIX1']=159.0;vals['CRPIX2']=68.0; vals['CRVAL1']=33.574641667; vals['CRVAL2']=31.82512474; 
        vals['BIN-FCT1']=vals['BIN-FCT2']=1;vals['PRD-MIN1']=97;  vals['PRD-MIN2']=188 
        vals['PRD-RNG1']=151; vals['PRD-RNG2']=151
        vals['RA']='02:14:17.914'; vals['DEC']='+31:49:30.45'; vals['EQUINOX']=2000.0
        vals['RA2000']='02:14:17.914'; vals['DEC2000']='+31:49:30.45';
        vals['CDELT1']=vals['CD1_1']=0.000026093
        vals['CDELT2']=vals['CD2_2']=0.000026093
        vals['ALTITUDE']=89.0; vals['AZIMUTH']=-90.0;
        vals['DATE-OBS']='2006-08-26'; vals['UT']='15:31:14.636'; vals['MJD']=53973.6466972;vals['HST']='05:31:14.636'; vals['LST']='03:28:17.619' 
        vals['EXPTIME']=0.56; 
        vals['AIRMASS']=9.99999; vals['ZD']=9.999; vals['DOM-PRS']=9.99
        vals['OBSERVER']='OCS, SS, TEL'; vals['PROP-ID']='o98003'; vals['TELESCOP']='Subaru'
        vals['TELFOCUS'] = vals['FOC-POS'] = 'Prime'
        vals['FOC-VAL'] = 7.5
        vals['M2-POS1']=1.0; vals['M2-POS2']=1.1; vals['M2-ANG1']=1.2; vals['M2-ANG2']=1.3
        vals['AG-PRB1']=10.0; vals['AG-PRB2']=20.0 ; vals['INSROT']=90.0
        #vals['IMGROT']=46.0; vals['IMR-TYPE']='BLUE' 
        #vals['ADC-TYPE']='NULL';  vals['ADC']=999.999
        vals['FRAMEID'] = vals['EXP-ID']= self.frameid;  vals['OBS-ALOC'] = 'Observation'
        vals['INSTRUME']='AG';  vals['DATA-TYP']='OBJECT'; vals['DETECTOR']='AG'; vals['GAIN']=1.0; vals['DET-TMP']=-40.0;  vals['FILTER01']='AGFILTER'   
        
        aliasVal['FITS.SBR.RA']='02:14:17.914'; aliasVal['FITS.SBR.DEC']='+31:49:30.45'; aliasVal['FITS.SBR.EQUINOX']=2000.0;
        aliasVal['FITS.SBR.ALTITUDE']=89.0; aliasVal['FITS.SBR.AZIMUTH']=-90.0; aliasVal['FITS.SBR.UT1-UTC']=0.0;  
        aliasVal['FITS.SBR.AIRMASS']=9.99999; aliasVal['FITS.SBR.ZD']=9.999; aliasVal['FITS.SBR.DOM-PRS']=9.99;
        aliasVal['FITS.VGW.OBSERVER']='OCS, SS, TEL'; aliasVal['FITS.VGW.PROP-ID']='o98003'; aliasVal['FITS.SBR.TELESCOP']='Subaru';
        aliasVal['FITS.SBR.TELFOCUS']='Prime'
        aliasVal['FITS.SBR.FOC-VAL']=7.5; 
        aliasVal['FITS.SBR.M2-POS1']=1.0; aliasVal['FITS.SBR.M2-POS2']=1.1; aliasVal['FITS.SBR.M2-ANG1']=1.2; aliasVal['FITS.SBR.M2-ANG2']=1.3;
        aliasVal['FITS.SBR.AG-PRBX']=10.0; aliasVal['FITS.SBR.AG-PRBY']=20.0;aliasVal['FITS.SBR.INSROT']=90.0;
        #aliasVal['FITS.SBR.AG-PRBX']=10.0; aliasVal['FITS.SBR.AG-PRBY']=20.0; aliasVal['FITS.SBR.SV-PRB']=100.0; 
        #aliasVal['FITS.SBR.IMGROT']=46.0;  aliasVal['FITS.SBR.IMR-TYPE']='BLUE'; 
        #aliasVal['FITS.SBR.ADC-TYPE']='NULL'; aliasVal['FITS.SBR.ADC']=999.999;
        aliasVal['FITS.VGW.OBS-ALOC']='Observation';  
        aliasVal['FITS.SBR.DET-TMPAG']=-40.0; 
    
        self.assertFitskeyword(self.frameid, header, sec, usec, keyVal,  aliasVal, vals)


    ###### AG PFIR #####
    def testAgPfirGuiderKeyword(self):        
        
        usec=tv_usec=636996     # time sec
        sec=tv_sec=1156606274   # time milisec
        
        header="0006AG%%PFIR1x1%009701880151015100000560u%160101510151      "    # header
        aliasVal=self.aliasVal                            # status alias values
        keyVal=self.keyVal    
        vals=self.keyVal
        
        vals['CRPIX1']=159.0;vals['CRPIX2']=68.0; vals['CRVAL1']=33.574641667; vals['CRVAL2']=31.82512474; 
        vals['BIN-FCT1']=vals['BIN-FCT2']=1;vals['PRD-MIN1']=97;  vals['PRD-MIN2']=188 
        vals['PRD-RNG1']=151; vals['PRD-RNG2']=151
        vals['RA']='02:14:17.914'; vals['DEC']='+31:49:30.45'; vals['EQUINOX']=2000.0
        vals['RA2000']='02:14:17.914'; vals['DEC2000']='+31:49:30.45';
        vals['CDELT1']=vals['CD1_1']=0.000026093
        vals['CDELT2']=vals['CD2_2']=0.000026093
        vals['ALTITUDE']=89.0; vals['AZIMUTH']=-90.0;
        vals['DATE-OBS']='2006-08-26'; vals['UT']='15:31:14.636'; vals['MJD']=53973.6466972;vals['HST']='05:31:14.636'; vals['LST']='03:28:17.619' 
        vals['EXPTIME']=0.56; 
        vals['AIRMASS']=9.99999; vals['ZD']=9.999; vals['DOM-PRS']=9.99
        vals['OBSERVER']='OCS, SS, TEL'; vals['PROP-ID']='o98003'; vals['TELESCOP']='Subaru'
        vals['TELFOCUS'] = vals['FOC-POS'] = 'Prime'
        vals['FOC-VAL'] = 7.5
        vals['M2-POS1']=1.0; vals['M2-POS2']=1.1; vals['M2-ANG1']=1.2; vals['M2-ANG2']=1.3
        vals['AG-PRB1']=10.0; vals['AG-PRB2']=20.0 ; vals['INSROT']=9999.999
        #vals['IMGROT']=46.0; vals['IMR-TYPE']='BLUE' 
        #vals['ADC-TYPE']='NULL';  vals['ADC']=999.999
        vals['FRAMEID'] = vals['EXP-ID']= self.frameid;  vals['OBS-ALOC'] = 'Observation'
        vals['INSTRUME']='AG';  vals['DATA-TYP']='OBJECT'; vals['DETECTOR']='AG'; vals['GAIN']=1.0; vals['DET-TMP']=-40.0;  vals['FILTER01']='AGFILTER'   
        
        aliasVal['FITS.SBR.RA']='02:14:17.914'; aliasVal['FITS.SBR.DEC']='+31:49:30.45'; aliasVal['FITS.SBR.EQUINOX']=2000.0;
        aliasVal['FITS.SBR.ALTITUDE']=89.0; aliasVal['FITS.SBR.AZIMUTH']=-90.0; aliasVal['FITS.SBR.UT1-UTC']=0.0;  
        aliasVal['FITS.SBR.AIRMASS']=9.99999; aliasVal['FITS.SBR.ZD']=9.999; aliasVal['FITS.SBR.DOM-PRS']=9.99;
        aliasVal['FITS.VGW.OBSERVER']='OCS, SS, TEL'; aliasVal['FITS.VGW.PROP-ID']='o98003'; aliasVal['FITS.SBR.TELESCOP']='Subaru';
        aliasVal['FITS.SBR.TELFOCUS']='Prime'
        aliasVal['FITS.SBR.FOC-VAL']=7.5; 
        aliasVal['FITS.SBR.M2-POS1']=1.0; aliasVal['FITS.SBR.M2-POS2']=1.1; aliasVal['FITS.SBR.M2-ANG1']=1.2; aliasVal['FITS.SBR.M2-ANG2']=1.3;
        aliasVal['FITS.SBR.AG-PRBX']=10.0; aliasVal['FITS.SBR.AG-PRBY']=20.0; 
        #aliasVal['FITS.SBR.INSROT']=90.0
        #aliasVal['FITS.SBR.AG-PRBX']=10.0; aliasVal['FITS.SBR.AG-PRBY']=20.0; aliasVal['FITS.SBR.SV-PRB']=100.0; 
        #aliasVal['FITS.SBR.IMGROT']=46.0;  aliasVal['FITS.SBR.IMR-TYPE']='BLUE'; 
        #aliasVal['FITS.SBR.ADC-TYPE']='NULL'; aliasVal['FITS.SBR.ADC']=999.999;
        aliasVal['FITS.VGW.OBS-ALOC']='Observation';  
        aliasVal['FITS.SBR.DET-TMPAG']=-40.0; 
    
    
        self.assertFitskeyword(self.frameid, header, sec, usec, keyVal,  aliasVal, vals)


    ###### SV NSOP #####   
    def testSvNsopGuiderKeyword(self):        
        
        usec=tv_usec=636996     # time sec
        sec=tv_sec=1156606274   # time milisec
        
        header="0006SV%%NSOP1x1%009701880151015100000560u%160101510151      "
        aliasVal=self.aliasVal                            # status alias values
        keyVal=self.keyVal    
        vals=self.keyVal
    

        vals['CRPIX1']=159.0;vals['CRPIX2']=68.0; vals['CRVAL1']=33.574641667; vals['CRVAL2']=31.82512474; 
        vals['BIN-FCT1']=vals['BIN-FCT2']=1;vals['PRD-MIN1']=97;  vals['PRD-MIN2']=188 
        vals['PRD-RNG1']=151; vals['PRD-RNG2']=151
        vals['RA']='02:14:17.914'; vals['DEC']='+31:49:30.45'; vals['EQUINOX']=2000.0
        vals['RA2000']='02:14:17.914'; vals['DEC2000']='+31:49:30.45';
        vals['PC001001']=0.8403774; vals['PC001002']=-0.54200159037;
        vals['PC002001']=0.54200159037; vals['PC002002']=0.840377460
        vals['CDELT1']=vals['CDELT2']=0.000034722
        vals['CD1_1']=0.0000291795; vals['CD1_2']= -0.000018819379220837; vals['CD2_1']= 0.0000188193792208
        vals['CD2_2']=0.0000291795
        vals['ALTITUDE']=89.0; vals['AZIMUTH']=-90.0;
        vals['DATE-OBS']='2006-08-26'; vals['UT']='15:31:14.636'; vals['MJD']=53973.6466972;vals['HST']='05:31:14.636'; vals['LST']='03:28:17.619' 
        vals['EXPTIME']=0.56; 
        #vals['AIRMASS']=9.99999; vals['ZD']=9.999; vals['DOM-PRS']=9.99
        vals['OBSERVER']='OCS, SS, TEL'; vals['PROP-ID']='o98003'; vals['TELESCOP']='Subaru'
        vals['TELFOCUS'] = vals['FOC-POS'] = 'Nasmyth-Opt'
        vals['FOC-VAL'] = 7.5
        vals['M2-POS1']=1.0; vals['M2-POS2']=1.1; vals['M2-ANG1']=1.2; vals['M2-ANG2']=1.3
        vals['AG-PRB1']=10.0; vals['AG-PRB2']=20.0
        #vals['INSROT']=90.0
        vals['SV-PRB']=100.100
        vals['IMGROT']=46.0; vals['IMR-TYPE']='BLUE' 
        #vals['ADC-TYPE']='NULL';  vals['ADC']=999.999
        vals['FRAMEID'] = vals['EXP-ID']= self.frameid;  vals['OBS-ALOC'] = 'Observation'
        vals['INSTRUME']='SV';  vals['DATA-TYP']='OBJECT'; vals['DETECTOR']='SV'; vals['GAIN']=1.0; vals['DET-TMP']=-41.0;  vals['FILTER01']='Filter1'   


        aliasVal['FITS.SBR.RA']='02:14:17.914'; aliasVal['FITS.SBR.DEC']='+31:49:30.45'; aliasVal['FITS.SBR.EQUINOX']=2000.0;
        aliasVal['FITS.SBR.ALTITUDE']=89.0; aliasVal['FITS.SBR.AZIMUTH']=-90.0; aliasVal['FITS.SBR.UT1-UTC']=0.0;  
        aliasVal['FITS.SBR.AIRMASS']=9.99999; aliasVal['FITS.SBR.ZD']=9.999; aliasVal['FITS.SBR.DOM-PRS']=9.99;
        aliasVal['FITS.VGW.OBSERVER']='OCS, SS, TEL'; aliasVal['FITS.VGW.PROP-ID']='o98003'; aliasVal['FITS.SBR.TELESCOP']='Subaru';
        aliasVal['FITS.SBR.TELFOCUS']='Nasmyth-Opt'
        aliasVal['FITS.SBR.FOC-VAL']=7.5; 
        aliasVal['FITS.SBR.M2-POS1']=1.0; aliasVal['FITS.SBR.M2-POS2']=1.1; aliasVal['FITS.SBR.M2-ANG1']=1.2; aliasVal['FITS.SBR.M2-ANG2']=1.3;
        aliasVal['FITS.SBR.AG-PRBR']=10.0; aliasVal['FITS.SBR.AG-PRBT']=20.0
        #;aliasVal['FITS.SBR.INSROT']=90.0;
        
        #aliasVal['FITS.SBR.AG-PRBX']=10.0; aliasVal['FITS.SBR.AG-PRBY']=20.0; 
        aliasVal['FITS.SBR.SV-PRB']=100.100; 
        aliasVal['FITS.SBR.IMGROT']=46.0;  aliasVal['FITS.SBR.IMR-TYPE']='BLUE'; 
        aliasVal['FITS.SBR.ADC-TYPE']='NULL';  aliasVal['FITS.SBR.ADC']=999.999;
        aliasVal['FITS.VGW.OBS-ALOC']='Observation';  
        aliasVal['FITS.VGW.FILTER01']=1.0
        aliasVal['FITS.SBR.DET-TMPSV']=-41.0
        aliasVal['FITS.VGW.IROT_TELESCOPE']='LINK'; aliasVal['FITS.VGW.IMGROT_FLG']='08';  aliasVal['FITS.VGW.INSROTPA']=90.0;
        

        self.assertFitskeyword(self.frameid, header, sec, usec, keyVal,  aliasVal, vals)
        
             
    def testSvCassGuiderKeyword(self):  
               ###### AG PFVS #####
        usec=tv_usec=636996     # time sec
        sec=tv_sec=1156606274   # time milisec
        
        header="0006SV%%CASS1x1%009701880151015100000560u%160101510151      " 
        aliasVal=self.aliasVal                            # status alias values
        keyVal=self.keyVal    
        vals=self.keyVal


        vals['CRPIX1']=159.0;vals['CRPIX2']=68.0; vals['CRVAL1']=33.574641667; vals['CRVAL2']=31.82512474; 
        vals['BIN-FCT1']=vals['BIN-FCT2']=1;vals['PRD-MIN1']=97;  vals['PRD-MIN2']=188 
        vals['PRD-RNG1']=151; vals['PRD-RNG2']=151
        vals['RA']='02:14:17.914'; vals['DEC']='+31:49:30.45'; vals['EQUINOX']=2000.0
        vals['RA2000']='02:14:17.914'; vals['DEC2000']='+31:49:30.45';
        #vals['PC001001']=0.8403774; vals['PC001002']=-0.54200159037;
        #vals['PC002001']=0.54200159037; vals['PC002002']=0.840377460
        vals['CDELT1']=vals['CDELT2']=0.000034722
        vals['CD1_1']=0.00003472199 #; vals['CD1_2']= -0.000018819379220837; vals['CD2_1']= 0.0000188193792208
        vals['CD2_2']=0.00003472199
        vals['ALTITUDE']=89.0; vals['AZIMUTH']=-90.0;
        vals['DATE-OBS']='2006-08-26'; vals['UT']='15:31:14.636'; vals['MJD']=53973.6466972;vals['HST']='05:31:14.636'; vals['LST']='03:28:17.619' 
        vals['EXPTIME']=0.56; 
        vals['AIRMASS']=9.99999; vals['ZD']=9.999; vals['DOM-PRS']=9.99
        vals['OBSERVER']='OCS, SS, TEL'; vals['PROP-ID']='o98003'; vals['TELESCOP']='Subaru'
        vals['TELFOCUS'] = vals['FOC-POS'] = 'Cassegrain'
        vals['FOC-VAL'] = 7.5
        vals['M2-POS1']=1.0; vals['M2-POS2']=1.1; vals['M2-ANG1']=1.2; vals['M2-ANG2']=1.3
        vals['AG-PRB1']=10.0; vals['AG-PRB2']=20.0 ; vals['INSROT']=90.0
        vals['SV-PRB']=100.100
        #vals['IMGROT']=46.0; vals['IMR-TYPE']='BLUE' 
        vals['ADC-TYPE']='NULL';  vals['ADC']=999.999
        vals['FRAMEID'] = vals['EXP-ID']= self.frameid;  vals['OBS-ALOC'] = 'Observation'
        vals['INSTRUME']='SV';  vals['DATA-TYP']='OBJECT'; vals['DETECTOR']='SV'; vals['GAIN']=1.0; vals['DET-TMP']=-41.0;  vals['FILTER01']='Filter1'   


        aliasVal['FITS.SBR.RA']='02:14:17.914'; aliasVal['FITS.SBR.DEC']='+31:49:30.45'; aliasVal['FITS.SBR.EQUINOX']=2000.0;
        aliasVal['FITS.SBR.ALTITUDE']=89.0; aliasVal['FITS.SBR.AZIMUTH']=-90.0; aliasVal['FITS.SBR.UT1-UTC']=0.0;  
        aliasVal['FITS.SBR.AIRMASS']=9.99999; aliasVal['FITS.SBR.ZD']=9.999; aliasVal['FITS.SBR.DOM-PRS']=9.99;
        aliasVal['FITS.VGW.OBSERVER']='OCS, SS, TEL'; aliasVal['FITS.VGW.PROP-ID']='o98003'; aliasVal['FITS.SBR.TELESCOP']='Subaru';
        aliasVal['FITS.SBR.TELFOCUS']='Cassegrain'
        aliasVal['FITS.SBR.FOC-VAL']=7.5; 
        aliasVal['FITS.SBR.M2-POS1']=1.0; aliasVal['FITS.SBR.M2-POS2']=1.1; aliasVal['FITS.SBR.M2-ANG1']=1.2; aliasVal['FITS.SBR.M2-ANG2']=1.3;
        aliasVal['FITS.SBR.AG-PRBR']=10.0; aliasVal['FITS.SBR.AG-PRBT']=20.0;aliasVal['FITS.SBR.INSROT']=90.0;
        
        #aliasVal['FITS.SBR.AG-PRBX']=10.0; aliasVal['FITS.SBR.AG-PRBY']=20.0; 
        aliasVal['FITS.SBR.SV-PRB']=100.100; 
        aliasVal['FITS.SBR.IMGROT']=9999.9999;  aliasVal['FITS.SBR.IMR-TYPE']='BLUE'; 
        aliasVal['FITS.SBR.ADC-TYPE']='NULL'; aliasVal['FITS.SBR.ADC']=999.999;
        aliasVal['FITS.VGW.OBS-ALOC']='Observation';  
        aliasVal['FITS.VGW.FILTER01']=1.0
        aliasVal['FITS.SBR.DET-TMPSV']=-41.0
        aliasVal['FITS.VGW.IROT_TELESCOPE']='LINK'; aliasVal['FITS.VGW.IMGROT_FLG']='08';  aliasVal['FITS.VGW.INSROTPA']=90.0;

        self.assertFitskeyword(self.frameid, header, sec, usec, keyVal,  aliasVal, vals)


    def testShCassGuiderKeyword(self):

        ###### SH CASS #####
        usec=tv_usec=636996     # time sec
        sec=tv_sec=1156606274   # time milisec
        
        header="0006SH%%CASS1x1%009701880151015100000560u%160101510151      "     # header
        aliasVal=self.aliasVal                            # status alias values
        keyVal=self.keyVal
        vals=self.keyVal                            # keyword values
        #print keyVal
        
        
        vals['CRPIX1']=415.0;vals['CRPIX2']=324.0; vals['CRVAL1']=33.574641667; vals['CRVAL2']=31.82512474; 
        vals['BIN-FCT1']=vals['BIN-FCT2']=1;vals['PRD-MIN1']=97;  vals['PRD-MIN2']=188 
        vals['PRD-RNG1']=151; vals['PRD-RNG2']=151
        vals['RA']='02:14:17.914'; vals['DEC']='+31:49:30.45'; vals['EQUINOX']=2000.0
        vals['RA2000']='02:14:17.914'; vals['DEC2000']='+31:49:30.45';
        vals['CDELT1']=vals['CDELT2']=vals['CD1_1']=vals['CD2_2']=0.000026044
        vals['ALTITUDE']=89.0; vals['AZIMUTH']=-90.0;
        vals['DATE-OBS']='2006-08-26'; vals['UT']='15:31:14.636'; vals['MJD']=53973.6466972;vals['HST']='05:31:14.636'; vals['LST']='03:28:17.619' 
        vals['EXPTIME']=0.56; 
        vals['AIRMASS']=9.99999; vals['ZD']=9.999; vals['DOM-PRS']=9.99
        vals['OBSERVER']='OCS, SS, TEL'; vals['PROP-ID']='o98003'; vals['TELESCOP']='Subaru'
        vals['TELFOCUS'] = vals['FOC-POS'] = 'Cassegrain';vals['FOC-VAL'] = 7.5
        vals['M2-POS1']=1.0; vals['M2-POS2']=1.1; vals['M2-ANG1']=1.2; vals['M2-ANG2']=1.3
        vals['AG-PRB1']=140.0; vals['AG-PRB2']=90.0 ; 
        vals['INSROT']=90.0
        vals['FRAMEID'] = vals['EXP-ID']= self.frameid;  vals['OBS-ALOC'] = 'Observation'
        vals['INSTRUME']='SH';  vals['DATA-TYP']='OBJECT'; vals['DETECTOR']='SH'; vals['GAIN']=1.0; vals['DET-TMP']=-40.0;  vals['FILTER01']='SHFILTER'
        
        aliasVal['FITS.SBR.RA']='02:14:17.914'; aliasVal['FITS.SBR.DEC']='+31:49:30.45'; aliasVal['FITS.SBR.EQUINOX']=2000.0;
        aliasVal['FITS.SBR.ALTITUDE']=89.0; aliasVal['FITS.SBR.AZIMUTH']=-90.0; aliasVal['FITS.SBR.UT1-UTC']=0.0;  
        aliasVal['FITS.SBR.AIRMASS']=9.99999; aliasVal['FITS.SBR.ZD']=9.999; aliasVal['FITS.SBR.DOM-PRS']=9.99;
        aliasVal['FITS.VGW.OBSERVER']='OCS, SS, TEL'; aliasVal['FITS.VGW.PROP-ID']='o98003'; aliasVal['FITS.SBR.TELESCOP']='Subaru';
        aliasVal['FITS.SBR.TELFOCUS']='Cassegrain'; aliasVal['FITS.SBR.FOC-VAL']=7.5; 
        aliasVal['FITS.SBR.M2-POS1']=1.0; aliasVal['FITS.SBR.M2-POS2']=1.1; aliasVal['FITS.SBR.M2-ANG1']=1.2; aliasVal['FITS.SBR.M2-ANG2']=1.3;
        aliasVal['FITS.SBR.AG-PRBR']=140.0; aliasVal['FITS.SBR.AG-PRBT']=90.0;aliasVal['FITS.SBR.INSROT']=90.0;
        #aliasVal['FITS.SBR.AG-PRBX']=10.0; aliasVal['FITS.SBR.AG-PRBY']=20.0; aliasVal['FITS.SBR.SV-PRB']=100.0; 
        #aliasVal['FITS.SBR.IMGROT']=45.0; aliasVal['FITS.SBR.IMR-TYPE']='RED'; 
        aliasVal['FITS.SBR.ADC-TYPE']='NULL'; aliasVal['FITS.SBR.ADC']=999.999;
        aliasVal['FITS.VGW.OBS-ALOC']='Observation';  
        aliasVal['FITS.SBR.DET-TMPSH']=-40.0; 
        #aliasVal['FITS.SBR.DET-TMPSV']=-41.0;aliasVal['FITS.SBR.DET-TMPSH']=-42.0;
        #aliasVal['FITS.VGW.IROT_TELESCOPE']='LINK'; aliasVal['FITS.VGW.IMGROT_FLG']='08';  aliasVal['FITS.VGW.INSROTPA']=90.0;
                    
        self.assertFitskeyword(self.frameid, header, sec, usec, keyVal,  aliasVal, vals)


    def testShNsopGuiderKeyword(self):

        ###### SH NSOP #####
        usec=tv_usec=636996     # time sec
        sec=tv_sec=1156606274   # time milisec
        
        header="0006SH%%NSOP1x1%009701880151015100000560u%160101510151      "     # header
        aliasVal=self.aliasVal                            # status alias values
        keyVal=self.keyVal
        vals=self.keyVal                            # keyword values
        #print keyVal
        
        
        vals['CRPIX1']=415.0;vals['CRPIX2']=324.0; vals['CRVAL1']=33.574641667; vals['CRVAL2']=31.82512474; 
        vals['BIN-FCT1']=vals['BIN-FCT2']=1;vals['PRD-MIN1']=97;  vals['PRD-MIN2']=188 
        vals['PRD-RNG1']=151; vals['PRD-RNG2']=151
        vals['RA']='02:14:17.914'; vals['DEC']='+31:49:30.45'; vals['EQUINOX']=2000.0
        vals['RA2000']='02:14:17.914'; vals['DEC2000']='+31:49:30.45';
        vals['CDELT1']=vals['CDELT2']=vals['CD1_1']=vals['CD2_2']=0.000025252
        vals['ALTITUDE']=89.0; vals['AZIMUTH']=-90.0;
        vals['DATE-OBS']='2006-08-26'; vals['UT']='15:31:14.636'; vals['MJD']=53973.6466972;vals['HST']='05:31:14.636'; vals['LST']='03:28:17.619' 
        vals['EXPTIME']=0.56; 
        vals['AIRMASS']=9.99999; vals['ZD']=9.999; vals['DOM-PRS']=9.99
        vals['OBSERVER']='OCS, SS, TEL'; vals['PROP-ID']='o98003'; vals['TELESCOP']='Subaru'
        vals['TELFOCUS'] = vals['FOC-POS'] ='Nasmyth-Opt'
        vals['FOC-VAL'] = 7.5
        vals['M2-POS1']=1.0; vals['M2-POS2']=1.1; vals['M2-ANG1']=1.2; vals['M2-ANG2']=1.3
        vals['AG-PRB1']=140.0; vals['AG-PRB2']=90.0 ; 
        #vals['INSROT']=90.0
        vals['IMGROT']=45.0
        vals['FRAMEID'] = vals['EXP-ID']= self.frameid;  vals['OBS-ALOC'] = 'Observation'
        vals['INSTRUME']='SH';  vals['DATA-TYP']='OBJECT'; vals['DETECTOR']='SH'; vals['GAIN']=1.0; vals['DET-TMP']=-40.0;  vals['FILTER01']='SHFILTER'
        
        aliasVal['FITS.SBR.RA']='02:14:17.914'; aliasVal['FITS.SBR.DEC']='+31:49:30.45'; aliasVal['FITS.SBR.EQUINOX']=2000.0;
        aliasVal['FITS.SBR.ALTITUDE']=89.0; aliasVal['FITS.SBR.AZIMUTH']=-90.0; aliasVal['FITS.SBR.UT1-UTC']=0.0;  
        aliasVal['FITS.SBR.AIRMASS']=9.99999; aliasVal['FITS.SBR.ZD']=9.999; aliasVal['FITS.SBR.DOM-PRS']=9.99;
        aliasVal['FITS.VGW.OBSERVER']='OCS, SS, TEL'; aliasVal['FITS.VGW.PROP-ID']='o98003'; aliasVal['FITS.SBR.TELESCOP']='Subaru';
        aliasVal['FITS.SBR.TELFOCUS']='Nasmyth-Opt'; aliasVal['FITS.SBR.FOC-VAL']=7.5; 
        aliasVal['FITS.SBR.M2-POS1']=1.0; aliasVal['FITS.SBR.M2-POS2']=1.1; aliasVal['FITS.SBR.M2-ANG1']=1.2; aliasVal['FITS.SBR.M2-ANG2']=1.3;
        aliasVal['FITS.SBR.AG-PRBR']=140.0; aliasVal['FITS.SBR.AG-PRBT']=90.0;aliasVal['FITS.SBR.INSROT']=90.0;
        #aliasVal['FITS.SBR.AG-PRBX']=10.0; aliasVal['FITS.SBR.AG-PRBY']=20.0; aliasVal['FITS.SBR.SV-PRB']=100.0; 
        aliasVal['FITS.SBR.IMGROT']=45.0; aliasVal['FITS.SBR.IMR-TYPE']='NULL'; 
        aliasVal['FITS.SBR.ADC-TYPE']='NULL'; aliasVal['FITS.SBR.ADC']=999.999;
        aliasVal['FITS.VGW.OBS-ALOC']='Observation';  
        aliasVal['FITS.SBR.DET-TMPSH']=-40.0; 
        #aliasVal['FITS.SBR.DET-TMPSV']=-41.0;aliasVal['FITS.SBR.DET-TMPSH']=-42.0;
        #aliasVal['FITS.VGW.IROT_TELESCOPE']='LINK'; aliasVal['FITS.VGW.IMGROT_FLG']='08';  aliasVal['FITS.VGW.INSROTPA']=90.0;
                    
        self.assertFitskeyword(self.frameid, header, sec, usec, keyVal,  aliasVal, vals)



    def testShPfvsGuiderKeyword(self):

        ###### SH PFVS #####
        usec=tv_usec=636996     # time sec
        sec=tv_sec=1156606274   # time milisec
        
        header="0006SH%%PFVS1x1%009701880151015100000560u%160101510151      "     # header
        aliasVal=self.aliasVal                            # status alias values
        keyVal=self.keyVal
        vals=self.keyVal                            # keyword values
        #print keyVal
        
        
        vals['CRPIX1']=415.0;vals['CRPIX2']=324.0; vals['CRVAL1']=33.574641667; vals['CRVAL2']=31.82512474; 
        vals['BIN-FCT1']=vals['BIN-FCT2']=1;vals['PRD-MIN1']=97;  vals['PRD-MIN2']=188 
        vals['PRD-RNG1']=151; vals['PRD-RNG2']=151
        vals['RA']='02:14:17.914'; vals['DEC']='+31:49:30.45'; vals['EQUINOX']=2000.0
        vals['RA2000']='02:14:17.914'; vals['DEC2000']='+31:49:30.45';
        vals['CDELT1']=vals['CDELT2']=vals['CD1_1']=vals['CD2_2']=0.000056106
        vals['ALTITUDE']=89.0; vals['AZIMUTH']=-90.0;
        vals['DATE-OBS']='2006-08-26'; vals['UT']='15:31:14.636'; vals['MJD']=53973.6466972;vals['HST']='05:31:14.636'; vals['LST']='03:28:17.619' 
        vals['EXPTIME']=0.56; 
        vals['AIRMASS']=9.99999; vals['ZD']=9.999; vals['DOM-PRS']=9.99
        vals['OBSERVER']='OCS, SS, TEL'; vals['PROP-ID']='o98003'; vals['TELESCOP']='Subaru'
        vals['TELFOCUS'] = vals['FOC-POS'] ='Prime'
        vals['FOC-VAL'] = 7.5
        vals['M2-POS1']=1.0; vals['M2-POS2']=1.1; vals['M2-ANG1']=1.2; vals['M2-ANG2']=1.3
        vals['AG-PRB1']=140.0; vals['AG-PRB2']=90.0 ; 
        vals['INSROT']=90.0
        #vals['IMGROT']=45.0
        vals['FRAMEID'] = vals['EXP-ID']= self.frameid;  vals['OBS-ALOC'] = 'Observation'
        vals['INSTRUME']='SH';  vals['DATA-TYP']='OBJECT'; vals['DETECTOR']='SH'; vals['GAIN']=1.0; vals['DET-TMP']=-40.0;  vals['FILTER01']='SHFILTER'
        
        aliasVal['FITS.SBR.RA']='02:14:17.914'; aliasVal['FITS.SBR.DEC']='+31:49:30.45'; aliasVal['FITS.SBR.EQUINOX']=2000.0;
        aliasVal['FITS.SBR.ALTITUDE']=89.0; aliasVal['FITS.SBR.AZIMUTH']=-90.0; aliasVal['FITS.SBR.UT1-UTC']=0.0;  
        aliasVal['FITS.SBR.AIRMASS']=9.99999; aliasVal['FITS.SBR.ZD']=9.999; aliasVal['FITS.SBR.DOM-PRS']=9.99;
        aliasVal['FITS.VGW.OBSERVER']='OCS, SS, TEL'; aliasVal['FITS.VGW.PROP-ID']='o98003'; aliasVal['FITS.SBR.TELESCOP']='Subaru';
        aliasVal['FITS.SBR.TELFOCUS']='Prime'; aliasVal['FITS.SBR.FOC-VAL']=7.5; 
        aliasVal['FITS.SBR.M2-POS1']=1.0; aliasVal['FITS.SBR.M2-POS2']=1.1; aliasVal['FITS.SBR.M2-ANG1']=1.2; aliasVal['FITS.SBR.M2-ANG2']=1.3;
        aliasVal['FITS.SBR.AG-PRBX']=140.0; aliasVal['FITS.SBR.AG-PRBY']=90.0;aliasVal['FITS.SBR.INSROT']=90.0;
        #aliasVal['FITS.SBR.AG-PRBX']=10.0; aliasVal['FITS.SBR.AG-PRBY']=20.0; aliasVal['FITS.SBR.SV-PRB']=100.0; 
        aliasVal['FITS.SBR.IMGROT']=9999.999; aliasVal['FITS.SBR.IMR-TYPE']='NULL'; 
        aliasVal['FITS.SBR.ADC-TYPE']='NULL'; aliasVal['FITS.SBR.ADC']=999.999;
        aliasVal['FITS.VGW.OBS-ALOC']='Observation';  
        aliasVal['FITS.SBR.DET-TMPSH']=-40.0; 
        #aliasVal['FITS.SBR.DET-TMPSV']=-41.0;aliasVal['FITS.SBR.DET-TMPSH']=-42.0;
        #aliasVal['FITS.VGW.IROT_TELESCOPE']='LINK'; aliasVal['FITS.VGW.IMGROT_FLG']='08';  aliasVal['FITS.VGW.INSROTPA']=90.0;
                    
        self.assertFitskeyword(self.frameid, header, sec, usec, keyVal,  aliasVal, vals)



    def testShPfirGuiderKeyword(self):

        ###### SH CASS #####
        usec=tv_usec=636996     # time sec
        sec=tv_sec=1156606274   # time milisec
        
        header="0006SH%%PFIR1x1%009701880151015100000560u%160101510151      "     # header
        aliasVal=self.aliasVal                            # status alias values
        keyVal=self.keyVal
        vals=self.keyVal                            # keyword values
        #print keyVal
        
        
        vals['CRPIX1']=415.0;vals['CRPIX2']=324.0; vals['CRVAL1']=33.574641667; vals['CRVAL2']=31.82512474; 
        vals['BIN-FCT1']=vals['BIN-FCT2']=1;vals['PRD-MIN1']=97;  vals['PRD-MIN2']=188 
        vals['PRD-RNG1']=151; vals['PRD-RNG2']=151
        vals['RA']='02:14:17.914'; vals['DEC']='+31:49:30.45'; vals['EQUINOX']=2000.0
        vals['RA2000']='02:14:17.914'; vals['DEC2000']='+31:49:30.45';
        vals['CDELT1']=vals['CDELT2']=vals['CD1_1']=vals['CD2_2']=0.000056106
        vals['ALTITUDE']=89.0; vals['AZIMUTH']=-90.0;
        vals['DATE-OBS']='2006-08-26'; vals['UT']='15:31:14.636'; vals['MJD']=53973.6466972;vals['HST']='05:31:14.636'; vals['LST']='03:28:17.619' 
        vals['EXPTIME']=0.56; 
        vals['AIRMASS']=9.99999; vals['ZD']=9.999; vals['DOM-PRS']=9.99
        vals['OBSERVER']='OCS, SS, TEL'; vals['PROP-ID']='o98003'; vals['TELESCOP']='Subaru'
        vals['TELFOCUS'] = vals['FOC-POS'] ='Prime'
        vals['FOC-VAL'] = 7.5
        vals['M2-POS1']=1.0; vals['M2-POS2']=1.1; vals['M2-ANG1']=1.2; vals['M2-ANG2']=1.3
        vals['AG-PRB1']=140.0; vals['AG-PRB2']=90.0 ; 
        #vals['INSROT']=90.0
        #vals['IMGROT']=45.0
        vals['FRAMEID'] = vals['EXP-ID']= self.frameid;  vals['OBS-ALOC'] = 'Observation'
        vals['INSTRUME']='SH';  vals['DATA-TYP']='OBJECT'; vals['DETECTOR']='SH'; vals['GAIN']=1.0; vals['DET-TMP']=-40.0;  vals['FILTER01']='SHFILTER'
        
        aliasVal['FITS.SBR.RA']='02:14:17.914'; aliasVal['FITS.SBR.DEC']='+31:49:30.45'; aliasVal['FITS.SBR.EQUINOX']=2000.0;
        aliasVal['FITS.SBR.ALTITUDE']=89.0; aliasVal['FITS.SBR.AZIMUTH']=-90.0; aliasVal['FITS.SBR.UT1-UTC']=0.0;  
        aliasVal['FITS.SBR.AIRMASS']=9.99999; aliasVal['FITS.SBR.ZD']=9.999; aliasVal['FITS.SBR.DOM-PRS']=9.99;
        aliasVal['FITS.VGW.OBSERVER']='OCS, SS, TEL'; aliasVal['FITS.VGW.PROP-ID']='o98003'; aliasVal['FITS.SBR.TELESCOP']='Subaru';
        aliasVal['FITS.SBR.TELFOCUS']='Prime'; aliasVal['FITS.SBR.FOC-VAL']=7.5; 
        aliasVal['FITS.SBR.M2-POS1']=1.0; aliasVal['FITS.SBR.M2-POS2']=1.1; aliasVal['FITS.SBR.M2-ANG1']=1.2; aliasVal['FITS.SBR.M2-ANG2']=1.3;
        aliasVal['FITS.SBR.AG-PRBX']=140.0; aliasVal['FITS.SBR.AG-PRBY']=90.0;aliasVal['FITS.SBR.INSROT']=90.0;
        #aliasVal['FITS.SBR.AG-PRBX']=10.0; aliasVal['FITS.SBR.AG-PRBY']=20.0; aliasVal['FITS.SBR.SV-PRB']=100.0; 
        aliasVal['FITS.SBR.IMGROT']=9999.999; aliasVal['FITS.SBR.IMR-TYPE']='NULL'; 
        aliasVal['FITS.SBR.ADC-TYPE']='NULL'; aliasVal['FITS.SBR.ADC']=999.999;
        aliasVal['FITS.VGW.OBS-ALOC']='Observation';  
        aliasVal['FITS.SBR.DET-TMPSH']=-40.0; 
        #aliasVal['FITS.SBR.DET-TMPSV']=-41.0;aliasVal['FITS.SBR.DET-TMPSH']=-42.0;
        #aliasVal['FITS.VGW.IROT_TELESCOPE']='LINK'; aliasVal['FITS.VGW.IMGROT_FLG']='08';  aliasVal['FITS.VGW.INSROTPA']=90.0;
                    
        self.assertFitskeyword(self.frameid, header, sec, usec, keyVal,  aliasVal, vals)
      
        

    def assertFitskeyword(self, frameid, header, sec, usec, keyVal,  aliasVal, vals):
                                  
        keyVals=self.createfits.setGuiderFitsKeyword(frameid, header, sec, usec, keyVal,  aliasVal)
        
        for i in keyVals:
                       
            if NUM.match(str(vals[i])):
                self.assertAlmostEqual(vals[i], keyVals[i],6)
            else:
                self.assertEqual(vals[i], keyVals[i])
 


    def testPutGetFits(self):
        #self.env.removeTestDirs()  # just in case, remove dir
        #self.env.makeDirs()    
        #self.createfits=guiderfits.GuiderCreateFits(monitor=None, debug=None, usethread=True)
        
        #self.createfits.create_fits_start()
            
         
        guiderfits.CREATE_FITS.put((self.dirpath, self.frameid,self.dummy_image, self.header_info, self.sec, self.usec ))
        dir, id, image, headerinfo, sec, usec = guiderfits.CREATE_FITS.get_nowait()
        self.assertEquals( (self.dirpath, self.frameid, self.dummy_image._data, self.header_info, self.sec, self.usec), 
                            (dir, id, image._data, headerinfo, sec, usec))
        
 
    def testPutGetVlanCmd(self):
        
        guidersave.VLAN_SAVE_CMD.put_nowait( (self.dirpath, self.framelist) )
        self.assertEquals((self.dirpath, self.framelist), guidersave.VLAN_SAVE_CMD.get())
 
    def testPutGetSaveFits(self):
        
        for frame in self.framelist:
            guidersave.SAVE_FITS.put_nowait((self.dirpath, frame))
            self.assertEquals( (self.dirpath, frame), guidersave.SAVE_FITS.get() )
                                    
        
#    def tearDown(self):
#        self.env.removeTestDirs()

    

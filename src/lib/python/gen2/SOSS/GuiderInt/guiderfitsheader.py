#
# guiderfitsheader.py -- module for creating FITS headers for AG guide images
#
#[ Takeshi Inagaki (tinagaki@naoj.org) --
#]
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Sat Mar  2 22:05:06 HST 2013
#]
#
import math
import astro.wcs as wcs
import astro.fitsheader as fitsheader
import Bunch

###################################################################
# Tables used to interpret the Ag header codes
###################################################################

# AG -> AGFILTER
# SH -> SHFILTER
# SV (0.0/1.0/2.0/3.0) ->  NoFilter/Filter1/Filter2/NDFilter
guider_filter = { 'AG': "AGFILTER",
                  'SH': "SHFILTER",
                  0.0: "NoFilter",
                  1.0: "Filter1",
                  2.0: "Filter2",
                  3.0: "NDFilter",
                  }

# adu conversion factor (electron/ADU)    
guider_gain = { 'AG': 1.0, 'SV': 1.0, 'SH': 1.0 }

# foci full name
guider_foc_pos = { 'CASS': 'Cassegrain',
                   'NSOP': 'Nasmyth-Opt',
                   'NSIR': 'Nasmyth-IR',
                   'PFVS': 'Prime',
                   'PFIR': 'Prime',
                   'COUD': 'Coude',
                   }

# ccd center point (pixel)
guider_ccd = { 'AG': 256.0, 'SV': 256.0, 'SH': 512.0 }

# guider data kind
guider_data_kind = { '01': 'OBJECT',
                     '02': 'DARK',
                     '03': 'FLAT',
                     '04': 'SKY',
                     '05': 'BIAS',
                     }


def getGuiderDegPix(guider, foci, degpix):
    guider_deg_pix = { 'AG':{
                              'CASS':{'CDELT1': 0.000026044,  'CDELT2': 0.000026044},
                              'NSIR':{'CDELT1': 0.000023825,  'CDELT2': 0.000023823},
                              'NSOP':{'CDELT1': 0.000025252,  'CDELT2': 0.000025252},
                              'PFVS':{'CDELT1': 0.000026093,  'CDELT2': 0.000026093},
                              'PFIR':{'CDELT1': 0.000026093,  'CDELT2': 0.000026093},
                            },
                       'SV':{
                              'CASS':{'CDELT1': 0.000034722,  'CDELT2': 0.000034722},
                              'NSOP':{'CDELT1': 0.000034722,  'CDELT2': 0.000034722},
                            }, 
                       'SH':{
                              'CASS':{'CDELT1': 0.000026044,  'CDELT2': 0.000026044},
                              'NSIR':{'CDELT1': 0.000023825,  'CDELT2': 0.000023823},
                              'NSOP':{'CDELT1': 0.000025252,  'CDELT2': 0.000025252},
                              'PFVS':{'CDELT1': 0.000056106,  'CDELT2': 0.000056106},
                              'PFIR':{'CDELT1': 0.000056106,  'CDELT2': 0.000056106},
                            },
                     }  
    return guider_deg_pix[guider][foci][degpix]

# Sample FITS header from a VGW frame:
#
## SIMPLE  =                    T / Standard FITS format                           
## BITPIX  =                  -32 / # of bits storing pix values                   
## NAXIS   =                    2 / # of axes in frame                             
## NAXIS1  =                  100 / # of pixels/row                                
## NAXIS2  =                  100 / # of rows (also # of scan lines)               
## BSCALE  =                  1.0 / Real=fits-value*BSCALE*BZERO                   
## BZERO   =                  0.0 / Real=fits-value*BSCALE*BZERO                   
## BUNIT   = 'CCD COUNT IN ADU'   / Unit of original pixel values                  
## BLANK   =               -32767 / Value used for NULL pixels                     
## CRPIX1  =                256.0 / Reference pixel in X (pixel)                   
## CRPIX2  =                166.0 / Reference pixel in Y (pixel)                   
## CRVAL1  =         193.92189026 / Physical value of the reference pixel X        
## CRVAL2  =          12.56037235 / Physical value of the reference pixel Y        
## CTYPE1  = 'RA---TAN'           / Pixel coordinate system                        
## CTYPE2  = 'DEC--TAN'           / Pixel coordinate system                        
## CDELT1  =           0.00002609 / X Scale projected on detector (#/pix)          
## CDELT2  =           0.00002609 / Y Scale projected on detector (#/pix)          
## CUNIT1  = 'degree  '           / Units used in both CRVAL1 and CDELT1           
## CUNIT2  = 'degree  '           / Units used in both CRVAL2 and CDELT2           
## BIN-FCT1=                    1 / Binning factor of X axis (pixel)               
## BIN-FCT2=                    1 / Binning factor of Y axis (pixel)               
## PRD-MIN1=                    0 / Start X pos. of partialy read out (pix)        
## PRD-MIN2=                   90 / Start Y pos. of partialy read out (pix)        
## PRD-RNG1=                  100 / X Range of the partialy read out (pix)         
## PRD-RNG2=                  100 / Y Range of the partialy read out (pix)         
## RA      = '12:55:41.254'       / HH:MM:SS.SSS RA (J2000) pointing               
## DEC     = '+12:33:37.34'       / +/-HH:MM:SS.SSS DEC (J2000) pointing           
## EQUINOX =             2000.000 / Standard FK5 (years)                           
## RA2000  = '12:55:41.254'       / HH:MM:SS.SSS RA (J2000) pointing               
## DEC2000 = '+12:33:37.34'       / +/-HH:MM:SS.SSS DEC (J2000) pointing           
## RADECSYS= 'FK5     '           / The equatorial coordinate system               
## PC001001=           1.00000000 / Pixel Coordinate translation matrix            
## PC001002=           0.00000000 / Pixel Coordinate translation matrix            
## PC002001=           0.00000000 / Pixel Coordinate translation matrix            
## PC002002=           1.00000000 / Pixel Coordinate translation matrix            
## CD1_1   =           0.00002609 / Pixel Coordinate translation matrix            
## CD1_2   =           0.00000000 / Pixel Coordinate translation matrix            
## CD2_1   =           0.00000000 / Pixel Coordinate translation matrix            
## CD2_2   =           0.00002609 / Pixel Coordinate translation matrix            
## LONGPOLE=            180.00000 / The North Pole of standard system (deg)        
## WCS-ORIG= 'SUBARU Toolkit'     / Origin of the WCS value                        
## ALTITUDE=             73.12314 / Altitude of telescope pointing (degree)        
## AZIMUTH =            246.76396 / Azimuth of telescope pointing (degree)         
## TIMESYS = 'UTC     '           / Time System used in the header. UTC fix.       
## DATE-OBS= '2006-05-02'         / Observation start date (yyyy-mm-dd)            
## UT      = '09:40:43.107'       / HH:MM:SS.S typical UTC at exposure             
## MJD     =       53857.40327942 / Modified Julian Day at typical time            
## HST     = '23:40:43.107'       / HH:MM:SS.S typical HST at exposure             
## LST     = '13:59:28.317'       / HH:MM:SS.S typical LST at exposure             
## EXPTIME =                 0.97 / Total integration time of the frame (sec)      
## AIRMASS =                1.045 / Averaged Air Mass                              
## ZD      =             16.87758 / Zenith Distance at typical time                
## DOM-PRS =               618.00 / Atmospheric pressure in the Dome (hpa)         
## OBSERVER= '"Tomono, Usuda, Negishi, Iseki @ summit, (Fuse @ base 27:00-' / Name of obs
## PROP-ID = 'o99005  '           / Proposal ID                                    
## OBSERVAT= 'NAOJ    '           / Observatory                                    
## TELESCOP= 'Subaru  '           / Telescope/System which Inst. is attached       
## TELFOCUS= 'Prime   '           / Focus where a beam is reachable                
## FOC-POS = 'Prime   '           / Focus where the instrument is attached         
## FOC-VAL =                7.590 / Encoder value of the focus unit (mm)           
## M2-POS1 =           0.45043700 / X Position of the M2 (mm)                      
## M2-POS2 =          -1.21687000 / Y Position of the M2 (mm)                      
## M2-ANG1 =           0.00001000 / Theta X of the M2 (arcmin)                     
## M2-ANG2 =          -0.00002000 / Theta Y of the M2 (arcmin)                     
## AG-PRB1 =          31.58502500 / AG Probe position (r:mm, x:mm)                 
## AG-PRB2 =          19.99992200 / AG Probe position (Theta:degree, y:mm)         
## SV-PRB  =              999.999 / SV Probe position (mm)                         
## INSROT  =              152.336 / Instrument Rotator angle (deg)                 
## IMGROT  =             9999.999 / Image Rotator angle (deg)                      
## IMR-TYPE= 'NULL    '           / Identifire of the image rotator                
## ADC-TYPE= 'NULL    '           / ADC name/type if used                          
## ADC     =              999.999 / ADC name if used                               
## FRAMEID = 'VGWA00460924'       / Image sequential number                        
## EXP-ID  = 'VGWA00460924'       / ID of the exposure this data was taken         
## OBS-ALOC= 'Observation'        / Allocation mode for Instrument                 
## OBS-MOD = 'IMAGING '           / Observation Mode                               
## INSTRUME= 'AG      '           / Name of instrument                             
## OBJECT  = 'Focusing'           / Target Description                             
## DATA-TYP= 'OBJECT  '           / Type/Characteristics of this data              
## DETECTOR= 'AG      '           / Name of the detector/CCD                       
## GAIN    =                 1.00 / AD conversion factor (electron/ADU)            
## DET-TMP =           -40.000000 / Detector temperature (K)                       
## FILTER01= 'AGFILTER'           / Filter name/ID                                 
## EXTEND  =                    F / Presence of FITS Extention                     
## HISTORY Integral Time = 1. Calib Mode = OFF.                                    
## END                                                                          

# keywords have to be 8 characters long
# guider fits header template


class GuiderFitsParams(fitsheader.FitsHeaderParams):

    def get_agheader(self, name):
        # User is assumed to have passed in a parameter called agheader
        return self.params.agheader[name]
    
    def get_agheader_list(self, *args):
        return map(self.get_agheader, args)
    
    def get_agtime(self):
        # User is assumed to have passed in a parameter called agtime
        return self.params.agtime
    

class GuiderFitsHeaderMaker(fitsheader.FitsHeaderMaker):

    def __init__(self, logger):
        super(GuiderFitsHeaderMaker, self).__init__(logger)

        deriveList = [
            # Some constants
            dict(key='BSCALE', comment='Real=fits-value*BSCALE*BZERO',
                 derive=('@const', 1.0), index=6),
            dict(key='BZERO', comment='Real=fits-value*BSCALE*BZERO',
                 derive=('@const', 0.0), index=7),
            dict(key='BUNIT', comment='Unit of original pixel values',
                 derive=('@const', "CCD COUNT IN ADU"), index=8),
            ## dict(key='BLANK', comment='Value used for NULL pixels',
            ##      derive=('@const', -32767), index=9),
            dict(key='LONGPOLE', comment='The North Pole of standard system (deg)',
                 derive=('@const', 180.0), index=40),
            dict(key='RADECSYS', comment='The equatorial coordinate system',
                 derive=('@const', 'FK5'), index=30.1),
            dict(key='OBSERVAT', comment='Observatory',
                 derive=('@const', "NAOJ"), index=55.1),
            dict(key='WCS-ORIG', comment='Origin of the WCS value',
                 derive=('@const', "SUBARU Toolkit"), index=41),
            dict(key='TIMESYS', comment='Time System used in the header. UTC fix',
                 derive=('@const', "UTC"), index=44),
            dict(key='OBS-MOD', comment='Observation Mode',
                 derive=('@const', "IMAGING"), index=76),
            ## dict(key='HISTORY', comment='', 
            ##      derive=('@const', "Integral Time = 1. Calib Mode = OFF")),
            dict(key='CUNIT1', comment='Units used in both CRVAL1 and CDELT1',
                 derive=('@const', "degree"), index=18),
            dict(key='CUNIT2', comment='Units used in both CRVAL2 and CDELT2',
                 derive=('@const', "degree"), index=19),
            dict(key='CTYPE1', comment='Pixel coordinate system',
                 derive=('@const', "RA---TAN"), index=15.5),
            dict(key='CTYPE2', comment='Pixel coordinate system',
                 derive=('@const', "DEC--TAN"), index=15.6),

            # INSTRUME <- header[insName]
            dict(key='INSTRUME', comment='Name of instrument', index=77),

            # DETECTOR <- header[insName]
            dict(key='DETECTOR', comment='Name of the detector/CCD', index=80),

            # BIN-FCT1 <- header[binX]
            dict(key='BIN-FCT1', comment='Binning factor of X axis (pixel)',
                 derive=self.calc_BIN_FCT1, index=20),

            # BIN-FCT2 <- header[binY]
            dict(key='BIN-FCT2', comment='Binning factor of Y axis (pixel)',
                 derive=self.calc_BIN_FCT2, index=21),

            # PRD-MIN1 <- header[expRangeX]
            dict(key='PRD-MIN1', comment='Start X pos. of partially read out (pix)',
                 derive=self.calc_PRD_MIN1, index=22),

            # PRD-MIN2 <- header[expRangeY]
            dict(key='PRD-MIN2', comment='Start Y pos. of partially read out (pix)',
                 derive=self.calc_PRD_MIN2, index=23),

            # PRD-RNG1 <- header[numPixX]
            dict(key='PRD-RNG1', comment='X Range of the partially read out (pix)',
                 derive=self.calc_PRD_RNG1, index=24),

            # PRD-RNG2 <- header[numPixY]
            dict(key='PRD-RNG2', comment='Y Range of the partially read out (pix)',
                 derive=self.calc_PRD_RNG2, index=25), 

            # EXPTIME <- header[expTime]
            dict(key='EXPTIME', comment='Total integration time of the frame (sec)',
                 index=50),

            # DATA-TYP <- header[data]
            dict(key='DATA-TYP', comment='Type|Characteristics of this data',
                 derive=self.calc_DATA_TYP, index=79),

            # FOC-POS <- header[foci]
            dict(key='FOC-POS', comment='Encoder value of the focus unit (mm)',
                 derive=self.calc_FOC_POS, index=59),

            # CRPIX1 <- ccd - ( exp / bin ) header[insName] header[expRangeX] header[binX]
            dict(key='CRPIX1', comment='Reference pixel in X (pixel)',
                 index=10),

            # CRPIX2 <- ccd - ( exp / bin ) header[insName] header[expRangeY] header[binY]                   
            dict(key='CRPIX2', comment='Reference pixel in Y (pixel)',
                 index=11),

            # CDELT1 <- cdelt * bin 
            dict(key='CDELT1', comment='X Scale projected on detector (#/pix)',
                 index=16),
            
            # CDELT2 <- cdelt * bin
            dict(key='CDELT2', comment='Y Scale projected on detector (#/pix)',
                 index=17),

            # GAIN <- header[insName]
            dict(key='GAIN', comment='AD conversion factor (electron/ADU)',
                 index=81),

            # DATE-OBS <- observation time
            dict(key='DATE-OBS', comment='Observation start date (yyyy-mm-dd)',
                 derive=self.calc_DATE_OBS, index=45),

            dict(key='UT', comment='HH:MM:SS.S typical UTC at exposure',
                 index=46),

            dict(key='HST', comment='HH:MM:SS.S typical HST at exposure',
                 index=48),

            dict(key='MJD', comment='Modified Julian Day at typical time',
                 dep=['!FITS.SBR.UT1_UTC'], index=47),  

            dict(key='LST', comment='HH:MM:SS.S typical LST at exposure',
                 dep=['!FITS.SBR.UT1_UTC'], index=49), 

            # CRVAL1 <- FITS.SBR.RA  hms to deg
            dict(key='CRVAL1', comment='Physical value of the reference pixel X',
                 dep=['!FITS.SBR.RA'], index=12),

            # CRVAL2 <- FITS.SBR.DEC dms to deg
            dict(key='CRVAL2', comment='Physical value of the reference pixel Y',
                 dep=['!FITS.SBR.DEC'], index=13),     

            # RA <- FITS.SBR.RA     
            dict(key='RA', comment='HH:MM:SS.SSS RA (J2000) pointing',
                 dep=['!FITS.SBR.RA'], derive=('@status', 0), index=26),

            # DEC <- FITS.SBR.DEC
            dict(key='DEC', comment='+|-HH:MM:SS.SSS DEC (J2000) pointing',
                 dep=['!FITS.SBR.DEC'], derive=('@status', 0), index=27),

            # EQUINOX <- FITS.SBR.EQUINOX
            dict(key='EQUINOX', comment='Standard FK5 (years)',
                 dep=['!FITS.SBR.EQUINOX'], derive=self.calc_equinox,
                 index=28),

            # RA2000 <- CRVAL1/FITS.SBR.EQUINOX   calc ra with equinox 2000
            # DEC2000 <- CRVAL2/FITS.SBR.EQUINOX  calc dec with equinox 2000
            dict(key='RA2000', comment='HH:MM:SS.SSS RA (J2000) pointing',
                 dep=['!FITS.SBR.EQUINOX', 'CRVAL1', 'CRVAL2'],
                 derive=self.calc_eq2000, index=29),

            dict(key='DEC2000', comment='+|-HH:MM:SS.SSS DEC (J2000) pointing',
                 dep=['!FITS.SBR.EQUINOX', 'CRVAL1', 'CRVAL2'],
                 derive=self.calc_eq2000, index=30),

            #  PC <- (FITS.VGW.IROT_TELESCOPE/FITS.VGW.IMGROT_FLG/FITS.VGW.INSROTPA/FITS.SBR.ALTITUDE/FITS.SBR.AZIMUTH/FITS.SBR.IMGROT)  
            #  only if guider is SV, PCs will be calculated. otherwise, default values will be assigned
            dict(key='PC001001', comment='Pixel Coordinate translation matrix',
                 dep=['!FITS.VGW.IROT_TELESCOPE', '!FITS.VGW.IMGROT_FLG',
                      '!FITS.VGW.INSROTPA', '!FITS.SBR.ALTITUDE', '!FITS.SBR.AZIMUTH',
                      '!FITS.SBR.IMGROT'], derive=self.calc_pc, index=32),

            dict(key='PC001002', comment='Pixel Coordinate translation matrix',
                 dep=['!FITS.VGW.IROT_TELESCOPE', '!FITS.VGW.IMGROT_FLG',
                      '!FITS.VGW.INSROTPA', '!FITS.SBR.ALTITUDE', '!FITS.SBR.AZIMUTH',
                      '!FITS.SBR.IMGROT'], derive=self.calc_pc, index=33),

            dict(key='PC002001', comment='Pixel Coordinate translation matrix',
                 dep=['!FITS.VGW.IROT_TELESCOPE', '!FITS.VGW.IMGROT_FLG',
                      '!FITS.VGW.INSROTPA', '!FITS.SBR.ALTITUDE', '!FITS.SBR.AZIMUTH',
                      '!FITS.SBR.IMGROT'], derive=self.calc_pc, index=34),

            dict(key='PC002002', comment='Pixel Coordinate translation matrix',
                 dep=['!FITS.VGW.IROT_TELESCOPE', '!FITS.VGW.IMGROT_FLG',
                      '!FITS.VGW.INSROTPA', '!FITS.SBR.ALTITUDE', '!FITS.SBR.AZIMUTH',
                      '!FITS.SBR.IMGROT'], derive=self.calc_pc, index=35),

            # CD1_1 <- PC001001 * CDELT1   
            dict(key='CD1_1', comment='Pixel Coordinate translation matrix',
                 dep=['PC001001', 'CDELT1'], index=36),

            # CD1_2 <- PC001002 * CDELT1 
            dict(key='CD1_2', comment='Pixel Coordinate translation matrix',
                 dep=['PC001002', 'CDELT1'], index=37),

            # CD2_1 <- PC002001 * CDELT2
            dict(key='CD2_1', comment='Pixel Coordinate translation matrix',
                 dep=['PC002001', 'CDELT2'], index=38),

            # CD2_2 <- PC001002 * CDELT2
            dict(key='CD2_2', comment='Pixel Coordinate translation matrix',
                 dep=['PC002002', 'CDELT2'], index=39),       

            # ALTITUDE <- FITS.SBR.ALTITUDE
            dict(key='ALTITUDE', comment='Altitude of telescope pointing (degree)',
                 dep=['!FITS.SBR.ALTITUDE'], derive=('@status', 0),
                 index=42),

            # AZIMUTH <- FITS.SBR.AZIMUTH
            dict(key='AZIMUTH', comment='Azimuth of telescope pointing (degree)',
                 dep=['!FITS.SBR.AZIMUTH'], derive=('@status', 0), index=43),

            # AIRMASS <- FITS.SBR.AIRMASS
            dict(key='AIRMASS', comment='Averaged Air Mass',
                 dep=['!FITS.SBR.AIRMASS'], derive=('@status', 0), index=51),

            # ZD <- FITS.SBR.ZD
            dict(key='ZD', comment='Zenith Distance at typical time',
                 dep=['!FITS.SBR.ZD'], derive=('@status', 0), index=52),

            # DOM-PRS <- FITS.SBR.DOM-PRS
            dict(key='DOM-PRS', comment='Atmospheric pressure in the Dome (hpa)',
                 dep=['!FITS.SBR.DOM-PRS'], derive=('@status', 0), index=53),

            # OBSERVER <- FITS.VGW.OBSERVER
            dict(key='OBSERVER', comment='Name of observers',
                 dep=['!FITS.VGW.OBSERVER'], derive=('@status', 0), index=54),

            # PROP-ID <- FITS.VGW.PROP-ID
            dict(key='PROP-ID', comment='Proposal ID',
                 dep=['!FITS.VGW.PROP-ID'], derive=('@status', 0), index=55),

            # OBJECT <- FITS.VGW.OBJECT
            dict(key='OBJECT', comment='Target Description',
                 dep=['!FITS.VGW.OBJECT'], derive=('@status', 0), index=78),

            # FRAMEID <- FRAMEID
            dict(key='FRAMEID', comment='Image sequential number', index=73),  

            # EXP-ID <- FRAMEID
            dict(key='EXP-ID', comment='ID of the exposure this data was taken',
                 derive=self.calc_EXP_ID, index=74),  

            # TELESCOP <- FITS.SBR.TELESCOP 
            dict(key='TELESCOP', comment='Telescope/System which Inst. is attached',
                 dep=['!FITS.SBR.TELESCOP'], derive=('@status', 0), index=57),

            # TELFOCUS <- FITS.SBR.TELFOCUS
            dict(key='TELFOCUS', comment='Focus where a beam is reachable',
                 dep=['!FITS.SBR.TELFOCUS'], derive=('@status', 0), index=58),

            # FOC-VAL <- FITS.SBR.FOC-VAL
            dict(key='FOC-VAL', comment='Encoder value of the focus unit (mm)',
                 dep=['!FITS.SBR.FOC-VAL'], derive=('@status', 0), index=60),

            # M2-POS1 <- FITS.SBR.M2-POS1
            dict(key='M2-POS1', comment='X Position of the M2 (mm)',
                 dep=['!FITS.SBR.M2-POS1'], derive=('@status', 0), index=61),

            # M2-POS2 <- FITS.SBR.M2-POS2
            dict(key='M2-POS2', comment='Y Position of the M2 (mm)',
                 dep=['!FITS.SBR.M2-POS2'], derive=('@status', 0), index=62),

            # M2-ANG1 <- FITS.SBR.M2-ANG1
            dict(key='M2-ANG1', comment='Theta X of the M2 (arcmin)',
                 dep=['!FITS.SBR.M2-ANG1'], derive=('@status', 0), index=63),

            # M2-ANG2 <- FITS.SBR.M2-ANG2
            dict(key='M2-ANG2', comment='Theta Y of the M2 (arcmin)',
                 dep=['!FITS.SBR.M2-ANG2'], derive=('@status', 0), index=64),

            # AG-PRB1 <- FITS.SBR.AG-PRBR  if foci is CASS|NSOP|NSIR.
            # AG-PRB1 <- FITS.SBR.AG-PRBX  if foci is PFVS|PFIR.
            # AG-PRB1 <- None otherwise.   
            dict(key='AG-PRB1', comment='AG Probe position (x:mm)',
                 dep=['!FITS.SBR.AG-PRBR', '!FITS.SBR.AG-PRBX'], index=65,
                 derive=self._mk_choice_foci('AG-PRB1',
                                             [(('CASS', 'NSOP', 'NSIR'),
                                               'FITS.SBR.AG-PRBR'),
                                              (('PFVS', 'PFIR'),
                                               'FITS.SBR.AG-PRBX')]) ),

             # AG-PRB2 <- FITS.SBR.AG-PRBT  if foci is CASS|NSOP|NSIR.
             # AG-PRB2 <- FITS.SBR.AG-PRBY  if foci is PFVS|PFIR.  
             # AG-PRB1 <- None otherwise.
            dict(key='AG-PRB2', comment='AG Probe position (y:mm)',
                 dep=['!FITS.SBR.AG-PRBT', '!FITS.SBR.AG-PRBY'], index=66,
                 derive=self._mk_choice_foci('AG-PRB2',
                                             [(('CASS', 'NSOP', 'NSIR'),
                                               'FITS.SBR.AG-PRBT'),
                                              (('PFVS', 'PFIR'),
                                               'FITS.SBR.AG-PRBY')]) ),

             # SV-PRB <- FITS.SBR.SV-PRB  if guider is SV
             # SV-PRB <- None  if guider is AG|SH
             dict(key='SV-PRB', comment='SV Probe position (mm)',
                  dep=['!FITS.SBR.SV-PRB'], index=67,
                  derive=self._mk_choice_guider('SV-PRB',
                                                [(('SV',),
                                                  'FITS.SBR.SV-PRB')]) ),

             # INSROT <- FITS.SBR.INSROT  if foci is CASS|PVFS
             # INSROT <- None   otherwise.             
            dict(key='INSROT', comment='Instrument Rotator angle (deg)',
                 dep=['!FITS.SBR.INSROT'], index=68,
                 derive=self._mk_choice_foci('INSROT', 
                                             [(('CASS', 'PFVS'),
                                               'FITS.SBR.INSROT')]) ),

             # IMGROT <- FITS.SBR.IMGROT  if foci is NSIR|NSOP
             # IMGROT <- None   otherwise.             
            dict(key='IMGROT', comment='Image Rotator angle (deg)',
                 dep=['!FITS.SBR.IMGROT'], index=69,
                 derive=self._mk_choice_foci('IMGROT',
                                             [(('NSIR', 'NSOP'),
                                               'FITS.SBR.IMGROT')]) ),

            # IMR-TYPE <- FITS.SBR.IMR-TYPE if foci is NSIR|NSOP
            # IMR-TYPE <- None otherwise.
            dict(key='IMR-TYPE', comment='Identifire of the image rotator',
                 dep=['!FITS.SBR.IMR-TYPE'], index=70,
                 derive=self._mk_choice_foci('IMR-TYPE',
                                             [(('NSIR', 'NSOP'),
                                               'FITS.SBR.IMR-TYPE')]) ),

            # ADC-TYPE  <- FITS.SBR.ADC  if foci is CASS|NSOP
            # ADC-TYPE  <- None  otherwise.
            dict(key='ADC-TYPE', comment='ADC name/type if used',
                 dep=['!FITS.SBR.ADC-TYPE'], index=71,
                 derive=self._mk_choice_foci('ADC-TYPE',
                                             [(('CASS', 'NSOP'),
                                               'FITS.SBR.ADC-TYPE')]) ),

            # ADC <- FITS.SBR.ADC  if foci is CASS|NSOP
            # ADC <- None otherwise.
            dict(key='ADC', comment='ADC name if used',
                 dep=['!FITS.SBR.ADC'], index=72,
                 derive=self._mk_choice_foci('ADC',
                                             [(('CASS', 'NSOP'),
                                               'FITS.SBR.ADC')]) ),

            # OBS-ALOC <- FITS.VGW.OBS-ALOC
            dict(key='OBS-ALOC', comment='Allocation mode for Instrument',
                 dep=['!FITS.VGW.OBS-ALOC'], index=75,
                 derive=('@status', 0)),

            # DET-TMP <- FITS.SBR.DET-TMPAG if guider is AG
            # DET-TMP <- FITS.SBR.DET-TMPSV if guider is SV
            # DET-TMP <- FITS.SBR.DET-TMPSH if guider is SH 
            dict(key='DET-TMP', comment='Detector temperature (K)',
                 dep=['!FITS.SBR.DET-TMPAG', '!FITS.SBR.DET-TMPSV',
                      '!FITS.SBR.DET-TMPSH'], index=82,
                 derive=self._mk_choice_guider('DET-TMP',
                                               [(('AG',), 'FITS.SBR.DET-TMPAG'),
                                                (('SV',), 'FITS.SBR.DET-TMPSV'),
                                                (('SH',), 'FITS.SBR.DET-TMPSH')]) ),

            #  FILTER01 <- AGFILTER if guider is AG
            #  FILTER01 <- SHGFILTER if guider is SH
            #  FILTER01 <- None if guider is SV and FITS.VGW.FILTER01 is 0.0
            #  FILTER01 <- FILTER1 if guider is SV and FITS.VGW.FILTER01 is 1.0
            #  FILTER01 <- FILTER1 if guider is SV and FITS.VGW.FILTER01 is 2.0
            #  FILTER01 <- FILTER1 if guider is SV and FITS.VGW.FILTER01 is 3.0
            dict(key='FILTER01', comment='Filter name/ID',
                 dep=['!FITS.VGW.FILTER01'], index=83),  

            ]
        self.load(deriveList)

    def _mk_choice_foci(self, keyword, choices):
        def anon(p):
            foci = p.get_agheader('foci')
            for items, alias in choices:
                if foci in items:
                    val = p.get_status(alias)
                    p.update_keywords({ keyword: val })
                    return

            p.update_keywords({ keyword: 'UNKNOWN' })
        return anon

    def _mk_choice_guider(self, keyword, choices):
        def anon(p):
            guider = p.get_agheader('insName')
            for items, alias in choices:
                if guider in items:
                    val = p.get_status(alias)
                    p.update_keywords({ keyword: val })
                    return

            p.update_keywords({ keyword: 'UNKNOWN' })
        return anon

    # CALCULATED FROM AG HEADER
    
    def calc_INSTRUME(self, p):
        p.set_keywords(INSTRUME=p.get_agheader('insName'))

    def calc_DETECTOR(self, p):
        p.set_keywords(DETECTOR=p.get_agheader('insName'))

    def calc_BIN_FCT1(self, p):
        p.update_keywords({ 'BIN-FCT1': p.get_agheader('binX') })

    def calc_BIN_FCT2(self, p):
        p.update_keywords({ 'BIN-FCT2': p.get_agheader('binY') })

    def calc_PRD_MIN1(self, p):
        p.update_keywords({ 'PRD-MIN1': p.get_agheader('expRangeX') })

    def calc_PRD_MIN2(self, p):
        p.update_keywords({ 'PRD-MIN2': p.get_agheader('expRangeY') })

    def calc_PRD_RNG1(self, p):
        p.update_keywords({ 'PRD-RNG1': p.get_agheader('numPixX') })

    def calc_PRD_RNG2(self, p):
        p.update_keywords({ 'PRD-RNG2': p.get_agheader('numPixY') })

    def calc_EXPTIME(self, p):
        expTime = p.get_agheader('expTime')
        p.set_keywords(EXPTIME=wcs.calcExpTime(expTime))

    def calc_DATA_TYP(self, p):
        datakind = p.get_agheader('dataKind')
        kind = guider_data_kind.get(datakind)
        p.update_keywords({ 'DATA-TYP': kind })

    def calc_FOC_POS(self, p):
        foci = p.get_agheader('foci')
        pos = guider_foc_pos.get(foci)
        p.update_keywords({ 'FOC-POS': pos })

    # WORLD COORDINATES
    
    def calc_CRPIX1(self, p):
        insName, rangeX, binX = p.get_agheader_list('insName',
                                                       'expRangeX', 'binX')
        crpix1 = wcs.calcCRPIX(guider_ccd.get(insName), rangeX, binX)
        p.set_keywords(CRPIX1=crpix1)

    def calc_CRPIX2(self, p):
        insName, rangeY, binY = p.get_agheader_list('insName',
                                                       'expRangeY', 'binY')
        crpix2 = wcs.calcCRPIX(guider_ccd.get(insName), rangeY, binY)
        p.set_keywords(CRPIX2=crpix2)

    def calc_CDELT1(self, p):
        insName, foci, binX = p.get_agheader_list('insName', 'foci', 'binX')
        deg_pix_x = getGuiderDegPix(insName, foci, 'CDELT1')
        cdelt1 = wcs.calcCDELT(deg_pix_x, binX)
        p.set_keywords(CDELT1=cdelt1)

    def calc_CDELT2(self, p):
        insName, foci, binY = p.get_agheader_list('insName', 'foci', 'binY')
        deg_pix_y = getGuiderDegPix(insName, foci, 'CDELT2')
        cdelt2 = wcs.calcCDELT(deg_pix_y, binY)
        p.set_keywords(CDELT2=cdelt2)

    def calc_CRVAL1(self, p):
        ra = p.get_status('FITS.SBR.RA')
        p.set_keywords(CRVAL1=wcs.hmsToDeg(ra))
        
    def calc_CRVAL2(self, p):
        dec = p.get_status('FITS.SBR.DEC')
        p.set_keywords(CRVAL2=wcs.dmsToDeg(dec))

    def calc_CD1_1(self, p):
        pc001001, cdelt1 = p.get_keywords_list('PC001001', 'CDELT1')
        val = wcs.calcCD(pc001001, cdelt1)
        p.set_keywords(CD1_1=val)

    def calc_CD1_2(self, p):
        pc001002, cdelt1 = p.get_keywords_list('PC001002', 'CDELT1')
        val = wcs.calcCD(pc001002, cdelt1)
        p.set_keywords(CD1_2=val)

    def calc_CD2_1(self, p):
        pc002001, cdelt2 = p.get_keywords_list('PC002001', 'CDELT2')
        val = wcs.calcCD(pc002001, cdelt2)
        p.set_keywords(CD2_1=val)

    def calc_CD2_2(self, p):
        pc002002, cdelt2 = p.get_keywords_list('PC002002', 'CDELT2')
        val = wcs.calcCD(pc002002, cdelt2)
        p.set_keywords(CD2_2=val)

    def calc_pc(self, p):
        insName, foci = p.get_agheader_list('insName', 'foci')

        args = p.get_status_list(
            'FITS.VGW.IROT_TELESCOPE', 'FITS.VGW.IMGROT_FLG', 
            'FITS.VGW.INSROTPA', 'FITS.SBR.ALTITUDE',
            'FITS.SBR.AZIMUTH', 'FITS.SBR.IMGROT')

        if (insName == 'SV') and (foci == 'NSOP'):
        ## these WCS vals only seem to be calculated for SV, for some reason
            pc1, pc2, pc3, pc4 = wcs.calcPC(*args)

            p.set_keywords(PC001001=pc1, PC001002=pc2, PC002001=pc3, PC002002=pc4)
        else:
            pa_rad = math.radians(float(args[2]))
            cos_pa = math.cos(pa_rad)
            sin_pa = math.sin(pa_rad)

            # adjust according to the telescope foci (prime, cassegrain, etc.)
            if foci == 'CASS':
                p.set_keywords(PC001001=-cos_pa, PC001002=-sin_pa,
                               PC002001=-sin_pa, PC002002=cos_pa)
            # elif foci == 'NSIR':
            #     p.set_keywords(PC001001=-cos_pa, PC001002=-sin_pa,
            #                    PC002001=-sin_pa, PC002002=cos_pa)
            # elif foci in ('PFVS', 'PFIR'):
            #     p.set_keywords(PC001001=-cos_pa, PC001002=-sin_pa,
            #                    PC002001=-sin_pa, PC002002=cos_pa)
            else:
                p.set_keywords(PC001001=1.0, PC001002=0.0,
                               PC002001=0.0, PC002002=1.0)

    # POINTING
    
    def calc_GAIN(self, p):
        insName = p.get_agheader('insName')
        gain = guider_gain.get(insName)
        p.set_keywords(GAIN=gain)
    
    def calc_eq2000(self, p):
        crval1, crval2 = p.get_keywords_list('CRVAL1', 'CRVAL2')
        eqx = float(p.get_status('FITS.SBR.EQUINOX'))
        ra, dec = wcs.eq2000(crval1, crval2, eqx)
        p.set_keywords(RA2000=ra, DEC2000=dec)

    def calc_equinox(self, p):
        eqx = float(p.get_status('FITS.SBR.EQUINOX'))
        p.set_keywords(EQUINOX=eqx)

    # TIMES
    
    def calc_DATE_OBS(self, p):
         agtime = p.get_agtime()
         date_s = wcs.calcObsDate(agtime, format='%04d-%02d-%02d')
         p.update_keywords({ 'DATE-OBS': date_s })

    def calc_UT(self, p):
         agtime = p.get_agtime()
         date_s = wcs.calcUT(agtime)
         p.set_keywords(UT=date_s)

    def calc_HST(self, p):
         agtime = p.get_agtime()
         date_s = wcs.calcHST(agtime)
         p.set_keywords(HST=date_s)

    def calc_MJD(self, p):
         agtime = p.get_agtime()
         ut1_utc = p.get_status('FITS.SBR.UT1_UTC')
         date_s = wcs.calcMJD(agtime, ut1_utc)
         p.set_keywords(MJD=date_s)

    def calc_LST(self, p):
         agtime = p.get_agtime()
         ut1_utc = p.get_status('FITS.SBR.UT1_UTC')
         date_s = wcs.calcLST(agtime, ut1_utc)
         p.set_keywords(LST=date_s)

    # OTHER

    #  FILTER01 <- AGFILTER if guider is AG
    #  FILTER01 <- SHGFILTER if guider is SH
    #  FILTER01 <- None if guider is SV and FITS.VGW.FILTER01 is 0.0
    #  FILTER01 <- FILTER1 if guider is SV and FITS.VGW.FILTER01 is 1.0
    #  FILTER01 <- FILTER1 if guider is SV and FITS.VGW.FILTER01 is 2.0
    #  FILTER01 <- FILTER1 if guider is SV and FITS.VGW.FILTER01 is 3.0
    def calc_FILTER01(self, p):
        guider = p.get_agheader('insName')
        if guider in ('AG', 'SH'):
            val = guider_filter.get(guider)
            p.set_keywords(FILTER01=val)

        elif guider in ('SV',):
            filt = p.get_status('FITS.VGW.FILTER01')
            val = guider_filter.get(filt)
            p.set_keywords(FILTER01=val)

        else:
            p.set_keywords(FILTER01='None')
            
    # these are expected to be set already
    def calc_FRAMEID(self, p):
        raise Exception("No FRAMEID set!")
    
    def calc_EXP_ID(self, p):
        raise Exception("No EXP-ID set!")
    
#END

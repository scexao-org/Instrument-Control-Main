#!/usr/bin/env python
#
# Derive.py -- Derived Status Computation Module for OCS Gen2
#
# Bruce Bon (Bruce.Bon@SubaruTelescope.org)  last edit: 2007-09-16
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Jun  8 14:47:46 HST 2012
#]
#
"""
This module contains a class for deriving various status
alias values from the primitive values provided by TCS, instruments
and internal OCS values.  One of the public functions, deriveStatus,
is intended to be called from the status.py store function, which
receives status values as they come into STATint; deriveStatus, if
called in this way, will be called many times per second, and 
performance may be an issue. 

For status values that are derived from TSC status, most of the derivations
herein are taken from the SOSS derivations found in:
    product/OSSL/OSSL_StatL.d/OSSL_StatLexec.c
    product/OSSL/OSSL_StatL.d/OSSL_StatLexec_calc.c
    product/OSSL/OSSL_StatS.d/OSSL_StatSexec.c
    product/OSSL/OSSL_StatU.d/OSSL_StatUexec.c

The following FITS-related status alias values are constants, so are 
not computed herein:

        FITS.SBR.TELESCOP
        FITS.SBR.TRANSP
        FITS.SBR.WEATHER

The following status aliases are assigned by user interface processes, so are 
not computed herein:

        FITS.<ins>.DATASET   (not used)
        FITS.<ins>.STATUS    (not used)
        FITS.<ins>.FOC-POS   (?)  (Prime, Cassegrain, Nasmyth IR )
        FITS.<ins>.FOC_POS   (?)
        FITS.<ins>.OBSERVER  (SM)
        FITS.<ins>.OBS-ALOC  (SM)
        FITS.<ins>.OBS_ALOC  (SM)
        FITS.<ins>.OBS-MOD   (skTask)
        FITS.<ins>.OBS_MOD   (skTask)
        FITS.<ins>.OBJECT    (skTask)
        FITS.<ins>.PROP-ID   (SM)
        FITS.<ins>.PROP_ID   (SM)
        FITS.<ins>.FRAMEID   (FS)
        FITS.<ins>.FRAMEIDQ  (FS)
        FITS.SBR.MAINOBCP    (SM)
        FITS.SBR.ALLOBCP     (SM)

"""

# IMPLEMENTATION NOTES:
#   - After discussion with Eric, I am computing derived values as
#     trimmed strings.  E.g. for floats, I will not specify field
#     widths.  It will be up to the INSint module to expand these as
#     needed for instrument interfaces.
#   - Algorithms for derivations are taken from OSSL_StatUexec.c, with
#     some modification, such as assigning trimmed strings.
#   - A commonly used function in OSSL_StatUexec.c is getStatusString, which
#     given a status alias name, returns the same value as OSSC_screenPrint or,
#     if there is a failure, a pointer to NODATA_STR ("").
#   - A commonly used function in OSSL_StatUexec.c is getStatusBitString:
#       getStatusBitString(char *status, char **pattern, char **string)
#          status     alias name for a char string representing bit-mapped data
#          pattern    array of strings to match with status value
#          string     array of strings providing return value
#       If value string matches exactly one of the strings in pattern,
#          returns string[i] where i is the index of the matching pattern string
#       Else  return ""
#   - Another commonly used function in OSSL_StatUexec.c is adjustStatusData:
#       adjustStatusData(char *string, char *format, char *status)
#       If  status == NODATA_STR (i.e. ''), then copy '' into string;
#       Else  sprintf(string, format, atof(status))
#       Thus adjustStatusData is used mainly to convert a string status value 
#       into a float, before formatting the float value according to format.

import math
import time
import re
import array

import astro.radec as radec
import astro.wcs as wcs
import Bunch
import common
import logging
from common import STATNONE, STATERROR

class statusDerivationError(common.statusError):
    pass
class DeriveError(statusDerivationError):
    pass


class statusDeriver(object):
    
    def __init__(self, statObj, logger):
        self.statObj = statObj
        self.logger = logger

        # Process derived aliases map
        #   <derived alias>: (<list of source aliases>, <derivation function>)
        #   ...
        self.deriveMap = {
            'FITS.SBR.ADC'     : (['TSCL.ADCPOS_PF','TSCL.ADCPos','TSCV.FOCUSINFO','TSCV.FOCUSINFO2'], 
                                  (lambda valDict: _FitsSbrPn(
                        valDict['TSCL.ADCPOS_PF'], 
                        valDict['TSCL.ADCPos'], valDict))),
            'FITS.SBR.AG-PRBR' : _ident('TSCL.AGPRBR'),
            'FITS.SBR.AG-PRBT' : _ident('TSCL.AGPRBT'),
            'FITS.SBR.AG-PRBX' : _ident('TSCL.AGPF_X'),
            'FITS.SBR.AG-PRBY' : _ident('TSCL.AGPF_Y'),
            'FITS.SBR.AG-PRBZ' : _ident('TSCL.AGPF_Z'),
            'FITS.SBR.ALTITUDE': _ident('TSCS.EL'),
            'FITS.SBR.AIRMASS' : (['TSCS.EL'], _FitsSbrAirmass),
            'FITS.SBR.ADC-TYPE': (['TSCV.ADCInOut','TSCV.FOCUSINFO','TSCV.FOCUSINFO2'],
                                  _FitsSbrAdc_type),
            'FITS.SBR.AUTOGUID': (['TSCV.AutoGuideOff','TSCV.AutoGuideOn',
                                   'TSCV.SVAutoGuideOn'], _FitsSbrAutoguid),
            'FITS.SBR.AZIMUTH' : (['TSCS.AZ'], _FitsSbrAzimuth),
            'FITS.SBR.CHP-PA'  : _ident('TSCL.TT_POS'),
            'FITS.SBR.CHP-WID' : _ident('TSCL.Amp'),
            'FITS.SBR.DEC'     : (['TSCS.DELTA'], _FitsSbrDec),
            'FITS.SBR.DEC_CMD'     : (['TSCS.DELTA_C'], _FitsSbrDec_Cmd),
            'FITS.SBR.DET-TMPAG': _ident('TSCL.DETTMPAG'),
            'FITS.SBR.DET-TMPSV': _ident('TSCL.DETTMPSV'),
            'FITS.SBR.DET-TMPSH': _ident('TSCL.DETTMPSH'),
            # !! This is not in StatusAlias.def !!
            #'FITS.SBR.FILTER01' : (['TSCV.FILTER01'], 
            #                  (lambda valDict: _FmtP6f(valDict['TSCV.FILTER01']))),
            'FITS.SBR.DOM-WND' : _ident('TSCL.WINDS_I'),
            'FITS.SBR.OUT-WND' : _ident('TSCL.WINDS_O'),
            'FITS.SBR.DOM-TMP' : (['TSCL.TEMP_I'], _FitsSbrDom_tmp),
            'FITS.SBR.OUT-TMP' : (['TSCL.TEMP_O'], _FitsSbrOut_tmp),
            'FITS.SBR.DOM-HUM' : _ident('TSCL.HUMI_I'),
            'FITS.SBR.OUT-HUM' : _ident('TSCL.HUMI_O'),
            'FITS.SBR.DOM-PRS' : _ident('TSCL.ATOM'),
            'FITS.SBR.OUT-PRS' : _ident('TSCL.ATOM'),
            'FITS.SBR.EQUINOX' : (['TSCS.EQUINOX'], _StatsFitsSbrEquinox),
            'FITS.SBR.EPOCH'     : (['TSCS.ALPHA'], _FitsSbrEpoch),
            'FITS.SBR.HST'     : (['FITS.SBR.EPOCH'], _FitsSbrHST),
            'FITS.SBR.UT'      : (['FITS.SBR.EPOCH'], _FitsSbrUT),
            'FITS.SBR.LST'     : (['TSCS.ALPHA', 'FITS.SBR.EPOCH',
                                   'FITS.SBR.UT1-UTC'],
                                  _FitsSbrLST),
            'FITS.SBR.HA'      : (['STATS.RA', 'FITS.SBR.EPOCH',
                                   'FITS.SBR.UT1-UTC'],
                                  _FitsSbrHA),
            'FITS.SBR.FOC-VAL' : _ident('TSCL.Z'),
            'FITS.SBR.FOC_VAL' : _ident('TSCL.Z'),
            'FITS.SBR.IMGROT'  : _ident('TSCS.ImgRotPos'),
            'FITS.SBR.IMR-TYPE': (['TSCV.ImgRotType','TSCV.ImgRotType_NS_IR'],
                                  _FitsSbrImr_type),
            'FITS.SBR.INSROT'  : (['TSCS.INSROTPOS_PF','TSCS.InsRotPos','TSCV.FOCUSINFO','TSCV.FOCUSINFO2'], 
                                  (lambda valDict: _FitsSbrPn(
                        valDict['TSCS.INSROTPOS_PF'], 
                        valDict['TSCS.InsRotPos'], valDict))),
            'FITS.SBR.INSROT_CMD': (['TSCS.INSROTCMD_PF','TSCS.INSROTCMD','TSCV.FOCUSINFO','TSCV.FOCUSINFO2'], 
                                  (lambda valDict: _FitsSbrPn(
                        valDict['TSCS.INSROTCMD_PF'], 
                        valDict['TSCS.INSROTCMD'], valDict))),
            'FITS.SBR.INST-PA' : (['TSCL.INSROTPA_PF','TSCL.InsRotPA','TSCV.FOCUSINFO','TSCV.FOCUSINFO2'], 
                                  (lambda valDict: _FmtP3fpn(
                        valDict['TSCL.INSROTPA_PF'], 
                        valDict['TSCL.InsRotPA'], valDict))),
            'FITS.SBR.INST_PA' : (['TSCL.INSROTPA_PF','TSCL.InsRotPA','TSCV.FOCUSINFO','TSCV.FOCUSINFO2'], 
                                  (lambda valDict: _FmtP3fpn(
                        valDict['TSCL.INSROTPA_PF'], 
                        valDict['TSCL.InsRotPA'], valDict))),
            'FITS.SBR.M2-POS1' : _ident('TSCL.M2POS1'),
            'FITS.SBR.M2-POS2' : _ident('TSCL.M2POS2'),
            'FITS.SBR.M2-POS3' : _ident('TSCL.M2POS3'),
            'FITS.SBR.M2-ANG1' : _ident('TSCL.M2ANG1'),
            'FITS.SBR.M2-ANG2' : _ident('TSCL.M2ANG2'),
            'FITS.SBR.M2-ANG3' : _ident('TSCL.M2ANG3'),
            'FITS.SBR.M2-TIP'  : _ident('STATL.TT_MODE'),
            'FITS.SBR.M2-TYPE' : (['TSCV.FOCUSINFO','TSCV.FOCUSINFO2'],
                                  _StatlTsc_F_Select),
            'FITS.SBR.RA'      : (['TSCS.ALPHA'], _FitsSbrRa),
            'FITS.SBR.RA_CMD'  : (['TSCS.ALPHA_C'], _FitsSbrRa_Cmd),
            'FITS.SBR.SECZ'    : (['TSCS.EL'], _FitsSbrSecz),
            'FITS.SBR.SEEING'  : _fmt('TSCL.SEEN', "%.2f", float),
            'FITS.SBR.SV-PRB'  : _ident('TSCL.SVPRB'),
            'FITS.SBR.TELFOCUS': (['TSCV.FOCUSINFO','TSCV.FOCUSINFO2'], 
                                  # _FitsSbrTelfocus),
                                  _StatlTsc_F_Select),
            'FITS.SBR.RA2000'  : (['TSCS.ALPHA', 'TSCS.DELTA', 'TSCS.EQUINOX'],
                                  _FitsSbrRa2000),
            'FITS.SBR.DEC2000' : (['TSCS.ALPHA', 'TSCS.DELTA', 'TSCS.EQUINOX'],
                                  _FitsSbrDec2000),
            # TODO: Need a dependence related to the date
            'FITS.SBR.UT1-UTC' : (['TSCS.ALPHA'],
                                  lambda valDict: self._FitsSbrUt1_Utc()),
            # TODO: Need a dependence related to the date
            'FITS.SBR.UT1_UTC' : (['TSCS.DELTA'],
                                  lambda valDict: self._FitsSbrUt1_Utc()),
            'FITS.SBR.ZD'      : (['TSCS.EL'], _FitsSbrZd),

            'FITS.PFU.OFFSET-X': _fmt('TSCV.PF_OFF_X', "%.8f", float),
            'FITS.PFU.OFFSET-TX': _fmt('TSCV.PF_OFF_TX', "%.8f", float),
            'FITS.PFU.OFFSET-Y': _fmt('TSCV.PF_OFF_Y', "%.8f", float),
            'FITS.PFU.OFFSET-TY': _fmt('TSCV.PF_OFF_TY', "%.8f", float),
            'FITS.PFU.OFFSET-Z': _fmt('TSCV.PF_OFF_Z', "%.8f", float),
            'FITS.PFU.OFFSET-TZ': _fmt('TSCV.PF_OFF_TZ', "%.8f", float),

            'FITS.VGW.IROT_TELESCOPE' : (['TSCV.InsRotMode'],
                                         _Statl_Irot_Telescope),
            'FITS.VGW.IMGROT_FLG': _fmt('VGWCMD.IMGROT_FLG', "%02x", int),
            'FITS.VGW.INSROTPA': _fmt('TSCL.INSROTPA', "%.8f", float),
            'FITS.VGW.FILTER01': _ident('TSCV.FILTER01'),

            'STATS.ANAB'       : _fmt('TSCS.ANAB', "%f", float),
            'STATS.AZ'        : _fmt('TSCS.AZ', "%f", float),
            'STATS.AZ_ADJ'    : (['TSCS.AZ'], _Stats_Az_Adj),
            'STATS.AZDIF'     : (['TSCS.AZDIF'], 
                                 (lambda valDict: _FmtP6f(_absval(valDict['TSCS.AZDIF'])))),
            'STATS.DEC'       : (['TSCS.DELTA'], _StatsDec),
            'STATL.DOMEDRIVE_POS' : _fmt('TSCS.DDPOS', "%f", float),
            'STATS.E'         : _chooser('TSCS.E', _onoff),
            'STATS.EL'        : _fmt('TSCS.EL', "%f", float),
            'STATS.ELDIF'     : (['TSCS.ELDIF'], 
                                 (lambda valDict: _FmtP6f(_absval(valDict['TSCS.ELDIF'])))),
            'STATS.EQUINOX'    : (['TSCS.EQUINOX'], _StatsFitsSbrEquinox),
            'STATS.IROTPF_POS' : _fmt('TSCS.INSROTPOS_PF',"%f", float),
            'STATS.IROT_POS'   : _fmt('TSCS.InsRotPos', "%f", float),
            'STATS.PMRA'       : _fmt('TSCS.PMRA', "%f", float),
            'STATS.PMDEC'      : _fmt('TSCS.PMDEC', "%f", float),
            'STATS.RA'        : (['TSCS.ALPHA'], _StatsRa),
            'STATS.ROTDIF'    : (['TSCS.ROTCMD','TSCS.ROTPOS'], 
                                 _Stats_Rotdif),
            'STATS.ROTDIF_PF'   : (['TSCS.INSROTCMD_PF','TSCS.INSROTPOS_PF'],
                                   _Stats_Rotdif_PF),
            # MISSING: STATL.ADCDIF
            # MISSING: STATL.ADCDIF_PF
            'STATL.ADC_F_SELECT' : (['TSCV.ADCType',
                                     'TSCV.FOCUSINFO','TSCV.FOCUSINFO2',
                                     'STATL.TSC_F_SELECT'],
                                    _StatlAdc_F_Select),
            'STATL.ADC_MODE' : _chooser('TSCV.ADCInOut',
                                         { 0x08 : 'IN',
                                           0x10 : 'OUT',
                                           }),
            'STATL.ADC_POS' : _fmt('TSCL.ADCPos', "%f", float),
            'STATL.ADC_SPEED' : _fmt('TSCL.ADCSpeed', "%f", float),
            'STATL.ADC_TELESCOPE': _chooser('TSCV.ADCMode',
                                             { 0x04 : 'LINK',
                                               0x08 : 'FREE',
                                               }),
            'STATL.ADCPF_POS' : _fmt('TSCL.ADCPOS_PF', "%f", float),
            'STATL.ADCPF_SPEED' : _fmt('TSCL.ADCSPEED_PF', "%f", float),
            'STATL.ADCPF_TELESCOPE': _chooser('TSCV.ADCMODE_PF',
                                             { 0x40 : 'LINK',
                                               0x80 : 'FREE',
                                               }),
            'STATL.WAVELEN' : _fmt('TSCV.ADCWaveLen', "%f", float),
            'STATL.ADCPF_POS' : _fmt('TSCL.ADCPOS_PF', "%f", float),
            # MISSING: STATL.AGXDIF
            # MISSING: STATL.AGYDIF
            'STATL.AG_AUTO_I_CUT' : _chooser('TSCV.AG_AUTO_I_CUT',
                                            { 0x40 : 'ON',
                                              0x80 : 'OFF',
                                              }),
            'STATL.AG_CALC_MODE' : _chooser('TSCV.AGCCalcMode',
                                                 { 0x01 : 'CTR',
                                                   0x02 : 'BSECT',
                                                   0x04 : 'PK',
                                                   }),
            'STATL.AG_CAL_LOOP'  : _fmt('TSCV.AG_CAL_LOOP',  "%d", int),
            'STATL.AG_EXPOSURE_DARK'  : _fmt('TSCV.AG_EXP_DARK', "%d", int),
            'STATL.AG_EXPOSURE_FLAT'  : _fmt('TSCV.AG_EXP_FLAT', "%d", int),
            'STATL.AG_EXPOSURE_OBJ'  : _fmt('TSCV.AG_EXP_OBJ', "%d", int),
            'STATL.AG_EXPOSURE_SKY'  : _fmt('TSCV.AG_EXP_SKY', "%d", int),

            'STATL.AG_OVERLOAD' : _chooser('TSCV.AG_OVERLOAD',
                                            { 0x00 : 'NORMAL',
                                              0x08 : 'ALARM',
                                              }),
            'STATL.AG_R'         : _fmt('TSCL.AG_R', "%.8f", float),
            'STATL.AG_R_CMD'     : _fmt('TSCL.AG_R_CMD', "%.8f", float),
            'STATL.AG_R_DIF'     : (['TSCL.AG_R', 'TSCL.AG_R_CMD'],
                                 (lambda valDict: "%f" % (
                                    math.fabs(valDict['TSCL.AG_R_CMD'] - valDict['TSCL.AG_R'])))),
            'STATL.AG_THETA'     : _fmt('TSCL.AG_THETA', "%.8f", float),
            'STATL.AG_THETA_CMD' : _fmt('TSCL.AG_THETA_CMD', "%.8f", float),
            'STATL.AG_THETA_DIF' : (['TSCL.AG_THETA', 'TSCL.AG_THETA_CMD'],
                                 (lambda valDict: "%f" % (
                                    math.fabs(valDict['TSCL.AG_THETA_CMD'] - valDict['TSCL.AG_THETA'])))),
            'STATL.AG_X1'     : _fmt('TSCV.AGImgRegX1', "%d", int),
            'STATL.AG_X2'     : (['TSCV.AGImgRegX1', 'TSCV.AGImgRegX2'],
                                 (lambda valDict: "%d" % (
                                    int(valDict['TSCV.AGImgRegX1']) + int(valDict['TSCV.AGImgRegX2']) - 1))),
            'STATL.AG_Y1'     : _fmt('TSCV.AGImgRegY1', "%d", int),
            'STATL.AG_Y2'     : (['TSCV.AGImgRegY1', 'TSCV.AGImgRegY2'],
                                 (lambda valDict: "%d" % (
                                    int(valDict['TSCV.AGImgRegY1']) + int(valDict['TSCV.AGImgRegY2']) - 1))),
            'STATL.AG1_I_BOTTOM' : _fmt('TSCV.AG1_I_BOTTOM', "%d", int),
            'STATL.AG1_I_CEIL'   : _fmt('TSCV.AG1_I_CEIL', "%d", int),
            'STATL.AG1_X1' : _fmt('TSCV.AGCCalcRegX11', "%d", int),
            'STATL.AG1_X2' : (['TSCV.AGCCalcRegX11', 'TSCV.AGCCalcRegX21'],
                                 (lambda valDict: "%d" % (
                                    int(valDict['TSCV.AGCCalcRegX11']) + int(valDict['TSCV.AGCCalcRegX21']) - 1))),
            'STATL.AG1_Y1' : _fmt('TSCV.AGCCalcRegY11', "%d", int),
            'STATL.AG1_Y2' : (['TSCV.AGCCalcRegY11', 'TSCV.AGCCalcRegY21'],
                                 (lambda valDict: "%d" % (
                                    int(valDict['TSCV.AGCCalcRegY11']) + int(valDict['TSCV.AGCCalcRegY21']) - 1))),
            'STATL.AG2_I_BOTTOM' : _fmt('TSCV.AG2_I_BOTTOM', "%d", int),
            'STATL.AG2_I_CEIL'   : _fmt('TSCV.AG2_I_CEIL', "%d", int),
            'STATL.AG2_X1' : _fmt('TSCV.AGCCalcRegX12', "%d", int),
            'STATL.AG2_X2' : (['TSCV.AGCCalcRegX12', 'TSCV.AGCCalcRegX22'],
                                 (lambda valDict: "%d" % (
                                    int(valDict['TSCV.AGCCalcRegX12']) + int(valDict['TSCV.AGCCalcRegX22']) - 1))),
            'STATL.AG2_Y1' : _fmt('TSCV.AGCCalcRegY12', "%d", int),
            'STATL.AG2_Y2' : (['TSCV.AGCCalcRegY12', 'TSCV.AGCCalcRegY22'],
                                 (lambda valDict: "%d" % (
                                    int(valDict['TSCV.AGCCalcRegY12']) + int(valDict['TSCV.AGCCalcRegY22']) - 1))),
            'STATL.AGPF_X'       : _fmt('TSCL.AGPF_X', "%.6f", float),
            'STATL.AGPF_Y'       : _fmt('TSCL.AGPF_Y', "%.6f", float),
            'STATL.AGPF_Z'       : _fmt('TSCL.AGPF_Z', "%.6f", float),

            'STATL.AGPIR_EXPOSURE' : _fmt('TSCV.AGPIRExpTime', "%d", int),
            'STATL.AGPIR_BINNING' : _fmt('TSCV.AGPIRBinning', "%02x", int),
            'STATL.AGPIR_X'       : _fmt('TSCL.AGPIR_X', "%f", float),
            # MISSING?: STATL.AGPIR_Y (can't find it in StatLexec.c)
            'STATL.AGPIR_X1'       : _fmt('TSCV.AGPIRImgRegX1', "%d", int),
            'STATL.AGPIR_X2' : (['TSCV.AGPIRImgRegX1', 'TSCV.AGPIRImgRegX2'],
                                 (lambda valDict: "%d" % (
                                    int(valDict['TSCV.AGPIRImgRegX1']) + int(valDict['TSCV.AGPIRImgRegX2']) - 1))),
            'STATL.AGPIR_Y1'       : _fmt('TSCV.AGPIRImgRegY1', "%d", int),
            'STATL.AGPIR_Y2' : (['TSCV.AGPIRImgRegY1', 'TSCV.AGPIRImgRegY2'],
                                 (lambda valDict: "%d" % (
                                    int(valDict['TSCV.AGPIRImgRegY1']) + int(valDict['TSCV.AGPIRImgRegY2']) - 1))),
            'STATL.AGPIR_CALC_X1'   : _fmt('TSCV.AGPIRCCalcRegX1', "%d", int),
            'STATL.AGPIR_CALC_X2' : (['TSCV.AGPIRCCalcRegX1', 'TSCV.AGPIRCCalcRegX2'],
                                 (lambda valDict: "%d" % (
                                    int(valDict['TSCV.AGPIRCCalcRegX1']) + int(valDict['TSCV.AGPIRCCalcRegX2']) - 1))),
            'STATL.AGPIR_CALC_Y1'   : _fmt('TSCV.AGPIRCCalcRegY1', "%d", int),
            'STATL.AGPIR_CALC_Y2' : (['TSCV.AGPIRCCalcRegY1', 'TSCV.AGPIRCCalcRegY2'],
                                 (lambda valDict: "%d" % (
                                    int(valDict['TSCV.AGPIRCCalcRegY1']) + int(valDict['TSCV.AGPIRCCalcRegY2']) - 1))),
            'STATL.AGPIR_I_BOTTOM'     : _fmt('TSCV.AGPIR_I_BOTTOM', "%d", int),
            'STATL.AGPIR_I_CEIL'       : _fmt('TSCV.AGPIR_I_CEIL', "%d", int),
            'STATL.PIR_SHUTTER' : _chooser('TSCV.PIRShutter',
                                            { 0x00: '',
                                              0x01 : 'OPEN',
                                              0x02 : 'CLOSE',
                                              }),
            'STATL.PIR_CALC_REGION' : (['TSCV.AGPIRCCalc','TSCV.AGFMOSCCalc'],
                                    _StatL_PIR_Calc_Region),
            # MISSING: STATL.PIR_CALC_REGION_INFO

            'STATL.AGHSC_X1' : _fmt('TSCV.HSC.SCAG.ImgRegX1', "%d", int),
            'STATL.AGHSC_X2' : (['TSCV.HSC.SCAG.ImgRegX1', 'TSCV.HSC.SCAG.ImgRegX2'],
                                 (lambda valDict: "%d" % (
                                    int(valDict['TSCV.HSC.SCAG.ImgRegX1']) + int(valDict['TSCV.HSC.SCAG.ImgRegX2']) - 1))),
            'STATL.AGHSC_Y1' : _fmt('TSCV.HSC.SCAG.ImgRegY1', "%d", int),
            'STATL.AGHSC_Y2' : (['TSCV.HSC.SCAG.ImgRegY1', 'TSCV.HSC.SCAG.ImgRegY2'],
                                 (lambda valDict: "%d" % (
                                    int(valDict['TSCV.HSC.SCAG.ImgRegY1']) + int(valDict['TSCV.HSC.SCAG.ImgRegY2']) - 1))),
            'STATL.AGHSC_CALC_X1' : _fmt('TSCV.HSC.SCAG.CCalcRegX1', "%d", int),
            'STATL.AGHSC_CALC_X2' : (['TSCV.HSC.SCAG.CCalcRegX1', 'TSCV.HSC.SCAG.CCalcRegX2'],
                                 (lambda valDict: "%d" % (
                                    int(valDict['TSCV.HSC.SCAG.CCalcRegX1']) + int(valDict['TSCV.HSC.SCAG.CCalcRegX2']) - 1))),
            'STATL.AGHSC_CALC_Y1' : _fmt('TSCV.HSC.SCAG.CCalcRegY1', "%d", int),
            'STATL.AGHSC_CALC_Y2' : (['TSCV.HSC.SCAG.CCalcRegY1', 'TSCV.HSC.SCAG.CCalcRegY2'],
                                 (lambda valDict: "%d" % (
                                    int(valDict['TSCV.HSC.SCAG.CCalcRegY1']) + int(valDict['TSCV.HSC.SCAG.CCalcRegY2']) - 1))),

            'STATL.AG_BINNING'   : _fmt('TSCV.AGBinning', "%02x", int),
            'STATL.AG_SHUTTER' : _chooser('TSCV.AGShutter',
                                           { 0x00: '',
                                             0x01 : 'OPEN',
                                             0x02 : 'CLOSE',
                                             }),
            'STATL.AGRERR':   (['TSCL.AG1dX','TSCL.AG1dY',
                                'TSCV.FOCUSINFO','TSCV.FOCUSINFO2',
                                'TSCV.TelDrive','TSCL.AGPIRdX','TSCL.AGPIRdY',
                                'TSCL.AGFMOSdAZ','TSCL.AGFMOSdEL',
                                'TSCV.AGPIRCCalc','TSCV.AGFMOSCCalc',
                                'TSCL.HSC.SCAG.DX', 'TSCL.HSC.SCAG.DY',
                                'TSCL.HSC.SHAG.DX', 'TSCL.HSC.SHAG.DY',
                                'TSCV.HSC.SCAG.CCalc','TSCV.HSC.SHAG.CCalc',
                                ],
                               _StatlAgrErr),

            'STATL.AZ_SPEED'  : _fmt('TSCL.AZ_SPEED', "%+.1f", float),
            'STATL.CALC_MODE' : _chooser('TSCV.AGCCalcMode',
                                         { 0x00: '',
                                           0x01 : 'CTR',
                                           0x02 : 'BSECT',
                                           0x04 : 'PK',
                                           0x08 : 'SLIT',
                                           }),
            'STATL.CALC_REGION' : _chooser('TSCV.AGCCalc',
                                           { 0x00 : '',
                                             0x04 : '1',
                                             0x10 : '2',
                                             0x14 : '1', # BB?
                                             }),
            'STATL.CAL_DARK' : _chooser('TSCV.AGCalibDark', _onoff),
            # MISSING: STATL.CAL_FILTER_A
            'STATL.CAL_FILTER_A_NUM' : _chooser('TSCV.CAL_FILTER_A',
                                                 { 0x00 : '-',
                                                   0x01 : '1',
                                                   0x02 : '2',
                                                   0x04 : '3',
                                                   0x08 : '4',
                                                   }),
            # MISSING: STATL.CAL_FILTER_B
            'STATL.CAL_FILTER_B_NUM' : _chooser('TSCV.CAL_FILTER_B',
                                                 { 0x00 : '-',
                                                   0x01 : '1',
                                                   0x02 : '2',
                                                   0x04 : '3',
                                                   0x08 : '4',
                                                   }),
            # MISSING: STATL.CAL_FILTER_C
            'STATL.CAL_FILTER_C_NUM' : _chooser('TSCV.CAL_FILTER_C',
                                                 { 0x00 : '-',
                                                   0x01 : '1',
                                                   0x02 : '2',
                                                   0x04 : '3',
                                                   0x08 : '4',
                                                   }),
            # MISSING: STATL.CAL_FILTER_D
            'STATL.CAL_FILTER_D_NUM' : _chooser('TSCV.CAL_FILTER_D',
                                                 { 0x00 : '-',
                                                   0x01 : '1',
                                                   0x02 : '2',
                                                   0x04 : '3',
                                                   0x08 : '4',
                                                   }),
            'STATL.CAL_FLAT' : _chooser('TSCV.AGCalibFlat', _onoff),
            # MISSING: STATL.CAL_HAL_LAMP1
            # MISSING: STATL.CAL_HAL_LAMP2
            # MISSING: STATL.CAL_HCT_LAMP1
            # MISSING: STATL.CAL_HCT_LAMP2
            'STATL.CAL_HAL1_AMP' : _fmt('TSCL.CAL_HAL1_AMP', "%+6.4f", float),
            'STATL.CAL_HAL2_AMP' : _fmt('TSCL.CAL_HAL2_AMP', "%+6.4f", float),
            'STATL.CAL_HCT1_AMP' : _fmt('TSCL.CAL_HCT1_AMP', "%+6.3f", float),
            'STATL.CAL_HCT2_AMP' : _fmt('TSCL.CAL_HCT2_AMP', "%+6.3f", float),
            'STATL.CAL_POS' : _fmt('TSCL.CAL_POS', "%+7.3f", float),
            # MISSING: STATL.CAL_RGL_LAMP1
            # MISSING: STATL.CAL_RGL_LAMP2
            # MISSING: STATL.CAL_SHUTTER
            'STATL.CAL_SKY' : _chooser('TSCV.AGCalibSky', _onoff),
            'STATL.CELLCOVER_POS' : _chooser('TSCV.CellCover',
                                              { 0x00: '',
                                                0x01 : 'OPEN',
                                                0x04 : 'CLOSE',
                                                }),
            # MISSING: STATL.DEC_OFFSET
            'STATL.DOMESHUTTER_POS' : _chooser('TSCV.DomeShutter',
                                              { 0x00: '',
                                                0x10 : 'OPEN',
                                                0x20 : 'CLOSE',
                                                }),
            # MISSING STATL.DRIVE
            'STATL.D_TYPE'    : (['TSCV.AG_DT_OBJ','TSCV.AG_DT_SKY',
                                  'TSCV.AG_DT_FLAT','TSCV.AG_DT_DARK'],
                                 _Statl_D_Type),
            'STATL.EL_SPEED'  : _fmt('TSCL.EL_SPEED', "%+.1f", float),
            'STATL.FILTER' : _fmt('TSCV.SVFilter', "%d", int),
            'STATL.HCT_LAMP' : _chooser('TSCV.CAL_HCT_LAMP',
                                         { 0x01 : 'LAMP1',
                                           0x02 : 'LAMP2',
                                           0x04 : 'RETRACT',
                                           }),
            'STATL.IROT_POS' : _fmt('TSCS.InsRotPos', "%f", float),
            'STATL.IROT_SPEED' : _fmt('TSCL.InsRotSpeed', "%f", float),
            'STATL.IROT_TELESCOPE' : (['TSCV.InsRotMode'],
                                      _Statl_Irot_Telescope),
            'STATL.IROTPF_SPEED' : _fmt('TSCL.IROTPF_SPEED', "%f", float),
            'STATL.IROTPF_TELESCOPE' : (['TSCV.INSROTMODE_PF'],
                                        _Statl_IrotPf_Telescope),
            'STATL.IROT_TYPE' : (['TSCV.ImgRotType','TSCV.ImgRotType_NS_IR',
                                  'TSCV.FOCUSINFO','TSCV.FOCUSINFO2'],
                                 _Statl_Irot_Type),
            # MISSING: STATL.LAMP
            # MISSING: STATL.LIMIT_AZ
            # MISSING: STATL.LIMIT_EL
            # MISSING: STATL.LIMIT_ROT
            'STATL.M1COVER_POS' : _chooser('TSCV.M1Cover',
                                         { 0x1111111111111111111111 : 'OPEN',
                                           0x4444444444444444444444 : 'CLOSE',
                                           }),
            'STATL.M2_TIPTILT' : _chooser('TSCV.M2_TIPTILT',
                                              { 0x08 : 'AG',
                                                0x10 : 'AO_OBE',
                                                }),
            'STATL.OBJNAME': _fmt('TSCV.OBJNAME', "%.32s", str),
            'STATL.OBJKIND': _fmt('TSCV.OBJKIND', "%.32s", str),
            'STATL.P_SELECT' : _chooser('TSCV.P_SEL',
                                         { 0x00 : '',
                                           0x10 : 'FRONT',
                                           0x20 : 'FRONT',
                                           0x30 : 'FRONT',
                                           0x40 : 'REAR',
                                           0x80 : 'REAR',
                                           0xC0 : 'REAR',
                                           }),
            # MISSING: STATL.RA_OFFSET
            'STATL.SH_BINNING' : _fmt('TSCV.SHBinning', "%02x", int),
            'STATL.SH_CAL_DARK' : _chooser('TSCV.SHCalibDark', _onoff),
            'STATL.SH_CAL_LOOP' : _fmt('TSCV.SH_CAL_LOOP', "%d", int),
            'STATL.SH_CAL_SKY' : _chooser('TSCV.SHCalibSky', _onoff),
            'STATL.SH_EXPOSURE' : _fmt('TSCV.SHExpTime', '%d',
                                          lambda val: int(val)*100),
            'STATL.SH_I_BOTTOM' : _fmt('TSCV.SH_I_BOTTOM', "%d", int),
            'STATL.SH_I_CEIL' : _fmt('TSCV.SH_I_CEIL', "%d", int),
            'STATL.SH_SHUTTER' : _chooser('TSCV.SHShutter',
                                         { 0x10 : 'OPEN',
                                           0x20 : 'CLOSE',
                                           }),
            'STATL.SVRERR'      : (['TSCL.SV1DX','TSCL.SV1DY'],
                                   _StatlSvrErr),
            'STATL.SVPROBE_POS' : _fmt('TSCL.SVPos', "%f", float),
            'STATL.SV_AUTO_I_CUT' : _chooser('TSCV.SV_AUTO_I_CUT',
                                            { 0x40 : 'ON',
                                              0x80 : 'OFF',
                                              }),
            'STATL.SV_BINNING' : _fmt('TSCV.SVBinning', "%02x", int),
            'STATL.SV_CALC_MODE' : _chooser('TSCV.SVCCalcMode',
                                                 { 0x01 : 'CTR',
                                                   0x02 : 'BSECT',
                                                   0x04 : 'PK',
                                                   0x08 : 'SLIT',
                                                   }),
            'STATL.SV_CALC_REGION' : _chooser('TSCV.SVCCalc',
                                                 { 0x00 : '',
                                                   0x04 : '1',
                                                   0x10 : '2',
                                                   0x14 : '1', # BB?
                                                   }),
            'STATL.SV_CAL_LOOP' : _fmt('TSCV.SV_CAL_LOOP', "%d", int),
            'STATL.SV_EXPOSURE' : _fmt('TSCV.SVExpTime', "%d", int),
            'STATL.SV_OVERLOAD' : _chooser('TSCV.SV_OVERLOAD',
                                            { 0x00 : 'NORMAL',
                                              0x08 : 'ALARM',
                                              }),
            'STATL.SV_X1'     : _fmt('TSCV.SVImgRegX1', "%d", int),
            'STATL.SV_X2'     : (['TSCV.SVImgRegX1', 'TSCV.SVImgRegX2'],
                                 (lambda valDict: "%d" % (
                                    int(valDict['TSCV.SVImgRegX1']) + int(valDict['TSCV.SVImgRegX2']) - 1))),
            'STATL.SV_Y1'     : _fmt('TSCV.SVImgRegY1', "%d", int),
            'STATL.SV_Y2'     : (['TSCV.SVImgRegY1', 'TSCV.SVImgRegY2'],
                                 (lambda valDict: "%d" % (
                                    int(valDict['TSCV.SVImgRegY1']) + int(valDict['TSCV.SVImgRegY2']) - 1))),
            'STATL.SV1_I_BOTTOM' : _fmt('TSCV.SV1_I_BOTTOM', "%d", int),
            'STATL.SV1_I_CEIL'   : _fmt('TSCV.SV1_I_CEIL', "%d", int),
            'STATL.SV1_X1' : _fmt('TSCV.SVCCalcRegX11', "%d", int),
            'STATL.SV1_X2' : (['TSCV.SVCCalcRegX11', 'TSCV.SVCCalcRegX21'],
                                 (lambda valDict: "%d" % (
                                    int(valDict['TSCV.SVCCalcRegX11']) + int(valDict['TSCV.SVCCalcRegX21']) - 1))),
            'STATL.SV1_Y1' : _fmt('TSCV.SVCCalcRegY11', "%d", int),
            'STATL.SV1_Y2' : (['TSCV.SVCCalcRegY11', 'TSCV.SVCCalcRegY21'],
                                 (lambda valDict: "%d" % (
                                    int(valDict['TSCV.SVCCalcRegY11']) + int(valDict['TSCV.SVCCalcRegY21']) - 1))),
            'STATL.SV2_I_BOTTOM' : _fmt('TSCV.SV2_I_BOTTOM', "%d", int),
            'STATL.SV2_I_CEIL'   : _fmt('TSCV.SV2_I_CEIL', "%d", int),

            'STATL.SV2_X1' : _fmt('TSCV.SVCCalcRegX12', "%d", int),
            'STATL.SV2_X2' : (['TSCV.SVCCalcRegX12', 'TSCV.SVCCalcRegX22'],
                                 (lambda valDict: "%d" % (
                                    int(valDict['TSCV.SVCCalcRegX12']) + int(valDict['TSCV.SVCCalcRegX22']) - 1))),
            'STATL.SV2_Y1' : _fmt('TSCV.SVCCalcRegY12', "%d", int),
            'STATL.SV2_Y2' : (['TSCV.SVCCalcRegY12', 'TSCV.SVCCalcRegY22'],
                                 (lambda valDict: "%d" % (
                                    int(valDict['TSCV.SVCCalcRegY12']) + int(valDict['TSCV.SVCCalcRegY22']) - 1))),

            'STATL.SV_SHUTTER' : _chooser('TSCV.SVShutter',
                                           { 0x01 : 'OPEN',
                                             0x02 : 'CLOSE',
                                             }),
            'STATL.TELDRIVE'    :    (
                ['TSCV.TelDrive','TSCL.AG1Intensity','TSCL.SV1Intensity',
                 'TSCL.SV1Intensity','TSCS.AZDIF','TSCS.ELDIF',
                 'TSCV.TRACKING',
                 'TSCV.AutoGuideOn','TSCV.SVAutoGuideOn',
                 'TSCL.AGPIRIntensity','TSCL.AGFMOSIntensity',
                 'TSCL.AG2Intensity','TSCL.SV2Intensity',
                 'STATL.AGRERR', 'STATL.SVRERR',
                 'TSCL.HSC.SCAG.Intensity', 'TSCL.HSC.SHAG.Intensity'],
                _StatlTeldrive),
            'STATL.TELDRIVE_INFO': (
                ['TSCV.TelDrive','TSCL.AG1Intensity','TSCL.SV1Intensity',
                 'TSCL.SV1Intensity','TSCS.AZDIF','TSCS.ELDIF',
                 'TSCV.TRACKING',
                 'TSCV.AutoGuideOn','TSCV.SVAutoGuideOn',
                 'TSCL.AGPIRIntensity','TSCL.AGFMOSIntensity',
                 'TSCL.AG2Intensity','TSCL.SV2Intensity',
                 'STATL.AGRERR', 'STATL.SVRERR',
                 'TSCL.HSC.SCAG.Intensity', 'TSCL.HSC.SHAG.Intensity'],
                _StatlTeldriveInfo),
            'STATL.TOPSCREEN_FPOS' : _fmt('TSCL.TSFPOS', "%f", float),
            'STATL.TOPSCREEN_RPOS' : _fmt('TSCL.TSRPOS', "%f", float),
            # MISSING: STATL.TOPS_F_DIF
            # MISSING: STATL.TOPS_R_DIF
            'STATL.TRACKING'     :  _chooser('TSCV.TRACKING',
                                              { 0x00       : 'POINTING',
                                                0x04       : 'SIDEREAL',
                                                0x08       : 'NON_SIDEREAL_ERR',
                                                0x10       : 'NON_SIDEREAL',
                                                0x20       : 'NON_SIDEREAL_ERR',
                                                }),
            'STATL.TSC_F_SELECT' : (['TSCV.FOCUSINFO','TSCV.FOCUSINFO2'],
                                    _StatlTsc_F_Select),
            'STATL.TT_AMP' : _fmt('TSCL.Amp', "%f", float),
            'STATL.TT_FQ' : _fmt('TSCL.Fq', "%f", float),
            'STATL.TT_MODE'      :  _chooser('TSCV.M2TipTilt',
                                              { 0x00       : 'OFF',
                                                0x01       : 'CHOPPING',
                                                0x02       : 'TIPTILT',
                                                0x04       : 'POSN',
                                                }),
            'STATL.TT_OFFSETMODE': _chooser('TSCV.TT_OFFSETMODE',
                                             { 0x01       : 'MINUS',
                                               0x02       : 'ZERO',
                                               0x04       : 'PLUS',
                                               }),
            'STATL.TT_PATTERN'   : _chooser('TSCV.TT_PATTERN',
                                             { 0x01       : '1',
                                               0x02       : '2',
                                               0x04       : '3',
                                               }),
            'STATL.TT_POS' : _fmt('TSCL.TT_POS', "%f", float),
            'STATL.TT_SIGNAL'    : _chooser('TSCV.TT_SIGNAL',
                                             { 0x01       : 'INT',
                                               0x02       : 'EXT',
                                               }),
            'STATL.TT_TX' : _fmt('TSCS.TT_TX', "%f", float),
            'STATL.TT_TY' : _fmt('TSCS.TT_TY', "%f", float),
            'STATL.TT_Z' : _fmt('TSCS.TT_Z', "%f", float),
            'STATL.TT_ZEROBIAS' : _fmt('TSCV.TT_ZEROBIAS', "%f", float),
            'STATL.WINDSCREEN_POS' : _fmt('TSCL.WSPOS', "%f", float),
            'STATL.WINDSDIF'    : (['TSCL.WINDSCMD','TSCL.WINDSPOS'],
                                   _Statl_WindsDif),
            'STATL.WINDSDIF_SIGN' :(['TSCL.WINDSCMD','TSCL.WINDSPOS'],
                                    _Statl_WindsDif_Sign),
            'STATL.Z'           : _fmt('TSCL.ZPOS', "%f", float),
            'STATL.Z_PIR'       : _fmt('TSCL.ZPOS_PIR', "%f", float),
            'STATL.ZDIF'        : (['TSCL.ZCMD','TSCL.ZPOS'], _Statl_ZDif),
            'STATL.ZERNIKE_RMS' : (['TSCV.ZERNIKE_RMS'],
                                   (lambda valDict: _Statl_Zernike_RMS('TSCV.ZERNIKE_RMS',
                                                                       valDict))),
            'STATL.ZERNIKE_RMS_WOA20' : (['TSCV.ZERNIKE_RMS_WOA20'],
                                         (lambda valDict: _Statl_Zernike_RMS('TSCV.ZERNIKE_RMS_WOA20',
                                                                             valDict))),
            'GEN2.TSCLOGINS' : (['TSCV.TSC.LOGIN0', 'TSCV.TSC.LOGIN1',
                                 'TSCV.TSC.LOGIN2', 'TSCV.TSC.LOGIN3',
                                 'TSCV.TSC.LOGIN4', 'TSCV.TSC.LOGIN5',
                                 'TSCV.TSC.LOGIN6', 'TSCV.TSC.LOGIN7',
                                 'TSCV.TSC.LOGIN8', 'TSCV.TSC.LOGIN9',
                                 ],
                                (lambda valDict: ','.join(_calc_tsc_logins(valDict)))),

            'GEN2.OCSLOGIN' : (['GEN2.TSCLOGINS'],
                               (lambda valDict: 'OCS%' in valDict['GEN2.TSCLOGINS'])),
            'GEN2.OBSLOGIN' : (['GEN2.TSCLOGINS'],
                               (lambda valDict: 'OBS%' in valDict['GEN2.TSCLOGINS'])),
            'GEN2.TSCMODE' : (['TSCL.MODE'], _calc_tsc_mode),
            'STATL.DEW_POINT_O' : (["TSCL.TEMP_O", "TSCL.HUMI_O"], _calc_dew_point_outside),
            'STATL.HSC.IRFiltExchRdy0': (['TSCV.HSC.FiltExchRdy'], lambda valDict: _maskBits('TSCV.HSC.FiltExchRdy', 0x01, valDict)),
            'STATL.HSC.OptFiltExchRdy0': (['TSCV.HSC.FiltExchRdy'], lambda valDict: _maskBits('TSCV.HSC.FiltExchRdy', 0x04, valDict)),
            'STATL.ELStowPins90Sel':  (['CXWS.TSCV.STOW_1'], lambda valDict: _maskBits('CXWS.TSCV.STOW_1', 0x01, valDict)),
            'STATL.ELStowPinsOn':     (['CXWS.TSCV.STOW_1'], lambda valDict: _maskBits('CXWS.TSCV.STOW_1', 0x04, valDict)),
            'STATL.ELStowPinsOnRdy':  (['CXWS.TSCV.STOW_1'], lambda valDict: _maskBits('CXWS.TSCV.STOW_1', 0x10, valDict)),
            'STATL.ELDriveOn':        (['CXWS.TSCV.TELDRIVE'], lambda valDict: _maskBits('CXWS.TSCV.TELDRIVE', 0x08, valDict)),
            'STATL.ELDriveOff':       (['CXWS.TSCV.TELDRIVE'], lambda valDict: _maskBits('CXWS.TSCV.TELDRIVE', 0x10, valDict)),
           }

        self.derivedKeys = self.deriveMap.keys()
        #self.derivedKeys.sort()
        
        # The set of all aliases covered by this deriver
        self.allDerived = set(self.derivedKeys)

        # This sets self.revDerviceMap
        self.__compute_reverse_dependence_map()
        #print self.revDeriveMap

        # table of UT1-UTC offsets, indexed by truncated julian date
        self.ut1_utc = {}


    def __compute_reverse_dependence_map(self):
        """Compute the reverse dependency graph of needed keys, such that
        each value of self.revDeriveMap is a set of derived aliases linked
        to the alias that is the key.
        """

        def process_keys(orig_key, key):
            needed_keys, derive_fn = self.deriveMap[key]
            for nkey in needed_keys:
                if not (nkey in self.derivedKeys):
                    try:
                        s = self.revDeriveMap[nkey]
                        s.add(orig_key)
                        
                    except KeyError:
                        s = set([orig_key])
                        self.revDeriveMap[nkey] = s

                else:
                    process_keys(orig_key, nkey)
            
        self.revDeriveMap = {}

        for key in self.derivedKeys:
            process_keys(key, key)
            

    def isDerived(self, alias):
        return (alias in self.allDerived)


    def aliasesToDerivedAliases(self, aliases):
        """Return all derived aliases that are linked to those in (aliases)
        as a list.
        """
        to_derive = set([])
        
        for alias in aliases:
            if self.revDeriveMap.has_key(alias):
                to_derive = to_derive.union(self.revDeriveMap[alias])

        return list(to_derive)


    def aliasToDerivedAliases(self, alias):
        return self.aliasesToDerivedAliases([alias])
    

    def aliasesToDerivedAliasesDict(self, aliases, value=None):
        """Return all derived aliases that are linked to those in (aliases)
        as a dict, where the values are set to (value).
        """
        to_derive = self.aliasesToDerivedAliases(aliases)
        
        return {}.fromkeys(to_derive, value)


    def __derive(self, statusDict, valDict):
        # Derive values into statusDict.  valDict contains all necessary
        # values
        for key in statusDict.keys():
            if key in self.derivedKeys:
                #? print '  self.derivedMap[%s ] = %s' % (key,self.derivedMap[key ])
                try:
                    needed_keys, derive_fn = self.deriveMap[key]

##                     self.logger.debug("Deriving '%s' using %s" % (key,
##                                                                   valDict))
                    val = derive_fn(valDict)

##                     self.logger.debug("%s <== %s" % (key, str(val)))

                except Exception, e:
                    val = STATERROR
                    #? print 'Exception deriving %s' % key
                    # Switch to level 15 logging here, which is between
                    # DEBUG and INFO; that way we don't see this message
                    # which is generated constantly
                    self.logger.log(15, "Exception deriving '%s': %s" % (
                        key, str(e)))

            else:
                # Just an ordinary piece of status
                # TODO: should this be an error?
                val = self.statObj[key]

            statusDict[key] = val


    def derive(self, statusDict):
        """Compute derived status alias values that are not provided directly 
        by TCS, instruments or OCS subsystems.
        """

        # Compute the list of aliases we need to get from the status
        # store to compute all derived values
        fetch_set = set([])
        
        for alias in statusDict.keys():
            try:
                needed_keys, derive_fn = self.deriveMap[alias]

                fetch_set = fetch_set.union(set(needed_keys))

            except KeyError:
                pass

        # Now get those values
        if fetch_set:
            # NOTE: statObj needs to provide derived alias values as
            # well as non-derived, because some derived values depend
            # on others!
            valDict = self.statObj.fetchList2Dict(fetch_set, derive=True)

        else:
            valDict = {}

        # Derive all keys in this statusDict
        self.__derive(statusDict, valDict)


    def deriveOne(self, alias):
        d = { alias: None }
        self.derive(d)

        return d[alias]
        

    def read_UT1_UTC_table(self, ut1utc_path):
        """Reads in the UT1-UTC table."""

        regex_ut1utc = re.compile(r'^\s*(\d{4}\s+\d+\s+\d+)\s+(\d+)\s+([\d\.\-]+)\s+([\d\.\-]+)\s+([\d\.\-]+)\s*$')
        # Sample from the file:
        ##        2008 11  1  54771       0.1501      0.1603     -0.49034
        ##        2008 11  2  54772       0.1470      0.1590     -0.49078
        ##        2008 11  3  54773       0.1438      0.1577     -0.49123
        ##        2008 11  4  54774       0.1407      0.1565     -0.49175

        try:
            fd = open(ut1utc_path, 'r')

        except IOError, e:
            raise statusDerivationError("Could not open '%s': %s" % (
                    ut1utc_path, str(e)))

        try:
            lineno = 0
            for line in fd:
                lineno += 1
                inLine = line.strip()
                if len(inLine) == 0:
                    continue
                if not inLine.startswith('20'):    # slight optimization
                    continue
            
                match = regex_ut1utc.match(inLine)
                if not match:
                    continue
                self.logger.debug("inLine=%s" % inLine)

                inWords = inLine.split()  #string.split(inLine)
                if len(inWords) == 7:
                    self.ut1_utc[inWords[3]] = (float(inWords[4]),
                                                float(inWords[5]),
                                                float(inWords[6]))

        except Exception, e:
            fd.close()
            raise statusDerivationError("Failure during reading '%s': %s" % (
                    ut1utc_path, str(e)))

        fd.close()


    def _FitsSbrUt1_Utc(self):
        """Compute FITS.SBR.UT1-UTC.
        The algorithm for this function should be equivalent to that in the
        SOSS code in OSSL/OSSL_StatU.d/OSSL_StatUexec.c and the OSSg_GetDate
        and getJDTime functions in liboss_g/OSSg_GetDateTime.c .  
        """
        # Subtracting 2400000.5 from Julian Date yields
        # Modified Julian Date (MJD)
        jd = radec.julianDate()
        cm = '%.0f' % (jd - 2400000.5)
        #? print 'jd = ', jd, ', cm = ', cm

        try:
            return self.ut1_utc[cm][2]

        except KeyError:
            raise statusDerivationError("%s not found in UT1-UTC table" % (
                    cm))



######################################################################
################   declare computation functions   ###################
######################################################################

# Utility functions that are mused for multiple alias computations
def _FmtF(fval):
    """Format fval with %f"""
    if  fval == STATNONE:
        return STATNONE
    else:
        return '%f' % fval

def _FmtD(dval):
    """Format dval with %d"""
    if  dval == STATNONE:
        return STATNONE
    else:
        return '%d' % dval

def _FmtP0f(fval):
    """Format fval with %.0f"""
    if  fval == STATNONE:
        return STATNONE
    else:
        return '%.0f' % fval

def _FmtP1f(fval):
    """Format fval with %.1f"""
    if  fval == STATNONE:
        return STATNONE
    else:
        return '%.1f' % fval

def _FmtP2f(fval):
    """Format fval with %.2f"""
    if  fval == STATNONE:
        return STATNONE
    else:
        return '%.2f' % fval

def _FmtP3f(fval):
    """Format fval with %.3f"""
    if  fval == STATNONE:
        return STATNONE
    else:
        return '%.3f' % fval

def _FmtP5f(fval):
    """Format fval with %.5f"""
    if  fval == STATNONE:
        return STATNONE
    else:
        return '%.5f' % fval

def _FmtP6f(fval):
    """Format fval with %.6f"""
    if  fval == STATNONE:
        return STATNONE
    else:
        return '%.6f' % fval

def _FmtP8f(fval):
    """Format fval with %.8f"""
    if  fval == STATNONE:
        return STATNONE
    else:
        return '%.8f' % fval

def _Fmt02x(ival):
    """Format ival with %02x"""
    if  ival == STATNONE:
        return STATNONE
    else:
        return '%02x' % ival

def _ident(aliasName):
    return ([aliasName], lambda valDict: valDict[aliasName])

def _apply(aliasName, fn):
    return ([aliasName], lambda valDict: fn(valDict[aliasName]))

def _fmt(aliasName, fmt, fn):
    return ([aliasName], lambda valDict: fmt % fn(valDict[aliasName]))

_onoff = { 0x01: 'ON', 0x02: 'OFF' }

def _chooser(aliasName, choiceDict):
    """Meta function to make a chooser deriver.
    """
    def anon(valDict):
        # Check source values
        ret = _validValues([aliasName], valDict)
        if  ret != None:
            return ret

        # Choose derived value from selection according to input
        try:
            val = valDict[aliasName]
            return choiceDict[val]
        except KeyError:
            raise DeriveError("Unknown value for %s (%s)" % (
                aliasName, str(val)))

    return ([aliasName], anon)


def _absval(val):
    """Return absolute value of a numeric value"""
    if  val == STATNONE:
        return STATNONE
    else:
        try:
            ret = abs(val)
            return ret
        except:
            return STATERROR

def _FmtP3fpn(fval_pf, fval_npf, valDict):
    """Choose fval acccording to primeFocus, then format fval with %.3f"""

    primeFocus, nsirFocus = _getFocus(valDict)

    if  primeFocus == STATNONE:
        return STATERROR
    elif  primeFocus:
        fval = fval_pf
    else:
        fval = fval_npf
    if  fval == STATNONE:
        return STATNONE
    else:
        return '%.3f' % fval

def _ApBm1(a, b):
    """Return float a + b - 1, or STATERROR or STATNONE if a or b are those."""
    if  a == STATERROR or b == STATERROR:
        return STATERROR
    if  a == STATNONE or b == STATNONE:
        return STATNONE
    return a + b - 1.0


def _FitsSbrPn(fval_pf, fval_npf, valDict):
    """Choose fval acccording to primeFocus"""

    primeFocus, nsirFocus = _getFocus(valDict)

    if  primeFocus == STATNONE:
        return STATERROR
    elif  primeFocus:
        fval = fval_pf
    else:
        fval = fval_npf
    if  fval == STATNONE:
        return STATNONE
    else:
        return fval

def _getFocus(valDict):
    """Acquire focusInfo and focusInfo2, and compute primeFocus and 
    nsirFocus booleans."""

    focusInfo  = valDict['TSCV.FOCUSINFO']
    focusInfo2 = valDict['TSCV.FOCUSINFO2']
    #? print '  focusInfo  = ', focusInfo
    if  (focusInfo == STATNONE) or (focusInfo  == STATERROR) or \
           (focusInfo2 == STATNONE) or (focusInfo2 == STATERROR):
        primeFocus  = STATNONE
        nsirFocus  = STATNONE

    else:
        if (focusInfo == 0x01000000) or (focusInfo == 0x02000000) or \
               (focusInfo2 == 0x08):
            primeFocus = True

        else:
            primeFocus = False

        if ((focusInfo2 & 0x07) != 0) or ((focusInfo & 0x000C0C18) != 0):
            nsirFocus = True

        else:
            nsirFocus = False

    return (primeFocus, nsirFocus)

# Functions that are derived from on TCS status aliases
def _FitsSbrAirmass(valDict):
    """Compute FITS.SBR.AIRMASS"""
    e = valDict['TSCS.EL']
    if  e == STATNONE:
        return STATNONE
    else:
        d1 = 90.0 - e
        d2 = 1.0 / math.cos(d1/180.0*math.pi)
        d3 = d2 - 1.0
        d0 = d2 - 0.0018167 * d3 - 0.002875 * d3*d3 - 0.0008083 * d3*d3*d3;
        return d0
        #return ('%.3f' % d0)

def _FitsSbrAdc_type(valDict):
    """Compute FITS.SBR.ADC-TYPE"""

    # Following is a Pythonic replacement for a 
    # getStatusBitString() call in OSSL_StatUexec.c
    _ADCInOut = { 0x08 :  'IN',
                  0x10 :  'NONE' }

    primeFocus, nsirFocus = _getFocus(valDict)

    if  primeFocus == STATNONE:
        return STATERROR
    elif  primeFocus:
        return 'IN'
    else:
        a = valDict['TSCV.ADCInOut']
        if  a in _ADCInOut.keys():
            return _ADCInOut[a]
        else:
            return STATERROR
      
def _FitsSbrAutoguid(valDict):
    """Compute FITS.SBR.AUTOGUID"""
    vAgOff = valDict['TSCV.AutoGuideOff']     # binary, mask 0x40
    if  vAgOff == STATNONE:
        return STATNONE
    if  vAgOff == 0:        # AG off
        return "OFF"
#     oAgOn  = valDict['TSCV.SVAutoGuideOn']      # character
#     if  oAgOn == STATNONE:
#         return STATNONE
#     if  oAgOn != 0:         # SV guiding?
#         return "ON"
    vAgOn  = valDict['TSCV.AutoGuideOn']      # binary, mask 0x07
    if  vAgOn == STATNONE:
        return STATNONE
    if  vAgOn == 1 or vAgOn == 2 or vAgOn == 4:     # AG1/AG2/OBE guiding
        return "ON"
    return STATERROR        # invalid

def _FitsSbrAzimuth(valDict):
    """Compute FITS.SBR.AZIMUTH"""
    a = valDict['TSCS.AZ']
    if  a == STATNONE:
        return STATNONE
    else:
        d0 = a + 540.0
        while  d0 > 360.0:
            d0 -= 360.0
        while  d0 < 0.0:
            d0 += 360.0
        return d0
        #return ('%.5f' % d0)

def _dec_encode(d):
    if  d == STATNONE:
        return STATNONE
    else:
        d = ('%010x' % d)
        if  d[0]=='8':
            flag = '-'
        else:
            flag = '+'

        return '%s%s:%s:%s.%s' % (flag, d[2:4], d[4:6], d[6:8], d[8:10]) 

def _FitsSbrDec(valDict):
    """Compute FITS.SBR.DEC"""
    return _dec_encode(valDict['TSCS.DELTA'])

def _FitsSbrDec_Cmd(valDict):
    """Compute FITS.SBR.DEC_CMD"""
    return _dec_encode(valDict['TSCS.DELTA_C'])

def _FitsSbrDom_tmp(valDict):
    """Compute FITS.SBR.DOM-TMP"""
    t = valDict['TSCL.TEMP_I']
    if  t == STATNONE:
        return STATNONE
    else:
        return t+273.15

def _FitsSbrOut_tmp(valDict):
    """Compute FITS.SBR.OUT-TMP"""
    t = valDict['TSCL.TEMP_O']
    if  t == STATNONE:
        return STATNONE
    else:
        return t+273.15

def _ra_encode(d):
    # depends on funky encoding
    if  (d == STATNONE) or (d == STATERROR):
        return d
    else:
        d = ('%010x' % d)
        #return '%s:%s:%s.%s' % (d[3:5], d[5:7], d[7:9], d[9:12]) 
        return '%s:%s:%s.%s' % (d[0:2], d[2:4], d[4:6], d[6:9]) 

def _FitsSbrRa(valDict):
    """Compute FITS.SBR.RA"""
    return _ra_encode(valDict['TSCS.ALPHA'])

def _FitsSbrRa_Cmd(valDict):
    """Compute FITS.SBR.RA_CMD"""
    return _ra_encode(valDict['TSCS.ALPHA_C'])

def _FitsSbrEpoch(valDict):
    """Compute FITS.SBR.EPOCH"""
    return time.time()

def _FitsSbrLST(valDict):
    """Compute FITS.SBR.LST"""
    t_sec = valDict['FITS.SBR.EPOCH']
    ut1_utc = valDict['FITS.SBR.UT1-UTC']
    return wcs.calcLST(t_sec, ut1_utc)

def _FitsSbrHA(valDict):
    """Compute FITS.SBR.HA"""
    t_sec = valDict['FITS.SBR.EPOCH']
    ut1_utc = valDict['FITS.SBR.UT1-UTC']
    lst_sec = wcs.calcLST_sec(t_sec, ut1_utc)

    ra = valDict['STATS.RA']
    ra_deg = radec.funkyHMStoDeg(ra)
    ha_sec = wcs.calcHA_sec(lst_sec, ra_deg)
    ha_abs = math.fabs(ha_sec)
    ha_hrs = ha_abs // 3600
    ha_abs -= ha_hrs
    ha_min = ha_abs // 60
    ha_sec = ha_abs - ha_min
    c = '+'
    if ha_sec < 0.0:
        c = '-'
    ha = '%s%02d:%02d:%06.3f' % (c, ha_hrs, ha_min, ha_sec)
    return ha

def _FitsSbrHST(valDict):
    """Compute FITS.SBR.HST"""
    t_sec = valDict['FITS.SBR.EPOCH']
    return wcs.calcHST(t_sec)

def _FitsSbrUT(valDict):
    """Compute FITS.SBR.UT"""
    t_sec = valDict['FITS.SBR.EPOCH']
    return wcs.calcUT(t_sec)

def _FitsSbrRaDec2000(valDict):
    # Helper function for _FitsSbrRa2000 and _FitsSbrDec2000. This
    # function converts the RA/Dec coordinates in valDict, i.e.,
    # valDict['TSCS.ALPHA'] and valDict['TSCS.DELTA'], from the
    # specified equinox (valDict['TSCS.EQUINOX']) to the 2000.0
    # equinox. Note that this is valid only for input coordinates that
    # are in the Julian epoch, e.g., JXXXX.X. This function *does not*
    # convert from a Besselian epoch, e.g, B1950, to a Julian epoch,
    # e.g., J2000.
    ra = _FitsSbrRa(valDict)
    if  (ra == STATNONE) or (ra == STATERROR):
        return ra, ra
    dec = _FitsSbrDec(valDict)
    if  (dec == STATNONE) or (dec == STATERROR):
        return dec, dec
    equinox = _StatsFitsSbrEquinox(valDict)
    if  (equinox == STATNONE) or (equinox == STATERROR):
        return equinox, equinox
    ra_deg = wcs.hmsToDeg(ra)
    dec_deg = wcs.dmsToDeg(dec)
    return wcs.eq2000(ra_deg, dec_deg, equinox)

def _FitsSbrRa2000(valDict):
    """Compute FITS.SBR.RA2000"""
    (ra2000, dec2000) = _FitsSbrRaDec2000(valDict)
    return ra2000

def _FitsSbrDec2000(valDict):
    """Compute FITS.SBR.DEC2000"""
    (ra2000, dec2000) = _FitsSbrRaDec2000(valDict)
    return dec2000

def _FitsSbrSecz(valDict):
    """Compute FITS.SBR.SECZ"""
    e = valDict['TSCS.EL']
    if  e == STATNONE:
        return STATNONE
    else:
        d1 = 90.0 - e
        d0 = 1.0 / math.cos(d1/180.0*math.pi)
        return ('%.3f' % d0)

# Following is a Pythonic replacement for a 
# getStatusBitString() call in OSSL_StatUexec.c
_Telfocus = { 0x01000000 :  'Prime',
              0x02000000 :  'Prime',
              0x04000000 :  'Cassegrain',
              0x08000000 :  'Cassegrain',
              0x10000000 :  'Nasmyth-OPT',
              0x20000000 :  'Nasmyth-OPT',
              0x40000000 :  'Nasmyth-OPT',
              0x80000000 :  'Nasmyth-OPT',
              0x00010000 :  'Nasmyth-OPT',
              0x00020000 :  'Nasmyth-OPT',
              0x00040000 :  'Nasmyth-IR',
              0x00080000 :  'Nasmyth-IR',
              0x00100000 :  'Nasmyth-OPT',
              0x00200000 :  'Nasmyth-OPT',
              0x00400000 :  'Nasmyth-OPT',
              0x00800000 :  'Nasmyth-OPT',
              0x00000100 :  'Nasmyth-OPT',
              0x00000200 :  'Nasmyth-OPT',
              0x00000400 :  'Nasmyth-IR',
              0x00000800 :  'Nasmyth-IR',
              0x00001000 :  'Cassegrain',
              0x00002000 :  'Nasmyth-OPT',
              0x00004000 :  'Nasmyth-OPT',
              0x00008000 :  'Nasmyth-OPT',
              0x00000001 :  'Nasmyth-OPT',
              0x00000002 :  'Nasmyth-OPT',
              0x00000004 :  'Nasmyth-OPT',
              0x00000008 :  'Nasmyth-IR',
              0x00000010 :  'Nasmyth-IR' }
_Telfocus2 ={ 0x01       :  'Nasmyth-IR',
              0x02       :  'Nasmyth-IR',
              0x04       :  'Nasmyth-IR',
              0x08       :  'Prime'      }

def _FitsSbrTelfocus(valDict):
    """Compute FITS.SBR.TELFOCUS"""

    ret = _validValues(('TSCV.FOCUSINFO','TSCV.FOCUSINFO2'), valDict)
    if  ret != None:
        return ret

    a = valDict['TSCV.FOCUSINFO']
    b = valDict['TSCV.FOCUSINFO2']

    if  a in _Telfocus.keys():
        return _Telfocus[a]

    elif  b in _Telfocus2.keys():
        return _Telfocus2[b]

    else:
        return STATERROR
      
def _FitsSbrImr_type(valDict):
    """Compute FITS.SBR.IMR-TYPE"""
    #? print '_FitsSbrImr_type:'
    focusInfo  = valDict['TSCV.FOCUSINFO']

    if  focusInfo in _Telfocus.keys():
        tf = _Telfocus[focusInfo]
    else:
        tf = None
    if  tf == 'Nasmyth-IR':
        d = valDict['TSCV.ImgRotType_NS_IR']
        if  d == 0x08:
            return 'RED'
        elif  d == 0x10:
            return 'NONE'
        else:
            return STATERROR
    else:
        d = valDict['TSCV.ImgRotType']
        if  d == 0x12:
            return 'BLUE'
        elif  d == 0x0C:
            return 'RED'
        elif  d == 0x14:
            return 'NONE'
        else:
            return STATERROR

def _FitsSbrZd(valDict):
    """Compute FITS.SBR.ZD"""
    e = valDict['TSCS.EL']
    if  e == STATNONE:
        return STATNONE

    else:
        return (90.0-e)
        #return ('%.5f' % (90.0-e))

def _validValues(keys, valDict):
    """Utility function to make sure there are no STATNONE or STATERROR 
    values for these keys in the status."""
    ret = None
    for  key in keys:
        try:
            val = valDict[key]
            #? print '_validValues: valDict[%s] = %s' % (key, `val`)

        except KeyError:
            val = STATNONE
            #? print '_validValues: KeyError'

        if (ret == None) and (val == STATNONE):
            #? print '_validValues: STATNONE'
            ret = STATNONE

        if (val == STATERROR):
            #? print '_validValues: STATERROR'
            ret = STATERROR
            break
        
    return ret

def _StatsRa(valDict):
    """Compute STATS.RA"""
    d = valDict['TSCS.ALPHA']    # depends on funky encoding
    #? print '_StatsRa: TSCS.ALPHA = "%s"' % d
    if  (d == STATNONE) or (d == STATERROR):
        return d
    else:
        #return '%s.%s' % (d[3:9], d[9:12])
        d = ('%010x' % d)
        return '%s.%s' % (d[0:6], d[6:9])

def _StatsDec(valDict):
    """Compute STATS.DEC"""
    d = valDict['TSCS.DELTA']    # depends on funky encoding
    #? print '_StatsDec: TSCS.DELTA = "%s"' % d
    if  (d == STATNONE) or (d == STATERROR):
        return d
    else:
        d = ('%010x' % d)
        if  d[0]=='8':
            c = '-'
        else:
            c = '+'
        #return '%s%s.%s' % (c, d[5:11], d[11:13])
        return '%s%s.%s' % (c, d[2:8], d[8:10])

def _OnOff(val):
    """Choose a On/Off string based on _OnOffDict"""

    # Following is a Pythonic replacement for a 
    # getStatusBitString() call in OSSL_StatSexec.c
    # Several functions use this On/Off dictionary.
    _OnOffDict = { 0x01 :  'ON',
                   0x02 :  'OFF' }

    if  val == STATNONE or val == STATERROR:
        return val
    elif  val in _OnOffDict.keys():
        return _OnOffDict[val]
    else:
        return STATERROR


def _StatsFitsSbrEquinox(valDict):
    """Compute STATS.EQUINOX or FITS.SBR.EQUINOX"""
    e = valDict['TSCS.EQUINOX']
    if  e == STATNONE:
        return STATNONE
    else:
        #return '%8.3f' % (e*10000.0)
        return e*10000.0

def _Stats_Rotdif(valDict):
    """Compute STATS.ROTDIF"""
    # Make sure that both constituents are defined
    ret = _validValues(('TSCS.ROTCMD','TSCS.ROTPOS'), valDict)
    if  ret != None:
        return ret
    return '%.6f' % abs(valDict['TSCS.ROTCMD'] - valDict['TSCS.ROTPOS'])

def _Stats_Rotdif_PF(valDict):
    """Compute STATS.ROTDIF_PF"""
    # Make sure that both constituents are defined
    ret = _validValues(('TSCS.INSROTCMD_PF','TSCS.INSROTPOS_PF'), valDict)
    if  ret != None:
        return ret
    return '%.6f' % abs(valDict['TSCS.INSROTCMD_PF'] - valDict['TSCS.INSROTPOS_PF'])

def _StatlAdc_F_Select(valDict):
    """Compute STATL.ADC_F_SELECT"""
    # Make sure that all constituents are defined
    ret = _validValues(('TSCV.ADCType','TSCV.FOCUSINFO','TSCV.FOCUSINFO2','STATL.TSC_F_SELECT'), valDict)
    if  ret != None:
        return ret

    adcType = valDict['TSCV.ADCType']
    primeFocus, nsirFocus = _getFocus(valDict)
    tscFSelect = valDict['STATL.TSC_F_SELECT']

    # According to Tomono-san (1 June 2012), TSCV.ADCType will be
    # accurate only for non-prime-focus foci. Therefore, for
    # prime-focus, we will set STATL.ADC_F_SELECT to have the same
    # value as STATL.TSC_F_SELECT. For other foci, use TSCV.ADCType to
    # determine how to set STATL.ADC_F_SELECT.
    if primeFocus:
        return tscFSelect
    else:
        if adcType == 0x04:
            return 'CS'
        elif adcType == 0x08:
            return 'NS_OPT'
        else:
            return STATERROR

def _StatlAgrErr(valDict):
    """Compute STATL.AGRERR"""

    focusInfo  = valDict['TSCV.FOCUSINFO']
    focusInfo2  = valDict['TSCV.FOCUSINFO2']
    
    if  focusInfo == 0x02000000:        # P_IR
        ret = _validValues(('TSCV.TelDrive',
                            'TSCV.AGPIRCCalc', 'TSCV.AGFMOSCCalc'), valDict)
        if  ret != None:
            return ret
        agPirCalc  = valDict['TSCV.AGPIRCCalc']
        agFmosCalc = valDict['TSCV.AGFMOSCCalc']
        if  agPirCalc == 0x04 and agFmosCalc == 0x04:
            vTeldrive = valDict['TSCV.TelDrive']
            if  vTeldrive == 0x0004:
                ret = _validValues(('TSCL.AGPIRdX','TSCL.AGPIRdY'), valDict)
                if  ret != None:
                    return ret
                agPirDx = valDict['TSCL.AGPIRdX']
                agPirDy = valDict['TSCL.AGPIRdY']
                dw = math.sqrt(agPirDx*agPirDx + agPirDy*agPirDy)
            else:
                ret = _validValues(('TSCL.AGFMOSdAZ','TSCL.AGFMOSdEL'), valDict)
                if  ret != None:
                    return ret
                agFmosDx = valDict['TSCL.AGFMOSdAZ']
                agFmosDy = valDict['TSCL.AGFMOSdEL']
                dw = math.sqrt(agFmosDx*agFmosDx + agFmosDy*agFmosDy) * 1000.0
        else:
            if  agPirCalc == 0x04:
                ret = _validValues(('TSCL.AGPIRdX','TSCL.AGPIRdY'), valDict)
                if  ret != None:
                    return ret
                agPirDx = valDict['TSCL.AGPIRdX']
                agPirDy = valDict['TSCL.AGPIRdY']
                dw = math.sqrt(agPirDx*agPirDx + agPirDy*agPirDy)
            else:
                ret = _validValues(('TSCL.AGFMOSdAZ','TSCL.AGFMOSdEL'), valDict)
                if  ret != None:
                    return ret
                agFmosDx = valDict['TSCL.AGFMOSdAZ']
                agFmosDy = valDict['TSCL.AGFMOSdEL']
                dw = math.sqrt(agFmosDx*agFmosDx + agFmosDy*agFmosDy) * 1000.0
    elif focusInfo2 == 0x08:        # P_OPT2 (HSC)
        ret = _validValues(('TSCV.TelDrive',
                            'TSCV.HSC.SCAG.CCalc', 'TSCV.HSC.SHAG.CCalc'), valDict)
        if  ret != None:
            return ret
        agSCCalc  = valDict['TSCV.HSC.SCAG.CCalc']
        agSHCalc = valDict['TSCV.HSC.SHAG.CCalc']
        if  agSCCalc == 0x04 and agSHCalc == 0x04:
            vTeldrive = valDict['TSCV.TelDrive']
            if  vTeldrive == 0x0010:
                ret = _validValues(('TSCL.HSC.SCAG.DX','TSCL.HSC.SCAG.DY'), valDict)
                if  ret != None:
                    return ret
                agSCDx = valDict['TSCL.HSC.SCAG.DX']
                agSCDy = valDict['TSCL.HSC.SCAG.DY']
                dw = math.sqrt(agSCDx*agSCDx + agSCDy*agSCDy)
            else:
                ret = _validValues(('TSCL.HSC.SHAG.DX','TSCL.HSC.SHAG.DX'), valDict)
                if  ret != None:
                    return ret
                agSHDx = valDict['TSCL.HSC.SHAG.DX']
                agSHDy = valDict['TSCL.HSC.SHAG.DY']
                dw = math.sqrt(agSHDx*agSHDx + agSHDy*agSHDy)
        else:
            if agSCCalc == 0x04:
                ret = _validValues(('TSCL.HSC.SCAG.DX','TSCL.HSC.SCAG.DY'), valDict)
                if  ret != None:
                    return ret
                agSCDx = valDict['TSCL.HSC.SCAG.DX']
                agSCDy = valDict['TSCL.HSC.SCAG.DY']
                dw = math.sqrt(agSCDx*agSCDx + agSCDy*agSCDy)
            else:
                ret = _validValues(('TSCL.HSC.SHAG.DX','TSCL.HSC.SHAG.DY'), valDict)
                if  ret != None:
                    return ret
                agSHDx = valDict['TSCL.HSC.SHAG.DX']
                agSHDy = valDict['TSCL.HSC.SHAG.DX']
                dw = math.sqrt(agSHDx*agSHDx + agSHDy*agSHDy)
    else:
        ret = _validValues(('TSCL.AG1dX','TSCL.AG1dY'), valDict)
        if  ret != None:
            return ret
        agDx = valDict['TSCL.AG1dX']
        agDy = valDict['TSCL.AG1dY']
        dw = math.sqrt(agDx*agDx + agDy*agDy)

    return dw


def _StatlSvrErr(valDict):
    """Compute STATL.SVRERR"""

    # Make sure that all constituents are defined
    ret = _validValues(('TSCL.SV1DX','TSCL.SV1DY'), valDict)
    if  ret != None:
        return ret

    # Find STATL.SVRERR
    sv1dx = valDict['TSCL.SV1DX']
    sv1dy = valDict['TSCL.SV1DY']
    if  sv1dx == STATERROR or sv1dy == STATERROR:
        return STATERROR
    if  sv1dx == STATNONE or sv1dy == STATNONE:
        return STATNONE

    return math.sqrt(sv1dx*sv1dx + sv1dy*sv1dy)


def _StatlAgX1(val):
    """Format and save STATL.AG1_X1, STATL.AG2_X1 or STATL.AG_X1;
                  also STATL.AG1_Y1, STATL.AG2_Y1 or STATL.AG_Y1"""

    if  val == STATNONE:
        return STATNONE
    else:
        try:
            x1 = int(math.floor(val))
            return '%d' % x1
        except:
            return STATERROR        # not a float, or other exception

def _StatlAgX2(val1, val2):
    """Compute and format STATL.AG1_X2, STATL.AG2_X2 or STATL.AG_X2;
                     also STATL.AG1_Y2, STATL.AG2_Y2 or STATL.AG_Y2"""

    if  val1 == STATNONE or val2 == STATNONE:
        return STATNONE
    else:
        try:
            x1 = int(math.floor(val1))
            dx = int(math.floor(val2))
            return '%d' % (x1 + dx - 1)
        except:
            return STATERROR        # not a float, or other exception


def _StatlAgShutter(valDict):
    """Compute STATL.AG_SHUTTER"""
    _AgShutter = { 0x01 :  'OPEN',
                   0x02 :  'CLOSE'}

    ret = _validValues(('TSCV.AGShutter',), valDict)
    if  ret != None:
        return ret
    a = valDict['TSCV.AGShutter']
    if  a in _AgShutter.keys():
        return _AgShutter[a]
    else:
        return STATERROR

def _Statl_Irot_Telescope(valDict):
    """Compute STATL.IROT_TELESCOPE or FITS.VGW.IROT_TELESCOPE"""
    _IrotTelescope = { 0x01 :  'LINK',
                       0x02 :  'FREE' }

    ret = _validValues(('TSCV.InsRotMode',), valDict)
    a = valDict['TSCV.InsRotMode']
    if  ret != None:
        return ret
    if  a in _IrotTelescope.keys():
        return _IrotTelescope[a]
    else:
        return STATERROR

def _Statl_IrotPf_Telescope(valDict):
    """Compute STATL.IROTPF_TELESCOPE"""
    _IrotPfTelescope = { 0x10 :  'LINK',
                         0x20 :  'FREE' }

    ret = _validValues(('TSCV.INSROTMODE_PF',), valDict)
    a = valDict['TSCV.INSROTMODE_PF']
    if  ret != None:
        return ret
    if  a in _IrotPfTelescope.keys():
        return _IrotPfTelescope[a]
    else:
        return STATERROR


def _Statl_Irot_Type(valDict):
    """Compute STATL.IROT_TYPE"""

    # Following is a Pythonic replacement for a 
    # getStatusBitString() call in OSSL_StatLexec.c
    _Irot_Type = { 
                 0x12       : 'BLUE',
                 0x0C       : 'RED',
                 0x14       : 'NONE' }
    _Irot_Type_Nsir = { 
                 0x08       : 'RED',
                 0x10       : 'NONE' }

    primeFocus, nsirFocus = _getFocus(valDict)

    if  nsirFocus == STATNONE:
        return STATERROR
    if  nsirFocus:
        a = valDict['TSCV.ImgRotType_NS_IR']
        if  a in _Irot_Type_Nsir.keys():
            return _Irot_Type_Nsir[a]
        else:
            return STATERROR
    else:
        a = valDict['TSCV.ImgRotType']
        if  a in _Irot_Type.keys():
            return _Irot_Type[a]
        else:
            return STATERROR


_Sv_Calc_Mode = { 0x01 :  'CTR',
                  0x02 :  'BSECT',
                  0x04 :  'PK',
                  0x08 :  'SLIT' }

def _Statl_Calc_Mode(valDict):
    """Compute STATL.CALC_MODE -- use same table as for STATL.SV_CALC_MODE."""

    ret = _validValues(('TSCV.AGCCalcMode',), valDict)
    a = valDict['TSCV.AGCCalcMode']
    if  ret != None:
        return ret
    if  a in _Sv_Calc_Mode.keys():
        return _Sv_Calc_Mode[a]
    else:
        return STATERROR

def _Statl_Sv_Calc_Mode(valDict):
    """Compute STATL.SV_CALC_MODE -- use same table as for STATL.CALC_MODE."""

    ret = _validValues(('TSCV.SVCCalcMode',), valDict)
    a = valDict['TSCV.SVCCalcMode']
    if  ret != None:
        return ret
    if  a in _Sv_Calc_Mode.keys():
        return _Sv_Calc_Mode[a]
    else:
        return STATERROR

def _Statl_Calc_Region(valDict):
    """Compute STATL.CALC_REGION"""

    # Following is a Pythonic replacement for a 
    # getStatusBitString() call in OSSL_StatLexec.c
    _Calc_Region = { 0x00:   '',
                     0x04 :  '1',
                     0x10 :  '2',
                     0x14 :  '1'  }

    ret = _validValues(('TSCV.AGCCalc',), valDict)
    a = valDict['TSCV.AGCCalc']
    if  ret != None:
        return ret
    if  a in _Calc_Region.keys():
        return _Calc_Region[a]
    else:
        return STATERROR

def _Statl_Sv_Calc_Region(valDict):
    """Compute STATL.SV_CALC_REGION"""

    # Following is a Pythonic replacement for a 
    # getStatusBitString() call in OSSL_StatLexec.c
    _Calc_Region = { 0x00 :  '',
                     0x04 :  '1',
                     0x10 :  '2',
                     0x14 :  '1'  }

    ret = _validValues(('TSCV.SVCCalc',), valDict)
    a = valDict['TSCV.SVCCalc']
    if  ret != None:
        return ret
    if  a in _Calc_Region.keys():
        return _Calc_Region[a]
    else:
        return STATERROR

def _StatL_PIR_Calc_Region(valDict):
    """Compute STATL.PIR_CALC_REGION"""

    ret = _validValues(('TSCV.AGPIRCCalc', 'TSCV.AGFMOSCCalc'), valDict)
    if  ret != None:
        return ret
    v1 = valDict['TSCV.AGPIRCCalc']
    v2 = valDict['TSCV.AGFMOSCCalc']

    if (v1 == 0x04) and (v2 == 0x04):
        return "PIR"
    
    if (v1 == 0x02): return "PIR"
    if (v2 == 0x02): return "FMOS"
    return STATNONE

def _Statl_D_Type(valDict):
    """Compute STATL.D_TYPE -- a string corresponding to the first one
       of the 4 TSCV status values which is '04'."""
    objVal  = valDict['TSCV.AG_DT_OBJ']
    skyVal  = valDict['TSCV.AG_DT_SKY']
    flatVal = valDict['TSCV.AG_DT_FLAT']
    darkVal = valDict['TSCV.AG_DT_DARK']
    if  objVal == 4:
        return 'OBJ'
    elif  skyVal == 4:
        return 'SKY'
    elif  flatVal == 4:
        return 'FLAT'
    elif  darkVal == 4:
        return 'DARK'
    else:
        return STATNONE


def _Statl_WindsDif(valDict):
    """Compute STATL.WINDSDIF"""
    # Make sure that both constituents are defined
    ret = _validValues(('TSCL.WINDSCMD', 'TSCL.WINDSPOS'), valDict)
    if  ret != None:
        return ret
    return abs(valDict['TSCL.WINDSCMD'] - valDict['TSCL.WINDSPOS'])

def _Statl_WindsDif_Sign(valDict):
    """Compute STATL.WINDSDIF_SIGN"""
    # Make sure that both constituents are defined
    ret = _validValues(('TSCL.WINDSCMD', 'TSCL.WINDSPOS'), valDict)
    if  ret != None:
        return ret
    return (valDict['TSCL.WINDSCMD'] - valDict['TSCL.WINDSPOS'])

def _Statl_ZDif(valDict):
    """Compute STATL.ZDIF"""
    # Make sure that both constituents are defined
    ret = _validValues(('TSCL.ZCMD','TSCL.ZPOS'), valDict)
    if  ret != None:
        return ret
    return abs(valDict['TSCL.ZCMD'] - valDict['TSCL.ZPOS'])

def _Stats_Az_Adj(valDict):
    """Compute STATS.AZ_ADJ"""
    ret = _validValues(('TSCS.AZ',), valDict)
    if  ret != None:
        return ret
    # Mitsubishi measures S=0 deg
    az_deg = float(valDict['TSCS.AZ']) + 180.0
    if math.fabs(az_deg) >= 360.0:
        az_deg = math.fmod(az_deg, 360.0)
    if az_deg < 0.0:
        az_deg += 360.0
    return az_deg

def _Statl_Zernike_RMS(sourceAlias, valDict):
    """Compute STATL.ZERNIKE_RMS and STATL.ZERNIKE_WOA20"""
    #ret = _validValues((sourceAlias,), valDict)
    #if  ret != None:
    #    return ret

    val_str = valDict[sourceAlias]
    if ('\x00' in val_str) or (len(val_str) < 8):
        # ?? This agrees with C SOSS source code
        val_flt = 0.0
    else:
        # convert to double float and byteswap the value
        val_a = array.array('d', val_str)
        val_a.byteswap()
        val_flt = val_a[0]

    val = ('%10.8f' % val_flt)
    
    # SOSS defines these in a 32 char left adjusted field.  Is it necessary
    # in Gen2?  Probably not.
    #val = ('%-32s' % val)
    return val


def _StatlTeldrive_common(valDict):
    """Helper function for STATL.TELDRIVE and STATL.TELDRIVE_INFO"""

    # Make sure that all constituents are defined
    ret = _validValues(('TSCV.TelDrive','TSCV.AutoGuideOn'), valDict)
    if  ret != None:
        info = "WARNING"
        return (ret, info)

    # Find STATL.TELDRIVE and STATL.TELDRIVE_INFO
    vTeldrive = valDict['TSCV.TelDrive']
    if  vTeldrive == 0x4000:        # AG autoguiding modes
        agon    = valDict['TSCV.AutoGuideOn']
        if  agon == 0x01:
            ret = _validValues(('TSCL.AG1Intensity',), valDict)
            if  ret != None:
                info = "WARNING"
                return (ret, info)
            dag1i   = valDict['TSCL.AG1Intensity']
            if  dag1i < 1.0:
                info = "ALARM"
            else:
                STATL_AGRERR = valDict['STATL.AGRERR']
                if (STATL_AGRERR == STATNONE) or (STATL_AGRERR == STATERROR):
                    info = "WARNING"
                    return (STATL_AGRERR, info)
                if  STATL_AGRERR > 500:
                    info = "WARNING"
                else:
                    info = "NORMAL"
            return ("Guiding(AG1)", info)
        
        elif  agon == 0x02:
            ret = _validValues(('TSCL.AG2Intensity',), valDict)
            if  ret != None:
                info = "WARNING"
                return (ret, info)
            dag2i   = valDict['TSCL.AG2Intensity']
            if  dag2i < 1.0:
                info = "ALARM"
            else:
                info = "NORMAL"
            return ("Guiding(AG2)", info)
        else:
            info = "WARNING"
            return ("Unknown", info)

    elif  vTeldrive == 0x8000:        # SV autoguiding modes
        svon    = valDict['TSCV.SVAutoGuideOn']
        if  svon == 0x01:
            ret = _validValues(('TSCL.SV1Intensity',), valDict)
            if  ret != None:
                info = "WARNING"
                return (ret, info)
            dsv1i   = valDict['TSCL.SV1Intensity']
            if  dsv1i < 1.0:
                info = "ALARM"
            else:
                STATL_SVRERR = valDict['STATL.SVRERR']
                if (STATL_SVRERR == STATNONE) or (STATL_SVRERR == STATERROR):
                    info = "WARNING"
                    return (STATL_SVRERR, info)
                if  STATL_SVRERR > 500:
                    info = "WARNING"
                else:
                    info = "NORMAL"
            return ("Guiding(SV1)", info)
        
        elif  svon == 0x02:
            ret = _validValues(('TSCL.SV2Intensity',), valDict)
            if  ret != None:
                info = "WARNING"
                return (ret, info)
            dsv2i   = valDict['TSCL.SV2Intensity']
            if  dsv2i < 1.0:
                info = "ALARM"
            else:
                info = "NORMAL"
            return ("Guiding(SV2)", info)
        else:
            info = "WARNING"
            return ("Unknown", info)

    elif  vTeldrive == 0x0004:        # AG PIR autoguiding mode
        ret = _validValues(('TSCL.AGPIRIntensity',), valDict)
        if  ret != None:
            info = "WARNING"
            return (ret, info)
        dpiri   = valDict['TSCL.AGPIRIntensity']
        if  dpiri < 1.0:
            info = "ALARM"
        else:
            STATL_AGRERR = valDict['STATL.AGRERR']
            if (STATL_AGRERR == STATNONE) or (STATL_AGRERR == STATERROR):
                info = "WARNING"
                return (STATL_AGRERR, info)
            if  STATL_AGRERR > 500:
                info = "WARNING"
            else:
                info = "NORMAL"
        return ("Guiding(AGPIR)", info)

    elif  vTeldrive == 0x0008:        # AG FMOS autoguiding mode
        ret = _validValues(('TSCL.AGFMOSIntensity',), valDict)
        if  ret != None:
            info = "WARNING"
            return (ret, info)
        dfmosi  = valDict['TSCL.AGFMOSIntensity']
        if  dfmosi < 1.0:
            info = "ALARM"
        else:
            STATL_AGRERR = valDict['STATL.AGRERR']
            if (STATL_AGRERR == STATNONE) or (STATL_AGRERR == STATERROR):
                info = "WARNING"
                return (STATL_AGRERR, info)
            if  STATL_AGRERR > 500:
                info = "WARNING"
            else:
                info = "NORMAL"
        return ("Guiding(AGFMOS)", info)

    elif  vTeldrive == 0x0010:        # AG for SC HSC autoguiding mode
        ret = _validValues(('TSCL.HSC.SCAG.Intensity',), valDict)
        if  ret != None:
            print 'ret not equal to None'
            info = "WARNING"
            return (ret, info)
        dhsci  = valDict['TSCL.HSC.SCAG.Intensity']
        if  dhsci < 1.0:
            info = "ALARM"
        else:
            STATL_AGRERR = valDict['STATL.AGRERR']
            if (STATL_AGRERR == STATNONE) or (STATL_AGRERR == STATERROR):
                info = "WARNING"
                return (STATL_AGRERR, info)
            if  STATL_AGRERR > 500:
                info = "WARNING"
            else:
                info = "NORMAL"
        return ("Guiding(HSCSCAG)", info)

    elif  vTeldrive == 0x0020:        # AG for SH HSC autoguiding mode
        ret = _validValues(('TSCL.HSC.SHAG.Intensity',), valDict)
        if  ret != None:
            info = "WARNING"
            return (ret, info)
        dhsci  = valDict['TSCL.HSC.SHAG.Intensity']
        if  dhsci < 1.0:
            info = "ALARM"
        else:
            STATL_AGRERR = valDict['STATL.AGRERR']
            if (STATL_AGRERR == STATNONE) or (STATL_AGRERR == STATERROR):
                info = "WARNING"
                return (STATL_AGRERR, info)
            if  STATL_AGRERR > 500:
                info = "WARNING"
            else:
                info = "NORMAL"
        return ("Guiding(HSCSHAG)", info)

    elif  vTeldrive == 0x2000:        # Tracking modes
        ret = _validValues(('TSCS.AZDIF','TSCS.ELDIF','TSCV.TRACKING'),
                           valDict)
        if  ret != None:
            info = "WARNING"
            return (ret, info)
        azdif = valDict['TSCS.AZDIF']
        eldif = valDict['TSCS.ELDIF']
        if  azdif == STATNONE or azdif == STATERROR or    \
            eldif == STATNONE or eldif == STATERROR:
            info = "WARNING"
            return ("Unknown", info)
        ddiff = abs(azdif) + abs(eldif)
        if  ddiff > 0.25:
            info = "WARNING"
            return ("Slewing", info)
        else:
            tracking = valDict['TSCV.TRACKING']
            if  tracking == 0x04:
                info = "NORMAL"
                return ("Tracking", info)
            elif  tracking == 0x08:
                info = "ALARM"
                return ("Tracking(Non-Sidereal)", info)
            elif  tracking == 0x10:
                info = "NORMAL"
                return ("Tracking(Non-Sidereal)", info)
            elif  tracking == 0x20:
                info = "ALARM"
                return ("Tracking(Non-Sidereal)", info)
            else:
                info = "WARNING"
                return ("Unknown", info)

    elif  vTeldrive == 0x1000:        # Pointing mode
        info = "NORMAL"
        return ("Pointing", info)

    info = "WARNING"
    return ("Unknown", info)


def _StatlTeldrive(valDict):
    """Compute STATL.TELDRIVE"""
    (teldrive, teldrive_info) = _StatlTeldrive_common(valDict)
    return teldrive


def _StatlTeldriveInfo(valDict):
    """Compute STATL.TELDRIVE_INFO"""

    (teldrive, teldrive_info) = _StatlTeldrive_common(valDict)

    if teldrive_info == STATNONE:
        return "Unknown"
    if  teldrive_info == STATERROR:
        return STATERROR

    return teldrive_info


def _StatlTsc_F_Select(valDict):
    """Compute STATL.TSC_F_SELECT"""

    # Following is a Pythonic replacement for a 
    # getStatusBitString() call in OSSL_StatUexec.c
    _fSelect = { 
                 0x01000000 : 'P_OPT',
                 0x02000000 : 'P_IR',
                 0x04000000 : 'CS_OPT',
                 0x08000000 : 'CS_OPT',
                 0x10000000 : 'NS_OPT',
                 0x20000000 : 'NS_OPT',
                 0x40000000 : 'NS_OPT',
                 0x80000000 : 'NS_OPT',
                 0x00010000 : 'NS_OPT',
                 0x00020000 : 'NS_OPT',
                 0x00040000 : 'NS_IR',
                 0x00080000 : 'NS_IR',
                 0x00100000 : 'NS_OPT',
                 0x00200000 : 'NS_OPT',
                 0x00400000 : 'NS_OPT',
                 0x00800000 : 'NS_OPT',
                 0x00000100 : 'NS_OPT',
                 0x00000200 : 'NS_OPT',
                 0x00000400 : 'NS_IR',
                 0x00000800 : 'NS_IR',
                 0x00001000 : 'CS_IR',
                 0x00002000 : 'NS_OPT',
                 0x00004000 : 'NS_OPT',
                 0x00008000 : 'NS_OPT',
                 0x00000001 : 'NS_OPT',
                 0x00000002 : 'NS_OPT',
                 0x00000004 : 'NS_OPT',
                 0x00000008 : 'NS_IR',
                 0x00000010 : 'NS_IR' }
    _fSelect2 = { 
                 0x01       : 'NS_IR',
                 0x02       : 'NS_IR',
                 0x04       : 'NS_IR',
                 0x08       : 'P_OPT2' }

    ret = _validValues(('TSCV.FOCUSINFO','TSCV.FOCUSINFO2'), valDict)
    if  ret != None:
        return ret

    focusCode  = valDict['TSCV.FOCUSINFO']
    focusCode2 = valDict['TSCV.FOCUSINFO2']
    if  focusCode in _fSelect.keys():
        return _fSelect[focusCode]

    elif  focusCode2 in _fSelect2.keys():
        return _fSelect2[focusCode2]

    else:
        return STATERROR

def _Statl_Tt_Mode(valDict):
    """Compute STATL.TT_MODE"""

    _ttMode = { 
                 0x00       : 'OFF',
                 0x01       : 'CHOPPING',
                 0x02       : 'TIPTILT',
                 0x04       : 'POSN' }

    modeCode = valDict['TSCV.M2TipTilt']
    if  modeCode in _ttMode.keys():
        return _ttMode[modeCode]
    else:
        return STATERROR

def _calc_tsc_logins(valDict):
    """Used to calculate GEN2.TSCLOGINS, GEN2.OCSLOGIN and GEN2.OBSLOGIN"""
    res = []
    for alias in [ 'TSCV.TSC.LOGIN%d' % n for n in xrange(10) ]:
        val = valDict[alias].strip()
        if len(val) > 0:
            res.append(val)

    return res

def _calc_tsc_mode(valDict):
    """Used to calculate GEN2.TSCMODE"""
    val = int(valDict['TSCL.MODE'])
    if val == 1:
        return 'OBS'
    else:
        return 'TSC'

def _calc_dew_point_outside(valDict):
    """ calcaute STATL.DEW_POINT_O """

    temp = valDict['TSCL.TEMP_O']
    hum =  valDict['TSCL.HUMI_O']
    a = 17.27
    b = 237.7

    try:
        gamma = ((a * temp) / (b + temp)) + math.log(float(hum) / 100.0)
        dew_point = (b * gamma) / (a - gamma)
    except Exception as e:
        dew_point = None
    return dew_point

def _maskBits(aliasName, mask, valDict):
    """
    Apply bit-mask to specified status alias. If result of applying
    bit-mask evaluates to True, return 1. Otherwise, return 0.
    """
    ret = _validValues([aliasName], valDict)
    if  ret != None:
        return ret

    if valDict[aliasName] & mask:
        return 1
    else:
        return 0
    

# Functions that are NOT derived from on TCS status aliases

#END

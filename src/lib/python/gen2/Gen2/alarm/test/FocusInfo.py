#!/usr/bin/env python

#
# FocusInfo.py - provides a method to iterate through focal stations
#                and provide attribute information for each one.
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Thu Jun 21 12:32:44 HST 2012
#]
#

import re

class FocusInfo(object):

    TSCV_FOCUSINFO_values = {
        0x00000000 : {'STATL.TSC_F_SELECT': 'OTHER',  'M2': 'OTHER',  'ADC': 'NONE',  'MelcoName': 'OTHER'},
        0x01000000 : {'STATL.TSC_F_SELECT': 'P_OPT',  'M2': 'PF_OPT', 'ADC': 'IN',  'MelcoName': 'POpt Selected'},
        0x02000000 : {'STATL.TSC_F_SELECT': 'P_IR',   'M2': 'PF_IR',  'ADC': 'OUT', 'MelcoName': 'PIR Selected'},
        0x04000000 : {'STATL.TSC_F_SELECT': 'CS_OPT', 'M2': 'CS_OPT', 'ADC': 'OUT', 'MelcoName': 'Cs(CsOpt) Selected'},
        0x08000000 : {'STATL.TSC_F_SELECT': 'CS_OPT', 'M2': 'CS_OPT', 'ADC': 'IN',  'MelcoName': 'Cs(CsOpt)+ADC Selected'},
        0x10000000 : {'STATL.TSC_F_SELECT': 'NS_OPT', 'M2': 'NS_OPT', 'ADC': 'OUT', 'MelcoName': 'NsOpt(CsOPt) Selected'},
        0x20000000 : {'STATL.TSC_F_SELECT': 'NS_OPT', 'M2': 'NS_OPT', 'ADC': 'IN',  'MelcoName': 'NsOpt(CsOpt)+ADC Selected'},
        0x40000000 : {'STATL.TSC_F_SELECT': 'NS_OPT', 'M2': 'NS_OPT', 'ADC': 'OUT', 'MelcoName': 'NsOpt(CsOpt)+ImR(B) Selected'},
        0x80000000 : {'STATL.TSC_F_SELECT': 'NS_OPT', 'M2': 'NS_OPT', 'ADC': 'IN',  'MelcoName': 'NsOpt(CsOpt)+ImR(B)+ADC Selected'},
        0x00010000 : {'STATL.TSC_F_SELECT': 'NS_OPT', 'M2': 'CS_OPT', 'ADC': 'OUT', 'MelcoName': 'NsOpt(CsOpt)+ImR(R) Selected'},
        0x00020000 : {'STATL.TSC_F_SELECT': 'NS_OPT', 'M2': 'CS_OPT', 'ADC': 'IN',  'MelcoName': 'NsOpt(CsOpt)+ImR(R)+ADC Selected'},
        0x00040000 : {'STATL.TSC_F_SELECT': 'NS_IR',  'M2': 'CS_OPT', 'ADC': 'OUT', 'MelcoName': 'NsIR(CsOpt) Selected'},
        0x00080000 : {'STATL.TSC_F_SELECT': 'NS_IR',  'M2': 'CS_OPT', 'ADC': 'OUT', 'MelcoName': 'NsIR(CsOpt)+ImR Selected'},
        0x00100000 : {'STATL.TSC_F_SELECT': 'NS_OPT', 'M2': 'NS_OPT', 'ADC': 'OUT', 'MelcoName': 'NsOpt(NsOpt) Selected'},
        0x00200000 : {'STATL.TSC_F_SELECT': 'NS_OPT', 'M2': 'NS_OPT', 'ADC': 'IN',  'MelcoName': 'NsOpt(NsOpt)+ADC Selected'},
        0x00400000 : {'STATL.TSC_F_SELECT': 'NS_OPT', 'M2': 'NS_OPT', 'ADC': 'OUT', 'MelcoName': 'NsOpt(NsOpt)+ImR(B) Selected'},
        0x00800000 : {'STATL.TSC_F_SELECT': 'NS_OPT', 'M2': 'NS_OPT', 'ADC': 'IN',  'MelcoName': 'NsOpt(NsOpt)+ImR(B)+ADC Selected'},
        0x00000100 : {'STATL.TSC_F_SELECT': 'NS_OPT', 'M2': 'NS_OPT', 'ADC': 'OUT', 'MelcoName': 'NsOpt(NsOpt)+ImR(R) Selected'},
        0x00000200 : {'STATL.TSC_F_SELECT': 'NS_OPT', 'M2': 'NS_OPT', 'ADC': 'IN',  'MelcoName': 'NsOpt(NsOpt)+ImR(R)+ADC Selected'},
        0x00000400 : {'STATL.TSC_F_SELECT': 'NS_IR',  'M2': 'NS_OPT', 'ADC': 'OUT', 'MelcoName': 'NsIR(NsOpt) Selected'},
        0x00000800 : {'STATL.TSC_F_SELECT': 'NS_IR',  'M2': 'NS_OPT', 'ADC': 'OUT', 'MelcoName': 'NsIR(NsOpt)+ImR Selected'},
        0x00001000 : {'STATL.TSC_F_SELECT': 'CS_IR',  'M2': 'IR',     'ADC': 'OUT', 'MelcoName': 'Cs(IR) Selected'},
        0x00002000 : {'STATL.TSC_F_SELECT': 'NS_OPT', 'M2': 'IR',     'ADC': 'OUT', 'MelcoName': 'NsOpt(IR) Selected'},
        0x00004000 : {'STATL.TSC_F_SELECT': 'NS_OPT', 'M2': 'IR',     'ADC': 'IN',  'MelcoName': 'NsOpt(IR)+ADC Selected'},
        0x00008000 : {'STATL.TSC_F_SELECT': 'NS_OPT', 'M2': 'IR',     'ADC': 'OUT', 'MelcoName': 'NsOpt(IR)+ImR(B) Selected'},
        0x00000001 : {'STATL.TSC_F_SELECT': 'NS_OPT', 'M2': 'IR',     'ADC': 'IN',  'MelcoName': 'NsOpt(IR)+ImR(B)+ADC Selected'},
        0x00000002 : {'STATL.TSC_F_SELECT': 'NS_OPT', 'M2': 'IR',     'ADC': 'OUT', 'MelcoName': 'NsOpt(IR)+ImR(R) Selected'},
        0x00000004 : {'STATL.TSC_F_SELECT': 'NS_OPT', 'M2': 'IR',     'ADC': 'IN',  'MelcoName': 'NsOpt(IR)+ImR(R)+ADC Selected'},
        0x00000008 : {'STATL.TSC_F_SELECT': 'NS_IR',  'M2': 'IR',     'ADC': 'OUT', 'MelcoName': 'NsIR(IR) Selected'},
        0x00000010 : {'STATL.TSC_F_SELECT': 'NS_IR',  'M2': 'IR',     'ADC': 'OUT', 'MelcoName': 'NsIR(IR)+ImR Selected'}
}
    TSCV_FOCUSINFO2_values = {
        0x01       : {'STATL.TSC_F_SELECT': 'NS_IR', 'M2': 'IR',     'ADC': 'OUT', 'MelcoName': 'NsIR(IR)+AO Selected'},
        0x02       : {'STATL.TSC_F_SELECT': 'NS_IR', 'M2': 'CS_OPT', 'ADC': 'OUT', 'MelcoName': 'NsIR(CsOpt)+AO Selected'},
        0x04       : {'STATL.TSC_F_SELECT': 'NS_IR', 'M2': 'NS_OPT', 'ADC': 'OUT', 'MelcoName': 'NsIR(NsOpt)+AO Selected'},
        0x08       : {'STATL.TSC_F_SELECT': 'P_OPT2','M2': 'PF_OPT2','ADC': 'IN',  'MelcoName': 'HSC Selected'}
        }

    def focusInfoIterator(self, focalStation = ''):
        focInfo = {}
        for key1 in self.TSCV_FOCUSINFO_values:
            focInfo['TSCV.FOCUSINFO'] = key1
            if key1 == 0x00000000:
                for key2 in self.TSCV_FOCUSINFO2_values:
                    thisFocalStation = self.TSCV_FOCUSINFO2_values[key2]['STATL.TSC_F_SELECT']
                    if re.match(focalStation, thisFocalStation):
                        focInfo['TSCV.FOCUSINFO2'] = key2
                        focInfo['FOCAL_STATION'] = thisFocalStation
                        for key3 in self.TSCV_FOCUSINFO2_values[key2]:
                            focInfo[key3] = self.TSCV_FOCUSINFO2_values[key2][key3]
                        yield focInfo
            else:
                thisFocalStation = self.TSCV_FOCUSINFO_values[key1]['STATL.TSC_F_SELECT']
                if re.match(focalStation, thisFocalStation):
                    focInfo['TSCV.FOCUSINFO2'] = 0x00000000
                    focInfo['FOCAL_STATION'] = thisFocalStation
                    for key2 in self.TSCV_FOCUSINFO_values[key1]:
                        focInfo[key2] = self.TSCV_FOCUSINFO_values[key1][key2]
                    yield focInfo

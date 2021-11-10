#!/usr/bin/env python

#
# FocalStation.py - methods for determining the current focal station
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Thu Jun 21 12:24:48 HST 2012
#]
#

import re
import remoteObjects as ro

class FocalStation(object):
    def __init__(self, logger = ro.nullLogger()):
        self.logger = logger
        self.statusVar1 = {
            'FocalStation':                     {'ID': 'FocStation',    'value': None},
            'FocusInfo':                        {'ID': 'FocusInfo',     'value': None}
            }
        self.statusVar2 = {
            'POpt Selected':                    {'ID': 'Melco_00A13E4', 'value': None, 'M2': 'PF_OPT', 'Rotator': 'INSR', 'ADC': 'IN'},
            'PIR Selected':                     {'ID': 'Melco_00A13E5', 'value': None, 'M2': 'PF_IR',  'Rotator': 'INSR', 'ADC': 'OUT'},
            'Cs(CsOpt) Selected':               {'ID': 'Melco_00A13E6', 'value': None, 'M2': 'CS_OPT', 'Rotator': 'INSR', 'ADC': 'OUT'},
            'Cs(CsOpt)+ADC Selected':           {'ID': 'Melco_00A13E7', 'value': None, 'M2': 'CS_OPT', 'Rotator': 'INSR', 'ADC': 'IN'},

            'NsOpt(CsOPt) Selected':            {'ID': 'Melco_00A13E8', 'value': None, 'M2': 'NS_OPT', 'Rotator': 'OUT',  'ADC': 'OUT'},
            'NsOpt(CsOpt)+ADC Selected':        {'ID': 'Melco_00A13E9', 'value': None, 'M2': 'NS_OPT', 'Rotator': 'OUT',  'ADC': 'IN'},
            'NsOpt(CsOpt)+ImR(B) Selected':     {'ID': 'Melco_00A13EA', 'value': None, 'M2': 'NS_OPT', 'Rotator': 'IMRB', 'ADC': 'OUT'},
            'NsOpt(CsOpt)+ImR(B)+ADC Selected': {'ID': 'Melco_00A13EB', 'value': None, 'M2': 'NS_OPT', 'Rotator': 'IMRB', 'ADC': 'IN'},

            'NsOpt(CsOpt)+ImR(R) Selected':     {'ID': 'Melco_00A13EC', 'value': None, 'M2': 'CS_OPT', 'Rotator': 'IMRR', 'ADC': 'OUT'},
            'NsOpt(CsOpt)+ImR(R)+ADC Selected': {'ID': 'Melco_00A13ED', 'value': None, 'M2': 'CS_OPT', 'Rotator': 'IMRR', 'ADC': 'IN'},
            'NsIR(CsOpt) Selected':             {'ID': 'Melco_00A13EE', 'value': None, 'M2': 'CS_OPT', 'Rotator': 'OUT',  'ADC': 'OUT'},
            'NsIR(CsOpt)+ImR Selected':         {'ID': 'Melco_00A13EF', 'value': None, 'M2': 'CS_OPT', 'Rotator': 'IMR',  'ADC': 'OUT'},

            'NsOpt(NsOpt) Selected':            {'ID': 'Melco_00A13F0', 'value': None, 'M2': 'NS_OPT', 'Rotator': 'OUT',  'ADC': 'OUT'},
            'NsOpt(NsOpt)+ADC Selected':        {'ID': 'Melco_00A13F1', 'value': None, 'M2': 'NS_OPT', 'Rotator': 'OUT',  'ADC': 'IN'},
            'NsOpt(NsOpt)+ImR(B) Selected':     {'ID': 'Melco_00A13F2', 'value': None, 'M2': 'NS_OPT', 'Rotator': 'IMRB', 'ADC': 'OUT'},
            'NsOpt(NsOpt)+ImR(B)+ADC Selected': {'ID': 'Melco_00A13F3', 'value': None, 'M2': 'NS_OPT', 'Rotator': 'IMRB', 'ADC': 'IN'},

            'NsOpt(NsOpt)+ImR(R) Selected':     {'ID': 'Melco_00A13F4', 'value': None, 'M2': 'NS_OPT', 'Rotator': 'IMRR', 'ADC': 'OUT'},
            'NsOpt(NsOpt)+ImR(R)+ADC Selected': {'ID': 'Melco_00A13F5', 'value': None, 'M2': 'NS_OPT', 'Rotator': 'IMRR', 'ADC': 'IN'},
            'NsIR(NsOpt) Selected':             {'ID': 'Melco_00A13F6', 'value': None, 'M2': 'NS_OPT', 'Rotator': 'OUT',  'ADC': 'OUT'},
            'NsIR(NsOpt)+ImR Selected':         {'ID': 'Melco_00A13F7', 'value': None, 'M2': 'NS_OPT', 'Rotator': 'IMR',  'ADC': 'OUT'},

            'Cs(IR) Selected':                  {'ID': 'Melco_00A13F8', 'value': None, 'M2': 'IR',     'Rotator': 'INSR', 'ADC': 'OUT'},
            'NsOpt(IR) Selected':               {'ID': 'Melco_00A13F9', 'value': None, 'M2': 'IR',     'Rotator': 'OUT',  'ADC': 'OUT'},
            'NsOpt(IR)+ADC Selected':           {'ID': 'Melco_00A13FA', 'value': None, 'M2': 'IR',     'Rotator': 'OUT',  'ADC': 'IN'},
            'NsOpt(IR)+ImR(B) Selected':        {'ID': 'Melco_00A13FB', 'value': None, 'M2': 'IR',     'Rotator': 'IMRB', 'ADC': 'OUT'},

            'NsOpt(IR)+ImR(B)+ADC Selected':    {'ID': 'Melco_00A13FC', 'value': None, 'M2': 'IR',     'Rotator': 'IMRB', 'ADC': 'IN'},
            'NsOpt(IR)+ImR(R) Selected':        {'ID': 'Melco_00A13FD', 'value': None, 'M2': 'IR',     'Rotator': 'IMRR', 'ADC': 'OUT'},
            'NsOpt(IR)+ImR(R)+ADC Selected':    {'ID': 'Melco_00A13FE', 'value': None, 'M2': 'IR',     'Rotator': 'IMRR', 'ADC': 'IN'},
            'NsIR(IR) Selected':                {'ID': 'Melco_00A13FF', 'value': None, 'M2': 'IR',     'Rotator': 'OUT',  'ADC': 'OUT'},

            'NsIR(IR)+ImR Selected':            {'ID': 'Melco_00A1400', 'value': None, 'M2': 'IR',     'Rotator': 'IMR',  'ADC': 'OUT'},

            'NsIR(IR)+AO Selected':             {'ID': 'Melco_00A1407', 'value': None, 'M2': 'IR',     'Rotator': 'OUT',  'ADC': 'OUT'},
            'NsIR(CsOpt)+AO Selected':          {'ID': 'Melco_00A1408', 'value': None, 'M2': 'CS_OPT', 'Rotator': 'OUT',  'ADC': 'OUT'},
            'NsIR(NsOpt)+AO Selected':          {'ID': 'Melco_00A1409', 'value': None, 'M2': 'NS_OPT', 'Rotator': 'OUT',  'ADC': 'OUT'},
            'HSC Selected':                     {'ID': 'Melco_00A140F', 'value': None, 'M2': 'PF_OPT2','Rotator': 'INSR', 'ADC': 'IN'}
            }

    def updateStatusVar(self, svConfig, statusFromGen2, statusVar):
        for key in statusVar:
            ID = statusVar[key]['ID']
            svConfigItem = svConfig.configID[ID]
            if svConfigItem.Gen2Alias in statusFromGen2:
                statusVar[key]['value'] = svConfigItem.MelcoValue(statusFromGen2[svConfigItem.Gen2Alias])

    def update(self, svConfig, statusFromGen2):
        # Update our statusVar dictionary based on the status values
        # received from Gen2.
        self.updateStatusVar(svConfig, statusFromGen2, self.statusVar1)
        self.updateStatusVar(svConfig, statusFromGen2, self.statusVar2)

    def focalStation(self):
        return self.statusVar1['FocalStation']['value']

    def focalStationIsPrimeFocus(self):
        return re.match('^P_', self.statusVar1['FocalStation']['value'])

    def focalStationIsNasmyth(self):
        return re.match('^NS_', self.statusVar1['FocalStation']['value'])

    def focalStationIsNasmythOpt(self):
        return re.match('^NS_OPT', self.statusVar1['FocalStation']['value'])

    def focalStationIsCassegrain(self):
        return re.match('^CS_', self.statusVar1['FocalStation']['value'])

    def focusInfo(self):
        return self.statusVar1['FocusInfo']['value']

    def rotIsIn(self):
        return not self.rotIsOut()

    def rotIsOut(self):
        return self.rotatorState() == 'OUT'

    def adcIsIn(self):
        return not self.adcIsOut()

    def adcIsOut(self):
        return self.adcState() == 'OUT'

    def m2IsIR(self):
        return self.m2State() == 'IR'

    def m2State(self):
        for key in self.statusVar2:
            if self.statusVar2[key]['value']:
                return self.statusVar2[key]['M2']

    def rotatorState(self):
        for key in self.statusVar2:
            if self.statusVar2[key]['value']:
                return self.statusVar2[key]['Rotator']

    def adcState(self):
        for key in self.statusVar2:
            if self.statusVar2[key]['value']:
                return self.statusVar2[key]['ADC']

    def description(self):
        for key in self.statusVar2:
            if self.statusVar2[key]['value']:
                return key

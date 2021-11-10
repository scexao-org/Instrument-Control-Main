#!/usr/bin/env python

#
# MirrorCover.py - methods for determining the state of the mirror
#                  covers
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Thu Apr 12 13:47:18 HST 2012
#]
#
#

import remoteObjects as ro

class MirrorCover(object):
    def __init__(self, logger = ro.nullLogger()):
        self.logger = logger
        self.statusVar = {
            'PM/M3 Cover Open OPN':         {'ID': 'Melco_0024005', 'value': None},
            'PM/M3 Cover Close OPN':        {'ID': 'Melco_0024006', 'value': None},
            'PM/M3 Cover Stop':             {'ID': 'Melco_0024057', 'value': None},
            'PM Cover Upper U-1A Open':     {'ID': 'Melco_0024007', 'value': None},
            'PM Cover Upper U-1A Close':    {'ID': 'Melco_0024009', 'value': None},
            'PM Cover Upper U-1B Open':     {'ID': 'Melco_002400B', 'value': None},
            'PM Cover Upper U-1B Close':    {'ID': 'Melco_002400D', 'value': None},
            'PM Cover Upper U-2A Open':     {'ID': 'Melco_002400F', 'value': None},
            'PM Cover Upper U-2A Close':    {'ID': 'Melco_0024011', 'value': None},
            'PM Cover Upper U-2B Open':     {'ID': 'Melco_0024013', 'value': None},
            'PM Cover Upper U-2B Close':    {'ID': 'Melco_0024015', 'value': None},
            'PM Cover Upper U-3A Open':     {'ID': 'Melco_0024017', 'value': None},
            'PM Cover Upper U-3A Close':    {'ID': 'Melco_0024019', 'value': None},
            'PM Cover Upper U-3B Open':     {'ID': 'Melco_002401B', 'value': None},
            'PM Cover Upper U-3B Close':    {'ID': 'Melco_002401D', 'value': None},
            'PM Cover Upper U-3C Open':     {'ID': 'Melco_002401F', 'value': None},
            'PM Cover Upper U-3C Close':    {'ID': 'Melco_0024021', 'value': None},
            'PM Cover Upper U-3D Open':     {'ID': 'Melco_0024023', 'value': None},
            'PM Cover Upper U-3D Close':    {'ID': 'Melco_0024025', 'value': None},
            'PM Cover Lower L-A Open':      {'ID': 'Melco_0024027', 'value': None},
            'PM Cover Lower L-A Close':     {'ID': 'Melco_0024029', 'value': None},
            'PM Cover Lower L-B Open':      {'ID': 'Melco_002402B', 'value': None},
            'PM Cover Lower L-B Close':     {'ID': 'Melco_002402D', 'value': None},
            'PM Cover Lower L-C Open':      {'ID': 'Melco_002402F', 'value': None},
            'PM Cover Lower L-C Close':     {'ID': 'Melco_0024031', 'value': None},
            'PM Cover Lower L-D Open':      {'ID': 'Melco_0024033', 'value': None},
            'PM Cover Lower L-D Close':     {'ID': 'Melco_0024035', 'value': None},
            'PM Cover Door U-1A-I Open':    {'ID': 'Melco_0024037', 'value': None},
            'PM Cover Door U-1A-I Close':   {'ID': 'Melco_0024039', 'value': None},
            'PM Cover Door U-1B-I Open':    {'ID': 'Melco_002403B', 'value': None},
            'PM Cover Door U-1B-I Close':   {'ID': 'Melco_002403D', 'value': None},
            'PM Cover Door U-2A-I-A Open':  {'ID': 'Melco_002403F', 'value': None},
            'PM Cover Door U-2A-I-A Close': {'ID': 'Melco_0024041', 'value': None},
            'PM Cover Door U-2A-I-B Open':  {'ID': 'Melco_0024043', 'value': None},
            'PM Cover Door U-2A-I-B Close': {'ID': 'Melco_0024045', 'value': None},
            'PM Cover Door U-2B-I-A Open':  {'ID': 'Melco_0024047', 'value': None},
            'PM Cover Door U-2B-I-A Close': {'ID': 'Melco_0024049', 'value': None},
            'PM Cover Door U-2B-I-B Open':  {'ID': 'Melco_002404B', 'value': None},
            'PM Cover Door U-2B-I-B Close': {'ID': 'Melco_002404D', 'value': None},
            'PM Cover Door U-3A-I Open':    {'ID': 'Melco_002404F', 'value': None},
            'PM Cover Door U-3A-I Close':   {'ID': 'Melco_0024051', 'value': None},
            'PM Cover Door U-3B-I Open':    {'ID': 'Melco_0024053', 'value': None},
            'PM Cover Door U-3B-I Close':   {'ID': 'Melco_0024055', 'value': None},
            'PM Cover Door U-3C-I Open':    {'ID': 'Melco_00240EB', 'value': None},
            'PM Cover Door U-3C-I Close':   {'ID': 'Melco_00240ED', 'value': None},
            'PM Cover Door U-3D-I Open':    {'ID': 'Melco_00240EF', 'value': None},
            'PM Cover Door U-3D-I Close':   {'ID': 'Melco_00240F1', 'value': None},
            }

    def update(self, svConfig, statusFromGen2):
        # Update our statusVar dictionary based on the status values
        # received from Gen2.
        for key in self.statusVar:
            ID = self.statusVar[key]['ID']
            svConfigItem = svConfig.configID[ID]
            if svConfigItem.Gen2Alias in statusFromGen2:
                self.statusVar[key]['value'] = svConfigItem.MelcoValue(statusFromGen2[svConfigItem.Gen2Alias])

    def m1Closed(self):
        allClosed = None
        # This code is based on some of the logic in the TelStat
        # GlobalStates class. The TelStat logic was based on Gen2
        # status aliases but the alarm handler code is based on MELCO
        # status values. The next line computes the value that is
        # equivalent to the Gen2 status alias TSCV.M1CoverOnway by
        # combining the individual MELCO status values.
        M1CoverOnway = self.statusVar['PM/M3 Cover Open OPN']['value'] + \
            (self.statusVar['PM/M3 Cover Close OPN']['value'] << 1) + \
            (self.statusVar['PM/M3 Cover Stop']['value']      << 2)
        # Set the preliminary value of allClosed based on
        # M1CoverOnway. This uses the same logic as TelStat
        # GlobalStates used.
        if M1CoverOnway != 0x01 and M1CoverOnway != 0x02:
            allClosed = True
        else:
            allClosed = False
        # Iterate through all of the "PM Cover" status values. If any
        # of the "Open" values are True, then allClosed is set to
        # False. If any of the "Close" values are False, then
        # allClosed is set to False.
        for key in self.statusVar:
            if 'PM Cover' in key:
                if 'Open' in key:
                    if self.statusVar[key]['value']:
                        allClosed = False
                elif 'Close' in key:
                    if self.statusVar[key]['value']:
                        allClosed = allClosed and True
                    else:
                        allClosed = False
        return allClosed

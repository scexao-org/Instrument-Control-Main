#!/usr/bin/env python

#
# DomeShutter.py - methods for determining the state of the dome
#                  shutters
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Thu Apr 12 13:02:46 HST 2012
#]
#

import remoteObjects as ro

class DomeShutter(object):
    def __init__(self, logger = ro.nullLogger()):
        self.logger = logger
        self.statusVar = {
            'irShutterOpen':  {'ID': 'Melco_003002C', 'value': None},
            'optShutterOpen': {'ID': 'Melco_003002E', 'value': None}
            }

    def update(self, svConfig, statusFromGen2):
        # Update our statusVar dictionary based on the status values
        # received from Gen2.
        for key in self.statusVar:
            ID = self.statusVar[key]['ID']
            svConfigItem = svConfig.configID[ID]
            if svConfigItem.Gen2Alias in statusFromGen2:
                self.statusVar[key]['value'] = svConfigItem.MelcoValue(statusFromGen2[svConfigItem.Gen2Alias])

    def shutterClosed(self):
        if self.irShutterOpen() or self.optShutterOpen():
            return False
        else:
            return True

    def irShutterOpen(self):
        return self.statusVar['irShutterOpen']['value']

    def optShutterOpen(self):
        return self.statusVar['optShutterOpen']['value']

#!/usr/bin/env python

#
# GuideStarTest.py - Test the GuideStar class to make sure it:
#                      - accurately reports alarm states
#                      - mutes alarm warnings when dome is closed
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Thu Jun 21 13:01:14 HST 2012
#]
#

import unittest
import AlarmTest
import FocusInfo
import AG_PosnErrorTest
import ADCFreeTest
import Gen2.alarm.GuideStar as GuideStar
import Gen2.alarm.FocalStation as FocalStation

class GuideStarTest(AlarmTest.AutoguiderTest):
    def setUp(self):
        super(GuideStarTest, self).setUp()
        # We will need a GuideStar object, so create one here
        self.guidestar = GuideStar.GuideStar()
        # Will also need a FocusInfo object.
        self.focusInfo = FocusInfo.FocusInfo()
        self.alarmFuncs = {
            'guideStarLost': {'Critical':  self.guidestar.guideStarLost},
            }

    def checkIntensity(self, name):
        if 'PIR AG' in name:
            Gen2Alias = self.svConfig.configID[self.getGuideStarID('PIR AG for SH Star Detect Start')].Gen2Alias
            self.statusFromGen2[Gen2Alias] = 0x04
            self.setIntensity('PIR AG for SH Star Posn Intensity', 'Critical')
        elif 'PIR Fibre AG' in name:
            Gen2Alias = self.svConfig.configID[self.getGuideStarID('PIR Fibre AG Star Detect Start')].Gen2Alias
            self.statusFromGen2[Gen2Alias] = 0x04
            self.setIntensity('PIR Fibre AG Star Posn Intensity', 'Critical')
        elif 'HSC AG for SC' in name:
            Gen2Alias = self.svConfig.configID[self.getGuideStarID('HSC AG for SC Star Detect Start')].Gen2Alias
            self.statusFromGen2[Gen2Alias] = 0x04
            self.setIntensity('HSC AG for SC Star Posn Intensity', 'Critical')
        elif 'HSC AG for SH' in name:
            Gen2Alias = self.svConfig.configID[self.getGuideStarID('HSC AG for SH Star Detect Start')].Gen2Alias
            self.statusFromGen2[Gen2Alias] = 0x04
            self.setIntensity('HSC AG for SH Star Posn Intensity', 'Critical')
        else:
            self.setIntensity('%s Star Position1 Intensity on %s' % (name, name), 'Critical')
        self.guidestar.update(self.svConfig, self.statusFromGen2)
        self.assertTrue(self.alarmFuncs['guideStarLost']['Critical']())

    def testGuideStarLost(self):
        for gmode in self.telState.telDriveModes['Guiding']:
            self.setTelDrive(gmode)
            # The "guide star lost" alarm depends on the focus settings,
            # so iterate through all of them.
            for f in self.focusInfo.focusInfoIterator():
                self.setFocStation(f)
                if f['STATL.TSC_F_SELECT'] == 'P_IR':
                    self.checkIntensity('PIR AG')
                    self.checkIntensity('PIR Fibre AG')
                elif f['STATL.TSC_F_SELECT'] == 'P_OPT2':
                    self.checkIntensity('HSC AG for SC')
                    self.checkIntensity('HSC AG for SH')
                else:
                    if 'SV' in gmode:
                        self.checkIntensity('SV')
                    else:
                        self.checkIntensity('AG')

    def guideStarLostTest(self, focalStation=None):
        self.setPosnErrorAllOk()
        if 'P_IR' in focalStation:
            gmode = 'Guiding(AGPIR)'
        elif 'P_OPT2' in focalStation:
            gmode = 'Guiding(HSCSCAG)'
        else:
            gmode = 'Guiding(AG1)'
        self.setTelDrive(gmode)
        for f in self.focusInfo.focusInfoIterator(focalStation):
            self.setFocStation(f)
            focalStation = FocalStation.FocalStation()
            focalStation.update(self.svConfig, self.statusFromGen2)
            adcFreeTest = ADCFreeTest.ADCFreePFTest()
            adcFreeTest.setUp()
            if focalStation.adcIsIn():
                adcFreeTest.setADCInDriveOnSync()
            else:
                adcFreeTest.setADCOut()
            self.statusFromGen2.update(adcFreeTest.statusFromGen2)
            if f['STATL.TSC_F_SELECT'] == 'P_IR':
                gmode = 'Guiding(AGPIR)'
                Gen2Alias = self.svConfig.configID[self.getGuideStarID('PIR AG for SH Star Detect Start')].Gen2Alias
                self.statusFromGen2[Gen2Alias] = 0x04
                self.setIntensity('PIR AG for SH Star Posn Intensity', 'Critical')
                self.guidestar.update(self.svConfig, self.statusFromGen2)
            elif f['STATL.TSC_F_SELECT'] == 'P_OPT2':
                gmode = 'Guiding(HSCSCAG)'
                Gen2Alias = self.svConfig.configID[self.getGuideStarID('HSC AG for SC Star Detect Start')].Gen2Alias
                self.statusFromGen2[Gen2Alias] = 0x04
                self.setIntensity('HSC AG for SC Star Posn Intensity', 'Critical')
                self.guidestar.update(self.svConfig, self.statusFromGen2)
            else:
                if 'SV' in gmode:
                    gmode = 'Guiding(SV1)'
                    self.setIntensity('SV Star Position1 Intensity on SV', 'Critical')
                else:
                    gmode = 'Guiding(AG1)'
                    self.setIntensity('AG Star Position1 Intensity on AG', 'Critical')
            self.setTelDrive(gmode)
            break

    def guideStarLostP_IRTest(self):
        self.guideStarLostTest('P_IR')

    def guideStarLostP_OPT2Test(self):
        self.guideStarLostTest('P_OPT2')

    def guideStarLostNS_OPTTest(self):
        self.guideStarLostTest('NS_OPT')

    def guideStarLostAllOkTest(self):
        for f in self.focusInfo.focusInfoIterator('NS_OPT'):
            self.focalStationName = f['FOCAL_STATION']
            self.setFocStation(f)
            focalStation = FocalStation.FocalStation()
            focalStation.update(self.svConfig, self.statusFromGen2)
            adcFreeTest = ADCFreeTest.ADCFreePFTest()
            adcFreeTest.setUp()
            if focalStation.adcIsIn():
                adcFreeTest.setADCInDriveOnSync()
            else:
                adcFreeTest.setADCOut()
            self.statusFromGen2.update(adcFreeTest.statusFromGen2)
            break

        self.setPosnErrorAllOk()
        self.setIntensityAllOk()
        self.guidestar.update(self.svConfig, self.statusFromGen2)

if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python

#
# AlarmTest.py - Base class for the tests of the alarm_handler classes
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Thu Jun 21 13:08:23 HST 2012
#]
#

import unittest
import os, sys
import math
import ssdlog
import Gen2.alarm.StatusVar as StatusVar
import Gen2.alarm.DomeShutter as DomeShutter
import Gen2.alarm.MirrorCover as MirrorCover
import Gen2.alarm.TelState as TelState
import Gen2.alarm.AG_PosnError as AG_PosnError
import Gen2.alarm.GuideStar as GuideStar

class AlarmTest(unittest.TestCase):

    def runTest(self):
        pass

    def setUp(self):
        try:
            pyhome = os.environ['PYHOME']
            cfgDir = os.path.join(pyhome, 'cfg', 'alarm')
        except:
            cfgDir = '.'
        default_alarm_cfg_file = os.path.join(cfgDir, '*.yml')

        from optparse import OptionParser
        usage = "usage: %prog [options]"
        optprs = OptionParser(usage=usage, version=('%%prog'))

        optprs.add_option("-f", "--configfile", dest="configfile", default=default_alarm_cfg_file,
                          help="Specify configuration file")
        ssdlog.addlogopts(optprs)

        (options, args) = optprs.parse_args(sys.argv[1:])

        # Create top level logger.
        logger = ssdlog.make_logger('module_test', options)

        dummyDatafileLock = None

        try:
            self.svConfig = StatusVar.StatusVarConfig(options.configfile, dummyDatafileLock, logger)
        except Exception, e:
            logger.error('Error opening configuration file(s): %s' % str(e))

        self.domeShutter = DomeShutter.DomeShutter()
        self.mirrorCover = MirrorCover.MirrorCover()
        self.telState = TelState.TelState()
        self.statusFromGen2 = {}

        self.severityList = ('WarningLo', 'WarningHi', 'CriticalLo', 'CriticalHi')

    def setDomeShutter(self, irShutterOpen, optShutterOpen):
        self.statusFromGen2['TSCV.DomeShutter'] = 0
        if irShutterOpen:
            self.statusFromGen2['TSCV.DomeShutter'] |= 0x10 
        if optShutterOpen:
            self.statusFromGen2['TSCV.DomeShutter'] |= 0x40 

    def setMirrorCover(self, allClosed):
        self.statusFromGen2['TSCV.M1CoverOnway'] = 0
        self.statusFromGen2['TSCV.M1Cover'] = 0
        if allClosed:
            self.statusFromGen2['TSCV.M1CoverOnway'] = 0x06
            self.statusFromGen2['TSCV.M1Cover'] = 0x4444444444444444444444
        else:
            self.statusFromGen2['TSCV.M1CoverOnway'] = 0x01
            self.statusFromGen2['TSCV.M1Cover'] = 0x1111111111111111111111

    def setTelEl(self, elevation):
        self.statusFromGen2['TSCS.EL'] = elevation

    def setTelStowed(self, parked):
        if parked:
            self.setTelEl(self.telState.inactiveElevationThreshold * 1.02)
        else:
            self.setTelEl(self.telState.inactiveElevationThreshold * 0.8)

    def setTelLimitFlag(self, elLowValid = None, elHighValid = None, azValid = None, rotValid = None, bigRotValid = None):
        self.statusFromGen2['TSCL.LIMIT_FLAG'] = 0
        if elLowValid:
            self.statusFromGen2['TSCL.LIMIT_FLAG'] |= 0x01
        if elHighValid:
            self.statusFromGen2['TSCL.LIMIT_FLAG'] |= 0x02
        if azValid:
            self.statusFromGen2['TSCL.LIMIT_FLAG'] |= 0x04
        if rotValid:
            self.statusFromGen2['TSCL.LIMIT_FLAG'] |= 0x08
        if bigRotValid:
            self.statusFromGen2['TSCL.LIMIT_FLAG'] |= 0x10

    def setTelDrive(self, state):
        # Code based on settings in Derive._StatlTeldrive_common function
        settingsTSC = {
            'Guiding(AG1)':    {'TSCV.TelDrive': 0x4000, 'TSCV.AutoGuideOn': 0x01},
            'Guiding(AG2)':    {'TSCV.TelDrive': 0x4000, 'TSCV.AutoGuideOn': 0x02},
            'Guiding(SV1)':    {'TSCV.TelDrive': 0x8000, 'TSCV.SVAutoGuideOn': 0x01},
            'Guiding(SV2)':    {'TSCV.TelDrive': 0x8000, 'TSCV.SVAutoGuideOn': 0x02},
            'Guiding(AGPIR)':  {'TSCV.TelDrive': 0x0004},
            'Guiding(AGFMOS)': {'TSCV.TelDrive': 0x0008},
            'Guiding(HSCSCAG)':{'TSCV.TelDrive': 0x0010},
            'Guiding(HSCSHAG)':{'TSCV.TelDrive': 0x0020},
            'Slewing':         {'TSCV.TelDrive': 0x2000, 'TSCS.AZDIF': 0.1251, 'TSCS.ELDIF': 0.1251},
            'Tracking':        {'TSCV.TelDrive': 0x2000, 'TSCS.AZDIF': 0., 'TSCS.ELDIF': 0., 'TSCV.TRACKING': 0x04},
            'Tracking(Non-Sidereal)':  {'TSCV.TelDrive': 0x2000, 'TSCV.TRACKING': 0x10},
            'Pointing':        {'TSCV.TelDrive': 0x1000}
            }
        for name in settingsTSC[state]:
            value = settingsTSC[state][name]
            self.statusFromGen2[name] = value
        self.statusFromGen2['STATL.TELDRIVE'] = state

    def setAngleLimitTime(self, limitTimeAz = 100, limitTimeElLow = 100, limitTimeElHigh = 100, limitTimeRot = 100):
        if limitTimeAz:
            self.statusFromGen2['TSCL.LIMIT_AZ'] = limitTimeAz
        if limitTimeElLow:
            self.statusFromGen2['TSCL.LIMIT_EL_LOW'] = limitTimeElLow
        if limitTimeElHigh:
            self.statusFromGen2['TSCL.LIMIT_EL_HIGH'] = limitTimeElHigh
        if limitTimeRot:
            self.statusFromGen2['TSCL.LIMIT_ROT'] = limitTimeRot

    def setOpState(self, operational):
        if operational:
            self.setDomeShutter(True, True)
            self.setMirrorCover(False)
            self.setTelStowed(False)
        else:
            self.setDomeShutter(False, False)
            self.setMirrorCover(True)
            self.setTelStowed(True)

    def setFocusChanging(self, changing):
        value = 0x00
        if changing:
            value |= 0x40
        self.statusFromGen2['TSCV.FOCUSALARM'] = value

    def setFocStation(self, focInfo):
        self.statusFromGen2['STATL.TSC_F_SELECT'] = focInfo['STATL.TSC_F_SELECT']
        self.statusFromGen2['TSCV.FOCUSINFO'] = focInfo['TSCV.FOCUSINFO']
        self.statusFromGen2['TSCV.FOCUSINFO2'] = focInfo['TSCV.FOCUSINFO2']

class AutoguiderTest(AlarmTest):
    def setUp(self):
        super(AutoguiderTest, self).setUp()
        self.agPosnError = AG_PosnError.AG_PosnError()
        self.guidestar = GuideStar.GuideStar()
        self.posnErrorTSC = {
            'Guiding(AGPIR)':  ('TSCL.AGPIRdX',   'TSCL.AGPIRdY'),
            'Guiding(AGFMOS)': ('TSCL.AGFMOSdAZ', 'TSCL.AGFMOSdEL'),
            'Guiding(HSCSCAG)':('TSCL.HSC.SCAG,DX', 'TSCL.HSC.SCAG.DY'),
            'Guiding(HSCSHAG)':('TSCL.HSC.SHAG,DX', 'TSCL.HSC.SHAG,DY'),
            'Guiding(AG1)':    ('TSCL.AG1dX',     'TSCL.AG1dY'),
            'Guiding(AG2)':    ('TSCL.AG2dX',     'TSCL.AG2dY'),
            'Guiding(SV1)':    ('TSCL.SV1DX',     'TSCL.SV1DY'),
            'Guiding(SV2)':    ('TSCL.SV2DX',     'TSCL.SV2DY')
            }

    def getAG_ID(self, name):
        # Return the status variable ID
        return self.agPosnError.statusVar[name]['ID']

    def setPosnError(self, gmode, name, severity):
        # AGFMOS guiding position errors must be divided by 1000 to be
        # consistent with other autoguider values. See _StatlAgrErr
        # function in SOSS/status/Derive.py
        if 'AGFMOS' in gmode:
            factor = 1. / 1000.
        else:
            factor = 1.
        svConfigItem = self.svConfig.configID[self.getAG_ID(name)]
        Gen2Alias = svConfigItem.Gen2Alias
        if 'Ok' in severity:
            value = svConfigItem.Alarm['WarningHi'].Threshold * 0.5
        elif 'Warning' in severity:
            value = svConfigItem.Alarm[severity].Threshold * 1.02
        elif 'Critical' in severity:
            value = svConfigItem.Alarm[severity].Threshold * 1.02
        value *= factor
        self.statusFromGen2[Gen2Alias] = value
        for alias in self.posnErrorTSC[gmode]:
            self.statusFromGen2[alias] = value / math.sqrt(2)

    def setPosnErrorAllOk(self):
        for gmode in self.telState.telDriveModes['Guiding']:
            self.setTelDrive(gmode)
            if 'SV' in gmode:
                name = 'SV_Error'
            else:
                name = 'AG_Error'
            self.setPosnError(gmode, name, 'Ok')
            self.agPosnError.update(self.svConfig, self.statusFromGen2)

    def getGuideStarID(self, name):
        # Return the status variable ID
        return self.guidestar.statusVar[name]['ID']

    def setIntensity(self, name, severity):
        ID = self.getGuideStarID(name)
        Gen2Alias = self.svConfig.configID[ID].Gen2Alias
        threshold = self.svConfig.configID[ID].Alarm['CriticalLo'].Threshold
        if 'Ok' in severity:
            value = threshold * 1.02
        else:
            value = threshold * 0.5
        self.statusFromGen2[Gen2Alias] = value

    def setIntensityAllOk(self):
        gmode = 'Guiding(AG1)'
        self.setTelDrive(gmode)
        self.setIntensity('PIR AG for SH Star Posn Intensity', 'Ok')
        self.setIntensity('PIR Fibre AG Star Posn Intensity', 'Ok')
        self.setIntensity('HSC AG for SC Star Posn Intensity', 'Ok')
        self.setIntensity('HSC AG for SH Star Posn Intensity', 'Ok')
        for name in ('SV', 'AG'):
            self.setIntensity('%s Star Position1 Intensity on %s' % (name, name), 'Ok')
        self.guidestar.update(self.svConfig, self.statusFromGen2)

class DomeShutterTest(AlarmTest):
    def testDomeShutterBothOpen(self):
        self.setDomeShutter(True, True)
        self.domeShutter.update(self.svConfig, self.statusFromGen2)
        self.assertFalse(self.domeShutter.shutterClosed())

    def testDomeShutterIrOpen(self):
        self.setDomeShutter(True, False)
        self.domeShutter.update(self.svConfig, self.statusFromGen2)
        self.assertFalse(self.domeShutter.shutterClosed())

    def testDomeShutterOptOpen(self):
        self.setDomeShutter(False, True)
        self.domeShutter.update(self.svConfig, self.statusFromGen2)
        self.assertFalse(self.domeShutter.shutterClosed())

    def testDomeShutterClosed(self):
        self.setDomeShutter(False, False)
        self.domeShutter.update(self.svConfig, self.statusFromGen2)
        self.assertTrue(self.domeShutter.shutterClosed())

class MirrorCoverTest(AlarmTest):
    def testMirrorCoverOpen(self):
        self.setMirrorCover(False)
        self.mirrorCover.update(self.svConfig, self.statusFromGen2)
        self.assertFalse(self.mirrorCover.m1Closed())

    def testMirrorCoverClosed(self):
        self.setMirrorCover(True)
        self.mirrorCover.update(self.svConfig, self.statusFromGen2)
        self.assertTrue(self.mirrorCover.m1Closed())

class TelStateTest(AlarmTest):
    def testElNotStowed(self):
        self.setTelStowed(False)
        self.telState.update(self.svConfig, self.statusFromGen2)
        self.assertFalse(self.telState.elStowed())

    def testElStowed(self):
        self.setTelStowed(True)
        self.telState.update(self.svConfig, self.statusFromGen2)
        self.assertTrue(self.telState.elStowed())

    def testElLowValid(self):
        self.setTelLimitFlag(elLowValid = True)
        self.telState.update(self.svConfig, self.statusFromGen2)
        self.assertTrue(self.telState.limitFlagElLow())

    def testElHighValid(self):
        self.setTelLimitFlag(elHighValid = True)
        self.telState.update(self.svConfig, self.statusFromGen2)
        self.assertTrue(self.telState.limitFlagElHigh())

    def testAzValid(self):
        self.setTelLimitFlag(azValid = True)
        self.telState.update(self.svConfig, self.statusFromGen2)
        self.assertTrue(self.telState.limitFlagAz())

    def testRotValid(self):
        self.setTelLimitFlag(rotValid = True)
        self.telState.update(self.svConfig, self.statusFromGen2)
        self.assertTrue(self.telState.limitFlagRot())

    def testBigRotValid(self):
        self.setTelLimitFlag(bigRotValid = True)
        self.telState.update(self.svConfig, self.statusFromGen2)
        self.assertTrue(self.telState.limitFlagBigRot())

if __name__ == '__main__':
    unittest.main()

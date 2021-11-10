#!/usr/bin/env python

#
# EnviroTest.py - Test the Enviro class to make sure it:
#                   - accurately reports alarm states
#                   - mutes alarm warnings when dome is closed
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Wed Apr 25 15:16:57 HST 2012
#]
#

import unittest
import time
import AlarmTest
import Gen2.alarm.Enviro as Enviro

class EnviroTest(AlarmTest.AlarmTest):
    def setUp(self):
        super(EnviroTest, self).setUp()
        # We will need an Enviro object, so create one here
        self.enviro = Enviro.Enviro()
        self.alarmFuncs = {
            'HighHumidity':     {'WarningHi':  self.enviro.warnHumidity, 'CriticalHi': self.enviro.critHumidity},
            'HighWindspeed':    {'WarningHi':  self.enviro.warnWindspeed, 'CriticalHi': self.enviro.critWindspeed},
            'HumidityInRange15Min':  {'OK': self.enviro.humidityInRange15},
            'WindspeedInRange15Min': {'OK': self.enviro.windspeedInRange15},
            'EnviroInRange30Min':    {'OK': self.enviro.enviroInRange30}
            }
        self.alarmStates =  {
            'extTemp':          {'WarningLo':  False},
            'lowTemp':          {'WarningLo':  False},
            'extHumidity':      {'WarningHi':  False, 'CriticalHi': False},
            'intHumidity':      {'WarningHi':  False, 'CriticalHi': False},
            'HighHumidity':     {'WarningHi':  False, 'CriticalHi': False},
            'extWindspeed':     {'WarningHi':  False, 'CriticalHi': False},
            'intWindspeed':     {'WarningHi':  False, 'CriticalHi': False},
            'HighWindspeed':    {'WarningHi':  False, 'CriticalHi': False},
            'HumidityInRange15Min':  {'OK':         True},
            'WindspeedInRange15Min': {'OK':         True},
            'EnviroInRange30Min':    {'OK':         True}
            }
        for name in self.enviro.statusVar:
            self.setEnviroValue(name, self.getEnviroValue(name, 'Ok'))

    def update(self, svConfig, statusFromGen2):
        self.domeShutter.update(svConfig, statusFromGen2)
        self.enviro.update(svConfig, statusFromGen2)

    def getID(self, name):
        # Return the status variable ID
        return self.enviro.statusVar[name]['ID']

    def getEnviroValue(self, name, severity):
        svConfigItem = self.svConfig.configID[self.getID(name)]
        if 'Ok' in severity:
            # Return a value that is well below the threshold
            minValue = None
            threshold = 0
            for sev in svConfigItem.Alarm:
                this_threshold = svConfigItem.Alarm[sev].Threshold
                if minValue:
                    if this_threshold < minValue:
                        threshold = this_threshold
                else:
                    minValue = this_threshold
            return threshold / 2
        else:
            # Return a value that is just past the threshold
            threshold = svConfigItem.Alarm[severity].Threshold
            return threshold * 1.02

    def setEnviroValue(self, name, value):
        # Set the Gen2 status alias for the specified environmental
        # item to the specified value
        Gen2Alias = self.svConfig.configID[self.getID(name)].Gen2Alias
        self.statusFromGen2[Gen2Alias] = value

    def checkSVItemAlarmState(self, name, ID):
        svConfigItem = self.svConfig.configID[ID]
        if svConfigItem.Alarm:
            for severity in svConfigItem.Alarm:
                if 'OK' not in severity:
                    if svConfigItem.importedObject:
                    
                        alarmState = self.alarmFuncs[name][severity]()
                    else:
                        alarmState = svConfigItem.isAlarm(severity, self.enviro.statusVar[name]['value'])
                        if self.alarmStates[name][severity]:
                            self.assertTrue(alarmState)
                        else:
                            self.assertFalse(alarmState)
        

    def checkAlarmStates(self):
        for name in self.enviro.statusVar:
            self.checkSVItemAlarmState(name, self.getID(name))
        for name in self.enviro.compositeAlarms:
            self.checkSVItemAlarmState(name, name)

    def checkMuteStates(self):
        for name in self.enviro.compositeAlarms:
            ID = name
            svConfigItem = self.svConfig.configID[ID]
            if svConfigItem.Alarm:
                for severity in svConfigItem.Alarm:
                    muteOnState = self.svConfig.getMuteOnState(severity, ID)
                    if self.domeShutter.shutterClosed():
                        self.assertTrue(muteOnState)
                    else:
                        self.assertFalse(muteOnState)

    def checkEnviroQuantity(self, singleName, compositeName, severity):
        self.setEnviroValue(singleName, self.getEnviroValue(singleName, severity))
        if 'CriticalHi' in severity:
            self.alarmStates[singleName]['WarningHi'] = True
            if compositeName:
                self.alarmStates[compositeName]['WarningHi'] = True
        self.alarmStates[singleName][severity] = True
        if compositeName:
            self.alarmStates[compositeName][severity] = True
        self.setDomeShutter(True, True)
        self.update(self.svConfig, self.statusFromGen2)
        self.checkAlarmStates()
        self.checkMuteStates()

    def checkMuteDomeClosed(self, singleName, compositeName, severity):
        # Set dome to closed and make sure all alarms are muted
        self.setDomeShutter(False, False)
        self.setEnviroValue(singleName, self.getEnviroValue(singleName, severity))
        if 'CriticalHi' in severity:
            self.alarmStates[singleName]['WarningHi'] = True
            self.alarmStates[compositeName]['WarningHi'] = True
        self.alarmStates[singleName][severity] = True
        self.alarmStates[compositeName][severity] = True
        self.update(self.svConfig, self.statusFromGen2)
        self.checkAlarmStates()
        self.checkMuteStates()

    def checkEnvCondOK(self, criticalName, okName):
        self.setDomeShutter(True, True)
        self.update(self.svConfig, self.statusFromGen2)
        self.checkAlarmStates()
        criticalID = criticalName
        okID = okName
        now = time.time()
        notifyWaitTimePeriod = self.svConfig.configID[okID].Alarm['OK'].MinNotifyInterval
        self.svConfig.configID[criticalID].Alarm['CriticalHi'].lastAlarmTimestamp = now - notifyWaitTimePeriod
        self.assertTrue(self.alarmFuncs[okName]['OK']())

    def checkEnvCondInRange30(self, singleName, compositeName, okName):
        self.setDomeShutter(True, True)
        self.setEnviroValue(singleName, self.getEnviroValue(singleName, 'CriticalHi'))
        self.alarmStates[singleName]['WarningHi'] = True
        self.alarmStates[compositeName]['WarningHi'] = True
        self.alarmStates[singleName]['CriticalHi'] = True
        self.alarmStates[compositeName]['CriticalHi'] = True
        self.update(self.svConfig, self.statusFromGen2)
        self.checkAlarmStates()
        compositeID = compositeName
        okID = okName
        now = time.time()
        notifyWaitTimePeriod = self.svConfig.configID[okID].Alarm['OK'].MinNotifyInterval
        self.svConfig.configID[compositeID].Alarm['CriticalHi'].lastAlarmTimestamp = now - notifyWaitTimePeriod
        self.setEnviroValue(singleName, self.getEnviroValue(singleName, 'Ok'))
        self.alarmStates[singleName]['WarningHi'] = False
        self.alarmStates[compositeName]['WarningHi'] = False
        self.alarmStates[singleName]['CriticalHi'] = False
        self.alarmStates[compositeName]['CriticalHi'] = False
        self.update(self.svConfig, self.statusFromGen2)
        self.checkAlarmStates()
        self.assertTrue(self.alarmFuncs[okName]['OK']())

    def testEnvCondInRange(self):
        self.checkEnvCondOK('HighHumidity', 'HumidityInRange15Min')

    def testEnvCondInRange(self):
        self.checkEnvCondOK('HighWindspeed', 'WindspeedInRange15Min')

    def testEnvCondInRange30(self):
        self.checkEnvCondInRange30('extHumidity', 'HighHumidity', 'EnviroInRange30Min')
        self.checkEnvCondInRange30('extWindspeed', 'HighWindspeed', 'EnviroInRange30Min')

    def testEnviroAllOk(self):
        self.setDomeShutter(True, True)
        self.update(self.svConfig, self.statusFromGen2)
        self.checkAlarmStates()

    def testExtTempWarningLo(self):
        self.checkEnviroQuantity('extTemp', None, 'WarningLo')
        
    def testExtHumidityWarningHi(self):
        self.checkEnviroQuantity('extHumidity', 'HighHumidity', 'WarningHi')

    def testExtHumidityCriticalHi(self):
        self.checkEnviroQuantity('extHumidity', 'HighHumidity', 'CriticalHi')

    def testIntHumidityWarningHi(self):
        self.checkEnviroQuantity('intHumidity', 'HighHumidity', 'WarningHi')

    def testIntHumidityCriticalHi(self):
        self.checkEnviroQuantity('intHumidity', 'HighHumidity', 'CriticalHi')

    def testExtWindspeedWarningHi(self):
        self.checkEnviroQuantity('extWindspeed', 'HighWindspeed', 'WarningHi')

    def testExtWindspeedCriticalHi(self):
        self.checkEnviroQuantity('extWindspeed', 'HighWindspeed', 'CriticalHi')

    def testIntWindspeedWarningHi(self):
        self.checkEnviroQuantity('intWindspeed', 'HighWindspeed', 'WarningHi')

    def testIntWindspeedCriticalHi(self):
        self.checkEnviroQuantity('intWindspeed', 'HighWindspeed', 'CriticalHi')

    def testMuteDomeClosed(self):
        self.checkMuteDomeClosed('extWindspeed', 'HighWindspeed', 'CriticalHi')

if __name__ == '__main__':
    unittest.main()

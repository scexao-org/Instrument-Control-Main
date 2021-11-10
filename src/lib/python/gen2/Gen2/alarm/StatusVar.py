#!/usr/bin/env python
#
# StatusVar.py - Status Variable classes for Gen2 alarm_handler.py
#                application
#
#[ Russell Kackley (rkackley@naoj.org) --
#  Last edit: Tue Feb 12 10:32:55 HST 2013
#]
#

import getopt, sys, os
import shelve, anydbm
import threading
import yaml
import math
import time
import glob
import cfg.g2soss as g2soss
import SOSS.status.common as common

audiofileDir = os.path.join(g2soss.producthome, 'file', 'Sounds')

class Gen2AliasError(Exception):
    pass

class IDError(Exception):
    pass

class StatusVarTypeError(Exception):
    pass

class StatusVar(object):
    def __init__(self, ID, Name, Type, Gen2Alias=None, STSAlias=None, FocalStation=None, Module=None, Class=None, Alarm=None):
        self.ID = ID
        self.Name = Name
        self.Type = Type
        self.Gen2Alias = Gen2Alias
        self.STSAlias = STSAlias
        self.FocalStation = FocalStation
        if FocalStation:
            self.ID = '_'.join([ID, FocalStation])
            self.Gen2AliasModifier = FocalStation
        else:
            self.Gen2AliasModifier = None
        self.Module = Module
        if Class:
            self.Class = Class
        else:
            self.Class = self.Module
        self.path = None
        self.Alarm = Alarm

        self.importedObject = None
        if self.Module:
            exec('import ' + self.Module)
            self.importedObject = eval('%s.%s()' % (self.Module, self.Class))

    def __repr__(self):
        return "ID=%s Name=%s Type=%s Gen2Alias=%s STSAlias=%s Module=%s Class=%s path=%s Alarm=%s" % (self.ID, self.Name, self.Type, self.Gen2Alias, self.STSAlias, self.Module, self.Class, self.path, self.Alarm)

    def isAlarm(self, identifier, gen2value):
        if identifier in self.Alarm:
            alarm = self.Alarm[identifier]
            if alarm.Type == 'Derived':
                return alarm.isAlarm(identifier, self.importedObject)
            else:
                return alarm.isAlarm(identifier, self.MelcoValue(gen2value))
        else:
            return False
       
    def MelcoValue(self, gen2Value):
        return gen2Value

    def manageNotifyTime(self, severity):
        if severity == 'Ok':
            now = time.time()            
            for key in self.Alarm:
                alarm = self.Alarm[key]
                if alarm.firstNotifyTimestamp != None and \
                       now > alarm.firstNotifyTimestamp + alarm.NotifyTimeout:
                    alarm.firstNotifyTimestamp = None
        elif 'warning' in severity.lower():
            for key in self.Alarm:
                alarm = self.Alarm[key]
                if 'critical' in key.lower():
                    alarm.firstNotifyTimestamp = None
                    alarm.lastNotifyTimestamp = None
        elif 'critical' in severity.lower():
            for key in self.Alarm:
                alarm = self.Alarm[key]
                if 'warning' in key.lower():
                    alarm.firstNotifyTimestamp = None
                    alarm.lastNotifyTimestamp = None

    def resetFirstNotifyTime(self):
        for key in self.Alarm:
            self.Alarm[key].firstNotifyTimestamp = None

class AnalogSV(StatusVar):
    def __init__(self, ID, Name, Type='Analog', Gen2Alias=None, STSAlias=None, FocalStation=None, Module=None, Class=None, Alarm=None, Units=None):
        super(AnalogSV, self).__init__(ID, Name, Type, Gen2Alias, STSAlias, FocalStation, Module, Class, Alarm)
        self.Units = Units
        self.allowedAlarmLevels = ['WarningHi', 'WarningLo', 'Warning', 'CriticalHi', 'CriticalLo', 'Critical'] 

    def __repr__(self):
        retVal = super(AnalogSV, self).__repr__()
        retVal += ' Units=%s' % self.Units
        return retVal

    def alarmState(self, gen2Value):
        if self.Alarm == None:
            return 'N/A'
        else:
            severity = 'Ok'
            for alarmLevel in self.allowedAlarmLevels:
                if alarmLevel in self.Alarm and self.isAlarm(alarmLevel, gen2Value):
                    severity = alarmLevel
            self.manageNotifyTime(severity)
            return severity

class DigitalSV(StatusVar):
    def __init__(self, ID, Name, Type='Digital', Gen2Alias=None, STSAlias=None, FocalStation=None, Module=None, Class=None, Alarm=None, InvertLogic=False):
        if Gen2Alias:
            result = str.split(Gen2Alias, '!')
            Gen2AliasName = result[0]
        else:
            result = ''
            Gen2AliasName = None

        super(DigitalSV, self).__init__( ID, Name, Type, Gen2AliasName, STSAlias, FocalStation, Module, Class, Alarm)
        self.InvertLogic = InvertLogic
        if len(result) > 1:
            self.Gen2AliasModifier = result[1]
            if self.Gen2AliasModifier.startswith('M'):
                self.Gen2AliasBitMask = int(self.Gen2AliasModifier.lstrip('M'), 16)
            elif self.Gen2AliasModifier.startswith('B'):
                self.Gen2AliasBitMask = 1 << int(self.Gen2AliasModifier.lstrip('B'))
            else:
                raise Gen2AliasError('Gen2 Alias should be specified as either M (Mask) or B (Bit)')
        else:
            self.Gen2AliasModifier = None
            self.Gen2AliasBitMask = None

    def __repr__(self):
        retVal = super(DigitalSV, self).__repr__()
        retVal += ' Gen2AliasModifier=%s Gen2AliasBitMask=%s InvertLogic=%s' % (self.Gen2AliasModifier, self.Gen2AliasBitMask, self.InvertLogic)
        return retVal

    def MelcoValue(self, gen2Value):
        if self.Gen2AliasBitMask == None:
            return gen2Value
        else:
            try:
                common.assertValidStatusValue(self.Gen2Alias, gen2Value)
            except common.statusError:
                return gen2Value
            maskedValue = gen2Value & self.Gen2AliasBitMask
            if self.Gen2AliasModifier.startswith('M'):
                return maskedValue >> int(math.log(int(self.Gen2AliasModifier.lstrip('M'), 16), 2))
            elif self.Gen2AliasModifier.startswith('B'):
                return maskedValue >> int(self.Gen2AliasModifier.lstrip('B'))

    def alarmState(self, gen2Value):
        if self.Alarm == None:
            return 'N/A'
        else:
            keys = self.Alarm.keys()
            if self.isAlarm(keys[0], gen2Value):
                severity = keys[0]
            else:
                severity = 'Ok'
            self.manageNotifyTime(severity)
            return severity

_DEFAULT_MIN_INTERVAL = 60
_DEFAULT_TIMEOUT = 60*60*24*365  
class Alarm(object):
    def __init__(self,  Type=None, Audio=None, MinNotifyInterval=_DEFAULT_MIN_INTERVAL, NotifyTimeout=_DEFAULT_TIMEOUT, MuteOn=False, Ignore=False, Visible=True):
        self.Type = Type
        self.Audio = Audio
        self.MinNotifyInterval = MinNotifyInterval
        self.NotifyTimeout = NotifyTimeout
        self.MuteOn = {'Config': MuteOn, 'User': False}
        self.Ignore = Ignore
        self.Visible = Visible
        self.firstNotifyTimestamp = None
        self.lastNotifyTimestamp = None
        self.lastAlarmTimestamp = None
        self.acknowledged = False

    def __repr__(self):
        retVal = 'Type=%s Audio=%s MinNotifyInterval=%s NotifyTimeout=%s MuteOn[Config]=%s MuteOn[User]=%s Ignore=%s Visible=%s acknowledged=%s ' % (self.Type, self.Audio, self.MinNotifyInterval, self.NotifyTimeout, self.MuteOn['Config'], self.MuteOn['User'], self.Ignore, self.Visible, self.acknowledged)
        if self.firstNotifyTimestamp:
            retVal += 'firstNotifyTimestamp=%s ' % time.asctime(time.localtime(self.firstNotifyTimestamp))
        else:
            retVal += 'firstNotifyTimestamp=%s ' % self.firstNotifyTimestamp
        if self.lastNotifyTimestamp:
            retVal += 'lastNotifyTimestamp=%s ' % time.asctime(time.localtime(self.lastNotifyTimestamp))
        else:
            retVal += 'lastNotifyTimestamp=%s ' % self.lastNotifyTimestamp
        if self.lastAlarmTimestamp:
            retVal += 'lastAlarmTimestamp=%s ' % time.asctime(time.localtime(self.lastAlarmTimestamp))
        else:
            retVal += 'lastAlarmTimestamp=%s ' % self.lastAlarmTimestamp
        return retVal

class AnalogAlarm(Alarm):
    def __init__(self, Threshold=None, Audio=None, MinNotifyInterval=_DEFAULT_MIN_INTERVAL, NotifyTimeout=_DEFAULT_TIMEOUT, MuteOn=False, Ignore=False, Visible=True):
        super(AnalogAlarm, self).__init__('Analog', Audio, MinNotifyInterval, NotifyTimeout, MuteOn, Ignore, Visible)
        self.Threshold = Threshold

    def __repr__(self):
        retVal = super(AnalogAlarm, self).__repr__()
        retVal += " Threshold=%s" % self.Threshold
        return retVal

    def isAlarm(self, identifier, value):
        if self.Ignore:
            return False
        else:
            try:
                common.assertValidStatusValue('Unknown', value)
            except common.statusError:
                return False
            if 'hi' in identifier.lower():
                return value >= self.Threshold
            elif 'lo' in identifier.lower():
                return value <= self.Threshold

class DigitalAlarm(Alarm):
    def __init__(self, InvertLogic=False, Audio=None, MinNotifyInterval=_DEFAULT_MIN_INTERVAL, NotifyTimeout=_DEFAULT_TIMEOUT, MuteOn=False, Ignore=False, Visible=True):
        super(DigitalAlarm, self).__init__('Digital', Audio, MinNotifyInterval, NotifyTimeout, MuteOn, Ignore, Visible)
        self.InvertLogic = InvertLogic

    def __repr__(self):
        retVal = super(DigitalAlarm, self).__repr__()
        retVal += "InvertLogic=%s" % self.InvertLogic
        return retVal

    def isAlarm(self, identifier, value):
        if self.Ignore:
            return False
        else:
            try:
                common.assertValidStatusValue('Unknown', value)
            except common.statusError:
                return False
            if value:
                if self.InvertLogic:
                    return False
                else:
                    return True

class DerivedAlarm(Alarm):
    def __init__(self, Method=None, Audio=None, MinNotifyInterval=_DEFAULT_MIN_INTERVAL, NotifyTimeout=_DEFAULT_TIMEOUT, MuteOn=False, Ignore=False, Visible=True):
        super(DerivedAlarm, self).__init__('Derived', Audio, MinNotifyInterval, NotifyTimeout, MuteOn, Ignore, Visible)
        self.Method = Method

    def __repr__(self):
        retVal = super(DerivedAlarm, self).__repr__()
        retVal += " Method=%s" % self.Method
        return retVal

    def isAlarm(self, identifier, importedObject):
        if self.Ignore:
            return False
        else:
            return eval('importedObject.%s()' % self.Method)

def AnalogSVConstructor(loader, node):
    fields = loader.construct_mapping(node)
#    print 'AnalogSVConstructor ',fields
    return AnalogSV(**fields)

def DigitalSVConstructor(loader, node):
    fields = loader.construct_mapping(node)
#    print 'DigitalSVConstructor ',fields
    return DigitalSV(**fields)

def AnalogAlarmConstructor(loader, node):
    fields = loader.construct_mapping(node)
#    print 'AnalogAlarmConstructor ',fields
    return AnalogAlarm(**fields)

def DigitalAlarmConstructor(loader, node):
    fields = loader.construct_mapping(node)
#    print 'DigitalAlarmConstructor ',fields
    return DigitalAlarm(**fields)

def DerivedAlarmConstructor(loader, node):
    fields = loader.construct_mapping(node)
#    print 'DerivedAlarmConstructor ',fields
    return DerivedAlarm(**fields)

class AlarmKeyError(Exception):
    pass

class StatusVarConfig:

    def __init__(self, filename, persistDatafileLock, logger):
 
        self.configFromFile = {}
        self.configGen2 = {}
        self.configID = {}
        self.logger = logger
        self.lock = threading.RLock()
        self.persistConfigDataKey = 'configAlarms'
        self.persistDatafileLock = persistDatafileLock

        yaml.add_constructor('!AnalogSV', AnalogSVConstructor)
        yaml.add_constructor('!DigitalSV', DigitalSVConstructor)
        yaml.add_constructor('!AnalogAlarm', AnalogAlarmConstructor)
        yaml.add_constructor('!DigitalAlarm', DigitalAlarmConstructor)
        yaml.add_constructor('!DerivedAlarm', DerivedAlarmConstructor)

        self.loadSvConfig(filename)

    def addConfig(self, fname, newConfig, existConfig):
        for key in newConfig:
            newValue = newConfig[key]
            if key in existConfig:
                existValue = existConfig[key]
                if type(newValue) == list and type(existValue) == list:
                    for item in newValue:
                        existConfig[key].append(item)
                elif type(newValue) == list and type(existValue) != list:
                    raise Exception('Configuration for %s read from %s is a list but existing configuration is not a list' % (key, fname))
                elif type(newValue) != list and type(existValue) == list:
                    raise Exception('Configuration for %s read from %s is not a list but existing configuration is a list' % (key, fname))
                elif type(newValue) == dict and type(existValue) == dict:
                    self.addConfig(fname, newValue, existValue)
                elif type(newValue) == dict and type(existValue) != dict:
                    raise Exception('Configuration for %s read from %s is a dict but existing configuration is not a dict' % (key, fname))
                elif type(newValue) != dict and type(existValue) == dict:
                    raise Exception('Configuration for %s read from %s is not a dict but existing configuration is a dict' % (key, fname))
                else:
                    raise Exception('Unexpected error for %s read from %s' % (key, fname))
            else:
                existConfig[key] = newValue

    def loadSvConfig(self, filename):
        # Read the status variable configuration from the YAML file(s)
        filelist = glob.glob(filename)
        if len(filelist) > 0:
            for fname in filelist:
                self.logger.info("Reading config file %s" % fname)
                with open(fname, 'r') as in_f:
                    buf = in_f.read()
                newConfig = yaml.load(buf)
                self.addConfig(fname, newConfig, self.configFromFile)
                
            # configFromFile is a dictionary reflecting the
            # hierarchical structure of the YAML file. However, it
            # will be much more convenient if we create a
            # configuration attribute that is a dictionary indexed
            # using the Gen2 status aliases as the keys because, in
            # general, we will access the status variables by their
            # Gen2 aliases.
            self.configToGen2()
            # Examine each status variable to make sure that the
            # Analog Alarms have the correct dictionary keys. If there
            # are any errors, an exception will be thrown. We check
            # the keys now so that we don't have to check them later
            # on every time we get a status update.
            self.checkAlarmKeys()
            # It will also be convenient to have a dictionary indexed
            # by the ID's.
            self.configToID()
        else:
            raise Exception('File(s) not found: %s' % filename)
        self.logger.debug('StatusVarConfig.configFromFile is %s' % self.configFromFile)

    def buildGen2Config(self, dictionary, path, depth):
        for key in dictionary:
            if depth == 0:
                path = key
            else:
                path += '.' + key 
            value = dictionary[key]
            if type(value) == list:
                for listItem in value:
                    listItem.path = path
                    if listItem.Gen2Alias:
                        Gen2Alias = listItem.Gen2Alias
                        if Gen2Alias not in self.configGen2:
                            self.configGen2[Gen2Alias] = {}
                        Gen2AliasModifier = listItem.Gen2AliasModifier
                        if Gen2AliasModifier == None:
                            self.configGen2[Gen2Alias]['NoMod'] = listItem
                        else:
                            self.configGen2[Gen2Alias][Gen2AliasModifier] = listItem
            elif type(value) == dict:
                self.buildGen2Config(value, path, depth + 1)

    def configToGen2(self):
        self.configGen2 = {}
        self.buildGen2Config(self.configFromFile, '', 0)

    def buildIDConfig(self, dictionary, path, level):
        for key in dictionary:
            if level == 1:
                path = key
            else:
                path += '.' + key 
            value = dictionary[key]
            if type(value) == list:
                for listItem in value:
                    listItem.path = path
                    ID = listItem.ID
                    self.configID[ID] = listItem

            elif type(value) == dict:
                self.buildIDConfig(value, path, level + 1)

    def configToID(self):
        self.configID = {}
        self.buildIDConfig(self.configFromFile, '', 1)

    def buildGen2AliasDict(self, dictionary):
        for key in dictionary:
            value = dictionary[key]
            if type(value) == list:
                for listItem in value:
                    if listItem.Gen2Alias:
                        Gen2Alias = listItem.Gen2Alias
                        self.gen2AliasDict[Gen2Alias] = None
            elif type(value) == dict:
                self.buildGen2AliasDict(value)

    def getGen2AliasDict(self):
        self.gen2AliasDict = {}
        self.buildGen2AliasDict(self.configFromFile)
        return self.gen2AliasDict

    def checkAlarmKeys(self):
        badKeys = {}
        for gen2Alias in self.configGen2:
            svConfigItem = self.configGen2[gen2Alias]
            for gen2AliasModifier in svConfigItem:
                svItem = svConfigItem[gen2AliasModifier]
                if svItem.Alarm:
                    for key in svItem.Alarm:
                        alarm = svItem.Alarm[key]
                        if alarm.Type == 'Analog' and \
                                not('hi' in key.lower() or 'lo' in key.lower()):
                            badKeys[gen2Alias] = key
        if len(badKeys) > 0:
            self.logger.error('Bad Alarm keys %s' % badKeys)
            raise AlarmKeyError('One or more keys in the Alarm definitions are bad: must have either hi or lo in the key name')

    def loadSavedConfig(self, filename):
        configAlarms = None
        with self.persistDatafileLock:
            try:
                self.logger.info('Opening alarm_handler config for loading %s...' % filename)  
                persistData = shelve.open(filename)
            except anydbm.error,e:
                message = 'Error creating or opening %s %s' % (filename,str(e))
                self.logger.error(message)
                raise Exception(message)

            try:
                configAlarms = persistData[self.persistConfigDataKey]
            except KeyError, e:
                self.logger.warn('Warning %s key not found in filename %s' % (str(e), filename))
            finally:
                self.logger.info('Closing alarm_handler config after loading')
                persistData.close()

        if configAlarms:
            for ID in configAlarms:
                if ID in self.configID:
                    configAlarmItem = configAlarms[ID]
                    if configAlarmItem.Alarm:
                        for severity in configAlarmItem.Alarm:
                            self.configID[ID].Alarm[severity].MuteOn['User'] = configAlarmItem.Alarm[severity].MuteOn['User']
                            self.configID[ID].Alarm[severity].Ignore = configAlarmItem.Alarm[severity].Ignore
                else:
                    self.logger.info('Ignoring ID %s from saved config file' % ID)

    def getAlarmAudio(self, alarmState, ID = None):
        svConfigItem = None
        if ID:
            try:
                svConfigItem = self.configID[ID]
            except:
                raise IDError('ID %s does not exist in StatusVarConfig.configID' % ID)
            
        if alarmState == 'Ok':
            audioFilename = None
        elif alarmState in svConfigItem.Alarm:
            audioFilename = svConfigItem.Alarm[alarmState].Audio
        else:
            audioFilename = None

        if audioFilename != None and not audioFilename.startswith('/'):
            audioFilename = os.path.join(audiofileDir, audioFilename)

        return audioFilename

    def getMuteOnState(self, alarmState, ID = None, Type = None):
        svConfigItem = None
        if ID:
            try:
                svConfigItem = self.configID[ID]
            except:
                raise IDError('ID %s does not exist in StatusVarConfig.configID' % ID)
        if alarmState == 'Ok':
            muteOn = False
        elif alarmState in svConfigItem.Alarm:
            alarm = svConfigItem.Alarm[alarmState]
            if Type:
                with self.lock:
                    muteOn = alarm.MuteOn[Type]
            else:
                with self.lock:
                    muteOn = alarm.MuteOn['Config'] or alarm.MuteOn['User']
        else:
            muteOn = False

        return muteOn

    def setMuteOnState(self, ID, severity, state, Type = None):
        if ID in self.configID:
            svConfigItem = self.configID[ID]
            if severity in svConfigItem.Alarm:
                with self.lock:
                    svConfigItem.Alarm[severity].MuteOn[Type] = state
            else:
                raise Exception('Severity %s not found for ID %s' % (severity, ID))
        else:
            raise Exception('ID %s not found' % ID)

    def muteOn(self, ID, severity, Type = None):
        try:
            self.setMuteOnState(ID, severity, True, Type)
            return 0
        except Exception, e:
            return str(e)

    def muteOff(self, ID, severity, Type = None):
        try:
            self.setMuteOnState(ID, severity, False, Type)
            return 0
        except Exception, e:
            return str(e)

    def getVisibleState(self, alarmState, ID = None):
        svConfigItem = None
        if ID:
            try:
                svConfigItem = self.configID[ID]
            except:
                raise IDError('ID %s does not exist in StatusVarConfig.configID' % ID)
        if alarmState == 'Ok':
            visible = True
        elif alarmState in svConfigItem.Alarm:
            visible = svConfigItem.Alarm[alarmState].Visible
        else:
            visible = False

        return visible

    def setIgnoreAlarmState(self, ID, severity, state):
        if ID in self.configID:
            svConfigItem = self.configID[ID]
            if severity in svConfigItem.Alarm:
                with self.lock:
                    svConfigItem.Alarm[severity].Ignore = state
            else:
                raise Exception('Severity %s not found for ID %s' % (severity, ID))
        else:
            raise Exception('ID %s not found' % ID)

    def startIgnoreAlarm(self, ID, severity):
        try:
            self.setIgnoreAlarmState(ID, severity, True)
            return 0
        except Exception, e:
            return str(e)

    def stopIgnoreAlarm(self, ID, severity):
        try:
            self.setIgnoreAlarmState(ID, severity, False)
            return 0
        except Exception, e:
            return str(e)

    def dumpSvConfigItem(self, ID):
        if ID in self.configID:
            return str(self.configID[ID])
        else:
            return 'ID %s not found' % ID

    def getConfigAlarms(self):
        configAlarms = {}
        for ID in self.configID:
            svConfigItem = self.configID[ID]
            if svConfigItem.Alarm:
                configAlarms[ID] = StatusVar(ID, svConfigItem.Name, svConfigItem.Type, Alarm=svConfigItem.Alarm)
        return configAlarms

    def saveConfig(self, filename):
        with self.persistDatafileLock:
            try:
                self.logger.info('Opening alarm_handler config for saving %s...' % filename)   
                persistData = shelve.open(filename)
            except anydbm.error,e:
                message = 'Error creating or opening %s %s' % (filename,str(e))
                self.logger.error(message)
                raise Exception(message)

            with self.lock:
                try:
                    persistData[self.persistConfigDataKey] = self.getConfigAlarms()
                finally:
                    self.logger.info('Closing alarm_handler config after saving')
                    persistData.close()

        return 0

def main(options, args):

    import remoteObjects as ro
    logger = ro.nullLogger()

    dummyDatafileLock = None

    svConfig = StatusVarConfig(options.configfile, dummyDatafileLock, logger)
    gen2AliasDict = svConfig.getGen2AliasDict()
    print '\nconfigFromFile is ',svConfig.configFromFile
    print '\ngen2AliasDict is ',gen2AliasDict
    print '\nconfigGen2 is ',svConfig.configGen2
    print '\nconfigID is ',svConfig.configID

if __name__=='__main__':

    from optparse import OptionParser

    # Default alarm configuration file
    try:
        pyhome = os.environ['PYHOME']
        cfgDir = os.path.join(pyhome, 'cfg', 'alarm')
    except:
        cfgDir = '.'
    default_alarm_cfg_file = os.path.join(cfgDir, '*.yml')

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))

    optprs.add_option("-f", "--configfile", dest="configfile", default=default_alarm_cfg_file,
                      help="Specify configuration file")
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")

    (options, args) = optprs.parse_args(sys.argv[1:])

    # Are we debugging this?
    if options.debug:
        import pdb

        pdb.run('main(options, args)')

    # Are we profiling this?
    elif options.profile:
        import profile

        print "%s profile:" % sys.argv[0]
        profile.run('main(options, args)')

    else:
        main(options, args)

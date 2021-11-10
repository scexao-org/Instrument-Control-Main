#
# DellPowerGroup.py -- Classes to facilitate reading computer status
# from Dell's OpenManage Server Administrator (OMSA) software. We use
# SNMP (Simple Network Management Protocol) messages to communicate
# with the OMSA. The classes in this file are designed to get
# information from the OMSA's Power Group, whose top-level OID is
# 1.3.6.1.4.1.674.10892.1.600.
#
# For more information on the Dell OMSA Power Group, see:
# http://support.dell.com/support/edocs/software/svradmin/6.5/en/SNMP/HTML/snmpc9.htm
#
# See also the DellOMSA.py file for classes used by this file.
#
# Russell Kackley - 17 May 2011
#
import socket
import re
from DellOMSA import *

class DellPowerSupplyStateCapabilitiesUnique(DellOMSAStateType):
    """
    The DellPowerSupplyStateCapabilitiesUnique class implements the
    data values from Table 9-1 in the Dell OMSA Reference Guide -
    Power Group
    """
    okStates = ('onlineCapable')
    states = {
        1:  'unknown',
        2:  'onlineCapable',
        4:  'notReadyCapable'
        };
										
class DellPowerSupplyStateSettingsUnique(DellOMSAStateType):
    """
    The DellPowerSupplyStateSettingsUnique class implements the data
    values from Table 9-2 in the Dell OMSA Reference Guide - Power
    Group
    """
    okStates = ('acPowerAndSwitchAreOnPowerSupplyIsOnIsOkAndOnline')
    states = {
        1:   'unknown',
        2:   'online',
        4:   'notReady',
        8:   'fanFailure',
        10:  'onlineAndFanFailure',
        16:  'powerSupplyIsON',
        32:  'powerSupplyIsOk',
        64:  'acSwitchIsON',
        66:  'onlineandAcSwitchIsON',
        128: 'acPowerIsON',
        130: 'onlineAndAcPowerIsON',
        210: 'onlineAndPredictiveFailure',
        242: 'acPowerAndSwitchAreOnPowerSupplyIsOnIsOkAndOnline'
        };
										
class DellPowerSupplySensorState(DellOMSAStateType):
    """
    The DellPowerSupplySensorState class implements the data values
    from Table 9-4 in the Dell OMSA Reference Guide - Power Group
    """
    okStates = ('presenceDetected')
    states = {
        1:  'presenceDetected',
        2:  'psFailureDetected',
        4:  'predictiveFailure',
        8:  'psACLost',
        16: 'acLostOrOutOfRange',
        32: 'acOutOfRangeButPresent',
        64: 'configurationError'
        };
										
class DellVoltageType(DellOMSAStateType):
    """
    The DellVoltageType class implements the data values from Table
    9-6 in the Dell OMSA Reference Guide - Power Group
    """
    states = {
        1:  'voltageProbeTypeIsOther',
        2:  'voltageProbeTypeIsUnknown',
        3:  'voltageProbeTypeIs1Point5Volt',
        4:  'voltageProbeTypeIs3Point3volt',
        5:  'voltageProbeTypeIs5Volt',
        6:  'voltageProbeTypeIsMinus5Volt',
        7:  'voltageProbeTypeIs12Volt',
        8:  'voltageProbeTypeIsMinus12Volt',
        9:  'voltageProbeTypeIsIO',
        10: 'voltageProbeTypeIsCore',
        11: 'voltageProbeTypeIsFLEA',
        12: 'voltageProbeTypeIsBattery',
        13: 'voltageProbeTypeIsTerminator',
        14: 'voltageProbeTypeIs2Point5Volt',
        15: 'voltageProbeTypeIsGTL',
        16: 'voltageProbeTypeIsDiscrete'
        };

class DellVoltageDiscreteReading(DellOMSAStateType):
    """
    The DellVoltageDiscreteReading class implements the data values
    from Table 9-7 in the Dell OMSA Reference Guide - Power Group
    """
    okStates = ('voltageIsGood')
    states = {
        1:  'voltageIsGood',
        2:  'voltageIsBad'
        };
										
class DellAmperageType(DellOMSAStateType):
    """
    The DellAmperageType class implements the data values from Table
    9-8 in the Dell OMSA Reference Guide - Power Group
    """
    states = {
        1:  'amperageProbeTypeIsOther',
        2:  'amperageProbeTypeIsUnknown',
        3:  'amperageProbeTypeIs1Point5Volt',
        4:  'amperageProbeTypeIs3Point3volt',
        5:  'amperageProbeTypeIs5Volt',
        6:  'amperageProbeTypeIsMinus5Volt',
        7:  'amperageProbeTypeIs12Volt',
        8:  'amperageProbeTypeIsMinus12Volt',
        9:  'amperageProbeTypeIsIO',
        10: 'amperageProbeTypeIsCore',
        11: 'amperageProbeTypeIsFLEA',
        12: 'amperageProbeTypeIsBattery',
        13: 'amperageProbeTypeIsTerminator',
        14: 'amperageProbeTypeIs2Point5Volt',
        15: 'amperageProbeTypeIsGTL',
        16: 'amperageProbeTypeIsDiscrete',
        23: 'amperageProbeTypeIsPowerSupplyAmps',
        24: 'amperageProbeTypeIsPowerSupplyWatts',
        25: 'amperageProbeTypeIsSystemAmps',
        26: 'amperageProbeTypeIsSystemWatts'
        };

class DellAmperageDiscreteReading(DellOMSAStateType):
    """
    The DellAmperageDiscreteReading class implements the data values
    from Table 9-9 in the Dell OMSA Reference Guide - Power Group
    """
    okStates = ('amperageIsGood')
    states = {
        1:  'amperageIsGood',
        2:  'amperageIsBad'
        };
										
class DellBatteryReading(DellOMSAStateType):
    """
    The DellBatteryReading class implements the data values from Table
    9-15 in the Dell OMSA Reference Guide - Power Group
    """
    predictiveFailure = 1
    failed = 2
    presenceDetected = 4
    okStates = ('presenceDetected_and_ok_and_predictiveOk')
    states = {
        0:  {0: 'predictiveOk',        1:  'predictiveFailure'},
        1:  {0: 'ok',                  1: 'failed'},
        2:  {0: 'presenceNotDetected', 1: 'presenceDetected'}
        };
    def __init__(self, state):
        self.state = state
										
    def __str__(self):
        retString = ''
        if self.state & self.presenceDetected:
            retString = self.states[2][1]
        else:
            retString = self.states[2][0]
            
        if self.state & self.failed:
            retString += '_and_' + self.states[1][1]
        else:
            retString += '_and_' + self.states[1][0]
            
        if self.state & self.predictiveFailure:
            retString += '_and_' + self.states[0][1]
        else:
            retString += '_and_' + self.states[0][0]
            
        return retString

class PowerGroup(DellOMSAGroup):
    """
    The PowerGroup class is a container that holds the Dell OMSA Power
    Group objects
    """
    OID = DellChassisOID.OID + '.600'
    logFilename = 'PowerGroup'
    groupName = 'Power'

    def __init__(self, connection):
        super(PowerGroup, self).__init__(connection)
        self.contents = {
            'PowerUnitTable':     PowerUnitTable(connection),
            'PowerSupplyTable':   PowerSupplyTable(connection),
            'VoltageProbeTable':  VoltageProbeTable(connection),
            'AmperageProbeTable': AmperageProbeTable(connection),
            'BatteryTable':       BatteryTable(connection)
            }

    def __str__(self):
        retString = super(PowerGroup, self).__str__()
        return retString

class PowerUnitTable(DellOMSATable):
    """
    The PowerUnitTable class is a container that holds the Dell OMSA
    Power Unit objects
    """
    OID = PowerGroup.OID + '.10.1'
    tableName = 'Power Unit'

    def __init__(self, connection):
        super(PowerUnitTable, self).__init__(connection)
        self.contents = {
            'PowerUnitStateCapabilities': PowerUnitStateCapabilities(connection),
            'PowerUnitStateSettings':     PowerUnitStateSettings(connection),
            'PowerUnitRedundancyStatus':  PowerUnitRedundancyStatus(connection),
            'PowerUnitName':              PowerUnitName(connection),
            'PowerUnitStatus':            PowerUnitStatus(connection)
            }

    def __str__(self):
        retString = super(PowerUnitTable, self).__str__()
        i = 0
        for n in self.contents['PowerUnitName'].value:
            ss = self.contents['PowerUnitStateSettings'].value[i]
            if str(ss) == 'enabled':
                retString += '\n%s: Settings: %s Redundancy Status: %s Status: %s '  % \
                    (n,
                     ss,
                     self.contents['PowerUnitRedundancyStatus'].value[i],
                     self.contents['PowerUnitStatus'].value[i])
            else:
                retString += '\n%s: Settings: %s' % (n, ss)
            i += 1
        return retString

class PowerUnitStateCapabilities(DellOMSAState):
    OID = PowerUnitTable.OID + '.3.1'
    stateClass = DellStateCapabilities

class PowerUnitStateSettings(DellOMSAState):
    OID = PowerUnitTable.OID + '.4.1'
    stateClass = DellStateSettings

class PowerUnitRedundancyStatus(DellOMSAState):
    OID = PowerUnitTable.OID + '.5.1'
    stateClass = DellStatusRedundancy

class PowerUnitName(DellOMSALocationName):
    OID = PowerUnitTable.OID + '.7.1'

class PowerUnitStatus(DellOMSAState):
    OID = PowerUnitTable.OID + '.8.1'
    stateClass = DellStatus

class PowerSupplyTable(DellOMSATable):
    """
    The PowerSupplyTable class is a container that holds the Dell OMSA
    Power Supply objects
    """
    OID = PowerGroup.OID + '.12.1'
    tableName = 'Chassis Power Supply'

    def __init__(self, connection):
        super(PowerSupplyTable, self).__init__(connection)
        self.contents = {
            'PowerSupplyStateSettingsUnique': PowerSupplyStateSettingsUnique(connection),
            'PowerSupplyStatus':       PowerSupplyStatus(connection),
            'PowerSupplyOutputWatts':  PowerSupplyOutputWatts(connection),
            'PowerSupplyLocationName': PowerSupplyLocationName(connection),
            'PowerSupplySensorState':  PowerSupplySensorState(connection)
            }

    def __str__(self):
        retString = super(PowerSupplyTable, self).__str__()
        i = 0
        for n in self.contents['PowerSupplyLocationName'].value:
            retString += '\n%s: Settings: %s Status: %s Output: %s State: %s'  % \
                (n,
                 self.contents['PowerSupplyStateSettingsUnique'].value[i],
                 self.contents['PowerSupplyStatus'].value[i],
                 self.contents['PowerSupplyOutputWatts'].value[i],
                 self.contents['PowerSupplySensorState'].value[i])
            i += 1
        return retString

class PowerSupplyStateCapabilitiesUnique(DellOMSAState):
    OID = PowerSupplyTable.OID + '.3.1'
    stateClass = DellPowerSupplyStateCapabilitiesUnique

class PowerSupplyStateSettingsUnique(DellOMSAState):
    OID = PowerSupplyTable.OID + '.4.1'
    stateClass = DellPowerSupplyStateSettingsUnique

class PowerSupplyStatus(DellOMSAState):
    OID = PowerSupplyTable.OID + '.5.1'
    stateClass = DellStatus

class PowerSupplyOutputWatts(DellOMSAReading):
    OID = PowerSupplyTable.OID + '.6.1'
    conversion = 1. / 10.
    units = 'watts'

class PowerSupplyLocationName(DellOMSALocationName):
    OID = PowerSupplyTable.OID + '.8.1'

class PowerSupplySensorState(DellOMSAState):
    OID = PowerSupplyTable.OID + '.11.1'
    stateClass = DellPowerSupplySensorState

class VoltageProbeTable(DellOMSATable):
    """
    The VoltageProbeTable class is a container that holds the Dell
    OMSA Voltage Probe objects
    """
    OID = PowerGroup.OID + '.20.1'
    tableName = 'Voltage Probe'
    locationNamePattern = re.compile('PS\s*(\d*) Voltage')

    def __init__(self, connection):
        super(VoltageProbeTable, self).__init__(connection)
        self.contents = {
            'VoltageProbeStateCapabilities': VoltageProbeStateCapabilities(connection),
            'VoltageProbeStateSettings':     VoltageProbeStateSettings(connection),
            'VoltageProbeStatus':            VoltageProbeStatus(connection),
            'VoltageProbeReading':           VoltageProbeReading(connection),
            'VoltageProbeType':              VoltageProbeType(connection),
            'VoltageProbeLocationName':      VoltageProbeLocationName(connection),
            'VoltageProbeDiscreteReading':   VoltageProbeDiscreteReading(connection)
            }

    def __str__(self):
        retString = super(VoltageProbeTable, self).__str__()
        i = 0
        iDiscrete = 0
        iOther = 0
        for n in self.contents['VoltageProbeLocationName'].value:
            ss = self.contents['VoltageProbeStateSettings'].value[i]
            if str(ss) == 'enabled':
                if str(self.contents['VoltageProbeType'].value[i]) == 'voltageProbeTypeIsDiscrete':        
                    retString += '\n%s: Settings: %s Status: %s Reading: %s '  % \
                        (n,
                         ss,
                         self.contents['VoltageProbeStatus'].value[i],
                         self.contents['VoltageProbeDiscreteReading'].value[iDiscrete])
                    iDiscrete += 1
                else:
                    retString += '\n%s: Settings: %s Status: %s Reading: %s'  % \
                        (n,
                         ss,
                         self.contents['VoltageProbeStatus'].value[i],
                         self.contents['VoltageProbeReading'].value[iOther])
                    iOther += 1
            else:
                retString += '\n%s: Settings: %s' % (n, ss)
            i += 1
        return retString

    def as_dict(self):
        """
        Create a dictionary from the VoltageProbeTable contents with
        the VoltageProbeLocationName as the key. We do this because
        we need to sort the table based on the location names and
        dictionaries are easy to sort in python.
        """
        probes = {}
        i = 0
        iDiscrete = 0
        iOther = 0
        for n in self.contents['VoltageProbeLocationName'].value:
            probes[n] = {}
            for key in self.contents:
                # We have to be careful here when the key is either
                # VoltageProbeDiscreteReading and VoltageProbeReading
                # because voltage probes whose type is
                # voltageProbeTypeIsDiscrete will have a value in
                # VoltageProbeDiscreteReading, but nothing in
                # VoltageProbeReading. Conversely, voltage probes
                # whose type is not voltageProbeTypeIsDiscrete will
                # have a value in VoltageProbeReading, but nothing in
                # VoltageProbeDiscreteReading.
                if key in ('VoltageProbeDiscreteReading', 'VoltageProbeReading'):
                    if key == 'VoltageProbeDiscreteReading' and \
                            str(self.contents['VoltageProbeType'].value[i]) == 'voltageProbeTypeIsDiscrete':
                        probes[n][key] = str(self.contents['VoltageProbeDiscreteReading'].value[iDiscrete])
                        iDiscrete += 1
                    elif key == 'VoltageProbeReading' and \
                            str(self.contents['VoltageProbeType'].value[i]) != 'voltageProbeTypeIsDiscrete':
                        probes[n][key] = str(self.contents['VoltageProbeReading'].value[iOther])
                        iOther += 1
                else:
                    probes[n][key] = str(self.contents[key].value[i])
            i += 1
        return probes

    def getPSNum(self, locationName):
        """                                                                   
        Parse the location name and return the power supply
        number. Return a nonsense power supply number if we have
        trouble parsing the location name.
        """
        try:
            psNum = self.locationNamePattern.match(locationName).group(1)
        except AttributeError:
            psNum = 997
        except IndexError:
            psNum = 998
        except Exception:
            psNum = 999
        return psNum

    def munin_config_volts(self):
        print 'graph_title %s Power Supply Input Voltage' % (socket.gethostname())
        print 'graph_args --base 1000 -l 0'
        print 'graph_vlabel Voltage (volts)'
        print 'graph_category Chassis'
        print 'graph_info This graph shows the input voltage of all chassis power supplies.'
        print 'graph_period second'
        devices = self.as_dict()
        for key in sorted(devices):
            if devices[key]['VoltageProbeType'] != 'voltageProbeTypeIsDiscrete' and \
                    devices[key]['VoltageProbeStateSettings'] == 'enabled':
                psNum = self.getPSNum(key)
                print 'ps_%s_volts.label %s' % (psNum, key)

    def munin_report_volts(self):
        devices = self.as_dict()
        for key in sorted(devices):
            if devices[key]['VoltageProbeType'] != 'voltageProbeTypeIsDiscrete' and \
                    devices[key]['VoltageProbeStateSettings'] == 'enabled':
                psNum = self.getPSNum(key)
                value = devices[key]['VoltageProbeReading'].rstrip(' volts')
                print 'ps_%s_volts.value %s' % (psNum, value)

class VoltageProbeStateCapabilities(DellOMSAState):
    OID = VoltageProbeTable.OID + '.3.1'
    stateClass = DellStateCapabilities

class VoltageProbeStateSettings(DellOMSAState):
    OID = VoltageProbeTable.OID + '.4.1'
    stateClass = DellStateSettings

class VoltageProbeStatus(DellOMSAState):
    OID = VoltageProbeTable.OID + '.5.1'
    stateClass = DellStatusProbe

class VoltageProbeReading(DellOMSAReading):
    OID = VoltageProbeTable.OID + '.6.1'
    conversion = 1. / 1000.
    units = 'volts'

class VoltageProbeType(DellOMSAProbeType):
    OID = VoltageProbeTable.OID + '.7.1'
    stateClass = DellVoltageType

class VoltageProbeLocationName(DellOMSALocationName):
    OID = VoltageProbeTable.OID + '.8.1'

class VoltageProbeDiscreteReading(DellOMSAState):
    OID = VoltageProbeTable.OID + '.16.1'
    stateClass = DellVoltageDiscreteReading

class AmperageProbeTable(DellOMSATable):
    """
    The AmperageProbeTable class is a container that holds the Dell
    OMSA Amperage Probe objects
    """
    OID = PowerGroup.OID + '.30.1'
    tableName = 'Amperage Probe'
    locationNamePattern = re.compile('PS\s*(\d*) Current')

    def __init__(self, connection):
        super(AmperageProbeTable, self).__init__(connection)
        self.contents = {
            'AmperageProbeStateCapabilities': AmperageProbeStateCapabilities(connection),
            'AmperageProbeStateSettings':     AmperageProbeStateSettings(connection),
            'AmperageProbeStatus':            AmperageProbeStatus(connection),
            'AmperageProbeReading':           AmperageProbeReading(connection),
            'AmperageProbeType':              AmperageProbeType(connection),
            'AmperageProbeLocationName':      AmperageProbeLocationName(connection)
            }

    def update(self):
        super(AmperageProbeTable, self).update()
        # AmperageProbeReading values could be in amps or
        # watts. AmperageProbeType tells us which they are. Set
        # AmperageProbeReading attributes to correct values based on
        # what AmperageProbeType tells us.
        i = 0
        for r in self.contents['AmperageProbeReading'].value:
            t = self.contents['AmperageProbeType'].value[i]
            if str(t) == 'amperageProbeTypeIsPowerSupplyAmps':
                # Ouput from Dell OMSA is tenths of amps. Convert
                # to the more standard amps.
                r.value /= 10
                r.units = 'amps'
            elif str(t) == 'amperageProbeTypeIsSystemWatts':
                # Output from Dell OMSA is watts. Set unit string
                # to watts.
                r.units = 'watts'
            i += 1

    def __str__(self):
        retString = super(AmperageProbeTable, self).__str__()
        i = 0
        iDiscrete = 0
        iOther = 0
        for n in self.contents['AmperageProbeLocationName'].value:
            ss = self.contents['AmperageProbeStateSettings'].value[i]
            if str(ss) == 'enabled':
                if str(self.contents['AmperageProbeType'].value[i]) == 'amperageProbeTypeIsDiscrete':
                
                    retString += '\n%s: Settings: %s Status: %s Reading: %s '  % \
                        (n,
                         ss,
                         self.contents['AmperageProbeStatus'].value[i],
                         self.contents['AmperageProbeDiscreteReading'].value[iDiscrete])
                    iDiscrete += 1
                else:
                    retString += '\n%s: Settings: %s Status: %s Reading: %s'  % \
                        (n,
                         ss,
                         self.contents['AmperageProbeStatus'].value[i],
                         self.contents['AmperageProbeReading'].value[iOther])
                    iOther += 1
            else:
                retString += '\n%s: Settings: %s' % (n, ss)
            i += 1
        return retString
 
    def as_dict(self):
        """
        Create a dictionary from the AmperageProbeTable contents with
        the AmperageProbeLocationName as the key. We do this because
        we need to sort the table based on the location names and
        dictionaries are easy to sort in python.
        """
        probes = {}
        i = 0
        for n in self.contents['AmperageProbeLocationName'].value:
            probes[n] = {}
            for key in self.contents:
                probes[n][key] = str(self.contents[key].value[i])
            i += 1
        return probes

    def getPSNum(self, locationName):
        """
        Parse the location name and return the power supply
        number. Return a nonsense power supply number if we have
        trouble parsing the location name.
        """
        try:
            psNum = self.locationNamePattern.match(locationName).group(1)
        except AttributeError:
            psNum = 997
        except IndexError:
            psNum = 998
        except Exception:
            psNum = 999
        return psNum

    def munin_config_amps(self):
        print 'graph_title %s Power Supply Output Current' % (socket.gethostname())
        print 'graph_args --base 1000 -l 0'
        print 'graph_vlabel Current (amps)'
        print 'graph_category Chassis'
        print 'graph_info This graph shows the output current of all chassis power supplies.'
        print 'graph_period second'
        devices = self.as_dict()
        for key in sorted(devices):
            if devices[key]['AmperageProbeType'] == 'amperageProbeTypeIsPowerSupplyAmps' and \
                    devices[key]['AmperageProbeStateSettings'] == 'enabled':
                psNum = self.getPSNum(key)
                print 'ps_%s_amps.label %s' % (psNum, key)

    def munin_report_amps(self):
        devices = self.as_dict()
        for key in sorted(devices):
            if devices[key]['AmperageProbeType'] == 'amperageProbeTypeIsPowerSupplyAmps' and \
                    devices[key]['AmperageProbeStateSettings'] == 'enabled':
                psNum = self.getPSNum(key)
                value = devices[key]['AmperageProbeReading'].rstrip(' amps')
                print 'ps_%s_amps.value %s' % (psNum, value)

    def munin_config_watts(self):
        print 'graph_title %s Power Consumption' % (socket.gethostname())
        print 'graph_args --base 1000 -l 0'
        print 'graph_vlabel Power (watts)'
        print 'graph_category Chassis'
        print 'graph_info This graph shows the power consumption of the system board.'
        print 'graph_period second'
        devices = self.as_dict()
        i = 0
        for key in sorted(devices):
            if devices[key]['AmperageProbeType'] == 'amperageProbeTypeIsSystemWatts' and \
                    devices[key]['AmperageProbeStateSettings'] == 'enabled':
                print 'pwr_cnsmp_%s.label %s' % (i, key)
                i += 1

    def munin_report_watts(self):
        devices = self.as_dict()
        i = 0
        for key in sorted(devices):
            if devices[key]['AmperageProbeType'] == 'amperageProbeTypeIsSystemWatts' and \
                    devices[key]['AmperageProbeStateSettings'] == 'enabled':
                value = devices[key]['AmperageProbeReading'].rstrip(' watts')
                print 'pwr_cnsmp_%s.value %s' % (i, value)
                i += 1

class AmperageProbeStateCapabilities(DellOMSAState):
    OID = AmperageProbeTable.OID + '.3.1'
    stateClass = DellStateCapabilities

class AmperageProbeStateSettings(DellOMSAState):
    OID = AmperageProbeTable.OID + '.4.1'
    stateClass = DellStateSettings

class AmperageProbeStatus(DellOMSAState):
    OID = AmperageProbeTable.OID + '.5.1'
    stateClass = DellStatusProbe

class AmperageProbeReading(DellOMSAReading):
    OID = AmperageProbeTable.OID + '.6.1'
    conversion = 1.
    units = 'unknown'

class AmperageProbeType(DellOMSAProbeType):
    OID = AmperageProbeTable.OID + '.7.1'
    stateClass = DellAmperageType

class AmperageProbeLocationName(DellOMSALocationName):
    OID = AmperageProbeTable.OID + '.8.1'

class AmperageProbeDiscreteReading(DellOMSAState):
    OID = AmperageProbeTable.OID + '.16.1'
    stateClass = DellAmperageDiscreteReading

class BatteryTable(DellOMSATable):
    """
    The BatteryTable class is a container that holds the Dell
    OMSA Battery Table objects
    """
    OID = PowerGroup.OID + '.50.1'
    tableName = 'Chassis Battery'

    def __init__(self, connection):
        super(BatteryTable, self).__init__(connection)
        self.contents = {
            'BatteryStateCapabilities': BatteryStateCapabilities(connection),
            'BatteryStateSettings':     BatteryStateSettings(connection),
            'BatteryStatus':            BatteryStatus(connection),
            'BatteryReading':           BatteryReading(connection),
            'BatteryLocationName':      BatteryLocationName(connection)
            }

    def __str__(self):
        retString = super(BatteryTable, self).__str__()
        i = 0
        for n in self.contents['BatteryLocationName'].value:
            ss = self.contents['BatteryStateSettings'].value[i]
            if str(ss) == 'enabled':
                retString += '\n%s: Settings: %s Status: %s Reading: %s'  % \
                        (n,
                         ss,
                         self.contents['BatteryStatus'].value[i],
                         self.contents['BatteryReading'].value[i])
                i += 1
            else:
                retString += '\n%s: Settings: %s' % (n, ss)
            i += 1
        return retString

class BatteryStateCapabilities(DellOMSAState):
    OID = BatteryTable.OID + '.3.1'
    stateClass = DellStateCapabilities

class BatteryStateSettings(DellOMSAState):
    OID = BatteryTable.OID + '.4.1'
    stateClass = DellStateSettings

class BatteryStatus(DellOMSAState):
    OID = BatteryTable.OID + '.5.1'
    stateClass = DellStatus

class BatteryReading(DellOMSAState):
    OID = BatteryTable.OID + '.6.1'
    stateClass = DellBatteryReading

class BatteryLocationName(DellOMSALocationName):
    OID = BatteryTable.OID + '.7.1'


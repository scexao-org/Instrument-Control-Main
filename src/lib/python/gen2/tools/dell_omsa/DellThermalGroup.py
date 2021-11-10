#
# DellThermalGroup.py -- Classes to facilitate reading computer status
# from Dell's OpenManage Server Administrator (OMSA) software. We use
# SNMP (Simple Network Management Protocol) messages to communicate
# with the OMSA. The classes in this file are designed to get
# information from the OMSA's Thermal Group, whose top-level OID is
# 1.3.6.1.4.1.674.10892.1.700.
#
# For more information on the Dell OMSA Thermal Group, see:
# http://support.dell.com/support/edocs/software/svradmin/6.5/en/SNMP/HTML/snmpc10.htm
#
# See also the DellOMSA.py file for classes used by this file.
#
# Russell Kackley - 17 May 2011
#
import socket
import re
from DellOMSA import *

class DellCoolingDeviceType(DellOMSAStateType):
    """
    The DellCoolingDeviceType class implements the data values from
    Table 10-1 in the Dell OMSA Reference Guide - Thermal Group
    """
    states = {
        1:  'coolingDeviceTypeIsOther',
        2:  'coolingDeviceTypeIsUnknown',
        3:  'coolingDeviceTypeIsAFan',
        4:  'coolingDeviceTypeIsABlower',
        5:  'coolingDeviceTypeIsAChipFan',
        6:  'coolingDeviceTypeIsACabinetFan',
        7:  'coolingDeviceTypeIsAPowerSupplyFan',
        8:  'coolingDeviceTypeIsAHeatPipe',
        9:  'coolingDeviceTypeIsRefrigeration',
        10: 'coolingDeviceTypeIsActiveCooling',
        11: 'coolingDeviceTypeIsPassiveCooling'
        };

class DellTemperatureProbeType(DellOMSAStateType):
    """
    The DellTemperatureProbeType class implements the data values from
    Table 10-4 in the Dell OMSA Reference Guide - Thermal Group
    """
    states = {
        1:  'temperatureProbeTypeIsOther',
        2:  'temperatureProbeTypeIsUnknown',
        3:  'temperatureProbeTypeIsAmbientESM',
        16: 'temperatureProbeTypeIsDiscrete'
        };

class ThermalGroup(DellOMSAGroup):
    """
    The ThermalGroup class is a container that holds the Dell OMSA
    Thermal Group objects
    """
    OID = DellChassisOID.OID + '.700'
    logFilename = 'ThermalGroup'
    groupName = 'Thermal'

    def __init__(self, connection):
        super(ThermalGroup, self).__init__(connection)
        self.contents = {
            'CoolingUnitTable':      CoolingUnitTable(connection),
            'CoolingDeviceTable':    CoolingDeviceTable(connection),
            'TemperatureProbeTable': TemperatureProbeTable(connection)
            }

    def __str__(self):
        retString = super(ThermalGroup, self).__str__()
        return retString

class CoolingUnitTable(DellOMSATable):
    """
    The CoolingUnitTable class is a container that holds the Dell OMSA
    Cooling Unit objects
    """
    OID = ThermalGroup.OID + '.10.1'
    tableName = 'Cooling Unit'

    def __init__(self, connection):
        super(CoolingUnitTable, self).__init__(connection)
        self.contents = {
            'CoolingUnitStateCapabilities':  CoolingUnitStateCapabilities(connection),
            'CoolingUnitStateSettings':      CoolingUnitStateSettings(connection),
            'CoolingUnitRedundancyStatus':   CoolingUnitRedundancyStatus(connection),
            'CoolingUnitName':               CoolingUnitName(connection),
            'CoolingUnitStatus':             CoolingUnitStatus(connection)
            }

    def __str__(self):
        retString = super(CoolingUnitTable, self).__str__()
        i = 0
        for n in self.contents['CoolingUnitName'].value:
            ss = self.contents['CoolingUnitStateSettings'].value[i]
            if str(ss) == 'enabled':
                retString += '\n%s: Settings: %s Redundancy Status: %s Status: %s '  % \
                    (n,
                     ss,
                     self.contents['CoolingUnitRedundancyStatus'].value[i],
                     self.contents['CoolingUnitStatus'].value[i])
            else:
                retString += '\n%s: Settings: %s' % (n, ss)
            i += 1
        return retString

class CoolingUnitStateCapabilities(DellOMSAState):
    OID = CoolingUnitTable.OID + '.3.1'
    stateClass = DellStateCapabilities

class CoolingUnitStateSettings(DellOMSAState):
    OID = CoolingUnitTable.OID + '.4.1'
    stateClass = DellStateSettings

class CoolingUnitRedundancyStatus(DellOMSAState):
    OID = CoolingUnitTable.OID + '.5.1'
    stateClass = DellStatusRedundancy

class CoolingUnitName(DellOMSALocationName):
    OID = CoolingUnitTable.OID + '.7.1'

class CoolingUnitStatus(DellOMSAState):
    OID = CoolingUnitTable.OID + '.8.1'
    stateClass = DellStatus

class CoolingDeviceTable(DellOMSATable):
    """
    The CoolingDeviceTable class is a container that holds the Dell
    OMSA Cooling Device objects
    """
    OID = ThermalGroup.OID + '.12.1'
    tableName = 'Cooling Device'
    locationNamePattern = re.compile('System Board (FAN|Fan)\s*(\d*) RPM')

    def __init__(self, connection):
        super(CoolingDeviceTable, self).__init__(connection)
        self.contents = {
            'CoolingDeviceStateCapabilities': CoolingDeviceStateCapabilities(connection),
            'CoolingDeviceStateSettings':     CoolingDeviceStateSettings(connection),
            'CoolingDeviceStatus':            CoolingDeviceStatus(connection),
            'CoolingDeviceReading':           CoolingDeviceReading(connection),
            'CoolingDeviceType':              CoolingDeviceType(connection),
            'CoolingDeviceLocationName':      CoolingDeviceLocationName(connection)
            }

    def __str__(self):
        retString = super(CoolingDeviceTable, self).__str__()
        i = 0
        for n in self.contents['CoolingDeviceLocationName'].value:
            ss = self.contents['CoolingDeviceStateSettings'].value[i]
            if str(ss) == 'enabled':
                retString += '\n%s: Settings: %s Status: %s Reading: %s'  % \
                    (n,
                     ss,
                     self.contents['CoolingDeviceStatus'].value[i],
                     self.contents['CoolingDeviceReading'].value[i])
            else:
                retString += '\n%s: Settings: %s' % (n, ss)
            i += 1
        return retString

    def as_dict(self):
        """
        Create a dictionary from the CoolingDeviceTable contents with
        the CoolingDeviceLocationName as the key. We do this because
        we need to sort the table based on the location names and
        dictionaries are easy to sort in python.
        """
        devices = {}
        i = 0
        for n in self.contents['CoolingDeviceLocationName'].value:
            devices[n] = {}
            for key in self.contents:
                devices[n][key] = str(self.contents[key].value[i])
            i += 1
        return devices

    def getFanNum(self, locationName):
        """
        Parse the location name and return the fan number. Return a
        nonsense fan number if we have trouble parsing the location
        name.
        """
        try:
            fanNum = self.locationNamePattern.match(locationName).group(2)
        except AttributeError:
            fanNum = 997
        except IndexError:
            fanNum = 998
        except Exception:
            fanNum = 999
        return fanNum

    def munin_config(self):
        print 'graph_title %s Chassis Fan Speeds' % (socket.gethostname())
        print 'graph_args --base 1000 -l 0'
        print 'graph_vlabel Speed (RPM)'
        print 'graph_category Chassis'
        print 'graph_info This graph shows the speed in RPM of all chassis fans.'
        print 'graph_period second'
        devices = self.as_dict()
        for key in sorted(devices):
            if 'Fan' in devices[key]['CoolingDeviceType'] and devices[key]['CoolingDeviceStateSettings'] == 'enabled':
                fanNum = self.getFanNum(key)
                label = key.rstrip(' RPM')
                print 'fans_%s.label %s' % (fanNum, label)

    def munin_report(self):
        devices = self.as_dict()
        for key in sorted(devices):
            if 'Fan' in devices[key]['CoolingDeviceType'] and devices[key]['CoolingDeviceStateSettings'] == 'enabled':
                fanNum = self.getFanNum(key)
                value = devices[key]['CoolingDeviceReading'].rstrip(' RPM')
                print 'fans_%s.value %s' % (fanNum, value)

class CoolingDeviceStateCapabilities(DellOMSAState):
    OID = CoolingDeviceTable.OID + '.3.1'
    stateClass = DellStateCapabilities

class CoolingDeviceStateSettings(DellOMSAState):
    OID = CoolingDeviceTable.OID + '.4.1'
    stateClass = DellStateSettings

class CoolingDeviceStatus(DellOMSAState):
    OID = CoolingDeviceTable.OID + '.5.1'
    stateClass = DellStatusProbe

class CoolingDeviceReading(DellOMSAReading):
    OID = CoolingDeviceTable.OID + '.6.1'
    conversion = 1.
    units = 'RPM'

class CoolingDeviceType(DellOMSAState):
    OID = CoolingDeviceTable.OID + '.7.1'
    stateClass = DellCoolingDeviceType

    def overallStatus(self):
        return DellOverallStatus(DellOverallStatus.okState)

class CoolingDeviceLocationName(DellOMSALocationName):
    OID = CoolingDeviceTable.OID + '.8.1'

class TemperatureProbeTable(DellOMSATable):
    """
    The TemperatureProbeTable class is a container that holds the Dell
    OMSA Temperature Probe objects
    """
    OID = ThermalGroup.OID + '.20.1'
    tableName = 'Chassis Temperature Probe'

    def __init__(self, connection):
        super(TemperatureProbeTable, self).__init__(connection)
        self.contents = {
            'TemperatureProbeStateCapabilities': TemperatureProbeStateCapabilities(connection),
            'TemperatureProbeStateSettings':     TemperatureProbeStateSettings(connection),
            'TemperatureProbeStatus':            TemperatureProbeStatus(connection),
            'TemperatureProbeReading':           TemperatureProbeReading(connection),
            'TemperatureProbeType':              TemperatureProbeType(connection),
            'TemperatureProbeLocationName':      TemperatureProbeLocationName(connection)
            }

    def __str__(self):
        retString = super(TemperatureProbeTable, self).__str__()
        i = 0
        for n in self.contents['TemperatureProbeLocationName'].value:
            ss = self.contents['TemperatureProbeStateSettings'].value[i]
            if str(ss) == 'enabled':
                retString += '\n%s: Settings: %s Status: %s Reading: %s'  % \
                        (n,
                         ss,
                         self.contents['TemperatureProbeStatus'].value[i],
                         self.contents['TemperatureProbeReading'].value[i])
            else:
                retString += '\n%s: Settings: %s' % (n, ss)
            i += 1
        return retString

    def munin_config(self):
        print 'graph_title %s Chassis Temperature Readings' % (socket.gethostname())
        print 'graph_args --base 1000 -l 0'
        print 'graph_vlabel Temperature (Deg C)'
        print 'graph_category Chassis'
        print 'graph_info This graph shows the temperature for all sensors.'
        print 'graph_period second'
        i = 0
        for n in self.contents['TemperatureProbeLocationName'].value:
            probeType = str(self.contents['TemperatureProbeType'].value[i])
            ss = self.contents['TemperatureProbeStateSettings'].value[i]
            if str(probeType) == 'temperatureProbeTypeIsAmbientESM' and str(ss) == 'enabled':
                print 'temps_%s.label %s' % (i, n)
            i += 1

    def munin_report(self):
        i = 0
        for n in self.contents['TemperatureProbeLocationName'].value:
            probeType = str(self.contents['TemperatureProbeType'].value[i])
            ss = self.contents['TemperatureProbeStateSettings'].value[i]
            if str(probeType) == 'temperatureProbeTypeIsAmbientESM' and str(ss) == 'enabled':
                value = str(self.contents['TemperatureProbeReading'].value[i]).rstrip(' deg. C')
                print 'temps_%s.value %s' % (i, value)
            i += 1

class TemperatureProbeStateCapabilities(DellOMSAState):
    OID = TemperatureProbeTable.OID + '.3.1'
    stateClass = DellStateCapabilities

class TemperatureProbeStateSettings(DellOMSAState):
    OID = TemperatureProbeTable.OID + '.4.1'
    stateClass = DellStateSettings

class TemperatureProbeStatus(DellOMSAState):
    OID = TemperatureProbeTable.OID + '.5.1'
    stateClass = DellStatusProbe

class TemperatureProbeReading(DellOMSAReading):
    OID = TemperatureProbeTable.OID + '.6.1'
    conversion = 1. / 10.
    units = 'deg. C'

class TemperatureProbeType(DellOMSAProbeType):
    OID = TemperatureProbeTable.OID + '.7.1'
    stateClass = DellTemperatureProbeType

class TemperatureProbeLocationName(DellOMSALocationName):
    OID = TemperatureProbeTable.OID + '.8.1'

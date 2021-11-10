#
# DellDeviceGroup.py -- Classes to facilitate reading computer status
# from Dell's OpenManage Server Administrator (OMSA) software. We use
# SNMP (Simple Network Management Protocol) messages to communicate
# with the OMSA. The classes in this file are designed to get
# information from the OMSA's Device Group, whose top-level OID is
# 1.3.6.1.4.1.674.10892.1.1100.
#
# For more information on the Dell OMSA Device Group, see:
# http://support.dell.com/support/edocs/software/svradmin/6.5/en/SNMP/HTML/snmpc14a.htm
#
# See also the DellOMSA.py file for classes used by this file.
#
# Russell Kackley - 23 May 2011
#
from DellOMSA import *

class DellMemoryDeviceType(DellOMSAStateType):
    """
    The DellMemoryDeviceType class implements the data values from
    Table 14-16 in the Dell OMSA Reference Guide - Device Group
    """
    states = {
        1:  'deviceTypeIsOther',
        2:  'deviceTypeIsUnknown',
        3:  'deviceTypeIsDRAM',
        4:  'deviceTypeIsEDRAM',
        5:  'deviceTypeIsVRAM',
        6:  'deviceTypeIsSRAM',
        7:  'deviceTypeIsRAM',
        8:  'deviceTypeIsROM',
        9:  'deviceTypeIsFLASH',
        10: 'deviceTypeIsEEPROM',
        11: 'deviceTypeIsFEPROM',
        12: 'deviceTypeIsEPROM',
        13: 'deviceTypeIsCDRAM',
        14: 'deviceTypeIs3DRAM',
        15: 'deviceTypeIsSDRAM',
        16: 'deviceTypeIsSGRAM',
        17: 'deviceTypeIsRDRAM',
        18: 'deviceTypeIsDDR',
        19: 'deviceTypeIsDDR2',
        20: 'deviceTypeIsDDR2FBDIMM',
        24: 'deviceTypeIsDDR3',
        25: 'deviceTypeIsFBD2'
       };

class DellMemoryDeviceFailureModes(DellOMSAStateType):
    """
    The DellMemoryDeviceFailureModes class implements the data values from
    Table 14-19 in the Dell OMSA Reference Guide - Device Group
    """
    noFaults = 0
    eccSingleBitCorrectionWarningRate = 1
    eccSingleBitCorrectionFailureRate = 2
    eccMultiBitFault = 4
    eccSingleBitCorrectionLoggingDisabled = 8
    deviceDisabledBySpareActivation = 16
    okStates = ('none')
    states = {
        0:  'none',
        1:  'eccSingleBitCorrectionWarningRate',
        2:  'eccSingleBitCorrectionFailureRate',
        4:  'eccMultiBitFault',
        8:  'eccSingleBitCorrectionLoggingDisabled',
        16: 'deviceDisabledBySpareActivation'
       };
    def __init__(self, state):
        self.state = state

    def __str__(self):
        retString = ''
        if self.state == self.noFaults:
            retString = self.states[self.noFaults]
        else:
            if self.state & self.eccSingleBitCorrectionWarningRate:
                retString = self.states[self.eccSingleBitCorrectionWarningRate]
            if self.state & self.eccSingleBitCorrectionFailureRate:
                if len(retString) > 0:
                    retString += '_and_'
                retString += self.states[self.eccSingleBitCorrectionFailureRate]
            if self.state & self.eccMultiBitFault:
                if len(retString) > 0:
                    retString += '_and_'
                retString += self.states[self.eccMultiBitFault]
            if self.state & self.eccSingleBitCorrectionLoggingDisabled:
                if len(retString) > 0:
                    retString += '_and_'
                retString += self.states[self.eccSingleBitCorrectionLoggingDisabled]
            if self.state & self.deviceDisabledBySpareActivation:
                if len(retString) > 0:
                    retString += '_and_'
                retString += self.states[self.deviceDisabledBySpareActivation]
        return retString

class DeviceGroup(DellOMSAGroup):
    """
    The DeviceGroup class is a container that holds the Dell OMSA
    Device Group objects
    """
    OID = DellChassisOID.OID + '.1100'
    logFilename = 'DeviceGroup'
    groupName = 'Device'

    def __init__(self, connection):
        super(DeviceGroup, self).__init__(connection)
        self.contents = {
            'MemoryDeviceTable':    MemoryDeviceTable(connection),
            'PciDeviceTable':       PciDeviceTable(connection)
            }

    def __str__(self):
        retString = super(DeviceGroup, self).__str__()
        return retString

class MemoryDeviceTable(DellOMSATable):
    """
    The MemoryDeviceTable class is a container that holds the Dell
    OMSA Memory Device objects
    """
    OID = DeviceGroup.OID + '.50.1'
    tableName = 'Memory Device'

    def __init__(self, connection):
        super(MemoryDeviceTable, self).__init__(connection)
        self.contents = {
            'MemoryDeviceStateCapabilities': MemoryDeviceStateCapabilities(connection),
            'MemoryDeviceStateSettings':     MemoryDeviceStateSettings(connection),
            'MemoryDeviceStatus':            MemoryDeviceStatus(connection),
            'MemoryDeviceType':              MemoryDeviceType(connection),
            'MemoryDeviceLocationName':      MemoryDeviceLocationName(connection),
            'MemoryDeviceFailureModes':      MemoryDeviceFailureModes(connection)
            }

    def __str__(self):
        retString = super(MemoryDeviceTable, self).__str__()
        i = 0
        for n in self.contents['MemoryDeviceLocationName'].value:
            ss = self.contents['MemoryDeviceStateSettings'].value[i]
            if str(ss) == 'enabled':
                retString += '\nLocation: %s: Settings: %s Status: %s Faults: %s'  % \
                    (n,
                     ss,
                     self.contents['MemoryDeviceStatus'].value[i],
                     self.contents['MemoryDeviceFailureModes'].value[i])
            else:
                retString += '\n%s: Settings: %s' % (n, ss)
            i += 1
        return retString

class MemoryDeviceStateCapabilities(DellOMSAState):
    OID = MemoryDeviceTable.OID + '.3.1'
    stateClass = DellStateCapabilities

class MemoryDeviceStateSettings(DellOMSAState):
    OID = MemoryDeviceTable.OID + '.4.1'
    stateClass = DellStateSettings

class MemoryDeviceStatus(DellOMSAState):
    OID = MemoryDeviceTable.OID + '.5.1'
    stateClass = DellStatusProbe

class MemoryDeviceType(DellOMSAState):
    OID = MemoryDeviceTable.OID + '.7.1'
    stateClass = DellMemoryDeviceType

    def overallStatus(self):
        return DellOverallStatus(DellOverallStatus.okState)

class MemoryDeviceLocationName(DellOMSALocationName):
    OID = MemoryDeviceTable.OID + '.8.1'

class MemoryDeviceFailureModes(DellOMSAState):
    OID = MemoryDeviceTable.OID + '.20.1'
    stateClass = DellMemoryDeviceFailureModes

class PciDeviceTable(DellOMSATable):
    """
    The PciDeviceTable class is a container that holds the Dell
    OMSA PCI Device objects
    """
    OID = DeviceGroup.OID + '.80.1'
    tableName = 'PCI Device'

    def __init__(self, connection):
        super(PciDeviceTable, self).__init__(connection)
        self.contents = {
            'PciDeviceStateCapabilities': PciDeviceStateCapabilities(connection),
            'PciDeviceStateSettings':     PciDeviceStateSettings(connection),
            'PciDeviceStatus':            PciDeviceStatus(connection),
            'PciDeviceDescriptionName':   PciDeviceDescriptionName(connection),
            'PciDeviceAdapterFault':      PciDeviceAdapterFault(connection)
            }

    def __str__(self):
        retString = super(PciDeviceTable, self).__str__()
        i = 0
        for n in self.contents['PciDeviceDescriptionName'].value:
            ss = self.contents['PciDeviceStateSettings'].value[i]
            if str(ss) == 'enabled':
                retString += '\nDescription: %s: Settings: %s Status: %s Adapter Fault: %s'  % \
                        (n,
                         ss,
                         self.contents['PciDeviceStatus'].value[i],
                         self.contents['PciDeviceAdapterFault'].value[i])
            else:
                retString += '\n%s: Settings: %s' % (n, ss)
            i += 1
        return retString

class PciDeviceStateCapabilities(DellOMSAState):
    OID = PciDeviceTable.OID + '.3.1'
    stateClass = DellStateCapabilities

class PciDeviceStateSettings(DellOMSAState):
    OID = PciDeviceTable.OID + '.4.1'
    stateClass = DellStateSettings

class PciDeviceStatus(DellOMSAState):
    OID = PciDeviceTable.OID + '.5.1'
    stateClass = DellStatusProbe

class PciDeviceDescriptionName(DellOMSALocationName):
    OID = PciDeviceTable.OID + '.9.1'
    def update(self):
        # Call our base class's update method to get the current
        # values from the Dell OMSA. The results will be stored as a
        # list of items in our value attribute.
        super(PciDeviceDescriptionName, self).update()

        # It looks like Dell OMSA puts a newline characer at the end
        # of the DescriptionName. Strip it off here.
        value = []
        for v in self.value:
            value.append(v.rstrip('\r\n'))
        self.value = value
                          

class PciDeviceAdapterFault(DellOMSAState):
    OID = PciDeviceTable.OID + '.11.1'
    stateClass = DellBooleanFalseOk

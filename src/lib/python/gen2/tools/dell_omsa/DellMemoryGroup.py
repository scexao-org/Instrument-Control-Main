#
# DellMemoryGroup.py -- Classes to facilitate reading computer status
# from Dell's OpenManage Server Administrator (OMSA) software. We use
# SNMP (Simple Network Management Protocol) messages to communicate
# with the OMSA. The classes in this file are designed to get
# information from the OMSA's Memory Group, whose top-level OID is
# 1.3.6.1.4.1.674.10892.1.1300
#
# For more information on the Dell OMSA Memory Group, see:
# http://support.dell.com/support/edocs/software/svradmin/6.5/en/SNMP/HTML/snmpc16.htm
#
# See also the DellOMSA.py file for classes used by this file.
#
# Russell Kackley - 17 May 2011
#
from DellOMSA import *

class DellPhysicalMemoryArrayLocation(DellOMSAStateType):
    """
    The DellPhysicalMemoryArrayLocation class implements the data
    values from Table 16.1 in the Dell OMSA Reference Guide - Memory
    Group
    """
    states = {
        1:  'memoryArrayLocationIsOther',
        2:  'memoryArrayUseIsUnknown',
        3:  'memoryArrayUseIsSystemMemory',
        4:  'memoryArrayUseIsVideoMemory',
        5:  'memoryArrayUseIsFLASHMemory',
        6:  'memoryArrayUseIsNonVolatileRAMMemory',
        7:  'memoryArrayUseIsCacheMemory',
        8:  'memoryArrayLocationIsPCMCIA',
        9:  'memoryArrayLocationIsProprietary',
        10:  'memoryArrayLocationIsNUBUS',
        11:  'memoryArrayLocationIsPC98C20',
        12:  'memoryArrayLocationIsPC98C24',
        13:  'memoryArrayLocationIsPC98E',
        14:  'memoryArrayLocationIsPC98LocalBus',
        15:  'memoryArrayLocationIsPC98Card'
        };

class MemoryGroup(DellOMSAGroup):
    """
    The MemoryGroup class is a container that holds the Dell OMSA
    Memory Group objects
    """
    OID = DellChassisOID.OID + '.1300'
    logFilename = 'MemoryGroup'
    groupName = 'Memory'

    def __init__(self, connection):
        super(MemoryGroup, self).__init__(connection)
        self.contents = {
            'PhysicalMemoryArrayTable':       PhysicalMemoryArrayTable(connection),
            'PhysicalMemoryArrayMappedTable': PhysicalMemoryArrayMappedTable(connection)
            }

    def __str__(self):
        retString = super(MemoryGroup, self).__str__()
        return retString

class PhysicalMemoryArrayTable(DellOMSATable):
    """
    The PhysicalMemoryArrayTable class is a container that holds the
    Dell OMSA Physical Memory Array objects
    """
    OID = MemoryGroup.OID + '.10.1'
    tableName = 'Physical Memory Array'

    def __init__(self, connection):
        super(PhysicalMemoryArrayTable, self).__init__(connection)
        self.contents = {
            'PhysicalMemoryArrayStateSettings': PhysicalMemoryArrayStateSettings(connection),
            'PhysicalMemoryArrayStatus':        PhysicalMemoryArrayStatus(connection),
            'PhysicalMemoryArrayLocation':      PhysicalMemoryArrayLocation(connection),
            }

    def __str__(self):
        retString = super(PhysicalMemoryArrayTable, self).__str__()
        i = 0
        for n in self.contents['PhysicalMemoryArrayLocation'].value:
            ss = self.contents['PhysicalMemoryArrayStateSettings'].value[i]
            if str(ss) == 'enabled':
                retString += '\nLocation: %s Settings: %s Status: %s '  % \
                    (n,
                     ss,
                     self.contents['PhysicalMemoryArrayStatus'].value[i])
            else:
                retString += '\n%s: Settings: %s' % (n, ss)
            i += 1
        return retString

class PhysicalMemoryArrayStateSettings(DellOMSAState):
    OID = PhysicalMemoryArrayTable.OID + '.4'
    stateClass = DellStateSettings

class PhysicalMemoryArrayStatus(DellOMSAState):
    OID = PhysicalMemoryArrayTable.OID + '.5'
    stateClass = DellStatus

class PhysicalMemoryArrayLocation(DellOMSAState):
    OID = PhysicalMemoryArrayTable.OID + '.8'
    stateClass = DellPhysicalMemoryArrayLocation

    def overallStatus(self):
        return DellOverallStatus(DellOverallStatus.okState)

class PhysicalMemoryArrayMappedTable(DellOMSATable):
    """
    The PhysicalMemoryArrayMappedTable class is a container that holds
    the Dell OMSA Physical Memory Array Mapped objects
    """
    OID = MemoryGroup.OID + '.20.1'
    tableName = 'Physical Memory Array Mapped'

    def __init__(self, connection):
        super(PhysicalMemoryArrayMappedTable, self).__init__(connection)
        self.contents = {
            'PhysicalMemoryArrayMappedStateSettings':   PhysicalMemoryArrayMappedStateSettings(connection),
            'PhysicalMemoryArrayMappedStatus':          PhysicalMemoryArrayMappedStatus(connection),
            'PhysicalMemoryArrayMappedStartingAddress': PhysicalMemoryArrayMappedStartingAddress(connection)
            }

    def __str__(self):
        retString = super(PhysicalMemoryArrayMappedTable, self).__str__()
        i = 0
        for n in self.contents['PhysicalMemoryArrayMappedStartingAddress'].value:
            ss = self.contents['PhysicalMemoryArrayMappedStateSettings'].value[i]
            if str(ss) == 'enabled':
                retString += '\nAddress: %s Settings: %s Status: %s '  % \
                    (repr(n),
                     ss,
                     self.contents['PhysicalMemoryArrayMappedStatus'].value[i])
            else:
                retString += '\n%s: Settings: %s' % (n, ss)
            i += 1
        return retString

class PhysicalMemoryArrayMappedStateSettings(DellOMSAState):
    OID = PhysicalMemoryArrayMappedTable.OID + '.4'
    stateClass = DellStateSettings

class PhysicalMemoryArrayMappedStatus(DellOMSAState):
    OID = PhysicalMemoryArrayMappedTable.OID + '.5'
    stateClass = DellStatus

class PhysicalMemoryArrayMappedStartingAddress(DellOMSALocationName):
    OID = PhysicalMemoryArrayMappedTable.OID + '.7.1'

    def update(self):
        super(PhysicalMemoryArrayMappedStartingAddress, self).update()
        # Convert the address value returned by Dell OMSA into a
        # string that is easier to read
        value = []
        for v in self.value:
            new = '0X'
            for i in range(len(v)):
                new += '%02X' % (ord(v[i]))
            value.append(new)
        self.value = value

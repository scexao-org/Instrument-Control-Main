#
# DellSystemsManagementSoftwareGroup.py -- Classes to facilitate
# reading computer status from Dell's OpenManage Server Administrator
# (OMSA) software. We use SNMP (Simple Network Management Protocol)
# messages to communicate with the OMSA. The classes in this file are
# designed to get information from the OMSA's System Management
# Software Group, whose top-level OID is 1.3.6.1.4.1.674.10892.1.100.
#
# For more information on the Dell OMSA Systems Management Software
# Group, see:
# http://support.dell.com/support/edocs/software/svradmin/6.5/en/SNMP/HTML/snmpc9.htm
#
# See also the DellOMSA.py file for classes used by this file.
#
# Russell Kackley - 18 April 2013
#
import socket
import re
from DellOMSA import *
										
class DellSMSSupportedType(DellOMSAStateType):
    """
    The DellSMSSupportedType class implements the data values from
    Table 4-1 in the Dell OMSA Reference Guide - System Managements
    Software Group
    """
    okStates = ('supportsSNMP', 'supportsDMI', 'supportsSNMPandDMI', 'supportsCIMOM', 'supportsSNMPandCIMOM')
    states = {
        1:  'supportsSNMP',
        2:  'supportsDMI',
        3:  'supportsSNMPandDMI',
        4:  'supportsCIMOM',
        5:  'supportsSNMPandCIMOM'
        };

class DellSMSFeatureFlags(DellOMSAStateType):
    """
    The DellSMSFeatureFlags class implements the data values from
    Table 4-2 in the Dell OMSA Reference Guide - Systems Management
    Software Group
    """
    okStates = ('none', 'webOneToOneManagementPreferred')
    states = {
        0:  'none',
        1:  'webOneToOneManagementPreferred'
        };
										
class DellSMSSNMPFeatureFlags(DellOMSAStateType):
    """
    The DellSMSSNMPFeatureFlags class implements the data values from
    Table 4-3 in the Dell OMSA Reference Guide - Systems Management
    Software Group
    """
    okStates = ('none', 'supportsSparseTables')
    states = {
        1:  'none',
        2:  'supportsSparseTables'
        };

class SystemsManagementSoftwareGroup(DellOMSAGroup):
    """
    The SystemsManagementSoftwareGroup class is a container that holds
    the Dell OMSA Systems Management Software Group objects
    """
    OID = DellChassisOID.OID + '.100'
    logFilename = 'SystemsManagementSoftwareGroup'
    groupName = 'SystemsManagementSoftware'

    def __init__(self, connection):
        super(SystemsManagementSoftwareGroup, self).__init__(connection)
        self.contents = {
            'SystemsManagementSoftwareTable': SystemsManagementSoftwareTable(connection)
            }

    def __str__(self):
        retString = super(SystemsManagementSoftwareGroup, self).__str__()
        return retString

    def dellOMSAVersion(self):
        return self.contents['SystemsManagementSoftwareTable'].contents['SystemManagementSoftwareGlobalVersionName'].value[0]

class SystemsManagementSoftwareTable(DellOMSATable):
    """
    The Systems Management Software Table class is a container that
    holds the Dell OMSA Systems Management Software objects
    """
    OID = SystemsManagementSoftwareGroup.OID
    tableName = 'Systems Management Software'

    def __init__(self, connection):
        super(SystemsManagementSoftwareTable, self).__init__(connection)
        self.contents = {
            'SystemManagementSoftwareName':                  SystemManagementSoftwareName(connection),
            'SystemManagementSoftwareVersionNumberName':     SystemManagementSoftwareVersionNumberName(connection),
            'SystemManagementSoftwareBuildNumber':           SystemManagementSoftwareBuildNumber(connection),
            'SystemManagementSoftwareDescriptionName':       SystemManagementSoftwareDescriptionName(connection),
            'SystemManagementSoftwareSupportedProtocol':     SystemManagementSoftwareSupportedProtocol(connection),
            'SystemManagementSoftwarePreferredProtocol':     SystemManagementSoftwarePreferredProtocol(connection),
            'SystemManagementSoftwareUpdateLevelName':       SystemManagementSoftwareUpdateLevelName(connection),
            'SystemManagementSoftwareURLName':               SystemManagementSoftwareURLName(connection),
            'SystemManagementSoftwareLanguageName':          SystemManagementSoftwareLanguageName(connection),
            'SystemManagementSoftwareGlobalVersionName':     SystemManagementSoftwareGlobalVersionName(connection),
            'SystemManagementSoftwareFeatureFlags':          SystemManagementSoftwareFeatureFlags(connection),
            'SystemManagementSoftwareSNMPAgentFeatureFlags': SystemManagementSoftwareSNMPAgentFeatureFlags(connection),
            'SystemManagementSoftwareManufacturerName':      SystemManagementSoftwareManufacturerName(connection)
            }

class SystemManagementSoftwareName(DellOMSALocationName):
    OID = SystemsManagementSoftwareTable.OID + '.1'

class SystemManagementSoftwareVersionNumberName(DellOMSALocationName):
    OID = SystemsManagementSoftwareTable.OID + '.2'

class SystemManagementSoftwareBuildNumber(DellOMSALocationName):
    OID = SystemsManagementSoftwareTable.OID + '.3'

class SystemManagementSoftwareDescriptionName(DellOMSALocationName):
    OID = SystemsManagementSoftwareTable.OID + '.4'

class SystemManagementSoftwareSupportedProtocol(DellOMSAState):
    OID = SystemsManagementSoftwareTable.OID + '.5'
    stateClass = DellSMSSupportedType

class SystemManagementSoftwarePreferredProtocol(DellOMSAState):
    OID = SystemsManagementSoftwareTable.OID + '.6'
    stateClass = DellSMSSupportedType

class SystemManagementSoftwareUpdateLevelName(DellOMSALocationName):
    OID = SystemsManagementSoftwareTable.OID + '.7'

class SystemManagementSoftwareURLName(DellOMSALocationName):
    OID = SystemsManagementSoftwareTable.OID + '.8'

class SystemManagementSoftwareLanguageName(DellOMSALocationName):
    OID = SystemsManagementSoftwareTable.OID + '.9'

class SystemManagementSoftwareGlobalVersionName(DellOMSALocationName):
    OID = SystemsManagementSoftwareTable.OID + '.10'

class SystemManagementSoftwareFeatureFlags(DellOMSAState):
    OID = SystemsManagementSoftwareTable.OID + '.11'
    stateClass = DellSMSFeatureFlags

class SystemManagementSoftwareSNMPAgentFeatureFlags(DellOMSAState):
    OID = SystemsManagementSoftwareTable.OID + '.12'
    stateClass = DellSMSSNMPFeatureFlags

class SystemManagementSoftwareManufacturerName(DellOMSALocationName):
    OID = SystemsManagementSoftwareTable.OID + '.13'

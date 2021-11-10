#
# DellStorageManagementGroup.py -- Classes to facilitate reading
# computer status from Dell's OpenManage Server Administrator (OMSA)
# software. We use SNMP (Simple Network Management Protocol) messages
# to communicate with the OMSA. The classes in this file are designed
# to get information from the OMSA's Storage Management Group, whose
# top-level OID is 1.3.6.1.4.1.674.10893.1
#
# For more information on the Dell OMSA Power Group, see:
# http://support.dell.com/support/edocs/software/svradmin/6.5/en/SNMP/HTML/snmpc24.htm
#
# See also the DellOMSA.py file for classes used by this file.
#
# Russell Kackley - 17 May 2011
#
import socket
from DellOMSA import *
import DellSystemsManagementSoftwareGroup

class DellPhysicalDeviceState(DellOMSAStateType):
    """
    The DellPhysicalDeviceState class implements the data values used
    by many of the states in the Dell OMSA Reference Guide - Storage
    Management Group, e.g., controllerState, channelState,
    enclosureState, arrayDiskState, etc.
    """
    okStates = ('Ready', 'Online')
    states = {
        0: 'Unknown',
        1: 'Ready',
        2: 'Failed',
        3: 'Online',
        4: 'Offline',
        6: 'Degraded',
        }

class DellArrayDiskState(DellPhysicalDeviceState):
    """
    The DellArrayDiskState class implements the additional data values
    beyond those of the DellPhysicalDeviceState class. These
    additional values are used by the arrayDiskState item.
    """
    okStates = ('Ready', 'Online', 'Foreign')
    our_states = {
        7:  'Recovering',
        11: 'Removed',
        15: 'Resynching',
        22: 'Replacing',
        24: 'Rebuild',
        25: 'NoMedia',
        26: 'Formatting',
        28: 'Diagnostics',
        34: 'PredictiveFailure',
        35: 'Initializing',
        39: 'Foreign',
        40: 'Clear',
        41: 'Unsupported',
        53: 'Incompatible'
        }
    def __init__(self, state):
        super(DellArrayDiskState, self).__init__(state)
        for key in self.our_states.keys():
            self.states[key] = self.our_states[key]

class DellArrayDiskDellCertified(DellOMSAStateType):
    """
    The DellArrayDiskDellCertified class implements implements the
    data values used by the arrayDiskDellCertified value in the Dell
    OMSA Reference Guide - Storage Management Group.
    """
    okStates = ('NotCertified', 'Certified')
    states = {
        0: 'NotCertified',
        1: 'Certified',
        99: 'Unknown'
        }

class DellArrayDiskDellCertified_v7_1_0(DellArrayDiskDellCertified):
    """
    The DellArrayDiskDellCertified_v7_1_0 class implements implements
    the data values used by the arrayDiskDellCertified value in the
    Dell OMSA Reference Guide - Storage Management Group. Note that
    this class applies only to Dell OMSA Version 7.1.0 wherein the
    NotCertified/Certified states are reversed from the usual
    definitions. For comparison, see the DellArrayDiskDellCertified
    class in this file.
    """
    states = {
        0: 'Certified',
        1: 'NotCertified',
        99: 'Unknown'
        }

class DellFanState(DellPhysicalDeviceState):
    """
    The DellFanState class implements the additional data values
    beyond those of the DellPhysicalDeviceState class. These
    additional values are used by the fanState item.
    """
    our_states = {
        21: 'Missing'
        }
    def __init__(self, state):
        super(DellFanState, self).__init__(state)
        for key in self.our_states.keys():
            self.states[key] = self.our_states[key]

class DellPowerSupplyState(DellOMSAStateType):
    """
    The DellPowerSupplyState class implements the data values used by
    the powerSupplyState value in the Dell OMSA Reference Guide -
    Storage Management Group.
    """
    okStates = ('Ready')
    states = {
        0:  'Unknown',
        1:  'Ready',
        2:  'Failed',
        5:  'NotInstalled',
        6:  'Degraded',
        11: 'Removed'
        };
										
class DellTemperatureProbeState(DellOMSAStateType):
    """
    The DellTemperatureProbeState class implements the data values
    used by the temperatureProbeState value in the Dell OMSA Reference
    Guide - Storage Management Group.
    """
    okStates = ('Ready')
    states = {
        0:  'Unknown',
        1:  'Ready',
        2:  'Failed',
        4:  'Offline',
        6:  'Degraded',
        9:  'Inactive',
        21: 'Missing'
        };
										
class DellEnclosureManagementModuleState(DellPhysicalDeviceState):
    """
    The DellEnclosureManagementModuleState class implements the
    additional data values beyond those of the DellPhysicalDeviceState
    class. These additional values are used by the
    enclosureManagementModuleState item.
    """
    our_states = {
        5:  'NotInstalled',
        21: 'Missing'
        }
    def __init__(self, state):
        super(DellEnclosureManagementModuleState, self).__init__(state)
        for key in self.our_states.keys():
            self.states[key] = self.our_states[key]

class DellEnclosureType(DellOMSAStateType):
    """
    The DellEnclosureType class implements the
    data values used by the enclosureType item in the
    Dell OMSA Reference Guide - Storage Management Group.
    """
    states = {
        1: 'Internal', 
        2: 'Dell PowerVault 200S', 
        3: 'Dell PowerVault 210S', 
        4: 'Dell PowerVault 220S', 
        5: 'Dell PowerVault 660F', 
        6: 'Dell PowerVault 224F', 
        7: 'Dell PowerVault 660F/224F', 
        8: 'Dell MD1000', 
        9: 'Dell MD1120'
        }

class DellArrayDiskSmartAlertIndicationState(DellOMSAStateType):
    """
    The DellArrayDiskSmartAlertIndicationState class implements the
    data values used by the arrayDiskSmartAlertIndication item in the
    Dell OMSA Reference Guide - Storage Management Group.
    """
    okStates = ('No')
    warningStates = ('Yes')
    states = {
        1: 'No', # disk has not received a predictive failure alert
        2: 'Yes' # disk has received a predictive failure alert
        }

class DellEnclosureManagementModuleType(DellOMSAStateType):
    """
    The DellEnclosureManagementModuleType class implements the data
    values used by the enclosureManagementModuleType item in the Dell
    OMSA Reference Guide - Storage Management Group.
    """
    okStates = ('EMM', 'TerminationCard')
    states = {
        0: 'Unknown',
        1: 'EMM',
        2: 'TerminationCard'
        }

class DellBatteryState(DellOMSAStateType):
    """
    The DellBatteryState class implements the data values used by
    batteryState item in the Dell OMSA Reference Guide - Storage
    Management Group. Note that we specify the battery states of
    Degraded, Learning, and Charging as being 'Ok'. The battery goes
    through those states during its periodic learn cycle and we don't
    want to report errors just because the battery is in a learn
    cycle.
    """
    okStates = ('OK', 'Degraded', 'Learning', 'Charging')
    states = {
        0:  'Unknown',
        1:  'OK',
        2:  'Failed',
        6:  'Degraded',
        7:  'Reconditioning',
        9:  'High',
        10: 'Low',
        12: 'Charging',
        21: 'Missing',
        36: 'Learning'
        }

class DellBatteryPredictedCapacity(DellOMSAStateType):
    """
    The DellBatteryPredictedCapacity class implements the data values
    used by batteryPredictedCapacity item in the Dell OMSA Reference
    Guide - Storage Management Group. Note that we specify the
    predicted capacity state of Unknown as being 'Ok'. The battery is
    in this state during the learn cycle and we don't want to report
    errors just because the battery is in a learn cycle.
    """
    okStates = ('Ready', 'Unknown')
    states = {
        1: 'Failed',
        2: 'Ready',
        4: 'Unknown'
        }

class DellBatteryLearnState(DellOMSAStateType):
    """
    The DellBatteryLearnState class implements the data values used by
    batteryLearnState item in the Dell OMSA Reference Guide - Storage
    Management Group. Note that the 'Due' state is not listed in that
    Dell document. However, the value of 32 does occur at the start of
    a learn cycle and the document Dell OpenManage Server
    Administrator Storage Management User's Guide - RAID Controller
    Batteries does mention that state.
    """
    okStates = ('Active', 'Requested', 'Idle', 'Due')
    states = {
        1:  'Failed',
        2:  'Active',
        4:  'TimedOut',
        8:  'Requested',
        16: 'Idle',
        32: 'Due'
        }

class DellVirtualDiskState(DellPhysicalDeviceState):
    """
    The DellVirtualDiskState class implements the additional data
    values beyond those of the DellPhysicalDeviceState class. These
    additional values are used by the virtualDiskState item.
    """
    okStates = ('Ready', 'Online', 'BackgroundInitialization')
    our_states = {
        15: 'Resynching',
        16: 'Regenerating',
        24: 'Rebuilding',
        26: 'Formatting',
        32: 'Reconstructing',
        35: 'Initializing',
        36: 'BackgroundInitialization',
        38: 'ResynchingPaused',
        52: 'PermanentlyDegraded',
        54: 'DegradedRedundancy'
        }
    def __init__(self, state):
        super(DellVirtualDiskState, self).__init__(state)
        for key in self.our_states.keys():
            self.states[key] = self.our_states[key]

class StorageManagementGroup(DellOMSAGroup):
    """
    The StorageManagementGroup class is a container that holds the Dell
    OMSA Storage Management objects
    """
    OID = DellStorageManagementOID.OID + '.20'
    logFilename = 'StorageManagementGroup'
    groupName = 'Storage Management'

    def __init__(self, connection):
        super(StorageManagementGroup, self).__init__(connection)
        self.contents = {
            'GlobalDataGroup':      GlobalDataGroup(connection),
            'PhysicalDevicesGroup': PhysicalDevicesGroup(connection),
            'LogicalDevicesGroup':  LogicalDevicesGroup(connection)
            }

    def __str__(self):
        retString = super(StorageManagementGroup, self).__str__()
        return retString
 
    # StorageManagementGroup has its own overallStatus method because
    # we want to override the 'Warning' status when the
    # PhysicalDevicesGroup/ControllerTable has an external controller
    # and the PhysicalDevicesGroup/ArrayDiskTable reports that it has
    # Foreign disks and the GlobalDataGroup/AgentGlobalSystemStatus is
    # reported as nonCritical. We also want to override the 'Error'
    # status when a PERC controller battery is in its learning cycle.
    def overallStatus(self):
        physicalDevicesGroup = self.contents['PhysicalDevicesGroup']
        if physicalDevicesGroup.contents['ControllerTable'].hasExternal() and \
                physicalDevicesGroup.contents['ArrayDiskTable'].hasForeign() and \
                str(self.contents['GlobalDataGroup'].contents['AgentGlobalSystemStatus'].value[0]) == 'nonCritical':
            self.contents['GlobalDataGroup'].contents['AgentGlobalSystemStatus'].value[0].setState('ok')

        # This section overrides the nonCritical status in the
        # GlobalDataGroup, BatteryTable, and ControllerTable when a
        # controller is in its battery learn cycle.
        if physicalDevicesGroup.contents['ControllerTable'].hasBattery():
            batteryTable = physicalDevicesGroup.contents['BatteryTable']
            i = 0
            for v in batteryTable.contents['BatteryState'].value:
                # For the PERC H810 card, Dell OMSA does not report
                # the BatteryLearnState, despite the fact that the
                # card does have a battery. If the BatteryLearnState
                # table is missing the expected values, set it to
                # Idle so as not to generate any errors.
                try:
                    batteryLearnState = batteryTable.contents['BatteryLearnState'].value[i]
                except:
                    batteryLearnState = 'Idle'
                if (str(v) == 'Degraded' and str(batteryLearnState) == 'Due') or \
                       (str(v) == 'Learning' and str(batteryLearnState) == 'Active') or \
                       (str(v) == 'Charging' and str(batteryLearnState) == 'Requested') or \
                       (str(v) == 'Charging' and str(batteryLearnState) == 'Idle'):
                    if str(self.contents['GlobalDataGroup'].contents['AgentGlobalSystemStatus'].value[0]) == 'nonCritical':
                        self.contents['GlobalDataGroup'].contents['AgentGlobalSystemStatus'].value[0].setState('ok')
                    if str(batteryTable.contents['BatteryRollUpStatus'].value[i]) == 'nonCritical':
                        batteryTable.contents['BatteryRollUpStatus'].value[i].setState('ok')
                    if str(batteryTable.contents['BatteryComponentStatus'].value[i]) == 'nonCritical':
                        batteryTable.contents['BatteryComponentStatus'].value[i].setState('ok')
                    if str(physicalDevicesGroup.contents['ControllerTable'].contents['ControllerRollUpStatus'].value[i]) == 'nonCritical':
                        physicalDevicesGroup.contents['ControllerTable'].contents['ControllerRollUpStatus'].value[i].setState('ok')
                i += 1

        # Some of the Dell PERC controllers (H200 in particular)
        # report when they sense that a connected disk is not
        # Dell-certified. This results in RollUp Status and Component
        # Status in various places being set to nonCritical. We want
        # to suppress the nonCritical status here so that we don't get
        # warnings or errors as a result of using non-Dell-certified
        # disks. We will iterate through all the disks in the
        # ArrayDiskTable and, if we find any disks that are reporting
        # as non-Dell-certified, set their status to Ok. In addition,
        # we have to modify the status of the controllers to which
        # those disks are attached. Finally, the EnclosureTable has
        # status information on the controller, so we have to suppress
        # the nonCritical status in that table as well.
        i = 0
        arrayDiskTable = physicalDevicesGroup.contents['ArrayDiskTable']
        arrayDiskEnclosureConnectionTable = physicalDevicesGroup.contents['ArrayDiskEnclosureConnectionTable']
        controllerTable = physicalDevicesGroup.contents['ControllerTable']
        enclosureTable = physicalDevicesGroup.contents['EnclosureTable']
        for v in arrayDiskTable.contents['ArrayDiskDellCertified'].value:
            if str(v) == 'NotCertified':
                arrayControllerIndex = int(str(arrayDiskEnclosureConnectionTable.contents['ArrayDiskControllerNumber'].value[i])) - 1
                enclosureIndex = int(str(arrayDiskEnclosureConnectionTable.contents['ArrayDiskEnclosureNumber'].value[i])) - 1
                if str(arrayDiskTable.contents['ArrayDiskRollUpStatus'].value[i]) == 'nonCritical':
                    arrayDiskTable.contents['ArrayDiskRollUpStatus'].value[i].setState('ok')
                if str(arrayDiskTable.contents['ArrayDiskComponentStatus'].value[i]) == 'nonCritical':
                    arrayDiskTable.contents['ArrayDiskComponentStatus'].value[i].setState('ok')
                if str(self.contents['GlobalDataGroup'].contents['AgentGlobalSystemStatus'].value[0]) == 'nonCritical':
                    self.contents['GlobalDataGroup'].contents['AgentGlobalSystemStatus'].value[0].setState('ok')
                if ('H200' in controllerTable.contents['ControllerName'].value[arrayControllerIndex] or \
                        'H800' in controllerTable.contents['ControllerName'].value[arrayControllerIndex] or \
                        'H810' in controllerTable.contents['ControllerName'].value[arrayControllerIndex]) and \
                        str(controllerTable.contents['ControllerRollUpStatus'].value[arrayControllerIndex]) == 'nonCritical':
                    controllerTable.contents['ControllerRollUpStatus'].value[arrayControllerIndex].setState('ok')
                if str(enclosureTable.contents['EnclosureRollUpStatus'].value[enclosureIndex]) == 'nonCritical':
                    enclosureTable.contents['EnclosureRollUpStatus'].value[enclosureIndex].setState('ok')
            i += 1

        overallStatus = super(StorageManagementGroup, self).overallStatus()
        return overallStatus
       
class GlobalDataGroup(DellOMSATable):
    """
    The GlobalDataGroup class is a container that holds the Dell OMSA
    Global Data objects
    """
    OID = StorageManagementGroup.OID + '.110'
    tableName = 'Global Data'

    def __init__(self, connection):
        super(GlobalDataGroup, self).__init__(connection)
        self.contents = {
            'AgentGlobalSystemStatus': AgentGlobalSystemStatus(connection)
            }

    def __str__(self):
        retString = super(GlobalDataGroup, self).__str__()
        for s in self.contents['AgentGlobalSystemStatus'].value:
            retString += '\n%s: Status: %s '  % \
                    ('AgentGlobalSystemStatus', s)
        return retString

class AgentGlobalSystemStatus(DellOMSAState):
    OID = GlobalDataGroup.OID + '.13'
    stateClass = DellStatus

class PhysicalDevicesGroup(DellOMSAGroup):
    """
    The PhysicalDevicesGroup class is a container that holds the Dell
    OMSA Physical Devices objects
    """
    OID = StorageManagementGroup.OID + '.130'
    groupName = 'Physical Devices'

    def __init__(self, connection):
        super(PhysicalDevicesGroup, self).__init__(connection)
        self.contents = {
            'ControllerTable': ControllerTable(connection),
            'EnclosureTable':  EnclosureTable(connection),
            'ArrayDiskTable':  ArrayDiskTable(connection),
            'ArrayDiskEnclosureConnectionTable':  ArrayDiskEnclosureConnectionTable(connection),
            'BatteryTable':    BatteryTable(connection)
            }

    # PhysicalDevicesGroup has its own update method because we have
    # to update the ControllerTable first and determine which types of
    # controllers are installed. Some controllers have a battery
    # (e.g., PERC 6/E, 6/I, H800, and H810) and some don't (e.g., PERC
    # H200). If we find any controllers that have a battery, update the
    # BatteryTable. Also, we need to look at the EnclosureTable to see
    # if there are any MD1000 enclosures. If so, then we add FanTable,
    # PowerSupplyTable, TemperatureProbeTable, and
    # EnclosureManagementModuleTable items to our self.contents
    # attribute.
    def update(self):
        self.contents['EnclosureTable'].update()
        self.contents['ArrayDiskTable'].update()
        self.contents['ControllerTable'].update()
        self.contents['ArrayDiskEnclosureConnectionTable'].update()

        # See if we have any controllers with a battery. If we found a
        # controller with a battery, update the BatteryTable.
        if self.contents['ControllerTable'].hasBattery():
            self.contents['BatteryTable'].update()
        else:
            # If no controllers have a battery, delete the
            # BatteryTable from our contents attribute. Wrap the
            # deletion in a try/except block because we want to
            # supress the exception if the BatteryTable has already
            # been deleted.
            try:
                del self.contents['BatteryTable']
            except:
                pass

        # See if any of the items in the EnclosureTable are identified
        # as MD1000. If so, check to see if the ArrayDiskTable has
        # Foreign disks. If there are no Foreign disks, then add
        # FanTable, PowerSupplyTable, TemperatureProbeTable, and
        # EnclosureManagementModuleTable items to our self.contents
        # attribute.
        enclosureTable = self.contents['EnclosureTable']
        if enclosureTable.hasMD1000() and not self.contents['ArrayDiskTable'].hasForeign():
            self.contents['FanTable'] = FanTable(self.connection)
            self.contents['PowerSupplyTable'] = PowerSupplyTable(self.connection)
            self.contents['TemperatureProbeTable'] = TemperatureProbeTable(self.connection)
            self.contents['EnclosureManagementModuleTable'] = EnclosureManagementModuleTable(self.connection)
            self.contents['FanTable'].update()
            self.contents['PowerSupplyTable'].update()
            self.contents['TemperatureProbeTable'].update()
            self.contents['EnclosureManagementModuleTable'].update()

    # PhysicalDevicesGroup has its own overallStatus method because we
    # want to override the 'Warning' status when the ControllerTable
    # and EnclosureTable report an external controller Rollup status
    # as nonCritical and the ArrayDiskTable reports that it has
    # Foreign disks.
    def overallStatus(self):
        # First, get the index number of the first external controller
        # in the ControllerTable, if there are any.
        controllerTable = self.contents['ControllerTable']
        externalControllerIndex = controllerTable.indexExternal()
        enclosureTable = self.contents['EnclosureTable']

        # If we found an external controller, look to see if the
        # Rollup status of that controller is nonCritical. If so look
        # to see if ArrayDiskTable has Foreign disks. If so, set the
        # ControllerRollUpStatus to ok. Do a similar operation on the
        # EnclosureRollUpStatus. After that, call the parent class's
        # overallStatus method to determine our overallStatus.
        if externalControllerIndex >= 0:
            if str(controllerTable.contents['ControllerRollUpStatus'].value[externalControllerIndex]) == 'nonCritical':
                if self.contents['ArrayDiskTable'].hasForeign():
                    controllerTable.contents['ControllerRollUpStatus'].value[externalControllerIndex].setState('ok')
            # It is possible that there is nothing connected to the
            # external controller. If there is nothing connected, we
            # will get an IndexError exception from the next block, so
            # catch and ignore that exception.
            try:
                if str(enclosureTable.contents['EnclosureRollUpStatus'].value[externalControllerIndex]) == 'nonCritical':
                    if self.contents['ArrayDiskTable'].hasForeign():
                        enclosureTable.contents['EnclosureRollUpStatus'].value[externalControllerIndex].setState('ok')
            except IndexError:
                pass
        overallStatus = super(PhysicalDevicesGroup,self).overallStatus()
        return overallStatus

    def munin_config_battery(self):
        print 'graph_title %s PERC Battery Next Learn Time' % (socket.gethostname())
        print 'graph_args --base 1000 -l 0'
        print 'graph_vlabel Time (Days)'
        print 'graph_category Chassis'
        print 'graph_info This graph shows the time until the next learn cycle of all PERC disk controller batteries.'
        print 'graph_period second'
        controllerTable = self.contents['ControllerTable']
        i = 0
        for n in controllerTable.contents['ControllerName'].value:
            print 'perc_batt_nxt_lrn_tm_%s.label %s' % (i, n)
            i += 1

    def munin_report_battery(self):
        batteryTable = self.contents['BatteryTable']
        i = 0
        for n in batteryTable.contents['BatteryName'].value:
            # For the PERC H810 card, Dell OMSA does not report the
            # BatteryNextLearnTime, despite the fact that the card
            # does have a battery.  If the BatteryLearnTime table is
            # missing the expected values, set it to 0 so that we
            # don't generate an exception.
            try:
                value = batteryTable.contents['BatteryNextLearnTime'].value[i].value
            except IndexError:
                value = 0
            if batteryTable.contents['BatteryNextLearnTime'].units == 'hours':
                value /= 24
            print 'perc_batt_nxt_lrn_tm_%s.value %s' % (i, value)
            i += 1

    def __str__(self):
        retString = super(PhysicalDevicesGroup, self).__str__()
        return retString

class ControllerTable(DellOMSATable):
    """
    The ControllerTable class is a container that holds the Dell OMSA
    Controller objects
    """
    OID =PhysicalDevicesGroup.OID + '.1.1'
    tableName = 'Devices Controller'

    def __init__(self, connection):
        super(ControllerTable, self).__init__(connection)
        self.contents = {
            'ControllerName':            ControllerName(connection),
            'ControllerState':           ControllerState(connection),
            'ControllerRollUpStatus':    ControllerRollUpStatus(connection),
            'ControllerComponentStatus': ControllerComponentStatus(connection),
            }

    def __str__(self):
        retString = super(ControllerTable, self).__str__()
        i = 0
        for n in self.contents['ControllerName'].value:
            retString += '\n%s: State: %s RollUp Status: %s Component Status: %s '  % \
                (n,
                 self.contents['ControllerState'].value[i],
                 self.contents['ControllerRollUpStatus'].value[i],
                 self.contents['ControllerComponentStatus'].value[i])
            i += 1
        return retString

    def hasBattery(self):
        return self.contents['ControllerName'].hasBattery()

    def hasExternal(self):
        return self.contents['ControllerName'].hasExternal()

    def indexExternal(self):
        return self.contents['ControllerName'].indexExternal()

class ControllerName(DellOMSALocationName):
    OID = ControllerTable.OID + '.2'

    # The hasBattery method looks at the names in our value attribute
    # and returns True if it finds a controller that has a battery and
    # False otherwise. Currently, we recognize the PERC 6/E, 6/I, H800,
    # and H810 as having batteries.
    def hasBattery(self):
        for name in self.value:
            if 'PERC 6/i Integrated' in name or 'PERC 6/E Adapter' in name or 'PERC H800 Adapter' in name or 'PERC H810 Adapter' in name:
                return True
        return False

    # The hasExternal method looks at the names in our value attribute
    # and returns True if it finds a controller that is an 'external'
    # controller and False otherwise. Currently, we recognize the
    # PERC 6/E, H800, and H810 as being external controllers.
    def hasExternal(self):
        for name in self.value:
            if 'PERC 6/E Adapter' in name or 'PERC H800 Adapter' in name or 'PERC H810 Adapter' in name:
                return True
        return False        

    # The indexExternal method looks at the names in our value
    # attribute and returns the index number of the first external
    # controller that it finds. If no external controller is found,
    # returns -1. Currently, we recognize the PERC 6/E, H800, and
    # H810 as being external controllers.
    def indexExternal(self):
        index = -1
        i = 0
        for name in self.value:
            if 'PERC 6/E Adapter' in name or 'PERC H800 Adapter' in name or 'PERC H810 Adapter' in name:
                index = i
                break
            i += 1
        return index     

class ControllerState(DellOMSAState):
    OID = ControllerTable.OID + '.5'
    stateClass = DellPhysicalDeviceState

class ControllerRollUpStatus(DellOMSAState):
    OID = ControllerTable.OID + '.37'
    stateClass = DellStatus

class ControllerComponentStatus(DellOMSAState):
    OID = ControllerTable.OID + '.38'
    stateClass = DellStatus

class EnclosureTable(DellOMSATable):
    """
    The EnclosureTable class is a container that holds the Dell OMSA
    Enclosure objects
    """
    OID = PhysicalDevicesGroup.OID + '.3.1'
    tableName = 'Devices Enclosure'

    def __init__(self, connection):
        super(EnclosureTable, self).__init__(connection)
        self.contents = {
            'EnclosureName':              EnclosureName(connection),
            'EnclosureState':             EnclosureState(connection),
            'EnclosureType':              EnclosureType(connection),
            'EnclosureRollUpStatus':      EnclosureRollUpStatus(connection),
            'EnclosureComponentStatus':   EnclosureComponentStatus(connection)
           }

    def __str__(self):
        retString = super(EnclosureTable, self).__str__()
        i = 0
        for n in self.contents['EnclosureName'].value:
            retString += '\n%s: State: %s Type: %s RollUp Status: %s Component Status: %s'  % \
                (n,
                 self.contents['EnclosureState'].value[i],
                 self.contents['EnclosureType'].value[i],
                 self.contents['EnclosureRollUpStatus'].value[i],
                 self.contents['EnclosureComponentStatus'].value[i])
            i += 1
        return retString

    def hasMD1000(self):
        return self.contents['EnclosureType'].hasMD1000()

class EnclosureName(DellOMSALocationName):
    OID = EnclosureTable.OID + '.2'

class EnclosureState(DellOMSAState):
    OID = EnclosureTable.OID + '.4'
    stateClass = DellPhysicalDeviceState

class EnclosureType(DellOMSAState):
    OID = EnclosureTable.OID + '.16'
    stateClass = DellEnclosureType

    # The hasMD1000 looks at the enclosure types in our value
    # attribute and returns True if it finds an enclosure type that
    # matches the string 'MD1000' and False otherwise.
    def hasMD1000(self):
        for v in self.value:
            if 'MD1000' in str(v):
               return True
        return False

    def overallStatus(self):
        return DellOverallStatus(DellOverallStatus.okState)

class EnclosureRollUpStatus(DellOMSAState):
    OID = EnclosureTable.OID + '.23'
    stateClass = DellStatus

class EnclosureComponentStatus(DellOMSAState):
    OID = EnclosureTable.OID + '.24'
    stateClass = DellStatus

class ArrayDiskTable(DellOMSATable):
    """
    The ArrayDiskTable class is a container that holds the Dell OMSA
    Array Disk objects
    """
    OID =PhysicalDevicesGroup.OID + '.4.1'
    tableName = 'Devices Array Disk'

    def __init__(self, connection):
        super(ArrayDiskTable, self).__init__(connection)
        # Note that we create a SystemsManagementSoftwareGroup object
        # here. That group is not really part of the ArrayDiskTable,
        # but we need it so that we can get the Dell OMSA version and
        # work around a bug in the DellArrayDiskDellCertified value in
        # Dell OMSA 7.1.0. In that version, a value of 0 corresponds
        # to a "Certified" disk. For older versions of Dell OMSA, a
        # value of 1 corresponds to a "Certified" disk.
        self.contents = {
            'ArrayDiskName':            ArrayDiskName(connection),
            'ArrayDiskState':           ArrayDiskState(connection),
            'ArrayDiskChannel':         ArrayDiskChannel(connection),
            'ArrayDiskRollUpStatus':    ArrayDiskRollUpStatus(connection),
            'ArrayDiskComponentStatus': ArrayDiskComponentStatus(connection),
            'ArrayDiskSmartAlertIndication': ArrayDiskSmartAlertIndication(connection),
            'ArrayDiskDellCertified':   ArrayDiskDellCertified(connection),
            'SystemsManagementSoftwareGroup': DellSystemsManagementSoftwareGroup.SystemsManagementSoftwareGroup(connection)
            }

    # We have our own update method so that we can get the Dell OMSA
    # version number and work around the bug in Dell OMSA 7.1.0 with
    # regard to Certified/NotCertified disks.
    def update(self):
        self.contents['SystemsManagementSoftwareGroup'].update()
        self.contents['ArrayDiskDellCertified'].setStateClass(self.contents['SystemsManagementSoftwareGroup'].dellOMSAVersion())
        super(ArrayDiskTable, self).update()

    def __str__(self):
        retString = super(ArrayDiskTable, self).__str__()
        i = 0
        for n in self.contents['ArrayDiskName'].value:
            retString += '\n%s: State: %s Channel: %s RollUp Status: %s Component Status: %s SmartAlertIndication: %s ArrayDiskDellCertified: %s'  % \
                (n,
                 self.contents['ArrayDiskState'].value[i],
                 self.contents['ArrayDiskChannel'].value[i],
                 self.contents['ArrayDiskRollUpStatus'].value[i],
                 self.contents['ArrayDiskComponentStatus'].value[i],
                 self.contents['ArrayDiskSmartAlertIndication'].value[i],
                 self.contents['ArrayDiskDellCertified'].value[i])
            i += 1
        return retString

    # ArrayDiskTable has its own overallStatus method because we want
    # to override the 'Warning' status when Dell OMSA reports the
    # disks as 'Foreign', as happens when two machines are connected
    # to the same RAID array (e.g., g2s3 and g2s4). If we find that
    # the ArrayDiskState is Foreign and the ArrayDiskRollUpStatus and
    # ArrayDiskComponentStatus are nonCritical, change the statuses to
    # ok and then call the parent class overallStatus method to
    # determine our overallStatus.
    def overallStatus(self):
        i = 0
        for name in self.contents['ArrayDiskName'].value:
            if str(self.contents['ArrayDiskState'].value[i]) == 'Foreign' and \
                    str(self.contents['ArrayDiskRollUpStatus'].value[i]) == 'nonCritical' and \
                    str(self.contents['ArrayDiskComponentStatus'].value[i]) == 'nonCritical':
                self.contents['ArrayDiskRollUpStatus'].value[i].setState('ok') 
                self.contents['ArrayDiskComponentStatus'].value[i].setState('ok')
            i += 1
        overallStatus = super(ArrayDiskTable,self).overallStatus()
        return overallStatus

    def hasForeign(self):
        return self.contents['ArrayDiskState'].isForeign()

class ArrayDiskName(DellOMSALocationName):
    OID = ArrayDiskTable.OID + '.2'

class ArrayDiskState(DellOMSAState):
    OID = ArrayDiskTable.OID + '.4'
    stateClass = DellArrayDiskState

    # Check to see if any of the disks are reported as 'Foreign'. If
    # so, return True. Otherwise, return False.
    def isForeign(self):
        for v in self.value:
            if str(v) == 'Foreign':
                return True
        return False

class ArrayDiskChannel(DellOMSALocationName):
    OID = ArrayDiskTable.OID + '.10'

class ArrayDiskRollUpStatus(DellOMSAState):
    OID = ArrayDiskTable.OID + '.23'
    stateClass = DellStatus

class ArrayDiskComponentStatus(DellOMSAState):
    OID = ArrayDiskTable.OID + '.24'
    stateClass = DellStatus

class ArrayDiskSmartAlertIndication(DellOMSAState):
    OID = ArrayDiskTable.OID + '.31'
    stateClass = DellArrayDiskSmartAlertIndicationState

class ArrayDiskDellCertified(DellOMSAState):
    OID = ArrayDiskTable.OID + '.36'
    stateClassDefault = DellArrayDiskDellCertified

    def setStateClass(self, dellOMSAVersion):
        if dellOMSAVersion == '7.1.0':
            # print 'using DellArrayDiskDellCertified_v7_1_0'
            self.stateClass = DellArrayDiskDellCertified_v7_1_0
        else:
            self.stateClass = self.stateClassDefault
        super(ArrayDiskDellCertified, self).update()

class ArrayDiskEnclosureConnectionTable(DellOMSATable):
    """
    The ArrayDiskEnclosureConnectionTable class is a container that
    holds the Dell OMSA Array Disk Enclosure Connection objects
    """
    OID =PhysicalDevicesGroup.OID + '.5.1'
    tableName = 'Devices Array Disk Enclosure Connection'

    def __init__(self, connection):
        super(ArrayDiskEnclosureConnectionTable, self).__init__(connection)
        self.contents = {
            'ArrayDiskEnclosureDiskName': ArrayDiskEnclosureDiskName(connection),
            'ArrayDiskNumber':            ArrayDiskNumber(connection),
            'ArrayDiskEnclosureName':     ArrayDiskEnclosureName(connection),
            'ArrayDiskEnclosureNumber':   ArrayDiskEnclosureNumber(connection),
            'ArrayDiskControllerName':    ArrayDiskControllerName(connection),
            'ArrayDiskControllerNumber':  ArrayDiskControllerNumber(connection)
            }

class ArrayDiskEnclosureDiskName(DellOMSALocationName):
    OID = ArrayDiskEnclosureConnectionTable.OID + '.2'

class ArrayDiskNumber(DellOMSALocationName):
    OID = ArrayDiskEnclosureConnectionTable.OID + '.3'

class ArrayDiskEnclosureName(DellOMSALocationName):
    OID = ArrayDiskEnclosureConnectionTable.OID + '.4'

class ArrayDiskEnclosureNumber(DellOMSALocationName):
    OID = ArrayDiskEnclosureConnectionTable.OID + '.5'

class ArrayDiskControllerName(DellOMSALocationName):
    OID = ArrayDiskEnclosureConnectionTable.OID + '.6'

class ArrayDiskControllerNumber(DellOMSALocationName):
    OID = ArrayDiskEnclosureConnectionTable.OID + '.7'

class FanTable(DellOMSATable):
    """
    The FanTable class is a container that holds the Dell OMSA Fan
    objects (specifically, fans contained in the Physical Devices
    Group)
    """
    OID = PhysicalDevicesGroup.OID + '.7.1'
    tableName = 'Devices Fan'

    def __init__(self, connection):
        super(FanTable, self).__init__(connection)
        self.contents = {
            'FanName':              FanName(connection),
            'FanState':             FanState(connection),
            'FanProbeCurrValue':    FanProbeCurrValue(connection),
            'FanRollUpStatus':      FanRollUpStatus(connection),
            'FanComponentStatus':   FanComponentStatus(connection)
           }

    def __str__(self):
        retString = super(FanTable, self).__str__()
        i = 0
        for n in self.contents['FanName'].value:
            retString += '\n%s: State: %s Current Value: %s RollUp Status: %s Component Status: %s'  % \
                (n,
                 self.contents['FanState'].value[i],
                 self.contents['FanProbeCurrValue'].value[i],
                 self.contents['FanRollUpStatus'].value[i],
                 self.contents['FanComponentStatus'].value[i])
            i += 1
        return retString

class FanName(DellOMSALocationName):
    OID = FanTable.OID + '.2'

class FanState(DellOMSAState):
    OID = FanTable.OID + '.4'
    stateClass = DellFanState

class FanProbeCurrValue(DellOMSA):
    OID = FanTable.OID + '.11'

    def overallStatus(self):
        return DellOverallStatus(DellOverallStatus.okState)

class FanRollUpStatus(DellOMSAState):
    OID = FanTable.OID + '.14'
    stateClass = DellStatus

class FanComponentStatus(DellOMSAState):
    OID = FanTable.OID + '.15'
    stateClass = DellStatus

class PowerSupplyTable(DellOMSATable):
    """
    The PowerSupplyTable class is a container that holds the Dell OMSA
    PowerSupply objects (specifically, Power Supplies contained in the
    Physical Devices Group)
    """
    OID = PhysicalDevicesGroup.OID + '.9.1'
    tableName = 'Devices Power Supply'

    def __init__(self, connection):
        super(PowerSupplyTable, self).__init__(connection)
        self.contents = {
            'PowerSupplyName':              PowerSupplyName(connection),
            'PowerSupplyState':             PowerSupplyState(connection),
            'PowerSupplyRollUpStatus':      PowerSupplyRollUpStatus(connection),
            'PowerSupplyComponentStatus':   PowerSupplyComponentStatus(connection)
           }

    def __str__(self):
        retString = super(PowerSupplyTable, self).__str__()
        i = 0
        for n in self.contents['PowerSupplyName'].value:
            retString += '\n%s: State: %s RollUp Status: %s Component Status: %s'  % \
                (n,
                 self.contents['PowerSupplyState'].value[i],
                 self.contents['PowerSupplyRollUpStatus'].value[i],
                 self.contents['PowerSupplyComponentStatus'].value[i])
            i += 1
        return retString

class PowerSupplyName(DellOMSALocationName):
    OID = PowerSupplyTable.OID + '.2'

class PowerSupplyState(DellOMSAState):
    OID = PowerSupplyTable.OID + '.4'
    stateClass = DellPowerSupplyState

class PowerSupplyRollUpStatus(DellOMSAState):
    OID = PowerSupplyTable.OID + '.8'
    stateClass = DellStatus

class PowerSupplyComponentStatus(DellOMSAState):
    OID = PowerSupplyTable.OID + '.9'
    stateClass = DellStatus

class TemperatureProbeTable(DellOMSATable):
    """
    The TemperatureProbeTable class is a container that holds the Dell
    OMSA Temperature Probe objects (specifically, temperature probes
    contained in the Physical Devices Group)
    """
    OID = PhysicalDevicesGroup.OID + '.11.1'
    tableName = 'Devices Temperature Probe'

    def __init__(self, connection):
        super(TemperatureProbeTable, self).__init__(connection)
        self.contents = {
            'TemperatureProbeName':            TemperatureProbeName(connection),
            'TemperatureProbeState':           TemperatureProbeState(connection),
            'TemperatureProbeUnit':            TemperatureProbeUnit(connection),
            'TemperatureProbeCurValue':        TemperatureProbeCurValue(connection),
            'TemperatureProbeRollUpStatus':    TemperatureProbeRollUpStatus(connection),
            'TemperatureProbeComponentStatus': TemperatureProbeComponentStatus(connection)
            }

    def __str__(self):
        retString = super(TemperatureProbeTable, self).__str__()
        i = 0
        for n in self.contents['TemperatureProbeName'].value:
            retString += '\n%s: State: %s RollUp Status: %s Component Status: %s Reading %s'  % \
                (n,
                 self.contents['TemperatureProbeState'].value[i],
                 self.contents['TemperatureProbeRollUpStatus'].value[i],
                 self.contents['TemperatureProbeComponentStatus'].value[i],
                 self.contents['TemperatureProbeCurValue'].value[i])
            i += 1
        return retString

    # TemperatureProbeTable has its own update method because we have
    # to update the TemperatureProbeUnit item first to determine the
    # units of the TemperatureProbeCurValue items and then, based on
    # the TemperatureProbeUnit value, convert the
    # TemperatureProbeCurValue to Deg C (we want all temperatures to
    # be in consistent units and Deg C seems like the best one to use
    # since it looks like the default unit is celcius and chassis
    # temperature is also reported in Deg C).
    def update(self):
        super(TemperatureProbeTable, self).update()
        i = 0
        for v in self.contents['TemperatureProbeUnit'].value:
            if 'celcius' in str(v).lower():
                # We don't need to do anything if units are already Celcius
                pass
            elif 'fahrenheit' in str(v).lower():
                # Convert from Fahrenheit to Celcius
                f_value = self.contents['TemperatureProbeCurValue'].value[i].value
                self.contents['TemperatureProbeCurValue'].value[i].value = (f_value - 32) * 5 / 9
            # Unit will always be Deg C based on the above conversions
            self.contents['TemperatureProbeCurValue'].value[i].units = 'Deg C'
            i += 1

    def munin_config(self):
        print 'graph_title %s MD1000 Enclosure Temperature Readings' % (socket.gethostname())
        print 'graph_args --base 1000 -l 0'
        print 'graph_vlabel Temperature (Deg C)'
        print 'graph_category MD1000_Enclosure'
        print 'graph_info This graph shows the temperature for all sensors.'
        print 'graph_period second'
        i = 0
        for n in self.contents['TemperatureProbeName'].value:
            print 'encl_temps_%s.label %s' % (i, n)
            i += 1

    def munin_report(self):
        i = 0
        for n in self.contents['TemperatureProbeName'].value:
            value = self.contents['TemperatureProbeCurValue'].value[i].value
            print 'encl_temps_%s.value %s' % (i, value)
            i += 1

class TemperatureProbeName(DellOMSALocationName):
    OID = TemperatureProbeTable.OID + '.2'

class TemperatureProbeState(DellOMSAState):
    OID = TemperatureProbeTable.OID + '.4'
    stateClass = DellTemperatureProbeState

class TemperatureProbeUnit(DellOMSA):
    OID = TemperatureProbeTable.OID + '.6'

    def overallStatus(self):
        return DellOverallStatus(DellOverallStatus.okState)

class TemperatureProbeCurValue(DellOMSAReading):
    OID = TemperatureProbeTable.OID + '.11'
    conversion = 1.

class TemperatureProbeRollUpStatus(DellOMSAState):
    OID = TemperatureProbeTable.OID + '.12'
    stateClass = DellStatus

class TemperatureProbeComponentStatus(DellOMSAState):
    OID = TemperatureProbeTable.OID + '.13'
    stateClass = DellStatus

class EnclosureManagementModuleTable(DellOMSATable):
    """
    The EnclosureManagementModuleTable class is a container that holds the Dell OMSA
    EnclosureManagementModule objects
    """
    OID = PhysicalDevicesGroup.OID + '.13.1'
    tableName = 'Devices Enclosure Management Module'

    def __init__(self, connection):
        super(EnclosureManagementModuleTable, self).__init__(connection)
        self.contents = {
            'EnclosureManagementModuleName':              EnclosureManagementModuleName(connection),
            'EnclosureManagementModuleState':             EnclosureManagementModuleState(connection),
            'EnclosureManagementModuleType':              EnclosureManagementModuleType(connection),
            'EnclosureManagementModuleRollUpStatus':      EnclosureManagementModuleRollUpStatus(connection),
            'EnclosureManagementModuleComponentStatus':   EnclosureManagementModuleComponentStatus(connection)
           }

    def __str__(self):
        retString = super(EnclosureManagementModuleTable, self).__str__()
        i = 0
        for n in self.contents['EnclosureManagementModuleName'].value:
            retString += '\n%s: State: %s Type: %s RollUp Status: %s Component Status: %s'  % \
                (n,
                 self.contents['EnclosureManagementModuleState'].value[i],
                 self.contents['EnclosureManagementModuleType'].value[i],
                 self.contents['EnclosureManagementModuleRollUpStatus'].value[i],
                 self.contents['EnclosureManagementModuleComponentStatus'].value[i])
            i += 1
        return retString

class EnclosureManagementModuleName(DellOMSALocationName):
    OID = EnclosureManagementModuleTable.OID + '.2'

class EnclosureManagementModuleState(DellOMSAState):
    OID = EnclosureManagementModuleTable.OID + '.4'
    stateClass = DellEnclosureManagementModuleState

class EnclosureManagementModuleType(DellOMSAState):
    OID = EnclosureManagementModuleTable.OID + '.7'
    stateClass = DellEnclosureManagementModuleType

class EnclosureManagementModuleRollUpStatus(DellOMSAState):
    OID = EnclosureManagementModuleTable.OID + '.10'
    stateClass = DellStatus

class EnclosureManagementModuleComponentStatus(DellOMSAState):
    OID = EnclosureManagementModuleTable.OID + '.11'
    stateClass = DellStatus

class BatteryTable(DellOMSATable):
    """
    The BatteryTable class is a container that holds the Dell OMSA
    Battery objects
    """
    OID = PhysicalDevicesGroup.OID + '.15.1'
    tableName = 'Devices Battery'

    def __init__(self, connection):
        super(BatteryTable, self).__init__(connection)
        self.contents = {
            'BatteryName':              BatteryName(connection),
            'BatteryState':             BatteryState(connection),
            'BatteryRollUpStatus':      BatteryRollUpStatus(connection),
            'BatteryComponentStatus':   BatteryComponentStatus(connection),
            'BatteryPredictedCapacity': BatteryPredictedCapacity(connection),
            'BatteryNextLearnTime':     BatteryNextLearnTime(connection),
            'BatteryLearnState':        BatteryLearnState(connection)
           }

    def __str__(self):
        retString = super(BatteryTable, self).__str__()
        i = 0
        for n in self.contents['BatteryName'].value:
            # For the PERC H810 card, Dell OMSA does not report
            # the BatteryNextLearnTime or the BatteryLearnState,
            # despite the fact that the card does have a battery.
            # If the BatteryLearnTime/BatteryLearnState tables are
            # missing the expected values, set them to 0/Idle,
            # respectively, so that we don't generate an exception.
            try:
                batteryNextLearnTime = self.contents['BatteryNextLearnTime'].value[i]
            except IndexError:
                batteryNextLearnTime = 0
            try:
                batteryLearnState = self.contents['BatteryLearnState'].value[i]
            except IndexError:
                batteryLearnState = 'Idle'
            retString += '\n%s: State: %s RollUp Status: %s Component Status: %s Predicted Capacity: %s Next Learn Time: %s Learn State: %s'  % \
                (n,
                 self.contents['BatteryState'].value[i],
                 self.contents['BatteryRollUpStatus'].value[i],
                 self.contents['BatteryComponentStatus'].value[i],
                 self.contents['BatteryPredictedCapacity'].value[i],
                 batteryNextLearnTime,
                 batteryLearnState)
            i += 1
        return retString

class BatteryName(DellOMSALocationName):
    OID = BatteryTable.OID + '.2'

class BatteryState(DellOMSAState):
    OID = BatteryTable.OID + '.4'
    stateClass = DellBatteryState

class BatteryRollUpStatus(DellOMSAState):
    OID = BatteryTable.OID + '.5'
    stateClass = DellStatus

class BatteryComponentStatus(DellOMSAState):
    OID = BatteryTable.OID + '.6'
    stateClass = DellStatus

class BatteryPredictedCapacity(DellOMSAState):
    OID = BatteryTable.OID + '.10'
    stateClass = DellBatteryPredictedCapacity

class BatteryNextLearnTime(DellOMSAReading):
    OID = BatteryTable.OID + '.11'
    conversion = 1.
    units = 'hours'

class BatteryLearnState(DellOMSAState):
    OID = BatteryTable.OID + '.12'
    stateClass = DellBatteryLearnState

class LogicalDevicesGroup(DellOMSAGroup):
    """
    The LogicalDevicesGroup class is a container that holds the Dell
    OMSA Logical Devices objects
    """
    OID = StorageManagementGroup.OID + '.140'
    groupName = 'Logical Devices'

    def __init__(self, connection):
        super(LogicalDevicesGroup, self).__init__(connection)
        self.contents = {
            'VirtualDiskTable': VirtualDiskTable(connection)
            }

    def __str__(self):
        retString = super(LogicalDevicesGroup, self).__str__()
        return retString

class VirtualDiskTable(DellOMSATable):
    """
    The VirtualDiskTable class is a container that holds the Dell OMSA
    Virtual Disk objects
    """
    OID = LogicalDevicesGroup.OID + '.1.1'
    tableName = 'Virtual Disk'

    def __init__(self, connection):
        super(VirtualDiskTable, self).__init__(connection)
        self.contents = {
            'VirtualDiskName':            VirtualDiskName(connection),
            'VirtualDeviceDiskName':      VirtualDeviceDiskName(connection),
            'VirtualDiskState':           VirtualDiskState(connection),
            'VirtualDiskRollUpStatus':    VirtualDiskRollUpStatus(connection),
            'VirtualDiskComponentStatus': VirtualDiskComponentStatus(connection)
            }

    def __str__(self):
        retString = super(VirtualDiskTable, self).__str__()
        i = 0
        for n in self.contents['VirtualDeviceDiskName'].value:
            retString += '\n%s: Name: %s State: %s RollUp Status: %s Component Status: %s'  % \
                (n,
                 self.contents['VirtualDiskName'].value[i],
                 self.contents['VirtualDiskState'].value[i],
                 self.contents['VirtualDiskRollUpStatus'].value[i],
                 self.contents['VirtualDiskComponentStatus'].value[i])
            i += 1
        return retString

class VirtualDiskName(DellOMSALocationName):
    OID = VirtualDiskTable.OID + '.2'

class VirtualDeviceDiskName(DellOMSALocationName):
    OID = VirtualDiskTable.OID + '.3'

class VirtualDiskState(DellOMSAState):
    OID = VirtualDiskTable.OID + '.4'
    stateClass = DellVirtualDiskState

class VirtualDiskRollUpStatus(DellOMSAState):
    OID = VirtualDiskTable.OID + '.19'
    stateClass = DellStatus

class VirtualDiskComponentStatus(DellOMSAState):
    OID = VirtualDiskTable.OID + '.20'
    stateClass = DellStatus


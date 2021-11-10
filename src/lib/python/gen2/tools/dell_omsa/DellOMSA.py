#
# DellOMSA.py -- Classes to facilitate reading computer status
# from Dell's OpenManage Server Administrator (OMSA) software. We use
# SNMP (Simple Network Management Protocol) messages to communicate
# with the OMSA.
#
# For more information on Dell OMSA, see:
# http://support.dell.com/support/edocs/software/svradmin/6.5/en/SNMP/HTML/index.htm
#
# The Dell OMSA Standard Data Type Definitions are documented here:
# http://support.dell.com/support/edocs/software/svradmin/6.5/en/SNMP/HTML/snmpaa.htm
#
# Russell Kackley - 17 May 2011
#
import os
import logging
import logging.handlers
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.proto import rfc1155
from pyasn1.type import univ

class StateNotFoundError(Exception):
    pass

class DellOMSAStateType(object):
    """
    DellOMSAStateType is the Base class for all the Dell OMSA State
    classes, e.g., DellStatus, DellStatusProbe, etc.
    """
    # Default okStates and warningStates attributes are empty
    # tuples. Sub-classes will usually override them with their own
    # values.
    okStates = ()
    warningStates = ()

    def __init__(self, state):
        if state in self.states:
            self.state = state
        else:
            raise StateNotFoundError('State not found in states attribute: ' + str(state))

    def __str__(self):
        return self.states[self.state]

    def __int__(self):
        return int(self.state)

    def setState(self, status):
        """
        The DellOMSAStateType.setState method allows us to set the
        status with a text string, i.e, Ok, Warning, ..., rather than
        with the integer key (0, 1, ...).
        """
        found = 0
        for s in self.states:
            if status == self.states[s]:
                self.state = s
                found = 1
        if not found:
            raise StateNotFoundError('Status not found in states attribute: ' + status)

class DellOverallStatus(DellOMSAStateType):
    """
    The DellOverallStatus class is used to record the overall status
    of the Dell OMSA Group or Table containers.
    """
    okState      = 0
    warningState = 1
    errorState   = 2
    unknownState = 3
    states = {
        okState:      'Ok',
        warningState: 'Warning',
        errorState:   'Error',
        unknownState: 'Unknown'
        }

    def setStatus(self, status):
        """
        The DellOverallStatus.setStatus method allows us to set the
        status with a text string, i.e, Ok, Warning, Error, or
        Unknown, rather than with the integer key (0, 1, 2, or 3).
        """
        super(DellOverallStatus, self).setState(status)

class DellBoolean(DellOMSAStateType):
    """
    The DellBoolean class implements the DellBoolean datatype from
    Table 29-1 in the Dell OMSA Reference Guide - Standard Data Type
    Definitions. Note that DellBoolean doesn't have an okStates
    attribute. That's because some objects might consider False ok
    while False is an error for others. Normally, we would use
    DellBooleanFalseOk or DellBooleanTrueOk instead of just
    DellBoolean so that can have the okStates attribute available to
    us.
    """
    states = {
        0: 'False',
        1: 'True'
        }

class DellBooleanFalseOk(DellBoolean):
    """
    The DellBooleanFalseOk class inherits from the DellBoolean class
    with the only difference being that DellBooleanFalseOk adds the
    okStates attribute.
    """
    okStates = ('False')

class DellBooleanTrueOk(DellBoolean):
    """
    The DellBooleanTrueOk class inherits from the DellBoolean class
    with the only difference being that DellBooleanTrueOk adds the
    okStates attribute.
    """
    okStates = ('True')

class DellStatus(DellOMSAStateType):
    """
    The DellStatus class implements the data values from Table 29-5 in
    the Dell OMSA Reference Guide - Standard Data Type Definitions
    """
    okStates = ('ok')
    warningStates = ('nonCritical')
    states = {
        1: 'other',
        2: 'unknown',
        3: 'ok',
        4: 'nonCritical',
        5: 'critical',
        6: 'nonRecoverable'
        }

class DellStatusRedundancy(DellOMSAStateType):
    """
    The DellStatusRedundancy class implements the data values from
    Table 29-6 in the Dell OMSA Reference Guide - Standard Data Type
    Definitions
    """
    okStates = ('full')
    warningStates = ('degraded')
    states = {
        1: 'other',
        2: 'unknown',
        3: 'full',
        4: 'degraded',
        5: 'lost',
        6: 'notRedundant'
        }
    def __init__(self, state):
        super(DellStatusRedundancy, self).__init__(state)

class DellStatusProbe(DellOMSAStateType):
    """
    The DellStatusProbe class implements the data values from Table
    29-7 in the Dell OMSA Reference Guide - Standard Data Type
    Definitions
    """
    okStates = ('ok')
    warningStates = ('nonCriticalUpper', 'nonCriticalLower')
    states = {
        1: 'other',
        2: 'unknown',
        3: 'ok',
        4: 'nonCriticalUpper',
        5: 'CriticalUpper',
        6: 'nonRecoverableUpper',
        7: 'nonCriticalLower',
        8: 'criticalLower',
        9: 'nonRecoverableLower',
        10: 'failed'
        };
										
class DellStateCapabilities(DellOMSAStateType):
    """
    The DellStateCapabilities class implements the data values from
    Table 29-2 in the Dell OMSA Reference Guide - Standard Data Type
    Definitions
    """
    okStates = ('noCapabilities', 'enableCapable')
    states = {
        0: 'noCapabilities',
        1: 'unknownCapabilities',
        2: 'enableCapable',
        4: 'notReadyCapable',
        6: 'enableAndNotReadyCapable',
        };
										
class DellStateSettings(DellOMSAStateType):
    """
    The DellStateSettings class implements the data values from Table
    29-3 in the Dell OMSA Reference Guide - Standard Data Type
    Definitions
    """
    okStates = ('enabled')
    enabled = 2
    notReady = 4
    states = {
        0: 'noCapabilities',
        1: 'unknown',
        2: 'enabled',
        4: 'notReady',
        6: 'enableAndNotReady',
        };

class DellMeasurement:
    def __init__(self, value, units):
        self.value = value
        self.units = units

    def get(self):
        return {'value': self.value, 'units': self.units}

    def __str__(self):
        return str(self.value) + ' ' + self.units

class OidNotFoundError(Exception):
    pass

class DellOID:
    """
    DellOID is the base of all the Dell OID's. The 674 at the end of
    the OID is the identifier assigned to Dell.
    """
    OID = '.1.3.6.1.4.1.674'

class DellChassisOID:
    """
    DellChassisOID is the base OID for the Power, Thermal, and Memory
    Groups.
    """
    OID = DellOID.OID + '.10892.1'

class DellStorageManagementOID:
    """
    DellStorageManagementOID is the base OID for the StorageManagement
    Group.
    """
    OID = DellOID.OID + '.10893.1'

class DellOMSA(object):
    """
    DellOMSA is the Base class for all the Dell OMSA classes, e.g.,
    DellOMSAState, DellOMSAReading, etc. The update method in
    this class is what calls the netsnmp methods to get the
    information from the Dell OMSA system.
    """
    def __init__(self, connection):
        self.connection = connection
        self.value = None

    def get(self, update):
        if update:
            self.update()
        return self.value

    def update(self):
        # We don't know if the OID is a leaf or a node in the
        # tree. First, assume the OID is a node in the tree, so use
        # the walk method
#        print 'calling walk OID ' + self.OID
        result = self.connection.walk(self.OID)

        # If OID was a actually a leaf, result will be an empty
        # list. In that case, assume OID is a leaf, so try the get
        # method
        value = []
        if len(result) == 0:
            result = self.connection.get(self.OID)
            # Check the last element of the leaf result. If the value
            # part is a univ.Null object, then the OID wasn't found in
            # the MIB. Raise an OidNotFoundError exception. Otherwise,
            # set our value attribute to the result.
            if isinstance(result[-1][1], univ.Null):
                raise OidNotFoundError('OID not found ' + self.OID)
            else:
                # For a leaf, the result will be a list with a single
                # element, which will be a tuple of ManagedObjects
                # (see pysnmp documentation for more info). Each
                # ManagedObject is a tuple of ObjectName (i.e., the
                # OID) and ObjectValue (i.e., the value of the OID).
                # Save the ObjectValue and convert it to a string
                # because that is what the rest of the DellOMSA
                # classes want.
                value.append(str(result[0][1]))
        else:
            # Check the last element of the tree result. If the value
            # part is a univ.Null object, then the OID wasn't found in
            # the MIB. Raise an OidNotFoundError exception. Otherwise,
            # set our value attribute to the result.
           if isinstance(result[-1][-1][1], univ.Null):
               raise OidNotFoundError('OID not found ' + self.OID)
           else:
               # For a tree, the result will be a list of leaf node
               # lists, so we have to iterate through them and save
               # the ObjectValue parts, similar to what we do for
               # leaves (see above).
               for r in result:
                   value.append(str(r[0][1]))
        self.value = value

    def overallStatus(self):
        # Return a DellOverallStatus object with the value set to
        # 'Unknown'
        return DellOverallStatus(DellOverallStatus.unknownState)

class DellOMSAState(DellOMSA):

    def update(self):
        # Call our base class's update method to get the current
        # values from the Dell OMSA. The results will be stored as a
        # list of items in our value attribute.
        super(DellOMSAState, self).update()

        # Iterate through the list of returned values and create a new
        # list with the values instantiated as objects of the type
        # specified by our stateClass attribute. Store this new list
        # in our value attribute
        value = []
        for v in self.value:
            value.append(self.stateClass(int(v)))
        self.value = value

    def overallStatus(self):

        # Call our base class's overallStatus method, which will set
        # overallStatus to 'Unknown'
        overallStatus = super(DellOMSAState, self).overallStatus()

        # Iterate through the list of objects in our value attribute
        for v in self.value:
            # On the first iteration, overallStatus will be
            # 'Unknown'. In that case, set the overallStatus to be
            # consistent with the status of the first item in our
            # value attribute.
            if str(overallStatus) == 'Unknown':
                # If this item matches any of our stateClass's
                # okStates values, set status to 'Ok'. Otherwise,
                # check to see if matches any of the warningStates
                # values. If so, set status to 'Warning'. For any
                # other condition, set status to 'Error'.
                if str(v) in self.stateClass.okStates:
                    overallStatus.setStatus('Ok')
                elif str(v) in self.stateClass.warningStates:
                    overallStatus.setStatus('Warning')
                else:
                    overallStatus.setStatus('Error')
            else:
                # On subsequent iterations, we need to change
                # overallStatus only when the value of the item is
                # something other than one of the states listed in our
                # stateClass's okStates value.
                if str(v) not in self.stateClass.okStates:
                    # If the status matches one of the warningStates,
                    # set status to 'Warning'. Otherwise, set status
                    # to 'Error'
                    if str(v) in self.stateClass.warningStates:
                        overallStatus.setStatus('Warning')
                    else:
                        overallStatus.setStatus('Error')
        return overallStatus

class DellOMSAReading(DellOMSA):
    conversion = 1.0
    units = 'unknown'

    def update(self):
        super(DellOMSAReading, self).update()
        value = []
        for v in self.value:
            value.append(DellMeasurement(float(v) * self.conversion, self.units))
        self.value = value

    def overallStatus(self):
        return DellOverallStatus(DellOverallStatus.okState)

class DellOMSALocationName(DellOMSA):
    def overallStatus(self):
        return DellOverallStatus(DellOverallStatus.okState)

class DellOMSAProbeType(DellOMSAState):
    def overallStatus(self):
        return DellOverallStatus(DellOverallStatus.okState)

class LoggerUndefinedError(Exception):
    pass

class DellOMSAGroup(object):
    def __init__(self, connection):
        self.connection = connection
        self.contents = {}
        self.logger = None

    def update(self):
        for key in self.contents:
            self.contents[key].update()

    def get(self):
        self.update()
        return self.contents

    def __str__(self):
        overallStatus = self.overallStatus()
        retString = self.groupName + ' Group: Overall Status: ' + str(int(overallStatus)) + ' ' + str(overallStatus) + '\n'
        for key in self.contents:
            retString += self.contents[key].__str__() + '\n\n'
        return retString

    def setLogging(self, directory):
        self.lfh = logging.handlers.RotatingFileHandler(os.path.join(directory, self.logFilename) + '.log', maxBytes=100000000, backupCount=1)
        logging.getLogger(self.logFilename).addHandler(self.lfh)
        formatter = logging.Formatter(fmt='%(asctime)s: %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')
        self.lfh.setFormatter(formatter)
        self.logger = logging.getLogger(self.logFilename)
        self.logger.setLevel(logging.INFO)

    def setLogger(self, logger):
        self.logger = logger

    def log(self):
        if self.logger == None:
            raise LoggerUndefinedError('Logger undefined')
        else:
            for line in str(self).split('\n'):
                if (len(line) > 0):
                    self.logger.info(line)

    def overallStatus(self):
        # Set the initial status to Unknown
        overallStatus = DellOverallStatus(DellOverallStatus.unknownState)
        # Iterate through our contents attribute and modify
        # overallStatus if we get a status value with an integer value
        # greater than our existing status. This works because Ok is
        # 0, Warning is 1, and Error is 2.
        i = 0
        for key in self.contents:
            # First time through, set overallStatus to the status of
            # the contents object
            if i == 0:
                overallStatus.setStatus(str(self.contents[key].overallStatus()))
            else:
                # On subsequent iterations, set the status value only
                # if the new value has a greater integer value than
                # the existing one (i.e., worse status).
                if int(self.contents[key].overallStatus()) > int(overallStatus):
                    overallStatus.setStatus(str(self.contents[key].overallStatus()))
            i += 1
        return overallStatus

class DellOMSATable(DellOMSAGroup):

    def __str__(self):
        overallStatus = self.overallStatus()
        retString = self.tableName + ' Table: Overall Status: ' + str(int(overallStatus)) + ' ' + str(overallStatus) + '\n'
        return retString

class ConnectionError(Exception):
    pass

class Connection(object):
    """
    The Connection class is a wrapper around the
    pysnmp CommandGenerator class that makes it easier to use.
    """
    DEFAULT_SNMP_PORT = 161
    def __init__(self, hostname, community, version):
        # version was used by netsnmp. pysnmp doesn't use version, but
        # leave it in place for backwards compatibility.
        self.cmdGen = cmdgen.CommandGenerator()
        self.authData = cmdgen.CommunityData('my-agent', community, 0)
        self.transTarget = cmdgen.UdpTransportTarget((hostname, self.DEFAULT_SNMP_PORT))

        # Check to see if we can use the supplied hostname and
        # community to get the sysName (i.e., the hostname). If we
        # can't get the value, then something is wrong, so raise an
        # exception.
        sysNameOID = '1.3.6.1.2.1.1.5.0'
        errorIndication, errorStatus, errorIndex, result = self.cmdGen.getCmd(self.authData, self.transTarget, rfc1155.ObjectName(sysNameOID))
        if len(result) == 0 or isinstance(result[-1][1], univ.Null):
            raise ConnectionError('Connection failed')

    def walk(self, OID):
        # It seems like pysnmp doesn't really fill in anything in
        # errorIndication or errorStatus (as of 6 July 2011), so don't
        # do anything with them for now.
        errorIndication, errorStatus, errorIndex, result = self.cmdGen.nextCmd(self.authData, self.transTarget, rfc1155.ObjectName(OID))
        return result

    def get(self, OID):
        # It seems like pysnmp doesn't really fill in anything in
        # errorIndication or errorStatus (as of 6 July 2011), so don't
        # do anything with them for now.
        errorIndication, errorStatus, errorIndex, result = self.cmdGen.getCmd(self.authData, self.transTarget, rfc1155.ObjectName(OID))
        return result

#
# DellOMSA.py -- Classes to facilitate reading computer status from
# Dell's OpenManage Server Administrator (OMSA) software. We use SNMP
# (Simple Network Management Protocol) messages to communicate with
# the OMSA. The class in this file are represents the top-level of the
# Dell OMSA system. This class instantiates objects from the
# DellDeviceGroup, DellMemoryGroup, DellPowerGroup, DellThermalGroup,
# and DellStorageManagementGroup.
#
# For more information on the Dell OMSA Memory Group, see:
# http://support.dell.com/support/edocs/software/svradmin/6.5/en/SNMP/HTML/snmpc16.htm
#
# See also the Dell*.py file for classes used by this file.
#
# Russell Kackley - 13 June 2011
#
import os
import socket
import logging
import logging.handlers
from DellOMSA import *
import DellDeviceGroup
import DellMemoryGroup
import DellPowerGroup
import DellThermalGroup
import DellStorageManagementGroup

class DellOMSASystem(object):
    def __init__(self, connection):
        self.groups = {'powerGroup': DellPowerGroup.PowerGroup(connection),
                       'thermalGroup': DellThermalGroup.ThermalGroup(connection),
                       'deviceGroup': DellDeviceGroup.DeviceGroup(connection),
                       'memoryGroup': DellMemoryGroup.MemoryGroup(connection),
                       'storageManagementGroup': DellStorageManagementGroup.StorageManagementGroup(connection)}
        self.hostname = socket.gethostname()
        self.logFilename = self.hostname + '_OMSA.log'

    def update(self):
        for group in self.groups:
            self.groups[group].update()

    def log(self):
        if self.logger == None:
            raise LoggerUndefinedError('Logger undefined')
        else:
            for line in str(self).split('\n'):
                if (len(line) > 0):
                    self.logger.info(line)

    def __str__(self):
        overallStatus = self.overallStatus()
        retString = self.hostname + ': Overall Status: ' + str(int(overallStatus)) + ' ' + str(overallStatus) + '\n'
        for group in self.groups:
            retString += self.groups[group].__str__() + '\n\n'
        return retString

    def setLogging(self, directory):
        self.lfh = logging.handlers.RotatingFileHandler(os.path.join(directory, self.logFilename), maxBytes=10000000, backupCount=10)
        logging.getLogger(self.logFilename).addHandler(self.lfh)
        formatter = logging.Formatter(fmt='%(asctime)s: %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')
        self.lfh.setFormatter(formatter)
        self.logger = logging.getLogger(self.logFilename)
        self.logger.setLevel(logging.INFO)
        for group in self.groups:
            self.groups[group].setLogger(self.logger)
        
    def overallStatus(self):
        overallStatus = DellOverallStatus(DellOverallStatus.unknownState)
        i = 0
        for group in self.groups:
            if str(self.groups[group].overallStatus()) == 'Ok':
                if i == 0:
                    overallStatus.setStatus('Ok')
            else:
                overallStatus.setStatus(str(self.groups[group].overallStatus()))
            i += 1
        return overallStatus


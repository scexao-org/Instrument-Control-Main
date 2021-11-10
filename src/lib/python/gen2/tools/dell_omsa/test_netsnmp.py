#!/usr/bin/env python

# A simple test of Python/SNMP/Dell OMSA
# Russell Kackley - 5 May 2011 

import netsnmp

# Set up some OID's to test
sysName1 = 'sysName.0'
sysName2 = '.iso.org.dod.internet.mgmt.mib-2.system.sysName.0'
sysName3 = '.1.3.6.1.2.1.1.5.0'

sysRoot1 = '.iso.org.dod.internet.mgmt.mib-2.system' # fails - can't use text OID as OID for netsnmp.Session.walk method
sysRoot2 = '.1.3.6.1.2.1.1'

DellRoot1 = '.iso.org.dod.internet.private.enterprises.674' # 674 is the Dell identifier
DellRoot2 = '.1.3.6.1.4.1.674'

coolingDeviceRoot1 = DellRoot1 + '.10892.1.700.12.1.6' # fails - can't mix text OID with dotted-decimal OID
coolingDeviceRoot2 = DellRoot2 + '.10892.1.700.12.1.6'

coolingDeviceReading1 = DellRoot1 + '.10892.1.700.12.1.6.1.1' # fails - can't mix text OID with dotted-decimal OID
coolingDeviceReading2 = DellRoot2 + '.10892.1.700.12.1.6.1.1'

leaves = [sysName1, sysName2, sysName3, coolingDeviceReading2]

roots = [sysRoot2, coolingDeviceRoot2]

# Connect to default SNMP - DestHost=localhost, Community=public
session = netsnmp.Session(Version = 2)

# Loop through all the leaves
for leaf in leaves:
    print 'leaf is ' + leaf
    result = session.get(netsnmp.VarList(netsnmp.Varbind(leaf)))
    if result[0] == None:
        print 'Failed to get value for leaf ' + leaf
    else:
        print 'result is ' + result[0]

print ' '

# Loop through all the roots
for root in roots:
    print 'root is ' + root
    result = session.walk(netsnmp.VarList(netsnmp.Varbind(root)))
    if len(result) == 0:
        print 'Failed to get value for root ' + root
    else:
        print 'result is '
        print result

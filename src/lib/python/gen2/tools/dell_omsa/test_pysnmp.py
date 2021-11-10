#!/usr/bin/env python
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.proto import rfc1155
from pyasn1.type import univ

# Set up some OID's to test
sysName1 = 'sysName.0' # Fails - PyASN1 requires integer OID
sysName2 = '.iso.org.dod.internet.mgmt.mib-2.system.sysName.0' # Fails - PyASN1 requires integer OID
sysName3 = '.1.3.6.1.2.1.1.5.0'

sysRoot1 = '.iso.org.dod.internet.mgmt.mib-2.system' # fails - PyASN1 requires integer OID
sysRoot2 = '.1.3.6.1.2.1.1'

DellRoot1 = '.iso.org.dod.internet.private.enterprises.674' # 674 is the Dell identifier, but, fails - PyASN1 requires integer OID
DellRoot2 = '.1.3.6.1.4.1.674'

coolingDeviceRoot1 = DellRoot1 + '.10892.1.700.12.1.6' # fails - PyASN1 requires integer OID
coolingDeviceRoot2 = DellRoot2 + '.10892.1.700.12.1.6'

coolingDeviceReading1 = DellRoot1 + '.10892.1.700.12.1.6.1.1' # fails - PyASN1 requires integer OID
coolingDeviceReading2 = DellRoot2 + '.10892.1.700.12.1.6.1.1'

leaves = [sysName3, coolingDeviceReading2]

roots = [sysRoot2, coolingDeviceRoot2]

# Setup objects to connect to SNMP on localhost
cg = cmdgen.CommandGenerator()
authData = cmdgen.CommunityData('my-agent', 'public', 0)
transTarget = cmdgen.UdpTransportTarget(('localhost', 161))

# Loop through all the leaves
for leaf in leaves:
    print 'leaf is ' + leaf
    errorIndication, errorStatus, errorIndex, result = cg.getCmd(authData, transTarget, rfc1155.ObjectName(leaf))
    if errorIndication == None and len(result) > 0 and not isinstance(result[-1][1], univ.Null) :
        print 'result is ', result
    else:
        print 'Failed to get value for leaf ' + leaf, result

print ' '

# Loop through all the roots
for root in roots:
    print 'root is ' + root
    errorIndication, errorStatus, errorIndex, result = cg.nextCmd(authData, transTarget, rfc1155.ObjectName(root))
    if errorIndication == None and len(result) > 0:
        print 'result is ', result
    else:
        print 'Failed to get value for root ' + root, result

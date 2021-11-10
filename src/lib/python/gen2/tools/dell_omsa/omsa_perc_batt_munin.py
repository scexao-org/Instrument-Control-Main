#!/usr/bin/env python
"""
Report PERC batteries next learn time(s) in a form that can be used by
munin to produce a time-history plot of the time(s). This script
depends on the Dell OMSA system being up and running.

Russell Kackley - 15 September 2011
"""
import sys
import DellOMSA
import DellStorageManagementGroup

# Connect to the Dell OMSA via SNMP
try:
    connection = DellOMSA.Connection('localhost', 'public', 2)
except DellOMSA.ConnectionError:
    print 'Connection error occured'
    exit(1)

# The PhysicalDevicesGroup object has the controller and battery
# information, so create one and update its values.
pdg = DellStorageManagementGroup.PhysicalDevicesGroup(connection)
pdg.update()

# Munin populates sys.argv[1] with "" (an empty argument), let's remove it.
sys.argv = [x for x in sys.argv if x]

if len(sys.argv) > 1:
    if sys.argv[1].lower() == "autoconf":
        # The update ran earlier, since we got this far autoconf is good.
        print "true"
    elif sys.argv[1].lower() == "config":
        # Tell munin plot titles, curve titles, etc.
        pdg.munin_config_battery()
else:
    # Tell munin the current values
    pdg.munin_report_battery()

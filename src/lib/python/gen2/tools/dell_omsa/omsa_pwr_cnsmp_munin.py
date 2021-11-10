#!/usr/bin/env python
"""
Report system board power consumption in a form that can be used by
munin to produce a time-history plot of the output power
consumption. This script depends on the Dell OMSA system being up and
running.

Russell Kackley - 9 August 2011
"""
import sys
import DellOMSA
import DellPowerGroup

# Connect to the Dell OMSA via SNMP
try:
    connection = DellOMSA.Connection('localhost', 'public', 2)
except DellOMSA.ConnectionError:
    print 'Connection error occured'
    exit(1)

# The AmperageProbeTable object has the output current values, so
# create one and update its values.
apt = DellPowerGroup.AmperageProbeTable(connection)
apt.update()

# Munin populates sys.argv[1] with "" (an empty argument), let's
# remove it.
sys.argv = [x for x in sys.argv if x]

if len(sys.argv) > 1:
    if sys.argv[1].lower() == "autoconf":
        # The update ran earlier, since we got this far autoconf is
        # good.
        print "true"
    elif sys.argv[1].lower() == "config":
        # Tell munin plot titles, curve titles, etc.
        apt.munin_config_watts()
else:
    # Tell munin the current values
    apt.munin_report_watts()

#!/usr/bin/env python
"""
Report chassis power supply input voltage(s) in a form that can be
used by munin to produce a time-history plot of the input
voltage(s). This script depends on the Dell OMSA system being up and
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

# The VoltageProbeTable object has the output current values, so
# create one and update its values.
vpt = DellPowerGroup.VoltageProbeTable(connection)
vpt.update()

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
        vpt.munin_config_volts()
else:
    # Tell munin the current values
    vpt.munin_report_volts()

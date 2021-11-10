#!/usr/bin/env python

# Log system parameters accesible via Dell OMSA
# Russell Kackley - 5 May 2011

import os
import getopt, sys
import time
import DellOMSA
import DellOMSASystem

def usage():
    print 'Usage: omsa_logger [-h|--help] [--logdir <dir>]'

# SLEEP is the number of seconds to sleep in between Dell OMSA updates
SLEEP = 30

# Set default log directory
if 'LOGHOME' in os.environ:
    logDir = os.environ['LOGHOME']
else:
    logDir = os.getcwd()

# Process command-line options
try:
    opts, args = getopt.getopt(sys.argv[1:], 'h', ['logdir=', 'help'])
except getopt.GetoptError as e:
    print e
    usage()
    exit(1)

for o, a in opts:
    if o == '--logdir':
        logDir = a
    elif o in ('-h', '--help'):
        usage()
        exit(0)
    else:
        print 'Unexpected option:',o

print 'Logs will be written to the directory', logDir

# Connect to the Dell OMSA via SNMP
try:
    connection = DellOMSA.Connection('localhost', 'public', 2)
except DellOMSA.ConnectionError:
    print 'Connection error occured'
    exit(1)

print 'Dell OMSA Connection ok'
sys.stdout.flush()

# Instantiate the Dell OMSA System
ds = DellOMSASystem.DellOMSASystem(connection)

# Tell the Dell OMSA System where we want to write the logfiles
ds.setLogging(logDir)

# This loop will run forever
loop = 1
while (loop):
    # Update the Dell OMSA system
    print 'Updating Dell OMSA system...'
    try:
        ds.update()
    except DellOMSA.OidNotFoundError as e:
        print 'OID not found error occured:',e
        exit(1)

    # Log the current values
    ds.log()

    print 'Sleeping for ' + str(SLEEP) + ' seconds...'
    sys.stdout.flush()
    time.sleep(SLEEP)
#    loop = 0

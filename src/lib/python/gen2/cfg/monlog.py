#
# Configuration file for monitor logger
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Sat Oct 23 12:19:50 HST 2010
#]
#
import os
import INS

# TODO: read these from a config file
# Rotate logs at 8am and 5pm
timespecs = [ {'hr': 8}, {'hr': 17} ]
#timespecs = [ {'sec': 10}, {'sec': 40} ]

# Keep one week's worth of backups
#backupCount = 14
backupCount = 4

# Where to write our logs
logdir = os.environ['LOGHOME']

# Use synchronous writes?  Set to True to be able to "tail -f" files
# in real time
syncwrites = True

# Subdirectory to put the rollover files
# Set to '' to leave in the same directory as original
backupFolder = 'rollover'

# These are the logs we should write
logs = INS.INSdata().getNames()
logs.extend(['STARS', 'status', 'archiver', 'gen2base', 'sessions', 'frames',
             'TSC', 'taskmgr0', 'taskmgr0_debug', 'integgui2',
             ])

#END

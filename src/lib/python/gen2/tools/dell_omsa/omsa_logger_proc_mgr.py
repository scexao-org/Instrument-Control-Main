#! /usr/bin/env python
#
# omsa_logger_proc_mgr.py -- Dell OMSA Logger Process Manager
#
# Description:
# omsa_logger_proc_mgr.py provides a way to start/stop/restart/status
# the STSradio and omsa_logger.py tasks
#
# Usage:
# omsa_logger_proc_mgr.py <action> <task>
#
# where:
#    <action> can be one of:
#              start   => start the specified process
#              stop    => stop the specified process
#              restart => stop and then start the specified process
#              status  => report the running/not running status of the specified process
#    <task>  is the name of the task to act on. Can be one of the following:
#              STSradio    => perform the <action> on the STSradio task
#              omsa_logger =>  perform the <action> on the omsa_logger task
#              all         =>  perform the <action> on both tasks

import sys, os
import time
import shlex
from subprocess import *
import socket

PKILL      = '/usr/bin/pkill'
PGREP      = '/usr/bin/pgrep'

# The OLtask has attributes and methods to start/stop/restart/status
# the Dell OMSA logger tasks
class DellOMSAtask:
    def __init__(self, taskName, options):
        self.taskName = taskName
        self.options = options

    def start(self):
        print 'Starting task ' + self.taskName
        command = ' '.join([self.taskName, self.options])
        print 'Running command ' + command
        pid = Popen(shlex.split(command)).pid
        print 'Task ' + self.taskName + ' PID is', pid

    def stop(self):
        print 'Stopping task ' + self.taskName
        command = ' '.join([PKILL, '-f', self.taskName])
        print 'Running command ' + command
        try:
            return call(command, shell=True)
        except OSError, e:
            print 'ERROR: execution of ' + command + ' failed:', e

    def restart(self, pause):
        self.stop()
        print 'Wait a bit ...'
        time.sleep(pause)
        self.start()

    def status(self):
        print 'Status of task ' + self.taskName
        command = ' '.join([PGREP, '-fc', self.taskName])
        print 'Running command ' + command
        numTasks = Popen(shlex.split(command), stdout=PIPE).communicate()[0].rstrip('\r\n')
        if (numTasks == '0'):
            print 'Task ' + self.taskName + ' is NOT running'
        elif (numTasks == '1'):
            print 'Task ' + self.taskName + ' is running'
        else:
            print 'Task ' + self.taskName + ' has ' + numTasks + ' copies running?'

# Get the command-line arguments
this = sys.argv[0]

# First supplied argument is the action (start, stop, status, or restart)
try:
    action = sys.argv[1]
except:
    print 'ERROR: action not specified'
    exit(1)

# Second supplied argument is the task (STSradio, omsa_logger.py, or all)
try:
    task = sys.argv[2]
except:
    print 'ERROR: task not specified'
    exit(1)

# Create a taskList from the specified task
if task == 'all':
    taskList = ['STSradio', 'omsa_logger']
else:
    taskList = [task]

# Determine the path to this script file. The omsa_logger.py and
# STSradio configuration files will be in the same directory.
OMSA_LOGGER_DIR =  os.path.dirname(os.path.abspath(this))

# The STSradio binary should be in our PATH. It will be if we have
# logged in as gen2.  STSradio configuration file name will be
# ${HOST}_DellOMSA_STS.config
STSradioConfigFilename =  os.path.join(OMSA_LOGGER_DIR, socket.gethostname() + '_DellOMSA_STS.config')

# Setup a dictionary with the task names and their properties
tasks = {
    'STSradio': {'task': 'STSradio',
                 'options': ' '.join(['-c', STSradioConfigFilename])}, 
    'omsa_logger': {'task': os.path.join(OMSA_LOGGER_DIR, 'omsa_logger.py'),
                    'options': ' '.join(['--logdir', '/gen2/logs'])},
    }

# Loop through each task in the taskList, performing the specified action.
for taskname in taskList:
    if taskname in tasks: 
        task = DellOMSAtask(tasks[taskname]['task'], tasks[taskname]['options'])
        if action == 'start':
            retcode = task.start()
        elif action == 'stop':
            retcode = task.stop()
        elif action == 'status':
            retcode = task.status()
        elif action == 'restart':
            retcode = task.restart(4) # Sleep for 4 seconds between stop/start
        else:
            print 'ERROR: action ' + action + ' not recognized'
            retcode = 1
    else:
        print 'ERROR: task ' + taskname + ' not recognized'
        retcode = 1

exit(retcode)


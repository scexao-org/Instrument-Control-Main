#!/usr/bin/env python

# ========================================================================== #
#    ___                     _                      _         __             #
#   / _ \___ _ __   ___ _ __(_) ___    ___ ___   __| | ___   / _| ___  _ __  #
#  / /_\/ _ \ '_ \ / _ \ '__| |/ __|  / __/ _ \ / _` |/ _ \ | |_ / _ \| '__| #
# / /_\\  __/ | | |  __/ |  | | (__  | (_| (_) | (_| |  __/ |  _| (_) | |    #
# \____/\___|_| |_|\___|_|  |_|\___|  \___\___/ \__,_|\___| |_|  \___/|_|    #
#                                                                            #
#   __ _ _                                     _                             #
#  / _| (_)_ __    _ __ ___   ___  _   _ _ __ | |_ ___                       #
# | |_| | | '_ \  | '_ ` _ \ / _ \| | | | '_ \| __/ __|                      #
# |  _| | | |_) | | | | | | | (_) | |_| | | | | |_\__ \                      #
# |_| |_|_| .__/  |_| |_| |_|\___/ \__,_|_| |_|\__|___/                      #
#         |_|                                                                #
#                                                                            #
# ========================================================================== #

import sys
import os
import numpy as np
import subprocess

home = os.getenv('HOME')
sys.path.append(home + '/src/lib/python/')
import dio
import logit  #Custom logging library

from scxkw.config import REDIS_DB_HOST, REDIS_DB_PORT
from scxkw.redisutil.typed_db import Redis

rdb = Redis(host=REDIS_DB_HOST, port=REDIS_DB_PORT)
LEGACY_EXEC = '/home/scexao/bin/scexaostatus'

# =====================================================================
# =====================================================================


class flipmount:
    def __init__(self,
                 flipname,
                 flipid,
                 args=[],
                 description="no description",
                 defpos=["IN","OUT"]):

        self.flipname = flipname
        self.description = description
        self.defpos = defpos

        if args != [] and "--help1" in args[0]:
            self.quickhelp()
            sys.exit()

        self.flipid = flipid
        filename = "/home/scexao/bin/devices/conf/path_dio.txt"
        filep = open(filename, 'r')
        self.diodev = "/dev/serial/"
        self.diodev += filep.read().rstrip('\n')

        na = args.__len__()

        if args == []:
            self.flipit()
            self.savestate()

        elif "reset" in args[0]:
            self.savestate()

        elif "set" in args[0]:
            self.setout()

        elif "status" in args[0]:
            self.status()

        else:
            self.usage()


# =====================================================================

    def usage(self):
        print("""---------------------------------------
Usage: %s <command>
---------------------------------------
COMMAND:
    status  displays status
     reset  reset status
       set  set status to out
---------------------------------------""") % (self.flipname, )

    # -----------------------------------------------------------------
    def quickhelp(self):
        print("%20s       %s" % (self.flipname, self.description))

    # -----------------------------------------------------------------
    def flipit(self):
        a = dio.dio(self.diodev)
        a.flip(self.flipid)
        logit.logit(self.flipname, 'flipped')
        a.close()

    # -----------------------------------------------------------------
    def savestate(self):
        key = rdb.hget('map:shm_lookup', self.flipname)
        # Now Getting the keys
        value = rdb.hget(key, 'value').strip()
        if value == self.defpos[0]:
            value = self.defpos[1]
            color = '1'
        elif value == self.defpos[1]:
            value = self.defpos[0]
            color = '0'
        else:
            value = 'UNKNOWN'
            color = '3'

        command = LEGACY_EXEC + ' set ' + self.flipname + ' "' + value + '" ' + color
        os.system(command)

    # -----------------------------------------------------------------
    def setout(self):
        value = self.defpos[1]
        color = '1'
        command = LEGACY_EXEC + ' set ' + self.flipname + ' "' + value + '" ' + color
        os.system(command)

    # -----------------------------------------------------------------
    def status(self):
        key = rdb.hget('map:shm_lookup', self.flipname)
        # Now Getting the keys
        value = rdb.hget(key, 'value').strip()
        if value == self.defpos[0]:
            print("Flip mount is %s" %value)
        elif value == self.defpos[1]:
            print("Flip mount is %s" %value)
        else:
            print("Flip mount in unknown state")

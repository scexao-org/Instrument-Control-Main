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
sys.path.append(home+'/src/lib/python/')
import dio
import logit #Custom logging library
from   xaosim.scexao_shmlib   import shm


# =====================================================================
# =====================================================================
mydata = np.zeros((1,1)).astype(np.float32) # required for shared memory added by PP (copying Frantz)

class flipmount:

    def __init__(self, flipname, flipid, args=[], description="no description"):
        
        self.flipname = flipname
        self.description = description

        if args != [] and "--help1" in args[0]:
            self.quickhelp()
            sys.exit()
            
        self.flipid = flipid
        filename = "/home/scexao/bin/devices/conf/path_dio.txt"
        filep = open(filename, 'r')
        self.diodev  = "/dev/serial/by-path/"
        self.diodev += filep.read().rstrip('\n')

        na = args.__len__()

        if args == []:
            self.flipit()
            self.savestate()
            
        elif "reset" in args[0]:
            self.savestate()

        elif "status" in args[0]:
            self.status()
            
        else:
            self.usage()
        
# =====================================================================

    def usage(self):
        print """---------------------------------------
Usage: %s <command>
---------------------------------------
COMMAND:
    status  displays status
     reset  reset status
---------------------------------------""" % (self.flipname,)
    
    # -----------------------------------------------------------------
    def quickhelp(self):
        print "%20s       %s" % (self.flipname,self.description)
    
    # -----------------------------------------------------------------
    def flipit(self):
        a = dio.dio(self.diodev)
        a.flip(self.flipid)
        logit.logit(self.flipname,'flipped')
        a.close()

    # -----------------------------------------------------------------
    def savestate(self):
        if not os.path.isfile("/tmp/%s.im.shm" % (self.flipname,)):
            os.system("creashmim %s 1 1" % (self.flipname,))
            print "Position unsure"
            subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.flipname, 'UNKNOWN', '3'])
        intspshm = shm("/tmp/%s.im.shm" % (self.flipname,), verbose=False)
        intsp = int(intspshm.get_data())
        if intsp:
            mydata[0,0] = float(0)
            intspshm.set_data(mydata)
            subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.flipname, 'OUT', '1'])
        else:
            mydata[0,0] = float(np.ones(1))
            intspshm.set_data(mydata)
            subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.flipname, 'IN', '0'])
        intspshm.close()

    # -----------------------------------------------------------------
    def status(self):
        if not os.path.isfile("/tmp/%s.im.shm" % (self.flipname,)):
            print "Position unsure"
            subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.flipname, 'UNKNOWN', '3'])

        exec "intspshm = shm('/tmp/%s.im.shm', verbose=False)" % (self.flipname,)
        intsp = int(intspshm.get_data())
        if intsp:
            print "Flip mount is in"
            subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.flipname, 'IN', '0'])
        else:
            print "Flip mount is out"
            subprocess.call(['/home/scexao/bin/scexaostatus', 'set', self.flipname, 'OUT', '1'])
        intspshm.close()

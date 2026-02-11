#!/usr/bin/env python

# ========================================================= #
#    ___                     _                      _       #
#   / _ \___ _ __   ___ _ __(_) ___    ___ ___   __| | ___  #
#  / /_\/ _ \ '_ \ / _ \ '__| |/ __|  / __/ _ \ / _` |/ _ \ #
# / /_\\  __/ | | |  __/ |  | | (__  | (_| (_) | (_| |  __/ #
# \____/\___|_| |_|\___|_|  |_|\___|  \___\___/ \__,_|\___| #
#                                                           #
#   __                  __  ___  __                         #
#  / _| ___  _ __    /\ \ \/ _ \/ _\                        #
# | |_ / _ \| '__|  /  \/ / /_)/\ \                         #
# |  _| (_) | |    / /\  / ___/ _\ \                        #
# |_|  \___/|_|    \_\ \/\/     \__/                        #
#                                                           #
# ========================================================= #

import socket
import random
import time
import sys
import string
import os
import subprocess

SCEXAO_NPS_IP = {1: "133.40.162.194", 2: "133.40.162.195", 3: "133.40.162.198", 4: "133.40.163.186"}

# =====================================================================
# =====================================================================

'''
NPS factury function that calls the constructor of the appropriate class
'''
def NPS(npsname, npsid, portid, args=[], description="no description"):
    klass = {1: OldNPS, 2: NewNPS, 3: OldNPS, 4: NewNPS}[npsid]

    return klass(npsname, npsid, portid, args=args, description=description)


class AbstractNPS:
    def __init__(self,
                 npsname,
                 npsid,
                 portid,
                 args=[],
                 description="no description"):

        self.npsname = npsname
        self.description = description

        if args != [] and "--help1" in args[0]:
            self.quickhelp()
            sys.exit()

        self.npsid = npsid
        self.portid = portid

        if len(args) == 0:
            self.usage()

        cmd = args[0].lower()
        if cmd == "on":
            self.npson()
        elif cmd == "off":
            self.npsoff()
        elif cmd == "status":
            self.status()
        else:
            self.usage()


# =====================================================================

    def usage(self):
        print("""---------------------------------------
Usage: %s <command>
---------------------------------------
COMMAND:
    on      turns on
    off     turns off
    status  displays status
        ---------------------------------------""" % (self.npsname, ))

    # -----------------------------------------------------------------
    def quickhelp(self):
        print("%20s       %s" % (self.npsname, self.description))

    def npson(self):
        raise NotImplementedError()

    def npsoff(self):
        raise NotImplementedError()

    def status(self):
        raise NotImplementedError()


class OldNPS(AbstractNPS):
    def _establish_conn(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SCEXAO_NPS_IP[self.npsid], 23))
        sock.send("@@@@\r\n".encode())
        time.sleep(0.1)
        temp = sock.recv(1024)
        time.sleep(0.1)

        return sock

    # -----------------------------------------------------------------
    def npson(self):
        try:
            sock = self._establish_conn()
            cmd = str.encode("N0%i\r\n" % (self.portid, ))
            sock.send(cmd)
            time.sleep(1)
            temp = sock.recv(1024)
            subprocess.call([
                "/home/scexao/bin/scexaostatus", "set",
                "nps%d_%d" % (self.npsid, self.portid), 'ON', '1'
            ])
            time.sleep(0.1)
            sock.close()
            time.sleep(0.1)
            print(self.npsname + " is ON")
        except Exception as e:
            print("""-------------------------------------------------------
nps_on could not connect to NPS.
check that environment variable NPS_IP is correctly set
-------------------------------------------------------""")
            print("Actual exception:")
            print(e)
            print("-------------------------------------------------------")

    # -----------------------------------------------------------------
    def npsoff(self):
        try:
            sock = self._establish_conn()

            cmd = str.encode("F0%i\r\n" % (self.portid, ))
            sock.send(cmd)
            time.sleep(1)
            temp = sock.recv(1024)
            subprocess.call([
                "/home/scexao/bin/scexaostatus", "set",
                "nps%d_%d" % (self.npsid, self.portid), 'OFF', '0'
            ])
            time.sleep(0.1)
            sock.close()
            time.sleep(0.1)
            print(self.npsname + " is OFF")
        except Exception as e:
            print("""-------------------------------------------------------
nps_on could not connect to NPS.
check that environment variable NPS_IP is correctly set
-------------------------------------------------------""")
            print("Actual exception:")
            print(e)
            print("-------------------------------------------------------")

    # -----------------------------------------------------------------
    def status(self):
        try:
            sock = self._establish_conn()

            cmd = "DN0\r\n".encode()
            sock.send(cmd)
            time.sleep(1)
            npsstatus = sock.recv(1024).decode()
            npsstatus2 = npsstatus[npsstatus.find("OUTLET %i" %
                                                  (self.portid, )) + 9:]
            npsstatus3 = npsstatus2[:npsstatus2.find("(") - 1]
            if npsstatus3 == 'ON':
                col = '1'
            elif npsstatus3 == 'OFF':
                col = '0'
            else:
                col = '3'
            subprocess.call([
                "/home/scexao/bin/scexaostatus", "set",
                "nps%d_%d" % (self.npsid, self.portid), npsstatus3, col
            ])
            time.sleep(0.1)
            sock.close()
            time.sleep(0.1)
            print(self.npsname + " is " + npsstatus3)

        except Exception as e:
            print("""-------------------------------------------------------
nps_status could not connect to NPS.
check that environment variable NPS_IP is correctly set
-------------------------------------------------------""")
            print("Actual exception:")
            print(e)
            print("-------------------------------------------------------")


class NewNPS(AbstractNPS):
    '''
        We gotta use snmp (v1, to avoid auth) protocol.

        sudo apt-get install snmp

        Explanation:
        https://www.youtube.com/watch?v=Lq7j-QipNrI

        Actually - you only need MIB files to see attributes by name.
        Otherwise, you can talk by number-dotted-strings, except you have no idea what you're doing.

        How to decode MIBs:
        https://net-snmp.sourceforge.io/wiki/index.php/TUT:Using_and_loading_MIBS

        Tripp-lite SNMP MIB files:
        https://assets.tripplite.com/firmware/tripplite-mib.zip

        JFC:
        apt-get install snmp-mibs-downloader # Pulls a gazillion mib libraries

        One file has a glitch: replace /usr/share/snmp/mibs/ietf/SNMPv2-PDU with:
        https://pastebin.com/raw/p3QyuXzZ

        Test - are attributes all named ??? (Note if this is a new NPS,
        you'll need to configure the username scexaoV2c with
        appropriate protocol version and perms)
        snmpwalk -mALL -v1 -cscexaoV2c 133.40.162.195 1. 2>&1 | less
    '''
    '''
    FOR STATUS
        TRIPPLITE-PRODUCTS::tlpPduOutletState.1.<n>
    '''
    STATUS_STRING = "iso.3.6.1.4.1.850.1.1.3.2.3.3.1.1.4.1.%u"
    '''
    FOR CONTROL
        TRIPPLITE-PRODUCTS::tlpPduOutletCommand.1.<n>
        Reads 0 if ready, set to 1 for OFF and 2 for ON
    '''
    CONTROL_STRING = ".1.3.6.1.4.1.850.1.1.3.2.3.3.1.1.6.1.%u"

    def npson(self):

        subprocess.call([
            'snmpset', '-v2c', '-cscexaoV2c', SCEXAO_NPS_IP[self.npsid],
            self.CONTROL_STRING % self.portid, 'i', '2'
        ])
        subprocess.call([
            "/home/scexao/bin/scexaostatus", "set",
            "nps%d_%d" % (self.npsid, self.portid), 'ON', '1'
        ])

    def npsoff(self):

        subprocess.call([
            'snmpset', '-v2c', '-cscexaoV2c', SCEXAO_NPS_IP[self.npsid],
            self.CONTROL_STRING % self.portid, 'i', '1'
        ])
        subprocess.call([
            "/home/scexao/bin/scexaostatus", "set",
            "nps%d_%d" % (self.npsid, self.portid), 'OFF', '0'
        ])

    def status(self):

        out = subprocess.check_output([
            'snmpget', '-v2c', '-cscexaoV2c', SCEXAO_NPS_IP[self.npsid],
            self.STATUS_STRING % self.portid
        ])
        status_bool = int(out.decode().rstrip().split(' ')[-1]) == 2

        col = ('0', '1')[status_bool]
        status_str = ('OFF', 'ON')[status_bool]
        subprocess.call([
            "/home/scexao/bin/scexaostatus", "set",
            "nps%d_%d" % (self.npsid, self.portid), status_str, col
        ])

        print(self.npsname + " is " + status_str)

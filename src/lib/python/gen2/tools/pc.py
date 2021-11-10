#!/usr/bin/env python
#
# pc.py - stub version of pc.py. Instead of generating the actual
# proposal password, just return the string "password".
#

import sys

def pc(prop_num):
    passwd = 'password'
    return passwd

if __name__ == '__main__':

    for acct in sys.argv[1:]:
        print pc(acct)

#! /usr/bin/env python
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Aug 13 14:49:29 HST 2008
#]
#
# Program to determine the DAQtk environment variables for legacy
# instruments for Gen2.
#
# Usage:
#  ./g2env.py <INSTRUMENT_NAME> <GEN2_HOSTNAME> [COMMAND] [PARAMS] [...]
#
# where INSTRUMENT_NAME is the full instrument name of the instrument
# and GEN2_HOSTNAME is the name of a Gen2 host.  If these are followed
# by additional parameters then they will be interpreted as a command
# and parameters to invoke after setting the environment variables
# appropriately.
#
# Examples:
#  ./g2env.py SPCAM ssdd1
#
#  ./g2env.py COMICS ssdd1 startobe
#
# Important:
#  This only requires a fairly standard Python installation to run.
#

import sys, os
import xmlrpclib

class Error(Exception):
    """Raised if there is an error trying to get the information."""
    pass

def get_hosts(insname, nshost):
    try:
        # Query the name server on the Gen2 host for the service
        # names of the instrument and the status subsystems
        proxy = xmlrpclib.ServerProxy('http://%s:7075/' % nshost)

        insint_hosts = proxy.getHosts(insname)
        if len(insint_hosts) == 0:
            raise Error("No instrument interface found")

        status_hosts = proxy.getHosts('status')
        if len(insint_hosts) == 0:
            raise Error("No status interface found")

        # Strip off FQDN to short name
        cmds = insint_hosts[0][0].split('.')[0]
        sdst = status_hosts[0][0].split('.')[0]

        d = { 'CMDOBS': cmds, 'THROUGHOBS': cmds, 'GETOBS': cmds,
              'STATOBS': sdst, 'DATOBC': cmds }
        return d
    
    except Exception, e:
        raise Error("Couldn't get information: %s" % str(e))


def main():
    if len(sys.argv) < 3:
        print "Usage: %s <INSTRUMENT_NAME> <GEN2_HOSTNAME> [COMMAND] [PARAMS] ..." % sys.argv[0]
        sys.exit(1)
        
    insname = sys.argv[1]
    g2host = sys.argv[2]

    try:
        res = get_hosts(sys.argv[1], sys.argv[2])

    except Error, e:
        print str(e)
        print "Please check:"
        print "1) Instrument name (%s) is correct?" % insname
        print "2) Gen2 hostname (%s) correct and Gen2 software running?" % (
            g2host)
        print "3) Network is OK?"
        sys.exit(1)

    print """
# for sh/bash
export CMDOBS=%(CMDOBS)s
export THROUGHOBS=%(THROUGHOBS)s
export GETOBS=%(GETOBS)s
export STATOBS=%(STATOBS)s
export DATOBC=%(DATOBC)s
""" % res

    print """
# for csh/tcsh
setenv CMDOBS %(CMDOBS)s
setenv THROUGHOBS %(THROUGHOBS)s
setenv GETOBS %(GETOBS)s
setenv STATOBS %(STATOBS)s
setenv DATOBC %(DATOBC)s
""" % res

    if len(sys.argv) > 3:
        for key, val in res.items():
            os.environ[key] = val

        os.execvpe(sys.argv[3], sys.argv[3:], os.environ)


if __name__ == '__main__':
    main()


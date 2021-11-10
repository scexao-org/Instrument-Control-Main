#!/usr/local/bin/python
#
# SOSSstatusServer.py
""" Sample Status server, used for FMOS
This is an [x]inetd server
"""

# xinetd config file:

# service sossstatus
# {
#         type            = UNLISTED
#         port            = 65010   # Used by FMOS
#         flags           = IPv4
#         socket_type     = stream
#         protocol        = tcp
#         wait            = no
#         server          = {path}/SOSSstatusServer.py
#         user            = {non-root user}
# }

import sys # for stdin
import os
import syslog

scriptdir = os.path.dirname(os.path.realpath( __file__ ))
sys.path.insert(1, scriptdir.replace('SOSS/status', ''))
from SOSS.status import cachedStatusObj, statusError

def main():
    sc = cachedStatusObj('obs.sum.subaru.nao.ac.jp')
    syslog.openlog("SOSSstatusServer", syslog.LOG_PID,
        syslog.LOG_WARNING | syslog.LOG_DAEMON)
    while True:
        line = sys.stdin.readline()
        if line == "":
            break
        aliasname = line.strip(' \r\n')
        val = sc.get_statusValue(aliasname)
        sys.stderr.write(str(val) + "\n")
    syslog.closelog()
    
if __name__ == '__main__':
    main()

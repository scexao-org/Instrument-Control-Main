#!/usr/bin/env python
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Tue Jul 27 14:46:16 HST 2010
#]

import sys
import hashlib
import socket

"""
Program to make X authentication cookies.

Example usage:
  $ authgen.py
  $ authgen.py -n 1 -H '' -C <cookie> 
"""
# compatible with stdin to xauth
cmd_tmpl = """add %(host)s:%(number)d . %(cookie)s"""

# Reports are that this should work as well for generating a cookie:
#   - dd if=/dev/urandom count=1|md5sum
#   - mcookie
def mk_cookie():
    """Make an MIT-MAGIC-COOKIE-1 compatible cookie."""
    in_f = open('/dev/urandom', 'r')
    data = in_f.read(8192 * 4)
    in_f.close()
    
    md5hash = hashlib.md5(data).hexdigest()
    return md5hash

def mk_entry(dispnum, host, cookie=None):
    if not cookie:
        cookie = mk_cookie()
        
    d = {'number': dispnum,
         'host': host,
         'cookie': cookie,
        }
    return cmd_tmpl % d

def mk_entries_for_host(dispnum, host, fqdn, cookie=None):
    res = []
    res.append(mk_entry(dispnum, '', cookie=cookie))
    res.append(mk_entry(dispnum, host, cookie=cookie))
    res.append(mk_entry(dispnum, fqdn, cookie=cookie))
    return res


def main(options, args):
    print mk_entry(options.number, options.host,
                   cookie=options.cookie)
    
    
if __name__ == '__main__':

    myhost = socket.getfqdn().split('.')[0]
    
    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%prog'))
    
    optprs.add_option("-C", "--cookie", dest="cookie", metavar="COOKIE",
                      help="Pass in a cookie to be used for authentication")
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-H", "--host", dest="host", metavar="HOST",
                      default=myhost,
                      help="Generate entry for host HOST")
    optprs.add_option("-n", "--number", dest="number", metavar="NUMBER",
                      type="int", default=0,
                      help="Choose display number")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")

    (options, args) = optprs.parse_args(sys.argv[1:])

    if len(args) > 0:
        optprs.error("incorrect number of arguments")
       
    # Are we debugging this?
    if options.debug:
        import pdb

        pdb.run('main(options, args)')

    # Are we profiling this?
    elif options.profile:
        import profile

        print "%s profile:" % sys.argv[0]
        profile.run('main(options, args)')

    else:
        main(options, args)

# END

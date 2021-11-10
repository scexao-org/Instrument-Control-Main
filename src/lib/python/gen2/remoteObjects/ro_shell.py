#!/usr/bin/env python
#
# ro_shell.py -- generic remote object client
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Tue Jul 22 09:20:51 HST 2008
#]
#
#
"""This generic remoteObjects client gives a command line interface
that allows you to create proxies to any number of remoteObject servers
and execute commands on them.

Example use:
$ ro_shell.py
names>getNames()
"""

import sys, os
import socket, time
# for command line interface:
import atexit, readline
import traceback
import remoteObjects as ro

    
version = '20080130.0'

# History file for ro_sh
hist_file = os.path.join(os.environ['HOME'], '.roshrc')

# Prompt template.
prompt_templ = '%s> '


class Shell(object):
    """Remote Object Shell class.  Encapsulates methods for interacting
    with a set of remote object proxy objects.
    """

    def __init__(self, connects=[]):
        """Constructor for a remote shell object."""
        self.options = options
        self.cursor = 'names'
        self.svc = {}
        self.svc[self.cursor] = ro.getns()

        for svcname in connects:
            self.rosh_conn(svcname)


    def builtin(self, cmdstr):
        """Execute a built in command."""
        try:
            print eval('self.rosh_' + cmdstr)

        except Exception, e:
            print str(e)
            (type, value, tb) = sys.exc_info()
            tb_str = ("Traceback:\n%s" % \
                      "".join(traceback.format_tb(tb)))
            print tb_str

        
    def rosh_conn(self, svcname, auth=None):
        """Connect to remote object service (svcname)"""

        self.svc[svcname] = ro.remoteObjectProxy(svcname,
                                                 auth=auth)
        try:
            self.svc[svcname].ro_echo(1)
            self.cursor = svcname
            return svcname

        except ro.remoteObjectError, e:
            print str(e)
            return None
        
        
    def rosh_sw(self, svcname):
        """Switch cursor to remote object service (svcname)"""

        try:
            foo = self.svc[svcname]
            self.cursor = svcname
            return svcname

        except KeyError:
            print "No such connection: %s; please use @conn()" % svcname
            return None
        
        
    def rosh_help(self):
        """Built in help command"""
        print """Built-in Commands:
        
@conn(svcname) -- get a RO connection to service with name svcname
@sw(svcname)   -- switch to an existing connection to svcname
@help()        -- generate this help message

Any other method is considered to be a method call on the remote service.
"""
        
        
    def execute(self, cmdstr):
        """Execute a method on a remote object."""
        try:
            print eval("self.svc['%s'].%s" % (self.cursor, cmdstr))

        except Exception, e:
            print str(e)
            (type, value, tb) = sys.exc_info()
            tb_str = ("Traceback:\n%s" % \
                      "".join(traceback.format_tb(tb)))
            print tb_str
            print "\nUse @help() for help with ro_shell.py"

        
    def shell(self):
        """Execute a read-eval-print loop."""

        try:
            # load the history file
            readline.read_history_file(hist_file)

        except IOError:
            pass

        # Write out history file when the program terminates
        atexit.register(readline.write_history_file, hist_file)

        # Command processing loop.  Iterate until a ^C or ^D
        while True:

            # Prompt user using current svc name 
            prompt = (prompt_templ % self.cursor)
            cmdstr = raw_input(prompt)
            if len(cmdstr) == 0:
                continue

            cmdstr = cmdstr.strip()
            if not cmdstr.startswith('@'):
                self.execute(cmdstr)

            else:
                cmdstr = cmdstr[1:]
                self.builtin(cmdstr)



def main(options, args):

    # Not used yet.
    if options.rohosts:
        rohosts = options.rohosts.split(',')
    else:
        rohosts = None

    ro.init(ro_hosts=rohosts)

    if options.connect:
        svcs = options.connect.split(',')
    else:
        svcs = []

    # Get a remote object shell instance
    ro_sh = Shell(connects=svcs)

    # If there are command line arguments (after stripping options)
    # then treat them as a command and try to execute it.  Otherwise
    # enter an interactive command line shell.
    if len(args) > 0:
        cmdstr = ('%s(%s)' % (args[0], ', '.join(args[1:])))
        ro_sh.execute(cmdstr)

    else:
        quit = False
        while not quit:
            try:
                ro_sh.shell()

            except (EOFError, KeyboardInterrupt):
                print ""
                if not options.confirm:
                    quit = True
                else:
                    try:
                        ans = raw_input("Really quit? ")
                        ans = ans.upper()
                        if (ans == 'Y') or (ans == 'YES'):
                            quit = True
                    except (EOFError, KeyboardInterrupt):
                        print ""
                        quit = True
                    
        
    sys.exit(0)

    
if __name__ == '__main__':

    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options] command [args]"
    parser = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    parser.add_option('-y', "--confirm", dest="confirm", default=False,
                      action="store_true",
                      help="Confirm certain actions")
    parser.add_option('-c', "--connect", dest="connect", metavar="NAMES",
                      help="Connect to service NAMES")
    parser.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    parser.add_option("--rohosts", dest="rohosts",
                      help="Override hosts configuration (careful)",
                      metavar="HOSTS")
    parser.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")

    (options, args) = parser.parse_args(sys.argv[1:])


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

#END

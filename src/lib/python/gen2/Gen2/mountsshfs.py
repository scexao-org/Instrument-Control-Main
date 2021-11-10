#! /usr/bin/env python
#
# mountsshfs.py -- used for remote mounting directories via sshfs
#
# Eric Jeschke (eric@naoj.org)
#
# WARNING: ALL YE WHO ENTER HERE
#  This is extremely ugly code, not the least reason being that using
#  pexpect to do ssh logins is very hacky
# YOU HAVE BEEN WARNED
#

import sys, os
import re
import pexpect

import tools.pc
import ssdlog

class MountError(Exception):
    pass
class PasswordError(MountError):
    pass

# For loading of private OPE files
# TODO: this information should go into a config file or something
mountarea = os.path.join(os.environ['HOME'], 'Procedure', 'ANA')
mounthost = 'da2.sum.subaru.nao.ac.jp'


def getuserpass(propid):
    try:
        passfile = os.path.join(os.environ['GEN2COMMON'], 'db', 'proposals')
        in_f = open(passfile, 'r')
    except IOError, e:
        raise PasswordError(e)

    lines = in_f.read().split('\n')
    in_f.close()

    for line in lines:
        line = line.strip()
        if len(line) == 0:
            continue
        parts = line.split()
        if len(parts) != 9:
            continue
        if propid != parts[0].strip():
            continue
        
        username = parts[0]
        password = parts[8]
        return (username, password)

    raise PasswordError("No user account found for '%s'" % propid)


def getpass(username):
    try:
        if re.match('^o\d{5}$', username):
            return tools.pc.pc(username)
        raise PasswordError("Passwords only available for 'o' proposal accounts")
    except Exception, e:
        raise PasswordError(e)

        
def mount_remote(logger, host, username, password, 
                 localdir, remotedir, timeout=20):

    # Prevent graphical popups
    try:
        os.environ['SSH_ASKPASS']=''
    except KeyError:
        pass

    cmdstr = "sshfs %s@%s: %s -o nonempty -o NumberOfPasswordPrompts=1 -o follow_symlinks -o idmap=user" % (
        username, host, localdir)
    print cmdstr

    logger.debug("Command is '%s'" % cmdstr)
    try:
        child = pexpect.spawn(cmdstr)

        # Look for "Password:" or "continue connecting"
        i = child.expect(["[Pp]assword:", pexpect.EOF,
                          "continue connecting (yes/no)?"],
                         timeout=timeout)

        if i == 1:
            logger.debug("EOF immediately after command")
            return
        
        if i == 2:  # "continue connecting"
            logger.debug("confirm connect")
            child.sendline('yes')
            i = child.expect("[Pp]assword:", pexpect.EOF,
                             timeout=timeout)
            if i == 1:
                logger.debug("EOF immediately after confirm connect")
                return
        
        if i == 0:  # "Password:"
            logger.debug("password input")
            child.sendline(password)
            i = child.expect([pexpect.EOF], timeout=timeout)
            if i == 0:
                logger.debug("EOF immediately after password input")
                return

        lines = child.before
        errstr = ("sshfs: sshfs failure for %s@%s: %s" % (
            username, host, lines))
        logger.error(errstr)
        raise MountError(errstr)

    except KeyboardInterrupt, e:
        raise MountError(e)

    except pexpect.TIMEOUT:
        errstr = "ssh timeout for %s@%s" % (username, host)
        logger.error(errstr)
        raise MountError(errstr)

    #except pexpect.EOF, e:
    except Exception, e:
        errstr = "ssh EOF during pexpect to host %s: %s" % (
            host, str(e))
        logger.error(errstr)
        raise MountError(errstr)

def unmount_remote(logger, localdir):

    cmdstr = "fusermount -u -z %s" % (localdir)
    try:
        res = os.system(cmdstr)
        if res != 0:
            raise MountError("Error result from unmounting %s: res=%d" % (
                    localdir, res))
    except OSError, e:
        raise MountError("Exception raised unmounting %s: %s" % (
                localdir, str(e)))


def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('mountsshfs', options)

    if not options.action:
        print "Please specify an action with -a or --action !"
        sys.exit(1)

    # Find mount point
    if not options.mountpoint:
        if not options.propid:
            print "Please specify a --propid or --mountpoint !"
            sys.exit(1)
        else:
            mountpt = os.path.join(mountarea, options.propid)
    else:
        mountpt = options.mountpoint

    mountpt = os.path.abspath(mountpt)

    if options.action == 'unmount':
        # Try to unmount the directory
        logger.info("Attempting to lazily unmount %s" % mountpt)
        unmount_remote(logger, mountpt)
        return

    if options.action == 'mount':
        # Get info necessary to establish new mountpoint
        if not options.username:
            if not options.propid:
                print "Please specify a --propid or --username !"
                sys.exit(1)
            else:
                username = options.propid
        else:
            username = options.username
                
        if not options.password:
            if not options.propid:
                print "Please specify a --propid or --password !"
                sys.exit(1)
            else:
                # If no password specified then try to get one from OPAL
                password = getpass(username)
        else:
            password = options.password
                
        if not options.host:
            host = mounthost
        else:
            host = options.host

        if not os.path.isdir(mountpt):
            if not options.autocreate:
                print "Mount point does not exist: %s" % mountpt
                sys.exit(1)

            logger.info("Attempting to mount %s" % mountpt)
            try:
                os.mkdir(mountpt)
            except OSError, e:
                logger.error("Error creating mount point '%s': %s" % (
                        mountpt, str(e)))
                sys.exit(1)
        
        logger.info("Attempting to mount %s" % mountpt)
        mount_remote(logger, host, username, password, mountpt,
                     options.remotedir, timeout=options.timeout)
        return

    print "I don't understand action '%s'" % options.action
    sys.exit(1)
    
        
# Create demo in root window for testing.
if __name__ == '__main__':
  
    from optparse import OptionParser

    usage = "usage: %prog [options] [propid]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-a", "--action", dest="action",
                      help="Specify an action (mount|unmount)")
    optprs.add_option("--create", dest="autocreate", default=False,
                      action="store_true",
                      help="Auto-create mount points")
    optprs.add_option("-m", "--mountpoint", dest="mountpoint",
                      metavar="PATH",
                      help="Local mount point is PATH")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("-d", "--remotedir", dest="remotedir", metavar="PATH",
                      default='',
                      help="Specify PATH on remote host to mount")
    optprs.add_option("--host", dest="host", metavar="HOST",
                      help="Specify remote HOST for ssh")
    optprs.add_option("-u", "--username", dest="username", metavar="NAME",
                      help="Specify user NAME for ssh login")
    optprs.add_option("-P", "--password", dest="password", metavar="PASS",
                      help="Specify password PASS for ssh login")
    optprs.add_option("-p", "--propid", dest="propid", metavar="PROPID",
                      help="Specify propid for mounting")
    optprs.add_option("-t", "--timeout", dest="timeout", metavar="SECS",
                      type='int', default=20,
                      help="Specify timeout for ssh in SECS")
    ssdlog.addlogopts(optprs)


    (options, args) = optprs.parse_args(sys.argv[1:])

    if len(args) != 0:
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

#END

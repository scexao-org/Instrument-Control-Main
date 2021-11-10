#! /usr/bin/env python
#
# rpctool.py -- tool to diagnose/debug/fix SOSS rpc problems
#
# Mark Garboden
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Dec  5 16:59:04 HST 2007
#]
#

import sys, popen2
from optparse import OptionParser

import SOSS.SOSSrpc as SOSSrpc

# Where is rpcinfo program
rpcinfo_cmdstr = "rpcinfo -p %s"

def showtable():
    """Shows the table of all possible SOSS rpc program numbers.
    """
    print "      Key            Initial Packet ProgNo     Reply Packet ProgNo"
    keys = SOSSrpc.get_rpcsvc_keys.keys()
    keys.sort()
    values = {}

    for key in keys:
        info = SOSSrpc.lookup_rpcsvc(key)

        if info.server_receive_prgnum != None:
            recv_dec = info.server_receive_prgnum
            recv_hex = hex(info.server_receive_prgnum)
        else:
            recv_dec = None
            recv_hex = None

        if info.server_send_prgnum != None:
            send_dec = info.server_send_prgnum
            send_hex = hex(info.server_send_prgnum)
        else:
            send_dec = None
            send_hex = None

        print "%-20s %s = %s    %s = %s" % (key, recv_hex, recv_dec,
                                            send_hex, send_dec)
    

def showinfo(hosts):
    """Run rpcinfo on on list of hosts and show which program numbers are
    registered on them."""

    # If no hosts specified, then assume local host
    if len(hosts) == 0:
        hosts = [ SOSSrpc.get_myhost(short=True) ]
    
    #print "hosts = %s" % str(hosts)
    rpcinfo = {}
    for host in hosts:
        rpcinfo[host] = {}
        cmd = rpcinfo_cmdstr % host
        #print cmd
        (stdout0, stdin0, stderr0) = popen2.popen3(cmd)
        outlines0 = stdout0.readlines()
        print stderr0.read()
        for line in outlines0:
            #print "o0",line[:-1]
            try:
                info = line.split()
                (prog, vers, tcpudp, port) = (info[0], info[1],
                                              info[2], info[3])
                if tcpudp == 'tcp':
                    # TODO: collect info also for UDP entries
                    #print host, prog, vers, port
                    rpcinfo[host][prog] = (vers, port)
            except:
                pass

    keys = SOSSrpc.get_rpcsvc_keys()
    keys.sort()
    values = {}

    for key in keys:
        info = SOSSrpc.lookup_rpcsvc(key)

        if info.server_receive_prgnum != None:
            recv_dec = info.server_receive_prgnum
            recv_hex = hex(info.server_receive_prgnum)
        else:
            recv_dec = None
            recv_hex = None

        if info.server_send_prgnum != None:
            send_dec = info.server_send_prgnum
            send_hex = hex(info.server_send_prgnum)
        else:
            send_dec = None
            send_hex = None

        values[str(recv_dec)] = (key, recv_hex, 1)
        values[str(send_dec)] = (key, send_hex, 0)
    
    init_ackres = {0: 'init', 1:'ack/res'}
    for host in hosts:
        #print host
        progs = rpcinfo[host].keys()
        progs.sort()
        for prog in progs:
            #print prog
            if values.has_key(prog):
                print "%-7s provides %-7s %-18s at %s = %s" % (host,
                    init_ackres[values[prog][2]], values[prog][0], values[prog][1], prog)
            else:
                val = int(prog)
                print "Unknown program type: 0x%x = %d" % (val, val)
            #  end if found a match
        # end for all prog numbers found in rpcinfo
    # end for all hosts


def unregister(keys):
    """Unregister SOSS RPC programs associated with _keys_ with local
    portmapper."""

    try:
        dict_res = SOSSrpc.unregister(keys)

        # Result is a dictionary of symbolic SOSS rpc keys;
        # if an entry is True, it was unregistered
        for key in dict_res:
            if dict_res[key]:
                print "%s unregistered" % key

    except KeyError, e:
        print "No such SOSS RPC key: %s" % str(e)
        sys.exit(1)


def unregister_all():
    """Unregister ALL SOSS RPC programs with the local portmapper."""
    
    unregister(SOSSrpc.get_rpcsvc_keys())


def main(options, args):

    if options.showtable:
        showtable()
        sys.exit(0)

    elif options.unregister_all:
        unregister_all()
        sys.exit(0)

    elif options.rpcinfo:
        showinfo(args)
        sys.exit(0)

    elif options.unregister:
        unregister(args)
        sys.exit(0)

    else:
        print "Please specify an option. --help shows options."
        sys.exit(1)

        
usage = "%prog [options] [host] ..."

if __name__ == '__main__':

    # Parse command line options
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage, version=('%prog'))
    
    parser.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    parser.add_option("--info", dest="rpcinfo", default=False,
                      action="store_true",
                      help="Show RPC program info for hosts")
    parser.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    parser.add_option("--showtable", dest="showtable", default=False,
                      action="store_true",
                      help="Show table of all possible RPC program numbers")
    parser.add_option("--unregister", dest="unregister", default=False,
                      action="store_true",
                      help="Unregister SOSS RPC program keys")
    parser.add_option("--unregister_all", dest="unregister_all", default=False,
                      action="store_true",
                      help="Unregister all SOSS RPC program keys")

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


# END

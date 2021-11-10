#! /usr/bin/env python
#
# ifcfg.py -- program to configure Gen2 floating interfaces
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Jul 22 16:21:35 HST 2010
#]
#
"""
This program configures the network interfaces according to the the node's
own hostname/ip and the current configuration passed in via --config

Examples:
  $ ifcfg.py --config=gen2 --dry-run
  
  $ ifcfg.py --config=gen2

--dry-run will just print out the commands that should be executed without
actually executing them.
"""
import sys, os
import socket

# Module prefix for loading configurations
# (relative to a member of $PYTHONPATH)
conf_pfx = 'cfg.bm.'

def my_import(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


def getaliases(config):
    
    res = {}

    for node, hostbnch in config.managers.items():
        host = hostbnch['fqdn']
        try:
            names_or_ips = hostbnch['alt']
        except KeyError:
            res[host] = []
            continue

        aliases = []
        for alias in names_or_ips:
            d = {}
            d.update(config.interfaces[alias])
            if not d.has_key('addr'):
                d['addr'] = socket.gethostbyname(d['name'])
            aliases.append(d)
        res[host] = aliases

    return res

# example of stanzas:
# [{'mask': '255.255.255.0', 'addr': '192.168.103.141', 'dev': 'vlan103:1'}, {'mask': '255.255.255.0', 'name': 'g2stat', 'dev': 'vlan167:3', 'addr': '133.40.167.45'}, {'mask': '255.255.255.0', 'name': 'g2guide', 'dev': 'vlan167:6', 'addr': '133.40.167.44'}]
# this function would return
# ['vlan103', 'vlan167']
#
def getbasedevs(stanzas):
    def f(cfg):
        return cfg['dev'].split(':')[0]
    return set(map(f, stanzas))


def main(options, args):

    try:
        module = my_import(conf_pfx + options.config)

    except ImportError, e:
        print "Can't load configuration '%s: %s'" % (
            options.config, str(e))
        sys.exit(1)

    # TODO: provide option to load from alternate configuration file
    config = module.config
        
    # Get our FQDN for identifying ourselves
    if options.host:
        fqdn = socket.getfqdn(options.host)
    else:
        fqdn = socket.getfqdn()
        
    # Look up my configuration of aliases
    aliases = getaliases(config)

    if not aliases.has_key(fqdn):
        sys.stderr.write("Can't find my FQDN (%s) in managers list: %s\n" % (
            fqdn, str(aliases.keys())))
        sys.exit(1)

    #print aliases
    hosts = aliases.keys()
    other_hosts = filter(lambda host: host != fqdn, hosts)

    # Prepare command list to configure interfaces
    cmd_list = []

    # Bring down any interfaces used by other hosts
    for host in other_hosts:
        for cfg in aliases[host]:
            cmd_str = "sudo ifconfig %(dev)s down" % cfg
            cmd_list.append(cmd_str)

    stanzas = aliases[fqdn]
    # Bring up my "base" interfaces
    basedevs = getbasedevs(stanzas)
    for dev in basedevs:
        cmd_str = "sudo ifconfig %s up" % dev
        cmd_list.append(cmd_str)

    # Bring up my "sub" interfaces
    for cfg in stanzas:
        cmd_str = "sudo ifconfig %(dev)s %(addr)s netmask %(mask)s up" % cfg
        cmd_list.append(cmd_str)
        #cmd_str = "sudo ifconfig %(dev)s up" % cfg
        #cmd_list.append(cmd_str)

    # Execute commands.  Note that the account must have privileges
    # necessary to execute interface commands!
    for cmd_str in cmd_list:
        if options.dry_run:
            print cmd_str
        else:
            res = os.system(cmd_str)
            print "%s [%d]" % (cmd_str, res)
            

if __name__ == '__main__':
    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--config", dest="config", default=None,
                      help="Specify configuration to use")
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--dry-run", dest="dry_run", default=False,
                      action="store_true",
                      help="Just show the commands we would do, but don't do it")
    optprs.add_option("--host", dest="host", default=None,
                      help="Specify host for configuration")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")

    (options, args) = optprs.parse_args(sys.argv[1:])

    if len(args) != 0:
        optprs.error("Incorrect number of arguments")

    if not options.config:
        optprs.error("Please specify a configuration with --config")

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




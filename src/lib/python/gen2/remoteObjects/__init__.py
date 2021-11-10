#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Dec 27 15:47:53 HST 2010
#]

"""remoteObjects -- wrapper for remote object access protocol

"""

__author__ = "Eric Jeschke <eric@naoj.org>"


from remoteObjects import managerServicePort, nameServicePort, OK, ERROR, \
    timeout, remoteObjectError, NameServiceWarning, \
    remoteObjectServer, remoteObjectClient, remoteObjectProxy, remoteObjectSP, \
    remoteObjectSPAll, nullLogger, \
    servicePack, make_robunch, init, get_myhost, get_hosts, get_ro_hosts, \
    getms, getns, binary_encode, binary_decode, compress, uncompress, \
    split_host, populate_host, unique_hosts, unique_host_ports, addlogopts

__all__ = ['managerServicePort', 'nameServicePort', 'OK', 'ERROR',
           'timeout', 'remoteObjectError', 'NameServiceWarning',
           'remoteObjectServer', 'remoteObjectClient', 'remoteObjectProxy',
           'remoteObjectSP', 'remoteObjectSPAll', 'nullLogger',
           'servicePack', 'make_robunch', 'init',
           'get_myhost', 'get_hosts', 'get_ro_hosts', 'getms', 'binary_encode',
           'binary_decode', 'compress', 'uncompress',
           'split_host', 'populate_host',
           'unique_hosts', 'unique_host_ports', 'addlogopts',
           'PubSub', 'Monitor'
           ]

# END



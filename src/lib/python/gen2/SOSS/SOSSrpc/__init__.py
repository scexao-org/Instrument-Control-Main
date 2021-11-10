"""SOSS_rpc - a common interface for SOSS RPC calls.
"""

__author__ = "Eric Jeschke <eric@naoj.org>"


from common import get_rpcsvc_keys, lookup_rpcsvc, \
     unregister, unregister_all, time2timestamp, \
     timestamp2time, get_myhost, rpcError, rpcMsgError, \
     rpcSequenceNumber

from SOSSrpc import SOSScmdRpcMsgError, SOSScmdRpcHeader, SOSScmdRpcMsg

from TCSrpc import TCScmdRpcMsgError, TCSstatRpcMsgError, \
     TCSstatRpcHeader, TCSstatRpcMsg

from client_server import rpcClientError, rpcServerError, \
     callrpc, rpcClient, lazyClient, TCP_rpcClient, UDP_rpcClient, \
     rpcServer, TCP_rpcServer, UDP_rpcServer, SOSS_rpcServer, \
     clientServerPair


__all__ = ['get_rpcsvc_keys', 'lookup_rpcsvc', 'time2timestamp',
           'timestamp2time', 'get_myhost', 'callrpc', 'rpcError',
           'rpcMsgError', 'rpcClientError', 'rpcServerError',
	   'rpcHeader', 'rpcMsg', 'rpcSequenceNumber',

           'SOSScmdRpcMsgError', 'SOSScmdRpcHeader', 'SOSScmdRpcMsg',

           'TCScmdRpcMsgError', 'TCSstatRpcMsgError', 'TCSstatRpcHeader',
           'TCSstatRpcMsg',

           'rpcClient', 'TCP_rpcClient', 'UDP_rpcClient','lazyClient',
           'rpcServer', 'TCP_rpcServer', 'UDP_rpcServer', 'SOSS_rpcServer',
           'clientServerPair']

#END

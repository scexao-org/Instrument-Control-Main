#
# SOSS_status -- Retrieve status from SOSS
#
# Eric Jeschke (eric@naoj.org)  last edit: 2006.06.01
# Yasu Sakakibara (yasu@naoj.org)
#
#
import sys, os, time
import re, binascii
import socket, threading
import struct

import rpc
import common
import Convert

from OSSC_ScreenGetconstants import *
from OSSC_ScreenGettypes import *
import OSSC_ScreenGetpacker


    ################################################
    #    OSSC_ScreenGetSvc RPC INTERFACE STUFF
    ################################################


# Base class for making RPC calls to the SOSS OSSC_ScreenGet service.
#
class OSSC_SCREENGETClient(object):

    def __init__(self):
        pass

    # Add the packers and unpackers for OSSC_ScreenGet calls.  This is somehow
    # invoked from the rpc.py package.
    #
    def addpackers(self):
        self.packer = OSSC_ScreenGetpacker.OSSC_SCREENGETPacker()
        self.unpacker = OSSC_ScreenGetpacker.OSSC_SCREENGETUnpacker('')

    #
    # RPC procedures
    #

    # This implements the client call to the OSSC_ScreenGet RPC server.
    #
    def call(self, tabledef, start, size):
        args = ScreenGetArgs(tabledef, start, size)
        res = self.make_call(GET_SCREEN, args, \
                             self.packer.pack_ScreenGetArgs, \
                             self.unpacker.unpack_ScreenGetRet)

        return res


# Subclass implementing specific UDP RPC interface to OSSC_ScreenGet
#
class UDP_OSSC_SCREENGETClient(OSSC_SCREENGETClient, rpc.UDPClient):
    def __init__(self, host, uid=os.getuid(), gid=os.getgid(), \
                 #sec=(rpc.AUTH_UNIX, None)
                 sec=(rpc.AUTH_NULL, None)
                 ):
        rpc.UDPClient.__init__(self, host, OSSC_GETSCREEN, \
                               OSSC_GETSCREEN_VERSION, sec)
        OSSC_SCREENGETClient.__init__(self)
        self.uid = uid
        self.gid = gid


# Subclass implementing specific TCP RPC interface to OSSC_ScreenGet
#
class TCP_OSSC_SCREENGETClient(OSSC_SCREENGETClient, rpc.TCPClient):
#
#sec=(rpc.AUTH_UNIX, rpc.make_auth_unix_default())
#
    def __init__(self, host, uid=os.getuid(), gid=os.getgid(),
                 #sec=(rpc.AUTH_UNIX, None)
                 sec=(rpc.AUTH_NULL, None)
                 ):
        rpc.TCPClient.__init__(self, host, OSSC_GETSCREEN, \
                               OSSC_GETSCREEN_VERSION, sec)
        OSSC_SCREENGETClient.__init__(self)
        self.uid = uid
        self.gid = gid


class baseSOSSstatusObj(common.baseStatusObj):

    def __init__(self):

        # holds all kinds of data about SOSS status aliases 
        self.info = Convert.statusInfo()

        # statusConverter object, used to extract and interpret SOSS
        # values in the tables
        self.conv = Convert.statusConverter()

        super(baseSOSSstatusObj, self).__init__()


    def get_statusConverter(self):
        return self.conv

        
class rpcStatusObj(baseSOSSstatusObj):
    """ Implements a Python dictionary interface to the SOSS status system.

    This kind of object does not cache results, and ALWAYS makes a new rpc call
    for each dictionary access and for each status alias.

    Example usage:
    ...
    import SOSS.status
    ...
    status = SOSS.status.rpcStatusObj('obs')

    print status['TSCS.AZ']
    """
    
    def __init__(self, host, transport='auto',
                 suppress_fetch_errors=False,
                 suppress_conversion_errors=False):

        # set any attributes here - before initialisation
        # these remain as normal attributes
        super(rpcStatusObj, self).__init__()

        # Record RPC preferences for later lazy client creation
        self.transport = transport
        self.statushost = host
        self.rpcclient = None

        self.suppress_fetch_errors = suppress_fetch_errors
        self.suppress_conversion_errors = suppress_conversion_errors

        self.__initialised = True
        # after initialisation, setting attributes is the same as setting an item


    # Make the RPC client 
    def _mk_client(self):

        try:
            # Create the rpc client
            if self.transport == "auto":
                # Try TCP first, then UDP, according to RFC2224
                try:
                    cl = TCP_OSSC_SCREENGETClient(self.statushost)
                except socket.error:
                    # print "TCP Connection refused, trying UDP"
                    cl = UDP_OSSC_SCREENGETClient(self.statushost)
            elif transport == "tcp":
                cl = TCP_OSSC_SCREENGETClient(self.statushost)
            elif transport == "udp":
                cl = UDP_OSSC_SCREENGETClient(self.statushost)
            else:
                raise RuntimeError, "Invalid protocol"

            self.rpcclient = cl
            return

        except (rpc.PortMapError, socket.error), e:
            self.rpcclient = None
            raise common.statusError('Cannot create RPC client: %s' % (str(e)))
            
        
    # Make an rpc call to extract an entire table.
    #
    def get_statusTable(self, tablename):
        # 
        try:
            tabledef = self.info.get_tableDef(tablename)

        except KeyError, e:
            raise KeyError(str(e))

        # Lazy client creation, prevents problems if server is not up
        # before client
        if not self.rpcclient:
            self._mk_client()
            
        try:
            res = self.rpcclient.call(tabledef.line, str(0), \
                                      str(tabledef.tablesize))
        except Exception, e:
            # Possibly stale RPC client, try resetting it...
            # this may raise a statusError
            self._mk_client()

            # Now try again, one more time...
            try:
                res = self.rpcclient.call(tabledef.line, str(0), \
                                          str(tabledef.tablesize))
            except Exception, e:
                self.rpcclient = None
                raise common.statusError("Exception raised invoking client rpc: %s" % str(e))
            
        return res

        
    def get_statusTables(self, tablenames, res):
        
        for tablename in tablenames:
            res[tablename] = self.get_statusTable(tablename)
            
        
    def get_statusTablesByAliases(self, aliasnames, res):
        
        self.get_statusTables(self.info.aliasesToTables(aliasnames), res)
            
        
    # Make an rpc call to extract a single status value.
    #
    def get_statusValue(self, aliasname):
        # Replace '--' with '.'
        #aliasname = aliasname.replace('__', '.')

        try:
            aliasinfo = self.info.get_aliasDef(aliasname)

        except common.statusError, e:
            raise KeyError(str(e))

        # Lazy client creation, prevents problems if server is not up
        # before client
        if not self.rpcclient:
            self._mk_client()
            
        try:
            res = self.rpcclient.call(aliasinfo.tabledef.line, \
                                      str(aliasinfo.offset), \
                                      str(aliasinfo.length))
        except Exception, e:
            # Possibly stale RPC client, try resetting it...
            # this may raise a statusError
            self._mk_client()

            # Now try again, one more time...
            try:
                res = self.rpcclient.call(aliasinfo.tabledef.line, \
                                          str(aliasinfo.offset), \
                                          str(aliasinfo.length))
            except Exception, e:
                self.rpcclient = None
                if not self.supress_fetch_errors:
                    raise common.statusError("Exception raised invoking client rpc: %s" % str(e))
                return common.STATERROR

        # Return conversion of value to Python type
        try:
            return self.conv.convert(res, aliasinfo)

        except Convert.statusConversionError, e:
            if not self.supress_conversion_errors:
                raise e
            return common.STATERROR


    def get_statusValuesList(self, aliasnames):
            res = []
            for aliasname in aliasnames:
                res.append(self.get_statusValue(aliasname))

            return res

        
    def get_statusValuesDict(self, res):

        for aliasname in res.keys():
            res[aliasname] = self.get_statusValue(aliasname)

        
# Helper class for implementing the cachedStatusObj.  Basically defines a
# data structure for holding a cached table and its attributes.  Not used
# in an OO way.
#
class cachedTable(object):

    def __init__(self):
        # The buffer for the table fetched via rpc call
        self.table = None

        # Tabledef object associated with this table
        self.tabledef = None

        # Last time table was updated via rpc
        self.timestamp = 0

        # Cache expiration time
        self.expirationDelta = 0

        # Cache validity flag (independent of expiration time)
        self.valid = False

        # Mutex to arbitrate access between threads
        self.lock = threading.RLock()

    
class cachedStatusObj(baseSOSSstatusObj):
    """ Implements a Python dictionary interface to the SOSS status system.

    This kind of object makes rpc calls to fetch entire tables and caches them in
    memory.  You can set the expiration time for individual tables.

    THIS IS A THREAD-SAFE OBJECT (as long as you don't call superclass methods
    directly), so several threads can share a cachedStatusObj to decrease the
    amount and number of network transfers.

    Example usage:
    ...
    import SOSS.status
    ...
    status = SOSS.status.cachedStatusObj(host='obs')
    
    # Set a expiration time of 1/10 sec for TSCS table values
    status.set_tableExpiration('TSCS', 0.10)
    ...
    
    print status['TSCS.AZ']

    """
    
    def __init__(self, host=None, statusObj=None, transport='auto', delta=1.0,
                 suppress_fetch_errors=False,
                 suppress_conversion_errors=False):

        # Superclass initialization
        super(cachedStatusObj, self).__init__()

        # Dictionary holding all the cachedTable objects, indexed by table name
        self.cache = {}

        # Default cache expiration time for this table
        self.delta = delta

        # mutex used to arbitrate access to this object's state, particularly
        # self.cache
        self.lock = threading.RLock()

        # Thing we are going to use to get status.  If we are not passed a
        # delegate, then try creating a rpcStatusObj with optional host param
        if statusObj != None:
            self.statusObj = statusObj
        else:
            if not host:
                raise common.statusError('Need to specify a host= or statusObj=')

            self.statusObj = rpcStatusObj(host, transport=transport)
            
        self.suppress_fetch_errors = suppress_fetch_errors
        self.suppress_conversion_errors = suppress_conversion_errors



    # Create new table cache.  Default expiration delta is 1 sec.
    #
    def __addTableCache(self, tablename, delta=1.0):
        cacheobj = cachedTable()
        cacheobj.tabledef = self.info.get_tableDef(tablename)
        cacheobj.valid = False
        cacheobj.timestamp = time.time()
        cacheobj.expirationDelta = delta
        
        self.lock.acquire()
        self.cache[tablename] = cacheobj
        self.lock.release()


    # Look up a table cache based on the table name.
    #
    def get_tableCache(self, tablename):
        self.lock.acquire()
        try:
            try:
                cacheobj = self.cache[tablename]

            except KeyError, e:
                # cacheTable object hasn't yet been created for this table.
                # Do so now.
                self.__addTableCache(tablename, self.delta)
                cacheobj = self.cache[tablename]

        finally:
            self.lock.release()

        return cacheobj

    
    def __get_tableNames(self):
        self.lock.acquire()
        keys = self.cache.keys()
        self.lock.release()

        return keys


    ####################################
    #    PUBLIC METHODS
    ####################################


    def updateTable(self, tablename):

        cacheobj = self.get_tableCache(tablename)

        # Get entire table via rpc parent object
        # print "Getting table %s via rpc" % tablename
        cacheobj.lock.acquire()

        try:
            cacheobj.table = self.statusObj.get_statusTable(tablename)
            cacheobj.valid = True
            cacheobj.timestamp = time.time()

        finally:
            cacheobj.lock.release()

            
    def updateTables(self):

        for tablename in self.__get_tableNames():
            self.updateTable(tablename)
            
        
    def updateTableConditionally(self, tablename):

        cacheobj = self.get_tableCache(tablename)

        # If this entry has been invalidated, or is too old, pull a new version
        # from the rpc server and update the cache.
        cacheobj.lock.acquire()
        try:
            if (not cacheobj.valid) or ((time.time() - cacheobj.timestamp) > \
                                        cacheobj.expirationDelta):
                self.updateTable(tablename)

        finally:
            cacheobj.lock.release()


    def updateTablesConditionally(self):

        for tablename in self.__get_tableNames():
            self.updateTableConditionally(tablename)
            
        
    def set_tableExpiration(self, tablename, expirationDelta):

        cacheobj = self.get_tableCache(tablename)

        cacheobj.lock.acquire()
        cacheobj.expirationDelta = expirationDelta
        cacheobj.lock.release()
            

    def isTableExpired(self, tablename):

        cacheobj = self.get_tableCache(tablename)

        cacheobj.lock.acquire()
        # Timestamp is only meaningful if cache object is valid
        if (not cacheobj.valid) or ((time.time() - cacheobj.timestamp) > \
                                    cacheobj.expirationDelta):
            val = True
        else:
            val = False

        cacheobj.lock.release()
        return val
            

    def invalidateTable(self, tablename):

        cacheobj = self.get_tableCache(tablename)

        cacheobj.lock.acquire()
        cacheobj.valid = False
        cacheobj.lock.release()
        

    def invalidateTables(self):

        for tablename in self.__get_tableNames():
            self.invalidateTable(tablename)
        

    def isTableValid(self, tablename):

        cacheobj = self.get_tableCache(tablename)

        cacheobj.lock.acquire()
        val = cacheobj.valid
        cacheobj.lock.release()
        return val
            

    def isValueExpired(self, aliasname):
        try:
            aliasinfo = self.info.get_aliasDef(aliasname)

        except common.statusError, e:
            raise KeyError(str(e))

        return self.isTableExpired(aliasinfo.tablename)
        

    def isValueValid(self, aliasname):
        try:
            aliasinfo = self.info.get_aliasDef(aliasname)

        except common.statusError, e:
            raise KeyError(str(e))

        return self.isTableValid(aliasinfo.tablename)
        

    # Extract a single status value from the table cache.  Throws an exception if
    # the table for this alias is not in the cache AND does NOT attempt to get the
    # table via rpc if the table does not exist.
    #
    def get_cachedStatusValue(self, aliasname, allow_fail=True):
        # Replace '--' with '.'
        #aliasname = aliasname.replace('__', '.')

        try:
            aliasinfo = self.info.get_aliasDef(aliasname)

        except common.statusError, e:
            raise KeyError(str(e))

        tablename = aliasinfo.tablename

        cacheobj = self.get_tableCache(tablename)

        cacheobj.lock.acquire()
        try:
            if not cacheobj.valid:
                raise common.statusError("Table '%s' not in cache" % tablename)

            res = cacheobj.table[aliasinfo.offset:aliasinfo.offset+aliasinfo.length]

        finally:
            cacheobj.lock.release()
            
        try:
            val = self.conv.convert(res, aliasinfo)

        except Convert.statusConversionError, e:
            if not allow_fail:
                raise e
            val = common.STATERROR

        return val


    # Extract a single status value.
    #
    def get_statusValue(self, aliasname, allow_fail=True):
        # Replace '--' with '.'
        #aliasname = aliasname.replace('__', '.')

        try:
            aliasinfo = self.info.get_aliasDef(aliasname)

        except common.statusError, e:
            raise KeyError(str(e))

        tablename = aliasinfo.tablename
        self.updateTableConditionally(tablename)

        cacheobj = self.get_tableCache(tablename)

        cacheobj.lock.acquire()
        try:
            res = cacheobj.table[aliasinfo.offset:aliasinfo.offset+aliasinfo.length]

        finally:
            cacheobj.lock.release()

        try:
            val = self.conv.convert(res, aliasinfo)

        except Convert.statusConversionError, e:
            if (not allow_fail) and (not self.supress_conversion_errors):
                raise e
            val = common.STATERROR
            
        return val


    def get_statusValuesList(self, aliasnames, allow_fail=True):
            res = []
            for aliasname in aliasnames:
                res.append(self.get_statusValue(aliasname,
                                                allow_fail=allow_fail))

            return res

        
    def get_statusValuesDict(self, res, allow_fail=True):

        for aliasname in res.keys():
            res[aliasname] = self.get_statusValue(aliasname,
                                                  allow_fail=allow_fail)

        
    #########################################################
    # For compatability with Gen2
    #########################################################
    #
    def fetch(self, statusDict, allow_fail=True):
        # Make a copy of the dictionary
        newDict = {}
        newDict.update(statusDict)

        self.get_statusValuesDict(newDict, allow_fail=allow_fail)
        return newDict
        
    def fetchOne(self, statusname, allow_fail=True):
        return self.get_statusValue(statusname, allow_fail=allow_fail)
        
    def fetchList(self, aliasnames, allow_fail=True):
            res = {}
            for aliasname in aliasnames:
                res[aliasname] = self.get_statusValue(aliasname,
                                                      allow_fail=allow_fail)
            return res
        
    def store(self, statusDict):
        raise common.statusError("This is a read-only status object.")

        
class possiblyStaleCachedStatusObj(cachedStatusObj):
    """ Implements a Python dictionary interface to the SOSS status system.

    Identical to a cachedStatusObj, but if freshly cached status cannot be
    obtained it will return stale cached data, if at all possible.  This
    object is useful for applications in which you would like to have the
    "last known good" status values even if the connection to the status
    server is disrupted.

    """
    
    def get_statusValue(self, aliasname):

        try:
            return cachedStatusObj.get_statusValue(self, aliasname)

        except common.statusError, e:
            return cachedStatusObj.get_cachedStatusValue(self, aliasname)

                
class storeStatusObj(cachedStatusObj):

    def __init__(self):

        statusObj = baseSOSSstatusObj()
        
        # Superclass initialization
        super(storeStatusObj, self).__init__(host=None, statusObj=statusObj)


    def initTable(self, tablename):

        cacheobj = self.get_tableCache(tablename)

        cacheobj.lock.acquire()

        try:
            # Initialize table to NULLs
            if cacheobj.table == None:
                cacheobj.table = ('\0' * cacheobj.tabledef.tablesize)
            cacheobj.valid = True
            cacheobj.timestamp = time.time()

        finally:
            cacheobj.lock.release()

            
    def updateTable(self, tablename):
        return self.initTable(tablename)

    
    def get_subTable(self, tablename, offset, length):

        # Make sure there is a valid table present
        self.updateTable(tablename)

        cacheobj = self.get_tableCache(tablename)

        cacheobj.lock.acquire()
        try:
            if offset + length > cacheobj.tabledef.tablesize:
                raise common.statusError("Bad offset/length for table size")

            return cacheobj.table[offset:offset+length]

        finally:
            cacheobj.lock.release()

    
    def get_table(self, tablename):

        # Make sure there is a valid table present
        self.updateTable(tablename)

        cacheobj = self.get_tableCache(tablename)

        cacheobj.lock.acquire()
        try:
            return cacheobj.table

        finally:
            cacheobj.lock.release()

    
    def put_subTable(self, tablename, data, offset):

        # Make sure there is a valid table present
        self.updateTable(tablename)

        cacheobj = self.get_tableCache(tablename)

        cacheobj.lock.acquire()
        try:
            newtbl = cacheobj.table[:offset] + data + \
                     cacheobj.table[offset+len(data):]

            if len(newtbl) != cacheobj.tabledef.tablesize:
                raise common.statusError("Bad data length for table size: %d != %d" % (
                    len(newtbl), cacheobj.tabledef.tablesize))

            cacheobj.table = newtbl

        finally:
            cacheobj.lock.release()

    
    def put_table(self, tablename, data):

        self.put_subTable(tablename, data, 0)
    
            
# END SOSS_status.py

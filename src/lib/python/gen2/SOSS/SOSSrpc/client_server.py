#
# SOSS/TCS rpc interface module
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Tue Jun 16 14:16:21 HST 2009
#]
# Bruce Bon (Bruce.Bon@SubaruTelescope.org)  2006-11-21
#
import os, socket, select
import threading, Queue
import logging

import rpc

import common
import SOSSrpc

# RPC interface includes
# constants file not necessary and causes FutureWarning
#from OSSC_ComCDconstants import *
from OSSC_ComCDtypes import *
import OSSC_ComCDpacker


class rpcClientError(common.rpcError):
    """RPC Server Error Exception.  Inherits from Exception and
       adds no functionality, but distinct name allows distinct catch
       clauses."""
    pass

class rpcServerError(common.rpcError):
    """RPC Server Error Exception.  Inherits from Exception and
       adds no functionality, but distinct name allows distinct catch
       clauses."""
    pass


## def make_client(prognum, args, **kwdargs):
##     '''Make a SOSS rpc client.  args is a Bunch with a 'client' variable
##     defined.  
##     '''

##     try:
##         # Create buffer for RPC message
##         rpcbuf = rpcMsg(**kwdargs)
##         client = TCP_rpcClient(rpcbuf.receiver, prognum, rpcmsg=rpcbuf)
##         args.client = client

##         return client

##     except Exception, e:
##         args.client = None
##         raise rpcClientError("Couldn't create RPC client: %s" % str(e))


def make_client(args, rpcmsg):
    try:
        receiver = common.strip_host(rpcmsg.receiver)
        #client = TCP_rpcClient(receiver, args.prognum, rpcmsg=rpcbuf)
        client = TCP_rpcClient(receiver, args.prognum)
        args.client = client

        return client

    except Exception, e:
        args.client = None
        raise rpcClientError("Couldn't create RPC client: %s" % str(e))


def get_client(args, rpcmsg):

    if not args.client:
        receiver = common.strip_host(rpcmsg.receiver)
        args.logger.debug("Trying to create client to '%s'" % \
                         receiver)
        client = make_client(args, rpcmsg)

    else:
        client = args.client

    return client


def callrpc(args, rpcmsg=None):

    if not rpcmsg:
        rpcmsg = args.rpcbuf

    client = get_client(args, rpcmsg)

    args.logger.info(str(rpcmsg))
    try:
        res = client.call(rpcmsg=rpcmsg)

    except Exception, e:
        args.logger.warn("Client call error (possible stale client), resetting client...")
        args.client = None
        client = make_client(args, rpcmsg)

        # Try one more time...best effort
        try:
            res = client.call(rpcmsg=rpcmsg)

        except Exception, e:
            args.client = None
            raise rpcClientError("Exception raised invoking client rpc: %s" % str(e))

    if not res:
        raise rpcClientError("Error return from rpc call: %s" % str(res))

    return res
    

class rpcClient(object):
    """SOSS RPC Client base class.  Clients should inherit from this.
    This class is abstract because it calls make_call(), which is
    not defined herein or in object.  A derived class should inherit
    from rpcClient and from one of {rpc.TCPClient, rpc.UDPClient, 
    rpc.BroadcastUDPClient}.
    """

    def __init__(self, fun_index=1, rpcmsg=None):
        """Constructor.  Sets default function index.  Accepts an RPC message
        object, if furnished.
        """

        self.fun_index = fun_index
        self.rpcbuf = rpcmsg
        #self.lock = threading.RLock()

    #
    # RPC stuff
    #

    def addpackers(self):
        """Set data payload packer and unpacker to OSSC_ComCD versions.
           Subclass must inherit also from rpc.py, which will access 
           these variables.
           """
        self.packer = OSSC_ComCDpacker.OSSC_COMCDPacker()
        self.unpacker = OSSC_ComCDpacker.OSSC_COMCDUnpacker('')


    def call(self, fun_index=None, rpcmsg=None):
        """Call the remote function.  Subclass must inherit also from 
           rpc.py, which defines the make_call() method (i.e. this makes 
           an abstract method call here).
           """
        if  fun_index == None:
            fun_index = self.fun_index

        if not rpcmsg:
            rpcmsg = self.rpcbuf

        # Not actually sure that we need this lock, but I strongly suspect that
        # the rpc.py code is not thread-safe.
        self.lock.acquire()
        try:

            #arg = rpcmsg.packet2str()
            arg = str(rpcmsg)
            res = self.make_call(fun_index, arg,
                                 self.packer.pack_ComCDarg,
                                 self.unpacker.unpack_bool)
        finally:
            self.lock.release()
            
        return res

    
class TCP_rpcClient(rpcClient, rpc.TCPClient):
    """SOSS TCP RPC Client Class.  Inherits addpackers() and call() from 
       rpcClient.  Inherits RPC client methods (do_call(), makesocket(),
       make_call(), close(), etc.) from rpc.TCPClient, rpc.RawTCPClient and 
       rpc.Client."""

    def __init__(self, host, prognum, progver=1,
                 uid=os.getuid(), gid=os.getgid(),
                 #sec=(rpc.AUTH_UNIX, rpc.make_auth_unix_default()),
                 # (This used to be our default, but has problems on some
                 #  systems where LDAP is used for user authentication.)
                 #sec=(rpc.AUTH_UNIX, None),
                 sec=(rpc.AUTH_NULL, None),
                 fun_index=1, rpcmsg=None, logger=None):
        """Constructor.
        """
        # Call parent constructors to provide parameters
        rpc.TCPClient.__init__(self, host, prognum, progver, sec,
                               logger=logger)
        rpcClient.__init__(self, fun_index=fun_index, rpcmsg=rpcmsg)
        # These are needed by the rpc.py package
        self.uid = uid
        self.gid = gid


class UDP_rpcClient(rpcClient, rpc.UDPClient):
    """SOSS/TCS TCP RPC Client Class.  Inherits addpackers() and call() from 
       rpcClient.  Inherits RPC client methods (do_call(), makesocket(),
       make_call(), close(), etc.) from rpc.TCPClient, rpc.RawTCPClient and 
       rpc.Client."""

    def __init__(self, host, prognum, progver=1,
                 uid=os.getuid(), gid=os.getgid(),
                 #sec=(rpc.AUTH_UNIX, rpc.make_auth_unix_default()),
                 # (This used to be our default, but has problems on some
                 #  systems where LDAP is used for user authentication.)
                 #sec=(rpc.AUTH_UNIX, None),
                 sec=(rpc.AUTH_NULL, None),
                 fun_index=1, rpcmsg=None, logger=None):
        """Constructor.
        """
        # Call parent constructors to provide parameters
        rpc.UDPClient.__init__(self, host, prognum, progver, sec,
                               logger=logger)
        rpcClient.__init__(self, fun_index=fun_index, rpcmsg=rpcmsg)
        # These are needed by the rpc.py package
        self.uid = uid
        self.gid = gid


class lazyClient(object):
    """This is a wrapper class that creates a delegate object to a TCP_rpcClient.
    It abstracts lazy client creation and stale client handling (client recreation),
    thus making more robust clients (see below).  It is also thread safe, so a
    lazyClient object can be shared freely by several threads.

    lazy client creation handles the case that a client is created before the server
    is up and has registered the function with the portmapper.  It allows clients
    to be created before servers, just as long as the server function is not CALLED
    before the server is up.  This gets around a common case of errors where a
    client program starts before the server, but doesn't actually use the server
    until it is up.

    stale client handling is for cases where the server is restarted, breaking all
    existing TCP connections and possibly rebinding to a different port, thus rendering
    all existing clients unable to continue.  The lazy client will attempt to recreate
    the client in an call error condition and retry the call, thus surviving a common case
    where a normal client would fail.

    Typical use:
    client = lazyClient(host=dsthost, prognum=prognum, logger=logger)

    rpcmsg = SOSScmdRpcMsg(seq_num=seq_num)
    rpcmsg.pack_cd(cmdstr)
    
    res = client.callrpc(rpcmsg)
    """

    def __init__(self, clientClass=TCP_rpcClient, **kwdargs):
        """The constructor parameters are the same as for TCP_rcpClient,
        except that everything is passed by keyword argument.
        """
        # Lock for thread safety on self.client checks and mutations
        self.lock = threading.RLock()
        # RPC client (use lazy client creation)
        self.client = None

        self.clientClass = clientClass

        # prgnum must be explicit
        if not kwdargs.has_key('prognum'):
            raise rpcClientError("client creation requires prognum")
        self.prognum = kwdargs['prognum']
        
        # These will be passed to TCP_rpcClient at client creation time.
        # They must include the prognum, and usually 
        self.clientArgs = {}
        self.clientArgs.update(kwdargs)
        del self.clientArgs['prognum']

        # host may be specified here, or inferred from rpc packet later
        if self.clientArgs.has_key('host'):
            self.host = self.clientArgs['host']
            del self.clientArgs['host']
        else:
            self.host = None

        if self.clientArgs.has_key('logger'):
            self.logger = self.clientArgs['logger']
        else:
            self.logger = logging.getLogger("rpc")
        
    def _make_client(self, rpcmsg):
        """This function makes a client and stores a reference in self.client
        """
        self.lock.acquire()
        try:
            # If the client args specified a host, use it, otherwise, infer
            # host from the rpcmsg (SOSS rpc messages have a receiver field)
            if self.host:
                tohost = self.host
            else:
                tohost = common.strip_host(rpcmsg.receiver)

            # Create client
            self.client = None
            self.logger.debug("Trying to create client to '%s (prgnum=%x)'" % (
                tohost, self.prognum))
            try:
                self.client = self.clientClass(tohost, self.prognum, **self.clientArgs)

            except Exception, e:
                raise rpcClientError("Couldn't create RPC client: %s" % str(e))

        finally:
            self.lock.release()


    def callrpc(self, rpcmsg, fun_index=None):
        """Try to use the current client to call the RPC function
        """

        self.lock.acquire()
        try:
            if not self.client:
                self._make_client(rpcmsg)

            self.logger.info(str(rpcmsg))
            try:
                res = self.client.call(fun_index=fun_index, rpcmsg=rpcmsg)

            except Exception, e:
                self.logger.warn("Client call error (possible stale client), resetting client...")
                self._make_client(rpcmsg)

                # Try one more time...best effort
                try:
                    res = self.client.call(fun_index=fun_index, rpcmsg=rpcmsg)

                except Exception, e:
                    self.client = None
                    raise rpcClientError("Exception raised invoking client rpc: %s" % str(e))

        finally:
            self.lock.release()

        return res


class rpcServer(object):
    """SOSS RPC Server Class.  Servers should inherit from this.
    This provides a generic server that simply receives an rpc packet, 
    enqueues it on a queue and then replies with a True value and loops.
    See also TCP_rpcServer, below.
    """ 

    def __init__(self, ev_quit=None, logger=None, queue=None, tag=None,
                 func=None):
        """Constructor.  Initialized quit-event and self.rpcqueue to receive
           messages as they come in.  Sets self.mythread to None, indicating
           that no server thread is running."""

        # Event that is used to tell the server to terminate
        if ev_quit:
            self.quit = ev_quit
        else:
            self.quit = threading.Event()

        # Events that are used to detect that the server has stopped or started
        # See server_started() and server_stopped()
        self.ev_stopped = threading.Event()
        self.ev_stopped.set()
        self.ev_started = threading.Event()

        # Queue of rpc messages received
        if queue != None:
            self.rpcqueue = queue
        else:
            self.rpcqueue = Queue.Queue()

        # Optional fn to process messages
        self.func = func
        # Optional tag to tag messages on the queue
        self.tag = tag
        self.logger = logger
        
        # Indicate that no server thread is running.
        self.mythread = None

        # Subclass may overload this--it's simply the name given to the thread
        # that handles the requests
        self.name = 'SOSS_rpcServer'
        # Timeout value used by subclass in socket select calls
        self.timeout = 0.1

    #
    # RPC abstract methods 
    #

    def addpackers(self):
        """Subclass must inherit also from rpc.py, which will access 
        these methods.  Subclasses must override.
        """
        raise rpcServerError("subclass should override this method!")


    def beatheart(self):
        """Used by AsyncTCPServer objects."""
        pass


    def handle_1(self):
        """Function to handle remote call served by this object.
        Subclass must override this method, whihc is invoked from
        rpc.py.
        """
        raise rpcServerError("subclass should override this method!")


    #
    # initialization methods 
    #

    def start(self, usethread=True, wait=True, timeout=None):
        """Start the rpc server.
        If usethread=False, then this caller enters the server handling loop and
        does not return until the server terminates by another caller calling
        stop().  If usethread=True then a thread is started to execute the server.

        The wait and timeout parameters only matter if usethread==False.
        If wait==True, then caller wants to wait for the rpc server thread to be up
        before returning.  See wait_start() for the behavior of the timeout parameter.
        """
        self.quit.clear()

        if not usethread:
            self.rpc_server()

        else:
            # Create a thread for the rpc server (rpc_server should be defined in
            # the subclass; e.g. TCP_rpcServer)
            self.mythread = threading.Thread(target=self.rpc_server, name=self.name)
            self.mythread.start()

            if wait:
                self.wait_start(timeout=timeout)


    def stop(self, wait=True, timeout=None):
        """Stop the rpc server.
        If wait==True, then caller wants to wait for the rpc server to terminate
        before returning.  See wait_stop() for the behavior of the timeout parameter.
        """
        self.quit.set()

        # Wait for server thread to quit.  Type of wait depends on whether we spawned
        # a thread or not.
        if wait:
            if self.mythread and (timeout == None):
                self.mythread.join()
            else:
                self.wait_stop(timeout=timeout)


    def wait_start(self, timeout=None):
        """Wait for an rpc server that was previously start()-ed to be up and 'hot'.
        If timeout!=None then it specifies a time in seconds (a float) to wait.
        If the server is not started by that time, an rpcServerError exception is
        raised.  On the other hand, if timeout==None, then it will wait indefinitely.
        """
        self.ev_started.wait(timeout=timeout)

        if not self.ev_started.isSet():
            raise rpcServerError("rpc server failed to start by deadline")

        
    def wait_stop(self, timeout=None):
        """Wait for an rpc server that was previously stop()-ped to terminate.
        If timeout!=None then it specifies a time in seconds (a float) to wait.
        If the server is not down by that time, an rpcServerError exception is
        raised.  On the other hand, if timeout==None, then it will wait indefinitely.
        """
        self.ev_stopped.wait(timeout=timeout)

        if not self.ev_stopped.isSet():
            raise rpcServerError("rpc server failed to stop by deadline")


    def rpc_server(self):
        """rpcServer processing loop.
        Some subclass ultimately needs to also inherit from
        rpc.MultipleTCPServer or other rpc.py Server class in order
        to define some functions called herein.
        """

        # Try to unregister from portmapper, just in case there is a stale entry
        try:
            self.unregister()
            if self.logger:
                self.logger.debug("Found stale RPC entry at portmapper.")

        except rpc.PortMapError, e:
            if self.logger:
                self.logger.debug("No registration at portmapper: %s" % (
                    str(e)))
        
        # Now re-register with portmapper
        try:
            if self.logger:
                self.logger.debug("Registering RPC entry at portmapper.")
            self.register()

        except:
            raise rpcServerError("Unable to register with portmapper")

        if self.logger:
            self.logger.debug("RPC server started.")

        # Defined in the base class
        self.server_started()
            
        try:
            # Serve requests until interrupted
            self.loop()

        finally:
            try:
                if self.logger:
                    self.logger.debug("Unregistering RPC entry at portmapper.")
                self.unregister()

            except rpc.PortMapError:
                pass

            if self.logger:
                self.logger.debug("RPC server terminated.")

            # Defined in the base class
            self.server_stopped()
            
    
    def server_started(self):
        """Called by a subclass when the server starts.
        """
        self.ev_started.set()
        self.ev_stopped.clear()
    
    def server_stopped(self):
        """Called by a subclass when the server stops.
        """
        self.ev_stopped.set()
        self.ev_started.clear()
    

class TCP_rpcServer(rpcServer, rpc.MultipleTCPServer):
    """SOSS TCP RPC Server Class.  Inherits from rpcServer and 
    rpc.MultipleTCPServer.
    """

       
    def __init__(self, prognum, progver=1, host='', port=None, ev_quit=None,
                 logger=None, queue=None, tag=None, func=None):
        """Constructor.  Finds a free port, unless handed a port to use.
        """

        # If we are given a specific port to use, try to bind to it.
        if port:
            rpc.MultipleTCPServer.__init__(self, host, prognum, progver, port,
                                           logger=logger)
            found_free_port = True
            
        # Otherwise, try a few random ports to see if we can locate one.
        else:
            found_free_port = False
            attempts = 0

            while (not found_free_port) and (attempts < 500):
                try:
                    port = common.get_randomport()
                    rpc.MultipleTCPServer.__init__(self, host, prognum,
                                                   progver, port, logger=logger)
                    found_free_port = True
                    break

                except socket.error:
                    attempts += 1
                    continue

        if found_free_port:
            rpcServer.__init__(self, ev_quit=ev_quit, logger=logger,
                               queue=queue, tag=tag, func=func)
        else:
            raise rpcServerError("Could not find a port to bind.")


##     def loop(self):
##         # I hate to replace this call to self.loop() with the actual
##         # code from rpc.py, but it looped forever and I need the thread
##         # to notice when when we call stop().

##         self.sock.listen(0)
##         while not self.quit.isSet():
##             input = [ self.sock ] + self.active
##             try:
##                 (sin, sout, sexp) = select.select(input, [], [], self.timeout)

##             except KeyboardInterrupt:
##                 return

##             for i in sin:
##                 if i == self.sock:
##                     self.newsession(self.sock.accept())
##                 else:
##                     self.session(i)


class UDP_rpcServer(rpcServer, rpc.UDPServer):
    """SOSS UDP RPC Server Class.  Inherits from rpcServer and 
    rpc.UDPServer.
    """
       
    def __init__(self, prognum, progver=1, host='', port=None, ev_quit=None,
                 logger=None, queue=None, tag=None, func=None):
        """Constructor.  Finds a free port, unless handed a port to use.
        """

        # If we are given a specific port to use, try to bind to it.
        if port:
            rpc.UDPServer.__init__(self, host, prognum, progver, port,
                                   logger=logger)
            found_free_port = True
            
        # Otherwise, try a few random ports to see if we can locate one.
        else:
            found_free_port = False
            attempts = 0

            while (not found_free_port) and (attempts < 500):
                try:
                    port = common.get_randomport()
                    rpc.UDPServer.__init__(self, host, prognum, progver, port,
                                           logger=logger)
                    found_free_port = True
                    break

                except socket.error:
                    attempts += 1
                    continue

        if found_free_port:
            rpcServer.__init__(self, ev_quit=ev_quit, logger=logger,
                               queue=queue, tag=tag, func=func)
        else:
            raise rpcServerError("Could not find a port to bind.")


##     def loop(self):
##         # I hate to replace this call to self.loop() with the actual
##         # code from rpc.py, but it looped forever and I need the thread
##         # to notice when when we call stop().

##         try:
##             while not self.quit.isSet():
##                 input = [ self.sock ]
##                 try:
##                     (sin, sout, sexp) = select.select(input, [], [],
##                                                       self.timeout)

##                 except KeyboardInterrupt:
##                     return

##                 if sin != []:
##                     self.session()

##         finally:
##             self.sock.close()
            

class SOSS_rpcServer(TCP_rpcServer):
    #
    # fully realized methods for abstract methods in rpcServer
    #

    def addpackers(self):
        """Set data payload packer and unpacker to OSSC_ComCD versions.
        This will be called from rpc.py
        """
        self.packer = OSSC_ComCDpacker.OSSC_COMCDPacker()
        self.unpacker = OSSC_ComCDpacker.OSSC_COMCDUnpacker('')


    def handle_1(self):
        """Function to handle remote call served by this object.
        Unpacks incoming message into a string, converts it to an
        SOSScmdRpcMsg object and places the object onto self.rpcqueue.
        Always returns True to the remote caller.
        This will be called from rpc.py
        """
        data = self.unpacker.unpack_ComCDarg()

        rpcmsg = SOSSrpc.SOSScmdRpcMsg(rpcmsg=data)
        if self.logger:
            self.logger.info(data)
        
        # Add message to queue of received messages
        if self.func != None:
            self.rpcqueue.put(self.func(rpcmsg))
        elif self.tag != None:
            self.rpcqueue.put((self.tag, (rpcmsg,)))
        else:
            self.rpcqueue.put(rpcmsg)

        res = True
        try:
            self.turn_around()
            
        except rpc.RPCUnextractedData:
            self.logger.error("*** Unextracted Data in request!")
            res = False

        # Return confirmation result
        self.packer.pack_bool(res)


class clientServerPair(object):

    def __init__(self, key, initiator=False, logger=None, ev_quit=None,
                 myhost='', recvqueue=None, tag=None, func=None):

        super(clientServerPair, self).__init__()

        self.logger = logger
        self.ev_quit = ev_quit
        
        # Look up RPC configuration info
        try:
            svc = common.lookup_rpcsvc(key)

        except KeyError, e:
            raise common.rpcError("Can't find rpc program numbers (key=%s)" % key)

        # Set send and receive program numbers based on role of this side
        # (initiator of transaction or not)
        if initiator:
            self.send_prognum = svc.server_receive_prgnum
            self.recv_prognum = svc.server_send_prgnum
        else:
            self.send_prognum = svc.server_send_prgnum
            self.recv_prognum = svc.server_receive_prgnum
        
        # Create RPC server
        self.server = SOSS_rpcServer(host=myhost,
                                     port=None,
                                     prognum=self.recv_prognum,
                                     ev_quit=self.ev_quit,
                                     logger=self.logger,
                                     queue=recvqueue,
                                     tag=tag, func=func)

        # Create RPC client 
        self.client = lazyClient(logger=self.logger, prognum=self.send_prognum)

        
    def callrpc(self, rpcmsg):

        res = self.client.callrpc(rpcmsg)

        # SOSS RPC calls are supposed to return True
        if not res:
            raise rpcClientError("Error return from rpc call: %s" % str(res))

        return res


    def start(self, usethread=True, wait=True, timeout=None):
        self.server.start(usethread=usethread, wait=wait, timeout=timeout)

    def stop(self, wait=True, timeout=None):
        self.server.stop(wait=wait, timeout=timeout)

    def wait_start(self, timeout=None):
        self.server.wait_start(timeout=timeout)

    def wait_stop(self, timeout=None):
        self.server.wait_stop(timeout=timeout)

#END

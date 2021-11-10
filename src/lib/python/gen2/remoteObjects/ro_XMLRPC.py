#
# ro_XMLRPC.py -- enhanced XML-RPC services for remoteObjects system
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Feb 22 16:29:55 HST 2012
#]
#
"""
"""
import sys, os, time
import threading
import base64, urllib
import httplib
import string
import types
import socket, SocketServer, select
import xmlrpclib
import SimpleXMLRPCServer
import traceback
import logging
try:
    import fcntl
except ImportError:
    fcntl = None
try:
    from OpenSSL import SSL
except ImportError:
    SSL = None

import Task

version = '20101208.0'

# Timeout value for XML-RPC sockets
socket_timeout = 0.25


class Error(Exception):
    """Class of errors raised in this module."""
    pass

class socketTimeout(Error):
    """Raised when a socket times out waiting for a client."""
    pass


#
# ------------------ CONVENIENCE FUNCTIONS ------------------
#

def make_serviceProxy(host, port, auth=False, secure=False, timeout=None):
    """
    Convenience function to make a XML-RPC service proxy.
    'auth' is None for no authentication, otherwise (user, passwd)
    'secure' should be True if you want to use SSL, otherwise vanilla http.
    """
    try:
        if secure:
            transport = SecureAuthTransport(auth, use_datetime=0,
                                            timeout=timeout)
            url = 'https://%s:%d/' % (host, port)
            proxy = SSLServerProxy(url, transport=transport, allow_none=True)
        else:
            transport = BasicAuthTransport(auth, use_datetime=0,
                                           timeout=timeout)
            url = 'http://%s:%d/' % (host, port)
            proxy = xmlrpclib.ServerProxy(url, transport=transport,
                                          allow_none=True)

        return proxy
    
    except Exception, e:
        raise Error("Can't create proxy to service found on '%s:%d': %s" % (
            host, port, str(e)))


#
# ------------------ CLIENT EXTENSIONS ------------------
#
# [NOTE:SSL_PAD]
# This is a hack to get around an anomaly with the OpenSSL sockets library.
# If the buffer size is too small (< 1024 KB), performance takes a large hit.
# So we pad the request with 2KB worth of data and strip it out on the other
# side.  This is the data we add.
ssl_padding = '0'*2048


class BaseAuthTransport(object):
    """
    Handles an HTTP transaction to an XML-RPC server.  We augment the
    xmlrpclib.Transport class to pass an authentication header line.
    An instance of this class can by passed as the 'transport' argument
    to xmlrpclib.ServerProxy() to have your client pass authorization.

    Usage:
        transport = BasicAuthTransport(('myuser', 'mypass'))
        
        proxy = xmlrpclib.ServerProxy('http://myhost/',
                                      transport=transport)
    """

    # client identifier (may be overridden)
    user_agent = "remoteObjects/%s" % version

    def __init__(self, auth, timeout=None):
        if not auth:
            self.extra_headers = None
        else:
            (username, password) = auth
            auth = ('%s:%s' % (username, password))
            auth = base64.encodestring(urllib.unquote(auth))
            auth = string.join(string.split(auth), "") # get rid of whitespace
            self.extra_headers = [
                ("Authorization", "Basic " + auth)
                ]

        self.timeout = timeout

    # We override make_connection() in order to set a timeout on the
    # socket connection if possible
    def make_connection(self, host):
        #return an existing connection if possible.  This allows
        #HTTP/1.1 keep-alive.
        # if self._connection and host == self._connection[0]:
        #     return self._connection[1]

        # create a HTTP connection object from a host descriptor
        chost, self._extra_headers, x509 = self.get_host_info(host)
        #store the host argument along with the connection object
        self._connection = host, httplib.HTTPConnection(chost,
                                                        timeout=self.timeout)
        return self._connection[1]

       
class BasicAuthTransport(BaseAuthTransport, xmlrpclib.Transport):

    def __init__(self, auth, use_datetime=0, timeout=None):
        BaseAuthTransport.__init__(self, auth, timeout=timeout)
        xmlrpclib.Transport.__init__(self, use_datetime=use_datetime)
        self._use_datetime = use_datetime

    def get_host_info(self, host):
        x509 = {}
        return (host, self.extra_headers, x509)


class SecureAuthTransport(BaseAuthTransport, xmlrpclib.SafeTransport):

    def __init__(self, auth, use_datetime=0, timeout=None):
        BaseAuthTransport.__init__(self, auth, timeout=timeout)

        if self.extra_headers == None:
            self.extra_headers = []
        self.extra_headers.append(
                ("X-Padding", ssl_padding)
            )
        xmlrpclib.SafeTransport.__init__(self, use_datetime=use_datetime)
        self._use_datetime = use_datetime

    def get_host_info(self, host):
        x509 = {}
        return (host, self.extra_headers, x509)


class SSLServerProxy:
    """
    Copy of xmlrpclib.ServerProxy used for SSL connections.  Provides a hack for a
    wierd anomaly with bad performance for small payloads.  See [NOTE:SSL_PAD]
    """
    def __init__(self, uri, transport=None, encoding=None, verbose=0,
                 allow_none=0, use_datetime=0):
        # establish a "logical" server connection

        # get the url
        type, uri = urllib.splittype(uri)
        if type not in ("http", "https"):
            raise IOError, "unsupported XML-RPC protocol"
        self.__host, self.__handler = urllib.splithost(uri)
        if not self.__handler:
            self.__handler = "/RPC2"

        if transport is None:
            if type == "https":
                transport = xmlrpclib.SafeTransport(use_datetime=use_datetime)
            else:
                transport = xmlrpclib.Transport(use_datetime=use_datetime)
        self.__transport = transport

        self.__encoding = encoding
        self.__verbose = verbose
        self.__allow_none = allow_none


    def __request(self, methodname, params):

        # call a method on the remote server
        request = xmlrpclib.dumps(params, methodname,
                                  encoding=self.__encoding,
                                  allow_none=self.__allow_none)

        response = self.__transport.request(
            self.__host,
            self.__handler,
            request,
            verbose=self.__verbose
            )

        if len(response) == 1:
            response = response[0]

        return response
        
    def __repr__(self):
        return (
            "<ServerProxy for %s%s>" %
            (self.__host, self.__handler)
            )

    __str__ = __repr__

    def __getattr__(self, name):
        # magic method dispatcher
        return xmlrpclib._Method(self.__request, name)

#
# ------------------ SERVER EXTENSIONS ------------------
#

# We overload SimpleXMLRPCRequestHandler in order to provide a exception
# handling wrapper around the superclass method do_POST, which handles
# requests. 
#
class XMLRPCRequestHandler(SimpleXMLRPCServer.SimpleXMLRPCRequestHandler):
    """
    """
    #def __init__(self, *args, **kwdargs):
    #    SimpleXMLRPCServer.SimpleXMLRPCRequestHandler.__init__(*args, **kwdargs)

    def get_authorization_creds(self):
        auth = self.headers.get("authorization", None)
        logger = self.server.logger

        #logger.debug("Auth is %s" % (str(auth)))
        if auth:
            try:
                method, auth = auth.split()
                if method.lower() == 'basic':
                    auth = base64.decodestring(auth)
                    username, password = auth.split(':')
                    #logger.debug("username: '%s', password: '%s'" % (
                    #    username, password))
                    auth = { 'method': 'basic',
                             'username': username,
                             'password': password,
                             }
                else:
                    logger.error("unsupported auth method: '%s'" % method)
                    auth = None
            except IndexError:
                logger.error("unrecognized auth cred: '%s'" % auth)
                auth = None

        return auth

                
    def _dispatch(self, method, params):
        """
        Called to dispatch an XML-RPC request.
        """
        auth = self.get_authorization_creds()
        
        
        # Refer back to server to do the dispatch
        return self.server.do_dispatch(method, params, auth,
                                       self.client_address)
        

##     def do_POST(self):
##         """
##         Called to handle a POST request on the HTTP protocol (all XML-RPC
##         is supposed to be done via POST).
##         """
##         logger = self.server.logger

##         # If we don't wrap this in a try clause then when server-client
##         # connections are disrupted between request and reply the reply
##         # gets a 'Broken pipe' error.  This lets it fail more gracefully.
##         try:
##             logger.debug("Dispatching via XMLRPCRequestHandler.do_POST()")

##             return SimpleXMLRPCServer.SimpleXMLRPCRequestHandler.do_POST(self)

##         except socket.error, e:
##             errstr = "Communication error: %s" % str(e)
##             logger.warn(errstr)
##             logger.info("Remote object server continuing...")

##             # internal error, report as HTTP server error
##             self.send_response(500)
##             self.end_headers()

##     def do_POST(self):
##         """
##         Called to handle a POST request on the HTTP protocol (all XML-RPC
##         is supposed to be done via POST).
##         """
##         logger = self.server.logger

##         # Check that the path is legal
##         if not self.is_rpc_path_valid():
##             self.report_404()
##             return

##         try:
##             # Get arguments by reading body of request.
##             # We read this in chunks to avoid straining
##             # socket.read(); around the 10 or 15Mb mark, some platforms
##             # begin to have problems (bug #792570).
##             max_chunk_size = 10*1024*1024
##             size_remaining = int(self.headers["content-length"])
##             L = []
##             while size_remaining:
##                 chunk_size = min(size_remaining, max_chunk_size)
##                 L.append(self.rfile.read(chunk_size))
##                 size_remaining -= len(L[-1])
##             data = ''.join(L)

##             # In previous versions of SimpleXMLRPCServer, _dispatch
##             # could be overridden in this class, instead of in
##             # SimpleXMLRPCDispatcher. To maintain backwards compatibility,
##             # check to see if a subclass implements _dispatch and dispatch
##             # using that method if present.
##             response = self.server._marshaled_dispatch(
##                     data, getattr(self, '_dispatch', None)
##                 )
##         except Exception, e: # This should only happen if the module is buggy
##             # internal error, report as HTTP server error
##             logger.error("Internal exception raised: %s" % str(e))
##             self.send_response(500)
##             self.end_headers()
##         else:
##             # got a valid XML RPC response
##             self.send_response(200)
##             self.send_header("Content-type", "text/xml")
##             self.send_header("Content-length", str(len(response)))
##             self.end_headers()
##             self.wfile.write(response)

##             # shut down the connection
##             self.wfile.flush()
##             self.connection.shutdown(1)

    
#class BaseXMLRPCServer(SocketServer.TCPServer, SimpleXMLRPCServer.SimpleXMLRPCDispatcher):
class BaseXMLRPCServer(SimpleXMLRPCServer.SimpleXMLRPCDispatcher):
    """Yet Another XML-RPC Server.

    Simple XML-RPC server that allows functions and a single instance
    to be installed to handle requests. The default implementation
    attempts to dispatch XML-RPC calls to the functions or instance
    installed in the server. Override the _dispatch method inhereted
    from SimpleXMLRPCDispatcher to change this behavior.
    """

    def __init__(self, host, port, ev_quit=None, timeout=0.1,
                 logger=None,
                 requestHandler=XMLRPCRequestHandler,
                 logRequests=False, allow_none=True, encoding=None,
                 authDict=None):
        
        self.logRequests = logRequests
        self.authDict = authDict

        # Poorly documented hack to allow port to be released immediately after
        # application terminates...see SocketServer.py
        self.allow_reuse_address = True

        if logger:
            self.logger = logger
        else:
            self.logger = logging.Logger('null')

        # Our termination flag
        if not ev_quit:
            self.ev_quit = threading.Event()
        else:
            self.ev_quit = ev_quit
        
        # Defines how responsive to termination we are
        self.timeout = timeout

        # Yecchh!  They changed the SimpleXMLRPCDispatcher constructor
        # API at Python v2.4
        if sys.hexversion < 0x02040000:
            SimpleXMLRPCServer.SimpleXMLRPCDispatcher.__init__(self)
            self.encoding = encoding
            self.allow_none = allow_none
        else:
            # Python 2.5 or greater (allow None as a type)
            SimpleXMLRPCServer.SimpleXMLRPCDispatcher.__init__(self, allow_none, encoding)


    # Hacked version of the Python 2.3 _marshaled_dispatch function to allow
    # None as a type (it's not in the XML-RPC standard)
    def _hacked_marshaled_dispatch(self, data, dispatch_method = None):
        params, method = xmlrpclib.loads(data)

        # generate response
        try:
            if dispatch_method is not None:
                response = dispatch_method(method, params)
            else:
                response = self._dispatch(method, params)
            #print "response is: %s" % str(response)
            # wrap response in a singleton tuple
            response = (response,)
            response = xmlrpclib.dumps(response, methodresponse=1,
                                       allow_none=self.allow_none,
                                       encoding=self.encoding)
        except Fault, fault:
            # TODO: log Faults ?
            response = xmlrpclib.dumps(fault, allow_none=self.allow_none,
                                       encoding=self.encoding)
        except Exception, e:
            # report exception back to client
            try:
                # include traceback if possible
                (type, value, tb) = sys.exc_info()
                tb_str = ("Traceback:\n%s" % '\n'.join(traceback.format_tb(tb)))
                self.logger.error(tb_str)

                response = xmlrpclib.dumps(
                    xmlrpclib.Fault(1, "%s:%s--%s" % (type, value, tb_str)),
                    allow_none=self.allow_none, encoding=self.encoding)
            except:
                response = xmlrpclib.dumps(
                    xmlrpclib.Fault(1, "%s" % (str(e))),
                    allow_none=True)

        return response


    def verify_request(self, request, client_address):
        """Verify the request.  May be overridden.

        Return True if we should proceed with this request.

        """
        #possible host-based authentication protection
        ip, port = client_address
        self.logger.debug("caller ip: %s:%d" % (ip, port))
        #if not (ip in self.authorizedHosts):
        #    return False
        return True


    def authenticate_client(self, methodName, params, auth, client_address):
        # this is the caller's ip address and port
        ip, port = client_address

        if not auth:
            self.logger.error("No authentication credentials passed")
            raise Error("Service requires authentication and no credentials passed")

        # this is the client authentication, pulled from the HTTP header
        try:
            username = auth['username']
            password = auth['password']

        except KeyError:
            self.logger.error("Bad authentication credentials passed")
            raise Error("Service only handles 'basic' authentication type")

        if not self.authDict.has_key(username):
            self.logger.error("No user matching '%s'" % username)
            # sleep thwarts brute force attacks
            # but also delays applications when there is a legitimate
            # authentication mismatch
            #time.sleep(1.0)
            raise Error("Service requires authentication; username or password mismatch")

        if self.authDict[username] != password:
            self.logger.error("Password incorrect '%s'" % password)
            # sleep thwarts brute force attacks
            time.sleep(1.0)
            raise Error("Service requires authentication; username or password mismatch")

        self.logger.debug("Authorized client '%s'" % (username))


    def my_dispatch(self, methodName, params, auth, client_addr):
        """Dispatches the XML-RPC method.

        XML-RPC calls are forwarded to a registered function that
        matches the called XML-RPC method name. If no such function
        exists then the call is forwarded to the registered instance,
        if available.

        If the registered instance has a _dispatch method then that
        method will be called with the name of the XML-RPC method,
        its parameters as a tuple
        e.g. instance._dispatch('add',(2,3))

        If the registered instance does not have a _dispatch method
        then the instance will be searched to find a matching method
        and, if found, will be called.

        Methods beginning with an '_' (except _dispatch) are considered
        private and will not be called.
        """
        kwdargs = {}
        func = None

        # check for a _dispatch method
        if (self.instance is not None) and hasattr(self.instance, '_dispatch'):
            return self.instance._dispatch(methodName, params, kwdargs,
                                           auth, client_addr)

        try:
            # check to see if a matching function has been registered
            func = self.funcs[methodName]

        except KeyError:
            if self.instance is not None:
                # call instance method directly
                try:
                    func = SimpleXMLRPCServer.resolve_dotted_attribute(
                        self.instance,
                        methodName,
                        self.allow_dotted_names
                        )
                except AttributeError:
                    pass

        if func is not None:
            return func(*params, **kwdargs)
        else:
            raise Error('method "%s" is not supported' % methodName)


    def do_dispatch(self, methodName, params, auth, client_addr):

        # TODO: combine with my_dispatch ?
        try:
            if self.authDict:
                self.authenticate_client(methodName, params, auth, client_addr)

            # log all method calls, but truncate params to a reasonable size
            # in case a huge parameter(s) was sent
            self.logger.debug("calling method %s(%s)" % (str(methodName),
                                                         str(params)[:500]))
##             response = SimpleXMLRPCServer.SimpleXMLRPCDispatcher._dispatch(self, method, params)
            response = self.my_dispatch(methodName, params, auth, client_addr)
            self.logger.debug("response is: %s" % str(response))
            return response

        except Exception, e:
            self.logger.error("Method %s raised exception: %s" % (str(methodName),
                                                                  str(e)))
            try:
                (type, value, tb) = sys.exc_info()
                tb_str = ("Traceback:\n%s" % '\n'.join(traceback.format_tb(tb)))
                self.logger.error(tb_str)
            except:
                self.logger.error("Traceback information unavailable")
            raise e


    # If we are running on Python < 2.5 then add this method to the otherwise
    # class use the stock version
    if sys.hexversion < 0x02040000:
        _marshaled_dispatch = _hacked_marshaled_dispatch
    #_marshaled_dispatch = _hacked_marshaled_dispatch

    # We override this method so we don't have to block indefinitely on the
    # socket.accept() method.  See SocketServer.py
    def get_request(self):
        while not self.ev_quit.isSet():
            #self.logger.debug("Ready to accept request, socket %s" % (
            #        str(self.socket)))
            inputs = [ self.socket ]
            try:
                (sin, sout, sexp) = select.select(inputs, [], [], self.timeout)

            except KeyboardInterrupt, e:
                raise e

            except select.error, e:
                self.logger.error("select.error: %s" % str(e))
                (code, msg) = e
                # code==4 is interrupted system call.  This typically happens
                # when the process receives a signal.
                if code == 4:
                    raise socketTimeout('select() timed out, system call interrupted')
                raise e
            
            for i in sin:
                if i == self.socket:
                    conn = self.socket.accept()
                    # wierd hack dues to Solaris 10 handling of sockets
                    conn[0].setblocking(1)
                    return conn

            # Normal timeout, nothing to do.  This will be caught by
            # __cmd_loop in remoteObjectServer
            raise socketTimeout('select() timed out')


    def handle_request(self):
        """Handle one request, possibly blocking."""
        try:
            request, client_address = self.get_request()

        except socketTimeout, e:
            raise e

        except socket.error, e:
            self.logger.error("Socket error: %s" % (str(e)))
            #raise e
            # ?? this is what SocketServer does...
            return

        if self.verify_request(request, client_address):
            try:
                self.process_request(request, client_address)

            except socket.error, e:
                self.logger.error("Socket error: %s" % (str(e)))
            except Exception, e:
                self.logger.error("process_request error: %s" % (str(e)))
                try:
                    self.handle_error(request, client_address)
                    self.close_request(request)
                except Exception, e:
                    self.logger.debug("Error in close: %s" % (str(e)))

#
# ------------------ SSL EXTENSIONS ------------------
#
# SSL pieces found in an article "XML-RPC over SSL in Python",
#   by James Gregory of Anchor Shipyard, (circa) 21 September 2004
# Found at this URL, no source license and site looks abandoned:
#
# http://www.anchor.com.au/shipyard/articles/webdevelopment/sslxmlrpc.py
#

class ConnWrapper:
    """
    Base class for implementing the rest of the wrappers in this section.
    Operates by taking a connection argument which is used when 'self' doesn't
    provide the functionality being requested.
    """
    def __init__(self, connection):
        self.connection = connection

    def __getattr__(self, function):
        return getattr(self.connection, function)

class SSLConn2File(ConnWrapper):
    """
    Wrapper for SSL.Connection that makes it look like a file object for use
    with xmlrpclib.
    """
    def __init__(self, connection):
        ConnWrapper.__init__(self, connection)
        self.buf = ''
        self.closed = False

    def flush (self):
        pass

    def close(self):
        self.closed = True

    # Methinks this function should be examined for correctness and
    # optomization...EJ
    #
    def _readline(self, length=None):
        # inspect the internal buffer, if there's a newline there, use that.
        # else, we need to fill the buffer up and do the same thing.
        def bufManip(location):
            """
            Update self.buf as if there were a newline at the offset @location.
            Then return the string up to the newline.
            """
            result = self.buf[0: location + 1]
            self.buf = self.buf[location + 1:]
            return result

        start_time = time.time()

        nl_loc = self.buf.find('\n')
        if nl_loc != -1:
            return bufManip(nl_loc)

        segments = []
        while self.buf.find('\n') == -1:
            newdata = self.connection.recv(4096)
            if len(newdata):
                segments.append(newdata)
                if newdata.find('\n') != -1:
                    self.buf += ''.join(segments)
                    nl_loc = self.buf.find('\n')
                    return bufManip(nl_loc)
            else:
                # if we get to here, it means we weren't able to fetch any
                # more data with newlines (probably EOF). Just return the
                # contents of the internal buffer.
                self.buf += ''.join(segments)
                return self.buf

    def readline(self, length=None):
        try:
            return self._readline(length=length)

        except Exception, e:
            raise Error(e)
        

class SSLConnWrapper(ConnWrapper):
    """
    Proxy class to provide makefile function on SSL Connection objects.
    """
    def __init__(self, connection):
        ConnWrapper.__init__(self, connection)

    def makefile(self, mode, bufsize = 0):
        (_, _) = (mode, bufsize)
        return SSLConn2File(self.connection)

    def shutdown(self, _):
        return self.connection.shutdown()

class SSLWrapper(ConnWrapper):
    """
    Proxy class to inject the accept method to generate the *next* proxy class.
    """
    def __init__(self, connection):
        ConnWrapper.__init__(self, connection)

    def accept(self):
        (conn, whatsit) = self.connection.accept()
        return (SSLConnWrapper(conn), whatsit)

class SSLSocketServer(SocketServer.BaseServer):
    """
    Hack to provide SSL over the existing TCPServer class.
    """
    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 5
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass, cert_file=None):
        """
        Constructor. We're overloading it, even though TCPServer's
        constructor says not to.
        """
        SocketServer.BaseServer.__init__(self, server_address,
                                         RequestHandlerClass)

        # this function should do the authentication checking to see that
        # the client is who they say they are.
        def verify_cb(conn, cert, errnum, depth, ok):
            return ok

        # setup an SSL context.
        context = SSL.Context(SSL.SSLv23_METHOD)
        context.set_verify(SSL.VERIFY_PEER, verify_cb)

        # load up certificate stuff.
        if not cert_file:
            cert_file = os.environ['PEMFILE']
        key_file = cert_file
        context.use_privatekey_file(key_file)
        context.use_certificate_file(cert_file)

        # make the socket
        real_sock = socket.socket(self.address_family, self.socket_type)

        # [Bug #1222790] If possible, set close-on-exec flag; if a
        # method spawns a subprocess, the subprocess shouldn't have
        # the listening socket open.
        if fcntl is not None and hasattr(fcntl, 'FD_CLOEXEC'):
            flags = fcntl.fcntl(real_sock.fileno(), fcntl.F_GETFD)
            flags |= fcntl.FD_CLOEXEC
            fcntl.fcntl(real_sock.fileno(), fcntl.F_SETFD, flags)

        self.socket = SSLWrapper(SSL.Connection(context, real_sock))

        self.server_bind()
        self.server_activate()

    # functions after here are copied directly from TCPServer, just to avoid
    # a pychecker error.
    def server_bind(self):
        if self.allow_reuse_address:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)

    def server_activate(self):
        self.socket.listen(self.request_queue_size)

    def server_close(self):
        self.socket.close()

    def fileno(self):
        return self.socket.fileno()

    def get_request(self):
        return self.socket.accept()

    def close_request(self, request):
        request.close()

#
# ------------------ THREADING EXTENSIONS ------------------
#
class ProcessingMixIn(object):
    """Mix-in class to handle each request in a new thread."""

    def __init__(self, fn=None, threaded=False, daemon=False,
                 threadPool=None):
        if fn:
            self.fn = fn
        else:
            self.fn = self.do_process_request
            
        self.useThread = threaded
        self.daemon_threads = daemon
        self.threadPool = threadPool
        
    def do_process_request(self, request, client_address):
        """Same as in SocketServer.BaseServer but as a thread.

        In addition, exception handling is done here.

        """
        try:
            self.finish_request(request, client_address)
            self.close_request(request)

        except Exception, e:
            self.logger.error("Error handling request: %s" % (
                    str(e)))
            try:
                self.handle_error(request, client_address)
                self.close_request(request)
            except Exception, e:
                self.logger.error("Error handling error handling!: %s" % (
                        str(e)))
                raise e

    def process_request(self, request, client_address):
        """Start a new thread to process the request."""

        if self.useThread:
            if self.threadPool:
                self.logger.debug("Handing off request %s to threadpool." % (
                        str(client_address)))
                # If there is a threadpool with worker tasks, use it
                task = Task.FuncTask2(self.fn, request, client_address)
                task.initialize(self)
                self.threadPool.addTask(task)
            else:
                self.logger.debug("Creating thread to handle request %s." % (
                        str(client_address)))
                # otherwise create a new thread
                t = threading.Thread(target=self.fn,
                                     args=(request, client_address))
                if self.daemon_threads:
                    t.setDaemon(1)
                t.start()
            
        # Default behavior is single-threaded sequential execution
        else:
            self.fn(request, client_address)



#
# ------------------ XML-RPC SERVERS ------------------
#
# These just inherit from the base transport (SocketServer.TCPServer or
# SSLSocketServer) and the base class BaseXMLRPCServer.

# Using the ProcessingMixIn allows the XML-RPC server to handle more than
# one request at a time.
#
class XMLRPCServer(ProcessingMixIn, BaseXMLRPCServer,
                   SocketServer.TCPServer):
    """
    Basic XML-RPC server.
    """

    # Note: cert_file param is just for constructor compatibility with
    # SecureXMLRPCServer--it is ignored
    def __init__(self, host, port, ev_quit=None, timeout=socket_timeout,
                 logger=None, 
                 requestHandler=XMLRPCRequestHandler,
                 logRequests=False, allow_none=True, encoding=None,
                 threaded=False, threadPool=None,
                 authDict=None, cert_file=None):
        
        BaseXMLRPCServer.__init__(self, host, port, ev_quit=ev_quit,
                                  timeout=timeout, logger=logger,
                                  requestHandler=requestHandler,
                                  logRequests=logRequests,
                                  allow_none=allow_none, encoding=encoding,
                                  authDict=authDict)
                                  
        self.ssl_pad = False
        ProcessingMixIn.__init__(self, threaded=threaded, threadPool=threadPool)
        SocketServer.TCPServer.__init__(self, (host, port), requestHandler)

        # Make XML-RPC sockets not block indefinitely
        self.socket.settimeout(timeout)
        
        # [Bug #1222790] If possible, set close-on-exec flag; if a
        # method spawns a subprocess, the subprocess shouldn't have
        # the listening socket open.
        if fcntl is not None and hasattr(fcntl, 'FD_CLOEXEC'):
            flags = fcntl.fcntl(self.fileno(), fcntl.F_GETFD)
            flags |= fcntl.FD_CLOEXEC
            fcntl.fcntl(self.fileno(), fcntl.F_SETFD, flags)


class SecureXMLRPCServer(ProcessingMixIn, BaseXMLRPCServer,
                         SSLSocketServer):
    """
    Basic XML-RPC server over SSL.
    """
    def __init__(self, host, port, ev_quit=None, timeout=socket_timeout,
                 logger=None,
                 requestHandler=XMLRPCRequestHandler,
                 logRequests=False, allow_none=True, encoding=None,
                 threaded=False, threadPool=None,
                 authDict=None, cert_file=None):

        if not SSL:
            raise Error("SSL support or Python wrapper not installed")
        
        BaseXMLRPCServer.__init__(self, host, port, ev_quit=ev_quit,
                                  timeout=timeout, logger=logger,
                                  requestHandler=requestHandler,
                                  logRequests=logRequests,
                                  allow_none=allow_none, encoding=encoding,
                                  authDict=authDict)

        self.ssl_pad = True
        ProcessingMixIn.__init__(self, threaded=threaded, threadPool=threadPool)
        SSLSocketServer.__init__(self, (host, port), requestHandler,
                                 cert_file=cert_file)

        # Make XML-RPC sockets not block indefinitely
        self.socket.settimeout(timeout)
        

#END

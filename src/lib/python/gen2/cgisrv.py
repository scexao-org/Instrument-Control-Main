#!/usr/bin/env python
#
# Simple embedded CGI server
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Dec 10 12:04:25 HST 2010
#]
#
"""
This module implements a simple, embeddable CGI web server.  With it you can
have a CGI-based web interface to your app up in a few minutes.

Example usage:

import cgisrv

    my_data = <some object>
    
    # Create basic object with instance data and methods to be called
    # when CGI requests come in
    cgi_obj = cgisrv.CGIobject(my_data)

    # Create the server
    httpd = cgisrv.CGIserver(cgi_obj)
    
    try:
        httpd.serve_forever()

    except KeyboardInterrupt:
        print "Keyboard interrupt!"

"""

import sys, time, re
import socket
import threading
import StringIO
from SocketServer import BaseServer, ThreadingMixIn
from BaseHTTPServer import HTTPServer
import SimpleHTTPServer
import urlparse, urllib, base64
import traceback
import logging
try:
    from OpenSSL import SSL
    has_ssl = True

except ImportError:
    has_ssl = False

import Task


def urldecode(query):
    d = {}
    a = query.split('&')
    for s in a:
        if s.find('='):
            k, v = map(urllib.unquote, s.split('='))
        if not d.has_key(k):
            d[k] = v
        else:
            if type(d[k]) == list:
                d[k].append(v)
            else:
                d[k] = [d[k], v]
 
    return d


class HTTPError(Exception):
    pass

class NotFoundError(HTTPError):
    pass
    
class AuthError(HTTPError):
    pass
    
class HTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    protocol_version = "HTTP/1.0"

    def do_GET(self):
        """Serve a GET request."""
        buf = self.send_head()
        if buf:
            self.wfile.write(buf)
            self.wfile.flush()

    def do_HEAD(self):
        """Serve a HEAD request."""
        buf = self.send_head()

    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """
        try:
            (hdrs, buf) = self.dispatch(self.path)

        except NotFoundError, e:
            self.send_error(404, str(e))
            return None

        except AuthError, e:
            (hdrs, buf) = ({}, str(e))
            hdrs.setdefault("WWW-Authenticate", 'Basic')
            code = 401

        except Exception, e:
            self.send_error(500, "Internal Error: %s" % str(e))
            return None

        else:
            code = 200

        # Set default headers if not provided
        # TODO: add Content-Encoding?
        hdrs.setdefault("Content-Type", 'text/html')
        hdrs.setdefault("Content-Length", str(len(buf)))
        hdrs.setdefault("Last-Modified", self.date_time_string(time.time()))

        self.send_response(code)
        for header, val in hdrs.items():
            self.send_header(header, val)
        self.end_headers()

        return buf


    def authenticate_client(self):
        # TODO: it would be nice to return a 401 UNAUTHORIZED 
        # error if authentication fails
        
        auth = self.headers.get("authorization", None)
        logger = self.server.logger
        auth_verify = self.server.auth_verify

        if auth:
            try:
                method, auth = auth.split()
                if method.lower() == 'basic':
                    auth = base64.decodestring(auth)
                    username, password = auth.split(':')
                    #logger.debug("username: '%s', password: '%s'" % (
                    #    username, password))
                else:
                    logger.error("unsupported auth method: '%s'" % method)
                    auth = None
            except IndexError:
                logger.error("unrecognized auth cred: '%s'" % auth)
                auth = None

        if not auth:
            logger.error("No authentication credentials passed")
            raise AuthError("Service requires authentication and no credentials passed")

        if not auth_verify(username, password):
            errmsg = ("Authentication failed for username=%s" % username)
            logger.error(errmsg)
            raise AuthError(errmsg)
            
        logger.debug("Authorized client '%s'" % (username))


    def dispatch(self, path):
        # First, authenticate client if we were supplied with an authentication
        # dictionary.
        logger = self.server.logger

        logger.debug("authenticating %s" % (path))
        if self.server.auth_verify:
            self.authenticate_client()

        logger.debug("dispatching %s" % (path))
        return self.server.dispatch_cgi(path)


class BaseCGIserver(object):

    def __init__(self, cgi_obj, host='', port=9000, logger=None,
                 authVerifyFn=None, hostVerifyFn=None, **kwdargs):
        """Constructor for the server.  Takes an object whose methods will
        be called for the CGI calls and (optionally) a host name to bind to
        (leave default for all interfaces), a port number to listen on, and
        a handler class for requests.
        """

        self.cgi = cgi_obj
        if host:
            self.cgi.host = host
        else:
            self.cgi.host = socket.getfqdn()
        self.cgi.port = port
        # self.proto set by our subclass, depending on mixin
        self.cgi.proto = self.proto

        # Did user supply a logger?
        if not logger:
            logger = logging.getLogger('BaseCGIserver')
        self.logger = logger

        # Did user supply an authorization function?
        self.auth_verify = authVerifyFn
        
        # Did user supply a host verify fn?
        self.host_verify = hostVerifyFn
        

    def verify_request(self, request, client_address):
        """Verify the request.  Overridding a method in SocketServer.

        Return True if we should proceed with this request.

        """
        #possible host-based authentication protection
        ip, port = client_address
        self.logger.debug("caller ip: %s:%d" % (ip, port))

        if self.host_verify:
            return self.host_verify(ip, port)
         
        return True


    def wrap(self, content):
        """This wraps any HTML code generated by the called function.
        It should ensure that the code is everything necessary in the body
        if the HTML document returned.
        """
        
        # If content is a 2-tuple, then assume that first element
        # is a dict containing the headers and the second is the content
        # as a buffer
        if isinstance(content, tuple) and (len(tuple) == 2):
            return content

        # Otherwise assume return value is HTML code to be wrapped
        wrapper = "<body>%s</body>"
        buf = wrapper % str(content)
        hdrs = {}
        return (hdrs, buf)
    

    def parse_path(self, path):
        """Parses the path passed by the browser into a tuple of a method
        name, arguments and keyword arguments.

        The first element of the path is considered the method name.
        Subsequent arguments are considered positional parameters and any
        query elements are parsed into keyword arguments.
        """

        tup = urlparse.urlparse(path)
        print tup
        
        # Strip leading and trailing /
        path = tup.path.strip('/')

        # Construct method name from path
        path_l = path.split('/')
        name = path_l[0]
        args = path_l[1:]

        # Do any name mangling to make sure we get a valid method name
        name = name.replace('.', '_')
        
        # handle params (is there something in Python stdlib to do this?)
        kwdargs = {}
        if tup.query:
            kwdargs = urldecode(tup.query)
##             for pair in tup.query.split('&'):
##                 try:
##                     (var, val) = pair.split('=')
##                     kwdargs[var] = val
                    
##                 except ValueError:
##                     raise Exception("Bad key/value pair format: %s" % pair)
            
        return (name, args, kwdargs)


    def dispatch_cgi(self, path):
        """This method is called back from the handler class to dispatch
        the CGI.  You can overload it to do custom dispatching.  Otherwise
        it will attempt to call the corresponding methods in your CGI object
        and return 404s if the method is not found.
        """

        self.logger.debug("path=%s" % (path))
        method_name, args, kwdargs = self.parse_path(path)
        self.logger.debug("method=%s args=%s kwdargs=%s" % (
            method_name, str(args), str(kwdargs)))

        print self.cgi
        self.cgi.path = path

        if not method_name:
            method_name = 'default'

        
        try:
            method = getattr(self.cgi, method_name)

            if not callable(method):
                raise NotFoundError("Method '%s' not callable" % method_name)

        except AttributeError, e:
            # Try to call the CGI object's not_found() method
            if not hasattr(self.cgi, 'not_found'):
                raise NotFoundError("Method '%s' not found" % method_name)

            args.insert(0, method_name)
            return self.wrap(self.cgi.not_found(*args, **kwdargs))

        try:
            return self.wrap(method(*args, **kwdargs))

        except Exception, e:
            # Try to call the CGI object's error() method
            if not hasattr(self.cgi, 'error'):
                raise e

            tb_info = sys.exc_info()
            args.insert(0, method_name)
            args.insert(0, tb_info)
            return self.wrap(self.cgi.error(*args, **kwdargs))


    def serveit(self):
        self.serve_forever()


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
                # If there is a threadpool with worker tasks, use it
                self.logger.debug("adding %s to threadpool" % (
                        str(client_address)))
                task = Task.FuncTask2(self.fn, request, client_address)
                task.initialize(self)
                self.threadPool.addTask(task)

            else:
                # otherwise create a new thread
                self.logger.debug("creating new thread for request %s" % (
                        str(client_address)))
                t = threading.Thread(target=self.fn,
                                     args=(request, client_address))
                if self.daemon_threads:
                    t.setDaemon(1)
                t.start()
            
        # Default behavior is single-threaded sequential execution
        else:
            print "handling request %s" % (str(client_address))
            self.fn(request, client_address)


class CGIserver(ProcessingMixIn, BaseCGIserver, HTTPServer):
   
    def __init__(self, cgi_obj, host='', port=9000, logger=None,
                 authVerifyFn=None, hostVerifyFn=None,
                 handlerClass=HTTPRequestHandler,
                 threaded=False, threadPool=None):

        self.proto = 'http'
        BaseCGIserver.__init__(self, cgi_obj, host=host, port=port,
                               logger=logger,
                               authVerifyFn=authVerifyFn,
                               hostVerifyFn=hostVerifyFn)
        HTTPServer.__init__(self, (host, port), handlerClass)
        ProcessingMixIn.__init__(self, threaded=threaded,
                                 threadPool=threadPool)


if has_ssl:
    class SecureHTTPRequestHandler(HTTPRequestHandler):

        # Overrides a method in SocketServer.StreamRequestHandler
        def setup(self):
            self.connection = self.request
            self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
            self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)


    class SecureHTTPServer(HTTPServer):

        def __init__(self, server_address, HandlerClass, fpem=None):
            BaseServer.__init__(self, server_address, HandlerClass)
            ctx = SSL.Context(SSL.SSLv23_METHOD)
            ctx.use_privatekey_file (fpem)
            ctx.use_certificate_file(fpem)
            self.socket = SSL.Connection(ctx, socket.socket(self.address_family,
                                                            self.socket_type))
            self.server_bind()
            self.server_activate()


    class SecureCGIserver(ProcessingMixIn, BaseCGIserver, SecureHTTPServer):
   
        def __init__(self, cgi_obj, host='', port=9000, logger=None,
                     authVerifyFn=None, hostVerifyFn=None,
                     handlerClass=SecureHTTPRequestHandler,
                     fpem='none', threaded=False, threadPool=None):
            """Constructor for the server.  Takes an object whose methods will
            be called for the CGI calls and (optionally) a host name to bind to
            (leave default for all interfaces), a port number to listen on, and
            a handler class for requests.
            """

            self.proto = 'https'
            BaseCGIserver.__init__(self, cgi_obj, host=host, port=port,
                                   logger=logger,
                                   authVerifyFn=authVerifyFn,
                                   hostVerifyFn=hostVerifyFn)
            SecureHTTPServer.__init__(self, (host, port), handlerClass,
                                      fpem=fpem)
            ProcessingMixIn.__init__(self, threaded=threaded, threadPool=threadPool)


class CGIobject(object):
    """Example CGI object.  Methods will be called as CGI methods.
    Can subclass this or make your own.
    """

    def __init__(self, static_data):
        """Add any parameters that you want to store in the object."""
        self.data = static_data
        self.count = 0
        self.path = ''
    
    def test(self, *args, **kwdargs):
        self.count += 1
        return "test: (%d) path=%s args=%s  kwdargs=%s" % (self.count,
                                                           self.path,
                                                           str(args),
                                                           str(kwdargs))
    
    def default(self, *args, **kwdargs):
        """This method will be called if no method is specified.
        """
        return "default: args=%s  kwdargs=%s" % (str(args), str(kwdargs))


    def not_found(self, *args, **kwdargs):
        """This method will be called if there is a bad method specified.
        """
        # Method name is passed as the first argument
        method_name = args[0]
        raise NotFoundError("Method '%s' not found" % method_name)


    def error(self, *args, **kwdargs):
        """This method will be called if there is an exception raised
        calling your CGI methods.  By default it produces a readable, but
        minimal traceback dump.
        """
        tb_info = args[0]
        method_name = args[1]

        # Return debugging traceback
        (type, value, tb) = tb_info
        return "<pre>Exception %s: %s\nTraceback:\n%s</pre>" % (
            str(type), str(value), "".join(traceback.format_tb(tb)) )
    
        
def main(options, args):

    # Create basic object with instance data and methods to be called
    # when CGI requests come in
    cgi_obj = CGIobject('static data blah blah')

    auth_verify = None
    if options.auth_users:
        authDict = {}
        for userpass in options.auth_users.split(','):
            auth = userpass.split(':')
            authDict[auth[0]] = auth[1]

        def auth(username, password):
            return authDict.has_key(username) and authDict[username] == password

        auth_verify = auth

    host_verify = None
    if options.auth_hosts:
        hostList = options.auth_hosts.split(',')
        
        def auth(ip, port):
            return ip in hostList

        host_verify = auth

    # Create the server
    kwdargs = { 'host': options.host, 'port': options.port,
                'authVerifyFn': auth_verify, 'hostVerifyFn': host_verify,
                'threaded': True }

    if options.cert_file:
        ServerClass = SecureCGIserver
        kwdargs['fpem'] = options.cert_file
        proto = 'HTTPS'
    else:
        ServerClass = CGIserver
        proto = 'HTTP'

    print kwdargs
    httpd = ServerClass(cgi_obj, **kwdargs)

    sa = httpd.socket.getsockname()
    print "Serving %s on %s:%d ..." % (proto, sa[0], sa[1])
    try:
       try:
          httpd.serveit()

       except KeyboardInterrupt:
          print "Keyboard interrupt!"
          sys.exit(0)

    finally:
        print "Stopping %s service..." % (proto)
        httpd.socket.close()
          

if __name__ == '__main__':

    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--auth_users", dest="auth_users",
                      help="User authorization; arg should be user:passwd")
    optprs.add_option("--auth_hosts", dest="auth_hosts",
                      help="Host authorization; arg should be list of hosts")
    optprs.add_option("--cert", dest="cert_file",
                      help="Path to key/certificate file")
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--host", dest="host",
                      default='',
                      help="Host to serve on (default: all interfaces)")
    optprs.add_option("--numthreads", dest="numthreads", type="int",
                      default=30,
                      help="Use NUM threads", metavar="NUM")
    optprs.add_option("--port", dest="port", type="int", default=None,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
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

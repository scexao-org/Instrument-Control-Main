#!/usr/bin/env python
#
# g2web.py -- web interface to various Gen2 services
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Nov 12 10:32:58 HST 2010
#]
#
"""
This is a web browser-based GUI for Gen2.
It allows one to control and monitor the status of the various running
processes in Gen2.

Typical use (solo configuration, default port 20000):

    $ cd $GEN2HOME
    $ web/g2web.py --config=solo --detach
    
"""

import sys, os, signal, time
import threading
import traceback

# --- TEMP, until we figure out configuration issues ---
thisDir = os.path.split(sys.modules[__name__].__file__)[0]
moduleHome = '%s/..' % (thisDir)
sys.path.insert(1, moduleHome)
# ------------------------------------------------------
import Bunch
import Task
import remoteObjects as ro
import ssdlog
import cgisrv
import Gen2.BootManager as BootManager

LOG_FORMAT = '%(asctime)s %(levelno)3.3d S:%(filename)s,L:%(lineno)d,FN:%(funcName)s,TID:%(thread)d  %(message)s'

version = "20101020.0"

pluginconfpfx = 'Gen2.web.plugins'

css = """
  <STYLE type="text/css">
.header {border-width: 1; border: solid; background-color: #AAAAAA}
.header2 {background-color: #AAAAAA}
.even {border-width: 1; border: solid; background-color: #99FF66}
.odd  {border-width: 1; border: solid; background-color: #99CC66}
.warn  {border-width: 1; border: solid; background-color: #FF9966}
.error {border-width: 1; border: solid; background-color: #CC0000; color: #FFFF99}
.down  {border-width: 1; border: solid; background-color: #DDDDDD}
.periodic  {border-width: 1; border: solid; background-color: #99CCFF}
.btn  {border-width: 0; background-color: #CCFF99;
       text-decoration: none; color: black; padding: 2px 4px; }
.btn2 {border-width: 1px; border: groove; background-color: #CCFF99;
       text-decoration: none; color: black; padding: 2px 4px; }
  </STYLE>
"""

class g2_cgi(cgisrv.CGIobject):
    """This is the main application object, which contains the methods
    that will be called from the CGI interface.
    """

    def __init__(self, logger, cfg):
            
        super(g2_cgi, self).__init__(None)

        self.logger = logger
        self.cfg = cfg

        # Dicts containing all the plugins that have been loaded
        self._module = {}
        self._plugin = {}

    
    def loadPlugin(self, moduleName):
        try:
            self.logger.info("Loading plugin '%s'..." % moduleName)
            if self._module.has_key(moduleName):
                module = reload(self._module[moduleName])

            else:
                module = my_import(pluginconfpfx + '.' + moduleName)
            
            method = getattr(module, moduleName)

            # Prepare subconfiguration for module
            subcfg = self.cfg.setdefault(moduleName, Bunch.Bunch())
            subcfg.css = css
            subcfg.base_url = self._my_base_url()
            subcfg.my_url = self._my_base_url() + '/plugin/' + moduleName

            self._plugin[moduleName] = method(self.logger, subcfg)
            self._module[moduleName] = module
            
            return self.page("Plugin '%s' loaded." % moduleName)
        
        except Exception, e:
            self.logger.error("Failed to load plugin '%s': %s" % (
                moduleName, str(e)))
            # TODO: log the stack trace
            return self.page("Can't load plugin '%s': %s" % (
                moduleName, str(e)))
        

    def _my_base_url(self):
        return '%s://%s:%d' % (self.proto, self.host, self.port)

    def _my_url(self):
        return '%s%s' % (self._my_base_url(), self.path)

    # This function crafts a basic html wrapper 
    def page(self, s):
        page = """
<html>
<head>
</head>
<body>
%s
<p>
%s
</body>
</html>
""" % (s, time.strftime("page rendered at %Y-%m-%d %H:%M:%S"))
        return page

    def errorpage(self, msg):
        return self.page("Error retrieving page: %s" % msg)
        
    def plugin(self, *args, **kwdargs):
        """Request for a module.
        """
        path = self.cfg.docroot + '/' + ('/'.join(args).lstrip('/'))

        try:
            modname = args[0]
            methodname = args[1]
        except IndexError:
            return self.errorpage("Page '%s' not found" % path)

        try:
            plugin = self._plugin[modname]
        except KeyError:
            return self.errorpage("Page '%s' not found" % path)

        try:
            method = getattr(plugin, methodname)
        except AttributeError:
            return self.errorpage("Page '%s' not found" % path)

        try:
            args = args[2:]
            page = method(*args, **kwdargs)

        except Exception, e:
            self.logger.error(str(e))
            page = self.errorpage("Error loading page '%s': %s" % (
                path, str(e)))

        return page
    

    def doc(self, *args):
        """Standard web serving of documents.
        """

        def filt_elt(elt):
            elt = elt.strip()
            if elt[0] in ('.', '/'):
                return False
            return True

        # Construct the path to the requested document
        filt_args = filter(filt_elt, args)
        subpath = '/' + ('/'.join(filt_args).lstrip('/'))
        subpath = os.path.normpath(subpath)

        path = self.cfg.docroot + subpath
        if not os.path.exists(path):
            self.logger.error("Path does not exist: %s" % path)
            return self.errorpage("Page '%s' not found" % subpath)

        if os.path.isdir(path):
            # different behavior for directories
            # TODO: provide support for indexing?
            self.logger.error("Path refers to a directory: %s" % path)
            return self.errorpage("Page '%s' not found" % subpath)

        # Open and return the file
        try:
            in_f = open(path, 'r')
            page = in_f.read()
            in_f.close()

        except IOError, e:
            page = self.errorpage("Error loading page '%s': %s" % (
                subpath, str(e)))

        return page
    

    def default(self, *args, **kwdargs):
        """This method will be called if no method is specified.
        """
        return self.doc('index.html')
    
        
    def not_found(self, *args, **kwdargs):
        """This method will be called if there is a bad method specified.
        """
        # Method name is passed as the first argument
        #method_name = args[0]
        #raise cgisrv.NotFoundError("Method '%s' not found" % method_name)
        return self.doc(*args)


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
    
        
def my_import(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


def main(options, args):
    
    # Create top level logger.
    svcname = ('g2web_%d' % (options.port))
    logger = ssdlog.make_logger(svcname, options)

    httpd = None

    # Write out our pid
    if options.pidfile:
        pidfile = options.pidfile
    else:
        pidfile = ('/tmp/g2web_%d.pid' % (options.port))

    if options.kill:
        try:
            try:
                pid_f = open(pidfile, 'r')
                pid = int(pid_f.read().strip())
                pid_f.close()

                logger.info("Killing %d..." % (pid))
                os.kill(pid, signal.SIGKILL)
                logger.info("Killed.")

            except IOError, e:
                logger.error("Cannot read pid file (%s): %s" % (
                    pidfile, str(e)))
                sys.exit(1)

            except OSError, e:
                logger.error("Error killing pid (%d): %s" % (
                    pid, str(e)))
                sys.exit(1)
                
        finally:
            sys.exit(0)

    ro.init()
        
    # Global termination flag
    ev_quit = threading.Event()
    
    def quit():
        logger.info("Shutting down g2web CGI service...")
        if httpd:
            # Httpd currently uses callbacks from monitors threadpool
            pass

    def SigHandler(signum, frame):
        """Signal handler for all unexpected conditions."""
        logger.error('Received signal %d' % signum)
        quit()
        ev_quit.set()

    # Set signal handler for signals
    #signal.signal(signal.SIGINT, SigHandler)
    signal.signal(signal.SIGTERM, SigHandler)

    threadPool = Task.ThreadPool(logger=logger,
                                 ev_quit=ev_quit,
                                 numthreads=options.numthreads)
        
    # Create the boot manager
    bm = BootManager.BootManager(logger, confpfx=options.confpfx)
    # Try to load the specified config
    bm.loadConfig(options.configname)

    cfg = Bunch.Bunch()
    cfg.docroot = options.docroot
    cfg.bm = Bunch.Bunch(bm=bm, configname=options.configname)
    cfg.dsp = Bunch.Bunch(bm=bm)
        
    def serve(options):

        # Set up custom authentication function for user/passwd based
        # basic HTTP authentication, if requested
        auth_verify = None
        if options.auth_users:
            # Format of auth_users is user1:pass1,user2:pass2,...
            authDict = {}
            for userpass in options.auth_users.split(','):
                auth = userpass.split(':')
                authDict[auth[0]] = auth[1]

            # custom function to return True/False authentication by looking
            # up username and password in a dictionary
            def auth(username, password):
                return authDict.has_key(username) and (
                    authDict[username] == password)

            auth_verify = auth

        # Set up custom authentication function for host ip based
        # authentication, if requested
        host_verify = None
        if options.auth_hosts:
            # Format of auth_hosts is ip1,ip2,ip3...
            hostList = options.auth_hosts.split(',')

            # custom function to return True/False authentication by looking
            # up username and password in a dictionary
            def auth(ip, port):
                return ip in hostList

            host_verify = auth

        # Keyword args to be passed to the server class constructor
        kwdargs = { 'host': options.host, 'port': options.port,
                    'logger': logger,
                    'authVerifyFn': auth_verify, 'hostVerifyFn': host_verify,
                    'threaded': True, 'threadPool': threadPool }

        # If --cert was passed then user wants a secure (SSL/HTTPS) server,
        # otherwise a normal, unsecured HTTP one
        if options.cert_file:
            ServerClass = cgisrv.SecureCGIserver
            kwdargs['fpem'] = options.cert_file
            proto = 'HTTPS'
        else:
            ServerClass = cgisrv.CGIserver
            proto = 'HTTP'

        logger.info("Starting g2web CGI service...")
        try:
            # Create basic object with instance data and methods to be called
            # when CGI requests come in
            cgi_obj = g2_cgi(logger, cfg)

            # Start the threadPool
            threadPool.startall(wait=True)
            
            # Create the server
            httpd = ServerClass(cgi_obj, **kwdargs)
            
            sa = httpd.socket.getsockname()
            logger.info("Serving %s on %s:%d; ^C to quit..." % (
                proto, sa[0], sa[1]))

            # Load plugins specified on the command line
            for plugin in options.plugins.split(','):
                cgi_obj.loadPlugin(plugin)
                
            try:
                httpd.serveit()

            except KeyboardInterrupt:
                logger.error("Caught keyboard interrupt!")
            
        finally:
            quit()
            logger.info("Stopping %s service..." % (proto))
        
    if options.detach:
        import myproc
        
        print "Detaching from this process..."
        sys.stdout.flush()
        try:
            try:
                logfile = ('/tmp/%s.log' % svcname)
                child = myproc.myproc(serve, args=[options],
                                      pidfile=pidfile, detach=True,
                                      stdout=logfile,
                                      stderr=logfile)
                child.wait()

            except Exception, e:
                print "Error detaching process: %s" % (str(e))

            # TODO: check status of process and report error if necessary
        finally:
            pass
            #sys.exit(0)

    else:
        serve(options)
        
    

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
    optprs.add_option("--config", dest="configname", default=None,
                      metavar="NAME",
                      help="Use configuration with name=NAME for setup")
    optprs.add_option("--docroot", dest="docroot", default='.',
                      metavar="DIR",
                      help="Use DIR for the default document root")
    optprs.add_option("--confpfx", dest="confpfx", default='cfg.bm.',
                      metavar="PACKAGE",
                      help="Use python package PACKAGE for loading configs")
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--detach", dest="detach", default=False,
                      action="store_true",
                      help="Detach from terminal and run as a daemon")
    optprs.add_option("--host", dest="host",
                      default='',
                      help="Host to serve on (default: all interfaces)")
    optprs.add_option("-k", "--kill", dest="kill", default=False,
                      action="store_true",
                      help="Kill running instance of g2web")
    optprs.add_option("-m", "--monitor", dest="monitor", default='monitor',
                      metavar="NAME",
                      help="Subscribe to feed from monitor service NAME")
    optprs.add_option("--numthreads", dest="numthreads", type="int",
                      default=30,
                      help="Use NUM threads", metavar="NUM")
    optprs.add_option("--pidfile", dest="pidfile", metavar="FILE",
                      help="Write process pid to FILE")
    optprs.add_option("-P", "--plugins", dest="plugins", default='',
                      help="Comma-separated list of web plugins to load")
    optprs.add_option("--port", dest="port", type="int", default=20000,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("-s", "--showconfigs", dest="showconfigs", default=False,
                      action="store_true",
                      help="Show available configurations")
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

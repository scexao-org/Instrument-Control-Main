#!/usr/bin/env python2.5
#
# ltcs-remote.py -- Remote service for Subaru LTCS reporting.
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon May  4 11:40:28 HST 2009
#]
"""
Remote service for Subaru Laser Traffic Control System reporting.

This program implements a remoteObjects service for writing a file.
It runs _outside_ the Subaru firewall.  The ltcs.py program running
somewhere inside the firewall makes calls to the putFile() method.
The parameter to this method is a base64-encoded buffer, which is
decoded and written to a file.

SSL encryption + http authentication are used to secure the communication.

Example invocation:

./ltcs-remote.py --cert=/path/to/server.pem --log=ltcs-remote.log \
       --dst=/path/to/ltcs.html --port=9190  --auth=user:passwd

for better security, set the environment variable LTCSAUTH to the
authentication username:password before you invoke the program,
and omit the --auth parameter from the command line.
"""
# remove once we're certified on python 2.6
from __future__ import with_statement

import sys, os, time
import traceback
import threading

import ssdlog
import remoteObjects as ro
import myproc
import cgisrv


class ltcs_cgi(cgisrv.CGIobject):
    """This is the main application object, which contains the methods
    that will be called from the CGI interface.
    """
    
    def ltcs_html(self, *args, **kwdargs):
        return self.data.get()
    
    def default(self, *args, **kwdargs):
        """This method will be called if no method is specified.
        """
        return self.ltcs_html(args, kwdargs)
    
    def not_found(self, *args, **kwdargs):
        """This method will be called if there is a bad method specified.
        """
        # Method name is passed as the first argument
        method_name = args[0]
        raise cgisrv.NotFoundError("Method '%s' not found" % method_name)

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
                                                    
                                    
class LTCSRemoteService(ro.remoteObjectServer):
    """
    Class implementing one or more remotely-invocable methods.
    """

    def __init__(self, options, logger, usethread=False):

        self.dstfile = options.dstfile

        self.lock = threading.RLock()

        # Get service name and HTTP authorization parameters
        svcname = options.svcname
        auth = None
        if options.auth:
            auth = options.auth.split(':')
        elif os.environ.has_key('LTCSAUTH'):
            auth = os.environ['LTCSAUTH'].split(':')

        authDict = {}
        if auth:
            authDict[auth[0]] = auth[1]
        
        # Superclass constructor
        ro.remoteObjectServer.__init__(self, svcname=svcname,
                                       #logger=logger,
                                       usethread=usethread,
                                       port=options.roport,
                                       authDict=authDict,
                                       secure=(options.cert_file != None),
                                       cert_file=options.cert_file)
        self.data = "No data from LTCS reporter"
        self.logger = logger
        
        
    def putFile(self, encodedBuffer):
        """
        A remote method that takes a base64-encoded buffer, decodes it,
        and writes it to a file (self.dstfile).  Returns True on success,
        otherwise logs an error and returns False.
        """

        try:
            data = ro.binary_decode(encodedBuffer)

            with self.lock:
                self.data = data
                self.logger.info("Received update: %s" % (
                    time.ctime(time.time())))

            #f_out = open(self.dstfile, 'w')

            #f_out.write(data)
            #f_out.close()
            #self.logger.info("Wrote file '%s'" % self.dstfile)

            return True

        except Exception, e:
            self.logger.error("Error writing file: %s" % str(e))

        return False


    def get(self):

        with self.lock:
            return self.data

    
def status(options):
    if not options.pidfile:
        print "Please specify a --pidfile"
        sys.exit(1)
        
    print "Looking for LTCS process..."
    try:
        child = myproc.getproc(pidfile=options.pidfile)
        print child.status()

    except myproc.myprocError, e:
        print "Error getting PID for LTCS process; please check manually"

    sys.exit(0)


def stop(options):
    if not options.pidfile:
        print "Please specify a --pidfile"
        sys.exit(1)
        
    print "Looking for LTCS process..."
    try:
        child = myproc.getproc(pidfile=options.pidfile)
        if child.status != 'exited':
            print "Trying to stop LTCS process..."
            child.kill()
            sys.exit(0)
        else:
            print "No LTCS process found."
            sys.exit(1)
    except myproc.myprocError, e:
        print "Error getting PID for LTCS process; please check manually"

    sys.exit(0)
    

def start(options):
    # Create logger 
    logger = ssdlog.make_logger('ltcs-remote', options)

    # Initialize remote objects service, necessary before any
    ro.init()

    svc = LTCSRemoteService(options, logger, usethread=True)
    
<<<<<<< .mine
    # Create basic object with instance data and methods to be called
    # when CGI requests come in
    cgi_obj = cgisrv.CGIobject(svc)

    # Create the server
    httpd = cgisrv.CGIserver(cgi_obj, port=options.port, logger=logger)

=======
    # Create basic object with instance data and methods to be called
    # when CGI requests come in
    if options.port:
        cgi_obj = ltcs_cgi(svc)

        # Create the server
        httpd = cgisrv.CGIserver(cgi_obj, port=options.port, logger=logger)

>>>>>>> .r6031
    logger.info("Starting LTCS remote service '%s'..." % options.svcname)
    svc.ro_start(wait=True)
    try:
        try:
            # Start remote objects server.  Since usethread=False
            # in the constructor, we will block here until server
            # exits.
            httpd.serve_forever()

        except KeyboardInterrupt:
            logger.error("Received keyboard interrupt!")

    finally:
        logger.info("Stopping LTCS remote service...")
        svc.ro_stop(wait=True)


# ------- Main program -------

def main(options, args):

    cmd = args[0]
    
    # Stop daemon?
    if cmd == 'stop':
        return stop(options)

    # Check status?
    elif cmd == 'status':
        return status(options)

    # Check status?
    elif cmd == 'start':
        if options.detach:
            try:
                null_f = open('/dev/null', 'w')

            except IOError, e:
                sys.stderr.write("Could not open /dev/null: %s" % (str(e)))
                sys.exit(1)

            print "Detaching from this process..."
            child = myproc.myproc(start, args=[options],
                                  pidfile=options.pidfile, detach=True,
                                  stdout=null_f, stderr=null_f)

            null_f.close()
            sys.exit(0)

        return start(options)

    else:
        print "I don't know what '%s' means; invoke with --help to see usage" % (
            cmd)
        sys.exit(1)


if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options] start|stop|status"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--auth", dest="auth",
                      help="Use authorization; arg should be user:passwd")
    optprs.add_option("--cert", dest="cert_file",
                      help="Path to key/certificate file")
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--detach", dest="detach", default=False,
                      action="store_true",
                      help="Run process as a detached daemon")
    optprs.add_option("--dst", dest="dstfile",
                      default='./ltcs.html',
                      help="Path to destination file")
    optprs.add_option("--pidfile", dest="pidfile", metavar="FILE",
                      help="Write process pid to FILE")
    optprs.add_option("--roport", dest="roport", type="int",
                      help="Register for remoteObjects using PORT", metavar="PORT")
    optprs.add_option("--port", dest="port", type="int", default=8000,
                      help="Register for web service using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--svcname", dest="svcname",
                      default='ltcs-remote', metavar="NAME",
                      help="Register using service NAME")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    if len(args) != 1:
        optprs.error("incorrect number of arguments")

    elif not (args[0] in ('start', 'stop', 'status')):
        optprs.error("unknown command: '%s'" % args[0])

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


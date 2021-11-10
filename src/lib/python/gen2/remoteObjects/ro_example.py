#!/usr/bin/env python
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Tue Jul 20 14:49:38 HST 2010
#]
""" 
Simple example of a remoteObjects client/service.

To run example:

  on SERVER host, in one xterm, run
   ./remoteObjectNameSvc.py --hosts=serverhost,clienthost

  on CLIENT host, in one xterm, run
   ./remoteObjectNameSvc.py --hosts=clienthost,serverhost

  on SERVER host, in another xterm, run
   ./ro_example.py --server

  on CLIENT host, in another xterm, run
   ./ro_example.py 

Using HTTP authentication:
   (server) ./ro_example.py --server --auth=bob:foo
   (client) ./ro_example.py --auth=bob:foo

Using SSL encryption:
   (server) ./ro_example.py --server --secure --cert=/path/to/server.pem
   (client) ./ro_example.py --secure

Using SSL encryption + authentication:
   (server) ./ro_example.py --server --auth=bob:foo \
                            --secure --cert=/path/to/server.pem
   (client) ./ro_example.py --secure --auth=bob:foo

"""
import sys, time
import remoteObjects as ro


class MyRemoteService(ro.remoteObjectServer):
    """
    Class implementing one or more remotely-invocable methods.
    """

    def __init__(self, svcname, usethread=False, secure=False,
                 default_auth=False, authDict=None, cert_file=None):

        self.count = 0
        
        # Superclass constructor
        ro.remoteObjectServer.__init__(self, svcname=svcname,
                                       usethread=usethread,
                                       default_auth=default_auth,
                                       authDict=authDict, secure=secure,
                                       cert_file=cert_file)

    def _dispatch(self, methodName, params, kwdargs, auth, client_addr):
        print "calling %s%s auth=%s client=%s" % (methodName, str(params),
                                                  str(auth), str(client_addr))
        method = getattr(self, methodName)
        return method(*params, **kwdargs)
    
    
    def search(self, ra, dec, radius, mag):
        self.count += 1
        print "(%5d) ra: %f  dec: %f  radius: %f  mag: %f" % \
              (self.count, ra, dec, radius, mag)

        # Make up some simple result to show we got and
        # manipulated parameters
        res = (ra+2.0, dec+2.0)

        return res

# ------- Main program -------

def main(options, args):

    # Initialize remote objects service, necessary before any
    ro.init()

    svcname = options.svcname
    auth = None
    if options.auth:
        auth = options.auth.split(':')
    
    if options.server:
        authDict = {}
        if auth:
            authDict[auth[0]] = auth[1]
        
        print "Starting '%s' service..." % svcname
        svc = MyRemoteService(svcname, usethread=False, authDict=authDict,
                              secure=options.secure, cert_file=options.cert,
                              default_auth=False)

        try:
            # Start remote objects server.  Since usethread=False
            # in the constructor, we will block here until server
            # exits.
            svc.ro_start()

        except KeyboardInterrupt:
            print "Shutting down '%s' ..." % svcname

    else:
        # Create proxy object for service
        svc = ro.remoteObjectProxy(svcname, auth=auth, secure=options.secure)

        try:
            i = options.count
            while i > 0:
                # Call remote method on service
                try:
                    res = svc.search(1.0, 2.0, 3.0, 4.0)
                    print "(%5d)  res=%s" % (i, str(res))
                    
                except ro.remoteObjectError, e:
                    print "Call error: %s" % (str(e))

                i -= 1
                if i > 0:
                    time.sleep(options.interval)

        except KeyboardInterrupt:
            print "Keyboard interrupt received!"
            

if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage, version=('%%prog'))
    
    parser.add_option("--auth", dest="auth",
                      help="Use authorization; arg should be user:passwd")
    parser.add_option("--cert", dest="cert",
                      help="Path to key/certificate file")
    parser.add_option("--count", dest="count", type="int",
                      default=1,
                      help="Make NUM calls", metavar="NUM")
    parser.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    parser.add_option("--interval", dest="interval", type="float",
                      default=1.0,
                      help="Wait VAL seconds between calls",
                      metavar="VAL")
    parser.add_option("--port", dest="port", type="int",
                      help="Register using PORT", metavar="PORT")
    parser.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    parser.add_option("--secure", dest="secure", action="store_true",
                      default=False,
                      help="Use SSL encryption")
    parser.add_option("--server", dest="server", action="store_true",
                      default=False,
                      help="Run as a server")
    parser.add_option("--svcname", dest="svcname",
                      default='ro_example',
                      help="Register using service NAME", metavar="NAME")

    (options, args) = parser.parse_args(sys.argv[1:])

    if len(args) != 0:
        parser.error("incorrect number of arguments")

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


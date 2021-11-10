#!/usr/bin/env python
#
# AgSim.py -- AG camera simulator
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri May  6 13:08:26 HST 2011
#]
#
#
import sys, time
import traceback

import Ag
import SOSS.SOSSrpc as SOSSrpc
import remoteObjects as ro
import logging, ssdlog
import pyfits
import Bunch
import remoteObjects as ro

# Version/release number
version = "0.10"


defaultServiceName = 'fitsview'

class DisplayFITS_client(object):
    """This class implements a simple remoteObject-based fits image receiver.
    Two methods are served: display_fitsfile() and display_fitsbuf().

    Usage as client--sending buffer:
      ...
      from fitsview import DisplayFITS_client
      ...

        try:
            fits_f = pyfits.open(fitsfile, 'readonly')
            data = fits_f[0].data
            fits_f.close()
            
        except IOError, e:
            print "Can't open input file '%s': %s" % (fitsfile, str(e))
            sys.exit(1)

        # Create a client and send the buffer to the display server
        client = DisplayFITS_client()

        client.display_fitsbuf(fitsfile, data)


    Usage as client--sending filename:
      ...
      from fitsview import DisplayFITS_client
      ...

        # Create a client and send the file path to the display server
        client = DisplayFITS_client()
        
        client.display_fitsfile(fitsfile)
      
    """

    def __init__(self, svcname=defaultServiceName):
        # Get handle to server
        self.server = ro.remoteObjectProxy(svcname)

        
    def display_fitsbuf(self, fitsfile, data, byteswap=False):
        """Sends a FITS buffer to the server.
        _data_ is a numpy containing the image data to send
        If _byteswap_ is true the data will by byteswapped before sending.
        """

        time1 = time.time()

        # Byteswap data if requested
        if byteswap:
            data.byteswap()

        (width, height) = data.shape
        na_type = data.type()
        bitpix = data.itemsize()

        # Convert numpy to buffer
        data = data.tostring()
        size = len(data)

        # Encode buffer for XMLRPC transport
        data = ro.binary_encode(data)

        time2 = time.time()

        # Call remote object to display buffer
        res = self.server.display_fitsbuf(fitsfile, data, width, height,
                                          bitpix)

        tottime = time.time() - time1

        print "Time taken: %d bytes / %f secs (%f bytes/sec) (enc: %f secs) " % \
              (size, tottime, size/tottime, time2-time1)


    def display_fitsfile(self, fitsfile):
        # Call remote object to display a file that IT loads
        res = self.server.display_fitsfile(fitsfile)


class AgSplitter (Ag.AgServer):

    def __init__(self, logger, hosts=[], ev_quit=None, delta=1.0): 
        self.logger = logger
        self.ev_quit = ev_quit

        self.clients = Bunch.threadSafeBunch()
        self.add_clients(hosts)

        # Initialize my AG handler
        super(AgSplitter, self).__init__(self.logger, ev_quit=self.ev_quit,
                                         delta=delta)
         
       
    def add_client(self, hostname, agtype):
        ag_client = Ag.AgClient(hostname, agtype, self.logger)

        self.clients[hostname] = ag_client
        
    def add_clients(self, hostnames):
        for hostname in hostnames:
            self.add_client(hostname)

    def remove_client(self, hostname):
        del self.clients[hostname]
        
            
    def process(self, agheader, datatime, data_np):
        """Process AG data packet.
        _agheader_ is a string corresponding to the AG header string.
        _datatime_ is the data time (as float) of the data.
        _data_np_ is a numpy of the pixel data.
        """

        start_time = time.time()
        
        self.logger.debug("datatime: %8.4f  header: %s" % (
            datatime, agheader))

        # Distribute packet to clients
        for hostname in self.clients.keys():
            try:
                self.logger.debug("forwarding data to host '%s' %8.4f" % (
                    hostname, time.time()))
                ag_client = self.clients[hostname]

                res = ag_client.send_ag(header, datatime, data_np)
                self.logger.debug("end forwarding data to host '%s' %8.4f" % (
                    hostname, time.time()))

            except Exception, e:
                self.logger.error("Error sending data to host '%s': %s" % (
                    hostname, str(e)))
                (type, value, tback) = sys.exc_info()
                #self.logger.error("Traceback:\n%s" % \
                #                  tback.format_exec())
                self.logger.error("Traceback:\n%s" % \
                                  str(tback))
                traceback.print_tb(tback)

        end_time = time.time()
        elapsed_time = end_time - start_time
        self.logger.debug("elapsed time: %8.4f" % (elapsed_time))
        
                
class AgDisplay (Ag.AgServer):

    def __init__(self, logger, svcname, ev_quit=None, delta=1.0, agtype='AG'): 
        self.logger = logger
        self.ev_quit = ev_quit

        self.client = DisplayFITS_client(svcname=svcname)

        # Initialize my AG handler
        super(AgDisplay, self).__init__(self.logger, ev_quit=self.ev_quit,
                                        delta=delta, agtype=agtype)
         
       
    def process(self, agheader, datatime, data_np):
        """Process AG data packet.
        _agheader_ is a string corresponding to the AG header string.
        _datatime_ is the data time (as float) of the data.
        _data_np_ is a numpy of the pixel data.
        """

        start_time = time.time()
        
        self.logger.debug("datatime: %8.4f  header: %s" % (
            datatime, agheader))
        
        try:
            res = self.client.display_fitsbuf("VGWIMAGE", data_np,
                                              byteswap=False)

        except Exception, e:
            self.logger.error("Error sending data to client: %s" % (
                str(e)))
            (type, value, tback) = sys.exc_info()
            #self.logger.error("Traceback:\n%s" % \
            #                  tback.format_exec())
            self.logger.error("Traceback:\n%s" % \
                              str(tback))
            traceback.print_tb(tback)

        end_time = time.time()
        elapsed_time = end_time - start_time
        self.logger.debug("elapsed time: %8.4f" % (elapsed_time))
        

class AgSimulator(object):

    def __init__(self, options, logger):

        self.options = options
        self.logger = logger
 
        self.logger.debug('svcname<%s>' %options.svcname)

        # Initialize remoteObjects system, if necessary
        if self.options.svcname:
            self.logger.debug('svcname<%s>' %options.svcname)
            try:
                ro.init()

            except ro.remoteObjectError, e:
                raise Ag.AgClientError("Can't initialize remote object service: %s" % (str(e)))

        self.client = None
        self.server = None

        
    def ag_server(self):
        """Implements a simple AG server.
        """

        if self.options.clients:
            self.server = AgSplitter(self.logger, delta=self.options.delta,
                                     agtype=self.options.agtype)
            self.server.add_clients(self.options.clients.split(','))

        elif self.options.display:
            ro.init()

            self.server = AgDisplay(self.logger, self.options.display,
                                    delta=self.options.delta,
                                    agtype=self.options.agtype)

        else:
            self.server = Ag.AgServer(self.logger, delta=self.options.delta,
                                      agtype=self.options.agtype)

        self.server.start()
        try:
            try:
                self.logger.info("Press ^C to terminate server...")
                self.server.mainloop()

            except KeyboardInterrupt:
                self.logger.error("Caught keyboard interrupt!")

            except Exception, e:
                self.logger.error("Server failed with exception: %s" % str(e))

        finally:
            self.server.stop(wait=True)


    def ag_client(self):
        """Implements a simple AG client.
        """

        # Open test image to send
        try:
            fitsobj = pyfits.open(self.options.fitsfile, 'readonly')

        except IOError, e:
            raise Ag.AgClientError("Cannot open FITS file '%s'" % (self.options.fitsfile))

        # Main client code.  If specified number of packets, then send only
        # that many, otherwise go into continuous mode and send until user
        # types ^C
        #
        if self.options.numpkts:
            m = self.options.numpkts
            for i in xrange(m):
                self.send_pkt(i+1, m, fitsobj)

        else:
            try:
                try:
                    self.logger.info("Starting continuous send--press ^C to terminate...")
                    while True:
                        self.send_pkt(1, 2, fitsobj)

                except KeyboardInterrupt:
                    self.logger.error("Keyboard interrupt!")
            finally:
                self.logger.info("Terminating client...")


    def mk_client(self):
        """RPC client making function.
        """

        # Get hostname of target host.  If None, assume we are running on
        # target host.
        if self.options.tgthost:
            tgthost = self.options.tgthost

        elif self.options.svcname:
            # Look up the host by finding what host service name is running on
            try:
                hosts = ro.get_hosts(self.options.svcname)
                if len(hosts) < 1:
                    raise Ag.AgClientError("Cannot find a '%s' server running" % (
                        self.options.svcname))

                tgthost = hosts.pop(0)

            except ro.remoteObjectError, e:
                raise Ag.AgClientError("Error looking up '%s': %s" % (
                        self.options.svcname, str(e)))

        else:
            tgthost = SOSSrpc.get_myhost(short=True)

        agtype = 'AG'
        if self.options.agtype:
            agtype = self.options.agtype

        # Create ag interface
        self.client = Ag.AgClient(tgthost, agtype, self.logger)


    # RPC client send function
    #
    def send_pkt(self, n, m, fitsobj):
        start_time = time.time()

        try:
            if self.client == None:
                self.logger.info("Trying to reset client...")
                self.mk_client()

            self.client.sendAgFITS(self.options.agtype, self.options.agfocus,
                                   fitsobj, datatime=time.time(),
                                   iBinning=self.options.binning,
                                   iKind=self.options.datakind,
                                   expRangeX=options.expRangeX,
                                   expRangeY=options.expRangeY,
                                   expRangeDX=options.expRangeDX,
                                   expRangeDY=options.expRangeDY,
                                   expTime=options.expTime)

        except Ag.AgClientError, e:
            self.logger.error("Error sending packet: %s" % (str(e)))
            self.client = None

        if n < m:
            # Sleep just enough so that next packet starts on interval
            end_time = start_time + self.options.interval
            sleep_time = max(0, end_time - time.time())
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                self.logger.warn("Can't sustain interval %f sec" % (self.options.interval))

    
def main(options, args):

    logname = 'AgSend'
    logger = ssdlog.make_logger(logname, options)

    # Do our specified function, whether server or client
    agsim = AgSimulator(options, logger)
    
    if options.server:
        agsim.ag_server()

    else:
        agsim.ag_client()


usage = "usage : %%prog [options]"

if __name__ == '__main__':

    import os
    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("-a", "--agtype", dest="agtype", metavar="TYPE",
                      help="Set AG type to {AG|SV|SH|FMOS}")
    optprs.add_option("-b", "--binning", dest="binning", metavar="BINNING",
                      type="int", default=1,
                      help="Set AG binning to BINNING (1:1x1, 2:2x2, 4:4x4, 8:8x8)")
    optprs.add_option("--clients", dest="clients", metavar="HOSTS",
                      help="Operate in splitter mode with clients HOSTS")
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--delta", dest="delta", metavar="SEC",
                      type="float", default=1.0,
                      help="Drop packets arriving less than delta SEC apart")
    optprs.add_option("--display", dest="display", metavar="SVCNAME",
                      help="Send data to display SVCNAME")
    optprs.add_option("--expRangeX", dest="expRangeX", type="int",
                      help="exposure range origin X")
    optprs.add_option("--expRangeY", dest="expRangeY", type="int",
                      help="exposure range origin Y")
    optprs.add_option("--expRangeDX", dest="expRangeDX", type="int",
                      help="exposure range origin width")
    optprs.add_option("--expRangeDY", dest="expRangeDY", type="int",
                      help="exposure range origin height")
    optprs.add_option("--expTime", dest="expTime", type="int",
                      default=1000,
                      help="exposure time")
    optprs.add_option("-f", "--fitsfile", dest="fitsfile", metavar="FILE",
                      default="%s/agsim/AG.fits" %(os.environ['DATAHOME']),
                      help="Use data from FILE for AG data")
    optprs.add_option("--focus", dest="agfocus", metavar="FOCUS",
                      default='CASS',
                      help="Set AG focus to FOCUS (PFVS|PIR|CASS|NSIR|NSOP)")
    optprs.add_option("-k", "--kind", dest="datakind", metavar="KIND",
                      type="int", default=1,
                      help="Set AG data kind to KIND (1:Obj, 2:Dark, 3:Flat, 4:Sky)")
    optprs.add_option("--interval", dest="interval", metavar="SEC",
                      type="float", default=1.0,
                      help="Sleep SEC seconds between packets")
    optprs.add_option("--num", dest="numpkts", metavar="NUM",
                      type="int", help="Send NUM packets")
    optprs.add_option("--tgthost", dest="tgthost", 
                      help="Use HOST as the target host", metavar="HOST")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--server", dest="server", default=False,
                      action="store_true",
                      help="Be a server and not a client")
    optprs.add_option("--svcname", dest="svcname", 
                      help="Use NAME as the service name", metavar="NAME")
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
       
# END


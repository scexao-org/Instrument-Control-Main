#!/usr/bin/env python
#
# STARSsim.py -- Simulator for Subaru Observatory STARS archive system.
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Dec 18 14:05:09 HST 2008
#]
#
#
import sys, os, re, time
import threading, Queue

import rpc
from Bunch import Bunch
import Task
import SOSS.SOSSrpc as SOSSrpc
from SOSS.INSint import BaseInterface
from cfg.INS import INSdata as INSconfig
import logging, ssdlog
import STARSint

# Version/release number
version = "20100208.0"

# A dictionary of dictionaries.  Each sub-dictionary needs to have key/value
# pairs: transfermethod=('ftp' or 'ssh'), username (login id), password (if
# using ftp), raidpath (local place to store transferred files).
# Top level dictionary is keyed by hostname (of STARS interface at other end).
#
transferParams = {
    }

# Look up the transfer parameters by key=host and load them into a
# Bunch object.  If no parameters are found, raise a STARSsimError.
#
def get_transferParams(host):

    key = host.lower()
    try:
        vals = transferParams[key]

        res = Bunch(host=host)
        res.__dict__.update(vals)

        return res

    except KeyError:
        pass

    # No host-specific parameters.  Try the wildcard entry.
    try:
        vals = transferParams['*']

        res = Bunch(host=host)
        res.__dict__.update(vals)

        return res

    except KeyError:
        raise STARSsimError("No transfer parameters on file for host '%s'" % \
                            host)

    
def add_transferParams(host, **kwdargs):
    key = host.lower()

    d = {}
    d.update(kwdargs)
    transferParams[key] = d


class STARSsimError(Exception):
    pass


def getFrameInfoFromPath(fitspath):
    # Extract frame id from file path
    (fitsdir, fitsname) = os.path.split(fitspath)
    (frameid, ext) = os.path.splitext(fitsname)
    
    match = re.match('^(\w{3})([AQ])(\d{8})$', frameid)
    if match:
        (inscode, frametype, frame_no) = match.groups()
        frame_no = int(frame_no)
        
        return Bunch(frameid=frameid, fitsname=fitsname,
                     fitsdir=fitsdir, inscode=inscode,
                     frametype=frametype, frame_no=frame_no)

    raise STARSsimError("path does not match Subaru FITS specification")


class STARSchannel(BaseInterface):
    ''' Instantiating this class creates a single "channel" (RPC) interface to
    the OCS STARS interface.  Normally, multiple channels are aggregated to
    create the full interface
    '''

    def __init__(self, channelnum, ev_quit, logger, taskqueue,
                 myhost=None, myport=None, seq_num=None):

        # Initialize common attributes
        super(STARSchannel, self).__init__(ev_quit, logger, None,
                                           taskqueue,
                                           myhost=myhost, myport=myport,
                                           seq_num=seq_num)
        self.channelnum = channelnum
        self.recvTasker = Task.make_tasker(self.cmd_recv)

        self.insconfig = INSconfig()

        # Create an RPC server
        try:
            key = ('OBCtoSTARS%d' % channelnum)

            self.rpcconn = SOSSrpc.clientServerPair(key, initiator=False,
                                                    logger=self.logger,
                                                    ev_quit=self.ev_quit,
                                                    #myhost=self.myhost,
                                                    recvqueue=taskqueue,
                                                    func=self.recvTasker)

        except SOSSrpc.rpcError, e:
            raise STARSsimError("Error creating rpc client-server pair: %s" % \
                                str(e))


    def cmd_recv(self, rpcmsg):

        if rpcmsg.msg_type != 'FS':
            raise STARSsimError("receive_fits: rpc msg is not a SOSS FS request")

        try:
            data = rpcmsg.unpack_fs()

        except SOSSrpc.rpcMsgError, e:
            raise STARSintError("SOSS RPC payload format error: %s" % str(e))
            
        # TODO: check for validity of all command parameters
        result = 0

        # Create RPC message
        rpcbuf = SOSSrpc.SOSScmdRpcMsg(sender=self.myhost, pkt_type='FT')

        # Send AB message
        rpcbuf.pack_ab(rpcmsg.seq_num, result, receiver=rpcmsg.sender,
                       seq_num=self.seq_num.bump())
        try:
            res = self.rpcconn.callrpc(rpcbuf)

        except SOSSrpc.rpcClientError, e:
            raise STARSsimError("receive_fits: error sending AB response: %s" % str(e))

        if result != 0:
            return
        
        # Get transfer parameters
        trans = get_transferParams(rpcmsg.sender)

        # FITS file....come on down!!
        (status1, result) = self.save_fits_via_ftp(data.fitspath,
                                                   data.fitssize, trans,
                                                   data.propid)

        # Index file....come on down!!
        if result == 0:
            (status2, result) = self.save_fits_via_ftp(data.indexpath,
                                                       data.indexsize, trans,
                                                       data.propid)
        else:
            status2 = 0

        # Send EN message
        rpcbuf.pack_fe(rpcmsg.seq_num, status1, status2, result,
                       receiver=rpcmsg.sender, seq_num=self.seq_num.bump())
        try:
            res = self.rpcconn.callrpc(rpcbuf)

        except SOSSrpc.rpcClientError, e:
            raise STARSsimError("receive_fits: error sending FE response: %s" % str(e))
            
        self.logger.info("Processed FITS transfer request successfully!")


    # This function handles saving a fits file via FTP or SSH transfer.
    #
    def save_fits_via_ftp(self, path, size, trans, propid):

        (dir, fn) = os.path.split(path)

        propid = propid.lower()
        if propid != 'summitlog':
            # Look up instrument name based on filename
            fr = getFrameInfoFromPath(fn)
            insname = self.insconfig.getNameByCode(fr.inscode)
        else:
            insname = 'LOGS'

        # construct local path to file
        localpath = os.path.join(trans.raidpath, insname, fn)

        if trans.transfermethod == 'ftp':
            self.logger.info("Request to transfer file '%s' via FTP" % fn)
            cmd = ("wget --tries=5 --waitretry=7 --user=%s --password='%s' -O %s -a FTP.log ftp://%s/%s" % (trans.username, trans.password, localpath, trans.host, path))
        else:
            self.logger.info("Request to transfer file '%s' via SSH" % fn)
            cmd = ("scp %s@%s:%s %s" % (trans.username, trans.host, path, localpath))
            self.logger.info("command is: %s" % cmd)

        # TODO: build retry in here?
        try:
            res = os.system(cmd)

        except OSError, e:
            self.logger.error("Failed to FTP/SCP fits file '%s': %s" % (fn, str(e)))
            return (1, 1)

        if res != 0:
            self.logger.error("Failed to FTP/SCP fits file '%s': exit err=%d" % (fn, res))
            return (1, 1)

        # Check the transferred file's size against passed value.
        try:
            statbuf = os.stat(localpath)

        except OSError, e:
            raise STARSsimError("[save_fits_via_ftp] Cannot stat file '%s': %s" % \
                                (localpath, str(e)))

        if statbuf.st_size != size:
            raise STARSsimError("[save_fits_via_ftp] Transferred file (%s) size differs from stated size: %d vs. %d" % \
                                (localpath, statbuf.st_size, size))

        return (0, 0)
    

class STARSsimulator(object):
    '''This class encompasses the STARS archive simulator.
    '''

    def __init__(self, channels=(7,8), ev_quit=None, logger=None,
                 numthreads=None, threadPool=None, seq_num=None):

        if not ev_quit:
            self.ev_quit = threading.Event()
        else:
            self.ev_quit = ev_quit
        self.channels = list(channels)
        self.numchannels = len(channels)
        self.channel = {}
        self.logger = logger

        if numthreads:
            self.numthreads = numthreads
        else:
            # Estimate number of threads needed to handle traffic
            self.numthreads = 2 + (self.numchannels * 2)
            
        # Thread pool for autonomous tasks
        # If we were passed in a thread pool, then use it.  If not,
        # make one.  Record whether we made our own or not.  This
        # threadPool is shared by all interfaces.
        if threadPool != None:
            self.threadPool = threadPool
            self.mythreadpool = False

        else:
            self.threadPool = Task.ThreadPool(logger=self.logger,
                                              ev_quit=self.ev_quit,
                                              numthreads=self.numthreads)
            self.mythreadpool = True

        if seq_num:
            self.seq_num = seq_num
        else:
            # Share a sequence number between interfaces, or let each
            # interface generate it's own sequence numbers
            #self.seq_num = SOSSrpc.rpcSequenceNumber()
            self.seq_num = None
        
        # Master queue for distributing work to threadpool
        self.taskqueue = Queue.Queue()

        # For task inheritance:
        self.tag = 'STARSsim'
        self.shares = ['logger', 'ev_quit', 'timeout', 'threadPool']
        self.timeout = 0.1
        self.qtask = None

        # Make the channels for this STARS interface.
        self.make_channels(self.logger)


    # Create our set of "channels" available from STARS.  Normal operation is
    # two channels (1,2: summit or 5,6: Fujitsu simulator or 7,8: SSD simulator)
    #
    def make_channels(self, logger):

        for ch_i in self.channels:
            # Create a log for logging results
            if not logger:
                queue = Queue.Queue()
                log = ssdlog.mklog('ch%d' % ch_i, queue, logging.DEBUG)
            else:
                log = logger
                queue = None

            # Create STARS rpc interface object for channel 'ch_i'
            iface = STARSchannel(ch_i, self.ev_quit, log, self.taskqueue,
                                 seq_num=self.seq_num)

            # Create channel bundle object
            self.channel[ch_i] = Bunch(log=log, logqueue=queue, iface=iface)

        
    def get_threadPool(self):
        return self.threadPool
    
        
    # start rpc clients and servers associated with each channel.
    #
    def start(self, wait=True):

        # Create a thread for the rpc server
        self.ev_quit.clear()

        # Start our thread pool (if we created it)
        if self.mythreadpool:
            self.threadPool.startall(wait=True)

        # Initialize the task queue processing task
        t = Task.QueueTaskset(self.taskqueue, waitflag=False)
        self.qtask = t
        t.initialize(self)
        t.start()
        
        for ch_i in self.channels:
            self.channel[ch_i].iface.start(wait=wait)


    # stop rpc server.
    #
    def stop(self, wait=True):
        for ch_i in self.channels:
            self.channel[ch_i].iface.stop(wait=wait)

        if self.qtask:
            self.qtask.stop()
        
        # Stop our thread pool (if we created it)
        if self.mythreadpool:
            self.threadPool.stopall(wait=wait)

        self.logger.info("STARS INTERFACE STOPPED.")
        self.ev_quit.set()


def monitor(ch_i, queue, ev_quit):

    print "Monitoring log for channel %d" % ch_i
    while not ev_quit.isSet():

        line = queue.get()
        if line:
            print "CH(%d): %s" % (ch_i, line)

        else:
            ev_quit.wait(0.1)


def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('STARSsim', options)

    # Get list of channels to communicate with OCS host(s).
    channels = map(int, options.channels.split(','))
    for ch_i in channels:
        if not ch_i in [1,2,3,4,5,6,7,8]:
            print "Channels must be in the range 1-8"
            sys.exit(1)

    # Get the current username as the login for transfers if one was not
    # provided.
    if not options.username:
        # os.getlogin() doesn't always appear to work
        #username = os.getlogin()
        #username = getpass.getuser()
        username = os.environ['LOGNAME']
    else:
        username = options.username

    # Add info for file transfer ftp/ssh operations.
    # Currently just the wildcard entry is added.
    add_transferParams('*', transfermethod=options.transfermethod,
                       raidpath=options.starsdir, username=username,
                       password=options.password)
    
    # Quit event that everyone will wait on
    ev_quit = threading.Event()

    # Create the simulator
    stars = STARSsimulator(channels=channels, ev_quit=ev_quit,
                           logger=logger,
                           numthreads=options.numthreads)

    # Monitor it's outputs to stdout
##     for ch_i in stars.channels:
        
##         thread = threading.Thread(target=monitor,
##                                   args=[ch_i,
##                                         stars.channel[ch_i].logqueue,
##                                         ev_quit])
##         thread.start()

    # Start it
    logger.info("STARS simulator starting up...")
    try:
        stars.start()

        # Now wait from someone to press ^C
        try:
            sys.stdin.readline()
        
        except KeyboardInterrupt:
            logger.error("Caught keyboard interrupt!")

    finally:
        # Stop servers
        logger.info("STARS simulator shutting down...")
        stars.stop()


if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("-c", "--channels", dest="channels", default="7,8",
                      help="List of numbered channels to use (1-8)")
    optprs.add_option("-d", "--dir", dest="starsdir", default=".",
                      metavar="DIR",
                      help="Use DIR to store transferred files")
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-m", "--method", dest="transfermethod", default="ssh",
                      help="Specify method for file transfers (ftp|ssh")
    optprs.add_option("--numthreads", dest="numthreads", type="int",
                      help="Use NUM threads for thread pool", metavar="NUM")
    optprs.add_option("-p", "--password", dest="password",
                      help="Specify password for ftp transfers")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("-u", "--user", dest="username", metavar="USER",
                      help="Login as USER to transfer files")
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

#! /usr/bin/env python
#
# gen2sts.py -- subscribe to 1Hz status feed from Gen2
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Oct 28 13:44:24 HST 2011
#]
#
import sys, time
import threading
import optparse
import socket
import yaml

import ssdlog
import remoteObjects as ro
import remoteObjects.Monitor as Monitor

# Default port to open up on this system for subscribe communication
default_port = 9877

# Default set of servers to contact for remote objects initialization
default_rohosts = ["g2ins1.sum.subaru.nao.ac.jp"]

# Default set of channels to subscribe to
default_channels = ['status']

# Default place to store output (recommend to use a FIFO)
default_output = "/tmp/gen2sts.fifo"

# --- MODULE STATE ---
# mutex to arbitrate access to status values
lock = threading.RLock()
# status feed will be stored in here as flat dictionary
status = {}
# This is the set of aliases we are interested in
aliases = set(['STS.TIME2'])


def read_config(configfile):
    """Read the Gen2STS configuration file.
    """
    global aliases
    with open(configfile, 'r') as in_f:
        buf = in_f.read()

    config = yaml.load(buf)

    # Reset the alias set
    aliases = set(config.get('aliases', aliases))
    
    
# This function will be called at an approximately 1Hz rate with status
# updates
def status_cb(payload, logger, out_f):
    """Receive a status update.
    - payload is the payload data received from the pub/sub system
    - out_f is an open descriptor to a file to write the information
    """
    global status, lock
    try:
        bnch = Monitor.unpack_payload(payload)
        if bnch.path != 'mon.status':
            return

        with lock:
            statusDict = bnch.value
            statusDict['STS.TIME2'] = time.time()
            status.update(statusDict)
            logger.debug("status updated: %d items time:%s" % (
                len(statusDict),
                time.strftime("%H:%M:%S", time.localtime())))
            #logger.debug("status: %s" % (str(statusDict)))

        write_sts(statusDict, logger, out_f)

    except Monitor.MonitorError, e:
        logger.error("monitor error: %s" % (str(e)))


def write_sts(statusDict, logger, out_f):
    """Write the output file or FIFO read by STS
    - statusDict is a dictionary of status items
    - out_f is an open descriptor to a file to write the information
    """
    # Find out alaises we have in common with what we are looking for
    keys = set(statusDict.keys()).intersection(aliases)

    d = dict((k, statusDict[k]) for k in keys)
    # d contains all the status items we are interested in and nothing more
    logger.debug("status=%s" % str(d))

    # Write keys to output file
    try:
        for key in keys:
            out_f.write("%s=%s\n" % (key, str(d[key])))
        out_f.flush()

    except IOError, e:
        logger.error("Error writing to output: %s" % (str(e)))


def main(options, args):
    global lock, status

    # create logger
    logger = ssdlog.make_logger('gen2sts', options)

    # Initialize remote objects system
    if not options.rohosts:
        rohosts = default_rohosts
    else:
        rohosts = options.rohosts.split(',')
    logger.debug("Initializing remote objects")
    ro.init(rohosts)

    if options.configfile:
        logger.info("Reading config file %s" % (options.configfile))
        read_config(options.configfile)

    logger.debug("Opening output file %s" % (options.outfile))
    out_f = open(options.outfile, 'a')
    
    # fetch initial status items that we need
    stobj = ro.remoteObjectProxy(options.statussvc)
    logger.info("Fetching initial status values")
    fetchDict = {}.fromkeys(aliases)
    statusDict = stobj.fetch(fetchDict)

    # Initial write out of information to STS
    with lock:
        statusDict['STS.TIME2'] = time.time()
        status.update(statusDict)
    write_sts(statusDict, logger, out_f)

    # Create a local subscribe object
    myhost = ro.get_myhost(short=True)
    mymon = Monitor.Monitor(myhost+'.mon', logger)

    if not options.channels:
        channels = default_channels
    else:
        channels = options.channels.split(',')
    
    # Subscribe our local callback function
    fn = lambda payload, name, channels: status_cb(payload, logger, out_f)
    mymon.subscribe_cb(fn, channels)

    # Startup monitor
    logger.debug("Starting pub/sub components")
    mymon.start(wait=True)
    mymon.start_server(wait=True, port=options.monport)

    # subscribe our monitor to the publication feed
    logger.debug("Subscribing to status feed")
    mymon.subscribe_remote(options.monitor, channels, {})

    logger.info("starting up main program...")
    try:
        try:
            # YOUR MAIN PROGRAM CALL GOES HERE
            # (don't forget to use the mutex to arbitrate access to the
            #    status dictionary)
            while True:
                time.sleep(1.0)
                #logger.debug("Zzzzz ...")

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt--shutting down...")
    finally:
        logger.info("shutting down...")
        mymon.unsubscribe_remote(options.monitor, channels, {})
        mymon.stop_server()
        mymon.stop()
        out_f.close()

        
if __name__ == '__main__':
    usage = "usage: %prog"
    optprs = optparse.OptionParser(usage=usage, version=('%%prog'))

    optprs.add_option("-f", "--configfile", dest="configfile",
                      help="Specify configuration file")
    optprs.add_option("--channels", dest="channels",
                      help="Specify channels to subscribe to")
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--gen2hosts", dest="rohosts",
                      help="Specify gen2 server names")
    optprs.add_option("--monitor", dest="monitor", default='monitor',
                      help="Specify NAME of pubsub service")
    optprs.add_option("--monport", dest="monport", type="int",
                      default=default_port,
                      help="Register monitor using PORT", metavar="PORT")
    optprs.add_option("--output", dest="outfile", default=default_output,
                      help="Specify output file or FIFO")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--statussvc", dest="statussvc", default='status',
                      help="Specify NAME of status service")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

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


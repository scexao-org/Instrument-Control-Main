#!/usr/bin/env python
#
# datasink.py -- a program to receive FITS data from Gen2
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Oct 17 13:52:02 HST 2012
#]
#
"""
A program to receive FITS frames from the Gen2 system.

This program (by itself) shouldn't require anything other than a standard
Python installation.  Feedback and bug fixes welcome (ocs@naoj.org)

Typical use:

$ datasink.py -g <gen2host> -f <keyfile>

where <keyfile> is the path to a file containing the data key provided by
Subary for your observation.  In this case, when each file is streamed to
your laptop a log message will display to the terminal and the data file
will be written to the current directory.

This lets you specify a special directory for the files:

$ datasink.py -g <gen2host> -f <keyfile> -d /path/to/data/directory

This lets you specify a custom program to run each time after the
file is saved (e.g. a fits viewer).

$ datasink.py -g <gen2host> -f <keyfile> -a "./send_skycat %(filepath)s"

Same, but for DS9:

$ datasink.py -g <gen2host> -f <keyfile> -a "xpaset -p ds9 file %(filepath)s"

Get help for program arguments.

$ datasink.py --help

will show all available options.
"""

import sys, os, re, time, signal
import socket
import logging, logging.handlers
import threading, Queue
import datetime
import xmlrpclib
import SocketServer
from SimpleXMLRPCServer import SimpleXMLRPCServer
import binascii
if sys.hexversion > 0x02050000:
    import hashlib
    digest_algorithm = hashlib.sha1
else:
    import sha
    digest_algorithm = sha
import hmac
import bz2
import subprocess


LOG_FORMAT = '%(asctime)s | %(levelname)1.1s | %(filename)s:%(lineno)d | %(message)s'

version = "20120409"


# def any_sha1_hex_digest (s):
#     # Python <= 2.4
#     if sys.hexversion < 0x02050000:
#         import sha
#         return sha.new(s).hexdigest()
#     # Python >= 3.0
#     elif sys.hexversion > 0x03000000:
#         import hashlib
#         return hashlib.sha1(bytes(s,'utf-8')).hexdigest()
#     else:
#         import hashlib
#         return hashlib.sha1(s).hexdigest()


class SinkError(Exception):
    pass
class md5Error(SinkError):
    pass

class Bunch(object):
    def __init__(self, **kwdargs):
        self.tbl = {}
        self.tbl.update(kwdargs)
        # after initialisation, setting attributes is the same as setting
        # an item.
        self.__initialised = True

    def keys(self):
        return self.tbl.keys()

    def has_key(self, key):
        return self.tbl.has_key(key)

    def update(self, dict2):
        return self.tbl.update(dict2)

    def __getattr__(self, attr):
        return self.tbl[attr]

    def __setattr__(self, attr, value):
        # this test allows attributes to be set in the __init__ method
        # (self.__dict__[_Bunch__initialised] same as self.__initialized)
        if not self.__dict__.has_key('_Bunch__initialised'):
            self.__dict__[attr] = value

        else:
            # Any normal attributes are handled normally
            if self.__dict__.has_key(attr):
                self.__dict__[attr] = value
            # Others are entries in the table
            else:
                self.tbl[attr] = value
    
def getHandle(svcname, host, port=7075):
    # Look up archiver
    ns = xmlrpclib.ServerProxy("http://%s:%d/" % (host, port))
    try:
        res = ns.getHosts(svcname)

    except Exception, e:
        raise SinkError("Cannot make connection to name service on host '%s': %s" % (
            host, str(e)))

    if (type(res) != list) or (len(res) < 1):
        raise SinkError("Name server on '%s' says service '%s' not found" % (
            host, svcname))
        
    (host, port) = res[0]

    svc = xmlrpclib.ServerProxy("http://%s:%s@%s:%d/" % (svcname, svcname,
                                                         host, port))
    try:
        res = svc.ro_echo(0)

    except Exception, e:
        raise SinkError("Cannot make connection to service '%s' on host '%s': %s" % (
            svcname, host, str(e)))
    
    return svc


def get_myip(host='subarutelescope.org'):
    """Clever way to get your public IP address.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((host, 80))
    return s.getsockname()[0]


def cleanup_children():
    # clean up any child processes waiting to be reaped
    pid = 1
    try:
        while pid:
            (pid, status) = os.waitpid(-1, os.WNOHANG)
    except OSError, e:
        pass

          
class DataSink(object):

    def __init__(self, logger, datadir, notify_fn=None,
                 md5check=False, pullhost='localhost', pullmethod='ftps',
                 pullname=None, pullport=None, xferlog='/dev/null',
                 mountmangle=None, storeby=None, filter_fn=None):

        self.logger = logger
        self.notify_fn = notify_fn
        # transfer log name--this is ostensibly for storing the output
        # of the external programs used to transfer the files, but it
        # is currently unused because our choice of program (lftp) does
        # not give a decent option for specifying the log file
        self.xferlog = xferlog

        # Where to store any FITS files we receive directly
        self.datadir = datadir
        # Should we verify md5 checksum
        self.md5check = md5check
        # controls use of subdirectories for storing files
        self.storeby = storeby

        # These are used in pull transfers--host, method and username
        self.pullhost = pullhost
        self.pullport = pullport
        self.pullmethod = pullmethod
        if not pullname:
            try:
                pullname = os.environ['LOGNAME']
            except KeyError:
                pullname = 'anonymous'
        self.pullname = pullname
        self.filter = filter_fn

        # Used to mangle remote filenames for NFS copying (see transfermethod())
        if mountmangle:
            self.mountmangle = mountmangle.rstrip('/')
        else:
            self.mountmangle = None

        # my hostname, for logging
        self.myhost = socket.getfqdn()
        
        # For critical sections in this object
        self.lock = threading.RLock()
        self.fileinfo = {}

        super(DataSink, self).__init__()


    def ro_echo(self, arg):
        """For remoteObjects internal use."""
        return arg

    def get_fileinfo(self, key, **kwdargs):
        with self.lock:
            try:
                d = self.fileinfo[key]
            except KeyError:
                d = Bunch(lock=threading.RLock())
                d.update(kwdargs)
                self.fileinfo[key] = d
                
            return d

    def get_lock(self, key):
        with self.lock:
            d = self.get_fileinfo(key)
            return d.lock


    def notify(self, filepath, filetype, propid, md5sum, kind=None):
        # Subclass should override to do something interesting, or supply
        # notify_fn to consructor
        self.logger.info("File received: %s type=%s propid=%s md5sum=%s" % (
            filepath, filetype, propid, md5sum))
        
        # If application is specified to do something then invoke it
        # otherwise we're done
        if not self.notify_fn:
            return

        self.notify_fn(filepath, filetype, propid, md5sum)

        
    def md5failed(self, filename, filetype):
        errmsg = "md5 checksum failed for '%s'" % (filename)
        self.logger.error(errmsg)
        raise md5Error(errmsg)


    def calc_md5sum(self, filepath):
        try:
            start_time = time.time()
            # NOTE: this will stall us a long time, so make sure
            # you've called this function from a thread
            proc = subprocess.Popen(['md5sum', filepath],
                                    stdout=subprocess.PIPE)
            result = proc.communicate()[0]
            if proc.returncode == 0:
                calc_md5sum = result.split()[0]
            else:
                raise md5Error(result)

            self.logger.debug("%s: md5sum=%s calc_time=%.3f sec" % (
                    filepath, calc_md5sum, time.time() - start_time))
            return calc_md5sum

        except Exception, e:
            raise SinkError("Error calculating md5sum for '%s': %s" % (
                filepath, str(e)))


    def check_md5sum(self, filepath, md5sum):
        """Check the md5sum of a file.  Requires the command 'md5sum' is
        installed.
        """
        if not md5sum:
            # For now only raise a warning when checksum seems to be
            # missing
            #raise md5Error("%s: upstream md5 checksum missing!" % (
            #    filepath))
            self.logger.warn("%s: missing checksum. upstream md5 checksum turned off?!" % (
                    filepath))

        calc_md5sum = self.calc_md5sum(filepath)
        if not md5sum:
            return calc_md5sum

        # Check MD5
        if calc_md5sum != md5sum:
            errmsg = "%s: md5 checksums don't match recv='%s' sent='%s'" % (
                filepath, calc_md5sum, md5sum)
            raise md5Error(errmsg)

        return md5sum
                               

    def get_newpath(self, filename, filetype, propid):

        if not self.storeby:
            newpath = os.path.abspath(os.path.join(self.datadir, filename))
        elif self.storeby == 'propid':
            newpath = os.path.abspath(os.path.join(self.datadir, propid,
                                                   filename))
        else:
            raise SinkError("I don't know how to store by '%s'" % (
                self.storeby))
        
        return newpath
    

    def process_data(self, filename, buffer, offset, num, count,
                     compressed, filetype, md5sum, propid):

        self.logger.debug("Processing %d/%d %s..." % (num, count, filename))
        try:
            # Decode binary data
            data = binascii.a2b_base64(buffer)

            if compressed:
                data = bz2.decompress(data)
                
            d = self.get_fileinfo(filename)
            with d.lock:
                if not d.has_key('count'):
                    d.num = 1
                    d.backlog = []
                    filepath = self.get_newpath(filename, filetype,
                                                propid)
                    # check for file exists already; if so, rename it
                    # and allow the transfer to continue
                    self.check_rename(filepath)

                    d.filepath = filepath
                    d.out_f = open(filepath, 'w')
                    d.total_bytes = 0
                    d.count = count
                    d.time_start = time.time()

                # NOTE: currently this probably only works for Unix (POSIX?)
                # filesystems and others with sparse writes...
                d.out_f.seek(offset)
                d.out_f.write(data)
                d.total_bytes += len(data)
                d.count -= 1
                left = d.count

            if left > 0:
                return 0

            # <== file finished transferring
            d.out_f.close()

            transfer_time = time.time() - d.time_start
            if d.total_bytes > 0:
                rate = float(d.total_bytes) / (1024 * 1024) / transfer_time
            self.logger.info("Total transfer time %.3f sec (%.2f MB/s)" % (
                transfer_time, rate))

            with self.lock:
                del self.fileinfo[filename]
                
            if self.md5check:
                # Check MD5 hash
                md5sum = self.check_md5sum(d.filepath, md5sum)

            self.notify(d.filepath, filetype, propid, md5sum,
                        kind='push')
            return 0

        except Exception, e:
            errmsg = "Failed to process FITS file '%s': %s" % (
                filename, str(e))
            self.logger.error(errmsg)
            raise SinkError(errmsg)

        
    def pull_data(self, filepath, filetype, md5sum, propid):

        (dirpath, filename) = os.path.split(filepath)
        self.logger.debug("Preparing to pull %s..." % (filename))
        newpath = self.get_newpath(filename, filetype, propid)

        # check for file exists already; if so, rename it and allow the
        # transfer to continue
        self.check_rename(newpath)

        xferDict = {}
        try:
            
            # Copy file
            self.transfer_file(filepath, self.pullhost, newpath,
                               transfermethod=self.pullmethod,
                               username=self.pullname,
                               port=self.pullport, result=xferDict,
                               md5sum=md5sum)
            # retrieve md5sum in case we had to calculate it ourself
            md5sum = xferDict.get('md5sum', None)

            self.notify(newpath, filetype, propid, md5sum,
                        kind='pull')
            return 0

        except Exception, e:
            errmsg = "Failed to process FITS file '%s': %s" % (
                filename, str(e))
            self.logger.error(errmsg)
            raise SinkError(errmsg)
            

    def check_rename(self, newpath):
        if os.path.exists(newpath):
            renamepath = newpath + time.strftime(".%Y%m%d-%H%M%S",
                                                 time.localtime())
            self.logger.warn("File '%s' exists; renaming to '%s'" % (
                newpath, renamepath))
            os.rename(newpath, renamepath)
            return True
        return False
        
    def transfer_file(self, filepath, host, newpath,
                      transfermethod='ftps', username=None,
                      password=None, port=None, result={},
                      md5sum=None):

        """This function handles transfering a file via one of the following
        protocols: { ftp, ftps, sftp, http, https, scp, copy (nfs) }

        Parameters:
          filepath: file path on the source host
          host: the source hostname
          port: optional port for the protocol
          newpath: file path on the destination host
          transfermethod: one of the protocols listed above
          username: username for ftp/ftps/sftp/http/https/scp transfers
          password: password for ftp/ftps/sftp/http/https transfers
          result: dictionary to store info about transfer
          md5sum: an optional md5sum to check against the file
        """

        self.logger.info("transfer file (%s): %s <-- %s" % (
            transfermethod, newpath, filepath))
        (directory, filename) = os.path.split(filepath)

        result.update(dict(time_start=datetime.datetime.now(),
                           src_host=host, src_path=filepath,
                           dst_host=self.myhost, dst_path=newpath,
                           xfer_method=transfermethod))
        
        if not username:
            try:
                username = os.environ['LOGNAME']
            except KeyError:
                username = 'anonymous'
            
        if transfermethod == 'copy':
            # NFS mount is assumed to be setup.  If we have an alternate mount location
            # locally, then mangle the path to reflect the mount on this host
            if self.mountmangle and filepath.startswith(self.mountmangle):
                sfx = filepath[len(self.mountmangle):].lstrip('/')
                copypath = os.path.join(self.mountmangle, sfx)
            else:
                copypath = filepath
                                        
            cmd = ("cp %s %s" % (copypath, newpath))
            result.update(dict(src_path=copypath))

        elif transfermethod == 'scp':
            # passwordless scp is assumed to be setup
            cmd = ("scp %s@%s:%s %s" % (username, host, filepath, newpath))

        ## elif transfermethod == 'ftp':
        ##     cmd = ("wget --tries=5 --waitretry=1 -O %s -a FTP.log --user=%s ftp://%s/%s" % (
        ##         newpath, username, host, filepath))
            
        else:
            # <== Set up to do an lftp transfer (ftp/sftp/ftps/http/https)

            if password:
                login = '"%s","%s"' % (username, password)
            else:
                # password to be looked up in .netrc
                login = '"%s"' % (username)

            setup = "set xfer:log yes; set net:max-retries 5; set net:reconnect-interval-max 2; set net:reconnect-interval-base 2; set xfer:disk-full-fatal true;"

            # Special args for specific protocols
            if transfermethod == 'ftp':
                setup = "%s set ftp:use-feat no; set ftp:use-mdtm no;" % (setup)

            elif transfermethod == 'ftps':
                setup = "%s set ftp:use-feat no; set ftp:use-mdtm no; set ftp:ssl-force yes;" % (
                    setup)

            elif transfermethod == 'sftp':
                setup = "%s set ftp:use-feat no; set ftp:ssl-force yes;" % (
                    setup)
                
            elif transfermethod == 'http':
                pass

            elif transfermethod == 'https':
                pass

            else:
                raise SinkError("Request to transfer file '%s': don't understand '%s' as a transfermethod" % (
                    filename, transfermethod))

            if port:
                cmd = ("""lftp -e '%s get %s -o %s; exit' -u %s %s://%s:%d""" % (
                    setup, filepath, newpath, login, transfermethod, host, port))
            else:
                cmd = ("""lftp -e '%s get %s -o %s; exit' -u %s %s://%s""" % (
                    setup, filepath, newpath, login, transfermethod, host))


        try:
            result.update(dict(xfer_cmd=cmd))

            self.logger.debug(cmd)
            res = os.system(cmd)

            if self.md5check:
                # Check MD5 hash
                md5sum = self.check_md5sum(newpath, md5sum)

            result.update(dict(time_done=datetime.datetime.now(),
                               md5sum=md5sum, xfer_code=res))

        except (OSError, md5Error), e:
            self.logger.error("Command was: %s" % (cmd))
            errmsg = "Failed to transfer fits file '%s': %s" % (
                filename, str(e))
            result.update(dict(time_done=datetime.datetime.now(),
                               res_str=errmsg, xfer_code=-1))
            raise SinkError(errmsg)

        if res != 0:
            self.logger.error("Command was: %s" % (cmd))
            errmsg = "Failed to transfer fits file '%s': exit err=%d" % (
                filename, res)
            result.update(dict(res_str=errmsg))
            raise SinkError(errmsg)


    def receive_data(self, filename, buffer, offset, num, count,
                     compressed, filetype, md5sum, propid):
        if self.filter and (not self.filter(filename)):
                self.logger.debug("Skipping %s, which doesn't match filter" % (
                    filename))
                return 0

        return self.process_data(filename, buffer, offset, num, count,
                                 compressed, filetype, md5sum, propid)


    def notify_data(self, filepath, filetype, md5sum, propid):

        dirpath, filename = os.path.split(filepath)

        if self.filter and (not self.filter(filename)):
                self.logger.debug("Skipping %s, which doesn't match filter" % (
                    filename))
                return 0
            
        return self.pull_data(filepath, filetype, md5sum, propid)

    
class AppSink(DataSink):

    def __init__(self, logger, datadir, appstr, **kwdargs):

        self.appstr = appstr
        super(AppSink, self).__init__(logger, datadir,
                                      notify_fn=self.launch_app,
                                      **kwdargs)
        
    def launch(self, cmdstr):
        try:
            self.logger.debug("Invoking '%s'" % (cmdstr))
            return os.system(cmdstr)

        except OSError, e:
            self.logger.error("Application '%s' raised exception: %s" % (
                cmdstr, str(e)))


    def launch_app(self, filepath, filetype, propid, md5sum, kind=None):

        d = {'filepath': filepath,
             'filetype': filetype,
             }

        if not self.appstr:
            return
        
        try:
            cmdstr = self.appstr % d
            t = threading.Thread(target=self.launch, args=[cmdstr])
            t.start()

            return 0

        except Exception, e:
            self.logger.error("Failed to start thread: %s" % (
                str(e)))

# Threaded mix-in
class AsyncXMLRPCServer(SimpleXMLRPCServer):

    def __init__(self, *args, **kwdargs):
        self.logger = args[0]
        self.workqueue = Queue.Queue()
        self.ev_quit = threading.Event()

        SimpleXMLRPCServer.__init__(self, *args[1:], **kwdargs)

    def process_request_thread(self, request, client_address):
        try:
            self.finish_request(request, client_address)
            self.close_request(request)

        except Exception, e:
            self.logger.error(str(e))
            self.handle_error(request, client_address)
            self.close_request(request)

    def process_request(self, request, client_address):
        # Put the call on the work queue, where one of the worker bees
        # will pick it up
        self.workqueue.put((self.process_request_thread,
                            (request, client_address)))

    def worker_bee(self, i):
        self.logger.debug("Starting worker bee #%d..." % (i))
        # Worker bee threads iterate, picking up work requests from the work
        # queue and handling them, until the quit flag is signaled.
        while not self.ev_quit.isSet():
            try:
                (target, args) = self.workqueue.get(block=True, timeout=0.1)

                self.logger.debug("Worker %d: invoking %s" % (
                    i, str(target)))
                target(*args)
                
            except Queue.Empty:
                continue

            except Exception, e:
                # NOTE: exceptions are logged in each kind of transfer method
                self.logger.debug("Worker %d: %s failed with exception: %s" % (
                    i, str(target), str(e)))

        self.logger.debug("Quitting worker bee #%d..." % (i))

    def interrupt(self):
        self.ev_quit.set()
        

def datasink(options, logger, keyname, hmac_digest, sink):

    # Create server
    server = AsyncXMLRPCServer(logger, ('', options.port))
    server.register_function(sink.ro_echo)
    server.register_function(sink.receive_data)
    server.register_function(sink.notify_data)

    ev_quit = threading.Event()
    
    try:
        myip = get_myip()
        
    except Exception, e:
        raise SinkError("Cannot get my IP address: %s" % (str(e)))

    def get_handles():
        logger.debug("Getting handle to session manager...")
        try:
            sessmgr = getHandle('sessions', options.host, 7075)

        except Exception, e:
            raise SinkError("Cannot get handle to session mgr: %s" % (str(e)))

        return sessmgr

    def register_loop():
        initialized = False
        while not ev_quit.isSet():
            # Register ourselves with session manager
            try:
                if not initialized:
                    initialized = True
                    sessmgr = get_handles()
                    
                logger.debug("Reregistering data sink...")
                sessmgr.register_datasink((myip, options.port), keyname,
                                          hmac_digest)

            except Exception, e:
                logger.warn("Cannot make connection to session manager on host '%s': %s" % (
                    options.host, str(e)))
                initialized = False

            cleanup_children()

            ev_quit.wait(options.interval)

        try:
            if initialized:
                logger.debug("Unregistering data sink...")
                sessmgr.unregister_datasink((myip, options.port), keyname,
                                            hmac_digest)
        except Exception, e:
            logger.warn("Unregister error: %s" % (str(e)))

    # Start a thread to register every so often
    t1 = threading.Thread(target=register_loop, args=[])
    t1.start()
    
    # Start worker threads
    for i in xrange(options.workers):
        t = threading.Thread(target=server.worker_bee, args=[i])
        t.start()
    
    # Start server and wait for callbacks
    try:
        logger.info("Starting data interface service...")
        try:
            server.serve_forever()
            
        except KeyboardInterrupt:
            logger.error("Caught keyboard interrupt!")
            server.interrupt()

    finally:
        logger.info("Data service shutting down...")
        ev_quit.set()
        t1.join()

def main(options, args):

    # Create top level logger.
    logger = logging.getLogger('datasink')
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(LOG_FORMAT)

    if options.logfile:
        fileHdlr  = logging.handlers.RotatingFileHandler(options.logfile,
                                                         maxBytes=options.loglimit,
                                                         backupCount=4)
        fileHdlr.setFormatter(fmt)
        fileHdlr.setLevel(options.loglevel)
        logger.addHandler(fileHdlr)
    # Add output to stderr, if requested
    if options.logstderr or (not options.logfile):
        stderrHdlr = logging.StreamHandler()
        stderrHdlr.setFormatter(fmt)
        stderrHdlr.setLevel(options.loglevel)
        logger.addHandler(stderrHdlr)

    if options.keyfile:
        keypath, keyfile = os.path.split(options.keyfile)
        keyname, ext = os.path.splitext(keyfile)
        try:
            in_f = open(options.keyfile, 'r')
            key = in_f.read().strip()
            in_f.close()

        except IOError, e:
            logger.error("Cannot open key file '%s': %s" % (
                options.keyfile, str(e)))
            sys.exit(1)

    elif options.key:
        key = options.key
        keyname = key.split('-')[0]

    else:
        logger.error("Please specify --keyfile or --key")
        sys.exit(1)

    if options.passfile:
        try:
            in_f = open(options.passfile, 'r')
            passphrase = in_f.read().strip()
            in_f.close()

        except IOError, e:
            logger.error("Cannot open passphrase file '%s': %s" % (
                options.passfile, str(e)))
            sys.exit(1)

    elif options.passphrase != None:
        passphrase = options.passphrase
        
    else:
        print "Please type the authorization passphrase:"
        passphrase = sys.stdin.readline().strip()

    pullport = None
    if options.pullport:
        pullport = int(options.pullport)

    # Compute hmac
    hmac_digest = hmac.new(key, passphrase, digest_algorithm).hexdigest()

    filter_fn = None
    if options.filter:
        regex = re.compile(options.filter)
        filter_fn = lambda filename: regex.match(filename)
        
    sink = AppSink(logger, options.datadir, options.appstr,
                   md5check=options.md5check,
                   pullhost=options.pullhost, pullport=pullport,
                   pullmethod=options.pullmethod,
                   pullname=options.pullname, xferlog=options.xferlog,
                   mountmangle=options.mountmangle, storeby=options.storeby,
                   filter_fn=filter_fn)
        
    datasink(options, logger, keyname, hmac_digest, sink)
    
    logger.info("Exiting program.")
    sys.exit(0)
    

if __name__ == '__main__':

    # Parse command line options
    from optparse import OptionParser
    
    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%prog'))
    optprs.add_option("-a", "--app", dest="appstr", metavar="STRING",
                      help="Specify STRING to exec on data receipt")
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-d", "--datadir", dest="datadir",
                      metavar="DIR", default='.',
                      help="Specify DIR to store FITS files")
    optprs.add_option("--detach", dest="detach", default=False,
                      action="store_true",
                      help="Detach from terminal and run as a daemon")
    optprs.add_option("-f", "--keyfile", dest="keyfile", metavar="NAME",
                      help="Specify authorization key file NAME")
    optprs.add_option("--filter", dest="filter", metavar="REGEX",
                      help="Specify REGEX filter for files")
    optprs.add_option('-g', "--gen2host", dest="host", metavar="NAME",
                      default='localhost',
                      help="Specify NAME for a Gen2 host")
    optprs.add_option("--interval", dest="interval", type="int",
                      default=60,
                      help="Registration interval in SEC", metavar="SEC")
    optprs.add_option("-k", "--key", dest="key", metavar="KEY",
                      help="Specify authorization KEY")
    optprs.add_option("--kill", dest="kill", default=False,
                      action="store_true",
                      help="Kill running instance of datasink")
    optprs.add_option("--log", dest="logfile", metavar="FILE",
                      help="Write logging output to FILE")
    optprs.add_option("--loglevel", dest="loglevel", metavar="LEVEL",
                      type="int", default=logging.INFO,
                      help="Set logging level to LEVEL")
    optprs.add_option("--loglimit", dest="loglimit", metavar="NUM",
                      type="int", default=200*1024*1024,
                      help="Set logging limit to NUM bytes before rollover")
    optprs.add_option("--mountmangle", dest="mountmangle", 
                      help="Specify a file prefix transformation for NFS copies")
    optprs.add_option("--md5check", dest="md5check", action="store_true",
                      default=False,
                      help="Check/calculate MD5 sums on files")
    optprs.add_option("--pass", dest="passphrase",
                      help="Specify authorization pass phrase")
    optprs.add_option('-p', "--passfile", dest="passfile", 
                      help="Specify authorization pass phrase file")
    optprs.add_option("--pidfile", dest="pidfile", metavar="FILE",
                      help="Write process pid to FILE")
    optprs.add_option("--port", dest="port", type="int", default=15003,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--stderr", dest="logstderr", default=False,
                      action="store_true",
                      help="Copy logging also to stderr")
    optprs.add_option("--pullhost", dest="pullhost", metavar="NAME",
                      default='localhost',
                      help="Specify NAME for a file transfer host")
    optprs.add_option("--pullport", dest="pullport", 
                      help="Specify PORT for a file transfer port",
                      metavar="PORT")
    optprs.add_option("--pullmethod", dest="pullmethod",
                      default='ftps',
                      help="Use METHOD (ftp|ftps|sftp|http|https|scp|copy) for transferring FITS files")
    optprs.add_option("--pullname", dest="pullname", metavar="USERNAME",
                      default='anonymous',
                      help="Login as USERNAME for ftp/ssh transfers")
    optprs.add_option("--storeby", dest="storeby", metavar="NAME",
                      help="Store by propid|inst")
    optprs.add_option("--workers", dest="workers", metavar="NUM",
                      type="int", default=4,
                      help="Specify number of work threads")
    optprs.add_option("--xferlog", dest="xferlog", metavar="FILE",
                      default="/dev/null",
                      help="Specify log file for transfers")

    (options, args) = optprs.parse_args(sys.argv[1:])

    # Write out our pid
    if options.pidfile:
        pidfile = options.pidfile
    else:
        pidfile = ('/tmp/datasink_%d.pid' % (options.port))

    if options.detach:
        import myproc
        
        print "Detaching from this process..."
        sys.stdout.flush()
        try:
            try:
                logfile = ('/tmp/datasink_%d.log' % (options.port))
                child = myproc.myproc(main, args=[options, args],
                                      pidfile=pidfile, detach=True,
                                      stdout=logfile,
                                      stderr=logfile)
                child.wait()

            except Exception, e:
                print "Error detaching process: %s" % (str(e))

            # TODO: check status of process and report error if necessary
        finally:
            sys.exit(0)

    if options.kill:
        try:
            try:
                pid_f = open(pidfile, 'r')
                pid = int(pid_f.read().strip())
                pid_f.close()

                print "Killing %d..." % (pid)
                os.kill(pid, signal.SIGKILL)
                print "Killed."

            except IOError, e:
                print "Cannot read pid file (%s): %s" % (
                    pidfile, str(e))
                sys.exit(1)

            except OSError, e:
                print "Error killing pid (%d): %s" % (
                    pid, str(e))
                sys.exit(1)
                
        finally:
            sys.exit(0)

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

#!/usr/bin/env python
#
# anasink.py -- a program to receive FITS data from Gen2
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Jan 28 15:55:49 HST 2010
#]
#
"""
A program to receive FITS frames from the Gen2 system.

This program (by itself) shouldn't require anything other than a standard
Python installation.  Feedback and bug fixes welcome (ocs@naoj.org)


## START anasink
 $ /usr/local/bin/python /home/builder/Svn/python/Gen2/client/anasink.py -a fitsviewer -d /data --nomd5check --detach
 or 
 # /etc/init.d/Gen2_anasink start


## TERMINATE anasink
 $ /usr/local/bin/python /home/builder/Svn/python/Gen2/client/anasink.py --kill 
 or 
 # /etc/init.d/Gen2_anasink stop


## SWITCH to gen2 sim or sum when anasink is running as daemom
 # type python or ipython on your terminal
 $ipython
 In [1]: import xmlrpclib
 In [2]: s = xmlrpclib.ServerProxy('http://hana:15003') # hana or ana
 In [3]: s.set_gen2host('simulator') # set to gen2 simulator(g2b3)
 In [3]: s.set_gen2host('summit') # set to gne2 summit(g2s3) 


## LOGS
 anasink log file: /var/log/anasink.log
 anasink pid file: /var/run/anasink_XXXX.pid  XXXX is a port number
 ftp log file: /tmp/FTP.log


$ anasink.py --help

will show all available options.
"""

import logging.handlers
import Queue

import remoteObjects as ro
import SOSS.SOSSrpc as SOSSrpc
from datasink import *

LOG_FORMAT = '%(asctime)s | %(levelname)1.1s | %(filename)s:%(lineno)d | %(message)s'

version = "20091227.0"

# Chose type of authorization encryption 
#digest_algorithm = hashlib.sha1

class AnaSink(DataSink):

    #global initialized
    def __init__(self, logger, datadir, appstr, notify_thread=False,
                 md5check=True, pullhost='localhost', pullmethod='ftp',
                 pullname=None, forking=False, ftplog='/dev/null', 
                 queue=None, ev_queue=None):

        self.appstr=appstr

        # used to change gen2 sum or sim when datasink is running as a daemon 
        self._queue=queue
        self.ev_queue=ev_queue
   

                
        super(AnaSink, self).__init__(logger, datadir,
                                      notify_fn=self.launch_app,
                                      notify_thread=notify_thread,
                                      md5check=md5check, pullhost=pullhost,
                                      pullmethod=pullmethod,
                                      pullname=pullname, forking=forking, ftplog=ftplog)


    def transfer_file(self, filepath, host, newpath,
                      transfermethod='ftp', username='anonymous'):

        self.logger.info("transfer fits: %s <-- %s" % (newpath, filepath))
        (directory, filename) = os.path.split(filepath)

        if transfermethod == 'ftp':
            
            self.logger.info("Request to transfer file '%s' via FTP" % filename)
            # passwords are assumed to be in .netrc
            cmd = ("su - daqusr  -c '/usr/sfw/bin/wget --tries=5 --waitretry=1 -O %s -a %s --user=%s ftp://%s/%s'" % (
                newpath, self.ftplog, username, host, filepath))

            #cmd = ("su - daqusr  -c '/usr/sfw/bin/wget --tries=5 --waitretry=1 -O %s -a /tmp/FTP.log --user=%s ftp://%s/%s'" % (
            #    newpath, username, host, filepath))
        else:
            self.logger.info("Request to transfer file '%s' via SSH" % filename)
            # passwordless scp is assumed to be setup
            cmd = ("scp %s@%s:%s %s" % (username, host, filepath, newpath))

        try:
            self.logger.info(cmd)
            res = os.system(cmd)

        except OSError, e:
            raise SinkError("Failed to FTP/SCP fits file '%s': %s" % (filename, str(e)))

        if res != 0:
            raise SinkError("Failed to FTP/SCP fits file '%s': exit err=%d" % (filename, res))


    def put_queue(self, host):
        try:
            self.logger.debug('putting hostname into queue. host<%s>' %host)
            self._queue.put_nowait(host)
        except Queue.Full, e:
            self.logger.error('Queue is full. Try again... <%s>' %str(e))
            #raise SinkError('Queue is full. <%s>' %e)  

    def set_gen2host(self, gen2):
        if gen2 == 'summit':
            self.logger.debug('setting gen2 host<%s>' %gen2)
            self.pullhost='g2b1'
            self.put_queue('g2s3')
            self.ev_queue.set()
              
        elif gen2 == 'simulator':
            self.logger.debug('setting gen2 host<%s>' %gen2)
            self.pullhost='g2sim'
            self.put_queue('g2sim')
            self.ev_queue.set()
        else:
            raise SinkError("Specify gen2 as either summit or simulator :<%s>" %(gen2))
        return ro.OK

    def _change_ownership(self, filepath, propid):
        ''' change the owner of a file'''      
        self.logger.debug('changing the owner filepath<%s> propid<%s> ' %(filepath, propid))
 
        try:
            # the owner of fits under /data/oXXXXX is daqusr:oXXXXX
            os.system('chown daqusr:%s %s' %(propid,filepath)) 
        except OSError, e:
            self.logger.error('changeing the owner error<%s>' %e)
            #raise SinkError('changing ownership error')

    
    def launch_app(self, filepath, filetype, propid):
        ''' display an image on fits-viewer '''

        self._change_ownership(filepath, propid)
        try:
            self.logger.debug('Calling display_fits(%s)' %filepath )
            self.appstr.display_fitsfile(filepath)
        except Exception,e:
            self.logger.error("Calling display_fits error: <%s>" %(e))
        
      
#    def change_datadir(self, propid):
#        ''' change data dir for archive'''
#        self.propid=propid
#        self.logger.debug('changing data-dir propid<%s>' %self.propid)
#        self.datadir= os.path.join('/data', self.propid)
#        self.logger.debug('changing data-dir newpath <%s>' %(self.datadir))
#        #return self.datadir    
#        return ro.OK



def datasink(options, logger, keyname, hmac_digest, sink, queue, ev_queue):

    # Create server
    server = SimpleXMLRPCServer(('', options.port))
    server.register_function(sink.ro_echo)
    server.register_function(sink.receive_data)
    server.register_function(sink.notify_data)
    server.register_function(sink.set_gen2host)

    ev_quit = threading.Event()
   
    try:
        myip = get_myip()
        
    except Exception, e:
        raise SinkError("Cannot get my IP address: %s" % (str(e)))

    def get_handles(host):
        logger.debug("Getting handle to session manager...")
        try:
            sessmgr= getHandle('sessions', host, 7075)
            return sessmgr 

        except Exception, e:
            raise SinkError("Cannot get handle to session mgr: %s" % (str(e)))
            return None

    def register_loop():
        initialized = False
        sink.put_queue(options.host)
        while not ev_quit.isSet():
            # Register ourselves with session manager
            try:
                host=queue.get_nowait()
                sessmgr = get_handles(host)
                logger.debug('session mgr hostname<%s>' %host) 
                initialized =True
                ev_queue.clear()
            except Queue.Empty, e:
                pass          
  
            if initialized:
                logger.debug('Registering ana sink...')
                try:
                    sessmgr.register_datasink((myip, options.port), keyname, hmac_digest)
                except:
                    logger.debug("can't register")
                    pass    
         
            cleanup_children()
            
            ev_queue.wait(options.interval)
            #ev_quit.wait(options.interval)


        try:
            if initialized:
                logger.debug("Unregistering ana sink...")
                sessmgr.unregister_datasink((myip, options.port), keyname,
                                            hmac_digest)
        except Exception, e:
            logger.warn("Unregister error: %s" % (str(e)))

    # Start a thread to register every so often
    t1 = threading.Thread(target=register_loop, args=[])
    t1.start()
    
    # Start server and wait for callbacks
    try:
        logger.info("Starting data interface service...")
        try:
            server.serve_forever()
            
        except KeyboardInterrupt:
            logger.error("Caught keyboard interrupt!")

    finally:
        logger.info("Data service shutting down...")
        ev_quit.set()
        ev_queue.set()
        t1.join()


def main(options, args):

    # Create top level logger.
    logger = logging.getLogger('anasink')
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(LOG_FORMAT)
        
    if options.logfile:
        fileHdlr  = logging.handlers.RotatingFileHandler(filename=options.logfile,maxBytes=10000000,backupCount=4)
        fileHdlr.setFormatter(fmt)
        fileHdlr.setLevel(options.loglevel)
        logger.addHandler(fileHdlr)
    # Add output to stderr, if requested
    if options.logstderr or (not options.logfile):
        stderrHdlr = logging.StreamHandler()
        stderrHdlr.setFormatter(fmt)
        stderrHdlr.setLevel(options.loglevel)
        logger.addHandler(stderrHdlr)

    try:
        localhost = SOSSrpc.get_myhost(short=True)
        options.keyfile="/home/builder/bin/%s.key" %localhost
        options.passfile="/home/builder/bin/%s.pass" %localhost
        logger.debug('fetching a host name by calling get_myhost func key<%s> pass<%s>' %(options.keyfile, options.passfile))
    except Exception,e:
        try:
            options.keyfile="/home/builder/bin/%s.key" %os.environ['HOSTNAME']
            options.passfile="/home/builder/bin/%s.pass" %os.environ['HOSTNAME']
            logger.debug('fetching host name from environ key<%s>  pass<%s>' %(options.keyfile, options.passfile))  
        except KeyError,e:
            logger.error('fetching host name error<%s>' %e) 
            sys.exit(1)  
   
#    if options.detach:
#        try:
#            options.keyfile="/home/builder/bin/%s.key" %os.environ['HOST']
#            options.passfile="/home/builder/bin/%s.pass" %os.environ['HOST']
#            logger.debug('fetching host name from environ key<%s> pass<%s>' %(options.keyfile, options.passfile))  
#        except KeyError,e:
#            logger.error('fetching host name error; set HOST env either ana or hana<%s>' %e)
#            sys.exit(1)  
    

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


    if options.gen2host == 'summit':
        logger.debug('setting gen2 host<%s>' %options.gen2host)
        options.pullhost='g2b1'
        options.host='g2s3'
        options.pullname='gen2'
    elif options.gen2host == 'simulator':
        logger.debug('setting gen2 host<%s>' %options.gen2host)
        options.pullhost='g2sim'
        options.host='g2sim'
        options.pullname='gen2' 
    else:
        logger.warn('you need to specify host, pullhost, and pullname')
        sys.exit(1)
 
    if options.appstr == 'fitsviewer':
        
        try:
            ro.init()
            options.appstr = ro.remoteObjectClient('localhost', 22020, auth=('fitsview_ana', 'fitsview_ana')) 
        except ro.remoteObjectError, e:
            logger.error("Error initializing remote objects subsystem: %s" % str(e))
            sys.exit(1)

    # Compute hmac
    hmac_digest = hmac.new(key, passphrase, digest_algorithm).hexdigest()

    queue = Queue.Queue(1)
    ev_queue = threading.Event()
    
    sink = AnaSink(logger, options.datadir, options.appstr,
                   notify_thread=True, md5check=options.md5check,
                   pullhost=options.pullhost, pullmethod=options.pullmethod,
                   pullname=options.pullname, forking=options.dofork,
                   ftplog=options.ftplog, queue=queue, ev_queue=ev_queue)
      
  
    datasink(options, logger, keyname, hmac_digest, sink, queue, ev_queue)
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
    optprs.add_option("--fork", dest="dofork", default=False,
                      action="store_true",
                      help="Fork process when storing/transferring files")
    optprs.add_option("-f", "--keyfile", dest="keyfile", metavar="NAME",
                      help="Specify authorization key file NAME")
    optprs.add_option("--gen2host", dest="gen2host", metavar="NAME",
                      default='summit',
                      help="Specify either gen2 summit or simulator. [summit|simulator]")
    optprs.add_option("--host", dest="host", metavar="NAME",
                      default='g2b3.subaru.nao.ac.jp',
                      help="Specify Gen2 host for retrieving data")
    optprs.add_option("--interval", dest="interval", type="int",
                      default=60,
                      help="Registration interval in SEC", metavar="SEC")
    optprs.add_option("-k", "--key", dest="key", metavar="KEY",
                      help="Specify authorization KEY")
    optprs.add_option("--kill", dest="kill", default=False,
                      action="store_true",
                      help="Kill running instance of datasink")
    optprs.add_option("--ftplog", dest="ftplog", metavar="FILE",
                      default='/dev/null',
                      help="Write ftp logging output to FILE")
    optprs.add_option("--log", dest="logfile", metavar="FILE",
                      #default='/var/log/anasink.log',
                      help="Write logging output to FILE")
    optprs.add_option("--loglevel", dest="loglevel", metavar="LEVEL",
                      type="int", default=logging.INFO,
                      help="Set logging level to LEVEL")
    optprs.add_option("--nomd5check", dest="md5check", action="store_false",
                      default=True,
                      help="Suppress MD5 checks for speed")
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
    optprs.add_option("--pullmethod", dest="pullmethod",
                      default='ftp',
                      help="Use METHOD (ftp|ssh) for transferring FITS files")
    optprs.add_option("--pullname", dest="pullname", metavar="USERNAME",
                      default='anonymous',
                      help="Login as USERNAME for ftp/ssh transfers")

    (options, args) = optprs.parse_args(sys.argv[1:])

    # Write out our pid
    if not options.pidfile:
        options.pidfile=('/var/run/anasink_%d.pid' % (options.port))

    if options.detach:
        import myproc
        
        print "Detaching from this process..."
        sys.stdout.flush()
        try:
            try:
                
                logfile = '/dev/null'
                #logfile = ('/var/log/anasink_%d.log' % (options.port))
                child = myproc.myproc(main, args=[options, args],
                                      pidfile=options.pidfile, detach=True,
                                      stdout=logfile,
                                      stderr=logfile)
                 
                child.wait()

            except Exception, e:
                print "Error detaching process: %s" % (str(e))

            # TODO: check status of process and report error if necessary
        finally:
            sys.exit(0)

    if options.kill:
     
        #exit(options.pidfile)

        try:
            try:
                pid_f = open(options.pidfile, 'r')
                pid = int(pid_f.read().strip())
                pid_f.close()

                print "Killing %d..." % (pid)
                os.kill(pid, signal.SIGKILL)
                print "Killed."

            except IOError, e:
                print "Cannot read pid file (%s): %s" % (
                    options.pidfile, str(e))
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

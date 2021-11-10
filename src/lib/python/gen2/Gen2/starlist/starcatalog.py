#!/usr/bin/env python

import os
import sys
import threading
import signal

import ssdlog

import starlist
import starselection
import remoteObjects as ro
import Task

class StarCatalog(object):

    def __init__(self, dbhost, logger, threadpool):
           
        self.catalog=starlist.CatalogSearch(dbhost, logger, threadpool)
        self.star=starselection.StarSelection(logger)

        self.kargs=None
        self.logger=logger

    def search_starlist(self, kargs):

        self.logger.debug('start searching....')
        try:
            catalog = kargs['catalog']
            self.logger.debug('found catalog keyword...')
            res = self.get_starlist(ra=kargs['ra'], dec=kargs['dec'], \
                                    fov=kargs['fov'], lowermag=kargs['lowermag'], \
                                    uppermag=kargs['uppermag'], catalog=catalog)
        except KeyError:
            self.logger.debug('no catalog keyword. use all catalogs...')
            res = self.get_starlist(ra=kargs['ra'], dec=kargs['dec'], \
                                    fov=kargs['fov'], lowermag=kargs['lowermag'], \
                                    uppermag=kargs['uppermag'])
        finally:
            return res

    def get_starlist(self, ra, dec, fov, lowermag, uppermag, catalog='usnob,gsc,sao'):
        ''' search star catalog and return the list of stars '''
 
        self.logger.debug('getting stars from db.')
        res=self.catalog.search_starcatalog(ra, dec, fov, lowermag, uppermag, catalog)
        return res

    def get_lower_upper_mag(self, limitmag):
        ''' get lower/upper mag '''
  
        lowermag=uppermag=None   

        if limitmag > 0:
            uppermag=limitmag
            lowermag=0.0
        else:
            uppermag=limitmag
            lowermag=0.0    

        #self.logger.debug('min_mag=%s max_mag=%s' %(str(min_mag), str(max_mag)))
        return (lowermag, uppermag)  

    def select_sh_stars(self,kargs):
        ''' key args for sh are {ra:n dec:n fov:n, limitmag=13.0}  
            limitmag=13.0 is fixed value for sh auto select
            ra, dec, fov in degrees '''
      
        self.logger.debug('starting sh_auto_selcet...')

        lowermag, uppermag = self.get_lower_upper_mag(kargs['limitmag'])
        starlist=self.get_starlist(ra=kargs['ra'], dec=kargs['dec'], \
                                   fov=kargs['fov'], \
                                   lowermag=lowermag, uppermag=uppermag)
        ''' starlist is list of dictinaries 
            [{'name':'UB0687-0042169', 'ra':58,4, 'dec':-21.22, 
              'mag':11.3, 'flag':7, 'b_r':9.3, 'r_i':-11.5},
             {...}]
        '''

        self.logger.debug('filtering sh stars...')
        sh_stars=self.star.select_sh_stars(kargs=kargs, starlist=starlist)    
        ''' sh_stars is list of dictinaries ordered by priority 
            {'name':'UB1100-0008258','ra': '9.994380', 
             'dec''20.067200', 'mag':'19.300000', 'flag':'4', 
             'b_r':'0.600000', 'preference':'-1.300000', 
             'priority':'30', 'dst':'4.044432'},
            {...}]
            note dst is in degree 
        '''
        return sh_stars

    def select_ag_stars(self, kargs):
        ''' key args for sh are 
            {'ra':10.0, 'dec':20.0, 'fov':0.076, 'probe_ra':10.0, 
             'probe_dec':20.0, 'focus':'CS', 'ins':'MOIRCS',  
             'probe_r':0.0, 'probe_theta':0.0, 'probe_x':0.0, 'probe_y':0.0,  
             'pa':0.0, 'limitmag':21.0, 'goodmag':10.0, 'fov_pattern':'STANDARD'}
            note: ra, dec, fov, prboe_ra, probe_dec, pa are in degrees
        '''

        self.logger.debug('starting ag_auto_selcet...')
        lowermag, uppermag = self.get_lower_upper_mag(kargs['limitmag'])
        starlist=self.get_starlist(ra=kargs['ra'], dec=kargs['dec'], \
                                   fov=kargs['fov'], lowermag=lowermag, \
                                   uppermag=uppermag)

        self.logger.debug('filtering ag stars...')
        ag_stars=self.star.select_ag_stars(kargs=kargs, starlist=starlist)
        ''' ag_stars is list of dictinaries 
            [{'name':'UB1100-0008258','ra': '9.994380', 'dec''20.067200', 
              'mag':'19.300000', 'flag':'4', 'b_r':'0.600000', 
              'preference':'-1.300000', 'priority':'30', 'dst':'4.044432'}, 
             {...}]
        # note: dst is in min
        '''
        return ag_stars

def main(options, args):

    logname = 'star_catalog'
    # Create top level logger.
    logger = ssdlog.make_logger(logname, options)
 
    # Initialize remote objects subsystem.
    try:
        ro.init()
    except ro.remoteObjectError, e:
        logger.error("error: initializing remote objects subsystem: %s" % str(e))
        sys.exit(1)

    # Global termination flag
    ev_quit = threading.Event()

    def quit():
      
        logger.debug('quitting...')
        ev_quit.set()
        try:
            logger.debug('stoping remoteobject...')
            svc.ro_stop(wait=False) 
        except Exception:
            pass

    def SigHandler(signum, frame):
        """Signal handler for all unexpected conditions."""
        logger.error('Received signal %d' % signum)
        quit()

    # Set signal handler for signals
#    signal.signal(signal.SIGINT, SigHandler)
    signal.signal(signal.SIGTERM, SigHandler)
    try:
        threadpool = Task.ThreadPool(logger=logger, ev_quit=ev_quit, numthreads=20)
        threadpool.startall(wait=True)
        starcat=StarCatalog(dbhost=options.dbhost, logger=logger, threadpool=threadpool)
     
        # sh_keys={'ra':10.1, 'dec':10.0, 'fov':0.076, 'limitmag':13.0}
        # ag_keys={'ra':10.0, 'dec':20.0, 'fov':0.076, 'probe_ra':10.0, 'probe_dec':20.0, 'focus':'CS', 'ins':'MOIRCS',  'probe_r':0.0, 'probe_theta':0.0, 'probe_x':0.0, 'probe_y':0.0,  'pa':0.0, 'limitmag':15.0, 'goodmag':10.0, 'fov_pattern':'STANDARD'}
        
        # starcat.select_sh_stars(sh_keys)
        #starcat.select_ag_stars(ag_keys)

#        svr_started = False 
        svc = ro.remoteObjectServer(svcname=options.svcname,
                                    obj=starcat, logger=logger,
                                    port=options.port,
                                    default_auth=None,
                                    ev_quit=ev_quit,
                                    usethread=False,)
        
        svc.ro_start(wait=True)
#        svr_started = True

    except KeyboardInterrupt:
        print 'keyboard interrupting...'  
        quit()
    except Exception as e:
        logger.error('error: starting svc.  %s' %str(e))
        quit()

        
if __name__ == "__main__":
    
    import sys
    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog -r 0 -d 0 -f 0 -l 10"
    parser = OptionParser(usage=usage, version=('%prog'))

    parser.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")

    parser.add_option("--svcname", dest="svcname", metavar="NAME",
                      default="starcatalog",
                      help="Register using NAME as service name")
    parser.add_option("--port", dest="port", type="int", default=None,
                      help="Register using PORT", metavar="PORT")
    
    parser.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    parser.add_option("--dbhost", dest="dbhost",
                      default='g2db',
                      help="Specify DB host")    
    
    ssdlog.addlogopts(parser)
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

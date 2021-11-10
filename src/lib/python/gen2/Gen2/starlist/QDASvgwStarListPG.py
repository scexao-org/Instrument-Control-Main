#!/usr/bin/env python

import time
import math
import types
import threading
import astro.radec as radec
import Bunch
import ssdlog, logging
import psycopg2  # python-postgres db adaptor
from antipool import ConnectionPool

# user gen2 is granted for select statement only; no other sql statement is permitted 
conn_pool = ConnectionPool(psycopg2, host='g2s1', database='star_catalog', \
                           user='gen2', password='gen2', port=9999)

def get_connection(logger):
    
    got_connection = False
    while not got_connection:
        try:
            conn = conn_pool.connection()
            cur = conn.cursor()
            got_connection = True
        except psycopg2.OperationalError, mess:
            logger.error('get_connection operational error<%s>' %(str(mess)))
            # Might log exception here
            time.sleep(1)
        except AttributeError, mess:
            logger.error('get_connection attribute error<%s>' %(str(mess)))
            # Might log exception here
            time.sleep(1)
    return conn, cur


def get_min_max_mag(limitmag):
    ''' get min/max value of mag '''
    
    if limitmag > 0:
        max_mag=limitmag
        min_mag=0
    else:
        min_mag=limitmag
        max_mag=0    
    return (min_mag, max_mag)  

def get_ra_dec(pos):
    
    pos=pos[1:-1].split(',')
    try:
        ra=math.degrees(float(pos[0].strip()))
        dec=math.degrees(float(pos[1].strip()))
        return (ra,dec)
    except:
        print 'error' 


#class Stars(object):
#    __slots__=['name', 'ra_deg', 'dec_deg', 'ra_rad', 'dec_rad', 'mag', 'flag']
  
NS=0  
  
class StarList(object):
    
    def __init__(self):
        self.stars=[]
   
    def setstar(self, name,ra, dec, mag, flag, b_r, r_i):
        '''  make usnob star dictionary  '''
        KEYS=['NAME', 'RA', 'DEC', 'MAG', 'FLAG', 'B_R', 'R_I']
        self.stars.append( dict( zip(KEYS, [name, ra, dec, mag, flag, b_r, r_i] ))  )
     
    def __iter__(self):
        return self
   
    def next(self):
        if len(self.stars) == 0:    # threshhold terminator
            raise StopIteration     # end of iteration
        else:                       # look for usable candidate
            res = self.stars.pop(0)
            return Bunch.Bunch(name=res['NAME'], ra=res['RA'], dec=res['DEC'], mag=res['MAG'], flag=res['FLAG'],  b_r=res['B_R'], r_i=res['R_I'])

 
class USNOB(object):
            
    def __init__(self, starlist, logger):
        self.stars = starlist
        self.logger = logger 
 
    def search_USNOB(self, ra,dec,fov,limitmag):
        """ query USNOB star catalog"""
        
        global NS
        
        conn, cur= get_connection(self.logger)
       
        min_mag,max_mag=get_min_max_mag(limitmag)
        
        where_cluse = "where pos @ scircle'<(%sd, %sd), %sd>' and r1mag between %s and %s " %( str(ra), str(dec), str(fov), str(min_mag), str(max_mag) )
       
        sql_statement= """ select pool_parallel("select name,pos, b1mag, b2mag, r1mag, r2mag, imag, flagsgb1, flagsgb2, flagsgr1, flagsgr2 from usnob %s ") """  %(where_cluse) 
     
        c=0
        try:
            try:
                self.logger.debug("executing usnob sql<%s>" %(sql_statement) )
                cur.execute (sql_statement)
                rows = cur.fetchall()
                              
                for name, pos, b1mag, b2mag, r1mag, r2mag, imag, flagsgb1, flagsgb2, flagsgr1, flagsgr2 in rows:
                    c=c+1   
                    ra,dec=get_ra_dec(pos)
                                               
                    bmag=self._get_usnob_mag(b1mag,b2mag)
                 
                    rmag=self._get_usnob_mag(r1mag,r2mag)
                                   
                    if imag > 25.0: imag=99.9
                                       
                    ''' flag is to identify star '''
                    flag= self._get_usnob_flag( flagsgb1, flagsgb2, flagsgr1, flagsgr2)
                    b_r=self._get_usnob_blue_red_mag(bmag, rmag)
                    r_i=self._get_usnob_blue_red_mag(imag, rmag)
        
                    self.stars.setstar(name, ra, dec, rmag, flag, b_r, r_i)
            except:
                self.logger.error('usnob query error')
     
        finally:
            conn.release()
            self.logger.debug("connection to usnob released")
            NS=NS+c
   
    def _get_usnob_blue_red_mag(self, mag1, mag2):
        if mag1 < 99.9 and mag2 < 99.9:
            mag = mag1-mag2
        else:
            mag = 99.9
        
        return mag
           
    def _get_usnob_flag(self, flagb1, flagb2, flagr1, flagr2 ):
             
        if flagr1 <= 11 and flagr2 <= 11:   flag=(flagr1+flagr2)//2.0
        elif flagr1 > 11 and flagr2 <= 11:  flag=flagr2
        elif flagr1 <= 11 and flagr2 > 11:  flag=flagr1
        else:
            if flagb1 <= 11 and flagb2 <= 11:   flag=(flagb1+flagb2)//2.0
            elif flagb1 > 11 and flagb2 <= 11:  flag=flagb2
            elif flagb1 <= 11 and flagb2 > 11:  flag=flagb1
            else:                               flag=0
       
        '''  Transforming Flag to Classical USNO-A1.0 Yasuda Version  '''
        if flag <= 11 and flag >=8:   flag=1
        elif flag <= 3 and flag >=0:  flag=7
        else:                         flag=10-flag
        
        return flag
    
    def _get_usnob_mag(self, mag1, mag2):
        if mag1 > 25.0 and mag2 > 25.0:
            mag=99.9
        elif mag1 > 25.0 and mag2 <= 25.0:
            mag=mag2
        elif mag1 <= 25.0 and mag2 > 25.0:
            mag=mag1
        else:
            mag=(mag1+mag2)/2.0
            
        return mag                          

class GSC(object):
        
    def __init__(self, starlist, logger):
        self.stars = starlist
        self.logger = logger 
            
    def search_GSC(self, ra,dec,fov,limitmag):
        
        global NS

        conn, cur= get_connection(self.logger)
       
        min_mag,max_mag=get_min_max_mag(limitmag)
        
        where_cluse = "where pos @ scircle'<(%sd, %sd), %sd>' and mag between %s and %s " %( str(ra), str(dec), str(fov), str(min_mag), str(max_mag) )
       
        sql_statement= """ select pool_parallel("select name,pos,mag,class from gsc %s ") """  %(where_cluse) 
     
        c=0
        try:
            try:
                self.logger.debug("executing gsc sql<%s>" %(sql_statement) )
                cur.execute (sql_statement)
                rows = cur.fetchall()
                
                for name, pos, mag, cl in rows:
                    c=c+1
                    ra,dec=get_ra_dec(pos)
                    '''  calculate flag value  '''
                    flag=self._get_gsc_flag(cl)
            
                    ''' flag 99.0s are fixed values fro gsc'''
                    self.stars.setstar(name, ra, dec, mag, flag, 99.9, 99.0 )
            except:
                self.logger.error('gsc query error')
       
        finally:
            conn.release()
            self.logger.debug("connection to gsc released")
            NS=NS+c
 
    
    def _get_gsc_flag(self,flag):
        
        if flag==0:    return 2    
        elif flag==3:  return -1
        else:          return -9 
      
class SAO(object):
    
    
    def __init__(self, starlist, logger):
        self.stars = starlist
        self.logger = logger 
        
    def search_SAO(self,ra, dec, fov, limitmag):
        ''' query SAO star catalog and set results in a dictionary '''
        
        global NS
         
        conn, cur= get_connection(self.logger)
       
        min_mag,max_mag=get_min_max_mag(limitmag)
        
        where_cluse = "where pos @ scircle'<(%sd, %sd), %sd>' and mag between %s and %s " %( str(ra), str(dec), str(fov), str(min_mag), str(max_mag) )
       
        sql_statement= """ select pool_parallel("select name,pos,mag,type from sao %s ") """  %(where_cluse) 
     
        c=0 
        try:
            try:
                self.logger.debug("executing sao sql<%s>" %(sql_statement) )
                cur.execute (sql_statement)
                rows = cur.fetchall()
                     
                for name,pos,mag,typ in rows:
                    c=c+1
                    ra,dec=get_ra_dec(pos)
                            
                    ''' get flag value  '''
                    flag=self._get_sao_flag(typ)
                    
                    ''' 2 and 99.9 are fixed flag for sao '''
                    self.stars.setstar(name, ra, dec, mag, 2, flag, 99.9)
            except:
                self.logger.error('sao query error')
                print 'report sql sao error'
        finally:
            conn.release()
            self.logger.debug("connection to sao released")
            NS=NS+c        
 
    
    def _get_sao_flag(self,typ):
        ''' based on star type, 
            set return flag to identify a star '''
        if   typ.startswith('A'):  return 0.1
        elif typ.startswith('B'):  return -0.2
        elif typ.startswith('O'):  return -0.4
        elif typ.startswith('F'):  return 0.4
        elif typ.startswith('G'):  return 0.6
        elif typ.startswith('K'):  return 1.1
        elif typ.startswith('M'):  return 1.5
        else:                      return 0.0


class StarCatalog(USNOB,GSC, SAO):
    
    def __init__(self, logger):
        self.logger = logger        
        self.starlist=StarList()
       
        self.usnob=USNOB(self.starlist, self.logger)
        self.gsc=GSC(self.starlist, self.logger)
        self.sao=SAO(self.starlist, self.logger)
            
    def search_starCatalog(self, ra, dec, fov, limitmag, star_catalog='usnob,gsc,sao'):
       
                    
        catalog_thread=[]
       
        self.logger.debug("catalog query starts")
        self._start_thread(ra, dec, fov, limitmag, star_catalog, catalog_thread)

        self._wait_thread_done(catalog_thread)
       
        return self.starlist
    

    def _wait_thread_done(self, catalog_thread):
        for thr in catalog_thread:
            thr.join()
            self.logger.debug("%s query done" %(thr))
        
    def _start_thread(self, ra, dec, fov, limitmag, star_catalog, catalog_thread):
                 
        for i in star_catalog.split(','):
            catalog=i.strip()
                          
            if catalog.lower()=='usnob':
                self.logger.debug("usnob query starts")
                #usnob_thread=threading.Thread(target=USNOB.search_USNOB, args=(self, ra, dec, fov, limitmag))
                usnob_thread=threading.Thread(target=self.usnob.search_USNOB, args=(ra, dec, fov, limitmag))
                catalog_thread.append(usnob_thread)
                usnob_thread.start() 
                #print 'main usnob thread started  '
            elif catalog.lower()=='gsc':
                self.logger.debug("gsc query starts")
                #gsc_thread=threading.Thread(target=GSC.search_GSC, args=(self, ra, dec, fov, limitmag))
                gsc_thread=threading.Thread(target=self.gsc.search_GSC, args=(ra, dec, fov, limitmag))
                catalog_thread.append(gsc_thread)
                gsc_thread.start() 
                #print 'main gsc thread started'
            elif catalog.lower()=='sao':
                self.logger.debug("sao query starts")
                sao_thread=threading.Thread(target=self.sao.search_SAO, args=(ra, dec, fov, limitmag))
                catalog_thread.append(sao_thread)
                sao_thread.start() 
                #print 'main gsc thread started'




def printoutHeader(ra, dec, fov, limitmag):
    
    global NS
    rah, ramin, rasec=radec.degToHms(ra)
    ra=radec.raHmsToString(rah, ramin, rasec, format="%02d:%02d:%06.3f")
    
    sign,dec_deg,dec_min,dec_sec=radec.degToDms(dec)
    dec=radec.decDmsToString( sign,dec_deg,dec_min,dec_sec, format='%s%02d:%02d:%05.2f' )
       
    ra_range=dec_range=fov*120
                
    print "The Skycat Interface for Subaru STAGE search system"
    print "                      By                      "
    print "Subaru Software Development Team Hilo, Hawaii\n\n"
    print "FieldCenterRA=%s"  %(ra)
    print "FieldCenterDEC=%s" %(dec)
    print "Epoch=J2000.0"
    print "FieldRangeRA(arcmin)=%5.1f" %(ra_range)
    print "FieldRangeDEC(arcmin)=%5.1f" %(dec_range)
    print "MinimumMagnitude=%4.1f" %(0.0)
    print "MaximumMagnitude=%4.1f" %(limitmag)
    print "StarNumber=%5d" %(NS)
    print "name\tRA\tDEC\tmag\tFlag\tB-R\tR-I\tPreference"
    print "----\t--\t---\t---\t----\t---\t---\t----------"


def printoutStars(starlist):
    count=0
    for star in starlist:
        count =count+1
        print ("%-17s\t%9.5f\t%9.5f\t%4.1f\t%2d\t%4.1f\t%4.1f\t%5d" %(star.name, star.ra, star.dec, star.mag, star.flag, star.b_r, star.r_i, count))

def main(options, args):
    
    logname = 'star_selection'
    # Create top level logger.
    #logger = ssdlog.make_logger(logname, options)
  
    logger = ssdlog.simple_logger(logname, level=logging.DEBUG)
    
    ra= float(options.ra)
    dec= float(options.dec)
    fov=float(options.fov)
    limitmag=float(options.limitmag)
    star_catalog=options.starcatalog
    
    stars=StarCatalog(logger)
    starlist=stars.search_starCatalog(ra, dec, fov, limitmag, star_catalog)
    printoutHeader(ra, dec, fov, limitmag)
    printoutStars(starlist)
   
        
if __name__ == "__main__":
    
    import sys
    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog -r 0 -d 0 -f 0 -l 10"
    parser = OptionParser(usage=usage, version=('%prog'))

    parser.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    
    parser.add_option("-r", "--ra", dest="ra", type="float",  
                      default=False,
                      help="RA(J2000.0) the center of a sight in degree")
    parser.add_option("-d", "--dec", dest="dec", type="float", 
                      default=False,
                      help="DEC(J2000.0) the center of a sight in degree")
    parser.add_option("-f", "--fov", dest="fov", type="float",
                      default=False,
                      help="FOV(radious) in degree")
    parser.add_option("-l", "--limitmag", dest="limitmag",
                      default=21.0,
                      help="Max mag to filter stars")
    
    parser.add_option("-s", "--starcatalog", dest="starcatalog",
                      default='usnob,gsc,sao',
                      help="star catalog to qury")
    
    parser.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
 
    
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
    
    
    
    
#    stars=StarList()
#    usnob=USNOB(stars)
#    usnob.search_USNOB(0, 0, 0.46, 13)
#    for star in stars:
#        print star.name
    
#    stars=StarCatalog()
#    starlist=stars.search_starCatalog(0.0, 0.0, 0.46, 11)
#    
#    printHeader(ra=0, dec=0, fov_radious=0.46, limitmag=21)
#    
#    count=0
#    for star in starlist:
#        count =count+1
#        print ("%-17s\t%9.5f\t%9.5f\t%4.1f\t%2d\t%4.1f\t%4.1f\t%5d" %(star.name, star.ra, star.dec, star.mag, star.flag, star.b_r, star.r_i, count))
#    
#    print NS    
#    
 

#!/usr/bin/env python
#
# starlist.py -- STAR catalog query and filter function
#
# Takeshi Inagaki
#
#

import os
import time
import math
import threading
import astro.radec as radec
import ssdlog, logging
import sqlalchemy.pool as pool
import psycopg2  # python-postgres db adaptor
psycopg2.threadsafety=30
#from antipool import ConnectionPool
#from psycopg2.pool import ThreadedConnectionPool

import Task

""" usage
    -r=RA(degree), -d=DEC(degree), -f=Field of View(degree), -l=Lower Magnitude, -u=Upper Magnitude, --dbhost=DB host, g2db(summit) or g2b3(base)

    # searching all star catalog at base. if you don't specify dbhost, default is an env value 'DBHOST'
    $python starlist.py -r 300 -d 15 -f 0.4  -l 10 -u 21 --loglevel=0 --stderr   --dbhost=g2b3

    # searching only particular starcatalog. e.g. sao is the one to be searched. 
    $python starlist.py -r 10.3 -d 0.4 -f 0.076  --lowermag=-1 --uppermag=0 --loglevel=0 --stderr --catalog=sao 

""" 

class DBConnection(object):
    """ Postgres DB connection  """

    def __init__(self, dbhost, logger ):
        dbname = 'star_catalog'
        user = 'gen2'
        passwd = 'gen2'
        port = 9999
        self.logger = logger
    
        self.logger.debug('dbhost=%s' %dbhost)

        def getconn():
            c = psycopg2.connect(dsn)
            return c

        dsn = "dbname=%s user=%s host=%s password=%s port=%d" %(dbname, user, dbhost, passwd,  port)
        self.pool = pool.QueuePool(getconn, max_overflow=20, pool_size=15)
        # user gen2 is granted for only select statement; no other sql statement is permitted 

    def establish_connection(self):
    
        conn = cur = None
        cur_time = time.time()
        timeout = cur_time+2  # 2sec to timeout

        while not cur  and cur_time < timeout:
            try:
                conn = self.pool.connect()
                cur = conn.cursor()
            except psycopg2.OperationalError as  e:
                self.logger.error('get_connection operational error<%s>' %(str(e)))
                time.sleep(0.1)
            except AttributeError as  e:
                self.logger.error('get_connection attribute error<%s>' %(str(e)))
                time.sleep(0.1)
            except Exception as e:
                time.sleep(0.1)
                self.logger.error('get_connection error<%s>' %(str(e)))
            cur_time = time.time()
        return (conn, cur)
       

class Catalog(object):
    ''' star catalog  '''
    def __init__(self, logger):

        self.keys = ['name', 'ra', 'dec', 'mag', 'flag', 'b_r', 'r_i'] 
        self.logger = logger

    def get_ra_dec(self, pos):
        ''' retreive ra and dec out of arg(pos) whose format is "(ra, dec)"  '''
        ra = dec = None

        try:
            pos = pos[1:-1].split(',')
            ra = float(pos[0])
            dec = float(pos[1])
        except Exception,e:
            self.logger.error('failed to fetch ra&dec %s' %str(e))
        return (ra,dec)

    def fetch_stars(self, cur,conn, sql_statement):
                
        rows = None
        try:
            self.logger.debug("executing sql<%s>" %(sql_statement) )
            cur.execute(sql_statement)
            rows = cur.fetchall()
        except Exception as e:
            self.logger.error('error: fetching stars from db %s' %str(e))        
        finally:
            conn.close()
            self.logger.debug("connection closed")
        
        return rows


class USNOB(Catalog):
    """ search USNOB star catalog """        
    def __init__(self, db, logger):
        super(USNOB,self).__init__(logger)
#        self.starlist=starlist
#        self.starlist=[]
#        self.append=starlist.append
        self.db = db
        self.logger = logger 

    def search(self, ra,dec,fov, lowermag, uppermag):
        """ query USNOB star catalog"""
                
        self.logger.debug('usnob searching....') 
        where_cluse = "where pos @ scircle'<(%sd, %sd), %sd>' and r1mag between %s and %s " %( str(ra), str(dec), str(fov), str(lowermag), str(uppermag) )
        sql_statement = """ select pool_parallel("select name,pos, b1mag, b2mag, r1mag, r2mag, imag, flagsgb1, flagsgb2, flagsgr1, flagsgr2 from usnob %s ") """  %(where_cluse) 

        #self.logger.debug('getting db connection') 
        conn, cur = self.db.establish_connection()
        rows = self.fetch_stars(cur, conn, sql_statement)
        self.logger.debug("usnob fetched.") 

        degrees=math.degrees
#        set_star=self.starlist.set_star
        starlist = []
        append = starlist.append
        for name, pos, b1mag, b2mag, r1mag, r2mag, imag, flagsgb1, flagsgb2, flagsgr1, flagsgr2 in rows:
              
            ra,dec = self.get_ra_dec(pos)

            bmag = self.__get_usnob_mag(b1mag,b2mag)
            rmag = self.__get_usnob_mag(r1mag,r2mag)

            if imag > 25.0: imag=99.9

            # flag is to identify star 
            flag = self.__get_usnob_flag( flagsgb1, flagsgb2, flagsgr1, flagsgr2)
            b_r = self.__get_usnob_blue_red_mag(bmag, rmag)
            r_i = self.__get_usnob_blue_red_mag(imag, rmag)

            append(dict(zip(self.keys, [name, degrees(ra), degrees(dec), rmag, flag, b_r, r_i])))

        return starlist   

    def __get_usnob_blue_red_mag(self, mag1, mag2):
        if mag1 < 99.9 and mag2 < 99.9:
            mag = mag1-mag2
        else:
            mag = 99.9
        
        return mag
           
    def __get_usnob_flag(self, flagb1, flagb2, flagr1, flagr2 ):
             
        if flagr1 <= 11 and flagr2 <= 11:
            flag = (flagr1+flagr2)//2.0
        elif flagr1 > 11 and flagr2 <= 11:
            flag = flagr2
        elif flagr1 <= 11 and flagr2 > 11:
            flag = flagr1
        else:
            if flagb1 <= 11 and flagb2 <= 11:
                flag = (flagb1+flagb2)//2.0
            elif flagb1 > 11 and flagb2 <= 11:
                flag = flagb2
            elif flagb1 <= 11 and flagb2 > 11:
                flag = flagb1
            else:
                flag = 0
       
        '''  Transforming Flag to Classical USNO-A1.0 Yasuda Version  '''
        if flag <= 11 and flag >=8:
            flag = 1
        elif flag <= 3 and flag >=0:
            flag = 7
        else:
            flag = 10-flag
        
        # not all flag values are integer format.  need to convert float to int
        return int(flag)
    
    def __get_usnob_mag(self, mag1, mag2):
        if mag1 > 25.0 and mag2 > 25.0:
            mag = 99.9
        elif mag1 > 25.0 and mag2 <= 25.0:
            mag = mag2
        elif mag1 <= 25.0 and mag2 > 25.0:
            mag = mag1
        else:
            mag = (mag1+mag2)/2.0
            
        return mag                          

class GSC(Catalog):
    """ search GSC star catalog """
    def __init__(self, db, logger):
        super(GSC,self).__init__(logger)
#        self.starlist=starlist
#        self.starlist=[]
        self.db = db
        self.logger = logger 
            
    def search(self, ra,dec,fov,lowermag, uppermag):
        """ query GSC star catalog"""       

        self.logger.debug('gsc searching....')
        where_cluse = "where pos @ scircle'<(%sd, %sd), %sd>' and mag between %s and %s " %( str(ra), str(dec), str(fov), str(lowermag), str(uppermag) )
       
        sql_statement = """ select pool_parallel("select name,pos,mag,class from gsc %s ") """  %(where_cluse) 

        conn, cur=self.db.establish_connection()
        rows = self.fetch_stars(cur, conn, sql_statement)
        self.logger.debug("gsc fetched.")

        degrees = math.degrees
#        set_star=self.starlist.set_star 
        starlist = []
        append = starlist.append
        for name, pos, mag, cl in rows:
            ra,dec=self.get_ra_dec(pos)
            flag=self.__get_gsc_flag(cl)

            # blue,red,image mag 99.9s are fixed values for gsc
            append(dict(zip(self.keys, [name, degrees(ra), degrees(dec), mag, flag, 99.9, 99.9])))  
  
        return starlist 

    def __get_gsc_flag(self,flag):
        #calculate flag value 
        if flag == 0:
            return 2    
        elif flag == 3:
            return -1
        else:
            return -9 
          
class SAO(Catalog):
    """ search SAO star catalog """
    def __init__(self, db, logger):
        super(SAO,self).__init__(logger)
#        self.starlist=starlist
#        self.starlist=[]
        self.db = db
        self.logger = logger 

    def search(self,ra, dec, fov, lowermag, uppermag):
        ''' query SAO star catalog and set results in a dictionary '''

        self.logger.debug('sao searching....')
        where_cluse = "where pos @ scircle'<(%sd, %sd), %sd>' and mag between %s and %s " %( str(ra), str(dec), str(fov), str(lowermag), str(uppermag) )
       
        sql_statement= """ select pool_parallel("select name,pos,mag,type from sao %s ") """  %(where_cluse) 

        conn, cur=self.db.establish_connection()
        rows=self.fetch_stars(cur, conn, sql_statement)
        self.logger.debug("sao fetched.")

        degrees=math.degrees   
#        set_star=self.starlist.set_star
        starlist=[]
        append = starlist.append
        for name,pos,mag, sao_type in rows:
            ra,dec = self.get_ra_dec(pos)

            # get flag value 
            flag = self.__get_sao_flag(sao_type)

            # 2 and 99.9 are fixed flag for sao '''
            append(dict(zip(self.keys, [name, degrees(ra), degrees(dec), mag, 2,  flag, 99.9])))   

        return starlist      

    def __get_sao_flag(self, sao_type):
        ''' based on star type, 
            set and return flag to identify a star '''
        if sao_type.startswith('A'):   return 0.1
        elif sao_type.startswith('B'): return -0.2
        elif sao_type.startswith('O'): return -0.4
        elif sao_type.startswith('F'): return 0.4
        elif sao_type.startswith('G'): return 0.6
        elif sao_type.startswith('K'): return 1.1
        elif sao_type.startswith('M'): return 1.5
        else:                          return 0.0

class CatalogSearch(object):
    ''' search star catalog. USNOB,GSC,SAO '''    
    def __init__(self, dbhost,  logger, threadpool):
        self.logger = logger        
        self.threadPool = threadpool
        self.tag = 'starcatalog_search'
        self.shares = ['logger', 'threadPool']

        self.db = DBConnection(dbhost, logger) 
     
#        self.starlist=StarList()
#        self.starlist=[]
        self.usnob = USNOB(self.db, logger)
        self.gsc = GSC(self.db, logger)
        self.sao = SAO(self.db, logger)
        #self.__search_star=[]

    def get_min_max_mag(self, limitmag):
        ''' get min/max value of mag '''
  
        min_mag = max_mag = None   

        if limitmag > 0:
            max_mag = limitmag
            min_mag = 0.0
        else:
            min_mag = limitmag
            max_mag = 0.0    

        #self.logger.debug('min_mag=%s max_mag=%s' %(str(min_mag), str(max_mag)))
        return (min_mag, max_mag)  
    
    def search_starcatalog(self, ra, dec, fov, lowermag, uppermag, catalog='usnob,gsc,sao'):

        #self.__search_star = []
        res = []
        try:
            task_list = self.__start_task(ra, dec, fov, lowermag, uppermag, star_catalog=catalog)
            t = Task.ConcurrentAndTaskset(task_list)
            t.init_and_start(self)
            t.wait() 
        except Exception as e:
            self.logger.error('error: fetching star catalog. %s' %str(e))
            res = []
        else:
            for t in task_list:
                #self.logger.debug('t result=%s' %t.result)
                res.extend(t.result)
        finally:
            return res 

    def __start_task(self, ra, dec, fov, lowermag, uppermag, star_catalog):
        
        cat_obj = {'usnob': self.usnob, 'gsc': self.gsc, 'sao': self.sao}
        method = 'search'
        task_list = [] 
        for catalog in star_catalog.split(','):
            catalog = catalog.strip() 
            self.logger.debug("%s thread starting..." %catalog)
            cat = cat_obj[catalog]
            #search = ("self.%s.search" %catalog)
            try:
                search = getattr(cat, method)
                #t = Task.FuncTask(eval(search), [ra, dec, fov, lowermag, uppermag], {}, logger=self.logger)
                t = Task.FuncTask(search, [ra, dec, fov, lowermag, uppermag], {}, logger=self.logger)
                task_list.append(t)
            except Exception as e:
                self.logger.error('error: starting task. %s' %str(e)) 
                continue  
         
        return task_list   

def printout(ra, dec, fov, lowermag, uppermag, starlist):
    
    rah, ramin, rasec=radec.degToHms(ra)
    ra=radec.raHmsToString(rah, ramin, rasec, format="%02d:%02d:%06.3f")
    
    sign,dec_deg,dec_min,dec_sec=radec.degToDms(dec)
    dec=radec.decDmsToString( sign,dec_deg,dec_min,dec_sec, format='%s%02d:%02d:%05.2f' )
       
    ra_range=dec_range=fov*120
    total=len(starlist)          
      
    print "Star Catalog search system"
    print "by"
    print "Subaru Software Development Team Hilo, Hawaii\n\n"
    print "FieldCenterRA=%s"  %(ra)
    print "FieldCenterDEC=%s" %(dec)
    print "Epoch=J2000.0"
    print "FieldRangeRA(arcmin)=%5.1f" %(ra_range)
    print "FieldRangeDEC(arcmin)=%5.1f" %(dec_range)
    print "MinimumMagnitude=%4.1f" %(lowermag)
    print "MaximumMagnitude=%4.1f" %(uppermag)
    print "StarNumber=%5d" %(total)
    print "name\tRA\tDEC\tmag\tFlag\tB-R\tR-I\tPreference"
    print "----\t--\t---\t---\t----\t---\t---\t----------"

    for num,star in enumerate(starlist):
        num+=1
        print "{name:17s}\t{ra:9.5f}\t{dec:9.5f}\t{mag:4.1f}\t{flag:2d}\t{b_r:4.1f}\t{r_i:4.1f}\t{0:5d}".format(num, **star)


def main(options, args):

    logname = 'star_list'
    # Create top level logger.
    logger = ssdlog.make_logger(logname, options)
 
    try:
        ra= float(options.ra)
        dec= float(options.dec)
        fov=float(options.fov)
        uppermag=float(options.uppermag)
        lowermag=float(options.lowermag)
    except Exception as e:
        print 'need args.  %s' %str(e)
        sys.exit(1)
    
    if lowermag >= uppermag:
        print 'upper mag should be greater than lower mag'
        sys.exit(1)

    catalog=options.catalog

    if options.dbhost:
        dbhost=options.dbhost
    else:
        try:
            dbhost=os.environ['DBHOST']
        except KeyError,e:
            dbhost='g2db'

    logger.debug('DB host=%s' %os.environ['DBHOST'])
 
    try:
        cat=CatalogSearch(dbhost, logger)
        #min_mag, max_mag=cat.get_min_max_mag(options.limitmag)
        starlist=cat.search_starcatalog(ra, dec, fov, lowermag, uppermag, catalog)
        #starlist=cat.usnob.starlist+cat.gsc.starlist+cat.sao.starlist
        printout(ra, dec, fov, lowermag, uppermag, starlist)

    except KeyboardInterrupt:
        print 'keyboard interrupting...'  
    except Exception as e:
        logger.error('error: executing catalog search.  %s' %str(e))
 
        
if __name__ == "__main__":
    
    import sys
    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog -r 0 -d 0 -f 0 -l 10"
    parser = OptionParser(usage=usage, version=('%prog'))

    parser.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    
    parser.add_option("-r", "--ra", dest="ra", type="float",  
                      help="RA(J2000.0) the center of a sight in degree")
    parser.add_option("-d", "--dec", dest="dec", type="float", 
                      help="DEC(J2000.0) the center of a sight in degree")
    parser.add_option("-f", "--fov", dest="fov", type="float",
                      help="FOV(radious) in degree")
    parser.add_option("-u", "--uppermag", dest="uppermag", type="float",
                      default=21.0,
                      help="Upper mag to filter stars")
    parser.add_option("-l", "--lowermag", dest="lowermag", type="float",
                      default=0.0,
                      help="Lower mag to filter stars")
    parser.add_option("--dbhost", dest="dbhost",
                      default=False,
                      help="Specify DB host")    
    parser.add_option("-c", "--catalog", dest="catalog",
                      default='usnob,gsc,sao',
                      help="Specify catalog name")
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
#    
 

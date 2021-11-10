#!/usr/bin/env python
#
# QDASvgwStarList.py -- STAR catalog query and filter function
#
# Takeshi Inagaki
#
#

import os
import time
import math
import threading
import astro.radec as radec
import Bunch
import ssdlog, logging
import psycopg2  # python-postgres db adaptor
from antipool import ConnectionPool


""" usage
    -r=RA(degree), -d=DEC(degree), -f=Field of View(degree), -l=Limited Magnitude, --dbhost=DB host, g2db(summit) or g2b3(base)

    # searching all star catalog at base. if you don't specify dbhost, default is an env value 'DBHOST'
    $python QDASvgwStarList.py -r 300 -d 15 -f 0.4  -l 21 --loglevel=0 --stderr --starcatalog=usnob,gsc,sao  --dbhost=g2b3

    # searching only particular starcatalog at summit. this case, sao is a startcatlog that will being searched. 
    $python QDASvgwStarList.py -r 10.3 -d 0.4 -f 0.076  -l 10 --loglevel=0 --stderr --starcatalog=sao  --dbhost=g2db

""" 

class StarList(object):
    """ create a list of guide stars with their info """    
    def __init__(self):
        self.__stars=[]
   
    def setstar(self, name,ra, dec, mag, flag, b_r, r_i):
        '''  make usnob star dictionary  '''
        KEYS=['NAME', 'RA', 'DEC', 'MAG', 'FLAG', 'B_R', 'R_I']
        self.__stars.append( dict( zip(KEYS, [name, ra, dec, mag, flag, b_r, r_i] ))  )
     
    def __iter__(self):
        return self

    def __len__(self):
        return len(self.__stars)
   
    def next(self):
        if len(self.__stars) == 0:    # threshhold terminator
            raise StopIteration     # end of iteration
        else:                       # look for usable candidate
            res = self.__stars.pop(0)
            return Bunch.Bunch(name=res['NAME'], ra=res['RA'], dec=res['DEC'], mag=res['MAG'], flag=res['FLAG'],  b_r=res['B_R'], r_i=res['R_I'])



class DBConnection(object):
    """ Postgres DB connection  """

    def __init__(self, dbhost, logger ):
        self.__starcat_host = dbhost
        self.__starcat_db = 'star_catalog'
        self.__starcat_username  = 'gen2'
        self.__starcat_password  = 'gen2'
        self.__starcat_port = 9999
        self.logger = logger

        self.__conn=None
        self.__cur=None     
      
        # user gen2 is granted for only select statement; no other sql statement is permitted 
        self.__conn_pool = ConnectionPool(psycopg2, host=self.__starcat_host, database=self.__starcat_db, user=self.__starcat_username, password=self.__starcat_password, port=self.__starcat_port)

    @property
    def conn(self):
        return self.__conn

    @property
    def cur(self):
        return self.__cur
 
    def establish_connection(self):

        got_connection = False
        count=0  # 2sec to time out
        while not got_connection and count < 20:
            try:
                self.__conn = self.__conn_pool.connection()
                self.__cur = self.__conn.cursor()
                got_connection = True
            except psycopg2.OperationalError, mess:
                self.logger.error('get_connection operational error<%s>' %(str(mess)))
                time.sleep(0.1)
            except AttributeError, mess:
                self.logger.error('get_connection attribute error<%s>' %(str(mess)))
                time.sleep(0.1)
            except Exception,e:
                time.sleep(0.1)
                self.logger.error('get_connection error<%s>' %(str(e)))
            count+=1


class StarCatalog(object):
    ''' star catalog  abstruct class '''
    def __init__(self, logger):
        self.logger=logger
        self.__min_mag=None
        self.__max_mag=None
        self.__ra=None
        self.__dec=None

    def search(self):
        pass
   
    @property
    def min_max_mag(self):
        return (self.__min_mag, self.__max_mag)

    @property
    def ra_dec(self):
        return (self.__ra, self.__dec)

    def calc_min_max_mag(self, limitmag):
        ''' get min/max value of mag '''

        #with self.lock:
        try:
            assert limitmag > 0
            self.__max_mag=limitmag
            self.__min_mag=0
        except AssertError,e:
            self.__min_mag=limitmag
            self.__max_mag=0    

        #self.logger.debug('min_mag=%s max_mag=%s' %(str(min_mag), str(max_mag)))
        #return (min_mag, max_mag)  

    def fetch_ra_dec(self, pos):
        ''' fetch ra and dec from the format of "(xxx, xxx)"
            then, convert to degree.   '''
        degrees=math.degrees     

        try:
            pos=pos[1:-1].split(',')
            self.__ra=degrees(float(pos[0].strip()))
            self.__dec=degrees(float(pos[1].strip()))
            #return (ra,dec)
        except Exception,e:
            self.logger.error('failed to fetch ra&dec %s' %str(e))
            #return (None, None)



class USNOB(StarCatalog):
    """ search USNOB star catalog """        
    def __init__(self, db, logger):
        super(USNOB,self).__init__(logger)
        self.__usnob=StarList()
        self.__db=db
        self.logger = logger 
 
    @property 
    def starlist(self):
        return self.__usnob

    def search(self, ra,dec,fov,limitmag):
        """ query USNOB star catalog"""

        #  minimum,maximum values of star magnitude   
        self.calc_min_max_mag(limitmag); min_mag,max_mag=self.min_max_mag; 
                
        where_cluse = "where pos @ scircle'<(%sd, %sd), %sd>' and r1mag between %s and %s " %( str(ra), str(dec), str(fov), str(min_mag), str(max_mag) )
        sql_statement= """ select pool_parallel("select name,pos, b1mag, b2mag, r1mag, r2mag, imag, flagsgb1, flagsgb2, flagsgr1, flagsgr2 from usnob %s ") """  %(where_cluse) 

        try:
            self.__db.establish_connection()
            conn=self.__db.conn; cur=self.__db.cur;
            self.logger.debug("executing usnob sql<%s>" %(sql_statement) )
            cur.execute (sql_statement)
            rows = cur.fetchall()
        except Exception,e:
            self.logger.error('db connection, execution error %s' %str(e))        
            return

        for name, pos, b1mag, b2mag, r1mag, r2mag, imag, flagsgb1, flagsgb2, flagsgr1, flagsgr2 in rows:
              
            self.fetch_ra_dec(pos); ra,dec=self.ra_dec;

            bmag=self.__get_usnob_mag(b1mag,b2mag)
            rmag=self.__get_usnob_mag(r1mag,r2mag)

            if imag > 25.0: imag=99.9

            ''' flag is to identify star '''
            flag= self.__get_usnob_flag( flagsgb1, flagsgb2, flagsgr1, flagsgr2)
            b_r=self.__get_usnob_blue_red_mag(bmag, rmag)
            r_i=self.__get_usnob_blue_red_mag(imag, rmag)

            self.__usnob.setstar(name, ra, dec, rmag, flag, b_r, r_i)
            #self.stars.setstar(name, ra, dec, rmag, flag, b_r, r_i)

        conn.release()
        self.logger.debug("connection to usnob released")
   
    def __get_usnob_blue_red_mag(self, mag1, mag2):
        if mag1 < 99.9 and mag2 < 99.9:
            mag = mag1-mag2
        else:
            mag = 99.9
        
        return mag
           
    def __get_usnob_flag(self, flagb1, flagb2, flagr1, flagr2 ):
             
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
    
    def __get_usnob_mag(self, mag1, mag2):
        if mag1 > 25.0 and mag2 > 25.0:
            mag=99.9
        elif mag1 > 25.0 and mag2 <= 25.0:
            mag=mag2
        elif mag1 <= 25.0 and mag2 > 25.0:
            mag=mag1
        else:
            mag=(mag1+mag2)/2.0
            
        return mag                          

class GSC(StarCatalog):
    """ search GSC star catalog """
    def __init__(self, db, logger):
        super(GSC,self).__init__(logger)
        self.__gsc=StarList()
        self.__db=db
        self.logger = logger 
 
    @property 
    def starlist(self):
        return self.__gsc
            
    def search(self, ra,dec,fov,limitmag):

        self.calc_min_max_mag(limitmag); min_mag,max_mag=self.min_max_mag; 
                
        where_cluse = "where pos @ scircle'<(%sd, %sd), %sd>' and mag between %s and %s " %( str(ra), str(dec), str(fov), str(min_mag), str(max_mag) )
       
        sql_statement= """ select pool_parallel("select name,pos,mag,class from gsc %s ") """  %(where_cluse) 

        try:
            self.__db.establish_connection()
            conn=self.__db.conn; cur=self.__db.cur;
            self.logger.debug("executing gsc sql<%s>" %(sql_statement) )
            cur.execute (sql_statement)
            rows = cur.fetchall()
        except Exception,e:
            self.logger.error('db connection, execution error %s' %str(e))        
            return
                
        for name, pos, mag, cl in rows:

            self.fetch_ra_dec(pos); ra,dec=self.ra_dec;
            
            '''  calculate flag value  '''
            flag=self.__get_gsc_flag(cl)

            ''' flag 99.0s are fixed values fro gsc'''
            self.__gsc.setstar(name, ra, dec, mag, flag, 99.9, 99.0 )

        conn.release()
        self.logger.debug("connection to gsc released")    

    def __get_gsc_flag(self,flag):
        
        if flag==0:    return 2    
        elif flag==3:  return -1
        else:          return -9 
      
class SAO(StarCatalog):

    def __init__(self, db, logger):
        super(SAO,self).__init__(logger)
        self.__sao=StarList()
        self.__db=db
        self.logger = logger 
 
    @property 
    def starlist(self):
        return self.__sao
        
    def search(self,ra, dec, fov, limitmag):
        ''' query SAO star catalog and set results in a dictionary '''

        self.calc_min_max_mag(limitmag); min_mag,max_mag=self.min_max_mag; 
        
        where_cluse = "where pos @ scircle'<(%sd, %sd), %sd>' and mag between %s and %s " %( str(ra), str(dec), str(fov), str(min_mag), str(max_mag) )
       
        sql_statement= """ select pool_parallel("select name,pos,mag,type from sao %s ") """  %(where_cluse) 

        try:
            self.__db.establish_connection()
            conn=self.__db.conn; cur=self.__db.cur;
            self.logger.debug("executing sao sql<%s>" %(sql_statement) )
            cur.execute (sql_statement)
            rows = cur.fetchall()
        except Exception,e:
            self.logger.error('db connection, execution error %s' %str(e))        
            return
                     
        for name,pos,mag,typ in rows:
            
            self.fetch_ra_dec(pos); ra,dec=self.ra_dec;

            ''' get flag value  '''
            flag=self._get_sao_flag(typ)

            ''' 2 and 99.9 are fixed flag for sao '''
            self.__sao.setstar(name, ra, dec, mag, 2, flag, 99.9)

        conn.release()
        self.logger.debug("connection to sao released")       
     
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


class StarSearch(object):
    
    def __init__(self, dbhost, logger):
        self.logger = logger        
        self.__db=DBConnection(dbhost, logger) 
        self.usnob=USNOB(self.__db, logger)
        self.gsc=GSC(self.__db, logger)
        self.sao=SAO(self.__db, logger)
        
        self.__search_thread=[]
    
    def search_starcatalog(self, ra, dec, fov, limitmag, star_catalog='usnob,gsc,sao'):

        self.__start_thread(ra, dec, fov, limitmag, star_catalog)
        self.__wait_thread_done()

    def __wait_thread_done(self):
        for thr in self.__search_thread:
            thr.join()
            self.logger.debug("%s query done" %(thr.name))
        
    def __start_thread(self, ra, dec, fov, limitmag, star_catalog):
         
        for i in star_catalog.split(','):
            catalog=i.strip() 
            #search=catalogs[catalog]
            self.logger.debug("%s thread starting..." %catalog)
            search="self.%s.search" %catalog
            try:
                search_thread=threading.Thread(target=eval(search), args=(ra, dec, fov, limitmag))
                self.__search_thread.append(search_thread)
                search_thread.start()     
            except Exception,e:
                self.logger.error('thread failing... %s' %search_thread.name) 
                continue           

def printout_header(ra, dec, fov, limitmag, total):
    
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
    print "StarNumber=%5d" %(total)
    print "name\tRA\tDEC\tmag\tFlag\tB-R\tR-I\tPreference"
    print "----\t--\t---\t---\t----\t---\t---\t----------"


def printout_stars(starlist):
    
    for num, star in enumerate(starlist):
        num+=1
        print ("%-17s\t%9.5f\t%9.5f\t%4.1f\t%2d\t%4.1f\t%4.1f\t%5d" %(star.name, star.ra, star.dec, star.mag, star.flag, star.b_r, star.r_i, num))

def main(options, args):
    
    logname = 'star_selection'
    # Create top level logger.
    logger = ssdlog.make_logger(logname, options)
    
    ra= float(options.ra)
    dec= float(options.dec)
    fov=float(options.fov)
    limitmag=float(options.limitmag)
    star_catalog=options.starcatalog
    
    if options.dbhost:
        dbhost=options.dbhost
    else:
        try:
            dbhost=os.environ['DBHOST']
        except KeyError,e:
            dbhost='g2db'
             
    logger.debug('DB host=%s' %dbhost)

    try:
        stars=StarSearch(dbhost, logger)
        stars.search_starcatalog(ra, dec, fov, limitmag, star_catalog)
 
        usnob=stars.usnob.starlist    
        gsc=stars.gsc.starlist
        sao=stars.sao.starlist
  
        total_num=len(usnob)+len(gsc)+len(sao)
      
        starlist=[]
        for s in [usnob, gsc, sao]:
            starlist.extend(s)

        printout_header(ra, dec, fov, limitmag, total_num)
        printout_stars(starlist)   

    except KeyboardInterrupt,e:
        print 'keyboard interrupting...'     
        sys.exit(1)
   
        
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
    parser.add_option("--dbhost", dest="dbhost",
                      default=False,
                      help="Specify DB host")    
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
 

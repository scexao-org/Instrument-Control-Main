#! /usr/bin/env python
#
# STARS_db -- Interface to the STARS Oracle database
#
# Mark Garboden
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Dec 18 13:08:11 HST 2008
#]
#
# TODO: this should all be replaced with a good OO<-->relational
#       mapper like SQLobjects, etc.
#
import sys, os
import time, datetime
import pprint

import Bunch 
import logging, ssdlog
try:
    import cx_Oracle as db

except ImportError, e:
    print "Failed to import Oracle client module--check envt variables"
    raise e


class STARSdbError(Exception):
    """Class of errors thrown by the STARS db interface.
    """
    pass

class STARSdbEmptyResult(STARSdbError):
    """Raised when there are no entries matching a given result.
    """
    pass


def datetime_fromSTARS1(ts):
    """Routine to get a Python time.time() compatible value from the STARS
    database.  Example:
       registration_time = STARSdb.datetime_fromSTARS1(rec.registtime)
    """
    # starsdt: 20070727151911.673
    #          012345678901234567
    try:
        pydt = datetime.datetime(int(ts[0:4]),int(ts[4:6]),int(ts[6:8]),
                                 int(ts[8:10]),int(ts[10:12]),
                                 int(ts[12:14]))
   
        # There ought to be a direct conversion, shouldn't there?
        return time.mktime(pydt.timetuple())

    except ValueError, e:
        return STARSdbError("Bad date/time value: '%s'" % ts)


def datetime_toSTARS1(secs):
    """Converts a python-style date/time value (a float) into a
    STARS Oracle date time field: 'YYYYMMDDHHMMSS'
    """
    dt = datetime.datetime(*time.localtime(secs)[0:6])
    
    return dt.strftime('%Y%m%d%H%M%S')


class STARSdb(object):

    def __init__(self, logger, host=None, port=1521, connect=False,
                 dbname=None, user=None, passwd=None):
        self.logger = logger
        self.port = port
        if not host:
            try:
                host = os.environ['STARS_DBHOST']

            except KeyError:
                raise STARSdbError("Please set your STARS_DBHOST env var")

        self.host = host

        if not dbname:
            try:
                dbname = os.environ['STARS_DBNAME']

            except KeyError:
                raise STARSdbError("Please set your STARS_DBNAME env var")

        self.dbname = dbname

        if not user:
            try:
                user = os.environ['STARS_DBUSER']

            except KeyError:
                raise STARSdbError("Please set your STARS_DBUSER env var")

        self.user = user

        if not passwd:
            try:
                passwd = os.environ['STARS_DBPASS']

            except KeyError:
                raise STARSdbError("Please set your STARS_DBPASS env var")

        self.passwd = passwd

        self.dsn  = None
        self.conn = None

        if connect:
            self.connect()

        
    def connect(self):
        """Connect to the STARS db.  This takes a few seconds, so there is
        an option to the constructor to not automatically do this.
        """
        try:
            self.logger.debug("Connecting to database '%s' on host %s:%d as user %s" % (self.dbname, self.host, self.port, self.user))

            self.dsn = db.makedsn(self.host, self.port, self.dbname)
            self.conn = db.connect(self.user, self.passwd,
                                   self.dsn)

        except db.DatabaseError, e:
            raise STARSdbError("STARS database connection error: %s" % str(e))
        

    def getcursor(self):
        if not self.conn:
            self.connect()

        try:
            return db.Cursor(self.conn)

        except db.DatabaseError, e:
            raise STARSdbError("STARS database connection error: %s" % str(e))


    def commit(self):
        raise STARSdbError("Read only access to this database!")
        
            
    def _getTablesDesc(self, tables):
        """Helper function to get STARS table descriptionss.
        """
        cur = self.getcursor()

        # Get table descriptions
        for tblname in tables.keys():
            bnch = tables[tblname]
            sql = """select * from %s where 0 == 1 """ % (bnch.name,)
            try:
                cur.execute(sql)
                bnch.description = cur.description
            
            except db.DatabaseError, e:
                bnch.description = None
                
                
    def getTables(self):
        """Get the list of all STARS tables.
        """
        cur = self.getcursor()

        # we don't want any mirror tables or backup tables
        sql = """select * from tab where tname not like '%$%'
        and tname not like '%_BK'"""

        self.logger.debug("Executing '%s'" % sql)
        try:
            cur.execute(sql)
            res = cur.fetchall()

        except db.DatabaseError, e:
            raise STARSdbError("STARS database error: %s" % str(e))
        # pprint.pprint(res)
        # pprint.pprint(cur.description)

        # Should return a list like:
        #[('DAYREPORTTBL', 'TABLE', None), ('FITSHEADERTBL', 'TABLE', None),
        tables = Bunch.Bunch()
        for (tblname, objtype, whatisthis) in res:
            tables[tblname.lower()] = Bunch.Bunch(name=tblname,
                                                  description=None)

        # Currently there doesn't seem to be anything in the form
        # of table descriptions so skip this
        #self._getTablesDesc(tables)
        
        return tables
    
    def is_log_stars(self,log):
        """ returns true if a log file is in STARS. otherwise, false"""
                
        cur = self.getcursor()

        sql="select logid from OBSLOGTBL where logid='%s' """ %log

        self.logger.debug('sql<%s>' %sql)

        try:
            cur.execute(sql)
            res=cur.fetchall()
        except db.DatabaseError,e:
            raise STARSdbError("STARS datebasae error: %s" %str(e))
   
        if len(res)==0:
            self.logger.debug('no found res<%s>' %str(res))
            return False
        else:
            self.logger.debug('found res<%s>' %str(res))
            return True

    def are_frames_in_stars(self, ins, sframe, eframe):
        cur = self.getcursor()
        sql = "select frame_id from %sADM where FRAME_ID between '%s' and '%s'   """ %(ins,sframe,eframe) 
        try:
            cur.execute(sql)
            res = cur.fetchall()
            return res
        except db.DatabaseError as e:
            raise STARSdbError("STARS database query error: %s" % str(e))
            #return [] 

    def is_in_stars(self, frameid):
        """ this is much faster query to check if a frame is in stars or not 
            return True if found. otherwise False"""         

        cur = self.getcursor()

        sql = "select frame_id from %sADM where FRAME_ID = '%s' """ % ( frameid[:3], frameid )

        self.logger.debug("Executing '%s'" % sql)
        try:
            cur.execute(sql)
            res = cur.fetchone()
        except db.DatabaseError, e:
            return False

        try:
            assert not res is None
            return True
        except AssertionError,e:
            return False

    def getFrame(self, frameid):
        """Used for retrieving a record from the INDEXDATATBL.
        """
        cur = self.getcursor()

        # we don't want any mirror tables or backup tables
        sql = "select * from %sADM where FRAME_ID like '%s' """ % (
            frameid[:3], frameid)

        self.logger.debug("Executing '%s'" % sql)
        try:
            cur.execute(sql)
            res = cur.fetchall()

        except db.DatabaseError, e:
            raise STARSdbError("STARS database error: %s" % str(e))

        if len(res) <= 0:
            raise STARSdbEmptyResult("No results matching query")

        # Take first matching record
        assert(len(res) == 1)
        res = res[0]

        bnch = Bunch.Bunch()
        tup = cur.description
        for i in xrange(len(tup)):
            desc_tup = tup[i]
            fieldname = desc_tup[0].lower()
            bnch[fieldname] = res[i]
            
        return bnch

    
    def inSTARS(self, frameid):
        """Returns True if this frameid is safely registered in STARS,
        False otherwise.
        """
        try:
            res = self.getFrame(frameid)

            if len(res.registtime.strip()) != 0:
                return True

            return False

        except STARSdbError, e:
            return False


def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('STARSdb', options)
 
    starsdb = STARSdb(logger, host=options.host, port=options.port,
                      dbname=options.dbname, user=options.username,
                      passwd=options.password)
    
    #------0123456789012345678901234567890123456789012345678901234567890123456789
    print "FRAMEID        HILO                 MITAKA"
    for arg in args:
        frameid = arg.upper()

        out = {'frameid': frameid,
               'hilo': 'NEVER',
               'mitaka': 'NEVER',
               }
        try:
            res = starsdb.getFrame(frameid)

            ts = res.registtime.strip()
            if len(ts) != 0:
                out['hilo'] = time.strftime("%Y-%m-%d %H:%M:%S",
                                            time.localtime(datetime_fromSTARS1(ts)))
            
            ts = res.mtk_regist.strip()
            if len(ts) != 0:
                out['mitaka'] = time.strftime("%Y-%m-%d %H:%M:%S",
                                              time.localtime(datetime_fromSTARS1(ts)))
            
        except STARSdbError, e:
            logger.warn("STARS error: %s" % str(e))
            
        print "%(frameid)-14.14s %(hilo)-20.20s %(mitaka)-20.20s" % (
            out)

if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("-d", "--dbname", dest="dbname", metavar="NAME",
                      help="Use NAME as the STARS database name")
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-q", "--host", dest="host",
                      help="Use HOST as the STARS database host",
                      metavar="HOST")
    optprs.add_option("-p", "--password", dest="password", metavar="PASSWD",
                      help="Use PASSWD as the STARS database password")
    optprs.add_option("--port", dest="port", type="int", default=1521,
                      help="Use PORT as the STARS database port",
                      metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("-u", "--username", dest="username",
                      help="Use NAME as the STARS database user name",
                      metavar="NAME")
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
       
#END

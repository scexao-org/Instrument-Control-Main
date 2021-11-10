#! /usr/bin/env python
#
# SOSS_db -- Interface to the SOSS Oracle database
#
# Mark Garboden
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Dec 18 14:19:00 HST 2008
#]
#
# TODO: this should all be replaced with a good OO<-->relational
#       mapper like SQLobjects, etc.
#
import sys, os
import time, datetime
import pprint

import logging, ssdlog
import Bunch
try:
    import cx_Oracle as db

except ImportError, e:
    print "Failed to import Oracle client module--check envt variables"
    raise e


class SOSSdbError(Exception):
    """Class of errors thrown by the SOSS db interface.
    """
    pass


class SOSSdbEmptyResult(SOSSdbError):
    """Raised when there are no entries matching a given result.
    """
    pass


def datetime_fromSOSS1(ts):
    # sossdt: 20070727151911
    #         01234567890123
    try:
        pydt = datetime.datetime(int(ts[0:4]),int(ts[4:6]),int(ts[6:8]),
                                 int(ts[8:10]),int(ts[10:12]),
                                 int(ts[12:14]))
   
        # There ought to be a direct conversion, shouldn't there?
        return time.mktime(pydt.timetuple())

    except ValueError, e:
        return SOSSdbError("Bad date/time value: '%s'" % ts)


def datetime_toSOSS1(secs):
    """Converts a python-style date/time value (a float) into a
    SOSS Oracle date time field: 'YYYYMMDDHHMMSS'
    """
    dt = datetime.datetime(*time.localtime(secs)[0:6])
    
    return dt.strftime('%Y%m%d%H%M%S')


def datetime_fromSOSS2(ts):
    # sossdt: 2005-07-20-00:00:00
    #         0123456789012345678
    try:
        pydt = datetime.datetime(int(ts[0:4]),int(ts[5:7]),int(ts[8:10]),
                                 int(ts[11:13]),int(ts[14:16]),
                                 int(ts[17:19]))
        
        # There ought to be a direct conversion, shouldn't there?
        return time.mktime(pydt.timetuple())

    except ValueError, e:
        return SOSSdbError("Bad date/time value: '%s'" % ts)


def datetime_toSOSS2(secs):
    """Converts a python-style date/time value (a float) into a
    SOSS Oracle date time field: 'YYYY-MM-DD-HH:MM:SS'
    """
    dt = datetime.datetime(*time.localtime(secs)[0:6])
    
    return dt.strftime('%Y-%m-%d-%H:%M:%S')


class SOSSdb(object):

    def __init__(self, logger, host=None, port=1521, connect=False,
                 dbname=None, user=None, passwd=None):
        self.logger = logger
        self.port = port
        if not host:
            try:
                host = os.environ['SOSS_DBHOST']

            except KeyError:
                raise SOSSdbError("Please set your SOSS_DBHOST env var")

        self.host = host

        if not dbname:
            try:
                dbname = os.environ['SOSS_DBNAME']

            except KeyError:
                raise SOSSdbError("Please set your SOSS_DBNAME env var")

        self.dbname = dbname

        if not user:
            try:
                user = os.environ['SOSS_DBUSER']

            except KeyError:
                raise SOSSdbError("Please set your SOSS_DBUSER env var")

        self.user = user

        if not passwd:
            try:
                passwd = os.environ['SOSS_DBPASS']

            except KeyError:
                raise SOSSdbError("Please set your SOSS_DBPASS env var")

        self.passwd = passwd

        self.dsn  = None
        self.conn = None
        self.cur = None
        self.fields = None

        if connect:
            self.connect()


    def __iter__(self):
        return self

    
    def connect(self):
        """Connect to the SOSS db.  This takes a few seconds, so there is
        an option to the constructor to not automatically do this.
        """
        try:
            self.logger.debug("Connecting to database '%s' on host %s:%d as user %s" % (self.dbname, self.host, self.port, self.user))

            self.dsn = db.makedsn(self.host, self.port, self.dbname)
            self.conn = db.connect(self.user, self.passwd,
                                   self.dsn)

            self.cur =  db.Cursor(self.conn)
            
        except db.DatabaseError, e:
            raise SOSSdbError("SOSS database connection error: %s" % str(e))
        

    def getcursor(self):
        if not self.conn:
            self.connect()

        try:
            return db.Cursor(self.conn)

        except db.DatabaseError, e:
            raise SOSSdbError("SOSS database connection error: %s" % str(e))


    def commit(self):
        if not self.conn:
            self.connect()

        self.logger.debug("Commiting database")
        try:
            self.conn.commit()

        except db.DatabaseError, e:
            raise SOSSdbError("SOSS database error: %s" % str(e))
        
            
    def getFrame(self, frameid):
        """Used for retrieving a record from the INDEXDATATBL.
        """
        if not self.conn:
            self.connect()

        # we don't want any mirror tables or backup tables
        sql = "select * from INDEXDATATBL where FRAMENO like '%s'" % (
            frameid)

        self.logger.debug("Executing '%s'" % sql)
        try:
            self.cur.execute(sql)
            res = self.cur.fetchall()

        except db.DatabaseError, e:
            raise SOSSdbError("SOSS database error: %s" % str(e))
        #pprint.pprint(self.cur.description)

        if len(res) <= 0:
            raise SOSSdbEmptyResult("No results matching query")

        # Take first matching record
        assert(len(res) == 1)
        res = res[0]

        # Return result as a bunch, where the field names match the record
        bnch = Bunch.Bunch()
        tup = self.cur.description
        for i in xrange(len(tup)):
            desc_tup = tup[i]
            fieldname = desc_tup[0].lower()
            bnch[fieldname] = res[i]
            
        return bnch


    def query(self, sql):
        """Generic function to process SQL statements. 
        """
        if not self.conn:
            self.connect()

        self.cur.execute(sql)

        self.description = self.cur.description
        fields = []
        for i in xrange(len(self.description)):
            desc_tup = self.description[i]
            fields.append(desc_tup[0].lower())

        self.fields = tuple(fields)

        return self.fields


    def next(self):
        if not self.fields:
            raise SOSSdbError("Please execute a query first!")
        
        rec = self.cur.next()

        bnch = Bunch.Bunch()
        for i in xrange(len(self.fields)):
            fieldname = self.fields[i]
            bnch[fieldname] = rec[i]

        return bnch
    
                
    def getTables(self):
        """Get the list of all SOSS tables.
        """
        if not self.conn:
            self.connect()

        # we don't want any mirror tables or backup tables
        sql = """select * from tab where tname not like '%$%'
        and tname not like '%_BK'"""

        self.logger.debug("Executing '%s'" % sql)
        try:
            self.cur.execute(sql)
            res = self.cur.fetchall()

        except db.DatabaseError, e:
            raise SOSSdbError("SOSS database error: %s" % str(e))
        # pprint.pprint(res)
        # pprint.pprint(self.cur.description)

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
    

    def getFrame(self, frameid):
        """Used for retrieving a record from the INDEXDATATBL.
        """
        if not self.conn:
            self.connect()

        # we don't want any mirror tables or backup tables
        sql = "select * from INDEXDATATBL where FRAMENO like '%s'" % (
            frameid)

        self.logger.debug("Executing '%s'" % sql)
        try:
            self.cur.execute(sql)
            res = self.cur.fetchall()

        except db.DatabaseError, e:
            raise SOSSdbError("SOSS database error: %s" % str(e))
        #pprint.pprint(self.cur.description)

        if len(res) <= 0:
            raise SOSSdbEmptyResult("No results matching query")

        # Take first matching record
        assert(len(res) == 1)
        res = res[0]

        # Return result as a bunch, where the field names match the record
        bnch = Bunch.Bunch()
        tup = self.cur.description
        for i in xrange(len(tup)):
            desc_tup = tup[i]
            fieldname = desc_tup[0].lower()
            bnch[fieldname] = res[i]
            
        return bnch
    

    def inSOSS(self, frameid):
        """Returns True if this frameid is safely in SOSS RAID, False otherwise.
        """
        try:
            res = self.getFrame(frameid)

            if len(res.removetime.strip()) != 0:
                return False

            if len(res.writetime.strip()) != 0:
                return True

            return False

        except SOSSdbError, e:
            return False


    def getProp(self, propid):
        """Used for retrieving a record from the USRADMINTBL.
        """
        if not self.conn:
            self.connect()

        # we don't want any mirror tables or backup tables
        sql = "select * from USERADMINTBL where PROPOSALID like '%s'" % (
            propid)

        self.logger.debug("Executing '%s'" % sql)
        try:
            self.cur.execute(sql)
            res = self.cur.fetchall()

        except db.DatabaseError, e:
            raise SOSSdbError("SOSS database error: %s" % str(e))
        #pprint.pprint(self.cur.description)

        if len(res) <= 0:
            raise SOSSdbEmptyResult("No results matching query")

        # Take first matching record
        assert(len(res) == 1)
        res = res[0]
        
        # Return tuple
        bnch = Bunch.Bunch(createtime=datetime_fromSOSS1(res[0]),
                           updatetime=datetime_fromSOSS1(res[1]),
                           proposalid=res[2],
                           starttime=datetime_fromSOSS2(res[3]),
                           endtime=datetime_fromSOSS2(res[4]),
                           instruments=res[5].split(','),
                           purpose=res[6],
                           oplevel=res[7].split(','))
                           
        return bnch
    

    def insProp(self, bnch):
        """Used for inserting a record into the USRADMINTBL.
        """
        if not self.conn:
            self.connect()

        d = {}
        curtime = time.time()
        d['createtime'] = datetime_toSOSS1(curtime)
        d['updatetime'] = datetime_toSOSS1(curtime)
        d['proposalid'] = bnch.proposalid
        d['starttime'] = datetime_toSOSS2(bnch.starttime)
        d['endtime'] = datetime_toSOSS2(bnch.endtime)
        d['instruments'] = ','.join(bnch.instruments)
        d['purpose'] = bnch.purpose
        d['oplevel'] = ','.join(bnch.oplevel)

        sql = """insert into USERADMINTBL
                 values ('%(createtime)s', '%(updatetime)s',
                 '%(proposalid)s', '%(starttime)s', '%(endtime)s',
                 '%(instruments)s', '%(purpose)s', '%(oplevel)s')
        """ % d

        self.logger.debug("Executing '%s'" % sql)
        try:
            self.cur.execute(sql)

        except db.DatabaseError, e:
            raise SOSSdbError("SOSS database error: %s" % str(e))
                           
    
    def setProp(self, bnch):
        """Used for updating a record in the USRADMINTBL.
        """
        if not self.conn:
            self.connect()

        d = {}
        #d['createtime'] = datetime_toSOSS1(bnch.createtime)
        d['updatetime'] = datetime_toSOSS1(time.time())
        d['proposalid'] = bnch.proposalid
        d['starttime'] = datetime_toSOSS2(bnch.starttime)
        d['endtime'] = datetime_toSOSS2(bnch.endtime)
        d['instruments'] = ','.join(bnch.instruments)
        d['purpose'] = bnch.purpose
        d['oplevel'] = ','.join(bnch.oplevel)

        sql = """update USERADMINTBL
                 set UPDATETIME='%(updatetime)s',
                 STARTTIME='%(starttime)s', ENDTIME='%(endtime)s',
                 INSTRUMENTS='%(instruments)s', PURPOSE='%(purpose)s',
                 OPLEVEL='%(oplevel)s'
                 where PROPOSALID like '%(proposalid)s'
        """ % d

        self.logger.debug("Executing '%s'" % sql)
        try:
            self.cur.execute(sql)

        except db.DatabaseError, e:
            raise SOSSdbError("SOSS database error: %s" % str(e))
                           
    
    def mkProp(self, proposalid, starttime=None, endtime=None,
               instruments=[], purpose='none', oplevel=[]):
        """Facility for cranking out proposal db records.
        """

        now = time.time()
        if not starttime:
            starttime = now
        if not endtime:
            endtime = now
            
        bnch = Bunch.Bunch(createtime=now, updatetime=now,
                           proposalid=proposalid,
                           starttime=starttime, endtime=endtime,
                           instruments=instruments,
                           purpose=purpose,
                           oplevel=oplevel)
                           
        return bnch
    

def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('SOSSdb', options)

    sossdb = SOSSdb(logger, host=options.host, port=options.port,
                    dbname=options.dbname, user=options.username,
                    passwd=options.password)

    #------0123456789012345678901234567890123456789012345678901234567890123456789
    print "FRAMEID        RAID                 STARS                TAPE"
    for arg in args:
        frameid = arg.upper()

        out = {'frameid': frameid,
               'disk': 'NEVER',
               'tape': 'NEVER',
               'stars': 'NEVER',
               }
        try:
            res = sossdb.getFrame(frameid)

            ts = res.writetime.strip()
            if len(ts) != 0:
                out['disk'] = time.strftime("%Y-%m-%d %H:%M:%S",
                                      time.localtime(datetime_fromSOSS1(ts)))
            
            ts = res.transmittime.strip()
            if len(ts) != 0:
                out['stars'] = time.strftime("%Y-%m-%d %H:%M:%S",
                                      time.localtime(datetime_fromSOSS1(ts)))
            
            ts = res.tapetime.strip()
            if len(ts) != 0:
                out['tape'] = time.strftime("%Y-%m-%d %H:%M:%S",
                                      time.localtime(datetime_fromSOSS1(ts)))
            
        except STARSdbError, e:
            logger.warn("STARS error: %s" % str(e))
            
        print "%(frameid)-14.14s %(disk)-20.20s %(tape)-20.20s %(stars)-20.20s" % (
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

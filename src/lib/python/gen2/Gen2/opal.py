#!/usr/bin/env python
# opal.py
#
# Original by Mark Garboden
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Tue Jan  4 22:35:14 HST 2011
#]
# Bruce Bon (Bruce.Bon@SubaruTelescope.org)
#
import sys, os
import time, datetime
import MySQLdb
import pprint


samples = """
-- MySQL maria --
ALLOC table

mysql> desc alloc;
+----------+-----------+------+
| Field    | Type      | Null |
+----------+-----------+------+
| idno     | int(11)   |      |  3705L,
| propid   | char(15)  | YES  |  'S05B-OT20',
| name     | char(100) | YES  |  '',
| piidno   | int(11)   | YES  |  1414L,
| pw       | char(10)  | YES  |  None,
| gid      | char(6)   | YES  |  'o05440',
| nights   | int(11)   | YES  |  1L,
| instr    | char(20)  | YES  |  'All',
| datein   | date      | YES  |  datetime.date(2005, 11, 20),
| dateout  | date      | YES  |  datetime.date(2005, 11, 21),
| sem      | char(4)   | YES  |  'S05B',
| first    | char(30)  | YES  |  'Operator',
| last     | char(30)  | YES  |  'STARS',
| username | char(20)  | YES  |  'starsopr',
| comment  | char(100) | YES  |  '',
| subidno  | int(11)   | YES  |  3826L,
| stn_flag | char(3)   | YES  |  'No',
| pwu      | char(8)   | YES  |  None,
| pwo      | char(8)   | YES  |  None,
| pep      | char(12)  | YES  |  'mcbYlJWoShkX',
| pwot     | char(10)  | YES  |  '\xdf\xc3\x88\xae\xa1\x88\xe0\xb0',
| pwut     | char(10)  | YES  |  '\xe0\xca\x87\xa0\x9f\x94\xaf\x91',
+----------+-----------+------+

-- OPAL -- 
Prop ID:        S05B-OT20
Prop Title:     
PI First:       Operator
PI Last:        STARS
Group ID:       o05440
        
Start:  2005-11-20
End:    2005-11-21
Nights:         1
Instr:  All

        
Prop IDNo: 3705
Sem: S05B
PI IDNo: 1414
UserName: starsopr STN? No
Comment: 
Alloc IDNo: 3826

Observation Allocations for
Proposal: S05B-OT20 GID: o05440
AllocID - GID -  1st Night  - Last Day   - Nights - Instr - PropIDNo - Primary
3826  - o05440 - 2005-11-20 - 2005-11-21 -   1    -  All  -  3705    -    *

0 Co-PI's for S05B-OT20

1 STN Users Assigned to o05440
1       starsopr        Stars Operator



TSR table

mysql> desc tsr;
+-----------+--------------+------+-----+---------+-------+
| Field     | Type         | Null | Key | Default | Extra |
+-----------+--------------+------+-----+---------+-------+
| date      | date         | YES  |     | NULL    |       |
| instr     | varchar(10)  | YES  |     | NULL    |       |
| ss        | varchar(15)  | YES  |     | NULL    |       |
| last      | varchar(30)  | YES  |     | NULL    |       |
| first     | varchar(30)  | YES  |     | NULL    |       |
| propid    | varchar(10)  | YES  |     | NULL    |       |
| focus     | varchar(10)  | YES  |     | NULL    |       |
| arrive    | varchar(10)  | YES  |     | NULL    |       |
| ag        | varchar(10)  | YES  |     | NULL    |       |
| sv        | varchar(10)  | YES  |     | NULL    |       |
| adc       | varchar(10)  | YES  |     | NULL    |       |
| imr       | varchar(10)  | YES  |     | NULL    |       |
| cal       | varchar(10)  | YES  |     | NULL    |       |
| flats     | varchar(10)  | YES  |     | NULL    |       |
| polar     | varchar(10)  | YES  |     | NULL    |       |
| ao        | varchar(10)  | YES  |     | NULL    |       |
| irm2      | varchar(10)  | YES  |     | NULL    |       |
| pmdusk    | varchar(10)  | YES  |     | NULL    |       |
| pmdome    | varchar(10)  | YES  |     | NULL    |       |
| pmcal     | varchar(15)  | YES  |     | NULL    |       |
| amdawn    | varchar(10)  | YES  |     | NULL    |       |
| amdome    | varchar(10)  | YES  |     | NULL    |       |
| flatrun   | varchar(10)  | YES  |     | NULL    |       |
| calrun    | varchar(10)  | YES  |     | NULL    |       |
| comments  | varchar(100) | YES  |     | NULL    |       |
| idno      | varchar(10)  | YES  |     | NULL    |       |
| calcomm   | varchar(50)  | YES  |     | NULL    |       |
| imrcomm   | varchar(50)  | YES  |     | NULL    |       |
| day       | char(3)      | YES  |     | NULL    |       |
| gid       | varchar(6)   | YES  |     | NULL    |       |
| pmcomm    | varchar(50)  | YES  |     | NULL    |       |
| amcomm    | varchar(50)  | YES  |     | NULL    |       |
| observers | varchar(62)  | YES  |     | NULL    |       |
| obsarrive | varchar(10)  | YES  |     | NULL    |       |
| location  | varchar(6)   | YES  |     | NULL    |       |
| sh        | char(3)      | YES  |     | NULL    |       |
| chop      | char(3)      | YES  |     | NULL    |       |
| m2        | varchar(6)   | YES  |     | NULL    |       |
| m3        | varchar(6)   | YES  |     | NULL    |       |
| adccomm   | varchar(50)  | YES  |     | NULL    |       |
| propidno  | varchar(10)  | YES  |     | NULL    |       |
| amfini    | varchar(10)  | YES  |     | NULL    |       |
| instrot   | char(3)      | YES  |     | NULL    |       |
| flatcomm  | varchar(50)  | YES  |     | NULL    |       |
| sslist    | varchar(75)  | YES  |     | NULL    |       |
| oplist    | varchar(75)  | YES  |     | NULL    |       |
| remhilo   | varchar(10)  | YES  |     | NULL    |       |
| remmtk    | varchar(10)  | YES  |     | NULL    |       |
| amcal     | varchar(15)  | YES  |     | NULL    |       |
| allocidno | varchar(10)  | YES  |     | NULL    |       |
+-----------+--------------+------+-----+---------+-------+
50 rows in set (0.00 sec)

Sample tsr row
*************************** 433. row ***************************
     date: 2006-07-13
    instr: CIAO
       ss: ishii
     last: Fukagawa
    first: Misato
   propid: S06A-128
    focus: Cs
   arrive: 18:00
       ag: Yes
       sv: No
      adc: Out
      imr: No
      cal: Yes
    flats: Yes
    polar: Out
       ao: Yes
     irm2: Yes
   pmdusk: Yes
   pmdome: Yes
    pmcal: No
   amdawn: Yes
   amdome: No
  flatrun: Yes
   calrun: No
 comments:
     idno: 5486
  calcomm: HAL1, 1.5-2.0A
  imrcomm:
      day: Thu
      gid: o06130
   pmcomm:
   amcomm:
observers:
obsarrive: 19:00
 location: Remote
       sh: No
     chop: No
       m2: IR
       m3: None
  adccomm:
 propidno: 3771
   amfini:
  instrot: Yes
 flatcomm: NULL
   sslist: Ishii
   oplist:
  remhilo: None
   remmtk: None
    amcal: No
allocidno: 3932


"""

class OPALError(Exception):
    pass

class OPALinfo(object):

    def __init__(self, opal_dbhost=None, opal_dbuser=None, opal_dbpass=None,
                 opal_dbname=None):

        try:
            if not opal_dbhost:
                opal_dbhost = os.environ['OPAL_DBHOST']
            self.opal_dbhost = opal_dbhost

            if not opal_dbuser:
                opal_dbuser = os.environ['OPAL_DBUSER']
            self.opal_dbuser = opal_dbuser

            if not opal_dbpass:
                opal_dbpass = os.environ['OPAL_DBPASS']
            self.opal_dbpass = opal_dbpass

            if not opal_dbname:
                opal_dbname = os.environ['OPAL_DBNAME']
            self.opal_dbname = opal_dbname

        except KeyError, e:
            raise OPALError("No OPAL database connection parameters found")

        #self._connect()
        

    def connect(self):
        self.con = MySQLdb.connect(host=self.opal_dbhost,
                                   user=self.opal_dbuser,
                                   passwd=self.opal_dbpass,
                                   db=self.opal_dbname)
        self.cur = self.con.cursor(MySQLdb.cursors.DictCursor)


    def close(self):
        self.con.close()

        
    def getInfoForDates(self, fromdate, todate, table='alloc'):

        date1 = fromdate.strftime("%Y/%m/%d")
        date2 = todate.strftime("%Y/%m/%d")

        table = table.lower()
        
        if table == 'alloc':
            sql = """select * from alloc  
                     where ( datein >= str_to_date('%s','%%Y/%%m/%%d')
                     and     dateout <= str_to_date('%s','%%Y/%%m/%%d') )
                     order by datein""" % (date1, date2)

        elif table == 'tsr':
            sql = """select * from tsr  
                     where ( date >= str_to_date('%s','%%Y/%%m/%%d')
                     and     date <= str_to_date('%s','%%Y/%%m/%%d') )
                     order by date""" % (date1, date2)


        self.connect()
        
        self.cur.execute(sql)
        opalinfo = self.cur.fetchall()
        #pprint.pprint(opalinfo)

        self.close()
        
        res = []
        for prop in opalinfo:
            d = {}
            d.update(prop)

            # Adjustment for "terminology" differences between SOSS and OPAL
            d['proposal'] = d['propid']
            d['propid'] = d['gid']

            res.append(d)

        return res
    

    def getInfoForNights(self, fromdate, todate, table='alloc'):

        (yr, mo, da, hr, min, sec, x, y, z) = todate.timetuple()
        todate_midnight = datetime.datetime(yr, mo, da, 23, 59, 59)
        todate_end = todate_midnight + datetime.timedelta(hours=7)
        
        return self.getInfoForDates(fromdate, todate_end, table=table)
    

    def getInfoForNight(self, ondate, table='alloc'):

        (yr, mo, da, hr, min, sec, x, y, z) = ondate.timetuple()

        # Else get info for today+tomorrow
        fromdate = datetime.datetime(yr, mo, da, 12, 0, 0)
        todate = fromdate + datetime.timedelta(hours=24)

        return self.getInfoForDates(fromdate, todate, table=table)
    

    def getInfoForTonight(self, table='alloc'):

        now = datetime.datetime.now()
        (yr, mo, da, hr, min, sec, x, y, z) = now.timetuple()

        # If it is after midnight and before 9am, get info for
        # yesterday+today
        if (hr >= 0) and (hr < 9):
            todate = datetime.datetime(yr, mo, da, 9, 0, 0)
            yesterday = now - datetime.timedelta(hours=12)
            (yr, mo, da, hr, min, sec, x, y, z) = yesterday.timetuple()
            fromdate = datetime.datetime(yr, mo, da, 12, 0, 0)
        else:
            # Else get info for today+tomorrow
            fromdate = datetime.datetime(yr, mo, da, 12, 0, 0)
            todate = fromdate + datetime.timedelta(hours=24)

        return self.getInfoForNights(fromdate, todate, table=table)
    

    def getProp(self, propid):
        """Get one proposal, return dictionary of info.
        """

        sql = """select * from props
        where ( gid = "%s" )
        order by gid""" % (propid)

        self.connect()
        
        self.cur.execute(sql)
        info = self.cur.fetchall()

        self.close()
        
        tup = info[0]
        #pprint.pprint(tup)
        row = {}
        row.update(tup)

        # Adjustment for "terminology" differences between SOSS and OPAL
        row['proposal'] = row['propid']
        row['propid'] = row['gid']

        # Get the passwords
        getpass(row)

        return row


    def getProps(self):
        """Get all proposals, return giant dictionary indexed by propid.
        """

        sql = """select * from props order by gid"""

        self.connect()
        
        self.cur.execute(sql)
        info = self.cur.fetchall()

        self.close()
        
        opal = {}

        for tup in info:
            #pprint.pprint(tup)
            row = {}
            row.update(tup)

            propid = row['gid']
            if propid == None:       # ignore None rows
                continue

            opal[propid] = row

            # Adjustment for "terminology" differences between SOSS and OPAL
            row['proposal'] = row['propid']
            row['propid'] = propid

            # Get the passwords
            getpass(row)

        return opal


def decrypt(passwd, pepper):

    key = [0,2,3,5,6,8,10,11]
    #print len(passwd), len(pepper), len(key)
    result = ""
    if not passwd:
        return(None)

    for i in range(len(passwd)):
        char = passwd[i]
        keychar = pepper[key[i % len(key)]]
        result = result + chr(ord(char) - ord(keychar))

    return result


def getpass(row):
  
    if row['pwot'] and row['pwut'] and row['pep']:
        row['opass'] = decrypt(row['pwot'], row['pep'])
        row['upass'] = decrypt(row['pwut'], row['pep'])

    elif row['pwot'] and row['pwut']:   # and row['pep'] == None
        # "WARNING: Proposal has unencrypted passwords in OPAL!
        row['opass'] = row['pwot']
        row['upass'] = row['pwut']

    else:       # no password!
        # WARNING: Proposal %s is missing passwords in OPAL!
        row['opass'] = None
        row['upass'] = None


def main(options, args):
    
    typ_fmt = "%(date)-10.10s %(program)2.2s %(typ)3.3s %(proposal)-10.10s %(propid)6.6s %(instr)8.8s %(ss)-12.12s %(operators)-20.20s %(observers)-20.20s %(locations)s"
    ext_fmt = "%(date)-10.10s %(program)2.2s %(typ)3.3s %(proposal)-10.10s %(propid)6.6s %(instr)8.8s %(ss)-12.12s %(operators)-20.20s %(ulogin)-8.8s %(upass)-8.8s %(opass)-8.8s %(observers)-20.20s %(locations)s"

    fmt = typ_fmt
    if options.full:
        fmt = ext_fmt

    op = OPALinfo()

    d = {'date': 'Date', 'program': 'Program', 'typ': 'Type',
         'proposal': 'Proposal', 'propid': 'PropId',
         'instr': 'Instruments', 'ss': 'Support Scientist',
         'observers': 'Observers', 'operators': 'Operators',
         'locations': 'Locations', 'comments': 'Comments',
         'ulogin': 'UAcct', 'upass': 'UPass', 'opass': 'OPass'}

    res = [fmt % d]
    
    now = datetime.datetime.now()
    if options.opaldate:
        now = now.strptime(options.opaldate, '%Y-%m-%d')
            
    d['opaldate'] = now.strftime('%Y-%m-%d')

    opalinfo = op.getInfoForNight(now, table='tsr')

    for rec in opalinfo:
        t = {}
        t.update(rec)
        t['date'] = rec['date'].strftime("%Y-%m-%d")
        t['typ'] = 'TSR'
        t['ss'] = rec['sslist']
        t['instr'] = rec.get('instr', 'N/A')
        t['propid'] = rec.get('propid', 'N/A')
        if t['propid'] != 'N/A':
            data = op.getProp(t['propid'])
            t['ulogin'] = data.get('ulogin', 'N/A')
            t['upass'] = data.get('upass', 'N/A')
            t['ologin'] = t['propid']
            t['opass'] = data.get('opass', 'N/A')
        else:
            t['ulogin'] = 'N/A'
            t['upass'] = 'N/A'
            t['ologin'] = t['propid']
            t['opass'] = 'N/A'
            
        t['time'] = rec.get('arrive', 'N/A')
        t['program'] = rec.get('program', 'N/A')
        t['operators'] = rec.get('oplist', 'N/A')
        t['comments'] = rec.get('comments', '')
        # figure out locations
        loc = ['Summit']
        #print rec
        hilo = rec.get('remhilo', '').strip().lower()
        if hilo and (not hilo.startswith('no')):
            loc.append('Hilo:'+hilo)
        mtk = rec.get('remmtk', '').strip().lower()
        if mtk and (not mtk.startswith('no')):
                loc.append('Mitaka:'+mtk)
        t['locations'] = ','.join(loc)
        row = fmt % t
        res.append(row)

    opalinfo = op.getInfoForNight(now)
    for rec in opalinfo:
        t = {}
        t.update(rec)
        t['date'] = rec['datein'].strftime("%Y-%m-%d")
        t['typ'] = ''
        t['observers'] = rec['last']
        t['instr'] = rec.get('instr', 'N/A')
        t['propid'] = rec.get('propid', 'N/A')
        if t['propid'] != 'N/A':
            data = op.getProp(t['propid'])
            t['ulogin'] = data.get('ulogin', 'N/A')
            t['upass'] = data.get('upass', 'N/A')
            t['ologin'] = t['propid']
            t['opass'] = data.get('opass', 'N/A')
        else:
            t['ulogin'] = 'N/A'
            t['upass'] = 'N/A'
            t['ologin'] = t['propid']
            t['opass'] = 'N/A'
        t['time'] = rec.get('arrive', 'N/A')
        t['program'] = rec.get('program', 'N/A')
        t['locations'] = 'Summit'
        t['comments'] = rec.get('comments', '')
        t['ss'] = 'N/A'
        t['operators'] = 'N/A'
        row = fmt % t
        res.append(row)

    print '\n'.join(res)


if __name__ == '__main__':

    # Parse command line options with optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("-d", "--date", dest="opaldate", default=None,
                      help="Specify date (YYYY-MM-DD) of observation")
    optprs.add_option("-f", "--full", dest="full", default=False,
                      action="store_true",
                      help="Give an extended listing")

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

#END


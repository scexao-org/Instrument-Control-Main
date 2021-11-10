#
# sm.py -- g2web plugin for SessionManager web interface
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Jan 19 10:52:42 HST 2012
#]
#

import time
import datetime

import Bunch

from cfg.INS import INSdata as INSconfig
try:
    import Gen2.opal as OPAL
    has_OPAL = True
except ImportError:
    has_OPAL = False

import remoteObjects as ro


# Do we really need this--seems it is not being used
default_sort = 'sessionName'

class sm(object):

    def __init__(self, logger, cfg):
        self.logger = logger
        self.cfg = cfg
        
        self.sm = ro.remoteObjectProxy('sessions')

        if has_OPAL:
            try:
                self.opal = OPAL.OPALinfo()
            except Exception, e:
                self.logger.warn("Couldn't create OPAL object: %s" % (
                        str(e)))
                self.logger.warn("OPAL queries will not be possible")
                self.opal = None
        else:
            self.logger.warn("Couldn't import OPAL module")
            self.logger.warn("OPAL queries will not be possible")
            self.opal = None

        self.opalinfo = {}
        self.opalcnt = 0

        self.insconfig = INSconfig()

        
    def sessions(self, sort=default_sort):
        """Produce the main SessionManager page. 
        """

        # Header string for the generated web page
        page_hdr = """
<html>
<head>
  <TITLE>SessionManager Control</title>
  %(css)s
</head>
<body>
<h2>Session Configuration</h2>
Click on the session name to change session parameters (e.g. prop id) or to 
configure from OPAL.  Click on the allocations to do manual allocation.
<p>
<strong>NOTE: After changing session parameters, please invoke the "Config from
session" menu item in integgui2 to update the client.</strong>
"""

        # Row template for sessions table
        tbl_row = """
        <TR class=%(class)s>
        <TD>%(name)s</TD>
        <TD>%(time_start)s</TD>
        <TD>%(time_update)s</TD>
        <TD>%(propid)s</TD>
        <TD>%(ss)s</TD>
        <TD>%(operator)s</TD>
        <TD>%(observers)s</TD>
        <TD>%(allocs)s</TD>
        </TR>
        """

        # -- PAGE HEADER ---
        my_url = self.cfg.my_url + '/sessions'
        reload_url = my_url + ('?sort=%s' % sort)

        res = [page_hdr % {'css': self.cfg.css}]
        my_url = self.cfg.my_url

        # -- GLOBAL CONTROLS ---
        res.append("<h3>Controls</h3>")

        res.append('<a class=btn2 href="%s">Refresh</a>' % (reload_url))
        res.append("&nbsp;|&nbsp;")
        res.append('<a class=btn2 href="%s/doc/help/index.html">Help</a>' % (
                self.cfg.base_url))
        res.append("<p>Page last refreshed: %s</p>" % time.ctime())

        # -- SESSIONS TABLE ---
        res.append("<h3>Sessions</h3>")
        
        sessions = self.sm.getSessionNames()

        res.append("<table border=1 cellspacing=2 cellpadding=5>")

        d = {'name': '<b>Name</b>',
             'time_start': '<b>Session Created</b>',
             'time_update': '<b>Session Updated</b>',
             'propid': '<b>PropID</b>',
             'ss': '<b>Support Scientist</b>',
             'operator': '<b>Operators</b>',
             'observers': '<b>Observers</b>',
             'allocs': '<b>Allocations</b>',
             'class': 'header',
             }
        res.append(tbl_row % d)
        
        for name in sessions:
            data = self.sm.getSessionInfo(name)

            d = {}
            d['name'] = '<a href="%s/sm_edit/%s">%s</a>' % (
                my_url, data['name'], data['name'])
            #d['name'] = data['name']
            d['time_start'] = time.ctime(data['time_start'])
            d['time_update'] = time.ctime(data['time_update'])
            propid = data.get('propid', 'None')
            d['propid'] = '<a href="%s/sm_getpass/%s">%s</a>' % (
                my_url, propid, propid)
            d['ss'] = data.get('ss', 'None')
            d['operator'] = data.get('operator', 'None')
            d['observers'] = data.get('observers', 'None')
            if len(data['allocs']) == 0:
                allocs = 'None'
            else:
                allocs = ', '.join(data['allocs'])
            d['allocs'] = '<a href="%s/sm_alloc/%s">%s</a>' % (
                my_url, data['name'], allocs)
            d['class'] = 'none'

            res.append(tbl_row % d)

        res.append("</table>")

        res.append('<p><hr width="30%">')
        res.append('<a href="/default">Back to home</a>')
        res.append("</body>\n</html>")

        html = " ".join(res)
        #print html
        return html


    def sm_getpass(self, propid):
        data = self.opal.getProp(propid)

        info = {'css': self.cfg.css}
        info['uacct'] = data.get('ulogin', 'N/A')
        info['upass'] = data.get('upass', 'N/A')
        info['oacct'] = propid
        info['opass'] = data.get('opass', 'N/A')

        html = """
<html>
<head>
  <TITLE>Login Info</title>
  %(css)s
</head>
<body>
<table border=1 cellspacing=2 cellpadding=5>
<tr><th>Login</th><td>%(uacct)s</td><td>%(upass)s</td></tr>
<tr><th>PropID</th><td>%(oacct)s</td><td>%(opass)s</td></tr>
</table>
<p>
Log in to ana or hana with the Login info.
The PropID information is not needed unless you are doing manual
configuration.
</body></html>
""" % info

        return html

    def sm_edit(self, name, opaldate=None):
        """Edit session information for session _name_. 
        """

        # Header string for the generated web page
        page_html = """
<html>
<head>
  <TITLE>Session: %(title)s</title>
  %(css)s
</head>
<body>
<h2>Editing session: %(title)s</h2>
<form action=%(url)s method="get">
<table border=1 cellspacing=2 cellpadding=5>
<tr><th class=header2>PropID</th>
    <td><input type="text" name="propid" size=10 value="%(propid)s"></td>
    </tr>
<tr><th class=header2>Support Scientist</th>
    <td><input type="text" name="ss" size=20 value="%(ss)s"></td>
    </tr>
<tr><th class=header2>Operators</th>
    <td><input type="text" name="operator" size=40 value="%(operator)s"></td>
    </tr>
<tr><th class=header2>Observers</th>
    <td><input type="text" name="observers" size=80 value="%(observers)s"></td>
    </tr>
</table>
<p>
<input class=btn2 type="submit" value="Update">
</form>
<h3>Configure from OPAL</h3>
<table border=1 cellpadding=4>
<tr>
<th>Date</th>
<th>Program</th>
<th>Type</th>
<th>Proposal</th>
<th>PropID</th>
<th>Instr</th>
<th>SS</th>
<th>Observers</th>
<th>Locations</th>
<th>&nbsp;</th>
</tr>
%(opal)s
</table>
<p>
<form action=%(opalurl)s method="get">
Get info from a different date
<input type="text" name="opaldate" size=10 value="%(opaldate)s">
<input class=btn2 type="submit" value="Refresh">
</form>
<p><hr width="30%%">
<a href="/default">Back to home</a>
</body>
</html>
"""

        def make_cfg(data):
            btn_fmt = """<tr><form action="%(url)s" method="get">
<td>%(date)s</td>
<td>%(program)s</td>
<td>%(typ)s</td>
<td>%(proposal)s</td>
<td>%(propid)s</td>
<td>%(instr)s</td>
<td>%(ss)s</td>
<td>%(observers)s</td>
<td>%(locations)s</td>
<td>%(action)s</td>
</form></tr>"""
            return btn_fmt % data


        # -- PAGE HEADER ---
        my_url = self.cfg.my_url

        data = self.sm.getSessionInfo(name)

        d = {}
        d['url'] = ("%s/sm_update/%s" % (my_url, name))
        d['title'] = name
        d['propid'] = data.get('propid', 'None')
        d['ss'] = data.get('ss', 'None')
        d['operator'] = data.get('operator', 'None')
        d['observers'] = data.get('observers', 'None')
        d['opalurl'] = '%s/sm_edit/%s' % (my_url, name)

        #fmt = "%(date)10.10s  %(typ)3.3s  %(proposal)10.10s  %(observers)30.30s  %(ss)15.15s  %(propid)6.6s  %(instr)8.8s"

        opal = []

        now = datetime.datetime.now()
        if opaldate:
            now = now.strptime(opaldate, '%Y-%m-%d')
            
        d['opaldate'] = now.strftime('%Y-%m-%d')

        if self.opal != None:
            try:
                opalinfo = self.opal.getInfoForNight(now, table='tsr')
                for rec in opalinfo:
                    t = {}
                    t.update(rec)
                    self.opalinfo[self.opalcnt] = rec
                    form_url = '%s/sm_config/%s/%d' % (my_url, name, self.opalcnt)
                    self.opalcnt += 1
                    t['date'] = rec['date'].strftime("%Y-%m-%d")
                    t['typ'] = 'TSR'
                    t['ss'] = rec['sslist']
                    t['instr'] = rec.get('instr', 'N/A')
                    t['propid'] = rec.get('propid', 'N/A')
                    t['time'] = rec.get('arrive', 'N/A')
                    t['program'] = rec.get('program', 'N/A')
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
                    t['url'] = form_url
                    t['action'] = '<input class=btn2 type="submit" value="Configure">'
                    row = make_cfg(t)
                    opal.append(row)

                opalinfo = self.opal.getInfoForNight(now)
                for rec in opalinfo:
                    t = {}
                    t.update(rec)
                    self.opalinfo[self.opalcnt] = rec
                    form_url = '%s/sm_config/%s/%d' % (my_url, name, self.opalcnt)
                    self.opalcnt += 1
                    t['date'] = rec['datein'].strftime("%Y-%m-%d")
                    t['typ'] = '&nbsp;'
                    t['observers'] = rec['last'] + '&nbsp;'
                    t['instr'] = rec.get('instr', 'N/A')
                    t['propid'] = rec.get('propid', 'N/A')
                    t['time'] = rec.get('arrive', 'N/A')
                    t['program'] = rec.get('program', 'N/A')
                    t['locations'] = 'Summit'
                    t['ss'] = 'N/A'
                    t['url'] = form_url
                    t['action'] = '&nbsp;'
                    row = make_cfg(t)
                    opal.append(row)

                d['opal'] = ''.join(opal)
            except Exception, e:
                d['opal'] = "Can't access OPAL: %s" % (str(e))
        else:
            d['opal'] = ''
        d['css'] = self.cfg.css
        
        html = page_html % d
        return html


    def sm_update(self, name, **kwdargs):
        """Update session information for session _name_. 
        """
        print "name=%s, kwdargs=%s" % (name, str(kwdargs))

        params = self.sm.getSessionInfo(name)

        # TODO: use url escape
        for key, val in kwdargs.items():
            kwdargs[key] = kwdargs[key].replace('+', ' ')
            
        args = Bunch.Bunch(kwdargs)
        
        # TODO: form verification
        params['propid'] = args.propid
        params['ss'] = args.ss
        params['operator'] = args.operator
        params['observers'] = args.observers

        res = self.sm.updateSession(name, params)

        return self.sessions()


    def sm_config(self, name, index):
        """Configure session for session _name_. 
        """
        index = int(index)
        print "name=%s, index=%d" % (name, index)

        params = self.sm.getSessionInfo(name)

        try:
            opalrec = {}
            opalrec.update(self.opalinfo[index])
            # TEMP: hack to remote unmarshallable datetime.date objects
            for key in opalrec.keys():
                if isinstance(opalrec[key], datetime.date):
                    opalrec[key] = None

            # hack for telescope engineering TSRs
            if opalrec['instr'].lower() == '-none':
                opalrec['instr'] = 'SUKA'

            self.logger.info("opalrec=%s" % (str(opalrec)))
            res = self.sm.configureFromOPAL(opalrec, name, params['key'])
        
        except KeyError:
            print "Stale OPAL key, refresh the page!"
        
        return self.sessions()


    def sm_alloc(self, name):
        """Edit allocation information for session _name_. 
        """

        # Header string for the generated web page
        page_html = """
<html>
<head>
  <TITLE>Session: %(title)s</title>
  %(css)s
</head>
<body>
<h2>Allocations for session: %(title)s</h2>
<form action=%(url)s/alloc/%(name)s method="get">
<h3>Typical Allocation</h3>
Only one primary instrument can be selected.
Additional allocations will be automatically added that are necessary
for observation.
<p>
Hold down the Ctrl key to select multiple secondary instruments.
<p>
<p>
<table cols=2>
  <tr><th>Primary</th>
      <th>Secondary</th>
  </tr>
  <tr><td>
<select name="pri_inst" size="10">
%(inslist)s
</select>
      </td>
      <td>
<select multiple name="sec_inst" size="10">
%(inslist)s
</select> <br>
      </td>
  </tr>
  <tr>
    <td colspan=2>
<input class=btn2 type="submit" value="Alloc">
      </td>
  </tr>
</table>
</form>
<p>
Deallocate everything allocated to this session.
<p>
<form action=%(url)s/dealloc_all/%(name)s  method="get">
<input class=btn2 type="submit" value="Dealloc All">
</form>
<p>
<form action=%(url)s/alloc/%(name)s method="get">
<h3>Custom Allocations</h3>
<textarea name="allocs" cols=80 rows=3>
%(allocs)s
</textarea> <br>
<input class=btn2 type="submit" value="Alloc">
</form>
<p>
<form action=%(url)s/dealloc/%(name)s  method="get">
<h3>Custom Deallocations</h3>
<textarea name="allocs" cols=80 rows=3>
%(allocs)s
</textarea> <br>
<input class=btn2 type="submit" value="Dealloc">
</form>
<p><hr width="30%%">
<a href="/default">Back to home</a>
</body>
</html>
"""

        # -- PAGE HEADER ---
        my_url = self.cfg.my_url

        data = self.sm.getSessionInfo(name)

        d = {}
        d['url'] = my_url
        d['name'] = name
        d['title'] = name
        allocs = data['allocs']
        allocs.sort()
        if len(allocs) == 0:
            allocs = ''
        else:
            allocs = ', '.join(allocs)
        d['allocs'] = allocs

        d['inslist'] = '\n'.join(['<option value="%s">%s</option>' % (
            ins, ins) for ins in self.insconfig.getNames()])
        d['css'] = self.cfg.css

        html = page_html % d
        return html


    def alloc(self, name, **kwdargs):
        """Update allocations for session _name_. 
        """
        params = self.sm.getSessionInfo(name)

        args = Bunch.Bunch(kwdargs)

        # First, deallocate everything
        self.sm.deallocateAll(name, params['key'])

        if args.has_key('pri_inst'):
            allocs = args.pri_inst
            if type(allocs) == str:
                # Ugh--wierd URL encoding hackaround
                allocs = allocs.strip().replace('+','')
                allocs = allocs.split(',')

            assert(len(allocs) == 1)
            mainObcp = allocs[0]

            if args.has_key('sec_inst'):
                itemList = args.sec_inst
                if type(itemList) == str:
                    # Ugh--wierd URL encoding hackaround
                    itemList = itemList.strip().replace('+','')
                    itemList = itemList.split(',')
            else:
                itemList = []
            
            self.logger.debug("mainObcp=%s itemList='%s'" % (
                mainObcp, itemList))
            self.sm.alloc(mainObcp, itemList)

        else:
            # "custom" alloc
            instlist = args.allocs.strip().replace('+','')
            itemList = instlist.split(',')
            self.sm.allocate(itemList, name, params['key'])
        
        return self.sessions()


    def dealloc(self, name, **kwdargs):
        """Update allocations for session _name_. 
        """
        params = self.sm.getSessionInfo(name)

        args = Bunch.Bunch(kwdargs)
        itemList = args.allocs
        self.logger.debug("itemList='%s'" % itemList)
        if type(itemList) == str:
            # Ugh--wierd URL encoding hackaround
            itemList = args.allocs.strip().replace('+','')
            itemList = itemList.split(',')

        self.sm.deallocate(itemList, name, params['key'])
        
        return self.sessions()


    def dealloc_all(self, name, **kwdargs):
        """Update allocations for session _name_. 
        """
        params = self.sm.getSessionInfo(name)

        self.sm.deallocateAll(name, params['key'])
        
        return self.sessions()


#END

#!/usr/bin/env python
#
# bm_web.py -- make remoteObjectManagerSvc/BootManager information
#   available via a web browser
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Sun Oct 10 14:08:30 HST 2010
#]
#
"""
This is a web browser-based GUI for the Gen2 BootManager application.
It allows one to control and monitor the status of the various running
processes in Gen2.

Typical use (solo configuration, default port 20000):

    $ cd $GEN2HOME
    $ web/bm_web.py --config=solo --detach
    
"""

import sys, os, signal, time
import re
import threading
import datetime
import traceback
import pprint
import urllib

# --- TEMP, until we figure out configuration issues ---
thisDir = os.path.split(sys.modules[__name__].__file__)[0]
moduleHome = '%s/..' % (thisDir)
sys.path.insert(1, moduleHome)
# ------------------------------------------------------
import pyfits

import Bunch
import remoteObjects as ro
from cfg.INS import INSdata as INSconfig
import Gen2.BootManager as BM
import cfg.g2soss as g2soss
import Gen2.db.frame as framedb
import tools.pama as pama
import ssdlog
import cgisrv
try:
    import Gen2.opal as OPAL
    has_OPAL = True
except ImportError:
    has_OPAL = False

# PA/MA settings file
try:
    pamafile = '%s/cfg/PAMA.yml' % (os.environ['PYHOME'])
except KeyError:
    pamafile = None

LOG_FORMAT = '%(asctime)s %(levelno)3.3d S:%(filename)s,L:%(lineno)d,FN:%(funcName)s,TID:%(thread)d  %(message)s'

version = "20100910.0"


# Default item to sort on
default_sort = 'level'

# Where documents are stored that should be fetched
document_root = os.environ['GEN2HOME'] + "/docs"


css = """
  <STYLE type="text/css">
.header {border-width: 1; border: solid; background-color: #AAAAAA}
.header2 {background-color: #AAAAAA}
.even {border-width: 1; border: solid; background-color: #99FF66}
.odd  {border-width: 1; border: solid; background-color: #99CC66}
.warn  {border-width: 1; border: solid; background-color: #FF9966}
.down  {border-width: 1; border: solid; background-color: #DDDDDD}
.periodic  {border-width: 1; border: solid; background-color: #99CCFF}
.btn  {border-width: 0; background-color: #CCFF99;
       text-decoration: none; color: black; padding: 2px 4px; }
.btn2 {border-width: 1px; border: groove; background-color: #CCFF99;
       text-decoration: none; color: black; padding: 2px 4px; }
  </STYLE>
"""

class bm_cgi(cgisrv.CGIobject):
    """This is the main application object, which contains the methods
    that will be called from the CGI interface.
    """

    def __init__(self, bm, title, logger):
        self.bm = bm
        self.title = title
        self.logger = logger

        ro.init()
        self.sm = ro.remoteObjectProxy('sessions')
        self.tsc = ro.remoteObjectProxy('TSC')
        self.status = ro.remoteObjectProxy('status')
        self.fv = ro.remoteObjectProxy('fitsview')
        self.fv1 = ro.remoteObjectProxy('fitsview1')

        self.insconfig = INSconfig()

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

        # For doing pa/ma settings changes
        self.pama = pama.PAMASettings(self.logger)
        if pamafile and os.path.exists(pamafile):
            self.pama.loadYAML(pamafile)

        # Set up display maps
        self.dispmap = {}
        for loc in ['summit', 'hilo', 'mitaka', 'ocs', 'mogi', 'default']:
            d = {'ul': 's6', 'll': 's5',
                 'um': 's4', 'lm': 's3',
                 'ur': 's2', 'lr': 's1',
                 }
            self.dispmap[loc] = d

        super(bm_cgi, self).__init__(None)


    def _my_base_url(self):
        return '%s://%s:%d' % (self.proto, self.host, self.port)

    def _my_url(self):
        return '%s%s' % (self._my_base_url(), self.path)

    def restart(self, svcname, sort=default_sort):
        try:
            level = float(svcname)
            self.bm.restart(level)

        except ValueError:
            self.bm.restart(svcname)
        
        return self.bm_page(sort=sort)


    def restart_host(self, host, svcname, sort=default_sort):

        self.bm.restart_host(host, svcname)
       
        return self.bm_page(sort=sort)


    def stop(self, svcname, sort=default_sort):
        try:
            level = float(svcname)
            self.bm.stop(level)

        except ValueError:
            self.bm.stop(svcname)
        
        return self.bm_page(sort=sort)


    def stop_host(self, host, svcname, sort=default_sort):

        self.bm.stop_host(host, svcname)
       
        return self.bm_page(sort=sort)


    def start(self, svcname, sort=default_sort):
        try:
            level = float(svcname)
            self.bm.start(level)

        except ValueError:
            self.bm.start(svcname)
        
        return self.bm_page(sort=sort)


    def start_host(self, host, svcname, sort=default_sort):

        self.bm.start_host(host, svcname)
       
        return self.bm_page(sort=sort)


    def bootctl(self, btype='levels', action='none', **kwdargs):

        self.logger.debug("kwdargs=%s" % str(kwdargs))

        action = action.lower()
        if btype == 'levels':
            levels = kwdargs['levels']
            # hack for cgisrv
            if isinstance(levels, str):
                levels = [ levels ]
            args = map(float, levels)
        else:
            services = kwdargs['services']
            # hack for cgisrv
            if isinstance(services, str):
                services = [ services ]
            args = services

        for arg in args:
            if action == 'start':
                self.bm.start(arg)
            elif action == 'stop':
                self.bm.stop(arg)
            elif action == 'restart':
                self.bm.restart(arg)
            
        return self.bm_page(sort=kwdargs['sort'])


    def stopall(self, sort=default_sort):
        self.bm.stopall()
        
        return self.bm_page(sort=sort)


    def shutdown(self, sort=default_sort):
        self.bm.shutdown()
        
        return self.bm_page(sort=sort)


    def reloadConfig(self, sort=default_sort):
        self.bm.reloadConfig()
        
        return self.bm_page(sort=sort)


    def setup(self, sort=default_sort):
        self.bm.setup()
        
        return self.bm_page(sort=sort)


    def uptime(self, sort=default_sort):

        return self.bm_page(sort=sort)


    def bm_page(self, sort=default_sort):
        """Produce the main BootManager page. 
        """

        # Header string for the generated web page
        page_hdr = """
<html>
<head>
  <TITLE>BootManager Control: %(title)s</title>
  %(css)s
</head>
<body>
<h2>BootManager Web Interface: <i>%(title)s</i> configuration</h2>
"""

        # Row template for services table
        uptime_hdr_row = """

        <TR class=%(class)s>
        <TD>%(check)s</TD>
        <TD>%(svcname)s</TD>
        <TD>%(level)s</TD>
        <TD>%(count)s</TD>
        <TD>%(hostlist)s</TD>
        <TD>%(uptime_r)s</TD>
        <TD>%(start)s</TD>
        <TD>%(stop)s</TD>
        <TD>%(restart)s</TD>
        <TD>%(log)s</TD>
        </TR>
        """

        # Row template for hosts table
        hosts_tbl_hdr = """
        <TR class=%(class)s>
        <TD>%(svcname)s</TD>
        <TD>%(level)s</TD>
        <TD>%(count)s</TD>
        """

        # Row template for levels table
        level_tbl_row = """
        <TR class=%(class)s>
        <TD>%(check)s</TD>
        <TD>%(level)s</TD>
        <TD>%(svcnames)s</TD>
        <TD>%(start)s</TD>
        <TD>%(stop)s</TD>
        <TD>%(restart)s</TD>
        </TR>
        """

        # -- PAGE HEADER ---
        base_url = self._my_base_url()
        my_url = base_url + '/uptime'
        reload_url = my_url + ('?sort=%s' % sort)

        d = {'reload': reload_url,
             'title': self.title,
             'css': css,
            }
        res = [page_hdr % d]
        my_url = self._my_base_url()

        data = self.bm.sl_info()

        level_warn = {}

        services = {}
        hosts = set([])

        # Add links for stop/start/restart
        for d in data:
            host = d['hostname']
            hosts.add(host)

            svcname = d['svcname']
            sd = services.setdefault(svcname, {})
            sd['svcname'] = svcname
            hd = sd.setdefault('hosts', {})
            hd[host] = d

            sd['start'] = '<a class=btn2 href="%s/start/%s?sort=%s">start</a>' % (
                my_url, svcname, sort)
            sd['stop'] = '<a class=btn2 href="%s/stop/%s?sort=%s">stop</a>' % (
                my_url, svcname, sort)
            sd['restart'] = '<a class=btn2 href="%s/restart/%s?sort=%s">restart</a>' % (
                 my_url, svcname, sort)
            sd['check'] = '<input type="checkbox" name="services" value="%s" />' % (
                svcname)
            sd['class'] = 'even'

            d['start'] = '<a class=btn2 href="%s/start_host/%s/%s?sort=%s">start</a>' % (
                my_url, d['hostname'], svcname, sort)
            d['stop'] = '<a class=btn2 href="%s/stop_host/%s/%s?sort=%s">stop</a>' % (
                my_url, d['hostname'], svcname, sort)
            d['restart'] = '<a class=btn2 href="%s/restart_host/%s/%s?sort=%s">restart</a>' % (
                my_url, d['hostname'], svcname, sort)

            # Interpret data more user-friendly than just seconds up
            uptime = d['uptime']
            if not isinstance(uptime, float):
                d['uptime_r'] = '<strong>N/A</strong>'

            elif uptime <= 0:
                d['uptime_r'] = '<strong>NOT RUNNING</strong>'

            elif uptime < 60.0:
                d['uptime_r'] = '%.2f secs' % uptime

            elif uptime < 3600.0:
                d['uptime_r'] = '%.2f mins' % (uptime/60.0)

            elif uptime < 86400.0:
                d['uptime_r'] = '%.2f hours' % (uptime/3600.0)

            elif uptime < 604800.0:
                d['uptime_r'] = '%.2f days' % (uptime/86400.0)

            elif uptime < 31449600.0:
                d['uptime_r'] = '%.2f weeks' % (uptime/604800.0)

            else:
                d['uptime_r'] = '%.2f years' % (uptime / 31449600.0)

            # Track maximum uptime
            old_uptime = sd.setdefault('uptime', uptime)
            if uptime >= old_uptime:
                sd['uptime'] = uptime
                sd['uptime_r'] = d['uptime_r']
                sd['uptime_host'] = host

            svinfo = self.bm.get_svcinfo(svcname)
            sd['description'] = svinfo.get('description', '[N/A]')
            flags = svinfo.get('flags', [])
            sd['periodic'] = ('manual' in flags) or \
                                 (svinfo.get('periodic', False))
            logname = svinfo.get('stdout', None)
            if logname:
                sd['log'] = '<a href="%s/getlog?logname=%s">log</a>' % (
                    base_url, logname)
            else:
                sd['log'] = 'N/A'
            #pprint.pprint(svinfo)

            # Count number of instances we see of this svcname go by
            counted = sd.setdefault('counted', 0)
            if isinstance(uptime, float) and (uptime > 0):
                sd['counted'] = counted + 1
            sd['count'] = str(svinfo['count'])

            #d['log'] = svinfo.get('stdout', '[N/A]')

            level = d['level']
            #d['level'] = str(level)
            d['level'] = level
            sd['level'] = level
            level_warn.setdefault(level, {'flag': 0, 'count': 0,
                                          'counted': 0})
            d['class'] = 'plain'

        # Sort the data according to the selected column
        svcs = services.values()
        svcs.sort(lambda x, y: cmp(x[sort], y[sort]))

        # If sort order was by level, then alternately shade
        # the rows when there is a level change
        if (sort == 'level'):
            last_level = 0
            last_class = 'even'

            for d in svcs:
                level = float(d['level'])
                if level == last_level:
                    d['class'] = last_class
                else:
                    last_level = level
                    if last_class == 'even':
                        last_class = 'odd'
                    else:
                        last_class = 'even'
                    d['class'] = last_class
            

        # Last check of the counts.  Alter the class of the service
        # and level table entries to turn the background red if it is
        # an instance that is not running and it is below the count
        #print counts, counted
        for svcname, d in services.items():
            host_l = d['hosts'].keys()
            host_l.sort()
            d['hostlist'] = ', '.join(host_l)

            w = level_warn[float(d['level'])]
            w['count'] += int(d['count'])
            w['counted'] += d['counted']

            if d['counted'] < int(d['count']):
                w['flag'] += 1
                if d['counted'] == 0:
                    if d['periodic']:
                        d['class'] = 'periodic'
                    else:
                        d['class'] = 'down'
                else:
                    d['class'] = 'warn'
                    
        # -- GLOBAL CONTROLS ---
        res.append("<h3>Controls</h3>")

        res.append('<a class=btn2 href="%s">Refresh</a>' % (reload_url))
        res.append("&nbsp;|&nbsp;")
        res.append('<a class=btn2 href="%s/stopall?sort=%s">Stop All</a>' % (
                my_url, sort))
        res.append("&nbsp;|&nbsp;")
        res.append('<a class=btn2 href="%s/reloadConfig?sort=%s">Reload</a>' % (
                my_url, sort))
        res.append("&nbsp;|&nbsp;")
        res.append('<a class=btn2 href="%s/setup?sort=%s">Push Out</a>' % (
                my_url, sort))
        res.append("&nbsp;|&nbsp;")
        res.append('<a class=btn2 href="%s/shutdown?sort=%s">Shut Down</a>' % (
                my_url, sort))
        res.append("&nbsp;|&nbsp;")
        res.append('<a class=btn2 href="%s/doc/help/index.html">Help</a>' % (
                my_url))
        res.append("<p>Page last refreshed: %s</p>" % time.ctime())
        

        # -- LEVELS TABLE ---
        res.append("<h3>Levels</h3>")
        res.append('<form action=%s/bootctl?sort=%s method="get">' % (
            my_url, sort))
        res.append('<input type="hidden" name="btype" value="levels" />')
        res.append('<input type="hidden" name="sort" value="%s" />' % sort)
        
        # Print levels control table
        levels = self.bm.get_levels()

        res.append("<table border=1 cellspacing=2 cellpadding=5>")

        d = {'check': '<b>Select</b>',
             'level': '<b>Level</b>',
             'svcnames': '<b>Services</b>',
             'uptime': '<b>Uptime</b>',
             'start': '<b>Start</b>',
             'stop': '<b>Stop</b>',
             'restart': '<b>Restart</b>',
             'class': 'header',
             }
        res.append(level_tbl_row % d)
        
        last_level = 0
        last_class = 'even'

        for level in levels:
            
            svcnames = self.bm.getSvcs(lambda info: info['level'] == level)
            svcnames.sort()
            d['check'] = '<input type="checkbox" name="levels" value="%d" />' % (
                level)
            d['level'] = str(level)
            d['svcnames'] = ', '.join(svcnames)
            d['uptime_r'] = 'N/A'
            d['start'] = '<a class=btn2 href="%s/start/%f?sort=%s">start</a>' % (
                my_url, level, sort)
            d['stop'] = '<a class=btn2 href="%s/stop/%f?sort=%s">stop</a>' % (
                my_url, level, sort)
            d['restart'] = '<a class=btn2 href="%s/restart/%f?sort=%s">restart</a>' % (
                my_url, level, sort)

            if level == last_level:
                d['class'] = last_class
            else:
                last_level = level
                if last_class == 'even':
                    last_class = 'odd'
                else:
                    last_class = 'even'
                d['class'] = last_class

            # If this level contains a service that doesn't have the
            # proper count level, flag it red
            w = level_warn[level]
            if w['flag'] > 0:
                if w['counted'] == 0:
                    d['class'] = 'down'
                else:
                    d['class'] = 'warn'

            res.append(level_tbl_row % d)
            
        res.append("</table><p>")
        res.append('<input class=btn2 type="submit" name="action" value="Start" />')
        res.append('<input class=btn2 type="submit" name="action" value="Stop" />')
        res.append('<input class=btn2 type="submit" name="action" value="Restart" />')
        res.append("</form>")
            
        # -- SERVICES TABLE ---
        res.append("<h3>Services</h3>")
        res.append('<form action=%s/bootctl?sort=%s method="get">' % (
            my_url, sort))
        res.append('<input type="hidden" name="btype" value="services" />')
        res.append('<input type="hidden" name="sort" value="%s" />' % sort)
        res.append("<table border=1 cellspacing=2 cellpadding=5>")

        d = {'check': '<b>Select</b>',
             'svcname': '<b><a href="%s/uptime?sort=svcname">Service</a></b>' % my_url,
             'level': '<b><a href="%s/uptime?sort=level">Level</a></b>' % my_url,
             'count': '<b><a href="%s/uptime?sort=count">Count</a></b>' % my_url,
             'hostlist': '<b>Hosts</b>',
             'uptime_r': '<b><a href="%s/uptime?sort=uptime">Uptime</a></b>' % my_url,
             'start': '<b>Start</b>',
             'stop': '<b>Stop</b>',
             'restart': '<b>Restart</b>',
             'log': '<b>Log</b>',
             'class': 'header',
             }
        #pprint.pprint(d)
        res.append(uptime_hdr_row % d)

        for d in svcs:
            res.append(uptime_hdr_row % d)

        res.append("</table><p>")
        res.append('<input class=btn2 type="submit" name="action" value="Start" />')
        res.append('<input class=btn2 type="submit" name="action" value="Stop" />')
        res.append('<input class=btn2 type="submit" name="action" value="Restart" />')
        res.append("</form>")


        # -- HOSTS TABLE ---
        res.append("<h3>Hosts</h3>")
        res.append('<form action=%s/bootctl?sort=%s method="get">' % (
            my_url, sort))
        res.append('<input type="hidden" name="btype" value="hosts" />')
        res.append("<table border=1 cellspacing=2 cellpadding=5>")

        # Prepare hosts table header
        l = [ hosts_tbl_hdr ]
        hosts = list(hosts)
        hosts.sort()
        for host in hosts:
            l.append("<TD>%%(%s)s</TD>" % host)
        l.append("</TR>")
        hosts_hdr = ''.join(l)

        d = {'svcname': '<b>Service</b>',
             'level': '<b>Level</b>',
             'count': '<b>Count</b>',
             'class': 'header',
             }
        for host in hosts:
            d[host] = ("<b>%s</b>" % host)

        res.append(hosts_hdr % d)
        for d in svcs:
            host_d = d['hosts']
            host_d_keys = host_d.keys()
            for host in hosts:
                try:
                    if host_d[host]['uptime'] <= 0:
                        host_d[host]['uptime_r'] = ''

                    d[host] = ("%(uptime_r)s<p>%(start)s %(stop)s %(restart)s" % host_d[host])
                except KeyError:
                    d[host] = 'N/A'

            res.append(hosts_hdr % d)

        res.append("</form>")
        res.append("</table>")
        res.append('<p><hr width="30%">')
        res.append('<a href="/default">Back to home</a>')
        res.append("</body>\n</html>")

        html = " ".join(res)
        #print html
        return html

        
    def getlog(self, logname=None, n=500):
        """Show the detail for a log _logname_.
        """

        # Header string for the generated web page
        page_hdr = """
<html>
<head>
  <TITLE>Log: %(logname)s</title>
  %(css)s
</head>
<body>
<h3>Tail of log "%(logname)s"</h3>
<pre>
%(logdata)s
</pre>
<p>
<form action=%(url)s method="get">
Last N lines: <input type="text" name="n" size=4 value="%(n)d">
Log:   <input type="text" name="logname" size=20 value="%(logname)s">
<input class=btn2 type="submit" value="Reload">
<p><hr width="30%%">
<a href="/default">Back to home</a>
</body>
</html>
"""
        # -- PAGE HEADER ---
        my_url = self._my_base_url() + '/getlog'
        n = int(n)
        if not '.' in logname:
            logname += '.log'

        d = {'css': css,
             'url': my_url,
             'n': n,
             'logname': logname,
             }

        try:
            if not logname.startswith('/'):
                logpath = os.path.join(g2soss.loghome, logname)
            else:
                logpath = logname

            dir, fn = os.path.split(logpath)
            tmpname = '/tmp/%s.tail' % (fn)

            cmdstr = "tail --lines=%d %s > %s" % (n, logpath, tmpname)
            res = os.system(cmdstr)

            in_f = open(tmpname, 'r')
            try:
                d['logdata'] = in_f.read()
            finally:
                in_f.close()
                                   
        except Exception, e:
            d['logdata'] = "Sorry, that log is not available.<p><tt>%s</tt>" % (
                str(e))
            
        return page_hdr % d


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
        my_url = self._my_base_url() + '/sessions'
        reload_url = my_url + ('?sort=%s' % sort)

        res = [page_hdr % {'css': css}]
        my_url = self._my_base_url()

        # -- GLOBAL CONTROLS ---
        res.append("<h3>Controls</h3>")

        res.append('<a class=btn2 href="%s">Refresh</a>' % (reload_url))
        res.append("&nbsp;|&nbsp;")
        res.append('<a class=btn2 href="%s/doc/help/index.html">Help</a>' % (
                my_url))
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


    def sm_restart_ig(self, sort=default_sort):
        # TODO: change this to invoke the "Config from session" command in integgui2
        #self.bm.restart('integgui')

        return self.sessions(sort=sort)
    
    def sm_getpass(self, propid):
        data = self.opal.getProp(propid)

        info = {'css': css}
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
Log in to vgw, ows2, ows1 and ana with the Login info.
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
<td><input class=btn2 type="submit" value="Configure"></td>
</form></tr>"""
            return btn_fmt % data


        # -- PAGE HEADER ---
        my_url = self._my_base_url()

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
                row = make_cfg(t)
                opal.append(row)

            d['opal'] = ''.join(opal)
        else:
            d['opal'] = ''
        d['css'] = css
        
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
            opalrec = self.opalinfo[index]

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
        my_url = self._my_base_url()

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
        d['css'] = css

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


    def frames(self, sort=default_sort, fromdate=None, todate=None):
        """Produce the main Frames page. 
        """

        # Header string for the generated web page
        page_hdr = """
<html>
<head>
  <TITLE>Frames</title>
  %(css)s
</head>
<body>
"""

        # Row template for frames table
        tbl_row = """
        <TR class=%(class)s>
        <TD>%(check)s</TD>
        <TD>%(frameid)s</TD>
        <TD>%(time_alloc)s</TD>
        <TD>%(time_saved)s</TD>
        <TD>%(time_hilo)s</TD>
        </TR>
        """

        # -- PAGE HEADER ---
        base_url = self._my_base_url()
        my_url = base_url + '/frames'
        reload_url = my_url + ('?sort=%s' % sort)

        res = [page_hdr % {'css': css}]

        now = datetime.datetime.now()

        if todate:
            todate = urllib.unquote_plus(todate)
            todate_t = datetime.datetime.strptime(todate, '%Y-%m-%d %H:%M:%S')
        else:
            todate_t = datetime.datetime.now()
            
        if fromdate:
            fromdate = urllib.unquote_plus(fromdate)
            fromdate_t = datetime.datetime.strptime(fromdate, '%Y-%m-%d %H:%M:%S')
        else:
            fromdate_t = datetime.datetime.fromtimestamp(time.time() - 86400)
            
        fromdate_s = fromdate_t.strftime('%Y-%m-%d %H:%M:%S')
        todate_s = todate_t.strftime('%Y-%m-%d %H:%M:%S')
        
        # -- GLOBAL CONTROLS ---
        res.append("<h3>Controls</h3>")

        res.append('<a class=btn2 href="%s">Refresh</a>' % (reload_url))
        res.append("&nbsp;|&nbsp;")
        res.append('<a class=btn2 href="%s/doc/help/index.html">Help</a>' % (
                my_url))
        res.append("<p>Page last refreshed: %s</p>" % time.ctime())

        # -- FRAMES TABLE ---
        res.append("<h3>Recent Frames</h3>")
        
        framelist = framedb.getFramesByDate(fromdate_t, todate_t)
        # TODO: allow sorting options
        framelist.reverse()

        res.append("<table border=1 cellspacing=2 cellpadding=5>")
        res.append('<form action=%s/framectl method="get">' % (base_url))
        res.append('<input type="hidden" name="fromdate" value="%s">' % fromdate_s)
        res.append('<input type="hidden" name="todate" value="%s">' % todate_s)

        d = {'check': '<b>Select</b>',
             'frameid': '<b>Frame ID</b>',
             'time_alloc': '<b>Time Allocated</b>',
             'time_saved': '<b>Time Received</b>',
             'time_hilo': '<b>Sent to STARS</b>',
             'class': 'header',
             }
        res.append(tbl_row % d)
        
        for data in framelist:

            d = {}
            d['check'] = '<input type="checkbox" name="frames" value="%s" />' % (
                data['frameid'])

            frameid = data['frameid']
            fitspath = self._get_fitspath(frameid)

            if os.path.exists(fitspath):
                d['frameid'] = '<a href="%s/getfitsheader/%s">%s</a>' % (
                    base_url, frameid, frameid)
            else:
                d['frameid'] = frameid
                
            d['class'] = 'none'

            if isinstance(data['time_alloc'], datetime.datetime):
                d['time_alloc'] = data['time_alloc'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                d['time_alloc'] = 'N/A'
                d['class'] = 'warn'
            if isinstance(data['time_saved'], datetime.datetime):
                d['time_saved'] = data['time_saved'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                d['time_saved'] = 'N/A'
                d['class'] = 'warn'
            if isinstance(data['time_hilo'], datetime.datetime):
                d['time_hilo'] = data['time_hilo'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                d['time_hilo'] = 'N/A'
                d['class'] = 'warn'

            res.append(tbl_row % d)

        res.append("</table>")
        res.append('<p><input class=btn2 type="submit" name="action" value="Show in FITS viewer" />')
        res.append('<!-- input class=btn2 type="submit" name="action" value="Retry instrument transfer" /-->')
        res.append('<!-- input class=btn2 type="submit" name="action" value="Retry STARS transfer" /-->')
        res.append('</form>')

        res.append("""<p>
<form action=%(url)s method="get">
Specify different date range (format YYYY-MM-DD HH:MM:SS): <p>
<input type="text" name="fromdate" size=20 value="%(fromdate)s">
<input type="text" name="todate" size=20 value="%(todate)s">
<input class=btn2 type="submit" value="Reload">
</form>""" % ({
    'url': my_url,
    'fromdate': fromdate_s,
    'todate': todate_s,
    }))

        res.append('<p><hr width="30%">')
        res.append('<a href="/default">Back to home</a>')
        res.append("</body>\n</html>")

        html = " ".join(res)
        #print html
        return html


    def _get_fitspath(self, frameid):
        match = re.match('^(\w{3})([AQ])(\d)(\d{7})$', frameid)
        if not match:
            raise IOError("Bad frameid '%s'" % frameid)

        (inscode, frtype, prefix, number) = match.groups()
        insname = self.insconfig.getNameByCode(inscode)

        fitspath = os.path.abspath(os.path.join(g2soss.datahome,
                                                insname,
                                                "%s.fits" % frameid))
        return fitspath

    
    def getfitsheader(self, frameid):
        """Show the detail for a frame _frameid_.
        """

        # Header string for the generated web page
        page_hdr = """
<html>
<head>
  <TITLE>Frame: %(frameid)s</title>
  %(css)s
</head>
<body>
"""

        # Row template for fits header
        tbl_row = """
        <TR class=%(class)s>
        <TD>%(kwd)s</TD>
        <TD>%(val)s</TD>
        </TR>
        """

        # -- PAGE HEADER ---
        base_url = self._my_base_url()
        my_url = base_url + '/frames'

        frameid = frameid.upper()
        res = [page_hdr % {'css': css,
                           'frameid': frameid}]

        # -- FRAMES TABLE ---
        res.append("<h3>%s</h3>" % frameid)
        res.append('<a href="%s/framectl?frames=%s&action=show">View frame in FITS viewers</a>' % (
                (base_url, frameid)))
        
        try:
            fitspath = self._get_fitspath(frameid)
            
            fits_f = pyfits.open(fitspath, "readonly")
            try:
                res.append("<h4>FITS Header</h4>")
                res.append("<table border=1 cellspacing=2 cellpadding=5>")

                d = {'kwd': '<b>Keyword</b>',
                     'val': '<b>Value</b>',
                     'class': 'header',
                     }
                res.append(tbl_row % d)

                # this seems to be necessary now for some fits files...
                fits_f.verify('fix')
    
                header = fits_f[0].header
                keys = []
                for key, val in header.items():
                    keys.append(key)
                keys.sort()
                for key in keys:
                
                    d = {}
##                 d['check'] = '<input type="checkbox" name="frames" value="%s" />' % (
##                     data['frameid'])
                    d['kwd'] = '%-8.8s' % key
                    d['val'] = str(header[key])
                    d['class'] = 'none'

                    res.append(tbl_row % d)

                res.append("</table>")

            finally:
                fits_f.close()
        
        except Exception, e:
            res.append("Sorry, that frame is not available.<p><tt>%s</tt>" % (
                str(e)))
            
        res.append('<p><hr width="30%">')
        res.append('<a href="/default">Back to home</a>')
        res.append("</body>\n</html>")

        html = " ".join(res)
        #print html
        return html


    def framectl(self, frames=[], action='none', fromdate=None, todate=None):
        action = action.lower()
        # hack needed because cgisrv delivers singly selected list items as a
        # string
        if isinstance(frames, str):
            frames = [ frames ]
        self.logger.debug("action=%s frames=%s" % (
                action, str(frames)))

        try:
            for frameid in frames:
                fitspath = self._get_fitspath(frameid)
                if action.startswith("show"):
                    self.fv.display_fitsfile(fitspath)
                    self.fv1.display_fitsfile(fitspath)

        except Exception, e:
            self.logger.error(str(e))

        if not fromdate:
            return self.getfitsheader(frameid)
        else:
            return self.frames(fromdate=fromdate, todate=todate)


    def tscctl(self, cmd, **kwdargs):
        """TSC controls
        """

        def interp_res(res):
            try:
                table = { ro.OK: 'OK', ro.ERROR: 'NG' }
                return table[res]
            except KeyError:
                return res
            
        try:
            if cmd == 'lockon':
                res = self.tsc.safetyLockOn()
                res = interp_res(res)
                return self.tscctl('view', res=res)
            if cmd == 'lockoff':
                res = self.tsc.safetyLockOff()
                res = interp_res(res)
                return self.tscctl('view', res=res)
            if cmd == 'login':
                res = self.tsc.tsc_login()
                # Ugh!...give time for command to register
                time.sleep(1.0)
                res = interp_res(res)
                return self.tscctl('view', res=res)
            if cmd == 'logout':
                res = self.tsc.tsc_logout()
                # Ugh!...give time for command to register
                time.sleep(1.0)
                res = interp_res(res)
                return self.tscctl('view', res=res)
            if cmd == 'obspri':
                res = self.tsc.tsc_obspri()
                # Ugh!...give time for command to register
                time.sleep(1.0)
                res = interp_res(res)
                return self.tscctl('view', res=res)
            if cmd == 'tscpri':
                res = self.tsc.tsc_tscpri()
                # Ugh!...give time for command to register
                time.sleep(1.0)
                res = interp_res(res)
                return self.tscctl('view', res=res)
            if cmd == 'statuson':
                res = self.tsc.tsc_statusOn()
                res = interp_res(res)
                return self.tscctl('view', res=res)
        except Exception, e:
            return self.tscctl('view', res=str(e))
            

        # Header string for the generated web page
        page_html = """
<html>
<head>
  <TITLE>TSC Control</title>
  %(css)s
</head>
<body>
<h2>TSC Control</h2>
<a class=btn2 href="/tscctl/view">Refresh</a> 
<p>
Logging in? <p> 
 1) Safety Lock <b>OFF</b> 2) TSC <b>Login</b>  3) <b>OBS</b> priority <p>
Logging out? <p>
 1) <b>TSC</b> priority 2) TSC <b>Logout</b> 3) Safety Lock <b>ON</b>
<p>
<table border=1 cellspacing=2 cellpadding=5>
<tr class=header>
  <th>Safety Lock</th>
  <th>TSC Login</th>
  <th>Priority</th>
  </tr>
<tr cellpadding=8 align="center">
  <td> %(safety)s
  </td>
  <td> %(login)s 
  </td>
  <td> %(priority)s 
  </td>
</tr>
<tr cellpadding=8>
  <td> 
<a class=btn2 href="/tscctl/lockon">ON</a> &nbsp;|&nbsp;
<a class=btn2 href="/tscctl/lockoff">OFF</a>
  </td>
  <td> 
<a class=btn2 href="/tscctl/login">Login</a> &nbsp;|&nbsp;
<a class=btn2 href="/tscctl/logout">Logout</a>
  </td>
  <td> 
<a class=btn2 href="/tscctl/obspri">OBS</a> &nbsp;|&nbsp;
<a class=btn2 href="/tscctl/tscpri">TSC</a>
  </td>
</tr>
</table>

<p>
<table border=1 cellspacing=2 cellpadding=5>
<tr class=header>
  <th>Status</th>
  </tr>
<tr cellpadding=8>
  <td>
<a class=btn2 href="/tscctl/statuson">ON</a> &nbsp;|&nbsp;
OFF
  </td>
</tr>
</table>

<h4>Secondary Mirror</h4>
<!-- form action="/tcsctl/get2m" method="get">
<select name="m2confname" size="10">
%(m2config)s
</select>
<input class=btn2 type="submit" value="Get" />
</form -->
<p>
<form action="/tcsctl/set2m" method="get">
<table border=1 cellspacing=2 cellpadding=5>
<tr class=header>
  <th>X</th>
  <th>Y</th>
  <th>Z</th>
  <th>tX</th>
  <th>tY</th>
  <th>&nbsp;</th>
  </tr>
<tr>
  <td>%(s_x)f</td>
  <td>%(s_y)f</td>
  <td>%(s_z)f</td>
  <td>%(s_tx)f</td>
  <td>%(s_ty)f</td>
  <td>&nbsp;</td>
</tr>
<!-- tr>
  <td><input type=text name=x size=6 value="%(x)s" /></td>
  <td><input type=text name=y size=6 value="%(y)s" /></td>
  <td><input type=text name=z size=6 value="%(z)s" /></td>
  <td><input type=text name=tx size=6 value="%(tx)s" /></td>
  <td><input type=text name=ty size=6 value="%(ty)s" /></td>
  <td><input class=btn2 type="submit" value="Set" /></td>
</td>
</tr -->
</table>
</form>

<h3>Result</h3>
Previous result was:
<pre>
%(res)s
</pre>

<a class=btn2 href="/doc/help/index.html">Help</a>

<p><hr width="30%%">
<a href="/default">Back to home</a>
</body>
</html>
"""

        # -- PAGE HEADER ---
        my_url = self._my_base_url()

        statusDict = {'GEN2.TSCLOGINS': 'NODATA',
                      'GEN2.TSCMODE': 'NODATA',
                      'TSCV.PF_OFF_X': 'NODATA',
                      'TSCV.PF_OFF_Y': 'NODATA',
                      'TSCV.PF_OFF_Z': 'NODATA',
                      'TSCV.PF_OFF_TX': 'NODATA',
                      'TSCV.PF_OFF_TY': 'NODATA', 
                      }
        try:
            res = self.status.fetch(statusDict)
        except Exception, e:
            res = {}

        statusDict.update(res)

        d = {}
        d['res'] = kwdargs.get('res', '---')
        d['css'] = css
        # get status of TSC safety lock
        try:
            res = self.tsc.safetyLockSetP()
            if res:
                d['safety'] = 'ON'
            else:
                d['safety'] = 'OFF'
        except Exception, e:
            d['safety'] = 'N/A'

        logins = statusDict.get('GEN2.TSCLOGINS', '')
        logins = logins.split(',')
        if 'OCS%' in logins:
            d['login'] = 'Gen2 Logged IN'
        else:
            d['login'] = 'Gen2 Logged OUT'
        if statusDict.get('GEN2.TSCMODE', '') == 'OBS':
            d['priority'] = 'Gen2/OBS'
        else:
            d['priority'] = 'TSC'
        
        d['s_x'] = statusDict['TSCV.PF_OFF_X']
        d['s_y'] = statusDict['TSCV.PF_OFF_Y']
        d['s_z'] = statusDict['TSCV.PF_OFF_Z']
        d['s_tx'] = statusDict['TSCV.PF_OFF_TX']
        d['s_ty'] = statusDict['TSCV.PF_OFF_TY']

        d['x'] = kwdargs.get('x', d['s_x'])
        d['y'] = kwdargs.get('y', d['s_y'])
        d['z'] = kwdargs.get('z', d['s_z'])
        d['tx'] = kwdargs.get('tx', d['s_tx'])
        d['ty'] = kwdargs.get('ty', d['s_ty'])

        d['m2config'] = '\n'.join(['<option value="%s">%s</option>' % (
            name, name) for name in self.pama.getNames()])
                     
        html = page_html % d
        return html


    def _get_dispmap(self, loc):
        try:
            return self.dispmap[loc.lower()]
        except KeyError:
            return self.dispmap['default']
        
        
    def dspctl(self, cmd, **kwdargs):
        """Display controls
        """

        def load_pass():
            try:
                passwd_file = '%s/.vnc/passwd' % os.environ['HOME']
                in_f = open(passwd_file, 'r')
                passwd = in_f.read()
                in_f.close()
                
                return ro.binary_encode(passwd)
            except IOError, e:
                self.logger.error("Cannot read password file '%s': %s" % (
                        passwd_file, str(e)))
                return None
            
        def start_host(up, up_rmdsp, dn, dn_rmdsp, passwd, viewonly):
            
            print "starting on host %s" % (up.host)
            try:
                svcname = ('g2disp-%s' % up.host.replace('.', '_'))
                handle = ro.remoteObjectProxy(svcname)

                handle.viewerOn(up.xdisp, up.geom, up_rmdsp, passwd, viewonly)
                handle.viewerOn(dn.xdisp, dn.geom, dn_rmdsp, passwd, viewonly)
            except ro.remoteObjectError, e:
                self.logger.error("Error starting viewer on remote host '%s': %s" % (
                        up.host, str(e)))

        def stop_host(up, dn):

            try:
                svcname = ('g2disp-%s' % up.host.replace('.', '_'))
                handle = ro.remoteObjectProxy(svcname)

                handle.viewerOff(up.xdisp, up.geom)
                handle.viewerOff(dn.xdisp, dn.geom)
            except ro.remoteObjectError, e:
                self.logger.error("Error stopping viewer on remote host '%s': %s" % (
                        up.host, str(e)))

        def start_loc(loc, viewonly):
            self.logger.info("Starting displays for location '%s'" % (loc))
            dsplst = g2soss.get_displays(loc)

            passwd = load_pass()

            # Get the vnc servers
            # TODO: need to allow for a variable number
            displays = {}
            for i in xrange(1, 7):
                key = 's%d' % i
                displays[key] = self.bm.get_disp(key)

            # Display map is a dict mapping the keys (ul, ll, um, lm, ur, lr)
            dispmap = self._get_dispmap(loc)
            print dispmap

            def get_serv(pos):
                try:
                    return displays[dispmap[pos]]
                except KeyError:
                    return displays.values()[0]
                
            # X display list is ordered LEFT to RIGHT, with tuples of
            # (UPPER, LOWER)
            (up, dn) = dsplst.pop(0)
            serv_up = get_serv('ul')
            serv_dn = get_serv('ll')
            start_host(up, serv_up, dn, serv_dn, passwd, viewonly)

            (up, dn) = dsplst.pop(0)
            serv_up = get_serv('um')
            serv_dn = get_serv('lm')
            start_host(up, serv_up, dn, serv_dn, passwd, viewonly)

            (up, dn) = dsplst.pop(0)
            serv_up = get_serv('ur')
            serv_dn = get_serv('lr')
            start_host(up, serv_up, dn, serv_dn, passwd, viewonly)

        def stop_loc(loc):
            self.logger.info("Stopping displays for location '%s'" % (loc))
            dsplst = g2soss.get_displays(loc)

            (up, dn) = dsplst.pop(0)
            stop_host(up, dn)
            (up, dn) = dsplst.pop(0)
            stop_host(up, dn)
            (up, dn) = dsplst.pop(0)
            stop_host(up, dn)

        def interp_res(res):
            try:
                table = { ro.OK: 'OK', ro.ERROR: 'NG' }
                return table[res]
            except KeyError:
                return res
            
        try:
            if cmd == 'start':
                viewonly = (kwdargs['mode'] != 'control')
                res = start_loc(kwdargs['loc'], viewonly)
                res = str(res)

            if cmd == 'stop':
                res = stop_loc(kwdargs['loc'])
                res = str(res)

            if cmd == 'view':
                pass

        except Exception, e:
            return self.dspctl('view', res=str(e))
            

        # Header string for the generated web page
        page_html = """
<html>
<head>
  <TITLE>Display Control</title>
  %(css)s
</head>
<body>
<h2>Display Control</h2>
<a class=btn2 href="/dspctl/view">Refresh</a> 
<p>
At the appropriate site, please login <strong>first</strong> and run the
Gen2 display control server (<tt>g2disp_gui.py</tt>).
<p>
<strong>NOTE</strong>: <em>Changing display control does <b>not</b> affect currently running operations</em>.
<p>
<table border=1 cellspacing=2 cellpadding=5>
<tr class=header>
  <th>Location</th>
  <th>Displays</th>
  </tr>
<tr>
  <td>
Summit
  </td>
  <td>
<a class=btn2 href="/dspctl/start?loc=summit&mode=control">Control</a>
<a class=btn2 href="/dspctl/start?loc=summit&mode=view">View</a>
<a class=btn2 href="/dspctl/stop?loc=summit">Close</a>
<a class=btn2 href="/dspcfg/view?loc=summit">Configure</a>
  </td>
</tr>
<tr>
  <td>
Hilo
  </td>
  <td>
<a class=btn2 href="/dspctl/start?loc=hilo&mode=control">Control</a>
<a class=btn2 href="/dspctl/start?loc=hilo&mode=view">View</a>
<a class=btn2 href="/dspctl/stop?loc=hilo">Close</a>
<a class=btn2 href="/dspcfg/view?loc=hilo">Configure</a>
  </td>
</tr>
<tr>
  <td>
Mitaka
  </td>
  <td>
<a class=btn2 href="/dspctl/start?loc=mitaka&mode=control">Control</a>
<a class=btn2 href="/dspctl/start?loc=mitaka&mode=view">View</a>
<a class=btn2 href="/dspctl/stop?loc=mitaka">Close</a>
<a class=btn2 href="/dspcfg/view?loc=mitaka">Configure</a>
  </td>
</tr>
<tr>
  <td>
OCS Room
  </td>
  <td>
<a class=btn2 href="/dspctl/start?loc=ocs&mode=control">Control</a>
<a class=btn2 href="/dspctl/start?loc=ocs&mode=view">View</a>
<a class=btn2 href="/dspctl/stop?loc=ocs">Close</a>
<a class=btn2 href="/dspcfg/view?loc=ocs">Configure</a>
  </td>
</tr>
<tr>
  <td>
Mogi
  </td>
  <td>
<a class=btn2 href="/dspctl/start?loc=mogi&mode=control">Control</a>
<a class=btn2 href="/dspctl/start?loc=mogi&mode=view">View</a>
<a class=btn2 href="/dspctl/stop?loc=mogi">Close</a>
<a class=btn2 href="/dspcfg/view?loc=mogi">Configure</a>
  </td>
</tr>
</table>

<h3>Result</h3>
Previous result was:
<pre>
%(res)s
</pre>

<a class=btn2 href="/doc/help/index.html">Help</a>

<p><hr width="30%%">
<a href="/default">Back to home</a>
</body>
</html>
"""

        # -- PAGE HEADER ---
        my_url = self._my_base_url()

        d = {}
        d['res'] = kwdargs.get('res', '---')
        d['css'] = css

        html = page_html % d
        return html


    def dspcfg(self, cmd, **kwdargs):
        """Display configuration.
        """

        def _get_dispmap_options(loc, pos, screens):
            d = self._get_dispmap(loc)
            
            res = []
            res.append('<select name="%s" size="1">' % pos)
            for screen in screens:
                if d[pos] == screen:
                    res.append('<option selected value="%s">%s</option>' % (
                        screen, screen.upper()))
                else:
                    res.append('<option value="%s">%s</option>' % (
                        screen, screen.upper()))
            res.append('</select>')
            return '\n'.join(res)
            
        try:
            if cmd == 'setmap':
                loc = kwdargs['loc'].lower()
                dmap = {}
                dmap.update(kwdargs)
                del dmap['loc']
                self.dispmap[loc] = dmap
                res = 'OK'

            if cmd == 'view':
                pass

        except Exception, e:
            return self.dspcfg('view', res=str(e))
            

        # Header string for the generated web page
        page_html = """
<html>
<head>
  <TITLE>Display Configuration</title>
  %(css)s
</head>
<body>
<h2>Display Mapping</h2>
<a class=btn2 href="/dspcfg/view?loc=%(loc)s">Refresh</a> 
<p>
Here you can set the mapping for the various screens for your location.
Typical assignments to screens:
<ul>
  <li> S6: env mon, new fits viewer
  <li> S5: VGW gui
  <li> S4: QDAS windows, old fits viewer
  <li> S3: integgui2
  <li> S2: telstat
  <li> S1: hskymon
</ul>
<p>
Here you can choose locations for the screens:
<form action="/dspcfg/setmap" method="get">
<table border=1 cellspacing=2 cellpadding=5>
<tr class=header align="center">
  <th>Location</th>
  <th>Upper Left</th>
  <th>Lower Left</th>
  <th>Upper Middle</th>
  <th>Lower Middle</th>
  <th>Upper Right</th>
  <th>Lower Right</th>
  </tr>
<tr align="center">
  <td>%(loc_c)s</td>
  <td>%(ul_v)s</td>
  <td>%(ll_v)s</td>
  <td>%(um_v)s</td>
  <td>%(lm_v)s</td>
  <td>%(ur_v)s</td>
  <td>%(lr_v)s</td>
</tr>
<tr align="center">
  <td>&nbsp;
    <input type="hidden" name="loc" value="%(loc)s">
  </td>
  <td>%(ul)s</td>
  <td>%(ll)s</td>
  <td>%(um)s</td>
  <td>%(lm)s</td>
  <td>%(ur)s</td>
  <td>%(lr)s</td>
</tr>
</table>
<br>
<input class=btn2 type="submit" value="Set" />
</form>
<p>
<strong>NOTE</strong>: <em>changing the mapping will not affect any running
applications</em>.
<p>
Reconnect your displays using the controls below after clicking "Set" to change the mapping.

<h3>Update Displays</h3>
<a class=btn2 href="/dspctl/start?loc=%(loc)s&mode=control">Control</a>
<a class=btn2 href="/dspctl/start?loc=%(loc)s&mode=view">View</a>
<a class=btn2 href="/dspctl/stop?loc=%(loc)s">Close</a>
<p>
<a href="/dspctl/view">Back to Display Control</a>
<p>
<a class=btn2 href="/doc/help/index.html">Help</a>

<p><hr width="30%%">
<a href="/default">Back to home</a>
</body>
</html>
"""

        # -- PAGE HEADER ---
        my_url = self._my_base_url()

        d = {}
        d['res'] = kwdargs.get('res', '---')
        d['css'] = css
        d['loc'] = kwdargs.get('loc', 'summit')
        d['loc_c'] = d['loc'].capitalize()

        # TODO: this can vary by location!
        screens = ['s1', 's2', 's3', 's4', 's5', 's6']
        dm = self._get_dispmap(d['loc'])
        for pos in ('ul', 'll', 'um', 'lm', 'ur', 'lr'):
            d[pos] = _get_dispmap_options(d['loc'], pos, screens)
            d['%s_v' % pos] = dm[pos].upper()
                     
        html = page_html % d
        return html


    # This function crafts a basic html wrapper 
    def page(self, s):
        page = """
<html>
<head>
</head>
<body>
Error fetching document: %s
</body>
</html>
""" % s
        return page


    def datakeys(self, cmd, **kwdargs):
        """Manage data keys. 
        """

        # Header string for the generated web page
        page_html = """
<html>
<head>
  <TITLE>Manage Data Keys</title>
  %(css)s
</head>
<body>
<h2>Manage Data Streaming</h2>
<a class=btn2 href="%(url)s/view">Refresh</a> |
<a class=btn2 href="/doc/help/index.html">Help</a>

<h3>Active data keys</h3>
<table cellpadding=5 border=1>
<tr><th class=header2>Key</th>
    <th class=header2>Type</th>
    <th class=header2>Realm</th>
    <th class=header2>Priority</th>
    <th class=header2>Enabled</th>
    <th class=header2>Update</th>
    <th class=header2>Data Sinks (clients)</th></tr>
%(keyinfo)s
</table>

<h3>Manage data keys</h3>

<table cellpadding=5 cellspacing=0 border=0>
<tr><td>
<form action=%(url)s/gen method="get">
<input class=btn2 type="submit" style="width: 135px" value="Gen Data Key">
Key: <input type="text" name="key" size=10>
</form>
</td></tr>

<tr><td>
<form action=%(url)s/load method="get">
<input class=btn2 type="submit" style="width: 135px" value="Load Data Key">
Key: <input type="text" name="key" size=10>
Type: <select name="type" size="1">
<option value="PUSH" selected>PUSH</option>
<option value="PULL">PULL</option>
<option value="COPY">COPY</option>
</select>
Realm: <select name="realm" size="1">
<option value="SUMMIT">SUMMIT</option>
<option value="BASE" selected>BASE</option>
<option value="MITAKA">MITAKA</option>
<option value="OTHER">OTHER</option>
</select> <p>
Priority: <select name="priority" size="1">
<option value="0">HIGHEST</option>
<option value="1">1</option>
<option value="2">2</option>
<option value="3">3</option>
<option value="4">4</option>
<option value="5" selected>5</option>
<option value="6">6</option>
<option value="7">7</option>
<option value="8">8</option>
<option value="9">LOWEST</option>
</select>
Enable: <select name="enable" size="1">
<option value="YES">YES</option>
<option value="NO" selected>NO</option>
</select> <p>
Pass Phrase: <input type="text" name="passphrase" size=60>
</form>
</td></tr>

<tr><td>
<form action=%(url)s/revoke method="get">
<input class=btn2 type="submit" style="width: 135px" value="Unload Data Key">
Key: <select name="key" size="1">%(keymenu)s</select>
</form>
</td></tr>

<tr><td>
<form action=%(url)s/clrsink method="get">
<input class=btn2 type="submit" style="width: 135px" value="Clear DataSinks">
Key: <select name="key" size="1">%(keymenu)s</select>
</form>
</td></tr>

<tr><td>
<form action=%(url)s/addsink method="get">
<input class=btn2 type="submit" style="width: 135px" value="Add DataSink">
Key: <select name="key" size="1">%(keymenu)s</select>
Host/IP: <input type="text" name="host" size=30>
Port: <input type="text" name="port" value="15003" size=8>
</form>
</td></tr>

<tr><td>
<form action=%(url)s/delsink method="get">
<input class=btn2 type="submit" style="width: 135px" value="Del DataSink">
Key: <select name="key" size="1">%(keymenu)s</select>
Host/IP: <input type="text" name="host" size=30>
Port: <input type="text" name="port" value="15003" size=8>
</form>
</td></tr>

</table>

<h3>Result</h3>
Previous result was:
<pre>
%(res)s
</pre>

<p><hr width="30%%">
<a href="/default">Back to home</a>
</body>
</html>
"""

        try:
            sessionName = ''
            sessionKey = ''
            
            if cmd == 'gen':
                res = self.sm.gen_datakey(sessionName, sessionKey,
                                          kwdargs['key'])
                return self.datakeys('view', **{'res': res})

            elif cmd == 'load':
                properties = {
                    'type': kwdargs['type'],
                    'realm': kwdargs['realm'],
                    'priority': kwdargs['priority'],
                    'enable': kwdargs['enable'],
                    'passphrase': urllib.unquote_plus(kwdargs['passphrase']),
                    }
                res = self.sm.load_datakey(sessionName, sessionKey,
                                           kwdargs['key'], properties)
                return self.datakeys('view', **{'res': res})

            elif cmd == 'revoke':
                res = self.sm.revoke_datakey(sessionName, sessionKey,
                                             kwdargs['key'])
                return self.datakeys('view', **{'res': res})

            elif cmd == 'addsink':
                port = int(kwdargs['port'])
                res = self.sm.add_datasink(kwdargs['host'], port,
                                           kwdargs['key'])
                return self.datakeys('view', **{'res': res})

            elif cmd == 'delsink':
                port = int(kwdargs['port'])
                res = self.sm.del_datasink(kwdargs['host'], port,
                                           kwdargs['key'])
                return self.datakeys('view', **{'res': res})

            elif cmd == 'clrsink':
                res = self.sm.clear_datasinks(kwdargs['key'])
                return self.datakeys('view', **{'res': res})

            elif cmd == 'view':
                pass

            else:
                res = "I don't understand the command '%s'" % (cmd)
                return self.datakeys('view', **{'res': res})

        except Exception, e:
            return self.datakeys('view', res=str(e))
            
        tbl_row = """
<tr><td>%(key)s</td>
    <td>%(type)s</td>
    <td>%(realm)s</td>
    <td>%(priority)s</td>
    <td>%(enable)s</td>
    <td>%(update)s</td>
    <td>%(clients)s</td></tr>
"""
        # Keys we don't want people messing with
        #restricted_keys = ['daq', 'gen2base', 'stars2']
        restricted_keys = []
        
        # -- PAGE HEADER ---
        my_url = self._my_base_url()

        keydata = self.sm.get_datasinks()
        keys = keydata.keys()
        keys.sort()
        tbldata = []
        keymenu = []
        for key in keys:
            vals = keydata[key]
            d = {}
            shortkey = key.split('-')[0]
            d['key'] = shortkey
            d['type'] = vals['properties'].get('type', 'N/A')
            d['realm'] = vals['properties'].get('realm', 'N/A')
            d['priority'] = vals['properties'].get('priority', 'N/A')
            d['enable'] = vals['properties'].get('enable', 'NO')
            d['update'] = time.strftime("%Y-%m-%d %H:%M:%S",
                                        time.localtime(vals['update_time']))
            clients = []
            for tup in vals['clients']:
                if type(tup) == str:
                    clients.append(tup)
                else:
                    clients.append('%s:%d' % (tup[0], tup[1]))
            if len(clients) == 0:
                d['clients'] = '&nbsp;'
            else:
                d['clients'] = '<br>'.join(clients)
            tbldata.append(tbl_row % d)

            if not (shortkey in restricted_keys):
                keymenu.append('<option value="%s">%s</option>' % (shortkey,
                                                                   shortkey))

        d = {}
        d['css'] = css
        d['keyinfo'] = '\n'.join(tbldata)
        d['url'] = my_url + '/datakeys'
        d['keymenu'] = '\n'.join(keymenu)
        d['res'] = str(kwdargs.get('res', '---'))
        
        html = page_html % d
        return html


    def doc(self, *args):
        """Standard web serving of documents.
        """

        # Construct the path to the requested document
        path = document_root + '/' + ('/'.join(args).lstrip('/'))
        if not os.path.exists(path):
            return self.page("Page '%s' not found" % path)

        # Open and return the file
        try:
            in_f = open(path, 'r')
            page = in_f.read()
            in_f.close()

        except IOError, e:
            page = self.page("Error loading page '%s': %s" % (
                path, str(e)))

        return page
    

    def default(self, *args, **kwdargs):
        """This method will be called if no method is specified.
        """
        # Header string for the generated web page
        page_html = """
<html>
<head>
  <TITLE>Gen2 Web Interface</TITLE>
  %(css)s
</head>
<body>
<h2>Gen2 Web Interface</h2>
What are you looking for?
<p>
<a class=btn2 href="/dspctl/view">Displays</a> |
<a class=btn2 href="/uptime">Boot Manager</a> |
<a class=btn2 href="/sessions">Sessions</a> |
<a class=btn2 href="/datakeys/view">Data Keys</a> |
<!-- a class=btn2 href="/frames">Frames</a -->
<a class=btn2 href="/tscctl/view">TSC</a> |
<a class=btn2 href="/doc/help/index.html">Help</a>
<br><br>
<a href="/doc/precheck.html">Precheck</a>
</body>
</html>
"""

        # -- PAGE HEADER ---
        my_url = self._my_base_url()

        html = page_html % {'css': css}
        return html
    
        
    def not_found(self, *args, **kwdargs):
        """This method will be called if there is a bad method specified.
        """
        # Method name is passed as the first argument
        method_name = args[0]
        raise cgisrv.NotFoundError("Method '%s' not found" % method_name)


    def error(self, *args, **kwdargs):
        """This method will be called if there is an exception raised
        calling your CGI methods.  By default it produces a readable, but
        minimal traceback dump.
        """
        tb_info = args[0]
        method_name = args[1]

        # Return debugging traceback
        (type, value, tb) = tb_info
        return "<pre>Exception %s: %s\nTraceback:\n%s</pre>" % (
            str(type), str(value), "".join(traceback.format_tb(tb)) )
    
        
def main(options, args):
    
    # Create top level logger.
    svcname = ('bm_web_%d' % (options.port))
    logger = ssdlog.make_logger(svcname, options)

    httpd = None

    # Write out our pid
    if options.pidfile:
        pidfile = options.pidfile
    else:
        pidfile = ('/tmp/bm_web_%d.pid' % (options.port))

    if options.kill:
        try:
            try:
                pid_f = open(pidfile, 'r')
                pid = int(pid_f.read().strip())
                pid_f.close()

                logger.info("Killing %d..." % (pid))
                os.kill(pid, signal.SIGKILL)
                logger.info("Killed.")

            except IOError, e:
                logger.error("Cannot read pid file (%s): %s" % (
                    pidfile, str(e)))
                sys.exit(1)

            except OSError, e:
                logger.error("Error killing pid (%d): %s" % (
                    pid, str(e)))
                sys.exit(1)
                
        finally:
            sys.exit(0)

    # Global termination flag
    ev_quit = threading.Event()
    
    def quit():
        logger.info("Shutting down BM CGI service...")
        if httpd:
            # Httpd currently uses callbacks from monitors threadpool
            pass

    def SigHandler(signum, frame):
        """Signal handler for all unexpected conditions."""
        logger.error('Received signal %d' % signum)
        quit()
        ev_quit.set()

    # Set signal handler for signals
    #signal.signal(signal.SIGINT, SigHandler)
    signal.signal(signal.SIGTERM, SigHandler)

    logger.info("Creating BootManager...")

    # Create the boot manager
    bootmgr = BM.BootManager(logger,
                             confpfx=options.confpfx)

    # Show possible configurations
    # NOTE: this won't work unless a module is loaded
    if options.showconfigs:
        print "Available configurations: %s" % str(bootmgr.getConfigs())
        sys.exit(0)

    if options.configname:
        # Try to load the specified config
        try:
            bootmgr.loadConfig(options.configname)

        except BM.BootError, e:
            print str(e)
            print "Available configurations: %s" % str(bootmgr.getConfigs())
            sys.exit(1)
        
    def serve(options):

        # Set up custom authentication function for user/passwd based
        # basic HTTP authentication, if requested
        auth_verify = None
        if options.auth_users:
            # Format of auth_users is user1:pass1,user2:pass2,...
            authDict = {}
            for userpass in options.auth_users.split(','):
                auth = userpass.split(':')
                authDict[auth[0]] = auth[1]

            # custom function to return True/False authentication by looking
            # up username and password in a dictionary
            def auth(username, password):
                return authDict.has_key(username) and (
                    authDict[username] == password)

            auth_verify = auth

        # Set up custom authentication function for host ip based
        # authentication, if requested
        host_verify = None
        if options.auth_hosts:
            # Format of auth_hosts is ip1,ip2,ip3...
            hostList = options.auth_hosts.split(',')

            # custom function to return True/False authentication by looking
            # up username and password in a dictionary
            def auth(ip, port):
                return ip in hostList

            host_verify = auth

        # Keyword args to be passed to the server class constructor
        kwdargs = { 'host': options.host, 'port': options.port,
                    'logger': logger,
                    'authVerifyFn': auth_verify, 'hostVerifyFn': host_verify }

        # If --cert was passed then user wants a secure (SSL/HTTPS) server,
        # otherwise a normal, unsecured HTTP one
        if options.cert_file:
            ServerClass = cgisrv.SecureCGIserver
            kwdargs['fpem'] = options.cert_file
            proto = 'HTTPS'
        else:
            ServerClass = cgisrv.CGIserver
            proto = 'HTTP'

        logger.info("Starting BM CGI service...")
        try:
            # Create basic object with instance data and methods to be called
            # when CGI requests come in
            cgi_obj = bm_cgi(bootmgr, options.configname, logger)

            # Create the server
            httpd = ServerClass(cgi_obj, **kwdargs)
            
            sa = httpd.socket.getsockname()
            logger.info("Serving %s on %s:%d; ^C to quit..." % (
                proto, sa[0], sa[1]))

            try:
                httpd.serveit()

            except KeyboardInterrupt:
                logger.error("Caught keyboard interrupt!")
            
        finally:
            quit()
            logger.info("Stopping %s service..." % (proto))
        
    if options.detach:
        import myproc
        
        print "Detaching from this process..."
        sys.stdout.flush()
        try:
            try:
                logfile = ('/tmp/%s.log' % svcname)
                child = myproc.myproc(serve, args=[options],
                                      pidfile=pidfile, detach=True,
                                      stdout=logfile,
                                      stderr=logfile)
                child.wait()

            except Exception, e:
                print "Error detaching process: %s" % (str(e))

            # TODO: check status of process and report error if necessary
        finally:
            pass
            #sys.exit(0)

    else:
        serve(options)
        
    

if __name__ == '__main__':

    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--auth_users", dest="auth_users",
                      help="User authorization; arg should be user:passwd")
    optprs.add_option("--auth_hosts", dest="auth_hosts",
                      help="Host authorization; arg should be list of hosts")
    optprs.add_option("--cert", dest="cert_file",
                      help="Path to key/certificate file")
    optprs.add_option("--config", dest="configname", default=None,
                      metavar="NAME",
                      help="Use configuration with name=NAME for setup")
    optprs.add_option("--confpfx", dest="confpfx", default='cfg.bm.',
                      metavar="PACKAGE",
                      help="Use python package PACKAGE for loading configs")
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--detach", dest="detach", default=False,
                      action="store_true",
                      help="Detach from terminal and run as a daemon")
    optprs.add_option("--host", dest="host",
                      default='',
                      help="Host to serve on (default: all interfaces)")
    optprs.add_option("-k", "--kill", dest="kill", default=False,
                      action="store_true",
                      help="Kill running instance of bm_web")
    optprs.add_option("-m", "--monitor", dest="monitor", default='monitor',
                      metavar="NAME",
                      help="Subscribe to feed from monitor service NAME")
    optprs.add_option("--pidfile", dest="pidfile", metavar="FILE",
                      help="Write process pid to FILE")
    optprs.add_option("--port", dest="port", type="int", default=20000,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("-s", "--showconfigs", dest="showconfigs", default=False,
                      action="store_true",
                      help="Show available configurations")
    ssdlog.addlogopts(optprs)

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

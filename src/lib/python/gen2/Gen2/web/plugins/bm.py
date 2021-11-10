#
# bm.py -- g2web plugin to make BootManager web interface
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Oct 20 14:12:12 HST 2010
#]
#
import time

# Default item to sort on
default_sort = 'level'


class bm(object):
    
    def __init__(self, logger, cfg):
        self.logger = logger
        self.cfg = cfg
        
        # Get the boot manager
        self.bm = cfg.bm

    def restart(self, svcname, sort=default_sort):
        try:
            level = float(svcname)
            self.bm.restart(level)

        except ValueError:
            self.bm.restart(svcname)
        
        return self.page(sort=sort)


    def restart_host(self, host, svcname, sort=default_sort):

        self.bm.restart_host(host, svcname)
       
        return self.page(sort=sort)


    def stop(self, svcname, sort=default_sort):
        try:
            level = float(svcname)
            self.bm.stop(level)

        except ValueError:
            self.bm.stop(svcname)
        
        return self.page(sort=sort)


    def stop_host(self, host, svcname, sort=default_sort):

        self.bm.stop_host(host, svcname)
       
        return self.page(sort=sort)


    def start(self, svcname, sort=default_sort):
        try:
            level = float(svcname)
            self.bm.start(level)

        except ValueError:
            self.bm.start(svcname)
        
        return self.page(sort=sort)


    def start_host(self, host, svcname, sort=default_sort):

        self.bm.start_host(host, svcname)
       
        return self.page(sort=sort)


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
            
        return self.page(sort=kwdargs['sort'])


    def stopall(self, sort=default_sort):
        self.bm.stopall()
        
        return self.page(sort=sort)


    def shutdown(self, sort=default_sort):
        self.bm.shutdown()
        
        return self.page(sort=sort)


    def reloadConfig(self, sort=default_sort):
        self.bm.reloadConfig()
        
        return self.page(sort=sort)


    def setup(self, sort=default_sort):
        self.bm.setup()
        
        return self.page(sort=sort)


    def uptime(self, sort=default_sort):

        return self.page(sort=sort)


    def page(self, sort=default_sort):
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
        base_url = self.cfg.my_url
        my_url = base_url + '/uptime'
        reload_url = my_url + ('?sort=%s' % sort)

        d = {'reload': reload_url,
             'title': self.cfg.configname,
             'css': self.cfg.css,
            }
        res = [page_hdr % d]
        my_url = base_url

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
                self.cfg.base_url))
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

#END

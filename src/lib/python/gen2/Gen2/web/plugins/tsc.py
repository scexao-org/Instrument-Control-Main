#
# tsc.py -- g2web plugin to make TSC web interface
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Oct 20 12:40:44 HST 2010
#]
#
import os, time

import tools.pama as pama
import remoteObjects as ro

REFRESH_INTERVAL = 30 # Web page refresh interval (seconds)
TSCV_STALE_AGE = 60 # TSCV status info is stale if age exceeds this value (seconds)

# PA/MA settings file
try:
    pamafile = '%s/cfg/PAMA.yml' % (os.environ['PYHOME'])
except KeyError:
    pamafile = None

class tsc(object):

    def __init__(self, logger, cfg):
        self.logger = logger
        self.cfg = cfg
        
        self.tsc = ro.remoteObjectProxy('TSC')
        self.status = ro.remoteObjectProxy('status')

        # For doing pa/ma settings changes
        self.pama = pama.PAMASettings(self.logger)
        if pamafile and os.path.exists(pamafile):
            self.pama.loadYAML(pamafile)


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
  <STYLE type="text/css">
  .normal {background-color: white; color: black}
  </STYLE>
  <meta HTTP-EQUIV="Refresh" CONTENT="%(refreshInterval)s;%(url)s/tscctl/view">
</head>
<body>
<h2>TSC Control</h2>
<a class=btn2 href="%(url)s/tscctl/view">Refresh</a> 
<p>Page last refreshed: %(refreshed)s</p>
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
  <td class=%(tscvStatusStyle)s> %(login)s 
  </td>
  <td class=%(tscvStatusStyle)s> %(priority)s 
  </td>
</tr>
<tr cellpadding=8>
  <td> 
<a class=btn2 href="%(url)s/tscctl/lockon">ON</a> &nbsp;|&nbsp;
<a class=btn2 href="%(url)s/tscctl/lockoff">OFF</a>
  </td>
  <td> 
<a class=btn2 href="%(url)s/tscctl/login">Login</a> &nbsp;|&nbsp;
<a class=btn2 href="%(url)s/tscctl/logout">Logout</a>
  </td>
  <td> 
<a class=btn2 href="%(url)s/tscctl/obspri">OBS</a> &nbsp;|&nbsp;
<a class=btn2 href="%(url)s/tscctl/tscpri">TSC</a>
  </td>
</tr>
</table>

<p>
<table border=1 cellspacing=2 cellpadding=5>
<tr class=header>
  <th>TSC Status</th>
  <th>Last Update</th>
  <th>State</th>
  </tr>
<tr cellpadding=8>
  <td align="center">
<a class=btn2 href="%(url)s/tscctl/statuson">START</a>
  </td>
  <td class=%(tscvStatusStyle)s>%(lastTscvUpdateTime)s</td>
  <td class=%(tscvStatusStyle)s>%(tscvStatusStateMsg)s</td>
</tr>
</table>

<p>
"TSC Login" and "Priority" values are derived from TSC Status packets.<br>
If TSC Status is stale, press START button and refresh the page to get current status.</p>

<h4>Secondary Mirror</h4>
<!-- form action="%(url)s/tcsctl/get2m" method="get">
<select name="m2confname" size="10">
%(m2config)s
</select>
<input class=btn2 type="submit" value="Get" />
</form -->
<p>
<form action="%(url)s/tcsctl/set2m" method="get">
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
        my_url = self.cfg.my_url

        statusDict = {'GEN2.TSCLOGINS': 'NODATA',
                      'GEN2.TSCMODE': 'NODATA',
                      'GEN2.STATUS.TBLTIME.TSCV': 'NODATA',
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
        d['url'] = my_url
        d['res'] = kwdargs.get('res', '---')
        d['refreshed'] = time.ctime()
        d['css'] = self.cfg.css
        # get status of TSC safety lock
        try:
            res = self.tsc.safetyLockSetP()
            if res:
                d['safety'] = 'ON'
            else:
                d['safety'] = 'OFF'
        except Exception, e:
            d['safety'] = 'N/A'

        # Set the web page refresh interval
        d['refreshInterval'] = REFRESH_INTERVAL

        # Determine if TSCV data is up-to-date or stale.
        now = time.time()  # Current time
        # GEN2.STATUS.TBLTIME.TSCV tells us the time of the last TSCV
        # update.
        tscvUpdateTime = statusDict.get('GEN2.STATUS.TBLTIME.TSCV', 0)
        # Gracefully handle the situation if TSCV status time is
        # ##NODATA## or some other non-parsable string.
        try:
            tscvUpdateTime = float(tscvUpdateTime)
        except ValueError:
            tscvUpdateTime = 0.0
        # If TSCV status is "fresh", i.e., up-to-date, set HTML style
        # tags to "normal". Otherwise, set them to "error".
        if now - tscvUpdateTime <= TSCV_STALE_AGE:
            d['tscvStatusStyle'] = 'normal'
            d['tscvStatusStateMsg'] = 'Ok'
        else:
            d['tscvStatusStyle'] = 'error'
            d['tscvStatusStateMsg'] = 'TSC Status might be stale!'
        # This is so we can write the last TSCV update time into the
        # web page.
        d['lastTscvUpdateTime'] = time.ctime(tscvUpdateTime)

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


#END

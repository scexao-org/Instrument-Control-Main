#
# dsp.py -- g2web plugin to make displays web interface
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Jan 19 10:37:43 HST 2012
#]
#
import os
import cfg.g2soss as g2soss
import remoteObjects as ro

class dsp(object):

    def __init__(self, logger, cfg):
        self.logger = logger
        self.cfg = cfg

        # Set up display maps
        self.dispmap = {}
        for loc in ['summit', 'hilo', 'mitaka', 'ocs', 'default']:
            d = {'ul': 's6', 'll': 's5',
                 'um': 's4', 'lm': 's3',
                 'ur': 's2', 'lr': 's1',
                 }
            self.dispmap[loc] = d

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
                displays[key] = self.cfg.bm.get_disp(key)

            # Display map is a dict mapping the keys (ul, ll, um, lm, ur, lr)
            dispmap = self._get_dispmap(loc)
            #print dispmap

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
<a class=btn2 href="%(url)s/dspctl/view">Refresh</a> 
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
<a class=btn2 href="%(url)s/dspctl/start?loc=summit&mode=control">Control</a>
<a class=btn2 href="%(url)s/dspctl/start?loc=summit&mode=view">View</a>
<a class=btn2 href="%(url)s/dspctl/stop?loc=summit">Close</a>
<a class=btn2 href="%(url)s/dspcfg/view?loc=summit">Configure</a>
  </td>
</tr>
<tr>
  <td>
Hilo
  </td>
  <td>
<a class=btn2 href="%(url)s/dspctl/start?loc=hilo&mode=control">Control</a>
<a class=btn2 href="%(url)s/dspctl/start?loc=hilo&mode=view">View</a>
<a class=btn2 href="%(url)s/dspctl/stop?loc=hilo">Close</a>
<a class=btn2 href="%(url)s/dspcfg/view?loc=hilo">Configure</a>
  </td>
</tr>
<tr>
  <td>
Mitaka
  </td>
  <td>
<a class=btn2 href="%(url)s/dspctl/start?loc=mitaka&mode=control">Control</a>
<a class=btn2 href="%(url)s/dspctl/start?loc=mitaka&mode=view">View</a>
<a class=btn2 href="%(url)s/dspctl/stop?loc=mitaka">Close</a>
<a class=btn2 href="%(url)s/dspcfg/view?loc=mitaka">Configure</a>
  </td>
</tr>
<tr>
  <td>
OCS Room
  </td>
  <td>
<a class=btn2 href="%(url)s/dspctl/start?loc=ocs&mode=control">Control</a>
<a class=btn2 href="%(url)s/dspctl/start?loc=ocs&mode=view">View</a>
<a class=btn2 href="%(url)s/dspctl/stop?loc=ocs">Close</a>
<a class=btn2 href="%(url)s/dspcfg/view?loc=ocs">Configure</a>
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
        my_url = self.cfg.my_url

        d = {}
        d['url'] = my_url
        d['res'] = kwdargs.get('res', '---')
        d['css'] = self.cfg.css

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
<a class=btn2 href="%(url)s/dspcfg/view?loc=%(loc)s">Refresh</a> 
<p>
Here you can set the mapping for the various screens for your location.
Typical assignments to screens:
<ul>
  <li> S6: env mon, old fits viewer
  <li> S5: guiding guis (VGW, etc)
  <li> S4: QDAS windows, new fits viewer
  <li> S3: integgui2
  <li> S2: telstat
  <li> S1: sky monitor, obs planning tools
</ul>
<p>
Here you can choose locations for the screens:
<form action="%(url)s/dspcfg/setmap" method="get">
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
<a class=btn2 href="%(url)s/dspctl/start?loc=%(loc)s&mode=control">Control</a>
<a class=btn2 href="%(url)s/dspctl/start?loc=%(loc)s&mode=view">View</a>
<a class=btn2 href="%(url)s/dspctl/stop?loc=%(loc)s">Close</a>
<p>
<a href="%(url)s/dspctl/view">Back to Display Control</a>
<p>
<a class=btn2 href="/doc/help/index.html">Help</a>

<p><hr width="30%%">
<a href="/default">Back to home</a>
</body>
</html>
"""

        # -- PAGE HEADER ---
        my_url = self.cfg.my_url

        d = {}
        d['url'] = my_url
        d['res'] = kwdargs.get('res', '---')
        d['css'] = self.cfg.css
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


#END

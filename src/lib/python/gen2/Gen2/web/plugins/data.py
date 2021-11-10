#
# data.py -- g2web plugin to make data handling web interface
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Oct 15 14:24:01 HST 2012
#]
#
import time
import urllib
import remoteObjects as ro

class data(object):

    def __init__(self, logger, cfg):
        self.logger = logger
        self.cfg = cfg
        
        self.sm = ro.remoteObjectProxy('sessions')

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
<p>Page last refreshed: %(refreshed)s</p>

<h3>Active data keys</h3>
<table cellpadding=5 border=1>
<tr><th class=header2>Key</th>
    <th class=header2>Type</th>
    <th class=header2>Realm</th>
    <th class=header2>Priority</th>
    <th class=header2>Limit</th>
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
Limit: <input type="text" name="limit" size=3>
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
                    'limit': int(kwdargs.get('limit', 2)),
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
    <td>%(limit)s</td>
    <td>%(enable)s</td>
    <td>%(update)s</td>
    <td>%(clients)s</td></tr>
"""
        # Keys we don't want people messing with
        #restricted_keys = ['daq', 'gen2base', 'stars2']
        restricted_keys = []
        
        # -- PAGE HEADER ---
        my_url = self.cfg.my_url

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
            props = vals['properties']
            d['type'] = props.get('type', 'N/A')
            d['realm'] = props.get('realm', 'N/A')
            d['priority'] = props.get('priority', 'N/A')
            d['limit'] = props.get('limit', 'N/A')
            d['enable'] = props.get('enable', 'NO')
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
        d['css'] = self.cfg.css
        d['keyinfo'] = '\n'.join(tbldata)
        d['url'] = my_url + '/datakeys'
        d['keymenu'] = '\n'.join(keymenu)
        d['res'] = str(kwdargs.get('res', '---'))
        d['refreshed'] = time.ctime()

        html = page_html % d
        return html


#END

#
# log.py -- g2web plugin to make Logs web interface
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Oct 20 12:58:25 HST 2010
#]
#
import os
import cfg.g2soss as g2soss

class log(object):

    def __init__(self, logger, cfg):
        self.logger = logger
        self.cfg = cfg
        
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
<form action=%(url)s/getlog method="get">
Last N lines: <input type="text" name="n" size=4 value="%(n)d">
Log:   <input type="text" name="logname" size=20 value="%(logname)s">
<input class=btn2 type="submit" value="Reload">
<p><hr width="30%%">
<a href="/default">Back to home</a>
</body>
</html>
"""
        # -- PAGE HEADER ---
        my_url = self.cfg.my_url
        n = int(n)
        if not '.' in logname:
            logname += '.log'

        d = {'css': cfg.css,
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


#END

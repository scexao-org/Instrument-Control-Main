#
# frames.py -- g2web plugin to make frames web interface
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Oct 20 12:55:59 HST 2010
#]
#
import time, datetime
import os, re
import urllib

import pyfits
import remoteObjects as ro

import Gen2.db.frame as framedb
from cfg.INS import INSdata as INSconfig
import cfg.g2soss as g2soss


default_sort = 'frameid'

class frame(object):

    def __init__(self, logger, cfg):
        self.logger = logger
        self.cfg = cfg
        
        self.fv = ro.remoteObjectProxy('fitsview')
        self.fv1 = ro.remoteObjectProxy('fitsview1')
        self.stars = ro.remoteObjectProxy('STARS')

        self.insconfig = INSconfig()


    def frames(self, sort=default_sort, fromdate=None, todate=None,
               noxfer=None, norecv=None, nostars=None, skip=None,
               allbox=None):
        """Produce the main Frames page. 
        """

        print "entered frames!"
        # Header string for the generated web page
        page_hdr = """
<html>
<head>
  <TITLE>Frames</title>
  %(css)s

<script language="javascript">
function checkAll() {
    for (var i=0; i<document.forms[0].elements.length; i++)
    {
        var e=document.forms[0].elements[i];
        if ((e.name != 'allbox') && (e.type == 'checkbox'))
        {
            e.checked=document.forms[0].allbox.checked;
        }
    }
}
</script>
</head>
<body>
"""

        # Row template for frames table
        tbl_row = """
        <TR class=%(class)s>
        <TD>%(check)s</TD>
        <TD>%(frameid)s</TD>
        <TD>%(time_alloc)s</TD>
        <TD>%(time_xfer)s</TD>
        <TD>%(time_saved)s</TD>
        <TD>%(time_stars)s</TD>
        </TR>
        """

        # -- PAGE HEADER ---
        base_url = self.cfg.my_url
        my_url = base_url + '/frames'
        reload_url = my_url + ('?sort=%s' % sort)

        #print "norecv=%s nostars=%s" % (norecv, nostars)
        res = [page_hdr % {'css': self.cfg.css}]

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
        self.logger.debug("from %s to %s" % (fromdate_s, todate_s))
        
        skip_cancel = (skip != None)
        norecv = (norecv != None)
        nostars = (nostars != None)

        # -- GLOBAL CONTROLS ---
        res.append("<h3>Controls</h3>")

        res.append('<a class=btn2 href="%s">Refresh</a>' % (reload_url))
        res.append("&nbsp;|&nbsp;")
        res.append('<a class=btn2 href="/doc/help/index.html">Help</a>')
        res.append("<p>Page last refreshed: %s</p>" % time.ctime())

        # -- FRAMES TABLE ---
        res.append("<h3>Frames from %s to %s</h3>" % (fromdate_s, todate_s))
        
        self.logger.debug("getting framelist")
        framelist = framedb.getFramesByDate(fromdate_t, todate_t,
                                            no_time_xfer=noxfer,
                                            no_time_saved=norecv,
                                            no_time_hilo=nostars,
                                            skip_cancel=skip_cancel)
        # TODO: allow sorting options
        framelist.reverse()
        self.logger.debug("framelist=%s" % (str(framelist)))

        res.append("<table border=1 cellspacing=2 cellpadding=5>")
        res.append('<form action=%s/framectl method="get">' % (base_url))
        res.append('<input type="hidden" name="fromdate" value="%s">' % fromdate_s)
        res.append('<input type="hidden" name="todate" value="%s">' % todate_s)

        d = {'check': '<b>Select</b>',
             'frameid': '<b>Frame ID</b>',
             'time_alloc': '<b>Time Allocated</b>',
             'time_xfer': '<b>Time Transfer</b>',
             'time_saved': '<b>Time Saved</b>',
             'time_stars': '<b>Sent to STARS</b>',
             'class': 'header',
             }
        res.append(tbl_row % d)
        
        for data in framelist:

            d = {}
            d['check'] = '<input type="checkbox" name="frames" value="%s" />' % (
                data['frameid'])

            frameid = data['frameid']
            fitspath = self._get_fitspath(frameid)
            d['frameid'] = frameid

            d['class'] = 'none'

            if isinstance(data['time_alloc'], datetime.datetime):
                d['time_alloc'] = data['time_alloc'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                d['time_alloc'] = 'N/A'
                d['class'] = 'warn'
            if isinstance(data['time_xfer'], datetime.datetime):
                d['time_xfer'] = data['time_xfer'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                d['time_xfer'] = 'N/A'
                d['class'] = 'warn'
            if isinstance(data['time_stars'], datetime.datetime):
                d['time_stars'] = data['time_stars'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                d['time_stars'] = 'N/A'
                d['class'] = 'warn'
            if isinstance(data['time_saved'], datetime.datetime):
                d['time_saved'] = data['time_saved'].strftime('%Y-%m-%d %H:%M:%S')
                d['frameid'] = '<a href="%s/getfitsheader/%s">%s</a>' % (
                    base_url, frameid, frameid)
            else:
                d['time_saved'] = 'N/A'
                if d['time_xfer'] == 'N/A':
                    d['class'] = 'warn'
                else:
                    d['class'] = 'error'

            res.append(tbl_row % d)

        res.append("</table>")
        res.append('<p><input type="checkbox" value="on" name="allbox" onclick="checkAll();"/> Select all<br />')

        res.append('<p><input class=btn2 type="submit" name="action" value="Show in FITS viewer" />')
        res.append('<input class=btn2 type="submit" name="action" value="Retry STARS transfer" />')
        res.append('<p>')
        res.append('<input class=btn2 type="submit" name="action" value="Get list" />')
        res.append('<input type="text" name="path" size=20 value="/tmp/framelist.txt" />')
        res.append('</form>')

        res.append("""<p>
<form action=%(formurl)s method="get">
Specify different date range (format YYYY-MM-DD HH:MM:SS): <p>
<input type="text" name="fromdate" size=20 value="%(fromdate)s">
<input type="text" name="todate" size=20 value="%(todate)s">
<p>
Skip cancelled <input type="checkbox" name="skip" value="true">
No transfer time <input type="checkbox" name="noxfer" value="true">
No saved time <input type="checkbox" name="norecv" value="true">
No STARS time <input type="checkbox" name="nostars" value="true">
<p>
<input class=btn2 type="submit" value="Reload">
</form>""" % ({
    'formurl': my_url,
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
        base_url = self.cfg.my_url

        frameid = frameid.upper()
        res = [page_hdr % {'css': self.cfg.css,
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


    def framectl(self, frames=[], action='none', fromdate=None, todate=None,
                 path='/tmp/framelist.txt', allbox=None):
        action = action.lower()
        # hack needed because cgisrv delivers singly selected list items as a
        # string
        if isinstance(frames, str):
            frames = [ frames ]
        self.logger.debug("action=%s frames=%s" % (
                action, str(frames)))

        try:
            if action.startswith("show"):
                for frameid in frames:
                    fitspath = self._get_fitspath(frameid)
                    self.fv.display_fitsfile(fitspath)
                    self.fv1.display_fitsfile(fitspath)

            elif action.startswith("get"):
                out_f = open(path, 'w')
                
                for frameid in frames:
                    print frameid
                    out_f.write(frameid + '\n')

                out_f.close()


        except Exception, e:
            self.logger.error(str(e))

        if not fromdate:
            return self.getfitsheader(frameid)
        else:
            return self.frames(fromdate=fromdate, todate=todate)


#END

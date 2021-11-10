# 
# Eric Jeschke (eric@naoj.org)
#

import threading

import remoteObjects as ro
import remoteObjects.Monitor as Monitor
import Bunch

# Headers we show
headers = [ 'DATE-OBS', 'UT-STR', 'EXPTIME', 'OBS-MOD',
            'OBJECT', 'FILTERS', 'MEMO' ]


class IntegGUINotify(object):

    def __init__(self, gui, fitsdir):
        self.gui = gui
        self.fitsdir = fitsdir
        # Dict used to flag processed files so they are not repeated
        self.framecache = {}
        self.framelist = []
        self.needsort = False
        self.lock = threading.RLock()

    def update_framelist(self):
        with self.lock:
            return self.gui.update_frames(self.framelist)

    def output_line(self, frameinfo):
        print "output line: %s" % str(frameinfo)
        self.gui.update_frame(frameinfo)

    def clear(self):
        with self.lock:
            self.framecache = {}
            self.framelist = []
            self.update_framelist()
        
    def _getframe(self, frameid, **kwdargs):
        with self.lock:
            if self.framecache.has_key(frameid):
                d = self.framecache[frameid]
                d.update(kwdargs)
                return d

            # Create a new entry
            dct = dict.fromkeys(headers, '')
            dct['frameid'] = frameid
            dct['status'] = 'A'
            
            d = Bunch.Bunch(dct)
            d.update(kwdargs)

            self.framecache[frameid] = d
            try:
                lastid = self.framelist[-1]
                if frameid < lastid:
                    self.needsort = True
            except IndexError:
                # First frame
                pass
            self.framelist.append(d)

            return d


    def frame_allocated(self, frameid):
        """Called when _frameid_ is allocated.
        """
        with self.lock:
            # Create a new entry
            d = self._getframe(frameid)

            self.output_line(d)


    def transfer_started(self, frameid):
        """Called when the _frameid_ transfer from the OBCP has been
        initiated.
        """
        with self.lock:
            d = self._getframe(frameid)
            if d.status == 'A':
                d.status = 'X'

            self.output_line(d)


    def transfer_done(self, frameid, status):
        """Called when the _frameid_ transfer from the OBCP has
        finished.  status==0 indicates success, error otherwise.
        """
        with self.lock:
            d = self._getframe(frameid)
            if d.status in ('X', 'A'):
                if status == 0:
                    d.status = 'R'
                else:
                    d.status = 'E'

            self.output_line(d)


    def fits_info(self, frameid, frameinfo):
        """Called when there is some information about the frame.
        """
        with self.lock:
            d = self._getframe(frameid, **frameinfo)

            self.output_line(d)
            return ro.OK


    def in_stars(self, frameid, status):
        """Called when the _frameid_ is finished a transaction with STARS."""

        with self.lock:
            d = self._getframe(frameid)
            d.status = 'R' + status[0]

            self.output_line(d)
            return ro.OK

    
    def frameSvc_hdlr(self, frameid, vals):
        """Called with information provided by the frame service."""

        print "frame handler"
        if vals.has_key('time_alloc'):
            self.frame_allocated(frameid)


    def INSint_hdlr(self, frameid, vals):
        """Called with information provided by the instrument interface."""
        
        if Monitor.has_keys(vals, ['done', 'time_done', 'status',
                                   'filepath']):
            self.transfer_done(frameid, vals['status'])

        elif vals.has_key('time_start'):
            self.transfer_started(frameid)


    def Archiver_hdlr(self, frameid, vals):
        """Called with information provided by the Archiver."""
        
        # TODO: check vals['PROP-ID'] against propid for this
        # integgui before proceeding
        self.fits_info(frameid, vals)


    def STARSint_hdlr(self, frameid, vals):
        """Called with information provided by the STARS interface."""

        # TODO: integgui shouldn't have to understand this level of
        # the stars protocol
        if Monitor.has_keys(vals, ['done', 'time_done']):
            if Monitor.has_keys(vals, ['errorclass', 'msg']):
                # --> there was an error in the STARS interface
                self.in_stars(frameid, 'E')
            elif (Monitor.has_keys(vals, ['end_result', 'end_status1',
                                       'end_status2']) and
                (vals['end_result'] == 0) and
                (vals['end_status1'] == 0) and
                (vals['end_status2'] == 0)):
                # --> STARS may have the file
                self.in_stars(frameid, 'T')


# END

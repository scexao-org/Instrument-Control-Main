# 
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Mar 13 15:31:34 HST 2013
#]

import sys, os
import threading
import traceback
# To prevent a nasty issue with Gtk
import warnings
warnings.filterwarnings("ignore")
import Queue
import random

import Bunch
import SOSS.GuiderInt.guiderfitsheader as gfh

import remoteObjects as ro


class AgDisplay(object):

    def __init__(self, agkey, aginfo, logger, ev_quit=None):

        super(AgDisplay, self).__init__()

        self.aginfo = aginfo
        self.name = aginfo.name
        self.agkey = agkey
        self.width = aginfo.maxwd
        self.height = aginfo.maxht
        self.logger = logger
        if not ev_quit:
            ev_quit = threading.Event()
        self.ev_quit = ev_quit

        self.lock = threading.RLock()

        
    def start(self):
        pass

    def stop(self):
        pass
        
    def start_skycat(self):
        pass
        
    def stop_skycat(self):
        pass
            


    def update_image(self, image):
        self.logger.debug("Updating gui image...%s" % image)
        data = image.get_data()

        objname = image.get_keyword('OBJECT', 'Noname')
        try:
            viewer = self.aginfo.viewer
            deriver = image.get('deriver', None)
            if deriver:
                deriver.deriveAll(image)

            height, width = data.shape
            data = data.byteswap(True)
            buf = ro.binary_encode(data.tostring())
            header = image.get_header()
            self.logger.debug("Header is %s" % (str(header)))

            metadata = {}
            guiding = image.get('hasregion', False)
            metadata['guiding'] = guiding
            if guiding:
                metadata['region'] = image.get('region')

            aghdr = {}
            aghdr.update(image.get('agheader'))
            metadata['agheader'] = aghdr
            metadata['agtime'] = image.get('agtime')
            
            name = self.agkey
            ## viewer.display_fitsbuf(name, name, buf, width, height,
            ##                        0, header, metadata)
            viewer.callGlobalPlugin("foo", "VGW", 'display_fitsbuf',
                                    (name, name, buf, width, height,
                                     0, header, metadata), {})
        except Exception, e:
            self.logger.error("Error updating fits image (%s): %s" % (
                self.agkey, str(e)))


    def clear_rect(self):
        self.logger.debug("Clearing gui rectangle...")
        #self.fitsimage.deleteAllObjects()
        
    def draw_rect(self, x1, y1, x2, y2):
        # account for difference between FITS coords and data coords
        x1, y1, x2, y2 = x1-1, y1-1, x2-1, y2-1
        
        self.clear_rect()
        
        self.logger.debug("Drawing gui rectangle...")
                           
        # determine best coordinates for text label
        x = max(x1, x2)
        y = max(y1, y2)

        # draw label 
        ## self.fitsimage.add(CompoundObject(Rectangle(x1, y1, x2, y2,
        ##                                             color='green'),
        ##                                   Text(x, y, "Calc Region",
        ##                                        color='gold')))
        
    def raise_win(self):
        pass

    def update_rates(self, avg, peak, delta):
        print "rates: ", avg, peak, delta
        
    def update_quality(self, quality):
        print "update quality"

    # --- CALLBACKS ---


class AgMainWindow(object):

    def __init__(self, controller, logger, ev_quit, viewerName):
        self.controller = controller
        self.logger = logger
        self.ev_quit = ev_quit
        self.viewerName = viewerName
        self.gui_queue = Queue.Queue()

        self.displays = Bunch.Bunch()

        # helper object to make our FITS headers from definitions
        self.fitshelper = gfh.GuiderFitsHeaderMaker(self.logger)

        self.procs = {}

        self.reset_viewer()

        for key in self.controller.getnames():
            aginfo = self.controller.getinfo(key)

            self.start(key, aginfo)


    def _mkstart(self, key, aginfo):
        return lambda w: self.startstop(w, key, aginfo)

    def startstop(self, w, key, aginfo):
        if w.get_active():
            self.start(key, aginfo)
        else:
            self.stop(key, aginfo)

    def reset_viewer(self):
        self.viewer = ro.remoteObjectProxy(self.viewerName)

    def start(self, key, aginfo):
        agdisp = AgDisplay(key, aginfo, self.logger)
        self.displays[key] = agdisp
        agdisp.start()
        aginfo.agmain = self
        #aginfo.fv = None
        aginfo.viewer = self.viewer
        aginfo.agdisp = agdisp

    def stop(self, key, aginfo):
        aginfo.agdisp = None
        agdisp = self.displays[key]
        try:
            agdisp.stop()
        except Exception, e:
            self.logger.warn("Error stopping skycat comm: %s" % (str(e)))

    def stopall(self):
        for key in self.displays.keys():
            aginfo = self.controller.getinfo(key)
            self.stop(key, aginfo)
            
    # --- CALLBACKS ---

    def set_delta(self, rng, agkey, which):
        val = rng.get_value()
        self.logger.debug("Setting limit to %.2f" % val)
        if which == 1:
            self.controller.set_delta1(agkey, val)
        else:
            self.controller.set_delta2(agkey, val)
        
    def reset_counts(self, w, agkey, aginfo):
        self.controller.reset_perf(agkey)
        aginfo.w_rateavg2.set_markup('<span></span>')
        aginfo.w_ratepeak2.set_markup('<span></span>')
        
    def delete_event(self, widget, event, data=None):
        self.quit(widget)
        return False

    def quit(self, widget):
        """Quit the application.
        """
        self.stopall()
        
        self.ev_quit.set()
        return False

    def mainloop(self):
        self.ev_quit.wait()

def MainGUI(options, args, ev_quit, logger=None):
    # Placeholder
    print "Press ^C to terminate instrument..."
    while not ev_quit.isSet():
        ev_quit.wait(1.0)
            

#END

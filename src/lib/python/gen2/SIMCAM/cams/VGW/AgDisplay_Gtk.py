# 
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Apr 15 17:04:04 HST 2013
#]

# stdlib imports
import numpy
import threading

# GUI imports
import gtk

import Bunch
import remoteObjects as ro

import sys, os

import ginga.gtkw.FitsImageCanvasGtk as FitsImage
from ginga.gtkw.FitsImageCanvasTypesGtk import *


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
        data = image.data

        objname = image.get_keyword('OBJECT', 'Noname')
        try:
            fv = self.aginfo.fv
            deriver = image.get('deriver', None)
            if deriver:
                deriver.deriveAll(image)

            fv.gui_do(fv.update_image, self.agkey, image, chname=self.agkey)
            ## self.fitsimage.set_image(image)

            #self.w.num.set_text(objname)

            # If we are guiding, then set our calculation region and draw
            # a rectangle on the image
            guiding = image.get('hasregion', False)
            if guiding:
                x1, y1, x2, y2 = image.get_region()
                self.draw_rect(x1, y1, x2, y2)
            else:
                self.clear_rect()

            quality = image.get('quality', None)
            if quality:
                self.update_quality(quality)
                
        except Exception, e:
            self.logger.error("Error updating fits image (%s): %s" % (
                self.agkey, str(e)))


    ## def update_image(self, image):
    ##     self.logger.debug("Updating gui image...%s" % image)
    ##     data = image.data

    ##     objname = image.get_keyword('OBJECT', 'Noname')
    ##     try:
    ##         viewer = self.aginfo.viewer
    ##         deriver = image.get('deriver', None)
    ##         if deriver:
    ##             deriver.deriveAll(image)

    ##         height, width = data.shape
    ##         data = data.byteswap(True)
    ##         buf = ro.binary_encode(data.tostring())
    ##         header = image.get_header()

    ##         name = self.agkey
    ##         viewer.display_fitsbuf(name, name, buf, width, height,
    ##                                0, header)

    ##         ## # If we are guiding, then set our calculation region and draw
    ##         ## # a rectangle on the image
    ##         ## guiding = image.get('hasregion', False)
    ##         ## if guiding:
    ##         ##     x1, y1, x2, y2 = image.get_region()
    ##         ##     self.draw_rect(x1, y1, x2, y2)
    ##         ## else:
    ##         ##     self.clear_rect()

    ##         ## quality = image.get('quality', None)
    ##         ## if quality:
    ##         ##     self.update_quality(quality)
                
    ##     except Exception, e:
    ##         self.logger.error("Error updating fits image (%s): %s" % (
    ##             self.agkey, str(e)))


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
        ## gui = self.aginfo.agmain
        ## if avg > delta:
        ##     col_s = ' background="red"'
        ## else:
        ##     col_s = ''
        ## gui.gui_do(self.aginfo.w_rateavg2.set_markup, '<span%s>%.3f</span>' % (
        ##     col_s, avg))

        ## if peak > delta:
        ##     col_s = ' background="yellow"'
        ## else:
        ##     col_s = ''
        ## gui.gui_do(self.aginfo.w_ratepeak2.set_markup, '<span%s>%.3f</span>' % (
        ##     col_s, peak))
        pass
        
    def update_quality(self, quality):
        def __update():
            self.logger.debug("Setting quality info!")
            self.aginfo.w_fwhm.set_text('%.3f' % quality.fwhm)
            self.aginfo.w_starsize.set_text('%.3f' % quality.starsize)
            self.aginfo.w_skylvl.set_text('%.3f' % quality.skylevel)
            self.aginfo.w_brightness.set_text('%.3f' % quality.brightness)
            self.aginfo.w_calctime.set_text('%.3f' % quality.calctime)
            
        gui = self.aginfo.agmain
        ## if quality != None:
        ##     gui.gui_do(__update)
        ## else:
        ##     pass
            # TODO: show some error condition visually

    # --- CALLBACKS ---

    def delete_event(self, widget, event, data=None):
        self.win.destroy()
        return False

    def quit(self, widget):
        self.win.destroy()
        return False



#END

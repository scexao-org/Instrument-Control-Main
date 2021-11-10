# 
# Eric Jeschke (eric@naoj.org)
#

import time
import pygtk
pygtk.require('2.0')
import gtk, gobject, cairo

import common
import Page

# Create a GTK+ widget on which we will draw using Cairo
class CairoDrawable(gtk.DrawingArea):

    # Draw in response to an expose-event
    __gsignals__ = { "expose-event": "override" }

    def __init__(self, drawfn):
        self.draw = drawfn
        super(gtk.DrawingArea, self).__init__()

    # Handle the expose-event by drawing
    def do_expose_event(self, event):

        # Create the cairo context
        cr = self.window.cairo_create()

        # Restrict Cairo to the exposed area; avoid extra work
        cr.rectangle(event.area.x, event.area.y,
                event.area.width, event.area.height)
        cr.clip()

        self.draw(cr, *self.window.get_size())


class ObsInfoPage(Page.ButtonPage):

    def __init__(self, frame, name, title):

        super(ObsInfoPage, self).__init__(frame, name, title)

        # where we store updates
        self.obsdict = {}
        for key in ('OBSINFO1', 'OBSINFO2', 'OBSINFO3', 'OBSINFO4', 'OBSINFO5',
                    'TIMER', 'PROP-ID'):
            self.obsdict[key] = ''

        # rgb triplets we use
        self.black = (0.0, 0.0, 0.0)
        self.blue  = (0.0, 0.0, 1.0)
        self.green = (0.0, 0.5, 0.0)
        self.white = (1.0, 1.0, 1.0)
        self.orange = (0.824, 0.412, 0.1176)

        self.timertask = None

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_border_width(2)

        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,
                                   gtk.POLICY_AUTOMATIC)
        # create cairo drawing area
        self.area = CairoDrawable(self.draw)
        self.area.set_size_request(400, 300)
        self.maxwd = 1200
        self.maxht = 1000

        scrolled_window.add_with_viewport(self.area)
        scrolled_window.show()
        self.area.show()

        frame.pack_start(scrolled_window, fill=True, expand=True)

        menu = self.add_pulldownmenu("Page")

        # Add items to the menu
        item = gtk.MenuItem(label="Cancel Timer")
        menu.append(item)
        item.connect_object ("activate", lambda w: self.cancel_timer(),
                             "menu.Cancel_Timer")
        item.show()

        #self.add_close()
        item = gtk.MenuItem(label="Close")
        # currently disabled
        item.set_sensitive(False)
        menu.append(item)
        item.connect_object ("activate", lambda w: self.close(),
                             "menu.Close")
        item.show()

    def _draw_blank(self, cr, width, height):
        # Fill the background with white
        cr.set_source_rgb(*self.white)
        cr.rectangle(0, 0, width, height)
        cr.fill()

    def _draw_text(self, cr, x, y, text):
        cr.move_to(x, y)
        cr.show_text(text)

    def draw(self, cr, width, height):
        self._draw_blank(cr, width, height)

        cr.select_font_face("fixed",
                cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_source_rgb(*self.black)
        cr.set_font_size(18.0)
        self._draw_text(cr, 300, 20, self.obsdict['PROP-ID'])

        cr.set_source_rgb(*self.orange)
        cr.set_font_size(150.0)
        self._draw_text(cr, 550, 270, self.obsdict['TIMER'])

        cr.set_source_rgb(*self.blue)
        cr.select_font_face("Georgia",
                cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(48.0)
        self._draw_text(cr, 10, 75, self.obsdict['OBSINFO1'])

        cr.set_source_rgb(*self.green)
        cr.set_font_size(42.0)
        self._draw_text(cr, 250, 120, self.obsdict['OBSINFO2'])

        cr.set_source_rgb(*self.black)
        cr.set_font_size(24.0)
        self._draw_text(cr,  10, 160, self.obsdict['OBSINFO3'])
        self._draw_text(cr, 250, 190, self.obsdict['OBSINFO4'])
        self._draw_text(cr, 500, 160, self.obsdict['OBSINFO5'])

    def redraw(self):
        cr = self.area.window.cairo_create()
        cr.rectangle(0, 0, self.maxwd, self.maxht)
        cr.clip()

        return self.draw(cr, self.maxwd, self.maxht)

    def update_obsinfo(self, obsdict):

        self.logger.debug("obsinfo update: %s" % str(obsdict))
        self.obsdict.update(obsdict)

        if obsdict.has_key('TIMER_SEC'):
            self.set_timer(obsdict['TIMER_SEC'])

        self.redraw()

    def cancel_timer(self):
        if self.timertask:
            gobject.source_remove(self.timertask)
        self.timertask = None
        self.obsdict['TIMER'] = ''
        self.redraw()
        # TODO: play sound?

    def set_timer(self, val):
        self.logger.debug("val = %s" % str(val))
        self.cancel_timer()
        val = float(val)
        if val <= 0:
            return
        self.timer_val = time.time() + val
        self.logger.debug("timer_val = %d" % self.timer_val)
        self.timer_interval()


    def timer_interval(self):
        diff = self.timer_val - time.time()
        diff = max(0, int(diff))
        self.logger.debug("timer: %d sec" % diff)
        self.obsdict['TIMER'] = str(diff).rjust(5)
        self.redraw()
        if diff > 0:
            self.timertask = gobject.timeout_add(1000, self.timer_interval)
        else:
            # TODO: play sound?
            self.timertask = None
            self.obsdict['TIMER'] = ''
            self.redraw()
        

#END

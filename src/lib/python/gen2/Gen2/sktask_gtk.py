#! /usr/bin/env python
#
# sktask_gtk.py -- Skeleton File Task Viewer for Gen2
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Jul  8 11:14:38 HST 2010
#]

# remove once we're certified on python 2.6
from __future__ import with_statement

import sys, os
import re, time
import threading, Queue
import logging
import pygtk
pygtk.require('2.0')
import gtk, gobject

import remoteObjects as ro
import remoteObjects.Monitor as Monitor
import Bunch
import cfg.g2soss
import ssdlog


class TagError(Exception):
    pass

class skDisp(object):
    def __init__(self, logger, ev_quit, **kwdargs):

        self.logger = logger
        self.ev_quit = ev_quit
        self.__dict__.update(kwdargs)
        self.lock = threading.RLock()

        # size (in lines) we will let log buffer grow to before
        # trimming
        self.logsize = 5000

        # Number of pages of command history we want to keep around
        self.pagelimit = 50

        # Create top-level window
        self.root = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.root.set_title("Skeleton Task Viewer")
        self.root.connect("delete_event", self.delete_event)
        self.root.set_border_width(2)

        # create main frame
        self.mainfr = gtk.VBox(spacing=2)
        self.root.add(self.mainfr)
        self.mainfr.show()

        self.w = Bunch.Bunch()
        self.w.root = self.root
        
        menubar = gtk.MenuBar()
        self.mainfr.pack_start(menubar, expand=False)

        # create a File pulldown menu, and add it to the menu bar
        filemenu = gtk.Menu()
        file_item = gtk.MenuItem(label="File")
        menubar.append(file_item)
        file_item.show()
        file_item.set_submenu(filemenu)
        
        showlog = gtk.MenuItem(label="Show Log")
        filemenu.append(showlog)
        showlog.connect_object ("activate", self.showlog, "file.showlog")
        showlog.show()
        sep = gtk.SeparatorMenuItem()
        filemenu.append(sep)
        sep.show()
        quit_item = gtk.MenuItem(label="Exit")
        filemenu.append(quit_item)
        quit_item.connect_object ("activate", self.quit, "file.exit")
        quit_item.show()

        # create an Option pulldown menu, and add it to the menu bar
        optionmenu = gtk.Menu()
        option_item = gtk.MenuItem(label="Option")
        menubar.append(option_item)
        option_item.show()
        option_item.set_submenu(optionmenu)

        # Option variables
        self.save_decode_result = False
        self.show_times = False
        self.track_elapsed = False
        self.audible_errors = True

        w = gtk.CheckMenuItem("Save Decode Result")
        w.set_active(False)
        optionmenu.append(w)
        w.connect("activate", lambda w: self.toggle_var(w, 'save_decode_result'))
        w = gtk.CheckMenuItem("Show Times")
        w.set_active(False)
        optionmenu.append(w)
        w.connect("activate", lambda w: self.toggle_var(w, 'show_times'))
        w = gtk.CheckMenuItem("Track Elapsed")
        w.set_active(False)
        optionmenu.append(w)
        w.connect("activate", lambda w: self.toggle_var(w, 'track_elapsed'))
        w = gtk.CheckMenuItem("Audible Errors")
        w.set_active(True)
        optionmenu.append(w)
        w.connect("activate", lambda w: self.toggle_var(w, 'audible_errors'))

        menubar.show()

        self.w.nb = gtk.Notebook()
        self.w.nb.set_tab_pos(gtk.POS_TOP)
        self.w.nb.set_scrollable(True)
        self.w.nb.set_show_tabs(True)
        self.w.nb.set_show_border(True)
        self.w.nb.set_size_request(1000, 700)
        self.mainfr.pack_start(self.w.nb, expand=True, fill=True)
        self.w.nb.show()
        
        # bottom buttons
        table = gtk.Table(rows=1, columns=3, homogeneous=True)
        btnbox = gtk.HBox()
        table.attach(btnbox, 1, 2, 0, 1, xoptions=gtk.EXPAND|gtk.FILL)
        #self.mainfr.pack_end(btnbox, expand=False)
        self.mainfr.pack_end(table, expand=False)
        btnbox.show()
        table.show()
        
        self.w.quit = gtk.Button("Quit")
               # Let's append a bunch of pages to the notebook
        self.w.quit.connect("clicked", self.quit)
        btnbox.pack_end(self.w.quit, expand=True)
        self.w.quit.show()

        self.track = {}
        self.pages = {}
        self.pagelist = []

        self.create_logwindow()
        
        #self.root.show()
        self.root.show_all()

        
    def create_logwindow(self):
        # pop-up log file
        self.w.log = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.w.log.set_title("Application Log")
        self.w.log.set_destroy_with_parent(True)
        self.w.log.connect("delete_event",
                           lambda w, e: self.closelog(w))
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_size_request(700, 400)
        scrolled_window.set_border_width(2)
        
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,
                                   gtk.POLICY_AUTOMATIC)
        
        tw = gtk.TextView(buffer=None)
        scrolled_window.add_with_viewport(tw)
        tw.show()
        scrolled_window.show()

        tw.set_editable(False)
        tw.set_wrap_mode(gtk.WRAP_NONE)
        tw.set_left_margin(4)
        tw.set_right_margin(4)
        self.w.logtw = tw

        self.logbuf = tw.get_buffer()
        self.queue = Queue.Queue()
        guiHdlr = ssdlog.QueueHandler(self.queue)
        fmt = logging.Formatter(ssdlog.STD_FORMAT)
        guiHdlr.setFormatter(fmt)
        guiHdlr.setLevel(logging.DEBUG)
        self.logger.addHandler(guiHdlr)

        self.w.log.add(scrolled_window)
        

    def toggle_var(self, widget, key):
        if widget.active: 
            self.__dict__[key] = True
        else:
            self.__dict__[key] = False

    def setPos(self, geom):
        # TODO: currently does not seem to be honoring size request
        match = re.match(r'^(?P<size>\d+x\d+)?(?P<pos>[\-+]\d+[\-+]\d+)?$',
                         geom)
        if not match:
            return
        
        size = match.group('size')
        pos = match.group('pos')

        if size:
            match = re.match(r'^(\d+)x(\d+)$', size)
            if match:
                width, height = map(int, match.groups())
                self.root.set_default_size(width, height)

        # TODO: placement
        if pos:
            pass

        #self.root.set_gravity(gtk.gdk.GRAVITY_NORTH_WEST)
        ##width, height = window.get_size()
        ##window.move(gtk.gdk.screen_width() - width, gtk.gdk.screen_height() - height)
        # self.root.move(x, y)

    def closelog(self, w):
        # close log window
        self.w.log.hide()
        return True
        
    def showlog(self, w):
        # open log window
         self.w.log.show()

    def logupdate(self):
        try:
            while True:
                msgstr = self.queue.get(block=False)

                loc = self.logbuf.get_end_iter()
                self.logbuf.insert(loc, msgstr + '\n')

                # Remove some old log lines if necessary
                excess_lines = loc.get_line() - self.logsize
                if excess_lines > 0:
                    bitr1 = self.logbuf.get_start_iter()
                    bitr2 = bitr1.copy()
                    bitr2.set_line(excess_lines)
                    self.logbuf.delete(bitr1, bitr2)

                loc = self.logbuf.get_end_iter()
                self.w.logtw.scroll_to_iter(loc, 0.1)

        except Queue.Empty:
            gobject.timeout_add(1000, self.logupdate)

        #print "Returning..."

    def insert_ast(self, tw, text):

        buf = tw.get_buffer()
        all_tags = set([])

        def insert(text, tags):

            loc = buf.get_end_iter()
            #linenum = loc.get_line()
            try:
                foo = text.index("<div ")

            except ValueError:
                buf.insert_with_tags_by_name(loc, text, *tags)
                return

            match = re.match(r'^\<div\sclass=([^\>]+)\>', text[foo:],
                             re.MULTILINE | re.DOTALL)
            if not match:
                buf.insert_with_tags_by_name(loc, 'ERROR 1: %s' % text, *tags)
                return

            num = int(match.group(1))
            regex = r'^(.*)\<div\sclass=%d\>(.+)\</div\sclass=%d\>(.*)$' % (
                num, num)
            #print regex
            match = re.match(regex, text, re.MULTILINE | re.DOTALL)
            if not match:
                buf.insert_with_tags_by_name(loc, 'ERROR 2: %s' % text, *tags)
                return

            buf.insert_with_tags_by_name(loc, match.group(1), *tags)

            serial_num = '%d' % num
            buf.create_tag(serial_num, foreground="black")
            newtags = [serial_num]
            all_tags.add(serial_num)
            newtags.extend(tags)
            insert(match.group(2), newtags)

            insert(match.group(3), tags)

        # Create tags that will be used
        buf.create_tag('code', foreground="black")
        
        insert(text, ['code'])
        #tw.tag_raise('code')
        #print "all tags=%s" % str(all_tags)

    def astIdtoTitle(self, ast_id):
        page = self.pages[ast_id]
        return page.title
        
    def delpage(self, ast_id):
        with self.lock:
            i = self.pagelist.index(ast_id)
            self.w.nb.remove_page(i)

            del self.pages[ast_id]
            self.pagelist.remove(ast_id)

    def addpage(self, ast_id, title, text):

        with self.lock:
            # Make room for new pages
            while len(self.pagelist) >= self.pagelimit:
                oldast_id = self.pagelist[0]
                self.delpage(oldast_id)
                
            scrolled_window = gtk.ScrolledWindow()
            scrolled_window.set_border_width(2)

            scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,
                                       gtk.POLICY_AUTOMATIC)

            tw = gtk.TextView(buffer=None)
            scrolled_window.add_with_viewport(tw)
            tw.show()
            scrolled_window.show()

            tw.set_editable(False)
            tw.set_wrap_mode(gtk.WRAP_NONE)
            tw.set_left_margin(4)
            tw.set_right_margin(4)
            #tw.set_pixels_above_lines(2)
            #tw.set_pixels_below_lines(2)

            label = gtk.Label(title)
            label.show()

            self.w.nb.append_page(scrolled_window, label)

            self.insert_ast(tw, text)

            txtbuf = tw.get_buffer()
            tagtbl = txtbuf.get_tag_table()
            try:
                page = self.pages[ast_id]
                page.tw = tw
                page.buf = txtbuf
                page.tagtbl = tagtbl
                page.title = title
            except KeyError:
                self.pages[ast_id] = Bunch.Bunch(tw=tw, title=title,
                                                 buf=txtbuf, tagtbl=tagtbl)

            self.pagelist.append(ast_id)

            self.setpage(ast_id)

    def setpage(self, name):
        # Because %$%(*)&^! gtk notebook widget doesn't associate names
        # with pages
        i = self.pagelist.index(name)
        self.w.nb.set_current_page(i)

        
    def delete_event(self, widget, event, data=None):
        self.ev_quit.set()
        gtk.main_quit()
        return False

    # callback to quit the program
    def quit(self, widget):
        self.ev_quit.set()
        gtk.main_quit()
        return False


    def change_text(self, page, tagname, **kwdargs):
        tagname = str(tagname)
        tag = page.tagtbl.lookup(tagname)
        if not tag:
            raise TagError("Tag not found: '%s'" % tagname)

        for key, val in kwdargs.items():
            tag.set_property(key,val)
            
        #page.tw.tag_raise(ast_num)
        # Scroll the view to this area
        start, end = self.get_region(page.buf, tagname)
        page.tw.scroll_to_iter(start, 0.1)


    def get_region(self, txtbuf, tagname):
        """Returns a (start, end) pair of Gtk text buffer iterators
        associated with this tag.
        """
        # Painfully inefficient and error-prone way to locate a tagged
        # region.  Seems gtk text buffers have tags, but no good way to
        # manipulate text associated with them efficiently.

        # Get the tag table associated with this text buffer
        tagtbl = txtbuf.get_tag_table()
        # Look up the tag
        tag = tagtbl.lookup(tagname)
        
        # Get text iters at beginning and end of buffer
        start, end = txtbuf.get_bounds()

        # Now search forward from beginning for first location of this
        # tag, and backwards from the end
        result = start.forward_to_tag_toggle(tag)
        if not result:
            raise TagError("Tag not found: '%s'" % tagname)
        result = end.backward_to_tag_toggle(tag)
        if not result:
            raise TagError("Tag not found: '%s'" % tagname)

        return (start, end)


    def replace_text(self, page, tagname, textstr):
        tagname = str(tagname)
        txtbuf = page.buf
        start, end = self.get_region(txtbuf, tagname)
        txtbuf.delete(start, end)
        txtbuf.insert_with_tags_by_name(start, textstr, tagname)

        # Scroll the view to this area
        page.tw.scroll_to_iter(start, 0.1)


    def append_error(self, page, tagname, textstr):
        tagname = str(tagname)
        txtbuf = page.buf
        start, end = self.get_region(txtbuf, tagname)
        txtbuf.insert_with_tags_by_name(end, textstr, tagname)

        self.change_text(page, tagname,
                         foreground="red", background="lightyellow")


    def update_time(self, page, tagname, vals, time_s):

        if not self.show_times:
            return

        tagname = str(tagname)
        txtbuf = page.buf
        start, end = self.get_region(txtbuf, tagname)

        if vals.has_key('time_added'):
            length = vals['time_added']
            end = start.copy()
            end.forward_chars(length)
            txtbuf.delete(start, end)
            
        vals['time_added'] = len(time_s)
        txtbuf.insert_with_tags_by_name(start, time_s, tagname)
        

    def audible_warn(self, cmd_str, vals):
        """Called when we get a failed command and should/could issue an audible
        error.  cmd_str, if not None, is the device dependent command that caused
        the error.
        """
        self.logger.debug("Audible warning: %s" % cmd_str)
        if not cmd_str:
            return

        if not self.audible_errors:
            return

        cmd_str = cmd_str.lower().strip()
        match = re.match(r'^exec\s+(\w+)\s+.*', cmd_str)
        if not match:
            subsys = 'general'
        else:
            subsys = match.group(1)

        #soundfile = 'g2_err_%s.au' % subsys
        soundfile = 'E_ERR%s.au' % subsys.upper()
        soundpath = os.path.join(cfg.g2soss.producthome, 'file/Sounds', soundfile)
        if os.path.exists(soundpath):
            cmd = "OSST_audioplay %s" % (soundpath)
            self.logger.debug(cmd)
            res = os.system(cmd)
        else:
            self.logger.error("No such audio file: %s" % soundpath)
        

    def update_page(self, bnch):

        page = bnch.page
        vals = bnch.state
        print "vals = %s" % str(vals)
        ast_num = vals['ast_num']

        cmd_str = None
        if vals.has_key('cmd_str'):
            cmd_str = vals['cmd_str']

            if not vals.has_key('inserted'):
                # Replace the decode string with the actual parameters
                self.replace_text(page, ast_num, cmd_str)
                vals['inserted'] = True
                try:
                    del vals['time_added']
                except KeyError:
                    pass

        if vals.has_key('task_error'):
            self.append_error(page, ast_num, '\n ==> ' + vals['task_error'])
            
            # audible warnings
            self.audible_warn(cmd_str, vals)

        elif vals.has_key('task_end'):
            if vals.has_key('task_start'):
                if self.track_elapsed and bnch.page.has_key('asttime'):
                    elapsed = vals['task_start'] - bnch.page.asttime
                else:
                    elapsed = vals['task_end'] - vals['task_start']
                self.update_time(page, ast_num, vals, '[ F %9.3f s ]: ' % (
                        elapsed))
            else:
                self.update_time(page, ast_num, vals, '[TE %s]: ' % (
                        self.time2str(vals['task_end'])))
            self.change_text(page, ast_num, foreground="blue2",
                             background="white")
                
        elif vals.has_key('end_time'):
            self.update_time(page, ast_num, vals, '[EN %s]: ' % (
                    self.time2str(vals['end_time'])))
            self.change_text(page, ast_num, foreground="blue1",
                             background="palegreen")
                
        elif vals.has_key('ack_time'):
            self.update_time(page, ast_num, vals, '[AB %s]: ' % (
                    self.time2str(vals['ack_time'])))
            self.change_text(page, ast_num, foreground="green4",
                             background="palegreen")

        elif vals.has_key('cmd_time'):
            self.update_time(page, ast_num, vals, '[CD %s]: ' % (
                    self.time2str(vals['cmd_time'])))
            self.change_text(page, ast_num, foreground="brown",
                             background="palegreen")

        elif vals.has_key('task_start'):
            self.update_time(page, ast_num, vals, '[TS %s]: ' % (
                    self.time2str(vals['task_start'])))
            self.change_text(page, ast_num, background="palegreen")

        else:
            #self.change_text(page, ast_num, foreground="gold2")
            pass

                
    def time2str(self, time_cmd):
        time_int = int(time_cmd)
        time_str = time.strftime("%H:%M:%S", time.localtime(float(time_int)))
        time_sfx = ('%.3f' % (time_cmd - time_int)).split('.')[1]
        title = time_str + ',' + time_sfx
        return title
            

    def process_ast(self, ast_id, vals):
        #print ast_id, vals

        with self.lock:
            try:
                page = self.pages[ast_id]
            except KeyError:
                # this page is not received/set up yet
                page = Bunch.Bunch(vals)
                page.nodes = {}
                self.pages[ast_id] = page

            if vals.has_key('ast_buf'):
                ast_str = ro.binary_decode(vals['ast_buf'])
                # Get the time of the command to construct the tab title
                title = self.time2str(vals['ast_time'])
                page.asttime = vals['ast_time']

                # TODO: what if this page has already been deleted?
                if self.save_decode_result:
                    self.addpage(ast_id + '.decode', title, ast_str)

                self.addpage(ast_id, title, ast_str)

            elif vals.has_key('ast_track'):
                path = vals['ast_track']

                curvals = self.monitor.getitems_suffixOnly(path)
                if isinstance(curvals, dict):
                    vals.update(curvals)
               
                # Make an entry for this ast node, if there isn't one already
                ast_num = '%d' % vals['ast_num']
                state = page.nodes.setdefault(ast_num, vals)

                bnch = Bunch.Bunch(page=page, state=state)
                self.track.setdefault(vals['ast_track'], bnch)
        
                # Replace the decode string with the actual parameters
                # ?? Has string really changed at this point??
                self.replace_text(page, ast_num, vals['ast_str'])
                
                self.update_page(bnch)
                

    def process_task(self, path, vals):
        #print path, vals

        with self.lock:
            try:
                bnch = self.track[path]
            except KeyError:
                # this page is not received/set up yet
                return

            #print path, vals
            bnch.state.update(vals)

            self.update_page(bnch)
            

    # this one is called if new data becomes available
    def anon_arr(self, payload, name, channels):
        self.logger.debug("received values '%s'" % str(payload))

        try:
            bnch = Monitor.unpack_payload(payload)

        except Monitor.MonitorError:
            self.logger.error("malformed packet '%s': %s" % (
                str(payload), str(e)))
            return

        try:
            ast_id = bnch.value['ast_id']
            # because gtk thread handling sucks
            gobject.idle_add(self.process_ast, ast_id, bnch.value)

        except KeyError:
            gobject.idle_add(self.process_task, bnch.path, bnch.value)
        
       

rc = """
style "window"
{
}

style "button"
{
  # This shows all the possible states for a button.  The only one that
  # doesn't apply is the SELECTED state.
  
  #fg[PRELIGHT] = {255, 255, 0}
  fg[PRELIGHT] = 'yellow'
  #bg[PRELIGHT] = "#089D20"
  #bg[PRELIGHT] = {8, 157, 32}
  bg[PRELIGHT] = 'forestgreen'
  #bg[PRELIGHT] = {1.0, 0, 0}
#  bg[ACTIVE] = { 1.0, 0, 0 }
#  fg[ACTIVE] = { 0, 1.0, 0 }
#  bg[NORMAL] = { 1.0, 1.0, 0 }
#  fg[NORMAL] = { .99, 0, .99 }
#  bg[INSENSITIVE] = { 1.0, 1.0, 1.0 }
#  fg[INSENSITIVE] = { 1.0, 0, 1.0 }

#GtkButton::focus-line-width = 1
#GtkButton::focus-padding = 0
GtkLabel::width-chars = 20
}

# In this example, we inherit the attributes of the "button" style and then
# override the font and background color when prelit to create a new
# "main_button" style.

style "main_button" = "button"
{
  font = "-adobe-helvetica-medium-r-normal--*-100-*-*-*-*-*-*"
  bg[PRELIGHT] = { 0.75, 0, 0 }
}

style "toggle_button" = "button"
{
  fg[NORMAL] = { 1.0, 0, 0 }
  fg[ACTIVE] = { 1.0, 0, 0 }
 
}

style "text"
{
  fg[NORMAL] = { 1.0, 1.0, 1.0 }
  font_name = "Monospace 10"
}

# These set the widget types to use the styles defined above.
# The widget types are listed in the class hierarchy, but could probably be
# just listed in this document for the users reference.

widget_class "GtkWindow" style "window"
widget_class "GtkDialog" style "window"
widget_class "GtkFileSelection" style "window"
widget_class "*GtkCheckButton*" style "toggle_button"
widget_class "*GtkRadioButton*" style "toggle_button"
widget_class "*GtkButton*" style "button"
widget_class "*GtkTextView" style "text"

# This sets all the buttons that are children of the "main window" to
# the main_button style.  These must be documented to be taken advantage of.
widget "main window.*GtkButton*" style "main_button"
"""

def main(options, args):
    
    # Create top level logger.
    logger = ssdlog.make_logger('sktask_gui', options)

    # evil hack required to use threads with GTK
    gtk.gdk.threads_init()

    # Parse resource string
    gtk.rc_parse_string(rc) 

    ro.init()

    ev_quit = threading.Event()

    # make a name for our monitor
    if options.monname:
        myMonName = options.monname
    else:
        myMonName = 'sktask_gtk-%s-%d.mon' % (
            ro.get_myhost(short=True), options.monport)

    #print myMonName

    # monitor channels we are interested in
    channels = options.channels.split(',')

    # Create a local monitor
    mymon = Monitor.Monitor(myMonName, logger, numthreads=20)

    skdisp = skDisp(logger, ev_quit, monitor=mymon,
                    monpath=options.monpath)
    if options.geometry:
        skdisp.setPos(options.geometry)
    skdisp.logupdate()

    # Subscribe our callback functions to the local monitor
    mymon.subscribe_cb(skdisp.anon_arr, channels)
    
    # for skfile in args:
    #     skdisp.parsefile(skfile)

    server_started = False
    try:
        # Startup monitor threadpool
        mymon.start(wait=True)
        # start_server is necessary if we are subscribing, but not if only
        # publishing
        mymon.start_server(wait=True, port=options.monport)
        server_started = True

        # subscribe our monitor to the central monitor hub
        mymon.subscribe_remote(options.monitor, channels, ())
    
        try:
            gtk.main()

        except KeyboardInterrupt:
            logger.error("Received keyboard interrupt!")

    finally:
        if server_started:
            mymon.stop_server(wait=True)
        mymon.stop(wait=True)
    
    logger.info("Exiting Gen2 skTask viewer...")
    ev_quit.set()
    sys.exit(0)
    

# Create demo in root window for testing.
if __name__ == '__main__':
  
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-c", "--channels", dest="channels", default='taskmgr0,g2task',
                      metavar="LIST",
                      help="Subscribe to the comma-separated LIST of channels")
    optprs.add_option("--display", dest="display", metavar="HOST:N",
                      help="Use X display on HOST:N")
    optprs.add_option("-g", "--geometry", dest="geometry",
                      metavar="GEOM", default="963x1037+0+57",
                      help="X geometry for initial size and placement")
    optprs.add_option("-m", "--monitor", dest="monitor", default='monitor',
                      metavar="NAME",
                      help="Subscribe to feeds from monitor service NAME")
    optprs.add_option("--monname", dest="monname", metavar="NAME",
                      help="Use NAME as our monitor subscriber name")
    optprs.add_option("-p", "--path", dest="monpath", default='mon.sktask',
                      metavar="PATH",
                      help="Show values for PATH in monitor")
    optprs.add_option("--monport", dest="monport", type="int", default=10013,
                      help="Register monitor using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("-n", "--svcname", dest="svcname", metavar="NAME",
                      help="Use NAME as our subscriber name")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

##     if len(args) != 0:
##         optprs.error("incorrect number of arguments")

    if options.display:
        os.environ['DISPLAY'] = options.display

    # Are we debugging this?
    if options.debug:
        import pdb

        pdb.run('main(options, args)')

    # Are we profiling this?
    elif options.profile:
        import profile

        print "%s profile:" % sys.argv[0]
        profile.run('main(options, args)')

    else:
        main(options, args)

#END


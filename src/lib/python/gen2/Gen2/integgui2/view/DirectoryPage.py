# 
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Nov  5 10:35:08 HST 2010
#]
import sys
import glob
import os, re
import gtk

import common
import LogPage


class DirectoryPage(LogPage.NotePage):

    def __init__(self, frame, name, title):
        super(DirectoryPage, self).__init__(frame, name, title)

        self.listing = []
        self.pattern = '*'
        self.clickfn = None

        self.cursor = 0
        self.moving_cursor = False

        self.tw.set_editable(False)
        #self.tw.connect("button-press-event", self.jump_tag)

        self.buf.connect("mark-set", self.show_cursor)

        # add standard decorative tags
        for tag, bnch in common.directory_tags:
            properties = {}
            properties.update(bnch)
            self.addtag(tag, **properties)

        # keyboard shortcuts
        self.tw.connect("key-press-event", self.keypress)
        self.tw.connect("enter-notify-event", self.focus_in)

        # add some bottom buttons
        ## self.btn_exec = gtk.Button("Exec")
        ## self.btn_exec.connect("clicked", lambda w: self.execute())
        ## self.btn_exec.modify_bg(gtk.STATE_NORMAL,
        ##                         common.launcher_colors['execbtn'])
        ## self.btn_exec.show()
        ## self.leftbtns.pack_end(self.btn_exec)

    def regist_clickfn(fn):
        """Register a function to be called on the files when you click them."""
        self.clickfn = fn

    def process_listing(self, listing):
        self.clear()
        for path in listing:
            dirname, filename = os.path.split(path)
            tags = ['normal']
            if os.path.isdir(path):
                filename += '/'
                tags = ['directory']
            elif os.path.islink(path):
                filename += '@'
                tags = ['link']
            else:
                #stat = os.stat(path)
                pass
            self.append(filename + '\n', tags)
        
    def listdir(self, dirpath, pattern):
        listing = glob.glob(os.path.join(dirpath, pattern))
        listing.append(os.path.join(dirpath, '..'))
        listing.sort()
        self.listing = listing
        self.process_listing(listing)
        
    def load(self, dirpath, pattern):
        self.listdir(dirpath, pattern)
        self.dirpath = dirpath
        self.pattern = pattern
        self._redraw()

    def reload(self):
        self.listdir(self.dirpath, self.pattern)
        self._redraw()


    def _redraw(self):
        # restore cursor
        end = self.buf.get_end_iter()
        #self.moving_cursor = False
        self.cursor = min(self.cursor, end.get_line())
        loc = self.buf.get_iter_at_line(self.cursor)
        self.buf.place_cursor(loc)

        # Hacky way to get our cursor on screen
        insmark = self.buf.get_insert()
        if insmark != None:
            res = self.tw.scroll_to_mark(insmark, 0, use_align=True)

    def redraw(self):
        common.gui_do(self._redraw)
        
    def show_cursor(self, tbuf, titer, tmark):
        if self.moving_cursor:
            return False
        
        insmark = tbuf.get_insert()
        if insmark != tmark:
            return False

        self.moving_cursor = True
        try:
            # Color the new line nwe
            start, end = tbuf.get_bounds()
            self.buf.remove_tag_by_name('cursor', start, end)

            line = titer.get_line()
            self.cursor = line
            start = tbuf.get_iter_at_line(line)
            end = start.copy()
            end.forward_to_line_end()
            ## end.forward_char()
            tbuf.apply_tag_by_name('cursor', start, end)

            selmark = tbuf.get_mark('selection_bound')
            seliter = tbuf.get_iter_at_mark(selmark)
            if not seliter.starts_line():
                tbuf.move_mark_by_name('selection_bound', start)
            tbuf.move_mark(insmark, start)

        finally:
            self.moving_cursor = False
        return True
    
    ## def jump_tag(self, w, evt):
    ##     print str(evt)
    ##     widget = self.tw
    ##     try:
    ##         tup = widget.window_to_buffer_coords(gtk.TEXT_WINDOW_TEXT,
    ##                                              evt.x, evt.y)
    ##         #print tup
    ##         buf_x1, buf_y1 = tup
    ##     except Exception, e:
    ##         self.logger.error("Error converting coordinates to line: %s" % (
    ##             str(e)))
    ##         return False
        
    ##     (startiter, coord) = widget.get_line_at_y(buf_y1)
    ##     lineno = startiter.get_line()
    ##     ## enditer = startiter.copy()
    ##     ## enditer.forward_to_line_end()
    ##     ## text = self.buf.get_text(startiter, enditer)
    ##     text = self.listing[lineno]
    ##     self.process_line(text)
       
    ##     return True
            
    def process_entry(self, text, keyname):
        """Subclass should override this to do something interesting when
        a folder link is clicked."""
        self.logger.debug("text is %s, key is '%s'" % (text, keyname))
        path = os.path.abspath(text)

        if keyname == 'e':
            common.view.gui_do(common.view.load_file, path)
            return True
        
        if keyname == 'i':
            common.view.gui_do(common.view.load_inf, path)
            return True
        
        if keyname == 'f':
            common.view.gui_do(common.view.load_ephem, path)
            return True
        
        if keyname == 't':
            common.view.gui_do(common.view.load_tscTrack, path)
            return True
        
        if keyname == 'Return':
            if os.path.isdir(path):
                self.load(path, self.pattern)
            else:
                common.view.gui_do(common.view.load_file, path)
            
        ## if (keyname == 'Return') and (self.clickfn):
        ##     common.controller.ctl_do(self.clickfn, text)

        return False
       
        
    def keypress(self, w, event):
        keyname = gtk.gdk.keyval_name(event.keyval)
        if keyname in ('Up', 'Down', 'Shift_L', 'Shift_R',
                       'Alt_L', 'Alt_R', 'Control_L', 'Control_R'):
            # navigation and other
            return False
        if keyname in ('Left', 'Right'):
            # ignore these
            return True
        #print "key pressed --> %s" % keyname

        if event.state & gtk.gdk.CONTROL_MASK:
            if keyname == 'r':
                self.reload()
                return True
            
            elif keyname == 'q':
                common.view.raise_queue()
                return True
        
            elif keyname == 'h':
                common.view.raise_handset()
                return True

        else:
            try:
                text = self.listing[self.cursor]
            except IndexError:
                return False
            
            return self.process_entry(text, keyname)
            
        return False
    

#END

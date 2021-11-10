# 
# Eric Jeschke (eric@naoj.org)
#
import os, re
import gtk

import Bunch

import common
import Page
import CommandObject

class QueuePage(Page.ButtonPage, Page.TextPage):

    def __init__(self, frame, name, title):

        super(QueuePage, self).__init__(frame, name, title)

        self.paused = False

        self.queueName = ''
        self.queueObj = None
        self.tm_queueName = 'executer'

        # Create the widgets for the text
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_border_width(2)

        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,
                                   gtk.POLICY_AUTOMATIC)

        tw = gtk.TextView()
        scrolled_window.add(tw)
        tw.show()
        scrolled_window.show()

        tw.set_editable(False)
        tw.set_wrap_mode(gtk.WRAP_NONE)
        tw.set_left_margin(4)
        tw.set_right_margin(4)

        self.tw = tw
        self.buf = tw.get_buffer()

        # Stores saved selection
        self.sel_i = None
        self.sel_j = None
        # Stores cut
        self.clip = []

        self.cursor = 0
        self.moving_cursor = False
        
        # keyboard shortcuts
        self.tw.connect("key-press-event", self.keypress)
        # Can't seem to get focus follows mouse effect
        #self.tw.connect("enter-notify-event", self.focus_in)
        self.buf.connect("mark-set", self.show_cursor)

        tagtbl = self.buf.get_tag_table()

        # remove decorative tags
        for tag, bnch in common.queue_tags:
            gtktag = tagtbl.lookup(tag)
            try:
                if gtktag:
                    self.buf.remove_tag_by_name(tag, start, end)
            except:
                # tag may not exist--that's ok
                pass

            properties = {}
            properties.update(bnch)
            try:
                self.buf.create_tag(tag, **properties)
            except:
                # tag may already exist--that's ok
                pass
        #self.buf.create_tag('selected', background="pink1")
        #self.buf.create_tag('cursor', background="skyblue1")

        frame.pack_start(scrolled_window, fill=True, expand=True)

        ## self.add_menu()
        ## self.add_close()

        # self.tw.drag_source_set(gtk.gdk.BUTTON1_MASK,
        #                       [('text/cmdtag', 0, 555)], gtk.gdk.ACTION_MOVE)
        # self.tw.drag_dest_set(gtk.DEST_DEFAULT_ALL,
        #                       [('text/cmdtag', 0, 555)], gtk.gdk.ACTION_MOVE)
        #self.tw.connect("drag-data-get", self.grabdata)
        #self.tw.connect("drag-drop", self.rearrange)

        # add some bottom buttons
        self.btn_exec = gtk.Button("Resume")
        self.btn_exec.connect("clicked", lambda w: self.resume())
        self.btn_exec.modify_bg(gtk.STATE_NORMAL,
                                common.launcher_colors['execbtn'])
        self.btn_exec.show()
        self.leftbtns.pack_end(self.btn_exec)

        self.btn_step = gtk.Button("Step")
        self.btn_step.connect("clicked", lambda w: self.step())
        self.btn_step.modify_bg(gtk.STATE_NORMAL,
                                common.launcher_colors['execbtn'])
        self.btn_step.show()
        self.leftbtns.pack_end(self.btn_step)

        self.btn_break = gtk.Button("Break")
        self.btn_break.connect("clicked", lambda w: self.insbreak(line=0))
        self.btn_break.show()
        self.leftbtns.pack_end(self.btn_break)

        self.btn_refresh = gtk.Button("Refresh")
        self.btn_refresh.connect("clicked", lambda w: self.redraw())
        self.btn_refresh.show()
        self.leftbtns.pack_end(self.btn_refresh)

        menu = self.add_pulldownmenu("Page")

        item = gtk.MenuItem(label="Close")
        # currently disabled
        item.set_sensitive(False)
        menu.append(item)
        item.connect_object ("activate", lambda w: self.close(),
                             "menu.Close")
        item.show()

        menu = self.add_pulldownmenu("Queue")

        item = gtk.MenuItem(label="Clear All")
        menu.append(item)
        item.connect_object ("activate", lambda w: common.controller.clearQueue(self.queueName),
                             "menu.Clear_All")
        item.show()

        item = gtk.MenuItem(label="Pop and edit command")
        menu.append(item)
        item.connect_object ("activate", lambda w: self.editCommand(),
                             "menu.Edit_command")
        item.show()


    def set_queue(self, queueName, queueObj):
        self.queueName = queueName
        self.queueObj = queueObj
        # Hmmm...asking for GC troubles?
        queueObj.add_view(self)
        
        # change our tab title to match the queue
        tabName = queueObj.name.capitalize()
        self.setLabel(tabName)

    def close(self):
        self.queueObj.del_view(self)
        super(QueuePage, self).close()

    def editCommand(self):
        try:
            cmdObj = self.queueObj.peek()
            self.queueObj.remove(cmdObj)

        except Exception, e:
            # TODO: popup error here?
            common.view.gui_do(common.view.popup_error, str(e))

        common.controller.editOne(cmdObj)

    def _redraw(self):
        common.view.assert_gui_thread()
        
        with self.lock:
            #self.moving_cursor = True
            common.clear_tv(self.tw)

            numlines = 0
            for cmdObj in self.queueObj.peekAll():
                tag = 'normal'
                try:
                    text = cmdObj.get_preview()
                    if text.startswith('###'):
                        tag = 'comment3'
                    elif text.startswith('##'):
                        tag = 'comment2'
                    elif text.startswith('#'):
                        tag = 'comment1'
                except Exception, e:
                    text = "++ THIS COMMAND HAS BEEN DELETED IN THE SOURCE PAGE ++"
                    tag = 'badref'
                    
                # Insert text icon at end of the 
                loc1 = self.buf.get_end_iter()
                self.buf.insert_with_tags_by_name(loc1, text, tag)
                loc2 = self.buf.get_end_iter()
                self.buf.insert(loc2, '\n')
                numlines += 1

            # Apply color to rows and save selection indexes
            # TODO: make selection a part of the CommandQueue?
            if self.has_selection():
                first, last = self.buf.get_bounds()
                self.sel_i = min(self.sel_i, numlines)
                first.set_line(self.sel_i)
                self.sel_j = min(self.sel_j, numlines)
                last.set_line(self.sel_j)
                last.forward_to_line_end()
                self.buf.apply_tag_by_name('selected', first, last)

            # restore cursor
            #self.moving_cursor = False
            self.cursor = min(self.cursor, numlines)
            #print "2. cursor is %d numlines is %d" % (self.cursor, numlines)
            loc = self.buf.get_iter_at_line(self.cursor)
            self.buf.place_cursor(loc)

            # Hacky way to get our cursor on screen
            insmark = self.buf.get_insert()
            if insmark != None:
                ## insiter = self.buf.get_iter_at_mark(insmark)
                ## insline = insiter.get_line()
                res = self.tw.scroll_to_mark(insmark, 0, use_align=True)
                #print "2. scrolling res is %s insline=%d" % (res, insline)
                

    def redraw(self):
        common.gui_do(self._redraw)
        
    def set_selection(self):
        # Clear previous selection, if any
        first, last = self.buf.get_bounds()
        self.buf.remove_tag_by_name('selected', first, last)

        # Get the range of text selected
        try:
            first, last = self.buf.get_selection_bounds()

            # Clear the selection
            common.clear_selection(self.tw)

        except ValueError:
            # If there is no selection, then use position of insertion mark
            insmark = self.buf.get_insert()
            if insmark == None:
                common.view.popup_error("Please make selection or set insertion mark first.")
                return

            first = self.buf.get_iter_at_mark(insmark)
            last = first.copy()
            last.forward_to_line_end()
            
        frow = first.get_line()
        lrow = last.get_line()

        # Adjust to beginning and end of lines
        if not first.starts_line():
            first.set_line(frow)
        if last.starts_line():
            # Hack to fix problem where selection covers the newline
            # but not the first character of the next line
            lrow -= 1
            last.set_line(lrow)
        if not last.ends_line():
            last.forward_to_line_end()
        #print "selection: %d-%d" % (frow, lrow)

        # Apply color to rows and save selection indexes
        self.buf.apply_tag_by_name('selected', first, last)
        self.sel_i = first.get_line()
        self.sel_j = last.get_line()
        
    def clear_selection(self):
        first, last = self.buf.get_bounds()
        self.buf.remove_tag_by_name('selected', first, last)

        common.clear_selection(self.tw)

        self.sel_i = None
        self.sel_j = None

    def has_selection(self):
        return self.sel_i != None
    
    def cut(self):
        if not self.has_selection():
            # Try to set a selection if none provided
            self.set_selection()
            
        if self.has_selection():
            (i, j) = (self.sel_i, self.sel_j)
            print "i=%d j=%d" % (i, j)
            self.clear_selection()

            self.clip = self.queueObj.delete(i, j+1)
        else:
            common.view.popup_error("Please make a selection first!")

    def copy(self):
        if not self.has_selection():
            # Try to set a selection if none provided
            self.set_selection()
            
        if self.has_selection():
            (i, j) = (self.sel_i, self.sel_j)
            print "i=%d j=%d" % (i, j)
            self.clear_selection()

            self.clip = self.queueObj.getslice(i, j+1)
        else:
            common.view.popup_error("Please make a selection first!")

    def set_clip(self, clip):
        # clip must contain CommandObjects!
        self.clip = clip
        
    def paste(self, clip=None):
        if clip == None:
            clip = self.clip
        if len(clip) == 0:
            common.view.popup_error("Please cut/copy the selection first.")
            return
        
        insmark = self.buf.get_insert()
        if insmark == None:
            common.view.popup_error("Please set insertion mark first.")
            return

        insiter = self.buf.get_iter_at_mark(insmark)
        k = insiter.get_line()

        self.queueObj.insert(k, clip)
        #self.clip = []
        
    def move(self):
        if not self.has_selection():
            common.view.popup_error("Please make a selection with 's' first.")
            return

        insmark = self.buf.get_insert()
        if insmark == None:
            common.view.popup_error("Please set insertion mark first.")
            return
        
        (i, j) = (self.sel_i, self.sel_j)
        print "i=%d j=%d" % (i, j)
        self.clear_selection()
        
        deleted = self.queueObj.delete(i, j+1)
        
        insmark = self.buf.get_insert()
        if insmark != None:
            insiter = self.buf.get_iter_at_mark(insmark)
        else:
            insiter = self.buf.get_end_iter()
            
        k = insiter.get_line()

        self.queueObj.insert(k, deleted)

        
    def insbreak(self, line=None):
        if line == None:
            insmark = self.buf.get_insert()
            if insmark != None:
                insiter = self.buf.get_iter_at_mark(insmark)
                line = insiter.get_line()
            else:
                line = 0

        try:
            cmdobj = CommandObject.BreakCommandObject('brk%d', self.queueName,
                                                     self.logger, self)
            self.queueObj.insert(line, [cmdobj])
        except Exception, e:
            common.view.popup_error(str(e))

    def _skip_comment(self, line):
        # TODO: need lock?
        while line < len(self.queueObj):
            cmdObj = self.queueObj[line]
            if isinstance(cmdObj, CommandObject.CommentCommandObject):
                line += 1
                continue
            break
        return line
    
    def _resume(self, w_break=False):
        """Callback when the Resume button is pressed.
        """
        # Check whether we are busy executing a command here
        if common.controller.executingP.isSet():
            # Yep--popup an error message
            common.view.popup_error("There is already a %s task running!" % (
                self.tm_queueName))
            return

        # Get length of queued items, if any
        num_queued = len(self.queueObj)
        
        if num_queued == 0:
            common.view.popup_error("No %s queued commands!" % (
                self.queueName))
            return

        if w_break:
            try:
                # Take a peek at the top item on the queue.  If it is not
                # a break, then insert a break right after the top command
                cmdobj = self.queueObj.peek()
                if not isinstance(cmdobj, CommandObject.BreakCommandObject):
                    cmdobj = CommandObject.BreakCommandObject('brk%d',
                                                              self.queueName,
                                                              self.logger, self)
                    i = self._skip_comment(0)
                    if i < num_queued:
                        i += 1
                    self.queueObj.insert(i, [cmdobj])
            except Exception, e:
                common.view.popup_error(str(e))
                return

        try:
            common.controller.execQueue(self.queueName,
                                        tm_queueName=self.tm_queueName)
        except Exception, e:
            common.view.popup_error(str(e))


    def resume(self):
        return self._resume()

    def step(self):
        return self._resume(w_break=True)

    def keypress(self, w, event):
        keyname = gtk.gdk.keyval_name(event.keyval)
        if keyname in ('Up', 'Down', 'Shift_L', 'Shift_R',
                       'Alt_L', 'Alt_R', 'Control_L', 'Control_R'):
            # navigation and other
            return False
        if keyname in ('Left', 'Right'):
            # ignore these
            return True
        print "key pressed --> %s" % keyname

        if keyname == 'r':
            self._redraw()
            return True
        elif keyname == 's':
            self.set_selection()
            return True
        elif keyname == 'a':
            self.clear_selection()
            return True
        elif keyname == 'c':
            self.copy()
            return True
        elif keyname == 'x':
            self.cut()
            return True
        elif keyname == 'v':
            self.paste()
            return True
        elif keyname == 'm':
            self.move()
            return True
        elif keyname == 'b':
            self.insbreak()
            return True

        common.view.setStatus("I don't understand that key: %s", keyname)
        return True
    
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
            tbuf.apply_tag_by_name('cursor', start, end)

            selmark = tbuf.get_mark('selection_bound')
            seliter = tbuf.get_iter_at_mark(selmark)
            if not seliter.starts_line():
                tbuf.move_mark_by_name('selection_bound', start)
            tbuf.move_mark(insmark, start)

        finally:
            self.moving_cursor = False
        return True
    
    def grabdata(self, tw, context, selection, info, tstamp):
        print "grabbing!"
        return True
    
    def rearrange(self, tw, context, x, y, tstamp):
        print "rearrange!"
        buf_x1, buf_y1 = tw.window_to_buffer_coords(gtk.TEXT_WINDOW_TEXT,
                                                    x, y)
        txtiter = tw.get_iter_at_location(buf_x1, buf_y1)

        print "Drop!"
        print '\n'.join([str(t) for t in context.targets])
        context.finish(True, False, tstamp)
        return True
    

#END

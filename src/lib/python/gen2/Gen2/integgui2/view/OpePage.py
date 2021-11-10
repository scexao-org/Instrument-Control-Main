# 
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Dec  1 17:22:51 HST 2011
#]
import sys, traceback

import os, re
import gobject, gtk

import common
import Page, CodePage
import CommandObject

import SOSS.parse.ope as ope

thisDir = os.path.split(sys.modules[__name__].__file__)[0]
icondir = os.path.abspath(os.path.join(thisDir, "..", "icons"))

warning_close = """
WARNING:        
You are attempting to delete text in this buffer that is needed
by queued commands.

Please choose one of the following options:

1) Don't close page.
2) Unlink queued commands from this page and close page.
3) Remove the commands from the queue and close page.

"""

warning_reload = """
WARNING:        
You are attempting to replace text in this buffer that is needed
by queued commands.

Please choose one of the following options:

1) Don't reload page.
2) Unlink queued commands from this page and reload page.
3) Remove the commands from the queue and reload page.
4) Open the OPE file again in a new page.

"""

warning_queued = """
WARNING:        
There are queued commands.

Please choose one of the following options:

1) Prepend these commands to the queue along with a breakpoint and execute.
2) Prepend these commands to the queue, but don't execute.
2) Append these commands to the queue, but don't execute.
3) Replace queued commands with these commands and execute.
4) Cancel this execute request.

"""


class OpePage(CodePage.CodePage, Page.CommandPage):

    def __init__(self, frame, name, title):
        super(OpePage, self).__init__(frame, name, title)

        self.queueName = 'default'
        self.tm_queueName = 'executer'

        self.varDict = {}

        # this is for variable definition popups
        self.tw.set_property("has-tooltip", True)
        self.tw.connect("query-tooltip", self.query_vardef)
        #self.tw.connect("focus-out-event", self.focus_out)
        self.tw.connect("focus-in-event", self.focus_in)

        self.tw.set_show_line_marks(True)
        self.tw.set_insert_spaces_instead_of_tabs(True)

        # add marker pixbufs
        pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(icondir,
                                                           'apple-green.png'))
        if pixbuf:
            self.tw.set_mark_category_pixbuf('executing', pixbuf)
        pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(icondir,
                                                           'apple-red.png'))
        if pixbuf:
            self.tw.set_mark_category_pixbuf('error', pixbuf)

        # keyboard shortcuts
        self.tw.connect("key-press-event", self.keypress)

        # add some bottom buttons
        self.btn_exec = gtk.Button("Exec")
        self.btn_exec.connect("clicked", lambda w: self.execute())
        self.btn_exec.modify_bg(gtk.STATE_NORMAL,
                                common.launcher_colors['execbtn'])
        self.btn_exec.show()
        self.leftbtns.pack_end(self.btn_exec)

        self.btn_append = gtk.Button("Append")
        self.btn_append.connect("clicked", lambda w: self.insert())
        self.btn_append.show()
        self.leftbtns.pack_end(self.btn_append)

        self.btn_prepend = gtk.Button("Prepend")
        self.btn_prepend.connect("clicked", lambda w: self.insert(loc=0))
        self.btn_prepend.show()
        self.leftbtns.pack_end(self.btn_prepend)

        self.btn_cancel = gtk.Button("Cancel")
        self.btn_cancel.connect("clicked", lambda w: self.cancel())
        self.btn_cancel.modify_bg(gtk.STATE_NORMAL,
                                common.launcher_colors['cancelbtn'])
        self.btn_cancel.show()
        self.leftbtns.pack_end(self.btn_cancel)

        self.btn_pause = gtk.Button("Pause")
        self.btn_pause.connect("clicked", self.toggle_pause)
        self.btn_pause.show()
        self.leftbtns.pack_end(self.btn_pause)

        # Add items to the menu
        menu = self.add_pulldownmenu("Buffer")
        
        item = gtk.MenuItem(label="Recolor")
        menu.append(item)
        item.connect_object ("activate", lambda w: self.color(),
                             "menu.Recolor")
        item.show()

        item = gtk.MenuItem(label="Uncolor")
        menu.append(item)
        item.connect_object ("activate", lambda w: self.color(eraseall=True),
                             "menu.Uncolor")
        item.show()

        item = gtk.MenuItem(label="Current")
        menu.append(item)
        item.connect_object ("activate", lambda w: self.current(),
                             "menu.Current")
        item.show()

        menu = self.add_pulldownmenu("Queue")

        item = gtk.MenuItem(label="Clear all")
        menu.append(item)
        item.connect_object ("activate", lambda w: common.controller.clearQueue(self.queueName),
                             "menu.Clear_all")
        item.show()

        item = gtk.MenuItem(label="Clear my")
        menu.append(item)
        item.connect_object ("activate", lambda w: self.unqueue_my_commands(),
                             "menu.Clear_my")
        item.show()

        item = gtk.MenuItem(label="Unlink my")
        menu.append(item)
        item.connect_object ("activate", lambda w: self.unlink_my_commands(),
                             "menu.Unlink_my")
        item.show()

        item = gtk.MenuItem(label="Attach to ...")
        menu.append(item)
        item.connect_object ("activate", lambda w: self.attach_queue(),
                             "menu.Attach_to")
        item.show()

        menu = self.add_pulldownmenu("Options")

        item = gtk.CheckMenuItem("Wrap lines")
        item.set_active(False)
        menu.append(item)
        item.connect("activate", self.toggle_line_wrapping)
        item.show()

        item = gtk.CheckMenuItem("Show line numbers")
        item.set_active(False)
        menu.append(item)
        item.connect("activate", self.toggle_line_numbering)
        item.show()

        item = gtk.CheckMenuItem("Don't link commands to page")
        item.set_active(False)
        menu.append(item)
        item.connect("activate", lambda w: self.toggle_var(w, 'add_frozen'))
        item.show()

        # option variables
        self.add_frozen = False


    def toggle_var(self, widget, key):
        if widget.active: 
            self.__dict__[key] = True
        else:
            self.__dict__[key] = False

    def build_dialog(self, title, text, func):
        dialog = gtk.MessageDialog(flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                                   type=gtk.MESSAGE_WARNING,
                                   message_format=text)
        dialog.set_title(title)
        dialog.connect("response", func)
        return dialog

    def load(self, filepath, buf):
        super(OpePage, self).load(filepath, buf)
        self.cond_color()

    def _reload(self):
        super(OpePage, self).reload()
        self.cond_color()
        common.remove_all_marks(self.buf)

    def reload(self):
        if not self.reload_check():
            return
        self._reload()

    def reload_check(self):
        num = len(self.my_queued_commands())
        if num == 0:
            return True
        #common.view.popup_error("%d commands are still queued!" % num)
        w = self.build_dialog("%d commands are queued" % num,
                              warning_reload, self.reload_check_res)
        w.add_button("Cancel", 1)
        w.add_button("Unlink", 2)
        w.add_button("Remove", 3)
        w.add_button("New Page", 4)
        w.show()
        return False

    def reload_check_res(self, w, rsp):
        w.destroy()
        if rsp == 2:
            self.unlink_my_commands()
            self._reload()

        elif rsp == 3:
            self.unqueue_my_commands()
            self._reload()

        elif rsp == 4:
            common.view.load_generic(self.filepath, OpePage)

        return True

    def queued_check(self, fn_res):
        num = len(self.my_queued_commands())
        if num == 0:
            return True
        w = self.build_dialog("%d commands are queued" % num,
                              warning_queued, fn_res)
        w.add_button("Prepend w/Break and Exec", 1)
        w.add_button("Prepend", 2)
        w.add_button("Append", 3)
        w.add_button("Replace and Exec", 4)
        w.add_button("Cancel", 5)
        w.show()
        return False

    def close_check(self):
        num = len(self.my_queued_commands())
        if num == 0:
            return True
        #common.view.popup_error("%d commands are still queued!" % num)
        w = self.build_dialog("%d commands are queued" % num,
                              warning_close, self.close_check_res)
        w.add_button("Cancel", 1)
        w.add_button("Unlink", 2)
        w.add_button("Remove", 3)
        w.show()
        return False

    def close_check_res(self, w, rsp):
        w.destroy()
        if rsp == 2:
            self.unlink_my_commands()
            self._close()
            
        elif rsp == 3:
            self.unqueue_my_commands()
            self._close()
            
        return True

    def _close(self):
        super(OpePage, self).close()

    def close(self):
        if not self.close_check():
            return
        self._close()

    def unqueue_my_commands(self):
        tags = self.my_queued_commands()
        common.controller.remove_by_tags(tags)
        
    def unlink_my_commands(self):
        tags = self.my_queued_commands()
        self._convert_linked_commands(tags)
        return True
            
    def my_queued_commands(self):
        """Return the list of tags from our text buffer that are referenced
        from active queues."""
        tags = common.controller.get_all_queued_tags()
        return self.sift_tags(tags)
        
    def remove_commands(self, tags):
        """Remove from any queues commands corresponding to this
        list of tags."""
        common.controller.remove_by_tag(tags)
        
    def sift_tags(self, taglist):
        """From a list of tags (taglist), return the subset that are
        defined in our buffer."""
        # TODO: can we improve the efficiency of this?
        res = []
        tagtbl = self.buf.get_tag_table()
        num = 0
        for tagname in taglist:
            if tagtbl.lookup(tagname) != None:
                res.append(tagname)
        return res

    def cond_color(self):
        name, ext = os.path.splitext(self.filepath)
        ext = ext.lower()

        if ext in ('.ope', '.cd'):
            self.color()

    def get_vardef(self, varname):
        try:
            return self.varDict[varname]
        except KeyError:
            raise Exception("No definition found for '%s'" % varname)
        
    def color(self, reporterror=True, eraseall=False):
        try:
            # Get the text from the code buffer
            start, end = self.buf.get_bounds()
            buf = self.buf.get_text(start, end)

            # compute the variable dictionary
            include_dirs = common.view.include_dirs

            # check the file
            self.logger.debug("Parsing OPE file.")
            res = ope.check_ope(buf, include_dirs=include_dirs)

            # store away our variable dictionary for future reference
            self.varDict = res.vardict

            tagtbl = self.buf.get_tag_table()
            tags = common.decorative_tags + common.execution_tags

            if eraseall:
                removetags = tags
            else:
                removetags = common.decorative_tags

            # Get "Tags" page
            tagpage = common.view.tagpage
            # TODO: what if user closed Tags page?
            
            # Remove everything from the tag buffer
            self.logger.debug("Preparing tags.")
            tagpage.initialize(self)

            # remove decorative tags
            for tag, bnch in removetags:
                gtktag = tagtbl.lookup(tag)
                try:
                    if gtktag:
                        self.buf.remove_tag_by_name(tag, start, end)
                except:
                    # tag may not exist--that's ok
                    pass

            # add tags back in
            for tag, bnch in tags:
                properties = {}
                properties.update(bnch)
                try:
                    self.buf.create_tag(tag, **properties)
                except:
                    # tag may already exist--that's ok
                    pass

                try:
                    tagpage.addtag(tag, **properties)
                except:
                    # tag may already exist--that's ok
                    pass

            # Update the tag coloring and the tag list
            self.logger.debug("Coloring tags.")
            for bnch in res.taglist:
                lineno = bnch.lineno - 1
                # apply desired tags to entire line in main text buffer
                start.set_line(lineno)
                end.set_line(lineno)
                end.forward_to_line_end()

                for tag in bnch.tags:
                    self.buf.apply_tag_by_name(tag, start, end)

                tagpage.add_mapping(lineno, bnch.text, bnch.tags)

            # apply desired tags to varrefs in main text buffer
            self.logger.debug("Coloring refs.")
            for bnch in res.reflist:
                #print bnch
                lineno = bnch.lineno - 1
                
                start.set_line(lineno)
                start.forward_chars(bnch.start)
                end.set_line(lineno)
                end.forward_chars(bnch.end)
                if end.get_line() > lineno:
                    end.backward_char()

                self.buf.apply_tag_by_name('varref', start, end)
                if bnch.varref in res.badset:
                    self.buf.apply_tag_by_name('badref', start, end)

            self.logger.debug("Summarizing.")
            common.view.statusMsg('')
            errlst = []
            if len(res.badset) > 0:
                # Add all undefined refs to the tag table
                errline = tagpage.get_end_lineno()
                tagpage.add_mapping(1, "UNDEFINED VARIABLE REFS", ['badref'])
                for bnch in res.badlist:
                    tagpage.add_mapping(bnch.lineno, "%s: line %d" % (
                        bnch.varref, bnch.lineno), ['badref'])

                errmsg = "Undefined variable references: " + \
                         ' '.join(res.badset)
                errlst.append(errmsg)

                # scroll tag table to errors
                tagpage.scroll_to_lineno(errline)

            if len(res.badcoords) > 0:
                # Add all bad coords to the tag table
                errline = tagpage.get_end_lineno()
                tagpage.add_mapping(1, "POSSIBLE BAD COORDINATES", ['badref'])
                for bnch in res.badcoords:
                    tagpage.add_mapping(bnch.lineno, "line %d: %s" % (
                        bnch.lineno, bnch.errstr), ['badref'])

                errmsg = "Possible bad RA/DEC coordinates."
                errlst.append(errmsg)

                # scroll tag table to errors
                tagpage.scroll_to_lineno(errline)

            if len(errlst) > 0:
                errlst.append("See bottom of tags for details.")
                errmsg = '; '.join(errlst)
                if reporterror:
                    common.view.raise_page('tags')
                    common.view.popup_error(errmsg)
                else:
                    common.view.statusMsg(errmsg)
                    
                tagpage.tablbl.set_markup('<span background="orange">Tags</span>')

            else:
                tagpage.tablbl.set_markup('<span>Tags</span>')
                
                
        except Exception, e:
            errmsg = "Error coloring buffer: %s" % (str(e))
            self.logger.error(errmsg)
            common.view.statusMsg(errmsg)
            if reporterror:
                common.view.popup_error(errmsg)
            

    def focus_in(self, w, evt):
        self.logger.debug("got focus!")
        self.color(reporterror=False)
        return False

    def focus_out(self, w, evt):
        self.logger.info("lost focus!")
        try:
            first, last = self.buf.get_selection_bounds()
            self.buf.apply_tag_by_name('savedselection', first, last)
        except ValueError:
            print "Error getting selection--no selection?"
        return False

    def current(self):
        """Scroll to the current position in the buffer.  The current
        poistion is determined by the first tag found, otherwise it
        just scrolls to the mark position.
        """

        # Try to find a mark ('executing' or 'error') and scroll to it
        start, end = self.buf.get_bounds()
        res = self.buf.forward_iter_to_source_mark(start, None)
        if res:
            self.scroll_to_lineno(start.get_line())
            return
        
        # If we can't find a mark then look for tags
        # It might be better to scroll to the mark than these tags
        for tag in ('executing', 'queued', 'error', 'done'):
            try:
                start, end = common.get_region(self.buf, tag)
                self.scroll_to_lineno(start.get_line())
                return

            except common.TagError:
                continue

        #common.view.popup_error("Sorry, cannot find any region of interest.")
        # Scroll to mark, if any
        res = self.tw.scroll_mark_onscreen(self.mark)


    def reset(self):
        common.clear_tags(self.buf, ('executing',))
        # this will reset Pause button, etc.
        super(OpePage, self).reset()

    def query_vardef(self, tw, x, y, kbmode, ttw):
        # parameters are text widget, x and y coords, boolean for keyboard
        # mode (?) and the tooltip widget.  Return True if a tooltip should
        # be displayed
        #print "tooltip: args are %s" % (str(args))
        buf_x1, buf_y1 = tw.window_to_buffer_coords(gtk.TEXT_WINDOW_TEXT,
                                                    x, y)
        txtiter = tw.get_iter_at_location(buf_x1, buf_y1)

        buf = tw.get_buffer()
        tagtbl = buf.get_tag_table()
        varref = tagtbl.lookup('varref')
        if not varref:
            return False
        
        # Check if we are in the middle of a varref
        result = txtiter.has_tag(varref)
        if not result:
            #print "tooltip: not in word!"
            return False

        # Get boundaries of the tag.
        # TODO: there must be a more efficient way to do this!
        startiter = txtiter.copy()
        while not startiter.begins_tag(varref):
            startiter.backward_char()

        enditer = txtiter.copy()
        while not enditer.ends_tag(varref):
            enditer.forward_char()

        # Get the text of the varref
        varname = buf.get_text(startiter, enditer)
        varname = varname[1:]
        try:
            res = self.get_vardef(varname)
            ttw.set_text(res)
        except Exception, e:
            ttw.set_text(str(e))
            
        return True


    def copy(self):
        # A hack to get around accidentally copying rich text tags along
        # with the text

        # Get the selection.  If there is none, we're done.
        tup = self.buf.get_selection_bounds()
        if not tup:
            return

        # Set the clipboard to the plain ASCII text
        text = self.buf.get_text(*tup)
        common.view.clipboard.set_text(text, -1)

        
    def keypress(self, w, event):
        keyname = gtk.gdk.keyval_name(event.keyval)
        #print "key pressed --> %s" % keyname

        if event.state & gtk.gdk.CONTROL_MASK:
            if keyname == 't':
                common.view.raise_page('tags')
                return True
        
            elif keyname == 'r':
                self.color()
                return True
        
            ## elif keyname == 'e':
            ##     self.color(eraseall=True)
            ##     return True
        
            elif keyname == 'l':
                self.current()
                return True
        
            elif keyname == 'q':
                common.view.raise_page('queues')
                return True
        
            elif keyname == 'h':
                common.view.raise_page('handset')
                return True
        
            elif keyname == 'c':
                self.copy()
                return True
        
            elif keyname == 'f':
                self.find()
                return True
        
        return False
    

    def process_cmdstr(self, txtbuf, cmdstr):
        cmdstr = cmdstr.strip()

        # remove trailing semicolon, if present
        if cmdstr.endswith(';'):
            cmdstr = cmdstr[:-1]

        # Resolve all variables/macros
        try:
            self.logger.debug("Unprocessed command is: %s" % cmdstr)
            include_dirs = common.view.include_dirs
            p_cmdstr = ope.getCmd(txtbuf, cmdstr, include_dirs)
            self.logger.debug("Processed command is: %s" % p_cmdstr)

            return p_cmdstr
        
        except Exception, e:
            errstr = "Error parsing command: %s" % (str(e))
            raise Exception(errstr)


    def _convert_linked_commands(self, tags):
        """Takes a set of command tags, as may be found in our text buffer,
        and converts any queued instance of it to a new SimpleCommandObject
        (which contains the expanded command string) and that is not linked
        to this page.
        """

        # Get current value of text buffer
        start, end = self.buf.get_bounds()
        txtbuf = self.buf.get_text(start, end)

        # Get all the commands strings referenced by _tags_ and put
        # them in dict _cmds_
        cmds = {}
        for tag in tags:
            # Now get the command from the text widget
            start, end = common.get_region_lines(self.buf, tag)
            cmds[tag] = self.buf.get_text(start, end)

        # Define a mapping 
        # NOTE: enclosed function captures values of tags, cmds and
        #   txtbuf
        def f(cmdObj):
            tag = str(cmdObj)
            if not (tag in tags):
                return cmdObj
            
            cmdstr = self.process_cmdstr(txtbuf, cmds[tag])
            return CommandObject.SimpleCommandObject('cp%d', self.queueName,
                                                     self.logger,
                                                     cmdstr)

        # This function just iterates over all current queues, applying
        # the mapping function
        def g():
            for queueObj in common.controller.queue.values():
                queueObj.mapFilter(f)

        # Execute this as a thread in the controller
        common.controller.ctl_do(g)


    def _get_commands_from_selection(self, copytext=None):

        if copytext == None:
            copytext = self.add_frozen
            
        if copytext:
            # If copytext==True then we are not storing a reference
            # to the command in the page, but the command string
            # already pre-expanded
            start, end = self.buf.get_bounds()
            txtbuf = self.buf.get_text(start, end)
        
        # Get the range of text selected
        try:
            first, last = self.buf.get_selection_bounds()
        except ValueError:
            raise common.SelectionError("Error getting selection--no selection?")
            
        frow = first.get_line()
        lrow = last.get_line()
        if last.starts_line():
            # Hack to fix problem where selection covers the newline
            # but not the first character of the next line
            lrow -= 1
        #print "selection: %d-%d" % (frow, lrow)

        # Clear the selection
        common.clear_selection(self.tw)

        # Break selection into individual lines
        cmds = []

        for i in xrange(int(lrow)+1-frow):

            row = frow+i
            #print "row: %d" % (row)

            first.set_line(row)
            last.set_line(row)
            last.forward_to_line_end()
            if last.get_line() > row:
                # forward_to_line_end() seems to go to the next row
                # if the line consists of simply a newline
                cmd = ""
            else:
                cmd = self.buf.get_text(first, last).strip()
            self.logger.debug("cmd=%s" % (cmd))
            if (len(cmd) == 0) or cmd.startswith('#'):
                # TODO: linked comments
                cmdobj = CommandObject.CommentCommandObject('cm%d',
                                                            self.queueName,
                                                            self.logger, cmd)

            elif copytext:
                cmdstr = self.process_cmdstr(txtbuf, cmd)
                cmdobj = CommandObject.SimpleCommandObject('cp%d',
                                                           self.queueName,
                                                           self.logger, cmdstr)
            else:
                # tag the text so we can manipulate it later
                cmdobj = OpeCommandObject('ope%d', self.queueName,
                                          self.logger, self)
                tag = cmdobj.guitag
                self.buf.create_tag(tag)
                self.buf.apply_tag_by_name(tag, first, last)

            cmds.append(cmdobj)

        return cmds

    def _save_selection(self):
        """A hack to work around a bug/feature of the textview where it
        loses the selection when it loses focus.  This method can be used
        to save the focus.  Call _restore_selection() to restore it.
        """
        try:
            first, last = self.buf.get_selection_bounds()
            self.sel_first = first
            self.sel_last = last
            
        except ValueError:
            raise Exception("Error getting selection--no selection?")

        first = first.copy()
        last = last.copy()
        
        tag = 'savedselection'
        tt = self.buf.get_tag_table()

        # Create it so priority is highest
        tt_tag = tt.lookup(tag)
        if tt_tag:
            tt.remove(tt_tag)
        self.buf.create_tag(tag, background='lightpink1')
        # Adjust apparent selection to line start and end
        if not first.starts_line():
            first.set_line(first.get_line())
        if last.starts_line():
            last.set_line(last.get_line()-1)
        if not last.ends_line():
            last.forward_to_line_end()
        self.buf.apply_tag_by_name(tag, first, last)


    def _restore_selection(self):
        """A hack to work around a bug/feature of the textview where it
        loses the selection when it loses focus.  This method can be used
        to restore the focus.  Call _save_selection() to save it.
        """
        tag = 'savedselection'
        first, last = self.buf.get_bounds()
        try:
            self.buf.remove_tag_by_name(tag, first, last)
        except:
            pass

        self.buf.move_mark_by_name("insert", self.sel_first)
        self.buf.move_mark_by_name("selection_bound", self.sel_last)


    def execute(self, copytext=None):
        """Callback when the EXEC button is pressed.
        """
        # Check whether we are busy executing a command here
        if common.controller.executingP.isSet():
            # Yep--popup an error message
            common.view.popup_error("There is already a %s task running!" % (
                self.tm_queueName))
            return

        # Get length of queued items, if any
        queue = common.controller.queue[self.queueName]
        num_queued = len(queue)
        
        if not self.buf.get_has_selection():
            # No selection.  See if there are previously queued commands
            if num_queued == 0:
                common.view.popup_error("No mouse selection and no %s queued commands!" % (
                    self.queueName))
            else:
                #------------------
                def _execute_1(res):
                    if res != 'yes':
                        return
                    common.controller.execQueue(self.queueName,
                                                tm_queueName=self.tm_queueName)
                #------------------
        
                if common.view.suppress_confirm_exec:
                    _execute_1('yes')
                else:
                    common.view.popup_confirm("Confirm execute",
                                              "No selection--resume execution of %s queued commands?" % (
                        self.queueName),
                                              _execute_1)
                
            return

        #------------------
        # Code to do if we have a selection
        def _execute_2(w, rsp):
            if w:
                w.destroy()
                self._restore_selection()

            try:
                cmds = self._get_commands_from_selection(copytext=copytext)

                if rsp == 1:
                    cmdobj = CommandObject.BreakCommandObject('brk%d',
                                                              self.queueName,
                                                              self.logger, self)
                    queue.prepend(cmdobj)
                    queue.insert(0, cmds)
                    common.controller.execQueue(self.queueName,
                                                tm_queueName=self.tm_queueName)
                elif rsp == 2:
                    queue.insert(0, cmds)
                elif rsp == 3:
                    queue.extend(cmds)
                elif rsp == 4:
                    queue.replace(cmds)
                    common.controller.execQueue(self.queueName,
                                                tm_queueName=self.tm_queueName)

            except Exception, e:
                common.view.popup_error(str(e))
            return True

        #------------------

        # <== There is a selection
        if num_queued > 0:
            if common.view.suppress_confirm_exec:
                #_execute_2(None, 1)
                _execute_2(None, 4)
            else:
                self._save_selection()
                self.queued_check(_execute_2)

        else:
            _execute_2(None, 4)


    def insert(self, loc=None, copytext=None):
        """Callback when the APPEND button is pressed.
        """
        if not self.buf.get_has_selection():
            # No selection.
            common.view.popup_error("No mouse selection!")
            return

        try:
            cmds = self._get_commands_from_selection(copytext=copytext)
            #print len(cmds), "selected!"

            queue = common.controller.queue[self.queueName]
            if loc == None:
                queue.extend(cmds)
            else:
                queue.insert(loc, cmds)
        except Exception, e:
            common.view.popup_error(str(e))

    def attach_queue(self):
        dialog = gtk.MessageDialog(flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                                   type=gtk.MESSAGE_QUESTION,
                                   buttons=gtk.BUTTONS_OK_CANCEL,
                                   message_format="Pick the destination queue:")
        dialog.set_title("Connect Queue")
        # Add a combo box to the content area containing the names of the
        # current queues
        vbox = dialog.get_content_area()
        cbox = gtk.combo_box_new_text()
        index = 0
        names = []
        for name in common.controller.queue.keys():
            cbox.insert_text(index, name.capitalize())
            names.append(name)
            index += 1
        cbox.set_active(0)
        vbox.add(cbox)
        cbox.show()
        dialog.connect("response", self.attach_queue_res, cbox, names)
        dialog.show()

    def attach_queue_res(self, w, rsp, cbox, names):
        queueName = names[cbox.get_active()].strip().lower()
        w.destroy()
        if rsp == gtk.RESPONSE_OK:
            if not common.view.queue.has_key(queueName):
                common.view.popup_error("No queue with that name exists!")
                return True
            self.queueName = queueName
        return True
        

class OpeCommandObject(CommandObject.CommandObject):

    def __init__(self, format, queueName, logger, opepage):
        self.page = opepage
        
        super(OpeCommandObject, self).__init__(format, queueName, logger)


    def get_preview(self):
        """This is called to get a preview of the command string that
        should be executed.
        """
        common.view.assert_gui_thread()

        # Get the entire buffer from the page's text widget
        buf = self.page.buf
        # Now get the command from the text widget
        start, end = common.get_region_lines(buf, self.guitag)
        #start, end = common.get_region(buf, self.guitag)
        cmdstr = buf.get_text(start, end).strip()

        # remove trailing semicolon, if present
        if cmdstr.endswith(';'):
            cmdstr = cmdstr[:-1]

        self.logger.debug("preview is '%s'" % (cmdstr))
        return '>>' + cmdstr

    def _get_cmdstr(self):
        """This is called to get the command string that should be executed.
        """
        common.view.assert_gui_thread()

        # Get the entire buffer from the page's text widget
        buf = self.page.buf
        start, end = buf.get_bounds()
        txtbuf = buf.get_text(start, end)

        # Now get the command from the text widget
        start, end = common.get_region_lines(buf, self.guitag)
        #start, end = common.get_region(buf, self.guitag)
        cmdstr = buf.get_text(start, end)

        return (txtbuf, cmdstr)
    
    def get_cmdstr(self):
        common.view.assert_nongui_thread()

        # Get the command string associated with this kind of page.
        # We are executing in another thread, so use gui_do_res()
        # to get the text
        f_res = common.gui_do_res(self._get_cmdstr)
        txtbuf, cmdstr = f_res.get_value(timeout=10.0)

        cmdstr = self.page.process_cmdstr(txtbuf, cmdstr)
        return cmdstr


    def _mark_status(self, txttag):
        """This is called when our command changes status.  _txttag_ should
        be one of unqueued, queued, normal, executing, done, error
        """
        common.view.assert_gui_thread()

        # Get the entire OPE buffer
        buf = self.page.buf
        start, end = common.get_region_lines(buf, self.guitag)
        #start, end = common.get_region(buf, self.guitag)

        if txttag == 'unqueued':
            common.clear_tags_region(buf, ('queued',),
                                     start, end)
            return

        if txttag == 'normal':
            common.clear_tags_region(buf, ('done', 'error', 'executing'),
                                     start, end)
            return

        if txttag == 'executing':
            common.clear_tags_region(buf, ('done', 'error'),
                                     start, end)
            # annotate line with executing mark
            common.remove_all_marks(buf)
            buf.create_source_mark(None, 'executing', start)

        elif txttag in ('done',):
            common.clear_tags_region(buf, ('executing',),
                                     start, end)
        elif txttag in ('error',):
            common.clear_tags_region(buf, ('executing',),
                                     start, end)
            # annotate line with error mark
            common.remove_all_marks(buf)
            buf.create_source_mark(None, 'error', start)
            
        buf.apply_tag_by_name(txttag, start, end)

    def mark_status(self, txttag):
        # This MAY be called from a non-gui thread
        common.gui_do(self._mark_status, txttag)
        

class OpeCommentCommandObject(CommandObject.CommandObject):

    def __init__(self, format, queueName, logger, opepage):
        self.page = opepage
        
        super(OpeCommentCommandObject, self).__init__(format,
                                                      queueName, logger)


    def get_preview(self):
        """This is called to get a preview of the command string that
        should be executed.
        """
        common.view.assert_gui_thread()

        # Get the entire buffer from the page's text widget
        buf = self.page.buf
        # Now get the command from the text widget
        start, end = common.get_region_lines(buf, self.guitag)
        #start, end = common.get_region(buf, self.guitag)
        comment = buf.get_text(start, end).strip()

        self.logger.debug("preview is '%s'" % (comment))
        return '>>' + comment

    def _get_cmdstr(self):
        return '== NOP =='
    
    def get_cmdstr(self):
        return '== NOP =='
        
    def mark_status(self, txttag):
        pass
        

#END

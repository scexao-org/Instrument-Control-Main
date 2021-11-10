# 
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Mar 28 14:17:14 HST 2012
#]
import os.path
import string

import common
import Page
import dialogs

import gtk
import gtksourceview2

warning_close = """
WARNING: Buffer is modified

Please choose one of the following options:

1) Don't close page.
2) Close without saving.
3) Save buffer and close page.

"""

class CodePage(Page.ButtonPage, Page.TextPage):

    def __init__(self, frame, name, title):

        super(CodePage, self).__init__(frame, name, title)

        # Path of the file loaded into this buffer
        self.filepath = ''
        
        # Used to strip out bogus characters from buffers
        acceptchars = set(string.printable)
        self.deletechars = ''.join(set(string.maketrans('', '')) -
                                   acceptchars)
        self.transtbl = string.maketrans('\r', '\n')

        self.border = gtk.Frame("")
        self.border.set_shadow_type(gtk.SHADOW_ETCHED_OUT)
        self.border.set_label_align(0.1, 0.5)

        # Create the widgets for the OPE file text
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_border_width(2)

        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,
                                   gtk.POLICY_AUTOMATIC)

        # create buffer
        lm = gtksourceview2.LanguageManager()
        self.buf = gtksourceview2.Buffer()
        self.buf.set_data('languages-manager', lm)

        tw = gtksourceview2.View(self.buf)
        scrolled_window.add(tw)
        tw.show()
        scrolled_window.show()

        tw.set_editable(True)
        tw.set_wrap_mode(gtk.WRAP_NONE)
        tw.set_left_margin(4)
        tw.set_right_margin(4)

        self.tw = tw
        # hack to get auto-scrolling to work
        self.mark = self.buf.create_mark('end', self.buf.get_end_iter(),
                                         False)
        # For find & replace
        self.searchmark = self.buf.create_mark('search',
                                               self.buf.get_start_iter(),
                                               False)
        self.sr = dialogs.SearchReplace("Find and/or Replace")
        self.buf.connect('mark-set', self.place_cursor_cb)

        self.border.add(scrolled_window)
        self.border.show()

        frame.pack_start(self.border, fill=True, expand=True)

        menu = self.add_pulldownmenu("Page")

        item = gtk.MenuItem(label="Reload")
        menu.append(item)
        item.connect_object ("activate", lambda w: self.reload(),
                             "menu.Reload")
        item.show()

        item = gtk.MenuItem(label="Save")
        menu.append(item)
        item.connect_object ("activate", lambda w: self.save(),
                             "menu.Save")
        item.show()

        item = gtk.MenuItem(label="Save as ...")
        menu.append(item)
        item.connect_object ("activate", lambda w: self.save_as(),
                             "menu.Save_As")
        item.show()

        item = gtk.MenuItem(label="Save selection as ...")
        menu.append(item)
        item.connect_object ("activate", lambda w: self.save_selection_as(),
                             "menu.Save_As")
        item.show()

        #self.add_close()
        item = gtk.MenuItem(label="Close")
        menu.append(item)
        item.connect_object ("activate", lambda w: self.close(),
                             "menu.Close")
        item.show()

        menu = self.add_pulldownmenu("Buffer")

        item = gtk.MenuItem(label="Find/Replace ...")
        menu.append(item)
        item.connect_object ("activate", lambda w: self.find(),
                             "menu.Find")
        item.show()

        item = gtk.MenuItem(label="Print ...")
        menu.append(item)
        item.connect_object ("activate", lambda w: self.print_cb(),
                             "menu.Print")
        item.show()


    def loadbuf(self, buftxt):

        # "cleanse" text--change CR to NL, delete unprintable chars
        # TODO: what about unicode?
        buftxt = buftxt.translate(self.transtbl, self.deletechars)
        # translate tabs
        buftxt = buftxt.replace('\t', '        ')

        self.buf.begin_not_undoable_action()

        # insert text
        #tags = ['code']
        tags = []
        try:
            start, end = self.buf.get_bounds()
            self.buf.remove_source_marks(start, end)
            self.buf.delete(start, end)
        except:
            pass

        # Create default 'code' tag
        try:
            self.buf.create_tag('code', foreground="black")
        except:
            # tag may be already created
            pass

        self.buf.insert_with_tags_by_name(start, buftxt, *tags)
        self.buf.set_modified(False)

        self.buf.end_not_undoable_action()


    def load(self, filepath, buf):
        self.loadbuf(buf)
        self.filepath = filepath
        #lw = self.txt.component('label')
        #lw.config(text=filepath)
        self.border.set_label(filepath)

        manager = self.buf.get_data('languages-manager')
        language = manager.guess_language(filepath)
        if language:
            self.buf.set_highlight_syntax(True)
            self.buf.set_language(language)
        else:
            self.logger.info('No language found for file "%s"' % filepath)
            self.buf.set_highlight_syntax(False)

        #self.buf.set_modified(False)

        
    def reload(self):
        try:
            in_f = open(self.filepath, 'r')
            buf = in_f.read()
            in_f.close()
        except IOError, e:
            # ? raise exception instead ?
            return common.view.popup_error("Cannot read '%s': %s" % (
                    self.filepath, str(e)))

        self.loadbuf(buf)

    def _do_save(self):
            # TODO: make backup?

            # get text to save
            start, end = self.buf.get_bounds()
            buf = self.buf.get_text(start, end)

            try:
                out_f = open(self.filepath, 'w')
                out_f.write(buf)
                out_f.close()
                #self.statusMsg("%s saved." % self.filepath)
            except IOError, e:
                return common.view.popup_error("Cannot write '%s': %s" % (
                        self.filepath, str(e)))

            self.buf.set_modified(False)

    def save(self):
        def _save(res):
            if res != 'yes':
                return
            self._do_save()

        dirname, filename = os.path.split(self.filepath)
        common.view.popup_confirm("Save file", 
                                  'Really save "%s"?' % filename,
                                  _save)
        
    def build_dialog(self, title, text, func):
        dialog = gtk.MessageDialog(flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                                   type=gtk.MESSAGE_WARNING,
                                   message_format=text)
        dialog.set_title(title)
        dialog.connect("response", func)
        return dialog

    def close(self):
        if self.buf.get_modified():
            w = self.build_dialog("Close file",
                                  warning_close, self._close_check_res)
            w.add_button("Cancel", 1)
            w.add_button("Close", 2)
            w.add_button("Save and Close", 3)
            w.show()
            return False
        
        super(CodePage, self).close()
        return True

    def _close_check_res(self, w, rsp):
        w.destroy()
        if rsp == 2:
            super(CodePage, self).close()
            
        elif rsp == 3:
            self._do_save()
            super(CodePage, self).close()
            
        return True

    def get_filepath(self):
        return self.filepath

    def line_numbering(self, onoff):
        self.tw.set_show_line_numbers(onoff)
        
    def toggle_line_numbering(self, widget):
        self.line_numbering(widget.active)
        return True
        
    def line_wrapping(self, kind):
        d = { 'none': gtk.WRAP_NONE,
              'char': gtk.WRAP_CHAR,
              'word': gtk.WRAP_WORD,
              'full': gtk.WRAP_WORD_CHAR }
        self.tw.set_wrap_mode(d[kind])
        
    def toggle_line_wrapping(self, widget):
        if widget.active:
            self.line_wrapping('full')
        else:
            self.line_wrapping('none')
        return True

    ##### Printing callbacks
    
    def begin_print_cb(self, operation, context, compositor):
        while not compositor.paginate(context):
            pass
        n_pages = compositor.get_n_pages()
        operation.set_n_pages(n_pages)

    def draw_page_cb(self, operation, context, page_nr, compositor):
        compositor.draw_page(context, page_nr)

    def print_cb(self):
        sourceview = self.tw
        window = sourceview.get_toplevel()
        buffer = sourceview.get_buffer()

        compositor = gtksourceview2.print_compositor_new_from_view(sourceview)
        compositor.set_wrap_mode(gtk.WRAP_WORD_CHAR)
        compositor.set_highlight_syntax(True)
        #compositor.set_print_line_numbers(5)
        #compositor.set_header_format(False, 'Printed on %A', None, '%F')
        filename = self.get_filepath()
        compositor.set_footer_format(True, '%T %F', filename, 'Page %N/%Q')
        compositor.set_print_header(False)
        compositor.set_print_footer(True)

        print_op = gtk.PrintOperation()
        print_op.connect("begin-print", self.begin_print_cb, compositor)
        print_op.connect("draw-page", self.draw_page_cb, compositor)
        res = print_op.run(gtk.PRINT_OPERATION_ACTION_PRINT_DIALOG, window)

        if res == gtk.PRINT_OPERATION_RESULT_ERROR:
            #error_dialog(window, "Error printing file:\n\n" + filename)
            return common.view.popup_error("Error printing file '%s'" % (
                filename))
        elif res == gtk.PRINT_OPERATION_RESULT_APPLY:
            common.view.statusMsg('File printed: %s' % filename)

    ##### Find and Replace callbacks
    
    def _find(self, response):
        dialog = self.sr

        if response == 'close':
            common.clear_selection(self.tw)
            return True
        
        if response == 'replace':
            if not self.buf.get_has_selection():
                # No selection.
                dialog.set_message("NO SELECTION")
                return True
                
            try:
                start, end = self.buf.get_selection_bounds()
            except ValueError:
                dialog.set_message("ERROR SELECTION?")
                return True

            # TODO: how to force increments of undoable actions?
            self.buf.delete(start, end)
            self.buf.insert(start, dialog.get_replace_text())

            # Clear the selection
            common.clear_selection(self.tw)

            return True

        reverse = dialog.is_reverse_search()
        if dialog.is_case_sensitive():
            search_flags = gtksourceview2.SEARCH_CASE_INSENSITIVE
        else:
            search_flags = 0

        i = self.buf.get_iter_at_mark(self.searchmark)
        if i == None:
            dialog.set_message("PLEASE PLACE CURSOR")
            return
        dialog.set_message("Search begins in line %d" % (
            i.get_line()))

        if reverse:
            searched = i.backward_search(dialog.get_search_text(),
                                        search_flags, None)
        else:
            searched = i.forward_search(dialog.get_search_text(),
                                        search_flags, None)
        if searched:
            dialog.set_message("Found string")
            start, end = searched
            self.buf.select_range(start, end)
            self.scroll_to_lineno(start.get_line())
            if reverse:
                self.buf.move_mark(self.searchmark, start)
            else:
                self.buf.move_mark(self.searchmark, end)

        else:
            end = i
            if reverse:
                i = self.buf.get_end_iter()
                searched = i.backward_search(dialog.get_search_text(),
                                            search_flags, end)
            else:
                i = self.buf.get_start_iter()
                searched = i.forward_search(dialog.get_search_text(),
                                            search_flags, end)
            if searched:
                dialog.set_message("Found string")
                start, end = searched
                self.buf.select_range(start, end)
                self.scroll_to_lineno(start.get_line())
                if reverse:
                    self.buf.move_mark(self.searchmark, start)
                else:
                    self.buf.move_mark(self.searchmark, end)

            else:
                dialog.set_message("NO MORE INSTANCES FOUND")

    def find(self):
        loc = self.buf.get_iter_at_mark(self.buf.get_insert())
        if not loc:
            loc = self.buf.get_start_iter()
        self.buf.move_mark(self.searchmark, loc)

        self.sr.popup(self._find)

    def place_cursor_cb(self, buf, loc, mark):
        if mark == buf.get_insert():
            self.buf.move_mark(self.searchmark, loc)
        return False
            

#END

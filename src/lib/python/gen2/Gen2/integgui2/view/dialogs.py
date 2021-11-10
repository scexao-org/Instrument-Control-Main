# 
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Sat Apr 16 11:27:35 HST 2011
#]
import time
import threading

import gtk
import gobject
import pango

import common

dialog_count = 0

# This is a table of dialogs that have been opened by a remote task.
dialog_table = {}
# A lock to protect the table
dialog_table_lock = threading.RLock()

def register_dialog(tag, dialog):
    """Register a dialog in the dialog table."""
    if not tag:
        # dialog is not associated with a remote task
        return
    with dialog_table_lock:
        print "Registering dialog %s" % tag
        dialog_table[tag] = dialog

def unregister_dialog(tag):
    """Unregister a dialog from the dialog table."""
    if not tag:
        return
    with dialog_table_lock:
        print "Unregistering dialog %s" % tag
        try:
            del dialog_table[tag]
        except KeyError:
            # if already deleted no big deal
            pass

def cancel_dialog(tag):
    """Cancel any dialogs associated with a remote task.
    """
    with dialog_table_lock:
        items = dialog_table.items()

    # Search the dialog table for a tag that starts with this tag
    for key, obj in items:
        if key.startswith(tag):
            # Found one--it must be associated with that command
            print "Command cancelled--closing dialog %s" % key
            unregister_dialog(key)
            if obj.w:
                obj.close(obj.w)
    

# NOTE [1]:
#   There seems to be a bug in the gtk.FileChooserDialog() where if the
# directory contents are changing while the dialog is open it will sometimes
# crash the program.  For this reason I changed the class to create the
# widget each time it is needed and destroy it afterwards
#

class FileSelection(object):
    
    # Get the selected filename and print it to the console
    def file_ok_sel(self, w, rsp):
        filepath = w.get_filename()
        #print "(dialog) File is %s" % filepath
        self.close(w)
        if rsp == 0:
            return
        
        self.callfn(filepath)

    def __init__(self, action=gtk.FILE_CHOOSER_ACTION_OPEN):
        self.action = action

    def _create_widget(self, action):
        # Create a new file selection widget
        self.filew = gtk.FileChooserDialog(title="Select a file",
                                           action=action)
        # See NOTE [1]
        #self.filew.connect("destroy", self.close)
        if action == gtk.FILE_CHOOSER_ACTION_SAVE:
            self.filew.add_buttons(gtk.STOCK_SAVE, 1, gtk.STOCK_CANCEL, 0)
        else:
            self.filew.add_buttons(gtk.STOCK_OPEN, 1, gtk.STOCK_CANCEL, 0)
        self.filew.set_default_response(1)
        
        # Connect the ok_button to file_ok_sel method
        #self.filew.ok_button.connect("clicked", self.file_ok_sel)
        self.filew.connect("response", self.file_ok_sel)
    
        # Connect the cancel_button to destroy the widget
        #self.filew.cancel_button.connect("clicked", self.close)
    
    def popup(self, title, callfn, initialdir=None,
              filename=None):
        # See NOTE [1]
        self._create_widget(self.action)
        
        self.callfn = callfn
        self.filew.set_title(title)
        if initialdir:
            self.filew.set_current_folder(initialdir)

        if filename:
            #self.filew.set_filename(filename)
            self.filew.set_current_name(filename)

        self.filew.show()

    def close(self, widget):
        # See NOTE [1]
        #self.filew.hide()
        self.filew.destroy()
        self.filew = None


class MyDialog(gtk.Dialog):
    def __init__(self, title=None, flags=None, buttons=None,
                 callback=None):

        button_list = []
        for name, val in buttons:
            button_list.extend([name, val])

        super(MyDialog, self).__init__(title=title, flags=flags,
                                       buttons=tuple(button_list))
        #self.w.connect("close", self.close)
        if callback:
            self.connect("response", callback)
        

class SearchReplace(object):

    def __init__(self, title='Search and/or Replace'):
        self.title = title

        self.what = ''
        self.replacement = ''
        
    def _create_widget(self, buttons, callback):
        global dialog_count
        
        if not common.view.embed_dialogs:
            self.w = MyDialog(title=self.title,
                              flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                              buttons=buttons,
                              callback=callback)
        else:
            dialog_count += 1
            name = 'Dialog_%d' % dialog_count
            self.w = common.view.create_dialog(name, name)
            self.w.add_hook('close', lambda: common.view.lower_page_transient('dialogs'))
            common.view.raise_page_transient('dialogs')
            common.view.dialogs.select(name)
            self.w.add_buttons(buttons, callback)
            
        cvbox = self.w.get_content_area()
        self.cvbox = cvbox

        lbl = gtk.Label('Search string:')
        lbl.show()
        self.cvbox.pack_start(lbl, True, False, 0)
        self._search_widget = gtk.Entry()
        if self.what:
            self._search_widget.set_text(self.what)
        self._search_widget.set_activates_default(True)
        self._search_widget.show()
        self.cvbox.pack_start(self._search_widget, True, True, 0)

        lbl = gtk.Label('Replacement string:')
        lbl.show()
        self.cvbox.pack_start(lbl, True, False, 0)
        self._replace_widget = gtk.Entry()
        if self.replacement:
            self._replace_widget.set_text(self.replacement)
        self._replace_widget.set_activates_default(True)
        self._replace_widget.show()
        self.cvbox.pack_start(self._replace_widget, True, True, 0)

        self._case_sensitive = gtk.CheckButton("Case sensitive")
        self._case_sensitive.set_active(True)
        self._case_sensitive.set_sensitive(False)
        self._case_sensitive.show()
        self.cvbox.pack_start(self._case_sensitive, False, False, 0)

        self._reverse = gtk.CheckButton("Reverse")
        self._reverse.show()
        self.cvbox.pack_start(self._reverse, False, False, 0)

        self._message = gtk.Label('')
        self._message.show()
        self.cvbox.pack_start(self._message, True, True, 0)
        
    def popup(self, callfn):
        button_list = [['Close', 0], ['Replace', 1], ['Find', 2], ]
        button_vals = ['close', 'replace', 'find']

        def callback(w, rsp):
            if rsp < 0:
                val = 'close'
            else:
                val = button_list[rsp][0].lower()
                #print "rsp=%d val=%s" % (rsp, val)

            if val == 'close':
                self.close(w)
                
            return callfn(val)
            
        self._create_widget(tuple(button_list), callback)
        self.set_message("Search begins at cursor")
        
        self.w.show()

    def is_case_sensitive(self):
        return self._case_sensitive.get_active()

    def is_reverse_search(self):
        return self._reverse.get_active()

    def get_search_text(self):
        self.what = self._search_widget.get_text()
        return self.what

    def get_replace_text(self):
        self.replacement = self._replace_widget.get_text()
        return self.replacement

    def set_message(self, text):
        self._message.set_text(text)

    def close(self, widget):
        #self.w.hide()
        widget.destroy()
        self.w = None


class Confirmation(object):

    def __init__(self, title='OBS Confirmation',
                 logger=None, soundfn=None, timefreq=5):
        self.title = title
        self.logger = logger
        
        self.soundfn = soundfn
        self.timertask = None
        self.interval = timefreq * 1000
        
    def _create_widget(self, title, iconfile, buttons, callback):
        global dialog_count
        
        if not common.view.embed_dialogs:
            ## self.w = gtk.Dialog(title=self.title,
            ##                     flags=gtk.DIALOG_DESTROY_WITH_PARENT,
            ##                     buttons=buttons)
            ## #self.w.connect("close", self.close)
            ## self.w.connect("response", callback)
            self.w = MyDialog(title=self.title,
                              flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                              buttons=buttons,
                              callback=callback)
        else:
            dialog_count += 1
            name = 'Dialog_%d' % dialog_count
            self.w = common.view.create_dialog(name, name)
            self.w.add_hook('close', lambda: common.view.lower_page_transient('dialogs'))
            common.view.raise_page_transient('dialogs')
            common.view.dialogs.select(name)
            self.w.add_buttons(buttons, callback)
            
        cvbox = self.w.get_content_area()
        self.cvbox = cvbox
        tw = gtk.TextView()
        # TODO: parameterize this
        pangoFont = pango.FontDescription("Sans Bold 14")
        tw.modify_font(pangoFont)
        tw.set_editable(False)
        tw.set_cursor_visible(False)
        tw.set_size_request(425, -1)
        tw.set_wrap_mode(gtk.WRAP_WORD_CHAR)
        tw.set_left_margin(4)
        tw.set_right_margin(4)
        txtbuf = tw.get_buffer()
        enditer = txtbuf.get_end_iter()
        txtbuf.insert(enditer, title)
        self.tw = tw
        tw.show()

        self.icon = gtk.Image()
        self.icon.set_from_file(iconfile)
        cvbox.pack_start(self.icon, expand=False, padding=2)
        cvbox.pack_start(tw, expand=False, padding=5)

        self.anim = gtk.gdk.PixbufAnimation(iconfile)
        self.icon.set_from_animation(self.anim)
        self.icon.show_all()
        
    def popup(self, title, iconfile, soundfn, buttons, callfn, tag=None):
        button_list = []
        button_vals = []
        i = 0
        for name, val in buttons:
            button_list.append([name, i])
            button_vals.append(val)
            i += 1

        def callback(w, rsp):
            self.close(w)
            if rsp < 0:
                val = None
            else:
                val = rsp

            unregister_dialog(self.tag)
            return callfn(val, button_vals)
            
        self._create_widget(title, iconfile, tuple(button_list),
                            callback)
        self.tag = tag
        register_dialog(tag, self)
        
        self.w.show()
        #self.timeraction(soundfn)
        self.timertask = gobject.timeout_add(self.interval,
                                             self.timeraction,
                                             soundfn)

    def close(self, widget):
        #self.w.hide()
        widget.destroy()
        self.w = None
        if self.timertask:
            gobject.source_remove(self.timertask)
        self.timertask = None

    def timeraction(self, soundfn):
        if self.w:
            if soundfn != None:
                # play sound
                soundfn()
            
                # Schedule next sound event
                self.timertask = gobject.timeout_add(self.interval,
                                                     self.timeraction,
                                                     soundfn)
        else:
            self.timertask = None

      
class UserInput(Confirmation):

    def __init__(self, title='OBS UserInput', logger=None, soundfn=None):
        super(UserInput, self).__init__(title=title, logger=logger,
                                        soundfn=soundfn)
        
    def popup(self, title, iconfile, soundfn, itemlist, callfn, tag=None):
        button_vals = [1, 0]
        # NOTE: numbers here are INDEXES into self.button_vals, not values!
        button_list = [['OK', 0], ['Cancel', 1]]
            
        resDict = {}

        def callback(w, rsp):
            if rsp < 0:
                val = None
            else:
                val = rsp

            # Read out the entry widgets before we close the dialog
            d = {}
            for key, ent in resDict.items():
                s = ent.get_text()
                d[key] = s

            unregister_dialog(self.tag)
            self.close(w)
            return callfn(val, button_vals, d)
            
        self._create_widget(title, iconfile, tuple(button_list),
                            callback)

        tbl = gtk.Table(rows=len(itemlist), columns=2)
        tbl.set_row_spacings(2)
        tbl.set_col_spacings(2)

        row = 0
        for name, val in itemlist:
            lbl = gtk.Label(name)
            lbl.set_alignment(1.0, 0.5)
            ent = gtk.Entry()
            val_s = str(val)
            ent.set_text(val_s)
            resDict[name] = ent

            tbl.attach(lbl, 0, 1, row, row+1, xoptions=gtk.FILL)
            tbl.attach(ent, 1, 2, row, row+1, xoptions=gtk.EXPAND|gtk.FILL)
            row += 1

        tbl.show_all()
        self.cvbox.pack_start(tbl, fill=True, expand=False, padding=2)
        
        self.tag = tag
        register_dialog(tag, self)

        self.w.show()
        #self.timeraction(soundfn)
        self.timertask = gobject.timeout_add(self.interval,
                                             self.timeraction,
                                             soundfn)


class Timer(Confirmation):

    def __init__(self, title='OBS Timer', logger=None, soundfn=None):
        super(Timer, self).__init__(title=title, logger=logger,
                                    soundfn=soundfn)
        # override time interval to 1 sec
        self.interval = 1000

        self.fmtstr = '<span size="120000" weight="bold">%s</span>'
        
        # rgb triplets we use
        self.green = gtk.gdk.Color(0.0, 0.5, 0.0)
        self.white = gtk.gdk.Color(1.0, 1.0, 1.0)

    def redraw(self):
        s = self.timestr.rjust(5)
        self.area.set_markup(self.fmtstr % (s))

    def popup(self, title, iconfile, soundfn, time_sec, callfn, tag=None):
        button_vals = [0]
        # NOTE: numbers here are INDEXES into self.button_vals, not values!
        button_list = [['Close', 0]]
            
        def callback(w, rsp):
            self.close(w)
            if rsp < 0:
                val = None
            else:
                val = rsp

            unregister_dialog(self.tag)
            return callfn(val, button_vals)
            
        self._create_widget(title, iconfile, tuple(button_list),
                            callback)

        val = float(time_sec)
        self.duration = val
        self.timestr = str(int(val)).rjust(5)
        self.timer_val = time.time() + val
        
        self.area = gtk.Label()
        self.area.modify_bg(gtk.STATE_NORMAL, self.white)
        self.area.modify_fg(gtk.STATE_NORMAL, self.green)
        self.area.show()

        self.pbar = gtk.ProgressBar()
        self.pbar.show()
        self.pbar.set_orientation(gtk.PROGRESS_LEFT_TO_RIGHT)
        self.pbar.set_fraction(0.0)
        self.pbar.set_text("0%")
        self.cvbox.pack_start(self.area, fill=True, expand=False, padding=2)
        self.cvbox.pack_start(self.pbar, fill=True, expand=False, padding=2)

        self.tag = tag
        register_dialog(tag, self)

        self.w.show()
        self.redraw()

        self.timertask = gobject.timeout_add(1000, self.timeraction,
                                             soundfn)

    def timeraction(self, soundfn):
        diff = self.timer_val - time.time()
        diff = max(0, int(round(diff)))
        #self.logger.debug("timer: %d sec" % diff)
        self.timestr = str(diff).rjust(5)
        if self.w:
            self.redraw()
        if diff > 0:
            frac = 1.0 - diff/self.duration
            self.pbar.set_fraction(frac)
            self.pbar.set_text("%d%%" % int(frac*100))
            self.timertask = gobject.timeout_add(1000, self.timeraction,
                                                 soundfn)
        else:
            self.timertask = None
            self.pbar.set_fraction(1.0)
            self.pbar.set_text("100%")
            self.timerstr = '0'
            self.redraw()

            # Play sound
            soundfn()
        
            self.close(self.w)
            
class ComboBox(Confirmation):

    def __init__(self, title='OBS ComboBox', logger=None, soundfn=None):
        super(ComboBox, self).__init__(title=title, logger=logger,
                                        soundfn=soundfn)
        self.selectedValue = None

    def popup(self, title, iconfile, soundfn, itemlist, callfn, tag=None):
        button_vals = [1, 0]
        # NOTE: numbers here are INDEXES into self.button_vals, not values!
        button_list = [['OK', 0], ['Cancel', 1]]

        def callback(w, rsp):
            if rsp < 0:
                val = None
            else:
                val = rsp

            d = {'selected': self.selectedValue}

            unregister_dialog(self.tag)
            self.close(w)
            return callfn(val, button_vals, d)

        self._create_widget(title, iconfile, tuple(button_list),
                            callback)

        combobox = gtk.combo_box_new_text()

        for item in itemlist:
            combobox.append_text(item)
        combobox.connect('changed', self.changed_cb)
        combobox.set_active(0)
        self.selectedValue = itemlist[0]
        if len(itemlist) > 20:
            combobox.set_wrap_width(int(len(itemlist)/20))

        combobox.show()
        self.cvbox.pack_start(combobox, fill=True, expand=False, padding=2)

        self.tag = tag
        register_dialog(tag, self)

        self.w.show()
        #self.timeraction(soundfn)
        self.timertask = gobject.timeout_add(self.interval,
                                             self.timeraction,
                                             soundfn)

    def changed_cb(self, combobox):
        model = combobox.get_model()
        index = combobox.get_active()
        if index:
            self.selectedValue = model[index][0]
        return

#END

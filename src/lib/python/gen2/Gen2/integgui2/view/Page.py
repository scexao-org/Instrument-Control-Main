#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Mar  7 12:21:01 HST 2011
#]
#
import os
import threading

import gtk

import Bunch
import common

# constants
LEFT  = 'left'
RIGHT = 'right'


class Page(object):

    def __init__(self, frame, name, title):

        #super(Page, self).__init__()
        
        self.frame = frame
        self.name = name
        self.title = title

        self.closed = False

        # every page has a lock
        self.lock = threading.RLock()

        self.hooks = Bunch.Bunch(close=[])

    def close(self):
        for bnch in self.hooks.close:
            bnch.cbfn(*bnch.args, **bnch.kwdargs)

        # parent attribute is assigned by parent
        self.parent.delpage(self.name)

        self.closed = True

    def setLabel(self, name):
        # tablbl attribute is added by parent workspace
        # NOTE: this doesn't really change the name of the page, as known
        # by the parent, just the appearance of the tab
        self.tablbl.set_label(name)

    def add_hook(self, name, cbfn, args=None, kwdargs=None):
        if args is None:
            args = []
        if kwdargs is None:
            kwdargs = {}
        self.hooks[name].append(Bunch.Bunch(cbfn=cbfn, args=args,
                                            kwdargs=kwdargs))


class ButtonPage(Page):

    def __init__(self, frame, name, title):
        Page.__init__(self, frame, name, title)
        #super(ButtonPage, self).__init__(frame, name, title)

        self.add_menubar()
        
        # bottom buttons
        self.btnframe = gtk.HBox()
        
        btns = gtk.HButtonBox()
        btns.set_layout(gtk.BUTTONBOX_START)
        btns.set_spacing(5)
        self.leftbtns = btns

        self.btnframe.pack_start(self.leftbtns, fill=False, expand=False,
                                 padding=4)
        btns.show()

        btns = gtk.HButtonBox()
        btns.set_layout(gtk.BUTTONBOX_START)
        btns.set_spacing(5)
        self.rightbtns = btns
        
        self.btnframe.pack_end(self.rightbtns, fill=False, expand=False,
                               padding=4)
        btns.show()

        frame.pack_end(self.btnframe, fill=True, expand=False, padding=2)
        self.btnframe.show()

    def _get_side(self, side):
        if side == LEFT:
            return self.leftbtns
        elif side == RIGHT:
            return self.rightbtns
        return None
    
    def add_close(self, side=RIGHT):
        self.btn_close = gtk.Button("Close")
        self.btn_close.connect("clicked", lambda w: self.close())
        self.btn_close.show()
        w = self._get_side(side)
        w.pack_end(self.btn_close, padding=4)

    def add_menubar(self):
        self.menubar = gtk.MenuBar()
        self._menus = {}
        self.frame.pack_start(self.menubar, fill=True, expand=False, padding=0)
        self.menubar.show()
        return self.menubar

    def add_pulldownmenu(self, name):
        if not self.menubar:
            self.add_menubar()
        try:
            # Look for existing menu with this name
            menu = self._menus[name]
            return menu
        except KeyError:
            pass
        # No such menu, so go ahead and create it
        menu = gtk.Menu()
        self._menus[name] = menu
        menu.show()
        item = gtk.MenuItem(label=name)
        self.menubar.append(item)
        item.show()
        item.set_submenu(menu)
        return menu

    def add_menu(self, side=RIGHT):
        self.btn_menu = gtk.Button("Menu")
        self.menu = gtk.Menu()
        self.btn_menu.connect_object("event", self.popup_menu, self.menu)
        self.btn_menu.show()
        w = self._get_side(side)
        w.pack_end(self.btn_menu, padding=4)

    def popup_menu(self, w, event):
        if event.type == gtk.gdk.BUTTON_PRESS:
            self.menu.popup(None, None, None, event.button, event.time)
            return True
        return False
        

class CommandPage(ButtonPage):
    """Mixin class adding methods for kill, cancel, pause, etc.
    """

    def __init__(self, frame, name, title):
        self.paused = False
        # *** subclass should define self.tm_queueName ***

        ButtonPage.__init__(self, frame, name, title)
        #super(CommandPage, self).__init__(frame, name, title)
        
    def cancel(self):
        #controller = self.parent.get_controller()
        controller = common.controller
        controller.tm_cancel(self.tm_queueName)
        self.reset_pause()

    def pause(self):
        self.btn_pause.set_label("Resume")
        self.paused = True
        #controller = self.parent.get_controller()
        controller = common.controller
        controller.tm_pause(self.tm_queueName)

    def resume(self):
        self.reset_pause()
        #controller = self.parent.get_controller()
        controller = common.controller
        controller.tm_resume(self.tm_queueName)

    def toggle_pause(self, w):
        print "toggle pause!"
        common.controller.playSound(common.sound.pause_toggle)
        if self.paused:
            self.resume()
        else:
            self.pause()

        return True

    def reset_pause(self):
        self.btn_pause.set_label("Pause")
        self.paused = False

    def reset(self):
        self.reset_pause()


class TextPage(Page):
    """Mixin class adding methods for text manipulation.
    """

    ## def __init__(self, frame, name, title):
    ##     super(TextPage, self).__init__(frame, name, title)
        
    def save(self, dirpath=None, filename=None):
        # If we have a filepath associated with this buffer, try to
        # use it, otherwise revert to a save_as()
        if hasattr(self, 'filepath') and self.filepath:
            return self._savefile(self.filepath)

        return self.save_as(self, dirpath=dirpath,
                            filename=filename)


    def _get_save_directory(self):
        if hasattr(self, 'filepath') and self.filepath:
            # Use directory of current file, if one exists
            dirpath, xx = os.path.split(self.filepath)
        else:
            # default directory for saving, if none provided
            dirpath = os.path.join(os.environ['HOME'], 'Procedure')

        return dirpath
    
    def save_as(self, dirpath=None, filename=None):
        def _save(filepath):
            self.filepath = filepath
            return self._savefile(filepath)

        if not dirpath:
            dirpath = self._get_save_directory()
            
        common.view.popup_save("Save buffer as", _save,
                               dirpath, filename=filename)

    def save_selection_as(self, dirpath=None, filename=None):
        try:
            first, last = self.buf.get_selection_bounds()
        except ValueError:
            return common.view.popup_error("Please make a selection first!")
        
        def _save(filepath):
            return self._savefile(filepath, (first, last))

        if not dirpath:
            dirpath = self._get_save_directory()

        common.view.popup_save("Save selection as", _save,
                               dirpath, filename=filename)

    def _savefile(self, filepath, iterbounds=None):
        """Save buffer to (filepath).  If the file exists, confirm whether
        to overwrite it.
        """
        def _save(res):
            if res != 'yes':
                return

            # get text to save
            if iterbounds:
                start, end = iterbounds
            else:
                start, end = self.buf.get_bounds()

            buf = self.buf.get_text(start, end)

            try:
                out_f = open(filepath, 'w')
                out_f.write(buf)
                out_f.close()
                #self.statusMsg("%s saved." % self.filepath)
            except IOError, e:
                return common.view.popup_error("Cannot write '%s': %s" % (
                        filepath, str(e)))

        if os.path.exists(filepath):
            common.view.popup_confirm("Confirm overwrite",
                                      "File '%s' exists.\nOK to Overwrite ?" % (
                filepath), _save)
        else:
            _save('yes')

    def select_all(self):
        start, end = self.buf.get_bounds()
        self.buf.select_range(start, end)

    def select_clear(self):
        common.clear_selection(self.tw)

    def get_end_lineno(self):
        loc = self.buf.get_end_iter()
        return loc.get_line()

    def scroll_to_lineno(self, lineno):
        loc = self.buf.get_start_iter()
        loc.set_line(lineno)
        self.buf.move_mark(self.mark, loc)
        #res = self.tw.scroll_to_iter(loc, 0.5)
        #res = self.tw.scroll_to_mark(self.mark, 0.2)
        res = self.tw.scroll_to_mark(self.mark, 0.2, True)
        if not res:
            res = self.tw.scroll_mark_onscreen(self.mark)
        #print "line->%d res=%s" % (lineno, res)

    def scroll_to_end(self):
        lineno = self.get_end_lineno()
        self.scroll_to_lineno(lineno)
        
    def focus_in(self, *args):
        print args
        self.tw.grab_focus()
        return True
    
#END

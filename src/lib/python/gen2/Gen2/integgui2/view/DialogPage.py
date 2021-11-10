#
# DialogPage.py -- implements an Integgui2 dialog
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Apr 15 16:33:43 HST 2011
#]

import gtk
import common
import Page

import Bunch
        
class DialogError(Exception):
    pass

class DialogPage(Page.Page):

    def __init__(self, frame, name, title):

        super(DialogPage, self).__init__(frame, name, title)

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_border_width(2)

        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,
                                   gtk.POLICY_AUTOMATIC)

        vbox = gtk.VBox()
        scrolled_window.add(vbox)
        vbox.show()
        scrolled_window.show()

        frame.pack_start(scrolled_window, expand=True, fill=True)

        self.cvbox = gtk.VBox()
        vbox.pack_start(self.cvbox, expand=False, fill=True)
        self.cvbox.show()
        
        separator = gtk.HSeparator()
        separator.show()
        vbox.pack_start(separator, expand=False, fill=True)

        # bottom buttons
        btns = gtk.HButtonBox()
        btns.set_layout(gtk.BUTTONBOX_START)
        btns.set_spacing(5)
        self.leftbtns = btns

        vbox.pack_start(self.leftbtns, fill=True, expand=False,
                        padding=4)
        btns.show()

    def get_content_area(self):
        return self.cvbox

    def add_button(self, name, rsp, callback):
        def _callback(w):
            return callback(self, rsp)
        btn = gtk.Button(name)
        btn.connect("clicked", _callback)
        btn.show()
        self.leftbtns.pack_start(btn)

    def add_buttons(self, buttonlist, callback):
        for name, rsp in buttonlist:
            self.add_button(name, rsp, callback)
            
    def destroy(self):
        # this method is here to make it similar to a widget based class
        return self.close()

    def show(self):
        pass
        
#END

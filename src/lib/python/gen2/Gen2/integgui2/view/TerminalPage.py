# 
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Tue Sep 28 14:19:45 HST 2010
#]

import gtk
import vte

import common
import Page


class TerminalPage(Page.ButtonPage):

    def __init__(self, frame, name, title):

        super(TerminalPage, self).__init__(frame, name, title)

        tw = vte.Terminal()
        #tw.set_color_foreground(common.terminal_colors.fg)
        #tw.set_color_background(common.terminal_colors.bg)
        
        tw.connect("child-exited", lambda w: self.close())
        tw.fork_command()
        self.tw = tw

        tw.show()
        frame.pack_start(tw, expand=True, fill=True)

        #self.add_close()
        # Add items to the menu
        menu = self.add_pulldownmenu("Page")

        item = gtk.MenuItem(label="Close")
        menu.append(item)
        item.connect_object ("activate", lambda w: self.close(),
                             "menu.Close")
        item.show()

        

#END

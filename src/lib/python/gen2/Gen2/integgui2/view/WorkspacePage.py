# 
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Sat Oct  9 20:29:07 HST 2010
#]

import gtk

import Workspace
import Page


class WorkspacePage(Workspace.Workspace, Page.Page):

    def __init__(self, frame, name, title):
        Page.Page.__init__(self, frame, name, title)
        Workspace.Workspace.__init__(self, frame, name, title)

        #self.nb.set_tab_pos(gtk.POS_LEFT)
        
class ButtonWorkspacePage(Workspace.Workspace, Page.ButtonPage):

    def __init__(self, frame, name, title):
        Page.ButtonPage.__init__(self, frame, name, title)
        Workspace.Workspace.__init__(self, frame, name, title)

#END

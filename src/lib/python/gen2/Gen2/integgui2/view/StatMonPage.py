# 
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Tue Aug 23 13:38:41 HST 2011
#]

import gtk
import Bunch

import common
import Page

class StatMonPage(Page.ButtonPage):

    def __init__(self, frame, name, title):

        super(StatMonPage, self).__init__(frame, name, title)

        #self.frame = frame
        self.params = Bunch.Bunch()
        self.paramList = []
        self.row = 1
        self.col = 1
        self.max_col = self.col
        self.def_width = 20
        self.cursor = None

        # Create the widgets for the text
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_border_width(2)

        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,
                                   gtk.POLICY_AUTOMATIC)
        frame.pack_start(scrolled_window, expand=True, fill=True)

        self.fw = gtk.VBox()
        scrolled_window.add_with_viewport(self.fw)

        self.table = gtk.Table(rows=2, columns=2)
        self.table.set_name('statmon')
        self.table.show()

        self.fw.pack_start(self.table, expand=True, fill=True)

        hbox = gtk.HBox(spacing=4)

        self.lblent = gtk.Entry()
        self.alsent = gtk.Entry()
        btn1 = gtk.Button("Add Alias")
        btn1.connect('clicked', lambda w: self.add_item())
        btn2 = gtk.Button("New Row")
        btn2.connect('clicked', lambda w: self.add_break())
        btn3 = gtk.Button("Update")
        btn3.connect('clicked', lambda w: self.update())

        for w in (btn3, btn2, btn1,
                  self.alsent, gtk.Label("Status Alias:"),
                  self.lblent, gtk.Label("Label:")):
            hbox.pack_end(w, fill=False, expand=False)

        self.fw.pack_end(hbox, expand=False, fill=True)

        self._mark_cursor()
        scrolled_window.show_all()
        

    def addParam(self, name):
        self.paramList.append(name)

    def add_break(self):
        self.table.remove(self.cursor)
        self.row += 2
        self.col = 1
        self.table.resize(self.row+1, self.max_col+1)
        self._mark_cursor()
        return True

    def bump_col(self):
        self.col += 1
        self.max_col = max(self.col, self.max_col)
        self.table.resize(self.row+1, self.max_col+1)

    def add_status(self, name, width, alias, label):
        
        lbl = gtk.Label(label)
        lbl.show()
        self.table.attach(lbl, self.col, self.col+1, self.row-1, self.row,
                          xoptions=gtk.FILL, yoptions=gtk.FILL,
                          xpadding=1, ypadding=1)
        field = gtk.Entry()
        field.set_width_chars(width)
        field.set_text(alias)
        field.show()
        self.table.attach(field, self.col, self.col+1, self.row, self.row+1,
                          xoptions=gtk.FILL, yoptions=gtk.FILL,
                          xpadding=1, ypadding=1)
        self.bump_col()

        name = name.lower()
        self.params[name] = Bunch.Bunch(widget=field, alias=alias,
                                        type='field')
        self.addParam(name)

    def get_params(self):
        return self.params

    def _mark_cursor(self):
        self.cursor = gtk.Label("<Next Here>")
        self.cursor.show()
        self.table.attach(self.cursor, self.col, self.col+1, self.row-1, self.row,
                          xoptions=gtk.FILL, yoptions=gtk.FILL,
                          xpadding=1, ypadding=1)

    def add_item(self):
        label = self.lblent.get_text()
        name = label.lower()
        alias = self.alsent.get_text()

        self.table.remove(self.cursor)
        self.add_status(name, self.def_width, alias, label)
        self._mark_cursor()

        return True
        
    def update(self, statusDict):
        for bnch in self.params.values():
            bnch.widget.set_text(str(statusDict[bnch.alias]))
        
    def update_controller(self):
        fetchDict = {}
        for bnch in self.params.values():
            fetchDict[bnch.alias] = None

        common.controller.add_statusdict(fetchDict, self.update)
    
#END

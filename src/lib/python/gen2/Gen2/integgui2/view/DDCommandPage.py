# 
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Sat Sep 25 12:36:37 HST 2010
#]

import gtk

import common
import Page
import CommandObject

class DDCommandPage(Page.CommandPage):

    def __init__(self, frame, name, title):

        super(DDCommandPage, self).__init__(frame, name, title)

        self.queueName = 'default'
        self.tm_queueName = 'executer'

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_border_width(2)

        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,
                                   gtk.POLICY_AUTOMATIC)

        tw = gtk.TextView()
        tw.set_editable(True)
        tw.set_wrap_mode(gtk.WRAP_WORD)
        tw.set_left_margin(4)
        tw.set_right_margin(4)
        scrolled_window.add(tw)
        tw.show()
        scrolled_window.show()

        frame.pack_start(scrolled_window, expand=True, fill=True)

        self.tw = tw
        self.buf = tw.get_buffer()

        ## self.add_menu()
        ## self.add_close()
        
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
        menu = self.add_pulldownmenu("Page")

        item = gtk.MenuItem(label="Clear text")
        menu.append(item)
        item.connect_object ("activate", lambda w: self.clear_text(),
                             "menu.Clear")
        item.show()

        item = gtk.MenuItem(label="Close")
        menu.append(item)
        item.connect_object ("activate", lambda w: self.close(),
                             "menu.Close")
        item.show()

        menu = self.add_pulldownmenu("Command")

        item = gtk.MenuItem(label="Exec as launcher")
        menu.append(item)
        item.connect_object ("activate", lambda w: self.execute_as_launcher(),
                             "menu.Execute_as_launcher")
        item.show()

        menu = self.add_pulldownmenu("Queue")

        item = gtk.MenuItem(label="Clear All")
        menu.append(item)
        item.connect_object ("activate", lambda w: common.controller.clearQueue(self.queueName),
                             "menu.Clear_All")
        item.show()

        item = gtk.MenuItem(label="Attach to ...")
        menu.append(item)
        item.connect_object ("activate", lambda w: self.attach_queue(),
                             "menu.Attach_to")
        item.show()

    def clear_text(self):
        start, end = self.buf.get_bounds()
        self.buf.delete(start, end)
        
    def set_text(self, text):
        self.clear_text()
        itr = self.buf.get_end_iter()
        self.buf.insert(itr, text)
        itr = self.buf.get_end_iter()
        self.buf.place_cursor(itr)         

    # TODO: this is code share with OpePage.  Should be shared.
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
        
    def get_dd_command(self):
        # Clear the selection
        itr = self.buf.get_end_iter()
        self.buf.place_cursor(itr)         

        # Get the entire buffer from the page's text widget
        start, end = self.buf.get_bounds()
        txtbuf = self.buf.get_text(start, end).strip()

        # remove trailing semicolon, if present
        cmdstr = txtbuf
        if cmdstr.endswith(';'):
            cmdstr = cmdstr[:-1]

        if len(cmdstr) == 0:
            raise Exception("No text in command buffer!")
            
        # tag the text so we can manipulate it later
        cmdObj = DDCommandObject('dd%d', self.queueName,
                                 self.logger, self, cmdstr)
        return cmdObj

    def execute(self):
        """Callback when the 'Exec' button is pressed.
        """
        # Check whether we are busy executing a command here
        if common.controller.executingP.isSet():
            # Yep--popup an error message
            common.view.popup_error("There is already a %s task running!" % (
                self.tm_queueName))
            return

        try:
            cmdObj = self.get_dd_command()

            common.controller.execOne(cmdObj, self.tm_queueName)
        except Exception, e:
            common.view.popup_error(str(e))

    def execute_as_launcher(self):
        """Callback when the 'Exec as launcher' menu item is invoked.
        """
        try:
            cmdObj = self.get_dd_command()
            common.controller.execOne(cmdObj, 'launcher')

        except Exception, e:
            common.view.popup_error(str(e))

    def insert(self, loc=None, queueName='default'):
        """Callback when the Append button is pressed.
        """
        try:
            cmdObj = self.get_dd_command()

            queue = common.controller.queue[self.queueName]
            if loc == None:
                queue.append(cmdObj)
            else:
                queue.insert(loc, [cmdObj])

        except Exception, e:
            common.view.popup_error(str(e))


class DDCommandObject(CommandObject.CommandObject):

    def __init__(self, format, queueName, logger, page, cmdstr):
        self.page = page
        self.cmdstr = cmdstr

        super(DDCommandObject, self).__init__(format, queueName, logger)
        
    def get_preview(self):
        return self.get_cmdstr()
    
    def get_cmdstr(self):
        return self.cmdstr

    def mark_status(self, txttag):
        pass

#END

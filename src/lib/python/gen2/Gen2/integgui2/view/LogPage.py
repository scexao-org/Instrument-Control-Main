# 
# Eric Jeschke (eric@naoj.org)
#
import time
import threading

import gtk
import gobject
import os.path
## import subprocess

import common
import Page


class NotePage(Page.ButtonPage, Page.TextPage):

    def __init__(self, frame, name, title):
        super(NotePage, self).__init__(frame, name, title)

        # How many lines should we keep in this buffer beyond which
        # we cull from the top.  A value of 0 disables auto-culling.
        self.logsize = 0

        # Whether to automatically scroll the text widget when data
        # is appended to the bottom of the buffer programatically.
        self.autoscroll = True

        self.lock = threading.RLock()

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_border_width(2)

        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,
                                   gtk.POLICY_AUTOMATIC)

        tw = gtk.TextView()
        scrolled_window.add(tw)
        tw.show()
        scrolled_window.show()

        frame.pack_start(scrolled_window, expand=True, fill=True)

        tw.set_editable(False)
        tw.set_wrap_mode(gtk.WRAP_NONE)
        tw.set_left_margin(4)
        tw.set_right_margin(4)

        self.tw = tw
        self.buf = tw.get_buffer()
        # hack to get auto-scrolling to work
        self.mark = self.buf.create_mark('end', self.buf.get_end_iter(),
                                         False)

        #self.add_close()
        menu = self.add_pulldownmenu("Page")

        item = gtk.MenuItem(label="Save as ...")
        menu.append(item)
        item.connect_object ("activate", lambda w: self.save_log_as(),
                             "menu.Save_as")
        item.show()
        
        item = gtk.MenuItem(label="Save selection as ...")
        menu.append(item)
        item.connect_object ("activate", lambda w: self.save_log_selection_as(),
                             "menu.Save_selection_as")
        item.show()
        
        #self.add_close()
        item = gtk.MenuItem(label="Close")
        menu.append(item)
        item.connect_object ("activate", lambda w: self.close(),
                             "menu.Close")
        self.menu_close = item
        item.show()


    def set_editable(self, value):
        self.tw.set_editable(value)
        
    def set_logsize(self, size):
        """(size) should be an integer value indicating number of
        lines.  Setting to 0 will disable any culling of old lines.
        """
        self.logsize = size

    def set_autoscroll(self, onoff):
        self.autoscroll = onoff

    def addtag(self, name, **properties):
        try:
            self.buf.create_tag(name, **properties)
        except:
            # tag may already exist--that's ok
            pass

    def clear(self):
        start, end = self.buf.get_bounds()
        self.buf.delete(start, end)
        
    def _cull(self):
        if self.logsize:
            end = self.buf.get_end_iter()
            excess_lines = end.get_line() - self.logsize
            if excess_lines > 0:
                bitr1 = self.buf.get_start_iter()
                bitr2 = bitr1.copy()
                bitr2.set_line(excess_lines)
                self.buf.delete(bitr1, bitr2)

    def append(self, data, tags):
        end = self.buf.get_end_iter()
        if not tags:
            tags = ['normal']
            
        try:
            self.buf.insert_with_tags_by_name(end, data, *tags)

        except Exception, e:
            tags = ['error']
            data = "--DATA COULD NOT BE INSERTED--: %s" % (str(e))
            self.buf.insert_with_tags_by_name(end, data, *tags)

        # Remove some old log lines if necessary
        self._cull()

        # Auto scroll to end of buffer
        if self.autoscroll:
            self.scroll_to_end()

    def save_log_as(self):
        homedir = os.path.join(os.environ['HOME'], 'Procedure')
        filename = time.strftime("%Y%m%d-%H:%M:%S") + (
            '-%s.txt' % self.name)

        common.view.popup_save("Save buffer", self._savefile,
                               homedir, filename=filename)

    def save_log_selection_as(self):
        homedir = os.path.join(os.environ['HOME'], 'Procedure')
        filename = time.strftime("%Y%m%d-%H:%M:%S") + (
            '-%s.txt' % self.name)
        return self.save_selection_as(homedir, filename)


class LogPage(NotePage):

    def __init__(self, frame, name, title):
        super(LogPage, self).__init__(frame, name, title)

        # interval between checking for log file updates (ms)
        self.poll_interval = 500

        self.set_logsize(5000)

        # add standard decorative tags
        for tag, bnch in common.log_tags:
            properties = {}
            properties.update(bnch)
            self.addtag(tag, **properties)

        # This is a table of regex, tag tuples used to do
        # auto coloring of log entries
        self.regexes = []


    def clear_regexes(self):
        self.regexes = []
        
    def add_regex(self, regex, tags):
        self.regexes.append((regex, tags))
        
    def add_regexes(self, tuples):
        for tup in tuples:
            self.add_regex(*tup)
        
    def load(self, filepath):
        self.filepath = filepath
        self.file = open(self.filepath, 'r')
        # Go to the end of the file
        if self.logsize:
            try:
                self.file.seek(- self.logsize, 2)
            except:
                pass
            self.size = self.file.tell()
        else:
            self.size = 0
        self.poll()

    def close(self):
        try:
            self.file.close()
        except:
            pass

        super(LogPage, self).close()

    def push(self, msgstr):
        line = msgstr + '\n'
        
        # set tags according to content of message
        for (regex, tags) in self.regexes:
            if regex.match(msgstr):
                self.append(line, tags)
                return

        self.append(line, [])


    def poll(self):
        if self.closed:
            return

        #self.tw.scroll_mark_onscreen(self.mark)

        #if os.path.getsize(self.filepath) > self.size:
        try:
            data = self.file.read()
            self.size = self.size + len(data)

            if len(data) > 0:
                with self.lock:
                    for line in data.split('\n'):
                        self.push(line)
                    
        except IOError, e:
            pass
            
        gobject.timeout_add(self.poll_interval, self.poll)


## class TailPage(LogPage):

##     def __init__(self, frame, name, title):
##         super(TailPage, self).__init__(frame, name, title)

##         # interval between checking for log file updates (ms)
##         self.poll_interval = 500
##         self.proc = None

##     def load(self, svcname):
##         self.filepath = 'g2log(%s)' % svcname
##         try:
##             self.proc = subprocess.Popen(['g2log.py', svcname],
##                                          buzsize=1, stdout=subprocess.PIPE)
##         except Exception, e:
##             self.logger.error("Couldn't open tail process: %s" % str(e))
##             return
        
##         self.file = self.proc.stdout
##         self.size = 0
##         self.poll()


##     def close(self):
##         if self.proc:
##             try:
##                 self.proc.kill()
##             except:
##                 pass

##         super(TailPage, self).close()


class MonLogPage(LogPage):

    def add2log(self, logdict):
        #self.tw.scroll_mark_onscreen(self.mark)

        data = logdict['msgstr']

        if len(data) > 0:
            with self.lock:
                for line in data.split('\n'):
                    if len(line) > 0:
                        self.push(line)

#END

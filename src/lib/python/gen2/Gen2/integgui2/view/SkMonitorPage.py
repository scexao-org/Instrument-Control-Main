# 
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Oct 19 16:55:16 HST 2011
#]

# Standard library imports
import sys
import re, time
import threading

# Special library imports
import gtk

import Bunch
import remoteObjects as ro
import common
import WorkspacePage
from LogPage import NotePage


class SkMonitorPage(WorkspacePage.ButtonWorkspacePage):

    def __init__(self, frame, name, title):

        WorkspacePage.ButtonWorkspacePage.__init__(self, frame, name, title)

        self.pagelist = []
        self.pagelimit = 100
        self.db = {}
        # TODO: this dict is growing indefinitely
        self.track = {}

        # Don't allow DND to this workspace
        self.nb.set_group_id(2)
        self.nb.set_tab_pos(gtk.POS_RIGHT)

        ## menu = self.add_pulldownmenu("Page")

        ## item = gtk.MenuItem(label="Close")
        ## # currently disabled
        ## item.set_sensitive(False)
        ## menu.append(item)
        ## item.connect_object ("activate", lambda w: self.close(),
        ##                      "menu.Close")
        ## item.show()

        # Options menu
        ## menu = self.add_pulldownmenu("Option")
        menu = gtk.Menu()
        item = gtk.MenuItem(label="Option")
        self.wsmenu.append(item)
        item.show()
        item.set_submenu(menu)

        # Option variables
        self.save_decode_result = False
        self.show_times = False
        self.track_elapsed = False
        self.track_subcommands = True

        w = gtk.CheckMenuItem("Track Subcommands")
        w.set_active(self.track_subcommands)
        menu.append(w)
        w.show()
        w.connect("activate", lambda w: self.toggle_var(w, 'track_subcommands'))

        w = gtk.CheckMenuItem("Save Decode Result")
        w.set_active(self.save_decode_result)
        menu.append(w)
        w.show()
        w.connect("activate", lambda w: self.toggle_var(w, 'save_decode_result'))
        w = gtk.CheckMenuItem("Show Times")
        w.set_active(self.show_times)
        menu.append(w)
        w.show()
        w.connect("activate", lambda w: self.toggle_var(w, 'show_times'))

        w = gtk.CheckMenuItem("Track Elapsed")
        w.set_active(self.track_elapsed)
        menu.append(w)
        w.show()
        w.connect("activate", lambda w: self.toggle_var(w, 'track_elapsed'))


    def toggle_var(self, widget, key):
        if widget.active: 
            self.__dict__[key] = True
        else:
            self.__dict__[key] = False


    def insert_ast(self, tw, text):

        buf = tw.get_buffer()
        all_tags = set([])

        def insert(text, tags):

            loc = buf.get_end_iter()
            #linenum = loc.get_line()
            try:
                idx_div = text.index("<div ")

            except ValueError:
                buf.insert_with_tags_by_name(loc, text, *tags)
                return

            match = re.match(r'^\<div\sclass=([^\>]+)\>', text[idx_div:],
                             re.MULTILINE | re.DOTALL)
            if not match:
                buf.insert_with_tags_by_name(loc, 'ERROR 1: %s' % text, *tags)
                return

            num = int(match.group(1))
            regex = r'^(.*)\<div\sclass=%d\>(.+)\</div\sclass=%d\>(.*)$' % (
                num, num)
            #print regex
            match = re.match(regex, text, re.MULTILINE | re.DOTALL)
            if not match:
                buf.insert_with_tags_by_name(loc, 'ERROR 2: %s' % text, *tags)
                return

            buf.insert_with_tags_by_name(loc, match.group(1), *tags)

            serial_num = '%d' % num
            buf.create_tag(serial_num, foreground="black")
            newtags = [serial_num]
            all_tags.add(serial_num)
            newtags.extend(tags)
            insert(match.group(2), newtags)

            insert(match.group(3), tags)

        # Create tags that will be used
        buf.create_tag('code', foreground="black")
        
        insert(text, ['code'])
        #tw.tag_raise('code')
        #print "all tags=%s" % str(all_tags)

    def delpage(self, name):
        with self.lock:
            try:
                super(SkMonitorPage, self).delpage(name)
            except Exception, e:
                # may have already been removed
                pass
            try:
                self.pagelist.remove(name)
            except ValueError:
                # may have already been removed
                pass
            try:
                del self.db[name]
            except KeyError:
                # may have already been removed
                pass

    def addpage(self, name, title, text):

        with self.lock:
            # Make room for new pages
            while len(self.pagelist) >= self.pagelimit:
                oldname = self.pagelist.pop(0)
                self.delpage(oldname)

            page = super(SkMonitorPage, self).addpage(name, title, NotePage)

            self.pagelist.append(name)

            self.nb.set_tab_reorderable(page.frame, False)
            self.nb.set_tab_detachable(page.frame, False)

            self.insert_ast(page.tw, text)
            page.tagtbl = page.buf.get_tag_table()

            #self.select(name)
            return page
        
    def change_text(self, page, tagname, key):
        tagname = str(tagname)
        tag = page.tagtbl.lookup(tagname)
        if not tag:
            raise TagError("Tag not found: '%s'" % tagname)

        bnch = common.monitor_tags[key]

        for key, val in bnch.items():
            tag.set_property(key, val)
            
        #page.tw.tag_raise(ast_num)
        # Scroll the view to this area
        start, end = common.get_region(page.buf, tagname)
        page.tw.scroll_to_iter(start, 0.1)


    def replace_text(self, page, tagname, textstr,
                     start_offset=0):
        #print "replacing '%s' on %s" % (textstr, tagname)
        tagname = str(tagname)
        txtbuf = page.buf
        #print "getting region"
        start, end = common.get_region(txtbuf, tagname)
        start.forward_chars(start_offset)
        text = txtbuf.get_text(start, end)
        #print "deleting %s" % (text)
        txtbuf.delete(start, end)
        #print "inserting %s" % (textstr)
        txtbuf.insert_with_tags_by_name(start, textstr, tagname)

        # Scroll the view to this area
        page.tw.scroll_to_iter(start, 0.1)


    def insert_line(self, page, tagname, newtag, level, textstr):
        tagname = str(tagname)
        txtbuf = page.buf
        start, end = common.get_region(txtbuf, tagname)
        end2 = end.copy()
        end2.forward_to_line_end()
        if end.get_line() != end2.get_line():
            end2 = end.copy()
        txtbuf.create_tag(newtag, foreground="black")
        prefix = '\n' + ('  ' * level) + ' '
        txtbuf.insert_with_tags_by_name(end2, prefix, 'code')
        txtbuf.insert_with_tags_by_name(end2, textstr, newtag)
        txtbuf.insert_with_tags_by_name(end2, ' ', 'code')


    def append_error(self, page, tagname, textstr):
        tagname = str(tagname)
        txtbuf = page.buf
        start, end = common.get_region(txtbuf, tagname)
        txtbuf.insert_with_tags_by_name(end, textstr, tagname)

        self.change_text(page, tagname, 'error')


    def update_time(self, page, tagname, vals, time_s):

        if not self.show_times:
            return

        tagname = str(tagname)
        txtbuf = page.buf
        start, end = common.get_region(txtbuf, tagname)

        if vals.has_key('time_added'):
            length = vals['time_added']
            end = start.copy()
            end.forward_chars(length)
            txtbuf.delete(start, end)
            
        vals['time_added'] = len(time_s)
        txtbuf.insert_with_tags_by_name(start, time_s, tagname)
        

    def update_page(self, bnch):

        info = bnch.info
        page = info.page
        vals = bnch.state
        ## print "update_page: vals = %s" % str(vals)
        tagname = bnch.tag

        cmd_str = None
        if vals.has_key('cmd_str'):
            cmd_str = vals['cmd_str']
            cmd_repn = vals.get('cmd_repn', cmd_str)

            # Only update this string if it has changed
            if not vals.has_key('inserted') or (vals['inserted'] != cmd_repn):
                offset = vals.get('time_added', 0)
                # Replace the decode string with the actual parameters
                self.replace_text(page, tagname, cmd_repn,
                                  start_offset=offset)
                vals['inserted'] = cmd_repn

        if vals.has_key('task_error'):
            self.append_error(page, tagname, '\n ==> ' + vals['task_error'])
            
            # audible warnings
            if not vals.has_key('audible'):
                vals['audible'] = True
                # Only play an audible error if this was not a cancel
                if vals.has_key('task_code') and (vals['task_code'] != 3):
                    common.controller.audible_warn(cmd_str, vals)

        elif vals.has_key('task_end'):
            if vals.has_key('task_start'):
                if self.track_elapsed and info.has_key('asttime'):
                    elapsed = vals['task_start'] - info.asttime
                else:
                    elapsed = vals['task_end'] - vals['task_start']
                self.update_time(page, tagname, vals, '[ F %9.3f s ]: ' % (
                        elapsed))
            else:
                self.update_time(page, tagname, vals, '[TE %s]: ' % (
                        self.time2str(vals['task_end'])))
            self.change_text(page, tagname, 'task_end')
                
        elif vals.has_key('end_time'):
            self.update_time(page, tagname, vals, '[EN %s]: ' % (
                    self.time2str(vals['end_time'])))
            self.change_text(page, tagname, 'end_time')
                
        elif vals.has_key('ack_time'):
            self.update_time(page, tagname, vals, '[AB %s]: ' % (
                    self.time2str(vals['ack_time'])))
            self.change_text(page, tagname, 'ack_time')

        elif vals.has_key('cmd_time'):
            self.update_time(page, tagname, vals, '[CD %s]: ' % (
                    self.time2str(vals['cmd_time'])))
            self.change_text(page, tagname, 'cmd_time')

        elif vals.has_key('task_start'):
            self.update_time(page, tagname, vals, '[TS %s]: ' % (
                    self.time2str(vals['task_start'])))
            self.change_text(page, tagname, 'task_start')

        else:
            #self.change_text(page, tagname, 'code')
            pass

                
    def time2str(self, time_cmd):
        time_int = int(time_cmd)
        time_str = time.strftime("%H:%M:%S", time.localtime(float(time_int)))
        time_sfx = ('%.3f' % (time_cmd - time_int)).split('.')[1]
        title = time_str + ',' + time_sfx
        return title

            
    def process_ast(self, ast_id, vals):
        #print ast_id, vals
        name = str(ast_id)
        
        with self.lock:
            try:
                info = self.db[name]
                page = info.page
            except KeyError:
                # this ast_id is not received/set up yet
                #info = Bunch.Bunch(nodes={}, page=None)
                info = Bunch.Bunch(page=None, pageid=ast_id)
                self.db[name] = info
                page = None

            if vals.has_key('ast_buf'):
                ast_str = ro.binary_decode(vals['ast_buf'])
                ast_str = ro.uncompress(ast_str)
                # Due to an unfortunate way in which we have to search for
                # tags in common.get_region()
                if not ast_str.endswith('\n'):
                    ast_str = ast_str + '\n'
                #print "BUF!"; print ast_str

                # Get the time of the command to construct the tab title
                title = self.time2str(vals['ast_time'])
                info.asttime = vals['ast_time']

                # TODO: what if this page has already been deleted?
                if self.save_decode_result:
                    self.addpage(name + '.decode', title, ast_str)

                page = self.addpage(name, title, ast_str)
                info.page = page

            elif vals.has_key('ast_track'):
                path = vals['ast_track']
                
                # GLOBAL VAR READ
                curvals = common.controller.getvals(path)
                if isinstance(curvals, dict):
                    vals.update(curvals)
               
                # Make an entry for this ast node, if there isn't one already
                tagname = '%d' % vals['ast_num']
                # ?? necessary to have "nodes" table?
                #state = info.nodes.setdefault(tagname, vals)
                state = vals.copy()

                bnch = Bunch.Bunch(info=info, state=state, tag=tagname,
                                   level=0, count=0)
                self.track.setdefault(path, bnch)

                # It's possible in some cases that the ast_track could
                # arrive before the page is added or set up
                if not page:
                    return

                # Replace the decode string with the actual parameters
                # ?? Has string really changed at this point??
                #self.replace_text(page, tagname, vals['ast_str'])

                self.update_page(bnch)
                

    def process_subcommand(self, parent_path, subpath, vals):

        with self.lock:
            # Don't do anything if we are not tracking subcommands
            if not self.track_subcommands:
                return
            
            try:
                # Get parent track record
                p_bnch = self.track[parent_path]
            except KeyError:
                # parent command is not received/set up yet
                return

            # Have we already set this up?
            if self.track.has_key(subpath):
                return
            
            page = p_bnch.info.page
            if not page:
                return

            # Collect any state that has built up for this path
            state = {}
            curvals = common.controller.getvals(subpath)
            if isinstance(curvals, dict):
                state.update(curvals)
            print "What we know is: %s" % str(state)

            # Figure out the text tag of the last subcommand under this
            # command based on the count
            lasttag = p_bnch.tag
            if p_bnch.count > 0:
                lasttag = '%s_%d' % (lasttag, p_bnch.count)
            p_bnch.count += 1
            count = p_bnch.count
            level = p_bnch.level + 1
            # make a new text tag for the subcommand
            tagname = '%s_%d' % (p_bnch.tag, count)
            cmd_str = 'SUBCOMMAND'

            # Insert a new line for the subcommand
            print "inserting new line: lasttag=%s" % (lasttag)
            self.insert_line(page, lasttag, tagname, level, cmd_str)
            
            bnch = Bunch.Bunch(info=p_bnch.info, state=state, tag=tagname,
                               level=level, count=count)
            self.track.setdefault(subpath, bnch)

            self.update_page(bnch)


    def process_task(self, path, vals):
        ## print "process_task: ", path, vals

        with self.lock:
            try:
                bnch = self.track[path]
            except KeyError:
                # this page is not received/set up yet
                return

            #print path, vals
            bnch.state.update(vals)

            if bnch.info.page:
                self.update_page(bnch)
            

           
#END

# 
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Jan 20 13:20:34 HST 2012
#]

import os, time
import gtk

import LogPage
import common

import Bunch


header = "FrameNo      State   Date_Obs     Ut       Exptime  ObsMode         Object          Disperser,Filters    [memo................]"

# Format string used to pass information to IntegGUI
format_str = "%(frameid)-12.12s %(status)5.5s  %(DATE-OBS)-10.10s %(UT-STR)-8.8s %(EXPTIME)10.10s  %(OBS-MOD)-15.15s %(OBJECT)-15.15s %(FILTERS)-20.20s %(MEMO)-s"

frame_tags = [
    ('A', 'normal', Bunch.Bunch(foreground='black', background='white')),
    ('X', 'transfer', Bunch.Bunch(background='palegreen')),
    ('R', 'received', Bunch.Bunch(foreground='dark green', background='white')),
    ('RS', 'stars', Bunch.Bunch(foreground='blue2', background='white')),
    ('RT', 'starstrans', Bunch.Bunch(foreground='darkgreen', background='white')),
    ('RE', 'starserror', Bunch.Bunch(foreground='orange', background='white')),
    ('E', 'error', Bunch.Bunch(foreground='red', background='lightyellow')),
    ]

    
class FrameInfoPage(LogPage.NotePage):

    def __init__(self, frame, name, title):

        super(FrameInfoPage, self).__init__(frame, name, title)

        # bottom buttons
        btns = gtk.HButtonBox()
        btns.set_layout(gtk.BUTTONBOX_START)
        btns.set_spacing(5)
        self.btns = btns

#         self.btn_load = gtk.Button("Load")
#         self.btn_load.connect("clicked", lambda w: self.load_frames())
#         self.btn_load.show()
#         btns.pack_end(self.btn_load, padding=4)

        frame.pack_end(btns, fill=False, expand=False, padding=2)

#        menu = self.add_menu()
#        self.add_close()

        menu = self.add_pulldownmenu("Page")

        # item = gtk.MenuItem(label="Print")
        # menu.append(item)
        # item.connect_object ("activate", lambda w: self.print_journal(),
        #                      "menu.Print")
        # item.show()

        # For line coloring
        self.colortbl = {}
        for status, tag, bnch in frame_tags:
            properties = {}
            properties.update(bnch)
            self.addtag(tag, **properties)

            self.colortbl[status] = tag


    def update_frame(self, frameinfo):
        self.logger.debug("UPDATE FRAME: %s" % str(frameinfo))

        frameid = frameinfo.frameid
        with self.lock:
            text = format_str % frameinfo

            # set tags according to content of message
            try:
                tags = [ self.colortbl[frameinfo.status] ]
            except Exception, e:
                print str(e)
                tags = ['normal']

            print tags, frameinfo
            if hasattr(frameinfo, 'row'):
                row = frameinfo.row
                #common.update_line(self.buf, row, text)
                common.update_line(self.buf, row, text, tags=tags)

            else:
                end = self.buf.get_end_iter()
                frameinfo.row = end.get_line()
                
                self.append(text+'\n', tags)

        
    def update_frames(self, framelist):

        # Delete frames text
        start, end = self.buf.get_bounds()
        self.buf.delete(start, end)
        
        # Create header
        self.append(header+'\n', [])

        # add frames
        for frameinfo in framelist:
            self.update_frame(frameinfo)


    def select_frame(self, w, evt):
        with self.lock:
            widget = self.tw
            win = gtk.TEXT_WINDOW_TEXT
            buf_x1, buf_y1 = widget.window_to_buffer_coords(win, evt.x, evt.y)
            (startiter, coord) = widget.get_line_at_y(buf_y1)
            (enditer, coord) = widget.get_line_at_y(buf_y1)
            enditer.forward_to_line_end()
            text = self.buf.get_text(startiter, enditer).strip()
            frameno = text.split()[0]
            line = startiter.get_line()
            print "%d: %s" % (line, frameno)

            # Load into a fits viewer page
            common.view.load_frame(frameno)

##             try:
##                 self.image = self.datasrc[line]
##                 self.cursor = line
##                 self.update_img()
##             except IndexError:
##                 pass
            
        return True
        

    def load_frames(self):
        if not self.buf.get_has_selection():
            common.view.popup_error("No selection!")
            return

        # Get the range of text selected
        first, last = self.buf.get_selection_bounds()
        frow = first.get_line()
        lrow = last.get_line()

        # Clear the selection
        self.buf.move_mark_by_name("insert", first)         
        self.buf.move_mark_by_name("selection_bound", first)

        # Break selection into individual lines
        frames = []

        for i in xrange(int(lrow)+1-frow):

            row = frow+i

            first.set_line(row)
            last.set_line(row)
            last.forward_to_line_end()

            # skip comments and blank lines
            line = self.buf.get_text(first, last).strip()
            if len(line) == 0:
                continue

            frameno = line.split()[0]
            frames.append(frameno, [])

        #print "Loading frames", frames
        common.controller.load_frames(frames)

    def save_journal(self):
        homedir = os.path.join(os.environ['HOME'], 'Procedure')
        filename = time.strftime("%Y%m%d-obs") + '.txt'

        common.view.popup_save("Save frame journal", self._savefile,
                               homedir, filename=filename)

    def print_journal(self):
        pass

#END

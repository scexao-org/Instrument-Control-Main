# 
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Nov  5 10:10:10 HST 2010
#]

import gtk

import common
import LogPage

class TagPage(LogPage.NotePage):

    def __init__(self, frame, name, title):
        super(TagPage, self).__init__(frame, name, title)

        self.tw.connect("button-press-event", self.jump_tag)
        # currently disable close button
        self.menu_close.set_sensitive(False)

        self.tagidx = {}
        self.opepage = None

    def initialize(self, opepage):
        super(TagPage, self).clear()

        self.tagidx = {}
        self.opepage = opepage
        
    def add_mapping(self, lineno, line, tags):
        # Add this line and a tag to the tags buffer
        tend = self.buf.get_end_iter()
        taglineno = tend.get_line()
        ## self.tagbuf.insert_with_tags_by_name(tend, line+'\n',
        ##                                      *(tags + [tag]))
        self.buf.insert_with_tags_by_name(tend, line+'\n', *tags)
        # make an entry in the tags index
        self.tagidx[taglineno] = lineno

    ## def scroll_to_lineno(self, lineno):
    ##     # Scroll tag table to errors
    ##     loc = self.buf.get_end_iter()
    ##     loc.set_line(lineno)
    ##     # HACK: I have to defer the scroll operation until the widget
    ##     # is rendered or it does not scroll
    ##     # UPDATE: this causes a crash
    ##     ## common.view.gui_do(self.tw.scroll_to_iter,
    ##     ##                     loc, 0, True)

    def jump_tag(self, w, evt):
        widget = self.tw
        try:
            tup = widget.window_to_buffer_coords(gtk.TEXT_WINDOW_TEXT,
                                                 evt.x, evt.y)
            #print tup
            buf_x1, buf_y1 = tup
        except Exception, e:
            self.logger.error("Error converting coordinates to line: %s" % (
                str(e)))
            return False
        
        (startiter, coord) = widget.get_line_at_y(buf_y1)
        taglineno = startiter.get_line()
        try:
            lineno = self.tagidx[taglineno]
        except KeyError:
            return

        if not self.opepage:
            return True
        
        # TODO: raise self.opepage

        self.opepage.scroll_to_lineno(lineno)
        return True

#END

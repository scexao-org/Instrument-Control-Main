#
# common.py -- common module for IntegGUI view
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Jan 11 22:27:57 HST 2012
#]
import os.path
import re
import gtk

import Bunch

# Top directory to look for stuff
topprocdir = os.path.join(os.environ['HOME'], 'Procedure')

color_blue = '#cae1ff'     # pale blue
color_green = '#c1ffc1'     # pale green
color_yellow = '#fafad2'     # cream
#color_white = 'whitesmoke'
color_white = 'white'

color_bg = 'light grey'

# Gtk color objects used to set widgets dynamically
launcher_colors = Bunch.Bunch(error = gtk.gdk.color_parse('salmon'),
                              done = gtk.gdk.color_parse('skyblue'),
                              normal = gtk.gdk.color_parse('#dcdad5'),
                              executing =  gtk.gdk.color_parse('palegreen'),

                              #execbtn = gtk.gdk.color_parse('royalblue'),
                              #execbtn = gtk.gdk.color_parse('steelblue1'),
                              execbtn = gtk.gdk.color_parse('#82a8db'),
                              cancelbtn = gtk.gdk.color_parse('palevioletred'),
                              killbtn = gtk.gdk.color_parse('salmon'),

                              badtags = gtk.gdk.color_parse('red1'))

# Colors for embedded terminals
terminal_colors = Bunch.Bunch(fg=gtk.gdk.color_parse('black'),
                              bg=gtk.gdk.color_parse('white'),
                              )

# Colors used in the OpePage
decorative_tags = [
    ('comment3', Bunch.Bunch(foreground='indian red')),
    ('comment2', Bunch.Bunch(foreground='saddle brown')),
    ('comment1', Bunch.Bunch(foreground='dark green')),
    ('varref', Bunch.Bunch(foreground='royalblue')),
    ('badref', Bunch.Bunch(foreground='darkorange')),
    ]

# Colors used in the QueuePage
queue_tags = [
    ('normal', Bunch.Bunch(foreground='black')),
    ('comment3', Bunch.Bunch(foreground='indian red')),
    ('comment2', Bunch.Bunch(foreground='saddle brown')),
    ('comment1', Bunch.Bunch(foreground='dark green')),
    ('badref', Bunch.Bunch(foreground='red1')),
    ('selected', Bunch.Bunch(background='pink1')),
    ('cursor', Bunch.Bunch(background='#bf94e3')),
    ]

# Colors used in the OpePage for execution
execution_tags = [
    ('queued', Bunch.Bunch(background='lightyellow2')),
    ('executing', Bunch.Bunch(background='palegreen')),
    ('done',     Bunch.Bunch(foreground='blue2')),
    ('error',   Bunch.Bunch(foreground='red')),
    ]

# Colors used in the LogPage
log_tags = [
    ('error', Bunch.Bunch(foreground='red', background='lightyellow')),
    ('cancel', Bunch.Bunch(foreground='orange3')),
    ('normal', Bunch.Bunch(foreground='black')),
    ]

# If a log message matches one of these regexes, then color it.
# Tags are defined in the log_tags above
error_regexes = [
    (re.compile(r'^.*\|\sE\s\|.*$'), ['error']),
    (re.compile(r'^.*(error|exception).*$', re.I), ['error']),
    ]

# Colors used in the DirectoryPage
directory_tags = [
    ('normal', Bunch.Bunch(foreground='black')),
    ('executable', Bunch.Bunch(foreground='dark green')),
    ('directory',  Bunch.Bunch(foreground='blue2')),
    ('cursor',  Bunch.Bunch(foreground='yellow', background='dark green')),
    ]

# colors used in the SkMonitorPage
monitor_tags = Bunch.Bunch(
    code=Bunch.Bunch(foreground='black'),
    task_start=Bunch.Bunch(foreground='black', background='palegreen'),
    cmd_time=Bunch.Bunch(foreground='brown', background='palegreen'),
    ack_time=Bunch.Bunch(foreground='green4', background='palegreen'),
    end_time=Bunch.Bunch(foreground='blue1', background='white'),
    task_end=Bunch.Bunch(foreground='blue2', background='white'),
    error=Bunch.Bunch(foreground='red', background='lightyellow')
    )

# Define sounds used in IntegGUI
sound = Bunch.Bunch(#success_executer='doorbell.au',
                    success_executer='ogg/ocs/doorbell-1.ogg',
                    #success_executer='beep-09.au',
                    success_launcher='ogg/ocs/beep-02.ogg',
                    #success_launcher='LAUNCHER_COMPLETE.au',
                    #cancel_launcher='E_CANCEL.au',
                    #cancel_executer='E_CANCEL.au',
                    ## cancel_launcher='tos-computer-05.au',
                    ## cancel_executer='tos-computer-05.au',
                    cancel_launcher='ogg/ocs/taskmgr_cancelled.ogg',
                    cancel_executer='ogg/ocs/taskmgr_cancelled.ogg',
                    #tm_cancel='tos-computer-04.au',
                    tm_cancel='ogg/ocs/integgui2_cancel.ogg',
                    ## tm_kill='ogg/ocs/photon-torpedo.ogg',
                    ## tm_ready='ogg/ocs/tos-computer-03.ogg',
                    tm_kill='ogg/ocs/integgui2_kill.ogg',
                    tm_ready='ogg/ocs/taskmgr_ready.ogg',
                    #fail_executer='splat.au',
                    failure_executer='ogg/ocs/hit-02.ogg',
                    failure_launcher='ogg/ocs/dishes-break-01.ogg',
                    break_executer='ogg/ocs/beep-04.ogg',
                    #open_panel='ogg/ocs/tos-turboliftdoor.ogg',
                    open_panel='ogg/ocs/beep-05.ogg',
                    #close_panel='ogg/ocs/tos-turboliftdoor.ogg',
                    close_panel='ogg/ocs/beep-05.ogg',
                    pause_toggle='ogg/ocs/beep-05.ogg',
                    bad_keystroke='ogg/ocs/beep-07.ogg',
                    )

# YUK...MODULE-LEVEL GLOBAL VARIABLES
view = None
controller = None

def set_view(pview):
    global view
    view = pview

def set_controller(pcontroller):
    global controller
    controller = pcontroller

def gui_do(method, *args, **kwdargs):
    return view.gui_do(method, *args, **kwdargs)
    
def gui_do_res(method, *args, **kwdargs):
    return view.gui_do_res(method, *args, **kwdargs)
    
def update_line(buf, row, text, tags=None):
    """Update a line of the text widget _tw_, defined by _row_,
    with the value _val_.
    """
    start = buf.get_start_iter()
    start.set_line(row)
    if start.get_line() == row:
        end = start.copy()
        end.forward_to_line_end()
    
        buf.delete(start, end)
    else:
        # append some rows so we can go to the correct row
        end = buf.get_end_iter()
        while end.get_line() <= row:
            buf.insert(end, '\n')
            end = buf.get_end_iter()

    if len(text) == 0:
        text = ' '

    res = start.set_line(row)
    if start.get_line() != row:
        print "Could not set line to %d !" % row

    if not tags:
        buf.insert(start, text)
    else:
        buf.insert_with_tags_by_name(start, text, *tags)

def change_text(page, tagname, **kwdargs):
    tag = page.tagtbl.lookup(tagname)
    if not tag:
        raise TagError("Tag not found: '%s'" % tagname)

    for key, val in kwdargs.items():
        tag.set_property(key,val)

    # Scroll the view to this area
    start, end = get_region(page.buf, tagname)
    page.tw.scroll_to_iter(start, 0.1)


def get_region(txtbuf, tagname):
    """Returns a (start, end) pair of Gtk text buffer iterators
    associated with this tag.
    """
    # Painfully inefficient and error-prone way to locate a tagged
    # region.  Seems gtk text buffers have tags, but no good way to
    # manipulate text associated with them efficiently.

    # Get the tag table associated with this text buffer
    tagtbl = txtbuf.get_tag_table()
    # Look up the tag
    tag = tagtbl.lookup(tagname)

    # Get text iters at beginning and end of buffer
    start, end = txtbuf.get_bounds()

    # Now search forward from beginning for first location of this
    # tag, and backwards from the end
    result = start.forward_to_tag_toggle(tag)
    if not result:
        raise TagError("Tag not found: '%s'" % tagname)
    result = end.backward_to_tag_toggle(tag)
    if not result:
        raise TagError("Tag not found: '%s'" % tagname)

    return (start, end)


def get_region_lines(txtbuf, tagname):
    start, end = get_region(txtbuf, tagname)

    if not start.starts_line():
        frow = start.get_line()
        start.set_line(frow)
    if not end.ends_line():
        end.forward_to_line_end()
    
    return (start, end)


def replace_text(page, tagname, textstr):
    txtbuf = page.buf
    start, end = get_region(txtbuf, tagname)
    txtbuf.delete(start, end)
    txtbuf.insert_with_tags_by_name(start, textstr, tagname)

    # Scroll the view to this area
    page.tw.scroll_to_iter(start, 0.1)


def clear_tags_region(buf, tags, start, end):
    for tag in tags:
        buf.remove_tag_by_name(tag, start, end)

def clear_tags(buf, tags):
    start, end = buf.get_bounds()
    for tag in tags:
        buf.remove_tag_by_name(tag, start, end)

##### remove all markers
def remove_all_marks(buffer):
    # Only for gtksourceview buffers
    begin, end = buffer.get_bounds()
    buffer.remove_source_marks(begin, end)

def get_tv(widget):
    txtbuf = widget.get_buffer()
    startiter, enditer = txtbuf.get_bounds()
    text = txtbuf.get_text(startiter, enditer)
    return text

def append_tv(widget, text):
    txtbuf = widget.get_buffer()
    enditer = txtbuf.get_end_iter()
    txtbuf.place_cursor(enditer)
    txtbuf.insert_at_cursor(text)
    startiter = txtbuf.get_start_iter()
    txtbuf.place_cursor(startiter)
    enditer = txtbuf.get_end_iter()
    widget.scroll_to_iter(enditer, False, 0, 0)

def clear_tv(widget):
    txtbuf = widget.get_buffer()
    startiter, enditer = txtbuf.get_bounds()
    txtbuf.delete(startiter, enditer)

def clear_selection(widget):
    txtbuf = widget.get_buffer()
    insmark = txtbuf.get_insert()
    if insmark != None:
        insiter = txtbuf.get_iter_at_mark(insmark)
        txtbuf.select_range(insiter, insiter)
    else:
        try:
            first, last = txtbuf.get_selection_bounds()
            txtbuf.select_range(first, first)
        except ValueError:
            return
        

class TagError(Exception):
    pass

class SelectionError(Exception):
    pass

#END

#!/usr/bin/env python
#
# STARSintTester.py -- STARS interface tester
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Dec 18 12:26:29 HST 2008
#]
#
#
import sys, time
import threading, Queue

from STARSint import STARSintError, STARSinterface
from SOSS import SOSSrpc
import StatusBundle
import remoteObjects as ro

try:
    import gtk
    import gobject
except:
    print "You need to install GTKv2 ",
    print "or set your PYTHONPATH correctly."
    print "try: export PYTHONPATH=",
    print "/usr/lib/python2.X/site-packages/"
    sys.exit(1)

try:
    from STARSintGUI import *
except:
    print "You need to set your PYTHONPATH to include STARSintGUI.py",
    print "or you may need to run GladeGen.py to generate it."
    sys.exit(1)


version = '20080104.0'

# Get text from a GtkTextView
#
def get_tv(widget):
    txtbuf = widget.get_buffer()
    startiter, enditer = txtbuf.get_bounds()
    text = txtbuf.get_text(startiter, enditer)
    return text

def get_selection_tv(widget):
    txtbuf = widget.get_buffer()
    startiter, enditer = txtbuf.get_selection_bounds()
    text = txtbuf.get_text(startiter, enditer)
    return text
    
# Append text to a GtkTextView
#
def append_tv(widget, text):
    txtbuf = widget.get_buffer()
    enditer = txtbuf.get_end_iter()
    txtbuf.place_cursor(enditer)
    txtbuf.insert_at_cursor(text)
    # Put cursor at end
    enditer = txtbuf.get_end_iter()
    txtbuf.place_cursor(enditer)
    # Scroll window to show end
    widget.scroll_to_iter(enditer, False, 0, 0)

def get_combobox_text(combobox):
    model = combobox.get_model()
    active = combobox.get_active()
    if active < 0:
        return None
    return model[active][0]
        
# This is the class defining our main GUI-based application.
# We subclass from STARSintGUI so that all we need to really do here
# is define callback functions for the widgets.
#
class STARSintTester(STARSintGUI):

    def __init__(self, options):
        """
        Constructor for the STARSintTester object.
        """
        self.starshost = SOSSrpc.get_myhost(short=True)
        self.starsdir = 'data'
        self.channels = [7,8]
        self.numchannels = len(self.channels)
        self.ev_quit = threading.Event()
        self.ev_mainquit = threading.Event()
        self.stars = None
        self.mode = 'stopped'
        self.monitor = options.monitor
        self.counter = 0

        # Invoke our base class constructor.
        STARSintGUI.__init__(self)

        # Initialize setup gui defaults
        sw = self.widgets['location']
        sw.set_active(0)
        self.widgets['channels'].set_text('7,8')
        self.widgets['starshost'].set_text(self.starshost)
        self.widgets['starsdir'].set_text(self.starsdir)


# --- CALLBACKS ---
# These are automatically registered by the STARSintGUI.py file.
# You specify the function names you want to use in the Glade designer.


    def on_start_clicked(self, widget):
        if not self.stars:
            self.showStatus("PLEASE SETUP INTERFACE FIRST")
            return gtk.TRUE
            
        if self.mode != 'stopped':
            self.showStatus("PLEASE STOP SERVERS FIRST")
            return gtk.TRUE
            
        self.ev_quit.clear()
        self.mode = 'started'

        self.stars.start(wait=True)

        for ch_i in self.channels:
            gobject.timeout_add(100, self.mk_checklog(ch_i, self.stars.channel[ch_i].logqueue, \
                                                      self.widgets['chantext']))

        # TODO: disable certain widgets 
        return gtk.TRUE

    def on_stop_clicked(self, widget):
        if not self.stars:
            self.showStatus("PLEASE SETUP INTERFACE FIRST")
            return gtk.TRUE
            
        if self.mode != 'started':
            self.showStatus("PLEASE START SERVERS FIRST")
            return gtk.TRUE
            
        self.stars.stop(wait=True)
        self.mode = 'stopped'

        # TODO: reenable certain widgets 
        return gtk.TRUE

    def on_send_clicked(self, widget):
        if not self.stars:
            self.showStatus("PLEASE SETUP INTERFACE FIRST")
            return gtk.TRUE

        if self.mode != 'started':
            self.showStatus("PLEASE START SERVERS FIRST")
            return gtk.TRUE
            
        # Throw up a file selection dialog and let the user pick a file
        sw = self.widgets['dialog_filechooser']
        sw.window.show()
        resp = sw.run()
        sw.window.hide()

        # If they clicked "OK" then try to send the file.
        if resp == gtk.RESPONSE_OK:
            filepath = sw.get_filename()
            #print str(filepath)
            (filedir, filename) = os.path.split(filepath)
            
#            self.showStatus("Trying to archive %s to STARS..." % filename)
            self.counter += 1
            tag = ('stars.%d' % self.counter)
            self.stars.submit_fits(tag, filepath)

        return gtk.TRUE


    def mk_checklog(self, ch_i, queue, widget):
        return lambda: self.checklog(ch_i, queue, widget)
    
    def checklog(self, ch_i, queue, widget):

        if (not self.stars) or (not queue):
            return False

        try:
            msg = queue.get(block=False)
            append_tv(widget, ('CH(%d): %s\n' % (ch_i, msg)))

        except Queue.Empty:
            pass

        return True
        

        return True
            

    def on_location_changed(self, widget):
        locn = get_combobox_text(self.widgets['location'])
        if locn.lower() == 'summit':
            self.widgets['channels'].set_text('1,2')
            self.widgets['starshost'].set_text('N/A')
            self.widgets['starsdir'].set_text('N/A')
            
        elif locn.lower() == 'simulator':
            self.widgets['channels'].set_text('5,6')
            self.widgets['starshost'].set_text('N/A')
            self.widgets['starsdir'].set_text('N/A')
        
        else:
            self.widgets['channels'].set_text('7,8')
            self.widgets['starshost'].set_text(self.starshost)
            self.widgets['starsdir'].set_text(self.starsdir)
        
        return gtk.TRUE


    def on_setup_clicked(self, widget):
        sw = self.widgets['dialog_setup']

        # Set other fields to defaults
        self.on_location_changed(widget)
        
        sw.window.show()
        resp = sw.run()
        sw.window.hide()

        if resp == gtk.RESPONSE_OK:
            starshost = self.widgets['starshost'].get_text()
            if starshost == 'N/A':
                starshost = None
            self.starshost=starshost
            starsdir = self.widgets['starsdir'].get_text()
            if starsdir == 'N/A':
                starsdir = None
            self.starsdir=starsdir
            channels = self.widgets['channels'].get_text()
            channels = map(int, channels.split(','))
            for ch_i in channels:
                if not ch_i in [1,2,3,4,5,6,7,8]:
                    self.showStatus("Channels must be in the range 1-8!!")
            
                    return gtk.TRUE
            self.channels = channels
                
            db = StatusBundle.nestedStatusBundle()
            if self.monitor:
                monitor = ro.remoteObjectProxy(self.monitor)
                svcname = 'STARSint'
                db.register_sync(svcname, monitor)

            # Any way to force collection of the socket here?
            self.stars = None
            try:
                self.stars = STARSinterface(starshost=self.starshost,
                                            starsdir=self.starsdir,
                                            channels=self.channels, db=db,
                                            ev_quit=self.ev_quit)
            except Exception, e:
                self.showStatus("FAILED TO INITIALIZE INTERFACE")
                self.stars = None
            
        return gtk.TRUE


    # Quit the application.
    #
    def quit(self, widget):
        if self.stars:
            self.on_stop_clicked(widget)

        self.ev_mainquit.set()
        return gtk.TRUE


    # Send selected FITS files.
    #
    def sendfiles(self, widget):
        if not self.stars:
            self.showStatus("Servers not started!")
            return gtk.TRUE

        self.showStatus("Files queued.")
        
        return gtk.TRUE


    # Write a message to the status bar.
    #
    def showStatus(self, text):
        sw = self.widgets['statusbar']
        context = sw.get_context_id("status")

        sw.pop(context)
        sw.push(context, text)
        return


def main(options, args):

    if options.monitor:
        ro.init()
        
    app = STARSintTester(options)
    app.show()
    sw = app.widgets['dialog_filechooser']
    sw.window.hide()
    sw = app.widgets['dialog_setup']
    sw.window.hide()


    # Enter GUI event-processing loop.
    while not app.ev_mainquit.isSet():
        # Process X events
        while gtk.events_pending():
            gtk.main_iteration()

        # Sleep and let other threads run
        time.sleep(0.1)
    

if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    parser.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    parser.add_option("-m", "--monitor", dest="monitor",
                      metavar="NAME",
                      help="Reflect internal status to monitor service NAME")
    parser.add_option("--numthreads", dest="numthreads", type="int",
                      default=1,
                      help="Use NUM threads for each interface", metavar="NUM")
    parser.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")

    (options, args) = parser.parse_args(sys.argv[1:])

    if len(args) != 0:
        parser.error("incorrect number of arguments")


    # Are we debugging this?
    if options.debug:
        import pdb

        pdb.run('main(options, args)')

    # Are we profiling this?
    elif options.profile:
        import profile

        print "%s profile:" % sys.argv[0]
        profile.run('main(options, args)')

    else:
        main(options, args)

#END


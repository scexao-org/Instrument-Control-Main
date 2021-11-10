#!/usr/bin/env python
#
# INSintTester.py -- instrument interface tester for SOSS & Gen2
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Jul  8 11:14:35 HST 2010
#]
#
#
import sys, os, time
import re
import threading, Queue
# optparse imported below (if needed)

import SOSS.INSint as INSint
from cfg.INS import INSdata as INSconfig
from SOSS import SOSSrpc
import Bunch
import remoteObjects as ro
import remoteObjects.Monitor as Monitor
# SOSS.status imported below (if needed)
import logging, ssdlog

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
    from INSintGUI import *
except:
    print "You need to set your PYTHONPATH to include INSintGUI.py",
    print "or you may need to run GladeGen.py to generate it."
    sys.exit(1)


version = '20080103.0'


# --- Helper functions for Gtk widgets ---

## def _idle_func(function, args, kw):
##        gtk.threads_enter()
##        try:
##            return function(*args, **kw)
##        finally:
##            gtk.threads_leave()

## def idle_add_lock(function, *args, **kw):
##    gobject.idle_add(_idle_func, function, args, kw)

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

def clear_tv(widget):
    txtbuf = widget.get_buffer()
    startiter = txtbuf.get_start_iter()
    enditer = txtbuf.get_end_iter()
    txtbuf.delete(startiter, enditer)

def get_combobox_text(combobox):
    model = combobox.get_model()
    active = combobox.get_active()
    if active < 0:
        return None
    return model[active][0]

        
class INSintTester(INSintGUI):
    """This is the class defining our main GUI-based application.
    We subclass from INSintGUI so that all we need to really do here
    is define callback functions for the widgets.
    """
    
    def __init__(self, options, logger):
        """Constructor for the INSintTester object.
        """

        # Invoke our base class constructor.
        INSintGUI.__init__(self)

        self.logger = logger
        self.insconfig = INSconfig()
        
        # Set up default connection parameters from command line
        self.obcpnum = options.obcpnum
        self.monunitnum = options.monunitnum
        if not options.obcphost:
            self.obcphost = SOSSrpc.get_myhost(short=True)
        else:
            self.obcphost = options.obcphost
        self.raidpath = options.fitsdir
        self.transfermethod = options.transfermethod
        self.username = options.username
        self.password = options.password
        
        self.ev_quit = threading.Event()
        self.ev_mainquit = threading.Event()
        self.soss = None

        # Did user specify a Gen2 status source?
        if options.statussvc:
            ro_status = ro.remoteObjectProxy(options.statussvc)
            statusObj = INSint.FetchStatusWrapper_Gen2(ro_status)
        
        # Did user specify a SOSS status source?
        elif options.statushost:
            from SOSS.status import cachedStatusObj

            statusDict = cachedStatusObj(options.statushost)
            statusObj = INSint.FetchStatusWrapper_SOSS(statusDict)

        # Did user specify a SOSS status file?
        elif options.statusfile:
            try:
                in_f = open(options.statusfile, 'r')
                statusDict = eval(in_f.read())
                in_f.close()
                
            except Exception, e:
                self.showStatus("Error reading status file '%s': %s" % \
                                (options.statusfile, str(e)))
                statusDict = {}

            statusObj = INSint.FetchStatusWrapper_SOSS(statusDict)

        else:
            statusDict = {}
            statusObj = INSint.FetchStatusWrapper_SOSS(statusDict)
            
        self.statusObj = statusObj
        self.mode = None
        self.cmdtag = 0
        self.cmdqueue = Queue.Queue()
        self.monitor = options.monitor
    
        # Set defaults for setup dialog
        sw = self.widgets['transfermethod']
        sw.set_active(1)
        #current default for this widget is 9, but it would be nice to set it here
        #self.widgets['obcpnum'].set_value_as_int(self.obcpnum)
        self.widgets['username'].set_text(self.username)
        self.widgets['password'].set_text(self.password)
        self.widgets['obcphost'].set_text(self.obcphost)
        self.widgets['raidarea'].set_text(self.raidpath)
        

# --- CALLBACKS ---
# These are automatically registered by the INSintGUI.py file.
# You specify the function names you want to use in the Glade designer.


    def start(self, widget):
        """Start all instrument interface servers.
        """
        if not self.mode:
            self.showStatus("PLEASE SETUP SERVERS FIRST")
            return gtk.TRUE
            
        if self.mode != 'stopped':
            self.showStatus("PLEASE STOP SERVERS FIRST")
            return gtk.TRUE

        # Reset global event used to synchronize threads
        self.ev_quit.clear()

        self.mythread = threading.Thread(target=self.send_loop)
        self.mythread.start()

        # Start the interface
        self.soss.start(wait=True)

        # Add timed interval callbacks to widgets to monitor logs
        gobject.timeout_add(100, lambda: self.checklog(self.soss.iface['cmd'].logqueue, \
                                                       self.widgets['resulttext']))
        gobject.timeout_add(100, lambda: self.checklog(self.soss.iface['thru'].logqueue, \
                                                       self.widgets['throughtext']))
        gobject.timeout_add(100, lambda: self.checklog(self.soss.iface['sreq'].logqueue, \
                                                       self.widgets['statusreqtext']))
        gobject.timeout_add(100, lambda: self.checklog(self.soss.iface['sdst'].logqueue, \
                                                       self.widgets['statusrcvdtext']))
        gobject.timeout_add(100, lambda: self.checklog(self.soss.iface['file'].logqueue, \
                                                       self.widgets['fitsrecvtext']))

        self.mode = 'started'
        
        # TODO: disable certain widgets 
        return gtk.TRUE
    

    def stop(self, widget):
        """Stop all instrument interface servers.
        """
        if not self.mode:
            self.showStatus("PLEASE SETUP SERVERS FIRST")
            return gtk.TRUE
            
        if self.mode != 'started':
            self.showStatus("PLEASE START SERVERS FIRST")
            return gtk.TRUE
            
        self.soss.stop(wait=True)

        # stop() method above should have set ev_quit flag
        self.mythread.join()
        
        self.mode = 'stopped'

        # TODO: reenable certain widgets 
        return gtk.TRUE


    def send_cmd(self, cmdstr, wait=False, timeout=None):

        if not self.soss:
            raise INSint.INSintError("Servers not started!")
        
        # Bump the command tag
        self.cmdtag += 1
        tag = 'mon.INSint%d.%d' % (self.obcpnum, self.cmdtag)

        try:
            self.soss.send_cmd(tag, cmdstr)

            if wait:
                self.db.get_wait(tag, 'done', timeout=timeout)

        except Exception, e:
            self.showStatus("ERROR: %s" % str(e))
    
            
    def release(self, widget):
        """Releases any waiters on the instrument.
        """
        self.db.releaseAll()
        
        
    def cancel(self, widget):
        """Sends a cancel command to the instrument.
        """
        cmdstr = "EXEC %s CANCEL" % \
                 self.insconfig.getNameByNumber(self.obcpnum)
        self.send_cmd(cmdstr, wait=False)
        
        
    def send_loop(self):
        """Loop for sending commands.  A thread is created in here
        when 'Start' is pressed and stops when 'Stop' is pressed.
        Commands are read from the queue and sent to the instrument
        with the send_cmd() method.  Each command has an associated
        wait flag which tells whether to wait for the command to finish
        before reading the next command from the queue.
        """
        while not self.ev_quit.isSet():
            try:
                cmdb = self.cmdqueue.get(block=False, timeout=0.1)
                
                self.send_cmd(cmdb.cmd, wait=cmdb.wait)

            except Queue.Empty:
                self.ev_quit.wait(0.1)
                

    def send(self, widget):
        """Get the selection from the text box _widget_ and send it as a
        command string to the instrument interface.
        """

        if not self.soss:
            self.showStatus("Servers not started!")
            return gtk.TRUE
        
        sw = self.widgets['cmdtext']
        cmdstr = get_selection_tv(sw)

        # Grab the selected text.  Split along {,;\n} to separate commands.
        # Enqueue each command to the outgoing command queue along with
        # a wait flag.  If a command ends with ',' the wait flag is Falwe
        # in all other cases, the wait flag is True
        rest = cmdstr
        match = re.match(r'^([^,;\n]*)([,;\n])(.*)$', cmdstr, re.DOTALL)
        while match:
            cmd = match.group(1).strip()
            term = match.group(2)
            rest = match.group(3)

            #print "cmd: '%s'" % cmd
            #print "term: '%s'" % term
            #print "rest: '%s'" % rest

            # If command terminator is ',' then don't wait between commands
            wait_flag = not (term == ',')

            # Don't send empty commands
            if len(cmd) != 0:
                self.cmdqueue.put(Bunch.Bunch(cmd=cmd, wait=wait_flag))
            
            match = re.match(r'^([^,;\n]*)([,;\n])(.*)$', rest, re.DOTALL)
            
        cmd = rest.strip()
        if len(cmd) != 0:
            # Last command is always assumed to wait
            self.cmdqueue.put(Bunch.Bunch(cmd=cmd, wait=True))

        return gtk.TRUE


    def checklog(self, queue, widget):
        """Check the log represented by _queue_ and if there is a message
        present, append it to _widget_ (a text box widget).
        """

        if (not self.soss) or (not queue):
            return False
        try:
            msg = queue.get(block=False)
            append_tv(widget, msg + '\n')
            
        except Queue.Empty:
            pass

        return True
            
    def _start_server(self, iface):
            self.soss.start_ifaces([iface])

    def _stop_server(self, iface):
            self.soss.stop_ifaces([iface])

    def on_cmdstart_clicked(self, widget):
        self._start_server('cmd')
        
    def on_cmdstop_clicked(self, widget):
        self._stop_server('cmd')
        
    def on_thrustart_clicked(self, widget):
        self._start_server('thru')
     
    def on_thrustop_clicked(self, widget):
        self._stop_server('thru')
        
    def on_sreqstart_clicked(self, widget):
        self._start_server('sreq')
        
    def on_sreqstop_clicked(self, widget):
        self._stop_server('sreq')
        
    def on_sdststart_clicked(self, widget):
        self._start_server('sdst')
        
    def on_sdststop_clicked(self, widget):
        self._stop_server('sdst')
        
    def on_filestart_clicked(self, widget):
        self._start_server('file')
        
    def on_filestop_clicked(self, widget):
        self._stop_server('file')
        
    def on_btncmd_clear_clicked(self, widget):
        sw = self.widgets['resulttext']
        clear_tv(sw)
        
    def on_btnthru_clear_clicked(self, widget):
        sw = self.widgets['throughtext']
        clear_tv(sw)
        
    def on_btnsreq_clear_clicked(self, widget):
        sw = self.widgets['statusreqtext']
        clear_tv(sw)
        
    def on_btnsdst_clear_clicked(self, widget):
        sw = self.widgets['statusrcvdtext']
        clear_tv(sw)
        
    def on_btnfile_clear_clicked(self, widget):
        sw = self.widgets['fitsrecvtext']
        clear_tv(sw)
        

    def setup(self, widget):
        """Display and run the Setup dialog for configuring obcp info.
        """
        if self.mode == 'started':
            self.showStatus("PLEASE STOP SERVERS FIRST")
            return gtk.TRUE
            
        sw = self.widgets['setup_obcp']
        sw.window.show()
        resp = sw.run()
        sw.window.hide()

        if resp == gtk.RESPONSE_OK:
            # If not CANCEL, then refresh our core parameters from the dialog
            self.obcpnum = self.widgets['obcpnum'].get_value_as_int()
            self.username = self.widgets['username'].get_text()
            self.password = self.widgets['password'].get_text()
            self.obcphost = self.widgets['obcphost'].get_text()
            self.raidpath = self.widgets['raidarea'].get_text()
            self.transfermethod = get_combobox_text(self.widgets['transfermethod'])

            # If user specified a monitor, then create a mini-monitor and
            # sync ourselves to it
            channel_cmd  = 'INSint%d' % self.obcpnum
            channel_file = 'frames'
            
            # Create a new instrument interface object, but don't start it
            self.soss = INSint.ocsInsInt(self.obcpnum, self.obcphost, self.raidpath,
                                         self.statusObj, ev_quit=self.ev_quit,
                                         interfaces=('cmd','thru','sreq','sdst','file'),
                                         monunitnum=self.monunitnum,
                                         transfermethod=self.transfermethod,
                                         username=self.username,
                                         db=None)

            # If user requested to link to an external monitor, do so.
            self.db = self.soss.get_monitor()
            if self.monitor:
                self.db.subscribe(self.monitor, [channel_cmd, channel_file],
                                  None)

            self.mode = 'stopped'
            self.showStatus("Servers configured.")
            
        return gtk.TRUE


    def load_file(self, path):
        """Loads a command file from _path_ into the commands window.
        """
        sw = self.widgets['cmdtext']

        # clear widget
        clear_tv(sw)
        
        # Read in file and append lines to the widget
        in_f = open(path, 'r')
            
        for line in in_f:
            append_tv(sw, line)

        in_f.close()

        
    def load_cmd_file(self, widget):
        """Runs dialog to read in a command file into the command window.
        """
            
        # Throw up a file selection dialog and let the user pick a file
        sw = self.widgets['dialog_filechooser']
        sw.window.show()
        resp = sw.run()
        sw.window.hide()

        # If they clicked "OK" then try to send the file.
        if resp == gtk.RESPONSE_OK:
            filepath = sw.get_filename()
            (filedir, filename) = os.path.split(filepath)
            
            try:
                self.load_file(filepath)

            except IOError, e:
                self.showStatus("Failed to load '%s': %s" % (filename, str(e)))

        else:
            self.showStatus("Load cancelled.")
               
        return gtk.TRUE


    def quit(self, widget):
        """Quit the application.
        """
        if (self.mode) and (self.mode == 'started'):
            self.stop(widget)

        self.ev_mainquit.set()
        return gtk.TRUE


    def showStatus(self, text):
        """Write a message (_text_) to the status bar.
        """
        sw = self.widgets['statusbar1']
        context = sw.get_context_id("status")

        sw.pop(context)
        sw.push(context, text)
        return


def main(options, args):
    """Main program.  _options_ is an OptionParser object that holds parsed
    options.  _args_ is a list of the remaining non-option parameters.
    """

    # Create top level logger.
    logger = ssdlog.make_logger('INSintTester', options)

    # Only import and initialize remoteObjects if we are trying to
    # use Gen2 services
    if options.monitor or options.statussvc:
        ro.init()

    # Create app and display
    app = INSintTester(options, logger)
    app.show()

    # TODO: find a better way to keep these dialogs suppressed at
    # startup.
    sw = app.widgets['setup_obcp']
    sw.window.hide()
    sw = app.widgets['dialog_filechooser']
    sw.window.hide()

    # Enter GUI event-processing loop.
    while not app.ev_mainquit.isSet():
        # Process X events
        while gtk.events_pending():
            gtk.main_iteration()

        # Sleep and let other threads run
        time.sleep(0.25)
    

if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-d", "--fitsdir", dest="fitsdir", metavar="DIR",
                      default=".",
                      help="Use DIR for storing instrument FITS files")
    optprs.add_option("-m", "--monitor", dest="monitor",
                      metavar="NAME",
                      help="Reflect internal status to monitor service NAME")
    optprs.add_option("--monunit", dest="monunitnum", type="int",
                      default=3, metavar="NUM",
                      help="Target OSSL_MonitorUnit NUM on OBS")
    optprs.add_option("--numthreads", dest="numthreads", type="int",
                      default=2,
                      help="Use NUM threads for each interface", metavar="NUM")
    optprs.add_option("--obcphost", dest="obcphost", 
                      help="Use HOST as the OBCP host", metavar="HOST")
    optprs.add_option("-n", "--obcpnum", dest="obcpnum", type="int",
                      default=9,
                      help="Use NUM as the OBCP number", metavar="NUM")
    optprs.add_option("-P", "--password", dest="password", metavar="PASSWORD",
                      default='',
                      help="Use PASSWORD for ftp transfers")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("-s", "--statusfile", dest="statusfile",
                      help="Use FILE for providing SOSS status", metavar="FILE")
    optprs.add_option("--statushost", dest="statushost",
                      help="Use HOST for obtaining SOSS status", metavar="HOST")
    optprs.add_option("--statussvc", dest="statussvc",
                      help="Use SVCNAME for obtaining Gen2 status",
                      metavar="SVCNAME")
    optprs.add_option("-t", "--transfermethod", dest="transfermethod",
                      default="ssh",
                      help="Use METHOD (ftp|rpc|ssh) for transferring FITS files (OBCP must support method)")
    optprs.add_option("-u", "--username", dest="username", metavar="USERNAME",
                      #default=os.getlogin()
                      default=os.environ['LOGNAME'],
                      help="Login as USERNAME@obcp for ftp/ssh transfers")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    if len(args) != 0:
        optprs.error("incorrect number of arguments")


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
       
#END INSintTester.py

#! /usr/bin/env python
# 
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Jul  8 10:59:53 HST 2010
#]

# remove once we're certified on python 2.6
from __future__ import with_statement

import sys, os
import re, time
import threading, Queue
import Tkinter
import Pmw
import ssdlog, logging

import remoteObjects as ro
import remoteObjects.Monitor as Monitor
import Bunch
import cfg.g2soss


class skDisp(object):
    def __init__(self, parent, logger, ev_quit, **kwdargs):

        self.root = parent
        self.logger = logger
        self.ev_quit = ev_quit
        self.__dict__.update(kwdargs)
        self.lock = threading.RLock()

        self.w = Bunch.Bunch()
        
        menubar = Tkinter.Menu(parent, relief='flat')

        # create a pulldown menu, and add it to the menu bar
        filemenu = Tkinter.Menu(menubar, tearoff=0)
        filemenu.add('command', label="Show Log", command=self.showlog)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        optionmenu = Tkinter.Menu(menubar, tearoff=0)
        self.save_decode_result = Tkinter.IntVar(0)
        #self.save_decode_result.set(0)
        optionmenu.add('checkbutton', label="Save Decode Result", 
                       variable=self.save_decode_result)
        self.show_times = Tkinter.IntVar(0)
        #self.show_times.set(0)
        optionmenu.add('checkbutton', label="Show Times", 
                       variable=self.show_times)
        self.audible_errors = Tkinter.IntVar(0)
        self.audible_errors.set(1)
        optionmenu.add('checkbutton', label="Audible Errors", 
                       variable=self.audible_errors)
        menubar.add_cascade(label="Option", menu=optionmenu)

        parent.config(menu=menubar)

        # pop-up log file
        self.w.log = Pmw.TextDialog(parent, scrolledtext_labelpos='n',
                                    title='Log',
                                    buttons=('Close',),
                                    defaultbutton=None,
                                    command=self.closelog)
                                    #label_text = 'Log')        
        self.queue = Queue.Queue()
        guiHdlr = ssdlog.QueueHandler(self.queue)
        fmt = logging.Formatter(ssdlog.STD_FORMAT)
        guiHdlr.setFormatter(fmt)
        guiHdlr.setLevel(logging.INFO)
        self.logger.addHandler(guiHdlr)

        txt = Pmw.NoteBook(parent, tabpos='n')
        self.w.nb = txt
        self.w.nb.pack(padx=5, pady=2, fill='both', expand=1)

        # bottom buttons
        frame = Tkinter.Frame(parent) 
        
        self.w.quit = Tkinter.Button(frame, text="Quit",
                                     width=40,
                                     command=self.quit,
                                     activebackground="#089D20",
                                     activeforeground="#FFFF00")
        self.w.quit.pack(padx=5, pady=4, side=Tkinter.BOTTOM)

        frame.pack()

        self.closelog(self.w.log)

        self.track = {}
        self.pages = {}
        self.pagelist = []
        self.pagelimit = 10
        

    def setPos(self, geom):
        self.root.geometry(geom)

    def closelog(self, w):
        # close log window
        self.w.log.withdraw()
        
    def showlog(self):
        # open log window
         self.w.log.show()

    def logupdate(self):
        try:
            while True:
                msgstr = self.queue.get(block=False)

                self.w.log.insert('end', msgstr + '\n')

        except Queue.Empty:
            self.root.after(200, self.logupdate)
    
    def insert_ast(self, tw, text):

        def insert(text, tags):
            try:
                foo = text.index("<div ")

            except ValueError:
                tw.insert('end', text, tuple(tags))
                return

            match = re.match(r'^\<div\sclass=([^\>]+)\>', text[foo:],
                             re.MULTILINE | re.DOTALL)
            if not match:
                tw.insert('end', 'ERROR 1: %s' % text, tuple(tags))
                return

            num = int(match.group(1))
            regex = r'^(.*)\<div\sclass=%d\>(.+)\</div\sclass=%d\>(.*)$' % (
                num, num)
            #print regex
            match = re.match(regex, text, re.MULTILINE | re.DOTALL)
            if not match:
                tw.insert('end', 'ERROR 2: %s' % text, tuple(tags))
                return

            tw.insert('end', match.group(1), tuple(tags))

            serial_num = '%d' % num
            tw.tag_config(serial_num, foreground="black")
            newtags = [serial_num]
            newtags.extend(tags)
            insert(match.group(2), newtags)

            insert(match.group(3), tags)

        tw.tag_configure('code', foreground="black")
        insert(text, ['code'])
        tw.tag_raise('code')

    def astIdtoTitle(self, ast_id):
        page = self.pages[ast_id]
        return page.title
        
    def delpage(self, ast_id):
        #title = self.astIdtoTitle(ast_id)
        self.w.nb.delete(ast_id)
        del self.pages[ast_id]

    def addpage(self, ast_id, title, text):
        with self.lock:

            # Make room for new pages
            while len(self.pagelist) >= self.pagelimit:
                oldast_id = self.pagelist.pop(0)
                self.delpage(oldast_id)
                
            page = self.w.nb.add(ast_id, tab_text=title)
            #self.w.nb.tab(ast_id).focus_set()
            page.focus_set()

            txt = Pmw.ScrolledText(page, text_wrap='none',
                                   vscrollmode='dynamic', hscrollmode='dynamic')

            tw = txt.component('text')
            tw.configure(background="#FFFFFF", font=(('monospace'), '10'),
                         borderwidth=2, padx=10, pady=5)

            self.insert_ast(tw, text)
            txt.pack(fill='both', expand=True, padx=4, pady=4)

            self.w.nb.setnaturalsize()

            try:
                page = self.pages[ast_id]
                page.tw = tw
                page.title = title
            except KeyError:
                self.pages[ast_id] = Bunch.Bunch(tw=tw, title=title)

            self.pagelist.append(ast_id)
            self.w.nb.selectpage(ast_id)

        
    def parsefile(self, filepath):
        bnch = self.parser.parse_skfile(filepath)
        if bnch.errors == 0:
            (path, filename) = os.path.split(filepath)

            text = self.issue.issue(bnch.ast, [])
            print text
            #print dir(txt)
            self.addpage(filename, filename, text)
            
        
    # callback to quit the program
    def quit(self):
        self.ev_quit.set()
        sys.exit(0)


    def change_text(self, page, ast_num, **kwdargs):
        page.tw.tag_config(ast_num, **kwdargs)
        page.tw.tag_raise(ast_num)
        try:
            page.tw.see('%s.first' % ast_num)
        except KeyError, e:
            # this throws a KeyError due to a bug in Python megawidgets
            # but it is benign
            self.logger.error(str(e))
            pass


    def update_time(self, page, ast_num, vals, time_s):

        if not self.show_times.get():
            return

        if vals.has_key('time_added'):
            length = vals['time_added']
            page.tw.delete('%s.first' % ast_num, '%s.first+%dc' % (ast_num, length))
            
        vals['time_added'] = len(time_s)
        page.tw.insert('%s.first' % ast_num, time_s, (ast_num,))
        

    def audible_warn(self, cmd_str, vals):
        """Called when we get a failed command and should/could issue an audible
        error.  cmd_str, if not None, is the device dependent command that caused
        the error.
        """
        self.logger.debug("Audible warning: %s" % cmd_str)
        if not cmd_str:
            return

        if not self.audible_errors.get():
            return

        cmd_str = cmd_str.lower().strip()
        match = re.match(r'^exec\s+(\w+)\s+.*', cmd_str)
        if not match:
            subsys = 'general'
        else:
            subsys = match.group(1)

        #soundfile = 'g2_err_%s.au' % subsys
        soundfile = 'E_ERR%s.au' % subsys.upper()
        soundpath = os.path.join(cfg.g2soss.producthome, 'file/Sounds', soundfile)
        if os.path.exists(soundpath):
            cmd = "OSST_audioplay %s" % (soundpath)
            self.logger.debug(cmd)
            res = os.system(cmd)
        else:
            self.logger.error("No such audio file: %s" % soundpath)
        

    def update_page(self, bnch):

        page = bnch.page
        vals = bnch.state
        print "vals = %s" % str(vals)
        ast_num = vals['ast_num']

        cmd_str = None
        if vals.has_key('cmd_str'):
            cmd_str = vals['cmd_str']

            if not vals.has_key('inserted'):
                # Replace the decode string with the actual parameters
                pos = page.tw.index('%s.first' % ast_num)
                page.tw.delete('%s.first' % ast_num, '%s.last' % ast_num)
                page.tw.insert(pos, cmd_str, (ast_num,))
                vals['inserted'] = True
                try:
                    del vals['time_added']
                except KeyError:
                    pass

        if vals.has_key('task_error'):
            self.change_text(page, ast_num, foreground="red", background="lightyellow")
            page.tw.insert('%s.last' % ast_num, '\n ==> ' + vals['task_error'],
                           (ast_num,))
            
            # audible warnings
            self.audible_warn(cmd_str, vals)

        elif vals.has_key('task_end'):
            if vals.has_key('task_start'):
                elapsed = vals['task_end'] - vals['task_start']
                self.update_time(page, ast_num, vals, '[ F %9.3f s ]: ' % (
                        elapsed))
            else:
                self.update_time(page, ast_num, vals, '[TE %s]: ' % (
                        self.time2str(vals['task_end'])))
            self.change_text(page, ast_num, foreground="blue4")
                
        elif vals.has_key('end_time'):
            self.update_time(page, ast_num, vals, '[EN %s]: ' % (
                    self.time2str(vals['end_time'])))
            self.change_text(page, ast_num, foreground="blue1")
                
        elif vals.has_key('ack_time'):
            self.update_time(page, ast_num, vals, '[AB %s]: ' % (
                    self.time2str(vals['ack_time'])))
            self.change_text(page, ast_num, foreground="green4")

        elif vals.has_key('cmd_time'):
            self.update_time(page, ast_num, vals, '[CD %s]: ' % (
                    self.time2str(vals['cmd_time'])))
            self.change_text(page, ast_num, foreground="brown")

        elif vals.has_key('task_start'):
            self.update_time(page, ast_num, vals, '[TS %s]: ' % (
                    self.time2str(vals['task_start'])))
            self.change_text(page, ast_num, foreground="gold2")

        else:
            #self.change_text(page, ast_num, foreground="gold2")
            pass

                
    def time2str(self, time_cmd):
        time_int = int(time_cmd)
        time_str = time.strftime("%H:%M:%S", time.localtime(float(time_int)))
        time_sfx = ('%.3f' % (time_cmd - time_int)).split('.')[1]
        title = time_str + ',' + time_sfx
        return title
            
    def process_ast(self, ast_id, vals):
        #print ast_id, vals

        with self.lock:
            try:
                page = self.pages[ast_id]
            except KeyError:
                # this page is not received/set up yet
                page = Bunch.Bunch(vals)
                page.nodes = {}
                self.pages[ast_id] = page

            if vals.has_key('ast_buf'):
                ast_str = ro.binary_decode(vals['ast_buf'])
                # Get the time of the command to construct the tab title
                title = self.time2str(vals['ast_time'])

                # TODO: what if this page has already been deleted?
                if self.save_decode_result.get():
                    self.addpage(ast_id + '.decode', title, ast_str)

                self.addpage(ast_id, title, ast_str)

            elif vals.has_key('ast_track'):
                path = vals['ast_track']

                curvals = self.monitor.getitems_suffixOnly(path)
                if isinstance(curvals, dict):
                    vals.update(curvals)
               
                # Make an entry for this ast node, if there isn't one already
                ast_num = '%d' % vals['ast_num']
                state = page.nodes.setdefault(ast_num, vals)

                bnch = Bunch.Bunch(page=page, state=state)
                self.track.setdefault(vals['ast_track'], bnch)
                
                # Replace the decode string with the actual parameters
                pos = page.tw.index('%s.first' % ast_num)
                page.tw.delete('%s.first' % ast_num, '%s.last' % ast_num)
                page.tw.insert(pos, vals['ast_str'],
                               (ast_num,))

                self.update_page(bnch)
                

    def process_task(self, path, vals):
        #print path, vals

        with self.lock:
            try:
                bnch = self.track[path]
            except KeyError:
                # this page is not received/set up yet
                return

            #print path, vals
            bnch.state.update(vals)

            self.update_page(bnch)
            

    # this one is called if new data becomes available
    def anon_arr(self, payload, name, channels):
        self.logger.debug("received values '%s'" % str(payload))

        try:
            bnch = Monitor.unpack_payload(payload)

        except Monitor.MonitorError:
            self.logger.error("malformed packet '%s': %s" % (
                str(payload), str(e)))
            return

        try:
            ast_id = bnch.value['ast_id']
            return self.process_ast(ast_id, bnch.value)

        except KeyError:
            return self.process_task(bnch.path, bnch.value)
        
        
    def get_cbs(self):
        return self.anon_arr


def main(options, args):
    
    # Create top level logger.
    logger = ssdlog.make_logger('sktask_gui', options)

    ro.init()

    root = Tkinter.Tk()
    Pmw.initialise(root)
    title='Gen2 skTask Viewer'
    root.title(title)

    ev_quit = threading.Event()

    # make a name for our monitor
    myMonName = options.svcname

    # monitor channels we are interested in
    channels = options.channels.split(',')

    # Create a local monitor
    mymon = Monitor.Monitor(myMonName, logger, numthreads=20)

    skdisp = skDisp(root, logger, ev_quit, monitor=mymon,
                    monpath=options.monpath)
    if options.geometry:
        skdisp.setPos(options.geometry)
    skdisp.logupdate()

    # Subscribe our callback functions to the local monitor
    mymon.subscribe_cb(skdisp.anon_arr, channels)
    
    for skfile in args:
        skdisp.parsefile(skfile)

    server_started = False
    try:
        # Startup monitor threadpool
        mymon.start(wait=True)
        # start_server is necessary if we are subscribing, but not if only
        # publishing
        mymon.start_server(wait=True, port=options.port)
        server_started = True

        # subscribe our monitor to the central monitor hub
        mymon.subscribe_remote(options.monitor, channels, ())
    
        try:
            root.mainloop()

        except KeyboardInterrupt:
            logger.error("Received keyboard interrupt!")

    finally:
        if server_started:
            mymon.stop_server(wait=True)
        mymon.stop(wait=True)
    
    logger.info("Exiting Gen2 skTask viewer...")
    skdisp.quit()
    

# Create demo in root window for testing.
if __name__ == '__main__':
  
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-c", "--channels", dest="channels", default='taskmgr0,g2task',
                      metavar="LIST",
                      help="Subscribe to the comma-separated LIST of channels")
    optprs.add_option("--display", dest="display", metavar="HOST:N",
                      help="Use X display on HOST:N")
    optprs.add_option("-g", "--geometry", dest="geometry",
                      metavar="GEOM", default="963x1037+0+57",
                      help="X geometry for initial size and placement")
    optprs.add_option("-m", "--monitor", dest="monitor", default='monitor',
                      metavar="NAME",
                      help="Subscribe to feeds from monitor service NAME")
    optprs.add_option("-p", "--path", dest="monpath", default='mon.sktask',
                      metavar="PATH",
                      help="Show values for PATH in monitor")
    optprs.add_option("--port", dest="port", type="int", default=10013,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("-n", "--svcname", dest="svcname", default='monwatch',
                      metavar="NAME",
                      help="Use NAME as our subscriber name")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

##     if len(args) != 0:
##         optprs.error("incorrect number of arguments")

    if options.display:
        os.environ['DISPLAY'] = options.display

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


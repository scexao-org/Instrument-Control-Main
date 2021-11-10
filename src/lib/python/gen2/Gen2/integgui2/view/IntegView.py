# 
# Eric Jeschke (eric@naoj.org)
#

# Standard library imports
import sys, os, glob
import re
import thread, threading, Queue
import traceback

# Special library imports
import pygtk
pygtk.require('2.0')
import gtk, gobject

# SSD/Gen2 imports
from ginga.misc import Bunch, Future

# Local integgui2 imports
import common
from pages import *
import Page as PG
import Workspace as WS
import dialogs

# Parse our gtk resource file
thisDir = os.path.split(sys.modules[__name__].__file__)[0]
rc_file = os.path.join(thisDir, "gtk_rc")
gtk.rc_parse(rc_file) 

# Formatting string used to format History table
fmt_history = "%(t_start)s  %(t_end)s  %(t_elapsed)7.7s %(result)s %(queue)8.8s  %(cmdstr)s"


class IntegView(object):

    def __init__(self, logger, ev_quit, queues, logtype='normal'):

        self.logger = logger
        self.ev_quit = ev_quit
        self.queue = queues
        self.logtype = logtype
        self.lock = threading.RLock()
        # Used for tagging commands
        self.cmdcount = 0
        # ugh--ugly race condition hack
        common.set_view(self)

        self.gui_queue = Queue.Queue()
        self.placeholder = '--notdone--'
        self.gui_thread_id = None

        # Options that can be set graphically
        self.audible_errors = True
        self.suppress_confirm_exec = True
        self.embed_dialogs = False
        self.clear_obs_info = True

        # This is the home directory for loading all kinds of files
        self.procdir = None
        # This is the list of directories to search for include
        # (e.g. PRM) files named by other files
        self.include_dirs = []

        # Set default location, until changed
        procdir = os.path.join(os.environ['HOME'], 'Procedure')
        self.set_procdir(procdir, 'SUKA')
        
        # Create the GUI
        self.w = Bunch.Bunch()

        # hack required to use threads with GTK
        gobject.threads_init()
        gtk.gdk.threads_init()

        # Create top-level window
        root = gtk.Window(gtk.WINDOW_TOPLEVEL)
        root.set_size_request(1900, 1050)
        root.set_title('Gen2 Integrated GUI II')
        root.connect("delete_event", self.delete_event)
        root.set_border_width(2)

        # These are sometimes needed
        self.display = gtk.gdk.display_manager_get().get_default_display()
        self.clipboard = gtk.Clipboard(self.display, "CLIPBOARD")

        # create main frame
        self.w.mframe = gtk.VBox(spacing=2)
        root.add(self.w.mframe)
        #self.w.mframe.show()

        self.w.root = root

        self.w.menubar = gtk.MenuBar()
        self.w.mframe.pack_start(self.w.menubar, expand=False)

        # Create a "desktop" the holder for workspaces
        self.ds = Desktop(self.w.mframe, 'desktop', 'IntegGUI Desktop')
        # Some attributes we force on our children
        self.ds.logger = self.logger

        self.add_statusbar()
        
        # Add workspaces
        self.ojws = self.ds.addws('ul', 'obsjrn', "Upper Left Workspace")
        self.oiws = self.ds.addws('ur', 'obsinfo', "Upper Right Workspace")
        self.umws = self.ds.addws('um', 'umws', "Upper Middle Workspace")
        self.lmws  = self.ds.addws('lm', 'lmws', "Lower Middle Workspace")
        self.lws  = self.ds.addws('ll', 'launchers', "Lower Left Workspace")
        self.exws = self.ds.addws('lr', 'executor', "Lower Right Workspace")

        # Populate "Observation Journal" ws
        self.add_frameinfo(self.ojws)
        #self.ojws.addpage('statmon', "StatMon", StatMonPage)

        # Populate "Lower Middle" ws
        self.handsets = self.lmws.addpage('handset', "Handset",
                                         WorkspacePage.WorkspacePage)
        self.queuepage = self.lmws.addpage('queues', "Queues",
                                           WorkspacePage.WorkspacePage)
        self.add_queue(self.queuepage, 'default', create=False)
        self.add_tagpage(self.lmws)
        self.dialogs = self.lmws.addpage('dialogs', "Dialogs",
                                         WorkspacePage.WorkspacePage)
        self.lmws.select('queues')

        # Populate "Observation Info" ws
        self.add_obsinfo(self.oiws)
        self.add_monitor(self.oiws)
        self.logpage = self.oiws.addpage('loginfo', "Logs",
                                         WorkspacePage.WorkspacePage)
        # self.fitspage = self.oiws.addpage('fitsview', "Fits",
        #                                   WorkspacePage.WorkspacePage)
        # self.fitspage.addpage('viewer', 'Fits Viewer',
        #                       FitsViewerPage)
        self.add_history(self.oiws)
        self.oiws.select('obsinfo')

        # Populate "Command Executors" ws
        self.add_terminal(self.exws)
        self.new_source('command', self.exws, title='Commands')
        
        self.add_dialogs()
        self.add_menus(self.w.menubar)

        self.w.root.show_all()

    # Define some functions that depend on the workspace
    def raise_page(self, name):
        ws, page = self.ds.getPage(name)
        self.ds.show_ws(ws.name)
        ws.select(name)

    def lower_page(self, name):
        ws, page = self.ds.getPage(name)
        self.ds.restore_ws(ws.name)

    def raise_page_transient(self, name):
        ws, page = self.ds.getPage(name)
        self.ds.show_ws(ws.name)
        ws.showTransient(name)

    def lower_page_transient(self, name):
        ws, page = self.ds.getPage(name)
        ws.hideTransient(name)
        self.ds.restore_ws(ws.name)

    def toggle_var(self, widget, key):
        if widget.active: 
            self.__dict__[key] = True
        else:
            self.__dict__[key] = False

    def set_procdir(self, path, inst):
        topprocdir = common.topprocdir
        inst = inst.upper()

        if not os.path.isdir(path):
            path = os.path.join(topprocdir, inst)
            if not os.path.isdir(path):
                path = topprocdir
            
        self.procdir = path

        # Calculate list of include directories for this path
        # TODO: add a graphical way to modify this
        self.include_dirs = [
            path,
            os.path.join(path, 'COMMON'),
            os.path.join(topprocdir, inst),
            os.path.join(topprocdir, inst, 'COMMON'),
            os.path.join(topprocdir, 'COMMON'),
            ]
        
    def add_menus(self, menubar):

        # create a File pulldown menu, and add it to the menu bar
        filemenu = gtk.Menu()
        file_item = gtk.MenuItem(label="File")
        menubar.append(file_item)
        file_item.show()
        file_item.set_submenu(filemenu)

        # Add all the different kind of loaders to load up into these
        # default workspaces
        d = {'executers': self.exws,
             'launchers': self.lws,
             'journals': self.ojws,
             'logs': self.logpage,
             #'fits': self.fitspage,
             'handsets': self.handsets,
             'queues': self.queuepage,
            }
        self.add_load_menus(filemenu, d)
        
        item = gtk.MenuItem(label="Config from session")
        filemenu.append(item)
        item.connect_object ("activate", lambda w: self.reconfig(),
                             "file.Config from session")
        item.show()

        sep = gtk.SeparatorMenuItem()
        filemenu.append(sep)
        sep.show()
        quit_item = gtk.MenuItem(label="Exit")
        filemenu.append(quit_item)
        quit_item.connect_object ("activate", self.quit, "file.exit")
        quit_item.show()

        # create an Option pulldown menu, and add it to the menu bar
        optionmenu = gtk.Menu()
        option_item = gtk.MenuItem(label="Option")
        menubar.append(option_item)
        option_item.show()
        option_item.set_submenu(optionmenu)

        w = gtk.CheckMenuItem("Audible Errors")
        w.set_active(self.audible_errors)
        optionmenu.append(w)
        w.connect("activate", lambda w: self.toggle_var(w, 'audible_errors'))

        w = gtk.CheckMenuItem("Suppress 'Confirm Execute' popups")
        w.set_active(self.suppress_confirm_exec)
        optionmenu.append(w)
        w.connect("activate", lambda w: self.toggle_var(w, 'suppress_confirm_exec'))

        w = gtk.CheckMenuItem("Embed dialogs")
        w.set_active(self.embed_dialogs)
        optionmenu.append(w)
        w.connect("activate", lambda w: self.toggle_var(w, 'embed_dialogs'))

        w = gtk.CheckMenuItem(label="Clear info on Config")
        w.set_active(self.clear_obs_info)
        optionmenu.append(w)
        w.connect("activate", lambda w: self.toggle_var(w, 'clear_obs_info'))

        # create a Queue pulldown menu, and add it to the menu bar
        queuemenu = gtk.Menu()
        item = gtk.MenuItem(label="Queue")
        menubar.append(item)
        item.show()
        item.set_submenu(queuemenu)

        item = gtk.MenuItem(label="New queue ...")
        queuemenu.append(item)
        item.connect_object ("activate", lambda w: self.gui_create_queue(self.queuepage),
                             "queue.Create queue")
        item.show()


    def add_load_menus(self, filemenu, where):

        def _get_ws(bnch, name, where):
            if isinstance(where, WS.Workspace):
                bnch[name] = where
            ## elif isinstance(where, Desktop):
            ##     bnch[name] = where.getws(name)
            elif isinstance(where, dict):
                bnch[name] = where[name]
            else:
                raise Exception("I don't know how to find the workspace '%s' in %s" % (
                name, where))

        ws = Bunch.Bunch()
        
        loadmenu = gtk.Menu()
        item = gtk.MenuItem(label="Load source")
        filemenu.append(item)
        item.show()
        item.set_submenu(loadmenu)

        _get_ws(ws, 'executers', where)
        
        item = gtk.MenuItem(label="ope")
        loadmenu.append(item)
        item.connect_object ("activate", lambda w: self.gui_load_ope(ws.executers),
                             "file.Load ope")
        item.show()

        item = gtk.MenuItem(label="sk")
        loadmenu.append(item)
        item.connect_object ("activate", lambda w: self.gui_load_sk(ws.executers),
                             "file.Load sk")
        item.show()

        item = gtk.MenuItem(label="task")
        loadmenu.append(item)
        item.connect_object ("activate", lambda w: self.gui_load_task(ws.executers),
                             "file.Load task")
        item.show()

        item = gtk.MenuItem(label="launcher")
        loadmenu.append(item)
        item.connect_object ("activate", lambda w: self.gui_load_launcher_source(ws.executers),
                             "file.Load launcher")
        item.show()

        item = gtk.MenuItem(label="handset")
        loadmenu.append(item)
        item.connect_object ("activate", lambda w: self.gui_load_handset_source(ws.executers),
                             "file.Load handset")
        item.show()

        item = gtk.MenuItem(label="inf")
        loadmenu.append(item)
        item.connect_object ("activate", lambda w: self.gui_load_inf(ws.executers),
                             "file.Load inf")
        item.show()

        item = gtk.MenuItem(label="eph")
        loadmenu.append(item)
        item.connect_object ("activate", lambda w: self.gui_load_ephem(ws.executers),
                             "file.Load eph")
        item.show()

        item = gtk.MenuItem(label="tsc track")
        loadmenu.append(item)
        item.connect_object ("activate", lambda w: self.gui_load_tscTrack(ws.executers),
                             "file.Load tsc")
        item.show()

        loadmenu = gtk.Menu()
        item = gtk.MenuItem(label="Load")
        filemenu.append(item)
        item.show()
        item.set_submenu(loadmenu)

        item = gtk.MenuItem(label="directory")
        loadmenu.append(item)
        item.connect_object ("activate", lambda w: self.gui_load_folder(ws.executers, '*'),
                             "file.Load dir")
        item.show()

        # _get_ws(ws, 'fits', where)
        # item = gtk.MenuItem(label="fits")
        # loadmenu.append(item)
        # item.connect_object ("activate", lambda w: self.gui_load_fits(ws.fits),
        #                      "file.Load fits")
        # item.show()

        _get_ws(ws, 'launchers', where)

        item = gtk.MenuItem(label="launcher")
        loadmenu.append(item)
        item.connect_object ("activate", lambda w: self.gui_load_launcher(ws.launchers),
                             "file.Load launcher")
        item.show()

        _get_ws(ws, 'handsets', where)

        item = gtk.MenuItem(label="handset")
        loadmenu.append(item)
        item.connect_object ("activate", lambda w: self.gui_load_handset(ws.handsets),
                             "file.Load handset")
        item.show()

        _get_ws(ws, 'logs', where)

        item = gtk.MenuItem(label="log")
        loadmenu.append(item)
        item.connect_object ("activate", lambda w: self.gui_load_log(ws.logs),
                             "file.Load log")
        item.show()
        
        item = gtk.MenuItem(label="monlog")
        loadmenu.append(item)
        item.connect_object ("activate", lambda w: self.gui_load_monlog(ws.logs),
                             "file.Load mon log")
        item.show()
        
        # "New" submenu
        newmenu = gtk.Menu()
        item = gtk.MenuItem(label="New")
        filemenu.append(item)
        item.show()
        item.set_submenu(newmenu)

        # New->Source sub-sub-menu
        newsrcmenu = gtk.Menu()
        item = gtk.MenuItem(label="Source")
        newmenu.append(item)
        item.show()
        item.set_submenu(newsrcmenu)

        item = gtk.MenuItem(label="Command page")
        newsrcmenu.append(item)
        item.connect_object ("activate", lambda w: self.new_source('command',
                                                                   ws.executers),
                             "file.New command page")
        item.show()

        item = gtk.MenuItem(label="OPE file")
        newsrcmenu.append(item)
        item.connect_object ("activate", lambda w: self.new_source('ope',
                                                                   ws.executers),
                             "file.New ope page")
        item.show()

        # end of New->Source
        
        item = gtk.MenuItem(label="Terminal page")
        newmenu.append(item)
        item.connect_object ("activate", lambda w: self.add_terminal(ws.executers),
                             "file.New terminal")
        item.show()
        
        _get_ws(ws, 'queues', where)

        item = gtk.MenuItem(label="Queue ...")
        newmenu.append(item)
        item.connect_object ("activate", lambda w: self.gui_create_queue(ws.queues),
                             "file.New queue")
        item.show()

        _get_ws(ws, 'journals', where)

        item = gtk.MenuItem(label="Workspace ...")
        newmenu.append(item)
        item.connect_object ("activate", lambda w: self.gui_create_workspace(ws.journals),
                             "file.New Workspace")
        item.show()


    def add_dialogs(self):
        self.filesel = dialogs.FileSelection(action=gtk.FILE_CHOOSER_ACTION_OPEN)
        self.filesave = dialogs.FileSelection(action=gtk.FILE_CHOOSER_ACTION_SAVE)


    def add_statusbar(self):
        hbox = gtk.HBox()
        btns = gtk.HButtonBox()

        btns.set_layout(gtk.BUTTONBOX_START)
        btns.set_spacing(5)

        self.btn_kill = gtk.Button("Kill")
        self.btn_kill.connect("clicked", lambda w: self.kill())
        self.btn_kill.modify_bg(gtk.STATE_NORMAL,
                                common.launcher_colors['killbtn'])

        btns.pack_end(self.btn_kill, fill=False, expand=False, padding=4)

        hbox.pack_end(btns, fill=False, expand=False, padding=4)

        # TODO: should we use a TextWidget so we can use tags?
        self.w.status = gtk.Label("")

        hbox.pack_start(self.w.status, fill=True, expand=True,
                        padding=4)

        hbox.show_all()
        self.w.mframe.pack_end(hbox, expand=False, fill=True)


    def statusMsg(self, format, *args):
        if not format:
            msgstr = ''
        else:
            msgstr = format % args

        self.w.status.set_text(msgstr)

    def setPos(self, geom):
        # TODO: currently does not seem to be honoring size request
        match = re.match(r'^(?P<size>\d+x\d+)?(?P<pos>[\-+]\d+[\-+]\d+)?$',
                         geom)
        if not match:
            return
        
        size = match.group('size')
        pos = match.group('pos')

        if size:
            match = re.match(r'^(\d+)x(\d+)$', size)
            if match:
                width, height = map(int, match.groups())
                self.w.root.set_default_size(width, height)

        # TODO: placement
        if pos:
            pass

        #self.root.set_gravity(gtk.gdk.GRAVITY_NORTH_WEST)
        ##width, height = window.get_size()
        ##window.move(gtk.gdk.screen_width() - width, gtk.gdk.screen_height() - height)
        # self.root.move(x, y)


#     def set_controller(self, controller):
#         self.controller = controller

    def popup_error(self, errstr):
        w = gtk.MessageDialog(flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                              type=gtk.MESSAGE_WARNING,
                              buttons=gtk.BUTTONS_OK,
                              message_format=errstr)
        #w.connect("close", self.close)
        w.connect("response", lambda w, id: w.destroy())
        w.set_title('IntegGUI Error')
        w.show()


    def popup_confirm(self, title, qstr, f_res, *args, **kwdargs):
        w = gtk.MessageDialog(flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                              type=gtk.MESSAGE_QUESTION,
                              buttons=gtk.BUTTONS_YES_NO,
                              message_format=qstr)
        w.set_title(title)

        def f(w, rsp):
            w.destroy()
            res = 'no'
            if rsp == gtk.RESPONSE_YES:
                res = 'yes'
            f_res(res, *args, **kwdargs)
            
        w.connect("response", f)
        w.show()

    def popup_info(self, title, qstr):
        w = gtk.MessageDialog(flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                              type=gtk.MESSAGE_INFO,
                              message_format=qstr)
        w.set_title(title)
        w.show()
        return w

    def readfile(self, filepath):
        in_f = open(filepath, 'r')
        buf = in_f.read()
        in_f.close()

        return buf

    def popup_select(self, title, execfn, filedir):
        self.filesel.popup(title, execfn, initialdir=filedir)

    def popup_save(self, title, execfn, filedir, filename=None):
        self.filesave.popup(title, execfn, initialdir=filedir,
                            filename=filename)

    def add_terminal(self, workspace):
        try:
            os.chdir(os.path.join(os.environ['HOME'], 'Procedure'))
            #os.chdir(os.environ['HOME'])

            name = 'Terminal'
            page = workspace.addpage(name, name, TerminalPage)

            # Bring shell tab to front
            workspace.select(page.name)
            return page

        except Exception, e:
            self.popup_error("Cannot start terminal: %s" % (str(e)))
            return None

    def gui_load_monlog(self, workspace):

        def pick_log(w, rsp, cbox, names):
            logName = names[cbox.get_active()].strip()
            w.hide()
            if rsp == gtk.RESPONSE_OK:
                self.load_monlog(workspace, logName)
            return True
            
        dialog = gtk.MessageDialog(flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                                   type=gtk.MESSAGE_QUESTION,
                                   buttons=gtk.BUTTONS_OK_CANCEL,
                                   message_format="Select a log to view")
        dialog.set_title("Choose Log")
        # Add a combo box to the content area containing the names of the
        # logs
        vbox = dialog.get_content_area()
        cbox = gtk.combo_box_new_text()
        index = 0
        names = list(common.controller.valid_monlogs)
        names.sort()
        for name in names:
            cbox.insert_text(index, name)
            index += 1
        cbox.set_active(0)
        vbox.add(cbox)
        cbox.show()
        dialog.connect("response", pick_log, cbox, names)
        dialog.show()
        return True

    def load_monlog(self, workspace, logname):
        try:
            try:
                page = workspace.getPage(logname)
                raise Exception("There is already a log open by that name!")
            except KeyError:
                pass
            page = workspace.addpage(logname, logname, MonLogPage)

            # Add standard error regex matching
            page.add_regexes(common.error_regexes)
            
            # Bring log tab to front
            workspace.select(page.name)
            return page

        except Exception, e:
            self.popup_error("Cannot load log '%s': %s" % (
                    logname, str(e)))
            return None


    def gui_load_log(self, workspace):
        initialdir = os.path.abspath(os.environ['LOGHOME'])
        
        self.filesel.popup("Follow log",
                           lambda filepath: self.load_log(workspace, filepath),
                           initialdir=initialdir)

    def load_log(self, workspace, filepath):
        try:
            dirname, filename = os.path.split(filepath)
            # Drop ".log" from tab names
            filepfx, filesfx = os.path.splitext(filename)
            if filesfx.lower() == '.log':
                filename = filepfx

            name = filename
            page = workspace.addpage(name, name, LogPage)

            # Add standard error regex matching
            page.add_regexes(common.error_regexes)
            
            page.load(filepath)

            # Bring log tab to front
            workspace.select(page.name)
            return page

        except Exception, e:
            self.popup_error("Cannot load '%s': %s" % (
                    filepath, str(e)))
            return None


    def gui_load_ope(self, workspace):
        #initialdir = os.path.join(os.environ['HOME'], 'Procedure')
        initialdir = self.procdir
        self.filesel.popup("Load OPE file",
                           lambda filepath: self.load_generic(workspace,
                                                              filepath,
                                                              # ???!!!
                                                              OpePage.OpePage),
                           initialdir=initialdir)

    def gui_load_sk(self, workspace):
        initialdir = os.environ['OBSHOME']
        
        self.filesel.popup("Load skeleton file",
                           lambda filepath: self.load_generic(workspace,
                                                              filepath,
                                                              SkPage),
                           initialdir=initialdir)

    def gui_load_task(self, workspace):
        initialdir = os.environ['OBSHOME']
        
        self.filesel.popup("Load python task",
                           lambda filepath: self.load_generic(workspace,
                                                              filepath,
                                                              TaskPage),
                           initialdir=initialdir)

    def gui_load_folder(self, workspace, pattern):
        initialdir = self.procdir
        self.filesel.popup("Load folder",
                           lambda dirpath: self.load_folder(workspace,
                                                             dirpath,
                                                             pattern=pattern),
                           initialdir=initialdir)

    def gui_load_inf(self, workspace):
        initialdir = os.path.join(os.environ['HOME'], 'Procedure',
                                  'COMICS')
        
        self.filesel.popup("Load inf file",
                           lambda filepath: self.load_generic(workspace,
                                                              filepath,
                                                              InfPage),
                           initialdir=initialdir)

    def gui_load_ephem(self, workspace):
        initialdir = os.path.join(os.environ['HOME'], 'Procedure')
        
        self.filesel.popup("Load eph file",
                           lambda filepath: self.load_generic(workspace,
                                                              filepath,
                                                              EphemPage),
                           initialdir=initialdir)

    def gui_load_tscTrack(self, workspace):
        initialdir = os.path.join(os.environ['HOME'], 'Procedure')
        
        self.filesel.popup("Load TSC Tracking Coordinate file",
                           lambda filepath: self.load_generic(workspace,
                                                              filepath,
                                                              TSCTrackPage),
                           initialdir=initialdir)

    def gui_load_launcher_source(self, workspace):
        initialdir = os.environ['OBSHOME']
        
        self.filesel.popup("Load launcher source",
                           lambda filepath: self.load_generic(workspace,
                                                              filepath,
                                                              # ???!!!
                                                              CodePage.CodePage),
                           initialdir=initialdir)

    def gui_load_handset_source(self, workspace):
        initialdir = os.environ['OBSHOME']
        
        self.filesel.popup("Load handset source",
                           lambda filepath: self.load_generic(workspace,
                                                              filepath,
                                                              # ???!!!
                                                              CodePage.CodePage),
                           initialdir=initialdir)


    def open_generic(self, workspace, buf, filepath, pageKlass,
                     title=None):
        try:
            dirname, filename = os.path.split(filepath)
            #print pageKlass

            name = filename
            if not title:
                title = name
            page = workspace.addpage(name, title, pageKlass)
            page.load(filepath, buf)

            workspace.select(page.name)
            return page

        except Exception, e:
            self.popup_error("Cannot load '%s': %s" % (
                    filepath, str(e)))
            return None


    def kill(self):
        controller = common.controller
        controller.tm_restart()

    def load_ope(self, filepath):
        return self.load_generic(self.exws, filepath, OpePage.OpePage)

    def load_inf(self, filepath):
        return self.load_generic(self.exws, filepath, InfPage)

    def load_ephem(self, filepath):
        return self.load_generic(self.exws, filepath, EphemPage)

    def load_tscTrack(self, filepath):
        return self.load_generic(self.exws, filepath, TSCTrackPage)

    def load_file(self, filepath):
        if os.path.isdir(filepath):
            return self.load_folder(self.exws, filepath)
        else:
            pfx, ext = os.path.splitext(filepath)
            ext = ext.lower()[1:]
            try:
                d = {'ope': OpePage.OpePage,
                     'cd': OpePage.OpePage,
                     'sk': SkPage,
                     'py': TaskPage,
                     'inf': InfPage,
                     'eph': EphemPage,
                     'tsc': TSCTrackPage,
                     }
                pageKlass = d[ext]
            except KeyError:
                pageKlass = CodePage.CodePage

            return self.load_generic(self.exws, filepath, pageKlass)

    def load_generic(self, workspace, filepath, pageKlass):
        try:
            buf = self.readfile(filepath)

            return self.open_generic(workspace, buf, filepath, pageKlass)

        except Exception, e:
            self.popup_error("Cannot load '%s': %s" % (
                    filepath, str(e)))


    def load_folder(self, workspace, dirpath, pattern='*'):
        try:
            pathpfx, dirname = os.path.split(dirpath)

            page = workspace.addpage(dirpath, dirname, DirectoryPage)
            page.load(dirpath, pattern)
            workspace.select(page.name)
            return page

        except Exception, e:
            self.popup_error("Cannot load directory '%s': %s" % (
                    dirpath, str(e)))
            return None


    def gui_load_launcher(self, workspace):
        initialdir = os.environ['OBSHOME']
        
        self.filesel.popup("Load launcher",
                           lambda filepath: self.load_launcher(workspace,
                                                               filepath),
                           initialdir=initialdir)


    def load_launcher(self, workspace, filepath):
        try:
            buf = self.readfile(filepath)

            dirname, filename = os.path.split(filepath)

            match = re.match(r'^(.+)\.yml$', filename)
            if not match:
                return

            name = match.group(1).replace('_', ' ')
            page = workspace.addpage(name, name, LauncherPage,
                                     adjname=False)
            page.load(buf)
            workspace.select(page.name)
            return page

        except Exception, e:
            self.popup_error("Cannot load '%s': %s" % (
                    filepath, str(e)))
            return None


    def gui_load_handset(self, workspace):
        initialdir = os.environ['OBSHOME']
        
        self.filesel.popup("Load handset",
                           lambda filepath: self.load_handset(workspace,
                                                              filepath),
                           initialdir=initialdir)


    def load_handset(self, workspace, filepath):
        try:
            buf = self.readfile(filepath)

            dirname, filename = os.path.split(filepath)

            match = re.match(r'^(.+)\.yml$', filename)
            if not match:
                return None

            name = match.group(1).replace('_', ' ')
            page = workspace.addpage(name, name, HandsetPage,
                                     adjname=False)
            page.load(buf)
            workspace.select(page.name)
            return page

        except Exception, e:
            self.popup_error("Cannot load '%s': %s" % (
                    filepath, str(e)))
            return None


    def new_source(self, pagetype, workspace, title=None):
        if pagetype == 'command':
            buf = ":COMMAND\n# paste or type commands below\n\n"
            ext = '.cd'
            pageKlass = OpePage.OpePage
        elif pagetype == 'ope':
            buf = """
:HEADER
:PARAMETER
# targets and definitions here

:COMMAND
# paste or type commands below
"""
            ext = '.ope'
            pageKlass = OpePage.OpePage

        filename = time.strftime("%Y%m%d-%H%M%S", time.localtime())
        filename = filename + ext
        filepath = os.path.join(self.procdir, filename)

        return self.open_generic(workspace, buf, filepath, pageKlass,
                                 title=title)

    def add_history(self, workspace):
        try:
            page = workspace.addpage('history', "History", LogPage)
            # TODO: add toggling of editing
            page.set_editable(True)

            # mark command errors
            regexes = [
                (re.compile(r'^[\d:]+\s+[\d:]+\s+[\d\.s]+\sCN\s+'),
                 ['cancel']),
                (re.compile(r'^[\d:]+\s+[\d:]+\s+[\d\.s]+\sNG\s+'),
                 ['error']),
                ]
            page.add_regexes(regexes)

            # Global side effect--for now we can only have one history page
            self.history = page
            workspace.select(page.name)
            return page

        except Exception, e:
            self.popup_error("Cannot load history page: %s" % (
                    str(e)))
            return None
        
    ## def add_history(self, workspace):
    ##     try:
    ##         page = workspace.addpage('history', "History", TablePage.TablePage)
    ##         columns = [("Time start", 't_start', 'text'),
    ##                    ("Time stop", 't_end', 'text'),
    ##                    ("Elapsed", 't_elapsed', 'text'),
    ##                    ("TM Queue", 'queue', 'text'),
    ##                    ("", 'icon', 'icon'),
    ##                    ("Result", 'result', 'text'),
    ##                    ("Command", 'cmdstr', 'text'),]
    ##         page.set_columns(columns)

    ##         # Global side effect--for now we can only have one history page
    ##         self.history = page
    ##         workspace.select(page.name)
    ##         return page

    ##     except Exception, e:
    ##         self.popup_error("Cannot load history page: %s" % (
    ##                 str(e)))
    ##         return None
        
    def add_tagpage(self, workspace):
        try:
            page = workspace.addpage('tags', "Tags", TagPage)

            # Global side effect--for now we can only have one tag page
            self.tagpage = page
            workspace.select(page.name)
            return page

        except Exception, e:
            self.popup_error("Cannot load tag page: %s" % (
                    str(e)))
            return None
        
    def add_frameinfo(self, workspace):
        try:
            page = workspace.addpage('frames', "Frames", FrameInfoPage)
            # TODO: add toggling of editing
            #page.set_editable(True)

            # Global side effect--for now we can only have one frame info page
            self.framepage = page
            workspace.select(page.name)
            return page

        except Exception, e:
            self.popup_error("Cannot load frame info page: %s" % (
                    str(e)))
            return None
        
    def add_obsinfo(self, workspace):
        try:
            page = workspace.addpage('obsinfo', "Obsinfo", ObsInfoPage)

            # Global side effect--for now we can only have one obs info page
            self.obsinfo = page
            workspace.select(page.name)
            return page

        except Exception, e:
            self.popup_error("Cannot load obs info page: %s" % (
                    str(e)))
            return None
        
    def add_monitor(self, workspace):
        try:
            page = workspace.addpage('moninfo', "Monitor", SkMonitorPage)

            # Global side effect--for now we can only have one monitor page
            self.monpage = page
            workspace.select(page.name)
            return page

        except Exception, e:
            self.popup_error("Cannot load monitor page: %s" % (
                    str(e)))
            return None
        
    def get_launcher_paths(self, insname, launcherpfx):
        insname = insname.upper()
        filename = '%s*.yml' % launcherpfx
        pathmatch = os.path.join(os.environ['OBSHOME'], insname,
                                 'launcher', filename)

        res = glob.glob(pathmatch)
        return res
        
    def get_file_paths_workspace(self, workspace, regex=None):
        """This returns a list of all the paths of files loaded into
        windows in workspace, that match regular expression _regex_.
        """
        res = []
        for page in workspace.getPages():
            if hasattr(page, 'get_filepath'):
                path = page.get_filepath()
                if (not regex) or re.match(regex, path):
                    res.append(path)
        return res
        
    def get_file_paths_desktop(self, desktop, regex=None):
        res = []
        for ws in desktop.getWorkspaces():
            res.extend(self.get_file_paths_workspace(ws, regex=regex))

        return res
            
    def get_ope_paths(self):
        return self.get_file_paths_desktop(self.ds, regex='^.*\.(ope|OPE)$')
    
    def create_dialog(self, name, title):
        try:
            try:
                page = self.dialogs.getPage(name)
                raise Exception("There is already a paage open by that name!")
            except KeyError:
                pass
            page = self.dialogs.addpage(name, title, DialogPage)

            # Bring tab to front
            self.dialogs.select(page.name)
            return page

        except Exception, e:
            self.popup_error("Cannot create dialog '%s': %s" % (
                    title, str(e)))
            return None

    def close_pages_workspace(self, workspace, pageKlass, exclude=[]):
        try:
            for page in workspace.getPages():
                if isinstance(page, pageKlass) and \
                       (not page.name in exclude):
                    self.logger.debug("closing page '%s'" % (page.name))
                    page.close()

                elif isinstance(page, WorkspacePage.WorkspacePage):
                    # Recurse into workspace pages
                    self.close_pages_workspace(page, pageKlass, exclude=exclude)

        except Exception, e:
            self.logger.error("Error closing pages: %s" % str(e))
            
    def close_pages_desktop(self, desktop, pageKlass, exclude=[]):
        for ws in desktop.getWorkspaces():
            self.close_pages_workspace(ws, pageKlass, exclude=exclude)

    def close_pages(self, pageKlass, exclude=[]):
        self.close_pages_desktop(self.ds, pageKlass)
            
    def close_launchers(self):
        return self.close_pages(LauncherPage)

    def close_handsets(self):
        return self.close_pages(HandsetPage)

    def close_logs(self):
        if self.logtype == 'monlog':
            return self.close_pages(MonLogPage)
        self.close_pages_workspace(self.logpage, LogPage)

    def reconfig(self):
        self.close_logs()
        self.close_handsets()
        self.close_launchers()

        if self.clear_obs_info:
            self.clear_observation()

        try:
            common.controller.ctl_do(common.controller.config_from_session,
                                     'main')
        except Exception, e:
            self.gui.popup_error("Failed to initialize from session: %s" % (
                str(e)))

    def clear_observation(self):

        # Clear some pages
        for name in ('history', 'frames', 'tags', 'moninfo'):
            try:
                ws, page = self.ds.getPage(name)
                page.clear()
            except:
                # possibly they don't have this page open
                pass
            
        # TODO: breaks abstraction to know that the controller has this.
        # Fix!
        #common.controller.fits.clear()


    def get_handset_paths(self, insname, handsetpfx):
        insname = insname.upper()
        filename = '%s*.yml' % handsetpfx
        pathmatch = os.path.join(os.environ['OBSHOME'], insname,
                                 'handset', filename)

        res = glob.glob(pathmatch)
        return res
        
    def get_log_path(self, insname):
        filename = '%s.log' % insname
        filepath = os.path.join(os.environ['LOGHOME'], filename)
        return filepath

    # def gui_load_fits(self, workspace):
    #     initialdir = os.environ['DATAHOME']
        
    #     self.filesel.popup("Load FITS file",
    #                        lambda filepath: self.load_fits(workspace, filepath),
    #                        initialdir=initialdir)
        
    # def load_fits(self, workspace, filepath):
            
    #     (filedir, filename) = os.path.split(filepath)
    #     (filepfx, fileext) = os.path.splitext(filename)
    #     try:
    #         page = workspace.addpage(filepath, filepfx, FitsViewerPage)
    #         page.load(filepath)

    #         # Bring FITS tab to front
    #         workspace.select(page.name)
    #         return page
        
    #     except Exception, e:
    #         self.popup_error("Cannot load '%s': %s" % (
    #                 filepath, str(e)))
    #         return None

    def gui_create_queue(self, workspace):
        
        def create_queue_res(w, rsp, went):
            queueName = went.get_text()
            w.destroy()
            if rsp == 1:
                self.add_queue(workspace, queueName)
            return True

        dialog = gtk.MessageDialog(flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                                   type=gtk.MESSAGE_QUESTION,
                                   message_format="Please enter a name for the new queue:")
        dialog.set_title("Create Queue")
        dialog.add_buttons("Ok", 1, "Cancel", 0)
        vbox = dialog.get_content_area()
        ent = gtk.Entry()
        vbox.add(ent)
        ent.show()
        dialog.connect("response", create_queue_res, ent)
        dialog.show()

    def add_queue(self, workspace, name, create=True):
        queueName = name.strip().lower()
        try:
            if create:
                if self.queue.has_key(queueName):
                    raise Exception("A queue with that name already exists!")
                queue = common.controller.addQueue(queueName, self.logger)
            else:
                queue = self.queue[queueName]

            page = workspace.addpage(queueName, queueName.capitalize(),
                                     QueuePage)
            page.set_queue(queueName, queue)

            workspace.select(page.name)
            return page
        
        except Exception, e:
            self.popup_error("Cannot add queue page '%s': %s" % (
                    name, str(e)))
            return None

    def gui_create_workspace(self, workspace):
        
        def create_workspace_res(w, rsp, went):
            name = went.get_text()
            w.destroy()
            if rsp == 1:
                self.add_workspace(workspace, name)
            return True

        dialog = gtk.MessageDialog(flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                                   type=gtk.MESSAGE_QUESTION,
                                   message_format="Please enter a name for the new workspace:")
        dialog.set_title("Create Workspace")
        dialog.add_buttons("Ok", 1, "Cancel", 0)
        vbox = dialog.get_content_area()
        ent = gtk.Entry()
        vbox.add(ent)
        ent.show()
        dialog.connect("response", create_workspace_res, ent)
        dialog.show()

    def add_workspace(self, workspace, name):
        try:
            page = workspace.addpage(name, name,
                                     WorkspacePage.WorkspacePage)

            workspace.select(page.name)

            page.menu_close.set_sensitive(True)

            #self.add_load_menus(page.wsmenu, page)
            return page

        except Exception, e:
            self.popup_error("Cannot create workspace page: %s" % (
                    str(e)))
            return None
        
    def edit_command(self, cmdstr):
        try:
            page = self.exws.getPage('Commands')
            page.set_text(cmdstr)

            # Bring Commands tab to front
            self.exws.select('Commands')
        except Exception, e:
            self.popup_error("Cannot edit command: %s" % (
                    str(e)))

    def delete_event(self, widget, event, data=None):
        self.ev_quit.set()
        #gtk.main_quit()
        return False

    # callback to quit the program
    def quit(self, widget):
        self.ev_quit.set()
        #gtk.main_quit()
        return False

    def reset_pause(self):
        try:
            # Perform a global reset across all command-type pages
            for ws in self.ds.getWorkspaces():
                for page in ws.getPages():
                    if isinstance(page, PG.CommandPage):
                        page.reset_pause()
        except Exception, e:
            self.logger.error("Error resetting pages: %s" % str(e))

    ############################################################
    # Interface from controller into the view
    #
    # Due to poor thread-handling in gtk, we are forced to spawn
    # these calls off to the GUI thread using gui_do()
    ############################################################

    def obs_timer(self, tag, title, iconfile, soundfn, time_sec, callfn):
        dialog = dialogs.Timer()
        self.gui_do(dialog.popup, title, iconfile, soundfn, time_sec, callfn,
                    tag=tag)
    
    def obs_confirmation(self, tag, title, iconfile, soundfn, btnlist, callfn):
        dialog = dialogs.Confirmation()
        self.gui_do(dialog.popup, title, iconfile, soundfn, btnlist, callfn,
                    tag=tag)
    
    def obs_userinput(self, tag, title, iconfile, soundfn, itemlist, callfn):
        dialog = dialogs.UserInput()
        self.gui_do(dialog.popup, title, iconfile, soundfn, itemlist, callfn,
                    tag=tag)

    def obs_combobox(self, tag, title, iconfile, soundfn, itemlist, callfn):
        dialog = dialogs.ComboBox()
        self.gui_do(dialog.popup, title, iconfile, soundfn, itemlist, callfn,
                    tag=tag)

    def cancel_dialog(self, tag):
        self.gui_do(dialogs.cancel_dialog, tag)
        
    def update_frame(self, frameinfo):
        if hasattr(self, 'framepage'):
            self.gui_do(self.framepage.update_frame, frameinfo)

    def update_frames(self, framelist):
        if hasattr(self, 'framepage'):
            self.gui_do(self.framepage.update_frames, framelist)

    def update_obsinfo(self, infodict):
        self.logger.debug("OBSINFO=%s" % str(infodict))
        if hasattr(self, 'obsinfo'):
            self.gui_do(self.obsinfo.update_obsinfo, infodict)
   
    def update_history(self, key, info):
        if hasattr(self, 'history'):
            #self.gui_do(self.history.update_table, key, info)
            print "INFO IS", info
            msgstr = fmt_history % info
            self.gui_do(self.history.push, msgstr)
           
   
    def update_loginfo(self, logname, infodict):
        if hasattr(self, 'logpage'):
            try:
                page = self.logpage.getPage(logname)
                #print "%s --> %s" % (logname, str(infodict)) 
                self.gui_do(page.add2log, infodict)
            except KeyError:
                # No log page for this log loaded, so silently drop message
                # TODO: drop into the integgui2 log page?
                pass
   
    def process_ast(self, ast_id, vals):
        if hasattr(self, 'monpage'):
            self.gui_do(self.monpage.process_ast, ast_id, vals)

    def process_subcommand(self, parent_path, subpath, vals):
        if hasattr(self, 'monpage'):
            self.gui_do(self.monpage.process_subcommand,
                        parent_path, subpath, vals)

    def process_task(self, path, vals):
        if hasattr(self, 'monpage'):
            self.gui_do(self.monpage.process_task, path, vals)

    def update_statusMsg(self, format, *args):
        self.gui_do(self.statusMsg, format, *args)
        
    def gui_do(self, method, *args, **kwdargs):
        """General method for calling into the GUI.
        """
        #gobject.idle_add(method, *args, **kwdargs)
        future = Future.Future()
        future.freeze(method, *args, **kwdargs)
        self.gui_queue.put(future)
        return future
   
    def gui_do_future(self, future):
        """General method for calling into the GUI.
        """
        self.gui_queue.put(future)

    def gui_do_res(self, method, *args, **kwdargs):
        """General method for calling into the GUI.
        """
        # Note: I suppose there may be a valid reason for the GUI thread
        # to create one of these, but better safe than sorry...
        self.assert_nongui_thread()
        
        return self.gui_do(method, *args, **kwdargs)
    
    def assert_gui_thread(self):
        my_id = thread.get_ident() 
        assert my_id == self.gui_thread_id, \
               Exception("Non-GUI thread (%d) is executing GUI code!" % (
            my_id))
        
    def assert_nongui_thread(self):
        my_id = thread.get_ident() 
        assert my_id != self.gui_thread_id, \
               Exception("GUI thread (%d) is executing non-GUI code!" % (
            my_id))
        

    def update_pending(self, timeout=0.0):
        
        # Process "out-of-band" GTK events
        #print "PROCESSING OUT-BAND"
        #gtk.gdk.threads_enter()
        try:
            while gtk.events_pending():
                gtk.main_iteration(False)
        finally:
            #gtk.gdk.threads_leave()
            pass

        done = False
        while not done:
            #print "PROCESSING IN-BAND"
            # Process "in-band" GTK events
            try:
                future = self.gui_queue.get(block=True, 
                                            timeout=timeout)

                # Execute the GUI method
                #gtk.gdk.threads_enter()
                try:
                    try:
                        res = future.thaw(suppress_exception=False)

                    except Exception, e:
                        future.resolve(e)

                        self.logger.error("gui error: %s" % str(e))
                        try:
                            (type, value, tb) = sys.exc_info()
                            tb_str = "".join(traceback.format_tb(tb))
                            self.logger.error("Traceback:\n%s" % (tb_str))

                        except Exception, e:
                            self.logger.error("Traceback information unavailable.")

                finally:
                    #gtk.gdk.threads_leave()
                    pass

                    
            except Queue.Empty:
                done = True
                
            except Exception, e:
                self.logger.error("Main GUI loop error: %s" % str(e))
                #pass
                
            # Process "out-of-band" GTK events
            #print "PROCESSING OUT-BAND"
            #gtk.gdk.threads_enter()
            try:
                while gtk.events_pending():
                    gtk.main_iteration(False)
            finally:
                #gtk.gdk.threads_leave()
                pass
            

    def mainloop(self, timeout=0.001):
        # Mark our thread id
        self.gui_thread_id = thread.get_ident()

        while not self.ev_quit.isSet():
            self.update_pending(timeout=timeout)

        #gtk.main_quit()


#END

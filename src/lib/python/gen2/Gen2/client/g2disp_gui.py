#! /usr/bin/env python
# 
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Sep 14 14:29:42 HST 2009
#]

import sys, time
import ssdlog, logging
import Queue
import Tkinter
import Pmw
import g2disp
import Bunch

class g2Disp_GUI(object):
    def __init__(self, rootWin, options
, obj):
     
        self.root = rootWin
        self.options = options

        self.obj = obj
        # Share main object's logger
        self.logger = obj.logger

        self.w = Bunch.Bunch()

        menubar = Tkinter.Menu(self.root, relief='flat')

        # create "File" pulldown menu, and add it to the menu bar
        filemenu = Tkinter.Menu(menubar, tearoff=1)
        filemenu.add('command', label="Show Log", command=self.showlog)
        self.muted = Tkinter.IntVar()
        self.muted.set(1)
        filemenu.add('checkbutton', label="Mute", 
                     variable=self.muted,
                     command=self.muteOnOff)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        # pop-up other system dialog
        self.w.sys = Pmw.PromptDialog(self.root,
                                      title='Gen2 System Selector',
                                      label_text='Enter hostname of system:',
                                      entryfield_labelpos='n',
                                      defaultbutton=0,
                                      buttons=('OK', 'Cancel'),
                                      command=self.setGen2System)
        self.w.sys.withdraw()

        # create "System" pulldown menu, and add it to the menu bar
        sysmenu = Tkinter.Menu(menubar, tearoff=1)
        self.rohosts = Tkinter.StringVar()
        self.rohosts.set("g2ins1")
        sysmenu.add('radiobutton', label="Summit", 
                    variable=self.rohosts,
                    value="g2ins1",
                    command=self.selectSystem)
        sysmenu.add('radiobutton', label="Simulator", 
                    variable=self.rohosts,
                    value="g2sim",
                    command=self.selectSystem)
        sysmenu.add('radiobutton', label="Other", 
                    variable=self.rohosts,
                    value="other",
                    command=self.w.sys.show)
        menubar.add_cascade(label="System", menu=sysmenu)

        self.root.config(menu=menubar)

        # pop-up log file
        self.w.log = Pmw.TextDialog(self.root, scrolledtext_labelpos='n',
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
        
        # logo pane
        #logo = Tkinter.PhotoImage(file='gen2_logo.gif')
        logo = Tkinter.PhotoImage(data=logo_b64)
        self.w.logo = Tkinter.Label(self.root, image=logo)
        self.w.logo.image = logo
        self.w.logo.pack(padx=5, pady=2, fill='both', expand=0)

        # bottom buttons
        frame = Tkinter.Frame(self.root) 
        
        self.w.quit = Tkinter.Button(frame, text="Quit",
                                     width=40,
                                     command=self.quit,
                                     activebackground="#089D20",
                                     activeforeground="#FFFF00")
        self.w.quit.pack(padx=5, pady=4, side=Tkinter.BOTTOM)

        frame.pack()

        self.closelog(self.w.log)

    def closelog(self, w):
        # close log window
        self.w.log.withdraw()
        
    def showlog(self):
        # open log window
        self.w.log.show()

    def muteOnOff(self):
        # mute audio
        if self.muted.get():
            self.obj.muteOn()
        else:
            self.obj.muteOff()

    def get_rohosts(self):
        return self.rohosts.get()

    def restart_servers(self, rohosts):
        self.obj.stop_server()
        time.sleep(1.0)
        self.obj.start_server(rohosts, self.options)

    def selectSystem(self):
        # Choose summit or simulator
        rohosts = self.get_rohosts()
        print "rohosts=%s" % rohosts
        self.restart_servers(rohosts.split(','))

    def setGen2System(self, result):
        # Choose other system
        if result is None or result == 'Cancel':
            self.w.sys.deactivate()
        else:
            rohosts = self.w.sys.get()
            self.restart_servers(rohosts.split(','))
        self.w.sys.withdraw()
        
    def setPos(self, geom):
        self.root.geometry(geom)

    def logupdate(self):
        try:
            while True:
                msgstr = self.queue.get(block=False)

                self.w.log.insert('end', msgstr + '\n')

        except Queue.Empty:
            self.root.after(200, self.logupdate)

    # callback to quit the program
    def quit(self):
        self.obj.allViewersOff()
        self.obj.stop_server()
        sys.exit(0)


class GraphicalUI(object):

    def __init__(self, options):
        self.options = options

    def ui(self, obj):
        root = Tkinter.Tk()
        Pmw.initialise(root)
        title='Gen2 Display Server'
        root.title(title)

        g2disp = g2Disp_GUI(root, self.options, obj)
        if self.options.geometry:
            g2disp.setPos(self.options.geometry)
        
        g2disp.logupdate()

        rohosts = g2disp.get_rohosts().split(',')
        obj.start_server(rohosts, self.options)

        root.mainloop()


def main(options, args):
    gui = GraphicalUI(options)

    g2disp.main(options, args, gui)
    
   
logo_b64 = """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"""

# Create demo in root window for testing.
if __name__ == '__main__':
  
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    optprs.add_option("-g", "--geometry", dest="geometry",
                      metavar="GEOM", default="-30-100",
                      help="X geometry for initial size and placement")
    g2disp.add_options(optprs)
    
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

#END


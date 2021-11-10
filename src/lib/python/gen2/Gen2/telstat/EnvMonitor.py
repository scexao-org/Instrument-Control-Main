#! /usr/bin/env python

# Sam Streeper
# 2008-12-04
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Feb  6 12:27:44 HST 2009
#]

# New Environment Monitor, using the StatusGraph

from Tkinter import *  # UI widgets and event loop infrastructure
import Tkinter
import Pmw             # Additional UI widgets
import StatusGraph as sg
import SOSS.status as st
import math
import os
import ssdlog

version = '20090206.0'

windWindow = None
quitDialog = None

THINDEFAULTLINE = [('A', '#7f0084',   0, 1, '', "A: %d", "Helvetica 12 bold"),
               ('B', '#107800', 0, 1, '', "B: %d", "Helvetica 12 bold")]


class ResourceMonitor(Frame):
    '''ResourceMonitor is a frame that displays water & oil status'''

    def __init__(self, parent, status_obj, logger):

        self.cachedStatus = status_obj
        self.logger = logger
        
        self.statusKeys = ("TSCV.WATER", "TSCV.OIL")
        Frame.__init__(self, parent)

        label = Label(self, text="Water Storage : ",
                      font="Helvetica 11", fg="#000000")
        label.grid(row=0,column=0,sticky=E)
        self.waterStorageLabel = Label(self, text="Normal",
                                       font="Helvetica 11", fg="#000000")
        self.waterStorageLabel.grid(row=0,column=1, sticky=W)

        label = Label(self, text="Oil Storage   : ",
                      font="Helvetica 11", fg="#000000")
        label.grid(row=1,column=0,sticky=E)
        self.oilStorageLabel = Label(self, text="Normal",
                                     font="Helvetica 11", fg="#000000")
        self.oilStorageLabel.grid(row=1,column=1, sticky=W)

        invisibleframe = Frame(self, width=105)
        invisibleframe.grid(row=2,column=0)
        invisibleframe = Frame(self, width=125)
        invisibleframe.grid(row=2,column=1)
        self.tmpW = 0
        self.tmpO = 1

    def tick(self):
        try:
            statusAliasValues = map(lambda alias:self.cachedStatus[alias],
                                    self.statusKeys)

            waterVal = statusAliasValues[0]
            if waterVal  != 0:
                bg = "#eebbbb"
                if waterVal <= -1.0:
                    text = "LOW ALARM"
                elif waterVal >= 1.0:
                    text = "HIGH ALARM"
                else:
                    text = "???"
            else:
                bg = "#e0f4e0"
                text = "Normal"
            self.waterStorageLabel.config(text=text, bg=bg)

            oilVal = statusAliasValues[1]
            if oilVal  != 0:
                bg = "#eebbbb"
                if oilVal <= -1.0:
                    text = "LOW ALARM"
                elif oilVal >= 1.0:
                    text = "HIGH ALARM"
                else:
                    text = "???"
            else:
                bg = "#e0f4e0"
                text = "Normal"
            self.oilStorageLabel.config(text=text, bg=bg)

        except st.statusError, e:
            #self.logger.error("Error getting status values: %s" % (str(e)))
            pass
            
        self.after(5000, self.tick)


class WindMonitor(Canvas):

    def __init__(self, status_obj, logger):
        global windWindow

        windWindow = Tkinter.Toplevel()
        graphsize = 220
        self.half = graphsize / 2
        self.sz1 = 15
        self.sz2 = 22
        self.cachedStatus = status_obj
        self.logger = logger

        windWindow.title("Wind Direction & Dome AZ")
        windWindow.geometry("%sx%s" % (graphsize, graphsize))
        windWindow.protocol("WM_DELETE_WINDOW", self._delete_window)

        Canvas.__init__(self, windWindow, width=graphsize, height=graphsize)
        self.grid(row=0, column=0)
        self.windGif = None
        try:
            self.windGif = PhotoImage(file = 'WindMonitor.gif')

        except TclError, e:
            try:
                self.windGif = PhotoImage(file = '/app/LOAD/DEBUG/' + 'WindMonitor.gif')
            except TclError, e:
                self.logger.error("Can't load wind monitor image WindMonitor.gif: %s" % (
                    str(e)))
                
        if self.windGif:
            self.create_image(0,0,image = self.windGif, anchor=Tkinter.NW)

        start = self.half - self.sz1
        end = self.half + self.sz1
        self.create_oval(start,start,end,end, outline='grey', fill='grey')

        # here I fill out data structures with temp values, updated in self.tick()
        domeAz = 0
        self.domeAZtriangle = [ self.center(),self.center(),
                                self.center(),self.center() ]

        direction = 10
        speed = 8
        self.windLine = [self.center(), self.windPoint(direction, speed)]

        self.windTriangle = [self.xy(angle=0,distance=85),
                             self.xy(angle=4, distance=(85 + self.sz2)),
                             self.xy(angle=-4, distance=(85 + self.sz2)),
                             self.xy(angle=0,distance=85)]
        self.tick()

    def _delete_window(self):
        global windWindow
        try:
            windWindow.destroy()
            windWindow = None
        except Exception, e:
            self.logger.error("Error deleting wind direction window: %s" % (
                str(e)))

    def center(self):
        return [self.half, self.half]

    def xy(self, angle=0, distance=5):
        radians = (angle - 90) * math.pi / 180
        x = self.half + (distance * math.cos(radians))
        y = self.half + (distance * math.sin(radians))
        return [x,y]

    def windPoint(self, direction, speed):
        WINDS_MAX = 60
        return self.xy(direction, (self.half * speed / WINDS_MAX) + 5)

    def tick(self):
        try:
            domeAz = self.cachedStatus["TSCS.AZ"] + 180
            self.domeAZtriangle[1] = self.xy(domeAz+26,self.sz2)
            self.domeAZtriangle[2] = self.xy(domeAz-26,self.sz2)

            direction = self.cachedStatus["TSCL.WINDD"]
            speed = self.cachedStatus["TSCL.WINDS_O"]
            self.windLine[1] = self.windPoint(direction, speed)
            self.windTriangle[0] = self.windTriangle[3] = self.xy(angle=direction,distance=85)
            self.windTriangle[1] = self.xy(angle=direction+4, distance=(85 + self.sz2))
            self.windTriangle[2] = self.xy(angle=direction-4, distance=(85 + self.sz2))

            self.delete('movable')

            self.create_polygon(self.domeAZtriangle, outline='grey', fill='grey', tags='movable')
            self.create_polygon(self.windTriangle, outline='steel blue', fill='steel blue', tags='movable')
            self.create_line(self.windLine, fill= "navy blue", capstyle="round", width=5, tags='movable')

        except Exception, e:
            self.logger.error("Exception raised during tick update: %s" % (
                str(e)))
            #raise e
        
        self.after(5000, self.tick)


class Gen2StatusObject(object):
    def __init__(self, serviceName):
        import remoteObjects as ro

        ro.init()
        self.status = ro.remoteObjectProxy(serviceName)

    def __getitem__(self, key):
        # This is not efficient at all, but it will do for now...
        return self.status.fetchOne(key)
    
# =================  main() starts here ============================

def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger('EnvMonitor', options)

    # Create status object to be shared by all interested parties
    if options.statsvc:
        # Specified Gen2 status
        status_obj = Gen2StatusObject(options.statsvc)

    else:
        # Specified SOSS status
        status_obj = st.cachedStatusObj(options.statint)

    # callback for popping up wind monitor
    def showWindDirection():
        global windWindow

        if windWindow:
            windWindow.deiconify()
            #windWindow.show()
            return

        # Create the base frame for the widgets
        WindMonitor(status_obj, logger)

    # Create the base frame for the widgets
    root = Tk()
    Pmw.initialise(root)
    root.title("Environment Monitor")
    root.tk.call('tk','scaling',1)
    if options.geometry:
        root.geometry(options.geometry)
    else:
        root.geometry("433x742")
    
    def dialogResult(result):
        global quitDialog
        #print 'You clicked on ', result
        quitDialog.deactivate(result)
        if result == 'Yes':
            root.quit()

    def askAboutQuitting():
        # Create the dialog.
        global quitDialog
        quitDialog = Pmw.Dialog(None,
                                buttons = ('No', 'Yes'),
                                defaultbutton = 'Yes',
                                title = 'Quit Environment Monitor?',
                                command = dialogResult)
        quitDialog.geometry("300x45")
        quitDialog.activate(globalMode = 1)
        quitDialog.withdraw()

    def _delete_main_window():
        askAboutQuitting()


    root.protocol("WM_DELETE_WINDOW", _delete_main_window)

    row = 0
    widget1 = sg.StatusGraph(root,
                             title="Wind direction (deg) N:0 E:90",
                             statusKeys=("TSCL.WINDD",),
                             maxDeltas=(300,),
                             gconfig = (None, "black", "white", (0,360,90),
                                        1, 0, 1),
                             background="#f5fffc",
                             statusObj=status_obj)
    widget1.grid(row=row, column=0)
    widget1.tick()
    row +=1


    widget2 = sg.StatusGraph(root, title="Wind Speed(m/s)",
                             statusKeys=("TSCL.WINDS_O", "TSCL.WINDS_I"),
                             alarmValues = (10,15),
                             #gconfig = (None, "black", "white", (-1,20,5), 1, 0, 1),
                             background="#f7fff4",
                             statusObj=status_obj)
    widget2.grid(row=row, column=0)
    widget2.tick()
    row +=1


    widget3 = sg.StatusGraph(root, title="Temperature(C)",
                             statusKeys=("TSCL.TEMP_O", "TSCL.TEMP_I"),
                             statusObj=status_obj)
    widget3.grid(row=row, column=0)
    widget3.tick()
    row +=1


    widget4 = sg.StatusGraph(root, title="Humidity(%)",
                             statusKeys=("TSCL.HUMI_O", "TSCL.HUMI_I"),
                             alarmValues = (80,80),
                             background="#fffff6",
                             size=(112,430),
                             displayTime=True,
                             lconfig=THINDEFAULTLINE,
                             statusObj=status_obj)
    widget4.grid(row=row, column=0)
    widget4.tick()
    row +=1


    widget5 = sg.StatusGraph(root, title="Air Pressure(hPa) :",
                             size=(97,430),
                             statusKeys=("TSCL.ATOM",),
                             statusFormats=("%0.1f",),
                             lconfig=THINDEFAULTLINE,
                             statusObj=status_obj)
    widget5.grid(row=row, column=0)
    widget5.tick()
    row +=1


    widget6 = sg.StatusGraph(root, title="Rain Gauge(mm/h) :",
                             statusKeys=("TSCL.RAIN",),
                             statusFormats=("%0.1f",),
                             alarmValues = (50,),
                             size=(93,430),
                             background="#f4f4f4",
                             statusObj=status_obj)
    widget6.grid(row=row, column=0)
    widget6.tick()
    row +=1


    widget7 = sg.StatusGraph(root, title="Seeing Size(arcsec)",
                             statusKeys=("TSCL.SEEN", "VGWD.FWHM.AG"),
                             alarmValues = (1,1),
                             statusFormats=("TSC: %0.1f", "VGW: %0.1f"),
                             displayTime=True,
                             statusObj=status_obj)
    widget7.grid(row=row, column=0)
    widget7.tick()
    row +=1


#    widget8 = sg.StatusGraph(root, title="Sky Transparency(%) :",
#                                statusKeys=("TSCL.THRU",),
#                                background="#f4f4f4",
#                                displayTime=True, statusObj=status_obj)
#    widget8.grid(row=row, column=0)
#    widget8.tick()
#    row +=1

    
    bottomframe = Frame(root, width=440)
    buttons = Pmw.ButtonBox(bottomframe)
    buttons.add('Quit',
                command=askAboutQuitting,
                font=('Helvetica', 12, 'bold'))
    buttons.grid(row=0,column=0)
    
    resourceframe = ResourceMonitor(bottomframe, status_obj, logger)
    resourceframe.grid(row=0,column=1)
    resourceframe.tick()
    
    buttons = Pmw.ButtonBox(bottomframe)
    buttons.add('Wind Direction',
                command=showWindDirection,
                font=('Helvetica', 12, 'bold'))
    buttons.grid(row=0,column=2)
    bottomframe.grid(row=row, column=0)
    row +=1

    try:
        try:
            root.mainloop()

        except KeyboardInterrupt:
            logger.error("Received keyboard interrupt!")

    except Exception, e:
        logger.error("Top-level exception raised: %s" % str(e))
        raise e
        
    logger.info("Terminating application")

   
if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options] command [args]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-g", "--geometry", dest="geometry",
                      metavar="GEOM", default="433x742",
                      help="X geometry for initial size and placement")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--statint", dest="statint", metavar="HOST",
                      default='obs',
                      help="Fetch SOSS status from HOST")
    optprs.add_option("--statsvc", dest="statsvc", metavar="NAME",
                      default=None,
                      help="Get Gen2 status via service NAME")
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


# END

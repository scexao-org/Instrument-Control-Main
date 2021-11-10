#! /usr/local/bin/python

#  Arne Grimstrup
#  2003-09-29

#  This module implements a digital clock widget based on a standard Tk label.
#  Data is retrieved from the system clock but other functions that return the
#  as seconds since the UNIX epoch (00:00:00 UTC 1970-01-01) can be substituted.

from Tkinter import *  # UI widgets and event loop infrastructure
import Pmw             # Additional UI widgets
import time            # Time and time-specific formatting functions
import Util            # Utility function module

#  Default widget configuration reports the basic "HH:MM:SS" in the local timezone
DEFAULTCLOCKFORMAT = '%H:%M:%S'
DEFAULTCLOCKFONT = 'Helvetica 20 bold'
DEFAULTFGCLOCKCOLOR = 'white'
DEFAULTBGCLOCKCOLOR = 'black'
DEFAULTCLOCKTIME = time.localtime

class TimeLabel(Label):

    def __init__(self, parent, ifgcolor=DEFAULTFGCLOCKCOLOR, ibgcolor=DEFAULTBGCLOCKCOLOR,
                 ifont=DEFAULTCLOCKFONT):
        """Create a new instance of a time label with the given configuration.
        The iformat must be a valid strftime() format string and tfunc must point
        to a function that returns the time, in 9-tuple form, from the UNIX epoch."""
        Label.__init__(self, parent)

        # StringVar is used because the display will be updated immediately
        # after its value changes.  
        self.nowStr = StringVar()

        # Configure the label attributes.  Passing a large number of attributes via
        # the parameter list is ok for now, but we really should consider using a
        # dictionary or configuration object.  We also need to consider allowing the
        # user to customize the widget on the fly.
        self.configure(font = ifont, fg=ifgcolor, bg=ibgcolor, textvariable=self.nowStr)

    def update(self, timestr):
        """Update the label with the time string."""
        self.nowStr.set(timestr)

    def tick(self):
        """Update the label every second."""
        self.update(time.strftime(DEFAULTCLOCKFORMAT))
        self.after(1000, self.tick)

# Test application
if __name__ == '__main__':
    # Create the base frame for the widgets
    root = Tk()
    Pmw.initialise(root)
    root.title("Time Label")

    # Create an instance that reports time and date in UTC
    widget = TimeLabel(root, ifgcolor="red")
    widget.grid(row=0,column=0)
    widget.tick()

    # Create an instance that reports time and date in the local timezone
    widget2 = TimeLabel(root, ifgcolor="lightblue")
    widget2.grid(row=0,column=1)
    widget2.tick()

    # Create an instance that reports time and date in the local timezone
    widget3 = TimeLabel(root, ifgcolor="yellow")
    widget3.grid(row=0,column=2)
    widget3.tick()

    root.mainloop()


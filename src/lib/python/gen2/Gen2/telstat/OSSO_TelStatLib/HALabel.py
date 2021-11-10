#! /usr/local/bin/python

#  Arne Grimstrup
#  2004-10-05
#  Modified 2005-08-23 19:41 Bruce Bon

#  This module implements an hour angle clock widget based on a standard Tk label.

#  References
#
#  [Kit95]  Kitchin C.R., Telescopes and Techniques: An Introduction to Practical
#              Astronomy, Springer-Verlag London, 1995.

from Tkinter import *  # UI widgets and event processing library
import Util            # Utility function library
import Pmw             # Additional UI widget library

#  Default widget configuration
DEFAULTFGCOLOR = 'white'
DEFAULTBGCOLOR = 'black'
DEFAULTFONT = 'Helvetica 20 bold'
DEFAULTTIMER = Util.sidereal
DEFAULTTARGET = (10,12,14.689)

class HALabel(Label):

    def __init__(self, parent, ifgcolor=DEFAULTFGCOLOR, ibgcolor=DEFAULTBGCOLOR,
                 ifont=DEFAULTFONT):
        """Create an instance of an hour angle clock."""
        Label.__init__(self, parent)
        self.nowStr = StringVar()
        self.configure(font = ifont, fg=ifgcolor, bg=ibgcolor, textvariable=self.nowStr)

    def setTarget(self, itgtsrc=DEFAULTTARGET):
        """Sets the RA for the target object."""
        self.ra = itgtsrc

    def update(self, lst):
        """Update the label with the value from the time calculation function."""

        # According to Kitchin[Kit95], the relationship between local sidereal time,
        # right ascension and hour angle can be expressed in the following formula
        #
        #       LST = RA + HA
        #
        # or alternatively
        #
        #       HA = LST - RA
        #
        # The LST is the passed parameter and the telescope supplies the RA for the
        # designated target.
        delta = Util.timediff(lst[3:6],self.ra)

        # normalize the expression. The hour value must be
        # between -12 < HA < 12. If it is +13, it must be -11
        if  (delta[0] == '+' and delta[1][0] > 12 ):
            delta = Util.timediff(delta[1], [24, 0, 0])
        elif  (delta[0] == '-' and delta[1][0] > 12 ):
            delta = Util.timediff(delta[1], [24, 0, 0])
            delta[0] = '+'

        # Calculation is performed using H:M:S but need only be reported
        # as H:M.  We may want to support display of H:M:S in the future.
        self.nowStr.set("HA:%c%2.2dh%2.2dm" %
                        (delta[0], delta[1][0], delta[1][1]))

        
    def tick(self):
        """Update the label every second."""
        self.update(Util.sidereal())
        self.after(1000, self.tick)

# Test application
if __name__ == '__main__':
    # Create the base frame for the widgets
    root = Tk()
    Pmw.initialise(root)
    root.title("HA Label")

    # Create an instance that reports HA for the default target
    widget = HALabel(root)
    widget.setTarget()
    widget.grid(row=0,column=0)
    widget.tick()

    # Create an instance that reports HA for target 1 hour later
    widget2 = HALabel(root)
    widget2.setTarget((20,20,00))
    widget2.grid(row=0,column=1)
    widget2.tick()

    root.mainloop()

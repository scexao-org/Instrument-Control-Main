#! /usr/local/bin/python

#  Arne Grimstrup
#  2003-09-29

#  This module implements a strip chart widget.

from Tkinter import *  # UI widgets and event loop infrastructure
import Pmw             # Additional UI widgets
import time            # Time functions
import math            # Math functions

#  Default widget configuration
#
#  DEFAULTGRAPH contains the overall configuration for the strip chart widget.
#  0) Text for the frame's label
#  1) Frame foreground colour
#  2) Frame background colour
#  3) Tuple containing Y scale information (None if autoscale)
#     0) Minimum Y value
#     1) Maximum Y value
#     2) Major tick increment value
#  4) X scale disable
#  5) Y scale disable
#  6) Legend disable
DEFAULTGRAPH = ("Test", "white", "black", (0,100,20), 0, 0, 1)

#  DEFAULTLINE contains a list of configurations for the lines that
#  are plotted in the graph.  For each line, there must be a tuple
#  containing the following information:
#  0) Line name
#  1) Line colour
#  2) Line style
#  3) Line width
#  4) Point symbol
#  5) Label format
#  6) Label font
DEFAULTLINE = [('A', '#008800',   0, 1, '', "A: %d", "Helvetica 8"),
               ('B', '#000088', 0, 1, '', "B: %d", "Helvetica 8")]

#  DEFAULTSIZE gives the widget dimensions (height, width) in pixels
DEFAULTSIZE = (100,900)

#  DEFAULTWINDOW gives the maximum capacity that the data vectors can store.
#  In this case, we can store a maximum of one hour of data sampled at 1 Hz.
DEFAULTWINDOW = 14400

#  DEFAULTSCALE indicates the size (in seconds) of the display window.
#  in the graph at each level.  DEFAULTSSCALE gives the initial display window
#  size to be used.
DEFAULTSSCALE = 5
DEFAULTSCALES = (300, 900, 1800, 3600, 7200, 14400)

#  DEFAULTFONTS gives the fonts for the X and Y scale respectively.
DEFAULTFONTS = ("Helvetica 9", "Helvetica 10")

class LineSegment:

    def __init__(self, lsgraph, lsname, lscolor, lsstyle, lswidth, lssymbol):
        """Create a new instance of line segment."""

        # Create storage for the data pairs
        self.xvector = Pmw.Blt.Vector()
        self.yvector = Pmw.Blt.Vector()

        # Cache the segment name
        self.name = lsname

        # Min and max values are stored rather than searched for to speed processing.
        self.ymax = None
        self.ymin = None
        self.xmax = None
        self.xmin = None

        # Create the graph element for this segment
        lsgraph.line_create(lsname, xdata=self.xvector, ydata=self.yvector,
                            color=lscolor, dashes=lsstyle, linewidth=lswidth, symbol=lssymbol)

    def deregister(self, lsgraph):
        """Remove the line segment from the graph."""
        lsgraph.element_delete(self.name)

    def length(self):
        """Report the number of values plotted in this segment."""
        return self.yvector.length()

    def update(self, x, y, w):
        """Plot a new data point in this segment."""

        # Add the new values to the data set.
        self.xvector.append(x)
        self.yvector.append(y)

        # Prune an values that appear outside the working set of the line
        while self.xvector[0] < x-w:
            self.xvector.delete(0)
            self.yvector.delete(0)

        # Update the max and min cache
        self.xmin = self.xvector[0]
        self.xmax = self.xvector[self.xvector.length() - 1]
        self.ymin = self.yvector.min()
        self.ymax = self.yvector.max()

    def min(self, since):
        """Report the lowest value plotted in this segment."""

        if self.xmax == None or self.xmin == None:
            # Line segment has no plotted points
            return None
        elif self.xmax < since:
            # Line segment has no values in the requested range
            return None
        elif self.xmax == since:
            # Slice operation fails when only last value in range.
            return self.yvector[self.yvector.length()-1]
        elif self.xmin >= since:
            # All points are within the range so standard search can be used.
            return self.yvector.min()
        else:
            # Limit search to points after the limit
            r = self.xvector.search(since)
            if r == None:
                # FIXME:  The limit point wasn't found, but other points do
                # exist in the data set.  Reporting global minimum is wrong,
                # but will do for now.
                return self.yvector.min()
            else:
                # Report lowest in the range
                v = self.yvector[r[0]:]
                return min(v)

    def max(self, since):
        """Report the highest value plotted in this segment."""

        if self.xmax == None or self.xmin == None:
            # Line segment has no plotted points
            return None
        elif self.xmax < since:
            # Line segment has no values in the requested range
            return None
        elif self.xmax == since:
            # Slice operation fails when only last value in range.
            return self.yvector[self.yvector.length()-1]
        elif self.xmin >= since:
            # All points are within the range so standard search can be used.
            return self.yvector.max()
        else:
            # Limit search to points after the limit
            r = self.xvector.search(since)
            if r == None:
                # FIXME:  The limit point wasn't found, but other points do
                # exist in the data set.  Reporting global maximum is wrong,
                # but will do for now.
                return self.yvector.max()
            else:
                # Report lowest in the range
                v = self.yvector[r[0]:]
                return max(v)

class Line:

    def __init__(self, lframe, lpos, lgraph, lconf, lwindow):
        """Create an instance of a line for the given graph."""

        # A line in the graph is a sequence of line segments that have the same
        # basic configuration.
        self.graph = lgraph
        self.basename = lconf[0]
        self.color = lconf[1]
        self.style = lconf[2]
        self.width = lconf[3]
        self.symbol = lconf[4]
        self.labelfmt = lconf[5]

        #  In addition, there is a text label that displays the last value plotted.
        self.label = Label(lframe, height=1, text=lconf[0], font=lconf[6], bg=lframe.configure("background")[4], fg=lconf[1])

        # sam note: bad to make placement magic in general purpose widget...
        if (lpos == 0) :
            self.label.grid(row=0,column=lpos)
        else : self.label.grid(row=0,column=lpos,sticky=W)

        # Each element in a Pmw.Blt graph must have a unique name.  For these
        # line segments, we use a name + serial number value.  self.segment
        # contains the serial number of the currently active segment.
        self.segment = 1

        # The window size is needed to determine when line segments should be removed
        self.window = lwindow

        # Every line has an initial segment
        self.seglist = [LineSegment(lgraph, "%s%d" % (lconf[0], self.segment), self.color, self.style, self.width, self.symbol)]

    def setbackground(self, color):
        """Sets the label background color."""
        self.label.configure(bg=color)

    def length(self):
        """Compute the number of points plotted in the line."""

        # The length of the line is the sum of the length of the component line segments
        sum = 0
        for ls in self.seglist:
            sum += ls.length()
        return sum

    def update(self, x, y):
        """Add a new value to the line."""

        # A y value of None indicates a break in the plot
        if y == None:
            # No point starting a new segment when the current one has no data
            if self.seglist[len(self.seglist) - 1].length() > 0:
                # Start a new line segment
                self.segment += 1
                self.seglist.append(LineSegment(self.graph, "%s%d" % (self.basename, self.segment), self.color, self.style,
                                                self.width, self.symbol))
            self.label.configure(text="%s: <No Data>" % self.basename)
        else:
            # Update the existing line segment
            self.label.configure(text=self.labelfmt % y)
            self.seglist[len(self.seglist)-1].update(x,y, self.window)

        # Delete the first line segment if it is not longer part of the data window
        #if self.seglist[0].length() > 0 and self.seglist[0].max(x-self.window) == None:
        #    self.seglist.pop(0).deregister(self.graph)

    def min(self, since):
        """Report the lowest y value plotted in the line."""

        # Search the line segments for the lowest value in the valid range.
        lsmin = []
        for ls in self.seglist:
            lm = ls.min(since)
            if lm != None:
                lsmin.append(lm)
        if len(lsmin) == 0:
            return None
        else:
            return min(lsmin)

    def max(self, since):
        """Report the highest y value plotted in the line."""

        # Search the line segments for the highest value in the valid range.
        lsmax = []
        for ls in self.seglist:
            lm = ls.max(since)
            if lm != None:
                lsmax.append(lm)
        if len(lsmax) == 0:
            return None
        else:
            return max(lsmax)


def xtick(path, value):
    """Format the given time as HH:MM. """
    return time.strftime("%H:%M", time.localtime(float(value)))

class LineGraph(LabelFrame):

    def __init__(self, parent, size=DEFAULTSIZE, gconfig=DEFAULTGRAPH, lconfig=DEFAULTLINE,
                 pwindow=DEFAULTWINDOW, iscale=DEFAULTSSCALE, pscales=DEFAULTSCALES, ptickfont=DEFAULTFONTS):
        """Create a new instance of a line graph with the given configuration."""
        # Initialize base and force update so that widget size correctly reflects
        # assigned area.
        LabelFrame.__init__(self, parent, height=size[0], width=size[1], text=gconfig[0],
                            foreground=gconfig[1],background=gconfig[2], font=('Helvetica', 12, 'bold'))
        self.name = gconfig[0]
        self.update_idletasks()

        # Cache scale information.
        self.currscale = iscale   # Current time scale in use
        self.scales = pscales     # List of available time scales

        # Instance counters
        self.modcnt = 0       # Current base modulus (debug only)
        self.count = 0        # Number of updates performed since start up
        self.lastx = int(time.time()) # End of initial time scale
        self.x = self.lastx   # Base time (debug only)

        # Y scale boundary limits
        self.gmin = None
        self.gmax = None

        # The LineGraph widget contains two distinct zones.  Zone 1 contains the legend
        # information for the plot and Zone 2 contains the plot itself.
        #
        # Create and place the chart portion of the widget
        self.chart = Pmw.Blt.Graph(self)
        #self.chart.grid(row=1,column=0,columnspan=len(lconfig),rowspan=19)
        # by changing row to 0, I move the label onto (inside) the chart -sam
        self.chart.grid(row=0,column=0,columnspan=len(lconfig),rowspan=19)

        # Configure the chart, axises and legend components
        self.chart.configure(height=size[0]-19, width=size[1]-self.cget('borderwidth')*2,
                             plotpady=0,plotpadx=0, plotbackground=gconfig[2],
                             plotrelief="flat", background=gconfig[2])

# sammy test
#        print "stepsize : %s   width: %s\n" % (self.scales[self.currscale]*0.4,
#                                               size[1]-self.cget('borderwidth')*2)
        self.chart.axis_configure("x", hide=gconfig[4], color=gconfig[1],
# vvvvv this line breaks the environment monitor under VNC vvvvvvv
#                                  stepsize=self.scales[self.currscale]*0.4,
                                  command=xtick, background=gconfig[2],
                                  tickfont=ptickfont[0], ticklength="0.05i")

        self.yautoscale = gconfig[3]
        if self.yautoscale != None:
            self.chart.axis_configure("y", hide=gconfig[5], min=gconfig[3][0], max=gconfig[3][1],
                                      stepsize=gconfig[3][2], color=gconfig[1], background=gconfig[2],
                                      tickfont=ptickfont[1])
        else:
            self.chart.axis_configure("y", hide=gconfig[5], color=gconfig[1],
                                      background=gconfig[2], autorange=0.0,
                                      tickfont=ptickfont[1])

        self.chart.legend_configure(hide=gconfig[6], background = gconfig[2])

        # Configure the plot lines
        self.curves = len(lconfig)        # Number of lines being plotted
        self.lines = []                   # List of lines being plotted

        for c in range(self.curves):
            self.lines.append(Line(self, c, self.chart, lconfig[c], pwindow))

        # Establish event handler for rescaling commands
        self.chart.bind('<Double-Button-1>', self.scaleup)
        self.chart.bind('<Double-Button-3>', self.scaledown)

    def rescale(self):
        """Update the time scale."""
        self.chart.xaxis_configure(min=self.lastx-self.scales[self.currscale]+1,
                                   max=self.lastx, stepsize=self.scales[self.currscale]*0.4)

    def yrescale(self):
        """Update the Y scale to reflect the new values."""
        ystep = 0    # Increment for the major ticks
        minlist = [] # Minimum values found in each dataset
        maxlist = [] # Maximum values found in each dataset

        # Find the largest and smallest value in each dataset and add it
        # to the appropriate list.
        for d in self.lines:
            if d.length() > 1:
                l = d.min(self.lastx - self.scales[self.currscale])
                if l != None:
                    minlist.append(l)
                l = d.max(self.lastx - self.scales[self.currscale])
                if l != None:
                    maxlist.append(l)

        # Find the largest of the large and smallest of the small.
        # Update the scales so that based on that both can be plotted.
        if len(minlist) > 0 and len(maxlist) > 0:
            self.gmax = math.ceil(max(maxlist))
            self.gmin = math.floor(min(minlist))
            ystep = round((self.gmax - self.gmin) / 3.0)

            # BLT cannot label a y-axis that has the same min and max value
            # This will only occur when the data point are always the same
            if self.gmin >= self.gmax:
                self.gmin = self.gmax - 1
                self.gmax += 1

            # if min is 0, values of zero are clipped (line draws below 0?)
            if (self.gmin == 0 and self.gmax >= 2): self.gmin = -0.25

            self.chart.axis_configure('y',min=self.gmin, max=self.gmax, stepsize=ystep)


    def scaleup(self, foo):
        """Increase the timescale of the display."""
        if self.currscale >= len(self.scales)-1:
            # Alert the user that the scale cannot increase any more
            self.bell()
        else:
            # Rescale the X axis to reflect the new limits
            self.currscale += 1
            self.rescale()

            # Increasing the number of values that can be plotted
            # may also alter the range of Y values displayed.
            if self.yautoscale == None:
                self.yrescale()

    def scaledown(self, foo):
        """Decrease the timescale of the display."""
        if self.currscale == 0:
            # Alert the user that the scale cannot decrease any more
            self.bell()
        else:
            # Rescale the X axis to reflect the new limits
            self.currscale -= 1
            self.rescale()

            # Increasing the number of values that can be plotted
            # may also alter the range of Y values displayed.
            if self.yautoscale == None:
                self.yrescale()

    def newbackground(self, bgcolor):
        """Change the background colour of the widget."""
        # FIXME: This widget jitters when the background changes
        self.configure(bg=bgcolor)
        self.chart.configure(bg=bgcolor, plotbackground=bgcolor)

        for axis in "xy":
            self.chart.axis_configure(axis,background=bgcolor)

        for line in self.lines:
            line.setbackground(bgcolor)

    def nowbackground(self):
        """Report the current background colour of the widget."""
        return self.configure("background")[4]

    def resize(self, graphHeight=DEFAULTSIZE[0], graphWidth=DEFAULTSIZE[1]):
        """Change the geometry of the widget."""
        self.chart.configure(height=graphHeight-19, width=graphWidth-self.cget('borderwidth')*2)
        self.configure(height=graphHeight, width=graphWidth)

    def update(self, xval, values):
        """Plot another set of values."""
        # Check to make sure that xval isn't None
        if  xval == None:
            return
        # Add the new X value.  If the maximum data set size is exceeded
        # remove the extra one in FIFO order.
        self.count += 1
        self.lastx = xval

        # Add the new Y values
        for c in range(self.curves):
            self.lines[c].update(int(xval), values[c])

        # Update the Y axis labels if necessary
        self.rescale()
        if self.yautoscale == None and (min(values) < self.gmin or max(values) > self.gmax \
                                        or self.count % self.scales[self.currscale] == 0):
            self.yrescale()


    def tick(self):
        """Update the label every second.  Used for debugging purposes only."""
        self.base = (0, 10, 20, 30, 40, 50, 60, 70, 80, 90)
        if self.count % 400 == 0:
            self.modcnt += 1
            self.modcnt %= 10

        # Toggle the background colour
##         self.nowbackground()
##         if self.count % 2 == 0:
##             self.newbackground("black")
##         else:
##             self.newbackground("white")

        # Generate and plot new values
        self.x += 1
        self.y = self.base[self.modcnt] + self.x % 10
        if (self.x % 100) == 0:
            self.update(self.x,(None,100-self.y,))
        else:
            self.update(self.x,(self.y,100-self.y,))
        self.after(10, self.tick)

# Test application
if __name__ == '__main__':
    # Create the base frame for the widgets
    root = Tk()
    Pmw.initialise(root)
    root.title("Line Graph")
    root.geometry("900x440")


    # Create an instance that reports time and date in UTC
    widget = LineGraph(root, size=(200,900))
    widget.grid(row=0, column=0)
    widget.tick()

    widget2 = LineGraph(root, size=(200,900),
                        gconfig=("Humidity", "black", "white", None, 1, 0, 1, "Humidity: %d%%"),
                        lconfig=[('Humidity', 'green', 0, 2, '', "Now: %d%%", "Helvetica 8")])
    widget2.grid(row=1, column=0)
    widget2.tick()

    root.mainloop()












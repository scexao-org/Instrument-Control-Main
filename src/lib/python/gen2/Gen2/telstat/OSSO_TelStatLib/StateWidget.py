#! /usr/local/bin/python

#  Arne Grimstrup
#  2003-09-29
#  Modified 2005-05-16 16:28 Bruce Bon

#  This module implements an text-based state reporting widget.

from Tkinter import *  # UI widgets and event loop infrastructure
import Pmw             # Additional UI widgets

#  Default widget configuration
#  The widget accepts a list of text and background colour tuples.
#  The state number is the position of a particular pair in the list.
DEFAULTSTATES = [('OffLine','red'),('Stand-by', 'yellow'),('Ready', 'green')]

#  The size is a height and width tuple given in pixels
DEFAULTSIZE = (100, 300)

#  The font for the text label
DEFAULTFONT = "Helvetica 50"

class StateWidget(Canvas):

    def __init__(self, parent, 
                 ptext=DEFAULTSTATES[0][0], pcolor=DEFAULTSTATES[0][1],
                 psize=DEFAULTSIZE, pfont=DEFAULTFONT):
        """Create a new instance of a state reporter with the given configuration."""
        Canvas.__init__(self, parent)

        # Cache the current state and configuration for quick access
        self.text   = ptext
        self.color  = pcolor
        self.size   = psize
        self.font   = pfont

        # The state report is simply text on a coloured background
        # Set the background and text for the initial state.
        self.configure(height=self.size[0], width=self.size[1], bg=self.color)

        # There is no boundary checking for the text
        self.target = self.create_text(int(self.size[1]/2),int(self.size[0]/2),
                                       text=self.text, font=self.font)
          
    def updateText(self, ntext):
        """Update the label with new text information."""
        if self.text != ntext:
            self.delete( self.target )
            self.text = ntext
            self.target = self.create_text(self.size[1]/2,self.size[0]/2,
                                           text=self.text, font=self.font)

    def updateColor(self, ncolor):
        """Update the label with new color information."""
        if self.color != ncolor:
            self.color = ncolor
            self.configure(bg=ncolor)

    def tick(self):
        """Update the label every second."""
        import time

        y = int(time.time() % 3)
        self.update(y)
        self.after(1000, self.tick)

# Test application
if __name__ == '__main__':
    # Create the base frame for the widgets
    root = Tk()
    Pmw.initialise(root)
    root.title("State Widget")
    root.geometry("300x100")

    # Create an instance that reports time and date in UTC
    widget = StateWidget(root,2)
    widget.grid(row=0,column=0)
    widget.tick()

    root.mainloop()


#! /usr/local/bin/python

#  Arne Grimstrup
#  2003-09-29
#  Modified 2005-02-15 17:13 Bruce Bon

#  This module implements an off-on indicator light widget.

from Tkinter import *  # UI widgets and event loop infrastructure
import Pmw             # Additional UI widgets

#  Default widget configuration
#
#  The widget configuration is a 6-tuple consisting of
#  0) width of the widget
#  1) height of the widget
#  2) background color of the widget
#  3) foreground color of the widget
#  4) list containing off, on and alert color for the light elipse
#  5) list containing off, on and alert color for the text imposed on the light elipse
DEFAULTSETTINGS = (50, 30, "black", "white", ['darkred', 'red', 'red', 'red'],\
                                        ['white', 'black', 'black', 'black'])

class IndicatorLamp(Canvas):

    def __init__(self, parent, ptext, psettings = DEFAULTSETTINGS):
        """Create a new instance of an indicator light with the given configuration."""
        Canvas.__init__(self, parent)

        # Light and text colors are cached for fast retrieval
        self.color = psettings[4]
        self.tcolor = psettings[5]

        # Establish the canvas color scheme.  Borders and highlights are removed
        # to ensure that the widget blends in with the host pane background.
        self.configure(height=psettings[1], width=psettings[0], bg=psettings[2],
                       borderwidth=0, highlightthickness=0)

        # The edge of the light is created by overlaying a larger oval in the
        # canvas foreground color with a smaller oval in the off color.
        self.edge = self.create_oval(3,3,psettings[0]-3,psettings[1]-3,
                                      outline=psettings[3], fill=psettings[3])
        self.light = self.create_oval(5,5,psettings[0]-5,psettings[1]-5,
                                      outline=self.color[0], fill=self.color[0])

        # No boundary checking on the text.  If the oval is taller than wide,
        # the text will fall out side the light.
        self.label     = self.create_text(psettings[0]/2,psettings[1]/2,
                                          text=ptext, fill=self.tcolor[0])

        # Save state for testing when it changes
        self.labeltext = ptext
        self.state     = 0
            
    def update(self, state, newtext=None):
        """Update the light state. (Off == 0  On == 1, Warning == 2, Alarm == 3).
           Set newtext only for the Alarm state."""
        if  state != self.state:                        # state has changed
            self.itemconfig(self.light, outline=self.color[state], fill=self.color[state])
            self.itemconfig(self.label, fill=self.tcolor[state])
            if  state < 2:                              # restore normal text
                self.itemconfig(self.label, text=self.labeltext)
        if  newtext != None:                            # set alarm text
            self.itemconfig(self.label, text=newtext)
        self.state = state

    def tick(self):
        """Update the light state every second."""
        import time
        
        self.update(int(time.time() % 2))
        self.after(1000, self.tick)

# Test application
if __name__ == '__main__':
    # Create the base frame for the widgets
    root = Tk()
    Pmw.initialise(root)
    root.title("Indicator Lamp")

    # Create an instance with default settings
    widget = IndicatorLamp(root, "10W")
    widget.grid(row=0,column=1)
    widget.tick()

    # Create a custom lamp
    widget2 = IndicatorLamp(root, "600W",
                            (25,25,"black", "white", ["darkgreen", "green"], ['white','black']))
    widget2.grid(row=0,column=2)
    widget2.tick()

    root.mainloop()


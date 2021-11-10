#! /usr//bin/env python

#  Arne Grimstrup
#  2003-09-29
#  Modified 2005-02-10 15:48 Bruce Bon

#  This module implements an AG error plot widget.

from Tkinter import *  # UI widgets and event loop infrastructure
import Pmw             # Additional UI widgets

import ssdlog
import Bunch

#  Default widget configuration
DEFAULTCOLOR = ['green', '#c1ffc1', 'darkgreen']
DEFAULTTARGET = (3, 'yellow', 'red')
DEFAULTSIZE = 300
DEFAULTSCALE = (0.125, 1.001, 0.125, 0.25)
ERRORLINGER = 1000 
DEFAULTGRID = 1


class ErrorWidget(Canvas):

    def __init__(self, parent, psize=DEFAULTSIZE, pscale=DEFAULTSCALE, pgrid=DEFAULTGRID,
                 pbcolor=DEFAULTCOLOR, pointcfg=DEFAULTTARGET, linger=ERRORLINGER, logger=None):
        """Create a new instance of an indicator light with the given configuration."""
        #super(ErrorWidget, self).__init__()
        Canvas.__init__(self, parent) 

        self.color = pbcolor
        self.point = pointcfg
        self.center = int(psize / 2)
        self.showgrid = pgrid
        # Create the plot with numGridLines in the X and Y directions
        self.numGridLines = 5
        # The spacing between the grid lines is pixscale
        self.pixscale = int(psize / self.numGridLines)
        self.scale = pscale
        self.currscale = self.scale[3]
        self.linger = linger
        self.targetlist = []
        self.logger=logger        

        self.cur_circle=5
        self.pre_circle=1

        self.plot_color='blue'
        self.warn_color='magenta'
        self.warn_color='orange'
 
        self.alarm_color='red'
        self.pre_plot_color='black'

        if self.showgrid:
            self.configure(height=psize+15, width=psize+40, bg=self.color[1])
        else:
            self.configure(height=psize, width=psize, bg=self.color[1])
        
        self.vcross = self.create_line(self.center,0,self.center,psize, fill=self.color[0])
        self.hcross = self.create_line(0,self.center,psize,self.center, fill=self.color[0])
        offset = self.pixscale

        self.inner = self.create_oval(self.center-offset,self.center-offset,
                                      self.center+offset,self.center+offset,
                                      outline=self.color[0], width=2)
        
        if self.showgrid:
            
            # button to clear plotting on canvas
            self.clearbtn=Button(self, text='clear', fg='blue', bg=self.color[1], height=1, width=2, command=self.clear_canvas)
            self.clearbtn.pack()
            self.create_window(self.center+offset*3-10, psize+5, window=self.clearbtn)    


            self.crossscalelabel = self.create_text(self.center,psize,anchor='n',
                                                     fill=self.color[2],text='arcsec')
            self.neginvscale = self.create_line(self.center-offset,0,self.center-offset,psize,
                                                fill=self.color[2])
            self.neginvscalelabel = self.create_text(self.center-offset,psize,anchor='n',
                                                     fill=self.color[2],text='%.4f'%(-self.currscale))
            self.posinvscale = self.create_line(self.center+offset,0,self.center+offset,psize,
                                                fill=self.color[2])
            self.posinvscalelabel = self.create_text(self.center+offset,psize,anchor='n',
                                                     fill=self.color[2],text='%.4f'%(self.currscale))
            self.neginhscale = self.create_line(0,self.center-offset,psize,self.center-offset,
                                                fill=self.color[2])
            self.posinhscale = self.create_line(0,self.center+offset,psize,self.center+offset,
                                                fill=self.color[2])
        
        offset = self.pixscale * 2
        self.outer = self.create_oval(self.center-offset,self.center-offset,
                                      self.center+offset,self.center+offset,
                                      outline=self.color[0], width=2)

        if self.showgrid:
            self.negoutvscale = self.create_line(self.center-offset,0,self.center-offset,psize,
                                                 fill=self.color[2])
            self.negoutvscalelabel = self.create_text(self.center-offset,psize,anchor='n',
                                                      fill=self.color[2],
                                                      text='%.4f'%(-2*self.currscale))
            self.posoutvscale = self.create_line(self.center+offset,0,self.center+offset,psize,
                                                 fill=self.color[2])
            self.posoutvscalelabel = self.create_text(self.center+offset,psize,anchor='n',
                                                     fill=self.color[2],text='%.4f'%(2*self.currscale))
            self.negouthscale = self.create_line(0,self.center-offset,psize,self.center-offset,
                                                 fill=self.color[2])
            self.posouthscale = self.create_line(0,self.center+offset,psize,self.center+offset,
                                                 fill=self.color[2])


        self.bind('<Double-Button-1>', self.scaleup)
        self.bind('<Double-Button-2>', self.scaledown)
        #self.bind('<Double-Button-2>', self.clear_canvas)

    def clear_canvas(self):
        """Clear all points from the target list."""
        self.logger.debug('clearing canvas button event...')
        self.clear()
            
    def clear(self):
        """Clear all points from the target list."""
        self.logger.debug('clearing canvas...')    
 
#        self.delete(ALL)    
        for x in self.targetlist:
            self.delete(x.id)
        self.targetlist = []

    def relabel(self):
        self.itemconfigure(self.posoutvscalelabel,text='%.4f'%(2*self.currscale))
        self.itemconfigure(self.negoutvscalelabel,text='%.4f'%(-2*self.currscale))
        self.itemconfigure(self.posinvscalelabel,text='%.4f'%(self.currscale))
        self.itemconfigure(self.neginvscalelabel,text='%.4f'%(-self.currscale))



    def __redraw(self, target, x, y):
        ''' redraw all plotted points based on the change of the scale '''
        px, py=self.calc_pixel_coordinate(x, y)

        target.px=px; target.py=py;

        self.__change_config(target)
  
    def calc_pixel_coordinate(self, x, y):
        ''' calculate pixel values of x,y '''
        px = self.center + int ((x / self.currscale) * self.pixscale)
        py = self.center - int ((y / self.currscale) * self.pixscale)
        return (px, py)

    def __change_config(self, target):
        ''' change both size and color of plotted point  '''

        if target.color==self.warn_color or target.color==self.alarm_color:
            self.itemconfig(target.id, outline=target.color, fill=target.color)
        else:
            self.itemconfig(target.id, outline=self.pre_plot_color, fill=self.pre_plot_color)

        self.coords(target.id, target.px-self.pre_circle, target.py-self.pre_circle, target.px+self.pre_circle, target.py+self.pre_circle )


    def plot_pre_point(self, targetlist):
        ''' re-plot previouly plottd point '''
        self.logger.debug('changing color....')
        num=len(targetlist)
   
        if num < 1:
            return
        
        pre_target=num-1     

        def change_config(target):
            ''' change both size and color of plotted point  '''
        
            if target.color==self.warn_color or target.color==self.alarm_color:
                self.itemconfig(target.id, outline=target.color, fill=target.color)
            else:
                self.itemconfig(target.id, outline=self.pre_plot_color, fill=self.pre_plot_color)
       
            self.coords(target.id, target.px-self.pre_circle, target.py-self.pre_circle, target.px+self.pre_circle, target.py+self.pre_circle )


        self.__change_config(targetlist[pre_target]) 


    def plotpoint(self, x, y):
        ''' plot current point '''
        px,py=self.calc_pixel_coordinate(x, y)

#        color = self.point[1]
        color = self.plot_color
        if px < 0:
            px = 4
            color = self.point[2]
        elif px > self.center * 2:
            px = self.center *2 - 4
            color = self.point[2]
        if py < 0:
            py = 4
            color = self.point[2]
        elif py > self.center * 2:
            py = self.center *2 - 4
            color = self.point[2]

        oval_id = self.create_oval(px-self.cur_circle, py-self.cur_circle, px+self.cur_circle, py+self.cur_circle, outline=color, fill=color)

        return  (oval_id, px, py, color)

    def delete_oldest_plot(self, targetlist):

        if len(targetlist) > self.linger:
            self.delete(targetlist[0].id)
            del targetlist[0]


    def update(self, x, y):
        """Update the label with the time reported by the time management function."""

        self.logger.debug('updating....')
        # convert milli arcseg to arcsec
        x *= 0.001
        y *= 0.001
        self.logger.debug('updating x=%f y=%f' %(x,y))
        
        self.delete_oldest_plot(self.targetlist)
        
        self.plot_pre_point(self.targetlist)

        oval_id, px, py, oval_color=self.plotpoint(x,y)

        self.targetlist.append(Bunch.Bunch(x=x, y=y, id=oval_id, px=px, py=py, color=oval_color))
        
        self.logger.debug('target x=%f y=%f' %(px, py) )
        #self.logger.debug('target list=%s' %str(self.targetlist))

    def scaleup(self, foo):
        self.logger.debug('scaling up...')
        if self.currscale + self.scale[2] > self.scale[1]:
            self.bell()
        else:
            self.currscale += self.scale[2]
            self.redraw()
            if self.showgrid:
                self.relabel()

    def scaledown(self, foo):
        self.logger.debug('scaling down...')
        if self.currscale - self.scale[2] < self.scale[0]:
            self.bell()
        else:
            self.currscale -= self.scale[2]
            self.redraw()
            if self.showgrid:
                self.relabel()

    def redraw(self):
        for star in self.targetlist:
            #self.delete(star.id)
            self.__redraw(star, star.x, star.y)
            #star.id = self.plotpoint(star.x, star.y)

    def tick(self, interval):
        """Update the label every second."""
        import random

        random.seed()
        #x = random.random() * self.currscale * random.randrange(-1,4,2)
        #y = random.random() * self.currscale * random.randrange(-1,4,2)

        x=random.random()*random.randrange(-1000,1000)
        y=random.random()*random.randrange(-1000,1000)
        self.update(x,y)
        self.after(interval, self.tick, interval)

class ErrorWidgetAO(ErrorWidget):

    def __init__(self, parent, psize=DEFAULTSIZE, pscale=DEFAULTSCALE, pgrid=DEFAULTGRID,
                 pbcolor=DEFAULTCOLOR, pointcfg=DEFAULTTARGET, linger=100, logger=None):

        ErrorWidget.__init__(self, parent=parent, psize=DEFAULTSIZE, pscale=DEFAULTSCALE, pgrid=False, pbcolor=DEFAULTCOLOR, pointcfg=DEFAULTTARGET, linger=linger, logger=None)

#        self.targetlist=[]
        self.targetlist2=[]

        self.pre_plot_color='grey'
        self.fillcolor2='white'

        # unit is voltage  
        # AON.TT.TTX/Y alarm
        self.warn_p=6.0   
        self.warn_n=-6.0 
        self.alarm_p=9.0
        self.alarm_n=-9.0   
    
        # AON.TT.WTTC1/2 alarm
        # x-axis in voltage
        self.alarm_c11=2.0  
        self.alarm_c12=8.0

        # y-axis in voltage
        self.alarm_c21=2.0
        self.alarm_c22=8.0


        self.pixscale = int(self.center * 0.4)
        self.currscale = 5.0 # voltage

        self.psize = psize
        self.color = pbcolor
        self.logger=logger

        self.set_grid()

    def set_grid(self):
        
        self.configure(height=self.psize+15, width=self.psize+40, bg=self.color[1])
        self.vcross = self.create_line(self.center,0,self.center,self.psize, fill=self.color[0])
        self.hcross = self.create_line(0,self.center,self.psize,self.center, fill=self.color[0])
        offset = int(self.psize * 0.2)

        self.inner = self.create_oval(self.center-offset,self.center-offset,
                                      self.center+offset,self.center+offset,
                                      outline=self.color[0], width=2)
            
        # button to clear plotting on canvas
        self.clearbtn=Button(self, text='clear', fg='blue', bg=self.color[1], height=1, width=2, command=self.clear_canvas)
        self.clearbtn.pack()
        self.create_window(self.center+offset*3-10, self.psize+5, window=self.clearbtn)    


        self.crossscalelabel = self.create_text(self.center,self.psize,anchor='n',
                                                 fill=self.color[2],text='voltage')
        self.neginvscale = self.create_line(self.center-offset,0,self.center-offset,self.psize,
                                            fill=self.color[2])
        self.neginvscalelabel = self.create_text(self.center-offset,self.psize,anchor='n',
                                                 fill=self.color[2],text='%.1f'%(-self.currscale))
        self.posinvscale = self.create_line(self.center+offset,0,self.center+offset,self.psize,
                                            fill=self.color[2])
        self.posinvscalelabel = self.create_text(self.center+offset,self.psize,anchor='n',
                                                 fill=self.color[2],text='%.1f'%(self.currscale))
        self.neginhscale = self.create_line(0,self.center-offset,self.psize,self.center-offset,
                                            fill=self.color[2])
        self.posinhscale = self.create_line(0,self.center+offset,self.psize,self.center+offset,
                                            fill=self.color[2])
        
        offset = int(self.psize * 0.4)
        self.outer = self.create_oval(self.center-offset,self.center-offset,
                                      self.center+offset,self.center+offset,
                                      outline=self.color[0], width=2)

        self.negoutvscale = self.create_line(self.center-offset,0,self.center-offset,self.psize,
                                             fill=self.color[2])
        self.negoutvscalelabel = self.create_text(self.center-offset,self.psize,anchor='n',
                                                  fill=self.color[2],
                                                  text='%.1f'%(-2*self.currscale))
        self.posoutvscale = self.create_line(self.center+offset,0,self.center+offset,self.psize,
                                             fill=self.color[2])
        self.posoutvscalelabel = self.create_text(self.center+offset,self.psize,anchor='n',
                                                 fill=self.color[2],text='%.1f'%(2*self.currscale))
        self.negouthscale = self.create_line(0,self.center-offset,self.psize,self.center-offset,
                                             fill=self.color[2])
        self.posouthscale = self.create_line(0,self.center+offset,self.psize,self.center+offset,
                                             fill=self.color[2])


    def clear(self):
        """Clear all points from the target list."""
        self.logger.debug('clearing canvas...')    
 
#        self.delete(ALL)    
        for x in self.targetlist:
            self.delete(x.id)
        self.targetlist = []

        for x in self.targetlist2:
            self.delete(x.id)
        self.targetlist2 = []


    def plotpoint(self, x, y):
        ''' plot current point '''

        color = self.plot_color
       
        # warn_p/n = 6.0/-6.0  alarm_p/n=9.0/-9.0
        if (x >= self.alarm_p or x <= self.alarm_n) or (y >= self.alarm_p or y <= self.alarm_n):
            color=self.alarm_color
        elif (self.warn_p <= x or x <= self.warn_n) or (self.warn_p <= y  or y <= self.warn_n):
            color=self.warn_color

        px,py=self.calc_pixel_coordinate(x, y) 

        oval_id = self.create_oval(px-self.cur_circle, py-self.cur_circle, px+self.cur_circle, py+self.cur_circle, outline=color, fill=color)

        return  (oval_id, px, py, color)

    def update(self, x, y):
        """ plotting  x, y in voltage"""

        self.logger.debug('updating x=%f y=%f' %(x,y))
        
        self.delete_oldest_plot(self.targetlist)
        
        self.plot_pre_point(self.targetlist)

        oval_id, px, py, oval_color=self.plotpoint(x,y)

        self.targetlist.append(Bunch.Bunch(x=x, y=y, id=oval_id, px=px, py=py, color=oval_color))
        
        self.logger.debug('target list=%s' %str(self.targetlist))

    def plotpoint_2(self, x, y): 
 
        color = self.plot_color

        # alarm x-axis = 2.0/8.0  alarm y-axis=2.0/8.0
        if (x >= self.alarm_c12 or x <= self.alarm_c11) or (y >= self.alarm_c22 or y <= self.alarm_c21):
            color=self.alarm_color

        px,py=self.calc_pixel_coordinate(x, y) 
   
        oval_id=self.create_rectangle(px-self.cur_circle, py+self.cur_circle, px+self.cur_circle, py-self.cur_circle,  outline=color, fill=self.fillcolor2)
     
        return  (oval_id, px, py, color)

    def plot_pre_point2(self, targetlist):
        ''' re-plot previouly plottd point '''
        self.logger.debug('changing color....')
        num=len(targetlist)
   
        if num < 1:
            return
        
        pre_target=num-1     

        def change_config(target):
            ''' change both size and color of plotted point  '''
        
            if target.color==self.warn_color or target.color==self.alarm_color:
                self.itemconfig(target.id, outline=target.color, fill=self.fillcolor2)
            else:
                self.itemconfig(target.id, outline=self.plot_color, fill=self.fillcolor2)
       
            self.coords(target.id, target.px-self.pre_circle, target.py-self.pre_circle, target.px+self.pre_circle, target.py+self.pre_circle )


        change_config(targetlist[pre_target]) 

    def update2(self, x, y):
        """ plotting  x, y in voltage"""

        self.logger.debug('updating 2 x=%f y=%f' %(x,y))    
 
        self.delete_oldest_plot(self.targetlist2)

        self.plot_pre_point2(self.targetlist2)

        oval_id, px, py, oval_color=self.plotpoint_2(x, y)
        self.targetlist2.append(Bunch.Bunch(x=x, y=y, id=oval_id, px=px, py=py, color=oval_color))

    def tick(self, interval):
        """Update the label every second."""
        import random

        random.seed()

        x=random.random()*random.randrange(-2,2)
        y=random.random()*random.randrange(-12,12)
        self.update(x,y)

        x=random.random()*random.randrange(0,15)
        y=random.random()*random.randrange(0,15)
        self.update2(x,y)


        self.after(interval, self.tick, interval)


def main(options, args):
    
    # Create top level logger.
    logger = ssdlog.make_logger('scatter_plot', options)
 
    try:
        root = Tk()
        Pmw.initialise(root)
        root.title("Error Widget")
        if options.mode=='ag':
            widget = ErrorWidget(parent=root, logger=logger)
        elif options.mode=='ao':
            widget = ErrorWidgetAO(parent=root, logger=logger)
        widget.grid(row=0,column=1)
        widget.tick(options.interval)

        root.mainloop()
    except KeyboardInterrupt, e:
        logger.warn('keyboard interruption....')
        sys.exit(0)

# Test application
if __name__ == '__main__':
    # Create the base frame for the widgets

    from optparse import OptionParser
 
    usage = "usage: %prog [options] command [args]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--display", dest="display", metavar="HOST:N",
                      help="Use X display on HOST:N")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--interval", dest="interval", type='int',
                      default=1000,
                      help="Inverval for plotting(milli sec).")
    optprs.add_option("--mode", dest="mode",
                      default='ag',
                      help="Specify a plotting mode [ag|ao]")

    ssdlog.addlogopts(optprs)
    
    (options, args) = optprs.parse_args()

    if len(args) != 0:
        optprs.error("incorrect number of arguments")

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




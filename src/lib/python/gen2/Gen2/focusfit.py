#! /usr/bin/env python
#
# focusfit.py -- calculate and graph a focus fitting curve
#
# Yasu Sakakibara
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Mar 17 03:33:37 HST 2011
#]
#
"""
Example usage:
  $ ./focusfit.py --fitsdir=/data/VGW --startframe=VGWA00460864 --endframe=VGWA00460884

same thing, but short options:
  $ ./focusfit.py -d /data/VGW -s VGWA00460864 -e VGWA00460884
  
same thing, but using a length:
  $ ./focusfit.py -d /data/VGW -s VGWA00460864 -n 21
  
specify region:
  $ ./focusfit.py -d /data/VGW -s VGWA00460864 -n 21 -r "x1=10, y1=10, x2=20, y2=20"
  use specified region, do fhwm calculation

save cutout image:
  $ ./focusfit.py -d /data/VGW -s VGWA00460864 -n 21 -r "x1=10, y1=10, x2=20, y2=20" -c /tmp
  option -c to specify dir to save cutout(sliced) image. name of fits file will be VGWXXXXX_XdeltaxYdelta. e.g, VGWA00460864_30x30.fits
  option -r is the region of an image you'd like to cutout  

"""


import sys, os
# profile imported below (if needed)
# pdb imported below (if needed)
# optparse imported below (if needed)
import numpy

import gtk, gobject
import matplotlib
matplotlib.use('GTKAgg')
#import matplotlib.pyplot as plt
#import matplotlib.axes.Subplot as subplot
import matplotlib.figure as figure
from  matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as figurecanvas
from matplotlib.patches import Ellipse

import astro.fitsutils as fitsutils
import astro.curvefit as curvefit
import ssdlog
    

version = '20100922.0'

class CurveFitGraph(object):

    def __init__(self, logger, lsf, no_close=True):
        """Takes a logger and a LeastSquareFits object."""
        super(CurveFitGraph, self).__init__()
        
        self.logger = logger
        # least square fits object
        self.lsf = lsf
        self.root = None
        self.no_close = no_close

    def build_window(self):
        self.logger.debug("building window...")
        self.root=gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.root.connect("delete_event", lambda w, e: self.close())
        self.root.set_size_request(500, 400)       
        self.fig=figure.Figure()
        self.ax=self.fig.add_subplot(111)
        self.ax.set_title('')
        self.canvas=figurecanvas(self.fig)
        self.root.set_title("Focus Fitting")

        frame=gtk.VBox() 
        frame.pack_start(self.canvas)
        self.root.add(frame)

        self.root.show_all()
                        
    def _sanity_check_window(self):
        if self.root == None:
            self.build_window()

    def set_title(self, title):
        self._sanity_check_window()
        self.ax.set_title(title)

    def close(self):
        self.logger.debug('closing window....')
        if self.root != None:
            self.root.destroy()
        # so we know we need to rebuild the window next time
        self.root = None
        if self.no_close:
            gtk.main_quit()
        return False

    def clear(self):
        self._sanity_check_window()
        self.logger.debug('clearing canvas...')
        self.ax.cla()

    def raisewin(self):
        self._sanity_check_window()
        self.logger.debug('raising window...')
        gdkwin = self.root.window
        gdkwin.show()

    def _draw(self):
        self.ax.grid(True)
        self.fig.canvas.draw()

    def set_err_msg(self,msg,x,y):
        self._sanity_check_window()
        
        self.ax.text(  x,y,msg, bbox=dict(facecolor='red',  alpha=0.1, ),
        horizontalalignment='center',
        verticalalignment='center',
        fontsize=20, color='red')

        
        #pylab.text(0, 0, msg, size=10, rotation=20, ha="center", va="center",bbox = dict(facecolor="red",alpha=0.7,))
        #pylab.legend(('Model length', 'Data length', 'Total message length'),'center', shadow=True)

        
        #pylab.annotate(msg, horizontalalignment='center', xy=(-100, 100), xytext=(0,30), 
        #               bbox=dict(facecolor='red',  alpha=0.3, ),  verticalalignment='center', fontsize=20)
  
    def display_error(self, msg):
        self._sanity_check_window()

        print 'display error', msg
        #pylab.text(0.5, 0.5, msg, size=50, rotation=20, ha="center", va="center",bbox = dict(facecolor="red",alpha=0.7,), size='x-large')
        self.ax.annotate(msg, horizontalalignment='right', verticalalignment='bottom', fontsize=20)
        #pylab.text(0.5, 0.5, msg, size=50, rotation=20, ha="center", va="center",bbox = dict(facecolor="red",alpha=0.7,))

        #plt.show()
        self._draw()


    def _drawGraph(self, title, result, data, minX, minY,
                   a, b, c):

        # NOTE: unfortunately the raisewin() method does not seem to
        # work on every system, so as a workaround we close first
        # TODO: it would be better to get this working without a close
        self.close()
        self.raisewin()

        el = Ellipse((2, -1), 0.5, 0.5)

        self.clear()
        self.set_title(title)
        
        if result == 'empty':
            # all fwhm calculations failed; no data points found
            msg='No data available: FWHM all failed'
            self.set_err_msg(msg, 0.5, 0.5)
            self._draw()
            return False

        # <-- there are data points
        dpX  = [aDataPoint[0] for aDataPoint in data]
        dpY  = [aDataPoint[1] for aDataPoint in data]
        self.logger.debug("datapoints<%s> dpX<%s> dpY<%s>>" %(str(data), str(dpX),str(dpY) ))

        if result == 'singular':
            msg='bad data: result matrix is singular \ncurve fitting failed'
            self.ax.plot(dpX, dpY, 'ro')
            self.set_err_msg(msg, 0.5*(min(dpX)+max(dpX)), 0.5*(min(dpY)+max(dpY)))
            self._draw()
            return False

        if result == 'positive':
            msg="fitting curve calc failed\n a*x**2 + b*x + c \n a[%.3f] must be positive"  %(a)
            self.set_err_msg(msg, 0.465*(min(dpX)+max(dpX)), 0.5*(min(dpY)+max(dpY)))
            self.ax.plot(dpX, dpY, 'o')
            #pylab.text(0.5, 0.5, msg, size=50, rotation=20, ha="center", va="center",bbox = dict(facecolor="red",alpha=0.7,))
            self._draw()
            return False

        # <-- maybe ok
        stX=dpX[0]
        enX=dpX[-1]
        numdataX = len(dpX)
        self.logger.debug(" stX[%s] minX[%s] enX[%s]  dpYmin<%s> minY<%s>  dpYmax<%s>" \
                           %(str(stX), str(minX), str(enX),  str(min(dpY)), str(minY), str(max(dpY)) ) )
                         
        # TODO: Hard coded constants!!
        t1 = numpy.arange(stX -0.035  , enX + 0.035, 0.005)
        
        t2 = self.lsf.plotQuadratic(t1, a, b, c)
        self.ax.plot(dpX, dpY, 'go', t1, t2)
                
        if dpX[0] <= minX <= dpX[-1]:
            self.ax.annotate('Z : %+.4f \nFWHM : %.4f(arcsec)' % (minX, minY) , xy=(minX, minY), xytext=(minX + 0.00001, max(dpY)-0.1),
                           bbox=dict(boxstyle="round",facecolor='green',ec="none",  alpha=0.1, ),
                           size=25, color='b',
                           arrowprops=dict(arrowstyle="wedge,tail_width=2.0",facecolor='green', ec="none", alpha=0.1, patchA=None, relpos=(0.5, -0.09)),
                           horizontalalignment='center')

               
            self.logger.debug("Z[%f] Fwhm[%f]" %(minX, minY) )
            #self.fig.canvas.set_window_title("Z[%f] Fwhm[%f]" %(minX, minY) )           

        else:
            self.logger.error("X<%s>  or Y<%s>  is out of range X<%s> Y<%s> " %(str(minX),str(minY), str(dpX), str(dpY)) )
            msg="z is out of range\nmin[%.3f] < z[%.3f] < max[%.3f]" %(dpX[0], minX, dpX[-1])
            self.set_err_msg(msg , 0.5*(min(dpX)+max(dpX)), 0.5*(min(dpY)+max(dpY)) )

        self._draw()
        return False

    def mainloop(self):
        gtk.gdk.threads_init()

        self._sanity_check_window()
              
        return gtk.main()

    def focus_fitting(self, file_list, x1=None, y1=None, x2=None, y2=None):
        """This method can be called by other threads.
        """

        try:
            # get beginning and ending frameids for title
            path,s_fits=os.path.split(file_list[0])
            path,e_fits=os.path.split(file_list[-1])
            s_fitsid,ext=os.path.splitext(s_fits)
            e_fitsid,ext=os.path.splitext(e_fits)
            title='%s ~ %s' %(s_fitsid,e_fitsid)
            self.logger.debug('fits %s' %(title)) 
        except OSError,e:
            self.logger.error('fail to set title %s' %str(e))
            title=''
            pass
 
        z = None
        try:
            data_points = self.lsf.buildDataPoints(file_list, x1, y1, x2, y2)

            result = 'unknown'
            lsf_b = self.lsf.fitCurve(data_points)
            result = lsf_b.code

            z = lsf_b.minX; fwhm = lsf_b.minY
            self.logger.debug("result=%s z=%s fwhm=%s" % (result, z, fwhm))
            
            # draw graph at next available opportunity
            gobject.idle_add(self._drawGraph, title, result,
                             data_points, z, fwhm, lsf_b.a, lsf_b.b, lsf_b.c)

        except Exception, e:
            self.logger.error("focus fitting error <%s>" % (str(e)))

        return z           

        
def main(options, args):
  
    logname = 'least_sq'
    logger = ssdlog.make_logger(logname, options)
 
    # make an instance of LeastSquareFits before importing getFrameInfoFromPath
    # otherwise, some pyfits error is caused.  
    lsf = curvefit.LeastSquareFits(logger)
    focusfit = CurveFitGraph(logger, lsf)
 
    if not options.fitsdir:
        logger.error("No --fitsdir given!")
        sys.exit(1)

    if not options.startframe:
        logger.error("No --startframe given!")
        sys.exit(1)

    # Get the starting frame
    (frameid, fitsname, fitsdir, inscode, frametype,
     frame_no) = fitsutils.getFrameInfoFromPath(options.startframe)
    st_fnum = frame_no

    # We'd better have an --endframe or a --numframes
    if options.endframe:
        (frameid, fitsname, fitsdir, inscode, frametype,
         frame_no) = fitsutils.getFrameInfoFromPath(options.endframe)
        en_fnum = frame_no

    elif options.numframes:
        en_fnum = st_fnum + options.numframes

    else:
        logger.error("No --endframe or --numframes given!")
        sys.exit(1)

    if options.region:
        region=options.region.split(',')
        logger.debug("frame region<%s> " % region )
        x1=region[0].strip(); y1=region[1].strip(); x2=region[2].strip(); y2=region[3].strip();
        x1=int(x1[3:]); y1=int(y1[3:]); x2=int(x2[3:]); y2=int(y2[3:]); 
        logger.debug("frame region x1<%s> y1<%s> x2<%s> y2<%s> " % (x1, y1, x2, y2) )  
    else:
        x1=y1=x2=y2=None
        
    if options.cutout:
        cutout = options.cutout
        logger.debug("cutout image <%s> " % cutout )
    else:
        cutout=None   

    # Calculate the frame list
    framelist = [ "%s%s%08d" % (inscode, frametype, i) \
                  for i in range(st_fnum, en_fnum) ]
    logger.debug("framelist=%s" % str(framelist))

    try:
        gtk.gdk.threads_init()

        focusfit.set_title('focus fitting test')

        file_list=lsf.make_file_list(options.fitsdir, framelist)

        z = focusfit.focus_fitting(file_list, x1, y1, x2, y2)
        logger.debug('z=%s' % str(z))
    
        focusfit.mainloop()

    except KeyboardInterrupt, e:
        logger.error('Caught keyboard interrupt!')

    except Exception,e:
        logger.error('focus fitting error %s' %(e))


if __name__ == '__main__':
  
    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options] [<frameid>] ..."
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    
    optprs.add_option("-e", "--endframe", dest="endframe",
                      metavar="FRAMEID",
                      help="Specify an ending FRAMEID")
    optprs.add_option("-d", "--fitsdir", dest="fitsdir", metavar="DIR",
                      help="Use DIR for fetching instrument FITS files")
    optprs.add_option("-n", "--numframes", dest="numframes", type="int",
                      help="Use NUM frames for fitting", metavar="NUM")
    optprs.add_option("-r", "--region", dest="region",
                      help="Use REG 'x1=xx, y1=xx, x2=xx, y2=xx' to specify frame region for slicing an image", metavar="REG")
    optprs.add_option("-c", "--cutout", dest="cutout",
                      help="Save cutout image; specify a path to save an sliced image, file name will be frameid_size.fits  ", metavar="CUT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("-s", "--startframe", dest="startframe",
                      metavar="FRAMEID",
                      help="Specify a starting FRAMEID")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

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

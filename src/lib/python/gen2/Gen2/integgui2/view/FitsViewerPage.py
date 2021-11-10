# 
# Eric Jeschke (eric@naoj.org)
#
# stdlib imports
import os.path
import time
import numpy
import pyfits
import threading

# GUI imports
import gtk

import common
import Page

import astro.fitsdata as fitsdata
from ginga.misc import Bunch, Datasrc
from ginga.gtkw.FitsImageCanvasGtk import FitsImageCanvas


class FitsViewerPage(Page.ButtonPage):

    def __init__(self, datasrc, logger, ev_quit=None):
        """Implements a fancier display with buttons and accouterments.
        """
        
    def __init__(self, frame, name, title):

        super(FitsViewerPage, self).__init__(frame, name, title)

        # datasrc for incoming images
        self.datasrc = Datasrc.Datasrc(length=40)

        self.cursor = 0
        self.saved_cursor = 0

        self.lock = threading.RLock()

        vbox = gtk.VBox()
        hbox1 = gtk.HPaned()

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_border_width(2)

        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,
                                   gtk.POLICY_AUTOMATIC)

        self.fitsinfo = gtk.TextView()
        self.fitsinfo.set_editable(False)
        self.fitsinfo.set_wrap_mode(gtk.WRAP_NONE)
        self.fitsinfo.set_left_margin(4)
        self.fitsinfo.set_right_margin(4)
        scrolled_window.add(self.fitsinfo)
        self.fitsinfo.show()
        scrolled_window.show()

        scrolled_window.set_size_request(250, -1)
        hbox1.add1(scrolled_window)

        self.fitsimage = FitsImageCanvas()
        self.widget = self.fitsimage.get_widget()

        hbox1.add2(self.widget)
        hbox1.show()

        # Colormap we will use for image display
        #self.cmap = cm.gray
        self.cmap = 'gray'
        
        # Initialize the viewer with an empty image
        data = numpy.zeros((512,512))
        self.image = Bunch.Bunch(name='', width=512, height=512,
                           data=data, header={})
        self.datasrc['__'] = self.image

        vbox.pack_start(hbox1, expand=True, fill=True)

        self.add_close()
        
        self.btn_load = gtk.Button("Load")
        self.btn_load.connect("clicked", lambda w: self.load_fits())
        self.btn_load.show()
        self.leftbtns.pack_end(self.btn_load, padding=4)

##         self.btn_save = gtk.Button("Save")
##         self.btn_save.connect("clicked", lambda w: self.save())
##         self.btn_save.show()
##         self.leftbtns.pack_end(self.btn_save, padding=4)

        vbox.show()
        
        frame.pack_start(vbox, expand=True, fill=True)

        frame.show_all()
        

    def cut_levels(self, w):
        with self.lock:
            self.logger.debug("Cut levels")
            fitsdata.cut_levels(self.image.data)
            self.update_img()
        return True


    def prev_img_in_list(self, w):
        with self.lock:
            self.logger.debug("Previous image")
            try:
                self.image = self.datasrc[self.cursor-1]
                self.cursor -= 1
                self.update_img()
            except IndexError:
                self.showStatus("No previous image!")
                self.logger.error("No previous image!")
            
        return True


    def next_img_in_list(self, w):
        with self.lock:
            self.logger.debug("Next image")
            try:
                self.image = self.datasrc[self.cursor+1]
                self.cursor += 1
                self.update_img()
            except IndexError:
                self.showStatus("No next image!")
                self.logger.error("No next image!")

        return True


    def load_image_datasrc(self, name):

        with self.lock:
            self.cursor = self.datasrc.index(name)
            #self.image = self.datasrc[self.cursor]
            self.image = self.datasrc[name]

            imagelist = self.datasrc.keys()

##             w = self.history
##             clear_tv(w)
##             append_tv(w, '\n'.join(imagelist))

            self.update_img()

                
    def load(self, fitspath):
        """Loads a command file from _path_ into the commands window.
        """
        with self.lock:
            imgb = self.open_fits(fitspath)

            self.fitspath = fitspath
            
            # Enqueue image to display datasrc
            self.datasrc[imgb.name] = imgb

            self.load_image_datasrc(imgb.name)


    def open_fits(self, fitspath):

        fits_f = pyfits.open(fitspath, "readonly")

        # this seems to be necessary now for some fits files...
        fits_f.verify('fix')

        data = fits_f[0].data

        header = fits_f[0].header
        fits_f.close()

        if len(data.shape) == 2:
            (width, height) = data.shape
        elif len(data.shape) > 2:
            while len(data.shape) > 2:
                data = data[0]
            (width, height) = data.shape
        else:
            raise Exception("Data shape of FITS file is undetermined!")

        (path, filename) = os.path.split(fitspath)

        # Create a bunch with the image params
        imgb = Bunch.Bunch(name=filename, path=fitspath,
                           width=width, height=height,
                           data=data, header=header)

        return imgb

    
    def update_img(self):
        """Update the image in the window, based on changes to the
        image data contained in self.image.data.
        """

        with self.lock:
            self.logger.debug("Update image start")
            curtime = time.time()
            try:
                self.fitsimage.set_data(self.image.data)
                
                # Update the header info
                hdr_list = []
                for (key, val) in self.image.header.items():
                    hdr_list.append("%-8.8s : %s" % (key, str(val)))

                w = self.fitsinfo
                common.clear_tv(w)
                common.append_tv(w, '\n'.join(hdr_list))
                self.logger.debug("Update fits kwds: %.4f sec" % (time.time() - curtime))
                
                tottime = time.time() - curtime
                self.logger.debug("Update image end: time=%.4f sec" % tottime)

            finally:
                pass

        return True


#END

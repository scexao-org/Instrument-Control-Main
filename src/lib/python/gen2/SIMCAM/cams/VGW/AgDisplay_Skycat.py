# 
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri May  6 12:51:04 HST 2011
#]

# stdlib imports
import os
import numpy
import pyfits
import threading
import subprocess
import time

import Bunch
import rtd
import SkycatControl as skycat

class AgDisplayError(Exception):
    pass

class AgDisplay(object):
    """The AgDisplay class handles displaying the received AG data in a
    GUI.
    """
    def __init__(self, agkey, aginfo, logger, ev_quit=None):

        super(AgDisplay, self).__init__()

        self.aginfo = aginfo
        self.name = aginfo.name
        self.agkey = agkey
        self.width = aginfo.maxwd
        self.height = aginfo.maxht
        self.datasize = -32
        self.buffers = 1
        self.bytes_per_pixel = 2
        self.logger = logger
        if not ev_quit:
            ev_quit = threading.Event()
        self.ev_quit = ev_quit

        self.host = 'localhost'
        self.port = 30000 + aginfo.index
        self.shmkey = 40800 + (aginfo.index * self.buffers)
        self.semkey = 40800 + (aginfo.index * self.buffers)
        self.skycat_proc = None

        self.lock = threading.RLock()

        self.previous_graphics_state = None

    def start(self):
        self.connect_rtd()
        #self.start_skycat()
        self.connect_skycat()
        self.clear_rect()

    def stop(self):
        self.clear_rect()
        self.disconnect_skycat()
        self.rtd = None
        #self.stop_skycat()
        
    def start_skycat(self):
        self.logger.info("Starting skycat...")
        skycat_cmd = "skycat -rtd 1" % (self.port)
        self.skycat_proc = subprocess.Popen(skycat_cmd, shell=True)
        # TODO: look for connection at port
        time.sleep(3)
        
    def stop_skycat(self):
        if self.skycat_proc:
            self.skycat_proc.kill()
            
    def connect_skycat(self):
        self.logger.info("Connecting to skycat at %s:%d" % (
            self.host, self.port))
        try:
            self.skycat = skycat.SkycatControl(self.host, self.port,
                                               self.logger)
            self.skycat.connect()
            title = '%s (%d)' % (self.name, self.port)
            self.skycat.update_title(title)
            self.skycat.send_command("camera attach %s" % self.agkey)

        except Exception, e:
            self.logger.error(str(e))
            raise e

    def disconnect_skycat(self):
        title = '%s (disconnected)' % (self.name)
        self.skycat.send_command("camera detach")
        self.skycat.update_title(title)
        self.skycat.close()

    def connect_rtd(self):
        self.logger.info("Connecting to RTD camera '%s'" % (self.agkey))
        try:
            # dereferencing the object (in stop()) should cause the
            # object to be DECREFed and the IPC resources to be reclaimed
            # you can check this with ipcs -sm | grep <shmkey>
            # using the shmkey listed in the debug statement
            self.rtd = rtd.Rtd(self.agkey, self.width, self.height,
                               self.datasize, buffers=self.buffers,
                               shmkey=self.shmkey, semkey=self.semkey)
            self.logger.debug("shmkey=0x%08x semkey=0x%08x" % (
                self.shmkey, self.semkey))
            self.rtd.unlock()

            ## self.datafile = '/tmp/%s_data' % self.agkey
            ## self.f_data = pyfits.open(self.datafile, mode='update', memmap=1)
            ## self.f_header = open('/tmp/%s_header' % self.agkey, 'w')

        except Exception, e:
            self.logger.error(str(e))
            raise e

    ## def make_fitshdr(self, fitsobj):
    ##     hdr = fitsobj[0].header
    ##     header = str(hdr).replace('\n', '')
    ##     padlen = len(header) % 2880
    ##     header = header + (' '*padlen)
    ##     return header
        
    def update_image(self, image):
        self.logger.debug("Updating gui image...")
        data = image.data

        objname = image.get_keyword('OBJECT', 'Noname')
        
        ## self.f_data.seek(0)
        ## self.f_data.write(data.tostring())
        ## self.f_data.flush()

        ## self.logger.debug("Updating header file...")
        ## self.f_header.seek(0)
        ## self.f_header.write(self.make_fitshdr(fitsobj))
        ## self.f_header.flush()
        ##with self.lock:
        try:
            ## fitsobj.writeto(self.datafile, output_verify='silentfix',
            ##                 clobber=True)
            ## for key, val in fitsobj[0].header.items():
            ##     self.f_data[0].header.update(key, val)

            ## #self.f_data[0].data[:] = fitsobj[0].data[:]
            ## self.f_data[0].data = fitsobj[0].data
            ## self.f_data.flush()

            res = self.rtd.update_np(data, self.datasize, self.bytes_per_pixel)

            self.skycat.update_object(objname)

            # If we are guiding, then set our calculation region and draw
            # a rectangle on the image
            guiding = image.get('hasregion', False)
            if guiding:
                x1, y1, x2, y2 = image.get_region()
                self.draw_rect(x1, y1, x2, y2)
            else:
                self.clear_rect()

            quality = image.get('quality', None)
            if quality:
                self.update_quality(quality)
                
        except Exception, e:
            self.logger.error("Error updating fits image (%s): %s" % (
                self.agkey, str(e)))


    def exec_tcl(self, cmdstr):
        try:
            res = os.system(cmdstr)
            if res != 0:
                errstr = "TCL command (%s) failed: res=%d" % (cmdstr, res)
                self.logger.error(errstr)
                raise AgDisplayError(errstr)

        except OSError, e:
            errstr = "TCL command (%s) failed: %s" % (cmdstr, str(e))
            self.logger.error(errstr)
            raise AgDisplayError(errstr)
            

    def clear_rect(self):
        if self.previous_graphics_state == 'CLEAR':
            return
        
        self.logger.debug("Clearing gui rectangle...")

        ## Used to be done by DAQvgwXXClear.tcl
        image = ".skycat1.image"
        canvas  = "%s.imagef.canvas" % image
        ids = self.skycat.send_tcl("%s find withtag bling" % (canvas))
        res = self.skycat.send_tcl("%s delete %s" % (canvas, ids))
            
        self.previous_graphics_state = 'CLEAR'
        
    def draw_rect(self, x1, y1, x2, y2):
        if self.previous_graphics_state == ('RECT', x1, y1, x2, y2):
            return
        
        self.clear_rect()
        
        self.logger.debug("Drawing gui rectangle...")

        ## Used to be done by DAQvgwXXEdit.tcl
        image = ".skycat1.image"
        canvas  = "%s.imagef.canvas" % image
        
        # convert coordinates
        res = self.skycat.send_tcl("%s convert coords %d %d image {} {} canvas" % (
            image, x1, y1))
        cx1, cy1 = map(int, res.split())
        res = self.skycat.send_tcl("%s convert coords %d %d image {} {} canvas" % (
            image, x2, y2))
        cx2, cy2 = map(int, res.split())
        self.logger.debug("coords are %d %d %d %d" % (cx1, cy1, cx2, cy2))

        # draw rectangle QDASvgwComEditRectAG
        res = self.skycat.send_tcl("%s create rectangle %d %d %d %d -outline cyan -tags bling" % (
            canvas, cx1, cy1, cx2, cy2))

        # determine best coordinates for text label
        cx = max(cx1, cx2)
        cy = min(cy1, cy2)

       # draw label 
        res = self.skycat.send_tcl('%s create text %d %d -fill gold -text {Calc Region} -justify left -tags bling' % (
            canvas, cx, cy))

        self.previous_graphics_state = ('RECT', x1, y1, x2, y2)
        
    def raise_win(self):
        res = self.skycat.send_tcl("raise .")

    def update_rates(self, avg, peak, delta):
        gui = self.aginfo.agmain
        if avg > delta:
            col_s = ' background="red"'
        else:
            col_s = ''
        gui.gui_do(self.aginfo.w_rateavg2.set_markup, '<span%s>%.3f</span>' % (
            col_s, avg))

        if peak > delta:
            col_s = ' background="yellow"'
        else:
            col_s = ''
        gui.gui_do(self.aginfo.w_ratepeak2.set_markup, '<span%s>%.3f</span>' % (
            col_s, peak))
        
    def update_quality(self, quality):
        def __update():
            self.logger.debug("Setting quality info!")
            self.aginfo.w_fwhm.set_text('%.3f' % quality.fwhm)
            self.aginfo.w_starsize.set_text('%.3f' % quality.starsize)
            self.aginfo.w_skylvl.set_text('%.3f' % quality.skylevel)
            self.aginfo.w_brightness.set_text('%.3f' % quality.brightness)
            self.aginfo.w_calctime.set_text('%.3f' % quality.calctime)
            
        gui = self.aginfo.agmain
        if quality != None:
            gui.gui_do(__update)
        else:
            pass
            # TODO: show some error condition visually

#END

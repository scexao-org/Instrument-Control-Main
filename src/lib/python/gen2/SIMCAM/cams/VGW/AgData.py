#
# AgData.py -- support class for VGW instrument
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Apr 15 17:04:03 HST 2013
#]
#
import time
import sys, traceback
import threading, Queue
import math

import os
import numpy
import pyfits
import qualsize

import SOSS.GuiderInt.Ag as Ag
from ginga.AstroImage import AstroImage
from ginga import wcs, iqcalc
from ginga.misc import Bunch
import SOSS.GuiderInt.guiderfitsheader as gfh
import Task
import remoteObjects as ro

class AgError(Exception):
    pass

class AgImage(AstroImage):

    def get_status(self, alias):
        # User is assumed to have attached a status metadata
        return self.metadata['status'][alias]
    
    def get_status_list(self, *args):
        return map(self.get_status, args)

    def get_agheader(self, name):
        # User is assumed to have attached a agheader metadata
        return self.metadata['agheader'][name]
    
    def get_agheader_list(self, *args):
        return map(self.get_agheader, args)
    
    def get_agtime(self):
        # User is assumed to have attached a agtime metadata
        return self.metadata['agtime']
    

class AgRpcHandler(Ag.AgServer):
    """AgRpcHandler class handles the AG data packets received by the RPC
    interface.  Basically, we just overload the AgServer class to provide
    a new 'process' method.
    """

    def __init__(self, agdata, logger, ev_quit=None, delta=1.0, agtype='AG'): 
        self.agdata = agdata
        self.logger = logger
        self.ev_quit = ev_quit

        # Initialize my AG handler
        super(AgRpcHandler, self).__init__(self.logger, ev_quit=self.ev_quit,
                                           delta=delta, agtype=agtype)
         
       
    def process(self, agheader, datatime, data_np):
        """Process AG data packet.
        _agheader_ is a string corresponding to the AG header string.
        _datatime_ is the data time (as float) of the data.
        _data_np_ is a numpy of the pixel data.
        """

        self.logger.debug("datatime: %8.4f  header: %s" % (
            datatime, str(agheader)))
        
        try:
            metadata = dict(agtime=datatime, agheader=agheader)

            # convert data to floats
            data_np = data_np.astype('float32')
            
            # make a generic CCD image wrapper
            image = AgImage(data_np, metadata=metadata,
                            wcsclass=wcs.BareBonesWCS)

            height, width = data_np.shape
            self.logger.debug("data shape is %dx%d" % (width, height))

            # hand it to the AgDataHandler
            self.agdata.update_data(image)

        except Exception, e:
            self.logger.error("Error processing AG data: %s" % (
                str(e)))
            (type, value, tback) = sys.exc_info()
            #self.logger.error("Traceback:\n%s" % \
            #                  tback.format_exec())
            self.logger.error("Traceback:\n%s" % \
                              str(tback))
            traceback.print_tb(tback)

        

class AgDataHandler(object):
    """The AgDataHandler class handles the received AG data.
    """
    def __init__(self, agbnch, logger, delta=1.0, fitshelper=None,
                 statusset=None, vgwcam=None, imagequeue=None):

        self.agbnch = agbnch
        self.logger = logger
        self.agcount = 0
        # Set to a bunch of quality metrics if compute quality is enabled
        self.quality = None

        self.params = Bunch.threadSafeBunch()
        self.params.delta = delta
        self.params.compute_quality = True
        self.last_time = 0.0

        self.lock = threading.RLock()

        # Used for saving images
        self.save_count = 0
        if not imagequeue:
            imagequeue = Queue.Queue()
        self.imagequeue = imagequeue

        # for timings
        self.time_last_report = 0.0
        self.peak_time = 0.0
        self.total_time = 0.0
        self.time_count = 0
        
        self.clear()

        # Object that allows us to form a fits header
        self.fitshelper = fitshelper
        self.statusset = statusset
        self.vgwcam = vgwcam
        self.statusDict = {}.fromkeys(self.statusset.ALL, None)
        self.proxySt = ro.remoteObjectProxy('status')

    def clear(self):
        width = self.agbnch.maxwd
        height = self.agbnch.maxht
        metadata = {}

        # initialize the guide image to zeros
        data_np = numpy.zeros((height, width)).astype('float32')
        with self.lock:
            #self.image = AstroImage(data_np, metadata=metadata)
            self.image = AgImage(data_np, metadata=metadata,
                                 wcsclass=wcs.BareBonesWCS)

            self.update_displays()

    ## def update_header(self, image):
    ##     agheader, agtime = image.get_list('agheader', 'time')

    ##     header = {}
    ##     self.fitshdr.fillheader(header, aghdr=agheader,
    ##                             agtime=agtime, status=self.ocsstatus)
    ##     print header
    ##     image.update_keywords(header)
    ##     ## agkey, aginfo = Ag.ag_map[agheader.insCode]
    ##     ## foci = agheader.foci
    ##     ## header = {
    ##     ##     # Get pixel scale
    ##     ##     'CDELT1': aginfo[foci].degx,
    ##     ##     'CUNIT1': 'degrees',
    ##     ##     'CDELT2': aginfo[foci].degy,
    ##     ##     'CUNIT2': 'degrees',
    ##     ##     'TELFOCUS': Ag.ag_foci[foci],
    ##     ##     'PRD-MIN1': 0,
    ##     ##     'PRD-MIN2': 0,
    ##     ##     'PRD-RNG1': aginfo[foci].ccdx,
    ##     ##     'PRD-RNG2': aginfo[foci].ccdy,
    ##     ##     'BIN-FCT1': agheader.binX,
    ##     ##     'BIN-FCT2': agheader.binY,
    ##     ##     'EXPTIME': agheader.expTime / 1000.0,
    ##     ##     'CRPIX1': float(aginfo[foci].ccdx)/2.0,
    ##     ##     'CRPIX2': float(aginfo[foci].ccdy)/2.0,
    ##     ##     'INSTRUME': agkey,
    ##     ##     'DETECTOR': agkey,
    ##     ##     }

    def set_calc_window(self, image):
        """If there is a centroid calculation being performed on the TCS
        side, calculate the region in our image and set the coordinates
        in this image.
        """

        cX = cY = cWd = cHt = 0
        eX = eY = eWd = eHt = 0
        guiding = False
        image.set(hasregion=guiding)
        area = 'NONE'
        agkey = self.agbnch.name
        self.logger.debug("My key is '%s'" % (agkey))

        # Get status and agheader, which are attached as metadata to the
        # image
        status = image.get('status')
        agheader = image.get('agheader')

        # Examine recent status to determine whether a centroid is
        # being calculated on the TCS side, and if so, what the
        # calculation region is
        if agkey in ('AG', 'HSCSCAG', 'FMOS', 'QDAS'):
            mode = status['TSCV.AGCCalc']
            self.logger.debug("agccalc=%x" % (mode))
            if (mode & 0x04 != 0):
                # AG1 guider
                guiding = True; area = 'AG1'
                cX = status['TSCV.AGCCalcRegX11']
                cY = status['TSCV.AGCCalcRegY11']
                cWd = status['TSCV.AGCCalcRegX21']
                cHt = status['TSCV.AGCCalcRegY21']
                ## eX = status['TSCV.AGImgRegX1']
                ## eWd = status['TSCV.AGImgRegX2']
                ## eY = status['TSCV.AGImgRegY1']
                ## eHt = status['TSCV.AGImgRegY2']
            
            elif (mode & 0x10 != 0):
                # AG2 guider
                guiding = True; area = 'AG2'
                cX = status['TSCV.AGCCalcRegX12']
                cY = status['TSCV.AGCCalcRegY12']
                cWd = status['TSCV.AGCCalcRegX22']
                cHt = status['TSCV.AGCCalcRegY22']
                ## eX = status['TSCV.AGImgRegX1']
                ## eWd = status['TSCV.AGImgRegX2']
                ## eY = status['TSCV.AGImgRegY1']
                ## eHt = status['TSCV.AGImgRegY2']

        elif agkey in ('SV',):
            mode = status['TSCV.SVCCalc']
            self.logger.debug("svccalc=%x" % (mode))
            if (mode & 0x04 != 0):
                # SV1 guider
                guiding = True; area = 'SV1'
                cX = status['TSCV.SVCCalcRegX11']
                cY = status['TSCV.SVCCalcRegY11']
                cWd = status['TSCV.SVCCalcRegX21']
                cHt = status['TSCV.SVCCalcRegY21']
                ## eX = status['TSCV.SVImgRegX1']
                ## eWd = status['TSCV.SVImgRegX2']
                ## eY = status['TSCV.SVImgRegY1']
                ## eHt = status['TSCV.SVImgRegY2']
            
            elif (mode & 0x10 != 0):
                # SV2 guider
                guiding = True; area = 'SV2'
                cX = status['TSCV.SVCCalcRegX12']
                cY = status['TSCV.SVCCalcRegY12']
                cWd = status['TSCV.SVCCalcRegX22']
                cHt = status['TSCV.SVCCalcRegY22']
                ## eX = status['TSCV.SVImgRegX1']
                ## eWd = status['TSCV.SVImgRegX2']
                ## eY = status['TSCV.SVImgRegY1']
                ## eHt = status['TSCV.SVImgRegY2']

        else:
            raise AgError("Don't know how to calculate region for '%s'" % (
                agkey))

        image.set(guidearea=area)
        if not guiding:
            return

        # <== TCS side is calculating a centroid
        # convert to ints
        ## cX, cY, cWd, cHt, eX, eY, eWd, eHt = map(
        ##     int, (cX, cY, cWd, cHt, eX, eY, eWd, eHt))
        cX, cY, cWd, cHt = map(int, (cX, cY, cWd, cHt))

        # Prefer the info coming from the AG header over the status
        # for establishing the exposure range in the CCD
        eX = agheader.expRangeX
        eY = agheader.expRangeY
        eWd = agheader.expRangeDX
        eHt = agheader.expRangeDY
        binX = agheader.binX
        binY = agheader.binY

        # Check if calculation region is totally enclosed by the
        # guide image area we've received
        cX2 = cX + cWd; cY2 = cY + cWd
        eX2 = eX + eWd; eY2 = eY + eWd
        if ((cX < eX) or (cY < eY) or (cX2 > eX2) or (cY2 > eY2)):
            errmsg = "Calculation region not enclosed in guide image area: calc=(%d,%d),(%d,%d) exp=(%d,%d),(%d,%d)" % (
                cX, cY, cX2, cY2, eX, eY, eX2, eY2)
            raise AgError(errmsg)
            
        # calculation and exposure regions are reported in absolute
        # pixels on the AG sensor.  subtract exposure region so that we
        # know the offsets into our guide image (we receive just a
        # clip of the exposure region)
        cX = cX - eX; cY = cY - eY
        # Clip may be binned, resulting in a smaller image.  Adjust
        # accordingly.
        x1 = cX // binX  ; y1 = cY // binY
        cWd = cWd // binX; cHt = cHt // binY
        x2 = x1 + cWd - 1; y2 = y1 + cHt - 1

        # <== x1,y1,x2,y2 should be the region on OUR image
        # Sanity check on the transformed region, that the coordinates actually
        # are inside the dimensions of the clipped image we received
        try:
            assert((x1 >= 0) and (x1 < agheader.numPixX))
            assert((y1 >= 0) and (y1 < agheader.numPixY))
            assert((x2 >= 0) and (x2 < agheader.numPixX))
            assert((y2 >= 0) and (y2 < agheader.numPixY))
        except AssertionError:
            errmsg = "Transformed calculation region not enclosed in the clip image area: calc=(%d,%d),(%d,%d) image=(%d,%d),(%d,%d)" % (
                x1, y1, x2, y2, 0, 0, agheader.numPixX, agheader.numPixY)
            raise AgError(errmsg)
            
        ## image.set(hasregion=True)
        ## image.set_region(x1, y1, x2, y2)
        image.set(hasregion=True, region=(x1, y1, x2, y2))
        self.logger.debug("Region: area=%s x1=%d y1=%d x2=%d y2=%d" % (
            area, x1, y1, x2, y2))
                
                
    def starsize(self, fwhm_x, deg_pix_x, fwhm_y, deg_pix_y):
        cdelta1 = math.fabs(deg_pix_x)
        cdelta2 = math.fabs(deg_pix_y)
        fwhm = (fwhm_x * cdelta1 + fwhm_y * cdelta2) / 2.0
        fwhm = fwhm * 3600.0
        return fwhm

    def compute_quality_metrics(self, image):
        try:
            time_start = time.time()
            image.set(quality=None)

            # Figure out if we are guiding or not and what the centroid
            # region is
            self.set_calc_window(image)

            hasregion = image.get('hasregion', False)
            if not hasregion:
                # <== No centroid region is set on the TCS side--seemingly
                return None

            # TODO
            # Do we really need to compute this here?  Are any abstract
            # commands using these values?
            (x1, y1, x2, y2) = image.get('region')
            data = image.cutout_data(x1, y1, x2, y2)
            (x, y, fwhm, brightness, skylevel, objx, objy) = qualsize.qualsize(
                data)
            qs = Bunch.Bunch(x=x, y=y, fwhm=fwhm, brightness=brightness,
                             skylevel=skylevel, objx=objx, objy=objy)
            qs.x += x1
            qs.y += y1
            qs.objx += x1
            qs.objy += y1
            image.set(quality=qs)

            # Get the degrees/pixel on the sensor for the particular
            # camera this image came from
            agheader = image.get('agheader')
            agkey, aginfo = Ag.ag_map[agheader.insCode]
            foci = agheader.foci
            self.logger.info("aginfo=%s" % str(aginfo))
            deg_pix_x = aginfo['foci'][foci]['degx']
            deg_pix_y = aginfo['foci'][foci]['degy']

            qs.starsize = self.starsize(qs.fwhm, deg_pix_x,
                                        qs.fwhm, deg_pix_y)
            
            elapsed_time = time.time() - time_start
            quality.calctime = elapsed_time
            self.logger.info("quality metrics: %s" % (
                str(qs)))
            self.logger.debug("Time to compute quality metrics %.4f sec" % (
                elapsed_time))

        except Exception, e:
            self.logger.error("Error computing quality metrics: %s" % (
                str(e)))
            
        
    def update_data(self, image):
        """Called by the AgHandler object to update our data with a new
        AG image.
        """
        start_time = time.time()

        # continue processing if at least delta seconds
        # has elapsed since last packet
        delta = self.params.delta
        if (start_time - self.last_time) < delta:
            self.logger.debug("dropping image received under delta %-.4f" % (
                delta))
            return

        self.last_time = start_time

        # Fetch latest status
        fetchDict = self.proxySt.fetch(self.statusDict)
        self.logger.debug("Status fetch time %.4f sec" % (
            time.time() - start_time))
        self.logger.debug("status returned was: %s" % (str(fetchDict)))
        # attach status to this image's metadata
        image.set(status=fetchDict, deriver=self.fitshelper)

        # TODO: computation should be automatically enabled
        # when the value of TSCV.AGCCalc & 0x6 != 0
        # set this in VGW where we are monitoring status
        # May need to clear the display and redraw the region
        # if it changes
        if self.params.compute_quality:
            self.compute_quality_metrics(image)
                
        # Display the image
        with self.lock:
            self.agcount += 1
            count = self.agcount
            #self.image.set_keywords(OBJECT=str(count))

            self.logger.debug("new image metadata: %s" % str(image.metadata))
            # Force reconstruction of the FITS header keywords
            #self.image.set(header={})
            #self.image.set_data(data, metadata=image.metadata)
            #image.copy_region(self.image)
            self.image = image

            if self.save_count > 0:
                self.save_count -= 1
                self.imagequeue.put(image)

            # Update any displays
            self.update_displays()

            # Tell VGW about this image
            self.vgwcam.data_cb(self.agbnch.name, self.agcount, image)

            end_time = time.time()
            elapsed = end_time - start_time

            # record peak, avg
            self.time_count += 1
            self.peak_time = max(self.peak_time, elapsed)
            self.total_time += elapsed
            avg_time = self.total_time / self.time_count

            if end_time - self.time_last_report > 1.0:
                dispobj = self.agbnch.agdisp
                self.time_last_report = end_time
                self.logger.info("performance avg=%6.3f max=%6.3f" % (
                    avg_time, self.peak_time))
                if dispobj:
                    dispobj.update_rates(avg_time, self.peak_time,
                                         self.params.delta)
                    ## dispobj.update_quality(quality)
                

    def save_n(self, num):
        with self.lock:
            self.save_count += num
            
    def reset_count(self):
        with self.lock:
            self.agcount = 0
            
    def reset_n(self):
        with self.lock:
            self.save_count = 0
            
    def reset_perf(self):
        with self.lock:
            self.time_count = 0
            self.time_last_report = 0.0
            self.peak_time = 0.0
            self.total_time = 0.0

    def update_image_status(self, image):
        # Fetch latest status
        fetchDict = self.proxySt.fetch(self.statusDict)
        self.logger.debug("status returned was: %s" % (str(fetchDict)))

        statusDict = image.get('status')

        # replace certain fields with updated status
        for alias in ('FITS.VGW.PROP-ID', 'FITS.VGW.OBSERVER', ):
            statusDict[alias] = fetchDict[alias]

        statusDict = image.get('status')
        self.logger.debug("values are now: %s" % (str(statusDict)))
        header = image.get_header()
        self.logger.debug("header is now: %s" % (str(header)))

    def transfer_data(self, agdata):
        """Copy our image to another AgDataHandler (usually QDAS)."""
        with self.lock:
            data = self.image.get_data()
            metadata = self.image.get_metadata()

        #image = AstroImage(data, metadata=metadata)
        image = AgImage(data, metadata=metadata,
                        wcsclass=wcs.BareBonesWCS)
        
        with agdata.lock:
            agdata.update_data(image)
        
    def load_qdas(self, agdata):
        with self.lock:
            aghdr = self.image.get('agheader')

        self.transfer_data(agdata)
        return aghdr
        
    def get_image(self):
        with self.lock:
            if self.agcount <= 0:
                raise AgError("No %s image in buffer!" % self.agbnch.name)

            data = self.image.get_data()
            other = AgImage(data,
                            wcsclass=wcs.BareBonesWCS)
            self.image.transfer(other)
        return other

    def update_displays(self):
        try:
            dispobj = self.agbnch.agdisp
            if dispobj == None:
                return

            image = self.get_image()
            dispobj.update_image(image)
            
        except Exception, e:
            self.logger.warn("Can't update image for %s: %s" % (
                self.agbnch.name, str(e)))

    ## def clear_rect(self):
    ##     try:
    ##         dispobj = self.agbnch.agdisp
    ##         if dispobj:
    ##             dispobj.clear_rect()
            
    ##     except Exception, e:
    ##         self.logger.warn("Can't update image for %s: %s" % (
    ##             self.agbnch.name, str(e)))
        
    ## def draw_rect(self, x1, y1, x2, y2):
    ##     try:
    ##         dispobj = self.agbnch.agdisp
    ##         if dispobj:
    ##             dispobj.draw_rect(x1, y1, x2, y2)
            
    ##     except Exception, e:
    ##         self.logger.warn("Can't update image for %s: %s" % (
    ##             self.agbnch.name, str(e)))


    ## def create_file(self, fitspath, width, height):
    ##     # TODO: do we need to store VGW files as float?
    ##     self.create_blank(width, height)
    ##     self.fits_path = fitspath
    ##     self.write_file(self.fits_path)

    def open_file(self, fitspath):
        self.image.update_file(fitspath)

    ## def update_header(self, agheader, width, height):
    ##     # Update the image header
    ##     #self.fits_obj[0].update_header()
    ##     self.agcount += 1
    ##     self.fits_hdr['NAXIS']  = 2
    ##     self.fits_hdr['NAXIS1'] = width
    ##     self.fits_hdr['NAXIS2'] = height
    ##     self.fits_hdr.update('PRD_MIN1', 0)
    ##     self.fits_hdr.update('PRD_MIN2', 0)
    ##     self.fits_hdr.update('PRD_RNG1', width)
    ##     self.fits_hdr.update('PRD_RNG2', height)
    ##     self.fits_hdr.update('OBJECT', str(self.agcount))
        
    def write_file(self, fitspath):
        try:
            os.remove(fitspath)
        except:
            pass
        self.fits_obj.writeto(fitspath, output_verify='silentfix',
                              clobber=True)

    def set_delta(self, value):
        self.params.delta = value
        
class GuiderControl(object):

    def __init__(self, logger, threadPool, vgwcam):
        self.logger = logger
        self.threadPool = threadPool
        self.vgwcam = vgwcam

        self.param = Bunch.threadSafeBunch()

        self.delta1 = 0.1
        self.delta2 = 1.0
        
        # For task inheritance:
        self.tag = 'GuiderControl'
        self.shares = ['logger', 'threadPool', 'param', 'shares']

        # Holds the AG data processor
        self.agrcvr = {}

        # helper object to make our FITS headers from definitions
        # in the guiderfitsheader.deriveList
        self.fitshelper = gfh.GuiderFitsHeaderMaker(self.logger)
                                                     
        # VGW pulls status in sets.  These are the known sets.
        self.statusset = Bunch.Bunch()
        # OCS aliases necessary to build any AG header
        self.statusset.OBJECT = self.fitshelper.get_statusAliases()

        # Status aliases needed for finding out about centroid calculation
        self.statusset.DETECT = set([
            'TSCV.AGCCalc', 'TSCV.AGCCalcRegX11', 'TSCV.AGCCalcRegY11',
            'TSCV.AGCCalcRegX21', 'TSCV.AGCCalcRegY21', 'TSCV.AGCCalcRegX12',
            'TSCV.AGCCalcRegY12', 'TSCV.AGCCalcRegX22', 'TSCV.AGCCalcRegY22',
            'TSCV.SVCCalc', 'TSCV.SVCCalcRegX11', 'TSCV.SVCCalcRegY11',
            'TSCV.SVCCalcRegX21', 'TSCV.SVCCalcRegY21', 'TSCV.SVCCalcRegX12',
            'TSCV.SVCCalcRegY12', 'TSCV.SVCCalcRegX22', 'TSCV.SVCCalcRegY22',
            'TSCV.AGImgRegX1', 'TSCV.AGImgRegY1', 'TSCV.AGImgRegX2',
            'TSCV.AGImgRegY2',
            'TSCV.SVImgRegX1', 'TSCV.SVImgRegY1', 'TSCV.SVImgRegX2',
            'TSCV.SVImgRegY2',
            'TSCV.AGPIRImgRegX1', 'TSCV.AGPIRImgRegY1', 'TSCV.AGPIRImgRegX2',
            'TSCV.AGPIRImgRegY2'
            ])

        # The set of all status values we are interested in
        self.statusset.ALL = set([])
        for key in self.statusset.keys():
            self.statusset.ALL = self.statusset.ALL.union(self.statusset[key])

        # Initialize remoteObjects subsystem
        ro.init()
        
    def start_interface(self, agtype):
        self.logger.info("starting interface for %s" % (agtype))
        if not (agtype in Ag.ag_types):
            raise VGWError("Bad ag type: '%s': must be one of {%s}" % (
                agtype, ','.join(Ag.ag_types)))

        aginfo = Ag.ag_info[agtype]
        index  = Ag.ag_types.index(agtype)

        # Figure out how big the maximum buffer needs to be for the
        # guide images at this foci
        width = 0
        height = 0
        for key, d in aginfo['foci'].items():
            width = max(width, d['ccdx'])
            height = max(height, d['ccdy'])

        imagequeue = Queue.Queue()
        agbnch = Bunch.threadSafeBunch(aginfo=aginfo, name=agtype, agdisp=None,
                                       index=index, maxwd=width, maxht=height,
                                       imagequeue=imagequeue)
                           
        self.logger.debug("creating data handler")
        agdata = AgDataHandler(agbnch, self.logger, delta=self.delta2,
                               fitshelper=self.fitshelper,
                               statusset=self.statusset,
                               vgwcam=self.vgwcam, imagequeue=imagequeue)

        # Create a handler to receive the RPC packets
        self.logger.debug("creating rpc handler")
        ev_quit = threading.Event()
        server = AgRpcHandler(agdata, self.logger, ev_quit=ev_quit,
                              agtype=agtype, delta=self.delta1)
        self.agrcvr[agtype] = Bunch.Bunch(agdata=agdata, server=server,
                                          ev_quit=ev_quit, agbnch=agbnch)

        self.logger.info("Starting AG image interface for '%s'" % (
                agtype))
        server.start()

        task = Task.FuncTask(server.mainloop, [], {},
                             logger=self.logger)
        task.init_and_start(self)
        
    def start_qdas(self):
        self.logger.info("starting interface for QDAS")
        index  = len(Ag.ag_types)

        # Figure out how big the maximum buffer needs to be for all
        # guide images
        width  = 0
        height = 0
        for aginfo in Ag.ag_info.values():
            for key, d in aginfo['foci'].items():
                width = max(width, d['ccdx'])
                height = max(height, d['ccdy'])

        imagequeue = Queue.Queue()
        agbnch = Bunch.threadSafeBunch(aginfo=None, name='QDAS', agdisp=None,
                                       index=index, maxwd=width, maxht=height,
                                       imagequeue=imagequeue)
                           
        self.logger.debug("creating data handler")
        agdata = AgDataHandler(agbnch, self.logger, delta=self.delta2,
                               fitshelper=self.fitshelper,
                               statusset=self.statusset,
                               vgwcam=self.vgwcam, imagequeue=imagequeue)

        ev_quit = threading.Event()
        self.agrcvr['QDAS'] = Bunch.Bunch(agdata=agdata, server=None,
                                          ev_quit=ev_quit, agbnch=agbnch)

        
    def stop_interface(self, agtype):
        self.logger.info("stopping interface for %s" % (agtype))
        self.agrcvr[agtype].ev_quit.set()

    def stop_qdas(self):
        self.logger.info("stopping interface for QDAS")
    
    def start(self):
        for agtype in Ag.ag_types:
            self.start_interface(agtype)
        self.start_qdas()

    def stop(self):
        for agtype in Ag.ag_types:
            self.stop_interface(agtype)
        self.stop_qdas()

    def getnames(self):
        l = self.agrcvr.keys()
        l.sort()
        return l

    def getinfo(self, agtype):
        return self.agrcvr[agtype].agbnch

    def set_delta1(self, agtype, delta):
        return self.agrcvr[agtype].server.set_delta(delta)
        
    def set_delta2(self, agtype, delta):
        return self.agrcvr[agtype].agdata.set_delta(delta)

    def reset_perf(self, agtype):
        self.agrcvr[agtype].agdata.reset_perf()
        
    def transfer_data(self, agtype_src, agtype_dst):
        dst = self.agrcvr[agtype_dst].agdata
        return self.agrcvr[agtype_src].agdata.transfer_data(dst)
        
    def load_qdas(self, agtype):
        qdas = self.agrcvr['QDAS'].agdata
        return self.agrcvr[agtype].agdata.load_qdas(qdas)
        
    def raise_qdas(self):
        disp = self.agrcvr['QDAS'].agbnch.agdisp
        if disp:
            disp.raise_win()
        
    def get_image(self, agtype, block=True, timeout=None):
        agbnch = self.agrcvr[agtype].agbnch
        return agbnch.imagequeue.get(block=block, timeout=timeout) 
        
    def get_saved_image(self, agtype):
        agdata = self.agrcvr[agtype].agdata

        image = agdata.get_image() 
        agdata.update_image_status(image)
        return image
        
    def save_image_n(self, agtype, num):
        agdata = self.agrcvr[agtype].agdata
        return agdata.save_n(num) 
        
    def reset_image_n(self, agtype):
        agdata = self.agrcvr[agtype].agdata
        return agdata.reset_n() 

#END

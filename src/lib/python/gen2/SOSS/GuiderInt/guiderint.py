#! /usr/bin/env python
#
# guiderint.py -- main program to receive and process AG guide images
#
#[ Takeshi Inagaki (tinagaki@naoj.org) --
#]
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Dec 18 13:00:05 HST 2008
#]
#

import sys, os, time
import pyfits

import threading
import Queue

import remoteObjects as ro
import logging, ssdlog

import Ag
import guidersave
import guiderfits
import guiderfitsheader
   

DELTA_TIME = 1.0   # frame interval 1 sec

IMAGE_X='deltaX'
IMAGE_Y='deltaY'

version='0.2'
serviceName = 'guiderint'


class VgwServer (Ag.AgServer):

    def __init__(self, logger, display=None, ev_quit=None, delta=DELTA_TIME): 
        self.logger = logger
        self.display = display
        self.ev_quit = ev_quit
        self.delta = delta

        # State variables that exist from previous calls to process()
        self.previous = None            # receiving data interval 
      
        # Initialize my AG handler
        super(VgwServer, self).__init__(self.logger, ev_quit=self.ev_quit,
                                        delta=self.delta)
         
       
    def process(self, agheader, datatime, data_na):
        """Process AG data packet.
        _agheader_ is a string corresponding to the AG header string.
        _datatime_ is the data time (as float) of the data.
        _data_na_ is a numpy of the pixel data.
        """
        self.logger.debug("time: %8.4f  header: %s" % (datatime, agheader))
       
        # Get data size reported by ag header
        (height, width) = data_na.shape

        # print out intervals of receiving image 
        self.logger.debug("data intervals (%s - %s)" % (
            datatime, self.previous))

        # put an image into queue if there is more than one second intervals
        # between current and previous coming image                
        if (self.previous == None) or \
               ((datatime - self.previous) >= self.delta):

            # set current time to previous             
            self.previous = datatime

            ###########################
            ## server-client version ## 
            ###########################

            if self.display != None:

                self.logger.debug("encoding data for remote display")

                # Encode buffer for XMLRPC transport
                encoded_image = ro.binary_encode(data_na.tostring())

                self.logger.debug("calling guider_display")

                # Call object to display buffer
                try:
                    res = self.display.guider_display(encoded_image,
                                                      width, height)
                    if res != ro.OK:
                        self.logger.error("guider_display call failed: %d" % (
                            res))
                except Exception, e:
                        self.logger.error("guider_display call failed: %s" % (
                            str(e)))

        # time intervals are less than one second    
        else:
            self.logger.debug("data interval less than 1 sec")

        # acquire thread lock to save an image                                
        guidersave.FITS_SAVE_LOCK.acquire()
        try:                 
            dirpath, frameid = guidersave.SAVE_FITS.get_nowait()
            self.logger.debug("get dir %s and frameid %s from SAVE_FITS Q" % (
                dirpath, frameid))

            try:
                # TODO: change other parts to use float instead of
                # separate tv_sec and tv_usec
                (sec_s, usec_s) = str(datatime).split('.')
                sec = int(sec_s)
                usec = int(usec_s)
                
                # put fullpath and an image into Fits Image queue
                # TODO: are VGW files supposed to be 32-bit float?
                tup = ( dirpath, frameid,
                        data_na.astype('Float32'),
                        agheader, sec, usec )

                self.logger.debug("put into create_fits Q  path:%s frameid:%s " % (
                    dirpath, frameid))
                guiderfits.CREATE_FITS.put_nowait(tup)

            except Exception, e:
                ### TODO: ###
                ###  report failure ###
                self.logger.error("failed to create FITS file: %s " % str(e))

        except Queue.Empty:
            # set event so that next frame set will be put into
            # Fits Image queue
            guidersave.FITS_SAVE_EVENT.set()

        # release fits save thread lock 
        guidersave.FITS_SAVE_LOCK.release()
        

def main(options, args):
    """This is the main program.
    """
    
    # Create top level logger.
    logger = ssdlog.make_logger(options.svcname, options)

    # Flags that indicate which servers are started
    vgwserver_started = False
    savefits_started  = False
    createfits_started = False
    rosvc_started = False

    try:
        guidisplay = None
        try:
            # Remote objects initializion
            ro.init()

            if options.display:
                guidisplay = ro.remoteObjectProxy(options.display)
                
        except Exception, e:
            logger.error("failed to initialize ro subsystem: %s" % str(e))
            sys.exit(1)

        #-----------------------------------------------------

        logger.info("starting ag rpc server")
        try:
            vgwserver = VgwServer(logger, guidisplay, delta=options.delta)
            vgwserver.start()

        except Exception, e:
            logger.error("failed to start vgw server: %s" % str(e))
            sys.exit(1)

        vgwserver_started = True

        #-----------------------------------------------------
        
        logger.info("starting save frame")
        try:
            savefits = guidersave.GuiderSaveFrame(logger,
                                                  options.svcname,
                                                  options.monitor,
                                                  options.debug,
                                                  usethread=True)
            savefits.save_frame_start()

        except Exception, e:
            logger.error("failed to start save frame: %s" % str(e))
            sys.exit(1)

        savefits_started = True

        #-----------------------------------------------------
        
        logger.info("starting create fits")
        try:
            createfits = guiderfits.GuiderCreateFits(logger,
                                                     options.monitor,
                                                     options.debug,
                                                     options.fitsdummy,
                                                     usethread=True)
            createfits.create_fits_start()

        except Exception, e:
            logger.error("failed to start create fits: %s" % str(e))
            sys.exit(1)

        createfits_started = True

        #-----------------------------------------------------
        # start remote object command service
        logger.info("starting remote objects interface")
        try:
            svc = guidersave.remoteGuiderInt(logger,
                                             options.svcname,
                                             options.monitor, options.debug,
                                             options.port, usethread=True)

            svc.ro_start()

        #except Exception, e:
        except KeyboardInterrupt, e:
            logger.error("failed to start remote objects service: %s" % str(e))
            sys.exit(1)

        rosvc_started = True

        #-----------------------------------------------------
        
        logger.info("Press ^C to terminate server...")
        try:
            vgwserver.mainloop()

        except KeyboardInterrupt:
            logger.error("Received keyboard interrupt!")

    finally:
        # stop all threads
        if rosvc_started:
            logger.info("stopping remote objects service")
            svc.ro_stop()

        if savefits_started:
            logger.info("stopping save fits")
            savefits.save_frame_stop()

        if createfits_started:
            logger.info("stopping create fits")
            createfits.create_fits_stop() 

        if vgwserver_started:
            logger.info("stopping vgwserver")
            vgwserver.stop()

    logger.info("Exiting program")
    sys.exit(1)
    

if __name__ == "__main__":
 
    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                     help="Enter the pdb debugger on main()")
    optprs.add_option("--delta", dest="delta", metavar="SEC",
                      type="float", default=1.0,
                      help="Set delta packet acceptance interval to SEC")
    optprs.add_option("--display", dest="display", metavar="NAME",
                     help="Service NAME of GUI display program")
    optprs.add_option("--fitsdummy", dest="fitsdummy", default=False, action="store_true",
                     help="Use dummy fits values")                     
    optprs.add_option("-m", "--monitor", dest="monitor", default=False,
                      metavar="NAME",
                      help="Reflect internal status to monitor service NAME")
    optprs.add_option("--port", dest="port", type="int",
                      default=None,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                     default=False,
                     help="Run the profiler on main()")
    optprs.add_option("--svcname", dest="svcname", metavar="NAME",
                      default=serviceName,
                      help="Register using NAME as service name")
    ssdlog.addlogopts(optprs)
                      
    (options, args) = optprs.parse_args(sys.argv[1:])

    if len(args) != 0:
        optprs.error("incorrect number of arguments")

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

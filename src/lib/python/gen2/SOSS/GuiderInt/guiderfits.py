#
# guiderfits.py -- module for saving AG guide images
#
#[ Takeshi Inagaki (tinagaki@naoj.org) --
#]
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Tue Apr 12 15:29:45 HST 2011
#]
#

import sys, os, time
import re, math
import pyfits
import guiderfitsheader
import guiderfitstestvalue
import Queue
import threading
import remoteObjects as ro
import remoteObjects.Monitor as Monitor

#import statusClient as sc

# image for fits queue
CREATE_FITS = Queue.Queue(300)

KEYWORD='key'
COMMENT='comment'

# fits keyword
NAXIS1='NAXIS1'
NAXIS2='NAXIS2'
EXTEND='EXTEND'

# comments
NAXIS1_COMMENT="# of pixels/row"
NAXIS2_COMMENT="# of rows (also # of scan lines)"
EXTEND_COMMENT="Presence of FITS Extention"

FITS=".fits"   # fits extension

class GuiderCreateFits(object):
    
    def __init__(self, logger, monitor, debug, dummyval, usethread, ev_quit=None):
              
        self.logger = logger
        self.debug=debug               # do dubug or not   
        self.monitor=monitor           # do monitoring 
        self.dummyval=dummyval         # use dummy fits values 
        self.usethread = usethread     # use thread
        
        self.timeout=0.2               # Q timeout
       
        self.cmd_end="END"
       
        self.aliasVal=guiderfitsheader.getAlias()                            # status alias values
        self.keyVal=guiderfitsheader.getKeyVal()
        
        # fits header template
        self.guiderFitsHeader=guiderfitsheader.guider_fits_header

        # set thread event
        if not ev_quit:  self.ev_quit = threading.Event()
        else:            self.ev_quit = ev_quit
   
        # monitor instance
        if self.monitor:
            self.db = Monitor.Minimon('GuiderInt.mon', self.logger)
            self.db.subscribe(self.monitor, ['GuiderInt'], None)
     
        if not self.dummyval:
            self.svc = ro.remoteObjectProxy('status')
   
    # start create fits thread
    def create_fits_start(self):
        '''Start/enable guider save frame.'''
        
        if self.usethread:
            self.create_fits_thread=threading.Thread(target=self.create_fits)
            #qfits_thread.setDaemon(1)
            self.create_fits_thread.start()

        else:
            self.create_fits()
        
    # stop create fits thread
    def create_fits_stop(self):
        '''Stop/disable remote object server.'''
        #self.block=False
        self.ev_quit.set()

          
    # create a fits and write it
    def create_fits(self):
              
        self.logger.info("starting create fits")
        
        while not self.ev_quit.isSet():
            try:
                # get dir-path, frame-id, and image 
                # self.dirpath is 'END' and self.frameid is tag, if the end of each command 
                dirpath, frameid, image, header, sec, usec = CREATE_FITS.get(block=True, timeout=self.timeout)
                                           
                # check the end of a command
                if dirpath==self.cmd_end:
                    if self.monitor:

                        # if command is end, frameid is the same as tag

                        self.db.setvals(frameid, done=True, result=0, msg="save vlan frame completed", time_done=time.time())
                    continue

                
                # set default keyword value              
                keyVal=self.keyVal              
                              
                if not self.dummyval:
                    # get status alias values
                    aliasVal=self.aliasVal
                    aliasVal=self.svc.fetch(aliasVal) 
                    # update keyword value
                    keyVal=self.setGuiderFitsKeyword(frameid, header, sec, usec, keyVal,  aliasVal)
                                                                           
                self.logger.debug("get create_fits Q dirpath:%s frameid:%s" % (dirpath, frameid))
           
                try:        
                    hdu=pyfits.PrimaryHDU(image)
                    cards = hdu.header.ascardlist()
                    
                    # add missing comments 
                    cards[NAXIS1].comment=NAXIS1_COMMENT
                    cards[NAXIS2].comment=NAXIS2_COMMENT
                    cards[EXTEND].comment=EXTEND_COMMENT        
                  
                    # update keyword values 
                    for key in self.guiderFitsHeader:
                       
                        self.logger.debug("keyword=%s value=%s" % (
                            str(key[KEYWORD]), str(keyVal[key[KEYWORD]])))
                        try:
                            hdu.header.update(key[KEYWORD], keyVal[key[KEYWORD]], key[COMMENT])
                        except Exception, e:
                            # need to report
                            self.logger.error("error updating keyword '%s': %s" % (
                                key[KEYWORD], str(e)))
                                          
                    try:

                        hdu.writeto(os.path.join(  os.path.abspath(dirpath), frameid ) + FITS  )
                                                                     

                        if self.monitor:
                            tag = "mon.frame.%s" % frameid
                            self.db.setvals(tag, done=True, status=0, msg="fits created", time_done=time.time())
                        
                        # print out a fullpath where a fits is written  
                        self.logger.debug("fits created frameid '%s'"  % (
                            frameid))
                                              
                    except IOError, e:
                        if self.monitor:
                            tag = "mon.frame.%s" % frameid
                            self.db.setvals(tag, done=True, status=1, msg="fits hdu.writeto() error", time_done=time.time())
                        
                        self.logger.error("error creating fits file '%s': %s" % (
                            frameid, str(e)))
                                                      
                except Exception, e:
                    if self.monitor:
                        tag = "mon.frame.%s" % frameid
                        self.db.setvals(tag, done=True, status=1, msg="fits PrimaryHDU() error", time_done=time.time())    
                    self.logger.error("PrimaryHDU(image) failed: %s" % str(e))

    
            except Queue.Empty:
                #self.logger.debug("create_fits Q empty")
                pass

        self.logger.info('stopping create fits')


    # set up keyword values
    def setGuiderFitsKeyword(self, frameid, header, sec, usec, keyVal,  aliasVal):
        
        # guider (AG/SV/SH)
        guider = guiderfitsheader.getHeaderValue(header, guiderfitsheader.GUIDER)
                
        # foci (CASS/NSIR/NSOP/PFVS/PFIR)
        foci = guiderfitsheader.getHeaderValue(header, guiderfitsheader.FOCI)
        
        # frame id and exp-id
        try:
            keyVal[guiderfitsheader.FRAMEID]=keyVal[guiderfitsheader.EXP_ID]=frameid
        except:
            pass
        
        # set up keyword values    
        for key in guiderfitsheader.KEYWORDS:
            
            para=len(key)
            
            # get each keyword value 
            value=key[para-1](header, sec, usec, guider, foci, keyVal, aliasVal)
              
            for i in range(para-1):
               
                if value[i] is not None:
                    try:
                        keyVal[key[i]]=value[i]
                    except:
                        pass 
                else:
                    pass 
               
        return keyVal       

# END

#
# guidersave.py -- module for saving AG guide images
#
#[ Takeshi Inagaki (tinagaki@naoj.org) --
#]
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Jul  8 11:14:44 HST 2010
#]
#
import os
import timeit
import time
import threading, Queue
import remoteObjects as ro
import remoteObjects.Monitor as Monitor


# fits save lock object 
FITS_SAVE_LOCK = threading.RLock()       

# fist saving event object
FITS_SAVE_EVENT=threading.Event()

# fits queue
SAVE_FITS = Queue.Queue(300)

# command queue
VLAN_SAVE_CMD = Queue.Queue(300)
#RCV_VLAN_CMD = Queue.Queue(300)

# queue time out 
TIMEOUT=0.01

# For communication with Monitor
monSvcName = 'GuiderInt.mon'
monChannel = 'GuiderInt'


class remoteGuiderInt(ro.remoteObjectServer):
    def __init__(self, logger, svcname, monitor, debug, port, usethread=False):
       
        # Superclass constructor
        #self.guider=GuiderSaveFrame(debug=False, monitor=monitor, svcname=svcname)
        ro.remoteObjectServer.__init__(self, svcname=svcname, port=port,
                                       logger=logger, usethread=usethread)
                                      
        self.logger = logger
        self.debug=debug
        self.monitor=monitor
       
        if self.monitor:
            self.db = Monitor.Minimon(monSvcName, self.logger)
            self.db.subscribe(self.monitor, (monChannel), (Monitor.TWO_WAY))

       
    ######################################
    # Methods provided by remote object interface
    ######################################

    # save v-lan frame command
    # tag, dir, and framelist are passed    
    def save_vlan_frames(self, tag, dirpath, framelist):
        try:
                                                
            if self.monitor:
                self.db.setvals(tag, time_start=time.time(), dirpath=dirpath, framelist=str(framelist) )
                       
            self.logger.debug("cmd called dir:%s f_lists:%s" % (
                dirpath, framelist))
                        
            try:
                VLAN_SAVE_CMD.put_nowait( (tag, dirpath, framelist) )
                self.logger.debug("put cmd into Vlan_Save_Cmd Queue dirpath:%s framelist:%s" % (
                    dirpath, framelist))
                return ro.OK
            
            except Exception, e:
                self.logger.error("vlan save cmd Q put failed: %s" % str(e))
                
        except Exception, e:
            self.logger.error("failed to proceed vlan_save cmd: %s", str(e))
                     
            return ro.ERROR



class GuiderSaveFrame(object):
        
    def __init__(self, logger, svcname, monitor, debug, usethread, ev_quit=None):
        
        self.logger = logger
        self.tag=None
        self.framelist=None        # frame list
        self.name=self.dirpath=None   # name and path for saving
        
        self.usethread = usethread
        self.debug=debug           # debug       
        self.monitor=monitor       # monitor
        
        self.timeout=0.2
        
        self.cmd_end='END'
        
        # set thread event 
        if not ev_quit:
            self.ev_quit = threading.Event()
        else:
            self.ev_quit = ev_quit
        
    # start save frame thread
    def save_frame_start(self):
        '''Start/enable guider save frame.'''
        
        if self.usethread:
            self.save_fits_thread=threading.Thread(target=self.save_frame)
            #qfits_thread.setDaemon(1)
            self.save_fits_thread.start()
            
        else:
            self.save_frame()
        
    # stop save frame thread
    def save_frame_stop(self):
        '''Stop/disable guider save frame.'''
        FITS_SAVE_EVENT.set()
        self.ev_quit.set()
   
    # get save-vlan cmd and make fullpath in order to save fits file
    # after fullpath is made, put fullpath into save_fits queue if queue is clean. 
    # otherwise, wait unitl save_fits queue gets clean
    def save_frame(self):
       
        self.logger.info('starting save frame')

        while not self.ev_quit.isSet():
            
            if not FITS_SAVE_EVENT.isSet():
                FITS_SAVE_EVENT.wait()
                
                try:
                    # get cmd from vlan_save_cmd queue
                    self.tag, self.dirpath, self.framelist=VLAN_SAVE_CMD.get(block=True, timeout=self.timeout)
                                        
                    self.logger.debug("get cmd from Vlan_Save_Cmd Queue dirpath:%s framelist:%s" % (
                        self.dirpath, self.framelist))
                    
                    FITS_SAVE_LOCK.acquire()
                                                          
                    for frameid in self.framelist:
                        try:
                            
                            SAVE_FITS.put_nowait((self.dirpath, frameid))
                            self.logger.debug("put dirpath and frameid into Save_Fits Queue dirpath:%s  frameID:%s" % (
                                self.dirpath, frameid))
  
                        except Exception, e:
                            ### TODO 
                            ### need report ?????
                            self.logger.error("failed to put name/path into save_fits Q: %s" % str(e))
                        
                    # this tells the end of cmd
                    SAVE_FITS.put_nowait((self.cmd_end, self.tag))
                                        
                    FITS_SAVE_LOCK.release()

                except Queue.Empty:
                    self.logger.debug("no cmd received")
                        
            FITS_SAVE_EVENT.clear()
            
        self.logger.info('stopping save frame')

#END


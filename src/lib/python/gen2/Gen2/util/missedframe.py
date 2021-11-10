#!/usr/bin/env python

import os
import sys
import glob
import time
import threading
import datetime
from dateutil.relativedelta import relativedelta

import ssdlog
from SOSS.STARSint import STARSdb
from cfg.INS import INSdata
from notify_me import *

try:
    import Gen2.opal as OPAL
    has_OPAL = True
except ImportError:
    has_OPAL = False


class Frame(object):
    
    def __init__(self, summit_dir, base_dir, error=None, logger=None):
        
        self.error=error
        self.logger=logger
    
        self.stars=None  # frames in STARS 
        
        self.summit={}  # all frames @ summit 
        self.base={}    # all frames @ base
        
        self.summit_a={} # A-frames @ summit
        self.base_a={}   # A-frames @ base
        self.summit_q={} # Q-frames @ summit
        self.base_q={}   # Q-frames @ base
        
        self.intersect=None  # union of summit and base frames
        
        self.summit_dir=summit_dir  # frame dir @summit
        self.base_dir=base_dir      # frame dir @base
        
        self.obcp=INSdata()   
        self.starsdb = STARSdb(logger)

                         
    def get_base(self):
        self.logger.debug('getting base frames...')
        
        sync_base={}
        
        try:
            frames=set(self.summit.keys()).difference(self.base.keys())

            for f in frames:
                sync_base[f]=self.summit[f]
                
            return sync_base
        except Exception as e:
            self.logger.error('error: getting base frames... %s' %e)
            if self.error:
                enditer = self.error.get_end_iter()
                self.error.insert(enditer, 'error: getting base frames... %s\n' %e)      

    def get_summit(self):
        self.logger.debug('getting summit frames...')
        
        sync_summit={}
        
        try:
            frames=set(self.base.keys()).difference(self.summit.keys())
            for f in frames:
                sync_summit[f]=self.base[f]
            return sync_summit    
        except Exception as e:
            self.logger.error('error: getting summit frames... %s' %e)
            if self.error:
                enditer = self.error.get_end_iter()
                self.error.insert(enditer, 'error: getting summit frames... %s\n' %e)      


    def get_stars(self):
        self.logger.debug('getting stars frames...')

        frames=list(set(self.intersect).difference(self.stars))
  
        try:
            stars={}
            for frame in frames:
                stars[frame]=self.base[frame]
            return stars
        except Exception as e:
            self.logger.error('error: getting stars frames... %s' %e)
            if self.error: 
                enditer = self.error.get_end_iter()
                self.error.insert(enditer, 'error: getting stars frames... %s\n' %e)      


    def get_delete(self):
        self.logger.debug('getting delete frames...')  
        
        try:     
            frames=list(set(self.intersect).intersection(self.stars))
             
            delete={}
            
            for frame in frames:
                delete[frame]=self.base[frame]
            return delete

        except Exception as e:
            self.logger.error('error: getting summit frames... %s' %e)
            if self.error:
                enditer = self.error.get_end_iter()
                self.error.insert(enditer, 'error: getting delete frames... %s\n' %e)      


    def __search_stars(self, frameid):
        self.logger.debug('querying stars...')  

        # note: STARS somehow does not let me query both A/Q frames in parallel.
        #       need to query one after other  

        stars_q=self.__search_Q_frames(frameid) 
        stars_a=self.__search_A_frames(frameid)
        self.stars=stars_a + stars_q
        

    def __search_Q_frames(self,frameid):

        intersect_q=list(set(self.base_q.keys()).intersection(self.summit_q.keys()))
         
        stars_q=[] 
        if not len(intersect_q):
            return stars_q
        
        intersect_q.sort()
        sframe,e=os.path.splitext(intersect_q[0])
        eframe,e=os.path.splitext(intersect_q[-1])
        
        self.logger.debug('ins=%s Q between %s and %s' %(frameid, sframe,eframe))
        
        stars=self.starsdb.are_frames_in_stars(frameid, sframe, eframe)
        stars_q.extend(map(lambda x: '%s.fits' %x, stars))
        self.logger.debug('Q query done num=%d' %len(stars_q))
        return stars_q
       

    def __search_A_frames(self,frameid):
        
        intersect_a=list(set(self.base_a.keys()).intersection(self.summit_a.keys()))
        stars_a=[]
        if not len(intersect_a):
            return stars_a
        
        intersect_a.sort()
        sframe,e=os.path.splitext(intersect_a[0])
        eframe,e=os.path.splitext(intersect_a[-1])
        
        self.logger.debug('ins=%s A between %s and %s' %(frameid, sframe,eframe))

        stars=self.starsdb.are_frames_in_stars(frameid, sframe, eframe)
        stars_a.extend(map(lambda x: '%s.fits' %x, stars))
        self.logger.debug('A query done num=%d' %len(stars_a))
        return stars_a
        

    def collect_frames(self, ins):
        
        today=datetime.datetime.today()
        frameid=self.obcp.getCodeByName(ins)
        
        try:
            self.base_a,self.base_q=self.__collect_frames(self.base_dir, ins, frameid, today)
            self.summit_a, self.summit_q=self.__collect_frames(self.summit_dir, ins, frameid, today)
            self.summit.clear(); self.base.clear()
            self.summit.update(self.summit_a); self.summit.update(self.summit_q)
            self.base.update(self.base_a); self.base.update(self.base_q) 
            self.intersect=list(set(self.base.keys()).intersection(self.summit.keys()))
            self.logger.debug('base_a=%d  base_q=%d  base=%d'%(len(self.base_a), len(self.base_q), len(self.base))) 
            self.logger.debug('summit_a=%d  summit_q=%d  summit=%d'%(len(self.summit_a), len(self.summit_q), len(self.summit))) 
            self.logger.debug('intersect=%d' %(len(self.intersect)))
#            
            self.__search_stars(frameid)
        except Exception as e:
            self.logger.error('error: collecting frames.  %s ' %e)
            if self.error:
                enditer = self.error.get_end_iter()
                self.error.insert(enditer, 'error: collecting frames..  %s\n' %e)      
        


    def __collect_frames(self, path, ins, frameid, today):
        #print 'collecting base frame....'        
        Afits='%sA*.fits' %frameid   
        Qfits='%sQ*.fits' %frameid   
        
        ins_dir = os.path.join(path, ins)    
        os.chdir(ins_dir)
        Aframes= glob.glob(Afits) 
        Qframes=glob.glob(Qfits)
    
        Aframes=self.__get_frame_info(Aframes, today)
        Qframes=self.__get_frame_info(Qframes, today)
        return (Aframes, Qframes)


    def __get_frame_info(self, frames,  today):     
        
        """ get time stamp, age, size of a file """
  
        stat=os.stat
        fromtimestamp=datetime.datetime.fromtimestamp
        frame_info={} #; append=frame_info.append

        for frame in frames:
            info=stat(frame)
            m_time=fromtimestamp(info.st_mtime)
            age=today-m_time
            frame_info[frame]=(m_time.strftime("%Y-%m-%d %H:%M:%S"), age.days, info.st_size)

        return frame_info


def get_instrument(opal, lastnight, logger):
    # init remote object 

    yda=lastnight.strftime('%Y-%m-%d')
    info=opal.getInfoForNight(lastnight, table='tsr')

    ins_list=[]

    for k in info:
        ins=k['instr'].split('+')

        d='%s' % k['date']
        logger.debug('checking date match <%s> <%s>  ins=%s' %(d,yda, ins))
        if d == yda and (not ins[0] in ins_list):
            logger.debug('adding ins to the list. ins=%s, opal-day=%s obs-day=%s' %(k['instr'], k['date'], yda))
            ins_list.append(ins[0])
    logger.debug('ins_list = %s' %ins_list) 
     
    return ins_list
 
def make_msg(ins, frames):
    
    msg='\n%s to STARS...\n' %ins 

    if len(frames)==0:
        msg+='None\n'
    for k in sorted(frames.keys()):
        msg+='%s %s %d-days-old\n' %(k,frames[k][0], frames[k][1]) 
    
    return msg

def read_err_file(err_file, logger):

    msg=''
    logger.debug('file name=%s' %err_file)
    try:
        for line in open('%s' %err_file).xreadlines(): 
            msg+=line
    except Exception as e:
        logger.error('error: reading %s' %err_file)
        msg='error: reading %s\n' %err_file

    if not msg:
        msg='No Error\n'
    return msg

def main(options,args):
 
    # TO DO 
    # import tools.cleanfits.frame instead of copying frame class here

    logname = 'frame_to_stars'
    logger = ssdlog.make_logger(logname, options)

    base = options.base
    summit=options.summit

    archive_err=options.archive
    transfer_err=options.transfer

    try:
        error_dir=os.environ['GEN2COMMON']
    except Exception:
        error_dir='/gen2/share'
    finally:
        error_dir=os.path.join(error_dir, 'db')

    archive_err=os.path.join(error_dir, archive_err) 
    transfer_err=os.path.join(error_dir, transfer_err) 

    today=datetime.datetime.today()
    # testing
    #today=datetime.date(2011,6, 16)
    
    oneday=datetime.timedelta(1)
    lastnight=today-oneday
    logger.debug('today = %s lastnigth=%s' %(today,lastnight))

 
    if options.ins:
        ins_list=options.ins.split(',')
    else:
        ins_list=['VGW']  

        if has_OPAL:
            try:
                opal = OPAL.OPALinfo()
            except Exception as e:
                logger.warn("warn: couldn't create OPAL object: %s" % (str(e)))
                logger.warn("warn: OPAL queries will not be possible, only VGW frame will be checked!")
            else:
                ins=get_instrument(opal, lastnight, logger)  
                ins_list.extend(ins)    
        else:
            logger.warn("warn: couldn't import OPAL module")
            logger.warn("warn: OPAL queries will not be possible")
    
    ins_list.sort() 

    msg='%s observation on %s\n' %(','.join(ins_list), lastnight.strftime("%Y-%m-%d"))

    
    archive_err_msg='\nSummary of archiving(STARS)...\n'
    msg+=archive_err_msg
    msg+=read_err_file(err_file=archive_err, logger=logger)

    transfer_err_msg='\nSummary of transfering(OBCP -> Gen2)...\n'
    msg+=transfer_err_msg
    msg+=read_err_file(err_file=transfer_err, logger=logger)
    
    subject='Missed frames to STARS'

    try:
        f=Frame(summit_dir=summit, base_dir=base, logger=logger)
        
        # instrument at night
        for ins in ins_list:
            f.collect_frames(ins) 
            frames=f.get_stars()
            msg+=make_msg(ins, frames)

        #print msg
     
        notify_me(sub=subject, sndr=options.sender, rcpt=options.recipient, msg=msg, logger=logger)

    except KeyboardInterrupt,e:
        print 'interrupting....'
        logger.debug('Keyboard Interrupt...')


if __name__ == "__main__":

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options] [file] ..."
    optprs = OptionParser(usage=usage, version=('%prog'))
    
    optprs.add_option('-a', "--action", dest="action", metavar="ACTION",
                      default=None,
                      help="specify ACTION to operate on fits files")
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")

    optprs.add_option("-r", "--recipient", dest="recipient", metavar="RECIPIENT", default='ocs@naoj.org',
                      help="Specify mail recipient")

    optprs.add_option("-s", "--sender", dest="sender", metavar="SENDER", default='tinagaki@naoj.org',
                      help="Specify mail sender")

    optprs.add_option("--ins", dest="ins", metavar="INS", default=False,
                      help="Specify a obcp instrument name")

    optprs.add_option("--archive", dest="archive", metavar="ARCHIVE", default="archive.errors",
                      help="Specify data archive error file")

    optprs.add_option("--transfer", dest="transfer", metavar="TRANSFER", default="transfer.errors",
                      help="Specify data transfer error file")


 
    optprs.add_option("--base", dest="base", metavar="BASE", 
                      #default='/mnt/raid6data/data',
                      default='/mnt/raid6base_data',
                      help="Specify base dir")

    optprs.add_option("--summit", dest="summit", metavar="SUMMIT", 
                      default='/gen2/data',
                      help="Specify summit dir")

 
    optprs.add_option("--host", dest="host", metavar="HOST", 
                      default="g2b1",
                      help="Specify host name [g2b1|g2b3]")

    optprs.add_option("--dry-run", dest="dry_run", default=False,
                      action="store_true",
                      help="Don't really delete files, just show what we would do")


    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    #if len(args) > 0:
    #    optprs.error("incorrect number of arguments")
       
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


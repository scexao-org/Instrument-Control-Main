#!/usr/bin/env python

import os
import sys
import glob
import time
import datetime
from dateutil.relativedelta import relativedelta

import remoteObjects as ro
from SOSS.STARSint import STARSdb
import ssdlog

from notify_me import *

class TSClog(object):

    def __init__(self, logger):

        starsdb = STARSdb(logger)
        self.isSTARS=starsdb.is_log_stars

        ro.init()
        self.tm=ro.remoteObjectProxy('taskmgr0')
        self.tm.loadModule('LOGTask')
        self.tm.addAllocs(['STARS'])

        self.sendcmd_tpl='EXEC LOG Send_Log logpath="%s" indexdir="%s" name=%s logstarttime="%s" logendtime="%s" '
 
        self.removecmd_tpl='EXEC LOG Remove_Log logpath="%s"'  

        self.logger=logger  

    def ignore_ongoing_log(self, logs, logdir):
        print 'to do'

        t=datetime.date.today()

        tscs_day='%s/TSCS-%d%02d%02d-08.pkt' %(logdir,t.year,t.month, t.day )
        tscl_day='%s/TSCL-%d%02d%02d-08.pkt' %(logdir,t.year,t.month, t.day )
        tscv_day='%s/TSCV-%d%02d%02d-08.pkt' %(logdir,t.year,t.month, t.day )   

        tscs_obs='%s/TSCS-%d%02d%02d-17.pkt' %(logdir,t.year,t.month, t.day )
        tscl_obs='%s/TSCL-%d%02d%02d-17.pkt' %(logdir,t.year,t.month, t.day )
        tscv_obs='%s/TSCV-%d%02d%02d-17.pkt' %(logdir,t.year,t.month, t.day )   

        for tsc in [tscs_day, tscl_day, tscv_day, tscs_obs,tscl_obs,tscv_obs]:
            try:
                self.logger.info('removing %s from tsc-log list...' %tsc)
                logs.remove(tsc)
            except Exception as e:
                self.logger.warn('warn: %s not in list. %s' %(tsc, e))

    def make_timestamp(self, logid):

        year=int(logid[4:8])
        month=int(logid[8:10])
        day=int(logid[10:12])
        obs_mode=logid[-3:]
        d=datetime.date(year,month,day)    

        stime=etime=None
        if obs_mode=='DAY':
            stime='%s 08:00:00' %d.isoformat()
            etime='%s 17:00:00' %d.isoformat()
        elif obs_mode=='OBS':
            stime='%s 17:00:00' %d.isoformat()
            d=d+relativedelta(days=1)
            etime='%s 08:00:00' %d.isoformat() 
        else:
            self.logger.error('error: obs_mode=%s???' %obs_mode)

        return(stime,etime) 



    def get_logid(self, log):

        logid=os.path.splitext(os.path.split(log)[1])[0]
        logid=logid.split('-')
        if len(logid[0])>4:
            logid[0]=logid[0][0:4]    

        if logid[2]=='17' or logid[2]=='obs':
            obs='OBS'
        elif logid[2]=='08':
            obs='DAY'   
        else:
            self.logger.error('error: tsc status, obs mode is not either 08 or 17')
            return False
        # format e.g. TSC[S|V|L]YYYYMMDD[OBS|DAY]
        return '%s%s%s' %(logid[0],logid[1],obs)               


    def send_endlog(self, options):

        endlog='ENDLOG'
        endlog=os.path.join(options.endlogdir, endlog)      

        today=datetime.date.today()
        oneday=relativedelta(days=1)
        yesterday=today-oneday

        endlogid='ENDL%02d%02d%02dDAY' %(yesterday.year, yesterday.month, yesterday.day)
        stime='%s 08:00:00' %yesterday.isoformat() 
        etime='%s 08:00:00' %today.isoformat()
    
        cmd=self.sendcmd_tpl %(endlog, options.cutsdir, endlogid, stime, etime )  

        if options.dry_run:
            self.logger.info("d-run endcmd=%s" %cmd) 
        else:
            res=self.tm.execTask("launcher", cmd, '')
            self.logger.info("res=%d cmd=%s" %(res, cmd))   
            if  res:
                self.logger.warn('warn: sending endlog failed. cmd=%s' %cmd) 


    def send_tsclog(self, tsclogs, options):

        failed=[]
  
        for log in tsclogs:
            logid=self. get_logid(log)
  
            if self.isSTARS(logid) or not logid:
                self.logger.debug('%s is in STARS..' %logid)
                continue
            else:
                self.logger.debug('%s is not in STARS..' %logid)

            stime, etime=self.make_timestamp(logid)
            cmd=self.sendcmd_tpl %(log, options.cutsdir, logid, stime, etime )  


            if options.dry_run:
                self.logger.info("d-run cmd=%s" %cmd)
                # testing
                failed.append('log: %s' %log)
                failed.append('cmd: %s' %cmd )
            else:
                
                res=self.tm.execTask("launcher", cmd, '')
                self.logger.info("res=%d cmd=%s" %(res, cmd)) 
                if res:
                    failed.append('log: %s' %log)
                    failed.append('cmd: %s' %cmd )
        return failed 
 

    def get_log_age(self, today, log):
        """ get file's age  """

        st_mtime=os.path.getmtime(log)
        modified_time=datetime.datetime.fromtimestamp(st_mtime)
        age=today-modified_time

        return age

    def delete_inf(self, infs, today, options):
        print ''

        for inf in infs:
            age=self.get_log_age(today, inf)
            self.logger.info('age=%d log=%s' %(age.days, inf))
            if not options.age < age.days:
                continue

            cmd=self.removecmd_tpl %inf
            if options.dry_run:
                self.logger.info('d-run cmd=%s' %cmd)
            else:
                res=self.tm.execTask("launcher", cmd, '')
                self.logger.info("res=%d cmd=%s" %(res, cmd)) 
                if res:
                    self.logger.warn('warn: deleting failed. check %s.' %(inf))

    def delete_tsclog(self, tsclogs, today, options):

        failed=[]

        for log in tsclogs:
            age=self.get_log_age(today, log)
            self.logger.info('age=%d log=%s' %(age.days, log))

            if not options.age < age.days:
                continue
            logid=self.get_logid(log)
               
            cmd=self.removecmd_tpl %log

            if self.isSTARS(logid) or not logid:
                if options.dry_run:
                    self.logger.info('d-run cmd=%s' %cmd)
                    # this is testing
                    failed.append('log: %s' %log)
                    failed.append('cmd: %s' %cmd )
                else:
                    res=self.tm.execTask("launcher", cmd, '')
                    self.logger.info("res=%d cmd=%s" %(res, cmd)) 
                    if res:
                        failed.append('log: %s' %log)
                        failed.append('cmd: %s' %cmd )
            else:
                self.logger.info('age=%d, %s is not in STARS.' %(age.days, logid) )
        return failed
        
def main(options,args):
    
    logname = 'tsc_statuslog'
    logger = ssdlog.make_logger(logname, options)

    tl=TSClog(logger)

    tsclog='TSC*.pkt'
    tsclog=os.path.join(options.cutsdir, tsclog)

    tsclogs=glob.glob(tsclog)

    tl.ignore_ongoing_log(logs=tsclogs, logdir=options.cutsdir)

    tsclogs.sort()
    logger.info('tsc=%s' %tsclogs)

    subject='TSC Log'
    sender='tinagaki@naoj.org'
    recipient='ocs@naoj.org'

    if options.act=='send':
        logger.debug('begin sending tsc logs to stars...')
        failed_log=tl.send_tsclog(tsclogs, options)  
        tl.send_endlog(options)
       
        if failed_log:
            msg='Error: TSC Logs to STARS... '
            failed_log='\n'.join(failed_log)
            msg='%s\n%s' %(msg, failed_log)

            notify_me(sub=subject, sndr=sender, rcpt=recipient, msg=msg, logger=logger)
            #notify_me(failed_log, msg, logger)

    elif options.act=='delete':
        logger.debug('begin deleting tsc logs...')
        inf='*.inf'
        inf=os.path.join(options.cutsdir, inf)
        infs=glob.glob(inf)

        today=datetime.datetime.today()
        failed_log=tl.delete_tsclog(tsclogs, today,  options)
        tl.delete_inf(infs, today, options)
        if failed_log:
            msg='Error: TSC Logs to delete.. '
            failed_log='\n'.join(failed_log)
            msg='%s\n%s' %(msg, failed_log)

            notify_me(sub=subject, sndr=sender, rcpt=recipient, msg=msg, logger=logger)
        
    else:
        logger.error('wrong options %s' %options.act )
        sys.exit(1)

if __name__=="__main__":
    
    from optparse import OptionParser

    usage = "usage: %prog [options] [file] ..."
    optprs = OptionParser(usage=usage, version=('%prog'))

    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")

    optprs.add_option("--act", dest="act", metavar="ACT",
                      help="specify what do you like to do [send|delete]")
    
    optprs.add_option("--cutsdir", dest="cutsdir", metavar="CUTSDIR",
                      default="/gen2/logs/cuts",
                      help="specify cuts dir")

    optprs.add_option("--endlogdir", dest="endlogdir", metavar="ENDLOGDIR",
                      default="/gen2/logs",
                      help="specify endlog dir")

    optprs.add_option("--age", dest="age", metavar="AGE", type="int",
                      default=30,
                      help="specify the age of a file to delete")
    
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

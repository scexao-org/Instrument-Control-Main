#!/usr/bin/env python

import os
import sys
import glob
import time
import datetime

import remoteObjects as ro
from SOSS.STARSint import STARSdb
import ssdlog
import send_log as sl

# tsc status logs
tsc_status_logs=['TSCS-%s-%s.pkt', 'TSCL-%s-%s.pkt', 'TSCV-%s-%s.pkt']
     

def get_log_age(ct, logpath, logger):
    """ get file's age  """

    st_mtime=os.path.getmtime(logpath)
    t=time.localtime(st_mtime) 

    modified_time=datetime.datetime(t.tm_year,t.tm_mon,t.tm_mday,t.tm_hour,t.tm_min,t.tm_sec)

    current_time=datetime.datetime(ct.tm_year,ct.tm_mon,ct.tm_mday,ct.tm_hour,ct.tm_min,ct.tm_sec)

    delta=current_time-modified_time
   
    #logger.info('time deleta<%s>' %str(delta))
    return '%s' %str(delta)


def get_tsc_status_logs(logdir):
    
    status_logs='%s/*.pkt' %logdir
    return glob.glob(status_logs)

def get_gen2_logs(logdir):
    
    status_logs='%s/*.log' %logdir
    return glob.glob(status_logs)

def cmp_age(age, age_deletion, logger):
    
    # e.g. age = '1378 days, 12:51:07' or '1:29:01'
    age=age.split(',')
    
    if len(age)<2:
        logger.info("younger age<%s hours>" %(age))
        age=0
    else:
        age=age[0].split()
        age=int(age[0])
    
    if age >= age_deletion:
        logger.info("older age<%s days>" %(age))
        return True
    else:
        logger.info("not old enough age<%s days>" %(age))
        return False
    

def get_logid(log, logger):

    logid=os.path.splitext(os.path.split(log)[1])[0]
    logid=logid.split('-')
    if len(logid[0])>4:
        logid[0]=logid[0][0:4]    

    if logid[2]=='17' or logid[2]=='obs':
        obs='OBS'
    elif logid[2]=='08':
        obs='DAY'   
    else:
        logger.error('tsc status, obs mode is not either 08 or 17')
        return False
    # format e.g. TSC[S|V|L]YYYYMMDD[OBS|DAY]
    return '%s%s%s' %(logid[0],logid[1],obs)               


def delete_tsc_status_logs(tm, logdir, isSTARS,  current_time,  options, logger):
    logs=get_tsc_status_logs(logdir)
    delete_old_log(tm, logs, isSTARS,  current_time, options, logger)


def delete_gen2_logs(tm, logdir, isSTARS,  options, logger):
 
    logs= get_gen2_logs(logdir)
    delete_old_log(tm, logs, isSTARS,  options, logger)
            
def delete_old_log(tm, logs, isSTARS,  current_time,  options, logger):
    ''' delete more than 10 days old tsc-status log files '''
    
    cmd_tmp='EXEC LOG Remove_Log logpath="%s"'  
    
    #logs=get_tsc_status_logs(cutsdir)

    #logger.info('logs<%s>' %(logs))
 
    for log in logs:
        cmd=cmd_tmp %log
        
        age=get_log_age(current_time, log, logger)
        logger.info("log's age <%s %s>" %(log, age))
    
        if cmp_age(age, options.age, logger):
         
            logid=get_logid(log,logger)
            logger.debug('logid<%s>' %(logid))
            if not logid:
                continue
                  
            if isSTARS(logid):
                logger.info('log in STARS<%s>' %(logid))
                if options.dry_run:
                    logger.info('dry-run deleting log cmd<%s>' %cmd)
                else:
                    logger.info('deleting log cmd<%s>' %cmd) 
                    tm.execTask("launcher", cmd, '')
            else:
                logger.info('log not in STARS')

                if not os.path.getsize(log):
                    logger.info('log is an empty <%s>' %(log))
                    if options.dry_run:
                        logger.info('dry-run deleting log cmd<%s>' %cmd)
                    else:
                        logger.info('deleting log cmd<%s>' %cmd) 
                        tm.execTask("launcher", cmd, '')
                 
def get_inf_files(infdir):
    
    inf_files='%s/*.inf' %infdir
    return glob.glob(inf_files)


def delete_inf(tm, current_time, options, logger):

    cmd_tmp='EXEC LOG Remove_Log logpath="%s"' 
   
    inf_files=get_inf_files(options.infdir)
    
    #logger.info('getting inf files <%s>' %(inf_files))
    
    for inf in inf_files:

        age=get_log_age(current_time, inf, logger)
        logger.info("log's age <%s %s>" %(inf, age))
    
        if cmp_age(age, options.age, logger):

            cmd = cmd_tmp %(inf)
            if options.dry_run:
                logger.info('dry-run deleting inf file cmd<%s>' %cmd)
            else:
                logger.info('deleting inf file cmd<%s>' %cmd) 
                tm.execTask("launcher", cmd, '')
                logger.info('deleting inf file done')


def main(options,args):
    
    logname = 'deletelog'
    logger = ssdlog.make_logger(logname, options)
   
    starsdb = STARSdb(logger)
    isSTARS=starsdb.is_log_stars

    ro.init()
    tm=ro.remoteObjectProxy('taskmgr0')
    tm.loadModule('LOGTask')
    tm.addAllocs(['STARS'])

    try:
        logdir=os.environ['LOGHOME']
    except KeyError,e:
        logdir='/gen2/logs'     

    cutsdir=os.path.join(logdir, 'cuts')

    current_time=time.localtime()

    ''' delete old tsc-staus logs '''
    logger.info('deleting tsc status logs ...')
    delete_tsc_status_logs(tm, cutsdir, isSTARS, current_time,  options, logger)
    logger.info('deleting tsc status logs done')

    ''' delete gen2 logs '''
    # logger.info('deleting gen2 logs ...')
    # delete_gen2_logs(tm, cutsdir, isSTARS,  options, logger)
    # logger.info('deleting gen2 logs done')

    ''' delete inf files '''
    logger.info('deleting inf files ...')
    delete_inf(tm, current_time,  options, logger)
    logger.info('deleting inf files done')
            
    
if __name__=="__main__":
    
    from optparse import OptionParser

    usage = "usage: %prog [options] [file] ..."
    optprs = OptionParser(usage=usage, version=('%prog'))

    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")

    optprs.add_option("--age", dest="age", metavar="AGE", type="int",
                      default=15,
                      help="specify day(s) to delete log files")
    
    optprs.add_option("--dry-run", dest="dry_run", default=False,
                      action="store_true",
                      help="Don't really delete files, just show what we would do")

    optprs.add_option("--infdir", dest="infdir", metavar="INFDIR", 
                      default="/gen2/logs/cuts",
                      help="Specify inf file stored dir")

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
    
    
    

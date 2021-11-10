#!/usr/bin/env python

import os
import sys
import glob
import time
import datetime
import remoteObjects as ro
import ssdlog

'''
usage:

--dry-run
./send_log.py --dry-run
   

./send_log.py 

'''

# tsc status logs
TSC_STATUS_LOGS=['TSCS-%s-%s.pkt', 'TSCL-%s-%s.pkt', 'TSCV-%s-%s.pkt']
#tsc_ststus_index=['TSCS-%s-%s.pkt', 'TSCL-%s-%s.pkt', 'TSCV-%s-%s.pkt']

# gen2 logs
GEN2_LOGS=['taskmgr0.log', 'TSC.log', 'status.log']
GEN2_CUTLOGS=['TASKMGR0-%s-%s.log', 'TSC-%s-%s.log', 'STATUS-%s-%s.log']

# for testing 
#GEN2_LOGS=['taskmgr0.log']
#GEN2_CUTLOGS=['TASKMGR0-%s-%s.log']

# application logs
#app_logs=['telstat_stdout.log', 'VGW_stdout.log']
#app_cutlogs=['telstat_stdout-%s-%s.log', 'VGW_stdout-%s-%s.log']

# instrumet logs
INS_LOGS=['AO188.log', 'COMICS.log', 'FMOS.log', 'FOCAS.log', 'HDS.log', 'HICIAO.log', 'MOIRCS.log', 'IRCS.log', 'K3D.log','SPCAM.log','WAVEPLAT.log', 'VGW.log']
INS_CUTLOGS=['AO188-%s-%s.log', 'COMICS-%s-%s.log', 'FMOS-%s-%s.log', 'FOCAS-%s-%s.log', 'HDS-%s-%s.log', 'HICIAO-%s-%s.log', 'MOIRCS-%s-%s.log', 'IRCS-%s-%s.log',  'K3D-%s-%s.log', 'SPCAM-%s-%s.log', 'WAVEPLAT-%s-%s.log', 'VGW-%s-%s.log']

# for testing
#INS_LOGS=['SPCAM.log','HDS.log']  
#INS_CUTLOGS=['SPCAM-%s-%s.log','HDS-%s-%s.log']    

# end log
end_log=['ENDLOG']


def get_log_name( logs, day, mode, logger):
    ''' the name of log file is created with time stamp appended'''
     # mode = '08', '17', 'obs'

    log_list=[]
    
    for name in logs:
        logger.info('get log name name=%s mode=%s'  %(name, mode))
        name=name %(day, mode)
        log_list.append(name)
    
    logger.info('list of logs<%s>' %log_list)
    return log_list


def send_endlog(tm, logdir, logs, log_time_yd, index_dir, time_from, time_to, mode, options, logger):
    ''' send the endlog file to STARS '''
    
    cmd_tmp='EXEC LOG Send_Log logpath="%s" indexdir="%s" name=%s logstarttime="%s" logendtime="%s" ' 
    
    for log in logs:
        
        name='%s%s%s' %(log[:4],log_time_yd, mode)  
        logger.info('sending log name<%s>' %name)   

        log=os.path.join(logdir, log)
                       
        cmd=cmd_tmp %(log, index_dir, name, time_from, time_to)
        if options.dry_run:
            logger.info('send-log cmd<%s>' %cmd)
        else:
            logger.info('sending log...<%s>' %log)
            res=tm.execTask("launcher", cmd, '')
            logger.info('sending log res<%s>' %(str(res)))



def send_log(tm, logdir, logs, log_time_yd, index_dir, time_from, time_to, mode, options, logger):
    ''' send a log file to STARS '''
    
    cmd_tmp='EXEC LOG Send_Log logpath="%s" indexdir="%s" name=%s logstarttime="%s" logendtime="%s" '
    
    for log in logs:
        
        num=log.find('-')
        if num > 4:
            num=4 

        name='%s%s%s' %(log[:num],log_time_yd, mode)  
        logger.info('sending log name<%s>' %name)   
       
        log=os.path.join(logdir, log)
        #if not os.path.exists(log):
        if not (os.path.exists(log) and os.path.getsize(log)):
            logger.warn('log is not existed or an empty<%s>' %(log))
            continue    
        
          
        cmd=cmd_tmp %(log, index_dir, name, time_from, time_to)
        if options.dry_run:
            logger.info('send-log cmd<%s>' %cmd)
        else:
            logger.info('sending log...<%s>' %cmd)
            res=tm.execTask("launcher", cmd, '')
            logger.info('sending log res<%s>' %(str(res)))
          
    
def cut_log(tm, logdir, logs, cutdir, cutlogs, time_from, time_to, options, logger):
    ''' cut log file in specified time range'''
    
    # e.g. logs.py --in=/gen2/logs/TSC.log --out=/tmp/tsc_cut.log --from='2010-05-20 17:00:00' --to='2010-05-21 08:00:00' --action=cut
    
    cmd_tmp='EXEC LOG CUT_LOG inlog="%s" outlog="%s" time_from="%s" time_to="%s"'    
    
    for log,cutlog in zip(logs,cutlogs):

        log=os.path.join(logdir,log)
        cutlog=os.path.join(cutdir,cutlog)
        logger.info("cutting logpath<%s>" %cutlog)
        cmd = cmd_tmp %(log, cutlog, time_from, time_to)
        try:
            if options.dry_run:
                logger.info('cut-log cmd<%s>' %cmd)
            else:
                logger.info('cut-log cmd<%s>' %cmd)
                tm.execTask("launcher", cmd, '')
                logger.info('cut-log done') 
        except Exception, e:
            logger.error('cutting log error<%s>' %str(e))
      
     

def remove_cutlog(tm, logdir, logs, options, logger):
    ''' removing a cut-log file '''
    
    cmd_tmp='EXEC LOG Remove_Log logpath="%s"'
    
    for log in logs:
        
        log=os.path.join(logdir, log)
        if not os.path.exists(log):
            logger.info('remove-cut-log not exist<%s>' %log)
            continue
               
        cmd=cmd_tmp %log
        if options.dry_run:
            logger.info('remove-cut-log cmd<%s>' %cmd)
        else:
            logger.info('remove-cut-log cmd<%s>' %cmd)
            tm.execTask("launcher", cmd, '')
            logger.info('remove-cut-log done')

def get_log_age(ct, logpath, logger):
    """ get time stamp of a file and file's age. 
        args=(filepath, time.localtime()) """

    st_mtime=os.path.getmtime(logpath)
    t=time.localtime(st_mtime) 

    modified_time=datetime.datetime(t.tm_year,t.tm_mon,t.tm_mday,t.tm_hour,t.tm_min,t.tm_sec)

    current_time=datetime.datetime(ct.tm_year,ct.tm_mon,ct.tm_mday,ct.tm_hour,ct.tm_min,ct.tm_sec)

    delta=current_time-modified_time
   
    #logger.info('time deleta<%s>' %str(delta))
    return '%s' %str(delta)

def main(options,args):
    
    logname = 'sendlog'
    logger = ssdlog.make_logger(logname, options)
   
    ro.init()
    tm=ro.remoteObjectProxy('taskmgr0')
    tm.loadModule('LOGTask')
    tm.addAllocs(['STARS'])
     
    today = datetime.date.today()
    one_day = datetime.timedelta(days=1)
    yesterday = today - one_day

    if not options.fromdate:
        obs_time_from= '%s 17:00:00' %(yesterday)
        day_time_from= '%s 08:00:00' %(yesterday)
  
    else:
        obs_time_from=options.fromdate
        day_time_from=options.fromdate

    if not options.todate:
        obs_time_to='%s 08:00:00' %(today)
        day_time_to= '%s 17:00:00' %(yesterday)
  
    else:
        obs_time_to=options.todate    
        day_time_to=options.fromdate

    try:
        logdir=os.environ['LOGHOME']
    except KeyError,e:
        logdir='/gen2/logs'     

    if not options.indexdir:
        index_dir=os.path.join(os.environ['LOGHOME'],'cuts')
    else:
        index_dir=options.indexdir

    if not options.cutdir:
        cutdir=os.path.join(os.environ['LOGHOME'],'cuts')
    else:
        cutdir=options.cutdir  

    # time for today
    log_time_td="%d%02d%02d" %(today.year, today.month, today.day)  # e.g. 20100515

    # time for yesterday
    log_time_yd="%d%02d%02d" %(yesterday.year, yesterday.month, yesterday.day)  # e.g. 20100515


    ''' send tsc status logs '''
    obs_mode='17';
    tsc_logs=get_log_name(TSC_STATUS_LOGS, log_time_yd, obs_mode, logger)
    mode='OBS'
    send_log(tm, cutdir, tsc_logs, log_time_yd, index_dir, obs_time_from, obs_time_to, mode, options, logger)
   
    obs_mode='08';
    tsc_logs=get_log_name(TSC_STATUS_LOGS, log_time_yd, obs_mode, logger)
    mode='DAY'
    send_log(tm, cutdir, tsc_logs, log_time_yd, index_dir, day_time_from, day_time_to, mode, options, logger)

    ''' send instrument logs'''
    #obs_mode='obs'
    #cutlogs=get_log_name(INS_CUTLOGS, log_time_yd, obs_mode, logger)
    #cut_log(tm, logdir, INS_LOGS, cutdir, cutlogs, time_from, time_to, options, logger)
    #mode='OBS'
    #send_log(tm, cutdir, cutlogs, log_time_yd, index_dir, time_from, time_to, mode, options, logger)


    ''' send gen2 logs '''
    #obs_mode='obs'
    #cutlogs=get_log_name(GEN2_CUTLOGS, log_time_yd, obs_mode, logger)
    #cut_log(tm, logdir, GEN2_LOGS, options.cutdir, cutlogs, time_from, time_to, options,logger)
    #mode='OBS'
    #send_log(tm, cutdir, cutlogs, log_time_yd, index_dir, time_from, obs_time_to, mode, options, logger)

 
    ''' send ENDLOG'''
    mode='OBS'
    send_endlog(tm, logdir, end_log, log_time_yd, index_dir, obs_time_from, obs_time_to, mode, options, logger)

    
if __name__=="__main__":
    
    from optparse import OptionParser

    usage = "usage: %prog [options] [file] ..."
    optprs = OptionParser(usage=usage, version=('%prog'))

    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    
    optprs.add_option("--indexdir", dest="indexdir", metavar="INDEXDIR",
                      default="/gen2/logs/cuts",
                      help="specify index dir")

    optprs.add_option("--cutdir", dest="cutdir", metavar="CUTDIR",
                      default="/gen2/logs/cuts",
                      help="specify temporary stored cut-log dir")
    
    optprs.add_option("--from", dest="fromdate", metavar="DATE",
                      help="Specify to DATE as YYYY-MM-DD HH:MM:SS")

    optprs.add_option("--to", dest="todate", metavar="DATE",
                      help="Specify to DATE as YYYY-MM-DD HH:MM:SS")
    
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
    
    
    

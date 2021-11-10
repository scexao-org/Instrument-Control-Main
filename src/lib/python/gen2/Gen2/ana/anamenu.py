#!/usr/bin/env python

import os
import sys
import re
import getpass
import subprocess
import shlex
import pango

import ssdlog

from anamenuui import * 

class Error(Exception):
    """Base class for exceptions in this module."""
    pass
 
class Process(object):

    def __init__(self, logger):

        self.logger = logger
        self.processes = []    

    def execute(self, args):
    
        self.logger.debug('executing %s' %args)
        try:
            process = subprocess.Popen(args)
        except Exception as e:
            res = '%s' %str(e)
        else:
            if process.pid:
                self.processes.append(process)    
            res = 0
        finally:
            return res

    def terminate(self):
        
        for process in self.processes:
            try:
                self.logger.debug('terminating pid=%d' %process.pid)
                process.terminate()
            except Exception as e:
                self.logger.error('error: terminating process. %s' %e)
                
    
class AnaMenuCd(AnaMenuUi):

    def __init__(self, logger):

        super(AnaMenuCd,self).__init__(logger)
        self.set_ui()
        
        self.process = Process(logger)
        self.window_width = 430
        self.window_height = 450
        self.uid = None
        self.propid = None
        self.propfile = '/tmp/propid'
        self.logger = logger

        self.__init_propid_entry()

    def expand_log(self, expander):
        
        if expander.get_expanded():
            expander.remove(expander.child)
            self.window.resize(self.window_width, self.window_height)
        else:
            expander.add(self.sw_expander)            #expander.add(self.textview_log)

#            iter=self.buffer_log.get_start_iter()
#            self.buffer_log.insert(iter, 'test... %d\n' %self.c)
#            self.c+=1

    def __init_propid_entry(self):
        self.get_propid()
        if self.propid:
            self.write_propid()
            self.attr_list.insert(self.attr_valid)
            self.entry_propid.get_layout().set_attributes(self.attr_list)  
            self.entry_propid.set_text(self.propid)
            self.entry_propid.set_sensitive(False)
            self.btn_propid.set_active(True)
            
 
    def get_propid(self):
        self.uid = getpass.getuser()   
        self.logger.debug('user=%s' %self.uid)
        m = re.search(r'(?<=u|o)\d{5}', self.uid)
        if m:
            self.propid = 'o%s' %m.group(0)
            self.logger.debug('propid<%s>' %self.propid)

    def quit(self, obj):
        
        self.remove_propid()
        self.process.terminate()
        gtk.main_quit()
        
    def start(self):   
        gtk.main() 

    def is_propid(self, propid):
        try:
            m=re.search(r'(?<=o)\d{5}', propid)
        except Exception:
            m=None
        return m
               
    def set_propid(self, obj):
 
        if obj.get_active():
            propid=self.entry_propid.get_text()
            res=self.is_propid(propid)
            if res:
                self.propid=propid
                self.write_propid()
                self.attr_list.insert(self.attr_valid)
                self.entry_propid.get_layout().set_attributes(self.attr_list)  
                self.entry_propid.set_sensitive(False)
            else:
                self.attr_list.insert(self.attr_invalid)
                self.entry_propid.get_layout().set_attributes(self.attr_list)  
                self.btn_propid.set_active(False)    
        else:
            self.entry_propid.set_sensitive(True) 

    def __execute(self, cmd, procname):
        ''' execute applications '''
        iter=self.buffer_log.get_start_iter()
    
        error=self.process.execute(cmd)
        
        if not error:
            self.buffer_log.insert(iter, '%s started...\n' %(procname))
        else:
            self.logger.error('error: launching %s.. %s'  %(procname, error))
            self.buffer_log.insert(iter, 'error: %s. %s\n' %(procname, error)) 

    def remove_propid(self):
        try:
            os.remove(self.propfile)  
        except OSError as e:
            self.logger.error('error: removing propfile. %s' %str(e))

    def write_propid(self):
        try:
            f = open(self.propfile, 'w')
            f.write(self.propid)
        except OSError as e:
            self.logger.error('error: writing propid. %s' %str(e))

    def get_gen2home(self):
        try:
            gen2home = os.environ['GEN2HOME']
        except OSError:
            gen2home = '/home/gen2/Git/python/Gen2'    
        finally:
            return gen2home
   
    @property
    def loghome(self):
        return os.path.join('/home', self.uid)  

    def launch_fits_viewer(self, obj):
        ''' fits viewer '''

        #os.environ['DISPLAY']='133.40.159.24:0.1'
        gen2home='/home/gen2/Git/Fitsview'
        #logdir = os.path.join('/home', self.uid)

        command_line="{0}/fitsview.py --rohosts=g2ins1 --modules=ANA --plugins=Ana_Confirmation,Ana_UserInput --svcname=ANA --port=11033 --monport=11034 --loglevel=warn --log={1}/anaview.log".format(gen2home, self.loghome)
        args = shlex.split(command_line)
        self.__execute(cmd=args, procname='fits viewer')
   
    def launch_telstat(self, obj):
        ''' telstat '''
        self.logger.debug('starting telstat...') 
        #os.environ['DISPLAY']='133.40.159.24:0.1'
        os.environ['RO_NAMES']='g2ins1'

        gen2home = self.get_gen2home()
        #logdir = os.path.join('/home', self.uid)

        #command_line="{0}/telstat/telstat.py --name=telstat_ana.mon --loglevel=0  --log={1}/telstat.log".format(gen2home, self.loghome)
  
        command_line="{0}/telstat/OSSO_TelStat --name=telstat_ana.mon --g2 -c status --loglevel=0 --geometry +20+100".format(gen2home)

        args = shlex.split(command_line)   

        self.__execute(cmd=args, procname='telstat')
         
    def launch_skycat(self, obj):
        ''' skycat '''
        #os.environ['DISPLAY']='133.40.159.24:0.0'
        command_line = "wish8.4 /usr/local/lib/skycat3.1.2/main.tcl"
        args = shlex.split(command_line)

        self.__execute(cmd=args, procname='skycat')

    def launch_ds9(self, obj):
        ''' ds9 '''
        #os.environ['DISPLAY']='133.40.159.24:0.0'
        self.__execute(cmd=["ds9",], procname='ds9')

    @property
    def workdir(self):
        return os.path.join('/work', self.propid)

    @property
    def datadir(self):
        return os.path.join('/data', self.propid)

    def __execute_obcp(self, obcp, cmd, insname=None):
        ''' execute obcp '''  
        #os.environ['DISPLAY']='133.40.159.24:0.0'

        iter=self.buffer_log.get_start_iter()
        
        if not self.is_propid(self.propid):
            self.buffer_log.insert(iter, 'error: propid=%s\n' %str(self.propid))
            self.logger.error('error: propid=%s' %str(self.propid))
            return 
  
        command_line=cmd  %(self.propid, obcp, self.datadir, self.workdir)
        args = shlex.split(command_line)
  
        self.logger.debug('%s cmd=%s' %(insname, args)) 

        error = self.process.execute(args)
        if not error:
            self.buffer_log.insert(iter, 'starting %s...\n' %(insname))
        else:
            self.buffer_log.insert(iter, 'error: %s. %s\n' %(insname, error))     
            self.logger.error('error: launching %s.. %s'  %(insname, error))

    def launch_spcam(self, obj):
        self.logger.debug('starting spcam....') 

        obcp = 'OBCP08'
        cmd = "/home/spcam01/suprime/suprime.ana %s %s %s %s"
        insname = 'SPCAM' 
        self.__execute_obcp(obcp, cmd, insname)
 
    def launch_hds(self, obj):
        self.logger.debug('starting hds....') 
        obcp = 'OBCP06'
        cmd = "/home/hds01/hds.ana %s %s %s %s" 
        insname = 'HDS' 
        self.__execute_obcp(obcp, cmd, insname)

    def launch_ircs(self, obj):
        self.logger.debug('starting ircs....') 

        obcp = 'OBCP01'
        cmd = "/home/ircs01/ircs/ircs.ana %s %s %s %s"
        insname = 'IRCS'
        self.__execute_obcp(obcp, cmd, insname)

    def launch_focas(self, obj):
        self.logger.debug('starting focas....') 

        obcp = 'OBCP05'
        cmd = "/home/focas01/focas.ana %s %s %s %s"
        insname = 'FOCAS'
        self.__execute_obcp(obcp, cmd, insname)

    def launch_moircs(self, obj):
        self.logger.debug('starting moircs....') 
        obcp = 'OBCP17'
        cmd = "/home/moircs01/moircs/moircs.ana %s %s %s %s"
        insname = 'MOIRCS'
        self.__execute_obcp(obcp, cmd, insname)

    def datasink(self):
        ''' running as daemon 
             datasink.py -g <gen2host> -f <keyfile> -d /path/to/data/directory '''


def main(options,args):
 
    logname = 'ana_menu'
    logger = ssdlog.make_logger(logname, options)

    try:
        ana=AnaMenuCd(logger)
        ana.start()
      
        print 'GUI END' 
    except KeyboardInterrupt,e:
        print 'interrupting....'
        logger.debug('Keyboard Interrupt...')
        ana.quit('quit')
        #gtk.main_quit()


if __name__ == "__main__":

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options] [file] ..."
    optprs = OptionParser(usage=usage, version=('%prog'))
    

    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
 
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










    

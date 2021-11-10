#! /usr/bin/env python

# Import Pmw from this directory tree.
import sys
import os
import threading
import subprocess
import time
import Tkinter
import Pmw
import getpass
import re
import ssdlog
import signal
import SOSS.SOSSrpc as SOSSrpc
#import cfg.g2soss as g2soss

""" usage

for observation
/home/builder/bin/pywrap.sh /home/builder/Svn/python/Gen2/client/ana.py
* loglevel is 0
* log file is /tmp/ana.log 


# for testing with gen2 simulator. on terminal: 
/home/builder/bin/pywrap.sh /home/builder/Svn/python/Gen2/client/ana.py --display=lower --stderr --gen2host=simulator
*default display is upper. that is,  fitsviewr starts on upper screen. 

*make sure to switch anasink to sim. otherwise, data are not comming
 on terminal:
 $ipython
 In [1]: import xmlrpclib
 In [2]: s = xmlrpclib.ServerProxy('http://hana:15003') # hana or ana
 In [3]: s.set_gen2host('simulator') # set to gen2 simulator(g2b3)
         OR
 In [3]: s.set_gen2host('summit') # set to gne2 summit(g2s3) 
 


"""


class AnaUi(object):

    def setup_ui(self,parent, logger):
        
        logger.debug("setting up ana menu gui")  
        ''' buttons for Gen2 application'''
        self.buttonBoxView = Pmw.ButtonBox(parent,
                labelpos = 'nw',
                label_text = 'Viewers:',
                frame_borderwidth = 2,
                frame_relief = 'groove')
        self.buttonBoxView.pack(fill = 'both', expand = 1, padx = 10, pady = 10)

        ''' buttons for instruments '''
        self.buttonBoxIns = Pmw.ButtonBox(parent,
                labelpos = 'nw',
                label_text = 'Instrument:',
                frame_borderwidth = 2,
                frame_relief = 'groove')
        self.buttonBoxIns.pack(fill = 'both', expand = 1, padx = 10, pady = 10)

        ''' buttons for more instrument '''
        self.buttonBoxProg = Pmw.ButtonBox(parent,
                labelpos = 'nw',
                label_text = 'Data-sink | Ana-prog:',
                frame_borderwidth = 2,
                frame_relief = 'groove')

        self.buttonBoxProg.pack(fill = 'both', expand = 1, padx = 10, pady = 10)

        ''' status of a pressed button '''
        self.messageBar = Pmw.MessageBar(parent,
                entry_width = 40,
                entry_relief='groove',
                labelpos = 'nw',
                label_text = 'Status:')
        self.messageBar.pack(fill = 'x', expand = 1, padx = 10, pady = 10)

        ''' dialog to display the status of datasink server'''
        self.ds_dialog = Pmw.TextDialog(parent, scrolledtext_labelpos = 'n',
                title = 'Frame Log',
                buttons = ('stop data-sink',),
                defaultbutton = None,
                command=self.stop_datasink)
                #label_text = 'incoming frame status')        

        self.ds_dialog.withdraw()        
 
        ''' dialog to get proposal id  '''
        self.prop_dialog = Pmw.PromptDialog(parent, 
                                            title = 'Proposal ID',
                                            label_text = 'Prop ID:',
                                            entryfield_labelpos = 'w',
                                            #entry_show = '*',
                                            defaultbutton = 0,
                                            buttons = ('OK','Cancel'),
                                            command = self.get_propid )
        self.prop_dialog.withdraw()
 
        '''  create the confirmation dialog '''
        self.confirm = Pmw.MessageDialog(title = 'Prop ID Confirmation',
                                         message_text = 'Are you really sure?',
                                         defaultbutton = 0,
                                         buttons = ('OK', 'Cancel'))
        self.confirm.withdraw()
 
 
        '''  create the confirmation dialog '''
        self.pid_format = Pmw.MessageDialog(title = 'PID Format Error',
                                         message_text = 'Pid Format Error\nFormat is oXXXXX',
                                         defaultbutton = 0,
                                         #icon_bitmap='error',
                                         buttons = ('Close',))
        self.pid_format.withdraw()

 
        ''' Add some buttons to the ButtonBox.'''
        self.buttonBoxView.add('FitsViewer', command = self.launch_viewer)
        self.buttonBoxView.add('TelStat', command=self.launch_telstat )
        #self.buttonBoxGen2.add('DataSink', command = self.init_datasink )
        self.buttonBoxView.add('Ds9', command = self.launch_ds9)
        self.buttonBoxView.add('Skycat', command = self.launch_skycat)

        #self.buttonBoxGen2.add('ANA Prog',command=self.start_ana_prog )

        self.buttonBoxIns.add('HDS', command = self.launch_hds)
        self.buttonBoxIns.add('SPCAM', command = self.launch_spcam)
        self.buttonBoxIns.add('FOCAS', command = self.launch_focas)
        self.buttonBoxIns.add('MOIRCS', command = self.launch_moircs)
        self.buttonBoxIns.add('IRCS', command = self.launch_ircs)
    
        self.buttonBoxProg.add('DataSink', command = self.init_datasink )
        self.buttonBoxProg.add('ANA Prog',command=self.start_ana_prog )
        self.buttonBoxProg.add('Avail 1',command='' )
        self.buttonBoxProg.add('Avail 2',command='' )

        ''' Make all the buttons the same width. '''
        self.buttonBoxView.alignbuttons()
        self.buttonBoxIns.alignbuttons()
        self.buttonBoxProg.alignbuttons()
        
        ''' disable buttons '''
        self.buttonBoxProg.component('DataSink').configure(state='disabled')
        #self.buttonBoxView.component('Avail 1').configure(state='disabled')
        self.buttonBoxProg.component('Avail 1').configure(state='disabled')
        self.buttonBoxProg.component('Avail 2').configure(state='disabled')

        #self. exitButton = Tkinter.Button(parent, text = 'Exit', command = parent.destroy)
        self. exitButton = Tkinter.Button(parent, text = 'Exit', command = self.close_window)
        self.exitButton.pack(side = 'bottom') 
  
        logger.debug("ana menu gui done")


class AnaMenu(AnaUi):
    def __init__(self, parent, propid, gen2host, display, localhost, host_key, host_pass, logger=None, usethread=True, ev_quit=None ):

        self.propid=propid
        self.display=display
        self.localhost = localhost
        self.key=host_key
        self.apass=host_pass
        self.parent=parent
        self.logger=logger        

        if gen2host == 'summit':
            self.ro_name='g2s1'
            self.gen2host='g2b1'
            self.pullhost='g2b1'
        else:
            self.ro_name='g2sim'
            self.gen2host='g2sim'     
            self.pullhost='g2sim'
                    
        self.pullname='gen2'
        
        AnaUi.setup_ui(self, self.parent, logger=logger)
             
        self.usethread = usethread
             
        if not ev_quit:
            self.ev_quit = threading.Event()
        else:
            self.ev_quit = ev_quit
       
        self.pid_list=[]
        #self.ppid_list=[]
    
        self.start_ana_prog()

    def close_window(self):
        self.logger.debug("closing window")
        self.stop_reading()
        self.terminate_pid()
        #self.stop_datasind(status='stop')
        self.parent.destroy()

    def terminate_ppid(self): 
        
        for ppid in self.ppid_list:
            self.logger.debug("terminating ppid<%d>" %(int(ppid)))
            try:
                subprocess.Popen("pkill -15  -P %d" %(int(ppid)), shell=True)
                idx=self.ppid_list.index(ppid)
                del self.ppid_list[idx]
            except OSError,e:
                self.logger.error("fail to terminate ppid<%d>" %(ppid))
               

    def terminate_pid(self):
        for pid in self.pid_list:
            try:
                self.logger.debug('terminating a process<%d>' %(pid))
                os.kill(pid, signal.SIGTERM)
                idx=self.pid_list.index(pid)
                del self.pid_list[idx]
            except OSError,e:
                self.logger.error('failed to terminate a process<%d>' %pid)
      

    def stop_datasink(self,status):
        self.messageBar.message('state','stopping data-sink')
        self.logger.debug('stopping data-sink<%s>' % status)
        if status.startswith('stop'):
            self.stop_reading()
            #self.terminate_ppid()
            self.terminate_pid()
            self.ds_dialog.withdraw() 
            self.messageBar.message('state','data-sink stopped')
            self.buttonBoxProg.component('DataSink').configure(state='normal')
                       
    def stop_reading(self):
        '''Stop updating lcd '''
        self.ev_quit.set()
        self.logger.debug("stop updating dialog")

    def start_reading_pipe(self,ds):
        if self.usethread:
            dialog_thread=threading.Thread(target=self.updating_dialog,args=(ds,) )
            dialog_thread.start()

    def updating_dialog(self,ds):
        
        self.logger.debug("start updating dialog")
        self.ds_dialog.clear()     
        while not self.ev_quit.isSet():# and self.ds_dialog.insert('end', self.output.stdout.readline()):
            output=ds.stderr.readline()
            self.logger.debug('data-sink pipe<%s>' %output)
            #if not output.strip()=='Terminated':
            if not output == '':
                self.ds_dialog.insert('end', output)
    
    def start_datasink(self, data_dir):
        ''' data is being sent to ana '''      
        self.logger.debug("starting data sink")
     
        self.ev_quit.clear()     
   
        cmd = '/home/builder/Svn/python/Gen2/client/anasink.py'
        #viewer='/home/builder/bin/send_skycat %(filepath)s' 
        viewer='fitsviewer' 
        
        self.logger.debug('%s -f %s -d %s -p %s -a %s --host %s --pullhost=%s --pullname=%s --nomd5check' %(cmd, self.key, data_dir, self.apass, viewer, self.gen2host, self.pullhost, self.pullname ))
        try:
            self.messageBar.message('state','starting data-sink')
  
            os.environ['PATH']="/usr/local/bin:%s" %(os.environ["PATH"])
            ds=subprocess.Popen( [cmd,'-f', self.key, '-d', data_dir, '-p', self.apass,'-a', viewer, '--host', self.gen2host, '--pullhost', self.pullhost, '--pullname', self.pullname, '--nomd5check', '--loglevel=0'], stderr=subprocess.PIPE )

            #self.ds=subprocess.Popen( [cmd,'-f',ana_key, '-d', data_dir, '-p', ana_pass,'-a', viewer], env={'PATH':path}, stderr=subprocess.PIPE )
            self.pid_list.append(ds.pid)
            self.messageBar.message('state','data-sink started')
            
            
        except OSError,e:
            self.logger.error("fail to start data-sink<%s>" %(e))
            self.messageBar.message('systemerror','data-sink error<%s>' %e)
            ds=None
        
        return ds    

    def _get_user(self):
        ''' get login user '''
        return getpass.getuser()

    #def _validate_propid(uid):
    #    return re.search(r'(?<=u)\d{5}', uid )
        
 
    def _get_proposal_id(self):
        ''' get propid '''    
  
        uid=self._get_user()
        m=re.search(r'(?<=u)\d{5}', uid )
  
        ''' when a u-user's account does not start with u such as eng account ircs01,
            ask a user to enter a propid
        '''
      
        if m:
            self.propid = 'o%s' %m.group(0)
            self.logger.debug('get_proposal id<%s>' %self.propid)
        else:
            self.prop_dialog.title('Prop ID for %s' %(uid))
            self.prop_dialog.activate()
                  
    def _get_data_dir(self):
        ''' get user's storing data dir '''
        
        try:
            self.logger.debug('get_data_dir<%s>' %self.propid) 
            self.propid.startswith('o')
            return '/data/%s' %self.propid
            #return '/data'
        except:
            #return '/data'
            return os.getenv('HOME')
                   
 
    def _get_work_dir(self): 
        ''' get user's work dir '''       
        
        try:
            self.propid.startswith('o')

            return '/work/%s' %self.propid
        except:
            return os.getenv('HOME')    
   
    def get_propid(self,result):
        '''  get propid from dialog '''
        
      
        
        if result is None or result == 'Cancel':
            
            self.logger.debug('prop id canceled')
            #self.get_propid(result)
            self.prop_dialog.deactivate(result)
            self.propid=None
            self.logger.debug('Canceled')
            
        else:
            result = self.confirm.activate()
            if result == 'OK':
                self.propid = self.prop_dialog.get()
                self.logger.debug('prop id entered:<%s>' %(self.propid))
                if re.match(r"^o\d{5}$", self.propid):
                #if self.propid.startswith('o'):
                    self.prop_dialog.deactivate()
                    self.logger.debug('get right pid<%s>' %(self.propid))
                    
                else:
                    self.pid_format.activate()
                    self.propid=None
                    

    def start_ana_prog(self):
        ''' ana_prog is to execute ana cmds  '''
        
        os.environ['PYTHONPATH']='/home/builder/Svn/python'
        #os.environ['RO_NAMES']='g2s1'
        os.environ['RO_NAMES']=self.ro_name
        os.environ['SOSSHOME']='/home/builder'
        os.environ['PATH']="/usr/local/bin:%s" %(os.getenv("PATH"))
 
        ##path="/usr/local/bin:%s" %(os.environ["PATH"])
        try:
            #qdas_pid=subprocess.Popen(["/home/builder/bin/qdas.py",  '--svcname=ANA', '--loglevel=10'], env={'PYTHONPATH':'/home/builder/Svn/python', 'RO_NAMES':'g2s1', 'SOSSHOME':'/home/builder', 'PATH':path, 'DATAHOME':'/data' },)
            self.logger.debug("starting ana_prog") 
            qdas_pid=subprocess.Popen(["/home/builder/bin/qdas.py", '--port=9009',  '--svcname=ANA', '--loglevel=0','--log=/tmp/ana.log' ]).pid
            self.pid_list.append(qdas_pid)
            
            self.buttonBoxProg.component('ANA Prog').configure(state='disabled')            
            self.messageBar.message('state','ana_prog started')

        except OSError, e:
            self.logger.error('ana_prog error <%s>' ,e)
            self.messageBar.message('systemerror','ana_prog starting error<%s>' %(e))
               

    def init_datasink(self):
        ''' recieve data '''
        if not self.propid:
            self._get_proposal_id()
        
        data_dir=self._get_data_dir()  
        self.logger.debug("data-sink dir<%s>" %(data_dir))

        ds=self.start_datasink(data_dir)
        if not ds==None:
            self.ds_dialog.show() 
            self.start_reading_pipe(ds)
            self.buttonBoxProg.component('DataSink').configure(state='disabled')    
          
  
        
    def launch_ds9(self):
        ''' launch ds9 '''
        try:
            self.logger.debug("starting ds9")
            #self.messageBar.message('state','starting ds9')
            subprocess.Popen(['ds9',])
            self.messageBar.message('state','ds9 started')
        except OSError,e:
            self.logger.error('ds9 error <%s>' ,e)
            self.messageBar.message('systemerror','ds9 starting error<%s>' %(e))

    def launch_skycat(self):
        ''' launch ds9 '''
        try:
            self.logger.debug("starting skycat")
            #self.messageBar.message('state','starting ds9')
            subprocess.Popen(['skycat',])
            self.messageBar.message('state','skycat started')
        except OSError,e:
            self.logger.error('skycat error <%s>' ,e)
            self.messageBar.message('systemerror','skycat starting error<%s>' %(e))
        

    def launch_telstat(self):
        ''' launch telstat '''

        #g2soss.make_env('TELSTAT', options=self.options)
        
        self.logger.debug('starting telstat@%s ...' %self.localhost) 
  
         
        if self.localhost=='ana':
            self.logger.debug('telstat@ana ...')
            os.environ['OSSO_LOCALE']='SUMMIT'
            os.environ['OSS_LOAD_MODULE']='/app/LOAD/DEBUG'
            os.environ['OSS_SOUND']='/home/builder/conf/file/Sounds'
            os.environ['OSSO_IMAGE']='/home/builder/conf/file'
            os.environ['PYTHONPATH']='/app/LOAD/DEBUG/OSSO_TelStatLib:/opt/share/ssd/python251/lib/python2.5/site-packages:/home/builder/Svn/python'
            
        else:
    
            if self.localhost=='hana':
                self.logger.debug('telstat@hana ...')
                os.environ['OSSO_LOCALE']='HILO'
            elif self.localhost=='sbana':
                self.logger.debug('telstat@sbana ...')
                os.environ['OSSO_LOCALE']='MITAKA'
            else:
                self.logger.error('telstat@??? ...')
 
            os.environ['OSS_LOAD_MODULE']='/app/OSS/remote/load'
            os.environ['OSS_SOUND']='/app/OSS/remote/file'
            os.environ['OSSO_IMAGE']='/app/OSS/remote/file'
            os.environ['PYTHONPATH']="/app/OSS/remote/load/OSSO_TelStatLib:/opt/share/ssd/python251/lib/python2.5/site-packages:/home/builder/Svn/python"


        os.environ['TELSTAT_MANPATH']=os.path.join(os.environ['OSS_LOAD_MODULE'],'OSSO_TelStatLib')
        #os.environ['PYTHONPATH']="/app/OSS/remote/load/OSSO_TelStatLib:/opt/share/ssd/python251/lib/python2.5/site-packages:/home/builder/Svn/python"

        path=os.environ['PATH']
        os.environ['PATH']="/opt/share/ssd/python251/bin:/opt/share/ssd/tcl84/bin:%s"  %(path)

        ld_lib_path=os.environ['LD_LIBRARY_PATH']
        os.environ['LD_LIBRARY_PATH']="/opt/share/ssd/python251/lib:/opt/share/ssd/tcl84/lib:/opt/share/ssd/lib:/usr/local/lib/python2.5/lib-dynload:/app/TOOL/skycat/ld_lib:/usr/openwin/lib:/usr/dt/lib:/opt/SUNWspro/lib:/usr/lib:/opt/ORA/app/oracle/product/10.2.0/lib32:/opt/share/lib:/usr/local/lib" # %(ld_lib_path)

        self.logger.debug('PATH=%s' %(os.environ['PATH']))
        self.logger.debug('PYTHONPATH=%s' %(os.environ['PYTHONPATH']))
        self.logger.debug('LD_LIBRARY_PATH=%s' %(os.environ['LD_LIBRARY_PATH']))


        os.environ['RO_NAMES']='g2s1'

        if self.display:
            os.environ['DISPLAY']=self.display

        try:
            cmd = os.path.join(os.environ['OSS_LOAD_MODULE'], 'OSSO_TelStat')
            self.logger.debug('telstat cmd %s' %cmd)
            subprocess.Popen([cmd, '-g2'])
            self.messageBar.message('state','telstat started')
        except OSError,e:
            self.logger.error('telstat error %s' %str(e))
            self.messageBar.message('systemerror','telstat error<%s>' %(e))

    def launch_viewer(self):
        ''' launch fitsviewer '''
       
        if not self.propid:
            self._get_proposal_id()
            self.logger.debug('get propid<%s>' %(self.propid))  
            if self.propid==None:
                self.logger.warn('could not get proposal id:<%s>' %(str(self.propid)))
                return


        #try:
        #    self.propid.startswith('o')       
        #except Exception,e:
        #    self.logger.error("propid is an empty. can't start fitsviewer")  
        #    return 

        self.logger.debug('fits viewer prop-id<%s>' %self.propid)
        #os.environ['PATH']='/opt/share/ssd/python251/bin:/opt/share/ssd/tcl84/bin:%s' %os.getenv('PATH')
        
        os.environ['FITSVIEW_HOME']='/tmp'  # under /tmp/dat  two fifo will be created 

        if self.display:
            os.environ['DISPLAY']=self.display

        self.logger.debug("viewer display<%s>" %(self.display))

        #if self.gen2host=='g2b1':
        #    os.environ['DISPLAY']=':0.1'         
        #else:
        #    os.environ['DISPLAY']=':0.0'
   
        try:
            self.logger.debug("starting up fits-viewer")
            #self.messageBar.message('state','starting viewer')
            self.logger.debug('/home/builder/bin/fitsviewer.py --usefifo --svcname=fitsview_ana --host=%s --propid=%s' %(self.localhost,self.propid))
            subprocess.Popen(['/home/builder/bin/fitsviewer.py','--usefifo', '--svcname', 'fitsview_ana', '--host', self.localhost, '--propid', self.propid, '--loglevel=0', '--stderr', '--log=/tmp/ana.log'])

            #subprocess.Popen(['/home/builder/bin/fitsviewer.py','--usefifo', '--svcname', 'fitsview_ana', '--host', self.localhost, ],)
            #subprocess.Popen(['skycat','-name', 'anaview'])
            self.messageBar.message('state','viewer started')
        except OSError,e:
            self.logger.error("viewer error")
            self.messageBar.message('systemerror','viewer starting error<%s>' %(e))


    def _exec_instrument(self, exec_ins, obcp):
        '''' exec instrument application '''
        os.environ['DISPLAY']=':0.0'
        if not self.propid:
            self._get_proposal_id()
            
        data_dir=self._get_data_dir()
        work_dir=self._get_work_dir()
  
        try:
            self.logger.debug("%s  args<%s %s %s %s>" %(exec_ins, self.propid, obcp, data_dir, work_dir ))
            ins_pid=subprocess.Popen([ exec_ins, self.propid,obcp, data_dir, work_dir]).pid
            self.pid_list.append(ins_pid)
            self.messageBar.message('state','%s started' %(exec_ins))
        except OSError,e:
            self.logger.error('%s error<%s>' %(exec_ins,e))
            self.messageBar.message('systemerror','launching %s  error<%s>' %(exec_ins,e))
  
    def launch_hds(self):
        ''' launch hds application  '''
      
        exec_ins='/opt/share/bin/hds.ana'
        obcp='OBCP06'
                
        self._exec_instrument(exec_ins, obcp)
     
    def launch_spcam(self):
        ''' launch spcam application  '''
        exec_ins='/opt/share/bin/suprime.ana'
        obcp='OBCP08'
                
        self._exec_instrument(exec_ins, obcp)

   
    def launch_focas(self):
        ''' launch focas application '''
        exec_ins='/opt/share/bin/focas.ana'
        obcp='OBCP05'
                
        self._exec_instrument(exec_ins,obcp)
 

    def launch_moircs(self):
        ''' launch moircs application '''
        exec_ins='/opt/share/bin/moircs.ana'
        obcp='OBCP17'
                
        self._exec_instrument(exec_ins,obcp)

    def launch_ircs(self):
        ''' launch ircs application '''
        exec_ins='/opt/share/bin/ircs.ana'
        obcp='OBCP01'
                
        self._exec_instrument(exec_ins,obcp)
        


######################################################################


def main(options, args):
    
    svcname = ('ana_menu')

    if not options.logstderr:
        options.logfile='/tmp/ana.log'
        options.loglevel=0

    logger = ssdlog.make_logger(svcname, options)

    try:
        os.chmod(options.logfile,0666)
    except Exception,e:
        logger.warn('warning: changing permission.<%s> ' %(e))
  
    logger.debug('ana menu started')

    logger.debug('PROPID:<%s>' %(options.propid))

    try:
        localhost = SOSSrpc.get_myhost(short=True)
        logger.debug('fetching host name<%s>' %localhost) 
    except Exception,e:
        try:
            localhost = os.environ['HOST']
            logger.debug('fetching host name from environ<%s>' %localhost)  
        except KeyError,e:
            logger.error('fetching host name error<%s>' %e)
            sys.exit(1)

    host_key="/home/builder/bin/%s.key" %localhost
    host_pass="/home/builder/bin/%s.pass" %localhost

    logger.debug('KEY:<%s>' %(host_key))
    logger.debug('PASS:<%s>' %(host_pass))
    
    if (not options.gen2host=='summit') and (not options.gen2host=='simulator'):
        logger.error('gen2 host is either summit or simulator') 
        sys.exit(1)  
    
 
    if options.display=='upper':
        options.display=':0.1'
    elif options.display=='lower':
        options.display=None
    else:
        logger.error('options display should be either upper or lower')

    root = Tkinter.Tk()
    Pmw.initialise(root)
    root.title('ANA Menu')
 
    if options.geometry:
        root.geometry(options.geometry)

    ana = AnaMenu(root, options.propid, options.gen2host, options.display,localhost, host_key, host_pass, logger)
    root.mainloop()
   
    ana.stop_reading() 
    #ana.terminate_ppid()
    ana.terminate_pid()  
    logger.debug('Ana Menu END')



# Create demo in root window for testing.
if __name__ == '__main__':
  
    # Parse command line options with nifty optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options] <cmd>"
    parser = OptionParser(usage=usage, version=('%%prog'))
    

    parser.add_option("-g", "--geometry", dest="geometry",
                      metavar="GEOM", default="+750+450",
                      help="X geometry for initial size and placement")

    parser.add_option("-p", "--propid", dest="propid", default=None,
                      metavar="PROPID",
                      help="proposal id for data analysis")
    
    parser.add_option("--gen2host", dest="gen2host", default='summit',
                      metavar="GEN2HOST",
                      help="Communicate with gen2 [summit|simulator]")

    parser.add_option("--display", dest="display", default='upper',
                      metavar="DISPLAY",
                      help="Specify which display you want to run fitsviewr [upper|lower] ")


    #parser.add_option("--key", dest="key", default='/home/builder/bin/ana.key',
    #                  metavar="KEY",
    #                  help="key to recieve data")
    
    #parser.add_option("--pass", dest="apass", default='/home/builder/bin/ana.pass',
    #                  metavar="PASS",
    #                  help="pass to recieve data")
   
    ssdlog.addlogopts(parser)  
    (options,args) = parser.parse_args(sys.argv[1:])

    main(options, args) 













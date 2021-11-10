#! /usr/bin/env python
#
# example of creating a local monitor and subscribing to info with
# callback functions
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Jul  8 11:14:37 HST 2010
#]


import sys, os
import threading
import ssdlog
import pprint
import time
import Queue

import remoteObjects as ro
import remoteObjects.Monitor as Monitor
import re

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass
try:
    import gtk
    import gtk.glade
    import gnome.ui
except:
    sys.exit(1)


# task queue
TASKS = Queue.Queue(300)

def feed_test_data():
    
    
    test_data=[
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309': {'task_start': 1235779689.3433881}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141': {'task_start': 1235779689.352967}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Sequence-1235779689-3693430': {'task_start': 1235779689.3693981}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Sequence-1235779689-3693430.anonTask-1235779689-3719280': {'task_start': 1235779689.371979}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Sequence-1235779689-3693430.anonTask-1235779689-3719280': {'task_code': 0, 'task_end': 1235779689.3727331}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Sequence-1235779689-3693430.anonTask-1235779689-5140259': {'task_start': 1235779689.5140879}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Sequence-1235779689-3693430.anonTask-1235779689-5140259': {'task_code': 0, 'task_end': 1235779689.5274529}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Sequence-1235779689-3693430.anonTask-1235779689-5987711': {'task_start': 1235779689.5988269}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.anonTask-1235779689-5998781': {'task_start': 1235779689.599921}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Sleep-1235779689-6015170': {'task_start': 1235779689.601563}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Sleep-1235779689-6015170': {'task_code': 0, 'task_end': 1235779690.6032701}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.anonTask-1235779689-5998781': {'task_code': 0, 'task_end': 1235779690.6278181}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Concurrent-1235779690-6437271.anonTask-1235779690-6564901': {'task_start': 1235779690.6565621}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Concurrent-1235779690-6437271': {'task_start': 1235779690.6437931}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Sleep-1235779690-6676891': {'task_start': 1235779690.667779}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Concurrent-1235779690-6437271.anonTask-1235779690-7038059': {'task_start': 1235779690.7038691}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Sleep-1235779690-7168200': {'task_start': 1235779690.716871}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Sleep-1235779690-6676891': {'task_code': 0, 'task_end': 1235779691.6913519}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Sleep-1235779690-7168200': {'task_code': 0, 'task_end': 1235779691.719557}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Concurrent-1235779690-6437271.anonTask-1235779690-6564901': {'task_code': 0, 'task_end': 1235779691.723099}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Concurrent-1235779690-6437271.anonTask-1235779690-7038059': {'task_code': 0, 'task_end': 1235779691.765976}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Concurrent-1235779690-6437271': {'task_code': 0, 'task_end': 1235779691.8549161}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.anonTask-1235779691-9388571': {'task_start': 1235779691.9389141}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Sleep-1235779691-9451849': {'task_start': 1235779691.9452341}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Sleep-1235779691-9451849': {'task_code': 0, 'task_end': 1235779692.956269}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.anonTask-1235779691-9388571': {'task_code': 0, 'task_end': 1235779692.993854}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Sequence-1235779689-3693430.anonTask-1235779689-5987711': {'task_code': 0, 'task_end': 1235779693.1136031}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Sequence-1235779689-3693430.anonTask-1235779693-1281600': {'task_start': 1235779693.128216}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Sequence-1235779689-3693430.anonTask-1235779693-1281600': {'task_code': 0, 'task_end': 1235779693.134012}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Sequence-1235779689-3693430.anonTask-1235779693-2735910': {'task_start': 1235779693.2736449}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Sequence-1235779689-3693430.anonTask-1235779693-2735910': {'task_code': 0, 'task_end': 1235779693.2993889}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141.Sequence-1235779689-3693430': {'task_code': 0, 'task_end': 1235779693.3700669}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309.sleep-1235779689-3529141': {'task_code': 0, 'task_end': 1235779693.415879}},
        {'mon.tasks.taskmgr0.execTask-TaskManager-1235779689-3305309': {'task_code': 0, 'task_end': 1235779693.46804}},
    ]

    for i in range(1):
        for d in test_data:
            TASKS.put_nowait(d)

class TaskAppView(object):
    """This is a monitoring cmds GTK application"""

    def __init__(self, logger, usethread=True, ev_quit=None):
         
        self.logger = logger       
        #Set the Glade file
        self.wTree = gtk.glade.XML("test.glade")
        #self.wTree = gtk.glade.XML("monitor.glade")
        dic = { "gtk_main_quit" : self.destory, 
                "on_button_monitor_clicked" : self.close_clicked, 
                "on_button_clear_clicked" : self.clear_clicked,
                "on_dialog1_destroy": self.close_dialog }
                #"on_treeview_monitor_row_expanded" : self.row_expanded}
        self.wTree.signal_autoconnect(dic)
       
        self.__init_treeview()  #  tree initializatiojn 

    def __init_treeview(self):
        
        self.logger.debug('TaskAppView __init_treeview called')
        treeview = self.wTree.get_widget("treeview_monitor")
        
        #self.treelist = gtk.ListStore(str)
        self.treelist = gtk.TreeStore(str, str, str, str, str)
        treeview.set_model(self.treelist)
    
        # colunm labels 
        for (col,num) in [('task', 0), ('status',1), ('start time',2), ('end time',3), ('cmd desc',4)]:
            treeview.append_column(gtk.TreeViewColumn(col, gtk.CellRendererText(), markup=num))

        # Allow drag and drop reordering of rows
        #treeview.set_reorderable(True)

    def clear_clicked(self, obj):
        print 'clear clicked'
        self.treelist.clear()

    def close_clicked(self, obj):
        gtk.main_quit() 
  
    def destory(self, obj):
        gtk.main_quit()

    def close_dialog(self,obj):
        print 'DIALOG'
        gtk.main_quit()


            
class TreeView(object):
    def __init__(self, logger, usethread=True, ev_quit=None):
        
        self.logger = logger
        self.task_view = TaskAppView(logger)
        
        self.usethread = usethread
       
        if not ev_quit:
            self.ev_quit = threading.Event()
        else:
            self.ev_quit = ev_quit
          
        self.__set_task_level()
        
        self.lock = threading.RLock()


    def __set_task_level(self):
        
        #self.seq = re.compile(r"Sequence")
        #self.con = re.compile(r"Concurrent")
        #self.ano = re.compile(r"anonTask")
    
        TASK_ID="mon.tasks.taskmgr[0-9]+\.execTask-TaskManager-[0-9]{10}-[0-9]{7}"
        CMD_ID="\.[a-zA-Z0-9_-]+[0-9]{10}-[0-9]{7}"

#        t_dict={'TASK_ID':"mon.tasks.taskmgr[0-9]+\.execTask-TaskManager-[0-9]{10}-[0-9]{7}",
#                'CMD_ID':"\.[a-zA-Z0-9_-]+[0-9]{10}-[0-9]{7}"}
#
#        for k, n in [(L1_KEY,1),(L1_KEY,1),(L2_KEY,2),(L3_KEY,3),(L4_KEY,4),(L5_KEY,5),(L6_KEY,6),(L7_KEY,7),(L8_KEY,8)]:
#            cmds="%(CMD_ID)s"*n % t_dict
#            k = re.compile(r"\A%s%s\Z" %(TASK_ID, cmds))

        ''' top level task ''' 
        L0_TASK_KEY=re.compile(r"\A%s\Z" %(TASK_ID))
        
        ''' sk or dd or function level;  Q  how many levels are needed????  '''  
        L1_TASK_KEY=re.compile(r"\A%s%s\Z" %(TASK_ID, CMD_ID))
        L2_TASK_KEY=re.compile(r"\A%s%s%s\Z" %(TASK_ID, CMD_ID, CMD_ID))
        L3_TASK_KEY=re.compile(r"\A%s%s%s%s\Z" %(TASK_ID, CMD_ID, CMD_ID, CMD_ID))
        L4_TASK_KEY=re.compile(r"\A%s%s%s%s%s\Z" %(TASK_ID, CMD_ID, CMD_ID, CMD_ID, CMD_ID))
        L5_TASK_KEY=re.compile(r"\A%s%s%s%s%s%s\Z" %(TASK_ID, CMD_ID, CMD_ID, CMD_ID, CMD_ID, CMD_ID ))
        L6_TASK_KEY=re.compile(r"\A%s%s%s%s%s%s%s\Z" %(TASK_ID, CMD_ID, CMD_ID, CMD_ID, CMD_ID, CMD_ID, CMD_ID))
        L7_TASK_KEY=re.compile(r"\A%s%s%s%s%s%s%s%s\Z" %(TASK_ID, CMD_ID, CMD_ID, CMD_ID, CMD_ID, CMD_ID, CMD_ID, CMD_ID))
        L8_TASK_KEY=re.compile(r"\A%s%s%s%s%s%s%s%s%s\Z" %(TASK_ID, CMD_ID, CMD_ID, CMD_ID, CMD_ID, CMD_ID, CMD_ID, CMD_ID, CMD_ID))


        L1_list={}
        L2_list={}  
        L3_list={}
        L4_list={}
        L5_list={}
        L6_list={}  
        L7_list={}
        L8_list={}
         
        # the set of tree levels and their key formats
        self.task_set={5:(L1_list, L1_TASK_KEY), 6:(L2_list, L2_TASK_KEY), 
                       7:(L3_list, L3_TASK_KEY), 8:(L4_list, L4_TASK_KEY),
                       9:(L5_list, L5_TASK_KEY), 10:(L6_list, L6_TASK_KEY),
                       11:(L7_list, L7_TASK_KEY),12:(L8_list, L8_TASK_KEY) } 

 

    def start_updating(self):
        if self.usethread:
            self.logger.debug('Tree View update_task starting')
            update_task_thread=threading.Thread(target=self.update_task)
            update_task_thread.start()
        else:
            self.update_task()
 
    def stop_updating(self):
        '''Stop updating monitor'''
        self.ev_quit.set()
        
#    def _get_localtime(self, sec):
#        (year,mon,day,hour,min,sec,week,days,flag)=time.localtime(sec)
#        #"%s:%s.%s %s-%s-%s" %(hour,min,sec,mon,day,year)
#        return "%02d:%02d:%02d" %(int(hour),int(min),int(sec))

    def _convTime(self, val):
        ms = int((val - int(val)) * 1000.0)
        s = time.strftime("%H:%M:%S", time.localtime(val))
        return "%s.%03.3d" % (s, ms)


    def _check_task_code(self, code):
        
        if code==0:
            return 'Pau:%d' %(code)
        else:            
            return '<span background="red">Error:%d</span>' %(code)
             
    def _get_tree(self, task_key, task_list):
        try:
            t_key='.'.join(task_key.split('.')[:-1])   # parent tree key
            tree_level=task_list[t_key]['tree']        # parent tree 
            return tree_level
        except:
            return None 
     
    def _get_task_name(self, task_key):
        unix_time=-19  # take out "-1235779689-3529141" from task key
        try:
            t_key='.'.join(task_key.split('.')[-1:]) # Level key (sk or dd)
            task_name = t_key[:unix_time]  # name of cmd(sk or dd), chop off unix time
            return task_name
        except:
            print ''
     
    def _get_tcs_cmdinfo(self, tree, task_status, cmd_kind, column):
        try:
            cmd_info =task_status[cmd_kind]
            print "CMD INFO <%s>" %(cmd_info)
            self.task_view.treelist.set(tree, column, cmd_info)
            #self.task_view.treelist.append(tree, [cmd_info, None, None, None, None])
        except:
            pass
     
            
    def _display_tree(self, task_key, task_status, task_list, task_name, tree=None):
         
        print 'DISPLAY TREE CALLED'      
        if not task_list.has_key(task_key):
            status_dict={'tree':None}
   
            s_time= self._convTime(task_status['task_start']) 
            status = '<span background="green">started</span>'
            self.logger.debug("Tree View  _display_tree task_name<%s> status<%s>  start_time<%s>" %(task_name, status, s_time))
            try:
                newtree=self.task_view.treelist.prepend(tree, [task_name, status, s_time, None, None] )
            except:
                print "PREPENDING ERROR<%s>" %(task_name)
                pass  
            status_dict['tree']=newtree
            task_list[task_key]=status_dict
            print "SET NEW LIST<%s>" %(task_list)
            self.logger.debug("Tree View  _display_tree task_list<%s>" %(task_list))
            
        else:
            tree = task_list[task_key]['tree']
            #try:
            self._get_tcs_cmdinfo(tree, task_status, 'cmd_str', 0)
            self._get_tcs_cmdinfo(tree, task_status, 'cmd_desc', 4)
                
            #    cmd_str = task_status['cmd_str']
            #     self.task_view.treelist.set(tree, 0, cmd_str)
            #except:
            #    pass    
            
            end_time=self._convTime(task_status['task_end'])
            status=self._check_task_code(task_status['task_code'])
            self.logger.debug("Tree View  _display_tree task key found end_time<%s> status<%s>" %(end_time, status))
            
            self.task_view.treelist.set(tree, 1, status)    # 1 is a column number
            self.task_view.treelist.set(tree, 3, end_time)  # 3 is a column number
            print "DELETING LIST<%s>" %(task_list)
            del task_list[task_key]
            print "DELETED LIST<%s>" %(task_list)
             
        
          
    def _set_task_status(self, task_key, task_status):
        
        
        try:
            num=int(len(task_key.split('.')))
            self.logger.debug("Tree View  _set_task_status task_key<%s>  split_num<%d>" %(task_key, num))
            l_list, t_key=self.task_set[num]
            self.logger.debug("Tree View  _set_task_status L-list<%s>  task_key<%s>" %(l_list, t_key))
            try:
                pre_list, pre_key=self.task_set[num-1]
            except:
                pre_list=None
                
            #if t_key.match(task_key):
            l_tree=self._get_tree(task_key, pre_list)
            l_name=self._get_task_name(task_key)
            self.logger.debug("Tree View  _set_task_status task_key matched l_tree<%s>  l_name<%s>" %(l_tree, l_name))
            self._display_tree(task_key, task_status, l_list, l_name, l_tree)
                #task_set[num]=(l_list, l_list)
            
        except:
            pass     
    
        print 'RELEASING *************'
        #self.lock.release()

        
    def _search_keyword(self,task):
        
        for task_key, task_status in task.items():
            self._set_task_status(task_key, task_status)
            break
                       
#            if self.seq.search(task_key) or self.con.search(task_key) or self.ano.search(task_key):
#                pass
#            else:
#                self._set_task_status(task_key, task_status)
           
                
 
    def update_task(self):
        
        while not self.ev_quit.isSet():
            try:
                task=TASKS.get(block=True, timeout=0.001)
                print 'QUE GET <%s>' %(task)
                print 'LOCKING   *************'
                #self.lock.acquire()
                print 'ACQUIRED  *************'
                self._search_keyword(task)  
                print 'RELEASED  *************'
                    
            except:
                pass
      

class Make_cb(object):

    def __init__(self, **kwdargs):
        self.__dict__.update(kwdargs)
 
    # this one is called if new data becomes available
    def anon_arr(self, valDict, name, channels):
        TASKS.put_nowait(valDict)
        print "CALL BACK <%s>" %(valDict)
         
     

def stop_service(task_view, mymon):
    if not mymon==None:
        mymon.stop_server(wait=True)
        mymon.stop(wait=True)
    task_view.stop_updating()
        

def main(options, args):
    logger = ssdlog.make_logger('test', options)
      
    print "mode<%s>" %(options.mode) 
      
    if not options.mode == 'test':
 
        ro.init()
        # make a name for our monitor
   
        #myMonName = ('testmon-%d' % os.getpid())
        myMonName = ('testmon')
        # monitor channels we are interested in
        channels = options.channels.split(',')

        # Create a local monitor
        mymon = Monitor.Monitor(myMonName, logger, numthreads=4)

        # Startup monitor threadpool
        mymon.start(wait=True)
        # start_server is necessary if we are subscribing, but not if only
        # publishing
        mymon.start_server(wait=True)

        # Make our callback functions
        m = Make_cb(logger=logger, monitor=mymon)
   
        # Subscribe our callback functions to the local monitor
        mymon.subscribe_cb(m.anon_arr, channels)
        
        try:
            # subscribe our monitor to the central monitor hub
            monitor = ro.remoteObjectProxy(options.monitor)
            monitor.subscribe(myMonName, channels, ())
        except:
            logger.error("subscribe to the central monitor faild")
   
    else:
        feed_test_data()
        mymon=None
    
    try:
        
        gtk.gdk.threads_init()
        task_view =  TreeView(logger)
        task_view.start_updating()
        gtk.main()
        stop_service(task_view, mymon=mymon)
        print 'GUI END'

    except KeyboardInterrupt:
        #gtk.main_quit() 
        stop_service(task_view, mymon=mymon)
        
   
if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options] command [args]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-c", "--channels", dest="channels", default='',
                      metavar="LIST",
                      help="Subscribe to the comma-separated LIST of channels")
    optprs.add_option("-m", "--monitor", dest="monitor", default='monitor',
                      metavar="NAME",
                      help="Subscribe to feeds from monitor service NAME")
    optprs.add_option("--mode", dest="mode", metavar="MODE",
                     help="Test mode")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

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

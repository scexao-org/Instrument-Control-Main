#! /usr/bin/env python

import sys
import os
import threading
import pprint
import time
import Queue
import re

import remoteObjects as ro
import remoteObjects.Monitor as Monitor
import ssdlog

from PyQt4 import QtCore, QtGui

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

    for d in test_data:
        TASKS.put_nowait(d)


# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mon.ui'
#
# Created: Wed Apr 15 09:51:14 2009
#      by: PyQt4 UI code generator 4.3.3
#
# WARNING! All changes made in this file will be lost!


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(QtCore.QSize(QtCore.QRect(0,0,702,549).size()).expandedTo(Form.minimumSizeHint()))

        self.treeWidget = QtGui.QTreeWidget(Form)
        self.treeWidget.setGeometry(QtCore.QRect(40,20,611,451))

        font = QtGui.QFont()
        font.setPointSize(9)
        self.treeWidget.setFont(font)
        self.treeWidget.setFrameShape(QtGui.QFrame.VLine)
        self.treeWidget.setObjectName("treeWidget")

        self.pushButtonClose = QtGui.QPushButton(Form)
        self.pushButtonClose.setGeometry(QtCore.QRect(570,500,80,28))
        self.pushButtonClose.setObjectName("pushButtonClose")

        self.pushButtonClear = QtGui.QPushButton(Form)
        self.pushButtonClear.setGeometry(QtCore.QRect(450,500,80,28))
        self.pushButtonClear.setObjectName("pushButtonClear")

        self.retranslateUi(Form)
        QtCore.QObject.connect(self.pushButtonClose,QtCore.SIGNAL("clicked()"),Form.close)
        QtCore.QObject.connect(self.pushButtonClear,QtCore.SIGNAL("clicked()"),self.treeWidget.clear)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtGui.QApplication.translate("Form", "Task Monitor", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(0,QtGui.QApplication.translate("Form", "task", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(1,QtGui.QApplication.translate("Form", "status", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(2,QtGui.QApplication.translate("Form", "start time", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(3,QtGui.QApplication.translate("Form", "end time", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButtonClose.setText(QtGui.QApplication.translate("Form", "close", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButtonClear.setText(QtGui.QApplication.translate("Form", "clear all", None, QtGui.QApplication.UnicodeUTF8))


class TreeView(QtGui.QMainWindow):
    def __init__(self, parent=None, usethread=True, ev_quit=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
     
        self.usethread = usethread
       
        if not ev_quit:
            self.ev_quit = threading.Event()
        else:
            self.ev_quit = ev_quit
          
        #self.__set_task_level()   


        
#        red=QtGui.QColor('red')
#        green=QtGui.QColor('green')
#        
#        a = QtGui.QTreeWidgetItem(self.ui.treeWidget, ['hahah','eeee','6666'])
#        b = QtGui.QTreeWidgetItem(self.ui.treeWidget, ['fffff'])
#        aa = QtGui.QTreeWidgetItem(self.ui.treeWidget, ['insert'])
#        
#        self.ui.treeWidget.addTopLevelItems([a,b])
#        self.ui.treeWidget.addTopLevelItem(aa)
#        #a.append(0, 'fffff')
#        c= QtGui.QTreeWidgetItem(a,['ccc'] )
#        a.addChild(c)
#        c.setText(3,'BBBBBBBB')
#        c.setBackgroundColor(3, QtGui.QColor('red'))
#        c.setTextColor(0, red)
#        a.setText(3, 'MMMMM')
#        g= QtGui.QTreeWidgetItem(c,['GGGGG'] )
#        g.setTextColor(0, green)
#        d= QtGui.QTreeWidgetItem(b,['kkkkk','hhhhh','kkkkk'] )
#        b.addChild(d)


        self.__set_task_level()   

    def __set_task_level(self):
        
        self.seq = re.compile(r"Sequence")
        self.con = re.compile(r"Concurrent")
        self.ano = re.compile(r"anonTask")
        
        id_dict={'TASK_ID':"mon.tasks.taskmgr[0-9]+\.execTask-TaskManager-[0-9]{10}-[0-9]{7}",
                 'CMD_ID':"\.[a-zA-Z0-9_-]+[0-9]{10}-[0-9]{7}"}
        TASK_ID="mon.tasks.taskmgr[0-9]+\.execTask-TaskManager-[0-9]{10}-[0-9]{7}"
        CMD_ID="\.[a-zA-Z0-9_-]+[0-9]{10}-[0-9]{7}"

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
    
    def _get_localtime(self, sec):
        (year,mon,day,hour,min,sec,week,days,flag)=time.localtime(sec)
        return "%02d:%02d:%02d" %(int(hour),int(min),int(sec))

    def _get_task_name(self, task_key):
        unix_time=-19  # take out "-1235779689-3529141" from task key
        try:
            t_key='.'.join(task_key.split('.')[-1:]) # Level key (sk or dd)
            task_name = t_key[:unix_time]  # name of cmd(sk or dd), chop off unix time
            return task_name
        except:
            print ''

    def _get_tree(self, task_key, task_list):
        try:
            t_key='.'.join(task_key.split('.')[:-1])   # parent tree key
            tree_level=task_list[t_key]['tree']        # parent tree 
            return tree_level
        except:
            return None 

    def _check_task_code(self, code):
        
        if code==0:
            return 'Pau:%d' %(code)
        else:            
            return 'Error:%d' %(code)

    def _display_tree(self, task_key, task_status, task_list, task_name, tree=None):
        
        print '_display tree called list<%s>' %(tree)
        if not task_list.has_key(task_key):
            status_dict={'tree':None}
   
            s_time= self._get_localtime(task_status['task_start']) 
            
            
            #status = '<span background="green">started</span>'
            print task_name, s_time
            
            green=QtGui.QColor('green')
            
            if tree == None:
                print 'TREEEEE  NNNNNNNOOOONNNEEEE'
                new_entry = QtGui.QTreeWidgetItem(self.ui.treeWidget, [task_name, 'started', s_time])
                self.ui.treeWidget.addTopLevelItem(new_entry)
            else:
                print 'TREEEEE  YEESSSSSS'
                
                
                new_entry= QtGui.QTreeWidgetItem(tree,[task_name, 'started', s_time] )
                tree.addChild(new_entry)
                
            new_entry.setTextColor(1, green)
            
            status_dict['tree']=new_entry
            task_list[task_key]=status_dict

            print 'L_list<%s>' %(task_list)
        else:
            red=QtGui.QColor('red')
            gray=QtGui.QColor('gray')
            print 'there is a key'
            end_time=self._get_localtime(task_status['task_end'])
            status=self._check_task_code(task_status['task_code'])
            tree = task_list[task_key]['tree']
            tree.setText(1, status)
            tree.setText(3, end_time)
            if status.startswith('Error'):
                tree.setTextColor(1, red)
            else:
                tree.setTextColor(1, gray)
            #self.task_view.treelist.set(tree, 1, status)
            #self.task_view.treelist.set(tree, 3, end_time)
            del task_list[task_key]


    def _set_task_status(self, task_key, task_status):

        try:
            
            num=int(len(task_key.split('.')))
            print "NUM<%d>" %(num)
            l_list, t_key=self.task_set[num]
            print "GEEETTTL-list%s> Key<%s>" %(l_list, t_key)
            try:
                parent_list, parent_key=self.task_set[num-1]
            except:
                parent_list=None
                
            if t_key.match(task_key):
                print 'KEY MATCHED'
                l_tree=self._get_tree(task_key, parent_list)
                l_name=self._get_task_name(task_key)
                print l_tree, l_name
                self._display_tree(task_key, task_status, l_list, l_name, l_tree)
                            
        except:
            pass     



        
    def start_updating(self):
        if self.usethread:
            update_tree_thread=threading.Thread(target=self.update_tree)
            update_tree_thread.start()
        else:
            self.update_tree()
 
    def stop_updating(self):
        '''Stop updating monitor'''
        self.ev_quit.set()

    def _search_keyword(self,task):
        
        for task_key, task_status in task.items():
            #if SEQ.search(task_key) or CON.search(task_key) or ANO.search(task_key):
            if self.seq.search(task_key) or self.con.search(task_key) or self.ano.search(task_key):
                pass
            else:
                self._set_task_status(task_key, task_status)
 
    def update_tree(self):
              
        while not self.ev_quit.isSet():
            try:
                task=TASKS.get(block=True, timeout=0.01)
                #print task
                self._search_keyword(task)
            except:
                pass  
     
     
        # set the widths of the columns
	
        #self.ui.treeWidget.setColumnWidth()
	#self.ui.treeWidget.setColumnWidth(1,100)
        

        
        #c.insertChildren(0,a)
        #bb=a.setText(0, 'a')
        #a.setText(1, 'b')
        #a.append(0,'aaaa')
        #a.setText(2, 'c')
        #a.setText(0, 'aaaaaaa')

        #QtGui.treeWidgetItem.setText(1, 'sleep')

class Make_cb(object):

    def __init__(self, **kwdargs):
        self.__dict__.update(kwdargs)
       
    # this one is called if new data becomes available
    def anon_arr(self, valDict, name, channels):
               
        if len(valDict):
            self.logger.info("\nRECEIVED")
            #print 'DDD <%s>' %(valDict)
            TASKS.put_nowait(valDict)
        else:
            self.logger.info("\nRECEIVED VAL EMMMMPTY\n")
        print 'EEEEEEEEEEEEEEEEEEEEE'
        

def stop_service(tv, mymon):
    if not mymon==None:
        mymon.stop_server(wait=True)
        mymon.stop(wait=True)
    tv.stop_updating()

def main(options, args):
    logger = ssdlog.make_logger('test', options)
  
    if options.mode == 'test':
        print 'test mode'
        feed_test_data()
        mymon=None
      
    else:
 
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

    
    try:
        
        app = QtGui.QApplication(sys.argv)
        tv = TreeView()
        tv.start_updating()
        tv.show()
        sys.exit(app.exec_())
        stop_service(tv, mymon=mymon)
        print 'GUI END'

    except KeyboardInterrupt:
        print 'Keyboard'
        #gtk.main_quit() 
        stop_service(tv, mymon=mymon)


if __name__ == "__main__":
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
    
    
    
    




      

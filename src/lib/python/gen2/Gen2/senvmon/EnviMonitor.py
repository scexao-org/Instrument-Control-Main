#!/usr/bin/env python
#
# Sam Streeper
# Takeshi Inagaki (tinagaki@naoj.org)
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Apr 30 13:11:35 HST 2012
#]
#

from __future__ import division

from timeValueGraph import *
from statusGraph import *
import resourceMon as rmon
import direction as dr
import ssdlog
import remoteObjects as ro
import remoteObjects.Monitor as Monitor

def init_status():
    ''' init status ''' 
    status = ro.remoteObjectProxy('status')  
    stat_dict={"TSCL.WINDD":None, "TSCL.WINDS_O":None, "TSCL.WINDS_I":None, "TSCL.TEMP_O":None, "TSCL.TEMP_I":None, "TSCL.HUMI_O":None, "TSCL.HUMI_I":None, "TSCL.ATOM":None, "TSCL.RAIN":None, "TSCL.SEEN":None, "VGWD.FWHM.AG":None, "TSCV.WATER":None, "TSCV.OIL":None, "TSCS.AZ":None}

    return status.fetch(stat_dict)


def __set_data(envi_data, key, logger):

    try:
        Global.persistentData=envi_data[key]
        #print 'GETDATA:%d' % len(Global.persistentData['temperature'][0])
        #print 'GETDATA:%s' % Global.persistentData 
        logger.debug('getting data for key %s' %key)
        #print envi_data[key_str]
    except KeyError,e:
        Global.persistentData = {}
        logger.debug('getting data for no key')


def __restore_data(envi_data, key, logger):
    try:
        envi_data[key]=Global.persistentData
    except Exception,e:
        logger.warn('no key found...  %s' %e)


def load_data(envi_file,  key, datapoint, logger):
    ''' loading data '''

    # open/load shelve file 
    try:
        logger.debug('opening env data...')   
        envi_data = shelve.open(envi_file)

        __set_data(envi_data, key, logger)  

        __remove_old_data(datapoint, logger)

        __restore_data(envi_data, key,logger)
 
        envi_data.close()
  
    except IOError,e:
        logger.warn('warn  opening envi_data %s' %str(e))
        Global.persistentData = {}
        #envi_data.close()

def __remove_old_data(datapoint, logger):
 
    for k in Global.persistentData.keys():
         logger.debug('removing key=%s' %k)
         for val in range(len(Global.persistentData[k])):
              num_points=len(Global.persistentData[k][val])

              logger.debug('length of datapoint=%d' %num_points )
              if num_points  >  datapoint:
                  del Global.persistentData[k][val][:num_points-datapoint]     
                  #logger.debug('after  deleting datapoint=%s' % Global.persistentData[k][val])
                  logger.debug('length of datapoint=%d' %len(Global.persistentData[k][val]) )

class Make_cb(object):

    def __init__(self, **kwdargs):
        self.__dict__.update(kwdargs)
        self.lock = threading.RLock()
        self.pretime=0
        
        # define callback functions for the monitor

    # this one is called if new data becomes available
    def anon_arr(self, payload, name, channels):
        #recvtime = time.time()         

        try:
            bnch = Monitor.unpack_payload(payload)
            
            if self.monpath and (not bnch.path.startswith(self.monpath)):
                return
            try: 
                # update status values as soon as they are changed  
                self.stat_val.update((k,bnch.value[k]) for k in self.stat_val.keys() if k in bnch.value)

                self.coordinator.stat_dict=self.stat_val

                self.logger.debug('stat val  %s' %self.stat_val)
                
            except Exception, e:
                self.logger.error('status updating error %s' %e)
                return 

        except Monitor.MonitorError:
            return


#        with self.lock:
#            try:
#                assert (recvtime-self.pretime) < self.interval
#                self.logger.debug('%f < %d ' %((recvtime-self.pretime), self.interval))
#                return 
#            except Exception,e:
#                self.logger.debug('%f > %d' %((recvtime-self.pretime), self.interval))
#                self.pretime=recvtime
                
#                self.coordinator.update_status(self.stat_val)
                #self.logger.debug('updated stat_vals  %s' %str(self.stat_val))

#        self.logger.debug('unlocked ... ')
#        return 



#################################################################
### =================  main() starts here =======================
#################################################################
def main(options, args):
  
    # Create top level logger.
    logger = ssdlog.make_logger('EnviMonitor', options)

    # init remote object
    ro.init()

    # init status 
    stat_val=init_status()

    try:
        envi_file=os.path.join(os.environ['GEN2COMMON'], 'db', 'envi.shelve')  
    except OSError,e:
        envi_file=='/gen2/share/db/envi.shelve' 

    key='envi_key'

    load_data(envi_file, key, options.datapoint, logger)

    # setGraphicsSystem makes the anti-aliased fonts look nice when
    # the application is run inside a VNC. setGraphicsSystem is not
    # really necessary when the application is not inside a VNC, but
    # causes no harm, so it is invoked whether or not the application
    # is running inside a VNC.
    QApplication.setGraphicsSystem('raster')

    global_font=QFont("Helvetica", 8, QFont.Bold)
    #global_font=QFont("lucida", 8, 10, QFont.Bold)
    global_font=QFont("Arial", 10, QFont.Bold)
    QApplication.setFont(global_font)    
    app = QApplication(sys.argv)

    root = QWidget()
    layout = QVBoxLayout()
    layout.setContentsMargins(4, 4, 4, 4)
    layout.setSpacing(8)
    root.setLayout(layout)
    root.setWindowTitle(root.tr("Environment Monitor"))
    
    coordinator = TVCoordinator(stat_val, options.minute, envi_file, key, logger)
    
    # wind direction 
    widget = StatusGraph(title="Wind direction N:0 E:90",
                         key="winddir",
                         size=(430,200),
                         statusKeys=("TSCL.WINDD",),
                         maxDeltas=(300,),
                         backgroundColor=QColor(245,255,252),
                         logger=logger)
    # don't crop/scale the compass values to the wind data
    widget.hardMinDisplayVal = -0.1
    widget.hardMaxDisplayVal = 370
    widget.valueRuler.marksPerUnit = 1
    widget.valueRuler.hardValueIncrement = 90
    coordinator.addGraph(widget)
    layout.addWidget(widget, stretch=1)
    
    # wind speed
    widget = StatusGraph(title="Wind Speed (m/s)",
                         key="windspeed",
                         size=(430,120),
                         statusKeys=("TSCL.WINDS_O", "TSCL.WINDS_I"),
                         alarmValues = (10,15),
                         backgroundColor=QColor(247,255,244),                   
                         displayTime=True,
                         logger=logger)
    coordinator.addGraph(widget)
    layout.addWidget(widget, stretch=1)

    # temperature
    widget = StatusGraph(title="Temperature (C)",
                         key="temperature",
                         statusKeys=("TSCL.TEMP_O", "TSCL.TEMP_I"),
                         #statusObj=status_obj,
                         logger=logger)
    coordinator.addGraph(widget)
    layout.addWidget(widget, stretch=1)

    # humidity
    widget = StatusGraph(title="Humidity (%)",
                         key="humidity",
                         statusKeys=("TSCL.HUMI_O", "TSCL.HUMI_I"),
                         alarmValues = (80,80),
                         warningValues = (70,70),
                         backgroundColor=QColor(255,255,246),
                         size=(430,112),
                         displayTime=True,
                         logger=logger)
    coordinator.addGraph(widget)
    layout.addWidget(widget, stretch=1)
    
    # air pressure
    widget = StatusGraph(title="Air Pressure (hPa)",
                         key="airpressure",
                         #size=(430,97),
                         size=(430,150),
                         statusKeys=("TSCL.ATOM",),
                         statusFormats=("%0.1f",),
                         logger=logger)
    coordinator.addGraph(widget)
    layout.addWidget(widget, stretch=1)

    # rain gauge
    widget = StatusGraph(title="Rain Gauge (mm/h)",
                         key="raingauge",
                         statusKeys=("TSCL.RAIN",),
                         statusFormats=("%0.1f",),
                         alarmValues = (50,),
                         #size=(430,93),
                         size=(430,150),
                         backgroundColor=QColor(244,244,244),
                         logger=logger)
    coordinator.addGraph(widget)
    layout.addWidget(widget, stretch=1)

    # seeing size
    widget = StatusGraph(title="Seeing Size (arcsec)",
                         key="seeingsize",
                         statusKeys=("TSCL.SEEN", "VGWD.FWHM.AG"),
                         alarmValues = (1,1),
                         statusFormats=("TSC: %0.1f", "VGW: %0.1f"),
                         #size=(430,97),
                         size=(430,150),
                         displayTime=True,
                         logger=logger)
    coordinator.addGraph(widget)
    layout.addWidget(widget, stretch=1)

    # resource monitor 
    rs = rmon.ResourceMonitor(statusKeys=("TSCV.WATER", "TSCV.OIL"),
                                   logger=logger)
    coordinator.graphs.append(rs)
    layout.addWidget(rs, stretch=0)
    
    # wind directon & quit buttons 
    vl=QVBoxLayout()
    buttonLayout = QHBoxLayout()

    windButton = QPushButton("Wind Direction")
    quitButton = QPushButton("&Quit") 
           
    buttonLayout.addWidget(windButton)
    buttonLayout.addStretch()
    buttonLayout.addWidget(quitButton)
    vl.addLayout(buttonLayout)
    layout.addLayout(vl)

    # wind direction 
    wd=dr.Directions(statusKeys=("TSCS.AZ", "TSCL.WINDD", "TSCL.WINDS_O"), logger=logger)

    coordinator.graphs.append(wd)
    
    def launch_wind_direction():
        wd.show()

    def quit():
        logger.debug('quitting app...')
   
        """ once all-windows are closed, 
        'def close()' is called anyway because of close-slot connection to main widget. """ 
        app.closeAllWindows() 
     
 
    def close():
        logger.debug('closing app...')
        
        if server_started:
            mymon.stop_server(wait=True)
        mymon.stop(wait=True)

        ''' remove resource/wind_direction objects. 
            no need to store those data'''
        try:
            [coordinator.graphs.remove(obj) for obj in [rs, wd]]
        except Exception,e:
            logger.debug('object is not in list %s' %e)
            pass 

        coordinator.saveDatastoresShelve()
        app.closeAllWindows()

    # this is for quit button
    QObject.connect(quitButton, SIGNAL("clicked()"), quit)
    # this is to start up wind-direction
    QObject.connect(windButton, SIGNAL("clicked()"), launch_wind_direction)
    # this is for main widget 'X' button
    QObject.connect(app, SIGNAL("lastWindowClosed()"),  close)

    #import signal
    # catch keyboard interruption
    #signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    Global.persistentData = None

    root.resize(layout.closestAcceptableSize(root, QSize(500,800)))

#    coordinator.init_time_anchored()

    # create local monitor 
    logger.debug('setting monitor')
    # make a name for our monitor
    myMonName = options.name

    # monitor channels we are interested in
    channels = options.channels.split(',')

    # Create a local monitor
    mymon = Monitor.Monitor(myMonName, logger, numthreads=20)

    # Make our callback functions
    m = Make_cb(coordinator=coordinator, stat_val=stat_val, logger=logger,
                monpath=options.monpath, history=options.history,
                interval=options.interval)

    # Subscribe our callback functions to the local monitor
    mymon.subscribe_cb(m.anon_arr, channels)
    server_started = False
    try:
        # Startup monitor threadpool
        mymon.start(wait=True)
        # start_server is necessary if we are subscribing, but not if only
        # publishing
        mymon.start_server(wait=True, port=options.port)
        server_started = True

        # subscribe our monitor to the central monitor hub
        mymon.subscribe_remote(options.monitor, channels, ())
        
        logger.debug('monitor starting ...')

        #coordinator.save_data_interval(options.minute)
  
        coordinator.runAtInterval(options.interval)
        root.show()

        app.exec_()
    except Exception,e:
        logger.error('error %s' %e)
        quit()


if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser
 
    usage = "usage: %prog [options] command [args]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--display", dest="display", metavar="HOST:N",
                      help="Use X display on HOST:N")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("-m", "--monitor", dest="monitor", default='monitor',
                      metavar="NAME",
                      help="Subscribe to feeds from monitor service NAME")
    optprs.add_option("-c", "--channels", dest="channels", default='status',
                      metavar="LIST",
                      help="Subscribe to the comma-separated LIST of channels")
    optprs.add_option("-p", "--path", dest="monpath", default=None,
                      metavar="PATH",
                      help="Show values for PATH in monitor")
    optprs.add_option("--port", dest="port", type="int", default=10013,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("-n", "--name", dest="name", default='env.mon',
                      metavar="NAME",
                      help="Use NAME as our subscriber name")
    optprs.add_option("--history", dest="history", action="store_true",
                      default=False,
                      help="Fetch history on path instead of latest elements")

    optprs.add_option("--datapoint", dest="datapoint", type='int', metavar="DATAPOINT",                      
                      default=3600,  
                      help="The number of data points to be stored")

    optprs.add_option("--minute", dest="minute", type='int', metavar="MINUTE",                      
                      default=10,
                      help="Time interval to save env-data")

    optprs.add_option("--interval", dest="interval", type='int', metavar="INTERVAL",                      
                      default=5,
                      help="Time to update EnviMon")

    ssdlog.addlogopts(optprs)
    
    (options, args) = optprs.parse_args()

    if len(args) != 0:
        optprs.error("incorrect number of arguments")

    if options.display:
        os.environ['DISPLAY'] = options.display

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

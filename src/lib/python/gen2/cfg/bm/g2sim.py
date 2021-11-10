# For compatibility mode front ends
import cfg.g2soss as g2soss
import remoteObjects as ro
from common import *

#############################################################################
# LAPTOP OR DESKTOP CONFIGURATION
# Everything runs on one machine.  Starts simulators for Telescope,
# Instrument and STARS.
#############################################################################
g2sim = Bunch()

# All managers that will be controlled by this configuration.
#
# For each instance, possible attributes are
#   host -- host this instance will run on
#   port -- port at which to bind for remoteObject (XML-RPC) calls
#   user -- user to run under
#   basedir -- base directory in which to run
#
g2sim.managers = populate(
    h1=Bunch(host=ro.get_myhost(short=True)),
    )

g2sim.frontends = ['h1']

# Displays
g2sim.disp = Bunch()
# g2sim.disp.s6 = '%s:6' % (host(g2sim, 'h1'))
# g2sim.disp.s5 = '%s:5' % (host(g2sim, 'h1'))
# g2sim.disp.s4 = '%s:4' % (host(g2sim, 'h1'))
# g2sim.disp.s3 = '%s:3' % (host(g2sim, 'h1'))
# g2sim.disp.s2 = '%s:2' % (host(g2sim, 'h1'))
# g2sim.disp.s1 = '%s:1' % (host(g2sim, 'h1'))

g2sim.disp.s6 = ':6'
g2sim.disp.s5 = ':5' 
g2sim.disp.s4 = ':4' 
g2sim.disp.s3 = ':3' 
g2sim.disp.s2 = ':2' 
g2sim.disp.s1 = ':1' 



g2sim.screens = g2sim.disp.keys()

# predefined groups
g2sim.hosts = g2sim.managers.keys()
g2sim.ns = ro.unique_hosts(g2sim.managers.values())

g2sim.basedir = gen2home
#g2sim.basedir = '$GEN2HOME'

g2sim.defaults = {
    'stderr':   True,
    'monitor':  'monitor',
    'loglevel': 'info',
    'logmon': False,
    'description': '[N/A]',
    }

g2sim.svconfig = {


    "mgrsvc": {                     # Name of the service
        'level': 0,                 # what level does it belong to
        'hosts': g2sim.hosts,       # which hosts can it run on
        'count': len(g2sim.hosts),  # how many instances should I start
                                    # what is the path to the executable from
                                    #the base directory
        'description': DESCR.mgrsvc,
        'cmddir': '../remoteObjects',
                                     # command to start the program 
        'start': 'remoteObjectManagerSvc.py --detach --loglevel=20 --log=%s --output=%s' % (
            get_log('ro_mgrsvc.log'), get_log('ro_mgrsvc_stdout.log')),
        'flags': ('each'),         # special notes to BootManager
        },

    "names": {
        'level': 1,
        'hosts': g2sim.hosts,
        'count': len(g2sim.hosts),
        'description': DESCR.names,
        'cmddir': '../remoteObjects',
        'start': 'remoteObjectNameSvc.py --monport=7077 --monauth=monitor:monitor --monitor=g2s2:7077 --loglevel=info --log=%(log)s',
        'log'  : get_log('ro_names.log'),
        'flags': ('each'),
        },

    "monitor": {
        'level': 2,
        'hosts': g2sim.hosts,
        'count': 1,
        'description': DESCR.monitor,
        'cmddir': '../remoteObjects',
        'start': 'PubSub.py --port=7080 --svcname=monitor --config=cfg.pubsub --loglevel=info --log=%(log)s',
        'log'  : get_log('monitor.log'),
        'flags': ('random'),
        },

    # Star Catalogs
    "starcat": {
        'level': 1.5,
        'hosts': g2sim.hosts,
        'count': 1,
        'description': DESCR.starcat,
        'rundir': '%s' % (starcatdir()),
        'start': '/usr/lib/postgresql/8.4/bin/postgres -p 5436 -D %s/8_4db' % (starcatdir()),
        'stop': '/usr/lib/postgresql/8.4/bin/pg_ctl stop -D %s/8_4db -m fast' % (starcatdir()),
        'stdout': get_log('starcat.log'),
        'flags': ('fixed', 'nosvccheck'),
        },

    "starcat1": {
        'level': 1.5,
        'hosts': g2sim.hosts,
        'count': 1,
        'description': DESCR.starcat,
        'rundir': '%s' % (starcatdir()),
        'start': '/usr/lib/postgresql/8.4/bin/postgres -p 5433 -D %s/8_4db1' % (starcatdir()),
        'stop': '/usr/lib/postgresql/8.4/bin/pg_ctl stop -D %s/8_4db1 -m fast' % (starcatdir()),
        'stdout': get_log('starcat1.log'),
        'flags': ('fixed', 'nosvccheck'),
        },

    "starcat2": {
        'level': 1.5,
        'hosts': g2sim.hosts,
        'count': 1,
        'description': DESCR.starcat,
        'rundir': '%s' % (starcatdir()),
        'start': '/usr/lib/postgresql/8.4/bin/postgres -p 5434 -D %s/8_4db2' % (starcatdir()),
        'stop': '/usr/lib/postgresql/8.4/bin/pg_ctl stop -D %s/8_4db2 -m fast' % (starcatdir()),
        'stdout': get_log('starcat2.log'),
        'flags': ('fixed', 'nosvccheck'),
        },
    
    "starcat3": {
        'level': 1.5,
        'hosts': g2sim.hosts,
        'count': 1,
        'description': DESCR.starcat,
        'rundir': '%s' % (starcatdir()),
        'start': '/usr/lib/postgresql/8.4/bin/postgres -p 5435 -D %s/8_4db3' % (starcatdir()),
        'stop': '/usr/lib/postgresql/8.4/bin/pg_ctl stop -D %s/8_4db3 -m fast' % (starcatdir()),
        'stdout': get_log('starcat3.log'),
        'flags': ('fixed', 'nosvccheck'),
        },

    # STSradio and omsa_logger
    "STSradio": {
        'level': 1.5,
        'hosts': g2sim.hosts,
        'count': len(g2sim.hosts),
        'description': """This is the STS radio reporting software.  It reports
information to the Subaru Telemetry System.""",
        'rundir': '../tools/dell_omsa',
        'cmddir': '.',
        'start': 'STSradio_wrapper.sh %s/STSradio DellOMSA_STS.config' % g2soss.dirload,
        'flags': ('fixed', 'nosvccheck'),
        },

    "omsa_logger": {
        'level': 1.5,
        'hosts': g2sim.hosts,
        'count': len(g2sim.hosts),
        'description': """This is the Dell OMSA logging system.""",
        'cmddir': '../tools/dell_omsa',
        'start': 'omsa_logger.py',
        'stdout': get_log('omsa_logger_stdout.log'),
        'flags': ('fixed', 'nosvccheck'),
        },

    # Star Catalogs
    "starcat_pool": {
        'level': 2.5,
        'hosts': g2sim.hosts,
        'count': 1,
        'description': DESCR.starcat,
        'rundir': '%s' % (starcatdir()),
        'start': '/usr/sbin/pgpool -n -f %s/pgpool.conf' % (starcatdir()),
        'stop': '/usr/sbin/pgpool -f %s/pgpool.conf -m fast stop' % (starcatdir()),
        'stdout': get_log('starcat_pool.log'),
        'flags': ('fixed', 'nosvccheck'),
        },

    "dss_server": {
        'level': 2.5,
        'hosts': g2sim.hosts,
        'count': 1,
        'description': DESCR.dssserver,
        'cmddir': 'web',
        'start': 'dss_server.py --port=30000 --loglevel=debug --log=%(log)s',
        'log'  : get_log('dss_server.log'),
        'flags': ('fixed', 'nosvccheck'),
        },
    
    "bootmgr": {
        'level': 3,
        'hosts': g2sim.hosts,
        'count': 1,
        'description': DESCR.bootmgr,
        'cmddir': '.',
        'start': 'BootManager.py --config=g2sim --port=8090 --svcname="bootmgr" --loglevel=info --log=%(log)s',
        'log': get_log('bootmgr.log'),
        'flags': ('random'),
        },

    # This is the status server
    "status": {
        'level': 3,
        'hosts': g2sim.hosts,
        'count': 1,
        'description': DESCR.status,
        'cmddir': '../SOSS/status',
        'start': 'status.py --svcname=status --port=8151 --monitor=monitor --loglevel=info --log=%(log)s --checkpt=%(dbdir)s/status.cpt',
        'log'  : get_log('status.log'),
        'dbdir': dbdir(),
        'flags': ('random'),
        },

    "agsim": {
        'level': 90,
        'hosts': prefer([left(g2sim.frontends)], g2sim.frontends),
        'count': 1,
        'cmddir': '../tools',
        'start': 'agsim.py --loglevel=debug --log=%(log)s --display=%(xdisp)s',
        'log'  : get_log('agsim.log'),
        'xdisp': screen(g2sim.disp.s6),
        'flags': ('manual'),
        },


    ### sendlog and deletelog are testing phase
    "sendlog": {
        'level': 90,
        'hosts': g2sim.hosts,
        'count': len(g2sim.hosts),
        'cmddir': '../tools',
        'start': 'send_log.py',
        'periodic': calc_future(86400, hr=9),
        'stdout': get_log('sendlog.log'),
        'flags': ('fixed'),
        },
    
    "deletelog": {
        'level': 90,
        'hosts': g2sim.hosts,
        'count': len(g2sim.hosts),
        'cmddir': '../tools',
        'start': 'delete_log.py --age=15',
        'periodic': calc_future(1296000, hr=11),
        'stdout': get_log('deletelog.log'),
        'flags': ('fixed'),
        },
    ############################################ 

    "test": {
        'level': 90,
        'hosts': g2sim.hosts,
        'count': len(g2sim.hosts),
        #'cmddir': '.',
        'start': '/bin/echo `date`',
        'periodic': calc_future(604800, hr=10),
        'stdout': get_log('test.log'),
        'flags': ('fixed'),
        },

    "sessions": {
        'level': 4,
        'hosts': g2sim.hosts,
        'count': 1,
        'description': DESCR.sessions,
        'cmddir': '.',
        'start': 'SessionManager.py --port=8105 --svcname="sessions" --db=%(dbdir)s/sessiondb-g2sim --loglevel=info --log=%(log)s',
        'log'  : get_log('sessions.log'),
        'dbdir': dbdir(),
        'flags': ('random'),
        },
    
    # This is the frame service interface
    "frames": {
        'level': 4,
        'hosts': g2sim.hosts,
        'count': 1,
        'description': DESCR.frames,
        'cmddir': '.',
        'start': 'frameSvc.py --server --port=8161 --monport=15161 --svcname="frames" --monitor=monitor --loglevel=info --log=%(log)s',
        'log'  : get_log('frames.log'),
        'flags': ('random'),
        },

    # This is the alarm_handler, which monitors and reports alarms
    # from the incoming TSC feed.
    "alarm_handler": {
        'level': 4,
        'hosts': g2sim.hosts,
        'count': 1,
#        'description': DESCR.alarm_handler,
        'cmddir': 'alarm',
        'start': 'alarm_handler.py --configfile "../cfg/alarm/*_alarm_cfg.yml" --log=%(log)s --loglevel=info',
        'log'  : get_log('alarm_handler.log'),
        'stdout': get_log('alarm_handler_stdout.log'),
        'flags': ('random'),
        },

    "taskmgr0": {
        'level': 5,
        'hosts': g2sim.hosts,
        'count': 1,
        'description': DESCR.taskmgr,
        'cmddir': '.',
        'start': 'TaskManager.py --port=8170 --svcname="taskmgr0" --db=taskmgrdb-g2sim  --monitor=monitor --session=main --numthreads=100 --loglevel=info --stderr --log=%(log_d)s:debug',
        'stdout': get_log('taskmgr0.log'),
        'log_d': get_log('taskmgr0_debug.log'),
        'flags': ('random'),
        },

    "soundsink": {
        'level': 5,
        'hosts': g2sim.hosts,
        'count': 1,
        'cmddir': '.',
        'description': "Sound drop off point for distributing audio",
        'start': 'soundsink.py --monitor=monitor --svcname=sound --port=15051 --monport=15052 --loglevel=info --log=%(log)s',
        'log'  : get_log('soundsink.log'),
        'flags': ('random'),
        },

    # This is the DAQ equivalent for Gen2 (compatibility mode)
    "archiver": {
        'level': 5,
        'hosts': g2sim.hosts,
        'count': 1,
        'description': DESCR.archiver,
        'cmddir': '.',
        'start': 'Archiver.py --monitor=monitor --svcname=archiver --port=8104 --monport=15104 --server --realm=other --loglevel=info --log=%(log)s',
        'log'  : get_log('archiver.log'),
        'flags': ('random', 'nosvccheck'),
        },

    "gen2base": {
        'level': 5,
        'hosts': g2sim.hosts,
        'count': 1,
        'cmddir': '.',
        'description': DESCR.archiver,
        'start': 'Archiver.py --monitor=monitor --svcname=gen2base --realm=base --port=8106 --monport=15106 --server --keyfile=%(key)s --datadir=/gen2/data/BASE --pullmethod=copy --loglevel=info --log=%(log)s',
        'key'  : get_key('gen2base'),
        'log'  : get_log('gen2base.log'),
        'flags': ('prefer'),
        },

     # This is the STARS interface
    "STARS": {
        'level': 5,
        'hosts': g2sim.hosts,
        'count': 1,
        'description': DESCR.STARSint,
        'cmddir': '../SOSS/STARSint',
        'start': 'STARSint.py --monitor=monitor --channels=7,8 --svcname=STARS --starshost=localhost --port=8121  --keyfile=%(key)s --loglevel=debug --log=%(log)s',
        'key'  : get_key('stars'),
        'log'  : get_log('STARS.log'),

        'flags': ('random'),
        },

    # This is the STARS simulator (s01)
    "STARSsim": {
        'level': 7,
        'hosts': g2sim.hosts,
        'count': 1,
        'description': DESCR.STARSsim,
        'cmddir': '../SOSS/STARSint',
        'start': 'STARSsim.py --channels=7,8 --dir=%(datadir)s --loglevel=info --log=%(log)s',
        'datadir': datadir('STARS'),
        'log'  : get_log('STARSsim.log'),
        'flags': ('random', 'nosvccheck'),
        },

##     # This is the guider simulator (telescope)
##     "AgSim": {
##     'level': 99,
##     'hosts': g2sim.hosts,
##     'count': 1,
##     'cmddir': '../SOSS/GuiderInt',
##     'start': 'AgSim.py --binning=1 --kind=1 --fitsfile=../SOSS/GuiderInt/AG.fits --interval=0.5 --svcname=guiderint --stderr --loglevel=debug',
##     'stdout': get_log('AgSim.log'),
##     'flags': ('random', 'nosvccheck'),
##     },

    # TCS interface to TSC simulator
    "TSC": {
        'level': 4.2,
        'hosts': g2sim.hosts,
        'count': 1,
        'description': DESCR.TSC,
        'cmddir': '../SOSS/TCSint',
        'start': 'TCSint2.py --svcname=TSC --monitor=monitor --port=8141 --loglevel=debug --log=%(log)s',
        'log'  : get_log('TSC.log'),
        'flags': ('random'),
        },

    # TSC simulator
    "TSCsim": {
        'level': 4.2,
        'hosts': g2sim.hosts,
        'count': 1,
        'description': DESCR.TSC,
        'cmddir': '../SOSS/TCSint',
        'start': 'TCSint2.py --sim --loglevel=info --log=%(log)s',
        'log'  : get_log('TSCsim.log'),
        'flags': ('random', 'nosvccheck'),
        },

    # starcatalog with remoteobject 
    "starcatalog": {
        'level': 2.5,
        'hosts': g2sim.hosts,
        'count': 1,
        'description': DESCR.starcat,
        'cmddir': 'starlist',
        'start': 'starcatalog.py --loglevel=debug --log=%(log)s --port=8888 --dbhost=localhost',
        'log': get_log('starcatalog.log'),
        'flags': ('fixed', 'nosvccheck'),
        },

    "g2ag": {
        'level': 4.2,
        'hosts': g2sim.hosts,
        'count': 1,
        'cmddir': '../SIMCAM',
        'start': 'g2cam.py --cam=VGW --obcpnum=33 --gen2host=localhost --loglevel=debug --seppuku --log=%(log)s',
        'log'  : get_log('g2ag.log'),
        'stdout': get_log('g2ag_stdout.log'),
        'flags': ('prefer'),
        },

    # *** USER INTERFACE INFRASTRUCTURE ***

    # Lower Left display in a two-display setup
    "vncs-s5": {
        'level': 8,
        'hosts': g2sim.frontends,
        'count': 1,
        'cmddir': './util',
        'start': "startvnc.py 5",
        'stdout': get_log('s5_stdout.log'),
        'flags': ('fixed', 'manual'),
        },

    # Upper Left display in a two-display setup
    "vncs-s6": {
        'level': 8,
        'hosts': g2sim.frontends,
        'count': 1,
        'cmddir': './util',
        'start': "startvnc.py 6",
        'stdout': get_log('s6_stdout.log'),
        'flags': ('fixed', 'manual'),
        },

    # Lower Middle display in a two-display setup
    "vncs-s3": {
        'level': 8,
        'hosts': g2sim.frontends,
        'count': 1,
        'cmddir': './util',
        'start': "startvnc.py 3",
        'stdout': get_log('s3_stdout.log'),
        'flags': ('fixed', 'manual'),
        },

    # Upper Middle display in a two-display setup
    "vncs-s4": {
        'level': 8,
        'hosts': g2sim.frontends,
        'count': 1,
        'cmddir': './util',
        'start': "startvnc.py 4",
        'stdout': get_log('s4_stdout.log'),
        'flags': ('fixed', 'manual'),
        },

    # Lower Right display in a two-display setup
    "vncs-s1": {
        'level': 8,
        'hosts': g2sim.frontends,
        'count': 1,
        'cmddir': './util',
        'start': "startvnc.py 1",
        # 'start': 'mytightvncserver %s  -dpi 100 -depth 24 -geometry 1920x1200 -alwaysshared' % (screen(g2sim.disp.s1)),
        # 'stop': '/usr/bin/tightvncserver -kill %s' % (screen(g2sim.disp.s1)),
        'stdout': get_log('s1_stdout.log'),
        'flags': ('fixed', 'manual'),
        },

    # Upper Right display in a two-display setup
    "vncs-s2": {
        'level': 8,
        'hosts': g2sim.frontends,
        'count': 1,
        'cmddir': './util',
        'start': "startvnc.py 2",
        'stdout': get_log('s2_stdout.log'),
        'flags': ('fixed', 'manual'),
        },

    # *** SOSS COMPATIBILITY MODE FRONT ENDS ***

    "integgui2": {
        'level': 10,
        'hosts': prefer([left(g2sim.frontends)], g2sim.frontends),
        'count': 1,
        'cmddir': 'integgui2',
        'start': 'integgui2.py --taskmgr=taskmgr0 --session=main --display=%(xdisp)s --loglevel=debug --log=%(log)s',
        'xdisp': g2sim.disp.s3,
        'log'  : get_log('integgui2.log'),
        'screens': g2sim.screens,
        'stdout': get_log('integgui2_stdout.log'),
        'flags': ('prefer'),
        },

    # New fits viewer
    "fitsviewer": {
        'level': 10,
        'hosts': prefer([mid(g2sim.frontends)], g2sim.frontends),
        'count': 1,
        #'rundir': gen2home + '/Fitsview',
        'rundir': gen2home + '/../../Fitsview',
        'cmddir': '.',
        #'start': 'fitsview.py --svcname=fitsview --bufsize=10 --port=9502 --monport=10502 --monchannels=fits --geometry=+866+545 --display=%(xdisp)s --loglevel=warn --log=%(log)s',
        'start': 'fitsview.py --svcname=fitsview --bufsize=10 --port=9502 --monport=10502 --monitor=monitor --monchannels=fits --modules=QDAS --plugins=Region_Selection,Sv_Drive,FocusFit --geometry=+866+545 --display=%(xdisp)s --loglevel=info --log=%(log)s',
        'xdisp' : g2sim.disp.s4,
        'log'   : get_log('fitsview.log'),
        'stdout': get_log('fitsview_stdout.log'),
        'screens': g2sim.screens,
        'flags': ('prefer'),
        },

    "hskymon": {
        'level': 10,
        'hosts': prefer([mid(g2sim.frontends)], g2sim.frontends),
        'count': 1,
        'rundir': os.path.join(g2soss.archhome, 'bin'),
        'cmddir': '.',
        'start': 'hskymon.py --nopg --stderr --loglevel=debug --port=9506 --display=%(xdisp)s',
        'xdisp': g2sim.disp.s1,
        'screens': g2sim.screens,
        'stdout': get_log('hskymon_stdout.log'),
        'flags': ('prefer'),
        },

    "statmon": {
        'level': 10,
        'hosts': prefer([mid(g2sim.frontends)], g2sim.frontends),
        'count': 1,
        'cmddir': 'statmon',
        'start': 'statmon.py --display=%(xdisp)s --monport=34945 --loglevel=10 --log=%(log)s',
        'stop': gen2home + '/../remoteObjects/ro_shell.py -c statmon close_all_plugins',
        'xdisp' : g2sim.disp.s2,
        'screens': g2sim.screens,
        'stdout': get_log('statmon_stdout.log'),
        'log': get_log('statmon.log'),
        'flags': ('prefer'),
        },

    "telstat": {
        'level': 10,
        'hosts': prefer([left(g2sim.frontends)], g2sim.frontends),
        'count': 1,
        'cmddir': 'telstat',
        'start': 'telstat.py --nopg --stderr --geometry=+20+100 --display=%(xdisp)s',
        'xdisp': g2sim.disp.s2,
        'screens': g2sim.screens,
        'stdout': get_log('telstat_stdout.log'),
        'flags': ('prefer'),
        },

    # starcatalog with remoteobject 
    "starcatalog": {
        'level': 11,
        'hosts': g2sim.hosts,
        'count': 1,
        'description': DESCR.starcat,
        'cmddir': 'starlist',
        'start': 'starcatalog.py --loglevel=debug --log=%(log)s --port=8888',
        'log': get_log('starcatalog.log'),
        'flags': ('fixed', 'nosvccheck'),
        },


    "g2ag": {
        'level': 11,
        'hosts': g2sim.hosts,
        'count': 1,
        'cmddir': '../SIMCAM',
        'start': 'g2cam.py --cam=VGW --obcpnum=33 --gen2host=localhost --loglevel=debug --seppuku --log=%(log)s',
        'log'  : get_log('g2ag.log'),
        'stdout': get_log('g2ag_stdout.log'),
        'flags': ('prefer'),
        },

    "guideview": {
        'level': 10,
        'hosts': g2sim.hosts,
        'count': 1,
        'rundir': gen2home + '/../../Fitsview',
        #'rundir': gen2home + '/Fitsview',
        'cmddir': '.',
        'start': 'guideview.py --svcname=guideview --bufsize=2 --port=9522 --monport=10522 --display=%(xdisp)s --loglevel=info --log=%(log)s',
        'xdisp': g2sim.disp.s5,
        'log'  : get_log('guideview.log'),
        'screens': g2sim.screens,
        'stdout': get_log('guideview_stdout.log'),
        'flags': ('prefer'),
        },

    # "oldvgw-gui": {
    #     'level': 12,
    #     'hosts': g2sim.hosts,
    #     'count': 1,
    #     'rundir': g2soss.dirload,
    #     'cmddir': '.',
    #     'start': 'startvgw.py --nopg --stderr --display=%(xdisp)s',
    #     'xdisp': g2sim.disp.s5,
    #     'screens': g2sim.screens,
    #     'stdout': get_log('VGW_stdout.log'),
    #     'flags': ('prefer'),
    #     },

    # "envmon2": {
    #     'level': 15,
    #     'hosts': prefer([left(g2sim.frontends)], g2sim.frontends),
    #     'count': 1,
    #     'cmddir': 'senvmon',
    #     'start': 'EnviMonitor.py -c status --stderr --display=%(xdisp)s',
    #     'xdisp': g2sim.disp.s6,
    #     'screens': g2sim.screens,
    #     'stdout': get_log('envmon2.log'),
    #     'flags': ('prefer'),
    #     },

    "g2web": {
        'level': 90,
        'hosts': g2sim.hosts,
        'count': 1,
        'description': "The Gen2 web interface",
        'cmddir': 'web',
        'start': "g2web.py --config=g2sim --cert=%(dbdir)s/g2cert.pem --auth_users='ocs:g2/ocs' --plugins=bm,dsp,sm,data,tsc,frame --docroot=$GEN2HOME/docs --loglevel=info --log=%(log)s --detach",
        'stop': 'g2web.py --kill',
        'log':   get_log('g2web.log'),
        'dbdir': dbdir(),
        'flags': ('manual'),
        },

    "status_relay": {
        'level': 90,
        'hosts': g2sim.hosts,
        'count': 1,
        'description': "Relay summit status to Gen2 simulator.",
        'cmddir': 'misc',
        'start': "relay.py -g g2ins1.sum.subaru.nao.ac.jp",
        'flags': ('manual'),
        },

}

# Add all instrument interfaces and simulators
for insname in ins_data.getNames():
    num = ins_data.getNumberByName(insname)

    # Skip VGW, for now
    if num == 33:
        continue

    g2sim.svconfig[insname] = {
        'level': 50,
        'hosts': g2sim.hosts,
        'count': 1,
        'description': DESCR.INSint,
        'cmddir': '../SOSS/INSint',
        'start': 'INSint.py --obcpnum=%d --svcname=%s --interfaces=cmd,file --monitor=monitor --fitsdir=%s --statussvc=status --port=82%02d --inscfg=%s --loglevel=info --log=%s' % (
        num, insname, datadir(insname), num, dbdir()+'/inscfg', get_log('%s.log' % insname)),
        'flags': ('random'),
        }

    # Simulated instrument
    g2sim.svconfig['%ssim' % insname] = {
        'level': 99,
        'hosts': g2sim.hosts,
        'count': 1,
        'description': DESCR.SIMCAM,
        'cmddir': '../SIMCAM',
        'start': 'simcam.py --cam=%s=GENERIC --obcpnum=%d --paradir=../SOSS/SkPara/cmd --gen2host=localhost --loglevel=info --log=%s' % (
            insname, num, get_log('%ssim.log' % insname)),
        'flags': ('fixed', 'nosvccheck', 'manual'),
        }

g2sim.svconfig['VGW'] = {
    'level': 12,
    'hosts': g2sim.hosts,
    'count': 1,
    'description': DESCR.INSint,
    'cmddir': '../SOSS/INSint',
    'start': 'INSint.py --obcpnum=33 --svcname=VGW --interfaces=cmd,file --monitor=monitor --numthreads=50 --fitsdir=%s --myhost=g2ins1 --port=8233 --inscfg=%s --loglevel=info --log=%%(log)s --logmon=monlog' % (
    datadir('VGW'), dbdir()+'/inscfg'),
    'log'  : get_log('VGW.log'),
    'flags': ('prefer'),
    }


config = g2sim

#END

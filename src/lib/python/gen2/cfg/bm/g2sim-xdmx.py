# For compatibility mode front ends
import cfg.g2soss as g2soss
import remoteObjects as ro
from common import *

# for xdmx display
def xscreen(disp):
    return ':20'


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
g2sim.disp.ul = '%s:6' % host(g2sim, 'h1')
g2sim.disp.ll = '%s:5' % host(g2sim, 'h1')
g2sim.disp.um = '%s:4' % host(g2sim, 'h1')
g2sim.disp.lm = '%s:3' % host(g2sim, 'h1')
g2sim.disp.ur = '%s:2' % host(g2sim, 'h1')
g2sim.disp.lr = '%s:1' % host(g2sim, 'h1')

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

    "mgrsvc": {                # Name of the service
    'level': 0,                # what level does it belong to
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
    'start': 'remoteObjectNameSvc.py --monport=7077 --monauth=monitor:monitor --monitor=localhost:7080 --loglevel=info --log=%s' % (
    get_log('ro_names.log')),
    'flags': ('each'),
    },

    # Star Catalogs
    "starcat": {
    'level': 1.5,
    'hosts': g2sim.hosts,
    'count': 1,
    'description': DESCR.starcat,
    'rundir': '%s/star_catalog' % (dbdir()),
    'cmddir': '/usr/bin',
    'start': 'sudo -u postgres /usr/lib/postgresql/8.4/bin/postmaster -p 5436 -D %s/star_catalog/db' % (dbdir()),
    'stop': 'sudo -u postgres /usr/lib/postgresql/8.4/bin/pg_ctl stop -w -D %s/star_catalog/db' % (dbdir()),
    'stdout': get_log('starcat.log'),
    'flags': ('fixed', 'nosvccheck'),
    },

    "starcat1": {
    'level': 1.5,
    'hosts': g2sim.hosts,
    'count': 1,
    'description': DESCR.starcat,
    'rundir': '%s/star_catalog' % (dbdir()),
    'cmddir': '/usr/bin',
    'start': 'sudo -u postgres /usr/lib/postgresql/8.4/bin/postmaster -p 5433 -D %s/star_catalog/db1' % (dbdir()),
    'stop': 'sudo -u postgres /usr/lib/postgresql/8.4/bin/pg_ctl stop -w -D %s/star_catalog/db1' % (dbdir()),
    'stdout': get_log('starcat1.log'),
    'flags': ('fixed', 'nosvccheck'),
    },

    "starcat2": {
    'level': 1.5,
    'hosts': g2sim.hosts,
    'count': 1,
    'description': DESCR.starcat,
    'rundir': '%s/star_catalog' % (dbdir()),
    'cmddir': '/usr/bin',
    'start': 'sudo -u postgres /usr/lib/postgresql/8.4/bin/postmaster -p 5434 -D %s/star_catalog/db2' % (dbdir()),
    'stop': 'sudo -u postgres /usr/lib/postgresql/8.4/bin/pg_ctl stop -w -D %s/star_catalog/db2' % (dbdir()),
    'stdout': get_log('starcat2.log'),
    'flags': ('fixed', 'nosvccheck'),
    },

    "starcat3": {
    'level': 1.5,
    'hosts': g2sim.hosts,
    'count': 1,
    'description': DESCR.starcat,
    'rundir': '%s/star_catalog' % (dbdir()),
    'cmddir': '/usr/bin',
    'start': 'sudo -u postgres /usr/lib/postgresql/8.4/bin/postmaster -p 5435 -D %s/star_catalog/db3' % (dbdir()),
    'stop': 'sudo -u postgres /usr/lib/postgresql/8.4/bin/pg_ctl stop -w -D %s/star_catalog/db3' % (dbdir()),
    'stdout': get_log('starcat3.log'),
    'flags': ('fixed', 'nosvccheck'),
    },

    # Star Catalogs
    "starcat_pool": {
    'level': 2.5,
    'hosts': g2sim.hosts,
    'count': 1,
    'description': DESCR.starcat,
    'rundir': '%s/star_catalog' % (dbdir()),
    'cmddir': '/usr/bin',
    'start': 'sudo -u postgres /usr/sbin/pgpool -n -f %s/star_catalog/pgpool.conf' % (dbdir()),
    'stop': 'sudo -u postgres /usr/sbin/pgpool -n -f %s/star_catalog/pgpool.conf stop' % (dbdir()),
    'stdout': get_log('starcat_pool.log'),
    'flags': ('fixed', 'nosvccheck'),
    },

    "dss_server": {
    'level': 2.5,
    'hosts': g2sim.hosts,
    'count': 1,
    'description': DESCR.dssserver,
    'cmddir': 'web',
    'start': 'dss_server.py --port=30000 --loglevel=debug --log=%s' % (
    get_log('dss_server.log')),
    'flags': ('fixed', 'nosvccheck'),
    },

    "monitor": {
    'level': 2,
    'hosts': g2sim.hosts,
    'count': 1,
    'description': DESCR.monitor,
    'cmddir': '../remoteObjects',
    'start': 'PubSub.py --port=7080 --svcname=monitor --config=cfg.pubsub --loglevel=info --log=%s' % (
    get_log('monitor.log')),
    'flags': ('random'),
    },

    "bootmgr": {
    'level': 3,
    'hosts': g2sim.hosts,
    'count': 1,
    'description': DESCR.bootmgr,
    'cmddir': '.',
    'start': 'BootManager.py --config=g2sim --port=8090 --svcname="bootmgr" --loglevel=info --log=%s' % (
    get_log('bootmgr.log')),
    'flags': ('random'),
    },

    # This is the status server
    "status": {
    'level': 3,
    'hosts': g2sim.hosts,
    'count': 1,
    'description': DESCR.status,
    'cmddir': '../SOSS/status',
    'start': 'status.py --svcname=status --port=8151 --monitor=monitor --loglevel=info --log=%s --checkpt=%s/status.cpt' % (get_log('status.log'), dbdir()),
    'flags': ('random'),
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

    "sessions": {
    'level': 4,
    'hosts': g2sim.hosts,
    'count': 1,
    'description': DESCR.sessions,
    'cmddir': '.',
    'start': 'SessionManager.py --port=8105 --svcname="sessions" --db=%s/sessiondb-g2sim --loglevel=info --log=%s' % (
            dbdir(), get_log('session.log')),
    'flags': ('random'),
    },

    # This is the frame service interface
    "frames": {
    'level': 4,
    'hosts': g2sim.hosts,
    'count': 1,
    'description': DESCR.frames,
    'cmddir': '.',
    'start': 'frameSvc.py --server --port=8161 --svcname="frames" --monitor=monitor --loglevel=info --log=%s' % (
    get_log('frames.log')),
    'flags': ('random'),
    },

    "taskmgr0": {
    'level': 5,
    'hosts': g2sim.hosts,
    'count': 1,
    'description': DESCR.taskmgr,
    'cmddir': '.',
    'start': 'TaskManager.py --port=8170 --svcname="taskmgr0" --db=taskmgrdb-g2sim  --monitor=monitor --session=main --numthreads=100 --loglevel=info --stderr --log=%s:debug' % (
    get_log('taskmgr0_debug.log')),
    'stdout': get_log('taskmgr0.log'),
    'flags': ('random'),
    },

    "soundsink": {
    'level': 5,
    'hosts': g2sim.hosts,
    'count': 1,
    'cmddir': '.',
    'description': "Sound drop off point for distributing audio",
    'start': 'soundsink.py --monitor=monitor --svcname=sound --port=15051 --monport=15052 --loglevel=info --log=%s' % (
    get_log('soundsink.log')),
    'flags': ('random'),
    },

    # This is the DAQ equivalent for Gen2 (compatibility mode)
    "archiver": {
    'level': 5,
    'hosts': g2sim.hosts,
    'count': 1,
    'description': DESCR.archiver,
    'cmddir': '.',
    'start': 'Archiver.py --monitor=monitor --svcname=archiver --port=8104 --server --nomd5check --realm=other --loglevel=info --log=%s' % (get_log('archiver.log')),
    'flags': ('random', 'nosvccheck'),
    },

    "gen2base": {
    'level': 5,
    'hosts': g2sim.hosts,
    'count': 1,
    'cmddir': '.',
    'description': DESCR.archiver,
    'start': 'Archiver.py --monitor=monitor --svcname=gen2base --realm=base --port=8106 --server --nomd5check --keyfile=%s --datadir=/gen2/data/BASE --pullmethod=copy --loglevel=info --log=%s' % (
    get_key('gen2base'), get_log('gen2base_debug.log')),
    'stdout': get_log('gen2base.log'),
    'flags': ('prefer'),
    },

     # This is the STARS interface
    "STARS": {
    'level': 5,
    'hosts': g2sim.hosts,
    'count': 1,
    'description': DESCR.STARSint,
    'cmddir': '../SOSS/STARSint',
    'start': 'STARSint.py --monitor=monitor --channels=7,8 --svcname=STARS --starshost=localhost --port=8121  --keyfile=%s --loglevel=debug --log=%s' % (
    get_key('stars'), get_log('STARS.log')),
    'flags': ('random'),
    },

    # This is the STARS simulator (s01)
    "STARSsim": {
    'level': 7,
    'hosts': g2sim.hosts,
    'count': 1,
    'description': DESCR.STARSsim,
    'cmddir': '../SOSS/STARSint',
    'start': 'STARSsim.py --channels=7,8 --dir=%s --loglevel=info --log=%s' % (
    datadir('STARS'), get_log('STARSsim.log')),
    'flags': ('random', 'nosvccheck'),
    },

    # TCS interface to TSC simulator
    "TSC": {
    'level': 4.2,
    'hosts': g2sim.hosts,
    'count': 1,
    'description': DESCR.TSC,
    'cmddir': '../SOSS/TCSint/Interface',
    'start': 'TCSint2.py --svcname=TSC --monitor=monitor --port=8141 --loglevel=debug --log=%s' % (
    get_log('TSC.log')),
    'flags': ('random'),
    },

    # TSC simulator
    "TSCsim": {
    'level': 4.2,
    'hosts': g2sim.hosts,
    'count': 1,
    'description': DESCR.TSC,
    'cmddir': '../SOSS/TCSint/Interface',
    'start': 'TCSint2.py --sim --loglevel=info --log=%s' % (
    get_log('TSCsim.log')),
    'flags': ('random', 'nosvccheck'),
    },

    # TCS interface to TSC simulator
#    "TSC": {
#    'level': 4.2,
#    'hosts': g2sim.hosts,
#    'count': 1,
#    'description': DESCR.INSint,
#    'cmddir': '../SOSS/INSint',
#    'start': 'INSint.py --obcpnum=32 --svcname=TSC --interfaces=cmd,file --monitor=monitor --fitsdir=/tmp --statussvc=status --port=8232 --stderr --loglevel=info',
#    'stdout': get_log('TSC.log'),
#    'flags': ('random'),
#    },

    # TSC simulator
#    "TSCsim": {
#    'level': 4.2,
#    'hosts': g2sim.hosts,
#    'count': 1,
#    'description': DESCR.SIMCAM,
#    'cmddir': '../SIMCAM',
#    'start': 'simcam.py --cam=TSC=TSCCAM --obcpnum=32 --paradir=../SOSS/SkPara/cmd --gen2host=localhost --stderr --loglevel=info',
#    'stdout': get_log('TSCsim.log'),
#    'flags': ('fixed', 'nosvccheck'),
#    },

    # *** USER INTERFACE INFRASTRUCTURE ***

    # Lower Left display in a two-display setup
    "vncs-ll": {
        'level': 8,
        'hosts': g2sim.frontends,
        'count': len(g2sim.frontends),
        'start': 'vnc4server %s  -dpi 100 -depth 24 -geometry 1920x1200 -alwaysshared' % (screen(g2sim.disp.ll)),
        'stop': '/usr/bin/tightvncserver -kill %s' % (screen(g2sim.disp.ll)),
        'flags': ('fixed', 'manual'),
        },

    # Upper Left display in a two-display setup
    "vncs-ul": {
        'level': 8,
        'hosts': g2sim.frontends,
        'count': len(g2sim.frontends),
        'start': 'vnc4server %s  -dpi 100 -depth 24 -geometry 1920x1200 -alwaysshared' % (screen(g2sim.disp.ul)),
        'stop': '/usr/bin/tightvncserver -kill %s' % (screen(g2sim.disp.ul)),
        'flags': ('fixed', 'manual'),
        },

    # Lower Middle display in a two-display setup
    "vncs-lm": {
        'level': 8,
        'hosts': g2sim.frontends,
        'count': len(g2sim.frontends),
        'start': 'vnc4server %s  -dpi 100 -depth 24 -geometry 1920x1200 -alwaysshared' % (screen(g2sim.disp.lm)),
        'stop': '/usr/bin/tightvncserver -kill %s' % (screen(g2sim.disp.lm)),
        'flags': ('fixed', 'manual'),
        },

    # Upper Middle display in a two-display setup
    "vncs-um": {
        'level': 8,
        'hosts': g2sim.frontends,
        'count': len(g2sim.frontends),
        'start': 'vnc4server %s  -dpi 100 -depth 24 -geometry 1920x1200 -alwaysshared' % (screen(g2sim.disp.um)),
        'stop': '/usr/bin/tightvncserver -kill %s' % (screen(g2sim.disp.um)),
        'flags': ('fixed', 'manual'),
        },

    # Lower Right display in a two-display setup
    "vncs-lr": {
        'level': 8,
        'hosts': g2sim.frontends,
        'count': len(g2sim.frontends),
        'start': 'vnc4server %s  -dpi 100 -depth 24 -geometry 1920x1200 -alwaysshared' % (screen(g2sim.disp.lr)),
        'stop': '/usr/bin/tightvncserver -kill %s' % (screen(g2sim.disp.lr)),
        'flags': ('fixed', 'manual'),
        },

    # Upper Right display in a two-display setup
    "vncs-ur": {
        'level': 8,
        'hosts': g2sim.frontends,
        'count': len(g2sim.frontends),
        'start': 'vnc4server %s  -dpi 100 -depth 24 -geometry 1920x1200 -alwaysshared' % (screen(g2sim.disp.ur)),
        'stop': '/usr/bin/tightvncserver -kill %s' % (screen(g2sim.disp.ur)),
        'flags': ('fixed', 'manual'),
        },

    # Control server for keyboard and mouse events
    "xdmx-c": {
        'level': 9.1,
        'hosts': g2sim.frontends,
        'count': 1,
        'start': 'vnc4server :14  -depth 24 -geometry 1440x600 -alwaysshared',
        'stop': '/usr/bin/tightvncserver -kill :14',
        'stdout': get_log('xdmx-c.log'),
        'flags': ('nosvccheck'),
        },

    # Merge of all the individual VNC displays
    "xdmx-s": {
        'level': 9.2,
        'hosts': g2sim.frontends,
        'count': 1,
        'start': 'startx -- /usr/bin/Xdmx :20 -configfile %s/xdmx.conf -config gen2 -noxkb -input localhost:14,console,xkb,xfree86,pc104' % (dbdir()),
        'stdout': get_log('xdmx-s.log'),
        'flags': ('each'),
        },

    # *** SOSS COMPATIBILITY MODE FRONT ENDS ***

    "integgui": {
        'level': 15,
        'hosts': prefer([mid(g2sim.frontends)], g2sim.frontends),
        'count': 1,
        'rundir': g2soss.dirload,
        'cmddir': '.',
        'start': 'integgui.py  --nopg --stderr --taskmgr=taskmgr0 --display=%s' % (
            xscreen(g2sim.disp.lm)),
        'stdout': get_log('integgui_stdout.log'),
        'flags': ('prefer'),
        },

     "fitsviewer": {
         'level': 10,
         'hosts': prefer([mid(g2sim.frontends)], g2sim.frontends),
         'count': 1,
         'rundir': g2soss.dirload,
         'cmddir': '.',
         'start': 'fitsviewer.py --nopg --svcname=fitsview1 --geometry=+808+44 --display=%s --port=9501 --loglevel=info --log=%s' % (
             xscreen(g2sim.disp.um), get_log('fitsviewer.log')),
         'flags': ('prefer'),
         },

    # New fits viewer
    "fitsview": {
        'level': 10,
        'hosts': prefer([mid(g2sim.frontends)], g2sim.frontends),
        'count': 1,
        'rundir': gen2home + '/Fitsview',
        'cmddir': '.',
        'start': 'fitsview.py --svcname=fitsview --bufsize=40 --port=9502 --geometry=+20+250 --display=%s --loglevel=info --log=%s' % (
            xscreen(g2sim.disp.um), get_log('fitsview.log')),
        'flags': ('prefer'),
        },

    "sktask_gtk": {
        'level': 15,
        'hosts': g2sim.frontends,
        'count': 1,
        'cmddir': '.',
        'start': 'sktask_gtk.py --channels=taskmgr0,g2task --display=%s --loglevel=info --log=%s' % (
            xscreen(g2sim.disp.ul), get_log('sktask_gtk.log')),
        'flags': ('prefer', 'nosvccheck'),
        },

    # New monitor viewer
    "monview": {
        'level': 15,
        'hosts': prefer([right(g2sim.frontends)], g2sim.frontends),
        'count': 1,
        'rundir': gen2home + '/task_viewer',
        'cmddir': '.',
        'start': 'mon_task.py --channels=g2task --monitor=taskmgr0.mon --display=%s' % (
            xscreen(g2sim.disp.ur)),
        'stdout': get_log('mon_task.log'),
        'flags': ('prefer', 'nosvccheck'),
        },

    "telstat": {
        'level': 10,
        'hosts': prefer([left(g2sim.frontends)], g2sim.frontends),
        'count': 1,
        'rundir': g2soss.dirload,
        'cmddir': '.',
        'start': 'telstat.py --nopg --stderr --geometry=+20+100 --display=%s' % (
            xscreen(g2sim.disp.ur)),
        'stdout': get_log('telstat_stdout.log'),
        'flags': ('prefer'),
        },

    "envmon": {
        'level': 10,
        'hosts': prefer([left(g2sim.frontends)], g2sim.frontends),
        'count': 1,
        'rundir': g2soss.dirload,
        'cmddir': '.',
        'start': 'envmon.py --nopg --stderr --geometry=433x742-84-87 --display=%s' % (
            xscreen(g2sim.disp.ul)),
        'stdout': get_log('envmon_stdout.log'),
        'flags': ('prefer'),
        },

    "vgw": {
        'level': 10,
        'hosts': g2sim.hosts,
        'count': 1,
        'rundir': g2soss.dirload,
        'cmddir': '.',
        'start': 'startvgw.py --nopg --stderr --display=%s' % (
            xscreen(g2sim.disp.ll)),
        'stdout': get_log('VGW_stdout.log'),
        'flags': ('prefer'),
        },

    "skymon": {
        'level': 15,
        'hosts': prefer([mid(g2sim.frontends)], g2sim.frontends),
        'count': 1,
        'rundir': g2soss.dirload,
        'cmddir': '.',
        'start': 'skymonitor.py --nopg --stderr --loglevel=info --port=9505 --display=%s --user=g2sim' % (
            xscreen(g2sim.disp.lr)),
        'stdout': get_log('skymon.log'),
        'flags': ('prefer'),
        },

    "insmon": {
        'level': 15,
        'hosts': prefer([right(g2sim.frontends)], g2sim.frontends),
        'count': 1,
        'rundir': g2soss.dirload,
        'cmddir': '.',
        'start': 'insmon.py --nopg --stderr --geometry=433x742-84-87 --display=%s' % (
            xscreen(g2sim.disp.ur)),
        'stdout': get_log('insmon_stdout.log'),
        'flags': ('prefer'),
        },

    "hskymon": {
        'level': 10,
        'hosts': prefer([mid(g2sim.frontends)], g2sim.frontends),
        'count': 1,
        'rundir': g2soss.dirload,
        'cmddir': '.',
        'start': 'hskymon.py --nopg --stderr --loglevel=info --port=9506 --display=%s' % (
            xscreen(g2sim.disp.lr)),
        'stdout': get_log('hskymon.log'),
        'flags': ('prefer'),
        },

    "envmon2": {
        'level': 15,
        'hosts': prefer([left(g2sim.frontends)], g2sim.frontends),
        'count': 1,
        'cmddir': 'senvmon',
        'start': 'EnviMonitor.py --stderr --display=%s' % (
            xscreen(g2sim.disp.ul)),
        'stdout': get_log('envmon2.log'),
        'flags': ('prefer'),
        },

    "integgui2": {
        'level': 10,
        'hosts': prefer([left(g2sim.frontends)], g2sim.frontends),
        'count': 1,
        'cmddir': 'integgui2',
        'start': 'integgui2.py --taskmgr=taskmgr0 --session=main --display=%s --loglevel=debug --log=%s' % (
            xscreen(g2sim.disp.lm), get_log('integgui2.log')),
        'stdout': get_log('integgui2_stdout.log'),
        'flags': ('prefer'),
        },

    "qdas": {
        'level': 10,
        'hosts': g2sim.frontends,
        'count': 1,
        'rundir': g2soss.dirload,
        'cmddir': '.',
        'start': 'qdas.py --nopg --svcname=OBC --stderr --loglevel=debug --port=9510 --disp=%s' % (
            xscreen(g2sim.disp.um)),
        'stdout': get_log('qdas_stdout.log'),
        'flags': ('prefer'),
        },

}

# Add all instrument interfaces and simulators
for insname in ins_data.getNames():
    num = ins_data.getNumberByName(insname)
    g2sim.svconfig[insname] = {
        'level': 50,
        'hosts': g2sim.hosts,
        'count': 1,
        'description': DESCR.INSint,
        'cmddir': '../SOSS/INSint',
        'start': 'INSint.py --obcpnum=%d --svcname=%s --interfaces=cmd,file --monitor=monitor --fitsdir=%s --statussvc=status --port=82%02d --inscfg=%s --loglevel=info --log=%s' % (
        num, insname, datadir(insname), num, dbdir()+'/inscfg',
        get_log('%s.log' % insname)),
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

config = g2sim

#END

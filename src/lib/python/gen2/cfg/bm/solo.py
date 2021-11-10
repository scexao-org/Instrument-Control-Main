# For compatibility mode front ends
import cfg.g2soss as g2soss
import remoteObjects as ro
from common import *

#############################################################################
# LAPTOP OR DESKTOP CONFIGURATION
# Everything runs on one machine.  Starts simulators for Telescope,
# Instrument and STARS.
#############################################################################
solo = Bunch()

# All managers that will be controlled by this configuration.
#
# For each instance, possible attributes are
#   host -- host this instance will run on
#   port -- port at which to bind for remoteObject (XML-RPC) calls
#   user -- user to run under
#   basedir -- base directory in which to run
#
solo.managers = populate(
    h1=Bunch(host=ro.get_myhost(short=True)),
    )

solo.frontends = ['h1']

# Displays - first set is if we are using VNC's for the GUI displays
solo.disp = Bunch()
solo.disp.ul = '%s:6' % host(solo, 'h1')
solo.disp.ll = '%s:5' % host(solo, 'h1')
solo.disp.um = '%s:4' % host(solo, 'h1')
solo.disp.lm = '%s:3' % host(solo, 'h1')
solo.disp.ur = '%s:2' % host(solo, 'h1')
solo.disp.lr = '%s:1' % host(solo, 'h1')

# These override the above set and put the GUI's into non-VNC displays
solo.disp.ul = '%s:0' % host(solo, 'h1')
solo.disp.ll = '%s:0' % host(solo, 'h1')
solo.disp.um = '%s:0' % host(solo, 'h1')
solo.disp.lm = '%s:0' % host(solo, 'h1')
solo.disp.ur = '%s:0' % host(solo, 'h1')
solo.disp.lr = '%s:0' % host(solo, 'h1')

# predefined groups
solo.hosts = solo.managers.keys()
solo.ns = ro.unique_hosts(solo.managers.values())

solo.basedir = gen2home
#solo.basedir = '$GEN2HOME'

solo.defaults = {
    'stderr':   True,
    'monitor':  'monitor',
    'loglevel': 'info',
    'logmon': False,
    'description': '[N/A]',
    }

solo.svconfig = {

    "mgrsvc": {                # Name of the service
    'level': 0,                # what level does it belong to
    'hosts': solo.hosts,       # which hosts can it run on
    'count': len(solo.hosts),  # how many instances should I start
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
    'hosts': solo.hosts,
    'count': len(solo.hosts),
    'description': DESCR.names,
    'cmddir': '../remoteObjects',
    'start': 'remoteObjectNameSvc.py --monport=7077 --loglevel=info --log=%s' % (
    get_log('ro_names.log')),
    'flags': ('each'),
    },

    "monitor": {
    'level': 2,
    'hosts': solo.hosts,
    'count': 1,
    'description': DESCR.monitor,
    'cmddir': '../remoteObjects',
    'start': 'PubSub.py --port=7080 --svcname=monitor --config=cfg.pubsub --loglevel=info --log=%s' % (
    get_log('monitor.log')),
    'flags': ('random'),
    },

    "bootmgr": {
    'level': 3,
    'hosts': solo.hosts,
    'count': 1,
    'description': DESCR.bootmgr,
    'cmddir': '.',
    'start': 'BootManager.py --config=solo --port=8090 --svcname="bootmgr" --loglevel=info --log=%s' % (
    get_log('bootmgr.log')),
    'flags': ('random'),
    },

    # This is the status server
    "status": {
    'level': 3,
    'hosts': solo.hosts,
    'count': 1,
    'description': DESCR.status,
    'cmddir': '../SOSS/status',
    'start': 'status.py --svcname=status --port=8151 --monitor=monitor --loglevel=info --log=%s --checkpt=%s/status.cpt' % (get_log('status.log'), dbdir()),
    'flags': ('random'),
    },

    "sessions": {
    'level': 4,
    'hosts': solo.hosts,
    'count': 1,
    'description': DESCR.sessions,
    'cmddir': '.',
    'start': 'SessionManager.py --port=8105 --svcname="sessions" --db=%s/sessiondb-solo --loglevel=info --log=%s' % (
            dbdir(), get_log('session.log')),
    'flags': ('random'),
    },

    # This is the frame service interface
    "frames": {
    'level': 4,
    'hosts': solo.hosts,
    'count': 1,
    'description': DESCR.frames,
    'cmddir': '.',
    'start': 'frameSvc.py --server --port=8161 --svcname="frames" --monitor=monitor --loglevel=info --log=%s' % (
    get_log('frames.log')),
    'flags': ('random'),
    },

    # This is the alarm_handler, which monitors and reports alarms
    # from the incoming TSC feed.
    "alarm_handler": {
    'level': 4,
    'hosts': solo.hosts,
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
    'hosts': solo.hosts,
    'count': 1,
    'description': DESCR.taskmgr,
    'cmddir': '.',
    'start': 'TaskManager.py --port=8170 --svcname="taskmgr0" --db=taskmgrdb-solo  --monitor=monitor --session=main --numthreads=100 --loglevel=info --stderr --log=%s:debug' % (
    get_log('taskmgr0_debug.log')),
    'stdout': get_log('taskmgr0.log'),
    'flags': ('random'),
    },

    "soundsink": {
    'level': 5,
    'hosts': solo.hosts,
    'count': 1,
    'cmddir': '.',
    'description': "Sound drop off point for distributing audio",
    'start': 'soundsink.py --monitor=monitor --monport=15052 --loglevel=info --log=%s' % (
    get_log('soundsink.log')),
    'flags': ('random'),
    },

    # This is the DAQ equivalent for Gen2 (compatibility mode)
    "archiver": {
    'level': 5,
    'hosts': solo.hosts,
    'count': 1,
    'description': DESCR.archiver,
    'cmddir': '.',
    'start': 'Archiver.py --monitor=monitor --svcname=archiver --port=8104 --server --nomd5check --realm=other --loglevel=info --log=%s' % (get_log('archiver.log')),
    'flags': ('random', 'nosvccheck'),
    },

    # TCS interface to TSC simulator
    "TSC": {
    'level': 4.2,
    'hosts': solo.hosts,
    'count': 1,
    'description': DESCR.TSC,
    'cmddir': '../SOSS/TCSint',
    'start': 'TCSint2.py --svcname=TSC --monitor=monitor --port=8141 --loglevel=info --log=%s' % (
    get_log('TSC.log')),
    'flags': ('random'),
    },

    # TSC simulator
    "TSCsim": {
    'level': 4.2,
    'hosts': solo.hosts,
    'count': 1,
    'description': DESCR.TSC,
    'cmddir': '../SOSS/TCSint',
    'start': 'TCSint2.py --sim --loglevel=info --log=%s' % (
    get_log('TSCsim.log')),
    'flags': ('random', 'nosvccheck'),
    },

    # TCS interface to TSC simulator
#    "TSC": {
#    'level': 4.2,
#    'hosts': solo.hosts,
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
#    'hosts': solo.hosts,
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
        'hosts': solo.frontends,
        'count': len(solo.frontends),
        'cmddir': './util',
        'start': 'startvnc.py 5',
        #'start': 'mytightvncserver %s  -dpi 100 -depth 24 -geometry 1920x1200 -alwaysshared' % (screen(solo.disp.ll)),
        #'stop': '/usr/bin/tightvncserver -kill %s' % (screen(solo.disp.ll)),
        'flags': ('fixed', 'manual'),
        },

    # Upper Left display in a two-display setup
    "vncs-ul": {
        'level': 8,
        'hosts': solo.frontends,
        'count': len(solo.frontends),
        'cmddir': './util',
        'start': 'startvnc.py 6',
        #'start': 'mytightvncserver %s  -dpi 100 -depth 24 -geometry 1920x1200 -alwaysshared' % (screen(solo.disp.ul)),
        #'stop': '/usr/bin/tightvncserver -kill %s' % (screen(solo.disp.ul)),
        'flags': ('fixed', 'manual'),
        },

    # Lower Middle display in a two-display setup
    "vncs-lm": {
        'level': 8,
        'hosts': solo.frontends,
        'count': len(solo.frontends),
        'cmddir': './util',
        'start': 'startvnc.py 3',
        #'start': 'mytightvncserver %s  -dpi 100 -depth 24 -geometry 1920x1200 -alwaysshared' % (screen(solo.disp.lm)),
        #'stop': '/usr/bin/tightvncserver -kill %s' % (screen(solo.disp.lm)),
        'flags': ('fixed', 'manual'),
        },

    # Upper Middle display in a two-display setup
    "vncs-um": {
        'level': 8,
        'hosts': solo.frontends,
        'count': len(solo.frontends),
        'cmddir': './util',
        'start': 'startvnc.py 4',
        #'start': 'mytightvncserver %s  -dpi 100 -depth 24 -geometry 1920x1200 -alwaysshared' % (screen(solo.disp.um)),
        #'stop': '/usr/bin/tightvncserver -kill %s' % (screen(solo.disp.um)),
        'flags': ('fixed', 'manual'),
        },

    # Lower Right display in a two-display setup
    "vncs-lr": {
        'level': 8,
        'hosts': solo.frontends,
        'count': len(solo.frontends),
        'cmddir': './util',
        'start': 'startvnc.py 1',
        #'start': 'mytightvncserver %s  -dpi 100 -depth 24 -geometry 1920x1200 -alwaysshared' % (screen(solo.disp.lr)),
        #'stop': '/usr/bin/tightvncserver -kill %s' % (screen(solo.disp.lr)),
        'flags': ('fixed', 'manual'),
        },

    # Upper Right display in a two-display setup
    "vncs-ur": {
        'level': 8,
        'hosts': solo.frontends,
        'count': len(solo.frontends),
        'cmddir': './util',
        'start': 'startvnc.py 2',
        #'start': 'mytightvncserver %s  -dpi 100 -depth 24 -geometry 1920x1200 -alwaysshared' % (screen(solo.disp.ur)),
        #'stop': '/usr/bin/tightvncserver -kill %s' % (screen(solo.disp.ur)),
        'flags': ('fixed', 'manual'),
        },

    # *** FRONT ENDS ***

    "integgui": {
        'level': 15,
        'hosts': prefer([mid(solo.frontends)], solo.frontends),
        'count': 1,
        'rundir': g2soss.dirload,
        'cmddir': '.',
        'start': 'integgui.py  --nopg --stderr --taskmgr=taskmgr0 --display=%s' % (
            screen(solo.disp.lm)),
        'stdout': get_log('integgui_stdout.log'),
        'flags': ('prefer'),
        },

     "fitsviewer": {
         'level': 10,
         'hosts': prefer([mid(solo.frontends)], solo.frontends),
         'count': 1,
         'rundir': g2soss.dirload,
         'cmddir': '.',
         'start': 'fitsviewer.py --nopg --svcname=fitsview1 --geometry=+808+44 --display=%s --port=9501 --loglevel=info --log=%s' % (
             screen(solo.disp.um), get_log('fitsviewer.log')),
         'flags': ('prefer'),
         },

    # New fits viewer
    "fitsview": {
        'level': 10,
        'hosts': prefer([mid(solo.frontends)], solo.frontends),
        'count': 1,
        'rundir': gen2home + '/../../Fitsview',
        'cmddir': '.',
        'start': 'fitsview.py --svcname=fitsview --bufsize=10 --port=9502 --monport=10502 --monitor=monitor --monchannels=fits --modules=QDAS --plugins=Region_Selection,Sv_Drive,FocusFit --geometry=+20+250 --display=%s --loglevel=info --log=%s' % (
            screen(solo.disp.um), get_log('fitsview.log')),
        'flags': ('prefer'),
        },

    "telstat": {
        'level': 10,
        'hosts': prefer([left(solo.frontends)], solo.frontends),
        'count': 1,
        'rundir': g2soss.dirload,
        'cmddir': '.',
        'start': 'telstat.py --nopg --stderr --geometry=+20+100 --display=%s' % (
            screen(solo.disp.ur)),
        'stdout': get_log('telstat_stdout.log'),
        'flags': ('prefer'),
        },

    "statmon": {
        'level': 10,
        'hosts': prefer([left(solo.frontends)], solo.frontends),
        'count': 1,
        'cmddir': 'statmon',
        'start': 'statmon.py --display=%(xdisp)s --monport=34945 --loglevel=10 --log=%(log)s',
        'stop': gen2home + '/../remoteObjects/ro_shell.py -c statmon close_all_plugins',
        'xdisp' : screen(solo.disp.ul),
        'stdout': get_log('statmon_stdout.log'),
        'log': get_log('statmon.log'),
        'flags': ('prefer'),
        },

    "vgw": {
        'level': 10,
        'hosts': solo.hosts,
        'count': 1,
        'rundir': g2soss.dirload,
        'cmddir': '.',
        'start': 'startvgw.py --nopg --stderr --display=%s' % (
            screen(solo.disp.ll)),
        'stdout': get_log('VGW_stdout.log'),
        'flags': ('prefer'),
        },

    "insmon": {
        'level': 15,
        'hosts': prefer([right(solo.frontends)], solo.frontends),
        'count': 1,
        'rundir': g2soss.dirload,
        'cmddir': '.',
        'start': 'insmon.py --nopg --stderr --geometry=433x742-84-87 --display=%s' % (
            screen(solo.disp.ur)),
        'stdout': get_log('insmon_stdout.log'),
        'flags': ('prefer'),
        },

    "hskymon": {
        'level': 10,
        'hosts': prefer([mid(solo.frontends)], solo.frontends),
        'count': 1,
        'rundir': gen2home + '/util',
        'cmddir': '.',
        'start': 'hskymon.py --nopg --stderr --loglevel=info --display=%s' % (
            screen(solo.disp.lr)),
        'stdout': get_log('hskymon.log'),
        'flags': ('prefer'),
        },

    "envmon2": {
        'level': 15,
        'hosts': prefer([left(solo.frontends)], solo.frontends),
        'count': 1,
        'cmddir': 'senvmon',
        'start': 'EnviMonitor.py --stderr --display=%s' % (
            screen(solo.disp.ul)),
        'stdout': get_log('envmon2.log'),
        'flags': ('prefer'),
        },

    "integgui2": {
        'level': 10,
        'hosts': prefer([left(solo.frontends)], solo.frontends),
        'count': 1,
        'cmddir': 'integgui2',
        'start': 'integgui2.py --taskmgr=taskmgr0 --session=main --display=%s --loglevel=debug --log=%s' % (
            screen(solo.disp.lm), get_log('integgui2.log')),
        'stdout': get_log('integgui2_stdout.log'),
        'flags': ('prefer'),
        },

    "qdas": {
        'level': 10,
        'hosts': solo.frontends,
        'count': 1,
        'rundir': g2soss.dirload,
        'cmddir': '.',
        'start': 'qdas.py --nopg --svcname=OBC --stderr --loglevel=debug --port=9510 --disp=%s' % (
            screen(solo.disp.um)),
        'stdout': get_log('qdas_stdout.log'),
        'flags': ('prefer'),
        },

    "g2ag": {
        'level': 12,
        'hosts': solo.frontends,
        'count': 1,
        'cmddir': '../SIMCAM',
        'start': 'g2cam.py --cam=VGW --obcpnum=33 --gen2host=localhost --loglevel=debug --seppuku --log=%(log)s',
        'log'  : get_log('g2ag.log'),
        'stdout': get_log('g2ag_stdout.log'),
        'flags': ('prefer'),
        },

    "guideview": {
        'level': 12,
        'hosts': solo.frontends,
        'count': 1,
        'rundir': gen2home + '/../../Fitsview',
        'cmddir': '.',
        'start': 'guideview.py --svcname=guideview --bufsize=2 --port=9522 --monport=10522 --display=%(xdisp)s --loglevel=info --log=%(log)s',
        'xdisp' : solo.disp.ll,
        'log'   : get_log('guideview.log'),
        'stdout'   : get_log('guideview_stdout.log'),
        'flags': ('prefer'),
        },

    "g2web": {
        'level': 90,
        'hosts': solo.frontends,
        'count': 1,
        'description': "The Gen2 web interface",
        'cmddir': 'web',
        'start': "g2web.py --config=solo --plugins=bm,dsp,sm,data,tsc,frame --docroot=$GEN2HOME/docs --loglevel=info --log=%(log)s --detach",
        'log':   get_log('g2web.log'),
        'flags': ('random'),
        },

    # Test of periodic functions
    "test_future": {
        'level': 90,
        'hosts': solo.frontends,
        'count': 1,
        'description': "A test of the future facility in BootManager",
        'periodic': calc_future(10.0),
        'start': 'date',
        'stdout': get_log('test-future.log'),
        'flags': ('random', 'nosvccheck'),
        },

    "test-cron": {
        'level': 90,
        'hosts': solo.frontends,
        'count': 1,
        'description': "A test of the cron facility in BootManager",
        'periodic': calc_cron(min=range(1,60,2)),
        'start': 'date',
        'stdout': get_log('test-cron.log'),
        'flags': ('random', 'nosvccheck'),
        },

    "agsim": {
        'level': 90,
        'hosts': solo.frontends,
        'count': 1,
        'cmddir': '../tools',
        'start': 'agsim.py --loglevel=debug --log=%(log)s --display=%(xdisp)s',
        'xdisp' : solo.disp.ul,
        'log'   : get_log('agsim.log'),
        'stdout': get_log('agsim_stdout.log'),
        'flags': ('prefer'),
    },
}

# Add all instrument interfaces and simulators
for insname in ins_data.getNames():
    num = ins_data.getNumberByName(insname)
    solo.svconfig[insname] = {
        'level': 50,
        'hosts': solo.hosts,
        'count': 1,
        'description': DESCR.INSint,
        'cmddir': '../SOSS/INSint',
        'start': 'INSint.py --obcpnum=%d --svcname=%s --interfaces=cmd,file --monitor=monitor --fitsdir=%s --statussvc=status --port=82%02d --inscfg=%s --loglevel=info --log=%s' % (
        num, insname, datadir(insname), num, dbdir()+'/inscfg',
        get_log('%s.log' % insname)),
        'flags': ('random'),
        }

    # Simulated instrument
    solo.svconfig['%ssim' % insname] = {
    'level': 99,
    'hosts': solo.hosts,
    'count': 1,
    'description': DESCR.SIMCAM,
    'cmddir': '../SIMCAM',
    'start': 'simcam.py --cam=%s=GENERIC --obcpnum=%d --paradir=../SOSS/SkPara/cmd --gen2host=localhost --loglevel=info --log=%s' % (
        insname, num, get_log('%ssim.log' % insname)),
    'flags': ('fixed', 'nosvccheck', 'manual'),
    }

config = solo

#END

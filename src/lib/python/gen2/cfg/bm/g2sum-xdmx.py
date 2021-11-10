# For compatibility mode front ends
import cfg.g2soss as g2soss
from common import *

# for xdmx display
def xscreen(disp):
    return ':20'

#############################################################################
# GEN2 CLUSTER CONFIGURATION
#############################################################################
gen2 = Bunch()

gen2.defaults = {
    'stderr':   True,
    'monitor':  'monitor',
    'loglevel': 'info',
    'nologmon': True,
    'description': '[N/A]',
    }

# Gen2 floating interfaces
gen2.interfaces = Bunch(
    tscint=Bunch(addr='192.168.103.141', mask='255.255.255.0', dev='vlan103:1'),
    agint=Bunch(addr='192.168.106.141', mask='255.255.255.0', dev='vlan106:1'),
    nfs=Bunch(addr='133.40.167.8', mask='255.255.255.0', dev='vlan167:2'),
    g2stat=Bunch(name='g2stat', mask='255.255.255.0', dev='vlan167:3'),
    g2ins1=Bunch(name='g2ins1', mask='255.255.255.0', dev='vlan167:4'),
    g2ins2=Bunch(name='g2ins2', mask='255.255.255.0', dev='vlan167:5'),
    g2guide=Bunch(name='g2guide', mask='255.255.255.0', dev='vlan167:6'),
    )

# Gen2 hosts
gen2.managers = populate(
    # cluster, real hosts
    c1=Bunch(host='g2s1', alt=['agint']),
    #c2=Bunch(host='g2s2', alt=['g2ins2']),
    c3=Bunch(host='g2s3', alt=['g2ins1', 'nfs']),
    c4=Bunch(host='g2s4', alt=['tscint', 'g2stat', 'g2guide']),
    cb=Bunch(host='g2b1'),

    # cluster, vms
    #cv1=Bunch(host='ssvm1'),
    #cv2=Bunch(host='ssvm2'),
    #cv3=Bunch(host='ssvm3'),

    # others
    #dh1=Bunch(host='castor'),
    #dh2=Bunch(host='pollux'),
    #dh3=Bunch(host='antares'),
    )

gen2.be1 = 'c1'
#gen2.be2 = 'c2'
gen2.be2 = 'c1'
gen2.be3 = 'c3'
gen2.be4 = 'c4'
gen2.beb = 'cb'

gen2.summit = list(set([gen2.be1, gen2.be2, gen2.be3, gen2.be4]))
gen2.base   = list(set([gen2.beb]))
gen2.backends = gen2.summit + gen2.base
gen2.backends.sort()

# "floating" interfaces
gen2.float = get_floaters(gen2.managers)

# Front ends
gen2.fe1 = 'c1'
gen2.fe2 = 'c3'
gen2.fe3 = 'c4'

#gen2.frontends = list(set((gen2.fe1, gen2.fe2, gen2.fe3)))
#gen2.frontends.sort()
gen2.frontends = [gen2.fe3, gen2.fe2, gen2.fe1]

# Displays
gen2.disp = Bunch()
gen2.disp.ul = '%s:6' % host(gen2, gen2.fe3)
gen2.disp.ll = '%s:5' % host(gen2, gen2.fe3)
gen2.disp.um = '%s:4' % host(gen2, gen2.fe2)
gen2.disp.lm = '%s:3' % host(gen2, gen2.fe2)
gen2.disp.ur = '%s:2' % host(gen2, gen2.fe1)
gen2.disp.lr = '%s:1' % host(gen2, gen2.fe1)

gen2.hosts = list(set(gen2.backends + gen2.frontends))

gen2.basedir = gen2home

gen2.svconfig = {

    "mgrsvc": {                # Name of the service
    'level': 0,                # what level does it belong to
    'hosts': gen2.hosts,

    'count': len(gen2.hosts),  # how many instances should I start
    'description': DESCR.mgrsvc,
                               # what is the path to the executable from
                               #the base directory
    'cmddir': '../remoteObjects',
                               # command to start the program 
    'start': 'remoteObjectManagerSvc.py --detach --logdir=%s --logbyhostname --log=ro_mgrsvg.log --output=ro_mgrsvc_stdout.log --loglevel=info' % (
        logdir()),
    'flags': (),         # special notes to BootManager
    },

    "ifup": {
    'level': 0.1,
    'hosts': gen2.hosts,
    'count': len(gen2.hosts),
    'description': DESCR.names,
    'cmddir': '.',
    'start': 'ifcfg.py --config=g2sum',
    'stdout': '/tmp/ifcfg.log',
    'flags': ('each', 'manual'),
    },

    "names": {
    'level': 1,
    'hosts': gen2.hosts,
    'count': len(gen2.hosts),
    'description': DESCR.names,
    'cmddir': '../remoteObjects',
    'start': 'remoteObjectNameSvc.py --monport=7077 --monitor=g2stat:7080 --monauth=monitor:monitor --logdir=%s --logbyhostname --loglevel=info' % (
        logdir()),
    'flags': ('each'),
    },

    "monitor": {
    'level': 2,
    #'hosts': gen2.backends,
    'hosts': prefer([gen2.float.g2stat], gen2.summit),
    'count': 1,
    'description': DESCR.monitor,
    'cmddir': '../remoteObjects',
    'start': 'PubSub.py --port=7080 --svcname=monitor --config=cfg.pubsub --loglevel=info --log=%s' % (get_log('monitor.log')),
    'flags': ('prefer'),
    },

    "bootmgr": {
    'level': 3,
    'hosts': gen2.summit,
    'count': 1,
    'description': DESCR.bootmgr,
    'cmddir': '.',
    'start': 'BootManager.py --config=gen2 --port=8090 --svcname="bootmgr" --loglevel=info --log=%s' % (get_log('bootmgr.log')),
    'flags': ('random'),
    },

    # This is the status server
    "status": {
    'level': 3,
    'hosts': prefer([gen2.float.g2stat], gen2.summit),
    'count': 1,
    'description': DESCR.status,
    'cmddir': '../SOSS/status',
    'start': 'status.py --svcname=status --port=8151 --monitor=monitor --myhost=g2stat --loglevel=info --log=%s --checkpt=%s/status.cpt --loghome=%s' % (
    get_log('status.log'), dbdir(), logdir()),
    'flags': ('prefer'),
    },

    # AG/SV/SH/FMOS autoguider splitter.
    "agsplit": {
    'level': 3,
    'hosts': prefer([gen2.float.agint], gen2.summit),
    'count': 1,
    'description': """This is the AG/SV/SH splitter software.  It sends the
images coming from the guider cameras to both SOSS and Gen2.""",
    'rundir': g2soss.dirload,
    'cmddir': '.',
    'start': 'agsplit.py --nopg vgw.sum.subaru.nao.ac.jp %s' % ('g2guide.sum.subaru.nao.ac.jp'),
    'stdout': get_log('agsplit.log'),
    'flags': ('fixed', 'nosvccheck'),
    },

    # Star Catalogs
    "starcat": {
    'level': 1,
    'hosts': prefer([gen2.be1], gen2.backends),
    'count': 1,
    'description': DESCR.starcat,
    'rundir': '%s/starcat' % (starcatdir()),
    'cmddir': '/usr/bin',
    'start': 'sudo -u postgres /usr/lib/postgresql/8.4/bin/postgres -p 5436 -D %s/starcat/8_4db' % (starcatdir()),
    'stop': 'sudo -u postgres /usr/lib/postgresql/8.4/bin/pg_ctl stop -D %s/starcat/8_4db -m fast' % (starcatdir()),
    'stdout': get_log('starcat.log'),
    'flags': ('fixed', 'nosvccheck'),
    },

    "starcat1": {
    'level': 1,
    'hosts': prefer([gen2.be1], gen2.backends),
    'count': 1,
    'description': DESCR.starcat,
    'rundir': '%s/starcat' % (starcatdir()),
    'cmddir': '/usr/bin',
    'start': 'sudo -u postgres /usr/lib/postgresql/8.4/bin/postgres -p 5433 -D %s/starcat/8_4db1' % (starcatdir()),
    'stop': 'sudo -u postgres /usr/lib/postgresql/8.4/bin/pg_ctl stop -D %s/starcat/8_4db1 -m fast' % (starcatdir()),
    'stdout': get_log('starcat1.log'),
    'flags': ('fixed', 'nosvccheck'),
    },

    "starcat2": {
    'level': 1,
    'hosts': prefer([gen2.be1], gen2.backends),
    'count': 1,
    'description': DESCR.starcat,
    'rundir': '%s/starcat' % (starcatdir()),
    'cmddir': '/usr/bin',
    'start': 'sudo -u postgres /usr/lib/postgresql/8.4/bin/postgres -p 5434 -D %s/starcat/8_4db2' % (starcatdir()),
    'stop': 'sudo -u postgres /usr/lib/postgresql/8.4/bin/pg_ctl stop -D %s/star_catalog/8_4db2 -m fast' % (starcatdir()),
    'stdout': get_log('starcat2.log'),
    'flags': ('fixed', 'nosvccheck'),
    },

    "starcat3": {
    'level': 1,
    'hosts': prefer([gen2.be1], gen2.backends),
    'count': 1,
    'description': DESCR.starcat,
    'rundir': '%s/starcat' % (starcatdir()),
    'cmddir': '/usr/bin',
    'start': 'sudo -u postgres /usr/lib/postgresql/8.4/bin/postgres -p 5435 -D %s/starcat/8_4db3' % (starcatdir()),
    'stop': 'sudo -u postgres /usr/lib/postgresql/8.4/bin/pg_ctl stop -D %s/starcat/8_4db3 -m fast' % (starcatdir()),
    'stdout': get_log('starcat3.log'),
    'flags': ('fixed', 'nosvccheck'),
    },

    # Star Catalogs
    "starcat_pool": {
    'level': 2,
    'hosts': prefer([gen2.be1], gen2.backends),
    'count': 1,
    'description': DESCR.starcat,
    'rundir': '%s/starcat' % (starcatdir()),
    'cmddir': '/usr/bin',
    'start': 'sudo -u postgres /usr/sbin/pgpool -n -f %s/starcat/pgpool.conf' % (starcatdir()),
    'stop': 'sudo -u postgres /usr/sbin/pgpool -m fast stop',
    'stdout': get_log('starcat_pool.log'),
    'flags': ('fixed', 'nosvccheck'),
    },

    # DSS Server
    "dss_server": {
    'level': 2,
    'hosts': prefer([gen2.be1], gen2.backends),
    'count': 1,
    'description': DESCR.dssserver,
    'cmddir': 'web',
    'start': 'dss_server.py --loglevel=debug --log=%s --port=30000' % (
    get_log('dss_server.log')),
    'flags': ('fixed', 'nosvccheck'),
    },

    # LTCS file generator.
#     "ltcs": {
#     'level': 3.1,
#     'hosts': prefer([gen2.float.g2ins2], gen2.summit),
#     'count': 1,
#     'description': """This is the Laser Traffic Control System reporting daemon.  It reports Subaru's pointing position to other laser propagating telescopes on the summit of Mauna Kea.""",
#     'cmddir': '.',
#     'rundir': 'ltcs',
#     'count': 1,
#     'start': "ltcs.py --update=1.0 --stderr --rohost=ltcs.naoj.hawaii.edu:8111 --auth=joe:bob2bob --secure --svcname=ltcs:8212 start",
#     'stdout': get_log('ltcs.log'),
#     'flags': ('fixed', 'nosvccheck'),
#     },

    "sessions": {
    'level': 4,
    'hosts': gen2.summit,
    'count': 1,
    'description': DESCR.sessions,
    'cmddir': '.',
    'start': 'SessionManager.py --port=8105 --svcname="sessions" --loglevel=debug --log=%s --db=%s/sessiondb-gen2' % (
            get_log('session.log'), dbdir()),
    'flags': ('random'),
    },

    "taskmgr0": {
    'level': 5,
    #'hosts': gen2.summit,
    'hosts': prefer([gen2.float.g2stat], gen2.summit),
    'count': 1,
    'description': DESCR.taskmgr,
    'cmddir': '.',
    'start': 'TaskManager.py --port=8170 --svcname="taskmgr0" --monitor=monitor --session=main --numthreads=120 --stderr --loglevel=info --log=%s:debug' % (get_log('taskmgr0_debug.log')),
#    'start': 'TaskManager.py --port=8170 --svcname="taskmgr0" --monitor=monitor --session=main --numthreads=120 --stderr --loglevel=info',
    'stdout': get_log('taskmgr0.log'),
    'flags': ('prefer'),
    },

    "archiver": {
    'level': 5,
    #'hosts': gen2.summit,
    'hosts': prefer([gen2.float.g2ins1], gen2.summit),
    'count': 1,
    'cmddir': '.',
    'description': DESCR.archiver,
    'start': 'Archiver.py --monitor=monitor --svcname=archiver --realm=summit --nomd5check --port=8104 --server --loglevel=debug --log=%s' % (get_log('archiver_debug.log')),
    'flags': ('prefer'),
    },

    "gen2base": {
    'level': 5,
    #'hosts': gen2.base,
    'hosts': prefer([gen2.beb], gen2.backends),
    'count': 1,
    'cmddir': '.',
    'description': DESCR.archiver,
    'start': 'Archiver.py --monitor=monitor --svcname=gen2base --realm=base --port=8104 --server --nomd5check --keyfile=%s --datadir=/mnt/raid6data/data --pullhost=g2ins1 --pullname=gen2 --pullmethod=copy --loglevel=debug --log=%s' % (get_key('gen2base'), get_log('gen2base_debug.log')),
    'flags': ('prefer'),
    },

    "soundsink": {
    'level': 4,
    'hosts': gen2.summit,
    'count': 1,
    'cmddir': '.',
    'description': "Sound drop off point for distributing audio",
    'start': 'soundsink.py --monitor=monitor --svcname=sound --port=15051 --monport=15052 --loglevel=info --log=%s' % (get_log('soundsink.log')),
    'flags': ('random'),
    },

    # This is the STARS simulator (s01)
    "STARSsim": {
    'level': 40.1,
    'hosts': gen2.base,
    'count': 1,
    'description': DESCR.STARSsim,
    'cmddir': '../SOSS/STARSint',
    'start': 'STARSsim.py --channels=7,8 --dir=%s --loglevel=info --log=%s' % (
    datadir('STARS'), get_log('STARSsim.log')),
    'flags': ('random', 'nosvccheck'),
    },

    # This is the frame service interface
    "frames": {
    'level': 40.1,
    #'hosts': gen2.summit,
    'hosts': prefer([gen2.be3], gen2.summit),
    'count': 1,
    'description': DESCR.frames,
    'cmddir': '.',
    'start': 'frameSvc.py --server --port=8161 --svcname=frames --monitor=monitor --log=Logs/frames.log --loglevel=info --log=%s' % (get_log('frames.log')),
    'flags': ('prefer'),
    },

    # This is the frame service interface with proxy to SOSS
    "frames0": {
    'level': 4.1,
    #'hosts': gen2.summit,
    'hosts': prefer([gen2.be3], gen2.summit),
    'count': 1,
    'description': DESCR.frames,
    'cmddir': '.',
    'start': 'frameSvc.py --server --port=8161 --svcname=frames --monitor=monitor --proxy=obs.sum.subaru.nao.ac.jp --loglevel=debug --log=%s' % (
    get_log('frames_debug.log')),
    'flags': ('prefer'),
    },

    # TCS interface
    "TSC0": {
    'level': 4.1,
    'hosts': prefer([gen2.float.g2stat], gen2.summit),
    'count': 1,
    'description': DESCR.TSC,
    'cmddir': '../SOSS/TCSint/Interface',
    'start': 'TCSint2.py --svcname=TSC --monitor=monitor --numthreads=70 --port=8141 --tcshost=tsc --loglevel=info --log=%s' % (
    get_log('TSC.log')),
    'flags': ('prefer'),
    },

    # This is the STARS interface ##   
    "STARS": {
    'level': 4.1,
    'hosts': gen2.base,
    'count': 1,
    'description': DESCR.STARSint,
    'cmddir': '../SOSS/STARSint',
    'start': 'STARSint.py --monitor=monitor --channels=3,4 --svcname=STARS  --port=8121 --keyfile=%s  --loglevel=debug --log=%s' % (
    get_key('stars'), get_log('STARS.log')),
    'flags': ('random'),
    },

    # TCS interface
    "fakeTSC": {
    'level': 40.1,
    'hosts': prefer([gen2.float.g2stat], gen2.summit),
    'count': 1,
    'description': DESCR.TSC,
    'cmddir': '../SOSS/TCSint/Interface',
    'start': 'TCSint2.py --svcname=TSC --monitor=monitor --numthreads=100 --port=8141 --tcshost=localhost --loglevel=info --log=%s' % (
    get_log('fakeTSC.log')),
    'flags': ('prefer'),
    },

    # TSC simulator
    "TSCsim": {
    'level': 40.1,
    'hosts': prefer([gen2.float.g2stat], gen2.summit),
    'count': 1,
    'description': DESCR.TSC,
    'cmddir': '../SOSS/TCSint/Interface',
    'start': 'TCSint2.py --sim --loglevel=info --log=%s' % (
    get_log('TSCsim.log')),
    'flags': ('prefer', 'nosvccheck'),
    },

    # This fetches UT1_UTC tables
    "ut1-utc": {
    'level': 90,
    'hosts': gen2.backends,
    'count': 1,
    'description': DESCR.ut1_utc,
    'periodic': calc_future(604800, hr=10),
    'cmddir': '../SOSS/status',
    'start': 'get-ut1utc.py --loglevel=debug --log=%s' % (
    get_log('ut1_utc.log')),
    'flags': ('random', 'nosvccheck'),
    },

    # send gen2-logs every morning at 9 am
    "sendlog": {
    'level': 90,
    'hosts': prefer([gen2.float.g2ins1], gen2.summit),
    'count': 1,
    'cmddir': '../tools',
    'start': 'send_log.py --loglevel=debug',
    'periodic': calc_future(86400, hr=9),
    'stdout': get_log('sendlog.log'),
    'flags': ('prefer'),
    },
    
    # delete tsc-status logs if they are 15 days old; run in every 30 days
    # note: 2010-07-19 becasue of testing phase, this script runs in every 3days 
    #       and delete logs that are 2 days old. 
    "deletelog": {
    'level': 90,
    'hosts': prefer([gen2.float.g2ins1], gen2.summit),
    'count': 1,
    'cmddir': '../tools',
    'start': 'delete_log.py --age=2 --loglevel=debug',
    'periodic': calc_future(259200, hr=11),
    'stdout': get_log('deletelog.log'),
    'flags': ('prefer'),
    },

    "monarch": {
    'level': 99,
    #'hosts': gen2.backends,
    'hosts': gen2.summit,
    'count': 1,
    'description': DESCR.monitor,
    'cmddir': '..',
    'start': 'Monitor.py --port=9009 --svcname=monarch --loglevel=debug --log=%s' % (get_log('monarch.log')),
    'flags': ('random'),
    },

    # *** USER INTERFACE INFRASTRUCTURE ***

    # Lower Left display in a two-display setup
    "vncs-ll": {
        'level': 8,
        'hosts': prefer([left(gen2.frontends)], gen2.frontends),
        'count': 1,
        'start': 'vnc4server %s  -dpi 100 -depth 24 -geometry 1910x1165 -alwaysshared' % (screen(gen2.disp.ll)),
        'stop': '/usr/bin/tightvncserver -kill %s' % (screen(gen2.disp.ll)),
        'flags': ('fixed', 'manual'),
        },

    # Upper Left display in a two-display setup
    "vncs-ul": {
        'level': 8,
        'hosts': prefer([left(gen2.frontends)], gen2.frontends),
        'count': 1,
        'start': 'vnc4server %s  -dpi 100 -depth 24 -geometry 1910x1165 -alwaysshared' % (screen(gen2.disp.ul)),
        'stop': '/usr/bin/tightvncserver -kill %s' % (screen(gen2.disp.ul)),
        'flags': ('fixed', 'manual'),
        },

    # Lower Middle display in a two-display setup
    "vncs-lm": {
        'level': 8,
        'hosts': prefer([mid(gen2.frontends)], gen2.frontends),
        'count': 1,
        'start': 'vnc4server %s  -dpi 100 -depth 24 -geometry 1910x1165 -alwaysshared' % (screen(gen2.disp.lm)),
        'stop': '/usr/bin/tightvncserver -kill %s' % (screen(gen2.disp.lm)),
        'flags': ('fixed', 'manual'),
        },

    # Upper Middle display in a two-display setup
    "vncs-um": {
        'level': 8,
        'hosts': prefer([mid(gen2.frontends)], gen2.frontends),
        'count': 1,
        'start': 'vnc4server %s  -dpi 100 -depth 24 -geometry 1910x1165 -alwaysshared' % (screen(gen2.disp.um)),
        'stop': '/usr/bin/tightvncserver -kill %s' % (screen(gen2.disp.um)),
        'flags': ('fixed', 'manual'),
        },

    # Lower Right display in a two-display setup
    "vncs-lr": {
        'level': 8,
        'hosts': prefer([right(gen2.frontends)], gen2.frontends),
        'count': 1,
        'start': 'vnc4server %s  -dpi 100 -depth 24 -geometry 1910x1165 -alwaysshared' % (screen(gen2.disp.lr)),
        'stop': '/usr/bin/tightvncserver -kill %s' % (screen(gen2.disp.lr)),
        'flags': ('fixed', 'manual'),
        },

    # Upper Right display in a two-display setup
    "vncs-ur": {
        'level': 8,
        'hosts': prefer([right(gen2.frontends)], gen2.frontends),
        'count': 1,
        'start': 'vnc4server %s  -dpi 100 -depth 24 -geometry 1910x1165 -alwaysshared' % (screen(gen2.disp.ur)),
        'stop': '/usr/bin/tightvncserver -kill %s' % (screen(gen2.disp.ur)),
        'flags': ('fixed', 'manual'),
        },

#     # Synergy server
#     "synergys": {
#         'level': 9,
#         'hosts': [mid(gen2.frontends)],
#         'count': 1,
#         'start': 'synergys -f --display %s' % (),
#         'flags': ('fixed'),
#         },

#     # Synergy clients
#     "synergyc": {
#         'level': 10,
#         #'hosts': [left(gen2.frontends), right(gen2.frontends)],
#         'hosts': [left(gen2.frontends)],
#         'count': len(gen2.frontends)-1,
#         'start': 'synergyc -f %s' % (mid(gen2.frontends)),
#         'flags': ('fixed'),
#         },

    # Control server for keyboard and mouse events
    "xdmx-c": {
        'level': 9.1,
        'hosts': prefer([gen2.float.agint], gen2.summit),
        'count': 1,
        'start': 'vnc4server :14  -depth 24 -geometry 1440x600 -alwaysshared',
        'stop': '/usr/bin/tightvncserver -kill :14',
        'stdout': get_log('xdmx-c.log'),
        'flags': ('nosvccheck'),
        },

    # Merge of all the individual VNC displays
    "xdmx-s": {
        'level': 9.2,
        'hosts': prefer([gen2.float.agint], gen2.summit),
        'count': 1,
        'start': 'startx -- /usr/bin/Xdmx :20 -configfile %s/xdmx.conf -config gen2 -noxkb -input localhost:14,console,xkb,xfree86,pc104' % (dbdir()),
        'stdout': get_log('xdmx-s.log'),
        'flags': ('each'),
        },

    # *** SOSS COMPATIBILITY MODE FRONT ENDS ***

    "integgui": {
        'level': 15,
        'hosts': prefer([mid(gen2.frontends)], gen2.frontends),
        'count': 1,
        'rundir': g2soss.dirload,
        'cmddir': '.',
        'start': 'integgui.py  --nopg --stderr --taskmgr=taskmgr0 --display=%s' % (
            xscreen(gen2.disp.lm)),
        'stdout': get_log('integgui_stdout.log'),
        'flags': ('prefer'),
        },

    "integgui2": {
        'level': 10,
        'hosts': prefer([mid(gen2.frontends)], gen2.frontends),
        'count': 1,
        'cmddir': 'integgui2',
        'start': 'integgui2.py --taskmgr=taskmgr0 --session=main --display=%s --loglevel=debug --log=%s' % (
            xscreen(gen2.disp.lm), get_log('integgui2.log')),
        'stdout': get_log('integgui2_stdout.log'),
        'flags': ('prefer'),
        },

    "fitsviewer": {
        'level': 10,
        'hosts': prefer([mid(gen2.frontends)], gen2.frontends),
        'count': 1,
        'rundir': g2soss.dirload,
        'cmddir': '.',
        'start': 'fitsviewer.py --nopg --svcname=fitsview1 --geometry=+816+28 --display=%s --port=9501 --loglevel=10 --log=%s' % (
            xscreen(gen2.disp.um), get_log('fitsviewer.log')),
        'flags': ('prefer'),
        },

    # New fits viewer
    "fitsview": {
        'level': 10,
        'hosts': prefer([left(gen2.frontends)], gen2.frontends),
        'count': 1,
        'rundir': gen2home + '/Fitsview',
        'cmddir': '.',
        'start': 'fitsview.py --svcname=fitsview --bufsize=40 --port=9502 --geometry=+866+545 --display=%s --loglevel=debug --log=%s' % (
            xscreen(gen2.disp.ul), get_log('fitsview.log')),
        'flags': ('prefer'),
        },

#     "sktask_gui": {
#         'level': 15,
#         'hosts': prefer([left(gen2.frontends)], gen2.frontends),
#         'count': 1,
#         'cmddir': '.',
#         'start': 'sktask_gui.py --channels=taskmgr0,g2task --display=%s' % (
#             xscreen(gen2.disp.ul)),
#         'stdout': get_log('sktask_gui.log'),
#         'flags': ('prefer', 'nosvccheck'),
#         },

    "sktask_gtk": {
        'level': 15,
        'hosts': prefer([left(gen2.frontends)], gen2.frontends),
        'count': 1,
        'cmddir': '.',
        'start': 'sktask_gtk.py --channels=taskmgr0,g2task --display=%s --loglevel=info --log=%s' % (
            xscreen(gen2.disp.ul), get_log('sktask_gtk.log')),
        'flags': ('prefer', 'nosvccheck'),
        },

    "telstat": {
        'level': 10,
        'hosts': prefer([right(gen2.frontends)], gen2.frontends),
        'count': 1,
        'rundir': g2soss.dirload,
        'cmddir': '.',
        'start': 'telstat.py --nopg --stderr --geometry=+20+100 --display=%s' % (
            xscreen(gen2.disp.ur)),
        'stdout': get_log('telstat_stdout.log'),
        'flags': ('prefer'),
        },

    "envmon": {
        'level': 10,
        'hosts': prefer([left(gen2.frontends)], gen2.frontends),
        'count': 1,
        'rundir': g2soss.dirload,
        'cmddir': '.',
        'start': 'envmon.py --nopg --stderr --geometry=433x742-84-87 --display=%s' % (
            xscreen(gen2.disp.ul)),
        'stdout': get_log('envmon_stdout.log'),
        'flags': ('prefer'),
        },

    "insmon": {
        'level': 15,
        'hosts': prefer([left(gen2.frontends)], gen2.frontends),
        'count': 1,
        'rundir': g2soss.dirload,
        'cmddir': '.',
        'start': 'insmon.py --nopg --stderr --geometry=433x742-84-87 --display=%s' % (
            xscreen(gen2.disp.ul)),
        'stdout': get_log('insmon_stdout.log'),
        'flags': ('prefer'),
        },

    "vgw": {
        'level': 10,
        'hosts': prefer([gen2.float.g2guide], gen2.frontends),
        'count': 1,
        'rundir': g2soss.dirload,
        'cmddir': '.',
        'start': 'startvgw.py --nopg --stderr --stathost=g2stat --gethost=g2stat --obchost=g2ins1 --obshost=g2ins1 --display=%s' % (
            xscreen(gen2.disp.ll)),
        'stdout': get_log('VGW_stdout.log'),
        'flags': ('prefer'),
        },

    "skymon": {
        'level': 15,
        'hosts': prefer([right(gen2.frontends)], gen2.frontends),
        'count': 1,
        'rundir': g2soss.dirload,
        'cmddir': '.',
        'start': 'skymonitor.py --nopg --stderr --loglevel=debug --port=9505 --display=%s --user=gen2' % (
            xscreen(gen2.disp.lr)),
        'stdout': get_log('skymon.log'),
        'flags': ('prefer'),
        },

    "hskymon": {
        'level': 10,
        'hosts': prefer([right(gen2.frontends)], gen2.frontends),
        'count': 1,
        'rundir': g2soss.dirload,
        'cmddir': '.',
        'start': 'hskymon.py --nopg --stderr --loglevel=debug --port=9506 --display=%s' % (
            xscreen(gen2.disp.lr)),
        'stdout': get_log('hskymon_stdout.log'),
        'flags': ('prefer'),
        },

    "qdas": {
        'level': 10,
        'hosts': prefer([mid(gen2.frontends)], gen2.frontends),
        'count': 1,
        'rundir': g2soss.dirload,
        'cmddir': '.',
        'start': 'qdas.py --nopg --svcname=OBC --port=9510 --display=%s --loglevel=debug --stderr' % (
            xscreen(gen2.disp.um)),
        'stdout': get_log('qdas_stdout.log'),
        'flags': ('prefer'),
        },

    "envmon2": {
        'level': 15,
        'hosts': prefer([left(gen2.frontends)], gen2.frontends),
        'count': 1,
        'cmddir': 'senvmon',
        'start': 'EnviMonitor.py --stderr --display=%s' % (
            xscreen(gen2.disp.ul)),
        'stdout': get_log('envmon2.log'),
        'flags': ('prefer'),
        },

}

# Add all instrument interfaces and simulators
for insname in ins_data.getNames():
    num = ins_data.getNumberByName(insname)

    gen2.svconfig[insname] = {
        'level': 50,
        'hosts': prefer([gen2.float.g2ins1], gen2.summit),
        'count': 1,
        'description': DESCR.INSint,
        'cmddir': '../SOSS/INSint',
        'start': 'INSint.py --obcpnum=%d --svcname=%s --interfaces=cmd,file --monitor=monitor --numthreads=50 --fitsdir=%s --myhost=g2ins1 --port=82%02d --inscfg=%s --loglevel=info --log=%s' % (
        num, insname, datadir(insname), num, dbdir()+'/inscfg',
        get_log('%s.log' % insname)),
        'flags': ('prefer'),
        }

#     # Simulated instrument
#     gen2.svconfig['%ssim' % insname] = {
#     'level': 99,
#     'hosts': gen2.hosts,
#     'count': 1,
#     'description': DESCR.SIMCAM,
#     'cmddir': '../SIMCAM',
#     'start': 'simcam.py --cam=%s=GENERIC --obcpnum=%d --paradir=../SOSS/SkPara/cmd --gen2host=localhost --stderr --loglevel=debug' % (insname, num),
#     'stdout': get_log('%ssim.log' % insname),
#     'flags': ('fixed', 'nosvccheck'),
#     }

config = gen2

#END

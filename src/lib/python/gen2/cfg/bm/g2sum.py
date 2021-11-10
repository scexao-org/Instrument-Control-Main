# For compatibility mode front ends
import cfg.g2soss as g2soss
import os
from common import *

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
    tcsint=Bunch(addr='192.168.103.141', mask='255.255.255.0', dev='vlan103:1'),
    tcsint2=Bunch(addr='192.168.103.142', mask='255.255.255.0', dev='vlan103:2'),
    agint=Bunch(addr='192.168.106.141', mask='255.255.255.0', dev='vlan106:1'),
    nfs=Bunch(addr='133.40.167.8', mask='255.255.255.0', dev='vlan167:2'),
    g2stat=Bunch(name='g2stat', mask='255.255.255.0', dev='vlan167:3'),
    g2ins1=Bunch(name='g2ins1', mask='255.255.255.0', dev='vlan167:4'),
    g2ins2=Bunch(name='g2ins2', mask='255.255.255.0', dev='vlan167:5'),
    g2guide=Bunch(name='g2guide', mask='255.255.255.0', dev='vlan167:6'),
    g2db=Bunch(name='g2db', mask='255.255.255.0', dev='vlan167:7'),
    )

# Gen2 hosts
# NOTES:
#   - 'g2stat' and 'tcsint' attributes must run on the same node
#   - for performance reasons, 'nfs' and 'g2ins1' should run on the
#       same node and that should be one with an external RAID6
#       controller (currently only g2s3 or g2s4) 
gen2.managers = populate(
    # cluster, real hosts
    c1=Bunch(host='g2s1', alt=['agint', 'g2db']),
    #c2=Bunch(host='g2s2', alt=['g2ins2']),
    c3=Bunch(host='g2s3', alt=['g2ins1', 'tcsint2', 'nfs' ]),
    c4=Bunch(host='g2s4', alt=['g2guide', 'g2stat', 'tcsint']),
    cb1=Bunch(host='g2b2'),
    #cb2=Bunch(host='g2b1'),

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
gen2.be2 = 'c1'
gen2.be3 = 'c3'
gen2.be4 = 'c4'
gen2.bb1 = 'cb1'
#gen2.bb2 = 'cb2'

gen2.summit = list(set([gen2.be1, gen2.be2, gen2.be3, gen2.be4]))
#gen2.base   = list(set([gen2.bb1, gen2.bb2]))
gen2.base   = list(set([gen2.bb1]))
#gen2.backends = gen2.summit
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
gen2.disp.s6 = '%s:6' % host(gen2, gen2.fe3)
gen2.disp.s5 = '%s:5' % host(gen2, gen2.fe3)
gen2.disp.s4 = '%s:4' % host(gen2, gen2.fe2)
gen2.disp.s3 = '%s:3' % host(gen2, gen2.fe2)
gen2.disp.s2 = '%s:2' % host(gen2, gen2.fe1)
gen2.disp.s1 = '%s:1' % host(gen2, gen2.fe1)

gen2.screens = gen2.disp.keys()

gen2.hosts = list(set(gen2.backends + gen2.frontends))

gen2.basedir = gen2home

# NOTES:
#   - for performance reasons, fitsviewers and Archiver should run on 
#     the node providing the 'g2ins1' attribute
#   - currently, SessionManager mounts the ana host so that integgui2
#       and hskymon can access the OPE files in user accounts.  For that 
#       reason all three of these applications should run on the same
#       node
gen2.svconfig = {

    "mgrsvc": {                # Name of the service
        'level': 0,            # what level does it belong to
        'hosts': gen2.hosts,

        'count': len(gen2.hosts),  # how many instances should I start
        'description': DESCR.mgrsvc,
                               # what is the path to the executable from
                               # the base directory
        'cmddir': '../remoteObjects',
                               # command to start the program 
        'start': 'remoteObjectManagerSvc.py --detach --logdir=%s --logbyhostname --log=ro_mgrsvc.log --output=ro_mgrsvc_stdout.log --loglevel=info' % (
            logdir()),
        'flags': (),           # special notes to BootManager
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

    "monitor": {
        'level': 2,
        #'hosts': gen2.backends,
        'hosts': prefer([gen2.be1], gen2.summit),
        'count': 1,
        'description': DESCR.monitor,
        'cmddir': '../remoteObjects',
        'start': 'PubSub.py --port=7080 --svcname=monitor --config=cfg.pubsub --loglevel=info --log=%s' % (get_log('monitor.log')),
        'flags': ('prefer'),
        },

    "monlog": {
        'level': 2,
        #'hosts': gen2.backends,
        'hosts': prefer([gen2.float.nfs], gen2.summit),
        'count': 1,
        'description': DESCR.monitor,
        'cmddir': '.',
        'start': 'monlog.py --port=7082 --svcname=monlog --loglevel=debug --log=%s' % (get_log('monlog.log')),
        'flags': ('prefer'),
        },

    "names": {
        'level': 1,
        'hosts': gen2.hosts,
        'count': len(gen2.hosts),
        'description': DESCR.names,
        'cmddir': '../remoteObjects',
        # NOTE: --monitor should point at host where PubSub is running!
        # 'start': 'remoteObjectNameSvc.py --monport=7077 --monitor=%s:7080 --monauth=monitor:monitor --logdir=%s --logbyhostname --log=ro_names.log --loglevel=info' % (
        'start': 'remoteObjectNameSvc.py --monport=7077 --monitor=%s:7077 --monauth=monitor:monitor --logdir=%s --logbyhostname --log=ro_names.log --loglevel=info' % (
            host(gen2, gen2.be1), logdir()),
        'flags': ('each'),
        },

    "bootmgr": {
        'level': 3,
        'hosts': gen2.summit,
        'count': 1,
        'description': DESCR.bootmgr,
        'cmddir': '.',
        'start': 'BootManager.py --config=g2sum --port=8090 --svcname="bootmgr" --loglevel=info --log=%s' % (get_log('bootmgr.log')),
        'flags': ('random'),
        },

    # "g2web": {
    #     'level': 3,
    #     #'hosts': prefer([gen2.float.g2ins1], gen2.summit),
    #     'hosts': [gen2.be3],
    #     'count': 1,
    #     'description': "The Gen2 web interface",
    #     'cmddir': 'web',
    #     'start': "g2web.py --config=g2sum --cert=%(dbdir)s/g2cert.pem --auth_users='ocs:g2/ocs' --plugins=bm,dsp,sm,data,tsc,frame --docroot=$GEN2HOME/docs --loglevel=info --log=%(log)s",
    #     'log':   get_log('g2web.log'),
    #     'dbdir': dbdir(),
    #     'flags': ('prefer'),
    #     },

    # This is the status server
    "status": {
        'level': 3,
        'hosts': prefer([gen2.float.tcsint], gen2.summit),
        'count': 1,
        'description': DESCR.status,
        'cmddir': '../SOSS/status',
        'start': 'status.py --svcname=status --port=8151 --monitor=monitor --myhost=g2stat --loglevel=info --log=%(log)s --logmon=monlog --checkpt=%(dbdir)s/status.cpt --loghome=%(loghome)s',
        'log'  : get_log('status.log'),
        # for status rpc dumps
        'loghome': '/gen2/logs',
        'dbdir': dbdir(),
        'flags': ('prefer'),
        },

    # AG/SV/SH/FMOS autoguider splitter.
    "agsplit": {
        'level': 2.5,
        'hosts': prefer([gen2.float.agint], gen2.summit),
        'count': 1,
        'description': """This is the AG/SV/SH splitter software.  It sends the
images coming from the guider cameras to both SOSS and Gen2.""",
        'rundir': os.path.join(g2soss.archhome, 'bin'),
        'cmddir': '.',
        'start': 'agsplit.py --nopg %s' % ('g2guide.sum.subaru.nao.ac.jp'),
        'stdout': get_log('agsplit.log'),
        'flags': ('fixed', 'nosvccheck'),
        },

    # Star Catalogs
    "starcat": {
        'level': 1.5,
        'hosts': prefer([gen2.be1], gen2.backends),
        'count': 1,
        'description': DESCR.starcat,
        'rundir': '%s' % (starcatdir()),
        'cmddir': '/usr/bin',
        'start': 'sudo -u postgres /usr/lib/postgresql/8.4/bin/postgres -p 5436 -D %s/8_4db' % (starcatdir()),
        'stop': 'sudo -u postgres /usr/lib/postgresql/8.4/bin/pg_ctl stop -D %s/8_4db -m fast' % (starcatdir()),
        'stdout': get_log('starcat.log'),
        'flags': ('fixed', 'nosvccheck'),
        },

    "starcat1": {
        'level': 1.5,
        'hosts': prefer([gen2.be1], gen2.backends),
        'count': 1,
        'description': DESCR.starcat,
        'rundir': '%s' % (starcatdir()),
        'cmddir': '/usr/bin',
        'start': 'sudo -u postgres /usr/lib/postgresql/8.4/bin/postgres -p 5433 -D %s/8_4db1' % (starcatdir()),
        'stop': 'sudo -u postgres /usr/lib/postgresql/8.4/bin/pg_ctl stop -D %s/8_4db1 -m fast' % (starcatdir()),
        'stdout': get_log('starcat1.log'),
        'flags': ('fixed', 'nosvccheck'),
    },

    "starcat2": {
        'level': 1.5,
        'hosts': prefer([gen2.be1], gen2.backends),
        'count': 1,
        'description': DESCR.starcat,
        'rundir': '%s' % (starcatdir()),
        'cmddir': '/usr/bin',
        'start': 'sudo -u postgres /usr/lib/postgresql/8.4/bin/postgres -p 5434 -D %s/8_4db2' % (starcatdir()),
        'stop': 'sudo -u postgres /usr/lib/postgresql/8.4/bin/pg_ctl stop -D %s/8_4db2 -m fast' % (starcatdir()),
        'stdout': get_log('starcat2.log'),
        'flags': ('fixed', 'nosvccheck'),
        },

    "starcat3": {
        'level': 1.5,
        'hosts': prefer([gen2.be1], gen2.backends),
        'count': 1,
        'description': DESCR.starcat,
        'rundir': '%s' % (starcatdir()),
        'cmddir': '/usr/bin',
        'start': 'sudo -u postgres /usr/lib/postgresql/8.4/bin/postgres -p 5435 -D %s/8_4db3' % (starcatdir()),
        'stop': 'sudo -u postgres /usr/lib/postgresql/8.4/bin/pg_ctl stop -D %s/8_4db3 -m fast' % (starcatdir()),
        'stdout': get_log('starcat3.log'),
        'flags': ('fixed', 'nosvccheck'),
        },

    "g2db": {
        'level': 1.5,
        'hosts': prefer([gen2.float.nfs], gen2.summit),
        'count': 1,
        'description': "Postgres database instance for the Gen2 general database.",
        'start': '/usr/lib/postgresql/8.4/bin/postgres -p 5440 -D /gen2/data/g2db/pg8_4',
        'stop': '/usr/lib/postgresql/8.4/bin/pg_ctl stop -p 5440 -D /gen2/data/g2db/pg8_4 -m fast',
        'stdout': get_log('g2db_stdout.log'),
        'flags': ('fixed', 'nosvccheck'),
        },

    # STSradio and omsa_logger
    "STSradio": {
        'level': 1.5,
        'hosts': gen2.hosts,
        'count': len(gen2.hosts),
        'description': """This is the STS radio reporting software.  It reports
information to the Subaru Telemetry System.""",
        'rundir': '../tools/dell_omsa',
        'cmddir': '.',
        'start': 'STSradio_wrapper.sh STSradio DellOMSA_STS.config',
        'flags': ('fixed', 'nosvccheck'),
        },

    "omsa_logger": {
        'level': 1.5,
        'hosts': gen2.hosts,
        'count': len(gen2.hosts),
        'description': """This is the Dell OMSA logging system.""",
        'cmddir': '../tools/dell_omsa',
        'start': 'omsa_logger.py --logdir /gen2/logs',
        'stdout': get_log('omsa_logger_stdout.log'),
        'flags': ('fixed', 'nosvccheck'),
        },

    # Star Catalogs
    "starcat_pool": {
        'level': 2.5,
        'hosts': prefer([gen2.be1], gen2.backends),
        'count': 1,
        'description': DESCR.starcat,
        'rundir': '%s' % (starcatdir()),
        'cmddir': '/usr/bin',
        'start': 'sudo -u postgres /usr/sbin/pgpool -n -f %s/pgpool.conf' % (starcatdir()),
        'stop': 'sudo -u postgres /usr/sbin/pgpool -f %s/pgpool.conf -m fast stop' % (starcatdir()),
        'stdout': get_log('starcat_pool.log'),
        'flags': ('fixed', 'nosvccheck'),
        },

    # DSS Server
    "dss_server": {
        'level': 2.5,
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
        # same machine as integgui2
        'hosts': prefer([mid(gen2.frontends)], gen2.frontends),
        #'hosts': [mid(gen2.frontends)],
        'count': 1,
        'description': DESCR.sessions,
        'cmddir': '.',
        'start': 'SessionManager.py --port=8105 --svcname="sessions" --ampd --log=%(log)s --loglevel=debug --logmon=monlog --db=%(dbdir)s/sessiondb-gen2',
        'log'  : get_log('sessions.log'),
        'dbdir': dbdir(),
        'flags': ('prefer'),
        },

    # This is the alarm_handler, which monitors and reports alarms
    # from the incoming TSC feed.
    "alarm_handler": {
        'level': 4,
        'hosts': gen2.summit,
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
        #'hosts': gen2.summit,
        'hosts': prefer([gen2.be1], gen2.summit),
        'count': 1,
        'description': DESCR.taskmgr,
        'cmddir': '.',
        'start': 'TaskManager.py --port=8170 --svcname="taskmgr0" --monitor=monitor --session=main --numthreads=120 --stderr --loglevel=info --logmon=monlog --log=%(log_d)s:debug',
        'log_d' : get_log('taskmgr0_debug.log'),
        'stdout': get_log('taskmgr0.log'),
        'flags': ('prefer'),
        },

    "archiver": {
        'level': 5,
        #'hosts': gen2.summit,
        'hosts': prefer([gen2.float.nfs], gen2.summit),
        'count': 1,
        'cmddir': '.',
        'description': DESCR.archiver,
        'start': 'Archiver.py --monitor=monitor --svcname=archiver --realm=summit --nomd5check --port=8104 --monport=15104 --inscfg=%(inscfg)s --server --loglevel=info --log=%(log)s --logmon=monlog',
        'log'  : get_log('archiver.log'),
        'inscfg': dbdir()+'/inscfg',
        'flags': ('prefer'),
        },
    
    "gen2base": {
        'level': 5,
        #'hosts': gen2.base,
        'hosts': prefer([gen2.bb1], gen2.backends),
        'count': 1,
        'cmddir': '.',
        'description': DESCR.archiver,
        'start': 'Archiver.py --monitor=monitor --svcname=gen2base --realm=base --port=8106 --monport=15106 --server --nomd5check --keyfile=%(keyf)s --datadir=/mnt/raid6base_data --pullhost=g2ins1 --pullname=gen2 --pullmethod=copy --loglevel=info --log=%(log)s --logmon=monlog',
        'keyf' : get_key('gen2base'),
        'log'  : get_log('gen2base.log'),
        'flags': ('prefer'),
        },
    
    "session-proxy": {
        'level': 6,
        #'hosts': gen2.base,
        'hosts': prefer([gen2.bb1], gen2.backends),
        'count': 1,
        'cmddir': '.',
        'description': "Proxy for the SessionManager for non-summit datasinks",
        'start': 'SessionProxy.py --svcname=session-proxy --port=8167 --loglevel=info --log=%(log)s',
        'log'  : get_log('session-proxy.log'),
        'flags': ('prefer'),
        },
    
    "soundsink": {
        'level': 4,
        'hosts': gen2.summit,
        'count': 1,
        'cmddir': '.',
        'description': "Sound drop off point for distributing audio",
        'start': 'soundsink.py --monitor=monitor --svcname=sound --port=15051 --monport=15052 --loglevel=info --log=%(log)s',
        'log'  : get_log('soundsink.log'),
        'flags': ('random'),
        },
    
    # This is the STARS interface ##   
    "STARS": {
        'level': 6,
        #'hosts': gen2.base,
        'hosts': prefer([gen2.bb1], gen2.summit),
        'count': 1,
        'description': DESCR.STARSint,
        'cmddir': '../SOSS/STARSint',
        'start': 'STARSint.py --monitor=monitor --channels=3,4 --svcname=STARS  --port=8121 --keyfile=%(keyf)s  --loglevel=info --log=%(log)s --logmon=monlog',
        'keyf' : get_key('stars'),
        'log'  : get_log('STARS.log'),
        'flags': ('prefer'),
        },

    # This is the STARS simulator (s01)
    "STARSsim": {
        'level': 40.1,
        'hosts': gen2.base,
        'count': 1,
        'description': DESCR.STARSsim,
        'cmddir': '../SOSS/STARSint',
        'start': 'STARSsim.py --channels=7,8 --dir=%(ddir)s --loglevel=info --log=%(log)s',
        'ddir' : datadir('STARS'),
        'log'  : get_log('STARSsim.log'),
        'flags': ('random', 'nosvccheck'),
        },
    
    # This is the frame service interface
    "frames": {
        'level': 4.1,
        #'hosts': gen2.summit,
        'hosts': prefer([gen2.float.nfs], gen2.summit),
        'count': 1,
        'description': DESCR.frames,
        'cmddir': '.',
        'start': 'frameSvc.py --server --port=8161 --monport=15161 --svcname=frames --monitor=monitor --log=%(log)s --loglevel=info --logmon=monlog',
        'log'  : get_log('frames.log'),
        'flags': ('prefer'),
        },
    
    # # This is the frame service interface with proxy to SOSS
    # "frames0": {
    #     'level': 40.1,
    #     #'hosts': gen2.summit,
    #     'hosts': prefer([gen2.float.nfs], gen2.summit),
    #     'count': 1,
    #     'description': DESCR.frames,
    #     'cmddir': '.',
    #     'start': 'frameSvc.py --server --port=8161 --monport=15161 --svcname=frames --monitor=monitor --proxy=obs.sum.subaru.nao.ac.jp --loglevel=debug --log=%(log)s --logmon=monlog',
    #     'log'  : get_log('frames.log'),
    #     'flags': ('prefer'),
    #     },

    "g2ag": {
        'level': 12,
        'hosts': prefer([gen2.float.g2guide], gen2.backends),
        'count': 1,
        'cmddir': '../SIMCAM',
        'start': 'g2cam.py --cam=VGW --obcpnum=33 --gen2host=g2ins1 --loglevel=debug --seppuku --log=%(log)s',
        'log'  : get_log('g2ag.log'),
        'stdout': get_log('g2ag_stdout.log'),
        'flags': ('prefer'),
        },

    # TCS interface
    "TSC0": {
        'level': 4.1,
        'hosts': prefer([gen2.float.tcsint], gen2.summit),
        'count': 1,
        'description': DESCR.TSC,
        'cmddir': '../SOSS/TCSint',
        'start': 'TCSint2.py --svcname=TSC --monitor=monitor --numthreads=70 --port=8141 --tcshost=tsc --loglevel=info --log=%(log)s --logmon=monlog',
        'log'  : get_log('TSC.log'),
        'flags': ('prefer'),
        },
    
    # TCS interface
    "fakeTSC": {
        'level': 40.1,
        'hosts': prefer([gen2.float.tcsint], gen2.summit),
        'count': 1,
        'description': DESCR.TSC,
        'cmddir': '../SOSS/TCSint',
        'start': 'TCSint2.py --svcname=TSC --monitor=monitor --numthreads=100 --port=8141 --tcshost=localhost --loglevel=info --log=%(log)s --logmon=monlog',
        'log'  : get_log('TSC.log'),
        'flags': ('prefer'),
        },

    # TSC simulator
    "TSCsim": {
        'level': 40.1,
        'hosts': prefer([gen2.float.tcsint], gen2.summit),
        'count': 1,
        'description': DESCR.TSC,
        'cmddir': '../SOSS/TCSint',
        'start': 'TCSint2.py --sim --loglevel=info --log=%(log)s',
        'log'  : get_log('TSCsim.log'),
        'flags': ('prefer', 'nosvccheck'),
        },

   # starcatalog with remoteobject 
    "starcatalog": {
        'level': 12,
        'hosts': prefer([gen2.be1], gen2.backends),
        'count': 1,
        'description': DESCR.starcat,
        'cmddir': 'starlist',
        'start': 'starcatalog.py --loglevel=debug --log=%(log)s --port=8888',
        'log': get_log('starcatalog.log'),
        'flags': ('prefer'),
        },

    # This fetches UT1_UTC tables
    "ut1-utc": {
        'level': 90,
        'hosts': gen2.backends,
        'count': 1,
        'description': DESCR.ut1_utc,
        'periodic': calc_cron(wday=[0], hr=[12], min=[10]),
        'cmddir': '../SOSS/status',
        'start': 'get-ut1utc.py --loglevel=debug --log=%(log)s',
        'log'  : get_log('ut1_utc.log'),
        'flags': ('random', 'nosvccheck'),
        },

    # This handles the tomorrow-2am file for TSC
    "get2am": {
        'level': 90,
        #'hosts': gen2.backends,
        'hosts': prefer([gen2.float.g2ins1], gen2.summit),
        #'hosts': [gen2.float.g2ins1],
        'count': 1,
        'description': "Generates the tomorrow-2am weather file for TSC",
        'periodic': calc_cron(hr=[10,12,14], min=[0]),
        'rundir': '/gen2/home/tsc',
        'cmddir': gen2home + '/../tools',
        'start': 'get2am.py --dbfile=get2am.db --tscfile=tomorrow-2am.txt --loglevel=20 --log=%(log)s',
        'log'  : get_log('get2am.log'),
        'flags': ('prefer', 'nosvccheck'),
        },

    # send taskmgr0-logs to STARS at 11:30 am every day.
    "send-tasklog": {
        'level': 90,
        'hosts': prefer([gen2.be1], [gen2.be1]),
        'count': 1,
        'cmddir': 'util',
        'start': 'gen2log.py --act=tasklog --loglevel=debug --log=%(log)s',
        'log'  : get_log('sendtask.log'),
        #'periodic': calc_future(86400, hr=12, min=0),
        'periodic': calc_cron(hr=[11], min=[30]),
        'flags': ('prefer'),
        },


    # send tsc-cmd-log to STARS at 11:40 am every day.
    "send-tsccmdlog": {
        'level': 90,
        'hosts': prefer([gen2.be4], [gen2.be4]),
        'count': 1,
        'cmddir': 'util',
        'start': 'gen2log.py --act=tsccmdlog --loglevel=debug --log=%(log)s',
        'log'  : get_log('sendtsccmd.log'),
        #'periodic': calc_future(86400, hr=12, min=0),
        'periodic': calc_cron(hr=[11], min=[40]),
        'flags': ('prefer'),
        },

    # send status-log to STARS at 11:50 am every day.
    "send-statuslog": {
        'level': 90,
        'hosts': prefer([gen2.be4], [gen2.be4]),
        'count': 1,
        'cmddir': 'util',
        'start': 'gen2log.py --act=statlog --loglevel=debug --log=%(log)s',
        'log'  : get_log('sendstatus.log'),
        #'periodic': calc_future(86400, hr=12, min=0),
        'periodic': calc_cron(hr=[11], min=[50]),
        'flags': ('prefer'),
        },

    # send tsc-status-logs to STARS at 12:00 pm every day.
    "send-tscstatlog": {
        'level': 90,
        'hosts': prefer([gen2.float.nfs], gen2.summit),
        'count': 1,
        'cmddir': 'util',
        'start': 'gen2log.py --act=tscstatlog --loglevel=debug --log=%(log)s',
        'log'  : get_log('sendtscstat.log'),
        #'periodic': calc_future(86400, hr=12, min=0),
        'periodic': calc_cron(hr=[12], min=[00]),
        'flags': ('prefer'),
        },

    # send taskmgr0_debug-logs to STARS at 12:10 pm every day.
    "send-taskdebuglog": {
        'level': 90,
        'hosts': prefer([gen2.be1], [gen2.be1]),
        'count': 1,
        'cmddir': 'util',
        'start': 'gen2log.py --act=taskdebuglog --loglevel=debug --log=%(log)s',
        'log'  : get_log('sendtaskdebug.log'),
        #'periodic': calc_future(86400, hr=12, min=0),
        'periodic': calc_cron(hr=[12], min=[10]),
        'flags': ('prefer'),
        },


    # send stars-logs to STARS at 12:20 pm every day.
    "send-starslog": {
        'level': 90,
        'hosts': prefer([gen2.bb1], gen2.base),
        'count': 1,
        'cmddir': 'util',
        'start': 'gen2log.py --act=starslog --loglevel=debug --log=%(log)s',
        'log'  : get_log('sendstars.log'),
        #'periodic': calc_future(86400, hr=12, min=0),
        'periodic': calc_cron(hr=[12], min=[20]),
        'flags': ('prefer'),
        },

    # send end-log to STARS at 12:30 pm every day.
    "send-endlog": {
        'level': 90,
        'hosts': prefer([gen2.float.nfs], gen2.summit),
        'count': 1,
        'cmddir': 'util',
        'start': 'gen2log.py --act=endlog --loglevel=debug --log=%(log)s',
        'log'  : get_log('sendend.log'),
        #'periodic': calc_future(86400, hr=12, min=0),
        'periodic': calc_cron(hr=[12], min=[30]),
        'flags': ('prefer'),
        },

    
    # delete gen2 logs which are over 30 days old,  
    # run it at 13:00 every day  
    "delete-log": {
        'level': 90,
        'hosts': prefer([gen2.float.nfs], gen2.summit),
        'count': 1,
        'cmddir': 'util',
        'start': 'gen2log.py --act=deletelog --age=30 --loglevel=debug --log=%(log)s',
        'log':  get_log('deletelog.log'),
        #'periodic': calc_future(86400, hr=13, min=0),
        'periodic': calc_cron(hr=[13], min=[0]),
        'flags': ('prefer'),
        },

    "missedframe": {
        'level': 90,
        'hosts': prefer([gen2.bb1], gen2.base),
        'count': 1,
        'cmddir': 'util',
        'start': 'missedframe.py --loglevel=debug --log=%(log)s',
        'log':  get_log('missedframe.log'),
        #'periodic': calc_future(86400, hr=11, min=0),
        'periodic': calc_cron(hr=[11], min=[0]),
        'flags': ('prefer'),
        },
  
    "cleanupFitsGui": {
        'level': 90,
        'hosts': prefer([gen2.bb1], gen2.base),
        'count': 1,
        'cmddir': '../tools/cleanfits',
        'start': 'cleanfits.py --loglevel=debug --log=%(log)s --display=%(xdisp)s',
        'xdisp' : gen2.disp.s1,
        'log':  get_log('cleanfits.log'),
        'screens': gen2.screens, 
        'flags': ('prefer'),
        },
  
    "agsim": {
        'level': 90,
        'hosts': prefer([gen2.float.g2guide], gen2.frontends),
        'count': 1,
        'cmddir': '../tools',
        'start': 'agsim.py --loglevel=debug --log=%(log)s --display=%(xdisp)s',
        'xdisp' : gen2.disp.s6,
        'log'   : get_log('agsim.log'),
        'stdout': get_log('agsim_stdout.log'),
        'screens': gen2.screens,
        'flags': ('prefer'),
    },

    "alarm_gui": {
        'level': 90,
        'hosts': prefer([right(gen2.frontends)], gen2.frontends),
        'count': 1,
        'cmddir': 'alarm',
        'start': 'alarm_gui.py --configfile "../cfg/alarm/*_alarm_cfg.yml" --log=%(log)s --display=%(xdisp)s',
        'xdisp': gen2.disp.s2,
        'screens': gen2.screens,
        'log'  : get_log('alarm_gui.log'),
        'stdout': get_log('alarm_gui_stdout.log'),
        'flags': ('prefer'),
        },

    "monarch": {
        'level': 99,
        #'hosts': gen2.backends,
        'hosts': gen2.summit,
        'count': 1,
        'description': DESCR.monitor,
        'cmddir': '..',
        'start': 'Monitor.py --port=9009 --svcname=monarch --loglevel=debug --log=%(log)s',
        'log'  : get_log('monarch.log'),
        'flags': ('random'),
        },

    # *** USER INTERFACE INFRASTRUCTURE ***

    # Lower Left display in a two-display setup
    "vncs-s5": {
        'level': 8,
        'hosts': prefer([left(gen2.frontends)], gen2.frontends),
        'count': 1,
        'cmddir': './util',
        'start': 'startvnc.py 5',
        'stdout': get_log('s5_stdout.log'),
        'flags': ('fixed', 'manual'),
        },

    # Upper Left display in a two-display setup
    "vncs-s6": {
        'level': 8,
        'hosts': prefer([left(gen2.frontends)], gen2.frontends),
        'count': 1,
        #'start': 'mytightvncserver %s  -dpi 100 -depth 24 -geometry 1910x1165 -alwaysshared' % (screen(gen2.disp.s6)),
        'cmddir': './util',
        'start': 'startvnc.py 6',
        #'stop': '/usr/bin/tightvncserver -kill %s' % (screen(gen2.disp.s6)),
        'stdout': get_log('s6_stdout.log'),
        'flags': ('fixed', 'manual'),
        },

    # Lower Middle display in a two-display setup
    "vncs-s3": {
        'level': 8,
        'hosts': prefer([mid(gen2.frontends)], gen2.frontends),
        'count': 1,
        'cmddir': './util',
        'start': 'startvnc.py 3',
        'stdout': get_log('s3_stdout.log'),
        'flags': ('fixed', 'manual'),
        },

    # Upper Middle display in a two-display setup
    "vncs-s4": {
        'level': 8,
        'hosts': prefer([mid(gen2.frontends)], gen2.frontends),
        'count': 1,
        'cmddir': './util',
        'start': 'startvnc.py 4',
        'stdout': get_log('s4_stdout.log'),
        'flags': ('fixed', 'manual'),
        },

    # Lower Right display in a two-display setup
    "vncs-s1": {
        'level': 8,
        'hosts': prefer([right(gen2.frontends)], gen2.frontends),
        'count': 1,
        'cmddir': './util',
        'start': 'startvnc.py 1',
        'stdout': get_log('s1_stdout.log'),
        'flags': ('fixed', 'manual'),
        },

    # Upper Right display in a two-display setup
    "vncs-s2": {
        'level': 8,
        'hosts': prefer([right(gen2.frontends)], gen2.frontends),
        'count': 1,
        'cmddir': './util',
        'start': 'startvnc.py 2',
        'stdout': get_log('s2_stdout.log'),
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

    # *** SOSS COMPATIBILITY MODE FRONT ENDS ***

    "integgui2" : {
        'level' : 10,
        # Same machine as 'sessions'
        'hosts' : prefer([mid(gen2.frontends)], gen2.frontends),
        'count' : 1,
        'cmddir': 'integgui2',
        'start' : 'integgui2.py --taskmgr=taskmgr0 --session=main --display=%(xdisp)s --port=10232 --monport=10233 --loglevel=info --logmon=monlog --log=%(log)s',
        'xdisp' : gen2.disp.s3,
        'log'   : get_log('integgui2.log'),
        'stdout': get_log('integgui2_stdout.log'),
        'screens': gen2.screens,
        'flags' : ('prefer'),
        },

    # New fits viewer
    "fitsview": {
        'level': 10,
        # file performance
        'hosts': prefer([gen2.float.nfs], gen2.frontends),
        'count': 1,
        'rundir': gen2home + '/../../Fitsview',
        #'rundir': gen2home + '/Fitsview',
        'cmddir': '.',
        #'start': 'fitsview.py --svcname=fitsview --bufsize=10 --port=9502 --monport=10502 --monchannels=fits --geometry=+866+545 --display=%(xdisp)s --loglevel=warn --log=%(log)s',
        'start': 'fitsview.py --svcname=fitsview --bufsize=10 --port=9502 --monport=10502 --monitor=monitor --monchannels=fits --modules=QDAS --plugins=Region_Selection,Sv_Drive,FocusFit --geometry=+866+545 --display=%(xdisp)s --loglevel=info --log=%(log)s',
        'xdisp' : gen2.disp.s4,
        'log'   : get_log('fitsview.log'),
        'stdout': get_log('fitsview_stdout.log'),
        'screens': gen2.screens,
        'flags': ('prefer'),
        },

    # New fits viewer
    "fitsview-test": {
        'level': 80,
        # file performance
        'hosts': prefer([gen2.float.nfs], gen2.frontends),
        'count': 1,
        'rundir': gen2home + '/../../Fitsview',
        #'rundir': gen2home + '/Fitsview',
        'cmddir': '.',
        #'start': 'fitsview.py --svcname=fitsview --bufsize=10 --port=9502 --monport=10502 --monchannels=fits --geometry=+866+545 --display=%(xdisp)s --loglevel=warn --log=%(log)s',
        'start': 'fitsview.py --svcname=fitsview --bufsize=10 --port=9502 --monport=10502 --monitor=monitor --monchannels=fits --modules=QDAS --plugins=Region_Selection,Sv_Drive,FocusFit --geometry=+866+545 --display=%(xdisp)s --loglevel=info --log=%(log)s',
        'xdisp' : gen2.disp.s4,
        'log'   : get_log('fitsview.log'),
        'screens': gen2.screens,
        'flags': ('prefer'),
        },

    # New guide interface
    "guideview": {
        'level': 12,
        'hosts': prefer([gen2.float.g2guide], gen2.frontends),
        'count': 1,
        'rundir': gen2home + '/../../Fitsview',
        #'rundir': gen2home + '/Fitsview',
        'cmddir': '.',
        'start': 'guideview.py --svcname=guideview --bufsize=2 --port=9522 --monport=10522 --display=%(xdisp)s --loglevel=info --log=%(log)s',
        'xdisp' : gen2.disp.s5,
        'log'   : get_log('guideview.log'),
        'stdout'   : get_log('guideview_stdout.log'),
        'screens': gen2.screens,
        'flags': ('prefer'),
        },

    "hskymon": {
        'level': 10,
        # Same machine as 'sessions'
        'hosts': prefer([mid(gen2.frontends)], gen2.frontends),
        'count': 1,
        'rundir': os.path.join(g2soss.archhome, 'bin'),
        'cmddir': '.',
        'start': 'hskymon.py --nopg --stderr --loglevel=debug --port=9506 --display=%(xdisp)s',
        'xdisp' : gen2.disp.s1,
        'stdout': get_log('hskymon_stdout.log'),
        'screens': gen2.screens,
        'flags': ('prefer'),
        },

    # All instruments are switched over to the new QDAS tasks.
    # "qdas": {
    #     'level': 10,
    #     'hosts': prefer([mid(gen2.frontends)], gen2.frontends),
    #     'count': 1,
    #     'rundir': g2soss.dirload,
    #     'cmddir': '.',
    #     'start': 'qdas.py --nopg --svcname=OBC --port=9510 --display=%(xdisp)s --loglevel=debug --stderr',
    #     'stdout': get_log('qdas_stdout.log'),
    #     'xdisp' : gen2.disp.s4,
    #     'screens': gen2.screens,
    #     'flags': ('prefer'),
    #     },

    "statmon": {
        'level': 10,
        'hosts': prefer([left(gen2.frontends)], gen2.frontends),
        'count': 1,
        'cmddir': 'statmon',
        'start': 'statmon.py --display=%(xdisp)s --monport=34945 --loglevel=10 --log=%(log)s',
        'stop': gen2home + '/../remoteObjects/ro_shell.py -c statmon close_all_plugins',
        'xdisp' : gen2.disp.s6,
        'screens': gen2.screens,
        'stdout': get_log('statmon_stdout.log'),
        'log': get_log('statmon.log'),
        'flags': ('prefer'),
        },

    "vgw-gui": {
        'level': 11,
        'hosts': prefer([gen2.float.g2guide], gen2.frontends),
        'count': 1,
        'rundir': g2soss.dirload,
        'cmddir': '.',
        'start': 'startvgw.py --nopg --stderr --stathost=g2stat --gethost=g2stat --obchost=g2ins1 --obshost=g2ins1 --display=%(xdisp)s',
        'stdout': get_log('VGW_stdout.log'),
        'xdisp' : gen2.disp.s5,
        'screens': gen2.screens,
        'flags': ('prefer'),
        },

    # "sktask_gtk": {
    #     'level': 15,
    #     'hosts': prefer([left(gen2.frontends)], gen2.frontends),
    #     'count': 1,
    #     'cmddir': '.',
    #     'start': 'sktask_gtk.py --display=%(xdisp)s --loglevel=info --log=%(log)s',
    #     'xdisp' : gen2.disp.s6,
    #     'log'   : get_log('sktask_gtk.log'),
    #     'screens': gen2.screens,
    #     'flags': ('prefer', 'nosvccheck'),
    #     },

    "telstat": {
        'level': 10,
        'hosts': prefer([right(gen2.frontends)], gen2.frontends),
        'count': 1,
        'cmddir': 'telstat',
        'start': 'telstat.py --nopg --stderr --geometry=+20+100 --display=%(xdisp)s',
        'stdout': get_log('telstat_stdout.log'),
        'xdisp' : gen2.disp.s2,
        'screens': gen2.screens,
        'flags': ('prefer'),
        },

    # "oldfitsviewer": {
    #     'level': 15,
    #     'hosts': prefer([gen2.float.nfs], gen2.frontends),
    #     'count': 1,
    #     'rundir': g2soss.dirload,
    #     'cmddir': '.',
    #     'start': 'fitsviewer.py --nopg --svcname=fitsview1 --geometry=+816+28 --display=%(xdisp)s --port=9501 --monport=10501 --loglevel=10 --log=%(log)s',
    #     'xdisp' : gen2.disp.s6,
    #     'log'   : get_log('fitsviewer.log'),
    #     'screens': gen2.screens,
    #     'flags': ('prefer'),
    #     },

    "envmon2": {
        'level': 15,
        'hosts': prefer([left(gen2.frontends)], gen2.frontends),
        'count': 1,
        'cmddir': 'senvmon',
        'start': 'EnviMonitor.py --log=%(log)s --display=%(xdisp)s',
        'xdisp' : gen2.disp.s6,
        'log'   : get_log('envmon2.log'),
        'screens': gen2.screens,
        'flags': ('prefer'),
        },

    # "oldenvmon": {
    #     'level': 15,
    #     'hosts': prefer([left(gen2.frontends)], gen2.frontends),
    #     'count': 1,
    #     'cmddir': 'telstat',
    #     'start': 'envmon.py --nopg --stderr --geometry=433x742-84-87 --display=%(xdisp)s',
    #     'stdout': get_log('envmon_stdout.log'),
    #     'xdisp' : gen2.disp.s6,
    #     'screens': gen2.screens,
    #     'flags': ('prefer'),
    #     },

    "insmon": {
        'level': 15,
        'hosts': prefer([left(gen2.frontends)], gen2.frontends),
        'count': 1,
        'rundir': g2soss.dirload,
        'cmddir': '.',
        'start': 'insmon.py --nopg --stderr --geometry=433x742-84-87 --display=%(xdisp)s',
        'stdout': get_log('insmon_stdout.log'),
        'xdisp' : gen2.disp.s6,
        'screens': gen2.screens,
        'flags': ('prefer'),
        },

    # "skymon": {
    #     'level': 15,
    #     'hosts': prefer([right(gen2.frontends)], gen2.frontends),
    #     'count': 1,
    #     'rundir': g2soss.dirload,
    #     'cmddir': '.',
    #     'start': 'skymonitor.py --nopg --stderr --loglevel=debug --port=9505 --display=%(xdisp)s --user=gen2',
    #     'stdout': get_log('skymon.log'),
    #     'xdisp' : gen2.disp.s1,
    #     'screens': gen2.screens,
    #     'flags': ('prefer'),
    #     },

}

# Add all instrument interfaces and simulators
for insname in ins_data.getNames():
    num = ins_data.getNumberByName(insname)

    # QDAS display
    gen2.svconfig['%s_qdas' % insname] = {
        'level': 20,
        'hosts': prefer([gen2.float.nfs], gen2.frontends),
        'count': 1,
        'rundir': g2soss.dirload,
        'cmddir': '.',
        'start': 'skycat -name %sSkycat -display %%(xdisp)s' % insname,
        'xdisp': gen2.disp.s4,
        'stdout': get_log('skycat_%s_qdas.log' % insname),
        'screens': gen2.screens,
        'flags': ('prefer', 'nosvccheck'),
        }

    # skip VGW, temporarily
    if num == 33:
        continue
    gen2.svconfig[insname] = {
        'level': 50,
        'hosts': prefer([gen2.float.g2ins1], gen2.summit),
        'count': 1,
        'description': DESCR.INSint,
        'cmddir': '../SOSS/INSint',
        'start': 'INSint.py --obcpnum=%d --svcname=%s --interfaces=cmd,file --monitor=monitor --numthreads=50 --fitsdir=%s --myhost=g2ins1 --port=82%02d --inscfg=%s --loglevel=info --log=%%(log)s --logmon=monlog' % (
        num, insname, datadir(insname), num, dbdir()+'/inscfg'),
        'log'  : get_log(insname + '.log'),
        'flags': ('prefer'),
        }

gen2.svconfig['VGW'] = {
    'level': 11,
    'hosts': prefer([gen2.float.g2ins1], gen2.summit),
    'count': 1,
    'description': DESCR.INSint,
    'cmddir': '../SOSS/INSint',
    'start': 'INSint.py --obcpnum=33 --svcname=VGW --interfaces=cmd,file --monitor=monitor --numthreads=50 --fitsdir=%s --myhost=g2ins1 --port=8233 --inscfg=%s --loglevel=info --log=%%(log)s --logmon=monlog' % (
    datadir('VGW'), dbdir()+'/inscfg'),
    'log'  : get_log('VGW.log'),
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


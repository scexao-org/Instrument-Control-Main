from common import *
import remoteObjects as ro

#############################################################################
# CIAX CONFIGURATION
# Everything runs on one machine.
#############################################################################
ciax = Bunch()

ciax.managers = populate(
    h1=Bunch(host=ro.get_myhost(short=True)),
    )

# predefined groups
ciax.hosts = ciax.managers.keys()
ciax.ns = ro.unique_hosts(ciax.managers.values())

ciax.basedir = '$PYHOME'

ciax.svconfig = {

    "mgrsvc": {                # Name of the service
    'level': 0,                # what level does it belong to
    'hosts': ciax.hosts,       # which hosts can it run on
    'count': len(ciax.hosts),  # how many instances should I start
                               # what is the path to the executable from
                               #the base directory
    'description': DESCR.mgrsvc,
    'cmddir': 'remoteObjects',
                               # command to start the program 
    'start': 'remoteObjectManagerSvc.py --detach --logdir=%s --loglevel=info --log=ro_mgrsvc.log --output=ro_mgrsvc_stdout.log' % (logdir()),
    'flags': ('each'),         # special notes to BootManager
    },

    "names": {
    'level': 1,
    'hosts': ciax.hosts,
    'count': len(ciax.hosts),
    'description': DESCR.names,
    'cmddir': 'remoteObjects',
    'start': 'remoteObjectNameSvc.py --monitor=localhost:7080 --monport=7077 --monauth=monitor:monitor --logdir=%s --log=ro_names.log --loglevel=info' % (logdir()),
    'flags': ('each'),
    },

    "monitor": {
    'level': 2,
    'hosts': ciax.hosts,
    'count': 1,
    'description': DESCR.monitor,
    'cmddir': 'remoteObjects',
    'start': 'PubSub.py --port=7080 --svcname=monitor --config=cfg.pubsub --logdir=%s --log=monitor.log --loglevel=info' % (logdir()),
    'flags': ('random'),
    },

    # This is the status server
    "status": {
    'level': 3,
    'hosts': ciax.hosts,
    'count': 1,
    'description': DESCR.status,
    'cmddir': 'SOSS/status',
    'start': 'status.py --svcname=status --port=8151 --monitor=monitor --loglevel=info --log=%(log)s --checkpt=%(dbdir)s/status.cpt',
    'log': get_log('status.log'),
    'dbdir': dbdir(),
    'flags': ('fixed'),
    },

    # TCS interface to TSC simulator
    "TSC": {
    'level': 4,
    'hosts': ciax.hosts,
    'count': 1,
    'description': DESCR.TSC,
    'cmddir': 'SOSS/TCSint/Interface',
    'start': 'TCSint2.py --svcname=TSC --monitor=monitor --uid=1 --gid=7 --sender=CXWS --port=8141 --tcshost=tsc --loglevel=info --log=%(log)s --logmon=monlog',
    'log': get_log('TSC.log'),
    'flags': ('fixed'),
    },

    "taskmgr0": {
    'level': 5,
    'hosts': ciax.hosts,
    'count': 1,
    'description': DESCR.taskmgr,
    'cmddir': 'Gen2',
    'start': 'TaskManager.py --port=8170 --svcname="taskmgr0" --db=taskmgrdb-ciax  --monitor=monitor --allocs=taskmgr,TSC,status --load=TCSdd,skTask --para=TSC --numthreads=30 --loglevel=info --stderr --log=%(log_d)s:debug',
    'log_d': get_log('taskmgr0_debug.log'),
    'stdout': get_log('taskmgr0.log'),
    'flags': ('random'),
    },

    # TCS interface to TSC simulator
    "fakeTSC": {
    'level': 9,
    'hosts': ciax.hosts,
    'count': 1,
    'description': DESCR.TSC,
    'cmddir': 'SOSS/TCSint/Interface',
    'start': 'TCSint2.py --svcname=TSC --monitor=monitor --uid=1 --gid=7 --sender=CIAX --port=8141 --tcshost=localhost --log=%(log)s --loglevel=info --logmon=monlog',
    'log'  : get_log('TSC.log'),
    'flags': ('fixed'),
    },

    # TSC simulator
    "TSCsim": {
    'level': 9,
    'hosts': ciax.hosts,
    'count': 1,
    'description': DESCR.TSC,
    'cmddir': 'SOSS/TCSint/Interface',
    'start': 'TCSint2.py --sim --loglevel=info --log=%(log)s',
    'log': get_log('TSCsim.log'),
    'flags': ('random', 'nosvccheck'),
    },

    # *** USER INTERFACE INFRASTRUCTURE ***

    "g2web": {
        'level': 90,
        'hosts': ciax.hosts,
        'count': 1,
        'description': "The CIAX web interface",
        'cmddir': 'Gen2/web',
        'start': "g2web.py --config=ciax --plugins=bm --docroot=$GEN2HOME/docs --loglevel=info --log=%(log)s --detach",
        'log':   get_log('g2web.log'),
        'flags': ('random'),
        },

}

config = ciax

#END

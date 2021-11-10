from common import *
import os

def get_log(logfile):
    return os.path.join(os.environ['LOGHOME'], logfile)

#############################################################################
# INSTRUMENTS CONFIGURATION
#############################################################################
instr = Bunch()

instr.managers = populate(
    fldmon=Bunch(host='fldmon', user='fldmon'),
    )

# predefined groups
instr.hosts = instr.managers.keys()

instr.basedir = '$HOME'

instr.svconfig = {

    "mgrsvc": {                # Name of the service
    'level': 0,                # what level does it belong to
    'hosts': instr.hosts,
    'count': len(instr.hosts), # how many instances should I start
                               # what is the path to the executable from
                               #the base directory
    'description': DESCR.mgrsvc,
    'cmddir': 'Git/python/remoteObjects',
                               # command to start the program 
    'start': 'remoteObjectManagerSvc.py --log=%(log)s --output=%(output)s --detach --loglevel=20',
    'log'  :  get_log('ro_mgrsvc.log'),
    'output': get_log('ro_mgrsvc_stdout.log'),
    'flags': ('each'),         # special notes to BootManager
    },

    "monitor": {
    'level': 1,
    'hosts': instr.hosts,
    'count': 1,
    'description': DESCR.monitor,
    'cmddir': 'Git/python/remoteObjects',
    'start': 'PubSub.py --port=7080 --svcname=fldmon --loglevel=info --log=%(log)s',
    'log'  : get_log('monitor.log'),
    'flags': ('prefer'),
    },

    "names": {
    'level': 2,
    'hosts': instr.hosts,
    'count': len(instr.hosts),
    'description': DESCR.names,
    'cmddir': 'Git/python/remoteObjects',
    'start': 'remoteObjectNameSvc.py --monport=7077 --monitor=fldmon:7080 --monauth=fldmon:fldmon --log=%(log)s',
    'log'  : get_log('ro_names.log'),
    'flags': ('each'),
    },

    "pulseaudio": {
    'level': 99,
    'hosts': instr.hosts,
    'count': len(instr.hosts),
    'description': """This provides audio service for Gen2 observations""",
    #'cmddir': '.',
    'start': '/usr/bin/pulseaudio',
    'flags': ('each'),
    },

    # FieldMonitor instrument.
    "fldmon": {
    'level': 99,
    'hosts': ['fldmon'],
    'count': 1,
    'description': """This is the FieldMonitor instrument OBCP software.""",
    'rundir': 'Git/python/SIMCAM',
    'cmddir': '.',
    # 'start': 'simcam.py --cam=FLDMON --obcpnum=19 --paradir=PARA --obshost=obs --stathost=obs --framehost=obs --obchost=obc --loglevel=info --log=%(log)s',
    'start': 'g2cam.py --cam=FLDMON --obcpnum=19 --gen2host=g2ins1 --loglevel=info --log=%(log)s',
    'log': get_log('fldmon.log'),
    'flags': ('fixed', 'nosvccheck'),
    },

    # LTCS file generator (new version).
    "ltcs": {
    'level': 5,
    'hosts': ['fldmon'],
    'count': 1,
    'description': """This is the Laser Traffic Control System reporting daemon.  It reports Subaru's pointing position to other laser propagating telescopes on the summit of Mauna Kea.""",
    'cmddir': '.',
    'rundir': 'Git/ltcs-pointing',
    'count': 1,
    'start': "ltcs.py --update=1.0 --port=8011 --svcname=ltcs:9011 --auth=joe:bob2bob --statushost=g2stat --statussvc=status --log=%(log)s start",
    'log'  : '/data/LTCS/logs/ltcs.log',
    'stdout': '/data/LTCS/logs/ltcs_stdout.log',
    'flags': ('fixed', 'nosvccheck'),
    },

    # Boltwood Cloud Sensor
    "bcs": {
    'level': 5,
    'hosts': ['fldmon'],
    'count': 1,
    'description': """This is the Boltwood Cloud Sensor software.  It reads the
sensor and makes the data available via a web page.""",
    'rundir': 'BCS/python',
    'cmddir': '.',
    'start': 'bcs.py',
    'stop' : '/home/fldmon/BCS/python/bcs_kill.py',
    'stdout': '/data/BCS/logs/bcs_stdout.log',
    'flags': ('fixed', 'nosvccheck'),
    },

    # LGS collision (GA server)
    "lgs_ga": {
    'level': 7,
    'hosts': ['fldmon'],
    'count': 1,
    'description': """GA server for the LGS collision software.""",
    'cmddir': '.',
    'rundir': '/data/LTCS/bin',
    'count': 1,
    'start': "ltcs_proc_mgr.py start ga",
    'stdout': '/data/LTCS/logs/lgs_ga_stdout.log',
    'flags': ('fixed', 'nosvccheck'),
    },

    # LGS collision (STATUS_MGR server)
    "lgs_status_mgr": {
    'level': 7,
    'hosts': ['fldmon'],
    'count': 1,
    'description': """STATUS_MGR server for the LGS collision software.""",
    'cmddir': '.',
    'rundir': '/data/LTCS/bin',
    'count': 1,
    'start': "ltcs_proc_mgr.py start status",
    'stdout': '/data/LTCS/logs/lgs_status_mgr_stdout.log',
    'flags': ('fixed', 'nosvccheck'),
    },

    # LGS collision (COLLECTOR server)
    "lgs_collector": {
    'level': 7,
    'hosts': ['fldmon'],
    'count': 1,
    'description': """COLLECTOR server for the LGS collision software.""",
    'cmddir': '.',
    'rundir': '/data/LTCS/bin',
    'count': 1,
    'start': "ltcs_proc_mgr.py start collector",
    'stdout': '/data/LTCS/logs/lgs_collector_stdout.log',
    'flags': ('fixed', 'nosvccheck'),
    },

    "g2web": {
        'level': 80,
        'hosts': ['fldmon'],
        'count': 1,
        'description': "The fldmon web interface",
        'cmddir': 'Git/python/Gen2/web',
        'start': "g2web.py --config=fldmon --cert=/data/FLDMON/conf/fldmon.pem --auth_users='ocs:g2/ocs' --plugins=bm --docroot=/data/FLDMON/web/docs --loglevel=info --log=%(log)s --detach",
        'log'  :  get_log('g2web.log'),
        'flags': ('fixed', 'nosvccheck'),
        },

    # Cleanup FITS daemon.
    "cleanup_fld": {
    'level': 99,
    'hosts': ['fldmon'],
    'count': 1,
    'rundir': 'Git/python/SIMCAM',
    'cmddir': '.',
    'start': './cleanup_fits.py --loglevel=10 --action=delete --fitsdir=/data/FLDMON/fits --lo=10 --hi=20 --log=$LOGHOME/cleanup.log',
    'flags': ('fixed', 'nosvccheck'),
    },

    # AG/SV/SH/FMOS autoguider splitter.
    "agsplit": {
    'level': 99,
    'hosts': ['fldmon'],
    'count': 1,
    'description': """This is the AG/SV/SH splitter software.  It sends the
images coming from the guider cameras to both SOSS and Gen2.""",
    'rundir': 'AgSplit',
    'cmddir': '.',
    'start': 'agsplit.py --nopg vgw.sum.subaru.nao.ac.jp %s' % ('g2guide.sum.subaru.nao.ac.jp'),
    'stdout': '/data/FLDMON/logs/agsplit.log',
    'flags': ('fixed', 'nosvccheck'),
    },

}

config = instr

#END

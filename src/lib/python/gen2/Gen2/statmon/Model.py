#
# Model.py -- Model for StatMon.
#
# Eric Jeschke (eric@naoj.org)
#
import time
import threading

import remoteObjects.Monitor as Monitor
from ginga.misc import Callback

# import from SOSS.status ?
statNone = '##STATNONE##'

class StatusModel(Callback.Callbacks):

    def __init__(self, logger):
        super(StatusModel, self).__init__()
        
        self.logger = logger

        self.lock = threading.RLock()
        # This is where we store all incoming status
        self.statusDict = {}
        
        # Enable callbacks that can be registered
        for name in ['status-arrived', ]:
            self.enable_callback(name)

    def arr_status(self, payload, name, channels):
        """Called when new status information arrives at the periodic
        interval.
        """
        #self.logger.debug("received values '%s'" % str(payload))
        try:
            bnch = Monitor.unpack_payload(payload)

        except Monitor.MonitorError:
            self.logger.error("malformed packet '%s': %s" % (
                str(payload), str(e)))
            return

        if bnch.path != 'mon.status':
            return
        
        statusInfo = bnch.value

        self.update_statusInfo(statusInfo)

    def store(self, statusInfo):
        with self.lock:
            self.statusDict.update(statusInfo)

    def update_statusInfo(self, statusInfo):
        self.store(statusInfo)
        self.make_callback('status-arrived', statusInfo)

    def fetch(self, fetchDict):
        with self.lock:
            for key in fetchDict.keys():
                fetchDict[key] = self.statusDict.get(key, statNone)
                
    def calc_missing_aliases(self, aliasset):
        with self.lock:
            aliases = self.statusDict.keys()

        # Figure out the set of aliases we don't yet have
        need_aliases = aliasset.difference(set(aliases))
        return need_aliases

        
# END


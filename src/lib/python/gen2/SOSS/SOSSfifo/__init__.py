"""SOSS.SOSSfifo - support legacy SOSS FIFO formats.

"""

__author__ = "Eric Jeschke <eric@naoj.org>"


from SOSSfifo import SOSSfifoError, SOSSfifoMsg, SOSSfifoMsgError
from DAQfifo import DAQfifoMsg, DAQfifoMsgError, DAQViewfifoMsg
from Skymonfifo import SkymonfifoMsg, SkymonfifoMsgError
# Add other fifo types here

__all__ = ['SOSSfifoError', 'SOSSfifoMsg', 'SOSSfifoMsgError',
           'DAQfifoMsg', 'DAQfifoMsgError', 'DAQViewfifoMsg',
           'SkymonfifoMsg', 'SkymonfifoMsgError',
           ]

#END

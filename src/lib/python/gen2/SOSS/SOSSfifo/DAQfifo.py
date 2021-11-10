#!/usr/bin/env python


import sys, time

import SOSSfifo
import SOSS.SOSSrpc as SOSSrpc
import astro.fitsutils as fitsutils
from cfg.INS import INSdata as INSconfig


"""
KIND should be one of the following, if sending to :
 - "FLOWCTRL" for unprocessed fits files
 - "ENDMAKE" for DB insertion
 - "FLOWSND" for sending to Hilo base
 - "FLOWSAVE" for saving to tape
 - "FLOWDEL" for cleaning up
"""

_FIFO_KIND = {
    'CMDRCV':   "CMDRCV  ",
    'GETRCV':   "GETRCV  ",
    'ENDFTP':   "ENDFTP  ",
    'GETRAID':  "GETRAID ",
    'FITSRCV':  "FITSRCV ",
    'FLOWCTRL': "FLOWCTRL",
    'ENDMAKE':  "ENDMAKE ",
    'ENDCHANG': "ENDCHANG",
    'ENDSND':   "ENDSND  ",
    'ENDSAVE':  "ENDSAVE ",
    'ENDLOAD':  "ENDLOAD ",
    'ENDINIT':  "ENDINIT ",
    'ENDERASE': "ENDERASE",
    'ENDCLEAN': "ENDCLEAN",
    'ENDINS':   "ENDINS  ",
    'ENDUPDAT': "ENDUPDAT",
    'FLOWSND':  "FLOWSND ",
    'FLOWSAVE': "FLOWSAVE",
    'FLOWDEL':  "FLOWDEL ",
    'ENDDEL':   "ENDDEL  ",
    'MAKE':     "MAKE    ",
    'CHANGE':   "CHANGE  ",
    'SNDCTRL':  "SNDCTRL ",
    'SNDLOG':   "SNDLOG  ",
    'SNDREPLY': "SNDREPLY",
    'SNDEND':   "SNDEND  ",
    'TAPESAVE': "TAPESAVE",
    'TAPEMODE': "TAPEMODE",
    'TAPETIME': "TAPETIME",
    'TAPELOAD': "TAPELOAD",
    'TAPEINIT': "TAPEINIT",
    'TAPEERAS': "TAPEERAS",
    'TAPECLEA': "TAPECLEA",
    'DBSINS':   "DBSINS  ",
    'DBSUPDAT': "DBSUPDAT",
    'STATTIME': "STATTIME",
    'STATCMD':  "STATCMD ",
    'STATDSP':  "STATDSP ",
    'QDASCTRL': "QDASCTRL",
    'QDASREXE': "QDASREXE",
    }

_FIFO_UPDATE = {
    'TAPE':   "00",         #tape saving date/time/volume number setting
    'FOOT':   "01",
    'DELETE': "02",
    'DELETE': "03",         # RAID deleting date/time setting
    'OBC':    "00",         # OBC operation mode
    'RESET':  "01",         # OBC status reset
    'C_DBS':  "10",         # DBS connection status
    'C_TAPE': "30",         # Tape connection status
    'C_FOOT': "50",         # Hilo base connection status
    'C_OBCP': "60",         # OBCP connection status
    }

_FIFO_MANUAL = {
    'first': "ST",          # First frame, if more than 1 frame
    'last': "ON",           # Last frame, or if only 1 frame
    'neither': "  ",        # Any other frame not first or last
    }

## _FIFO_MANUFLG = {
##     'ST':   1,
##     'ON':   2,
##     'BOTH': 3,
##     }
_FIFO_MANUFLG = {
    'first': 'S',
    'other': ' ',
    }

_FIFO_RESULT = {
    'OK': 'OK',
    'NG': 'NG',
    'NO': 'NO',
    }


class DAQfifoMsgError(SOSSfifo.SOSSfifoMsgError):
    pass

class DAQfifoMsg(SOSSfifo.SOSSfifoMsg):
    """
    DESCRIPTION

    FIFO's are used to communicate 100-byte records between DAQ processes. Only
    the fields needed in order to pass a message for a particular transaction are
    actually filled in. A FIFO is often used in conjunction with a shared memory
    block which is organized as a circular queue in parallel to the FIFO. Each
    shared memory entry contains application-specific data which may be much
    larger than a 100-byte FIFO record.

    The DAQobcGetCtl process uses one getctrl.fifo FIFO.

    ???TBD???

    Each DAQobcGetFitsRcv process (DAQobcGetFitsRcv_1 - DAQobcGetFitsRcv_33) uses
    one getfits.fifo FIFO (getfits_1.fifo - getfits_33.fifo). The RPC server
    function (daqtk_dat_snd_mem_1, see DAQobcGetFitsRcv(1) ) calls function
    DAQobcGetFitsRcvNotice in order to construct a FIFO message and append it to
    getfits.fifo .

    In the FIFO names below, <Host_Number> represents the host number, between "01"
    and "33", of the OBCP/VGW served by the DAQobcGetFitsRcv_<Host_Number> process.
    The getfits.fifo file is found in $DAQOBCHOME/dat/getfits<Host_Number>.fifo .
    Each message appended to the file is 100 bytes long and is comprised of fields
    whose offsets are defined by the following constants from the DAQobcCom.h
    header file:

    Field        Pos  Len  Description
    KIND           0    8  8 byte ASCII command (e.g. "FLOWSAVE")
    FRAME          8   12  FITS frame ID (e.g. "FLDA00000063")
    TIME          20   18  "YYYYMMDDHHMMSS.SSS"
    HOST          38    4  HOST_NO, i.e. n, the OBCP/VGW host number (1 - 33)
    RESULT        42    2  Result code (e.g. "OK" or "NG")
    PREFRAME      44   12  For a "Q" frame this is the associated "A" frame
    VOLUME        56   14  Tape volume number
    UPDATE        70    2  Update item (e.g. "01", "02" or "03")
    SEQNO         72    8  Sequence number
    STAT          80    8  Status item ("00", "01", "10", "30", "50", "70")
    MANUAL        88    2  Manual operation ("ST" or "ON")
    TAPESET       90    6  Tape head position
    MANUFLG       96    1  Manual flags ("S")
    RSV           97    3  Reserved for future use
                       --
                      100

    Refer to the Fujitsu Manual "Softare Composition Specifications,
    Part 2. DATA ACQUISITION SYSTEM" for details on the fields.
    """

    def __init__(self):
    
        # TODO: DAQ FIFO messages should be initialized to 100 bytes of NULLs.
        # Setting a field overrides the nulls.
        
        # allots 'kind' and 'reserved'
        super(DAQfifoMsg, self).__init__()

        # Additional fields
        self.frame = ''
        self.time = time.time()
        self.host = 0
        self.result = ''
        self.preframe = ''
        self.volume = ''
        self.update = ''
        self.seqno = 0
        self.stat = 0
        self.manual = ''
        self.tapeset = ''
        self.manuflg = ''


    def new_message(self, **kwdargs):
        """Same as "set", but updates the timesent and seq_num."""

        self.time = time.time()
        self.seqno += 1

        self.set(**kwdargs)


    def message2str(self):
        
        tstamp = SOSSrpc.time2timestamp(self.time)

##         msgstr = "%(kind)-8.8s%(frame)12.12s%(time)18.18s%(host)4d%(result)2.2s%(preframe)12.12s%(volume)14.14s%(update)2.2s%(seqno)8d%(stat)8d%(manual)2.2s%(tapeset)6.6s%(manuflg)1.1s%3.3s" % (
        msgstr = "%-8.8s%12.12s%18.18s%4d%2.2s%12.12s%14.14s%2.2s%8d%8d%2.2s%6.6s%1.1s%3.3s" % (
            self.kind,
            self.frame,
            tstamp,
            self.host,
            self.result,
            self.preframe,
            self.volume,
            self.update,
            self.seqno,
            self.stat,
            self.manual,
            self.tapeset,
            self.manuflg,
            self.reserved )

        self.msgCheck(msgstr)

        return msgstr
                                  

class DAQViewfifoMsg(SOSSfifo.SOSSfifoMsg):

    def __init__(self):
        # allots 'kind' and 'reserved'
        super(DAQViewfifoMsg, self).__init__()

        # Additional fields
        self.frame = ''
        self.fitspath = ''


    def message2str(self):
        
        msgstr = "%8.8s%12.12s%-80.80s" % (
            self.kind,
            self.frameid,
            self.padNull(self.fitspath, 80) )

        self.msgCheck(msgstr)

        return msgstr
                                  

def error(msg):
    sys.stderr.write(msg + '\n')

    
def main(options, args):

    # Make sure there is at least 1 argument
    if len(args) == 0:
        parser.error("incorrect number of arguments")

    # Get an instrument configuration object
    insconfig = INSconfig()

    # Valididate fifo command
    try:
        kind = _FIFO_KIND[options.kind.upper()]

    except KeyError, e:
        sys.stderr.write("Not a valid DAQ fifo command: '%s'" % options.kind)
        sys.exit(1)

    # For each fits file listed, generate a DAQ flow control FIFO message
    if options.manual:
        manual = _FIFO_MANUAL['first']
    else:
        manual = _FIFO_MANUAL['neither']

    while len(args) > 0:
        fitspath = args.pop(0)
        if options.manual and (len(args) == 0):
            manual = _FIFO_MANUAL['last']
        
        # Separate leading directory
        res = fitsutils.getFrameInfoFromPath(fitspath)

        if not res:
            error("File name '%s' doesn't match a valid Subaru FITS name." % \
                  (fitspath))
            error("Please rename the file as 'XXX{A|Q}DDDDDDDD.fits'")
            error("Skipping this file...")
            continue

        (frameid, fitsfile, fitsdir, inscode, frametype, frameno) = res
        try:
            insno = insconfig.getNumberByCode(inscode)
        except KeyError:
            error("File name '%s' doesn't match a valid Subaru instrument." % \
                  (fitsfile))
            error("Skipping this file...")
            continue

        msg = DAQfifoMsg()
        # DAQobcFlowCtrl commands require the following
        msg.set(kind=kind, frame=frameid, host=insno, manual=manual)

        manual = _FIFO_MANUAL['neither']
#    msg = DAQViewfifoMsg()
#    msg.set(kind='FITSFILE', frameid=args[0], fitspath=args[1])

        sys.stderr.write("Outputting fifo string for '%s'...\n" % frameid)
        sys.stdout.write(str(msg))
        if options.newline:
            sys.stdout.write('\n')
        sys.stdout.flush()


if __name__ == '__main__':

    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options] <FITS file> ..."
    parser = OptionParser(usage=usage, version=('%prog'))

    parser.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    parser.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    parser.add_option("-n", "--newline", dest="newline", action="store_true",
                      default=False,
                      help="Output a newline between fifo records")
    parser.add_option("-k", "--kind", dest="kind", default='FLOWCTRL',
                      help="Specify the kind of fifo message.")
    parser.add_option("-m", "--manual", dest="manual", action="store_true",
                      default=False,
                      help="Set the manual field")

    (options, args) = parser.parse_args(sys.argv[1:])
    
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
    
#END


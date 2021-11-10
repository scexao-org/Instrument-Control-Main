#!/usr/bin/env python
#
# STARSint.py -- Interface with Subaru Observatory STARS archive system.
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Apr 11 16:47:57 HST 2012
#]
#
#
import sys, os, re
import threading, Queue
import time, datetime
# profile imported below (if needed)
# pdb imported below (if needed)
# optparse imported below (if needed)
import hashlib, hmac
import logging

import SOSS.SOSSrpc as SOSSrpc
from SOSS.INSint import BaseInterface
import Gen2.db.frame as framedb
import STARScheck
from Bunch import Bunch
import Task
import dates
import remoteObjects as ro
import remoteObjects.Monitor as Monitor
import ssdlog
import pyfits

# Version/release number
version = "20120410.0"

# Number of STARS channels there are
num_STARS_channels = 8

# Service name for directory of remote objects

serviceName = 'STARSint'

# Chose type of authorization encryption 
digest_algorithm = hashlib.sha1


class STARSintError(Exception):
    """STARS Interface Error Exception.
    """
    pass

        
# Index by channel number to get host interface name and destination

# directory.

# env setting for a pair of a hannel and STARS host is followings: 
# S1=s01-a1 
# S2=s01-a2 
# S3=s01-a1
# S4=s01-a2
# S5=s02-a1
# S6=s02-a2
# S7=s02-a1
# S8=s02-a2
 
# STARSDIR was fixed dir sdata04, but sdata01/2/3 are also used

#                    RPCHOST   STARSDIR
STARSTransConfig = ((None, None),             # channel numbers indexes are 1 based
                    ('s01-a1', 'sdata01'),
                    ('s01-a2', 'sdata02'),
                    ('s01-a1', 'sdata01'),
                    ('s01-a2', 'sdata02'),
                    #('sreg', 'sdata01'),
                    #('sreg', 'sdata02'),
                    ('s02-a1', 'sdata03'),
                    ('s02-a2', 'sdata04'),
                    ('s02-a1', 'sdata03'),
                    ('s02-a2', 'sdata04'),
                    )

def get_STARSparams(channelnum, starshost=None, starsdir=None, version=None):
    """An interface for pulling information from the STARSTransConfig table.
    This table has an RPCHOST/STARSDIR pair (tuple) for each channel index."""

    tup = STARSTransConfig[channelnum]

    # Version is always the same, near as I can figure
    if not version:
        version='S01'

    # If STARS host is explicitly specified then use it, otherwise look it up
    # in STARSTransConfig.  If there is nothing there, then assume the local host.
    if not starshost:
        starshost = tup[0]
        if not starshost:
            starshost = SOSSrpc.get_myhost(short=True)
        
    if not starsdir:
        starsdir = tup[1]
        if not starsdir:
            starsdir = 'tmp'

    return Bunch(rpchost=starshost, starsdir=starsdir, version=version)

    
    
# Create index file.
#
# Index file should be 400 bytes
#define SIZ_INDEX               (400)           /* Index information file */
#define SIZ_INDEX_FRAME         (12)            /* Frame number */
#define SIZ_INDEX_RETURN_1      (1)             /* Carriage return */
#define SIZ_INDEX_MAKE          (18)            /* Index information compilation time */
#define SIZ_INDEX_RETURN_2      (1)             /* Carriage return */
#define SIZ_INDEX_UPDATE        (18)            /* Index information renewal time */
#define SIZ_INDEX_RETURN_3      (1)             /* Carriage return */
#define SIZ_INDEX_DATANAME      (128)           /* Acquisition data file name */
#define SIZ_INDEX_RETURN_4      (1)             /* Carriage return */
#define SIZ_INDEX_KIND          (1)             /* Data classification */
#define SIZ_INDEX_RETURN_5      (1)             /* Carriage return */
#define SIZ_INDEX_PREFRAME      (12)            /* Original frame number */
#define SIZ_INDEX_RETURN_6      (1)             /* Carriage return */
#define SIZ_INDEX_USERID        (8)             /* User identification */
#define SIZ_INDEX_RETURN_7      (1)             /* Carriage return */
#define SIZ_INDEX_GROUPID       (8)             /* Group ID */
#define SIZ_INDEX_RETURN_8      (1)             /* Carriage return */
#define SIZ_INDEX_RAIDSET       (18)            /* RAID housing time */
#define SIZ_INDEX_RETURN_9      (1)             /* Carriage return */
#define SIZ_INDEX_RAIDDEL       (18)            /* RAID deletion time */
#define SIZ_INDEX_RETURN_10     (1)             /* Carriage return */
#define SIZ_INDEX_TAPE          (18)            /* Tape retention time */
#define SIZ_INDEX_RETURN_11     (1)             /* Carriage return */
#define SIZ_INDEX_VOLUME        (14)            /* Volume number */
#define SIZ_INDEX_RETURN_12     (1)             /* Carriage return */
#define SIZ_INDEX_FOOT          (18)            /* Mountain base transfer time */
#define SIZ_INDEX_RETURN_13     (1)             /* Carriage return */
#define SIZ_INDEX_DATASIZ       (10)            /* Acquisition data size */
#define SIZ_INDEX_RETURN_14     (1)             /* Carriage return */
#define SIZ_INDEX_TAPESET       (6)             /* Tape housing position */
#define SIZ_INDEX_RETURN_15     (1)             /* Carriage return */
#define SIZ_INDEX_RSV           (78)            /* Padding for reserved space */
##    """An Index File is created for every FITS file and is transmitted to STARS
##    along with the FITS file. It records the time at which each operation within
##    DAQ has been completed, or has a blank line if the operation has not been
##    completed. The meaning of each line is determined by its line number: 
##   
##       1. FITS file ID, e.g. MCSA00010926 -- (0/12)
##       2. Date/time of Index File creation, e.g. 20050922183231.898 -- (13/18)
##       3. Date/time of most recent update of the Index File, e.g. 20050924133034.412
##       -- (32/18)
##       4. File path on obc1, e.g. /mdata/fits/obcp17/MCSA00010926.fits -- (51/128)
##       5. FITS type, A (raw instrument sensor data) or Q (pipeline-processed data)
##       -- (180/1)
##       6. "pre-frame", i.e. original frame ID; usually blank -- (182/12)
##       7. "user ID", but seems to always be blank -- (195/8)
##       8. "group ID", but seems to always be blank -- (204/8)
##       9. Date/time the FITS file was saved to RAID, e.g. 20050922183231.857
##       -- (213/18)
##      10. Date/time the FITS file was deleted from RAID -- (232/18)
##      11. Date/time the FITS file was saved to DMS -- (251/18)
##      12. DMS tape ID on which the FITS file was saved -- (270/14)
##      13. Date/time the FITS file was transferred to STARS -- (285/18)
##      14. FITS file size in bytes -- (304/10)
##      15. "tape set", probably the file number or block number where the saved FITS
##      file starts on the DMS tape -- (315/6)
##      16. Reserve -- 78 characters not used, therefore left blank -- (322/78) 
## 
##    The Index File is formatted as a single 400-character array, with the offset and
##    length of each line absolutely fixed. The numbers in parentheses above are the
##    offset and size (not including EOL) of each line, e.g. (51/128). Hence, it is
##    important never to insert or delete any characters. If any edits are needed,
##    they must be made by using the overwrite mode of an editor, being very careful
##    not to add to the end of any line. The constants defining the character offsets
##    in the array are set in #define statements in SRC/OBC/src/flow/inc/DAQobcCom.h
##    and all begin with "SET_INDEX".
##
##    Anomaly/bug -- I have noticed that line 16, which is 6 characters long, usually
##    contains a 4 or 5-character number followed by 1 or 2 null characters. This is
##    caused by the fact that the process which writes this information onto the queue
##    or FIFO uses a %d specification instead of a %6d specification for the sprintf
##    statement in line 130 of SRC/OBC/src/tape/save/DAQobcTapeSaveSh.pc. Apparently
##    this causes no problem, so I am not correcting it as of this time (2005-10-05).
##    """
index_template = """\
%(frameid)-12.12s
%(indexmaketime)-18.18s
%(indexupdatetime)-18.18s
%(fitspath)-128.128s
%(frametype)1.1s
%(preframeid)-12.12s
%(userid)-8.8s
%(groupid)-8.8s
%(raidaddtime)-18.18s
%(raiddeltime)-18.18s
%(tapeaddtime)-18.18s
%(tapevolumeno)-14.14s
%(basexfertime)-18.18s
%(fitssize)-10d
%(tapeheadpos)-6d
%(padding)-78.78s\
"""

# This one is for log files
#
inf_template = """\
%(updatetime)-14.14s
%(filetime)-8.8s
%(fitssize) 10d
%(raidaddtime)-14.14s
%(filepath)s
%(raiddeltime)-14.14s
%(tapeaddtime)-14.14s
%(tapevolumeno)-20.20s
%(basexfertime)-14.14s
%(statusname)-8.8s
%(frameid)s
/dummy_path/%(frameid)s
%(logstarttime)-14.14s
%(logendtime)-14.14s
"""

def create_index_file(metadata, template, indexpath=None):

    # Verify that we have a path to write index file
    if not indexpath:
        # TODO: add indexdir to metadata ?
        if not metadata.has_key('indexdir'):
            raise STARSintError("No indexpath or indexdir specified")

        # Blank indexdir is OK, defaults to '.'
        indexdir = metadata['indexdir']
        if  indexdir == '':
            indexdir = '.'
        if not indexdir.endswith('/'):
            indexdir += '/'
        indexpath = indexdir + metadata['frameid'] + '.index'
        
    # Note: indexpath in metadata may be different--it's OK
    if not metadata.has_key('indexpath'):
        metadata['indexpath'] = indexpath
        
    # Create index file
    try:
        out_f = open(indexpath, 'w')
        out_f.write(template % metadata)
        out_f.close()

    except IOError, e:
        raise STARSintError("Can't open index file (%s) for writing: %s" % \
                            (indexpath, str(e)) )

    # Change index file's permission
    try:
        # Index files are stored as -rw-rw-r--
        os.chmod(indexpath, 0664)

    except OSError, e:

        raise STARSintError("Can't chmod index file: %s" % str(e))

    # Stat the index file to get the size.
    try:
        statbuf = os.stat(indexpath)

        metadata['indexsize'] = statbuf.st_size

    except OSError, e:
        raise STARSintError("Cannot stat file '%s': %s" % \
                            (indexpath, str(e)))


class STARSchannel(BaseInterface):
    ''' Instantiating this class creates a single "channel" (RPC) interface to
    the STARS archive.  Normally, multiple channels are aggregated to create
    the full interface
    '''

    def __init__(self, channelnum, ev_quit, logger, db, taskqueue, checkobj,
                 starshost=None, starsdir=None, monchannels=[],
                 myhost=None, myport=None, seq_num=None):

        # Initialize common attributes
        super(STARSchannel, self).__init__(ev_quit, logger, db,
                                           taskqueue,
                                           myhost=myhost, myport=myport,
                                           seq_num=seq_num)
        self.channelnum = channelnum
        self.monchannels = monchannels
        self.fitscheck = checkobj
        self.sendTasker = Task.make_tasker(self.cmd_send)
        self.recvTasker = Task.make_tasker(self.cmd_recv)

        # Look up program numbers for STARS RPC interface
        try:
            key = ('OBCtoSTARS%d' % channelnum)

            self.rpcconn = SOSSrpc.clientServerPair(key, initiator=True,
                                                    logger=self.logger,
                                                    ev_quit=self.ev_quit,
                                                    #myhost=self.myhost,
                                                    recvqueue=self.taskqueue,
                                                    func=self.recvTasker)

        except SOSSrpc.rpcError, e:
            raise INSintError("Error creating rpc client-server pair: %s" % \
                              str(e))

        # Restore sequence number from db in case of a restart
        key = 'stars.%d.seq_num' % (self.channelnum)
        if self.db.has_key(key):
            self.seq_num.reset(self.db[key])

        # Get stars parameters (default hostname, directory, version, etc.)
        try:
            self.stars = get_STARSparams(channelnum, starshost=starshost,
                                         starsdir=starsdir)
            self.logger.debug("rpchost: %s, starsdir: %s" % \
                              (self.stars.rpchost, self.stars.starsdir))

        except IndexError, e:
            raise STARSintError("Can't find STARS params (channel=%d)" % channelnum)
        

    def _get_key(self, seq_num):
        return 'stars.%d.%d' % (self.channelnum, seq_num)
        
    def put_trans(self, seq_num, tag):
        key = self._get_key(seq_num)

        # Is there a cmdb bundle for this seq_num?
        if self.db.has_key(key):
            raise STARSintError("Tag exists matching sequence number %d" % \
                                (seq_num))

        else:
            self.db[key] = tag

    def get_trans(self, seq_num):
        key = self._get_key(seq_num)

        # Is there a bundle for this seq_num?
        if self.db.has_key(key):
            return self.db[key]

        else:
            raise STARSintError("No tag matching sequence number %d" % \
                                (seq_num))

    def del_trans(self, seq_num, tag):
        """This is called to delete a transaction from the pending transaction
        table (self.db).  The transaction tag is deleted under (key) IFF the
        transaction contains all three RPC components: cmd, ack, end
        """
        key = self._get_key(seq_num)

        # Raises an exception if tag not found?
        if not self.db.has_key(key):
            self.logger.warn("No command data found for tag '%s'" % tag)
            return

        cmdb = self.db.get_node(tag)
        cmdb.enter()
        try:
            if cmdb.has_key('cmd') and cmdb.has_key('ack') and \
                   cmdb.has_key('end'):
                try:
                    del self.db[key]
                except KeyError:
                    pass

        finally:
            cmdb.leave()


    def get_log_metadata(self, datadict, logpath, statusname=None):
        """Gets meta data about this log file _logpath_ and fills in the
        dict interface _datadict_.  The keys need to match the keys
        in inf_template.
        """

        datadict['filepath'] = logpath

        if not os.path.exists(logpath):
            raise STARSintError("Not a regular file: %s" % logpath)

        # Stat the FITS file to get the size.
        try:
            statbuf = os.stat(logpath)

            datadict['fitssize'] = statbuf.st_size
            datadict['filetime'] = SOSSrpc.time2timestamp(statbuf.st_ctime)
            if not datadict.has_key('raidaddtime'):
                datadict['raidaddtime'] = SOSSrpc.time2timestamp(statbuf.st_mtime)

        except OSError, e:
            raise STARSintError("Cannot stat file '%s': %s" % (
                    logpath, str(e)))

        # Extract frame id from file path
        (logdir, logname) = os.path.split(logpath)
        if  logdir == '':
            logdir = '.'

        # If there is no particular index dir chosen, create the index file
        # in the same directory as the LOG file.
        if not datadict.has_key('indexdir'):
            datadict['indexdir'] = logdir

        # Is this a timestamped status packet log?
        match = re.match(r'^(\w+).*(\.(pkt|log))?$', logname)
        if not match:
            raise STARSintError("Cannot log file '%s' does not match standard naming conventions" % (
                    (logpath)))

        # status name will be something like 'TSCV' or 'TASKMGR'
        name = match.group(1).upper()[:8]
        datadict['statusname'] = name
        # 'name' value is expected to be present, e.g. 'TSCV20100528OBS'
        datadict['frameid'] = datadict['name'].upper()
        datadict['propid'] = 'summitlog'

        # Set timestamps as needed
        tstamp = SOSSrpc.time2timestamp()
        datadict['updatetime'] = tstamp
        if not datadict.has_key('raidaddtime'):
            datadict['raidaddtime'] = tstamp
        if not datadict.has_key('raiddeltime'):
            datadict['raiddeltime'] = ''
        if not datadict.has_key('basexfertime'):
            datadict['basexfertime'] = tstamp
            #datadict['basexfertime'] = ''
        if not datadict.has_key('tapeaddtime'):
            #datadict['tapeaddtime'] = tstamp
            datadict['tapeaddtime'] = ''

        # Set summit tape info
        if not datadict.has_key('tapevolumeno'):
            datadict['tapevolumeno'] = ''
        #if not datadict.has_key('tapeheadpos'):
        #    datadict['tapeheadpos'] = 0

        # If no start and stop times given, then 
        if not datadict.has_key('logstarttime'):
            datadict['logstarttime'] = datadict['filetime'][:8] + '000000'
        else:
            t_s = datadict['logstarttime']
            t_s = t_s.replace(' ', '').replace('-', '').replace(':', '')
            datadict['logstarttime'] = t_s[:14]

        if not datadict.has_key('logendtime'):
            datadict['logendtime'] = datadict['raidaddtime'][:8] + '235959'
        else:
            t_s = datadict['logendtime']
            t_s = t_s.replace(' ', '').replace('-', '').replace(':', '')
            datadict['logendtime'] = t_s[:14]


    def get_fits_metadata(self, datadict, fitspath=None, use_mtime=False):
        """Gets meta data about this FITS file _fitspath_ and fills in the
        dict interface _datadict_.  The keys need to match the template in
        index_template.  If _use_mtime_ is True, then the modification
        time of the file will be used for the RAIDADDTIME metadata instead
        of the file's creation time.
        """

        # Verify file path is passed in
        if fitspath:
            # Add path to metadata if missing
            if not datadict.has_key('fitspath'):
                datadict['fitspath'] = fitspath
        else:
            if datadict.has_key('fitspath'):
                fitshpath = datadict['fitspath']
            else:
                raise STARSintError("No fitspath specified")

        if not os.path.isfile(fitspath):
            raise STARSintError("Not a regular file: %s" % fitspath)

        # Stat the FITS file to get the size.
        try:
            statbuf = os.stat(fitspath)

            datadict['fitssize'] = statbuf.st_size
            if not datadict.has_key('raidaddtime'):
                if use_mtime:
                    datadict['raidaddtime'] = SOSSrpc.time2timestamp(statbuf.st_mtime)
                else:
                    datadict['raidaddtime'] = SOSSrpc.time2timestamp(statbuf.st_ctime)

        except OSError, e:
            raise STARSintError("Cannot stat file '%s': %s" % \
                                (fitspath, str(e)))

        # Extract frame id from file path
        (fitsdir, fitsname) = os.path.split(fitspath)
        if  fitsdir == '':
            fitsdir = '.'
        datadict['fitsdir'] = fitsdir
        datadict['fitsname'] = fitsname

        # If there is no particular index dir chosen, create the index file
        # in the same directory as the FITS file.
        if not datadict.has_key('indexdir'):
            datadict['indexdir'] = fitsdir

        # Extract frameid from the filename, if possible.
        # TODO: check the filename matches a valid Subaru frame id
        match = re.match(r'^(\w+)(\.fits)*$', fitsname)
        if match:
            datadict['frameid'] = match.group(1)

        # Open the file and extract the FITS keywords.
        fitsobj = None
        try:
            #fitsobj = pyfits.open(fitspath, 'readonly')
            os.chmod(fitspath, 0640)  # need write permission to update fits
            fitsobj = pyfits.open(fitspath, 'update')

        except Exception, e:
            raise STARSintError("Cannot open FITS file '%s': %s" % (
                    fitsname, str(e)))

        # Read the FITS keywords from the primary HDU
        #kwds = {}
        try:
            try:
                # Seems to be necessary to get pyfits to read fits keywords
                fitsobj.verify('silentfix')

                # Extract primary header 
                prihdr = fitsobj[0].header
                
                try:
                    if not datadict.has_key('propid'):
                        datadict['propid'] = prihdr['PROP-ID']

                except KeyError, e:
                    self.logger.error("FITS file '%s' does not have PROP-ID" % (fitsname))

                # Check the FITS file for STARS readiness
                self.fitscheck.check(fitspath, fitsobj, prihdr, datadict,
                                     fix=True)

            except Exception, e:
                raise STARSintError("STARS precheck raised exception for '%s': %s" % (
                        fitsname, str(e)))

        finally:
            fitsobj.close()
            # change back to the same permission as summit 
            os.chmod(fitspath, 0440)  


        # Get frame type
        match = re.match(r'^\w\w\w(\w)[\w\.\-]+$', datadict['frameid'])
        if not match:
            raise STARSintError("Cannot determine FITS file type (A or Q): '%s'" % (fitsname))

        datadict['frametype'] = match.group(1)

        # These can be blank
        datadict['preframeid'] = ''
        datadict['userid'] = ''
        datadict['groupid'] = ''
        datadict['raiddeltime'] = ''
        datadict['padding'] = ''

        # Set timestamps as needed
        tstamp = SOSSrpc.time2timestamp()
        datadict['indexmaketime'] = tstamp
        datadict['indexupdatetime'] = tstamp
        if not datadict.has_key('raidaddtime'):
            datadict['raidaddtime'] = tstamp
        if not datadict.has_key('basexfertime'):
            datadict['basexfertime'] = tstamp
            #datadict['basexfertime'] = ''
        if not datadict.has_key('tapeaddtime'):
            #datadict['tapeaddtime'] = tstamp
            datadict['tapeaddtime'] = ''

        # Set summit tape info
        if not datadict.has_key('tapevolumeno'):
            datadict['tapevolumeno'] = ''
        if not datadict.has_key('tapeheadpos'):
            datadict['tapeheadpos'] = 0

    def cmd_send(self, tag):
        """Look up the file information registered under _tag_, and send
        the file command to STARS.
        """

        seq_num = -1
        try:
            if not self.db.has_key(tag):
                raise STARSintError("No command data found for tag '%s'" % tag)

            # Raises an exception if tag not found?
            cmdb = self.db.get_node(tag)

            # Create dict of params that we will record to Gen2 database
            start_time = time.time()
            cmdb.xferDict = dict(xfer_type='gen2->stars', 
                                 time_start=datetime.datetime.fromtimestamp(start_time),
                                 xfer_method='ftp',
                                 src_host=self.myhost, src_path=cmdb.fitspath,
                                 dst_host=self.stars.rpchost)
            
            # Once we recieve a request, get any metadata
            # about the file (propid, etc.) necessary for the
            # rpc interface
            fitspath = cmdb.fitspath

            if cmdb.has_key('propid') and cmdb.propid == 'summitlog':
                # Special dispensation for log files
                self.logger.debug("Getting log metadata for '%s'" % fitspath)
                self.get_log_metadata(cmdb, logpath=fitspath)

                # Create strange little associated .index file required
                # by STARS.  
                self.logger.debug("Creating INF file for '%s'" % fitspath)
                inffile = '%s/%s.inf' % (cmdb['indexdir'], cmdb['frameid'])
                create_index_file(cmdb, inf_template, indexpath=inffile)
                
            else:
                # FITS file
                self.logger.debug("Getting fits metadata for '%s'" % (
                        fitspath))
                # Get metadata and do a pre-STARS check
                self.get_fits_metadata(cmdb, fitspath=fitspath)

                # Report results
                result = cmdb['checkresult']
                if len(result) > 0:
                    self.logger.error("Issues with '%s'" % (fitspath))
                    for message in result:
                        self.logger.warn(message)

                handling = cmdb['handling']
                if handling & STARScheck.HANDLE_SILENTREJECT:
                    return
                if handling & STARScheck.HANDLE_REJECT:
                    self.db.setvals(self.monchannels, tag,
                                    errorclass='starscheck')
                    raise STARSintError("Did not pass STARS precheck: %s" % (
                            fitspath))
                
                # Create strange little associated .index file required
                # by STARS.  TODO: specify path for index files
                self.logger.debug("Creating index file for '%s'" % fitspath)
                create_index_file(cmdb, index_template, indexpath=None)

            # Get new sequence number for this transaction
            seq_num = self.seq_num.bump()

            # Create RPC message
            rpcbuf = SOSSrpc.SOSScmdRpcMsg(sender=self.myhost,
                                           receiver=self.stars.rpchost,
                                           pkt_type='FT')

            # Send initial message as client
            rpcbuf.pack_fs(cmdb.fitspath, cmdb.fitssize,
                           cmdb.frameid, cmdb.propid,
                           self.stars.starsdir,
                           self.stars.version, cmdb.indexpath,
                           cmdb.indexsize, seq_num=seq_num)

            # Record time sent to STARS for this command
            self.db.setvals(self.monchannels, tag, cmd_time=time.time(),
                            seq_num=seq_num)
            # Associate this tag with this seq_num
            self.put_trans(seq_num, tag)

            # Make the rpc client call
            try:
                res = self.rpcconn.callrpc(rpcbuf)

            except SOSSrpc.rpcClientError, e:
                raise STARSintError("Error sending STARS archive request: %s" % str(e))

        except KeyError, e:
            # Errors thrown from get_fits_metadata?
            self.cmd_error(e, seq_num, tag)

        except STARSintError, e:
            # Errors thrown in send_fits trying to interface to
            # STARS end up here
            self.cmd_error(e, seq_num, tag)

        # Unexpected error.  We only catch this so we can execute
        # planB, then re-raise the error.
        except Exception, e:
            self.cmd_error(e, seq_num, tag)
            raise e


    # Acknowledgement payload validator.
    #
    def validate_ack(self, tag, result):

        cmdb = self.db.get_node(tag)
        
        # Is there an AB record for this seq_num?
        if cmdb.has_key('ack_time'):
            raise STARSintError("Error ack reply: duplicate record matching sequence number (%d)" % \
                                (cmdb.seq_num))

        # Record AB record for this seq_num
        self.db.setvals(self.monchannels, tag, ack_time=time.time(),
                        ack_result=result)

        # Is there a command record for this seq_num?  Should be.
        if not cmdb.has_key('cmd_time'):
            raise STARSintError("Error in ack reply: no command record matching sequence number (%d)" % \
                                (cmdb.seq_num))

        # Is there an FE record for this seq_num?  Should not be.
        if cmdb.has_key('end_time'):
            errmsg = "Error ack reply: end record exists matching sequence number (%d)" % (cmdb.seq_num)
            #raise STARSintError(errmsg)
            # Depending on network delays FE could arrive before AB...
            self.logger.warn(errmsg)

        # Error in AB result code?
        if result != 0:
            raise STARSintError("Error ack reply: result=%d" % result)
        

    # Command completion payload validator.
    #
    def validate_end(self, tag, status1, status2, result):

        cmdb = self.db.get_node(tag)
        
        # Is there an FE record for this seq_num?
        if cmdb.has_key('end_time'):
            raise STARSintError("Error end reply: duplicate end record matching sequence number (%d)" % \
                                (cmdb.seq_num))

        end_time = time.time()
        # Record FE record for this seq_num
        self.db.setvals(self.monchannels, tag, end_time=end_time,
                        end_status1=status1, end_status2=status2,
                        end_result=result)

        # Record transfer in Gen2 db transfer table
        if cmdb.has_key('frameid') and (cmdb.propid != 'summitlog'):
            xferDict = cmdb.xferDict
            xferDict.update(dict(time_done=datetime.datetime.fromtimestamp(end_time),
                                 res_code=result, res_str='OK'))
            framedb.addTransfer(cmdb.frameid, **xferDict)

        # Is there a command record for this seq_num?  Should be.
        if not cmdb.has_key('cmd_time'):
            raise STARSintError("Error in ack reply: no command record matching sequence number (%d)" % \
                                (cmdb.seq_num))

        # Is there an AB record for this seq_num? Should be.
        if not cmdb.has_key('ack_time'):
            errmsg = "Error end reply: no ack record matching sequence number (%d)" % (cmdb.seq_num)
            # Depending on network delays FE could arrive before AB...
            #raise STARSintError(errmsg)
            self.logger.warn(errmsg)

        if (status1 != 0) or (status2 != 0) or (result != 0):
            raise STARSintError("Error end reply: status1=%d, status2=%d, result=%d" % \
                                (status1, status2, result))

        try:
            total_bytes = cmdb.fitssize + cmdb.indexsize
            transfer_time = end_time - cmdb.ack_time
            rate = float(total_bytes) / (1024 * 1024) / transfer_time
            self.logger.info("Total transfer time %.3f sec (%.2f MB/s)" % (
                    transfer_time, rate))
        except Exception, e:
            self.logger.info("Error calculating transfer rate: %s" % (str(e)))


    def cmd_recv(self, rpcmsg):
                    
        # Until we have seq_num in payload we don't know which
        # command this is associated with
        tag = None
        seq_num = 0
        self.logger.debug("Recv: %s" % str(rpcmsg))

        try:
            # Call handler for appropriate rpc msg type
            if rpcmsg.msg_type == 'AB':
                try:
                    data = rpcmsg.unpack_ab()

                except SOSSrpc.rpcMsgError, e:
                    raise STARSintError("SOSS RPC payload format error: %s" % str(e))

                # Look up the transaction matching this seq_num
                seq_num = data.seq_num
                tag = self.get_trans(seq_num)

                # Validate payload
                self.validate_ack(tag, data.result)

            elif rpcmsg.msg_type == 'FE':
                try:
                    data = rpcmsg.unpack_fe()
                    
                except SOSSrpc.rpcMsgError, e:
                    raise STARSintError("SOSS RPC payload format error: %s" % str(e))
                
                seq_num = data.seq_num
                tag = self.get_trans(seq_num)

                # Validate payload
                self.validate_end(tag, data.status1, data.status2, data.result)

                # End command validated--notify waiters
                self.db.setvals(self.monchannels, tag,
                                msg='file sent successfully to STARS',
                                time_done=time.time(), done=True)

            else:
                raise STARSintError("Different reply than AB or FE!")

            # Delete our reference to the seq number mapping
            # so as not to leak memory
            if tag:
                self.del_trans(seq_num, tag)

        except STARSintError, e:
            # Errors thrown in send_fits trying to interface to
            # STARS end up here
            self.cmd_error(e, seq_num, tag)

        except Exception, e:
            self.cmd_error(e, seq_num, tag)
            raise e
                    

    # This is called when we have an error anywhere in the process of
    # sending a file to STARS.
    #
    def cmd_error(self, e, seq_num, tag):
        # Log the exception that led to us being called
        msg = str(e)
        self.logger.error(msg)

        # Plan B: contingency plan for this FITS file.  May be nothing
        # or could be special callback to Archiver, etc.
        self.planB(tag)
        
        if tag:
            # Signal to any waiters on this command that we are done
            self.db.setvals(self.monchannels, tag, msg=msg,
                            time_done=time.time(), done=True)

            # Add a record of the failed transfer to the Gen2 database
            # IF this is not a summit log archive request
            cmdb = self.db.get_node(tag)
            if cmdb.has_key('frameid'):
                propid = cmdb.get('propid')
                if propid != 'summitlog':
                    xferDict = cmdb.xferDict
                    xferDict.update(dict(time_done=datetime.datetime.now(),
                                         res_str=msg, res_code=-1))

                    # Record transfer in Gen2 db transfer table
                    framedb.addTransfer(cmdb.frameid, **xferDict)

            # Delete our reference to the cmdb so as not to leak memory
            self.del_trans(seq_num, tag)


    def planB(self, tag):
        """If the file cannot be sent to STARS for any reason, this method is
        called.
        """
        msg = 'STARS submission failed: %s' % str(tag)
        
        time_err = time.time()
        time_str = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(time_err))
        
        # Write an entry to the archiver journal
        errlog = os.path.join(os.environ['GEN2COMMON'],
                              'db', 'archive.errors')
        with open(errlog, 'a') as out_f:
            out_f.write("%s, %s\n" % (time_str, msg))

        # send an error message on the monitor, severity level 2
        tag = 'mon.error.2.STARSint.%s' % (time_str)
        self.db.setvals(['errors'], tag, msg=msg,
                        time_error=time_err)

    def submit_fits(self, tag):
        self.taskqueue.put(self.sendTasker(tag))


        
class STARSinterface(object):
    '''This class encompasses the STARS archive interface.
    '''

    def __init__(self, channels=[7,8], netifaces=None,
                 starshost=None, starsdir=None, 
                 logger=None, ev_quit=None, numthreads=None,
                 threadPool=None, db=None,
                 monchannels=['frames'], seq_num=None):

        self.channels = channels
        self.netifaces = netifaces
        self.starshost = starshost
        self.starsdir = starsdir
        self.numchannels = len(channels)
        self.chindex = 0
        self.channel = {}

        if not ev_quit:
            self.ev_quit = threading.Event()
        else:
            self.ev_quit = ev_quit

        if logger:
            self.logger = logger
        else:
            self.logger = ssdlog.NullLogger('STARSint')

        if numthreads:
            self.numthreads = numthreads
        else:
            # Estimate number of threads needed to handle traffic
            self.numthreads = 2 + (self.numchannels * 2)
            
        # Thread pool for autonomous tasks
        # If we were passed in a thread pool, then use it.  If not,
        # make one.  Record whether we made our own or not.  This
        # threadPool is shared by all interfaces.
        if threadPool != None:
            self.threadPool = threadPool
            self.mythreadpool = False

        else:
            self.threadPool = Task.ThreadPool(logger=self.logger,
                                              ev_quit=self.ev_quit,
                                              numthreads=self.numthreads)
            self.mythreadpool = True

        # Make/load the local monitor
        self.monchannels = monchannels
        if db:
            self.db = db
            self.mymonitor = False
        else:
            # TODO: should be based on svcname
            self.db = Monitor.Minimon('STARSint.mon', self.logger,
                                      threadPool=self.threadPool)
            self.mymonitor = True

        if seq_num:
            self.seq_num = seq_num
        else:
            # Share a sequence number between interfaces, or let each
            # interface generate it's own sequence numbers
            #self.seq_num = SOSSrpc.rpcSequenceNumber()
            self.seq_num = None

        # Object for checking/correcting FITS headers
        self.fitscheck = STARScheck.STARScheck(self.logger)
        # TEMP: until Mark fixes IRCQ frames
        self.fitscheck.startIgnorePfx('IRCQ')
        # TEMP: Minowa-san doesn't want any AO188 frames to go to STARS
        self.fitscheck.startIgnorePfx('AON')

        # Master queue for distributing work to threadpool
        self.taskqueue = Queue.Queue()

        # For task inheritance:
        self.tag = 'STARSint'
        self.shares = ['logger', 'ev_quit', 'timeout', 'threadPool']
        self.timeout = 0.1
        self.qtask = None

        # Make the channels for this STARS interface.
        self.make_channels(logger)


    # Create our set of "channels" to STARS.  Normal operation is
    # two channels (1,2: summit or 5,6: Fujitsu simulator or 7,8: SSD simulator)
    #
    def make_channels(self, logger):

        for i in xrange(len(self.channels)):
            ch_i = self.channels[i]
            if not self.netifaces:
                myhost = None
            else:
                myhost = self.netifaces[i]

            # Create a log for logging results
            if not logger:
                queue = Queue.Queue()
                log = ssdlog.mklog('ch%d' % ch_i, queue, logging.DEBUG)
            else:
                log = logger
                queue = None

            # Create STARS rpc interface object for channel 'ch_i'
            iface = STARSchannel(ch_i, self.ev_quit, log, self.db,
                                 self.taskqueue, self.fitscheck,
                                 starshost=self.starshost, starsdir=self.starsdir,
                                 monchannels=self.monchannels, myhost=myhost,
                                 seq_num=self.seq_num)

            # Create channel bundle object
            self.channel[ch_i] = Bunch(log=log, logqueue=queue, iface=iface)

        
    def get_threadPool(self):
        return self.threadPool
    
    def get_monitor(self):
        return self.db

    
    # start rpc clients and servers associated with each channel.
    #
    def start(self, wait=True):

        # Create a thread for the rpc server
        self.ev_quit.clear()

        # Start our thread pool (if we created it)
        if self.mythreadpool:
            self.threadPool.startall(wait=True)

        # Start our monitor (if we created it)
        if self.mymonitor:
            self.db.start(wait=True)
        
        # Initialize the task queue processing task
        t = Task.QueueTaskset(self.taskqueue, waitflag=False)
        self.qtask = t
        t.initialize(self)
        t.start()
        
        for i in self.channels:
            self.channel[i].iface.start(wait=wait)


    # stop rpc server.
    #
    def stop(self, wait=True):
        # Stop our monitor (if we created it)
        if self.mymonitor:
            self.db.releaseAll()        # Release all waiters
            self.db.stop(wait=True)
        
        for i in self.channels:
            self.channel[i].iface.stop(wait=wait)

        if self.qtask:
            self.qtask.stop()
        
        # Stop our thread pool (if we created it)
        if self.mythreadpool:
            self.threadPool.stopall(wait=wait)

        self.logger.info("STARS INTERFACE STOPPED.")
        self.ev_quit.set()


    # Submit a FITS file to STARS.
    # Files are distributed to channels in a round-robin fashion.
    #
    def submit_fits(self, tag, fitspath, propid=None, indexdir=None):
        """Submit a FITS file to STARS.  _tag_ is a task manager
        generated id for keeping track of this command.
        """

        self.logger.debug("tag=%s fits='%s'" % (tag, fitspath))
        try:
            # Get next channel to send to
            ch_i = self.channels[self.chindex]

            if self.db.has_key('%s.time_start' % tag):
                raise STARSintError("A command already exists with this tag")

            # Record time that request was submitted and path
            self.db.setvals(self.monchannels, tag,
                            time_start=time.time(), fitspath=fitspath)

            # Additionally record propid and indexdir, if supplied
            if propid:
                self.db.setvals(self.monchannels, tag, propid=propid)
            if indexdir:
                self.db.setvals(self.monchannels, tag, indexdir=indexdir)
        
            # Add send_cmd job to work queue
            self.channel[ch_i].iface.submit_fits(tag)
            
            # Set the chindex to point to the next channel for the
            # next transmission.
            self.chindex = (self.chindex + 1) % self.numchannels

        except STARSintError, e:
            msg = "Error submitting fits file to STARS: %s" % str(e)
            self.logger.error(msg)

            # Signal to any waiters on this command that we are done
            self.db.setvals(self.monchannels, tag, msg=msg,
                            time_done=time.time(), done=True)

    def submit_log(self, tag, logpath, indexdir, 
                   name, logstarttime, logendtime):
        """Submit a log file to STARS.  _tag_ is a task manager
        generated id for keeping track of this command.
        """

        self.logger.debug("tag=%s log='%s'" % (tag, logpath))
        try:
            # Get next channel to send to
            ch_i = self.channels[self.chindex]

            if self.db.has_key('%s.time_start' % tag):
                raise STARSintError("A command already exists with this tag")

            # Record time that request was submitted and path
            self.db.setvals(self.monchannels, tag,
                            time_start=time.time(), fitspath=logpath,
                            logstarttime=logstarttime,
                            logendtime=logendtime, name=name,
                            indexdir=indexdir,
                            propid='summitlog')

            # Add send_cmd job to work queue
            self.channel[ch_i].iface.submit_fits(tag)
            
            # Set the chindex to point to the next channel for the
            # next transmission.
            self.chindex = (self.chindex + 1) % self.numchannels

        except STARSintError, e:
            msg = "Error submitting log file to STARS: %s" % str(e)
            self.logger.error(msg)

            # Signal to any waiters on this command that we are done
            self.db.setvals(self.monchannels, tag, msg=msg,
                            time_done=time.time(), done=True)


    def delete_tag(self, tag):
        self.db.delete(tag, [])
        
        
def logmon(ch_i, queue, ev_quit):

    print "Monitoring log for channel %d" % ch_i
    while not ev_quit.isSet():

        line = queue.get()
        if line:
            print "CH(%d): %s" % (ch_i, line)

        else:
            ev_quit.wait(0.1)
            

# Encapsulate our remote object interface as a simple class
# 
class roSTARS(ro.remoteObjectServer):

    def __init__(self, svcname, stars, logger, port=None, usethread=False,
                 threadPool=None):

        self.stars = stars
        self.ev_quit = threading.Event()
        self.logger = logger

        # Superclass constructor
        ro.remoteObjectServer.__init__(self, svcname=svcname,
                                       port=port,
                                       ev_quit=self.ev_quit,
                                       logger=self.logger,
                                       usethread=usethread,
                                       threadPool=threadPool)

    ######################################
    # Methods provided by remote object interface
    ######################################

    def submit_fits(self, tag, fitspath):
        """Send a FITS file to STARS.
        """

        try:
            self.stars.submit_fits(tag, fitspath)
            return ro.OK

        except Exception, e:
            self.logger.error("Exception raised: %s" % str(e))
            return ro.ERROR


    def submit_log(self, tag, logpath, indexdir, 
                   name, logstarttime, logendtime):
        """Send a FITS file to STARS.
        """

        try:
            self.stars.submit_log(tag, logpath, indexdir,
                                  name, logstarttime, logendtime)
            return ro.OK

        except Exception, e:
            self.logger.error("Exception raised: %s" % str(e))
            return ro.ERROR


    def notify_data(self, filepath, filetype, md5sum, propid):

        self.logger.debug("Received notification: %s" % (filepath))

        # Hmmm..we are assuming that the file is named after the frameid...
        directory, filename = os.path.split(filepath)
        frameid, ext = os.path.splitext(filename)

        # Generate a tag based on frameid
        tag = ('mon.frame.%s.STARSint' % frameid)

        self.submit_fits(tag, filepath)

        return ro.OK


    def resend_fits(self, filepath):

        self.logger.debug("Resending: %s" % (filepath))

        # Hmmm..we are assuming that the file is named after the frameid...
        directory, filename = os.path.split(filepath)
        frameid, ext = os.path.splitext(filename)

        # Generate a tag based on frameid
        tag = ('mon.frame.%s.STARSint' % frameid)

        try:
            self.stars.delete_tag(tag)
        except KeyError:
            pass

        self.submit_fits(tag, filepath)

        return ro.OK

    def startIgnorePfx(self, pfx):
        self.stars.fitscheck.startIgnorePfx(pfx)

    def stopIgnorePfx(self, pfx):
        self.stars.fitscheck.stopIgnorePfx(pfx)


def main(options, args):

    svcname = options.svcname
    logger = ssdlog.make_logger(svcname, options)
    
    # If we were supplied a key to be a downstream data sink, then
    # register ourselves with the SessionManager
    if options.keyfile:
        keypath, keyfile = os.path.split(options.keyfile)
        keyname, ext = os.path.splitext(keyfile)
        try:
            in_f = open(options.keyfile, 'r')
            key = in_f.read().strip()
            in_f.close()

        except IOError, e:
            logger.error("Cannot open key file '%s': %s" % (
                options.keyfile, str(e)))
            sys.exit(1)

    elif options.key:
        key = options.key
        keyname = key.split('-')[0]

    else:
        key = None

    if options.passfile:
        try:
            in_f = open(options.passfile, 'r')
            passphrase = in_f.read().strip()
            in_f.close()

        except IOError, e:
            logger.error("Cannot open passphrase file '%s': %s" % (
                options.passfile, str(e)))
            sys.exit(1)

    elif options.passphrase != None:
        passphrase = options.passphrase
        
    else:
        passphrase = ''

    # NOTE: currently nothing is sent on the channel_cmd
    my_monitor_channels = [svcname, 'frames', 'errors']

    # Initialize remote objects subsystem.
    try:
        ro.init()

    except ro.remoteObjectError, e:
        logger.error("Error initializing remote objects subsystem: %s" % str(e))
        sys.exit(1)

    # Get hostname of STARS host.  If None, assume we are running on STARS
    # host.
# Need to fix this.  Each channel uses a different host (there is not just one).
# Second, other channel-specific parameters need to be put into options before we
# can get rid of the STARS_transferParams table.
##     if not options.starshost:
##         starshost = SOSSrpc.get_myhost(short=True)
##     else:
##         starshost = options.starshost
    starshost = options.starshost

    # Get list of channels to communicate with STARS host.
    channels = map(int, options.channels.split(','))
    for ch_i in channels:
        if not ch_i in [1,2,3,4,5,6,7,8]:
            print "Channels must be in the range 1-8"
            sys.exit(1)

    # Get list of interfaces to communicate with STARS host.
    if options.netifaces:
        netifaces = options.netifaces.split(',')
        if len(netifaces) != len(channels):
            print "Number of network interfaces must match number of channels"
            sys.exit(1)
    else:
        netifaces = None

    try:
        stars = STARSinterface(channels=channels,
                               netifaces=netifaces,
                               starshost=starshost,
                               starsdir=options.starsdir,
                               ev_quit=None,
                               db=None, logger=logger,
                               numthreads=options.numthreads)

        logger.info("STARS interface coming up.")
        stars.start(wait=True)

    except STARSintError, e:
        logger.error("Couldn't create/start STARS interface: %s" % str(e))
        sys.exit(1)
        
    # Start remote objects interface
    svc = None
    try:
        # Publish to the main monitor, if one was specified
        minimon = stars.get_monitor()
        if options.monitor:
            minimon.publish_to(options.monitor, my_monitor_channels, {})

        # Configure logger for logging via our monitor
        if options.logmon:
            minimon.logmon(logger, options.logmon, ['logs'])

        threadPool = stars.get_threadPool()
        
        # If we were supplied with a key then register ourselves with
        # the session manager as a downstream datasink
        if key:
            # Compute hmac
            hmac_digest = hmac.new(key, passphrase,
                                   digest_algorithm).hexdigest()
    
            sessions = ro.remoteObjectProxy('sessions')
            sessions.register_datasink(svcname, keyname, hmac_digest)
            
        try:
            svc = roSTARS(svcname, stars, logger, port=options.port,
                          usethread=False, threadPool=threadPool)

            svc.ro_start(wait=True)

        except KeyboardInterrupt:
            logger.error("Caught keyboard interrupt!")

    finally:
        logger.info("STARS interface shutting down.")
        if svc:
            svc.stars.stop(wait=True)
            #svc.ro_stop(wait=True)
            svc.ro_stop(wait=False)


if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("-c", "--channels", dest="channels", default="7,8",
                      help="List of numbered channels to use (1-8)")
    optprs.add_option("-C", "--clear", dest="clear", default=False,
                      action="store_true",
                      help="Clear the rpc transaction database on startup")
##  optprs.add_option("--db", dest="dbpath", metavar="FILE",
##                    help="Use FILE as the rpc transaction database")
    optprs.add_option("-d", "--dir", dest="starsdir", 
                      metavar="DIR",
                      help="Use DIR on the STARS host")
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-f", "--keyfile", dest="keyfile", metavar="NAME",
                      help="Specify authorization key in file NAME")
    optprs.add_option("-k", "--key", dest="key", metavar="KEY",
                      default='',
                      help="Specify authorization KEY")
    optprs.add_option("-m", "--monitor", dest="monitor", default=False,
                      metavar="NAME",
                      help="Reflect internal status to monitor service NAME")
    optprs.add_option("--netifaces", dest="netifaces", 
                      help="List of network interfaces to use for each channel")
    optprs.add_option("--numthreads", dest="numthreads", type="int",
                      default=50,
                      help="Use NUM threads for thread pool", metavar="NUM")
    optprs.add_option("--pass", dest="passphrase",
                      help="Specify authorization pass phrase")
    optprs.add_option('-p', "--passfile", dest="passfile", 
                      help="Specify authorization pass phrase file")
    optprs.add_option("--port", dest="port", type="int", default=None,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--starshost", dest="starshost",
                      help="Use HOST as the STARS host", metavar="HOST")
    optprs.add_option("--svcname", dest="svcname", metavar="NAME",
                      default=serviceName,
                      help="Register using NAME as service name")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    if len(args) != 0:
        optprs.error("incorrect number of arguments")


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
       
# END

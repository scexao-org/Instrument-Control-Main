#!/usr/bin/env python
#
# Archiver.py -- initiate various activities for incoming frames
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Dec 10 14:46:01 HST 2012
#]
#
"""
This program implements many of the features of the old SOSS Data Archive
System (DAQ).  The way it works is to create a monitor that subscribes to
the 'frames' channel of the main monitor.  Callback functions in the
Archiver class are registered, such that when information comes in about
a frame, the archiver knows about it.

TODO:
[X] needs to update multiple archivers (and remember where they are)
    -- use monitor channel?
[ ] needs to update archivers when key or properties have changed, not
    just when new clients are added
"""

import sys, re, os
import time, signal
import threading
import datetime as dt
import hashlib, hmac

import pyfits

import Gen2.client.datasink as Datasink
import Gen2.db.frame as framedb
import remoteObjects as ro
import remoteObjects.Monitor as Monitor
import logging, ssdlog
import Task
#import PubSub
import Bunch

from SOSS.SOSSrpc import rpcSequenceNumber
try:
    #from SOSS.STARSint import STARSdb
    #has_STARS = True
    # TEMP: disable STARS query function until we can debug occasional
    #   segfaults
    has_STARS = False
except ImportError:
    has_STARS = False
from cfg.INS import INSdata as INSconfig

serviceName = "archiver"

version = "20110329.0"

# Chose type of authorization encryption 
digest_algorithm = hashlib.sha1

# Default number of files to transfer in parallel
groups_of = 10

# Default size to break files into multiples of for PUSH transfers
chunk_size = 20 * 1024 * 1024

# Regex used to discover/parse frame info
regex_frame = re.compile(r'^mon\.frame\.(\w+)\.(\w+)$')

class ArchiveError(Datasink.SinkError):
    """Class used for raising exceptions in this module.
    """
    pass


def getFrameInfoFromPath(fitspath):
    # Extract frame id from file path
    (fitsdir, fitsname) = os.path.split(fitspath)
    (frameid, ext) = os.path.splitext(fitsname)
    
    match = re.match('^(\w{3})([AQ])(\d{8})$', frameid)
    if match:
        (inscode, frametype, frame_no) = match.groups()
        frame_no = int(frame_no)
        
        return Bunch.Bunch(frameid=frameid, fitsname=fitsname,
                           fitsdir=fitsdir, inscode=inscode,
                           frametype=frametype, frame_no=frame_no)

    raise ArchiveError("path does not match Subaru FITS specification")


def get_fits_info(fitspath, frameinfo, logger):
    """Gets meta data about this _fitspath_ from the FITS header
    and fills in the dictionary _frameinfo_.
    """

    try:
        fitsobj = pyfits.open(fitspath, 'readonly')

        try:
            prihdr = fitsobj[0].header

            # Pull values for the following fits cards.
            for key in ['FRAMEID', 'DATE-OBS', 'UT-STR', 'EXPTIME', 'OBS-MOD',
                        'OBJECT', 'DISPERSR', 'FILTER01', 'FILTER02',
                        'FILTER03', 'FILTER04', 'FILTER05', 'FILTER06',
                        'PROP-ID']:

                # If a key is not available, mark item as [N/A]
                if not prihdr.has_key(key):
                    # Special hack for VGW frames
                    if (key == 'UT-STR') and prihdr.has_key('UT'):
                        frameinfo[key] = prihdr['UT'].strip()
                    else:
                        frameinfo[key] = '[N/A]'
                else:
                    # If an item is not a string, convert it
                    if type(prihdr[key]) != str:
                        frameinfo[key] = str(prihdr[key]).strip()
                    else:
                        frameinfo[key] = prihdr[key].strip()

            # Meta key for all filter keywords found
            filterlist = []
            for key in ['DISPERSR', 'FILTER01', 'FILTER02', 'FILTER03',
                        'FILTER04', 'FILTER05', 'FILTER06']:
                if frameinfo[key] != '[N/A]':
                    filterlist.append(frameinfo[key])
            frameinfo['FILTERS'] = ','.join(filterlist)

            # TODO: see get_memo method in Archiver class
            frameinfo['MEMO'] = '[N/A]'

        finally:
            fitsobj.close()

    except IOError, e:
        raise ArchiveError("Cannot open FITS file '%s'" % (fitspath))


class ArchiverBase(object):
    """Archiver base class.  Has methods of interest for objects that have
    interest in frame info.
    """

    def __init__(self, logger, monitor):
        self.logger = logger
        self.monitor = monitor

        # We'll share our monitor's thread pool
        self.threadPool = self.monitor.get_threadPool()

        # Needed for starting our own tasks on it
        self.tag = 'Archiver'
        self.shares = ['logger', 'threadPool']

    def INSint_hdlr(self, frameid, path, value):
        """Called when something by any instrument interface appears.

        Interesting keys:
          time_start: time that the frame was attempted to be transferred
          time_done: time that the transfer attempt finished
          status: 0=success, anything else is an error
          msg: success/failure string
        """
        self.logger.debug("path: %s, value: %s" % (path, str(value)))

    def STARSint_hdlr(self, frameid, path, value):
        """Called when something by the STARS interface appears.

        Interesting keys:
          time_start: time that the frame was attempted to be archived
          time_done: time that the archive attempt finished
          end_result: 0=success, anything else is an error
          msg: success/failure string
        """
        self.logger.debug("path: %s, value: %s" % (path, str(value)))

    def frameSvc_hdlr(self, frameid, path, value):
        """Called when something by the frame service appears.

        Interesting keys:
          time_alloc: time that the frame was allocated
        """
        self.logger.debug("path: %s, value: %s" % (path, str(value)))

    def Archiver_hdlr(self, frameid, path, value):
        """Called when something by the Archiver appears.

        Interesting keys:
          fitsinfo: dictionary of fits headers
          md5sum: md5sum of fits file (if calculated)
        """
        self.logger.debug("path: %s, value: %s" % (path, str(value)))


    def remote_update(self, payload, name, channels):
        """Callback function from the monitor when we receive information
        about frames.
        """
        self.logger.debug("payload: %s" % str(payload))
        try:
            bnch = Monitor.unpack_payload(payload)
        
        except Monitor.MonitorError:
            # Silently ignore packets that are not in Monitor format
            return ro.OK
            
        match = regex_frame.match(bnch.path)
        if match:
            (frameid, subsys) = match.groups()

            try:
                method = getattr(self, '%s_hdlr' % subsys)

            except AttributeError:
                self.logger.debug("No handler for '%s' subsystem" % subsys)
                return ro.OK

            try:
                t = Task.FuncTask(method, [frameid, bnch.path, bnch.value], {},
                              logger=self.logger)
                t.init_and_start(self)
                return ro.OK
        
            except Exception, e:
                self.logger.error("Failed to start monitor update task for %s: %s" % (
                    frameid, str(e)))
                return ro.ERROR

        # Skip things that don't match the expected paths
        self.logger.error("No match for path '%s'" % bnch.path)
        return ro.OK

            
class Archiver(ArchiverBase, Datasink.DataSink):
    """
    Implements DAQ-like functions for Gen2.  Used in SOSS compatability mode.
    """
    def __init__(self, logger, monitor, monchannels=[],
                 realms=None, datadir='.', insconfig=None,
                 md5check=True, pullmethod='ftps', pullhost='localhost',
                 pullport=None,
                 pullname=None, xferlog=None, mountmangle=None):

        super(Archiver, self).__init__(logger, monitor)
        Datasink.DataSink.__init__(self, logger, datadir,
                                   md5check=md5check,
                                   pullhost=pullhost, pullport=pullport,
                                   pullmethod=pullmethod, pullname=pullname,
                                   xferlog=xferlog, mountmangle=mountmangle)

        self.monchannels = monchannels

        # Used to generate unique tags
        self.counter = rpcSequenceNumber()

        # Break PUSH transfers into this size chunks
        self.chunksize = chunk_size

        # Number of files to transfer in parallel
        self.max_group_size = groups_of
        # Maximum time to wait for a transfer to complete
        self.data_timeout = 240.0

        # Used to query info from STARS
        if has_STARS:
            try:
                self.starsdb = STARSdb(self.logger)
            except Exception, e:
                self.logger.warn("Can't create STARSdb object: %s" % (str(e)))
                self.logger.warn("STARS query will not be available")
                self.starsdb = None
        else:
            self.logger.warn("Can't import STARSdb module")
            self.logger.warn("STARS query will not be available")
            self.starsdb = None

        # List of realms we administer (summit, base, mitaka, etc.)
        if not realms:
            realms = []
        self.realms = realms
        
        # List of sink clients as remoteObjectClients
        self.clients = []
        # Cache of proxies to sink clients
        self._proxy = {}
        self.compress = True
        self.count_compress = 0
        self.ratio_compress = 0.0
        self.time_compress = 0.0

        self.tag_template = 'mon.frame.%s.INSint'
        self.insconfig = insconfig

    def _get_info(self, frameid):
        tag = 'mon.frame.%s.Archiver' % (frameid)
        info = self.monitor.getitems_suffixOnly(tag)
        if not isinstance(info, dict):
            return {}
        return info

    def _set_info(self, frameid, **kwdargs):
        tag = 'mon.frame.%s.Archiver' % (frameid)
        return self.monitor.setvals(['frames'], tag, **kwdargs)

    def _exists(self, info, key):
        return isinstance(info, dict) and info.has_key(key)

    # TODO: this is currently not connected to anything.  The memo should
    # be sent out on the frames channel if anything is found
    def get_memo(self, frameid, frameinfo):
        # Try to read a memo for this frame
        frameinfo['MEMO'] = '[N/A]'
        if self.fitsdir:
            try:
                memodir = self.fitsdir
                memofile = memodir + '/' + frameid + '.memo'
                with open(memofile, 'r') as memo_f:
                    memo = memo_f.read().strip()
                    frameinfo['MEMO'] = memo

            except IOError:
                pass

    ###########################################################
    #    ArchiverBase overrides
    ###########################################################

    def INSint_hdlr(self, frameid, path, vals):
        """
        Called when something by any instrument interface appears.

        Interesting keys:
          time_start: time that the frame was attempted to be transferred
          time_done: time that the transfer attempt finished
          done: True when transaction done
          status: 0=success, anything else is an error
          filepath: FITS file path on disk
          msg: success/failure string
        """

        lock = self.get_lock(frameid)
        with lock:
            info = self._get_info(frameid)

            self.logger.debug("path: %s, vals: %s" % (path, str(vals)))

            vals = self.monitor.getitems_suffixOnly(path)
            self.logger.debug("vals = %s" % str(vals))

            if not Monitor.has_keys(vals, ['done', 'time_done', 'status',
                                           'filepath']):
                # --> transaction still in progress
                self.logger.debug("Noting instrument transfer (%s) in progress..." % frameid)
                return

            if not self._exists(info, 'time_recv_notify'):
                
                if vals['status'] == 0: 
                    try:
                        # Mark that we did a notify
                        self._set_info(frameid, time_recv_notify=time.time())

                        # --> OCS has the file
                        fitspath = vals['filepath']
                        self.logger.info("Frame %s received OK." % (
                                frameid))

                        # Pick up some frame info for the observation journal
                        # and other interested clients
                        # TODO: send the whole fits header!??
                        frameinfo = {}
                        get_fits_info(fitspath, frameinfo, self.logger)
                        propid = frameinfo.get('PROP-ID', '')

                        frameinfo['fitspath'] = fitspath
                        frameinfo['SIZE'] = vals.get('filesize', 'N/A')
                        
                        self.logger.info("FITS metadata for %s is %s" % (
                                frameid, str(frameinfo)))
                    
                        # Push this metadata out onto the frames and fits channels
                        tag = 'mon.frame.%s.Archiver' % frameid
                        self.monitor.setvals(['frames', 'fits'], tag, **frameinfo)

                        # Get the md5sum if we are requiring it
                        md5sum = vals.get('md5sum', None)
                        if (not md5sum) and self.md5check:
                            try:
                                md5sum = self.calc_md5sum(fitspath)
                                self.logger.debug("Calculated md5sum as '%s'" % (md5sum))
                                
                                self.monitor.setvals(['frames'], tag, md5sum=md5sum)
                                
                            except Exception as e:
                                self.logger.error("md5sum calc error: %s" % (str(e)))
                                # ??? for now, proceeed with no md5sum
                        
                        # Initiate data sink transfers
                        self.notify_sinks(frameid, fitspath, propid, md5sum)

                    except Exception, e:
                        self.logger.error("Error notifying downstream for %s: %s" % (
                                frameid, str(e)))
                        try:
                            (type, value, tb) = sys.exc_info()
                            self.logger.error("Traceback:\n%s" % \
                                                  "".join(traceback.format_tb(tb)))

                            # NOTE: to avoid creating a cycle that might cause
                            # problems for GC--see Python library doc for sys
                            # module
                            tb = None

                        except Exception, e:
                            self.logger.error("Traceback information unavailable.")
                        

                else:
                    # TODO: need to log path on host and transfer mechanism
                    msg = "Instrument file transfer failed: %s" % (frameid)
                    self.logger.error(msg)
                    time_err = time.time()
                    time_str = time.strftime("%Y-%m-%d %H:%M:%S",
                                             time.localtime(time_err))

                    src_path = vals.get('srcpath', 'N/A')
                    err_msg  = vals.get('msg', msg)
                    
                    # Write an entry to the archiver journal
                    errlog = os.path.join(os.environ['GEN2COMMON'],
                                          'db', 'transfer.errors')
                    with open(errlog, 'a') as out_f:
                        out_f.write("%s, %s, %s, %s\n" % (time_str, frameid,
                                                          src_path, err_msg))

                    # Send a message on the errors channel
                    time_str = time_str.replace(' ', '_')
                    tag = 'mon.error.1.Archiver.%s' % (time_str)
                    self.monitor.setvals(['errors'], tag, msg=err_msg,
                                         frameid=frameid,
                                         time_error=time_err, 
                                         filepath=vals['filepath'])



    ###########################################################
    #    DataSink overrides
    ###########################################################
    
    def get_newpath(self, filename, filetype, propid):

        # Look up instrument name based on filename
        fr = getFrameInfoFromPath(filename)
        insname = self.insconfig.getNameByCode(fr.inscode)

        # Store data by instrument
        newpath = os.path.abspath(os.path.join(self.datadir, insname, filename))
        return newpath
    
        
    def receive_data(self, filename, buffer, offset, num, count,
                     compressed, filetype, md5sum, propid):
        # Pass on this piece to other PUSH sinks
        t = Task.FuncTask(self.push_sink_piece,
                          (filename, buffer, offset, num, count,
                           compressed, filetype, md5sum, propid), {},
                          logger=self.logger)
        t.init_and_start(self)

        # Save local copy
        return self.process_data(filename, buffer, offset, num, count,
                                 compressed, filetype, md5sum, propid)


    def notify_data(self, filepath, filetype, md5sum, propid):
        self.logger.debug("Attempting to copy %s" % (filepath))
        return self.pull_data(filepath, filetype, md5sum, propid)

        
    def notify(self, filepath, filetype, propid, md5sum,
               kind='pull'):
        self.logger.info("File received: %s" % filepath)

#        (frameid, fitsname, fitsdir, inscode,
#         frametype, frame_no) = getFrameInfoFromPath(filepath)
        fr = getFrameInfoFromPath(filepath)

        # Initiate appropriate data sink transfers
        # notify_method will be set according to how we received the file.
        # If we received the file via PUSH, then we have also forwarded
        # our packets to our PUSH sinks, so only need to notify other
        # kinds of sinks.  If we received via PULL/COPY, then we need to
        # notify all our sinks.
        if kind == 'push':
            notify_method = self.notify_pull_sinks
        else:
            notify_method = self.notify_sinks
        
        t = Task.FuncTask(notify_method,
                          (fr.frameid, filepath, propid, md5sum),
                          {}, logger=self.logger)
        t.init_and_start(self)

        
    ###########################################################
    #    Request transfer
    # NOTE: this code needs to be better integrated with the
    # code from INSint.  In particular, the file transfer logic
    # should be shared.
    ###########################################################
    
    def archive_framelist(self, host, transfermethod, framelist):

        self.logger.info("transfer request: %s" % (framelist))
        new_frlist = []
        total_bytes = 0
        
        while len(framelist) > 0:
            
            tup = framelist.pop(0)
            (frameid, fitspath) = tup[:2]

            if len(tup) == 2:
                size = None
                md5sum = None
                
            elif len(tup) == 3:
                size = tup[2]
                md5sum = None

            elif len(tup) == 4:
                size = tup[2]
                md5sum = tup[3]
                total_bytes += size

            else:
                raise ArchiveError("Unrecognized format of framelist")

            # Look up instrument name from the frameid
#            (frameid, fitsname, fitsdir, inscode,
#            frametype, frame_no) = getFrameInfoFromPath('%s.fits' % frameid)
            fr = getFrameInfoFromPath('%s.fits' % frameid)
            insname = self.insconfig.getNameByCode(fr.inscode)

            # Get defaults for host and transfer method, if not supplied
            insinfo = self.insconfig.getOBCPInfoByName(insname)
            if host.lower() == 'lookup':
                host = insinfo.get('obcphost', 'localhost')

            if transfermethod.lower() == 'lookup':
                transfermethod = insinfo.get('transfermethod', 'ftp')
            
            new_frlist.append((insname, frameid, fitspath,
                               host, transfermethod, size, md5sum))

        # For each frame on the frame list, attempt to transfer the file
        # and record in the monitor what happened.
        total_frames = len(new_frlist)
        if total_frames == 0:
            self.logger.info("Empty frame list, finishing up")
            return ro.OK

        # Figure out group size
        group_size = min(self.max_group_size, total_frames)

        group_num = total_frames // group_size
        extra_num = total_frames % group_size
        self.logger.info("%d rounds of %d, extra round of %d" % (group_num, group_size, extra_num))

        rounds = group_num
        if extra_num > 0:
            rounds += 1
        resultlist = []

        # Begin transferring groups
        time_xfer = time.time()

        # For each group, create a concurrent task containing individual tasks
        # to transfer the files
        for k in xrange(group_num):
            self.logger.info("Round %d/%d (group of %d)" % (k+1, rounds, group_num))
            tasklist = []
            resDict = Bunch.threadSafeBunch()
            index = 0

            for j in xrange(group_size):
                kwdargs = dict(index=index, resDict=resDict)
                tup = new_frlist.pop(0)

                t = Task.FuncTask(self.transfer, tup, kwdargs,
                                  logger=self.logger)
                tasklist.append(t)
                index += 1

            # Create a concurrent task to manage all the parallel transfers
            t = Task.ConcurrentAndTaskset(tasklist)

            # Preinitialize results to errors
            for i in xrange(index):
                resDict[i] = 1
            
            # Start the task and await the results
            result = 1
            try:
                t.init_and_start(self)

                # What is a reasonable timeout value?
                result = t.wait(timeout=self.data_timeout)
                self.logger.debug("result is %s" % (str(result)))

                # Check result (although task SHOULD raise an exception
                # if there is a problem with any of the subtasks
                if result in (None, 0):
                    result = 0
                else:
                    result = 1

            except Task.TaskError, e:
                pass

            statuslist = [ resDict[i] for i in xrange(index) ]

            resultlist.extend(statuslist)

        if extra_num > 0:
            tasklist = []
            resDict = Bunch.threadSafeBunch()
            index = 0

            self.logger.info("Round %d/%d (group of %d)" % (rounds, rounds, extra_num))
            for j in xrange(extra_num):
                kwdargs = dict(index=index, resDict=resDict)
                tup = new_frlist.pop(0)

                t = Task.FuncTask(self.transfer, tup, kwdargs,
                                  logger=self.logger)
                tasklist.append(t)
                index += 1

            # Create a concurrent task to manage all the parallel transfers
            t = Task.ConcurrentAndTaskset(tasklist)

            # Preinitialize results to errors
            for i in xrange(index):
                resDict[i] = 1
            
            # Start the task and await the results
            result = 1
            try:
                t.init_and_start(self)

                # What is a reasonable timeout value?
                result = t.wait(timeout=self.data_timeout)
                self.logger.debug("result is %s" % (str(result)))

                # Check result (although task SHOULD raise an exception
                # if there is a problem with any of the subtasks
                if result in (None, 0):
                    result = 0
                else:
                    result = 1

            except Task.TaskError, e:
                pass

            statuslist = [ resDict[i] for i in xrange(index) ]

            resultlist.extend(statuslist)

        time_end = time.time()

        # sanity check on individual results
        if sum(resultlist) != 0:
            result = 1
                
        # log any additional info?  statuslist?
        if result != 0:
            raise ArchiveError("File transfer request failed!")
            
        transfer_time = time_end - time_xfer
        if total_bytes > 0:
            rate = float(total_bytes) / (1024 * 1024) / transfer_time
            self.logger.info("Total transfer time %.3f sec (%.2f MB/s)" % (
                transfer_time, rate))
        else:
            self.logger.info("Total transfer time %.3f sec" % (
                transfer_time))

        return ro.OK
            

    def transfer(self, insname, frameid, fitspath,
                 host, transfermethod, size, md5sum,
                 resDict=None, index=None):
        """Transfer a single file from an instrument to Gen2.
        Parameters:
        insname: the instrument name
        frameid: the frame id of the file as provided by the instrument
        fitspath: the full file path as provided by the instrument
        host: the host name to transfer from as provided by the instrument
        transfermethod: the transfer protocol as provided by the instrument
        md5sum: an optional md5sum as provided by the instrument
        """

        tag = (self.tag_template % frameid)

        try:
            username = os.environ['LOGNAME']
        except KeyError:
            username = 'anonymous'
            
        # Get username for transfer
        insinfo = self.insconfig.getOBCPInfoByName(insname)
        username = insinfo.get('username', username)

        # Calculate new path on our side
        newpath = '%s/%s/%s.fits' % (self.datadir, insname, frameid)

        # check for file exists already; if so, rename it and allow the
        # transfer to continue
        self.check_rename(newpath)

        # Record start of transfer for this frame
        self.monitor.setvals(['frames'], tag, time_start=time.time(),
                             filepath=newpath, srcpath=fitspath)

        # TODO: try to integrate this code better with pull_data() in
        # the Datasink class
        msg = "No message"
        try:
            xferDict = dict(xfer_type='inst->gen2')
            
            # Copy file
            self.transfer_file(fitspath, host, newpath,
                               transfermethod=transfermethod,
                               username=username, result=xferDict,
                               md5sum=md5sum)

            # TEMP: FITS files are stored as -r--r-----
            os.chmod(newpath, 0440)

            # If instrument sent a file size, let's check that ours matches
            if size != None:
                # Stat the FITS file to get the size.
                try:
                    statbuf = os.stat(newpath)

                except OSError, e:
                    raise ArchiveError("Cannot stat file '%s': %s" % \
                                      (newpath, str(e)))

                if statbuf.st_size != size:
                    raise ArchiveError("File size (%d) does not match sent size (%d)" % (
                        statbuf.st_size, size))

            # Check the md5sum.  If instrument did not send one this only
            # logs a warning.
            if self.md5check:
                md5sum = self.check_md5sum(newpath, md5sum)

            msg = ("Received fits file %s.fits successfully!" % (frameid))
            xferDict.update(dict(res_str=msg, res_code=0, md5sum=md5sum))
            self.logger.info(msg)
            status = 0

        except Exception as e:
            errmsg = ("FITS archive error for frame id %s: %s" % \
                   (frameid, str(e)))
            xferDict.update(dict(res_str=errmsg, res_code=-1))
            self.logger.error(errmsg)
            # TODO: what is the proper error return value(s)?
            # All we know is 0=OK, non-zero is error
            status = 1

        # Record transfer in Gen2 db transfer table
        framedb.addTransfer(frameid, **xferDict)

        # If we are a part of a multi-file transfer, then store the result
        # of this transfer into our "slot" in the results dictionary
        if resDict != None:
            resDict[index] = status

        # Record end of transfer for this frame
        self.monitor.setvals(['frames'], tag, time_done=time.time(),
                             status=status, msg=msg, md5sum=md5sum,
                             done=True)

        # NOTE: we don't call notify here because the equivalent
        # result will happen through our monitor subscription to the
        # 'frames' channel (see INSint_hdlr() above)
        #return self.notify(newpath, filetype, propid, md5sum)

        return status

    ###########################################################
    #    Misc commands
    ###########################################################

    def set_md5check(self, enabled):
        """Toggle the md5 checksumming on or off.  parameter should
        be a boolean.
        """
        with self.lock:
            self.md5check = enabled
            self.logger.info("MD5 checksumming enabled=%s" % str(enabled))

        return ro.OK

    def set_chunksize(self, chunksize):
        """Change the chunk size used for PUSH datasink transfers.
        """
        with self.lock:
            self.chunksize = chunksize
            self.logger.info("Chunk size set to %d" % (chunksize))

        return ro.OK

    def set_compression(self, onoff):
        """Set whether compression is used for PUSH datasink transfers.
        """
        with self.lock:
            self.compress = onoff
            self.logger.info("Compression set to %s" % (str(onoff)))

        return ro.OK

    def get_compression_statistics(self):
        with self.lock:
            return (self.chunksize, self.count_compress,
                    self.ratio_compress, self.time_compress)

    def _retry_notify_data(self, filepath, filetype):
        """
        Called to retry a failed downstream transfer.
        """
        try:
            frameinfo = {}
            get_fits_info(filepath, frameinfo, self.logger)
            frameid = frameinfo.get('FRAMEID', None)
            propid = frameinfo.get('PROP-ID', None)

            # Get the md5sum if we are requiring it
            md5sum = None
            if self.md5check:
                md5sum = self.check_md5sum(fitspath, md5sum)
                
            assert (frameid != None) and (propid != None), \
                   ArchiverError("Missing FRAMEID or PROP-ID in %s" % (
                filepath))

            # Initiate data sink transfers
            return self.notify_data(filepath, filetype, propid, md5sum)

        except Exception, e:
            self.logger.error("Error notifying downstream: %s" % frameid)
            try:
                (type, value, tb) = sys.exc_info()
                self.logger.error("Traceback:\n%s" % \
                                  "".join(traceback.format_tb(tb)))
                
                # NOTE: to avoid creating a cycle that might cause
                # problems for GC--see Python library doc for sys
                # module
                tb = None
                
            except Exception, e:
                self.logger.error("Traceback information unavailable.")
                

    def retry_notify_data(self, filepath, filetype):
        self.logger.debug("Starting task to retry downstream transfer of %s" % (filepath))
        t = Task.FuncTask(self._retry_notify_data,
                          (filepath, filetype), {},
                          logger=self.logger)
        t.init_and_start(self)

        return 0

        
    ###########################################################
    #    Notifiers
    ###########################################################
    
    def notify_sinks(self, frameid, fitspath, propid, md5sum):

        self.logger.info("Notifying downstream of frame %s." % (
                frameid))
        # Get list of data sink clients
        with self.lock:
            clients = list(self.clients)

        self.logger.debug("len(clients)=%d" % (
            len(clients)))
        
        # Create a task to transfer to each client
        # Errors will be caught and logged by threadpool
        for client in clients:
            self.logger.debug("client %s n_type=%s" % (
                client, client.n_type))

            try:
                if client.filter and (not client.filter(frameid)):
                    self.logger.debug("Client %s: skipping %s, which doesn't match client filter" % (
                        client, frameid))
                    continue
                
                if client.n_type in ('pull', 'copy'):
                    t = Task.FuncTask(self.notify_datasink,
                                      (client, fitspath, 'fits', md5sum,
                                       propid), {}, logger=self.logger)
                    t.init_and_start(self)

                elif client.n_type == 'push':
                    t = Task.FuncTask(self.push_to_datasink,
                                      (client, fitspath, 'fits', md5sum,
                                       propid), {}, logger=self.logger)
                    t.init_and_start(self)

                else:
                    self.logger.error("Unknown client type: '%s'" % (
                        client.n_type))

            except Exception as e:
                self.logger.error("Failed to create task for sink: %s" % (
                    str(e)))


    def notify_pull_sinks(self, frameid, fitspath, propid, md5sum):

        self.logger.info("Notifying pull/copy sinks of frame %s." % (
                frameid))
        # Get list of data sink clients
        with self.lock:
            clients = list(self.clients)

        # Create a task to transfer to each client
        # Errors will be caught and logged by threadpool
        for client in clients:

            try:
                if client.n_type in ('pull', 'copy'):
                    t = Task.FuncTask(self.notify_datasink,
                                      (client, fitspath, 'fits', md5sum,
                                       propid), {}, logger=self.logger)
                    t.init_and_start(self)

            except Exception as e:
                self.logger.error("Failed to create task for sink: %s" % (
                    str(e)))


    def _push_sink_piece_client(self, client, filename, buffer, offset,
                               num, count, compressed,
                                filetype, md5sum, propid):
        try:
            client.receive_data(filename, buffer, offset, num, count,
                                compressed, filetype, md5sum, propid)

        except Exception as e:
            self.logger.error("Failed to push %s piece %d/%d to %s: %s" % (
                filename, num, count, client, str(e)))
            # TODO: AND ???


    def push_sink_piece(self, filename, buffer, offset, num, count,
                        compressed, filetype, md5sum, propid):
        """Pass on a piece of a file to all of our PUSH customers.  PULL
        and COPY sinks need to wait until we have the complete file.
        """

        ## self.logger.info("Notifying downstream of frame %s." % (
        ##         frameid))
        # Get list of data sink clients
        with self.lock:
            clients = list(self.clients)

        # Create a task to transfer to each client
        # Errors will be caught and logged by threadpool
        for client in clients:
            
            if client.filter and (not client.filter(filename)):
                self.logger.debug("Client %s: skipping %s, which doesn't match client filter" % (
                    client, filename))
                continue

            if client.n_type == 'push':
                t = Task.FuncTask(self._push_sink_piece_client,
                                  (client, filename, buffer, offset,
                                   num, count, compressed,
                                   filetype, md5sum, propid), {},
                                  logger=self.logger)
                t.init_and_start(self)


    def compress_buffer(self, fitsbuf):
        time_start = time.time()
        len_before = len(fitsbuf)
        fitsbuf = ro.compress(fitsbuf)
        len_after = len(fitsbuf)
        ratio = float(len_before) / float(len_after)
        time_elapsed = time.time() - time_start
        self.logger.debug("Compression ratio is %.2f%% (%d/%d) %.2f sec" % (
            ratio, len_before, len_after, time_elapsed))

        with self.lock:
            # Update running averages
            count = self.count_compress
            self.count_compress += 1
            self.ratio_compress = (((self.ratio_compress * count) + ratio) /
                                   self.count_compress)
            self.time_compress = (((self.time_compress * count) + time_elapsed) /
                                   self.count_compress)

        return fitsbuf

    def push_to_datasink(self, client, fitspath, filetype, md5sum,
                         propid):

        with self.lock:
            do_compress = self.compress
            chunksize = self.chunksize
            
        # TODO: share reading the file and encoding among all PUSH clients
        try:
            # Stat the FITS file to get the size.
            try:
                statbuf = os.stat(fitspath)

            except OSError, e:
                raise ArchiveError("Cannot stat file '%s': %s" % \
                                  (fitspath, str(e)))

            # Figure out how many chunks we need to break this into
            size = statbuf.st_size
            chunks = size // chunksize
            if (size % chunksize) > 0:
                chunks += 1

            dirname, filename = os.path.split(fitspath)

            with open(fitspath, 'r') as in_f:

                offset = 0
                for i in xrange(chunks):

                    fitsbuf = in_f.read(chunksize)

                    if do_compress:
                        fitsbuf = self.compress_buffer(fitsbuf)
                        
                       
                    # Encode buffer for XMLRPC transport
                    fitsbuf = ro.binary_encode(fitsbuf)

                    with client.limit:
                        self.logger.debug("Transmitting %d/%d to %s" % (
                            i+1, chunks, client))
                        client.receive_data(filename, fitsbuf, offset,
                                            i+1, chunks, do_compress,
                                            filetype, md5sum, propid)

                    offset += chunksize

        except Exception, e:
            self.logger.error("Failed to push %s to %s: %s" % (
                filename, client, str(e)))
            # TODO: AND ???

    def notify_datasink(self, client, filepath, filetype, md5sum,
                        propid):
        dirname, filename = os.path.split(filepath)
        try:
            with client.limit:
                self.logger.info("Notifying %s to %s" % (
                    filepath, client))
                client.notify_data(filepath, filetype, md5sum, propid)

        except Exception, e:
            self.logger.error("Failed to notify %s to %s: %s" % (
                filename, client, str(e)))
            # TODO: AND ???


    def cb_datasinks(self, valDict, name, channels):
        self.logger.debug("valDict: %s" % str(valDict))

        # TODO: remove or add only changed sinks
        self.init_datasinks()

        
    def clear_proxy_cache(self):
        with self.lock:
            self._proxy = {}
            
    def get_proxy(self, svc, n_type, limit, use_cached=True):

        if isinstance(svc, list):
            (host, port) = svc
            key = (host, port)
        elif ':' in svc:
            (host, port) = svc.split(':')
            port = int(port)
            key = (host, port)
        else:
            key = svc

        if use_cached and self._proxy.has_key(key):
            proxy = self._proxy[key]
        else:
            if isinstance(key, tuple):
                (host, port) = key
                proxy = ro.remoteObjectClient(host, port)
            else:
                proxy = ro.remoteObjectProxy(svc)

            self._proxy[key] = proxy

        # Store type: 'push' or 'pull' into proxy obj
        proxy.n_type = n_type
        proxy.limit  = threading.Semaphore(limit)
        proxy.filter = None
        return proxy


    def setup_datasinks(self, sinks):
        """The SessionManager calls this method when the configuration of
        data sink keys has changed.  Re-obtain proxies to all downstream
        clients.

        _sinks_ is a dictionary, where each key is a datasink key and the
        value is a list of (host, port) values.
        """

        self.logger.info("Resetting datasinks.")
        sorted = []
        with self.lock:
            # Recalculate list of clients
            self.clients = []

            for dataKey, fields in sinks.items():

                if not fields:
                    continue
                
                properties = fields['properties']
                
                # skip realms other than we are responsible for
                realm = properties.get('realm', 'N/A').lower()
                if not (realm in self.realms):
                    continue

                # Skip disabled keys
                enabled = properties.get('enable', 'NO').lower()
                if enabled != 'yes':
                    self.logger.debug("Skipping disabled key %s" % (
                            dataKey))
                    continue

                # skip types other than we have implemented
                n_type = properties.get('type', 'N/A').lower()
                if not (n_type in ['push', 'pull', 'copy']):
                    self.logger.warn("Unknown type '%s' for key %s ...skipping" % (
                            n_type, dataKey))
                    continue

                # sort by priority (default is middle)
                priority = properties.get('priority', '5')

                # get connection limits
                limit = int(properties.get('limit', '2'))

                # load up proxies for registered clients
                for svc in fields['clients']:
                    proxy = self.get_proxy(svc, n_type, limit)
                    sorted.append([priority, proxy])

            # Sort by priority and reset clients
            sorted.sort()
            self.clients = [x[1] for x in sorted]

            self.logger.debug("Made clients to data sinks")

        
    def init_datasinks(self):
        """Initialize data sinks (destinations for data files).  We call the
        SessionManager to obtain the current registrations and initialize
        our client list.
        """

        try:
            sessions = ro.remoteObjectProxy('sessions')
            sinks = sessions.get_datasinks()

            self.setup_datasinks(sinks)

        except ro.remoteObjectError, e:
            self.logger.error("Couldn't fetch data sinks from SessionManager")


def server(options, args):

    if len(args) != 0:
        print "Usage: %s [options]"
        print "Use '%s --help' for options"
        sys.exit(1)

    svcname = options.svcname
    # TODO: parameterize monitor channels
    monchannels = ['frames', 'datakeys']
        
    # Create top level logger.
    logger = ssdlog.make_logger(svcname, options)

    # If we were supplied a key to be a downstream data sink, then
    # register ourselves with the SessionManager
    if options.keyfile:
        keypath, keyfile = os.path.split(options.keyfile)
        keyname, ext = os.path.splitext(keyfile)
        try:
            with open(options.keyfile, 'r') as in_f:
                key = in_f.read().strip()

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
            with open(options.passfile, 'r') as in_f:
                passphrase = in_f.read().strip()

        except IOError, e:
            logger.error("Cannot open passphrase file '%s': %s" % (
                options.passfile, str(e)))
            sys.exit(1)

    elif options.passphrase != None:
        passphrase = options.passphrase
        
    else:
        passphrase = ''

    cfg = {}
    if options.inscfg:
        try:
            with open(options.inscfg, 'r') as in_f:
                buf = in_f.read()

            d = eval(buf)
            insconfig = INSconfig(info=d)
            
        except IOError, e:
            logger.error("Error opening instrument configuration '%s': %s" % (
                    options.inscfg, str(e)))
            sys.exit(1)
    else:
        insconfig = INSconfig()

    # Initialize remote objects subsystem.
    try:
        ro.init()

    except ro.remoteObjectError, e:
        logger.error("Error initializing remote objects subsystem: %s" % str(e))
        sys.exit(1)

    svc = None
    svr_started = False
    minimon = None
    mon_svr_started = False

    # Global termination flag
    ev_quit = threading.Event()
    
    def quit():
        logger.info("Shutting down archiver service...")
        if svr_started:
            svc.ro_stop(wait=False)
        if minimon:
            if mon_svr_started:
                minimon.stop_server(wait=True)
            minimon.stop(wait=True)

    def SigHandler(signum, frame):
        """Signal handler for all unexpected conditions."""
        logger.error('Received signal %d' % signum)
        quit()
        ev_quit.set()

    # Set signal handler for signals
    #signal.signal(signal.SIGINT, SigHandler)
    signal.signal(signal.SIGTERM, SigHandler)

    logger.info("Starting archiver service...")
    try:
        # Create mini monitor to reflect to main monitor
        mymonname = ('%s.mon' % svcname)
        minimon = Monitor.Monitor(mymonname, logger,
                                  numthreads=options.numthreads)
        #minimon = PubSub.PubSub(mymonname, logger, numthreads=options.numthreads)
        minimon.start()
        mon_started = True

        if options.monitor:
            # Publish our channels of interest to the specified monitor
            minimon.publish_to(options.monitor, ['frames', 'fits', 'errors'],
                               {})

        # Configure logger for logging via our monitor
        if options.logmon:
            minimon.logmon(logger, options.logmon, ['logs'])

        # Set realms of operation
        realms = []
        if options.realm:
            realms = options.realm.split(',')

        if options.datadir:
            datadir = options.datadir
        else:
            try:
                # TODO: Get from g2soss
                datadir = os.environ['DATAHOME']
            except KeyError:
                datadir = '.'
            
        pullport = None
        if options.pullport:
            pullport = int(options.pullport)

        # Create archiver object
        archiver = Archiver(logger, minimon, monchannels=monchannels,
                            realms=realms, datadir=datadir,
                            insconfig=insconfig, md5check=options.md5check,
                            pullhost=options.pullhost,
                            pullport=pullport,
                            pullmethod=options.pullmethod,
                            pullname=options.pullname, xferlog=options.xferlog)

        # Register archiver callbacks to monitor channels
        if not key:
            minimon.subscribe_cb(archiver.remote_update, ['frames'])
            
        minimon.subscribe_cb(archiver.cb_datasinks, ['datakeys'])
        minimon.start_server(port=options.monport, usethread=True)
        mon_svr_started = True

        threadPool = minimon.get_threadPool()
        
        if options.monitor:
            # Subscribe ourselves to information of interest
            minimon.subscribe_remote(options.monitor, monchannels, {})

        archiver.init_datasinks()

        # If we were supplied with a key then register ourselves with
        # the session manager as a downstream datasink
        if key:
            # Compute hmac
            hmac_digest = hmac.new(key, passphrase,
                                   digest_algorithm).hexdigest()
    
            sessions = ro.remoteObjectProxy('sessions')
            sessions.register_datasink(options.svcname, keyname, hmac_digest)
            
        svc = ro.remoteObjectServer(svcname=options.svcname,
                                    obj=archiver, logger=logger,
                                    port=options.port,
                                    default_auth=None,
                                    ev_quit=ev_quit,
                                    usethread=False,
                                    threadPool=threadPool)
        try:
            print "Press ^C to terminate the server."
            svc.ro_start(wait=True)
            svr_started = True

        except KeyboardInterrupt:
            logger.error("Caught keyboard interrupt!")
            
    finally:
        quit()
        
    logger.info("Stopping archiver service...")


if __name__ == '__main__':
    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("-d", "--datadir", dest="datadir",
                      metavar="DIR",
                      help="Specify DIR to store FITS files")
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-f", "--keyfile", dest="keyfile", metavar="NAME",
                      help="Specify authorization key in file NAME")
    optprs.add_option("--inscfg", dest="inscfg", metavar="FILE",
                      help="Read instrument configuration data from FILE")
    optprs.add_option("-k", "--key", dest="key", metavar="KEY",
                      default='',
                      help="Specify authorization KEY")
    optprs.add_option("--pass", dest="passphrase",
                      help="Specify authorization pass phrase")
    optprs.add_option('-p', "--passfile", dest="passfile", 
                      help="Specify authorization pass phrase file")
    optprs.add_option("--port", dest="port", type="int", default=None,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("-m", "--monitor", dest="monitor", default='monitor',
                      metavar="NAME",
                      help="Subscribe to feeds from monitor service NAME")
    optprs.add_option("--monport", dest="monport", type="int", default=None,
                      help="Register monitor using PORT", metavar="PORT")
    optprs.add_option("--mountmangle", dest="mountmangle", 
                      help="Specify a file prefix transformation for NFS copies")
    optprs.add_option("--nomd5check", dest="md5check", action="store_false",
                      default=True,
                      help="Suppress MD5 checks for speed")
    optprs.add_option("--numthreads", dest="numthreads", type="int",
                      default=50,
                      help="Use NUM threads", metavar="NUM")
    optprs.add_option("--realm", dest="realm", 
                      metavar="NAME",
                      help="Administer realm NAME (or comma separated list)")
    optprs.add_option("--server", dest="server", default=False,
                      action="store_true",
                      help="Run the server instead of client")
    optprs.add_option("--svcname", dest="svcname", metavar="NAME",
                      default=serviceName,
                      help="Register using NAME as service name")
    optprs.add_option("--pullhost", dest="pullhost", metavar="NAME",
                      default='localhost',
                      help="Specify NAME for a file transfer host")
    optprs.add_option("--pullport", dest="pullport", 
                      help="Specify PORT for a file transfer port",
                      metavar="PORT")
    optprs.add_option("--pullmethod", dest="pullmethod",
                      default='ftps',
                      help="Use METHOD (ftp|ftps|sftp|http|https|scp|copy) for transferring FITS files")
    optprs.add_option("--pullname", dest="pullname", metavar="USERNAME",
                      default='anonymous',
                      help="Login as USERNAME for ftp/scp transfers")
    optprs.add_option("--workers", dest="workers", metavar="NUM",
                      type="int", default=10,
                      help="Specify number of work threads")
    optprs.add_option("--xferlog", dest="xferlog", metavar="FILE",
                      default="/dev/null",
                      help="Specify log file for transfers")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    # Are we debugging this?
    if options.debug:
        import pdb

        pdb.run('server(options, args)')

    # Are we profiling this?
    elif options.profile:
        import profile

        print "%s profile:" % sys.argv[0]
        profile.run('server(options, args)')

    elif options.server:
        server(options, args)

    else:
        raise ArchiveError("I don't know what to do!")
    
#END

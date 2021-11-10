#!/usr/bin/env python
#
# Monitor.py -- internal status monitoring and synchronization
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Apr 19 14:51:02 HST 2013
#]
#
"""
The Monitor and Minimon classes are subclasses of the PubSubsetvals class.

They differ from the more generic PubSub class in the following ways:

- The value passed from publisher to subscribers is always assumed to be a
  dictionary object conforming to certain characteristics.

- The value is stored into a local storage object before notifying
  subscribers, whether local or remote.

- There are a variety of access methods to read the data from the local
  store.

- For Minimon objects, the local store has synchronization that allows
  readers to block efficiently until data becomes available.
  

Important definitions:
    path        A dot-separated string of the form t0.t1.t2 ... .tN, that
                describes a path into a hierarchically named storage space
                t0 is the name of a top-level node, t1 is the name
                of an entry under that, t2 is an entry filed under t1, etc.
                tN may represent a 'leaf' value or not.

    tag         gen2 term for 'path'--in particular, a path that refers to
                a node that will have values stored into it.  This term not
                used much in this module.  In general, subsystems that do not
                care about the leading path, but only values stored under
                that path refer to the leading path as a 'tag'.

    value       the value associated with a path may be any Python data type
                (or any RemoteObject-compatible data type, if the monitor is
                to be accessed/synchronized remotely).  See also 'node'.

    node        A value that is a container of other values--a 'folder'.

    channel     An identifier that is associated with changes made to the
                storage space by a monitor.  Other monitors that subscribe
                to the same channel will receive update and delete calls to
                reflect the changes to their storage spaces.

Main issues to think about/resolve:
   
    [X] Deleting data (esp. wrt. bidirectional subscriptions)
"""
# remove once we're certified on python 2.6
from __future__ import with_statement

import sys, re
import time
import string
import threading
import Queue
import logging

import Task
import Bunch, NestedBunch
import remoteObjects as ro
import PubSub as ps
import ssdlog

serviceName = 'monitor'

version = '20100128.0'


class MonitorError(ps.PubSubError):
    """General class for exceptions raised by Monitor.
    """
    pass

class TimeoutError(MonitorError):
    """Exception class that is thrown when timing out waiting for a value
    to be set in a Minimon.
    """
    pass

class EventError(MonitorError):
    """Exception class that is thrown when interrupted waiting for a value
    to be set in a Minimon.
    """
    pass


def unpack_payload(payload):
    # Skip packets that are not in Monitor format
    if not isinstance(payload, dict) or (not payload.has_key('msg')):
        raise MonitorError("PubSub value is not a Monitor payload: %s" % (
                str(payload)))
            
    return Bunch.Bunch(payload)


def has_keys(valDict, keys):
    """Check whether dictionary _valDict_ has all the keys in _keys_."""
    for key in keys:
        if not valDict.has_key(key):
            return False
    return True
    

# TODO: should this also inherit from NestedBunch?  Would save having to
# define a bunch of delegate calls, but would lose generality of 3rd party
# store
#
class Monitor(ps.PubSub):

    def __init__(self, name, logger, dbpath=None, useSync=False,
                 ev_quit=None, threadPool=None, numthreads=20):

        self._store = NestedBunch.NestedBunch(dbpath=dbpath)
        self.defaultChannels = [name]

        self.lock = threading.RLock()

        # TEMP: to get around an infinite recursion issue for monitor
        # logging
        logger = ro.nullLogger()

        # Superclass initialization
        super(Monitor, self).__init__(name, logger,
#                                      ev_quit=None, threadPool=None,
                                      ev_quit=ev_quit, threadPool=threadPool,
                                      numthreads=numthreads)
            
        # number of seconds after which a delivery to a subscriber is
        # considered "late"
        self.update_limit = 10.0

    # INTERNAL INTERFACE
    
    def do_update(self, path, value):
        # Update items in our store
        with self.lock:
            self._store.update(path, value)

    def do_delete(self, path):
        # Delete item from our store
        with self.lock:
            self._store.delitem(path)

    # CALLED BY MONITOR USERS TO SAVE/RESTORE THEIR STATE
    
    def save(self):
        with self.lock:
            self._store.save()
        
    def restore(self):
        with self.lock:
            self._store.restore()

    # PUBSUB INTERFACE
    
    def remote_update(self, payload, names, channels):
        """method called by PubSub to notify us with items.
        """
        # Avoid cyclic dependencies--don't update ourselves if we
        # originated this event
        if self.name in names:
            return ro.OK

        bnch = unpack_payload(payload)

        # Check for late delivery of monitor messages
        if bnch.has_key('time_pack'):
            elapsed = time.time() - bnch.time_pack
            if elapsed > self.update_limit:
                self.logger.warn("delivery time (%f) exceeded limit (%f); names=%s" % (
                    elapsed, self.update_limit, names))

        msg = bnch.msg.lower()

        if msg == 'update':
            self.do_update(bnch.path, bnch.value)

        elif msg == 'delete':
            self.do_delete(bnch.path)
                
        else:
            raise MonitorError("Unrecognized 'msg' field: %s" % (msg))

        # Then update any of our subscribers
        return super(Monitor, self).remote_update(payload, names, channels)


    def update(self, path, value, channels):
        """
        Method called by local users of this Monitor to update it
        with new and changed items.
            path        path whose value will be updated
            value
            channels    one (a string) or more (a list) of channel names to
                        which to send the specified update
        """
        # TODO: should this all be in a critical section?
        self.do_update(path, value)
        
        payload = dict(msg='update', path=path, value=value,
                       time_pack=time.time())
        
        return self.notify(payload, channels)


    def delete(self, path, channels):
        """
        Method called by local users of this Monitor to delete items.
            path        path to a value which will be deleted
            channels    one (a string) or more (a list) of channel names to
                        which to send a deletion command for the specified
                        path
        """
        # TODO: should this all be in a critical section?
        self.do_delete(path)

        payload = dict(msg='delete', path=path,
                       time_pack=time.time())
        
        return self.notify(payload, channels)


    ###########################################################
    
    def setvals(self, channels, path, **values):
        """Similar method to update(), but uses keyword arguments as the
        value (a dict) to store.
        """
        return self.update(path, values, channels)
    

    def get_nowait(self, pfx, key):
        """Try to get a status value associated with the path formed by
        concatenating _pfx_ and _key_ in the table.  Returns a tuple
        (True, value) if the get was successful, and (False, exception)
        if there was no value present.
        """
        path = '.'.join((pfx, key))
        
        with self.lock:
            try:
                val = self.getitem(path)
                return (True, val)
        
            except KeyError, e:
                return (False, e)

    # DELEGATE OBJECT METHODS, with locking

    def getitem(self, path):
        """Non-blocking get.
            path    path for desired value
        """
        with self.lock:
            return self._store.getitem(path)

    
    def getitems(self, path):
        """Get the status values associated with this path in the table.
        If successful, then return a dictionary of the items found, otherwise
        return an error code.
        """
        
        with self.lock:
            try:
                return self._store.getitems(path)

            except KeyError:
                return ro.ERROR


    def getitems_suffixOnly(self, path):
        """Get the status values associated with this path in the table.
        If successful, then return a dictionary of the items found, otherwise
        return an error code.
        """
        
        with self.lock:
            try:
                return self._store.getitems_suffixOnly(path)

            except KeyError:
                return ro.ERROR


    def getTree(self, path):
        """Get the status values associated with this path in the table.
        If successful, then return a dictionary of the items found, otherwise
        return an error code.
        """
        
        with self.lock:
            try:
                return self._store.getTree(path)

            except KeyError:
                return ro.ERROR
        

    def get_node(self, path, create=False):
        """Get the leaf dict for dotted path _path_. 
        """
        with self.lock:
            return self._store.get_node(path, create=create)


    def get_dict(self, path):
        """Same as get_node, but returns a dict."""
        with self.lock:
            b = self.get_node(path, create=False)
            # TODO: optomize this
            return eval(repr(b))


    def keys(self, path):
        with self.lock:
            try:
                return self._store.keys(path=path)

            except KeyError:
                return ro.ERROR


    def has_key(self, path):
        with self.lock:
            return self._store.has_key(path)


    def has_val(self, path, key):
        with self.lock:
            return self._store.has_key('%s.%s' % (path, key))


    def isLeaf(self, path):
        with self.lock:
            try:
                return self._store.isLeaf(path)

            except KeyError:
                return ro.ERROR


    def logmon(self, logger, svcname, channels):
        try:
            # Subscribe specified monitor to our log feed
            self.subscribe(svcname, channels, {})

            # Find the MonitorHandler and set the monitor to ourself.
            # At the time the logger is created, this is not usually set
            for hdlr in logger.handlers:
                if isinstance(hdlr, MonitorHandler):
                    # TODO: could also override default handler parameters here
                    hdlr.set_monitor(self)

                    # Start a thread to processing the log messages
                    t = Task.FuncTask2(hdlr.process_queue, self.ev_quit)
                    t.init_and_start(self)

        except Exception, e:
            logger.error("Error attaching monitor to logging handler: %s" % (
                str(e)))
        
##     def setvals(self, channels, path, **values):
##         if not channels:
##             channels = self.defaultChannels
            
##         return self.update(path, values, channels)
    

    # Get deprecate these item interface methods if we remove dict-style
    # uses of these objects
    
    def __getitem__(self, path):
        """Called for dictionary style access of this object.
        """
        return self.getitem(path)


    def __setitem__(self, path, value):
        """Called for dictionary style access with assignment.
        """
        return self.update(path, value, self.defaultChannels)
        

    def __delitem__(self, path):
        """Deletes key/value pairs from object.
        """
        return self.delete(path, self.defaultChannels)


class Minimon(Monitor):
    """A Minimon is like a Monitor, but adds support for local
    synchronization of threads.

    TODO: how many of these methods can we deprecate
    """

    def __init__(self, name, logger, dbpath=None, useSync=False, 
                 ev_quit=None, threadPool=None, numthreads=20):

        # dictionary of lists of condition variables for synchronization
        self.syncd = {}

        # Intervals to wait between checks for interruptions
        self.wait_interval = 0.1

        super(Minimon, self).__init__(name, logger,
                                      ev_quit=ev_quit,
                                      threadPool=threadPool,
                                      numthreads=numthreads)
            
    def getitem(self, path, block=True, timeout=None):
        with self.lock:
            try:
                return self._store.getitem(path)

            except KeyError, e:
                if not block:
                    raise e

                d = self.getitem_any([path], timeout=timeout)
                return d.values()[0]
        
    
    def get_wait(self, pfx, key, timeout=None):

        return self.getitem('%s.%s' % (pfx, key), timeout=timeout)

    
    def release(self, path, has_value=False):
        with self.lock:
            self.logger.debug("RELEASING on %s" % (path))
            try:
                l = self.syncd[path]

                # release any waiters on this path
                for i in xrange(len(l)):
                    (ev_store, cond) = l.pop(0)
                    # Set flag to true if a value was stored
                    if has_value:
                        ev_store.set()
                    with cond:
                        cond.notifyAll()

                del self.syncd[path]
            except KeyError:
                pass
                        
            return ro.OK
    
    def releaseAll(self):
        with self.lock:
            for path in self.syncd.keys():
                self.release(path)
                
            return ro.OK

    def _getitems_list(self, tags):
        res = {}

        for path in tags:
            try:
                res[path] = self._store.getitem(path)

            except KeyError, e:
                # Store does not contain item.
                continue

        return res
        

    def getitem_any(self, tags, timeout=None, eventlist=None):

        start_time = time.time()
        with self.lock:
            # if there are any tags found, return this set
            res = self._getitems_list(tags)
            if len(res) > 0:
                return res

            # Quick check on timeout to avoid a lot of work 
            if (timeout != None) and (time.time() - start_time >= timeout):
                raise TimeoutError("Timed out waiting for keys: %s" % (
                    str(tags)))

            # Create condition variable to wait on
            cond = threading.Condition(self.lock)

            # Event that signals whether a value was stored or not
            ev_store = threading.Event()

            # Add the cond var to each items wait list
            for path in tags:
                self.logger.debug("BLOCKING on %s" % (path))
                l = self.syncd.setdefault(path, [])
                #if not (cond in l):
                l.append((ev_store, cond))

            if eventlist == None:
                eventlist = []

            if timeout != None:
                deadline = start_time + timeout
                
            while not ev_store.isSet():
                # Check for interruption
                for evt in eventlist:
                    if evt.isSet():
                        raise EventError("Another event interrupted wait")

                wait_time = self.wait_interval

                # Check for timeout
                if (timeout != None):
                    time_left = deadline - time.time()
                    if time_left <= 0:
                        raise TimeoutError("Timed out waiting for keys: %s" % (
                            str(tags)))
                    else:
                        wait_time = min(wait_time, time_left)
                
                # wait for someone to release us for one of these tags
                cond.wait(timeout=wait_time)

            # Get the items again and see what we found
            res = self._getitems_list(tags)
            if len(res) > 0:
                self.logger.debug("RELEASED on %s" % (str(res.keys())))
                return res

            raise EventError("Awakened without finding a value!")

            
    def getitem_all(self, tags, timeout=None, eventlist=None):

        start_time = time.time()
        # Calculate deadline if timeout was specified
        if timeout != None:
            deadline = time.time() + timeout

        stags = set(tags)

        # initialize result dictionary
        res = {}

        while len(stags) > 0:
            if timeout != None:
                wait_time = deadline - time.time()
                if wait_time <= 0:
                    raise TimeoutError("Timed out waiting for keys %s" % str(stags))
            else:
                wait_time = None

            # Returns dict of values
            d = self.getitem_any(stags, timeout=wait_time,
                                 eventlist=eventlist)

            # Add partial results to result dict
            res.update(d)

            # Set of remaining tags to wait on
            stags = stags.difference(set(d.keys()))
            self.logger.debug("stags = %s" % (str(stags)))

        self.logger.debug("res = %s" % (str(res)))
        return res


    def do_update(self, path, value):

        with self.lock:
            res = super(Minimon, self).do_update(path, value)

            # release all waiters
            if isinstance(value, dict):
                for key in value.keys():
                    self.release('%s.%s' % (path, key), has_value=True)
            ## else:
            ##     # ??!
            ##     self.release(path, has_value=True)

            return res


class MonitorHandler(logging.Handler):

    def __init__(self, monitor, tagpfx,
                 channels=['logs'], level=logging.NOTSET,
                 buflimit=50000, interval=0.25):
        self.monitor = monitor
        self.tagpfx = tagpfx
        self.monchannels = channels

        # size of the current buffer
        self.bufsize = 0
        # size limit beyond which buffer is sent out as a datagram
        self.buflimit = buflimit
        # the buffer
        self.buffer = []
        
        # time of the last transmission
        self.lastsend = time.time()
        # time delta (sec) beyond which the buffer is sent regardless
        # of size
        self.interval = interval

        # Used to strip out bogus characters from log buffers
        self.deletechars = ''.join(set(string.maketrans('', '')) -
                                   set(string.printable))

        self.lock = threading.RLock()
        self.queue = Queue.Queue()

        logging.Handler.__init__(self, level=level)

    def set_monitor(self, monitor):
        self.monitor = monitor

    def _sendbuf(self):
        with self.lock:
            if len(self.buffer) == 0:
                return

            # Concatenate buffer and send it out over the socket
            buf = ('\n'.join(self.buffer)) + '\n'
            self.buffer = []
            self.bufsize = 0
            self.lastsend = time.time()

            # TODO: append tag suffix based on level and/or logging tag
            tag = self.tagpfx

            # Drop off with the monitor and off we go
            self.monitor.setvals(self.monchannels, tag, msgstr=buf,
                                 msgtime=self.lastsend)

    def emit(self, record):
        """Emit a log record to the monitor."""

        if not self.monitor:
            return self.handleError(record)

        # Format the log record
        msgstr = self.format(record)
        self.queue.put(msgstr)


    def process_queue(self, ev_quit):

        while not ev_quit.isSet():
            try:
                msgstr = self.queue.get(block=True, timeout=self.interval)
                # Strip out bogus characters
                msgstr = msgstr.translate(None, self.deletechars)
                msglen = len(msgstr) + 1

                # Would message size exceed buffer limit?
                if self.bufsize + msglen > self.buflimit:
                    # Yes, send current buffer
                    self._sendbuf()

                self.buffer.append(msgstr)
                self.bufsize += msglen

            except Queue.Empty:
                pass

            # if there is anything in the buffer, and it has reached
            # the minimum time interval since we last sent a packet, then
            # send the buffer
            if (self.bufsize > 0) and \
                    (time.time() - self.lastsend > self.interval):
                self._sendbuf()
        
        
    def handleError(self, record):
        """Called when there is an error emitting."""

        # Format the log record and write to stderr
        logstr = self.format(record)
        sys.stderr.write(logstr + '\n')
        

def config_monitor(monitor, channels, aggregates):
    """Configure the given monitor with the default base channels and
    aggregates."""
    # Add all the channels
    for name in channels.keys():
        monitor.add_channels(channels[name])

    # Create aggregations
    for name in aggregates.keys():
        monitor.aggregate(name, aggregates[name])

        
def addlogopts(optprs):
    """Add special options used in Monitor applications."""
    optprs.add_option("--monitor", dest="monitor",
                      help="Use NAME or HOST:PORT for publish/subscribe",
                      metavar="NAME")
    optprs.add_option("--monport", dest="monport", type="int",
                      help="Register my monitor using PORT", metavar="PORT")
    optprs.add_option("--monauth", dest="monauth", metavar="USER:PASS",
                      help="Authenticate to monitor using USER:PASS")


def main(options, args):

    # Create top level logger.
    logger = ssdlog.make_logger(options.svcname, options)

    # Initialize remote objects subsystem.
    try:
        ro.init()

    except ro.remoteObjectError, e:
        logger.error("Error initializing remote objects subsystem: %s" % str(e))
        sys.exit(1)

    ev_quit = threading.Event()
    usethread=False

    # Create our monitor and start it
    monitor = Monitor(options.svcname, logger, 
                      numthreads=options.numthreads)
    #config_monitor(monitor)

    logger.info("Starting monitor...")
    monitor.start()
    try:
        try:
            monitor.start_server(port=options.port, wait=True, 
                                 usethread=usethread)
        
        except KeyboardInterrupt:
            logger.error("Caught keyboard interrupt!")

    finally:
        logger.info("Stopping monitor...")
        if usethread:
            monitor.stop_server(wait=True)
        monitor.stop()
    
    
if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("--db", dest="dbpath", metavar="FILE",
                      help="Use FILE as the monitor database")
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--numthreads", dest="numthreads", type="int",
                      default=20,
                      help="Use NUM threads", metavar="NUM")
    optprs.add_option("--port", dest="port", type="int", default=None,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
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

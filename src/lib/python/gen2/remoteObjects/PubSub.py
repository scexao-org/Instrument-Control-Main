#!/usr/bin/env python
#
# PubSub.py -- Subaru Remote Objects Publish/Subscribe module
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Apr 19 14:51:03 HST 2013
#]
#

"""
Main issues to think about/resolve:
   
  [ ] Preserving ordering of updates (e.g. use a queue or sequence number)
       is it even necessary (or desirable)?
  [ ] Clumping updates together to improve network efficiency (i.e. caching)
  [ ] Bidirectional channel subscriptions
  [X] Local subscriber callbacks
  [X] Ability to set up ad-hoc channels based on aggregate channels;
        e.g. TaskManager needs to pull combined feed
  [ ] Permissions/access issues
"""

import sys, time
import threading, Queue
# API at Python v2.4
if sys.hexversion < 0x02040000:
    from sets import Set as set

import Bunch
import Task
import remoteObjects as ro
from ro_config import *
import ssdlog

version = '20110722.0'

# Subscriber options
TWO_WAY = 'bidirectional'
CH_ALL  = '*'


class PubSubError(Exception):
    """General class for exceptions raised by this module.
    """
    pass

class PubSubBase(object):
    """Base class for publish/subscribe entities.
    """

    ######## INTERNAL METHODS ########
    
    def __init__(self, name, logger,  
                 ev_quit=None, threadPool=None, numthreads=10):
        """
        Constructor for the PubSubBase class.
            name        pubsub name
            logger      logger to be used for any diagnostic messages
            threadPool  optional, threadPool for serving PubSub activities
            numthreads  if a threadPool is NOT furnished, the number of
                          threads to allocate
        """

        super(PubSubBase, self).__init__()

        self.logger = logger
        self.name = name
        self.numthreads = numthreads

        # Handles to subscriber remote proxies
        self._partner = Bunch.threadSafeBunch()
        # Defines aggregate channels
        self.aggregates = Bunch.threadSafeBunch()

        # Termination event
        if not ev_quit:
            ev_quit = threading.Event()
        self.ev_quit = ev_quit
        
        # If we were passed in a thread pool, then use it.  If not,
        # make one.  Record whether we made our own or not.
        if threadPool != None:
            self.threadPool = threadPool
            self.mythreadpool = False

        else:
            self.threadPool = Task.ThreadPool(logger=self.logger,
                                              ev_quit=self.ev_quit,
                                              numthreads=self.numthreads)
            self.mythreadpool = True
            
        # For task inheritance:
        self.tag = 'PubSub'
        self.shares = ['logger', 'threadPool']

        # For handling subscriber info 
        self._lock = threading.RLock()
        self._sub_info = {}

        # number of seconds to wait before unsubscribing a subscriber
        # who is unresponsive
        self.failure_limit = 60.0

    def get_threadPool(self):
        return self.threadPool

    
    def add_channel(self, channelName):
        self._lock.acquire()
        try:
            self._get_channelInfo(channelName, create=True)
                
        finally:
            self._lock.release()
                
    
    def add_channels(self, channelNames):
        self._lock.acquire()
        try:
            for channelName in channelNames:
                self._get_channelInfo(channelName, create=True)
                
        finally:
            self._lock.release()
                
    
    def get_channels(self):
        self._lock.acquire()
        try:
            return self._sub_info.keys()
                
        finally:
            self._lock.release()
                
    
    def loadConfig(self, moduleName):
        self._lock.acquire()
        try:
            try:
                self.logger.debug("Loading configuration from '%s'" % (
                        moduleName))
                cfg = my_import(moduleName)

            except ImportError, e:
                raise PubSubError("Can't load configuration '%s': %s" % (
                        moduleName, str(e)))

            if hasattr(cfg, 'setup'):
                cfg.setup(self)

        finally:
            self._lock.release()


    def loadConfigs(self, moduleList):
        for moduleName in moduleList:
            self.loadConfig(moduleName)


    def _get_channelInfo(self, channelName, create=True):
        # Should only get called from within a lock!

        if self._sub_info.has_key(channelName):
            return self._sub_info[channelName]

        elif create:
            # Need to create subscriber bunch for this channel.
            bunch = Bunch.Bunch(channel=channelName,
                                subscribers=set([]),
                                computed_channels=set([channelName]),
                                computed_subscribers=set([]))
            self._sub_info[channelName] = bunch
            return bunch

        else:
            raise PubSubError("No such channel exists: '%s'" % channelName)
                
    
    def _subscribe(self, subscriber, proxy_obj, channels, options):
        """Add a subscriber (named by _subscriber_ and accessible via
        object _proxy_obj_) to channel (or list of channels) _channels_
        and with options _options_.

        This is an internal method.  See class 'PubSub' and its method
        subscribe() for a public interface.
        """
        channels = set(channels)

        can_unsubscribe = True
        if isinstance(options, dict):
            # Does subscriber allow us to unsubscribe them if they are
            # unreachable?  Default=True
            if options.has_key('unsub'):
                can_unsubscribe = options['unsub']

        self._lock.acquire()
        try:
            # Record proxy in _partner table
            self._partner[subscriber] = Bunch.Bunch(proxy=proxy_obj,
                                                    time_failure=None,
                                                    can_unsubscribe=can_unsubscribe)

            for channel in channels:
                bunch = self._get_channelInfo(channel, create=True)
                bunch.subscribers.add(subscriber)
                
            # Compute subscriber relationships
            self.compute_subscribers()

        finally:
            self._lock.release()

        
    def _unsubscribe(self, subscriber, channels, options):
        """Delete a subscriber (named by _subscriber_) to channel (or list
        of channels) described by _channels_.

        This is an internal method.  See class 'PubSub' and its method
        unsubscribe() for a public interface.
        """
        channels = set(channels)

        self._lock.acquire()
        try:
            for channel in channels:

                bunch = self._get_channelInfo(channel)

                try:
                    bunch.subscribers.remove(subscriber)

                except KeyError:
                    #raise PubSubError("No subscriber '%s' to channel '%s'" % (
                    #    subscriber, channel))
                    # For now, silently ignore requests to unsubscribe from channels
                    # they are not a member of
                    pass

            # Compute subscriber relationships
            self.compute_subscribers()

        finally:
            self._lock.release()


    def remove_subscriber(self, subscriber):
        channels = self.get_channels()

        self._unsubscribe(subscriber, channels, [])

        # Delete proxy entry
        try:
            del self._partner[subscriber]
        except KeyError:
            pass


    def _named_update(self, value, names, channels):
        """
        Internal method to push a _value_.  _names_ are the
        names of the pubsubs doing the updating.  _channels_ is the
        channel(s) to which this update applies.
        """
        self.logger.debug("update: names=%s, channels=%s value=%s" % (
            str(names), str(channels), str(value)))

        # Start a task to do the remote update to subscribers.  Task will
        # call _subscriber_update(value, names, channels).  Meanwhile,
        # we are free to return immediately so as not delay the caller
        # any further.
        #self._subscriber_update(value, names, channels)
        t = Task.FuncTask2(self._subscriber_update, value, names, channels)
        t.init_and_start(self)


    def _subscriber_update(self, value, names, channels):
        """
        Internal method to update all subscribers who would be affected
        by these channels.  Triggered by a _named_update() call, which creates
        a task to call this method via the thread pool.  The update includes
        any local objects or remote objects by proxy.
        """
        self.logger.debug("subscriber update: names=%s, channels=%s value=%s" % (
            str(names), str(channels), str(value)))
        #self.logger.debug("value=%s" % (str(value)))

        # Get a list of partners that we should update for this value
        subscribers, all_channels = self._get_subscribers(channels)
        # sets don't go across remoteObjects (yet)
        all_channels = list(all_channels)

        self.logger.debug("subscribers for channel=%s are %s" % (
            str(channels), str(subscribers)))

        # Add ourself to the set of names (prevents cyclic updates)
        if self.name in names:
            updnames = names
        else:
            updnames = names[:]
            updnames.append(self.name)
        
        # Update them.  Silently log errors.
        for subscriber in subscribers:
            # Don't update any originators.
            if subscriber in names:
                continue

            try:
                # self._individual_update(subscriber, value, updnames,
                #                         all_channels)
                # Start a new task to concurrently do the individual update
                task = Task.FuncTask(self._individual_update,
                                     (subscriber, value, updnames,
                                         all_channels), {},
                                     logger=self.logger)
                task.init_and_start(self)

            except Exception, e:
                self.logger.error("cannot update subscriber '%s': %s" % (
                    subscriber, str(e)))


    def _individual_update(self, subscriber, value, names, channels):
        self.logger.debug("attempting to update subscriber '%s' on channels(%s)  with value: %s" % (
            subscriber, str(channels), str(value)))
        
        try:
            bnch = self._partner[subscriber]
            proxy_obj = bnch.proxy

            proxy_obj.remote_update(value, names, channels)

            bnch.time_failure = None

        except Exception, e:
            # TODO: capture and log traceback
            self.logger.error("cannot update subscriber '%s': %s" % (
                subscriber, str(e)))
            if not bnch.time_failure:
                bnch.time_failure = time.time()
            else:
                if (time.time() - bnch.time_failure) > self.failure_limit:
                    if bnch.can_unsubscribe:
                        self.remove_subscriber(subscriber)

    ######## PUBLIC METHODS ########
    
    def start(self, wait=True):
        """Start any background threads, etc. used by this pubsub.
        """

        #self.ev_quit.clear()
        
        # Start our thread pool (if we created it)
        if self.mythreadpool:
            self.threadPool.startall(wait=wait)

        self.logger.info("PubSub background tasks started.")


    def stop(self, wait=True):
        """Stop any background threads, etc. used by this pubsub.
        """

        # Stop our thread pool (if we created it)
        if self.mythreadpool:
            self.threadPool.stopall(wait=wait)
        
        self.logger.info("PubSub background tasks stopped.")

       
    def aggregate(self, channel, channels):
        """
        Establish a new aggregate channel (channel) based on a group of
        other channels (channels).  (channels) may contain aggregate or
        non-aggregate channels.
        """
        self._lock.acquire()
        try:
            self.aggregates[channel] = set(channels)

            # Update subscriber relationships
            self.compute_subscribers()

        finally:
            self._lock.release()
        

    def deaggregate(self, channel):
        """
        Delete an aggregate channel (channel). 
        """
        self._lock.acquire()
        try:
            self.aggregates.delitem(channel)

            # Update subscriber relationships
            self.compute_subscribers()

        finally:
            self._lock.release()
        

    def _get_constituents(self, channel, visited):
        """
        Internal helper function used by the 'get_constituents' method.
        """

        res = set([])

        self._lock.acquire()
        try:
            # Only process this if it is an aggregate channel and we haven't
            # visited it yet
            if (not self.aggregates.has_key(channel)) or (channel in visited):
                return res
            
            visited.add(channel)

            # For each subchannel in our aggregate set:
            #   - add it to the results
            #   - if IT is an aggregate, recurse and add its constituents
            for sub_ch in self.aggregates[channel]:

                res.add(sub_ch)
                if self.aggregates.has_key(sub_ch):
                    res.update(self._get_constituents(sub_ch, visited))

            return res

        finally:
            self._lock.release()


    def get_constituents(self, channel):
        """
        Returns the set of subaggregate and nonaggregate channels associated with the
        channel.
        """
        res = self._get_constituents(channel, set([]))

        return list(res)
    
        
    def compute_subscribers(self):
        """
        Internal helper function used by the subscribe(), unsubscribe(), 
        aggregate() and deaggregate(), methods.
        """

        self._lock.acquire()
        try:
            # PASS 1
            # For each channel, initialize its set of computed subscribers
            # to the explicitly subscribed set
            for channel in self.get_channels():
                bunch = self._get_channelInfo(channel)
                bunch.computed_subscribers = bunch.subscribers.copy()
                if self.name in bunch.computed_subscribers:
                    bunch.computed_subscribers.remove(self.name)

            # PASS 2 (aggregates only)
            # For each *aggregate* channel, get the constituents
            # and add any of the aggregate's subscribers to the non-aggregate
            # channels' computed_subscribers.
            for agg_channel in self.aggregates.keys():

                # Get my subscribers
                bunch = self._get_channelInfo(agg_channel)
                my_subscribers = bunch.subscribers
                #my_subscribers = bunch.computed_subscribers
                #self.logger.debug("subscribers(%s) = %s" % (agg_channel,
                #                                            list(my_subscribers)))

                # Get my constituents
                constituents = self.get_constituents(agg_channel)
                #self.logger.debug("constituents(%s) = %s" % (agg_channel,
                #                                             list(constituents)))

                for constituent in constituents:
                    # Add aggregate channel's subscribers to constituent's
                    bunch = self._get_channelInfo(constituent)
                    bunch.computed_subscribers.update(my_subscribers)
                    # Add aggregate channel name to consituent's
                    bunch.computed_channels.add(agg_channel)

                    # Remove self to avoid circular loops
                    if self.name in bunch.computed_subscribers:
                        bunch.computed_subscribers.remove(self.name)

            # PASS 3 (DEBUG ONLY)
            #for channel in self.get_channels():
            #    bunch = self._get_channelInfo(channel)
            #    self.logger.debug("%s --> %s" % (channel,
            #                                     str(list(bunch.computed_subscribers))))
        finally:
            self._lock.release()

        
    def _get_subscribers(self, channels):
        """Get the list of subscriber names that match subscriptions for
        a given channel or channels AND get the list of all channels that
        this aggregates to.
        """
        if isinstance(channels, basestring):
            channels = [channels]
        self.logger.debug("channels=%s" % str(channels))
        
        self._lock.acquire()
        try:
            # Optomization for case where there is only one channel
            if len(channels) == 1:
                channel = channels[0]
                try:
                    bunch = self._sub_info[channel]
                
                    return (bunch.computed_subscribers, bunch.computed_channels)
                
                except KeyError:
                    return (set([]), set([]))
            
            else:
                # Otherwise we have to compute the union of all the channels
                # computed subscribers
                subscribers = set([])
                all_channels = set([])

                for channel in channels:
                    try:
                        bunch = self._sub_info[channel]
                        subscribers.update(bunch.computed_subscribers)
                        all_channels.update(bunch.computed_channels)
                        
                    except KeyError:
                        continue

                # Remove self to avoid circular loops (shouldn't need to do this
                # because it should have already been done in compute_subscribers)
                if self.name in subscribers:
                    subscribers.remove(self.name)
                
                return (subscribers, all_channels)

        finally:
            self._lock.release()


    def get_subscribers(self, channels):
        """
        remoteObjects callable version of _get_subscribers (currently sets are not
        supported on XML-RPC, so we cannot guarantee that apps written in other
        languages will be able to access it).
        """
        subscribers, all_channels = self._get_subscribers(channels)

        return (list(subscribers), list(all_channels))

        

    def remote_update(self, value, names, channels):
        """method called by another PubSub to update this one
        with new and changed items.
        """
        # Avoid cyclic dependencies--don't update ourselves if we
        # originated this event
        if self.name in names:
            return ro.OK

        return self._named_update(value, names, channels)


    def notify(self, value, channels):
        """
        Method called by local users of this PubSub to update it
        with new and changed items.
            value
            channels    one (a string) or more (a list) of channel names to
                        which to send the specified update
        """
        return self._named_update(value, [self.name], channels)


class PubSub(PubSubBase):
    """Like a PubSubBase, but adds support for creating and caching
    remote object handles based on service names (i.e. abstract out
    remoteObjects proxy creation).
    """

    def __init__(self, name, logger,
                 ev_quit=None, threadPool=None, numthreads=10):
        """Constructor.
        """

        super(PubSub, self).__init__(name, logger,
                                      ev_quit=ev_quit,

                                      threadPool=threadPool,
                                      numthreads=numthreads)
        
        # Holds proxies to other pubsubs
        self._proxyCache = {}

        # Holds information about remote subscriptions
        #self._remote_sub_info = set([])
        self._remote_sub_info = {}

        # Timeout for remote updates
        self.remote_timeout = 10.0

        # Interval between remote subscription updates
        self.update_interval = 10.0


    def removeAllProxies(self):
        self._proxyCache = {}
        
    def removeProxies(self, nameList):
        """Remove remoteObject proxies to remote pubsubs (subscribers).
        """
        for name in nameList:
            try:
                del self._proxyCache[name]
            except KeyError:
                # already deleted?  in any case, it's ok
                pass

    def _getProxy(self, subscriber, options):
        """Internal method to create & cache remoteObject proxies to remote
        pubsubs (subscribers).
        """
        try:
            # If we already have a proxy for the _svcname_, return it.
            return self._proxyCache[subscriber]

        except KeyError:
            # Create a new proxy to the external pubsub and cache it

            # Fill in possible authentication and security params
            kwdargs = { 'timeout': self.remote_timeout }
            #kwdargs = {}
            if options.has_key('auth'):
                kwdargs['auth'] = options['auth']
            if options.has_key('secure'):
                kwdargs['secure'] = options['secure']

            # subscriber can be a service name or a host:port
            if not (':' in subscriber):
                proxy_obj = ro.remoteObjectProxy(subscriber, **kwdargs)
            else:
                (host, port) = subscriber.split(':')
                port = int(port)
                proxy_obj = ro.remoteObjectClient(host, port, **kwdargs)
                
            self._proxyCache[subscriber] = proxy_obj
            self.logger.debug("Created proxy for '%s'" % (subscriber))

            return proxy_obj
            
        
    def subscribe(self, subscriber, channels, options):
        """Register a subscriber (named by _subscriber_) for updates on
        channel(s) _channels_. 

        This call is expected to be called via remoteObjects.
        """
        self.logger.debug("registering '%s' as a subscriber for '%s'." % (
            subscriber, channels))

        if not options:
            options = {}
            
        if isinstance(channels, basestring):
            channels = [channels]
            
        try:
            proxy_obj = self._getProxy(subscriber, options)
            
            super(PubSub, self)._subscribe(subscriber, proxy_obj,
                                            channels, options)
            self.logger.debug("local registration of '%s' successful." % (
                subscriber))

            return ro.OK

        except PubSubError, e:
            self.logger.error("registration of '%s' for '%s' failed: %s" % (
                subscriber, channels, str(e)))
            return ro.ERROR


    def unsubscribe(self, subscriber, channels, options):
        """Unregister a subscriber (named by _subscriber_) for updates on
        channel(s) _channels_. 

        This call is expected to be called via remoteObjects.
        """
        self.logger.debug("unregistering '%s' as a subscriber for '%s'." % (
            subscriber, channels))

        if not options:
            options = {}
            
        if isinstance(channels, basestring):
            channels = [channels]
            
        try:
            #proxy_obj = self._getProxy(subscriber, options)
            
            super(PubSub, self)._unsubscribe(subscriber, channels, options)
            self.logger.debug("local unregistration of '%s' successful." % (
                subscriber))

            return ro.OK

        except PubSubError, e:
            self.logger.error("unregistration of '%s' for '%s' failed: %s" % \
                             (subscriber, str(channels), str(e)))
            return ro.ERROR


    def publish_to(self, subscriber, channels, options):
        """Register a subscriber (named by _subscriber_) for updates on
        channel(s) _channels_.

        This method is just a shortcut for subscribing someone with an
        option never to remove them.
        """
        options1 = options.copy()
        options1.setdefault('unsub', False)
            
        return self.subscribe(subscriber, channels, options1)


    def _subscribe_remote(self, publisher, channels, options):
        self.logger.debug("Subscribing ourselves to publisher %s channels=%s options=%s" % (
            publisher, str(channels), str(options)))
        try:
            # Fill in possible authentication and security params
            kwdargs = {}
            if options.has_key('pubauth'):
                kwdargs['auth'] = options['pubauth']
            if options.has_key('pubsecure'):
                kwdargs['secure'] = options['pubsecure']
            if options.has_key('name'):
                name = options['name']
            else:
                name = self.name

            pub_proxy = self._getProxy(publisher, kwdargs)
            
            self.logger.debug("Subscribing %s to %s options=%s" % (
                    name, str(channels), str(options)))
            pub_proxy.subscribe(name, channels, options)
            
        except Exception, e:
            self.logger.error("registration via '%s' for '%s' failed: %s" % \
                             (publisher, str(channels), str(e)))

        
    def _unsubscribe_remote(self, publisher, channels, options):
        try:
            # Fill in possible authentication and security params
            kwdargs = {}
            if options.has_key('pubauth'):
                kwdargs['auth'] = options['pubauth']
            if options.has_key('pubsecure'):
                kwdargs['secure'] = options['pubsecure']
            if options.has_key('name'):
                name = options['name']
            else:
                name = self.name

            pub_proxy = self._getProxy(publisher, kwdargs)
            
            self.logger.debug("Unsubscribing %s to %s options=%s" % (
                    name, str(channels), str(options)))
            pub_proxy.unsubscribe(name, channels, options)
            
        except Exception, e:
            self.logger.error("unregistration via '%s' for '%s' failed: %s" % \
                             (publisher, str(channels), str(e)))

        
    def subscribe_remote(self, publisher, channels, options):

        # Necessary to add to a set; list objects are not hashable
        if type(channels) == str:
            channels = (channels,)
        elif type(channels) == list:
            channels = tuple(channels)
        assert(type(channels) == tuple)

        if not options:
            options = {}
            
        self._lock.acquire()
        try:
            #self._remote_sub_info.add((publisher, channels, options))
            self._remote_sub_info[(publisher, channels)] = (publisher,
                                                            channels, options)

            self._subscribe_remote(publisher, channels, options)
            
        finally:
            self._lock.release()
                
    
    def unsubscribe_remote(self, publisher, channels, options):

        # Necessary to add to a set; list objects are not hashable
        if type(channels) == str:
            channels = (channels)
        elif type(channels) == list:
            channels = tuple(channels)
        assert(type(channels) == tuple)

        self._lock.acquire()
        try:
            #self._remote_sub_info.remove((publisher, channels, options))
            del self._remote_sub_info[(publisher, channels)]

            self._unsubscribe_remote(publisher, channels, options)
        finally:
            self._lock.release()
                

    def subscribe_local(self, local_obj, channels):
        """Register a subscriber (represented by _local_obj_)
        for updates on channel(s) _channels_.

        This call is expected to be a local call.
        """
        # TODO: is this string guaranteed to be unique among objects?
        subscriber = str(local_obj)
        
        self.logger.debug("registering '%s' as a subscriber for '%s'." % (
            subscriber, channels))

        if (not hasattr(local_obj, 'remote_update')) or \
               (not hasattr(local_obj, 'remote_delete')):
            raise PubSubError('object needs both remote_update and remote_delete methods')

        super(PubSub, self)._subscribe(subscriber, local_obj,
                                        channels, {})
        self.logger.debug("local registration of '%s' successful." % (
            subscriber))


    def unsubscribe_local(self, local_obj, channels):
        """Unregister a subscriber (named by _subscriber_) for updates on
        channel(s) _channels_.

        This call is expected to be a local call.
        """
        subscriber = str(local_obj)
        
        self.logger.debug("unregistering '%s' as a subscriber for '%s'." % (
            subscriber, channels))

        super(PubSub, self)._unsubscribe(subscriber, channels, {})
        self.logger.debug("local unregistration of '%s' successful." % (
            subscriber))


    def subscribe_cb(self, fn_update, channels):
        """Register local subscriber callback (_fn_update_)
        for updates on channel(s) _channels_.

        This call is expected to be a local call.
        """
        if not callable(fn_update):
            raise PubSubError('subscriber functions must be callables')

        # TODO: should come up with unique name
        subscriber = fn_update.__name__
        self.logger.debug("registering '%s' as a subscriber for '%s'." % (
            subscriber, channels))

        class anonClass(object):
            def __init__(self, update):
                self.update = update
                
            def remote_update(self, value, name, channels):
                # Could wrap this or modify interface if necessary
                self.update(value, name, channels)

        local_obj = anonClass(fn_update)

        super(PubSub, self)._subscribe(subscriber, local_obj,
                                        channels, {})
        self.logger.debug("local registration of '%s' successful." % (
            subscriber))


    def unsubscribe_cb(self, fn_update, channels):
        """Unregister a subscriber (_fn_update_) for updates on
        channel(s) _channels_.

        This call is expected to be a local call.
        """
        subscriber = fn_update.__name__
        self.logger.debug("unregistering '%s' as a subscriber for '%s'." % (
            subscriber, channels))

        super(PubSub, self)._unsubscribe(subscriber, channels, {})
        self.logger.debug("local unregistration of '%s' successful." % (
            subscriber))


    # TODO: deprecate this and make apps create their own remoteObjectServer
    # with a delegate to this object??
    def start_server(self, svcname=None, host=None, port=None,
                     ping_interval=default_ns_ping_interval,
                     strict_registration=False,
                     threaded_server=default_threaded_server,
                     authDict=None, default_auth=use_default_auth,
                     secure=default_secure, cert_file=default_cert,
                     ns=None, 
                     usethread=True, wait=True, timeout=None):

        if not svcname:
            svcname = self.name
        # make our RO server for remote interface
        self.server = ro.remoteObjectServer(svcname=svcname, obj=self,
                                            logger=self.logger,
                                            ev_quit=self.ev_quit,
                                            port=port, usethread=usethread,
                                            threadPool=self.threadPool,
                                            threaded_server=threaded_server,
                                            authDict=authDict, default_auth=default_auth,
                                            secure=secure, cert_file=cert_file)

        self.logger.info("Starting remote subscriptions update loop...")
        t = Task.FuncTask(self.update_remote_subscriptions_loop, [], {})
        t.init_and_start(self)

        self.logger.info("Starting server...")
        if not usethread:
            self.server.ro_start(wait=wait, timeout=timeout)

        else:
            # Use one of our threadPool to run the server
            t = Task.FuncTask(self.server.ro_start, [], {})
            t.init_and_start(self)
            if wait:
                self.server.ro_wait_start(timeout=timeout)
            
    def stop_server(self, wait=True, timeout=None):
        self.logger.info("Stopping server...")
        #self.server.ro_stop(wait=wait, timeout=timeout)
        # This is not quite working correctly...
        self.server.ro_stop(wait=False, timeout=timeout)


    def update_remote_subscriptions_loop(self):

        while not self.ev_quit.isSet():
            time_end = time.time() + self.update_interval

            self._lock.acquire()
            try:
                #tups = list(self._remote_sub_info)
                tups = self._remote_sub_info.values()
            finally:
                self._lock.release()
                
            self.logger.debug("updating remote subscriptions: %s" % (
                str(tups)))
            for tup in tups:
                try:
                    (publisher, channels, options) = tup
                    
                    self._subscribe_remote(publisher, channels, options)

                except Exception, e:
                    self.logger.error("Error pinging remote subscription %s: %s" % (
                            str(tup), str(e)))

            # Sleep for remainder of desired interval.  We sleep in
            # small increments so we can be responsive to changes to
            # ev_quit
            cur_time = time.time()
            self.logger.debug("Waiting interval, remaining: %f sec" % \
                              (time_end - cur_time))

            while (cur_time < time_end) and (not self.ev_quit.isSet()):
                time.sleep(0)
                self.ev_quit.wait(min(0.1, time_end - cur_time))
                cur_time = time.time()

            self.logger.debug("End interval wait")


##     def ro_echo(self, arg):
##         """(Required by remoteObjects interface for 'pinging'.)
##         """
##         return arg


class ExampleSubscriber(object):

    def __init__(self, queue):
        self.queue = queue

    def get(self, block=True, timeout=None):
        return self.queue.get(block=block, timeout=timeout)

    def remote_update(self, value, names, channels):
        """This will be called by the PubSub class when a value is available.
        """
        self.queue.put(value)

    
def my_import(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


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
    
    # Create our pubsub and start it
    pubsub = PubSub(options.svcname, logger,
                    numthreads=options.numthreads)

    # Load configurations, if any specified
    if options.config:
        pubsub.loadConfigs(options.config.split(','))

    logger.info("Starting pubsub...")
    pubsub.start()
    try:
        try:
            pubsub.start_server(port=options.port, wait=True, 
                                 usethread=usethread)
        
        except KeyboardInterrupt:
            logger.error("Caught keyboard interrupt!")

    finally:
        logger.info("Stopping pubsub...")
        if usethread:
            pubsub.stop_server(wait=True)
        pubsub.stop()
    
    
if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("--config", dest="config", 
                      metavar="FILE",
                      help="Use configuration FILE for setup")
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--numthreads", dest="numthreads", type="int",
                      default=100,
                      help="Use NUM threads", metavar="NUM")
    optprs.add_option("--port", dest="port", type="int", default=None,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--svcname", dest="svcname", metavar="NAME",
                      default='pubsub',
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

#!/usr/bin/env python
#
# SessionManager.py -- implements a basic session manager.
#
# Eric Jeschke (eric@naoj.org)
#

import sys, time
import threading
import random
# for command line interface:
import os
#optparse imported below (if needed)
import hashlib, hmac

import remoteObjects as ro
import remoteObjects.Monitor as Monitor
import logging, ssdlog
from cfg.INS import INSdata as INSconfig
import hashlib, hmac
import Gen2.db.obsnote as obsnote
import Task
import tools.pc as pc
import mountsshfs

# Version/release number
version = "20100925.0"

# Chose type of authorization encryption 
digest_algorithm = hashlib.sha1

# Service name prefix for directory of remote objects
serviceName = 'sessions'

# monitor channels we should broadcast on
monchannels = ['sessions']

# Session name used for primary observation
primarySessionName = 'main'

# Items always allocated to primary observation
primarySessionAllocs = ['TSC', 'status', 'sessions',
                        'frames', 'bootmgr', 'taskmgr0',
                        'monitor', 'taskmgr',
                        'VGW', 'OBS', 'OBC', 
                        'ANA', #'STARS',
                        'integgui0',
                        'guideview', 'fitsview',
                        ]

mountarea = mountsshfs.mountarea
mounthost = mountsshfs.mounthost


class sessionError(Exception):
    pass

class sessionInvalidNameError(sessionError):
    pass

class sessionInvalidKeyError(sessionError):
    pass

class sessionAllocError(sessionError):
    pass


class SessionManager(object):
    """Manages the session.
    """

    def __init__(self, name, logger, monitor, threadPool,
                 automount_propdir=False):
        self.name = name
        self.logger = logger
        self.mon = monitor
        # For looking up instrument info
        self.insconfig = INSconfig()

        # For critical sections in this object
        self.lock = threading.RLock()

        # Should we automount proposal id directories
        self.automount_propdir = automount_propdir

        # For background tasks
        self.threadPool = threadPool
        self.shares = ['logger', 'threadPool']
        self.tag = 'SessionManager'

        super(SessionManager, self).__init__()
        
        
    def start(self):

        # prefixes will be mon.session and mon.alloc
        self.tagpfx = ('mon')
        self.channels = monchannels

        # For updating status system with session info
        # TODO: parameterize object
        self.status = ro.remoteObjectProxy('status')

        # For starting interfaces
        # TODO: parameterize object
        self.bootmgr = ro.remoteObjectProxy('bootmgr')

        # Try to restore previous session.  If it fails, then create
        # a new session.
        try:
            self.mon.restore()

        except IOError, e:
            self.initialize()

        # Set necessary status
        self.set_needed_status()


    def stop(self, wait=True):
        pass

        
    def initialize(self):
        # Allocation items without any limit
        # TODO: set all items at once
        self.mon.setvals(self.channels, '%s.alloc.status' % self.tagpfx,
                         limited=False, count=0, allocList=[])
        self.mon.setvals(self.channels, '%s.alloc.frames' % self.tagpfx,
                         limited=False, count=0, allocList=[])
        self.mon.setvals(self.channels, '%s.alloc.sessions' % self.tagpfx,
                         limited=False, count=0, allocList=[])
        self.mon.setvals(self.channels, '%s.alloc.bootmgr' % self.tagpfx,
                         limited=False, count=0, allocList=[])
        self.mon.setvals(self.channels, '%s.alloc.fitsview' % self.tagpfx,
                         limited=False, count=0, allocList=[])
        self.mon.setvals(self.channels, '%s.alloc.guideview' % self.tagpfx,
                         limited=False, count=0, allocList=[])
        self.mon.setvals(self.channels, '%s.alloc.OBC' % self.tagpfx,
                         limited=False, count=0, allocList=[])
        self.mon.setvals(self.channels, '%s.alloc.OBS' % self.tagpfx,
                         limited=False, count=0, allocList=[])
        self.mon.setvals(self.channels, '%s.alloc.STARS' % self.tagpfx,
                         limited=False, count=0, allocList=[])
        self.mon.setvals(self.channels, '%s.alloc.taskmgr' % self.tagpfx,
                         limited=False, count=0, allocList=[])
        self.mon.setvals(self.channels, '%s.alloc.monitor' % self.tagpfx,
                         limited=False, count=0, allocList=[])

        # Should this be count limited?
        for i in xrange(3):
            self.mon.setvals(self.channels, '%s.alloc.taskmgr%d' % (
                self.tagpfx, i), limited=False, count=0, allocList=[])
            self.mon.setvals(self.channels, '%s.alloc.integgui%d' % (
                self.tagpfx, i), limited=False, count=0, allocList=[])

        # Count-limited allocations
        for name in ['TSC', 'ANA', 'guiderint']:
            self.mon.setvals(self.channels, '%s.alloc.%s' % (
                    self.tagpfx, name), limited=True,
                             allocLimit=1, count=1, allocList=[])
        # Instruments (includes VGW)
        for insname in self.insconfig.getNames():
            self.mon.setvals(self.channels, '%s.alloc.%s' % (
                    self.tagpfx, insname), limited=True,
                             allocLimit=1, count=1, allocList=[])

        # Create a primary session, which always has allocated the
        # telescope
        sessionName = primarySessionName
        sessionKey = self.genkey()
        self.createSession(sessionName, {'key': sessionKey})

        # Set up a temporary data sink key
        dataKey = self.genkey2('tmp')
        self.add_datakey(sessionName, sessionKey, dataKey, {})
        
        # Always allocate the following items to the main session
        #self.allocate(primarySessionAllocs, sessionName, sessionKey)

        self.save()


    def save(self):
        self.mon.save()


    def genkey(self):
        """Generate a random key for a session.  Idea is not hard
        security, but to prevent accidental use.
        """
        choices = 'abcdefghijklmnopqrstuvwxyz'
        choices += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        choices += '0123456789$&#@!*+'

        key = ''
        for i in xrange(4):
            if key != '':
                key += '-'
            for j in xrange(4):
                key += random.choice(choices)

        return key

    def genkey2(self, prefix='', m=6, n=4):
        """Generate a random key for a session or data.
        """
        choices = 'abcdefghijklmnopqrstuvwxyz'
        choices += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        choices += '0123456789$&#@!*+'

        key = prefix
        if key != '':
            key += '-'
        key += time.strftime("%Y%m%d-%H%M%S", time.localtime())
        for i in xrange(m):
            key += '-'
            for j in xrange(n):
                key += random.choice(choices)

        return key

    # ----- SESSION MANIPULATION -----
        
    def getSessionInfo(self, sessionName):
        """Gets information about the session _sessionName_.  Returns
        a dictionary of information about the session if the session
        exists, and raises a sessionInvalidNameError otherwise.
        """

        sessionName = sessionName.lower().strip()
        
        # Check for existing session with this name.
        tag = ('%s.session' % self.tagpfx)
        (okflag, res) = self.mon.get_nowait(tag, sessionName)
        if not okflag:
            raise sessionInvalidNameError("No existing session named '%s'" % \
                                              sessionName)

        # Return all items with this path prefix
        tag = ('%s.session.%s' % (self.tagpfx, sessionName))
        vals = self.mon.getitems_suffixOnly(tag)
        return vals


    def authenticate(self, sessionName, sessionKey):
        """Authenticates _sessionName_ via _sessionKey_.  Raises a
        sessionInvalidKeyError if authentication fails, otherwise returns
        normally.
        """

        self.logger.info("Authenticating session='%s' with key='%s'" % \
                         (sessionName, sessionKey))

        info = self.getSessionInfo(sessionName)

        # Check keys match
        if (not info.has_key('key')) or (info['key'] != sessionKey):
            raise sessionInvalidKeyError("Invalid key for session '%s'" % \
                                         sessionName)

        return ro.OK
        

    def _makeNote(self, note, tags=None):
        """Create an ObsNote in the database.
        """
        self.logger.info("making session note: %s" % str(note))
        try:
            if tags:
                obsnote.createNote(memo=note, meta='session:%s' % ','.join(tags))
            else:
                obsnote.createNote(memo=note)

        except Exception, e:
            self.logger.error("Failed to update obsnote database: %s" % str(e))
            

    def makeNoteSessionChange(self, sessionName):
        
        sp = self.getSessionInfo(sessionName)
        sa = self.getSessionAllocations(sessionName)

        memo = ( "Session updated." + 
                 " Prop_Id: %s;" % (sp.get('propid', 'N/A')) +
                 " Instrument: %s;" % (sp.get('mainInst', 'N/A')) +
                 " Observers: %s;" % (sp.get('observers', 'N/A')) +
                 " Support Scientist: %s;" % (sp.get('ss', 'N/A')) +
                 " Operators: %s;" % (sp.get('operator', 'N/A'))
                 )

        self._makeNote(memo, tags=['update'])
        
        
    def createSession(self, sessionName, sessionParams):
        """Creates session _sessionName_ with new information.
        _sessionParams_ is a dictionary of arbitrary keys/values to store
        in the session.  Raises a sessionInvalidKeyError if there is
        an existing session with this name, or _sessionParams_ does not
        contain a valid key for this session.
        """

        try:
            info = self.getSessionInfo(sessionName)

            raise sessionInvalidKeyError("There is an existing session '%s'" % \
                                         sessionName)
        except sessionInvalidNameError, e:
            pass

        if not sessionParams.has_key('key'):
            sessionParams['key'] = self.genkey()
            
        sessionName = sessionName.lower().strip()
        tag = ('%s.session.%s' % (self.tagpfx, sessionName))

        sessionParams['name'] = sessionName
        sessionParams['allocs'] = []
        # for SOSS compatibility mode
        sessionParams['mainInst'] = '#'
        # Add timestamps for session creation and update
        sessionParams['time_start'] = time.time()
        sessionParams['time_update'] = sessionParams['time_start']

        self.logger.info("Creating session='%s' with params='%s'" % \
                         (sessionName, str(sessionParams)))
        self.mon.update(tag, sessionParams, self.channels)

        # Make changes persistent
        self.save()

        memo = "session='%s' created" % (sessionName)
        self._makeNote(memo, tags=['create'])
        self.logger.info(memo)

        return ro.OK
        

    def updateSession(self, sessionName, sessionParams):
        """Update session _sessionName_ with new/more information.
        The session must already have been created.
        _sessionParams_ is a dictionary of arbitrary keys/values to store
        in the session.  Raises a sessionInvalidKeyError if
        _sessionParams_ does not contain a valid matching key for this
        session.
        """

        if not sessionParams.has_key('key'):
            raise sessionInvalidKeyError("Invalid key for session '%s'" % \
                                         sessionName)

        self.authenticate(sessionName, sessionParams['key'])
        
        sessionName = sessionName.lower().strip()
        tag = ('%s.session.%s' % (self.tagpfx, sessionName))

        # Set session update timestamp
        sessionParams['time_update'] = time.time()
        # TODO: Remove key 'time_start'

        # Check for propid change
        info = self.getSessionInfo(sessionName)
        new_propid = sessionParams.get('propid')
        old_propid = info.get('propid', None)

        self.logger.info("Updating session='%s' with params='%s'" % \
                         (sessionName, str(sessionParams)))
        self.mon.update(tag, sessionParams, self.channels)

        # Record an ObsNote about this change
        self.makeNoteSessionChange(sessionName)
        
        # ==SOSS COMPATABILITY MODE==
        # Set status values needed by various SOSS components
        self.set_needed_status()
        
        # Make changes persistent
        self.save()
        self.logger.info("session='%s' updated" % \
                         (sessionName))

        if old_propid != new_propid:
            self.proposal_change(sessionName, sessionParams['key'],
                                 old_propid, new_propid)

        return ro.OK
        

    # TEMP: used by IntegGUI to change session info
    def changeProp(self, sessionName, params):
        """TEMPORARY INTERFACE.
        """

        # _params_ should contain following keys:
        # PROPID, OBSERVERS, SS and OPERATOR
        self.logger.info("session: '%s' params: %s" % (sessionName,
                                                       str(params)))
        sessionParams = self.getSessionInfo(sessionName)
        sessionParams.update(params)

        return self.updateSession(sessionName, sessionParams)


    def proposal_change(self, sessionName, sessionKey,
                        old_propid, new_propid):
        """Called if there has been a change of proposal ID."""

        # Unload any data key for the old propid 
        try:
            self.revoke_datakey(sessionName, sessionKey, old_propid)

        except Exception, e:
            self.logger.warn("Error unloading old propid key '%s': %s" % (
                old_propid, str(e)))

        try:
            self.revoke_datakey(sessionName, sessionKey, 'obssum')

        except Exception, e:
            self.logger.warn("Error unloading key 'obssum': %s" % (
                str(e)))

        try:
            self.revoke_datakey(sessionName, sessionKey, 'obsrem')

        except Exception, e:
            self.logger.warn("Error unloading key 'obssum': %s" % (
                str(e)))

        # Auto-generate a new data key for the new propid 
        try:
            self.gen_datakey(sessionName, sessionKey, new_propid)

            # TODO: properties should be defined according to location and
            # circumstances!
            properties = {
                'priority': '5', 'realm': 'SUMMIT', 'enable': 'YES',
                'type': 'PUSH', 'passphrase': '',
                }
            self.load_datakey(sessionName, sessionKey, new_propid,
                              properties)

        except Exception, e:
            self.logger.error("Error loading new propid key '%s': %s" % (
                new_propid, str(e)))

        passwd = pc.pc(new_propid)
        try:
            # TODO: properties should be defined according to location and
            # circumstances!
            properties = {
                'priority': '5', 'realm': 'SUMMIT', 'enable': 'YES',
                'type': 'PUSH', 'passphrase': passwd,
                }
            self.load_datakey(sessionName, sessionKey, 'obssum',
                              properties)

        except Exception, e:
            self.logger.error("Error loading key 'obssum': %s" % (
                str(e)))

        try:
            # TODO: properties should be defined according to location and
            # circumstances!
            properties = {
                'priority': '5', 'realm': 'BASE', 'enable': 'YES',
                'type': 'PUSH', 'passphrase': passwd,
                }
            self.load_datakey(sessionName, sessionKey, 'obsrem',
                              properties)

        except Exception, e:
            self.logger.error("Error loading key 'obsrem': %s" % (
                str(e)))

        if self.automount_propdir:
            # If we have a procedure change, fire up a task to do the
            # mounting and unmounting of the ANA directory in the background
            t = Task.FuncTask2(self.mount_change, old_propid, new_propid)
            t.init_and_start(self)

            
    def mount_change(self, old_propid, new_propid,
                     host=mounthost, username=None, password=None,
                     remotedir=''):

        # GLOBALS READ: mountarea, mounthost
        
        # Unmount old area if it was mounted
        if old_propid:
            unmountpt = os.path.join(mountsshfs.mountarea, old_propid)
            # Try to unmount the directory
            self.logger.info("Attempting to lazily unmount %s" % unmountpt)
            try:
                mountsshfs.unmount_remote(self.logger, unmountpt)
            except Exception, e:
                self.logger.error("Error unmounting directory '%s': %s" % (
                    unmountpt, str(e)))

        # Try to mount the new area, if one was specified
        if new_propid:
            mountpt = os.path.join(mountsshfs.mountarea, new_propid)

            self.logger.info("Attempting to mount %s" % mountpt)
            if not os.path.isdir(mountpt):
                try:
                    os.mkdir(mountpt)
                except OSError, e:
                    self.logger.error("Error creating mount point '%s': %s" % (
                        mountpt, str(e)))
        
            try:
                # Get info necessary to establish new mountpoint
                if not username:
                    username, password = mountsshfs.getuserpass(new_propid)

                if not password:
                    # If no password specified then try to get one from OPAL
                    password = mountsshfs.getpass(username)

                mountsshfs.mount_remote(self.logger, mounthost,
                                        username, password,
                                        mountpt, remotedir)

            except Exception, e:
                self.logger.error("Error mounting directory '%s': %s" % (
                    mountpt, str(e)))
            

    def instrument_change(self, sessionName, sessionKey, allocList):

        datakeys = self.get_datakeys()
        ins_loaded = map(lambda x: x.split('-')[0].upper(), datakeys)
        self.logger.debug("Instrument keys loaded for %s" % (str(ins_loaded)))

        for insname in self.insconfig.getNames():
            inskey = insname.lower()
            
            # Unload unused instrument keys
            if (insname in ins_loaded) and (not insname in allocList):
                try:
                    self.revoke_datakey(sessionName, sessionKey, inskey)
                except Exception, e:
                    self.logger.error("Error revoking instr key '%s': %s" % (
                        insname, str(e)))
                    pass

            # And load used instrument keys
            if (insname in allocList):
                try:
                    # TODO: properties should be defined according to
                    # config file or session settings
                    properties = {
                        'priority': '5', 'realm': 'BASE', 'enable': 'YES',
                        'type': 'PULL', 'passphrase': '',
                        }
                    self.load_datakey(sessionName, sessionKey, inskey,
                                      properties)
                    
                except Exception, e:
                    self.logger.error("Error loading new instr key '%s': %s" % (
                        insname, str(e)))
                    

    def set_needed_status(self):
        """Sets needed status variables used by legacy SOSS systems.
        """

        statusDict = {}
        statusDict['FITS.SBR.MAINOBCP'] = '#'
        statusDict['FITS.SBR.ALLOBCP'] = '#'

        # Initialize all instrument variables to defaults
        for insname in self.insconfig.getNames():

            inscode = self.insconfig.getCodeByName(insname)

            # Preinitialize to nulls
            for alias in ['FITS.%s.PROP-ID' % inscode,
                          'FITS.%s.PROP_ID' % inscode,
                          'FITS.%s.OBSERVER'% inscode,
                          'FITS.%s.OBS-ALOC' % inscode,
                          'FITS.%s.OBS_ALOC' % inscode,
                          ]:
                #statusDict[alias] = ''
                statusDict[alias] = '#'

        # Iterate over sessions, setting appropriate values
        for sessionName in self.getSessionNames():
            sp = self.getSessionInfo(sessionName)

            # determine which instruments are allocated and set
            # the appropriate variables.
            allocs = self.getSessionAllocations(sessionName)

            # Insure that none of the values is an empty string
            propid = sp.get('propid', '#').strip()
            if len(propid) == 0:
                propid = '#'
            observers = quote_spaces(sp.get('observers', '#')).strip()
            if len(observers) == 0:
                observers = '#'
            mainInst = sp.get('mainInst', '#')
            if len(mainInst) == 0:
                mainInst = '#'

            allobcps = []
            for insname in self.insconfig.getNames():

                inscode = self.insconfig.getCodeByName(insname)
                iface = self.insconfig.getInterfaceByName(insname)

                # Now add back in allocated instruments
                if insname in allocs:

                    allobcps.append(insname)

                    # Only set FITS.SBR.MAINOBCP if the instrument is
                    # actually allocated to our (primary) session
                    if (sessionName == primarySessionName) and \
                           (insname == mainInst):
                        statusDict['FITS.SBR.MAINOBCP'] = insname

                    statusDict['FITS.%s.PROP-ID' % inscode] = propid
                    statusDict['FITS.%s.PROP_ID' % inscode] = propid
                    statusDict['FITS.%s.OBSERVER' % inscode] = observers
                    statusDict['FITS.%s.OBS-ALOC' % inscode] = 'Observation'
                    statusDict['FITS.%s.OBS_ALOC' % inscode] = 'Observation'

                    # If instr interface is DAQtk then start interface,
                    # if not already started.  Otherwise we talk directly
                    # to the instrument.
                    try:
                        if iface[0].lower() == 'daqtk':
                            self.logger.debug("Starting DAQtk interface '%s'" % (
                                insname))
                            self.bootmgr.start(insname)

                    except Exception, e:
                        self.logger.warn("Error starting interface '%s': %s" % (
                                insname, str(e)))

        statusDict['FITS.SBR.ALLOBCP'] = ':'.join(allobcps)

        self.logger.debug("Updating status: %s" % str(statusDict))
        try:
            self.status.store(statusDict)

        except ro.remoteObjectError, e:
            self.logger.error("Error updating status: %s" % str(e))
        

    def getSessionNames(self):
        """Returns the list of valid, existing session names.
        """
        # TODO: make more efficient
        tag = ('%s.session' % self.tagpfx)
        vals = self.mon[tag]
        self.logger.info("vals=%s" % str(vals))

        return vals.keys()

    
    def destroySession(self, sessionName, sessionKey):
        """Destroys the session _sessionName_.  All allocations held by the
        session are deallocated.
        """

        self.authenticate(sessionName, sessionKey)

        # De-allocate all items allocated to this session
        self.deallocateAll(sessionName, sessionKey)
        
        sessionName = sessionName.lower().strip()
        tag = ('%s.session.%s' % (self.tagpfx, sessionName))

        self.mon.delete(tag, self.channels)
        
        # Make changes persistent
        self.save()
        self.logger.info("session='%s' deleted" % \
                         (sessionName))

        return ro.OK
        
    # ----- ALLOCATIONS MANIPULATION -----

    def getAllocNames(self):
        """Returns all items that are allocatable.
        """
        # TODO: make more efficient
        tag = ('%s.alloc' % self.tagpfx)
        vals = self.mon[tag]

        return vals.keys()

            
    def _getAllocInfo(self, itemName):

        try:
            tag = ('%s.alloc.%s' % (self.tagpfx, itemName))
            vals = self.mon.getitems_suffixOnly(tag)
            if vals == ro.ERROR:
                raise sessionAllocError("Not a valid item '%s' to allocate." % \
                                    itemName)

        except KeyError, e:
            raise sessionAllocError("Not a valid item '%s' to allocate." % \
                                    itemName)
            
        return vals
        

    def canAllocate(self, itemName, sessionName):

        vals = self._getAllocInfo(itemName)

        # Is this a count-limited allocation item
        if vals.has_key('limited') and (vals['limited'] == False):
            # no, can allocate
            return True
            
        return vals.has_key('count') and (vals['count'] > 0)
        
        
    def _do_allocate(self, itemName, sessionName):
        """Internal method to allocate an item, DOES NOT CHECK FOR
        ITEM AVAILABILITY.  DO NOT USE EXCEPT FROM OTHER METHODS,
        AFTER CHECKING WITH canAllocate()
        """
        # Protect ourselves against multiple allocations
        if self.isAllocatedToSession(itemName, sessionName):
            self._do_deallocate(itemName, sessionName)

        vals = self._getAllocInfo(itemName)

        sessionName = sessionName.lower().strip()

        count = vals['count']
        allocList = vals['allocList']

        tag = ('%s.alloc.%s' % (self.tagpfx, itemName))
        allocList.append(sessionName)
        self.mon.setvals(self.channels, tag, count=count-1,
                         allocList=allocList)
        self.logger.info("Allocated '%s' to session='%s'" % (
            itemName, sessionName))
                                

    def _do_deallocate(self, itemName, sessionName):
        """Internal method to deallocate an item.
        """
        vals = self._getAllocInfo(itemName)

        sessionName = sessionName.lower().strip()

        count = vals['count']
        allocList = vals['allocList']

        try:
            allocList.remove(sessionName)
           
            tag = ('%s.alloc.%s' % (self.tagpfx, itemName))
            self.mon.setvals(self.channels, tag, count=count+1,
                             allocList=allocList)

            self.logger.info("Deallocated '%s' from session='%s'" % (
                itemName, sessionName))

        except ValueError:
            raise sessionAllocError("Item '%s' not allocated to this session." % \
                                    itemName)
                                

    def isAllocatedToSession(self, itemName, sessionName):
        """Checks whether _itemName_ is allocated to _sessionName_.
        Returns True/False.
        """

        sessionName = sessionName.lower().strip()

        vals = self._getAllocInfo(itemName)

        return sessionName in vals['allocList']
        

    def deallocate(self, itemList, sessionName, sessionKey):
        """Try to deallocate all items allocated to _sessionName_.
        """
        self.authenticate(sessionName, sessionKey)

        for itemName in itemList:
            if self.isAllocatedToSession(itemName, sessionName):
                self._do_deallocate(itemName, sessionName)
            else:
                # Silently ignore attempts to deallocate something that is
                # not allocated
                pass

        # Update the session portion of our tables, not strictly
        # necessary, but it shows the allocations in the session info
        sp = self.getSessionInfo(sessionName)
        sp['allocs'] = self.getSessionAllocations(sessionName)
        self.updateSession(sessionName, sp)

        # Load/unload instrument data keys
        self.instrument_change(sessionName, sessionKey, sp['allocs'])

        return ro.OK


    def getSessionAllocations(self, sessionName):
        """Return a list of all the item allocations recorded to session
        _sessionName_.
        """

        res = []
        for itemName in self.getAllocNames():
            if self.isAllocatedToSession(itemName, sessionName):
                res.append(itemName)

        return res

        
    def getAllocationsBySession(self):
        """Return all the allocations in a dictionary, indexed by session
        name.
        """

        res = {}
        for sessionName in self.getSessionNames():
            res[sessionName] = self.getSessionAllocations(sessionName)

        return res

        
    def getAllocationsByItem(self):
        """Return all the allocations in a dictionary, indexed by itemName.
        """

        res = {}
        for itemName in self.getAllocNames():
            allocInfo = self._getAllocInfo(itemName)
            res[itemName] = allocInfo['allocList']

        return res

        
    def deallocateAll(self, sessionName, sessionKey):
        """Try to deallocate all items allocated to this session.
        """
        return self.deallocate(self.getAllocNames(), sessionName,
                               sessionKey)


    def allocate(self, itemList, sessionName, sessionKey):
        """Try to atomically allocate the list of items to the given
        session.
        """
        self.authenticate(sessionName, sessionKey)

        # Check the entire list, make sure we can allocate everything
        for itemName in itemList:
            if not self.canAllocate(itemName, sessionName):
                raise sessionAllocError("Can't allocate item '%s' to this session." % itemName)

        # Now iterate over the list, doing allocations
        for itemName in itemList:
            self._do_allocate(itemName, sessionName)

        # Update the session portion of our tables, not strictly
        # necessary, but it shows the allocations in the session info.
        # This also updates the necessary SOSS status items.
        sp = self.getSessionInfo(sessionName)
        sp['allocs'] = self.getSessionAllocations(sessionName)
        self.updateSession(sessionName, sp)

        # Load/unload instrument data keys
        self.instrument_change(sessionName, sessionKey, sp['allocs'])

        # Restart TaskManager
        try:
            self.logger.info("Restarting TaskManager...")
            # TODO: SERVICE NAME SHOULD BE PARAMETERIZED!!!
            self.bootmgr.restart('taskmgr0')

        except Exception, e:
            self.logger.warn("Error restarting TaskManager: %s" % (str(e)))

        return ro.OK


    # TEMP: called by IntegGUI to allocate 
    def alloc(self, mainInst, itemList):
        sessionName = primarySessionName
        info = self.getSessionInfo(sessionName)

        # Sanity check
        mainInst = self.insconfig.getNameByCode(
            self.insconfig.getCodeByName(mainInst))
        
        info['mainInst'] = mainInst
        self.updateSession(sessionName, info)

        # Make sure mainInst is in allocs
        allocs = set(itemList)
        allocs.add(mainInst)
        
        # Add typical items needed for observation
        for item in primarySessionAllocs:
            allocs.add(item)
                
        res = self.allocate(list(allocs), sessionName, info['key'])

        return res

        
    # TEMP: called by IntegGUI to deallocate 
    def free(self, itemList):
        sessionName = primarySessionName
        info = self.getSessionInfo(sessionName)

        if ('all' in itemList) or ('ALL' in itemList) or ('All' in itemlist):
            return self.deallocateAll(sessionName, info['key'])
        else:
            return self.deallocate(itemList, sessionName, info['key'])


    def configureFromOPAL(self, opalrec, sessionName, sessionKey):
        """Configure the session from an OPAL record.  The best kind
        of record is a TSR record, but a record from ALLOC will also do
        (it just won't fill in all the information).
        """

        self.authenticate(sessionName, sessionKey)

        info = self.getSessionInfo(sessionName)

        # Fill in the session info from the OPAL record.
        info['propid'] = opalrec['propid']
        
        if opalrec.has_key('sslist'):
            # <-- this is a TSR record
            if len(opalrec['sslist'].strip()) == 0:
                info['ss'] = opalrec['ss']
            else:
                info['ss'] = opalrec['sslist']
            info['operator'] = opalrec['oplist']
            info['observers'] = opalrec['observers']
        else:
            # <-- Some other kind of record, maybe from ALLOC table
            info['observers'] = opalrec.get('last', 'N/A')

        if opalrec.has_key('instr'):

            instr = opalrec['instr'].upper().strip()
            if instr == 'ALL':
                return ro.OK

            # AO is listed as XXXX+AO
            inslst = instr.split('+')
            instr = inslst[0]

            # Sanity check
            mainInst = self.insconfig.getNameByCode(
                self.insconfig.getCodeByName(instr))

            info['mainInst'] = mainInst

            self.updateSession(sessionName, info)

            # First, deallocate everything
            self.deallocateAll(sessionName, sessionKey)
            
            # Make sure mainInst is in allocs
            allocs = set([mainInst])

            # Ugh, hack.  Add "accessory" instruments automatically
            # in the case of NasIR instruments
            if mainInst in ('IRCS', 'HICIAO'):
                allocs = allocs.union(set(['WAVEPLAT', 'AO188', 'LGS']))

            # Add other typical items needed for observation
            for item in primarySessionAllocs:
                allocs.add(item)

            # Finally, attempt to allocate everything
            return self.allocate(list(allocs), sessionName, info['key'])

        else:
            # Update session info
            self.updateSession(sessionName, info)

        return ro.OK
    
        
    # ----- DATA SINKS MANIPULATION -----

    def add_datakey(self, sessionName, sessionKey, dataKey, properties):

        #self.authenticate(sessionName, sessionKey)
            
        tag = '%s.datakeys.%s' % (self.tagpfx, dataKey)
        with self.lock:
            # Create data key entry if it doesn't exist
            if not self.mon.has_key(tag):
                self.mon.setvals(['datakeys'], tag, clients=[],
                                 properties=properties,
                                 update_time=time.time())
                self.logger.info("Data key '%s' added" % (dataKey))

            else:
                self.mon.setvals(['datakeys'], tag, 
                                 properties=properties,
                                 update_time=time.time())
                self.logger.info("Data key '%s' modified" % (dataKey))

            # Make changes persistent
            self.save()

        return ro.OK

   
    def del_datakey(self, sessionName, sessionKey, dataKey):

        #self.authenticate(sessionName, sessionKey)

        with self.lock:
            tag = '%s.datakeys.%s' % (self.tagpfx, dataKey)
            if self.mon.has_key(tag):
                # for some reason this causes a remote deletion exception
                # with the usual channel datakeys2
                self.mon.delete(tag, ['datakeys'])

                # Make changes persistent
                self.save()
                self.logger.info("Data key '%s' removed" % (dataKey))

        return ro.OK


    def gen_datakey(self, sessionName, sessionKey, keyName,
                    overwrite=False):

        #self.authenticate(sessionName, sessionKey)
            
        keyName = keyName.lower()

        dataKey = self.genkey2(keyName)
        
        keyFile = ("%s/keys/%s.key" % (os.environ['GEN2COMMON'], keyName))

        if os.path.exists(keyFile) and not overwrite:
            self.logger.info("Key exists (%s) and overwrite=False" % keyFile)
            return ro.OK
        
        out_f = open(keyFile, 'w')
        out_f.write(dataKey + '\n')
        out_f.close()
        os.chmod(keyFile, 0660)

        self.logger.info("Key written to %s" % keyFile)

        return ro.OK


    def read_datakey(self, keyName):

        keyName = keyName.lower()

        keyFile = ("%s/keys/%s.key" % (os.environ['GEN2COMMON'], keyName))
        #self.logger.debug("opening key file '%s'" % keyFile)

        in_f = open(keyFile, 'r')
        dataKey = in_f.read().strip()
        in_f.close()

        return dataKey


    def load_datakey(self, sessionName, sessionKey, keyName, properties):

        dataKey = self.read_datakey(keyName)

        return self.add_datakey(sessionName, sessionKey, dataKey, properties)


    def revoke_datakey(self, sessionName, sessionKey, keyName):

        dataKey = self.read_datakey(keyName)

        return self.del_datakey(sessionName, sessionKey, dataKey)


    def get_datakeys(self):
        
        tag = '%s.datakeys' % (self.tagpfx)
        vals = self.mon.get_node(tag)
        self.logger.debug("vals = %s" % str(vals))

        return vals.keys()
    

    def clear_datakeys(self, sessionName, sessionKey):
        
        #self.authenticate(sessionName, sessionKey)

        with self.lock:
            for dataKey in self.get_datakeys():
                self.del_datakey(sessionName, sessionKey, dataKey)

        return ro.OK


    def get_datasink(self, dataKey):

        with self.lock:
            tag = '%s.datakeys.%s' % (self.tagpfx, dataKey)
            if not self.mon.has_key(tag):
                raise sessionError("Not a valid key: '%s'" % (dataKey))

            vals = self.mon.get_dict(tag)
            self.logger.debug("vals=%s" % str(vals))
            return vals

    
    def get_datasinks(self):

        with self.lock:
            d = {}
            for dataKey in self.get_datakeys():
                d[dataKey] = self.get_datasink(dataKey)

            return d


    def authorize_sink(self, keyName, hmac_digest):

        dataKey = self.read_datakey(keyName)

        vals = self.get_datasink(dataKey)
        self.logger.debug("vals=%s" % str(vals))

        passphrase = vals['properties'].get('passphrase', '')
        self.logger.debug("key='%s' passphrase='%s'" % (
            dataKey, passphrase))
        
        # Compute hmac
        my_hmac_digest = hmac.new(dataKey, passphrase,
                                  digest_algorithm).hexdigest()

        if hmac_digest != my_hmac_digest:
            self.logger.debug("Digest mismatch: mine=%s theirs=%s" % (
                my_hmac_digest, hmac_digest))
            raise sessionError("Data sink authorization error: key or passphrase mismatch")

        return dataKey, vals
        

##     def update_archivers(self):
        
##         # Update Archiver with new idea of data sinks
##         sinks = self.get_datasinks()

##         try:
##             archiver = ro.remoteObjectProxy('archiver')
##             archiver.setup_datasinks(sinks)

##             return ro.OK

##         except ro.remoteObjectError, e:
##             self.logger.error("Unable to update Archiver with data sinks: %s" % (
##                 str(e)))
##             return ro.ERROR

    def _register_datasink(self, svc, dataKey, vals):

        with self.lock:
            clients = vals['clients']
            if not svc in clients:
                clients.append(svc)

                tag = '%s.datakeys.%s' % (self.tagpfx, dataKey)
                self.mon.setvals(['datakeys'], tag, clients=clients,
                                 update_time=time.time())
            # Make changes persistent
            self.save()
            self.logger.info("Registered %s under key '%s'" % (
                str(svc), dataKey))

        # Update Archivers
##             self.update_archivers()
        
        return ro.OK


    def register_datasink(self, svc, keyName, hmac_digest):

        with self.lock:
            dataKey, vals = self.authorize_sink(keyName, hmac_digest)

            return self._register_datasink(svc, dataKey, vals)


    def _unregister_datasink(self, svc, dataKey, vals):

        with self.lock:
            clients = vals['clients']
            self.logger.debug("removing client")
            if svc in clients:
                clients.remove(svc)

                self.logger.debug("updating monitor")
                tag = '%s.datakeys.%s' % (self.tagpfx, dataKey)
                self.mon.setvals(['datakeys'], tag, clients=clients,
                                 update_time=time.time())

            # Make changes persistent
            self.save()
            self.logger.info("Unregistered %s under key '%s'" % (
                str(svc), dataKey))

            # Update Archivers
##             self.update_archivers()

        return ro.OK


    def unregister_datasink(self, svc, keyName, hmac_digest):

        with self.lock:
            dataKey, vals = self.authorize_sink(keyName, hmac_digest)

            return self._unregister_datasink(svc, dataKey, vals)


    def add_datasink(self, host, port, keyName):

        dataKey = self.read_datakey(keyName)

        vals = self.get_datasink(dataKey)

        return self._register_datasink([host, port], dataKey, vals)


    def del_datasink(self, host, port, keyName):

        dataKey = self.read_datakey(keyName)

        vals = self.get_datasink(dataKey)

        return self._unregister_datasink([host, port], dataKey, vals)


    def clear_datasinks(self, keyName):

        dataKey = self.read_datakey(keyName)

        vals = self.get_datasink(dataKey)

        if vals.has_key('clients'):
            for svc in vals['clients']:
                self._unregister_datasink(svc, dataKey, vals)

        return ro.OK



def main(options, args):

    if options.svcname:
       svcname = options.svcname
    else:
        svcname = serviceName
        
    # Create top level logger.
    logger = ssdlog.make_logger(svcname, options)

    # Initialize remote objects subsystem.
    try:
        ro.init()

    except ro.remoteObjectError, e:
        logger.error("Error initializing remote objects subsystem: %s" % str(e))
        sys.exit(1)

    # Session monitor
    minimon = Monitor.Monitor('%s.mon' % svcname, logger,
                              dbpath=options.dbpath,
                              numthreads=options.numthreads)
    channels = list(monchannels)
    channels.extend(['datakeys'])
    minimon.publish_to(options.monitor, channels, {})
    minimon.start(wait=True)

    # Configure logger for logging via our monitor
    if options.logmon:
        minimon.logmon(logger, options.logmon, ['logs'])

    # Encapsulate our remote object interface as a simple class
    # 
    class roInterface(ro.remoteObjectServer):

        def __init__(self, svcname, sm, usethread=False, threadPool=None):
            self.ev_quit = threading.Event()
            self.sm = sm

            # Superclass constructor
            ro.remoteObjectServer.__init__(self, svcname=svcname,
                                           obj=self.sm, logger=logger,
                                           port=options.port,
                                           ev_quit=self.ev_quit,
                                           usethread=usethread,
                                           threadPool=threadPool)

    threadPool = minimon.get_threadPool()
    
    sm = SessionManager(svcname, logger, minimon, threadPool,
                        automount_propdir=options.automount_propdir)
    sm.start()
    
    # Create our remote service object
    svc = roInterface(svcname, sm, usethread=False, threadPool=threadPool)

    # Start it
    try:
        logger.info("Starting Session Manager service...")
        try:
            svc.ro_start()

        except KeyboardInterrupt:
            logger.error("Caught keyboard interrupt!")

    finally:
        logger.info("Session Manager service shutting down...")
        sm.stop(wait=True)
        minimon.stop(wait=True)
        svc.ro_stop()


def quote_spaces(s):
    # Spaces cause all kinds of problems for FITS headers,
    # status request handling, etc.
    if ' ' in s:
        s = '"' + s + '"'
    return s


if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("--ampd", dest="automount_propdir",
                      default=False, action="store_true",
                      help="Automount proposal directories on propid changes")
    optprs.add_option("--db", dest="dbpath", metavar="FILE",
                      help="Use FILE as the monitor database")
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-m", "--monitor", dest="monitor", 
                      metavar="NAME", default='monitor',
                      help="Reflect internal status to monitor service NAME")
    optprs.add_option("--numthreads", dest="numthreads", type="int",
                      default=50,
                      help="Use NUM threads", metavar="NUM")
    optprs.add_option("--port", dest="port", type="int", default=None,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--svcname", dest="svcname", metavar="NAME",
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

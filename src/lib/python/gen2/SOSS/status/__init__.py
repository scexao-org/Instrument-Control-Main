"""SOSS_status - an interface to SOSS status.

Implements a Python dictionary interface to the SOSS status system.

This kind of object does not cache results, and ALWAYS makes a new rpc call
for each dictionary access and for each status alias.

Example 1:
    ...
    import SOSS.status
    ...
    status = SOSS.status.rpcStatusObj('obc')

    print status['TSCS.AZ']


Example 2:
    ...
    import SOSS.status
    ...
    status = SOSS.status.cachedStatusObj(host='obc')

    # Set a expiration time of 1/10 sec for TSCS table values
    status.set_tableExpiration('TSCS', 0.10)
    ...
    print status['TSCS.AZ']


Example 3:
    ...
    import SOSS.status
    ...
    status = SOSS.status.possiblyStaleStatusObj(host='obc')

    print status['TSCS.AZ']


The difference between the three different kinds of status objects are as follows:

- rpcStatusObj-ects make a new rpc call for each access to a status value.  Hence,
  you can always count on the freshest status, but at the cost of some network
  traffic, since a call is made for each piece of status.  NOTE THAT THESE OBJECTS
  ARE *NOT* THREAD_SAFE.

- cachedStatusObj-ects pull entire tables of status on each rpc call and cache it
  in the object.  If you set the table expiration time, then any subsequent calls
  to fetch status from the same table within the time delta will use cached values.
  This means potentially less network traffic.  In general, this is the all around
  best choice for fetching status because many SOSS status values are cached
  themselves (on the SOSS side).  These objects ARE thread-safe.  You should probably
  set different table expiration times depending on your needs; the default is 1 sec.

- possiblyStaleCachedStatusObj-ects are the same as cachedStatusObj-ects, but will
  not throw an exception if the cache data is stale and new status cannot be fetched.
  Useful for applications that wish to tolerate status outages gracefully.
  
"""

__author__ = "Eric Jeschke <eric@naoj.org>"

from common import STATNONE, STATERROR, statusError, assertValidStatusValue, \
     assertValidStatusValues

from Convert import statusInfoError, statusConversionError, statusInfo, \
     statusConverter

from SOSS_status import rpcStatusObj, cachedStatusObj, \
     possiblyStaleCachedStatusObj, storeStatusObj

from Gen2_status import g2StatusObj


__all__ = ['STATNONE', 'STATERROR', 'statusError',
           'statusInfoError', 'statusConversionError',
           'statusInfo', 'statusConverter',
           'rpcStatusObj', 'cachedStatusObj', 'possiblyStaleCachedStatusObj',
           'storeStatusObj', 'g2StatusObj']


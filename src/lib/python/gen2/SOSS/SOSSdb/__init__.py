"""SOSS.SOSSdb - support legacy SOSS Oracle database.

This provides a set of classes for manipulating the SOSS Oracle
database from Python.
  
"""

__author__ = "Eric Jeschke <eric@naoj.org>"


from SOSS_db import SOSSdbError, SOSSdbEmptyResult, SOSSdb, \
     datetime_fromSOSS1, datetime_fromSOSS2, datetime_toSOSS1, \
     datetime_toSOSS2

__all__ = ['SOSSdbError', 'SOSSdbEmptyResult', 'SOSSdb',
           'datetime_fromSOSS1', 'datetime_fromSOSS2', 'datetime_toSOSS1',
           'datetime_toSOSS2'
           ]

#END

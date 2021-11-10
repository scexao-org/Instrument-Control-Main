"""SOSS.STARSint - support legacy interface (on the SOSS side)
    to Subaru Telescope ARchive System (STARS).

This provides a set of services that implement the "client" (SOSS) side of
the STARS interface in Python.
  
"""

__author__ = "Eric Jeschke <eric@naoj.org>"


from STARSint import get_STARSparams, create_index_file, \
     STARSintError, STARSinterface
from STARSsim import STARSsimulator, STARSsimError, add_transferParams
from STARS_db import STARSdb, STARSdbError, STARSdbEmptyResult, \
     datetime_fromSTARS1, datetime_toSTARS1


__all__ = ['get_STARSparams', 'get_fits_metadata', 'create_index_file',
           'STARSintError', 'STARSinterface',
           'STARSsimulator', 'STARSsimError', 'add_transferParams',
           'STARSdb', 'STARSdbError', 'STARSdbEmptyResult',
           'datetime_fromSTARS1', 'datetime_toSTARS1'
           ]


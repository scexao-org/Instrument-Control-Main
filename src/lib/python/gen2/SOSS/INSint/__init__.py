"""SOSS.INSint - support legacy instrument interfaces (on the SOSS side) to
    Subaru Observatory Instruments.

This provides a set of services that implement the "server" (SOSS) side of
the Subaru Telescope DAQtk toolkit in Python.
  
"""

__author__ = "Eric Jeschke <eric@naoj.org>"


from BaseInterface import BaseInterface
from INSint import INSintError, ocsInsInt, \
                   FetchStatusWrapper_SOSS, FetchStatusWrapper_Gen2

__all__ = ['INSintError', 'BaseInterface', 'ocsInsInt',
           'FetchStatusWrapper_SOSS', 'FetchStatusWrapper_Gen2',
           ]

#END

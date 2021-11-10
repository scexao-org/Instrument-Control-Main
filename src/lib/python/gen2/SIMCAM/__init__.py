#
# SIMCAM -- Pluggable Subaru instrument framework/simulator
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Feb  7 11:56:19 HST 2011
#]
#
"""This module implements a general, configurable Subaru instrument interface
framework written entirely in Python.

Directory:
- simcam.py: a top-level program that invokes a variety of instrument
  'personalities' to simulate various Subaru instruments.

- Instrument.py: the main module for creating new instruments.  Provides
  a gateway between the OCS interface (currently DAQtk) and the instrument
  code.

- cams/: directory containing instrument personalities and support files.
  - SIMCAM/, SPCAM/, TSC/, etc

"""

__author__ = "Eric Jeschke <eric@naoj.org>"

mypath = __path__[0]
__path__.append(mypath + "/cams")
    
from Instrument import BASECAM, Instrument, CamError, CamCommandError, \
     CamInterfaceError
import cams

#__all__ = ['Instrument', 'BASECAM', 'SIMCAM', 'cams', 'common']
__all__ = ['Instrument', 'BASECAM', 'CamError', 'CamCommandError',
           'CamInterfaceError', 'cams']

#END

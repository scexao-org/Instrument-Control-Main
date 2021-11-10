#!/usr/bin/env python
# StatIOtest.py -- Bruce Bon -- 2008-08-26

# Test program for StatIO.py

import os
from StatIO import *
from DispType import *
import StatusDictionary
import TelStat_cfg

print '\nAllocating pane instances:'
pane1 = StatPaneBase( \
 ('TSCS.ALPHA', 'TSCS.DELTA', 'TSCS.AZ', 'TSCS.EL', 'test.addition'), 'pane1' )
pane2 = StatPaneBase( \
 ('TSCS.ALPHA', 'TSCS.INSROTCMD', 'TSCV.RotatorType'), 'pane2' )


StatIO_initialize( StatIO_ScreenPrintSim )


dictFileName = 'StatDict1' + TelStat_cfg.timeString + '.log'
print '\nCalling StatIO_printDict():'
fp = open( dictFileName, 'w' )
os.chmod( dictFileName, 0644 )
StatIO_printDict( fp )
fp.close()

print "\nTesting direct access to dictionary:"
print '  RA_HrMinSec    = ', \
        StatusDictionary.StatusDictionary[ 'TSCS.ALPHA' ].format_HrMinSec()
print '  RA_DegMinSec   = ', \
        StatusDictionary.StatusDictionary[ 'TSCS.ALPHA' ].format_DegMinSec()
print '  RA_defaultFmt  = ', \
        StatusDictionary.StatusDictionary[ 'TSCS.ALPHA' ].format()

print '\n  DEC_defaultFmt= ', \
        StatusDictionary.StatusDictionary[ 'TSCS.DELTA' ].format()
print '  AZ_defaultFmt  = ', \
        StatusDictionary.StatusDictionary[ 'TSCS.AZ' ].format()
print '  EL_defaultFmt  = ', \
        StatusDictionary.StatusDictionary[ 'TSCS.EL' ].format()

print '\n  Rotator Pos, actual = ', \
        StatusDictionary.StatusDictionary[ 'TSCS.INSROTPOS' ].format()
print '\n  RotatorType         = ', \
        StatusDictionary.StatusDictionary[ 'TSCV.RotatorType' ].format()

print '\nSetting FITS.IRC.PROP_ID:'
print StatusDictionary.StatusDictionary['FITS.IRC.PROP_ID']
print '  FITS.IRC.PROP_ID_defaultFmt  = ', \
        StatusDictionary.StatusDictionary['FITS.IRC.PROP_ID'].format()
StatusDictionary.StatusDictionary['FITS.IRC.PROP_ID'].setValue(
                                                    'FITS.IRC.PROP_ID string !!')
print StatusDictionary.StatusDictionary['FITS.IRC.PROP_ID']
print '  FITS.IRC.PROP_ID_defaultFmt  = ', \
        StatusDictionary.StatusDictionary['FITS.IRC.PROP_ID'].format()

print '\nSetting other values:'
StatusDictionary.StatusDictionary['TELSTAT.ADC'].setValue( False )
print '  TELSTAT.ADC_defaultFmt  = ', \
        StatusDictionary.StatusDictionary['TELSTAT.ADC'].format()

StatusDictionary.StatusDictionary['STATL.AG_THETA_CMD'].setValue(338.23147807)
print '  STATL.AG_THETA_CMD_defaultFmt  = ', \
        StatusDictionary.StatusDictionary['STATL.AG_THETA_CMD'].format()

StatusDictionary.StatusDictionary['TELSTAT.UNIXTIME'].setValue(38338.23147807)
print '  TELSTAT.UNIXTIME_defaultFmt  = ', \
        StatusDictionary.StatusDictionary['TELSTAT.UNIXTIME'].format()


print '\nCalling StatIO_service() 1:',
StatIO_service()

print '\nCalling StatIO_service() 2:',
StatIO_service()

print '\nCalling StatIO_service() 3:',
StatIO_service()

print '\nCalling StatIO_service() 4:',
StatIO_service()

print '\nCalling StatIO_service() 5:',
StatIO_service()

print '\nCalling StatIO_service() 6:',
StatIO_service()

print '\nCalling StatIO_service() 7:',
StatIO_service()

print '\nCalling StatIO_service() 8:',
StatIO_service()

print '\nCalling StatIO_printDict():'
dictFileName = 'StatDict2' + TelStat_cfg.timeString + '.log'
fp = open( dictFileName, 'w' )
os.chmod( dictFileName, 0644 )
StatIO_printDict( fp )
fp.close()

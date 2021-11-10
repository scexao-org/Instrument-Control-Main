#
# initialize.py -- code to initialize the Gen2 database
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Apr  9 15:46:36 HST 2012
#]
#
"""
*** BE CAREFUL RUNNING THIS CODE!!!  IT WILL INITIALIZE THE DATABASE!!! ***

Usage:
  $ python db/initialize.py
  
"""
import sys
from common import *
from schema import *
import Bunch


# -----------------------------
#session.begin(subtransactions=True)

setup_all()

# Create tables
create_all()

# -----------------------------
# populate tables specified on the command line

# Populate Instrument table
if 'instrument' in sys.argv:
    print "Populating 'instrument' table..."
    inst = Bunch.Bunch(
        IRCS=Instrument(number=1, shortname='IRCS', fullname='IRCS', code='IRC',
                        year=2008,
                        description=u'Infra Red Camera and Spectrograph'),
        AO=Instrument(number=2, shortname='AO', fullname='AO', code='AOS',
                      year=2008, description=u'Adaptive Optics 36'),
        CIAO=Instrument(number=3, shortname='CIAO', fullname='CIAO', code='CIA',
                        year=2008,
                        description=u'Coronagraphic Imager with Adaptive Optics'),
        OHS=Instrument(number=4, shortname='OHS', fullname='OHS', code='OHS',
                       year=2008, description=u''),
        FOCAS=Instrument(number=5, shortname='FOCAS', fullname='FOCAS', code='FCS',
                         year=2008, description=u''),
        HDS=Instrument(number=6, shortname='HDS', fullname='HDS', code='HDS',
                       year=2008, description=u'High Dispersion Spectrograph'),
        COMICS=Instrument(number=7, shortname='COMICS', fullname='COMICS', code='COM',
                          year=2008, description=u''),
        SPCAM=Instrument(number=8, shortname='SPCAM', fullname='Suprime Cam',
                         code='SUP', year=2008, description=u''),
        SUKA=Instrument(number=9, shortname='SUKA', fullname='SUKA', code='SUK',
                        year=2008, description=u''),
        MIRTOS=Instrument(number=10, shortname='MIRTOS', fullname='MIRTOS',
                          code='MIR', year=2008, description=u''),
        VTOS=Instrument(number=11, shortname='VTOS', fullname='VTOS', code='VTO',
                        year=2008, description=u''),
        CAC=Instrument(number=12, shortname='CAC', fullname='CAC', code='CAC',
                       year=2008, description=u'Commissioning instrument'),
        SKYMON=Instrument(number=13, shortname='SKYMON', fullname='Sky Monitor',
                          code='SKY', year=2008, description=u''),
        PI1=Instrument(number=14, shortname='PI1', fullname='PI 1', code='PI1',
                       year=2008, description=u''),
        K3D=Instrument(number=15, shortname='K3D', fullname='Kyoto 3D', code='K3D',
                       year=2008, description=u''),
        SCEXAO=Instrument(number=16, shortname='SCEXAO', fullname='SCEXAO',
                           code='XAO', year=2008, description=u'Extreme AO'),
        MOIRCS=Instrument(number=17, shortname='MOIRCS', fullname='MOIRCS',
                          code='MCS', year=2008,
                          description=u'Multi-Object Infra-Red Camera and Spectrograph'),
        FMOS=Instrument(number=18, shortname='FMOS', fullname='FMOS', code='FMS',
                        year=2008, description=u'Fiber Multi-Object Spectrograph'),
        FLDMON=Instrument(number=19, shortname='FLDMON', fullname='Field Monitor',
                          code='FLD',
                          year=2008, description=u'High Intensity Field Imager'),
        AO188=Instrument(number=20, shortname='AO188', fullname='AO188', code='AON',
                         year=2008, description=u'Adaptive Optics 188'),
        HICIAO=Instrument(number=21, shortname='HICIAO', fullname='HiCIAO',
                          code='HIC', year=2008, description=u''),
        WAVEPLAT=Instrument(number=22, shortname='WAVEPLAT', fullname='Waveplate',
                            code='WAV',
                            year=2008, description=u'Nasmyth Waveplate Unit for IR'),
        LGS=Instrument(number=23, shortname='LGS', fullname='LGS', code='LGS',
                       year=2008, description=u'Laser Guide Star'),
        HSC=Instrument(number=24, shortname='HSC', fullname='Hyper-Suprime Cam',
                       code='HSC',
                       year=2011, description=u'Hyper-Suprime Cam'),
        OTHER25=Instrument(number=25, shortname='OTHER25', fullname='OTHER25',
                           code='025',
                           year=2020, description=u'Future Instrument'),
        OTHER26=Instrument(number=26, shortname='OTHER26', fullname='OTHER26',
                           code='026',
                           year=2020, description=u'Future Instrument'),
        OTHER27=Instrument(number=27, shortname='OTHER27', fullname='OTHER27',
                           code='027',
                           year=2020, description=u'Future Instrument'),
        OTHER28=Instrument(number=28, shortname='OTHER28', fullname='OTHER28',
                           code='028',
                           year=2020, description=u'Future Instrument'),
        OTHER29=Instrument(number=29, shortname='OTHER29', fullname='OTHER29',
                           code='029',
                           year=2020, description=u'Future Instrument'),
        OTHER30=Instrument(number=30, shortname='OTHER30', fullname='OTHER30',
                           code='030',
                           year=2020, description=u'Future Instrument'),
        OTHER31=Instrument(number=31, shortname='OTHER31', fullname='OTHER31',
                           code='031',
                           year=2020, description=u'Future Instrument'),
        OTHER32=Instrument(number=32, shortname='OTHER32', fullname='OTHER32',
                           code='032',
                           year=2020, description=u'Future Instrument'),
        VGW=Instrument(number=33, shortname='VGW', fullname='VGW', code='VGW',
                       year=2008, description=u'Guide Star Images')
        )

    # Add instruments up to 99.  Remove this if we ever get past 33.
    for i in range(34, 100):
        name = 'OTHER%02d' % i
        inst[name] = Instrument(number=i, shortname=name, fullname=name,
                                code='O%02d' % i,
                                year=2020, description=u'Future Instrument')

# Sort by number
instruments = inst.values()
instruments.sort(lambda x, y: cmp(x.number, y.number))

# Populate FrameMap table (frame counts)
if 'framemap' in sys.argv:
    print "Populating 'framemap' table..."
    for ins in instruments:
        name = ins.shortname
        for frtype in ('A', 'Q'):
            for prefix in ('0', '7', '8', '9'):
                FrameMap(instrument=inst[name], frtype=frtype, prefix=prefix,
                         count=0)

# -----------------------------
# finalize
session.commit()

session.flush()

# -----------------------------
session.close()

sys.exit(0)

# -----------------------------

# END

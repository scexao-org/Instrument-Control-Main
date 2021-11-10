#
# Base module for SOSS status related components
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Sun Apr 17 12:17:50 HST 2011
#]


# If True, invoke special workaround for XML-RPC inability to transmit
# long ints
ro_long_fix = False

# If True, transmit changing status through a special monitor channel
mon_transmit = True


class statusError(Exception):
    """Base class for all exceptions thrown by methods in the SOSS status
    module.
    """
    pass

# Constants for Gen2 status
STATNONE  = '##NODATA##'
STATERROR = '##ERROR##'

# TABLE DEFINITIONS FOR GEN2
#     table     "owner"   max size     Notes   
tableDef = [
    ('TSCS',     'tsc',    1292),
    ('TSCL',     'tsc',    9044),
    ('TSCV',     'tsc',    200000),
    ('IRCS0001', 'obcp1',  2222),
    ## ('AOSS0001', 'obcp2',  2222),      # extinct OBCP
    ## ('AOSS0002', 'obcp2',  2222),      # extinct OBCP
    ## ('AOSS0003', 'obcp2',  2222),      # extinct OBCP
    ## ('AOSS0004', 'obcp2',  2222),      # extinct OBCP
    ## ('AOSS0005', 'obcp2',  2222),      # extinct OBCP
    ## ('AOSS0006', 'obcp2',  2222),      # extinct OBCP
    ## ('AOSS0007', 'obcp2',  2222),      # extinct OBCP
    ## ('AOSS0008', 'obcp2',  2222),      # extinct OBCP
    ## ('CIAS0001', 'obcp3',  2222),      # extinct OBCP
    ## ('CIAS0002', 'obcp3',  2222),      # extinct OBCP
    ## ('CIAS0004', 'obcp3',  2222),      # extinct OBCP
    ## ('CIAS0005', 'obcp3',  2222),      # extinct OBCP
    ## ('OHSS0001', 'obcp4',  2222),      # extinct OBCP
    ('FCSS0001', 'obcp5',  2222),      # FOCAS
    ('FCSS0002', 'obcp5',  2222),
    ('FCSS0003', 'obcp5',  2222),
    ('FCSS0004', 'obcp5',  2222),
    ('FCSS0005', 'obcp5',  2222),
    ('FCSS0006', 'obcp5',  2222),
    ('FCSS0008', 'obcp5',  2222),
    ('FCSS0009', 'obcp5',  2222),
    ('HDSS0001', 'obcp6',  2222),      # HDS
    ('COMS0001', 'obcp7',  2222),      # COMICS
    ('SUPS0001', 'obcp8',  2222),      # SPCAM
    ('OBCPD',    'obcp9',  2222),      # SUKA
    ## ('MIRS0001', 'obcp10', 2222),      # extinct OBCP
    ## ('VTOS0001', 'obcp11', 2222),      # extinct OBCP
    ## ('CACS0001', 'obcp12', 2222),      # extinct OBCP
    ## ('SKYS0001', 'obcp13', 2222),      # extinct OBCP
    ## ('PI1S0001', 'obcp14', 2222),      # extinct OBCP
    ('K3DS0001', 'obcp15', 2222),      # Kyoto3D
    ## ('O16S0001', 'obcp16', 2222),      # extinct OBCP
    ('MCSS0001', 'obcp17', 2222),      # MOIRCS
    ('MCSS0002', 'obcp17', 2222),
    ('MCSS0003', 'obcp17', 2222),
    ('MCSS0004', 'obcp17', 2222),
    ('FMSS0001', 'obcp18', 2222),      # FMOS
    ('FMSS0002', 'obcp18', 2222),
    ('FMSS0003', 'obcp18', 2222),
    ('FMSS0004', 'obcp18', 2222),
    ('FLDS0001', 'obcp19', 2222),      # FieldMonitor
    ('AONS0001', 'obcp20', 2222),      # AO188
    ('HICS0001', 'obcp21', 2222),      # HICIAO
    ('WAVS0001', 'obcp22', 2222),      # Waveplate
    ## ('LGSS0001', 'obcp23', 2222),      # Nonexistent OBCP
    ('HSCS0001', 'obcp24', 2222),      # HSC
    ('VGWC',     'obcp33', 4848),      # ?? is this actually used?
    ('VGWD',     'obcp33', 640),
    ('VGWQ',     'obcp33', 4224),
    ]


class baseStatusObj(object):
    """Abstract base class from which the other xxxStatusObj's inherit.
    Provides standard common dictionary interface for these objects.
    """
    
    def __init__(self):
        super(baseStatusObj, self).__init__()


    def __getitem__(self, alias):
        """Returns the value associated with a status alias.
        """
        return self.get_statusValue(alias)


    def __setitem__(self, alias, val):
        """Sets a value associated with a status alias.
        """
        return self.set_statusValue(alias, val)


    # This is an abstract class--base classes are expected to provide
    # an "info" attribute ---------------------
    def get_statusInfo(self):
        return self.info
        
    def keys(self):
        """Returns the list of all status aliases (names) known to us."""

        return self.info.getAliasNames()


    def getAliasNames(self):
        """Return the list of all status aliases known to us."""

        return self.info.getAliasNames()


    def getTableNames(self):
        """Return the list of all table names known to us."""

        return self.info.getTableNames()
        
    # -----------------------------------------
        
    def get_statusTable(self, tablename):
        raise common.statusError("Subclass needs to provide this method!")

    def get_statusValue(self, aliasname):
        raise common.statusError("Subclass needs to provide this method!")

        
def ro_sanitize(statusDict, pfx=None):
    """Sanetize a dictionary of values for travel over remoteObjects.
    This is currently XML-RPC based, and doesn't allow integer values
    larger than 32 bits.  These values are converted to a special form:
    0xYYYYYYYYYYYYL, where the prefix '0x' indicates such an encoded
    form, and YYYY... is the hex-encoded string representing the value.

    This method returns a copy of the statusDict with all such special
    values converted.
    """

#     try:
#         del statusDict['STATLOG']
#         del statusDict['CXWS.TSCV.OBE_INR']
#         del statusDict['TSCV.ZERNIKE_RMS_WOA20']
#         del statusDict['TSCV.ZERNIKE_RMS']
#         del statusDict['TSCV.OBJKIND']
#     except KeyError:
#         pass

    # Create a new dictionary and iterate over the alias/value set
    # transforming the affected values and aliases
    newDict = {}
    for alias, val in statusDict.items():
        if isinstance(val, long) and ro_long_fix:
            val = hex(val)
        # expat (XML-RPC parser) does not like NULs embedded in strings
        elif isinstance(val, str) and ('\x00' in val):
            # Just skip these items
            continue

        if pfx:
            newDict['%s%s' % (pfx, alias)] = val
        else:
            newDict[alias] = val

    return newDict


def ro_unsanitize(statusDict):

    for key, val in statusDict.items():
        if isinstance(val, str) and val.startswith('0x') and \
               val.endswith('L'):
            statusDict[key] = long(val, 16)

    return statusDict

            
def assertValidStatusValue(name, value):
    if value in (STATNONE, STATERROR):  
        raise statusError("Invalid or undefined status (%s) value '%s'" % (
            name, str(value)))
    
def assertValidStatusValues(*args):
    for name, value in args:
        assertValidStatusValue(name, value)
        

#END


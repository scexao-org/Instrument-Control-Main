#
# Convert.py -- SOSS status conversion
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Nov 12 10:40:02 HST 2010
#]
# Yasu Sakakibara (yasu@naoj.org)
#
#
import sys, os, time
import re, binascii
import struct

from Bunch import Bunch
import common


tableDeffilename = 'Table.def'
statusAliasDeffilename = 'StatusAlias.def'
TSCVDeffilename = 'StatusTSCV.def'


class statusInfoError(common.statusError):
    """Class for value conversion errors.
    """
    pass

class statusConversionError(common.statusError):
    """Class for value conversion errors.
    """
    pass


def conv_TSCL_CAL_HCTx_AMP(val_D, aliasdef):
    try:
        digits = binascii.hexlify(val_D)
        ascstr = digits[1:4] + '.' + digits[4:]
    #        print "digits are: %s" % digits
        if digits.startswith('8'):
            val = -float(ascstr)
        else:
            val = float(ascstr)
    except ValueError, e:
        # TSC seems to return all 'f's if there is no status
        if digits == 'ffffffffffff':
            val = None
        else:
            raise statusConversionError("Unrecognized format: %s" % str(e))
            
    # empty string-- return null??
    return val

    
def conv_strange(val, aliasdef):
    print "Strange value: %s" % str(val)
    
    return None


# Supplementary data on SOSS StatusAlias.def
#
# This table contains additional information regarding SOSS status
# aliases that is not contained in the StatusAlias.def file.  Example
# attributes are: type: a conversion override of the type (typical
# example is most non-TSC aliases which are all 'C' types (strings);
# many of these are actually ASCII-encoded integers (I) or floats
# (F)).
#
statusAlias_SupplementaryData = {
    'FITS.SBR.EQUINOX': {'type': 'F'},
    'FITS.SBR.AIRMASS': {'type': 'F'},
    'FITS.SBR.ALTITUDE': {'type': 'F'},
    'FITS.SBR.AZIMUTH': {'type': 'F'},
    'FITS.SBR.OUT_HUM': {'type': 'F'},
    'FITS.SBR.OUT_TMP': {'type': 'F'},
    'FITS.SBR.OUT_WND': {'type': 'F'},
    'FITS.SBR.OUT_PRS': {'type': 'F'},
    'TSCL.CAL_HCT1_AMP': {'conv': conv_TSCL_CAL_HCTx_AMP},
    'TSCL.CAL_HCT2_AMP': {'conv': conv_TSCL_CAL_HCTx_AMP},

##     'CXWS.TSCV.POWER_V1': {'conv': conv_strange},
##     'CXWS.TSCV.POWER_V2': {'conv': conv_strange},
##     'CXWS.TSCV.OBE_ID': {'conv': conv_strange},
##     'CXWS.TSCL.Z_SENSOR': {'conv': conv_strange},
##     'STATUS.MLP2_VZ': {'conv': conv_strange},
##     'STATUS.MLP2_V2': {'conv': conv_strange},
##     'TSCV.M1Cover': {'conv': conv_strange},
##     'STATUS.MLP2_L3A': {'conv': conv_strange},
##     'STATUS.MLP2_L3F': {'conv': conv_strange},
##     'STATUS.MLP2_L2': {'conv': conv_strange},
##     'CXWS.TSCL.POWER': {'conv': conv_strange},
##     'STATUS.AG_L': {'conv': conv_strange},
##     'STATUS.AG_V': {'conv': conv_strange},
    }


class statusInfo(object):
    """ Helper class to parse and hold content of StatusAlias.def,
    Table.def and StatusTSCV.def files.
    """

    def __init__(self, tableDef=None, statusAliasDef=None, TSCVDef=None,
                 version=1):

        super(statusInfo, self).__init__()

        self.reloadInfo(tableDef=tableDef, statusAliasDef=statusAliasDef,
                        TSCVDef=TSCVDef, version=version)

        
    def get_conf(self, filename):

        if not os.environ.has_key('OSS_SYSTEM'):
            dir = os.path.split(sys.modules[__name__].__file__)[0]
            
        else:
            dir = os.environ['OSS_SYSTEM']

        if not dir:
            raise statusInfoError('OSS_SYSTEM env variable is not defined.')

        return dir + '/' + filename


    def reloadInfo(self, tableDef=None, statusAliasDef=None, TSCVDef=None,
                   version=1):

        if tableDef == None:
            if version == 1:
                tableDef = self.get_conf(tableDeffilename)
        if statusAliasDef == None:
            statusAliasDef = self.get_conf(statusAliasDeffilename)
        if TSCVDef == None:
            TSCVDef = self.get_conf(TSCVDeffilename)

        # Read in Table.def and StatusAlias.def files
        if version == 1:
            self.__read_tableDef(tableDef)
        else:
            self.__read_tableDefv2(common.tableDef)

        self.__read_statusAliasDef(statusAliasDef)

        # build reverse index
        self.__buildRevIndex()

        # read TSCVDef file
        self.__read_TSCVDef(TSCVDef)
        

    # Read and parse the SOSS Table.def file.  Stores results in a dictionary
    # indexed by table name.  The value of each dictionary element is a Bunch.
    #
    def __read_tableDef(self, file):

        try:
            in_f = open(file, 'r')

        except IOError, e:
            raise statusInfoError("Cannot read status configuration data: %s" % str(e))

	self.tableDef = {}

        for line in in_f:
            line = line.strip()
	    parts = line.split(',')
            table = parts[2].strip().upper()

            # Skip blank and comment lines
            if line == "" or line.startswith('#'):
		continue
        
            self.tableDef[table] = Bunch(line = line,
                                         tablename = table,
                                         hostname = parts[0].strip(),
                                         statusname = parts[1].strip(),
                                         tablesize = int(parts[3].strip()),
                                         key1 = parts[4].strip(),
                                         key2 = parts[5].strip(),
                                         keyS = parts[6].strip())

        in_f.close()

   
    # Read and parse the Gen2 status tables configuration.
    # Stores results in a dictionary indexed by table name.  The value
    # of each dictionary element is a Bunch.
    #
    def __read_tableDefv2(self, tblList):

	self.tableDef = {}

        for tup in tblList:
            table = tup[0].strip().upper()

            self.tableDef[table] = Bunch(tablename = table,
                                         hostname = tup[1].strip(),
                                         tablesize = tup[2])

   
    # Read and parse the SOSS StatusAlias.def file.  Stores results in a
    # dictionary indexed by alias name.  The value of each dictionary
    # element is a Bunch.
    #
    def __read_statusAliasDef(self, file):

        try:
            in_f = open(file, 'r')

        except IOError, e:
            raise statusInfoError("Cannot read status configuration data: %s" % str(e))

	self.statusAliasDef = {}

        # Hairy regex to match Table.def lines
        regex = re.compile(r'^\s*(?P<alias>[\w\.\-]+)\s*,\s*(?P<table>[\w]+)\s*\(\s*(?P<offset>\d+)\s*:\s*(?P<length>\d+)\s*:\s*(?P<stype>\w+)\s*:\s*(?P<mask>[\w\.]*)\s*\)\s*$')
        
        for line in in_f:
            line = line.strip()

            # Skip blank and comment lines
            if line == "" or line.startswith('#'):
		continue
        
	    match = regex.match(line)
            if not match:
                raise statusInfoError("Line doesn't match expected format:\n%s" % line)

            name = match.group('alias')
            table = match.group('table')

            # Look up the tableDef info for the table associated with this alias
            try:
                tabledef = self.tableDef[table]

            except KeyError, e:
#                raise statusInfoError("No tabledef info found for alias:\n%s" % line)
#                print "**WARNING** No tabledef info found for alias:\n%s" % line
                tabledef = None
                
            # Is there supplementary data for this StatusAlias?
            try:
                supp_data = statusAlias_SupplementaryData[name]

            except KeyError, e:
                supp_data = {}

            offset = int(match.group('offset'))
            length = int(match.group('length'))
            stype = match.group('stype')
            if not (stype in ['B', 'C', 'D', 'F', 'I', 'L', 'R', 'S']):
                raise statusInfoError("Odd type found for alias:\n%s" % line)

            # Final field is either a mask or a multiplier.  If it begins with 'H'
            # then it is a mask (value in hex); otherwise it is a multiplier.
            mask = match.group('mask')
            if len(mask) == 0:
                mask = None
                multiplier = None
            elif mask.startswith('H'):
                mask = eval('0x' + mask[1:] + 'L')
                multiplier = None
            else:
                multiplier = float(mask)
                mask = None
            
            self.statusAliasDef[name] = Bunch(line = line, 
                                              aliasname = name,
                                              tablename = table,
                                              tabledef = tabledef,
                                              offset = offset,
                                              length = length,
                                              stype = stype,
                                              mask = mask,
                                              multiplier = multiplier,
                                              supp_data = supp_data )

        in_f.close()


    def __buildRevIndex(self):
        self.table2aliases = {}

        for (alias, bnch) in self.statusAliasDef.items():
            tablename = bnch.tablename
            if not self.table2aliases.has_key(tablename):
                self.table2aliases[tablename] = []

            l = self.table2aliases[tablename]
            l.append(alias)
            
            
    # Read and parse the StatusTSCV.def file.  Stores results in a dictionary
    # indexed by table name.  The value of each dictionary element is a Bunch.
    #
    def __read_TSCVDef(self, file):

        try:
            in_f = open(file, 'r')

        except IOError, e:
            raise statusInfoError("Cannot read status configuration data: %s" % str(e))

	self.TSCVDef = {}

        linecnt = 0
        for line in in_f:
            linecnt += 1
            line = line.strip()
            # Skip blank and comment lines
            if line == "" or line.startswith('#'):
		continue
        
	    parts = line.split()
            if len(parts) < 4:
                raise statusInfoError("Error in StatusTSCV.def file, line %d" % linecnt)

            try:
                table = parts[0].strip()
                length = int(parts[1])
                offset = int(parts[2])
                comment = ' '.join(parts[3:])
            except (ValueError, IndexError), e:
                raise statusInfoError("Error in StatusTSCV.def file, line %d" % linecnt)

            self.TSCVDef[table] = Bunch(line = line,
                                        tablename = table,
                                        length = int(length),
                                        offset = int(offset),
                                        comment = comment)

        in_f.close()

   
    ####################################
    #    PUBLIC METHODS
    ####################################

        
    def get_tableDef(self, tablename):
        try:
            tabledef = self.tableDef[tablename]

        except KeyError, e:
            raise statusInfoError("No such table found: %s" % tablename)

        return tabledef


    def get_tables(self):
        return self.tableDef.keys()

    
    def get_aliasDef(self, aliasname):
        try:
            aliasdef = self.statusAliasDef[aliasname]

        except KeyError, e:
            raise statusInfoError("No such alias found: %s" % aliasname)

        if not aliasdef.tabledef:
            raise statusInfoError("No tabledef found for alias: %s" % aliasname)

        return aliasdef

        
    def get_aliases(self):
        return self.statusAliasDef.keys()

    
    def get_TSCVDef(self, tablename):
        try:
            tscvdef = self.TSCVDef[tablename]

        except KeyError, e:
            raise statusInfoError("No such table found: %s" % tablename)

        return tscvdef

        
    def aliasToTableDef(self, aliasname):

        aliasinfo = self.get_aliasDef(aliasname)

        tabledef = aliasinfo.tabledef
        if not tabledef:
            raise statusInfoError("No tabledef found for alias: %s" % aliasname)
        
        return tabledef


    # Takes a list of aliases and returns the list of tables containing
    # those aliases.
    #
    def aliasesToTables(self, aliasnames):

        res = []
        for aliasname in aliasnames:
            # Look up tabledef for this alias
            tabledef = self.aliasToTableDef(aliasname)
            if not tabledef.tablename in res:
                res.append(tabledef.tablename)

        return res

        
    # Takes a table name and returns the list of aliases used by that table.
    #
    def tableToAliases(self, tablename):

        try:
            return self.table2aliases[tablename]

        except KeyError:
            return []

    def getTableNames(self):
        """Return the list of all table names known to us."""

        return self.tableDef.keys()
        
    def getAliasNames(self):
        """Return the list of all status aliases known to us."""

        return self.statusAliasDef.keys()

        
class statusConverter(object):
    """Helper class used in converting values returned from SOSS status
    requests, particularly telescope status values.
    """

    
    def __init__(self):
        self.convIndex = {'B': self.conv_B,
                          'C': lambda c,ad: c.strip(),
                          'D': self.conv_D,
                          'F': self.conv_F,
                          'I': self.conv_I,
                          'L': self.conv_L,
                          'R': lambda r,ad: r,
                          'S': self.conv_S,
                          }

    # *** NOTE *** <string>:0: FutureWarning: hex/oct constants > sys.maxint will return
    #              positive values in Python 2.4 and up
    # Some say it's faster to use 'unpack' then the 'binascii.hexlify' trick
    # UPDATE: Yasu has added code to do unpacking (see below).
    #
    def applyMask(self, val, mask):
        val = eval('0x' + binascii.hexlify(val))
        if mask:
            return val & mask
        return val

    def unpackData(self, data, signed):
        """
        Decode arbitrary length byte buffer (python string) into integer type.
        The conversion is done by padding 0's to the left and unpacking the 
        buffer assuming appropriate number type.
        
        TODO: this function will return the wrong value if the number is 
        signed and the length is not one of 1, 2, 4 or 8.
        It is not likely that the status uses two's compliment
        for the 3,5,6 or 7 bytes integer, though.
        """
        fmtStrings = [(1, '',             ('!b', '!B')),
                      (2, '\x00',         ('!h', '!H')),
                      (4, '\x00',         ('!l', '!L')),
                      (8, '\x00\x00\x00', ('!q', '!Q')),
                      #(16, '\x00\x00\x00\x00\x00\x00\x00\x00', ('!q', '!Q')),
                      ]
        length = len(data)

        # Linear search. any better way to handle this?
        for aStr in fmtStrings:
            if length <= aStr[0]:
                pad = aStr[1]
                if signed:
                    fmt = aStr[2][0]
                else:
                    fmt = aStr[2][1]
                val = struct.unpack(fmt, (pad + data)[-aStr[0]:])[0]
                return val
            
        raise statusConversionError('length of the data exceeds that of all possible data types')

    # Unsigned binary bit field
    def conv_B(self, val_B, aliasdef):
        #logger.debug('in conv_B() function; the input value is 0x%s'%(binascii.hexlify(val_B)))
        if aliasdef.length > 8:      # too long for struct.unpack!
            # TODO: this is slow...can we improve it?
            val = 0
            for i in xrange(aliasdef.length):
                val = (256 * val) + struct.unpack('!h','\x00'+val_B[i])[0]
        else:
            val = self.unpackData(val_B, False)

        if aliasdef.mask is not None:
            return long(val) & long(aliasdef.mask)
        else:
            return val

    # BCD conversion
    def conv_D(self, val_D, aliasdef):
        #The BCD type may have mask specified
        orig_len = len(val_D)
        val = self.unpackData(val_D, False)
        if aliasdef.mask is not None:
            val = long(val) & long(aliasdef.mask)
        digits = binascii.hexlify(struct.pack('!Q', val))
        digits = digits[-(orig_len * 2):]
        # TODO: This is true only for the BCD of length >=6 bytes
        if digits.startswith('8'):
            val = -float(digits[1:4] + '.' + digits[4:])
        else:
            val = float(digits[1:4] + '.' + digits[4:])
#        print "D value is %f" % val
        return val

    # ascii float
    def conv_F(self, val_F, aliasdef):
        val = val_F.strip()
        if len(val) > 0:
            return float(val)
        # empty string-- return null??
        return None

    # ascii integer
    def conv_I(self, val_I, aliasdef):
        val = val_I.strip()
        if len(val) > 0:
            return int(val)
        # empty string-- return null??
        return None

    # Unsigned binary float.
    # This is actually a 2- or 4-byte integer value with a floating point multiplier.
    def conv_L(self, val_L, aliasdef):
        val = self.unpackData(val_L, False)
        val = float(val)
        if aliasdef.multiplier:
            return val * aliasdef.multiplier
        return val

    # Signed binary float
    # This is actually a 2- or 4-byte integer value with a floating
    # point multiplier.  Will not be able to convert signed numbers if
    # the length of the data is anything other than 1, 2, 4 or 8
    # bytes.
    def conv_S(self, val_S, aliasdef):
        if len(val_S) not in [1, 2, 4, 8]:
            raise statusConversionError('Length of data not amenable to signed conversion')
        
        val = self.unpackData(val_S, True)
        val = float(val)
        if aliasdef.multiplier:
            return val * aliasdef.multiplier
        return val
    

    ####################################
    #    PUBLIC METHODS
    ####################################

    # Given a alias value and the corresponding aliasDef object, return the
    # value converted to a convenient Python data type.
    #
    def convert(self, value, aliasdef):

        # Do we have an override of the type from our StatusAlias
        # supplementary data?
        try:
            stype = aliasdef.supp_data['type']

        except KeyError, e:
            stype = aliasdef.stype

        # Do we have an override of the conversion function from our
        # StatusAlias supplementary data?
        try:
            convfunc = aliasdef.supp_data['conv']

        except KeyError, e:
            convfunc = self.convIndex[stype]

        # Apply the necessary conversion.
        try:
            newval = convfunc(value, aliasdef)

        except (IndexError, ValueError), e:
            raise statusConversionError(str(e))

        except struct.error, e:
            raise statusConversionError(str(e))

        except Exception, e:
            raise statusConversionError(str(e))

        return newval
        
    
# END Convert.py

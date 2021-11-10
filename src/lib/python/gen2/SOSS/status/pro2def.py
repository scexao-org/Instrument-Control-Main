#! /usr/bin/env python
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Feb  2 12:42:44 HST 2009
#]
#
#
"""
This program is used to generate *.def files from *.pro files for the SOSS
and Gen2 status systems.

Typical usage:

    $ ./pro2def.py --in=StatusAlias.pro --out=StatusAlias.def

If you need to regenerate the StatusTSCV.def file, you can do so by:

    $ ./pro2def.py --tscv --out=StatusTSCV.def

After creating a new *.def file, please copy it to all SOSS hosts in the
directory /app/OSS/GLOBAL_DEBUG/OSS_SYSTEM  (aka $OSS_SYSTEM)
"""
import sys, os, re, time
import Bunch

# Raised for errors 
class statusInfoError(Exception):
    pass


TSC_rpc_header_size = 19

#####################################################
# Offsets for TSCS subtables
#####################################################
_TSCS_subtables = [
    # subtable name        # offset
    ('TSCS_DRDR',          33+1),
    ('TSCS_MTDR',          33+1+19+18),
    ('TSCS_FRAD',          33+1+19+18+19+60),
    ('TSCS_TSC',           33+1+19+18+19+60+19+13),
    ('TSCS_FRADPF',        33+1+19+18+19+60+19+13+19+150),
    ('TSCS_TTCU',          33+1+19+18+19+60+19+13+19+150+19+13),
    ('TSCS_MLP1',          33+1+19+18+19+60+19+13+19+150+19+13+19+60+(118-118)),
    ]

def get_TSCS_offsets():
    """Generate TSCS subtable offsets.  Creates a Bunch, indexed by table
    name, where each entry is another Bunch containing the subtable name
    and offset.
    """

    res = Bunch.Bunch()
    
    for tup in _TSCS_subtables:
        res[tup[0]] = Bunch.Bunch(name=tup[0], table='TSCS',
                                  offset=tup[1]+TSC_rpc_header_size-1)

    return res

# Static list of these offsets
_TSCS_offsets = get_TSCS_offsets()

#####################################################
# Offsets for TSCL subtables
#####################################################
## l_ts = 1292
## TSCL_tables = [
##     # table name    start
##     ('L1',          0*l_ts,    ""         ),
##     ('L2',          1*l_ts,    ""         ),
##     ('L3',          2*l_ts,    ""         ),
##     ('L4',          3*l_ts,    ""         ),
##     ('L5',          4*l_ts,    ""         ),
##     ('L6',          5*l_ts,    ""         ),
##     ('L7',          6*l_ts,    ""         ),
##     ]

_TSCL_subtables = [
    # subtable name        # offset
    # L1
    ('TSCL_TSC',           33+2+1292*0),
    ('TSCL_MLP1',          33+2+1292*0+19+260),
    ('TSCL_DRDR',          33+2+1292*0+19+260+19+170),
    ('TSCL_MTDR',          33+2+1292*0+19+260+19+170+19+84),
    ('TSCL_FRAD',          33+2+1292*0+19+260+19+170+19+84+19+264),
    ('TSCL_AG',            33+2+1292*0+19+260+19+170+19+84+19+264+19+108),
    ('TSCL_SV',            33+2+1292*0+19+260+19+170+19+84+19+264+19+108+19+86),
    ('TSCL_CLOCK',         33+2+1292*0+19+260+19+170+19+84+19+264+19+108+19+86+19+64),
    # L2
    ('TSCL_MLP2',          33+2+1292*1),
    # L3
    ('TSCL_MLP2_L3',       33+2+1292*2),
    ('TSCL_SH',            33+2+1292*2+19+1100),
    ('TSCL_RED_EXH',       33+2+1292*2+19+1100+19+7),
    # L4
    ('TSCL_SMCU',          33+2+1292*3),
    ('TSCL_MLP3',          33+2+1292*3+19+198),
    ('TSCL_TLSCP_TEMP',    33+2+1292*3+19+198+19+192),
    ('TSCL_TLSCP_CT2',     33+2+1292*3+19+198+19+192+19+540),
    ('TSCL_HEAT_EXH',      33+2+1292*3+19+198+19+192+19+540+19+132),
    # L5
    ('TSCL_THRM',          33+2+1292*4),
    ('TSCL_DOME_TEMP',     33+2+1292*4+19+222),
    ('TSCL_DOME_CT2',      33+2+1292*4+19+222+19+480),
    ('TSCL_AO',            33+2+1292*4+19+222+19+480+19+192),
    ('TSCL_OBE',           33+2+1292*4+19+222+19+480+19+192+19+26),
    ('TSCL_CIAX',          33+2+1292*4+19+222+19+480+19+192+19+26+19+26),
    # L6
    ('TSCL_WMON',          33+2+1292*5),
    ('TSCL_HSBC',          33+2+1292*5+19+48),
    ('TSCL_HT_EXH',        33+2+1292*5+19+48+19+18),
    ('TSCL_BOLT',          33+2+1292*5+19+48+19+18+19+72),
    ('TSCL_CAL',           33+2+1292*5+19+48+19+18+19+72+19+120),
    ('TSCL_MCP2',          33+2+1292*5+19+48+19+18+19+72+19+120+19+60),
    ('TSCL_TTCU',          33+2+1292*5+19+48+19+18+19+72+19+120+19+60+19+111),
    ('TSCL_FRCU',          33+2+1292*5+19+48+19+18+19+72+19+120+19+60+19+111+19+24),
    ('TSCL_ASCU',          33+2+1292*5+19+48+19+18+19+72+19+120+19+60+19+111+19+24+19+90),
    ('TSCL_DOMEFLAT',      33+2+1292*5+19+48+19+18+19+72+19+120+19+60+19+111+19+24+19+90+19+156),
    ('TSCL_FPCI',          33+2+1292*5+19+48+19+18+19+72+19+120+19+60+19+111+19+24+19+90+19+156+19+192),
    # L7
    ('TSCL_OBCP',          33+2+1292*6),
    ('TSCL_BLCU',          33+2+1292*6+19+236),
    ('TSCL_HSCSCAG',       33+2+1292*6+19+236+19+72),
    ('TSCL_HSCSHAG',       33+2+1292*6+19+236+19+72+19+80),
    ('TSCL_HSCSH',         33+2+1292*6+19+236+19+72+19+80+19+80),
    ]

def get_TSCL_offsets():
    """Generate TSCL subtable offsets.  Creates a Bunch, indexed by table
    name, where each entry is another Bunch containing the subtable name
    and offset.
    """

    res = Bunch.Bunch()
    
    for tup in _TSCL_subtables:
        res[tup[0]] = Bunch.Bunch(name=tup[0], table='TSCL',
                                  offset=tup[1]+TSC_rpc_header_size-1)

    return res

# Static list of these offsets
_TSCL_offsets = get_TSCL_offsets()

#####################################################
# Offsets for TSCV subtables
#####################################################
_TSCV_tables = [
    # table name  offset   size,  comment
    ('TSCV00A1',   1000,   1557,  "TSC"         ),
    ('TSCV00B1',   3000,    175,  "MLP1"        ),
    ('TSCV0001',   4000,     49,  "DRDR"        ),
    ('TSCV0002',   5000,    240,  "MTDR"        ),
    ('TSCV0004',   6000,     42,  "FRAD"        ),
    ('TSCV0006',   7000,    120,  "AG"          ),
    ('TSCV0007',   8000,    162,  "SV"          ),
    ('TSCV0030',   9000,     78,  "THRM"        ),
    ('TSCV000D',  10000,     30,  "FPCI"        ),
    ('TSCV0027',  11000,     54,  'BLCU'        ),
    ('TSCV0008',  12000,     10,  "AO"          ),
    ('TSCV0051',  13000,     10,  "OBE"         ),
    ('TSCV002E',  14000,      1,  "CLOCK"       ),
    ('TSCV00B2',  15000,   1100,  "MLP2"        ),
    ('TSCV0009',  17000,    100,  "SH"          ),
    ('TSCV0003',  18000,     96,  "SMCU"        ),
    ('TSCV00B3',  19000,     74,  "MLP3"        ),
    ('TSCV0024',  20000,     96,  "CVCU"        ),
    ('TSCV0025',  21000,     36,  "TMCU"        ),
    ('TSCV002A',  22000,    160,  "DOME TEMP"   ),
    ('TSCV002B',  23000,     64,  "DOME CT2"    ),
    ("TSCV002C",  24000,    180,  'TLSCP TEMP'  ),
    ('TSCV002D',  25000,     44,  "TLSCP CT2"   ),
    ('TSCV0029',  26000,      6,  "HSBC"        ),
    ('TSCV000E',  27000,     76,  "CAL"         ),
    ('TSCV000A',  28000,     11,  "MIRROR HT EXE"),
    ('TSCV0031',  29000,     10,  "HT EXE"      ),
    ('TSCV000B',  30000,     50,  "MCP1"        ),
    ('TSCV0010',  32000,     33,  "MCP2"        ),
    ('TSCV0032',  33000,     33,  "BOLT"        ),
    ('TSCV0033',  34000,     53,  "SPU4"        ),
    ('TSCV0034',  35000,     23,  "SPU5"        ),
    ('TSCV0035',  36000,     22,  "SPU6"        ),
    ('TSCV0028',  37000,     53,  "TTCU"        ),
    ('TSCV0036',  38000,     40,  "FRAD(PF)"    ),
    ('TSCV0037',  39000,     31,  "ASCU(PF)"    ),
    ('TSCV0061',  40000,     27,  "DOME FLAT"   ),
    ('TSCV0040',  41000,   1000,  "SH TEST"     ),
    ('TSCV0038',  42000,      9,  "HEAT EXH"    ),
    ('TSCV0039',  43000,     25,  "RED EXH"     ),
    ('TSCV003A',  44000,     68,  "CIAX"        ),
    ('TSCV003B',  45000,    192,  "OBCP(FMOS)"  ),
    ('TSCV003C',  46000,     35,  "HYDRST EXH"  ),
    ('TSCV003D',  47000,    100,  "HSCSCAG"     ),
    ('TSCV003E',  48000,    100,  "HSCSHAG"     ),
    ('TSCV003F',  49000,     84,  "HSCSH"       ),
    ]

_CIAX_tables = [
    (r'08[6][1-3]',    4,  "PMA/PMFXS" ), 
    (r'0860',          2,  "PMFXS-3"   ),
    (r'0859',          2,  "PMFXS-2"   ),
    (r'0858',          2,  "PMFXS-1"   ),
    (r'08[5][0-1]',    4,  "PMA/PMFXS" ),
    (r'08[0-4][0-9]',  4,  "PMA/PMFXS" ),
    (r'07[4][0-8]',    4,  "PMA/PMFXS" ),
    (r'07[0-3][0-9]',  4,  "PMA/PMFXS" ),
    (r'06[4][0-2]',    4,  "PMA/PMFXS" ),
    (r'06[0-3][0-9]',  4,  "PMA/PMFXS" ),
    (r'05[3][0-6]',    4,  "PMA/PMFXS" ),
    (r'05[0-2][0-9]',  4,  "PMA/PMFXS" ),
    (r'04[3][0]',      4,  "PMA/PMFXS" ),
    (r'04[0-2][0-9]',  4,  "PMA/PMFXS" ),
    (r'03[2][0-4]',    4,  "PMA/PMFXS" ),
    (r'03[0-1][0-9]',  4,  "PMA/PMFXS" ),
    (r'02[1][0-8]',    4,  "PMA/PMFXS" ),
    (r'02[0][0-9]',    4,  "PMA/PMFXS" ),
    (r'01[1][0-2]',    4,  "PMA/PMFXS" ),
    (r'01[0][0-9]',    4,  "PMA/PMFXS" ),
    ]

def get_TSCV():
    """Generate TSCV subtable offsets.  Creates a Bunch, indexed by table
    name, where each entry is another Bunch containing the subtable name,
    table length, total length (inc RPC header), and offset.
    """

    tscv = Bunch.Bunch()
    
    for tup in _TSCV_tables:
        tscv[tup[0]] = Bunch.Bunch(name=tup[0], tbllen=tup[2],
                                   totlen=tup[2]+TSC_rpc_header_size,
                                   offset=tup[1], comment=tup[3])

    # Write CIAX offsets
    LIST1 = [n for n in xrange(1, 9)]
    LIST2 = [n for n in xrange(1, 65)]

    for AA1 in LIST1:
        for AA2 in LIST2:
            AAA = "%02d%02d" % (AA1, AA2)
            BBBBB = "1%1d%02d00" % (AA1, AA2)

            for tup in _CIAX_tables:
                if re.match(tup[0], AAA):
                    subtable = "TSCV%4.4s" % AAA
                    tscv[subtable] = Bunch.Bunch(name=subtable,
                                                 tbllen=tup[1],
                                                 totlen=tup[1]+TSC_rpc_header_size,
                                                 offset=int(BBBBB), comment=tup[2])

    return tscv

def get_TSCV_offsets():
    """Another view of TSCV subtable offsets, compatible with the views
    for TSCL and TSCS.
    """

    res = Bunch.Bunch()
    
    for bnch in get_TSCV().values():
        res[bnch.name] = Bunch.Bunch(name=bnch.name, table='TSCV',
                                     offset=bnch.offset+TSC_rpc_header_size-1)

    return res

# Static list of these offsets
_TSCV_offsets = get_TSCV_offsets()

#####################################################
# Offsets for SOSS subtables
#####################################################
_SOSS_subtables = [
    ('CON_SCH_DISP',                 40*(76)),
    ]

def get_SOSS_offsets():
    """Generate SOSS subtable offsets.  Creates a Bunch, indexed by table
    name, where each entry is another Bunch containing the subtable name
    and offset.
    """

    res = Bunch.Bunch()
    
    for tup in _SOSS_subtables:
        res[tup[0]] = Bunch.Bunch(name=tup[0], table=None,
                                  offset=tup[1])

    return res

# Static list of these offsets
_SOSS_offsets = get_SOSS_offsets()

#####################################################
# Offsets for *ALL* subtables
#####################################################
_all_offsets = Bunch.Bunch()
_all_offsets.update(_TSCS_offsets)
_all_offsets.update(_TSCL_offsets)
_all_offsets.update(_TSCV_offsets)
_all_offsets.update(_SOSS_offsets)

# _all_offsets should now have every subtable and its offset

# Regex matching StatusAlias.pro status alias definition lines
line_regex = re.compile(r'^([\w_\.\-]+)\s*,([\w_\.]+)\s*\(\s*([$\w\+\-\*\s]+:\d+:\w:?[\w\.]*)\s*\)\s*.*$')

# Regex matching StatusAlias.pro offset/type/mask specification
spec_regex = re.compile(r'^([$\w\+\-\*\s]+):(\d+):(\w):?([\w\.]*)$')


def error(msg, exitcode=None):
    """Report an error to stderr, if exitcode is not None, it should be
    an integer used to exit the program with an exit code.
    """
    sys.stderr.write(msg + '\n')
    sys.stderr.flush()

    if exitcode != None:
        sys.exit(exitcode)
        

def calc_offset(offset_exp, offset_tables):
    """Given an offset expression, like '$TSCV_MLP1+34-1', evaluate it
    and return the integer offset.  offset_tables is a list of bunches
    of subtables (e.g. _all_offsets) to search for referenced subtables.
    """

    # introduce delineating whitespace into expression
    exp = offset_exp.replace('+', ' + ')
    exp = exp.replace('-', ' - ')
    exp = exp.replace('*', ' * ')

    explist = exp.split()
    newlist = []
    for tok in explist:
        if not tok.startswith('$'):
            # python evaluator doesn't like leading zeros
            tok = tok.lstrip('0')
            if tok == '':
                tok = '0'
            newlist.append(tok)
            continue

        tableName = tok[1:]
        bnch = None
        for table in offset_tables:
            if table.has_key(tableName):
                bnch = table[tableName]

        if not bnch:
            raise statusInfoError("Table '%s' is not defined!" % tableName)

        newlist.append(str(bnch.offset))

    try:
        new_offset_exp = ' '.join(newlist)
        offset = eval(new_offset_exp)
    except Exception, e:
        print "Offset expression is '%s'" % new_offset_exp
        raise statusInfoError("Bad expression '%s': %s" % (offset_exp, str(e)))
    
    return offset
    
    
def read_dotPro(filename):
    """Read a *.pro file 'filename'.  If filename is '-', the input is read
    from stdin.  The result is a Bunch of Bunches.  The top-level bunch is
    indexed by alias names, for each alias, the sub-bunch contains the alias
    name, associated table (not subtable), offset, length, type and mask.

    See the document 'StatusAliasTypes.txt' for details about these
    attributes.
    """

    if filename != '-':
        in_f = open(filename, 'r')
    else:
        in_f = sys.stdin

    # Locally defined offsets
    offsets = Bunch.Bunch()

    # holds result
    aliases = Bunch.Bunch()
    
    lineno = 0
    for orgline in in_f:
        lineno += 1
        line = orgline.strip()

        # Skip comments and blank lines
        if (len(line) == 0) or line.startswith('#'):
            continue

        if line.startswith('@'):
            # Line defines an offset into a table
            res = line[1:].split()
            if len(res) != 2:
                raise statusInfoError("Error in offset definition line %d:\n%s" % (
                    lineno, orgline))

            # create "local" definition of this offset.  Local definition
            # usually shadows the definitions defined in this file.
            (subtable, offset_exp) = res
            try:
                offset = calc_offset(offset_exp, (_all_offsets, offsets))

            except statusInfoError, e:
                raise statusInfoError("Error in offset definition line %d: %s\n%s" % (
                    lineno, str(e), orgline))

            # Note: we don't know which table this offset is for, but put
            # it in the local defintions table
            offsets[subtable] = Bunch.Bunch(name=subtable, table=None,
                                            offset=offset)
            continue

        # Line should be a normal alias defintion line
        match = line_regex.match(line)
        if not match:
            raise statusInfoError("Unrecognized format at line %d:\n%s" % (
                lineno, orgline))
        
        alias = match.group(1)
        table = match.group(2)
        spec = match.group(3)

        # Decode spec (n: m: T) or (n: m: T: M)
        match = spec_regex.match(spec)
        if not match:
            raise statusInfoError("Error in status alias definition line %d (spec=%s):\n%s" % (
                lineno, spec, orgline))

        res = match.groups()
        length = len(res)
        if length == 3:
            (offset_exp, length, sttype) = res
            mask = None
        elif length == 4: 
            (offset_exp, length, sttype, mask) = res
        else:
            raise statusInfoError("Error in status alias definition line %d (spec=%s):\n%s" % (
                lineno, spec, orgline))

        length = int(length)

        # calculate offset from expression
        try:
            offset = calc_offset(offset_exp, (_all_offsets, offsets))

        except statusInfoError, e:
            raise statusInfoError("Error in alias definition line %d: %s\n%s" % (
                lineno, str(e), orgline))

        aliases[alias] = Bunch.Bunch(alias=alias, table=table, offset=offset,
                                     length=length, sttype=sttype, mask=mask)
        #print "alias=%s table=%s offset=%d length=%d type=%s mask=%s" % (
        #    alias, table, offset, length, sttype, mask)
            
    if filename != '-':
        in_f.close()

    return aliases


#####################################################
# Convert a *.pro file to a *.def file
#####################################################
def pro2def(infilename, outfilename):
    """infilename is a *.pro file and outfile name should refer to a
    non-existent *.def path.  *.def aliases are written in sorted order.
    """

    # Open input file
    if infilename != '-':
        if not os.path.exists(infilename):
            error("'%s' does not exist!" % infilename, exitcode=1)

    # Parse StatusAlias.pro
    aliases_res = read_dotPro(infilename)

    # Open output file
    if outfilename == '-':
        out_f = sys.stdout

    else:
        if os.path.exists(outfilename):
            raise OSError("File exists: '%s'" % outfilename)

        try:
            out_f = open(outfilename, 'w')

        except IOError, e:
            error("Cannot open output file '%s': %s" % (outfilename, str(e)),
                  exitcode=1)

    # Sort aliases by name
    aliases = aliases_res.values()
    aliases.sort(lambda x, y: cmp(x.alias, y.alias))
    
    out_f.write("#    create date    : %s\n" % (time.ctime()))
    out_f.write("#    create program : pro2def.py\n")
    out_f.write("#\n")

    for bnch in aliases:
        out_f.write("%(alias)s,%(table)s(%(offset)d:%(length)d:%(sttype)s:%(mask)s)\n" % bnch)
        
    if outfilename != '-':
        out_f.close()


#####################################################
# make a StatusTSCV.def file
# This file (StatusTSCV.def) is an intermediate file for use in converting
# *.pro files into *.def files by the old Fujitsu scripts.  However, this
# file may be read by the telescope status interface files in SOSS, and
# is also used in Gen2.
#####################################################

def make_StatusTSCVDotDef(outfilename):
    """Make a StatusTSCV.def file.  outfilename should refer to a non-existent
    path to the file spec of the output, usually ending in .../StatusTSCV.def
    """
    # Open output file
    if outfilename == '-':
        out_f = sys.stdout

    else:
        if os.path.exists(outfilename):
            raise OSError("File exists: '%s'" % outfilename)

        try:
            out_f = open(outfilename, 'w')

        except IOError, e:
            error("Cannot open output file '%s': %s" % (outfilename, str(e)),
                  exitcode=1)

    tscv = get_TSCV()

    tables = tscv.values()
    # Sort by offset
    tables.sort(lambda x, y: cmp(x.offset, y.offset))
    
    out_f.write("#    create date    : %s\n" % (time.ctime()))
    out_f.write("#    create program : pro2def.py\n")
    out_f.write("#\n")

    # Write TSCV offsets
    out_f.write("# TSCV status offset define table\n")
    out_f.write("#\n")
    out_f.write("#\n")
    out_f.write("#table_code         length    offset    comment                <CR>\n")
    out_f.write("#---+----1----+----2----+----3----+----4----+----5----+----6---<CR>\n")
    for bnch in tables:
        out_f.write("%-8.8s            %05d     %06d    %s\n" % (bnch.name,
                                                                 bnch.totlen,
                                                                 bnch.offset,
                                                                 bnch.comment))
    out_f.write("#\n")

    if outfilename != '-':
        out_f.close()


def main(options, args):

    if options.tscv:
        make_StatusTSCVDotDef(options.outfile)

    else:
        pro2def(options.infile, options.outfile)

    sys.exit(0)
        

if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options] command [args]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--in", dest="infile", metavar='FILE',
                      default='StatusAlias.pro',
                      help="Use FILE as *.pro input file (use '-' for stdin)")
    optprs.add_option("--out", dest="outfile", metavar='FILE',
                      default='-',
                      help="Use FILE as output file (use '-' for stdout)")
    optprs.add_option("--tscv", dest="tscv", action="store_true",
                      default=False,
                      help="Make a StatusTSCV.def file")

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

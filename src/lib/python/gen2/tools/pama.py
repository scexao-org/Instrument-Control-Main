#!/usr/bin/env python
#
# loadpama.py -- Load PA/MA settings from a table.
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Apr 19 12:10:21 HST 2010
#]
import sys
import yaml
import Bunch
import ssdlog

# example tables at http://siroan.subaru.nao.ac.jp/w/PaMa.html
#
example_csv = """
POpt,OK,,EngObs100217,EngObs061116 EngObs080601,EngObs061116,0,0,6.9,1.5,0,-,-
Cs(CsOpt),OK,None in S08A,EngObs061027 EngObs080511 32PA,EngObs061027 EngObs080511,EngObs080511 (eye),3.9784,3.2874,-0.12,5.7086,-5.1212,0,0
Cs(CsOpt)+ADC,Image acceptable but better do Offset SH,,EngObs070409,EngObs070729 EngObs080511,EngObs070729,3.9784,5.1874,-0.1,6.8910,-5.1212,0,0
NsOpt(CsOpt),OK,,EngObs061028,EngObs061027,,0,0,0,0,0,0,0
NsOpt(CsOpt)+ADC,OK,,EngObs061028,EngObs061027,,0,0,NA,0,0,0,0
NsOpt(CsOpt)+ImR(B),OK,,EngObs061028 1PA EngObs070727 32PA,EngObs070728,,0.5,0,NA,0,-0.31115,0,0
NsOpt(CsOpt)+ImR(B)+ADC,OK,,EngObs070727,EngObs070728,,0,-1,-0.1,-0.622295,0,0,0
NsOpt(CsOpt)+ImR(R)+ADC,OK,,EngObs070727,EngObs070728,,0,0,-0.1,0,0,0,0
NsOpt(CsOpt)+ImR(R),,Backup,EngObs061028 1PA EngObs070727,EngObs080511,,0,0,-0.1,0,0,0,0
NsIR(CsOpt)+ImR,PA needed after ImR reacoat,,EngObs070728,EngObs070917,eye*6,0,0,-0.23,0,0,0,0
NsIR(CsOpt),,Backup,EngObs070728,,,0.5,-0.5,-0.1,-0.311142,-0.311142,0,0
NsOpt(NsOpt),OK,,EngObs061207,EngObs061207,eye,-0.8,-0.4,0,0,0,0,0
NsOpt(NsOpt)+ADC,OK,,EngObs070124,EngObs070124,eye,-1.2,-0.8,0,0,0,0,0
NsOpt(NsOpt)+ImR(B),*1 EngObs080706,080429,EngObs070129,EngObs070129*1,eye,-1.2,-0.8,-0.24,0,0,0,0
NsOpt(NsOpt)+ImR(B)+ADC,OK,,EngObs070129,EngObs070129,eye,-1.2,-0.8,0,0,0,0,0
NsOpt(NsOpt)+ImR(R)+ADC,OK,,EngObs070130,EngObs070130,eye,-1.2,-0.8,0,0,0,0,0
NsOpt(NsOpt)+ImR(R),,,Night of 2008-08-18 HST 32PA,,EngObs080613 (eyes),-2,-1.3,0,-0.76038,1.16981,0,0
NsIR(NsOpt)+ImR,EngObs080615 - PA needed after ImR reacoat,,EngObs070905,EngObs070905,eye,-1.2,-0.3,-0.1,0.29245,0,0,0
NsIR(NsOpt),with AO offset,,EngObs090710,EngObs070905,eye,-2.5,-1,0,-0.58491,1.46227,0,0
Cs(IR),OK,,Night of 2008-06-24 HST 32PA,EngObs080903,EngObs070708,2.791055,1.367355,-0.06,-0.7330,-1.6508,0,0
NsOpt(IR)+ADC,OK,Backup,EngObs070627 32PA EngObs080521 5PA,EngObs070627*2 EngObs080521,eye EngObs070926,-1.0,-1.7,NA,-1.05710,0.62230,0,0
NsOpt(IR),OK,,EngObs070726,EngObs070725,eye,-1,-2,0,-1.24459,0.62230,0,0
NsOpt(IR)+ImR(R)+ADC,OK,Backup,EngObs070926 5PA EngObs080521 32PA,EngObs080521,eye EngObs070926,-1.0,-1.7,0.07,-1.05710,0.62230,0,0
NsOpt(IR)+ImR(B)+ADC,OK,,EngObs070726,EngObs070626,eye,-1.5,-2,0,-1.24459,0.93344,0,0
NsOpt(IR)+ImR(B),,Backup,EngObs070927 4PA,,eye EngObs080711,-1.4,-3.0,0,-1.86689,0.87121,0,0
NsOpt(IR)+ImR(R),,Backup,EngObs070927 3PA EngObs080521 5PA,EngObs080521,eye EngObs070927,-1,-2.5,0,-1.555739,0.622295,0,0
NsIR(IR)+ImR,Need MA before 2008-10-07 for AO,,Night of 2008-09-12 HST 32PA,EngObs080523,EngObs061106,-1.188121,0.001820,-0.12,0.90612,2.08125,0,0
NsIR(IR),AO offset!,,NA,EngObs070801,EngObs070801,3.791055,0.867355,0,1.31777,-5.08270,0,0
NsIR(IR+AO),Need MA before 2008-10-07,,EngObs090709,Uses NsIR(IR)+ImR,Uses NsIR(IR)+ImR,-1.188121,0.001820,NA,0.90612,2.08125,0,0
"""

example_yaml = """
cs(csopt): {ma: EngObs061027 EngObs080511, name: Cs(CsOpt), pa: EngObs061027 EngObs080511
    32PA, sh: EngObs080511 (eye), tx: 5.7085999999999997, ty: -5.1212, u: 0.0, usable: OK,
  use: None in S08A, v: 0.0, x: 3.9784000000000002, y: 3.2873999999999999, z: -0.12}
cs(csopt)+adc: {ma: EngObs070729 EngObs080511, name: Cs(CsOpt)+ADC, pa: EngObs070409,
  sh: EngObs070729, tx: 6.891, ty: -5.1212, u: 0.0, usable: Image acceptable but better
    do Offset SH, use: '', v: 0.0, x: 3.9784000000000002, y: 5.1874000000000002, z: -0.10000000000000001}
cs(ir): {ma: EngObs080903, name: Cs(IR), pa: Night of 2008-06-24 HST 32PA, sh: EngObs070708,
  tx: -0.73299999999999998, ty: -1.6508, u: 0.0, usable: OK, use: '', v: 0.0, x: 2.7910550000000001,
  y: 1.3673550000000001, z: -0.059999999999999998}
nsir(csopt): {ma: '', name: NsIR(CsOpt), pa: EngObs070728, sh: '', tx: -0.31114199999999997,
  ty: -0.31114199999999997, u: 0.0, usable: '', use: Backup, v: 0.0, x: 0.5, y: -0.5,
  z: -0.10000000000000001}
nsir(csopt)+imr: {ma: EngObs070917, name: NsIR(CsOpt)+ImR, pa: EngObs070728, sh: eye*6,
  tx: 0.0, ty: 0.0, u: 0.0, usable: PA needed after ImR reacoat, use: '', v: 0.0,
  x: 0.0, y: 0.0, z: -0.23000000000000001}
nsir(ir): {ma: EngObs070801, name: NsIR(IR), pa: NA, sh: EngObs070801, tx: 1.3177700000000001,
  ty: -5.0827, u: 0.0, usable: AO offset!, use: '', v: 0.0, x: 3.7910550000000001,
  y: 0.86735499999999999, z: 0.0}
nsir(ir)+imr: {ma: EngObs080523, name: NsIR(IR)+ImR, pa: Night of 2008-09-12 HST 32PA,
  sh: EngObs061106, tx: 0.90612000000000004, ty: 2.0812499999999998, u: 0.0, usable: Need
    MA before 2008-10-07 for AO, use: '', v: 0.0, x: -1.188121, y: 0.00182, z: -0.12}
nsir(ir+ao): {ma: Uses NsIR(IR)+ImR, name: NsIR(IR+AO), pa: EngObs090709, sh: Uses
    NsIR(IR)+ImR, tx: 0.90612000000000004, ty: 2.0812499999999998, u: 0.0, usable: Need
    MA before 2008-10-07, use: '', v: 0.0, x: -1.188121, y: 0.00182, z: NA}
nsir(nsopt): {ma: EngObs070905, name: NsIR(NsOpt), pa: EngObs090710, sh: eye, tx: -0.58491000000000004,
  ty: 1.46227, u: 0.0, usable: with AO offset, use: '', v: 0.0, x: -2.5, y: -1.0,
  z: 0.0}
nsir(nsopt)+imr: {ma: EngObs070905, name: NsIR(NsOpt)+ImR, pa: EngObs070905, sh: eye,
  tx: 0.29244999999999999, ty: 0.0, u: 0.0, usable: EngObs080615 - PA needed after
    ImR reacoat, use: '', v: 0.0, x: -1.2, y: -0.29999999999999999, z: -0.10000000000000001}
nsopt(csopt): {ma: EngObs061027, name: NsOpt(CsOpt), pa: EngObs061028, sh: '', tx: 0.0,
  ty: 0.0, u: 0.0, usable: OK, use: '', v: 0.0, x: 0.0, y: 0.0, z: 0.0}
nsopt(csopt)+adc: {ma: EngObs061027, name: NsOpt(CsOpt)+ADC, pa: EngObs061028, sh: '',
  tx: 0.0, ty: 0.0, u: 0.0, usable: OK, use: '', v: 0.0, x: 0.0, y: 0.0, z: NA}
nsopt(csopt)+imr(b): {ma: EngObs070728, name: NsOpt(CsOpt)+ImR(B), pa: EngObs061028
    1PA EngObs070727 32PA, sh: '', tx: 0.0, ty: -0.31114999999999998, u: 0.0, usable: OK,
  use: '', v: 0.0, x: 0.5, y: 0.0, z: NA}
nsopt(csopt)+imr(b)+adc: {ma: EngObs070728, name: NsOpt(CsOpt)+ImR(B)+ADC, pa: EngObs070727,
  sh: '', tx: -0.62229500000000004, ty: 0.0, u: 0.0, usable: OK, use: '', v: 0.0,
  x: 0.0, y: -1.0, z: -0.10000000000000001}
nsopt(csopt)+imr(r): {ma: EngObs080511, name: NsOpt(CsOpt)+ImR(R), pa: EngObs061028
    1PA EngObs070727, sh: '', tx: 0.0, ty: 0.0, u: 0.0, usable: '', use: Backup, v: 0.0,
  x: 0.0, y: 0.0, z: -0.10000000000000001}
nsopt(csopt)+imr(r)+adc: {ma: EngObs070728, name: NsOpt(CsOpt)+ImR(R)+ADC, pa: EngObs070727,
  sh: '', tx: 0.0, ty: 0.0, u: 0.0, usable: OK, use: '', v: 0.0, x: 0.0, y: 0.0, z: -0.10000000000000001}
nsopt(ir): {ma: EngObs070725, name: NsOpt(IR), pa: EngObs070726, sh: eye, tx: -1.2445900000000001,
  ty: 0.62229999999999996, u: 0.0, usable: OK, use: '', v: 0.0, x: -1.0, y: -2.0,
  z: 0.0}
nsopt(ir)+adc: {ma: EngObs070627*2 EngObs080521, name: NsOpt(IR)+ADC, pa: EngObs070627
    32PA EngObs080521 5PA, sh: eye EngObs070926, tx: -1.0570999999999999, ty: 0.62229999999999996,
  u: 0.0, usable: OK, use: Backup, v: 0.0, x: -1.0, y: -1.7, z: NA}
nsopt(ir)+imr(b): {ma: '', name: NsOpt(IR)+ImR(B), pa: EngObs070927 4PA, sh: eye EngObs080711,
  tx: -1.8668899999999999, ty: 0.87121000000000004, u: 0.0, usable: '', use: Backup,
  v: 0.0, x: -1.3999999999999999, y: -3.0, z: 0.0}
nsopt(ir)+imr(b)+adc: {ma: EngObs070626, name: NsOpt(IR)+ImR(B)+ADC, pa: EngObs070726,
  sh: eye, tx: -1.2445900000000001, ty: 0.93344000000000005, u: 0.0, usable: OK, use: '',
  v: 0.0, x: -1.5, y: -2.0, z: 0.0}
nsopt(ir)+imr(r): {ma: EngObs080521, name: NsOpt(IR)+ImR(R), pa: EngObs070927 3PA
    EngObs080521 5PA, sh: eye EngObs070927, tx: -1.555739, ty: 0.62229500000000004,
  u: 0.0, usable: '', use: Backup, v: 0.0, x: -1.0, y: -2.5, z: 0.0}
nsopt(ir)+imr(r)+adc: {ma: EngObs080521, name: NsOpt(IR)+ImR(R)+ADC, pa: EngObs070926
    5PA EngObs080521 32PA, sh: eye EngObs070926, tx: -1.0570999999999999, ty: 0.62229999999999996,
  u: 0.0, usable: OK, use: Backup, v: 0.0, x: -1.0, y: -1.7, z: 0.070000000000000007}
nsopt(nsopt): {ma: EngObs061207, name: NsOpt(NsOpt), pa: EngObs061207, sh: eye, tx: 0.0,
  ty: 0.0, u: 0.0, usable: OK, use: '', v: 0.0, x: -0.80000000000000004, y: -0.40000000000000002,
  z: 0.0}
nsopt(nsopt)+adc: {ma: EngObs070124, name: NsOpt(NsOpt)+ADC, pa: EngObs070124, sh: eye,
  tx: 0.0, ty: 0.0, u: 0.0, usable: OK, use: '', v: 0.0, x: -1.2, y: -0.80000000000000004,
  z: 0.0}
nsopt(nsopt)+imr(b): {ma: EngObs070129*1, name: NsOpt(NsOpt)+ImR(B), pa: EngObs070129,
  sh: eye, tx: 0.0, ty: 0.0, u: 0.0, usable: '*1 EngObs080706', use: 080429, v: 0.0,
  x: -1.2, y: -0.80000000000000004, z: -0.23999999999999999}
nsopt(nsopt)+imr(b)+adc: {ma: EngObs070129, name: NsOpt(NsOpt)+ImR(B)+ADC, pa: EngObs070129,
  sh: eye, tx: 0.0, ty: 0.0, u: 0.0, usable: OK, use: '', v: 0.0, x: -1.2, y: -0.80000000000000004,
  z: 0.0}
nsopt(nsopt)+imr(r): {ma: '', name: NsOpt(NsOpt)+ImR(R), pa: Night of 2008-08-18 HST
    32PA, sh: EngObs080613 (eyes), tx: -0.76037999999999994, ty: 1.16981, u: 0.0,
  usable: '', use: '', v: 0.0, x: -2.0, y: -1.3, z: 0.0}
nsopt(nsopt)+imr(r)+adc: {ma: EngObs070130, name: NsOpt(NsOpt)+ImR(R)+ADC, pa: EngObs070130,
  sh: eye, tx: 0.0, ty: 0.0, u: 0.0, usable: OK, use: '', v: 0.0, x: -1.2, y: -0.80000000000000004,
  z: 0.0}
popt: {ma: EngObs061116 EngObs080601, name: POpt, pa: EngObs100217, sh: EngObs061116,
  tx: 1.5, ty: 0.0, u: '-', usable: OK, use: '', v: '-', x: 0.0, y: 0.0, z: 6.9000000000000004}
"""

# Keys for the above format
schema = [ ('name', str), ('usable', str), ('use', str),
           ('pa', str), ('ma', str), ('sh', str),
           ('x', float), ('y', float), ('z', float),
           ('tx', float), ('ty', float),
           ('u', float), ('v', float),
           ]

keys = map(lambda x: x[0], schema)

class PAMASettings(object):

    def __init__(self, logger):
        self.logger = logger
        self.tbl = {}
    
    def loadCSV(self, tblpath, sep=','):
        """Load PAMA table in CSV format.  _sep_ indicates the separator
        value to use."""

        in_f = open(tblpath, 'r')
        lines = in_f.readlines()
        in_f.close()

        res = {}

        for line in lines:
            line = line.strip()
            items = line.split(sep)

            if len(items) != len(keys):
                self.logger.warn("Line items (%d) don't match up to keys (%d):\n%s" % (
                    len(items), len(keys), str(items)))
                continue

            for i in xrange(len(items)):
                try:
                    items[i] = schema[i][1](items[i])

                except ValueError, e:
                    self.logger.warn("Invalid value for %s: '%s'" % (
                        keys[i], items[i]))

            d = dict(zip(keys, items))

            confname = d['name'].lower()

            # Check for duplicates before overwriting anything
            if res.has_key(confname):
                self.logger.warn("Duplicate configuration for '%s':\n1: %s\n2: %s" % (
                    confname, res[confname], d))
                continue

            res[confname] = d

        self.tbl = res

    def loadYAML(self, tblpath):
        """Load PAMA table in YAML format."""

        in_f = open(tblpath, 'r')
        buf = in_f.read()
        in_f.close()

        self.tbl = yaml.load(buf)

    def loadPython(self, tblpath):
        """Load PAMA table in Python dict format."""

        in_f = open(tblpath, 'r')
        buf = in_f.read()
        in_f.close()

        self.tbl = eval(buf)

    def saveYAML(self, tblpath):
        """Save PAMA table in YAML format."""
        txt = yaml.dump(self.tbl)
        
        if tblpath == 'stdout':
            print txt
        else:
            out_f = open(tblpath, 'w')
            out_f.write(txt)
            out_f.close()
        
    def savePython(self, tblpath):
        """Save PAMA table in Python dict format."""
        txt = """
#
# THIS FILE WAS AUTOMATICALLY GENERATED -- PLEASE DO NOT EDIT!!!
#
import tools.pama

pama = tools.pama.PAMASettings(pytbl=%s)

""" % (repr(self.tbl))
        
        if tblpath == 'stdout':
            print txt
        else:
            out_f = open(tblpath, 'w')
            out_f.write(txt)
            out_f.close()

    def getNames(self):
        """Get all the keys representing valid configurations."""
        res = []
        for val in self.tbl.values():
            res.append(val['name'])

        res.sort()
        return res

    def getValues(self, name):
        """Look up a configuration based on the name and return a
        Bunch of the values."""
        name_l = name.lower()
        return Bunch.Bunch(self.tbl[name_l])
            
    def __str__(self):
        return str(self.tbl)
        
    def __repr__(self):
        return repr(self.tbl)
        

def main(options, args):
    
    # Create top level logger.
    logger = ssdlog.make_logger('loadpama', options)

    pama = PAMASettings(logger)

    if options.input:
        pama.loadYAML(options.input)

    elif options.table:
        pama.loadCSV(options.table, sep=options.sep)

    if options.output:
        pama.saveYAML(options.output)

    elif options.pyout:
        pama.savePython(options.pyout)

    sys.exit(0)
    

if __name__ == '__main__':
    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-i", "--input", dest="input",
                      help="Specify a file to read in YAML format")
    optprs.add_option("-o", "--output", dest="output",
                      help="Specify a file to write in YAML format")
    optprs.add_option("-p", "--pyout", dest="pyout",
                      help="Specify a file to write in Python format")
    optprs.add_option("-t", "--table", dest="table",
                      help="Specify a file to read in CSV format")
    optprs.add_option("--sep", dest="sep", default='\t',
                      help="Specify separator for files in CSV format")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    ssdlog.addlogopts(optprs)

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

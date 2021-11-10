#!/usr/bin/env python
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Tue Jun 23 10:45:21 HST 2009
#]
#
#
"""
dbtool.py -- a tool for manipulating the SOSS Oracle database.

This simple tool lets you update records in the SOSS Oracle database.  At the moment
it only handles the USERADMINTBL where information about proposals is stored.  But it
should not be difficult to add other tables.

EXAMPLES:
  # Show a record
  ./dbtool.py --action=get --target=summit --propid=o00096
  
  # Extend a observation date
  ./dbtool.py --action=set --target=summit,simulator --propid=o00096 --endtime='2008-08-10'
  
  # Add an instrument
  ./dbtool.py --action=set --target=summit,simulator --propid=o00096 --inst=+HICIAO
  
  # Add a proposal
  ./dbtool.py --action=add --target=summit --propid=o08105 --obsgrp=S08A-015 \
      --inst=SPCAM --starttime=2008-01-20 --endtime=2008-08-10

  # Add a bunch of proposals from a Tom Winegar file
  ./dbtool.py --action=twin --target=summit --twinfile=/path/to/summit_XXY.txt

  Set --loglevel=0 to see more detail.  You can also direct logging to a file
  with --log=db.log

  Finally, BE CAREFUL!  This program does a fair number of sanity checks on the data,
  but you can still manage to screw things up if you are not careful.
"""

import sys, os
import re, time
import pprint

import Bunch
import logging, ssdlog
import SOSS.SOSSdb as SOSSdb
from cfg.INS import INSdata as INSconfig

version = "20080114.0"

# TODO: configure elsewhere
dbhosts = { 'summit': 'dbs', 'simulator': 'mdbs' }

# default op level (for SOSS database)
g_oplevel = {'default': "AG_Select,AllocInfo,Env_Monitor,Ins_Monitor,Obs_Journal,Obs_Operation,Obs_ProcEditor,Obs_Report,SelectAll_Obs,Sys_Monitor,Tel_Monitor,VGW_System",
           'advanced': "AG_Select,AllocInfo,Dev_Table,Env_Monitor,Ins_Config,Ins_Monitor,LogGUI,Mainte_Report,Obs_Journal,Obs_Operation,Obs_ProcEditor,Obs_Report,Ope_Report,SelectAll_Obs,Sys_Mode,Sys_Monitor,Sys_Statistic,Tel_Monitor,UserAdmin,VGW_System",
           }

class Error(Exception):
    pass


def ObsProposalToSOSSobsGrp(ObsProposal):
    """
    --- 'twin' file: -----------
    3.  # EXISTS
    ProposalID: o07102
    ObsProposal: S07A-009
    ObsPeriod: 2007/01/20 - 2007/08/10
    Instrument: MOIRCS,SPCAM
    Deadline: 2005/08/05
    ----------------------------

    This function changes the ObsProposal field into the group name used by SOSS;
    e.g. 'S07A-009' --> 's07a009'
    """
    if not ('-' in ObsProposal):
        raise Error("ObsProposal not in correct format (e.g. 'S08A-043')")

    obsGrp = (ObsProposal.lower().replace('-', ''))

    return obsGrp
        

def readtwin(fname):
    
    in_f = open(fname, 'r')
    text = in_f.readlines()
    in_f.close()

    res = []
    while len(text) > 0:

        line = text.pop(0).strip()
        match = re.match('^(\d+)\.\s*(#\sEXISTS)*\s*$', line)
        if match:
            line = text.pop(0).strip()
            match = re.match('^ProposalID:\s(\w{6})\s*$', line)
            if match:
                propid = match.group(1)
            else:
                raise Exception("Unexpected input: %s" % line)
            line = text.pop(0).strip()
            match = re.match('^ObsProposal:\s(\w{4}\-\w+)\s*$', line)
            if match:
                obsprop = match.group(1)
            else:
                raise Exception("Unexpected input: %s" % line)
            line = text.pop(0).strip()
            match = re.match('^ObsPeriod:\s(\d{4}/\d{2}/\d{2})\s\-\s(\d{4}/\d{2}/\d{2})\s*$', line)
            if match:
                starttime, endtime = match.groups()
            else:
                raise Exception("Unexpected input: %s" % line)
            line = text.pop(0).strip()
            match = re.match('^Instrument:\s([\w,]+)\s*$', line)
            if match:
                inst = match.group(1)
            else:
                raise Exception("Unexpected input: %s" % line)
            line = text.pop(0).strip()
            match = re.match('^Deadline:\s(\d{4}/\d{2}/\d{2})\s*$', line)
            if match:
                deadline = match.group(1)
            else:
                raise Exception("Unexpected input: %s" % line)

            options = Bunch.Bunch()
            options.propid = propid
            options.division = obsprop
            options.starttime = starttime.replace('/', '-')
            options.endtime = endtime.replace('/', '-')
            options.instruments = inst
            options.oplevel = None

            res.append(options)

    return res


class DbTool(object):
    """Simple class to manipulate the SOSS database.  Uses the SOSSdb module
    access functions. 
    """
    
    def __init__(self, logger, host):
        """Constructor.
        """
        
        self.logger = logger
        
        # Create SOSS DB object
        self.db = SOSSdb.SOSSdb(self.logger, host=host)

        # For looking up instruments
        self.ins_config = INSconfig()

        super(DbTool, self).__init__()


    def check_options(self, options, optionlist):
        """Check an options object (can be a Bunch, generic object, or as e.g. returned
        by optparse module) for a set of required attributes that must be NOT None.
        If any of the options are missing, an error message is generated to prompt for
        the missing ones.

        If the option name and the options attribute have different names, then they can
        be distinguished by a colon in the optionlist.

        Example:
          optionlist: ['starttime', 'endtime', 'inst:instruments', 'obsgrp:division']

          The options object must contain the attributes starttime, endtime, instruments
          and division.  Supposed endtime and division are None.  Then the following
          error string is logged and an Error raised:
            'Missing options: --endtime, --obsgrp
        """
        missing = []
        for varname in optionlist:
            option = varname
            if ':' in varname:
                (option, varname) = varname.split(':')
            try:
                val = getattr(options, varname)
                if val == None:
                    missing.append('--%s' % option)

            except AttributeError:
                missing.append('--%s' % option)

        if len(missing) > 0:
            raise Error("Missing options: %s" % ', '.join(missing))


    def set_inst(self, bnch, instruments):
        """Check a list of instrument names for correctness and set the instruments
        attribute in the bunch (bnch is a record from the SOSS usradmintbl).
        If an instrument using AO is specified, and AO is not present, then add AO
        to the list.
        """
        for insname in instruments:
            insname = insname.upper()
            try:
                self.ins_config.getCodeByName(insname)

            except KeyError:
                errmsg = "'%s' is not a valid instrument name" % insname
                raise Error(errmsg)

        # Append AO if CIAO specified, but not AO as well
        if ('CIAO' in instruments) and not ('AO' in instruments):
            instruments.append('AO')

        bnch.instruments = instruments


    def _fillRecord(self, bnch, options):
        """Update a record (bnch) from the SOSS usradmintbl.  bnch is just a Bunch
        object with fields set to python translated values from the table.  Options
        is another Bunch or any object with matching attributes.  If any of them
        are present and NOT None, then they are copied with the approriate checks
        and type conversions to the record and then the record is written to the
        database.  May raise an Error.
        """

        # Update start and end dates
        # TODO: parse variety of date formats, not just twin style
        if options.starttime:
            twin_starttime = options.starttime
            if not ':' in twin_starttime:
                twin_starttime += '-00:00:00'
            if not re.match(r'^\d{4}\-\d{2}\-\d{2}\-\d{2}:\d{2}:\d{2}$',
                            twin_starttime):
                raise Error("Please specify dates in the form YYYY-MM-DD[-HH:MM:SS]")
            bnch.starttime = SOSSdb.datetime_fromSOSS2(twin_starttime)
            
        if options.endtime:
            twin_endtime = options.endtime
            if not ':' in twin_endtime:
                twin_endtime += '-00:00:00'
            if not re.match(r'^\d{4}\-\d{2}\-\d{2}\-\d{2}:\d{2}:\d{2}$',
                            twin_endtime):
                raise Error("Please specify dates in the form YYYY-MM-DD[-HH:MM:SS]")
            bnch.endtime = SOSSdb.datetime_fromSOSS2(twin_endtime)

        # Update division/observation group (to 'purpose' field in db)
        if options.division:
            #bnch.purpose = ObsProposalToSOSSobsGrp(options.division)
            bnch.purpose = options.division

        # Update instrument list.  options value is a comma-separated string of
        # isntrument names.  If it begins with a + or - then those instruments
        # are added or removed to the set already in bnch.instruments
        if options.instruments:
            if options.instruments.startswith('+'):
                instruments = list(bnch.instruments)
                add_instruments = options.instruments[1:].split(',')
                for insname in add_instruments:
                    insname = insname.upper()
                    if not insname in instruments:
                        instruments.append(insname)
            elif options.instruments.startswith('-'):
                instruments = list(bnch.instruments)
                sub_instruments = options.instruments[1:].split(',')
                for insname in sub_instruments:
                    insname = insname.upper()
                    if insname in instruments:
                        instruments.remove(insname)
            else:
                instruments = options.instruments.split(',')
                
            self.set_inst(bnch, instruments)

        # Update "oplevel".  This field is best left to default, unless you really
        # know what you are doing.
        if options.oplevel == 'default':
            bnch.oplevel = g_oplevel['default'].split(',')
        elif options.oplevel == 'advanced':
            bnch.oplevel = g_oplevel['advanced'].split(',')
        elif options.oplevel:
            bnch.oplevel = options.oplevel.split(',')
            
        self.logger.debug("Updated record is: %s" % str(bnch))


    def getProp(self, propid):
        """Method to get a record from the usradmintbl.
        """

        try:
            return self.db.getProp(propid)

        except SOSSdb.SOSSdbError, e:
            raise Error("Couldn't access proposal: %s" % str(e))
    
    
    def format(self, bnch):
        """Return human-friendly values for a record from the admintable.
        """

        d = {}
        d.update(bnch)
        if d.has_key('starttime'):
            try:
                d['starttime'] = time.strftime("%a, %d %b %Y %H:%M:%S",
                                               time.localtime(bnch.starttime))
            except TypeError:
                pass
            try:
                d['endtime'] = time.strftime("%a, %d %b %Y %H:%M:%S",
                                             time.localtime(bnch.endtime))
            except TypeError:
                pass
            try:
                d['createtime'] = time.strftime("%a, %d %b %Y %H:%M:%S",
                                                time.localtime(bnch.createtime))
            except TypeError:
                pass
            try:
                d['updatetime'] = time.strftime("%a, %d %b %Y %H:%M:%S",
                                                time.localtime(bnch.updatetime))
            except TypeError:
                pass

        return d
    
    
    def updateProp(self, propid, options):
        """Method to get a update a record from the usradmintbl.
        """

        # Get the current proposal
        try:
            bnch = self.db.getProp(propid)

        except SOSSdb.SOSSdbError, e:
            raise Error("Couldn't access proposal: %s" % str(e))

        # Update it
        try:
            self._fillRecord(bnch, options)

            self.logger.info("Updating db...")
            self.db.setProp(bnch)
            self.db.commit()
            self.logger.info("OK")
            
        except (Error, SOSSdb.SOSSdbError), e:
            raise Error("Couldn't update proposal: %s" % str(e))
        
    
    def _createProp(self, propid, options):
        """Method to get a create a record in the usradmintbl.
        """

        self.check_options(options, ['starttime', 'endtime',
                                     'inst:instruments', 'obsgrp:division'])

        # Check whether proposal already exists
        try:
            self.db.getProp(propid)

            raise Error("Proposal exists, please use --action=set to update it")

        except SOSSdb.SOSSdbError, e:
            pass

        # Create a new empty record with defaults.
        try:
            bnch = self.db.mkProp(propid,
                                  instruments=[],
                                  oplevel=g_oplevel['default'].split(','))

            self._fillRecord(bnch, options)

            self.db.insProp(bnch)

        except (Error, SOSSdb.SOSSdbError), e:
            raise Error("Couldn't create proposal: %s" % str(e))


    def createProp(self, propid, options):
        """Method to get a create a record in the usradmintbl.
        """

        self.logger.info("Inserting %s into db..." % propid)
        self._createProp(propid, options)
        try:
            self.logger.info("Committing db...")
            self.db.commit()
            self.logger.info("OK")

        except (Error, SOSSdb.SOSSdbError), e:
            raise Error("Couldn't create proposal: %s" % str(e))


    def createPropsFromTwinfile(self, twinfile):

        twinlist = readtwin(twinfile)
        
        while len(twinlist) > 0:
            options = twinlist.pop(0)

            propid = options.propid
            self.logger.info("Inserting %s into db..." % propid)
            try:
                self._createProp(propid, options)

            except (Error, SOSSdb.SOSSdbError), e:
                msg = str(e).strip()
                if msg == 'Proposal exists, please use --action=set to update it':
                    try:
                        self.updateProp(propid, options)

                    except (Error, SOSSdb.SOSSdbError), e:
                        self.logger.error("Couldn't update proposal '%s': %s" % (
                            propid, str(e)))
                else:
                    self.logger.error("Couldn't create proposal '%s': %s" % (
                        propid, str(e)))

        try:
            self.logger.info("Committing db...")
            self.db.commit()
            self.logger.info("OK")

        except (Error, SOSSdb.SOSSdbError), e:
            raise Error("Couldn't create proposals: %s" % str(e))


def dispatch(dbtool, options, logger):
    """Dispatch an action on the database.
    """

    if options.table == 'usradmintbl':
        if options.action == 'twin':
            if not options.twinfile:
                raise Error("Please specify a --twinfile !")
            dbtool.createPropsFromTwinfile(options.twinfile)
            return

        if not options.propid:
            raise Error("Please specify a --propid !")
        
        if options.action == 'get':
            bnch = dbtool.getProp(options.propid)
            # TODO: prettier printout
            pprint.pprint(dbtool.format(bnch))

        elif options.action == 'add':
            dbtool.createProp(options.propid, options)

        elif options.action == 'set':
            dbtool.updateProp(options.propid, options)

        else:
            raise Error("Please specify an --action I understand!")

    else:
        raise Error("Please specify a --table I understand!")
        

def main(options, args):
    """Main program.  Set up the logger, create a dbtool object and invoke
    a method on it.
    """

    # Create top level logger.
    logger = ssdlog.make_logger('dbtool', options)

    if not options.target:
        logger.error("Please specify a --target !")
        return

    dbtools = []
    for target in options.target.split(','):
        try:
            dbtools.append(DbTool(logger, dbhosts[target]))

        except KeyError:
            logger.error("--target must include one or more of %s" % (
                str(dbhosts.keys())))
            return

    try:
        for dbtool in dbtools:
            dispatch(dbtool, options, logger)

    except (Error, SOSSdb.SOSSdbError), e:
        logger.error(str(e))
        sys.exit(1)
    

if __name__ == '__main__':
    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    optprs.add_option("--action", dest="action", default=None,
                      help="Action to perform")
    optprs.add_option("--endtime", dest="endtime", default=None,
                      help="Observation end date+time")
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--inst", dest="instruments", default=None,
                      help="Comma separated list of instruments to use")
    optprs.add_option("--obsgrp", dest="division", default=None,
                      help="Division/observation group")
    optprs.add_option("--oplevel", dest="oplevel", default=None,
                      help="Comma separated OPLEVEL list")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--propid", dest="propid", default=None,
                      help="Proposal id to use; e.g. o00096")
    optprs.add_option("--starttime", dest="starttime", default=None,
                      help="Observation start date+time")
    optprs.add_option("--table", dest="table", default="usradmintbl",
                      help="table to manipulate; e.g. usradmintbl")
    optprs.add_option("--target", dest="target", default=None,
                      help="summit|simulator|all")
    optprs.add_option("--twinfile", dest="twinfile", default=None,
                      help="'twin' file to read, e.g. summit_S08A.txt")
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

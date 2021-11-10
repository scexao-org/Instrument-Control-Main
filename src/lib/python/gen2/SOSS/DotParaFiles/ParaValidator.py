#! /usr/bin/python
#
# ParaValidator -- wrapper of Yasu's para file tools for use in
#    TaskManager and SIMCAM
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Tue Dec 21 11:32:05 HST 2010
#]
# Bruce Bon -- last edit 2007-09-28
#
#?
#?  The call to validator.populate in the ParaValidator.populate()
#?  method will fail if it evaluates a parameter before the case
#?  variable controlling it has been evaluated.  The parameter names
#?  from the .para file need to be saved in a list to preserve their
#?  order, and then evaluation needs to proceed in that order.  New
#?  .para files must also be checked to be sure that case variable
#?  parameters are defined before any parameters that depend on
#?  them.               Bruce & Eric, 2007-09-11
# THIS HAS BEEN FIXED, AS FAR AS I COULD TEST IT....EJ (2008.04.21)

import os, glob, re
import Bunch

# For PARA file validation
import SOSS.parse.para_lexer as para_lexer
from SOSS.parse.para_parser import NOP, paraParser
from DotParaFileParser import ParameterHandler, ParameterValidationException, \
     InconsistentParameterDefinitionException, DotParaFileException

# is this still needed?
import SOSS.parse.CommandParser as CommandParser


class ParaValidatorError(Exception):
    pass

class ParaValidator(object):

    def __init__(self, logger):
        self.logger = logger
        self.parser = CommandParser.CommandParser()

        self.para_lexer = para_lexer.paraScanner(logger=logger, debug=0)
        self.para_parser = paraParser(self.para_lexer, logger=logger,
                                      debug=0)

        self.para = Bunch.threadSafeBunch()
        self.userRegMap = Bunch.threadSafeBunch()
        self.systemRegMap = Bunch.threadSafeBunch()
        self.commandRegMap = Bunch.threadSafeBunch()


    def keys(self):
        """Return all the keys for all loaded PARA definitions.
        """
        return self.para.keys()

    
    def items(self):
        """Return all the items for all loaded PARA definitions.
        """
        return self.para.items()

    
    def has_key(self, parakey):
        """Return True if there is a para definition for this key,
        False otherwise.
        """
        return self.para.keys()

    
    def getitem(self, parakey):
        """Get the para bunch for a particular key.  May raise a
        ParaValidatorError if it is not found.
        """
        try:
            return self.para[parakey]

        except KeyError:
            raise ParaValidatorError("No PARA validator for key '%s'" % \
                                     str(parakey))

    
    def loadParaBuf(self, parakey, paraFileBuf):
        """Load a para definition from a buffer.
        """
        # Create paramDefs and validator from parsing the buffer.
        # (see other modules in this directory for details)
        bnch = self.para_parser.parse_buf(paraFileBuf, name=str(parakey))
        validator = ParameterHandler(bnch, logger=self.logger)

        # Store paramdefs and validator under the passed in parakey
        # (e.g. parakey might be ("TSC", "AG_PARTS") ) 
        self.para[parakey] = Bunch.Bunch(paramDefs=bnch.paramDict,
                                         paramList=bnch.paramList,
                                         paramAliases=bnch.paramAliases,
                                         validator=validator)

    def loadParaFile(self, parakey, paraFile):
        """Load a para definition from a file.
        """
        # Read the specified file into a buffer and then load
        # the defintion from the buffer
        try:
            para_f = open(paraFile, 'r')
            buf = para_f.read()
            para_f.close()

            self.loadParaBuf(parakey, buf)
            
        except IOError, e:
            raise ParaValidatorError("Cannot open para file: %s" % str(e))


    def loadParaDir(self, paraDir, subsys=None):
        """Load a directory of para files.
        """

        if not os.path.isdir(paraDir):
            raise ParaValidatorError("Not a directory: %s" % paraDir)
        
        # If no subsystem name passed in, then strip off final directory name
        # in the paraDir path and use that (e.g. "TSC', "SPCAM", etc.)
        if not subsys:
            (dir, subsys) = os.path.split(paraDir)

        subsys = subsys.upper()

        # For each para file found in the directory, load it
        paraFiles = glob.glob(os.path.join(paraDir, '*.para'))
        #print paraFiles
        for paraFile in paraFiles:
            (pfx, fn) = os.path.split(paraFile)
            match = re.match('^(.+)\.para$', fn)
            if not match:
                self.logger.debug("skipping non-para file '%s'" % fn)
                continue
            # Upper case all command names in generated para key
            # NOTE: this case has to match what is going on with parakeys
            # in the Task files
            #cmd = match.group(1).lower()
            cmd = match.group(1).upper()
            self.logger.debug("loading para file '%s'" % fn)
            self.loadParaFile((subsys, cmd), paraFile)
        

    def loadParaDirs(self, paraDirList):
        """Loads the validator from a list of para file directories.
        """
        for paraDir in paraDirList:
            self.loadParaDir(paraDir)
            

    def populate(self, parakey, params, statusMap={}, frameMap={}):
        """Populates missing parameters with their defaults according to the
        para file definition.
        Notes:
           self.para[parakey].paramDefs is the result of a call to yacc.yacc()
             See DotParaFileParser.parser = yacc.yacc(tabmodule=yacc_tab_module)
           self.para[parakey].validator  is a ParameterHandler object
        """
        self.logger.debug("Populating key '%s' params=%s" % \
                          (str(parakey), str(params)))

        if not self.para.has_key(parakey):
            raise ParaValidatorError("No PARA validator for key '%s'" % \
                                     str(parakey))
        
        # Otherwise run the populator on it
        paramDefs = self.para[parakey].paramDefs
        validator = self.para[parakey].validator
        aliases = self.para[parakey].paramAliases

        # Find @COMMAND map, if any
        try:
            commandRegMap = self.commandRegMap[parakey]

        except KeyError:
            #commandRegMap = self.systemRegMap[parakey]
            commandRegMap = {}
        self.logger.debug("commandRegMap = %s" % str(commandRegMap))
            
        # Find @USER map, if any
        try:
            userRegMap = self.userRegMap[parakey]

        except KeyError:
            #userRegMap = self.systemRegMap[parakey]
            userRegMap = {}
        self.logger.debug("userRegMap = %s" % str(userRegMap))

        try:
            # Populate parameters
            # Only substitutes if param is None or key is missing
            result = validator.populate(params, statusMap=statusMap,
                                        userRegMap=userRegMap,
                                        systemRegMap=self.systemRegMap,
                                        commandRegMap=commandRegMap,
                                        frameMap=frameMap,
                                        statusAliases=aliases)
            
            # Convert parameter keys back to lower case (populator
            # returns them in uppercase) and fill in missing items
            for (key, val) in result.items():
                params[key.lower()] = result[key]

            self.logger.debug("Population result '%s' params=%s" % \
                              (str(parakey), str(params)))

        except InconsistentParameterDefinitionException, e:
            self.logger.error("Parameter validation error for %s: %s" % \
                               (str(parakey), str(e)))
            raise ParaValidatorError(str(e))


    def convert(self, parakey, params, nop=NOP, subst_nop=NOP):
        """Converts a set of parameters according to the para file
        definition and alters the _params_ dictionary appropriately.
        """
        self.logger.debug("Converting key '%s': params=%s" % \
                          (str(parakey), str(params)))
        if not self.para.has_key(parakey):
            raise ParaValidatorError("No PARA validator for key '%s'" % \
                                     str(parakey))

        # Sigh...convert keys to upper case
        # TODO: really must fix DotParaFileParser.py to use caseless dict
        # so we don't have to do all these conversions
        newdict = {}
        for (key, val) in params.iteritems():
            newdict[key.upper()] = val

        # Get parameter definitions
        paramDefs = self.para[parakey].paramDefs

        # Try to recast parameter values according to their type specified
        # in the paradefs
        for key in params.keys():
            # Get key and value
            uc_key = key.upper()
            value = params[key]

            try:
                #paramDef = paramDefs[uc_key].defaultDef
                paramDef = paramDefs[uc_key]
                aa = paramDef.getParamDefForParamMap(newdict)
                # TODO: get naming consistent with DotParaFileParser.py
                paramDef = aa
                #self.logger.debug("Converting parameter '%s': paramDef=%s" % \
                #                  (uc_key, str(paramDef)))

            except (KeyError, ValueError):
                raise ParaValidatorError("Converting %s: No param definition for '%s'" % (
                    str(parakey), str(uc_key)))

            if not paramDef:
                raise ParaValidatorError("Converting %s: No default param definition for '%s'" % (
                    str(parakey), str(uc_key)))

            # Get parameters type
            try:
                paramType = paramDef['TYPE']

            except KeyError:
                raise ParaValidatorError("Converting %s: param definition for '%s' is missing a TYPE spec" % (
                    str(parakey), str(uc_key)))
            
            # Special case for NOPs (a NOP can go through for a NUMBER!)
            if value == nop:
                value_cvt = subst_nop

            else:
                # Now dispatch according to type.
                # Possible types: { NUMBER, CHAR }
                if paramType == 'NUMBER':
                    try:
                        fmt = paramDef['FORMAT']

                    except KeyError:
                        raise ParaValidatorError("Converting %s: param definition for '%s' is missing a FORMAT spec" % (
                            str(parakey), str(uc_key)))

                    # Do conversion, since we might get anything from the
                    # status system
                    try:
                        if fmt.endswith('f'):
                            value_cvt = float(value)

                        elif fmt.endswith('d'):
                            # TODO: need a more sophisticated numerical conversion routine here!
                            value_cvt = int(float(value))
                            
                        else:
                            # Assume int value if we can't grok format?
                            value = int(float(value))

                    except ValueError:
                        # Hmmm, not sure what kind of value we have here
                        # lets leave it as is
                        pass

                elif paramType == 'CHAR':
                    # String.  Convert value "as is" to a string
                    value_cvt = str(value)

                else:
                    # ?? What the !??
                    raise ParaValidatorError("Converting %s: unknown type definition '%s' for parameter '%s'" % (
                        str(parakey), paramType, str(uc_key)))

            # Reassign value 
            params[key] = value_cvt

        # And we're done
        self.logger.debug("Conversion results '%s': params=%s" % \
                          (str(parakey), str(params)))
    

    def validate(self, parakey, params):
        """Validates a set of parameters against the para file definition.
        """
        self.logger.debug("Validating key '%s' params=%s" % \
                          (str(parakey), str(params)))

        if not self.para.has_key(parakey):
            raise ParaValidatorError("No PARA validator for key '%s'" % \
                                     str(parakey))
        
        # Otherwise run the validator on it
        paramDefs = self.para[parakey].paramDefs
        validator = self.para[parakey].validator

        # Sigh...convert keys to upper case
        # TODO: really must fix DotParaFileParser.py to use caseless dict
        # so we don't have to do all these conversions
        newdict = {}
        for (key, val) in params.iteritems():
            newdict[key.upper()] = val

        try:
            # Validate parameters
            validator.validate(newdict)

            # Store parameters to @COMMAND register
            # Should this be explicit in g2task?
            self.store_commandReg(parakey, newdict)
            
            self.logger.debug("Validation passed.")

        except ParameterValidationException, e:
            self.logger.error("Parameter validation error for %s: %s" % \
                              (str(parakey), str(e)))
            raise ParaValidatorError(str(e))


    def format(self, parakey, params, supress_quotation=False):
        """Formats a set of parameters according to the para file
        definition and returns a dict of strings
        """
        self.logger.debug("Formatting key '%s' params=%s" % \
                          (str(parakey), str(params)))

        if not self.para.has_key(parakey):
            raise ParaValidatorError("No PARA validator for key '%s'" % \
                                     str(parakey))
        
        # Get parameter definitions
        paramDefs = self.para[parakey].paramDefs

        # List of all parameters in upper case
        paramlst = paramDefs.keys()
        
        # This will hold the result set
        res = {}

        # Sigh...convert keys to upper case
        # TODO: really must fix DotParaFileParser.py to use caseless dict
        # so we don't have to do all these conversions
        newdict = {}
        for (key, val) in params.iteritems():
            newdict[key.upper()] = val

        # Try to recast parameter values according to their type specified
        # in the paradefs
        for key in params.keys():
            # Get key and value
            uc_key = key.upper()
            value = params[key]

            try:
                paramlst.remove(uc_key)
                #paramDef = paramDefs[uc_key].defaultDef
                paramDef = paramDefs[uc_key]
                aa = paramDef.getParamDefForParamMap(newdict)
                # TODO: get naming consistent with DotParaFileParser.py
                paramDef = aa
                #self.logger.debug("Converting parameter '%s': paramDef=%s" % \
                #                  (uc_key, str(paramDef)))

            except (KeyError, ValueError):
                raise ParaValidatorError("Formatting %s: No param definition for '%s'" % (
                    str(parakey), str(uc_key)))

            # Get parameters type
            try:
                paramType = paramDef['TYPE']

            except KeyError:
                raise ParaValidatorError("Formatting %s: param definition for '%s' is missing a TYPE spec" % (
                    str(parakey), str(uc_key)))
            
            # Special case for NOPs (a NOP can go through for a NUMBER!)
            if value == NOP:
                value_str = 'NOP'

            else:
                # Now dispatch according to type.
                # Possible types: { NUMBER, CHAR }
                if paramType == 'NUMBER':
                    try:
                        fmt = paramDef['FORMAT']

                    except KeyError:
                        raise ParaValidatorError("Formatting %s: param definition for '%s' is missing a FORMAT spec" % (
                            str(parakey), str(uc_key)))

                    # Do conversion, since we might get anything from the
                    # status system
                    try:
                        if fmt.endswith('f'):
                            value = float(value)

                        elif fmt.endswith('d'):
                            value = int(float(value))
                            
                        else:
                            # Assume int value if we can't grok format?
                            value = int(float(value))

                    except ValueError:
                        # Hmmm, not sure what kind of value we have here
                        # lets leave it as is
                        pass

                    # Finally, format the value
                    try:
                        value_str = (fmt % value)

                    except TypeError, e:
                        raise ParaValidatorError("Formatting %s: error formatting '%s' as number; value=%s: %s" % (
                            str(parakey), str(uc_key), str(value), str(e)))

                elif paramType == 'CHAR':
                    # String.  Convert value "as is" to a string
                    value_str = str(value)

                else:
                    # ?? What the !??
                    raise ParaValidatorError("Formatting %s: unknown type definition '%s' for parameter '%s'" % (
                        str(parakey), paramType, str(uc_key)))

            if not supress_quotation:
                # Check for spaces in value string and quote if necessary
                if (' ' in value_str) and (not value_str.startswith('"')):
                    value_str = ('"%s"' % value_str)
                
            # Assign shiny new value string to result set
            res[key] = value_str

        # Final sanity check to see that we didn't leave any parameters
        # unformatted (if so, they weren't passed to us!)
        if len(paramlst) > 0:
            raise ParaValidatorError("Formatting %s: some parameters missing: '%s'" % (
                str(parakey), str(paramlst)))
            
        # And we're done
        self.logger.debug("Formatting results '%s': res=%s" % \
                          (str(parakey), str(res)))
        return res
    

    def params2str(self, parakey, params):
        """This method takes a set of parameters and turns it back into a
        formatted command string.  The _params_ must be fully populated.
        """

        formatted_params = self.format(parakey, params)
        
        # Get parameter list
        paramLst = self.para[parakey].paramList

        (subsys, cmdname) = parakey
        res = ["EXEC", subsys.upper(), cmdname.upper()]

        for key in paramLst:
            val = formatted_params[key.lower()]
            
            # Check for spaces in value string and quote if necessary
            if (' ' in val) and (not val.startswith('"')):
                val = ('"%s"' % val)
                
            res.append('%s=%s' % (key.upper(), val))

        cmd_str = ' '.join(res)
        self.logger.debug("params2str key '%s' cmd_str=%s" % (
            str(parakey), cmd_str))
        return cmd_str
    

    def processCmd(self, cmdstr, noparaok=False):
        """Validates a command string against the para file definition.
        """
        try:
            # Scan command string into tokens
            tokens = self.parser.tokenize(cmdstr)

            # Parse tokens into args and kwdargs
            (args, params) = self.parser.parseParams(tokens)

        except CommandParser.CommandParserError, e:
            raise ParaValidatorError("Error parsing command string: %s" % \
                                     str(e))
        
        # Sanity check on cmdstr: EXEC SUBSYS CMD PARAM1=XX PARAM2=YY ...
        if (len(args) < 3) or (args[0].upper() != 'EXEC'):
            raise ParaValidatorError("Bad DD command format: %s" % cmdstr)

        # Extract subsystem and command names, which together form a
        # PARA key
        subsys = args[1].upper()
        cmd = args[2].strip()
        parakey = (subsys.upper(), cmd.upper())
        # Strip off above items; rest form argument list (may be [])
        args = args[4:]

        # Check for existence of para key.  If no key then it is an error
        # unless it has been explicitly allowed with the 'noparaok' flag
        if not self.para.has_key(parakey):
            if not noparaok:
                raise ParaValidatorError("No PARA validator for key '%s'" % \
                                         str(parakey))
            else:
                # No para key found.  Just return params "as is"
                return (subsys, cmd.lower(), args, params, 1)

        # Convert according to PARA definition.  This should change
        # string NOPs ("NOP") back to NOP objects.
        self.convert(parakey, params, nop='NOP')
        
        # Populate for any missing parameters
        self.populate(parakey, params)
        
        # Validate parameters against types
        self.validate(parakey, params)

        # Now change back the NOP objects to Python None's
        self.convert(parakey, params, subst_nop=None)
        
        return (subsys, cmd.lower(), args, params, 0)


    def store_commandReg(self, parakey, params):
        self.commandRegMap[parakey] = Bunch.caselessDict({})
        self.commandRegMap[parakey].update(params);

    def store_userReg(self, parakey, params):
        self.userRegMap[parakey] = Bunch.caselessDict({});
        self.userRegMap[parakey].update(params);


def main(options, args):

    import logging, os.path

    logger = logging.getLogger('para.ParaValidator')
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)

    validator = ParaValidator(logger)

    print args
    for arg in args:
        if os.path.isdir(arg):
            validator.loadParaDir(arg)

        else:
            (pfx, fn) = os.path.split(arg)
            (pfx, subsys) = os.path.split(pfx)
            (key, ext) = os.path.splitext(fn)
            parakey = (subsys, ext.upper())
            validator.loadParaFile(parakey, arg)
        

if __name__ == "__main__":
    # Parse command line options
    from optparse import OptionParser
    import sys

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")

    (options, args) = optprs.parse_args(sys.argv[1:])


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
       
#END

#!/usr/bin/env python
#
# DotParaFileParser.py
#
# Yasu Sakakibara
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Tue Dec 21 12:09:20 HST 2010
#]
# Bruce Bon
#
"""
.para file parser that parses .para file into a dictionary of 
parameter_name string -> ParamDef Object mapping. 

ParamDef is a class that encapsulate the .para file parameter
definition information. 
It holds the information about the parameter, i.e.
CHAR type parameter    : DEFAULT
                         SET
                         NOP
                         TYPE (=CHAR)

NUMERIC type parameter : DEFAULT
                         MAX
                         MIN
                         NOP
                         TYPE (=NUMBER)
                         
This module also includes the generator of all the possible parameter value
combinations and validator that validates if the parameter combination is
valid according to the .para file definition. These application level
classes probably should be moved to other module.

NOTES
=====
[ ] The parser has a problem with multiple PARA files when a file does not
have a proper newline at the end--make sure all PARA files end with a
NEWLINE
"""
import unittest
import re
import logging, ssdlog
import NestedException
import Bunch

import SOSS.parse.para_lexer as para_lexer
from SOSS.parse.para_parser import NOP, paraParser, DotParaFileException


#===================================================#
# Domain Exceptions
#===================================================#
class InconsistentParameterDefinitionException(DotParaFileException):
    def __init__(self, exception, message, offendingKey, offendingAttributes):
        DotParaFileException.__init__(self, exception = exception, message = message)
        self.offendingKey = offendingKey
        self.offendingAttributes = offendingAttributes[:]

class ParameterValueException(DotParaFileException):
    def __init__(self, exception, message, offendingKey, offendingValue):
        DotParaFileException.__init__(self, exception = exception, message = message)
        self.offendingKey = offendingKey
        self.offendingValue = offendingValue

class BadParameterDefinitionException(DotParaFileException):
    pass

#===================================================#
# Application level classes
#===================================================#

class ParameterValidationException(ParameterValueException):
    pass


class ParameterValueRangeValidationException(ParameterValidationException):
    def __init__(self, exception, message, offendingKey, offendingValue, minValue, maxValue):
        ParameterValidationException.__init__(self, exception = exception, 
                                               message = message,
                                               offendingKey = offendingKey,
                                               offendingValue = offendingValue)
        self.minValue = minValue
        self.maxValue = maxValue

class AliasWrapper(object):
    def __init__(self, alias):
        self.alias = alias

class ParameterHandler(object):
    def __init__(self, paramObj, logger=None):
        self.paramObj = paramObj
        self.paramDefMap = paramObj.paramDict
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger('dotPara.ParameterHandler')

        #self.regexp_frameref = re.compile(r'^&GET_F_NO\[\s*(\w+)\s*(\w+)\s*\]$')
        self.regexp_frameref = re.compile(r'^&GET_F_NO\[\s*(\w+)\s+(\w+)\s*(\d+)?\s*\]$',
                                          re.IGNORECASE)
        

    def get_systemRegMap(self, key, paramMap, paramDefMap):
        # @SYSTEM default is actually stored in the paramDefMap 
        if not paramDefMap.has_key('DEFAULT'):
            raise ParameterValueException(Exception(), 
                                          "@SYSTEM is specified as a value for [%s] but there is no DEFAULT attribute is the PARA file for this parameter" % (key),
                                          key,
                                          ['@SYSTEM'])
        paramMap[key] = paramDefMap['DEFAULT']


    def get_commandRegMap(self, key, paramMap, commandRegMap, paramDefMap):
        try:
            paramMap[key] = commandRegMap[key]

        except KeyError, e:
            # If uninitialized, default to @SYSTEM
            self.logger.warn("No @COMMAND history for param '%s', defaulting to @SYSTEM" % (key))
            self.get_systemRegMap(key, paramMap, paramDefMap)
##             raise ParameterValueException(e, 
##                                     "@COMMAND is specified as a value for [%s] but the register is empty" % (key),
##                                     key,
##                                     ['@COMMAND'])

    def get_userRegMap(self, key, paramMap, userRegMap, paramDefMap):
        try:
            paramMap[key] = userRegMap[key]

        except KeyError, e:
            # If uninitialized, default to @SYSTEM
            self.logger.warn("No @USER history for param '%s', defaulting to @SYSTEM" % (
                key))
            self.get_systemRegMap(key, paramMap, paramDefMap)
##             raise ParameterValueException(e, 
##                                     "@USER is specified as a value for [%s] but the register is empty" % (key),
##                                     key,
##                                     ['@USER'])

    def get_statusMap(self, key, paramMap, statusMap, paramDefMap):
        if not paramDefMap.has_key('STATUS'):
            raise ParameterValueException(Exception(), 
                                    "@STATUS is specified as a value for [%s] but there is no STATUS attribute defined in PARA file" % (key),
                                    key,
                                    ['@STATUS'])

        statusAlias = paramDefMap['STATUS'][1:]
        try:
            #paramMap[key] = statusMap[statusAlias]
            paramMap[key] = AliasWrapper(statusAlias)
            
        except KeyError, e:
            # TODO: trap other status errors?
            raise ParameterValueException(e, 
                                    "@STATUS is specified as a value for [%s] but there is an error getting that status" % (key),
                                    key,
                                    # @STATUS?
                                    ['@USER'])
            
    def resolveStatusItems(self, paramMap, statusMap, statusAliases,
                           statusCache):
        """This is an optimization to reduce the overhead of looking up status items.
        """

        keys = []
        for (param, val) in paramMap.iteritems():
            if isinstance(val, AliasWrapper):
                keys.append((param, val.alias))

        if len(keys) == 0:
            return

        # Now fetch all possibly needed status items in one call.
        # If we were here before then the statusCache already has
        # all the possibly needed items.
        if len(statusCache) == 0:
            try:
                # ?? None --> STATNONE
                statusCache = {}.fromkeys(statusAliases, None)
                #self.logger.debug("Fetching needed status items: %s" % (
                #        statusAliases))
                statusMap.fetch(statusCache)

            except Exception, e:
                raise DotParaFileException("Error fetching status %s: %s" % (
                        statusAliases, str(e)))

        # Replace these true values into the parameters
        for (param, alias) in keys:
            paramMap[param] = statusCache[alias]


    def fillDefaultValues(self, 
                          paramMap, 
                          statusMap=None, 
                          systemRegMap=None, 
                          userRegMap=None, 
                          commandRegMap=None,
                          frameMap=None,
                          doConditionals=True):
        """This function fills the dictionary 'paramMap' (a dictionary of DDC parameters) with
        default values for parameters that are missing from the keys."""

        #for key in self.paramDefMap.keys():
        for key in self.paramObj.paramList:
            if not key in paramMap.keys():
                aParamDef = self.paramDefMap[key]
                # Is this a CASE-type parameter and we are instructed to skip them?
                if aParamDef.isConditional() and (not doConditionals):
                    continue

                aa = aParamDef.getParamDefForParamMap(paramMap)
                self.logger.debug("Parameter definition for parameter '%s': %s" % (
                    key, str(aa)))
                if aa.has_key('DEFAULT'):
                    def_val = aa['DEFAULT']
                    self.logger.debug('handling default = [%s]' % (aa['DEFAULT']))
                    try:
                        if  '@SYSTEM' == def_val:
                            # Actually, this must be an error case
                            # since @SYSTEM default is the DEFAULT!
                            raise InconsistentParameterDefinitionException(Exception(), 
                                                            "Default value for [%s] is @SYSTEM, but that is a circular definition!" % key,
                                                             key,
                                                             ['DEFAULT'])
                            
                        elif '@USER' == def_val:
                            self.get_userRegMap(key, paramMap, userRegMap, aa)

                        elif '@COMMAND' == def_val :
                            self.get_commandRegMap(key, paramMap, commandRegMap, aa)
                            
                        elif '@STATUS' == def_val:
                            self.get_statusMap(key, paramMap, statusMap, aa)

                        else:
                            # &GET_F_NO[...] ?
                            match = self.regexp_frameref.match(def_val)
                            if match:
                                self.logger.debug('matched, getting frames (%s)' % str(match.groups()))
                                foo = frameMap[match.groups()]
                                self.logger.debug('got frames: %s' % str(foo))
                                paramMap[key] = foo
                            else:
                                paramMap[key] = def_val

                    except KeyError, e:
                        raise InconsistentParameterDefinitionException(e, 
                                                        "Could not find default value for [%s]" % key,
                                                         key,
                                                         ['DEFAULT'])
                    except TypeError, e:
                        raise InconsistentParameterDefinitionException(e, 
                                                        "Default for [%s] is defined as [%s] but the dictionary for it was None (or non dictionary type)" % (key, aa['DEFAULT']),
                                                        key,
                                                        ['DEFAULT'])
                else:
                    # no value specified and no default,
                    # raise. error? Empty parameters allowed?
                    # Eric: param errors will be caught in validation
                    # TODO: maybe should issue a warning though...
                    pass
        return paramMap
                               

    def replaceValues(self, 
                      paramMap, 
                      statusMap=None, 
                      systemRegMap=None, 
                      userRegMap=None, 
                      commandRegMap=None,
                      frameMap=None,
                      doConditionals=True):
        """This function replaces the NOP, @COMMAND, @SYSTEM, @USER and @STATUS values if present
        in the DDC parameters in 'paramMap'.
        """

        # Now convert the values to python types and 
        # replace the NOP, @COMMAND, @SYSTEM, @USER, and @STATUS
        #
        #for (key, value) in paramMap.iteritems():
        for key in self.paramObj.paramList:
            aParamDef = self.paramDefMap[key]
            # Is this a CASE-type parameter and we are instructed to skip them?
            if aParamDef.isConditional() and (not doConditionals):
                continue

            # should not raise a KeyError because this is usually preceeded by
            # fillDefaultValues
            if not paramMap.has_key(key):
                raise DotParaFileException("No value found for parameter '%s'" % key)
                
            value = paramMap[key]

            aa = aParamDef.getParamDefForParamMap(paramMap)
            self.logger.debug("Parameter definition for parameter '%s': %s" % (
                key, str(aa)))

            if 'NOP' == value:
                if aa.has_key('NOP'):
                    nop_val = aa['NOP']
                    self.logger.debug('handling NOP = [%s]' % (nop_val))
                    try:
                        if 'NOP' == nop_val:
                                paramMap[key] = NOP
                                
                        elif '@SYSTEM' == nop_val:
                            self.get_systemRegMap(key, paramMap, aa)
                            if paramMap[key] == 'NOP':
                            # WARNING: This is a Hack.
                            # This is the case where 
                            # NOP=@SYSTEM and DEFAULT=NOP
                            # This circular reference needs to be 
                            # terminated by assuming NOP=NOP
                                    paramMap[key] = NOP
                                    
                        elif  '@USER' == nop_val:
                            self.get_userRegMap(key, paramMap, userRegMap, aa)
                            
                        elif  '@COMMAND' == nop_val :
                            self.get_commandRegMap(key, paramMap, commandRegMap, aa)
                            
                        elif '@STATUS' == nop_val:
                            self.get_statusMap(key, paramMap, statusMap, aa)
                            
                        else:
                            # &GET_F_NO[...] ?
                            match = self.regexp_frameref.match(nop_val)
                            if match:
                                paramMap[key] = frameMap[match.groups()]
                            else:
                                paramMap[key] = nop_val

                    except KeyError, e:
                        raise InconsistentParameterDefinitionException(e, 
                                            "Could not find NOP value for [%s]" % key,
                                             key,
                                             ['NOP'])
                    except TypeError, e:
                        raise InconsistentParameterDefinitionException(e, 
                                            "NOP for [%s] is defined as [%s] but the dictionary for it was None (or non dictionary type)" % (key, nop_val),
                                            key,
                                            ['NOP'])
                else:
                    raise InconsistentParameterDefinitionException(Exception(), 
                                            "NOP is specified as a value for [%s]  but the .para file does not have NOP definition" % (key),
                                            key,
                                            ['NOP'])
            elif '@COMMAND' == value:
                self.get_commandRegMap(key, paramMap, commandRegMap, aa)
                
            elif '@USER' == value:
                self.get_userRegMap(key, paramMap, userRegMap, aa)
                
            elif '@STATUS' == value:
                self.get_statusMap(key, paramMap, statusMap, aa)
                
            elif '@SYSTEM' == value:
                self.get_systemRegMap(key, paramMap, aa)
                
        return paramMap


    def populate(self, paramMap, statusMap=None, systemRegMap=None, 
                 userRegMap=None, commandRegMap=None, frameMap=None,
                 statusAliases=None):
        '''
        This function returns a dictionary of SOSS DDC parameters with
        default/nop value substitution and type conversion.
        '''
        result = {}
        #result = Bunch.caselessDict()
        # If key = None, treat these as undefined
        for (key, val) in paramMap.iteritems():
            if val != None:
                result[key.upper()] = val
            
        # firstly, try to fill the missing parameters from DEFAULTs,
        # but skip CASE-based ones
        self.fillDefaultValues(result, statusMap, systemRegMap, 
                               userRegMap, commandRegMap, frameMap,
                               doConditionals=False)

        # now replace the NOP and register values, but skip the
        # CASE-based ones
        self.replaceValues(result, statusMap, systemRegMap, 
                           userRegMap, commandRegMap, frameMap,
                           doConditionals=False)

        # resolve all missing status items--this is needed here because some 
        # case-based items may depend on status values
        statusCache = {}
        self.resolveStatusItems(result, statusMap, statusAliases,
                                statusCache)

        # next, try to fill the missing parameters from DEFAULTs,
        # including CASE-based ones
        self.fillDefaultValues(result, statusMap, systemRegMap, 
                               userRegMap, commandRegMap, frameMap,
                               doConditionals=True)

        # again replace the NOP and register values, including
        # CASE-based ones
        self.replaceValues(result, statusMap, systemRegMap, 
                           userRegMap, commandRegMap, frameMap,
                           doConditionals=True)

        # Fill in remaining status items from cache
        self.resolveStatusItems(result, statusMap, statusAliases,
                                statusCache)

        # Now convert the values to python types
        #self.logger.debug("final conversion: result=%s" % (str(result)))
        for (key, value) in result.iteritems():
            aParamDef = self.paramDefMap[key]
            aa = aParamDef.getParamDefForParamMap(result)
            self.logger.debug("Parameter definition for parameter '%s': %s" % (
                key, str(aa)))
            if (result[key] is not None) and \
               (aa['TYPE'] == 'NUMBER') and \
               (NOP != result[key]):
                try:
                    if not aa.has_key('FORMAT'):
                        raise BadParameterDefinitionException("TYPE for [%s] is defined as [%s] but it has no FORMAT defined" % (key, aa['TYPE']))
                        
                    fmt = aa['FORMAT']
                    if fmt.endswith('f'):
                        result[key] = float(result[key])
                    else:
                        # TODO: need a more sophisticated numerical conversion routine here!
                        result[key] = int(float(result[key]))

                except (ValueError, TypeError), e:
                    message = "could not convert the value[%s] for key=[%s] to float" % (str(result[key]), key)
                    self.logger.error(message)                    
                    raise ParameterValueException(message = message, exception=e, offendingKey=key, offendingValue=value)
        #self.logger.debug("returning: result=%s" % (str(result)))
        return result
        
    def validate(self, paramMap):
        '''
        '''
        for aParamKey in paramMap.keys():
            aParamValue = paramMap[aParamKey]
            aParamDef = self.paramDefMap[aParamKey]
            aa = aParamDef.getParamDefForParamMap(paramMap)
            self.logger.debug('Parameter definition for parameter %s: %s' % (aParamKey, str(aa)))
            if  aParamValue is None:
                    message = "param with key=[%s] has None as value. This is not acceptable by validate() method" % aParamKey
                    self.logger.error(message)
                    raise ParameterValidationException(exception=Exception(), 
                                                       message = message,
                                                       offendingKey= aParamKey,
                                                       offendingValue="None")
            
            if ('NOP' == aParamValue) or (NOP == aParamValue):
                if aa.has_key('NOP') and ('NOP' == aa['NOP']):
                    continue
                else:
                    message = "param with key=[%s] has value=NOP but handling of NOP is not defined in the .para file" % aParamKey
                    self.logger.error(message)
                    raise ParameterValidationException(exception=Exception(), 
                                                       message = message,
                                                       offendingKey= aParamKey,
                                                       offendingValue="NOP")
                    #return False
            
            if aa['TYPE'] == 'CHAR':
                if aa.has_key('SET'):
                    s = set(aa['SET'])
                    if  not aParamValue in s:
                        message = "param with key=[%s] has value=[%s] but it is not in the acceptable value set defined in the .para file" % \
                                  (aParamKey, aParamValue)
                        self.logger.error(message)
                        raise ParameterValidationException(exception=Exception(), 
                                                           message = message,
                                                           offendingKey= aParamKey,
                                                           offendingValue=aParamValue)

            elif aa['TYPE'] == 'NUMBER':
                try:
                    if aa.has_key('MIN') and (float(aParamValue) < float(aa['MIN'])):
                        message =  'The value=[%s] for key=[%s] is lesser than the minumum value=[%s]' % \
                                        (aParamValue, aParamKey, aa['MIN'])
                        self.logger.error(message)
                        raise ParameterValueRangeValidationException(exception=Exception(), 
                                                           message =message,
                                                           offendingKey= aParamKey,
                                                           offendingValue=aParamValue,
                                                           minValue=aa['MIN'],
                                                           maxValue=aa['MAX'])

                    if aa.has_key('MAX') and (float(aParamValue) > float(aa['MAX'])):
                        message =  'The value=[%s] for key=[%s] exceeds the maximum value=[%s]' % \
                                        (aParamValue, aParamKey, aa['MAX'])
                        self.logger.error(message)
                        raise ParameterValueRangeValidationException(exception=Exception(), 
                                                           message =message,
                                                           offendingKey= aParamKey,
                                                           offendingValue=aParamValue,
                                                           minValue=aa['MIN'],
                                                           maxValue=aa['MAX'])
                                                           
                except ValueError, e:
                        message = "param with key=[%s] has value=[%s] but the value is defined as a numerical type in the .para file" % (aParamKey, aParamValue)
                        self.logger.error(message)
                        raise ParameterValidationException(exception=e, 
                                                           message = message,
                                                           offendingKey= aParamKey,
                                                           offendingValue=aParamValue)
        return True


def combination(set):
    first = set[0]
    rest = set[1:]
    if len(set) == 1:
        result = [[i] for i in set[0]]
        return result
    tmp = combination(rest)
    result = []
    for i in first:
        for j in tmp:
            tmp2 = [i]
            for k in j:
                tmp2.append(k)
            result.append(tmp2)
    return result


def main(options, args):

    import os

    # TODO: configure the logger
    logger = logging.getLogger('para.ParameterHandler')
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.WARN)

    lexer = para_lexer.paraScanner(logger=logger, debug=0)
    parser = paraParser(lexer, logger=logger, debug=0)

    if len(args) > 0:
        for filename in args:
            in_f = open(filename, 'r')
            buf = in_f.read()
            in_f.close()

            print filename, ":"
            if options.scan:
                res = lexer.tokenize(buf)
                print res
            else:
                res = parser.parse(buf)
                print res
            

    elif options.tsctest:
        #? rootLogger = logging.getLogger()
        pattern = re.compile(r'^(\w+)\.para$')
        currentDir = os.path.split(__file__)[0]
        TSCdir = os.path.join(currentDir, "../SkPara/cmd/TSC")
        have = os.listdir(TSCdir)

        for fname in have:
            if not pattern.match(fname):
                continue

            objectName = pattern.match(fname).group(1)
            # parser = yacc.yacc(debug=0)
            buf = ''
            print "#", "-" * 30, fname
            fh = open(os.path.join(TSCdir, fname),"r")
            fw = open(os.path.join(currentDir, "%s.cmd"%objectName), "w")
            for cline in fh.xreadlines():
                buf = buf + cline
            buf = buf + '\n'
            l2 = parser.mk_paramObj(fname, buf)
            print l2
            v = ParameterHandler(l2)

            listOfSets = []
            listOfParamNames = []
            for aKey in l2:
                listOfParamNames.append(aKey)
                listOfSets.append(l2[aKey].getAllParamValueList())

            combinationList = combination(listOfSets)

            for aList in combinationList:
                parameterMap = {}
                for i in range(len(listOfParamNames)):
                    parameterMap[listOfParamNames[i]] = aList[i]
                try:
                    parameterMap = v.populate(parameterMap, {}, {}, {}, {}, {})
                    v.validate(parameterMap)
                    printList = 'EXEC TSC %s'  % objectName
                    for i in parameterMap.keys():
                        printList= printList + (" %s=%s "%(i, parameterMap[i]))
                    fw.write(printList + "\n")
                except (ParameterValidationException, InconsistentParameterDefinitionException), e:
                    pass
            fw.close()
        

if __name__ == '__main__':
    import sys
    from optparse import OptionParser

    # Parse command line options
    usage = "usage: %prog [options] [file ...]"
    optparser = OptionParser(usage=usage, version=('%%prog'))
    
    optparser.add_option("--debug", dest="debug", default=False,
                         action="store_true",
                         help="Enter the pdb debugger on main()")
    optparser.add_option("--profile", dest="profile", action="store_true",
                         default=False,
                         help="Run the profiler on main()")
    optparser.add_option("--scan", dest="scan", default=False,
                         action="store_true",
                         help="Only run lexer on arguments")
    optparser.add_option("--tsc", dest="tsctest", default=False,
                         action="store_true",
                         help="Run tests on the TSC PARA files")
    optparser.add_option("-v", "--verbose", dest="verbose", default=False,
                         action="store_true",
                         help="Turn on verbose output")

    (options, args) = optparser.parse_args(sys.argv[1:])

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

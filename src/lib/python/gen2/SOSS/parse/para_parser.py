#!/usr/bin/env python
#
# para_parser.py -- SOSS PARA file parser
#
# Yasuhiko Sakakibara
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Dec 27 11:45:14 HST 2010
#]
#
import NestedException

from lex import LexToken
import yacc
import Bunch
import logging, ssdlog

import para_lexer

yacc_tab_module = 'paraParser'

class DotParaFileException(NestedException.NestedException):
    pass

class NoDefaultParameterDefinitonException(DotParaFileException):
    pass


class ParamDef(object):
    def __init__(self, name):
        self.name = name
        self.condList = []
        self.aliases = set([])
        self.defMap = {}
        self.defaultDef = None

    def isConditional(self):
        return (len(self.condList) > 0)
    
    def addParamDef(self, paramDef):
        
        if paramDef.has_key('CASE'):
            c = tuple(paramDef['CASE'])
            self.condList.append(c)
            self.defMap[c] = paramDef
        else:
            self.defaultDef = paramDef

        # If this paramDef has a status alias defined, then add
        # it to the set of aliases possible for this parameter
        if paramDef.has_key('STATUS'):
            self.aliases.add(paramDef['STATUS'][1:])

    def getParamDefForParamMap(self, paramMap = {}):
        # Create a set of tuples of the form (paramKey, paramValue)
        # out of the parameter given.
        # Go through the condition list and check if that set is the
        # super set of the condition. 
        paramSet = set([aPair for aPair in paramMap.iteritems()])
        for aCond in self.condList:
            aCondSet = set(aCond)
            if paramSet.issuperset(aCondSet):
                # aCond is the first condition list
                # that matches the current parameter set.
                return self.defMap[aCond]
        # We are here bacause none of the conditions matched.   
        if self.defaultDef is None:
            raise NoDefaultParameterDefinitonException(None, 
                                                       "There is no default parameter defined for %s" % self.name )
        return self.defaultDef

    def getAllParamValueList(self):
        result = set([])
        for aList in self.condList:
            result = result.union(self.getParamValueList(self.defMap[aList]))
        if not self.defaultDef is None:
            result = result.union(self.getParamValueList(self.defaultDef))
        return result
        
    def getParamValueList(self, map):
        if 'NUMBER' == map['TYPE']:
               result = []
               if map.has_key('MIN'):
                   result.append(map['MIN'])
               if map.has_key('MAX'):
                   result.append(map['MAX'])
               if not (map.has_key('MIN') or map.has_key('MAX')):
                   result.append("0")
               if map.has_key('NOP') and 'NOP' == map['NOP']:
                   result.append("NOP")
                   
               return set(result)
        elif 'CHAR' == map['TYPE']:
            result = []
            if map.has_key('SET'):
                result = result +  map['SET']
            elif map.has_key('DEFAULT'):
                result.append(map['DEFAULT'])
            if map.has_key('NOP') and 'NOP' == map['NOP']:
                result.append("NOP")
               
            return set(result)

    def __repr__(self):
        return "ParamDef(%s) cond=%s defMap=%s defaultDef=%s aliases=%s" % (
            self.name, self.condList, self.defMap, self.defaultDef,
            self.aliases)

    def __str__(self):
        return self.__repr__()

#Marker object
class NOPObject(object):
    def __str__(self):
        return 'NOP'

NOP = NOPObject()


#===================================================#
# PARA file Parser
#===================================================#

class paraParseError(Exception):
    pass

class paraParser(object):

##     def p_object_def1(self, t):
##         '''object_def : object_def  param_def_line'''
##         aParamID     = t[2][0]
##         aParamDefMap = t[2][1]
##         if t[1].has_key(aParamID):
##             pass
##         else:
##             o = ParamDef(aParamID)
##             t[1][aParamID] = o
##         t[1][aParamID].addParamDef(aParamDefMap)
##         t[0] = t[1]


##     def p_object_def2(self, t):
##         '''object_def : param_def_line'''
##         aParamID     = t[1][0]
##         aParamDefMap = t[1][1]
##         o = ParamDef(aParamID)
##         o.addParamDef(aParamDefMap)
##         t[0] = {aParamID : o}

    def p_object_def1(self, t):
        '''object_def : object_def  param_def_line'''
        aParamID     = t[2][0]
        aParamDefMap = t[2][1]
        if aParamID in t[1][1]:
            pass
        else:
            o = ParamDef(aParamID)
            t[1][1][aParamID] = o
            t[1][0].append(aParamID)
        t[1][1][aParamID].addParamDef(aParamDefMap)
        t[0] = t[1]


    def p_object_def2(self, t):
        '''object_def : param_def_line'''
        aParamID     = t[1][0]
        aParamDefMap = t[1][1]
        o = ParamDef(aParamID)
        o.addParamDef(aParamDefMap)
        t[0] = ([aParamID], {aParamID : o})

    def p_object_def3(self, t):
        '''object_def :  object_def NEWLINE'''
        t[0] = t[1]

    def p_object_def4(self, t):
        '''object_def : NEWLINE object_def'''
        t[0] = t[2]

    def p_param_def_line(self, t):
        '''param_def_line : param_def
                          | param_def NEWLINE'''
        t[0] = t[1]

    def p_param_def(self, t):
        '''param_def : ID defs_list'''
        t[0] = [t[1], t[2]]

    def p_defs_list1(self, t):
        '''defs_list : defs_list defs'''
        t[1][t[2][0]] = t[2][1]
        t[0] = t[1] 

    def p_defs_list2(self, t):
        '''defs_list : defs'''
        t[0] = {t[1][0] : t[1][1]} 

    def p_case_cond_element(self, t):
        '''case_cond_element : ID EQ STR'''
        t[0] = (t[1], t[3])

    def p_case_cond_list1(self, t):
        '''case_cond_list : case_cond_element '''
        t[0] = [t[1]]

    def p_case_cond_list2(self, t):
        '''case_cond_list : case_cond_list COMMA case_cond_element'''
        t[1].append(t[3])
        t[0] = t[1]

    def p_case_cond(self, t):
        '''case_cond   : LPAREN case_cond_list RPAREN'''
        t[0] = t[2]

    def p_comma_separated_list1(self, t):
        '''comma_separated_list : comma_separated_list COMMA STR
                                | comma_separated_list COMMA QSTR'''
        t[1].append(t[3])
        t[0] = t[1]

    def p_comma_separated_list2(self, t):
        '''comma_separated_list : STR
                                | QSTR'''
        t[0] = [t[1]]

    # Since we need to handle comma separated list
    # of STR or QSTR and the keyword SET may appear
    # in the rhs, we need to treat the single
    # STR(QSTR) token as comma_separated_list.
    # Therefore, the stand alone STR or QSTR
    # will not appear as the rhs.
    def p_rhs_1(self, t):
        '''rhs  : FSTR
                | REGREF
                | ALIASREF
                | FUNCREF
                | LSTR
                | case_cond'''
        t[0] = t[1]

    def p_defs_1(self, t):
        '''defs : STR EQ rhs'''
        t[0] = [t[1], t[3]]

    def p_defs_2(self, t):
        '''defs : STR EQ comma_separated_list'''
        if 'SET' != t[1].upper():
            t[3] = t[3][0]
        else:
            if (t[3]).__contains__('NOP'):
                (t[3]).remove('NOP')
        t[0] = [t[1], t[3]]

    def p_error(self, p):
        if isinstance(p, LexToken):
            self.logger.error("Syntax error at '%s'" % (p.value))
            # ? Try to recover to some sensible state
            self.parser.errok()
        else:
            self.logger.error("Syntax error; p=%s" % (str(p)))
            #? Try to recover to some sensible state
            self.parser.restart()
    

    def __init__(self, lexer, logger=None, tabmodule=yacc_tab_module,
                 **kwdargs):
        
        # Share lexer tokens
        self.lexer = lexer
        self.tokens = lexer.getTokens()

        self.tabmodule = tabmodule
        
        if not logger:
            logger = logging.getLogger('para.parser')
        self.logger = logger

        self.build(tabmodule=self.tabmodule, **kwdargs)
        self.reset()


    def reset(self, lineno=1):
        self.errors = 0
        self.errinfo = []
        # hack
        self.result = None

        self.lexer.reset(lineno=lineno)

        
    def build(self, **kwdargs):
        self.parser = yacc.yacc(module=self, start='object_def',
                                logger=self.logger, **kwdargs)
    
   
    def parse(self, buf, startline=1):

        # Initialize module level error variables
        self.reset(lineno=startline)

        res = self.parser.parse(buf, lexer=self.lexer)

        return res


    def parse_buf(self, buf, name=''):

        (paramList, paramDict) = self.parse(buf)

        # union together all the possible status aliases that could be
        # used in this para
        aliases = set([])
        for paramDef in paramDict.values():
            aliases.update(paramDef.aliases)

        res = Bunch.Bunch(name=name,
                          paramList=paramList,
                          paramDict=Bunch.caselessDict(paramDict),
                          paramAliases=aliases,
                          errors=self.errors,
                          errinfo=self.errinfo)
        return res


    def parse_file(self, parapath, name=None):

        in_f = open(parapath, 'r')
        buf = in_f.read()
        in_f.close()

        if not name:
            name = parapath
            
        res = self.parse_buf(buf, name=name)
        res.filepath = parapath

        return res


def main(options, args):

    # TODO: configure the logger
    logger = logging.getLogger('para.parser')

    lexer = para_lexer.paraScanner(logger=logger, debug=0)
    
    parser = paraParser(lexer, logger=logger, debug=0,
                        tabmodule=yacc_tab_module)

    if len(args) > 0:
        for filename in args:
            try:
                res = parser.parse_file(filename)

                if (res.errors == 0) and options.verbose:
                    print res.paramList
                    print res.paramDict

                print "%s: %d errors" % (filename, res.errors)

            except paraParseError, e:
                # Print error message and continue to next file
                print str(e)

    else:
        buf = sys.stdin.read()
        try:
            res = parser.parse_buf(buf)

            if (res.errors == 0) and options.verbose:
                print res.paramList
                print res.paramDict
            
                print "%d errors" % (res.errors)

        except paraParseError, e:
            # Print error message
            print str(e)


if __name__ == '__main__':
    import sys
    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options] [file ...]"
    optparser = OptionParser(usage=usage, version=('%%prog'))
    
    optparser.add_option("--debug", dest="debug", default=False,
                         action="store_true",
                         help="Enter the pdb debugger on main()")
    optparser.add_option("--profile", dest="profile", action="store_true",
                         default=False,
                         help="Run the profiler on main()")
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

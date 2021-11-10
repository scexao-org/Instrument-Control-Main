# 
# Eric Jeschke (eric@naoj.org)
#
import re
import lex
import yacc
import logging
import pprint

import Bunch
import ssdlog
from SOSS.parse.sk_common import ASTNode

lex_tab_module  = 'lex_tab_launcher'
yacc_tab_module  = 'yacc_tab_launcher'


#===================================================#
# Launcher file Lexer 
#===================================================#

class ScanError(Exception):
    pass

class launcherScanner(object):
    
    tokens = ('COMMA', 'NEWLINE', 'ID', 'STR', 'IDREF',
              'BREAK', 'LCONT', 'COMMENT', 'SEMICOLON', 'SEPARATOR',
              'LABEL', 'LIST', 'SELECT', 'INPUT', 'CMD', 'ASSIGN',
              )

    reserved = {'LABEL': 'LABEL',
                'INPUT': 'INPUT',
                'SELECT': 'SELECT',
                'LIST': 'LIST',
                'BREAK': 'BREAK',
                'CMD': 'CMD',
                } 

    t_SEMICOLON = r';'
    t_ASSIGN = r'='
    t_COMMA = r','
    t_SEPARATOR = r'<>'
    t_ignore = ' \t'

    def t_ID(self, t):
        #r'''[a-zA-Z0-9][a-zA-Z0-9_\.\:\-]*'''
        r'''[a-zA-Z0-9][a-zA-Z0-9_\.\:]*'''

        t.value = t.value.upper()
        #tok = t.value.upper()
        tok = t.value
        if tok in self.reserved:
            t.type = self.reserved[tok]
            # Convert lower case to upper
            #t.value = tok
        return t

    # Quoted string will not be an ID
    def t_STR(self, t):
        r'"[^"]*"'
        # Just strip off the quotes
        #t.value = t.value[1:-1]
        return t

    def t_IDREF(self, t):
        r'\$[\w_][\w\d_\.]*'
        # 'Variable' reference: strip off the '$'
        #t.value = t.value[1:]
        t.value = t.value.upper()
        return t

    def t_COMMENT(self, t):
        r'\#.*'
        #self.lexer.lineno += 1

    def t_NEWLINE(self, t):
        r'\n+'
        self.lexer.lineno += t.value.count("\n")
        return t

    def t_LCONT(self, t):
        r'\\\n'
        self.lexer.lineno += 1

    def t_error(self, t):
        self.logger.error("Illegal character in input '%s'" % (t.value[0]))
        t.skip(1)
    
    def build(self, **kwdargs):
        self.lexer = lex.lex(object=self, **kwdargs)


    def __init__(self, logger=None, lextab=lex_tab_module, **kwdargs):

        if not logger:
            logger = logging.getLogger('launcher.lexer')
        self.logger = logger
        
        # these variables are used to determine 
        # if the token we are looking is an ID
        self.isTokenAnID = True
        self.isTokenWithinParenthesis = False

        self.lextab = lextab

        self.build(lextab=self.lextab, **kwdargs)
        self.reset()

    def reset(self, lineno=1):
        self.errors = 0
        self.errinfo = []
        self.lexer.lineno = lineno
        
    def getTokens(self):
        return self.tokens

    # For compatibility with ply.yacc
    def token(self):
        return self.lexer.token()

    # For compatibility with ply.yacc
    def input(self, input):
        return self.lexer.input(input)

    def tokenize(self, buf, startline=1):
        # Reset lexer state
        self.reset(lineno=startline)

        self.lexer.input(buf)
        res = []
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            res.append(tok)

        #return (self.errors, res, self.errinfo)
        return res


    def scan_buf(self, buf):

        tokens = self.tokenize(buf)

        res = Bunch.Bunch(tokens=tokens, errors=self.errors,
                          errinfo=self.errinfo)
        return res


    def scan_file(self, launcherpath):

        in_f = open(launcherpath, 'r')
        buf = in_f.read()
        in_f.close()

        res = self.scan_buf(buf)
        res.filepath = launcherpath

        return res


#===================================================#
# Launcher file parser
#===================================================#

class ParseError(Exception):
    pass

class launcherParser(object):

    def p_launchers_def1(self, p):
        '''launchers : launcher'''
        p[0]  = ASTNode('launchers', p[1])

    def p_launchers_def2(self, p):
        '''launchers : launchers  launcher'''
        p[1].items.append(p[2])
        p[0] = p[1]

    def p_launcher1(self, p):
        '''launcher : label_def  body_def'''
        p[0] = ASTNode('launcher', p[1], p[2])
        
    def p_launcher2(self, p):
        '''launcher : SEPARATOR'''
        p[0] = ASTNode('sep', p[1])
        
    def p_launcher3(self, p):
        '''launcher : launcher NEWLINE'''
        p[0] = p[1]
        
    def p_launcher4(self, p):
        '''launcher : NEWLINE launcher'''
        p[0] = p[2]
        
    def p_label_def1(self, p):
        '''label_def : LABEL  id_or_str  NEWLINE'''
        p[0] = ASTNode('label', p[2])
        
    def p_body_def1(self, p):
        '''body_def : body_def  line_def'''
        p[1].items.append(p[2])
        p[0] = p[1]

    def p_body_def2(self, p):
        '''body_def : line_def'''
        p[0] = ASTNode('body', p[1])

    def p_line_def1(self, p):
        '''line_def : control_def
                    | command_def
                    | break'''
        p[0] = p[1]

    def p_control_def1(self, p):
        '''control_def : param INPUT width def_val ctrl_label NEWLINE'''
        p[0]  = ASTNode('input', p[1], p[3], p[4], p[5])

    def p_control_def2(self, p):
        '''control_def : param INPUT width def_val NEWLINE'''
        p[0]  = ASTNode('input', p[1], p[3], p[4], '')

    def p_control_def3(self, p):
        '''control_def : param SELECT val_list ctrl_label NEWLINE'''
        p[0]  = ASTNode('select', p[1], p[3], p[4])

    def p_control_def4(self, p):
        '''control_def : param SELECT val_list NEWLINE'''
        p[0]  = ASTNode('select', p[1], p[3], '')

    def p_control_def5(self, p):
        '''control_def : param LIST val_list ctrl_label NEWLINE'''
        p[0]  = ASTNode('list', p[1], p[3], p[4])

    def p_control_def6(self, p):
        '''control_def : param LIST val_list NEWLINE'''
        p[0]  = ASTNode('list', p[1], p[3], '')

    def p_val_list1(self, p):
        '''val_list : pure_val_list
                    | subst_val_list'''
        p[0] = p[1]

    def p_pure_val_list1(self, p):
        '''pure_val_list : pure_val_list COMMA id_or_str'''
        p[1].items.append(p[3])
        p[0] = p[1]

    def p_pure_val_list2(self, p):
        '''pure_val_list : id_or_str'''
        p[0] = ASTNode('pure_val_list', p[1])

    def p_subst_val_list1(self, p):  
        '''subst_val_list : subst_val_list COMMA value_pair'''
        p[1].items.append(p[3])
        p[0] = p[1]

    def p_subst_val_list2(self, p):  
        '''subst_val_list : value_pair'''
        p[0] = ASTNode('subst_val_list', p[1])

    def p_value_pair(self, p):
        '''value_pair : id_or_str ASSIGN id_or_str'''
        p[0] = ASTNode('value_pair', p[1], p[3])

    def p_command_def1(self, p):
        '''command_def : CMD ID param_list NEWLINE'''
        p[0] = ASTNode('cmd', p[2], p[3])

    def p_param_list1(self, p):  
        '''param_list : param_list param_pair'''
        p[1].items.append(p[2])
        p[0] = p[1]

    def p_param_list2(self, p):  
        '''param_list : param_pair'''
        p[0] = ASTNode('param_list', p[1])

    def p_param_pair(self, p):
        '''param_pair : id_or_str ASSIGN rhs'''
        p[0] = ASTNode('param_pair', p[1], p[3])

    def p_id_or_str(self, p):
        '''id_or_str : ID
                     | strnq'''
        p[0] = p[1]
        
    def p_rhs(self, p):
        '''rhs : ID
               | STR
               | IDREF'''
        p[0] = p[1]
        
    def p_ctrl_label(self, p):
        '''ctrl_label : strnq'''
        p[0] = p[1]
        
    def p_param(self, p):
        '''param : ID'''
        p[0] = p[1]
        
    def p_break(self, p):
        '''break : BREAK NEWLINE'''
        p[0] = ASTNode('break')
        
    def p_width(self, p):
        '''width : ID'''
        p[0] = p[1]
        
    def p_def_val(self, p):
        '''def_val : id_or_str'''
        p[0] = p[1]

    def p_strnq(self, p):
        '''strnq : STR'''
        # Just strip off the quotes
        p[0] = p[1][1:-1]
        
    def p_epslion(self, p):
        """empty :"""
        pass

    def p_error(self, p):
        if isinstance(p, lex.LexToken):
            self.logger.error("Syntax error at line %d: '%s'" % (
                    p.lineno, p.value))
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
            logger = logging.getLogger('launcher.parser')
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
        self.parser = yacc.yacc(module=self, start='launchers',
                                logger=self.logger, **kwdargs)
    
   
    def parse(self, buf, startline=1):

        # Initialize module level error variables
        self.reset(lineno=startline)

        res = self.parser.parse(buf, lexer=self.lexer)

        return res


    def parse_buf(self, buf, name=''):

        res = self.parse(buf)
        return res


    def parse_file(self, launcherpath, name=None):

        in_f = open(launcherpath, 'r')
        buf = in_f.read()
        in_f.close()

        if not name:
            name = launcherpath
            
        res = self.parse_buf(buf, name=name)
        return res


class LauncherManager(object):

    def __init__(self, logger):
        self.logger = logger

        self.reset()

    def reset(self):
        # Create the scanner
        self.scanner = launcherScanner(logger=self.logger, debug=0,
                                       lextab=lex_tab_module)
        # Create the parser
        self.parser = launcherParser(self.scanner, logger=self.logger,
                                     debug=1,
                                     tabmodule=yacc_tab_module)

    def parse_buf(self, buf):
        return self.parser.parse_buf(buf)

    def parse_file(self, filepath):
        return self.parser.parse_file(filepath)


def printTokens(tokens):
    for token in tokens:
        print token

        
def main(options, args):

    logger = ssdlog.make_logger('launcher', options)

    # Create the scanner
    scanner = launcherScanner(logger=logger, debug=0,
                              lextab=lex_tab_module)
    # Create the parser
    parser = launcherParser(scanner, logger=logger, debug=1,
                            tabmodule=yacc_tab_module)

    if len(args) > 0:
        for filename in args:
            try:
                if options.action == 'scan':
                    res = scanner.scan_file(filename)
                    if (res.tokens != None) and options.verbose:
                        printTokens(res.tokens)

                elif options.action == 'parse':
                    res = parser.parse_file(filename)
                    if (res != None) and options.verbose:
                        pprint.pprint(res)

                else:
                    raise ScanError("I don't understand action='%s'" % (
                            options.action))

            except (ScanError, ParseError), e:
                # Print error message and continue to next file
                logger.error(str(e))

    else:
        buf = sys.stdin.read()
        try:
            res = scanner.scan_buf(buf)

            if (res.tokens != None) and options.verbose:
                printTokens(res.tokens)
            
                print "%d errors" % (res.errors)

        except (ScanError, ParseError), e:
            # Print error message
            logger.error(str(e))


if __name__ == '__main__':
    import sys
    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--action", dest="action", metavar="WHAT",
                      default="parse",
                      help="'parse' or 'scan'; WHAT to do")
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("-v", "--verbose", dest="verbose", default=False,
                      action="store_true",
                      help="Turn on verbose output")
    ssdlog.addlogopts(optprs)

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
            


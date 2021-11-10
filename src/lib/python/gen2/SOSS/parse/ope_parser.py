#!/usr/bin/env python
#
# ope_parser.py -- SOSS OPE command parser
#
# Yasuhiko Sakakibara
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Feb 26 11:35:29 HST 2009
#]
#
# Derived from the sk_parser, and used to parse a single command.
#
import sys
# There are some unresolved issues with the new ply version
#import ply.yacc as yacc
#from ply.lex import LexToken
import yacc
from lex import LexToken
import sk_lexer
from sk_common import ASTNode
import logging
import Bunch

# TODO: switch to SSD logger
logger = logging.getLogger('ope_parser')
tokens = sk_lexer.tokens


precedence = (
    ('left', 'AND', 'OR'),
    ('right', 'NOT'),
    ('nonassoc', 'EQ', 'NE', 'GT', 'GE', 'LT', 'LE'),
    ('left', 'ADD', 'SUB'),
    ('left', 'MUL', 'DIV'),
    ('right', 'UMINUS'),         # Ficticious token, unary minus operator
)

class opeParseError(Exception):
    pass


# Yuck! module-level variables to count errors 
errors = 0
errinfo = []

def p_error(arg):
    global errors, errinfo

    errors += 1
    if isinstance(arg, LexToken):
        errstr = ("Parse error at line %d, token %s ('%s')" % (
            arg.lineno, arg.type, str(arg.value)))
        #print errstr
        errinfo.append(Bunch.Bunch(lineno=arg.lineno, errstr=errstr,
                                   token=arg))
        
    else:
        errstr = ("Parse error: %s" % str(arg))
        #print errstr
        errinfo.append(Bunch.Bunch(lineno=0, errstr=errstr, token=arg))


#####################################################################
#  This portion should be kept in sync with that in sk_parser as
#  much as possible.  TODO: is it possible to share?
#####################################################################
        
def p_statement(p):
    """statement : command_list"""
    p[0] = p[1]
    
def p_command_list(p):
    """command_list : exec_command
                    | abs_command
    """
    p[0] = ASTNode('cmdlist', p[1])

def p_command_exec(p):
    """exec_command : EXEC factor factor param_list"""
    p[0] = ASTNode('exec', p[2], p[3], p[4], None)

## def p_command_exec2(p):
##     """exec_command : SET factor factor param_list"""
##     p[0] = ASTNode('set', p[2], p[3], p[4])

def p_command_abs(p):
    """abs_command : factor param_list"""
    p[0] = ASTNode('abscmd', p[1], p[2], )

def p_param_list1(p):
    """ param_list : empty"""
    p[0] = ASTNode('param_list')
 
def p_param_list2(p):  
    """param_list : param_list key_value_pair"""
    p[1].append(p[2])
    p[0] = p[1]

def p_key_value_pair(p):
    """key_value_pair : ID ASSIGN expression"""
    #p[0] = ASTNode('key_value_pair', p[1].upper(), p[3])
    p[0] = ASTNode('key_value_pair', p[1].lower(), p[3])

def p_factor1(p):
    """factor : NUM"""
    if p[1].find('.') < 0:
        p[0] = ASTNode('number', int(p[1]))
    else:
        p[0] = ASTNode('number', float(p[1]))

def p_factor2(p):
    """factor : IDREF""" 
    p[0] = ASTNode('id_ref', p[1][1:])

def p_factor3(p):
    """factor : ALIASREF""" 
    p[0] = ASTNode('alias_ref', p[1][1:])

def p_factor4(p):
    """factor : frame_id_ref"""
    p[0] = p[1]

def p_factor6(p):
    """ factor : ID
               | AND
               | OR
               | IN
    """
    p[0] = ASTNode('string', p[1])

def p_factor7(p):
    """ factor : LSTR """
    #p[0] = p[1]
    p[0] = ASTNode('lstring', p[1])

def p_factor8(p):
    """ factor : QSTR """
    p[0] = ASTNode('qstring', p[1])

def p_factor9(p):
    """factor : REGREF""" 
    p[0] = ASTNode('reg_ref', p[1][1:])

## def p_factor_2_1(p):
##     """factor2 : SUB factor %prec UMINUS"""
##     p[0] = ASTNode('monad', p[1], p[2])

def p_factor_2_2(p):
    """factor2 : ADD factor %prec UMINUS"""
    p[0] = p[2]

## def p_factor_2_3(p):
##     """factor2 : factor"""
##     p[0] = p[1]

def p_dyad1(p):
    """dyad : expression MUL expression
            | expression DIV expression
            | expression ADD expression
            | expression SUB expression
            | expression LT expression
            | expression GT expression
            | expression LE expression
            | expression GE expression
            | expression EQ expression
            | expression NE expression
            | expression AND expression
            | expression OR expression
    """
    p[0] = ASTNode('dyad', p[1], p[2], p[3])

def p_monad1(p):
    """monad : NOT expression
             | SUB expression %prec UMINUS
    """
    p[0] = ASTNode('monad', p[1], p[2])

def p_func_call(p):
    """func_call : ID LPAREN expression_list RPAREN"""
    p[0] = ASTNode('func_call', p[1], p[3])

def p_asnum1(p):
    """asnum : LPAREN expression RPAREN"""
    p[0] = ASTNode('asnum', p[2])

def p_expression1(p):
    """expression : monad
                  | dyad
                  | func_call
                  | asnum
                  | factor
                  | factor2"""
    p[0] = p[1]

def p_frame_id_acquisition(p):
    """frame_id_ref : GET_F_NO LSTR"""
    p[0] = ASTNode('frame_id_ref', p[2])

def p_expression_list1(p):
    """expression_list : expression"""
    p[0]  = ASTNode('expression_list', p[1])

def p_expression_list2(p):
    """expression_list : expression_list COMMA expression"""
    p[1].append(p[3])
    p[0] = p[1]
    
def p_epslion(p):
    """empty :"""
    pass

## def p_list(p):
##     """list : LSQRBRACKET expressions RSQRBRACKET"""
##     p[0] = ASTNode('list', p[2])
    
def p_expressions(p):
    """expressions : expressions expression"""
    p[0] = p[1]
    p[0].append(p[2])
    
def p_expressions2(p):
    """expressions : expression"""
    p[0] = [p[1]]

    
parser = yacc.yacc(debug=0, tabmodule='ope_parser_tab')

def parse(cmdbuf, startline=1):
    global errors, errinfo

    # Initialize module level error variables
    errors = 0
    errinfo = []
    
    lexer = sk_lexer.lexer
    # TODO: fix lex.py
    lexer.lineno = startline

    ast = parser.parse(cmdbuf, lexer, 0)
    return (errors, ast, errinfo)


def parse_opebuf(buf):

    #(hdrbuf, prmbuf, cmdbuf, startline) = sk_lexer.get_skparts(buf)
    cmdbuf = buf
    prmbuf = ""
    startline = 1
    
    (errors, ast, errinfo) = parse(cmdbuf, startline=startline)

    if errors > 0:
        for errbnch in errinfo:
            errbnch.verbose = sk_lexer.mk_error(cmdbuf, errbnch, 10)

    # Make list of default params
    params = {}
    patterns = {}
    for line in prmbuf.split('\n'):
        line = line.strip()
        if '=' in line:
            try:
                (var, val) = line.split('=')
                var = var.strip().upper()
                val = val.strip()
                if not var.startswith('*'):
                    params[var] = val
                else:
                    patterns[var] = val.split(',')
            except:
                raise opeParseError("Default parameter section does not match expected format")

    res = Bunch.Bunch(ast=ast, errors=errors, errinfo=errinfo,
                      params=params, patterns=patterns)
    return res


def parse_opefile(opepath):

    in_f = open(opepath, 'r')
    buf = in_f.read()
    in_f.close()
    
    res = parse_opebuf(buf)
    res.filepath = opepath

    return res


def parse_params(parambuf):
    """Hack routine to parse a bare parameter list.
    """
    
    (errors, ast, errinfo) = parse('DOIT '+parambuf, startline=1)

    # Yuck!  Pull apart AST to get params ast
    try:
        assert(ast.tag == 'cmdlist')
        assert(len(ast.items) == 1)
        ast = ast.items[0]
        assert(ast.tag == 'abscmd')
        assert(len(ast.items) == 2)
        ast = ast.items[1]
        assert(ast.tag == 'param_list')

    except AssertionError:
        # ??  We're being silent like normal parsing
        pass

    return (errors, ast, errinfo)


    

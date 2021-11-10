#!/usr/bin/env python
#
# sk_parser.py -- SOSS Skeleton file parser
#
# Yasuhiko Sakakibara
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Oct  8 17:10:20 HST 2012
#]
#
import sys
import logging
# There are some unresolved issues with the new ply version
#import ply.yacc as yacc
#from ply.lex import LexToken
import yacc
from lex import LexToken
import sk_lexer
import sk_common
from sk_common import ASTNode
import logging
import Bunch

# !!!NOTE!!!
# *** When you update this file, you need to update the class
#     IssueAST in sk_common accordingly!! ***

class skParseError(sk_common.skError):
    pass

class skParser(object):
    
    precedence = (
        ('left', 'AND', 'OR'),
        ('right', 'NOT'),
        ('nonassoc', 'EQ', 'NE', 'GT', 'GE', 'LT', 'LE'),
        ('left', 'ADD', 'SUB'),
        ('left', 'MUL', 'DIV'),
        ('right', 'UMINUS'),         # Ficticious token, unary minus operator
    )

    def p_program1(self, p):
        """program : command_section"""
        p[0] = p[1]


    def p_command_section(self, p):
        """command_section : preamble mainpart endpart"""
        p[0] = ASTNode('command_section', p[1], p[2], p[3])

    def p_preamble1(self, p):
        """preamble : START statements"""
        p[0] = p[2]

    def p_preamble2(self, p):
        """preamble : START"""
        p[0] = ASTNode('nop')

    def p_mainpart1(self, p):
        """mainpart : MAINSTART statements MAINEND"""
        p[0] = p[2]

    def p_mainpart2(self, p):
        """mainpart : MAINSTART MAINEND"""
        p[0] = ASTNode('nop')

    def p_endpart1(self, p):
        """endpart : statements END"""
        p[0] = p[1]

    def p_endpart2(self, p):
        """endpart : END"""
        p[0] = ASTNode('nop')

    def p_statements(self, p):
        """statements : statement"""
        p[0] = p[1]

    ## def p_statements1(self, p):
    ##     """statements : statements statement"""
    ##     p[0] = p[1]
    ##     p[0].append(p[2])

    def p_statement(self, p):
        """statement : command_list"""
        p[0] = p[1]

    def p_command_list1(self, p):
        """command_list : command_list async
                        | command_list sync
        """
        p[0] = p[1]
        p[0].append(p[2])

    ## # just for debug
    ## def p_command_list2(self, p):
    ##     """command_list : command_list if_list
    ##                     | command_list while_loop
    ##                     | command_list raise
    ##                     | command_list star_if_list
    ##                     | command_list star_for_loop
    ##                     | command_list abs_command
    ##     """
    ##     p[0] = p[1]
    ##     p[0].append(p[2])

    ## def p_command_list3(self, p):
    ##     """command_list : command_list star_set_stmnt
    ##     """
    ##     p[0] = p[1]
    ##     p[0].append(p[2])


    ## def p_command_list4(self, p):
    ##     """command_list : async 
    ##                     | sync 
    ##                     | if_list
    ##                     | star_if_list
    ##                     | star_for_loop
    ##                     | while_loop
    ##                     | raise
    ##                     | abs_command
    ##                     | star_set_stmnt
    ##     """
    ##     p[0] = ASTNode('cmdlist', p[1])

    def p_command_list2(self, p):
        """command_list : command_list special_form
                        | command_list abs_command
        """
        p[0] = p[1]
        p[0].append(p[2])

    def p_command_list3(self, p):
        """command_list : async 
                        | sync 
                        | abs_command
                        | special_form
        """
        p[0] = ASTNode('cmdlist', p[1])

    def p_command_list4(self, p):
        """command_list : empty
        """
        #p[0] = ASTNode('cmdlist', ASTNode('nop'))
        p[0] = ASTNode('nop')

    def p_special_form(self, p):
        """special_form : if_list
                        | star_if_list
                        | star_for_loop
                        | while_loop
                        | raise
                        | star_set_stmnt
                        | let_stmnt
                        | set_stmnt
                        | proc_defn
        """
        p[0] = ASTNode('cmdlist', p[1])

    def p_async(self, p):
        """async : exec_command COMMA
                 | abs_command COMMA
                 | command_block COMMA
                 | proc_call COMMA
        """
        p[0] = ASTNode('async', p[1])

    def p_sync(self, p):
        """sync : exec_command SEMICOLON
                | abs_command SEMICOLON
                | command_block SEMICOLON
                | proc_call SEMICOLON
        """
        p[0] = ASTNode('sync', p[1])

    def p_command_block(self, p):
        """command_block : LCURBRACKET command_list RCURBRACKET"""
        p[0] = ASTNode('block', p[2]) 
        # avoid making a block inside a block
        p[0].items = p[2].items 

    def p_command_exec(self, p):
        """exec_command : EXEC factor factor param_list"""
        p[0] = ASTNode('exec', p[2], p[3], p[4], None)

    def p_command_exec1(self, p):
        """exec_command : ID ASSIGN EXEC factor factor param_list"""
        p[0] = ASTNode('exec', p[4], p[5], p[6], p[1])

    def p_command_abs(self, p):
        """abs_command : STAR_SUB factor param_list"""
        p[0] = ASTNode('star_sub', p[2], p[3], )

    def p_param_list1(self, p):
        """ param_list : empty"""
        p[0] = ASTNode('param_list')

    def p_param_list2(self, p):  
        """param_list : param_list key_value_pair"""
        p[1].append(p[2])
        p[0] = p[1]

    # TODO: can this be combined with the *IF rules?
    def p_if_list1_0(self, p):
        """if_list : IF expression ENDIF"""
        # empty then and ELSE clauses
        p[0] = ASTNode('nop')

    def p_if_list1_1(self, p):
        """if_list : IF expression command_list ENDIF"""
        p[0] = ASTNode('if_list', ASTNode('cond', p[2], p[3]))

    def p_if_list1_1_1(self, p):
        """if_list : IF expression command_list ELSE ENDIF"""
        # Empty ELSE clause
        p[0] = ASTNode('if_list', ASTNode('cond', p[2], p[3]))

    def p_if_list1_2(self, p):
        """if_list : IF expression command_list ELSE command_list ENDIF"""
        p[0] = ASTNode('if_list', ASTNode('cond', p[2], p[3]),
                       ASTNode('cond', True, p[5]))

    def p_if_list1_3(self, p):
        """if_list : IF expression command_list elif_list ENDIF"""
        p[0] = ASTNode('if_list', ASTNode('cond', p[2], p[3]))
        for i in p[4]:
            p[0].append(i)
        #p[0].append(p[4])

    def p_if_list1_4(self, p):
        """if_list : IF expression command_list elif_list ELSE command_list ENDIF"""
        p[0] = ASTNode('if_list', ASTNode('cond', p[2], p[3]))
        for i in p[4]:
            p[0].append(i)
        p[0].append(ASTNode('cond', True, p[6]))

    def p_elif(self, p):
        """elif : ELIF expression command_list"""
        p[0] = ASTNode('cond', p[2], p[3])

    def p_elif_list(self, p):
        """elif_list : elif"""
        p[0] = [p[1]]

    def p_elif_list2(self, p):
        """elif_list : elif_list elif"""
        p[0] = p[1]
        p[0].append(p[2])

    # TODO: can this be combined with the IF rules?
    def p_star_if_list1_1(self, p):
        """star_if_list : STAR_IF expression STAR_ENDIF"""
        # empty then and ELSE clauses
        p[0] = ASTNode('nop')

    def p_star_if_list1_2(self, p):
        """star_if_list : STAR_IF expression command_list STAR_ENDIF"""
        p[0] = ASTNode('star_if', ASTNode('cond', p[2], p[3]))

    def p_star_if_list2_1(self, p):
        """star_if_list : STAR_IF expression command_list STAR_ELSE STAR_ENDIF"""
        # Empty ELSE clause
        p[0] = ASTNode('star_if', ASTNode('cond', p[2], p[3]))

    def p_star_if_list2_2(self, p):
        """star_if_list : STAR_IF expression command_list STAR_ELSE command_list STAR_ENDIF"""
        p[0] = ASTNode('star_if', ASTNode('cond', p[2], p[3]),
                       ASTNode('cond', True, p[5]))

    def p_star_if_list3_1(self, p):
        """star_if_list : STAR_IF expression command_list star_elif_list STAR_ENDIF"""
        p[0] = ASTNode('star_if', ASTNode('cond', p[2], p[3]))
        for i in   p[4]:
            p[0].append(i)
        #p[0].append(p[4])

    def p_star_if_list3_2(self, p):
        """star_if_list : STAR_IF expression command_list star_elif_list STAR_ELSE command_list STAR_ENDIF"""
        p[0] = ASTNode('star_if', ASTNode('cond', p[2], p[3]))
        for i in p[4]:
            p[0].append(i)
        p[0].append(ASTNode('cond', True, p[6]))

    def p_star_elif(self, p):
        """star_elif : STAR_ELIF expression command_list"""
        p[0] = ASTNode('cond', p[2], p[3])

    def p_star_elif_list(self, p):
        """star_elif_list : star_elif_list star_elif"""
        p[0] = p[1]
        p[0].append(p[2])

    def p_star_elif_list2(self, p):
        """star_elif_list : star_elif"""
        p[0] = [p[1]]


    def p_key_value_pair(self, p):
        """key_value_pair : ID ASSIGN expression"""
        #p[0] = ASTNode('key_value_pair', p[1].upper(), p[3])
        p[0] = ASTNode('key_value_pair', p[1].lower(), p[3])

    def p_factor1(self, p):
        """factor : NUM"""
        if p[1].find('.') < 0:
            p[0] = ASTNode('number', int(p[1]))
        else:
            p[0] = ASTNode('number', float(p[1]))

    def p_factor2(self, p):
        """factor : IDREF""" 
        p[0] = ASTNode('id_ref', p[1][1:])

    def p_factor3(self, p):
        """factor : ALIASREF""" 
        p[0] = ASTNode('alias_ref', p[1][1:])

    def p_factor4(self, p):
        """factor : frame_id_ref"""
        p[0] = p[1]


    # This is for reserved keywords used like ordinary strings/ids
    # Grrrr!
    def p_factor6(self, p):
        """ factor : ID
                   | OR
                   | AND
        """
        p[0] = ASTNode('string', p[1])

    def p_factor7(self, p):
        """ factor : LSTR """
        #p[0] = p[1]
        p[0] = ASTNode('lstring', p[1])

    def p_factor8(self, p):
        """ factor : QSTR """
        p[0] = ASTNode('qstring', p[1])

    def p_factor9(self, p):
        """factor : REGREF""" 
        p[0] = ASTNode('reg_ref', p[1][1:])

    ## def p_factor_2_1(self, p):
    ##     """factor2 : SUB factor %prec UMINUS"""
    ##     p[0] = ASTNode('monad', p[1], p[2])

    def p_factor_2_2(self, p):
        """factor2 : ADD factor %prec UMINUS"""
        p[0] = p[2]

    ## def p_factor_2_3(self, p):
    ##     """factor2 : factor"""
    ##     p[0] = p[1]

    def p_dyad1(self, p):
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

    def p_monad1(self, p):
        """monad : NOT expression
                 | SUB expression %prec UMINUS
        """
        p[0] = ASTNode('monad', p[1], p[2])

    def p_func_call(self, p):
        """func_call : ID LPAREN arg_list RPAREN"""
        p[0] = ASTNode('func_call', p[1], p[3])

    def p_proc_call(self, p):
        """proc_call : REGREF LPAREN arg_list RPAREN"""
        p[0] = ASTNode('proc_call', p[1], p[3])

    def p_arg_list1(self, p):
        """ arg_list : expression_list COMMA kwd_params"""
        l = list(p[1].items)
        l.extend(p[3].items)
        p[0] = ASTNode('arg_list')
        p[0].items = l

    def p_arg_list2(self, p):
        """ arg_list : expression_list"""
        p[0] = ASTNode('arg_list')
        p[0].items = p[1].items

    def p_arg_list3(self, p):
        """ arg_list : kwd_params"""
        p[0] = ASTNode('arg_list')
        p[0].items = p[1].items

    def p_kwd_params1(self, p):  
        """kwd_params : key_value_pair COMMA kwd_params"""
        p[0] = ASTNode('kwd_params', p[1])
        p[0].items.extend(p[3].items)

    def p_kwd_params2(self, p):  
        """kwd_params : key_value_pair"""
        p[0] = ASTNode('kwd_params', p[1])

    ## def p_arg_list2(self, p):  
    ##     """arg_list : key_value_pair COMMA arg_list"""
    ##     p[0] = ASTNode('arg_list', p[1])
    ##     p[0].items.extend(p[3].items)

    ## def p_arg_list3(self, p):  
    ##     """arg_list : key_value_pair"""
    ##     p[0] = ASTNode('arg_list', p[1])

    def p_asnum1(self, p):
        """asnum : LPAREN expression RPAREN"""
        p[0] = ASTNode('asnum', p[2])

    def p_expression1(self, p):
        """expression : monad
                      | dyad
                      | func_call
                      | proc_call
                      | asnum
                      | factor
                      | factor2"""
        p[0] = p[1]

    def p_frame_id_acquisition(self, p):
        """frame_id_ref : GET_F_NO LSTR"""
        p[0] = ASTNode('frame_id_ref', p[2])

    def p_expression_list1(self, p):
        """expression_list : expression"""
        p[0]  = ASTNode('expression_list', p[1])

    def p_expression_list2(self, p):
        """expression_list : expression_list COMMA expression"""
        p[1].append(p[3])
        p[0] = p[1]

    def p_star_set_stmnt1(self, p):
        """star_set_stmnt : STAR_SET set_flags param_list"""
        p[0] = ASTNode('star_set', p[3], p[2])

    def p_star_set_stmnt2(self, p):
        """star_set_stmnt : STAR_SET param_list"""
        p[0] = ASTNode('star_set', p[2], None)

    def p_set_stmnt(self, 
p):
        """set_stmnt : ASN kwd_params"""
        p[0] = ASTNode('set', p[2])

    def p_set_flags1(self, p):
        """set_flags : set_flags set_flag"""
        p[0] = p[1]
        p[0].append(p[2])

    def p_set_flags2(self, p):
        """set_flags : set_flag"""
        p[0] = [p[1]]

    def p_set_flag(self, p):
        """set_flag : SUB ID"""
        p[0] = p[2]

    def p_star_for_loop1(self, p):
        """star_for_loop : STAR_FOR expression idlist IN expression command_list STAR_ENDFOR"""
        p[0] = ASTNode('star_for', p[2], p[3], p[5], p[6])

    def p_star_for_loop2(self, p):
        """star_for_loop : STAR_FOR expression idlist IN command_list STAR_ENDFOR"""
        p[0] = ASTNode('star_for', p[2], p[3], None, p[5])

    def p_star_for_loop3(self, p):
        """star_for_loop : STAR_FOR expression idlist IN STAR_ENDFOR"""
        # empty loop
        p[0] = ASTNode('star_for', p[2], p[3], None, ASTNode('nop'))

    def p_while_loop1(self, p):
        """while_loop : WHILE expression command_block"""
        p[0] = ASTNode('while', p[2], p[3])

    def p_let(self, p):
        """let_stmnt : LET kwd_params IN command_block"""
        p[0] = ASTNode('let', p[2], p[4])

    def p_proc_defn1(self, p):
        """proc_defn : DEF ID LPAREN varlist RPAREN command_block"""
        p[0] = ASTNode('proc', p[2], p[4], p[6])

    def p_raise(self, p):
        """raise : RAISE expression"""
        p[0] = ASTNode('raise', p[2])

    def p_epslion(self, p):
        """empty :"""
        pass

    def p_idlist1(self, p):
        """idlist : expressions"""
        p[0] = ASTNode('idlist', p[1])

    def p_varlist1(self, p):
        """varlist : ID"""
        p[0] = ASTNode('varlist', p[1])

    def p_varlist2(self, p):
        """varlist : varlist COMMA ID"""
        p[0] = p[1]
        p[0].append(p[3])
        
    ## def p_list(self, p):
    ##     """list : LSQRBRACKET expressions RSQRBRACKET"""
    ##     p[0] = ASTNode('list', p[2])

    def p_expressions(self, p):
        """expressions : expressions expression"""
        p[0] = p[1]
        p[0].append(p[2])

    def p_expressions2(self, p):
        """expressions : expression"""
        p[0] = [p[1]]


    # --- .OPE file commands ---
    
    def p_opecmd(self, p):
        """opecmd : exec_command
                  | abscmd
        """
        p[0] = ASTNode('cmdlist', p[1])

    def p_abscmd(self, p):
        """abscmd : factor param_list"""
        p[0] = ASTNode('abscmd', p[1], p[2], )


    def p_error(self, arg):

        self.errors += 1
        if isinstance(arg, LexToken):
            errstr = ("Parse error at line %d, token %s ('%s')" % (
                arg.lineno, arg.type, str(arg.value)))
            self.errinfo.append(Bunch.Bunch(lineno=arg.lineno, errstr=errstr,
                                            token=arg))
            self.logger.error(errstr)

            # ? Try to recover to some sensible state
            self.parser.errok()

        else:
            errstr = ("Parse error: %s" % str(arg))
            #print errstr
            self.errinfo.append(Bunch.Bunch(lineno=0, errstr=errstr, token=arg))
            self.logger.error(errstr)

            # ? Try to recover to some sensible state
            self.parser.restart()


    def __init__(self, lexer, logger=None, **kwdargs):
        
        # Share lexer tokens
        self.lexer = lexer
        self.tokens = lexer.getTokens()

        if not logger:
            logger = logging.getLogger('sk.parser')
        self.logger = logger

        self.build(**kwdargs)
        self.reset()


    def reset(self, lineno=1):
        self.errors = 0
        self.errinfo = []
        # hack
        self.result = None

        self.lexer.reset(lineno=lineno)

        
    def build(self, **kwdargs):
        self.parser = yacc.yacc(module=self, start='program',
                                logger=self.logger, **kwdargs)
        self.ope_parser = yacc.yacc(module=self, start='opecmd',
                                    logger=self.logger, **kwdargs)
        self.param_parser = yacc.yacc(module=self, start='param_list',
                                      logger=self.logger, **kwdargs)
    
   
##     def parse(cmdbuf, startline=1):
##         global errors, errinfo

##         # Initialize module level error variables
##         errors = 0
##         errinfo = []

##         lexer = sk_lexer.lexer
##         # TODO: fix lex.py
##         lexer.lineno = startline

##         ast = parser.parse(cmdbuf, lexer, 0)
##         return (errors, ast, errinfo)


    def parse(self, buf, startline=1):

        # Initialize module level error variables
        self.reset(lineno=startline)

        try:
            ast = self.parser.parse(buf, lexer=self.lexer)
            #print "errors=%d, AST=%s" % (self.errors, ast)

            # !!! HACK !!!  MUST FIX PARSER!!!
##             try:
##                 self.errinfo.pop()
##                 self.errors -= 1
##                 ast = self.result
##             except IndexError:
##                 pass
            #print ast
            #print errors, "errors"

        except Exception, e:
            # capture traceback?  Yacc tracebacks aren't that useful
            ast = ASTNode('ERROR: %s' % str(e))
            # verify errors>0 ???
            #assert(self.errors > 0)
            if self.errors == 0:
                self.errors += 1

        return (self.errors, ast, self.errinfo)


    def parse_params(self, buf):
        """Hack routine to parse a bare parameter list.
        """
        # TODO: need separate lexer? parser?

        # Initialize module level error variables
        self.reset(lineno=1)

        try:
            ast = self.param_parser.parse(buf, lexer=self.lexer)

        except Exception, e:
            # capture traceback?  Yacc tracebacks aren't that useful
            ast = ASTNode('ERROR: %s' % str(e))
            # verify errors>0
            #assert(self.errors > 0)
        
        try:
            assert(ast.tag == 'param_list')

        except AssertionError:
            # ??  We're being silent like normal parsing
            pass

        return (self.errors, ast, self.errinfo)


##     def parse_opebuf(self, buf):

##         cmdbuf = buf
##         prmbuf = ""
##         startline = 1

##         (errors, ast, errinfo) = self.ope_parser.parse(cmdbuf,
##                                                        startline=startline)

##         if errors > 0:
##             for errbnch in errinfo:
##                 errbnch.verbose = sk_lexer.mk_error(cmdbuf, errbnch, 10)

##         # Make list of default params
##         params = {}
##         patterns = {}
##         for line in prmbuf.split('\n'):
##             line = line.strip()
##             if '=' in line:
##                 try:
##                     (var, val) = line.split('=')
##                     var = var.strip().upper()
##                     val = val.strip()
##                     if not var.startswith('*'):
##                         params[var] = val
##                     else:
##                         patterns[var] = val.split(',')
##                 except:
##                     raise skParseError("Default parameter section does not match expected format")

##         res = Bunch.Bunch(ast=ast, errors=errors, errinfo=errinfo,
##                           params=params, patterns=patterns)
##         return res


    def parse_opecmd(self, buf, startline=1):

        # Initialize module level error variables
        self.reset(lineno=startline)

        try:
            ast = self.ope_parser.parse(buf, lexer=self.lexer)

        except Exception, e:
            # capture traceback?  Yacc tracebacks aren't that useful
            ast = ASTNode('ERROR: %s' % str(e))
            # verify errors>0
            assert(self.errors > 0)

        try:
            assert(ast.tag == 'cmdlist')

        except AssertionError:
            # ??  We're being silent like normal parsing
            pass

        return (self.errors, ast, self.errinfo)


    def parse_skbuf(self, buf):

        # Get the constituent parts of a skeleton file:
        # header, parameter list, command part
        (hdrbuf, prmbuf, cmdbuf, startline) = sk_common.get_skparts(buf)
        print "header", hdrbuf
        print "params", prmbuf
        print "commands", cmdbuf

        # Make a buffer of the default params in an easily parsable form
        params = {}
        param_lst = []
        patterns = {}
        lines = prmbuf.split('\n')
        while len(lines) > 0:
            line = lines.pop(0).strip()
            # skip comments and blank lines
            if line.startswith('#') or (len(line) == 0):
                continue

            # handle line continuations
            while line.endswith('\\') and (len(lines) > 0):
                line = line[:-1] + lines.pop(0).strip()

            if '=' in line:
                try:
                    idx = line.find('=')
                    var = line[0:idx].strip().upper()
                    val = line[idx+1:].strip()
                    if not var.startswith('*'):
                        params[var] = val
                        param_lst.append("%s=%s" % (var, val))
                    else:
                        patterns[var[1:]] = val.split(',')

                except Exception, e:
                    raise skParseError("Error parsing default parameter section: %s" % (str(e)))

        parambuf = ' '.join(param_lst)
        #print parambuf

        # Parse default params into an ast.
        (errors, ast_params, errinfo) = self.parse_params(parambuf)
        #print "ast_params:", ast_params.printAST()

        # This will hold the results
        res = Bunch.Bunch(errors=errors, errinfo=errinfo)

        # make readable errors
        if errors > 0:
            #print "ERRINFO = ", errinfo
            for errbnch in errinfo:
                errbnch.verbose = sk_common.mk_error(parambuf, errbnch, 1)

        # parse the command part
        (errors, ast_cmds, errinfo) = self.parse(cmdbuf, startline=startline)
        #print "ERRINFO = ", errinfo

        # Append errinfo together
        res.errors += errors
        res.errinfo.extend(errinfo)

        # make readable errors
        for errbnch in errinfo:
            errbnch.verbose = sk_common.mk_error(cmdbuf, errbnch, 10)

        res.params = params
        res.patterns = patterns

        # Finally, glue the params AST and the commands AST together to make
        # "skeleton" node
        res.ast = ASTNode("skeleton", ast_params, ast_cmds)

        # return a bundle of these objects
        return res


    def parse_skfile(self, skpath):

        in_f = open(skpath, 'r')
        buf = in_f.read()
        in_f.close()

        res = self.parse_skbuf(buf)
        res.filepath = skpath

        return res

    def parse_opebuf(self, opebuf):

        # Get the constituent parts of a skeleton file:
        # header, parameter list, command part
        (hdrbuf, prmbuf, cmdbuf, startline) = sk_common.get_opeparts(opebuf)
        print cmdbuf

        (errors, ast_params, errinfo) = self.parse_opecmd(cmdbuf,
                                                          startline=startline)

        # This will hold the results
        res = Bunch.Bunch(errors=errors, errinfo=errinfo)

        # make readable errors
        if errors > 0:
            #print "ERRINFO = ", errinfo
            for errbnch in errinfo:
                errbnch.verbose = sk_common.mk_error(cmdbuf, errbnch, 1)

        return res

    def parse_opefile(self, opepath):

        in_f = open(opepath, 'r')
        opebuf = in_f.read()
        in_f.close()

        res = self.parse_opebuf(opebuf)
        res.filepath = opepath

        return res

    
def main(options, args):

    # TODO: configure the logger
    logger = logging.getLogger('sk.parser')

    lexer = sk_lexer.skScanner(logger=logger, debug=0, lextab='scan_tab')
    
    parser = skParser(lexer, logger=logger, debug=0, tabmodule='parser_tab')

    if len(args) > 0:
        for filename in args:
            try:
                if options.ope:
                    res = parser.parse_opefile(filename)
                else:
                    res = parser.parse_skfile(filename)

                if res.errors > 0:
                    for errbnch in res.errinfo:
                        print "%d: %s (%s)" % (errbnch.lineno, errbnch.errstr,
                                               errbnch.token)
                        print errbnch.verbose
                        print ""
                    
                elif (res.ast != None) and options.verbose:
                    res.ast.printAST()

                print "%s: %d errors" % (filename, res.errors)

            except Exception, e:
                # Print error message and continue to next file
                print str(e)

    else:
        buf = sys.stdin.read()
        try:
            res = parser.parse_skbuf(buf)

            if res.errors > 0:
                for errbnch in res.errinfo:
##                     print "%d: %s (%s)" % (errbnch.lineno, errbnch.errstr,
##                                            errbnch.token)
                    print errbnch.verbose
                    print ""
                    
            elif (res.ast != None) and options.verbose:
                res.ast.printAST()
            
                print "%d errors" % (res.errors)
                print "Error info: %s" % (res.errinfo)

        except skParseError, e:
            # Print error message
            print str(e)


if __name__ == '__main__':
    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options] [file ...]"
    optparser = OptionParser(usage=usage, version=('%%prog'))
    
    optparser.add_option("--debug", dest="debug", default=False,
                         action="store_true",
                         help="Enter the pdb debugger on main()")
    optparser.add_option("--ope", dest="ope", default=False,
                         action="store_true",
                         help="Parse .ope file instead of .sk file")
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

#!/usr/bin/env python
#
# sk_lexer.py -- SOSS Skeleton file lexer
#
# Yasuhiko Sakakibara
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Oct  8 14:03:10 HST 2012
#]
#
"""
Exec TSC AG Readout=ON \
                        D_TYPE=OBJ 
                        EXPOSURE=(!VGWQ.SHG.EXPTIME_AG*$EXPTIME_FACTOR) \
                        BINNING=11 \
                        CAL_SKY=OFF \
                        CAL_DARK=OFF \
                        CAL_FLAT=OFF \
                        X1=70 \
                        Y1=70 \
                        X2=441 \
                        Y2=441 ;
	          Exec OBS Check_Status Mode=AND \
                                  Timeout=0060 \
                                  C1=[VGWD.DISP.AG NE !VGWD.DISP.AG] \
                                  C2="quoted string must be able to contain anything like <> ! $ ?";
     
    test('123.55+23.16')
"""
# There are some unresolved issues with the new ply versions
#import ply.lex as lex
#import ply.yacc as yacc
import logging
import lex
import yacc
import re
import Bunch

import sk_common

num_re = re.compile(r'^[0-9]+(\.\d*)?$')


class skScanError(sk_common.skError):
    pass

class skScanner(object):
    
    tokens = (
              'ID',
              #'CONST',
              'NUM',
              'ASSIGN',
              'NEWLINE',
              'COMMENT',
              'LPAREN',
              'RPAREN',
              'LCURBRACKET',
              'RCURBRACKET',
              'LSQRBRACKET',
              'RSQRBRACKET',
              'LCONT',
              'COMMA',
              'SEMICOLON',
              'QSTR',
              'LSTR',
              'IDREF',
              'ALIASREF',
              'REGREF',
              #'LIST',

              'EXEC',
              'LET',

              'ASN', 
              'STAR_SET', 

              'IF',
              'IN',
              'ELIF',
              'ELSE',
              'ENDIF',

              'STAR_IF',
              'STAR_ELIF',
              'STAR_ELSE',
              'STAR_ENDIF',

              'WHILE',
              'RAISE',
              'DEF',
              'RETURN',

              'STAR_SUB',

              'STAR_FOR',
              'STAR_ENDFOR',
              'GET_F_NO',
              'START',
              'MAINSTART',
              'MAINEND',
              'END',
              # operators
              'MUL',
              'ADD',
              'SUB',
              'DIV',
              # relationals
              'EQ',
              'NE',
              'GT',
              'GE',
              'LT',
              'LE',
              # logicals
              'AND',
              'OR',
              'NOT',
              )

    reserved_map = {
              'EXEC'   : 'EXEC',
              'ASN'    : 'ASN',
              'IF'     : 'IF',
              'AND'    : 'AND',
              'OR'     : 'OR',
              'NOT'    : 'NOT',
              'IN'     : 'IN',
              'ELIF'   : 'ELIF',
              'ELSE'   : 'ELSE',
              'ENDIF'  : 'ENDIF',
              'WHILE'  : 'WHILE',
              'RAISE'  : 'RAISE',
              'DEF'    : 'DEF',
              'RETURN' : 'RETURN',
              'LET'    : 'LET',
              ':START'  : 'START',
              ':MAIN_START' : 'MAINSTART',
              ':MAIN_END' : 'MAINEND',
              ':END'    : 'END',
    } 

    t_ignore = ' \t'

    t_START     = r'(?i)\:START'
    t_MAINSTART = r'(?i)\:MAIN_START'
    t_END       = r'(?i)\:END'
    t_MAINEND   = r'(?i)\:MAIN_END'
    t_NUM       = r'[0-9]+(\.\d*)?'
    t_EQ        = r'=='
    t_NE        = r'\!='
    t_GT        = r'\>'
    t_GE        = r'\>='
    t_LT        = r'\<'
    t_LE        = r'\<='
    t_ASSIGN    = r'='
    t_SEMICOLON = r';'
    t_COMMA     = r','
    t_LPAREN    = r'\('
    t_RPAREN    = r'\)'
    t_LCURBRACKET = r'{'
    t_RCURBRACKET = r'}'
    t_LSQRBRACKET = r'\['
    t_RSQRBRACKET = r'\]'
    t_ADD       = r'\+'
    t_SUB       = r'\-'
    t_MUL       = r'\*'
    t_DIV       = r'\/'
    t_GET_F_NO  = r'(?i)&GET_F_NO'

    t_STAR_IF     = r'(?i)\*IF'
    t_STAR_ENDIF  = r'(?i)\*ENDIF'
    t_STAR_ELIF   = r'(?i)\*ELIF'
    t_STAR_ELSE   = r'(?i)\*ELSE'
    t_STAR_SET    = r'(?i)\*SET'
    t_STAR_SUB    = r'(?i)\*SUB'
    t_STAR_FOR    = r'(?i)\*FOR'
    t_STAR_ENDFOR = r'(?i)\*ENDFOR'

    #t_ALIASREF  = r'![\w_][\w\d_\.]*'    # 'Status' reference
    def t_ALIASREF(self, t):
        r'![\w_][\w\d_\.]*'
        # 'Status' reference: strip off the '!'
        #t.value = t.value[1:]
        return t

    #t_IDREF     = r'\$[\w_][\w\d_\.]*'   # 'Variable' reference
    def t_IDREF(self, t):
        r'\$[\w_][\w\d_\.]*'
        # 'Variable' reference: strip off the '$'
        #t.value = t.value[1:]
        return t

    #t_REGREF     = r'\@[\w_][\w\d_\.]*'  # 'Register' reference
    def t_REGREF(self, t):
        r'\@[\w_][\w\d_\.]*'
        # 'Register' reference: strip off the '@'
        #t.value = t.value[1:]
        return t

    def t_ID(self, t):
        #r'''[a-zA-Z0-9][a-zA-Z0-9_\.\:\-]*'''
        r'''[a-zA-Z0-9][a-zA-Z0-9_\.\:]*'''

        # t_NUM unfortunately overlaps with t_ID, due to the bad specification
        # of the SOSS language, therefore we check if the item is all number
        # here and convert the token type as necessary.
        if num_re.match(t.value):
            t.type = 'NUM'
            return t

        t.value = t.value.upper()
        #tok = t.value.upper()
        tok = t.value
        if self.reserved_map.has_key(tok):
            t.type = self.reserved_map[tok]
            # Convert lower case to upper
            #t.value = tok
        return t

    #(((\"[^\"]*?\")?[^ \t\n\"]+)+)|(((\"[^\"]*?\")[^\t\n\"]*)+)
    ## def t_ID(self, t):
    ##     r'''(((\"[^\"]*?\")?[^ \t\n\"]+)+)|(((\"[^\"]*?\")[^\t\n\"]*)+)'''
    ##     tok = t.value.upper()
    ##     if reserved_map.has_key(tok):
    ##         t.type = reserved_map[tok]
    ##         # Convert lower case to upper
    ##         t.value = tok
    ##     return t

    # Quoted string will not be an ID
    def t_QSTR(self, t):
        r'"[^"]*"'
        # Just strip off the quotes
        t.value = t.value[1:-1]
        return t

    # List string is yet another kind of string
    def t_LSTR(self, t):
        r'\[[^\]]*\]'
        # Just strip off the quotes
        t.value = t.value[1:-1]
        return t

    def t_LCONT(self, t):
        r'\\\n'
        #print 'LCONT'
        #t.lineno += 1
        self.lexer.lineno += 1

    def t_COMMENT(self, t):
        r'\#.*\n'
        #t.lineno += 1
        self.lexer.lineno += 1

    ## def t_STAR_SET(self, t):
    ##     r'(?i)\*SET.*\n'
    ##     t.value = t.value[4:-1]
    ##     t.lineno += 1
    ##     return t

    ## def t_SET(self, t):
    ##     r'(?i)SET\s*.*\n'
    ##     t.value = t.value[3:-1]
    ##     t.lineno += 1
    ##     return t

    ## def t_IN(self, t):
    ##     r'(?i)IN\s*.*\n'
    ##     t.value = t.value[2:-1]
    ##     t.lineno += 1
    ##     return t

    def t_NEWLINE(self, t):
        r'\n+'
        #t.lineno += t.value.count('\n')
        self.lexer.lineno += t.value.count('\n')
        #return t

    # Error handling rule
    def t_error(self, t):
        errstr = ("Scan error at line %d, character ('%s')" % (
            t.lineno, t.value[0]))
        #print errstr
        self.errinfo.append(Bunch.Bunch(lineno=t.lineno, errstr=errstr,
                                        token=t))
        self.errors += 1
        t.skip(1)


    def build(self, **kwdargs):
        #lexer = lex.lex(debug=0, lextab='sk_lexer_tab')
        self.lexer = lex.lex(object=self, **kwdargs)

    def __init__(self, logger=None, **kwdargs):

        if not logger:
            logger = logging.getLogger('sk.lexer')
        self.logger = logger
        
        self.build(**kwdargs)
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

        return (self.errors, res, self.errinfo)


    def scan_skbuf(self, buf):

        (hdrbuf, prmbuf, cmdbuf, startline) = sk_common.get_skparts(buf)

        (errors, tokens, errinfo) = self.tokenize(cmdbuf,
                                                  startline=startline)

        if errors > 0:
            for errbnch in errinfo:
                errbnch.verbose = sk_common.mk_error(cmdbuf, errbnch, 10)

        res = Bunch.Bunch(tokens=tokens, errors=errors, errinfo=errinfo)
        return res


    def scan_skfile(self, skpath):

        in_f = open(skpath, 'r')
        buf = in_f.read()
        in_f.close()

        res = self.scan_skbuf(buf)
        res.filepath = skpath

        return res


def printTokens(tokens):
    for token in tokens:
        print token

        
def main(options, args):

    # TODO: configure the logger
    logger = logging.getLogger('sk_lexer')

    # Create the scanner
    scanner = skScanner(logger=logger, debug=0, lextab='scan_tab')
    
    if len(args) > 0:
        for filename in args:
            try:
                res = scanner.scan_skfile(filename)

                if res.errors > 0:
                    for errbnch in res.errinfo:
                        print errbnch.verbose
                        print ""
                    
                elif (res.tokens != None) and options.verbose:
                    printTokens(res.tokens)

                print "%s: %d errors" % (filename, res.errors)

            except skScanError, e:
                # Print error message and continue to next file
                print str(e)

    else:
        buf = sys.stdin.read()
        try:
            res = scanner.scan_skbuf(buf)

            if res.errors > 0:
                for errbnch in res.errinfo:
                    print errbnch.verbose
                    print ""
                    
            elif (res.tokens != None) and options.verbose:
                printTokens(res.tokens)
            
                print "%d errors" % (res.errors)

        except skScanError, e:
            # Print error message
            print str(e)


if __name__ == '__main__':
    import sys
    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage, version=('%%prog'))
    
    parser.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    parser.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    parser.add_option("-v", "--verbose", dest="verbose", default=False,
                      action="store_true",
                      help="Turn on verbose output")

    (options, args) = parser.parse_args(sys.argv[1:])

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

#! /usr/bin/env python
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Jul 17 16:30:01 HST 2009
#]
#
"""
Program to get the list of status aliases used by an instrument in SOSS
compatibility mode.  Run like this:

    $ ./get_statusAliases.py --ins=SPCAM

You can further restrict the scan by judicious use of --mode and --file
flags.  These work the same as for testfunc_sk_parser (whose classes this
program makes use of).

The aliases are sorted into alphabetical order and printed in a long list
at the end.

NOTE: the list will only be accurate if there are NO scanning or parsing
errors!!
"""
import sys
import pprint
from testfunc_sk_parser import TestSkLexer, TestSkParser
from sk_common import ASTNode
import ssdlog

class GetAliasesLexer(TestSkLexer):
    
    def __init__(self, *args, **kwdargs):
        super(GetAliasesLexer, self).__init__(*args, **kwdargs)

        self.aliases = set([])
        
    def processFile(self, skfile, func=None):
        try:
            res = self.fn(skfile)

            for token in res.tokens:
                if token.type == 'ALIASREF':
                    self.aliases.add(token.value[1:])

            if res.errors > 0:
                self.printerrors(res.errinfo)
            return res.errors

        except sk_lexer.skScanError, e:
            errmsg = "File (%s) contents do not match expected format" % \
                     skfile
            print errmsg
            return 1


class GetAliasesParser(TestSkParser):
    
    def __init__(self, *args, **kwdargs):
        super(GetAliasesParser, self).__init__(*args, **kwdargs)

        self.aliases = set([])
        
    def processFile(self, skfile, func=None):
        try:
            res = self.fn(skfile)

            if res.errors > 0:
                self.printerrors(res.errinfo)
                return res.errors
        
        except sk_lexer.skScanError, e:
            errmsg = "File (%s) contents do not match expected format" % \
                     skfile
            print errmsg
            return 1

        # Sanity check that result is a sk file
        assert(res.ast.tag == 'skeleton')
        ast_default_params = res.ast.items[0]

        # Sanity check that it has a default parameter list
        assert(ast_default_params.tag == 'param_list')

        # Scan the parameter list for any default values that are
        # status aliases and add them to the set of all aliases found.
        for ast in ast_default_params.items:
            assert(ast.tag == 'key_value_pair')
            var = ast.items[0]
            val = ast.items[1]

            if isinstance(val, ASTNode) and (val.tag == 'alias_ref'):
                self.aliases.add(val.items[0])

        #print ast_default_params

        return 0


if __name__ == "__main__":
    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optparser = OptionParser(usage=usage, version=('%%prog'))
    
    optparser.add_option("--skbase", dest="skbase", default='../SkPara/sk',
                         help="Specify base skeleton file directory")
    optparser.add_option("--ins", dest="ins", default='*',
                         help="Specify instrument to run tests")
    optparser.add_option("--mode", dest="mode", default='*',
                         help="Specify mode for skeleton files")
    optparser.add_option("--file", dest="file", default='*.sk',
                         help="Specify particular skeleton file(s)")
    ssdlog.addlogopts(optparser)

    (options, args) = optparser.parse_args(sys.argv[1:])

    #unittest.main()

    # Create top level logger.
    logger = ssdlog.make_logger('testlogger', options)

    test_s = GetAliasesLexer(logger=logger)
        
    test_s.setUp()
    test_s.manual_test(options.ins, options.mode, options.file, None)
    test_s.tearDown()

    test_p = GetAliasesParser(logger=logger)
    test_p.aliases = test_s.aliases
        
    test_p.setUp()
    test_p.manual_test(options.ins, options.mode, options.file, None)
    test_p.tearDown()

    aliases = list(test_p.aliases)
    aliases.sort()

    print ""
    print "Aliases used:"
    for alias in aliases:
        print alias
        
    
# END

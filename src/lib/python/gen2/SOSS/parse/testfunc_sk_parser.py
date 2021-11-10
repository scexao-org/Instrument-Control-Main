#!/usr/bin/env python

import unittest
import glob
import sys, os, stat
import logging, ssdlog

import sk_common
import sk_lexer, sk_parser, sk_interp

skbase = '../SkPara/sk'

# Fake status needed for tests
fakeStatus = {
        'STATL.TSC_F_SELECT': 'NS_IR',
        'FITS.VGW.IMGROT_FLG': '00',
        'VGWQ.AGP.ABS.RA': '123645.917',
        'VGWQ.AGP.ABS.DEC': '+623151.17',
        'VGWQ.AGP.EQUINOX': '2000.0',
        'STATS.RA': '010645.101',
        'STATS.DEC': '+194643.01',
        'STATS.EQUINOX': '2000.0000',
        'FITS.SBR.MAINOBCP': 'IRCS',
        'VGWQ.AGE.SKYLVL': '3192.1',
        'TSCL.Z': '7.35',
        'TSCL.INSROTPA': '71.834478',
    }


class Framework(unittest.TestCase):

    def __init__(self, *args, **kwdargs):
        if kwdargs.has_key('logger'):
            self.logger = kwdargs['logger']
            del kwdargs['logger']
        else:
            self.logger = logging.getLogger('testlogger')

        self.totalErrors = 0
        self.errorFiles = []

        if kwdargs.has_key('skbase'):
            self.skbase = kwdargs['skbase']
            del kwdargs['skbase']
        else:
            self.skbase = skbase

        super(Framework, self).__init__(*args, **kwdargs)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def runTest(self):
        pass

    def setparser(self, fn):
        self.fn = fn

    def printerrors(self, errinfo):
        for errbnch in errinfo:
            print errbnch.verbose

    def summarize_errors(self):
        print "------------------------------------"
        print "Files with errors:"
        
        for filename in self.errorFiles:
            print filename

        print ""
        print "TOTAL ERRORS: %d" % self.totalErrors

    def processFile(self, skfile, func=None):
        try:
            res = self.fn(skfile)

            if res.errors > 0:
                self.errorFiles.append(skfile)
                self.totalErrors += res.errors
                
                self.printerrors(res.errinfo)

            if func:
                func(res)

            return res.errors

        except (sk_lexer.skScanError, sk_common.skError), e:
            errmsg = "File (%s) contents do not match expected format" % \
                     skfile
            print errmsg
            return 1

    def recurseFilesMode(self, ins, mode, file, func=None):
        totalErrors = 0
        print self.skbase
        
        for skpath in glob.glob('%s/%s/%s/%s' % (self.skbase, ins, mode, file)):
            pfx, skfile = os.path.split(skpath)
            pfx, obe_mode = os.path.split(pfx)
            pfx, obe_id = os.path.split(pfx)
            sys.stdout.write("%8s/%s/%s: " % (obe_id, obe_mode, skfile))
            sys.stdout.flush()
            st = os.stat(skpath)
            if st[stat.ST_SIZE] > 250000:
                print "huge file--skipping"
                continue

            if func:
                def capfunc(res):
                    return func(obe_id, obe_mode, skfile, res)
            else:
                capfunc = None
            
            res = self.processFile(skpath, func=capfunc)
            totalErrors += res
            print "%d errors" % res

        return totalErrors
                        
    def recurseFilesInst(self, ins, func=None):
        totalErrors = 0
        
        for skdir in glob.glob('%s/%s/*' % (self.skbase, ins)):
            if os.path.isdir(skdir):
                pfx, mode = os.path.split(skdir)
                print "    %s:" % mode
                totalErrors += self.recurseFilesMode(ins, mode, '*.sk',
                                                     func=func)

        return totalErrors
                        
    def recurseFiles(self, func=None):
        totalErrors = 0
        
        for dir in glob.glob('%s/*' % (self.skbase)):
            if os.path.isdir(dir):
                print "%s:" % dir
                pfx, ins = os.path.split(dir)
                totalErrors += self.recurseFilesInst(ins, func=func)

        return totalErrors
                        

class TestSkLexer(Framework):

    def __init__(self, *args, **kwdargs):
        super(TestSkLexer, self).__init__(*args, **kwdargs)

    def setUp(self):
        lexer = sk_lexer.skScanner(debug=0, lextab='scan_tab',
                                   logger=self.logger)
        self.setparser(lexer.scan_skfile)

    def testLexer(self):
        errors = self.recurseFiles()
        self.summarize_errors()
        
    def manual_test(self, ins, mode, file, outdir):

        def saveTokens(ins, mode, file, res):
            name, ext = os.path.splitext(file)

            tokfile = ('%s_%s_%s.tokens' % (ins, mode, name))
            tokpath = '%s/%s' % (outdir, tokfile)

            out_f = open(tokpath, 'w')
            out_f.write('\n'.join(map(str, res.tokens)))
            out_f.close()

        if outdir:
            func = saveTokens
        else:
            func = None
            
        errors = self.recurseFilesMode(ins, mode, file, func=func)
        self.summarize_errors()
        

class TestSkParser(Framework):

    def setUp(self):
        lexer = sk_lexer.skScanner(debug=0, lextab='scan_tab',
                                   logger=self.logger)
        parser = sk_parser.skParser(lexer, debug=0,
                                    tabmodule='parser_tab',
                                    logger=self.logger)
        self.setparser(parser.parse_skfile)

    def testParser(self):
        errors = self.recurseFiles()
        self.summarize_errors()
        
    def manual_test(self, ins, mode, file, outdir):

        def saveParseTree(ins, mode, file, res):
            name, ext = os.path.splitext(file)

            prsfile = ('%s_%s_%s.ptree' % (ins, mode, name))
            prspath = '%s/%s' % (outdir, prsfile)

            out_f = open(prspath, 'w')
            out_f.write(str(res.ast))
            out_f.close()

        if outdir:
            func = saveParseTree
        else:
            func = None
            
        errors = self.recurseFilesMode(ins, mode, file, func=func)
        self.summarize_errors()
        

class TestSkDecoder(Framework):

    def setUp(self):
        lexer = sk_lexer.skScanner(debug=0, lextab='scan_tab',
                                   logger=self.logger)
        self.parser = sk_parser.skParser(lexer, debug=0,
                                         tabmodule='parser_tab',
                                         logger=self.logger)
        self.sk_bank = sk_interp.skBank(self.skbase)

        variable_resolver = sk_interp.VariableResolver({})
        register_resolver = sk_interp.RegisterResolver()
        status_resolver = sk_interp.MockStatusResolver(fakeStatus)
        frame_source = sk_interp.MockFrameSource()

        self.eval = sk_interp.Evaluator(variable_resolver, register_resolver,
                                        status_resolver, frame_source,
                                        self.logger)
        

    def processFile(self, skfile):
        try:
            res = self.parser.parse_skfile(skfile)
            #self.assertEquals(errors, 0)
            if res.errors > 0:
                # => there were parse errors
                self.printerrors(res.errinfo)
                return res.errors

        except sk_lexer.skScanError, e:
            errmsg = "File (%s) contents do not match expected format" % \
                     skfile
            print errmsg
            return 1

        assert(res.ast.tag == 'skeleton')
        ast_default_params = res.ast.items[0]
        ast_body = res.ast.items[1]
        
        # Evaluate default parameters
        params = self.eval.set_params(ast_default_params)
        
        decoder = sk_interp.Decoder(self.eval, self.sk_bank,
                                    self.logger)
        try:
            newast = decoder.decode(ast_body, self.eval)

            # no errors!
            return 0

        except (AssertionError, sk_interp.skError), e:
            print "Decoder error: %s" % str(e)
            return 1

    def testDecoder(self):
        errors = self.recurseFiles()
        self.summarize_errors()
        
    def manual_test(self, ins, mode, file, outdir):
        errors = self.recurseFilesMode(ins, mode, file)
        self.summarize_errors()
        

if __name__ == "__main__":
    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optparser = OptionParser(usage=usage, version=('%%prog'))
    
    optparser.add_option("--skbase", dest="skbase", default=skbase,
                         help="Specify base skeleton file directory")
    optparser.add_option("--ins", dest="ins", default='*',
                         help="Specify instrument to run tests")
    optparser.add_option("--mode", dest="mode", default='*',
                         help="Specify mode for skeleton files")
    optparser.add_option("--file", dest="file", default='*.sk',
                         help="Specify particular skeleton file(s)")
    optparser.add_option("--outdir", dest="outdir", default=None,
                         help="Specify output directory for results")
    optparser.add_option("--test", dest="test", default='parse',
                         help="Specify scan|parse|decode")
    ssdlog.addlogopts(optparser)

    (options, args) = optparser.parse_args(sys.argv[1:])

    #unittest.main()

    # Create top level logger.
    logger = ssdlog.make_logger('testlogger', options)

    if options.test == 'scan':
        print "TEST IS SCANNING"
        test = TestSkLexer(logger=logger, skbase=options.skbase)
    elif options.test == 'parse':
        print "TEST IS SCANNING/PARSING"
        test = TestSkParser(logger=logger, skbase=options.skbase)
    elif options.test == 'decode':
        print "TEST IS SCANNING/PARSING/DECODING"
        test = TestSkDecoder(logger=logger, skbase=options.skbase)
    else:
        print "Unknown test: '%s'" % options.test
        sys.exit(1)
        
    test.setUp()
    test.manual_test(options.ins, options.mode, options.file,
                     options.outdir)
    test.tearDown()
    
#END

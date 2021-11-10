#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# jacat.py -- babelfishing translator/server
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Apr 14 11:35:24 HST 2008
#]
#
# THIS IS A WORK IN PROGRESS!

import sys, os, getopt
import SocketServer
import SimpleXMLRPCServer
import xmlrpclib
import httplib, urllib
import re, string
import codecs, fileinput
# Needed for EUC-JP encodings widely used at Subaru Telescope.
#import japanese
#japanese.register_aliases()

version = '20080414.0'

# Dictionary of available translation languages:
#
__languages = { 'english'   : 'en',
                'french'    : 'fr',
                'spanish'   : 'es',
                'german'    : 'de',
                'italian'   : 'it',
                'portugese' : 'pt',
                'japanese'  : 'ja',
              }

def _is_unicode(x):
    return 1

# Do multipart/form-data encoding.  (query) is a dict containing the form fields
# and their values.  (boundary) is a string to use as the multipart MIME-encoded
# boundary between elements.  Returns the encoded query.
#
def mimeencode(query, boundary):

    if hasattr(query,"items"):
        # mapping objects
        query = query.items()

    crlf = "\r\n"
    res = "--" + boundary
    for k, v in query:
        res = res + crlf
        res = res + ("Content-Disposition: form-data; name=\"%s\"" % str(k)) + crlf
        if isinstance(v, str):
            res = res + crlf + str(v) + crlf
        elif _is_unicode(v):
            res = res + "Content-Type: text/plain; Charset=UTF-8" + crlf
            res = res + "Content-Transfer-Encoding: 8bit" + crlf
            res = res + crlf + v.encode('utf8') + crlf
        res = res + "--" + boundary
    res = res + "--" + crlf
    return res

def clean(text):
#    return text.replace("\n", ' ')
    return text

#  Calling translate() can raise the following exceptions:
#
class BabelfishError(Exception):
    pass
class LanguageNotAvailableError(BabelfishError):
    pass
class BabelfishChangedError(BabelfishError):
    pass
class BabelfishIOError(BabelfishError):
    pass

# Make a call to Babelfish to translate up to 150 words of text.
# Returns the HTML that is returned by Babelfish.
#
def translate2html(phrase, from_lang, to_lang):

    try:
        from_code = __languages[from_lang.lower()]
        to_code = __languages[to_lang.lower()]
    except KeyError, lang:
        raise LanguageNotAvailableError(lang)

    #  All of the available language names.
    #available_languages = [ x.title() for x in languages.keys() ]
    
    url = 'http://babelfish.altavista.com/babelfish/tr'
#    url = 'http://localhost/cgi-bin/cgitest.cgi'
##     url = 'http://www.systranet.com/systran/net'
    phrase = clean(phrase)

    boundary = "AaBB03x"
    params = mimeencode( { 'doit' : 'done',
                          'intl' : '1',
                          'tt' : 'urltext',
                          'urltext' : phrase,
                          'lp' : from_code + '_' + to_code }, boundary )

#    print params
    try:
        headers = {
#            "User-Agent": "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.6) Gecko/20040413 Debian/1.6-5",
            "Content-Type": ("multipart/form-data; boundary=%s" % boundary),
            "Accept": "text/html",
            "Accept-Charset": "ISO-8859-1,utf-8" }
        Cn = httplib.HTTPConnection("babelfish.altavista.com")
        Cn.request("POST", "/babelfish/tr", params, headers)
        response = Cn.getresponse()
        html = response.read()
        Cn.close()
    except IOError, what:
        raise BabelfishIOError("Couldn't talk to server: %s" % what)
    except:
        print "Unexpected error:", sys.exc_info()[0]

    return html

# Various patterns I have encountered in looking for the babelfish result.
# We try each of them in turn, based on the relative number of times I've
# seen each of these patterns.  $1.00 to anyone who can provide a heuristic
# for knowing which one to use.   This includes AltaVista employees.
where = [
    re.compile(ur'div style=padding:10px;>([^<]*)'),
    re.compile(ur'name=\"q\">([^<]*)'),
    re.compile(ur'td bgcolor=white>([^<]*)'),
    re.compile(ur'<\/strong><br>([^<]*)')
    ]

def translate(phrase, from_lang, to_lang):
    global where

    html = translate2html(phrase, from_lang, to_lang)

    # Scan the result HTML and extract the translated phrase.
    for regex in where:
        match = regex.search(html)
        if match: break
    if not match:
#      print "=== BabelFish Returned ===\n", html, "\n=========================="
      raise BabelfishChangedError("Can't recognize translated string.")

    res = clean(unicode(match.group(1)))
    return res


def translate_Ccode(Csourcecode, from_lang, to_lang):

    # This function is called when there is a C comment match; we translate
    # the comment and return the replacement string.
    #   matchobj: a match object that matched the comment.
    #
    def trans (text):
        try:
            result = translate(text, from_lang, to_lang)

        except Exception, e:
            # If error, just flag it and continue
#            print "error is %s" % e
            result = u"(TRANSLATION_ERROR) %s" % text

        return result
        
    def subst_cmt (matchobj):

        pat2 = re.compile(ur'^(J\s+)(.+)$')
        
        # Get the text inside the comment characters.
        comment = unicode(matchobj.group(1))

        # If this is a multiline comment, then split it up.
        if comment.count(u"\n") == 0:
            result = trans(comment)
        else:
            # Multi-line comment.  Scan through it, looking for structured comments
            # as seen in the headers of Fujitsu OCS code.  Only translate sections
            # that have a "J" prefix at the beginning of the line.
            result = u""
            jcmt = u""
            for icmt in comment.split(u"\n"):
                match = pat2.match(icmt)
                if not match:
                    if jcmt != u"":
                        tres = u"T " + trans(jcmt) + u"\n" + icmt + u"\n"
                        jcmt = u""
                    else:
                        tres = u"" + icmt + u"\n"
                    result = result + tres
                else:
                    jcmt = jcmt + match.group(2) + u" "

            if jcmt != u"":
                result = result + u"T " + trans(jcmt) + u"\n"
                
        res = u"/* " + result + u" */"
        return res

    # Create a compiled regex for comment matching and use it to
    # do substitutions over the entire file.
    pat = re.compile(ur'/\*(.+?)\*/', re.DOTALL)
    tsource = pat.sub(subst_cmt, Csourcecode)

    return tsource

def translate_SHcode(SHsourcecode, from_lang, to_lang):

    # This function is called when there is a shell script comment
    # match; we translate the comment and return the replacement string.
    #   matchobj: a match object that matched the comment.
    #
    def trans (text):
        try:
            result = translate(text, from_lang, to_lang)

        except Exception, e:
            # If error, just flag it and continue
#            print "error is %s" % e
            result = "(TRANSLATION_ERROR) %s" % text

        return result
        
    def subst_cmt (matchobj):

        pat2 = re.compile(ur'^(J\s+)(.+)$')
        
        # Get the text inside the comment characters.
        comment = matchobj.group(1)
        # This seems to be necessary otherwise we get ASCII conversion exceptions:
        result = trans(comment)
                
        res = u"# " + result
        return res

    # Create a compiled regex for comment matching and use it to
    # do substitutions over the entire file.
    pat = re.compile(ur'#(.+?)$', re.DOTALL | re.MULTILINE)
    tsource = pat.sub(subst_cmt, SHsourcecode)

    return tsource

# Dictionary of available translation filters:
#
__translation_filters = { "debug": translate2html,
                          "C": translate_Ccode,
                          "sh": translate_SHcode,
                          "text": translate
                          }

class RPCHandler:
    def print_arg(self, arg):
        print arg
        return arg

    def translate(self, text, from_lang, to_lang):
        # XML-RPC only allows 7-bit data (??).  Decode using unquote to allow
        # passing of unicode and other character encodings.
        text = urllib.unquote(text)

        # Attempt a Babelfish translation.  If it fails, just return the
        # original string.
        try:
            result = translate(text, from_lang, to_lang)
        except:
            result = text

        # encode result for return trip across XML-RPC 
        result = urllib.quote(result)
        return result

    def rtn_arg(self, arg):
        return arg

    def quit(self):
        global quit
        quit = 1
        return 1


usage = """\
Usage: jacat [--port=] [--server]
       jacat [--from=<lang>] [--to=<lang>] [--type=text|C|sh] [file ...]
"""


def main(options, args):
    
    # Server mode.
    if options.server:
        server = SimpleXMLRPCServer.SimpleXMLRPCServer(("localhost",
                                                        options.port))
        server.register_introspection_functions()
        server.register_instance(RPCHandler())

        global quit
        quit = 0
        while not quit:
            server.handle_request()
        print "Server shutting down..."
	sys.exit(0)

    # Get text to translate. Read from stdin if file not given as an argument.
    argc = len(args)
    if argc == 0:
        args = ['-']

    # Get codec handlers.
    (encode, indecode, inreader, writer) = codecs.lookup(options.input_encoding)
    (outencode, decode, reader, outwriter) = codecs.lookup(options.output_encoding)

    # Select input translation filter engine:
    if __translation_filters.has_key(options.type):
        transfn = __translation_filters[options.type]
    else:
        raise BabelfishError("Not a supported translation type: %s" %
                             options.type)
        sys.exit(1)

    # If there is a single output filename, open it now.
    outname = "-"
    if options.output:
        if options.output == '-':
            outfile = outwriter(sys.stdout)
        else:
            try:
                outname = options.output
                outfile = outwriter(open(outname, "w"))
            except IOError, e:
                sys.stderr.write("Error opening output file: " + str(e) + "\n")
                sys.stderr.write("Quitting...\n")
                sys.exit(1)

    # Iterate over filenames, translating each.
    for filename in args:
        if options.verbose:
            sys.stderr.write("Translating " + filename + " ...\n")
            
        # Open input file.  Read from stdin if file not specified.
        if filename == '-':
            infile = inreader(sys.stdin)
        else:
            try:
                infile = inreader(open(filename, "r"))
            except IOError, e:
                sys.stderr.write("Error opening file: " + str(e) + "\n")
                sys.stderr.write("Skipping file...\n")
                continue

        # Read in the file in its native encoding and re-encode it into
        # Unicode.  That way we don't have to mess around all over the place
        # checking, decoding and encoding and converting back and forth.
        text = infile.read()

        if filename != "-":
            infile.close()

        # Get translation result.
        result = (transfn)(text, options.fromlang, options.tolang)

        # Open output if using individual names.
        if not options.output:
            if filename != '-':
                (fn, sfx) = os.path.splitext(filename)
                from_code = __languages[options.tolang.lower()]
                outname = fn + "." + from_code + sfx

                try:
                    outfile = outwriter(open(outname, "w"))
                except IOError, e:
                    sys.stderr.write("Error opening file: " + str(e) + "\n")
                    sys.stderr.write("Skipping file...\n")
                    continue
            else:
                outfile = outwriter(sys.stdout)

        outfile.write(result)
        outfile.flush()

        if outname != "-":
            outfile.close()

## # Defaults
## opt = {}
## opt['from'] = 'japanese'
## opt['to'] = 'english'
## opt['input-encoding'] = 'euc-jp'
## opt['output-encoding'] = 'utf-8'
## opt['type'] = 'text'
## opt['port'] = '8087'

## # Command line options.  List of lists.  Each sublist gives the short
## # form and equivalent long form.  Append ":" in short forms and "=" in
## # long forms to indicate that the option takes a parameter.
## options = [['', 'debug'], ['h', 'help'], ['', 'profile'],
##            ['f:', 'from='], ['t:', 'to='],
##            ['o:', 'output='], ['k:', 'type='],
##            ['e:', 'input-encoding='], ['g:', 'output-encoding='],
##            ['s', 'server'], ['p:', 'port='], ['v', 'verbose']
##            ]

###################################################################
# MAIN PROGRAM
#
if __name__ == '__main__':
    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    parser.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    parser.add_option("--from", dest="fromlang", metavar="LANG",
                      default="japanese",
                      help="Use LANG as the source language")
    parser.add_option("--input-encoding", dest="input_encoding",
                      metavar="ENCODING",
                      default="euc-jp",
                      help="Use ENCODING as the input encoding")
    parser.add_option("--log", dest="logfile", metavar="FILE",
                      help="Write logging output to FILE")
    parser.add_option("--loglevel", dest="loglevel", metavar="LEVEL",
                      type="int", default=0,
                      help="Set logging level to LEVEL")
    parser.add_option("--numthreads", dest="numthreads", type="int",
                      help="Use NUM threads in thread pool", metavar="NUM")
    parser.add_option("--output", dest="output",
                      metavar="FILE", default=None,
                      help="Use FILE as the output file")
    parser.add_option("--output-encoding", dest="output_encoding",
                      metavar="ENCODING",
                      default="utf-8",
                      help="Use ENCODING as the output encoding")
    parser.add_option("--port", dest="port", metavar="NUM",
                      type="int", default=8087,
                      help="Use port NUM")
    parser.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    parser.add_option("--server", dest="server", default=False,
                      action="store_true",
                      help="Be a server for translation requests")
    parser.add_option("--stderr", dest="logstderr", default=False,
                      action="store_true",
                      help="Copy logging also to stderr")
    parser.add_option("--to", dest="tolang", metavar="LANG",
                      default="english",
                      help="Use LANG as the destination language")
    parser.add_option("--type", dest="type", metavar="TYPE",
                      default="text",
                      help="Use text|C|sh as the type of input")
    parser.add_option("-v", "--verbose", dest="verbose", default=False,
                      action="store_true",
                      help="Be verbose")

    (options, args) = parser.parse_args(sys.argv[1:])

    if len(args) <= 0:
        parser.error("incorrect number of arguments")


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

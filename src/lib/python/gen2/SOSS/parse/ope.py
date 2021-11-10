#!/usr/bin/env python
#
# ope.py -- helper code for processing legacy OPE (observation) files
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon May  9 15:22:42 HST 2011
#]
#
# remove once we're certified on python 2.6
from __future__ import with_statement

import re, sys, os
import Bunch

class OPEerror(Exception):
    pass

# OPE file regexes
# old style
ope_regex1 = re.compile(r'^.*\<HEADER\>(?P<hdr>.*)\</HEADER\>\s*'
'\<PARAMETER_LIST\>(?P<params>.*)\</PARAMETER_LIST\>\s*'
'\<COMMAND\>\s*(?P<cmd>.+)\s*\</COMMAND\>\s*$',
re.MULTILINE | re.DOTALL | re.IGNORECASE)
# new style
ope_regex2 = re.compile(r'^.*\:HEADER\s+(?P<hdr>.*)'
'\:PARAMETER(_LIST)?\s+(?P<params>.*)'
'\:COMMAND\s+(?P<cmd>.+)\s*$',
re.MULTILINE | re.DOTALL | re.IGNORECASE)

# CD file regex
# old style
cd_regex1 = re.compile(r'^.*\<COMMAND\>\s*(?P<cmd>.+)\s*\</COMMAND\>\s*$',
                      re.MULTILINE | re.DOTALL | re.IGNORECASE)
# new style
cd_regex2 = re.compile(r'^.*\:COMMAND\s+(?P<cmd>.+)\s*$',
                      re.MULTILINE | re.DOTALL | re.IGNORECASE)

# PRM includes regex
load_regex = re.compile(r'^\*LOAD\s*"(.+)"\s*$', re.IGNORECASE)

# regex for matching variable references
regex_varref = re.compile(r'^(.*?)(\$[\w_\.]+)(.*)$')

# regexes for checking RA and DEC in OPE files
regex_ra1 = re.compile(r'^.*[\s=]RA=([\d\.]+)(.*)$', re.IGNORECASE)
regex_ra2 = re.compile(r'^(?P<hr>\d\d)(?P<min>\d\d)(?P<sec>\d\d)\.(\d\d?\d?)$')
regex_dec1 = re.compile(r'^.*[\s=]DEC=([\d\+\-\.]+)(.*)$', re.IGNORECASE)
regex_dec2 = re.compile(r'^(?P<deg>[\-\+]?\d\d)(?P<min>\d\d)(?P<sec>\d\d)\.(\d\d?\d?)$')

def toupper(cmdstr):
    # TODO: is there a C-based module for something like this available?
    # This is terribly inefficient
    quotes = ('"', "'")
    
    start_quote = None
    chars = []             # Character buffer

    charlst = list(cmdstr)

    while len(charlst) > 0:
        c = charlst.pop(0)

        # process double quotes
        if c in quotes:
            # if we are not building a quoted string, then turn on quote
            # flag and continue scanning
            if not start_quote:
                start_quote = c
                chars.append(c)
                continue
            elif start_quote != c:
                chars.append(c)
                continue
            else:
                # end of quoted string
                chars.append(c)
                start_quote = None
                continue
        else:
            if start_quote != None:
                chars.append(c)
            else:
                chars.append(c.upper())

    return ''.join(chars)


# def toupper(s):
#     """Function to convert a string to upper case, preserving
#     case inside quotes.
#     """
#     # TODO: this is not sufficient!
#     return s.upper()


def locate_prm(filename, include_dirs):
    """Function to locate a filename within a list of directories.
    Returns the first valid path found.
    """

    for dirpath in include_dirs:
        path = os.path.join(dirpath, filename)
        if os.path.exists(path):
            return path

    raise OPEerror("Could not locate included PRM file '%s' in %s" % (
        filename, str(include_dirs)))


def prepend_prm(lines, filename, include_dirs):

    filepath = locate_prm(filename, include_dirs)

    try:
        with open(filepath, 'r') as in_f:
            buf = in_f.read()

        # Prepend the lines to the current set of lines
        # TODO: there has got to be a more efficient way
        # to do this
        newlines = buf.split('\n')
        newlines.reverse()
        for line in newlines:
            lines.insert(0, line)

    except IOError, e:
        raise OPEerror(str(e))

        
def get_sections(opebuf):
    def process_match(match):
        hdrbuf = match.group('hdr').strip()
        prmbuf = match.group('params').strip().replace('\t', ' ')
        cmdbuf = match.group('cmd').strip()

        return (hdrbuf, prmbuf, cmdbuf)

    for regex in (ope_regex1, ope_regex2):
        match = regex.match(opebuf)
        if match:
            return process_match(match)
    
    for regex in (cd_regex1, cd_regex2):
        match = regex.match(opebuf)
        if match:
            header = ''
            plist = ''
            cmds = match.group('cmd')
            return (header, plist, cmds)

    raise OPEerror("String contents do not match expected format")


def get_vars(plist, include_dirs):
    """Build substitution dictionary from the <Parameter_List> section
    of an OPE file."""

    lines = plist.split('\n')
    substDict = Bunch.caselessDict()
    while len(lines) > 0:
        line = lines.pop(0)
        line = line.strip()
        match = load_regex.match(line)
        if match:
            prepend_prm(lines, match.group(1), include_dirs)
            continue

        # convert to uc
        line = toupper(line)

        if line.startswith('#') or line.startswith('*') or (len(line) == 0):
            continue

        if '=' in line:
            idx = line.find('=')
            var = line[0:idx].strip()
            val = line[idx+1:].strip()
            substDict[var] = val

    return substDict


def get_vars_ope(opebuf, include_dirs):
    """Build substitution dictionary from the <Parameter_List> section
    of an OPE file."""
    (header, plist, cmds) = get_sections(opebuf)
    return get_vars(plist, include_dirs)

def check_ra(ra):
    match = regex_ra2.match(ra)
    if not match:
        raise OPEerror("RA of '%s' does not appear to be formatted correctly" % (
            ra))

    try:
        hr = int(match.group('hr'))
        assert((hr >= 0) and (hr <= 23)), OPEerror("Bad hour: %d" % (hr))
        mn = int(match.group('min'))
        assert((mn >= 0) and (mn < 60)), OPEerror("Bad minutes: %d" % (mn))
        sec = int(match.group('sec'))
        assert((sec >= 0) and (sec < 60)), OPEerror("Bad seconds: %d" % (sec))
    except Exception, e:
        raise OPEerror("RA of '%s' appears to have incorrect values: %s" % (
            ra, str(e)))

def check_dec(dec):
    match = regex_dec2.match(dec)
    if not match:
        raise OPEerror("DEC of '%s' does not appear to be formatted correctly")

    try:
        deg = int(match.group('deg'))
        assert((deg >= -90) and (deg <= 90)), OPEerror("Bad degrees: %d" % (deg))
        mn = int(match.group('min'))
        assert((mn >= 0) and (mn < 60)), OPEerror("Bad minutes: %d" % (mn))
        sec = int(match.group('sec'))
        assert((sec >= 0) and (sec < 60)), OPEerror("Bad seconds: %d" % (sec))
    except Exception, e:
        raise OPEerror("DEC of '%s' appears to have incorrect values: %s" % (
            dec, str(e)))

def check_coords(line):
    # Check line for RA's
    match = regex_ra1.match(line)
    while match:
        ra = match.group(1)
        check_ra(ra)
        sfx = match.group(2)
        if (len(sfx) > 0) and (not sfx.startswith(' ')):
            raise OPEerror("No space between RA and next parameter")
        match = regex_ra1.match(sfx)
        
    # Check line for DEC's
    match = regex_dec1.match(line)
    while match:
        dec = match.group(1)
        check_dec(dec)
        sfx = match.group(2)
        if (len(sfx) > 0) and (not sfx.startswith(' ')):
            raise OPEerror("No space between DEC and next parameter")
        match = regex_dec1.match(sfx)


def check_ope(buf, include_dirs=None):
    """Parse an OPE file and return a Bunch of information about it.
    Returns a bunch with several items defined:
      reflist: a list of all variable references (each is a bunch)
      refset: a set of all variable references (just variable names)
      badlist: a list of all undefined variable references (each is a bunch)
      badset: a set of all undefined variable references (just variable names)
      taglist: a list of all tag lines encountered (each is a bunch)
    """
    if include_dirs == None:
        include_dirs = []
        
    # compute the variable dictionary
    varDict = get_vars_ope(buf, include_dirs)

    refset = set([])
    badset = set([])
    reflist = []
    badlist = []
    taglist = []
    badcoords = []

    def addvarrefs(lineno, line):
        offset = 0
        match = regex_varref.match(line)
        while match:
            pfx, varref, sfx = match.groups()
            #print "1) %d pfx=(%s) varref=(%s) sfx=(%s)" % (
            #    lineno, pfx, varref, sfx)
            offset += len(pfx)
            start = offset
            offset += len(varref)
            end = offset
            varref = varref.upper()[1:]

            refset.add(varref)
            bnch = Bunch.Bunch(varref=varref, lineno=lineno,
                               text=line,
                               start=start, end=end)
            reflist.append(bnch)

            try:
                res = varDict[varref]
            except KeyError:
                badset.add(varref)
                badlist.append(bnch)

            match = regex_varref.match(sfx)

    lineno = 0
    for line in buf.split('\n'):
        lineno += 1
        sline = line.strip()
        if sline.startswith('###'):
            taglist.append(Bunch.Bunch(lineno=lineno,
                                       text=line,
                                       tags=['comment3']))

        elif sline.startswith('##'):
            taglist.append(Bunch.Bunch(lineno=lineno,
                                       text=line,
                                       tags=['comment2']))

        elif sline.startswith('#'):
            taglist.append(Bunch.Bunch(lineno=lineno,
                                       text=line,
                                       tags=['comment1']))

        else:
            try:
                check_coords(line)

            except OPEerror, e:
                bnch = Bunch.Bunch(errstr=str(e), lineno=lineno,
                                   text=line)
                badcoords.append(bnch)
            addvarrefs(lineno, line)


    return Bunch.Bunch(refset=refset, reflist=reflist,
                       badset=badset, badlist=badlist,
                       taglist=taglist, vardict=varDict,
                       badcoords=badcoords)
                           
            
def substitute_params(plist, cmdstr, include_dirs):

    substDict = get_vars(plist, include_dirs)
    
    cmdstr = toupper(cmdstr)

    # Now substitute into the command line wherever we see any of these
    # varrefs

    # Sort vars so that longest ones are tried first
    vars = substDict.keys()
    vars.sort(lambda x,y: len(y) - len(x))

    for key in vars:
        varref = '$%s' % key
        if varref in cmdstr:
            cmdstr = cmdstr.replace(varref, substDict[key])

    # Final sanity check
    # TODO: parse this with the OPE parser
    i = cmdstr.find('$')
    if i > 0:
        raise OPEerror("Not all variable references were converted: %s" % (
            cmdstr[i:]))
    
    return cmdstr

    
## def params_to_envstr(plist):

##     res = []
##     for line in plist.split('\n'):
##         line = line.strip()
##         if line.startswith('#') or line.startswith('*') or (len(line) == 0):
##             continue

##         elif '=' in line:
##             idx = line.find('=')
##             var = line[0:idx].strip()
##             val = line[idx+1:].strip()
##             res.append('%s=%s' % (var, val))

##         else:
##             # What!?
##             pass

##     return ' '.join(res)


def getCmd(opebuf, cmdstr, include_dirs):
    
    try:
        (header, plist, cmds) = get_sections(opebuf)

        cmdstr = cmdstr.strip()

        #print "PLIST", plist
        #print "CMDSTR", cmdstr
        
        # Substitute parameters into command list
        #print "SUBST <== (%s) : %s" % (str(plist), cmdstr)
        cmdstr = substitute_params(plist, cmdstr,
                                   include_dirs)
        #print "SUBST ==> %s" % (cmdstr)
        #envstr = params_to_envstr(plist)
        #envstr = ''
        
        #return (cmdstr, envstr)
        return cmdstr

    except Exception, e:
        raise OPEerror("Can't extract command: %s" % str(e))



def main(options, args):
    in_f = open(options.opefile, 'r')
    opebuf = in_f.read()
    in_f.close()

    print getCmd(opebuf, options.cmdstr, [])

    
if __name__ == '__main__':

    # Parse command line options
    from optparse import OptionParser

    optprs = OptionParser(version=('%prog'))
    optprs.add_option("--cmd", dest="cmdstr", metavar="CMDSTR",
                      help="The CMDSTR to convert")
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--ope", dest="opefile", metavar="FILE",
                      help="Specify OPE file to use")
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

# END

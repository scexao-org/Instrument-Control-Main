#! /usr/bin/env python
#
# Generate instrument simulator command stubs from a list of PARA file
#   definitions.
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Jul  8 17:16:03 HST 2009
#]
#
"""
This simple program creates a set of empty instrument method stubs for
creating an instrument 'personality' for simcam.  You call it in the
following way, e.g.:

./stubgen.py --paradir=../SkPara/cmd/SPCAM --type=simcam > spcam_stubs.txt

OR

./stubgen.py --paradir=../SkPara/cmd/SPCAM --type=task > task_stubs.txt

You can then pull the stubs into an editor and flesh them out to create a
more complete simulation or task definition.
"""

import sys, os
from optparse import OptionParser

import SOSS.DotParaFiles.ParaValidator as ParaValidator
import logging, ssdlog


templates = {}

# Template for generating methods for simcam stubs
templates['simcam'] = """\
    def %(methodname)s(self, %(kwdargs)s):
        self.logger.error("command '%(methodname)s' not yet implemented")
        res = unimplemented_res
        return res
"""        

# Template for generating Task stubs
templates['task'] = """\
class %(classname)s(%(instrument)sTask):
    def __init__(self, %(kwdargs)s):
        super(%(classname)s, self).__init__('%(classname)s', %(kwdargs2)s)
"""        


def error(msg, exitcode):
    """Called for a fatal error.  Print _msg_ to stderr and exit program
    with code _exitcode_.
    """
    sys.stderr.write(msg + '\n')
    sys.exit(exitcode)


def mkclassname(cmdname):
    s = cmdname.capitalize()
    i = 0
    res = []
    while i < len(s):
        # Capitalize letters after an underscore
        if s[i] == '_':
            res.append('_')
            i += 1
            res.append(s[i].upper())
        else:
            res.append(s[i])
        i += 1
    return ''.join(res)


def main(options, args):

    if not options.paradir:
        error("Please specify a PARA file directory with --paradir", 1)
    if not options.type or (options.type not in ['simcam', 'task']):
        error("Please specify a --type=simcam|task", 1)

    # Create top level logger.
    logger = ssdlog.make_logger('stubgen', options)
    # Create a para file parser/validator
    validator = ParaValidator.ParaValidator(logger)

    # Load it full of para file definitions
    validator.loadParaDir(options.paradir)

    template = templates[options.type]
    
    # Iterate over each para definition
    parakeys = validator.keys()
    parakeys.sort()
    subsys = parakeys[0][0].upper()

    formats = []
    classes = []
    htmlTableHdr = '''
<table border="1">
<tr><th>Parameter</th><th>Values</th><th>Type</th></tr>
'''
    for parakey in parakeys:
        (subsys, cmdname) = parakey
#        sys.stderr.write("%s:" % cmdname)
#        sys.stderr.flush()
        paramObj = validator.getitem(parakey)

        paramDefs = paramObj.paramDefs
        methodDict = {'methodname': cmdname.lower(),
                      'classname': mkclassname(cmdname),
                      'instrument': subsys.upper()
                      }
        print "<h2>%s</h2>" % cmdname
        # Iterate over each parameter in this definition
        paramlst = []
        paramlst2 = []
        formatlst = []
        paramsOutput = ''
        for param in paramObj.paramList:
#            sys.stderr.write(" %s" % param)
#            sys.stderr.flush()
            if param == 'DUMMY':
                continue
            paramType = 'CHAR'
            formatting = 's'
            try:
                # paramDef object will be a dict-type thing, UNLESS
                # it is a CASE statement..in that case give up and
                # assume string
                rowspan = 1
                valStr = ''
                paramType = paramDefs[param].defaultDef['TYPE']
                defDef = paramDefs[param].defaultDef
#                print defDef
                dm = paramDefs[param].defMap
                if dm != {}:
                    print "dm"
                cl = paramDefs[param].condList
                if cl != []:
                    print "cl"
                outType = paramType
                fmtType = ''
                if paramType == 'CHAR':
                    fmtType = '%s'
                if (paramType != 'NUMBER') and (paramType != 'CHAR'):
                    print paramType
                    sys.exit(1)
                valList = []
                if 'SET' in defDef:
                    paramList = defDef['SET']
                    rowspan = len(paramList)
                    for paramE in paramList:
                        valE = "<td>%s" % paramE
                        if paramE == defDef['DEFAULT']:
                            valE += " (default)"
                        valE += "</td><td>%s</td>" % fmtType
                        valList.append(valE)
         #           valList = map(lambda a : "<td>%s</td><td>%s</td>" % (a, fmtType), paramList)
                    valStr += '</tr>\n<tr>'.join(valList)
                else:
                    outType = 'float'
                    if 'FORMAT' in defDef:
                        fmtType = defDef['FORMAT']
                    try: valList.append(">%s" % defDef['MIN'])
                    except: pass
                    try: valList.append("<%s" % defDef['MAX'])
                    except: pass
                    try: valList.append("default: %s" % defDef['DEFAULT'])
                    except: pass
                    try: valList.append("</td><td>%s" % fmtType)
                    except: pass
                    valStr += "<td>%s</td>" % ' '.join(valList)
                paramsOutput += '<tr><td rowspan="%s">%s</td>' % (rowspan, param)
                paramsOutput += '%s</tr>\n' % valStr
            except TypeError:
                pass
            # FOR NOW, override formatting and force all to 's'.
            # This is currently the way DD tasks are working.
#            print "<tr><td>%s</td><td>%s</td></tr>" % (param, paramType)
            formatting = 's'
            paraml = param.lower()
            paramlst.append("%s=None" % paraml)
            paramlst2.append("%s=%s" % (paraml, paraml))
            formatlst.append("%s=%%(%s)%s" % (param, paraml, formatting))
        # Sort paramlist
        # TODO: get params in order listed in PARA file?
        #paramlst.sort()
        methodDict['kwdargs'] = ", ".join(paramlst)
        methodDict['kwdargs2'] = ", ".join(paramlst2)
        fmtstr = """
    '%s': Bunch(fmtstr='EXEC %s %s %s',
                parakey=('%s', '%s')),""" % \
        (cmdname.lower(), subsys.upper(), cmdname,
         ' '.join(formatlst), subsys.upper(), cmdname)
        formats.append(fmtstr)
        # Write out the method
        classes.append(template % methodDict)
        if paramsOutput == '':
            print "<p>No parameters</p>"
        else:
            print htmlTableHdr
            print paramsOutput
            print '</table>'
#    print """
#ddcmd_tbl = {
#    %s
#    }
#    """ % ('\n'.join(formats))
    sys.exit(0)

if __name__ == '__main__':

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--paradir", dest="paradir", metavar="DIR",
                      help="Use DIR for retrieving instrument PARA files")
    optprs.add_option("--type", dest="type", metavar="TYPE",
                      help="Generate stubs of TYPE (simcam|task)")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    if len(args) != 0:
        optprs.error("incorrect number of arguments")

    main(options, args)


# END

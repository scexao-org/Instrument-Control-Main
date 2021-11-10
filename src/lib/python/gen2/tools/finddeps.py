#! /usr/bin/env python
#

import sys, os, glob, re
import modulefinder
import pprint


builtins = set(['zipimport', 'thread', 'errno', 'signal', 'sys', 'imp',
                'pwd', 'gc', 'posix', 'marshal', 'exceptions'])

def getmods(dirpath):
    dir_contents = glob.glob(os.path.join(dirpath, '*'))

    modset = set([])
    for path in dir_contents:

        dirpath, filename = os.path.split(path)
        modname, ext = os.path.splitext(filename)

        #print modname
        if modname.startswith('_'):
            continue
        
        if os.path.isdir(path):
            modset.add(modname)
            continue
        
        if re.match(r'^.+\.so$', filename):
            modset.add(modname)
            continue
        
        if re.match(r'^.+\.py$', filename):
            modset.add(modname)
            continue

    return modset


def addmods(dirpath, modset):
    modset.update(getmods(dirpath))
    

def gettree(modset):
    res = {}
    for modname in modset:
        d = res
        for subname in modname.split('.'):
            d = d.setdefault(subname, {})

    return res

def showdeps(modset):
    tree = gettree(modset)
    pprint.pprint(tree)

def printfiles(pfx, d):
    keys = d.keys()
    keys.sort()
    for key in keys:
        if len(d[key]) == 0:
            pyfile = ('/'.join(pfx)) + '/' + key + '.py'
            pyfile = pyfile.strip('/')
            print pyfile
        else:
            print '/'.join(pfx)
            printfiles(pfx + [key], d[key])

    
def main(options, args):

    verdir = 'python%d.%d' % (sys.version_info[0],
                              sys.version_info[1])
    stdlib_contents = getmods('/usr/lib/' + verdir)

    for path in glob.glob('/usr/lib/' + verdir + '/*'):
        if os.path.isdir(path):
            addmods(path, stdlib_contents)

    stdlib_contents.update(builtins)

    pkglib_contents = getmods('/usr/lib/' + verdir + '/site-packages')
    addmods('/var/lib/python-support/' + verdir, pkglib_contents)

    finder = modulefinder.ModuleFinder()

    fullstdmods = set([])
    fullpkgmods = set([])
    fullextmods = set([])

    if options.show == 'all':
        show = "stdlib,pkg,ext,local".split(',')
    else:
        show = options.show.lower().split(',')
    
    for arg in args:

        dirpath, filename = os.path.split(arg)
        localmods = getmods(dirpath)
        #print localmods
        
        finder.run_script(arg)

        thisstdmods = set([])
        thispkgmods = set([])
        thisextmods = set([])
        thislocalmods = set([])
        for name, mod in finder.modules.iteritems():

            if name.startswith('_'):
                continue

            topname = name.split('.')[0]
            
            #print '%s: ' % name,
            #print ','.join(mod.globalnames.keys()[:3])
            if topname in stdlib_contents:
                thisstdmods.add(topname)
                continue

            if topname in pkglib_contents:
                thispkgmods.add(topname)
                continue

            #print name
            if topname in localmods:
                thislocalmods.add(name)
                continue
            
            thisextmods.add(name)

        if 'stdlib' in show:
            print "stdlib dependencies for '%s':" % arg
            showdeps(thisstdmods)

        if 'pkg' in show:
            print "Package dependencies for '%s':" % arg
            showdeps(thispkgmods)

        if 'local' in show:
            print "Local dependencies for '%s':" % arg
            showdeps(thislocalmods)

        if 'ext' in show:
            print "External dependencies for '%s':" % arg
            showdeps(thisextmods)

        fullextmods.update(thisextmods)
        fullpkgmods.update(thispkgmods)
        fullstdmods.update(thisstdmods)
        
    if 'stdlib' in show:
        print "Full stdlib dependency set:"
        showdeps(fullstdmods)
    
    if 'pkg' in show:
        print "Full package dependency set:"
        showdeps(fullpkgmods)
    
    if 'ext' in show:
        print "Full external dependency set:"
        showdeps(fullextmods)

        d = gettree(fullextmods)
        printfiles([], d)

            
        
if __name__ == '__main__':

    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--show", dest="show", default="local,ext,pkg",
                      help="Show which dependences")

    (options, args) = optprs.parse_args(sys.argv[1:])


    if len(args) == 0:
        optprs.error("incorrect number of arguments")

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

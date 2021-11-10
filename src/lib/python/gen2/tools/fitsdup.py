#!/usr/bin/env python
#
import sys, os
import astro.fitsutils as fitsutils

version = '20080205.0'


def main(options, args):

    if not options.srcfile:
        print "Please specify a --src"
        sys.exit(1)
        
    info = fitsutils.getFrameInfoFromPath(options.srcfile)
    (old_frameid, old_fitsname, old_srcdir, old_inscode, old_frametype,
     old_frameno) = info

    if not options.dstfile:
        print "Please specify a --dst"
        sys.exit(1)
        
    info = fitsutils.getFrameInfoFromPath(options.dstfile)
    (new_frameid, new_fitsname, new_dstdir, new_inscode, new_frametype,
     new_frameno) = info
    if new_dstdir == '':
        new_dstdir = '.'

    count = options.numframes
    
    out_f = open('/tmp/frames.txt', 'w')

    for i in xrange(count):

        # Construct new frameid
        newframeid = ('%3.3s%1.1s%08.8d' % (new_inscode, new_frametype,
                                            new_frameno + i))

        # FITS headers to update
        kwdvals = {'FRAMEID': newframeid,
                   'EXP-ID': newframeid,
                   }
        if options.propid:
            kwdvals.update({'PROP-ID': options.propid})

        srcpath = options.srcfile
        dstpath = new_dstdir + os.path.sep + newframeid + '.fits'
        
        fitsutils.update_fits(srcpath, dstpath, kwdvals)

	if options.daqperms:
	    os.chmod(dstpath, 0440)

	out_f.write('%s\n' % newframeid)
	sys.stderr

    out_f.close()


if __name__ == '__main__':
    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage, version=('%%prog %s' % version))
    
    parser.add_option("--daqperms", dest="daqperms", action="store_true",
                      default=False,
                      help="Use DAQ permissions on the resulting file")
    parser.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    parser.add_option("--src", dest="srcfile", 
                      metavar="FILE",
                      help="Use FILE as the source fits file")
    parser.add_option("--dst", dest="dstfile", 
                      metavar="FILE",
                      help="use FILE as the destination fits file")
    parser.add_option("-p", "--propid", dest="propid", 
                      metavar="PROPID",
                      help="Change to PROPID in the fits header")
    parser.add_option("-n", "--numframes", dest="numframes", 
                      metavar="NUM", type='int', default=1,
                      help="Generate NUM frames from initial file")
    parser.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")

    (options, args) = parser.parse_args(sys.argv[1:])

    if len(args) != 0:
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

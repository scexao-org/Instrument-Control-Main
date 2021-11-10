#!/usr/bin/env python
"""
MakeIndexFile.py -- use STARSint to create an index file from a FITS file.

Bruce Bon (Bruce.Bon@SubaruTelescope.org)  last edit: 2006-09-08
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Dec 18 12:26:29 HST 2008
#]

Usage:
    MakeIndexFile.py --make-index <FITS file> ...
      <FITS file>    the file names(s) of FITS files for
      which you want to generate index files
"""

import sys, re, os
from optparse import OptionParser

import astro.fitsutils as fitsutils
from SOSS.STARSint import get_fits_metadata, create_index_file
from cfg.INS import INSdata as INSconfig

# ========================================================================

# Usage string
usage = """MakeIndexFile.py <FITS file> ...
  <FITS file>    the file names(s) of FITS files for
     which you want to generate index files"""

# ========================================================================

def main(options, args):
    
    # Get an instrument configuration object
    insconfig = INSconfig()

    if options.check_stars:
        # Only import this if they are asking if file is in STARS
        import STARSquery
    
    for fitspath in args:
        # Separate leading directory
        res = fitsutils.getFrameInfoFromPath(fitspath)

        if not res:
            print "File name '%s' doesn't match a valid Subaru FITS name." % \
                  (fitspath)
            print "Please rename the file as 'XXX{A|Q}DDDDDDDD.fits'"
            print "Skipping this file..."
            continue

        (frameid, fitsfile, fitsdir, inscode, frametype, frameno) = res
        try:
            insname = insconfig.getNameByCode(inscode)
        except KeyError:
            print "File name '%s' doesn't match a valid Subaru instrument." % \
                  (fitsfile)
            print "Skipping this file..."
            continue

        if options.check_stars:
            print "Checking if frame %s is in STARS..." % frameid
            if STARSquery.GetStarsInfoForFitsID(frameid):
                print "Frame %s IS in STARS!" % frameid
                print "Skipping this file..."
                continue

        # Look up the instrument number and figure out the path where
        # the file should end up
        insnum = insconfig.getNumberByCode(inscode)
        obcInstrPath = '/mdata/fits/obcp%2d' % insnum
        obcIndexPath = '/mdata/index'
        indexfile = frameid + '.index'

        # Get some metadata by reading the file (if necessary)
        metadata = {}
        get_fits_metadata(metadata, fitspath=fitspath,
                          use_mtime=not options.use_ctime)

        # Substitute path where file should end up
        metadata['fitspath'] = obcInstrPath + '/' + fitsfile
        metadata['indexpath'] = obcIndexPath + '/' + indexfile
        indexpath = options.indexdir + '/' + indexfile

        # Make the index file
        if options.create_index:
            print "Creating index file for %s fits file '%s'..." % \
                  (insname, fitsfile)
            create_index_file(metadata, indexpath=indexpath)

        if options.copy_mdata:
            # chmod 440 fitspath--what DAQ expects
            try:
                os.chmod(fitspath, 0440)
            except OSError, e:
                print "Error chmod on '%s': %s" % (fitsfile, str(e))

            # FITS file
            dstpath = obcInstrPath + '/' + fitsfile
            sshcmd = "ssh daqusr@obc1.sum.naoj.org ls -ld %s" % dstpath
            res = os.system(sshcmd)
            if res != 512:
                print "File may already exist: %s" % dstpath
                print "Skipping file transfer..."
            else:
                scpcmd = "scp -p %s daqusr@obc1.sum.naoj.org:%s" % (
                    fitspath, dstpath)
                print scpcmd
                res = 0
                res = os.system(scpcmd)
                if res != 0:
                    print "Error code transferring file: %d" % res
            
            # Index file
            dstpath = obcIndexPath + '/' + indexfile
            sshcmd = "ssh daqusr@obc1.sum.naoj.org ls -ld %s" % dstpath
            res = os.system(sshcmd)
            if res != 512:
                print "File may already exist: %s" % dstpath
                print "Skipping file transfer..."
            else:
                scpcmd = "scp -p %s daqusr@obc1.sum.naoj.org:%s" % (
                    indexpath, dstpath)
                print scpcmd
                res = 0
                res = os.system(scpcmd)
                if res != 0:
                    print "Error code transferring file: %d" % res

        if options.insert_flowqueue:
            sshcmd = "ssh daqusr@obc1.sum.naoj.org /soss/SRC/TOOL/bin/DAQobcQueueInsert %s 10000000 -y" % frameid
            res = 0
            print sshcmd
            res = os.system(sshcmd)
            if res != 0:
                print "May have been problem with DAQobcQueueInsert"


if __name__ == '__main__':

    # Parse command line options
    parser = OptionParser(usage=usage, version=('%prog 2.0'))
    parser.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    parser.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    parser.add_option("--indexdir", dest="indexdir", default='.',
                      metavar="DIR",
                      help="Create index files in DIR")
    parser.add_option("--use-ctime", dest="use_ctime", action="store_true",
                      default=False,
                      help="Use file's ctime instead of mtime for RAIDADDTIME")
    parser.add_option("--check-stars", dest="check_stars", action="store_true",
                      default=False,
                      help="Check if the file exists in STARS before doing anything")
    parser.add_option("--copy-mdata", dest="copy_mdata", action="store_true",
                      default=False,
                      help="Copy the index and fits files to daqusr@obc1:/mdata")
    parser.add_option("--create-index", dest="create_index",
                      action="store_true",
                      default=False,
                      help="Create an index file")
    parser.add_option("--insert-flowqueue", dest="insert_flowqueue",
                      action="store_true",
                      default=False,
                      help="Insert an entry into DAQ flow queue table on OBC")
    
    (options, args) = parser.parse_args(sys.argv[1:])

    # Make sure there is at least 1 argument
    if len(args) == 0:
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

#END

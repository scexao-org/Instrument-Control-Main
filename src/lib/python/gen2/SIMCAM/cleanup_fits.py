#!/usr/bin/env python
#
# cleanup_fits.py -- removes FITS files that are already in STARS
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Dec 18 14:03:15 HST 2008
#]
#
"""
Removes FITS files from a directory, IFF they are in STARS.  Works by
iterating over a directory of files and querying STARS if each file is
registered or not.  Skips files that do not end in '.fits'

File listing is sorted, so oldest files are purged first.  Currently does
not stop when disk usage drops below a threshold, but iterates all the way
through the list of files.

Typical usage (assuming FITS directory is /data, and proper environment
vars are set):

# Shows you what it WOULD do:
$ ./cleanup_fits.py --loglevel=0 --stderr --fitsdir=/data/FLDMON/fits --dry-run

# Actualy do it & log results
$ ./cleanup_fits.py --loglevel=0 --stderr --fitsdir=/data/FLDMON/fits --action=delete --log=cleanup.log

# Continuously monitor filesystem and cleanup when disk usage rises
# above 80% and stop deleting when disk usage reaches 50%
$ ./cleanup_fits.py --loglevel=0 --fitsdir=/data/FLDMON/fits --lo=50 --hi=80 \
    --action=delete --daemon --log=cleanup.log

TODO: make this into a common module for instruments.  They can import
it and run the daemon or cleanup functions as tasks.
"""
import sys, os, re, time

import myproc
import logging, ssdlog
# For querying STARS
from SOSS.STARSint import STARSdb
import remoteObjects as ro
import Bunch

# for easily parsing frameids
def getFrameInfoFromPath(fitspath):
    # Extract frame id from file path
    (fitsdir, fitsname) = os.path.split(fitspath)
    (frameid, ext) = os.path.splitext(fitsname)
    
    match = re.match('^(\w{3})([AQ])(\d{8})$', frameid)
    if match:
        (inscode, frametype, frame_no) = match.groups()
        frame_no = int(frame_no)
        
        return Bunch.Bunch(frameid=frameid, fitsname=fitsname,
                           fitsdir=fitsdir, inscode=inscode,
                           frametype=frametype, frame_no=frame_no)

    raise Exception("path does not match Subaru FITS specification")

def get_disk_usage(path):
    """Takes a path to a directory and returns the percentage of space
    used on that filesystem (as a float).
    """

    res = os.statvfs(path)

    #scale = (res.f_bsize / 1024)

    # FS size in native fs size blocks
    fs_size = res.f_blocks #* scale
    fs_avail = res.f_bavail #* scale

    # This is not quite accurate wrt "df", but close enough
    pctused = 1.0 - (float(fs_avail) / float(fs_size))

    return pctused

 
def cleanup(options, args, logger):
    """Runs a cleanup on the directory specified in options.fitsdir.
    Specifically, deletes .fits files that ARE in STARS.  Stops when
    disk usage drops below the low water mark threshold specified by
    options.lowater
    """

    # If user specifed file list on command line then use that, otherwise
    # see if a directory was specified with --fitsdir
    if len(args) > 0:
        files = args

    elif options.fromframe and options.toframe:
        # user specified a --from and --to
        fb = getFrameInfoFromPath(options.fromframe)
        tb = getFrameInfoFromPath(options.toframe)
        
        files = [ os.path.join(options.fitsdir, '%3.3s%1.1s%08d.fits' % (
            fb.inscode, fb.frametype, frame_no)) for frame_no \
                  in xrange(fb.frame_no, tb.frame_no+1) ]
        
    elif options.fitsdir:
        # Get listing of files in FITS dir
        files = os.listdir(options.fitsdir)

    else:
        logger.error("No --fitsdir option specified.")
        logger.error("I don't know what I should delete!")
        sys.exit(1)

    # Object for querying STARS
    starsdb = STARSdb(logger)
    
    # Sort file list.  Should bubble older files to earlier in the list.
    files.sort()

    age = {}
    fitslist = []
    inSTARS = {}

    def pass1(files):

        # First pass.  Record information about files in FITS dir.
        logger.info("Cleanup PASS 1: information gathering.")
        for fitsfile in files:

            fitspath = os.path.join(options.fitsdir, fitsfile)

            logger.info("Examining file '%s'" % fitsfile)

            # If this is not a .fits file then move on
            (pfx, ext) = os.path.splitext(fitspath)
            if not re.match(r'^\.fits$', ext, re.IGNORECASE):
                logger.info("No FITS extension: '%s'" % fitsfile)
                continue

            # Assume: NOT in STARS and no age
            age[fitsfile] = 0

            # Record modification time of file
            try:
                stat = os.stat(fitspath)
                age[fitsfile] = stat.st_mtime

            except OSError, e:
                logger.error("Error stat(%s): %s" % (fitsfile, str(e)))
                continue

            # Record if this file is in STARS
            try:
                res = getFrameInfoFromPath(fitspath)

            except Exception, e:
                logger.info("Not a Subaru FITS frame: '%s': %s" % (
                    fitsfile, str(e)))
                continue

            # This shouldn't raise an exception
            inSTARS[fitsfile] = starsdb.inSTARS(res.frameid)
            logger.debug("inSTARS = %s" % str(inSTARS[fitsfile]))

            #fitslist.append(fitsfile)

        # Query STARS
        #try:
        #    inSTARS = client.checkFrames(fitslist)
        #    
        #except ro.remoteObjectError, e:
        #        logger.error("Error querying STARS: %s" % (
        #            str(e)))


        # TODO: sort by age?  Files are already sorted by name, which means that
        # older fits files are earlier in the list.  Unless files have been modified
        # since creation then it is unlikely that sorting by mtime will affect anything.

        if options.action == 'delete':
            # make the list of all files IN stars
            filelst = []
            for fitsfile in files:
                if inSTARS.has_key(fitsfile) and inSTARS[fitsfile]:
                    filelst.append(fitsfile)

            delete(options, logger, filelst)

        elif options.action == 'resend':
            # make the list of all files NOT IN stars
            filelst = []
            for fitsfile in files:
                if inSTARS.has_key(fitsfile) and (not inSTARS[fitsfile]):
                    filelst.append(fitsfile)

            resend(options, logger, filelst)

        else:
            # default action is to print all files not in STARS
            for fitsfile in files:
                if inSTARS.has_key(fitsfile) and (not inSTARS[fitsfile]):
                    print fitsfile

    while len(files) > 0:
        l = files[:options.groupsof]
        files = files[options.groupsof:]
        pass1(l)
        
            
def delete(options, logger, files):
    # Second pass.  Remove files already in STARS.
    # If --lo is provided then stop deleting when the free space reaches
    # a certain threshold?
    logger.info("Cleanup PASS 2: file deletion.")
    for fitsfile in files:

        # Check if we should stop because we have fallen below the low
        # water mark
        if options.lowater:
            pctused = get_disk_usage(options.fitsdir)
            if pctused < (float(options.lowater) / 100.0):
                logger.info("Filesystem usage has dropped below %3d%%" % \
                            options.lowater)
                logger.info("Stopping further deletion.")
                break
        
        fitspath = os.path.join(options.fitsdir, fitsfile)
        
        logger.info("File '%s' in STARS--deleting..." % fitsfile)
        try:
            if not options.dry_run:
                os.remove(fitspath)

        except OSError, e:
            logger.error("Error deleting %s: %s" % (fitsfile, str(e)))
            
    logger.info("Pass 2 finished.")


def resend(options, logger, files):
    # Second pass.  Resend files NOT in STARS.
    logger.info("Cleanup PASS 2: resend files.")

    # initialize remoteObjects and get a handle to the STARS interface
    ro.init()
    stars = ro.remoteObjectProxy('STARS')
    
    for fitsfile in files:

        fitspath = os.path.join(options.fitsdir, fitsfile)
        
        logger.info("File '%s' NOT in STARS--resending..." % fitsfile)
        try:
            if not options.dry_run:
                stars.resend_fits(fitspath)

                time.sleep(options.interval)

        except Exception, e:
            logger.error("Error resending %s: %s" % (fitsfile, str(e)))
            
    logger.info("Pass 2 finished.")


def daemon(options, args, logger):
    """Run as a daemon.  Specifically, monitor the FITS directory, and
    when usage climbs above the high water mark, invoke the cleanup
    function.
    """
    try:
        while True:
            # Check if we should delete because we have risen above the high
            # water mark
            pctused = get_disk_usage(options.fitsdir)
            logger.debug("Disk usage is %3.2f%%" % (pctused * 100))
            if pctused > (float(options.hiwater) / 100.0):
                logger.info("Filesystem usage has risen above %3d%%" % \
                            options.hiwater)
                logger.info("Invoking cleanup.")
                cleanup(options, args, logger)

            logger.debug("Sleeping for %3.2f secs" % options.interval)
            time.sleep(options.interval)
            
    except KeyboardInterrupt:
        logger.error("Caught keyboard interrupt!")
        
        
def main(options, args):

    logname = 'cleanup_fits'
    logger = ssdlog.make_logger(logname, options)

    # Initialize remote objects subsystem.
    #try:
    #    ro.init()
    #
    #except ro.remoteObjectError, e:
    #    logger.error("Error initializing remote objects subsystem: %s" % str(e))
    #    sys.exit(1)

    
    if options.daemon:
        daemon(options, args, logger)
    else:
        cleanup(options, args, logger)
    
    logger.info("Cleanup terminating.")

if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options] [file] ..."
    optprs = OptionParser(usage=usage, version=('%prog'))
    
    optprs.add_option('-a', "--action", dest="action", metavar="ACTION",
                      default=None,
                      help="specify ACTION to operate on fits files")
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option('-d', "--fitsdir", dest="fitsdir", metavar="DIR",
                      default=None,
                      help="Use DIR for storing instrument FITS files")
    optprs.add_option("--daemon", dest="daemon",  action="store_true",
                      default=False,
                      help="Run as a daemon.")
    optprs.add_option("--dry-run", dest="dry_run", default=False,
                      action="store_true",
                      help="Don't really delete files, just show what we would do")
    optprs.add_option("--from", dest="fromframe", metavar="FRAMEID",
                      help="Set FROM frameid")
    optprs.add_option("--groupsof", dest="groupsof", metavar="NUM",
                      type="int", default=500,
                      help="Process files in groups of NUM")
    optprs.add_option("--hi", dest="hiwater", metavar="PCT",
                      type="int", default=90,
                      help="Set high water disk usage to PCT")
    optprs.add_option("--interval", dest="interval", metavar="SECS",
                      type="float", default=60.0,
                      help="Set interval for waiting between disk checks")
    optprs.add_option("--lo", dest="lowater", metavar="PCT",
                      type="int", default=None,
                      help="Set low water disk usage to PCT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--to", dest="toframe", metavar="FRAMEID",
                      help="Set TO frameid")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    #if len(args) > 0:
    #    optprs.error("incorrect number of arguments")
       
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

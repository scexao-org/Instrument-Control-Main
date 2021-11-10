#!/usr/bin/env python
#
# cleanup_fits.py -- removes old FITS files
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Feb 21 12:27:47 HST 2013
#]
#
"""
Removes FITS files from a directory tree to bring the disk usage under
a certain percentage.  Skips files that do not end in '.fits'

Typical usage (assuming FITS directory is /data, and proper environment
vars are set):

# Shows you what it WOULD do:
$ ./cleanup_fits.py --loglevel=0 --stderr --fitsdir=/data --dry-run

# Actualy do it & log results
$ ./cleanup_fits.py --loglevel=0 --stderr --fitsdir=/data --action=delete --log=cleanup.log

# Continuously monitor filesystem and cleanup when disk usage rises
# above 80% and stop deleting when disk usage reaches 50%
$ ./cleanup_fits.py --loglevel=0 --fitsdir=/data --lo=50 --hi=80 \
    --action=delete --daemon --log=cleanup.log

TODO: make this into a common module for instruments.  They can import
it and run the daemon or cleanup functions as tasks.
"""
import sys, re, time
import os, fnmatch

import logging, ssdlog
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

def recursive_glob(treeroot, pattern):
  results = []
  for base, dirs, files in os.walk(treeroot):
    goodfiles = fnmatch.filter(files, pattern)
    results.extend(os.path.join(base, f) for f in goodfiles)
  return results


def cleanup(options, args, logger):
    """Runs a cleanup on the directory specified in options.fitsdir.
    Specifically, deletes .fits files that ARE in STARS.  Stops when
    disk usage drops below the low water mark threshold specified by
    options.lowater
    """

    files = recursive_glob(options.fitsdir, "*.fits")

    # First pass.  Record information about files in FITS dir.
    logger.info("Cleanup PASS 1: information gathering.")
    fitslist = []
    for fitspath in files:

        logger.debug("Examining file '%s'" % fitspath)

        # If this is not a .fits file then move on
        (pfx, ext) = os.path.splitext(fitspath)
        if not re.match(r'^\.fits$', ext, re.IGNORECASE):
            logger.info("No FITS extension: '%s'" % fitspath)
            continue

        # Assume: no age
        age = 0

        # Record modification time of file
        try:
            stat = os.stat(fitspath)
            age = stat.st_mtime

        except OSError, e:
            logger.error("Error stat(%s): %s" % (fitspath, str(e)))
            continue

        # Skip files that don't look like Subaru frames
        try:
            res = getFrameInfoFromPath(fitspath)

        except Exception, e:
            logger.info("Not a Subaru FITS frame: '%s': %s" % (
                fitspath, str(e)))
            continue

        bnch = Bunch.Bunch(fitspath=fitspath, age=age)
        fitslist.append(bnch)

    # Sort by age
    fitslist.sort(lambda x, y: int(round(x.age - y.age)))
    #print fitslist

    delete(options, logger, fitslist)

            
def delete(options, logger, files):
    # Second pass.  Remove files.  Stop deleting when the free space reaches
    # a certain threshold.
    logger.info("Cleanup PASS 2: file deletion.")
    for bnch in files:

        # Check if we should stop because we have fallen below the low
        # water mark
        if options.lowater:
            pctused = get_disk_usage(options.fitsdir)
            if pctused < (float(options.lowater) / 100.0):
                logger.info("Filesystem usage has dropped below %3d%%" % \
                            options.lowater)
                logger.info("Stopping further deletion.")
                break
        
        fitspath = bnch.fitspath
        filedate = time.strftime("%Y-%m-%d %H:%M:%S", 
                                 time.localtime(bnch.age))
        
        logger.info("Deleting '%s' aged %s" % (fitspath, filedate))
        try:
            if not options.dry_run:
                os.remove(fitspath)

        except OSError, e:
            logger.error("Error deleting '%s': %s" % (fitspath, str(e)))
            
    logger.info("Pass 2 finished.")


def check_usage(options, logger):
    # Check if we should delete because we have risen above the high
    # water mark
    pctused = get_disk_usage(options.fitsdir)
    logger.debug("Disk usage is %3.2f%%" % (pctused * 100))
    if pctused > (float(options.hiwater) / 100.0):
        logger.info("Filesystem usage has risen above %3d%%" % (
                        options.hiwater))
        logger.info("Invoking cleanup.")
        cleanup(options, args, logger)
    else:
        logger.info("Filesystem usage (%3d%%) is below %3d%% threshold" % (
                        int(pctused*100), options.hiwater))


def main(options, args):

    logname = 'cleanup_fits'
    logger = ssdlog.make_logger(logname, options)

    try:
        if options.daemon:
            while True:
                check_usage(options, logger)

                logger.debug("Sleeping for %3.2f secs" % options.interval)
                time.sleep(options.interval)
        else:
            check_usage(options, logger)
            
    except KeyboardInterrupt:
        logger.error("Caught keyboard interrupt!")
    
    logger.info("Cleanup terminating.")

if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options] [file] ..."
    optprs = OptionParser(usage=usage, version=('%prog'))
    
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
    optprs.add_option("--hi", dest="hiwater", metavar="PCT",
                      type="int", default=80,
                      help="Set high water disk usage to PCT")
    optprs.add_option("--interval", dest="interval", metavar="SECS",
                      type="float", default=60.0,
                      help="Set interval for waiting between disk checks")
    optprs.add_option("--lo", dest="lowater", metavar="PCT",
                      type="int", default=40,
                      help="Set low water disk usage to PCT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    if len(args) > 0:
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


# END

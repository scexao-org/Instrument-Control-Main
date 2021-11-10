#! /usr/bin/env python
#
# get-ut1utc.py -- fetch UT1-UTC adjustment table
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed May 12 14:39:02 HST 2010
#]

import sys, os, time

import ssdlog
import remoteObjects as ro

# Where to store the file
dbarea = os.path.join(os.environ['GEN2COMMON'], 'db')

# What to name the file
filename = 'UT1_UTC.table'

# Where to store a copy for TSC
tscfile = os.path.join('/gen2/home/tsc', filename)

def main(options, args):
    
    # Make top-level logger.
    logger = ssdlog.make_logger('ut1-utc', options)

    today = time.strftime("%Y%M%d", time.localtime())

    oldfile = os.path.join(dbarea, filename)
    bakfile = os.path.join(dbarea, filename + '.bak')
    newfile = os.path.join(dbarea, filename + '.' + today)

    res = os.system("wget --tries=5 -O %s %s" % (newfile, options.url))
    if res == 0:
        try:
            os.remove(bakfile)
        except OSError:
            pass

        try:
            os.rename(oldfile, bakfile)
            os.rename(newfile, oldfile)

        except Exception, e:
            logger.error("Failed to ftp ut1-utc file: %s" % url)
            logger.error(str(e))
            sys.exit(1)

    else:
        logger.error("Failed to ftp ut1-utc file: %s" % url)
        logger.error("wget result is %d" % (res))
        sys.exit(1)

    # copy the file to a special place where it will be FTPed by TSC
    res = os.system("cp -f %s %s" % (oldfile, tscfile))

    ro.init()

    # Have the status server reload the UT1_UTC table
    status = ro.remoteObjectProxy('status')
    status.update_ut1utc(oldfile)


if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options] command [args]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("--url", dest="url",
                      default="ftp://maia.usno.navy.mil/ser7/ser7.dat",
                      metavar="URL",
                      help="Fetch ut1-utc data from URL")
    ssdlog.addlogopts(optprs)

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

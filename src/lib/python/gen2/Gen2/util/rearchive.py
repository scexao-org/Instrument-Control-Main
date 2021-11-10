#!  /usr/bin/env python
#
# rearchive.py -- rearchive frames from an instrument
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Jan 27 07:42:19 HST 2012
#]
#
"""
   Usage:
      ./rearchive.py -f spec_file
      cat spec_file | ./rearchive.py

   --dry-run can be added to show what WOULD be done.

   Format of spec-file is as follows:
   <frameid>   <path-on-obcp>

   Instrument name and obcp machine are looked up.  If path includes a
   colon, then that is assumed to be a different host to use.
"""
import sys
import time

from cfg.INS import INSdata
import astro.frame as frame
import remoteObjects as ro
import ssdlog


def main(options, args):
    
    ro.init()

    insconfig = INSdata()

    archiver = ro.remoteObjectProxy('archiver')

    if options.infile:
        with open(options.infile, 'r') as in_f:
            buf = in_f.read()
    else:
        buf = sys.stdin.read()

    for line in buf.split('\n'):
        line = line.strip()
        # skip blank lines and comments
        if (len(line) == 0) or line.startswith('#'):
            continue

        (frameid, path) = line.split()
        if ':' in path:
            host, path = path.split(':')
        else:
            host = None
        
        finfo = frame.getFrameInfoFromPath(frameid)

        # TODO: we could do in groups, would be faster if there are
        # a lot of files to transfer
        framelist = [(finfo.frameid, path)]

        # Look up the instrument transfer info
        obcpinfo = insconfig.getOBCPInfoByCode(finfo.inscode)
        if not host:
            host = obcpinfo['obcphost']
        transfermethod = obcpinfo['transfermethod']

        # Make a call to the archiver to transfer this file
        print "Attempting to archive %s: %s" % (frameid, path)
        if not options.dry_run:
            res = archiver.archive_framelist(host, transfermethod,
                                             framelist)
            if res != ro.OK:
                print "Archiver returned error code %d" % (res)
            else:
                print "Archived file."

            time.sleep(options.interval)
        else:
            print "Host: %s Method: %s Framelist: %s" % (
                host, transfermethod, str(framelist))

if __name__ == '__main__':
    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog -f archive_file'))
    
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--dry-run", dest="dry_run", default=False,
                      action="store_true",
                      help="Only show what would be done.")
    optprs.add_option("-f", "--infile", dest="infile", metavar="PATH",
                      help="Specify frames to transfer in file PATH")
    optprs.add_option("-i", "--interval", dest="interval", metavar="SEC",
                      type='float', default=1.0,
                      help="Specify interval in SEC between transfers")
    # optprs.add_option('-p', "--passfile", dest="passfile", 
    #                   help="Specify authorization pass phrase file")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
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


#END

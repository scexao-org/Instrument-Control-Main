#!/usr/bin/env python
#
# checkproc.py -- utility to check status of a multithreaded service
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Tue Nov 29 12:22:52 HST 2011
#]
"""
USAGE:
    ./checkproc.py [ -t ]
"""

import sys, time
import remoteObjects as ro

def main(options, args):

    #logger = ssdlog.make_logger('checkproc', options)

    ro.init()

    fmt = "%5.5d  %10.10s  %12.12s  %s"

    if len(args) == 0:
        svc = ro.remoteObjectProxy('names')
        args = svc.getNames()
        print args
   
    for svcname in args:
        print " ------------- "
        svc = ro.remoteObjectProxy(svcname)

        table = []
        try:
            res = svc.ro_workerStatus()
            if not res:
                print "Service '%s' returned no worker information." % (
                    svcname)
                continue
                
            check_time = time.time()
            #print res

            i = 0
            for status, start_time in res:
                st = status[:9]
                t_s = ''
                if st.startswith('executing'):
                    elapsed = check_time - start_time
                    hrs = int(elapsed / 3600.0)
                    elapsed -= hrs*3600
                    mins = int(elapsed / 60.0)
                    elapsed -= mins*60
                    t_s = "%d:%d:%.3f" % (hrs, mins, elapsed)

                table.append((i, st, t_s, status[10:]))
                i += 1

        except Exception, e:
            print "Error getting threadPool information from '%s': %s" % (
                svcname, str(e))
            continue

        print "Status of threads in '%s':" % svcname
        # TODO: optional sorting

        total_cnt = len(table)
        idle_cnt = len(filter(lambda tup: tup[1] == 'idle', table))
        idle_pct = float(idle_cnt) / float(total_cnt) * 100.0

        if not options.summary:
            for tup in table:
                if (tup[1] == 'idle') and (not options.show_idle):
                    continue
                print fmt % tup

        print ""
        print "%d total threads, %d%% are idle (%d)." % (
            total_cnt, idle_pct, idle_cnt)


if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [-t]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--show-idle", dest="show_idle", default=False,
                      action="store_true",
                      help="Show idle threads in listing")
    optprs.add_option("-s", "--summary", dest="summary", default=False,
                      action="store_true",
                      help="Show summary only")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("-t", "--sorttime", dest="sorttime", default=False,
                      action="store_true",
                      help="Sort results by time instead of alphabetically")
    #ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    ## if len(args) != 0:
    ##     optprs.error("incorrect number of arguments")

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


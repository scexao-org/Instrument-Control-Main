#!/usr/bin/env python
#
# Remote objects tests
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Wed Feb 22 16:36:40 HST 2012
#]
#

import sys, time
import remoteObjects as ro


class TestRO(ro.remoteObjectServer):

    def __init__(self, options, usethread=False):

        authDict = {}
        if options.auth:
            auth = options.auth.split(':')
            authDict[auth[0]] = auth[1]

        # Superclass constructor
        ro.remoteObjectServer.__init__(self, svcname=options.svcname,
                                       port=options.port,
                                       usethread=usethread,
                                       authDict=authDict,
                                       secure=options.secure,
                                       cert_file=options.cert)

    def recv(self, data, is_binary):
        if is_binary:
            data = ro.binary_decode(data)
            
        print "Length of data received: %d" % len(data)

        return 1


    def search(self, ra, dec, radius, mag):
        # For testing call overhead time
        # comment out print statement to measure call overhead
        print "ra=%f dec=%f radius=%f mag=%f" % (ra, dec, radius, mag)
        return ra


    def sleep(self, tag, sec):
        print "[%s] called, sleeping for %f sec..." % (tag, sec)
        time.sleep(sec)
        print "[%s] woke up!" % (tag)
        return tag


def client(options, data, is_binary):

    datafile = None
    if options.datafile:
        datafile = open(options.datafile, 'a')
            
    auth = None
    if options.auth:
        auth = options.auth.split(':')

    # Get handle to server
    testro = ro.remoteObjectProxy(options.svcname, auth=auth,
                                  secure=options.secure)

    print "Starting '%s' client..." % (options.svcname)
    size = len(data)

    time1 = time.time()

    if is_binary:
        data = ro.binary_encode(data)

    time2 = time.time()
    
    amount = 0.0
    for i in xrange(options.count):
        res = testro.recv(data, is_binary)
        amount += size

    tottime = time.time() - time1
    # Average time if more than one call made
    if options.count > 1:
        tottime = tottime / options.count

    print "Time taken: %f secs (%f bytes/sec) (enc: %f secs) " % \
          (tottime, amount/tottime, time2-time1)

    if datafile:
        # total bytes, count, total time, encode time, avg rate
        datafile.write("%d %d %f %f %f\n" % (
            size*options.count, options.count, tottime, time2-time1,
            amount/tottime))
        datafile.close()

    
def client2(options):

    datafile = None
    if options.datafile:
        datafile = open(options.datafile, 'a')
            
    auth = None
    if options.auth:
        auth = options.auth.split(':')

    # Get handle to server
    testro = ro.remoteObjectProxy(options.svcname, auth=auth,
                                  secure=options.secure, timeout=2.0)

    time1 = time.time()

    for i in xrange(options.count):
        res = testro.search(1.0, 2.0, 3.0, 4.0)

        if options.interval:
            time.sleep(options.interval)

    tottime = time.time() - time1
    time_per_call = tottime / options.count
    calls_per_sec = int(1.0 / time_per_call)

    print "Time taken: %f secs total  %f sec per call  %d calls/sec" % \
          (tottime, time_per_call, calls_per_sec)

    if datafile:
        # total bytes, count, total time, encode time, avg rate
        datafile.write("%d %d %f %f %f\n" % (
            size*options.count, options.count, tottime, time2-time1,
            amount/tottime))
        datafile.close()

    
def main(options, args):

    ro.init()
    
    select = options.action

    if select == 'server':
        testro = TestRO(options, usethread=False)

        print "Starting TestRO service..."
        try:
            testro.ro_start()

        except KeyboardInterrupt:
            print "Shutting down..."

    elif select == 'file':
        infile = args[0]

        # Create data block of fixed size
        try:
            in_f = open(infile, 'r')
        except IOError, e:
            print "Can't open input file '%s': %s" % (infile, str(e))
            sys.exit(1)

        # Convert binary file to test data
        data = in_f.read()
        in_f.close()

        client(options, data, True)
            
    elif select == 'status':
        table = args[0]
        
        import SOSS.status as st
        status = st.cachedStatusObj(options.statushost)
        status.updateTable(table)
        
        # Convert binary file to test data
        data = status.cache[table].table

        client(options, data, True)

    elif select == 'calls':
        client2(options)

    else:
        print "I don't know how to do '%s'" % select
        sys.exit(1)

    sys.exit(0)
            
if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage, version=('%%prog'))
    
    parser.add_option("--action", dest="action",
                      help="Action is server|file|status")
    parser.add_option("--auth", dest="auth",
                      help="Use authorization; arg should be user:passwd")
    parser.add_option("--cert", dest="cert",
                      help="Path to key/certificate file")
    parser.add_option("--count", dest="count", type="int",
                      default=1,
                      help="Iterate NUM times", metavar="NUM")
    parser.add_option("--datafile", dest="datafile", metavar='FILE',
                      help="Write statistics to FILE")
    parser.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    parser.add_option("--interval", dest="interval", type="float",
                      help="Wait NUM seconds between client calls",
                      metavar="NUM")
    parser.add_option("--port", dest="port", type="int",
                      help="Register using PORT", metavar="PORT")
    parser.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    parser.add_option("--secure", dest="secure", action="store_true",
                      default=False,
                      help="Use SSL encryption")
    parser.add_option("--statushost", dest="statushost",
                      default='mobs', metavar='HOST',
                      help="Status host is HOST")
    parser.add_option("--svcname", dest="svcname",
                      default='ro_test',
                      help="Register using service NAME", metavar="NAME")

    (options, args) = parser.parse_args(sys.argv[1:])

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


    

    

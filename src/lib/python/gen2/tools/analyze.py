#! /usr/bin/env python
#

import sys, time
import ssdlog
import tools.logs as lt
import SOSS.TCSint.Packet as pkt
import Bunch

TSCpktParser = pkt.PacketParser()
TSCpktParser.setHeaderParser(pkt.TSCHeaderParser())
TSCpktParser.addPayloadParser(pkt.CommandRequestPayloadParser())
TSCpktParser.addPayloadParser(pkt.CommandAckPayloadParser())
TSCpktParser.addPayloadParser(pkt.CommandCompletionPayloadParser())
TSCpktParser.addPayloadParser(pkt.AsyncMessagePayloadParser())

def parse_integui_timings(cmd_offset=197):

    cmd_time = None
    for line in sys.stdin.readlines():
        match = lt.ig_regex1.match(line)
        if not match:
            sys.stderr.write("ERROR MATCHING LINE --> %s\n" % line)
            continue
        
        rpcstr = match.group('rpcstr')
        
        if 'CT,CD' in rpcstr:
            cmd_time = lt.sosstime_to_sec(match.group('time'))
            cmd_str = rpcstr[cmd_offset:]
            continue
        
        if 'CT,EN' in rpcstr:
            end_time = lt.sosstime_to_sec(match.group('time'))
	    if cmd_time == None:
		continue
            elapsed_time = end_time - cmd_time
            print "%s [ % 10.3f ] %s" % (
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(cmd_time)),
                elapsed_time, cmd_str)
	    cmd_time = None


def parse_sch_timings():

    ins_seq = {}
    tsc_seq = {}
    tel_seq = {}
    
    for line in sys.stdin.readlines():
        match = lt.sch_regex1.match(line)
        if not match:
            sys.stderr.write("ERROR MATCHING LINE --> %s\n" % line)
            continue

        d = Bunch.Bunch(match.groupdict())
        d_time = lt.sosstime_to_sec(d.time1)
        #d_time = lt.sosstime_to_sec(d.time2)
        #print d

        if d.subsys == 'OSSS_InterfaceOBCP8':
            match2 = lt.ig_regex2.match(d.data)
            if match2:
                i = Bunch.Bunch(match2.groupdict())

                if d.wtf == 'dc':
                    seqnum = i.seqnum.strip().lstrip('0')
                    b = ins_seq.setdefault(seqnum, Bunch.Bunch())
                    b.cmd_time = d_time
                    b.cmd_str = i.payload.strip()
                    
                elif d.wtf == 'dr':
                    tup = i.payload.strip().split(',')
                    seqnum = tup[0].strip().lstrip('0')
                    b = ins_seq.setdefault(seqnum, Bunch.Bunch())
                    if i.pktsubtype == 'AB':
                        b.ack_time = d_time
                    elif i.pktsubtype == 'EN':
                        b.end_time = d_time
        
        #elif d.subsys == 'OSSS_InterfaceTSC':
        else:

            if d.wtf in ('bc', 'ic', 'hc'):
                tup = d.data.strip().split()
                #print tup
                seqnum = tup[2][5:]
                print ">>>%s" % seqnum
                cmd_str = ' '.join(tup[3:])
                b = tel_seq.setdefault(seqnum, Bunch.Bunch())
                b.cmd_time = d_time
                b.cmd_str = cmd_str

            elif d.wtf in ('br', 'ir', 'hr'):
                tup = d.data.strip().split()
                #print tup
                seqnum = tup[0][4:]
                print "<<<%s" % seqnum
                b = tel_seq.setdefault(seqnum, Bunch.Bunch())
                b.end_time = d_time
                
##             elif d.wtf in ('cc', 'cr'):
##                 h, p = TSCpktParser.parse(d.data)
##                 seqnum = p.seqNum
##                 b = tsc_seq.setdefault(seqnum, Bunch.Bunch())

##                 if h.messageType == 'CD':
##                     b.cmd_time = d_time
##                     b.cmd_str = '%6.6s %s' % (p.commandId, p.commandParam)

##                 elif h.messageType == 'CA':
##                     b.ack_time = d_time

##                 elif h.messageType == 'CE':
##                     b.end_time = d_time
        
    vals2 = ins_seq.values()
    vals2.extend(tel_seq.values())
    #vals2 = tel_seq.values()

    vals = []
    for val in vals2:
        try:
            t1 = val.cmd_time
            t2 = val.end_time

            val.elapsed_time = t2 - t1
            vals.append(val)
        except KeyError:
            continue

    vals.sort(lambda x,y: int(x.cmd_time - y.cmd_time))

    for val in vals:
        print "%s [ % 10.3f ] %s" % (
            time.strftime("%Y-%m-%d %H:%M:%S",
                          time.localtime(val.cmd_time)),
            val.elapsed_time, val.cmd_str)
        

def main(options, args):

    if options.type == 'ig':
        parse_integui_timings(cmd_offset=options.offset)
    else:
        parse_sch_timings()
    

if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("-t", "--type", dest="type", default="ig",
                      help="Type of analysis to do")
    optprs.add_option("-o", "--offset", dest="offset", type="int",
		      default=197,
                      help="Offset to command string in packet")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    if len(args) != 0:
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

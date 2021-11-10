#!/usr/bin/env python

import os
import sys
import time
import datetime
import threading

import ssdlog

# Notification Receiver (TRAP)
from pysnmp.carrier.asynsock.dispatch import AsynsockDispatcher
from pysnmp.carrier.asynsock.dgram import udp
from pyasn1.codec.ber import decoder
from pysnmp.proto import api

from notify_me import *

class Shutdown(object):

    def __init__(self, power_off, logger):
        self.power_off=power_off
        self.rlock=threading.RLock() 
        self.logger=logger

 
    def shutdown(self, msg):
        ''' shutdown obcps then fldmon'''
  
        res=self.shutdown_obcp(msg)
        if res:
            self.logger.debug('shutting down obcp done, begin shutting down fldmon ')
            self.shutdown_fldmon()
            
    def shutdown_obcp(self, msg):

        with self.rlock:
            if not os.path.isfile(self.power_off):
                self.logger.info('creating shutdown file....')
                try:
                    file(self.power_off, 'w').close()
                except Exception as e:
                    self.logger.error('error: creating power_off file. %s' %e)
                    msg='%s\nerror: making obcp poweroff file. \ncreate %s @fldmon manually now!' %(msg, self.power_off)
                else:
                    self.logger.info('sending obcp shutdown msg...')
                    msg='%s. shutting down obcp!' %(msg)
                finally:
                    notify_snmp(msg=msg,  logger=self.logger)
                    return True
            else:
                self.logger.info('%s already exists.' %self.power_off)
                return False    

    def shutdown_fldmon(self):

        sec = 300  # wait until obcp shutted down
        self.logger.info('shutting down fldmon in %d min....' %(sec/60))

        msg='Shutting down fldmon in %d min!' %(sec/60)
        notify_snmp(msg=msg,  logger=self.logger)

        # wait a couple of  min to provide enough time for shutting down obcp.
        time.sleep(sec)  # 5(testing) -> 300

        cmd='/sbin/shutdown -h now'

        # test cmd, making it fail
        #cmd='lss -l'        
        
        res=os.system(cmd)
        if res:
            self.logger.error('error: shutting down fldmon.  shutdown fldmon manually...')
            msg='error: shutting down fldmon.  shutdown fldmon manually now!' 
            notify_snmp(msg=msg, logger=self.logger)

class SnmpTrap(object):

    def __init__(self, power_off, logger):
        self.logger=logger
        self.ev_quit = threading.Event()

        self.hosts= Shutdown(power_off, logger)

    def __watching_onbattery(self):

        timeout=600  #  wait 10 min
        cur_time = time.time()
        end_time = cur_time + timeout

        while cur_time < end_time and not self.ev_quit.is_set():
            
            time.sleep(1)
            cur_time = time.time()
            self.logger.debug('looping.. cur=%f  end=%f  e-c=%f' %(cur_time, end_time, end_time-cur_time) )

        self.logger.debug('out of loop. quit status is %s' %self.ev_quit.is_set())

        if not self.ev_quit.is_set():
            self.logger.debug('calling shutdown procedure...')
            msg='on-battery timed out(%d sec)...' %timeout
            self.hosts.shutdown(msg)


    def online(self):

        self.ev_quit.set()

        # with self.rlock:
        #     try:
        #         os.remove(self.power_off)
        #     except Exception as e:
        #         self.logger.warn('warn: online removing a file... no power-off file created yet?  %s' %e)

        msg='Summit UPS online...'
        notify_snmp(msg=msg, logger=self.logger) 
        

    def onbattery(self):


        self.logger.debug('1. threading Count %d' %threading.active_count())

        if threading.active_count() == 1:
            self.ev_quit.clear()
            watch=threading.Thread(target=self.__watching_onbattery, args=())
            watch.start()
            msg='Summit UPS onbattery...'
            notify_snmp(msg=msg, logger=self.logger)
        else:
            self.logger.info('watching on battery is already running...')   

        self.logger.debug('2. threading Count: %d' %threading.active_count())
    
    def lowbattery(self):
        
        self.ev_quit.set()  # make out of watching-onbattery loop
        msg='Summit UPS low battery...'
        self.hosts.shutdown(msg)

    def interpret_trap(self, msg, trap_num):

        try:
            trap_num = int(trap_num)
        except Exception:
            return 

        ups3="object=1.3.6.1.4.1.476.1.1.1.1.11"
        ups4_1="object=1.3.6.1.2.1.33.1.6.3.2"
        ups4_2="object=1.3.6.1.2.1.33.1.6.3.3"
 
        if ups3 in msg:
            if trap_num == 7:
                self.logger.debug('ups3 online...')
                self.online()
            elif trap_num == 3:
                self.logger.debug('ups3 low battery...')
                self.lowbattery()
            elif trap_num == 4:
                self.logger.debug('ups3 on battery...')
                self.onbattery()
            else:
                self.logger.debug('ups3 undefined number .... %d' %trap_num)
        elif ups4_1 in msg:
            if trap_num == 4:
                self.logger.debug('ups4 online...')
                self.online()
            elif trap_num == 3:
                self.logger.debug('ups4 on  battery...')
                self.onbattery()
            else:
                self.logger.debug('ups4 undefined number .... %d' %trap_num)

        elif ups4_2 in msg:
            if trap_num == 3:
                self.logger.debug('ups4 low battery...')
                self.lowbattery()
            else:
                self.logger.debug('ups4 undefined number .... %d' %trap_num)
        else:
            self.logger.debug('no ups3/4 in msg. %s' %msg)   

    def trap_cb(self, transportDispatcher, transportDomain, transportAddress, wholeMsg):

        self.logger.debug('msg=<%s>' %str(wholeMsg))

        msg_strip=wholeMsg.strip()
        self.logger.debug('msg_strip=<%s>' %str(msg_strip))

        if not msg_strip:
            self.logger.warn('warn: msg is an empty <%s>' %str(wholeMsg))
            return 
        
        while wholeMsg:

            msgVer = int(api.decodeMessageVersion(wholeMsg))
            if api.protoModules.has_key(msgVer):
                pMod = api.protoModules[msgVer]
            else:
                self.logger.warn('Unsupported SNMP version %s' % msgVer)
                return
            reqMsg, wholeMsg = decoder.decode(
                wholeMsg, asn1Spec=pMod.Message(),
                )
            self.logger.debug('Notification message from %s:%s: ' % (transportDomain, transportAddress))
            reqPDU = pMod.apiMessage.getPDU(reqMsg)
            if reqPDU.isSameTypeWith(pMod.TrapPDU()):
                if msgVer == api.protoVersion1:
                    self.logger.debug('Enterprise: %s' % (
                        pMod.apiTrapPDU.getEnterprise(reqPDU).prettyPrint()
                        ))
                    self.logger.debug('Agent Address: %s' % (
                        pMod.apiTrapPDU.getAgentAddr(reqPDU).prettyPrint()
                        ))
                    self.logger.debug('Generic Trap: %s' % (
                        pMod.apiTrapPDU.getGenericTrap(reqPDU).prettyPrint()
                        ))
                    trap_num=pMod.apiTrapPDU.getSpecificTrap(reqPDU).prettyPrint()
                    self.logger.debug('Specific Trap: %s' % (trap_num))

                    self.logger.debug('Uptime: %s' % (
                        pMod.apiTrapPDU.getTimeStamp(reqPDU).prettyPrint()
                        ))
                    varBinds = pMod.apiTrapPDU.getVarBindList(reqPDU)
                else:
                    varBinds = pMod.apiPDU.getVarBindList(reqPDU)
                #print 'Var-binds:' , varBinds

                for oid, val in varBinds:
                    self.logger.debug('[%s] = [%s]' % (oid.prettyPrint(), val.prettyPrint()))
                    msg=val.prettyPrint().split()
                    self.logger.debug('val=%s' %msg)
                    self.interpret_trap(msg, trap_num)
        return wholeMsg


def main(options, args):

    logname = 'summit_ups'
    logger = ssdlog.make_logger(logname, options)

    power_off='obcpPoff'
    power_off=os.path.join(options.dir, power_off)

    try:
        os.remove(power_off)
    except Exception as e:
        logger.warn('warn: is %s there??  %s' %(power_off, e))      

    snmp=SnmpTrap(power_off, logger)

    try:
        transportDispatcher = AsynsockDispatcher()
        transportDispatcher.registerTransport(udp.domainName, udp.UdpSocketTransport().openServerMode(('%s' %options.mgrhost , 162)))
        transportDispatcher.registerRecvCbFun(snmp.trap_cb)
        transportDispatcher.jobStarted(1) # this job would never finish
        transportDispatcher.runDispatcher()
    except KeyboardInterrupt:
        logger.info('keyboard interrupting...')
        snmp.ev_quit.set()
    except Exception as e:
        logger.error('error: %s' %e)
        snmp.ev_quit.set() 
        logger.error('error: snmp trap terminated..')

if __name__ == '__main__':

    # Parse command line options with nifty new optparse module
    from optparse import OptionParser

    usage = "usage: %prog [options] command [args]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")

    optprs.add_option("--dir", dest="dir", default="/gen2/poweroff",
                      help="Specify dir to create poweroff-file")

    optprs.add_option("--mgrhost", dest="mgrhost", default="fldmon.sum.subaru.nao.ac.jp",
                      help="Specify snmp manager host")

    optprs.add_option("--pidfile", dest="pidfile", metavar="FILE",
                      help="Write process pid to FILE")

    optprs.add_option("--detach", dest="detach", default=False,
                      action="store_true",
                      help="Detach from terminal and run as a daemon")

    optprs.add_option("--kill", dest="kill", default=False,
                      action="store_true",
                      help="Kill running instance of datasink")

    ssdlog.addlogopts(optprs)
    (options, args) = optprs.parse_args(sys.argv[1:])

    # Write out our pid
    if not options.pidfile:
        options.pidfile=('/var/run/snmptrap.pid')

    if options.detach:
        import myproc
        
        print "Detaching from this process..."
        sys.stdout.flush()
        try:
            try:
                
                logfile = '/dev/null'
                #logfile = ('/var/log/anasink_%d.log' % (options.port))
                child = myproc.myproc(main, args=[options, args],
                                      pidfile=options.pidfile, detach=True,
                                      stdout=logfile,
                                      stderr=logfile)
                 
                child.wait()

            except Exception as e:
                print "Error detaching process: %s" % (str(e))

            # TODO: check status of process and report error if necessary
        finally:
            sys.exit(0)

    if options.kill:
     
        import signal
        #exit(options.pidfile)

        try:
            try:
                pid_f = open(options.pidfile, 'r')
                pid = int(pid_f.read().strip())
                pid_f.close()

                print "Killing %d..." % (pid)
                os.kill(pid, signal.SIGKILL)
                print "Killed."

            except IOError, e:
                print "Cannot read pid file (%s): %s" % (
                    options.pidfile, str(e))
                sys.exit(1)

            except OSError, e:
                print "Error killing pid (%d): %s" % (
                    pid, str(e))
                sys.exit(1)
                
        finally:
            sys.exit(0)



    #if not len(args)==1:
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



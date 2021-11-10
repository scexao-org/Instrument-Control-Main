#!/usr/bin/env python
#
# Test cases for TaskManager
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Jul  8 11:14:42 HST 2010
#]
# Bruce Bon -- last edit 2007-10-01
#

import unittest
import time
import sys, os
import threading, Queue
import logging, ssdlog

import environment

import TaskManager
import SOSS.INSint as INSint
import SOSS.DAQtk as DAQtk
import SOSS.SIMCAM as SIMCAM
import SOSS.STARSint as STARSint

import SOSS.TCSint.Interface.CommandManager as CommandManager
import SOSS.TCSint.Interface.TCSint         as TCSint
import SOSS.TCSint.tests.TCSintTestCase     as TCSintTestCase

import Bunch
import SOSS.SOSSrpc as SOSSrpc
import remoteObjects as ro
import remoteObjects.Monitor as Monitor

## import archiver
## import mysqlarchiver
import astro.fitsutils as fitsutils

import g2Task

# TEMP: till we get configuration management worked out
# Path to where SIMCAM module is loaded
sys.path.insert(0, "../SOSS/SIMCAM/cams/SIMCAM")

# Create top level logger.
logger = logging.getLogger('testfunc_TaskManager')
logger.setLevel(logging.ERROR)

fmt = logging.Formatter(ssdlog.STD_FORMAT)

stderrHdlr = logging.StreamHandler()
stderrHdlr.setFormatter(fmt)
logger.addHandler(stderrHdlr)


LOGDEBUG = False

# ========================================================================
class TestInsCmds(unittest.TestCase):
    """This class tests invoking round-trip instrument commands through
    the task manager.
    """

    def setUp(self):
        self.env = environment.MockEnvironment()
        self.env.removeTestDirs()  # just in case
        self.env.makeDirs()
        self.obcpnum = 9
        self.fmtstr = 'EXEC SIMCAM FITS_FILE MOTOR=%(motor)s FRAME_NO=%(frame_no)s DELAY=%(delay)f'
        self.ev_quit = threading.Event()

        # Create monitor and other allocations
        self.monitor_name = 'monitor'
        self.monitor = Monitor.Minimon(self.monitor_name, logger)
        
        myhost = SOSSrpc.get_myhost(short=True)
        statusDict = {}
        
        # Create and start the instrument interface
        self.insint = INSint.ocsInsInt(self.obcpnum, myhost, self.env.ARCH_PROP,
                                       statusDict, db=self.monitor,
                                       logger=logger, ev_quit=self.ev_quit)
        self.insint.start()

        # This is our set of allocations
        self.alloc = Bunch.Bunch(monitor=self.monitor,
                                 INSint9=self.insint,
                                 status=None)

        # Create and start SIMCAM
        ocsint = DAQtk.ocsInt(self.obcpnum, logger=logger, ev_quit=self.ev_quit)
        self.simcam = SIMCAM.Instrument(logger, ev_quit=self.ev_quit,
                                        ocsint=ocsint, allowNoPara=True,
                                        env=self.env)
        self.simcam.loadPersonality('SIMCAM')
        #self.simcam.loadParaBuf(fits_file_para)
        self.simcam.start()

        # Create and start our task manager
        self.tm = TaskManager.TaskManager(logger=logger, ev_quit=self.ev_quit,
                                          internal_allocs=self.alloc)
        self.tm.setAllocs(['monitor', 'INSint9'])
        self.tm.start()


    def tearDown(self):
        self.tm.monitor.releaseAll()

        self.tm.stop()
        self.insint.stop()
        self.simcam.stop()

        self.env.removeTestDirs()


    def test_rawCmdSend(self):
        if  LOGDEBUG:
            print '\ntest_rawCmdSend'
        # Load the class file containing g2 base tasks
        self.tm.loadModule('g2Task')

        # Ask TM to instantiate a "raw" command send task
        tasktag = self.tm.addTask('INSintTask',
                                  ['INSint9', self.fmtstr, None],
                                  {'motor': 'ON',
                                   'frame_no': 'SIMA00000001',
                                   'delay': 0.0})
        self.assertNotEquals(tasktag, ro.ERROR)
        #? print "TASK TAG -----> %s <-----" % tasktag

        # Wait for 20 sec. or end of transaction, which ever comes first.
        (okflag, res) = self.monitor.get_wait(tasktag, 'task_end', timeout=10.0)
        self.assertEquals(True, okflag)
        self.assertEquals(True, type(res) == float)

        # Get all items currently associated with this transaction
        vals = self.monitor.getitems_suffixOnly(tasktag)
        #print "VALS ARE: %s" % str(vals)
        self.assertNotEquals(ro.ERROR, vals)

        self.assert_(vals.has_key('time_start'))
        time_start = vals['time_start']
        self.assertNotEquals(0, time_start)

        # command sanity check
        self.assert_(vals.has_key('cmd_time'))
        cmd_time = vals['cmd_time']
        self.assert_(time_start <= cmd_time)

        # Command string is same as we thought we sent
        self.assert_(vals.has_key('cmd_str'))

        # Ack sanity check
        self.assert_(vals.has_key('ack_time'))
        ack_time = vals['ack_time']
        self.assert_(cmd_time <= ack_time)

        self.assert_(vals.has_key('ack_result'))
        self.assertEquals(0, vals['ack_result'])

        # End sanity check
        self.assert_(vals.has_key('end_time'))
        end_time = vals['end_time']
        self.assert_(ack_time <= end_time)

        self.assert_(vals.has_key('end_result'))
        self.assertEquals(0, vals['end_result'])

        self.assert_(vals.has_key('end_payload'))
        self.assertEquals(['COMPLETE'], vals['end_payload'])

        self.assert_(vals.has_key('done'))
        done = vals['done']
        self.assertEquals(True, done)

        self.assert_(vals.has_key('time_done'))
        time_done = vals['time_done']
        self.assertEquals(True, type(time_done) == float)

        self.assert_(vals.has_key('msg'))


    def test_rawCmdSendwDelay(self):
        if  LOGDEBUG:
            print '\ntest_rawCmdSendwDelay'
        # Load the class file containing g2 base tasks
        self.tm.loadModule('g2Task')

        # Ask TM to instantiate a "raw" command send task
        tasktag = self.tm.addTask('INSintTask',
                                  ['INSint9', self.fmtstr, None],
                                  {'motor': 'ON',
                                   'frame_no': 'SIMA00000001',
                                   'delay': 2.0})
        self.assertNotEquals(tasktag, ro.ERROR)
        #print "TASK TAG -----> %s <-----" % tasktag

        # Wait for 10 sec. or end of transaction, which ever comes first.
        (okflag, res) = self.monitor.get_wait(tasktag, 'task_end', timeout=10.0)
        self.assertEquals(True, okflag)
        self.assertEquals(True, type(res) == float)

        # Get all items currently associated with this transaction
        vals = self.monitor.getitems_suffixOnly(tasktag)
        #print "VALS ARE: %s" % str(vals)
        self.assertNotEquals(ro.ERROR, vals)

        self.assert_(vals.has_key('task_start'))
        task_start = vals['task_start']
        self.assertEquals(True, type(task_start) == float)

        self.assert_(vals.has_key('time_start'))
        time_start = vals['time_start']
        self.assertEquals(True, type(time_start) == float)

        # command sanity check
        self.assert_(vals.has_key('cmd_time'))
        cmd_time = vals['cmd_time']
        self.assertEquals(True, type(cmd_time) == float)
        self.assert_(time_start <= cmd_time)

        # Command string is same as we thought we sent
        self.assert_(vals.has_key('cmd_str'))

        # Ack sanity check
        self.assert_(vals.has_key('ack_time'))
        ack_time = vals['ack_time']
        self.assertEquals(True, type(ack_time) == float)
        self.assert_(cmd_time <= ack_time)

        self.assert_(vals.has_key('ack_result'))
        self.assertEquals(0, vals['ack_result'])

        # End sanity check
        self.assert_(vals.has_key('end_time'))
        end_time = vals['end_time']
        self.assertEquals(True, type(end_time) == float)
        self.assert_(ack_time <= end_time)

        self.assert_(vals.has_key('end_result'))
        self.assertEquals(0, vals['end_result'])

        self.assert_(vals.has_key('end_payload'))
        self.assertEquals(['COMPLETE'], vals['end_payload'])

        self.assert_(vals.has_key('done'))
        done = vals['done']
        self.assertEquals(True, done)

        self.assert_(vals.has_key('time_done'))
        time_done = vals['time_done']
        self.assertEquals(True, type(time_done) == float)

        self.assert_(vals.has_key('msg'))

        # Assert that the frame has not been transferred yet!
        (okflag, res) = self.monitor.get_nowait('mon.frame', 'SIMA00000001')
        self.assertEquals(False, okflag)

        # Wait for 10 sec. or end of transaction, which ever comes first.
        (okflag, res) = self.monitor.get_wait('mon.frame.SIMA00000001',
                                              'done', timeout=10.0)
        self.assertEquals(True, okflag)

        # Get all items currently associated with this transaction
        vals = self.monitor.getitems_suffixOnly('mon.frame.SIMA00000001')
        #print "VALS ARE: %s" % str(vals)
        self.assertNotEquals(ro.ERROR, vals)

        # command sanity check
        self.assert_(vals.has_key('time_start'))
        time_start = vals['time_start']
        self.assert_(time_start > end_time)

        # Ack sanity check
        self.assert_(vals.has_key('time_done'))
        time_done = vals['time_done']
        self.assert_(time_start <= time_done)

        # End sanity check
        self.assert_(vals.has_key('status'))
        self.assertEquals(0, vals['status'])

        self.assert_(vals.has_key('filepath'))



class TestSTARSintTask(unittest.TestCase):
    """This class tests invoking round-trip STARS interface commands through
    the task manager.
    """

    def setUp(self):
        self.env = environment.MockEnvironment()
        self.env.removeTestDirs()  # just in case
        self.env.makeDirs()
        self.obcpnum = 9
        self.ev_quit = threading.Event()

        # Create monitor and other allocations
        self.monitor_name = 'monitor'
        self.monitor = Monitor.Minimon(self.monitor_name, logger)
        
        myhost = SOSSrpc.get_myhost(short=True)

        # Create and start STARS simulator
        self.stars = STARSint.STARSsimulator(logger=logger, ev_quit=self.ev_quit)
        # Tell STARS how to contact us to copy files
        STARSint.add_transferParams('*',
                                    transfermethod='ssh',
                                    raidpath=self.env.ARCH_PATH,
                                    #username=os.getlogin(),
                                    username=os.environ['LOGNAME'],
                                    password='xxxxxx')
        
        self.stars.start()

        # Create and start the STARS interface
        self.starsint = STARSint.STARSinterface(starshost=myhost,
                                                db=self.monitor, logger=logger,
                                                ev_quit=self.ev_quit)
        self.starsint.start()

        # This is our set of allocations
        self.alloc = Bunch.Bunch(monitor=self.monitor,
                                 STARSint=self.starsint,
                                 status=None)

        # Create and start our task manager
        self.tm = TaskManager.TaskManager(logger=logger, ev_quit=self.ev_quit,
                                          internal_allocs=self.alloc)
        self.tm.setAllocs(['monitor', 'STARSint'])
        self.tm.start()


    def tearDown(self):

        self.tm.stop()

        self.stars.stop()
        self.starsint.stop()

        self.env.removeTestDirs()


    def makefits(self, fitsfile, frame_no):
        
        # fake exposure
        hdrkwds = {
            'prop-id': self.env.proposal,
            'frameid': frame_no,
            #'obcpmode': self.mode,
            }
        fitsutils.make_fakefits(fitsfile, hdrkwds, 10, 5)


    def test_sendToSTARS(self):
        if  LOGDEBUG:
            print '\ntest_sendToSTARS'
        # Load the class file containing g2 base tasks
        self.tm.loadModule('g2Task')

        # Generate a FITS file
        self.frame_no = 'SIMA00000001'
        self.fitsfile = '%s/%s.fits' % (self.env.INST_PATH, self.frame_no)
        self.makefits(self.fitsfile, self.frame_no)
        
        # Ask TM to instantiate a STARSint command send task
        tasktag = self.tm.addTask('STARSintTask',
                                  ['STARSint', self.fitsfile],
                                  {})
        self.assertNotEquals(tasktag, ro.ERROR)
        #print "TASK TAG -----> %s <-----" % tasktag

        # Wait for 20 sec. or end of transaction, which ever comes first.
        (okflag, res) = self.monitor.get_wait(tasktag, 'task_end', timeout=20.0)
        self.assertEquals(True, okflag)
        self.assertEquals(True, type(res) == float)

        # Get all items currently associated with this transaction
        vals = self.monitor.getitems_suffixOnly(tasktag)
        #print "VALS ARE: %s" % str(vals)
        self.assertNotEquals(ro.ERROR, vals)

        self.assert_(vals.has_key('time_start'))
        time_start = vals['time_start']
        self.assertNotEquals(0, time_start)

        # command sanity check
        self.assert_(vals.has_key('cmd_time'))
        cmd_time = vals['cmd_time']
        self.assert_(time_start <= cmd_time)

        # Proper values are present
        self.assert_(vals.has_key('fitspath'))
        #self.assert_(vals.has_key('propid'))
        #self.assert_(vals.has_key('indexdir'))

        # Ack sanity check
        self.assert_(vals.has_key('ack_time'))
        ack_time = vals['ack_time']
        self.assert_(cmd_time <= ack_time)

        self.assert_(vals.has_key('ack_result'))
        self.assertEquals(0, vals['ack_result'])

        # End sanity check
        self.assert_(vals.has_key('end_time'))
        end_time = vals['end_time']
        self.assert_(ack_time <= end_time)

        self.assert_(vals.has_key('end_result'))
        self.assertEquals(0, vals['end_result'])

        self.assert_(vals.has_key('end_status1'))
        self.assertEquals(0, vals['end_status1'])

        self.assert_(vals.has_key('end_status2'))
        self.assertEquals(0, vals['end_status2'])

        # Verify that the correct files have ended up in the destination
        # directory
        dst_fits = '%s/%s.fits' % (self.env.ARCH_PATH, self.frame_no)
        dst_indx = '%s/%s.index' % (self.env.ARCH_PATH, self.frame_no)
        self.assert_(os.path.exists(dst_fits))
        self.assert_(os.path.exists(dst_indx))


# Temporarily commented out while we figure out what to do about Mark's
# stuff...
class fooTestArchCmds:#(unittest.TestCase):
    """This class tests invoking round-trip instrument commands with
    archiving through the task manager.
    """

    def setUp(self):
        self.env = environment.MockEnvironment()
        self.env.removeTestDirs()  # just in case
        self.env.makeDirs()
        mysqlarchiver._deleteMySQLArchiveDb()  # just in case
        (self.env.con,self.env.cur) = mysqlarchiver.initMySQLArchiveDb()
        self.framedb = archiver.SimFrameDBint(self.env)
        #import test_archiver
        #self.framedb = test_archiver.SimTestFrameDBint(self.env)
        self.iaq = 'SUKA'
        self.archmon = archiver.ArchiveMonitor(self.framedb,self.env)
        self.archivemgr = archiver.ArchiveMgr(self.framedb,self.archmon, self.env)
        self.framesrcSUKA = self.archivemgr.createFrameSourceA("SUK")
        self.basic = ['SIMPLE','BITPIX','NAXIS','EXTEND','PROP-ID',
                      'FRAMEID','RANDOM','OBCPMODE']
        self.basic.sort()
        self.archivemgr.registerKeywords(self.iaq,self.basic)
        import random
        #randokm.seed(0)  # force a random but repeatable sequence
        self.random = str(random.randrange(1000,1010))
        self.mode = "mode_"+str(random.randrange(0,10))

        self.obcpnum = 9
        self.ev_quit = threading.Event()
        # Timeout value for this task
        self.timeout = 20.0

        # Create monitor and other allocations
        self.monitor_name = 'monitor'
        self.monitor = Monitor.Minimon(self.monitor_name, logger=logger)
        
        myhost = SOSSrpc.get_myhost(short=True)
        statusDict = {}
        
        # Create and start the instrument interface
        self.insint = INSint.ocsInsInt(self.obcpnum, myhost, self.env.ARCH_PROP,
                                       statusDict, db=self.monitor,
                                       logger=logger, ev_quit=self.ev_quit)
        self.insint.start()

        # This is our set of allocations
        self.alloc = Bunch.Bunch(monitor=self.monitor,
                                 INSint9=self.insint,
                                 archmgr=self.archivemgr,
                                 status=None)

        # Create and start SIMCAM
        ocsint = DAQtk.ocsInt(self.obcpnum, logger=logger, ev_quit=self.ev_quit)
        simcam = SIMCAM.SIMCAM(logger, self.env, ev_quit=self.ev_quit)
        self.simcam = SIMCAM.OCSInterface(logger, ev_quit=self.ev_quit,
                                          ocsint=ocsint, instrument=simcam)
        self.simcam.start()

        # Create and start our task manager
        self.tm = TaskManager.TaskManager(logger=logger, internal_allocs=self.alloc)
        self.tm.setAllocs(['monitor', 'INSint9', 'archmgr'])
        self.tm.start()


    def tearDown(self):

        self.tm.stop()

        self.insint.stop()
        self.simcam.stop()
        self.env.removeTestDirs()
        #?mysqlarchiver._deleteMySQLArchiveDb()


    def test_snapCmd(self):
        if  LOGDEBUG:
            print '\ntest_snapCmd'
        #1 environment is up
        #  stat paths - since they should exist
        self.assert_(self.env.gettime())
        self.assert_(os.path.exists(self.env.ARCH_PATH))
        self.assert_(os.path.exists(self.env.INST_PATH))
        self.assert_(os.path.exists(self.env.ARCH_PROP))

        #2 database is up and running
        #3 plus archmon is OK, via no frames have yet been furnished database query
        self.assertEquals({},self.archmon.listFurnished())
        
        self.assertEquals({}, self.archmon.listFurnished())
        self.NUMFRAMES = 1
        self.framelist = self.framesrcSUKA.furnishNewFrames(self.NUMFRAMES)

        #5 frame src is up
        #4 as well as archmgr
        #  stat the file is not there
        self.assertEquals(self.NUMFRAMES, len(self.framelist))
        self.frameid = self.framelist[0].frameid
        self.assert_(not os.path.exists(self.framelist[0].path))

        #6 the monitor is running
        self.assertEquals(self.monitor_name, self.monitor.svcname)

        #7 the monitor bundle is empty
        # Not an accurate test, there will be root task entries there and
        # possibly other subsystem info
        #self.assertEquals([], self.monitor.nsb.keys())

        #8 instrument interface
        #? do SOSS_rpc queries of the servers and make sure they are up

        #9 simcam instrument
        #? do SOSS_rpc queries of the servers and make sure they are up

        #10a task manager is up but modules bundle is empty
        self.assertEquals([], self.tm.modules.keys())

        # Load the class file containing g2 base tasks
        self.g2TaskName = 'g2Task'
        self.tm.loadModule(self.g2TaskName)

        #10b task manager is up and modules bundle contains module name
        self.assertEquals([self.g2TaskName], self.tm.modules.keys())

     ### now we know everything is up and running!

        # Ask TM to instantiate a snapCmd task
        self.snap_cmd_format_str = 'EXEC SUKA FITS_FILE MOTOR=ON FRAME_NO=%(frame_no)s RANDOM=%(random)s'
        self.snap_cmd_params_dict = { 'frame_no': self.frameid,
                                      'random': self.random }
        tasktag = self.tm.addTask('snapCmd',
                                  ['INSint9', self.snap_cmd_format_str, self.framelist],
                                  self.snap_cmd_params_dict)
        self.assertNotEquals(tasktag, ro.ERROR)

        # Wait for INSint to complete command, or time out, whichever
        # comes first...
        (okflag, res) = self.monitor.get_wait(tasktag, 'task_end',
                                              timeout=self.timeout)
        self.assert_(okflag)
        self.assertEquals(True, type(res) == float)

        # Get all items currently associated with this transaction
        vals = self.monitor.getitems_suffixOnly(tasktag)
        #print "VALS ARE: %s" % str(vals)
        self.assertNotEquals(ro.ERROR, vals)

        self.assert_(vals.has_key('time_start'))
        time_start = vals['time_start']
        self.assertNotEquals(0, time_start)

        # command sanity check
        self.assert_(vals.has_key('cmd_time'))
        cmd_time = vals['cmd_time']
        self.assert_(time_start <= cmd_time)

        # Command string is same as we thought we sent
        self.assert_(vals.has_key('cmd_str'))
        self.assertEquals(self.snap_cmd_format_str % self.snap_cmd_params_dict,
                          vals['cmd_str'])

        # Ack sanity check
        self.assert_(vals.has_key('ack_time'))
        ack_time = vals['ack_time']
        self.assert_(cmd_time <= ack_time)

        self.assert_(vals.has_key('ack_result'))
        self.assertEquals(0, vals['ack_result'])

        # End sanity check
        self.assert_(vals.has_key('end_time'))
        end_time = vals['end_time']
        self.assert_(ack_time <= end_time)

        self.assert_(vals.has_key('end_result'))
        self.assertEquals(0, vals['end_result'])

        self.assert_(vals.has_key('end_payload'))
        self.assertEquals(['COMPLETE'], vals['end_payload'])


        # the file should be there now
        self.assert_(os.path.exists(self.framelist[0].path))
        
        self.assertEquals([f.frameid for f in self.framelist],
                          self.archmon.listSnapStartIDs())

        self.assertEquals([f.frameid for f in self.framelist],
                          self.archmon.listSnapDoneIDs())
        import pyfits
        self.archivemgr.registerFitsHeaders(self.framelist[0].frameid[:4],self.framelist[0].twid,pyfits.open(self.framelist[0].path))
        res = self.archmon.listHeaders(self.iaq)
        self.assertEquals(self.frameid, res['FRAMEID'])
        self.assertEquals(self.random, res['RANDOM'])
        #self.assertEquals(self.mode, res['OBCPMODE'])

        self.assertEquals([f.frameid for f in self.framelist],
                          self.archmon.listSnapDoneIDs())
        #? temporarily here
        #import pprint
        #pprint.pprint(res)


    def __testJustSetupTeardown1(self):
        pass
        
    def __testJustSetupTeardown2(self):
        pass
        

class TestTCSCmds(unittest.TestCase):
    monitorName = 'monitor'
    intName     = 'TSC'

    def setUp(self):
        import rpc
        
        self.ev_quit = threading.Event()

        # Create monitor and other allocations
        self.monitor = Monitor.Minimon(TestTCSCmds.monitorName, logger)

#
#        commandManager = CommandManager.CommandManager(None)
#        commandSender  = CommandManager.CommandSender(commandManager=commandManager,
#                                            timeout=0.1,
#                                            host='localhost',
#                                            prog=0x20000011,
#                                            uid=CommandManager.TCS_UID,
#                                            gid=CommandManager.TCS_GID )
#        #humm...
#        commandManager.commandQueue = commandSender.commandQueue
#        commandReceiver = CommandManager.ReplyReceiver(host="",
#                                            prog=0x20000012,
#                                            vers=1,
#                                            port=0,
#                                            commandManager=commandManager)

        commandManager  = TCSintTestCase.MockCommandManager()
        commandManager.mockResult = True
        commandSender   = TCSintTestCase.MockTCSClient()
        commandReceiver = TCSintTestCase.MockReplyReceiver(rpc.Packer(), 
                                                           rpc.Unpacker('\x00\x00\x00=CEOBS%TSC%00002006020719514370028000005930020000000COMPLETE%%\x00\x00\x00'), 
                                                           commandManager)
        ddSequenceGenerator = TCSint.FakeSequenceGenerator()
        
        self.tCSint   = TCSint.TCSint(self.monitor,
                                      commandManager, 
                                      commandSender, 
                                      commandReceiver, 
                                      ddSequenceGenerator)

        self.tCSint.start()

        self.alloc = Bunch.Bunch(monitor=self.monitor,
                                 TSC=self.tCSint,
                                 status=None)

        # Create and start our task manager
        self.tm = TaskManager.TaskManager(logger=logger, ev_quit=self.ev_quit,
                                          internal_allocs=self.alloc)
        self.tm.setAllocs([TestTCSCmds.monitorName, 
                           TestTCSCmds.intName])
        self.tm.start()

    def tearDown(self):
        self.tm.stop()
        self.tCSint.stop()

    def testSetupTearDown(self):
        pass

    def testCmdSend(self):
        if  LOGDEBUG:
            print '\ntestCmdSend'
        self.tm.loadModule('g2Task')

        tasktag = self.tm.addTask('TCSintTask',
                                  ['TSC', 
                                   'EXEC TSC TOPSCREEN POSITION=0.0  MOTOR=ON  COORD=ABS  P_SELECT=FRONT', None] ,
                                   {})
        self.assertNotEquals(tasktag, ro.ERROR)
        # Wait for 50 sec. or end of transaction, which ever comes first.
        (okflag, res) = self.monitor.get_wait(tasktag, 'done', timeout=50)
        self.assertEquals(True, okflag)
        self.assertEquals(True, res)


if __name__ == '__main__':

    LOGDEBUG = True
    unittest.main()


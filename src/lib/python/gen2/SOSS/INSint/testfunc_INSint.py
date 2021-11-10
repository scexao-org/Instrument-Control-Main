#!/usr/bin/env python
#
# Test cases for the instrument interface
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Jul  8 11:14:43 HST 2010
#]
#
import unittest
import sys, os, time
import threading, Queue

import environment

import SOSS.INSint as INSint
import SOSS.DAQtk as DAQtk
import SOSS.SIMCAM as SIMCAM

import remoteObjects as ro
import remoteObjects.Monitor as Monitor
import SOSS.SOSSrpc as SOSSrpc
import logging, ssdlog

# TEMP: till we get configuration management worked out
# Path to where SIMCAM module is loaded
sys.path.insert(0, "../SIMCAM/cams/SIMCAM")

# Create top level logger.
logger = logging.getLogger('testfunc_INSint')
logger.setLevel(logging.ERROR)

fmt = logging.Formatter(ssdlog.STD_FORMAT)

stderrHdlr = logging.StreamHandler()
stderrHdlr.setFormatter(fmt)
logger.addHandler(stderrHdlr)


fits_file_para = """
MOTOR           TYPE=CHAR       SET=ON          DEFAULT=ON
FRAME_NO        TYPE=CHAR       DEFAULT=NOP     NOP=NOP
DELAY           TYPE=NUMBER     DEFAULT=NOP     NOP=NOP
"""


class TestINSint(unittest.TestCase):
    """Start up a SIMCAM instrument and send a command to transfer a file
    to it.

    TODO: change this so that the SIMCAM command requests status to fill
    in the FITS headers and check the headers after the fits file comes
    back.
    """

    def setUp(self):
        self.env = environment.MockEnvironment()
        self.env.removeTestDirs()  # just in case
        self.env.makeDirs()

        self.obcpnum = 9
        self.ev_quit = threading.Event()

        # Create mini monitor for INSint
        self.minimon = Monitor.Minimon('monitor', logger)

        myhost = SOSSrpc.get_myhost(short=True)

        raidpath = self.env.INST_PATH
        statusObj = INSint.FetchStatusWrapper_SOSS({})
        
        # Create and start the instrument interface
        self.insint = INSint.ocsInsInt(self.obcpnum, myhost, raidpath,
                                       statusObj, db=self.minimon,
                                       logger=logger, ev_quit=self.ev_quit)
        self.insint.start(wait=True)

        # Create and start SIMCAM
        ocsint = DAQtk.ocsInt(self.obcpnum, logger=logger, ev_quit=self.ev_quit)
        self.simcam = SIMCAM.Instrument(logger, ev_quit=self.ev_quit,
                                        ocsint=ocsint, allowNoPara=False,
                                        env=self.env)
        self.simcam.loadPersonality('SIMCAM')
        self.simcam.loadParaBuf(('SIMCAM', 'FITS_FILE'), fits_file_para)
        # Wait until SIMCAM is up and running
        self.simcam.start(wait=True)


    def tearDown(self):

        self.insint.stop()
        self.simcam.stop()

        self.env.removeTestDirs()


    def test_INSint01(self):
        tag = 'mon.INSint%d.1' % self.obcpnum
        frameid = 'SIMA00000001'
        cmd_str = 'EXEC SIMCAM FITS_FILE MOTOR=ON FRAME_NO=%s DELAY=0.0' % (
                  frameid)

        # Parse para file to be able to validate interface for fits_file()
        #self.simcam.addPara("fits_file", fits_file_para)

        # Send command to instrument interface and check result code
        res = self.insint.send_cmd(tag, cmd_str)
        self.assertEquals(res, None)
        
        # Wait for 10 sec. or end of transaction, which ever comes first.
        (okflag, res) = self.minimon.get_wait(tag, 'done', timeout=10.0)
        self.assertEquals(True, okflag)
        self.assertEquals(True, res)

        # Was transaction successful?
        (okflag, res) = self.minimon.get_nowait(tag, 'end_result')
        self.assertEquals(True, okflag)
        self.assertEquals(0, res)

        # Check whether destination file exists
        dstfile = self.env.INST_PATH + '/' + frameid + '.fits'
        self.assertEquals(True, os.path.exists(dstfile))

        
if __name__ == '__main__':

    unittest.main()

#END

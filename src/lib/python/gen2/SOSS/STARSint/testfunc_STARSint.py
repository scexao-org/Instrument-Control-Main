#!/usr/bin/env python
#
# Test cases for the STARS interface.
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Jul  8 11:14:42 HST 2010
#]
#
import unittest
import os, time
import threading, Queue

import environment

import SOSS.STARSint as STARSint

import remoteObjects as ro
import remoteObjects.Monitor as Monitor
import SOSS.SOSSrpc as SOSSrpc
import logging, ssdlog
import astro.fitsutils as fitsutils

# Create fake logger
logger = logging.Logger('test_STARSint')
logger.setLevel(logging.ERROR)

fmt = logging.Formatter(ssdlog.STD_FORMAT)

stderrHdlr = logging.StreamHandler()
stderrHdlr.setFormatter(fmt)
logger.addHandler(stderrHdlr)


class TestSTARSint(unittest.TestCase):
    """Start up a STARS simulator and send a command to transfer a file
    to it.
    """

    def setUp(self):
        self.env = environment.MockEnvironment()
        self.env.removeTestDirs()  # just in case
        self.env.makeDirs()

        self.ev_quit = threading.Event()

        # Create mini monitor for STARSint
        self.minimon = Monitor.Minimon('monitor', logger)

        myhost = SOSSrpc.get_myhost(short=True)

        # Create and start STARS simulator
        self.starssim = STARSint.STARSsimulator(logger=logger,
                                                ev_quit=self.ev_quit)
        # Tell STARS how to contact us to copy files
        STARSint.add_transferParams('*',
                                    transfermethod='ssh',
                                    raidpath=self.env.ARCH_PATH,
                                    #username=os.getlogin(),
                                    username=os.environ['LOGNAME'],
                                    password='xxxxxx')
        
        self.starssim.start()

        # Create and start the STARS interface
        self.starsint = STARSint.STARSinterface(starshost=myhost,
                                                db=self.minimon, logger=logger,
                                                ev_quit=self.ev_quit)
        self.starsint.start()

        # Wait until STARS simulator is up and running
        # TODO: figure out a way to synchronize on the portmapper
        time.sleep(0.0)


    def tearDown(self):

        self.starsint.stop()
        self.starssim.stop()

        self.env.removeTestDirs()


    def test_STARSint01(self):
        tag_template = 'mon.frames.STARSint.%s'
        frameid = 'SIMA00000001'
        tag = (tag_template % frameid)
        fitsfile = frameid + '.fits'

        instfile = self.env.INST_PATH + '/' + fitsfile
        hdrkwds = {
            'prop-id': self.env.proposal,
            'frameid': frameid,
            }
        fitsutils.make_fakefits(instfile, hdrkwds, 5, 10)
        
        fitspath = os.path.abspath(instfile)

        # Send command to STARS interface
        self.starsint.submit_fits(tag, fitspath,
                                  indexdir=self.env.INST_PATH)
        
        # Wait for 20 sec. or end of transaction, which ever comes first.
        (okflag, res) = self.minimon.get_wait(tag, 'done', timeout=20)
        self.assertEquals(True, okflag)
        self.assertEquals(True, res)

        # Was transaction successful?
        (okflag, res) = self.minimon.get_nowait(tag, 'end_result')
        self.assertEquals(True, okflag)
        self.assertEquals(0, res)

        # Check whether index file exists
        idxfile = self.env.INST_PATH + '/' + frameid + '.index'
        self.assertEquals(True, os.path.exists(idxfile))

        # Check whether destination file exists
        dstfile = self.env.ARCH_PATH + '/' + fitsfile
        self.assertEquals(True, os.path.exists(dstfile))

        
if __name__ == '__main__':

    unittest.main()

#END

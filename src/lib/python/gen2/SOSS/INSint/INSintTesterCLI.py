# -*- coding: utf-8 -*-
# INSintTesterCLI

import threading
import time

import SOSS.INSint as INSint
import remoteObjects.Monitor as Monitor
import logging
from cfg.INS import INSdata as INSconfig

class INSintTester(object):
  def __init__(self):
    self.insconfig = INSconfig()
    self.obcpnum = 18
    self.obcphost = 'fmos02'
    self.ev_quit = threading.Event()
    self.ev_mainquit = threading.Event()
    self.soss = None
    self.logger = logging.getLogger('INSintTesterCLI')
    statusDict = {}
    self.statusObj = INSint.FetchStatusWrapper_SOSS(statusDict)
    self.cmdtag = 0

  def setup(self):
    self.minimon = Monitor.Minimon('mymon', self.logger, ev_quit=self.ev_quit)
    self.minimon.start(wait=True)
    tp = self.minimon.get_threadPool()
    self.soss = INSint.ocsInsInt(self.obcpnum, self.obcphost, '/tmp',
                                         self.statusObj, ev_quit=self.ev_quit,
                                         interfaces=('cmd',), db=self.minimon,
                                         logger=self.logger,
                                         threadPool=tp)
    self.soss.start(wait=True)

  def send_cmd(self, cmdstr, wait=False, timeout=None):
    if not self.soss:
      raise INSint.INSintError("Servers not started!")
    # Bump the command tag
    self.cmdtag += 1
    tag = 'mon.INSint%d.%d' % (self.obcpnum, self.cmdtag)
    print("send: '%s'" % cmdstr)
    try:
      self.soss.send_cmd(tag, cmdstr)
      if wait:
	self.minimon.get_wait(tag, 'done', timeout=timeout)
    except Exception, e:
      print("ERROR: %s" % str(e))

  def stop(self):
    print "stop mon..."
    self.ev_quit.set()
    self.minimon.stop(wait=True)
    print "stop soss..."
    self.soss.stop(wait=False)
    self.ev_quit.set()
    print "stopped"

if __name__ == '__main__':
  tester = INSintTester()
  tester.setup()
  for iter in range(10):
    tester.send_cmd("EXEC FMOS ECH_PRISMS PARK=1", True)
    tester.send_cmd("EXEC FMOS ECH_PRISMS PARK=0", True)
    tester.send_cmd("EXEC FMOS ECH_AG_CMD ACTION=START PERIOD=NOP NOTIFY=NOP MODE=NOP", True)
  tester.stop()

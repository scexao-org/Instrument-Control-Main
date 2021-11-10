#!/usr/bin/env python

import unittest

import DAQtk
import SOSS.SOSSrpc

## this should be in test_SOSS_rpc.py
class TestGetProgNums(unittest.TestCase):
  def setUp(self):
    self.allobcpnums = range(1,33)
  def testAllValsAreRight(self):
    self.assertEquals(1, self.allobcpnums[0])
    self.assertEquals(32, self.allobcpnums[-1])
  def testGetAllProgNums(self):
    for obcpnum in self.allobcpnums:
      #print obcpnum
      svc = SOSS.SOSSrpc.lookup_rpcsvc('OBCP%dtoOBC(file)' % obcpnum)
      self.assertEquals("0x2101%02x41" % obcpnum, hex(svc.client_send_prgnum))
      self.assertEquals("0x2102%02x41" % obcpnum, hex(svc.client_receive_prgnum))


class Test3WayTrans:#(unittest.TestCase): obsolete
  def setUp(self):
    self.inst = DAQtk.Instrument(self)

  def RequestTransfer(self,frameid):
    self.transrequested = True
    self.transrequestframeid = frameid
  def WaitForReqTransAck(self):
    self.assertEquals(True, self.transrequested)
    self.waitedforack = True
    return()
  def WaitForReqTransEnd(self):
    self.assertEquals(True, self.transrequested)
    self.assertEquals(True, self.waitedforack)
    self.waitedforend = True
    return()

  def testSnapMakesTrans(self):
    self.transrequested = False
    self.waitedforack = False
    self.waitedforend = False
    self.frameid = "SUKA90000001"
    self.inst.Snap(self.frameid)
    self.assertEquals(True, self.transrequested)
    self.assertEquals(self.frameid, self.transrequestframeid)
    self.assertEquals(True, self.waitedforack)
    self.assertEquals(True, self.waitedforend)

    #make sure seq nums match

if __name__ == "__main__":
  unittest.main()

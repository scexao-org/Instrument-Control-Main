#!/usr/bin/env python
#
# Mark Garboden
#
import unittest
import time
import os

import environment
import remoteObjects as ro
import remoteObjectNameSvc


class TestEnvConfiguredRight(unittest.TestCase):
  def test_etc_hosts_isRight(self):
    # there is a bug in XMLRPCServer that won't work right if the IP address
    # looked up is 127.0.0.1.  If the /etc/hosts file is written incorrectly
    # then everything else except remote objects will work.
    import socket
    info = socket.getaddrinfo(socket.getfqdn(),ro.nameServicePort)
    # returns something like
    #[(2, 1, 6, '', ('133.40.166.15', 7075)), (2, 2, 17, '', ('133.40.166.15', 7075))
    self.assertNotEquals('127.0.0.1', info[0][4][0])
    self.assertEquals(ro.nameServicePort, info[0][4][1])


class TestRONameServerOnly(unittest.TestCase):
  def setUp(self):
    self.myhost = ro.get_myhost()
    self.ns = remoteObjectNameSvc.remoteObjectNameService([],
                                 name='remoteObjectNameServer',host=self.myhost,
                                 port=ro.nameServicePort)
    self.ns.ro_start()
  def tearDown(self):
    self.ns.ro_stop()
  def testUpDown1(self):
    pass
  def testUpDown2(self):
    pass


class FakeServer(object):
    def __init__(self,initval):
      self.initval = initval
    def test(self, value):
        #print self.initval,"value: %s" % str(value)
        return value
    def ro_echo(self,arg):
        #print self.initval,"echo: %s" % str(arg)
        return self.initval+str(arg)
    def copyfile(self,filename,filedata):
        outfile = open(filename,"w")
        outfile.write(filedata)
        outfile.close()
        return(True)
    def sendfile(self,filename,filedata):
        #outfile = open(filename,"w")
        #outfile.write(filedata)
        #outfile.close()
        return(True)
        


class FakeROServer(FakeServer,ro.remoteObjectServer):
    INITVAL = "initVal"
    def __init__(self, svcname, usethread=False):
        # Superclass constructor
        FakeServer.__init__(self,'initVal')
        ro.remoteObjectServer.__init__(self, svcname=svcname, usethread=usethread)


# also assert raises no ronamesvr if run init w/o ronamesvc


def waitForService(nameservice,servicename):
    tries = 100
    while (tries and [] == nameservice.getHosts(servicename)):
      #print "Waiting for",servicename, tries,"tries left"
      tries -= 1
      time.sleep(0.001)
    #


class TestROwithServer(unittest.TestCase):
  def setUp(self):
    self.env = environment.MockEnvironment()
    self.env.removeTestDirs()  # just in case
    self.env.makeDirs()

    self.myhost = ro.get_myhost()
    self.rohosts = []
    self.ns = remoteObjectNameSvc.remoteObjectNameService(self.rohosts,
                                 name='remoteObjectNameServer',host=self.myhost,
                                 port=ro.nameServicePort)
    self.ns.ro_start()
    waitForService(self.ns,'names')
    #print "Status",self.ns.init0_up1_down2
    
    #print "Hosts for",'names',self.ns.getHosts('names')
    ro.init()
    #time.sleep(1)

    self.servicename = 'TestServiceName'
    self.ROserver = FakeROServer(self.servicename,usethread=True)
    self.ROserver.ro_start()
    waitForService(self.ns,self.servicename)
    #print "Hosts for",self.servicename,self.ns.getHosts(self.servicename)
    self.ROclient = ro.remoteObjectProxy(self.servicename)
    self.val1 = '1'
    self.val2 = self.val1 + "22"

    self.rofilename = self.env.INST_PATH+"/ROfilename"

  def tearDown(self):
    self.env.removeTestDirs()
    self.ROserver.ro_stop()
    #print "Status",self.ns.init0_up1_down2
    #print "Names left",self.ns.getNames()
    tries = 100
    while (tries and self.ROserver.init0_up1_down2 != 2):
      #print "Names left",self.ns.getNames(),self.ROserver.init0_up1_down2,tries
      tries -= 1
      time.sleep(0.1)
    #
    #print "Names left",self.ns.getNames(),self.ROserver.init0_up1_down2,tries

    self.ns.ro_stop()

    tries = 100
    while (tries and self.ns.init0_up1_down2 != 2):####self.servicename in self.ns.getNames()):
      #print "Names left",self.ns.getNames(),self.ns.init0_up1_down2,tries
      tries -= 1
      time.sleep(0.1)
    #
    #print "Names left",self.ns.getNames(),self.ns.init0_up1_down2,tries

  def testUpDown1(self):
    pass


  def testUsage(self):
    val = self.env.uniqueString()
    self.assertEquals(val,self.ROclient.test(val))
    # server,ROClient, and ROserver should get overridden ro_echo()
    val = self.env.uniqueString()
    self.assertEquals("initVal"+val,self.ROserver.ro_echo(val))
    val = self.env.uniqueString()
    self.assertEquals("initVal"+val,self.ROclient.ro_echo(val))


  def testFileCopy(self):
    self.filecontents = "ROfile contents\n"*10000
    self.assertEquals(False, os.path.exists(self.rofilename))
    start = time.time()
    self.ROclient.copyfile(self.rofilename,self.filecontents)
    elapsed = time.time() - start
    #print "\n\n%f %fKBps\n\n" % (elapsed, len(self.filecontents)/elapsed/1000.0)
    self.assertEquals(True, os.path.exists(self.rofilename))

  def testFileSend(self):
    self.filecontents = "ROfile contents\n"*10000
    self.assertEquals(False, os.path.exists(self.rofilename))
    start = time.time()
    self.ROclient.sendfile(self.rofilename,self.filecontents)
    elapsed = time.time() - start
    #print "\n\n%f %fKBps\n\n" % (elapsed, len(self.filecontents)/elapsed/1000.0)
    self.assertEquals(False, os.path.exists(self.rofilename))



class TestObjAsAttr(unittest.TestCase):
  def setUp(self):
    self.env = environment.MockEnvironment()
    self.myhost = ro.get_myhost()
    self.rohosts = []
    self.ns = remoteObjectNameSvc.remoteObjectNameService(self.rohosts,
                                 name='remoteObjectNameServer',host=self.myhost,
                                 port=ro.nameServicePort)
    self.ns.ro_start()
    waitForService(self.ns,'names')
    
    #print "Hosts for",'names',self.ns.getHosts('names')
    ro.init()

    self.initval = 'init'
    self.server = FakeServer(self.initval)

    self.servicename = 'TestServiceName2'
    self.ROserver = ro.remoteObjectServer(obj=self.server,name=self.servicename,
                                          svcname=self.servicename,usethread=True)
    self.ROserver.ro_start()
    waitForService(self.ns,self.servicename)
    #print "Hosts for",self.servicename,self.ns.getHosts(self.servicename)
    self.ROclient = ro.remoteObjectProxy(self.servicename)

  def tearDown(self):
    self.ROserver.ro_stop()
    #print "Status",self.ns.init0_up1_down2
    #print "Names left",self.ns.getNames()
    tries = 100
    while (tries and self.ROserver.init0_up1_down2 != 2):
      #print "Names left",self.ns.getNames(),self.ROserver.init0_up1_down2,tries
      tries -= 1
      time.sleep(0.1)
    #
    #print "Names left",self.ns.getNames(),self.ROserver.init0_up1_down2,tries
    self.ns.ro_stop()
    tries = 100
    while (tries and self.ns.init0_up1_down2 != 2):####self.servicename in self.ns.getNames()):
      #print "Names left",self.ns.getNames(),self.ns.init0_up1_down2,tries
      tries -= 1
      time.sleep(0.1)
    #
    #print "Names left",self.ns.getNames(),self.ns.init0_up1_down2,tries

  def test1(self):
    val = self.env.uniqueString()
    self.assertEquals(val,self.server.test(val))
    val = self.env.uniqueString()
    self.assertEquals(val,self.ROclient.test(val))
    val = self.env.uniqueString()
    # RO server should get default ro_echo()
    self.assertEquals(val,self.ROserver.ro_echo(val))
    # server and ROClient should get overridden ro_echo()
    val = self.env.uniqueString()
    self.assertEquals(self.initval+val,self.server.ro_echo(val))
    val = self.env.uniqueString()
    self.assertEquals(self.initval+val,self.ROclient.ro_echo(val))



if __name__ == '__main__':
  unittest.main()

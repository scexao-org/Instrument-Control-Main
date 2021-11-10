#
# BaseInterface.py -- Base class for SOSS style client/server instances
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Jan 14 17:53:29 HST 2013
#]
#

import Task
import SOSS.SOSSrpc as SOSSrpc

#
class BaseInterface(object):
    """Interface base class.  Combines common functionality shared by all
    of the unique instrument interfaces, to reduce redundant code.
    """

    def __init__(self, ev_quit, logger, db, taskqueue,
                 myhost=None, myport=None, seq_num=None):
        """Class constructor.
        
        Required parameters:
          ev_quit: a threading.Event object to synchronize any thread
          termination.  If None, then any RPC servers created by the
          subclass will create their own termination event object.

          logger: a Python logger object.  Must NOT be None.  Logs
          various events happening in the interface.

          db: a Monitor.Monitor object.  Used to inform the monitor of
          our activities, as well as a local hierarchical store of
          shared auxillary data.

          taskqueue: a Queue.Queue compatible object.  Passed through
          to the RPC servers.  When a packet arrives for a particular
          interface, the RPC server drops a processing task containing
          the packet into the queue.  The tasks are processed by a
          threadPool shared by all interfaces.

        Optional parameters:
          myhost: specifies the host interface to bind the RPC servers.
          Best left to None, in which case all host interfaces are
          bound--that way you don't have to care how the host network
          interfaces are configured.

          myport: specifies the host interface to bind the RPC servers.
          Best left to None, in which case a random, open port is
          chosen.

          seq_num: specifies a SOSSrpc.rpcSequenceNumber object to be
          used by this interface.  If left to None, a unique one is
          created for each interface.
        """

        super(BaseInterface, self).__init__()
        
        self.ev_quit = ev_quit
        self.logger = logger
        self.db = db
        self.taskqueue = taskqueue
        # Set interface for RPC server
        if myhost:
            self.myhost = myhost
        else:
            self.myhost = SOSSrpc.get_myhost(short=True)
            # None binds to all available interfaces
            #self.myhost = None
        # If None, will choose random, open port
        self.myport = myport
        # This will hold the client-server RPC object assigned by the
        # base class
        self.rpcconn = None

        # TODO: should seq_num be shared by all interfaces?
        # Check SOSS logs, but engineering night testing says it doesn't
        # matter...
        if seq_num:
            self.seq_num = seq_num
        else:
            # Create unique sequence number for this interface
            self.seq_num = SOSSrpc.rpcSequenceNumber()


    def start(self, usethread=True, wait=True, timeout=None):
        #self.rpcconn.start(usethread=usethread, wait=wait, timeout=timeout)
        # Add a task to run the function start() on our 
        t = Task.FuncTask(self.rpcconn.start, [],
                          {'usethread': False})
        self.taskqueue.put(t)
        if wait:
            self.rpcconn.wait_start(timeout=timeout)
        
    def stop(self, wait=True):
        self.rpcconn.stop(wait=wait)

#END

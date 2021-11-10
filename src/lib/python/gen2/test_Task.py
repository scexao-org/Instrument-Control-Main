#!/usr/bin/env python
#
# Unit Tests for the Task class
#
# Eric Jeschke  (eric@naoj.org) 2006.07.17
# Bruce Bon     (bon@naoj.org)  2007-08-31
#
# On vega, this test program takes about 8 seconds to run.
#

import unittest
import time, random

import Task
import logging, ssdlog

LOGDEBUG = False

# ========================================================================

class simpleTask(Task.Task):
    """Simple task used in various tests below.  Sleeps a random interval
    between 0 and 0.5 seconds, and then returns val.
    """
    def __init__(self, val):
        self.val = val
        super(simpleTask, self).__init__()

    def execute(self):
        time.sleep(0.5*random.random())
        self.result = self.val
        return self.val

    
def make_SimpleTask(val):
    """Create a simpleTask object and return it."""
    t = simpleTask(val)
    return t

def make_CompoundTask(typeClass, prefix, num):
    """
    Arguments:
        typeClass   Task.SequentialTaskset or Task.ConcurrentAndTaskset
        prefix      'ct', 't2', 't3', etc.
        num         number of tasks in this compound task
    Create num simpleTask objects in a list; create a compound task
    object of type typeClass with taskseq = the list of tasks, and
    return it.
    """
    tasks = []
    for i in xrange(num):
        st = make_SimpleTask(prefix + '_' + str(i))
        tasks.append(st)

    t = typeClass(taskseq=tasks)
    return t


class dynamicBuilderTask(Task.Task):
    """Dynamically builds and executes a sequential compound task.
    """
    def __init__(self, num):
        self.num = num
        super(dynamicBuilderTask, self).__init__()

    def execute(self):
        t = make_CompoundTask(Task.SequentialTaskset, 'ct', self.num)
        t.initialize(self)
        t.start()

        res = t.wait()
        self.results = []
        for i in xrange(self.num):
            self.results.append( t.taskseq[i].result )
        return res

    
class stepTask(Task.Task):
    """Simple sequential task used in various tests below.  Returns the result
    of the last step.
    Implemented using Python generators.  Less complex way to generate a
    sequential task.
    """

    def __init__(self):
        self.count = 0
        # Create generator for the task's sequential logic
        self.gen = self.tasklogic()
        
        super(stepTask, self).__init__()

    def tasklogic(self):
        """This implements the task's logic as a simple sequential function.
        """
        
        # e.g. This is the first step
        self.count += 1
        yield self.count
            
        # e.g. Second step
        self.count += 1
        yield self.count
            
        # e.g. Series of steps as an iteration
        while self.count < 7:
            yield self.count
            self.count += 1

        # e.g. Final step
        self.count += 1
        yield self.count
            
    def step(self):
        # Call generator for next step
        return self.gen.next()

    def execute(self):
        res = 0
        try:
            # Be careful that generator terminates or this will iterate forever
            while True:
                if  LOGDEBUG:
                    print "* stepTask.execute: About to call step()"
                res = self.step()
                if  LOGDEBUG:
                    print "* stepTask.execute: Result is %d" % res

        except StopIteration:
            # Raised when tasklogic() "runs off the end" (terminates)
            pass

        # Return final result
        return res

    

class TestTask01(unittest.TestCase):

    def setUp(self):
        """
        - Initialize logger
        - Create 20-thread thread pool
        - Make a fake parentTask using the thread pool
        """
        if  LOGDEBUG:
            print "\n*** TestTask01: setting up thread pool"
        self.logger = logging.getLogger( 'TestTask01Logger' )
        self.logger.setLevel(logging.WARN)
    
        self.tpool = Task.ThreadPool(numthreads=20, logger=self.logger)
        self.tpool.startall(wait=True)

        # Make a fake 'parent' task
        self.parentTask = make_SimpleTask('t1')
        self.parentTask.tag = 'tasks'

        sl = logging.getLogger( 'TestTask01ParentLogger' )
        sl.setLevel(logging.WARN)
        self.parentTask.logger = sl

        self.parentTask.threadPool = self.tpool

    def tearDown(self):
        """Stop all threads in pool"""
        if  LOGDEBUG:
            print "\n*** TestTask01: tearing down thread pool"
        self.tpool.stopall(wait=True)

    def test_01(self):
        if  LOGDEBUG:
            print "\n*** TestTask01.test_01: test of simple task creation and execution"
        t = simpleTask('t1')
        t.initialize(self.parentTask)

        t.start()
        res = t.wait()

        self.assertEqual('t1', res)

    def test_02(self):
        if  LOGDEBUG:
            print "\n*** TestTask01.test_02: test of a sequential (compound) task"
        t = make_CompoundTask(Task.SequentialTaskset, 't2', 3)
        t.initialize(self.parentTask)

        t.start()

        res = t.wait()
        resTuple = ( t.taskseq[0].result, t.taskseq[1].result, t.taskseq[2].result )
        if  LOGDEBUG:
            self.logger.info( 'resTuple = %s' % `resTuple` )
            print "Total time is %f" % t.getExecutionTime()
        self.assertEqual('t2_2', res)
        # test against the values assigned in make_CompoundTask()
        self.assertEqual('t2_0', resTuple[0])
        self.assertEqual('t2_1', resTuple[1])
        self.assertEqual('t2_2', resTuple[2])
        
    def test_03(self):
        if  LOGDEBUG:
            print "\n*** TestTask01.test_03: test of a concurrent (compound) task"
        t = make_CompoundTask(Task.ConcurrentAndTaskset, 't3', 3)
        t.initialize(self.parentTask)

        t.start()

        res = t.wait()
        resTuple = ( t.taskseq[0].result, t.taskseq[1].result, t.taskseq[2].result )
        if  LOGDEBUG:
            self.logger.info( 'resTuple = %s' % `resTuple` )
            print "Total time is %f" % t.getExecutionTime()
        # test against the values assigned in make_CompoundTask()
        self.assert_('t3_1' in resTuple)
        self.assert_('t3_0' in resTuple)
        self.assert_('t3_2' in resTuple)
        
    def test_04(self):
        if  LOGDEBUG:
            print "\n*** TestTask01.test_04: test of 2 seqential task sets in a concurrent task"
        t1 = make_CompoundTask(Task.SequentialTaskset, 't4a', 3)
        t2 = make_CompoundTask(Task.SequentialTaskset, 't4b', 3)
        t = Task.ConcurrentAndTaskset([t1, t2])
        t.initialize(self.parentTask)

        t.start()

        res = t.wait()
        resTuple = ( t1.result, t2.result )
        if  LOGDEBUG:
            self.logger.info( 'resTuple = %s' % `resTuple` )
            print "Total time is %f" % t.getExecutionTime()
        # test against the values assigned to final task in each make_CompoundTask()
        self.assert_('t4b_2' in resTuple)
        self.assert_('t4a_2' in resTuple)
        
    def test_05(self):
        if  LOGDEBUG:
            print "\n*** TestTask01.test_05: test of 2 seqential task sets in a sequential task"
        t1 = make_CompoundTask(Task.SequentialTaskset, 't5a', 3)
        t2 = make_CompoundTask(Task.SequentialTaskset, 't5b', 3)
        t = Task.SequentialTaskset([t1, t2])
        t.initialize(self.parentTask)

        t.start()

        res = t.wait()
        resTuple = ( t1.result, t2.result )
        if  LOGDEBUG:
            self.logger.info( 'resTuple = %s' % `resTuple` )
            print "Total time is %f" % t.getExecutionTime()
        self.assertEqual('t5b_2', res)
        # test against the values assigned in make_CompoundTask()
        self.assertEqual('t5a_2', resTuple[0])
        self.assertEqual('t5b_2', resTuple[1])
        
    def test_06(self):
        if  LOGDEBUG:
            print "\n*** TestTask01.test_06: test of 2 concurrent tasks in a concurrent task"
        t1 = make_CompoundTask(Task.ConcurrentAndTaskset, 't6a', 3)
        t2 = make_CompoundTask(Task.ConcurrentAndTaskset, 't6b', 3)
        t = Task.ConcurrentAndTaskset([t1, t2])
        t.initialize(self.parentTask)

        t.start()

        res = t.wait()
        resTuple = ( t1.taskseq[0].result, t1.taskseq[1].result, t1.taskseq[2].result,
                     t2.taskseq[0].result, t2.taskseq[1].result, t2.taskseq[2].result )
        if  LOGDEBUG:
            self.logger.info( 'resTuple = %s' % `resTuple` )
            print "Total time is %f" % t.getExecutionTime()
        self.assertEqual( 0, t.taskseq[0].result )
        self.assertEqual( 0, t.taskseq[1].result )
        # test against the values assigned in make_CompoundTask()
        self.assertEqual( 't6a_0', resTuple[0] )
        self.assertEqual( 't6a_1', resTuple[1] )
        self.assertEqual( 't6a_2', resTuple[2] )
        self.assertEqual( 't6b_0', resTuple[3] )
        self.assertEqual( 't6b_1', resTuple[4] )
        self.assertEqual( 't6b_2', resTuple[5] )

    def test_07(self):
        if  LOGDEBUG:
            print "\n*** TestTask01.test_07: test of simple step task"
        t = stepTask()
        t.initialize(self.parentTask)
        t.start()

        res = t.wait()
        if  LOGDEBUG:
            print "Total time is %f" % t.getExecutionTime()
        self.assertEqual( 8, res )

    def test_08(self):
        if  LOGDEBUG:
            print "\n*** TestTask01.test_08: test of dynamically built task"
        t = dynamicBuilderTask(5)
        t.initialize(self.parentTask)

        t.start()

        res = t.wait()
        results = t.results
        if  LOGDEBUG:
            self.logger.info( 'results = %s' % `results` )
            print "Total time is %f" % t.getExecutionTime()
        self.assertEqual( 'ct_0', results[0] )
        self.assertEqual( 'ct_1', results[1] )
        self.assertEqual( 'ct_2', results[2] )
        self.assertEqual( 'ct_3', results[3] )
        self.assertEqual( 'ct_4', results[4] )


if __name__ == "__main__":

    print '\n>>>>> Starting test_Task <<<<<\n'
    unittest.main()

#END

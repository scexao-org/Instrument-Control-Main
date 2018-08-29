#
# GtkMain.py -- pygtk threading help routines.
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Apr 30 16:37:58 HST 2012
#]
#
"""
GUI threading help routines.

Usage:

   import GtkMain

   # See constructor for GtkMain for options
   self.mygtk = GtkMain.GtkMain()

   # NOT THIS
   #gtk.main()
   # INSTEAD, main thread calls this:
   self.mygtk.mainloop()
   
   # (asynchronous call)
   self.mygtk.gui_do(method, arg1, arg2, ... argN, kwd1=val1, ..., kwdN=valN)

   # OR 
   # (synchronous call)
   res = self.mygtk.gui_call(method, arg1, arg2, ... argN, kwd1=val1, ..., kwdN=valN)

   # To cause the GUI thread to terminate the mainloop
   self.mygtk.qui_quit()
   
   """
import sys, traceback
import thread, threading
import logging
import Queue

import gtk

class GtkMain(object):

    def __init__(self, queue=None, logger=None, ev_quit=None):
        # You can pass in a queue if you prefer to do so
        if not queue:
            queue = Queue.Queue()
        self.gui_queue = queue
        # You can pass in a logger if you prefer to do so
        if not logger:
            logger = logging.getLogger('GtkHelper')
        self.logger = logger
        if not ev_quit:
            ev_quit = threading.Event()
        self.ev_quit = ev_quit
        
        self.gui_thread_id = None
        
    def update_pending(self, timeout=0.0):
        """Process all pending GTK events and return.  _timeout_ is a tuning
        parameter for performance.
        """
        # Process "out-of-band" GTK events
        try:
            while gtk.events_pending():
                gtk.main_iteration(False)
        finally:
            pass

        done = False
        while not done:
            # Process "in-band" GTK events
            try:
                future = self.gui_queue.get(block=True, 
                                            timeout=timeout)

                # Execute the GUI method
                try:
                    try:
                        res = future.thaw(suppress_exception=False)

                    except Exception, e:
                        future.resolve(e)

                        self.logger.error("gui error: %s" % str(e))
                        try:
                            (type, value, tb) = sys.exc_info()
                            tb_str = "".join(traceback.format_tb(tb))
                            self.logger.error("Traceback:\n%s" % (tb_str))

                        except Exception, e:
                            self.logger.error("Traceback information unavailable.")

                finally:
                    pass

                    
            except Queue.Empty:
                done = True
                
            except Exception, e:
                self.logger.error("Main GUI loop error: %s" % str(e))
                
        # Process "out-of-band" GTK events again
        try:
            while gtk.events_pending():
                gtk.main_iteration(False)
        finally:
            pass

    def gui_do(self, method, *args, **kwdargs):
        """General method for asynchronously calling into the GUI.
        It makes a future to call the given (method) with the given (args)
        and (kwdargs) inside the gui thread.  If the calling thread is a
        non-gui thread the future is returned.
        """
        future = Future()
        future.freeze(method, *args, **kwdargs)
        self.gui_queue.put(future)

        my_id = thread.get_ident() 
        if my_id != self.gui_thread_id:
            return future
   
    def gui_call(self, method, *args, **kwdargs):
        """General method for synchronously calling into the GUI.
        This waits until the method has completed before returning.
        """
        my_id = thread.get_ident() 
        if my_id == self.gui_thread_id:
            return method(*args, **kwdargs)
        else:
            future = self.gui_do(method, *args, **kwdargs)
            return future.wait()
   
    def gui_do_future(self, future):
        self.gui_queue.put(future)
        return future

    def assert_gui_thread(self):
        my_id = thread.get_ident() 
        assert my_id == self.gui_thread_id, \
               Exception("Non-GUI thread (%d) is executing GUI code!" % (
            my_id))
        
    def assert_nongui_thread(self):
        my_id = thread.get_ident() 
        assert my_id != self.gui_thread_id, \
               Exception("GUI thread (%d) is executing non-GUI code!" % (
            my_id))
        
    def mainloop(self, timeout=0.001):
        # Mark our thread id
        self.gui_thread_id = thread.get_ident()

        while not self.ev_quit.isSet():
            self.update_pending(timeout=timeout)

    def gui_quit(self, *args):
        "Call this to cause the GUI thread to quit the mainloop."""
        self.ev_quit.set()
        

class Future(object):
    """The Future class allows you to set up deferred computations that
    can be invoked by other threads, or by the same thread in a different
    time.
    """
    def __init__(self):
        self.evt = threading.Event()
        self.res = None

    def has_value(self):
        return self.evt.isSet()
    
    def freeze(self, method, *args, **kwdargs):
        self.method = method
        self.args = args
        self.kwdargs = kwdargs

    def thaw(self, suppress_exception=True):
        if not suppress_exception:
            res = self.method(*self.args, **self.kwdargs)

        else:
            try:
                res = self.method(*self.args, **self.kwdargs)

            except Exception, e:
                res = e

        self.resolve(res)
        return res
        
    def has_value(self):
        return self.evt.isSet()
    
    def resolve(self, value):
        self.res = value
        self.evt.set()

    def wait(self, timeout=None):
        self.evt.wait(timeout=timeout)
        if not self.has_value():
            raise Exception("Timed out waiting for value!")

        return self.res

# END

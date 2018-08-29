#
# QtMain.py -- pyqt threading help routines.
#
# Eric Jeschke (eric@naoj.org)
#
# Copyright (c) Eric R. Jeschke.  All rights reserved.
#
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the
#   distribution.
#
# * Neither the name of the Eric R. Jeschke nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
# IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""
GUI threading help routines.

Usage:

   import QtMain

   # See constructor for QtMain for options
   self.myqt = QtMain.QtMain()

   # main thread calls this:
   self.myqt.mainloop()

   # (asynchronous call)
   self.myqt.gui_do(method, arg1, arg2, ... argN, kwd1=val1, ..., kwdN=valN)

   # OR
   # (synchronous call)
   res = self.myqt.gui_call(method, arg1, arg2, ... argN, kwd1=val1, ..., kwdN=valN)

   # To cause the GUI thread to terminate the mainloop
   self.myqt.gui_quit()

   """
from __future__ import print_function
import sys
import traceback
import threading
import logging
import six
if six.PY2:
    import thread
    import Queue
else:
    import _thread as thread
    import queue as Queue

# PyQt4 only
from PyQt4.QtGui import QApplication
# if using qtpy package that provides lovely Qt4/Qt5/PySide wrapping
#from qtpy.QtWidgets import QApplication


class QtMain(object):

    def __init__(self, queue=None, logger=None, ev_quit=None):
        super(QtMain, self).__init__()

        # You can pass in a queue if you prefer to do so
        if not queue:
            queue = Queue.Queue()
        self.gui_queue = queue
        # You can pass in a logger if you prefer to do so
        if not logger:
            logger = logging.getLogger('QtMain')
        self.logger = logger
        if not ev_quit:
            ev_quit = threading.Event()
        self.ev_quit = ev_quit

        app = QApplication([])
        app.lastWindowClosed.connect(lambda *args: self._quit())
        self.app = app
        self.gui_thread_id = None

        # Get screen size
        desktop = self.app.desktop()
        #rect = desktop.screenGeometry()
        rect = desktop.availableGeometry()
        size = rect.size()
        self.screen_wd = size.width()
        self.screen_ht = size.height()

    def get_widget(self):
        return self.app

    def get_screen_size(self):
        return (self.screen_wd, self.screen_ht)

    def update_pending(self, timeout=0.0):

        #print "1. PROCESSING OUT-BAND"
        try:
            self.app.processEvents()
        except Exception as e:
            self.logger.error(str(e))
            # TODO: traceback!

        done = False
        while not done:
            #print "2. PROCESSING IN-BAND len=%d" % self.gui_queue.qsize()
            # Process "in-band" Qt events
            try:
                future = self.gui_queue.get(block=True,
                                            timeout=timeout)

                # Execute the GUI method
                try:
                    try:
                        res = future.thaw(suppress_exception=False)

                    except Exception as e:
                        future.resolve(e)

                        self.logger.error("gui error: %s" % str(e))
                        try:
                            (type, value, tb) = sys.exc_info()
                            tb_str = "".join(traceback.format_tb(tb))
                            self.logger.error("Traceback:\n%s" % (tb_str))

                        except Exception as e:
                            self.logger.error("Traceback information unavailable.")

                finally:
                    pass


            except Queue.Empty:
                done = True

            except Exception as e:
                self.logger.error("Main GUI loop error: %s" % str(e))
                #pass

        # Process "out-of-band" events
        #print "3. PROCESSING OUT-BAND"
        try:
            self.app.processEvents()
        except Exception as e:
            self.logger.error(str(e))
            # TODO: traceback!


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

    def gui_quit(self):
        "Call this to cause the GUI thread to quit the mainloop."""
        self.ev_quit.set()

        self.app.quit()

    def _quit(self):
        self.gui_quit()

    def mainloop(self, timeout=0.001):
        # Mark our thread id
        self.gui_thread_id = thread.get_ident()

        while not self.ev_quit.isSet():
            self.update_pending(timeout=timeout)


class TimeoutError(Exception):
    pass


class Future(object):

    def __init__(self, data=None, priority=0):
        super(Future, self).__init__()

        self.evt = threading.Event()
        self.res = None
        # User can attach some arbitrary data if desired
        self.data = data
        self.priority = priority

    # for sorting in PriorityQueues
    def __lt__(self, other):
        return self.priority < other.priority

    def get_data(self):
        return self.data

    # TODO: Could add some args type/value, return value validation here
    def freeze(self, method, *args, **kwdargs):
        self.method = method
        self.args = args
        self.kwdargs = kwdargs

    def thaw(self, suppress_exception=True):
        self.evt.clear()
        if not suppress_exception:
            res = self.method(*self.args, **self.kwdargs)

        else:
            try:
                res = self.method(*self.args, **self.kwdargs)

            except Exception as e:
                res = e

        self.resolve(res)
        return res

    def has_value(self):
        return self.evt.isSet()

    def resolve(self, value):
        self.res = value
        self.evt.set()

    def get_value(self, block=True, timeout=None, suppress_exception=False):
        if block:
            self.evt.wait(timeout=timeout)
        if not self.has_value():
            raise TimeoutError("Timed out waiting for value!")

        if isinstance(self.res, Exception) and (not suppress_exception):
            raise self.res

        return self.res

    def wait(self, timeout=None):
        self.evt.wait(timeout=timeout)
        if not self.has_value():
            raise TimeoutError("Timed out waiting for value!")

        return self.res


# END

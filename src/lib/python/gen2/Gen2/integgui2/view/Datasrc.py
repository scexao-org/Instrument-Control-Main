#
# Eric Jeschke (eric@naoj.org)
#
import threading

class TimeoutError(Exception):
    pass

class Datasrc(object):

    def __init__(self, length=20):
        self.length = length
        self.cursor = -1
        self.datums = {}
        self.history = []
        self.sortedkeys = []
        self.cond = threading.Condition()
        self.newdata = threading.Event()


    def __getitem__(self, key):
        with self.cond:
            if isinstance(key, int):
                return self.datums[self.sortedkeys[key]]
            else:
                return self.datums[key]

        
    def __setitem__(self, key, value):
        with self.cond:
            if key in self.history:
                self.history.remove(key)

            self.history.append(key)

            self.datums[key] = value

            if len(self.history) > self.length:
                oldest = self.history.pop(0)
                del self.datums[oldest]

            self.sortedkeys = self.datums.keys()
            self.sortedkeys.sort()
            
            self.newdata.set()
            self.cond.notify()
        

    def __len__(self):
        with self.cond:
            return len(self.sortedkeys)


    def index(self, key):
        with self.cond:
            return self.sortedkeys.index(key)


    def keys(self):
        with self.cond:
            return self.sortedkeys


    def wait(self, timeout=None):
        with self.cond:
            self.cond.wait(timeout=timeout)

            if not self.newdata.isSet():
                raise TimeoutError("Timed out waiting for datum")

            self.newdata.clear()
            return self.history[-1]


    def get_bufsize(self):
        with self.cond:
            return self.length
       
        
    def set_bufsize(self, length):
        with self.cond:
            if length < self.length:
                raise IndexError("Currently don't support downsizing!")
            
            self.length = length

        
    def put(self, obj):
        with self.cond:
            # Make room, if necessary for next item
            if len(self.queue) >= self.length:
                self.queue.pop(0)

            # Append the new item
            self.queue.append(obj)

            # Adjust cursor if necessary, to current item
            if self.cursor > 0:
                self.cursor -= 1

            # Release one waiter, if any
            self.cond.notify()
            return obj

        
    def next(self, block=True, timeout=None):
        with self.cond:
            if self.cursor >= (len(self.queue) - 1):
                if not block:
                    raise IndexError("No next item")

                else:
                    self.cond.wait(timeout=timeout)
                    if self.cursor >= (len(self.queue) - 1):
                        raise IndexError("No next item")

            self.cursor += 1
            print "cursor: %d" % self.cursor
            return self.queue[self.cursor]

            
    def current(self):
        with self.cond:
            return self.queue[self.cursor]


    def previous(self):
        with self.cond:
            if (self.cursor <= 0) or (len(self.queue) == 0):
                raise IndexError("No previous item")

            self.cursor -= 1
            print "cursor: %d" % self.cursor
            return self.queue[self.cursor]


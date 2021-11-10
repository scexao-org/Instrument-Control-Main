#
# command.py -- command object and queue object definitions
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Sat Apr 16 10:16:53 HST 2011
#]

import threading

class QueueEmpty(Exception):
    pass


class CommandQueue(object):
    
    def __init__(self, name, logger):
        self.name = name
        self.logger = logger

        self.queue = []
        self.views = []
        self.flag = threading.Event()
        self.lock = threading.RLock()

        self.enable()

    def add_view(self, view):
        with self.lock:
            self.views.append(view)

    def del_view(self, view):
        with self.lock:
            self.views.remove(view)

    def mark_status(self, cmdObjs, status):
        for cmdObj in cmdObjs:
            cmdObj.mark_status(status)
        
    def update_status(self, cmdObjs):
        with self.lock:
            for cmdObj in cmdObjs:
                if cmdObj in self.queue:
                    cmdObj.mark_status('queued')
                else:
                    cmdObj.mark_status('unqueued')
        
    def redraw(self):
        with self.lock:
            for view in self.views:
                view.redraw()
            self.mark_status(self.queue, 'queued')
                
        
    def enabledP(self):
        return self.flag.isSet()

    def enable(self):
        return self.flag.set()

    def disable(self):
        return self.flag.clear()

    def enableIfPending(self):
        with self.lock:
            if len(self.queue) > 0:
                self.enable()
                return True

            else:
                return False

    def get_tags(self):
        """Returns a list of all tag ids for the command objects in the
        queue."""
        with self.lock:
            return map(str, self.queue)

    def get_by_tags(self, tags):
        """Returns a list of all elements of the queue who have 
        queue."""
        with self.lock:
            return filter(lambda x: str(x) in tags, self.queue)

    def flush(self):
        with self.lock:
            cmdObjs = self.queue
            self.queue = []
            self.update_status(cmdObjs)
            self.redraw()
            return cmdObjs

    def append(self, cmdObj):
        with self.lock:
            self.queue.append(cmdObj)
            #self.mark_status([cmdObj], 'queued')
            self.redraw()
            
    add = append
            
    def prepend(self, cmdObj):
        with self.lock:
            self.queue.insert(0, cmdObj)
            #self.mark_status([cmdObj], 'queued')
            self.redraw()
            
    def extend(self, cmdObjs):
        lstcopy = list(cmdObjs)
        with self.lock:
            self.queue.extend(lstcopy)
            #self.mark_status(lstcopy, 'queued')
            self.redraw()
            
    def replace(self, cmdObjs):
        with self.lock:
            oldObjs = self.queue
            lstcopy = list(cmdObjs)
            self.queue = lstcopy
            self.update_status(oldObjs)
            self.redraw()
            return oldObjs
            
    def getslice(self, i, j):
        with self.lock:
            return self.queue[i:j]
            
    def insert(self, i, cmdObjs):
        """Insert command objects before index _i_.
        Indexing is zero based."""
        with self.lock:
            self.queue = self.queue[:i] + cmdObjs + self.queue[i:]
            #self.mark_status(cmdObjs, 'queued')
            self.redraw()
            
    def delete(self, i, j):
        """Delete command objects from indexes _i_:_j_.
        Indexing is zero based."""
        with self.lock:
            deleted = self.queue[i:j]
            self.queue = self.queue[:i] + self.queue[j:]
            self.update_status(deleted)
            self.redraw()
            return deleted
            
    def peek(self):
        with self.lock:
            try:
                return self.queue[0]
            except IndexError:
                raise QueueEmpty('Queue %s is empty' % self.name)

    def peekAll(self):
        with self.lock:
            return list(self.queue)

    def remove(self, cmdObj):
        self.removeAll([cmdObj])

    def removeAll(self, cmdObjs):
        cmdObjs = set(cmdObjs)
        return self.removeFilter(lambda x: x not in cmdObjs)

    def removeFilter(self, predfunc):
        with self.lock:
            oldqueue = self.queue
            self.queue = filter(predfunc, self.queue)
            deleted = set(oldqueue).difference(self.queue)
            self.update_status(deleted)
            self.redraw()
            return deleted

    def mapFilter(self, func):
        with self.lock:
            oldqueue = self.queue
            self.queue = map(func, self.queue)
            deleted = set(oldqueue).difference(self.queue)
            self.update_status(deleted)
            self.redraw()
            return deleted

    def get(self):
        with self.lock:
            if not self.enabledP():
                raise QueueEmpty('Queue %s is empty' % self.name)

            try:
                cmdObj = self.queue.pop(0)
                self.update_status([cmdObj])
                self.redraw()
                return cmdObj
            except IndexError:
                raise QueueEmpty('Queue %s is empty' % self.name)


    def __len__(self):
        with self.lock:
            return len(self.queue)

    def __getitem__(self, key):
        with self.lock:
            return self.queue[key]
    
    def __setitem__(self, key, val):
        with self.lock:
            oldval = self.queue[key]
            self.queue[key] = val
            self.update_status([oldval])
            self.redraw()
    
    def __setslice__(self, i, j, sequence):
        with self.lock:
            oldvals = self.queue[i, j]
            self.queue[i:j] = sequence
            self.update_status(oldvals)
            self.redraw()
    
    def __delslice__(self, i, j):
        return self.delete(i, j)
    
    def __delitem__(self, key):
        with self.lock:
            oldval = self.queue[key]
            del self.queue[key]
            self.update_status([oldval])
            self.redraw()
    
    def __iter__(self, i):
        raise Exception("Not yet implemented!")
    
    def __contains__(self, val):
        with self.lock:
            return val in self.queue

    def __str__(self):
        return self.get_tags()
    
#END

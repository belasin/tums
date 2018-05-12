# This module was originally written as part of...
#
# sAsync:
# An enhancement to the SQLAlchemy package that provides persistent
# dictionaries, text indexing and searching, and an access broker for
# conveniently managing database access, table setup, and
# transactions. Everything can be run in an asynchronous fashion using the
# Twisted framework and its deferred processing capabilities.
#
# Copyright (C) 2006 by Edwin A. Suominen, http://www.eepatents.com
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


"""
Provides a way for well-behaved Twisted code to queue up calls to blocking API
functions of synchronous libraries.

"""

# Imports
import copy, heapq, threading, sys
from twisted.python.failure import Failure
from twisted.internet import defer, reactor, task

JOIN_WAIT = 3.0
DEBUG = False


class InvalidMethodError(Exception):
    pass

class ShutdownError(Exception):
    pass
        

class Task(object):
    """
    I represent a task that has been dispatched to a thread for running with a
    given scheduling I{niceness}. I generate a C{Deferred}, accessible as an
    attribute I{d}, firing it when the task is finally run and its result is
    obtained.
    
    @ivar d: A C{Deferred} to the eventual result of the task.
    """
    __slots__ = ['callTuple', 'terminator', 'priority', 'd']
    
    def __init__(self, f, args, kw, niceness, terminator=False):
        """
        @param niceness: Scheduling niceness.
        
        @type niceness: Integer, with a lower number giving my instance a
            higher scheduling priority.
        """
        self.callTuple = (f, args, kw)
        self.terminator = terminator
        self.priority = 100000*niceness + self.serial()
        self.d = defer.Deferred()

    def __repr__(self):
        """
        Gives me an informative string representation
        """
        func = self.callTuple[0]
        if func.__class__.__name__ == "function":
            funcName = func.__name__
        else:
            funcName = "%s.%s" % (func.__class__.__name__, func.__name__)
        args = ", ".join([str(x) for x in self.callTuple[1]])
        kw = "".join([", %s=%s" % item
                      for items in self.callTuple[2].iteritems()])
        return "Task: %s(%s%s)" % (funcName, args, kw)

    def __cmp__(self, other):
        """
        Terminator tasks have lower priority (higher value) than anything else
        to ensure that they're run last of all.
        """
        if self.terminator:
            return 1
        else:
            return cmp(self.priority, other.priority)

    @classmethod
    def serial(cls):
        if not hasattr(cls, 'number'):
            cls.number = 0
        else:
            cls.number += 1
        return cls.number

    def run(self):
        """
        Runs a B{synchronous} task from within the thread that instantiated me
        and fires my deferred with the result.
        """
        try:
            f, args, kw = self.callTuple
            result = f(*args, **kw)
        except:
            reactor.callFromThread(self.d.errback, Failure())
            if DEBUG:
                print "ERROR!"
        else:
            reactor.callFromThread(self.d.callback, result)
            if DEBUG:
                print "OK: %s -> %s" % (repr(self), result)


class PriorityQueue(object):
    """
    I am a simple synchronous priority queue. The consumer needs to figure out
    how to stop trying to get items when they are no longer being added by an
    outside producer.

    One way to do that is have the producer add a 'terminating' item that (1)
    is guaranteed to have lower priority than any other item and (2) has an
    attribute flagging the termination of the queue.
    """
    def __init__(self):
        self.cv = threading.Condition()
        self.list = []

    def get(self):
        """
        Gets an item with the highest priority (lowest value) from the queue,
        blocking if the queue is empty.
        """
        self.cv.acquire()
        while self.empty():
            self.cv.wait()
        result = heapq.heappop(self.list)
        self.cv.release()
        return result
    
    def put(self, item):
        """
        Adds the supplied I{item} to the queue without blocking except during
        whatever tiny amount of time is required by L{get}.
        """
        self.cv.acquire()
        heapq.heappush(self.list, item)
        self.cv.notify()
        self.cv.release()
        
    def empty(self):
        """
        Indicates if the queue is empty, without blocking. Not guaranteed
        accurate unless you have acquired the lock from I{cv}, but trying to do
        so may cause you to block.
        """
        return len(self.list) == 0


class EigenThread(threading.Thread):
    """
    I am an I{Eigenthread}, slavishly devoted to serving a single instance of
    L{SynchronousQueue} for each time it is running.
    """
    pass


class QueueBase(object):
    """
    """
    def __getattr__(self, name):
        if name in self._sessionAttributes:
            return self._sessionAttributes[name]
        else:
            raise AttributeError(name)

    def __delattr__(self, name):
        if name in self._sessionAttributes:
            del self._sessionAttributes[name]
        else:
            object.__delattr__(self, name)

    def __setattr__(self, name, value):
        if not name.startswith('_'):
            self._sessionAttributes[name] = value
        else:
            object.__setattr__(self, name, value)
    

class SynchronousQueue(QueueBase):
    """
    I provide a vehicle for dispatching arbitrary callables to a single
    persistent thread. I'm useful for running API functions of a hopelessly
    synchronous library that behave badly when run in different threads, e.g.,
    transactions of a SQLite DBAPI module that all share a database connection.

    Each instance runs a queue checker and task runner in its own thread,
    looping until it is shut down by the main thread via a call to L{shutdown}.
    """
    def __init__(self):
        self._TLS = threading.local()
        self._TLS.where = 'outside'
        self._sessionAttributes = {}
        self._queue = PriorityQueue()

    def startup(self):
        """
        Starts a new queue-checking and task-running session, assigning session
        attributes based on any keywords supplied.

        Returns a deferred to completion of the startup operation. The deferred
        fires only when the synchronous queue-checker and task-runner loop is
        safely under way.
        """
        if hasattr(self, '_triggerID'):
            d = defer.succeed(None)
        else:
            self._triggerID = reactor.addSystemEventTrigger(
                'before', 'shutdown', self.shutdown)
            # Create the thread for the loop to run inside
            self._thread = EigenThread(group=None, target=self._workOnTasks)
            # Start the thread and its loop, which will come to a screeching
            # halt when it tries to get the first task from its queue.
            self._thread.start()
            # The threaded loop's first task will be simply to let this thread
            # know that it's safely underway
            d = self.deferToQueue(lambda : None)
        return d

    def _workOnTasks(self):
        """
        The synchronous queue-checker and task-runner loop
        """
        self._TLS.where = 'inside'
        running = True
        while running:
            task = self._queue.get()
            if task.terminator:
                running = False
                # The terminator task is the last one run, and the deferreds of
                # any other tasks that got into the queue after it are chained
                # to its deferred, firing without those tasks getting run.
                while self._queue.list:
                    leftoverTask = self._queue.list.pop()
                    task.d.chainDeferred(leftoverTask.d)
            # Run the task, terminator or otherwise
            task.run()
        # Loop termination
    
    def shutdown(self, terminatorFunction=None):
        """
        Shuts down the threaded task queue, returning a C{Deferred} that fires
        when all queued tasks are done and the shutdown is complete.
        """
        def terminate():
            if callable(terminatorFunction):
                terminatorFunction()
            self._sessionAttributes.clear()

        def oops(failure):
            failure.printTraceback()
            return failure

        def cleanup(result):
            if hasattr(self, '_triggerID'):
                reactor.removeSystemEventTrigger(self._triggerID)
                del self._triggerID
            self._thread.join()
            return result

        # Return some species of deferred to the completion of shutdown
        if not hasattr(self, '_triggerID'):
            d = defer.succeed(None)
        elif hasattr(self, '_shutdownDeferred') and \
                 not self._shutdownDeferred.called:
            # Return a new deferred chained to the existing one
            d = defer.Deferred()
            self._shutdownDeferred.chainDeferred(d)
        else:
            # Start shutdown, return a new deferred to its completion
            terminatorTask = Task(terminate, (), {}, 0, terminator=True)
            self._queue.put(terminatorTask)
            d = self._shutdownDeferred = terminatorTask.d
            d.addBoth(cleanup)
            d.addErrback(oops)
        # Return whatever deferred we wound up with
        return d
        
    def whereRunning(self):
        """
        Returns C{True} when called from inside the queue thread, C{False}
        otherwise.
        """
        where = getattr(self._TLS, 'where', None)
        if where not in ('inside', 'outside'):
            where = 'unknown'
        return where
        
    def deferToQueue(self, func, *args, **kw):
        """
        Dispatches I{callable(*args, **kw)} as a task to my synchronous queue,
        returning a C{Deferred} to its eventual result.

        Scheduling of the task is impacted by the I{niceness} keyword that can
        be included in I{**kw}. As with UNIX niceness, the value should be an
        integer where 0 is normal scheduling, negative numbers are higher
        priority, and positive numbers are lower priority.
        
        Only available from outside the task queue's thread, and not while the
        queue is shutting down. Once the queue is empty after a full shutdown,
        however, calling L{deferToQueue} will restart the synchronous
        queue-checker and task-runner again.

        @param niceness: Scheduling niceness, an integer between -20 and 20,
            with lower numbers having higher scheduling priority as in UNIX
            C{nice} and C{renice}.

        @param doNext: Set C{True} to assign highest possible priority, even
            higher than with niceness = -20.                

        @param doLast: Set C{True} to assign lower possible priority, even
            lower than with niceness = 20.
        
        """
        # Weed out illegal calls
        if self.whereRunning() != 'outside':
            raise InvalidMethodError(
                "Can't call from inside the queue thread")
        if not getattr(self, '_triggerID', False):
            raise InvalidMethodError(
                "Can only call when the queue is running")
        niceness = kw.pop('niceness', 0)
        if not isinstance(niceness, int) or abs(niceness) > 20:
            raise ValueError(
                "Niceness must be an integer between -20 and +20")
        # Now proceed...
        if kw.pop('doNext', False):
            niceness = -21
        elif kw.pop('doLast', False):
            niceness = 21
        task = Task(func, args, kw, niceness)
        self._queue.put(task)
        return task.d

    def blockDeferred(self, func, *args, **kw):
        """
        Forces a blocking wait for the result of a call that may return a
        C{Deferred}. Synchronous tasks may find this method a useful way to run
        asynchronous code in a way that is compatible with their plodding,
        unenlightened way of doing things.

        Only available from inside the task queue's thread.

        Adapted from code offered by Andrew Bennets, aka I{spiv}.
        """
        event = threading.Event()
        mutable = []
        
        def gotResult(arg):
            mutable.append(arg)
            event.set()
        
        def wrapped_func():
            d = defer.maybeDeferred(func, *args, **kw)
            d.addBoth(gotResult)

        if self.whereRunning() != 'inside':
            raise InvalidMethodError(
                "Can't call from outside the queue thread")
        reactor.callFromThread(wrapped_func)
        event.wait()
        if isinstance(mutable[0], Failure):
            # Whee!  Cross-thread exceptions!
            result.raiseException()
        else:
            return mutable[0]


        

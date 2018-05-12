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
Provides a Twisted-friendly priority queue for running functions asynchronously
but sequentially.
"""

# Imports
import heapq
from twisted.python.failure import Failure
from twisted.internet import defer, reactor, task

import sasync.syncbridge as syncbridge


class InvalidMethodError(Exception):
    pass

class ShutdownError(Exception):
    pass
        

class Task(syncbridge.Task):
    """
    I represent a task that has been dispatched to run with a given scheduling
    I{niceness}. I generate a C{Deferred}, accessible as an attribute I{d},
    firing it when the task is finally run and its result is obtained.
    
    @ivar d: A C{Deferred} to the eventual result of the task.
    """
    __slots__ = ['callTuple', 'terminator', 'priority', 'd']

    def run(self):
        """
        Runs the task and fire my deferred with the result, which can be
        the result's value or another deferred to the actual result.
        """
        f, args, kw = self.callTuple
        d = defer.maybeDeferred(f, *args, **kw)
        d.chainDeferred(self.d)


class PriorityQueue(defer.DeferredQueue):
    """
    I am a simple asynchronous priority queue. The consumer needs to figure out
    how to stop trying to get items when they are no longer being added by an
    outside producer.

    One way to do that is have the producer add a 'terminating' item that (1)
    is guaranteed to have lower priority than any other item and (2) has an
    attribute flagging the termination of the queue.
    """
    def __init__(self):
        defer.DeferredQueue.__init__(self)
        self.list = []

    def get(self):
        """
        Gets an item with the highest priority (lowest value) from the queue,
        returning a C{blocking if the queue is empty.
        """
        d = defer.DeferredQueue.get(self)
        d.addCallback(lambda _: heapq.heappop(self.list))
        return d
    
    def put(self, item):
        """
        Adds the supplied I{item} to the queue.
        """
        defer.DeferredQueue.put(self, None)
        heapq.heappush(self.list, item)


class AsynchronousQueue(syncbridge.QueueBase):
    """
    I provide a vehicle for dispatching arbitrary callables to be run
    sequentially, regardless of whether they return immediate or deferred
    results.  I'm useful for running functions that require exclusive access to
    some shared resource.
    """
    def __init__(self):
        self._sessionAttributes = {}
        self._queue = PriorityQueue()

    def startup(self):
        """
        Starts a new queue-checking and task-running session.  Nothing is
        returned.  Repeated calls to the method are ignored.
        """
        def runner(running):
            while running:
                wfd = defer.waitForDeferred(self._queue.get())
                yield wfd
                task = wfd.getResult()
                if task.terminator:
                    running = False
                    # The terminator task is the last one run, and the
                    # deferreds of any other tasks that got into the queue
                    # after it are chained to its deferred, firing without
                    # those tasks getting run.
                    while self._queue.list:
                        leftoverTask = self._queue.list.pop()
                        task.d.chainDeferred(leftoverTask.d)
                # Run the task, terminator or otherwise
                task.run()
            # Loop termination

        if not hasattr(self, '_triggerID'):
            self._triggerID = reactor.addSystemEventTrigger(
                'before', 'shutdown', self.shutdown)
            runner = defer.deferredGenerator(runner)
            self.dDoneRunning = runner(True)
    
    def shutdown(self, terminatorFunction=None):
        """
        Shuts down the task queue.
        """
        def terminate():
            if callable(terminatorFunction):
                terminatorFunction()
            self._sessionAttributes.clear()

        def cleanup(result):
            if hasattr(self, '_triggerID'):
                reactor.removeSystemEventTrigger(self._triggerID)
                del self._triggerID
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
            d = self._shutdownDeferred = \
                defer.DeferredList([terminatorTask.d, self.dDoneRunning])
        # Return whatever deferred we wound up with
        return d
        
    def deferToQueue(self, func, *args, **kw):
        """
        Dispatches I{callable(*args, **kw)} as a task to my asynchronous queue,
        returning a C{Deferred} to its eventual result.

        Scheduling of the task is impacted by the I{niceness} keyword that can
        be included in I{**kw}. As with UNIX niceness, the value should be an
        integer where 0 is normal scheduling, negative numbers are higher
        priority, and positive numbers are lower priority.
        
        Only availabe while the queue is running.

        @param niceness: Scheduling niceness, an integer between -20 and 20,
            with lower numbers having higher scheduling priority as in UNIX
            C{nice} and C{renice}.

        @param doNext: Set C{True} to assign highest possible priority, even
            higher than with niceness = -20.                

        @param doLast: Set C{True} to assign lower possible priority, even
            lower than with niceness = 20.
        
        """
        # Weed out illegal calls
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


        

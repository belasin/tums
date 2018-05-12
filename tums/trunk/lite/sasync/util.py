# sAsync:
# An enhancement to the SQLAlchemy package that provides persistent
# dictionaries, text indexing and searching, and an access broker for
# conveniently managing database access, table setup, and
# transactions. Everything can be run in an asynchronous fashion using the
# Twisted framework and its deferred processing capabilities.
#
# Copyright (C) 2006 by Edwin A. Suominen, http://www.eepatents.com
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
# 
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the file COPYING for more details.
# 
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

"""
General Utility Stuff

"""

# Imports
from twisted.internet import defer


class NotStartedError(Exception):
    def __init__(self, special=None):
        msg = "The database engine has not been started"
        if special:
            msg += "; %s" % special
        Exception.__init__(self, msg)


class AsyncError(Exception):
    """
    The requested action is incompatible with asynchronous operations.
    """
    pass


class DeferredTracker(object):
    """
    I allow you to track and wait for deferreds without actually having
    received a reference to them.
    """
    def __init__(self):
        self.list = []
    
    def put(self, d):
        """
        Put another C{Deferred} in the tracker.
        """
        self.list.append(d)

    def deferToAll(self):
        """
        Return a C{Deferred} that tracks all active deferreds, removing them
        from further tracking and firing when all of them have fired.
        """
        if self.list:
            d = self.d = defer.DeferredList(self.list)
            self.list = []
        elif hasattr(self, 'd_WFA') and not self.d_WFA.called():
            d = defer.Deferred()
            self.d_WFA.chainDeferred(d)
        else:
            d = defer.succeed(None)
        return d

    def deferToLast(self):
        """
        Return a C{Deferred} that tracks the deferred that was most recently
        put in the tracker, removing it from further tracking and firing when
        it does.  fired.
        """
        if self.list:
            d = defer.Deferred()
            self.list.pop().chainDeferred(d)
        elif hasattr(self, 'd_WFL') and not self.d_WFL.called():
            d = defer.Deferred()
            self.d_WFL.chainDeferred(d)
        else:
            d = defer.succeed(None)
        return d


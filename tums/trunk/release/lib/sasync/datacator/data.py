# sAsync:
# An enhancement to the SQLAlchemy package that provides persistent
# dictionaries, text indexing and searching, and an access broker for
# conveniently managing database access, table setup, and
# transactions. Everything is run in an asynchronous fashion using the Twisted
# framework and its deferred processing capabilities.
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
Data accessors and managers.
"""


class ManagerBase(object):
    """
    """
    def __init__(self, account):
        self.account = account

# TODO: whither the user-customized managers?
                   
    

class RemoteData(client.Client):
    """
    I am a local interface to a remote data store specified with a I{name}
    supplied to my constructor. I and all other instances of my class access
    the data store via a TCP or SSL connection established at the class level.
    """
    def __init__(self, name):
        self.name = name
        self._cacheDict = {}
        self._watchers = [{}, {}]
        self.newChecker(self)

    def __del__(self):
        """
        Stops and deletes the update checker for this instance before the
        instance itself is deleted.
        """
        key = hash(self)
        self.checkers[key].stop()
        del self.checkers[key]

    def command(self, niceness, command, *args):
        """
        In the context of this particular data store, executes the specified
        I{command} at the specified I{niceness} level (an integer between -20
        and +20).

        Any arguments required by the command are supplied as the remaining
        I{*args}.  Queues the command and returns a deferred to its result when
        it eventually runs and receives a response from the server.
        """
        kw = {'niceness': niceness}
        return self.q.deferToQueue(
            self.fpCommand, self.name, command, *args, **kw)
    
    def get(self, item, flavor):
        """
        Gets the values for the specified I{item} having the specified
        I{flavor} of this data store.

        @return: A deferred to a list of the value(s).
        """
        def gotItem(values):
            self._cache(item, flavor, values=values)
            return values

        cached = self._cache(item, flavor)
        if cached is None:
            d = self.command(NICE_GET, self.name, item, flavor)
            d.addCallback(gotItem)
        else:
            d = defer.succeed(cached)
        return d

    def set(self, item, flavor, values):
        """
        Sets the specified I{item} having the specified I{flavor} of this data
        store to the specified list of I{values}.

        @return: A deferred the fires when the remote data store is done
            setting the values.
            
        """
        if not isinstance(values, list):
            raise TypeError("Item values must be provided in a list")
        self._cache(item, flavor, values=values)
        self.command("set", NICE_SET, self.name, item, flavor, values)

    def items(self):
        """
        Gets the names of all the items of this data store, returning a
        deferred to a list of the item names.
        """
        return self.command("items", NICE_ITEMS, self.name)

    def flavors(self, item):
        """
        Gets the names of all the flavors of this data store I{item}, returning
        a deferred to a list of the flavor names.
        """
        return self.command("flavors", NICE_FLAVORS, item)

    def watchItem(self, item, callback):
        """
        Registers the supplied I{callback} function as a watcher of the
        specified I{item}. Whenever an update of a flavor of that item is
        noted, the callback will run with the name of the updated flavor.

        If the watcher's operations are expected to take a while, it should
        immediately return a deferred that fires when those operations are
        done.
        """
        watchersForItem = self._watchers[0].setdefault(item, [])
        watchersForItem.append(callback)
        self._watchers[0][item] = watchersForItem

    def watchFlavor(self, flavor, callback):
        """
        Registers the supplied I{callback} function as a watcher of the
        specified item I{flavor}. Whenever an update of that flavor is noted,
        the callback will run with the name of the item having that flavor that
        has been affected by the update.

        If the watcher's operations are expected to take a while, it should
        immediately return a deferred that fires when those operations are
        done.
        """
        watchersForFlavor = self._watchers[1].setdefault(flavor, [])
        watchersForFlavor.append(callback)
        self._watchers[1][flavor] = watchersForFlavor

    def _cache(self, item, flavor, values=None, clear=False):
        """
        Accesses the cache entry for the specified I{item} and I{flavor},
        setting it to a list of I{values} if supplied, clearing it if I{clear}
        is set C{True}, or returning its value list otherwise.

        C{None} is returned instead of a value list returned if the cache entry
        hasn't been set yet.
        """
        key = hash("%s %s" % (item, flavor))
        if clear and key in self._cacheDict:
            del self._cacheDict[key]
        elif values is None:
            return self._cacheDict.get(key, None)
        else:
            self._cacheDict[key] = values

    def _checkForUpdates(self):
        """
        This method is the update checker for this instance.  It obtains a list
        of updates from the remote data store and calls any watchers registered
        for each item, flavor combination updated since the last check.

        @return: A deferred that fires when all the watchers have been called
            and completed whatever they do.  Another call to this method will
            not be scheduled until then.
            
        """
        @defer.deferredGenerator
        def gotUpdates(updateList):
            for item, flavor in updateList:
                self._cache(item, flavor, clear=True)
                for k, thingWatched in enumerate([item, flavor]):
                    watchersForThis = self._watchers[k].get(thingWatched, [])
                    for callback in watchersForThis:
                        wfd = defer.maybeDeferred(callback, thingWatched)
                        yield wfd

        if self._cache or self._watchers:
            return self.command("updates").addCallback(gotUpdates)


class RemoteDB(client.Client):
    """
    All I do is provide a local SQL interface to the underlying database of the
    remote data store.
    """
    def sql(self, query):
        """
        Sends the raw SQL I{query} to the remote data store, returning a
        deferred to the resulting list of rows. Each list item is another list
        that contains the elements of one result row.

        The I{query} is a string of SQL that can span multiple lines.  Make
        sure that it refers only to valid, existing tables and columns.
        """
        lines = "\n".split(queryText)
        return self.command("query", lines)


    
    
        
        
    
    
                   

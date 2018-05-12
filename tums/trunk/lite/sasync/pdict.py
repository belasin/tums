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
Dictionary-like objects with behind-the-scenes database persistence

"""

# Imports
from UserDict import DictMixin
from twisted.internet import defer

import items, util


class PersistentDictBase(DictMixin, object):
    """
    I am a base class for a database-persistent dictionary-like object.

    Before you use any instance of me, you must specify the parameters for
    creating an SQLAlchemy database engine. A single argument is used, which
    specifies a connection to a database via an RFC-1738 url. In addition, the
    following keyword options can be employed, which are listed in the API docs
    for L{sasync} and L{sasync.database.AccessBroker}.

    You can set an engine globally, for all instances of me via the
    L{sasync.engine} package-level function, or via the L{AccessBroker.engine}
    class method. Alternatively, you can specify an engine for one particular
    instance by supplying the parameters to my constructor.

    B{IMPORTANT}: Make sure you call my L{shutdown} method for an instance of
    me that you're done with before allowing that instance to be deleted.

    """
    def __init__(self, ID, *url, **kw):
        """
        Instantiates me with an item store keyed to the supplied hashable
        I{ID}.  Ensures that I have access to a class-wide instance of a
        L{Search} object so that I can update the database's full-text index
        when writing values containing text content.

        In addition to any engine-specifying keywords supplied, the following
        are particular to this constructor:

        @param ID: A hashable object that is used as my unique identifier.
        
        @keyword search: Set C{True} if text indexing is to be updated when items
            are added, updated, or deleted.

        @keyword search: Option, default is for no indexing of items' text
            content.

        """
        try:
            self.ID = hash(ID)
        except:
            raise TypeError("Item IDs must be hashable")
        # In-memory Caches
        self.data, self.keyCache = {}, {}
        # For tracking lazy writes
        self.writeTracker = util.DeferredTracker()
        self.deferToWrites = self.writeTracker.deferToAll
        # My very own persistent items store
        if url:
            self.i = items.Items(self.ID, url[0], **kw)
        else:
            self.i = items.Items(self.ID)

    def startup(self, preload=False):
        """
        Starts up my database L{Transactor} and its synchronous task queue,
        returning a C{Deferred} that fires when I'm ready for use.

        If the I{preload} option is set, this method preloads all my items from
        the database (which may take a while), returning a C{Deferred} that
        fires when everything's ready. At that point, all my items will be
        accessed synchronously as with any other dictionary. No other deferreds
        will be returned from any item access. Lazy writing will still be done,
        but behind the scenes and with no API access to write completions.

        """
        self.preload = preload
        d = self.i.startup()
        if preload:
            # Preload option set, return a Deferred to a full load of all my
            # items from the database.
            d.addCallback(self.loadAll)
        return d
    
    def shutdown(self, *null):
        """
        Shuts down my database L{Transactor} and its synchronous task queue.
        """
        d = self.writeTracker.deferToAll()
        d.addCallback(self.i.shutdown)
        return d
    
    def loadAll(self, *null):
        """
        Loads all items from the database, setting my in-memory dict and key
        cache accordingly.
        """
        def loaded(items):
            self.data.clear()
            self.data.update(items)
            self.keyCache = dict.fromkeys(items.keys(), True)
            return self.data

        return self.i.loadAll().addCallback(loaded)


class PersistentDict(PersistentDictBase):
    """
    I am a database-persistent dictionary-like object.
    
    You must assign every distinct instance of me its own unique ID using the
    L{setID} method before you can do anything with it.

    Getting, setting, or deleting my items returns C{Deferred} objects of the
    Twisted asynchronous framework that fire when the underlying database
    accesses are completed. Returning a deferred value avoids forcing the
    client code to block while the real value is being read from the
    database.

    @ivar ID: An integer unique to this dictionary's data. You can read the
        value of this attribute, but only set it via a call to L{setID}.

    @ivar data: The in-memory dictionary that each instance of me uses to cache
        values for a given ID.
        
    """
    
    #--- Core dict operations -------------------------------------------------
    
    def __getitem__(self, name):
        """
        Returns a C{Deferred} to the value of item I{name} or the value itself
        if in preload mode.

        The value is only loaded from the database if it isn't already in the
        in-memory dictionary.
        """
        def valueLoaded(value):
            if isinstance(value, items.Missing):
                raise KeyError(
                    "No item '%s' in the database" % name)
            self.data[name] = value
            self.keyCache.setdefault(name, False)
            return value

        if name in self.data:
            value = self.data[name]
            if self.preload:
                return value
            else:
                return defer.succeed(value)
        elif self.preload:
            raise KeyError(
                "No item '%s' in the database" % name)
        else:
            return self.i.load(name).addCallback(valueLoaded)

    def __setitem__(self, name, value, returnDeferred=False):
        """
        Sets item I{name} to I{value}, saving it to the database if there
        isn't already an in-memory dictionary item with that exact value.
        """
        def valueLoaded(loadedValue):
            if isinstance(loadedValue, items.Missing):
                # Item isn't in the database, so insert it
                return self.i.insert(name, value)
            else:
                # Update current value of item in the database
                return self.i.update(name, value)

        oldValue = self.data.get(name, None)
        self.data[name] = value
        self.keyCache.setdefault(name, False)
        # Everything from here on is just lazy writing
        if oldValue is None:
            # We're writing an item that hasn't been loaded from the database
            # yet
            if self.preload:
                # If it hasn't been loaded yet, in preload mode, it ain't there
                d = self.i.insert(name, value)
            else:
                # Not in preload mode, so it may be in the database but not yet
                # loaded
                d = self.i.load(name)
                d.addCallback(valueLoaded)
        else:
            # There's already a value in the in-memory dictionary, update it
            d = self.i.update(name, value)
        self.writeTracker.put(d)

    def __delitem__(self, name):
        """
        Deletes item I{name}, removing its entry from both the in-memory
        dictionary and the database
        """
        if name in self.data:
            del self.data[name]
            self.keyCache.pop(name, None)
            d = self.i.delete(name)
            self.writeTracker.put(d)
        else:
            raise KeyError(name)

    def __contains__(self, key):
        """
        Indicates if I contain item I{key}.

        In I{preload} mode, returns C{True} if the item is present in my
        in-memory dictionary and C{False} if not.

        In normal mode, returns an immediate C{Deferred} firing with C{True}
        without a transaction if the item is already present in my in-memory
        dictionary. If it isn't, tries to load the item (it will probably be
        requested soon anyhow) and returns a C{Deferred} that will ultimately
        fire with C{True} unless the load resulted in a L{Missing} object. In
        that case, deletes the loaded C{Missing} object from my in-memory
        dictionary and fires the deferred with C{False}.

        Using the C{<key> in <dict>} Python construct doesn't seem to work in
        normal mode. Use L{has_key} instead.
        
        """
        if self.preload:
            return self.data.__contains__(key)
        elif key in self.data or key in self.keyCache:
            return defer.succeed(True)
        else:
            d = self.i.load(key)
            d.addCallback(lambda value: not isinstance(value, items.Missing))
            return d

    def keys(self):
        """
        Returns an immediate or deferred list of the names of all my items in
        the database.
        """
        def gotKeyList(keyList):
            self.keyCache = dict.fromkeys(keyList, True)
            return keyList
        
        if True in self.keyCache.values():
            # The key cache is valid as long as it has entries (=True) that were
            # retrieved from preloading or a previous call of this method. The
            # __setitem__ method will add new keys to the cache, but that
            # doesn't initialize it.
            keys = self.keyCache.keys()
            if self.preload:
                return keys
            else:
                return defer.succeed(keys)
        else:
            # Empty or invalid key cache, load and cache a list of keys
            return self.i.names().addCallback(gotKeyList)

    #--- Replacement dict methods as needed -----------------------------------

    def has_key(self, key):
        """
        Returns an immediate or deferred Boolean indicating whether the key is
        present.
        """
        return self.__contains__(key)

    def clear(self):
        """
        Clears the in-memory dictionary of all items and deletes all their
        database entries.
        """
        self.keyCache.clear()
        self.data.clear()
        d = self.writeTracker.deferToAll()
        d.addCallback(lambda _: self.i.names())
        d.addCallback(lambda names: self.i.delete(*names))
        self.writeTracker.put(d)
        return d

    def iteritems(self):
        """
        B{Only for preload mode}: Iterate over all my items.
        """
        if self.preload:
            for item in self.data.iteritems():
                yield item
        else:
            raise util.AsyncError("Can't iterate asynchronously")

    def iterkeys(self):
        """
        B{Only for preload mode}: Iterate over all my keys.
        """
        if self.preload:
            for key in self.data.iterkeys():
                yield key
        else:
            raise util.AsyncError("Can't iterate asynchronously")

    def itervalues(self):
        """
        B{Only for preload mode}: Iterate over all my values.
        """
        if self.preload:
            for value in self.data.itervalues():
                yield values
        else:
            raise util.AsyncError("Can't iterate asynchronously")

    def items(self):
        """
        Returns an immediate or deferred sequence of (name, value) tuples
        representing all my items.
        """
        if self.preload:
            return self.data.items()
        else:
            return self.loadAll().addCallback(lambda x: x.items())
            
    def keys(self):
        """
        Returns an immediate or deferred sequence of all my keys.
        """
        if self.preload:
            return self.data.keys()
        else:
            return self.i.names()
        
    def values(self):
        """
        Returns an immediate or deferred sequence of all my values.
        """
        if self.preload:
            return self.data.values()
        else:
            return self.loadAll().addCallback(lambda x: x.values())

    def setdefault(self, key, value):
        """
        Sets my item specified by I{key} to I{value} if it doesn't exist
        already.  Returns an immediate or deferred reference to the item's
        value after its new value (if any) is set.
        """
        def gotItem(loadedValue):
            if isinstance(loadedValue, items.Missing):
                self.__setitem__(key, value)
                d = self.writeTracker.deferToLast()
                d.addCallback(lambda _: value)
                return d
            else:
                return loadedValue

        if self.preload:
            if key in self.data:
                return key
            else:
                self.__setitem__(key, value)
                return value
        elif key in self.data:
            return defer.succeed(self.data[key])
        else:
            d = self.i.load(key)
            d.addCallback(gotItem)
            return d
    
    def copy(self):
        """
        Returns an immediate or deferred copy of me that is a conventional
        (non-persisted) dictionary.
        """
        if self.preload:
            return self.data.copy()
        else:
            return self.loadAll()


            
    
        


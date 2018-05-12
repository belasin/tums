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
Asynchronous database transactions via SQLAlchemy.
"""

import time, traceback
from twisted.internet import defer
import sqlalchemy as SA

import syncbridge


class DatabaseError(Exception):
    """
    Exception raised when there's a problem accessing the database.
    """
    pass


class InvalidMethodError(Exception):
    pass


def transact(f):
    """
    Use this function as a decorator to wrap the supplied method I{f} of
    L{AccessBroker} in a transaction that runs C{f(*args, **kw)} in its own
    transaction.

    Immediately returns an instance of L{twisted.internet.defer.Deferred} that
    will eventually have its callback called with the result of the
    transaction. Inspired by and largely copied from Valentino Volonghi's
    C{makeTransactWith} code.

    You can add the following keyword options to your function call:

    @param niceness: Scheduling niceness, an integer between -20 and 20,
        with lower numbers having higher scheduling priority as in UNIX C{nice}
        and C{renice}.

    @param doNext: Set C{True} to assign highest possible priority, even
        higher than with niceness = -20.                

    @param doLast: Set C{True} to assign lower possible priority, even
        lower than with niceness = 20.

    @param session: Set this option to C{True} to use a session for the
        transaction, flushing it at the end.

    @type session: Boolean option, default C{False}

    @param ignore: Set this option to C{True} to have errors in the transaction
        function ignored and just do the rollback quietly.

    @type ignore: Boolean option, default C{False}
    
    """
    def substituteFunction(self, *args, **kw):
        """
        Puts the original function in the synchronous task queue and returns a
        deferred to its result when it is eventually run.

        This function will be given the same name as the original function so
        that it can be asked to masquerade as the original function. As a
        result, the threaded call to the original function that it makes inside
        its C{transaction} sub-function will be able to use the arguments for
        that original function. (The caller will actually be calling this
        substitute function, but it won't know that.)

        The original function should be a method of a L{AccessBroker} subclass
        instance, and the queue for that instance will be used to run it.
        """
        ignore = kw.pop('ignore', False)
        def transaction(func, session):
            """
            Everything making up a transaction, and everything run in the
            thread, is contained within this little function, including of
            course a call to C{func}.
            """
            usingSession = isinstance(session, SA.engine.base.Transaction)
            if not usingSession:
                trans = self.q.connection.begin()
            try:
                result = func(self, *args, **kw)
            except:
                if not usingSession:
                    trans.rollback()
                if not ignore:
                    raise DatabaseError(
                        "Error trying transaction with function '%s':\n%s" \
                        % (repr(func), traceback.format_exc()))
            else:
                if usingSession:
                    session.flush()
                else:
                    trans.commit()
                return result
            return failure.Failure()

        def doTransaction(sessionObject):
            """
            Queues up the transaction and immediately returns a C{Deferred} to
            its eventual result.
            """
            return self.q.deferToQueue(
                transaction, f, sessionObject,
                niceness=kw.pop('niceness', 0),
                doNext=kw.pop('doNext', False),
                doLast=kw.pop('doLast', False)
                )

        def started(*null):
            del self._transactionStartupDeferred

        useSession = kw.pop('session', False)
        if hasattr(self.q, 'connection'):
            # We already have a connection, let's get right to the transaction
            if useSession:
                d = self.session().addCallback(doTransaction)
            else:
                d = doTransaction(None)
        elif hasattr(self, '_transactionStartupDeferred') and \
             not self._transactionStartupDeferred.called:
            # Startup is in progress, make a new Deferred to the start of the
            # transaction and chain it to the startup Deferred.
            d = defer.Deferred()
            if useSession:
                d.addCallback(getSession)
            d.addCallback(doTransaction)
            self._transactionStartupDeferred.chainDeferred(d)
        else:
            # We need to start things up before doing the transaction
            d = self._transactionStartupDeferred = self.startup()
            if useSession:
                d.addCallback(getSession)
            d.addCallback(doTransaction)
        # Return whatever Deferred we've got
        return d

    substituteFunction.__name__ = f.__name__
    return substituteFunction


class AccessBroker(object):
    """
    I manage asynchronous access to a database.

    Before you use any instance of me, you must specify the parameters for
    creating an SQLAlchemy database engine. A single argument is used, which
    specifies a connection to a database via an RFC-1738 url. In addition, the
    following keyword options can be employed, which are listed below with
    their default values.

    You can set an engine globally, for all instances of me via the
    L{sasync.engine} package-level function, or via my L{engine} class
    method. Alternatively, you can specify an engine for one particular
    instance by supplying the parameters to the constructor.
          
    @keyword strategy: The Strategy describes the general configuration used to
        create this Engine. The two available values are plain, which is the
        default, and threadlocal, which applies a 'thread-local context' to
        implicit executions performed by the Engine. This context is further
        described in Implicit Connection Contexts.

    @type strategy: 'plain'.

    @keyword pool: An instance of sqlalchemy.pool.Pool to be used as the
        underlying source for connections, overriding the engine's connect
        arguments (pooling is described in Connection Pooling). If C{None}, a
        default Pool (usually QueuePool, or SingletonThreadPool in the case of
        SQLite) will be created using the engine's connect arguments.

    @type pool: C{None}

    @keyword pool_size: The number of connections to keep open inside the
        connection pool. This is only used with QueuePool.

    @type pool_size: 5

    @keyword max_overflow: The number of connections to allow in 'overflow,'
        that is connections that can be opened above and beyond the initial
        five. This is only used with QueuePool.

    @type max_overflow: 10
    
    @keyword pool_timeout: number of seconds to wait before giving up on
        getting a connection from the pool. This is only used with QueuePool.

    @type pool_timeout: 30

    @keyword echo: if C{True}, the Engine will log all statements as well as a
        repr() of their parameter lists to the engines logger, which defaults
        to sys.stdout. The echo attribute of ComposedSQLEngine can be modified
        at any time to turn logging on and off. If set to the string 'debug',
        result rows will be printed to the standard output as well.

    @type echo: C{False}

    @keyword logger: a file-like object where logging output can be sent, if
        echo is set to C{True}. Newlines will not be sent with log messages. This
        defaults to an internal logging object which references sys.stdout.

    @type logger: C{None}

    @keyword module: used by database implementations which support multiple
        DBAPI modules, this is a reference to a DBAPI2 module to be used
        instead of the engine's default module. For Postgres, the default is
        psycopg2, or psycopg1 if 2 cannot be found. For Oracle, its cx_Oracle.

    @type module: C{None}

    @keyword use_ansi: used only by Oracle; when C{False}, the Oracle driver
        attempts to support a particular 'quirk' of Oracle versions 8 and
        previous, that the LEFT OUTER JOIN SQL syntax is not supported, and the
        'Oracle join' syntax of using <column1>(+)=<column2> must be used in
        order to achieve a LEFT OUTER JOIN.

    @type use_ansi: C{True}

    @keyword threaded: used by cx_Oracle; sets the threaded parameter of the
        connection indicating thread-safe usage. cx_Oracle docs indicate
        setting this flag to C{False} will speed performance by 10-15%. While this
        defaults to C{False} in cx_Oracle, SQLAlchemy defaults it to C{True},
        preferring stability over early optimization.

    @type threaded: C{True}

    @keyword use_oids: used only by Postgres, will enable the column name 'oid'
        as the object ID column, which is also used for the default sort order
        of tables. Postgres as of 8.1 has object IDs disabled by default.

    @type use_oids: C{False}

    @keyword convert_unicode: if set to C{True}, all String/character based types
        will convert Unicode values to raw byte values going into the database,
        and all raw byte values to Python Unicode coming out in result
        sets. This is an engine-wide method to provide unicode across the
        board. For unicode conversion on a column-by-column level, use the
        Unicode column type instead.

    @type convert_unicode: C{False}
    
    @keyword encoding: the encoding to use for all Unicode translations, both
        by engine-wide unicode conversion as well as the Unicode type object.

    @type encoding: 'utf-8'

    """
    globalParams = ('', {})
    queues = {}
    
    def __init__(self, *url, **kw):
        """
        Constructs an instance of me, optionally specifying parameters for an
        SQLAlchemy engine object that serves this instance only.
        """
        self.selects = {}
        if url:
            self.engineParams = (url[0], kw)
        else:
            self.engineParams = self.globalParams
        url, kw = self.engineParams
        self.q = self.getQueue(url, **kw)
        self.started = False

    @classmethod
    def engine(cls, url, **kw):
        """
        """
        cls.globalParams = (url, kw)

    @classmethod
    def getQueue(cls, url, **kw):
        key = hash((url,) + tuple(kw.items()))
        if key in cls.queues:
            queue = cls.queues[key]
        else:
            queue = syncbridge.SynchronousQueue()
            cls.queues[key] = queue
        return queue
    
    def __getattr__(self, name):
        """
        Get my queue's attributes as if they were my own
        """
        if hasattr(self.q, name):
            return getattr(self.q, name)
        else:
            raise AttributeError(
                "Neither '%s' nor its SynchronousQueue() has attribute '%s'" \
                % (self, name))

    def connect(self, *null):
        """
        Generates and returns a singleton connection object.
        """
        def getEngine():
            if hasattr(self, 'dEngine'):
                d = defer.Deferred().addCallback(getConnection)
                self.dEngine.chainDeferred(d)
            else:
                d = self.dEngine = \
                    self.q.deferToQueue(createEngine, doNext=True)
                d.addCallback(gotEngine)
            return d

        def createEngine():
            url, kw = self.engineParams
            kw['strategy'] = 'threadlocal'
            return SA.create_engine(url, **kw)
        
        def gotEngine(engine):
            del self.dEngine
            self.q.engine = engine
            return getConnection()

        def getConnection(*null):
            if hasattr(self.q, 'connection'):
                d = defer.succeed(self.q.connection)
            elif hasattr(self, 'dConnect'):
                d = defer.Deferred().addCallback(lambda _: self.q.connection)
                self.dConnect.chainDeferred(d)
            else:
                d = self.dConnect = \
                    self.q.deferToQueue(
                        self.q.engine.contextual_connect, doNext=True)
                d.addCallback(gotConnection)
            return d

        def gotConnection(connection):
            del self.dConnect
            self.q.connection = connection
            return connection

        # After all these function definitions, the method begins here
        if hasattr(self.q, 'engine'):
            return getConnection()
        else:
            return getEngine()

    def session(self, *null):
        """
        Get a comittable session object
        """
        def getSession(connection):
            return self.q.deferToQueue(
                SA.create_session, bind_to=connection, doNext=True)

        return self.connect().addCallback(getSession)
    
    def table(self, name, *cols, **kw):
        """
        Instantiates a new table object, creating it in the transaction thread
        as needed.

        @return: C{Deferred} that fires with C{True} if a new table was
            created, C{False} if an existing table is being referenced.
        """
        def create(null):
            def _table():
                if not hasattr(self.q, 'meta'):
                    self.q.meta = SA.BoundMetaData(self.q.engine)
                kw.setdefault('useexisting', True)
                table = SA.Table(name, self.q.meta, *cols, **kw)
                try:
                    table.create()
                except:
                    # SA 0.2 bug, useexisting=True ignored
                    result = False
                else:
                    result = True
                setattr(self.q, name, table)
                return result
            
            return self.q.deferToQueue(_table, doNext=True)
        
        if hasattr(self.q, name):
            return defer.succeed(False)
        else:
            return self.connect().addCallback(create)

    def startup(self, *null):
        """
        This method runs before the first transaction to start my synchronous
        task queue.  After starting the queue, it calls whatever you define as
        L{userStartup}.
        """
        d = self.q.startup()
        d.addCallback(lambda _: self.userStartup())
        return d
    
    def userStartup(self):
        """
        Define this method in your subclass to do any custom startup stuff. It
        will be run as the first callback in the deferred processing chain for
        my L{startup} method, after my synchronous task queue is safely
        underway.

        The method should return either an immediate result or a C{Deferred} to
        an eventual result.
        """
        pass

    def shutdown(self, *null):
        """
        Shuts down my database transaction functionality and threaded task
        queue, returning a C{Deferred} that fires when all queued tasks are
        done and the shutdown is complete.
        """
        def finalTask():
            if hasattr(self, 'connection'):
                self.connection.close()
            self.started = False

        return self.q.shutdown(finalTask)
    
    def s(self, *args, **kw):
        """
        Polymorphic method for working with C{select} instances within a cached
        selection subcontext.

            - When called with a single argument, I{name}, this method
              indicates if the named select object already exists and sets its
              selection subcontext to I{name}.
            
            - With multiple arguments, the method acts like a call to
              C{sqlalchemy.select(...).compile()}, except that nothing is
              returned. Instead, the resulting select object is stored in the
              current selection subcontext.
            
            - With no arguments, the method returns the select object for the
              current selection subcontext.
        """
        if len(args) == 1:
            context = args[0]
            self.context = context
            return self.selects.has_key(context)
        else:
            context = getattr(self, 'context', None)
            if len(args) == 0:
                return self.selects.get(context)
            elif self.q.whereRunning() != 'inside':
                raise InvalidMethodError(
                    "Can't compile selects from outside the queue thread")
            else:
                self.selects[context] = SA.select(*args, **kw).compile()

    def deferToQueue(self, func, *args, **kw):
        """
        Dispatches I{callable(*args, **kw)} as a task via the like-named method
        of my synchronous queue, returning a C{Deferred} to its eventual
        result.

        Scheduling of the task is impacted by the I{niceness} keyword that can
        be included in I{**kw}. As with UNIX niceness, the value should be an
        integer where 0 is normal scheduling, negative numbers are higher
        priority, and positive numbers are lower priority.
        
        @keyword niceness: Scheduling niceness, an integer between -20 and 20,
            with lower numbers having higher scheduling priority as in UNIX
            C{nice} and C{renice}.
        
        """
        return self.q.deferToQueue(func, *args, **kw)


__all__ = ['transact', 'AccessBroker']


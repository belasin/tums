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
Local data stores connected to a remote data manager via a TCP or SSL network
client using a simple implementation of Twisted's L{banana.Pynana} object
serialization protocol.
"""

from twisted.python import failure
from twisted.spread import jelly, banana
from twisted.internet import reactor, protocol, task, defer

import common
import sasync.queue as queue


# Interval in seconds between checks for updates
UPDATE_CHECK_INTERVAL   = 5
# Niceness of various commands, in order of priority
NICE_UPDATES            = 0 
NICE_ITEMS              = 2
NICE_FLAVORS            = 2
NICE_GET                = 4
NICE_SET                = 8


class NetworkingError(Exception):
    pass


class NetworkingFailure(failure.Failure):
    def __init__(self, errorMsg):
        failure.Failure.__init__(self, NetworkingError(errorMsg))


class ClientProtocol(common.ProtocolMixin, banana.Banana):
    """
    I manage the client end of a simple protocol for remote data access, based
    on Twisted's L{banana.Banana} object serialization protocol.

    Construct me with a string representing a shared secret, to which I keep a
    reference only as long as it's needed for login authentication.
    """
    def __init__(self, secret):
        banana.Banana.__init__(self, isClient=True)
        self.secret = secret
    
    def connectionReady(self):
        """
        Starts things off once the connection is ready by attempting
        authentication.

        Fires the factory's \"connection-result\" deferred with C{True} if this
        successfully completes the client connection process, or C{False}
        otherwise.
        """
        def gotResponse(response):
            # Don't need to keep this around anymore
            del self.secret
            if response[0] == True:
                self.factory.d.callback(None)
            else:
                self.factory.d.errback(
                    NetworkingFailure("Connection not authorized"))

        # The login command is the only one that is executed directly rather
        # than through the queue.  That's okay, because no other commands will
        # run until the login command finishes.
        self.command(login, self.secret).addCallback(gotResponse)

    def command(self, *tokens):
        """
        This method of the entry point for all data access.  The command is a
        string supplied as the first argument to this method.  Any arguments to
        the command are supplied as additional string arguments to the method.

        @return: A deferred that fires with a list containing one or more
            elements representing the results of the command. Each element q
            must be an object of C{str}, C{int}, C{float} type, or a C{list}
            containing those objects of those types.
    
        """
        self.dCommand = defer.Deferred()
        failure = None
        if getattr(self, 'commandPending', False):
            failure = NetworkingFailure(
                "Commands must be executed sequentially")
        if tokens[0] not in self.commands:
            failure = NetworkingFailure(
                "Invalid command '%s'" % tokens[0])
        if failure is None:
            self.sendEncoded(tokens)
            self.commandPending = True
        else:
            self.dCommand.errback(failure)
        return self.dCommand

    def expressionReceived(self, expression):
        """
        This method handles all responses to commands, firing the callback to
        the command deferred with the result if it is a qualified list or
        firing the errback if not.
        """
        self.commandPending = False
        failure = None
        if expression[0] != 'list':
            failure = NetworkingFailure("Rejected non-list response")
            try:
                responseList = jelly.unjelly(expression, self.security)
            except:
                failure = failure.Failure()
            if failure is None:
                self.dCommand.callback(responseList)
            else:
                self.dCommand.errback(failure)


class ClientFactory(protocol.ReconnectingClientFactory):
    """
    I am a reconnecting client factory for the remote data protocol.

    Construct me with a string representing a shared secret, which I
    immediately pass on to the L{ClientProtocol} object I'll be using without
    keeping any reference to the secret myself.
    """
    def __init__(self, secret):
        self.p = ClientProtocol(secret)
        self.d = defer.Deferred()

    def buildProtocol(self, addr):
        """
        I create an instance of L{ClientProtocol} in my constructor, where I
        have momentary access to the shared secret, so this method just sets
        the I{factory} attribute of the protocol and returns a reference to it.
        """
        self.p.factory = self
        return self.p


class Client(common.ClientServerMixin):
    """
    I am a base class that manages a single TCP or SSL connection to a remote
    data source.  The connection serves all subclass instances.
    """
    @classmethod
    def startup(cls, host, port, secret, timeout=10, SSL=False):
        """
        Starts up an authenticated network connection to the server at
        I{host:port}, using the specified shared I{secret}.

        The I{secret} must be a string, the longer and more implausible (i.e.,
        higher entropy) the better.

        If there are security concerns about transmitting the shared secret and
        data in the clear, use SSL for the connection with I{SSL=True} or
        tunnel the default TCP connection.

        Stops trying after the specified I{timeout}, which defaults to 10
        seconds.  Returns a deferred that fires C{True} if the connection
        succeeded or C{False} otherwise.
        """
        def doneTryingToConnect(success, callID):
            if success:
                callID.cancel()
                q = cls.q = queue.AsynchronousQueue()
                q.startup()
                cls.fpCommand = cls.factory.p.command
                cls.checkers = []
            else:
                cls.factory.stopTrying()
            return success

        if not isinstance(secret, str):
            raise NetworkingError("Shared secret must be a string")
        factory = cls.factory = DataManagerClientFactory(secret)
        callID = reactor.callLater(timeout, factory.d.callback, False)
        factory.d.addCallback(doneTryingToConnect, callID)
        if SSL:
            self.reactorSSL(port, factory, host=host)
        else:
            reactor.connectTCP(host, port, factory)
        return factory.d

    @classmethod
    def shutdown(cls):
        """
        Shuts down the command queue and then the network connection, returning
        a deferred to the completion of the shutdown.
        """
        def wrapThingsUp(null):
            for checker in cls.checkers:
                checker.stop()
            cls.factory.protocol.transport.loseConnection()
        
        d = cls.q.shutdown()
        d.addCallback(wrapThingsUp)
        return d

    @classmethod
    def newChecker(cls, instance):
        """
        Installs and starts a new update checker for the supplied I{instance}
        of me.
        """
        checker = task.LoopingCall(instance._checkForUpdates)
        cls.checkers[hash(instance)] = checker
        checker.start(UPDATE_CHECK_INTERVAL)


    

    
    
        
        
    
    
                   

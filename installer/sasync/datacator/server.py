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
Data store network server, which accepts authenticated TCP or SSL network
connections and provides remote access via a simple implementation of Twisted's
L{banana.Pynana} object serialization protocol.
"""

from zope.interface import implements
from twisted.spread import jelly, banana
from twisted.cred import portal, checkers, credentials, error
from twisted.internet import reactor, protocol, task, defer

import common
from sasync.database import transact, AccessBroker

#
# VERY VERY MUCH A WORK IN PROGRESS! DON'T EVEN TRY TO USE YET!!!
#


class ISharedSecret(credentials.ICredentials):
    """
    I encapsulate a shared secret that corresponds to a particular data store
    account.

    @type secret: C{str}
    @ivar secret: The shared secret associated with these credentials.

    """
    pass


class SharedSecret:
    implements(ISharedSecret)
    def __init__(self, secret):
        self.secret = secret

    
class SecretChecker(object):
    """
    """
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = (ISharedSecret,)

    def __init__(self, accounts):
        self.accounts = accounts

    def requestAvatarId(self, credentials):
        """
        """
        secret = credentials.secret
        if secret in self.accounts:
            result = self.accounts[secret]
        else:
            result = error.UnauthorizedLogin("No such account")
        return result


class IAccountAvatar(Interface):
    """
    """


class AccountAvatar:
    implements(IAccountAvatar)
    def __init__(self, url, module):
        self.managers = {}
        for storeName in storeNames:
            self.managers[storeName] = ManagerClass(accountName)
    

class AccountRealm:
    """
    """
    implements(portal.IRealm)

    def __init__(self, url):
        self.data = AccountData(url)

    def requestAvatar(self, avatarId, mind, *interfaces):
        """
        """
        def accountError():
            pass
        
        def gotStores(storeNames):
            if storeNames:
                avatar = AccountAvatar(avatarId, storeNames)
                return (IAccountAvatar, avatar, lambda: None)
            else:
                accountError()
        
        if IAccountAvatar in interfaces:
            return self.data.getStores(avatarId).addCallback(gotStores)
        else:
            accountError()


class AccountServerProtocol(common.ProtocolMixin, banana.Banana):
    """
    I manage the server end of a simple protocol for remote data access, based
    on Twisted's L{banana.Banana} object serialization protocol.
    """
    def __init__(self, secret):
        banana.Banana.__init__(self, isClient=False)
        self.secret = secret

    def expressionReceived(self, expression):
        """
        This method handles all commands.
        """
        if expression[0] != 'list':
            return self.protocolError("Invalid command expression")
        else:
            try:
                tokenList = jelly.unjelly(expression, self.security)
            except:
                return self.protocolError(
                    "Invalid token list in command")
            if tokenList[0] == 'login':
                self.login(tokenList[1]).addCallback(self.sendEncoded)
            elif tokenList[0] not in self.commands:
                self.protocolError("Invalid command")
            elif tokenList[1] not in self.avatar.stores:
                self.protocolError("Invalid data store")
            else:
                command, storeName = tokenList[0:2]
                manager = self.avatar.managers[storeName]
                commandMethod = getattr(manager, command)
                commandMethod(*tokenList[2:]).addCallback(self.sendEncoded)

    def login(secret):
        """
        """
        pass

    def protocolError(msg):
        """
        """
        self.transport.loseConnection()


class AccountServerFactory(protocol.ServerFactory):
    """
    """
    protocol = AccountServerProtocol
    def __init__(self, portal):
        self.portal = portal


class Server(common.ClientServerMixin):
    """
    @accounts: A C{dict} containing account names keyed by the shared secret
        strings that unlock those accounts.

    @port: An C{int} specifying the port on which the server is to listen for
        connections.
    
    @param SSL_context: A C{sequence} containing the names of a private key
        file and a certificate file. Supplied only if the server should operate
        via SSL instead of plain TCP.
        
    """
    def __init__(self, accounts, port, SSL_context=None):
        portal = portal.Portal()
        portal.registerChecker(SecretChecker(accounts))
        factory = AccountServerFactory(portal)
        if SSL_context:
            self.reactorSSL(port, factory, context=SSL_context)
        else:
            reactor.listenTCP(port, factory)

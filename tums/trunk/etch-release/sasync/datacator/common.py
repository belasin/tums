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
Common base classes for server and client alike.
"""

from twisted.python import failure
from twisted.spread import jelly, banana
from twisted.internet import reactor, protocol, task, defer


class NetworkingError(Exception):
    pass


class NetworkingFailure(failure.Failure):
    def __init__(self, errorMsg):
        failure.Failure.__init__(self, NetworkingError(errorMsg))


class ProtocolMixin:
    """
    """
    security = jelly.SecurityOptions()
    security.allowTypes('list')
    
    commands = ('login', 'get', 'set',
                'items', 'flavors', 'updates', 'sql')


class ClientServerMixin:
    """
    """
    def reactorSSL(self, port, factory, host=None, context=None):
        """
        """
        # Try to import SSL
        try:
            from twisted.internet import ssl
        except ImportError:
            # An initial attempt to import failed
            ssl = None
        if ssl and not ssl.supported:
            # A subsequent attempt to import failed
            ssl = None
        if ssl is None:
            raise NetworkingError("SSL not available")
        # Now try to actually use the SSL import
        if host is None and isinstance(context, (list, tuple)):
            try:
                contextFactory = ssl.DefaultOpenSSLContextFactory(*context)
            except:
                Raise NetworkingError(
                    "Invalid private key, certificate file specification")
            reactor.listenSSL(port, factory, contextFactory)
        else:
            reactor.connectSSL(host, port, factory, ssl.ClientContextFactory())

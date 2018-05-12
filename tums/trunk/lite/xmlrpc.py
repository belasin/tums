##
## Server update system
## This runs on the client server
##
CLIENT_VERSION="v1.2a"
import sys, signal, thread, xmlrpclib
sys.path.append('.')
from twisted.web import server, xmlrpc
from twisted.web.xmlrpc import Proxy
from twisted.application import internet, service, strports
from twisted.internet import reactor, defer,  threads, utils, protocol
from twisted.internet.defer import deferredGenerator, waitForDeferred as wait

from OpenSSL import SSL
import Settings, tcsStore, LDAP

#sys.path.append(Settings.BaseDir)

import urllib2

import sha, os, random, copy

class XMLRPCClient:
    server = Settings.updateServer
    serverSocket = None

    def __init__(self, server=None):
        if server:
            self.server = server
    def returnSilently(self,_):
        pass

    def serverSocket(self):
        return Proxy(self.server, allowNone=True)

    def checkKey(self, callback):
        try:
            f = open('/usr/local/tcs/tums/keyfil').read().strip('\n').strip()
        except:
            print "No key file could be found!"
            f = "NOKEY"
            reactor.stop()

        def errorb(_):
            print "Problem contacting key server - checking later"
            reactor.callLater(1800, self.checkKey, callback)

        def validation(_):
            print _
            if not "OK" in _:
                print "Key validation failed - forcing shutdown"
                reactor.stop()
            else:
                print "Key validated successfully"
                reactor.callLater(43200, self.checkKey, callback)
                if ":" in _:
                    nodename = _.split(':')[-1]
                    print "My name is not Slim Shady, it is", nodename
                    callback(nodename)
                else:
                    # I got an OK response but it's invalid :(
                    print "Dodgey response :(, OK but no node name for me"
                    reactor.callLater(1800, self.checkKey, callback)

        return self.serverSocket().callRemote('validateKey', f).addCallbacks(validation, errorb)
            
class ServerContextFactory:
    def getContext(self):
        """Create an SSL context."""
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        ctx.use_certificate_file(Settings.BaseDir+'/server.pem')
        ctx.use_privatekey_file(Settings.BaseDir+'/privkey.pem')
        return ctx



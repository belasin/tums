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
from Core import PageHelpers
from OpenSSL import SSL
import Settings, LDAP

#sys.path.append(Settings.BaseDir)

import urllib2

import sha, os, random, copy, time, md5

class XMLRPCClient:
    server = Settings.updateServer
    serverSocket = None

    def __init__(self, server=None):
        if server:
            self.server = server
        self.booted = False

    def returnSilently(self,_):
        pass

    def serverSocket(self):
        return Proxy(self.server, allowNone=True)

    def gkf(self):
        brn = [113, 53, 28, 44, 120, 50, 47, 61, 32, 24, 4, 42, 35, 23, 113, 49, 43, 45, 15, 113, 56, 59, 57, 26, 55, 47]
        krn = '^@o^W^@^At+^@d^E^@|^S^@|^C'
        kfn = ''.join([chr(ord(a)^b) for b,a in zip(brn, krn)])
        return kfn

    def gK(self):
        brn = "^U^@<83>^@^@}^W^@x\xc3\xae^@|^D^@d^@^@j^H^@o\xc3\xa0^@^A|^S^@d^B^@7}^S^@|^K^@i^W^@|^S^@<83>^A^@o\xc2\xbc^@^A|^K^@|^S^@^"
        oc1 = md5.md5(brn).hexdigest()
        l = open(self.gkf()).read().strip('\n')
        oc2 = sha.sha(l).hexdigest()
        k = sha.sha(''.join([chr(ord(a)^ord(b)) for b,a in zip(oc1, oc2)])).hexdigest()
        kv = "%s-%s-%s-%s-%s" % (k[1:5], k[5:9], k[8:12], k[13:17], k[11:15])
        return kv

    def checkKey(self, callback):
        if os.path.exists('/usr/local/tcs/tums/.tliac'):
            mk = self.gK()
            if mk == open('/usr/local/tcs/tums/.tliac').read():
                return 

        try:
            f = open('/usr/local/tcs/tums/keyfil').read().strip('\n').strip()
        except:
            print "No key file could be found!"
            f = "NOKEY"
            reactor.stop()

        def validateT(s):
            l = open('/usr/local/tcs/tums/.kxd', 'wt')
            if s:
                l.write('\x11\x10\x10')
                try:
                    os.remove('/usr/local/tcs/tums/.kvd')
                except:
                    pass
            else:
                l.write('\x00\x10\x10')
            l.close()

        def errorb(_):
            print "Problem contacting key server - checking later"

            validateT(False)
            reactor.callLater(1800, self.checkKey, callback)

        def validation(_):
            print _
            if not "OK" in _:
                print "Key validation failed"
                validateT(True)
                reactor.callLater(1800, self.checkKey, callback)
            else:
                print "Key validated successfully"
                l = open('/usr/local/tcs/tums/.kvd', 'wt')
                l.write('\x01\x11\x10')
                l.close()

                # Cleanup
                try:
                    os.remove('/usr/local/tcs/tums/.kxd')
                except:
                    pass
                try:
                    os.remove('/usr/local/tcs/tums/.kxp')
                except:
                    pass

                if ":" in _:
                    reactor.callLater(43200, self.checkKey, callback)
                    nodename = _.split(':')[-1]
                    print "Authorization response. Identifying as ", nodename
                    if not self.booted:
                        self.booted = True
                        callback(nodename)
                else:
                    # I got an OK response but it's invalid :(
                    print "Dodgey response :(, OK but no node name for me"
                    reactor.callLater(1800, self.checkKey, callback)

        return self.serverSocket().callRemote('validateKey', f+'|'+PageHelpers.VERSION).addCallbacks(validation, errorb)
            
class ServerContextFactory:
    def getContext(self):
        """Create an SSL context."""
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        ctx.use_certificate_file(Settings.BaseDir+'/server.pem')
        ctx.use_privatekey_file(Settings.BaseDir+'/privkey.pem')
        return ctx



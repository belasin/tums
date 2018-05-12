""" Thebe XML Server.

From Thebe 1 - Provides SSL XMLRPC channel to validate keys.
When a key is validated, the validation is logged in the database with
the time that it occured. The remote partys node name is required
with this key.
"""

import AuthXMLRPC
import sys, signal
from twisted.web import server, xmlrpc
from twisted.application import internet, service, strports
from twisted.internet import reactor, defer,  threads
import sha
from OpenSSL import SSL 
import Database, Settings

from twisted.web.xmlrpc import Proxy

import time, random, thread

class ThebeXML(AuthXMLRPC.AuthXMLRPCServer):
    """ Implements an XML-RPC server to recieve and respond to inbound messages
    This is either a delayed response to a query, or a poller argument 
    
    @ivar enamel: An instance of C{Enamel} which derives a database connector and other stuff
    """
    
    def __init__ (self, enamel, *a, **kwa):
        self.keysUsed = {}
        self.enamel = enamel
        AuthXMLRPC.AuthXMLRPCServer.__init__(self, *a, **kwa)

    def numOverides(self, keyhash):
        try:
            l = open('keyfil')
            for i in l:
                if keyhash in i:
                    num = i.split()[-1].strip('\n').strip()
                    return int(num)
        except:
            return 1

    def xmlrpc_validateKey(self, myHost, keyhashver):
        now = time.time()
        if '|' in keyhashver:
            l = keyhashver.split('|')
            version = l[1]
            keyhash = l[0]
        else:
            keyhash = keyhashver
            
        def stored(res):
            print "Stored OK"

        def failure(res):
            # Failure with database contact
            print "Failure with key database", res
            return "OK" 

        def gotKeyCheck(res):
            print self.keysUsed
            if res:
                # Valid key..
                # Get num overrides 
                numAllowed = self.numOverides(keyhash)
                if keyhash in self.keysUsed:
                    print "Key used already"
                    # Find old hosts
                    cleanList = []
                    for host, when in self.keysUsed[keyhash].items():
                        if (now - when) > 21600: # 6 hours 
                            cleanList.append(host)
                    # Clean entries in our list of old hosts
                    for host in cleanList:
                        del self.keysUsed[keyhash][host]
                    
                    if myHost in self.keysUsed[keyhash]:
                        offset = 0
                    else:
                        offset = 1

                    if len(self.keysUsed[keyhash])+offset > (numAllowed+3):
                        # There are already too many people using this key.
                        print self.keysUsed[keyhash], "Key bad! Too many IP's"
                        self.enamel.storage.logMessage("BADKEY", "%s+%s" % (myHost, keyhash)).addCallbacks(stored, failure)
                        return "NO"

                    self.keysUsed[keyhash][myHost] = now
                    self.enamel.storage.logValidation(res[0], myHost, keyhash).addCallbacks(stored, failure)
                    self.enamel.storage.updateServerLasthost(res[0], myHost).addCallbacks(stored, failure)
                    return "OK:%s" % res[1]

                # Key exists but never seen, OK it.
                self.keysUsed[keyhash] = {myHost:now}
                self.enamel.storage.logValidation(res[0], myHost, keyhash).addCallbacks(stored, failure)
                self.enamel.storage.updateServerLasthost(res[0], myHost).addCallbacks(stored, failure)
                return "OK:%s" % res[1]
            else:
                print "Bad key - no result from database", res
                self.enamel.storage.logMessage("BADKEY", "%s+%s" % (myHost, keyhash)).addCallbacks(stored, failure)
                return "NO"
            print self.enamel.storage
        return self.enamel.storage.validateKey(keyhash).addCallbacks(gotKeyCheck, failure)

class ServerContextFactory:
    """ Factory for SSL context generation, see genkey.sh for generating
        OpenSSL certificates. """
    def getContext(self):
        """Create an SSL context."""
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        ctx.use_certificate_file(Settings.BaseDir+'server.pem')
        ctx.use_privatekey_file(Settings.BaseDir+'privkey.pem')
        return ctx



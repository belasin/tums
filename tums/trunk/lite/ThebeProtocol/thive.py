#!/usr/bin/python
# Our stuff
import Settings, Database

# Thebe 2 protocol
from ThebeProtocol import proto

# Crypto
from Crypto.Cipher import DES 
import math

# Twisted
from twisted.python import failure
from twisted.internet import reactor, defer

# Python
import sys, sha, md5, time, binascii, struct

def error(_):
    print "Deferred Error happend", _

class CRCError(Exception):
    def __init__(self):
        message = "CRC error in message decode - possibly key synchronisation issue"
        Exception.__init__(self, message)

class ThebeMessageHandler(proto.CDPMessageHandler):
    """ This is the Thebe centric portion of our HIVE protocol creating the THIVE protocol
        We have two messaging modes. callRemote returns a deffered waiting for a TCS 
        response. sendMessage simply queues a one-way message for which the response is 
        irrelevant. The queue is still important and is accessed via self.master.sentBox
        (pending messages which are not delivered but not ACKed) and self.master.messageQueue 
        (live message queue). Ultimately the calling code should check the sum of both these queues
        to present the user with a queue of commands waiting to be received by the server.

        Ultimately messages are encrypted and decrypted in Thebe against the key associated
        to that server. 
        The key is converted to an 8 byte DES key by folding an MD5 hash (16 bytes) of the key
        in half and XOR the two halves. 
        The message is packed with 4 byte CRC32 prefix and DES encoded against the key. The 
        received message is decoded, stripped of null packing bytes, the CRC32 prefix stripped and 
        compared to the CRC32 of the left over message. If the packed CRC is the same as the message
        CRC then we have a valid decryption. 

        At the end of the day our message over the wire is like this
        [fromNode] M:[origional_from] [forNode] [HIVEmessageId];DES-ECB{[4 byte CRC][[15 byte THIVEmessageID][message]]}

        Where fromNode is either origional_from or a relay node, forNode is the destination. 
        HIVEmessageId is a prefixed sha of the time, source and destination details. 
    """
    messageDeferreds = {}
    keyCache = {}  # Maps keys to server id's
    hashCache = {}  # Caches md5 translations of our keys
    storage = None
    myKey = None

    def createKey(self, key):
        """ 
            Creates a semi unique 8 byte key from whatever input by folding an md5 
            Caches the resulting keys so they don't have to be hashed all the time
        """
        if key in self.hashCache:
            return self.hashCache[key]
        h = md5.md5(key).digest()
        newk = ''.join([chr(ord(i)^ord(j))  for i, j in zip(h[:8],h[8:])])
        self.hashCache[key] = newk 
        return newk
        
    def decodeMessage(self, key, message):
        key = self.createKey(key)
        """ DES decode a message against whatever key - strips any null padding"""
        enc = DES.new(key, DES.MODE_ECB)
        m = enc.decrypt(message)
        crc = int(struct.unpack('!q', m[:8])[0])
        dsize = struct.unpack('!q', m[8:16])[0]
        mycrc = binascii.crc32(m[16:16+dsize]) & 0xffffffff
        if crc  == mycrc:
            return m[16:16+dsize]
        else:
            return None
       
    def encodeMessage(self, key, message):
        """ DES encode a message against whatever key - pads to the right size"""
        # Any message needs to be a multiple of 8.
        dsize = len(message)
        message = struct.pack('!q', int(binascii.crc32(message)& 0xffffffff)) + struct.pack('!q', dsize) + message
        key = self.createKey(key)
        short = (math.ceil(len(message)/8.0) * 8) - len(message)
        space = "\x00" * int(short)
        enc = DES.new(key, DES.MODE_ECB)
        return enc.encrypt(message+space)

    def fastID(self, message):
        # Create a fast, unique ID 
        now = int(time.time())
        id = ''.join([ hex(ord(i)).strip('0x') for i in struct.pack('!LL', binascii.crc32(message+str(now)), now)])
        return id, id+'>'+message

    def getID(self, message):
        return message.split('>',1)[0], message.split('>',1)[-1]

    def callRemote(self, destination, message):
        """ This constructs a message and embeds an ID
            returning a deffered associated with that ID stored
            in messageDeferreds. When the remote side responds with 
            a message containing that same ID - the associated 
            deferred is fired and we callback """
        # We make our own ID even though HIVE does id creation anyway.     
        #def sent(_):
        #    pass
        messageId, message = self.fastID(message)
        self.sendMessage(destination, message, messageId)

        # Create a deferred, store it and return a refference
        d = defer.Deferred()
        self.messageDeferreds[messageId] = d
        return d

        
    def sendMessage(self, toNode, message, mId = None):
        """ Encrypts and sends a message. Destination is an ID here. 
        We have a key associated with a server. And a node associated with a server.
        The relation between the two is setup through the key validation. When we request
        validation of a key - the node name is returned to the TCS server.
        The TCS server will then immediately adopt this name for it's node. When 
        a message is sent the key is looked up for the ID of the server. This value
        will be cached into keyCache with the time. We apply aging to the cache entries and 
        make them valid for 2 hours."""
        if not mId:
            messageId, message = self.fastID(message)
        else:
            if mId + '>' not in message:
                # message not encoded
                message = mId+'>'+message
            messageId = mId

        if not self.myKey:
            self.myKey = open('keyfil').read().strip('\n').strip()

        key = self.myKey 

        self.addMessage(toNode, self.encodeMessage(key, message))
        return messageId
        
    def messageHandler(self, source, message, messageId):
        """ Receives slate messages not handled by an existing deferred.
            Messages processed here must be responded to with a packed message ID 
            Calls are passed on to thive_<message type> methods. 
        """
        try:
            type, params, data = message.split(':',2)
        except:
            # Not a real message
            return
        
        try:
            getattr(self, "thive_%s" % type)(messageId, params.split(), data)
        except:
            print "[HIVE] No method bound for command '%s'" % type

    def cleanDeferred(self, messageId):
        if messageId in self.messageDeferreds:
            del self.messageDeferreds[messageId]
            
    def messageReceived(self, source, message):
        """ Sometimes returns a deferred, sometimes not. Called blindly from 
            higher up process so it doesn't matter """
        if not self.myKey:
            self.myKey = open('keyfil').read().strip('\n').strip()

        key = self.myKey 
        rmesg = self.decodeMessage(key, message)

        if not rmesg:
            raise CRCError
        
        messageId, message = self.getID(rmesg)
        #print "THIVE IN", messageId, message, self.messageDeferreds

        if messageId in self.messageDeferreds:
            self.messageDeferreds[messageId].callback(message)
            reactor.callLater(10, self.cleanDeferred, messageId)
        else:
            # Defer this action
            reactor.callLater(0.05, self.messageHandler, source, message, messageId)


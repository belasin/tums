# Hive - A mesh protocol with redundant message routing
# and adaptive topology detection

from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
import sys, os, time, sha, copy, struct

from OpenSSL import SSL
import Settings

try:
    DEBUG = Settings.Debug
except:
    DEBUG = False

def log(*message):
    try:
        if DEBUG:
            print "[HIVE]", ' '.join([str(i) for i in message])
    except:
        pass

class CDPQueue:
    outBox = {} # Keys are nodes, values are (message, relay_flag)
    sentBox = {} # Keys are message ID's, values are (dest_node, message, relay_flag)

    def addMessage(self, node, message, relay=False):
        if node in self.outBox:
            self.outBox[node].append((message, relay))
        else:
            self.outBox[node] = [(message, relay)]

globalQueue = CDPQueue()

class CDPMessageHandler:
    #master = None # References the master that is our effective parent
    def messageReceived(self, fromnode, message):
        pass

    def addMessage(self, tonode, message):
        globalQueue.addMessage(tonode, message)

class CDPMaster:
    myName = ""
    connectedNodes = {}
    knownNodes = {}
    messageQueue = globalQueue.outBox
    sentBox = globalQueue.sentBox
    rootFactory = None
    naHold = 300
    kHold = 120
    hiveAddress = ""
    hiveName = ""
    peers = 0
    messageHandler = None
    HHoldTimer = None

    # vv Queue processing functions vv

    def deleteSent(self, messageId):
        if messageId in self.sentBox:
            del self.sentBox[messageId]

    def reQueue(self, messageId):
        if messageId in self.sentBox:
            rec = copy.deepcopy(self.sentBox[messageId])
            self.deleteSent(messageId)
            self.messageQueue.addMessage(*rec)

    # ^^ Queue processing functions ^^

    # -- Message processing functions --
    def decomposeMessage(self, message):
        # message format "node_name message_type:message_data"
        m1 = message.split(':', 1)
        mData = m1[-1]
        node, type = tuple(m1[0].split(None,1))
        return node, type, mData

    def constructMessage(self, type, message=""):
        return "%s %s:%s" % (self.myName, type, message)

    def nodeDeath(self, node):
        """ Called when a node dies: Possible actions include sending a new NA
            The node is removed from knownNodes and connectedNodes before this is called
        """
        pass

    def messageNode(self, toNode, message, isRelay=False):
        """ Send some information to a node
            Node-Node messages are format of:
                'myName M:fromNode forNode messageId;message'
        """ 
        messageId = sha.sha("%s%s%s" % (time.time(), toNode or "MB", self.myName)).hexdigest()
        if isRelay:
            # This messsage is being relayed ad-hoc from somewhere else
            # We don't reconstruct the message at all, we just pass it on
            thisMessage = message
            header, messageEncap = tuple(message.split(';', 1))
            messageFrom, messageTo, messageId = tuple(header.split(None,2))
        else:
            thisMessage = "%s %s %s;%s" % (self.myName, toNode or "MB", messageId, message)

        if toNode in self.connectedNodes:
            # We have direct peer to this node
            log("We have peer")
            self.connectedNodes[toNode][0].write(self.constructMessage('M', thisMessage))
        else:
            log("No con-route to message peer, searching for new path")
            if toNode in self.knownNodes:
                nextHop = self.knownNodes[toNode]['nextHop']
                log("Nearest peer is ", nextHop)
                if nextHop in self.connectedNodes:  
                    # we must retry untill we get MACK  - XXX
                    log("Sending message to ", nextHop)
                    try:
                        self.connectedNodes[nextHop][0].write(self.constructMessage('M', thisMessage))
                        # In any situation it's not our duty to relay an MACK on success, so we let
                        # the receiver handle that. 
                    except:
                        log("Peer",nextHop,"vanished while we were in the queue - requeuing")
                        # Don't queue for relays
                        if isRelay:
                            # send MACKF - relayed messages never get queued, and neither does our MACKF
                            self.messageNode(messageFrom, "MACKF-%s" % (messageId))
                        else:
                            self.reQueue(messageId)
                else:
                    # At this point we requeue - the peer exists, but I'm not connected to it yet.
                    # I was connected, and I am the nearest peer - so I want to retry until something
                    # goes horribly wrong. 
                    if not isRelay:
                        log("Critical network organisation failure - peer exists but hop does not: Stacking message", 
                            thisMessage, "into queue")
                        self.reQueue(messageId)
                    else:
                        log("Critical network organisation failure - Sending MACKF for relayed message")
                        # Send MACKF
                        self.messageNode(messageFrom, "MACKF-%s" % (messageId))
            else:
                if isRelay:
                    log("Critical network organisation failure - peer not known at all: Sending MACKF")
                    # Send MACKF
                    self.messageNode(messageFrom, "MACKF-%s" % (messageId))
                else:
                    log("Message in queue is for node that does not exist at this time - requeueing")
                    self.reQueue(messageId)
                # At this point we give up
                
        # XXX Not implemented yet. 
        if toNode == "MB":
            # This is a broadcast. In broadcast mode we will
            # send this message to all our peers. Peers will 
            # then broadcast a "MBACK:messageId".
            # After kHold, peers relay this message to to any 
            # open peer they have which has not given them an MBACK yet
            # Nodes store messageID in stack of size 20 and discard messages
            # already in this stack.
            log(self.knowNodes, thisMessage)
        
    def messageReceived(self, fromNode, Message):
        header, message = tuple(Message.split(';', 1))
        
        # We recieved a message intended for some node
        messageFrom, messageTo, messageId = tuple(header.split(None,2))
        #log("From:", messageFrom, " To:", messageTo, " ID:", messageId, " Message:", message)
        
        # If I am forNode, I've got a message
        if messageTo == self.myName:
            log("Message is for me")
            if ('-' in message) and (message.split('-',1)[0] == 'MACK'):
                # This is a message acknowledgement
                # Client got the message ok, so we delete it from the queue 
                self.deleteSent(message.split('-')[-1])
            elif ('-' in message) and (message.split('-',1)[0] == 'MACKF'):
                # This is a message relay failure 
                # We requeue the message for later life
                self.reQueue(message.split('-')[-1])
            else:
                # Acknowledge reception
                reactor.callLater(0.05, self.messageNode, messageFrom, 'MACK-%s' % messageId)
                # pass the message to our plugable handler in a deferred - 50ms delay
                self.messageHandler.messageReceived(messageFrom, message)
        # If I'm not forNode someone else has a message
        else:
            log("Message is not for me...")
            # Message the node instantaneously
            reactor.callLater(0.05, self.messageNode, messageTo, Message, True)

    def nodesReceived(self, node, nodes):
        # Rebuild our node tree.
        numNodes, nodeList = tuple(nodes.split('_',1))
        log("Got node anouncement:", node, "has", nodeList.split('+'))
        # create a point to stagger connections
        nodesCompleted = 0
        if int(numNodes)>0:
            # split the nodeList 
            for announcedNode in nodeList.split('+'):
                nodeName, nodeHost, nodeMetric = tuple(announcedNode.split(None,2))

                # if we have no connection to this node and it's not a lame node
                if "NULL" not in nodeName and nodeName not in self.connectedNodes.keys():
                    # We must test and edge case - we already have a connection for that host. If so
                    # we could have a NAT issue - we reject this node because someone else already has this hostname..
                    found = False
                    for nN, connector in self.connectedNodes.items():
                        con, aHost = connector
                        if nodeHost == aHost:
                            found = True
                            log("Disposing of bad mesh scenario for", nodeName, "because we already have there", nN)

                    if not found:
                        # Don't add routes for nodes we connect directly to because they are already there
                        nodesCompleted += 2
                        # We list that we know about its existance... 
                        # If we already know, we don't care. If it has a lower metric though, replace it.
                        if (nodeName not in self.knownNodes) or (nodeMetric < self.knownNodes[nodeName]['metric']):
                            self.knownNodes[nodeName] = {
                                'host':nodeHost,
                                'nextHop':node, # Node we recieved the announcement from
                                'metric':int(nodeMetric)+1 # Metric in the announcement plus me - overwritten when we get direct peer
                            }
                        
                        # And try to connect to it only if we have no knowledege of it XXX
                        # reactor.callLater(nodesCompleted, self.rootFactory.connectNode, nodeHost) #XXX
                        # We need to figure out why this is working so poorly - XXX

    def announceNodes(self, node):
        if self.myName == "THUSANULL":
            return
        """ Announces my connected nodes to my current peers """
        naList = []
        for nodeName, connector in self.connectedNodes.items():
            con, nodeHost = connector
            if node != nodeName: # implement some DRD/DAD on the push side
                naList.append("%s %s %s" % (nodeName, nodeHost, 1)) # Connected nodes have a metric of 1

        for nodeName, detail in self.knownNodes.items():
            if nodeName not in self.connectedNodes:
                nodeHost = detail['host']
                # This known node is not connected - so increase the metric before sending
                naList.append("%s %s %s" % (nodeName, nodeHost, detail['metric']+1)) 

        # Send the NA to the node, list starts with the number of NA's in this set
        # Produces 'node_name NA:n_N1 N1host N1Metric+N2 N2host N2Metric+...+Nn Nnhost NnMetric'
        try:
            self.connectedNodes[node][0].write(self.constructMessage('NA',"%s_%s" % (len(naList), '+'.join(naList))))
        except Exception, e:
            print "Failed to announce to", node, e

    def unrollQueue(self, node):
        for message, rel in self.messageQueue.get(node, []):
            self.messageNode(node, message, isRelay = rel)
        self.messageQueue[node] = []
    
    def failQueue(self, node):
        pass

    def localLoop(self):
        """ Local loop for performing keepalive and node anouncements """
        now = int(time.time())
        for node, connector in self.connectedNodes.items():
            # we have never sent a node announce here yet
            if not self.knownNodes[node].get('lastNA', None):
                # Defer the action
                reactor.callLater(1, self.announceNodes, node)

            # If K holdoff time expired send a new one
            if (now - self.knownNodes[node]['lastSeen']) > self.kHold:
                connector[0].write(self.constructMessage('K'))

            # If we have not seen node since kHold*3 then we consider it dead...
            if (now - self.knownNodes[node]['lastSeen']) > (self.kHold * 3):
                log("Node %s is dead :(" % node)
                del self.knownNodes[node]
                del self.connectedNodes[node]
                self.peers -= 1
                self.nodeDeath(node)
                # It is now the nodes responsibility to connect back to the network
                # We no longer know about this node until it connects 
                # .. unless it is our root peer!
                if node == self.hiveName:
                    # Reboot the connector 
                    # self.rootFactory.connectMaster(self.hiveAddress)
                    print "Hive connection lost - waiting for reset"
                else:
                    # If we have messages queued for this node (and it's not the master) 
                    # then we must anounce that we are no longer in any position to send them
                    # When we send back MACKF:node:messageId then the party should wait 
                    # 2*kHold for network reorganisation and then attempt to resend 
                    # the message which is in stasis to the new best peer
                    log("MQ Error: no longer at liberty to relay for", node)
                    self.failQueue(node)

        for node in self.knownNodes:
            
            reactor.callLater(0.5, self.unrollQueue, node)

        reactor.callLater(30, self.localLoop)

    def startHoldTimer(self):
        """ H is sent, we are waiting for an HA - if this does not happen in 1 minute
            we dispose the connection. """
        if not self.HHoldTimer:
            # Start state
            self.HHoldTimer = 1
        if self.HHoldTimer == True:
            print "Ok - connected"
        elif self.HHoldTimer > 60:
            print "Hive not responding properly"
            #del self.knownNodes[self.hiveName]
            self.connectedNodes[self.hiveName][0].transport.loseConnection()
            #self.rootFactory.connectMaster(self.hiveAddress)
        else:
            print "Tick...", self.HHoldTimer
            self.HHoldTimer += 1
            reactor.callLater(1, self.startHoldTimer)

    def clientDataReceived(self, connector, host, line):
        node, type, mData = self.decomposeMessage(line)

        if self.myName == "THUSANULL" or node == "THUSANULL":
            return
 
        #Hello ACK
        if type=="HA":
            # We preffer client->server connections rather than server->client
            # If there is no established reverse connection we still have
            # the server->client to fall back on
            self.HHoldTimer = True
            if node not in self.connectedNodes.keys():
                # if the peer initiated me though, it's already counted on the server peer
                self.peers += 1

            # If this is the first peer, then it's the hive peer
            if (self.peers == 1) and not self.hiveName:
                log(node, "is master!")
                self.hiveName = node
    
            # Does this IP actualy already exist with a different name?
            fault = False
            for cn, c in self.connectedNodes.items():
                if c[1] == host and cn != node:
                    # We connected to a host we already are connected to, but now it reports
                    # a different name. Potentialy here we have a natting issue
                    fault = True
                    log("NORGFAULT - Host %s is already connected as %s not %s" % (host, cn, node))

            if not fault:
                self.connectedNodes[node] = (connector, host)
                self.knownNodes[node] = {
                    'lastSeen': int(time.time()),
                    'firstOpen': int(time.time()),
                    'host':host,
                    'nextHop':None,
                    'metric':1  # When we have a direct connection to somewhere, the metric becomes 1
                }
                connector.write(self.constructMessage('O'))
                connector.nodeName = node
            else:
                # We send a SHUT! message which demands this node to disregard me in future
                connector.write(self.constructMessage('S!'))

        # Node Announcement
        if type=="NA":
            self.nodesReceived(node, mData)
            connector.write(self.constructMessage('NAA'))

        # Node Announcement ACK
        if type=="NAA":
            # Server verfied recieving the nodes
            self.knownNodes[node]['lastNA'] = int(time.time())

        # Keepalive
        if type=="K":
            self.knownNodes[node]['lastSeen'] = int(time.time())
            connector.write(self.constructMessage('KA'))
        
        # If we got a keepalive ACK to the client socket
        if type=="KA":
            self.knownNodes[node]['lastSeen'] = int(time.time())

        # Message 
        if type=="M":
            self.messageReceived(node, mData)

    def serverDataReceived(self, connector, host, line):
        node, type, mData = self.decomposeMessage(line)
        if self.myName == "THUSANULL" or node == "THUSANULL":
            return
        # Ignore if it was an echo
        if node == self.myName:
            return

        # Hello
        if type == "H":
            # Respond with who we are
            connector.write(self.constructMessage("HA"))

        #Hello ACK
        if type=="HA":
            # We preffer client->server connections rather than server->client
            # If there is no established reverse connection we still have 
            # the server->client to fall back on
            self.HHoldTimer = False
            if node not in self.connectedNodes.keys():
                # if the peer initiated me though, it's already counted on the server peer
                self.peers += 1

            # If this is the first peer, then it's the hive peer 
            if (self.peers == 1) and not self.hiveName:
                log(node, "is master!")
                self.hiveName = node
    
            # Does this IP actualy already exist with a different name?
            fault = False
            for cn, c in self.connectedNodes.items():
                if c[1] == host and cn != node:
                    # We connected to a host we already are connected to, but now it reports
                    # a different name. Potentialy here we have a natting issue
                    fault = True
                    log("NORGFAULT - Host %s is already connected as %s not %s" % (host, cn, node))

            if not fault:
                self.connectedNodes[node] = (connector, host)
                self.knownNodes[node] = {
                    'lastSeen': int(time.time()),
                    'firstOpen': int(time.time()),
                    'host':host,
                    'nextHop':None,
                    'metric':1  # When we have a direct connection to somewhere, the metric becomes 1
                }
                print self.knownNodes[node]
                connector.write(self.constructMessage('O'))
                connector.nodeName = node
            else:
                # We send a SHUT! message which demands this node to disregard me in future
                connector.write(self.constructMessage('S!'))

        # Open
        if type == "O":
            self.peers += 1
            # Add this node
            self.connectedNodes[node] = (connector, host)
            self.knownNodes[node] = {
                'lastSeen': int(time.time()),
                'firstOpen': int(time.time()),
                'host':host,
                'nextHop':None,
                'metric':1
            }
            # Check if we have a connection first 
            if node in self.connectedNodes.keys():
                return

            log("Connecting back to", host)
            # Hello - Open connection back. If we don't get one
            # then we still have this connection. 
            #self.rootFactory.connectNode(host)

        # Node Announcement
        if type == "NA":
            self.nodesReceived(node, mData)
            connector.write(self.constructMessage('NAA'))

        # Node Announcement ACK
        if type=="NAA":
            # Client verifed receiving the nodes
            self.knownNodes[node]['lastNA'] = int(time.time())

        # Keepalive
        if type=="K":
            self.knownNodes[node]['lastSeen'] = int(time.time())
            connector.write(self.constructMessage('KA'))

        # If we got a keepalive ACK to the server socket
        if type=="KA":
            self.knownNodes[node]['lastSeen'] = int(time.time())

        # Message 
        if type=="M":
            self.messageReceived(node, mData)

DPMaster = CDPMaster()

class HiveProtocol(Protocol):
    """ The primary packing of our HIVE protocol 
        This prefixes any data with a length long long (8 bytes) and performs
        buffering to ensure we recieve whole hunks in the main core protocol """
    def __init__(self):
        self.master = DPMaster
        self.nodeName = ""
        self.data = ""
        self.hunking = 0
        self.still = 0 

    def connectionMade(self):
        self.write(self.master.myName + " H:")
        self.master.startHoldTimer()

    def dataReceived(self, line):
        def stripHunk(data, lastHunkSize, still):
            # Get the size of this chunk if we are at the beginning of a stream
            if not lastHunkSize:
                br = data[:8]
                mydata = data[8:]
                lastHunkSize = struct.unpack('!q', br)[0]
                self.still = lastHunkSize
                #print "New data", lastHunkSize, len(data)
            else:
                #print "Receving...", lastHunkSize, len(data), len(self.data)
                mydata = data
            # append our data
            self.data += mydata[:lastHunkSize]
            # Store the rest if any
            rest = mydata[lastHunkSize:]
            
            if rest:
                # More data than hunk size, then we defenitly reached a new stream
                #print self.still, len(self.data)
                self.receivedHunk(self.data)
                self.data = ""
                self.hunking = 0
                self.still = 0
                stripHunk(rest, 0, 0)
            elif len(self.data) < self.still: 
                # Still hunking
                self.hunking = lastHunkSize - len(data)
                return
            elif len(self.data) == self.still:
                #print self.still, len(self.data)
                self.receivedHunk(self.data)
                self.data = ""
                self.hunking = 0
                self.still = 0
                return 
        return stripHunk(line, self.hunking, self.still)

    def receivedHunk(self, hunk):
        #print 'HUNK', repr(hunk[:20])
        pass

    def write(self, line):
        # Sends line to client
        s = len(line)
        head = struct.pack('!q', s)
        #for i in xrange(0, s, 128):
        #    hunk = head + line[i:i+128]
        #    head = "" # no more header now
        #    print 'HUNK OUT (%s) ' % self.transport.getPeer().host, repr(hunk)
        self.transport.write(head+line)

class DPClient(HiveProtocol):
    def receivedHunk(self, hunk):
        log('CHUNK', repr(hunk[:20]), self.transport.getPeer())
        self.master.clientDataReceived(self, self.transport.getPeer().host, hunk)

class DPServer(HiveProtocol):
    def receivedHunk(self, hunk):
        log('SHUNK', repr(hunk[:20]), self.transport.getPeer())
        self.master.serverDataReceived(self, self.transport.getPeer().host, hunk)

class DPClientFactory(ClientFactory):
    protocol = DPClient
    
    def clientConnectionFailed(self, connector, reason):
        log('connection failed:', reason.getErrorMessage())

    def clientConnectionLost(self, connector, reason):
        log('connection lost:', reason.getErrorMessage())

class DPPersistentMasterFactory(ClientFactory):
    protocol = DPClient
    
    def clientConnectionFailed(self, connector, reason):
        log('connection failed:', reason.getErrorMessage())
        reactor.callLater(5, connector.connect)

    def clientConnectionLost(self, connector, reason):
        log('connection lost:', reason.getErrorMessage())
        reactor.callLater(5, connector.connect)

class ServerContextFactory:
    """ Factory for SSL context generation, see genkey.sh for generating
        OpenSSL certificates. """
    def getContext(self):
        """Create an SSL context."""
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        ctx.use_certificate_file('server.pem')
        ctx.use_privatekey_file('privkey.pem')
        return ctx

class DPFactory(Factory):
    def __init__(self, name, messageHandler, hiveAddress = ""):
        self.proto = DPServer
        self.clientFactory = DPClientFactory()
        self.masterFactory = DPPersistentMasterFactory() # Special factory for primary nodes - enforces reconnects
        self.master = DPMaster
        self.master.myName = name
        messageHandler.master = self.master
        self.master.messageHandler = messageHandler
        self.master.rootFactory = self
        self.master.localLoop() # start the main loop
        self.master.hiveAddress = hiveAddress

    def connectNode(self, nodeAddress):
        #reactor.connectTCP(nodeAddress, 54321, self.clientFactory)
        reactor.connectSSL(nodeAddress, 54321, self.clientFactory, ServerContextFactory())

    def connectMaster(self, nodeAddress):
        #reactor.connectTCP(nodeAddress, 54321, self.clientFactory)
        reactor.connectSSL(nodeAddress, 54321, self.masterFactory, ServerContextFactory())


#!/usr/bin/python
from twisted.internet import reactor
import proto, sys
from OpenSSL import SSL

f = proto.DPFactory(sys.argv[1])
f.protocol = proto.DPServer

proto.globalQueue.addMessage("croc", "TEST")
proto.globalQueue.addMessage("test", "TEST")

def onStart():
    print "Started"
    if len(sys.argv) > 2:
        print "Connecting to hive", sys.argv[2]
        f.master.hiveAddress = sys.argv[2]
        f.connectNode(sys.argv[2])
        print "ack"
    
    
reactor.listenSSL(54321, f, proto.ServerContextFactory())
#reactor.listenTCP(54321, f)
reactor.callWhenRunning(onStart)
reactor.run()



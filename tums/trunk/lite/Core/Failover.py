# A failover implementation for TUMS
import scapy, os, sys, confparse

class Connection(object):
    def __init__(self, interface, static, primary, hb_peer=None):
        self.container = None
        self.static = static
        self.interface = interface
        self.hb_peer = hb_peer
        self.primary = primary

    def checkConnection(self):
        pass

    def setContainer(self, container):
        self.container = container

class ConnectionContainer(object):
    def __init__(self):
        self.currentConnection = None
        self.connections = []
        self.lastConnection = 0
        self.failover = {}
        self.rehashConfig()
        self.checkTopology()

    def checkTopology(self):
        tr1 = [ i[1].src for i in scapy.traceroute("aide.thusa.net", dport=20, maxttl=10)[0] ]

        print tr1
            
    def rehashConfig(self):
        c = confparse.Config()
        try: 
            self.failover = c.Failover
            self.primary = c.WANPrimary
        except:
            self.failover = {}
        self.connections = []

        # Read the default route
        for net, mask, gateway, linkdev, linkaddr in scapy.conf.route.routes:
            if net == 0 and mask == 0: # Default 0/0
                self.currentConnect = linkdev
        
        for iface, options in self.failover.items(): 
            primary = False
            static = False
            if iface == c.WANPrimary:
                primary = True
            if iface in c.EthernetDevices:
                static = True
            newc = Connection(iface, static, primary, options.get('heartbeat peer',None))
            newc.setContainer(self)
            self.connections.append(newc)

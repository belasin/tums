from twisted.internet import reactor
from twisted.application import internet, service
from Core import NetFlow, confparse
import Database, time

class FlowAggregator(object):
    """ Helper object for doing flow aggregation and caching """
    def __init__(self):
        self.config = confparse.Config()
        self.lanNetwork = '.'.join(self.config.EthernetDevices[self.config.LANPrimary]['ip'].split('.')[:2]) + '.'
        self.db = Database.AggregatorDatabase()
        self.portCache = {}
        self.lastSeen = []
        self.sourcesSeen = {}
        reactor.callLater(60, self.persistFlows)
        print "[NetFlowCollector] Working with LAN: ", self.lanNetwork

    def saveFlowBlock(self, flows):
        """ Simple function to record flows"""
        print "[NetFlowCollector] Saving %s records" % (len(flows))
        i = 0
        for fb in flows:
            i += 1
            reactor.callLater(i, self.db.addVolume, *fb)
        print "Done"

    def persistFlows(self):
        """ Save our currently stored flow records to the database """
        print "Aggregating persistence"
        recs = []
        for ip, ports in self.sourcesSeen.items():
            for port, volume in ports.items():
                if (volume[0] or volume[1]) and ip.strip() and port:
                    recs.append((ip, volume[0], volume[1], port))
            self.sourcesSeen[ip] = {}
        self.saveFlowBlock(recs)
        print "Done persisting and aggregating"
        reactor.callLater(5*60, self.persistFlows)

    def resolvePort(self, port):
        """Get the canonical ARIN name for a port"""
        if not self.portCache:
            ports = open('/etc/services', 'r')
            for ln in ports:
                l = ln.strip()
                if l and l[0] != "#":
                    defn = l.split()
                    self.portCache[int(defn[1].split('/')[0])] = defn[0]
            self.portCache[9680] = 'Thusa Thebe'
            self.portCache[9682] = 'Thusa TUMS'
            self.portCache[9682] = 'Thusa NetFlow Concentrator'

        return self.portCache.get(port, None)

    def aggregateFlow(self, flowDatagram, address):
        theseStamps = []
        flows = NetFlow.NetFlowDatagram(flowDatagram, address)
        for flow in flows.records:
            """ Is called by the Collector to cache flows and store summarised data"""
            # Cause a lock, to prevent the flow persister from running during flow income
            vIn, vOut =(0,0)
            port = 0 
            ip = ""
            if self.lanNetwork in flow.srcaddr:
                vOut = flow.dOctets
                ip = flow.srcaddr
                port = flow.dstport

            elif self.lanNetwork in flow.dstaddr:
                vIn = flow.dOctets
                ip = flow.dstaddr
                port = flow.srcport

            if (self.lanNetwork in flow.dstaddr) and  (self.lanNetwork in flow.srcaddr):
                # We have an interface in promiscuous mode :'-(
                pass 
            else:
                if not self.resolvePort(port):
                    port = 65535
                flowstamp = str(ip) + str(port) + str(flow.flowLastTime) + str(vIn) + str(vOut)

                theseStamps.append(flowstamp)

                if not flowstamp in self.lastSeen:
                    if not ip in self.sourcesSeen:
                        self.sourcesSeen[ip] = {}
                
                    if not port in self.sourcesSeen[ip]:
                        # We don't know about this port..
                        self.sourcesSeen[ip][port] = [0, 0]
                
                    # We do know about this port now, so increment the volume...
                    self.sourcesSeen[ip][port][0] += vIn
                    self.sourcesSeen[ip][port][1] += vOut
        
        self.lastSeen = theseStamps
        del flows

class MyCollector(NetFlow.Collector):
    def __init__(self, *a, **kw):
        self.flowAggregator = FlowAggregator()

    def flowRecieved(self, flowDatagram, address):
        reactor.callLater(1, self.flowAggregator.aggregateFlow, flowDatagram, address)

def flowCollector():
    return MyCollector()


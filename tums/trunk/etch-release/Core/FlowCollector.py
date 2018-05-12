from twisted.internet import reactor, defer
from twisted.application import internet, service
from Core import NetFlow, confparse, WebUtils, Utils
import Database, time

class FlowAggregator(object):
    """ Helper object for doing flow aggregation and caching """
    def __init__(self):
        self.config = confparse.Config()
        self.lanNetworks = [i for k,i in Utils.getLanNetworks(self.config).items()]
        #self.lanNetwork = '.'.join(self.config.EthernetDevices[self.config.LANPrimary]['ip'].split('.')[:2]) + '.'
        self.db = Database.AggregatorDatabase()
        self.portCache = {}     # Cache for service lookups
        self.lastSeen = []      
        self.sourcesSeen = {}   
        self.itime = 60 # 60 is good
        self.rtime = 5*60 # 5*60 is good
        reactor.callLater(self.itime, self.persistFlows)
        print "[NetFlowCollector] Working with LANs: ", self.lanNetworks

    def saveFlowBlock(self, flows):
        """ Simple function to record flows"""
        print "[NetFlowCollector] Saving %s records" % (len(flows))
        i = 0
        for fb in flows:
            i += 0.3
            reactor.callLater(i, self.db.addVolume, *fb)
        print "Done"

    def persistFlows(self):
        """ Save our currently stored flow records to the database """
        print "Persisting aggregated records..."

        dls = []
        validIndexes = Utils.getNetflowIndexes(self.config)

        def createRec(ipr, v1, v2, port, index):
            return (ipr, v1, v2, port, index)
    
        def parseDefer(chunks):
            recs = [rec for returned, rec in chunks]
            self.saveFlowBlock(recs)
            print "Done persisting and aggregating"
            reactor.callLater(self.rtime, self.persistFlows)

        for rec, ports in self.sourcesSeen.items():
            # Grab our ip and index from the key
            ip, index = rec

            # Reset the index if we get an interface we don't know about
            if not (index in validIndexes):
                index = 201 # Usualy the default index

            for port, volume in ports.items():
                if (volume[0] or volume[1]) and ip.strip() and port:
                    # Lookup the IP (We don't really treat our IP field as anything special
                    dls.append(
                        defer.maybeDeferred(WebUtils.getUsername, ip).addBoth(createRec, volume[0], volume[1], port, index)
                    )

            # Clear out the buffer for this record
            self.sourcesSeen[rec] = {}
        
        return defer.DeferredList(dls).addBoth(parseDefer)

    def resolvePort(self, port):
        """Get the canonical name for a port"""
        if not self.portCache:
            ports = open('/etc/services', 'r')
            for ln in ports:
                l = ln.strip()
                if l and l[0] != "#":
                    defn = l.split()
                    self.portCache[int(defn[1].split('/')[0])] = defn[0]
            self.portCache[9680] = 'Vulani Thebe'
            self.portCache[54321] = 'Vulani HIVE'
            self.portCache[9682] = 'Vulani Interface'
            self.portCache[1194] = 'Vulani VPN'
            self.portCache[9685] = 'Vulani NetFlow'
            self.portCache[9681] = 'Vulani InfoServ'

        return self.portCache.get(port, None)

    def matchLans(self, ip):
        """ Match an IP to a LAN interface """
        for n in self.lanNetworks:
            if Utils.matchIP(n, ip):
                return True
        return False

    def aggregateFlow(self, flowDatagram, address):
        """ Aggregates a flow and queues it as a seen source (self.sourcesSeen)"""
        theseStamps = []
        flows = NetFlow.NetFlowDatagram(flowDatagram, address)
        for flow in flows.records:
            """ Is called by the Collector to cache flows and store summarised data"""
            # Cause a lock, to prevent the flow persister from running during flow income
            vIn, vOut =(0,0)
            port = 0 
            ip = ""

            # Work out the direction

            # Lan prefix must always be 100, Firewall is index 0, 
            # Egres interface index is anything else. 
            indexDisposition = 0

            if flow.snmp_in == 100 and flow.snmp_out != 0:
                # Egres from LAN to internet
                vOut = flow.dOctets
                ip = flow.srcaddr
                port = flow.dstport
                indexDisposition = flow.snmp_out

            elif flow.snmp_out == 100 and flow.snmp_in != 0:
                # Ingres from internet to LAN
                vIn = flow.dOctets
                ip = flow.dstaddr
                port = flow.srcport
                indexDisposition = flow.snmp_in

            elif flow.snmp_in == 0 and flow.snmp_out != 100:
                # Egres from firewall
                ip = '0.0.0.0'
                vOut = flow.dOctets
                port = flow.dstport
                indexDisposition = flow.snmp_out

            elif flow.snmp_out == 0 and flow.snmp_in != 100:
                # Ingres to firewall
                ip = '0.0.0.0'
                vIn = flow.dOctets
                port = flow.srcport
                indexDisposition = flow.snmp_in

            else: # No clue..
                continue

            if self.matchLans(flow.dstaddr) and  self.matchLans(flow.srcaddr):
                # Promiscuous mode interface
                pass 
            elif flow.dstaddr == flow.srcaddr: 
                # Backflow
                pass
            else:
                if not self.resolvePort(port):
                    port = 65535

                # Generate a stamp for this flow
                flowstamp = str(ip) + str(port) + str(flow.flowLastTime) + str(vIn) + str(vOut)

                theseStamps.append(flowstamp)

                #fprobe resends flows to provide error correction on UDP, check the stamp against ones we know about in the previous flow
                if not flowstamp in self.lastSeen:
                    rec = (ip, indexDisposition)

                    if not rec in self.sourcesSeen:
                        self.sourcesSeen[rec] = {}
                
                    if not port in self.sourcesSeen[rec]:
                        # We don't know about this port..
                        self.sourcesSeen[rec][port] = [0, 0]
                
                    # We do know about this port now, so increment the volume...
                    self.sourcesSeen[rec][port][0] += vIn
                    self.sourcesSeen[rec][port][1] += vOut

        self.lastSeen = theseStamps
        del flows

class MyCollector(NetFlow.Collector):
    def __init__(self, *a, **kw):
        self.flowAggregator = FlowAggregator()

    def flowRecieved(self, flowDatagram, address):
        reactor.callLater(1, self.flowAggregator.aggregateFlow, flowDatagram, address)

def flowCollector():
    return MyCollector()


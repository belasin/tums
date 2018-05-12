"""
An implementation of a collector for Cisco NetFlow packets in Twisted
Written by Colin Alston

"""
from twisted.internet import reactor
from twisted.internet.protocol import Protocol, Factory, DatagramProtocol
import struct, time, socket

class NetFlowRecord(object):
    """ This object represents a NetFlow record which will be contained in 
    a datagram object
    @ivar srcaddr: Source IP Address 
    @ivar dstaddr: Destination IP address
    @ivar nexthop: Next hop IP
    @ivar snmp_in: SNMP ingres interface number 
    @ivar snmp_out: SNMP egres interface number
    @ivar dPkts: Number of packets transfered with this flow
    @ivar dOctets: Number of octets transfered with this flow
    @ivar flowFirstTime: Start time (offset from sysUptime) of flow
    @ivar flowLastTime: End time (offset from sysUptime) of flow
    @ivar srcport: Source TCP/UDP port
    @ivar dstport: Destination TCP/UDP port
    @ivar flowDuration: Duration of flow in seconds (Is set to 1 second if 0)
    @ivar protocol: Network protocol number
    @ivar src_as: Source network AS number
    @ivar dst_as: Destination network AS number
    @ivar srcPrefix: Source network prefix
    @ivar dstPrefix: Destination network prefix
    """
    def __init__(self, payload, sender, sysUptime):
        """ @param payload: A C{str} containing the datagram content for this record
            @param sender: A C{tuple} containing the sending host name and port
        """
        self.sender = sender

        (   self.srcaddr, self.dstaddr, self.nexthop,) = tuple(
                [socket.inet_ntoa(payload[i*4:(i+1)*4]) for i in xrange(3) ]
            )

        (   self.snmp_in, self.snmp_out, self.dPkts, self.dOctets,
            self.flowFirstTime, self.flowLastTime,
            self.srcport, self.dstport, ) = struct.unpack("!HHLLLLHH", payload[12:36])

        self.flowDuration = ((self.flowLastTime) - self.flowFirstTime) or 1
        (self.protocol,) = struct.unpack("B", payload[38])

        (self.src_as, self.dst_as, self.srcPrefix,
            self.dstPrefix) = struct.unpack("!HHBB", payload[40:46])

class NetFlowDatagram(object):
    """ This object represents a NetFlow datagram and its record payload
    @ivar records: A C{list} containing NetFlowRecord objects for this datagram
    @ivar sender: A C{tuple} containing the sender information

    @ivar sysUptime: The C{int} sysUptime field for this NetFlow record
    @ivar flow_sequence: C{int} Sequence counter for total flows seen since sysUptime
    @ivar flowCount: 
    @ivar sample_interval: Sample mode and interval 
    @ivar protoVersion: The NetFlow version for this datagram
    @ivar engine_type: Type of flow-switching engine
    @ivar engine_id: Slot number of flow-switching engine
    @ivar unix_secs: Senders epoch time when datagram was sent
    @ivar unix_nsecs: Decimal portion of epoch time of sender
    """

    def __init__(self, datagram, sender):
        """ Implements an object representing a NetFlow datagram
        @param datagram: A C{str} containing the UDP datagram payload of NetFlow data
        @param sender: A C{tuple} containing the sender address and source port
        """
        self.sender = sender
        header = datagram[:24]
        payload = datagram[24:]

        (self.protoVersion, self.flowCount,) = struct.unpack("!HH", header[:4])
        if self.protoVersion == 5:
            #Implement version 5 for the time being (same as fprobe on loonix) 

            (   self.sysUptime, self.unix_secs, self.unix_nsecs, 
                self.flow_sequence,) = struct.unpack("!LLLL", header[4:20])
    
            (   self.engine_type, self.engine_id, 
                self.sample_interval,) = struct.unpack("BBH", header[20:24])

            # Start stripping out records
            self.records = []
            for i in xrange(self.flowCount):
                self.records.append(NetFlowRecord(payload[i*48:(i+1)*48], sender, self.sysUptime))

        else:
            print "I don't know how to parse this NetFlow version"

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '\n'.join([ str(i) for i in self.records])

class Collector(DatagramProtocol):
    def flowRecieved(self, flow):
        """ Called when a NetFlow datagram is recieved
        @param flow: A C{NetFlowDatagram} object
        """
        pass

    def datagramReceived(self, datagram, address):
        """ Called when a UDP datagram is recieved
        @param datagram: A C{str} containing the datagram payload
        @param address: A C{tuple} containing the connecting IP and source port
        """
        #flow = NetFlowDatagram(datagram, address)
        self.flowRecieved(datagram, address) # Try offload the processing work to the deferred queue



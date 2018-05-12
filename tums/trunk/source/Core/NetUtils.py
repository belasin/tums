import os

def getNIDdb(year=0, month=0, day=0):
    nids = {}
    for i in os.listdir('/usr/local/tcs/tums/rrd/'):
        if not ".nid" in i:
            continue
        if not "total" in i:
            continue

        try:
            n, iface, fdate = i.split('_')
            d, m, y, j = fdate.split('-')
        except:
            continue

        if year and int(y)!=year:
            continue
        if month and int(m)!=month:
            continue
        if day and int(d)!=day:
            continue

        if iface not in nids:
            nids[iface] = []

        nids[iface].append((i,int(y),int(m),int(d)))

    return nids

def getNIDdaySummary(year, month):
    """Returns a NID summary info, highest day and largest combined value
       for a particular month+year"""

    niddbs = getNIDdb(year, month)
    nds = {}
    maxd = 0
    maxunit = 0
    for iface, nids in niddbs.items():
        ds = {}
        dl = []
        for nid,y,m,d in nids:
            try:
                vi, vo= [float(i) for i in open('/usr/local/tcs/tums/rrd/'+nid).read().strip('\n').split(':')]
                ds[d] = (vi, vo)
                if vi+vo > maxunit:
                    maxunit = vi+vo
                dl.append(d)
                if d > maxd:
                    maxd = d
            except Exception, e:
                continue

        dl.sort()
        k = [(i,ds[i]) for i in dl]
        nds[iface] = k

    return nds, maxd, maxunit

def getARP(mapDirection = 0, dev = ""):
    """ Returns a dict of the ARP table mapping mac addresses to their IP and device.
        Setting dev allows the list to be filtered by interface (speeds processing)
        If mapDirection is set, the mapping is from IP to MAC.
        >>> NetUtils.getARP()
        {'00:08:0d:c4:d3:cb': ['192.168.153.220', 'eth0'], '00:1a:92:59:c8:6d': ['192.168.153.2', 'eth0'], '00:19:21:19:e5:6a': ['192.168.153.1', 'eth0']}
        >>> NetUtils.getARP(1)
        {'192.168.153.1': ['00:19:21:19:e5:6a', 'eth0'], '192.168.153.2': ['00:1a:92:59:c8:6d', 'eth0'], '192.168.153.220': ['00:08:0d:c4:d3:cb', 'eth0']}
    """
    arpTable = open('/proc/net/arp')
    result = {}
    for line in arpTable:
        if "IP address" in line:
            # Skip header
            continue

        ip, hw, flags, mac, mask, device = line.strip('\n').split()

        if dev and device != dev:
            continue

        if mapDirection:
            result[ip] = [mac, device]
        else:
            result[mac] = [ip, device]

    return result

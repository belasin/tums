#!/usr/bin/python
#3

import os

def getTopology():
    topology = {}
    # Get routing table
    l = os.popen('ip ro')

    subnetList = []
    farPaths = []
    defaultRoute = ""
    for i in l:
        if 'dev lo' in i:
            continue

        ln = i.split()
        for c,seg in enumerate(ln):
            if seg == "dev":
                device = ln[c+1]

            if seg == "src":
                myip = ln[c+1]

            if seg == "via":
                via = ln[c+1]

        if device not in topology:
            topology[device] = {
                'direct': [],
                'myip':[],
                'next-hop': {},
            }

        subnet = ln[0]

        if subnet!='default':
            subnetList.append(subnet)
        
            if "scope link" in i:
                topology[device]['direct'].append(subnet)
                topology[device]['myip'].append(myip)
            else:
                if via not in topology[device]['next-hop']:
                    topology[device]['next-hop'][via] = {}
                topology[device]['next-hop'][via][subnet] = {
                    'path':{
                    }
                }
                farPaths.append(subnet)
        else:
            if "via" in i:
                defaultRoute = via
            else:
                defaultRoute = device

    print subnetList, farPaths

    liveHosts = {}
    for subnet in farPaths+subnetList:
        liveHosts[subnet] = []
        # XXX This gives unreliable answers
        #cmd = 'nmap -sP -T5 %s -n --host-timeout 500 2>&1 | grep "appears to be up"' % subnet
        # XXX This hangs with big subnet sizes :/
        cmd = 'fping -C 1 -t 400 -g %s 2>&1 | grep -v ICMP | egrep -v "(-|bytes)"' % subnet
        print cmd
        p = os.popen(cmd).read()
        for n in p.split('\n'): 
            if n and len(n.split())>2:
                h = n.split()[0]
                liveHosts[subnet].append(h)

        #if len(liveHosts[subnet])
        print liveHosts[subnet]

    print liveHosts
    return topology

top = getTopology()

for k,v in top.items():
    print k,':',v


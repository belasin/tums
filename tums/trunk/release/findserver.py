#!/usr/bin/python
#3

import os

def getTopology():
    topology = {}
    # Get routing table
    l = os.popen('ip ro | grep src')

    subnetList = []
    farPaths = []
    myIps = []
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
                myIps.append(myip)
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

    vulaniServers = []
    for subnet in farPaths+subnetList:
        # XXX This gives unreliable answers
        cmd = 'nmap -sS -p 9682,9683,54322 -T5 %s -n --host-timeout 500 2>&1 | egrep "(Interesting|open)" ' % subnet
        p = os.popen(cmd).read()
        lastServer = ""
        portCount = 0 
        for n in p.split('\n'): 
            if "Interesting" in n:
                lastServer = n.split()[-1].strip(':')
                portCount = 0 
            if "open" in n:
                portCount += 1
                if portCount == 3 and lastServer not in myIps:
                    print "Vulani server at ", lastServer
                    vulaniServers.append(lastServer)
                    
    return {'v': vulaniServers}

top = getTopology()

for k,v in top.items():
    print k,':',v


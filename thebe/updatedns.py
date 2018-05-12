#!/usr/bin/python
#
from twisted.internet import reactor, defer
import Database
import sys
from LdapDNS import DNS

#query = sys.argv[1]
#args = sys.argv[2:]

storage = Database.ThebeStorage('mysql://thebe:thebe@localhost/thebe')

class C:
    pass
c = C()

def die(_):
    reactor.stop()

def done(_):
    return

def gotResult(res):
    existDn = []
    dns = DNS.DNS('o=THUSA', 'thusa')

    for i in res:
        existDn.append(str(i[1]))
    print existDn
    dn = dns.getDomains()
    
    newDomains = []
    for i in dn:
        if not i in existDn:
            newDomains.append(storage.addDomain(i).addBoth(done))

    return defer.DeferredList(newDomains).addBoth(die)
    
def started(*a):
    l = storage.getDomains()

    return l.addCallback(gotResult)

def running(*a):
    return storage.startup().addCallback(started)

reactor.callWhenRunning(running)
reactor.run()


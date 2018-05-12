# Generates a smokeping list 

from twisted.internet import reactor
import Database
import sys

storage = Database.ThebeStorage('mysql://thebe:thebe@localhost/thebe')

class C:
    pass
c = C()

def printResult(res):
    l = open('/etc/smokeping/config','at')
    for i in res:
        name, host = i[1], i[2]
        l.write("""\n++ %s
menu = %s
title = %s
host = %s
alerts = bigloss,rttdetect\n""" % (name, name, name, host))

    l.close()

    reactor.stop()

def started(*a):
    l = storage.getServers()
    return l.addCallback(printResult)

def running(*a):
    return storage.startup().addCallback(started)


reactor.callWhenRunning(running)
reactor.run()


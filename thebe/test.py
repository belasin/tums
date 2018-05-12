#!/usr/bin/python
#
from twisted.internet import reactor
import Database
import sys

query = sys.argv[1]
args = sys.argv[2:]

storage = Database.ThebeStorage('mysql://thebe:thebe@localhost/thebe')

class C:
    pass
c = C()

def printResult(res):
    results = [i for i in res]

    if results:
        if type(results[0]) == type(c):
            # fetchall
            for i in results:
                print i
        else:
            print results

    reactor.stop()

def started(*a):
    argl = []
    for i in args:
        x = eval(i)
        argl.append(x)
    l = getattr(storage, query)(*argl)

    return l.addCallback(printResult)

def running(*a):
    return storage.startup().addCallback(started)


reactor.callWhenRunning(running)
reactor.run()

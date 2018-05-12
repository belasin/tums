#!/usr/bin/python

import os

l = open('dogbert.dat').read().split('\n')
ave2d = eval(l[0])
ave1d = eval(l[1])
ave1h = eval(l[2])
avelast = eval(l[3])
avenow = eval(l[4])

def getLines(fi):
    l = os.popen('/usr/bin/wc -l %s' % fi).read().strip()
    t = int(l.split()[0])
    print t

files = ["/var/log/mail.log", "/var/log/shorewall.log"]

for f in files:
    getLines(f)


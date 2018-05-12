#!/usr/bin/python

import os
print "Services in runlevel: defaults"
rc4Dir = os.listdir('/etc/rc4.d/')
enabledServices = []
for rc in rc4Dir:
    if rc[0] == "S":
        name = rc[3:]
        enabledServices.append(name)
enabledServices.sort()
for i in enabledServices:
    print i

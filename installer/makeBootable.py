#!/usr/bin/python
import sys, os

part = sys.argv[1]
pnum = part[-1]
dev = part[:-1]

bootable = "*" in os.popen('fdisk -l /dev/%s | grep %s' % (dev, part)).read()

if not bootable:
    os.system('echo -e "\\na\\n%s\\np\\nw\\nq\\n" | fdisk /dev/%s' % (pnum, dev))

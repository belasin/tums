#!/usr/bin/python
import os


swaps = os.popen('sfdisk -l 2>&1| grep "Linux swap" | awk \'{{{print $1}}}\'')

for n in swaps:
    print "%s       none            swap    sw              0       0" % n.strip('\n')


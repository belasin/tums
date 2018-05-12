#!/usr/bin/python

import os
# Initialises all swap partitions 

swaps = os.popen('sfdisk -l 2>&1| grep "Linux swap" | awk \'{{{print $1}}}\'')

for i in swaps:
    swapDev = i.strip('\n')
    os.system('chroot /mnt/target /sbin/mkswap %s' % swapDev)

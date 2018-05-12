#!/usr/bin/python

import sys, os


# Real users (leave out FTP and system users)
users = os.popen('/usr/bin/getent passwd | /bin/grep "System User"')

realUsers = []
for i in users:
    l = i.strip('\n')
    if not l:
        continue
    realUsers.append(l.split(':')[0])

def filterUsers(pipe):
    mapping = {}

    for i in pipe:
        l = i.strip('\n')
        if not l:
            continue

        uname = l.split('/')[-1]

        if uname in realUsers:
            mapping[uname] = l.split()[0]

    return mapping

def filterDu(pipe, grep=None):
    mapping = {}

    for i in pipe:
        l = i.strip('\n')
        if not l:
            continue

        if grep:
            if grep not in l:
                continue

        folder = l.split('/')[-1]

        mapping[folder] = l.split()[0]

    return mapping


def du(path):
    ducmd = '/usr/bin/nice -n 19 /usr/bin/du -s %s/* 2>/dev/null'
    return os.popen(ducmd % path.rstrip('/'))

# Disk space in KB.

diskspace = {
    'home': filterUsers(du('/home')),
    'profiles': filterUsers(du('/var/lib/samba/profile')),
    'mail': filterDu(du('/var/mail'), '@'), 
    'shares': filterDu(du('/var/lib/samba/data')),
}

store = open('/usr/local/tcs/tums/rrd/dindex.nid', 'wt')
store.write(repr(diskspace))
store.close()

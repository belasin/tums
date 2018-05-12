#!/usr/bin/python

import sha, os, sys

l = open('Settings.py', 'rt')
defaults = {}
for i in l:
    p = i.split(' = ')
    defaults[p[0].strip()] = p[1].strip().replace("'", "")
l.close()

l = os.popen('head -n 55 /root/tcs/boxprep/boxprep.sh')
preps = ""
reading = True
for line in l:
    if "SERVICES" in line:
        reading = False
    if reading:
        preps += line

DDNS_ADDR=""

exec preps

server = ""
password = ""
base = ""
dom = ""
manager = ""
org = ""
installDir = ""
ident = ""
smbdom = ""
sambaDN=True

if len(sys.argv)>1:
    if sys.argv[1] == '-s':
        server = "127.0.0.1"
else:
    server = raw_input("LDAP Server [%s]: " % defaults['LDAPServer'])
    password = raw_input("Password [%s]: " % LDAPPASSWD)
    base = raw_input("Base DN (without o=) [%s]: " % LDAPBASE)
    dom = raw_input("Default Domain [%s]: " % FQD)
    manager = raw_input("Manager CN (with cn=) [%s]: " % defaults['LDAPManager'])
    #print "The LDAPIdentifier is used to determine how to uniquely compare users, it should be left as the default 'mail' unless your name is Colin Alston"
    ident = None #raw_input("Identifier [Default %s]: ")
    org = raw_input("Organisation [%s]: " % FRIENDLYNAME)
    installDir = raw_input("Install Directory [Default %s]: " % os.getcwd())
    sambaDN=True
    #sambaDN = raw_input("Is this a Samba PDC? (Answer 'True' or 'False')[Default: %s]: " % defaults['sambaDN'])
    if sambaDN: 
        smbdom = raw_input("What is the name of this PDC Domain or Workgroup? [Default %s]: " % SMBDOMAIN)

# Write our settings
if not sambaDN:
    #sambaDN = defaults['sambaDN']
    sambaDN=True
if not smbdom:
    smbdom = SMBDOMAIN
if not server:
    server = defaults['LDAPServer']
if not password:
    password = LDAPPASSWD
if not manager:
    manager = defaults['LDAPManager']
if not dom:
    dom = FQD
if not base:
    base = LDAPBASE
if not ident:
    ident = defaults['LDAPPersonIdentifier']
if not org:
    org = FRIENDLYNAME
if not installDir:
    installDir = os.getcwd()

people = 'ou=People'

l = open('Settings.py', 'wt')

print "Writing config..."
l.write('LDAPServer = ' + repr(server) + '\n')
l.write('LDAPPass = ' + repr(password) + '\n')
l.write('LDAPManager = ' + repr(manager) + '\n')
l.write('LDAPBase = ' + repr(base) + '\n')
l.write('LDAPPersonIdentifier = ' + repr(ident) + '\n')
l.write('LDAPPeople = ' + repr(people) + '\n')
l.write('LDAPOrganisation = ' + repr(org) + '\n')
l.write('BaseDir = ' + repr(installDir) + '\n')
l.write('defaultDomain = ' + repr(dom) + '\n')
if sambaDN:
    l.write('sambaDN = True\n')
else:
    l.write('sambaDN = False\n')
l.write('SMBDomain = ' + repr(smbdom) + '\n')
l.close()

def upgradeTwisted():
    print "  twisted..."
    fork = os.popen('twistd --version | grep twistd | awk \'{{{ print $5}}}\'')
    l = fork.read().strip('\n')
    if '2.4.0' in l:
        print "  Twisted seems up to date"
        return True
    else:
        print "  This requires Twisted 2.4. Please direct complaints to Gentoo who still have not updated their packages. Never fear, I shall *try* to install it"

    print "  Removing Gentoos broken twisted..."
    fork = os.popen('emerge --unmerge dev-python/twisted')
    l = fork.read()

    print "  Deleting twistd controler"
    fork = os.popen('rm /usr/bin/twistd'); l = fork.read()

    print "  Fetching new twisted"
    fork = os.popen('wget -c http://tmrc.mit.edu/mirror/twisted/Twisted/2.4/Twisted-2.4.0.tar.bz2')
    for i in fork:
        print i

    print "  Extracting..."
    fork = os.popen('tar -jxf Twisted-2.4.0.tar.bz2')
    l = fork.read()

    print "  Installing..."
    os.chdir('Twisted-2.4.0')
    fork = os.popen('python2.4 setup.py install')
    l = fork.read()

def addDeps():
    print "Installing dependencies..."
    print "  python-ldap..."
    fork = os.popen('emerge dev-python/python-ldap')
    l = fork.read()
    print "  zope-interface..."
    fork = os.popen('emerge net-zope/zopeinterface')
    l = fork.read()
    upgradeTwisted()

def writeInitd():
    print "Writing init.d script..."
    l = open('/etc/init.d/tums', 'wt')

    init = """#!/sbin/runscript
# Copyright 1999-2006 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

start() {
    ebegin "Starting Tums"
    export PYTHONPATH='%s'
    if [ ! -e /var/run/tums.pid ]; then
        /usr/bin/twistd -l /var/log/tums.log --pidfile /var/run/tums.pid -oy %s/deploy-man.py > /dev/null 2>&1
        /usr/local/tcs/exilog-tums/exilog_agent.pl > /dev/null 2>&1
    fi
    eend 0
}

stop() {
    ebegin "Stopping Tums"
    start-stop-daemon --stop --pidfile /var/run/tums.pid
    sleep 1
    if [ -e /var/run/tums.pid ]; then
        kill -9 `cat /var/run/tums.pid` > /dev/null 2>&1
        rm /var/run/tums.pid > /dev/null 2>&1
    fi
    eend 0
}

restart() {
    start-stop-daemon --stop --pidfile /var/run/tums.pid
    sleep 2
    export PYTHONPATH='%s'
    if [ ! -e /var/run/tums.pid ]; then
        /usr/bin/twistd -l /var/log/tums.log --pidfile /var/run/tums.pid -oy %s/deploy-man.py > /dev/null 2>&1
    else
        kill -9 `cat /var/run/tums.pid` > /dev/null 2>&1
        rm /var/run/tums.pid > /dev/null 2>&1
        /usr/bin/twistd -l /var/log/tums.log --pidfile /var/run/tums.pid -oy %s/deploy-man.py > /dev/null 2>&1
    fi
    eend 0
}
""" % (installDir, installDir, installDir, installDir, installDir)

    l.write(init)
    l.close()
    os.system('/usr/bin/chmod a+x /etc/init.d/tums')

    print "Updating runlevels..."
    os.system('/sbin/rc-update -a tums default')

addDeps()
writeInitd()

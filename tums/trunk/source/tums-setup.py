#!/usr/bin/python
import os, sys, subprocess

from Core import Utils

def inputBox(title, preseed = ""):
    test = "/usr/bin/dialog --inputbox \"%s\" 8 70 \"%s\" " % (title, preseed)
    l = subprocess.Popen(test, shell=True, stderr=subprocess.PIPE)
    l.wait()
    return l.stderr.read()

def questionBox(title):
    test = "/usr/bin/dialog --yesno \"%s\" 6 70" % title
    l = subprocess.Popen(test, shell=True, stderr=subprocess.PIPE)
    l.wait()
    return not l.returncode

def radioBox(title, items):
    test = 'dialog --radiolist "%s" 20 60 15 %s' % (
        title,
        ' '.join(['"%s" "%s" %s' % (i[0], i[1], j) for j,i in enumerate(items)])
    )
    l = subprocess.Popen(test, shell=True, stderr=subprocess.PIPE)
    l.wait()
    return l.stderr.read()

def textBox(text):
    l = open('/tmp/dlgtmp', 'w')
    l.write(text)
    l.close()
    test = "/usr/bin/dialog --textbox /tmp/dlgtmp 24 70" 
    l = subprocess.Popen(test, shell=True, stderr=subprocess.PIPE)
    l.wait()
    return 

startupText = """                        - Vulani Setup - 

Welcome to the Vulani setup program. This program will require 
you to enter many details pertaining to the configuration of 
your system. These options will be written to the main 
configuration file /usr/local/tcs/tums/config.py

This file can be modified later, and is altered by the TUMS web
interface.

Before continuing this installation please have the following
details.
 * Your internet DNS server
 * Your SMTP server (if any)
 * The domain name used for email delivered to this site
 * The hostname by which this machine can be accessed on the 
   internet
 * Your ADSL username and password OR the static IP details for 
   your WAN port including the default gateway
"""

textBox(startupText)

if not questionBox("Would you like to continue the installation?"):
    sys.exit()

configuring = True
setup = {
    'CompanyName':'MyCompany',
    'ExternalName':'tcs-gw.myco.co.za',
    'Hostname':'tcs',
    'Domain':'myco.co.za',
    'SambaDomain': ''
}
setup['WANDevices'] = {}
setup['LANDevices'] = {}
setup['LANPrimary'] = 'eth0'
setup['EthernetDevices'] = {
    'eth0':{
        'ip': '192.168.0.1/24',
        'type': 'static',
        'network':'192.168.0.0/24',
        'dhcpserver': True
    }   
}
setup['TCSAliases'] = ['www', 'cache', 'mail', 'smtp', 'pop3', 'imap', 'router', 'ns', 'ntp', 'server', 'gateway']
setup['ProxyAllowedHosts'] = ['127.0.0.1']   
setup['ProxyAllowedDestinations'] = ['89.202.157.0/24']   
setup['ProxyAllowedDomains'] = ['.windowsupdate.com','.eset.com','.sophos.com','.microsoft.com','.adobe.com','.symantecliveupdate.com','.symantec.com','.veritas.com']   

setup['Tunnel'] = {}

setup['SambaConfig'] = {
    'domain logons': 'no',
    'smb ports': '139',
    'logon path': '\\\\%L\\Profiles\\%U',
    'logon drive': 'H:',
    'os level': '33',
    'local master': 'yes',
    'time server': 'yes',
    'wins support': 'yes',
    'preferred master': 'yes',
    ';logon script': 'STARTUP.BAT',
    'domain master': 'no',
    'logon home': '\\\\%L\\%U'
}   

setup['SambaShares'] = {
    'homes': {
        'writable': 'yes',
        'browseable': 'no',
        'comment': 'Home Directories',
        'directory mode': '700',
        'create mode': '600',
        'nt acl support':'yes'
    },  
    'Public': {
        'comment': 'Public Stuff',
        'writeable': 'yes',
        'printable': 'no',
        'create mode': '664',
        'path': '/var/lib/samba/data/public',
        'directory mode': '775',
        'nt acl support':'yes',
        'public': 'yes'
    },
    'Profiles':{
        'comment' : 'Windows Profile Path',
        'path' : '/var/lib/samba/profiles',
        'guest ok' : 'yes',
        'read only': 'no',
        'create mask': '0660',
        'directory mask': '0770',
        'profile acls': 'yes'
    },
    'Netlogon':{
        'comment': 'Network Logon Service',
        'path': '/var/lib/samba/netlogon',
        'guest ok': 'yes',
        'read only': 'yes',
        'write list': '@Administrator'
    },
    'Printers':{
        'comment' : 'All Printers',
        'path' : '/var/lib/samba/printers',
        'browseable' : 'no',
        'public' : 'yes',
        'guest ok' : 'yes',
        'writable' : 'no',
        'printable' : 'yes',
    }
}
setup['ProxyConfig'] = {
    'type': 'open',
    'adauth': False,
    'addom': '',
    'adserver': ''
}

setup['Mail'] = {
    'blockedfiles': [],
    'mailsize': '100M',
    'hubbed': [],
    'relay': []
}

setup['Shaping'] = {}

setup['DHCP'] = {
    'leases': {}
}

setup['General'] = {
    'aptrepo':[
        'deb http://debian.vulani.net/debian/ etch main',
        'deb http://debian.mirror.ac.za/debian/ etch main',
        'deb http://security.debian.org/ etch/updates main contrib',
        'deb-src http://security.debian.org/ etch/updates main contrib',
        'deb http://volatile.debian.org/debian-volatile etch/volatile main contrib non-free'
    ]
}

setup['Shorewall'] = { 
    'zones': {
        'loc': {
            'policy': 'ACCEPT',
            'interfaces': [
                'eth0 detect dhcp,routeback'
            ],
            'log': ''
        },
        'net': {
            'policy': 'DROP',
            'interfaces':[
                'eth1 detect'
            ],
            'log':'$LOG'
        }
    },
    'rules': [
        [1, 'Ping/ACCEPT       all      all'],
        [1, 'AllowICMPs        all      all'],
        [1, 'ACCEPT            all      all    udp        33434:33463'],
        [1,'ACCEPT net:196.211.242.160/29 all'],
        [1,'ACCEPT net:196.212.55.128/29 all'],
        [1,'ACCEPT net:74.53.87.72/29 all'],
        [1,'ACCEPT net        all      tcp     25'],
        [1,'ACCEPT net        all      tcp     80'],
        [1,'ACCEPT net        all      tcp     443'],
        [1,'ACCEPT net        all      tcp     143'],
        [1,'ACCEPT net        all      tcp     110'],
        [1,'ACCEPT net        all      udp     1194'],
        [1,'ACCEPT net        all      tcp     21'],
    ],
    'masq': {}
}

def getOption(tagName, description, setups = setup, required = True):
    setups[tagName]    = inputBox(description, setups.get(tagName,''))
    if required:
        while not setups.get(tagName,'').strip():
            setups[tagName]    = inputBox(description, setups.get(tagName,''))

LICKEY = ""

while (configuring):
    # Initial stuff
    getOption('CompanyName', 'Company Name (Required)')
    getOption('ExternalName', 'External Hostname (Required)')
    getOption('Hostname', 'Hostname (Required)')
    getOption('Domain', 'Domain Name (Required)')
    if not setup['SambaDomain']:
        setup['SambaDomain'] = setup['Domain'].split('.')[0].upper()
    getOption('SambaDomain', 'Windows Domain name (Required)')
    
    setup['LDAPBase']   = setup['SambaDomain']
    setup['LDAPPassword'] = setup['SambaDomain'].lower()

    if 'thusadns.com' in setup['ExternalName']:
        host = setup['ExternalName'].split('.')[0]
        setup['ThusaDNSUsername'] = host
        setup['ThusaDNSPassword'] = host+'123'
        setup['ThusaDNSAddress'] = setup['ExternalName']
    else:
        setup['ThusaDNSUsername'] = ''
        setup['ThusaDNSPassword'] = ''
        setup['ThusaDNSAddress'] = ''

    setup['NTP'] = '196.4.160.4'
    setup['SMTPRelay'] = 'smtp.isdsl.net'
    getOption('NTP', 'Network time server')
    getOption('SMTPRelay', 'SMTP Relay server (optional)', required=False)

    getOption('ForwardingNameservers', 'DNS Servers. Separate multiple entries with commas')

    lanType = ""
    while not lanType:
        lanType = radioBox('LAN Connection (required)', [
            ('DHCP', 'DHCP'),
            ('Static', 'Static IP address')
        ])

    # Network setups
    netType = ""
    while not netType:
        netType = radioBox('Internet connection (required)', [
            ('Static', 'Static IP address on WAN port'), 
            ('PPPoE', 'PPPoE connection on WAN port'),
            ('LAN', 'This installation has no WAN port, the LAN is used')
        ])
    
    if netType == "PPPoE":
        if not setup['WANDevices'].get('ppp0', None):
            setup['WANDevices'] = {
                'ppp0':{
                    'pppd':['defaultroute'],
                    'username':'',
                    'password':'',
                    'link': 'eth1',
                    'plugins':'pppoe'
                }
            }
        setup['WANPrimary'] = 'ppp0'
        getOption('username', 'PPPoE Username', setup['WANDevices']['ppp0'])
        getOption('password', 'PPPoE Password', setup['WANDevices']['ppp0'])
        setup['Shorewall']['masq'] = {'ppp0':['eth0']}
        setup['Shorewall']['zones']['net']['interfaces'] = ['ppp0 detect']

    if netType == "Static":
        setup['WANDevices'] = {}
        setup['LANDevices'] = {}

        if not setup['EthernetDevices'].get('eth1', None):
            setup['EthernetDevices']['eth1'] = {
                'ip': '196.211.1.2/29',
                'type': 'static',
                'network':'',
                'gateway':'196.211.1.1'
            }
        
        getOption('ip', 'WAN IP Address in CIDR format', setup['EthernetDevices']['eth1'])
        getOption('gateway', 'WAN Gateway', setup['EthernetDevices']['eth1'])

        gateway = setup['EthernetDevices']['eth1']['gateway']

        setup['EthernetDevices']['eth1']['routes'] = [('default', gateway)]

        setup['EthernetDevices']['eth1']['network'] = Utils.getNetwork(setup['EthernetDevices']['eth1']['ip'])
        setup['WANPrimary'] = 'eth1'
        setup['Shorewall']['masq'] = {'eth1':['eth0']}
        setup['Shorewall']['zones']['net']['interfaces'] = ['eth1 detect']

    if lanType == 'Static':
        getOption('ip', 'LAN IP Address in CIDR format', setup['EthernetDevices']['eth0'])
        setup['EthernetDevices']['eth0']['network'] = Utils.getNetwork(setup['EthernetDevices']['eth0']['ip'])
    else:
        setup['EthernetDevices']['eth0'] = {
            'type':'dhcp',
            'network': '192.168.0.0/24',
            'dhcpserver': False
        }
        getOption('network', 'Network address to which this server is attached', 
            setup['EthernetDevices']['eth0'])

    if netType == "LAN":
        setup['WANPrimary'] = 'eth0'
        setup['Shorewall']['masq'] = {}

        setup['Shorewall']['rules'] = [
            [1, 'Ping/ACCEPT       all      all'],
            [1, 'AllowICMPs        all      all'],
        ]

        del setup['Shorewall']['zones']['net']
        
        if lanType == 'Static':
            getOption('gateway', 'Gateway', setup['EthernetDevices']['eth0'])

    if questionBox("Do you want to require Web Proxy authentication?"):
        ProxyAuth = True
    else:
        ProxyAuth = False

    if questionBox("Should this server act as a Primary Domain Controller?"):
        PDC = True
    else:
        PDC = False

    while not LICKEY:
        LICKEY = inputBox("Enter license key", "")

    if questionBox("Is the information correct?"):
        # Stop configuring
        configuring = False
# Shorewall
setup['Shorewall']['rules'].append([1, 'REDIRECT loc      8080     tcp     80      -     !%s' % setup['EthernetDevices']['eth0']['network']])
setup['Shorewall']['rules'].append([1, 'REDIRECT loc      25       tcp     25      -     !%s' % setup['EthernetDevices']['eth0']['network']])
setup['LocalDomains'] = [setup['Domain']]
setup['ForwardingNameservers'] = setup['ForwardingNameservers'].split(',')

if setup['Hostname'] != "tcs":
    setup['TCSAliases'].append('tcs')

if ProxyAuth:
    # Enable proxy auth scenario - Firewall external web traffic and don't add the range to allowed hosts
    setup['Shorewall']['rules'].append([1, 'REJECT   loc   net   tcp  80'])

else:
    # Standard transparent proxy
    # Add lan network to allowed hosts
    setup['ProxyAllowedHosts'].append(setup['EthernetDevices']['eth0']['network'])

if PDC:
    # Enable Samba PDC
    setup['SambaConfig']['domain logons'] = 'yes'
    setup['SambaConfig']['domain master'] = 'yes'

try:
    del setup['EthernetDevices']['eth1']['gateway']
except:
    pass


l = open('/usr/local/tcs/tums/config.py', 'w')
for k,val in setup.items():
    l.write('%s = %s\n' % (k, repr(val)))

l.close()
l = open('/usr/local/tcs/tums/keyfil', 'w')
l.write(LICKEY+'\n')
l.close()

os.system('mkdir -p /var/lib/samba/data/public')
os.system('mkdir /usr/local/tcs/tums/profiles')
os.system('cp /usr/local/tcs/tums/config.py /usr/local/tcs/tums/profiles/default.py')
os.system('echo default.py > /usr/local/tcs/tums/runningProfile')
os.system('echo default.py > /usr/local/tcs/tums/currentProfile')
os.system('/usr/local/tcs/tums/configurator --upgrade')
os.system('cd /usr/local/tcs/tums; /usr/local/tcs/tums/configurator --upgrade')
os.system('clear')
os.system('rm /usr/local/tcs/tums/*.pyc') # Get rid of this crap
os.system('echo > /usr/local/tcs/tums/packages/set')
print "Your configuration has been written to /usr/local/tcs/tums/config.py and as a profile"
print "If you wish to alter this file, please make a note to copy it back to /usr/local/tcs/tums/profiles/default.py"
print "To configure your system according to this configuration file run:"
print "   cd /usr/local/tcs/tums"
print "   ./configurator -D"


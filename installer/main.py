#!/usr/bin/python
import sys

sys.path.append('/home/installer/')

from enamel import authentication, deployment, pages, servers, storage, deferreds, tags
from enamel import sql
import enamel

from pages import Index


class Enameltuminstall(enamel.Enamel):
    """ tuminstall Enamel class """

    indexPage = Index.Page
    loginPage = pages.Login
    
    anonymousAccess = True

    server = servers.TwistedWeb
    port = 8010

    setup = {
        # Test data
        'mountpoints': {
            '/': 'md0', 
        }, 
        'raidsets': {
            'md0': ['sda2', 'sdb2']
        }, 
        'nets': {}
    }

    def __init__(self, *a, **kw):
        enamel.Enamel.__init__(self, *a, **kw) 

        setup = {
            'CompanyName':'MyCompany',
            'ExternalName':'tcs-gw.myco.co.za',
            'Hostname':'tcs',
            'Domain':'myco.co.za',
            'SambaDomain': '',
            'ThusaDNSUsername':'',
            'ThusaDNSPassword':'',
            'ThusaDNSAddress':''
        }
        setup['WANDevices'] = {}
        setup['LANDevices'] = {}
        setup['LANPrimary'] = ['eth0']
        setup['EthernetDevices'] = {
            'eth0':{
                'ip': '192.168.0.1/24',
                'type': 'static',
                'network':'192.168.0.0/24'
            }
        }
        setup['TCSAliases'] = ['vulani']
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
            'logon script': 'STARTUP.BAT',
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
                'deb http://debian.vulani.net/debian/ lenny main',
                'deb http://ftp.debian.org/debian/ lenny main',
                'deb http://security.debian.org/ lenny/updates main contrib',
                'deb-src http://security.debian.org/ lenny/updates main contrib',
                'deb http://volatile.debian.org/debian-volatile lenny/volatile main contrib non-free'
            ]
        }
        setup['ShorewallBalance'] = []
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

        self.config = setup

EnameltuminstallInstance = Enameltuminstall()
deployment.run('tuminstall', [EnameltuminstallInstance], pidLoc = "/home/installer/")

import config, os

class Plugin(object):
    parameterHook = "--readboxprep"
    parameterArgs = " <Boxprep File>"
    parameterDescription = """Create a config file from a boxprep file
                          and output to stdout."""
    configFiles = [ 
    ]

    autoRun = False

    def reloadServices(self):
        pass
    def writeConfig(self, file, *a):
        l = open(file)
        stop = False
        config = []
        for i in l:
            line = i.strip('\n').strip()
            if line and not stop and line[0]!="#":
                if "SERVICES=" in line or "filelist" in line:
                    stop = True
                else:
                    config.append(line)

        boxprep = "\n".join(config)
        exec boxprep

        LOCALDOMS = ", ".join([ '"%s"' % i for i in open('/etc/exim/local_domains').read().strip('\n').split('\n')])

        basicConfig = """
CompanyName = "%s"
Hostname = "%s"
Domain = "%s"
SambaDomain = "%s"
LDAPBase = "%s"
LDAPPassword = "%s"
ExternalName = "%s.%s"
EthernetDevices = {
    "eth0": {
        "type"     : "static",
        "network"  : "192.168.0.0/24",
        "ip"       : "192.168.0.0/24",
    },
}
LANPrimary = "eth0"
WANDevices = {
    "ppp0": {
        "link"   : "%s",
        "plugins" : "pppoe",
        "pppd"   : ["defaultroute"],
        "username" : "%s",
        "password" : "%s"
    },
}
WANPrimary = "ppp0"
ThusaDNSUsername = "%s"
ThusaDNSPassword = "%s"
ThusaDNSAddress  = "%s"

# DNS
ForwardingNameservers = %s
TCSAliases = ['www', 'cache', 'mail', 'smtp', 'pop3', 'imap', 'router', 'ns', 'ntp', 'server', 'gateway']

# Network Time
NTP = "196.4.160.4"

# Email and SMTP
SMTPRelay = "%s"
LocalDomains = ["%%s.%%s" %% (Hostname, Domain), %s]

# Gentoo portage settings
GentooMirrors = [
    "ftp://ftp.is.co.za/linux/distributions/gentoo"
]

GentooRsync = ""
OverlayRsync = "rsync://portage.thusa.net/thusa-portage"

ProxyConfig = {
    'type' : 'closed'
}

ProxyAllowedHosts = [
    '127.0.0.1',
]

ProxyAllowedDestinations = [
    '89.202.157.0/24',
]
ProxyAllowedDomains = [
    '.windowsupdate.com',
    '.eset.com',
    '.sophos.com',
    '.microsoft.com',
    '.adobe.com',
    '.symantecliveupdate.com',
    '.symantec.com',
    '.veritas.com',
]

SambaShares = {
    'homes':{
        'writable':'yes',
        'directory mode':'700',
        'create mode':'600',
        'browseable':'no',
        'comment': 'Home Directories',
    },
    'Public':{
        'comment' : 'Public Stuff',
        'create mode' : '664',
        'public' : 'yes',
        'writeable' : 'yes',
        'directory mode' : '775',
        'path' : '/var/lib/samba/data/public',
        'printable' : 'no',
    },
    'Tools':{
        'comment' : 'Tools',
        'create mode' : '664',
        'public' : 'yes',
        'writeable' : 'yes',
        'directory mode' : '775',
        'path' : '/var/lib/samba/data/tools',
        'printable' : 'no'
    },
}
SambaConfig = {
    'smb ports' : '139',
    'preferred master' : 'yes',
    'domain master' : 'no',
    'local master' : 'yes',
    'domain logons' : 'no',
    'os level' : '33',
    'wins support' : 'yes',
    'time server' : 'yes',

    'logon path' : '\\%%L\Profiles\%%U',
    'logon drive' : 'H:',
    'logon home' : '\\%%L\%%U',
    ';logon script' : 'STARTUP.BAT',
}

Shaping = {
}
ShaperRules =  []

Shorewall = {
    'rules' : [
        [1, "Ping/ACCEPT       all      all"],
        [1, "AllowICMPs        all      all"],
        [0, "REDIRECT loc      8080     tcp     80      -     !192.168.0.0/24"],
        [0, "REDIRECT loc      25       tcp     25      -     !192.168.0.0/24"],
        [1, "ACCEPT net:196.211.242.160/29 all"],
    ],
    'zones' : {
        'loc':{
            'interfaces': ['eth0 detect dhcp'],
            'policy' : 'ACCEPT',
            'log' : '',
        },
        'net':{
            'interfaces': ['ppp0'],
            'policy': 'DROP',
            'log': '',
            },
            'vpn0':{
                'interfaces': ['tap0 detect'],
                'policy' : 'ACCEPT',
                'log' : '',
            },
        },
    'masq' : {
        'ppp0': ['eth0']
    },
}
# You must edit this config before using it
""" % (
    FRIENDLYNAME,
        HOSTNAME,
        FQD,
        SMBDOMAIN,
        LDAPBASE,
        LDAPPASSWD,
        HOSTNAME,
        FQD,
        NET_DEV,
        ADSL_USERNAME,
        ADSL_PASSWORD,
        DDNS_USER,
        DDNS_PASS,
        DDNS_ADDR,
        repr(NSFORWARD.strip('\;').split('\;')),
        SMTPRELAY,
        LOCALDOMS
    )
        print basicConfig



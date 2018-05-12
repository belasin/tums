# Customer details
CompanyName = "Thusa Business Support"
Hostname = "lilith"
Domain = "thusa.co.za"
ExternalName = "lilith.thusa.net"

# Samba Settings
SambaDomain = "LILITH"

# LDAP Settings
LDAPBase = "TRYPTOPHAN"
LDAPPassword = "wsthusa"

# Ethernet Settings
EthernetDevices = {
    "eth0": {
        "type"     : "dhcp",
        "network"  : "172.31.0.0/24",
        "ip"       : "172.31.0.212/24",
        "aliases"  : [],
    },
    
    "eth1": {
        "type"     : "static", 
        "ip"       : "172.31.5.1/24",
        "network"  : "172.31.5.0/24",
        "aliases"  : ["172.19.255.98/29", "192.168.0.22/24"], 
    }
}
LANPrimary = "eth0"

WANDevices = {
    "ppp0": {
        "link"   : "eth1",
        "plugins" : "pppoe", 
        "pppd"   : ["defaultroute"], 
        "username" : "isp00000@dsl512.isdsl.net",
        "password" : "password123"
    },
    "ppp1": { 
        "username" : ":)",
        "password" : ":P",
        "pppd" : [
            "persist",
            "remotename pptp-is-router",
            "ipparam adsl",
            "lock",
            "noauth",
            "nobsdcomp",
            "nodeflate",
          ],
        "link" : "pty \"pptp 196.35.66.114 --nolaunchpppd\"",
    }
}
WANPrimary = "ppp0" 

# Dynamic DNS
ThusaDNSUsername = "newdom"
ThusaDNSPassword = "newdompass"
ThusaDNSAddress  = "newdom.thusadns.com"

# DNS
ForwardingNameservers = ["196.14.239.2", "168.210.2.2"]
TCSAliases = ['www', 'cache', 'mail', 'smtp', 'pop3', 'imap', 'router', 'ns', 'ntp', 'server', 'gateway'] 

# Network Time 
NTP = "196.4.160.4"

# Email and SMTP
SMTPRelay = "smtp.isdsl.net"
LocalDomains = ["%s.%s" % (Hostname, Domain), "thusa.co.za"] 

# Gentoo portage settings
GentooMirrors = [
    "http://siza.thusa.net/gentoo",
    "ftp://ftp.is.co.za/linux/distributions/gentoo",
    "http://ftp.up.ac.za/mirrors/gentoo.org/gentoo"
]

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

    'logon path' : '\\%L\Profiles\%U',
    'logon drive' : 'H:',
    'logon home' : '\\%L\%U',
    ';logon script' : 'STARTUP.BAT',
}

GentooRsync = ""
OverlayRsync = "rsync://portage.thusa.net/thusa-portage"

Shaping = {
    'eth1': {
        'ratein':'6400kbit',
        'rateout':'6400kbit',
        'classes':[
            ["1", "6000kbit", "6200kbit", "1", "default,"],
        ],
    },
}
ShaperRules =  []


Shorewall = {
    'rules' : [
        [1, "Ping/ACCEPT       all      all"],
        [1, "AllowICMPs        all      all"],
        [0, "REDIRECT loc      8080     tcp     80      -     !172.31.0.0/24"],
        [0, "REDIRECT loc      25       tcp     25      -     !172.31.0.0/24"],
        [1, "ACCEPT net:196.211.242.160/29 all"],
        [1, "ACCEPT dwc:172.19.255.50 all"],
        [1, "ACCEPT dwc        all      tcp     80"],
        [1, "ACCEPT dwc        all      tcp     1194"],
        [0, "ACCEPT net        all      tcp     20"],
        [0, "ACCEPT net        all      tcp     21"],
        [0, "ACCEPT net        all      tcp     22"],
        [0, "ACCEPT net        all      tcp     80"],
        [0, "ACCEPT net        all      tcp     443"],
        [0, "ACCEPT net        all      tcp     25"],
        [0, "ACCEPT net        all      tcp     110"],
        [0, "ACCEPT net        all      tcp     143"],
        [0, "ACCEPT net        all      tcp     873"],
        [0, "ACCEPT net        all      udp     873"],
        [0, "ACCEPT all        all      udp     1194"],
        [0, "ACCEPT all        all      udp     5000"],
        [0, "ACCEPT net        all      udp     4569"],
        [0, "ACCEPT net        all      udp     5060"],
        [0, "ACCEPT net        all      udp     10000:20000"],
        [0, "DNAT   net:196.211.242.160/29 loc:172.31.0.3 tcp 3389"]
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
        'dwc':{
            'interfaces':['eth1 detect'],
            'policy': 'DROP',
            'log':'$LOG'
        },
        'vpn0':{
            'interfaces': ['tap0 detect'],
            'policy' : 'ACCEPT',
            'log' : '',
        },
    },
    'masq' : {
        'eth1': ['eth0']
    },
}
ShorewallBalance = [
#    ['net', 'detect', 'track'],
#    ['net2', '192.168.152.231', 'track']
]
ShorewallSourceRoutes = [
#    ["172.69.1.164", "net"],
#    ["172.69.1.2", "net", 10003]
]


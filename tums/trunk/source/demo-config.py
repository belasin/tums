# Customer details
CompanyName = "Thusa Business Support"
Hostname = "lilith"
Domain = "bulwer.thusa.net"

# Samba Settings
SambaDomain = "LILITH"

# LDAP Settings
LDAPBase = "LILITH"
LDAPPassword = "2salilith"

# Ethernet Settings
EthernetDevices = {
    "eth0": {
        "type"     : "dhcp",
        "network"  : "172.31.0.0/24",
        "ip"       : "172.31.0.212/24",
    },
    
    "eth1": {
        "type"     : "static", 
        "ip"       : "172.31.0.212/24",
        "network"  : "172.31.0.0/24"
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

GentooRsync = ""
OverlayRsync = "rsync://portage.thusa.net/thusa-portage"


# Horrible messy stuff 
CustomFiles = [
    {
        'files'    : [
            ('shorewall-rules', '/etc/shorewall/rules'),
        ],
        'replacers': [
            ('ACCEPT', 'DENY'),
            ('test.co.za', Domain),
            ('#MARK#', """
blah
blah blha
blha"""), 
        ]
    },
]

CustomPackages = [
    "="
]


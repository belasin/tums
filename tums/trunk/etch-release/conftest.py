LDAPBase = 'LILITH'
LANPrimary = 'eth0'
ForwardingNameservers = [
    '196.14.239.2','168.210.2.2'
]

ThusaDNSAddress = 'newdom.thusadns.com'
LocalDomains = [
    'lilith.bulwer.thusa.net','thusa.co.za'
]

ShorewallSourceRoutes = [
    [
        '172.69.1.164','net'
    ],
    [
        '172.69.1.2','net',10003
    ]
    
]

ThusaDNSPassword = 'newdompass'
ShorewallBalance = [
    [
        'net','detect','track'
    ],
    [
        'net2','192.168.152.231','track'
    ]
    
]

WANDevices = {
    'ppp0': {
        'pppd': [
            'defaultroute'
        ],
        'username': 'isp00000@dsl512.isdsl.net',
        'password': 'password123',
        'link': 'eth1',
        'plugins': 'pppoe'
    },
    'ppp1': {
        'username': ':)',
        'pppd': [
            'persist','remotename pptp-is-router','ipparam adsl','lock','noauth','nobsdcomp','nodeflate'
        ],
        'password': ':P',
        'link': 'pty "pptp 196.35.66.114 --nolaunchpppd"'
    }
    
}

WANPrimary = 'ppp0'
TCSAliases = [
    'www','cache','mail','smtp','pop3','imap','router','ns','ntp','server','gateway'
]

Hostname = 'lilith'
LDAPPasswrd = '2salilith'
GentooMirrors = [
    'http://siza.thusa.net/gentoo',
    'ftp://ftp.is.co.za/linux/distributions/gentoo',
    'http://ftp.up.ac.za/mirrors/gentoo.org/gentoo'
]

SMTPRelay = 'smtp.isdsl.net'
EthernetDevices = {
    'eth1': {
        'ip': '172.31.0.212/24',
        'type': 'static',
        'network': '172.31.0.0/24'
    },
    'eth0': {
        'ip': '172.31.0.212/24',
        'type': 'dhcp',
        'network': '172.31.0.0/24'
    }
    
}

ThusaDNSUsername = 'newdom'
OverlayRsync = 'rsync://portage.thusa.net/thusa-portage'
Domain = 'testo.co.zo'
CompanyName = 'Thusa Business Support'
NTP = '196.4.160.4'
GentooRsync = ''
SambaDomain = 'LILITH'
Shorewall = {
    'rules': [
        [
            1,'Ping/ACCEPT       all      all'
        ],
        [
            1,'AllowICMPs        all      all'
        ],
        [
            1,'REDIRECT loc      8080     tcp     80      -     !172.31.0.0/24'
        ],
        [
            1,'REDIRECT loc      25       tcp     25      -     !172.31.0.0/24'
        ],
        [
            1,
            'ACCEPT net:196.211.242.160/29 all'
        ],
        [
            0,'ACCEPT net        all      tcp     20'
        ],
        [
            0,'ACCEPT net        all      tcp     21'
        ],
        [
            0,'ACCEPT net        all      tcp     22'
        ],
        [
            1,'ACCEPT net        all      tcp     80'
        ],
        [
            0,'ACCEPT net        all      tcp     443'
        ],
        [
            1,'ACCEPT net        all      tcp     25'
        ],
        [
            0,'ACCEPT net        all      tcp     110'
        ],
        [
            0,'ACCEPT net        all      tcp     143'
        ],
        [
            0,'ACCEPT net        all      tcp     873'
        ],
        [
            0,'ACCEPT net        all      udp     873'
        ],
        [
            0,'ACCEPT all        all      udp     1194'
        ],
        [
            0,'ACCEPT all        all      udp     5000'
        ],
        [
            0,'ACCEPT net        all      udp     4569'
        ],
        [
            0,'ACCEPT net        all      udp     5060'
        ],
        [
            0,
            'ACCEPT net        all      udp     10000:20000'
        ],
        [
            0,
            'DNAT   net:196.211.242.160/29 loc:172.31.0.3 tcp 3389'
        ]
        
    ],
    'zones': {
        'loc': {
            'policy': 'ACCEPT',
            'interfaces': [
                'eth0 detect dhcp'
            ],
            'log': ''
        },
        'net': {
            'policy': 'DROP',
            'interfaces': [
                'ppp0'
            ],
            'log': 'info'
        },
        'vpn0': {
            'policy': 'ACCEPT',
            'interfaces': [
                'tap0 detect'
            ],
            'log': ''
        }
        
    },
    'masq': {
        'ppp0': [
            'eth0','tap0'
        ]
        
    }
    
}




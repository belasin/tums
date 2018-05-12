CompanyName = 'Thusa'

ExternalName = 'lilith.thusa.net'

Hostname = 'lilith'

Domain = 'bulwer.thusa.net'

SambaDomain = 'TRYPTOPHAN'

LDAPBase = 'TRYPTOPHAN'

LDAPPassword = 'wsthusa'

EthernetDevices = {'eth0': {'ip': '172.31.0.212/24', 'type': 'static', 'network': '172.31.0/24'},
 'eth1': {'type': 'dhcp', 'network': '172.31.0.0/24'}}

LANPrimary = 'eth0'

WANDevices = {}

WANPrimary = 'eth0'

ThusaDNSUsername = ''

ThusaDNSPassword = ''

ThusaDNSAddress = ''

ForwardingNameservers = ['172.31.0.1', '172.31.0.2']

TCSAliases = ['www',
 'cache',
 'mail',
 'smtp',
 'pop3',
 'imap',
 'router',
 'ns',
 'ntp',
 'server',
 'gateway']

NTP = '196.4.160.4'

SMTPRelay = '172.31.0.1'

LocalDomains = ['foo.net', 'testdom.com']

GentooMirrors = ['http://gentoo.mirror.ac.za/',
 'ftp://ftp.is.co.za/linux/distributions/gentoo',
 'http://ftp.up.ac.za/mirrors/gentoo.org/gentoo']

GentooRsync = ''

OverlayRsync = 'rsync://portage.thusa.net/thusa-portage'

Shorewall = {'qos': [(u'123', u'udp', '16'), ('1234', 'tcp', '8')],
 'rules': [[1, 'ACCEPT   test:172.31.0.1   all'],
           [1, 'ACCEPT   test     all     udp    1994   -    192.157.123.2'],
           [1, 'DNAT    net    loc:172.31.0.2:24    tcp      24    -   '],
           [1, 'REDIRECT  loc:172.31.0.0   3123 tcp  8080 - 172.31.0.212'],
           [1, 'ACCEPT   test:172.31.0.1   all'],
           [1, 'ACCEPT   test     all     udp    1994   -    192.157.123.2'],
           [1, 'DNAT    net    loc:172.31.0.2:24    tcp      24    -   '],
           [1, 'REDIRECT  loc:172.31.0.0   3123   tcp 8080  -  172.31.0.212'],
           [1,
            'DNAT    net     loc:172.31.0.23  47      -       -               196.211.202.165'],
           [1,
            'DNAT    net     loc:172.31.0.23  tcp     1723    -               196.211.202.165']],
 'zones': {'test': {'policy': 'ACCEPT', 'interfaces': [], 'log': ''}}}

ShorewallBalance = []

ShorewallSourceRoutes = []

SambaConfig = {}

SambaShares = {}

ProxyConfig = {'adauth': False,
 'timedaccess': {'test': {'allow': True,
                          'authenticate': True,
                          'days': 'MTWHF',
                          'sites': ['facebook.com'],
                          'timefrom': '08:30',
                          'timeto': '16:30'}}}

ProxyAllowedHosts = ['192.168.153.2']

ProxyAllowedDestinations = ['192.168.153.2']

ProxyAllowedDomains = ['test.com']

ProxyBlockedDomains = ['.vtunnel.com', '.votebigbird.com']

Mail = {'blockedfiles': [],
 'copytoall': '',
 'greylisting': True,
 'hubbed': [['foo.com', '172.31.0.2']],
 'mailsize': '10M',
 'relay': ['foo.org'],
 'spamscore': '70'}

Shaping = {}

ShaperRules = []

DHCP = {}

LocalRoute = ''

Failover = {}

Tunnel = {}

BGP = {'65501': {'neighbors': {'172.31.0.222': {}},
           'networks': ['172.31.0.0/24'],
           'router-id': '172.31.0.212'}}

FTP = {'globals': ['colin']}

RADIUS = {}


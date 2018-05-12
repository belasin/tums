from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP
from Core import PageHelpers, AuthApacheProxy, Utils
from Pages import Tools
import formal

class Page(PageHelpers.DefaultPage):
    addSlash = True
    docFactory  = loaders.xmlfile('blank.xml', templateDir=Settings.BaseDir+'/templates')
    config = {}

    def __init__(self, id=1, config={}):
        PageHelpers.DefaultPage.__init__(self)
        self.id = id
        self.config = config

    # Wizzard 1 - Server Identification
    def form_wizard1(self, data):
        form = formal.Form()
        form.addField('company', formal.String(), label = "Company Name")
        form.addField('hostname', formal.String(), label = "Hostname")
        form.addField('domain', formal.String(), label = "Domain name")
        form.addField('bigname', formal.String(), label = "Domain/Base", description="Company name in capitals usualy")
        form.addField('external', formal.String(), label = "External Hostname")
        form.addAction(self.submitWiz1)
        
        form.data = self.config

        return form

    def render_wizard1(self, ctx, data):
        return ctx.tag[
            tags.directive('form wizard1')
        ]

    def submitWiz1(self, c, f, data):
        for k,v in data.items():
            self.config[k] = v
        return url.root.child('Wizard').child(str(self.id+1))

    # Wizzard 2 - Network type

    def form_wizard2(self, data):
        form = formal.Form()
        form.addField('lanppp', formal.Boolean(), label = "2 LAN, 1 PPP", description="Two lan interfaces with an ADSL connection established on one of them")
        form.addField('lanwan', formal.Boolean(), label = "1 LAN, 1 WAN", description="One lan interface, and one interface with a direct WAN connection (Like IS Business DSL or diginet)")
        #form.addField('lanwanppp', formal.Boolean(), label = "2LAN, 1 PPP, 1 WAN", description="Two lan interfaces with internet balanced over an ADSL PPPoE as well as the WAN port")
        form.addAction(self.submitWiz2)
        form.data = self.config
        return form

    def render_wizard2(self, ctx, data):
        return ctx.tag[
            tags.directive('form wizard2'),
            tags.p["This is an initial layout. If your configuration is more complicated, simply chose the most relevant layout to create an initial configuration. After this you may modify the configuration from TUMS."]
        ]

    def submitWiz2(self, c, f, data):
        for k,v in data.items():
            self.config[k] = v
        return url.root.child('Wizard').child(str(self.id+1))

    # Wizzard 3 - LAN Interface
    def form_wizard3(self, data):
        form = formal.Form()
        form.addField('laninterface', formal.String(), label = "LAN Interface", description="ie eth0")
        form.addField('lanip', formal.String(), label = "LAN IP Address")
        form.addField('lannetwork', formal.String(), label = "LAN Network range")
        form.addField('dnsserv', formal.String(), label = "DNS Servers")
        form.addField('ntpserv', formal.String(), label = "NTP Server")
        
        if 'laninterface' in self.config:
            form.data = self.config

        else:
            form.data['laninterface'] = "eth0"
            form.data['lanip'] = "192.168.0.1/24"
            form.data['lannetwork'] = "192.168.0.0/24"

            form.data['dnsserv'] = '196.14.239.2, 168.210.2.2'
            form.data['ntpserv'] = '196.4.160.4'

        form.addAction(self.submitWiz3)
        return form

    def render_wizard3(self, ctx, data):
        return ctx.tag[tags.directive('form wizard3')]

    def submitWiz3(self, c, f, data):
        for k,v in data.items():
            self.config[k] = v

        if not '/' in data['lanip']:
            self.config['lanip'] = "%s/24" % data['lanip']

        if not data['lannetwork']:
            self.config['lannetwork'] = Utils.getNetwork(self.config['lanip'])

        return url.root.child('Wizard').child(str(self.id+1))

    # Wizzard 4 - ADSL Interface
    def form_wizard4(self, data):
        form = formal.Form()

        form.addField('adslinterface', formal.String(), label = "ADSL PPPoE Inteface")
        form.addField('adslusername', formal.String(), label = "ADSL Username")
        form.addField('adslpassword', formal.String(), label = "ADSL Password")

        if 'adslinterface' in self.config:
            form.data = self.config
        else:
            form.data['adslinterface'] = "eth1"

        form.addAction(self.submitWiz4)
        return form

    def render_wizard4(self, ctx, data):
        return ctx.tag[tags.directive('form wizard4')]

    def submitWiz4(self, c, f, data):
        for k,v in data.items():
            self.config[k] = v
        return url.root.child('Wizard').child(str(self.id+1))
       
    # Wizzard 5
    def form_wizard5(self, data):
        form = formal.Form()
        form.addField('waninterface', formal.String(), label = "WAN Port interface")
        form.addField('wanip', formal.String(), label = "WAN IP")
        form.addField('wanbaserate', formal.String(), label = "Basic Rate (in kb/s)")
        if 'waninterface' in self.config:
            form.data = self.config
        else:
            form.data['waninterface'] = "eth0"
            form.data['wanbaserate'] = "512"
        form.addAction(self.submitWiz5)
        return form

    def render_wizard5(self, ctx, data):
        return ctx.tag[tags.directive('form wizard5')]

    def submitWiz5(self, c, f, data):
        for k,v in data.items():
            self.config[k] = v

        if not '/' in data['wanip']:
            self.config['wanip'] = "%s/29" % data['wanip']

        return url.root.child('Wizard').child(str(self.id+1))

    # Wizzard 6
    def form_wizard6(self, data):
        form = formal.Form()
        form.addField('transproxy', formal.Boolean(), label = "Transparent Proxy")
        form.addField('blockweb', formal.Boolean(), label = "Force proxy usage", description="This setting forces browsing to only occur via the proxy. This should NOT be used in conjunction with the transparent proxy")
        form.addField('mailintercept', formal.Boolean(), label = "Intercept SMTP")
        if 'transproxy' in self.config:
            form.data = self.config
        else:
            form.data['transproxy'] = True
            form.data['mailintercept'] = True
        form.addAction(self.submitWiz6)
        return form

    def render_wizard6(self, ctx, data):
        return ctx.tag[tags.directive('form wizard6')]

    def submitWiz6(self, c, f, data):
        for k,v in data.items():
            self.config[k] = v

        return url.root.child('Wizard').child(str(self.id+1))

    # Wizzard 7
    def form_wizard7(self, data):
        form = formal.Form()

        form.addField('sambapdc', formal.Boolean(), label = "Domain Master")
        form.addField('windom', formal.String(), label = "Windows Domain")

        form.data = self.config

        form.addAction(self.submitWiz7)
        return form

    def render_wizard7(self, ctx, data):
        return ctx.tag[tags.directive('form wizard7')]

    def submitWiz7(self, c, f, data):
        for k,v in data.items():
            self.config[k] = v

        self.config['sambapdc'] = Utils.yesno(data['sambapdc'])
        return url.root.child('Wizard').child(str(self.id+1))

    # Wizzard 8
    def form_wizard8(self, data):
        form = formal.Form()

        form.addField('smrelay', formal.String(), label = "SMTP Outgoing Relay")
        form.addField('limit', formal.String(), label = "Size Restriction (In MB)")
        form.addField('exchangewash', formal.Boolean(), label = "Exchange Server forwarding")
        form.addField('exchangeserv', formal.String(), label = "Exchange Server IP")

        form.data = self.config

        if not self.config.get('limit'):
            form.data['limit'] = '100M'
        if not self.config.get('smrelay'):
            form.data['smrelay'] = 'smtp.isdsl.net'

        form.addAction(self.submitWiz8)
        return form

    def render_wizard8(self, ctx, data):
        return ctx.tag[tags.directive('form wizard8')]

    def submitWiz8(self, c, f, data):
        for k,v in data.items():
            self.config[k] = v

        return url.root.child('Wizard').child(str(self.id+1))


    # Wizzard 9 - End
    def form_end(self, data):
        form = formal.Form()

        form.addAction(self.submitWiz9)
        return form

    def render_wizard9(self, ctx, data):
        print self.config
        return ctx.tag[
            tags.p[
                "You have reached the end of the configuration wizard. ",
                "Please press the submit button to save the configuration.",
                "After the configuration is saved, this wizard will not be available"
            ],
            tags.directive('form end')
        ]

    def submitWiz9(self, c, f, data):
        self.config['bigname'] = self.config['bigname'].upper()
        self.config['smallname'] = self.config['bigname'].lower()

        head = """CompanyName = '%(company)s'
ExternalName = '%(external)s'
Hostname = '%(hostname)s'
Domain = '%(domain)s'
SambaDomain = '%(windom)s'
LDAPBase = '%(bigname)s'
LDAPPassword = '2sa%(smallname)s'\n""" % self.config

        if self.config['lanppp']:
            network = """EthernetDevices = {
    '%(laninterface)s': {
        'ip': '%(lanip)s',
        'type': 'static',
        'network': '%(lannetwork)s',
        'aliases': []
    },
}
LANPrimary = '%(laninterface)s'\n""" % self.config
            self.config['waninterface'] = 'ppp0'
            wan = """WANDevices = {
    'ppp0': {
        'pppd': [
            'defaultroute'
        ],
        'username': '%(adslusername)s',
        'password': '%(adslpassword)s',
        'link': '%(adslinterface)s',
        'plugins': 'pppoe'
    },
}\nWANPrimary = 'ppp0'\n""" % self.config
        elif self.config['lanwan']:
            wanip = self.config['wanip']
            self.config['wannet'] = Utils.getNetwork(wanip)
            wan = ""
            network = """EthernetDevices = {
    '%(laninterface)s': {
        'ip': '%(lanip)s',
        'type': 'static',
        'network': '%(lannetwork)s',
        'aliases': []
    },
    '%(waninterface)s':{
        'ip': '%(wanip)s',
        'type': 'static',
        'network': '%(wannet)s',
        'aliases': []
    },
}
WANDevices = {}
LANPrimary = '%(laninterface)s'
WANPrimary = '%(waninterface)s'
""" % self.config
        ds = self.config['dnsserv']
        self.config['dnsserv'] = [i.strip() for i in ds.split(',')]
        dns = """
ForwardingNameservers = %(dnsserv)s

TCSAliases = ['www','cache','mail','smtp','pop3','imap','router','ns','ntp','server','gateway']

NTP = '%(ntpserv)s'
SMTPRelay = '%(smrelay)s'
LocalDomains = ['%(domain)s']

GentooMirrors = [
    'http://siza.thusa.net/gentoo',
    'ftp://ftp.is.co.za/linux/distributions/gentoo',
    'http://ftp.up.ac.za/mirrors/gentoo.org/gentoo'
]
GentooRsync = ''
OverlayRsync = 'rsync://portage.thusa.net/thusa-portage' """ % self.config
        
        self.config['transparent'] = (self.config['transproxy'] and 1) or 0

        firewall = """
Shorewall = {
    'rules': [
        [1,'Ping/ACCEPT       all      all'],
        [1,'AllowICMPs        all      all'],
        [%(transparent)s,'REDIRECT loc      8080     tcp     80      -     !%(lannetwork)s'],
        [1,'REDIRECT loc      25       tcp     25      -     !%(lannetwork)s'],
        [1,'ACCEPT net:196.211.242.160/29 all'],
        [1,'ACCEPT net        all      tcp     80'],
        [1,'ACCEPT net        all      tcp     443'],
        [1,'ACCEPT net        all      tcp     25'],
        [1,'ACCEPT all        all      udp     1194'],
    ],
    'zones': {
        'loc': {
            'policy': 'ACCEPT',
            'interfaces': ['%(laninterface)s detect dhcp'],
            'log': ''
        },
        'net': {
            'policy': 'DROP',
            'interfaces': ['%(waninterface)s'],
            'log': ''
        },
    },
    'masq': {'%(waninterface)s': ['%(laninterface)s']}
}

ShorewallBalance = []
ShorewallSourceRoutes = []\n"""  % self.config
        sambaproxy = """SambaConfig = {
    'domain logons': '%(sambapdc)s',
    'smb ports': '139',
    'logon path': '\\\\\\\\%%L\\\\Profiles\\\\%%U',
    'logon drive': 'H:',
    'os level': '33',
    'local master': 'yes',
    'time server': 'yes',
    'wins support': 'yes',
    'preferred master': 'yes',
    ';logon script': 'STARTUP.BAT',
    'domain master': 'no',
    'logon home': '\\\\\\\\%%L\\\\%%U'
}

SambaShares = {
    'homes': {
        'writable': 'yes',
        'browseable': 'no',
        'directory mode': '700',
        'create mode': '600',
        'comment': 'Home Directories'
    },
    'Public': {
        'comment': 'Public Stuff',
        'writeable': 'yes',
        'printable': 'no',
        'create mode': '664',
        'path': '/var/lib/samba/data/public',
        'directory mode': '775',
        'public': 'yes'
    }

}

ProxyConfig = {
    'type': 'closed',
    'adauth': False,
    'addom': '',
    'adserver': ''
}

ProxyAllowedHosts = ['127.0.0.1', '%(lannetwork)s']

ProxyAllowedDestinations = ['89.202.157.0/24']

ProxyAllowedDomains = ['.windowsupdate.com','.eset.com','.sophos.com','.microsoft.com','.adobe.com','.symantecliveupdate.com','.symantec.com','.veritas.com']
ThusaDNSUsername = ''
ThusaDNSPassword = ''
ThusaDNSAddress = ''

Shaping = {}
ShaperRules = []""" % self.config

        if self.config['exchangewash']:
            mail = """\nMail = {
    'hubbed': [['%(domain)s', '%(exchangeserv)s']],
    'mailsize': '100M',
    'local': [],
    'relay': ['%(domain)s'],
    'blockedfiles': ['pif', 'lnk', 'com'],
}\n""" % self.config
        else:
            mail = """\nMail = {
    'hubbed': [],
    'mailsize': '',
    'local': ['%(domain)s'],
    'relay': [],
    'blockedfiles': ['pif', 'lnk', 'com']
}\n""" % self.config

        bigString = head + network + wan + dns + firewall + sambaproxy + mail

        lf = open('/usr/local/tcs/tums/config.py', 'wt')
        lf.write(bigString)
        lf.close()

        os.system('rm /usr/local/tcs/tums/initial')
        
        return url.root.child('auth')



    def render_pageLabel(self, ctx, data):
        labels = {
            1: "Server Identification",
            2: "Network configuration - Initial Layout",
            3: "Network configuration - LAN Details", 
            4: "Network configuration - ADSL Details",
            5: "Network configuration - WAN Details",
            6: "Firewall configuration",
            7: "Samba configuration",
            8: "Mail configuration",
            9: "Congratulations"
        }
        try:
            return ctx.tag[
                tags.h1(style="color:#fff;font-family:arial;")[labels[self.id]]
            ]
        except:
            return ctx.tag[tags.h1(style="color:#fff;font-family:arial;")["No Title"]]

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.invisible(render=tags.directive('wizard%s' % self.id))
        ]

    def locateChild(self, ctx, segs):
        print segs
        return Page(int(segs[0]), self.config), ()

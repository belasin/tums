from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP
from Core import PageHelpers, AuthApacheProxy, confparse, Utils, WebUtils
from Pages import Tools
import formal

class Page(PageHelpers.DefaultPage):
    addSlash = True

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Tools"]]

    def form_addStatic(self, data):
        form = formal.Form()
        form.addField('hostname', formal.String(required=True), label = "Hostname")
        form.addField('mac', formal.String(required=True), label = "Mac address", description="Hardware address of host. Must be : delimited")
        form.addField('ip', formal.String(required=True), label = "IP Address")
        form.addAction(self.submitForm)
        return form

    def submitForm(self, ctx, form, data):
        leases = self.sysconf.DHCP

        if leases.get('leases', None):
            leases['leases'][data['ip'].encode()] = [data['hostname'].encode(), data['mac'].encode()]
        else:
            leases['leases']  = {
                data['ip'].encode():[data['hostname'].encode(), data['mac'].encode()]
            }

        self.sysconf.DHCP = leases
        if os.path.exists('/etc/debian_versions'):
            WebUtils.system('/usr/local/tcs/tums/configurator --dhcp; /etc/init.d/dhcp3-server restart')
        else:
            WebUtils.system('/usr/local/tcs/tums/configurator --dhcp; /etc/init.d/dhcpd restart')
        return url.root.child('Dhcp')

    def form_confDhcp(self, data):
        form = formal.Form()
        form.addField('winserv', formal.String(), label = "Windows Server", description="A windows server (if any) to delegate for WINS and Netbios")
        form.addField('dnsserver', formal.String(), label = "DNS Server", description="DNS server")
        form.addField('network', formal.String(), label = "Network address")
        form.addField('netmask', formal.String(), label = "Subnet mask")
        form.addField('startip', formal.String(), label = "Start IP")
        form.addField('endip', formal.String(), label = "End IP")
        form.addField('gateway', formal.String(), label = "Default gateway")

        config = self.sysconf.DHCP
        myIp = self.sysconf.EthernetDevices[self.sysconf.LANPrimary]['ip'].split('/')[0]
        myNetmask = Utils.cidr2netmask(self.sysconf.EthernetDevices[self.sysconf.LANPrimary]['ip'].split('/')[1])

        rangeStart  = config.get('rangeStart', "100")
        rangeEnd    = config.get('rangeEnd', "220")
        netmask     = config.get('netmask', myNetmask)
        netbios     = config.get('netbios', myIp)
        nameserver  = config.get('nameserver', myIp)
        router      = config.get('gateway', myIp)
        myNet       = config.get('network', '.'.join(myIp.split('.')[:3]) + ".0")

        form.data['startip']     = rangeStart
        form.data['endip']       = rangeEnd
        form.data['gateway']     = router
        form.data['netmask']     = netmask
        form.data['network']     = myNet
        form.data['winserv']     = netbios
        form.data['dnsserver']   = nameserver

        form.addAction(self.confDhcp)
        return form

    def confDhcp(self, c, f, data):
        config = self.sysconf.DHCP
        config['rangeStart'] = data['startip']
        config['rangeEnd']   = data['endip']
        config['netmask']    = data['netmask']
        config['netbios']    = data['winserv']
        config['nameserver'] = data['dnsserver']
        config['gateway']    = data['gateway']
        config['network']    = data['network']

        self.sysconf.DHCP = config
        if os.path.exists('/etc/debian_versions'):
            WebUtils.system('/usr/local/tcs/tums/configurator --dhcp; /etc/init.d/dhcp3-server restart')
        else:
            WebUtils.system('/usr/local/tcs/tums/configurator --dhcp; /etc/init.d/dhcpd restart')
        return url.root.child('Dhcp')

    def form_addNet(self, ctx):
        form = formal.Form()
        ifaces = []
        for i, defin in self.sysconf.EthernetDevices.items():
            if defin.get('dhcpserver', False) and i != self.sysconf.LANPrimary:
                ifaces.append((i,i))
        form.addField('interface', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = ifaces), 
            description = "DHCP Interface", label = "Interface")
        form.addField('domain', formal.String(required=True), label = "Domain")
        form.addAction(self.submitNet)
        return form

    def submitNet(self, ctx, form, data):
        d = self.sysconf.DHCP
        if not d.get("sharenets", False):
            d['sharenets'] = {}

        d['sharenets'][data['interface'].encode()] = {
            'domain' : data['domain'].encode()
        }

        self.sysconf.DHCP = d 
        WebUtils.system('/usr/local/tcs/tums/configurator --dhcp')
        return url.root.child('Dhcp')

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Tools.Page.sideMenu(Tools.Page(None, self.db), ctx, data)]

    def render_content(self, ctx, data):
        leases = self.sysconf.DHCP.get('leases', {})
        statics = []
        for ip, hostmac in leases.items():
            statics.append((ip, hostmac[0], hostmac[1]))

        statics.sort()

        sharenets = []
        for sharenet, defin in self.sysconf.DHCP.get('sharenets', {}).items():
            sharenets.append((
                sharenet, 
                defin['domain'], 
                self.sysconf.EthernetDevices[sharenet]['ip'],
                tags.a(href="Delnet/%s/" % sharenet)[tags.img(src="/images/ex.png")]
            ))

        return ctx.tag[
            tags.h3[tags.img(src="/images/netdrive.png"), " DHCP"],
            PageHelpers.TabSwitcher((
                ('DHCP Settings', 'panelSettings'),
                ('Static Leases', 'panelLeases'),
                ('Shared Networks', 'panelAltnet'),
            )),
            tags.div(id="panelLeases", _class="tabPane")[
                tags.table(cellspacing=0, _class='listing')[
                    tags.thead(background="/images/gradMB.png")[
                        tags.tr[
                            tags.th["IP Address"],
                            tags.th["Hostname"],
                            tags.th["MAC Address"],
                            tags.th[""],
                        ]
                    ],
                    tags.tbody[
                    [   
                        tags.tr[
                            tags.td[i[0]],
                            tags.td[i[1]],
                            tags.td[i[2]],
                            tags.td[tags.a(href="Delete/%s/" % i[0])[tags.img(src="/images/ex.png")]]
                        ]
                    for i in statics],
                    ]
                ], tags.br,
                tags.h3["Add Static Lease"], 
                tags.directive('form addStatic')
            ], 
            tags.div(id="panelSettings", _class="tabPane")[
                tags.directive('form confDhcp')
            ],
            tags.div(id="panelAltnet", _class="tabPane")[
                PageHelpers.dataTable(("Interface", "Domain", "Network", ""), sharenets),
                tags.h3["Add DHCP Network"],
                tags.directive('form addNet')
            ],
            PageHelpers.LoadTabSwitcher()
        ]

    def locateChild(self, ctx, segs):
        if segs[0]=="Delete":
            leases = self.sysconf.DHCP
            del leases['leases'][segs[1]]
            self.sysconf.DHCP = leases
            return url.root.child('Dhcp'), ()
        if segs[0]=="Delnet":
            nets = self.sysconf.DHCP
            del nets['sharenets'][segs[1]]
            self.sysconf.DHCP = nets
            WebUtils.system('/usr/local/tcs/tums/configurator --dhcp')
            return url.root.child('Dhcp'), ()
        return rend.Page.locateChild(self, ctx, segs)
            

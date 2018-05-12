from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP
from Core import PageHelpers, AuthApacheProxy, Utils, confparse, WebUtils
from Pages import Tools
import formal, copy

class EditPage(PageHelpers.DefaultPage):
    def __init__(self, avatarId=None, db = None, iface = "", *a, **kw):
        self.iface = iface
        self.db = db
        PageHelpers.DefaultPage.__init__(self, avatarId, self.db, *a, **kw)

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Tools"]]

    def getZones(self):
        zones = self.sysconf.Shorewall['zones']
        return [(zo,zo) for zo in zones.keys()] # Build something we can se for drop downs

    def form_modInterface(self, data):
        form = formal.Form()

        form.addField('dhcp', formal.Boolean(), label = "DHCP")
        form.addField('ip', formal.String(), label = "IP Address", description = "IP address for this interface as CIDR (x.x.x.x/y)")
        if Settings.capabilities.get('ipv6', False):
            form.addField('ipv6', formal.String(), label = "IPv6 Address", description = "IPv6 address for this interface")
            form.addField('ipv6adv', formal.Boolean(), label = "Announce prefix", description = "Announce prefix on this interface")
        form.addField('netmask', formal.String(), label = "Network Address", description = "Network address for this interface (Required if DHCP selected)")
        form.addField('ipAlias', formal.String(), label = "IP Alias", 
            description = "Alias for this interface as CIDR (x.x.x.x/y). Separate multiple aliases with a semicolon")
        form.addField('dhcpserver', formal.Boolean(), label = "DHCP Server", description = "Serve DHCP on this interface")

        form.addField('firewallPolicy', formal.String(required=True),
            formal.widgetFactory(formal.SelectChoice, options = [('ACCEPT', 'Accept All'), ('DROP', 'Deny All')]),
            label = "Default firewall policy")

        form.addField('firewallZone', formal.String(required=True),
            formal.widgetFactory(formal.SelectChoice, options = self.getZones()),
            label = "Firewall Zone")

        ifDetail = self.sysconf.EthernetDevices[self.iface]
        print ifDetail
        form.data = {}
        if ifDetail.get('type', '') == "dhcp":
            form.data['dhcp'] = True

        form.data['dhcpserver'] = ifDetail.get('dhcpserver', False)

        if ifDetail.get('ip',False):
            form.data['ip'] = ifDetail['ip']

        if ifDetail.get('network', False):
            form.data['netmask'] = ifDetail['network']

        if ifDetail.get('aliases', False):
            form.data['ipAlias'] = ';'.join(ifDetail['aliases'])

        if Settings.capabilities.get('ipv6', False):
            if ifDetail.get('ipv6', False):
                form.data['ipv6'] = ifDetail['ipv6']
            if ifDetail.get('ipv6adv', False):
                form.data['ipv6adv'] = True

        wallZones = self.sysconf.Shorewall['zones']
        for i,v in wallZones.items():
            for k in v['interfaces']:
                if self.iface in k:
                    form.data['firewallZone'] = i
                    form.data['firewallPolicy'] = wallZones[i]['policy']

        form.addAction(self.submitForm)
        return form

    def submitForm(self, ctx, form, data):
        if data['ipAlias']:
            aliases = data['ipAlias'].encode().replace(' ', '').split(';')
        else:
            aliases = []
        if data['ip']:
            ip = data['ip'].strip().encode()
        else:
            ip = ""

        if data['dhcp']:
            type = "dhcp"
        else:
            type = "static"

        if data['netmask']:
            network = data['netmask'].strip().encode()
        elif data['ip']:
            # make a foney /24 network if we don't know wtf is going on
            network = '.'.join(ip.split('.')[:3])+'.0/24'
        else:
            # ok we're just boned, save and carry on
            network = ""
        iFaces = copy.deepcopy(self.sysconf.EthernetDevices)
        thisIf = iFaces[self.iface]
        thisIf['dhcpserver'] = data['dhcpserver']
        thisIf['type'] = type
        thisIf['ip'] = ip
        thisIf['network'] = network
        thisIf['aliases'] = aliases

        if data.get('ipv6', False):
            thisIf['ipv6'] = data['ipv6'].encode()
            thisIf['ipv6adv'] = data['ipv6adv']

        iFaces[self.iface] = thisIf
        self.sysconf.EthernetDevices = iFaces

        if os.path.exists('/etc/debian_version'):
            WebUtils.system(Settings.BaseDir+'/configurator --debnet')
        else:
            WebUtils.system(Settings.BaseDir+'/configurator --net')
        WebUtils.system('/etc/init.d/net.%s restart' % self.iface)

        # Perform shorewall configuration

        shoreWall = copy.deepcopy(self.sysconf.Shorewall)

        shoreWall['zones'][data['firewallZone']]['policy'] = data['firewallPolicy']

        # check the interface isn't there
        ifaceZone = shoreWall['zones'][data['firewallZone']]['interfaces']

        # Primary LAN interface should be defined with LAN Primary
        dhcp = ""
        if self.iface == self.sysconf.LANPrimary:
            dhcp = "dhcp"
    
        for cnt, iface in enumerate(ifaceZone):
            if self.iface in iface:
                del shoreWall['zones'][data['firewallZone']]['interfaces'][cnt]

        shoreWall['zones'][data['firewallZone']]['interfaces'].append('%s detect %s' % (self.iface, dhcp))

        # Delete interface from other zones
        for zone in shoreWall['zones']:
            if zone != data['firewallZone']:
                ifaceDefs = []
                for i in shoreWall['zones'][zone]['interfaces']:
                    if self.iface not in i:
                        ifaceDefs.append(i)
                shoreWall['zones'][zone]['interfaces'] = ifaceDefs

        self.sysconf.Shorewall = shoreWall

        WebUtils.system(Settings.BaseDir + '/configurator --shorewall')
        WebUtils.system('shorewall restart') 

        return url.root.child('Network')

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Tools.Page.sideMenu(Tools.Page(None, self.db), ctx, data)]

    def render_content(self, ctx, data):
        return ctx.tag[
                tags.h1["Configure ", self.iface.replace('eth', 'Port ')],
                tags.directive('form modInterface')
        ]

    def childFactory(self, ctx, seg):
        return EditPage(self.avatarId, self.db, iface=seg)

class Page(PageHelpers.DefaultPage):
    addSlash = True

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Tools"]]

    def childFactory(self, ctx, seg):
        if seg == "Edit":
            return EditPage(self.avatarId, self.db)

    def form_addInterface(self, data):
        form = formal.Form()

        form.addField('interface', formal.String(required=True),
            formal.widgetFactory(formal.SelectChoice, options = [(i, i.replace('eth', 'Port ')) for i in Utils.getInterfaces() if not i=="lo"]), 
            label = "Interface")

        form.addField('dhcp', formal.Boolean(), label = "DHCP")
        
        form.addField('ip', formal.String(), label = "IP Address")
        if Settings.capabilities.get('ipv6', False):
            form.addField('ipv6', formal.String(), label = "IPv6 Address", description = "IPv6 address for this interface")
            form.addField('ipv6adv', formal.Boolean(), label = "Announce prefix", description = "Announce prefix on this interface")
        
        form.addField('netmask', formal.String(), label = "Netmask", description = "Netmask or CIDR bitmask for this range")
        form.addField('dhcpserver', formal.Boolean(), label = "DHCP Server", description = "Serve DHCP on this interface")
            
        form.addAction(self.submitForm)
        return form

    def submitForm(self, ctx, form, data):
        ifaces = self.sysconf.EthernetDevices

        if '/' in data['ip']:
            ip = data['ip']
            network = Utils.getNetwork(ip)
        else:
            if "." in data['netmask']:
                cidr = Utils.netmask2cidr(data['netmask'])
                ip = "%s/%s" % (data['ip'], cidr)
                network = Utils.getNetwork(ip)
            else:
                ip = "%s/%s" % (data['ip'], data['netmask'])
                network = Utils.getNetwork(ip)

            
        
        defn = {
            'ip': ip,
            'network': network,
            'type': 'static',
            'dhcpserver': data['dhcpserver']
        }

        if data.get('ipv6', False):
            defn['ipv6'] = data['ipv6'].encode()
            defn['ipv6adv'] = data['ipv6adv']

        if data['dhcp']:
            defn['type'] = 'dhcp'
        else:
            defn['type'] = 'static'

        ifaces[data['interface']] = defn

        self.sysconf.EthernetDevices = ifaces
        if os.path.exists('/etc/debian_version'):
            WebUtils.system('/usr/local/tcs/tums/configurator --debnet')
        else:
            WebUtils.system('/usr/local/tcs/tums/configurator --net')
        return url.root.child('Network')

    def form_addVLAN(self, data):
        form = formal.Form()

        form.addField('interface', formal.String(required=True),
            formal.widgetFactory(formal.SelectChoice, options = [(i, i.replace('eth', 'Port ')) for i in Utils.getInterfaces() if not i=="lo"]), 
            label = "Attached Interface")

        form.addField('vlan', formal.Integer(), label = "VLAN Number")
        form.addField('ip', formal.String(), label = "IP Address")
        form.addField('netmask', formal.String(), label = "Netmask", description = "Netmask or CIDR bitmask for this range")
        form.addField('dhcpserver', formal.Boolean(), label = "DHCP Server", description = "Serve DHCP on this interface")
        form.addAction(self.submitVlan)
        return form

    def submitVlan(self, ctx, form, data):
        ifaces = self.sysconf.EthernetDevices

        if '/' in data['ip']:
            ip = data['ip']
            network = Utils.getNetwork(ip)
        else:
            if "." in data['netmask']:
                cidr = Utils.netmask2cidr(data['netmask'])
                ip = "%s/%s" % (data['ip'], cidr)
                network = Utils.getNetwork(ip)
            else:
                ip = "%s/%s" % (data['ip'], data['netmask'])
                network = Utils.getNetwork(ip)
        
        defn = {
            'ip': ip.encode(),
            'network': network.encode(),
            'interface': data['interface'].encode(), 
            'dhcpserver': data['dhcpserver']
        }

        ifaces['vlan%s' % data['vlan']] = defn

        self.sysconf.EthernetDevices = ifaces

        if os.path.exists('/etc/debian_version'):
            WebUtils.system('/usr/local/tcs/tums/configurator --debnet')
        else:
            WebUtils.system('/usr/local/tcs/tums/configurator --net')
        return url.root.child('Network')

    def form_tunnelConf(self, data):
        form = formal.Form()
        form.addField('remoteip', formal.String(), label = "Remote IPv4 address")
        form.addField('localip', formal.String(), label = "Local IPv4 address") 
        form.addField('localv6', formal.String(), label = "IPv6 address")
        form.addAction(self.submitTunnel)

        if self.sysconf.Tunnel.get('ipv6', False):
            form.data['remoteip'] = self.sysconf.Tunnel['ipv6'].get('remoteip', '')
            form.data['localip']  = self.sysconf.Tunnel['ipv6'].get('localip', '')
            form.data['localv6']  = self.sysconf.Tunnel['ipv6'].get('localv6', '')
        return form

    def submitTunnel(self, ctx, form, data):
        tun = self.sysconf.Tunnel
        tun['ipv6'] = {
            'remoteip' : data['remoteip'],
            'localip'  : data['localip'],
            'localv6'  : data['localv6']
        }
        self.sysconf.Tunnel = tun
        if os.path.exists('/etc/debian_version'):
            WebUtils.system('/usr/local/tcs/tums/configurator --debnet')
        else:
            WebUtils.system('/usr/local/tcs/tums/configurator --net')
        remote = data['remoteip']
        local = data['localip']
        localv6 = data['localv6']
        cont = []
        cont.append('ip tun del ipv6tun;')
        cont.append('ip tunnel add ipv6tun mode sit remote %s local %s ttl 255; ' % (remote, local))
        cont.append('ip link set ipv6tun up; ')
        cont.append('ip addr add %s dev ipv6tun; ' % (localv6))
        cont.append('ip -6 ro add 2003::/3 dev ipv6tun')
        WebUtils.system(''.join(cont))
        return url.root.child('Network')
 
    def form_addRoute(self, data):
        form = formal.Form()
        form.addField('destination', formal.String(), label = "Destination")
        form.addField('mask', formal.String(), label = "Netmask")
        form.addField('gateway', formal.String(), label = "Gateway")
        form.addField('interface', formal.String(),
            formal.widgetFactory(formal.SelectChoice, options = [(i, i.replace('eth', 'Port ')) for i in Utils.getInterfaces() if not i=="lo"]), 
            label = "Interface"
        )

        form.addAction(self.submitRouteForm)
        return form
        
    def submitRouteForm(self, ctx, form, data):
        return url.root.child('Network')

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Tools.Page.sideMenu(Tools.Page(None, self.db), ctx, data)]

    def render_content(self, ctx, data):
        interfaces = Utils.getInterfaces() + self.sysconf.EthernetDevices.keys()
        params = Utils.parseNet()
        d = {}
        vlans = []
        routes = {}
        types = {}
        vali = []
        for i in interfaces:
            if not "vlan" in i:
                if i in d.keys():
                    pass
                if i in params.keys():
                    types[i] = params[i]['type']
                    routes[i] = [params[i].get('network', '')]
                    if params[i]['type'] == 'static':
                        d[i] = params[i]['ip']
                    if params[i]['type'] =='manual':
                        d[i] = "Manual"
                    else:
                        d[i] = "DHCP"
                else:
                    types[i] = ""
                    routes[i] = ""
                    d[i] = ""
            else:
                vlans.append((
                    i, 
                    params[i]['ip'], 
                    tags.a(title="Edit Interface %s" % i, href="Edit/%s"%i)[tags.img(src="/images/edit.png")]
                ))

        return ctx.tag[
            tags.h3[tags.img(src="/images/netdrive.png"), " Network Setup"],
            PageHelpers.TabSwitcher((
                ('Interface Configuration', 'panelIface'),
                ('VLAN Configuration', 'panelVlan'), 
                ('IPv6 Tunnel', 'panelTunnel')
            )),
            tags.div(id="panelIface", _class="tabPane")[
                tags.h3["Configured Interfaces"],
                tags.table(cellspacing="0", _class="listing")[
                    tags.thead(background="/images/gradMB.png")[
                        tags.tr[
                            tags.th['Interface'],
                            tags.th['DHCP'],
                            tags.th['IP'],
                            tags.th['Associated Routes'],
                            tags.th[''],
                        ]
                    ],
                    tags.tbody[
                        [ tags.tr[
                            tags.td[i.replace('eth', 'Port ')],
                            tags.td[types[i]=='dhcp'],
                            tags.td[d[i]],
                            tags.td[[ [k,tags.br] for k in routes.get(i, ["None"]) ]],
                            tags.td[tags.a(title="Edit Interface %s" % i, href="Edit/%s"%i)[tags.img(src="/images/edit.png")]],
                        ]
                        for i in d.keys() if not i=="lo"]
                    ]
                ],
                tags.br,
                tags.h3["Add interface"],
                tags.directive('form addInterface')
            ],
            tags.div(id="panelVlan", _class="tabPane")[
                tags.h3["Configured VLAN Interfaces"],
                PageHelpers.dataTable(('Interface', 'IP', ''), vlans),
                tags.br,
                tags.h3["Add VLAN"],
                tags.directive('form addVLAN')
            ],
            tags.div(id="panelTunnel", _class="tabPane")[
                tags.h3["Configure IPv6 Tunnel"],
                tags.directive('form tunnelConf')
            ],
            PageHelpers.LoadTabSwitcher(),
        ]

    def locateChild(self, ctx, segs):
        #if segs[0]=="Delete":

        return rend.Page.locateChild(self, ctx, segs)
            

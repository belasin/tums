from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP, datetime
from Core import PageHelpers, AuthApacheProxy, Utils, confparse, WebUtils
from Pages import Tools
import formal, copy

class EditPage(Tools.Page):
    def __init__(self, avatarId=None, db = None, iface = "", *a, **kw):
        self.iface = iface
        self.db = db
        Tools.Page.__init__(self, avatarId, self.db, *a, **kw)

    def getZones(self):
        zones = self.sysconf.Shorewall['zones']
        return [(zo,zo) for zo in zones.keys()] # Build something we can se for drop downs

    def form_modInterface(self, data):
        form = formal.Form()

        form.addField('dhcp', formal.Boolean(), label = "DHCP")
        form.addField('interior', formal.Boolean(), label = "Interior", description = "Tick this if the interface in question is an interior LAN interface")

        form.addField('ip', formal.String(strip=True, validators=[PageHelpers.IPMaskValidator()]), 
            label = "IP Address", description = "IP address for this interface as CIDR (x.x.x.x/y)")

        try:
            if Settings.capabilities.get('ipv6', False):
                form.addField('ipv6', formal.String(), label = "IPv6 Address", description = "IPv6 address for this interface")
                form.addField('ipv6adv', formal.Boolean(), label = "Announce prefix", description = "Announce prefix on this interface")
        except:
            # No capability setting
            pass
        form.addField('gateway', formal.String(strip=True, validators=[PageHelpers.IPValidator()]), label = "Default Gateway", description = "IP Address that should be used to route default traffic from this server. This will over-write any other default gateways configured in this profile.")
        form.addField('netmask', formal.String(strip=True, validators=[PageHelpers.IPMaskValidator()]), label = "Network Address", description = "Network address for this interface (Required if DHCP selected)")
        form.addField('ipAlias', formal.String(), label = "IP Alias", 
            description = "Alias for this interface as CIDR (x.x.x.x/y). Separate multiple aliases with a comma")

        form.addField('mtu', formal.Integer(), label = "MTU", description = "Set this interfaces MTU. Value must be between 1200 and 1500.")
        form.addField('dhcpserver', formal.Boolean(), label = "DHCP Server", description = "Serve DHCP on this interface")

        form.addField('firewallPolicy', formal.String(required=True),
            formal.widgetFactory(formal.SelectChoice, options = [('ACCEPT', 'Accept All'), ('DROP', 'Deny All')]),
            label = "Default firewall policy")

        form.addField('firewallZone', formal.String(required=True),
            formal.widgetFactory(formal.SelectChoice, options = self.getZones()),
            label = "Firewall Zone")

        form.data = {}
        lp = self.sysconf.LANPrimary
        if self.iface in lp:
            form.data['interior'] = True

        ifDetail = self.sysconf.EthernetDevices.get(self.iface, {})
        print ifDetail
        if ifDetail.get('type', '') == "dhcp":
            form.data['dhcp'] = True

        form.data['dhcpserver'] = ifDetail.get('dhcpserver', False)

        if ifDetail.get('ip',False):
            form.data['ip'] = ifDetail.get('ip', '')

        if ifDetail.get('network', False):
            form.data['netmask'] = ifDetail.get('network', '')

        if ifDetail.get('routes', False):
            routes = ifDetail.get('routes', False)
            for dest, gw in routes:
                if dest == "default":
                    form.data['gateway'] = gw
                    break

        if ifDetail.get('aliases', False):
            form.data['ipAlias'] = ', '.join(ifDetail['aliases'])

        try:
            if Settings.capabilities.get('ipv6', False):
                if ifDetail.get('ipv6', False):
                    form.data['ipv6'] = ifDetail['ipv6']
                if ifDetail.get('ipv6adv', False):
                    form.data['ipv6adv'] = True
        except:
            pass

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
            aliases = data['ipAlias'].encode("ascii", "replace").replace(' ', '').split(',')
        else:
            aliases = []
        if data['ip']:
            ip = data['ip'].strip().encode("ascii", "replace")
        else:
            ip = ""

        if data['dhcp']:
            type = "dhcp"
        else:
            type = "static"

        if data['netmask']:
            network = data['netmask'].strip().encode("ascii", "replace")
        elif data['ip']:
            # make a foney /24 network if we don't know wtf is going on
            network = '.'.join(ip.split('.')[:3])+'.0/24'
        else:
            # ok we're just boned, save and carry on
            network = ""

        iFaces = copy.deepcopy(self.sysconf.EthernetDevices)
        thisIf = iFaces.get(self.iface, {})
        thisIf['dhcpserver'] = data['dhcpserver']
        thisIf['type'] = type
        thisIf['ip'] = ip

        # set the defualt route
        routes = thisIf.get('routes', [])
        rDict = dict(routes)
        if data['gateway']:
            fGateway = data['gateway'].encode("ascii", "replace")
            # Remove any other default routes because one is set here
            for dev, conf in self.sysconf.EthernetDevices.items():
                if dev == self.iface:
                    # Skip configured interface here
                    continue

                oldRoutes = conf.get('routes', [])
                newRoutes = []
                skip = True
                for dst, gw in oldRoutes:
                    if dst=="default":
                        skip = False
                        continue
                    newRoutes.append((dst, gw))

                if not skip:
                    iFaces[dev]['routes'] = newRoutes
        else:
            fGateway = ""

        if fGateway:
            rDict['default'] = fGateway
        elif rDict.get('default'):
            del rDict['default']

        newRoutes = [i for i in rDict.items()]

        if newRoutes:
            thisIf['routes'] = newRoutes
        elif thisIf.get('routes'):
            del thisIf['routes']

        # Continue config
        thisIf['network'] = network
        thisIf['aliases'] = aliases

        if (data['mtu'] > 1200) and (data['mtu'] < 1501):
            thisIf['mtu'] = data['mtu']

        if data.get('ipv6', False):
            thisIf['ipv6'] = data['ipv6'].encode("ascii", "replace")
            thisIf['ipv6adv'] = data['ipv6adv']

        iFaces[self.iface] = thisIf
        self.sysconf.EthernetDevices = iFaces

        lp = self.sysconf.LANPrimary

        newLP = lp
        if data['interior']:
            if self.iface not in lp:
                newLP.append(self.iface)
                self.sysconf.LANPrimary = newLP
        else:
            if self.iface in lp:
                newLP = []
                for k in lp:
                    if k != self.iface:
                        newLP.append(k)

            self.sysconf.LANPrimary = newLP
        # Perform shorewall configuration

        shoreWall = copy.deepcopy(self.sysconf.Shorewall)

        shoreWall['zones'][data['firewallZone']]['policy'] = data['firewallPolicy']

        # check the interface isn't there
        ifaceZone = shoreWall['zones'][data['firewallZone']]['interfaces']

        for cnt, iface in enumerate(ifaceZone):
            if self.iface in iface:
                del shoreWall['zones'][data['firewallZone']]['interfaces'][cnt]

        shoreWall['zones'][data['firewallZone']]['interfaces'].append('%s detect dhcp,routeback' % (self.iface))

        # Delete interface from other zones
        for zone in shoreWall['zones']:
            if zone != data['firewallZone']:
                ifaceDefs = []
                for i in shoreWall['zones'][zone]['interfaces']:
                    if self.iface not in i:
                        ifaceDefs.append(i)
                shoreWall['zones'][zone]['interfaces'] = ifaceDefs

        self.sysconf.Shorewall = shoreWall

        # Clear old aliases out of system
        oldAliases = self.sysconf.EthernetDevices.get(self.iface, {}).get('aliases', [])
        for addr in oldAliases:
            if addr not in aliases:
                WebUtils.system('ip addr del %s dev %s' % (i, self.iface))

        WebUtils.restartNetworking(data['dhcpserver'])

        return url.root.child('Network')

    def render_content(self, ctx, data):
        return ctx.tag[
                tags.h1["Configure ", self.iface],
                tags.directive('form modInterface')
        ]

    def childFactory(self, ctx, seg):
        if 'tap' in seg:
            return url.root.child('VPN')
        if 'ppp' in seg:
            return url.root.child('PPP')
        return EditPage(self.avatarId, self.db, iface=seg)

class Page(Tools.Page):
    addSlash = True

    def childFactory(self, ctx, seg):
        if seg == "Edit":
            return EditPage(self.avatarId, self.db)

    def form_addInterface(self, data):
        form = formal.Form()

        form.addField('interface', formal.String(required=True),
            formal.widgetFactory(formal.SelectChoice, options = [(i, i) for i in Utils.getInterfaces() if not i=="lo"]), 
            label = "Interface")

        form.addField('dhcp', formal.Boolean(), label = "DHCP", description="Use DHCP to discover an IP address for this interface")
        
        form.addField('ip', formal.String(strip=True, validators=[PageHelpers.IPValidator()]), label = "IP Address")
        try:
            if Settings.capabilities.get('ipv6', False):
                form.addField('ipv6', formal.String(), label = "IPv6 Address", description = "IPv6 address for this interface")
                form.addField('ipv6adv', formal.Boolean(), label = "Announce prefix", description = "Announce prefix on this interface")
        except:
            pass
            
        form.addField('netmask', formal.String(), label = "Netmask", description = "Netmask or CIDR bitmask for this range")
        form.addField('mtu', formal.Integer(), label = "MTU", description = "Set this interfaces MTU. Value must be between 1200 and 1500.")
        form.addField('dhcpserver', formal.Boolean(), label = "DHCP Server", description = "Serve DHCP on this interface")
            
        form.addAction(self.submitForm)
        return form

    def submitForm(self, ctx, form, data):
        ifaces = self.sysconf.EthernetDevices
        iface = data['interface'].encode("ascii", "replace")
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

        if (data['mtu'] > 1200) and (data['mtu'] < 1501):
            defn['mtu'] = data['mtu']

        if data['dhcpserver']:
            d = self.sysconf.DHCP
            if not d.get(iface):
                d[iface] = {}

            self.sysconf.DHCP = d
            
        if data.get('ipv6', False):
            defn['ipv6'] = data['ipv6'].encode("ascii", "replace")
            defn['ipv6adv'] = data['ipv6adv']

        if data['dhcp']:
            defn['type'] = 'dhcp'
        else:
            defn['type'] = 'static'

        ifaces[iface] = defn

        self.sysconf.EthernetDevices = ifaces

        WebUtils.restartNetworking(data['dhcpserver'])

        return url.root.child('Network')

    def form_addVLAN(self, data):
        form = formal.Form()

        form.addField('interface', formal.String(required=True),
            formal.widgetFactory(formal.SelectChoice, options = [(i, i) for i in Utils.getInterfaces() if not i=="lo"]), 
            label = "Attached Interface")

        form.addField('vlan', formal.Integer(), label = "VLAN Number")
        form.addField('ip', formal.String(strip=True, validators=[PageHelpers.IPValidator()]), label = "IP Address")
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
            'ip': ip.encode("ascii", "replace"),
            'network': network.encode("ascii", "replace"),
            'interface': data['interface'].encode("ascii", "replace"), 
            'dhcpserver': data['dhcpserver']
        }

        ifaces['vlan%s' % data['vlan']] = defn

        self.sysconf.EthernetDevices = ifaces

        WebUtils.restartNetworking(data['dhcpserver'])

        return url.root.child('Network')

    def form_tunnelConf(self, data):
        form = formal.Form()
        form.addField('remoteip', formal.String(strip=True, validators=[PageHelpers.IPValidator()]), label = "Remote IPv4 address")
        form.addField('localip', formal.String(strip=True, validators=[PageHelpers.IPValidator()]), label = "Local IPv4 address") 
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

        WebUtils.restartService('debnet', either='net')

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
 
    def form_advanced(self, data):
        form = formal.Form()
        form.addField('selack', formal.Boolean(), label = "Selective ACK", description = "Enable selective ACK windowing")
        form.addField('maxwin', formal.Integer(), label = "Window Max", description = "Maximum TCP Window")
        form.addField('backlog', formal.String(), label = "Backlog", description = "Maximum Device Backlog")

        form.addField('gige', formal.Boolean(), label = "Auto-Tune GigE", description = "Apply automatic tuning for GigE (overrides the settings above)")

        form.addField('cookies', formal.Boolean(), label = "SYN Cookies", description = "Enable SYN-Cookies. This is handy if you're at risk of DDoS SYN floods.")
        form.addField('proxyarp', formal.Boolean(), label = "Proxy ARP", description = "Enable Proxy ARP.")
    
        form.data['cookies'] = self.sysconf.General.get('tuning', {}).get('syn-cookies', False)
        form.data['proxyarp'] = self.sysconf.General.get('tuning', {}).get('proxyarp', False)

        gen = self.sysconf.General.get('tuning', {}).get('tcp-hp', False)
        if gen:
            form.data['maxwin'] = gen.get('max-window', '16777216')
            form.data['backlog'] = gen.get('backlog', '250000')
            form.data['selack'] = gen.get('selective-ack', True)
            # Test the settings against our defaults
            if gen.get('backlog', False)=='250000' and gen.get('max-window', False) == '16777216':
                # if they are default we assume auto-tune mode is active
                form.data['gige'] = True
        else:
            form.data['selack'] = True
            form.data['maxwin'] = 110592
            form.data['backlog'] = 1000
            form.data['gige'] = False

        form.addAction(self.submitAdvForm)
        return form
        
    def submitAdvForm(self, ctx, form, data):
        gen = self.sysconf.General
        # Apply direct
        selack = data['selack']
        maxwindow = data['maxwin']
        backlog = data['backlog']

        # Override if gige ticked
        if data['gige']:
            maxwindow = '16777216'
            backlog = '250000'

        hp = {
                'max-window': maxwindow,
                'backlog': backlog, 
                'selective-ack': selack, 
            }
        
        if not gen.get('tuning', False):
            # No tuning stanza, so make one
            gen['tuning'] = {}

        # apply the tcp high-performance rules
        gen['tuning']['tcp-hp'] = hp

        # Add syn cookies to the mix
        gen['tuning']['syn-cookies'] = data['cookies']
        gen['tuning']['proxyarp'] = data['proxyarp']

        self.sysconf.General = gen

        # Fold.
        def returnn(_):
            return url.root.child('Network')
        return WebUtils.system('/usr/local/tcs/tums/configurator --tuning; sysctl -q -p').addCallback(returnn)

    def roundedBlock(self, title, content):
        return tags.div(_class="roundedBlock")[tags.img(src="/images/network-small.png"), tags.h1[title],tags.div[tags.div[content]]]

    def render_content(self, ctx, data):
        interfaces = Utils.getInterfaces() + self.sysconf.EthernetDevices.keys()
        params = Utils.parseNet()
        d = {}
        vlans = []
        routes = {}
        types = {}
        vali = []
        traffic = {}
        da = datetime.datetime.now()
        today = "%s%s%s" % (da.day, da.month, da.year)
        for i in interfaces:
            if 'tap' not in i and 'eth' not in i and 'ppp' not in i and 'vlan' not in i:
                continue
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
            # Read the traffic counters
            try:
                p = open('/usr/local/tcs/tums/rrd/iface_%s_%stotal.nid' % (i, today) ).read().split(':')
                traffic[i] = (float(p[0]), float(p[1]))
            except:
                traffic[i] = (0,0)

        return ctx.tag[
            tags.h3[tags.img(src="/images/stock-disconnect.png"), self.text.toolsMenuNetconf],
            PageHelpers.TabSwitcher((
                ('Interface Configuration', 'panelIface'),
                ('VLAN Configuration', 'panelVlan'), 
                ('IPv6 Tunnel', 'panelTunnel'), 
                ('Advanced', 'panelAdvanced'),
            )),
            tags.div(id="panelIface", _class="tabPane")[
                tags.h3["Interfaces"],
                tags.table(width="95%")[
                    [tags.tr[
                        [tags.td[
                            self.roundedBlock(j, [
                                tags.img(src="/images/graphs/iface-%sFS.png" % j),
                                tags.table[
                                    tags.tr(valign="top")[
                                        tags.td[tags.strong["Traffic Out (24h): "]],
                                        tags.td[Utils.intToH(traffic[j][1])]
                                    ],
                                    tags.tr(valign="top")[
                                        tags.td[tags.strong["Traffic In (24h): "]],
                                        tags.td[Utils.intToH(traffic[j][0])]
                                    ],
                                    tags.tr(valign="top")[
                                        tags.td[tags.strong["Configuration Type: "]],
                                        tags.td[types[j] == 'dhcp' and 'DHCP' or 'Static']
                                    ],
                                    tags.tr(valign="top")[
                                        tags.td[tags.strong["Associated Routes: "]],
                                        tags.td[[ [k,tags.br] for k in routes.get(j, ["None"]) ]]
                                    ],
                                    tags.tr(valign="top")[
                                        tags.td[
                                            tags.a(title="Edit Interface %s" % j, href="Edit/%s"%j)[tags.img(src="/images/edit.png"), " Edit Settings"]
                                        ],
                                        tags.td[""]
                                    ]
                                ]
                            ])
                        ] for j in i if j]
                    ] for i in WebUtils.runIter(1, d.keys())]
                ],
                tags.br,
                #tags.h3["Add interface"],
                #tags.directive('form addInterface')
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
            tags.div(id="panelAdvanced", _class="tabPane")[
                tags.h3["Advanced Settings"],
                tags.p["If you are unsure of any of these settings you should almost certainly not change them"],
                tags.directive('form advanced')
            ],
            PageHelpers.LoadTabSwitcher(),
        ]

    def locateChild(self, ctx, segs):
        #if segs[0]=="Delete":

        return rend.Page.locateChild(self, ctx, segs)
            

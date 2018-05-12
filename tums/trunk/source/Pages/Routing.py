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

def applySettings():
    def goNext(_):
        print _
        return WebUtils.system('/etc/init.d/quagga restart')
    print "Reconfiguring..."

    return WebUtils.system('/usr/local/tcs/tums/configurator --quagga --debnet').addCallbacks(goNext, goNext)

class AddNeigh(Tools.Page):
    def __init__(self, avatarId, db, asn = None, *a, **kw):
        self.asn  = asn
        Tools.Page.__init__(self, avatarId, db, *a, **kw)

    def form_neigh(self, data):
        form = formal.Form()

        form.addField('ip', formal.String(required=True, validators=[PageHelpers.IPValidator()]), label = "Remote IP")
        form.addField('asn', formal.String(), label = "Remote AS", description="Remote AS number of peer. Leave blank for the same AS as this router")
        #form.addField('hold', formal.Integer(required=True), label = "Hold time", description="Override the Hold timer for this peer (default 120)")

        #form.data['hold'] = 120

        form.addField('multihop', formal.Boolean(), label = "EBGP Multihop", description="Set this if the peer is more than 1 hop away")

        form.addField('nexthop', formal.String(), label = "Next-Hop", 
           description="Set this to an IP if you want to rewrite the next-hop of routes coming in from this peer. This is useful for route servers.")

        form.addAction(self.submitNeigh)
        return form

    def submitNeigh(self, ctx, form, data):
        B = self.sysconf.BGP

        dta = {}#'hold': data['hold']}

        if data['asn']:
            dta['as'] = data['asn'].encode("ascii", "replace")

        if data['multihop']:
            dta['multihop'] = True

        if data['nexthop']:
            dta['nexthop'] = data['nexthop'].encode("ascii", "replace")

        B[self.asn]['neighbors'][data['ip'].encode("ascii", "replace")] = dta

        self.sysconf.BGP = B
        def next(_):
            return url.root.child('Routing')
        return applySettings().addCallback(next)
        
    def render_content(self, ctx, data):
        return ctx.tag[
            tags.h3["Add neighbor to AS ", self.asn],
            tags.directive('form neigh')
        ]

    def childFactory(self, ctx, segs):
        if not self.asn:
            return AddNeigh(self.avatarId, self.db, segs)
        return Tools.Page.childFactory(self, ctx, segs)

class AddNet(AddNeigh):
    def form_net(self, data):
        form = formal.Form()

        form.addField('cidr', formal.String(required=True), label = "Remote IP")

        form.addAction(self.submitNet)
        return form

    def submitNet(self, ctx, form, data):
        B = self.sysconf.BGP
        B[self.asn]['networks'].append(data['cidr'])
        self.sysconf.BGP = B
        def next(_):
            return url.root.child('Routing')
        return applySettings().addCallback(next)
        
    def render_content(self, ctx, data):
        return ctx.tag[
            tags.h3["Add network to AS ", self.asn],
            tags.directive('form net')
        ]

    def childFactory(self, ctx, segs):
        if not self.asn:
            return AddNet(self.avatarId, self.db, segs)
        return Tools.Page.childFactory(self, ctx, segs)


class RIPInterface(PageHelpers.DataTable):
    def getTable(self):
        headings = [('Domain', 'domain')]
        domains = self.sysconf.General.get('ripinterface', [])
        return headings, domains

    def addForm(self, form):
        ifs = []
        for i in Utils.getInterfaces():
            if 'eth' in i or 'tap' in i: # Only allow tap and eth binds...
                ifs.append((i, i))

        form.addField('iface', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = ifs), label = "Interface",)

    def returnAction(self, data):
        Utils.log.msg('%s added RIP interface %s' % (self.avatarId.username, repr(data)))
        return restartExim().addCallback(returnRoot)

class RIPPrefix(PageHelpers.DataTable):
    def getTable(self):
        headings = [('Network', 'network')]
        domains = self.sysconf.General.get('ripnetwork', [])
        return headings, domains

    def addForm(self, form):
        form.addField('network', formal.String(required=True, validators=[PageHelpers.IPMaskValidator()]), label = "Network")

    def returnAction(self, data):
        Utils.log.msg('%s added RIP network %s' % (self.avatarId.username, repr(data)))
        return restartExim().addCallback(returnRoot)


class Page(Tools.Page):
    addSlash = True

    def __init__(self, *a, **kw):
        Tools.Page.__init__(self, *a, **kw)
        
        self.ripInterface   = RIPInterface  (self, 'RIPInterface', 'interface', 'General', 'ripinterface')
        self.ripPrefix      = RIPPrefix     (self, 'RIPPrefix',    'network',   'General', 'ripnetwork')

    def childFactory(self, ctx, segs):  
        print segs
        if segs == "AddNeigh":
            return AddNeigh(self.avatarId, self.db)

        if segs == "AddNet":
            return AddNet(self.avatarId, self.db)

        return Tools.Page.childFactory(self, ctx, segs)

    def form_statroutes(self, data):
        form = formal.Form()

        form.addField('dest', formal.String(required=True, strip=True, validators=[PageHelpers.IPMaskValidator()]), label = "Destination network", description = "Destination network in CIDR or '0.0.0.0/0' for the default route.")
        form.addField('gate', formal.String(validators=[PageHelpers.IPValidator()]), label = "Gateway",   description = "Gateway to forward this network to")

        ifs = []
        for i in Utils.getInterfaces():
            if 'eth' or 'ppp': # Only allow ppp and eth binds...
                ifs.append((i, i))

        form.addField('device', formal.String(), 
            formal.widgetFactory(formal.SelectChoice, options = ifs), label = "Device", 
            description = "Device to forward this traffic to, or the interface to assign this route to")

        form.addAction(self.submitRoute)

        return form

    def submitRoute(self, ctx, form, data):
        eth = self.sysconf.EthernetDevices
        target = None
        destination = data['dest'].encode("ascii", "replace").lower()
        if data['gate']:
            gateway = data['gate'].encode("ascii", "replace")
            if data['device']:
                target = data['device'].encode("ascii", "replace")
        else:
            gateway = data['device'].encode("ascii", "replace")

        if '0.0.0.0/0' in destination:
            destination = 'default'

        if destination == 'default':
            # Purge existing default routes, if any
            for dev, items in eth.items():
                oldRoutes = items.get('routes', [])
                newRoutes = []
                for dst, gw in oldRoutes:
                    if dst == "default":
                        continue
                    newRoutes.append((dst, gw))
                eth[dev]['routes'] = newRoutes

        if (not target) and data['gate']:
            # Dunno where to go... Look at gateway and make an intelligent choice
            for iface, net in Utils.getLanNetworks(self.sysconf).items():
                print data['gate']
                if Utils.matchIP(net, gateway):
                    # Gateway matches this interface local-link
                    target = iface
        if not target:
            # Still nothing, go for broke - these will be added to Quagga anyways
            target = Utils.getLans(self.sysconf)[0]

        routes = eth[target].get('routes', [])
        routes.append((destination, gateway))
        
        eth[target]['routes'] = routes
        self.sysconf.EthernetDevices = eth

        def next(_):
            return url.root.child('Routing')
        return applySettings().addCallback(next)

    def form_bgp(self, data):
        form = formal.Form()

        form.addField('as', formal.String(required=True), label = "AS Number")

        form.addField('id', formal.String(required=True, strip=True, validators=[PageHelpers.IPValidator()]), label = "Router ID", description = "IP that is used to peered with this router")

        form.addAction(self.submitAS)
        return form

    def submitAS(self, ctx, form, data):
        B = self.sysconf.BGP
        
        if B.get(data['as'].encode("ascii", "replace"), False):
            B[data['as'].encode("ascii", "replace")]['router-id'] = data['id'].encode("ascii", "replace")
        else:
            B[data['as'].encode("ascii", "replace")] = {
                'networks': [],
                'neighbors': {},
                'router-id': data['id'].encode("ascii", "replace")
            }
        self.sysconf.BGP = B
        WebUtils.system(Settings.BaseDir+'/configurator --quagga')
        return url.root.child('Routing')

    def form_parp(self, data):
        form = formal.Form()

        ifs = []
        for i in Utils.getInterfaces():
            if 'eth' in i or 'tap' in i: # Only allow tap and eth binds...
                ifs.append((i, i))

        form.addField('ip', formal.String(required=True, strip=True, validators=[PageHelpers.IPValidator()]), label = "IP Address")

        form.addField('extif', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = ifs), label = "External Interface", 
            description = "The interface where this server will advertise availability of this IP address")

        form.addField('intif', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = ifs), label = "Internal Interface", 
            description = "The interface to which this IP address will be routed (Where the server binding this IP address is)")

        form.addAction(self.submitProxyARP)
        return form

    def submitProxyARP(self, ctx, form, data):
        B = self.sysconf.Shorewall
        
        if B.get('proxyarp', False):
            B['proxyarp'].append([data['ip'].encode("ascii", "replace"), data['intif'].encode("ascii", "replace"), data['extif'].encode("ascii", "replace")])
        else:
            B['proxyarp'] = [[data['ip'].encode("ascii", "replace"), data['intif'].encode("ascii", "replace"), data['extif'].encode("ascii", "replace")]]

        self.sysconf.Shorewall = B
        WebUtils.system(Settings.BaseDir+'/configurator --shorewall; shorewall restart')
        return url.root.child('Routing')

    def form_balance(self, data):
        form = formal.Form()
        zones = [(zo,zo) for zo in self.sysconf.Shorewall.get('zones', {}).keys()] # Build something we can se for drop downs

        form.addField('zone', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = zones), label = "Zone")

        form.addField('gateway', formal.String(), label = "Gateway", 
            description = "Gateway for this network. Not required, but highly recommended whenever possible.")

        form.addField('track', formal.Boolean(), label = "Track",
            description = "Track connections so that sessions are routed out of the same interface they came in. (Recommended)")

        form.addField('balance', formal.Boolean(), label = "Load Balance", 
            description = "Perform load balancing between this zone and any others marked for load balancing.")

        form.addField('loose', formal.Boolean(), label = "Allow Spoofing",
            description = "Don't force source routes to be added for this zone. Only use this if your upstream does not mind spoofed packets such as if you are a properly multihomed site. (Not Recommended)")

        form.data['track'] = True

        form.addAction(self.submitBalance)
        return form

    def submitBalance(self, ctx, form, data):
        opts = []
        if data['track']:
            opts.append("track")
        if data['balance']:
            opts.append("balance")
        if data['loose']:
            opts.append("loose")

        if data['gateway']:
            gateway = data['gateway']
        else:
            gateway = "-"

        balance = self.sysconf.ShorewallBalance

        balance.append([data['zone'].encode("ascii", "replace"), gateway, ','.join(opts)])

        self.sysconf.ShorewallBalance = balance

        def ok(_):
            return url.root.child('Routing')
        return WebUtils.system(Settings.BaseDir+'/configurator --shorewall; shorewall restart').addBoth(ok)

    def form_source(self, data):
        form = formal.Form()
        zones = []

        # Read zones available for balancing
        i = 1
        for bal in self.sysconf.ShorewallBalance:
            zones.append((i, bal[0]))
            i+= 1

        protocols = [
            ('-', 'Any'),
            ('tcp', 'TCP'),
            ('udp', 'UDP'),
            ('47', 'PPTP'),
            ('icmp', 'ICMP')
        ]

        form.addField('zone', formal.Integer(required=True), formal.widgetFactory(formal.SelectChoice, options = zones), 
            label = "Destination Zone",
            description = "Route packets matching this rule to this zone")

        form.addField('source', formal.String(), label = "Source", description = "Source CIDR network or IP. For anywhere leave blank.")

        form.addField('dest',   formal.String(), label = "Destination", description = "Destination CIDR network or IP. For anywhere leave blank.")

        form.addField('protocol', formal.String(required=True),formal.widgetFactory(formal.SelectChoice, options = protocols), label = "Protocol")
        form.addField('port', formal.String(), label = "Port", description = "TCP/UDP port, or sub-protocol type. Leave blank for a source-only policy")

        form.addAction(self.submitSource)
        return form

    def submitSource(self, ctx, form, data):
        if data['source']:
            source = data['source'].encode("ascii", "replace")
        else:
            source = '0.0.0.0/0'

        if data['dest']:
            dest = data['dest'].encode("ascii", "replace")
        else:
            dest = '0.0.0.0/0'

        if data['port']:
            port = data['port'].encode("ascii", "replace")
        else:
            port = '-'
    
        rule = "%s:P    %s      %s      %s      %s" % (
            data['zone'], 
            source,
            dest,
            data['protocol'].encode("ascii", "replace"), 
            port
        )

        rules = self.sysconf.ShaperRules
        rules.append(rule)
        self.sysconf.ShaperRules = rules

        WebUtils.system(Settings.BaseDir+'/configurator --shorewall; shorewall restart')
        return url.root.child('Routing')

    def render_routingTable(self, ctx, data):
        def formatTable(routes):
            rtab = []
            for l in routes.split('\n'):
                if not l.strip():
                    continue
                ln = l.split()
                src = ln[0]
                data = {'via': '', 'device': '', 'type': ''}
                t = ""
                for n in ln:
                    if t:
                        data[t] = n
                    if n == 'via':
                        t = 'via'
                        data['type'] = "Static"
                    elif n == 'dev':
                        t = 'device'
                        if not data['type']:
                            data['type'] = "Connected"
                    else:
                        t = ""
            
                print data
                if "kernel" in l:
                    data['type'] = "System"

                rtab.append([
                    src, 
                    data['via'],
                    data['device'],
                    data['type'],
                ])
            return ctx.tag[
                PageHelpers.dataTable(['Destination', 'Next hop', 'Interface', 'Type'], rtab),
            ]
        return WebUtils.system('ip ro').addBoth(formatTable)

    def render_content(self, ctx, data):
        routes = []
        i = 0

        for iface, vals in self.sysconf.EthernetDevices.items():
            for ro in vals.get('routes', []):
                i+= 1
                routes.append((ro[0], ro[1], iface, tags.a(href="Delete/%s" % i)[tags.img(src="/images/ex.png")]))

        balances = []
        zones = []
        num = 0 
        for bal in self.sysconf.ShorewallBalance:
            if "-" in bal[1]:
                gateway = "" # Detect gateway
            else:
                gateway = bal[1]
            zones.append(bal[0])
            balances.append([
                bal[0], 
                gateway, 
                'balance' in bal[2], 
                'track' in bal[2], 
                'loose' in bal[2],
                tags.a(href="DeleteBalance/%s" % num)[tags.img(src="/images/ex.png")]
            ])
            num += 1 

        sourceroutes = []
        num = 0
        for src in self.sysconf.ShaperRules:
            rules = src.split()
            print rules, zones
            try:
                zone = zones[int(rules[0].split(':')[0])-1] # Read the zone from the mark
            except:
                zone = "Mark "+ rules[0].split(':')[0]

            source = rules[1]

            if rules[2] == "0.0.0.0/0":
                dest = "any"
            else:
                dest = rules[2]

            protocol = rules[3]

            port  = rules[4]

            sourceroutes.append([
                zone,
                source, 
                dest, 
                protocol, 
                port,
                tags.a(href="DeleteSource/%s" % num)[tags.img(src="/images/ex.png")]
            ])
            num += 1

        return ctx.tag[
            tags.table(width="100%")[
                tags.tr[
                    tags.td(align="left")[tags.h3[tags.img(src="/images/netflow.png"), " IP Routing"]],
                    tags.td(align='right')[tags.a(id="advBtn", href="#", onclick="setAdvanced('routing', true);")["Advanced"]]
                ]
            ],
            PageHelpers.TabSwitcher((
                ('Static Routes', 'panelStatic'),
                ('BGP', 'panelBGP'), 
                ('RIP', 'panelRIP'), 
                ('Connections', 'panelBalance'), 
                ('Policy Routing', 'panelSource'), 
                ('Proxy ARP', 'panelParp'),
                ('Routing Table', 'panelTable'),
                #('IPv6 Tunnel', 'panelTunnel')
            )),
            tags.div(id="panelTable", _class="tabPane")[
                tags.h3["Routing Table"], 
                tags.invisible(render=tags.directive('routingTable'))
            ],
            tags.div(id="panelBalance", _class="tabPane")[
                tags.h3["Load Balancing"],
                PageHelpers.dataTable(['Zone', 'Gateway', 'Load Balance', 'Tracking', 'Soft Routes', ''], balances, sortable=True),
                tags.h3["Add Connection"],
                tags.directive('form balance')
            ],
            tags.div(id="panelSource", _class="tabPane")[
                tags.h3["Policy Routes"],
                PageHelpers.dataTable(['Zone', 'Source', 'Destination', 'Protocol', 'Port/SubService', ''], sourceroutes, sortable=True),
                tags.h3["Add source route"],
                tags.directive('form source')
            ],
            tags.div(id="panelStatic", _class="tabPane")[
                tags.h3["Static Routes"],
                PageHelpers.dataTable(['Destination', 'Gateway', 'Device', ''], routes, sortable=True),
                tags.h3["Add route"],
                tags.directive('form statroutes')
            ],
            tags.div(id="panelParp", _class="tabPane")[
                tags.h3["Proxy ARP"],
                tags.p[
                    "Proxy ARP allows you to forward external IP addresses to internal machines as ",
                    "if they were routable. This server will respond to ARP requests for all interfaces",
                    "on all interfaces and those listed here. You should use this if your ISP allocates ",
                    "you a subnet of IP addresses and you wish to make use of one on a machine in a DMZ",
                    "or local LAN from this gateway. Use a DNAT block in the firewall if you wish to simply forward ports."
                ],
                PageHelpers.dataTable(['IP', 'External', 'Internal', ''], [
                    [ 
                        i[0],
                        i[2],
                        i[1],
                        tags.a(href="Delparp/%s/" % i[0])[tags.img(src="/images/ex.png")]
                    ]
                    for i in self.sysconf.Shorewall.get('proxyarp', {})
                ], sortable=True),
                tags.h3["Add Proxy ARP"],
                tags.directive('form parp')
            ],
            tags.div(id="panelRIP", _class="tabPane")[
                tags.h3["RIP"], 

                tags.strong["Interfaces"],
                self.ripInterface.applyTable(self),

                tags.strong["Networks"], 
                self.ripPrefix.applyTable(self)
            ],
            tags.div(id="panelBGP", _class="tabPane")[
                [
                    [
                        tags.h3["AS ",asn],
                        tags.a(href="Delas/%s/%s" % (asn, i))[tags.img(src="/images/ex.png"), " Delete Router AS ", asn],
                        tags.br, tags.br,
                        tags.table(valign="top")[
                            tags.tr(valign="top")[
                                tags.td["ID: "], tags.td[det['router-id']]
                            ],
                            tags.tr(valign="top")[
                                tags.td["Neighbors: "], tags.td[
                                    PageHelpers.dataTable(['Remote', 'AS', 'Multi-hop','Next-Hop', ''],
                                    [
                                     [
                                        i,
                                        negh.get('as', asn),
                                        negh.get('multihop', False) and 'Yes' or 'No',
                                        negh.get('nexthop', False) or 'Peer',
                                        tags.a(href="Delneigh/%s/%s" % (asn, i))[tags.img(src="/images/ex.png")]
                                     ] for i,negh in det.get('neighbors', {}).items()],
                                    sortable=True),
                                    tags.a(href="AddNeigh/%s/" % asn)["Add Neighbor"],
                                    tags.br,
                                ]
                            ],
                            tags.tr(valign="top")[
                                tags.td["Networks: "], tags.td[
                                    PageHelpers.dataTable(['Netmask', ''],
                                    [[
                                        i, 
                                        tags.a(href="Delnet/%s/%s" % (asn, i.replace('/','+')))[tags.img(src="/images/ex.png")],
                                    ] for i in det.get('networks', [])], sortable=True),
                                    tags.a(href="AddNet/%s/" % asn)["Add Network"]
                                ]
                            ]
                        ]
                    ]
                for asn,det in self.sysconf.BGP.items()],
                tags.h3["Add AS"],
                tags.directive('form bgp')
            ],
            #tags.div(id="panelTunnel", _class="tabPane")[
            #    tags.h3["Configure IPv6 Tunnel"],
            #    tags.directive('form tunnelConf')
            #],
            PageHelpers.LoadTabSwitcher(),
        ]

    def locateChild(self, ctx, segs):

        if segs[0]=="Delparp":
            rules = self.sysconf.Shorewall

            parp = rules.get('proxyarp', {})
            newarp = []
            for i in parp:
                if i[0] != segs[1]:
                    newarp.append(i)
            rules['proxyarp'] = newarp            
            self.sysconf.Shorewall = rules
            WebUtils.system(Settings.BaseDir+'/configurator --shorewall; shorewall restart')
            return url.root.child('Routing'), ()

        if segs[0]=="DeleteBalance":
            rulenum = int(segs[1])
            rules = self.sysconf.ShorewallBalance

            del rules[rulenum]

            self.sysconf.ShorewallBalance = rules

            WebUtils.system(Settings.BaseDir+'/configurator --shorewall; shorewall restart')
            return url.root.child('Routing'), ()

        if segs[0]=="DeleteSource":
            rulenum = int(segs[1])
            rules = self.sysconf.ShaperRules

            del rules[rulenum]

            self.sysconf.ShaperRules = rules

            WebUtils.system(Settings.BaseDir+'/configurator --shorewall; shorewall restart')
            return url.root.child('Routing'), ()

        if segs[0]=="Delete":
            # Delete static route
            eth = self.sysconf.EthernetDevices
            
            i = 0 
            deleted = None

            for iface, vals in self.sysconf.EthernetDevices.items():
                if deleted:
                    continue
                routes = []
                for ro in vals.get('routes', []):
                    i+= 1
                    if i != int(segs[1]):
                        routes.append(ro)
                    else:
                        deleted = ro
                
                if deleted: 
                    # Was achange previously
                    c = self.sysconf.EthernetDevices
                    
                    c[iface]['routes'] = routes
                    
                    self.sysconf.EthernetDevices = c 

                    routes.append(ro)

            if deleted:
                WebUtils.system('ip ro del %s via %s' % ro)

            def next(_):
                return url.root.child('Routing')
            return applySettings().addCallback(next), ()
        
        if segs[0] == "Delnet":
            B = self.sysconf.BGP
            net = segs[2].replace('+', '/')
            newnets = []
            for i in B[segs[1]]['networks']:
                if i != net:
                    newnets.append(i)
            B[segs[1]]['networks'] = newnets
            self.sysconf.BGP = B
            def next(_):
                return url.root.child('Routing')
            return applySettings().addCallback(next), ()
        

        if segs[0] == "Delneigh":
            B = self.sysconf.BGP
            del B[segs[1]]['neighbors'][segs[2]]
            self.sysconf.BGP = B
            def next(_):
                return url.root.child('Routing')
            return applySettings().addCallback(next), ()
            
            return url.root.child('Routing'), ()

        if segs[0] == "Delas":
            B = self.sysconf.BGP
            del B[segs[1]]
            self.sysconf.BGP = B
            def next(_):
                return url.root.child('Routing')
            return applySettings().addCallback(next), ()

        return rend.Page.locateChild(self, ctx, segs)
                

from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
import time, formal, LDAP, os
import Tree, Settings
from Core import PageHelpers, Shorewall, confparse, Utils, WebUtils
from Pages import Users, Tools

class Page(PageHelpers.DefaultPage):
    rules = Shorewall.Rules()

    protocols = [('tcp', 'TCP'),
                 ('udp', 'UDP'),
                 ('47', 'PPTP')]

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Tools"]]

    def getZones(self):
        zones = self.sysconf.Shorewall.get('zones', {})
        return [(zo,zo) for zo in zones.keys()] # Build something we can se for drop downs

    def form_addZone(self, data):
        form = formal.Form()

        form.addField('zone', formal.String(required=True), label = "Zone name", description = "The name of this zone")

        form.addField('policy', formal.String(required=True),  formal.widgetFactory(formal.SelectChoice, options = [
                ('ACCEPT', 'ACCEPT'),
                ('DROP', 'DROP')
            ]), label = "Policy", 
            description = "The default action to take on traffic not matching any rule")

        form.addField('log', formal.String(), label = "Log", description = "Advanced: Logging target for dropped packets. Usualy $log if policy is ACCEPT")

        form.addField('interfaces', formal.String(), label = "Interface members", description = "Advanced: Comma separated list of interface defenitions.")
        
        form.addAction(self.submitZone)

        return form

    def submitZone(self, ctx, form, data):
        k = self.sysconf.Shorewall
        # Make a zone def if there isn't one
        if not k.get('zones', None):
            k['zones'] = {}

        if data['zone'] in k.get('zones', {}):
            del k['zones'][data['zone']]

        if data['interfaces']:
            ifs = data['interfaces'].split(',')
        else:
            ifs = []
        zone = {
            'policy': data['policy'],
            'log' : data['log'] or '',
            'interfaces': []
        }
        
        k['zones'][data['zone']] = zone

        self.sysconf.Shorewall = k 
            

    def form_allowRange(self, data):
        form = formal.Form()
        form.addField('sourceip', formal.String(required=True), label = "Source IP", description = "Source IP address of connecting host or network")
        #form.addField('destip', formal.String(), label = "Destination IP", description = "Destination IP address or network (Leave blank for ANY)")
        form.addField('zone', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = self.getZones()), label = "Zone")
        form.data['zone']="net"

        form.addAction(self.submitAllowRange)

        return form

    def submitAllowRange(self, ctx, form, data):
        self.rules.addRule("AIP", self.rules.buildRule("AIP", data['zone'], data['sourceip']))
        return url.root.child('Firewall')

    def form_allowPort(self, data):
        form = formal.Form()
        form.addField('destport', formal.String(required=True), label = "Destination Port", description = "TCP/UDP port to permit")
        form.addField('destip', formal.String(), label = "Destination IP", description = "Destination IP address or network (Leave blank for ANY)")
        form.addField('proto', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = self.protocols), label = "Protocol")
        form.data['proto'] = 'tcp'
        form.addField('zone', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = self.getZones()), label = "Zone")
        form.data['zone']="net"
        form.addAction(self.submitAllowPort)

        return form

    def submitAllowPort(self, ctx, form, data):
        self.rules.addRule("APORT", self.rules.buildRule("APORT", data['zone'], data['proto'], data['destport'], data['destip']))
        return url.root.child('Firewall')

    def form_forwardPort(self, data):
        form = formal.Form()
        form.addField('port', formal.String(), label = "Port", description = "TCP/UDP port to forward. Blank for protocol forward (like PPTP).")
        form.addField('destip', formal.String(required=True), label = "Target IP", description = "Destination IP address to forward to")
        form.addField('dstport', formal.String(), label = "Target Port", description = "TCP/UDP port to forward to. Blank for the same port.")
        form.addField('sourceip', formal.String(), label = "Destination IP", description = "External IP to forward from")
        form.addField('proto', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = self.protocols), label = "Protocol")
        form.data['proto'] = 'tcp'
        
        form.addAction(self.submitForwardPort)
        return form

    def submitForwardPort(self, ctx, form, data):
        if not data['dstport']:
            data['dstport'] = ""
        self.rules.addRule("FORWARD", self.rules.buildRule("FORWARD", data['destip'], data['proto'], data['port'], data['dstport'], data['sourceip']))
        return url.root.child('Firewall')

    def form_transProxy(self, data):
        form = formal.Form()
        form.addField('sourceip', formal.String(), label = "Source IP", description=["Source IP address of connecting host or network (Leave blank for ANY)."
        " This is usually a source host or network you want to exclude."])
        form.addField('destip', formal.String(), label = "Destination IP", description = ["Destination IP address or network (Leave blank for ANY). ", 
        "This is usually the opposite (!) of your local network.", "This is NOT the server you'd like to proxy to."])
        form.addField('srcport', formal.String(), label = "Source port", description = "TCP/UDP port to catch.")
        form.addField('dstport', formal.String(), label = "Destination port", description = "TCP/UDP port to forward to.")
        form.addField('proto', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = self.protocols), label = "Protocol")
        form.data['proto'] = 'tcp'
        form.addAction(self.submitTransProxy)

        return form

    def submitTransProxy(self, ctx, form, data):
        if data['sourceip']:
            source = ":%s" % data['sourceip']
        else:
            source = ""
        self.rules.addRule("PROXY", self.rules.buildRule("PROXY", source, data['dstport'], data['proto'], data['srcport'], data['destip']))
        return url.root.child('Firewall')

    def restartShorewall(self):
        WebUtils.system(Settings.BaseDir+'/configurator --shorewall; shorewall restart')

    def locateChild(self, ctx, segs):
        if segs[0]=="Delete":
            if segs[1] == 'Zone':
                k = self.sysconf.Shorewall
                if segs[2] in k.get('zones', {}):
                    del k['zones'][segs[2]]
                self.sysconf.Shorewall = k
            else:
                self.rules.deleteRule(segs[1], int(segs[2]))
            return url.root.child('Firewall'), ()
        if segs[0]=="Restart":
            self.restartShorewall()
            return url.root.child('Firewall'), ()
        return rend.Page.locateChild(self, ctx, segs)
        
    def getRules(self):
        return None

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Tools.Page.sideMenu(Tools.Page(None, self.db), ctx, data)]

    def render_content(self, ctx, data):
        rules = self.rules.read()
        return ctx.tag[
                tags.h2[tags.img(src="/images/firewall.png"), " Firewall"],
                tags.img(src="/images/refresh.png"),
                tags.a(
                    href="Restart", 
                    style="font-size:12pt;", 
                    title="Restart the firewall and apply the changes. Changes are only activated after this is clicked."
                )[tags.strong["Apply Changes"]],
                PageHelpers.TabSwitcher((
                    ('Allow IP'          , 'panelAllowIP'),
                    ('Allow Ports'       , 'panelAllowPort'),
                    ('Forward Ports'     , 'panelForwardPort'),
                    ('Transparent Proxy' , 'panelTransparentProxy'),
                    ('Firewall Zones'    , 'panelZones'),
                )),

                tags.div(id="panelAllowIP", _class="tabPane")[
                    tags.h3["Allowed IP addresses and networks"], 
                    PageHelpers.dataTable(['Network Zone', 'Source IP', ''], [ 
                        r + [tags.a(
                            href="Delete/AIP/%s/"%(i), 
                            onclick="return confirm('Are you sure you want to delete this entry?');",
                            title="Delete this allowed IP range"
                        )[tags.img(src="/images/ex.png")]]
                    for i,r in enumerate(rules['AIP'])]),
                    tags.h3["Add rule"],
                    tags.directive('form allowRange'),
                ],

                tags.div(id="panelAllowPort", _class="tabPane")[
                    tags.h3["Allowed ports"],
                    PageHelpers.dataTable(['Network Zone', 'Protocol', 'Port', 'Destination IP', ''], [
                        r + [tags.a(
                            href="Delete/APORT/%s/"%(i), 
                            title="Delete this allowed port",
                            onclick="return confirm('Are you sure you want to delete this entry?');"
                        )[tags.img(src="/images/ex.png")]]
                    for i,r in enumerate(rules['APORT'])]),
                    tags.h3["Add port rule"],
                    tags.directive('form allowPort'),
                ],

                tags.div(id="panelForwardPort", _class="tabPane")[
                    tags.h3["Forwarded ports"],
                    PageHelpers.dataTable(['Forward To', 'Protocol', 'Port', 'Destination IP', ''], [
                        r + [tags.a(
                            href="Delete/FORWARD/%s/"%(i), 
                            title="Delete this port forwarding rule",
                            onclick="return confirm('Are you sure you want to delete this entry?');"
                        )[tags.img(src="/images/ex.png")]]
                    for i,r in enumerate(rules['FORWARD'])]),
                    tags.h3["Add port forward"],
                    tags.directive('form forwardPort'),
                ],

                tags.div(id="panelTransparentProxy", _class="tabPane")[
                    tags.h3["Transparent Proxies"],
                    PageHelpers.dataTable(['Source Network', 'Destination Port', 'Source Port', 'Protocol', 'Destination Network', ''], [
                        r + [tags.a(
                            href="Delete/PROXY/%s/"%(i), 
                            title="Delete this transparent redirection rule",
                            onclick="return confirm('Are you sure you want to delete this entry?');"
                        )[tags.img(src="/images/ex.png")]]
                    for i,r in enumerate(rules['PROXY'])]),
                    tags.h3["Add proxy"],
                    tags.directive('form transProxy'),
                ],

                tags.div(id="panelZones", _class="tabPane")[
                    tags.h3["Zones"],
                    PageHelpers.dataTable(['Zone Name', 'Policy', 'Log target', 'Interfaces', ''], 
                        [
                            [
                                zone, zd['policy'], zd['log'], [[i, tags.br] for i in zd['interfaces']],
                                tags.a(
                                    href="Delete/Zone/%s/"%(zone),
                                    title="Delete this firewall zone",
                                    onclick="return confirm('Are you sure you want to delete this zone?');"
                                )[tags.img(src="/images/ex.png")]
                            ] 
                        for zone, zd in self.sysconf.Shorewall.get('zones', {}).items()]
                    ),
                    tags.h3['Add zone'],
                    tags.directive('form addZone')
                ],
            PageHelpers.LoadTabSwitcher()
        ]

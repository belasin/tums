from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan, athena
from nevow.taglibrary import tabbedPane
import time, formal, LDAP, os, re
import Tree, Settings
from Core import PageHelpers, Shorewall, confparse, Utils, WebUtils
from Pages import Tools

from twisted.python import log

def getFirewallRules(rules):
        securityViolation = None
        rules = rules.read()
        rows = []

        ### Read firewall rules table 
        for ru in rules['AIP']:
            # SSH and Vulani access violation
            if ru[7] in ["22", "9682"]:
                if (ru[2] == "Any") and ((ru[1] in ["net", "Any", "dsl", "ppp", "wan", "net2"]) or (ru[4] == "fw")):
                    securityViolation = "Inbound SSH and/or Vulani administrative access should not be unrestricted! "
                    securityViolation += "Your system security has been seriously compromised. Please remove this "
                    securityViolation += "rule and restrict the source IP or make use of the VPN to administer the server remotely"

            r = [
                ru[0],
                '<strong>Source<br/>Destination</strong>',
                "%s<br/>%s" % (
                    ru[1], # Source zone
                    ru[4] # Dst Zone
                ), 
                "%s<br/>%s" % (
                    ru[3].replace('-', 'Any'), # Source port
                    ru[7].replace('-', 'Any') # Dest Port
                ),
                "%s<br/>%s" % (
                    ru[2], # Source IP
                    ru[5] # Dest IP
                ),
                ru[6].replace('-', 'Any'),
                """<a href="Delete/rules/%s/" onclick="return confirm(\'Are you sure you want to delete this rule?\');" title="Delete rule.">
                <img src="/images/ex.png"/></a>""" % ru[8]
            ]
            rows.append([unicode(j) for j in r])

        # Construct firewall table
        return rows, securityViolation

class TestPage(Tools.Page):
    def render_content(self, ctx, data):
        Utils.log.msg('%s tested firewall configuration' % (self.avatarId.username))
        def Result(result):
            errors = []
            for i in result.split('\n'):
                if "ERROR" in i:
                    errors.append(tags.div(style='color:#F00')[i.strip()])

            if not errors:
                # Delete any potential error outputs
                WebUtils.system('rm /usr/local/tcs/tums/shorewallBroken > /dev/null 2>&1 ')

            return ctx.tag[
                tags.h3["Firewall Test Results"], 
                errors or "No Errors",
                tags.br,
                tags.br,
                tags.a(href=url.root.child('Firewall'))['Back to firewall configuration']
            ]

        return WebUtils.system('/usr/local/tcs/tums/configurator --shorewall; shorewall check').addCallback(Result)

class ZoneMemberList(PageHelpers.DataTable):
    def __init__(self, page, name, description, zone):
        PageHelpers.DataTable.__init__(self, page, name, description)
        self.zone = zone
    
    def getTable(self):
        data = []
        ifaces = self.sysconf.Shorewall['zones'].get(self.zone, {}).get('interfaces', [])
        
        for i in ifaces:
            tline = [i.split()[0]]
            if 'dhcp' in i:
                tline.append('yes') 
            else:
                tline.append('no')

            if 'routeback' in i:
                tline.append('yes')
            else:
                tline.append('no')

            data.append(tline)

        headings = [("Interface", 'iface'), ("Dhcp", 'dhcp'), ("Route-back", 'routeback')]
        return headings, data

    def addForm(self, form):
        ifaces = [(i,i) for i in Utils.getInterfaces()]

        form.addField('iface', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = ifaces), label = "Interface")
        form.addField('dhcp', formal.Boolean(), label = "DHCP", description="Check this if DHCP is performed on this interface")
        form.addField('routeback', formal.Boolean(), label = "Route-back", description = "Check this if route reflection is allowed on this interface")

        form.data['iface'] = ifaces[0][0]

    def addAction(self, data):
        Utils.log.msg('%s added interface to zone %s => %s' % (self.avatarId.username, self.zone, repr(data)))

        options = []
        if data['dhcp']:
            options.append('dhcp')
        if data['routeback']:
            options.append('routeback')

        ln = "%s detect %s" % (data['iface'].encode("ascii", "replace"), ','.join(options))

        shr = self.sysconf.Shorewall
        shr['zones'][self.zone]['interfaces'].append(ln)
        self.sysconf.Shorewall = shr

    def deleteItem(self, item):
        shr = self.sysconf.Shorewall
        del shr['zones'][self.zone]['interfaces'][item]
        self.sysconf.Shorewall = shr

    def returnAction(self, data):
        return url.root.child('Firewall').child('EditZone').child(self.zone)

class EditPage(Tools.Page):
    def __init__(self, avatarId, db, zone=None, *a, **kw):
        PageHelpers.DefaultPage.__init__(self, avatarId, db, *a, **kw)
        self.zone = zone
        self.interfaceList = ZoneMemberList(self, 'ZoneMemberList', 'interface', self.zone)

    def childFactory(self, ctx, segs):
        if not self.zone:
            return EditPage(self.avatarId, self.db, segs)
        return Tools.Page.childFactory(self, ctx, segs)

    def form_confZone(self, data):
        form = formal.Form()

        form.addField('policy', formal.String(required=True),  formal.widgetFactory(formal.SelectChoice, options = [
                ('ACCEPT', 'ACCEPT'),
                ('DROP', 'DROP')
            ]), label = "Policy", 
            description = "The default action to take on traffic not matching any rule")

        form.addField('log', formal.String(), label = "Log", description = "Advanced: Logging target for dropped packets. Usualy $log if policy is ACCEPT")

        form.addAction(self.confZone)

        k = self.sysconf.Shorewall
        zdef = k.get('zones', {}).get(self.zone)
        form.data['log'] = zdef.get('log', '')
        form.data['policy'] = zdef.get('policy', '')

        return form

    def confZone(self, c, f, data):
        Utils.log.msg('%s modified firewall zone %s' % (self.avatarId.username, self.zone))
        k = self.sysconf.Shorewall

        k['zones'][self.zone]['policy'] = data['policy'].encode("ascii", "replace")
        k['zones'][self.zone]['log'] = data['log'] or ''

        self.sysconf.Shorewall = k 
 
        return url.root.child('Firewall')
        

    def render_content(self, ctx, data):

        return ctx.tag[
            tags.h3[tags.img(src="/images/dhcp.png"), " Edit Zone %s" % self.zone],
            PageHelpers.TabSwitcher((
                ('Settings'          , 'panelConfig'),
                ('Members'       , 'panelMembers'),
            ), id = "zones"),
            tags.div(id="panelConfig", _class="tabPane")[
                tags.directive("form confZone")
            ],
            tags.div(id="panelMembers", _class="tabPane")[
                self.interfaceList.applyTable(self)
            ],
            PageHelpers.LoadTabSwitcher(id="zones")
        ]

class RulesTable(PageHelpers.TableWidget):

    def getData(self):
        rules = Shorewall.Rules()
        fwtable, securityViolation = getFirewallRules(rules)

        return fwtable, [
            u'Rule',
            u'',
            u'Zone',
            u'Port',
            u'IP',
            u'Protocol',
            u''
        ]
    athena.expose(getData)

    def tableChanged(self, rowOrder):
        sh = self.sysconf.Shorewall
        rules = sh.get('rules')
        newRules = []
        for i in rowOrder:
            newRules.append(rules[i])

        sh['rules'] = newRules
        self.sysconf.Shorewall = sh
        # Reload remote end
        return self.callRemote('renderTable')

    athena.expose(tableChanged)

class Page(PageHelpers.DefaultAthena):
    rules = Shorewall.Rules()
    largestRule = 0
    protocols = [
                 ('-',   'Any'),
                 ('tcp', 'TCP'),
                 ('udp', 'UDP'),
                 ('47', 'PPTP'),
                 ('icmp', 'ICMP')
                ]

    docFactory = loaders.xmlfile('firewall.xml', templateDir = Settings.BaseDir + '/templates')

    moduleName = 'tableWidget'
    moduleScript = 'tableWidget.js'
    
    addSlash = True


    def render_tableWidget(self, ctx, data):
        f = RulesTable()
        f.setFragmentParent(self)
        return ctx.tag[f]

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2[tags.img(src='/images/tools-lg.png'), " Tools"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Tools.Page.sideMenu(Tools.Page(None, self.db), ctx, data)]

    def childFactory(self, ctx, seg):
        if seg=="EditZone":
            return EditPage(self.avatarId, self.db)

        if 'Test' in seg:
            return TestPage(self.avatarId, self.db)

        return PageHelpers.DefaultAthena.childFactory(self, ctx, seg)

    def testProxy(self):
        transwww = self.sysconf.Shorewall.get('redirect', [])

        for en, ru in transwww:
            if "REDIRECT" in ru and "tcp" in ru and "80" in ru:
                return True

    def removeProxy(self):
        transwww = self.sysconf.Shorewall
        newRules = []
        for en, ru in transwww.get('redirect', []):
            if "REDIRECT" in ru and "tcp" in ru and "80" in ru and "8080" in ru:
                print "clipping"
            else:
                newRules.append([en, ru])

        transwww['redirect'] = newRules
        self.sysconf.Shorewall = transwww

    def addProxy(self):
        transwww = self.sysconf.Shorewall
        net = [i for j,i in Utils.getLanNetworks(self.sysconf).items()][0]

        if not transwww.get('redirect'):
            transwww['redirect'] = []

        transwww['redirect'].append([
            1, "REDIRECT loc      8080     tcp     80      -     !%s" % (net)
        ])
        self.sysconf.Shorewall = transwww

    def form_inetPol(self, data):
        form = formal.Form()
        if os.path.exists('/lib/iptables/libipt_ipp2p.so'):
            form.addField('blockp2p', formal.Boolean(), label = "Block P2P")

        form.addField('transProxy', formal.Boolean(), label = "Web transparent proxy",
            description = "Transparently proxy all web traffic")
        form.addField('blockAll', formal.Boolean(), label = "Block LAN -> Internet",
            description = "Block the LAN from accessing the internet directly. Web proxy access will still be permitted, as well as SMTP")

        try:
            lanpolicy = self.sysconf.Shorewall['zones']['loc']['policy']
            if lanpolicy != "ACCEPT":
                form.data['blockAll'] = True
        except:
            form.data['blockAll'] = False

        if self.testProxy():
            form.data['transProxy'] = True

        if self.sysconf.Shorewall.get('blockp2p', False):
            form.data['blockp2p'] = True

        form.addAction(self.submitPolicyForm)
        return form

    def submitPolicyForm(self, ctx, form, data):
        if data['transProxy'] and not self.testProxy():
            self.addProxy()
        if not data['transProxy']:
            self.removeProxy()

        shorewall = self.sysconf.Shorewall
        try:
            if data['blockAll']:
                lanpolicy = shorewall['zones']['loc']['policy'] = "DROP"
            else:
                lanpolicy = shorewall['zones']['loc']['policy'] = "ACCEPT"
        except:
            print "Failed to change loc zone"

        if data.get('blockp2p', False):
            shorewall['blockp2p'] = data['blockp2p']
        else:
            shorewall['blockp2p'] = False

        self.sysconf.Shorewall = shorewall
        WebUtils.system('/usr/local/tcs/tums/configurator --shorewall; shorewall restart')
        return url.root.child('Firewall')

    def form_addQos(self, data):
        tos = [
            ('16', 'Minimize Delay'),
            ('8',  'Maximize Throughput'),
            ('4',  'Maximize Reliability'),
            ('2',  'Minimize Cost'),
            ('0',  'Normal Service')
        ]
        form = formal.Form()
        protocols = [('tcp', 'TCP'),
                     ('udp', 'UDP'),
                     ('47', 'PPTP')]
        form.addField('port', formal.String(required=True, strip=True, validators=[PageHelpers.PortRangeValidator()]), label = "Port")
        form.addField('proto', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = protocols), label = "Protocol")
        form.addField('qos', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = tos), label = "Type of service")
        form.addAction(self.submitQosForm)

        return form

    def submitQosForm(self, ctx, form, data):
        conf = self.sysconf.Shorewall

        if conf.get('qos', None):
            conf['qos'].append((data['port'].encode("ascii", "replace"), data['proto'].encode("ascii", "replace"), data['qos'].encode("ascii", "replace")))
        else:
            conf['qos'] = [(data['port'].encode("ascii", "replace"), data['proto'].encode("ascii", "replace"), data['qos'].encode("ascii", "replace"))]

        self.sysconf.Shorewall = conf
        WebUtils.system('/usr/local/tcs/tums/configurator --shorewall')
        return url.root.child('Firewall')

    def getZones(self):
        zones = self.sysconf.Shorewall.get('zones', {})
        baseZones = [
            ("all", "Any"), 
            ('fw', "Firewall")
        ]
        if self.sysconf.ProxyConfig.get('captive'):
            for zo in Utils.getLanZones(self.sysconf):
                baseZones.append(("c%s" % zo, "Authenticted %s" % zo))
        return baseZones + [(zo,zo) for zo in zones.keys()] # Build something we can se for drop downs

    def form_addZone(self, data):
        form = formal.Form()

        form.addField('zone', formal.String(required=True), label = "Zone name", description = "The name of this zone")

        form.addField('policy', formal.String(required=True),  formal.widgetFactory(formal.SelectChoice, options = [
                ('ACCEPT', 'ACCEPT'),
                ('DROP', 'DROP')
            ]), label = "Policy", 
            description = "The default action to take on traffic not matching any rule")

        form.addField('log', formal.String(), label = "Log", description = "Advanced: Logging target for dropped packets. Usualy $log if policy is ACCEPT")

        #form.addField('interfaces', formal.String(), label = "Interface members", description = "Advanced: Comma separated list of interface defenitions.")

        form.data['policy'] = "ACCEPT"
        
        form.addAction(self.submitZone)

        return form

    def submitZone(self, ctx, form, data):
        Utils.log.msg('%s added a new firewall zone %s' % (self.avatarId.username, repr(data)))
        k = self.sysconf.Shorewall
        # Make a zone def if there isn't one
        if not k.get('zones', None):
            k['zones'] = {}

        if data['zone'] in k.get('zones', {}):
            del k['zones'][data['zone'].encode("ascii", "replace")]

        zone = {
            'policy': data['policy'],
            'log' : data['log'] or '',
            'interfaces': []
        }
        
        k['zones'][data['zone'].encode("ascii", "replace")] = zone

        self.sysconf.Shorewall = k 
            

    def form_allowRange(self, data):
        form = formal.Form()

        form.addField('action', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, 
            options = [
                ("ACCEPT", "Accept"),
                ("REJECT", "Reject")
            ]), label = "Action")

        # Source
        form.addField('sip', formal.String(), label = "Source IP", 
            description = "Source IP address of connecting host or network (Blank for Any)")

        form.addField('szone', formal.String(required=True), 
            formal.widgetFactory(formal.SelectChoice, options = self.getZones()), 
            label = "Source Zone")

        form.addField('sport', formal.String(strip=True, validators=[PageHelpers.PortRangeValidator()]), label = "Source Port",
            description = "Source port (Blank for Any)")

        # Destination
        form.addField('dip', formal.String(), label = "Destination IP", 
            description = "Destination IP address or network (Leave blank for ANY)")

        form.addField('dzone', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, 
            options = self.getZones()), label = "Destination Zone")

        form.addField('dport', formal.String(strip=True, validators=[PageHelpers.PortRangeValidator()]), label = "Destination Port/Type",
            description = "Destination port OR other protocol subtype (Blank for any)")

        form.addField('proto', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, 
            options = self.protocols), label = "Protocol")

        form.data['szone']="all"
        form.data['dzone']="all"
        form.data['proto']="-"

        form.addAction(self.submitAllowRange)

        return form

    def constructRule(self, data):
        rule = ""
        rule += data['action'] + "   "
        rule += data['szone']
        if data['sip']:
            rule += ":"+data['sip']
        rule += "    %s" % (data['dzone'] or '')
        if data['dip']:
            rule+= ":"+data['dip']

        rule += "        "
        
        rule += data['proto'] + "    "

        rule += data['dport'] or "-"
        rule += "    "
        rule+= data['sport'] or "-"

        k = self.sysconf.Shorewall

        # Find the biggest ACCEPT/REJECT rule
        biggest = 0
        for v,i in enumerate(k['rules']):
            if "ACCEPT" in i[1] or "REJECT" in i[1]:
                biggest = v
        k['rules'].insert(biggest+1, [1, rule])

        self.sysconf.Shorewall = k

    def submitAllowRange(self, ctx, form, data):
        Utils.log.msg('%s added a new firewall rule %s' % (self.avatarId.username, repr(data)))

        if (data['proto']=="-") and (data['dport'] or data['sport']):
            data['proto'] = "tcp"
            self.constructRule(data)
            data['proto'] = "udp"
            self.constructRule(data)
        else:
            self.constructRule(data)

        return url.root.child('Firewall')

    def form_allowPort(self, data):
        form = formal.Form()
        form.addField('destport', formal.String(required=True), label = "Destination Port", description = "TCP/UDP port to permit")
        form.addField('destip', formal.String(), label = "Destination IP", description = "Destination IP address or network (Leave blank for ANY)")
        form.addField('proto', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = self.protocols), label = "Protocol")
        form.data['proto'] = 'tcp'
        form.data['zone']="net"
        form.addAction(self.submitAllowPort)

        return form

    def submitAllowPort(self, ctx, form, data):
        self.rules.addRule("APORT", self.rules.buildRule("APORT", data['zone'], data['proto'], data['destport'], data['destip']))
        return url.root.child('Firewall')

    def form_forwardPort(self, data):
        form = formal.Form()
        form.addField('szone', formal.String(required=True), 
            formal.widgetFactory(formal.SelectChoice, options = self.getZones()), 
            label = "Source Zone", description = "Source zone from which this rule will catch packets. ")

        form.addField('dzone', formal.String(required=True), 
            formal.widgetFactory(formal.SelectChoice, options = self.getZones()), 
            label = "Destination Zone",
            description = "Destination Zone to which this rule will forward packets.")

        form.addField('port', formal.String(strip=True, validators=[PageHelpers.PortRangeValidator()]), label = "Port", description = "TCP/UDP port to forward. Blank for protocol forward (like PPTP). Use separate ranges with a colon.")
        form.addField('destip', formal.String(required=True, strip=True, validators=[PageHelpers.IPValidator()]), label = "Forward To", description = "Destination IP address to forward to")
        form.addField('dstport', formal.String(strip=True, validators=[PageHelpers.PortValidator()]), label = "Forward To:Port", description = "TCP/UDP port to forward to. Blank for the same port.")
        form.addField('sourceip', formal.String(strip=True, validators=[PageHelpers.IPValidator()]), label = "Destination IP", description = "External IP to forward from")
        form.addField('source', formal.String(strip=True, validators=[PageHelpers.IPValidator()]), label = "Source IP", description = "External IP to accept connections from")
        form.addField('proto', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = self.protocols), label = "Protocol")
        form.data['proto'] = 'tcp'
        form.data['szone'] = 'net'
        form.data['dzone'] = 'loc'
        form.addAction(self.submitForwardPort)
        return form

    def submitForwardPort(self, ctx, form, data):
        Utils.log.msg('%s added a new firewall port forward %s' % (self.avatarId.username, repr(data)))
        if not data['dstport']:
            data['dstport'] = ""
        self.rules.addRule("FORWARD", self.rules.buildRule(
                "FORWARD", data['destip'], 
                data['proto'], data['port'], 
                data['dstport'], data['sourceip'],
                data['szone'], data['dzone'], data['source'] or ""
            ))
        return url.root.child('Firewall')

    def form_transProxy(self, data):
        form = formal.Form()

        form.addField('zone', formal.String(required=True), 
            formal.widgetFactory(formal.SelectChoice, options = self.getZones()), 
            label = "Source Zone", description = "Source zone from which this rule will catch traffic")

        form.addField('sourceip', formal.String(), label = "Source IP", description=["Source IP address of connecting host or network (Leave blank for ANY)."
        " This is usually a source host or network you want to exclude."])

        form.addField('destip', formal.String(), label = "Destination IP", description = ["Destination IP address or network (Leave blank for ANY). ", 
        "This is usually the opposite (!) of your local network.", "This is NOT the server you'd like to proxy to."])
        form.addField('srcport', formal.String(strip=True, validators=[PageHelpers.PortValidator()]), label = "Source port", description = "TCP/UDP port to catch.")
        form.addField('dstport', formal.String(strip=True, validators=[PageHelpers.PortValidator()]), label = "Destination port", description = "TCP/UDP port to forward to.")
        form.addField('proto', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = self.protocols), label = "Protocol")
        form.data['proto'] = 'tcp'
        form.data['szone'] = 'loc'
        form.addAction(self.submitTransProxy)

        return form

    def submitTransProxy(self, ctx, form, data):
        Utils.log.msg('%s added a new firewall transparent proxy %s' % (self.avatarId.username, repr(data)))
        if data['sourceip']:
            source = ":%s" % data['sourceip']
        else:
            source = ""
        self.rules.addRule("PROXY", self.rules.buildRule("PROXY", data['zone'], source, data['srcport'], data['proto'], data['dstport'], data['destip']))
        return url.root.child('Firewall')

    def form_addNAT(self, data):
        form = formal.Form()

        ifs = [(i,i) for i in Utils.getInterfaces()]

        form.addField('dstif', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = ifs), label = "External Interface",
            description = "The interface to which this traffic will be NATed.")

        form.addField('srcif', formal.String(), formal.widgetFactory(formal.SelectChoice, options = ifs), label = "Source Interface",
            description = "The interface which will have NAT applied to it")

        form.addField('destip', formal.String(), label = "Destination IP", description = ["Destination IP or network (Leave blank for ANY). ", 
        "This is the destination network you would like to NAT to"])

        form.addField('srcip', formal.String(), label = "Source IP", description = ["Source IP or network (Leave blank for ANY). ", 
        "This is the source network you would like to NAT from."])

        form.addField('natip', formal.String(), label = "NAT IP", description = ["The IP address that you would like to NAT the connections as.",
            "Leave this blank to let the firewall decide based on the interface configuration."])

        form.addField('proto', formal.String(), formal.widgetFactory(formal.SelectChoice, options = self.protocols), 
            label = "Protocol", description = "Protocol to NAT")
        form.addField('srcport', formal.String(strip=True, validators=[PageHelpers.PortRangeValidator()]), label = "Source port", description = "TCP/UDP port to NAT.")

        form.addAction(self.submitNAT)

        return form

    def submitNAT(self, ctx, form, data):

        Utils.log.msg('%s added a new firewall nat rule %s' % (self.avatarId.username, repr(data)))
        rule = [data['destip'] or '-']
        rule.append(data['srcif'] or '-')
        rule.append(data['srcip'] or '-')
        rule.append(data['natip'] or '-')
        rule.append(data['proto'] or '-')
        rule.append(data['srcport'] or '-')

        dest = data['dstif'].encode("ascii", "replace")

        e = self.sysconf.Shorewall
        if not e.get('masq', None):
            e['masq'] = {
                dest: [rule]
            }
        else:
            if e['masq'].get(dest, False):
                e['masq'][dest].append(rule)
            else:
                e['masq'][dest] = [rule]
        self.sysconf.Shorewall = e
        return url.root.child('Firewall')

    def form_addSNAT(self, data):
        form = formal.Form()

        ifs = []
        for i in Utils.getInterfaces():
            if 'eth' in i or 'tap' in i: # Only allow tap and eth binds...
                ifs.append((i, i))

        form.addField('dstif', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = ifs), label = "External Interface",
            description = "The interface to which this traffic will be NATed. (Generaly the outside/internet interface)")

        form.addField('dstip', formal.String(required=True, validators=[PageHelpers.IPValidator()]), label = "External IP",
            description = "The IP to which this traffic will be NATed")

        form.addField('srcip', formal.String(required=True, strip=True, validators=[PageHelpers.IPValidator()]), label = "Source IP", description = ["The source IP you would like to NAT to and from."])

        form.addField('all', formal.Boolean(), label = "Any Interface", 
            description = "Tick this if the rule should apply to all interfaces and not just the External Interface.")

        form.addField('local', formal.Boolean(), label = "Use Internal", description = "Apply this NAT rule to this servers traffic as well.")

        form.data['local'] = False
        form.data['all'] = False

        form.addAction(self.submitSNAT)

        return form

    def submitSNAT(self, ctx, form, data):
        Utils.log.msg('%s added a new firewall SNAT rule %s' % (self.avatarId.username, repr(data)))
        e = self.sysconf.Shorewall

        ru = "%s    %s            %s      %s          %s" % (
            data['dstip'].encode("ascii", "replace"),
            data['dstif'].encode("ascii", "replace"),
            data['srcip'].encode("ascii", "replace"),
            data['all'] and "yes" or "no",
            data['local'] and "yes" or "no",
        )

        if e.get('snat',False):
            e['snat'].append(ru)
        else:
            e['snat'] = [ru]

        self.sysconf.Shorewall = e
        return url.root.child('Firewall')


    def restartShorewall(self):
        Utils.log.msg('%s caused shorewall restart' % (self.avatarId.username))
        def checkBroke(res):
            if "ERROR" in res:
                l = open('/usr/local/tcs/tums/shorewallBroken', 'wt')
                l.write(res)
            else:
                # Remove any broken warnings
                WebUtils.system('rm /usr/local/tcs/tums/shorewallBroken > /dev/null 2>&1 ')

        WebUtils.system(Settings.BaseDir+'/configurator --shorewall; shorewall save; shorewall restart').addCallback(checkBroke)

    def locateChild(self, ctx, segs):
        if segs[0]=="DelQos":
            index = int(segs[1])
            conf = self.sysconf.Shorewall
            try:
                del conf['qos'][index]
            except:
                print "Unable to delete ", index
            self.sysconf.Shorewall = conf
            WebUtils.system('/usr/local/tcs/tums/configurator --shorewall')
            return url.root.child('Firewall'), ()

        if segs[0]=="Delete":
            if segs[1] == 'Zone':
                Utils.log.msg('%s deleted firewall zone %s' % (self.avatarId.username, segs[2]))
                k = self.sysconf.Shorewall
                if segs[2] in k.get('zones', {}):
                    del k['zones'][segs[2]]
                self.sysconf.Shorewall = k
            elif segs[1] in ['rules', 'dnat', 'redirect']:
                Utils.log.msg('%s deleted firewall %s %s' % (self.avatarId.username, segs[1], segs[2]))
                k = self.sysconf.Shorewall
                del k[segs[1]][int(segs[2])]
                self.sysconf.Shorewall = k
            elif segs[1] == "NAT":
                Utils.log.msg('%s deleted firewall nat rule %s' % (self.avatarId.username, segs[2]))
                src = segs[2]
                runum = int(segs[3])
                
                k = self.sysconf.Shorewall
                
                del k['masq'][src][runum]
                
                self.sysconf.Shorewall = k
            elif segs[1] == "SNAT":
                Utils.log.msg('%s deleted firewall snat rule %s' % (self.avatarId.username, segs[2]))
                # convert rule number
                runum = int(segs[2])

                k = self.sysconf.Shorewall
                # Delete the offending rule
                del k['snat'][runum]
                # Save the config
                self.sysconf.Shorewall = k
            else:
                Utils.log.msg('%s deleted firewall rule (2) %s' % (self.avatarId.username, segs[1]))
                self.rules.deleteRule(segs[1], int(segs[2]))
            return url.root.child('Firewall'), ()

        if segs[0] == "Swap":
            # Swap two rules
            k = self.sysconf.Shorewall
            Utils.log.msg('%s swapped firewall rules %s and %s' % (self.avatarId.username, 
                repr(k['rules'][int(segs[1])]), repr(k['rules'][int(segs[2])]))
            )
            trule = k['rules'][int(segs[1])]
            k['rules'][int(segs[1])] = k['rules'][int(segs[2])]
            k['rules'][int(segs[2])] = trule
            self.sysconf.Shorewall = k
            return url.root.child('Firewall'), ()
        if segs[0]=="Restart":
            self.restartShorewall()
            return url.root.child('Firewall'), ()
        return PageHelpers.DefaultAthena.locateChild(self, ctx, segs)
        
    def getRules(self):
        return None

    def render_connections(self, ctx, data):
        # Grab netstat
        l = WebUtils.system('netstat -n --ip | grep -E ".?[0-9]?[0-9]?[0-9]\." | awk \'{print $4 " " $5}\'| uniq | sort')

        # build a matcher
        regex = re.compile("(.*):(.*) (.*):(.*)")

        def renderFragment(ret, error=False):
            if error:
                return ctx.tag["Error 1"]

            connections = []
            for con in ret.split('\n'):
                m = regex.match(con)
                if m:
                    tup = m.groups()
                    if tup[0] == tup[2]:
                        # boring
                        continue
                    connections.append(list(tup)+[
                        tags.a(href="#addRule", onclick="populateRule('%s', '%s', '%s', '%s');" % (tup))[
                            "Create Rule"
                        ]
                    ])

            return ctx.tag[
                PageHelpers.dataTable(["Destination IP", "Destination Port", "Source IP", "Source Port", ""], connections)
            ]

        return l.addCallback(renderFragment).addErrback(renderFragment, True)

    def render_content(self, ctx, data):
        Utils.log.msg('%s opened Tools/Firewall' % (self.avatarId.username))

        rules = self.rules.read()

        ### Read SNAT rules
        snat = self.sysconf.Shorewall.get('snat', [])
        snatRules = []
        n = 0
        for ru in snat:
            l = ru.split()
            l.append(
                tags.a(
                    href="Delete/SNAT/%s/" % n, 
                    onclick="return confirm('Are you sure you want to delete this SNAT rule?');",
                    title="Delete this SNAT rule."
                )[tags.img(src="/images/ex.png")]
            )
            snatRules.append(l)
            n += 1

        ### Read MASQ rules
        masq = self.sysconf.Shorewall.get('masq', {})
        natRules = []
        for k,mas in masq.items():
            runum = 0 
            for v in mas:
                if type(v) == list:
                    l = [k]
                    l.extend([i.replace('-', 'Any') for i in v])
                    l.append(
                        tags.a(
                            href="Delete/NAT/%s/%s/"%(k, runum), 
                            onclick="return confirm('Are you sure you want to delete this NAT rule?');",
                            title="Delete this NAT rule."
                        )[tags.img(src="/images/ex.png")]
                    )
                    natRules.append(l)
                else:
                    natRules.append([
                        k, 'Any', v, 'Any', 'Any', 'Any', 'Any',
                        tags.a(
                            href="Delete/NAT/%s/%s/"%(k, runum), 
                            onclick="return confirm('Are you sure you want to delete this NAT rule?');",
                            title="Delete this NAT rule."
                        )[tags.img(src="/images/ex.png")]
                    ])
                runum += 1

        # QOS
        toss = {
            '16':'Minimize Delay',
            '8':'Maximize Throughput',
            '4':'Maximize Reliability',
            '2':'Minimize Cost',
            '0':'Normal Service'
        }
        qosRules = []
        l = 0
        for port, proto, tos in self.sysconf.Shorewall.get('qos', []):
            qosRules.append([
                port,
                proto,
                toss[tos],
                tags.a(href=url.root.child("Qos").child("Delete").child(l), onclick="return confirm('Are you sure you want to delete this entry?');")[tags.img(src="/images/ex.png")]
            ])
            l += 1

        ### Check if shorewall is broken
        if os.path.exists('/usr/local/tcs/tums/shorewallBroken'):
            check = tags.div(style="color: #F00")[
                tags.br,
                tags.strong[
                    "The firewall configuration appears to be broken, please test the settings to see any errors and correct them"
                ],
                tags.br
            ]
        else:
            check = ""

        fwtable, securityViolation = getFirewallRules(self.rules)

        if securityViolation:
            secError =  [tags.table(width="70%", style="border:2px solid #ff5555")[tags.tr[
                tags.td[tags.img(src="/images/securityhz.png")],
                tags.td[
                    tags.h1["Security Violation!"],
                    securityViolation
                ]
            ]], tags.br, tags.br]
        else:
            secError = ""
        
        ### Return the page stanza
        return ctx.tag[
                tags.h3[tags.img(src="/images/firewall.png"), " Firewall"],

                check,
                secError,

                tags.img(src="/images/start.png"), " ",
                tags.a(
                    href="Test", 
                    style="font-size:11pt;", 
                    title="Test the firewall. (This may take some time!)"
                )[tags.strong(style="font-family:arial,verdana,helvetica,sans-serif;")["Test Settings"]],
                tags.br,
                tags.img(src="/images/refresh.png"), " ",
                tags.a(
                    href="Restart", 
                    style="font-size:11pt;", 
                    title="Restart the firewall and apply the changes. Changes are only activated after this is clicked."
                )[tags.strong(style="font-family:arial,verdana,helvetica,sans-serif")["Apply Changes"]],

                PageHelpers.TabSwitcher((
                    ('Rules'          , 'panelRules'),
                    #('Allow Ports'       , 'panelAllowPort'),
                    ('NAT',             'panelNATTab'),
                    ('QoS',             'panelQos'),
                    ('Policy',             'panelPolicy'),
                    ('Zones'    ,       'panelZones'),
                    ('Connections',     'panelCurrent'),
                ), id = "firewall"),

                tags.div(id="panelNATTab", _class="tabPane")[
                    PageHelpers.TabSwitcher((
                        ('Forwarding',  'panelForwardPort'), 
                        ('Redirection', 'panelTransparentProxy'), 
                        ('NAT',         'panelNAT'), 
                        ('Source NAT',  'panelSNAT')
                    ), id ="firewallNAT"),

                    tags.div(id="panelForwardPort", _class="tabPane")[
                        tags.h3["Port Forwarding"],
                        PageHelpers.dataTable(['Source Zone', 'Source IP', 'Forward To', 'Destination Zone', 'Protocol', 'Port', 'Destination IP', ''], [
                            r[:-1] + [tags.a(
                                href="Delete/dnat/%s/"%(r[-1]), 
                                title="Delete this port forwarding rule",
                                onclick="return confirm('Are you sure you want to delete this entry?');"
                            )[tags.img(src="/images/ex.png")]]
                        for i,r in enumerate(rules['FORWARD'])]),
                        tags.h3["Add Forwarding Rule"],
                        tags.directive('form forwardPort'),
                    ],

                    tags.div(id="panelTransparentProxy", _class="tabPane")[
                        tags.h3["Port Redirection (Transparent Proxy)"],
                        PageHelpers.dataTable(['Source Zone', 'Source Network', 'Destination Port', 'Source Port', 'Protocol', 'Destination Network', ''], [
                            r[:-1] + [tags.a(
                                href="Delete/redirect/%s/"%(r[-1]), 
                                title="Delete this transparent redirection rule",
                                onclick="return confirm('Are you sure you want to delete this entry?');"
                            )[tags.img(src="/images/ex.png")]]
                        for i,r in enumerate(rules['PROXY'])]),
                        tags.h3["Add Redirection Rule"],
                        tags.directive('form transProxy'),
                    ],

                    tags.div(id="panelNAT", _class="tabPane")[
                        tags.h3["Nework Address Translation (Masquerading)"],
                        PageHelpers.dataTable(
                            ['Destination Interface', 'Destination Network', 'Source Interface', 'Source Network', 'NAT IP', 'Protocol', 'Port', ''],
                            natRules
                        ),
                        tags.h3['Add NAT Rule'],
                        tags.directive('form addNAT')
                    ],

                    tags.div(id="panelSNAT", _class="tabPane")[
                        tags.h3["Source NAT"],
                        PageHelpers.dataTable(
                            ['Source IP', 'External Interface', 'Internal IP', 'Any Interface', 'Use Internal'],
                            snatRules
                        ),
                        tags.h3['Add SNAT Rule'],
                        tags.directive('form addSNAT')
                    ],

                    PageHelpers.LoadTabSwitcher(id="firewallNAT")
                ],

                tags.div(id="panelPolicy", _class="tabPane")[
                    tags.h3["General firewall policy"],
                    tags.directive('form inetPol') 
                ],

                tags.div(id="panelQos", _class="tabPane")[
                    tags.h3[tags.img(src="/images/compress.png"), "QOS"],
                    PageHelpers.dataTable(['Port', 'Protocol', 'Type of service', ''], qosRules),
                    tags.h3["Add Rule"],
                    tags.directive('form addQos'),
                ],

                tags.div(id="panelRules", _class="tabPane")[
                    tags.h3["Firewall Rules"], 
                    tags.invisible(render=tags.directive('tableWidget')), 
                    tags.br,
                    #fwtable,
                    tags.a(name="addRule")[''],
                    tags.h3["Add rule"],
                    tags.directive('form allowRange'),
                ],

                tags.div(id="panelZones", _class="tabPane")[
                    tags.h3["Zones"],
                    PageHelpers.dataTable(['Zone Name', 'Policy', 'Log target', 'Interfaces', ''], 
                        [
                            [
                                zone, zd['policy'], zd['log'], [[i, tags.br] for i in zd['interfaces']],
                                [
                                    tags.a(
                                        href="Delete/Zone/%s/"%(zone),
                                        title="Delete this firewall zone",
                                        onclick="return confirm('Are you sure you want to delete this zone?');"
                                    )[tags.img(src="/images/ex.png")],
                                    tags.a(href="EditZone/%s/" % zone)[tags.img(src="/images/edit.png")]
                                ]
                            ] 
                        for zone, zd in self.sysconf.Shorewall.get('zones', {}).items()]
                    ),
                    tags.h3['Add Firewall Zone'],
                    tags.directive('form addZone')
                ],
                tags.div(id="panelCurrent", _class="tabPane")[
                    tags.h3["Current Connections"],
                    tags.invisible(render=tags.directive('connections'))
                ],
            PageHelpers.LoadTabSwitcher(id="firewall")
        ]

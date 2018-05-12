from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan, entities
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP
from Core import PageHelpers, AuthApacheProxy, confparse, Utils, WebUtils
from Core.Configurator import DHCP
from Pages import Tools
import formal

from twisted.python import log

def printCallback(_):
    # Callback that prints results and returns nothing
    print _

class StaticAddress(PageHelpers.DataTable):
    def getTable(self):
        statics = []
        leases = self.sysconf.DHCP.get('leases', {})
        for ip, hostmac in leases.items():
            statics.append((ip, hostmac[0], hostmac[1]))

        statics.sort()
        
        headings = [("IP Address", 'ip'), ("Hostname", 'hostname'), ("MAC Address", 'mac')]
        return headings, statics

    def addForm(self, form):
        form.addField('hostname', formal.String(required=True),  label = "Hostname")
        form.addField('mac', formal.String(required=True), label = "Mac address", description="Hardware address of host. Must be colon (:) delimited.")
        form.addField('ip', formal.String(required=True, strip=True, validators=[PageHelpers.IPValidator()]), label = "IP Address")
        
    def addAction(self, data):
        Utils.log.msg('%s created static lease %s' % (self.avatarId.username, repr(data)))

        return DHCP.create_lease(self.sysconf, data)

    def deleteItem(self, item):
        
        leases = self.sysconf.DHCP

        # Convert our table index into an IP from the config
        bcks = [i[0] for i in leases['leases'].items()]
        bcks.sort()
        leaseIp = bcks[item]
        Utils.log.msg('%s deleted DHCP lease %s' % (self.avatarId.username, leaseIp))
    
        # Delete this IP lease
        del leases['leases'][leaseIp]

        self.sysconf.DHCP = leases
        
    def returnAction(self, data):
        return WebUtils.restartService('dhcp').addBoth(lambda _: url.root.child('Dhcp'))

def createForm(form):
    form.addField('domain', formal.String(strip=True, validators=[PageHelpers.HostValidator()]), label = "Domain", description="Domain name")
    form.addField('netbios', formal.String(strip=True, validators=[PageHelpers.IPValidator()]), 
        label = "Windows Server", description="A windows server (if any) to delegate for WINS and Netbios")

    form.addField('nameserver', formal.String(strip=True, validators=[PageHelpers.IPValidator()]), label = "DNS Server", description="DNS server")

    form.addField('network', formal.String(strip=True, validators=[PageHelpers.IPValidator()]), label = "Network address")
    form.addField('netmask', formal.String(strip=True, validators=[PageHelpers.IPValidator()]), label = "Subnet mask")

    form.addField('rangeStart', formal.String(), label = "Start IP")
    form.addField('rangeEnd', formal.String(), label = "End IP")
    form.addField('gateway', formal.String(strip=True, validators=[PageHelpers.IPValidator()]), label = "Default gateway")
    form.addField('autoProv', formal.Boolean(), label = "Auto Provision")
    form.addField('snomStart', formal.String(), label = "Phone Start IP")
    form.addField('snomEnd', formal.String(), label = "Phone End IP")
    form.addField('snomConfigAddr', formal.String(), label = "Snom Config URL")
 

class EditPage(Tools.Page):
    def __init__(self, avatarId, db, iface=None, *a, **kw):
        PageHelpers.DefaultPage.__init__(self, avatarId, db, *a, **kw)
        self.iface = iface

    def form_confDhcp(self, data):
        form = formal.Form()
        createForm(form)
        form.data = DHCP.get_dhcp_config(self.sysconf, self.iface)

        form.addAction(self.confDhcp)
        return form

    def confDhcp(self, c, f, data):
        return DHCP.set_dhcp_config(self.sysconf, data, self.iface).addBoth(lambda _: url.root.child('Dhcp'))

    def childFactory(self, ctx, segs):
        if not self.iface:
            return EditPage(self.avatarId, self.db, segs)
        return Tools.Page.childFactory(self, ctx, segs)
 
    def render_content(self, ctx, data):
        return ctx.tag[
            tags.h3[tags.img(src="/images/dhcp.png"), " Edit DHCP for interface %s" % self.iface],
            tags.directive('form confDhcp')
        ]

class Page(Tools.Page):
    addSlash = True

    def __init__(self, *a, **kw):
        PageHelpers.DefaultPage.__init__(self, *a, **kw)
        self.addStatic = StaticAddress(self, 'Static', 'Static address')

    def form_confDhcp(self, data):
        form = formal.Form()
        ifaces = []
        for i, defin in self.sysconf.EthernetDevices.items():
            if defin.get('dhcpserver', False):
                ifaces.append((i,i))
        form.addField('interface', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = ifaces), 
            description = "DHCP Interface", label = "Interface")
 
        createForm(form)
        #form.data = DHCP.get_dhcp_config(self.sysconf)

        form.data['domain'] = self.sysconf.Domain
        form.data['netmask'] = '255.255.255.0'
        form.addAction(self.confDhcp)
        return form

    def confDhcp(self, c, f, data):
        Utils.log.msg('%s changed DHCP configuration %s' % (self.avatarId.username, repr(data)))
        iface = data['interface'].encode("ascii", "replace")
        del data['interface']
        
        return DHCP.set_dhcp_config(self.sysconf, data, iface).addBoth(lambda _: url.root.child('Dhcp'))

    def render_content(self, ctx, data):
        Utils.log.msg('%s opened Tools/DHCP' % (self.avatarId.username))
        leases = self.sysconf.DHCP.get('leases', {})

        nets = []
        for i, defin in self.sysconf.EthernetDevices.items():
            if defin.get('dhcpserver'):
                data = DHCP.get_dhcp_config(self.sysconf, i)
                if not data:
                    continue
                ips = '.'.join(data['network'].split('.')[:3])
                range = "%s.%s - %s.%s" % (
                    ips, data['rangeStart'], 
                    ips, data['rangeEnd']
                )
                if '.' in data['rangeStart']:
                    range = "%s - %s" % (data['rangeStart'], data['rangeEnd'])

                nets.append((
                    i, 
                    data['network'], 
                    data['domain'], 
                    data['gateway'],
                    data['nameserver'], 
                    range, 
                    [
                        tags.a(href="Delnet/%s/" % i)[tags.img(src="/images/ex.png")], 
                        entities.nbsp,
                        tags.a(href="Edit/%s/" % i)[tags.img(src="/images/edit.png")]
                    ]
                ))

        cleases = []
        try:
            lfile = open('/var/lib/dhcp3/dhcpd.leases')
        except:
            lfile = None
        if lfile:
            leaseIP = ""
            currentInfo = {'hostname': "", 'state':""}
            for l in lfile:
                try:
                    ln = l.strip('\n').strip(';').strip()
                    if (not ln) or (ln[0] == "#"):
                        continue
                    
                    if ("lease" in ln) and (ln[-1] == "{"):
                        leaseIP = ln.split()[1]
                        continue
                    if leaseIP:
                        if ("binding state" in ln) and ("next" not in ln):
                            currentInfo['state'] = ln.split()[-1]
                        if "client-hostname" in ln:
                            currentInfo['hostname'] = ln.split()[-1].replace('"', '')
                        if "hardware ethernet" in ln:
                            currentInfo['mac'] = ln.split()[-1]
                    if "}" in ln:
                        if currentInfo['hostname']:
                            hostname = currentInfo['hostname']
                        else:
                            hostname = "E" + currentInfo.get('mac', '').replace(':', '')
                        ifdet = Utils.locateIp(self.sysconf, leaseIP)
                        iface = "?"
                        if ifdet:
                            iface = ifdet[0]

                        cleases.append((
                            iface, 
                            leaseIP,
                            currentInfo.get('mac', ''),
                            currentInfo['hostname'], 
                            currentInfo['state'],
                            tags.a(href=url.root.child('Dhcp').child('CreateLease').child(currentInfo['mac']).child(leaseIP).child(hostname))["Make Static"]
                        ))
                        leaseIP = ""
                        currentInfo = {'hostname': "", 'state':""}
                except Exception, e:
                    print "Error parsing leases. Likely that file is currently being written", e

        return ctx.tag[
            tags.h3[tags.img(src="/images/dhcp.png"), " DHCP"],
            PageHelpers.TabSwitcher((
                ('DHCP Settings', 'panelSettings'),
                ('Static Leases', 'panelLeases'),
                ('Current Leases', 'panelCurrent')
            )),
            tags.div(id="panelLeases", _class="tabPane")[
                self.addStatic.applyTable(self)
            ], 
            tags.div(id="panelSettings", _class="tabPane")[
                PageHelpers.dataTable(("Interface", "Network", "Domain", "Gateway", "DNS", "Range", ""), nets, sortable=True),
                tags.h3["Add DHCP Configuration"],
                tags.directive('form confDhcp')
            ],
            tags.div(id="panelCurrent", _class="tabPane")[
                PageHelpers.dataTable(("Interface", "IP", "MAC", "Hostname", "State", ""), cleases, sortable=True),
            ],
            PageHelpers.LoadTabSwitcher()
        ]

    def locateChild(self, ctx, segs):
        if segs[0]=="Edit":
            return EditPage(self.avatarId, self.db, segs[1]), ()
        if segs[0]=="Delnet":
            Utils.log.msg('%s deleted shared DHCP net %s' % (self.avatarId.username, segs[1]))
            nets = self.sysconf.DHCP
            try:
                del nets[segs[1]]
            except:
                pass
            self.sysconf.DHCP = nets

            # Disable it on the interface too
            Eths = self.sysconf.EthernetDevices
            Eths[segs[1]]['dhcpserver'] = False
            self.sysconf.EthernetDevices = Eths

            return WebUtils.restartService('dhcp').addBoth(lambda _: url.root.child('Dhcp')), ()
        if segs[0]=="CreateLease":
            data = {
                'mac': segs[1],
                'ip': segs[2],
                'hostname': segs[3]
            }
            DHCP.create_lease(self.sysconf, data)
            return WebUtils.restartService('dhcp').addBoth(lambda _: url.root.child('Dhcp')), ()
        return rend.Page.locateChild(self, ctx, segs)
            

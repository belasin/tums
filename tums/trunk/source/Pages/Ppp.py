from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure, log
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP
from Core import PageHelpers, AuthApacheProxy, Utils, confparse, WebUtils
from Pages import Tools
import formal, copy

class PPPInterfaces(PageHelpers.DataTable):
    def extraJs(self):
        return """
            if (el == "options") {
                var opts = exRows[index][c];
                getElement('addPPPInterface-defaultRoute').checked = false;
                getElement('addPPPInterface-localOnly').checked = false;
                getElement('addPPPInterface-defaultDNS').checked = false;
                getElement('addPPPInterface-createNAT').checked = false;
                
                alert('OPTS is: ' + opts);

                if (opts.search(/Default/) > -1) {
                    getElement('addPPPInterface-defaultRoute').checked = true;
                };
                
                if (opts.search(/Local/) > -1) {
                    getElement('addPPPInterface-localOnly').checked = true;
                };
                
                if (opts.search(/DNS/) > -1) {
                    getElement('addPPPInterface-defaultDNS').checked = true;
                };
                
                if (opts.search(/NAT/) > -1) {
                    getElement('addPPPInterface-createNAT').checked = true;
                };
            }
        """

    def getZones(self):
        zones = self.sysconf.Shorewall['zones']
        return [(zo,zo) for zo in zones.keys()] # Build something we can se for drop downs

    def getPeers(self):
        f = open('/proc/net/dev')
        devs = []
        for i in f:
            l = i.strip()
            if 'ppp' in l:
                devs.append(l.split(':')[0])
        return devs

    def getEthernets(self):
        f = open('/proc/net/dev')
        devs = []
        for i in f:
            l = i.strip()
            if 'eth' in l:
                devs.append(l.split(':')[0])
        return devs

    def getTable(self):
        headings = [
            ('Status', ''), 
            ('Interface', 'interface'), 
            ('Link', 'link'),
            ('Username', 'username'), 
            ('Password', 'password'), 
            ('Type', 'type'),
            ('Options', 'options'), 
            ('Zone', 'zone')
        ]
        
        wanDevices = self.sysconf.WANDevices
        wanTable = []
        pppDevs = self.getPeers()
        for iface, detail in wanDevices.items():
            if iface in pppDevs:
                peerStatus = [
                    tags.a(
                        href=url.root.child("PPP").child("Disconnect").child(iface), 
                        title="Connected: Click to disconnect.",
                        onclick="return confirm('Are you sure you want to disconnect this interface?');"
                    )[tags.img(src='/images/connect.png')],
                    " ",
                    tags.a(
                        href=url.root.child("PPP").child("Reset").child(iface),
                        title="Reconnect this interface",
                        onclick="return confirm('Are you sure you wish to reconnect this interface?');"
                    )[tags.img(src='/images/refresh.png')]
                ]
            else:
                peerStatus = tags.a(href=url.root.child("PPP").child("Connect").child(iface), title="Disconnected: Click to connect.")[tags.img(src='/images/noconnect.png')]
            options = ""
            if detail.get('pppd', None):
                if 'defaultroute' in detail['pppd']:
                    options += "Default Route "
                if 'peerdns' in detail['pppd']:
                    options += "Automatic DNS "
								#This was not using the usepeerdns value and hence wasn't populating.
               	if 'usepeerdns' in detail['pppd']:
                    options += "Default DNS "
            
            if self.sysconf.LocalRoute == iface:
                options += "Local Only "
            
						#Check if the value is in the firewall.
            shorewall = self.sysconf.Shorewall
            masq = shorewall.get('masq')
            if (iface in masq):
								options += "Default NAT "
            
            type = "PPP"
            if detail.get('plugins', None):
                if detail['plugins'] == "pppoe":
                    type = "PPPoE"
            
            wallZones = self.sysconf.Shorewall['zones']
            zone = ""
            for i,v in wallZones.items():
                for k in v['interfaces']:
                    if iface in k:
                        zone = i
            
            wanTable.append([
                peerStatus,
                iface,
                detail.get('link', ''),
                detail.get('username', ''),
                detail.get('password', ''),
                type,
                options,
                zone
                #tags.a(href=url.root.child("PPP").child("Delete").child(iface))[tags.img(src="/images/ex.png")]
            ])
        return headings, wanTable

    def addForm(self, form):
        form.addField('link', formal.String(required=True),
            formal.widgetFactory(formal.SelectChoice, options = [(i,i) for i in self.getEthernets() ]), label = "Ethernet Link")

        form.addField('username', formal.String(required=True), label = "Username")
        form.addField('password', formal.String(required=True), label = "Password")

        form.addField('localOnly', formal.Boolean(), label = "Local Only", description="Checking this box will cause only South African traffic to be routed over this link")
        form.addField('defaultRoute', formal.Boolean(), label = "Default Routes", description="Make this the default internet connection")
        form.addField('defaultDNS', formal.Boolean(), label = "Default DNS", description="Use the DNS servers that this connection provides")
        form.addField('createNAT', formal.Boolean(), label = "Default NAT", description = "Ensure there is a default NAT rule for this connection")

        form.addField('zone', formal.String(required=True),
            formal.widgetFactory(formal.SelectChoice, options = self.getZones()),
            label = "Firewall Zone"
        )

        form.data['createNAT'] = True
        form.data['link'] = 'eth0'
        form.data['defaultRoute'] = True

    def reconfItem(self, iface, data):
        wanDevices = self.sysconf.WANDevices

        defaults = []
        for d in wanDevices.get(iface, {}).get('pppd', []):
            # If we append these, it's impossible to reconfigure them
            if d not in ['defaultroute', 'usepeerdns']:
                defaults.append(d)

        if data['defaultRoute']:
            defaults.append('defaultroute')

        if data['defaultDNS']:
            defaults.append('usepeerdns')

        seg = {
            'pppd': defaults, 
            'username': data['username'],
            'password': data['password'],
            'link': data['link'],
            'plugins': 'pppoe'
        }

        wanDevices[iface] = seg

        self.sysconf.WANDevices = wanDevices

        if data['localOnly']:
            self.sysconf.LocalRoute = iface
        else:
            if self.sysconf.LocalRoute == iface:
                self.sysconf.LocalRoute = ''

        if data['createNAT']:
            shorewall = self.sysconf.Shorewall
            masq = shorewall.get('masq')
            if not (iface in masq):
                masq[iface] = Utils.getLans(self.sysconf)
                shorewall['masq'] = masq
                self.sysconf.Shorewall = shorewall
                WebUtils.system('/usr/local/tcs/tums/configurator --shorewall; shorewall restart')
        
        
        wallZones = self.sysconf.Shorewall['zones']
        s = self.sysconf.Shorewall
        # Remove interface from any and all zones
        for i,v in wallZones.items():
            newIfs = []
            for k in v['interfaces']:
                if not (iface in k):
                    newIfs.append(k)
            s['zones'][i]['interfaces'] = newIfs

        if data['zone']:
            # Add to new zone
            s['zones'][data['zone'].encode("ascii", "replace")]['interfaces'].append(
                '%s detect' % iface
            )
            self.sysconf.Shorewall = s

    def addAction(self, data):
        Utils.log.msg('%s added PPP account details %s' % (self.avatarId.username, repr(data)))
        wanDevices = self.sysconf.WANDevices

        devices = []
        for i in xrange(20):
            n = "ppp%s" % i
            if not (n in wanDevices.keys()):
                devices.append(n)
        this = devices[0]

        self.reconfItem(this, data)

    def editAction(self, item, data):
        iface = self.getTable()[1][item][1]

        Utils.log.msg('%s edited PPP account details %s to %s' % (self.avatarId.username,iface, data))

        self.reconfItem(iface, data)

    def deleteItem(self, item):
        iface = self.getTable()[1][item][1]

        Utils.log.msg('%s deleted PPP account %s' % (self.avatarId.username, iface))

        wanDevices = self.sysconf.WANDevices
        if iface in wanDevices:
            del wanDevices[iface]
        else:
            pass
        self.sysconf.WANDevices = wanDevices 
        
        if self.sysconf.LocalRoute == iface:
            self.sysconf.LocalRoute = ""

        # Check for and remove NAT rules
        shorewall = self.sysconf.Shorewall
        masq = shorewall.get('masq')
        if iface in masq:
            del masq[iface]
            shorewall['masq'] = masq
        self.sysconf.Shorewall = shorewall

        exitProcs = [
            '/usr/local/tcs/tums/configurator --shorewall', 
            'shorewall restart', 
            '/usr/local/tcs/tums/syscripts/pppoff %s' % iface[-1]
        ]

        def q(_):
            print _

        return WebUtils.system(';'.join(exitProcs)).addBoth(q)


    def returnAction(self, data):
        def returnPage(_):
            print _
            return url.root.child('PPP')

        return WebUtils.system(
            '/usr/local/tcs/tums/configurator --quagga; /etc/init.d/quagga restart; /usr/local/tcs/tums/configurator --debnet'
        ).addCallback(returnPage)

class Page(Tools.Page):
    addSlash = True

    def __init__(self, *a, **kw):
        Tools.Page.__init__(self, *a, **kw)
        self.pppIface = PPPInterfaces  (self, 'PPPInterface',  'PPP interface')

    def render_content(self, ctx, data):

        return ctx.tag[
            tags.h3[tags.img(src="/images/remote_access_section.png"), " PPPoE Interfaces"],
            self.pppIface.applyTable(self)
        ]

    def locateChild(self, ctx, segs):
        def returnMe(_):
            return url.root.child('PPP'), ()
            
        if segs[0] == "Connect":
            unitNumber = segs[1].strip('ppp')
            return WebUtils.system('/usr/local/tcs/tums/syscripts/pppoff %s; sleep 1; pon wan%s' % (unitNumber, unitNumber)).addBoth(returnMe)
            
        if segs[0] == "Disconnect":
            unitNumber = segs[1].strip('ppp')
            return WebUtils.system('/usr/local/tcs/tums/syscripts/pppoff %s' % unitNumber).addBoth(returnMe)

        if segs[0] == "Reset":
            unitNumber = segs[1].strip('ppp')
            return WebUtils.system('/usr/local/tcs/tums/syscripts/pppoff %s; sleep 1; pon wan%s' % (unitNumber, unitNumber)).addBoth(returnMe)

        if segs[0] == "Status":
            unitNumber = segs[1].strip('ppp')
            def ans(r):
                return r, ()
            
            return WebUtils.system('/usr/local/tcs/tums/syscripts/pppstat %s' % (unitNumber)).addBoth(ans)

        if segs[0] == "Delete":
            # Delete one
            return url.root.child('PPP'), ()
        return rend.Page.locateChild(self, ctx, segs)
            

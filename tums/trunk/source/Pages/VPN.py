from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
from twisted.internet.defer import deferredGenerator, waitForDeferred as wait

import Tree, Settings, os
from Core import PageHelpers, AuthApacheProxy, Shorewall, Utils, confparse, WebUtils
from Core.Configurator import VPN
from Pages import Tools
import formal

vpnInit = 'openvpn'

class Page(Tools.Page):
    addSlash = True
    
    def form_winForm(self, data):
        """ Windows VPN Form"""
        form = formal.Form()

        form.addField('windows', formal.Boolean(), label = self.text.vpnLabelWindows, description=self.text.vpnDescripWindows)
        form.addField('winip', formal.String(), label = self.text.vpnLabelWinserver)
        form.addField('winextip', formal.String(), label = self.text.vpnLabelExtwinserver,
            description = [self.text.vpnDescripExtwinserver])

        form.data['winip'], form.data['winextip'], form.data['windows'] = VPN.get_windows_vpn(self.sysconf)

        form.addAction(self.submitWinForm)

        return form
        
    def submitWinForm(self, c, f, data):
        """ Validate the windows vpn form and create relevant configuration"""
        if not data['winip']:
            return url.root.child('VPN')

        return VPN.set_windows_vpn(self.sysconf, data, lambda _: url.root.child('VPN'))

    def form_vpnForm(self, data):
        """ OpenVPN (Vulani VPN) form""" 
        form = formal.Form()

        form.addField('openvpn', formal.Boolean(), label = self.text.vpnLabelOpenvpn, description=self.text.vpnDescripOpenvpn)

        form.addField('iprange1', formal.String(required=True), label = self.text.vpnRangeStart)
        form.addField('iprange2', formal.String(required=True), label = self.text.vpnRangeTo)

        form.addField('mtu', formal.String(), label = self.text.vpnMTU)

        form.addField('WINS', formal.String(strip=True, validators=[PageHelpers.IPValidator()]), label = self.text.vpnWINSServer)
        form.addField('DNS', formal.String(), label = self.text.vpnDNSServer)
        form.addField('DOMAIN', formal.String(), label = self.text.vpnDomain)

        form.addField('tcp', formal.Boolean(), label = "Use TCP", description = "Use TCP instead of UDP for connections. Not recommended, but helps with connection issues from high packet-loss sites like GPRS or 3G, at the expense of performance. TCP port 1194 needs to be opened in the firewall for this to be successful")
        
        def returnForm(result):
            print result
            conf, routes = result 
            form.addField(
                'routes', formal.Sequence(formal.String()),
                formal.widgetFactory(formal.CheckboxMultiChoice, [(i,i) for i in routes]), 
                label = self.text.vpnRoutesPush
            )

            form.data = conf
            form.addAction(self.submitForm)
            return form
                
        return VPN.get_openvpn_settings(self.sysconf).addBoth(returnForm)

    def form_addTun(self, data):
        form = formal.Form()
        
        form.addField('name', formal.String(required=True), label = "Tunnel name")
        form.addField('endpoint', formal.String(strip=True, validators=[PageHelpers.IPValidator()]), label = "Tunnel endpoint", 
            description = "IP address or hostname of the remote computer")

        form.addField('type', formal.String(required=True),  formal.widgetFactory(formal.SelectChoice, options = [
                ('openvpn','OpenVPN'), 
                ('l2tp', 'L2TP'),
                #('pptp', 'PPTP'),
                #('sit', 'SIT'),
                #('gre', 'GRE'),
            ]), label = "Type",
            description = "The type of tunnel to use")
        form.data['type'] = 'openvpn'

        form.addField('default', formal.Boolean(), label = "Default route",
            description = "If set will route all traffic over the link once it is established. If you only need specific routes then add them with the Routing tool.")

        # JS will enable these for pptp or l2tp
        form.addField('username', formal.String(), label = "Username")
        form.addField('password', formal.String(), label = "Password")

        # JS will enable these for OpenVPN
        form.addField('proto', formal.String(required=True),  formal.widgetFactory(formal.SelectChoice, options = [
            ('udp', 'UDP'),
            ('tcp', 'TCP')
        ]), label = "Protocol", description="The layer 3 protocol to use for this connection. Usuauly UDP")

        form.data['proto'] = 'udp'

        form.addField('CA', formal.File(), formal.FileUploadWidget, label = "Remote CA")
        form.addField('crt', formal.File(), formal.FileUploadWidget, label = "Local certificate")
        form.addField('key', formal.File(), formal.FileUploadWidget, label = "Local key")

        form.addAction(self.submitTunnel)
        return form

    def submitTunnel(self, ctx, form, data):
        return VPN.create_tunnel(self.sysconf, data, lambda _: url.root.child('VPN'))

    def form_addUser(self, data):
        """ Form for adding a user"""
        form = formal.Form()
        
        form.addField('name', formal.String(required=True), label = self.text.vpnName)
        form.addField('mail', formal.String(), label = self.text.vpnMail) 
        form.addField('ip', formal.String(strip=True, validators=[PageHelpers.IPValidator()]), label = self.text.vpnStaticIP)
        form.addField('mailKey', formal.Boolean(), label = self.text.vpnMailQuestion)

        form.addAction(self.newCert)
        return form

    def newCert(self, ctx, form, data):
        """Create a cert and sign it"""
        
        return VPN.create_certificate(self.sysconf, data, lambda _: url.root.child('VPN'))

    def submitForm(self, ctx, form, data):
        """ Reconfigura the standard VPN"""
        return VPN.set_openvpn(self.sysconf, data, lambda _: url.root.child('VPN'))

    def render_content(self, ctx, data):
        keys = [i for i in os.listdir('/etc/openvpn/keys/') if '.key' in i]

        keys.sort()
        for key in ['vpn.key', 'ca.key']:
            try:
                keys.remove(key)
            except:
                pass

        # Build a list of tunnels
        types={}
        # reprocess the configuration
        for name, conf in self.sysconf.Tunnel.items():
            if name == "ipv6":
                continue
            cnf = conf
            cnf['name'] = str(name)
            if types.get(str(cnf['type'])):
                types[str(cnf['type'])].append(cnf)
            else:
                types[str(cnf['type'])] = [cnf]
                
        # Check vpn is configured
        if os.path.exists('/etc/openvpn/vpn.conf'):
            userForm = tags.directive('form addUser')
        else:
            userForm = tags.strong["Please configure the VPN in order to add new users"]

        tuns = []
        # Call the handler functions with the stores
        ifs = Utils.getInterfaces()
        for k,v in types.items():
            if v:
                v.sort()
                for c,tun in enumerate(v):
                    status = tags.a(href='Start/%s/' % tun['name'])["Disconnected"]
                    if k == 'openvpn':
                        # Hunt TAP interfaces
                        if 'tap%s' % (c+1) in ifs:
                            status = tags.a(href='Stop/%s/' % tun['name'])["Connected"]

                    tuns.append((
                        status, 
                        tun['name'], 
                        tun['type'], 
                        tun['endpoint'], 
                        tags.a(href="Delete/%s/" % (tun['name']))["Delete"]
                    ))

        return ctx.tag[
                tags.h3[tags.img(src="/images/vpn.png"), self.text.vpnConfig],
                PageHelpers.TabSwitcher((
                    (self.text.vpnTabWindows, 'panelWindows'),
                    (self.text.vpnTabTCS, 'panelOpenVPN'),
                    (self.text.vpnTabUsers, 'panelVPNUsers'),
                    (self.text.vpnTabTun, 'panelTun')
                )),
                tags.div(id="panelWindows", _class="tabPane")[
                    tags.h3[self.text.vpnHeadingWindows],
                    tags.directive('form winForm'),
                ],
                tags.div(id="panelTun", _class="tabPane")[
                    tags.h3["Tunnels"],
                    PageHelpers.dataTable(['Status', 'Name', 'Type', 'Endpoint', ''], tuns),
                    tags.h3["Add tunnel"],
                    tags.directive('form addTun'), tags.br,
                ],
                tags.div(id="panelOpenVPN", _class="tabPane")[
                    tags.h3[self.text.vpnHeadingTCS],
                    tags.directive('form vpnForm'), tags.br,
                ],
                tags.div(id="panelVPNUsers", _class="tabPane")[
                    tags.h3[self.text.vpnHeadingTCSUsers],
                    tags.table(cellspacing=0,  _class='sortable')[
                        tags.thead(background="/images/gradMB.png")[
                            tags.tr[
                                tags.th(colformat="str")[self.text.vpnCertificateName],
                                tags.th[""],
                            ]
                        ],
                        tags.tbody[
                        [
                            tags.tr[
                                tags.td['.'.join(i.split('.')[:-1])],
                                tags.td[
                                    tags.a(
                                        href="Revoke/%s/" % '.'.join(i.split('.')[:-1]), 
                                        onclick="return confirm('%s');" % self.text.vpnConfirmRevoke
                                    )[ 
                                        tags.img(src="/images/ex.png")
                                    ]
                                ]
                            ]
                        for i in keys],
                        ]
                    ], tags.br,
                    tags.h3[self.text.vpnHeadingAddUser],

                    userForm
                ],
                PageHelpers.LoadTabSwitcher()
            ]

    def locateChild(self, ctx, segs):
        if segs[0]=="Revoke":
            return VPN.revoke_certificate(segs[1]).addBoth(lambda _:url.root.child('VPN')), ()
        if segs[0]=="Start":
            tunName = segs[1]
            # First check if the tunnel type is OpenVPN or something here. For now we just assume it is...
            return WebUtils.system('/etc/init.d/openvpn start %s-client' %tunName).addBoth(lambda _:url.root.child('VPN')), ()
        
        if segs[0]=="Stop":
            tunName = segs[1]
            # First check if the tunnel type is OpenVPN or something here. For now we just assume it is...
            return WebUtils.system('/etc/init.d/openvpn stop %s-client' %tunName).addBoth(lambda _:url.root.child('VPN')), ()
            
        return rend.Page.locateChild(self, ctx, segs)
            

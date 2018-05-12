from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
from twisted.internet.defer import deferredGenerator, waitForDeferred as wait
from twisted.internet import utils

import Tree, Settings, os
from Core import PageHelpers, AuthApacheProxy, Shorewall, Utils, confparse, WebUtils
from Pages import Tools
import formal

if os.path.exists('/etc/debian_version'):
    vpnInit = 'openvpn'
else:
    vpnInit = 'openvpn.vpn'

class Page(PageHelpers.DefaultPage):
    addSlash = True
    
    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2[self.text.tools]]

    def getWindowsVPN(self):
        """ Retrieve the windows VPN settings from the firewall rules table"""

        sw = self.sysconf.Shorewall.get('rules', [])

        winserv = ""
        external = ""
        enabled = False
        for en, i in sw:
            l = i.strip('\n').split()
            if l and (l[0]=="DNAT" or l[0]=="#DNAT"):
                if len(l) > 5 and l[3]=="47":
                    winserv = l[2].split(':')[-1]
                    if len(l) > 6:
                        external = l[6]
                    if l[0]=="DNAT":
                        enabled = True
                    if not en:
                        enabled = False
        
        return winserv, external, enabled

    def form_winForm(self, data):
        """ Windows VPN Form"""
        form = formal.Form()

        form.addField('windows', formal.Boolean(), label = self.text.vpnLabelWindows, description=self.text.vpnDescripWindows)
        form.addField('winip', formal.String(), label = self.text.vpnLabelWinserver)
        form.addField('winextip', formal.String(), label = self.text.vpnLabelExtwinserver,
            description = [self.text.vpnDescripExtwinserver])

        form.data['winip'], form.data['winextip'], form.data['windows'] = True = self.getWindowsVPN()

        form.addAction(self.submitWinForm)

        return form
        
    def submitWinForm(self, c, f, data):
        """ Validate the windows vpn form and create relevant configuration"""
        if not data['winip']:
            return url.root.child('VPN')


        confdata = self.sysconf.Shorewall

        rset = confdata.get('rules', [])

        rule = "DNAT    net     loc:%s  47      -       -               %s" % (data['winip'] or "", data['winextip'] or "")
        rule2 = "DNAT    net     loc:%s  tcp     1723    -               %s" % (data['winip'] or "", data['winextip'] or "")

        # Find such a rule and strip it:
        rsetnew = []
        for en,ru in rset:
            rusp = ru.split()
            try:
                if "DNAT" == rusp[0] and "47" == rusp[3]:
                    exists = True
                elif "DNAT" == rusp[0] and "1723" == rusp[4]:
                    exists = True
                else:
                    exists = False
            except:
                exists = False

            if not exists:
                rsetnew.append([en, ru])

        if data['windows']:
            rsetnew.append([1, rule.encode()])
            rsetnew.append([1, rule2.encode()])
        confdata['rules'] = rsetnew

        self.sysconf.Shorewall = confdata

        Utils.reconfigure('shorewall')
        WebUtils.system('shorewall restart')

        return url.root.child('VPN')

    @deferredGenerator
    def form_vpnForm(self, data):
        """ OpenVPN (TCS VPN) form""" 
        form = formal.Form()

        form.addField('openvpn', formal.Boolean(), label = self.text.vpnLabelOpenvpn, description=self.text.vpnDescripOpenvpn)

        form.addField('iprange1', formal.String(required=True), label = self.text.vpnRangeStart)
        form.addField('iprange2', formal.String(required=True), label = self.text.vpnRangeTo)

        form.addField('mtu', formal.String(), label = self.text.vpnMTU)

        form.addField('WINS', formal.String(), label = self.text.vpnWINSServer)
        form.addField('DNS', formal.String(), label = self.text.vpnDNSServer)
        form.addField('DOMAIN', formal.String(), label = self.text.vpnDomain)
        
        mq = utils.getProcessOutput('/bin/sh', ['-c', "route -n | grep -E \"(eth|tun|tap)\" | grep -v \"G\"  | awk '{print $1 \" \" $3}'"], errortoo=1)
        res = wait(mq)
        yield res
        routes = res.getResult()
        nr = []
        for ro in routes.split('\n'):
            if ro.strip('\n'):  
                nr.append(ro.strip())

        routes = nr
        del nr

        try:
            confFile = open('/etc/openvpn/vpn.conf', 'rt')
        except:
            confFile = [""]

        activeRoutes = []

        conf = {'mtu': '1400'}

        if os.path.exists('/etc/debian_version'):
            rc = utils.getProcessOutput(Settings.BaseDir + '/syscripts/rcStatus.py', [], errortoo=1)
        else:
            rc = utils.getProcessOutput('/bin/rc-status', ['default'], errortoo=1)
        res = wait(rc)
        yield res
        rc = res.getResult()
        vpnstat = ""
        for i in rc.split('\n'):
            if vpnInit in i:
                vpnstat = i 

        if "openvpn" in vpnstat:
            conf['openvpn'] = True

        for i in confFile:
            line = i.strip('\n')
            
            if "route" in line:
                # Activate a route and add it to the list if not there
                route = line.split('"')[1].split()
                tr = "%s %s" % (route[1], route[2])
                activeRoutes.append(tr.strip())
                if not tr in routes:
                    routes.append(tr.strip())

            if "server-bridge" in line:
                ips = line.split()
                conf['iprange1'] = ips[3]
                conf['iprange2'] = ips[4]

            if "dhcp-option" in line:
                sp = line.replace('"','').split()
                conf[sp[2]] = sp[3]

        conf['routes'] = activeRoutes

        print conf

        form.addField('routes', formal.Sequence(formal.String()),
           formal.widgetFactory(formal.CheckboxMultiChoice, [(i,i) for i in routes]), label = self.text.vpnRoutesPush)

        form.data = conf
        form.addAction(self.submitForm)
                
        yield form

    def form_addUser(self, data):
        """ Form for adding a user"""
        form = formal.Form()
        
        form.addField('name', formal.String(), label = self.text.vpnName)
        form.addField('mail', formal.String(), label = self.text.vpnMail) 
        form.addField('ip', formal.String(), label = self.text.vpnStaticIP)
        form.addField('mailKey', formal.Boolean(), label = self.text.vpnMailQuestion)

        form.addAction(self.newCert)
        return form

    def newCert(self, ctx, form, data):
        """Create a cert and sign it"""
        
        name = data['name'].replace(' ', '').replace('-', '')

        def mailUser(_):
        # Mail the key to the person
            if data['mailKey']:
                files = [
                     '/etc/openvpn/keys/%s.csr' % name, 
                     '/etc/openvpn/keys/%s.crt' % name,
                     '/etc/openvpn/keys/%s.key' % name,
                     '/etc/openvpn/keys/ca.crt',
                     '/tmp/TCS.ovpn',
                     '/usr/local/tcs/tums/packages/openvpn-install.exe'
                    ]
                tempconf = """client
dev tap
proto udp
remote tcs-gw.%s
port 1194
resolv-retry infinite
redirect-gateway def1
nobind
persist-key
persist-tun
ca ca.crt
cert %s.crt
key %s.key
comp-lzo
verb 3
keepalive 10 360
tls-timeout 300""" % (self.sysconf.ExternalName, name, name)
                l = open('/tmp/TCS.ovpn', 'wt')
                l.write(tempconf)
                l.close()
            
                mailtext = """Your TCS VPN account has been created.

Please see the attached files to configure your VPN. Save 
all the attached files to a folder on your computer and 
run the attached openvpn-install.exe program. Copy
the rest of the attachments to this email to the folder
C:\\Program Files\\OpenVPN\\config\\

To connect to the VPN find the icon in the system tray 
of two red computers, and double click on it. 

You may be required to edit the TCS.ovpn file, and 
replace the address on the line "remote %s" with 
the external address of your server.

Should you have any trouble following these instructions 
please contact Thusa at support@thusa.co.za or via
telephone at +27 31 277 1250.""" % (self.sysconf.ExternalName,)
                try:
                    Utils.sendMail("TCS Server <root@%s>" % Settings.defaultDomain, [data['mail']], self.text.vpnConfigDetails, 
                        mailtext, files)
                except Exception, c: 
                    print c
                    Utils.exceptionOccured(c)

                return url.root.child('VPN')
        cmd = 'cd /etc/openvpn/easy-rsa; source /etc/openvpn/easy-rsa/vars; /etc/openvpn/easy-rsa/pkitool %s' % (name, )
            
        utils.getProcessOutput('/bin/sh', ['-c', cmd], errortoo=1).addCallbacks(mailUser, mailUser)

        if data['ip']:
            WebUtils.system('echo ifconfig-push %s 255.255.255.0 > /etc/openvpn/vpn-ccd/%s' % (data['ip'], name))
        
        return url.root.child('VPN')

    def submitForm(self, ctx, form, data):
        """ Reconfigura the standard VPN"""
        if data['openvpn']:
            # Enable vpn
            WebUtils.system('ln -s /etc/init.d/openvpn /etc/init.d/%s > /dev/null 2>&1' % vpnInit)
            if os.path.exists('/etc/debian_version'):
                WebUtils.system('update-rc.d %s defaults' % vpnInit)
            else:
                WebUtils.system('rc-update -a %s default' % vpnInit)
        else:
            if os.path.exists('/etc/debian_version'):
                WebUtils.system('update-rc.d %s defaults' % vpnInit)
            else:
                WebUtils.system('rc-update -d %s default' % vpnInit)

        # Save the config options

        servIp = '.'.join(data['iprange1'].split('.')[:3]) + '.1' # Take the IP network and /24 server is .1
        ip1 = data['iprange1']
        ip2 = data['iprange2']

        confData = """dev tap0
proto udp
port 1194
ifconfig-pool-persist /etc/openvpn/vpn_pool
client-config-dir /etc/openvpn/vpn-ccd/
keepalive 10 120
client-to-client
tls-timeout 300
comp-lzo
verb 3
persist-key
persist-tun
ca   /etc/openvpn/keys/ca.crt
cert /etc/openvpn/keys/vpn.crt
key  /etc/openvpn/keys/vpn.key
dh   /etc/openvpn/keys/dh1024.pem

server-bridge %s 255.255.255.0 %s %s
ifconfig %s 255.255.255.0
""" % (servIp, ip1, ip2, servIp)
        
        if data['routes']:
            for ro in data['routes']:
                confData += 'push "route %s"\n' % (ro,)

        for i in ['DNS', 'WINS', 'DOMAIN']:
            if data[i]:
                confData += 'push "dhcp-option %s %s"\n' % (i, data[i])
        
        confFile = open('/etc/openvpn/vpn.conf', 'wt')
                
        confFile.write(confData)
        confFile.close()

        if data['openvpn']:
            WebUtils.system('/etc/init.d/%s restart' % vpnInit)
        else:
            WebUtils.system('/etc/init.d/%s stop' % vpnInit)
            
        return url.root.child('VPN')

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Tools.Page.sideMenu(Tools.Page(None, self.db), ctx, data),]

    def render_content(self, ctx, data):
        keys = [i for i in os.listdir('/etc/openvpn/keys/') if 'key' in i]

        keys.sort()
        for key in ['vpn.key', 'ca.key']:
            try:
                keys.remove(key)
            except:
                pass

        return ctx.tag[
                tags.h2[tags.img(src="/images/vpn.png"), self.text.vpnConfig],
                PageHelpers.TabSwitcher((
                    (self.text.vpnTabWindows, 'panelWindows'),
                    (self.text.vpnTabTCS, 'panelOpenVPN'),
                    (self.text.vpnTabUsers, 'panelVPNUsers')
                )),
                tags.div(id="panelWindows", _class="tabPane")[
                    tags.h3[self.text.vpnHeadingWindows],
                    tags.directive('form winForm'),
                ],
                tags.div(id="panelOpenVPN", _class="tabPane")[
                    tags.h3[self.text.vpnHeadingTCS],
                    tags.directive('form vpnForm'), tags.br,
                ],
                tags.div(id="panelVPNUsers", _class="tabPane")[
                    tags.h3[self.text.vpnHeadingTCSUsers],
                    tags.table(cellspacing=0,  _class='listing')[
                        tags.thead(background="/images/gradMB.png")[
                            tags.tr[
                                tags.th[self.text.vpnCertificateName],
                                tags.th[""],
                            ]
                        ],
                        tags.tbody[
                        [
                            tags.tr[
                                tags.td['.'.join(i.split('.')[:-1])],
                                tags.td[tags.a(href="Revoke/%s/" % '.'.join(i.split('.')[:-1]), onclick="return confirm('%s');" % self.text.vpnConfirmRevoke)[ 
                                    tags.img(src="/images/ex.png")]
                                ]
                            ]
                        for i in keys],
                        ]
                    ], tags.br,
                    tags.h3[self.text.vpnHeadingAddUser],
                    tags.directive('form addUser')
                ],
                PageHelpers.LoadTabSwitcher()
            ]

    def locateChild(self, ctx, segs):
        if segs[0]=="Revoke":
            WebUtils.system('cd /etc/openvpn/easy-rsa/; source /etc/openvpn/easy-rsa/vars; /etc/openvpn/easy-rsa/revoke-full %s; rm /etc/openvpn/keys/%s.*' % (
                segs[1], segs[1]))

            return url.root.child('VPN'), ()

        return rend.Page.locateChild(self, ctx, segs)
            

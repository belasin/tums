from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
import time, formal, LDAP, os
import Tree, Settings
from Core import PageHelpers, confparse, Utils, WebUtils
from Pages import Users, Tools

class Page(PageHelpers.DefaultPage):
    def reloadConfig(self):
        # Call configurator to reconfigure squid
        if os.path.exists('/etc/debian_version'):
            WebUtils.system(Settings.BaseDir+'/configurator --squid; /usr/sbin/squid3 -k reconfigure > /dev/null 2>&1')
        else:
            WebUtils.system(Settings.BaseDir+'/configurator --squid; /etc/init.d/squid reload > /dev/null 2>&1')

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Tools"]]

    def form_authentication(self, data):
        form = formal.Form()

        form.addField('ldapauth', formal.Boolean(), label = "Default local authentication")

        form.addField('adauth', formal.Boolean(), label = "Active Directory authentication")

        form.addField('adserv', formal.String(), label = "Active Directory Server")
        form.addField('addom', formal.String(), label = "Active Directory Domain")

        form.addAction(self.submitAuth)

        k = self.sysconf.ProxyConfig
        data = {}
        if k.get('adauth', ''):
            data['ldapauth'] = False
            data['adauth'] = True
        else:
            data['ldapauth'] = True
            data['adauth'] = False

        data['adserv'] = k.get('adserver', u'').encode()
        data['addom'] = k.get('addom', u'').encode()

        form.data = data

        return form

    def submitAuth(self, ctx, form, data):
        k = self.sysconf.ProxyConfig
        if data['ldapauth']:
            k['adauth'] = False
        elif data['adauth']:
            k['adauth'] = True
        elif not data['adauth']:
            k['adauth'] = False

        if data['adserv']:
            k['adserver'] = data['adserv'] or ""
            k['addom'] = data['addom'] or ""
        else:
            k['adauth'] = False

        self.sysconf.ProxyConfig = k
        self.reloadConfig()
        return url.root.child('Squid')

    def form_addDomain(self, data):
        form = formal.Form()
        form.addField('domain', formal.String(required=True), label = "Domain name",
            description = "Domain name to allow. Preceede the domain with a full stop to include all subdomains")
        form.addAction(self.submitDomain)
        return form

    def submitDomain(self, ctx, form, data):
        k  = self.sysconf.ProxyAllowedDomains
        k.append(data['domain'].encode())
        self.sysconf.ProxyAllowedDomains = k
        self.reloadConfig()
        return url.root.child('Squid')
        
    def form_addDest(self, data):
        form = formal.Form()
        form.addField('ip', formal.String(required=True), label = "Destination IP or Network")
        form.addAction(self.submitDest)
        return form

    def submitDest(self, ctx, form, data):
        k = self.sysconf.ProxyAllowedDestinations
        k.append(data['ip'].encode())
        self.sysconf.ProxyAllowedDestinations = k
        self.reloadConfig()
        return url.root.child('Squid')
        
    def form_addHost(self, data):
        form = formal.Form()
        form.addField('ip', formal.String(required=True), label = "Computer IP or Network")
        form.addAction(self.submitHost)
        return form

    def submitHost(self, ctx, form, data):
        k = self.sysconf.ProxyAllowedHosts
        k.append(data['ip'].encode())
        self.sysconf.ProxyAllowedHosts = k
        self.reloadConfig()
        return url.root.child('Squid')

    def form_addBlock(self, data):
        form = formal.Form()
        form.addField('host', formal.String(required=True), label = "Domain name", 
            description = "Domain name to block. Preceede the domain with a full stop to include all subdomains")
        form.addAction(self.submitBlock)
        return form

    def submitBlock(self, ctx, form, data):
        k = self.sysconf.ProxyBlockedDomains
        k.append(data['host'].encode())
        self.sysconf.ProxyBlockedDomains= k
        self.reloadConfig()
        return url.root.child('Squid')

    def locateChild(self, ctx, segs):
        if segs[0]=="Delete":
            qtype = segs[1]
            num = int(segs[2])

            if qtype == "Domain":
                k = self.sysconf.ProxyAllowedDomains
                del k[num]
                self.sysconf.ProxyAllowedDomains = k

            elif qtype == "BDomain":
                k = self.sysconf.ProxyBlockedDomains
                del k[num]
                self.sysconf.ProxyBlockedDomains = k 
                
            elif qtype == "Destination":
                k = self.sysconf.ProxyAllowedDestinations
                del k[num]
                self.sysconf.ProxyAllowedDestinations = k

            elif qtype == "Host":
                k = self.sysconf.ProxyAllowedHosts
                del k[num]
                self.sysconf.ProxyAllowedHosts = k

            else:
                return url.root.child('Squid'), ()
            
            self.reloadConfig()
            
            return url.root.child('Squid'), ()
            
        return rend.Page.locateChild(self, ctx, segs)

    def getData(self):
        #allow_domains  allow_dst  allow_hosts
        doms = self.sysconf.ProxyAllowedDomains
        dsts = self.sysconf.ProxyAllowedDestinations
        ips = self.sysconf.ProxyAllowedHosts
        bdoms = self.sysconf.ProxyBlockedDomains
        domains = []
        cnt = 0 
        for ln in doms:
            l = ln.strip('\n')
            if l:
                domains.append([l, tags.a(href="Delete/Domain/%s/" % cnt, onclick="return confirm('Are you sure you want to delete this entry?');")[tags.img(src="/images/ex.png")] ] )
            cnt += 1

        bdomains = []
        cnt = 0 
        for ln in bdoms:
            l = ln.strip('\n')
            if l:
                bdomains.append([l, tags.a(href="Delete/BDomain/%s/" % cnt, onclick="return confirm('Are you sure you want to delete this entry?');")[tags.img(src="/images/ex.png")] ] )
            cnt += 1

        destinations = []
        cnt = 0
        for ln in dsts:
            l = ln.strip('\n')
            if l:
                destinations.append([l, tags.a(href="Delete/Destination/%s/" % cnt, onclick="return confirm('Are you sure you want to delete this entry?');")[tags.img(src="/images/ex.png")] ] )
            cnt += 1

        hosts = []
        cnt = 0
        for ln in ips:
            l = ln.strip('\n')
            if l:
                hosts.append([l, tags.a(href="Delete/Host/%s/" % cnt, onclick="return confirm('Are you sure you want to delete this entry?');")[tags.img(src="/images/ex.png")] ] )
            cnt += 1

        return domains, destinations, hosts, bdomains

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Tools.Page.sideMenu(Tools.Page(None, self.db), ctx, data)]

    def render_content(self, ctx, data):
        squidData = self.getData()
        return ctx.tag[
            tags.h2[tags.img(src='/images/proxy.png'), " Web Proxy"],
            PageHelpers.TabSwitcher((
                ('Proxy setup', 'panelProxySetup'),
                ('Allowed Domains', 'panelAdom'),
                ('Blocked Domains', 'panelBdom'),
                ('Allowed Destination', 'panelAdest'),
                ('Allowed Computers', 'panelAcomp'),
            )),
            tags.div(id="panelProxySetup", _class="tabPane")[
                tags.h3["Proxy setup"],
                tags.directive('form authentication'),
            ],
            tags.div(id="panelAdom", _class="tabPane")[
                tags.h3["Allowed Domains"],
                PageHelpers.dataTable(['Domain', ''], squidData[0]),
                tags.h3["Add Domain"],
                tags.directive('form addDomain'),
            ],
            tags.div(id="panelBdom", _class="tabPane")[
                tags.h3["Blocked Domains"],
                PageHelpers.dataTable(['Domain', ''], squidData[3]),
                tags.h3["Add Domain"],
                tags.directive('form addBlock'),
            ],
            tags.div(id="panelAdest", _class="tabPane")[
                tags.h3["Allowed Destination Networks"],
                PageHelpers.dataTable(['IP Address/Network', ''], squidData[1]),
                tags.h3["Add IP address or network"],
                tags.directive('form addDest'),
            ],
            tags.div(id="panelAcomp", _class="tabPane")[
                tags.h3["Allowed Computers"],
                PageHelpers.dataTable(['IP Address/Network', ''], squidData[2]),
                tags.h3["Add IP address or network"],
                tags.directive('form addHost'),
            ],
        PageHelpers.LoadTabSwitcher()
    ]

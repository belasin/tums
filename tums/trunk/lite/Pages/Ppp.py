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

class Page(PageHelpers.DefaultPage):
    addSlash = True
    
    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Tools"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Tools.Page.sideMenu(Tools.Page(None, self.db), ctx, data)]

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

    def form_addPPP(self, ctx):
        form = formal.Form()
        form.addField('link', formal.String(required=True),
            formal.widgetFactory(formal.SelectChoice, options = [(i,i) for i in self.getEthernets() ]), label = "Ethernet Link")

        form.addField('username', formal.String(required=True), label = "Username")
        form.addField('password', formal.String(required=True), label = "Password")

        form.addField('localOnly', formal.Boolean(), label = "Local Only", description="Checking this box will cause only South African traffic to be routed over this link")
        form.addField('defaultRoute', formal.Boolean(), label = "Default Routes", description="Make this the default internet connection")
        form.addField('defaultDNS', formal.Boolean(), label = "Default DNS", description="Use the DNS servers that this connection provides")
        form.addAction(self.addInterface)

        return form

    def addInterface(self, ctx, form, data):
        wanDevices = self.sysconf.WANDevices

        devices = []
        for i in xrange(20):
            n = "ppp%s" % i
            if not (n in wanDevices.keys()):
                devices.append(n)
        this = devices[0]

        if data['defaultRoute']:
            defaults = ['defaultroute']
        else:
            defaults = []

        if data['defaultDNS']:
            defaults.append('usepeerdns')

        seg = {
            'pppd': defaults, 
            'username': data['username'],
            'password': data['password'],
            'link': data['link'],
            'plugins': 'pppoe'
        }

        wanDevices[this] = seg

        self.sysconf.WANDevices = wanDevices
        if data['localOnly']:
            self.sysconf.LocalRoute = this

        WebUtils.system('/usr/local/tcs/tums/configurator --quagga')

        if os.path.exists('/etc/debian_version'):
            WebUtils.system('/etc/init.d/quagga restart')
            WebUtils.system('/usr/local/tcs/tums/configurator --debnet')
        else:
            WebUtils.system('/etc/init.d/zebra restart')
            WebUtils.system('/usr/local/tcs/tums/configurator --net')
            WebUtils.system('ln -s /etc/init.d/net.lo /etc/init.d/net.%s' % this)
            WebUtils.system('rc-update -a net.%s boot' % this)

        return url.root.child('PPP')

    def render_content(self, ctx, data):
        wanDevices = self.sysconf.WANDevices
        wanTable = []
        
        pppDevs = self.getPeers()

        for iface, detail in wanDevices.items():
            if iface in pppDevs:
                peerStatus = tags.a(href=url.root.child("PPP").child("Disconnect").child(iface), title="Connected: Click to disconnect.")[tags.img(src='/images/connect.png')]
            else:
                peerStatus = tags.a(href=url.root.child("PPP").child("Connect").child(iface), title="Disconnected: Click to connect.")[tags.img(src='/images/noconnect.png')]
            options = ""
            if detail.get('pppd', None):
                if 'defaultroute' in detail['pppd']:
                    options += "Default Route"

            if self.sysconf.LocalRoute == iface:
                options += "Local Only Route"

            type = "PPP"
            if detail.get('plugins', None):
                if detail['plugins'] == "pppoe":
                    type = "PPPoE"

            wanTable.append((
                peerStatus,
                iface,
                detail.get('link', ''),
                detail.get('username', ''),
                detail.get('password', ''), # XXX Remove Me!
                type,
                options,
                tags.a(href=url.root.child("PPP").child("Delete").child(iface))[tags.img(src="/images/ex.png")]
            ))

        return ctx.tag[
            tags.h3[tags.img(src="/images/netdrive.png"), " PPPoE Interfaces"],
            PageHelpers.dataTable(['', 'Interface', 'Link', 'Username', 'Password', 'Type', 'Options', ''],
                wanTable
            ),
            tags.br,
            tags.h3["Add PPP Interface"],
            tags.directive('form addPPP')
        ]

    def locateChild(self, ctx, segs):
        if segs[0] == "Connect":
            if os.path.exists('/etc/debian_version'):
                unitNumber = segs[1].strip('ppp')
                WebUtils.system('pon wan%s' % unitNumber)
            else:
                WebUtils.system('/etc/init.d/net.%s start' % segs[1])
            return url.root.child('PPP'), ()
                
        if segs[0] == "Disconnect":
            if os.path.exists('/etc/debian_version'):
                unitNumber = segs[1].strip('ppp')
                WebUtils.system('poff wan%s' % unitNumber)
            else:
                WebUtils.system('/etc/init.d/net.%s stop' % segs[1])
            return url.root.child('PPP'), ()

        if segs[0] == "Delete":
            # Delete one
            if not os.path.exists('/etc/debian_version'):
                WebUtils.system('rc-update -d net.%s' % segs[1])
            wanDevices = self.sysconf.WANDevices
            if segs[1] in wanDevices:
                del wanDevices[segs[1]]
            else:
                pass
            self.sysconf.WANDevices = wanDevices 
            
            if self.sysconf.LocalRoute == segs[1]:
                self.sysconf.LocalRoute = ""

            return url.root.child('PPP'), ()
        return rend.Page.locateChild(self, ctx, segs)
            

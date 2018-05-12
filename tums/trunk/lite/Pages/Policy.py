from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP
from Core import PageHelpers, AuthApacheProxy, confparse, Utils, WebUtils
from Pages import Tools
import formal

class Page(PageHelpers.DefaultPage):
    addSlash = True

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2[self.text.tools]]

    def testProxy(self):
        transwww = self.sysconf.Shorewall['rules']

        for en, ru in transwww:
            if "REDIRECT" in ru and "tcp" in ru and "80" in ru:
                return True


    def removeProxy(self):
        transwww = self.sysconf.Shorewall
        newRules = []
        for en, ru in transwww['rules']:
            if "REDIRECT" in ru and "tcp" in ru and "80" in ru and "8080" in ru:
                print "clipping"
            else:
                newRules.append([en, ru])

        transwww['rules'] = newRules
        self.sysconf.Shorewall = transwww

    def addProxy(self):
        transwww = self.sysconf.Shorewall
        # XXX We should have support for multiple LANPrimary interfaces here.
        transwww['rules'].append([
            1, "REDIRECT loc      8080     tcp     80      -     !%s" % (self.sysconf.EthernetDevices[self.sysconf.LANPrimary]['network'])
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

        form.addAction(self.submitForm)
        return form

    def submitForm(self, ctx, form, data):
        
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

        return url.root.child('Policy')

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Tools.Page.sideMenu(Tools.Page(None, self.db), ctx, data)]

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.h3[tags.img(src="/images/netdrive.png"), " System Policy"],
            PageHelpers.TabSwitcher((
                ('Internet Policy', 'panelInetpol'),
            )),
            tags.div(id="panelInetpol", _class="tabPane")[
                tags.h3["Internet Policy"], 
                tags.directive('form inetPol')
            ], 
            PageHelpers.LoadTabSwitcher()
        ]


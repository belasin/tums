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
        return ctx.tag[tags.h2[self.text.tools]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Tools.Page.sideMenu(Tools.Page(None, self.db), ctx, data)]

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.h3[tags.img(src="/images/netdrive.png"), " Network Setup"],
            PageHelpers.TabSwitcher((
                ('Static Routes', 'panelStatic'),
                ('BGP', 'panelBGP'), 
                ('IPv6 Tunnel', 'panelTunnel')
            )),
            tags.div(id="panelStatic", _class="tabPane")[
            ],
            tags.div(id="panelBGP", _class="tabPane")[
            ],
            tags.div(id="panelTunnel", _class="tabPane")[
                tags.h3["Configure IPv6 Tunnel"],
                tags.directive('form tunnelConf')
            ],
            PageHelpers.LoadTabSwitcher(),
        ]

    def locateChild(self, ctx, segs):
        #if segs[0]=="Delete":

        return rend.Page.locateChild(self, ctx, segs)
            

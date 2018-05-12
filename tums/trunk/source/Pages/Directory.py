from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP
from Core import PageHelpers, AuthApacheProxy, confparse, Utils, WebUtils
from Pages import Tools
from Pages.Users import Domains
import formal

class Page(Tools.Page):
    addSlash = True

    def form_addDomain(self, data):
        form = formal.Form()
        form.addField('domain', formal.String(), label = self.text.profileSource)
        form.addAction(self.submitForm)
        return form

    def submitForm(self, ctx, form, data):
        
        return WebUtils.system("" % (source, dest)).addCallback(ret)

    def form_renameDomain(self, data):
        form = formal.Form()
        form.addField('source', formal.String(), label = "Domain")
        form.addField('dest',   formal.String(), label = "New name")
        form.addAction(self.submitRename)
        return form

    def submitRename(self, ctx, form, data):

        return 

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.h3[tags.img(src="/images/cluster.png"), " "],
            PageHelpers.dataTable(['',""], tab),
            tags.br,
            tags.div(id="ren", style="display:none;")[
                tags.directive('form renameDomain')
            ]
        ]

    def locateChild(self, ctx, segs):
        def ret(_):
            return url.root.child('Directory'), ()

        if segs[0] == "rename":
            return ret(1)

        if segs[0] == "delete":
            return ret(1)

        return rend.Page.locateChild(self, ctx, segs)


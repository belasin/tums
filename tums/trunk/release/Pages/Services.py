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

class Page(Tools.Page):
    addSlash = True

    def form_rename(self, data):
        form = formal.Form()

        form.addField('descr', formal.String(), label = "Description")
        form.addField('init', formal.String(), label = "RC Script")
        form.addField('proc', formal.String(), label = "Process ID", description="Leave blank if same as RC script")

        form.addAction(self.submitForm)

        return form

    def submitForm(self, ctx, form, data):
        descr = data['descr'].encode("ascii", "replace")
        proc = data['proc'].encode("ascii", "replace")
        init = data['init'].encode("ascii", "replace")
        if not data['proc']:
            proc = init

        return url.root.child('Services')

    def render_content(self, ctx, data):
        tab = []

        return ctx.tag[
            tags.h3[tags.img(src="/images/cluster.png"), " Services"],
            PageHelpers.dataTable(['Service Description',"RC Script","Process Identifier"], tab),
            tags.br, 
            tags.div(id="ren", style="display:none;")[
                tags.directive('form rename')
            ]
        ]

    def locateChild(self, ctx, segs):
        def ret(_):
            return url.root.child('Services'), ()

        if segs[0] == "Delete":
            #return WebUtils.system("rm /usr/local/tcs/tums/profiles/%s" % (segs[1])).addCallback(ret)
            pass

        return rend.Page.locateChild(self, ctx, segs)


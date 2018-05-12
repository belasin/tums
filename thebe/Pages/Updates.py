from enamel import authentication, deployment, pages, servers, storage, deferreds, tags
from enamel import sql, form, url
import enamel, sha

from custom import Widgets

from twisted.internet import utils

from Pages import ServersManage

from lib import iter, PageBase

class Page(PageBase.Page):
    arbitraryArguments = True
    def document(self):
        return pages.template('defaultc.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Servers"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[""]

    def form_approveUpdate(self, data):
        f = form.Form()
        f.addField('package', form.String(required=True), label = "Package")
        f.addField('version', form.String(required=True), label = "Version")

        f.addAction(self.approveUpdate)

        return f
    
    def approveUpdate(self, ctx, f, data):
        def redirectPage(_):
            return url.root.child('Updates')
        
        return self.enamel.storage.approveUpdate(
            data['package'], 
            data['version']
        ).addBoth(redirectPage)

    def render_content(self, ctx, data):
        def renderUpdates(updates):
            trows = []
            for i in updates:
                trows.append((
                        i[1],
                        i[2], 
                        tags.a(href="Delete/%s" % i[0])["Delete"]
                    ))
 
            return ctx.tag[
                tags.h3["Approved Updates"],
                tags.br,
                self.dataTable(["Package","Version", ""], trows, sortable=True),
                tags.br,
                tags.h3["Approve Update"],
                tags.directive('form approveUpdate')
            ]

        return self.enamel.storage.getApprovedUpdates().addBoth(renderUpdates)

from enamel import authentication, deployment, pages, servers, storage, deferreds, tags
from enamel import sql, form, url
import enamel, sha

from custom import Widgets
from lib import web, PageBase
from twisted.internet import utils

class Page(PageBase.Page):
    arbitraryArguments = True # Enable REST style arguments to the page

    def document(self):
        return pages.template('defaultc.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Thebe Globals"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[""]

    def form_adminpassword(self, data):
        addServer = form.Form()
        addServer.addField('password', form.String(), label = "Administrator Password")
        addServer.addAction(self.changeAdminPass)
        return addServer

    def changeAdminPass(self, ctx, form, data):
        def setPasswords(servers):
            for i in servers:
                print "Sending changepass for", i[1]
                self.enamel.tcsClients.sendCommand(i[0], 'adminpass', [data['password'].encode()], '')
            return url.root.child('Thebe').child('Globals')
        return self.enamel.storage.getServers().addCallback(setPasswords)

    def rollupBlock(self, title, content):
        return tags.div(_class="roundedBlock")[title,tags.div[content]]

    def render_content(self, ctx, data):
        if self.avatarId.username != "colin":
            return ctx.tag['Feature in development']
            
        def rendercont(updated):
            return ctx.tag[
                tags.h3["Global Changes"],
                web.TabSwitcher([
                    ("Admin Password", 'adminpass'),
                    ("TUMS Updates", 'updatetums'),
                ]),   
                tags.div(id="updatetums", _class="tabPane")[
                    tags.h3["Update TUMS"],
                    updated and "Update sent" or tags.a(href="Update/")["Update all now"],
                ],
                tags.div(id="adminpass", _class="tabPane")[
                    tags.h3["Change Administrator Password"],
                    tags.directive('form adminpassword')
                ],
                web.LoadTabSwitcher()
            ]        
        def updateTUMS(servers):
            for i in servers:
                self.enamel.tcsClients.sendCommand(i[0], 'tumsupgrade', [], '')
            return rendercont(True)

        if self.arguments and self.arguments[0] == "Update":
            return self.enamel.storage.getServers().addCallback(updateTUMS)
        else:
            return rendercont(False)

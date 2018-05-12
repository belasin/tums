from enamel import authentication, deployment, pages, servers, storage, deferreds, tags
from enamel import sql, form, url
import enamel, sha

from custom import Widgets

from twisted.internet import utils
from twisted.internet.defer import deferredGenerator, waitForDeferred as wait

from lib import system, log, PageBase

class Page(PageBase.Page):
    arbitraryArguments = True # Enable REST style arguments to the page

    def document(self):
        return pages.template('defaultc.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Servers"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[""]

    def rollupBlock(self, title, content):
        return tags.div(_class="roundedBlock")[tags.h1[title],tags.div[content]]

    def form_global(self, data):
        f = form.Form()

        f.addField('command', form.String(), label = "Command")

        f.addAction(self.sendCommand)

        return f

    def sendCommand(self, c, f, data):
        def send(servers):
            for i in servers:
                print i
                self.enamel.tcsClients.sendMessage(i[0], "execute::%s" % data['command'].encode())

            return url.root.child('Dashboard')
        return self.enamel.storage.getServers().addCallback(send)

    
    def render_content(self, ctx, data):
        
        return ctx.tag[
            tags.h1["Global command"],
            tags.p["Warning: This will send the command to all servers"],
            tags.directive('form global')
        ]



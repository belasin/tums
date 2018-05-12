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
        return ctx.tag[tags.h2["Server Management"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[""]

    def rollupBlock(self, title, content):
        return tags.div(_class="roundedBlock")[tags.h1[title],tags.div[content]]

    def updatesSent(self, ctx):
        return ctx.tag[
            "Update sent. ",
            tags.a(href=url.root.child('Servers').child('Manage').child(self.arguments[0]))[
                "Back to server management"
            ]
        ]

    def render_content(self, ctx, data):
        def renderServerManager(ports, events, updates, server):
            reachability = [i[1] for i in ports]
            services = ["Vulani", "SMTP", "POP3", "IMAP"]

            if server[1] in self.enamel.tcsMaster.connectedNodes:
                ThiveReach = "Online"
            elif server[1] in self.enamel.tcsMaster.knownNodes:
                ThiveReach = "Online"
            else:
                ThiveReach = "Offline"


            tdata = [
                ("Server", tags.a(href="http://%s:9682/auth/"%server[4])[server[1]]), 
                ("Status", ThiveReach), 
                ("Services", tags.table[
                    [
                        tags.tr[
                            tags.td[service], 
                            tags.td[": ", reachability[k] and "Available" or "Offline"]
                        ]
                        for k, service in enumerate(services)
                    ]
                ]),
                ("Performance", tags.div[
                    tags.strong["Load"],tags.br,
                    tags.img(src='/RRD?source=%s&type=load&timeframe=-24h' % self.arguments[0]),
                    tags.br,
                    tags.strong["Mail"],tags.br,
                    tags.img(src='/RRD?source=%s&type=exim&timeframe=-24h' % self.arguments[0]),
                    tags.br,
                    tags.strong["Latency"],tags.br,
                    tags.img(src='/RRD?source=%s&type=latency&timeframe=-12h' % server[1]),
                ]),
                ("Updates", tags.table[
                    [
                        tags.tr[
                            #tags.td[tags.a(href='Package/%s/' % i[2])['Send Update']],
                            tags.td[i[2]], 
                            tags.td[i[3].ctime()]
                        ]
                    for i in updates]
                ]),
                ("Event Log", tags.table[
                    [
                        tags.tr[
                            tags.td[i[0].ctime()],
                            tags.td[tags.strong[log.formatLogType(i[1].encode())]],
                            tags.td[log.formatLogMessage(i[1].encode(), i[2].encode())]
                        ]
                        for i in events
                    ]
                ])
            ]

            return ctx.tag[
                tags.table[
                    [
                    tags.tr[
                        tags.td(valign="top")[tags.strong[i]], 
                        tags.td[j]
                    ]
                    for i,j in tdata]
                ]
            ]

        def getPorts(*a):
            return system.portCheck([9682, 25, 80, 110, 143], a[-1][2].encode()).addCallback(renderServerManager, *a)

        def getEvents(*a):
            return self.enamel.storage.getServerEvents(int(self.arguments[0])).addCallback(getPorts, *a)

        def getUpdates(*a):
            return self.enamel.storage.getUpdates(int(self.arguments[0])).addCallback(getEvents, *a)

        if len(self.arguments)>1:
            if self.arguments[1] == "Update":
                # Perform an update and continue rendering
                self.enamel.tcsClients.sendCommand(int(self.arguments[0]), 'tumsupgrade', [], '')
                return self.updatesSent(ctx)

            elif self.arguments[1] == "Package":
                self.enamel.tcsClients.sendCommand(int(self.arguments[0]), 'updatepackage', [self.arguments[2]], '')
                return self.updatesSent(ctx)

            elif self.arguments[1] == "AllPackage":
                def sendUpdates(updates):
                    l = [i[2] for i in updates]
                    self.enamel.tcsClients.sendCommand(int(self.arguments[0]), 'updatepackage', l, '')
                    return self.updatesSent(ctx)
                return self.enamel.storage.getUpdates(int(self.arguments[0])).addCallback(sendUpdates, *a)

        return self.enamel.storage.getServer(int(self.arguments[0])).addCallback(getUpdates)



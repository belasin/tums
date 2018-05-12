from enamel import authentication, deployment, pages, servers, storage, deferreds, tags
from enamel import sql, form, url
import enamel, sha

from custom import Widgets

from twisted.internet import utils

from Pages import ServersManage

from lib import iter, PageBase

class Page(PageBase.Page):
    arbitraryArguments = True
    childPages = {
        "Manage" : ServersManage.Page,
    }

    def document(self):
        return pages.template('defaultc.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Servers"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[""]

    def rollupBlock(self, title, content):
        return tags.div(_class="roundedBlock")[tags.h1[title],tags.div[content]]

    # Change the current graph view
    def form_switchView(self, data):
        f = form.Form()
        f.addField('view', form.String(required = True), 
            form.widgetFactory(form.SelectChoice, options = (
                ('load', 'System Load'),
                ('latency', 'Latency'),
                ('mailq',   'Mail Queue'),
                ('internet', 'Internet Traffic'),
                ('mailrate', 'Mail Rate')
            )),
            label = "Change view"
        )
        f.addAction(self.submitView)
        return f

    def submitView(self, c, f, data):
        return url.root.child('Servers').child(data['view'].encode())

    def dataTable(self, headings, content, sortable = False):
        """ Produces a tabular listing which is either sortable or not. Sortable expects headings to be a 
            list of tuples, but if it is not a list of tuples the 'string' type will be assumed for every cell """

        if sortable:
            if isinstance(headings[0], tuple):
                header = [ tags.th(colformat=j)[i] for j,i in headings ]
            else:
                header = [ tags.th(colformat='istr')[i] for i in headings ]
            tclass = 'sortable'
        else:
            header = [ tags.th[i] for i in headings ]
            tclass = 'listing'

        return tags.table(cellspacing=0,  _class=tclass)[
            tags.thead(background="/images/gradMB.png")[
                tags.tr[
                    header
                ]
            ],
            tags.tbody[
            [   
                tags.tr(style="background:#%s" % (row[0] and "b7ffb0" or "ffb0b0"))[ 
                    [tags.td[col] for col in row[1:]] 
                ]
            for row in content],
            ]
        ]

    def render_content(self, ctx, data):
        def renderServers(servers):
            servers2 = {}
            for s in servers:
                if s[1] in self.enamel.tcsMaster.connectedNodes:
                    servers2[s[1]] = ('Online', s[1], s[4], s[0])
                elif s[1] in self.enamel.tcsMaster.knownNodes:
                    servers2[s[1]] = ('Online (No Direct)', s[1], s[4], s[0])
                else:
                    servers2[s[1]] = ('Offline', s[1], s[2], s[0])

            def getGraph(server, canonical):
                # Returns the right graph image or structure for this particular view mode
                if (len(self.arguments) < 1) or (self.arguments[0] == 'load'):
                    return tags.img(src="/RRD?source=%s&type=load&timeframe=-7d&width=200&height=50&nog=yes" % (server))
                
                if self.arguments[0] == 'latency':
                    return tags.img(src="/RRD?source=%s&type=latency&timeframe=-7d&width=200&height=50&nog=yes" % (canonical))
                if self.arguments[0] == 'internet':
                    return tags.img(src="/RRD?source=%s&type=net&timeframe=-7d&width=200&height=50&nog=yes" % (server))

                if self.arguments[0] == 'mailrate':
                    return tags.img(src="/RRD?source=%s&type=exim&timeframe=-7d&width=200&height=50&nog=yes" % (server))

                    
            serversL = servers2.keys()
            serversL.sort()
            
            servers3 = []

            for i in serversL:
                servers3.append(servers2[i])
            
            return ctx.tag[
                tags.h3["Servers"],
                tags.br,
                tags.directive('form switchView'),
                self.dataTable(["Name","Status", "Last IP", "Load", ""], [
                    (
                        i[0] == "Online",
                        i[1], 
                        i[0], 
                        i[2], 
                        tags.div(_class="graphBlock")[getGraph(i[3], i[1])],
                        tags.a(href="/Servers/Manage/%s/" % i[3])["Manage"]
                    )
                    for i in servers3
                ], sortable=True),
            ]

        return self.enamel.storage.getServersInGroup(self.avatarId.gids).addCallback(renderServers)

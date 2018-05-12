from enamel import authentication, deployment, pages, servers, storage, deferreds, tags
from enamel import sql, url
import enamel

from twisted.internet import utils

from Pages import Users, Thebe

from lib import PageBase, iter, system

class Page(PageBase.Page):

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Dashboard"]]

    def __init__(self, *a, **kw):
        pages.Standard.__init__(self, *a, **kw)

    def document(self):
        baseDir = self.enamel.Settings.BaseDir
        theme = self.enamel.Settings.theme
        # Images, javascript and CSS locations
        # derived from base directory and theme 
        self.child_css = pages.static.File('%s/themes/%s/css/' % (baseDir, theme))
        self.child_js  = pages.static.File(baseDir + '/js/')
        self.child_images = pages.static.File('%s/themes/%s/images/' % (baseDir, theme))
        return pages.template('dashboard.xml', templateDir='%s/themes/%s/templates/' % (baseDir, theme))

    def render_sideMenu(self, ctx, data):
        return ctx.tag[""]

    def rollupBlock(self, title, content):
        return tags.div(_class="roundedBlock")[title,tags.div[content]]

    def render_contentTop(self, ctx, data):
        return ctx.tag[
            self.rollupBlock(tags.h1["Overview"],[
                tags.strong["Systems overview"],
                tags.br,
                #tags.xml('<object data="/Sexy" type="image/svg+xml" width="400" height="300"></object>')
                tags.xml('<img src="/Sexy"/>')
            ])
        ]

    def render_contentLeft(self, ctx, data):
        return ctx.tag[
            ""
            #tags.a(href="/__logout__/")["Click here to log out of Thebe"]
            #self.rollupBlock(tags.h1["Stats"],[
            #    tags.strong["All Internet Usage"], tags.br, 
            #    tags.img(src="/RRD?source=1&type=inetglobal&timeframe=-7d&width=300&height=150")
            #]),
        ]

    def render_user(self, ctx, data):
        def gotUser(row):
            return ctx.tag[
                tags.table(_class="stdTable")[
                    tags.tr[
                        tags.td(style="text-align:right;")[tags.strong["Name: "]], 
                        tags.td[row[3] or ""]
                    ],
                    tags.tr[
                        tags.td(style="text-align:right;")[tags.strong["Company: "]],
                        tags.td[row[5] or ""]
                    ],
                    tags.tr[
                        tags.td(style="text-align:right;")[tags.strong["Email: "]],
                        tags.td[row[4] or ""]
                    ],
                    tags.tr[
                        tags.td(style="text-align:right;")[tags.strong["Phone number: "]],
                        tags.td[row[10] or ""]
                    ],
                    tags.tr[
                        tags.td(style="text-align:right;")[tags.strong["Address: "]],
                        tags.td[row[6] or ""]
                    ],
                    tags.tr[
                        tags.td[""],
                        tags.td[row[7] or ""]
                    ],
                    tags.tr[
                        tags.td[""],
                        tags.td[row[8] or ""]
                    ],
                    tags.tr[
                        tags.td[""],
                        tags.td[row[9] or ""]
                    ]
                ],
            tags.a(href="/Account/")["Manage account"]
        ]
        return self.enamel.storage.getUser(self.avatarId.uid).addBoth(gotUser)

    def render_messageQueue(self, ctx, data):
        if not (1 in self.avatarId.gids):
            return ctx.tag[""]

        tcont = []
        
        for k,v in self.enamel.tcsMaster.messageQueue.items():  
            if v:
                tcont.append([tags.td[k], tags.td[repr(v)]])

        print tcont, "HERE!"
        
        return ctx.tag[
            tags.div(_class="tabBlock")[
                tags.div(_class="tabHeader")[
                    tags.div(_class="tabText")["Message Queue"]
                ], 
                tags.div(_class="tabContent")[
                    tags.table[
                        [tags.tr[i] for i in tcont]
                    ]
                ]
            ]
        ]

    def render_serverheadings(self, ctx, data):
        heads = [
            tags.td["Server Tag"],
            tags.td["License"],
            tags.td["Version"],
            tags.td["Status"]
        ]
        if 1 in self.avatarId.gids:
            heads.append(tags.td[""])

        return ctx.tag[heads]
            
    def render_servers(self, ctx, data):
        def renderOutage(servers):
            deadServers = []
            allServers = []
            idDict = {}
            faultyServers = []
            for i in servers:
                name = i[1]
                idDict[name] = i[0]
                allServers.append((name, i[3], i[5]))
                if name not in self.enamel.tcsMaster.connectedNodes:
                    if name not in self.enamel.tcsMaster.knownNodes:
                        deadServers.append(name)

            allServers.sort()

            table = []

            for svr in allServers:
                tr = [
                    tags.td[tags.a(href=url.root.child('Servers').child('Manage').child(idDict.get(svr[0])))[svr[0] or ""]],
                    tags.td[tags.pre[svr[1]]],
                    tags.td[svr[2] or "<1.7.0"],
                    tags.td[tags.span(style="color: %s" % (svr[0] in deadServers and "#f00" or "#0f0"))[svr[0] in deadServers and "Offline" or "Online"]]
                ]

                if 1 in self.avatarId.gids:
                    tr.append(tags.td[tags.a(href=url.root.child('Commands').child('Upgrade').child(idDict.get(svr[0])))["Update"]])
                
                table.append(tags.tr[tr])
 
            return ctx.tag[
                table
            ]

        return self.enamel.storage.getServersInGroup(self.avatarId.gids).addBoth(renderOutage)


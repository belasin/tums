from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings
from Core import PageHelpers
from Pages import Users

class Page(PageHelpers.DefaultPage):
    addSlash = True
    
    def childFactory(self, ctx, seg):
        if seg in self.childPages.keys():
            return self.childPages[seg].Page(self.avatarId)

    def render_content(self, ctx, seg):
        return ctx.tag[
            tags.div(id="rightBlock")[
                tags.invisible(render=tags.directive('shorerules'))
            ]
        ]

    def render_shorerules(self, ctx, data):
        def renderTable(result):
            resCopy = [i for i in result]
            return ctx.tag[
                    tags.h2["Shorewall Rules"],
                    tags.table(cellspacing=0)[
                        tags.thead[
                            tags.tr[tags.th["Priority"],tags.th["Action"], tags.th["Source"],
                                    tags.th["Destination"], tags.th["Protocol"], tags.th["Port"], tags.th["Comment"], tags.th[""]
                            ]
                        ],
                        tags.tbody[
                            [tags.tr[
                                tags.td[
                                    tags.a(href=url.root.child("swapShorerule").child(self.machineID).child(i[0]).child(resCopy[1+loc-len(resCopy)][0]))["Down"],"|",
                                    tags.a(href=url.root.child("swapShorerule").child(self.machineID).child(i[0]).child(resCopy[loc-1][0]))["Up"]
                                ],
                                tags.td[i[2]],
                                tags.td[i[3]],
                                tags.td[i[4]],
                                tags.td[i[5]],
                                tags.td[i[6]],
                                tags.td[i[10]],
                                tags.td[
                                    tags.a(href=url.root.child("deleteShorerule").child(self.machineID).child(i[0]))[tags.img(src="/images/delete.png")]
                                ]
                            ] for loc, i in enumerate(resCopy)]
                        ]
                    ],
                    tags.a(href=url.root.child("updateShorewall").child(self.machineID))["Send to client"]
                ]
        #return self.db.getShoreRule(self.machineID).addCallbacks(renderTable, printError)
        return ctx.tag["Pretend some shorewall rules go here"]

    def form_ruleOpenPort(self, data):
        form = formal.Form()

        form.addField('port',        formal.Integer(), label = "Port")
        form.addField('protocol',    formal.String(),  label = "Protocol")
        form.addField('description', formal.String(),  label = "Comment")

        form.addAction(self.submitOpenPort)
        return form

    def form_portTransparentProxy(self, data):
        form = formal.Form()
        form.addField('dest', formal.Integer(), label="Destination Port", description = ["This is the port traffic is destined for which will be redirected"])
        form.addField('dport', formal.Integer(), label="Proxy Port", description = ["This is the port to be redirected to"])
        form.addField('exclude', formal.String(), label="Exclude Destination(s)", description = ["Add destination host/network to exclude from this redirect. This should be any local address in the case of an http redirect"])
        form.addField('comment', formal.String(), label="Comment")

        form.addAction(self.submitTransProxy)
        return form

    def form_ruleDNAT(self, data):
        form = formal.Form()

        form.addField('dest', formal.String(), label = "Destination IP")
        form.addField('src', formal.String(), label = "Incomming IP")
        form.addField('sport', formal.Integer(), label = "Port")
        form.addField('proto', formal.String(), label = "Protocol")
        form.addField('comment', formal.String(), label = "Comment")

        form.addAction(self.submitRuleDNAT)
        return form

    def submitOpenPort(self, ctx, form, data):
        def returnToCtx(res):
            return url.root.child('viewHost').child(str(self.machineID))

        return self.db.addShoreRule(self.machineID, "ACCEPT", "net", "all",
            data['protocol'], data['port'], '', '', False, data['description']).addCallback(returnToCtx)

    def submitTransProxy(self, ctx, form, data):
        def returnToCtx(res):
            return url.root.child('viewHost').child(str(self.machineID))

        return self.db.addShoreRule(self.machineID, "REDIRECT", "loc", data['dport'],
            'tcp', data['dest'], '0', '!'+data['exclude'], False, data['comment']).addCallback(returnToCtx)

    def submitRuleDNAT(self, ctx, form, data):
        def returnToCtx(res):
            return url.root.child('viewHost').child(str(self.machineID))

        return self.db.addShoreRule(self.machineID, "DNAT", "net", "loc"+data['dest'],
            data['proto'], '-', data['sport'], data['src'], False, data['comment']).addCallback(returnToCtx)



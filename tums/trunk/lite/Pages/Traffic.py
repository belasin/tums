from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
import time, formal, LDAP, os
import Tree, Settings
from Core import PageHelpers, Shorewall, Utils, WebUtils
from Pages import Users, Tools


class Page(PageHelpers.DefaultPage):
    classes = Shorewall.TCClasses()
    rules = Shorewall.TCRules()

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Tools"]]

    def form_createClass(self, data):
        form = formal.Form()
        
        form.addField('interface', formal.String(required=True),
             formal.widgetFactory(formal.SelectChoice, options = [(i,i) for i in Utils.getInterfaces()]),
             label = "Interface", description = "The interface to which this class applies")

        form.addField('name', formal.String(required=True), label = "Name", description = "A name for this class")
             
        form.addField('baserate', formal.String(), label = "Base Rate", description = [
            "The basic rate for this class,",
            " preceded by the unit mbit or kbit (for example '768kbit')"
        ])
        
        form.addField('maxrate', formal.String(), label = "Maximum Rate", description = [
            "The maximum rate for this class,",
            " preceded by the unit mbit or kbit (for example '2mbit')"
        ])
            
        form.addField('prio', formal.Integer(), label = "Priority", description = "Priority of this traffic")

        form.addField('default', formal.Boolean(), label = "Default class", description = [
            "Tick if this is the default class to use for all traffic", 
            " Every interface must have a default class."
        ])
        
        form.addAction(self.submitTransProxy)

        return form

    def submitTransProxy(self, ctx, form, data):
        return url.root.child('Firewall')

    def restartShorewall(self):
        WebUtils.system('shorewall restart')

    def locateChild(self, ctx, segs):
        if segs[0]=="Delete":
            self.rules.deleteRule(segs[1], int(segs[2]))
            return url.root.child('Firewall'), ()
        if segs[0]=="Restart":
            self.restartShorewall()
            return url.root.child('Firewall'), ()
        return rend.Page.locateChild(self, ctx, segs)
        
    def getRules(self):
        return None

    def render_content(self, ctx, data):
        rules = self.rules.read()
        classes = self.classes.read()
        print rules
        return ctx.tag[
                Tools.Page.sideMenu(Tools.Page(None, self.db), ctx, data),
                tags.div(id="rightBlockIFrame")[
                    tags.h2[tags.img(src="/images/firewall.png"), " Bandwidth Management"],
                    [[
                        tags.fieldset[
                            tags.legend[r[6]],
                            tags.h3["Class Details"],
                            tags.table(cellspacing=0, _class='listing')[
                                tags.thead(background="/images/gradMB.png")[
                                    tags.tr[
                                        tags.th["Interface"], 
                                        tags.th["Base Rate"], 
                                        tags.th["Maximum Rate"], 
                                        tags.th["Priority"]
                                    ],
                                ],
                                tags.tbody[
                                    tags.tr[
                                        tags.td[r[0]], 
                                        tags.td[r[2]], 
                                        tags.td[r[3]], 
                                        tags.td[r[4]]
                                    ],
                                ]
                            ],
                            tags.h3["Rules"],
                            tags.table(cellspacing=0, _class='listing')[
                                tags.thead(background="/images/gradMB.png")[
                                    tags.tr[
                                        tags.th["Source IP"], 
                                        tags.th["Destination IP"], 
                                        tags.th["Protocol"], 
                                        tags.th["Source Port"],
                                        tags.th["Destination Port"]
                                    ],
                                ],
                                tags.tbody[
                                    [ tags.tr[
                                        tags.td[t[0] or "??"], 
                                        tags.td[t[1] or "??"], 
                                        tags.td[t[2] or "Any"], 
                                        tags.td[t[3] or "Any"],
                                        tags.td[t[4] or "Any"],
                                      ]
                                    for t in rules.get(r[1], [])]
                                ]
                            ]
                        ], tags.br]
                    for r in classes],
                ]
            ]

from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
import time
import Tree, Settings
from Core import PageHelpers
from Pages import Users, Reports

def error(_):
    print "Ooops" , _
    return [[None for i in xrange(30)]]

class Page(PageHelpers.DefaultPage):
    #docFactory  = loaders.xmlfile('framed.xml', templateDir=Settings.BaseDir+'/templates')
    def render_sideMenu(self, ctx, data):
        return ctx.tag[Reports.Page.sideMenu(Reports.Page(), self.avatarId)]

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Reports"]]

    def render_content(self, ctx, seg):
        def returnMailLog(mail):
            return ctx.tag[
                    tags.h3[tags.img(src="/images/maillog.png"), " Mail Queue"],
                    tags.br,
                    tags.table(cellspacing=0, _class='listing')[
                        tags.thead(background="/images/gradMB.png")[
                            tags.tr[
                                tags.th["Date"],
                                tags.th["From"],
                                tags.th["To"],
                                tags.th["Subject"],
                                tags.th["Message ID"]
                            ]
                        ],
                        tags.tbody[
                            [tags.tr[
                                    tags.td[time.ctime(m[3])],
                                    tags.td[m[2] or ""],
                                    tags.td[m[5] or ""],
                                    tags.td[m[9] or ""],
                                    tags.td[m[1] or ""]
                                ]
                            for m in mail]
                        ]
                    ],
            ]
        return self.db[0].getMailQueue().addCallbacks(returnMailLog, error)
    

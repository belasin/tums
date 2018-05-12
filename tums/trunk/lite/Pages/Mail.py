from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
import time, datetime, formal
import Tree, Settings
from Core import PageHelpers
from Pages import Users, Reports

def error(_):
    print "Ooops" , _
    return [[None for i in xrange(30)]]

class ShowSearch(PageHelpers.DefaultPage):
    #docFactory  = loaders.xmlfile('framed.xml', templateDir=Settings.BaseDir+'/templates')
    def __init__(self, avatarId = None, db = (None), search = [], *a, **kw):
        self.search = search
        PageHelpers.DefaultPage.__init__(self,avatarId, db, *a, **kw)

    def locateChild(self, ctx, segment):
        if segment[0]:
            return ShowSearch(self.avatarId, self.db, list(segment)), ()

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Reports"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Reports.Page.sideMenu(Reports.Page(), self.avatarId)]

    def render_content(self, ctx, seg):
        def returnMailLog(mail):
            return ctx.tag[
                    tags.h3[tags.img(src="/images/maillog.png"), " Mail Logs"],
                    tags.br,
                    tags.table(cellspacing=0, _class='listing')[
                        tags.thead(background="/images/gradMB.png")[
                            tags.tr[
                                tags.th["Date"],
                                tags.th["From"],
                                tags.th["To"],
                                tags.th["Size"],
                                tags.th["Message ID"]
                            ]
                        ],
                        tags.tbody[
                            [tags.tr[
                                    tags.td[time.ctime(m[2])],
                                    tags.td[m[5]],
                                    tags.td[m[18]],
                                    tags.td[ "%0.3f KB" % (float(m[11])/1024.0)],
                                    tags.td[m[1]]
                                ]
                            for m in mail]
                        ]
                    ],
                    tags.br,
            ]
        #return ctx.tag["search stuff go here ", repr(self.search)]
        return self.db.searchMessages(*self.search[:4]).addCallbacks(returnMailLog, error)

class Page(PageHelpers.DefaultPage):
    #docFactory  = loaders.xmlfile('framed.xml', templateDir=Settings.BaseDir+'/templates')
    def __init__(self, avatarId = None, db = (None), offset = 0, *a, **kw):
        self.offset = offset
        PageHelpers.DefaultPage.__init__(self,avatarId, db[0], *a, **kw)

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Reports"]]

    def submitForm(self, ctx, f, d):
        #print d
        #return Page(self.avatarId, self.db, self.offset, self.search)
        #print ctx

        #fromdate
        if d['fromdate']:
            fromdate = str(int(time.mktime(d['fromdate'].timetuple()))) 
        else:
            fromdate = "0"
        
        if d['todate']: 
            todate = str(int(time.mktime(d['todate'].timetuple())))
        else:
            todate = "0"
        
        searchEncode = '/'.join([d['to'] or "None", d['from'] or "None", 
                fromdate,
                todate])
        return url.root.child('Mail').child('Search').child(searchEncode)

    def form_searchForm(self, d):
        form = formal.Form()

        form.addField('to', formal.String(), label="To Address Contains")
        form.addField('from', formal.String(), label="From Address Contains", description=["Between Dates"])
        form.addField('fromdate', formal.Date(), label="")
        form.addField('todate', formal.Date(), label="")

        form.addAction(self.submitForm)
        return form
    def render_sideMenu(self, ctx, data):
        return ctx.tag[Reports.Page.sideMenu(Reports.Page(), self.avatarId)]
  
    def render_content(self, ctx, seg):
        def returnMailLog(mail):
            if self.offset >0:
                previousTag = tags.a(href=url.root.child("Mail").child(self.offset - 20))["Previous 20"]
            else:
                previousTag = "Previous 20"
            return ctx.tag[
                #tags.div(id="rightBlockIFrame")[
                    tags.h3[tags.img(src="/images/maillog.png"), " Mail Logs"],
                    previousTag,
                    tags.a(href=url.root.child("Mail").child(self.offset + 20))["Next 20"],tags.br,
                    tags.table(cellspacing=0, _class='listing')[
                        tags.thead(background="/images/gradMB.png")[
                            tags.tr[
                                tags.th["Date"],
                                tags.th["From"],
                                tags.th["To"],
                                tags.th["Size"],
                                tags.th["Message ID"]
                            ]
                        ],
                        tags.tbody[
                            [tags.tr[
                                    tags.td[time.ctime(m[2])],
                                    tags.td[m[5]],
                                    tags.td[m[18]],
                                    tags.td[ "%0.3f KB" % (float(m[11])/1024.0)],
                                    tags.td[m[1]]
                                ]
                            for m in mail]
                        ]
                    ],
                    tags.br,
                    previousTag,
                    tags.a(href=url.root.child("Mail").child(self.offset + 20))["Next 20"],
                    tags.br, 
                    tags.h3["Search Logs"],
                    tags.invisible(render=tags.directive('form searchForm'))
            ]
        return self.db.getLastMessages(offset = self.offset).addCallbacks(returnMailLog, error)
    
    def childFactory(self, ctx, segment):
        if segment == "Search":
            return ShowSearch(self.avatarId, self.db)
        return Page(self.avatarId, self.db, int(segment))

from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
import time, datetime, formal, os
import Tree, Settings
from Core import PageHelpers
from Pages import Users, Reports

class Page(PageHelpers.DefaultPage):
    docFactory  = loaders.xmlfile('overview.xml', templateDir=Settings.BaseDir+'/templates')
    def __init__(self, avatarId = None, db = None, year = 0, month = 0, *a, **kw):
        today = datetime.datetime.now()
        if not year:
            self.year = today.year
        else:
            self.year = year
        if not month:
            self.month = today.month
        else:
            self.month = month
        PageHelpers.DefaultPage.__init__(self,avatarId, db, *a, **kw)

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Reports"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Reports.Page.sideMenu(Reports.Page(), self.avatarId)]
  
    def form_selectDate(self, ctx):
        form = formal.Form()
        statdir = os.listdir('/var/www/localhost/htdocs/eximstat/')
        dates = []
        for d in statdir:
            if ".html" in d  and "index" not in d: # Not index but is html
                dD = "%s %s" % (d[4:].strip('.html'), d[:4])
                dates.append((d.strip('.html'), dD))
        
        print dates
        dates.sort()
        form.addField('stats', formal.String(required=True),
            formal.widgetFactory(formal.SelectChoice, options = dates),
            label = "Date "
        )
        if self.month < 10:
            month = "0" + str(self.month)
        else:
            month = str(self.month)
        
        form.addAction(self.selectDate)
        form.data = {'stats': "%s%s" % (self.year,month)}
        return form

    def selectDate(self, ctx, form, data):
        return url.root.child('Existat').child(data['stats'])

    def render_content(self, ctx, data):
        try:
            # Pad the month..
            if self.month < 10:
                month = "0" + str(self.month)
            else:
                month = str(self.month)
            latestEximstat = open('/var/www/localhost/htdocs/eximstat/%s%s.html'%(self.year, month))
            doc = ""
            cnt = 0
            for ln in latestEximstat:
                cnt += 1
                thisln = ln.replace('src="./', url.root.child('local').child('eximstat')).replace('src="images', 'src="/images')
                if not "html" in thisln and not "body" in thisln and cnt > 27:
                    doc+=thisln
        except Exception, e:
            print e
            doc = "No statistics for the last month" 
        return ctx.tag[
            tags.h3[tags.img(src="/images/maillog.png"), " Mail Statistics"],
            tags.directive('form selectDate'),
            tags.xml(doc)
        ]

    def childFactory(self, ctx, segment):
        year  = int(segment[:4])
        month = int(segment[4:])
        return Page(self.avatarId, self.db, year, month)

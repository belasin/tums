from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP, Database
from Core import PageHelpers, AuthApacheProxy, confparse, Utils, NetUtils, WebUtils
from Pages import Tools, Reports
import formal, datetime

class Page(Reports.Page):
    addSlash = True
    portCache = {}

    #docFactory  = loaders.xmlfile('netflow.xml', templateDir=Settings.BaseDir+'/templates')

    def __init__(self, avatarId, db, day=None, month=None, year=None, entry=None, view=None, index=0, *a, **kw):
        self.DB = db[5]['telDB']
        if not month:
            today = datetime.datetime.now()
            self.month = today.month
            self.year = today.year
            self.day = 0
        else:
            self.month = month
            self.year = year
        if day:
            if day > 0:
                self.day = day
        else:
            self.day = 0 

        self.view = view
        self.entry = entry

        try:
            self.index = int(index)
        except:
            self.index = 0

        Reports.Page.__init__(self, avatarId, db, *a, **kw)

    def form_dateRange(self, ctx):
        form = formal.Form()
        
        months = [(m+1, Utils.months[m+1]) for m in range(12)]
        days = [(0, 'Whole Month')] + [(m+1, m+1) for m in range(31)]
        yearLim = datetime.datetime.now().year
        years = [(y,y) for y in reversed(range(yearLim-3, yearLim+1))]

        form.addField('day', formal.Integer(),
            formal.widgetFactory(formal.SelectChoice, options = days),
            label = "Day")
        
        form.addField('month', formal.Integer(required=True),
            formal.widgetFactory(formal.SelectChoice, options = months),
            label = "Month")

        form.addField('year', formal.Integer(required=True),
            formal.widgetFactory(formal.SelectChoice, options = years),
            label = "Year")

        form.data['month'] = self.month
        form.data['day'] = self.day 
        form.data['year'] = self.year

        form.addAction(self.selectDate)
        return form

    def selectDate(self, ctx, form, data):
        if data['month']:
            self.month = data['month']
        if data['year']:
            self.year = data['year']

        self.day = data['day']

        if self.entry: #Assume View
            return url.root.child('TelReport').child(self.entry).child(self.view).child(self.day).child(self.month).child(self.year)
        if self.view:
            return url.root.child('TelReport').child(self.view).child(self.day).child(self.month).child(self.year)
        else:
            return url.root.child('TelReport').child(self.day).child(self.month).child(self.year)
    
    def locateChild(self, ctx, seg):
        """Returns page instances depending on the URL"""
        try: 
            day = int(seg[1])
            month = int(seg[2])
            year = int(seg[3])
        except:
            day = 0 
            month = None
            year = None



        return Page(self.avatarId, self.db, day, month, year, None, "Overview"), ()

    def gen_overview(self):
        def processResult(res):
            headerDialed = ["Call Date", "Duration", "User", "Dialed Number"]
            headerRec =    ["Call Date", "Duration", "User", "Source Number"]
            dataDialed = []
            dataRec = []
            for entry in res:
                if entry['dcontext'][0:8] == 'userProv':
                    dataDialed.append([
                        str(entry['calldate']),
                        entry['duration'],
                        entry['src'],
                        entry['dst']
                    ])
                else:
                    #XXX Add recieved log
                    pass
                
                
            return [
                tags.h3["Dialed Calls"], 
                PageHelpers.dataTable(headerDialed, dataDialed),tags.br,
                tags.h3["Received Calls"], 
                PageHelpers.dataTable(headerRec, dataRec),
            ]
        return self.DB.getReportData(self.year, self.month, self.day).addBoth(processResult)

    def render_report(self, ctx, data):
        rep = ""
        if self.view == 'Overview':
            rep = self.gen_overview()
        return rep 

    def render_content(self, ctx, data):
        title = "Telephone Usage Reports"

        return ctx.tag[
            tags.h2[tags.img(src="/images/mailsrv.png")," Telephone Utilisation"],
            tags.directive('form dateRange'),
            #other,
            #extraStats,
            tags.directive('report'),
            #PageHelpers.dataTable(header, reversed(table)),tags.br,
            tags.a(name="us")['']
        ]

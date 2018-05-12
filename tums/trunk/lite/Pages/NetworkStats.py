from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP, Database
from Core import PageHelpers, AuthApacheProxy, confparse, Utils
from Pages import Tools, Reports
import formal, datetime

class Page(PageHelpers.DefaultPage):
    addSlash = True
    portCache = {}
    flowDb = Database.AggregatorDatabase()

    #docFactory  = loaders.xmlfile('netflow.xml', templateDir=Settings.BaseDir+'/templates')

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Reports"]]

    def __init__(self, avatarId, db,day=None, month=None, year=None, ip=None, view=None, *a, **kw):
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
    
        self.ip = ip
        self.view = view

        PageHelpers.DefaultPage.__init__(self, avatarId, db, *a, **kw)

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

        if self.view and "Host" in self.view:
            return url.root.child('NetworkStats').child(self.view).child(self.ip).child(self.day).child(self.month).child(self.year)
        else:
            if self.view:
                return url.root.child('NetworkStats').child(self.view).child(self.day).child(self.month).child(self.year)
            else:
                return url.root.child('NetworkStats').child(self.day).child(self.month).child(self.year)

    def locateChild(self, ctx, seg):
        try: 
            day = int(seg[1])
            month = int(seg[2])
            year = int(seg[3]) 
        except:
            day = 0 
            month = None
            year = None

        if "Host" in seg[0]:
            try:
                day = int(seg[2])
                month=int(seg[3])
                year=int(seg[4])
            except:
                day = 0 
                month = None
                year = None
            ip = seg[1]
            return Page(self.avatarId, self.db, day, month, year, ip, "Host"), ()

        elif "Ports" in seg[0]:
            return Page(self.avatarId, self.db, day, month, year, None, "Ports"), ()

        return Page(self.avatarId, self.db, day, month, year, None, "Overview"), ()

    def resolvePort(self, port):
        """Get the canonical ARIN name for a port"""
        if not self.portCache:
            ports = open('/etc/services', 'r')
            for ln in ports:
                l = ln.strip()
                if l and l[0] != "#":
                    defn = l.split()
                    self.portCache[int(defn[1].split('/')[0])] = defn[0]
            self.portCache[9680] = 'Thusa Thebe'
            self.portCache[9682] = 'Thusa TUMS'
            self.portCache[9682] = 'Thusa NetFlow Concentrator'
            self.portCache[65535] = tags.a(href="#us")['Unknown Services*']

        return self.portCache.get(port, str(port))

    def dateLink(self):
        return '/'.join([str(self.day), str(self.month), str(self.year)])

    def dateStamp(self):
        if self.day>0:
            return "%s %s %s" % (self.day, Utils.months[self.month], self.year)
        else:
            return "%s %s" % (Utils.months[self.month], self.year)

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Reports.Page.sideMenu(Reports.Page(), self.avatarId)]

    def render_content(self, ctx, data):
        table = []
        header = []
        title = "?"
        total = 0
        tin = 0 
        tout = 0
        other = []
        if self.ip:
            # Render a hosts overview, utilisation by port
            title = "Internet Usage by port for %s during %s" % (self.ip, self.dateStamp())
            portStats = self.flowDb.getPortBreakdownForIp(self.month, self.year, self.ip, self.day)
            header = ["Port", "Traffic In", "Traffic Out", "Percentage of Total"]
            for port, inout in portStats.items():
                if (inout[0] + inout[1]) > 1024:
                    table.append([inout[0]+inout[1],self.resolvePort(port), Utils.intToH(inout[0]), Utils.intToH(inout[1])])
                total += inout[0] + inout[1]
                tin += inout[0]
                tout += inout[1]

        elif self.view == "Ports":
            title = "Internet Usage by port for all users during %s" % (self.dateStamp())
            header = ["Port", "Traffic In", "Traffic Out", "Percentage of Total"]
            portStats = self.flowDb.getPortTotals(self.month, self.year, self.day)
            portList = []
            for port, inout in portStats.items():
                total += inout[0] + inout[1]
                tin += inout[0]
                tout += inout[1]
                if (inout[0] + inout[1]) > 1024:
                    # discard the data if it's not of valuable size
                    table.append([inout[0]+inout[1], self.resolvePort(port), Utils.intToH(inout[0]), Utils.intToH(inout[1])])
                portList.append(port)

            # sort this data before we create the port distribution
            portList.sort()
            
        else:
            title = "Internet Usage by IP during %s" % (self.dateStamp())
            header = ["IP Address", "Traffic In", "Traffic Out", "Percentage of Total"]
            ipStats = self.flowDb.getVolumeTotalByIp(self.month, self.year, self.day)
            for ip, inout in ipStats.items():
                table.append([
                    inout[0]+inout[1],
                    tags.a(href=url.root.child("NetworkStats").child("Host").child(ip).child(self.dateLink()), title="View detail")[ip], 
                    Utils.intToH(inout[0]), 
                    Utils.intToH(inout[1])
                ])
                total += inout[0] + inout[1]
                tin += inout[0]
                tout += inout[1]

        table.sort()
        table = [i[1:]+[PageHelpers.progressBar(float(i[0])/float(total))] for i in table]
        table.append([tags.a(href=url.root.child("NetworkStats").child("Ports").child(self.dateLink()), title="View port usage for this time")['All'], 
            Utils.intToH(tin), Utils.intToH(tout), PageHelpers.progressBar(1)])

        return ctx.tag[
            tags.h2[tags.img(src="/images/netflow.png")," Network utilisation"],
            tags.img(src="/images/cisco.png", style="position:absolute; margin-left:25em;"),
            tags.directive('form dateRange'),
            tags.h3[title],
            #other,
            PageHelpers.dataTable(header, reversed(table)),tags.br,
            tags.a(name="us")[''],
            tags.p[tags.strong["* Unknown Services:"],""" Because large volumes of traffic are undefinable (MSN, Bittorrent, etc),
            during the aggregation process we must lump "high ports" (ports >1024) which can not be defined into a bigger subset called "Unknown Services".
            The reason for this is that this data is often a small amount of noise but accounts for many individual packets, 
            accounting the value of each of these ports will not provide any useful data to the person viewing it as the application 
            responsible for it is undefined. Processing the data without this aggregation also increases the volume of data considerably, 
            and the resources required to view it. If the value is extremely high, the most likely reasons are a virus infection or Bittorent activity.
            """]
        ]

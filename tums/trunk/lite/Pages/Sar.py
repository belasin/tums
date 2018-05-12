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

class ShowHost(PageHelpers.DefaultPage):
    def __init__(self, avatarId = None, db = None, ip="", year=0, month=0, day=0, *a, **kw):
        self.year = int(year)
        self.month = int(month)
        self.day = int(day)
        self.ip = ip
        PageHelpers.DefaultPage.__init__(self,avatarId, db, *a, **kw)

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Reports"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Reports.Page.sideMenu(Reports.Page(), self.avatarId)]
  
    def render_content(self, ctx, seg):
        def error(_):
            print _
            return ctx.tag["Database access error."]

        def returnDayView(dayData):
            """ Returns the details for a particular day"""
            flatBlocks  = []
            date = datetime.date(self.year, self.month, self.day).strftime("%d %h %Y")
            host = ""
            for rows in dayData:
                flatBlocks.append((
                    "%0.2fMB" % (rows[0]/(1024*1024)),
                    rows[1]
                ))
                host = rows[3]
            return ctx.tag[
                tags.h3[
                    tags.img(src="/images/stock-download.png"),
                    "Web Usage - Sites visited by %s on %s" % (host, date)
                ],
                tags.a(href=url.root.child("ProxyUse"))["Back to overview"], "  ",
                tags.a(href=url.root.child("ProxyUse").child("ShowDays").child(self.year).child(self.month))["Back to month overview"], "  ",
                tags.a(href=url.root.child("ProxyUse").child("ShowDays").child(self.year).child(self.month).child(self.day))["Back to day overview"],
                tags.br, tags.br,
                PageHelpers.dataTable(['Total Traffic', 'Site'], flatBlocks)
            ]

        return self.db.getSiteSummary(self.ip, self.year, self.month, self.day).addCallbacks(returnDayView, error)

    def locateChild(self, ctx, seg):
        arguments = [self.ip, self.year, self.month, self.day]
        
        for i, val in enumerate(seg):
            if i < 4:
                arguments[i] = val or 0

        return ShowHost(self.avatarId, self.db, *arguments), () # Return myself

class ShowDays(PageHelpers.DefaultPage):
    def __init__(self, avatarId = None, db = None, year=0, month=0, day=0, *a, **kw):
        self.year = int(year)
        self.month = int(month)
        self.day = int(day)
        PageHelpers.DefaultPage.__init__(self,avatarId, db, *a, **kw)

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Reports"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Reports.Page.sideMenu(Reports.Page(), self.avatarId)]
  
    def render_content(self, ctx, seg):
        def error(_):
            print _
            return ctx.tag["Database access error."]

        def returnMonthView(monthData):
            """ Returns days in this month for which we have data"""
            flatBlocks = []
            for rows in monthData:
                date = '/'.join([str(i) for i in (rows[0].year, rows[0].month, rows[0].day)])
                flatBlocks.append((
                    tags.a(href=url.root.child("ProxyUse").child("ShowDays").child(date))[
                        rows[0].strftime("%d %h %Y")
                    ], 
                    "%0.2fMB" % (rows[1]/(1024*1024)), 
                    rows[2]
                ))

            return ctx.tag[
                tags.h3[
                    tags.img(src="/images/stock-download.png"),
                    "Web Usage - Month overview for %s" % datetime.date(self.year, self.month, 1).strftime("%h %Y")
                ],
                tags.a(href=url.root.child("ProxyUse"))["Back to overview"], "  ",
                tags.br, tags.br,
                PageHelpers.dataTable(['Date', 'Total Traffic', 'Sites Visited'], flatBlocks)
            ]

        def returnDayView(dayData):
            """ Returns the details for a particular day"""
            flatBlocks  = []
            date = "%s/%s/%s" % (self.year, self.month, self.day)
            for rows in dayData:
                flatBlocks.append((
                    tags.a(href=url.root.child("ProxyUse").child("ShowHost").child(rows[3]).child(self.year).child(self.month).child(self.day))[rows[2]], 
                    rows[5], 
                    "%0.2fMB" % (rows[0]/(1024*1024)),
                    int(rows[1])
                ))
            
            return ctx.tag[
                tags.h3[
                    tags.img(src="/images/stock-download.png"),
                    "Web Usage - Per user statistics for %s" % datetime.date(self.year, self.month, self.day).strftime("%d %h %Y")
                ],
                tags.a(href=url.root.child("ProxyUse"))["Back to overview"], "  ",
                tags.a(href=url.root.child("ProxyUse").child("ShowDays").child(self.year).child(self.month))["Back to month overview"],
                tags.br, tags.br,
                PageHelpers.dataTable(['Host', 'Username', 'Total Traffic', 'Sites Visited'], flatBlocks)
            ]

        if not self.day:
            return self.db.getDaySummary(self.year, self.month).addCallbacks(returnMonthView, error)
        else:
            return self.db.getSummary(self.year, self.month, self.day).addCallbacks(returnDayView, error)

    def locateChild(self, ctx, seg):
        if len(seg) == 3:
            return ShowDays(self.avatarId, self.db, seg[0], seg[1]), ()

        if len(seg) == 4 and seg[2]: # Make sure the seg is valid
            return ShowDays(self.avatarId, self.db, seg[0], seg[1], seg[2]), ()

        return ShowDays(self.avatarId, self.db, self.year, self.month, self.day), () # Return myself


class Page(PageHelpers.DefaultPage):
    def __init__(self, avatarId = None, db = (None), *a, **kw):
        PageHelpers.DefaultPage.__init__(self,avatarId, db[1], *a, **kw)

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Reports"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Reports.Page.sideMenu(Reports.Page(), self.avatarId)]
  
    def render_content(self, ctx, seg):
        def error(_):
            print _
            return ctx.tag["Database access error."]

        def returnMonthView(monthData):
            # Construct some sensible data.
            dateBlocks = {}
            order = []
            for rows in monthData:
                yearMonth = "%s - %s" % (rows[0].year, rows[0].month)
                if yearMonth in dateBlocks:
                    dateBlocks[yearMonth][0] += rows[1]
                    dateBlocks[yearMonth][1] += rows[2]
                else:
                    order.append(yearMonth)
                    dateBlocks[yearMonth] = [rows[1], rows[2]]
            # flatten the dictionary
            flatBlocks = []
            for date in order:
                values = dateBlocks[date]
                year = int(date.split()[0])
                day = int(date.split()[1])
                month = int(date.split()[2])
                flatBlocks.append((
                    tags.a(href=url.root.child("ProxyUse").child("ShowDays").child(year).child(day).child(month))[
                        datetime.date(year, month, 1).strftime("%h %Y")
                    ], 
                    "%0.2fMB" % (values[0]/(1024*1024)), 
                    values[1]
                ))

            return ctx.tag[
                tags.h3[
                    tags.img(src="/images/stock-download.png"),
                    "Proxy Usage - Month Overview"
                ],
                PageHelpers.dataTable(['Date', 'Total Traffic', 'Sites Visited'], flatBlocks)
            ]
        return self.db.getMonths().addCallbacks(returnMonthView, error)
    
    def childFactory(self, ctx, segment):
        if segment == "ShowDays":
            return ShowDays(self.avatarId, self.db)
        if segment == "ShowHost":
            return ShowHost(self.avatarId, self.db)
        return Page(self.avatarId, self.db)

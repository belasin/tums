from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
import time, datetime, formal
import Tree, Settings
from Core import PageHelpers
from Pages import Reports

class ShowSites(Reports.Page):
    def __init__(self, avatarId = None, db = None, year=0, month=0, day=0, *a, **kw):
        self.year = int(year)
        self.month = int(month)
        self.day = int(day)
        Reports.Page.__init__(self,avatarId, db, *a, **kw)

    def locateChild(self, ctx, seg):
        arguments = [self.year, self.month, self.day]
        
        for i, val in enumerate(seg):
            if i < 3:
                arguments[i] = val or 0

        return ShowSites(self.avatarId, self.db, *arguments), () # Return myself

    def render_content(self, ctx, seg):
        def error(_):
            print _
            return ctx.tag["Database access error."]

        def returnMonthView(dayData):
            """ Returns the details for a particular month"""
            flatBlocks  = []
            date = datetime.date(self.year, self.month, 1).strftime("%h %Y")
            for rows in dayData:
                flatBlocks.append((
                    "%0.2fMB" % (rows[0]/(1024*1024)),
                    tags.a(href=url.root.child("ProxyUse").child("ShowSiteHost").child(rows[2]).child(self.year).child(self.month).child('0'))[rows[1]]
                ))
            return ctx.tag[
                tags.h3[
                    tags.img(src="/images/stock-download.png"),
                    "Web Usage - Sites visited during %s" % (date)
                ],
                tags.a(href=url.root.child("ProxyUse"))["Back to overview"], "  ",
                tags.a(href=url.root.child("ProxyUse").child("ShowDays").child(self.year).child(self.month))["Back to month overview"], "  ",
                tags.a(href=url.root.child("ProxyUse").child("ShowDays").child(self.year).child(self.month).child(self.day))["Back to day overview"],
                tags.br, tags.br,
                PageHelpers.dataTable([('int', 'Total Traffic'), ('istr', 'Site')], flatBlocks, sortable=True)
            ]

        def returnDayView(dayData):
            """ Returns the details for a particular day"""
            flatBlocks  = []
            date = datetime.date(self.year, self.month, self.day).strftime("%d %h %Y")
            for rows in dayData:
                flatBlocks.append((
                    "%0.2fMB" % (rows[0]/(1024*1024)),
                    tags.a(href=url.root.child("ProxyUse").child("ShowSiteHost").child(rows[2]).child(self.year).child(self.month).child(self.day))[rows[1]]
                ))
            return ctx.tag[
                tags.h3[
                    tags.img(src="/images/stock-download.png"),
                    "Web Usage - Sites visited on %s" % (date)
                ],
                tags.a(href=url.root.child("ProxyUse"))["Back to overview"], "  ",
                tags.a(href=url.root.child("ProxyUse").child("ShowDays").child(self.year).child(self.month))["Back to month overview"], "  ",
                tags.a(href=url.root.child("ProxyUse").child("ShowDays").child(self.year).child(self.month).child(self.day))["Back to day overview"],
                tags.br, tags.br,
                PageHelpers.dataTable([('int', 'Total Traffic'), ('istr', 'Site')], flatBlocks, sortable=True)
            ]

        print self.day
        if not self.day:
            return self.db.getSiteSummary(None, self.year, self.month).addCallbacks(returnMonthView, error)
        return self.db.getSiteSummary(None, self.year, self.month, self.day).addCallbacks(returnDayView, error)


class ShowSiteHost(Reports.Page):
    def __init__(self, avatarId = None, db = None, site="", year=0, month=0, day=0, *a, **kw):
        self.year = int(year)
        self.month = int(month)
        self.day = int(day)
        self.site = site
        Reports.Page.__init__(self,avatarId, db, *a, **kw)

    def locateChild(self, ctx, seg):
        arguments = [self.site, self.year, self.month, self.day]
        
        for i, val in enumerate(seg):
            if i < 4:
                arguments[i] = val or 0

        return ShowSiteHost(self.avatarId, self.db, *arguments), () # Return myself

    def render_content(self, ctx, seg):
        def error(_):
            print _
            return ctx.tag["Database access error."]

        def returnMonthView(dayData):
            """ Returns the details for a particular month"""
            flatBlocks  = []
            date = datetime.date(self.year, self.month, 1).strftime("%h %Y")

            tsite = ""
            for rows in dayData:
                tsite = rows[6]
                flatBlocks.append((
                    tags.a(href=url.root.child("ProxyUse").child("ShowHost").child(rows[2]).child(self.year).child(self.month).child('0'))[rows[1]], 
                    rows[4], 
                    "%0.2fMB" % (rows[0]/(1024*1024)),
                ))
            return ctx.tag[
                tags.h3[
                    tags.img(src="/images/stock-download.png"),
                    "Web Usage - Hosts who visited %s during %s" % (tsite, date)
                ],
                tags.a(href=url.root.child("ProxyUse"))["Back to overview"], "  ",
                tags.a(href=url.root.child("ProxyUse").child("ShowDays").child(self.year).child(self.month))["Back to month overview"], "  ",
                tags.a(href=url.root.child("ProxyUse").child("ShowDays").child(self.year).child(self.month).child(self.day))["Back to day overview"], "  ",
                tags.a(href=url.root.child("ProxyUse").child("ShowSites").child(self.year).child(self.month).child('0'))["Back to sites overview"],
                tags.br, tags.br,
                PageHelpers.dataTable([('str', 'Host'), ('str', 'Username'), ('int', 'Total Traffic')], flatBlocks, sortable=True)
            ]

        def returnDayView(dayData):
            """ Returns the details for a particular day"""
            flatBlocks  = []
            date = datetime.date(self.year, self.month, self.day).strftime("%d %h %Y")
            tsite = ""
            for rows in dayData:
                tsite = rows[6]
                flatBlocks.append((
                    tags.a(href=url.root.child("ProxyUse").child("ShowHost").child(rows[2]).child(self.year).child(self.month).child('0'))[rows[1]], 
                    rows[4], 
                    "%0.2fMB" % (rows[0]/(1024*1024)),
                ))
            return ctx.tag[
                tags.h3[
                    tags.img(src="/images/stock-download.png"),
                    "Web Usage - Hosts who visited %s during %s" % (tsite, date)
                ],
                tags.a(href=url.root.child("ProxyUse"))["Back to overview"], "  ",
                tags.a(href=url.root.child("ProxyUse").child("ShowDays").child(self.year).child(self.month))["Back to month overview"], "  ",
                tags.a(href=url.root.child("ProxyUse").child("ShowDays").child(self.year).child(self.month).child(self.day))["Back to day overview"], "  ",
                tags.a(href=url.root.child("ProxyUse").child("ShowSites").child(self.year).child(self.month).child(self.day))["Back to sites overview"],
                tags.br, tags.br,
                PageHelpers.dataTable([('str', 'Host'), ('str', 'Username'), ('int', 'Total Traffic')], flatBlocks, sortable=True)
            ]

        print self.day
        if not self.day:
            return self.db.getSiteHosts(self.site, self.year, self.month).addCallbacks(returnMonthView, error)
        return self.db.getSiteHosts(self.site, self.year, self.month, self.day).addCallbacks(returnDayView, error)



class ShowHost(Reports.Page):
    def __init__(self, avatarId = None, db = None, ip="", year=0, month=0, day=0, *a, **kw):
        self.year = int(year)
        self.month = int(month)
        self.day = int(day)
        self.ip = ip
        Reports.Page.__init__(self,avatarId, db, *a, **kw)

    def render_content(self, ctx, seg):
        def error(_):
            print _
            return ctx.tag["Database access error."]

        def returnMonthView(dayData):
            """ Returns the details for a particular month"""
            flatBlocks  = []
            date = datetime.date(self.year, self.month, 1).strftime("%h %Y")
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
                    "Web Usage - Sites visited by %s during %s" % (host, date)
                ],
                tags.a(href=url.root.child("ProxyUse"))["Back to overview"], "  ",
                tags.a(href=url.root.child("ProxyUse").child("ShowDays").child(self.year).child(self.month))["Back to month overview"], "  ",
                tags.a(href=url.root.child("ProxyUse").child("ShowDays").child(self.year).child(self.month).child(self.day))["Back to day overview"],
                tags.br, tags.br,
                PageHelpers.dataTable([('int', 'Total Traffic'), ('istr', 'Site')], flatBlocks, sortable=True)
            ]

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
                PageHelpers.dataTable([('int', 'Total Traffic'), ('istr', 'Site')], flatBlocks, sortable=True)
            ]

        print self.day
        if not self.day:
            return self.db.getSiteSummary(self.ip, self.year, self.month).addCallbacks(returnMonthView, error)
        return self.db.getSiteSummary(self.ip, self.year, self.month, self.day).addCallbacks(returnDayView, error)

    def locateChild(self, ctx, seg):
        arguments = [self.ip, self.year, self.month, self.day]
        
        for i, val in enumerate(seg):
            if i < 4:
                arguments[i] = val or 0

        return ShowHost(self.avatarId, self.db, *arguments), () # Return myself

class ShowDays(Reports.Page):
    def __init__(self, avatarId = None, db = None, year=0, month=0, day=0, *a, **kw):
        self.year = int(year)
        self.month = int(month)
        self.day = int(day)
        Reports.Page.__init__(self,avatarId, db, *a, **kw)

    def render_content(self, ctx, seg):
        def error(_):
            print _
            return ctx.tag["Database access error."]

        def returnMonthView(monthData):
            """ Returns days in this month for which we have data"""
            flatBlocks = []
            for rows in monthData:
                flatBlocks.append((
                    tags.a(href=url.root.child("ProxyUse").child("ShowDays").child(rows[0].year).child(rows[0].month).child(rows[0].day))[
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
                tags.a(href=url.root.child("ProxyUse").child("ShowDays").child(self.year).child(self.month).child("0"))["Month host overview"], "  ",
                tags.a(href=url.root.child("ProxyUse").child("ShowSites").child(self.year).child(self.month).child("0"))["Month sites overview"], "  ",
                tags.br, tags.br,
                PageHelpers.dataTable([('cdate', 'Date'), ('int', 'Total Traffic'), ('int', 'Sites Visited')], flatBlocks, sortable=True)
            ]

        def returnMonthIPView(dayData):
            """ Returns the details for a particular day"""
            flatBlocks  = []
            for rows in dayData:
                flatBlocks.append((
                    tags.a(href=url.root.child("ProxyUse").child("ShowHost").child(rows[3]).child(self.year).child(self.month))[rows[2]], 
                    rows[5], 
                    "%0.2fMB" % (rows[0]/(1024*1024)),
                    int(rows[1])
                ))
            
            return ctx.tag[
                tags.h3[
                    tags.img(src="/images/stock-download.png"),
                    "Web Usage - Per user statistics for %s" % datetime.date(self.year, self.month, 1).strftime("%h %Y")
                ],
                tags.a(href=url.root.child("ProxyUse"))["Back to overview"], "  ",
                #tags.a(href=url.root.child("ProxyUse").child("ShowSites").child(self.year).child(self.month).child(self.day))["Sites overview"], "  ",
                tags.a(href=url.root.child("ProxyUse").child("ShowDays").child(self.year).child(self.month))["Back to month overview"],
                tags.br, tags.br,
                PageHelpers.dataTable([('str', 'Host'), ('str', 'Username'), ('int', 'Total Traffic'), ('int', 'Sites Visited')],
                    flatBlocks, sortable=True)
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
                tags.a(href=url.root.child("ProxyUse").child("ShowSites").child(self.year).child(self.month).child(self.day))["Sites overview"], "  ",
                tags.a(href=url.root.child("ProxyUse").child("ShowDays").child(self.year).child(self.month))["Back to month overview"],
                tags.br, tags.br,
                PageHelpers.dataTable([('str', 'Host'), ('str', 'Username'), ('int', 'Total Traffic'), ('int', 'Sites Visited')],
                    flatBlocks, sortable=True)
            ]
        if not self.day:
            return self.db.getDaySummary(self.year, self.month).addCallbacks(returnMonthView, error)
        else:
            if self.day == 32:
                return self.db.getSummary(self.year, self.month).addCallbacks(returnMonthIPView, error)
            return self.db.getSummary(self.year, self.month, self.day).addCallbacks(returnDayView, error)

    def locateChild(self, ctx, seg):
        print seg
        if len(seg) == 3:
            return ShowDays(self.avatarId, self.db, seg[0], seg[1]), ()

        if len(seg) == 4 and seg[2]: # Make sure the seg is valid
            if seg[2] == "0":
                return ShowDays(self.avatarId, self.db, seg[0], seg[1], 32), ()
            return ShowDays(self.avatarId, self.db, seg[0], seg[1], seg[2]), ()

        return ShowDays(self.avatarId, self.db, self.year, self.month, self.day), () # Return myself


class Page(Reports.Page):
    def __init__(self, avatarId = None, db = (None), *a, **kw):
        Reports.Page.__init__(self,avatarId, db[1], *a, **kw)

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
                print date
                year = int(date.split()[0])
                month = int(date.split()[2])
                flatBlocks.append((
                    tags.a(href=url.root.child("ProxyUse").child("ShowDays").child(year).child(month))[
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
                PageHelpers.dataTable([('cdate', 'Date'), ('int', 'Total Traffic'), ('int', 'Sites Visited')], 
                    flatBlocks, sortable=True)
            ]
        return self.db.getMonths().addCallbacks(returnMonthView, error)
    
    def childFactory(self, ctx, segment):
        if segment == "ShowDays":
            return ShowDays(self.avatarId, self.db)
        if segment == "ShowHost":
            return ShowHost(self.avatarId, self.db)
        if segment == "ShowSites":
            return ShowSites(self.avatarId, self.db)
        if segment == "ShowSiteHost":
            return ShowSiteHost(self.avatarId, self.db)

        return Page(self.avatarId, self.db)

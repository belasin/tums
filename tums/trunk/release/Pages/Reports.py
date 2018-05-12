from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os
from Core import PageHelpers, AuthApacheProxy

class Page(PageHelpers.DefaultPage):
    addSlash = True

    sideMenuItems = [
        (url.root.child("DiskUsage"), "display", "View disk utilisation", "Disk Usage"),
        (url.root.child("Logs"), "display", "View detailed system logs", "Log Viewer"),
        (url.root.child("Mail"), "display", "Mail logs", "Mail Logs"),
        (url.root.child("Existat"), "display", "Mail statistics", 'Mail Statistics'),
        (url.root.child("MailQueue"), "display", "Mail currently waiting for delivery", "Mail Queue"),
        (url.root.child("NetworkStats"), "display", "Network utilisation statistics", 'Network Utilisation'),
        (url.root.child("System"), "display", "Information about the hardware this server is running on", 'System Statistics'),
        (url.root.child("Updates"), "display", "Software update caching details", 'Updates'),
        (url.root.child("ProxyUse"), "display", "Reports on pages accessed through the web proxy", 'Web Usage'),
    ]

    sideMenuDynItems = []

    def __init__(self, avatarId, db, *a, **kw):
        if os.path.exists('/var/log/asterisk/cdr.db') and 'TelReport' not in self.sideMenuDynItems:
            self.sideMenuDynItems.append('TelReport') #Stop repeating menu items
            self.sideMenuItems.append((url.root.child("TelReport"), "display", "Reports on telephone usage", 'Telephone Usage'))
        super(Page, self).__init__(avatarId, db, *a, **kw)

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2[tags.img(src="/images/reports-lg.png"), " Reports"]]

    def sideMenu(self, avatarId):
        if (not avatarId.isAdmin) and avatarId.reports:
            # show a simpler menu
            # XXX Clean up this and generalise it better 
            self.sideMenuItems = [
                (url.root.child("DiskUsage"), "display", "View disk utilisation", "Disk Usage"),
                (url.root.child("Mail"), "display", "Mail logs", "Mail logs"),
                (url.root.child('Overview'), 'display', "A general overview and statistics", 'Month Overview'),
                (url.root.child("NetworkStats"), "display", "Network utilisation statistics", 'Network Utilisation'),
                (url.root.child("ProxyUse"), "display", "Reports on pages accessed through the web proxy", 'Web Proxy Usage Reporting'),
            ]

        return tags.div(id="sideCont")[
            [
                tags.div(_class="sideMenuPrimary")[
                    tags.div(_class="sideMenuNames")[
                        tags.a(_class="MenuOptionLink", href=item[0], title = item[2], onclick="showElement('loading');")[item[3]]
                    ]
                ]
            for item in self.sideMenuItems]
        ]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[
            self.sideMenu(self.avatarId)
        ]

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.h2["Reports"],
            tags.p["Please select a section from the list on the left"]
        ]

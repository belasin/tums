from nevow import rend, loaders, tags, athena
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP
from Core import PageHelpers, AuthApacheProxy, confparse, Utils, WebUtils
import formal, socket, struct

import Database

class calendarFragment(athena.LiveFragment):
    jsClass = u'calendar.PS'

    docFactory = loaders.xmlfile('calendar-frag.xml', templateDir = Settings.BaseDir + '/templates')

    def __init__(self, avatarId):
        super(calendarFragment, self).__init__()
        self.sysconf = confparse.Config()
        self.db = Database.CalendarDatabase()
        self.avatarId = avatarId

    @athena.expose
    def getEntries(self, year, flow):
        owner = "%s@%s" % (self.avatarId.username, self.avatarId.dom)
        print flow

        res = []

        lMonth = 0

        for month, day in flow:
            month = int(month)+1
            year = int(year)
            day = int(day)

            if not lMonth:
                lMonth = month

            if (month == 1) and (lMonth == 12):
                year += 1

            for r in self.db.getEntriesDay(owner, day, month, year):
                #CalendarEntry(day=10, descrip='sasd', emailAlert=False, hourE=10, hourS=10, minuteE=30, minuteS=0, month=11, owner='colin@netlink.za.net', private=False, repeats=0, vacation=False, year=2009, storeID=1)@0x9F1E7AC
                blStart = int((r.hourS + (r.minuteS/60.0)) * 2)
                blEnd = int((r.hourE + (r.minuteE/60.0)) * 2)
                res.append((
                    unicode(r.descrip),
                    r.day, 
                    r.month-1, 
                    blStart, 
                    blEnd, 
                    unicode(r.ehash), 
                    u"%02d:%02d" % (r.hourS, r.minuteS), 
                    u"%02d:%02d" % (r.hourE, r.minuteE), 
                ))

        print res

        return res

    def addEntry(self, desc, year, month, day, st, ed):

        stTime = [int(i) for i in st.split(':')]
        enTime = [int(i) for i in ed.split(':')]

        date = (int(day), int(month)+1, int(year))

        owner = "%s@%s" % (self.avatarId.username, self.avatarId.dom)

        v = self.db.createEntry(owner, date, stTime, enTime, desc.encode('ascii', 'replace'))
        print v 
        return
    athena.expose(addEntry)

class Page(PageHelpers.DefaultAthena):
    moduleName = 'calendar'
    moduleScript = 'calendar.js' 
    docFactory = loaders.xmlfile('calendar.xml', templateDir = Settings.BaseDir + '/templates')

    addSlash = True

    def render_thisFragment(self, ctx, data):
        """ Renders calendarFragment instance """
        f = calendarFragment(self.avatarId)
        f.setFragmentParent(self)
        return ctx.tag[f]

    def render_pageName(self, ctx, data):
        return ctx.tag[""]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[""]

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.div[
                tags.invisible(render=tags.directive('thisFragment'))
            ]
        ]


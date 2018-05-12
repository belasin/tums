from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP
from Core import PageHelpers, AuthApacheProxy
from Pages import Tools
import formal
import _mysql

class Page(PageHelpers.DefaultPage):
    addSlash = True

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Tools"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Tools.Page.sideMenu(Tools.Page(None, self.db), ctx, data)]

    def render_content(self, ctx, data):
        db=_mysql.connect("localhost","root","rossi","mysql")
        db.query("SELECT * from db")
        r=db.use_result()
        l = True
        records = []
        while l:
            l = r.fetch_row()
            if l:
                row = l[0]

                records.append((row[1], row[2]))
        return ctx.tag[
            tags.h2[tags.img(src="/images/netdrive.png"), " MySQL Administration"],
            tags.table[
                [
                    tags.tr[
                        [tags.td[j] for j in i]
                    ]
                for i in records]
            ]
        ]


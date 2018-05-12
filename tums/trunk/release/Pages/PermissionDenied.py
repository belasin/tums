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

class Page(PageHelpers.DefaultPage):
    addSlash = True

    def render_pageName(self, ctx, data):
        return ctx.tag[""]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[""]
 
    def render_content(self, ctx, data):
        return ctx.tag[
            "You do not have permission to access this page"
        ]


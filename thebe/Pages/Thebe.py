from enamel import authentication, deployment, pages, servers, storage, deferreds, tags
from enamel import sql
import enamel

from twisted.internet import utils

from Pages import ThebeUsers, ThebeGroups, ThebeServers, ThebeGlobals, ThebeDomains

from lib import PageBase

class Page(PageBase.Page):
    childPages = {
        "Users": ThebeUsers.Page,
        "Groups": ThebeGroups.Page,
        "Servers": ThebeServers.Page,
        "Domains": ThebeDomains.Page,
        "Globals": ThebeGlobals.Page, 
        "SetDomainGroup":ThebeDomains.Set
    }

    def document(self):
        return pages.template('defaultc.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Thebe"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[
            tags.a(href="Users/")['Manage Users'], tags.br, 
            tags.a(href="Groups/")['Manage Groups'], tags.br,
            tags.a(href="Servers/")['Manage Servers'], tags.br,
            tags.a(href="Domains/")['Manage Domains'], tags.br,
            tags.a(href="Globals/")['Global Operations'], tags.br,
        ]

    def rollupBlock(self, title, content):
        return tags.div(_class="roundedBlock")[title,tags.div[content]]

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.h3["Thebe"],
            tags.a(href="Users/")['Manage Users'], tags.br, 
            tags.a(href="Groups/")['Manage Groups'], tags.br,
            tags.a(href="Servers/")['Manage Servers'], tags.br,
            tags.a(href="Domains/")['Manage Domains'], tags.br,
            tags.a(href="Globals/")['Global Operations'], tags.br,
        ]


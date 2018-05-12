from enamel import authentication, deployment, pages, servers, storage, deferreds, tags
from enamel import sql, form, url
import enamel, sha

from custom import Widgets

from twisted.internet import utils, defer

from lib import PageBase

class ViewGroup(PageBase.Page):
    arbitraryArguments = True
    def document(self):
        return pages.template('defaultc.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))

    def form_addMembership(self, data):
        # XXX Should only show this for Thusa group members
        addMember = form.Form()
        def gotUserGroups(user):
            users = [ (i[0], i[1]) for i in user ]
            addMember.addField('user', form.Integer(required=True), form.widgetFactory(form.SelectChoice, options = users), label = "User")
            addMember.addAction(self.addMembership)
            return addMember

        return self.enamel.storage.getUsers().addBoth(gotUserGroups)

    def addMembership(self, ctx, form, data):
        gid = int(self.arguments[0])
        def ok(_):
            return url.root.child('Thebe').child('Groups').child('View').child(self.arguments[0])

        return self.enamel.storage.addMembership(data['user'], gid).addBoth( ok)

    def form_addServerMembership(self, data):
        # XXX Should only show this for Thusa group members
        addMember = form.Form()
        def gotServerGroups(server):
            servers = [ (i[0], i[1]) for i in server ]
            addMember.addField('server', form.Integer(required=True), form.widgetFactory(form.SelectChoice, options = servers), label = "Server")
            addMember.addAction(self.addServerMembership)
            return addMember


        return self.enamel.storage.getServers().addBoth(gotServerGroups)

    def addServerMembership(self, ctx, form, data):
        gid = int(self.arguments[0])
        def ok(_):
            return url.root.child('Thebe').child('Groups').child('View').child(self.arguments[0])
        return self.enamel.storage.addServerMembership(gid, data['server']).addBoth(ok)

    def form_addDomainMembership(self, data):
        addMember = form.Form()
        def gotServerGroups(doms):
            domains = [ (i[0], i[1]) for i in doms ]
            addMember.addField('domain', form.Integer(required=True), form.widgetFactory(form.SelectChoice, options = domains), label = "Domain")
            addMember.addAction(self.addDomainMembership)
            return addMember


        return self.enamel.storage.getDomains().addBoth(gotServerGroups)

    def addDomainMembership(self, ctx, form, data):
        gid = int(self.arguments[0])
        def ok(_):
            return url.root.child('Thebe').child('Groups').child('View').child(self.arguments[0])

        return self.enamel.storage.addDomainMembership(gid, data['domain']).addBoth(ok)

    def render_content(self, ctx, data):
        gid = int(self.arguments[0])
        def renderTime(deferreds):
            # Unpack results
            users, servers, domains = [i[1] for i in deferreds]

            userTable = []
            for row in users:
                print row
                userTable.append((
                    row[1], 
                ))

            serverTable = []
            for row in servers:
                serverTable.append((
                    row[1], 
                    row[2]
                ))

            domainTable = []
            for row in domains:
                domainTable.append((
                    row[1], 
                    ""
                ))

            return ctx.tag[
                PageBase.TabSwitcher((
                    ('Users', 'pUsers'), 
                    ('Servers', 'pServers'), 
                    ('Domains', 'pDomains')
                )), 
                tags.div(id='pUsers', _class="tabPane")[
                    tags.h3["Users"],
                    self.dataTable(["Username"], userTable), 
                    tags.br, 
                    tags.h3["Add User"],
                    tags.directive('form addMembership')
                ],
                tags.div(id='pServers', _class="tabPane")[
                    tags.h3["Servers"],
                    self.dataTable(["Server", "Hostname"], serverTable), 
                    tags.br, 
                    tags.h3["Add Server"],
                    tags.directive('form addServerMembership')
                ],
                tags.div(id='pDomains', _class="tabPane")[
                    tags.h3["Domains"],
                    self.dataTable(["Domain", ""], domainTable), 
                    tags.br, 
                    tags.h3["Add Domain"],
                    tags.directive('form addDomainMembership')
                ], 
                PageBase.LoadTabSwitcher()
            ]
        
        return defer.DeferredList([
            self.enamel.storage.getGroupUsers(gid), 
            self.enamel.storage.getServersInGroup([gid]), 
            self.enamel.storage.getDomainsInGroup([gid])
        ]).addBoth(renderTime)

class Page(PageBase.Page):
    childPages = {
        'View': ViewGroup
    }

    def document(self):
        return pages.template('defaultc.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Thebe Users"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[""]

    def form_addGroup(self, data):
        addGroups = form.Form()
        addGroups.addField('name', form.String(), label = "Group Name")
        # XXX Add a dropdown box here if the Avatars group id is 0 (Thusa group)
        addGroups.addAction(self.addGroup)

        return addGroups

    def addGroup(self, ctx, form, data):
        def added(_):
            return url.root.child('Thebe').child('Groups')
        return self.enamel.storage.addGroup(
            data['name'].encode(),
        ).addCallbacks(added, added)

    def render_content(self, ctx, data):
        def gotGroups(groups):
            tlist = []

            for k in groups:
                tlist.append((
                    tags.a(href="View/%s/" % k[0])[k[1]], 
                    tags.a(href="Delete/%s/" % k[0])["Delete"]
                ))

            return ctx.tag[
                tags.h3["Group list"],
                self.dataTable(["Group name", ""], tlist),
                tags.br, tags.br,
                tags.h3["Add group"],
                tags.directive('form addGroup'),
            ]

        return self.enamel.storage.getGroups().addBoth(gotGroups)
    

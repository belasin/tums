from enamel import authentication, deployment, pages, servers, storage, deferreds, tags, url
from enamel import sql, form
import enamel, sha

from custom import Widgets
from twisted.internet import utils, defer

from lib import PageBase

class Page(PageBase.Page):
    arbitraryArguments = True # Enable REST style arguments to the page

    def document(self):
        return pages.template('defaultc.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Thebe Users"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[""]

    def form_addUser(self, data):
        addUsers = form.Form()
        addUsers.addField('name', form.String(), label = "Username")
        addUsers.addField('email', form.String(), label = "EMail address")
        addUsers.addField('password', form.String(), label = "Password")
        # XXX Add a dropdown box here if the Avatars group id is 0 (Thusa group)
        addUsers.addAction(self.addUser)

        return addUsers

    def addUser(self, ctx, form, data):
        def goBack(_):
            return url.root.child('Thebe').child('Users')

        return self.enamel.storage.addUser(
            data['name'].encode(),
            sha.sha(data['password'].encode()).hexdigest(),
            data['email'].encode()
        ).addCallbacks(goBack, goBack)


    def rollupBlock(self, title, content):
        return tags.div(_class="roundedBlock")[title,tags.div[content]]

    def render_content(self, ctx, data):
        def gotres(res):
            table = []
            # Create a dictionary out of our group memberships
            glist = {}
            for g in res[1][1]:
                if g[0] in glist:
                    glist[g[0]].append((g[1], g[2]))
                else:
                    glist[g[0]] = [(g[1], g[2])]

            for user in res[0][1]:
                groups = [ (i[1], tags.br) for i in glist.get(user[0], [])]
                table.append((user[0], tags.a(href="/Account/%s/" % user[0])[user[1]], user[3] or "Not set", user[4] or "Not set", groups))

            return ctx.tag[
                tags.h3["Users"],
                Widgets.autoTable(['Id', 'Username', 'Name', 'Email', 'Groups'], table),
                tags.h3["Add user"],
                tags.directive('form addUser')
            ]
        return defer.DeferredList([self.enamel.storage.getUsers(), self.enamel.storage.getMemberships()]).addCallbacks(gotres, gotres)


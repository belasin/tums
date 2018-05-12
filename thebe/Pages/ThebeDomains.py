from enamel import authentication, deployment, pages, servers, storage, deferreds, tags, url
from enamel import sql, form
import enamel, sha

from custom import Widgets
from twisted.internet import utils, defer

from lib import PageBase

from nevow import inevow

class Set(PageBase.Page):
    def document(self):
        return pages.template('defaultc.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))
        
    def locateChild(self, ctx, args):
        request = inevow.IRequest(ctx)
        vals = request.args
        dchain = []
        for k, v in vals.items():
            if not 'dom' in k:
                # only deal with the right values
                continue
            
            print k, v
            did = int(k[3:])
            gid = int(v[0][3:])

            def done(re):
                return
            
            def addMember(res, did, gid):
                print "Member for %s deleted. Adding membership for %s to %s" % (did, did, gid)
                return self.enamel.storage.addDomainMembership(gid, did).addBoth(done)

            dchain.append(self.enamel.storage.deleteDomainMembership(did).addBoth(addMember, did, gid))
 
        def good(r):
            return url.root.child('Thebe').child('Domains'), ()

        return defer.DeferredList(dchain).addBoth(good)


class Page(PageBase.Page):
    arbitraryArguments = True # Enable REST style arguments to the page

    def document(self):
        return pages.template('defaultc.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Thebe Domains"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[""]

    def form_addDomain(self, data):
        addDomain = form.Form()
        addDomain.addField('domain', form.String(), label = "Domain")
        addDomain.addAction(self.addDomain)

        return addDomain

    def addDomain(self, ctx, form, data):
        def goBack(_):
            return url.root.child('Thebe').child('Domains')

        return self.enamel.storage.addDomain(
            data['domain'].encode(),
        ).addCallbacks(goBack, goBack)


    def rollupBlock(self, title, content):
        return tags.div(_class="roundedBlock")[title,tags.div[content]]

    def render_content(self, ctx, data):
        def gotres(res):
            groups = [i for i in res[1][1]]
            gmem = {}
            for i in res[2][1]: 
                gmem[i[0]] = i[1]
            table = []
            for i in res[0][1]:
                grps = []
                for g in groups:
                    if gmem.get(i[0],None) == g[0]:
                        grps.append(tags.option(value="grp%s"%g[0], selected="selected")[g[1]])
                    else:
                        grps.append(tags.option(value="grp%s"%g[0])[g[1]])

                table.append([
                    i[0], i[1], 
                    tags.select(name="dom%s"%i[0])[
                        grps
                    ]
                ])

            return ctx.tag[
                tags.h3["Domainss"],
                tags.form(action="/Thebe/SetDomainGroup/", method="post")[
                    Widgets.autoTable(['Id', 'Domain', 'Group'], table),
                    tags.br,
                    tags.input(type="submit",value="Save Groups")
                ],
                tags.h3["Add domain"],
                tags.directive('form addDomain')
            ]

        return defer.DeferredList([
            self.enamel.storage.getDomains(), 
            self.enamel.storage.getGroups(),
            self.enamel.storage.getDomainMemberships(),
        ]).addCallbacks(gotres, gotres)


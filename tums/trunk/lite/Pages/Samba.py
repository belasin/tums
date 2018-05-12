from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
import time, formal, LDAP, os
import Tree, Settings
from Core import PageHelpers, confparse, Utils, WebUtils
from Pages import Users, Tools

class Page(PageHelpers.DefaultPage):
    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Tools"]]

    def reloadSamba(self):
        WebUtils.system(Settings.BaseDir+'/configurator --samba')
        WebUtils.system("/etc/init.d/samba restart");

    def form_addShare(self, data):
        form = formal.Form()

        form.addField('share', formal.String(required=True), label = "Shared Folder")
        form.addField('path', formal.String(required=True), label = "Shared Path", description = "Path to be shared")
        form.addField('comment', formal.String(required=True), label = "Comment")

        form.addField('public', formal.Boolean(), label = "Public")
        form.addField('writable', formal.Boolean(), label = "Writable")

        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dc = "%s,o=%s" % (LDAP.domainToDC(Settings.defaultDomain), Settings.LDAPBase)

        groups = LDAP.getGroups(l, dc)
        groups.sort()
                                

        form.addField('group', formal.String(), 
            formal.widgetFactory(formal.SelectChoice, options = [(i[1],i[1]) for i in groups]), 
            label = "Required Group")
        
        form.addAction(self.submitForm)

        return form

    def submitForm(self, ctx, form, data):
        if "/" in data['path']:
            path = data['path']
        else:
            path = '/var/lib/samba/data/%s' % data['path']
            
        share = {} #[%s]\n" % (data['share'],)
        share["path"] = path
        share["comment"] = data['comment']
        share["create mode"] = '664'
        share["directory mode"] = '775'
        WebUtils.system('mkdir -p %s' % path)
        
        if data['public']:
            share["public"] = "yes"

        if data['writable']:
            share["writable"] = "yes"

        if data['group']:
            share["valid users"] = '@"%s"' % data['group']
            WebUtils.system('chown -R root:"%s" %s' % (data['group'], path))

        WebUtils.system('chmod a+rwx %s' % path)
        WebUtils.system('chmod -R a+rw %s' % path)

        shares = self.sysconf.SambaShares
        shares[data['share'].encode()] = share
        self.sysconf.SambaShares = shares

        self.reloadSamba()
        
        return url.root.child('Samba')

    def locateChild(self, ctx, segs):
        if segs[0]=="Delete":
            try:
                shares = self.sysconf.SambaShares
                del shares[segs[1]]
                self.sysconf.SambaShares = shares
            except Exception, e:
                print "Error deleting share", e
            return url.root.child('Samba'), ()
            
        return rend.Page.locateChild(self, ctx, segs)

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Tools.Page.sideMenu(Tools.Page(None, self.db), ctx, data)]

    def render_content(self, ctx, data):
        shares = self.sysconf.SambaShares

        return ctx.tag[
            tags.h2[tags.img(src="/images/sharefold.png"), " Shared folders"],
            tags.table(cellspacing="0", _class="listing")[
                tags.thead(background="/images/gradMB.png")[
                    tags.tr[
                        tags.th['Shared Folder'], 
                        tags.th['Shared Path'], 
                        tags.th['Comment'], 
                        tags.th['Writable'], 
                        tags.th['Public'], 
                        tags.th['Permission'],
                        tags.th[''],
                    ]
                ],
                tags.tbody[
                    [ tags.tr[
                        tags.td[share],
                        [
                            tags.td[shares[share].get(i, None) or ""] 
                        for i in ['path', 'comment', 'writable', 'public','valid users']],
                        tags.td[
                            tags.a(
                                href='Delete/%s/' % (share,), 
                                onclick="return confirm('Are you sure you want to delete this share?');"
                            )[tags.img(src="/images/ex.png")]
                        ]
                    ] for share in shares.keys() if not share=="global"]
                ]
            ],
            tags.h3["Add new share"],
            tags.directive('form addShare'),
        ]

from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
import time, formal, LDAP, os
import Tree, Settings
from Core import PageHelpers, Utils, WebUtils
from Pages import Users, Tools

class Page(PageHelpers.DefaultPage):

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2[self.text.tools]]

    def form_addComputer(self, data):
        form = formal.Form()

        form.addField('name', formal.String(required=True), label = self.text.compName)

        form.addAction(self.submitForm)

        return form

    def submitForm(self, ctx, form, data):
        name = data['name']
        WebUtils.system('smbldap-useradd -w %s$; smbpasswd -a -m %s$' % (name, name))
        return url.root.child('Computers')

    def locateChild(self, ctx, segs):
        if segs[0]=="Delete":
            # Deletes Computer. 
            name = segs[1]
            WebUtils.system('smbldap-userdel %s$' % (name, ))
            return url.root.child('Computers'), ()
            
        return rend.Page.locateChild(self, ctx, segs)

    def getComputers(self):
        proc = os.popen('getent passwd | grep Computer')
        comps = []
        for i in proc:
            if i.strip('\n'):
                name = i.split(':')[0].strip('$')
                comps.append([name, tags.a(href=url.root.child("Computers").child("Delete").child(name), 
                onclick="return confirm('%s');" % self.text.compConfirm)[tags.img(src="/images/ex.png")]])

        return comps

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Tools.Page.sideMenu(Tools.Page(None, self.db), ctx, data)]

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.h2[tags.img(src='/images/srvman.png'), self.text.compHeading], 
            tags.h3[self.text.compHeadingList],
            PageHelpers.dataTable([self.text.compName, ''], self.getComputers()),
            tags.h3[self.text.compHeadingAdd],
            tags.directive('form addComputer'),
        ]

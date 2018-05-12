from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import time, formal, LDAP, os
import Tree, Settings

from Core import PageHelpers, Utils, WebUtils
from Pages import Tools

from twisted.python import log

from twisted.internet.defer import deferredGenerator, waitForDeferred as wait


class Page(Tools.Page):

    def form_addComputer(self, data):
        form = formal.Form()

        form.addField('name', formal.String(required=True), label = self.text.compName)

        form.addAction(self.submitForm)

        return form

    def submitForm(self, ctx, form, data):
        Utils.log.msg('%s added computer %s' % (self.avatarId.username, repr(data)))
        
        name = data['name'].encode()
        
        def returnPage(result):
            Utils.log.msg(result)
            return url.root.child('Computers')

        return WebUtils.system('smbldap-useradd -w %s$; smbpasswd -a -m %s$' % (name, name)).addBoth(returnPage)

    def locateChild(self, ctx, segs):
        if segs[0]=="Delete":
            # Deletes Computer. 
            Utils.log.msg('%s deleted computer %s' % (self.avatarId.username, segs[1]))
            name = segs[1]
            def returnPage(_):
                return url.root.child('Computers'), ()
            return WebUtils.system('smbldap-userdel %s$' % (name, )).addBoth(returnPage)
            
        return rend.Page.locateChild(self, ctx, segs)

    @deferredGenerator
    def render_content(self, ctx, data):
        mq = WebUtils.system('getent passwd | grep Computer')
        def gotResult(proc):
            comps = []
            for i in proc.split('\n'):
                if i.strip('\n'):
                    name = i.split(':')[0].strip('$')
                    comps.append([name, tags.a(href=url.root.child("Computers").child("Delete").child(name), 
                    onclick="return confirm('%s');" % self.text.compConfirm)[tags.img(src="/images/ex.png")]])
            return comps
        res = wait(mq)
        yield res
        mq = res.getResult()
        getComputers = gotResult(mq)

        Utils.log.msg('%s opened Tools/Computers' % (self.avatarId.username))
        yield ctx.tag[
            tags.h3[tags.img(src='/images/srvman.png'), self.text.compHeading], 
            tags.h3[self.text.compHeadingList],
            PageHelpers.dataTable([self.text.compName, ''], getComputers, sortable=True),
            tags.h3[self.text.compHeadingAdd],
            tags.directive('form addComputer'),
        ]

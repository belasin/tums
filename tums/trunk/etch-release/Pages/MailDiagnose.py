from nevow import rend, loaders, tags, athena
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP
from Core import PageHelpers, AuthApacheProxy, confparse, Utils, WebUtils
from Pages import Tools
import formal, socket, struct

class liveGraphFragment(athena.LiveFragment):
    jsClass = u'diagnostics.PS'

    docFactory = loaders.xmlfile('mail-diagnostics.xml', templateDir = Settings.BaseDir + '/templates')

    def __init__(self, *a, **kw):
        super(liveGraphFragment, self).__init__(*a, **kw)
        self.sysconf = confparse.Config()

    def testAddress(self, addr):
        def eximbt(res):
            print res
            return unicode(res)
        return WebUtils.system("exim -bt %s" % addr.encode('ascii')).addCallback(eximbt)
    athena.expose(testAddress)

class Page(PageHelpers.DefaultAthena):
    moduleName = 'diagnostics'
    moduleScript = 'mail-diagnostics.js' 
    docFactory = loaders.xmlfile('livepage.xml', templateDir = Settings.BaseDir + '/templates')

    addSlash = True

    def render_thisFragment(self, ctx, data):
        """ Renders liveGraphFragment instance """
        f = liveGraphFragment()
        f.setFragmentParent(self)
        return ctx.tag[f]

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2[tags.img(src='/images/tools-lg.png'), " Tools"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Tools.Page.sideMenu(Tools.Page(None, self.db), ctx, data)]

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.h3[tags.img(src="/images/networking_section.png"), " Mail Diagnostics"],
            tags.div[
                tags.invisible(render=tags.directive('thisFragment'))
            ]
        ]


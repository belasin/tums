from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, LDAP, formal, ldap, os, random, sha
from Core import PageHelpers, Utils, confparse, WebUtils
import copy, time
from Pages import VPN # Import the VPN module for making certs

alpha = "LLPETUMS"

class Page(PageHelpers.DefaultPage):
    addSlash = True
    flatFil = []
    docFactory  = loaders.xmlfile('ldaptree.xml', templateDir=Settings.BaseDir+'/templates')

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2[tags.img(src="/images/users-lg.png"), " ", self.text.users]]

    def __init__(self, avatarId=None, db=None, domain = None, *a, **ka):
        PageHelpers.DefaultPage.__init__(self, avatarId, db, *a, **ka)
        self.avatarId = avatarId
        self.db = db
        self.domain = domain
        self.cid = None
                            
    def render_editContent(self, ctx, data):
        return ctx.tag[""]

    def render_treeView(self, ctx, data):
        try:
            T = Tree.Tree("r", "Domains")
            l = Tree.retrieveTree(Settings.LDAPServer, Settings.LDAPManager, Settings.LDAPPass, 'o='+Settings.LDAPBase)
            flatL = Tree.flattenTree(l, 'o='+Settings.LDAPBase)
            flatL.sort()
            self.flatFil = []
        except Exception, e:
            flatL = []
            Utils.exceptionOccured(e)
        if not self.avatarId.isAdmin:
            for nod in flatL:
                for d in self.avatarId.domains:
                    if (d in nod):
                        self.flatFil.append(nod)
                    elif not "dm=" in nod:
                        self.flatFil.append(nod)
        else:
            self.flatFil = flatL
                    
        for node in self.flatFil:
            Tree.addPath(node, T)
    
        return ctx.tag[
            tags.div(id="TreeCont")[Tree.StanTree(T, self.cid)],
        ]

    def render_content(self, ctx, data):
        return ctx.tag[tags.div(id="rightBlock")[tags.invisible(render=tags.directive('editContent'))]]

class FailurePage(Page):
    def __init__(self, avatarId=None, db=None, code = None, *a, **ka):
        PageHelpers.DefaultPage.__init__(self,avatarId, db, *a, **ka)
        self.code = code
        self.cid="XXXXXXXXXXXXXXX"

    def render_editContent(self, ctx, data):
        codeDescr = {
            '0x11': "Failed to add local domain entry for new domain.",
            '0x12': "Failed to add OU entry for new domain.",
            '0x13': "Failed to delete OU entry for domain.",
            '0x14': "Failed to delete local domain entry for domain."
        }
        
        return ctx.tag[
            tags.h3["Error occured in last operation"],
            tags.p["An error has occured in the last operation. Code %s: %s" % (
                self.code,
                codeDescr.get(self.code, "Unknown Error")
            )
            ],
        ]

    def childFactory(self, ctx, seg):
        if not self.code:
            return FailurePage(self.avatarId, self.db, seg)
        else:
            return FailurePage(self.avatarId, self.db, self.code)



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
from Pages.Users import Add, Edit, Domains, Base, Group, Delete, Bulk

alpha = "LLPETUMS"

class Page(Base.Page):
    def childFactory(self, ctx, seg):
        set = {
            "Edit":         Edit.editPage,
            "Groups":       Group.editGroups,
            "GroupMod":     Group.editGroupsByGroup,
            "GroupAdd":     Group.addGroups,
            "Delete":       Delete.deletePage,
            "Add":          Add.addPage,
            "DomainAdd":    Domains.addDomain,
            "DomainDel":    Domains.delDomain,
            "Bulk":         Bulk.bulkUsers,
            "Failed":       Base.FailurePage
        }
        
        if seg in set.keys():
            return set[seg](self.avatarId, db=self.db)
        else:
            return Page(self.avatarId, self.db, seg)
    
    def render_editContent(self, ctx, data):
        return ctx.tag[
            tags.h2[self.text.userManagement],
            tags.p[self.text.usersBeginInstruction],
            tags.br,
            tags.img(src="/images/truck.png", alt="Bulk", style="vertical-align: middle"),
            " ",
            tags.a(href="Bulk/")["Bulk modifications"]
        ]

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



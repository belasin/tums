from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, LDAP, formal, ldap, os, random, sha
import base64
from Core import PageHelpers, Utils, confparse, WebUtils
import copy, time
from Pages import VPN # Import the VPN module for making certs
from Pages.Users import Base
alpha = "LLPETUMS"

class addGroups(Base.Page):
    addSlash = True
    cid = None
    domain = None

    def __init__(self, avatarId=None, domain=None, cid=None, db=None, *a, **ka):
        PageHelpers.DefaultPage.__init__(self, avatarId, db, *a, **ka)
        self.avatarId = avatarId
        self.domain = domain
        self.cid = cid

    def form_editForm(self, data):
        form = formal.Form()
        form.addField('groupName', formal.String(), label=self.text.userFormGroupName)
        form.addAction(self.submitForm)
        return form

    def submitForm(self, ctx, form, data):
        if data['groupName']:
            WebUtils.system('smbldap-groupadd -a %s' % data['groupName'].replace('-',''))
        
        #return url.root.child('auth').child('Users')
        if not self.cid:
            return url.root.child('Users').child('GroupMod').child(self.domain)
        else:
            return url.root.child('Users').child('Groups').child(self.domain).child(self.cid)

    def render_editContent(self, ctx, data):
        return ctx.tag[
            tags.h3[self.text.userHeadingAddGroup],
            tags.directive('form editForm')
        ]

    def childFactory(self, ctx, seg):
        if not self.domain:
            return addGroups(self.avatarId, seg, db=self.db)
        elif not self.cid:
            return addGroups(self.avatarId, self.domain, seg, db=self.db)

class editGroupsByGroup(Base.Page):
    addSlash = True
    def __init__(self, avatarId=None, db=None, domain=None, group=None, *a, **ka):
        PageHelpers.DefaultPage.__init__(self,avatarId, db, *a, **ka)
        self.group=group
        self.domain=domain
        self.cid="XXXXXXXXXXXXXXX"

    def addedMenu(self):
        return [
            tags.img(src="/images/blockMB.png"),
            [
                tags.a(href=elm[0])[tags.img(src=elm[1])]
                for elm in self.pageMenu+[(url.root.child('Users').child('Add').child(str(self.domain)), '/images/addUser.png'),
                (url.root.child('Users').child('DomainAdd'), '/images/adddom.png')]
            ]
        ]

    def form_editForm(self, data):
        form = formal.Form()
        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dc = "%s,o=%s" % (LDAP.domainToDC(self.domain), Settings.LDAPBase)

        users = [i['uid'][0] for i in LDAP.getUsers(l, "ou=People,"+dc)]
        users.sort()
        
        form.data = {}

        for user in users:
            fieldName = base64.urlsafe_b64encode(user).replace('=','_')
            form.addField(fieldName, formal.Boolean(), label = user)
            form.data[fieldName] = LDAP.isMemberOf(l, dc, user, group=self.group)

        form.addAction(self.submitForm)
        l.unbind_s()
        return form

    def submitForm(self, ctx, form, data):
        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dc = "%s,o=%s" % (LDAP.domainToDC(self.domain), Settings.LDAPBase)
        users = [i['uid'][0] for i in LDAP.getUsers(l, "ou=People,"+dc)]

        for user in users:
            fieldName = base64.urlsafe_b64encode(user).replace('=','_')
            if data[fieldName]:
                LDAP.makeMemberOf(l, dc, user, self.group)
            else:
                LDAP.makeNotMemberOf(l, dc, user, self.group)
        l.unbind_s() 
        return url.root.child('Users').child('GroupMod').child(self.domain)

    def render_editContent(self, ctx, data):
        if not self.avatarId.checkDomainPermissions(self.domain):
            return ctx.tag[
                "Not Authorised"
            ]
            
        if not self.group:
            l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
            dc = "%s,o=%s" % (LDAP.domainToDC(self.domain), Settings.LDAPBase)
            groups = LDAP.getGroups(l, dc)
            l.unbind_s() 
            return ctx.tag[
                tags.h3["Groups"], 
                tags.table(cellspacing="0", _class="listing")[
                    tags.thead(background="/images/gradMB.png")[
                        tags.tr[
                            tags.th[self.text.userFormGroupName],
                            tags.th[''],
                        ]
                    ],
                    tags.tbody[
                        [ 
                            tags.tr[
                                tags.td[group[1]], 
                                tags.td[
                                    tags.a(href=url.root.child("Users").child('GroupMod').child(self.domain).child(group[1]))[
                                        self.text.userLinkEditMembership
                                    ]
                                ]
                            ]
                        for group in groups]
                    ]
                ],
                tags.a(href=url.root.child("Users").child('GroupAdd').child(self.domain))[self.text.userLinkCreateGroup]
            ]
        else:
            return ctx.tag[
                tags.h3["%s%s" % (self.text.userHeadingMemberships, self.group)],
                tags.directive('form editForm')
            ]
        return ctx.tag[
            tags.h3[self.text.userErrorUserPlayedWithLink],
        ]

    def childFactory(self, ctx, seg):
        if not self.domain:
            return editGroupsByGroup(self.avatarId, self.db, seg, None)
        else:
            return editGroupsByGroup(self.avatarId, self.db, self.domain, seg)

class editGroups(Base.Page):
    addSlash = True
    userData = {}
    groups = []
    
    def __init__(self, avatarId=None, db=None, cid=None, domain = None, *a, **ka):
        PageHelpers.DefaultPage.__init__(self, avatarId, db, *a, **ka)
        self.avatarId = avatarId
        self.cid = cid
        self.domain = domain

    def form_editForm(self, data):
        form = formal.Form()
        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dc = "%s,o=%s" % (LDAP.domainToDC(self.domain), Settings.LDAPBase)

        self.groups = LDAP.getGroups(l, dc)
        
        form.data = {}
        for group in self.groups:
            form.addField(group[0], formal.Boolean(), label=group[1])
            form.data[group[0]] = LDAP.isMemberOf(l, dc, self.cid, group=group[1])

        form.addAction(self.submitForm)

        if self.avatarId.isAdmin:
            domains = []
            for i in self.flatFil:
                thisdom = i.split('dm=')[-1].split(',')[0]
                if not thisdom in domains:
                    domains.append(thisdom)
        l.unbind_s()
        return form

    def submitForm(self, ctx, form, data):
        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dc = "%s,o=%s" % (LDAP.domainToDC(self.domain), Settings.LDAPBase)
        self.groups = LDAP.getGroups(l, dc)
        for group in self.groups:
            if data.get(group[0], None):
                LDAP.makeMemberOf(l, dc, self.cid, group[1])
            else:
                LDAP.makeNotMemberOf(l, dc, self.cid, group[1])
        l.unbind_s() 
        return url.root.child('Users').child('Edit').child(self.domain).child(self.cid)

    def render_editContent(self, ctx, data):
        if not self.avatarId.checkDomainPermissions(self.domain):
            return ctx.tag[
                "Nice try"
            ]
        return ctx.tag[
            tags.h3[self.text.userHeadingMembershipsUser, self.cid], 
            tags.directive('form editForm'), 
            tags.br, 
            tags.a(href=url.root.child("Users").child('GroupAdd').child(self.domain).child(self.cid))[self.text.userLinkCreateGroup]
        ]

    def childFactory(self, ctx, seg):
        if not self.domain:
            return editGroups(self.avatarId, self.db, None, seg)
        else:
            return editGroups(self.avatarId, self.db, seg, self.domain)


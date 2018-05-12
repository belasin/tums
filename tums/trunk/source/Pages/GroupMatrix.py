from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
import time, formal, LDAP, os
import Tree, Settings
from Core import PageHelpers
from Pages import Tools

class Page(Tools.Page):
    groups = []
    users = []
    def form_groupForm(self, data):
        form = formal.Form()
        # get groups
        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dc = "%s,o=%s" % (LDAP.domainToDC(Settings.defaultDomain), Settings.LDAPBase)
        
        self.groups = LDAP.getGroups(l, dc)
        
        # get users

        self.users = [i['uid'][0] for i in LDAP.getUsers(l, "ou=People,"+dc)]
        
        form.data = {}
        for group in self.groups:
            for user in self.users:
                username = user
                field = "%s_%s" % (group[0], username)
                form.addField(field.replace('.','').replace('-',''), formal.Boolean(), label="%s-%s" % (group[1], username))
                form.data[field] = LDAP.isMemberOf(l, dc, username, group=group[1])
        
        form.addAction(self.submitForm)
        
        return form

    def submitForm(self, ctx, form, data):
        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dc = "%s,o=%s" % (LDAP.domainToDC(Settings.defaultDomain), Settings.LDAPBase)
        self.groups = LDAP.getGroups(l, dc)
        self.users = [i['uid'][0] for i in LDAP.getUsers(l, "ou=People,"+dc)]

        for group in self.groups:
            for user in self.users:
                username = user
                if data["%s_%s" % (group[0].replace('.','').replace('-',''), username.replace('.','').replace('-',''))]:
                    LDAP.makeMemberOf(l, dc, username, group[1])
                else:
                    LDAP.makeNotMemberOf(l, dc, username, group[1])

        return url.root.child('GroupMatrix')

    def matrixForm(self):
        # get groups
        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dc = "%s,o=%s" % (LDAP.domainToDC(Settings.defaultDomain), Settings.LDAPBase)

        self.groups = LDAP.getGroups(l, dc)

        # get users

        self.users = [i['uid'][0] for i in LDAP.getUsers(l, "ou=People,"+dc)]
        self.users.sort()

        tableCont = []
        ucnt = 0
        for user in self.users:
            ucnt += 1 
            username = user
            thisRow = [tags.td[username]]
            gcnt = 0
            for group in reversed(self.groups):
                gcnt += 1
                egroup = gcnt % 2
                euser = ucnt % 2 
                if egroup and euser:
                    colour = "#F5F5EB"
                if egroup and not euser:
                    colour = "#DFD6BF"
                if not egroup and euser:
                    colour = "#F5F0EB"
                if not egroup and not euser:
                    colour = "#DEDEBE" 
                isMember = LDAP.isMemberOf(l, dc, username, group=group[1])
                if isMember:
                    thisRow.append(tags.td(style="text-align: center;background:%s"% colour)[
                        tags.input(checked="checked",type="checkbox",id="groupForm-%s_%s" % (group[0], username),
                            value="True",name="%s_%s" % (group[0], username)
                        )
                    ])
                else:
                    thisRow.append(tags.td(style="text-align: center;background:%s" % colour)[
                        tags.input(type="checkbox",id="groupForm-%s_%s" % (group[0], username),value="True",name="%s_%s" % (group[0], username))
                    ])
                                                    
                

            tableCont.append(tags.tr[thisRow])
            
        return tags.table(cellspacing="0", id="matrix")[
            tags.tr[tags.td[""], [tags.td(style="text-align: center; padding-right:0.5em; padding-left: 0.5em")[
                    tags.strong[i[1]]
                ] for i in reversed(self.groups)]],
            tableCont
        ]

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.h3["Group membership matrix for ", Settings.SMBDomain],
            tags.div(_class="hidden")[
                tags.directive('form groupForm')
            ],
            tags.form(id="groupForm", _class="nevow-form", action=url.root.child("GroupMatrix"), method="post", enctype="multipart/form-data")[
                tags.input(type="hidden", name="_charset_"),
                tags.input(type="hidden", name="__nevow_form__", value="groupForm"),
                self.matrixForm(),
                tags.input(type="submit",name="submit",value="Submit",id="groupForm-action-submit")
            ]
        ]


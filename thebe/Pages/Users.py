from enamel import authentication, deployment, pages, servers, storage, deferreds, tags
from enamel import sql, form as formal, url
import enamel
import langEn
from twisted.internet import utils
from lib import web, PageBase

class ViewDomain(PageBase.Page):
    arbitraryArguments = True

    def document(self):
        return pages.template('users-users.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["%s users." % self.arguments[0].capitalize()]]

    def render_usersTable(self, ctx, data):
        def renderUsers(users):
            return ctx.tag[
                tags.table(_class="sortable", id="TdomainTable", cellspacing="0")[
                    tags.thead(background="/images/gradMB.png")[
                        tags.tr[tags.th(colformat="istr")["User"], tags.th(colformat="istr")["Server"]]
                    ], 

                    tags.tbody(id="searchTableBody")[
                        [
                            tags.tr[
                                tags.td[
                                    tags.a(href="/ServerUsers/Edit/%s/" % user[0] )[user[1]]
                                ], 
                                tags.td[
                                    user[2]
                                ]
                            ]
                        for user in users]
                    ]
                ]
            ]
        
        return self.enamel.storage.getServerUsersByDomain(self.arguments[0], self.avatarId.gids[-1]).addBoth(renderUsers)

   

class Page(PageBase.Page):
    arbitraryArguments = False 

    def __init__(self, *a, **kw):
        pages.Standard.__init__(self, *a, **kw)
        self.text = langEn
        self.childPages = {
            'Edit' : EditPage,
            'View' : ViewDomain
        }

    def document(self):
        return pages.template('users-domains.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["User Domains"]]

    def render_domainTable(self, ctx, data):
        def renderDomains(domains):
            return ctx.tag[
                tags.table(_class="sortable", id="TdomainTable", cellspacing="0")[
                    tags.thead(background="/images/gradMB.png")[
                        tags.tr[tags.th(colformat="istr")["Domain"]]
                    ], 

                    tags.tbody(id="searchTableBody")[
                        [
                            tags.tr[tags.td[tags.a(href="View/%s/" % domain[0])[domain[0]]]]
                        for domain in domains]
                    ]
                ]
            ]
                        
        return self.enamel.storage.getGroupServerDomains(self.avatarId.gids[-1]).addBoth(renderDomains)

class EditPage(Page):
    arbitraryArguments = True
    user = None

    def document(self):
        return pages.template('users-edit.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))

    def form_user(self, data):
        def renderForm(user):
            self.user = user
            domains = ['asd.co.za']
            username = self.user[3]
            domain = self.user[2]

            u_form = formal.Form(self.submitForm)[
                formal.Group('userSettings')[
                    tags.div(_class="field")[
                        tags.label[self.text.userFormLabelEmailAddress],
                        tags.div(id="emailAd", _class="inputs")[
                            "%s@%s"% (username, domain)
                        ]   
                    ],  
                    formal.Field('uid', formal.String(required=True), label = self.text.userFormLabelUsername),
                    formal.Field('givenName', formal.String(required=True), label = self.text.userFormLabelName),
                    formal.Field('sn', formal.String(), label = self.text.userFormLabelSurname),
                    formal.Field('userPassword', formal.String(), formal.CheckedPassword, label= self.text.userFormLabelPass),
                ],  
                formal.Group('mailSettings')[

                    formal.Field('mailForwardingAddress0', formal.String(), label=self.text.userFormLabelForward),
                    formal.Field('mailForwardingAddress1', formal.String(), label=""),
                    formal.Field('mailForwardingAddress2', formal.String(), label=""),
                    formal.Field('mailForwardingAddress3', formal.String(), label=""),
                    formal.Field('mailForwardingAddress4', formal.String(), label=""),
                    formal.Field('mailForwardingAddress5', formal.String(), label=""),
                    formal.Field('mailForwardingAddress6', formal.String(), label=""),
                    formal.Field('mailForwardingAddress7', formal.String(), label=""),
                    formal.Field('mailForwardingAddress8', formal.String(), label=""),
                    formal.Field('mailForwardingAddress9', formal.String(), label=""),

                    tags.div(_class="userLine")[tags.a(href="#", onclick="addForward();")[self.text.userFormLabelAddline]],
                    formal.Field('mailAlternateAddress0', formal.String(), label=self.text.userFormLabelAlias),
                    formal.Field('mailAlternateAddress1', formal.String(), label=""),
                    formal.Field('mailAlternateAddress2', formal.String(), label=""),
                    formal.Field('mailAlternateAddress3', formal.String(), label=""),
                    formal.Field('mailAlternateAddress4', formal.String(), label=""),
                    formal.Field('mailAlternateAddress5', formal.String(), label=""),
                    formal.Field('mailAlternateAddress6', formal.String(), label=""),
                    formal.Field('mailAlternateAddress7', formal.String(), label=""),
                    formal.Field('mailAlternateAddress8', formal.String(), label=""),
                    formal.Field('mailAlternateAddress9', formal.String(), label=""),
                    tags.div(_class="userLine")[tags.a(href="#", onclick="addAlias();")[self.text.userFormLabelAddline]],
                    formal.Field('vacen', formal.Boolean(), label = self.text.userFormLabelVacationActive, description=self.text.userFormTextVacationNote),
                    formal.Field('vacation', formal.String(), formal.TextArea, label=self.text.userFormLabelVacation),
                ],
                formal.Group('userPermissions')[
                    formal.Field('employeeType', formal.Boolean(), label = self.text.userFormLabelWeb),
                    formal.Field('accountStatus', formal.Boolean(), label = self.text.userFormLabelEmail),
                    formal.Field('tumsAdmin', formal.Boolean(), label = self.text.userFormLabelAdmin),
                    formal.Field('tumsUser', formal.Sequence(formal.String()), formal.widgetFactory(formal.CheckboxMultiChoice, [(i,i) for i in domains])),
                    formal.Field('tumsReports', formal.Boolean(), label = self.text.userFormLabelReports),
             #      formal.Field('copyto', formal.String(), label = self.text.userFormLabelCopy,
             #          description = self.text.userFormTextCopy)
                ],
             #  formal.Group('userAccess')[
             #      formal.Field('vpnEnabled', formal.Boolean(), label = self.text.userFormLabelVPN,
             #          description = self.text.userFormTextVPN),
             #      formal.Field('ftpEnabled', formal.Boolean(), label = self.text.userFormLabelFTP,
             #          description = self.text.userFormTextFTP),
             #      formal.Field('ftpGlobal', formal.Boolean(), label = self.text.userFormLabelGlobalFTP,
             #          description = self.text.userFormTextGlobal)
             #  ]
            ]

            u_form.addAction(self.submitForm)

            u_form.data['userSettings.uid'] = self.user[3]
            u_form.data['userSettings.givenName'] = self.user[4]
            u_form.data['userSettings.sn'] = self.user[5]
            
            u_form.data['userPermissions.employeeType']  = "squid" in self.user[9]
            u_form.data['userPermissions.tumsUser']      = []
            u_form.data['userPermissions.accountStatus'] = "active" in self.user[10]
            u_form.data['userPermissions.tumsAdmin']     = "tumsAdmin" in self.user[9]
            u_form.data['userPermissions.tumsReports']   = "Repor" in self.user[9]

            u_form.data['mailSettings.vacen']       = self.user[20] == 1
            u_form.data['mailSettings.vacation']    = self.user[19]

            return u_form
        return self.enamel.storage.getServerUserById(int(self.arguments[0]), self.avatarId.gids).addCallback(renderForm)

    def submitForm(self, ctx, form, data):

        def returnPage(_, user):
            # Now update the client box. the user var is the new record, we need to serialise and send it
            # Flags are read only currently, so we do not need to worry about them...

            x = ""
            for k,v in user.items():
                # Ditch the sid and ID items - they will break the end parsing...
                if k == "sid" :
                    continue
                elif k == "id" :
                    continue 
                x += "%s:%s`" % (k,v)

            message = "user:%s@%s edit:%s"  % (user['name'], user['domain'], x)
            print "Update user!", message
            self.enamel.tcsClients.sendMessage(user['sid'], message)

            return url.root.child('ServerUsers').child('Edit').child(self.arguments[0])

        def formSubmit(user):
            # Ordered with record columns
            tags = [
                'id', 'sid', 'domain', 'name', 'giveName', 'sn', 'cn', 
                'uid', 'gid', 'emp', 'active', 'mail', 'mailForward', 
                'mailAlias', 'ntPass', 'password', 'lmPass', 'samSid', 
                'pgSid','vacation', 'vacEnable', 'flags'
            ]

            newDict = {}
            for n, key in enumerate(tags):
                newDict[key] = user[n]

            newDict['name'] = data['userSettings.uid'].encode()
            newDict['giveName'] = data['userSettings.givenName'].encode()
            newDict['sn'] = data['userSettings.sn'].encode()
            newDict['cn'] = "%s %s" % (data['userSettings.givenName'].encode(), data['userSettings.sn'].encode())

            emp = []
            
            if data['userPermissions.employeeType']:
                emp.append('squid')

            if data['userPermissions.tumsUser']:
                emp.append('tumsUser[%s]' % ','.join(data['userPermissions.tumsUser']))

            if data['userPermissions.accountStatus']:
                newDict['active'] = "active"
            else:
                newDict['active'] = ""
        
            if data['userPermissions.tumsAdmin']:
                emp.append('tumsAdmin')
                
            if data['userPermissions.tumsReports']:
                emp.append('tumsReports')

            newDict['emp'] = '+'.join(emp)

            newDict['vacEnable'] = str(data['mailSettings.vacen'])
            newDict['vacation'] = data['mailSettings.vacation']

            return self.enamel.storage.updateServerUser(user[1], user[0], newDict).addCallback(returnPage, newDict)

        return self.enamel.storage.getServerUserById(int(self.arguments[0]), self.avatarId.gids).addCallback(formSubmit)

    def render_content(self, ctx, data):
        uid = int(self.arguments[0])
        def renderUser(user, serv): 
            self.user = user
            return ctx.tag[
                tags.h3["Editing user %s@%s on server %s" % (user[3], user[2], serv[1])],
                web.TabSwitcher([
                    (self.text.userTabSettings, 'user-userSettings'),
                    (self.text.userTabPermissions, 'user-userPermissions'),
                    (self.text.userTabMail, 'user-mailSettings'),
                    #(self.text.userTabAccess, 'user-userAccess')
                ]),
                tags.directive('form user'),
                web.LoadTabSwitcher()
            ]

        def getUser(*a):
            return self.enamel.storage.getServerUserById(uid, self.avatarId.gids).addCallback(renderUser, *a)

        return self.enamel.storage.getServerForUser(uid).addCallback(getUser)


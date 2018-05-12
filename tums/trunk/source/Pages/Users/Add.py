from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from twisted.internet import defer

from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, LDAP, formal, ldap, os, random, sha
from Core import PageHelpers, Utils, confparse, WebUtils
import copy, time
from Pages import VPN # Import the VPN module for making certs
from Pages.Users import Base
alpha = "LLPETUMS"

class addPage(Base.Page):
    def __init__(self, avatarId=None, db=None, domain = None, *a, **ka):
        PageHelpers.DefaultPage.__init__(self, avatarId, db, *a, **ka)
        self.avatarId = avatarId
        self.domain = domain
        self.cid = None

    def childFactory(self, ctx, seg):
        if not self.domain:
            return addPage(self.avatarId, self.db, seg)

    def form_addForm(self, data):
        domains = []
        if self.avatarId.isAdmin:
            # Resolve domain list 
            for i in self.flatFil:
                thisdom = i.split('dm=')[-1].split(',')[0]
                if not thisdom in domains:
                    domains.append(thisdom)

        form = formal.Form(self.submitForm)[
            formal.Group('userSettings')[
                tags.div(_class="field")[
                    tags.label[self.text.userFormLabelEmailAddress],
                    tags.div(id="emailAd", _class="inputs")[
                        "%s@%s"% (self.cid, self.domain)
                    ]
                ],
                formal.Field('uid', formal.String(required=True, validators=Base.UserNameValidators), label = self.text.userFormLabelUsername),
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
                formal.Field('tumsUser', formal.Sequence(formal.String()), formal.widgetFactory(formal.CheckboxMultiChoice, [(i,i) for i in domains]), 
                    label = self.text.userFormLabelDomainAdmin),
                formal.Field('tumsReports', formal.Boolean(), label = self.text.userFormLabelReports),
                formal.Field('copyto', formal.String(), label = self.text.userFormLabelCopy,
                    description = self.text.userFormTextCopy)
            ],
            formal.Group('userAccess')[
                formal.Field('vpnEnabled', formal.Boolean(), label = self.text.userFormLabelVPN,
                    description = self.text.userFormTextVPN),
                formal.Field('ftpEnabled', formal.Boolean(), label = self.text.userFormLabelFTP,
                    description = self.text.userFormTextFTP),
                formal.Field('ftpGlobal', formal.Boolean(), label = self.text.userFormLabelGlobalFTP,
                    description = self.text.userFormTextGlobal)
            ]
        ]

        form.data['userPermissions.accountStatus'] = True
        form.addAction(self.submitForm)
        return form

    def submitForm(self, ctx, form, data):
        # Process LDAP commands 

        ld = LDAP.LDAPConnector(self.domain, self.sysconf)

        newRecord = ld.addUser(data)

        user = data['userSettings.uid'].encode("utf-8").lower()
        emailAddress = str("%s@%s" % (user, self.domain))

        runLater = [] # Commands to run
        defs     = [] # Deferreds to wait for 

        if data.get('userPermissions.copyto'):
            address = emailAddress
            mailConf = self.sysconf.Mail
            if mailConf.get('copys', []):
                mailConf['copys'].append((address, data['userPermissions.copyto']))
            else:
                mailConf['copys'] = [(address, data['userPermissions.copyto'])]
            self.sysconf.Mail = mailConf
            # We need to restart exim if a copyto was set
            runLater.append('/usr/local/tcs/tums/configurator --exim; /etc/init.d/exim4 restart')

        def mailOut(result):
            if result[0]:
                print "Welcome message was successfully sent to %s" % emailAddress
            else:
                print "Error sending welcome message to %s" % emailAddress

        # Send this to Thebe
        try:
            ser = WebUtils.serialiseUser(newRecord, self.domain)
            mail = "%s@%s" % (user, self.domain)
            self.handler.sendMessage(self.handler.master.hiveName, "user:%s:%s" % (mail, ser))
        except:
            print "Failed to serialise user at this time"
 
        #Create User's MailDir
        if '/var/spool/mail' in newRecord['mailMessageStore'][0]:
            runLater.append('maildirmake "%(mailDir)s" ; chown mail:mail -R "%(mailDir)s" ; chmod 2770 -R "%(mailDir)s"' % {    
                'mailDir': '/var/spool/mail/' + emailAddress
            })

        # Send a mail to the luser to enable it...
        if data.get('userPermissions.accountStatus'):
            defs.append(
                Utils.sendMail(newRecord['mail'][0],
                    newRecord['mail'],
                    'Welcome %s' % newRecord['givenName'][0],
                    self.text.userMailWelcomeMessage % newRecord['cn'][0]
                ).addBoth(mailOut)
            )

        if data.get('userAccess.vpnEnabled'):  
            vdata = {
                'name': "%s.%s" % (self.cid, self.domain),
                'mail': "%s@%s" % (user, self.domain),
                'ip':None,
                'mailKey': True
            }
            v = VPN.Page()
            v.text = self.text
            defs.append(v.newCert(None, None, vdata))

        # Create Home directory and restart NSCD
        if Settings.sambaDN and self.domain==Settings.defaultDomain:
            runLater.append('/etc/init.d/nscd restart')
            runLater.append('mkdir /home/%s; chown %s:Domain\ Users /home/%s' % (user, user, user))

        runLater.append('/usr/local/tcs/tums/configurator --ftp; /etc/init.d/vsftpd restart')

        # Execute all this crap
        for cmd in runLater:
            defs.append(WebUtils.system(cmd))

        def ReturnPage(_):
            return url.root.child('Users').child('Edit').child(self.domain).child(user)

        return defer.DeferredList(defs).addCallback(ReturnPage)
        
    def render_editContent(self, ctx, data):
        return ctx.tag[
            tags.h2[self.text.userHeadingAddUser, self.domain],
            PageHelpers.TabSwitcher([
                (self.text.userTabSettings, 'addForm-userSettings'),
                (self.text.userTabPermissions, 'addForm-userPermissions'),
                (self.text.userTabMail, 'addForm-mailSettings'),
                (self.text.userTabAccess, 'addForm-userAccess')
            ]),
            tags.directive('form addForm'),
            PageHelpers.LoadTabSwitcher()
        ]


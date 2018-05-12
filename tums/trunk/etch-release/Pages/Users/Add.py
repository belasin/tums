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

    def validateAttributes(self, data, newRecord):
        if data['userPermissions.employeeType']:
            newRecord['employeeType'].append('squid')

        if data.get('userPermissions.tumsAdmin', None):
            newRecord['employeeType'].append('tumsAdmin')

        elif data.get('userPermissions.tumsUser', None):
            tuenc = 'tumsUser[%s]' % ','.join(data['userPermissions.tumsUser'])
            newRecord['employeeType'].append(tuenc.encode())

        if data.get('userPermissions.tumsReports', None):
            newRecord['employeeType'].append('tumsReports')

        if data['userPermissions.accountStatus']:
            newRecord['accountStatus'] = [ 'active' ]

        mFA = []
        for i in xrange(10):
            if data['mailSettings.mailForwardingAddress%s' % i]:
                ad = data['mailSettings.mailForwardingAddress%s' % i].replace(' ', '').replace('\r','')
                if ad:
                    mFA.append(ad)
        if mFA:
            newRecord['mailForwardingAddress'] = [ le.encode() for le in mFA ]

        mAA = []
        for i in xrange(10):
            if data['mailSettings.mailAlternateAddress%s' % i]:
                ad = data['mailSettings.mailAlternateAddress%s' % i].replace(' ', '').replace('\r','')
                if ad:
                    mAA.append(ad)
        if mAA:
            newRecord['mailAlternateAddress'] = [ le.encode().strip('\r') for le in mAA ]

        if data['userSettings.userPassword']:
            newRecord['userPassword'] = [
                "{SHA}"+LDAP.hashPassword(data['userSettings.userPassword'].encode())
            ]
        else:
            clearPassword = sha.sha("%s%s%s" % (alpha, time.time(),random.randint(1, 4000))).hexdigest()
            newRecord['userPassword'] = ["{SHA}"+LDAP.hashPassword(clearPassword)]

    def addEntry(self, newRecord, user, accountStatus, vpnEnabled):
        def mailOut(result):
            if result[0]:
                print "Welcome message was successfully sent to %s" % newRecord['mail'][0]
            else:
                print "Error sending welcome message to %s" % newRecord['mail'][0]

        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dc = "%s,%s,o=%s" % (Settings.LDAPPeople, LDAP.domainToDC(self.domain), Settings.LDAPBase)

        # Send this to Thebe
        ser = WebUtils.serialiseUser(newRecord, self.domain) 
        mail = "%s@%s" % (user, self.domain)
        self.handler.sendMessage(self.handler.master.hiveName, "user:%s:%s" % (mail, ser))
 
        try:
            print newRecord, user, dc
            LDAP.addElement(l, 'uid=%s,%s' % (user, dc), newRecord)
        except Exception, L:
            print "Error adding element", L 
            l.unbind_s()
            return url.root.child('Users').child(self.domain).child("Error")

        #Create User's MailDir
        if '/var/spool/mail' in newRecord['mailMessageStore'][0]:
            WebUtils.system('maildirmake "%(mailDir)s" ; chown mail:mail -R "%(mailDir)s" ; chmod 2770 -R "%(mailDir)s"'
                % {'mailDir':newRecord['mailMessageStore'][0]})

        # Send a mail to the luser to enable it...
        if accountStatus:
            Utils.sendMail(newRecord['mail'][0],
                newRecord['mail'],
                'Welcome %s' % newRecord['givenName'][0],
                self.text.userMailWelcomeMessage % newRecord['cn'][0]
            ).addBoth(mailOut)

        if vpnEnabled:  
            vdata = {
                'name': "%s.%s" % (self.cid, self.domain),
                'mail': "%s@%s" % (user, self.domain),
                'ip':None,
                'mailKey': True
            }
            v = VPN.Page()
            v.text = self.text
            v.newCert(None, None, vdata)
        l.unbind_s()

    def submitForm(self, ctx, form, data):
        user = data['userSettings.uid'].encode("utf-8").lower()
        data['userSettings.uid'] = user
        emailAddress = str("%s@%s" % (user, self.domain))
        if not data['userSettings.sn']:
            data['userSettings.sn'] = "-"
        if not data['userSettings.givenName']:
            data['userSettings.givenName'] = user.capitalize()

        if data['userPermissions.copyto']:
            address = emailAddress
            mailConf = self.sysconf.Mail
            if mailConf.get('copys', []):
                mailConf['copys'].append((address, data['userPermissions.copyto']))
            else:
                mailConf['copys'] = [(address, data['userPermissions.copyto'])]
            self.sysconf.Mail = mailConf
            # We need to restart exim if a copyto was set
            WebUtils.system('/usr/local/tcs/tums/configurator --exim; /etc/init.d/exim4 restart')

        if data['userSettings.userPassword']:
            clearPassword = data['userSettings.userPassword'].encode()
        else:
            clearPassword = sha.sha("%s" % random.randint(1, 4000)).hexdigest()

        LM = Utils.createLMHash(clearPassword)
        NT = Utils.createNTHash(clearPassword)

        if Settings.sambaDN and self.domain==Settings.defaultDomain:
            # Acquire local SID
            l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
            dc = "%s,o=%s" % (LDAP.domainToDC(self.domain), Settings.LDAPBase)
            domainData =  LDAP.getDomInfo(l, dc, Settings.SMBDomain)
            
            SID = str(domainData['sambaSID'][0])


            # Acquire UID offset
            uidOffset =  int(domainData['uidNumber'][0])

            # Make RID
            SIDOffset = 2*uidOffset

            # Append user to Domain Users
            try:
                domainUsers = LDAP.getDomUsers(l, dc)
                newDomainUsers = copy.deepcopy(domainUsers)
                if not newDomainUsers.get('memberUid', None): # Very very new domain
                    newDomainUsers['memberUid'] = []
                newDomainUsers['memberUid'].append(user)
                LDAP.modifyElement(l, 'cn=Domain Users,ou=Groups,'+dc, domainUsers, newDomainUsers)
            except:
                pass # User already in group
            
            # Increment UID for domain
            newDom = copy.deepcopy(domainData)
            newDom['uidNumber'] = [str(uidOffset+1)]
            try: 
                LDAP.modifyElement(l, 'sambaDomainName=%s,%s,o=%s' % 
                    (Settings.SMBDomain, LDAP.domainToDC(self.domain), Settings.LDAPBase), domainData, newDom)
            except:
                pass # User has a uid or something
            
            
            timeNow = str(int(time.time()))
            # LDAP template for SAMBA
            shell = '/bin/false'
            if data['userAccess.ftpEnabled']:
                shell = '/bin/bash'
            newRecord = {
                'sambaPrimaryGroupSID': [SID+"-"+str(1000+SIDOffset+1)],
                'sambaSID':             [SID+"-"+str(1000+SIDOffset)],
                'gidNumber':            ['513'],
                'uidNumber':            [str(uidOffset)],
                'sambaPasswordHistory': ['0000000000000000000000000000000000000000000000000000000000000000'],
                'sambaPwdMustChange':   ['2147483647'],
                'sambaPwdCanChange':    [timeNow],
                'sambaNTPassword':      [NT],
                'sambaLMPassword':      [LM],
                'gecos':                ['System User'],
                'sn':                   [data['userSettings.sn'].encode("utf-8")],
                'givenName':            [data['userSettings.givenName'].encode("utf-8")],
                'cn':                   ["%s %s" % (data['userSettings.givenName'].encode("utf-8"), data['userSettings.sn'].encode("utf-8"))],
                'o':                    [Settings.LDAPOrganisation],
                'objectClass':          ['top', 'inetOrgPerson', 'posixAccount', 'shadowAccount',
                                         'SambaSamAccount', 'thusaUser'],
                'loginShell':           [shell],
                'sambaPwdLastSet':      [timeNow],
                'sambaAcctFlags':       ['[U          ]'],
                'mailMessageStore':     ['/var/spool/mail/' + emailAddress],
                'mail':                 [emailAddress],
                'homeDirectory':        ['/home/%s' % user],
                'uid':                  [user],
                'employeeType':         []
            }
            l.unbind_s()
        else:
            # LDAP Template for without samba
            newRecord = {
                'sn':[data['userSettings.sn'].encode("utf-8")],
                'givenName':  [data['userSettings.givenName'].encode("utf-8")],
                'cn': ["%s %s" % (data['userSettings.givenName'].encode("utf-8"), data['userSettings.sn'].encode("utf-8"))],
                'o': [Settings.LDAPOrganisation],
                'objectClass':['top', 'inetOrgPerson', 'thusaUser'],
                'mailMessageStore': ['/var/spool/mail/' + emailAddress],
                'mail': [emailAddress],
                'uid': [user],
                'employeeType': []
            }

        self.validateAttributes(data, newRecord)

        self.addEntry(newRecord, user, data['userPermissions.accountStatus'], data['userAccess.vpnEnabled'])
        
        # Create Home directory and restart NSCD
        if Settings.sambaDN and self.domain==Settings.defaultDomain:
            WebUtils.system('/etc/init.d/nscd restart')
            WebUtils.system('mkdir /home/%s; chown %s:Domain\ Users /home/%s' % (user, user, user))

        WebUtils.system('/usr/local/tcs/tums/configurator --ftp; /etc/init.d/vsftpd restart') 
        return url.root.child('Users').child('Edit').child(self.domain).child(user)
        
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


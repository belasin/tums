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
        return ctx.tag[tags.h2[self.text.users]]

    def __init__(self, avatarId=None, db=None, domain = None, *a, **ka):
        PageHelpers.DefaultPage.__init__(self, avatarId, db, *a, **ka)
        self.avatarId = avatarId
        self.db = db
        self.domain = domain
        self.cid = None
                            
    def childFactory(self, ctx, seg):
        if seg == "Edit":   
            return editPage(self.avatarId, db=self.db)
        if seg == "Groups":
            return editGroups(self.avatarId, db=self.db)
        if seg == "GroupMod":
            return editGroupsByGroup(self.avatarId, db=self.db)
        if seg == "GroupAdd":
            return addGroups(self.avatarId, db=self.db)
        if seg == "Delete":
            return deletePage(self.avatarId, db=self.db)
        if seg == "Add":
            return addPage(self.avatarId, db=self.db)
        if seg =="DomainAdd":
            return addDomain(self.avatarId, db=self.db)
        if seg =="DomainDel":
            return delDomain(self.avatarId, db=self.db)
        if seg =="Bulk":
            return bulkUsers(self.avatarId, db=self.db)
        else:
            return Page(self.avatarId, self.db, seg)
    
    def render_editContent(self, ctx, data):
        return ctx.tag[
            tags.h2[tags.img(src="/images/userman.png"), self.text.userManagement],
            tags.p[self.text.usersBeginInstruction]
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

class bulkUsers(Page):
    
    def form_addForm(self, data):
        form = formal.Form(self.submitForm)
        
        form.addField('bulkData', formal.String(), formal.TextArea, label = "", description = "Enter bulk user commands in the box above")

        form.addAction(self.submitForm)

    def submitForm(self, ctx, form, data):
        adder = addPage().submitForm # Just reuse the existing stuff
        def deler(user, domain):
            myDeleter = deletePage().locateChild
            try:
                crud = myDeleter(None, [domain, user])
                return True
            except:
                return False

        deleter = deler

        dta = data['bulkData'].encode().split('\n')

        sucessfull = []
        failed = []

        for ln in dta:
            line = ln.strip('\r').strip() # Clean it up
            fields = line.split(',')
            # Fields are as "type,uid@domain,password,name,surname,*groups
            (type, canonid, password, name, surname) = tupple(fields[:5])


class deletePage(Page):
    def locateChild(self, ctx, segments):
        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dn = "uid=%s,%s,%s,o=%s" % (segments[1], Settings.LDAPPeople, LDAP.domainToDC(segments[0]), Settings.LDAPBase)
        LDAP.deleteElement(l, dn)
        l.unbind_s()

        # Update Thebe
        self.handler.sendMessage(self.handler.master.hiveName, "deluser:%s %s:+" % (segments[1], segments[0]))

        return url.root.child('Users'), ()

def userForm():
    return [
    ]

class addPage(Page):
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
                formal.Field('tumsUser', formal.Sequence(formal.String()), formal.widgetFactory(formal.CheckboxMultiChoice, [(i,i) for i in domains])),
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
        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dc = "%s,%s,o=%s" % (Settings.LDAPPeople, LDAP.domainToDC(self.domain), Settings.LDAPBase)

        # Send this to Thebe
        ser = WebUtils.serialiseUser(newRecord, self.domain) 
        mail = "%s@%s" % (user, self.domain)
        self.handler.sendMessage(self.handler.master.hiveName, "user:%s:%s" % (mail, ser))
 
        try:
            LDAP.addElement(l, 'uid=%s,%s' % (user, dc), newRecord)
        except Exception, L:
            l.unbind_s()
            return url.root.child('Users').child(self.domain).child("Error")
        # Send a mail to the luser to enable it...
        
        if accountStatus:
            WebUtils.system("echo '"+self.text.userMailWelcomeMessage % newRecord['cn'][0]+"' | mail -s 'Welcome %s' %s" % 
                (newRecord['givenName'][0], newRecord['mail'][0])
            )

        if vpnEnabled:  
            vdata = {
                'name': "%s.%s" % (self.cid, self.domain),
                'mail': "%s@%s" % (user, self.domain),
                'ip':None,
                'mailKey': True
            }
            v = VPN.Page()
            v.newCert(None, None, vdata)
        l.unbind_s()

    def submitForm(self, ctx, form, data):
        user = data['userSettings.uid'].encode().lower()
        data['userSettings.uid'] = user
        emailAddress = "%s@%s" % (user, self.domain)
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
            if os.path.exists('/etc/debian_version'):
                WebUtils.system('/usr/local/tcs/tums/configurator --exim; /etc/init.d/exim4 restart')
            else:
                WebUtils.system('/usr/local/tcs/tums/configurator --exim; /etc/init.d/exim restart')
 
        if Settings.sambaDN and self.domain==Settings.defaultDomain:
            # Acquire local SID
            l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
            dc = "%s,o=%s" % (LDAP.domainToDC(self.domain), Settings.LDAPBase)
            domainData =  LDAP.getDomInfo(l, dc, Settings.SMBDomain)
            
            SID = str(domainData['sambaSID'][0])

            if data['userSettings.userPassword']:
                clearPassword = data['userSettings.userPassword'].encode()
            else:
                clearPassword = sha.sha("%s" % random.randint(1, 4000)).hexdigest()

            # Construct NTLM hashes. 
            (LM, NT) = tuple(os.popen(Settings.BaseDir+'/ntlmgen/ntlm.pl %s' % (clearPassword)).read().strip('\n').split())

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
                'sn':                   [data['userSettings.sn'].encode()],
                'givenName':            [data['userSettings.givenName'].encode()],
                'cn':                   ["%s %s" % (data['userSettings.givenName'].encode(), data['userSettings.sn'].encode())],
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
        else:
            # LDAP Template for without samba
            newRecord = {
                'sn':[data['userSettings.sn'].encode()],
                'givenName':  [data['userSettings.givenName'].encode()],
                'cn': ["%s %s" % (data['userSettings.givenName'].encode(), data['userSettings.sn'].encode())],
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

        if os.path.exists('/etc/debian_version'):
            WebUtils.system('/usr/local/tcs/tums/configurator --ftp; /etc/init.d/vsftpd restart') 
        l.unbind_s()
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

class addGroups(Page):
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
            WebUtils.system('smbldap-groupadd -a %s' % data['groupName'])
        
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

class delDomain(Page):
    def locateChild(self, ctx, segments):
        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dn = "%s,o=%s" % (LDAP.domainToDC(segments[0]), Settings.LDAPBase)
        tree = LDAP.searchTree(l, dn, '(objectclass=*)', [''])
        treeNods = [i[0][0] for i in tree]
        for el in reversed(treeNods):
            LDAP.deleteElement(l, el)
        l.unbind_s()
        return url.root.child('Users'), ()

class addDomain(Page):
    addSlash = True
    cid = None
    domain = None

    def form_addForm(self, data):
        form = formal.Form()
        form.addField('domainName', formal.String(), label=self.text.userFormLabelDomainName)
        form.addAction(self.submitForm)
        return form

    def submitForm(self, ctx, form, data):
        dcObject = {}
        if data['domainName']:
            l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
            dc = "o=%s" % (Settings.LDAPBase,)
            
            # Add the domain segments
            for segment in reversed(data['domainName'].split('.')):
                newRecord = {
                    'dc':           [segment.encode()],
                    'objectClass':  ['dcObject', 'domain'],
                    'o':            [Settings.LDAPOrganisation]
                }
                try:
                    dn = "dc=%s,%s" % (segment, dc)
                    dc = dn
                    LDAP.addElement(l, dc, newRecord)
                except ldap.ALREADY_EXISTS:
                    print "Existing segment <", segment, "> on dn <", dc, ">"

            # Add an OU to it..
            newRecord = {
                'ou': ['People'],
                'objectClass' : ['top', 'organizationalUnit']
            }
            try:
                #Update the ou
                LDAP.addElement(l, "ou=People, %s" % (dc, ), newRecord)
                # Read our current domains and update the configuration file
                local = self.sysconf.LocalDomains
                local.append(data['domainName'].encode())
                self.sysconf.LocalDomains = local
                # Rewrite our mailers local_domains file
                if Settings.Mailer == "exim":
                    if os.path.exists('/etc/debian_version'):
                        l = open('/etc/exim4/local_domains', 'wt')
                    else:
                        l = open('/etc/exim/local_domains', 'wt')
                else:
                    l = open('/etc/postfix/local_domains', 'wt')

                l.write('\n'.join(local))
                l.close()

                # Reload our mailer
                WebUtils.system("/etc/init.d/%s reload" % (Settings.Mailer))
            except Exception, e:
                print "Failed to add OU.. ", e
        l.unbind_s() 
        return url.root.child('Users')
            
    def render_editContent(self, ctx, data):
        if not self.avatarId.isAdmin:
            return ctx.tag[self.text.userErrorDomainPermission]
        return ctx.tag[
            tags.h3[self.text.userHeadingAddDomain],
            tags.directive('form addForm')
        ]

class editGroupsByGroup(Page):
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
            form.addField(user.replace('.','').replace('-',''), formal.Boolean(), label = user)
            form.data[user.replace('.','').replace('-','')] = LDAP.isMemberOf(l, dc, user, group=self.group)

        form.addAction(self.submitForm)
        l.unbind_s()
        return form

    def submitForm(self, ctx, form, data):
        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dc = "%s,o=%s" % (LDAP.domainToDC(self.domain), Settings.LDAPBase)
        users = [i['uid'][0] for i in LDAP.getUsers(l, "ou=People,"+dc)]

        for user in users:
            if data[user.replace('.','').replace('-','')]:
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
                                tags.td[tags.a(href=url.root.child("Users").child('GroupMod').child(self.domain).child(group[1]))[self.text.userLinkEditMembership]]
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

class editGroups(Page):
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
            if data[group[0]]:
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


class editPage(Page):
    addSlash = True
    userData = {}
    def __init__(self, avatarId=None, db=None, cid=None, domain = None, returns=None, *a, **ka):
        PageHelpers.DefaultPage.__init__(self, avatarId, db, *a, **ka)
        self.avatarId = avatarId
        self.cid = cid
        self.domain = domain
        self.returns = returns

    def form_editForm(self, data):

        domains = []
        if self.avatarId.isAdmin:
            for i in self.flatFil:
                thisdom = i.split('dm=')[-1].split(',')[0]
                if not thisdom in domains:
                    domains.append(thisdom)

        # Form population

        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dc = "%s,%s,o=%s" % (Settings.LDAPPeople, LDAP.domainToDC(self.domain), Settings.LDAPBase)
        userData =  LDAP.getUsers(l, dc, 'uid='+self.cid)
        if not userData:
            l.unbind_s()
            return "Error"

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
                formal.Field('tumsUser', formal.Sequence(formal.String()), formal.widgetFactory(formal.CheckboxMultiChoice, [(i,i) for i in domains])),
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

        form.addAction(self.submitForm)

       
        tData = copy.deepcopy(userData[0])
        tData['userSettings.uid'] = tData['uid'][0]
        tData['userSettings.givenName'] = tData.get('givenName', [""])[0]
        tData['userSettings.sn']  = tData.get('sn', [""])[0]

        if tData.get('loginShell'):
            if '/bin/bash' in tData['loginShell']:
                tData['userAccess.ftpEnabled'] = True

        if self.sysconf.FTP.get('globals'):
            if tData['uid'][0] in self.sysconf.FTP['globals']:
                tData['userAccess.ftpGlobal'] = True

        tData['userSettings.userPassword'] = '' # Strip password
        address = "%s@%s" % (tData['uid'][0], self.domain)

        for i in os.listdir('/etc/openvpn/keys/'):
            if "%s.%s" % (self.cid, self.domain) in i and "key" in i:
                tData['userAccess.vpnEnabled'] = True

        if self.sysconf.Mail.get('copys', []):
            for addr, dest in self.sysconf.Mail['copys']:
                if addr == address:
                    tData['userPermissions.copyto'] = dest

        if userData[0].get('accountStatus', False):
            tData['userPermissions.accountStatus'] = True
        else: 
            tData['userPermissions.accountStatus'] = False

        # XXX XXX 
        if userData[0].get('mailForwardingAddress', False):
            for cnt,address in enumerate(userData[0]['mailForwardingAddress']):
                tData['mailSettings.mailForwardingAddress%s' % cnt] = address

        if userData[0].get('mailAlternateAddress', False):
            for cnt,address in enumerate(userData[0]['mailAlternateAddress']):
                tData['mailSettings.mailAlternateAddress%s' % cnt] = address

        emp = userData[0].get('employeeType', [False])
        
        if 'squid' in emp:
            tData['userPermissions.employeeType'] = True
        else:
            tData['userPermissions.employeeType'] = False
    
        if 'tumsAdmin' in emp:
            tData['userPermissions.tumsAdmin'] = True
        else:
            tData['userPermissions.tumsAdmin'] = False

        if 'tumsReports' in emp:
            tData['userPermissions.tumsReports'] = True
        else:
            tData['userPermissions.tumsReports'] = False

        if emp[0]:
            for i in emp:
                if 'tumsUser[' in i:
                    tData['userPermissions.tumsUser'] = i.split('[')[-1].split(']')[0].split(',')

        try:
            vac = open("/var/spool/mail/vacation/%s@%s.txt" % (self.cid, self.domain), 'r')
            tData['mailSettings.vacation'] = vac.read()
            tData['mailSettings.vacen'] = True
        except:
            pass # No vacation note

        try:
            vac = open("/var/spool/mail/vacation/DISABLED%s@%s.txt" % (self.cid, self.domain), 'r')
            tData['mailSettings.vacation'] = vac.read()
        except:
            pass # No disabled note either.

        form.data = tData
        l.unbind_s()
        return form

    def validateFormData(self, dc, data, newRecord):
        newRecord['uid'] = [data['userSettings.uid'].encode().lower()]
        newRecord['sn'] = [data['userSettings.sn'].encode()]

        shell = '/bin/false'
        if data['userAccess.ftpEnabled']:
            shell = '/bin/bash'

        newRecord['loginShell'] = [shell]

        uid = data['userSettings.uid'].encode().lower()
        if data['userAccess.ftpGlobal']:
            ftp = self.sysconf.FTP
            if ftp.get('globals', None):
                if uid not in ftp['globals']:
                    ftp['globals'].append(uid)
            else:
                ftp['globals'] = [uid]
            
            self.sysconf.FTP = ftp
        else:
            ftp = self.sysconf.FTP
            newGlobals = []
            globals = ftp.get('globals', [])
            for id in globals:
                if id != uid:
                    newGlobals.append(id)
            ftp['globals'] = newGlobals
            self.sysconf.FTP = ftp

        if data['userSettings.givenName']:
            newRecord['givenName'] = [data['userSettings.givenName'].encode()]
        else:
            newRecord['givenName'] = [data['userSettings.uid'].encode().capitalize()]

        newRecord['cn'] =  ["%s %s" % (newRecord['givenName'][0], data['userSettings.sn'].encode())]

        newRecord['employeeType'] = []
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
        elif newRecord.get('accountStatus',False):
            del newRecord['accountStatus']

        mFA = []
        for i in xrange(10):
            if data['mailSettings.mailForwardingAddress%s' % i]:
                ad = data['mailSettings.mailForwardingAddress%s' % i].replace(' ', '').replace('\r','')
                if ad:
                    mFA.append(ad)
        if mFA:
            newRecord['mailForwardingAddress'] = [ le.encode() for le in mFA ]
        else:
            try:
                del newRecord['mailForwardingAddress']
            except:
                pass

        mAA = []
        for i in xrange(10):
            if data['mailSettings.mailAlternateAddress%s' % i]:
                ad = data['mailSettings.mailAlternateAddress%s' % i].replace(' ', '').replace('\r','')
                if ad:
                    mAA.append(ad)
        if mAA:
            newRecord['mailAlternateAddress'] = [ le.encode().strip('\r') for le in mAA ]
        else:
            try:
                del newRecord['mailAlternateAddress']
            except:
                pass

        if data['userSettings.userPassword']:
            newRecord['userPassword'] = ["{SHA}"+LDAP.hashPassword(data['userSettings.userPassword'])]
            if Settings.sambaDN and self.domain==Settings.defaultDomain:
                (LM, NT) = tuple(os.popen(Settings.BaseDir+'/ntlmgen/ntlm.pl %s' % (data['userSettings.userPassword'])).read().strip('\n').split())
                newRecord['sambaNTPassword'] = [NT]
                newRecord['sambaLMPassword'] = [LM]


    def submitForm(self, ctx, form, data):
        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dc = "%s,%s,o=%s" % (Settings.LDAPPeople, LDAP.domainToDC(self.domain), Settings.LDAPBase)
        oldRecord =  LDAP.getUsers(l, dc, 'uid='+self.cid)[0]

        newRecord = copy.deepcopy(oldRecord)
        moveUser = False
       
        try:
            self.validateFormData(dc, data, newRecord)
        except Exception, e:
            print 'Submmit on edit failed', e
            l.unbind_s()
            return url.root.child('Users').child('Edit').child(self.domain).child(self.cid).child('Failed')
        
        if newRecord['uid'][0].lower() != oldRecord['uid'][0].lower(): # Rename first
            l.rename_s('uid='+self.cid+','+dc, 'uid='+newRecord['uid'][0])
            self.cid = newRecord['uid'][0]
            newRecord['mail'] = ['%s@%s' % (newRecord['uid'][0], self.domain)]
            newRecord['mailMessageStore'] = ['/var/spool/mail/%s@%s'  % (newRecord['uid'][0], self.domain)]
            if Settings.sambaDN and self.domain==Settings.defaultDomain:
                newRecord['homeDirectory'] = ['/home/%s' % newRecord['uid'][0]]
            moveUser = True
        
        vacFiles = [  "/var/spool/mail/vacation/%s@%s.db" % (self.cid, self.domain),
                      "/var/spool/mail/vacation/%s@%s.log" % (self.cid, self.domain),
                      "/var/spool/mail/vacation/%s@%s.txt" % (self.cid, self.domain) ] 
    
        vpnCurrent = False
        for i in os.listdir('/etc/openvpn/keys/'):
            if "%s.%s" % (self.cid, self.domain) in i and "key" in i:
                vpnCurrent = True
        

        if data['userAccess.vpnEnabled'] and vpnCurrent == False:
            vdata = {
                'name': "%s.%s" % (self.cid, self.domain),
                'mail': "%s@%s" % (self.cid, self.domain),
                'ip':None,
                'mailKey':True
            }
            v = VPN.Page()
            v.newCert(None, None, vdata)
        elif not data['userAccess.vpnEnabled'] and vpnCurrent == True:
            WebUtils.system('cd /etc/openvpn/easy-rsa/; source /etc/openvpn/easy-rsa/vars; /etc/openvpn/easy-rsa/revoke-full %s; rm /etc/openvpn/keys/%s.*' % (
                "%s.%s" % (self.cid, self.domain), "%s.%s" % (self.cid, self.domain)
            ))

        address = "%s@%s" % (newRecord['uid'][0].lower(), self.domain)
        mailConf = self.sysconf.Mail
        if data['userPermissions.copyto']:
            if mailConf.get('copys', []):
                newCopys = []
                for addr, dest in mailConf['copys']:
                    if addr != address:
                        newCopys.append((addr, dest))
                newCopys.append((address, data['userPermissions.copyto']))
                mailConf['copys'] = newCopys
            else:
                mailConf['copys'] = [(address, data['userPermissions.copyto'])]
            
        else:
            if mailConf.get('copys', []):
                newCopys = []
                for addr, dest in mailConf['copys']:
                    if addr != address:
                        newCopys.append((addr, dest))
                mailConf['copys'] = newCopys 
        self.sysconf.Mail = mailConf


        if data['mailSettings.vacation']:
            # Write a vacation note.
            try: 
                if data['mailSettings.vacen']:
                    l1 = open("/var/spool/mail/vacation/%s@%s.db" % (self.cid, self.domain), 'w')
                    l2 = open("/var/spool/mail/vacation/%s@%s.log" % (self.cid, self.domain), 'w')
                    l3 = open("/var/spool/mail/vacation/%s@%s.txt" % (self.cid, self.domain), 'w')
                    l1.write('')
                    l2.write('')
                else:
                    l3 = open("/var/spool/mail/vacation/DISABLED%s@%s.txt" % (self.cid, self.domain), 'w')
                l3.write(data['mailSettings.vacation'])
                # Update permissions
                if os.path.exists('/etc/debian_version'):
                    WebUtils.system('chown www-data:root /var/spool/mail/vacation/*; chmod a+r /var/spool/mail/vacation/*')
                else:
                    WebUtils.system('chown apache:root /var/spool/mail/vacation/*; chmod a+r /var/spool/mail/vacation/*')
            except Exception, e:
                print "Error ", e, " in vacation"
                
        if not data['mailSettings.vacation'] or not data['mailSettings.vacen']: # if vacation is disabled or blank.
            for vacFile in vacFiles:
                try:
                    os.remove(vacFile)
                except:
                    pass

        # Send this to Thebe (Unless this call is Thebe invoked..)
        if self.handler:
            ser = WebUtils.serialiseUser(newRecord, self.domain) 
            mail = "%s@%s" % (self.cid, self.domain)
            self.handler.sendMessage(self.handler.master.hiveName, "user:%s:%s" % (mail, ser))
        
        # Now update LDAP tree
        try:
            l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
            LDAP.modifyElement(l, 'uid='+self.cid+','+dc, oldRecord, newRecord)
        except Exception, e:
            print e, " LDAP issue in modify"
            l.unbind_s()
            return url.root.child('Users').child('Edit').child(self.domain).child(self.cid).child('Failed')

        l.unbind_s()
        try:
            if moveUser:
                WebUtils.system('mv /var/spool/mail/%s\@%s /var/spool/mail/%s\@%s' % (
                    oldRecord['uid'][0], self.domain,
                    newRecord['uid'][0], self.domain
                ))
            if Settings.sambaDN and self.domain==Settings.defaultDomain:
                if moveUser:
                    WebUtils.system('mv /home/%s /home/%s' % (oldRecord['uid'][0], newRecord['uid'][0]))
                    WebUtils.system('mv /var/lib/samba/profiles/%s /var/lib/samba/profiles/%s' % (oldRecord['uid'][0], newRecord['uid'][0]))
                WebUtils.system('/etc/init.d/nscd restart')
                if os.path.exists('/etc/debian_version'):
                    WebUtils.system('/usr/local/tcs/tums/configurator --exim; /etc/init.d/exim4 restart')
                    WebUtils.system('/usr/local/tcs/tums/configurator --ftp; /etc/init.d/vsftpd restart')
                else:
                    WebUtils.system('/usr/local/tcs/tums/configurator --exim; /etc/init.d/exim restart')
            return url.root.child('Users').child('Edit').child(self.domain).child(self.cid).child('Completed')
        except Exception, e:
            print e, " after LDAP change in Users"
            return url.root.child('Users').child('Edit').child(self.domain).child(self.cid).child('Failed')

    def render_editContent(self, ctx, data):
        if not self.avatarId.checkDomainPermissions(self.domain):
            return ctx.tag[
                "Nice try"
            ]
        if Settings.sambaDN and self.domain==Settings.defaultDomain:
            sambaGroups = tags.a(_class="noUnderline",href=url.root.child("Users").child('Groups').child(self.domain).child(self.cid))[
                tags.img(src="/images/groupsm.png", align="absmiddle"), self.text.userLinkEditMembership
            ]
        else:
            sambaGroups = ""

        notice = ""
        if self.cid == "root" and Settings.sambaDN:
            notice = tags.strong[tags.p(style="color:#f00")[self.text.userWarningEditRoot]]
            
        if self.returns=='Completed':
            notice = tags.img(src='/images/modsuccess.png')

        return ctx.tag[
            notice, 
            tags.h3[self.text.userHeadingEditUser, self.cid],
            tags.a(_class="noUnderline", href=url.root.child('Users').child('Delete').child(str(self.domain)).child(str(self.cid)), 
                onclick="return confirm('%s');" % self.text.userConfirmDelete)[
                    tags.img(src="/images/ex-wbg.png", align="absmiddle"), self.text.userLinkDeleteUser
            ],
            sambaGroups,
            PageHelpers.TabSwitcher([
                (self.text.userTabSettings, 'editForm-userSettings'),
                (self.text.userTabPermissions, 'editForm-userPermissions'),
                (self.text.userTabMail, 'editForm-mailSettings'),
                (self.text.userTabAccess, 'editForm-userAccess')
            ]),
            tags.directive('form editForm'),
            PageHelpers.LoadTabSwitcher()
        ]

    def childFactory(self, ctx, seg):
        if not self.domain:
            return editPage(self.avatarId, self.db, None, seg)
        elif not self.cid:
            return editPage(self.avatarId, self.db, seg, self.domain)
        elif not self.returns:
            return editPage(self.avatarId, self.db, self.cid, self.domain, seg)


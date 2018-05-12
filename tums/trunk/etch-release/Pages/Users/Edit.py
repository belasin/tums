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

class editPage(Base.Page):
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
            tData['mailSettings.vacen'] = False
        except:
            pass # No disabled note either.

        form.data = tData
        l.unbind_s()
        return form

    def validateFormData(self, dc, data, newRecord):
        newRecord['uid'] = [data['userSettings.uid'].encode("utf-8").lower()]
        sn = data['userSettings.sn'] or u""
        if sn:
            newRecord['sn'] = [sn.encode("utf-8")]
        else:
            newRecord['sn'] = [" "]

        shell = '/bin/false'
        if data['userAccess.ftpEnabled']:
            shell = '/bin/bash'

        if Settings.sambaDN and self.domain==Settings.defaultDomain:
            newRecord['loginShell'] = [shell]

        uid = data['userSettings.uid'].encode("utf-8").lower()
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

        # Disable password change date
        if data.get('sambaPwdMustChange'):
            del data['sambaPwdMustChange']
        
        if data.get('sambaPwdLastSet'):
            data['sambaPwdLastSet'] = [str(int(time.time()))]

        if data['userSettings.givenName']:
            newRecord['givenName'] = [data['userSettings.givenName'].encode("utf-8")]
        else:
            newRecord['givenName'] = [data['userSettings.uid'].encode("utf-8").capitalize()]

        newRecord['cn'] =  ["%s %s" % (newRecord['givenName'][0], sn.encode("utf-8"))]

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
                newRecord['sambaLMPassword'] = Utils.createLMHash(data['userSettings.userPassword'])
                newRecord['sambaNTPassword'] = Utils.createNTHash(data['userSettings.userPassword'])

        return newRecord

    def submitForm(self, ctx, form, data):
        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dc = "%s,%s,o=%s" % (Settings.LDAPPeople, LDAP.domainToDC(self.domain), Settings.LDAPBase)
        oldRecord =  LDAP.getUsers(l, dc, 'uid='+self.cid)[0]
        
        newRecord = copy.deepcopy(oldRecord)
        l.unbind_s()

        def failed(e):
            print 'Submmit on edit failed', e
            l.unbind_s()
            return url.root.child('Users').child('Edit').child(self.domain).child(self.cid).child('Failed')
        
        def formValidated(newRecord, oldRecord):
            l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
            dc = "%s,%s,o=%s" % (Settings.LDAPPeople, LDAP.domainToDC(self.domain), Settings.LDAPBase)
            moveUser = False
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
                v.text = self.text
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
                    l3.write(data['mailSettings.vacation'].encode("utf-8"))
                    # Update permissions
                    WebUtils.system('chown www-data:root /var/spool/mail/vacation/*; chmod a+rw /var/spool/mail/vacation/*')
                except Exception, e:
                    print "Error ", e, " in vacation"
                    
            if not data['mailSettings.vacation'] or not data['mailSettings.vacen']: # if vacation is disabled or blank.
                for vacFile in vacFiles:
                    try:
                        os.remove(vacFile)
                    except:
                        pass

            if data['mailSettings.vacen']:
                try:
                    os.remove("/var/spool/mail/vacation/DISABLED%s@%s.txt" % (self.cid, self.domain))
                except:
                    pass

            # Send this to Thebe (Unless this call is Thebe invoked..)
            if self.handler:
                try:
                    ser = WebUtils.serialiseUser(newRecord, self.domain) 
                    mail = "%s@%s" % (self.cid, self.domain)
                    self.handler.sendMessage(self.handler.master.hiveName, "user:%s:%s" % (mail, ser))
                except:
                    pass

            # Check if there are any LDAP changes to worry about
            change = False
            for k,v in newRecord.items():
                if v != oldRecord.get(k, []):
                    print k,v, oldRecord.get(k, [])
                    change = True
                    break

            # Now update LDAP tree if there were changes
            if change:
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
                    WebUtils.system('/usr/local/tcs/tums/configurator --exim; /etc/init.d/exim4 restart')
                    WebUtils.system('/usr/local/tcs/tums/configurator --ftp; /etc/init.d/vsftpd restart')
                print "Complete"
                return url.root.child('Users').child('Edit').child(self.domain).child(self.cid).child('Completed')

            except Exception, e:
                print e, " after LDAP change in User"
                return url.root.child('Users').child('Edit').child(self.domain).child(self.cid).child('Failed')
        
        d = self.validateFormData(dc, data, newRecord)
        return formValidated(d, oldRecord)

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
        elif self.returns=='Failed':
            notice = tags.h1['Edit Failed!']

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


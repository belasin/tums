from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from twisted.internet import defer
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, LDAP, formal, ldap, os, random, sha
from Core import PageHelpers, Utils, confparse, WebUtils, PBXUtils
import copy, time, datetime
from Pages import VPN # Import the VPN module for making certs
from Pages import Asterisk #Need the restart capability
from Pages.Users import Base

alpha = "LLPETUMS"

def restartAsterisk():
    return WebUtils.system(Settings.BaseDir+"/configurator --debzaptel; "+Settings.BaseDir+'/configurator --pbx; /etc/init.d/asterisk reload')

class editPage(Base.Page):
    addSlash = True
    userData = {}
    def __init__(self, avatarId=None, db=None, cid=None, domain = None, returns=None, *a, **ka):
        PageHelpers.DefaultPage.__init__(self, avatarId, db, *a, **ka)
        self.avatarId = avatarId
        self.cid = cid
        self.domain = domain
        self.returns = returns

        if domain:
            self.lc = LDAP.LDAPConnector(self.domain, self.sysconf)

    def form_editForm(self, data):

        domains = []
        if self.avatarId.isAdmin:
            for i in self.flatFil:
                thisdom = i.split('dm=')[-1].split(',')[0]
                if not thisdom in domains:
                    domains.append(thisdom)

        # Form population

        userData = self.lc.getUser(self.cid)

        devList = []
        #extList = []
        rouList = []
        UserExtForm = []
        fkeyForm = [] 
        if Settings.sambaDN and self.domain==Settings.defaultDomain and PBXUtils.enabled():
            includeList = []
            includeList = self.sysconf.PBXExtensions.get(userData['uid'][0], {'extensions':[]})['extensions']
            extList = PBXUtils.getAvaExtenNumSelect(True, includeList)
            #for ext in PBXUtils.getAvailibleExtensions():
            #    extList.append((str(ext), str(ext)))
            for dev in PBXUtils.getAllAvaExtDeviceEndPoints():
                devList.append((str(dev), str(dev)))
            queueList = [(queue, queue) for queue in self.sysconf.PBX.get('queues', {}).keys()]
                
            rouList = self.sysconf.PBXRouters.keys()

            extensionWidget = formal.widgetFactory(formal.SelectChoice, options = extList)
            deviceWidget = formal.widgetFactory(formal.SelectChoice, options = devList)
            #queueWidget = formal.widgetFactory(formal.SelectChoice, options = queueList)

            userExtensions = PBXUtils.getExtensionSelect()

            
            fKeyOptions = formal.widgetFactory(formal.SelectChoice, options = userExtensions)
            fKeys = []
            maxKeys = 11
            for i in range(maxKeys):
                fKeys.append(formal.Field('fkeys%s' % i, formal.String(), fKeyOptions, label = "Key %s" % i))

            fKeys.append(formal.Field('fkeys%s'%maxKeys, formal.String(), fKeyOptions, label = "Key %s"%maxKeys, 
                description = "Select the extensions for the function keys above"))


            UserExtForm = formal.Group('userExtension')[
                formal.Field('userExtEnabled', formal.Boolean(), label = self.text.userFormLabelExtEnabled),
                formal.Field('userExtOutbound', formal.Sequence(formal.String()),
                    formal.widgetFactory(formal.CheckboxMultiChoice,
                        options=[(i,i) for i in rouList]),
                    label = self.text.userFormLabelOutbound,
                    description = self.text.userFormDescOutbound),
                formal.Field('userExtQueues', formal.Sequence(formal.String()),
                    formal.widgetFactory(formal.CheckboxMultiChoice,
                        options = queueList),
                    label = self.text.userFormLabelQueues,
                    description = self.text.userFormDescQueues),
                formal.Field('userExtCallerID', formal.String(), label = self.text.userFormLabelCallID),
                formal.Field('userExtNumber0', formal.String(), extensionWidget, label = self.text.userFormLabelExtNumber),
                formal.Field('userExtNumber1', formal.String(), extensionWidget,label = ""),
                formal.Field('userExtNumber2', formal.String(), extensionWidget,label = ""),
                formal.Field('userExtNumber3', formal.String(), extensionWidget,label = ""),
                formal.Field('userExtNumber4', formal.String(), extensionWidget,label = ""),
                formal.Field('userExtNumber5', formal.String(), extensionWidget,label = ""),
                formal.Field('userExtNumber6', formal.String(), extensionWidget,label = ""),
                formal.Field('userExtNumber7', formal.String(), extensionWidget,label = ""),
                formal.Field('userExtNumber8', formal.String(), extensionWidget,label = ""),
                formal.Field('userExtNumber9', formal.String(), extensionWidget,label = ""),
                tags.div(_class="userLine")[tags.a(href="#", onclick="addExten();")[self.text.userFormLabelAddExt]],
                formal.Field('userExtFwdUA', formal.String(), label = self.text.userFormLabelRedNoAnswer,
                    description = self.text.userFormDescRedNoAnswer),
                formal.Field('userExtDev0', formal.String(), deviceWidget,label = self.text.userFormLabelDev),
                formal.Field('userExtDev1', formal.String(), deviceWidget,label = ""),
                formal.Field('userExtDev2', formal.String(), deviceWidget,label = ""),
                formal.Field('userExtDev3', formal.String(), deviceWidget,label = ""),
                formal.Field('userExtDev4', formal.String(), deviceWidget,label = ""),
                formal.Field('userExtDev5', formal.String(), deviceWidget,label = ""),
                formal.Field('userExtDev6', formal.String(), deviceWidget,label = ""),
                formal.Field('userExtDev7', formal.String(), deviceWidget,label = ""),
                formal.Field('userExtDev8', formal.String(), deviceWidget,label = ""),
                formal.Field('userExtDev9', formal.String(), deviceWidget,label = ""),
                tags.div(_class="userLine")[tags.a(href="#", onclick="addExtDev();")[self.text.userFormLabelAddDev]],
                formal.Field('userExtVoiceMail', formal.Boolean(), label = self.text.userFormLabelVoiceMail),
                formal.Field('userExtVoiceMailPin', formal.String(), label = self.text.userFormLabelVoiceMailPin),
            ]
            fkeyForm = formal.Group('userFKeys')[fKeys]

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
                formal.Field('vacvalidity', formal.Date(), label = "Valid until", description="Disable the vacation note automatically on this date")
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
            ],
            UserExtForm,
            fkeyForm
        ]


        form.addAction(self.submitForm)

       
        tData = copy.deepcopy(userData)
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

        if userData.get('accountStatus', False):
            tData['userPermissions.accountStatus'] = True
        else: 
            tData['userPermissions.accountStatus'] = False

        if userData.get('mailForwardingAddress', False):
            for cnt,address in enumerate(userData['mailForwardingAddress']):
                tData['mailSettings.mailForwardingAddress%s' % cnt] = address

        if userData.get('mailAlternateAddress', False):
            for cnt,address in enumerate(userData['mailAlternateAddress']):
                tData['mailSettings.mailAlternateAddress%s' % cnt] = address

        emp = userData.get('employeeType', [False])
        
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

        if os.path.exists('/var/spool/mail/vacation/%s@%s.validity' % (self.cid, self.domain)):
            n = open('/var/spool/mail/vacation/%s@%s.validity'% (self.cid, self.domain)).read().strip('\n')
            d = datetime.date(*[int(i) for i in n.split('-')])
            tData['mailSettings.vacvalidity'] = d

        #Populate Userextension Data
        if PBXUtils.enabled():
            ext = self.sysconf.PBXExtensions.get(tData['uid'][0], {
                'enabled': False,
                'outbound': [],
                'callerID': "",
                'voiceMail': False,
                'voiceMailPin': '',
                'fkeys': [],
                'extensions': [],
                'devices': [],
                'queues': []
            }) 
            tData['userExtension.userExtEnabled'] = ext['enabled']
            tData['userExtension.userExtOutbound'] = ext['outbound']
            tData['userExtension.userExtQueues'] = ext.get('queues', [])
            tData['userExtension.userExtCallerID'] = ext['callerID']
            tData['userExtension.userExtVoiceMail'] = ext['voiceMail']
            tData['userExtension.userExtVoiceMailPin'] = ext['voiceMailPin']
            for i in range(0,9):
                try: 
                    tData['userExtension.userExtNumber%s'%i]=ext['extensions'][i]
                except:
                    pass
                try: 
                    tData['userExtension.userExtDev%s'%i]=ext['devices'][i]
                except:
                    pass
            for i in range(12):
                try:
                    tData['userFKeys.fkeys%s'%i] = ext['fkeys'][i]
                except:
                    pass

        form.data = tData
        return form

    def commitUserExtensions(self, form, data):
        if Settings.sambaDN and self.domain==Settings.defaultDomain and PBXUtils.enabled():
            user = data['userSettings.uid'].encode('ascii', 'replace').lower()
            ext = self.sysconf.PBXExtensions.get(user, {
                'enabled': False,
                'outbound': [],
                'callerID': "",
                'voiceMail': False,
                'voiceMailPin': '',
                'fkeys': [],
                'extensions': [],
                'devices': [],
                'queues': []
            }) 
            ext['enabled'] = data['userExtension.userExtEnabled']
            ext['outbound'] = [
                i.encode('ascii', 'replace')
                for i in data['userExtension.userExtOutbound']
            ]
            ext['queues'] = [
                i.encode('ascii', 'replace')
                for i in data['userExtension.userExtQueues']
            ]
            if data['userExtension.userExtCallerID']:
                ext['callerID'] = data['userExtension.userExtCallerID'].encode('ascii', 'replace')
            else:
                ext['callerID'] = data['userExtension.userExtNumber0'].encode('ascii', 'replace')

            oldFullCID = self.sysconf.PBXExtensions.get(user, {'fullcallerID': ""})
            ext['fullcallerID'] = """"%s" <%s>""" % (data['cn'][0].encode('ascii','replace'), ext['callerID'])
            ext['voiceMail'] = data['userExtension.userExtVoiceMail']
            if data['userExtension.userExtVoiceMailPin']:
                ext['voiceMailPin'] = data['userExtension.userExtVoiceMailPin'].encode('ascii', 'replace')
            else:
                ext['voiceMailPin'] = ''
            ext['extensions'] = []
            ext['devices'] = []
            oldDev = self.sysconf.PBXExtensions.get(user, {'devices':[]})['devices']
            for i in range(0,9):
                if data['userExtension.userExtNumber%s'%i]:
                    ext['extensions'].append(data['userExtension.userExtNumber%s'%i].encode('ascii', 'replace'))
                if data['userExtension.userExtDev%s'%i]:
                    ext['devices'].append(data['userExtension.userExtDev%s'%i].encode('ascii', 'replace'))
            restartPhone = False
            fkeys = []
            for i in range(12):
                fkeys.append(data['userFKeys.fkeys%s'%i])
            if 'fkeys' in ext:
                if ext['fkeys'] != fkeys:
                   restartPhone = True 
            ext['fkeys'] = fkeys
            

            for k, devname in enumerate(oldDev):
                if k < len(ext['devices']):
                    if devname != ext['devices'][k]:
                        restartPhone = True

            if oldFullCID != ext['fullcallerID']:
                restartPhone = True
            if restartPhone:
                for devname in ext['devices']:
                    dev = devname.split('/')
                    if dev[0] == 'Phone':
                        Asterisk.restartSnom(dev[1])

            EXT = self.sysconf.PBXExtensions
            EXT[user] = ext
            self.sysconf.PBXExtensions = EXT 
            return True

    def submitForm(self, ctx, form, data):
        oldRecord, newRecord = self.lc.modifyUser(self.cid, data)

        dc = "%s,%s,o=%s" % (Settings.LDAPPeople, LDAP.domainToDC(self.domain), Settings.LDAPBase)

        user = data['userSettings.uid'].encode('ascii', 'replace').lower()

        moveUser = False
        if user!= self.cid:
            moveUser = True
        

        vacFiles = [  "/var/spool/mail/vacation/%s@%s.db" % (user, self.domain),
                      "/var/spool/mail/vacation/%s@%s.log" % (user, self.domain),
                      "/var/spool/mail/vacation/%s@%s.txt" % (user, self.domain) ] 

        runLater = []
        
        vpnCurrent = False
        for i in os.listdir('/etc/openvpn/keys/'):
            if "%s.%s" % (user, self.domain) in i and "key" in i:
                vpnCurrent = True
        
        if data['userAccess.vpnEnabled'] and vpnCurrent == False:
            vdata = {
                'name': "%s.%s" % (user, self.domain),
                'mail': "%s@%s" % (user, self.domain),
                'ip':None,
                'mailKey':True
            }
            v = VPN.Page()
            v.text = self.text
            v.newCert(None, None, vdata)
        elif not data['userAccess.vpnEnabled'] and vpnCurrent == True:
            runLater.append('cd /etc/openvpn/easy-rsa/; source /etc/openvpn/easy-rsa/vars; /etc/openvpn/easy-rsa/revoke-full %s; rm /etc/openvpn/keys/%s.*' % (
                "%s.%s" % (user, self.domain), "%s.%s" % (user, self.domain)
            ))

        address = "%s@%s" % (user, self.domain)

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
                    l1 = open("/var/spool/mail/vacation/%s@%s.db" % (user, self.domain), 'w')
                    l2 = open("/var/spool/mail/vacation/%s@%s.log" % (user, self.domain), 'w')
                    l3 = open("/var/spool/mail/vacation/%s@%s.txt" % (user, self.domain), 'w')
                    l1.write('')
                    l2.write('')
                else:
                    l3 = open("/var/spool/mail/vacation/DISABLED%s@%s.txt" % (user, self.domain), 'w')
                l3.write(data['mailSettings.vacation'].encode("utf-8"))
                # Update permissions
                runLater.append('chown www-data:root /var/spool/mail/vacation/*; chmod a+rw /var/spool/mail/vacation/*')
            except Exception, e:
                print "Error ", e, " in vacation"
                
        if not data['mailSettings.vacation'] or not data['mailSettings.vacen']: # if vacation is disabled or blank.
            for vacFile in vacFiles:
                if os.path.exists(vacFile):
                    os.remove(vacFile)

        if data['mailSettings.vacen']:
            try:
                os.remove("/var/spool/mail/vacation/DISABLED%s@%s.txt" % (user, self.domain))
            except:
                pass

        if data['mailSettings.vacvalidity']:
            d = data['mailSettings.vacvalidity']
            n = open('/var/spool/mail/vacation/%s@%s.validity'% (self.cid, self.domain), 'wt')
            n.write(str(d))
            n.close()

        # Send this to Thebe (Unless this call is Thebe invoked..)
        if self.handler:
            try:
                ser = WebUtils.serialiseUser(newRecord, self.domain) 
                mail = "%s@%s" % (user, self.domain)
                self.handler.sendMessage(self.handler.master.hiveName, "user:%s:%s" % (mail, ser))
            except:
                pass

        if moveUser:
            runLater.append('mv /var/spool/mail/%s\@%s /var/spool/mail/%s\@%s' % (
                self.cid, self.domain,
                user, self.domain
            ))
        if Settings.sambaDN and self.domain==Settings.defaultDomain:
            if moveUser:
                runLater.append('mv /home/%s /home/%s' % (self.cid, user))
                runLater.append('mv /var/lib/samba/profiles/%s /var/lib/samba/profiles/%s' % (self.cid, user))
            runLater.append('/etc/init.d/nscd restart')
            runLater.append('/usr/local/tcs/tums/configurator --exim; /etc/init.d/exim4 restart')
            runLater.append('/usr/local/tcs/tums/configurator --ftp; /etc/init.d/vsftpd restart')

        defs = []
        #Process UserExtsions
        if self.commitUserExtensions(form, data):
            defs.append(restartAsterisk())    
        
        def ReturnPage(_):
            return url.root.child('Users').child('Edit').child(self.domain).child(user).child('Completed')


        for cmd in runLater:
            defs.append(WebUtils.system(cmd))

        return defer.DeferredList(defs).addCallback(ReturnPage)

    def render_editContent(self, ctx, data):
        if not self.avatarId.checkDomainPermissions(self.domain):
            return ctx.tag[
                "Nice try"
            ]
        if Settings.sambaDN and self.domain==Settings.defaultDomain:
            sambaGroups = tags.a(_class="noUnderline",href=url.root.child("Users").child('Groups').child(self.domain).child(self.cid))[
                tags.img(src="/images/groupsm.png", align="absmiddle"), self.text.userLinkEditMembership
            ]
            PBXTab = PBXUtils.enabled()
        else:
            sambaGroups = ""
            PBXTab = False

        notice = ""
        if self.cid == "root" and Settings.sambaDN:
            notice = tags.strong[tags.p(style="color:#f00")[self.text.userWarningEditRoot]]
            
        if self.returns=='Completed':
            notice = tags.img(src='/images/modsuccess.png')
        elif self.returns=='Failed':
            notice = tags.h1['Edit Failed!']


        tabs = [
                (self.text.userTabSettings, 'editForm-userSettings'),
                (self.text.userTabPermissions, 'editForm-userPermissions'),
                (self.text.userTabMail, 'editForm-mailSettings'),
                (self.text.userTabAccess, 'editForm-userAccess')
               ] 

        if PBXTab:
            tabs.append((self.text.userFormUserExtension, 'editForm-userExtension'))
            tabs.append((self.text.userFormUserFKeys, 'editForm-userFKeys'))

        return ctx.tag[
            notice, 
            tags.h3[self.text.userHeadingEditUser, self.cid],
            tags.a(_class="noUnderline", href=url.root.child('Users').child('Delete').child(str(self.domain)).child(str(self.cid)), 
                onclick="return confirm('%s');" % self.text.userConfirmDelete)[
                    tags.img(src="/images/ex-wbg.png", align="absmiddle"), self.text.userLinkDeleteUser
            ],
            sambaGroups,
            PageHelpers.TabSwitcher(tabs),
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


from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, formal, LDAP, copy, os
from Core import PageHelpers, AuthApacheProxy, Utils, WebUtils

class Page(PageHelpers.DefaultPage):
    addSlash = True
    docFactory  = loaders.xmlfile('ldaptree.xml', templateDir=Settings.BaseDir+'/templates')

    def __init__(self, avatarId=None, db=None, returns=None, *a, **ka):
        PageHelpers.DefaultPage.__init__(self, avatarId, db, *a, **ka)
        self.avatarId = avatarId
        self.returns = returns

    def render_treeView(self, ctx, data):
        return ctx.tag[""]

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Settings"]]

    def childFactory(self, ctx, seg):
        if not self.returns:
            return Page(self.avatarId, None, seg)

    def form_userSettings(self, ctx):
        form = formal.Form()

        form.addField('userPassword', formal.String(), formal.CheckedPassword, label="Password")
        form.addField('mailForwardingAddress', formal.String(), formal.TextArea, label="Forward mail to")
        form.addField('vacen', formal.Boolean(), label = "Vacation note active", description="Tick this to enable/disable the vacation note")
        form.addField('vacation', formal.String(), formal.TextArea, label="Vacation Note")

        form.addAction(self.submitForm)
        print self.avatarId.username, self.avatarId.domains[0]

        tData = {}
        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dc = "%s,%s,o=%s" % (Settings.LDAPPeople, LDAP.domainToDC(self.avatarId.domains[0]), Settings.LDAPBase)
        userData =  LDAP.getUsers(l, dc, 'uid='+self.avatarId.username)

        if userData[0].get('mailForwardingAddress', False):
            tData['mailForwardingAddress'] = '\n'.join(userData[0]['mailForwardingAddress'])

        try:
            vac = open("/var/spool/mail/vacation/%s@%s.txt" % (self.avatarId.username, self.avatarId.domains[0]), 'r')
            tData['vacation'] = vac.read()
            tData['vacen'] = True
        except Exception, e :
            print e, "in read vac note"
            pass # No vacation note

        try:
            vac = open("/var/spool/mail/vacation/DISABLED%s@%s.txt" % (self.avatarId.username, self.avatarId.domains[0]), 'r')
            tData['vacation'] = vac.read()
        except Exception, e:
            print e, "Vacation enabled"
            pass

        form.data = tData

        return form

    def submitForm(self, ctx, form, data):
        print data
        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dc = "%s,%s,o=%s" % (Settings.LDAPPeople, LDAP.domainToDC(self.avatarId.domains[0]), Settings.LDAPBase)
        oldRecord =  LDAP.getUsers(l, dc, 'uid='+self.avatarId.username)[0]

        newRecord = copy.deepcopy(oldRecord)

        if data['mailForwardingAddress']:
            fA = []
            for le in data['mailForwardingAddress'].split('\n'):
                ad = le.replace(' ', '').replace('\r','')
                if ad:
                    fA.append(ad)
            newRecord['mailForwardingAddress'] = [ le.encode() for le in fA ]
        elif newRecord.get('mailForwardingAddress', False):
            del newRecord['mailForwardingAddress']

        def gotNTHash(res):
            (LM, NT) = tuple(res.strip('\n').split())

            if data['userPassword']:
                newRecord['userPassword'] = ["{SHA}"+LDAP.hashPassword(data['userPassword'])]
                if Settings.sambaDN and self.avatarId.domains[0]==Settings.defaultDomain:
                    newRecord['sambaNTPassword'] = [NT]
                    newRecord['sambaLMPassword'] = [LM]

            vacFiles = [  "/var/spool/mail/vacation/%s@%s.db" % (self.avatarId.username, self.avatarId.domains[0]),
                            "/var/spool/mail/vacation/%s@%s.log" % (self.avatarId.username, self.avatarId.domains[0]),
                            "/var/spool/mail/vacation/%s@%s.txt" %  (self.avatarId.username, self.avatarId.domains[0]) ]

            if data['vacation']:
                # Write a vacation note.
                try:
                    if data['vacen']:
                        l1 = open("/var/spool/mail/vacation/%s@%s.db" % (self.avatarId.username, self.avatarId.domains[0]), 'w')
                        l2 = open("/var/spool/mail/vacation/%s@%s.log" % (self.avatarId.username, self.avatarId.domains[0]), 'w')
                        l3 = open("/var/spool/mail/vacation/%s@%s.txt" % (self.avatarId.username, self.avatarId.domains[0]), 'w')
                        l1.write('')
                        l2.write('')
                    else:
                        l3 = open("/var/spool/mail/vacation/DISABLED%s@%s.txt" % (self.avatarId.username, self.avatarId.domains[0]), 'w')
                    l3.write(data['vacation'].encode('utf-8'))
                    WebUtils.system('chown www-data:root /var/spool/mail/vacation/*; chmod a+r /var/spool/mail/vacation/*')
                        
                except Exception, e:
                    print e, " in vacation"
                    return url.root.child('Settings').child('Failed')

            if not data['vacation'] or not data['vacen']:
                for vacFile in vacFiles:
                    try:
                        os.remove(vacFile)
                    except:
                        pass

            try:
                LDAP.modifyElement(l, 'uid='+self.avatarId.username+','+dc, oldRecord, newRecord)
                if Settings.sambaDN and self.avatarId.domains[0]==Settings.defaultDomain:
                    WebUtils.system('/etc/init.d/nscd restart')
                return url.root.child('Settings').child('Completed')
            except Exception, e:
                print e, " in last mod"
                return url.root.child('Settings').child('Failed')

        return WebUtils.system(Settings.BaseDir+'/ntlmgen/ntlm.pl %s' % (data['userPassword'])).addBoth(gotNTHash)

    def render_content(self, ctx, data):
        notice = ""
        if self.returns=='Completed':
            notice = tags.img(src='/images/modsuccess.png')

        keyName = "You do not have any support files associated with your username"
        for i in os.listdir('/etc/openvpn/keys/'):
            if "%s.%s" % (self.avatarId.username, self.avatarId.dom) in i and "key" in i:
                keyName = [
                    tags.a(href='/packs/%s.%s-vpn.zip' % (
                        self.avatarId.username,
                        self.avatarId.dom
                    ))["Download Client Settings"],
                    tags.br,
                    tags.a(href='/packs/openvpn-install.exe')["Download OpenVPN Client"]
                ]

        return ctx.tag[
            tags.div(id="rightBlock")[
                tags.h3["Account Settings"],
                notice,
                tags.directive('form userSettings'),
                tags.h3["User Support Files"],
                keyName
            ]
        ]

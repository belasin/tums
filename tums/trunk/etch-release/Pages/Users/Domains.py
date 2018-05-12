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

class delDomain(Base.Page):
    def locateChild(self, ctx, segments):
        try:
            l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
            dn = "%s,o=%s" % (LDAP.domainToDC(segments[0]), Settings.LDAPBase)
            tree = LDAP.searchTree(l, dn, '(objectclass=*)', [''])
            treeNods = [i[0][0] for i in tree]
            if not treeNods:
                return url.root.child('Users').child('Failed').child('0x13'), ()
            for el in reversed(treeNods):
                LDAP.deleteElement(l, el)
            l.unbind_s()
        except:
            return url.root.child('Users').child('Failed').child('0x13'), ()

        try:
            local = self.sysconf.LocalDomains
            newlocals = []
            for i in local:
                if segments[0] != i:
                    newlocals.append(i)
            self.sysconf.LocalDomains = newlocals

        except:
            return url.root.child('Users').child('Failed').child('0x14'), ()

        return url.root.child('Users'), ()

class addDomain(Base.Page):
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
        d = None
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
            except Exception, e:
                print "Failed to add OU.. ", e
                return url.root.child('Users').child('Failed').child('0x12')

            try: 
                # Read our current domains and update the configuration file
                local = self.sysconf.LocalDomains
                local.append(data['domainName'].encode())
                self.sysconf.LocalDomains = local
                # Rewrite our mailers local_domains file
                if Settings.Mailer == "exim":
                    l = open('/etc/exim4/local_domains', 'wt')
                else:
                    l = open('/etc/postfix/local_domains', 'wt')

                l.write('\n'.join(local))
                l.close()
                
                # Reload our mailer
                d = WebUtils.system("/etc/init.d/exim4 restart")
            except Exception, e:
                print "Failed to add local domain.. ", e
                return url.root.child('Users').child('Failed').child('0x11')
        def passo(_):
            return url.root.child('Users')
        
        if d:
            return d.addBoth(passo)
        return url.root.child('Users')
            
    def render_editContent(self, ctx, data):
        if not self.avatarId.isAdmin:
            return ctx.tag[self.text.userErrorDomainPermission]
        return ctx.tag[
            tags.h3[self.text.userHeadingAddDomain],
            tags.directive('form addForm')
        ]



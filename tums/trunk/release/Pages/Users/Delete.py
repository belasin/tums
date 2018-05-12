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

class deletePage(Base.Page):
    def locateChild(self, ctx, segments):
        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dn = "uid=%s,%s,%s,o=%s" % (segments[1], Settings.LDAPPeople, LDAP.domainToDC(segments[0]), Settings.LDAPBase)
        b = "%s,o=%s" % (LDAP.domainToDC(segments[0]), Settings.LDAPBase)

        # Remove user
        LDAP.deleteElement(l, dn)

        # Remove from group memberships
        for group in LDAP.getGroups(l, b):
            if LDAP.isMemberOf(l, b, segments[1], group[1]):
                LDAP.makeNotMemberOf(l, b, segments[1], group[1])

        l.unbind_s()

        # Update Thebe
        self.handler.sendMessage(self.handler.master.hiveName, "deluser:%s %s:+" % (segments[1], segments[0]))

        return url.root.child('Users'), ()


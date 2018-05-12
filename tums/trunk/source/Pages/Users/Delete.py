from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, LDAP, formal, ldap, os, random, sha
from Core import PageHelpers, Utils, confparse, WebUtils, PBXUtils
from Pages import Asterisk
import copy, time
from Pages import VPN # Import the VPN module for making certs
from Pages.Users import Base

alpha = "LLPETUMS"

def restartAsterisk():
    return WebUtils.system(Settings.BaseDir+"/configurator --debzaptel; "+Settings.BaseDir+'/configurator --pbx; /etc/init.d/asterisk reload')

class deletePage(Base.Page):

    def cleanupPBXUser(self, username):
        def restartDevs(res):
            for dev in devs:
                Asterisk.restartSnom(dev.split("/")[-1])
 
        ext = {}
        if PBXUtils.enabled():
            ext = self.sysconf.PBXExtensions
            devs = []
            for k,i in ext.items():
                search = "ext/"+username 
                if search in i.get("fkeys", []):
                    for idx, val in enumerate(i["fkeys"]):
                        if search == val:
                           ext[k]["fkeys"][idx] = None
            if username in ext:
                devs = ext[username]["devices"]
                del ext[username]
            self.sysconf.PBXExtensions = ext
            return restartAsterisk().addBoth(restartDevs)
   
    def locateChild(self, ctx, segments):
        if segments[0]==Settings.defaultDomain:
            self.cleanupPBXUser(segments[1])

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


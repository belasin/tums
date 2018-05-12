# InfoServ
# Provides a web service for branch dispatch and other information sharing
# This service runs on port 9681 and is instantiated by tums.py
from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, twcgi
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan, compression
from nevow.taglibrary import tabbedPane
import Tree, Settings, time, os, LDAP
from Core import PageHelpers, Auth, WebUtils, confparse, Utils

class authorizedResource(rend.Page):
    def render_root(self, ctx, data):
        req = inevow.IRequest(ctx)
        host = req.client.host

        # Pull out our config - requests to here should be minimised to reduce disk thrash
        sysconf = confparse.Config()
        authority = sysconf.General.get('infoserv', {}).get('authorized',[])

        bsvr = [] # branch server container
        for k in sysconf.Mail.get('branches', []):
            if isinstance(k, list):
                bsvr.append(k[0])
            else:
                bsvr.append(k)
        authority.extend(bsvr)

        if host in authority:
            return ctx.tag[self.allowed(host)]
        else:
            return ctx.tag[self.denied(host)]

    def allowed(self, host):
        return "Not implemented"

    def denied(self, host):
        return "Access Denied"

    docFactory = loaders.stan(
        tags.invisible(render=tags.directive('root'))
    )

class handlesMailFor(authorizedResource):
    def allowed(self, host):
        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dc = "o=%s" % (Settings.LDAPBase)
        
        # Hammer it a bit 
        d, v = 0, None
        while (not v and d < 3):
            v = LDAP.searchTree(l, dc, 'uid=*', [])
            d += 1

        
        addrs = []

        for i in v:
            path, detail = i[0]
            if "ou=People" not in path:
                continue

            if "uid=root," in path:
                # Ignore the root user
                continue
            
            if 'active' in detail.get('accountStatus', []):
                # Active user
                addr = detail['mail'][0]
                alts = detail.get('mailAlternateAddress', [])
                if addr not in addrs:
                    addrs.append(addr)
                for mail in alts:
                    if mail not in addrs:
                        addrs.append(mail)
        return "\n".join(addrs)

class rootResource(authorizedResource):
    child_handlesMailFor = handlesMailFor

    def allowed(self, host):
        return "Vulani InfoServ.\n Your host (%s) is authorized" % (host)
        
def deploy():
    siteRoot = rootResource()
    site = appserver.NevowSite(siteRoot)

    return site


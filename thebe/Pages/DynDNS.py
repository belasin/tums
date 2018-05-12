from enamel import authentication, deployment, pages, deferreds, tags
from nevow import rend, inevow
from twisted.internet import utils
from twisted.web import http

from LdapDNS import DNS
from lib import system, PageBase

import enamel, sha, os

class Updater(PageBase.Page):
    addSlash = False
    dns = DNS.DNS('o=THUSA', 'thusa')
    def updateDNS(self, username, ip):
        # Do DNS Updaty stuff
        print username, ip
        
        data = self.dns.getDNSRecord("%s.thusadns.com" % username)
        if data:
            oldip = data[1]['aRecord'][0]
            print oldip
            self.dns.deleteDomain("%s.thusadns.com" % username)

        self.dns.addDNSRecord("%s.thusadns.com" % username, 'A', ip)
        self.dns.addDNSRecord("%s.thusadns.com" % username, 'TTL', '60')

    def document(self, *a):
        pass

    def renderHTTP(self, ctx):
        request = inevow.IRequest(ctx)

        username, password = request.getUser(), request.getPassword()
        
        self.enamel.ldapAuthDn = "cn=Manager, o=THUSA"
        self.enamel.ldapAuthUrl = "ldap://dyndnsauth.vulani.net:389/ou=People,dc=thusadns,dc=com,o=THUSA?uid?sub?"
        self.enamel.ldapBindPassword = "thusa"

        if username and password:
            L = authentication.LDAPAuthenticator(self.enamel)
            print username, password
            result = L.authLDAP(username, password)
            nresult = L.handleAuthenticationResult(result, username, password)
        else:
            # Insufficient creds..
            nresult = False 

        if nresult and password:
            self.updateDNS(username, request.args['myip'][0])
            return "good %s" % (request.args['myip'][0])
        else:
            request.setHeader('WWW-Authenticate', 'Basic realm="topsecret"')
            request.setResponseCode(http.UNAUTHORIZED)
            return "Authentication required."

class Page(pages.Standard):
    childPages = {
        'update':Updater
    }

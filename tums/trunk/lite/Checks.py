from Core import WebUtils
import LDAP, Settings
from twisted.internet import task, reactor
import os, cPickle

class SelfChecker(object):
    checkers = [
        (60*60, 'profiles'),
        (12*60*60, 'updates'),
        (60*60, 'users'),
    ]

    def __init__(self, handler):
        self.loops = {}
        self.handler = handler

    def check_users(self):
        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dc = "o=%s" % (Settings.LDAPBase)

        d, v = 0, None
        while (not v and d < 3):
            v = LDAP.searchTree(l, dc, 'uid=*', [])
            d += 1

        # Get the count of useful entries to pass with burst header
        num = 0
        for i in v:
            path, detail = i[0]
            if "ou=People" in path:
                num += 1

        print "New burst"
        def Burst(_):
            print "Burst start", _
            for i in v:
                path, detail = i[0]
                if "ou=People" not in path:
                    continue
                dom = path.split(',o=')[0].split('ou=People,dc=')[-1].replace(',dc=', '.')

                x = WebUtils.serialiseUser(detail, dom)
                    
                # create a mail resource locator
                mail = "%s@%s" % (detail['uid'][0], dom)
                print "User check:", mail
                self.handler.sendMessage(self.handler.master.hiveName, "user:%s:%s" % (mail, x))

            # soften this
            reactor.callLater(2, self.handler.sendMessage, self.handler.master.hiveName, "usernoburst:+:+")

        d = self.handler.callRemote(self.handler.master.hiveName, "userburst:%s:+" % num)
        return d.addCallback(Burst)

    def check_updates(self):
        def sendPackageNames(names):
            for name in names.replace('\n', ' ').split():
                self.handler.sendMessage(self.handler.master.hiveName, 
                    "newupdate:%s:--" % (name))
        
        if os.path.exists('/etc/debian_version'):
            r = WebUtils.system(
                'debsecan --only-fixed --suite etch --format packages'
            )
        else:
            r = WebUtils.system(
                'glsa-check -ln affected 2>&1 | grep "......-.. \[N\]" | sed \'s/.*N\\] \\(.*\\):.*/\\1/\''
            )

        return r.addCallback(sendPackageNames)


    def check_profiles(self):
        # Sends our current profiles to the server ever few hours...
        params  = "CompanyName ExternalName Hostname Domain SambaDomain LDAPBase LDAPPassword LANPrimary WANPrimary "
        params += "ThusaDNSUsername ThusaDNSPassword ThusaDNSAddress NTP SMTPRelay GentooRsync OverlayRsync LocalRoute "
        params += "EthernetDevices WANDevices Shorewall SambaConfig SambaShares ProxyConfig Mail Shaping DHCP Failover Tunnel BGP FTP RADIUS "
        params += "ForwardingNameservers TCSAliases LocalDomains GentooMirrors ShorewallBalance ShorewallSourceRoutes "
        params += "ProxyAllowedHosts ProxyAllowedDestinations ProxyAllowedDomains ProxyBlockedDomains ShaperRules"

        paramL = params.split()

        for conf in os.listdir('profiles'):
            if conf[-3:] == ".py":
                l = open('profiles/' + conf).read()

                exec l
                confDict = {}
                myLocals = locals()
                for i in paramL:
                    confDict[i] = myLocals[i]

                pickle = cPickle.dumps(confDict)
                self.handler.sendMessage(self.handler.master.hiveName, "config:%s:%s" % (conf[:-3],pickle))

    def startCheckers(self):
        for checkDelay, checker in self.checkers:
            fn = getattr(self, 'check_%s' % checker)
            self.loops[checker] = task.LoopingCall(fn)
            self.loops[checker].start(checkDelay, now=True)


import os, config, pprint, StringIO
from Core import Utils, confparse
import socket, struct

class Plugin(object):
    parameterHook = "--upgrade"
    parameterDescription = "Upgrades a config file to the latest format"
    parameterArgs = ""
    autoRun = False
    configFiles = []

    def reloadServices(self):
        pass

    def checkType(self, vals, typet, typename, typeempty):
        newConf = ""
        for st in vals.split():
            try:
                val = getattr(config, st)
                # Make sure it's a string
                if type(val) != typet:
                    print "Configuration Error: %s must be a %s!" % (st, typename)
                s = StringIO.StringIO()
                pprint.pprint(val, stream = s)
                s.seek(0)
                newConf += "%s = %s\n" % (st, s.read())
            except:
                # Doesn't exist
                newConf += "%s = %s\n" % (st, repr(typeempty))
        return newConf

    def writeConfig(self, *a):
        Strings = "CompanyName ExternalName Hostname Domain SambaDomain LDAPBase LDAPPassword LANPrimary WANPrimary "
        Strings += "ThusaDNSUsername ThusaDNSPassword ThusaDNSAddress NTP SMTPRelay GentooRsync OverlayRsync LocalRoute"
        Dicts = "EthernetDevices WANDevices Shorewall SambaConfig SambaShares ProxyConfig Mail Shaping DHCP Failover Tunnel BGP FTP RADIUS"
        Lists = "ForwardingNameservers TCSAliases LocalDomains GentooMirrors ShorewallBalance ShorewallSourceRoutes"
        Lists += " ProxyAllowedHosts ProxyAllowedDestinations ProxyAllowedDomains ProxyBlockedDomains ShaperRules"

        newConf = self.checkType(Strings, str, "string (\"\")", "")
        newConf += self.checkType(Lists, list, "list ([])", [])
        newConf += self.checkType(Dicts, dict, "dictionary ({})", {})
        
        conf=newConf

        # Rewrite the config file (format will be nasty)
        l = open('/usr/local/tcs/tums/config.py', 'wt')
        #l = open('config.py', 'wt')
        l.write(conf)
        l.close()


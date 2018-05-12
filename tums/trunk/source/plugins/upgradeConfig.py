import os, config, pprint, StringIO
from Core import Utils, confparse
import socket, struct

class Plugin(object):
    parameterHook = "--upgradeconfig"
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
                # Make sure it's a whatever
                if (typet == list) and isinstance(val, str):
                    val = [val]
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

    def thisUpgrade(self):
        return 

    def writeConfig(self, *a):
        Strings = "CompanyName ExternalName Hostname Domain SambaDomain LDAPBase LDAPPassword WANPrimary "
        Strings += "ThusaDNSUsername ThusaDNSPassword ThusaDNSAddress NTP SMTPRelay LocalRoute"
        Dicts = "EthernetDevices WANDevices Shorewall SambaConfig SambaShares ProxyConfig Mail Shaping DHCP Failover Tunnel BGP FTP RADIUS General"
        Lists = "LANPrimary ForwardingNameservers TCSAliases LocalDomains ShorewallBalance ShorewallSourceRoutes"
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

        os.system('cat /usr/local/tcs/tums/runningProfile | xargs --replace=% cp /usr/local/tcs/tums/config.py /usr/local/tcs/tums/profiles/%')
        self.thisUpgrade()

        # Permissions checks
        os.system('chmod a+x /usr/local/tcs/tums/syscripts/*')

        # Ditch stupid logrotate files
        os.system('rm /etc/logrotate.d/*.ucf-dist >/dev/null 2>&1')

        # Update our cron script
        os.system('/usr/local/tcs/tums/configurator -f /etc/cron.d/tums')

        # patches to configuration file
        c = confparse.Config()
        g = c.General
        if not g.get('diskalert', None):
            g['diskalert'] = {
                '/': 90,
                '/var': 90,
            }

        c.General = g

        try:
            lp = c.LANPrimary
            if not isinstance(lp, list):
                c.LANPrimary = [lp]
            else:
                lp = lp[0]

        except:
            pass

        eth = c.EthernetDevices
        if not eth[lp].get('dhcpserver'):
            # Never assume that we should auto turn on DHCP
            eth[lp]['dhcpserver'] = False
            c.EthernetDevices = eth
    
        # Write our special proxy errors
        os.system('cp -a /usr/local/tcs/tums/packages/squid/* /usr/share/squid/errors/English/')
        os.system('chmod a+r /usr/share/squid/errors/English/*')

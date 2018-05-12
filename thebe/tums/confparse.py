""" Module for get/set interaction with TUMS configuration files
"""

import pprint, StringIO
class SetDefaults:
    BaseDir = '/usr/local/tcs/tums'
try:
    import Settings
except:
    Settings = SetDefaults()

class uselessDatatype(object):
    def __getattr__(self, *a):
        return None

def configDict(conf):
    return [
        ('CompanyName',                 conf.CompanyName),
        ('ExternalName',                conf.ExternalName),
        ('Hostname',                    conf.Hostname),
        ('Domain',                      conf.Domain),
        ('SambaDomain',                 conf.SambaDomain),
        ('LDAPBase',                    conf.LDAPBase),
        ('LDAPPassword',                conf.LDAPPassword),
        ('EthernetDevices',             conf.EthernetDevices),
        ('LANPrimary',                  conf.LANPrimary),
        ('WANDevices',                  conf.WANDevices),
        ('WANPrimary',                  conf.WANPrimary),
        ('ThusaDNSUsername',            conf.ThusaDNSUsername),
        ('ThusaDNSPassword',            conf.ThusaDNSPassword),
        ('ThusaDNSAddress',             conf.ThusaDNSAddress),
        ('ForwardingNameservers',       conf.ForwardingNameservers),
        ('TCSAliases',                  conf.TCSAliases),
        ('NTP',                         conf.NTP),
        ('SMTPRelay',                   conf.SMTPRelay),
        ('LocalDomains',                conf.LocalDomains),
        ('GentooMirrors',               conf.GentooMirrors),
        ('GentooRsync',                 conf.GentooRsync),
        ('OverlayRsync',                conf.OverlayRsync),
        ('Shorewall',                   conf.Shorewall),
        ('ShorewallBalance',            conf.ShorewallBalance),
        ('ShorewallSourceRoutes',       conf.ShorewallSourceRoutes),
        ('SambaConfig' ,                conf.SambaConfig),
        ('SambaShares' ,                conf.SambaShares),
        ('ProxyConfig' ,                conf.ProxyConfig),
        ('ProxyAllowedHosts',           conf.ProxyAllowedHosts),
        ('ProxyAllowedDestinations' ,   conf.ProxyAllowedDestinations),
        ('ProxyAllowedDomains',         conf.ProxyAllowedDomains),
        ('ProxyBlockedDomains',         conf.ProxyBlockedDomains),
        ('Mail' ,                       conf.Mail),
        ('Shaping',                     conf.Shaping),
        ('ShaperRules',                 conf.ShaperRules),
        ('DHCP',                        conf.DHCP),
        ('LocalRoute',                  conf.LocalRoute),
        ('Failover',                    conf.Failover),
        ('Tunnel',                      conf.Tunnel),
        ('BGP',                         conf.BGP),
    ]

class Config:
    values = [ i[0] for i in configDict(uselessDatatype())]
    def __init__(self, file)
        cfi = Settings.BaseDir+'/configs/'+file

    def __getattr__(self, name):
        if name in self.values:
            cfo = open(self.cfi, 'rt')
            exec cfo
            return locals()[name]
        else:
            raise AttributeError, name

    def __setattr__(self, name, value):
        if name in self.values:
            conf = __import__('config')
            conf.__setattr__(name, value)
            self.rewriteConfig(conf)
        else:
            raise AttributeError, name

    def rewriteConfig(self, conf):
        confurator = dict(configDict(conf))

        l = open(self.cfi, 'wt')
        conf = ""
        for key in self.values:
            s = StringIO.StringIO()
            pprint.pprint(confurator[key], stream = s)
            s.seek(0)
            lo = '%s = %s\n' % (key, s.read())
            conf+=lo

        l.write(conf)
        l.close()


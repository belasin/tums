#!/usr/bin/python
import pprint, StringIO
import os, time
class SetDefaults:
    BaseDir = '/usr/local/tcs/tums'
try:
    import Settings
except:
    Settings = SetDefaults()

class uselessDatatype(object):
    def __getattr__(self, *a):
        return None

class Config(object):
    validKeys = [
        'CompanyName',   
        'ExternalName', 
        'Hostname',    
        'Domain',     
        'SambaDomain',
        'LDAPBase', 
        'LDAPPassword', 
        'EthernetDevices',
        'LANPrimary',
        'WANDevices',
        'WANPrimary',
        'ThusaDNSUsername',
        'ThusaDNSPassword', 
        'ThusaDNSAddress',  
        'ForwardingNameservers',
        'TCSAliases',
        'NTP',  
        'SMTPRelay',
        'LocalDomains',
        'Shorewall',
        'ShorewallBalance', 
        'ShorewallSourceRoutes',
        'SambaConfig', 
        'SambaShares', 
        'ProxyConfig', 
        'ProxyAllowedHosts',
        'ProxyAllowedDestinations',
        'ProxyAllowedDomains',
        'ProxyBlockedDomains',
        'Mail',
        'Shaping',
        'ShaperRules',
        'DHCP', 
        'LocalRoute',
        'Failover', 
        'Tunnel',
        'BGP',
        'FTP',
        'RADIUS',
        'General',
        'Backup',
        'PBX',
        'PBXHardware',
        'PBXVoip',
        'PBXProviders',
        'PBXExtensions',
    ]

    def __init__(self):
        profileLocator = open(os.path.join(Settings.BaseDir, 'currentProfile'))
        profileName = profileLocator.read().replace('\n', '').strip()
        self.profileName = profileName
        self.configFile = os.path.join(Settings.BaseDir, 'profiles', profileName)

        self.cache = {}
        self.cacheAge = 0
        self.maxAge = 300

    def checkProfile(self):
        profileLocator = open(os.path.join(Settings.BaseDir, 'currentProfile'))
        profileName = profileLocator.read().replace('\n', '').strip()
        if self.profileName != profileName:
            self.profileName = profileName
            self.configFile = os.path.join(Settings.BaseDir, 'profiles', profileName)
            self.cacheAge += 9000

    def __getattr__(self, name):
        if name in self.validKeys:
            self.checkProfile()
            configAge = os.stat(self.configFile).st_mtime
            now = time.time()
            
            #Setup conditions
            stillValid = self.cacheAge == configAge
            tooOld = (now - self.cacheAge) > self.maxAge

            if self.cache and stillValid and not tooOld:
                return self.cache[name]

            # Read the file (full unbuffered)
            cfo = open(self.configFile, 'rt')
            self.cacheAge = os.stat(self.configFile).st_mtime
            data = cfo.read()
            cfo.close()

            d = {}
            exec data in d

            self.cache = d
    
            return d.get(name, {})

    def __setattr__(self, name, value):
        if name in self.validKeys:
            self.checkProfile()
            cfo = open(self.configFile, 'rt')
            data = cfo.read()
            cfo.close()

            conf = {}
            exec data in conf

            conf[name] = value

            self.rewriteConfig(conf)
        else:
            object.__setattr__(self, name, value)

    def rewriteConfig(self, confdata):
        l = open(self.configFile, 'wt')
        conf = ""
        for key in self.validKeys:
            s = StringIO.StringIO()
            pprint.pprint(confdata.get(key, {}), stream = s)
            s.seek(0)
            lo = '%s = %s\n' % (key, s.read())
            conf+=lo

        l.write(conf)
        l.close()


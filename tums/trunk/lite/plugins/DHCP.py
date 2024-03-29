import config, os
from Core import Utils

class Plugin(object):
    parameterHook = "--dhcp"
    parameterDescription = "Reconfigure DHCP"
    parameterArgs = ""
    autoRun = True
    configFiles = [ 
        "/etc/dhcp/dhcpd.conf"
    ]

    def reloadServices(self):
        os.system('/etc/init.d/dhcpd restart')

    def writeConfig(self, *a):
        myIp = config.EthernetDevices[config.LANPrimary]['ip'].split('/')[0]
        myNetmask = Utils.cidr2netmask(config.EthernetDevices[config.LANPrimary]['ip'].split('/')[1])
        rev = '.'.join([i for i in reversed(myIp.split('.')[:3])])
        statics = ""
        for ip, hostmac in config.DHCP.get('leases',{}).items():
            host, mac = hostmac
            statics += """    host %s {
        fixed-address %s;
        hardware ethernet %s;
    }\n""" % (host, ip, mac)
        # allow custom configuration options
        custom = ""
        extramain = ""

        rangeStart  = config.DHCP.get('rangeStart', "100")
        rangeEnd    = config.DHCP.get('rangeEnd', "220")
        netmask     = config.DHCP.get('netmask', myNetmask)
        netbios     = config.DHCP.get('netbios', myIp)
        nameserver  = config.DHCP.get('nameserver', myIp)
        router      = config.DHCP.get('gateway', myIp)
        myNet       = config.DHCP.get('network', '.'.join(myIp.split('.')[:3]) + ".0")

        if config.DHCP.get('custom', None):
            custom = config.DHCP['custom']
        if config.DHCP.get('main', None):
            extramain = config.DHCP['main']

        sharenets = ""
        if config.DHCP.get('sharenets', False):
            for i, defin in config.DHCP['sharenets'].items():
                network = config.EthernetDevices[i]['network'].split('/')[0]
                cidr = config.EthernetDevices[i]['network'].split('/')[1]
                opts = {
                    'network': '.'.join(network.split('.')[:3]),
                    'domain': defin['domain'],
                    'netmask': Utils.cidr2netmask(cidr),
                    'ip': config.EthernetDevices[i]['ip'].split('/')[0],
                    'netname': i.upper()
                }
                sharenets += """\nshared-network NET_%(netname)s {
  option domain-name "%(domain)s";
  subnet %(network)s.0 netmask %(netmask)s {
    range %(network)s.10 %(network)s.253;
    option routers %(ip)s;
    option domain-name-servers %(ip)s;\n  }\n}\n\n""" % opts

        defn = {
            'myIp': myIp,
            'rev': rev,
            'domain': config.Domain,
            'network': '.'.join(myNet.split('.')[:3]),
            'static': statics,
            'custom': custom,
            'netmask': netmask,
            'rangeStart': rangeStart,
            'rangeEnd': rangeEnd,
            'myNetbios': netbios,
            'myDns': nameserver,
            'myRouter': router,
            'sharenets': sharenets,
            'extramain': extramain,
            'ldapbase': config.LDAPBase,
        }
        dhcpconf = """# DHCPD config generated by TUMS Configurator
ddns-update-style interim;
default-lease-time 600;
max-lease-time 7200;
allow booting;
allow bootp;
authoritative;
log-facility local7;

zone %(domain)s. {
    primary 127.0.0.1;
}

zone %(rev)s.in-addr.arpa. {
    primary 127.0.0.1;
}

%(extramain)s

shared-network %(ldapbase)s {
    use-host-decl-names           on;
    option domain-name            "%(domain)s";
    option domain-name-servers    %(myDns)s;

    option netbios-name-servers   %(myNetbios)s;
    option netbios-node-type      8;

    option ntp-servers            %(myIp)s;
    option time-servers           %(myIp)s;
    option log-servers            %(myIp)s;
    option font-servers           %(myIp)s;
    option pop-server             %(myIp)s;
    option smtp-server            %(myIp)s;
    option x-display-manager      %(myIp)s;

    subnet %(network)s.0 netmask %(netmask)s {
        range dynamic-bootp           %(network)s.%(rangeStart)s %(network)s.%(rangeEnd)s;
        option subnet-mask            %(netmask)s;
        option broadcast-address      %(network)s.255;
        option routers                %(myRouter)s;
    }
%(static)s
%(custom)s
}
%(sharenets)s
""" % defn
        
        # Check for debianism (goes in /etc/dhcp3)
        if os.path.exists('/etc/debian_version'):
            f = open('/etc/dhcp3/dhcpd.conf', 'wt')
        else: 
            f = open('/etc/dhcp/dhcpd.conf','wt')
        f.write(dhcpconf)
        f.close()


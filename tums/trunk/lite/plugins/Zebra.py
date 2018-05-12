import config, os
from Core import Utils

class Plugin(object):
    parameterHook = "--quagga"
    parameterDescription = "Reconfigure Routing Daemon"
    parameterArgs = ""
    autoRun = True
    configFiles = [ 
        "/etc/quagga/zebra.conf"
        "/etc/quagga/bgpd.conf"
        "/etc/quagga/daemons"
    ]

    def reloadServices(self):
        if os.path.exists('/etc/debian_version'):
            # debian uses a whole system jobbie 
            os.system('/etc/init.d/quagga restart')
        else:
            # gentoo separates them into different ones 
            os.system('/etc/init.d/zebra restart')
            os.system('/etc/init.d/bgpd restart')

    def writeConfig(self, *a):
        routes = "! -*- Automaticaly created by TUMS Configurator -*-\n"
        routes += "hostname %s\npassword %s\nenable password %s\n" % (
            config.Hostname,
            config.LDAPPassword,
            config.LDAPPassword
        )
        bgp = routes # copy it over for BGP config too :)
        ifaceConfig = ""
        for interface, defin in config.EthernetDevices.items():
            # check routes - add to Zebra if not a default
            if defin.get('routes', None):
                for dest, gw in defin['routes']:
                    if dest!='default':
                        routes += '  ip route %s  %s\n' % (dest, gw)

            if defin.get('ipv6', None):
                ifaceConfig += '\ninterface %s\n' % interface
                ifaceConfig += '  no ipv6 nd suppress-ra\n'
                ifaceConfig += '  ipv6 nd prefix %s\n\n'  % Utils.getV6Network(defin['ipv6'])

        routes += '\n'
        
        try:
            if config.LocalRoute:
                lp = open('/usr/local/tcs/tums/configs/local_routes')
                for l in lp:
                    ln = l.strip('\n').strip()
                    if ln:                    
                        if not "/" in ln:
                            ln += "/32"
                        routes += "ip route %s %s\n" % (ln, config.LocalRoute)
        except:
            print "No local-only routing"

        zebra = open('/etc/quagga/zebra.conf', 'wt')
        zebra.write(routes)
        zebra.write(ifaceConfig)
        zebra.close()

        for asn, conf in config.BGP.items():
            bgp += "router bgp %s\n" % asn
            bgp += "  bgp router-id %s\n" % conf['router-id']
            for net in conf.get('networks', []):
                bgp += "  network %s\n" % net

            for neigh, nconf in conf.get('neighbors', {}).items():
                # BGP remote-as is either our AS or it's our AS (odd default but handy)
                bgp += "  neighbor %s   remote-as  %s\n" % (neigh, nconf.get('as', asn))

            bgp += '\n'

        bgpconf = open('/etc/quagga/bgpd.conf', 'wt')
        bgpconf.write(bgp)
        bgpconf.close()

        # Write startup daemons file (only used by Debian, doesn't hurt to write it anyway)
        daemons = open('/etc/quagga/daemons', 'wt')
        # enabled
        daemons.write("zebra=yes\n")
        daemons.write("bgpd=yes\n")
        # disabled
        daemons.write("ospfd=no\nospf6d=no\nripd=no\nripngd=no\nisisd=no\n")
        daemons.close()



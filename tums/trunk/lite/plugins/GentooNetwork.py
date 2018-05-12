import config, os
from Core import Utils

class Plugin(object):
    parameterHook = "--net"
    parameterDescription = "Reconfigure Gentoo network"
    parameterArgs = ""
    autoRun = True
    required = "gentoo"
    configFiles = [ 
        "/etc/conf.d/net",
    ]

    def reloadServices(self):

        for inter in config.EthernetDevices:
            os.system('/etc/init.d/net.%s restart' % inter)

        for inter in config.WANDevices:
            os.system('/etc/init.d/net.%s restart' % inter)

    def writeConfig(self, *a):
        # conf.d/net
        net = "\n"
        routes = ""
        vlanIfaces = {}
        dhcpIfaces = []
        for interface, defin in config.EthernetDevices.items():
            if interface!="extra":
                net += 'config_%s=(\n' % interface 
                if config.EthernetDevices[interface]['type'].lower() == 'dhcp':
                    net += '    "dhcp"\n'
                if config.EthernetDevices[interface]['type'].lower() == 'manual':
                    net += ' '
                else:
                    net += '    "%s"\n' % (config.EthernetDevices[interface]['ip'])

                if config.EthernetDevices[interface].get('aliases',None):
                    for addr in config.EthernetDevices[interface]['aliases']:
                        net+= '    "%s"\n' % (addr)

                if defin.get('extra', None):
                    net += defin['extra']

                net += ')\n\n'

                if "vlan" in interface:
                    if defin.get('interface', False):
                        if defin['interface'] in vlanIfaces:
                            vlanIfaces[defin['interface']].append(interface.strip('vlan'))
                        else:
                            vlanIfaces[defin['interface']] = [interface.strip('vlan')]

                routes += 'routes_%s=(\n' % interface
                for ro in config.EthernetDevices[interface].get('routes', []):
                    routes += '    "%s via %s"\n' % ro
                routes += ')\n'

                if interface == config.LANPrimary or defin.get('dhcpserver', False):
                    dhcpIfaces.append(interface)

        confddhcp = "DHCPD_IFACE=\"%s\"\n" % ' '.join(dhcpIfaces)
        cdd = open('/etc/conf.d/dhcpd', 'wt')
        cdd.write(confddhcp)
        cdd.close()

        # config tunnel
        cont = []
        l = open('/etc/conf.d/local.start')
        for i in l:
            if i.strip() and not "# TUN" in i:
                cont.append(i)

        l.close()

        if config.Tunnel.get('ipv6', False):
            remote = config.Tunnel['ipv6']['remoteip']
            local = config.Tunnel['ipv6']['localip']
            localv6 = config.Tunnel['ipv6']['localv6']

            cont.append('ip tunnel add ipv6tun mode sit remote %s local %s ttl 255 # TUN' % (remote, local))
            cont.append('ip link set ipv6tun up # TUN')
            cont.append('ip addr add %s dev ipv6tun # TUN' % (localv6))
            cont.append('ip -6 ro add 2003::/3 dev ipv6tun # TUN\n')

        l = open('/etc/conf.d/local.start', "wt")
        l.write('\n'.join(cont))
        l.close()

        for iface, vlans in vlanIfaces.items():
            net+= "vlans_%s=\"%s\"\n" % (iface, ' '.join(vlans))
            net+= "vconfig_%s=( \"set_name_type VLAN_PLUS_VID_NO_PAD\" )\n" % (iface)

        if config.EthernetDevices.get('extra', None):
            net += config.EthernetDevices['extra']
            net += '\n' 

        for wan in config.WANDevices:
            net += "config_%s=(\"ppp\")\n" % wan
            for opt in config.WANDevices[wan]:
                if type(config.WANDevices[wan][opt]) is list:
                    val = "( %s )" % (' '.join(['"%s"' % i for i in config.WANDevices[wan][opt]]))
                else:
                    val = '"%s"' % config.WANDevices[wan][opt]
                net += '%s_%s=%s \n' % (opt, wan, val)

            net += '\n'
        net += routes
        Utils.writeConf('/etc/conf.d/net', net, '#')



import config, os
from Core import Utils

class Plugin(object):
    parameterHook = "--shorewall"
    parameterDescription = "Reconfigure Shorewall"
    parameterArgs = ""
    autoRun = True
    configFiles = [ 
        '/etc/shorewall/rules',
        '/etc/shorewall/zones',
        '/etc/shorewall/interfaces',
        '/etc/shorewall/policy',
        '/etc/shorewall/params',
        '/etc/ulogd.conf',
        '/etc/shorewall/providers',
        '/etc/shorewall/route_rules',
        '/etc/shorewall/tcrules',
        '/etc/shorewall/tcclasses',
        '/etc/shorewall/tcdevices',
    ]

    def reloadServices(self):
        os.system('shorewall restart')

    def writeConfig(self, *a):
        rules = ""

        ruleList = [
           [1, 'Ping/ACCEPT       all      all'],
           [1, 'AllowICMPs        all      all'],
           [1, 'ACCEPT            all      all    udp        33434:33463'],
        ]
        
        ruleList.extend(config.Shorewall.get('redirect', []))
        ruleList.extend(config.Shorewall.get('rules', []))
        ruleList.extend(config.Shorewall.get('dnat', []))

        for enable, rule in ruleList:
            if not enable:
                rules += "#"

            rules += "%s\n" % rule

        if config.Shorewall.get('blockp2p', False):
            rules += "REJECT   all        all      ipp2p:tcp\n"
            rules += "REJECT   all        all      ipp2p:udp\n"

        rules += "\n#LAST LINE -- ADD YOUR ENTRIES BEFORE THIS ONE -- DO NOT REMOVE\n"

        l = open('/etc/shorewall/rules', 'wt')
        l.write(rules)
        l.close()
        
        tos =  "###############################################################################\n"
        tos +=     "#SOURCE         DEST            PROTOCOL        SOURCE  DEST    TOS\n"
        tos += "#                                               PORTS   PORTS\n"
        
        for p, proto, t in config.Shorewall.get('qos', []):
            tos += "all             all             %s         -       %s      %s\n" % (proto, p, t)
            tos += "all             all             %s         %s      -       %s\n" % (proto, p, t)

        tos += "\n#LAST LINE -- ADD YOUR ENTRIES BEFORE THIS ONE -- DO NOT REMOVE\n"

        l = open('/etc/shorewall/tos', 'wt')
        l.write(tos)
        l.close()

        policies = """fw         all           ACCEPT
loc             fw              ACCEPT
loc             loc             ACCEPT\n"""
        interfaces = ""
        zones = "fw      firewall\n"
        for zone in config.Shorewall.get('zones',{}):
            zoneifaces = config.Shorewall['zones'][zone]['interfaces']
            policy = config.Shorewall['zones'][zone]['policy']
            log  = config.Shorewall['zones'][zone]['log']

            zones += "%s    ipv4\n" % (zone, )

           
            policies += "%s     all    %s   %s\n" % (zone, policy, log)

            for interface in zoneifaces:
                interfaces += "%s   %s\n" % (zone, interface)

        for zone in Utils.getLanZones(config):
            if config.ProxyConfig.get('captive'):
                zones += "c%s:%s\n" % (zone, zone)
                if config.ProxyConfig.get('captiveblock'):
                    policies += "c%s    all   DROP  $LOG\n" % (zone, )
                else:
                    policies += "c%s    all   ACCEPT\n" % (zone, )
 
        policies += "\n#LAST LINE -- ADD YOUR ENTRIES BEFORE THIS ONE -- DO NOT REMOVE\n"
        interfaces += "\n#LAST LINE -- ADD YOUR ENTRIES BEFORE THIS ONE -- DO NOT REMOVE\n"
        zones += "\n#LAST LINE -- ADD YOUR ENTRIES BEFORE THIS ONE -- DO NOT REMOVE\n"

        params = "LOG=ULOG\n#LAST LINE -- ADD YOUR ENTRIES BEFORE THIS ONE -- DO NOT REMOVE\n"

        # SNAT configuration 
        nat = """###############################################################################
#EXTERNAL       INTERFACE       INTERNAL        ALL             LOCAL
#                                               INTERFACES\n"""

        for ru in config.Shorewall.get('snat', []):
            nat += ru + '\n'

        nat += "#LAST LINE -- ADD YOUR ENTRIES BEFORE THIS ONE -- DO NOT REMOVE\n"

        l = open('/etc/shorewall/nat', 'wt')
        l.write(nat)
        l.close()

        # Masqeurading 
        masq = ""
        for dest, sources in config.Shorewall.get('masq', {}).items():
            for source in sources:
                if type(source) == list:
                    # New style rule...
                    dstnet = source[0].replace('-', '')

                    if dstnet:
                        dstnet = ':'+dstnet

                    srcnet = source[1].replace('-', '')
                    srcif = source[2].replace('-', '')

                    if srcif:
                        # Ignore the srcnet rule...
                        srcnet = srcif
                    
                    using = source[3].replace('-', '')

                    proto = source[4].replace('-', '')
                    port = source[5].replace('-', '')

                    if proto and not using:
                        using = '-'

                    masq += "%s%s    %s    %s    %s    %s\n" % (dest, dstnet, srcnet, using, proto, port)
                else:
                    masq += "%s         %s \n" % (dest, source)
        masq += "#LAST LINE -- ADD YOUR ENTRIES BEFORE THIS ONE -- DO NOT REMOVE\n"

        wl = {'policy': policies, 'interfaces':interfaces, 'zones':zones, 'params':params, 'masq':masq}
        for i in wl:
            l = open('/etc/shorewall/%s' % i, 'wt')
            l.write(wl[i])
            l.close()

        providers = "#NAME   NUMBER  MARK    DUPLICATE       INTERFACE       GATEWAY         OPTIONS         COPY\n"
        i = 0
        lans = ','.join(Utils.getLans(config))
        for inter in config.ShorewallBalance:
            i+= 1
            interzone = config.Shorewall['zones'][inter[0]]['interfaces'][0].split()[0]
            providers += "%s   %s   %s   main   %s    %s    %s,optional    %s \n" % (inter[0], i, i, interzone, inter[1], inter[2], lans)

        providers += "#LAST LINE -- ADD YOUR ENTRIES BEFORE THIS ONE -- DO NOT REMOVE\n"

        l = open('/etc/shorewall/providers', 'wt')
        l.write(providers)
        l.close()

        routes = "#SOURCE                 DEST                    PROVIDER        PRIORITY\n"

        for ru in config.ShorewallSourceRoutes:
            if len(ru)>2:
                prio = ru[2]
            else:
                prio = 1000

            routes += "%s                  -                      %s              %s\n" % (ru[0], ru[1], prio)

        routes += "#LAST LINE -- ADD YOUR ENTRIES BEFORE THIS ONE -- DO NOT REMOVE\n"

        l = open('/etc/shorewall/route_rules', 'wt')
        l.write(routes)
        l.close()

        parp = """
#ADDRESS        INTERFACE       EXTERNAL        HAVEROUTE       PERSISTENT

"""
        for arps in config.Shorewall.get('proxyarp', {}):
            parp += "%s   %s        %s          no      yes\n" % tuple(arps)

        parp += "#LAST LINE -- ADD YOUR ENTRIES BEFORE THIS ONE -- DO NOT REMOVE\n"

        l = open('/etc/shorewall/proxyarp', 'wt')
        l.write(parp)
        l.close()

        routes = ""
        # Check if there are any routes to be added
        for interface, defin in config.EthernetDevices.items():
            for dest, gw in defin.get('routes', []):
                if dest!='default':
                    for inter in config.ShorewallBalance:
                        # Add a route to all shorewall balancing table
                        routes += "ip ro add %s via %s table %s\n" % (dest, gw, inter[0])

        init = """use Shorewall::Chains;

insert_rule $filter_table->{FORWARD}, 1, "-j ULOG --ulog-nlgroup 2";
insert_rule $filter_table->{INPUT}, 1, "-j ULOG --ulog-nlgroup 2";
insert_rule $filter_table->{OUTPUT}, 1, "-j ULOG --ulog-nlgroup 2";

1;\n"""
        l = open('/etc/shorewall/initdone', 'wt')
        l.write(init)
        l.close()

        tcdevices = ""
        tcclasses = ""
        for dev, det in config.Shaping.items():
            tcdevices += "%s          %s          %s\n" % (dev, det['ratein'], det['rateout'])

            for cls in det['classes']:
                tcclasses+= "%s       %s      %s      %s      %s      %s\n" %  (dev, cls[0], cls[1], cls[2], cls[3], cls[4])

        tcclasses += "\n#LAST LINE -- ADD YOUR ENTRIES BEFORE THIS ONE -- DO NOT REMOVE\n"

        tcrules = ""
        for i in config.ShaperRules:
            tcrules += "%s\n" % i
        tcrules += "\n#LAST LINE -- ADD YOUR ENTRIES BEFORE THIS ONE -- DO NOT REMOVE\n"


        l = open('/etc/shorewall/tcdevices', 'wt')
        l.write(tcdevices)
        l.write('\n#LAST LINE -- ADD YOUR ENTRIES BEFORE THIS ONE -- DO NOT REMOVE\n')
        l.close()
        l = open('/etc/shorewall/tcclasses', 'wt')
        l.write(tcclasses)
        l.close()
        l = open('/etc/shorewall/tcrules', 'wt')
        l.write(tcrules)
        l.close()

        ipup = """#!/bin/sh -e
killall shorewall
/sbin/shorewall restart
/etc/init.d/quagga restart
/usr/local/tcs/tums/networkManager up $1 || true
exit 0\n"""

        l = open('/etc/ppp/ip-up.d/shorewall', 'wt')
        l.write(ipup)
        l.close()

        ipdown = """#!/bin/sh -e
killall shorewall
/sbin/shorewall restart
/etc/init.d/quagga restart
/usr/local/tcs/tums/networkManager down $1 || true
exit 0\n"""

        l = open('/etc/ppp/ip-down.d/shorewall', 'wt')
        l.write(ipdown)
        l.close()

        os.system('chmod a+x /etc/ppp/ip-up.d/shorewall')
        os.system('chmod a+x /etc/ppp/ip-down.d/shorewall')

        # Update shorewall.conf
        os.system('cp /usr/local/tcs/tums/configs/shorewall.conf /etc/shorewall/')

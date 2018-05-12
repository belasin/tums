import config, os

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

        for enable, rule in config.Shorewall.get('rules',[]):
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

        policies = "fw         all           ACCEPT\nloc             fw              ACCEPT\n"
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

        policies += "\n#LAST LINE -- ADD YOUR ENTRIES BEFORE THIS ONE -- DO NOT REMOVE\n"
        interfaces += "\n#LAST LINE -- ADD YOUR ENTRIES BEFORE THIS ONE -- DO NOT REMOVE\n"
        zones += "\n#LAST LINE -- ADD YOUR ENTRIES BEFORE THIS ONE -- DO NOT REMOVE\n"

        params = "LOG=ULOG\n#LAST LINE -- ADD YOUR ENTRIES BEFORE THIS ONE -- DO NOT REMOVE\n"

        masq = ""
        for dest, sources in config.Shorewall.get('masq', {}).items():
            for source in sources:
                masq += "%s         %s \n" % (dest, source)
        masq += "#LAST LINE -- ADD YOUR ENTRIES BEFORE THIS ONE -- DO NOT REMOVE\n"

        wl = {'policy': policies, 'interfaces':interfaces, 'zones':zones, 'params':params, 'masq':masq}
        for i in wl:
            l = open('/etc/shorewall/%s' % i, 'wt')
            l.write(wl[i])
            l.close()

        providers = "#NAME   NUMBER  MARK    DUPLICATE       INTERFACE       GATEWAY         OPTIONS         COPY\n"
        i = 0
        for inter in config.ShorewallBalance:
            i+= 1
            interzone = config.Shorewall['zones'][inter[0]]['interfaces'][0].split()[0]
            providers += "%s   %s   %s   main   %s    %s    %s    %s \n" % (inter[0], i, i, interzone, inter[1], inter[2], config.LANPrimary)

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

        if os.path.exists('/etc/debian_version'):
            # fix default/shorewall
            print ""



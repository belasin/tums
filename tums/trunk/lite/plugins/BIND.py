import config, os, time
from Core import Utils

class Plugin(object):
    parameterHook = "--bind"
    parameterDescription = "Reconfigure BIND DNS"
    parameterArgs = ""
    autoRun = True
    configFiles = [ 
        '/etc/bind/named.conf',
        '/etc/bind/pri/forward.zone',
        '/etc/bind/pri/reverse.zone',
    ]

    def reloadServices(self):
        os.system('rm /var/bind/pri/*.jnl')
        os.system('/etc/init.d/named restart')

    def writeConfig(self, *a):
        SOA = """@ 86400         IN      SOA    %s.%s. postmaster.%s. (
                                    1               ; Serial
                                    28800           ; Refresh
                                    7200            ; Retry
                                    604800          ; Expire
                                    3600)          ; Minimum TTL

                            NS      %s.%s
""" % (config.Hostname, config.Domain, config.Domain, config.Hostname, config.Domain)

        serverIP = config.EthernetDevices[config.LANPrimary]['ip'].split('/')[0]

        forward = SOA + "                        A       %s\n" % serverIP

        for cname in config.TCSAliases:
            spaces = ''.join([" " for i in range(20-len(cname))])
            forward += "%s %s   CNAME   %s\n" % (cname, spaces, config.Hostname)

        forward += "%s                  A       %s\n" % (config.Hostname, serverIP)

        ipv6listen = ""
        ipv6query = ""
        if config.EthernetDevices[config.LANPrimary].get('ipv6', False):
            ipv6addr = config.EthernetDevices[config.LANPrimary]['ipv6'].split('/')[0]
            forward += "%s                  AAAA    %s\n" % (config.Hostname, ipv6addr)

            ipv6listen = "listen-on-v6 {\n        %s;\n    };" % ipv6addr

            ipv6query = "%s;" % Utils.getV6Network(config.EthernetDevices[config.LANPrimary]['ipv6'])


        reverse = SOA + "%s                     PTR     %s.%s.\n" % (serverIP.split('.')[-1], config.Hostname, config.Domain)
        os.system('mkdir -p /etc/bind/pri > /dev/null 2>&1')
        os.system('chown -R bind:bind /etc/bind/pri ')
        Utils.writeConf('/etc/bind/pri/forward.zone', forward, ';')
        Utils.writeConf('/etc/bind/pri/reverse.zone', reverse, ';')


        options = """options {
    listen-on {
        127.0.0.1;
        %s;
    };

    %s

    allow-query {
        %s;
        127.0.0.1;
        %s
    };

    forwarders {
%s    };

    directory "/var/bind";
    pid-file "/var/run/named/named.pid";
    forward first;\n};\n\n""" % (
            serverIP, 
            ipv6listen,  
            config.EthernetDevices[config.LANPrimary]['network'], 
            ipv6query,
            ''.join(["        %s;\n" % i for i in config.ForwardingNameservers])
        )


        zones = """zone "." in {
        type hint;
        file "named.ca";
    };

    zone "0.0.127.in-addr.arpa" in {
        type master;
        file "pri/127.zone";
        notify no;
    };

    zone "localhost" in {
        type master;
        file "pri/localhost.zone";
        notify no;
    };

    zone "%s.in-addr.arpa" in {
        type master;
        file "pri/reverse.zone";
        notify no;
        allow-update { 127.0.0.1; };
    };

    zone "%s" in {
        type master;
        file "pri/forward.zone";
        notify no;
        allow-update { 127.0.0.1; };
    };\n""" % ('.'.join([i for i in reversed(serverIP.split('.')[:3])]), config.Domain)
        # Debian modifications
        if os.path.exists('/etc/debian_version'):
            zones = zones.replace('named.ca', 'db.root')
            zones = zones.replace('pri/localhost.zone', 'db.local')
            zones = zones.replace('pri/127.zone', 'db.127')
            options = options.replace('pid-file "/var/run/named/named.pid";', '')
            options = options.replace('directory "/var/bind";', 'directory "/etc/bind";')

            # Rechown
            os.system('chown -R bind:bind /etc/bind/*')

        bindFile = options + zones

        Utils.writeConf('/etc/bind/named.conf', bindFile, '//')



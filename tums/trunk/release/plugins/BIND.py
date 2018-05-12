import config, os, time, sys
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
        os.system('rm /etc/bind/pri/*.jnl > /dev/null 2>&1')
        os.system('/etc/init.d/bind9 restart')
    
    def writeConfig(self, *a):

        try:
            serverIP = Utils.getLanIPs(config)[0]
        except:
            # We aren't sure what our IP is.. oh dear
            serverIP = "127.0.0.1"

        #Check current hostname is consistent
        try:
            l = open('/etc/hostname', 'r')
            sysHostname = l.read()
            l.close()
            if config.Hostname != sysHostname.strip():
                #If the hostname is inconsistent then we should redefine the hostname
                #This will fix problems with debsecan
                l = open('/etc/hostname', 'wt')
                l.write(config.Hostname + "\n")
                l.close()
                os.system('/bin/hostname -F /etc/hostname')
        except Exception, _e:
            print "Warning: Unable to validate or correct hostname, ", str(_e)

        # This all needs to happen first
        hosts = """127.0.0.1       localhost
127.0.1.1       %(host)s.%(domain)s   %(host)s

# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
ff02::3 ip6-allhosts\n""" % {'host': config.Hostname, 'domain': config.Domain}
        
        l = open('/etc/hosts', 'wt')
        l.write(hosts)
        l.close()
        
        if config.General.get('sysresolv', []):
            ns = ""
            for i in config.General['sysresolv']:
                ns += 'nameserver %s\n' % i
        else:
            if serverIP == "127.0.0.1":
                ns = ""
            else:
                ns = 'nameserver 127.0.0.1\n'
        
        resolv = """search %s
domain %s
%s\n""" % (config.Domain, config.Domain, ns )
        l = open('/etc/resolv.conf', 'wt')
        l.write(resolv)
        l.close()
 
        os.system('mkdir -p /etc/bind/pri > /dev/null 2>&1')

        # Default SOA template
        SOA = """@ 86400         IN      SOA    %s. postmaster.%s. (
                                    1               ; Serial
                                    28800           ; Refresh
                                    7200            ; Retry
                                    604800          ; Expire
                                    3600)          ; Minimum TTL\n"""
        zones = ""
        ipv6addr = ""
        ipv6listen = ""
        ipv6query = ""

        if Utils.getLanIP6s(config):
            ipv6addr = Utils.getLanIP6s(config)
            
            ipv6listen = "listen-on-v6 {\n        %s;\n    };" % ';'.join([n.split('/')[0] for n in ipv6addr])
            
            ipv6query = "%s;" % Utils.getV6Network(ipv6addr[0])
            
        # Create the defualt zone if there is no config overriding it
        TSOA = SOA % ("%s.%s" % (config.Hostname,config.Domain), config.Domain)
        TSOA += "                            NS      %s.%s.\n" % (config.Hostname, config.Domain)

        if not config.Domain in config.General.get('zones', {}):
            if not serverIP:
                serverIP = "127.0.0.1"
            
            forward = TSOA + "                        A       %s\n" % serverIP
            
            for cname in config.TCSAliases:
                spaces = ''.join([" " for i in range(20-len(cname))])
                forward += "%s %s   CNAME   %s\n" % (cname, spaces, config.Hostname)
            
            forward += "%s                  A       %s\n" % (config.Hostname, serverIP)
            
            if ipv6addr:
                forward += "%s                  AAAA    %s\n" % (config.Hostname, ipv6addr[0])
            
            Utils.writeConf('/etc/bind/pri/%s.zone' % (config.Domain,), forward, ';')
            zones += """    zone "%s" in {
        type master;
        allow-update {
            127.0.0.1;
        };
        notify no;
        file "pri/%s.zone";
    };\n\n""" % (config.Domain, config.Domain)
        
        for domain, info in config.General.get('zones', {}).items():
            if not info:
                continue

            zones += "    zone \"%s\" in {\n" % domain
            
            # Get options
            if info.get('options', None):
                for opt in info['options']:
                    zones += "        %s;\n" % opt
            else:
                # Use defaults
                zones += "        type master;\n        notify no;\n"
                
            if 'type forward' not in info.get('options'):
                # check updaters
                if info.get('update', None):
                    zones += "        allow-update {\n"
                    for update in info['update']:
                        zones += "            %s;\n" % update
                    zones += "        };\n"
                    
                else:
                    # Use default localhost.
                    zones += "        allow-update {\n            127.0.0.1;\n        };"

            ns = info.get('ns', [])
            if len(ns) < 1:
                print "ERROR!! Domain %s requires at least 1 name server!" % domain
                sys.exit()

            # Create zone data
            zonedata = ""

            for i in ns:
                zonedata += "                        NS      %s.\n" % i
            
            if info.get('records'):
                maxRec = max([len(rec.split()[0]) for rec in info.get('records', [])]) + 5
            else:
                maxRec = 4

            colspace = [maxRec, 8]
            first = ""
            for rec in info.get('records', []):
                if "MX" in rec:
                    host, type, prio, data = rec.split()
                    type = "%s %s" % (type, prio)
                else:
                    host, type, data = tuple(rec.split())

                theseSpaces = [ colspace[c]-len(i) for c,i in enumerate([host, type])]
                recLine = "%s%s%s%s%s\n" % (host, " "*theseSpaces[0], type, " "*theseSpaces[1], data)
                if type =="NS" or "MX" in rec:
                    first += recLine
                else:
                    zonedata += recLine

            if 'type forward' in info.get('options'):
                zones += "        forwarders {\n           %s;\n        };\n" % info.get('forward')

            if 'type slave' in info.get('options'):
                uservs = []
                
                for i in info.get('update'):
                    if i != "127.0.0.1":
                        uservs.append(i)

                zones += "        masters {\n           %s;\n        };\n" % ';'.join(uservs)
            
            if 'type master' in info.get('options'):
                zones += "        file \"pri/%s.zone\";\n" % domain
            # Terminate entry
            zones += "    };\n"
            
            l = open('/etc/bind/pri/%s.zone' % domain, 'wt')
            l.write(SOA % (ns[0],domain))
            l.write(first)
            l.write(zonedata)
            l.close()
            
        reverse = TSOA  + "%s                     PTR     %s.%s.\n" % (serverIP.split('.')[-1], config.Hostname, config.Domain)
        
        os.system('chown -R bind:bind /etc/bind/pri ')
        Utils.writeConf('/etc/bind/pri/reverse.zone', reverse, ';')
        
        lanv4Ips = Utils.getLanIPs(config)
        if lanv4Ips:
            listenv4 = ';'.join(lanv4Ips) + ';'
        else:
            listenv4 = ""
        
        options = """options {
    listen-on {
        127.0.0.1;
        %s
    };

    %s

    allow-query {
        %s
        127.0.0.1;
        0.0.0.0/0;
    };

    forwarders {
%s    };

    directory "/var/bind";
    pid-file "/var/run/named/named.pid";
    forward first;\n};\n\n""" % (
            listenv4,
            ipv6listen,  
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

%s\n""" % ('.'.join([i for i in reversed(serverIP.split('.')[:3])]), zones)
        
        # Debian modifications
        zones = zones.replace('named.ca', 'db.root')
        zones = zones.replace('pri/localhost.zone', 'db.local')
        zones = zones.replace('pri/127.zone', 'db.127')
        options = options.replace('pid-file "/var/run/named/named.pid";', '')
        options = options.replace('directory "/var/bind";', 'directory "/etc/bind";')
            
        # Rechown
        os.system('chown -R bind:bind /etc/bind/*')
        
        bindFile = options + zones
        
        Utils.writeConf('/etc/bind/named.conf', bindFile, '//')
        
       
        os.system('rm /etc/bind/pri/*.jnl > /dev/null 2>&1')

import config, os
from Core import Utils

class Plugin(object):
    """ Configures tunnels. """
    parameterHook = "--tunnel"
    parameterDescription = "Reconfigure tunnels"
    parameterArgs = ""
    autoRun = True
    required = "debian"
    configFiles = [ 
        "/etc/l2tpns/startup-config",
        "/etc/l2tpns/ip_pool",
    ]

    def reloadServices(self):
        os.system('/etc/init.d/l2tpns restart')

    def l2tpClient(self, clients):
        """ @param clients: C(dict) of l2tp client settings """
        l2tpclient  = "[global]\n"
        l2tpclient += " port = 1701\n"
        l2tpclient += " auth file = /etc/l2tp/l2tp-secrets\n"
        
        if clients:
            # Disable l2tpns
            os.system('/etc/init.d/l2tpns stop > /dev/null 2>&1')
            os.system('update-rc.d -f l2tpns remove > /dev/null 2>&1')
        else:
            os.system('/etc/init.d/l2tpns start > /dev/null 2>&1')
            os.system('update-rc.d l2tpns start 16 2 3 4 5 . stop 16 0 1 6 . > /dev/null 2>&1')
            
        for n in clients:
            l2tpclient += "[lac %s]\n" % c['name']
            l2tpclient += " lns = %s\n" % c['endpoint']
            l2tpclient += " redial = yes\n" 
            l2tpclient += " redial timeout = 15\n"
            l2tpclient += " max redials = 0\n"
            l2tpclient += " name = %s\n" % c['username']
            l2tpclient += " require chap = yes\n"
            l2tpclient += " require auth = yes\n"
            l2tpclient += " pppoptfile = /etc/l2tpd/options.l2tp\n"
        
            opts  = "ipcp-accept-local\n"
            opts += "ipcp-accept-remote\n"
            opts += "refuse-eap\n"
            opts += "noccp\n"
            opts += "noauth\n"
            opts += "crtscts\n"
            opts += "idle 1800\n"
            opts += "mtu 1410\n"
            opts += "mru 1410\n"
            if c['default']:
                opts += "defaultroute\n"
            else:
                opts += "nodefaultroute\n"
            opts += "debug\n"
            opts += "lock\n"

            optF = open('/etc/l2tpd/options.%s' % c['name'], 'wt')
            optF.write(opts)
            optF.close()

        l2tpC = open('/etc/l2tpd/l2tpd.conf', 'wt')
        l2tpC.write(l2tpclient)
        l2tpC.close()
        
    def openvpnClient(self, clients):
        """ @param clients: C(dict) of openvpn clients """
        cnt = 0
        for n in clients:
            cnt += 1 # keep a counter for each client to have a specific tun ID
            # XXX - we should probably configure the port as well...
            conf = """client
dev tap%(cnt)s
proto %(proto)s
remote %(remote)s
port 1194
resolv-retry infinite
nobind
persist-key
persist-tun
ca %(name)s-ca.crt
cert %(name)s-cert.crt
key %(name)s-key.key
comp-lzo
verb 3
keepalive 10 360
tls-timeout 300\n""" % { 
                'cnt': str(cnt), 
                'proto': str(n['proto'].lower()),
                'remote': str(n['endpoint']),
                'name': str(n['name']),
            }
            l = open('/etc/openvpn/%s-client.conf' % n['name'], 'wt')
            l.write(conf)
            l.close()

            l = open('/etc/openvpn/%s-ca.crt' % n['name'], 'wt')
            l.write(n['CA'])
            l.close()
            
            l = open('/etc/openvpn/%s-cert.crt' % n['name'], 'wt')
            l.write(n['crt'])
            l.close()
        
            l = open('/etc/openvpn/%s-key.key' % n['name'], 'wt')
            l.write(n['key'])
            l.close()

    def pptpClient(self, clients):
        pass

    def writeConfig(self, *a):
        # XXX Need to add rules to shorewall for the interface created!
        # Create a store for each type
        types = {
            'openvpn': [],
            'l2tp':    [], 
            'pptp':    [],
        }
        # Map types to their handler functions
        handlers = {
            'openvpn':  self.openvpnClient,
            'l2tp':     self.l2tpClient,
        }

        # reprocess the configuration
        for name, conf in config.Tunnel.items():
            cnf = conf
            cnf['name'] = str(name)
            types[str(cnf['type'])].append(cnf)
        
        # Call the handler functions with the stores
        for k,v in types.items():
            if v:
                v.sort()
                handlers[k](v)

from Core import WebUtils, Utils, confparse
from twisted.internet import utils, defer
import os, sys
import Settings
import lang

vpnInit = 'openvpn'

myLang = lang.Text('en')


def set_windows_vpn(sysconf, data, callback):
    """
    Configures Windows PPTP VPN Passthrough
    Returns a C{deferred} which will fire [callback] when complete
    @param sysconf: An instance of L{Core.confparse.Config}
    @param data: A dictionary of data options. This module requres the following
        'windows': C{bool} whether or not this configuration will handle PPTP passthrough
        'winip':   C{str} of the IP address for the windows server
        'winextip': C{str} for external IP address from which to forward these connections
    @param callback: C{function} which will be returned once this (potential) deferred chain is complete
    """
    confdata = sysconf.Shorewall

    rset = confdata.get('rules', [])

    rule = "DNAT    net     loc:%s  47      -       -               %s" % (data['winip'] or "", data['winextip'] or "")
    rule2 = "DNAT    net     loc:%s  tcp     1723    -               %s" % (data['winip'] or "", data['winextip'] or "")

    # Find such a rule and strip it:
    rsetnew = []
    for en,ru in rset:
        rusp = ru.split()
        try:
            if "DNAT" == rusp[0] and "47" == rusp[3]:
                exists = True
            elif "DNAT" == rusp[0] and "1723" == rusp[4]:
                exists = True
            else:
                exists = False
        except:
            exists = False

        if not exists:
            rsetnew.append([en, ru])

    if data['windows']:
        rsetnew.append([1, rule.encode('ascii', 'replace')])
        rsetnew.append([1, rule2.encode('ascii', 'replace')])
    confdata['rules'] = rsetnew

    sysconf.Shorewall = confdata

    return WebUtils.restartService('shorewall').addBoth(callback)
    
def get_windows_vpn(sysconf):
    """ Retrieve the windows VPN settings from the firewall rules table"""

    sw = sysconf.Shorewall.get('rules', [])

    winserv = ""
    external = ""
    enabled = False
    for en, i in sw:
        l = i.strip('\n').split()
        if l and (l[0]=="DNAT" or l[0]=="#DNAT"):
            if len(l) > 5 and l[3]=="47":
                winserv = l[2].split(':')[-1]
                if len(l) > 6:
                    external = l[6]
                if l[0]=="DNAT":
                    enabled = True
                if not en:
                    enabled = False

    return winserv, external, enabled

def get_openvpn_settings(*sysconf):
    """ Get settings out of openvpn """
    def callCompleted(status, routes):
        nr = []
        for ro in routes.split('\n'):
            if ro.strip('\n'):
                nr.append(ro.strip())

        routes = nr
        del nr

        try:
            confFile = open('/etc/openvpn/vpn.conf', 'rt')
        except:
            confFile = [""]

        activeRoutes = []
        conf = {'mtu': '1400'}
        rc = status
        vpnstat = ""
        for i in rc.split('\n'):
            if vpnInit in i:
                vpnstat = i

        if "openvpn" in vpnstat:
            conf['openvpn'] = True

        for i in confFile:
            line = i.strip('\n')

            if "route" in line:
                # Activate a route and add it to the list if not there
                route = line.split('"')[1].split()
                tr = "%s %s" % (route[1], route[2])
                activeRoutes.append(tr.strip())
                if not tr in routes:
                    routes.append(tr.strip())

            if "server-bridge" in line:
                ips = line.split()
                conf['iprange1'] = ips[3]
                conf['iprange2'] = ips[4]

            if "dhcp-option" in line:
                sp = line.replace('"','').split()
                conf[sp[2]] = sp[3]

            if "proto" in line:
                if "tcp" in line:
                    conf['tcp'] = True

        conf['routes'] = activeRoutes

        return conf, routes

    def getRc(routes):
        rc = WebUtils.system(Settings.BaseDir + '/syscripts/rcStatus.py')

        return rc.addBoth(callCompleted, routes)
 
    return WebUtils.system("route -n | grep -E \"(eth|tun|tap)\" | grep -v \"G\"  | awk '{print $1 \" \" $3}'").addBoth(getRc)

def create_certificate(sysconf, data, callback):
    """Create a cert and sign it"""

    name = data['name'].replace(' ', '').replace('-', '')

    def mailUser(_):
    # Mail the key to the person
        if data['mailKey']:
            files = ["/usr/local/tcs/tums/packages/%s-vpn.zip" % name]

            mailp = """Your Vulani VPN account has been created.

                Please see the attached files to configure your VPN. Save all the 
                attached files to a folder on your computer and run the attached 
                openvpn-install.exe program. Copy the rest of the attachments to 
                this email and extract the zip file to the folder
                C:\\Program Files\\OpenVPN\\config\\

                To connect to the VPN find the icon in the system tray of two 
                red computers, and double click on it. 

                You may be required to edit the TCS.ovpn file, and replace the 
                address on the line "remote %s" with the external address of 
                your server.

                Should you have any trouble following these instructions please 
                contact support@vulani.net or by telephone at +27 31 277 1250.
            """ % (sysconf.ExternalName,)

            # Recombobulate for syntax sake
            mailtext = '\n'.join([ i.strip() for i in mailp.split('\n')])

            try:
                return Utils.sendMail("Vulani <nobody@%s>" % Settings.defaultDomain, [data['mail']], myLang.vpnConfigDetails,
                    mailtext, files).addBoth(callback)

            except Exception, c:
                print c
                return Utils.exceptionOccured(c)

            return callback(None)
        return callback(None)
    def createZip(_):
        # Get protocol setting
        l = open('/etc/openvpn/vpn.conf')
        proto = "udp"
        for i in l:
            if not i.strip():
                continue
            s = i.split()
            if s[0] == "proto":
                proto = s[1]

        tempconf = """client
        dev tap
        proto %s
        remote %s
        port 1194
        resolv-retry infinite
        redirect-gateway def1
        nobind
        persist-key
        persist-tun
        ca ca.crt
        cert %s.crt
        key %s.key
        comp-lzo
        verb 3
        keepalive 10 360
        tls-timeout 300""" % (proto, sysconf.ExternalName, name, name)
        l = open('/tmp/TCS.ovpn', 'wt')
        for i in tempconf.split('\n'):
            l.write(i.strip()+'\n')
        l.close()

        return utils.getProcessOutput('/usr/bin/zip', ["-j",
            "/usr/local/tcs/tums/packages/%s-vpn.zip" % name,
            '/etc/openvpn/keys/%s.csr' % name,
            '/etc/openvpn/keys/%s.crt' % name,
            '/etc/openvpn/keys/%s.key' % name,
            '/etc/openvpn/keys/ca.crt',
            '/usr/local/tcs/tums/packages/openvpn-install.exe',
            "/tmp/TCS.ovpn",
        ], errortoo=1).addCallbacks(mailUser, mailUser)

    cmd = 'cd /etc/openvpn/easy-rsa; source /etc/openvpn/easy-rsa/vars; /etc/openvpn/easy-rsa/pkitool %s' % (name, )

    d = utils.getProcessOutput('/bin/sh', ['-c', cmd], errortoo=1).addCallbacks(createZip, createZip)

    if data['ip']:
        try:
            j = open('/etc/openvpn/vpn-ccd/%s' % (name), 'wt')
            j.write('ifconfig-push %s 255.255.255.0\n' % (data['ip']))
            j.close()
        except IOError:
            print "Unable to write CCD" 

    return d

def set_openvpn(sysconf, data, callback):
    """ Reconfigura the standard VPN"""
    defs = []
    if data['openvpn']:
        # Enable vpn
        defs.append(WebUtils.system('update-rc.d %s defaults' % vpnInit))
    else:   
        defs.append(WebUtils.system('update-rc.d %s defaults' % vpnInit))

    # Allow it in the firewall
    fw = sysconf.Shorewall

    if not fw['zones'].get('loc', False):
        # No loc zone, so make one
        fw['zones']['loc'] = {
            'policy':'ACCEPT',
            'interfaces': [],
            'log': ''
        }

    # Add the openvpn interface to the loc zone
    if 'tap0' not in fw['zones']['loc']['interfaces']:
        fw['zones']['loc']['interfaces'].append('tap0')

    sysconf.Shorewall = fw
    # Save the config options

    servIp = '.'.join(data['iprange1'].split('.')[:3]) + '.1' # Take the IP network and /24 server is .1
    # Allow through Exim

    m = sysconf.Mail
    servRange = '.'.join(data['iprange1'].split('.')[:3]) + '.0/24'
    if m.get('relay-from'):
        m['relay-from'].append(servRange)
    else:
        m['relay-from'] = [servRange]
    sysconf.Mail = m

    ip1 = data['iprange1']

    # Make sure people don't put the IP range on top of the server address:(
    i1segs = ip1.split('.')
    if int(i1segs[-1]) == 1:
        i1segs[-1] = "2"
        ip1 = '.'.join(i1segs)

    ip2 = data['iprange2']

    if data['tcp']:
        proto = "tcp"
    else:
        proto = "udp"

    confData = """dev tap0
        proto %s
        port 1194
        ifconfig-pool-persist /etc/openvpn/vpn_pool
        client-config-dir /etc/openvpn/vpn-ccd/
        keepalive 10 120
        client-to-client
        tls-timeout 300
        comp-lzo
        verb 3
        persist-key
        persist-tun
        status /var/log/vpn-status.log
        ca   /etc/openvpn/keys/ca.crt
        cert /etc/openvpn/keys/vpn.crt
        key  /etc/openvpn/keys/vpn.key
        dh   /etc/openvpn/keys/dh1024.pem
        crl-verify  /etc/openvpn/keys/crl.pem
        
        server-bridge %s 255.255.255.0 %s %s
        ifconfig %s 255.255.255.0
    """ % (proto, servIp, ip1, ip2, servIp)

    if data['routes']:
        for ro in data['routes']:
            confData += 'push "route %s"\n' % (ro,)

    for i in ['DNS', 'WINS', 'DOMAIN']:
        if data[i]:
            confData += 'push "dhcp-option %s %s"\n' % (i, data[i])

    confFile = open('/etc/openvpn/vpn.conf', 'wt')
    confFile.write(confData)
    confFile.close()

    def Continue(_):
        def returnB(_):
            return WebUtils.system('/usr/local/tcs/tums/configurator --shorewall; shorewall restart').addBoth(callback)

        if data['openvpn']:
            return WebUtils.system('/etc/init.d/%s restart' % vpnInit).addBoth(returnB)
        else:
            return WebUtils.system('/etc/init.d/%s stop' % vpnInit).addBoth(returnB)

    return defer.DeferredList(defs).addBoth(Continue)

def revoke_certificate(name):
    c = 'cd /etc/openvpn/easy-rsa/; source /etc/openvpn/easy-rsa/vars;'
    c += '/etc/openvpn/easy-rsa/revoke-full %s; rm /etc/openvpn/keys/%s.*' % (name, name)

    return WebUtils.system(c)

def create_tunnel(sysconf, data, callback):
    T = sysconf.Tunnel
    name = ""
    oldname = ""
    config = {}
    for k,v in data.items():
        if k == 'name':
            name = v
        elif k == 'oldname':
            oldname = v
        if k in ['CA', 'crt', 'key']:
            print v
            if v:
                config[k] = v[1].read()
        else:
            config[k] = v

    T[name] = config

    # In case this was a rename.
    if 'oldname' in data:
        del T[oldname]
    
    sysconf.Tunnel = T
    
    def returnB(_):
        return WebUtils.system('/etc/init.d/openvpn restart').addBoth(callback)

    return WebUtils.system('/usr/local/tcs/tums/configurator --tunnel').addBoth(returnB)


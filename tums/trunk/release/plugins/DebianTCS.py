import config, os
from Core import Utils
import socket, struct

class Plugin(object):
    parameterHook = "--debtcs"
    parameterDescription = "Install required packages into Debian"
    parameterArgs = ""
    autoRun = False
    required = "debian"
    configFiles = []

    def reloadServices(self):
        pass

    def writeConfig(self, *a):
        packageNames = [
            'apache2-mpm-prefork',
            'acl', 
            'libexpect-perl',
            'php5', 
            'traceroute',
            'tcptraceroute',
            'rrdtool',
            'php-db',
            'php5-mysql',
            'php5-gd',
            'slapd',
            'screen',
            'greylistd',
            'openssh-server',
            'ldap-utils',
            'libpam-ldap',
            #'ldap2dns',
            'bind9',
            'nscd',
            'libnss-ldap',
            'samba',
            'samba-doc',
            'smbldap-tools',
            'ulogd',
            'openvpn',
            'shorewall',
            'dhcp3-server',
            'lm-sensors',
            'smartmontools',
            'spamassassin',
            'python-zopeinterface',
            'python-sqlite',
            'python-pysqlite2',
            'python-pyopenssl',
            'python-ldap',
            'fprobe-ulog',
            'python-mysqldb',
            'exim4-daemon-heavy',
            'build-essential',
            'python-dev',
            'pppoe',
            'cupsys',
            'pppoeconf',
            'courier-authdaemon',
            'courier-authlib-ldap',
            'courier-imap',
            'courier-imap-ssl',
            'courier-ldap',
            'courier-pop',
            'courier-pop-ssl',
            'ddclient',
            'clamav-daemon',
            'squid',
            'ntpdate',
            'openntpd',
            'vim-full',
            'quagga',
            #'sarg',
            'mysql-server',
            'python-crypto',
            'vsftpd',
            '6tunnel',
            'xtradius',
            'l2tpns',
            'debsecan', 
            'vlan',
            'asterisk-bristuff',
            'asterisk-app-fax',
            'zaptel',
            'zaptel-source',
            'dansguardian',
            'python-imaging'
        ]
        aptArgs = " ".join(packageNames)
	print "Installing required files... ", 

        if not os.path.exists('/root/cdinst'):
            os.system('DEBIAN_FRONTEND="noninteractive" apt-get -y -q --force-yes install ' + aptArgs + ' > /dev/null 2>&1')
        
	print "Done!"
        # Put Openvpn stuff in the right place
        os.system('cp -a /usr/share/doc/openvpn/examples/easy-rsa/2.0 /etc/openvpn/easy-rsa > /dev/null 2>&1')
        os.system('cd packages; tar -jxf exilog.tar.bz2; mv exilog-tums /usr/local/tcs/ > /dev/null 2>&1')
        os.system('cd /; tar -jxf /usr/local/tcs/tums/packages/overlay.tar.bz2 > /dev/null 2>&1')
        os.system('mysqladmin create exilog > /dev/null 2>&1')
        os.system('cd /usr/local/tcs/tums/')

        # Fix exim things
        neededFiles = [
            '/etc/exim4/rbl_domain_whitelist', 
            '/etc/exim4/rbl_ip_whitelist', 
            '/etc/exim4/rbl_sender_whitelist', 
            '/etc/exim4/host_noscan_from',
            '/etc/exim4/host_av_noscan_from',
            '/etc/exim4/host_demime_noscan_from',
            '/etc/exim4/relay_domains',
            '/etc/exim4/etrn_domains',
        ]

        for each in neededFiles:
            os.system('touch %s' % each)

        # configure vpns
        os.system('ln -s /etc/openvpn/easy-rsa/keys /etc/openvpn/keys > /dev/null 2>&1')

        # Patch OpenVPN        
        os.system('cp /usr/local/tcs/tums/packages/rsa-revoke-full /etc/openvpn/easy-rsa/revoke-full')

        os.system('chmod +x /usr/local/tcs/tums/existat.py')
        os.system('chmod +x /usr/local/tcs/tums/existat-render.py')

        # Configure modprobe

        vmodules = """ip_conntrack_ftp
ip_conntrack_amanda
ip_conntrack_ftp
ip_conntrack_irc
ip_conntrack_netbios_ns
ip_conntrack_pptp
ip_conntrack_tftp
ip_nat_amanda
ip_nat_ftp 
ip_nat_irc 
ip_nat_pptp
ip_nat_snmp_basic
ip_nat_tftp
ip_set
ip_set_iphash
ip_set_ipmap
ip_set_macipmap
ip_set_portmap\n"""
        modules = open('/etc/modules').read()
        if not 'VFirewall' in modules:
            m = open('/etc/modules', 'at')
            m.write('\n#VFirewall\n')
            m.write(vmodules)
            m.close()

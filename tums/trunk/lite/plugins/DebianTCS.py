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
            'fprobe',
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
            'squid3',
            'ntpdate',
            'vim-full',
            'quagga',
            #'sarg',
            'mysql-server',
            'python-crypto',
            'vsftpd',
            '6tunnel',
            'xtradius',
            'l2tpns'
        ]
        aptArgs = " ".join(packageNames)
        os.system('aptitude install ' + aptArgs)
        # Put Openvpn stuff in the right place
        os.system('cp -a /usr/share/doc/openvpn/examples/easy-rsa/2.0 /etc/openvpn/easy-rsa')
        os.system('cd packages; tar -jxf exilog.tar.bz2; mv exilog-tums /usr/local/tcs/')
        os.system('cd /; tar -jxf /usr/local/tcs/tums/packages/overlay.tar.bz2')
        os.system('mysqladmin create exilog')
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
            os.system('echo -n > %s' % each)

        # configure vpns
        os.system('ln -s /etc/openvpn/easy-rsa/keys /etc/openvpn/keys')
        os.system('chmod +x /usr/local/tcs/tums/existat.py')
        os.system('chmod +x /usr/local/tcs/tums/existat-render.py')
